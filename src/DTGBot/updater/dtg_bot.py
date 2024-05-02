import asyncio
from asyncio import Queue, Task, gather

import pydantic as _p
import sqlmodel as sqm
from aiohttp import ClientSession
from asyncpraw import Reddit
from asyncpraw.reddit import Subreddit
from loguru import logger
from pydantic import alias_generators
from sqlmodel import select

from DTGBot.common.database import engine_
from DTGBot.common.dtg_types import DB_MODEL_TYPE, quiet_cancel, title_or_name_val
from DTGBot.common.dtg_config import DTGBotConfig, RedditConfig, dtgb_sett, reddit_sett
from DTGBot.common.models import episode_m, guru_m, reddit_m
from DTGBot.common.models.episode_m import Episode
from DTGBot.common.models.guru_m import Guru
from DTGBot.common.models.reddit_m import RedditThread
from scrapaw import dtg

type EndOfStream = object


class DTG:
    def __init__(
            self,
            reddit_settings: RedditConfig | None = None,
            dtgb_settings: DTGBotConfig | None = None,
    ):
        """Decoding The Gurus Bot

        Attributes:
            reddit_settings (RedditConfig): Reddit Configuration
            dtgb_settings (DTGBotConfig): DTGBot Configuration
        """
        self.r_settings = reddit_settings or reddit_sett()
        self.d_settings = dtgb_settings or dtgb_sett()
        self.episode_q = Queue()
        self.reddit_q = Queue()
        self.guru_q = Queue()
        self.tasks: list[Task] = list()
        self.reddit: Reddit | None = None
        self.subreddit: Subreddit | None = None
        self.http_session: ClientSession | None = None
        self.sqm_session: sqm.Session | None = None

    async def __aenter__(self):
        self.http_session = ClientSession()
        self.sqm_session = sqm.Session(engine_())
        self.reddit = Reddit(
            client_id=self.r_settings.client_id,
            client_secret=self.r_settings.client_secret,
            user_agent=self.r_settings.user_agent,
            redirect_uri=self.r_settings.redirect_uri,
            refresh_token=self.r_settings.refresh_token,
        )
        self.subreddit = await self.reddit.subreddit(self.r_settings.subreddit_name)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.reddit.close()
        self.sqm_session.close()
        await self.http_session.close()

    async def run(self):
        """Run the bot

        spawn queue managers and processors for episodes and reddit threads
        """
        logger.info('Initialised')
        self.tasks = [
            asyncio.create_task(self.get_episodes()),
            asyncio.create_task(self.get_reddit_threads()),
            asyncio.create_task(self.get_gurus()),
            asyncio.create_task(
                self.process_queue(
                    self.reddit_q,
                    reddit_m.RedditThread,
                    log_category='reddit',
                    relation_classes=[episode_m.Episode, guru_m.Guru],
                )
            ),
            asyncio.create_task(
                self.process_queue(
                    self.episode_q,
                    episode_m.Episode,
                    log_category='episode',
                    relation_classes=[reddit_m.RedditThread, guru_m.Guru],
                )
            ),
            asyncio.create_task(
                self.process_queue(
                    self.guru_q,
                    Guru,
                    log_category='episode',
                    relation_classes=[RedditThread, Episode],
                )
            ),
        ]
        logger.info('Tasks created')
        await gather(*self.tasks)
        logger.info('Tasks completed')
        return None

    async def get_gurus(self):
        with open(self.d_settings.guru_names_file) as f:
            guru_names = f.read().split(',')
        session_gurus = self.sqm_session.exec(sqm.select(guru_m.Guru.name)).all()
        if new_gurus := set(guru_names) - set(session_gurus):
            logger.info(f'Adding {len(new_gurus)} new gurus')
            gurus = [guru_m.Guru(name=_) for _ in new_gurus]
            [await self.guru_q.put(guru) for guru in gurus]
        await self.guru_q.put(EndOfStream)

    async def get_episodes(self):
        """Get episodes from the podcast feed and add them to the episode queue"""
        logger.debug('Getting Episodes', category='episode')
        max_dupes = self.d_settings.max_dupes
        episode__all = self.sqm_session.exec(select(episode_m.Episode)).all()

        dupes = 0
        async for ep_ in dtg.episode_generator(
                self.d_settings.scrap_config, self.http_session
        ):
            ep = episode_m.Episode.model_validate(ep_)
            if ep.get_hash in [_.get_hash for _ in episode__all]:
                dupes += 1
                logger.debug(f'Duplicate Episode: {ep.title}', category='episode')
                if max_dupes is not None and dupes > max_dupes:
                    break
                continue

            logger.debug(f'Found Episode: {ep.title}', category='episode')
            await self.episode_q.put(ep)

        logger.debug('Episode Generator Completed', category='episode')
        await self.episode_q.put(EndOfStream)
        return None

    async def get_reddit_threads(self) -> None:
        """Get Reddit Threads from the subreddit and add them to the reddit queue """
        max_dupes = self.d_settings.max_dupes
        dupes = 0
        thread__all = self.sqm_session.exec(select(RedditThread)).all()
        async for sub in self.subreddit.stream.submissions(skip_existing=False):
            thrd = reddit_m.RedditThread.from_submission(sub)
            if thrd.get_hash in [_.get_hash for _ in thread__all]:
                dupes += 1
                if max_dupes is not None and dupes > max_dupes:
                    break
                continue

            logger.info(f'Found Reddit Thread: {thrd.title}', category='reddit')
            await self.reddit_q.put(thrd)

        logger.debug('Reddit Generator Complete', category='reddit')
        await self.reddit_q.put(EndOfStream)
        return None

    @quiet_cancel
    async def process_queue(
            self,
            queue,
            model_class: type(_p.BaseModel),
            relation_classes: list[type(_p.BaseModel)],
            log_category: str = 'General',
    ):
        """Process items from the queue - validate and add to the database, assign related items

        Args:
            queue (Queue): Queue to process
            model_class (type): Model class to validate
            relation_classes (list[type]): List of related classed to check for matches
            log_category (str): organise log entries into categories
        """
        while True:
            item_ = await queue.get()
            if item_ is EndOfStream:
                logger.debug(f'{model_class.__name__} EndOfStream', category=log_category)
                return None

            item = model_class.model_validate(item_)
            await self.process_item(item, relation_classes, log_category)
            queue.task_done()
            item_str = f'{item.__class__.__name__} - {title_or_name_val(item)}'
            logger.info(f'Processed {item_str}', category=log_category)

    async def process_item(
            self,
            item,
            relation_classes: list[type(_p.BaseModel)],
            log_category: str = 'General',
    ):
        item_str = f'{item.__class__.__name__} - {title_or_name_val(item)}'
        logger.debug(f'Processing {item_str}', category=log_category)

        self.sqm_session.add(item)
        for relation_class in relation_classes:
            await self.assign_rel(item, relation_class)

        self.sqm_session.commit()

    async def assign_rel(self, item, relation_class):
        """Add related items to the item"""
        related_items = db_obj_matches(self.sqm_session, item, relation_class) if not isinstance(
            item,
            relation_class
        ) else []
        alias = alias_generators.to_snake(relation_class.__name__) + 's'
        getattr(item, alias).extend(related_items)


def db_obj_matches[T:DB_MODEL_TYPE](session: sqm.Session, obj: DB_MODEL_TYPE, model: type[T]) -> \
        list[
            T]:
    """Get matching objects from the database

    # todo much better logic here

    Args:
        session (sqlmodel.Session): Database session
        obj (DB_MODEL_TYPE): Object to match
        model (type): Model to match against

    Returns:
        list: List of matching objects

    """

    db_objs = session.exec(sqm.select(model)).all()
    title_or_name_value = title_or_name_val(obj)
    title_or_name = title_or_name_var(model)

    if matched_tag_models := [
        _ for _ in db_objs
        if one_in_other(_, title_or_name, title_or_name_value)
    ]:
        logger.debug(
            f"Found {len(matched_tag_models)} '{model.__name__}' {'match' if len(matched_tag_models) == 1 else 'matches'} for {obj.__class__.__name__} - {title_or_name_value}"
        )
    return matched_tag_models


def title_or_name_var(obj):
    return 'title' if hasattr(obj, 'title') else 'name'


def one_in_other(obj: DB_MODEL_TYPE, obj_var: str, compare_val: str) -> bool:
    """Check if one string is in another

    Args:
        obj (DB_MODEL_VAR): Object to check
        obj_var (str): Attribute to check
        compare_val (str): Value to compare

    Returns:
        bool: True if one string is in the other
    """
    ob_low = getattr(obj, obj_var).lower()
    return ob_low in compare_val.lower() or compare_val.lower() in ob_low


def gurus_from_file(session):
    """Add gurus from a file to the database"""
    infile = DTGBotConfig.guru_names_file
    with open(infile) as f:
        guru_names = f.read().split(',')
    session_gurus = session.exec(sqm.select(guru_m.Guru.name)).all()
    if new_gurus := set(guru_names) - set(session_gurus):
        logger.info(f'Adding {len(new_gurus)} new gurus')
        gurus = [guru_m.Guru(name=_) for _ in new_gurus]
        session.add_all(gurus)
        session.commit()
