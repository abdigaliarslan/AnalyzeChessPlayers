import os
from dotenv import load_dotenv
from openai import AsyncOpenAI 

load_dotenv()

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def get_chess_analysis(pgn_content: str) -> str:
    try:
        response = await client.chat.completions.create(
            model="gpt-4",  
            messages=[
                {
                    "role": "system", 
                    "content": "Проанализируй шахматную партию ниже. Пиши кратко, простыми словами и по делу. Формат: > 1. Итог игры (1-2 предложения). 2. Список из 2-3 главных ходов с пояснением «почему это важно». Важна не глубина анализа, а человекочитаемый текст."
                },
                {
                    "role": "user", 
                    "content": f"Analyze this game: {pgn_content}"
                }
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI Error: {e}")
        return "Ошибка при получении анализа от ИИ."