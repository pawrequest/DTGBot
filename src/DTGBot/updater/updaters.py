import datetime
import json
from collections.abc import AsyncGenerator, Sequence

from aiohttp import ClientSession
from asyncpraw import Reddit
from loguru import logger
from scrapaw import episode_generator
from sqlmodel import Session, col, not_, select

from DTGBot.common.database import engine_
from DTGBot.common.dtg_config import dtg_sett, reddit_sett
from DTGBot.common.models.episode_m import Episode
from DTGBot.common.models.guru_m import Guru, GuruBase
from DTGBot.common.models.reddit_m import RedditThread
from DTGBot.fapi.sql_stmts import (
    gurus_w_interest,
    select_episodes_with_guru,
    select_threads_with_guru,
)

dtg_settings = dtg_sett()
r_settings = reddit_sett()


def get_log_str(objs):
    return f'{len(objs)} {type(objs[0]).__name__}s: {'; '.join([obj.title if hasattr(obj, 'title') else obj.name for obj in objs])}'


async def update_guru(guru_update: dict, session):
    db_guru_stmt = select(Guru).where(Guru.name == guru_update['name'])
    if db_guru := session.exec(db_guru_stmt).first():
        for key, value in guru_update.items():
            if not key == 'name' and hasattr(db_guru, key):
                logger.info(f'{guru_update['name']}: {key} = {value}')
                setattr(db_guru, key, value)
    else:
        logger.info(f'creating new guru: {guru_update['name']}')
        db_guru = Guru.model_validate(guru_update)
    session.add(db_guru)
    session.commit()


async def update_relationships(db_guru: Guru, session):
    thrd_stmt = await select_threads_with_guru(db_guru.name)
    new_thrd_stmt = thrd_stmt.where(not_(col(RedditThread.id).in_([_.id for _ in db_guru.reddit_threads])))
    if new_threads := session.exec(new_thrd_stmt).all():
        logger.info(f'{db_guru.name} matched {get_log_str(new_threads)}')
        db_guru.reddit_threads.extend(new_threads)

    ep_stmt = await select_episodes_with_guru(db_guru)
    new_ep_stmt = ep_stmt.where(not_(col(Episode.id).in_([_.id for _ in db_guru.episodes])))
    if new_eps := session.exec(new_ep_stmt).all():
        logger.info(f'{db_guru.name} matched {get_log_str(new_eps)}')
        db_guru.episodes.extend(new_eps)

    session.add(db_guru)
    session.commit()


async def get_eps(session: Session, http_session: ClientSession) -> AsyncGenerator[Episode, None]:
    dupes = 0
    max_dupes = dtg_settings.max_dupes
    async for ep_ in episode_generator(dtg_settings.scrap_config, http_session):
        ep = Episode.model_validate(ep_)
        episode__all = session.exec(select(Episode)).all()

        if ep in episode__all:
            dupes += 1
            logger.debug(f'Duplicate Episode: {ep.title}', category='episode')
            if max_dupes is not None and dupes > max_dupes:
                logger.info('Reached max duplicates')
                break
            continue

        logger.info(f'Found New Episode: {ep.title}', category='episode')
        ep_ = Episode.model_validate(ep)
        yield ep_


async def get_reddits(session: Session, max_dupes: int = None):
    dupes = 0
    max_dupes = max_dupes or r_settings.max_red_dupes

    async with Reddit(
        client_id=r_settings.client_id,
        client_secret=r_settings.client_secret.get_secret_value(),
        user_agent=r_settings.user_agent,
        redirect_uri=r_settings.redirect_uri,
        refresh_token=r_settings.refresh_token.get_secret_value(),
    ) as redd:
        subb = await redd.subreddit(r_settings.subreddit_name)

        all_thread_ids = session.exec(select(RedditThread.reddit_id)).all()
        # async for sub in subb.new():
        async for sub in subb.top(limit=None, time_filter='all'):
            if sub.id in all_thread_ids:
                logger.debug(
                    f'Duplicate Reddit Thread: {sub.title}, {datetime.datetime.fromtimestamp(sub.created_utc)}',
                    category='reddit',
                )
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
        if dtg_settings.gurus_json:
            stmt = await gurus_w_interest()
            gurus = session.exec(stmt).all()
            gurus_base = [GuruBase.model_validate(guru) for guru in gurus]
            gurus_dicts = [{k: v} for _ in gurus_base for k, v in _.model_dump().items() if v]
            with open(dtg_settings.gurus_json, 'w') as backup_file:
                logger.info(f'writing backup to {backup_file}')
                json.dump(gurus_dicts, backup_file, indent=2)


def gurus_from_file() -> list[dict]:
    with open(dtg_settings.guru_update_json) as update_file:
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
