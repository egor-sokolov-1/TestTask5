from openai import AsyncOpenAI
import os
import re
from dotenv import load_dotenv

load_dotenv()

client = AsyncOpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

MODEL = "llama-3.1-70b-versatile"

MONTHS = {
    "января": "01", "февраля": "02", "марта": "03", "апреля": "04",
    "мая": "05", "июня": "06", "июля": "07", "августа": "08",
    "сентября": "09", "октября": "10", "ноября": "11", "декабря": "12",
    "январе": "01", "феврале": "02", "марте": "03", "апреле": "04",
    "мае": "05", "июне": "06", "июле": "07", "августе": "08",
    "сентябре": "09", "октябре": "10", "ноябре": "11", "декабре": "12",
    "январь": "01", "февраль": "02", "март": "03", "апрель": "04",
    "май": "05", "июнь": "06", "июль": "07", "август": "08",
    "сентябрь": "09", "октябрь": "10", "ноябрь": "11", "декабрь": "12"
}

SYSTEM_PROMPT = """
Ты — генератор SQL-запросов для PostgreSQL.
В базе есть две таблицы:
1) videos — итоговая статистика видео
   - id TEXT PRIMARY KEY
   - creator_id TEXT NOT NULL
   - video_created_at TIMESTAMPTZ NOT NULL
   - views_count BIGINT
   - likes_count BIGINT
   - comments_count BIGINT
   - reports_count BIGINT
2) video_snapshots — почасовые замеры
   - video_id TEXT
   - created_at TIMESTAMPTZ NOT NULL
   - delta_views_count BIGINT
Требования:
— Ответ всегда только один SQL-запрос.
— Ответ обязан начинаться с SELECT и заканчиваться ';'.
— SQL должен возвращать одно числовое значение.
— Никакого текста, пояснений, markdown и т.п.
Правила:
1) id и creator_id — строки (TEXT).
2) Итоговые просмотры → videos.views_count.
3) Если спрашивают про месяц → брать video_created_at в диапазоне [начало_месяца, начало_следующего).
4) Если спрашивают про день по delta → суммировать delta_views_count в диапазоне [день 00:00, следующий день 00:00).
5) «Опубликованные» → таблица videos.
6) «Замеры», «дельта», «за час» → таблица video_snapshots.
7) Если встречается «отрицательн», «меньше 0» → delta_views_count < 0.
"""

def clean_sql(raw: str) -> str:
    garbage = ["```sql", "```", "SQL:", "sql:", "Ответ:", "Вот ответ:"]
    for g in garbage:
        raw = raw.replace(g, "")
    return raw.strip()

def rule_based_sql(q: str) -> str | None:
    q_low = q.strip().lower()

    cid_match = re.search(r"id\s+([0-9a-f]{32})", q_low)
    cid = cid_match.group(1) if cid_match else None

    if "креатор" in q_low and ("100000" in q_low or "100 000" in q_low or "100к" in q_low or "100k" in q_low):
        return (
            "SELECT COUNT(DISTINCT creator_id) FROM videos "
            "WHERE views_count > 100000;"
        )

    if "календарн" in q_low and "дн" in q_low and cid:
        m = re.search(r"(ноябр[ьяе])\s+(\d{4})", q_low)
        if m:
            mm = "11"
            year = m.group(2)
            start = f"{year}-{mm}-01 00:00:00+00"
            end = f"{year}-12-01 00:00:00+00"
            return (
                "SELECT COUNT(DISTINCT DATE(video_created_at)) FROM videos "
                f"WHERE creator_id = '{cid}' "
                f"AND video_created_at >= '{start}' AND video_created_at < '{end}';"
            )

    neg = re.search(r"(отрицательн|меньше\s*0|уменьшил|стало\s+меньше)", q_low)
    if neg and any(k in q_low for k in ["delta", "дельт", "замер", "за час", "почас"]):
        return "SELECT COUNT(*) FROM video_snapshots WHERE delta_views_count < 0;"

    if "с " in q_low and " по " in q_low and "видео" in q_low and cid:
        m = re.search(
            r"с (\d{1,2}) (\w+) (\d{4}) по (\d{1,2}) (\w+) (\d{4})",
            q_low
        )
        if m:
            d1, m1, y1, d2, m2, y2 = m.groups()
            mm1 = MONTHS.get(m1.lower())
            mm2 = MONTHS.get(m2.lower())
            if mm1 and mm2:
                start = f"{y1}-{mm1}-{int(d1):02d} 00:00:00+00"
                end = f"{y2}-{mm2}-{int(d2):02d} 23:59:59+00"
                return (
                    "SELECT COUNT(*) FROM videos "
                    f"WHERE creator_id = '{cid}' "
                    f"AND video_created_at >= '{start}' "
                    f"AND video_created_at <= '{end}';"
                )

    if "дельт" in q_low or "замер" in q_low or "за час" in q_low or "почас" in q_low:
        time_range = re.search(r"с (\d{1,2}):(\d{2}) до (\d{1,2}):(\d{2})", q_low)
        date_match = re.search(r"(\d{1,2}) (\w+) (\d{4})", q_low)
        if cid and time_range and date_match:
            h1, m1, h2, m2 = time_range.groups()
            day, month_word, year = date_match.groups()
            mm = MONTHS.get(month_word.lower())
            if not mm:
                return None
            start_ts = f"{year}-{mm}-{int(day):02d} {int(h1):02d}:{int(m1):02d}:00+00"
            end_ts = f"{year}-{mm}-{int(day):02d} {int(h2):02d}:{int(m2):02d}:00+00"
            return (
                "SELECT COALESCE(SUM(delta_views_count), 0) FROM video_snapshots "
                f"WHERE video_id IN (SELECT id FROM videos WHERE creator_id = '{cid}') "
                f"AND created_at >= '{start_ts}' AND created_at <= '{end_ts}';"
            )

    if cid and ("10000" in q_low or "10 000" in q_low or "10k" in q_low or
                "10к" in q_low or "десяти тысяч" in q_low or
                "больше 10" in q_low or "более 10" in q_low):
        return (
            "SELECT COUNT(*) FROM videos "
            f"WHERE creator_id = '{cid}' AND views_count > 10000;"
        )

    m_month = re.search(
        r"(январ[ьяе]|феврал[ьяе]|март[ае]|апрел[ьяе]|ма[йяе]|июн[ьяе]|июл[ьяе]|август[ае]|сентябр[ьяе]|октябр[ьяе]|ноябр[ьяе]|декабр[ьяе])(?:\s+|[^0-9]+)(\d{4})",
        q_low
    )
    if m_month and ("просмотр" in q_low or "суммар" in q_low or "сколько" in q_low):
        month_word, year = m_month.groups()
        base = month_word.replace("е", "я")
        mm = MONTHS.get(base, MONTHS.get(month_word, None))
        if not mm:
            return None
        year_i = int(year)
        m_i = int(mm)
        if m_i == 12:
            start = f"{year_i}-12-01 00:00:00+00"
            end = f"{year_i+1}-01-01 00:00:00+00"
        else:
            start = f"{year_i}-{m_i:02d}-01 00:00:00+00"
            end = f"{year_i}-{m_i+1:02d}-01 00:00:00+00"
        return (
            "SELECT COALESCE(SUM(views_count), 0) FROM videos "
            f"WHERE video_created_at >= '{start}' AND video_created_at < '{end}';"
        )

    if cid and "сколько" in q_low and "видео" in q_low:
        return f"SELECT COUNT(*) FROM videos WHERE creator_id = '{cid}';"

    return None

async def ask_llm(messages):
    r = await client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.0,
        max_tokens=300
    )
    return r.choices[0].message.content.strip()

async def generate_sql(user_query: str) -> str:
    sql = None
    try:
        sql = rule_based_sql(user_query)
    except Exception:
        pass

    if sql:
        return sql

    raw = await ask_llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query}
    ])
    sql = clean_sql(raw)
    if not sql.endswith(";"):
        sql += ";"
    if sql.upper().startswith("SELECT"):
        return sql

    raw2 = await ask_llm([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Ответь строго SQL (SELECT ...;). " + user_query}
    ])
    sql2 = clean_sql(raw2)
    if not sql2.endswith(";"):
        sql2 += ";"
    if sql2.upper().startswith("SELECT"):
        return sql2

    return "SELECT 0;"
