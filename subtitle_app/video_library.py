from __future__ import annotations

import re
from pathlib import Path

from .models import Episode, VideoFile


VIDEO_EXTENSIONS = {
    ".mkv",
    ".mp4",
    ".avi",
    ".mov",
    ".m4v",
    ".wmv",
    ".mpg",
    ".mpeg",
    ".ts",
    ".m2ts",
    ".vob",
}


def normalize_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def parse_episode_from_name(name: str) -> tuple[int | None, int | None]:
    value = name.lower()
    patterns = [
        r"s(?P<season>\d{1,2})[ ._-]*e(?P<episode>\d{1,3})",
        r"(?P<season>\d{1,2})x(?P<episode>\d{1,3})",
        r"season[ ._-]*(?P<season>\d{1,2}).*episode[ ._-]*(?P<episode>\d{1,3})",
    ]

    for pattern in patterns:
        match = re.search(pattern, value, re.IGNORECASE)
        if match:
            return int(match.group("season")), int(match.group("episode"))

    return None, None


def scan_video_files(folder: Path | str, recursive: bool = True) -> list[VideoFile]:
    base = Path(folder).expanduser().resolve()
    if not base.exists() or not base.is_dir():
        raise ValueError(f"Pasta de videos invalida: {base}")

    iterator = base.rglob("*") if recursive else base.iterdir()
    videos: list[VideoFile] = []
    for path in iterator:
        if not path.is_file() or path.suffix.lower() not in VIDEO_EXTENSIONS:
            continue
        season, episode = parse_episode_from_name(path.name)
        videos.append(VideoFile(path=path, season=season, episode=episode))

    return sorted(videos, key=lambda video: str(video.path).lower())


def match_video_for_episode(episode: Episode, videos: list[VideoFile]) -> VideoFile | None:
    for video in videos:
        if video.season == episode.season and video.episode == episode.number:
            return video

    episode_title = normalize_title(episode.title)
    if episode_title:
        title_matches = [video for video in videos if episode_title in normalize_title(Path(str(video.path)).stem)]
        if len(title_matches) == 1:
            return title_matches[0]

    return None


def assign_videos_to_plans(plans, videos: list[VideoFile]) -> None:
    used_keys: set[str] = set()
    for plan in plans:
        match = match_video_for_episode(plan.episode, [video for video in videos if video.key not in used_keys])
        plan.target_video = match
        if match:
            used_keys.add(match.key)
