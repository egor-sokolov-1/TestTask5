from openai import AsyncOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = AsyncOpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

MODEL = "llama-3.1-70b-versatile"

SYSTEM_PROMPT = SYSTEM_PROMPT = """
Ты генерируй ТОЛЬКО SQL, ничего больше.

Пример:
Запрос: Сколько видео у креатора с id aca1061a9d324ecf8c3fa2bb32d7be63 набрали больше 10 000 просмотров по итоговой статистике?
SQL: 
SQL: SELECT COUNT(*) FROM videos WHERE creator_id = 'aca1061a9d324ecf8c3fa2bb32d7be63' AND views_count > 10000;

Запрос: Сколько всего видео?
SQL: SELECT COUNT(*) FROM videos;

Теперь запрос:
{query}

Ответь только SQL.
""".strip()

async def generate_sql(user_query: str) -> str:
    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.format(query=user_query)},
            {"role": "user", "content": user_query}
        ],
        temperature=0.0,
        max_tokens=300
    )
    sql = response.choices[0].message.content.strip()
    sql = sql.replace("```sql", "").replace("```", "").replace("SQL:", "").strip()
    
    return sql