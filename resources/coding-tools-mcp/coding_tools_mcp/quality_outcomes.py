from __future__ import annotations

"""Generic quality-outcome mixin for the canonical orchestration ledger."""

from typing import Any


def _bounded_text(value: Any, limit: int) -> str:
    text = str(value or "")
    return text if len(text) <= limit else text[:limit] + "..."


class QualityOutcomeLedgerMixin:
    """The parent owns run lookup, waves, event append, and event replay."""

    def record_quality_outcome(self, *, run_id: str, outcome: dict[str, Any], wave_id: str = "") -> dict[str, Any]:
        """Append one bounded immediate/delayed quality observation."""
        if self.get_run(run_id) is None:
            raise ValueError("quality outcome run was not found")
        if wave_id and not any(str(item.get("wave_id") or "") == wave_id for item in self.list_waves(run_id)):
            raise ValueError("quality outcome wave does not belong to the run")
        source = _bounded_text(outcome.get("source") or "", 128).strip()
        if not source:
            raise ValueError("quality outcome source is required")
        payload: dict[str, Any] = {"source": source}
        for key in ("oracle_pass", "regression_escape", "rollback_required", "manual_fix_required", "reviewer_blinded"):
            value = outcome.get(key)
            if isinstance(value, bool):
                payload[key] = value
        for key in ("critical_defect_count", "noncritical_defect_count"):
            value = outcome.get(key)
            if value is None:
                continue
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{key} must be a non-negative integer")
            payload[key] = value
        maintainability = _bounded_text(outcome.get("maintainability_gate") or "", 32).strip().lower()
        if maintainability:
            if maintainability not in {"pass", "fail", "not_applicable", "unknown"}:
                raise ValueError("maintainability_gate is invalid")
            payload["maintainability_gate"] = maintainability
        observation_window_end = _bounded_text(outcome.get("observation_window_end") or "", 128).strip()
        if observation_window_end:
            payload["observation_window_end"] = observation_window_end
        event = self.append_event(run_id, wave_id=wave_id or None, event_type="quality_outcome_recorded", payload=payload)
        return {**payload, "seq": event["seq"], "event_time": event["event_time"]}

    def latest_quality_outcome(self, run_id: str) -> dict[str, Any] | None:
        for event in reversed(self.list_events(run_id)):
            if str(event.get("event_type") or "") == "quality_outcome_recorded":
                payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
                return {**payload, "seq": event["seq"], "event_time": event["event_time"]}
        return None
