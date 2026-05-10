from __future__ import annotations

from flask import Blueprint, jsonify, request, send_file

from application.downloadProvider import buildSelectedPlansZip, downloadSelectedPlans
from application.episodeProvider import getSeasonEpisodes
from application.showProvider import searchShows
from application.subtitleProvider import scanSubtitlesForEpisodes

subtitleBp = Blueprint("subtitleBp", __name__)


@subtitleBp.get("/shows")
def getShows():
    query = request.args.get("q", "").strip()
    if not query:
        raise ValueError("Informe o parametro q.")
    return jsonify({"ok": True, "data": searchShows(query)}), 200


@subtitleBp.get("/shows/<int:tvmazeId>/episodes")
def getEpisodes(tvmazeId: int):
    season = int(request.args.get("season", "1"))
    show = {
        "index": 1,
        "name": request.args.get("name") or "Serie",
        "premiered": "?",
        "status": "?",
        "imdbId": request.args.get("imdbId") or "",
        "tvmazeId": tvmazeId,
    }
    return jsonify({"ok": True, "data": getSeasonEpisodes(show, season)}), 200


@subtitleBp.post("/subtitles/scan")
def postScanSubtitles():
    body = request.get_json(force=True) or {}
    return jsonify({"ok": True, "data": scanSubtitlesForEpisodes(body)}), 200


@subtitleBp.post("/download")
def postDownload():
    body = request.get_json(force=True) or {}
    return jsonify({"ok": True, "data": downloadSelectedPlans(body)}), 200


@subtitleBp.post("/download/zip")
def postDownloadZip():
    body = request.get_json(force=True) or {}
    archive, fileName = buildSelectedPlansZip(body)
    return send_file(
        archive,
        mimetype="application/zip",
        as_attachment=True,
        download_name=fileName,
    )
