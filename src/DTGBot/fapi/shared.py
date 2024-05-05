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


def select_page(sqlselect, pagination: Pagination):
    return sqlselect.offset(pagination.offset).limit(pagination.limit)


def select_page_more(session, sqlselect, pagination: Pagination) -> tuple[list, bool]:
    stmt = sqlselect.offset(pagination.offset).limit(pagination.limit + 1)
    res = session.exec(stmt).all()
    more = len(res) > pagination.limit
    return res[:pagination.limit], more


def ordinal(n):
    return str(n) + ('th' if 4 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th'))


def dt_ordinal(dt: datetime | date) -> str:
    return dt.strftime('%a {th} %b %Y').replace('{th}', ordinal(dt.day))
