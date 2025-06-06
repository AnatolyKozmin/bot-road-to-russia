from aiogram.dispatcher.middlewares.base import BaseMiddleware
from db.engine import session_maker

class DbSessionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        async with session_maker() as session:
            data["session"] = session
            return await handler(event, data)