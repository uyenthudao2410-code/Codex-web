from __future__ import annotations

import hashlib
import io
import json
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from control_plane.node_agent import (
    _admit_document_write_policy_request,
    _document_write_bridge_request,
    _document_write_journal_path,
    _document_write_projection_digest,
    _install_approved_patch_policy_values,
    _read_document_write_journal,
    _record_document_write_receipt,
    _recover_document_write_prepared_entry,
    _safe_document_write_bridge_result,
    _policy_digest,
    _write_json_atomic,
    poll_document_write_once,
)


FACADE_CONTRACT = {
    "schema_version": 24,
    "profile": "control-plane-oauth-standing-document-write-v1",
    "sha256": "f" * 64,
}


class DocumentWriteNodeAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="control-plane-document-write-node-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.config_path = self.directory / "node.json"
        self.registry_path = self.directory / "workspace-registry.json"
        self.data_root = self.directory / "data"
        self.root = self.directory / "workspace"
        (self.root / "docs").mkdir(parents=True)
        (self.root / "input.md").write_text("# input\n", encoding="utf-8")
        self.config = {
            "server_url": "https://control.example.test",
            "device_id": "device-control-plane-0001",
            "endpoint_id": "endpoint-control-plane-0001",
            "node_secret": "node-secret-not-printed",
        }
        self.config_path.write_text(json.dumps(self.config), encoding="utf-8")
        self.registry_path.write_text(json.dumps({
            "schema_version": 1,
            "entries": [{
                "workspace_id": "workspace-control-plane-0001",
                "workspace_generation": "generation-control-plane-0001",
                "canonical_path": str(self.root.resolve()),
                "display_name": "Fixture workspace",
                "capabilities": {"read": True, "write": True, "exec": False},
                "created_at_ms": 1_700_000_000_000,
            }],
        }), encoding="utf-8")

    def args(self) -> SimpleNamespace:
        return SimpleNamespace(
            config=str(self.config_path),
            workspace_registry=str(self.registry_path),
            data_root=str(self.data_root),
            project_root=str(Path.cwd()),
            node="node",
            runtime_mode="development",
            timeout_seconds=20,
            replace=True,
        )

    def install_policy(self, *, write: bool = True, generation: str = "generation-control-plane-0001") -> dict[str, object]:
        registry = json.loads(self.registry_path.read_text(encoding="utf-8"))
        registry["entries"][0]["capabilities"]["write"] = write
        registry["entries"][0]["workspace_generation"] = generation
        self.registry_path.write_text(json.dumps(registry), encoding="utf-8")
        return _install_approved_patch_policy_values(
            self.args(),
            config_path=self.config_path,
            config=self.config,
            owner_id="owner-control-plane-0001",
            workspace_id="workspace-control-plane-0001",
            workspace_generation=generation,
            expires_at_ms=None,
            facade_contract=FACADE_CONTRACT,
            allowed_relative_paths=["docs/result.md", "docs/result.docx", "input.md"],
            max_patch_bytes=4096,
            max_file_bytes=4096,
        )

    def action(self, *, operation: str = "document_create", content: str = "created\n", target: str | None = None,
               source: str | None = None, overwrite: bool = False, generation: str = "generation-control-plane-0001") -> dict[str, object]:
        if target is None:
            target = "docs/result.docx" if operation == "document_convert" else "docs/result.md"
        if operation == "document_convert" and source is None:
            source = "input.md"
        intent_digest = "d" * 64
        arguments = {
            "operation": operation,
            "authority_mode": "standing",
            "target": target,
            "source": source,
            "title": "Node document test",
            "content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            "overwrite": overwrite,
        }
        return {
            "action_id": "action-document-write-0001",
            "attempt_id": "attempt-document-write-0001",
            "owner_id": "owner-control-plane-0001",
            "device_id": "device-control-plane-0001",
            "endpoint_id": "endpoint-control-plane-0001",
            "workspace_id": "workspace-control-plane-0001",
            "workspace_generation": generation,
            "context_id": "context-document-write-0001",
            "binding_id": "binding-document-write-0001",
            "mcp_task_id": "task_" + "a" * 32,
            "writer_lease_generation": 1,
            "tool_name": "document_workflow",
            "arguments_json": json.dumps(arguments, separators=(",", ":")),
            "mcp_document_write_operation": operation,
            "mcp_document_write_target_path": target,
            "mcp_document_write_source_path": source,
            "mcp_document_write_title": "Node document test",
            "mcp_document_write_content": content,
            "mcp_document_write_overwrite": overwrite,
            "mcp_document_write_intent_digest": intent_digest,
            "mcp_document_write_facade_schema_version": FACADE_CONTRACT["schema_version"],
            "mcp_document_write_facade_profile": FACADE_CONTRACT["profile"],
            "mcp_document_write_facade_contract_sha256": FACADE_CONTRACT["sha256"],
            "admission_reference": "mcp_document_write:" + intent_digest,
            "expires_at_ms": int(time.time() * 1000) + 60_000,
        }

    def test_action_rebuild_and_local_policy_admission_cover_create_convert(self) -> None:
        policy = self.install_policy()
        for operation in ("document_create", "document_convert"):
            action = self.action(operation=operation)
            request = _document_write_bridge_request(action, self.config)
            admitted, entry = _admit_document_write_policy_request(
                self.args(), config_path=self.config_path, config=self.config, request=request
            )
            self.assertEqual(admitted["workspace_generation"], "generation-control-plane-0001")
            self.assertEqual(entry["capabilities"]["write"], True)
            self.assertEqual(request["operation"], operation)
            self.assertEqual(request["source"], None if operation == "document_create" else "input.md")
            self.assertEqual(request["facade_contract"], FACADE_CONTRACT)
        self.assertEqual(policy["authority_mode"], "standing")

    def test_action_rejects_tampered_content_hash_and_stale_generation(self) -> None:
        self.install_policy()
        action = self.action()
        action["mcp_document_write_content"] = "tampered\n"
        with self.assertRaisesRegex(RuntimeError, "CONTROL_PLANE_DOCUMENT_WRITE_ACTION_DENIED"):
            _document_write_bridge_request(action, self.config)

        stale = self.action(generation="generation-stale-0001")
        request = _document_write_bridge_request(stale, self.config)
        with self.assertRaisesRegex(RuntimeError, "CONTROL_PLANE_DOCUMENT_WRITE_TARGET_MISMATCH"):
            _admit_document_write_policy_request(
                self.args(), config_path=self.config_path, config=self.config, request=request
            )

    def test_missing_local_write_capability_rejects_before_bridge(self) -> None:
        self.install_policy(write=True)
        registry = json.loads(self.registry_path.read_text(encoding="utf-8"))
        registry["entries"][0]["capabilities"]["write"] = False
        self.registry_path.write_text(json.dumps(registry), encoding="utf-8")
        request = _document_write_bridge_request(self.action(), self.config)
        with self.assertRaisesRegex(RuntimeError, "CONTROL_PLANE_WORKSPACE_REGISTRATION_NOT_CURRENT"):
            _admit_document_write_policy_request(
                self.args(), config_path=self.config_path, config=self.config, request=request
            )

    def test_result_validator_is_digest_only_and_strict(self) -> None:
        policy = self.install_policy()
        request = _document_write_bridge_request(self.action(), self.config)
        _admitted_policy, _entry = _admit_document_write_policy_request(
            self.args(), config_path=self.config_path, config=self.config, request=request
        )
        request = {**request, "policy_sha256": _policy_digest(policy)}
        safe_result = {
            "operation": request["operation"],
            "target": request["target"],
            "source": request["source"],
            "size": 8,
            "sha256": "1" * 64,
            "format": "md",
        }
        value = {
            "schema_version": 1,
            "operation_kind": "control_plane_document_write",
            "local_handle": "cp_doc_" + "e" * 48,
            "action_id": request["action_id"],
            "attempt_id": request["attempt_id"],
            "task_id": request["task_id"],
            "writer_lease_generation": request["writer_lease_generation"],
            "operation": request["operation"],
            "target": request["target"],
            "source": request["source"],
            "result": safe_result,
            "actor": {"client_id": "electron-control-plane-document-bridge", "client_type": "electron"},
            "policy_sha256": request["policy_sha256"],
            "facade_contract": request["facade_contract"],
            "runtime_identity": {
                "activation_epoch_id": "activation-document-write-0001",
                "process_instance_id": "process-document-write-0001",
                "server_instance_id": "server-document-write-0001",
                "tool_contract_sha256": "2" * 64,
            },
            "response_sha256": _document_write_projection_digest(safe_result),
        }
        normalized = _safe_document_write_bridge_result(
            value, request, expected_policy_sha256=request["policy_sha256"]
        )
        self.assertEqual(normalized["result"], safe_result)
        self.assertNotIn(str(self.root), json.dumps(normalized))
        value["result"] = {**safe_result, "target": "C:/private/result.md"}
        with self.assertRaisesRegex(RuntimeError, "CONTROL_PLANE_DOCUMENT_WRITE_RESULT_INVALID"):
            _safe_document_write_bridge_result(value, request, expected_policy_sha256=request["policy_sha256"])

    def test_prepared_journal_becomes_unknown_and_replays_receipt_only(self) -> None:
        journal_path = _document_write_journal_path(self.config_path)
        journal = _read_document_write_journal(journal_path)
        entry = _record_document_write_receipt(
            journal_path,
            journal,
            state="prepared",
            action_id="action-document-write-0001",
            attempt_id="attempt-document-write-0001",
            receipt_state="prepared",
            local_handle="",
            payload={"operation_kind": "control_plane_document_write"},
        )
        _recover_document_write_prepared_entry(entry)
        journal["entries"]["action-document-write-0001|attempt-document-write-0001"] = entry
        _write_json_atomic(journal_path, journal)
        self.assertEqual(entry["state"], "unknown")
        self.assertEqual(entry["receipt"]["receipt_state"], "unknown")
        self.assertTrue(entry["receipt"]["payload"]["reconciliation_required"])
        self.assertEqual(entry["receipt"]["payload"]["code"], "CONTROL_PLANE_DOCUMENT_WRITE_EFFECT_UNKNOWN")

        def submit_receipt(_config: dict[str, object], value: dict[str, object]) -> dict[str, bool]:
            value["receipt"]["receipt_submitted"] = True  # type: ignore[index]
            return {"accepted": True}

        with mock.patch("control_plane.node_agent._submit_receipt", side_effect=submit_receipt) as submit:
            from control_plane.node_agent import _flush_document_write_journal
            loaded = _read_document_write_journal(journal_path)
            _flush_document_write_journal(self.config, journal_path, loaded)
            self.assertEqual(submit.call_count, 1)
            _flush_document_write_journal(self.config, journal_path, loaded)
            self.assertEqual(submit.call_count, 1)

    def _assert_bridge_rejection_receipt(self, code: str, state: str) -> dict[str, object]:
        self.install_policy()
        action = self.action()
        receipts: list[dict[str, object]] = []

        def request(_url: str, path: str, payload: dict[str, object], _authorization: str | None = None) -> dict[str, object]:
            if path.endswith("/poll"):
                self.assertEqual(payload, {"limit": 1, "lane": "document_write"})
                return {"actions": [action]}
            self.assertTrue(path.endswith("/receipts"))
            receipts.append(payload)
            return {"receipt_id": "receipt-document-write-rejection-0001"}

        status = {
            "state": "CURRENT", "host": "available", "installation": "current",
            "mcp_update_pending": "false", "mcp_running_revision": "sha-current",
            "mcp_disk_revision": "sha-current", "components_ready": "true",
            "fully_ready": "true", "runtime_update_incomplete": "false",
            "runtime_telemetry_available": "true", "runtime_signal_stale": "false",
            "connector_state": "CURRENT_ACKNOWLEDGED", "connector_rediscovered": "true",
            "connector_rediscovered_at": "2026-10-12T00:00:00Z",
            "connector_freshness_mode": "current_process_discovery",
            "connector_refresh_required": "false", "connector_ack_pending": "false",
            "connector_current_sha": "sha-current", "connector_ack_sha": "sha-current",
            "error_code": "none",
        }
        identity = {
            "observation_schema_version": 1, "observation_kind": "mcp_identity_read_only",
            "mcp_ready": True, "identity_current": True,
            "mcp_process_instance_id": "process-document-write-0001",
            "mcp_server_instance_id": "server-document-write-0001",
            "activation_epoch_id": "activation-document-write-0001",
            "current_activation_epoch_id": "activation-document-write-0001",
            "tool_contract_sha256": "a" * 64,
        }
        output = io.StringIO()
        with mock.patch("control_plane.node_agent._request", side_effect=request), \
             mock.patch("control_plane.node_agent._runtime_status", return_value=status), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=identity), \
             mock.patch("control_plane.node_agent.recovery_document_write_bridge", return_value=(None, code)) as bridge, \
             redirect_stdout(output):
            self.assertEqual(poll_document_write_once(self.args()), 0)
            # Re-delivery may only observe the durable receipt, never call the
            # document mutation bridge again.
            self.assertEqual(poll_document_write_once(self.args()), 0)

        bridge.assert_called_once()
        self.assertEqual(len(receipts), 1)
        self.assertEqual(receipts[0]["receipt_state"], state)
        self.assertEqual(receipts[0]["local_handle"], "")
        observation = json.loads(output.getvalue().splitlines()[0])
        self.assertEqual(observation[f"{state}_action_ids"], [action["action_id"]])
        self.assertEqual(observation["unknown_action_ids" if state == "rejected" else "rejected_action_ids"], [])
        saved = _read_document_write_journal(_document_write_journal_path(self.config_path))["entries"][
            f"{action['action_id']}|{action['attempt_id']}"
        ]
        self.assertEqual(saved["state"], state)
        self.assertEqual(saved["receipt"]["payload"], receipts[0]["payload"])
        self.assertTrue(saved["receipt"]["receipt_submitted"])
        self.assertFalse((self.root / "docs/result.md").exists())
        return receipts[0]["payload"]

    def test_bind_rejection_is_terminal_before_document_effect(self) -> None:
        payload = self._assert_bridge_rejection_receipt("CONTROL_PLANE_DOCUMENT_WRITE_BIND_REJECTED", "rejected")
        self.assertEqual(payload, {
            "schema_version": 1, "operation_kind": "control_plane_document_write",
            "code": "CONTROL_PLANE_DOCUMENT_WRITE_BIND_REJECTED",
        })

    def test_mcp_rejection_keeps_unknown_document_effect(self) -> None:
        payload = self._assert_bridge_rejection_receipt("CONTROL_PLANE_DOCUMENT_WRITE_MCP_REJECTED", "unknown")
        self.assertEqual(payload, {
            "schema_version": 1, "operation_kind": "control_plane_document_write",
            "code": "CONTROL_PLANE_DOCUMENT_WRITE_EFFECT_UNKNOWN",
            "diagnostic_code": "CONTROL_PLANE_DOCUMENT_WRITE_MCP_REJECTED",
            "reconciliation_required": True,
        })


if __name__ == "__main__":
    unittest.main()
