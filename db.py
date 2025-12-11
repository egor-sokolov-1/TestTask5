import asyncpg
import os
from typing import Optional

pool: Optional[asyncpg.Pool] = None

async def init_pool():
    global pool
    pool = await asyncpg.create_pool(dsn=os.getenv("DATABASE_URL"))

async def close_pool():
    global pool
    if pool:
        await pool.close()

async def get_scalar(sql: str, *args) -> int:
    """
    Выполняет SQL и возвращает одно число.
    Если ошибка — возвращает 0 и логирует.
    """
    async with pool.acquire() as conn:
        try:
            result = await conn.fetchval(sql, *args)
            return int(result) if result is not None else 0
        except Exception as e:
            print(f"SQL ERROR: {sql}")
            print(f"ERROR: {e}")
            return 0