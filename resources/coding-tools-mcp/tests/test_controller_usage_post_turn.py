from __future__ import annotations

import time
from types import SimpleNamespace

import pytest

from coding_tools_mcp.controller_usage_ingress import (
    CONTROLLER_USAGE_META_KEY,
    active_controller_usage_context,
    controller_usage_request,
    record_controller_usage,
)
from coding_tools_mcp.evaluation_report import (
    CURRENT_HOST_OBSERVATION_SCHEMA_VERSION,
    LEGACY_HOST_OBSERVATION_SCHEMA_VERSIONS,
)


class _TaskState:
    @staticmethod
    def get() -> dict[str, object]:
        return {"orchestration": {"run_id": "run-1", "wave_id": "wave-1"}}


class _Ledger:
    def __init__(
        self,
        status: str,
        *,
        lease: dict[str, object] | None = None,
        created_at: object | None = None,
    ) -> None:
        self.status = status
        self.lease = lease
        self.created_at = time.time() if created_at is None else created_at
        self.recorded: list[dict[str, object]] = []

    def get_run(self, _run_id: str) -> dict[str, object]:
        return {
            "status": self.status,
            "created_at": self.created_at,
            "metadata": {
                "host_correlation": {"eligible": True, "source": "electron_pending_host_turn"},
                "evaluation": {"turn_id": "turn-1", "trace_id": "trace-1"},
            },
        }

    def peek_controller_lease(self, _run_id: str) -> dict[str, object] | None:
        return self.lease

    def record_usage_event(self, **kwargs: object) -> dict[str, object]:
        event = dict(kwargs["usage_event"])
        self.recorded.append(event)
        return {"recorded": True, "usage_id": event["usage_id"]}


class _Control:
    def __init__(self, state: str, wave_id: str = "wave-1") -> None:
        self.state = state
        self.wave_id = wave_id

    def snapshot(self, _run_id: str) -> SimpleNamespace:
        return SimpleNamespace(state=self.state, wave_id=self.wave_id)


class _Runtime:
    def __init__(
        self,
        run_status: str,
        orchestration_state: str,
        wave_id: str = "wave-1",
        *,
        lease: dict[str, object] | None = None,
        created_at: object | None = None,
    ) -> None:
        self.task_state = _TaskState()
        self.orchestration_ledger = _Ledger(run_status, lease=lease, created_at=created_at)
        self.orchestration_control = _Control(orchestration_state, wave_id)
        self.require_calls = 0

    @staticmethod
    def _current_hub_client() -> dict[str, str]:
        return {"client_id": "chatweb", "client_type": "chatweb", "role": "controller"}

    @staticmethod
    def _hub_client_record_id(identity: dict[str, str]) -> str:
        return identity["client_id"]

    def _require_hub_controller(self, _run_id: str) -> dict[str, object]:
        self.require_calls += 1
        return self.orchestration_ledger.lease or {"status": "active", "owner_client_id": "chatweb"}


def _runtime(
    run_status: str,
    orchestration_state: str,
    wave_id: str = "wave-1",
    *,
    lease: dict[str, object] | None = None,
    created_at: object | None = None,
) -> _Runtime:
    return _Runtime(run_status, orchestration_state, wave_id, lease=lease, created_at=created_at)


def _report(**overrides: object) -> dict[str, object]:
    report: dict[str, object] = {
        "schema_version": 1,
        "run_id": "run-1",
        "wave_id": "wave-1",
        "turn_id": "turn-1",
        "trace_id": "trace-1",
        "provider_id": "openai",
        "model_id": "gpt-test",
        "source": "client_reported",
        "accounting_profile": "openai_compatible",
        "input_tokens": 100,
        "cached_input_tokens": 40,
        "output_tokens": 20,
        "reasoning_output_tokens": 5,
    }
    report.update(overrides)
    return report


def test_controller_usage_context_accepts_immediate_checkpointed_post_turn_receipt() -> None:
    assert active_controller_usage_context(_runtime("active", "EXECUTING")) == ("run-1", "wave-1")
    assert active_controller_usage_context(_runtime("accepted", "CHECKPOINTED")) == ("run-1", "wave-1")
    assert active_controller_usage_context(_runtime("accepted", "ABORTED")) is None
    assert active_controller_usage_context(_runtime("accepted", "CHECKPOINTED", "wave-2")) is None


def test_evaluation_report_consumes_current_host_schema_and_keeps_v5_as_legacy() -> None:
    assert CURRENT_HOST_OBSERVATION_SCHEMA_VERSION == 6
    assert 5 in LEGACY_HOST_OBSERVATION_SCHEMA_VERSIONS


def test_controller_usage_request_rejects_weak_transport_provenance_before_dispatch() -> None:
    request = {
        "method": "tools/call",
        "params": {
            "name": "task_control",
            "arguments": {"action": "audit", "run_id": "run-1", "wave_id": "wave-1"},
            "_meta": {CONTROLLER_USAGE_META_KEY: _report()},
        },
    }
    for source in ("implicit_default", "partial_headers", ""):
        with pytest.raises(ValueError, match="transport provenance"):
            controller_usage_request(request, {"client_type": "chatweb", "role": "controller", "identity_source": source})
    _, accepted = controller_usage_request(
        request,
        {"client_type": "chatweb", "role": "controller", "identity_source": "attested_transport"},
    )
    assert accepted is not None
    assert accepted["run_id"] == "run-1"


def test_deferred_agent_usage_does_not_infer_authority_from_run_timestamps() -> None:
    request = {
        "method": "tools/call",
        "params": {
            "name": "agent_workflow",
            "arguments": {"workflow": "diagnose", "phase": "prepare", "path": "."},
            "_meta": {CONTROLLER_USAGE_META_KEY: _report(run_id="", wave_id="")},
        },
    }
    _, deferred = controller_usage_request(
        request,
        {"client_type": "chatweb", "role": "controller", "identity_source": "attested_transport"},
    )
    assert deferred is not None

    # The HTTP handler owns the causal pre-dispatch authority boundary. Once a
    # report is marked deferred there, run timestamps must not be used as a
    # second, proximity-based authority signal: serialized clock precision can
    # make a run created by the same request appear older than prevalidation.
    created_by_same_request = _runtime("active", "EXECUTING", created_at=time.time() - 60)
    receipt = record_controller_usage(created_by_same_request, deferred, ("run-1", "wave-1"))
    assert receipt["recorded"] is True
    assert created_by_same_request.require_calls == 1


def test_controller_usage_report_binding_and_safe_integer_gates_fail_closed() -> None:
    from coding_tools_mcp.usage_events import JAVASCRIPT_MAX_SAFE_INTEGER, validate_controller_usage_report

    with pytest.raises(ValueError, match="supplied together"):
        validate_controller_usage_report({**_report(), "wave_id": ""})
    with pytest.raises(ValueError, match="JavaScript-safe"):
        validate_controller_usage_report({**_report(), "input_tokens": JAVASCRIPT_MAX_SAFE_INTEGER + 1})
    with pytest.raises(ValueError, match="cached_input_tokens"):
        validate_controller_usage_report({**_report(), "cached_input_tokens": 101})
    with pytest.raises(ValueError, match="reasoning_output_tokens"):
        validate_controller_usage_report({**_report(), "reasoning_output_tokens": 21})


def test_active_controller_usage_validates_exact_identity_before_lease_authorization() -> None:
    runtime = _runtime("active", "EXECUTING")
    receipt = record_controller_usage(runtime, _report(), ("run-1", "wave-1"))
    assert receipt["recorded"] is True
    assert runtime.require_calls == 1

    runtime = _runtime("active", "EXECUTING")
    with pytest.raises(ValueError, match="run_id/wave_id"):
        record_controller_usage(runtime, _report(wave_id="wave-other"), ("run-1", "wave-1"))
    assert runtime.require_calls == 0
    with pytest.raises(ValueError, match="turn_id/trace_id"):
        record_controller_usage(runtime, _report(trace_id="trace-other"), ("run-1", "wave-1"))
    assert runtime.require_calls == 0


def test_checkpointed_controller_usage_uses_existing_unexpired_lease_without_renewal() -> None:
    active_lease = {"status": "active", "owner_client_id": "chatweb", "expires_at": time.time() + 30}
    runtime = _runtime("accepted", "CHECKPOINTED", lease=active_lease)
    receipt = record_controller_usage(runtime, _report(), ("run-1", "wave-1"))
    assert receipt["recorded"] is True
    assert runtime.require_calls == 0

    expired = _runtime("accepted", "CHECKPOINTED", lease={**active_lease, "expires_at": time.time() - 1})
    with pytest.raises(ValueError, match="unexpired"):
        record_controller_usage(expired, _report(), ("run-1", "wave-1"))
    assert expired.require_calls == 0

    foreign = _runtime("accepted", "CHECKPOINTED", lease={**active_lease, "owner_client_id": "codex-desktop"})
    with pytest.raises(ValueError, match="unexpired"):
        record_controller_usage(foreign, _report(), ("run-1", "wave-1"))
    assert foreign.require_calls == 0
