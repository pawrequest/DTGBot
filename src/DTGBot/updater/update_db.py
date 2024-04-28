import asyncio

from DTGBot.common.database import create_db
from DTGBot.common.dtg_types import quiet_cancel
from DTGBot.updater.dtg_bot import DTG


@quiet_cancel
async def main():
    create_db()
    async with DTG() as dtg:
        await dtg.run()


if __name__ == '__main__':
    asyncio.run(main())
