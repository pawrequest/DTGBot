from typing import NamedTuple

from fastapi import Path
from fastapi.params import Depends

from DTGBot.common.models.episode_m import Episode
from DTGBot.common.models.guru_m import Guru
from DTGBot.common.models.reddit_m import RedditThread

TABLE_TYPES = type(Episode) | type(Guru) | type(RedditThread)


class TableMap(NamedTuple):
    table: TABLE_TYPES
    name: str
    route_prefix: str


TABLE_MAPS = [
    TableMap(Episode, 'Episode', 'eps'),
    TableMap(Guru, 'Guru', 'gurus'),
    TableMap(RedditThread, 'RedditThread', 'reddit'),
]

TYPE_MAP = {_.name: _ for _ in TABLE_MAPS}


def tablename_from_path(table_name: str = Path()):
    return table_name


def table_type_from_path(table_name: str = Depends(tablename_from_path)):
    return TYPE_MAP[table_name].table


def route_prefix_from_path(table_name: str = Depends(tablename_from_path)):
    return TYPE_MAP[table_name].route_prefix
