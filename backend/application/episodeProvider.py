from __future__ import annotations

from application.serializers import episodeToDict, showFromDict
from infrastructure.apis.subtitleCoreApi import tvmazeClient


def getSeasonEpisodes(showData: dict, season: int) -> list[dict]:
    show = showFromDict(showData)
    return [episodeToDict(episode) for episode in tvmazeClient.fetch_episodes(show, season)]
