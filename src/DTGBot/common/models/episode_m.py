from typing import ClassVar, TYPE_CHECKING

from sqlmodel import Field, Relationship
import sqlmodel as sqm
import sqlalchemy as sqa
import pydantic as _p
from scrapaw import EpisodeBase, ScrapawConfig

from DTGBot.common.models.links import GuruEpisodeLink, RedditThreadEpisodeLink

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
    def slug(self):
        return f'/{type(self).rout_prefix}/{self.id}'

    def matches(self, other):
        if isinstance(other, Guru):
            return other.name in self.title
        elif isinstance(other, RedditThread):
            return other.title in self.title or self.title in other.title
