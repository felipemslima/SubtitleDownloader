from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError

from .config import DEFAULT_OUTPUT_DIR
from .downloader import SubtitleDownloadService
from .models import Episode, ShowCandidate, Subtitle
from .providers import OpenSubtitlesV3Client, TvMazeClient
from .text_utils import normalize_imdb, safe_filename


def choose_show(tvmaze: TvMazeClient, query: str, assume_first: bool = False) -> ShowCandidate:
    candidates = tvmaze.search_shows(query)
    if not candidates:
        raise RuntimeError(
            "Nao encontrei essa serie no TVMaze com IMDb associado. "
            "Tente digitar o IMDb id diretamente, exemplo: tt0944947."
        )

    if normalize_imdb(query):
        return candidates[0]

    print("\nSeries encontradas:")
    for candidate in candidates[:10]:
        print(
            f"{candidate.index:>2}. {candidate.name} "
            f"({candidate.premiered}) - {candidate.status} - {candidate.imdb_id}"
        )

    if assume_first or len(candidates) == 1:
        selected = candidates[0]
        print(f"\nUsando: {selected.name} ({selected.imdb_id})")
        return selected

    while True:
        raw = input("\nEscolha a serie pelo numero: ").strip()
        if raw.isdigit():
            number = int(raw)
            for candidate in candidates:
                if candidate.index == number:
                    return candidate
        print("Opcao invalida. Digite um numero da lista.")


def choose_subtitle(subtitles: list[Subtitle], assume_first: bool = False) -> Subtitle:
    if not subtitles:
        raise RuntimeError("Nenhuma legenda encontrada com os filtros informados.")

    print("\nLegendas disponiveis:")
    for subtitle in subtitles:
        print(
            f"{subtitle.index:>2}. lang={subtitle.language:<4} "
            f"id={subtitle.subtitle_id:<9} encoding={subtitle.encoding:<10} url={subtitle.url}"
        )

    if assume_first or len(subtitles) == 1:
        selected = subtitles[0]
        print(f"\nUsando legenda #{selected.index} ({selected.language}, id {selected.subtitle_id})")
        return selected

    while True:
        raw = input("\nEscolha a legenda pelo numero: ").strip()
        if raw.isdigit():
            number = int(raw)
            for subtitle in subtitles:
                if subtitle.index == number:
                    return subtitle
        print("Opcao invalida. Digite um numero da lista.")


def read_int(prompt: str, current: int | None) -> int:
    if current is not None:
        return current
    while True:
        raw = input(prompt).strip()
        if raw.isdigit() and int(raw) > 0:
            return int(raw)
        print("Digite um numero inteiro maior que zero.")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Busca e baixa legendas de series pelo OpenSubtitles V3 usado pelo Stremio."
    )
    parser.add_argument("-s", "--series", help="Nome da serie ou IMDb id, exemplo: 'Breaking Bad' ou tt0903747")
    parser.add_argument("--season", type=int, help="Numero da temporada")
    parser.add_argument("--episode", type=int, help="Numero do episodio")
    parser.add_argument(
        "-l",
        "--language",
        default="pob",
        help="Codigo do idioma. Padrao: pob (Portugues Brasil). Use --all-languages para listar tudo.",
    )
    parser.add_argument("--all-languages", action="store_true", help="Nao filtra por idioma")
    parser.add_argument("-o", "--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Pasta de saida")
    parser.add_argument("--first-show", action="store_true", help="Seleciona automaticamente a primeira serie encontrada")
    parser.add_argument("--first-subtitle", action="store_true", help="Seleciona automaticamente a primeira legenda")
    parser.add_argument("--gui", action="store_true", help="Abre a interface grafica")
    return parser.parse_args(argv)


def run_single_episode(args: argparse.Namespace) -> int:
    tvmaze = TvMazeClient()
    opensubtitles = OpenSubtitlesV3Client()
    downloader = SubtitleDownloadService(opensubtitles)

    series_query = args.series or input("Serie ou IMDb id: ").strip()
    season = read_int("Temporada: ", args.season)
    episode_number = read_int("Episodio: ", args.episode)

    show = choose_show(tvmaze, series_query, assume_first=args.first_show)
    subtitles = opensubtitles.fetch_subtitles(
        show.imdb_id,
        season,
        episode_number,
        args.language,
        include_all=args.all_languages,
    )
    selected = choose_subtitle(subtitles, assume_first=args.first_subtitle)

    episode = Episode(season=season, number=episode_number, title=f"Episodio {episode_number}")
    series_name = show.name if not show.name.startswith("tt") else show.imdb_id
    base_name = safe_filename(
        f"{series_name} S{season:02d}E{episode_number:02d} {selected.language} opensubtitles-v3-{selected.subtitle_id}"
    )
    output_base = Path(args.output_dir).expanduser().resolve() / base_name

    print("\nBaixando...")
    output_path = downloader.download_subtitle(selected, output_base)
    print(f"Legenda salva em: {output_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    if args.gui:
        from .gui import main as gui_main

        gui_main()
        return 0

    try:
        return run_single_episode(args)
    except KeyboardInterrupt:
        print("\nCancelado.")
        return 130
    except (HTTPError, URLError, TimeoutError) as error:
        print(f"Erro de rede: {error}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as error:
        print(f"Resposta invalida da API: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1
    finally:
        time.sleep(0.2)
