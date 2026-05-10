from __future__ import annotations

from flask import Blueprint, jsonify, request

from application.androidBrowser import getAndroidDirectories, getAndroidRoots

androidBp = Blueprint("androidBp", __name__)


@androidBp.get("/android/roots")
def getRoots():
    return jsonify({"ok": True, "data": getAndroidRoots()}), 200


@androidBp.get("/android/directories")
def getDirectories():
    path = request.args.get("path", "/sdcard")
    return jsonify({"ok": True, "data": getAndroidDirectories(path)}), 200
