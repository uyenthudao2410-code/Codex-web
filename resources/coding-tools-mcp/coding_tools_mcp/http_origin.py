from __future__ import annotations

"""HTTP origin validation shared by the MCP handler and CORS responses."""

import os
import urllib.parse

from .envutils import ENV_PREFIX


def _configured_allowed_origins(raw: str) -> frozenset[str]:
    return frozenset(item.strip().rstrip("/") for item in raw.split(",") if item.strip())


def is_allowed_origin(origin: str) -> bool:
    # Authentication does not replace browser Origin validation.
    try:
        parsed = urllib.parse.urlparse(origin)
    except ValueError:
        return False
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.params
        or parsed.query
        or parsed.fragment
    ):
        return False
    try:
        _ = parsed.port
    except ValueError:
        return False
    normalized = origin.rstrip("/")
    configured = _configured_allowed_origins(os.environ.get(f"{ENV_PREFIX}_ALLOWED_ORIGINS", ""))
    return parsed.hostname in {"localhost", "127.0.0.1", "::1"} or normalized in configured
