import functools

from loguru import logger
from sqlalchemy import create_engine, delete, text
from sqlmodel import SQLModel, Session, col

from DTGBot.common.dtg_config import dtg_sett
from DTGBot.common import dtg_config
from DTGBot.common.models.episode_m import Episode


@functools.lru_cache
def get_db_url():
    sett = dtg_sett()
    logger.info(f'USING DB FILE: {sett.db_loc}')
    return f'sqlite:///{sett.db_loc}'


@functools.lru_cache
def engine_():
    db_url = get_db_url()
    # db_url = dtg_sett().db_driver_path
    connect_args = {'check_same_thread': False}
    return create_engine(db_url, echo=dtg_config.dtg_sett().debug, connect_args=connect_args)


def get_session(engine=None) -> Session:
    if engine is None:
        engine = engine_()
    with Session(engine) as session:
        yield session
    session.close()


def create_db(engine=None):
    if engine is None:
        engine = engine_()
    from DTGBot.common.dtg_types import DB_MODEL_TYPE, LINK_TYPES  # noqa: F401

    SQLModel.metadata.create_all(engine)
    logger.info('tables created')


def trim_db2(session: Session):
    ep_trim = 155
    red_trim = 1006
    # stmt = select(Episode).where(Episode.id <= ep_trim)
    # session.delete(Episode, Episode.id <= ep_trim)
    statement = delete(Episode).where(col(Episode.id) <= ep_trim)
    session.exec(statement)  # type:ignore[call-overload]
    session.commit()


def trim_db(session):
    ep_trim = 153
    red_trim = 0
    stmts = [
        text(_)
        for _ in [
            f'delete from guruepisodelink where episode_id >={ep_trim}',
            f'delete from episoderedditlink where episode_id >={ep_trim}',
            f'delete from episoderedditlink where reddit_thread_id >={red_trim}',
            f'delete from gururedditlink where reddit_thread_id >={red_trim}',
            f'delete from episode where id >={ep_trim}',
            f'delete from redditthread where id >={red_trim}',
        ]
    ]
    try:
        [session.execute(_) for _ in stmts]
        session.commit()
        logger.warning(f'DB TRIMMED TO EPISODE #{ep_trim} REDDITTHREAD #{red_trim}')
    except Exception as e:
        logger.error(e)
