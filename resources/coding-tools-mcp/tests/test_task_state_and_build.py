from __future__ import annotations

import json
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[1]
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

import coding_tools_mcp.server as server_module
from coding_tools_mcp.build_verify import collect_artifacts, detect_project
from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.task_state import TaskStateStore, classify_command
from coding_tools_mcp.server import Runtime
from coding_tools_mcp.protocol import dispatch_rpc
from coding_tools_mcp.document_tools import create_docx, extract_docx


class TaskStateTests(unittest.TestCase):
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
            })
            self.assertEqual(result["phase"], "prepare")
            self.assertEqual(result["context"]["files"][0]["path"], "app.py")
            self.assertEqual(len(result["context"]["searches"]), 2)

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
            self.assertEqual(result["task"]["status"], "completed")

    def test_agent_workflow_schema_exposes_final_execution_routes_without_new_tool(self) -> None:
        schemas = server_module.input_schemas()
        route_schema = schemas["agent_workflow"]["properties"]["execution_route"]
        self.assertEqual(
            route_schema["enum"],
            ["auto", "deterministic", "mini", "luna", "terra", "sol_xhigh", "sol_max", "sol_ultra"],
        )
        self.assertIn("allow_high_cost", schemas["agent_workflow"]["properties"])
        bridge_profiles = schemas["codex_bridge"]["properties"]["profile"]["enum"]
        self.assertIn("deep_code", bridge_profiles)
        self.assertIn("parallel_extreme", bridge_profiles)
        smart_names = set(server_module.TOOL_MODE_ALLOWLISTS["smart"])
        self.assertEqual(len(smart_names), 8)
        self.assertNotIn("codex_bridge", smart_names)

    def test_execution_router_keeps_expensive_and_experimental_routes_gated(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            runtime = Runtime(Path(temp), permission_mode="dangerous")
            small = {"selected_paths": ["app.py"], "total_content_bytes": 4_000}
            medium = {"selected_paths": ["a.py", "b.py", "c.py"], "total_content_bytes": 30_000}
            broad = {"selected_paths": [f"f{i}.py" for i in range(8)], "total_content_bytes": 90_000}
            self.assertEqual(runtime._select_agent_execution_route(workflow="bugfix", prepared=small, requested="auto", allow_high_cost=False)["selected"], "mini")
            self.assertEqual(runtime._select_agent_execution_route(workflow="feature", prepared=medium, requested="auto", allow_high_cost=False)["selected"], "luna")
            self.assertEqual(runtime._select_agent_execution_route(workflow="feature", prepared=broad, requested="auto", allow_high_cost=False)["selected"], "sol_xhigh")
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

    def test_agent_workflow_run_auto_uses_mini_candidate_then_mcp_writer(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
            runtime = Runtime(root, permission_mode="dangerous")
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
                    "economics": {"estimated_credits": 0.1},
                    "deadline_hit": False,
                },
            }
            with patch.object(runtime._codex_bridge, "run", return_value=bridge_result) as bridge_run, patch.dict(
                server_module.os.environ, {server_module.AGENT_EXTERNAL_REVIEW_ENV: "off"}
            ):
                result = runtime.agent_workflow({
                    "workflow": "bugfix",
                    "phase": "run",
                    "objective": "change VALUE",
                    "paths": ["app.py"],
                    "verification": "none",
                    "include_diff": False,
                })
            self.assertTrue(result["execution"]["ok"])
            self.assertEqual(result["execution_route"]["selected"], "mini")
            self.assertEqual(result["execution_route"]["model"], "gpt-5.4-mini")
            self.assertEqual((root / "app.py").read_text(encoding="utf-8"), "VALUE = 2\n")
            self.assertEqual(bridge_run.call_args.kwargs["profile"], "candidate_mini")
            runtime.close()

    def test_agent_workflow_auto_packet_review_uses_hidden_bridge(self) -> None:
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
            ) as bridge_run:
                result = runtime.agent_workflow({
                    "workflow": "feature",
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
            ) as bridge_run:
                result = runtime.agent_workflow({
                    "workflow": "bugfix",
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
            runtime.task_state.update({"objective": "continue fix", "next_step": "edit todo.py"})
            result = runtime.agent_workflow({"workflow": "resume", "phase": "resume", "paths": ["todo.py"]})
            self.assertEqual(result["task"]["objective"], "continue fix")
            self.assertEqual(result["context"]["files"][0]["path"], "todo.py")

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
