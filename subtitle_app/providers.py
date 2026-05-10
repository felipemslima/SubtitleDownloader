from __future__ import annotations

from urllib.parse import urlencode

from .config import OPENSUBTITLES_V3_URL, TVMAZE_SEARCH_URL, TVMAZE_SHOW_EPISODES_URL
from .http_client import http_json
from .models import Episode, ShowCandidate, Subtitle
from .text_utils import normalize_imdb, strip_html, wanted_language_codes


class TvMazeClient:
    def search_shows(self, query: str) -> list[ShowCandidate]:
        imdb_id = normalize_imdb(query)
        if imdb_id:
            return [ShowCandidate(1, imdb_id, "?", "IMDb id informado", imdb_id, None)]

        url = f"{TVMAZE_SEARCH_URL}?{urlencode({'q': query})}"
        data = http_json(url)
        candidates: list[ShowCandidate] = []

        for item in data:
            show = item.get("show") or {}
            externals = show.get("externals") or {}
            show_imdb_id = externals.get("imdb")
            if not show_imdb_id:
                continue
            candidates.append(
                ShowCandidate(
                    index=len(candidates) + 1,
                    name=show.get("name") or "Untitled",
                    premiered=show.get("premiered") or "?",
                    status=show.get("status") or "?",
                    imdb_id=show_imdb_id,
                    tvmaze_id=show.get("id"),
                )
            )

        return candidates

    def fetch_episodes(self, show: ShowCandidate, season: int) -> list[Episode]:
        if not show.tvmaze_id:
            raise ValueError("Para carregar uma temporada inteira, selecione a serie pela busca do TVMaze.")

        url = TVMAZE_SHOW_EPISODES_URL.format(show_id=show.tvmaze_id)
        data = http_json(url)
        episodes: list[Episode] = []

        for raw in data:
            if int(raw.get("season") or 0) != season:
                continue
            number = raw.get("number")
            if not number:
                continue
            episodes.append(
                Episode(
                    season=season,
                    number=int(number),
                    title=strip_html(raw.get("name")) or f"Episodio {number}",
                    airdate=raw.get("airdate") or "",
                )
            )

        return sorted(episodes, key=lambda episode: episode.number)


class OpenSubtitlesV3Client:
    def fetch_subtitles(
        self,
        imdb_id: str,
        season: int,
        episode: int,
        language: str | None,
        include_all: bool = False,
    ) -> list[Subtitle]:
        url = f"{OPENSUBTITLES_V3_URL}/series/{imdb_id}:{season}:{episode}.json"
        data = http_json(url)
        raw_subtitles = data.get("subtitles") or []
        wanted = wanted_language_codes(language, include_all)

        subtitles: list[Subtitle] = []
        for raw in raw_subtitles:
            lang = str(raw.get("lang") or "").lower()
            sub_url = str(raw.get("url") or "")
            if not lang or not sub_url:
                continue
            if wanted is not None and lang not in wanted:
                continue
            subtitles.append(
                Subtitle(
                    index=len(subtitles) + 1,
                    subtitle_id=str(raw.get("id") or "?"),
                    language=lang,
                    url=sub_url,
                    encoding=str(raw.get("SubEncoding") or raw.get("encoding") or "?"),
                    match_kind=str(raw.get("m") or "?"),
                )
            )

        return subtitles
