import typing as _t

import fastapi
import sqlmodel
from fastapi import Form, Request
from fastapi.responses import HTMLResponse
from sqlmodel import desc, select
from pawlogger.config_loguru import logger

from DTGBot.common.database import get_session
from DTGBot.common.models.reddit_m import RedditThread
from DTGBot.fapi.shared import (
    Pagination,
    get_pagination,
    templates, base_url_d, base_url,
)
from DTGBot.fapi.sql_stmts import reddit_by_guruname, search_column, select_page_more

router = fastapi.APIRouter()
SearchKind = _t.Literal['title', 'guru']


async def search_db(
    session: sqlmodel.Session,
    search_str: str,
    pagination: Pagination,
    search_kind: SearchKind = 'title',
):
    match search_kind:
        case 'title':
            stmt = await search_column(RedditThread, RedditThread.title, search_str)
        case 'guru':
            stmt = await reddit_by_guruname(search_str)
        case _:
            raise ValueError(f'Invalid kind: {search_kind}')

    threads, more = await select_page_more(session, stmt, pagination)
    return threads, more


@router.get('/get/', response_class=HTMLResponse)
async def get(
    request: Request,
    session: sqlmodel.Session = fastapi.Depends(get_session),
    pagination: Pagination = fastapi.Depends(get_pagination),
):
    stmt = select(RedditThread).order_by(desc(RedditThread.created_datetime))
    threads, more = await select_page_more(session, stmt, pagination)

    return templates().TemplateResponse(
        request=request,
        name='reddit/reddit_cards.html',
        context={'threads': threads, 'pagination': pagination, 'route_url': f'{await base_url()}/red', 'more': more} | await base_url_d(),
    )


@router.post('/get/', response_class=HTMLResponse)
async def search(
    request: Request,
    search_kind: SearchKind = Form(...),
    search_str: str = Form(...),
    session: sqlmodel.Session = fastapi.Depends(get_session),
    pagination: Pagination = fastapi.Depends(get_pagination),
):
    if search_kind and search_str:
        logger.debug(f'{search_kind=} {search_str=}')
        threads, more = await search_db(session, search_str, pagination, search_kind)
    else:
        stmt = select(RedditThread).order_by(desc(RedditThread.created_datetime))
        threads, more = await select_page_more(session, stmt, pagination)

    return templates().TemplateResponse(
        request=request,
        name='reddit/reddit_cards.html',
        context={'threads': threads, 'pagination': pagination, 'route_url': f'{await base_url()}/red', 'more': more} | await base_url_d(),
    )


@router.get('/', response_class=HTMLResponse)
async def index(
    request: Request,
):
    logger.debug('all_red')
    return templates().TemplateResponse(
        request=request,
        name='reddit/reddit_index.html',
        context=await base_url_d(),
    )
