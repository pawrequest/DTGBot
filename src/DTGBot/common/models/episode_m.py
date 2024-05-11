from typing import ClassVar, TYPE_CHECKING

from sqlmodel import Field, Relationship
import sqlmodel as sqm
import sqlalchemy as sqa
from scrapaw import EpisodeBase

from DTGBot.common.models.links import (
    EpisodeRedditExclude,
    EpisodeRedditLink,
    GuruEpisodeExclude,
    GuruEpisodeLink,
)
from DTGBot.fapi.shared import dt_ordinal

if TYPE_CHECKING:
    from DTGBot.common.models.guru_m import Guru
    from DTGBot.common.models.reddit_m import RedditThread


class Episode(EpisodeBase, sqm.SQLModel, table=True):
    title: str = Field(index=True)
    links: dict[str, str] = Field(default_factory=dict, sa_column=sqm.Column(sqa.JSON))
    notes: list[str] = Field(default_factory=list, sa_column=sqm.Column(sqa.JSON))
    id: int | None = Field(default=None, primary_key=True)

    gurus: list['Guru'] = Relationship(back_populates='episodes', link_model=GuruEpisodeLink)
    guru_excludes: list['Guru'] = Relationship(back_populates='episode_excludes', link_model=GuruEpisodeExclude)
    # guru_excludes: list[int] = sqm.Field(default_factory=list, sa_column=Column(sqm.JSON))

    reddit_threads: list['RedditThread'] = Relationship(back_populates='episodes', link_model=EpisodeRedditLink)
    reddit_excludes: list['RedditThread'] = Relationship(back_populates='episode_excludes', link_model=EpisodeRedditExclude)
    # reddit_excludes: list[int] = Field(default_factory=list, sa_column=Column(sqm.JSON))
    rout_prefix: ClassVar[str] = 'eps'

    @property
    def number_str(self) -> str:
        return f'Episode {self.number}' if self.number.isnumeric() else f'{self.number.title()} Episode'

    @property
    def number_date(self) -> str:
        return f'{self.number_str} - {self.ordinal_date}'

    @property
    def slug(self) -> str:
        return f'/{self.rout_prefix}/{self.id}'
        # astr = f'/{self.rout_prefix}/{self.number}_{self.date.isoformat()}'
        # return astr

    @property
    def ordinal_date(self) -> str:
        return dt_ordinal(self.date)
