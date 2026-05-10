from __future__ import annotations

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException


def registerErrorHandlers(app: Flask) -> None:
    @app.errorhandler(ValueError)
    def valueError(error: ValueError):
        return jsonify({"ok": False, "error": str(error)}), 400

    @app.errorhandler(HTTPException)
    def httpError(error: HTTPException):
        return jsonify({"ok": False, "error": error.description}), error.code or 500

    @app.errorhandler(Exception)
    def unexpectedError(error: Exception):
        return jsonify({"ok": False, "error": str(error)}), 500
