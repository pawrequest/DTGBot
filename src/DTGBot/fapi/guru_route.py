import typing as _t

import fastapi
import sqlmodel
from fastapi import Form, Request
from fastapi.responses import HTMLResponse

from DTGBot.common.database import get_session
from DTGBot.common.models.guru_m import Guru
from DTGBot.fapi.shared import Pagination, TEMPLATES, get_pagination
from DTGBot.fapi.sql_stmts import gurus_w_interest, search_column, select_page_more

router = fastapi.APIRouter()
SearchKind = _t.Literal['name']

HX_GET_ROUTE = f'{Guru.route_prefix}/get'  # noqa:


async def search_db(
    session,
    search_str,
    search_kind: SearchKind = 'name',
    pagination: Pagination = get_pagination(),
):
    match search_kind:
        case 'name':
            stmt = await search_column(Guru, Guru.name, search_str)
        case _:
            raise ValueError(f'Invalid kind: {search_kind}')

    gurus, more = await select_page_more(session, stmt, pagination)
    return gurus, more


@router.get('/get/', response_class=HTMLResponse)
async def get(
    request: Request,
    session: sqlmodel.Session = fastapi.Depends(get_session),
    pagination: Pagination = fastapi.Depends(get_pagination),
):
    stmt = await gurus_w_interest()
    gurus, more = await select_page_more(session, stmt, pagination)

    return TEMPLATES.TemplateResponse(
        request=request,
        name='guru/guru_cards.html',
        context={
            'gurus': gurus,
            'pagination': pagination,
            'hx_get_route': HX_GET_ROUTE,
            'more': more,
        },
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
        gurus, more = await search_db(session, search_str, search_kind, pagination)
    else:
        stmt = await gurus_w_interest()
        gurus, more = await select_page_more(session, stmt, pagination)

    return TEMPLATES.TemplateResponse(
        request=request,
        name='guru/guru_cards.html',
        context={
            'gurus': gurus,
            'pagination': pagination,
            'hx_get_route': HX_GET_ROUTE,
            'more': more,
        },
    )


@router.get('/{guru_id}/', response_class=HTMLResponse)
async def detail(guru_id: int, request: Request, sesssion: sqlmodel.Session = fastapi.Depends(get_session)):
    guru = sesssion.get(Guru, guru_id)
    return TEMPLATES.TemplateResponse(
        request=request,
        name='guru/guru_detail.html',
        context={'guru': guru},
    )


@router.get('/', response_class=HTMLResponse)
async def index(
    request: Request,
):
    return TEMPLATES.TemplateResponse(
        request=request,
        name='guru/guru_index.html',
        context={'hx_get_route': HX_GET_ROUTE},
    )
