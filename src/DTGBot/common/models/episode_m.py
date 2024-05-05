from typing import ClassVar, TYPE_CHECKING

from sqlmodel import Field, Relationship
import sqlmodel as sqm
import sqlalchemy as sqa
import pydantic as _p
from scrapaw import EpisodeBase, ScrapawConfig

from DTGBot.common.models.links import GuruEpisodeLink, RedditThreadEpisodeLink
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
    reddit_threads: list['RedditThread'] = Relationship(
        back_populates='episodes',
        link_model=RedditThreadEpisodeLink
    )
    settings_class: ClassVar[_p.BaseModel] = ScrapawConfig
    rout_prefix: ClassVar[str] = 'eps'

    @property
    def number_date(self) -> str:
        astr = f'Episode {self.number}' if self.number.isnumeric() else f'{self.number} Episode'
        return f'{astr} - {self.ordinal_date}'

    @property
    def slug(self) -> str:
        return f'/{self.rout_prefix}/{self.id}'
        # astr = f'/{self.rout_prefix}/{self.number}_{self.date.isoformat()}'
        # return astr

    @property
    def ordinal_date(self) -> str:
        return dt_ordinal(self.date)
