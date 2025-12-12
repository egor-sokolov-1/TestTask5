import asyncpg
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

pool: Optional[asyncpg.Pool] = None

async def get_pool() -> asyncpg.Pool:
    global pool
    if pool is None:
        dsn = os.getenv("DATABASE_URL")
        if not dsn:
            raise RuntimeError("DATABASE_URL не найден в .env!")
        if dsn.startswith("postgresql+psycopg"):
            dsn = dsn.replace("postgresql+psycopg", "postgresql")
        
        print("Создаём подключение к базе")
        pool = await asyncpg.create_pool(dsn=dsn, min_size=1, max_size=10)
        print("Подключение к базе установлено")
    
    return pool

async def get_scalar(sql: str) -> int:
    pool = await get_pool()
    async with pool.acquire() as conn:
        try:
            result = await conn.fetchval(sql)
            return int(result) if result is not None else 0
        except Exception as e:
            print(f"SQL ERROR: {sql}\n{e}")
            return 0