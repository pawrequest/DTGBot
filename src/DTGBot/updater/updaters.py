import json
from collections.abc import AsyncGenerator, Sequence
import sys
import asyncio

from aiohttp import ClientSession
from asyncpraw import Reddit
from loguru import logger
from scrapaw import episode_generator
from sqlmodel import Session, select

from DTGBot.common.database import engine_
from DTGBot.common.dtg_config import dtg_sett, reddit_sett
from DTGBot.common.models.episode_m import Episode
from DTGBot.common.models.guru_m import Guru, GuruBase
from DTGBot.common.models.reddit_m import RedditThread
from DTGBot.fapi.sql_stmts import (
    gurus_w_interest,
    select_new_eps_with_guru,
    select_new_eps_with_reddit,
    select_new_threads_with_episode,
    select_new_threads_with_guru,
)

DTG_SETTINGS = dtg_sett()
R_SETTINGS = reddit_sett()


async def spin(msg, delay=0.3):
    symbols = '|/-\\'  # Spinner symbols
    idx = 0
    try:
        while True:
            sys.stdout.write('\r' + msg + ' ' + symbols[idx])
            sys.stdout.flush()
            idx = (idx + 1) % len(symbols)
            await asyncio.sleep(delay)
    except asyncio.CancelledError:
        sys.stdout.write('\r' + msg + ' Done\n')
        sys.stdout.flush()


def get_log_str(objs):
    return f'{len(objs)} {type(objs[0]).__name__}s: \n{';\n'.join([obj.title if hasattr(obj, 'title') else obj.name for obj in objs])}'


async def update_guru(guru_update: dict, session):
    db_guru_stmt = select(Guru).where(Guru.name == guru_update['name'])
    if db_guru := session.exec(db_guru_stmt).first():
        for key, value in guru_update.items():
            if not key == 'name' and hasattr(db_guru, key):
                logger.info(f'{guru_update['name']}: {key} = {value}')
                setattr(db_guru, key, value)
    else:
        logger.info(f'creating new guru: {guru_update['name']}', category='GURU')
        db_guru = Guru.model_validate(guru_update)
    session.add(db_guru)
    session.commit()


async def update_guru_links(db_guru: Guru, session):
    thrd_stmt = await select_new_threads_with_guru(db_guru)
    if new_threads := session.exec(thrd_stmt).all():
        logger.info(f'"{db_guru.name}" matched {get_log_str(new_threads)}', category='GURU-MATCH')
        db_guru.reddit_threads.extend(new_threads)

    ep_stmt = await select_new_eps_with_guru(db_guru)
    if new_eps := session.exec(ep_stmt).all():
        logger.info(f'"{db_guru.name}" matched {get_log_str(new_eps)}', category='GURU-MATCH')
        db_guru.episodes.extend(new_eps)
    session.add(db_guru)
    session.commit()


async def update_episode_reddits(episode: Episode, session: Session):
    stmt = await select_new_threads_with_episode(episode)
    if new_threads := session.exec(stmt).all():
        logger.info(f'"{episode.title}" matched {get_log_str(new_threads)}', category='EP-MATCH')
        episode.reddit_threads.extend(new_threads)
    # else:
    #     logger.debug(f'No new threads matched {episode.title}', category='EP-MATCH')



async def update_reddit_episodes(reddit: RedditThread, session: Session):
    stmt = await select_new_eps_with_reddit(reddit)
    if new_eps := session.exec(stmt).all():
        logger.warning(f'"{reddit.title}" matched {get_log_str(new_eps)}', category='RED-MATCH')
        reddit.episodes.extend(new_eps)
    # else:
    #     logger.debug(f'No new episodes matched {reddit.title}', category='RED-MATCH')
    session.add(reddit)
    session.commit()


async def get_eps(session: Session, http_session: ClientSession) -> AsyncGenerator[Episode, None]:
    dupes = 0
    max_dupes = DTG_SETTINGS.max_dupes
    async for ep_ in episode_generator(DTG_SETTINGS.scrap_config, http_session):
        ep = Episode.model_validate(ep_)
        episode__all = session.exec(select(Episode)).all()

        if ep in episode__all:
            dupes += 1
            if max_dupes is not None and dupes > max_dupes:
                logger.info('Reached max duplicates')
                break
            continue

        ep_ = Episode.model_validate(ep)
        logger.info(f'Episode updater found new episode: "{ep.title}"', category='episode')
        yield ep_


async def get_reddits(session: Session, max_dupes: int = None):
    dupes = 0
    max_dupes = max_dupes or R_SETTINGS.max_red_dupes

    async with Reddit(
        client_id=R_SETTINGS.client_id,
        client_secret=R_SETTINGS.client_secret.get_secret_value(),
        user_agent=R_SETTINGS.user_agent,
        redirect_uri=R_SETTINGS.redirect_uri,
        refresh_token=R_SETTINGS.refresh_token.get_secret_value(),
    ) as redd:
        subb = await redd.subreddit(R_SETTINGS.subreddit_name)
        all_thread_ids = session.exec(select(RedditThread.reddit_id)).all()

        # async for sub in subb.new():
        async for sub in subb.top(limit=None, time_filter='all'):
            if sub.id in all_thread_ids:
                dupes += 1
                if max_dupes is not None and dupes > max_dupes:
                    logger.info(f'Reached max duplicate reddit threads ({max_dupes})')
                    break
                continue
            thrd = RedditThread.from_submission(sub)
            logger.info(f'Found New Reddit Thread: {thrd.title}', category='reddit')
            yield thrd


async def backup_gurus():
    with Session(engine_()) as session:
        if DTG_SETTINGS.guru_backup_json:
            stmt = await gurus_w_interest()
            gurus = session.exec(stmt).all()
            gurus_base = [GuruBase.model_validate(guru) for guru in gurus]
            gurus_dicts = [{k: v} for _ in gurus_base for k, v in _.model_dump().items() if v]
            with open(DTG_SETTINGS.guru_backup_json, 'w') as backup_file:
                logger.info(f'writing backup to {backup_file}')
                json.dump(gurus_dicts, backup_file, indent=2)


def gurus_from_file() -> list[dict]:
    with open(DTG_SETTINGS.guru_update_json) as update_file:
        gurus = json.load(update_file)
        return gurus


async def update_gurus(session: Session, gurus: Sequence[dict]):
    for guru in gurus:
        await update_guru(guru, session)


#
# async def update_reddit(reddit: RedditThread, session: Session):
#     logger.info(f'updating reddit: {reddit.title}')
#
#     guru_stmt = select(Guru).where(col(Guru.name).in_([reddit.title]))
#     # guru_stmt = await search_column_array(Guru, Guru.name, episode.title.split())
#     if gurus := session.exec(guru_stmt).all():
#         for guru in gurus:
#             if excludes := guru.exclude_strs:
#                 if any([_ in reddit.title for _ in excludes]):
#                     logger.info(f'skipping {guru.name}')
#                     continue
#             logger.info(f'adding {guru.name} to {reddit.title}')
#             reddit.gurus.append(guru)
#
#     session.add(reddit)
#     session.commit()
#
#
# async def update_titled(titled: RedditThread | Episode, session: Session):
#     logger.info(f'updating {type(titled).__name__}: {titled.title}')
#
#     if isinstance(titled, RedditThread):
#         guru_stmt = select(Guru).where(col(Guru.name).in_(titled.title))
#     elif isinstance(titled, Episode):
#         guru_stmt = select(Guru).where(
#             not_(col(Guru.episodes).contains(titled)).where(
#                 or_(
#                     col(Guru.name).in_([titled.title]),
#                     col(Guru.name).in_(titled.notes),
#                     col(Guru.name).in_(titled.links),
#                 ),
#             )
#         )
#     else:
#         raise ValueError(f'Invalid titled type: {type(titled)}')
#
#     # gurus = session.exec(guru_stmt).all()
#
#     if gurus := session.exec(guru_stmt).all():
#         logger.info(f'MATCHED {len(gurus)} GURUS: {get_log_str(gurus)}')
#         for guru in gurus:
#             if excludes := guru.exclude_strs:
#                 if any([_ in titled.title for _ in excludes]):
#                     logger.info(f'skipping {guru.name} due to exclusion {excludes=}')
#                     continue
#             logger.info(f'adding {guru.name} to {titled.title}')
#             titled.gurus.append(guru)
#     else:
#         logger.debug(f'No gurus matched {titled.title}')
#
#     session.add(titled)
#     session.commit()
