from __future__ import annotations

from flask import Blueprint, jsonify, request

from application.videoProvider import scanVideos

videoBp = Blueprint("videoBp", __name__)


@videoBp.post("/videos/scan")
def postScanVideos():
    body = request.get_json(force=True) or {}
    return jsonify({"ok": True, "data": scanVideos(body)}), 200
