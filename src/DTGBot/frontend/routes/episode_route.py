import typing as _t
from pathlib import Path

import fastapi
import sqlmodel
from fastapi import Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlmodel import desc, select
from pawlogger.config_loguru import logger

from DTGBot.common.database import get_session
from DTGBot.common.models.episode_m import Episode
from DTGBot.common.models.guru_m import Guru

router = fastapi.APIRouter()
SearchKind = _t.Literal['title', 'guru', 'notes']
THIS_DIR = Path(__file__).resolve().parent
template_dir = THIS_DIR.parent / 'templates'
print('TEMPLATE DIR', template_dir)
templates = Jinja2Templates(directory=str(template_dir))


def episode_matches(session: sqlmodel.Session, search_str: str, search_kind: SearchKind = 'title'):
    match search_kind:
        case 'guru':
            stmt = select(Guru).where(
                func.lower(Guru.name).like(f'%{search_str.lower()}%')
            )
            matching_gurus = session.exec(stmt).all()
            matching_episodes = {ep for guru in matching_gurus for ep in guru.episodes}
            # return matching_episodes
            return sorted(list(matching_episodes), key=lambda ep: ep.date, reverse=True)

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

    return session.exec(stmt).all()


@router.get('/get_eps/', response_class=HTMLResponse)
async def get_ep_cards(request: Request, session: sqlmodel.Session = fastapi.Depends(get_session)):
    episodes = session.exec(select(Episode).order_by(desc(Episode.date))).all()

    return templates.TemplateResponse(
        request=request, name='episode/episode_cards.html', context={'episodes': episodes}
    )


@router.post('/get_eps/', response_class=HTMLResponse)
async def search_eps(
        request: Request,
        search_kind: SearchKind = Form(...),
        search_str: str = Form(...),
        session: sqlmodel.Session = fastapi.Depends(get_session),
):
    if search_kind and search_str:
        logger.debug(f'{search_kind=} {search_str=}')
        episodes = episode_matches(session, search_str, search_kind)
    else:
        episodes = session.exec(select(Episode).order_by(desc(Episode.date))).all()

    return templates.TemplateResponse(
        request=request, name='episode/episode_cards.html', context={'episodes': episodes}
    )


@router.get('/{ep_id}/', response_class=HTMLResponse)
async def one_ep(
        ep_id: int,
        request: Request,
        sesssion: sqlmodel.Session = fastapi.Depends(get_session)
):
    episode = sesssion.get(Episode, ep_id)
    return templates.TemplateResponse(
        request=request,
        name='episode/episode_detail.html',
        context={'episode': episode}
    )


@router.get('/', response_class=HTMLResponse)
async def ep_index(request: Request, session=fastapi.Depends(get_session)):
    logger.debug('all_eps')
    episodes = session.exec(select(Episode).order_by(desc(Episode.date))).all()
    # episodes = sorted(episodes, key=lambda ep: ep.date, reverse=True)
    return templates.TemplateResponse(
        request=request, name='episode/episode_index.html', context={'episodes': episodes}
    )
