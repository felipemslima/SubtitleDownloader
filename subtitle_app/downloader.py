from __future__ import annotations

import time
from shutil import copy2
from pathlib import Path
from typing import Callable

from .config import DEFAULT_OUTPUT_DIR
from .adb_client import android_subtitle_path_for_video, push_file
from .http_client import http_get
from .models import Episode, EpisodeSubtitlePlan, ShowCandidate, Subtitle
from .providers import OpenSubtitlesV3Client
from .text_utils import infer_extension, safe_filename


ProgressCallback = Callable[[EpisodeSubtitlePlan, str], None]


class SubtitleDownloadService:
    def __init__(self, opensubtitles: OpenSubtitlesV3Client | None = None) -> None:
        self.opensubtitles = opensubtitles or OpenSubtitlesV3Client()

    def build_output_base(
        self,
        show: ShowCandidate,
        episode: Episode,
        subtitle: Subtitle,
        output_dir: Path,
    ) -> Path:
        series_name = show.name if not show.name.startswith("tt") else show.imdb_id
        season_dir = output_dir / safe_filename(series_name) / f"Season {episode.season:02d}"
        file_name = safe_filename(
            f"{series_name} - {episode.code} - {episode.title}.{subtitle.language}"
        )
        return season_dir / file_name

    def download_subtitle(self, subtitle: Subtitle, output_path_without_ext: Path) -> Path:
        body, headers = http_get(subtitle.url, timeout=40)
        extension = infer_extension(body, headers, subtitle.url)
        output_path = output_path_without_ext.with_suffix(f".{extension}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(body)
        return output_path

    def scan_episode(
        self,
        show: ShowCandidate,
        episode: Episode,
        language: str,
        include_all: bool = False,
    ) -> EpisodeSubtitlePlan:
        subtitles = self.opensubtitles.fetch_subtitles(
            show.imdb_id,
            episode.season,
            episode.number,
            language,
            include_all=include_all,
        )
        status = f"{len(subtitles)} legenda(s)" if subtitles else "Sem legenda"
        return EpisodeSubtitlePlan(
            episode=episode,
            subtitles=subtitles,
            selected_subtitle=subtitles[0] if subtitles else None,
            enabled=bool(subtitles),
            status=status,
        )

    def scan_season(
        self,
        show: ShowCandidate,
        episodes: list[Episode],
        language: str,
        include_all: bool = False,
        progress: ProgressCallback | None = None,
    ) -> list[EpisodeSubtitlePlan]:
        plans: list[EpisodeSubtitlePlan] = []
        for episode in episodes:
            plan = self.scan_episode(show, episode, language, include_all=include_all)
            plans.append(plan)
            if progress:
                progress(plan, "scanned")
            time.sleep(0.15)
        return plans

    def download_plan(
        self,
        show: ShowCandidate,
        plan: EpisodeSubtitlePlan,
        output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    ) -> Path:
        if not plan.selected_subtitle:
            raise ValueError(f"{plan.episode.code}: nenhuma legenda selecionada")

        if plan.target_video and plan.target_video.source == "android":
            output_base = self.build_output_base(
                show,
                plan.episode,
                plan.selected_subtitle,
                DEFAULT_OUTPUT_DIR / "_staging_android",
            )
        else:
            output_base = self.build_output_base(show, plan.episode, plan.selected_subtitle, Path(output_dir))

        output_path = self.download_subtitle(plan.selected_subtitle, output_base)
        if plan.target_video:
            if plan.target_video.source == "android":
                remote_path = android_subtitle_path_for_video(str(plan.target_video.path), output_path.suffix)
                push_file(output_path, remote_path)
                output_path = remote_path
            else:
                final_path = Path(plan.target_video.path).with_suffix(output_path.suffix)
                copy2(output_path, final_path)
                output_path = final_path
        plan.output_path = output_path
        plan.status = "Baixado"
        return output_path
