from __future__ import annotations

import functools
import os
from pathlib import Path
import typing as _t

from pawlogger import get_loguru
from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from scrapaw.scrapaw_config import ScrapawConfig


@functools.lru_cache
def dtg_env_from_env():
    guru_env = os.getenv('GURU_ENV')
    print(guru_env)
    if not guru_env or not Path(guru_env).exists():
        raise ValueError('GURU_ENV (path to environment file) not set')
    return guru_env


@functools.lru_cache
def reddit_env_from_env():
    reddit_env = os.getenv('REDDIT_ENV')
    if not reddit_env or not Path(reddit_env).exists():
        raise ValueError('REDDIT_ENV (path to environment file) not set')
    return reddit_env


class RedditConfig(BaseSettings):
    refresh_token: str
    client_id: str
    client_secret: str
    user_agent: str

    custom_flair_id: str | None = None
    redirect_uri: str

    send_key: str

    subreddit_name: str = 'test'
    wiki_name: str = 'test'

    model_config = SettingsConfigDict(
        env_ignore_empty=True,
        env_file=reddit_env_from_env(),
        extra='ignore'
    )


class DTGBotConfig(BaseSettings):
    guru_names_file: Path
    db_loc: Path
    log_file: Path
    log_profile: _t.Literal['local', 'remote', 'default'] = 'local'
    podcast_url: HttpUrl

    debug: bool = False

    sleep: int = 60 * 60  # 1 hour
    max_dupes: int = 5  # 1 page in captivate

    @functools.cached_property
    def scrap_config(self):
        return ScrapawConfig(
            log_file=self.log_file,
            podcast_url=self.podcast_url,
            debug=self.debug,
            max_dupes=self.max_dupes,
            scrape_limit=5 if self.debug else None,
            _env_file=None,
            _env_ignore_empty=True,
        )

    model_config = SettingsConfigDict(env_ignore_empty=True, env_file=dtg_env_from_env())


@functools.lru_cache
def dtgb_sett():
    sett = DTGBotConfig()
    logger = get_loguru(log_file=sett.log_file, profile=sett.log_profile)
    logger.info('DTGBotConfig loaded')
    return sett


@functools.lru_cache
def reddit_sett():
    return RedditConfig()
