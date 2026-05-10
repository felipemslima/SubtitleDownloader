from __future__ import annotations

from subtitle_app.adb_client import get_android_start_locations, list_android_directories, scan_android_video_files


def listAndroidRoots():
    return get_android_start_locations()


def listAndroidDirectories(path: str):
    return list_android_directories(path)


def scanAndroidVideos(path: str):
    return scan_android_video_files(path)
