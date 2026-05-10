from __future__ import annotations

import re
from html import unescape
from pathlib import Path
from urllib.parse import urlparse

from .config import LANGUAGE_ALIASES


def strip_html(value: str | None) -> str:
    if not value:
        return ""
    return unescape(re.sub(r"<[^>]+>", "", value)).strip()


def safe_filename(value: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', " ", value)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:140] or "subtitle"


def normalize_imdb(value: str) -> str | None:
    value = value.strip()
    match = re.search(r"(tt\d+)", value, re.IGNORECASE)
    if match:
        return match.group(1).lower()
    return None


def wanted_language_codes(language: str | None, include_all: bool) -> set[str] | None:
    if include_all or not language:
        return None
    key = language.strip().lower()
    return LANGUAGE_ALIASES.get(key, {key})


def infer_extension(body: bytes, headers: dict[str, str], url: str) -> str:
    content_disposition = headers.get("content-disposition", "")
    match = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)', content_disposition, re.IGNORECASE)
    if match:
        suffix = Path(match.group(1)).suffix.lower().lstrip(".")
        if suffix in {"srt", "vtt", "ass", "ssa", "sub"}:
            return suffix

    path_suffix = Path(urlparse(url).path).suffix.lower().lstrip(".")
    if path_suffix in {"srt", "vtt", "ass", "ssa", "sub"}:
        return path_suffix

    sample = body[:2048].decode("utf-8", errors="ignore").lstrip()
    if sample.startswith("WEBVTT"):
        return "vtt"
    if sample.startswith("[Script Info]") or "[Events]" in sample[:1000]:
        return "ass"
    return "srt"
