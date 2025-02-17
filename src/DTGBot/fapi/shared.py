from datetime import date, datetime
from typing import NamedTuple

from fastapi import Query
from starlette.templating import Jinja2Templates

from DTGBot.common.dtg_config import guru_config

PAGE_SIZE = 27

TEMPLATES = Jinja2Templates(directory=str(guru_config().guru_frontend / 'templates'))
TEMPLATES.env.globals.update({'URL_PREFIX': guru_config().url_prefix})


def get_pagination(limit: int = Query(PAGE_SIZE, gt=0), offset: int = Query(0, ge=0)):
    return Pagination(limit=limit, offset=offset)


class Pagination(NamedTuple):
    limit: int
    offset: int


def ordinal(n):
    return str(n) + ('th' if 4 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th'))


def dt_ordinal(dt: datetime | date) -> str:
    return dt.strftime('%a {th} %b %Y').replace('{th}', ordinal(dt.day))


