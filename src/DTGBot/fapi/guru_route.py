import typing as _t
from pathlib import Path

import fastapi
import sqlmodel
from fastapi import Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from loguru import logger
from sqlmodel import select, col

from DTGBot.common.database import get_session
from DTGBot.common.models.guru_m import Guru


SearchKind = _t.Literal['name', 'episode', 'reddit']
router = fastapi.APIRouter()
THIS_DIR = Path(__file__).resolve().parent
template_dir = THIS_DIR.parent / 'templates'
templates = Jinja2Templates(directory=str(template_dir))


def guru_matches(gurus, search_str, search_kind: SearchKind = 'title'):
    match search_kind:
        case 'name':
            matched_ = [_ for _ in gurus if search_str.lower() in _.name.lower()]
        case 'episode':
            matched_ = [_ for _ in gurus if any(search_str.lower() in guru.name.lower() for guru in _.gurus)]
        case 'reddit':
            matched_ = [
                _ for _ in gurus if any(search_str.lower() in r_thread.title.lower() for r_thread in _.reddit_threads)
            ]
        case _:
            raise ValueError(f'Invalid kind: {search_kind}')
    return sorted(matched_, key=lambda ep: ep.date, reverse=True)


@router.get('/get_gurus/', response_class=HTMLResponse)
async def get_gurus(request: Request, session: sqlmodel.Session = fastapi.Depends(get_session)):
    gurus = await gurus_from_sesh(session)
    # gurus = sorted(gurus, key=lambda ep: ep.date, reverse=True)

    return templates.TemplateResponse(request=request, name='guru/guru_cards.html', context={'gurus': gurus})


@router.post('/get_gurus/', response_class=HTMLResponse)
async def search_gurus(
    request: Request,
    search_kind: SearchKind = Form(...),
    search_str: str = Form(...),
    session: sqlmodel.Session = fastapi.Depends(get_session),
):
    gurus = await gurus_from_sesh(session)

    if search_kind and search_str:
        matched_gurus = guru_matches(gurus, search_str, search_kind)
    else:
        matched_gurus = gurus

    matched_gurus = sorted(matched_gurus, key=lambda guru: guru.name)

    return templates.TemplateResponse(request=request, name='guru/guru_cards.html', context={'gurus': matched_gurus})


@router.get('/{guru_id}/', response_class=HTMLResponse)
async def read_guru(guru_id: int, request: Request, sesssion: sqlmodel.Session = fastapi.Depends(get_session)):
    guru = sesssion.get(Guru, guru_id)
    return templates.TemplateResponse(request=request, name='guru/guru_detail.html', context={'guru': guru})


@router.get('/', response_class=HTMLResponse)
async def all_gurus(request: Request, session=fastapi.Depends(get_session)):
    logger.debug('all_gurus')
    gurus = await gurus_from_sesh(session)
    return templates.TemplateResponse(request=request, name='guru/guru_index.html', context={'gurus': gurus})


async def gurus_from_sesh(session: sqlmodel.Session):
    statement = select(Guru).where(col(Guru.episodes) != [] or Guru.reddit_threads != [])
    return session.exec(statement).all()
