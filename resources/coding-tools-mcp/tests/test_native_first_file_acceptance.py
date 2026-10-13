"""Real temporary File API acceptance; command/VM entry points are fail guards."""

from __future__ import annotations

import base64
import difflib
import hashlib
import json
import os
import tempfile
import time
import unittest
import zlib
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.server import Runtime


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def exact_patch(path: str, before: bytes, after: bytes) -> str:
    encoded = base64.b64encode(zlib.compress(after)).decode("ascii")
    return (
        f"*** Begin Patch\n*** Write Exact File: {path}\n"
        f"@@ encoding=zlib-base64 preimage_sha256={sha256(before)} postimage_sha256={sha256(after)}\n"
        f"+{encoded}\n*** End Patch\n"
    )


class NativeFirstFileAcceptanceTests(unittest.TestCase):
    def test_100_reads_and_20_exact_patch_transactions_need_no_command_or_vm(self) -> None:
        observed_at = datetime.now(timezone.utc).isoformat()
        started = time.perf_counter()
        report = {}
        with tempfile.TemporaryDirectory(prefix="native-first-file-acceptance-") as temporary, ExitStack() as stack:
            root = Path(temporary)
            originals = {
                f"source_{index:03d}.txt": f"SOURCE = {index}\r\nGhi chú: kiểm tra file\n".encode("utf-8")
                for index in range(100)
            }
            for relative, content in originals.items():
                (root / relative).write_bytes(content)
            stack.enter_context(patch.dict(os.environ, {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}))
            guards = {
                name: stack.enter_context(patch(target, side_effect=AssertionError(f"file acceptance entered {name}")))
                for name, target in {
                    "managed_command_spawn": "coding_tools_mcp.exec_tools.spawn_process",
                    "isolated_invocation": "coding_tools_mcp.exec_tools.build_mxc_windows_sandbox_invocation",
                    "native_invocation": "coding_tools_mcp.exec_tools.build_mxc_invocation",
                    "vm_lifecycle_phase": "coding_tools_mcp.windows_mxc_state_aware.MxcWindowsSandboxManager._run_envelope",
                }.items()
            }
            runtime = Runtime(root, permission_mode="dangerous")
            stack.callback(runtime.close)
            command = stack.enter_context(patch.object(runtime, "exec_command", side_effect=AssertionError("file API dispatched exec_command")))
            real_apply_patch = runtime.apply_patch
            mutation_lease_checks = []
            def apply_with_live_lease(args):
                if args.get("dry_run") is False:
                    projection = runtime.task_state.get()["orchestration"]
                    ctx = runtime.orchestration_control.snapshot(projection["run_id"])
                    self.assertIsNotNone(ctx.write_lease)
                    self.assertEqual(ctx.state, "EXECUTING")
                    mutation_lease_checks.append({"run_id": ctx.run_id, "allowed_paths": list(ctx.write_lease.allowed_paths)})
                return real_apply_patch(args)
            mutations = stack.enter_context(patch.object(runtime, "apply_patch", side_effect=apply_with_live_lease))
            binding = runtime.call_tool("workspace_context", {"path": str(root), "detail": "compact", "max_entries": 1})
            self.assertFalse(binding["isError"], binding)
            read_hashes = {}
            for relative, expected in originals.items():
                response = runtime.call_tool("read_file", {"path": relative, "start_line": 1, "max_lines": 10, "max_bytes": 1024})
                self.assertFalse(response["isError"], response)
                actual = response["structuredContent"]["content"].encode("utf-8")
                self.assertEqual(actual, expected)
                self.assertFalse(response["structuredContent"]["truncated"])
                read_hashes[relative] = sha256(actual)

            patch_records = []
            diffs = []
            for index in range(20):
                relative = f"source_{index:03d}.txt"
                before = originals[relative]
                after = before.replace(f"SOURCE = {index}".encode(), f"SOURCE = {index + 1000}".encode())
                pending_report = runtime.task_state.pending_completion_report()
                if pending_report:
                    acknowledgment = runtime.call_tool("task_control", {"action": "update", "payload": {
                        "extension": "operator_report_ack_v1", "report_id": pending_report["report_id"],
                    }})
                    self.assertFalse(acknowledgment["isError"], acknowledgment)
                start = runtime.call_tool("task_control", {"action": "start", "objective": f"Temporary file acceptance patch {index + 1}"})
                self.assertFalse(start["isError"], start)
                response = runtime.call_tool("agent_workflow", {
                    "workflow": "custom", "phase": "execute", "execution_mode": "mcp_only",
                    "execution_route": "deterministic", "verification": "none",
                    "objective": f"Temporary file acceptance patch {index + 1}",
                    "idempotency_key": f"native-first-file-acceptance-{index:03d}",
                    "patch": exact_patch(relative, before, after),
                })
                self.assertFalse(response["isError"], response)
                result = response["structuredContent"]
                run_id = result["orchestration"]["run_id"]
                wave_id = result["orchestration"]["wave_id"]
                events = runtime.orchestration_ledger.list_events(run_id, wave_id=wave_id)
                event_types = [event["event_type"] for event in events]
                self.assertIn("write_lease_acquired", event_types)
                self.assertIn("write_lease_revoked", event_types)
                self.assertLess(event_types.index("write_lease_acquired"), event_types.index("write_lease_revoked"))
                self.assertEqual(mutation_lease_checks[-1], {"run_id": run_id, "allowed_paths": [relative]})
                self.assertEqual((root / relative).read_bytes(), after)
                self.assertEqual(result["execution_route"]["selected"], "deterministic")
                final_read = runtime.call_tool("read_file", {"path": relative, "start_line": 1, "max_lines": 10, "max_bytes": 1024})
                self.assertFalse(final_read["isError"], final_read)
                self.assertEqual(final_read["structuredContent"]["content"].encode("utf-8"), after)
                diff = "".join(difflib.unified_diff(before.decode().splitlines(keepends=True), after.decode().splitlines(keepends=True),
                                                     fromfile=f"a/{relative}", tofile=f"b/{relative}"))
                self.assertIn(f"+SOURCE = {index + 1000}", diff)
                diffs.append(diff)
                stopped = runtime.call_tool("task_control", {"action": "stop", "reason": "temporary acceptance fixture cleanup"})
                self.assertFalse(stopped["isError"], stopped)
                self.assertEqual(runtime.orchestration_control.snapshot(run_id).state, "ABORTED")
                self.assertIsNone(runtime.orchestration_control.snapshot(run_id).write_lease)
                patch_records.append({"path": relative, "preimage_sha256": sha256(before), "postimage_sha256": sha256(after),
                                      "diff_sha256": sha256(diff.encode()), "run_id": run_id, "wave_id": wave_id,
                                      "writer_lease_acquired_and_revoked": True, "fixture_terminal_state": "ABORTED"})

            actual_mutations = [call for call in mutations.call_args_list if call.args[0].get("dry_run") is False]
            self.assertEqual(len(actual_mutations), 20)
            self.assertEqual(len(mutation_lease_checks), 20)
            self.assertEqual(len({item["run_id"] for item in patch_records}), 20)
            for relative, original in list(originals.items())[20:]:
                self.assertEqual((root / relative).read_bytes(), original)
            command.assert_not_called()
            for guard in guards.values():
                guard.assert_not_called()
            self.assertEqual(runtime.sessions, {})
            self.assertIsNone(getattr(runtime, "_windows_mxc_sandbox_manager", None))
            report = {
                "schema_version": 1, "observation_kind": "native_first_temporary_file_acceptance",
                "observed_git_head": os.environ.get("NATIVE_FIRST_OBSERVED_HEAD"), "captured_at_utc": observed_at,
                "completed_at_utc": datetime.now(timezone.utc).isoformat(), "elapsed_seconds": round(time.perf_counter() - started, 3),
                "sample": {"initial_read_files": 100, "post_patch_reads": 20, "exact_patch_transactions": 20,
                           "changed_files": 20, "untouched_source_files": 80, "writer_lease_lifecycles": 20},
                "proof_scope": "Actual Runtime.call_tool File API and agent_workflow exact writes in a temporary fixture; process and VM boundaries replaced by fail guards",
                "process_assertions": {"managed_command_spawns": 0, "native_invocations": 0, "isolated_invocations": 0,
                                       "vm_lifecycle_phase_calls": 0, "runtime_exec_calls": 0, "runtime_command_sessions": 0},
                "physical_vm_census_measured": False, "ram_measured": False, "live_control_plane_dispatch_measured": False,
                "model_assertions": {"execution_route": "deterministic", "execution_mode": "mcp_only", "native_safety_label_used": False},
                "initial_content_manifest_sha256": sha256(json.dumps(read_hashes, sort_keys=True, separators=(",", ":")).encode()),
                "aggregate_diff_sha256": sha256("".join(diffs).encode()), "patches": patch_records,
                "fixture_job_state": "No command Jobs; 20 synthetic fixture runs stopped as ABORTED after hash/diff checks; no false acceptance",
                "fixture_operator_actions": "Synthetic task start/stop and report acknowledgment only within temporary fixture; no production task or acceptance changed",
                "limitations": ["Zero VM means guarded adapter calls were zero in this fixture, not a live OS VM census",
                                "Does not prove packaged execution, native ProcessContainer compatibility, network denial or live reconnect"],
                "tests": ["test_native_first_file_acceptance.py::NativeFirstFileAcceptanceTests::test_100_reads_and_20_exact_patch_transactions_need_no_command_or_vm"],
            }
        evidence_path = os.environ.get("NATIVE_FIRST_FILE_EVIDENCE_PATH")
        if evidence_path:
            destination = Path(evidence_path)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("x", encoding="utf-8") as handle:
                json.dump(report, handle, ensure_ascii=False, indent=2)
                handle.write("\n")


if __name__ == "__main__":
    unittest.main()
