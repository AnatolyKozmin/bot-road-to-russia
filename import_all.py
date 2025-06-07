import asyncio
import os


from db.engine import async_sessionmaker
from excel_worker.excel_reader import create_location
from excel_worker.location_creator_excel import create_user_data


EXCEL_USERS = os.getenv("USERS_FILE", "user_data.xlsx")
EXCEL_CULT  = os.getenv("CULT_FILE",  "mero.xlsx")


async def main() -> None:
    await create_location()
    await create_user_data() 


if __name__ == "__main__":
    asyncio.run(main())
