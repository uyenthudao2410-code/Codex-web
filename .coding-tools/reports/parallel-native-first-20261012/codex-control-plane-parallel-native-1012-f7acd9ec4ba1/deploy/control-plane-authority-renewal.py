#!/usr/bin/env python3
"""Renew bounded shared-service authority without opening admission.

The systemd timer invokes this script with the protected operator environment.
It keeps the existing service bearer and exact live workspace pilots alive only
within the configured pilot anchor's owner, principal and device. Local folder
activation adds immutable decisions without changing that authority. This
script never creates a principal, issues a new bearer, changes admission,
changes a binding, or prints authorization material.
"""

from __future__ import annotations

import json
import os
import re
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


def _identity(item: dict[str, Any], field: str) -> str:
    value = item.get(field)
    if not isinstance(value, str) or re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value) is None:
        raise RenewalError(f"authority observation has invalid {field}")
    return value


def _expiry(item: dict[str, Any]) -> int:
    value = item.get("expires_at_ms")
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise RenewalError("authority observation has invalid expiry")
    return value


def _selected_pilots(
    decisions: Any, anchor: dict[str, Any], grant: dict[str, Any], now: int,
) -> list[dict[str, Any]]:
    """Follow exact live decisions within the already approved node."""
    if not isinstance(decisions, list) or any(not isinstance(item, dict) for item in decisions):
        raise RenewalError("operator API response has no valid pilot list")
    active = [item for item in decisions if item.get("revoked_at_ms") is None and _expiry(item) > now]
    selected = [item for item in active if all(
        _identity(item, field) == _identity(anchor, field)
        for field in ("owner_id", "principal_id", "device_id", "endpoint_id")
    )]
    if not selected:
        raise RenewalError("no live scoped pilot matches the configured identity anchor")
    targets = set()
    for item in selected:
        for field in ("owner_id", "principal_id"):
            if _identity(item, field) != _identity(grant, field):
                raise RenewalError("selected scoped pilot does not match the configured service grant")
        for field in ("decision_id", "binding_id", "workspace_id", "workspace_generation"):
            _identity(item, field)
        target = (item["binding_id"], item["workspace_id"], item["workspace_generation"])
        if target in targets:
            raise RenewalError("multiple live scoped pilot decisions cover the same target")
        targets.add(target)
    return sorted(selected, key=lambda item: item["decision_id"])


def _verify_renewal(renewed: dict[str, Any], original: dict[str, Any], expiry: int, fields: tuple[str, ...]) -> None:
    if _expiry(renewed) != expiry or renewed.get("revoked_at_ms") is not None:
        raise RenewalError("renewal receipt does not match the requested live expiry")
    if any(_identity(renewed, field) != _identity(original, field) for field in fields):
        raise RenewalError("renewal receipt changed the selected authority identity")


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
    decisions = _json_request(base_url, operator_token, "/v1/scoped-pilot-decisions", opener=opener).get("scoped_pilot_decisions")
    anchor = _one(decisions, "decision_id", decision_id)
    _identity(grant, "grant_id")
    _identity(anchor, "decision_id")
    for field in ("owner_id", "principal_id"):
        if _identity(grant, field) != _identity(anchor, field):
            raise RenewalError("configured pilot anchor does not match the configured service grant")
    for field in ("device_id", "endpoint_id"):
        _identity(anchor, field)
    if grant.get("revoked_at_ms") is not None or _expiry(grant) <= now:
        raise RenewalError("configured service grant is expired or revoked")
    admission = _json_request(base_url, operator_token, "/v1/maintenance/admission", opener=opener)
    mode = admission.get("admission_mode")
    if mode not in {"scoped_pilot", "recovery", "open"}:
        raise RenewalError("operator API returned an invalid admission mode")
    selected = _selected_pilots(decisions, anchor, grant, now) if mode == "scoped_pilot" else [anchor]
    decision = next((item for item in selected if item["decision_id"] == decision_id), selected[0])
    selected_decision_id = _identity(decision, "decision_id")
    result: dict[str, Any] = {
        "enabled": True,
        "admission_mode": mode,
        "grant_id": grant_id,
        "configured_decision_id": decision_id,
        "decision_id": selected_decision_id,
        "followed_selected_pilot": selected_decision_id != decision_id,
        "grant": {"expires_at_ms": grant["expires_at_ms"], "renewed": False},
        "decision": {"expires_at_ms": _expiry(decision), "renewed": False},
        "decisions": [{"decision_id": item["decision_id"], "expires_at_ms": _expiry(item), "renewed": False}
                      for item in selected],
    }
    grant_target = min(now + grant_ttl * 1000, now + MAX_GRANT_TTL_SECONDS * 1000 - 1000)
    if _expiry(grant) - now <= grant_window * 1000 and grant_target > _expiry(grant):
        renewed = _json_request(
            base_url,
            operator_token,
            f"/v1/mcp-service-grants/{grant_id}/renew",
            method="POST",
            body={"expires_at_ms": grant_target},
            opener=opener,
        )
        _verify_renewal(renewed, grant, grant_target, ("grant_id", "owner_id", "principal_id"))
        result["grant"] = {"expires_at_ms": renewed["expires_at_ms"], "renewed": True}
    # Recovery is an intentional maintenance state.  Never reopen it from a
    # timer, and never renew a pilot while its admission is not selected.
    pilot_target = min(now + pilot_ttl * 1000, now + MAX_PILOT_TTL_SECONDS * 1000 - 1000)
    for item, observation in zip(selected, result["decisions"]):
        if (mode == "scoped_pilot" and _expiry(item) - now <= pilot_window * 1000
                and pilot_target > _expiry(item)):
            renewed = _json_request(
                base_url, operator_token,
                f"/v1/scoped-pilot-decisions/{item['decision_id']}/renew",
                method="POST", body={"expires_at_ms": pilot_target}, opener=opener,
            )
            _verify_renewal(renewed, item, pilot_target, (
                "decision_id", "owner_id", "principal_id", "device_id", "endpoint_id",
                "binding_id", "workspace_id", "workspace_generation",
            ))
            observation.update(expires_at_ms=renewed["expires_at_ms"], renewed=True)
        if item["decision_id"] == selected_decision_id:
            result["decision"] = {key: observation[key] for key in ("expires_at_ms", "renewed")}
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
