from __future__ import annotations

import functools
import os
from pathlib import Path
import typing as _t

from loguru import logger
from pawlogger import get_loguru
from pydantic import HttpUrl, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from scrapaw.scrapaw_config import ScrapawConfig


# @functools.lru_cache
# def dtg_env_from_env():
#     guru_env = os.getenv('GURU_ENV')
#     print(guru_env)
#     if not guru_env or not Path(guru_env).exists():
#         raise ValueError('GURU_ENV (path to environment file) not set')
#     return guru_env


@functools.lru_cache
def reddit_env_from_env():
    reddit_env = os.getenv('REDDIT_ENV')
    if not reddit_env or not Path(reddit_env).exists():
        raise ValueError('REDDIT_ENV (path to environment file) not set')
    return reddit_env


class RedditConfig(BaseSettings):
    refresh_token: SecretStr
    client_id: str
    client_secret: SecretStr
    user_agent: str

    custom_flair_id: SecretStr | None = None
    redirect_uri: str

    send_key: SecretStr

    subreddit_name: str = 'test'
    wiki_name: str = 'test'

    max_red_dupes: int = 1000

    model_config = SettingsConfigDict(env_ignore_empty=True, env_file=reddit_env_from_env(), extra='ignore')


class DTGConfig(BaseSettings):
    guru_frontend: Path | None = None
    guru_data: Path
    url_prefix: str = ''

    db_driver_path: Path | None = None

    podcast_url: HttpUrl = 'https://decoding-the-gurus.captivate.fm/'
    log_profile: _t.Literal['local', 'remote', 'default'] = 'local'

    db_loc: Path | None = None
    log_file: Path | None = None
    backup_dir: Path | None = None
    guru_update_json: Path | None = None
    guru_backup_json: Path | None = None

    init_eps: bool = False
    debug: bool = False
    max_dupes: int = 5  # 1 page in captivate
    scrape_limit: int | None = None

    # @field_validator('scrape_limit', mode='before')
    # def fix_int(cls, v):
    #     if not v:
    #         return None

    @model_validator(mode='after')
    def set_paths(self):
        self.db_loc = self.db_loc or self.guru_data / 'guru.db'
        self.backup_dir = self.backup_dir or self.guru_data / 'backup'
        if not self.backup_dir.exists():
            self.backup_dir.mkdir(parents=True)
        self.guru_backup_json = self.guru_backup_json or self.backup_dir / 'gurus.json'
        self.log_file = self.log_file or self.guru_data / 'logs' / 'dtgbot.log'
        self.db_driver_path = self.db_driver_path or f'sqlite:///{self.db_loc}'
        self.guru_update_json = self.guru_update_json or self.guru_data / 'guru_init.json'
        if not self.guru_frontend or not self.guru_frontend.exists():
            try:
                fe_path = Path(__file__).parent.parent / 'frontend'
                assert fe_path.exists()
                self.guru_frontend = fe_path
            except AssertionError as e:
                logger.exception(e)
                raise
        return self

    @functools.cached_property
    def scrap_config(self):
        return ScrapawConfig(
            log_file=self.log_file,
            podcast_url=self.podcast_url,
            debug=self.debug,
            max_dupes=self.max_dupes,
            scrape_limit=self.scrape_limit,
            _env_file=None,
            _env_ignore_empty=True,
        )

    model_config = SettingsConfigDict()
    # model_config = SettingsConfigDict(env_ignore_empty=True, env_file=dtg_env_from_env())


@functools.lru_cache
def dtg_sett():
    sett = DTGConfig()
    logger = get_loguru(log_file=sett.log_file, profile=sett.log_profile)
    logger.info('DTGBotConfig loaded')
    return sett


@functools.lru_cache
def reddit_sett():
    return RedditConfig()
