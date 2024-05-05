import typing as _t

import fastapi
import sqlmodel
from fastapi import Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import func
from sqlmodel import desc, select
from pawlogger.config_loguru import logger

from DTGBot.common.database import get_session
from DTGBot.common.models.guru_m import Guru
from DTGBot.common.models.reddit_m import RedditThread
from DTGBot.fapi.shared import (
    Pagination,
    get_pagination,
    select_page,
    templates,
)

router = fastapi.APIRouter()
SearchKind = _t.Literal['title', 'guru']


def thread_matches(
        session: sqlmodel.Session,
        search_str: str,
        pagination: Pagination,
        search_kind: SearchKind = 'title',
):
    match search_kind:
        case 'title':
            stmt = select(RedditThread).order_by(desc(RedditThread.created_datetime)).where(
                func.lower(RedditThread.title).like(f'%{search_str.lower()}%')
            )

        case 'guru':
            stmt = select(Guru).where(
                func.lower(Guru.name).like(f'%{search_str.lower()}%')
            )
            matching_gurus = session.exec(stmt).all()
            matching_threads = {thread for guru in matching_gurus for thread in guru.reddit_threads}
            return sorted(
                list(matching_threads)[pagination.offset:pagination.limit + pagination.offset],
                key=lambda thread: thread.created_datetime,
                reverse=True
            )

        case _:
            raise ValueError(f'Invalid kind: {search_kind}')

    stmt = select_page(stmt, pagination)
    return session.exec(stmt).all()


@router.get('/get/', response_class=HTMLResponse)
async def get_threads(
        request: Request, session: sqlmodel.Session = fastapi.Depends(get_session),
        pagination: Pagination = fastapi.Depends(get_pagination)
):
    stmt = select(RedditThread).order_by(desc(RedditThread.created_datetime))
    stmt = select_page(stmt, pagination)
    threads = session.exec(stmt).all()
    more = len(threads) == pagination.limit

    return templates().TemplateResponse(
        request=request,
        name='reddit/reddit_cards.html',
        context={'threads': threads, 'pagination': pagination, 'route_url': 'red', 'more': more}
    )


@router.post('/get/', response_class=HTMLResponse)
async def search_threads(
        request: Request,
        search_kind: SearchKind = Form(...),
        search_str: str = Form(...),
        session: sqlmodel.Session = fastapi.Depends(get_session),
        pagination: Pagination = fastapi.Depends(get_pagination)

):
    if search_kind and search_str:
        logger.debug(f'{search_kind=} {search_str=}')
        threads = thread_matches(session, search_str, pagination, search_kind)
    else:
        stmt = select(RedditThread).order_by(desc(RedditThread.created_datetime))
        stmt = select_page(stmt, pagination)
        threads = session.exec(stmt).all()

    more = len(threads) == pagination.limit

    return templates().TemplateResponse(
        request=request,
        name='reddit/reddit_cards.html',
        context={'threads': threads, 'pagination': pagination, 'route_url': 'red', 'more': more}
    )


@router.get('/', response_class=HTMLResponse)
async def red_index(
        request: Request,
):
    logger.debug('all_red')
    return templates().TemplateResponse(
        request=request,
        name='reddit/reddit_index.html',
    )
