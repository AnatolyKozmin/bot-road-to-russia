import pandas as pd
import asyncio 
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker 
from db.engine import session_maker
from db.models import MessagesForUsers


df = pd.read_excel('data_mero.xlsx')
selected = df.iloc[:, [0,1,2,3]]

async def main():
    async with session_maker() as session:
        for _, row in selected.iterrows():
            message = ...