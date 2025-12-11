import asyncpg
import os
from typing import Optional

pool: Optional[asyncpg.Pool] = None

async def init_pool():
    global pool
    pool = await asyncpg.create_pool(dsn=os.getenv("DATABASE_URL"))

async def get_scalar(sql: str) -> int:
    async with pool.acquire() as conn:
        try:
            result = await conn.fetchval(sql)
            return int(result) if result is not None else 0
        except Exception as e:
            print(f"Ошибка SQL: {sql}\n{e}")
            return 0