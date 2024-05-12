from datetime import date, datetime
from functools import lru_cache
from typing import NamedTuple

from fastapi import Query
from starlette.requests import Request
from starlette.templating import Jinja2Templates

from DTGBot.common.dtg_config import dtg_sett

PAGE_SIZE = 27


@lru_cache
def templates_mount():
    return Jinja2Templates(directory=str(dtg_sett().guru_frontend / 'templates'))


TEMPLATES = Jinja2Templates(directory=str(dtg_sett().guru_frontend / 'templates'))


def get_pagination(limit: int = Query(PAGE_SIZE, gt=0), offset: int = Query(0, ge=0)):
    return Pagination(limit=limit, offset=offset)


class Pagination(NamedTuple):
    limit: int
    offset: int


def ordinal(n):
    return str(n) + ('th' if 4 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th'))


def dt_ordinal(dt: datetime | date) -> str:
    return dt.strftime('%a {th} %b %Y').replace('{th}', ordinal(dt.day))


BASE_URL = '/dtg'
BASE_URL_D = {'BASE_URL': BASE_URL}


def full_url_for(request: Request):
    def _url_for(name: str, **path_params):
        return f'{BASE_URL}/{request.url_for(name, **path_params)}'

    return {'full_url_for': _url_for}


TEMPLATES.env.globals.update({'full_url_for': full_url_for})
