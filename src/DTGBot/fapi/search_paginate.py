from dataclasses import field
from enum import StrEnum, auto
from typing import NamedTuple

from attr import dataclass
from fastapi import Depends, Query

from DTGBot.common.models.maps import TABLE_TYPES

PAGE_SIZE = 30


class ConditionType(StrEnum):
    EQUAL = auto()
    NOT_EQUAL = auto()
    CONTAIN = auto()
    NOT_CONTAIN = auto()
    BEFORE = auto()
    BETWEEN = auto()
    AFTER = auto()
    ON = auto()


class Pagination(NamedTuple):
    limit: int = PAGE_SIZE
    offset: int = 0

    @classmethod
    def from_query(cls, limit: int = Query(PAGE_SIZE, gt=0), offset: int = Query(0, ge=0)):
        return cls(limit=limit, offset=offset)


@dataclass
class SearchRequest:
    table: TABLE_TYPES
    row_id: str | None = None
    pk_value: str | None = None
    filtered: bool = True
    condition: ConditionType = ConditionType.CONTAIN
    max_rtn: int | None = None
    package: dict = field(default_factory=dict)
    pagination: Pagination = Depends(Pagination.from_query)

    @property
    def q_str(self):
        return self.q_str_paginate()

    @property
    def query_str_json(self):
        return self.q_str_paginate(json=True)

    @property
    def next_q_str(self):
        return self.q_str_paginate(self.pagination.next_page())

    @property
    def next_q_str_json(self):
        return self.q_str_paginate(self.pagination.next_page(), json=True)

    def q_str_paginate(self, pagination: Pagination = None, json: bool = False):
        # todo package?
        pagination = pagination or self.pagination
        qstr = '/api' if json else ''
        qstr += f'/search?csrname={self.csrname}'
        if self.filtered:
            qstr += f'&filtered={str(self.filtered).lower()}'
        if self.pk_value:
            qstr += f'&pkvalue={self.pk_value}'
        qstr += f'&limit={pagination.limit}&offset={pagination.offset}'
        return qstr

    def next_request(self):
        return self.model_copy(update={'pagination': self.pagination.next_page()})

    def prev_request(self):
        return self.model_copy(update={'pagination': self.pagination.prev_page()})

    @classmethod
    def from_query(
        cls,
        csrname: AmherstTableName = Path(...),
        filtered: bool = Query(True),
        pk_value: str = Query(''),
        pagination: Pagination = Depends(Pagination.from_query),
        condition: ConditionType = Query(ConditionType.CONTAIN),
        max_rtn: int = Query(None),
        row_id: str = Query(None),
    ):
        logger.warning(f'SearchRequest.from_query({csrname=}, {filtered=}, {pk_value=}, {pagination=})')
        return cls(
            csrname=csrname,
            pagination=pagination,
            pk_value=pk_value,
            filtered=filtered,
            condition=condition,
            max_rtn=max_rtn,
            row_id=row_id,
        )

    @classmethod
    def from_body(
        cls,
        csrname: AmherstTableName = Body(...),
        filtered: bool = Body(True),
        pk_value: str = Body(None),
        package: dict = Body(default_factory=dict),
        pagination: Pagination = Depends(Pagination.from_query),
        condition: ConditionType = Body(ConditionType.CONTAIN),
        row_id: str = Body(None),
        max_rtn: int = Body(None),
    ):
        logger.warning(f'SearchRequest.from_body({csrname=}, {filtered=}, {pk_value=}, {package=}, {pagination=})')
        return cls(
            csrname=csrname,
            filtered=filtered,
            pagination=pagination,
            pk_value=pk_value,
            package=package,
            condition=condition,
            row_id=row_id,
            max_rtn=max_rtn,
        )


class SearchResponse[T: AMHERST_TABLE_MODELS](BaseModel):
    records: list[T]
    length: int = 0
    search_request: SearchRequest | None = None
    more: MoreAvailable | None = None

    @model_validator(mode='after')
    def set_length(self):
        self.length = len(self.records)
        return self
