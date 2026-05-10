from __future__ import annotations

from flask import Blueprint, jsonify

healthBp = Blueprint("healthBp", __name__)


@healthBp.get("/health")
def getHealth():
    return jsonify({"ok": True, "data": {"service": "subtitle-downloader-web"}}), 200
