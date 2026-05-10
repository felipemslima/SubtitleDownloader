from __future__ import annotations

from pathlib import PurePosixPath

from infrastructure.apis.androidDeviceApi import listAndroidDirectories, listAndroidRoots
from subtitle_app.adb_client import parent_remote_path


def getAndroidRoots() -> list[dict]:
    return [{"label": label, "path": path} for label, path in listAndroidRoots()]


def getAndroidDirectories(path: str) -> dict:
    directories = listAndroidDirectories(path)
    return {
        "path": path,
        "parent": parent_remote_path(path),
        "directories": [{"name": PurePosixPath(directory).name, "path": directory} for directory in directories],
    }
