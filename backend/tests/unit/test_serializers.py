from __future__ import annotations

from application.serializers import episodeFromDict, episodeToDict


def testEpisodeSerializerRoundtrip():
    episode = episodeFromDict({"season": 1, "number": 2, "title": "Pilot"})
    assert episodeToDict(episode)["code"] == "S01E02"
