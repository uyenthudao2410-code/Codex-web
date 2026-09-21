"""Exec node policy, allowlist, workspace lock and bounded runner."""

from __future__ import annotations

import io
import json
import tempfile
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from control_plane.node_agent import (
    _admit_exec_policy_request,
    _exec_bridge_request,
    _exec_allowlist_match,
    _exec_argv_item,
    _exec_journal_key,
    _flush_exec_journal,
    _normalise_exec_policy,
    _policy_digest,
    _read_exec_journal,
    _record_exec_receipt,
    _run_bounded_exec,
    _write_json_atomic,
    disable_exec_policy,
    install_exec_policy,
    inspect_exec_policy,
    main,
    poll_exec_once,
)

FACADE = {"schema_version": 14, "profile": "control-plane-oauth-bounded-exec-v1", "sha256": "f" * 64}


def _policy(**overrides):
    base = {
        "schema_version": 2, "enabled": True, "authority_mode": "standing", "server_origin": "https://control.example.test",
        "owner_id": "owner-default", "device_id": "device-exec-0001", "endpoint_id": "endpoint-exec-0001",
        "workspace_id": "workspace-exec-0001", "workspace_generation": "generation-exec-0001",
        "expires_at_ms": None, "facade_contract": dict(FACADE),
        "allowed_argv_prefixes": [["python", "-m", "pytest"], ["npm", "test"]],
        "max_timeout_ms": 60000, "max_output_bytes": 32768, "max_concurrent": 2,
    }
    base.update(overrides)
    return base


class ExecPolicyTests(unittest.TestCase):
    def test_allowlist_prefix_match(self) -> None:
        prefixes = [["python", "-m", "pytest"], ["npm", "test"]]
        self.assertTrue(_exec_allowlist_match(["python", "-m", "pytest", "-q"], prefixes))
        self.assertTrue(_exec_allowlist_match(["npm", "test"], prefixes))
        self.assertFalse(_exec_allowlist_match(["python", "-m", "pip", "install", "x"], prefixes))
        self.assertFalse(_exec_allowlist_match(["rm", "-rf", "/"], prefixes))

    def test_shell_tokens_rejected_in_policy_items(self) -> None:
        with self.assertRaises(RuntimeError):
            _exec_argv_item("a;rm -rf /")
        with self.assertRaises(RuntimeError):
            _exec_argv_item("$(whoami)")

    def test_policy_caps_are_enforced_by_shape(self) -> None:
        ok = _normalise_exec_policy(_policy(), now_ms=1_700_000_000_000, require_enabled=True)
        self.assertEqual(ok["max_concurrent"], 2)
        self.assertEqual(ok["authority_mode"], "standing")
        self.assertIsNone(_normalise_exec_policy(_policy(), now_ms=9_000_000_000_000)["expires_at_ms"])
        with self.assertRaises(RuntimeError):
            _normalise_exec_policy(_policy(max_timeout_ms=10_000_000), now_ms=1_700_000_000_000)
        with self.assertRaises(RuntimeError):
            _normalise_exec_policy(_policy(enabled=False), now_ms=1_700_000_000_000, require_enabled=True)
        with self.assertRaises(RuntimeError):
            _normalise_exec_policy(_policy(expires_at_ms=1_600_000_000_000), now_ms=1_700_000_000_000)
        legacy = _policy(schema_version=1)
        legacy.pop("authority_mode")
        legacy["expires_at_ms"] = 1_600_000_000_000
        with self.assertRaisesRegex(RuntimeError, "^CONTROL_PLANE_EXEC_POLICY_EXPIRED$"):
            _normalise_exec_policy(legacy, now_ms=1_700_000_000_000)


class BoundedRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="exec-runner-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_success_and_output_caps(self) -> None:
        result, error = _run_bounded_exec(
            argv=["python3", "-c", "print('hello-exec')"], cwd_path=self.root,
            timeout_ms=10000, max_output_bytes=32768)
        self.assertIsNone(error)
        assert result is not None
        self.assertEqual(result["exit_code"], 0)
        self.assertIn("hello-exec", result["stdout"])

    def test_timeout_reports_typed_uncertainty_or_timeout(self) -> None:
        result, error = _run_bounded_exec(
            argv=["python3", "-c", "import time; time.sleep(30)"], cwd_path=self.root,
            timeout_ms=5000, max_output_bytes=32768)
        # Either a timed-out result or a typed cleanup-uncertain error; never silent.
        self.assertTrue((result is not None and result.get("timed_out")) or error is not None)

    def test_verified_stop_kills_tree(self) -> None:
        calls = {"n": 0}

        def _stop_check() -> bool:
            calls["n"] += 1
            return calls["n"] >= 3

        result, error = _run_bounded_exec(
            argv=["python3", "-c", "import time; time.sleep(30)"], cwd_path=self.root,
            timeout_ms=60000, max_output_bytes=32768, stop_check=_stop_check)
        self.assertIsNone(error)
        assert result is not None
        self.assertTrue(result.get("stopped"))

    def test_shell_is_never_used(self) -> None:
        # If shell were used, echo would expand; with shell=False the literal runs.
        result, error = _run_bounded_exec(
            argv=["python3", "-c", "import sys; sys.stdout.write(';rm')"], cwd_path=self.root,
            timeout_ms=10000, max_output_bytes=32768)
        self.assertIsNone(error)
        assert result is not None
        self.assertIn(";rm", result["stdout"])


class ExecNodeReceiptTests(unittest.TestCase):
    """The disabled exec lane still must preserve its no-replay boundary."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="exec-node-agent-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        self.config_path = self.root / "node.json"
        self.registry_path = self.root / "control-plane-workspaces.json"
        self.data_root = self.root / "profile"
        self.data_root.mkdir()
        self.config = {
            "server_url": "https://control.example.test",
            "device_id": "device-exec-0001",
            "endpoint_id": "endpoint-exec-0001",
            "node_secret": "node-secret-test-only",
        }
        self.config_path.write_text(json.dumps(self.config), encoding="utf-8")
        self.registry_path.write_text(json.dumps({
            "schema_version": 1,
            "entries": [{
                "workspace_id": "workspace-exec-0001",
                "workspace_generation": "generation-exec-0001",
                "canonical_path": str(self.workspace.resolve()),
                "display_name": "Exec fixture",
                "capabilities": {"read": True, "write": True, "exec": True},
                "created_at_ms": 1_700_000_000_000,
            }],
        }), encoding="utf-8")

    def args(self) -> SimpleNamespace:
        return SimpleNamespace(
            config=str(self.config_path),
            workspace_registry=str(self.registry_path),
            data_root=str(self.data_root),
            project_root=str(self.workspace),
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
            "mcp_process_instance_id": "mcp-process-exec-0001",
            "mcp_server_instance_id": "mcp-server-exec-0001",
            "activation_epoch_id": "activation-exec-0001",
            "current_activation_epoch_id": "activation-exec-0001",
            "tool_contract_sha256": "a" * 64,
        }

    def policy(self, **overrides: object) -> dict[str, object]:
        value = _policy(
            owner_id="owner-control-plane-0001",
            device_id=self.config["device_id"],
            endpoint_id=self.config["endpoint_id"],
            workspace_id="workspace-exec-0001",
            workspace_generation="generation-exec-0001",
            expires_at_ms=None,
        )
        value.update(overrides)
        return value

    def install_policy(self, **overrides: object) -> dict[str, object]:
        policy = self.policy(**overrides)
        _write_json_atomic(self.data_root / "control-plane-exec-policy.json", policy)
        return policy

    def exec_policy_cli_args(self, *, replace: bool = False, expires_at_ms: int | None = None) -> list[str]:
        args = [
            "install-exec-policy",
            "--config", str(self.config_path),
            "--workspace-registry", str(self.registry_path),
            "--owner-id", "owner-control-plane-0001",
            "--workspace-id", "workspace-exec-0001",
            "--workspace-generation", "generation-exec-0001",
            "--facade-schema-version", str(FACADE["schema_version"]),
            "--facade-profile", str(FACADE["profile"]),
            "--facade-sha256", str(FACADE["sha256"]),
            "--allowed-argv-prefix", json.dumps(["python", "-m", "pytest"]),
            "--max-timeout-ms", "60000",
            "--max-output-bytes", "32768",
            "--confirm-install",
            "--data-root", str(self.data_root),
            "--project-root", str(self.workspace),
        ]
        if replace:
            args.append("--replace")
        if expires_at_ms is not None:
            args.extend(["--expires-at-ms", str(expires_at_ms)])
        return args

    def test_cli_installs_standing_policy_and_reenable_after_disable(self) -> None:
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(self.exec_policy_cli_args()), 0)
        installed_receipt = json.loads(output.getvalue())
        self.assertEqual(installed_receipt["execution"], "exec_policy_installed")
        self.assertEqual(installed_receipt["authority_mode"], "standing")
        self.assertIsNone(installed_receipt["expires_at_ms"])

        policy_path = self.data_root / "control-plane-exec-policy.json"
        installed = json.loads(policy_path.read_text(encoding="utf-8"))
        self.assertEqual(installed["schema_version"], 2)
        self.assertEqual(installed["authority_mode"], "standing")
        self.assertIsNone(installed["expires_at_ms"])

        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main([
                "inspect-exec-policy",
                "--data-root", str(self.data_root),
                "--project-root", str(self.workspace),
            ]), 0)
        inspected = json.loads(output.getvalue())
        self.assertEqual(inspected["authority_mode"], "standing")
        self.assertIsNone(inspected["expires_at_ms"])
        self.assertTrue(inspected["enabled"])

        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main([
                "disable-exec-policy",
                "--confirm-disable",
                "--data-root", str(self.data_root),
                "--project-root", str(self.workspace),
            ]), 0)
        self.assertFalse(json.loads(policy_path.read_text(encoding="utf-8"))["enabled"])

        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(self.exec_policy_cli_args(replace=True)), 0)
        reenabled = json.loads(policy_path.read_text(encoding="utf-8"))
        self.assertTrue(reenabled["enabled"])
        self.assertEqual(reenabled["authority_mode"], "standing")
        self.assertIsNone(reenabled["expires_at_ms"])

    def test_cli_rejects_legacy_expiry_without_writing_policy(self) -> None:
        stderr = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(stderr):
            self.assertEqual(main(self.exec_policy_cli_args(expires_at_ms=int(time.time() * 1000) + 60_000)), 1)
        self.assertEqual(json.loads(stderr.getvalue())["error"], "CONTROL_PLANE_EXEC_POLICY_EXPIRY_UNSUPPORTED")
        self.assertFalse((self.data_root / "control-plane-exec-policy.json").exists())

    def running_journal(self) -> tuple[Path, dict[str, object], dict[str, object], dict[str, object]]:
        policy = self.install_policy()
        action = self.action()
        request = _exec_bridge_request(action, self.config)
        running_projection = {
            "status": "running",
            "exit_code": None,
            "stdout": "still running\n",
            "stderr": "",
            "truncated": False,
            "timed_out": False,
            "command_id": "command-exec-node-running-0001",
            "job_id": "job-exec-node-running-0001",
            "run_id": "",
            "wave_id": "",
            "output_refs": None,
        }
        running_result = {
            "schema_version": 1,
            "operation_kind": "control_plane_exec",
            "local_handle": "cp_exec_" + "b" * 48,
            "action_id": request["action_id"],
            "attempt_id": request["attempt_id"],
            "task_id": request["task_id"],
            "writer_lease_generation": request["writer_lease_generation"],
            "policy_sha256": _policy_digest(policy),
            "actor": {"client_id": "electron-control-plane-exec-bridge", "client_type": "electron"},
            "facade_contract": request["facade_contract"],
            "runtime_identity": {
                "activation_epoch_id": "activation-exec-0001",
                "process_instance_id": "mcp-process-exec-0001",
                "server_instance_id": "mcp-server-exec-0001",
                "tool_contract_sha256": "a" * 64,
            },
            **running_projection,
            "response_sha256": __import__("hashlib").sha256(json.dumps(
                running_projection, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")).hexdigest(),
        }
        journal_path = self.config_path.with_name(f"{self.config_path.name}.exec-journal.json")
        journal = {"schema_version": 1, "entries": {}}
        entry = _record_exec_receipt(
            journal_path,
            journal,
            state="running",
            action_id=request["action_id"],
            attempt_id=request["attempt_id"],
            receipt_state="accepted",
            local_handle=running_result["local_handle"],
            payload=running_result,
        )
        entry["request"] = request
        entry["policy_sha256"] = _policy_digest(policy)
        entry["result"] = running_result
        entry["receipt"]["receipt_submitted"] = True
        journal["entries"][_exec_journal_key(request["action_id"], request["attempt_id"])] = entry
        _write_json_atomic(journal_path, journal)
        return journal_path, journal, request, running_result

    @staticmethod
    def bridge_result(request: dict[str, object], *, status: str, local_handle: str,
                      command_id: str, job_id: str, policy_sha256: str) -> dict[str, object]:
        projection = {
            "status": status,
            "exit_code": 0 if status == "exited" else 143 if status == "stopped" else None,
            "stdout": "done\n" if status != "running" else "still running\n",
            "stderr": "" if status != "stopped" else "terminated\n",
            "truncated": False,
            "timed_out": False,
            "command_id": command_id,
            "job_id": job_id,
            "run_id": "",
            "wave_id": "",
            "output_refs": None,
        }
        return {
            "schema_version": 1,
            "operation_kind": "control_plane_exec",
            "local_handle": local_handle,
            "action_id": request["action_id"],
            "attempt_id": request["attempt_id"],
            "task_id": request["task_id"],
            "writer_lease_generation": request["writer_lease_generation"],
            "policy_sha256": policy_sha256,
            "actor": {"client_id": "electron-control-plane-exec-bridge", "client_type": "electron"},
            "facade_contract": request["facade_contract"],
            "runtime_identity": {
                "activation_epoch_id": "activation-exec-0001",
                "process_instance_id": "mcp-process-exec-0001",
                "server_instance_id": "mcp-server-exec-0001",
                "tool_contract_sha256": "a" * 64,
            },
            **projection,
            "response_sha256": __import__("hashlib").sha256(json.dumps(
                projection, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")).hexdigest(),
        }

    def action(self, **overrides: object) -> dict[str, object]:
        value: dict[str, object] = {
            "action_id": "act-exec-node-0001",
            "attempt_id": "try-exec-node-0001",
            "owner_id": "owner-control-plane-0001",
            "device_id": self.config["device_id"],
            "endpoint_id": self.config["endpoint_id"],
            "workspace_id": "workspace-exec-0001",
            "workspace_generation": "generation-exec-0001",
            "context_id": "ctx-exec-node-0001",
            "binding_id": "binding-exec-node-0001",
            "expires_at_ms": int(time.time() * 1000) + 120_000,
            "mcp_task_id": "task_" + "a" * 32,
            "writer_lease_generation": 1,
            "mcp_exec_argv_json": json.dumps({"argv": ["python", "-m", "pytest", "-q"]}),
            "mcp_exec_cwd": "",
            "mcp_exec_timeout_ms": 60_000,
            "mcp_exec_max_output_bytes": 32_768,
            "mcp_exec_facade_schema_version": FACADE["schema_version"],
            "mcp_exec_facade_profile": FACADE["profile"],
            "mcp_exec_facade_contract_sha256": FACADE["sha256"],
        }
        value.update(overrides)
        return value

    def test_owner_is_a_required_exact_exec_policy_binding(self) -> None:
        self.install_policy()
        request = _exec_bridge_request(self.action(), self.config)
        admitted = _admit_exec_policy_request(
            self.args(), config_path=self.config_path, config=self.config, request=request
        )
        self.assertEqual(admitted["owner_id"], "owner-control-plane-0001")

        mismatched = dict(request)
        mismatched["owner_id"] = "owner-control-plane-other"
        with self.assertRaisesRegex(RuntimeError, "^CONTROL_PLANE_EXEC_POLICY_CONFIG_MISMATCH$"):
            _admit_exec_policy_request(
                self.args(), config_path=self.config_path, config=self.config, request=mismatched
            )
        action_without_owner = self.action()
        action_without_owner.pop("owner_id")
        with self.assertRaisesRegex(RuntimeError, "^CONTROL_PLANE_EXEC_ACTION_DENIED$"):
            _exec_bridge_request(action_without_owner, self.config)

    def test_terminal_exec_receipt_is_durable_and_replayed_unchanged(self) -> None:
        journal_path = self.config_path.with_name(f"{self.config_path.name}.exec-journal.json")
        journal = {"schema_version": 1, "entries": {}}
        entry = _record_exec_receipt(
            journal_path,
            journal,
            state="completed",
            action_id="act-exec-node-0001",
            attempt_id="try-exec-node-0001",
            receipt_state="completed",
            local_handle="cp_exec_" + "a" * 48,
            payload={"schema_version": 1, "operation_kind": "control_plane_exec", "exit_code": 0},
        )
        self.assertIn("receipt", entry)
        self.assertFalse(entry["receipt"]["receipt_submitted"])

        sent: list[dict[str, object]] = []

        def request(_url: str, path: str, payload: dict[str, object], _authorization: str | None = None) -> dict[str, object]:
            self.assertEqual(path, "/v1/nodes/device-exec-0001/receipts")
            sent.append(payload)
            return {"receipt_id": "receipt-exec-node-0001"}

        with mock.patch("control_plane.node_agent._request", side_effect=request):
            self.assertEqual(_flush_exec_journal(self.config, journal_path, journal), 1)
        self.assertEqual(sent, [{
            "action_id": "act-exec-node-0001",
            "attempt_id": "try-exec-node-0001",
            "receipt_state": "completed",
            "local_handle": "cp_exec_" + "a" * 48,
            "payload": {"schema_version": 1, "operation_kind": "control_plane_exec", "exit_code": 0},
        }])
        durable = _read_exec_journal(journal_path)
        saved = durable["entries"][_exec_journal_key("act-exec-node-0001", "try-exec-node-0001")]
        self.assertTrue(saved["receipt"]["receipt_submitted"])

    def test_prepared_exec_recovers_as_unknown_without_a_second_spawn(self) -> None:
        journal_path = self.config_path.with_name(f"{self.config_path.name}.exec-journal.json")
        journal = {
            "schema_version": 1,
            "entries": {
                _exec_journal_key("act-exec-node-0001", "try-exec-node-0001"): {
                    "state": "prepared",
                    "action_id": "act-exec-node-0001",
                    "attempt_id": "try-exec-node-0001",
                },
            },
        }
        _write_json_atomic(journal_path, journal)
        receipts: list[dict[str, object]] = []

        def request(_url: str, path: str, payload: dict[str, object], _authorization: str | None = None) -> dict[str, object]:
            self.assertEqual(path, "/v1/nodes/device-exec-0001/receipts")
            receipts.append(payload)
            return {"receipt_id": "receipt-exec-unknown-0001"}

        with mock.patch("control_plane.node_agent._request", side_effect=request):
            self.assertEqual(_flush_exec_journal(self.config, journal_path, journal), 1)
        self.assertEqual(receipts[0]["receipt_state"], "unknown")
        self.assertEqual(receipts[0]["payload"]["code"], "CONTROL_PLANE_EXEC_EFFECT_UNKNOWN")
        self.assertEqual(
            _read_exec_journal(journal_path)["entries"][_exec_journal_key("act-exec-node-0001", "try-exec-node-0001")]["state"],
            "unknown",
        )

    def test_valid_exec_submission_uses_nested_receipt_shape(self) -> None:
        policy = self.install_policy()
        action = self.action()
        request = _exec_bridge_request(action, self.config)
        response_projection = {
            "status": "exited",
            "exit_code": 0,
            "stdout": "fixture complete\n",
            "stderr": "",
            "truncated": False,
            "timed_out": False,
            "command_id": "command-exec-node-0001",
            "job_id": "job-exec-node-0001",
            "run_id": "",
            "wave_id": "",
            "output_refs": None,
        }
        bridge_result = {
            "schema_version": 1,
            "operation_kind": "control_plane_exec",
            "local_handle": "cp_exec_" + "a" * 48,
            "action_id": request["action_id"],
            "attempt_id": request["attempt_id"],
            "task_id": request["task_id"],
            "writer_lease_generation": request["writer_lease_generation"],
            "policy_sha256": _policy_digest(policy),
            "actor": {"client_id": "electron-control-plane-exec-bridge", "client_type": "electron"},
            "facade_contract": request["facade_contract"],
            "runtime_identity": {
                "activation_epoch_id": "activation-exec-0001",
                "process_instance_id": "mcp-process-exec-0001",
                "server_instance_id": "mcp-server-exec-0001",
                "tool_contract_sha256": "a" * 64,
            },
            **response_projection,
            "response_sha256": __import__("hashlib").sha256(json.dumps(
                response_projection, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")).hexdigest(),
        }
        receipts: list[dict[str, object]] = []

        def request(_url: str, path: str, payload: dict[str, object], _authorization: str | None = None) -> dict[str, object]:
            if path.endswith("/exec-stops"):
                return {"stop_requests": []}
            if path.endswith("/poll"):
                return {"actions": [action]}
            self.assertTrue(path.endswith("/receipts"))
            receipts.append(payload)
            return {"receipt_id": "receipt-exec-completed-0001"}

        with mock.patch("control_plane.node_agent._request", side_effect=request), \
             mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch("control_plane.node_agent.recovery_exec_bridge", return_value=(bridge_result, None)), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(poll_exec_once(self.args()), 0)
        self.assertEqual(len(receipts), 1)
        self.assertEqual(receipts[0]["receipt_state"], "completed")
        self.assertEqual(receipts[0]["payload"]["exit_code"], 0)

    def test_owner_mismatch_is_rejected_instead_of_crashing_after_dequeue(self) -> None:
        self.install_policy()
        action = self.action(owner_id="owner-control-plane-other")
        receipts: list[dict[str, object]] = []

        def request(_url: str, path: str, payload: dict[str, object], _authorization: str | None = None) -> dict[str, object]:
            if path.endswith("/exec-stops"):
                return {"stop_requests": []}
            if path.endswith("/poll"):
                return {"actions": [action]}
            self.assertTrue(path.endswith("/receipts"))
            receipts.append(payload)
            return {"receipt_id": "receipt-exec-rejected-0001"}

        with mock.patch("control_plane.node_agent._request", side_effect=request), \
             mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch("control_plane.node_agent._run_bounded_exec") as runner, \
             redirect_stdout(io.StringIO()):
            self.assertEqual(poll_exec_once(self.args()), 0)
        runner.assert_not_called()
        self.assertEqual(receipts[0]["receipt_state"], "rejected")
        self.assertEqual(receipts[0]["payload"]["code"], "CONTROL_PLANE_EXEC_POLICY_CONFIG_MISMATCH")

    def test_running_job_is_polled_and_terminal_receipt_is_submitted_without_respawn(self) -> None:
        journal_path, _journal, request, running_result = self.running_journal()
        terminal = self.bridge_result(
            request,
            status="exited",
            local_handle=running_result["local_handle"],
            command_id=running_result["command_id"],
            job_id=running_result["job_id"],
            policy_sha256=running_result["policy_sha256"],
        )
        bridge_requests: list[dict[str, object]] = []
        receipts: list[dict[str, object]] = []

        def request_fn(_url: str, path: str, payload: dict[str, object], _authorization: str | None = None) -> dict[str, object]:
            if path.endswith("/exec-stops"):
                return {"stop_requests": []}
            if path.endswith("/poll"):
                return {"actions": []}
            self.assertTrue(path.endswith("/receipts"))
            receipts.append(payload)
            return {"receipt_id": "receipt-exec-polled-0001"}

        def bridge(_args: object, _project_root: Path, control: dict[str, object]) -> tuple[dict[str, object], None]:
            bridge_requests.append(control)
            return terminal, None

        with mock.patch("control_plane.node_agent._request", side_effect=request_fn), \
             mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch("control_plane.node_agent.recovery_exec_bridge", side_effect=bridge), \
             mock.patch("control_plane.node_agent._run_bounded_exec") as runner, \
             redirect_stdout(io.StringIO()):
            self.assertEqual(poll_exec_once(self.args()), 0)
        runner.assert_not_called()
        self.assertEqual([item["operation"] for item in bridge_requests], ["exec_poll"])
        self.assertEqual(len(receipts), 1)
        self.assertEqual(receipts[0]["receipt_state"], "completed")
        saved = _read_exec_journal(journal_path)["entries"][_exec_journal_key(request["action_id"], request["attempt_id"])]
        self.assertEqual(saved["state"], "completed")

    def test_stop_request_is_acknowledged_only_after_terminal_evidence(self) -> None:
        journal_path, _journal, request, running_result = self.running_journal()
        running = self.bridge_result(
            request,
            status="running",
            local_handle=running_result["local_handle"],
            command_id=running_result["command_id"],
            job_id=running_result["job_id"],
            policy_sha256=running_result["policy_sha256"],
        )
        stopped = self.bridge_result(
            request,
            status="stopped",
            local_handle=running_result["local_handle"],
            command_id=running_result["command_id"],
            job_id=running_result["job_id"],
            policy_sha256=running_result["policy_sha256"],
        )
        bridge_requests: list[dict[str, object]] = []
        paths: list[str] = []
        receipts: list[dict[str, object]] = []

        def request_fn(_url: str, path: str, payload: dict[str, object], _authorization: str | None = None) -> dict[str, object]:
            paths.append(path)
            if path.endswith("/exec-stops"):
                return {"stop_requests": [{"action_id": request["action_id"]}]}
            if path.endswith("/acknowledge"):
                return {"action_id": request["action_id"], "state": "acknowledged"}
            if path.endswith("/poll"):
                return {"actions": []}
            self.assertTrue(path.endswith("/receipts"))
            receipts.append(payload)
            return {"receipt_id": f"receipt-exec-stop-{len(receipts):04d}"}

        def bridge(_args: object, _project_root: Path, control: dict[str, object]) -> tuple[dict[str, object], None]:
            bridge_requests.append(control)
            return (running if control["operation"] == "exec_poll" else stopped), None

        with mock.patch("control_plane.node_agent._request", side_effect=request_fn), \
             mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch("control_plane.node_agent.recovery_exec_bridge", side_effect=bridge), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(poll_exec_once(self.args()), 0)
        self.assertEqual([item["operation"] for item in bridge_requests], ["exec_poll", "exec_stop"])
        self.assertIn(f"/v1/nodes/{self.config['device_id']}/exec-stops/{request['action_id']}/acknowledge", paths)
        self.assertEqual(receipts[-1]["receipt_state"], "stopped")
        saved = _read_exec_journal(journal_path)["entries"][_exec_journal_key(request["action_id"], request["attempt_id"])]
        self.assertEqual(saved["state"], "stopped")

    def test_bridge_timeout_after_prepare_becomes_unknown_without_a_second_spawn(self) -> None:
        self.install_policy()
        action = self.action()
        receipts: list[dict[str, object]] = []
        bridge_calls: list[dict[str, object]] = []

        def request_fn(_url: str, path: str, payload: dict[str, object], _authorization: str | None = None) -> dict[str, object]:
            if path.endswith("/exec-stops"):
                return {"stop_requests": []}
            if path.endswith("/poll"):
                return {"actions": [action] if not receipts else []}
            self.assertTrue(path.endswith("/receipts"))
            receipts.append(payload)
            return {"receipt_id": f"receipt-exec-timeout-{len(receipts):04d}"}

        def bridge(_args: object, _project_root: Path, control: dict[str, object]) -> tuple[None, str]:
            bridge_calls.append(control)
            return None, "CONTROL_PLANE_EXEC_TIMEOUT"

        with mock.patch("control_plane.node_agent._request", side_effect=request_fn), \
             mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch("control_plane.node_agent.recovery_exec_bridge", side_effect=bridge), \
             mock.patch("control_plane.node_agent._run_bounded_exec") as runner, \
             redirect_stdout(io.StringIO()):
            self.assertEqual(poll_exec_once(self.args()), 0)

        self.assertEqual(len(bridge_calls), 1)
        runner.assert_not_called()
        self.assertEqual(receipts[0]["receipt_state"], "unknown")
        self.assertEqual(receipts[0]["payload"]["code"], "CONTROL_PLANE_EXEC_EFFECT_UNKNOWN")
        self.assertEqual(receipts[0]["payload"]["diagnostic_code"], "CONTROL_PLANE_EXEC_TIMEOUT")
        journal_path = self.config_path.with_name(f"{self.config_path.name}.exec-journal.json")
        saved = _read_exec_journal(journal_path)["entries"][_exec_journal_key(action["action_id"], action["attempt_id"])]
        self.assertEqual(saved["state"], "unknown")

        # A later poll observes the durable unknown receipt, but it must not
        # dequeue or spawn the action a second time.
        with mock.patch("control_plane.node_agent._request", side_effect=request_fn), \
             mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch("control_plane.node_agent.recovery_exec_bridge", side_effect=bridge), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(poll_exec_once(self.args()), 0)
        self.assertEqual(len(bridge_calls), 1)
        self.assertEqual(len(receipts), 1)

    def test_bridge_unavailable_after_prepare_is_not_misclassified_as_rejected(self) -> None:
        self.install_policy()
        action = self.action(action_id="act-node-bridge-unavailable-0001", attempt_id="try-node-bridge-unavailable-0001")
        receipts: list[dict[str, object]] = []

        def request_fn(_url: str, path: str, payload: dict[str, object], _authorization: str | None = None) -> dict[str, object]:
            if path.endswith("/exec-stops"):
                return {"stop_requests": []}
            if path.endswith("/poll"):
                return {"actions": [action] if not receipts else []}
            self.assertTrue(path.endswith("/receipts"))
            receipts.append(payload)
            return {"receipt_id": "receipt-exec-unavailable-0001"}

        with mock.patch("control_plane.node_agent._request", side_effect=request_fn), \
             mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch("control_plane.node_agent.recovery_exec_bridge", return_value=(None, "CONTROL_PLANE_EXEC_UNAVAILABLE")), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(poll_exec_once(self.args()), 0)

        self.assertEqual(len(receipts), 1)
        self.assertEqual(receipts[0]["receipt_state"], "unknown")
        self.assertEqual(receipts[0]["payload"]["code"], "CONTROL_PLANE_EXEC_EFFECT_UNKNOWN")
        self.assertEqual(receipts[0]["payload"]["diagnostic_code"], "CONTROL_PLANE_EXEC_UNAVAILABLE")
        saved = _read_exec_journal(self.config_path.with_name(f"{self.config_path.name}.exec-journal.json"))[
            "entries"
        ][_exec_journal_key(action["action_id"], action["attempt_id"])]
        self.assertEqual(saved["state"], "unknown")

    def test_running_job_bridge_timeout_stays_running_until_a_later_terminal_observation(self) -> None:
        journal_path, _journal, request, running_result = self.running_journal()
        terminal = self.bridge_result(
            request,
            status="exited",
            local_handle=running_result["local_handle"],
            command_id=running_result["command_id"],
            job_id=running_result["job_id"],
            policy_sha256=running_result["policy_sha256"],
        )
        bridge_calls: list[str] = []
        receipts: list[dict[str, object]] = []

        def request_fn(_url: str, path: str, payload: dict[str, object], _authorization: str | None = None) -> dict[str, object]:
            if path.endswith("/exec-stops"):
                return {"stop_requests": []}
            if path.endswith("/poll"):
                return {"actions": []}
            self.assertTrue(path.endswith("/receipts"))
            receipts.append(payload)
            return {"receipt_id": "receipt-exec-running-timeout-0001"}

        def bridge(_args: object, _project_root: Path, control: dict[str, object]) -> tuple[dict[str, object] | None, str | None]:
            bridge_calls.append(str(control["operation"]))
            if len(bridge_calls) == 1:
                return None, "CONTROL_PLANE_EXEC_TIMEOUT"
            return terminal, None

        with mock.patch("control_plane.node_agent._request", side_effect=request_fn), \
             mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch("control_plane.node_agent.recovery_exec_bridge", side_effect=bridge), \
             mock.patch("control_plane.node_agent._run_bounded_exec") as runner, \
             redirect_stdout(io.StringIO()):
            self.assertEqual(poll_exec_once(self.args()), 0)

        runner.assert_not_called()
        self.assertEqual(bridge_calls, ["exec_poll"])
        saved = _read_exec_journal(journal_path)["entries"][_exec_journal_key(request["action_id"], request["attempt_id"])]
        self.assertEqual(saved["state"], "running")
        self.assertEqual(saved["last_control_error"], "CONTROL_PLANE_EXEC_TIMEOUT")
        self.assertEqual(receipts, [])

        with mock.patch("control_plane.node_agent._request", side_effect=request_fn), \
             mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch("control_plane.node_agent.recovery_exec_bridge", side_effect=bridge), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(poll_exec_once(self.args()), 0)
        self.assertEqual(bridge_calls, ["exec_poll", "exec_poll"])
        self.assertEqual(receipts[0]["receipt_state"], "completed")
        self.assertEqual(
            _read_exec_journal(journal_path)["entries"][_exec_journal_key(request["action_id"], request["attempt_id"])]["state"],
            "completed",
        )

    def test_stop_bridge_timeout_keeps_stop_pending_until_terminal_and_acknowledged(self) -> None:
        journal_path, _journal, request, running_result = self.running_journal()
        running = self.bridge_result(
            request,
            status="running",
            local_handle=running_result["local_handle"],
            command_id=running_result["command_id"],
            job_id=running_result["job_id"],
            policy_sha256=running_result["policy_sha256"],
        )
        stopped = self.bridge_result(
            request,
            status="stopped",
            local_handle=running_result["local_handle"],
            command_id=running_result["command_id"],
            job_id=running_result["job_id"],
            policy_sha256=running_result["policy_sha256"],
        )
        bridge_calls: list[str] = []
        paths: list[str] = []
        receipts: list[dict[str, object]] = []

        def request_fn(_url: str, path: str, payload: dict[str, object], _authorization: str | None = None) -> dict[str, object]:
            paths.append(path)
            if path.endswith("/exec-stops"):
                return {"stop_requests": [{"action_id": request["action_id"]}]}
            if path.endswith("/acknowledge"):
                return {"action_id": request["action_id"], "state": "acknowledged"}
            if path.endswith("/poll"):
                return {"actions": []}
            self.assertTrue(path.endswith("/receipts"))
            receipts.append(payload)
            return {"receipt_id": f"receipt-exec-stop-timeout-{len(receipts):04d}"}

        def bridge(_args: object, _project_root: Path, control: dict[str, object]) -> tuple[dict[str, object] | None, str | None]:
            operation = str(control["operation"])
            bridge_calls.append(operation)
            if operation == "exec_poll":
                return running, None
            if len([item for item in bridge_calls if item == "exec_stop"]) == 1:
                return None, "CONTROL_PLANE_EXEC_TIMEOUT"
            return stopped, None

        with mock.patch("control_plane.node_agent._request", side_effect=request_fn), \
             mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch("control_plane.node_agent.recovery_exec_bridge", side_effect=bridge), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(poll_exec_once(self.args()), 0)
        self.assertEqual(bridge_calls, ["exec_poll", "exec_stop"])
        self.assertFalse(any(path.endswith("/acknowledge") for path in paths))
        self.assertEqual(
            _read_exec_journal(journal_path)["entries"][_exec_journal_key(request["action_id"], request["attempt_id"])]["state"],
            "running",
        )

        with mock.patch("control_plane.node_agent._request", side_effect=request_fn), \
             mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch("control_plane.node_agent.recovery_exec_bridge", side_effect=bridge), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(poll_exec_once(self.args()), 0)
        self.assertEqual(bridge_calls, ["exec_poll", "exec_stop", "exec_poll", "exec_stop"])
        self.assertTrue(any(path.endswith("/acknowledge") for path in paths))
        self.assertEqual(receipts[-1]["receipt_state"], "stopped")

    def test_terminal_receipt_ack_loss_replays_same_receipt_without_relaying_job(self) -> None:
        journal_path, _journal, request, running_result = self.running_journal()
        terminal = self.bridge_result(
            request,
            status="exited",
            local_handle=running_result["local_handle"],
            command_id=running_result["command_id"],
            job_id=running_result["job_id"],
            policy_sha256=running_result["policy_sha256"],
        )
        bridge_calls: list[str] = []
        submitted: list[dict[str, object]] = []

        def first_request(_url: str, path: str, _payload: dict[str, object], _authorization: str | None = None) -> dict[str, object]:
            if path.endswith("/exec-stops"):
                return {"stop_requests": []}
            if path.endswith("/poll"):
                return {"actions": []}
            raise OSError("receipt acknowledgement lost")

        def bridge(_args: object, _project_root: Path, control: dict[str, object]) -> tuple[dict[str, object], None]:
            bridge_calls.append(str(control["operation"]))
            return terminal, None

        with mock.patch("control_plane.node_agent._request", side_effect=first_request), \
             mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch("control_plane.node_agent.recovery_exec_bridge", side_effect=bridge), \
             self.assertRaises(OSError), \
             redirect_stdout(io.StringIO()):
            poll_exec_once(self.args())

        saved_before = _read_exec_journal(journal_path)["entries"][_exec_journal_key(request["action_id"], request["attempt_id"])]
        self.assertEqual(saved_before["state"], "completed")
        self.assertFalse(saved_before["receipt"]["receipt_submitted"])
        self.assertEqual(bridge_calls, ["exec_poll"])

        def retry_request(_url: str, path: str, payload: dict[str, object], _authorization: str | None = None) -> dict[str, object]:
            if path.endswith("/receipts"):
                submitted.append(payload)
                return {"receipt_id": "receipt-exec-ack-retry-0001"}
            if path.endswith("/exec-stops"):
                return {"stop_requests": []}
            if path.endswith("/poll"):
                return {"actions": []}
            raise AssertionError(path)

        with mock.patch("control_plane.node_agent._request", side_effect=retry_request), \
             mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch("control_plane.node_agent.recovery_exec_bridge", side_effect=bridge), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(poll_exec_once(self.args()), 0)
        self.assertEqual(bridge_calls, ["exec_poll"])
        self.assertEqual(len(submitted), 1)
        self.assertEqual(submitted[0]["payload"], saved_before["receipt"]["payload"])
        self.assertTrue(
            _read_exec_journal(journal_path)["entries"][_exec_journal_key(request["action_id"], request["attempt_id"])]["receipt"]["receipt_submitted"]
        )


if __name__ == "__main__":
    unittest.main()
