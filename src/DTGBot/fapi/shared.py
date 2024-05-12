from datetime import date, datetime
from typing import NamedTuple

from fastapi import Query
from starlette.templating import Jinja2Templates

from DTGBot.common.dtg_config import dtg_sett

PAGE_SIZE = 27


def templates():
    return Jinja2Templates(directory=str(dtg_sett().guru_frontend / 'templates'))


def get_pagination(limit: int = Query(PAGE_SIZE, gt=0), offset: int = Query(0, ge=0)):
    return Pagination(limit=limit, offset=offset)


class Pagination(NamedTuple):
    limit: int
    offset: int


def ordinal(n):
    return str(n) + ('th' if 4 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th'))


def dt_ordinal(dt: datetime | date) -> str:
    return dt.strftime('%a {th} %b %Y').replace('{th}', ordinal(dt.day))


async def base_url() -> str:
    return '/dtg'


async def base_url_d() -> dict[str, str]:
    return {'BASE_URL': await base_url()}
