from __future__ import annotations

import os
import sys
from pathlib import Path

from flask import Flask, redirect, send_from_directory
from flask_cors import CORS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def loadDotEnv(path: Path) -> None:
    if not path.exists():
        return

    for rawLine in path.read_text(encoding="utf-8").splitlines():
        line = rawLine.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


loadDotEnv(PROJECT_ROOT / ".env")

from api.routes.errorHandlers import registerErrorHandlers
from api.routes.healthRoutes import healthBp
from api.routes.subtitleRoutes import subtitleBp


def createApp() -> Flask:
    app = Flask(__name__, static_folder="static")
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    registerErrorHandlers(app)
    app.register_blueprint(healthBp, url_prefix="/api")
    app.register_blueprint(subtitleBp, url_prefix="/api")

    @app.get("/docs")
    def docs():
        return send_from_directory(app.static_folder, "index.html")

    @app.get("/subtitleDownloader.yaml")
    def openApiSpec():
        return send_from_directory(Path(app.static_folder) / "dist", "subtitleDownloader.yaml")

    @app.get("/")
    def root():
        return redirect("/docs")

    return app


app = createApp()


if __name__ == "__main__":
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_PORT", "5000"))
    app.run(host=host, port=port, debug=True)
