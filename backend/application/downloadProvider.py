from __future__ import annotations

from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

from application.serializers import planFromDict, planToDict, showFromDict
from infrastructure.apis.subtitleCoreApi import downloadService
from subtitle_app.text_utils import safe_filename


def downloadSelectedPlans(payload: dict) -> list[dict]:
    show = showFromDict(payload.get("show") or {})
    outputDir = Path(str(payload.get("outputDir") or "downloads")).expanduser().resolve()
    plans = [planFromDict(item) for item in payload.get("plans") or []]
    downloaded = []
    for plan in plans:
        if not plan.enabled or not plan.selected_subtitle:
            continue
        downloadService.download_plan(show, plan, outputDir)
        downloaded.append(planToDict(plan))
    return downloaded


def buildSelectedPlansZip(payload: dict) -> tuple[BytesIO, str]:
    show = showFromDict(payload.get("show") or {})
    plans = [planFromDict(item) for item in payload.get("plans") or []]
    archive = BytesIO()

    with TemporaryDirectory(prefix="subtitle_downloader_") as tmpDir:
        stagingDir = Path(tmpDir)
        with ZipFile(archive, "w", compression=ZIP_DEFLATED) as zipFile:
            for plan in plans:
                if not plan.enabled or not plan.selected_subtitle:
                    continue

                outputBase = downloadService.build_output_base(show, plan.episode, plan.selected_subtitle, stagingDir)
                downloadedPath = downloadService.download_subtitle(plan.selected_subtitle, outputBase)
                archiveName = _archive_name_for_plan(plan, downloadedPath.suffix, stagingDir, downloadedPath)
                zipFile.write(downloadedPath, archiveName)
                plan.output_path = archiveName
                plan.status = "Adicionado ao ZIP"

    archive.seek(0)
    season = plans[0].episode.season if plans else 1
    fileName = safe_filename(f"{show.name or show.imdb_id or 'legendas'}-season-{season:02d}-subtitles.zip")
    return archive, fileName


def _archive_name_for_plan(plan, suffix: str, stagingDir: Path, downloadedPath: Path) -> str:
    if not plan.target_video:
        return downloadedPath.relative_to(stagingDir).as_posix()

    target = str(plan.target_video.path).replace("\\", "/").strip("/")
    if not target:
        return downloadedPath.name

    parts = [safe_filename(part) for part in target.split("/") if part not in {"", ".", ".."}]
    if not parts:
        return downloadedPath.name

    videoPath = Path(*parts)
    return videoPath.with_suffix(suffix).as_posix()
