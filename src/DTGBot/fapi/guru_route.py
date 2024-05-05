import typing as _t

import fastapi
import sqlmodel
from fastapi import Form, Request
from fastapi.responses import HTMLResponse
from loguru import logger
from sqlalchemy import func
from sqlmodel import select

from DTGBot.common.database import get_session
from DTGBot.common.models.guru_m import Guru
from DTGBot.common.models.links import GuruEpisodeLink, RedditThreadGuruLink
from DTGBot.fapi.shared import (
    Pagination,
    get_pagination,
    get_pagination_tup,
    select_page,
    templates,
)

router = fastapi.APIRouter()
SearchKind = _t.Literal['name']


def guru_matches(
        session,
        search_str,
        search_kind: SearchKind = 'title',
        pagination: Pagination = get_pagination_tup(),
):
    match search_kind:
        case 'name':
            stmt = select(Guru).where(
                func.lower(Guru.name).like(f'%{search_str.lower()}%')
            )

        case _:
            raise ValueError(f'Invalid kind: {search_kind}')
    # return sorted(matched_, key=lambda ep: ep.date, reverse=True)
    stmt = select_page(stmt, pagination)
    return session.exec(stmt).all()


@router.get('/get_gurus/', response_class=HTMLResponse)
async def get_gurus(
        request: Request, session: sqlmodel.Session = fastapi.Depends(get_session),
        pagination: Pagination = fastapi.Depends(get_pagination_tup)
):
    gurus = await gurus_from_sesh(session, pagination)

    return templates().TemplateResponse(
        request=request,
        name='guru/guru_cards.html',
        context={'gurus': gurus, 'pagination': pagination, 'route_url': 'guru'}
    )


@router.post('/get_gurus/', response_class=HTMLResponse)
async def search_gurus(
        request: Request,
        search_kind: SearchKind = Form(...),
        search_str: str = Form(...),
        session: sqlmodel.Session = fastapi.Depends(get_session),
        pagination: Pagination = fastapi.Depends(get_pagination_tup)
):
    if search_kind and search_str:
        matched_gurus = guru_matches(
            session,
            search_str,
            search_kind,
            pagination
        )
    else:
        matched_gurus = await gurus_from_sesh(
            session,
            pagination
        )

    return templates().TemplateResponse(
        request=request,
        name='guru/guru_cards.html',
        context={'gurus': matched_gurus, 'pagination': pagination, 'route_url': 'guru'}
    )


@router.get('/{guru_id}/', response_class=HTMLResponse)
async def guru_detail(
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
async def guru_index(
        request: Request,
        pagination: Pagination = fastapi.Depends(get_pagination_tup)
):
    logger.debug('all_gurus')
    return templates().TemplateResponse(
        request=request,
        name='guru/guru_index.html',
        context={'pagination': pagination, 'route_url': 'guru'}
    )


async def gurus_from_sesh(session: sqlmodel.Session, pagination: Pagination):
    stmt = (
        select(
            Guru,
        )
        .join(GuruEpisodeLink, isouter=True)
        .join(RedditThreadGuruLink, isouter=True)
        .group_by(Guru.id)
        .order_by(
            func.count(GuruEpisodeLink.guru_id) + func.count(RedditThreadGuruLink.guru_id).desc()
        )
    )
    stmt = select_page(stmt, pagination)
    result = session.exec(stmt).all()

    return result
