import pytest
from DTGBot.common.dtg_config import GuruConfig, RedditConfig
from DTGBot.updater.dtg_bot import DTG


def test_1():
    guru_conf = GuruConfig()
    reddit_config = RedditConfig()


@pytest.mark.asyncio
async def test_2():
    async with DTG() as dtg:
        await dtg.run()
