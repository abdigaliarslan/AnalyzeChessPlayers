import os
import re
from dotenv import load_dotenv

from backend.db import SessionLocal
from .models import Analysis, AnalysisStatus


load_dotenv()

import google.generativeai as genai
import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

async def get_chess_analysis(pgn_content: str) -> str:
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": """Проанализируй шахматную партию ниже. Пиши кратко, простыми словами и по делу. 
                    Формат: 1. Итог игры (1-2 предложения). 
                    "2. Список из 2-3 главных ходов с пояснением «почему это важно». Важна не глубина анализа, а человекочитаемый текст."""
                },
                {
                    "role": "user", 
                    "content": f"Analyze this game: {pgn_content}"
                }
            ],
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Groq API Error: {e}")
        return "Ошибка при получении анализа от ИИ."


def normalize_pgn(pgn: str) -> str:
    pgn = re.sub(r'\[.*?\]\s*', '', pgn)
    pgn = " ".join(pgn.split())
    return pgn.strip()
 


async def process_analysis(analysis_id: int):
    db = SessionLocal()

    try:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            return 

        analysis.status = AnalysisStatus.queued
        db.commit()
        
        result = await get_chess_analysis(analysis.pgn_content)

        analysis.result_text = result
        analysis.status = AnalysisStatus.done
        db.commit()
    except Exception as e:
        analysis.status = AnalysisStatus.failed
        db.commit()
    finally:
        db.close()