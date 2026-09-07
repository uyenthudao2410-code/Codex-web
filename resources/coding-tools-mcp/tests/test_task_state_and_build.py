from __future__ import annotations

# The package path is intentionally inserted before local imports.
# ruff: noqa: E402

import json
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[1]
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

import coding_tools_mcp.server as server_module
import coding_tools_mcp.coordination as coordination_module
import coding_tools_mcp.task_state as task_state_module
from coding_tools_mcp.build_verify import collect_artifacts, detect_project
from coding_tools_mcp.errors import JsonRpcError, ToolFailure
from coding_tools_mcp.task_state import TaskStateStore, classify_command, command_payload_succeeded
from coding_tools_mcp.server import Runtime
from coding_tools_mcp.restart_ticket import build_supervisor_restart_ticket, supervisor_restart_ticket_matches
from coding_tools_mcp.textutils import DEFAULT_MAX_LINES, truncate_text_head
from coding_tools_mcp.tool_schema import validate_arguments
from coding_tools_mcp.protocol import dispatch_rpc
from coding_tools_mcp.document_tools import create_docx, extract_docx


class TaskStateTests(unittest.TestCase):
    def test_command_success_requires_explicit_success_terminal_lifecycle(self) -> None:
        cases = (
            ("exited", True),
            ("completed", True),
            ("passed", True),
            ("", False),
            ("running", False),
            ("quiesced", False),
            ("terminated", False),
            ("timed_out", False),
        )
        for lifecycle, expected in cases:
            with self.subTest(lifecycle=lifecycle):
                self.assertEqual(
                    command_payload_succeeded({"status": lifecycle, "exit_code": 0}),
                    expected,
                )

    def test_atomic_state_replace_retries_transient_windows_access_denial(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            store = TaskStateStore(root)
            original_replace = task_state_module.os.replace
            attempts = 0

            def transient_replace(source, target):
                nonlocal attempts
                attempts += 1
                if attempts < 3:
                    raise PermissionError(13, "transient sharing violation")
                return original_replace(source, target)

            with (
                patch.object(task_state_module.os, "name", "nt"),
                patch.object(task_state_module.os, "replace", side_effect=transient_replace),
                patch.object(task_state_module.time, "sleep") as sleep,
            ):
                state = store.update({"objective": "Retry transient state replace"})

            self.assertEqual(attempts, 3)
            self.assertEqual([call.args[0] for call in sleep.call_args_list], [0.025, 0.05])
            self.assertEqual(state["objective"], "Retry transient state replace")
            self.assertEqual(TaskStateStore(root).get()["objective"], "Retry transient state replace")

    def test_atomic_state_replace_does_not_retry_nonretryable_error_and_cleans_temp(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            store = TaskStateStore(root)
            failure = FileNotFoundError(2, "non-retryable replace failure")
            with (
                patch.object(task_state_module.os, "name", "nt"),
                patch.object(task_state_module.os, "replace", side_effect=failure) as replace,
                patch.object(task_state_module.time, "sleep") as sleep,
            ):
                with self.assertRaises(FileNotFoundError):
                    store.update({"objective": "Fail closed"})

            self.assertEqual(replace.call_count, 1)
            sleep.assert_not_called()
            self.assertEqual(list(store.state_dir.glob(".task-state.json.*.tmp")), [])

    def test_atomic_state_replace_exhausts_bounded_windows_retry_budget(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            store = TaskStateStore(root)
            failure = PermissionError(13, "persistent sharing violation")
            with (
                patch.object(task_state_module.os, "name", "nt"),
                patch.object(task_state_module.os, "replace", side_effect=failure) as replace,
                patch.object(task_state_module.time, "sleep") as sleep,
            ):
                with self.assertRaises(PermissionError):
                    store.update({"objective": "Exhaust retry budget"})

            self.assertEqual(replace.call_count, task_state_module.WINDOWS_ATOMIC_REPLACE_ATTEMPTS)
            self.assertEqual(
                [call.args[0] for call in sleep.call_args_list],
                [
                    task_state_module.WINDOWS_ATOMIC_REPLACE_BASE_DELAY_SECONDS * attempt
                    for attempt in range(1, task_state_module.WINDOWS_ATOMIC_REPLACE_ATTEMPTS)
                ],
            )
            self.assertEqual(list(store.state_dir.glob(".task-state.json.*.tmp")), [])

    def test_anonymous_tool_calls_do_not_create_a_task_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            store = TaskStateStore(root)
            store.record_tool_result(
                "apply_patch",
                {"patch": "..."},
                {"ok": False, "error": {"message": "Cannot add file that already exists."}},
            )
            self.assertFalse(store.path.exists())

    def test_state_survives_new_store_and_tracks_results(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            store = TaskStateStore(root)
            store.update({"objective": "Ship release", "steps": ["test", "build"], "next_step": "test"})
            store.record_command_started("npm test", "session-one", ".")
            store.record_tool_result(
                "exec_command",
                {"cmd": "npm test"},
                {"ok": True, "status": "exited", "session_id": "session-one", "exit_code": 0, "elapsed_ms": 25},
            )
            store.record_tool_result(
                "apply_patch",
                {"patch": "..."},
                {"ok": True, "affected_files": [{"path": "src/app.js", "operation": "update"}]},
            )
            restored = TaskStateStore(root).get()
            self.assertEqual(restored["objective"], "Ship release")
            self.assertEqual(restored["test_results"][-1]["status"], "passed")
            self.assertEqual(restored["modified_files"], [{"path": "src/app.js", "operation": "update", "updated_at": restored["modified_files"][0]["updated_at"]}])

    def test_timeout_payload_with_exit_zero_is_never_recorded_as_passed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            store = TaskStateStore(root)
            store.update({"objective": "Timeout must fail closed"})
            store.record_command_started("python -m pytest -q", "timeout-command", ".")
            store.record_tool_result(
                "exec_command",
                {"cmd": "python -m pytest -q"},
                {
                    "ok": True,
                    "status": "timeout",
                    "session_id": "timeout-command",
                    "exit_code": 0,
                    "elapsed_ms": 1000,
                    "timed_out": True,
                    "summary": "terminated at deadline",
                },
            )
            state = store.get()
            self.assertEqual(state["test_results"][-1]["status"], "failed")
            self.assertEqual(state["status"], "failed")

    def test_agent_workflow_records_nested_execution_affected_files_for_final_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            store = TaskStateStore(root)
            store.update({"objective": "Accepted workflow must retain component scope"})
            store.record_tool_result(
                "agent_workflow",
                {"phase": "execute", "workflow": "feature"},
                {
                    "ok": True,
                    "phase": "execute",
                    "execution": {
                        "affected_files": [
                            {"path": "electron/services/recoveryHost.js", "operation": "modified"},
                            {"path": "electron/services/recoveryActionStore.js", "operation": "modified"},
                        ],
                    },
                },
            )
            modified = TaskStateStore(root).get()["modified_files"]
            self.assertEqual(
                [(item["path"], item["operation"]) for item in modified],
                [
                    ("electron/services/recoveryHost.js", "modified"),
                    ("electron/services/recoveryActionStore.js", "modified"),
                ],
            )

    def test_command_output_artifact_ref_survives_task_state_without_persisting_raw_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            store = TaskStateStore(root)
            store.update({"objective": "Preserve command evidence"})
            store.record_command_started("python -m pytest -q", "command-one", ".")
            raw_output = "sensitive-large-output-that-must-not-enter-artifact-ref"
            store.record_tool_result(
                "exec_command",
                {"cmd": "python -m pytest -q"},
                {
                    "ok": True,
                    "status": "exited",
                    "command_id": "command-one",
                    "session_id": "command-one",
                    "exit_code": 0,
                    "elapsed_ms": 42,
                    "summary": "42 tests passed",
                    "stdout": raw_output,
                    "output_refs": {
                        "stdout": "command:command-one:stdout",
                        "stderr": "command:command-one:stderr",
                    },
                    "output_retention": {
                        "stdout": {
                            "total_stream_bytes": 120000,
                            "total_retained_bytes": 65536,
                            "head_retained_bytes": 8192,
                            "tail_retained_bytes": 57344,
                            "evicted_gap_bytes": 54464,
                            "evicted_bytes_total": 54464,
                        },
                        "stderr": {
                            "total_stream_bytes": 0,
                            "total_retained_bytes": 0,
                            "head_retained_bytes": 0,
                            "tail_retained_bytes": 0,
                            "evicted_gap_bytes": 0,
                            "evicted_bytes_total": 0,
                        },
                    },
                },
            )
            restored = TaskStateStore(root).get()
            result = restored["test_results"][-1]
            artifact = result["artifact_ref"]
            self.assertEqual(artifact["schema_version"], 1)
            self.assertEqual(artifact["kind"], "command_output")
            self.assertEqual(artifact["scope"], "runtime_retained")
            self.assertEqual(artifact["source"], "command")
            self.assertEqual(artifact["locator"], {"command_id": "command-one"})
            self.assertEqual(artifact["command_id"], "command-one")
            self.assertEqual(artifact["retrieval"], {"tool": "command_control", "action": "read"})
            self.assertEqual(artifact["durability"], "process_runtime")
            self.assertFalse(artifact["restart_safe"])
            self.assertFalse(artifact["content_addressed"])
            self.assertNotIn("owner_run", artifact)
            self.assertNotIn("owner_wave", artifact)
            self.assertEqual(artifact["streams"]["stdout"]["output_ref"], "command:command-one:stdout")
            self.assertEqual(artifact["streams"]["stdout"]["total_stream_bytes"], 120000)
            self.assertEqual(artifact["streams"]["stdout"]["evicted_gap_bytes"], 54464)
            self.assertNotIn(raw_output, json.dumps(artifact, ensure_ascii=False))
            self.assertEqual(result["summary"], "42 tests passed")

    def test_running_command_carries_artifact_ref_for_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            store = TaskStateStore(Path(temp))
            store.update({
                "objective": "Long running proof",
                "orchestration": {
                    "orchestration_state": "EXECUTING",
                    "run_id": "run-proof",
                    "wave_id": "wave-proof",
                },
            })
            store.record_command_started(
                "npm test",
                "command-running",
                ".",
                owner_run_id="run-proof",
                owner_wave_id="wave-proof",
            )
            store.record_tool_result(
                "exec_command",
                {"cmd": "npm test"},
                {
                    "ok": True,
                    "status": "running",
                    "command_id": "command-running",
                    "session_id": "command-running",
                    "execution_owner": {"run_id": "run-proof", "wave_id": "wave-proof"},
                    "output_refs": {"stdout": "command:command-running:stdout"},
                    "output_retention": {"stdout": {"total_stream_bytes": 10, "total_retained_bytes": 10}},
                },
            )
            current = TaskStateStore(Path(temp)).get()["current_command"]
            self.assertEqual(current["artifact_ref"]["streams"]["stdout"]["output_ref"], "command:command-running:stdout")
            self.assertFalse(current["artifact_ref"]["restart_safe"])
            self.assertEqual(current["artifact_ref"]["owner_run"], "run-proof")
            self.assertEqual(current["artifact_ref"]["owner_wave"], "wave-proof")
            store.record_tool_result(
                "command_control",
                {"action": "poll", "command_id": "command-running"},
                {
                    "ok": True,
                    "status": "exited",
                    "command_id": "command-running",
                    "session_id": "command-running",
                    "exit_code": 0,
                    "elapsed_ms": 100,
                    "summary": "tests complete",
                    "output_refs": {"stdout": "command:command-running:stdout"},
                    "output_retention": {"stdout": {"total_stream_bytes": 20, "total_retained_bytes": 20}},
                },
            )
            terminal = TaskStateStore(Path(temp)).get()
            self.assertIsNone(terminal["current_command"])
            self.assertEqual(
                terminal["test_results"][-1]["artifact_ref"]["streams"]["stdout"]["output_ref"],
                "command:command-running:stdout",
            )
            self.assertEqual(terminal["test_results"][-1]["artifact_ref"]["owner_run"], "run-proof")
            self.assertEqual(terminal["test_results"][-1]["artifact_ref"]["owner_wave"], "wave-proof")

    def test_command_control_terminal_poll_terminalizes_current_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            store = TaskStateStore(root)
            store.update({"objective": "Poll public command control"})
            store.record_command_started("npm test", "command-public", ".")
            store.record_tool_result(
                "command_control",
                {"action": "poll", "command_id": "command-public"},
                {
                    "ok": True,
                    "status": "exited",
                    "command_id": "command-public",
                    "session_id": "command-public",
                    "exit_code": 0,
                    "elapsed_ms": 55,
                    "summary": "95 tests passed",
                    "output_refs": {
                        "stdout": "command:command-public:stdout",
                        "stderr": "command:command-public:stderr",
                    },
                    "output_retention": {
                        "stdout": {"total_stream_bytes": 20, "total_retained_bytes": 20},
                        "stderr": {"total_stream_bytes": 0, "total_retained_bytes": 0},
                    },
                },
            )
            terminal = TaskStateStore(root).get()
            self.assertIsNone(terminal["current_command"])
            self.assertEqual(terminal["status"], "waiting")
            self.assertEqual(terminal["test_results"][-1]["status"], "passed")
            self.assertEqual(
                terminal["test_results"][-1]["artifact_ref"]["streams"]["stdout"]["output_ref"],
                "command:command-public:stdout",
            )
            self.assertEqual(terminal["events"][-1]["event"], "command_finished")

    def test_public_terminal_command_control_requires_operator_report_and_recovers_lost_handle(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = Runtime(root)
            runtime.task_state.update({"objective": "Long delivery command", "status": "active"})
            runtime.task_state.record_command_started("delivery-helper", "command-delivery", ".")
            payload = {
                "ok": True,
                "status": "exited",
                "command_id": "command-delivery",
                "session_id": "command-delivery",
                "exit_code": 0,
                "elapsed_ms": 42,
                "summary": "sensitive raw output must not enter report",
            }
            runtime._record_task_tool_result(
                "command_control",
                {"action": "poll", "command_id": "command-delivery"},
                payload,
            )
            report = payload["completion_report"]
            self.assertTrue(payload["operator_visible_required"])
            self.assertTrue(report["operator_visible_required"])
            self.assertEqual(report["command_id"], "command-delivery")
            self.assertEqual(report["accepted_or_not"], "COMMAND_COMPLETED_AWAITING_OPERATOR_REPORT")
            self.assertFalse(report["what_changed"]["raw_source_or_command_output_included"])
            self.assertNotIn("sensitive raw output", json.dumps(report))
            durable = runtime.task_state.get()
            self.assertEqual(durable["completion_report"]["command_id"], "command-delivery")
            self.assertIn("operator report required", durable["current_step"].lower())

            recovered = runtime.command_control({"action": "poll", "command_id": "command-delivery"})
            self.assertTrue(recovered["reconciled"])
            self.assertTrue(recovered["operator_visible_required"])
            self.assertEqual(recovered["completion_report"]["command_id"], "command-delivery")
            runtime.close()

    def test_command_control_recovers_exact_terminal_managed_job_without_live_handle(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))
            try:
                admission = runtime.execution_resource_governor.admit(
                    command="git rev-parse HEAD",
                    command_id="durable-only-command",
                    resource_class="LIGHT",
                )
                runtime.execution_resource_governor.complete(
                    admission.job_id,
                    lifecycle_state="exited",
                    exit_code=0,
                )

                recovered = runtime.command_control(
                    {"action": "poll", "command_id": "durable-only-command"}
                )
                self.assertEqual(recovered["status"], "reconciled_terminal")
                self.assertEqual(recovered["job_id"], admission.job_id)
                self.assertEqual(recovered["exit_code"], 0)
                self.assertEqual(recovered["result_status"], "succeeded")
                self.assertEqual(
                    recovered["reconciled_sources"], ["managed_process_job"]
                )
                self.assertNotIn("completion_report", recovered)
            finally:
                runtime.close()

    def test_failed_plain_exec_requires_operator_report_but_active_eocl_does_not(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = Runtime(root)
            runtime.task_state.update({"objective": "Failing command", "status": "active"})
            failed = {"ok": False, "status": "failed", "session_id": "command-failed", "exit_code": 7, "elapsed_ms": 3}
            runtime._record_task_tool_result("exec_command", {"cmd": "failing-command"}, failed)
            self.assertTrue(failed["operator_visible_required"])
            self.assertEqual(failed["completion_report"]["accepted_or_not"], "COMMAND_FAILED")

            runtime.task_state.update({
                "objective": "EOCL owned command",
                "status": "active",
                "orchestration": {"orchestration_state": "EXECUTING", "run_id": "run-live", "wave_id": "wave-live"},
            })
            runtime.task_state.record_command_started("another-command", "command-eocl", ".")
            eocl_payload = {"ok": True, "status": "exited", "command_id": "command-eocl", "session_id": "command-eocl", "exit_code": 0, "elapsed_ms": 1}
            runtime._record_task_tool_result("command_control", {"action": "poll", "command_id": "command-eocl"}, eocl_payload)
            self.assertNotIn("completion_report", eocl_payload)
            self.assertEqual(runtime.task_state.get()["orchestration"]["orchestration_state"], "EXECUTING")
            runtime.close()

    def test_command_classification(self) -> None:
        self.assertEqual(classify_command("python -m pytest -q"), "test")
        self.assertEqual(classify_command("npm run build"), "build")
        self.assertEqual(classify_command("git status"), "command")

    def test_task_id_pause_resume_and_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            store = TaskStateStore(Path(temp))
            first = store.update({"objective": "First task", "next_step": "edit"})
            self.assertTrue(first["task_id"])
            paused = store.pause("user requested")
            self.assertEqual(paused["status"], "paused")
            self.assertEqual(paused["pause_reason"], "user requested")
            resumed = store.resume("test")
            self.assertEqual(resumed["status"], "active")
            self.assertEqual(resumed["next_step"], "test")
            second = store.update({"objective": "Second task", "new_task": True})
            self.assertNotEqual(first["task_id"], second["task_id"])
            history = store.history()
            self.assertEqual(history[0]["task_id"], first["task_id"])
            self.assertEqual(history[0]["archive_reason"], "superseded")

    def test_clear_archives_current_task(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            store = TaskStateStore(Path(temp))
            state = store.update({"objective": "Archive me"})
            store.clear()
            self.assertFalse(store.path.exists())
            self.assertEqual(store.history()[0]["task_id"], state["task_id"])


class BackgroundOperationTests(unittest.TestCase):
    def test_long_agent_workflow_hands_back_and_can_be_polled(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp))

            def slow_result(name, arguments, request_id=None):
                del name, arguments, request_id
                time.sleep(0.05)
                return {"done": True}

            with patch.object(server_module, "LONG_TOOL_HANDOFF_SECONDS", 0.01), patch.object(
                runtime, "_call_tool_sync", side_effect=slow_result
            ):
                first = runtime.call_tool("agent_workflow", {"phase": "run"})
                structured = first["structuredContent"]
                self.assertEqual(structured["status"], "running")
                self.assertTrue(structured["requires_progress_report"])
                operation_id = structured["background_operation"]["operation_id"]
                polled = runtime.task_control({"action": "operation", "operation_id": operation_id, "wait_ms": 1000})
                self.assertEqual(polled["background_operation"]["status"], "completed")
                self.assertEqual(polled["background_operation"]["result"], {"done": True})
            runtime.close()


class BuildVerificationTests(unittest.TestCase):
    def test_verify_build_projects_content_addressed_workspace_artifact_ref(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            artifact_path = root / "dist" / "app.bin"
            artifact_path.parent.mkdir(parents=True)
            artifact_path.write_bytes(b"verified-build-artifact")
            runtime = Runtime(root, permission_mode="dangerous")
            try:
                report = runtime.verify_build({
                    "path": ".",
                    "run_tests": False,
                    "run_build": False,
                    "artifact_paths": ["dist/app.bin"],
                    "hash_algorithm": "sha256",
                })
                self.assertTrue(report["ok"])
                self.assertEqual(len(report["artifacts"]), 1)
                artifact = report["artifacts"][0]
                ref = artifact["artifact_ref"]
                self.assertEqual(ref["kind"], "build_artifact")
                self.assertEqual(ref["scope"], "workspace_file")
                self.assertEqual(ref["locator"], {"path": "dist/app.bin"})
                self.assertEqual(ref["retrieval"], {"scheme": "workspace_path", "path": "dist/app.bin"})
                self.assertTrue(ref["restart_safe"])
                self.assertTrue(ref["content_addressed"])
                self.assertEqual(ref["sha256"], artifact["sha256"])
                self.assertEqual(ref["content_hash"], artifact["sha256"])
                self.assertEqual(runtime.task_state.get()["last_build_report"]["artifacts"][0]["artifact_ref"], ref)
            finally:
                runtime.close()

    def test_verify_build_requires_success_terminal_lifecycle_for_exit_zero(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp), permission_mode="dangerous")
            try:
                cases = (
                    ("exited", "passed"),
                    ("completed", "passed"),
                    ("passed", "passed"),
                    ("", "failed"),
                    ("quiesced", "failed"),
                    ("terminated", "failed"),
                    ("timed_out", "failed"),
                )
                for lifecycle, expected in cases:
                    terminal = {
                        "ok": True,
                        "status": lifecycle,
                        "session_id": f"verify-build-{lifecycle}",
                        "exit_code": 0,
                        "elapsed_ms": 1,
                    }
                    with self.subTest(lifecycle=lifecycle), patch.object(
                        runtime,
                        "exec_command",
                        return_value=terminal,
                    ):
                        report = runtime.verify_build({
                            "path": ".",
                            "run_tests": True,
                            "run_build": False,
                            "test_command": "python -m pytest -q",
                        })
                    self.assertEqual(report["test_result"]["status"], expected)
                    self.assertEqual(report["overall_status"], expected)
                    self.assertEqual(report["ok"], expected == "passed")
            finally:
                runtime.close()

    def test_detects_node_project_and_hashes_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "package.json").write_text(
                json.dumps({"name": "demo", "version": "1.2.0", "scripts": {"test": "node --test", "build": "node build.js"}}),
                encoding="utf-8",
            )
            project = detect_project(root)
            self.assertEqual(project["type"], "node")
            self.assertEqual(project["version"], "1.2.0")
            artifact = root / "dist" / "demo.exe"
            artifact.parent.mkdir()
            artifact.write_bytes(b"artifact")
            artifacts = collect_artifacts(root, ["dist"], "sha256", 0)
            self.assertEqual(artifacts[0]["path"], "dist/demo.exe")
            self.assertEqual(len(artifacts[0]["sha256"]), 64)


class ToolModeTests(unittest.TestCase):
    def test_windows_core_environment_keeps_required_os_paths(self) -> None:
        required = {"SYSTEMDRIVE", "PROGRAMDATA", "ALLUSERSPROFILE", "SYSTEMROOT", "USERPROFILE", "PUBLIC"}
        self.assertTrue(required.issubset(server_module.WINDOWS_CORE_ENV_NAMES))

    def test_tool_modes_expose_expected_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.dict("os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "readonly"}):
                readonly = set(Runtime(root)._exposed_tool_names)
            with patch.dict("os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "coding"}):
                coding = set(Runtime(root)._exposed_tool_names)
            with patch.dict("os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "build"}):
                build = set(Runtime(root)._exposed_tool_names)
            with patch.dict("os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "full"}):
                full = set(Runtime(root)._exposed_tool_names)
            self.assertIn("read_file", readonly)
            self.assertNotIn("apply_patch", readonly)
            self.assertIn("apply_patch", coding)
            self.assertIn("verify_build", coding)
            self.assertIn("verify_build", build)
            self.assertNotIn("apply_patch", build)
            self.assertGreater(len(full), len(coding))

    def test_smart_mode_is_compact_and_contains_batch_document_tools(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict("os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
            runtime = Runtime(Path(temp))
            tools = set(runtime.exposed_tool_names())
            self.assertLessEqual(len(tools), 8)
            self.assertEqual(tools, {"workspace_context", "agent_workflow", "task_control", "document_workflow", "exec_command", "command_control", "request_permissions", "view_image"})
            self.assertNotIn("document_extract", tools)
            task_schema = server_module.input_schemas()["task_control"]
            self.assertIn("restart_runtime", task_schema["properties"]["action"]["enum"])
            self.assertIn("solution_shadow", task_schema["properties"]["action"]["enum"])
            self.assertIn("confirm_restart", task_schema["properties"])
            self.assertIn("solution_shadow_recommendation", task_schema["properties"])

    def test_permission_elicitation_fallback_is_explicit_and_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp), permission_mode="safe")
            try:
                runtime.task_state.update({"objective": "permission status probe", "status": "active"})
                result = runtime.call_tool("request_permissions", {
                    "tool_name": "exec_command",
                    "permission": "long_timeout",
                    "reason": "test",
                    "arguments": {"cmd": "echo ok"},
                })
                structured = result["structuredContent"]
                self.assertFalse(result["isError"])
                self.assertTrue(structured["ok"])
                self.assertEqual(structured["status"], "unsupported")
                self.assertIsNone(structured["grant_id"])
                self.assertEqual(structured["error"]["code"], "ELICITATION_UNSUPPORTED")
                self.assertFalse(structured["fallback"]["granted"])
                self.assertTrue(structured["fallback"]["fail_closed"])
                self.assertEqual(structured["fallback"]["mode"], "server_policy")
                self.assertIsNone(runtime.task_state.get()["failure"])
            finally:
                runtime.close()

    def test_restart_runtime_requires_confirmation_and_enqueues_supervisor_ticket(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / "workspace"
            control = root / "control"
            workspace.mkdir()
            control.mkdir()
            ticket_path = control / "runtime-supervisor-request.json"
            with patch.dict("os.environ", {"CODING_TOOLS_MCP_SUPERVISOR_REQUEST_FILE": str(ticket_path)}):
                runtime = Runtime(workspace, permission_mode="safe")
                try:
                    with self.assertRaises(ToolFailure) as missing_confirmation:
                        runtime.task_control({"action": "restart_runtime"})
                    self.assertEqual(missing_confirmation.exception.code, "RESTART_CONFIRMATION_REQUIRED")
                    # Even an opaque random suffix that begins with characters
                    # forbidden at operation-id position zero must be made
                    # canonical by the restart producer.
                    with patch.object(coordination_module.secrets, "token_urlsafe", return_value="__unsafe-leading"):
                        result = runtime.task_control({
                            "action": "restart_runtime",
                            "confirm_restart": True,
                            "reason": "focused test",
                        })
                    self.assertTrue(result["accepted"])
                    self.assertTrue(result["expected_disconnect"])
                    self.assertTrue(ticket_path.is_file())
                    ticket = json.loads(ticket_path.read_text(encoding="utf-8"))
                    self.assertEqual(ticket["action"], "restart")
                    self.assertEqual(ticket["workspace"], str(workspace.resolve()))
                    self.assertEqual(ticket["ticket_id"], result["restart_ticket"])
                    self.assertEqual(ticket["operation_id"], result["restart_ticket"])
                    self.assertRegex(result["restart_ticket"], r"^[A-Za-z0-9][A-Za-z0-9_-]{15,127}$")
                    self.assertTrue(result["restart_ticket"].startswith("restart-"))
                    self.assertEqual(ticket["activation_mode"], "full_clean_activation")
                    self.assertTrue(ticket["full_clean_required"])
                    self.assertGreater(ticket["not_before_unix_ms"], ticket["requested_at_unix_ms"])
                    self.assertGreater(ticket["expires_at_unix_ms"], ticket["not_before_unix_ms"])
                    replay = runtime.task_control({"action": "restart_runtime", "confirm_restart": True})
                    self.assertTrue(replay["already_pending"])
                    self.assertEqual(replay["restart_ticket"], result["restart_ticket"])
                finally:
                    runtime.close()

    def test_restart_ticket_write_failure_releases_the_exact_new_fence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / "workspace"
            control = root / "control"
            workspace.mkdir()
            control.mkdir()
            ticket_path = control / "runtime-supervisor-request.json"
            with patch.dict("os.environ", {"CODING_TOOLS_MCP_SUPERVISOR_REQUEST_FILE": str(ticket_path)}):
                runtime = Runtime(workspace, permission_mode="safe")
                try:
                    with (
                        patch.object(coordination_module.secrets, "token_urlsafe", return_value="write-failure-0001"),
                        patch.object(coordination_module.os, "replace", side_effect=OSError("replace failed")),
                        self.assertRaises(ToolFailure) as raised,
                    ):
                        runtime._enqueue_runtime_restart({"confirm_restart": True})
                    self.assertEqual(raised.exception.code, "SUPERVISOR_REQUEST_FAILED")
                    self.assertIsNone(runtime.activation_fence)
                    self.assertFalse(ticket_path.exists())
                    self.assertEqual(list(control.iterdir()), [])
                finally:
                    runtime.close()

    def test_restart_ticket_replace_uncertainty_retains_fence_and_landed_ticket(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / "workspace"
            control = root / "control"
            workspace.mkdir()
            control.mkdir()
            ticket_path = control / "runtime-supervisor-request.json"
            original_replace = coordination_module.os.replace
            original_read_text = Path.read_text

            def replace_then_report_failure(source, target):
                original_replace(source, target)
                raise OSError("replace completion was not observable")

            def transient_confirmation_failure(path_value, *args, **kwargs):
                if path_value == ticket_path and ticket_path.exists():
                    raise OSError("temporary sharing violation")
                return original_read_text(path_value, *args, **kwargs)

            with patch.dict("os.environ", {"CODING_TOOLS_MCP_SUPERVISOR_REQUEST_FILE": str(ticket_path)}):
                runtime = Runtime(workspace, permission_mode="safe")
                try:
                    with (
                        patch.object(coordination_module.secrets, "token_urlsafe", return_value="uncertain-land-0001"),
                        patch.object(coordination_module.os, "replace", side_effect=replace_then_report_failure),
                        patch.object(Path, "read_text", new=transient_confirmation_failure),
                        self.assertRaises(ToolFailure) as raised,
                    ):
                        runtime._enqueue_runtime_restart({"confirm_restart": True})
                    self.assertEqual(raised.exception.code, "SUPERVISOR_REQUEST_STATE_UNCERTAIN")
                    self.assertEqual(
                        runtime.activation_fence["operation_id"],
                        "restart-uncertain-land-0001",
                    )
                    self.assertTrue(ticket_path.is_file())
                    self.assertEqual(
                        json.loads(original_read_text(ticket_path, encoding="utf-8"))["operation_id"],
                        "restart-uncertain-land-0001",
                    )
                    self.assertEqual(list(control.glob("*.tmp")), [])
                finally:
                    runtime.close()

    def test_restart_ticket_exact_expiry_is_not_reused(self) -> None:
        now_ms = 1_700_000_000_000
        ticket_id = "restart-expiry-boundary-0001"
        ticket = build_supervisor_restart_ticket(
            ticket_id=ticket_id,
            now_ms=now_ms - 1_000,
            workspace="C:\\work\\one",
            process_instance_id="process-one",
            server_instance_id="server-one",
            tool_contract_sha256="e" * 64,
            reason="expiry boundary",
        )
        ticket["expires_at_unix_ms"] = now_ms
        self.assertFalse(
            supervisor_restart_ticket_matches(
                ticket,
                now_ms=now_ms,
                workspace="C:\\work\\one",
                process_instance_id="process-one",
                server_instance_id="server-one",
                tool_contract_sha256="e" * 64,
                fence_operation_id=ticket_id,
            )
        )

    def test_existing_restart_ticket_is_not_reused_without_the_exact_live_fence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / "workspace"
            control = root / "control"
            workspace.mkdir()
            control.mkdir()
            ticket_path = control / "runtime-supervisor-request.json"
            with patch.dict("os.environ", {"CODING_TOOLS_MCP_SUPERVISOR_REQUEST_FILE": str(ticket_path)}):
                runtime = Runtime(workspace, permission_mode="safe")
                try:
                    with patch.object(coordination_module.secrets, "token_urlsafe", side_effect=("first-ticket-0001", "second-ticket-0002")):
                        first = runtime._enqueue_runtime_restart({"confirm_restart": True})
                        runtime.activation_fence = None
                        second = runtime._enqueue_runtime_restart({"confirm_restart": True})
                    self.assertFalse(second["already_pending"])
                    self.assertNotEqual(second["restart_ticket"], first["restart_ticket"])
                    self.assertEqual(
                        json.loads(ticket_path.read_text(encoding="utf-8"))["ticket_id"],
                        second["restart_ticket"],
                    )
                finally:
                    runtime.close()

    def test_concurrent_restart_requests_collapse_to_one_pending_ticket(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = root / "workspace"
            control = root / "control"
            workspace.mkdir()
            control.mkdir()
            ticket_path = control / "runtime-supervisor-request.json"
            with patch.dict("os.environ", {"CODING_TOOLS_MCP_SUPERVISOR_REQUEST_FILE": str(ticket_path)}):
                runtime = Runtime(workspace, permission_mode="safe")
                original_replace = server_module.os.replace
                active_replace = 0
                max_active_replace = 0
                replace_lock = threading.Lock()

                def delayed_replace(source, target):
                    nonlocal active_replace, max_active_replace
                    with replace_lock:
                        active_replace += 1
                        max_active_replace = max(max_active_replace, active_replace)
                    try:
                        time.sleep(0.05)
                        return original_replace(source, target)
                    finally:
                        with replace_lock:
                            active_replace -= 1

                try:
                    with patch.object(server_module.os, "replace", side_effect=delayed_replace):
                        with ThreadPoolExecutor(max_workers=4) as pool:
                            results = list(pool.map(
                                lambda _: runtime._enqueue_runtime_restart({"confirm_restart": True}),
                                range(4),
                            ))
                    ticket_ids = {result["restart_ticket"] for result in results}
                    self.assertEqual(ticket_ids, {json.loads(ticket_path.read_text(encoding="utf-8"))["ticket_id"]})
                    self.assertEqual(max_active_replace, 1)
                    self.assertEqual(sum(not result["already_pending"] for result in results), 1)
                finally:
                    runtime.close()

    def test_workspace_context_is_compact_and_cached(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict("os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
            root = Path(temp)
            (root / "app.py").write_text("print('ok')\n", encoding="utf-8")
            runtime = Runtime(root)
            first = runtime.workspace_context({})
            second = runtime.workspace_context({})
            self.assertEqual(first["detail"], "compact")
            self.assertFalse(first["cache"]["hit"])
            self.assertTrue(second["cache"]["hit"])
            self.assertNotIn("events", second["task"])

    def test_finished_command_moves_task_to_waiting(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            store = TaskStateStore(Path(temp))
            store.update({"objective": "Run a command", "status": "active"})
            store.record_command_started("echo ok", "session-one", ".")
            store.record_tool_result("exec_command", {"cmd": "echo ok"}, {"ok": True, "status": "exited", "session_id": "session-one", "exit_code": 0, "elapsed_ms": 1})
            self.assertEqual(store.get()["status"], "waiting")

    def test_terminal_orchestration_is_not_downgraded_by_command_housekeeping(self) -> None:
        for orchestration_state, task_status, current_step in (
            ("CHECKPOINTED", "completed", "Completed"),
            ("BLOCKED", "failed", "Blocked"),
            ("ABORTED", "stopped", "Aborted"),
        ):
            with self.subTest(orchestration_state=orchestration_state), tempfile.TemporaryDirectory() as temp:
                store = TaskStateStore(Path(temp))
                store.update({
                    "objective": "Terminal orchestration",
                    "status": task_status,
                    "current_step": current_step,
                    "next_step": "Terminal next step",
                    "failure": "terminal failure" if orchestration_state != "CHECKPOINTED" else None,
                    "orchestration": {"orchestration_state": orchestration_state, "run_id": "run-terminal"},
                })
                before = store.get()
                store.record_command_started("echo later", "session-terminal", ".")
                store.record_tool_result(
                    "exec_command",
                    {"cmd": "echo later"},
                    {"ok": True, "status": "exited", "session_id": "session-terminal", "exit_code": 0, "elapsed_ms": 1},
                )
                after = store.get()
                self.assertEqual(after["orchestration"]["orchestration_state"], orchestration_state)
                self.assertEqual(after["status"], before["status"])
                self.assertEqual(after["current_step"], before["current_step"])
                self.assertEqual(after["next_step"], before["next_step"])
                self.assertEqual(after["failure"], before["failure"])
                self.assertIsNone(after["current_command"])
                self.assertEqual(after["events"][-1]["event"], "command_finished")

    def test_terminal_orchestration_is_not_retroactively_failed_by_later_command_or_build(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            store = TaskStateStore(Path(temp))
            store.update({
                "objective": "Accepted orchestration",
                "status": "completed",
                "current_step": "Completed",
                "next_step": "Start next accepted behavior",
                "failure": None,
                "orchestration": {"orchestration_state": "CHECKPOINTED", "run_id": "run-accepted"},
            })
            store.record_command_started("cmd /c exit 7", "session-failed-later", ".")
            store.record_tool_result(
                "exec_command",
                {"cmd": "cmd /c exit 7"},
                {"ok": False, "status": "exited", "session_id": "session-failed-later", "exit_code": 7, "elapsed_ms": 1, "error": {"message": "later operator command failed"}},
            )
            store.record_build_report({"overall_status": "failed", "failure": "later build failed"})
            after = store.get()
            self.assertEqual(after["status"], "completed")
            self.assertEqual(after["current_step"], "Completed")
            self.assertEqual(after["next_step"], "Start next accepted behavior")
            self.assertIsNone(after["failure"])
            self.assertEqual(after["orchestration"]["orchestration_state"], "CHECKPOINTED")
            self.assertEqual(after["last_build_report"]["overall_status"], "failed")

    def test_prepare_coding_context_batches_search_reads_and_caches(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict("os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
            root = Path(temp)
            (root / "app.py").write_text("def greet():\n    return 'hello'\n", encoding="utf-8")
            runtime = Runtime(root)
            first = runtime.prepare_coding_context({"objective": "change greeting", "queries": ["greet"], "max_files": 4})
            second = runtime.prepare_coding_context({"objective": "change greeting", "queries": ["greet"], "max_files": 4})
            self.assertFalse(first["cache_hit"])
            self.assertTrue(second["cache_hit"])
            self.assertEqual(first["files"][0]["path"], "app.py")
            self.assertIn("hello", first["files"][0]["content"])

    def test_prepare_coding_context_max_lines_per_file_opt_in_materializes_2076_lines(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict("os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
            root = Path(temp)
            source = root / "large.py"
            source.write_text("".join(f"LINE_{index:04d} = {index}\n" for index in range(1, 2077)), encoding="utf-8")
            runtime = Runtime(root)
            try:
                bounded = runtime.prepare_coding_context({
                    "objective": "default bounded materialization",
                    "paths": ["large.py"],
                    "include_globs": ["large.py"],
                    "max_files": 1,
                    "max_total_bytes": 262144,
                    "force_refresh": True,
                })
                bounded_file = bounded["files"][0]
                self.assertTrue(bounded_file["truncated"])
                self.assertEqual(bounded_file["truncated_by"], "lines")
                self.assertEqual(bounded_file["output_lines"], 2000)
                self.assertEqual(bounded_file["total_lines"], 2076)
                self.assertEqual(bounded["composite_read"]["plan"]["limits"]["max_lines_per_file"], 2000)

                with patch.object(runtime, "prepare_coding_context", wraps=runtime.prepare_coding_context) as prepare:
                    expanded = runtime.agent_workflow({
                        "workflow": "diagnose",
                        "phase": "prepare",
                        "objective": "opt-in complete materialization",
                        "paths": ["large.py"],
                        "include_globs": ["large.py"],
                        "max_files": 1,
                        "max_total_bytes": 262144,
                        "max_lines_per_file": 2500,
                        "force_refresh": True,
                    })
                self.assertEqual(prepare.call_args.args[0]["max_lines_per_file"], 2500)
                expanded_file = expanded["context"]["files"][0]
                self.assertFalse(expanded_file["truncated"])
                self.assertIsNone(expanded_file["truncated_by"])
                self.assertEqual(expanded_file["output_lines"], 2076)
                self.assertEqual(expanded_file["total_lines"], 2076)
                self.assertEqual(expanded_file["output_bytes"], expanded_file["total_bytes"])
                self.assertIsNone(expanded_file["next_start_line"])
                self.assertEqual(expanded["context"]["composite_read"]["plan"]["limits"]["max_lines_per_file"], 2500)

                direct = runtime.read_file({"path": "large.py", "max_lines": 2500, "max_bytes": 262144})
                self.assertFalse(direct["truncated"])
                self.assertEqual(direct["output_lines"], 2076)
                with self.assertRaises(ToolFailure) as too_many_lines:
                    runtime.read_file({"path": "large.py", "max_lines": 5001})
                self.assertEqual(too_many_lines.exception.code, "INVALID_ARGUMENT")

                byte_limited = runtime.prepare_coding_context({
                    "objective": "opt-in remains byte bounded",
                    "paths": ["large.py"],
                    "include_globs": ["large.py"],
                    "max_files": 1,
                    "max_total_bytes": 4096,
                    "max_lines_per_file": 2500,
                    "force_refresh": True,
                })
                byte_limited_file = byte_limited["files"][0]
                self.assertTrue(byte_limited_file["truncated"])
                self.assertEqual(byte_limited_file["truncated_by"], "bytes")
                self.assertLessEqual(byte_limited_file["output_bytes"], 4096)
                self.assertLessEqual(byte_limited["total_content_bytes"], 4096)
            finally:
                runtime.close()

    def test_prepare_coding_context_projects_measured_composite_read_without_duplicating_query_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict("os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
            root = Path(temp)
            (root / "app.py").write_text("def greet():\n    return 'hello'\n", encoding="utf-8")
            runtime = Runtime(root)
            first = runtime.prepare_coding_context({
                "objective": "change greeting",
                "queries": ["greet", "hello"],
                "paths": ["app.py"],
                "max_files": 4,
                "max_total_bytes": 16384,
            })
            composite = first["composite_read"]
            self.assertEqual(composite["schema_version"], 1)
            self.assertEqual(composite["plan"]["mode"], "model_free")
            self.assertEqual(composite["plan"]["query_count"], 2)
            self.assertEqual(composite["plan"]["requested_path_count"], 1)
            self.assertEqual(len(composite["plan"]["plan_sha256"]), 64)
            operations = composite["execution"]["operations"]
            self.assertEqual([item["id"] for item in operations[:3]], ["workspace:0", "search:0", "search:1"])
            self.assertEqual([item["kind"] for item in operations[:3]], ["workspace_context", "search_text", "search_text"])
            self.assertTrue(any(item["kind"] == "read_file" and item["path"] == "app.py" for item in operations))
            self.assertEqual(composite["execution"]["content_bytes"], first["total_content_bytes"])
            self.assertEqual(
                sum(item.get("content_bytes", 0) for item in operations if item["kind"] == "read_file"),
                first["total_content_bytes"],
            )
            timing = composite["execution"]["phase_timing"]
            self.assertEqual(timing["source"], "monotonic_local")
            for key in ("workspace_ms", "localization_ms", "materialization_ms", "total_ms"):
                self.assertGreaterEqual(timing[key], 0)
            self.assertTrue(composite["execution"]["parallelism"]["search_parallel"])
            self.assertEqual(composite["execution"]["parallelism"]["search_max_workers"], 2)
            self.assertNotIn("greet", json.dumps(composite, ensure_ascii=False))
            self.assertNotIn("hello", json.dumps(composite, ensure_ascii=False))
            self.assertFalse(composite["cache"]["hit"])
            compact_prepare = first["task_resume"]
            self.assertNotIn("events", compact_prepare)
            self.assertNotIn("test_results", compact_prepare)
            self.assertNotIn("build_results", compact_prepare)

            second = runtime.prepare_coding_context({
                "objective": "change greeting",
                "queries": ["greet", "hello"],
                "paths": ["app.py"],
                "max_files": 4,
                "max_total_bytes": 16384,
            })
            self.assertTrue(second["cache_hit"])
            self.assertTrue(second["composite_read"]["cache"]["hit"])
            self.assertEqual(second["composite_read"]["cache"]["source"], "cached_previous_execution")
            self.assertEqual(second["composite_read"]["plan"]["plan_sha256"], composite["plan"]["plan_sha256"])

    def test_prepare_coding_context_prefers_semantic_provider_then_falls_back_per_query(self) -> None:
        semantic_paths = []

        class SemanticStub:
            def status(self):
                return {"available": True, "provider": "native-lsp-test", "read_only": True}

            def localize(self, *, workspace, path, queries, max_results, resource_class):
                del workspace, max_results, resource_class
                semantic_paths.append(path)
                return [
                    {
                        "query_index": 0,
                        "handled": True,
                        "matches": [{"path": "semantic.py", "line": 1, "kind": "definition", "symbol": queries[0]}],
                    },
                    {"query_index": 1, "handled": False, "matches": []},
                ]

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "semantic.py").write_text("def target_symbol():\n    return 1\n", encoding="utf-8")
            (root / "fallback.py").write_text("fallback_token = 2\n", encoding="utf-8")
            runtime = Runtime(root, semantic_localizer=SemanticStub())
            try:
                with patch.object(runtime, "search_text", wraps=runtime.search_text) as search_text:
                    result = runtime.prepare_coding_context({
                        "objective": "semantic localization",
                        "queries": ["target_symbol", "fallback_token"],
                        "paths": ["semantic.py"],
                        "max_files": 4,
                        "max_matches_per_query": 10,
                    })
                self.assertEqual(semantic_paths, ["semantic.py"])
                self.assertEqual(search_text.call_count, 1)
                self.assertEqual(search_text.call_args.args[0]["query"], "fallback_token")
                self.assertTrue(result["searches"][0]["engine"].startswith("semantic:"))
                self.assertEqual(result["searches"][0]["matches"][0]["path"], "semantic.py")
                localization = result["composite_read"]["execution"]["localization"]
                self.assertEqual(localization["semantic_attempted"], 2)
                self.assertEqual(localization["semantic_handled"], 1)
                self.assertEqual(localization["text_fallback_queries"], 1)
                self.assertEqual(localization["provider"]["provider"], "native-lsp-test")
                graph = localization["semantic_graph"]
                self.assertEqual(graph["schema_version"], 1)
                self.assertTrue(graph["read_only"])
                self.assertEqual(graph["provider"], "native-lsp-test")
                self.assertGreaterEqual(graph["indexed_records"], 2)
                self.assertGreaterEqual(graph["fallback_records"], 1)
                composite_text = json.dumps(result["composite_read"], ensure_ascii=False)
                self.assertNotIn("target_symbol", composite_text)
                self.assertNotIn("fallback_token", composite_text)
                self.assertIn("semantic.py", result["selected_paths"])
                self.assertIn("fallback.py", result["selected_paths"])
            finally:
                runtime.close()

    def test_prepare_coding_context_batches_native_queries_under_one_admission(self) -> None:
        semantic_batches: list[list[str]] = []

        class SemanticStub:
            def status(self):
                return {"available": True, "provider": "native-lsp-test", "read_only": True}

            def localize(self, *, workspace, path, queries, max_results, resource_class):
                del workspace, path, max_results, resource_class
                semantic_batches.append(list(queries))
                return [
                    {
                        "query_index": index,
                        "handled": query != "query-08",
                        "matches": ([] if query == "query-08" else [{"path": "semantic.py", "line": index + 1}]),
                    }
                    for index, query in enumerate(queries)
                ]

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            queries = [f"query-{index:02d}" for index in range(12)]
            (root / "semantic.py").write_text("\n".join(queries) + "\n", encoding="utf-8")
            runtime = Runtime(root, semantic_localizer=SemanticStub())
            try:
                with (
                    patch.object(
                        runtime.execution_resource_governor,
                        "semantic_native_claim",
                        wraps=runtime.execution_resource_governor.semantic_native_claim,
                    ) as native_claim,
                    patch.object(runtime, "search_text", wraps=runtime.search_text) as search_text,
                ):
                    result = runtime.prepare_coding_context({
                        "objective": "twelve semantic queries",
                        "queries": queries,
                        "paths": ["semantic.py"],
                        "max_files": 4,
                        "force_refresh": True,
                    })
                self.assertEqual(native_claim.call_count, 1)
                self.assertEqual(semantic_batches, [queries[:8], queries[8:]])
                self.assertEqual(search_text.call_count, 1)
                self.assertEqual(search_text.call_args.args[0]["query"], "query-08")
                localization = result["composite_read"]["execution"]["localization"]
                self.assertEqual(localization["semantic_attempted"], 12)
                self.assertEqual(localization["semantic_handled"], 11)
                self.assertEqual(localization["text_fallback_queries"], 1)
            finally:
                runtime.close()

    def test_prepare_coding_context_falls_back_before_native_call_during_heavy(self) -> None:
        semantic_calls = []

        class SemanticStub:
            def status(self):
                return {
                    "available": True,
                    "provider": "native-lsp-test",
                    "read_only": True,
                }

            def localize(self, *, workspace, path, queries, max_results, resource_class):
                del workspace, max_results, resource_class
                semantic_calls.append(path)
                return [
                    {
                        "query_index": 0,
                        "handled": True,
                        "matches": [
                            {
                                "path": "semantic.py",
                                "line": 1,
                                "kind": "definition",
                                "symbol": queries[0],
                            }
                        ],
                    }
                ]

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "semantic.py").write_text(
                "fallback_token = 2\n",
                encoding="utf-8",
            )
            runtime = Runtime(root, semantic_localizer=SemanticStub())
            try:
                run_id = runtime.orchestration_ledger.create_run(
                    objective="semantic admission conflict"
                )
                wave_id = runtime.orchestration_ledger.create_wave(
                    run_id,
                    execution_mode="mcp_only",
                )
                heavy = runtime.execution_resource_governor.admit(
                    command="cargo test",
                    command_id="semantic-admission-heavy",
                    run_id=run_id,
                    wave_id=wave_id,
                    resource_class="HEAVY",
                )
                with (
                    patch.object(
                        runtime.execution_resource_governor,
                        "_host_pressure",
                        return_value={"observed": True, "pressured": False},
                    ),
                    patch.object(
                        runtime.execution_resource_governor,
                        "_foreign_heavy_processes",
                        return_value=[],
                    ),
                ):
                    denied = runtime.prepare_coding_context(
                        {
                            "objective": "semantic conflict fallback",
                            "queries": ["fallback_token"],
                            "path": ".",
                            "max_files": 2,
                            "force_refresh": True,
                        }
                    )
                self.assertEqual(semantic_calls, [])
                denied_localization = denied["composite_read"]["execution"][
                    "localization"
                ]
                self.assertEqual(
                    denied_localization["native_admission"]["reason_code"],
                    "HEAVY_SLOT_BUSY",
                )
                self.assertEqual(denied_localization["semantic_attempted"], 0)
                self.assertEqual(denied_localization["text_fallback_queries"], 1)
                self.assertIn("semantic.py", denied["selected_paths"])

                (root / "src").mkdir()
                with (
                    patch.object(
                        runtime.execution_resource_governor,
                        "_host_pressure",
                        return_value={"observed": True, "pressured": False},
                    ),
                    patch.object(
                        runtime.execution_resource_governor,
                        "_foreign_heavy_processes",
                        return_value=[],
                    ),
                ):
                    directory_denied = runtime.prepare_coding_context(
                        {
                            "objective": "directory scope remains workspace heavy",
                            "queries": ["fallback_token"],
                            "path": "src",
                            "max_files": 2,
                            "force_refresh": True,
                        }
                    )
                directory_admission = directory_denied["composite_read"]["execution"][
                    "localization"
                ]["native_admission"]
                self.assertEqual(directory_admission["mode"], "workspace")
                self.assertEqual(directory_admission["cost"], "HEAVY")
                self.assertEqual(directory_admission["reason_code"], "HEAVY_SLOT_BUSY")
                self.assertEqual(semantic_calls, [])

                runtime.execution_resource_governor.complete(
                    heavy.job_id,
                    lifecycle_state="exited",
                    exit_code=0,
                )
                with (
                    patch.object(
                        runtime.execution_resource_governor,
                        "_host_pressure",
                        return_value={"observed": True, "pressured": False},
                    ),
                    patch.object(
                        runtime.execution_resource_governor,
                        "_foreign_heavy_processes",
                        return_value=[],
                    ),
                ):
                    recovered = runtime.prepare_coding_context(
                        {
                            "objective": "semantic conflict fallback",
                            "queries": ["fallback_token"],
                            "max_files": 2,
                            "force_refresh": True,
                        }
                    )
                self.assertEqual(semantic_calls, ["."])
                recovered_localization = recovered["composite_read"]["execution"][
                    "localization"
                ]
                self.assertTrue(recovered_localization["native_admission"]["allowed"])
                self.assertEqual(recovered_localization["semantic_handled"], 1)
                self.assertEqual(recovered_localization["text_fallback_queries"], 0)
            finally:
                runtime.close()

    def test_prepare_coding_context_releases_heavy_claim_after_provider_exception(self) -> None:
        class FailingSemanticStub:
            def status(self):
                return {
                    "available": True,
                    "provider": "native-lsp-test",
                    "read_only": True,
                }

            def localize(self, *, workspace, path, queries, max_results, resource_class):
                del workspace, path, queries, max_results, resource_class
                raise RuntimeError("provider failed")

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "semantic.py").write_text("fallback_token = 2\n", encoding="utf-8")
            runtime = Runtime(root, semantic_localizer=FailingSemanticStub())
            try:
                with (
                    patch.object(
                        runtime.execution_resource_governor,
                        "_host_pressure",
                        return_value={"observed": True, "pressured": False},
                    ),
                    patch.object(
                        runtime.execution_resource_governor,
                        "_foreign_heavy_processes",
                        return_value=[],
                    ),
                ):
                    result = runtime.prepare_coding_context(
                        {
                            "objective": "provider exception fallback",
                            "queries": ["fallback_token"],
                            "path": ".",
                            "max_files": 2,
                            "force_refresh": True,
                        }
                    )
                localization = result["composite_read"]["execution"]["localization"]
                self.assertEqual(
                    localization["provider"]["reason"],
                    "SEMANTIC_PROVIDER_CALL_FAILED",
                )
                self.assertEqual(localization["text_fallback_queries"], 1)
                self.assertEqual(
                    runtime.execution_resource_governor._claim_rows(active_only=True),
                    [],
                )
            finally:
                runtime.close()

    def test_continuous_check_terminalizes_internal_command_bookkeeping(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp), permission_mode="dangerous")
            try:
                runtime.task_state.update({"objective": "Internal proof bookkeeping", "status": "active"})
                result = runtime._run_continuous_check("python -m pytest --version", ".", 30_000)
                self.assertEqual(result["status"], "passed")
                state = runtime.task_state.get()
                self.assertIsNone(state["current_command"])
                self.assertEqual(state["events"][-1]["event"], "command_finished")
                self.assertEqual(state["test_results"][-1]["status"], "passed")
                artifact = state["test_results"][-1].get("artifact_ref")
                self.assertIsInstance(artifact, dict)
                self.assertFalse(artifact["restart_safe"])
                self.assertTrue(artifact["streams"]["stdout"]["output_ref"].startswith("command:"))
            finally:
                runtime.close()

    def test_continuous_check_timeout_exit_zero_is_not_proof_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp), permission_mode="dangerous")
            try:
                runtime.task_state.update({"objective": "Timeout proof classification", "status": "active"})
                terminal = {
                    "ok": True,
                    "status": "timeout",
                    "session_id": "timeout-proof",
                    "exit_code": 0,
                    "elapsed_ms": 25,
                    "timed_out": True,
                    "summary": "deadline",
                }
                with patch.object(runtime, "exec_command", return_value=terminal):
                    result = runtime._run_continuous_check("python -m pytest -q", ".", 30_000)
                self.assertEqual(result["status"], "timed_out")
                self.assertTrue(result["timed_out"])
                self.assertEqual(runtime.task_state.get()["test_results"][-1]["status"], "failed")
            finally:
                runtime.close()

    def test_continuous_check_caps_timeout_to_remaining_background_budget(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp), permission_mode="dangerous")
            try:
                runtime.task_state.update({"objective": "Cap proof to workflow budget", "status": "active"})
                terminal = {
                    "ok": True,
                    "status": "exited",
                    "session_id": "budget-capped-proof",
                    "exit_code": 0,
                    "elapsed_ms": 25,
                    "summary": "proof complete",
                }
                with (
                    patch.object(runtime, "_background_operation_remaining_seconds", return_value=8.0),
                    patch.object(runtime, "exec_command", return_value=terminal) as exec_command,
                ):
                    result = runtime._run_continuous_check("python -m pytest -q", ".", 30_000)
                self.assertEqual(result["status"], "passed")
                self.assertEqual(result["effective_timeout_ms"], 3_000)
                call = exec_command.call_args.args[0]
                self.assertEqual(call["timeout_ms"], 3_000)
                self.assertEqual(call["yield_time_ms"], 1_000)
            finally:
                runtime.close()

    def test_continuous_check_does_not_start_when_only_finalization_reserve_remains(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp), permission_mode="dangerous")
            try:
                with (
                    patch.object(runtime, "_background_operation_remaining_seconds", return_value=4.0),
                    patch.object(runtime, "exec_command") as exec_command,
                ):
                    result = runtime._run_continuous_check("python -m pytest -q", ".", 30_000)
                exec_command.assert_not_called()
                self.assertEqual(result["status"], "timed_out")
                self.assertTrue(result["timed_out"])
                self.assertFalse(result["cancelled"])
                self.assertFalse(result["command_started"])
                self.assertTrue(result["budget_limited"])
                self.assertEqual(result["effective_timeout_ms"], 0)
            finally:
                runtime.close()

    def test_cancelled_check_stops_following_checks_and_never_finalizes_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp), permission_mode="dangerous")
            try:
                cancelled = {
                    "command": "first",
                    "status": "cancelled",
                    "exit_code": 0,
                    "duration_ms": 1,
                    "summary": "budget expired",
                    "session_id": "cancelled-proof",
                    "cancelled": True,
                    "timed_out": True,
                }
                with patch.object(runtime, "_run_continuous_check", return_value=cancelled) as check:
                    result = runtime.apply_changes_and_verify({
                        "objective": "Stop proof sequence on cancellation",
                        "checks": ["first", "second"],
                        "verification": "none",
                        "include_diff": False,
                    })
                self.assertFalse(result["ok"])
                self.assertEqual(result["status"], "cancelled")
                self.assertEqual(result["error"]["code"], "WORKFLOW_RUNTIME_EXCEEDED")
                self.assertEqual(check.call_count, 1)
                self.assertEqual(runtime.task_state.get()["current_step"], "Replan required")
            finally:
                runtime.close()

    def test_aborted_canonical_run_repairs_stale_awaiting_acceptance_projection(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp), permission_mode="dangerous")
            try:
                state = runtime.task_state.update({
                    "objective": "Repair stale acceptance UI",
                    "status": "waiting",
                    "current_step": "Awaiting acceptance",
                    "next_step": "Accept stale proof",
                })
                ctx = runtime.orchestration_control.begin(
                    objective="Repair stale acceptance UI",
                    task_id=str(state["task_id"]),
                    execution_mode="mcp_only",
                    base_head="test-head",
                    worktree_fp="test-worktree",
                )
                stale = ctx.projection()
                stale["orchestration_state"] = "ACCEPTING"
                runtime.task_state.set_orchestration_projection(stale, event="test_stale_acceptance")
                runtime.orchestration_control.transition(ctx, "ABORTED", reason="test_timeout")
                self.assertTrue(runtime._reconcile_task_orchestration_projection())
                repaired = runtime.task_state.get()
                self.assertEqual(repaired["orchestration"]["orchestration_state"], "ABORTED")
                self.assertEqual(repaired["status"], "stopped")
                self.assertEqual(repaired["current_step"], "Aborted - operator report required")
                self.assertIn("completion_report", repaired["next_step"])
                self.assertNotEqual(repaired["current_step"], "Awaiting acceptance")
            finally:
                runtime.close()

    def test_reconcile_does_not_adopt_active_run_from_different_task(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp), permission_mode="dangerous")
            try:
                first = runtime.task_state.update({"objective": "Owned run", "status": "active"})
                ctx = runtime.orchestration_control.begin(
                    objective="Owned run",
                    task_id=str(first["task_id"]),
                    execution_mode="mcp_only",
                    base_head="test-head",
                    worktree_fp="test-worktree",
                )
                second = runtime.task_state.update({
                    "objective": "Different task",
                    "status": "active",
                    "new_task": True,
                })
                self.assertNotEqual(second["task_id"], first["task_id"])
                self.assertFalse(second.get("orchestration"))
                self.assertEqual(runtime.orchestration_ledger.current_active_run()["run_id"], ctx.run_id)
                self.assertIsNone(runtime.orchestration_ledger.current_active_run(task_id=str(second["task_id"])))

                self.assertFalse(runtime._reconcile_task_orchestration_projection())
                current = runtime.task_state.get()
                self.assertEqual(current["task_id"], second["task_id"])
                self.assertFalse(current.get("orchestration"))
            finally:
                runtime.close()

    def test_agent_workflow_explicit_objective_does_not_reuse_foreign_preflight_projection(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp), permission_mode="dangerous")
            try:
                foreign_task = runtime.task_state.update({
                    "objective": "foreign diagnose objective",
                    "status": "active",
                    "new_task": True,
                })
                foreign_ctx = runtime.orchestration_control.begin(
                    objective="foreign diagnose objective",
                    task_id=str(foreign_task["task_id"]),
                    execution_mode="mcp_only",
                    base_head="test-head",
                    worktree_fp="test-worktree",
                )
                runtime.task_state.set_orchestration_projection(
                    foreign_ctx.projection(),
                    event="test_foreign_projection",
                )

                result = runtime.agent_workflow({
                    "workflow": "diagnose",
                    "phase": "prepare",
                    "objective": "explicit Wave A objective",
                })

                new_run_id = result["orchestration"]["run_id"]
                new_wave_id = result["orchestration"]["wave_id"]
                self.assertNotEqual(new_run_id, foreign_ctx.run_id)
                self.assertEqual(
                    runtime.orchestration_ledger.get_run(new_run_id)["objective"],
                    "explicit Wave A objective",
                )
                provenance = runtime.orchestration_ledger.wave_objective_provenance(
                    new_run_id,
                    new_wave_id,
                )
                self.assertEqual(provenance["effective_objective"], "explicit Wave A objective")
                self.assertEqual(provenance["objective_source"], "run_initial_objective")
                self.assertEqual(
                    runtime.orchestration_ledger.get_run(foreign_ctx.run_id)["status"],
                    "active",
                )
                current = runtime.task_state.get()
                self.assertEqual(current["objective"], "explicit Wave A objective")
                self.assertNotEqual(current["task_id"], foreign_task["task_id"])
            finally:
                runtime.close()

    def test_apply_changes_and_verify_runs_continuous_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = Runtime(root, permission_mode="dangerous")
            result = runtime.apply_changes_and_verify({
                "objective": "create a file in one workflow",
                "patch": "*** Begin Patch\n*** Add File: done.txt\n+finished\n*** End Patch",
                "verification": "none",
                "include_diff": False,
            })
            self.assertTrue(result["ok"])
            self.assertEqual((root / "done.txt").read_text(encoding="utf-8"), "finished\n")
            self.assertEqual(runtime.task_state.get()["status"], "completed")

    def test_apply_changes_and_verify_scopes_diff_to_affected_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            runtime = Runtime(root, permission_mode="dangerous")
            with patch.object(runtime, "git_diff", return_value={"diff": "scoped", "truncated": False}) as git_diff:
                result = runtime.apply_changes_and_verify({
                    "objective": "change one file",
                    "patch": "*** Begin Patch\n*** Update File: app.py\n@@\n-VALUE = 1\n+VALUE = 2\n*** End Patch",
                    "verification": "none",
                })
            self.assertTrue(result["ok"])
            self.assertEqual(git_diff.call_args.args[0]["paths"], ["app.py"])
            self.assertNotIn("path", git_diff.call_args.args[0])
            runtime.close()

    def test_agent_workflow_build_failure_records_content_free_p2_v3_detail(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp), permission_mode="dangerous")
            try:
                result = runtime.agent_workflow({
                    "workflow": "feature",
                    "phase": "execute",
                    "execution_route": "deterministic",
                    "objective": "exercise P2 build verification observation",
                    "patches": [],
                    "verification": "build",
                    "build_command": "python -c \"import sys; sys.exit(7)\"",
                    "evaluation": {"provenance": "synthetic"},
                    "include_diff": False,
                })
                self.assertFalse(result["execution"]["ok"])
                self.assertEqual(result["execution"]["error"]["code"], "BUILD_VERIFICATION_FAILED")
                run_id = result["orchestration"]["run_id"]
                failures = [
                    event for event in runtime.orchestration_ledger.list_events(run_id)
                    if event["event_type"] == "failure_observed"
                ]
                self.assertEqual(len(failures), 1)
                payload = failures[0]["payload"]
                self.assertEqual(payload["failure_class"], "BUILD_VERIFICATION_FAILED")
                detail = payload["p2_failure_detail"]
                self.assertEqual(detail["schema"], "p2_failure_observation_v3")
                self.assertEqual(detail["stage"], "verification")
                self.assertEqual(detail["verification_failure_stage"], "build_command_failed")
                self.assertNotIn("unknown_reason", detail)
                self.assertNotIn("python -c", str(detail))
            finally:
                runtime.close()

    def test_agent_workflow_preflights_ambiguous_disjoint_patch_batch_before_orchestration(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "a.py").write_text("A = 1\n", encoding="utf-8")
            (root / "b.py").write_text("VALUE = 1\nVALUE = 1\n", encoding="utf-8")
            runtime = Runtime(root, permission_mode="dangerous")
            try:
                with self.assertRaises(ToolFailure) as caught:
                    runtime.agent_workflow({
                        "workflow": "bugfix",
                        "phase": "execute",
                        "execution_route": "deterministic",
                        "patches": [
                            "*** Begin Patch\n*** Update File: a.py\n@@\n-A = 1\n+A = 2\n*** End Patch",
                            "*** Begin Patch\n*** Update File: b.py\n@@\n-VALUE = 1\n+VALUE = 2\n*** End Patch",
                        ],
                        "verification": "none",
                    })
                self.assertEqual(caught.exception.code, "PATCH_CONTEXT_AMBIGUOUS")
                self.assertEqual(caught.exception.details["candidate_lines"], [1, 2])
                self.assertFalse(caught.exception.details["candidate_lines_truncated"])
                self.assertEqual((root / "a.py").read_text(encoding="utf-8"), "A = 1\n")
                self.assertEqual((root / "b.py").read_text(encoding="utf-8"), "VALUE = 1\nVALUE = 1\n")
                self.assertEqual(runtime.orchestration_ledger.list_runs(limit=10), [])
            finally:
                runtime.close()

    def test_verify_build_runs_commands_from_explicit_workdir(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "nested").mkdir()
            runtime = Runtime(root, permission_mode="dangerous")
            try:
                command = (
                    "python -c \"import os,sys; "
                    "sys.exit(0 if os.path.basename(os.getcwd()) == 'nested' else 7)\""
                )
                result = runtime.verify_build({
                    "path": ".",
                    "workdir": "nested",
                    "run_tests": True,
                    "run_build": False,
                    "test_command": command,
                })
                self.assertTrue(result["ok"], result)
                self.assertEqual(result["test_result"]["exit_code"], 0)
            finally:
                runtime.close()

    def test_agent_workflow_prepares_bug_context_in_one_call(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("def login():\n    raise RuntimeError('broken')\n", encoding="utf-8")
            runtime = Runtime(root, permission_mode="dangerous")
            result = runtime.agent_workflow({
                "workflow": "bugfix",
                "phase": "prepare",
                "objective": "fix login crash",
                "queries": ["login", "RuntimeError"],
                "max_files": 1,
                "max_entries": 10,
                "max_matches_per_query": 2,
                "max_total_bytes": 4096,
            })
            self.assertEqual(result["phase"], "prepare")
            self.assertEqual(result["context"]["files"][0]["path"], "app.py")
            self.assertEqual(len(result["context"]["searches"]), 2)
            limits = result["context"]["composite_read"]["plan"]["limits"]
            self.assertEqual(limits["max_files"], 1)
            self.assertEqual(limits["max_total_bytes"], 4096)
            self.assertEqual(limits["max_matches_per_query"], 2)

    def test_task_lifecycle_aborts_only_linked_nonterminal_orchestration(self) -> None:
        def link_run(runtime: Runtime, label: str):
            state = runtime.task_state.get()
            ctx = runtime.orchestration_control.begin(
                objective=label,
                task_id=str(state["task_id"]),
                execution_mode="mcp_only",
                base_head="test-head",
                worktree_fp=f"fp-{label}",
            )
            runtime.task_state.set_orchestration_projection(ctx.projection(), event="test_orchestration_linked")
            return ctx

        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp), permission_mode="dangerous")
            try:
                runtime.task_control({"action": "start", "objective": "stop case"})
                linked = link_run(runtime, "linked-stop")
                unrelated = runtime.orchestration_control.begin(
                    objective="unrelated",
                    task_id="unrelated-task",
                    execution_mode="mcp_only",
                    base_head="test-head",
                    worktree_fp="fp-unrelated",
                )
                stopped = runtime.task_control({"action": "stop", "reason": "operator stop"})
                self.assertEqual(stopped["state"]["status"], "stopped")
                self.assertEqual(stopped["state"]["orchestration"]["orchestration_state"], "ABORTED")
                self.assertEqual(runtime.orchestration_ledger.get_run(linked.run_id)["status"], "aborted")
                self.assertEqual(runtime.orchestration_ledger.get_run(unrelated.run_id)["status"], "active")

                runtime.task_control({"action": "start", "objective": "pause case"})
                paused_run = link_run(runtime, "linked-pause")
                runtime.task_control({"action": "pause", "reason": "temporary pause"})
                self.assertEqual(runtime.orchestration_ledger.get_run(paused_run.run_id)["status"], "active")

                runtime.task_control({"action": "start", "objective": "replacement case"})
                self.assertEqual(runtime.orchestration_ledger.get_run(paused_run.run_id)["status"], "aborted")
                replaced_run = link_run(runtime, "linked-replaced")
                runtime.task_control({"action": "start", "objective": "new replacement"})
                self.assertEqual(runtime.orchestration_ledger.get_run(replaced_run.run_id)["status"], "aborted")

                clear_run = link_run(runtime, "linked-clear")
                cleared = runtime.task_control({"action": "clear"})
                self.assertTrue(cleared["cleared"])
                self.assertEqual(runtime.orchestration_ledger.get_run(clear_run.run_id)["status"], "aborted")
                self.assertEqual(runtime.orchestration_ledger.get_run(unrelated.run_id)["status"], "active")
            finally:
                runtime.orchestration_control.transition(unrelated, "ABORTED", reason="test_cleanup")
                runtime.close()

    def test_agent_workflow_creates_greenfield_project_and_verifies(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = Runtime(root, permission_mode="dangerous")
            result = runtime.agent_workflow({
                "workflow": "greenfield",
                "phase": "execute",
                "objective": "create a tiny Python project",
                "directories": ["src"],
                "files": [{"path": "src/main.py", "content": "print('ready')\n"}],
                "commands": ["python src/main.py"],
                "verification": "none",
                "include_diff": False,
            })
            self.assertTrue(result["execution"]["ok"])
            self.assertEqual((root / "src" / "main.py").read_text(encoding="utf-8"), "print('ready')\n")
            self.assertEqual(result["task"]["status"], "waiting")
            self.assertEqual(result["orchestration"]["orchestration_state"], "ACCEPTING")
            runtime.task_state.record_tool_result(
                "agent_workflow",
                {"phase": "execute", "workflow": "greenfield"},
                {"ok": True, "execution": {"affected_files": [{"path": "src/main.py", "operation": "created"}]}},
            )
            accepted = runtime.task_control({"action": "accept", "run_id": result["orchestration"]["run_id"]})
            self.assertTrue(accepted["accepted"])
            self.assertEqual(accepted["state"]["status"], "completed")
            self.assertEqual(accepted["orchestration"]["orchestration_state"], "CHECKPOINTED")
            checkpoint = runtime.orchestration_ledger.export_summary(result["orchestration"]["run_id"])["checkpoints"][-1]
            receipt = checkpoint["metadata"]["accepted_files"]
            self.assertTrue(receipt["complete"])
            self.assertEqual(receipt["schema_version"], 2)
            self.assertEqual(receipt["count"], 1)
            self.assertEqual(receipt["files"][0]["path"], "src/main.py")
            self.assertEqual(receipt["files"][0]["state"], "file")
            self.assertEqual(receipt["files"][0]["receipt_kind"], "durable_wave_patch_surface")
            self.assertEqual(receipt["files"][0]["run_id"], result["orchestration"]["run_id"])
            self.assertEqual(
                receipt["files"][0]["sha256"],
                __import__("hashlib").sha256(b"print('ready')\n").hexdigest(),
            )

    def test_agent_workflow_schema_exposes_final_execution_routes_without_new_tool(self) -> None:
        schemas = server_module.input_schemas()
        agent_schema = schemas["agent_workflow"]
        agent_properties = agent_schema["properties"]
        max_lines_schema = agent_properties["max_lines_per_file"]
        self.assertEqual(max_lines_schema["default"], 2000)
        self.assertEqual(max_lines_schema["minimum"], 1)
        self.assertEqual(max_lines_schema["maximum"], 5000)
        validate_arguments("agent_workflow", {"max_lines_per_file": 2500})
        for invalid in (0, 5001):
            with self.subTest(max_lines_per_file=invalid), self.assertRaises(JsonRpcError):
                validate_arguments("agent_workflow", {"max_lines_per_file": invalid})
        read_file_lines_schema = schemas["read_file"]["properties"]["max_lines"]
        self.assertEqual(read_file_lines_schema["default"], 2000)
        self.assertEqual(read_file_lines_schema["minimum"], 1)
        self.assertEqual(read_file_lines_schema["maximum"], 5000)
        validate_arguments("read_file", {"path": "example.py", "max_lines": 5000})
        with self.assertRaises(JsonRpcError):
            validate_arguments("read_file", {"path": "example.py", "max_lines": 5001})
        route_schema = agent_properties["execution_route"]
        self.assertEqual(
            route_schema["enum"],
            ["auto", "deterministic", "mini", "luna", "terra", "sol_xhigh", "sol_max", "sol_ultra"],
        )
        self.assertFalse(agent_schema["additionalProperties"])
        self.assertIn("allow_high_cost", agent_properties)
        prepare_properties = schemas["prepare_coding_context"]["properties"]
        for field in (
            "path",
            "queries",
            "paths",
            "regex",
            "case_sensitive",
            "include_globs",
            "exclude_globs",
            "max_files",
            "max_entries",
            "max_matches_per_query",
            "max_total_bytes",
            "max_lines_per_file",
            "force_refresh",
        ):
            self.assertIn(field, agent_properties)
            for key in ("type", "items", "default", "minimum", "maximum", "maxItems"):
                if key in prepare_properties[field]:
                    self.assertEqual(agent_properties[field].get(key), prepare_properties[field][key])
        adoption_schema = agent_properties["adopt_existing_files"]
        self.assertEqual(adoption_schema["maxItems"], 64)
        self.assertEqual(adoption_schema["items"]["required"], ["path", "sha256"])
        evaluation_schema = schemas["agent_workflow"]["properties"]["evaluation"]
        self.assertEqual(evaluation_schema["properties"]["cache_stratum"]["enum"], ["cold", "warm", "unknown"])
        self.assertIn("policy_version", evaluation_schema["properties"])
        self.assertIn("topology_id", evaluation_schema["properties"])
        self.assertIn("router_id", evaluation_schema["properties"])
        self.assertIn("environment_id", evaluation_schema["properties"])
        self.assertIn("controller", evaluation_schema["properties"])
        self.assertIn("quality", schemas["task_control"]["properties"]["action"]["enum"])
        self.assertIn("quality_outcome", schemas["task_control"]["properties"])
        self.assertIn("observation", schemas["task_control"]["properties"]["action"]["enum"])
        observation_schema = schemas["task_control"]["properties"]["observation_span"]
        self.assertEqual(observation_schema["required"], ["span_id", "stage", "source", "measurement", "clock_domain", "start_ms", "end_ms"])
        bridge_profiles = schemas["codex_bridge"]["properties"]["profile"]["enum"]
        self.assertIn("deep_code", bridge_profiles)
        self.assertIn("parallel_extreme", bridge_profiles)
        smart_names = set(server_module.TOOL_MODE_ALLOWLISTS["smart"])
        self.assertEqual(len(smart_names), 8)
        self.assertNotIn("codex_bridge", smart_names)

    def test_task_control_records_delayed_quality_outcome(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp), permission_mode="dangerous")
            try:
                run_id = runtime.orchestration_ledger.create_run(objective="quality observation")
                wave_id = runtime.orchestration_ledger.create_wave(run_id, execution_mode="mcp_only")
                result = runtime.task_control({
                    "action": "quality",
                    "run_id": run_id,
                    "wave_id": wave_id,
                    "quality_outcome": {
                        "oracle_pass": True,
                        "critical_defect_count": 0,
                        "source": "test_observation",
                    },
                })
                self.assertTrue(result["recorded"])
                latest = runtime.orchestration_ledger.latest_quality_outcome(run_id)
                self.assertEqual(latest["source"], "test_observation")
                self.assertEqual(latest["critical_defect_count"], 0)
            finally:
                runtime.close()

    def test_task_control_records_content_free_observation_span(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp), permission_mode="dangerous")
            try:
                run_id = runtime.orchestration_ledger.create_run(objective="host observation")
                result = runtime.task_control({
                    "action": "observation",
                    "run_id": run_id,
                    "observation_span": {
                        "span_id": "host-visible",
                        "stage": "assistant_response_visible",
                        "source": "electron_chatgpt_dom",
                        "measurement": "observed_host_visible",
                        "clock_domain": "electron-renderer:1",
                        "start_ms": 100.0,
                        "end_ms": 125.5,
                        "observer_plane": "electron_chatgpt_dom",
                    },
                })
                self.assertTrue(result["recorded"])
                self.assertTrue(result["critical_path"]["complete"])
                self.assertEqual(result["critical_path"]["critical_path_ms"], 25.5)
                self.assertEqual(runtime.orchestration_ledger.list_observation_spans(run_id)[0]["measurement"], "observed_host_visible")
            finally:
                runtime.close()

    def test_execution_router_keeps_expensive_and_experimental_routes_gated(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp), permission_mode="dangerous")
            small = {"selected_paths": ["app.py"], "total_content_bytes": 4_000}
            medium = {"selected_paths": ["a.py", "b.py", "c.py"], "total_content_bytes": 30_000}
            broad = {"selected_paths": [f"f{i}.py" for i in range(8)], "total_content_bytes": 90_000}
            for workflow, prepared, strong_oracle in (
                ("bugfix", small, True),
                ("bugfix", small, False),
                ("feature", medium, False),
                ("feature", broad, False),
            ):
                automatic = runtime._select_agent_execution_route(
                    workflow=workflow,
                    prepared=prepared,
                    requested="auto",
                    allow_high_cost=False,
                    strong_oracle=strong_oracle,
                )
                self.assertEqual(automatic["selected"], "deterministic")
                self.assertEqual(automatic["reason"], "roi_gate_hold_insufficient_paired_evidence")
            self.assertEqual(runtime._select_agent_execution_route(workflow="bugfix", prepared=small, requested="mini", allow_high_cost=False)["selected"], "mini")
            self.assertEqual(runtime._select_agent_execution_route(workflow="feature", prepared=medium, requested="luna", allow_high_cost=False)["selected"], "luna")
            self.assertEqual(runtime._select_agent_execution_route(workflow="feature", prepared=broad, requested="sol_xhigh", allow_high_cost=False)["selected"], "sol_xhigh")
            terra = runtime._select_agent_execution_route(workflow="feature", prepared=broad, requested="terra", allow_high_cost=False)
            self.assertEqual((terra["model"], terra["effort"]), ("gpt-5.6-terra", "high"))
            with self.assertRaises(ToolFailure) as max_error:
                runtime._select_agent_execution_route(workflow="feature", prepared=broad, requested="sol_max", allow_high_cost=False)
            self.assertEqual(max_error.exception.code, "HIGH_COST_ACK_REQUIRED")
            with self.assertRaises(ToolFailure) as ultra_error:
                runtime._select_agent_execution_route(workflow="feature", prepared=broad, requested="sol_ultra", allow_high_cost=False)
            self.assertEqual(ultra_error.exception.code, "HIGH_COST_ACK_REQUIRED")
            self.assertEqual(runtime._select_agent_execution_route(workflow="feature", prepared=broad, requested="sol_max", allow_high_cost=True)["effort"], "max")
            self.assertEqual(runtime._select_agent_execution_route(workflow="feature", prepared=broad, requested="sol_ultra", allow_high_cost=True)["effort"], "ultra")
            runtime.close()

    def test_candidate_replacement_normalizes_newlines_before_exact_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_bytes(b"VALUE = 1\n")
            runtime = Runtime(root, permission_mode="dangerous")
            payload = {
                "replacements": [{"path": "app.py", "old": "VALUE = 1\r\n", "new": "VALUE = 2\r\n"}],
                "new_files": [],
            }
            patches, new_files = runtime._candidate_payload_to_patches(payload, allowed_paths=["app.py"])
            self.assertEqual(new_files, [])
            self.assertEqual(len(patches), 1)
            self.assertIn("-VALUE = 1", patches[0])
            self.assertIn("+VALUE = 2", patches[0])
            runtime.close()

    def test_candidate_scope_violation_is_rejected_before_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            (root / "other.py").write_text("OTHER = 1\n", encoding="utf-8")
            runtime = Runtime(root, permission_mode="dangerous")
            payload = {
                "replacements": [{"path": "other.py", "old": "OTHER = 1", "new": "OTHER = 2"}],
                "new_files": [],
            }
            with self.assertRaises(ToolFailure) as raised:
                runtime._candidate_payload_to_patches(payload, allowed_paths=["app.py"])
            self.assertEqual(raised.exception.code, "CANDIDATE_SCOPE_VIOLATION")
            self.assertEqual((root / "other.py").read_text(encoding="utf-8"), "OTHER = 1\n")
            runtime.close()

    def test_candidate_packet_includes_deep_query_centered_snippet(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            lines = [f"LINE_{index:04d} = {index}\n" for index in range(1, 2506)]
            lines[2399] = "def deeply_nested_target():\n"
            lines[2400] = "    VALUE = 1\n"
            lines[2299] = "QUERY_TARGET_2 = True\n"
            lines[2199] = "QUERY_TARGET_3 = True\n"
            lines[2099] = "QUERY_TARGET_4 = True\n"
            lines[2049] = "QUERY_TARGET_5 = True\n"
            (root / "large.py").write_text("".join(lines), encoding="utf-8")
            runtime = Runtime(root, permission_mode="dangerous")
            prepared = runtime.prepare_coding_context({
                "objective": "change deep target",
                "paths": ["large.py"],
                "queries": ["deeply_nested_target", "QUERY_TARGET_2", "QUERY_TARGET_3", "QUERY_TARGET_4", "QUERY_TARGET_5"],
                "max_files": 4,
            })
            self.assertTrue(prepared["files"][0]["truncated"])
            self.assertNotIn("deeply_nested_target", prepared["files"][0]["content"])
            packet, allowed_paths = runtime._agent_candidate_packet(
                workflow="bugfix",
                objective="change deep target",
                prepared=prepared,
                proof={},
                selected_route="mini",
            )
            self.assertEqual(allowed_paths, ["large.py"])
            deep_snippets = [item for item in packet["snippets"] if "deeply_nested_target" in item["content"]]
            self.assertEqual(len(deep_snippets), 1)
            self.assertEqual(len(packet["snippets"]), server_module.AGENT_CANDIDATE_SNIPPET_MAX_COUNT)
            self.assertEqual(deep_snippets[0]["match_line"], 2400)
            self.assertIn("VALUE = 1", deep_snippets[0]["content"])
            evidence_chars = sum(len(item["content"]) for item in packet["snippets"])
            evidence_chars += sum(len(item["content"]) for item in packet["files"])
            self.assertLessEqual(evidence_chars, server_module.AGENT_CANDIDATE_PACKET_MAX_CHARS)
            runtime.close()

    def test_agent_workflow_explicit_mini_uses_candidate_then_mcp_writer(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            runtime = Runtime(root, permission_mode="dangerous")
            test_cmd = f'"{sys.executable}" -c "from pathlib import Path; import sys; value=Path(\'app.py\').read_text(); print(\'expected VALUE = 2\'); sys.exit(0 if \'VALUE = 2\' in value else 1)"'
            bridge_result = {
                "status": "completed",
                "observation": {
                    "status": "completed",
                    "agent_text": json.dumps({
                        "status": "ready",
                        "summary": "repair value",
                        "replacements": [{"path": "app.py", "old": "VALUE = 1", "new": "VALUE = 2"}],
                        "new_files": [],
                        "proof": [],
                        "confidence": "high",
                    }),
                    "route": {"profile": "candidate_mini", "model": "gpt-5.4-mini", "effort": "low"},
                    "wall_time_ms": 100,
                    "economics": {
                        "model": "gpt-5.4-mini",
                        "input_tokens": 1000,
                        "cached_input_tokens": 800,
                        "uncached_input_tokens": 200,
                        "output_tokens": 100,
                        "reasoning_output_tokens": 20,
                        "estimated_credits": 0.1,
                        "estimated": True,
                        "measured": True,
                        "usage_provenance": "provider_reported",
                        "usage_source": "codex_app_server:thread/tokenUsage/updated",
                        "accounting_profile": "openai_compatible",
                    },
                    "deadline_hit": False,
                },
            }
            with patch.object(runtime._codex_bridge, "run", return_value=bridge_result) as bridge_run, patch.dict(
                server_module.os.environ, {server_module.AGENT_EXTERNAL_REVIEW_ENV: "off"}
            ):
                result = runtime.agent_workflow({
                    "workflow": "bugfix",
                    "evaluation": {"provenance": "benchmark"},
                    "phase": "run",
                    "execution_route": "mini",
                    "objective": "change VALUE",
                                        "paths": ["app.py"],
                    "verification": "tests",
                    "test_command": test_cmd,
                    "include_diff": False,
                })
            self.assertTrue(result["execution"]["ok"])
            self.assertEqual(result["execution_route"]["selected"], "mini")
            self.assertEqual(result["execution_route"]["model"], "gpt-5.4-mini")
            self.assertEqual(
                result["completion_readiness"]["oracle_preflight"]["classification"],
                "PRODUCT_ORACLE_REPRODUCED",
            )
            self.assertEqual((root / "app.py").read_text(encoding="utf-8"), "VALUE = 2\n")
            self.assertEqual(bridge_run.call_args.kwargs["profile"], "candidate_mini")
            self.assertIn("preflight_test", bridge_run.call_args.args[0])
            self.assertIn("expected VALUE = 2", bridge_run.call_args.args[0])
            usage_events = runtime.orchestration_ledger.list_usage_events(result["orchestration"]["run_id"], limit=None)
            self.assertEqual(len(usage_events), 1)
            usage = usage_events[0]
            self.assertEqual(usage["actor"], "provider")
            self.assertEqual(usage["provider_id"], "openai")
            self.assertEqual(usage["model_id"], "gpt-5.4-mini")
            self.assertEqual(usage["attribution"]["status"], "exact")
            self.assertEqual(usage["provenance"]["source"], "codex_app_server:thread/tokenUsage/updated")
            self.assertEqual(usage["provenance"]["usage"], "provider_reported")
            self.assertEqual(usage["measurement"]["usage"], "measured")
            self.assertNotEqual(usage["measurement"]["cost"], "measured")
            self.assertEqual(usage["usage"]["input_total_tokens"], 1000)
            self.assertEqual(usage["usage"]["input_cached_tokens"], 800)
            self.assertEqual(usage["usage"]["input_uncached_tokens"], 200)
            self.assertEqual(usage["usage"]["output_total_tokens"], 100)
            self.assertEqual(usage["usage"]["output_reasoning_tokens"], 20)
            runtime.close()

    def test_agent_workflow_prepare_reports_hashed_static_completion_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            runtime = Runtime(root, permission_mode="dangerous")
            try:
                result = runtime.agent_workflow({
                    "workflow": "bugfix",
                    "phase": "prepare",
                    "objective": "prepare readiness fixture",
                    "paths": ["app.py"],
                    "verification": "tests",
                    "test_command": f'"{sys.executable}" -m pytest',
                })
                readiness = result["completion_readiness"]
                self.assertEqual(readiness["schema_version"], 1)
                self.assertEqual(readiness["status"], "READY_FOR_EXECUTION")
                self.assertEqual(readiness["verification"]["steps"][0]["status"], "AVAILABLE")
                self.assertEqual(len(readiness["verification"]["steps"][0]["command_sha256"]), 64)
                self.assertNotIn("command", readiness["verification"]["steps"][0])
                self.assertEqual(readiness["scope"]["understood_paths"], ["app.py"])
                self.assertTrue(readiness["acceptance"]["business_outcome_not_inferred_from_build"])
            finally:
                runtime.close()

    def test_agent_workflow_blocks_candidate_when_baseline_is_setup_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            runtime = Runtime(root, permission_mode="dangerous")
            test_cmd = (
                f'"{sys.executable}" -c "import sys; '
                "print('No module named baseline_fixture_missing'); sys.exit(2)\""
            )
            with patch.object(runtime._codex_bridge, "run") as bridge_run:
                result = runtime.agent_workflow({
                    "workflow": "bugfix",
                    "evaluation": {"provenance": "benchmark"},
                    "phase": "run",
                    "execution_route": "mini",
                    "objective": "do not pay for a setup failure",
                    "paths": ["app.py"],
                    "verification": "tests",
                    "test_command": test_cmd,
                    "include_diff": False,
                })
            self.assertFalse(result["execution"]["ok"])
            self.assertEqual(result["execution"]["reason"], "COMPLETION_READINESS_BLOCKED")
            self.assertEqual(result["completion_readiness"]["status"], "BLOCKED")
            self.assertEqual(
                result["completion_readiness"]["oracle_preflight"]["classification"],
                "ENVIRONMENT_UNAVAILABLE",
            )
            bridge_run.assert_not_called()
            runtime.close()

    def test_agent_workflow_blocks_candidate_when_required_command_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            runtime = Runtime(root, permission_mode="dangerous")
            try:
                with patch.object(runtime._codex_bridge, "run") as bridge_run:
                    result = runtime.agent_workflow({
                        "workflow": "bugfix",
                        "evaluation": {"provenance": "benchmark"},
                        "phase": "run",
                        "execution_route": "mini",
                        "objective": "do not route without a local test command",
                        "paths": ["app.py"],
                        "verification": "tests",
                        "include_diff": False,
                    })
                self.assertEqual(result["execution"]["reason"], "COMPLETION_READINESS_BLOCKED")
                self.assertIn("TEST_COMMAND_MISSING", result["completion_readiness"]["blocking_reason_codes"])
                bridge_run.assert_not_called()
            finally:
                runtime.close()

    def test_agent_workflow_explicit_packet_review_uses_hidden_bridge(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp), permission_mode="dangerous")
            execution = {
                "ok": True,
                "status": "passed",
                "affected_files": [{"path": "src/app.py", "operation": "update"}],
                "check_results": [],
                "build_report": {
                    "overall_status": "passed",
                    "test_result": {"status": "passed"},
                    "build_result": None,
                    "artifacts": [],
                },
                "git_diff": {"diff": "diff --git a/src/app.py b/src/app.py\n-old\n+new\n", "truncated": False},
            }
            bridge_result = {
                "status": "completed",
                "route": {"profile": "packet", "model": "gpt-5.4-mini", "effort": "low"},
                "observation": {
                    "status": "completed",
                    "agent_text": json.dumps({"verdict": "accept", "findings": [], "missing_proof": [], "confidence": "high"}),
                    "route": {"profile": "packet", "model": "gpt-5.4-mini", "effort": "low"},
                    "wall_time_ms": 123,
                    "economics": {"estimated_credits": 0.1},
                    "deadline_hit": False,
                },
            }
            with patch.object(runtime, "apply_changes_and_verify", return_value=execution), patch.object(
                runtime._codex_bridge, "run", return_value=bridge_result
            ) as bridge_run, patch.dict(server_module.os.environ, {server_module.AGENT_EXTERNAL_REVIEW_ENV: "packet"}):
                result = runtime.agent_workflow({
                    "workflow": "feature",
                    "evaluation": {"provenance": "benchmark"},
                    "phase": "execute",
                    "objective": "change app behavior",
                    "patch": "*** Begin Patch\n*** End Patch",
                    "verification": "tests",
                })
            bridge_run.assert_called_once()
            self.assertEqual(bridge_run.call_args.kwargs["profile"], "packet")
            self.assertEqual(bridge_run.call_args.kwargs["deadline_ms"], server_module.AGENT_REVIEW_DEADLINE_MS)
            self.assertEqual(result["external_review"]["plane"], "external_mcp")
            self.assertEqual(result["external_review"]["verdict"], "accept")
            self.assertFalse(result["external_review"]["attention_required"])
            runtime.close()

    def test_agent_workflow_external_review_defaults_off(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp), permission_mode="dangerous")
            execution = {
                "ok": True,
                "status": "passed",
                "affected_files": [{"path": "src/app.py", "operation": "update"}],
                "check_results": [],
                "build_report": {"overall_status": "passed", "test_result": {"status": "passed"}, "build_result": None, "artifacts": []},
                "git_diff": {"diff": "diff --git a/src/app.py b/src/app.py\n-old\n+new\n", "truncated": False},
            }
            with patch.object(runtime, "apply_changes_and_verify", return_value=execution), patch.object(
                runtime._codex_bridge, "run"
            ) as bridge_run, patch.dict(server_module.os.environ, {}, clear=False):
                server_module.os.environ.pop(server_module.AGENT_EXTERNAL_REVIEW_ENV, None)
                result = runtime.agent_workflow({
                    "workflow": "feature",
                    "evaluation": {"provenance": "benchmark"},
                    "phase": "execute",
                    "objective": "change app behavior",
                    "patch": "*** Begin Patch\n*** End Patch",
                    "verification": "tests",
                })
            bridge_run.assert_not_called()
            self.assertEqual(result["external_review"]["plane"], "none")
            self.assertEqual(result["external_review"]["reason"], "external_review_disabled")
            runtime.close()

    def test_agent_workflow_skips_review_for_localized_bug_with_strong_oracle(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp), permission_mode="dangerous")
            execution = {
                "ok": True,
                "status": "passed",
                "affected_files": [{"path": "src/app.py", "operation": "update"}],
                "check_results": [],
                "build_report": {
                    "overall_status": "passed",
                    "test_result": {"status": "passed"},
                    "build_result": None,
                    "artifacts": [],
                },
                "git_diff": {"diff": "diff --git a/src/app.py b/src/app.py\n-old\n+new\n", "truncated": False},
            }
            with patch.object(runtime, "apply_changes_and_verify", return_value=execution), patch.object(
                runtime._codex_bridge, "run"
            ) as bridge_run, patch.dict(server_module.os.environ, {server_module.AGENT_EXTERNAL_REVIEW_ENV: "auto"}):
                result = runtime.agent_workflow({
                    "workflow": "bugfix",
                    "evaluation": {"provenance": "benchmark"},
                    "phase": "execute",
                    "objective": "fix localized bug",
                    "patch": "*** Begin Patch\n*** End Patch",
                    "verification": "tests",
                })
            bridge_run.assert_not_called()
            self.assertEqual(result["external_review"]["plane"], "none")
            self.assertEqual(result["external_review"]["reason"], "localized_change_with_strong_oracle")
            runtime.close()
    def test_agent_workflow_resume_returns_state_and_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "todo.py").write_text("VALUE = 1\n", encoding="utf-8")
            runtime = Runtime(root, permission_mode="dangerous")
            state = runtime.task_state.update({"objective": "continue fix", "next_step": "edit todo.py"})
            run_id = runtime.orchestration_ledger.create_run(objective="continue fix", task_id=state["task_id"])
            wave_id = runtime.orchestration_ledger.create_wave(run_id, execution_mode="mcp_only")
            runtime.orchestration_ledger.append_event(run_id, wave_id=wave_id, event_type="ready", state_after="READY")
            runtime.task_state.update({
                "orchestration": {
                    "run_id": run_id,
                    "wave_id": wave_id,
                    "orchestration_state": "READY",
                }
            })
            result = runtime.agent_workflow({"workflow": "resume", "phase": "resume", "paths": ["todo.py"]})
            self.assertEqual(result["task"]["objective"], "continue fix")
            self.assertEqual(result["context"]["files"][0]["path"], "todo.py")
            self.assertEqual(result["evidence"]["query"]["run_id"], run_id)
            self.assertEqual(result["evidence"]["query"]["wave_id"], wave_id)
            self.assertEqual(result["evidence"]["query"]["mode"], "model_free_priority")
            self.assertLessEqual(len(result["evidence"]["items"]), 12)
            self.assertTrue(result["evidence"]["model_free"])
            compact_resume = result["context"]["task_resume"]
            self.assertEqual(compact_resume["task_id"], state["task_id"])
            self.assertEqual(compact_resume["next_step"], "edit todo.py")
            self.assertNotIn("events", compact_resume)
            self.assertNotIn("test_results", compact_resume)
            self.assertNotIn("build_results", compact_resume)
            runtime.close()

    def test_server_discover_does_not_require_initialize(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            response = dispatch_rpc(Runtime(Path(temp)), {"jsonrpc": "2.0", "id": 1, "method": "server/discover", "params": {}})
            self.assertIn("result", response)
            self.assertEqual(response["result"]["serverInfo"]["name"], "coding-tools-mcp")

    def test_authorized_root_allows_absolute_read_write_and_blocks_other_paths(self) -> None:
        with tempfile.TemporaryDirectory() as main_temp, tempfile.TemporaryDirectory() as extra_temp, tempfile.TemporaryDirectory() as blocked_temp:
            main = Path(main_temp)
            extra = Path(extra_temp)
            blocked = Path(blocked_temp)
            source = extra / "共享资料.txt"
            source.write_text("中文内容\n", encoding="utf-8")
            blocked_file = blocked / "secret.txt"
            blocked_file.write_text("blocked\n", encoding="utf-8")
            runtime = Runtime(main)
            updated = runtime.set_authorized_roots([str(extra)])
            self.assertIn(str(extra.resolve()), updated["authorized_roots"])
            read = runtime.read_file({"path": str(source)})
            self.assertIn("中文内容", read["content"])
            target = runtime.resolve_for_write(str(extra / "nested" / "created.txt")).path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("created\n", encoding="utf-8")
            self.assertEqual(target.read_text(encoding="utf-8"), "created\n")
            with self.assertRaises(server_module.ToolFailure):
                runtime.read_file({"path": str(blocked_file)})
            runtime.close()

    def test_search_text_handles_utf8_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "中文文件.txt").write_text("工具搜索中文关键字\n", encoding="utf-8")
            runtime = Runtime(root)
            result = runtime.search_text({"query": "中文关键字", "path": "."})
            self.assertEqual(result["total_matches"], 1)
            self.assertIn("中文文件.txt", result["matches"][0]["path"])
            runtime.close()


class SourceFencedContinuationTests(unittest.TestCase):
    def _large_git_diff_runtime(self, root: Path) -> Runtime:
        subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
        source = root / "app.py"
        source.write_text("".join(f"VALUE_{index:04d} = {index}\n" for index in range(500)), encoding="utf-8")
        subprocess.run(["git", "add", "app.py"], cwd=root, check=True, capture_output=True)
        subprocess.run(
            ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "base"],
            cwd=root, check=True, capture_output=True,
        )
        source.write_text("".join(f"VALUE_{index:04d} = {index + 1}\n" for index in range(500)), encoding="utf-8")
        return Runtime(root, permission_mode="dangerous")

    def test_large_diff_continuation_is_exact_backward_compatible_and_detects_rereads(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = self._large_git_diff_runtime(Path(temp))
            try:
                full = runtime.git_diff({"paths": ["app.py"], "max_bytes": 1024 * 1024})
                self.assertFalse(full["truncated"])
                first = runtime.git_diff({"paths": ["app.py"], "max_bytes": 1024})
                self.assertTrue(first["truncated"])
                handoff = first["large_result_handoff"]
                self.assertEqual(handoff["kind"], "DIFF_PAGE")
                self.assertEqual(
                    handoff["source_identity"]["source_fingerprint"],
                    first["source_fingerprint"],
                )
                self.assertEqual(
                    handoff["scope_identity"]["scope_fingerprint"],
                    first["scope_fingerprint"],
                )
                self.assertEqual(handoff["continuation"], first["continuation"])
                self.assertEqual(handoff["next_operation"]["tool"], "agent_workflow")
                self.assertTrue(
                    handoff["recoverability"][
                        "continuation_recovers_all_omitted_data"
                    ]
                )
                expected_first = truncate_text_head(full["diff"], max_lines=DEFAULT_MAX_LINES, max_bytes=1024)
                self.assertEqual(first["diff"], expected_first.content)
                token = first["continuation"]
                self.assertTrue(token)
                peer = Runtime(Path(temp), permission_mode="dangerous")
                try:
                    second = peer.agent_workflow({"workflow": "resume", "phase": "resume", "continuation": token})["git_diff"]
                    repeated = runtime.agent_workflow({"workflow": "resume", "phase": "resume", "continuation": token})["git_diff"]
                    self.assertEqual(second["diff"], repeated["diff"])
                    self.assertFalse(second["result_tail"]["continuation_reread"])
                    self.assertTrue(repeated["result_tail"]["continuation_reread"])
                finally:
                    peer.close()
                pages = [first["diff"], second["diff"]]
                token = second["continuation"]
                page_count = 2
                while token:
                    page = runtime.agent_workflow({"workflow": "resume", "phase": "resume", "continuation": token})["git_diff"]
                    pages.append(page["diff"])
                    token = page["continuation"]
                    page_count += 1
                    self.assertLess(page_count, 100)
                self.assertEqual("".join(pages), full["diff"])
            finally:
                runtime.close()

    def test_diff_continuation_fails_closed_on_source_scope_option_or_signature_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = self._large_git_diff_runtime(root)
            try:
                first = runtime.git_diff({"paths": ["app.py"], "max_bytes": 1024})
                token = first["continuation"]
                with self.assertRaises(ToolFailure) as option_error:
                    runtime.git_diff({"continuation": token, "max_bytes": 2048})
                self.assertEqual(option_error.exception.code, "CONTINUATION_OPTIONS_MISMATCH")
                with self.assertRaises(ToolFailure) as scope_error:
                    runtime.git_diff({"continuation": token, "paths": ["other.py"]})
                self.assertEqual(scope_error.exception.code, "CONTINUATION_SCOPE_MISMATCH")
                with self.assertRaises(ToolFailure) as workflow_scope_error:
                    runtime.agent_workflow({
                        "workflow": "resume",
                        "phase": "resume",
                        "continuation": token,
                        "paths": ["other.py"],
                    })
                self.assertEqual(workflow_scope_error.exception.code, "CONTINUATION_SCOPE_MISMATCH")
                with self.assertRaises(ToolFailure) as signature_error:
                    runtime.agent_workflow({"workflow": "resume", "phase": "resume", "continuation": token[:-1] + ("A" if token[-1] != "A" else "B")})
                self.assertEqual(signature_error.exception.code, "INVALID_CONTINUATION")
                source = root / "app.py"
                source.write_text(source.read_text(encoding="utf-8") + "EXTRA = True\n", encoding="utf-8")
                with self.assertRaises(ToolFailure) as stale_error:
                    runtime.agent_workflow({"workflow": "resume", "phase": "resume", "continuation": token})
                self.assertEqual(stale_error.exception.code, "STALE_CONTINUATION")
                self.assertTrue(stale_error.exception.details["result_tail"]["continuation_stale"])
            finally:
                runtime.close()


class DocumentToolTests(unittest.TestCase):
    def test_create_and_extract_docx(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "report.docx"
            created = create_docx(target, "构建报告", "# 完成\n- 测试通过")
            self.assertGreater(created["size"], 500)
            extracted = extract_docx(target)
            self.assertIn("构建报告", extracted["content"])
            self.assertIn("测试通过", extracted["content"])

    def test_document_workflow_create_and_inspect(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp), permission_mode="dangerous")
            created = runtime.document_workflow({"action": "create", "target": "report.docx", "title": "Report", "content": "# Done\n- Passed"})
            self.assertGreater(created["result"]["size"], 500)
            inspected = runtime.document_workflow({"action": "inspect", "path": "report.docx"})
            self.assertEqual(inspected["count"], 1)
            self.assertIn("Passed", inspected["documents"][0]["content"])

    def test_document_workflow_creates_markdown_with_verification_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp), permission_mode="dangerous")
            created = runtime.document_workflow({
                "action": "create",
                "target": "learning-plan.md",
                "content": "# Plan\n\n- Week 1\n- Week 2\n",
            })
            result = created["result"]
            self.assertEqual((Path(temp) / "learning-plan.md").read_text(encoding="utf-8"), "# Plan\n\n- Week 1\n- Week 2\n")
            self.assertEqual(result["line_count"], 4)
            self.assertEqual(len(result["sha256"]), 64)
            self.assertEqual(result["preview"][0], "# Plan")


if __name__ == "__main__":
    unittest.main()
