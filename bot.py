from aiogram import Bot, Dispatcher
from aiogram.types import Message
import asyncio
from dotenv import load_dotenv
import os
from db import get_scalar
from llm import generate_sql

load_dotenv()

bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
dp = Dispatcher()

@dp.message()
async def handle(message: Message):
    try:
        sql = await generate_sql(message.text)
        result = await get_scalar(sql)
        await message.answer(str(result))
    except Exception as e:
        print("Ошибка:", e)
        await message.answer("Не понял запрос")

async def main():
    print("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())