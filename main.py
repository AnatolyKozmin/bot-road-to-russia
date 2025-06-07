from __future__ import annotations

import asyncio
import os
import subprocess
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


async def run_alembic_upgrade() -> None:

    proc = await asyncio.create_subprocess_exec(
        "alembic", "upgrade", "head",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError("Alembic failed:\n" + stdout.decode())
    print(stdout.decode().strip())



async def main() -> None:
    print("→ Alembic migrations…")
    await run_alembic_upgrade()

    print("→ Excel import…")
    await create_location()
    await create_user_data()

    print("→ Start polling bot…")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
