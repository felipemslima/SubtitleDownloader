from __future__ import annotations

from infrastructure.apis.subtitleCoreApi import tvmazeClient
from application.serializers import showToDict


def searchShows(query: str) -> list[dict]:
    return [showToDict(show) for show in tvmazeClient.search_shows(query)]
