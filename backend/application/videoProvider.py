from __future__ import annotations

from pathlib import Path

from application.serializers import videoToDict
from infrastructure.apis.androidDeviceApi import scanAndroidVideos
from infrastructure.files.videoStorage import scanLocalVideos


def scanVideos(payload: dict) -> list[dict]:
    source = str(payload.get("source") or "local")
    folder = str(payload.get("folder") or "").strip()
    if not folder:
        raise ValueError("Informe a pasta dos videos.")
    if source == "android":
        videos = scanAndroidVideos(folder)
    else:
        videos = scanLocalVideos(Path(folder))
    return [videoToDict(video) for video in videos]
