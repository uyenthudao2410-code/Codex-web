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
        },
        "reconciled": True,
        "completed_at_unix_ms": NOW_MS,
    }
    values.update(overrides)
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
                projection={"run_id": "", "wave_id": "", "orchestration_state": ""},
                reconciled=True,
            )
            idle_result = validate_projection_rebuild_receipt(idle, now_unix_ms=NOW_MS)
            self.assertTrue(idle_result["valid"])
            self.assertEqual(idle_result["projection_classification"], "NO_ACTIVE_PROJECTION")

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
            bootstrap.orchestration_ledger.create_wave(run_id, execution_mode="mcp_only")
            bootstrap.orchestration_ledger.append_event(run_id, event_type="state", state_after="PROVING")
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


if __name__ == "__main__":
    unittest.main()
