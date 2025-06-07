import sys
import os
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from db.engine import session_maker  # Исправлено: sessionmaker → session_maker
from db.models import MessagesForUsers
import logging

# Настройка пути к проекту
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Настройка логирования
logger = logging.getLogger(__name__)

async def create_location(session: AsyncSession):
    try:
        # Проверяем, есть ли записи в таблице messages_for_users
        count = await session.execute(select(func.count()).select_from(MessagesForUsers))
        if count.scalar() > 0:
            logger.info("MessagesForUsers data already imported, skipping...")
            return

        # Читаем Excel
        df = pd.read_excel("user_data.xlsx")
        messages = [
            MessagesForUsers(
                who=str(row["who"]),
                tg_username=str(row["tg_username"]),
                code=str(row["code"]),
                text_for_message=str(row["text_for_message"]),
            )
            for _, row in df.iterrows()
        ]
        session.add_all(messages)
        await session.commit()
        logger.info("MessagesForUsers data imported successfully from user_data.xlsx")
    except Exception as e:
        logger.error(f"Failed to import MessagesForUsers data: {str(e)}")
        await session.rollback()
        raise