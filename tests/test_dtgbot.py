import pytest
from DTGBot.models.guru_config import DTGBotConfig


def test_1():
    guru_conf = DTGBotConfig()
    reddit_config = RedditConfig()


@pytest.mark.asyncio
async def test_2():
    async with DTG() as dtg:
        await dtg.run()
