import inspect
import re

import pytest
from loguru import logger as _logger
from asyncpraw import Reddit
from pawlogger.config_loguru import get_loguru
from sqlalchemy import StaticPool, create_engine
from sqlmodel import SQLModel, Session

from DTGBot.common.dtg_config import RedditConfig
from scrapaw.scrapaw_config import ScrapawConfig

TEST_DB = 'sqlite://'
ENGINE = create_engine(
    TEST_DB,
    connect_args={'check_same_thread': False},
    poolclass=StaticPool,
)


@pytest.fixture
def scrapaw_sett_():
    return ScrapawConfig()


@pytest.fixture
def reddit_sett():
    return RedditConfig()


@pytest.fixture(scope='session')
def test_sesh():
    engine = ENGINE
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


async def override_subreddit():
    try:
        reddit = Reddit()
        subreddit = await reddit.subreddit('test')
        yield subreddit
    finally:
        await reddit.close()


def override_session():
    try:
        session = Session(ENGINE)
        yield session
    finally:
        session.close()


#
#
def override_logger():
    logger = _logger
    logger.remove()
    return logger


#
# @pytest.fixture(scope="function")
def test_logger(tmp_path):
    logger = get_loguru('local')
    logger.remove()
    test_loc = tmp_path / 'test.log'
    logger.add(test_loc)
    logger.info('test')
    logged_line = inspect.getframeinfo(inspect.currentframe()).lineno - 1
    with open(test_loc) as f:
        LOG1 = f.readline()
    pat_xml = r'^(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}\.\d{3}\s)\|(\s[A-Z]*\s*)\|(\s.+:.+:\d+\s-\s.*)$'
    match = re.match(pat_xml, LOG1)

    assert match
    assert match.string.endswith(
        f' | INFO     | DTGBot.tests.conftest:test_logger:{logged_line} - test\n'
    )


@pytest.fixture(scope='session')
def test_db():
    SQLModel.metadata.create_all(ENGINE)

    # EpisodeBase.metadata.create_all(bind=ENGINE)
    # Episode.metadata.create_all(bind=ENGINE)
    yield
    SQLModel.metadata.drop_all(bind=ENGINE)
    # Episode.metadata.drop_all(bind=ENGINE)
