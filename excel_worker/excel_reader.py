import pandas as pd
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from db.engine import engine  
from db.models import MessagesForUsers


df = pd.read_excel('data.xlsx')
selected = df.iloc[:, [0, 1, 4, 5]]

async def main():
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        for _, row in selected.iterrows():
            message = MessagesForUsers(
                who=str(row[0]),
                tg_username=str(row[1]),
                code=str(row[2]),
                text_for_message=str(row[3])
            )
            session.add(message)
        await session.commit()
    print('Импорт завершён успешно!')

if __name__ == "__main__":
    asyncio.run(main())