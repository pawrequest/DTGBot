import typing as _t

import fastapi
import sqlmodel
from fastapi import Form, Request
from fastapi.responses import HTMLResponse

from DTGBot.common.database import get_session
from DTGBot.common.models.guru_m import Guru
from DTGBot.fapi.shared import Pagination, get_pagination, templates
from DTGBot.fapi.sql_stmts import (by_column, gurus_w_interest, select_page_more)

router = fastapi.APIRouter()
SearchKind = _t.Literal['name']


async def search_db(
        session,
        search_str,
        search_kind: SearchKind = 'name',
        pagination: Pagination = get_pagination(),
):
    match search_kind:
        case 'name':
            stmt = await by_column(Guru, Guru.name, search_str)
        case _:
            raise ValueError(f'Invalid kind: {search_kind}')

    gurus, more = await select_page_more(session, stmt, pagination)
    return gurus, more


@router.get('/get/', response_class=HTMLResponse)
async def get(
        request: Request,
        session: sqlmodel.Session = fastapi.Depends(get_session),
        pagination: Pagination = fastapi.Depends(get_pagination)
):
    stmt = await gurus_w_interest()
    gurus, more = await select_page_more(session, stmt, pagination)

    return templates().TemplateResponse(
        request=request,
        name='guru/guru_cards.html',
        context={'gurus': gurus, 'pagination': pagination, 'route_url': 'guru', 'more': more}
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
        gurus, more = await search_db(session, search_str, search_kind, pagination)
    else:
        stmt = await gurus_w_interest()
        gurus, more = await select_page_more(session, stmt, pagination)

    return templates().TemplateResponse(
        request=request,
        name='guru/guru_cards.html',
        context={'gurus': gurus, 'pagination': pagination, 'route_url': 'guru', 'more': more}
    )


@router.get('/{guru_id}/', response_class=HTMLResponse)
async def detail(
        guru_id: int,
        request: Request,
        sesssion: sqlmodel.Session = fastapi.Depends(get_session)
):
    guru = sesssion.get(Guru, guru_id)
    return templates().TemplateResponse(
        request=request,
        name='guru/guru_detail.html',
        context={'guru': guru}
    )


@router.get('/', response_class=HTMLResponse)
async def index(
        request: Request,
):
    return templates().TemplateResponse(
        request=request,
        name='guru/guru_index.html',
    )
