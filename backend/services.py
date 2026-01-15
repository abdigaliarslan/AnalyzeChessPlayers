import os
import re
from dotenv import load_dotenv

from backend.db import SessionLocal
from .models import Analysis, AnalysisStatus

import google.generativeai as genai
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


async def get_chess_analysis(pgn_content: str) -> str:
    """
    Sends PGN content to Groq API to get a concise, human-readable analysis.
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Analyze the chess game below. Write concisely, in simple and clear language.\n"
                        "Format:\n"
                        "1. Game result (1-2 sentences).\n"
                        "2. List 2-3 key moves with explanation 'why this matters'. "
                        "Focus on readability, not deep analysis."
                    )
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
        return "Error obtaining analysis from AI."


def normalize_pgn(pgn: str) -> str:
    """
    Removes PGN tags and extra whitespace for cleaner processing.
    """
    pgn = re.sub(r'\[.*?\]\s*', '', pgn)
    return " ".join(pgn.split()).strip()


async def process_analysis(analysis_id: int):
    """
    Processes a single Analysis record: sets status, runs AI analysis,
    saves results and updates status in the database.
    """
    db = SessionLocal()
    analysis = None

    try:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            print(f"No analysis found for ID {analysis_id}")
            return

        analysis.status = AnalysisStatus.queued
        db.commit()

        normalized_pgn = normalize_pgn(analysis.pgn_content)
        result = await get_chess_analysis(normalized_pgn)

        analysis.result_text = result
        analysis.status = AnalysisStatus.done
        db.commit()
        print(f"Analysis {analysis_id} completed successfully.")

    except Exception as e:
        if analysis:
            analysis.status = AnalysisStatus.failed
            db.commit()
        print(f"Error processing analysis {analysis_id}: {e}")

    finally:
        db.close()
