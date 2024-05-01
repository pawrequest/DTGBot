import functools

from loguru import logger
from sqlalchemy import create_engine, text
from sqlmodel import SQLModel, Session

from DTGBot.common.dtg_config import dtgb_sett

from DTGBot.common import dtg_config


@functools.lru_cache
def get_db_url():
    sett = dtgb_sett()
    logger.info(f'USING DB FILE: {sett.db_loc}')
    return f'sqlite:///{sett.db_loc}'


@functools.lru_cache
def engine_():
    db_url = get_db_url()
    connect_args = {'check_same_thread': False}
    return create_engine(db_url, echo=False, connect_args=connect_args)


def get_session(engine=None) -> Session:
    if engine is None:
        engine = engine_()
    with Session(engine) as session:
        yield session
    session.close()


def create_db(engine=None):
    if engine is None:
        engine = engine_()
    from DTGBot.common.dtg_types import DB_MODEL_TYPE  # noqa: F401
    SQLModel.metadata.create_all(engine)


def trim_db(session):
    ep_trim = 108
    red_trim = 20
    stmts = [
        text(_)
        for _ in [
            f'delete from episode where id <={ep_trim}',
            f'delete from guruepisodelink where episode_id <={ep_trim}',
            f'delete from redditthreadepisodelink where episode_id <={ep_trim}',
            f'delete from redditthread where id <={red_trim}',
            f'delete from redditthreadepisodelink where reddit_thread_id <={red_trim}',
            f'delete from redditthreadgurulink where reddit_thread_id <={red_trim}',
        ]
    ]
    try:
        [session.execute(_) for _ in stmts]
        session.commit()
        logger.info('DB trimmed')
    except Exception as e:
        logger.error(e)
