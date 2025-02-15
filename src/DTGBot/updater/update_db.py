import asyncio
import sys
from asyncio import create_task, gather

import sqlmodel
from aiohttp import ClientSession
from loguru import logger
from sqlmodel import select

from DTGBot.common.dtg_config import guru_config
from DTGBot.common.database import create_db, engine_
from DTGBot.common.dtg_types import quiet_cancel
from DTGBot.common.models.guru_m import Guru
from DTGBot.updater.updaters import (
    backup_gurus,
    get_eps,
    get_reddits,
    gurus_from_file,
    spin,
    update_episode_reddits,
    update_guru_links,
    update_gurus,
    update_reddit_episodes,
)

DTG_SETTINGS = guru_config()


@quiet_cancel
async def main():
    try:
        create_db()
        with sqlmodel.Session(engine_()) as session:
            tasks = [
                create_task(import_gurus(session)),
                create_task(reddit_task(session)),
                create_task(episode_task(session)),
            ]
            await gather(*tasks)
            await guru_links_task(session)

            logger.warning('update complete')
    finally:
        await backup_gurus()


async def guru_links_task(session):
    gurus = session.exec(select(Guru)).all()
    await gather(*[update_guru_links(db_guru, session) for db_guru in gurus])


async def episode_task(session):
    if DTG_SETTINGS.log_profile == 'local':
        spinner = asyncio.create_task(spin('Fetching Episodes'))
    else:
        spinner = None
        logger.info('Fetching Episodes')
    try:
        async with ClientSession() as http_session:
            if new_eps := [_ async for _ in get_eps(session, http_session)]:
                logger.info(f'adding {len(new_eps)} episodes')
                sorted_eps = sorted(new_eps, key=lambda x: x.date)
                session.add_all(sorted_eps)
                [await update_episode_reddits(ep, session) for ep in sorted_eps]
                session.commit()
                await http_session.close()
    finally:
        if spinner:
            spinner.cancel()


async def import_gurus(session):
    if DTG_SETTINGS.guru_update_json.exists():
        logger.info(f'updating from {DTG_SETTINGS.guru_update_json}', category='GURU')
        gurus = gurus_from_file()
        await update_gurus(session, gurus)


async def reddit_task(session):
    if DTG_SETTINGS.log_profile == 'local':
        spinner = asyncio.create_task(spin('Fetching Reddit Threads'))
    else:
        spinner = None
        logger.info('Fetching Reddit Threads')
    try:
        async for reddit in get_reddits(session):
            await update_reddit_episodes(reddit, session)
    finally:
        if spinner is not None:
            spinner.cancel()


def run():
    asyncio.run(main())


if __name__ == '__main__':
    run()
    sys.exit(0)
