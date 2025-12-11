from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
import asyncio
import os
from dotenv import load_dotenv

from db import init_pool, close_pool, get_scalar
from llm import generate_sql

load_dotenv()

bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
dp = Dispatcher()

@dp.message()
async def handle_message(message: Message):
    query = message.text.strip()
    if not query:
        return

    try:
        sql = await generate_sql(query)
        result = await get_scalar(sql)
        await message.answer(str(result))
    except Exception as e:
        print(e)
        await message.answer("Ошибка. Попробуй перефразировать.")

async def main():
    await init_pool()
    await dp.start_polling(bot)
    await close_pool()

if __name__ == "__main__":
    asyncio.run(main())