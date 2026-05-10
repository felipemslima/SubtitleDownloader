from __future__ import annotations

from pathlib import Path

from subtitle_app.video_library import scan_video_files


def scanLocalVideos(folder: Path):
    return scan_video_files(folder, recursive=True)
