from __future__ import annotations

import shlex
import subprocess
import os
import shutil
from pathlib import Path, PurePosixPath

from .models import VideoFile
from .video_library import VIDEO_EXTENSIONS, parse_episode_from_name


class AdbError(RuntimeError):
    pass


def get_adb_command() -> str:
    configured = os.environ.get("ADB_PATH", "").strip()
    if configured:
        adb_path = Path(configured).expanduser()
        if adb_path.exists():
            return str(adb_path)
        raise AdbError(f"ADB_PATH aponta para um arquivo inexistente: {adb_path}")

    found = shutil.which("adb")
    if found:
        return found

    raise AdbError(
        "ADB nao encontrado. Instale Android Platform Tools e adicione a pasta ao PATH, "
        "ou defina ADB_PATH com o caminho completo do adb.exe."
    )


def run_adb(args: list[str], *, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    adb_command = get_adb_command()
    command = [adb_command, *args]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise AdbError(
            "ADB nao encontrado. Instale Android Platform Tools e adicione a pasta ao PATH, "
            "ou defina ADB_PATH com o caminho completo do adb.exe."
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise AdbError("ADB demorou demais para responder.") from exc

    if result.returncode != 0:
        details = (result.stderr or result.stdout or "").strip()
        raise AdbError(details or f"Comando adb falhou: {' '.join(command)}")
    return result


def ensure_device() -> None:
    result = run_adb(["devices"], timeout=15)
    lines = [line.strip() for line in result.stdout.splitlines()[1:] if line.strip()]
    devices = [line for line in lines if line.endswith("\tdevice")]
    if not devices:
        raise AdbError("Nenhum Android autorizado encontrado. Habilite USB debugging e aceite a autorizacao no aparelho.")


def join_remote_path(parent: str, child: str) -> str:
    parent = parent.rstrip("/") or "/"
    if parent == "/":
        return f"/{child.strip('/')}"
    return f"{parent}/{child.strip('/')}"


def parent_remote_path(path: str) -> str:
    cleaned = path.rstrip("/")
    if not cleaned or cleaned == "/":
        return "/"
    parent = str(PurePosixPath(cleaned).parent)
    return parent if parent else "/"


def list_android_directories(remote_folder: str) -> list[str]:
    ensure_device()
    folder = remote_folder.strip() or "/sdcard"
    quoted = shlex.quote(folder)
    try:
        result = run_adb(["shell", f"ls -1Ap {quoted}"], timeout=30)
        dirs: list[str] = []
        for raw_line in result.stdout.splitlines():
            name = raw_line.strip()
            if not name or name in {"./", "../"} or not name.endswith("/"):
                continue
            if name.startswith("."):
                continue
            dirs.append(join_remote_path(folder, name.rstrip("/")))
        return sorted(set(dirs), key=str.lower)
    except AdbError:
        result = run_adb(["shell", f"find {quoted} -maxdepth 1 -type d"], timeout=30)
        dirs = []
        for raw_line in result.stdout.splitlines():
            path = raw_line.strip()
            if not path or path.rstrip("/") == folder.rstrip("/"):
                continue
            dirs.append(path)
        return sorted(set(dirs), key=str.lower)


def get_android_start_locations() -> list[tuple[str, str]]:
    ensure_device()
    locations = [
        ("Armazenamento interno (/sdcard)", "/sdcard"),
        ("Armazenamento interno (/storage/emulated/0)", "/storage/emulated/0"),
    ]

    try:
        for path in list_android_directories("/storage"):
            name = PurePosixPath(path).name
            if name in {"self", "emulated"}:
                continue
            locations.append((f"Cartao/armazenamento externo ({path})", path))
    except AdbError:
        pass

    unique: dict[str, str] = {}
    for label, path in locations:
        unique[path] = label
    return [(label, path) for path, label in unique.items()]


def scan_android_video_files(remote_folder: str) -> list[VideoFile]:
    ensure_device()
    folder = remote_folder.strip() or "/sdcard"
    shell_command = f"find {shlex.quote(folder)} -type f"
    result = run_adb(["shell", shell_command], timeout=120)

    videos: list[VideoFile] = []
    for raw_line in result.stdout.splitlines():
        remote_path = raw_line.strip()
        if not remote_path:
            continue
        suffix = PurePosixPath(remote_path).suffix.lower()
        if suffix not in VIDEO_EXTENSIONS:
            continue
        season, episode = parse_episode_from_name(PurePosixPath(remote_path).name)
        videos.append(VideoFile(path=remote_path, season=season, episode=episode, source="android"))

    return sorted(videos, key=lambda video: str(video.path).lower())


def android_subtitle_path_for_video(remote_video_path: str, subtitle_suffix: str) -> str:
    video_path = PurePosixPath(remote_video_path)
    suffix = subtitle_suffix if subtitle_suffix.startswith(".") else f".{subtitle_suffix}"
    return str(video_path.with_suffix(suffix))


def push_file(local_file: Path, remote_path: str) -> None:
    ensure_device()
    run_adb(["push", str(local_file), remote_path], timeout=120)
