import functools

from sqlalchemy import func
from sqlmodel import col, desc, select

from DTGBot.common.models.episode_m import Episode
from DTGBot.common.models.guru_m import Guru
from DTGBot.common.models.links import GuruEpisodeLink, RedditThreadGuruLink
from DTGBot.common.models.reddit_m import RedditThread
from DTGBot.fapi.shared import Pagination


async def by_column(table, column, search_str):
    search = f'%{search_str}%'
    return (
        select(table)
        .where(col(column).ilike(search))
    )


async def by_related_column(table, link_table, related_table, related_col, search_str):
    search = f'%{search_str}%'
    return (
        select(table)
        .join(link_table)
        .join(related_table)
        .where(col(related_col).ilike(search))
    )


eps_by_guruname = functools.partial(by_related_column, Episode, GuruEpisodeLink, Guru, Guru.name)
reddit_by_guruname = functools.partial(
    by_related_column,
    RedditThread,
    RedditThreadGuruLink,
    Guru,
    Guru.name
)
GURU_INTEREST = func.count(GuruEpisodeLink.guru_id) + func.count(RedditThreadGuruLink.guru_id)


async def gurus_w_interest():
    stmt = (
        select(Guru)
        .join(GuruEpisodeLink, isouter=True)
        .join(RedditThreadGuruLink, isouter=True)
        .group_by(Guru.id)
        .having(GURU_INTEREST > 0)
        .order_by(desc(GURU_INTEREST))
    )
    return stmt


async def select_page_more(session, sqlselect, pagination: Pagination) -> tuple[list, bool]:
    stmt = sqlselect.offset(pagination.offset).limit(pagination.limit + 1)
    res = session.exec(stmt).all()
    more = len(res) > pagination.limit
    return res[:pagination.limit], more
