from typing import NamedTuple

from fastapi import Query
from loguru import logger
from starlette.templating import Jinja2Templates

from DTGBot.common.dtg_config import dtg_sett

PAGE_SIZE = 9


def templates():
    return Jinja2Templates(directory=str(dtg_sett().frontend_dir / 'templates'))


def get_pagination(limit: int = Query(PAGE_SIZE, gt=0), offset: int = Query(0, ge=0)):
    logger.info(f'got limit: {limit}, offset: {offset}')
    return {'limit': limit, 'offset': offset}


def get_pagination_tup(limit: int = Query(PAGE_SIZE, gt=0), offset: int = Query(0, ge=0)):
    return Pagination(limit=limit, offset=offset)


class Pagination(NamedTuple):
    limit: int
    offset: int


def select_page(sqlselect, pagination: Pagination):
    return sqlselect.offset(pagination.offset).limit(pagination.limit)
