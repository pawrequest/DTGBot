import typing as _t

import fastapi
import sqlmodel
from fastapi import Form, Request
from fastapi.responses import HTMLResponse
from sqlmodel import desc, select
from pawlogger.config_loguru import logger

from DTGBot.common.database import get_session
from DTGBot.common.models.episode_m import Episode
from DTGBot.fapi.shared import (
    Pagination,
    get_pagination,
    templates,
)
from DTGBot.fapi.sql_stmts import search_column, eps_by_guruname, select_page_more

router = fastapi.APIRouter()
SearchKind = _t.Literal['title', 'guru', 'notes']


async def search_db(
        session: sqlmodel.Session,
        search_str: str,
        search_kind: SearchKind = 'title',
        pagination: Pagination = None,
) -> tuple[list[Episode], bool]:
    match search_kind:
        case 'guru':
            stmt = await eps_by_guruname(search_str)
            # stmt = await by_related_column(Episode, Guru, Guru.name, search_str)
        case 'title':
            stmt = await search_column(Episode, Episode.title, search_str)
        case 'notes':
            stmt = await search_column(Episode, Episode.notes, search_str)
        case _:
            raise ValueError(f'Invalid kind: {search_kind}')
    episodes, more = await select_page_more(session, stmt, pagination)
    return episodes, more


@router.get('/get/', response_class=HTMLResponse)
async def get(
        request: Request,
        session: sqlmodel.Session = fastapi.Depends(get_session),
        pagination: Pagination = fastapi.Depends(get_pagination),
):
    stmt = select(Episode).order_by(desc(Episode.date))
    episodes, more = await select_page_more(session, stmt, pagination)

    return templates().TemplateResponse(
        request=request,
        name='episode/episode_cards.html',
        context={'episodes': episodes, 'pagination': pagination, 'route_url': 'eps', 'more': more}
    )


@router.post('/get/', response_class=HTMLResponse)
async def search(
        request: Request,
        search_kind: SearchKind = Form(...),
        search_str: str = Form(...),
        session: sqlmodel.Session = fastapi.Depends(get_session),
        pagination: Pagination = fastapi.Depends(get_pagination)
):
    if search_kind and search_str:
        logger.debug(f'{search_kind=} {search_str=}')
        episodes, more = await search_db(
            session,
            search_str,
            search_kind,
            pagination,
        )

    else:
        stmt = select(Episode).order_by(desc(Episode.date))
        episodes, more = await select_page_more(session, stmt, pagination)

    return templates().TemplateResponse(
        request=request,
        name='episode/episode_cards.html',
        context={'episodes': episodes, 'pagination': pagination, 'route_url': 'eps', 'more': more}
    )


@router.get('/{ep_id}/', response_class=HTMLResponse)
async def detail(
        ep_id: int,
        request: Request,
        sesssion: sqlmodel.Session = fastapi.Depends(get_session)
):
    episode = sesssion.get(Episode, ep_id)
    return templates().TemplateResponse(
        request=request,
        name='episode/episode_detail.html',
        context={'episode': episode}
    )


@router.get('/', response_class=HTMLResponse)
async def index(
        request: Request,
):
    return templates().TemplateResponse(
        request=request,
        name='episode/episode_index.html',
    )
