from __future__ import annotations

from application.serializers import episodeFromDict, planToDict, showFromDict, videoFromDict
from infrastructure.apis.subtitleCoreApi import downloadService
from subtitle_app.video_library import assign_videos_to_plans


def scanSubtitlesForEpisodes(payload: dict) -> list[dict]:
    show = showFromDict(payload.get("show") or {})
    episodes = [episodeFromDict(item) for item in payload.get("episodes") or []]
    language = str(payload.get("language") or "pob")
    videos = [video for video in (videoFromDict(item) for item in payload.get("videos") or []) if video]

    plans = [downloadService.scan_episode(show, episode, language) for episode in episodes]
    if videos:
        assign_videos_to_plans(plans, videos)
    return [planToDict(plan) for plan in plans]
