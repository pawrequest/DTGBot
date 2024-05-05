# no dont do this!! from __future__ import annotations
import hashlib
from functools import cached_property
from typing import ClassVar, TYPE_CHECKING

import sqlmodel
from sqlmodel import Field, Relationship, SQLModel
import sqlalchemy as sa
import pydantic as _p

from DTGBot.common.models.links import GuruEpisodeLink, RedditThreadGuruLink

if TYPE_CHECKING:
    from DTGBot.common.models.episode_m import Episode
    from DTGBot.common.models.reddit_m import RedditThread


class GuruBase(SQLModel):
    name: str = Field(index=True, unique=True)
    notes: list[str] | None = Field(default_factory=list)


class Guru(GuruBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    notes: list[str] | None = Field(default_factory=list, sa_column=sqlmodel.Column(sa.JSON))

    episodes: list['Episode'] = Relationship(back_populates='gurus', link_model=GuruEpisodeLink)

    reddit_threads: list['RedditThread'] = Relationship(
        back_populates='gurus',
        link_model=RedditThreadGuruLink
    )

    # relevant: bool = Field(default=False)

    rout_prefix: ClassVar[str] = 'guru'

    # @_p.model_validator(mode='after')
    # def validate_relevant(self):
    #     self.relevant = any([self.episodes, self.reddit_threads])
    #     return self

    @cached_property
    def slug(self):
        return f'/{type(self).rout_prefix}/{self.id}'

    @_p.computed_field
    @cached_property
    def interest(self) -> int:
        return len(self.episodes) + len(self.reddit_threads)

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name

    @_p.computed_field
    @property
    def get_hash(self) -> str:
        return hashlib.md5(
            ','.join([self.name]).encode('utf-8')
        ).hexdigest()
