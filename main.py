from __future__ import annotations

import asyncio
import os
from pathlib import Path

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv, find_dotenv

from handlers.user_handlers import router
from middleware import DbSessionMiddleware
from excel_worker.excel_reader import create_location
from excel_worker.location_creator_excel import create_user_data

load_dotenv(find_dotenv())
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("ИДИ НАХУЙ ТОКЕНА НЕТ УЕБОК БЛЯДСКИЙ МАТЬ ТВОЮ")

bot = Bot(token=TOKEN)
dp = Dispatcher()
dp.include_router(router)
dp.message.middleware(DbSessionMiddleware())

async def main() -> None:
    print("→ Excel import…")
    await create_location()
    await create_user_data()

    print("→ Start polling bot…")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
