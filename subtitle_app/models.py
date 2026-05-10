from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from pathlib import PurePosixPath


@dataclass(frozen=True)
class ShowCandidate:
    index: int
    name: str
    premiered: str
    status: str
    imdb_id: str
    tvmaze_id: int | None


@dataclass(frozen=True)
class Episode:
    season: int
    number: int
    title: str
    airdate: str = ""

    @property
    def code(self) -> str:
        return f"S{self.season:02d}E{self.number:02d}"


@dataclass(frozen=True)
class Subtitle:
    index: int
    subtitle_id: str
    language: str
    url: str
    encoding: str
    match_kind: str


@dataclass(frozen=True)
class VideoFile:
    path: Path | str
    season: int | None = None
    episode: int | None = None
    source: str = "local"

    @property
    def display_name(self) -> str:
        if self.source == "android":
            return PurePosixPath(str(self.path)).name
        return Path(self.path).name

    @property
    def key(self) -> str:
        return f"{self.source}:{self.path}"


@dataclass
class EpisodeSubtitlePlan:
    episode: Episode
    subtitles: list[Subtitle] = field(default_factory=list)
    selected_subtitle: Subtitle | None = None
    enabled: bool = True
    status: str = "Pendente"
    output_path: Path | str | None = None
    target_video: VideoFile | None = None

    @property
    def subtitle_count(self) -> int:
        return len(self.subtitles)
