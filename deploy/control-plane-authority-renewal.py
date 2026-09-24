#!/usr/bin/env python3
"""Renew bounded shared-service authority without opening admission.

The systemd timer invokes this script with the protected operator environment.
It keeps the existing service bearer and exact pilot target alive only while
they are still current.  It never creates a principal, issues a new bearer,
changes admission, changes a binding, or prints authorization material.
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


MAX_GRANT_TTL_SECONDS = 30 * 24 * 60 * 60
MAX_PILOT_TTL_SECONDS = 24 * 60 * 60
DEFAULT_GRANT_TTL_SECONDS = 28 * 24 * 60 * 60
DEFAULT_PILOT_TTL_SECONDS = 20 * 60 * 60
DEFAULT_GRANT_WINDOW_SECONDS = 24 * 60 * 60
DEFAULT_PILOT_WINDOW_SECONDS = 2 * 60 * 60


class RenewalError(RuntimeError):
    """A safe renewal observation or mutation failed."""


def _required(name: str) -> str:
    value = str(os.environ.get(name, "") or "").strip()
    if not value:
        raise RenewalError(f"{name} is required")
    return value


def _integer(name: str, default: int, *, minimum: int, maximum: int) -> int:
    raw = str(os.environ.get(name, str(default)) or "").strip()
    try:
        value = int(raw)
    except ValueError as error:
        raise RenewalError(f"{name} must be an integer") from error
    if not minimum <= value <= maximum:
        raise RenewalError(f"{name} is outside the allowed range")
    return value


def _enabled() -> bool:
    raw = str(os.environ.get("CONTROL_PLANE_AUTHORITY_RENEWAL_ENABLED", "false") or "").strip().lower()
    if raw not in {"true", "false"}:
        raise RenewalError("CONTROL_PLANE_AUTHORITY_RENEWAL_ENABLED must be true or false")
    return raw == "true"


def _operator_url() -> str:
    value = _required("CONTROL_PLANE_OPERATOR_URL").rstrip("/")
    if not value.startswith("https://"):
        raise RenewalError("CONTROL_PLANE_OPERATOR_URL must use https")
    return value


def _json_request(
    base_url: str,
    operator_token: str,
    path: str,
    *,
    method: str = "GET",
    body: dict[str, Any] | None = None,
    opener: Callable[..., Any] = urlopen,
) -> dict[str, Any]:
    payload = None if body is None else json.dumps(body, separators=(",", ":")).encode("utf-8")
    headers = {"Accept": "application/json", "Authorization": f"Bearer {operator_token}"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    request = Request(f"{base_url}{path}", data=payload, headers=headers, method=method)
    try:
        with opener(request, timeout=15) as response:
            parsed = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        # Do not echo the response body: a future endpoint must never be able
        # to put credentials or private task data into the systemd journal.
        raise RenewalError(f"operator API returned HTTP {error.code}") from error
    except (OSError, URLError, ValueError, json.JSONDecodeError) as error:
        raise RenewalError(f"operator API request failed: {type(error).__name__}") from error
    if not isinstance(parsed, dict):
        raise RenewalError("operator API returned a non-object response")
    return parsed


def _one(items: Any, key: str, value: str) -> dict[str, Any]:
    if not isinstance(items, list):
        raise RenewalError(f"operator API response has no {key} list")
    matches = [item for item in items if isinstance(item, dict) and item.get(key) == value]
    if len(matches) != 1:
        raise RenewalError(f"expected exactly one current {key}")
    return matches[0]


def renew_authority(
    *,
    environment: dict[str, str] | None = None,
    opener: Callable[..., Any] = urlopen,
    now_ms: int | None = None,
) -> dict[str, Any]:
    """Observe and, when necessary, renew configured bounded authorities."""

    source = os.environ if environment is None else environment
    if source is not os.environ:
        old = os.environ.copy()
        try:
            os.environ.clear()
            os.environ.update(source)
            return renew_authority(opener=opener, now_ms=now_ms)
        finally:
            os.environ.clear()
            os.environ.update(old)
    if not _enabled():
        return {"enabled": False, "state": "disabled"}
    base_url = _operator_url()
    operator_token = _required("CONTROL_PLANE_OPERATOR_TOKEN")
    grant_id = _required("CONTROL_PLANE_MCP_SERVICE_GRANT_ID")
    decision_id = _required("CONTROL_PLANE_SCOPED_PILOT_DECISION_ID")
    grant_ttl = _integer(
        "CONTROL_PLANE_AUTHORITY_GRANT_TTL_SECONDS", DEFAULT_GRANT_TTL_SECONDS,
        minimum=60, maximum=MAX_GRANT_TTL_SECONDS,
    )
    pilot_ttl = _integer(
        "CONTROL_PLANE_AUTHORITY_PILOT_TTL_SECONDS", DEFAULT_PILOT_TTL_SECONDS,
        minimum=60, maximum=MAX_PILOT_TTL_SECONDS,
    )
    grant_window = _integer(
        "CONTROL_PLANE_AUTHORITY_GRANT_WINDOW_SECONDS", DEFAULT_GRANT_WINDOW_SECONDS,
        minimum=1, maximum=MAX_GRANT_TTL_SECONDS,
    )
    pilot_window = _integer(
        "CONTROL_PLANE_AUTHORITY_PILOT_WINDOW_SECONDS", DEFAULT_PILOT_WINDOW_SECONDS,
        minimum=1, maximum=MAX_PILOT_TTL_SECONDS,
    )
    now = int(time.time() * 1000) if now_ms is None else int(now_ms)
    grant = _one(
        _json_request(base_url, operator_token, "/v1/mcp-service-grants", opener=opener).get("mcp_service_grants"),
        "grant_id", grant_id,
    )
    decision = _one(
        _json_request(base_url, operator_token, "/v1/scoped-pilot-decisions", opener=opener).get("scoped_pilot_decisions"),
        "decision_id", decision_id,
    )
    if grant.get("revoked_at_ms") is not None or int(grant.get("expires_at_ms", 0)) <= now:
        raise RenewalError("configured service grant is expired or revoked")
    if decision.get("revoked_at_ms") is not None or int(decision.get("expires_at_ms", 0)) <= now:
        raise RenewalError("configured scoped pilot decision is expired or revoked")
    admission = _json_request(base_url, operator_token, "/v1/maintenance/admission", opener=opener)
    mode = admission.get("admission_mode")
    result: dict[str, Any] = {
        "enabled": True,
        "admission_mode": mode,
        "grant_id": grant_id,
        "decision_id": decision_id,
        "grant": {"expires_at_ms": grant["expires_at_ms"], "renewed": False},
        "decision": {"expires_at_ms": decision["expires_at_ms"], "renewed": False},
    }
    if int(grant["expires_at_ms"]) - now <= grant_window:
        grant_target = min(
            now + grant_ttl * 1000,
            now + MAX_GRANT_TTL_SECONDS * 1000 - 1000,
        )
        renewed = _json_request(
            base_url,
            operator_token,
            f"/v1/mcp-service-grants/{grant_id}/renew",
            method="POST",
            body={"expires_at_ms": grant_target},
            opener=opener,
        )
        result["grant"] = {"expires_at_ms": renewed["expires_at_ms"], "renewed": True}
    # Recovery is an intentional maintenance state.  Never reopen it from a
    # timer, and never renew a pilot while its admission is not selected.
    if mode == "scoped_pilot" and int(decision["expires_at_ms"]) - now <= pilot_window:
        pilot_target = min(
            now + pilot_ttl * 1000,
            now + MAX_PILOT_TTL_SECONDS * 1000 - 1000,
        )
        renewed = _json_request(
            base_url,
            operator_token,
            f"/v1/scoped-pilot-decisions/{decision_id}/renew",
            method="POST",
            body={"expires_at_ms": pilot_target},
            opener=opener,
        )
        result["decision"] = {"expires_at_ms": renewed["expires_at_ms"], "renewed": True}
    return result


def main() -> int:
    try:
        result = renew_authority()
    except RenewalError as error:
        print(json.dumps({"ok": False, "error": str(error)}, separators=(",", ":")), file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, **result}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
