from sqlalchemy import String, Text, BigInteger, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from db.engine import Base


class Users(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    tg_username: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MessagesForUsers(Base):
    __tablename__ = 'messages_for_users'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    who: Mapped[str] = mapped_column(String)
    tg_username: Mapped[str] = mapped_column(String)
    code: Mapped[str] = mapped_column(String)
    text_for_message: Mapped[str] = mapped_column(Text)
    

class Culture(Base):
    __tablename__ = 'cultures'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    adress: Mapped[str] = mapped_column(String)
    date_time: Mapped[str] = mapped_column(String)
    desc: Mapped[str] = mapped_column(Text)
    ya_card: Mapped[str] = mapped_column(String)
    site: Mapped[str] = mapped_column(String)
    up_five: Mapped[bool] = mapped_column(Boolean, default=False)
    up_hundred: Mapped[bool] = mapped_column(Boolean, default=False)
    is_museum: Mapped[bool] = mapped_column(Boolean, default=False)
    is_park: Mapped[bool] = mapped_column(Boolean, default=False)
    is_delicious: Mapped[bool] = mapped_column(Boolean, default=False)
    is_all_day: Mapped[bool] = mapped_column(Boolean, default=False)


# class Foreigner(Base):
#     id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
#     tg_username: Mapped[str] = mapped_column(String)
#     owner_id: Mapped[str] = mapped_column(ForeignKey('users.id'))


class Meet(Base):
    __tablename__ = 'meets'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[str] = mapped_column(String)  
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    foreigner_tg_name: Mapped[str] = mapped_column(String)
    q1: Mapped[str] = mapped_column(Text, nullable=True)
    q2: Mapped[str] = mapped_column(Text, nullable=True )
    q3: Mapped[str] = mapped_column(Text, nullable=True)
    q4: Mapped[str] = mapped_column(Text, nullable=True)
    q5: Mapped[str] = mapped_column(Text, nullable=True)
    photo_base64: Mapped[str] = mapped_column(Text)


