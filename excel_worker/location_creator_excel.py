import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.engine import session_maker
import pandas as pd
import asyncio 
from db.models import Culture

df = pd.read_excel('mero.xlsx')
selected = df.iloc[:, [0, 1, 2, 3, 4, 5]]

async def create_user_data():
    async with session_maker() as session:
        for _, row in selected.iterrows():
            mero = Culture(
                name=str(row[0]),
                adress=str(row[1]),
                date_time=str(row[2]),
                desc=str(row[3]),
                ya_card=str(row[4]),
                site=str(row[5]),
            )
            session.add(mero)
        await session.commit()
    print('Импорт всё !')

