from __future__ import annotations
import asyncio
import os
import logging
from pathlib import Path
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv, find_dotenv
from handlers.user_handlers import router
from middleware import DbSessionMiddleware
from excel_worker.excel_reader import create_location
from excel_worker.location_creator_excel import create_user_data
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from db.engine import session_maker  # Используем session_maker из db.engine

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv(find_dotenv())
TOKEN = os.getenv("TOKEN")
DB_URL = os.getenv("DB_URL")

if not TOKEN:
    logger.error("ТОКЕНА НЕТ, ИДИ НАХУЙ!")
    raise RuntimeError("ТОКЕНА НЕТ, МАТЬ ТВОЮ!")
if not DB_URL:
    logger.error("DB_URL НЕТ, БЛЯТЬ!")
    raise RuntimeError("DB_URL НЕТ, ЕБАНА В РОТ!")

# Настройка базы данных
engine = create_async_engine(DB_URL)

# Инициализация бота
bot = Bot(token=TOKEN)
dp = Dispatcher()
dp.include_router(router)
dp.message.middleware(DbSessionMiddleware())

async def main() -> None:
    logger.info("→ Запускаем бота, сука...")
    
    # Импорт данных из Excel
    async with session_maker() as session:
        logger.info("→ Импортируем Excel, блять...")
        try:
            await create_location(session)
            await create_user_data(session)
            logger.info("→ Импорт Excel завершён, заебись!")
        except Exception as e:
            logger.error(f"→ Импорт Excel наебнулся: {str(e)}")
            raise

    # Запуск бота
    logger.info("→ Запускаем polling, держись...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"→ Polling наебнулся: {str(e)}")
        raise
    finally:
        logger.info("→ Бот остановлен, пиздец.")
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("→ Бот остановлен юзером, норм.")
    except Exception as e:
        logger.error(f"→ Бот наебнулся при старте: {str(e)}")
        raise
