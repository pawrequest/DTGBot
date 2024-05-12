# no dont do this!! from __future__ import annotations
import hashlib
from datetime import datetime
from typing import TYPE_CHECKING

from asyncpraw.models import Submission
import sqlmodel as sqm
from sqlmodel import Relationship

from DTGBot.common.models.links import (
    EpisodeRedditLink,
    GuruRedditLink,
)
from DTGBot.fapi.shared import dt_ordinal

if TYPE_CHECKING:
    from DTGBot.common.models.episode_m import Episode
    from DTGBot.common.models.guru_m import Guru


# def submission_to_dict(submission: Submission):
#     serializable_types = (int, float, str, bool, type(None))
#     if isinstance(submission, Submission):
#         submission = vars(submission)
#     return {k: v for k, v in submission.items() if isinstance(v, serializable_types)}


class RedditThreadBase(sqm.SQLModel):
    reddit_id: str = sqm.Field(index=True, unique=True)
    title: str
    shortlink: str
    created_datetime: datetime

    @property
    def ordinal_date(self) -> str:
        return dt_ordinal(self.created_datetime)

    # submission: dict = sqm.Field(default=None, sa_column=sqa.Column(sqa.JSON))

    # @_p.field_validator('submission', mode='before')
    # def validate_submission(cls, v):
    #     return submission_to_dict(v)

    @classmethod
    def from_submission(cls, submission: Submission):
        tdict = dict(
            reddit_id=submission.id,
            title=submission.title,
            shortlink=submission.shortlink,
            created_datetime=submission.created_utc,
            # submission=submission,
        )
        return cls.model_validate(tdict)


class RedditThread(RedditThreadBase, table=True, extend_existing=True):
    id: int | None = sqm.Field(default=None, primary_key=True)

    gurus: list['Guru'] = Relationship(back_populates='reddit_threads', link_model=GuruRedditLink)
    # guru_excludes: list['Guru'] = Relationship(back_populates='reddit_excludes', link_model=GuruRedditExclude)
    # guru_excludes: list[int] = sqm.Field(default_factory=list, sa_column=Column(sqm.JSON))

    episodes: list['Episode'] = Relationship(back_populates='reddit_threads', link_model=EpisodeRedditLink)

    # episode_excludes: list[int] = sqm.Field(default_factory=list, sa_column=Column(sqm.JSON))
    # episode_excludes: list['Episode'] = Relationship(back_populates='reddit_excludes', link_model=EpisodeRedditExclude)

    def __hash__(self):
        return hash(self.reddit_id)

    def __eq__(self, other):
        return self.reddit_id == other.reddit_id

    @property
    def get_hash(self):
        return hashlib.md5(','.join([self.reddit_id]).encode('utf-8')).hexdigest()

    @property
    def slug(self):
        return f'/red/{self.id}'

    @classmethod
    def rout_prefix(cls):
        return '/red/'


def submission_str(submisssion: Submission):
    return f'{submisssion.title} - {dt_ordinal(datetime.fromtimestamp(submisssion.created_utc))}'
