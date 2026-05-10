from __future__ import annotations

from subtitle_app.downloader import SubtitleDownloadService
from subtitle_app.providers import OpenSubtitlesV3Client, TvMazeClient

tvmazeClient = TvMazeClient()
openSubtitlesClient = OpenSubtitlesV3Client()
downloadService = SubtitleDownloadService(openSubtitlesClient)
