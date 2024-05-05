import typing as _t

import fastapi
import sqlmodel
from fastapi import Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import func
from sqlmodel import desc, select
from pawlogger.config_loguru import logger

from DTGBot.common.database import get_session
from DTGBot.common.models.episode_m import Episode
from DTGBot.common.models.guru_m import Guru
from DTGBot.fapi.shared import (Pagination, get_pagination, select_page, templates)

router = fastapi.APIRouter()
SearchKind = _t.Literal['title', 'guru', 'notes']


# def episode_matches(session: sqlmodel.Session, search_str: str, search_kind: SearchKind = 'title'):

def episode_matches(
        session: sqlmodel.Session,
        search_str: str,
        search_kind: SearchKind = 'title',
        pagination: Pagination = None,
):
    match search_kind:
        case 'guru':
            stmt = select(Guru).where(
                func.lower(Guru.name).like(f'%{search_str.lower()}%')
            )
            matching_gurus = session.exec(stmt).all()
            matching_episodes = {ep for guru in matching_gurus for ep in guru.episodes}
            # return matching_episodes
            return sorted(list(matching_episodes), key=lambda ep: ep.date, reverse=True)[
                   pagination.offset:pagination.limit + pagination.offset]

        case 'title':
            stmt = select(Episode).order_by(desc(Episode.date)).where(
                func.lower(Episode.title).like(f'%{search_str.lower()}%')
            )

        case 'notes':
            stmt = select(Episode).order_by(desc(Episode.date)).where(
                func.lower(Episode.notes).like(f'%{search_str.lower()}%')
            )
        case _:
            raise ValueError(f'Invalid kind: {search_kind}')

    stmt = select_page(stmt, pagination)
    return session.exec(stmt).all()


@router.get('/get/', response_class=HTMLResponse)
async def get_eps(
        request: Request,
        session: sqlmodel.Session = fastapi.Depends(get_session),
        pagination: Pagination = fastapi.Depends(get_pagination),
):
    stmt = select(Episode).order_by(desc(Episode.date))
    stmt = select_page(stmt, pagination)
    episodes = session.exec(stmt).all()
    more = len(episodes) == pagination.limit

    return templates().TemplateResponse(
        request=request,
        name='episode/episode_cards.html',
        context={'episodes': episodes, 'pagination': pagination, 'route_url': 'eps', 'more': more}
    )


@router.post('/get/', response_class=HTMLResponse)
async def search_eps(
        request: Request,
        search_kind: SearchKind = Form(...),
        search_str: str = Form(...),
        session: sqlmodel.Session = fastapi.Depends(get_session),
        pagination: Pagination = fastapi.Depends(get_pagination)
):
    if search_kind and search_str:
        logger.debug(f'{search_kind=} {search_str=}')
        episodes = episode_matches(
            session,
            search_str,
            search_kind,
            pagination,
        )

    else:
        stmt = select(Episode).order_by(desc(Episode.date))
        stmt = select_page(stmt, pagination)
        episodes = session.exec(stmt).all()

    more = len(episodes) == pagination.limit

    return templates().TemplateResponse(
        request=request,
        name='episode/episode_cards.html',
        context={'episodes': episodes, 'pagination': pagination, 'route_url': 'eps', 'more': more}
    )


@router.get('/{ep_id}/', response_class=HTMLResponse)
async def ep_detail(
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
async def ep_index(
        request: Request,
):
    logger.debug('all_eps')
    return templates().TemplateResponse(
        request=request,
        name='episode/episode_index.html',
    )
