from __future__ import annotations

from pathlib import Path

from subtitle_app.models import Episode, EpisodeSubtitlePlan, ShowCandidate, Subtitle, VideoFile


def showToDict(show: ShowCandidate) -> dict:
    return {"index": show.index, "name": show.name, "premiered": show.premiered, "status": show.status, "imdbId": show.imdb_id, "tvmazeId": show.tvmaze_id}


def showFromDict(data: dict) -> ShowCandidate:
    return ShowCandidate(int(data.get("index") or 1), str(data.get("name") or data.get("imdbId") or "Untitled"), str(data.get("premiered") or "?"), str(data.get("status") or "?"), str(data.get("imdbId") or data.get("imdb_id") or ""), data.get("tvmazeId") or data.get("tvmaze_id"))


def episodeToDict(episode: Episode) -> dict:
    return {"season": episode.season, "number": episode.number, "code": episode.code, "title": episode.title, "airdate": episode.airdate}


def episodeFromDict(data: dict) -> Episode:
    return Episode(int(data.get("season") or 1), int(data.get("number") or data.get("episode") or 1), str(data.get("title") or data.get("name") or "Episodio"), str(data.get("airdate") or ""))


def subtitleToDict(subtitle: Subtitle) -> dict:
    return {"index": subtitle.index, "subtitleId": subtitle.subtitle_id, "language": subtitle.language, "url": subtitle.url, "encoding": subtitle.encoding, "matchKind": subtitle.match_kind}


def subtitleFromDict(data: dict) -> Subtitle:
    return Subtitle(int(data.get("index") or 1), str(data.get("subtitleId") or data.get("subtitle_id") or "?"), str(data.get("language") or "pob"), str(data.get("url") or ""), str(data.get("encoding") or "?"), str(data.get("matchKind") or data.get("match_kind") or "?"))


def videoToDict(video: VideoFile) -> dict:
    return {"path": str(video.path), "displayName": video.display_name, "season": video.season, "episode": video.episode, "source": video.source, "key": video.key}


def videoFromDict(data: dict | None) -> VideoFile | None:
    if not data:
        return None
    source = str(data.get("source") or "local")
    rawPath = str(data.get("path") or "")
    path = rawPath if source in {"android", "browser"} else Path(rawPath)
    return VideoFile(path, data.get("season"), data.get("episode"), source)


def planToDict(plan: EpisodeSubtitlePlan) -> dict:
    return {"episode": episodeToDict(plan.episode), "subtitles": [subtitleToDict(subtitle) for subtitle in plan.subtitles], "selectedSubtitle": subtitleToDict(plan.selected_subtitle) if plan.selected_subtitle else None, "enabled": plan.enabled, "status": plan.status, "outputPath": str(plan.output_path) if plan.output_path else None, "targetVideo": videoToDict(plan.target_video) if plan.target_video else None, "subtitleCount": plan.subtitle_count}


def planFromDict(data: dict) -> EpisodeSubtitlePlan:
    subtitles = [subtitleFromDict(item) for item in data.get("subtitles") or []]
    selected = subtitleFromDict(data["selectedSubtitle"]) if data.get("selectedSubtitle") else None
    return EpisodeSubtitlePlan(episodeFromDict(data.get("episode") or {}), subtitles, selected, bool(data.get("enabled", True)), str(data.get("status") or "Pendente"), target_video=videoFromDict(data.get("targetVideo")))
