from typing import NamedTuple

from fastapi import Query
from starlette.templating import Jinja2Templates

from DTGBot.common.dtg_config import dtg_sett

PAGE_SIZE = 18


def templates():
    return Jinja2Templates(directory=str(dtg_sett().frontend_dir / 'templates'))


def get_pagination(limit: int = Query(PAGE_SIZE, gt=0), offset: int = Query(0, ge=0)):
    return Pagination(limit=limit, offset=offset)


class Pagination(NamedTuple):
    limit: int
    offset: int


def select_page(sqlselect, pagination: Pagination):
    return sqlselect.offset(pagination.offset).limit(pagination.limit)
