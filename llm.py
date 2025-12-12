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
Ты — эксперт PostgreSQL. База содержит две таблицы:

videos (
    id TEXT PRIMARY KEY,
    creator_id TEXT NOT NULL,
    video_created_at TIMESTAMPTZ NOT NULL,
    views_count BIGINT,
    likes_count BIGINT,
    comments_count BIGINT,
    reports_count BIGINT
)

video_snapshots (
    id TEXT PRIMARY KEY,
    video_id TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    delta_views_count BIGINT,
    delta_likes_count BIGINT,
    delta_comments_count BIGINT,
    delta_reports_count BIGINT,
    views_count BIGINT,
    likes_count BIGINT,
    comments_count BIGINT,
    reports_count BIGINT
)

Твоя задача: по запросу на русском языке вернуть ТОЛЬКО один правильный SQL-запрос, который возвращает ровно одно число.

ВАЖНО:
- id и creator_id — это строки (TEXT), всегда в одинарных кавычках
- views_count в таблице videos — это итоговая статистика
- даты пиши в формате '2025-11-28 00:00:00+00'

Примеры:

Запрос: Сколько всего видео?
SQL: SELECT COUNT(*) FROM videos;

Запрос: Сколько видео у креатора с id aca1061a9d324ecf8c3fa2bb32d7be63?
SQL: SELECT COUNT(*) FROM videos WHERE creator_id = 'aca1061a9d324ecf8c3fa2bb32d7be63';

Запрос: Сколько видео у креатора с id aca1061a9d324ecf8c3fa2bb32d7be63 набрали больше 10000 просмотров по итоговой статистике?
SQL: SELECT COUNT(*) FROM videos WHERE creator_id = 'aca1061a9d324ecf8c3fa2bb32d7be63' AND views_count > 10000;

Запрос: На сколько просмотров выросли все видео 28 ноября 2025?
SQL: SELECT COALESCE(SUM(delta_views_count), 0) FROM video_snapshots WHERE created_at >= '2025-11-28 00:00:00+00' AND created_at < '2025-11-29 00:00:00+00';

Запрос пользователя:
{query}

ОТВЕТЬ ТОЛЬКО SQL. Без ```sql, без пояснений, без лишних символов.
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
    sql = sql.replace("```sql", "").replace("```", "").strip()
    if not sql.upper().startswith("SELECT"):
        raise ValueError("LLM вернул не SQL")
    return sql