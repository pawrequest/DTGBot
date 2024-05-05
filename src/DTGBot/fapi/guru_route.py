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
    select_page,
    templates,
)

router = fastapi.APIRouter()
SearchKind = _t.Literal['name']


async def gurus_from_sesh(session: sqlmodel.Session, pagination: Pagination):
    one_extra = pagination.limit + 1

    stmt = (
        select(
            Guru,
            # func.count(GuruEpisodeLink.guru_id),
        )
        .join(GuruEpisodeLink, isouter=True)
        .join(RedditThreadGuruLink, isouter=True)
        .group_by(Guru.id)
        .having(
            (func.count(GuruEpisodeLink.guru_id) + func.count(RedditThreadGuruLink.guru_id)) > 0
        )
        .order_by(
            func.count(GuruEpisodeLink.guru_id) + func.count(RedditThreadGuruLink.guru_id).desc()
        )
        .offset(pagination.offset)
        .limit(one_extra)
    )
    result = session.exec(stmt).all()
    more = len(result) >= one_extra
    result_ = result[:pagination.limit]

    return result_, more


def guru_matches(
        session,
        search_str,
        search_kind: SearchKind = 'title',
        pagination: Pagination = get_pagination(),
):
    one_extra = pagination.limit + 1
    match search_kind:
        case 'name':
            stmt = select(Guru).where(
                func.lower(Guru.name).like(f'%{search_str.lower()}%')
            )

        case _:
            raise ValueError(f'Invalid kind: {search_kind}')
    # return sorted(matched_, key=lambda ep: ep.date, reverse=True)
    stmt = stmt.offset(pagination.offset).limit(one_extra)
    gurus = session.exec(stmt).all()
    more = len(gurus) >= one_extra
    return gurus[:pagination.limit], more


@router.get('/get/', response_class=HTMLResponse)
async def get(
        request: Request, session: sqlmodel.Session = fastapi.Depends(get_session),
        pagination: Pagination = fastapi.Depends(get_pagination)
):
    gurus, more = await gurus_from_sesh(session, pagination)
    logger.warning(f'{more=} {len(gurus)=}')

    return templates().TemplateResponse(
        request=request,
        name='guru/guru_cards.html',
        context={'gurus': gurus, 'pagination': pagination, 'route_url': 'guru', 'more': more}
    )


@router.post('/get/', response_class=HTMLResponse)
async def search_gurus(
        request: Request,
        search_kind: SearchKind = Form(...),
        search_str: str = Form(...),
        session: sqlmodel.Session = fastapi.Depends(get_session),
        pagination: Pagination = fastapi.Depends(get_pagination)
):
    if search_kind and search_str:
        gurus, more = guru_matches(
            session,
            search_str,
            search_kind,
            pagination
        )
    else:
        gurus, more = await gurus_from_sesh(
            session,
            pagination
        )

    logger.warning(f'{more=} {len(gurus)=}')

    return templates().TemplateResponse(
        request=request,
        name='guru/guru_cards.html',
        context={'gurus': gurus, 'pagination': pagination, 'route_url': 'guru', 'more': more}
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
):
    return templates().TemplateResponse(
        request=request,
        name='guru/guru_index.html',
    )
