from __future__ import annotations

from pathlib import Path


APP_USER_AGENT = "SubtitleDownloader/0.2"
TVMAZE_SEARCH_URL = "https://api.tvmaze.com/search/shows"
TVMAZE_SHOW_EPISODES_URL = "https://api.tvmaze.com/shows/{show_id}/episodes"
OPENSUBTITLES_V3_URL = "https://opensubtitles-v3.strem.io/subtitles"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[1] / "downloads"

LANGUAGE_ALIASES = {
    "br": {"pob"},
    "pt-br": {"pob"},
    "pt_br": {"pob"},
    "pob": {"pob"},
    "portugues-brasil": {"pob"},
    "pt": {"por", "pob"},
    "por": {"por"},
    "en": {"eng"},
    "eng": {"eng"},
    "es": {"spa"},
    "spa": {"spa"},
}
