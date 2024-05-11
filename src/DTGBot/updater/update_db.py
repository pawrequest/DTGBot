import asyncio
from asyncio import gather

import sqlmodel
from aiohttp import ClientSession
from loguru import logger
from sqlmodel import select

from DTGBot.common.dtg_config import dtg_sett
from DTGBot.common.database import create_db, engine_
from DTGBot.common.dtg_types import quiet_cancel
from DTGBot.common.models.guru_m import Guru
from DTGBot.updater.updaters import (
    backup_gurus,
    get_eps,
    get_reddits,
    gurus_from_file,
    update_relationships, update_gurus,
)

dtg_settings = dtg_sett()


@quiet_cancel
async def main():
    try:
        create_db()
        with sqlmodel.Session(engine_()) as session:
            if dtg_settings.guru_update_json.exists():
                logger.info(f'updating from {dtg_settings.guru_update_json}')
                gurus = gurus_from_file()
                await update_gurus(session, gurus)

            async for reddit in get_reddits(session):
                session.add(reddit)
                session.commit()

            async with ClientSession() as http_session:
                async for ep in get_eps(session, http_session):
                    session.add(ep)
                    session.commit()

            gurus = session.exec(select(Guru)).all()
            await gather(*[update_relationships(db_guru, session) for db_guru in gurus])

            logger.warning('update complete')
    finally:
        await http_session.close()
        await backup_gurus()


if __name__ == '__main__':
    asyncio.run(main())
