import functools

from loguru import logger
from sqlalchemy import func
from sqlmodel import and_, col, desc, not_, or_, select

from DTGBot.common.models.episode_m import Episode
from DTGBot.common.models.guru_m import Guru
from DTGBot.common.models.links import GuruEpisodeLink, GuruRedditLink
from DTGBot.common.models.reddit_m import RedditThread
from DTGBot.fapi.shared import Pagination


async def search_column(table, column, search_str: str):
    search = f'%{search_str}%'
    return select(table).where(col(column).ilike(search))


async def search_guru_and_title(model, search_string: str):
    condition1 = col(Guru.name).ilike(f'%{search_string}%')
    condition2 = col(model.title).ilike(f'%{search_string}%')
    return select(model).where(or_(condition1, condition2))


async def search_gurus(search_str: str):
    return select(Guru).where(col(Guru.name).ilike(f'%{search_str}%'))


async def search_in_title(model, search_str: str):
    return select(model).where(col(model.title).ilike(f'%{search_str}%'))


async def search_column_array(table, column, search_strs: list[str], excludes: list[str] | None = None):
    excludes = excludes or []
    yes_cond = [col(column).ilike(f'%{search_str}%') for search_str in search_strs]
    no_cond = [not_(col(column).ilike(f'%{search_str}%')) for search_str in excludes]
    return select(table).where(and_(or_(*yes_cond), *no_cond))


async def search_column_specific(table, column, search_strs: list[str], excludes: list[str] | None = None):
    logger.info(f'{search_strs=}')
    logger.info(f'{excludes=}')

    excludes = excludes or []
    yes_cond = [column == search_str for search_str in search_strs]
    no_cond = [not_(column.ilike(f'%{search_str}%')) for search_str in excludes]
    return select(table).where(and_(or_(*yes_cond, *no_cond)))


async def select_episodes_with_guru(guru):
    return select(Episode).where(
        and_(
            or_(
                col(Episode.title).ilike(f'%{guru.name}%'),
                col(Episode.notes).ilike(f'%{guru.name}%'),
                col(Episode.links).ilike(f'%{guru.name}%'),
                *[col(Episode.title).ilike(f'%{_}%') for _ in guru.include_strs],
            ),
            *[not_(col(Episode.title).ilike(f'%{exclude}%')) for exclude in guru.exclude_strs],
        )
    )


async def select_threads_with_guru(guru):
    return select(RedditThread).where(col(RedditThread.title).ilike(f'%{guru.name}%'))


async def select_episodes_with_reddit(reddit: RedditThread):
    return select(Episode).where(
        or_(
            col(Episode.title).ilike(f'%{reddit.title}%'),
            col(Episode.notes).ilike(f'%{reddit.title}%'),
            col(Episode.links).ilike(f'%{reddit.title}%'),
        )
    )

async def select_threads_with_episode(episode: Episode):
    return select(RedditThread).where(col(RedditThread.title).ilike(f'%{episode.title}%'))



async def select_new_threads_with_episode(episode: Episode):
    stmt = await select_threads_with_episode(episode)
    return stmt.where(not_(col(RedditThread.reddit_id).in_([_.reddit_id for _ in episode.reddit_threads])))

    # return stmt.where(not_(episode in RedditThread.episodes))


async def select_new_eps_with_reddit(reddit: RedditThread):
    stmt = await select_episodes_with_reddit(reddit)
    return stmt.where(not_(col(Episode.id).in_([_.id for _ in reddit.episodes]))).where(
        not_(col(Episode.title).in_([_.title for _ in reddit.episodes]))
    )

    # return stmt.where(not_(reddit in Episode.reddit_threads))


async def select_new_threads_with_guru(guru):
    stmt = await select_threads_with_guru(guru)
    return stmt.where(not_(col(RedditThread.id).in_([_.id for _ in guru.reddit_threads])))

    # return stmt.where(not_(guru in RedditThread.gurus))


async def select_new_eps_with_guru(guru):
    stmt = await select_episodes_with_guru(guru)
    return stmt.where(not_(col(Episode.id).in_([_.id for _ in guru.episodes])))
    # return stmt.where(not_(guru in Episode.gurus))


async def search_related_column(table, link_table, related_table, related_col, search_str):
    search = f'%{search_str}%'
    return select(table).join(link_table).join(related_table).where(col(related_col).ilike(search))


eps_by_guruname = functools.partial(search_related_column, Episode, GuruEpisodeLink, Guru, Guru.name)
reddit_by_guruname = functools.partial(search_related_column, RedditThread, GuruRedditLink, Guru, Guru.name)
GURU_INTEREST = func.count(GuruEpisodeLink.guru_id) + func.count(GuruRedditLink.guru_id)


async def gurus_w_interest():
    stmt = (
        select(Guru)
        .join(GuruEpisodeLink, isouter=True)
        .join(GuruRedditLink, isouter=True)
        .group_by(Guru.id)
        .having(GURU_INTEREST > 0)
        .order_by(desc(GURU_INTEREST))
    )
    return stmt


async def select_page_more(session, sqlselect, pagination: Pagination) -> tuple[list, bool]:
    stmt = sqlselect.offset(pagination.offset).limit(pagination.limit + 1)
    res = session.exec(stmt).all()
    more = len(res) > pagination.limit
    return res[: pagination.limit], more


async def new_links_array(model, search_col, search_strings: list, current_links, excludes: list[str] | None = None):
    stmt = await search_column_array(model, search_col, search_strings, excludes=excludes)
    existing_ids = [link.id for link in current_links]
    new_stmt = stmt.where(not_(col(model.id).in_(existing_ids)))
    return new_stmt


async def new_links(model, search_col, search_string: str, current_links):
    stmt = await search_column(model, search_col, search_string)
    existing_ids = [link.id for link in current_links]
    new_stmt = stmt.where(not_(col(model.id).in_(existing_ids)))
    return new_stmt


async def new_links2(model, search_col, search_string: str, current_links):
    # stmt = await search_column_bi_directional(model, search_col, search_string)
    stmt = await search_column(model, search_col, search_string)
    # stmt = await search_guru_and_title(model, search_string)

    existing_ids = [link.id for link in current_links]
    new_stmt = stmt.where(not_(col(model.id).in_(existing_ids)))
    return new_stmt


async def existing_links(model, search_col, search_strings, current_links):
    stmt = await search_column_array(model, search_col, search_strings)
    existing_ids = [link.id for link in current_links]
    new_stmt = stmt.where(col(model.id).in_(existing_ids))
    return new_stmt
