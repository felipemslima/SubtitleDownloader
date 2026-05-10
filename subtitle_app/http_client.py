from __future__ import annotations

import json
from typing import Any
from urllib.request import Request, urlopen

from .config import APP_USER_AGENT


def http_get(url: str, *, timeout: int = 25) -> tuple[bytes, dict[str, str]]:
    request = Request(
        url,
        headers={
            "User-Agent": APP_USER_AGENT,
            "Accept": "*/*",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        headers = {key.lower(): value for key, value in response.headers.items()}
        return response.read(), headers


def http_json(url: str, *, timeout: int = 25) -> Any:
    body, _headers = http_get(url, timeout=timeout)
    return json.loads(body.decode("utf-8"))
