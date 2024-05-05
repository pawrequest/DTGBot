import pytest
from DTGBot.common.dtg_config import DTGConfig, RedditConfig
from DTGBot.updater.dtg_bot import DTG


def test_1():
    guru_conf = DTGConfig()
    reddit_config = RedditConfig()


@pytest.mark.asyncio
async def test_2():
    async with DTG() as dtg:
        await dtg.run()
