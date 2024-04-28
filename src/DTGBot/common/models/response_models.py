import datetime as dt

import scrapaw

from DTGBot.common.models.guru_m import GuruBase
from DTGBot.common.models.reddit_m import RedditThreadBase


class EpisodeOut(scrapaw.EpisodeBase):
    id: int
    title: str
    url: str
    date: dt.date
    notes: list[str]
    links: dict[str, str]
    number: str

    gurus: list[GuruBase]
    reddit_threads: list[RedditThreadBase]

    @property
    def slug(self):
        return f'/eps/{self.id}'


class GuruOut(GuruBase):
    id: int
    episodes: list[scrapaw.EpisodeBase]
    reddit_threads: list[RedditThreadBase]


class RedditThreadOut(RedditThreadBase):
    id: int
    gurus: list[GuruBase]
    episodes: list[scrapaw.EpisodeBase]

# class EpisodeMeta(BaseModel):
#     length: int
#     msg: str = ""
#

# class EpisodeResponse(BaseModel):
#     meta: EpisodeMeta
#     episodes: list[Episode]
#
#     @classmethod
#     async def from_episodes(cls, episodes: Sequence[Episode], msg="") -> EpisodeResponse:
#         eps = [Episode.model_validate(ep) for ep in episodes]
#         if len(eps) == 0:
#             msg = "No Episodes Found"
#         meta_data = EpisodeMeta(
#             length=len(eps),
#             msg=msg,
#         )
#         res = cls.model_validate(dict(episodes=eps, meta=meta_data))
#         Episode.log_episodes(res.episodes, msg="Responding")
#         return res
#
#     def __str__(self):
#         return f"{self.__class__.__name__}: {self.meta.length} {self.episodes[0].__class__.__name__}s"
