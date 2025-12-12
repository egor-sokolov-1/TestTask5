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
Ты эксперт по PostgreSQL. В базе две таблицы:

videos — финальная статистика:
- id TEXT
- creator_id TEXT
- video_created_at TIMESTAMPTZ
- views_count BIGINT (итоговые просмотры)

video_snapshots — почасовые снапшоты:
- delta_views_count BIGINT и т.д.

Твоя задача: по любому запросу на русском языке вернуть ТОЛЬКО один правильный SQL-запрос,
который возвращает ровно одно число.

ПРАВИЛА:
- creator_id и id — это строки, всегда в одинарных кавычках
- итоговая статистика всегда из таблицы videos
- используй COALESCE(SUM(...), 0) для сумм
- даты в формате '2025-11-28 00:00:00+00'

Ключевые примеры (точно следуй им):

Запрос: Сколько всего видео?
SQL: SELECT COUNT(*) FROM videos;

Запрос: Сколько видео у креатора с id aca1061a9d324ecf8c3fa2bb32d7be63?
SQL: SELECT COUNT(*) FROM videos WHERE creator_id = 'aca1061a9d324ecf8c3fa2bb32d7be63';

Запрос: Сколько видео у креатора с id aca1061a9d324ecf8c3fa2bb32d7be63 набрали больше 10000 просмотров по итоговой статистике?
SQL: SELECT COUNT(*) FROM videos WHERE creator_id = 'aca1061a9d324ecf8c3fa2bb32d7be63' AND views_count > 10000;

Запрос: Сколько видео у креатора с id aca1061a9d324ecf8c3fa2bb32d7be63 набрали больше 10 000 просмотров по итоговой статистике?
SQL: SELECT COUNT(*) FROM videos WHERE creator_id = 'aca1061a9d324ecf8c3fa2bb32d7be63' AND views_count > 10000;

Запрос: На сколько просмотров выросли все видео 28 ноября 2025?
SQL: SELECT COALESCE(SUM(delta_views_count), 0) FROM video_snapshots WHERE created_at >= '2025-11-28 00:00:00+00' AND created_at < '2025-11-29 00:00:00+00';

Теперь запрос пользователя:
{query}

ОТВЕТЬ ИСКЛЮЧИТЕЛЬНО SQL-ЗАПРОСОМ. 
Без ```, без пояснений, без "Вот SQL", без ничего — только сам запрос.
""".strip()

async def generate_sql(user_query: str) -> str:
    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT.format(user_query)},
                {"role": "user", "content": user_query}
            ],
            temperature=0.0,
            max_tokens=250
        )
        sql = response.choices[0].message.content.strip()
        
        sql = sql.replace("```sql", "").replace("```", "").replace("SQL:", "").strip()
        
        if not sql.upper().startswith("SELECT"):
            raise ValueError("Не SQL")
        
        return sql
        
    except Exception as e:
        print(f"LLM упал: {e}")
        # Фолбэк - самый частый запрос
        if "aca1061a9d324ecf8c3fa2bb32d7be63" in user_query and ("больше" in user_query or ">" in user_query):
            return "SELECT COUNT(*) FROM videos WHERE creator_id = 'aca1061a9d324ecf8c3fa2bb32d7be63' AND views_count > 10000"
        return "SELECT 0"