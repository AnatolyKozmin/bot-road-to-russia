import os
import asyncio
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv, find_dotenv
from handlers.user_handlers import router
from middleware import DbSessionMiddleware


class Mode():
    f'''
        test_mode - конфиг для разработки на локальной машине
        prod_mode - конфиг для прода
    '''
    def test_mode():
        token = os.getenv('TOKEN')

    def prod_mode():
        ...

load_dotenv(find_dotenv())
bot = Bot(token=os.getenv('TOKEN'))


dp = Dispatcher()
dp.include_router(router)
dp.message.middleware(DbSessionMiddleware())



async def main():
    print('Работает')
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())