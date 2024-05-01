# no dont do this!! from __future__ import annotations
import hashlib
from datetime import datetime
from typing import ClassVar, TYPE_CHECKING

from asyncpraw.models import Submission
import pydantic as _p
import sqlalchemy as sqa
import sqlmodel as sqm

from DTGBot.common.dtg_config import RedditConfig
from DTGBot.common.models.links import RedditThreadEpisodeLink, RedditThreadGuruLink

if TYPE_CHECKING:
    from DTGBot.common.models.episode_m import Episode
    from DTGBot.common.models.guru_m import Guru


def submission_to_dict(submission: Submission):
    serializable_types = (int, float, str, bool, type(None))
    if isinstance(submission, Submission):
        submission = vars(submission)
    return {k: v for k, v in submission.items() if isinstance(v, serializable_types)}


class RedditThreadBase(sqm.SQLModel):
    reddit_id: str = sqm.Field(index=True, unique=True)
    title: str
    shortlink: str
    created_datetime: datetime
    submission: dict = sqm.Field(default=None, sa_column=sqa.Column(sqa.JSON))

    @_p.field_validator('submission', mode='before')
    def validate_submission(cls, v):
        return submission_to_dict(v)

    @classmethod
    def from_submission(cls, submission: Submission):
        tdict = dict(
            reddit_id=submission.id,
            title=submission.title,
            shortlink=submission.shortlink,
            created_datetime=submission.created_utc,
            submission=submission,
        )
        return cls.model_validate(tdict)


class RedditThread(RedditThreadBase, table=True, extend_existing=True):
    id: int | None = sqm.Field(default=None, primary_key=True)

    gurus: list['Guru'] = sqm.Relationship(
        back_populates='reddit_threads',
        link_model=RedditThreadGuruLink
    )
    episodes: list['Episode'] = sqm.Relationship(
        back_populates='reddit_threads',
        link_model=RedditThreadEpisodeLink
    )
    settings_class: ClassVar[_p.BaseModel] = RedditConfig

    def __hash__(self):
        return hash(self.reddit_id)

    @property
    def get_hash(self):
        return hashlib.md5(
            ','.join([self.reddit_id]).encode('utf-8')
        ).hexdigest()

    @property
    def slug(self):
        return f'/red/{self.id}'


    @classmethod
    def rout_prefix(cls):
        return '/red/'
