from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.lifecycle_census import (
    LIFECYCLE_CLASSES,
    ProcessIdentityObservation,
    lifecycle_census,
    open_lifecycle_census_snapshot,
    read_task_projection,
)
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger


OBSERVED_AT = 1_800_000_000.0


def _iso(seconds: float) -> str:
    return datetime.fromtimestamp(seconds, timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class LifecycleCensusTests(unittest.TestCase):
    def _run(self, ledger: OrchestrationLedger, *, started_at: str) -> str:
        run_id = ledger.create_run(objective="test lifecycle")
        with ledger._lock, ledger._connect() as connection:
            connection.execute("UPDATE runs SET started_at=? WHERE run_id=?", (started_at, run_id))
        return run_id

    @staticmethod
    def _probe(pid: int, _expected: str) -> ProcessIdentityObservation:
        return ProcessIdentityObservation(pid=pid, exists=True, identity="MISMATCH")

    def _fixture(self, root: Path) -> tuple[OrchestrationLedger, dict[str, str]]:
        ledger = OrchestrationLedger(root)
        old = _iso(OBSERVED_AT - 3_600)
        live = self._run(ledger, started_at=old)
        p5_anchor = self._run(ledger, started_at=old)
        accepting = self._run(ledger, started_at=old)
        grace = self._run(ledger, started_at=_iso(OBSERVED_AT - 60))
        threshold = self._run(ledger, started_at=old)
        unexplained = self._run(ledger, started_at=old)
        terminal_parent = self._run(ledger, started_at=old)
        terminal_wave = ledger.create_wave(terminal_parent, execution_mode="mcp_only")
        ledger.finish_run(terminal_parent, status="accepted")
        job_run = self._run(ledger, started_at=old)
        ledger.append_event(accepting, event_type="state", state_after="ACCEPTING")
        with ledger._lock, ledger._connect() as connection:
            connection.execute("UPDATE runs SET started_at='' WHERE run_id=?", (unexplained,))
            connection.execute(
                """INSERT INTO agent_lanes(
                    lane_id,run_id,wave_id,semantic_key,role,provider,thread_id,session_id,lifecycle,
                    profile,model,effort,base_head,worktree_fp,contract_fp,last_turn_id,created_at,updated_at,metadata_json
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    "unbound-live-lane", "", "", "", "executor", "test", "", "", "active",
                    "", "", "", "", "", "", "", old, old, "{}",
                ),
            )
            connection.execute(
                """INSERT INTO controller_leases(
                    run_id,fencing_token,lease_id,owner_client_id,status,expires_at,updated_at
                ) VALUES(?,?,?,?,?,?,?)""",
                (live, 1, "lease", "controller", "active", OBSERVED_AT + 120, _iso(OBSERVED_AT)),
            )
            connection.execute(
                """INSERT INTO p5_experiment_epochs(
                    activation_epoch_id,experiment_id,ledger_run_id,manifest_sha256,manifest_json,
                    phase,study_type,lifecycle,seed_commitment_sha256,seed_handle,opened_at,updated_at,
                    closed_at,hard_stop_reason,metadata_json
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    "epoch-1", "experiment-1", p5_anchor, "a" * 64, "{}", "A0", "A/A",
                    "EPOCH_HARD_STOPPED", "b" * 64, "secret://redacted", old, old, old,
                    "test", "{}",
                ),
            )
            connection.execute(
                """INSERT INTO managed_process_jobs(
                    job_id,run_id,wave_id,command_id,owner,checkout_id,resource_class,root_pid,
                    root_process_token,process_instance_id,runtime_instance_id,lifecycle_state,
                    started_at,updated_at,finished_at,metadata_json
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    "job-mismatch", job_run, "", "command-mismatch", "test", "wrong-checkout",
                    "MEDIUM", 4242, "expected-token", "process", "runtime", "running", old, old, None, "{}",
                ),
            )
        return ledger, {
            "live": live,
            "p5": p5_anchor,
            "accepting": accepting,
            "grace": grace,
            "threshold": threshold,
            "unexplained": unexplained,
            "terminal_parent": terminal_parent,
            "terminal_wave": terminal_wave,
            "job_run": job_run,
        }

    def test_classifies_every_gate_zero_path_from_one_immutable_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger, ids = self._fixture(root)
            before = hashlib.sha256(ledger.path.read_bytes()).hexdigest()
            projection = {
                "available": True,
                "orchestration": {"run_id": ids["terminal_parent"], "wave_id": ids["terminal_wave"]},
            }
            with open_lifecycle_census_snapshot(root) as snapshot:
                first = lifecycle_census(
                    snapshot,
                    workspace=root,
                    observed_at=OBSERVED_AT,
                    grace_seconds=300,
                    stale_after_seconds=1_800,
                    projection=projection,
                    process_probe=self._probe,
                )
                second = lifecycle_census(
                    snapshot,
                    workspace=root,
                    observed_at=OBSERVED_AT,
                    grace_seconds=300,
                    stale_after_seconds=1_800,
                    projection=projection,
                    process_probe=self._probe,
                )
                self.assertEqual(first, second)
                self.assertEqual(snapshot.ledger_fact_load_statements, 8)
                self.assertEqual(first["read_contract"]["ledger_facts_fact_load_statements"], 8)
                self.assertEqual(first["snapshot"]["integrity_check"], ["ok"])
                self.assertEqual(first["snapshot"]["foreign_key_check_rows"], 0)
            self.assertEqual(hashlib.sha256(ledger.path.read_bytes()).hexdigest(), before)

            classifications = {item["run_id"]: item["classification"] for item in first["runs"]}
            self.assertEqual(classifications[ids["live"]], "LIVE_OWNED")
            self.assertEqual(classifications[ids["p5"]], "P5_EXPERIMENT_ANCHOR")
            self.assertEqual(classifications[ids["accepting"]], "AWAITING_ACCEPTANCE")
            self.assertEqual(classifications[ids["grace"]], "GRACE_PERIOD_INACTIVE")
            self.assertEqual(classifications[ids["threshold"]], "THRESHOLD_SENSITIVE_STALE_CANDIDATE")
            self.assertEqual(classifications[ids["unexplained"]], "UNEXPLAINED_ACTIVE")
            self.assertEqual(classifications[ids["terminal_parent"]], "TERMINAL_PARENT_CONTRADICTION")
            self.assertEqual(first["managed_jobs"][0]["classification"], "STALE_MANAGED_JOB_RESIDUE")
            self.assertEqual(first["projection"]["classification"], "PROJECTION_DRIFT")
            self.assertEqual(first["summary"]["ordinary_active_runs"], 6)
            self.assertEqual(first["summary"]["unbound_live_resource_residues"], 1)
            self.assertEqual(first["unbound_live_resources"][0]["classification"], "UNEXPLAINED_ACTIVE")
            self.assertTrue(LIFECYCLE_CLASSES.issuperset({
                item["classification"] for item in first["runs"]
            }))

    def test_terminal_run_releases_controller_lease_without_hiding_real_contradictions(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            run_id = ledger.create_run(objective="terminal controller lease")
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            ledger.upsert_hub_client(client_id="chatweb:test", client_type="chatweb", role="controller")
            lease = ledger.acquire_controller_lease(
                run_id=run_id,
                owner_client_id="chatweb:test",
                lease_id="terminal-lease",
                ttl_seconds=100_000_000,
            )
            self.assertTrue(lease["acquired"], lease)

            ledger.finish_wave(wave_id, status="aborted")
            ledger.finish_run(run_id, status="aborted")

            released = ledger.get_controller_lease(run_id)
            self.assertIsNotNone(released)
            self.assertEqual(released["status"], "released")
            with open_lifecycle_census_snapshot(root) as snapshot:
                result = lifecycle_census(
                    snapshot,
                    workspace=root,
                    observed_at=float(lease["expires_at"]) - 1,
                    process_probe=self._probe,
                )
            classifications = {item["run_id"]: item["classification"] for item in result["runs"]}
            self.assertNotIn(run_id, classifications)

            checkpoint_run = ledger.create_run(objective="atomic checkpoint controller lease")
            checkpoint_wave = ledger.create_wave(checkpoint_run, execution_mode="mcp_only")
            checkpoint_lease = ledger.acquire_controller_lease(
                run_id=checkpoint_run,
                owner_client_id="chatweb:test",
                lease_id="checkpoint-lease",
                ttl_seconds=100_000_000,
            )
            self.assertTrue(checkpoint_lease["acquired"], checkpoint_lease)
            ledger.accept_checkpoint_atomic(
                run_id=checkpoint_run,
                wave_id=checkpoint_wave,
                git_head="head",
                proof_fingerprint="proof",
            )
            released_checkpoint = ledger.get_controller_lease(checkpoint_run)
            self.assertIsNotNone(released_checkpoint)
            self.assertEqual(released_checkpoint["status"], "released")

            # The existing fixture assertion above still proves a terminal parent
            # with a genuinely active child wave remains a hard contradiction.

    def test_process_token_mismatch_never_becomes_live_ownership(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger, ids = self._fixture(root)
            with ledger._lock, ledger._connect() as connection:
                expected_checkout = hashlib.sha256(str(root.resolve()).lower().encode("utf-8")).hexdigest()
                connection.execute(
                    "UPDATE managed_process_jobs SET checkout_id=? WHERE run_id=?",
                    (expected_checkout, ids["job_run"]),
                )
            with open_lifecycle_census_snapshot(root) as snapshot:
                result = lifecycle_census(
                    snapshot,
                    workspace=root,
                    observed_at=OBSERVED_AT,
                    process_probe=self._probe,
                )
            job = next(item for item in result["managed_jobs"] if item["run_id"] == ids["job_run"])
            run = next(item for item in result["runs"] if item["run_id"] == ids["job_run"])
            self.assertEqual(job["identity"], "MISMATCH")
            self.assertEqual(job["classification"], "STALE_MANAGED_JOB_RESIDUE")
            self.assertEqual(run["ownership"]["live_managed_jobs"], 0)

    def test_matching_managed_process_identity_remains_live_ownership(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger, ids = self._fixture(root)
            expected_checkout = hashlib.sha256(str(root.resolve()).lower().encode("utf-8")).hexdigest()
            with ledger._lock, ledger._connect() as connection:
                connection.execute(
                    "UPDATE managed_process_jobs SET checkout_id=? WHERE run_id=?",
                    (expected_checkout, ids["job_run"]),
                )

            def live_probe(pid: int, _expected: str) -> ProcessIdentityObservation:
                return ProcessIdentityObservation(pid=pid, exists=True, identity="MATCH")

            with open_lifecycle_census_snapshot(root) as snapshot:
                result = lifecycle_census(
                    snapshot,
                    workspace=root,
                    observed_at=OBSERVED_AT,
                    process_probe=live_probe,
                )
            job = next(item for item in result["managed_jobs"] if item["run_id"] == ids["job_run"])
            run = next(item for item in result["runs"] if item["run_id"] == ids["job_run"])
            self.assertEqual(job["classification"], "LIVE_OWNED")
            self.assertEqual(run["classification"], "LIVE_OWNED")
            self.assertEqual(run["ownership"]["live_managed_jobs"], 1)

    def test_stopped_runtime_ignores_only_aged_process_scoped_residue(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            old = _iso(OBSERVED_AT - 3_600)
            recent = _iso(OBSERVED_AT - 60)
            stale_run = self._run(ledger, started_at=old)
            recent_run = self._run(ledger, started_at=old)
            terminal_run = self._run(ledger, started_at=old)
            dead_job_run = self._run(ledger, started_at=old)
            ledger.finish_run(terminal_run, status="accepted")

            for operation_id, run_id, updated_at in (
                ("stale-bound", stale_run, old),
                ("recent-bound", recent_run, recent),
                ("stale-terminal", terminal_run, old),
                ("stale-unbound", "", old),
                ("recent-unbound", "", recent),
            ):
                ledger.start_background_operation(
                    operation_id=operation_id,
                    server_instance_id="retired-server",
                    tool="agent_workflow",
                    run_id=run_id,
                )
                with ledger._lock, ledger._connect() as connection:
                    connection.execute(
                        "UPDATE background_operations SET started_at=?,updated_at=? WHERE operation_id=?",
                        (updated_at, updated_at, operation_id),
                    )

            expected_checkout = hashlib.sha256(str(root.resolve()).lower().encode("utf-8")).hexdigest()
            with ledger._lock, ledger._connect() as connection:
                connection.execute(
                    """INSERT INTO managed_process_jobs(
                        job_id,run_id,wave_id,command_id,owner,checkout_id,resource_class,root_pid,
                        root_process_token,process_instance_id,runtime_instance_id,lifecycle_state,
                        started_at,updated_at,finished_at,metadata_json
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        "dead-job", dead_job_run, "", "dead-command", "test", expected_checkout,
                        "MEDIUM", 4242, "dead-token", "retired-process", "retired-runtime", "running",
                        old, old, None, "{}",
                    ),
                )

            def probe(pid: int, _expected: str) -> ProcessIdentityObservation:
                self.assertEqual(pid, 4242)
                return ProcessIdentityObservation(pid=pid, exists=False, identity="NOT_RUNNING")

            with open_lifecycle_census_snapshot(root) as snapshot:
                result = lifecycle_census(
                    snapshot,
                    workspace=root,
                    observed_at=OBSERVED_AT,
                    grace_seconds=300,
                    stale_after_seconds=1_800,
                    process_probe=probe,
                )

            records = {item["run_id"]: item for item in result["runs"]}
            self.assertEqual(records[stale_run]["classification"], "THRESHOLD_SENSITIVE_STALE_CANDIDATE")
            self.assertEqual(records[stale_run]["ownership"]["running_background_operations"], 0)
            self.assertEqual(records[stale_run]["stale_background_operations"], 1)
            self.assertEqual(records[recent_run]["classification"], "LIVE_OWNED")
            self.assertEqual(records[recent_run]["ownership"]["running_background_operations"], 1)
            self.assertNotIn(terminal_run, records)
            dead_job = next(item for item in result["managed_jobs"] if item["job_id"] == "dead-job")
            self.assertEqual(dead_job["classification"], "STALE_MANAGED_JOB_RESIDUE")
            self.assertEqual(
                {item["resource_id"] for item in result["unbound_live_resources"]},
                {"recent-unbound"},
            )
            self.assertEqual(result["summary"]["stale_background_operation_residues"], 3)

    def test_snapshot_never_initializes_writer_or_runtime_governor(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger, _ = self._fixture(root)
            with patch.object(OrchestrationLedger, "__init__", side_effect=AssertionError("writer initialization is forbidden")):
                with open_lifecycle_census_snapshot(root) as snapshot:
                    result = lifecycle_census(
                        snapshot,
                        workspace=root,
                        observed_at=OBSERVED_AT,
                        process_probe=self._probe,
                    )
            self.assertFalse(result["read_contract"]["canonical_writer_instantiated"])
            self.assertFalse(result["mutated_canonical_ledger"])

    def test_projection_classification_tracks_canonical_active_and_terminal_states(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            cases = (
                ("active", "PROVING", "PROJECTION_CONSISTENT"),
                ("accepted", "CHECKPOINTED", "CHECKPOINTED"),
                ("blocked", "BLOCKED", "BLOCKED"),
                ("aborted", "ABORTED", "ABORTED"),
            )
            accepted_projection: tuple[str, str] | None = None
            for run_status, canonical_state, expected_classification in cases:
                run_id = self._run(ledger, started_at=_iso(OBSERVED_AT - 60))
                wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
                ledger.append_event(run_id, event_type="state", state_after=canonical_state)
                if run_status != "active":
                    with ledger._lock, ledger._connect() as connection:
                        connection.execute("UPDATE runs SET status=? WHERE run_id=?", (run_status, run_id))
                        connection.execute("UPDATE waves SET status=? WHERE run_id=? AND wave_id=?", (run_status, run_id, wave_id))
                with open_lifecycle_census_snapshot(root) as snapshot:
                    result = lifecycle_census(
                        snapshot,
                        workspace=root,
                        observed_at=OBSERVED_AT,
                        projection={
                            "available": True,
                            "orchestration": {
                                "run_id": run_id,
                                "wave_id": wave_id,
                                "orchestration_state": canonical_state,
                            },
                        },
                        process_probe=self._probe,
                    )
                self.assertEqual(result["projection"]["classification"], expected_classification)
                if run_status == "accepted":
                    accepted_projection = (run_id, wave_id)
            self.assertIsNotNone(accepted_projection)
            accepted_run, accepted_wave = accepted_projection or ("", "")
            with open_lifecycle_census_snapshot(root) as snapshot:
                drift = lifecycle_census(
                    snapshot,
                    workspace=root,
                    observed_at=OBSERVED_AT,
                    projection={
                        "available": True,
                        "orchestration": {
                            "run_id": accepted_run,
                            "wave_id": accepted_wave,
                            "orchestration_state": "ACCEPTING",
                        },
                    },
                    process_probe=self._probe,
                )
            self.assertEqual(drift["projection"]["classification"], "PROJECTION_DRIFT")

    def test_read_task_projection_prefers_contextual_over_nonempty_stale_global(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_dir = root / ".coding-tools"
            context_dir = state_dir / "task-contexts"
            context_dir.mkdir(parents=True)
            stale_global = {
                "orchestration": {
                    "run_id": "accepted-run",
                    "wave_id": "wave-1",
                    "orchestration_state": "ACCEPTING",
                },
            }
            terminal_context = {
                "orchestration": {
                    "run_id": "accepted-run",
                    "wave_id": "wave-1",
                    "orchestration_state": "CHECKPOINTED",
                },
            }
            (state_dir / "task-state.json").write_text(json.dumps(stale_global), encoding="utf-8")
            (context_dir / "terminal.json").write_text(json.dumps(terminal_context), encoding="utf-8")

            projection = read_task_projection(root)

            self.assertTrue(projection["available"])
            self.assertEqual(projection["status"], "contextual")
            self.assertEqual(projection["mode"], "contextual")
            self.assertEqual(projection["context_count"], 1)
            self.assertEqual(projection["orchestration"], {})
            self.assertEqual(projection["contextual_projections"][0]["orchestration_state"], "CHECKPOINTED")

    def test_read_task_projection_uses_global_only_without_contextual_projections(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_dir = root / ".coding-tools"
            state_dir.mkdir(parents=True)
            global_projection = {
                "orchestration": {
                    "run_id": "active-run",
                    "wave_id": "wave-1",
                    "orchestration_state": "PROVING",
                },
            }
            (state_dir / "task-state.json").write_text(json.dumps(global_projection), encoding="utf-8")

            projection = read_task_projection(root)

            self.assertTrue(projection["available"])
            self.assertEqual(projection["status"], "readable")
            self.assertEqual(projection["mode"], "global")
            self.assertEqual(projection["orchestration"], global_projection["orchestration"])

    def test_read_task_projection_fails_closed_on_invalid_contextual_projection(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_dir = root / ".coding-tools"
            context_dir = state_dir / "task-contexts"
            context_dir.mkdir(parents=True)
            global_projection = {
                "orchestration": {
                    "run_id": "active-run",
                    "wave_id": "wave-1",
                    "orchestration_state": "PROVING",
                },
            }
            (state_dir / "task-state.json").write_text(json.dumps(global_projection), encoding="utf-8")
            (context_dir / "invalid.json").write_text("{not-json", encoding="utf-8")

            projection = read_task_projection(root)

            self.assertFalse(projection["available"])
            self.assertEqual(projection["status"], "contextual_invalid")
            self.assertEqual(projection["mode"], "contextual")
            self.assertEqual(projection["invalid_context_count"], 1)

    def test_unavailable_or_empty_projection_does_not_hide_an_active_ledger_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            run_id = self._run(ledger, started_at=_iso(OBSERVED_AT - 60))
            wave_id = ledger.create_wave(run_id, execution_mode="mcp_only")
            ledger.append_event(run_id, event_type="state", state_after="PROVING")

            for projection, expected, reason in (
                ({"available": False, "status": "unreadable", "orchestration": {}}, "PROJECTION_UNAVAILABLE", None),
                ({"available": True, "orchestration": {}}, "PROJECTION_DRIFT", "active_ledger_run_missing_projection"),
            ):
                with self.subTest(expected=expected), open_lifecycle_census_snapshot(root) as snapshot:
                    result = lifecycle_census(
                        snapshot,
                        workspace=root,
                        observed_at=OBSERVED_AT,
                        projection=projection,
                        process_probe=self._probe,
                    )
                self.assertEqual(result["projection"]["classification"], expected)
                if reason:
                    self.assertEqual(result["projection"]["reason"], reason)
                self.assertNotEqual(result["projection"]["classification"], "NO_ACTIVE_PROJECTION")
                self.assertEqual(result["projection"].get("run_id"), "")
                self.assertTrue(wave_id)


if __name__ == "__main__":
    unittest.main()
