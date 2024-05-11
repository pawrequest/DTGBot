# no dont do this!! from __future__ import annotations
from functools import cached_property
from typing import ClassVar, TYPE_CHECKING

import sqlmodel
from sqlmodel import Field, Relationship, SQLModel
import sqlalchemy as sa
import pydantic as _p

from DTGBot.common.models.links import (
    GuruEpisodeExclude,
    GuruEpisodeLink,
    GuruRedditExclude,
    GuruRedditLink,
)

if TYPE_CHECKING:
    from DTGBot.common.models.episode_m import Episode
    from DTGBot.common.models.reddit_m import RedditThread


class GuruBase(SQLModel):
    name: str = Field(index=True, unique=True)
    notes: list[str] | None = Field(default_factory=list)
    include_strs: list[str] | None = Field(default_factory=list)
    exclude_strs: list[str] | None = Field(default_factory=list)

    @property
    def title(self):
        return self.name


class Guru(GuruBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    notes: list[str] | None = Field(default_factory=list, sa_column=sqlmodel.Column(sa.JSON))
    include_strs: list[str] | None = Field(default_factory=list, sa_column=sqlmodel.Column(sa.JSON))
    exclude_strs: list[str] | None = Field(default_factory=list, sa_column=sqlmodel.Column(sa.JSON))

    episodes: list['Episode'] = Relationship(back_populates='gurus', link_model=GuruEpisodeLink)
    episode_excludes: list['Episode'] = Relationship(back_populates='guru_excludes', link_model=GuruEpisodeExclude)

    reddit_threads: list['RedditThread'] = Relationship(back_populates='gurus', link_model=GuruRedditLink)
    reddit_excludes: list['RedditThread'] = Relationship(back_populates='guru_excludes', link_model=GuruRedditExclude)

    rout_prefix: ClassVar[str] = 'guru'

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
