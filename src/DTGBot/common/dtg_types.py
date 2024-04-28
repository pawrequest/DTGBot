import asyncio

from loguru import logger

from DTGBot.common.models.episode_m import Episode
from DTGBot.common.models.guru_m import Guru
from DTGBot.common.models.reddit_m import RedditThread

DB_MODEL_TYPE = Guru | Episode | RedditThread


def quiet_cancel(func: callable) -> callable:
    """
    Async Decorator to catch CancelledError and log it quietly

    :param func: function to decorate
    :return: decorated function
    """

    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except asyncio.CancelledError:
            logger.info(f"'{func.__name__}' Cancelled")
        except Exception as e:
            logger.error(f"'{func.__name__}' raised {e}")
            raise e

    return wrapper


def title_or_name_val(obj) -> str:
    """
    Get the value of the title or name attribute on an object

    :param obj: object to get title or name from, must have one of those attributes
    :return: value of title or name attribute
    """

    res = getattr(obj, 'title', None) or getattr(obj, 'name')
    if not res:
        raise ValueError(f"Can't find title or name on {obj}")
    return res
