from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from coding_tools_mcp.orchestration_ledger import OrchestrationLedger


def _run(ledger: OrchestrationLedger) -> tuple[str, str]:
    run_id = ledger.create_run(objective="typed continuity telemetry test")
    wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
    return run_id, wave_id


def _record(ledger: OrchestrationLedger, run_id: str, wave_id: str, logical_id: str, event_type: str, **extra):
    return ledger.record_continuity_telemetry(
        logical_id=logical_id,
        run_id=run_id,
        wave_id=wave_id,
        event_type=event_type,
        problem_id="prl-telemetry-test",
        problem_revision=1,
        task_context_id="ctx_telemetry_test",
        activation_epoch_id="activation-test-1",
        process_instance_id="process-test-1",
        server_instance_id="server-test-1",
        **extra,
    )


def test_continuity_telemetry_persists_across_ledger_reopen(tmp_path: Path) -> None:
    first = OrchestrationLedger(tmp_path)
    run_id, wave_id = _run(first)
    created = _record(first, run_id, wave_id, "resume:1", "resume", outcome="succeeded", duration_ms=1250)
    assert created["created"] is True

    reopened = OrchestrationLedger(tmp_path)
    listed = reopened.list_continuity_telemetry(run_id=run_id)
    assert listed["complete"] is True
    assert len(listed["events"]) == 1
    event = listed["events"][0]
    assert event["logical_id"] == "resume:1"
    assert event["problem_id"] == "prl-telemetry-test"
    assert event["task_context_id"] == "ctx_telemetry_test"
    assert event["duration_ms"] == 1250


def test_continuity_telemetry_replay_is_idempotent_and_conflicts_fail_closed(tmp_path: Path) -> None:
    ledger = OrchestrationLedger(tmp_path)
    run_id, wave_id = _run(ledger)
    first = _record(ledger, run_id, wave_id, "continuation:1", "continuation_attempt", outcome="attempted")
    replay = _record(ledger, run_id, wave_id, "continuation:1", "continuation_attempt", outcome="attempted")
    assert first["created"] is True
    assert replay["created"] is False
    assert replay["idempotent"] is True
    with pytest.raises(ValueError, match="CONTINUITY_TELEMETRY_LOGICAL_ID_CONFLICT"):
        _record(ledger, run_id, wave_id, "continuation:1", "continuation_failure", outcome="failed")
    assert len(ledger.list_continuity_telemetry(run_id=run_id)["events"]) == 1


def test_continuity_telemetry_summary_is_correlated_and_aggregatable(tmp_path: Path) -> None:
    ledger = OrchestrationLedger(tmp_path)
    run_id, wave_id = _run(ledger)
    _record(ledger, run_id, wave_id, "nudge:1", "manual_nudge", outcome="observed")
    _record(ledger, run_id, wave_id, "interrupt:1", "interruption", outcome="observed", code="REPORT_GATE")
    _record(ledger, run_id, wave_id, "replan:1", "replan", outcome="succeeded", duration_ms=400)
    _record(ledger, run_id, wave_id, "gate:1", "report_gate", outcome="succeeded", duration_ms=600)
    _record(ledger, run_id, wave_id, "attempt:1", "continuation_attempt", outcome="attempted")
    _record(ledger, run_id, wave_id, "success:1", "continuation_success", outcome="succeeded")
    _record(ledger, run_id, wave_id, "resume:1", "resume", outcome="succeeded", duration_ms=900)
    _record(ledger, run_id, wave_id, "dedupe:1", "duplicate_effect_prevented", outcome="prevented")
    _record(ledger, run_id, wave_id, "accept:1", "accepted_checkpoint", outcome="succeeded")

    summary = ledger.continuity_telemetry_summary(problem_id="prl-telemetry-test", problem_revision=1)
    assert summary["complete"] is True
    assert summary["manual_nudge_count"] == 1
    assert summary["interruption_count"] == 1
    assert summary["replan_count"] == 1
    assert summary["report_gate_count"] == 1
    assert summary["continuation_attempt_count"] == 1
    assert summary["continuation_success_count"] == 1
    assert summary["duplicate_effect_prevented_count"] == 1
    assert summary["accepted_checkpoint_count"] == 1
    assert summary["counts_by_code"] == {"REPORT_GATE": 1}
    assert summary["time_to_resume_ms"] == {"count": 1, "total_ms": 900, "max_ms": 900, "avg_ms": 900.0}
    assert summary["replan_duration_ms"]["total_ms"] == 400
    assert summary["report_gate_wait_ms"]["total_ms"] == 600


def test_continuity_telemetry_is_content_free_and_rejects_free_form_values(tmp_path: Path) -> None:
    ledger = OrchestrationLedger(tmp_path)
    run_id, wave_id = _run(ledger)
    with pytest.raises(ValueError, match="CONTINUITY_TELEMETRY_CODE_INVALID"):
        _record(ledger, run_id, wave_id, "bad:1", "blocker", outcome="blocked", code="contains raw user prose")
    with pytest.raises(ValueError, match="CONTINUITY_TELEMETRY_EVENT_TYPE_INVALID"):
        _record(ledger, run_id, wave_id, "bad:2", "raw_prompt", outcome="observed")
    with pytest.raises(TypeError):
        ledger.record_continuity_telemetry(
            logical_id="bad:3",
            run_id=run_id,
            wave_id=wave_id,
            event_type="interruption",
            prompt="secret prompt",
        )

    _record(ledger, run_id, wave_id, "safe:1", "restart", outcome="observed", restart_ticket_id="restart-test-1")
    with sqlite3.connect(ledger.path) as connection:
        payloads = [row[0] for row in connection.execute(
            "SELECT payload_json FROM events WHERE run_id=? AND event_type='continuity_telemetry_recorded'",
            (run_id,),
        ).fetchall()]
    assert len(payloads) == 1
    payload = json.loads(payloads[0])
    assert payload["restart_ticket_id"] == "restart-test-1"
    forbidden = {"prompt", "raw_prompt", "transcript", "source", "stdout", "stderr", "reasoning", "private_reasoning"}
    assert forbidden.isdisjoint(payload)
