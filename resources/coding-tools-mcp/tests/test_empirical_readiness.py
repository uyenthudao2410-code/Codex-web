from __future__ import annotations

import importlib.util
from contextlib import AbstractContextManager
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "report_empirical_readiness.py"
SPEC = importlib.util.spec_from_file_location("report_empirical_readiness_under_test", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
reporter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reporter)


class FakeLedger:
    def __init__(self) -> None:
        self.runs = {
            "run-natural-2": {
                "run_id": "run-natural-2",
                "status": "accepted",
                "metadata": {"problem_resolution": {"policy_eligible": False}},
            },
            "run-natural-3": {
                "run_id": "run-natural-3",
                "status": "active",
                "metadata": {"problem_resolution": {"policy_eligible": None}},
            },
            **{
                f"stale-{index}": {"run_id": f"stale-{index}", "status": "active"}
                for index in range(12)
            },
        }

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        return self.runs.get(run_id)

    def list_checkpoints(self, run_id: str) -> list[dict[str, Any]]:
        return []

    def list_waves(self, run_id: str) -> list[dict[str, Any]]:
        return []

    def list_proofs(self, run_id: str) -> list[dict[str, Any]]:
        return [{"status": "passed"}] if run_id == "stale-0" else []


class FakeProblems:
    fact_load_statements = 9

    def __init__(self) -> None:
        self.revisions = [
            {"problem_id": "old", "revision": 1, "created_event_seq": 1},
            {"problem_id": "natural-2", "revision": 1, "created_event_seq": 2},
            {"problem_id": "natural-3", "revision": 1, "created_event_seq": 3},
        ]

    def events_for_revision(self, problem_id: str, revision: int) -> list[dict[str, Any]]:
        return [{"problem_id": problem_id, "revision": revision}]

    def verify_chain(self, problem_id: str) -> dict[str, Any]:
        return {"ok": True}


class FakeContinuity:
    fact_load_statements = 15


class FakeSnapshot(AbstractContextManager["FakeSnapshot"]):
    def __init__(self, ledger: FakeLedger) -> None:
        self.ledger = ledger
        self.reader = object()
        self.statement_count = 32
        self.live_backup_connections = 1

    def __enter__(self) -> "FakeSnapshot":
        return self

    def __exit__(self, *args: object) -> None:
        return None


def _unavailable(reason: str, *, unit: str = "token") -> dict[str, Any]:
    return {
        "status": "UNAVAILABLE",
        "value": None,
        "unit": unit,
        "missing_reason": reason,
        "unknown_is_not_zero": True,
    }


def _cohort() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "COLLECTING",
        "cohort": {"selected_rows": 1, "typed_natural_rows": 1},
        "raw_rows": [
            {
                "problem_id": "natural-2",
                "problem_revision": 1,
                "natural_problem_eligibility": {
                    "eligible": True,
                    "exact_primary_run_ids": ["run-natural-2"],
                },
                "metrics": {
                    "trusted_resolution": {
                        "receipt_bound_confirmation": False,
                        "resolved_confirmed": False,
                        "false_closure_count": 0,
                        "reopen_count": 0,
                    },
                    "ttpr": {
                        "execution_ms": {"status": "OBSERVED", "value_ms": 1803.0},
                        "proof_ms": {"status": "OBSERVED", "value_ms": 5250.0},
                        "acceptance_ms": {"status": "OBSERVED", "value_ms": 1165630.0},
                        "replan_ms": _unavailable(
                            "run_phase_timing_incomplete", unit="millisecond"
                        ),
                        "restricted_ttpr_active_ms": {
                            "status": "OBSERVED",
                            "value_ms": 1179585.8248,
                        },
                    },
                    "resource_economics": {
                        "controller_tokens_exact_when_available": _unavailable(
                            "controller_usage_not_observed_for_every_exact_run"
                        ),
                        "provider_tokens": {
                            "status": "OBSERVED",
                            "usage": {"total_tokens": 0},
                            "missing_reason": None,
                            "unknown_is_not_zero": True,
                        },
                        "monetary_cost_complete_when_available": _unavailable(
                            "controller_or_provider_cost_plane_incomplete",
                            unit="currency_as_reported",
                        ),
                        "rework": _unavailable("rework_usage_missing"),
                        "tool_invocation_count": _unavailable(
                            "problem_attributed_tool_invocation_receipts_not_recorded",
                            unit="tool_invocation",
                        ),
                    },
                    "governance_friction": {
                        "run_count": 1,
                        "wave_count": 1,
                        "replan_event_count": 0,
                    },
                    "usage_coverage": {
                        "controller": {"status": "OBSERVED", "rate": 0.0},
                        "provider": {"status": "OBSERVED", "rate": 1.0},
                    },
                },
            }
        ],
        "decision_checkpoints": {
            "n5": {
                "decision": "COLLECTING",
                "real_cross_session_pass_rows": 0,
                "observed_rows": 1,
            }
        },
        "missingness": {
            "missing_is_unknown_not_zero": True,
            "reason_counts": {"controller_usage_not_observed_for_every_exact_run": 1},
        },
    }


def _lifecycle() -> dict[str, Any]:
    return {
        "runs": [
            {
                "run_id": f"stale-{index}",
                "run_status": "active",
                "classification": "THRESHOLD_SENSITIVE_STALE_CANDIDATE",
                "reasons": [
                    "inactive_without_live_ownership",
                    "meets_current_stale_threshold",
                ],
                "activity_age_seconds": 100000 + index,
                "latest_state_after": "RUNNING",
                "last_event": {"seq": index, "hash": f"hash-{index}"},
                "ownership": {},
            }
            for index in range(12)
        ],
        "summary": {
            "ordinary_active_runs": 12,
            "run_classification_counts": {
                "THRESHOLD_SENSITIVE_STALE_CANDIDATE": 12
            },
        },
        "snapshot": {"immutable": True, "backup_api_copy": True},
        "mutated_canonical_ledger": False,
    }


def _p4() -> dict[str, Any]:
    return {
        "state": "COLLECTING",
        "p4_empirically_complete": False,
        "p4_gate": {"can_answer_which_signals_predict_repair": False},
        "predictive_validation": {
            "status": "representative_descriptive_comparison_available_but_unvalidated",
            "validation_blockers": ["pooled_leave_one_out_brier_gain_not_positive"],
        },
        "git_baseline": {
            "source_worktree_clean": False,
            "upstream_configured": True,
            "head_matches_upstream": False,
            "p5_baseline_ready": False,
        },
        "p5_baseline_ready": False,
        "p5_experiment_engineering_ready": False,
        "p5_experiment_start_ready": False,
        "p5_experiment_epoch_lifecycle": "EPOCH_HARD_STOPPED",
        "p5_latest_epoch": {"lifecycle": "EPOCH_HARD_STOPPED"},
        "p5_controlled_treatment_may_be_opened": False,
        "automatic_policy_activation": False,
        "p5_automatic_start": False,
    }


def _install_fakes(monkeypatch: Any, ledger: FakeLedger) -> None:
    problems = FakeProblems()
    monkeypatch.setattr(
        reporter, "open_existing_ledger_analysis", lambda root: FakeSnapshot(ledger)
    )
    monkeypatch.setattr(
        reporter, "ProblemLineageFacts", SimpleNamespace(load=lambda reader: problems)
    )
    monkeypatch.setattr(
        reporter,
        "CrossSessionContinuityFacts",
        SimpleNamespace(load=lambda reader: FakeContinuity()),
    )
    monkeypatch.setattr(
        reporter, "lifecycle_census_report", lambda *args, **kwargs: _lifecycle()
    )
    monkeypatch.setattr(
        reporter, "p4_readiness_report", lambda *args, **kwargs: _p4()
    )
    monkeypatch.setattr(
        reporter, "natural_problem_cohort_report", lambda *args, **kwargs: _cohort()
    )
    monkeypatch.setattr(
        reporter,
        "problem_resolution_economics_report",
        lambda *args, **kwargs: {
            "revision_4_metrics": {
                "independent_outcome_evidence_coverage": {
                    "status": "AVAILABLE",
                    "numerator": 0,
                    "denominator": 1,
                    "coverage": 0.0,
                    "missing_reason": None,
                    "unknown_is_not_zero": True,
                }
            }
        },
    )
    monkeypatch.setattr(
        reporter,
        "_exact_primary_run_ids",
        lambda events: {
            "natural-2": ["run-natural-2"],
            "natural-3": ["run-natural-3"],
        }.get(events[0]["problem_id"], []),
    )
    monkeypatch.setattr(
        reporter,
        "_run_natural_provenance",
        lambda run: {
            "status": "PASS"
            if str(run.get("run_id") or "").startswith("run-natural")
            else "UNAVAILABLE"
        },
    )


def test_report_is_read_only_compact_and_preserves_unknown_null(
    tmp_path: Path, monkeypatch: Any
) -> None:
    ledger_path = tmp_path / ".coding-tools" / "orchestration" / "ledger.sqlite3"
    ledger_path.parent.mkdir(parents=True)
    ledger_path.write_bytes(b"canonical-sentinel")
    before = ledger_path.read_bytes()
    ledger = FakeLedger()
    _install_fakes(monkeypatch, ledger)

    result = reporter.empirical_readiness_report(tmp_path, observed_at=123.0)

    assert ledger_path.read_bytes() == before
    assert result["read_contract"] == {
        "canonical_writer_instantiated": False,
        "runtime_instantiated_by_reporter": False,
        "stale_reconciliation_called": False,
        "p5_mutation_called": False,
        "objective_text_inference_used": False,
    }
    assert result["mutated_canonical_ledger"] is False
    row = result["natural_cohort"]["rows"][0]
    assert row["timing"]["acceptance_ms"]["value_ms"] == 1165630.0
    assert row["economics"]["controller_tokens"]["status"] == "UNAVAILABLE"
    assert row["economics"]["controller_tokens"]["value"] is None
    assert row["economics"]["provider_tokens"]["usage"]["total_tokens"] == 0
    assert row["economics"]["monetary_cost"]["value"] is None
    assert result["natural_cohort"]["independent_user_outcome_coverage"]["coverage"] == 0.0
    assert "details" not in result["stale_run_audit"]


def test_auto_start_uses_contiguous_typed_natural_suffix_without_objective_inference(
    monkeypatch: Any,
) -> None:
    ledger = FakeLedger()
    problems = FakeProblems()
    _install_fakes(monkeypatch, ledger)
    assert reporter._current_natural_suffix_start(ledger, problems) == {
        "problem_id": "natural-2",
        "problem_revision": 1,
    }


def test_auto_start_uses_latest_typed_segment_when_trailing_revisions_are_untyped(
    monkeypatch: Any,
) -> None:
    ledger = FakeLedger()
    problems = FakeProblems()
    problems.revisions.extend(
        [
            {"problem_id": "contract-only", "revision": 1, "created_event_seq": 4},
            {"problem_id": "unbound-latest", "revision": 1, "created_event_seq": 5},
        ]
    )
    _install_fakes(monkeypatch, ledger)

    assert reporter._current_natural_suffix_start(ledger, problems) == {
        "problem_id": "natural-2",
        "problem_revision": 1,
    }


def test_technical_acceptance_uses_canonical_provisional_resolution_not_all_attempt_statuses() -> None:
    problem_id = "natural-retried"
    accepted_run = "run-final-accepted"
    accepted_wave = "wave-final-accepted"

    class RetriedLedger(FakeLedger):
        def __init__(self) -> None:
            super().__init__()
            self.runs.update(
                {
                    "run-old-aborted-1": {"run_id": "run-old-aborted-1", "status": "aborted"},
                    "run-old-aborted-2": {"run_id": "run-old-aborted-2", "status": "aborted"},
                    accepted_run: {
                        "run_id": accepted_run,
                        "status": "accepted",
                        "metadata": {
                            "problem_resolution": {
                                "work_origin": "problem",
                                "resolution_claim": "full_problem",
                                "problem_id": problem_id,
                                "problem_revision": 1,
                            }
                        },
                    },
                }
            )

        def list_waves(self, run_id: str) -> list[dict[str, Any]]:
            if run_id != accepted_run:
                return []
            return [
                {
                    "wave_id": accepted_wave,
                    "status": "accepted",
                    "metadata": {
                        "problem_resolution": {
                            "work_origin": "problem",
                            "resolution_claim": "full_problem",
                            "problem_id": problem_id,
                            "problem_revision": 1,
                        }
                    },
                }
            ]

        def list_checkpoints(self, run_id: str) -> list[dict[str, Any]]:
            return (
                [{"checkpoint_id": "checkpoint-final", "status": "accepted", "wave_id": accepted_wave}]
                if run_id == accepted_run
                else []
            )

    class RetriedProblems:
        def verify_chain(self, current_problem_id: str) -> dict[str, Any]:
            return {"ok": current_problem_id == problem_id}

        def events_for_revision(
            self, current_problem_id: str, revision: int
        ) -> list[dict[str, Any]]:
            if current_problem_id != problem_id or revision != 1:
                return []
            return [
                {
                    "eligible_for_policy": True,
                    "relation_type": "PROVISIONAL_RESOLUTION",
                    "provenance": "DETERMINISTIC_EVIDENCE",
                    "evidence_level": "OBSERVED",
                    "link_status": "EXACT",
                    "link_role": "PRIMARY",
                    "state_after": "PROVISIONALLY_RESOLVED",
                    "transition_authority": "RUNTIME_RECONCILIATION",
                    "run_id": accepted_run,
                    "wave_id": accepted_wave,
                }
            ]

    row = {
        "problem_id": problem_id,
        "problem_revision": 1,
        "natural_problem_eligibility": {
            "eligible": True,
            "exact_primary_run_ids": [
                "run-old-aborted-1",
                "run-old-aborted-2",
                accepted_run,
            ],
        },
        "metrics": {},
    }

    compact = reporter._compact_natural_row(RetriedLedger(), RetriedProblems(), row)

    assert compact["technically_accepted"] is True
    assert compact["run_statuses"] == {
        "run-old-aborted-1": "aborted",
        "run-old-aborted-2": "aborted",
        accepted_run: "accepted",
    }


def test_technical_acceptance_rejects_accepted_run_without_valid_full_problem_checkpoint() -> None:
    problem_id = "natural-no-canonical-closure"
    run_id = "run-accepted-without-full-problem-checkpoint"

    class NoClosureLedger(FakeLedger):
        def __init__(self) -> None:
            super().__init__()
            self.runs[run_id] = {
                "run_id": run_id,
                "status": "accepted",
                "metadata": {
                    "problem_resolution": {
                        "work_origin": "problem",
                        "resolution_claim": "none",
                        "problem_id": problem_id,
                        "problem_revision": 1,
                    }
                },
            }

        def list_waves(self, current_run_id: str) -> list[dict[str, Any]]:
            return [{"wave_id": "wave-random", "status": "accepted", "metadata": {}}]

        def list_checkpoints(self, current_run_id: str) -> list[dict[str, Any]]:
            return [{"checkpoint_id": "checkpoint-random", "status": "accepted", "wave_id": "wave-random"}]

    class NoClosureProblems:
        def verify_chain(self, current_problem_id: str) -> dict[str, Any]:
            return {"ok": True}

        def events_for_revision(
            self, current_problem_id: str, revision: int
        ) -> list[dict[str, Any]]:
            return []

    row = {
        "problem_id": problem_id,
        "problem_revision": 1,
        "natural_problem_eligibility": {
            "eligible": True,
            "exact_primary_run_ids": [run_id],
        },
        "metrics": {},
    }

    compact = reporter._compact_natural_row(NoClosureLedger(), NoClosureProblems(), row)

    assert compact["run_statuses"] == {run_id: "accepted"}
    assert compact["technically_accepted"] is False


def test_explicit_start_remains_exact(monkeypatch: Any, tmp_path: Path) -> None:
    ledger = FakeLedger()
    _install_fakes(monkeypatch, ledger)

    result = reporter.empirical_readiness_report(
        tmp_path,
        observed_at=123.0,
        start_problem_id="explicit-problem",
        start_problem_revision=7,
    )

    assert result["natural_cohort"]["start"] == {
        "problem_id": "explicit-problem",
        "problem_revision": 7,
    }
    assert result["natural_cohort"]["start_source"] == "explicit_exact_start"


def test_stale_audit_is_bounded_and_never_reconciles() -> None:
    ledger = FakeLedger()
    audit = reporter._stale_audit(_lifecycle(), ledger)
    assert audit["audit_only"] is True
    assert audit["reconciliation_performed"] is False
    assert audit["threshold_sensitive_candidates"] == 12
    assert audit["beyond_current_stale_threshold"] == 12
    assert len(audit["sample"]) == 10
    assert {item["subtype"] for item in audit["sample"]} <= {
        "PASSED_PROOF_NO_ACCEPTED_CHECKPOINT",
        "INACTIVE_ACTIVE_RUN_NO_TERMINAL_EVIDENCE",
    }
    assert "details" not in audit


def test_stale_details_cover_every_candidate_and_reuse_subtype_semantics() -> None:
    ledger = FakeLedger()
    lifecycle = _lifecycle()
    below_threshold = lifecycle["runs"][-1]
    below_threshold["reasons"] = ["inactive_without_live_ownership"]
    below_threshold["activity_age_seconds"] = 120

    audit = reporter._stale_audit(lifecycle, ledger, include_details=True)

    assert audit["threshold_sensitive_candidates"] == 12
    assert audit["beyond_current_stale_threshold"] == 11
    assert audit["below_current_stale_threshold"] == 1
    assert len(audit["details"]) == 12
    by_run = {item["run_id"]: item for item in audit["details"]}
    assert by_run["stale-11"]["meets_current_stale_threshold"] is False
    assert by_run["stale-0"]["meets_current_stale_threshold"] is True
    for row in lifecycle["runs"]:
        detail = by_run[row["run_id"]]
        assert detail["activity_age_seconds"] == row["activity_age_seconds"]
        assert detail["latest_state_after"] == row["latest_state_after"]
        assert detail["last_event"] == row["last_event"]
        assert detail["subtype"] == reporter._stale_subtype(row, ledger)


def test_cli_stale_details_is_opt_in(tmp_path: Path, monkeypatch: Any) -> None:
    calls: list[dict[str, Any]] = []

    def fake_report(workspace: Path, **kwargs: Any) -> dict[str, Any]:
        calls.append(kwargs)
        return {"status": "OK"}

    monkeypatch.setattr(reporter, "empirical_readiness_report", fake_report)

    assert reporter.main(["--workspace", str(tmp_path)]) == 0
    assert calls[-1]["stale_details"] is False
    assert reporter.main(["--workspace", str(tmp_path), "--stale-details"]) == 0
    assert calls[-1]["stale_details"] is True


def test_p5_advisory_fails_closed_on_missing_empirical_and_user_outcome_evidence() -> None:
    outcome = {
        "status": "AVAILABLE",
        "numerator": 0,
        "denominator": 1,
        "coverage": 0.0,
        "unknown_is_not_zero": True,
    }
    compact = reporter._p4_compact(_p4(), _cohort(), outcome)
    assert compact["p5_runtime_contract"]["epoch_lifecycle"] == "EPOCH_HARD_STOPPED"
    assert compact["operator_advisory"]["eligible_to_recommend_p5_open"] is False
    assert "p4_predictive_validation_incomplete" in compact["operator_advisory"]["blockers"]
    assert "independent_user_outcome_coverage_incomplete" in compact["operator_advisory"]["blockers"]
    assert compact["operator_advisory"]["advisory_only_never_opens_epoch"] is True


def test_complete_actual_producer_outcome_clears_only_its_advisory_blocker(
    tmp_path: Path,
) -> None:
    from test_problem_resolution_economics import ProblemResolutionEconomicsTests

    # Existing synthetic fixture stays in tmp_path; it is not live outcome evidence.
    ProblemResolutionEconomicsTests()._fixture(tmp_path)
    ledger_path = tmp_path / ".coding-tools" / "orchestration" / "ledger.sqlite3"
    before = ledger_path.read_bytes()
    with reporter.open_existing_ledger_analysis(tmp_path) as snapshot:
        economics = reporter.problem_resolution_economics_report(
            snapshot.ledger, reporter.ProblemLineageFacts.load(snapshot.reader)
        )
    outcome = reporter._independent_outcome_coverage(economics)
    assert outcome["status"] == "AVAILABLE"
    assert outcome["numerator"] == outcome["denominator"] == 1
    assert outcome["coverage"] == 1.0
    assert "rate" not in outcome

    compact = reporter._p4_compact(_p4(), _cohort(), outcome)
    blockers = compact["operator_advisory"]["blockers"]
    assert "independent_user_outcome_coverage_incomplete" not in blockers
    assert "p4_predictive_validation_incomplete" in blockers
    assert compact["operator_advisory"]["eligible_to_recommend_p5_open"] is False
    assert compact["operator_advisory"]["advisory_only_never_opens_epoch"] is True
    assert ledger_path.read_bytes() == before


@pytest.mark.parametrize(
    "outcome",
    [
        {},
        {"status": "UNAVAILABLE", "coverage": None},
        {"status": "OBSERVED", "numerator": 1, "denominator": 1, "rate": 1.0},
        {"status": "AVAILABLE", "numerator": 0, "denominator": 1, "coverage": 0.0},
        {"status": "AVAILABLE", "numerator": 1, "denominator": 2, "coverage": 0.5},
        {"status": "AVAILABLE", "numerator": 0, "denominator": 0, "coverage": None},
        {"status": "AVAILABLE", "numerator": 0, "denominator": 0, "coverage": 1.0},
        {"status": "AVAILABLE", "numerator": 0, "denominator": 1, "coverage": 1.0},
        {"status": "AVAILABLE", "numerator": 2, "denominator": 1, "coverage": 1.0},
        {"status": "AVAILABLE", "numerator": -1, "denominator": -1, "coverage": 1.0},
        {"status": "AVAILABLE", "numerator": True, "denominator": 1, "coverage": 1.0},
        {"status": "AVAILABLE", "numerator": 1, "denominator": True, "coverage": 1.0},
        {"status": "AVAILABLE", "numerator": 1.0, "denominator": 1, "coverage": 1.0},
        {"status": "AVAILABLE", "numerator": 1, "denominator": "1", "coverage": 1.0},
        *[
            {"status": "AVAILABLE", "numerator": 1, "denominator": 1, "coverage": value}
            for value in (True, "1.0", None, float("nan"), float("inf"), -1.0, 1.1, 0.5)
        ],
    ],
)
def test_incomplete_or_invalid_outcome_never_clears_advisory_blocker(
    outcome: dict[str, Any],
) -> None:
    compact = reporter._p4_compact(_p4(), _cohort(), outcome)
    assert "independent_user_outcome_coverage_incomplete" in compact["operator_advisory"]["blockers"]
    assert compact["operator_advisory"]["eligible_to_recommend_p5_open"] is False
