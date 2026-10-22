"""Exec node policy, allowlist, workspace lock and bounded runner."""

from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from control_plane.node_agent import (
    _admit_exec_policy_request,
    _exec_bridge_request,
    _exec_control_request,
    _exec_allowlist_match,
    _exec_argv_item,
    _exec_journal_key,
    _flush_exec_journal,
    _normalise_exec_policy,
    _policy_digest,
    _read_exec_journal,
    _record_exec_receipt,
    _run_bounded_exec,
    _safe_exec_bridge_result,
    _write_json_atomic,
    disable_exec_policy,
    install_exec_policy,
    inspect_exec_policy,
    main,
    poll_exec_once,
    recovery_exec_bridge,
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

    def test_optional_routing_preserves_old_policy_and_rejects_unsafe_native_prefixes(self) -> None:
        old = _policy()
        self.assertEqual(_normalise_exec_policy(old), old)
        explicit = _policy(execution_mode="native_only", native_argv_prefixes=[["npm", "test"]])
        self.assertEqual(_normalise_exec_policy(explicit), explicit)
        self.assertNotEqual(_policy_digest(old), _policy_digest(explicit))
        for invalid in (None, [["C:/tools/node.exe"]], [["npm", "test"], ["npm", "test"]], [["npm", "test;whoami"]]):
            with self.subTest(prefixes=invalid), self.assertRaisesRegex(RuntimeError, "^CONTROL_PLANE_EXEC_POLICY_INVALID$"):
                _normalise_exec_policy(_policy(native_argv_prefixes=invalid))
        with self.assertRaisesRegex(RuntimeError, "^CONTROL_PLANE_EXEC_POLICY_INVALID$"):
            _normalise_exec_policy(_policy(execution_mode="unrestricted"))


class BoundedRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="exec-runner-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_success_and_output_caps(self) -> None:
        result, error = _run_bounded_exec(
            argv=[sys.executable, "-c", "print('hello-exec')"], cwd_path=self.root,
            timeout_ms=10000, max_output_bytes=32768)
        self.assertIsNone(error)
        assert result is not None
        self.assertEqual(result["exit_code"], 0)
        self.assertIn("hello-exec", result["stdout"])

    def test_timeout_reports_typed_uncertainty_or_timeout(self) -> None:
        result, error = _run_bounded_exec(
            argv=[sys.executable, "-c", "import time; time.sleep(30)"], cwd_path=self.root,
            timeout_ms=5000, max_output_bytes=32768)
        # Either a timed-out result or a typed cleanup-uncertain error; never silent.
        self.assertTrue((result is not None and result.get("timed_out")) or error is not None)

    def test_verified_stop_kills_tree(self) -> None:
        calls = {"n": 0}

        def _stop_check() -> bool:
            calls["n"] += 1
            return calls["n"] >= 3

        result, error = _run_bounded_exec(
            argv=[sys.executable, "-c", "import time; time.sleep(30)"], cwd_path=self.root,
            timeout_ms=60000, max_output_bytes=32768, stop_check=_stop_check)
        self.assertIsNone(error)
        assert result is not None
        self.assertTrue(result.get("stopped"))

    def test_shell_is_never_used(self) -> None:
        # If shell were used, echo would expand; with shell=False the literal runs.
        result, error = _run_bounded_exec(
            argv=[sys.executable, "-c", "import sys; sys.stdout.write(';rm')"], cwd_path=self.root,
            timeout_ms=10000, max_output_bytes=32768)
        self.assertIsNone(error)
        assert result is not None
        self.assertIn(";rm", result["stdout"])


class RecoveryExecBridgeTimeoutTests(unittest.TestCase):
    def test_cold_start_budget_is_only_used_for_initial_exec(self) -> None:
        args = SimpleNamespace(timeout_seconds=17)
        for operation, expected_timeout in (("exec_run", 360), ("exec_poll", 17), ("exec_stop", 17)):
            with self.subTest(operation=operation), \
                 mock.patch("control_plane.node_agent._adapter_command", return_value=(["node", "bridge"], {})), \
                 mock.patch("control_plane.node_agent.subprocess.run", return_value=SimpleNamespace(
                     returncode=0, stdout=b'{"ok":true,"result":{"status":"running"}}')) as run:
                result, error = recovery_exec_bridge(args, Path(__file__).parent, {"operation": operation})
                self.assertIsNone(error)
                self.assertEqual(result, {"status": "running"})
                self.assertEqual(run.call_args.kwargs["timeout"], expected_timeout)
                self.assertTrue(run.call_args.kwargs["capture_output"])

    def test_cold_start_timeout_keeps_the_typed_unknown_effect_boundary(self) -> None:
        with mock.patch("control_plane.node_agent._adapter_command", return_value=(["node", "bridge"], {})), \
             mock.patch("control_plane.node_agent.subprocess.run", side_effect=subprocess.TimeoutExpired("node", 360)):
            result, error = recovery_exec_bridge(SimpleNamespace(timeout_seconds=17), Path(__file__).parent,
                                                 {"operation": "exec_run"})
        self.assertIsNone(result)
        self.assertEqual(error, "CONTROL_PLANE_EXEC_TIMEOUT")

    def test_bridge_keeps_only_typed_native_diagnostics_and_authenticated_correlation(self) -> None:
        finished = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        error = {
            "code": "CONTROL_PLANE_EXEC_MCP_REJECTED",
            "recovery_response_received": True,
            "action_id": "act-exec-node-0001", "attempt_id": "try-exec-node-0001",
            "task_id": "task_" + "a" * 32, "writer_lease_generation": 1,
            "message": "private runtime message",
            "details": {
                "native_error_code": "SANDBOX_STATE_PHASE_FAILED", "phase": "state",
                "backend_error_code": "MXC_STATE_PHASE_FAILED",
                "command_id": "-4hBa9tkNAYi4ngWamUIO4Ba", "job_id": "job-exec-0001",
                "job_lifecycle": "spawn_failed", "root_pid": 0, "execution_started": False,
                "job_finished_at": finished, "path": "private/path", "stdout": "private output",
            },
        }
        with mock.patch("control_plane.node_agent._adapter_command", return_value=(["node", "bridge"], {})), \
             mock.patch("control_plane.node_agent.subprocess.run", return_value=SimpleNamespace(
                 returncode=1, stdout=json.dumps({"ok": False, "error": error}).encode())):
            result, diagnostic = recovery_exec_bridge(SimpleNamespace(timeout_seconds=17), Path(__file__).parent,
                                                       {"operation": "exec_run"})
        self.assertIsNone(result)
        self.assertEqual(diagnostic, {field: value for field, value in error.items() if field != "message"} | {
            "details": {field: value for field, value in error["details"].items() if field not in {"path", "stdout"}}
        })


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

    def test_inspect_reports_installed_facade_without_changing_policy(self) -> None:
        self.install_policy()
        policy_path = self.data_root / "control-plane-exec-policy.json"
        before = policy_path.read_bytes()
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(inspect_exec_policy(self.args()), 0)
        receipt = json.loads(output.getvalue())
        self.assertEqual(receipt["facade_contract"], FACADE)
        self.assertEqual(receipt["state"], "enabled")
        self.assertEqual(receipt["execution_mode"], "native_first")
        self.assertEqual(receipt["native_argv_prefixes"], [])
        self.assertEqual(policy_path.read_bytes(), before)
        self.assertNotIn(self.config["node_secret"], output.getvalue())

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

    def test_cli_requires_explicit_confirmation_to_disable_standing_exec(self) -> None:
        policy_path = self.data_root / "control-plane-exec-policy.json"
        self.install_policy()
        with redirect_stderr(io.StringIO()) as error:
            self.assertEqual(main([
                "disable-exec-policy",
                "--data-root", str(self.data_root),
                "--project-root", str(self.workspace),
            ]), 1)
        self.assertIn("CONTROL_PLANE_EXEC_POLICY_DISABLE_CONFIRMATION_REQUIRED", error.getvalue())
        self.assertTrue(json.loads(policy_path.read_text(encoding="utf-8"))["enabled"])

    def test_cli_install_and_inspection_preserve_explicit_native_routing_policy(self) -> None:
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(self.exec_policy_cli_args() + [
                "--execution-mode", "native_only", "--native-argv-prefix", '["python","-m","pytest"]',
            ]), 0)
        installed = json.loads(output.getvalue())
        self.assertEqual(installed["execution_mode"], "native_only")
        self.assertEqual(installed["native_argv_prefixes"], [["python", "-m", "pytest"]])
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(inspect_exec_policy(self.args()), 0)
        inspected = json.loads(output.getvalue())
        self.assertEqual(inspected["execution_mode"], installed["execution_mode"])
        self.assertEqual(inspected["native_argv_prefixes"], installed["native_argv_prefixes"])
        self.assertEqual(inspected["policy_sha256"], installed["policy_sha256"])

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
            "command_id": "_aJumSgZyYU90Yj_Mt7qu-Gp",
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

    @staticmethod
    def native_bridge_error(request: dict[str, object]) -> dict[str, object]:
        return {
            "code": "CONTROL_PLANE_EXEC_MCP_REJECTED", "recovery_response_received": True,
            **{field: request[field] for field in ("action_id", "attempt_id", "task_id", "writer_lease_generation")},
            "details": {
                "native_error_code": "SANDBOX_STATE_PHASE_FAILED", "phase": "state",
                "backend_error_code": "MXC_STATE_PHASE_FAILED",
                "command_id": "_aJumSgZyYU90Yj_Mt7qu-Gp", "job_id": "job-exec-0001",
                "job_lifecycle": "spawn_failed", "root_pid": 0, "execution_started": False,
                "job_finished_at": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            },
        }

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

    def test_native_command_tokens_remain_exact_across_terminal_and_control_results(self) -> None:
        policy = self.install_policy()
        request = _exec_bridge_request(self.action(), self.config)
        policy_sha256 = _policy_digest(policy)
        for command_id in ("-4hBa9tkNAYi4ngWamUIO4Ba", "_aJumSgZyYU90Yj_Mt7qu-Gp"):
            with self.subTest(command_id=command_id):
                result = self.bridge_result(
                    request, status="exited", local_handle="cp_exec_" + "a" * 48,
                    command_id=command_id, job_id="job-exec-node-0001", policy_sha256=policy_sha256,
                )
                self.assertEqual(_safe_exec_bridge_result(result, request, policy_sha256)["command_id"], command_id)
                for operation, status in (("exec_poll", "running"), ("exec_stop", "stopped")):
                    control = _exec_control_request(
                        request, result, operation=operation,
                        **({"signal": "TERM", "wait_ms": 3000} if operation == "exec_stop" else {}),
                    )
                    self.assertEqual(_admit_exec_policy_request(
                        self.args(), config_path=self.config_path, config=self.config, request=control,
                    )["workspace_id"], request["workspace_id"])
                    response = self.bridge_result(
                        control, status=status, local_handle=result["local_handle"], command_id=command_id,
                        job_id=result["job_id"], policy_sha256=policy_sha256,
                    )
                    self.assertEqual(_safe_exec_bridge_result(response, control, policy_sha256)["command_id"], command_id)
                    drift = {**response, "command_id": "different-command-id"}
                    with self.assertRaisesRegex(RuntimeError, "^CONTROL_PLANE_EXEC_RESULT_ENVELOPE_INVALID$"):
                        _safe_exec_bridge_result(drift, control, policy_sha256)
                for invalid in ("/invalid", "-bad/id", "-bad id", "-ba\nd", "-" * 257, "-x"):
                    with self.assertRaisesRegex(RuntimeError, "^CONTROL_PLANE_EXEC_RESULT_ENVELOPE_INVALID$"):
                        _safe_exec_bridge_result({**result, "command_id": invalid}, request, policy_sha256)
        with self.assertRaises(RuntimeError):
            _normalise_exec_policy(self.policy(workspace_id="_workspace-invalid"))

    def test_exec_backend_metadata_is_verified_and_preserved_in_durable_receipts(self) -> None:
        policy = self.install_policy()
        request = _exec_bridge_request(self.action(), self.config)
        policy_sha256 = _policy_digest(policy)
        result = self.bridge_result(
            request, status="exited", local_handle="cp_exec_" + "a" * 48,
            command_id="command-exec-node-0001", job_id="job-exec-node-0001", policy_sha256=policy_sha256,
        )
        output_keys = ("status", "exit_code", "stdout", "stderr", "truncated", "timed_out",
                       "command_id", "job_id", "run_id", "wave_id", "output_refs")
        output = {key: result[key] for key in output_keys}
        self.assertNotIn("execution_backend", _safe_exec_bridge_result(result, request, policy_sha256))
        metadata = {"execution_backend": "native", "isolation_level": "process_container", "policy_decision": "native_explicit_approval"}
        updated = {**result, **metadata, "response_sha256": __import__("hashlib").sha256(json.dumps(
            {**output, **metadata}, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")).hexdigest()}
        safe = _safe_exec_bridge_result(updated, request, policy_sha256)
        journal_path = self.config_path.with_name(self.config_path.name + ".exec-journal.json")
        _record_exec_receipt(journal_path, {"schema_version": 1, "entries": {}}, state="completed",
                             action_id=request["action_id"], attempt_id=request["attempt_id"], receipt_state="completed",
                             local_handle=safe["local_handle"], payload=safe)
        saved = _read_exec_journal(journal_path)["entries"][_exec_journal_key(request["action_id"], request["attempt_id"])]
        self.assertEqual(saved["receipt"]["payload"]["execution_backend"], "native")
        with self.assertRaisesRegex(RuntimeError, "^CONTROL_PLANE_EXEC_RESULT_DIGEST_INVALID$"):
            _safe_exec_bridge_result({**updated, "policy_decision": "native_safe_command"}, request, policy_sha256)
        for metadata_drift in ({"execution_backend": "native"}, {**metadata, "isolation_level": "hypervisor"}):
            with self.subTest(metadata=metadata_drift), self.assertRaisesRegex(RuntimeError, "^CONTROL_PLANE_EXEC_RESULT_METADATA_INVALID$"):
                _safe_exec_bridge_result({**result, **metadata_drift}, request, policy_sha256)

    def test_local_host_metadata_is_verified_and_preserved_in_durable_receipts(self) -> None:
        policy = self.install_policy()
        request = _exec_bridge_request(self.action(), self.config)
        policy_sha256 = _policy_digest(policy)
        result = self.bridge_result(
            request, status="exited", local_handle="cp_exec_" + "b" * 48,
            command_id="command-local-node-0001", job_id="job-local-node-0001", policy_sha256=policy_sha256,
        )
        metadata = {"execution_backend": "local", "isolation_level": "host_user", "policy_decision": "operator_local"}
        output_keys = ("status", "exit_code", "stdout", "stderr", "truncated", "timed_out",
                       "command_id", "job_id", "run_id", "wave_id", "output_refs")
        output = {key: result[key] for key in output_keys}
        updated = {**result, **metadata, "response_sha256": __import__("hashlib").sha256(json.dumps(
            {**output, **metadata}, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")).hexdigest()}
        safe = _safe_exec_bridge_result(updated, request, policy_sha256)
        journal_path = self.config_path.with_name(self.config_path.name + ".exec-journal.json")
        _record_exec_receipt(journal_path, {"schema_version": 1, "entries": {}}, state="completed",
                             action_id=request["action_id"], attempt_id=request["attempt_id"], receipt_state="completed",
                             local_handle=safe["local_handle"], payload=safe)
        saved = _read_exec_journal(journal_path)["entries"][_exec_journal_key(request["action_id"], request["attempt_id"])]
        self.assertEqual(saved["receipt"]["payload"]["isolation_level"], "host_user")
        for drift in ({"isolation_level": "process_container"}, {"policy_decision": "native_explicit_approval"}):
            with self.subTest(metadata=drift), self.assertRaisesRegex(RuntimeError, "^CONTROL_PLANE_EXEC_RESULT_METADATA_INVALID$"):
                _safe_exec_bridge_result({**updated, **drift}, request, policy_sha256)
        with self.assertRaisesRegex(RuntimeError, "^CONTROL_PLANE_EXEC_RESULT_DIGEST_INVALID$"):
            _safe_exec_bridge_result({**updated, "response_sha256": result["response_sha256"]}, request, policy_sha256)

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
            "command_id": "-4hBa9tkNAYi4ngWamUIO4Ba",
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
        self.assertEqual(bridge_requests[0]["yield_time_ms"], 0)
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

    def test_exact_native_spawn_failure_is_terminal_and_ack_retry_does_not_spawn(self) -> None:
        self.install_policy()
        action = self.action()
        receipts: list[dict[str, object]] = []
        bridge_calls: list[dict[str, object]] = []

        def request_fn(_url: str, path: str, payload: dict[str, object], _authorization: str | None = None) -> dict[str, object]:
            if path.endswith("/exec-stops"):
                return {"stop_requests": []}
            if path.endswith("/poll"):
                return {"actions": [action]}
            self.assertTrue(path.endswith("/receipts"))
            receipts.append(payload)
            if len(receipts) == 1:
                raise RuntimeError("TEST_RECEIPT_ACK_LOST")
            return {"receipt_id": "receipt-exec-spawn-failed-0001"}

        def bridge(_args: object, _root: Path, control: dict[str, object]) -> tuple[None, dict[str, object]]:
            bridge_calls.append(control)
            return None, self.native_bridge_error(control)

        with mock.patch("control_plane.node_agent._request", side_effect=request_fn), \
             mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch("control_plane.node_agent.recovery_exec_bridge", side_effect=bridge), \
             mock.patch("control_plane.node_agent._run_bounded_exec") as runner, redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(RuntimeError, "^TEST_RECEIPT_ACK_LOST$"):
                poll_exec_once(self.args())
            journal_path = self.config_path.with_name(f"{self.config_path.name}.exec-journal.json")
            saved = _read_exec_journal(journal_path)["entries"][_exec_journal_key(action["action_id"], action["attempt_id"])]
            self.assertEqual(saved["state"], "failed")
            self.assertFalse(saved["receipt"]["receipt_submitted"])
            self.assertEqual(poll_exec_once(self.args()), 0)
        runner.assert_not_called()
        self.assertEqual(len(bridge_calls), 1)
        self.assertEqual(receipts[0], receipts[1])
        self.assertEqual(receipts[0]["receipt_state"], "failed")
        payload = receipts[0]["payload"]
        self.assertEqual(payload["code"], "CONTROL_PLANE_EXEC_FAILED_BEFORE_PROCESS")
        self.assertEqual(payload["diagnostic_code"], "SANDBOX_STATE_PHASE_FAILED")
        self.assertEqual(payload["bridge_error_code"], "CONTROL_PLANE_EXEC_MCP_REJECTED")
        self.assertEqual(payload["native_error_code"], "SANDBOX_STATE_PHASE_FAILED")
        self.assertEqual(payload["job_lifecycle"], "spawn_failed")
        self.assertNotIn("exit_code", payload)
        self.assertNotIn("stdout", payload)

    def test_incomplete_or_wrongly_correlated_native_failure_stays_unknown(self) -> None:
        self.install_policy()
        variants = (
            ("code_only", {"details": {"native_error_code": "SANDBOX_STATE_PHASE_FAILED"}}),
            ("no_provenance", {"recovery_response_received": False}),
            ("wrong_action", {"action_id": "act-another-0001"}),
            ("wrong_attempt", {"attempt_id": "try-another-0001"}),
            ("wrong_task", {"task_id": "task_" + "b" * 32}),
            ("bool_generation", {"writer_lease_generation": True}),
            ("bool_pid", {"details.root_pid": False}),
            ("live_pid", {"details.root_pid": 123}),
            ("started", {"details.execution_started": True}),
            ("not_terminal", {"details.job_lifecycle": "running"}),
            ("wrong_job_type", {"details.job_id": []}),
            ("invalid_finished", {"details.job_finished_at": "2026-02-30T00:00:00Z"}),
            ("future_finished", {"details.job_finished_at": "2999-01-01T00:00:00Z"}),
        )
        for index, (name, changes) in enumerate(variants):
            with self.subTest(name=name):
                action = self.action(action_id=f"act-exec-failure-{index:04d}", attempt_id=f"try-exec-failure-{index:04d}")
                receipts: list[dict[str, object]] = []

                def request_fn(_url: str, path: str, payload: dict[str, object], _authorization: str | None = None) -> dict[str, object]:
                    if path.endswith("/exec-stops"):
                        return {"stop_requests": []}
                    if path.endswith("/poll"):
                        return {"actions": [action]}
                    receipts.append(payload)
                    return {"receipt_id": f"receipt-exec-failure-{index:04d}"}

                def bridge(_args: object, _root: Path, control: dict[str, object]) -> tuple[None, dict[str, object]]:
                    error = self.native_bridge_error(control)
                    for field, value in changes.items():
                        if field.startswith("details."):
                            error["details"][field.removeprefix("details.")] = value
                        else:
                            error[field] = value
                    return None, error

                with mock.patch("control_plane.node_agent._request", side_effect=request_fn), \
                     mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
                     mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
                     mock.patch("control_plane.node_agent.recovery_exec_bridge", side_effect=bridge) as bridge_mock, \
                     redirect_stdout(io.StringIO()):
                    self.assertEqual(poll_exec_once(self.args()), 0)
                    self.assertEqual(poll_exec_once(self.args()), 0)
                self.assertEqual(bridge_mock.call_count, 1)
                self.assertEqual(len(receipts), 1)
                self.assertEqual(receipts[0]["receipt_state"], "unknown")
                self.assertEqual(receipts[0]["payload"]["diagnostic_code"], "CONTROL_PLANE_EXEC_MCP_REJECTED")
                self.assertEqual(receipts[0]["payload"]["native_error_code"], "SANDBOX_STATE_PHASE_FAILED")

    def test_control_error_keeps_diagnostics_without_undoing_a_running_process(self) -> None:
        journal_path, _journal, request, running_result = self.running_journal()
        receipts: list[dict[str, object]] = []

        def request_fn(_url: str, path: str, payload: dict[str, object], _authorization: str | None = None) -> dict[str, object]:
            if path.endswith("/exec-stops"):
                return {"stop_requests": []}
            if path.endswith("/poll"):
                return {"actions": []}
            receipts.append(payload)
            return {"receipt_id": "receipt-control-native-error-0001"}

        def bridge(_args: object, _root: Path, control: dict[str, object]) -> tuple[None, dict[str, object]]:
            error = self.native_bridge_error(control)
            # Even a plausible no-process snapshot cannot overwrite the
            # durable evidence that this command had a running process.
            error["details"]["command_id"] = running_result["command_id"]
            error["details"]["job_id"] = running_result["job_id"]
            return None, error

        with mock.patch("control_plane.node_agent._request", side_effect=request_fn), \
             mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
             mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
             mock.patch("control_plane.node_agent.recovery_exec_bridge", side_effect=bridge), redirect_stdout(io.StringIO()):
            self.assertEqual(poll_exec_once(self.args()), 0)
        self.assertEqual(receipts[0]["receipt_state"], "unknown")
        self.assertEqual(receipts[0]["payload"]["native_error_code"], "SANDBOX_STATE_PHASE_FAILED")
        saved = _read_exec_journal(journal_path)["entries"][_exec_journal_key(request["action_id"], request["attempt_id"])]
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

    def test_recovery_reconciles_backend_metadata_loss_or_drift_without_respawn(self) -> None:
        output_keys = ("status", "exit_code", "stdout", "stderr", "truncated", "timed_out",
                       "command_id", "job_id", "run_id", "wave_id", "output_refs")
        metadata = {"execution_backend": "native", "isolation_level": "process_container", "policy_decision": "native_explicit_approval"}
        for changed in ({}, {**metadata, "policy_decision": "native_safe_command"}):
            with self.subTest(metadata=changed):
                journal_path, journal, request, running = self.running_journal()
                running.update(metadata)
                running["response_sha256"] = __import__("hashlib").sha256(json.dumps(
                    {**{key: running[key] for key in output_keys}, **metadata},
                    ensure_ascii=False, sort_keys=True, separators=(",", ":")
                ).encode("utf-8")).hexdigest()
                _write_json_atomic(journal_path, journal)
                terminal = self.bridge_result(request, status="exited", local_handle=running["local_handle"],
                    command_id=running["command_id"], job_id=running["job_id"], policy_sha256=running["policy_sha256"])
                terminal.update(changed)
                terminal["response_sha256"] = __import__("hashlib").sha256(json.dumps(
                    {**{key: terminal[key] for key in output_keys}, **changed},
                    ensure_ascii=False, sort_keys=True, separators=(",", ":")
                ).encode("utf-8")).hexdigest()
                receipts = []
                def request_fn(_url, request_path, payload, _authorization=None):
                    if request_path.endswith("/exec-stops"):
                        return {"stop_requests": []}
                    if request_path.endswith("/poll"):
                        return {"actions": []}
                    receipts.append(payload)
                    return {"receipt_id": "receipt-metadata-reconcile-0001"}
                with mock.patch("control_plane.node_agent._request", side_effect=request_fn), \
                     mock.patch("control_plane.node_agent._runtime_status", return_value=self.strict_status()), \
                     mock.patch("control_plane.node_agent.recovery_identity_observation", return_value=self.strict_identity()), \
                     mock.patch("control_plane.node_agent.recovery_exec_bridge", return_value=(terminal, None)) as bridge, \
                     mock.patch("control_plane.node_agent._run_bounded_exec") as runner, redirect_stdout(io.StringIO()):
                    self.assertEqual(poll_exec_once(self.args()), 0)
                runner.assert_not_called()
                self.assertEqual(bridge.call_args.args[2]["operation"], "exec_poll")
                self.assertEqual(receipts[0]["receipt_state"], "unknown")
                self.assertEqual(receipts[0]["payload"]["code"], "CONTROL_PLANE_EXEC_RESULT_METADATA_INVALID")

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
