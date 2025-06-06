import os
from dotenv import load_dotenv, find_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

load_dotenv(find_dotenv())

engine = create_async_engine(os.getenv('DB_URL'), echo=True)
session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=True)

class Base(DeclarativeBase):
    __abstract__ = True