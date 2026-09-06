from __future__ import annotations

import hashlib
import http.client
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.operator_report import (
    build_command_completion_report,
    build_operator_completion_report,
)
from coding_tools_mcp.protocol import PROTOCOL_VERSION
from coding_tools_mcp.server import MCPHandler, Runtime, RuntimeHTTPServer
from coding_tools_mcp.task_state import ContextualTaskStateStore, TaskStateStore


class OperatorReportIsolationTests(unittest.TestCase):
    RUN_ID = "a" * 32
    WAVE_ID = "b" * 32

    @staticmethod
    def _path_hash(path: str) -> str:
        return hashlib.sha256(path.encode("utf-8")).hexdigest()

    @classmethod
    def _patch_event(
        cls,
        seq: int,
        *,
        run_id: str | None = None,
        wave_id: str | None = None,
        event_id: str | None = None,
        event_time: str = "2026-09-05T05:00:00.000Z",
        complete: bool = True,
        file_ids: list[object] | None = None,
        file_count: object = 1,
        additions: object = 1,
        removals: object = 0,
        line_changes: object = 1,
        payload_extra: dict | None = None,
    ) -> dict:
        ids = [cls._path_hash("fixture.py")] if file_ids is None else file_ids
        payload = {
            "schema_version": 1,
            "measurement": "applied_patch_delta_v1",
            "content_free": True,
            "production_behavior_changed": False,
            "complete": complete,
            "file_count": file_count,
            "additions": additions,
            "removals": removals,
            "line_changes": line_changes,
            "file_ids": ids,
        }
        payload.update(payload_extra or {})
        return {
            "seq": seq,
            "event_id": event_id or f"{seq:032x}",
            "event_time": event_time,
            "event_type": "patch_surface_observed",
            "run_id": run_id or cls.RUN_ID,
            "wave_id": wave_id or cls.WAVE_ID,
            "payload": payload,
        }

    @classmethod
    def _operator_report(
        cls,
        events: list[dict],
        *,
        checkpoint: dict | None = None,
        task_state: dict | None = None,
    ) -> dict:
        run_id = cls.RUN_ID
        wave_id = cls.WAVE_ID

        class Ledger:
            def get_run(self, requested_run_id: str) -> dict:
                assert requested_run_id == run_id
                return {"status": "active"}

            def list_waves(self, requested_run_id: str) -> list[dict]:
                assert requested_run_id == run_id
                return [{"wave_id": wave_id, "status": "active"}]

            def list_proofs(self, requested_run_id: str, *, wave_id: str) -> list[dict]:
                assert requested_run_id == run_id
                return []

            def list_checkpoints(self, requested_run_id: str, *, wave_id: str) -> list[dict]:
                assert requested_run_id == run_id
                return [checkpoint] if checkpoint else []

            def list_events(self, requested_run_id: str, *, wave_id: str) -> list[dict]:
                assert requested_run_id == run_id
                return list(events)

            def wave_objective_provenance(self, requested_run_id: str, requested_wave_id: str) -> dict:
                assert requested_run_id == run_id
                assert requested_wave_id == wave_id
                return {"objective_source": "test_fixture"}

            def verify_chain(self, requested_run_id: str) -> dict:
                assert requested_run_id == run_id
                return {"ok": True, "checked": len(events)}

        state = {
            "status": "waiting",
            "modified_files": [],
            "orchestration": {"run_id": run_id, "wave_id": wave_id},
        }
        state.update(task_state or {})
        ctx = SimpleNamespace(
            run_id=run_id,
            wave_id=wave_id,
            state="REPLAN",
            base_head="c" * 40,
            worktree_fp="d" * 64,
            contract_fp="",
        )
        return build_operator_completion_report(
            ledger=Ledger(),
            ctx=ctx,
            task_state=state,
            reports={},
        )

    def test_replan_projects_canonical_partial_patch_after_unrelated_events(self) -> None:
        unrelated = [
            {
                "seq": index,
                "event_type": "observation_span_recorded",
                "run_id": self.RUN_ID,
                "wave_id": self.WAVE_ID,
                "payload": {"ignored": True},
            }
            for index in range(1, 151)
        ]
        event = self._patch_event(
            151,
            payload_extra={
                "path": "must/not/leak.py",
                "source": "must-not-leak",
                "command": "must-not-leak",
                "arbitrary": {"secret": "must-not-leak"},
            },
        )
        report = self._operator_report([*unrelated, event])
        changed = report["what_changed"]
        projection = changed["patch_surface_observations"]

        self.assertEqual(changed["files"], [])
        self.assertEqual(changed["source"], "canonical_patch_surface_observations")
        self.assertEqual(report["proof_actually_run"]["count"], 0)
        self.assertEqual(report["accepted_or_not"], "NOT_ACCEPTED_REPLAN_REQUIRED")
        self.assertEqual(projection["matching_event_count"], 1)
        self.assertEqual(projection["observation_count"], 1)
        self.assertTrue(projection["complete"])
        self.assertEqual(
            projection["authority"],
            "observation_only_not_exact_byte_receipt_proof_acceptance_or_user_outcome",
        )
        serialized = json.dumps(report, sort_keys=True)
        for forbidden in ("must/not/leak.py", "must-not-leak", '"arbitrary"'):
            self.assertNotIn(forbidden, serialized)

    def test_patch_projection_rejects_wrong_scope_and_malformed_identity_or_metadata(self) -> None:
        wrong_run = self._patch_event(1, run_id="f" * 32)
        wrong_wave = self._patch_event(2, wave_id="e" * 32)
        bad_id = self._patch_event(3, event_id="not-an-event-id")
        bad_time = self._patch_event(4, event_time="2026-99-99T25:61:00Z")
        bad_metadata = self._patch_event(
            5,
            payload_extra={"measurement": "wrong_measurement"},
        )
        report = self._operator_report(
            [wrong_run, wrong_wave, bad_id, bad_time, bad_metadata]
        )
        changed = report["what_changed"]
        projection = changed["patch_surface_observations"]

        self.assertEqual(changed["source"], "no_durable_file_receipts")
        self.assertEqual(projection["matching_event_count"], 3)
        self.assertEqual(projection["observation_count"], 0)
        self.assertEqual(projection["rejected_event_count"], 3)
        self.assertTrue(projection["invalid"])
        self.assertFalse(projection["truncated"])
        self.assertFalse(projection["complete"])

    def test_patch_projection_requires_exact_schema_and_canonical_timestamp(self) -> None:
        valid_times = [
            "2026-09-05T05:00:00Z",
            "2026-09-05T05:00:00.1+00:00",
            "2024-02-29T23:59:59.123456-05:30",
            "2026-09-05T05:00:00+23:59",
        ]
        for seq, event_time in enumerate(valid_times, start=20):
            with self.subTest(valid_time=event_time):
                projection = self._operator_report(
                    [self._patch_event(seq, event_time=event_time)]
                )["what_changed"]["patch_surface_observations"]
                self.assertEqual(projection["observation_count"], 1)
                self.assertEqual(projection["rejected_event_count"], 0)
                self.assertTrue(projection["complete"])
                self.assertEqual(projection["observations"][0]["event_time"], event_time)

        invalid_schema_values = [1.0, True, "1", None]
        for seq, schema_version in enumerate(invalid_schema_values, start=30):
            with self.subTest(schema_version=schema_version):
                event = self._patch_event(
                    seq,
                    payload_extra={"schema_version": schema_version},
                )
                projection = self._operator_report([event])["what_changed"]["patch_surface_observations"]
                self.assertEqual(projection["observation_count"], 0)
                self.assertEqual(projection["rejected_event_count"], 1)
                self.assertTrue(projection["invalid"])

        missing_schema = self._patch_event(34)
        missing_schema["payload"].pop("schema_version")
        projection = self._operator_report([missing_schema])["what_changed"]["patch_surface_observations"]
        self.assertEqual(projection["observation_count"], 0)
        self.assertEqual(projection["rejected_event_count"], 1)
        self.assertTrue(projection["invalid"])

        invalid_times = [
            "2026-09-05 05:00:00Z",
            "20260905T050000Z",
            "2026-W36-6T05:00:00Z",
            "2026-09-05T05:00:00",
            "2025-02-29T05:00:00Z",
            "2026-09-05T24:00:00Z",
            "2026-09-05T05:00:00+24:00",
            "2026-09-05T05:00:00+01:60",
            "2026-09-05T05:00:00Z ",
            "２０２６-09-05T05:00:00Z",
            "2026-09-05\n05:00:00Z",
        ]
        for seq, event_time in enumerate(invalid_times, start=40):
            with self.subTest(invalid_time=event_time):
                projection = self._operator_report(
                    [self._patch_event(seq, event_time=event_time)]
                )["what_changed"]["patch_surface_observations"]
                self.assertEqual(projection["observation_count"], 0)
                self.assertEqual(projection["rejected_event_count"], 1)
                self.assertTrue(projection["invalid"])

    def test_patch_projection_preserves_true_zero_and_marks_empty_missing_or_contradictory_counts(self) -> None:
        true_zero = self._patch_event(
            10,
            file_count=1,
            additions=0,
            removals=0,
            line_changes=0,
        )
        empty = self._patch_event(
            11,
            file_ids=[],
            file_count=0,
            additions=0,
            removals=0,
            line_changes=0,
        )
        missing = self._patch_event(12)
        missing["payload"].pop("additions")
        invalid = self._patch_event(
            13,
            file_ids=[],
            file_count=True,
            additions=None,
            removals=-1,
            line_changes=False,
        )
        contradictory = self._patch_event(
            14,
            file_ids=[self._path_hash("one.py")],
            file_count=2,
            additions=1,
            removals=1,
            line_changes=9,
        )
        projection = self._operator_report(
            [true_zero, empty, missing, invalid, contradictory]
        )["what_changed"]["patch_surface_observations"]
        by_seq = {item["seq"]: item for item in projection["observations"]}

        self.assertEqual(
            {key: by_seq[10][key] for key in ("file_count", "additions", "removals", "line_changes")},
            {"file_count": 1, "additions": 0, "removals": 0, "line_changes": 0},
        )
        self.assertTrue(by_seq[10]["complete"])
        self.assertFalse(by_seq[10]["invalid"])
        self.assertEqual(by_seq[11]["file_count"], 0)
        self.assertEqual(by_seq[11]["additions"], 0)
        self.assertEqual(by_seq[11]["removals"], 0)
        self.assertEqual(by_seq[11]["line_changes"], 0)
        self.assertTrue(by_seq[11]["invalid"])
        self.assertFalse(by_seq[11]["complete"])
        self.assertIn("file_count", by_seq[11]["invalid_fields"])
        self.assertIn("file_ids", by_seq[11]["invalid_fields"])
        self.assertEqual(by_seq[12]["additions"], None)
        self.assertTrue(by_seq[12]["invalid"])
        self.assertFalse(by_seq[12]["complete"])
        self.assertEqual(by_seq[13]["file_count"], None)
        self.assertEqual(by_seq[13]["additions"], None)
        self.assertEqual(by_seq[13]["removals"], None)
        self.assertEqual(by_seq[13]["line_changes"], None)
        self.assertTrue(by_seq[13]["invalid"])
        self.assertEqual(by_seq[14]["file_count"], None)
        self.assertEqual(by_seq[14]["line_changes"], None)
        self.assertEqual(by_seq[14]["additions"], 1)
        self.assertEqual(by_seq[14]["removals"], 1)
        self.assertTrue(by_seq[14]["invalid"])
        self.assertFalse(projection["complete"])

    def test_patch_projection_caps_latest_matching_rows_after_scope_filtering(self) -> None:
        matching = [
            self._patch_event(
                seq,
                file_count=1,
                additions=0,
                removals=0,
                line_changes=0,
            )
            for seq in range(1, 106)
        ]
        projection = self._operator_report(matching)["what_changed"]["patch_surface_observations"]
        self.assertEqual(projection["matching_event_count"], 105)
        self.assertEqual(projection["observation_count"], 100)
        self.assertEqual(projection["observations"][0]["seq"], 6)
        self.assertEqual(projection["observations"][-1]["seq"], 105)
        self.assertTrue(projection["truncated"])
        self.assertFalse(projection["complete"])

    def test_patch_projection_marks_duplicate_or_invalid_ids_incomplete(self) -> None:
        hashes = sorted(self._path_hash(f"path-{index}.py") for index in range(3))
        malformed_ids = [hashes[0], hashes[0], "BAD-ID", hashes[1]]
        incomplete = self._patch_event(
            200,
            complete=False,
            file_ids=malformed_ids,
            file_count=4,
            additions=0,
            removals=0,
            line_changes=0,
        )
        projection = self._operator_report([incomplete])["what_changed"]["patch_surface_observations"]
        row = projection["observations"][0]
        self.assertLessEqual(len(row["path_hashes_sha256"]), 256)
        self.assertTrue(row["truncated"])
        self.assertTrue(row["invalid"])
        self.assertFalse(row["producer_complete"])
        self.assertFalse(row["complete"])
        self.assertTrue(projection["truncated"])
        self.assertTrue(projection["invalid"])
        self.assertFalse(projection["complete"])

    def test_patch_projection_clean_producer_truncation_is_incomplete_not_invalid(self) -> None:
        hashes = sorted(self._path_hash(f"path-{index}.py") for index in range(256))
        incomplete = self._patch_event(
            201,
            complete=False,
            file_ids=hashes,
            file_count=257,
            additions=0,
            removals=0,
            line_changes=0,
        )
        projection = self._operator_report([incomplete])["what_changed"]["patch_surface_observations"]
        row = projection["observations"][0]
        self.assertEqual(row["path_hashes_sha256"], hashes)
        self.assertEqual(row["file_count"], 257)
        self.assertEqual(row["additions"], 0)
        self.assertEqual(row["removals"], 0)
        self.assertEqual(row["line_changes"], 0)
        self.assertTrue(row["truncated"])
        self.assertFalse(row["invalid"])
        self.assertFalse(row["producer_complete"])
        self.assertFalse(row["complete"])
        self.assertTrue(projection["truncated"])
        self.assertFalse(projection["invalid"])
        self.assertFalse(projection["complete"])

    def test_accepted_receipts_keep_precedence_and_plain_command_report_contract_is_unchanged(self) -> None:
        checkpoint = {
            "checkpoint_id": "checkpoint-report-fixture",
            "metadata": {
                "accepted_files": {
                    "source": "explicit_acceptance_attestations",
                    "files": [
                        {
                            "path": "accepted.py",
                            "state": "modified",
                            "sha256": "f" * 64,
                            "size_bytes": 17,
                            "receipt_kind": "explicit_attestation",
                            "run_id": self.RUN_ID,
                            "wave_id": self.WAVE_ID,
                        }
                    ],
                }
            },
        }
        report = self._operator_report([self._patch_event(300)], checkpoint=checkpoint)
        self.assertEqual(
            report["what_changed"]["source"],
            "accepted_checkpoint_file_attestations",
        )
        self.assertEqual([item["path"] for item in report["what_changed"]["files"]], ["accepted.py"])

        command_report = build_command_completion_report(
            task_state={
                "status": "completed",
                "modified_files": [],
                "orchestration": {},
                "last_command_result": {
                    "command_id": "plain-command-fixture",
                    "kind": "command",
                    "result_status": "passed",
                    "status": "exited",
                    "exit_code": 0,
                    "duration_ms": 1,
                },
            },
            workspace_identity={},
        )
        self.assertIsNotNone(command_report)
        self.assertEqual(
            set(command_report["what_changed"]),
            {"files", "source", "raw_source_or_command_output_included"},
        )

    def test_terminal_get_keeps_semantic_report_identity_stable_through_ack(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            runtime = Runtime(root, permission_mode="dangerous")
            try:
                result = runtime.agent_workflow({
                    "workflow": "bugfix",
                    "phase": "execute",
                    "objective": "stable operator report fixture",
                    "evaluation": {"provenance": "benchmark"},
                    "patch": "*** Begin Patch\n*** Update File: app.py\n@@\n-VALUE = 1\n+VALUE = 2\n*** End Patch",
                    "verification": "none",
                    "include_diff": False,
                })
                run_id = result["orchestration"]["run_id"]
                wave_id = result["orchestration"]["wave_id"]
                runtime.orchestration_ledger.record_proof(
                    run_id=run_id,
                    wave_id=wave_id,
                    stage_id="stable-operator-report-fixture",
                    stage_version="1",
                    input_fingerprint="stable-operator-report-fixture-proof",
                    status="passed",
                )
                accepted = runtime.task_control({
                    "action": "accept",
                    "run_id": run_id,
                    "reason": "fixture accepts proven terminal wave",
                })
                self.assertTrue(accepted["accepted"])
                checkpoint = runtime.orchestration_ledger.list_checkpoints(
                    run_id, wave_id=wave_id
                )[-1]

                first = runtime.task_control({"action": "get", "run_id": run_id})
                first_state = first["state"]
                report_id = str(first_state["completion_report_id"])
                self.assertTrue(report_id)
                self.assertEqual(
                    first_state["completion_report"]["source_run_wave"]["checkpoint_id"],
                    checkpoint["checkpoint_id"],
                )

                second = runtime.task_control({"action": "get", "run_id": run_id})
                self.assertEqual(second["state"]["completion_report_id"], report_id)

                acknowledged = runtime.task_control({
                    "action": "ack",
                    "run_id": run_id,
                    "wave_id": wave_id,
                    "message_id": report_id,
                })
                self.assertTrue(acknowledged["acknowledged"])
                after_ack = runtime.task_state.get()
                acknowledged_at = after_ack["completion_report_acknowledged_at"]
                self.assertEqual(after_ack["completion_report_acknowledged_id"], report_id)
                self.assertTrue(acknowledged_at)

                third = runtime.task_control({"action": "get", "run_id": run_id})
                self.assertEqual(third["state"]["completion_report_id"], report_id)
                self.assertEqual(
                    third["state"]["completion_report_acknowledged_id"], report_id
                )
                self.assertEqual(
                    third["state"]["completion_report_acknowledged_at"], acknowledged_at
                )
                repeated = runtime.task_control({"action": "ack", "message_id": report_id})
                self.assertTrue(repeated["acknowledged"])
                self.assertEqual(
                    runtime.task_state.get()["completion_report_acknowledged_at"],
                    acknowledged_at,
                )
            finally:
                runtime.close()

    def test_read_only_audit_preserves_acknowledged_terminal_report_latch(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            runtime = Runtime(root, permission_mode="dangerous")
            try:
                result = runtime.agent_workflow({
                    "workflow": "bugfix",
                    "phase": "execute",
                    "objective": "accepted audit latch fixture",
                    "evaluation": {"provenance": "benchmark"},
                    "patch": "*** Begin Patch\n*** Update File: app.py\n@@\n-VALUE = 1\n+VALUE = 2\n*** End Patch",
                    "verification": "none",
                    "include_diff": False,
                })
                run_id = result["orchestration"]["run_id"]
                runtime.orchestration_ledger.record_proof(
                    run_id=run_id,
                    wave_id=result["orchestration"]["wave_id"],
                    stage_id="operator-report-latch-fixture",
                    stage_version="1",
                    input_fingerprint="operator-report-latch-fixture-proof",
                    status="passed",
                )
                accepted = runtime.task_control({
                    "action": "accept",
                    "run_id": run_id,
                    "reason": "fixture accepts proven terminal wave",
                })
                self.assertTrue(accepted["accepted"])
                pending = runtime.task_state.pending_completion_report()
                self.assertIsNotNone(pending)
                report_id = str(pending["report_id"])

                acknowledged = runtime.task_control({"action": "ack", "message_id": report_id})
                self.assertTrue(acknowledged["acknowledged"])
                self.assertIsNone(runtime.task_state.pending_completion_report())

                audit = runtime.task_control({"action": "audit", "run_id": run_id, "limit": 20})
                self.assertEqual(audit["completion_report"]["accepted_or_not"], "ACCEPTED")
                after = runtime.task_state.get()
                self.assertEqual(after["completion_report_id"], report_id)
                self.assertEqual(after["completion_report_acknowledged_id"], report_id)
                self.assertIsNone(runtime.task_state.pending_completion_report())
            finally:
                runtime.close()

    def test_exact_terminal_get_materializes_missing_report_without_making_audit_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            runtime = Runtime(root, permission_mode="dangerous")
            try:
                result = runtime.agent_workflow({
                    "workflow": "bugfix",
                    "phase": "execute",
                    "objective": "exact recovery completion report fixture",
                    "evaluation": {"provenance": "benchmark"},
                    "patch": "*** Begin Patch\n*** Update File: app.py\n@@\n-VALUE = 1\n+VALUE = 2\n*** End Patch",
                    "verification": "none",
                    "include_diff": False,
                })
                run_id = result["orchestration"]["run_id"]
                wave_id = result["orchestration"]["wave_id"]
                runtime.orchestration_ledger.record_proof(
                    run_id=run_id,
                    wave_id=wave_id,
                    stage_id="exact-recovery-report-fixture",
                    stage_version="1",
                    input_fingerprint="exact-recovery-report-fixture-proof",
                    status="passed",
                )
                accepted = runtime.task_control({
                    "action": "accept",
                    "run_id": run_id,
                    "reason": "fixture accepts proven terminal wave",
                })
                self.assertTrue(accepted["accepted"])
                self.assertEqual(accepted["orchestration"]["orchestration_state"], "CHECKPOINTED")

                # Simulate a legacy/corrupted persisted projection. The public
                # update surface intentionally cannot clear an issued report latch.
                fixture_store = runtime.task_state._current_store()
                with fixture_store._lock:
                    fixture_state = fixture_store._read()
                    fixture_state["completion_report"] = None
                    fixture_state["completion_report_id"] = ""
                    fixture_state["completion_report_acknowledged_id"] = ""
                    fixture_state["completion_report_acknowledged_at"] = None
                    fixture_store._write(fixture_state)
                self.assertEqual(runtime.task_state.get()["completion_report_id"], "")

                audit = runtime.task_control({"action": "audit", "run_id": run_id, "limit": 20})
                self.assertEqual(audit["completion_report"]["accepted_or_not"], "ACCEPTED")
                self.assertEqual(runtime.task_state.get()["completion_report_id"], "")

                recovered = runtime.task_control({"action": "get", "run_id": run_id})
                recovered_state = recovered["state"]
                report_id = str(recovered_state["completion_report_id"])
                self.assertTrue(report_id)
                self.assertEqual(recovered_state["completion_report"]["source_run_wave"]["run_id"], run_id)
                self.assertEqual(recovered_state["completion_report"]["source_run_wave"]["wave_id"], wave_id)
                self.assertEqual(TaskStateStore._completion_report_id(recovered_state["completion_report"]), report_id)

                acknowledged = runtime.task_control({
                    "action": "ack",
                    "run_id": run_id,
                    "wave_id": wave_id,
                    "message_id": report_id,
                })
                self.assertTrue(acknowledged["acknowledged"])
                self.assertEqual(acknowledged["report_id"], report_id)
                after_ack = runtime.task_state.get()
                self.assertEqual(after_ack["completion_report_acknowledged_id"], report_id)
                self.assertTrue(after_ack["completion_report_acknowledged_at"])
            finally:
                runtime.close()

    def test_historical_audit_cannot_replace_current_operator_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            runtime = Runtime(root, permission_mode="dangerous")
            try:
                first = runtime.agent_workflow({
                    "workflow": "bugfix",
                    "phase": "execute",
                    "objective": "first accepted run",
                    "evaluation": {"provenance": "benchmark"},
                    "patch": "*** Begin Patch\n*** Update File: app.py\n@@\n-VALUE = 1\n+VALUE = 2\n*** End Patch",
                    "verification": "none",
                    "include_diff": False,
                })
                first_run_id = first["orchestration"]["run_id"]
                runtime.orchestration_ledger.record_proof(
                    run_id=first_run_id,
                    wave_id=first["orchestration"]["wave_id"],
                    stage_id="first-operator-report-fixture",
                    stage_version="1",
                    input_fingerprint="first-operator-report-fixture-proof",
                    status="passed",
                )
                runtime.task_control({
                    "action": "accept",
                    "run_id": first_run_id,
                    "reason": "fixture accepts first run",
                })
                first_pending = runtime.task_state.pending_completion_report()
                self.assertIsNotNone(first_pending)
                runtime.task_control({
                    "action": "update",
                    "payload": {
                        "extension": "operator_report_ack_v1",
                        "report_id": first_pending["report_id"],
                    },
                })
                runtime.task_control({"action": "start", "objective": "second accepted run"})

                second = runtime.agent_workflow({
                    "workflow": "bugfix",
                    "phase": "execute",
                    "objective": "second accepted run",
                    "evaluation": {"provenance": "benchmark"},
                    "patch": "*** Begin Patch\n*** Update File: app.py\n@@\n-VALUE = 2\n+VALUE = 3\n*** End Patch",
                    "verification": "none",
                    "include_diff": False,
                })
                second_run_id = second["orchestration"]["run_id"]
                runtime.orchestration_ledger.record_proof(
                    run_id=second_run_id,
                    wave_id=second["orchestration"]["wave_id"],
                    stage_id="second-operator-report-fixture",
                    stage_version="1",
                    input_fingerprint="second-operator-report-fixture-proof",
                    status="passed",
                )
                runtime.task_control({
                    "action": "accept",
                    "run_id": second_run_id,
                    "reason": "fixture accepts second run",
                })
                before = runtime.task_state.get()
                current_report_id = before["completion_report_id"]
                self.assertEqual(
                    before["completion_report"]["source_run_wave"]["run_id"],
                    second_run_id,
                )

                historical = runtime.task_control({
                    "action": "audit",
                    "run_id": first_run_id,
                    "limit": 20,
                })
                self.assertEqual(
                    historical["completion_report"]["source_run_wave"]["run_id"],
                    first_run_id,
                )
                historical_report_id = TaskStateStore._completion_report_id(
                    historical["completion_report"]
                )
                after = runtime.task_state.get()
                self.assertEqual(after["completion_report_id"], current_report_id)
                self.assertEqual(
                    after["completion_report"]["source_run_wave"]["run_id"],
                    second_run_id,
                )
                self.assertEqual(
                    runtime.task_state.pending_completion_report()["report_id"],
                    current_report_id,
                )

                with self.assertRaises(ToolFailure) as stale_ack:
                    runtime.task_control({
                        "action": "update",
                        "payload": {
                            "extension": "operator_report_ack_v1",
                            "report_id": historical_report_id,
                        },
                    })
                self.assertEqual(stale_ack.exception.code, "OPERATOR_REPORT_ACK_INVALID")
                acknowledged = runtime.task_control({
                    "action": "update",
                    "payload": {
                        "extension": "operator_report_ack_v1",
                        "report_id": current_report_id,
                    },
                })
                self.assertTrue(acknowledged["acknowledged"])
                started = runtime.task_control({"action": "start", "objective": "third task"})
                self.assertEqual(started["state"]["objective"], "third task")
            finally:
                runtime.close()

    def test_operator_report_latch_blocks_replacement_until_exact_ack(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                runtime.task_state.update({"objective": "terminal command", "status": "active"})
                runtime.task_state.record_command_started("delivery-helper", "command-delivery", ".")
                payload = {
                    "ok": True,
                    "status": "exited",
                    "command_id": "command-delivery",
                    "session_id": "command-delivery",
                    "exit_code": 0,
                    "elapsed_ms": 7,
                }
                runtime._record_task_tool_result(
                    "command_control",
                    {"action": "poll", "command_id": "command-delivery"},
                    payload,
                )
                pending = runtime.task_state.pending_completion_report()
                self.assertIsNotNone(pending)
                report_id = str(pending["report_id"])

                for args in (
                    {"action": "start", "objective": "replacement"},
                    {"action": "clear"},
                    {"action": "resume", "next_step": "unsafe"},
                    {"action": "update", "current_step": "hide report"},
                ):
                    with self.assertRaises(ToolFailure) as blocked:
                        runtime.task_control(args)
                    self.assertEqual(blocked.exception.code, "OPERATOR_REPORT_ACK_REQUIRED")

                with self.assertRaises(ToolFailure) as blocked_workflow:
                    runtime.agent_workflow({
                        "workflow": "diagnose",
                        "phase": "prepare",
                        "objective": "must report first",
                        "execution_mode": "mcp_only",
                        "verification": "none",
                    })
                self.assertEqual(blocked_workflow.exception.code, "OPERATOR_REPORT_ACK_REQUIRED")

                with self.assertRaises(ToolFailure) as wrong_ack:
                    runtime.task_control({
                        "action": "update",
                        "payload": {"extension": "operator_report_ack_v1", "report_id": "wrong"},
                    })
                self.assertEqual(wrong_ack.exception.code, "OPERATOR_REPORT_ACK_INVALID")

                with self.assertRaises(ToolFailure) as wrong_legacy_ack:
                    runtime.task_control({"action": "ack", "message_id": "wrong"})
                self.assertEqual(wrong_legacy_ack.exception.code, "MESSAGE_NOT_FOUND")

                acknowledged = runtime.task_control({"action": "ack", "message_id": report_id})
                self.assertTrue(acknowledged["acknowledged"])
                self.assertEqual(acknowledged["acknowledgement_type"], "operator_completion_report")
                self.assertIsNone(runtime.task_state.pending_completion_report())
                repeated = runtime.task_control({"action": "ack", "message_id": report_id})
                self.assertTrue(repeated["acknowledged"])
                self.assertEqual(repeated["report_id"], report_id)
                started = runtime.task_control({"action": "start", "objective": "replacement"})
                self.assertEqual(started["state"]["objective"], "replacement")
            finally:
                runtime.close()

    def test_cross_context_command_report_recovery_and_exact_ack_are_workspace_local(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            scope = ["mcp2026:session-a"]
            runtime = Runtime(root)
            runtime.task_state = ContextualTaskStateStore(root, lambda: scope[0])
            try:
                runtime.task_state.update({"objective": "Session A command", "status": "active"})
                runtime.task_state.record_command_started(
                    "git rev-parse HEAD", "command-session-a", "."
                )
                payload = {
                    "ok": True,
                    "status": "exited",
                    "command_id": "command-session-a",
                    "session_id": "command-session-a",
                    "exit_code": 0,
                    "elapsed_ms": 4,
                }
                runtime._record_task_tool_result(
                    "command_control",
                    {"action": "poll", "command_id": "command-session-a"},
                    payload,
                )
                report_id = runtime.task_state.get()["completion_report_id"]

                scope[0] = "mcp2026:session-b"
                self.assertEqual(runtime.task_state.get()["completion_report_id"], "")
                recovered = runtime.command_control(
                    {"action": "poll", "command_id": "command-session-a"}
                )
                self.assertEqual(recovered["status"], "reconciled_terminal")
                self.assertEqual(recovered["completion_report_id"], report_id)
                self.assertEqual(
                    recovered["reconciled_sources"], ["task_state_completion_report"]
                )

                acknowledged = runtime.task_control(
                    {"action": "ack", "message_id": report_id}
                )
                self.assertTrue(acknowledged["acknowledged"])
                scope[0] = "mcp2026:session-a"
                self.assertEqual(
                    runtime.task_state.get()["completion_report_acknowledged_id"],
                    report_id,
                )
            finally:
                runtime.close()

    def test_cross_context_completion_lookup_fails_closed_on_ambiguity_and_workspace_change(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            first_root = Path(first)
            second_root = Path(second)
            scope = ["mcp2026:a"]
            workspace = [first_root]
            store = ContextualTaskStateStore(
                first_root,
                lambda: scope[0],
                workspace_provider=lambda: workspace[0],
            )
            for label in ("a", "b"):
                scope[0] = f"mcp2026:{label}"
                store.update({"objective": f"Context {label}", "status": "active"})
                store.set_completion_report(
                    {
                        "operator_visible_required": True,
                        "command_id": "reused-command",
                        "accepted_or_not": f"RESULT_{label.upper()}",
                        "current_state": {},
                    }
                )

            scope[0] = "mcp2026:c"
            with self.assertRaisesRegex(ValueError, "ambiguous across task contexts"):
                store.find_command_completion("reused-command")

            workspace[0] = second_root
            self.assertIsNone(store.find_command_completion("reused-command"))
            with self.assertRaisesRegex(ValueError, "current workspace"):
                store.ack_completion_report("not-present")

    def test_eocl_task_ignores_foreign_and_unowned_command_projection(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                runtime.task_state.update({
                    "objective": "owned task",
                    "status": "active",
                    "orchestration": {
                        "orchestration_state": "EXECUTING",
                        "run_id": "run-a",
                        "wave_id": "wave-a",
                    },
                })
                runtime.task_state.record_command_started(
                    "foreign", "foreign", ".", owner_run_id="run-b", owner_wave_id="wave-b"
                )
                self.assertIsNone(runtime.task_state.get()["current_command"])
                runtime.task_state.record_command_started("unowned", "unowned", ".")
                self.assertIsNone(runtime.task_state.get()["current_command"])
                runtime.task_state.record_command_started(
                    "owned", "owned", ".", owner_run_id="run-a", owner_wave_id="wave-a"
                )
                self.assertEqual(runtime.task_state.get()["current_command"]["session_id"], "owned")

                runtime._record_task_tool_result(
                    "exec_command",
                    {"cmd": "foreign-result"},
                    {
                        "ok": True,
                        "status": "exited",
                        "exit_code": 0,
                        "session_id": "foreign-result",
                        "execution_owner": {"run_id": "run-b", "wave_id": "wave-b"},
                    },
                )
                self.assertIsNone(runtime.task_state.get()["last_command_result"])
            finally:
                runtime.close()

    def test_preinitialize_compatibility_sessions_are_same_root_but_task_isolated(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.dict(os.environ, {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
                runtime = Runtime(root, transport="http")
            server = RuntimeHTTPServer(("127.0.0.1", 0), MCPHandler, runtime, runtime_factory=None)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            port = int(server.server_address[1])
            try:
                status, headers_a, body_a = self._post(port, {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
                self.assertEqual(status, 200, body_a)
                status, headers_b, body_b = self._post(port, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
                self.assertEqual(status, 200, body_b)
                session_a = headers_a.get("mcp-session-id", "")
                session_b = headers_b.get("mcp-session-id", "")
                self.assertTrue(session_a.startswith("ws1."), session_a)
                self.assertTrue(session_b.startswith("ws1."), session_b)
                self.assertNotEqual(session_a, session_b)
                self.assertEqual(server.sessions.stats()["execution_contexts"], 2)

                result_a = self._prepare(port, session_a, 3, "compat-a")
                result_b = self._prepare(port, session_b, 4, "compat-b")
                self.assertNotEqual(result_a["orchestration"]["run_id"], result_b["orchestration"]["run_id"])
                state_a = self._task_get(port, session_a, 5)
                state_b = self._task_get(port, session_b, 6)
                self.assertEqual(state_a["objective"], "compat-a")
                self.assertEqual(state_b["objective"], "compat-b")
                self.assertNotEqual(state_a["task_id"], state_b["task_id"])
                self.assertEqual(len(runtime.exposed_tool_names()), 8)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
                self.assertFalse(thread.is_alive())

    @staticmethod
    def _post(port: int, payload: dict, *, session_id: str = "") -> tuple[int, dict[str, str], dict]:
        headers = {"Content-Type": "application/json"}
        if session_id:
            headers["Mcp-Session-Id"] = session_id
            headers["MCP-Protocol-Version"] = PROTOCOL_VERSION
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        try:
            connection.request("POST", "/mcp", body=json.dumps(payload).encode("utf-8"), headers=headers)
            response = connection.getresponse()
            raw = response.read()
            body = json.loads(raw.decode("utf-8")) if raw else {}
            return response.status, {key.lower(): value for key, value in response.getheaders()}, body
        finally:
            connection.close()

    def _prepare(self, port: int, session_id: str, request_id: int, objective: str) -> dict:
        status, _headers, body = self._post(
            port,
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/call",
                "params": {
                    "name": "agent_workflow",
                    "arguments": {
                        "workflow": "diagnose",
                        "phase": "prepare",
                        "objective": objective,
                        "execution_route": "deterministic",
                        "execution_mode": "mcp_only",
                        "verification": "none",
                    },
                },
            },
            session_id=session_id,
        )
        self.assertEqual(status, 200, body)
        self.assertFalse(body["result"]["isError"], body)
        return body["result"]["structuredContent"]

    def _task_get(self, port: int, session_id: str, request_id: int) -> dict:
        status, _headers, body = self._post(
            port,
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/call",
                "params": {"name": "task_control", "arguments": {"action": "get"}},
            },
            session_id=session_id,
        )
        self.assertEqual(status, 200, body)
        self.assertFalse(body["result"]["isError"], body)
        return body["result"]["structuredContent"]["state"]


if __name__ == "__main__":
    unittest.main()
