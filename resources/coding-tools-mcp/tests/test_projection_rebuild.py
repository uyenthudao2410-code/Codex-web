from __future__ import annotations

import http.client
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.projection_rebuild import (
    PROJECTION_REBUILD_MAX_AGE_MS,
    build_projection_rebuild_receipt,
    canonical_sha256,
    validate_projection_rebuild_receipt,
)
from coding_tools_mcp.server import MCPHandler, Runtime, RuntimeHTTPServer
from coding_tools_mcp.task_state import TaskStateStore


NOW_MS = 1_800_000_000_000
EPOCH_ID = "activation-epoch-projection-0001"
PROCESS_ID = "process-projection-0001"
SERVER_ID = "server-projection-0001"


def _snapshot() -> dict[str, object]:
    return {
        "backup_api_copy": True,
        "immutable": True,
        "query_only": True,
        "integrity_check": ["ok"],
        "foreign_key_check_rows": 0,
        "sha256": "a" * 64,
        "logical_sha256": "b" * 64,
    }


def _receipt(root: Path, **overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "activation_epoch_id": EPOCH_ID,
        "process_instance_id": PROCESS_ID,
        "server_instance_id": SERVER_ID,
        "workspace": root,
        "ledger_snapshot": _snapshot(),
        "projection_classification": "CHECKPOINTED",
        "projection": {
            "run_id": "run-projection-0001",
            "wave_id": "wave-projection-0001",
            "orchestration_state": "CHECKPOINTED",
            "mode": "global",
            "context_count": 0,
            "contextual_sha256": "",
        },
        "reconciled": True,
        "completed_at_unix_ms": NOW_MS,
    }
    values.update(overrides)
    values["projection"] = {
        "run_id": "run-projection-0001",
        "wave_id": "wave-projection-0001",
        "orchestration_state": "CHECKPOINTED",
        "mode": "global",
        "context_count": 0,
        "contextual_sha256": "",
        **dict(overrides.get("projection") or {}),
    }
    return build_projection_rebuild_receipt(**values)


class ProjectionRebuildReceiptTests(unittest.TestCase):
    def test_matching_current_receipt_is_valid_and_no_active_projection_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            receipt = _receipt(root)
            result = validate_projection_rebuild_receipt(
                receipt,
                activation_epoch_id=EPOCH_ID,
                process_instance_id=PROCESS_ID,
                server_instance_id=SERVER_ID,
                workspace=root,
                ledger_snapshot=_snapshot(),
                process_started_at_unix_ms=NOW_MS - 1,
                epoch_started_at_unix_ms=NOW_MS - 1,
                now_unix_ms=NOW_MS,
            )
            self.assertTrue(result["valid"])
            self.assertEqual(result["code"], "READY")

            idle = _receipt(
                root,
                projection_classification="NO_ACTIVE_PROJECTION",
                projection={"run_id": "", "wave_id": "", "orchestration_state": "", "mode": "global"},
                reconciled=True,
            )
            idle_result = validate_projection_rebuild_receipt(idle, now_unix_ms=NOW_MS)
            self.assertTrue(idle_result["valid"])
            self.assertEqual(idle_result["projection_classification"], "NO_ACTIVE_PROJECTION")

            contextual = _receipt(
                root,
                projection_classification="CONTEXTUAL_PROJECTIONS",
                projection={
                    "run_id": "",
                    "wave_id": "",
                    "orchestration_state": "",
                    "mode": "contextual",
                    "context_count": 2,
                    "contextual_sha256": "c" * 64,
                },
            )
            contextual_result = validate_projection_rebuild_receipt(contextual, now_unix_ms=NOW_MS)
            self.assertTrue(contextual_result["valid"])
            self.assertEqual(contextual_result["projection_classification"], "CONTEXTUAL_PROJECTIONS")

    def test_identity_workspace_and_ledger_mismatches_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as other:
            root = Path(temp)
            receipt = _receipt(root)
            cases = (
                ({"activation_epoch_id": "another-activation-epoch"}, "ACTIVATION_EPOCH_ID_MISMATCH"),
                ({"process_instance_id": "another-process"}, "PROCESS_INSTANCE_ID_MISMATCH"),
                ({"server_instance_id": "another-server"}, "SERVER_INSTANCE_ID_MISMATCH"),
                ({"workspace": Path(other)}, "WORKSPACE_MISMATCH"),
                ({"ledger_snapshot": {**_snapshot(), "sha256": "c" * 64}}, "LEDGER_SNAPSHOT_SHA256_MISMATCH"),
                ({"ledger_snapshot": {**_snapshot(), "logical_sha256": "d" * 64}}, "LEDGER_LOGICAL_SHA256_MISMATCH"),
            )
            for expected, reason in cases:
                with self.subTest(reason=reason):
                    result = validate_projection_rebuild_receipt(
                        receipt,
                        now_unix_ms=NOW_MS,
                        **expected,
                    )
                    self.assertFalse(result["valid"])
                    self.assertEqual(result["code"], "UPDATE_INCOMPLETE")
                    self.assertIn(reason, result["reasons"])

    def test_missing_receipt_and_receipt_before_current_process_fail_closed(self) -> None:
        missing = validate_projection_rebuild_receipt(None, now_unix_ms=NOW_MS)
        self.assertFalse(missing["valid"])
        self.assertEqual(missing["reasons"], ["RECEIPT_MISSING"])
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            receipt = _receipt(root)
            before_process = validate_projection_rebuild_receipt(
                receipt,
                process_started_at_unix_ms=NOW_MS + 1,
                now_unix_ms=NOW_MS + 1,
            )
            self.assertIn("RECEIPT_PRECEDES_PROCESS", before_process["reasons"])
            with self.assertRaises(ValueError):
                _receipt(root, reconciled=False)

    def test_drift_stale_future_and_integrity_tampering_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaises(ValueError):
                _receipt(root, projection_classification="PROJECTION_DRIFT")

            stale = _receipt(root, completed_at_unix_ms=NOW_MS - PROJECTION_REBUILD_MAX_AGE_MS - 1)
            self.assertIn(
                "RECEIPT_STALE",
                validate_projection_rebuild_receipt(stale, now_unix_ms=NOW_MS)["reasons"],
            )
            future = _receipt(root, completed_at_unix_ms=NOW_MS + 2_000)
            self.assertIn(
                "RECEIPT_FROM_FUTURE",
                validate_projection_rebuild_receipt(future, now_unix_ms=NOW_MS)["reasons"],
            )

            tampered = dict(_receipt(root))
            tampered["process_instance_id"] = "tampered-process"
            self.assertIn(
                "RECEIPT_INTEGRITY_INVALID",
                validate_projection_rebuild_receipt(tampered, now_unix_ms=NOW_MS)["reasons"],
            )
            extended = dict(_receipt(root))
            extended["unexpected"] = True
            extended["integrity_sha256"] = canonical_sha256({
                key: value for key, value in extended.items() if key != "integrity_sha256"
            })
            self.assertIn(
                "RECEIPT_FIELDS_INVALID",
                validate_projection_rebuild_receipt(extended, now_unix_ms=NOW_MS)["reasons"],
            )

    def test_runtime_builds_current_receipt_and_authenticated_health_exposes_it(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            environment = {
                "CODING_TOOLS_MCP_ACTIVATION_EPOCH_ID": EPOCH_ID,
                "CODING_TOOLS_MCP_ACTIVATION_GATE": "closed",
                "CODING_TOOLS_MCP_ACTIVATION_EXPIRES_AT_UNIX_MS": str(NOW_MS + 60_000),
            }
            with patch.dict(os.environ, environment, clear=False):
                runtime = Runtime(root, auth_token="projection-token")
            server = RuntimeHTTPServer(("127.0.0.1", 0), MCPHandler, runtime, runtime_factory=None)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                rebuild = runtime.projection_rebuild_snapshot()
                self.assertTrue(rebuild["current"])
                receipt = rebuild["receipt"]
                self.assertEqual(receipt["activation_epoch_id"], EPOCH_ID)
                self.assertEqual(receipt["process_instance_id"], runtime.process_instance_id)
                self.assertEqual(receipt["server_instance_id"], runtime.server_instance_id)
                self.assertEqual(receipt["projection_classification"], "NO_ACTIVE_PROJECTION")

                connection = http.client.HTTPConnection("127.0.0.1", int(server.server_address[1]), timeout=5)
                connection.request("GET", "/__control/health", headers={
                    "Authorization": "Bearer projection-token",
                })
                response = connection.getresponse()
                health = json.loads(response.read())
                connection.close()
                self.assertEqual(response.status, 200)
                self.assertTrue(health["projection_rebuild"]["current"])
                self.assertEqual(health["projection_rebuild"]["receipt"], receipt)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
                runtime.close()

    def test_runtime_materializes_missing_projection_before_minting_idle_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_path = root / ".coding-tools" / "task-state.json"
            environment = {
                "CODING_TOOLS_MCP_ACTIVATION_EPOCH_ID": EPOCH_ID,
                "CODING_TOOLS_MCP_ACTIVATION_GATE": "closed",
                "CODING_TOOLS_MCP_ACTIVATION_EXPIRES_AT_UNIX_MS": str(NOW_MS + 60_000),
            }
            self.assertFalse(state_path.exists())
            with patch.dict(os.environ, environment, clear=False):
                runtime = Runtime(root, auth_token="projection-token")
            try:
                self.assertTrue(state_path.is_file())
                rebuild = runtime.projection_rebuild_snapshot()
                self.assertTrue(rebuild["current"])
                self.assertEqual(rebuild["receipt"]["projection_classification"], "NO_ACTIVE_PROJECTION")
            finally:
                runtime.close()

    def test_runtime_does_not_mint_idle_receipt_when_projection_is_unavailable_for_active_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bootstrap = Runtime(root, auth_token="projection-token")
            run_id = bootstrap.orchestration_ledger.create_run(objective="projection-active-task")
            wave_id = bootstrap.orchestration_ledger.create_wave(run_id, execution_mode="mcp_only")
            bootstrap.orchestration_ledger.append_event(
                run_id,
                wave_id=wave_id,
                event_type="state",
                state_after="PROVING",
            )
            bootstrap.close()
            state_path = root / ".coding-tools" / "task-state.json"
            state_path.write_text("{not-json", encoding="utf-8")
            environment = {
                "CODING_TOOLS_MCP_ACTIVATION_EPOCH_ID": EPOCH_ID,
                "CODING_TOOLS_MCP_ACTIVATION_GATE": "closed",
                "CODING_TOOLS_MCP_ACTIVATION_EXPIRES_AT_UNIX_MS": str(NOW_MS + 60_000),
            }
            with patch.dict(os.environ, environment, clear=False):
                runtime = Runtime(root, auth_token="projection-token")
            try:
                rebuild = runtime.projection_rebuild_snapshot()
                self.assertFalse(rebuild["current"])
                self.assertIsNone(rebuild["receipt"])
                self.assertEqual(rebuild["validation"]["code"], "UPDATE_INCOMPLETE")
                self.assertIn("PROJECTION_REBUILD_FAILED", rebuild["validation"]["reasons"])
            finally:
                runtime.close()

    def test_runtime_restores_missing_global_projection_from_one_exact_active_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bootstrap = Runtime(root, auth_token="projection-token")
            run_id = bootstrap.orchestration_ledger.create_run(
                objective="restore exact projection",
                task_id="task-projection-restore-0001",
            )
            wave_id = bootstrap.orchestration_ledger.create_wave(run_id, execution_mode="mcp_only")
            bootstrap.orchestration_ledger.append_event(
                run_id,
                wave_id=wave_id,
                event_type="state",
                state_after="PROVING",
            )
            bootstrap.close()
            state_path = root / ".coding-tools" / "task-state.json"
            self.assertFalse(state_path.exists())
            environment = {
                "CODING_TOOLS_MCP_ACTIVATION_EPOCH_ID": EPOCH_ID,
                "CODING_TOOLS_MCP_ACTIVATION_GATE": "closed",
                "CODING_TOOLS_MCP_ACTIVATION_EXPIRES_AT_UNIX_MS": str(NOW_MS + 60_000),
            }
            with patch.dict(os.environ, environment, clear=False):
                runtime = Runtime(root, auth_token="projection-token")
            try:
                state = runtime.task_state.get()
                self.assertEqual(state["task_id"], "task-projection-restore-0001")
                self.assertEqual(state["objective"], "restore exact projection")
                self.assertEqual(state["orchestration"]["run_id"], run_id)
                self.assertEqual(state["orchestration"]["wave_id"], wave_id)
                rebuild = runtime.projection_rebuild_snapshot()
                self.assertTrue(rebuild["current"])
                self.assertEqual(rebuild["receipt"]["projection_classification"], "PROJECTION_CONSISTENT")
                self.assertEqual(rebuild["receipt"]["projection"]["mode"], "global")
            finally:
                runtime.close()

    def test_runtime_refuses_to_select_between_multiple_unscoped_active_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bootstrap = Runtime(root, auth_token="projection-token")
            for index in range(2):
                run_id = bootstrap.orchestration_ledger.create_run(
                    objective=f"ambiguous projection {index}",
                    task_id=f"task-ambiguous-{index}",
                )
                bootstrap.orchestration_ledger.create_wave(run_id, execution_mode="mcp_only")
                bootstrap.orchestration_ledger.append_event(run_id, event_type="state", state_after="PROVING")
            bootstrap.close()
            environment = {
                "CODING_TOOLS_MCP_ACTIVATION_EPOCH_ID": EPOCH_ID,
                "CODING_TOOLS_MCP_ACTIVATION_GATE": "closed",
                "CODING_TOOLS_MCP_ACTIVATION_EXPIRES_AT_UNIX_MS": str(NOW_MS + 60_000),
            }
            with patch.dict(os.environ, environment, clear=False):
                runtime = Runtime(root, auth_token="projection-token")
            try:
                self.assertFalse((root / ".coding-tools" / "task-state.json").exists())
                rebuild = runtime.projection_rebuild_snapshot()
                self.assertFalse(rebuild["current"])
                self.assertIn("PROJECTION_REBUILD_FAILED", rebuild["validation"]["reasons"])
            finally:
                runtime.close()

    def test_runtime_accepts_exact_contextual_projection_set_without_global_selection(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bootstrap = Runtime(root, auth_token="projection-token")
            # A cold runtime must also rebuild its receipt when an old pending
            # acceptance has no current context, without accepting that RUN.
            with patch("coding_tools_mcp.orchestration_ledger.utc_now", return_value="2000-01-01T00:00:00.000Z"):
                historical_run = bootstrap.orchestration_ledger.create_run(objective="historical acceptance")
                historical_wave = bootstrap.orchestration_ledger.create_wave(historical_run, execution_mode="mcp_only")
                bootstrap.orchestration_ledger.append_event(
                    historical_run, wave_id=historical_wave, event_type="state", state_after="ACCEPTING",
                )
            historical_events = bootstrap.orchestration_ledger.list_events(historical_run)
            run_ids: list[tuple[str, str, str]] = []
            for index, state in enumerate(("ACCEPTING", "PROVING")):
                task_id = f"task-contextual-{index}"
                run_id = bootstrap.orchestration_ledger.create_run(
                    objective=f"contextual projection {index}",
                    task_id=task_id,
                )
                wave_id = bootstrap.orchestration_ledger.create_wave(run_id, execution_mode="mcp_only")
                bootstrap.orchestration_ledger.append_event(run_id, event_type="state", state_after=state)
                run_ids.append((run_id, wave_id, state))
                store = TaskStateStore(root, scope_id=f"contextual-scope-{index}")
                store.ensure_started(f"contextual projection {index}")
                store.set_orchestration_projection({
                    "run_id": run_id,
                    "wave_id": wave_id,
                    "orchestration_state": state,
                })
            bootstrap.close()
            environment = {
                "CODING_TOOLS_MCP_ACTIVATION_EPOCH_ID": EPOCH_ID,
                "CODING_TOOLS_MCP_ACTIVATION_GATE": "closed",
                "CODING_TOOLS_MCP_ACTIVATION_EXPIRES_AT_UNIX_MS": str(NOW_MS + 60_000),
                "CODING_TOOLS_MCP_ACTIVATION_ALLOW_ACCEPTANCE_PENDING": "true",
            }
            with patch.dict(os.environ, environment, clear=False):
                runtime = Runtime(root, auth_token="projection-token")
            try:
                self.assertFalse((root / ".coding-tools" / "task-state.json").exists())
                rebuild = runtime.projection_rebuild_snapshot()
                self.assertTrue(rebuild["current"], rebuild["validation"])
                receipt = rebuild["receipt"]
                self.assertEqual(receipt["projection_classification"], "CONTEXTUAL_PROJECTIONS")
                self.assertEqual(receipt["projection"]["mode"], "contextual")
                self.assertEqual(receipt["projection"]["context_count"], 2)
                self.assertEqual(len(receipt["projection"]["contextual_sha256"]), 64)
                self.assertEqual(runtime.orchestration_ledger.get_run(historical_run)["status"], "active")
                self.assertEqual(runtime.orchestration_ledger.list_events(historical_run), historical_events)
            finally:
                runtime.close()

    def test_runtime_rejects_contextual_set_missing_a_current_acceptance_projection(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bootstrap = Runtime(root, auth_token="projection-token")
            accepting_run = bootstrap.orchestration_ledger.create_run(
                objective="missing acceptance projection",
                task_id="task-contextual-missing-acceptance",
            )
            bootstrap.orchestration_ledger.create_wave(accepting_run, execution_mode="mcp_only")
            bootstrap.orchestration_ledger.append_event(accepting_run, event_type="state", state_after="ACCEPTING")
            proving_run = bootstrap.orchestration_ledger.create_run(
                objective="present proving projection",
                task_id="task-contextual-present-proving",
            )
            proving_wave = bootstrap.orchestration_ledger.create_wave(proving_run, execution_mode="mcp_only")
            bootstrap.orchestration_ledger.append_event(proving_run, event_type="state", state_after="PROVING")
            store = TaskStateStore(root, scope_id="contextual-present-scope")
            store.ensure_started("present proving projection")
            store.set_orchestration_projection({
                "run_id": proving_run,
                "wave_id": proving_wave,
                "orchestration_state": "PROVING",
            })
            bootstrap.close()
            environment = {
                "CODING_TOOLS_MCP_ACTIVATION_EPOCH_ID": EPOCH_ID,
                "CODING_TOOLS_MCP_ACTIVATION_GATE": "closed",
                "CODING_TOOLS_MCP_ACTIVATION_EXPIRES_AT_UNIX_MS": str(NOW_MS + 60_000),
                "CODING_TOOLS_MCP_ACTIVATION_ALLOW_ACCEPTANCE_PENDING": "true",
            }
            with patch.dict(os.environ, environment, clear=False):
                runtime = Runtime(root, auth_token="projection-token")
            try:
                rebuild = runtime.projection_rebuild_snapshot()
                self.assertFalse(rebuild["current"])
                self.assertIn("PROJECTION_REBUILD_FAILED", rebuild["validation"]["reasons"])
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
