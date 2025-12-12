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
Ты — эксперт PostgreSQL. База имеет две таблицы:

videos (
    id TEXT PRIMARY KEY,
    creator_id TEXT NOT NULL,
    video_created_at TIMESTAMPTZ NOT NULL,   -- дата и время публикации видео
    views_count BIGINT
)

video_snapshots (
    id TEXT PRIMARY KEY,
    video_id TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    delta_views_count BIGINT
)

Твоя задача: по любому запросу на русском языке вернуть ТОЛЬКО один правильный SQL-запрос, который возвращает ровно одно число.

КРИТИЧЕСКИ ВАЖНЫЕ ПРАВИЛА:
- creator_id и id — строки в одинарных кавычках
- "по 5 ноября 2025 включительно" = до конца дня 5 ноября = video_created_at < '2025-11-06 00:00:00+00'
- "с 1 ноября 2025 по 5 ноября 2025 включительно" = от 2025-11-01 00:00:00 до 2025-11-05 23:59:59:999
- используй: video_created_at >= '2025-11-01 00:00:00+00' AND video_created_at < '2025-11-06 00:00:00+00'

Примеры (точно следуй им):

Запрос: Сколько всего видео?
SQL: SELECT COUNT(*) FROM videos;

Запрос: Сколько видео у креатора с id aca1061a9d324ecf8c3fa2bb32d7be63 набрали больше 10000 просмотров?
SQL: SELECT COUNT(*) FROM videos WHERE creator_id = 'aca1061a9d324ecf8c3fa2bb32d7be63' AND views_count > 10000;

Запрос: Сколько видео опубликовал креатор с id 8b76e572635b400c9052286a56176e03 в период с 1 ноября 2025 по 5 ноября 2025 включительно?
SQL: SELECT COUNT(*) FROM videos WHERE creator_id = '8b76e572635b400c9052286a56176e03' AND video_created_at >= '2025-11-01 00:00:00+00' AND video_created_at < '2025-11-06 00:00:00+00';

Запрос: Сколько видео у креатора 8b76e572635b400c9052286a56176e03 вышло с 10 по 15 декабря 2025?
SQL: SELECT COUNT(*) FROM videos WHERE creator_id = '8b76e572635b400c9052286a56176e03' AND video_created_at >= '2025-12-10 00:00:00+00' AND video_created_at < '2025-12-16 00:00:00+00';

Запрос: На сколько просмотров выросли все видео 28 ноября 2025?
SQL: SELECT COALESCE(SUM(delta_views_count), 0) FROM video_snapshots WHERE created_at >= '2025-11-28 00:00:00+00' AND created_at < '2025-11-29 00:00:00+00';

Теперь запрос пользователя:
{query}

ОТВЕТЬ ТОЛЬКО SQL. Без ```sql, без текста, без кавычек, только сам запрос.
""".strip()

async def generate_sql(user_query: str) -> str:
    try:
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
            raise ValueError("Не SQL")
        
        return sql
    except Exception as e:
        print(f"LLM ошибка: {e}")
        return "SELECT 0"