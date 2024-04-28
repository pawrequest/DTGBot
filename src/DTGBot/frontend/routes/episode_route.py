import typing as _t
from pathlib import Path

import fastapi
import sqlmodel
from fastapi import Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlmodel import select

from DTGBot.common.database import get_session
from DTGBot.common.models.episode_m import Episode
from DTGBot.common.models.guru_m import Guru
from pawlogger.config_loguru import logger

SearchKind = _t.Literal['title', 'guru', 'notes']
# app = FastAPI()
router = fastapi.APIRouter()
# app.mount('/static', StaticFiles(directory='static'), name='static')
THIS_DIR = Path(__file__).resolve().parent
template_dir = THIS_DIR.parent / 'templates'
print('TEMPLATE DIR', template_dir)
templates = Jinja2Templates(directory=str(template_dir))


def episode_matches(session, search_str, search_kind: SearchKind = 'title'):
    match search_kind:
        case 'title':
            statement = select(Episode).where(
                func.lower(Episode.title).like(f'%{search_str.lower()}%')
            )
        case 'guru':
            matching_gurus_stmt = select(Guru).where(
                func.lower(Guru.name).like(f'%{search_str.lower()}%')
            )
            matching_gurus = session.exec(matching_gurus_stmt).all()
            matching_episodes = {ep for guru in matching_gurus for ep in guru.episodes}

            return sorted(list(matching_episodes), key=lambda ep: ep.date, reverse=True)

        case 'notes':
            statement = select(Episode).where(
                func.lower(Episode.notes).like(f'%{search_str.lower()}%')
            )
        case _:
            raise ValueError(f'Invalid kind: {search_kind}')

    matched_ = session.exec(statement).all()
    return sorted(matched_, key=lambda ep: ep.date, reverse=True)


@router.get('/get_eps/', response_class=HTMLResponse)
async def get_ep_cards(request: Request, session: sqlmodel.Session = fastapi.Depends(get_session)):
    episodes = await from_sesh(Episode, session)
    episodes = sorted(episodes, key=lambda ep: ep.date, reverse=True)

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
    episodes = await from_sesh(Episode, session)
    if search_kind and search_str:
        logger.debug(f'{search_kind=} {search_str=}')
        matched_episodes = episode_matches(session, search_str, search_kind)
        # matched_episodes = episode_matches(episodes, search_str, search_kind)
    else:
        matched_episodes = episodes

    matched_episodes = sorted(matched_episodes, key=lambda ep: ep.date, reverse=True)

    return templates.TemplateResponse(
        request=request, name='episode/episode_cards.html', context={'episodes': matched_episodes}
    )


@router.get('/{ep_id}/', response_class=HTMLResponse)
async def read_episode(
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
async def all_eps(request: Request, session=fastapi.Depends(get_session)):
    logger.debug('all_eps')
    episodes = await from_sesh(Episode, session)
    episodes = sorted(episodes, key=lambda ep: ep.date, reverse=True)
    return templates.TemplateResponse(
        request=request, name='episode/episode_index.html', context={'episodes': episodes}
    )


async def from_sesh(clz, session: sqlmodel.Session):
    return session.exec(sqlmodel.select(clz)).all()
