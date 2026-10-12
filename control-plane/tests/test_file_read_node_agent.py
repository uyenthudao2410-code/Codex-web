from __future__ import annotations

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
    FILE_READ_JOURNAL_SCHEMA_VERSION,
    _admit_file_read_policy_request,
    _disable_matching_retired_workspace_file_read_policy,
    _file_read_bridge_request,
    _file_read_journal_path,
    _install_file_read_policy_values,
    _install_read_only_policy_values,
    _policy_digest,
    _read_file_read_journal,
    _read_file_read_policy,
    _write_json_atomic,
    main as node_agent_main,
    inspect_file_read_policy,
    poll_artifact_once,
    poll_file_read_once,
)


FACADE_CONTRACT = {
    "schema_version": 8,
    "profile": "control-plane-oauth-bounded-file-read-v1",
    "sha256": "f" * 64,
}


class FileReadNodeAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="control-plane-file-read-node-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.config_path = self.directory / "node.json"
        self.registry_path = self.directory / "workspace-registry.json"
        self.data_root = self.directory / "data"
        self.root = self.directory / "workspace"
        self.root.mkdir()
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
                "capabilities": {"read": True, "write": False, "exec": False},
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
        )

    @staticmethod
    def strict_status() -> dict[str, str]:
        return {
            "state": "CURRENT", "host": "available", "installation": "current",
            "mcp_update_pending": "false", "mcp_running_revision": "sha-current",
            "mcp_disk_revision": "sha-current", "components_ready": "true",
            "fully_ready": "true", "runtime_update_incomplete": "false",
            "runtime_telemetry_available": "true", "runtime_signal_stale": "false",
            "connector_state": "CURRENT_ACKNOWLEDGED", "connector_rediscovered": "true",
            "connector_rediscovered_at": "2026-09-15T00:00:00Z",
            "connector_freshness_mode": "current_process_discovery",
            "connector_refresh_required": "false", "connector_ack_pending": "false",
            "connector_current_sha": "sha-current", "connector_ack_sha": "sha-current",
            "error_code": "none",
        }

    @staticmethod
    def strict_identity() -> dict[str, object]:
        return {
            "observation_schema_version": 1,
            "observation_kind": "mcp_identity_read_only",
            "mcp_ready": True,
            "identity_current": True,
            "mcp_process_instance_id": "mcp-process-file-read-0001",
            "mcp_server_instance_id": "mcp-server-file-read-0001",
            "activation_epoch_id": "activation-file-read-0001",
            "current_activation_epoch_id": "activation-file-read-0001",
            "tool_contract_sha256": "a" * 64,
        }

    def action(self) -> dict[str, object]:
        return {
            "action_id": "action-control-plane-0001",
            "attempt_id": "attempt-control-plane-0001",
            "owner_id": "owner-control-plane-0001",
            "device_id": "device-control-plane-0001",
            "endpoint_id": "endpoint-control-plane-0001",
            "workspace_id": "workspace-control-plane-0001",
            "workspace_generation": "generation-control-plane-0001",
            "context_id": "context-control-plane-0001",
            "binding_id": "binding-control-plane-0001",
            "tool_name": "workspace_context",
            "arguments_json": json.dumps({
                "operation": "read_file", "path": "fixture.txt", "start_line": 1,
                "max_lines": 20, "max_bytes": 1024,
            }),
            "mcp_file_read_intent_digest": "b" * 64,
            "admission_reference": "mcp_file_read:" + "b" * 64,
            "mcp_file_read_facade_schema_version": FACADE_CONTRACT["schema_version"],
            "mcp_file_read_facade_profile": FACADE_CONTRACT["profile"],
            "mcp_file_read_facade_contract_sha256": FACADE_CONTRACT["sha256"],
            "expires_at_ms": int(time.time() * 1000) + 60_000,
        }

    def install_policy(self) -> dict[str, object]:
        return _install_file_read_policy_values(
            self.args(),
            config_path=self.config_path,
            config=self.config,
            owner_id="owner-control-plane-0001",
            workspace_id="workspace-control-plane-0001",
            workspace_generation="generation-control-plane-0001",
            expires_at_ms=int(time.time() * 1000) + 60_000,
            facade_contract=FACADE_CONTRACT,
            allowed_relative_paths=["fixture.txt"],
            max_bytes=1024,
            max_lines=20,
        )

    def test_inspect_reports_installed_facade_without_changing_policy(self) -> None:
        self.install_policy()
        policy_path = self.data_root / "control-plane-file-read-policy.json"
        before = policy_path.read_bytes()
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(inspect_file_read_policy(self.args()), 0)
        receipt = json.loads(output.getvalue())
        self.assertEqual(receipt["facade_contract"], FACADE_CONTRACT)
        self.assertEqual(receipt["state"], "enabled")
        self.assertEqual(policy_path.read_bytes(), before)
        self.assertNotIn(self.config["node_secret"], output.getvalue())

    def test_standing_file_read_policy_is_not_bound_to_the_former_ttl(self) -> None:
        policy = _install_file_read_policy_values(
            self.args(),
            config_path=self.config_path,
            config=self.config,
            owner_id="owner-control-plane-0001",
            workspace_id="workspace-control-plane-0001",
            workspace_generation="generation-control-plane-0001",
            expires_at_ms=None,
            facade_contract=FACADE_CONTRACT,
            allowed_relative_paths=["fixture.txt"],
            max_bytes=1024,
            max_lines=20,
        )
        self.assertEqual(policy["schema_version"], 2)
        self.assertEqual(policy["authority_mode"], "standing")
        self.assertIsNone(policy["expires_at_ms"])
        request = _file_read_bridge_request(self.action(), self.config)
        admitted = _admit_file_read_policy_request(
            self.args(), config_path=self.config_path, config=self.config, request=request
        )
        self.assertEqual(admitted["authority_mode"], "standing")

    def test_workspace_prefix_policy_admits_exact_nested_file_and_rejects_unsafe_paths(self) -> None:
        policy = _install_file_read_policy_values(
            self.args(), config_path=self.config_path, config=self.config,
            owner_id="owner-control-plane-0001", workspace_id="workspace-control-plane-0001",
            workspace_generation="generation-control-plane-0001", expires_at_ms=None,
            facade_contract=FACADE_CONTRACT, allowed_relative_paths=None,
            allowed_relative_prefixes=["."], max_bytes=1024, max_lines=20,
        )
        self.assertEqual(policy["schema_version"], 3)
        self.assertEqual(policy["allowed_relative_prefixes"], ["."])
        request = _file_read_bridge_request(self.action(), self.config)
        request["path"] = "src/deep/fixture.txt"
        self.assertEqual(_admit_file_read_policy_request(
            self.args(), config_path=self.config_path, config=self.config, request=request,
        )["schema_version"], 3)
        for unsafe in ("../outside.txt", "src/.env", "src/.git/config", "/tmp/file.txt"):
            with self.subTest(unsafe=unsafe), self.assertRaises(RuntimeError):
                _admit_file_read_policy_request(
                    self.args(), config_path=self.config_path, config=self.config,
                    request={**request, "path": unsafe},
                )

    def test_standing_artifact_read_uses_the_same_local_policy_without_ttl(self) -> None:
        """Document reads stay local-policy-bound after the pilot TTL is removed."""

        (self.root / "fixture.txt").write_bytes(b"standing document content\n")
        policy = _install_file_read_policy_values(
            self.args(),
            config_path=self.config_path,
            config=self.config,
            owner_id="owner-control-plane-0001",
            workspace_id="workspace-control-plane-0001",
            workspace_generation="generation-control-plane-0001",
            expires_at_ms=None,
            facade_contract=FACADE_CONTRACT,
            allowed_relative_paths=["fixture.txt"],
            max_bytes=1024,
            max_lines=20,
        )
        action = {
            "action_id": "action-artifact-standing-0001",
            "attempt_id": "attempt-artifact-standing-0001",
            "owner_id": "owner-control-plane-0001",
            "device_id": self.config["device_id"],
            "endpoint_id": self.config["endpoint_id"],
            "workspace_id": policy["workspace_id"],
            "workspace_generation": policy["workspace_generation"],
            "binding_id": "binding-control-plane-0001",
            "tool_name": "document_workflow",
            "arguments_json": json.dumps({"operation": "doc_read", "path": "fixture.txt"}),
            "mcp_artifact_kind": "document",
            "mcp_artifact_path": "fixture.txt",
            "mcp_artifact_facade_schema_version": FACADE_CONTRACT["schema_version"],
            "mcp_artifact_facade_profile": FACADE_CONTRACT["profile"],
            "mcp_artifact_facade_contract_sha256": FACADE_CONTRACT["sha256"],
            "expires_at_ms": int(time.time() * 1000) + 60_000,
        }
        receipts: list[dict[str, object]] = []

        def request(_url: str, path: str, payload: dict[str, object], _authorization: str | None = None) -> dict[str, object]:
            if path.endswith("/poll"):
                self.assertEqual(payload, {"limit": 1, "lane": "bounded_artifact"})
                return {"actions": [action]}
            self.assertTrue(path.endswith("/receipts"))
            receipts.append(payload)
            return {"receipt_id": "receipt-artifact-standing-0001"}

        with mock.patch("control_plane.node_agent._request", side_effect=request), \
             mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(poll_artifact_once(self.args()), 0)

        self.assertEqual(len(receipts), 1)
        self.assertEqual(receipts[0]["receipt_state"], "completed")
        self.assertEqual(receipts[0]["local_handle"].startswith("cp_artifact_"), True)
        self.assertEqual(receipts[0]["payload"]["operation_kind"], "control_plane_artifact_document")
        self.assertEqual(receipts[0]["payload"]["content"], "standing document content\n")
        self.assertEqual(receipts[0]["payload"]["facade_contract"], FACADE_CONTRACT)

    def test_file_read_policy_is_independent_and_retirement_disables_the_matching_generation(self) -> None:
        policy = self.install_policy()
        self.assertEqual(policy["allowed_relative_paths"], ["fixture.txt"])
        self.assertEqual(policy["max_bytes"], 1024)
        self.assertNotEqual(_policy_digest(policy), "")

        disabled = _disable_matching_retired_workspace_file_read_policy(
            self.args(),
            {"workspace_id": policy["workspace_id"], "workspace_generation": policy["workspace_generation"]},
        )
        self.assertTrue(disabled)
        self.assertFalse(_read_file_read_policy(self.data_root / "control-plane-file-read-policy.json")["enabled"])

    def test_workspace_retirement_disables_both_local_policy_lanes_before_forgetting_root(self) -> None:
        """A new content-read policy cannot outlive the old compact policy path."""

        compact_contract = {
            "schema_version": 6,
            "profile": "control-plane-scoped-read-only-relay-v5",
            "sha256": "c" * 64,
        }
        compact_policy = _install_read_only_policy_values(
            self.args(),
            config=self.config,
            owner_id="owner-control-plane-0001",
            workspace_id="workspace-control-plane-0001",
            workspace_generation="generation-control-plane-0001",
            expires_at_ms=int(time.time() * 1000) + 60_000,
            facade_contract=compact_contract,
        )
        file_read_policy = self.install_policy()
        requests: list[tuple[str, dict[str, object]]] = []

        def retire(_url: str, route: str, payload: dict[str, object], _authorization: str | None = None) -> dict[str, object]:
            self.assertEqual(route, "/v1/nodes/device-control-plane-0001/workspace-registrations/retire")
            requests.append((route, payload))
            return {
                "device_id": "device-control-plane-0001",
                "workspace_id": "workspace-control-plane-0001",
                "workspace_generation": "generation-control-plane-0001",
                "display_name": "Fixture workspace",
                "capabilities": {"read": True, "write": False, "exec": False},
                "registered_at_ms": 1_700_000_000_000,
                "retired_at_ms": 1_700_000_000_001,
                "replayed": False,
            }

        with mock.patch("control_plane.node_agent._request", side_effect=retire), redirect_stdout(io.StringIO()):
            self.assertEqual(node_agent_main([
                "retire-workspace", "--config", str(self.config_path),
                "--workspace-registry", str(self.registry_path),
                "--workspace-id", "workspace-control-plane-0001",
                "--workspace-generation", "generation-control-plane-0001",
                "--data-root", str(self.data_root),
            ]), 0)

        self.assertEqual(requests, [(
            "/v1/nodes/device-control-plane-0001/workspace-registrations/retire",
            {
                "workspace_id": "workspace-control-plane-0001",
                "workspace_generation": "generation-control-plane-0001",
            },
        )])
        self.assertFalse(json.loads((self.data_root / "control-plane-read-only-policy.json").read_text(encoding="utf-8"))["enabled"])
        self.assertFalse(json.loads((self.data_root / "control-plane-file-read-policy.json").read_text(encoding="utf-8"))["enabled"])
        self.assertEqual(json.loads(self.registry_path.read_text(encoding="utf-8"))["entries"], [])
        self.assertEqual(compact_policy["workspace_generation"], file_read_policy["workspace_generation"])

    def test_file_read_action_requires_sealed_provenance_and_never_forwards_general_arguments(self) -> None:
        request = _file_read_bridge_request(self.action(), self.config)
        self.assertEqual(request["path"], "fixture.txt")
        self.assertEqual(request["facade_contract"], FACADE_CONTRACT)
        self.assertNotIn("intent_digest", request)
        for field, value in (
            ("mcp_file_read_intent_digest", None),
            ("admission_reference", "mcp_file_read:" + "c" * 64),
            ("mcp_file_read_facade_schema_version", 0),
            ("arguments_json", json.dumps({"operation": "read_file", "path": "../outside", "start_line": 1, "max_lines": 1, "max_bytes": 1})),
        ):
            with self.subTest(field=field):
                rejected = self.action()
                rejected[field] = value
                with self.assertRaisesRegex(RuntimeError, "^CONTROL_PLANE_FILE_READ_ACTION_DENIED$"):
                    _file_read_bridge_request(rejected, self.config)

    def test_file_read_poll_uses_only_its_lane_and_rejects_invalid_work_before_a_local_bridge(self) -> None:
        action = self.action()
        action["tool_name"] = "exec_command"
        requests: list[tuple[str, dict[str, object]]] = []

        def request(_url: str, path: str, payload: dict[str, object], _authorization: str | None = None) -> dict[str, object]:
            requests.append((path, payload))
            if path.endswith("/poll"):
                return {"actions": [action]}
            self.assertTrue(path.endswith("/receipts"))
            self.assertEqual(payload["receipt_state"], "rejected")
            self.assertEqual(payload["payload"], {
                "schema_version": 1,
                "operation_kind": "control_plane_bounded_file_read",
                "code": "CONTROL_PLANE_FILE_READ_ACTION_DENIED",
            })
            return {"receipt_id": "receipt-file-read-0001"}

        with mock.patch("control_plane.node_agent._request", side_effect=request), \
             mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch("control_plane.node_agent.recovery_file_read_bridge") as bridge, \
             redirect_stdout(io.StringIO()):
            self.assertEqual(poll_file_read_once(self.args()), 0)
        bridge.assert_not_called()
        self.assertEqual(requests[0], (
            "/v1/nodes/device-control-plane-0001/poll",
            {"limit": 1, "lane": "bounded_file_read"},
        ))

    def test_artifact_policy_cannot_read_the_same_relative_path_from_another_registered_root(self) -> None:
        """A file allowlist is scoped to its policy root, not to every root on a node."""

        self.install_policy()
        other_root = self.directory / "other-workspace"
        other_root.mkdir()
        (other_root / "fixture.txt").write_text("other-root-only-content\n", encoding="utf-8")
        registry = json.loads(self.registry_path.read_text(encoding="utf-8"))
        registry["entries"].append({
            "workspace_id": "workspace-control-plane-other",
            "workspace_generation": "generation-control-plane-other",
            "canonical_path": str(other_root.resolve()),
            "display_name": "Other fixture workspace",
            "capabilities": {"read": True, "write": False, "exec": False},
            "created_at_ms": 1_700_000_000_001,
        })
        self.registry_path.write_text(json.dumps(registry), encoding="utf-8")
        action = {
            "action_id": "action-artifact-other-root-0001",
            "attempt_id": "attempt-artifact-other-root-0001",
            "tool_name": "document_workflow",
            "expires_at_ms": int(time.time() * 1000) + 30_000,
            "owner_id": "owner-control-plane-0001",
            "device_id": self.config["device_id"],
            "endpoint_id": self.config["endpoint_id"],
            "workspace_id": "workspace-control-plane-other",
            "workspace_generation": "generation-control-plane-other",
            "mcp_artifact_kind": "document",
            "mcp_artifact_path": "fixture.txt",
            "mcp_artifact_facade_schema_version": FACADE_CONTRACT["schema_version"],
            "mcp_artifact_facade_profile": FACADE_CONTRACT["profile"],
            "mcp_artifact_facade_contract_sha256": FACADE_CONTRACT["sha256"],
        }
        receipts: list[dict[str, object]] = []

        def request(_url: str, path: str, payload: dict[str, object], _authorization: str | None = None) -> dict[str, object]:
            if path.endswith("/poll"):
                self.assertEqual(payload, {"limit": 1, "lane": "bounded_artifact"})
                return {"actions": [action]}
            self.assertTrue(path.endswith("/receipts"))
            receipts.append(payload)
            return {"receipt_id": "receipt-artifact-other-root-0001"}

        with mock.patch("control_plane.node_agent._request", side_effect=request), \
             mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(poll_artifact_once(self.args()), 0)
        self.assertEqual(len(receipts), 1)
        self.assertEqual(receipts[0]["receipt_state"], "rejected")
        self.assertEqual(receipts[0]["payload"]["code"], "CONTROL_PLANE_FILE_READ_TARGET_MISMATCH")
        self.assertNotIn("other-root-only-content", json.dumps(receipts[0]))

    def test_prepared_file_read_is_terminalized_unknown_before_any_new_poll_or_reexecution(self) -> None:
        action = self.action()
        journal_path = _file_read_journal_path(self.config_path)
        _write_json_atomic(journal_path, {
            "schema_version": FILE_READ_JOURNAL_SCHEMA_VERSION,
            "entries": {
                f"{action['action_id']}|{action['attempt_id']}": {
                    "state": "prepared",
                    "action_id": action["action_id"],
                    "attempt_id": action["attempt_id"],
                },
            },
        })
        receipts: list[dict[str, object]] = []

        def request(_url: str, path: str, payload: dict[str, object], _authorization: str | None = None) -> dict[str, object]:
            self.assertTrue(path.endswith("/receipts"), "prepared recovery must settle before a new queue poll")
            receipts.append(payload)
            return {"receipt_id": "receipt-file-read-prepared-0001"}

        with mock.patch("control_plane.node_agent._request", side_effect=request), \
             mock.patch("control_plane.node_agent._runtime_status", return_value={"state": "MISSING", "host": "unavailable"}), \
             mock.patch("control_plane.node_agent.recovery_file_read_bridge") as bridge, \
             redirect_stdout(io.StringIO()):
            self.assertEqual(poll_file_read_once(self.args()), 0)
        bridge.assert_not_called()
        self.assertEqual(receipts[0]["receipt_state"], "unknown")
        self.assertEqual(receipts[0]["payload"], {
            "schema_version": 1,
            "operation_kind": "control_plane_bounded_file_read",
            "code": "CONTROL_PLANE_FILE_READ_EFFECT_UNKNOWN",
            "diagnostic_code": "CONTROL_PLANE_FILE_READ_PREPARED_RECOVERED",
        })
        journal = _read_file_read_journal(journal_path)
        entry = journal["entries"][f"{action['action_id']}|{action['attempt_id']}"]
        self.assertEqual(entry["state"], "unknown")
        self.assertTrue(entry["receipt"]["receipt_submitted"])

    def test_file_read_cli_parser_dispatches_to_the_separate_policy_command(self) -> None:
        command = [
            "install-file-read-policy", "--config", str(self.config_path),
            "--workspace-registry", str(self.registry_path),
            "--owner-id", "owner-control-plane-0001",
            "--workspace-id", "workspace-control-plane-0001",
            "--workspace-generation", "generation-control-plane-0001",
            "--facade-schema-version", "8",
            "--facade-profile", FACADE_CONTRACT["profile"],
            "--facade-sha256", FACADE_CONTRACT["sha256"],
            "--allowed-relative-path", "fixture.txt",
            "--max-bytes", "1024", "--max-lines", "20",
            "--expires-at-ms", str(int(time.time() * 1000) + 60_000),
            "--confirm-install", "--data-root", str(self.data_root),
        ]
        with mock.patch("control_plane.node_agent.install_file_read_policy", return_value=7) as command_fn:
            self.assertEqual(node_agent_main(command), 7)
        command_fn.assert_called_once()

    def test_file_read_cli_without_expiry_installs_standing_policy(self) -> None:
        command = [
            "install-file-read-policy", "--config", str(self.config_path),
            "--workspace-registry", str(self.registry_path),
            "--owner-id", "owner-control-plane-0001",
            "--workspace-id", "workspace-control-plane-0001",
            "--workspace-generation", "generation-control-plane-0001",
            "--facade-schema-version", "8",
            "--facade-profile", FACADE_CONTRACT["profile"],
            "--facade-sha256", FACADE_CONTRACT["sha256"],
            "--allowed-relative-path", "fixture.txt",
            "--max-bytes", "1024", "--max-lines", "20",
            "--confirm-install", "--data-root", str(self.data_root),
        ]
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(node_agent_main(command), 0)
        receipt = json.loads(output.getvalue())
        self.assertEqual(receipt["authority_mode"], "standing")
        self.assertIsNone(receipt["expires_at_ms"])
        installed = json.loads((self.data_root / "control-plane-file-read-policy.json").read_text(encoding="utf-8"))
        self.assertEqual(installed["schema_version"], 2)
        self.assertEqual(installed["authority_mode"], "standing")
        self.assertIsNone(installed["expires_at_ms"])


if __name__ == "__main__":
    unittest.main()
