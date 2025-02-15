from __future__ import annotations

import functools
import os
import ssl
from pathlib import Path
import typing as _t

from loguru import logger
from pawlogger import get_loguru
from pydantic import HttpUrl, SecretStr, model_validator
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
    refresh_token: SecretStr
    client_id: str
    client_secret: SecretStr
    user_agent: str
    redirect_uri: str
    subreddit_name: str = 'test'
    max_red_dupes: int = 1000
    model_config = SettingsConfigDict(env_ignore_empty=True, env_file=reddit_env_from_env(), extra='ignore')


class GuruConfig(BaseSettings):
    # mandatory
    guru_data: Path | None = None

    # optional
    lets_encrypt: bool = False
    lets_encrypt_path: Path | None = None
    log_profile: _t.Literal['local', 'remote', 'default'] = 'local'
    podcast_url: HttpUrl = 'https://decoding-the-gurus.captivate.fm/'

    ## scrapaw
    debug: bool = False
    max_dupes: int = 5  # 1 page in captivate
    scrape_limit: int | None = None

    # calculated
    guru_frontend: Path | None = None
    url_prefix: str = ''
    db_driver_path: Path | None = None

    ssl_key: Path | None = None
    ssl_cert: Path | None = None


    db_loc: Path | None = None
    log_file: Path | None = None
    backup_dir: Path | None = None
    guru_update_json: Path | None = None
    guru_backup_json: Path | None = None

    @model_validator(mode='after')
    def calculate_paths(self):
        self.guru_data = self.guru_data or Path(__file__).parent.parent.parent.parent / 'data'
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
                return self
            except AssertionError as e:
                print('ERROR:', e)
                raise

    @model_validator(mode='after')
    def set_ssl(self):
        logger.info(f'{self.lets_encrypt=}')
        if not self.lets_encrypt:
            return self
        if not self.lets_encrypt_path or not self.lets_encrypt_path.exists():
            raise ValueError('lets_encrypt_path must be set and exist')
        logger.info(f'setting ssl paths relative to  {self.lets_encrypt_path=}')
        self.ssl_key = self.lets_encrypt_path / 'privkey.pem'
        self.ssl_cert = self.lets_encrypt_path / 'fullchain.pem'
        return self


    @functools.cached_property
    def scrap_config(self):
        return ScrapawConfig(
            log_file=self.log_file,
            podcast_url=self.podcast_url,
            debug=self.debug,
            max_dupes=self.max_dupes,
            scrape_limit=self.scrape_limit,
            # _env_file=None,
            # _env_ignore_empty=True,
        )

    model_config = SettingsConfigDict()
    # model_config = SettingsConfigDict(env_ignore_empty=True, env_file=dtg_env_from_env())


@functools.lru_cache
def dtg_sett():
    sett = GuruConfig()
    logger = get_loguru(log_file=sett.log_file, profile=sett.log_profile)
    logger.info('DTGBotConfig loaded')
    return sett


@functools.lru_cache
def reddit_sett():
    return RedditConfig()
