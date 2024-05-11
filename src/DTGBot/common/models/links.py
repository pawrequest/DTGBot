# from __future__ import annotations

from sqlmodel import Field, SQLModel


class GuruEpisodeLink(SQLModel, table=True):
    guru_id: int | None = Field(default=None, foreign_key='guru.id', primary_key=True)
    episode_id: int | None = Field(default=None, foreign_key='episode.id', primary_key=True)


class GuruEpisodeExclude(SQLModel, table=True):
    guru_id: int | None = Field(default=None, foreign_key='guru.id', primary_key=True)
    episode_id: int | None = Field(default=None, foreign_key='episode.id', primary_key=True)


class GuruRedditLink(SQLModel, table=True):
    reddit_thread_id: int | None = Field(default=None, foreign_key='redditthread.id', primary_key=True)
    guru_id: int | None = Field(default=None, foreign_key='guru.id', primary_key=True)


class GuruRedditExclude(SQLModel, table=True):
    guru_id: int | None = Field(default=None, foreign_key='guru.id', primary_key=True)
    reddit_thread_id: int | None = Field(default=None, foreign_key='redditthread.id', primary_key=True)


class EpisodeRedditLink(SQLModel, table=True):
    reddit_thread_id: int | None = Field(default=None, foreign_key='redditthread.id', primary_key=True)
    episode_id: int | None = Field(default=None, foreign_key='episode.id', primary_key=True)


class EpisodeRedditExclude(SQLModel, table=True):
    reddit_thread_id: int | None = Field(default=None, foreign_key='redditthread.id', primary_key=True)
    episode_id: int | None = Field(default=None, foreign_key='episode.id', primary_key=True)


