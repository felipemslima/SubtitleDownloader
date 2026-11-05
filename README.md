# Subtitle Downloader

**Fetch subtitles for an entire TV season and drop each one next to its video file, renamed to match.** Works with folders on your PC or directly on an Android device over ADB.

<!-- TODO: add a screenshot of the GUI and of the web app -->

One core library, three front-ends: a **CLI**, a **desktop GUI** (Tkinter) and a **web app / PWA** (Flask + React).

## Features

- Search a show by name (TVMaze → IMDb id) or by IMDb id directly
- Query the public **OpenSubtitles V3** endpoint used by Stremio (no API key needed)
- **Season mode:** load every episode, pick the best subtitle for each one, and download them all in one go
- **Automatic matching:** reads the video folder, figures out which file is `S01E03` and saves the subtitle as `Show.S01E03.srt` next to it. You can override the match manually.
- **Android over ADB:** browse the phone's storage (including SD cards under `/storage/XXXX-XXXX`) and `adb push` subtitles straight to the device. MTP folders can't be opened from Python, so this goes through ADB instead.
- Filters to Brazilian Portuguese by default, with an option to list all languages
- The core library uses **only the Python standard library**

## Architecture

```
                 ┌──────────────────────────────────────────┐
                 │        subtitle_app/  (shared core)      │
                 │  providers · downloader · video_library  │
                 │  adb_client · http_client (stdlib only)  │
                 └───────▲──────────────▲──────────────▲────┘
                         │              │              │
                 ┌───────┴──┐   ┌───────┴──┐   ┌───────┴─────────────┐
                 │   CLI    │   │ Tkinter  │   │ Flask REST API      │
                 │          │   │   GUI    │   │ (layered: api /     │
                 └──────────┘   └──────────┘   │ application/domain/ │
                                               │ infrastructure)     │
                                               └───────▲─────────────┘
                                                       │ /api
                                               ┌───────┴─────────────┐
                                               │ React 19 + TS PWA   │
                                               │ TanStack Query      │
                                               └─────────────────────┘
```

- **Backend:** Flask with a layered structure (routes → application services → domain → infrastructure adapters). Endpoints include `/shows`, `/shows/<id>/episodes`, `/subtitles/scan`, `/download/zip`, `/videos/scan` and `/android/*`.
- **Frontend:** React 19 + TypeScript + Vite, with a data/domain/services split, TanStack Query and an installable **PWA** (manifest + service worker).
- **Deploy:** Docker Compose for local development. In production it runs behind **Nginx + Gunicorn + systemd** on an Ubuntu VM (see [INSTRUCOES_NUVEM.md](INSTRUCOES_NUVEM.md)).

## Quick start

### Desktop GUI

```bash
python subtitle_downloader.py --gui
```

Search the show → choose `Local` or `Android ADB` → read the video folder → load the season → **Search subtitles** → review → **Download selected**.

### CLI

```bash
# interactive
python subtitle_downloader.py

# one episode, non-interactive
python subtitle_downloader.py --series "Breaking Bad" --season 1 --episode 1 --first-show --first-subtitle

# by IMDb id, all languages, custom output folder
python subtitle_downloader.py --series tt0944947 --season 1 --episode 1 --all-languages --output-dir ./subs
```

### Web app

```bash
docker compose up --build
# API:  http://localhost:7001/api   (Swagger at /docs)
# Web:  http://localhost:7002
```

Or run it without Docker: `pip install -r backend/requirements.txt && python backend/app.py`, then `npm install && npm run dev` in `frontend/`.

### Android over ADB

Install Android Platform Tools, enable USB debugging and connect the phone. If `adb` is not on your `PATH`, set `ADB_PATH` to its full path.

## Project layout

```
subtitle_app/     # shared core: models, providers, matching, ADB, CLI, GUI
backend/          # Flask API (api / application / domain / infrastructure / tests)
frontend/         # React + TypeScript PWA
docker-compose.yml
```

## Notes

The OpenSubtitles V3 endpoint is a public service. For bulk automation, use a queue, low concurrency and a local cache to avoid temporary blocks.
