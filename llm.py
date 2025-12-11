from openai import AsyncOpenAI
import os

client = AsyncOpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

MODEL = "llama-3.1-70b-versatile" 

SYSTEM_PROMPT = """
Ты эксперт PostgreSQL. По запросу на русском языке верни ТОЛЬКО один SQL-запрос,
возвращающий ровно одно число.

Примеры:
Запрос: Сколько всего видео?
SQL: SELECT COUNT(*) FROM videos;

Запрос: Сколько видео у креатора 123 вышло с 1 по 10 ноября 2025?
SQL: SELECT COUNT(*) FROM videos WHERE creator_id = 123 AND video_created_at >= '2025-11-01' AND video_created_at < '2025-11-11';

Запрос: На сколько просмотров выросли все видео 28 ноября 2025?
SQL: SELECT COALESCE(SUM(delta_views_count),0) FROM video_snapshots WHERE created_at >= '2025-11-28 00:00:00' AND created_at < '2025-11-29 00:00:00';

Запрос пользователя: {query}

Ответь исключительно SQL. Без ```, без текста.
""".strip()

async def generate_sql(user_query: str) -> str:
    response = await client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.format(query=user_query)},
            {"role": "user", "content": user_query}
        ],
        temperature=0,
        max_tokens=300
    )
    sql = response.choices[0].message.content.strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()
    if not sql.upper().startswith("SELECT"):
        raise ValueError("Не SQL")
    return sql