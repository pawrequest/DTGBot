import datetime as dt

import scrapaw
from . import guru_m, reddit_m


class EpisodeOut(scrapaw.EpisodeBase):
    id: int
    title: str
    url: str
    date: dt.date
    notes: list[str]
    links: dict[str, str]
    number: str

    gurus: list[guru_m.GuruBase]
    reddit_threads: list[reddit_m.RedditThreadBase]

    @property
    def slug(self):
        return f'/eps/{self.id}'


class GuruOut(guru_m.GuruBase):
    id: int
    episodes: list[scrapaw.EpisodeBase]
    reddit_threads: list[reddit_m.RedditThreadBase]


class RedditThreadOut(reddit_m.RedditThreadBase):
    id: int
    gurus: list[guru_m.GuruBase]
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
