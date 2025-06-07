import sys
import os
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from db.engine import session_maker  # Исправлено: sessionmaker → session_maker
from db.models import Culture
import logging

# Настройка пути к проекту
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Настройка логирования
logger = logging.getLogger(__name__)

async def create_user_data(session: AsyncSession):
    try:
        # Проверяем, есть ли записи в таблице cultures
        count = await session.execute(select(func.count()).select_from(Culture))
        if count.scalar() > 0:
            logger.info("Culture data already imported, skipping...")
            return

        # Читаем Excel
        df = pd.read_excel("mero.xlsx")
        cultures = [
            Culture(
                name=str(row["name"]),
                address=str(row["address"]),
                date_time=str(row["date_time"]),
                desc=str(row["description"]),
                ya_card=str(row["ya_card"]),
                site=str(row["site"]),
            )
            for _, row in df.iterrows()
        ]
        session.add_all(cultures)
        await session.commit()
        logger.info("Culture data imported successfully from mero.xlsx")
    except Exception as e:
        logger.error(f"Failed to import Culture data: {str(e)}")
        await session.rollback()
        raise
