from openai import AsyncOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = AsyncOpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

MODEL = "llama-3.1-70b-versatile"

SYSTEM_PROMPT = """
Ты эксперт PostgreSQL.

Таблица videos:
- id TEXT
- creator_id TEXT
- video_created_at TIMESTAMPTZ
- views_count BIGINT  -- это итоговая статистика

Твоя задача — вернуть ТОЛЬКО SQL, который даёт одно число.

ВАЖНО:
- creator_id всегда в кавычках: 'aca1061a9d324ecf8c3fa2bb32d7be63'
- "больше 10 000" или "больше 10000" = views_count > 10000

ПРИМЕРЫ:

Запрос: Сколько всего видео?
SQL: SELECT COUNT(*) FROM videos;

Запрос: Сколько видео у креатора с id aca1061a9d324ecf8c3fa2bb32d7be63 набрали больше 10 000 просмотров по итоговой статистике?
SQL: SELECT COUNT(*) FROM videos WHERE creator_id = 'aca1061a9d324ecf8c3fa2bb32d7be63' AND views_count > 10000;

Запрос: Сколько видео у креатора с id aca1061a9d324ecf8c3fa2bb32d7be63 набрали больше 10000 просмотров?
SQL: SELECT COUNT(*) FROM videos WHERE creator_id = 'aca1061a9d324ecf8c3fa2bb32d7be63' AND views_count > 10000;

Запрос пользователя:
{query}

ОТВЕТЬ ТОЛЬКО SQL. НИЧЕГО БОЛЬШЕ.
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