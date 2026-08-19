from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from typing import Any

from .usage_events import accounting_profile_for, canonicalize_usage


CANONICAL_USAGE_KEYS = (
    "input_total_tokens",
    "input_cached_tokens",
    "input_uncached_tokens",
    "input_cache_creation_tokens",
    "output_total_tokens",
    "output_reasoning_tokens",
    "output_nonreasoning_tokens",
    "total_tokens",
)


def canonical_usage_payload(payload: dict[str, Any]) -> dict[str, Any]:
    usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
    accounting = payload.get("accounting") if isinstance(payload.get("accounting"), dict) else {}
    profile = str(
        usage.get("accounting_profile")
        or accounting.get("profile")
        or accounting_profile_for(
            str(payload.get("provider_id") or ""),
            str(payload.get("model") or payload.get("model_id") or ""),
        )
    ).strip().lower()
    return canonicalize_usage(usage, profile)


def _usage_evidence_for_dedupe(payload: dict[str, Any]) -> dict[str, Any]:
    comparable = dict(payload)
    usage = dict(comparable.get("usage") or {}) if isinstance(comparable.get("usage"), dict) else {}
    for key in CANONICAL_USAGE_KEYS:
        usage.pop(key, None)
    comparable["usage"] = usage
    return comparable


def record_usage_event(
    ledger: Any,
    *,
    run_id: str,
    wave_id: str,
    delegation_id: str,
    usage_event: dict[str, Any],
) -> dict[str, Any]:
    usage_id = str(usage_event.get("usage_id") or "")[:256].strip()
    with ledger._lock:
        with ledger._connect() as connection:
            rows = connection.execute(
                "SELECT event_id,payload_json FROM events WHERE run_id=? AND event_type='usage_event' ORDER BY seq",
                (str(run_id)[:256],),
            ).fetchall()
        for row in rows:
            payload = json.loads(row["payload_json"] or "{}")
            if usage_id and str(payload.get("usage_id") or "") == usage_id:
                if _usage_evidence_for_dedupe(payload) != _usage_evidence_for_dedupe(usage_event):
                    raise ValueError("usage_id already exists with different evidence")
                return {"recorded": False, "event_id": row["event_id"], "usage_id": usage_id}
        event = ledger.append_event(
            run_id,
            wave_id=wave_id,
            delegation_id=delegation_id,
            event_type="usage_event",
            payload=usage_event,
        )
        return {"recorded": True, "event_id": event["event_id"], "usage_id": usage_id}


def _project_event(ledger: Any, row: Any) -> dict[str, Any]:
    item = ledger._event_row(row)
    return {
        **(item.get("payload") or {}),
        "seq": item["seq"],
        "event_time": item["event_time"],
    }


def list_usage_events(ledger: Any, run_id: str, *, limit: int | None = 100) -> list[dict[str, Any]]:
    with ledger._lock, ledger._connect() as connection:
        if limit is None:
            rows = connection.execute(
                "SELECT * FROM events WHERE run_id=? AND event_type='usage_event' ORDER BY seq",
                (str(run_id)[:256],),
            ).fetchall()
            return [_project_event(ledger, row) for row in rows]
        bounded_limit = max(1, min(int(limit), 500))
        rows = connection.execute(
            "SELECT * FROM events WHERE run_id=? AND event_type='usage_event' ORDER BY seq DESC LIMIT ?",
            (str(run_id)[:256], bounded_limit),
        ).fetchall()
    return [_project_event(ledger, row) for row in reversed(rows)]


def recent_usage_events(ledger: Any, *, limit: int = 8) -> list[dict[str, Any]]:
    bounded_limit = max(1, min(int(limit), 500))
    with ledger._lock, ledger._connect() as connection:
        rows = connection.execute(
            "SELECT * FROM events WHERE event_type='usage_event' ORDER BY seq DESC LIMIT ?",
            (bounded_limit,),
        ).fetchall()
    return [_project_event(ledger, row) for row in reversed(rows)]


def usage_analytics(ledger: Any, *, days: int = 7, now: str | None = None) -> dict[str, Any]:
    """Aggregate every durable UsageEvent in an exact UTC window without sampling."""
    if isinstance(days, bool) or not isinstance(days, int) or not 1 <= days <= 31:
        raise ValueError("days must be an integer between 1 and 31")

    def parse_time(value: str) -> datetime:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def iso(value: datetime, *, milliseconds: bool = True) -> str:
        timespec = "milliseconds" if milliseconds else "seconds"
        return value.isoformat(timespec=timespec).replace("+00:00", "Z")

    end = parse_time(now) if now else datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    rolling_start = end - timedelta(minutes=5)
    with ledger._lock, ledger._connect() as connection:
        rows = connection.execute(
            """SELECT * FROM events
               WHERE event_type='usage_event'
                 AND julianday(event_time) >= julianday(?)
                 AND julianday(event_time) <= julianday(?)
               ORDER BY event_time,seq""",
            (iso(start), iso(end)),
        ).fetchall()

    def empty_bucket() -> dict[str, Any]:
        return {
            "event_count": 0,
            "usage": {key: 0 for key in CANONICAL_USAGE_KEYS},
            "cost": {
                "measured_usd": 0.0,
                "derived_usd": 0.0,
                "measured_event_count": 0,
                "derived_event_count": 0,
                "unobserved_event_count": 0,
            },
            "usage_provenance": {},
            "cost_provenance": {},
        }

    def add(bucket: dict[str, Any], payload: dict[str, Any], canonical: dict[str, Any]) -> None:
        bucket["event_count"] += 1
        for key in CANONICAL_USAGE_KEYS:
            bucket["usage"][key] += max(0, int(canonical.get(key) or 0))
        measurement = payload.get("measurement") if isinstance(payload.get("measurement"), dict) else {}
        cost = payload.get("cost") if isinstance(payload.get("cost"), dict) else {}
        provenance = payload.get("provenance") if isinstance(payload.get("provenance"), dict) else {}
        measured = cost.get("provider_cost")
        derived = cost.get("derived_cost_usd")
        if (
            measurement.get("cost") == "measured"
            and isinstance(measured, (int, float))
            and not isinstance(measured, bool)
            and math.isfinite(float(measured))
            and measured >= 0
        ):
            bucket["cost"]["measured_usd"] += float(measured)
            bucket["cost"]["measured_event_count"] += 1
        elif (
            measurement.get("cost") == "derived"
            and isinstance(derived, (int, float))
            and not isinstance(derived, bool)
            and math.isfinite(float(derived))
            and derived >= 0
        ):
            bucket["cost"]["derived_usd"] += float(derived)
            bucket["cost"]["derived_event_count"] += 1
        else:
            bucket["cost"]["unobserved_event_count"] += 1
        for source_key, target_key in (("usage", "usage_provenance"), ("cost", "cost_provenance")):
            source = str(provenance.get(source_key) or "unobserved").strip() or "unobserved"
            bucket[target_key][source] = int(bucket[target_key].get(source) or 0) + 1

    def finish(bucket: dict[str, Any]) -> dict[str, Any]:
        return {
            "event_count": int(bucket["event_count"]),
            "usage": dict(bucket["usage"]),
            "cost": {
                **bucket["cost"],
                "measured_usd": round(float(bucket["cost"]["measured_usd"]), 12),
                "derived_usd": round(float(bucket["cost"]["derived_usd"]), 12),
            },
            "provenance": {
                "usage": dict(sorted(bucket["usage_provenance"].items())),
                "cost": dict(sorted(bucket["cost_provenance"].items())),
            },
        }

    overall = empty_bucket()
    rolling = empty_bucket()
    hours: dict[str, dict[str, Any]] = {}
    actors: dict[str, dict[str, Any]] = {}
    providers: dict[str, dict[str, Any]] = {}
    models: dict[tuple[str, str, str], dict[str, Any]] = {}
    invalid_event_count = 0
    for row in rows:
        item = ledger._event_row(row)
        payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
        try:
            canonical = canonical_usage_payload(payload)
            event_time = parse_time(str(item.get("event_time") or ""))
        except (TypeError, ValueError):
            invalid_event_count += 1
            continue
        actor = str(payload.get("actor") or "provider").strip().lower() or "provider"
        provider_id = str(payload.get("provider_id") or "unknown").strip() or "unknown"
        model = str(payload.get("model") or payload.get("model_id") or "unknown").strip() or "unknown"
        hour_key = iso(event_time.replace(minute=0, second=0, microsecond=0), milliseconds=False)
        add(overall, payload, canonical)
        add(hours.setdefault(hour_key, empty_bucket()), payload, canonical)
        add(actors.setdefault(actor, empty_bucket()), payload, canonical)
        add(providers.setdefault(provider_id, empty_bucket()), payload, canonical)
        add(models.setdefault((actor, provider_id, model), empty_bucket()), payload, canonical)
        if event_time >= rolling_start:
            add(rolling, payload, canonical)

    return {
        "schema_version": 1,
        "source": "durable_usage_events",
        "measurement": "canonical_non_overlapping",
        "missing_measurement_policy": "unknown_not_zero",
        "window": {
            "days": days,
            "start": iso(start),
            "end": iso(end),
            "source_event_count": len(rows),
            "aggregated_event_count": int(overall["event_count"]),
            "invalid_event_count": invalid_event_count,
        },
        "overall": finish(overall),
        "rolling_5m": {"start": iso(rolling_start), "end": iso(end), **finish(rolling)},
        "hourly": [{"hour": key, **finish(hours[key])} for key in sorted(hours)],
        "by_actor": [{"actor": key, **finish(actors[key])} for key in sorted(actors)],
        "by_provider": [{"provider_id": key, **finish(providers[key])} for key in sorted(providers)],
        "by_model": [
            {"actor": key[0], "provider_id": key[1], "model": key[2], **finish(models[key])}
            for key in sorted(models)
        ],
    }
