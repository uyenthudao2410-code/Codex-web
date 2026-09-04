from __future__ import annotations

import math
from typing import Any

from .context_observability import controller_knowledge_for_run


def _bounded_text(value: Any, limit: int) -> str:
    text = str(value or "")
    return text if len(text) <= limit else text[:limit] + "..."


class ObservationSpanLedgerMixin:
    """Own content-free observation-span recording and critical-path analysis."""

    def record_observation_span(self, *, run_id: str, span: dict[str, Any], wave_id: str = "") -> dict[str, Any]:
        run = self.get_run(run_id)
        if run is None:
            raise ValueError("observation span run was not found")
        if wave_id and not any(str(item.get("wave_id") or "") == wave_id for item in self.list_waves(run_id)):
            raise ValueError("observation span wave does not belong to the run")

        span_id = _bounded_text(span.get("span_id") or "", 128).strip()
        stage = _bounded_text(span.get("stage") or "", 100).strip().lower()
        source = _bounded_text(span.get("source") or "", 128).strip()
        measurement = _bounded_text(span.get("measurement") or "", 100).strip().lower()
        clock_domain = _bounded_text(span.get("clock_domain") or "", 160).strip()
        if not span_id or not stage or not source or not measurement or not clock_domain:
            raise ValueError("span_id, stage, source, measurement and clock_domain are required")

        def finite_number(name: str) -> float:
            value = span.get(name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or float(value) < 0:
                raise ValueError(f"{name} must be a finite non-negative number")
            return float(value)

        start_ms = finite_number("start_ms")
        end_ms = finite_number("end_ms")
        if end_ms < start_ms:
            raise ValueError("end_ms must be greater than or equal to start_ms")

        parent_span_id = _bounded_text(span.get("parent_span_id") or "", 128).strip()
        raw_dependencies = span.get("depends_on") if isinstance(span.get("depends_on"), list) else []
        depends_on = list(dict.fromkeys(
            _bounded_text(item, 128).strip() for item in raw_dependencies[:32] if _bounded_text(item, 128).strip()
        ))
        payload: dict[str, Any] = {
            "span_id": span_id,
            "stage": stage,
            "source": source,
            "measurement": measurement,
            "clock_domain": clock_domain,
            "start_ms": round(start_ms, 6),
            "end_ms": round(end_ms, 6),
            "duration_ms": round(end_ms - start_ms, 6),
            "depends_on": depends_on,
        }
        if parent_span_id:
            payload["parent_span_id"] = parent_span_id
        for key, limit in (("trace_id", 128), ("turn_id", 128), ("observer_plane", 100)):
            value = _bounded_text(span.get(key) or "", limit).strip()
            if value:
                payload[key] = value

        existing = next((item for item in self.list_observation_spans(run_id) if item.get("span_id") == span_id), None)
        if existing is not None:
            comparable = {
                key: value
                for key, value in existing.items()
                if key not in {"seq", "event_time", "controller_knowledge_at_observation"}
            }
            if comparable != payload:
                raise ValueError("observation span_id already exists with different evidence")
            return {**existing, "recorded": False}

        if (
            payload.get("source") == "electron_chatgpt_dom"
            and payload.get("observer_plane") == "electron_chatgpt_dom"
            and payload.get("trace_id")
            and payload.get("turn_id")
        ):
            payload["controller_knowledge_at_observation"] = controller_knowledge_for_run(
                self,
                run_id,
                run=run,
            )

        event = self.append_event(run_id, wave_id=wave_id or None, event_type="observation_span_recorded", payload=payload)
        return {**payload, "recorded": True, "seq": event["seq"], "event_time": event["event_time"]}

    def list_observation_spans(self, run_id: str, *, limit: int = 500) -> list[dict[str, Any]]:
        bounded_limit = max(1, min(int(limit), 1000))
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM events WHERE run_id=? AND event_type='observation_span_recorded' ORDER BY seq LIMIT ?",
                (_bounded_text(run_id, 256), bounded_limit),
            ).fetchall()
        events = [self._event_row(row) for row in rows]
        return [
            {**(item.get("payload") or {}), "seq": item["seq"], "event_time": item["event_time"]}
            for item in events
        ]

    def critical_path_analysis(self, run_id: str) -> dict[str, Any]:
        spans = self.list_observation_spans(run_id, limit=1000)
        if not spans:
            return {
                "schema_version": 1,
                "status": "incomplete",
                "complete": False,
                "reasons": ["no_observation_spans"],
                "critical_path_ms": None,
                "path_span_ids": [],
                "span_count": 0,
                "cross_clock_edges": 0,
                "timestamp_policy": "durations_within_declared_clock_domain_only",
            }

        nodes = {str(item.get("span_id") or ""): item for item in spans if str(item.get("span_id") or "")}
        dependencies: dict[str, list[str]] = {}
        missing_dependencies: set[str] = set()
        children: dict[str, list[str]] = {span_id: [] for span_id in nodes}
        indegree: dict[str, int] = {span_id: 0 for span_id in nodes}
        cross_clock_edges = 0
        for span_id, item in nodes.items():
            refs = []
            parent = str(item.get("parent_span_id") or "").strip()
            if parent:
                refs.append(parent)
            refs.extend(str(value or "").strip() for value in (item.get("depends_on") or []) if str(value or "").strip())
            refs = list(dict.fromkeys(refs))
            dependencies[span_id] = refs
            for dependency in refs:
                if dependency not in nodes:
                    missing_dependencies.add(dependency)
                    continue
                indegree[span_id] += 1
                children.setdefault(dependency, []).append(span_id)
                if str(nodes[dependency].get("clock_domain") or "") != str(item.get("clock_domain") or ""):
                    cross_clock_edges += 1

        queue = sorted(span_id for span_id, degree in indegree.items() if degree == 0)
        longest: dict[str, float] = {}
        predecessor: dict[str, str | None] = {}
        processed: list[str] = []
        while queue:
            span_id = queue.pop(0)
            processed.append(span_id)
            duration = float(nodes[span_id].get("duration_ms") or 0.0)
            available_dependencies = [item for item in dependencies.get(span_id, []) if item in longest]
            if available_dependencies:
                best = max(available_dependencies, key=lambda item: longest[item])
                longest[span_id] = longest[best] + duration
                predecessor[span_id] = best
            else:
                longest[span_id] = duration
                predecessor[span_id] = None
            for child in sorted(children.get(span_id, [])):
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)
                    queue.sort()

        reasons: list[str] = []
        if missing_dependencies:
            reasons.append("missing_dependency_spans")
        if len(processed) != len(nodes):
            reasons.append("dependency_cycle")
        if not longest or "dependency_cycle" in reasons:
            path_ids: list[str] = []
            critical_path_ms: float | None = None
        else:
            end_span = max(longest, key=lambda item: longest[item])
            critical_path_ms = round(longest[end_span], 6)
            path_ids = []
            cursor: str | None = end_span
            while cursor:
                path_ids.append(cursor)
                cursor = predecessor.get(cursor)
            path_ids.reverse()

        by_stage_ms: dict[str, float] = {}
        for span_id in path_ids:
            stage = str(nodes[span_id].get("stage") or "unknown")
            by_stage_ms[stage] = round(by_stage_ms.get(stage, 0.0) + float(nodes[span_id].get("duration_ms") or 0.0), 6)
        return {
            "schema_version": 1,
            "status": "complete" if not reasons else "incomplete",
            "complete": not reasons,
            "reasons": reasons,
            "critical_path_ms": critical_path_ms,
            "path_span_ids": path_ids,
            "by_stage_ms": by_stage_ms,
            "span_count": len(nodes),
            "clock_domains": sorted({str(item.get("clock_domain") or "") for item in nodes.values() if str(item.get("clock_domain") or "")}),
            "cross_clock_edges": cross_clock_edges,
            "missing_dependency_span_ids": sorted(missing_dependencies),
            "timestamp_policy": "durations_within_declared_clock_domain_only; cross_clock_order_requires_explicit_dependency_identity",
        }
