from __future__ import annotations

import base64
import hashlib
import io
import json
import tempfile
import time
import unittest
import zlib
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from control_plane.node_agent import (
    APPROVED_PATCH_JOURNAL_SCHEMA_VERSION,
    _admit_approved_patch_policy_request,
    _approved_patch_bridge_request,
    _approved_patch_journal_path,
    _approved_patch_projection_digest,
    _disable_matching_retired_workspace_approved_patch_policy,
    _install_approved_patch_policy_values,
    _install_file_read_policy_values,
    _install_read_only_policy_values,
    _policy_digest,
    _read_approved_patch_journal,
    _read_approved_patch_policy,
    _write_json_atomic,
    main as node_agent_main,
    poll_approved_patch_once,
    run_approved_patch_loop,
)


FACADE_CONTRACT = {
    "schema_version": 10,
    "profile": "control-plane-oauth-approved-patch-v1",
    "sha256": "f" * 64,
}


class ApprovedPatchNodeAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="control-plane-approved-patch-node-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.config_path = self.directory / "node.json"
        self.registry_path = self.directory / "workspace-registry.json"
        self.data_root = self.directory / "data"
        self.root = self.directory / "workspace"
        self.root.mkdir()
        self.fixture = self.root / "src" / "fixture.txt"
        self.fixture.parent.mkdir()
        self.initial_content = b"original fixture\n"
        self.fixture.write_bytes(self.initial_content)
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
            "mcp_process_instance_id": "mcp-process-approved-patch-0001",
            "mcp_server_instance_id": "mcp-server-approved-patch-0001",
            "activation_epoch_id": "activation-approved-patch-0001",
            "current_activation_epoch_id": "activation-approved-patch-0001",
            "tool_contract_sha256": "a" * 64,
        }

    def exact_patch(self, content: bytes = b"updated fixture\n") -> str:
        payload = base64.b64encode(zlib.compress(content)).decode("ascii")
        preimage = hashlib.sha256(self.initial_content).hexdigest()
        postimage = hashlib.sha256(content).hexdigest()
        return "\n".join((
            "*** Begin Patch",
            "*** Write Exact File: src/fixture.txt",
            f"@@ encoding=zlib-base64 preimage_sha256={preimage} postimage_sha256={postimage}",
            "+" + payload,
            "*** End Patch",
            "",
        ))

    def action(self, content: bytes = b"updated fixture\n") -> dict[str, object]:
        patch = self.exact_patch(content)
        preimage = hashlib.sha256(self.initial_content).hexdigest()
        patch_sha256 = hashlib.sha256(patch.encode("utf-8")).hexdigest()
        return {
            "action_id": "action-approved-patch-0001",
            "attempt_id": "attempt-approved-patch-0001",
            "owner_id": "owner-control-plane-0001",
            "device_id": "device-control-plane-0001",
            "endpoint_id": "endpoint-control-plane-0001",
            "workspace_id": "workspace-control-plane-0001",
            "workspace_generation": "generation-control-plane-0001",
            "context_id": "context-approved-patch-0001",
            "binding_id": "binding-approved-patch-0001",
            "mcp_task_id": "task_" + "a" * 32,
            "writer_lease_generation": 1,
            "tool_name": "agent_workflow",
            "arguments_json": json.dumps({
                "operation": "apply_patch",
                "permission_request_id": "permission-approved-patch-0001",
                "path": "src/fixture.txt",
                "preimage_sha256": preimage,
                "patch_sha256": patch_sha256,
                "validation_profile": "targeted",
            }),
            "mcp_approved_patch_permission_request_id": "permission-approved-patch-0001",
            "mcp_approved_patch_permission_digest": "c" * 64,
            "mcp_approved_patch_intent_digest": "d" * 64,
            "mcp_approved_patch_relative_path": "src/fixture.txt",
            "mcp_approved_patch_preimage_sha256": preimage,
            "mcp_approved_patch_sha256": patch_sha256,
            "mcp_approved_patch_validation_profile": "targeted",
            "mcp_approved_patch_envelope": patch,
            "mcp_approved_patch_facade_schema_version": FACADE_CONTRACT["schema_version"],
            "mcp_approved_patch_facade_profile": FACADE_CONTRACT["profile"],
            "mcp_approved_patch_facade_contract_sha256": FACADE_CONTRACT["sha256"],
            "admission_reference": "mcp_approved_patch:" + "d" * 64,
            "expires_at_ms": int(time.time() * 1000) + 60_000,
        }

    def install_policy(self) -> dict[str, object]:
        return _install_approved_patch_policy_values(
            self.args(),
            config_path=self.config_path,
            config=self.config,
            owner_id="owner-control-plane-0001",
            workspace_id="workspace-control-plane-0001",
            workspace_generation="generation-control-plane-0001",
            expires_at_ms=int(time.time() * 1000) + 5 * 60_000,
            facade_contract=FACADE_CONTRACT,
            allowed_relative_paths=["src/fixture.txt"],
            max_patch_bytes=4096,
            max_file_bytes=4096,
        )

    def test_standing_approved_patch_policy_is_not_bound_to_the_former_ttl(self) -> None:
        policy = _install_approved_patch_policy_values(
            self.args(),
            config_path=self.config_path,
            config=self.config,
            owner_id="owner-control-plane-0001",
            workspace_id="workspace-control-plane-0001",
            workspace_generation="generation-control-plane-0001",
            expires_at_ms=None,
            facade_contract=FACADE_CONTRACT,
            allowed_relative_paths=["src/fixture.txt"],
            max_patch_bytes=4096,
            max_file_bytes=4096,
        )
        self.assertEqual(policy["schema_version"], 2)
        self.assertEqual(policy["authority_mode"], "standing")
        self.assertIsNone(policy["expires_at_ms"])
        request = _approved_patch_bridge_request(self.action(), self.config)
        admitted, _entry = _admit_approved_patch_policy_request(
            self.args(), config_path=self.config_path, config=self.config, request=request
        )
        self.assertEqual(admitted["authority_mode"], "standing")

    def test_workspace_prefix_policy_admits_exact_patch_and_denies_unsafe_targets(self) -> None:
        policy = _install_approved_patch_policy_values(
            self.args(), config_path=self.config_path, config=self.config,
            owner_id="owner-control-plane-0001", workspace_id="workspace-control-plane-0001",
            workspace_generation="generation-control-plane-0001", expires_at_ms=None,
            facade_contract=FACADE_CONTRACT, allowed_relative_paths=None,
            allowed_relative_prefixes=["."], max_patch_bytes=4096, max_file_bytes=4096,
        )
        self.assertEqual(policy["schema_version"], 3)
        request = _approved_patch_bridge_request(self.action(), self.config)
        admitted, _ = _admit_approved_patch_policy_request(
            self.args(), config_path=self.config_path, config=self.config, request=request,
        )
        self.assertEqual(admitted["allowed_relative_prefixes"], ["."])
        for unsafe in ("../outside.txt", "src/.env", "src/.git/config", "C:/outside.txt"):
            with self.subTest(unsafe=unsafe), self.assertRaises(RuntimeError):
                _admit_approved_patch_policy_request(
                    self.args(), config_path=self.config_path, config=self.config,
                    request={**request, "path": unsafe},
                )

    def bridge_result(self, request: dict[str, object], policy: dict[str, object]) -> dict[str, object]:
        patch = zlib.decompress(base64.b64decode(
            "".join(line[1:] for line in str(request["patch_envelope"]).splitlines()[3:-1])
        ))
        file = {
            "path": request["path"],
            "preimage_sha256": request["preimage_sha256"],
            "postimage_sha256": hashlib.sha256(patch).hexdigest(),
            "bytes_written": len(patch),
        }
        return {
            "schema_version": 1,
            "operation_kind": "control_plane_approved_patch",
            "installation_id": None,
            "runtime_mode": "development",
            "action_id": request["action_id"],
            "attempt_id": request["attempt_id"],
            "task_id": request["task_id"],
            "writer_lease_generation": request["writer_lease_generation"],
            "run_id": "a" * 32,
            "wave_id": "b" * 32,
            "local_handle": "cp_ap_" + "e" * 48,
            "patch_applied": True,
            "local_semantic_acceptance": "pending",
            "policy_sha256": _policy_digest(policy),
            "actor": {
                "client_id": "electron-control-plane-approved-patch-bridge",
                "client_type": "electron",
            },
            "runtime_identity": {
                "activation_epoch_id": "activation-approved-patch-0001",
                "process_instance_id": "mcp-process-approved-patch-0001",
                "server_instance_id": "mcp-server-approved-patch-0001",
                "tool_contract_sha256": "a" * 64,
            },
            "facade_contract": FACADE_CONTRACT,
            "file": file,
            "response_sha256": _approved_patch_projection_digest(file),
        }

    def test_policy_requires_local_write_capability_and_retirement_revokes_it(self) -> None:
        policy = self.install_policy()
        self.assertEqual(policy["allowed_relative_paths"], ["src/fixture.txt"])
        self.assertEqual(policy["validation_profile"], "targeted")
        self.assertTrue(_disable_matching_retired_workspace_approved_patch_policy(
            self.args(),
            {"workspace_id": policy["workspace_id"], "workspace_generation": policy["workspace_generation"]},
        ))
        self.assertFalse(_read_approved_patch_policy(
            self.data_root / "control-plane-approved-patch-policy.json"
        )["enabled"])

    def test_workspace_retirement_disables_all_local_policy_lanes_before_forgetting_root(self) -> None:
        """A retired writable root cannot leave any older lane enabled."""

        compact_policy = _install_read_only_policy_values(
            self.args(),
            config=self.config,
            owner_id="owner-control-plane-0001",
            workspace_id="workspace-control-plane-0001",
            workspace_generation="generation-control-plane-0001",
            expires_at_ms=int(time.time() * 1000) + 60_000,
            facade_contract={
                "schema_version": 6,
                "profile": "control-plane-scoped-read-only-relay-v5",
                "sha256": "c" * 64,
            },
        )
        file_read_policy = _install_file_read_policy_values(
            self.args(),
            config_path=self.config_path,
            config=self.config,
            owner_id="owner-control-plane-0001",
            workspace_id="workspace-control-plane-0001",
            workspace_generation="generation-control-plane-0001",
            expires_at_ms=int(time.time() * 1000) + 60_000,
            facade_contract={
                "schema_version": 8,
                "profile": "control-plane-oauth-bounded-file-read-v1",
                "sha256": "b" * 64,
            },
            allowed_relative_paths=["src/fixture.txt"],
            max_bytes=1024,
            max_lines=20,
        )
        patch_policy = self.install_policy()

        def retire(_url: str, route: str, payload: dict[str, object], _authorization: str | None = None) -> dict[str, object]:
            self.assertEqual(route, "/v1/nodes/device-control-plane-0001/workspace-registrations/retire")
            self.assertEqual(payload, {
                "workspace_id": "workspace-control-plane-0001",
                "workspace_generation": "generation-control-plane-0001",
            })
            return {
                "device_id": "device-control-plane-0001",
                "workspace_id": "workspace-control-plane-0001",
                "workspace_generation": "generation-control-plane-0001",
                "display_name": "Fixture workspace",
                "capabilities": {"read": True, "write": True, "exec": False},
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

        for filename in (
            "control-plane-read-only-policy.json",
            "control-plane-file-read-policy.json",
            "control-plane-approved-patch-policy.json",
        ):
            self.assertFalse(json.loads((self.data_root / filename).read_text(encoding="utf-8"))["enabled"])
        self.assertEqual(json.loads(self.registry_path.read_text(encoding="utf-8"))["entries"], [])
        self.assertEqual(
            {compact_policy["workspace_generation"], file_read_policy["workspace_generation"], patch_policy["workspace_generation"]},
            {"generation-control-plane-0001"},
        )

    def test_action_reconstruction_and_local_admission_reject_wrong_scope_digest_contract_and_expiry(self) -> None:
        self.install_policy()
        request = _approved_patch_bridge_request(self.action(), self.config)
        self.assertNotIn("arguments_json", request)
        self.assertEqual(request["path"], "src/fixture.txt")

        for field, value, code in (
            ("owner_id", "owner-other-0001", "CONTROL_PLANE_APPROVED_PATCH_TARGET_MISMATCH"),
            ("path", "src/other.txt", "CONTROL_PLANE_APPROVED_PATCH_PATH_DENIED"),
            ("preimage_sha256", "0" * 64, "CONTROL_PLANE_APPROVED_PATCH_ENVELOPE_INVALID"),
            ("patch_sha256", "1" * 64, "CONTROL_PLANE_APPROVED_PATCH_ENVELOPE_INVALID"),
            ("facade_contract", {**FACADE_CONTRACT, "sha256": "2" * 64}, "CONTROL_PLANE_APPROVED_PATCH_CONTRACT_MISMATCH"),
        ):
            with self.subTest(field=field):
                changed = dict(request)
                changed[field] = value
                with self.assertRaisesRegex(RuntimeError, "^" + code + "$"):
                    _admit_approved_patch_policy_request(
                        self.args(), config_path=self.config_path, config=self.config, request=changed
                    )

        policy_path = self.data_root / "control-plane-approved-patch-policy.json"
        disabled = json.loads(policy_path.read_text(encoding="utf-8"))
        disabled["enabled"] = False
        _write_json_atomic(policy_path, disabled)
        with self.assertRaisesRegex(RuntimeError, "^CONTROL_PLANE_APPROVED_PATCH_DISABLED$"):
            _admit_approved_patch_policy_request(
                self.args(), config_path=self.config_path, config=self.config, request=request
            )

        disabled["enabled"] = True
        disabled["expires_at_ms"] = int(time.time() * 1000) - 1
        _write_json_atomic(policy_path, disabled)
        with self.assertRaisesRegex(RuntimeError, "^CONTROL_PLANE_APPROVED_PATCH_POLICY_EXPIRED$"):
            _admit_approved_patch_policy_request(
                self.args(), config_path=self.config_path, config=self.config, request=request
            )

    def test_action_reconstruction_rejects_sealed_field_disagreement_before_bridge(self) -> None:
        for field, value in (
            ("tool_name", "exec_command"),
            ("mcp_approved_patch_permission_request_id", "permission-other-patch-0001"),
            ("mcp_approved_patch_relative_path", "src/other.txt"),
            ("mcp_approved_patch_preimage_sha256", "0" * 64),
            ("mcp_approved_patch_sha256", "1" * 64),
            ("mcp_approved_patch_validation_profile", "unbounded"),
            ("admission_reference", "mcp_approved_patch:" + "e" * 64),
        ):
            with self.subTest(field=field):
                action = self.action()
                action[field] = value
                with self.assertRaisesRegex(RuntimeError, "^CONTROL_PLANE_APPROVED_PATCH_ACTION_DENIED$"):
                    _approved_patch_bridge_request(action, self.config)

    def test_repeating_patch_loop_stops_before_heartbeat_or_poll_when_policy_is_not_usable(self) -> None:
        loop_args = self.args()
        loop_args.interval_seconds = 15
        loop_args.max_iterations = 1
        policy_path = self.data_root / "control-plane-approved-patch-policy.json"

        for state, expected_code in (
            ("missing", "CONTROL_PLANE_APPROVED_PATCH_POLICY_MISSING"),
            ("disabled", "CONTROL_PLANE_APPROVED_PATCH_DISABLED"),
            ("expired", "CONTROL_PLANE_APPROVED_PATCH_POLICY_EXPIRED"),
        ):
            with self.subTest(state=state):
                policy_path.unlink(missing_ok=True)
                if state != "missing":
                    policy = self.install_policy()
                    if state == "disabled":
                        policy["enabled"] = False
                    else:
                        policy["expires_at_ms"] = int(time.time() * 1000) - 1
                    _write_json_atomic(policy_path, policy)
                output = io.StringIO()
                with mock.patch("control_plane.node_agent.runtime_heartbeat") as heartbeat, \
                     mock.patch("control_plane.node_agent.poll_approved_patch_once") as poll, \
                     redirect_stdout(output):
                    self.assertEqual(run_approved_patch_loop(loop_args), 0)
                heartbeat.assert_not_called()
                poll.assert_not_called()
                self.assertEqual(json.loads(output.getvalue()), {
                    "execution": "approved_patch_loop_not_started",
                    "reason": expected_code,
                    "completed_iterations": 0,
                })

    def test_approved_patch_cli_without_expiry_installs_standing_policy(self) -> None:
        command = [
            "install-approved-patch-policy", "--config", str(self.config_path),
            "--workspace-registry", str(self.registry_path),
            "--owner-id", "owner-control-plane-0001",
            "--workspace-id", "workspace-control-plane-0001",
            "--workspace-generation", "generation-control-plane-0001",
            "--facade-schema-version", "10",
            "--facade-profile", FACADE_CONTRACT["profile"],
            "--facade-sha256", FACADE_CONTRACT["sha256"],
            "--allowed-relative-path", "src/fixture.txt",
            "--max-patch-bytes", "4096", "--max-file-bytes", "4096",
            "--confirm-install", "--data-root", str(self.data_root),
        ]
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(node_agent_main(command), 0)
        receipt = json.loads(output.getvalue())
        self.assertEqual(receipt["authority_mode"], "standing")
        self.assertIsNone(receipt["expires_at_ms"])
        installed = json.loads((self.data_root / "control-plane-approved-patch-policy.json").read_text(encoding="utf-8"))
        self.assertEqual(installed["schema_version"], 2)
        self.assertEqual(installed["authority_mode"], "standing")
        self.assertIsNone(installed["expires_at_ms"])

    def test_poll_rejects_wrong_tool_before_the_mutation_bridge(self) -> None:
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
                "operation_kind": "control_plane_approved_patch",
                "code": "CONTROL_PLANE_APPROVED_PATCH_ACTION_DENIED",
            })
            return {"receipt_id": "receipt-approved-patch-rejected-0001"}

        with mock.patch("control_plane.node_agent._request", side_effect=request), \
             mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch("control_plane.node_agent.recovery_approved_patch_bridge") as bridge, \
             redirect_stdout(io.StringIO()):
            self.assertEqual(poll_approved_patch_once(self.args()), 0)
        bridge.assert_not_called()
        self.assertEqual(requests[0], (
            "/v1/nodes/device-control-plane-0001/poll",
            {"limit": 1, "lane": "approved_patch"},
        ))

    def test_poll_uses_only_approved_patch_lane_and_receipt_never_contains_patch_bytes(self) -> None:
        policy = self.install_policy()
        action = self.action()
        requests: list[tuple[str, dict[str, object]]] = []

        def request(_url: str, path: str, payload: dict[str, object], _authorization: str | None = None) -> dict[str, object]:
            requests.append((path, payload))
            if path.endswith("/poll"):
                return {"actions": [action]}
            self.assertTrue(path.endswith("/receipts"))
            self.assertEqual(payload["receipt_state"], "completed")
            self.assertNotIn(str(action["mcp_approved_patch_envelope"]), json.dumps(payload))
            self.assertNotIn("patch_envelope", json.dumps(payload))
            return {"receipt_id": "receipt-approved-patch-0001"}

        bridge_calls: list[dict[str, object]] = []

        def bridge(_args: object, _root: Path, request_value: dict[str, object]) -> tuple[dict[str, object], None]:
            bridge_calls.append(request_value)
            return self.bridge_result(request_value, policy), None

        with mock.patch("control_plane.node_agent._request", side_effect=request), \
             mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch("control_plane.node_agent.recovery_approved_patch_bridge", side_effect=bridge), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(poll_approved_patch_once(self.args()), 0)
            # A duplicate delivery can only replay the durable receipt. It
            # cannot call the mutation bridge a second time.
            self.assertEqual(poll_approved_patch_once(self.args()), 0)

        self.assertEqual(len(bridge_calls), 1)
        self.assertEqual(requests[0], (
            "/v1/nodes/device-control-plane-0001/poll",
            {"limit": 1, "lane": "approved_patch"},
        ))
        receipt_payloads = [payload for path, payload in requests if path.endswith("/receipts")]
        self.assertEqual(len(receipt_payloads), 1)
        self.assertEqual(receipt_payloads[0]["payload"]["file"]["path"], "src/fixture.txt")

    def test_prepared_patch_is_terminalized_unknown_before_repoll_or_reexecution(self) -> None:
        action = self.action()
        journal_path = _approved_patch_journal_path(self.config_path)
        _write_json_atomic(journal_path, {
            "schema_version": APPROVED_PATCH_JOURNAL_SCHEMA_VERSION,
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
            self.assertTrue(path.endswith("/receipts"), "prepared mutation must settle before any new poll")
            receipts.append(payload)
            return {"receipt_id": "receipt-approved-patch-prepared-0001"}

        with mock.patch("control_plane.node_agent._request", side_effect=request), \
             mock.patch("control_plane.node_agent._runtime_status", return_value={"state": "MISSING", "host": "unavailable"}), \
             mock.patch("control_plane.node_agent.recovery_approved_patch_bridge") as bridge, \
             redirect_stdout(io.StringIO()):
            self.assertEqual(poll_approved_patch_once(self.args()), 0)
        bridge.assert_not_called()
        self.assertEqual(receipts[0]["receipt_state"], "unknown")
        self.assertEqual(receipts[0]["payload"], {
            "schema_version": 1,
            "operation_kind": "control_plane_approved_patch",
            "code": "CONTROL_PLANE_APPROVED_PATCH_EFFECT_UNKNOWN",
            "diagnostic_code": "CONTROL_PLANE_APPROVED_PATCH_PREPARED_RECOVERED",
        })
        entry = _read_approved_patch_journal(journal_path)["entries"][
            f"{action['action_id']}|{action['attempt_id']}"
        ]
        self.assertEqual(entry["state"], "unknown")
        self.assertTrue(entry["receipt"]["receipt_submitted"])

    def test_cli_parser_dispatches_to_the_separate_approved_patch_policy_command(self) -> None:
        command = [
            "install-approved-patch-policy", "--config", str(self.config_path),
            "--workspace-registry", str(self.registry_path),
            "--owner-id", "owner-control-plane-0001",
            "--workspace-id", "workspace-control-plane-0001",
            "--workspace-generation", "generation-control-plane-0001",
            "--facade-schema-version", "10",
            "--facade-profile", FACADE_CONTRACT["profile"],
            "--facade-sha256", FACADE_CONTRACT["sha256"],
            "--allowed-relative-path", "src/fixture.txt",
            "--max-patch-bytes", "4096", "--max-file-bytes", "4096",
            "--expires-at-ms", str(int(time.time() * 1000) + 60_000),
            "--confirm-install", "--data-root", str(self.data_root),
        ]
        with mock.patch("control_plane.node_agent.install_approved_patch_policy", return_value=7) as command_fn:
            self.assertEqual(node_agent_main(command), 7)
        command_fn.assert_called_once()


if __name__ == "__main__":
    unittest.main()
