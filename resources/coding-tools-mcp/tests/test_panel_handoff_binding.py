"""Regression tests for the W7 live panel-handoff failure (smoke item 5).

Live condition (r20, Windows): in the Electron "Chat Codex (native)" panel,
"Chuyển thành việc điều hành" always failed with
HANDOFF_PANEL_BINDING_MISMATCH ("The displayed panel RUN/WAVE no longer has
an exact task binding; refresh the panel."), Refresh did not help, and the
handoff registry stayed null.

Root cause: the panel displays the RUN from the canonical orchestration
ledger (Electron ``task-state:read``), but ``panel_handoff_state`` demanded
that the single UNSCOPED workspace task-state file simultaneously match
that RUN, its current wave, and the canonical task.  In a live workspace
that shared file is routinely overwritten by other activity (a finished
task, an auto-started replacement task, a scoped ChatWeb context), while
the displayed RUN's own binding lives in its scoped store — so the gate
failed deterministically and Refresh (which only re-reads the ledger
display) could never repair it.  The Node handoff tests used a fake
``task_control`` and the Python panel test used a pristine single-task
workspace, so the gate never ran against realistic live state.

These tests reproduce that shape over real HTTP: the target RUN is bound
in a scoped ``mcp2026:*`` store, the unscoped projection belongs to a
different finished task, and the scoped projection's wave is stale.
Handoff record for the exact RUN must succeed; a RUN with no binding
anywhere, and a caller-supplied stale wave, must still be refused.
"""
from __future__ import annotations

import http.client
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.connector_attestation import CONNECTOR_ATTESTATION_HEADER, build_connector_attestation
from coding_tools_mcp.protocol import STATELESS_PROTOCOL_VERSION
from coding_tools_mcp.server import MCPHandler, Runtime, RuntimeHTTPServer
from coding_tools_mcp.task_state import TaskStateStore


def modern_params(extra: dict | None = None) -> dict:
    payload = dict(extra or {})
    payload["_meta"] = {
        "io.modelcontextprotocol/protocolVersion": STATELESS_PROTOCOL_VERSION,
        "io.modelcontextprotocol/clientCapabilities": {},
        "io.modelcontextprotocol/clientInfo": {"name": "raw-canary", "version": "1"},
    }
    return payload


PANEL_HEADERS = {
    "X-Coding-Tools-Client-Id": "electron-panel",
    "X-Coding-Tools-Client-Type": "electron",
}


class PanelHandoffBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(
            os.environ,
            {
                "CODING_TOOLS_MCP_TOOL_MODE": "smart",
                "CODING_TOOLS_MCP_STATELESS_HTTP_2026": "1",
                "CODING_TOOLS_MCP_DEVICE_ID": "11111111-1111-4111-8111-111111111111",
                "CODING_TOOLS_MCP_DEVICE_INSTANCE_ID": "device-instance-office-0001",
                "CODING_TOOLS_MCP_DEVICE_DISPLAY_NAME": "Office Workstation",
                "CODING_TOOLS_MCP_CONNECTOR_ATTESTATION_SECRET": "test-connector-attestation-secret",
            },
        )
        self.env.start()
        waiter = patch("coding_tools_mcp.activation_lifecycle.ACTIVATION_BOOTSTRAP_WAIT_SECONDS", 0)
        waiter.start()
        self.addCleanup(waiter.stop)
        self.runtime = Runtime(Path(self.temp.name), transport="http")
        self.server = RuntimeHTTPServer(("127.0.0.1", 0), MCPHandler, self.runtime, runtime_factory=None)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = int(self.server.server_address[1])

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.assertFalse(self.thread.is_alive())
        self.env.stop()
        self.temp.cleanup()

    def request(self, method: str, params: dict, *, request_id: int = 1, extra_headers: dict[str, str] | None = None) -> tuple[int, dict]:
        headers = {
            "Content-Type": "application/json",
            "MCP-Protocol-Version": STATELESS_PROTOCOL_VERSION,
            "Mcp-Method": method,
            "X-Coding-Tools-Client-Id": "chatweb",
            "X-Coding-Tools-Client-Type": "chatweb",
        }
        headers.update(extra_headers or {})
        if CONNECTOR_ATTESTATION_HEADER not in headers and "X-Coding-Tools-Client-Id" in headers:
            headers[CONNECTOR_ATTESTATION_HEADER] = build_connector_attestation(
                "test-connector-attestation-secret",
                client_id=headers["X-Coding-Tools-Client-Id"],
                client_type=headers["X-Coding-Tools-Client-Type"],
                activation_epoch_id=getattr(self.runtime, "activation_epoch_id", ""),
                process_instance_id=self.runtime.process_instance_id,
                server_instance_id=self.runtime.server_instance_id,
                contract_sha256=self.runtime.tool_contract["sha256"],
            )
        body = json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}).encode("utf-8")
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            connection.request("POST", "/mcp", body=body, headers=headers)
            response = connection.getresponse()
            raw = response.read()
            return response.status, (json.loads(raw.decode("utf-8")) if raw else {})
        finally:
            connection.close()

    def tool_call(self, name: str, arguments: dict, *, request_id: int, extra_headers: dict[str, str] | None = None):
        return self.request(
            "tools/call",
            modern_params({"name": name, "arguments": arguments}),
            request_id=request_id,
            extra_headers={"Mcp-Name": name, **(extra_headers or {})},
        )

    def prepare_scoped_run(self, context_id: str, objective: str, request_id: int) -> dict:
        status, response = self.tool_call(
            "agent_workflow",
            {
                "task_context_id": context_id,
                "workflow": "diagnose",
                "phase": "prepare",
                "objective": objective,
                "execution_route": "deterministic",
                "execution_mode": "mcp_only",
                "verification": "none",
                "path": ".",
            },
            request_id=request_id,
        )
        self.assertEqual(status, 200)
        self.assertFalse(response["result"]["isError"], response)
        return response["result"]["structuredContent"]

    def pollute_unscoped_with_other_finished_task(self) -> None:
        """Live shape: the shared unscoped slot no longer holds the chat RUN."""
        ledger = self.runtime.orchestration_ledger
        other_run = ledger.create_run(objective="Other finished workspace task", task_id="finished-other-task")
        other_wave = ledger.create_wave(other_run, execution_mode="mcp_only")
        store = TaskStateStore(Path(self.temp.name))
        state = store.get()
        state.update({
            "task_id": "finished-other-task",
            "objective": "Other finished workspace task",
            "status": "completed",
            "current_step": "Completed",
            "next_step": "",
        })
        state["orchestration"] = {
            "run_id": other_run,
            "wave_id": other_wave,
            "orchestration_state": "CHECKPOINTED",
        }
        store._write(state)

    def test_record_succeeds_when_binding_lives_in_scoped_store_and_unscoped_slot_moved_on(self) -> None:
        prepared = self.prepare_scoped_run("panel-handoff-live", "Chat-linked panel task", 41)
        run_id = prepared["orchestration"]["run_id"]
        wave_id = prepared["orchestration"]["wave_id"]
        self.assertTrue(run_id and wave_id)

        # The scoped projection's wave goes stale (the RUN advanced after
        # the chat turns completed) — binding stays exact on run + task.
        scoped = TaskStateStore(Path(self.temp.name), scope_id="mcp2026:panel-handoff-live")
        scoped_state = scoped.get()
        task_id = scoped_state["task_id"]
        self.assertTrue(task_id)
        self.assertEqual(scoped_state["orchestration"]["run_id"], run_id)
        scoped_state["orchestration"] = {**scoped_state["orchestration"], "wave_id": "stale-wave-id"}
        scoped._write(scoped_state)

        self.pollute_unscoped_with_other_finished_task()
        unscoped = TaskStateStore(Path(self.temp.name)).get()
        self.assertNotEqual(unscoped["orchestration"]["run_id"], run_id)

        status, response = self.tool_call(
            "task_control",
            {"action": "handoff", "handoff_action": "record", "run_id": run_id,
             "payload": {"source": "workhub-codex-chat", "kind": "codex-chat-handoff"}},
            request_id=42, extra_headers=PANEL_HEADERS,
        )
        self.assertEqual(status, 200)
        self.assertFalse(response["result"]["isError"], response)
        structured = response["result"]["structuredContent"]
        self.assertTrue(structured["recorded"])
        capsule = structured["capsule"]
        self.assertEqual(capsule["run_id"], run_id)
        # Wave stamped from the orchestration snapshot, not the stale file.
        self.assertEqual(capsule["wave_id"], wave_id)
        runtime_block = capsule["payload"]["runtime"]
        self.assertEqual(runtime_block["task_id"], task_id)
        self.assertEqual(runtime_block["objective"], "Chat-linked panel task")
        self.assertEqual(runtime_block["run_id"], run_id)
        self.assertEqual(runtime_block["wave_id"], wave_id)

        # Handoff get for the same RUN reads the capsule back.
        status, response = self.tool_call(
            "task_control",
            {"action": "handoff", "handoff_action": "get", "run_id": run_id},
            request_id=43, extra_headers=PANEL_HEADERS,
        )
        self.assertEqual(status, 200)
        self.assertFalse(response["result"]["isError"], response)
        self.assertEqual(
            response["result"]["structuredContent"]["capsule"]["capsule_id"], capsule["capsule_id"]
        )

    def test_record_still_refused_without_any_exact_binding(self) -> None:
        prepared = self.prepare_scoped_run("panel-handoff-bound", "Bound panel task", 51)
        run_id = prepared["orchestration"]["run_id"]

        # A ledger RUN whose task has no persisted binding anywhere.
        ledger = self.runtime.orchestration_ledger
        orphan_run = ledger.create_run(objective="Orphan ledger run", task_id="orphan-task")
        ledger.create_wave(orphan_run, execution_mode="mcp_only")

        status, response = self.tool_call(
            "task_control",
            {"action": "handoff", "handoff_action": "record", "run_id": orphan_run, "payload": {}},
            request_id=52, extra_headers=PANEL_HEADERS,
        )
        self.assertEqual(status, 200)
        self.assertTrue(response["result"]["isError"], response)
        error = response["result"]["structuredContent"]["error"]
        self.assertEqual(error["code"], "HANDOFF_PANEL_BINDING_MISMATCH")
        details = error.get("details") or {}
        self.assertIn("exact_task_binding_missing", details.get("failed_checks") or [])
        self.assertEqual(details.get("canonical_task_id"), "orphan-task")
        self.assertFalse(details.get("binding_found"))

        # A caller-supplied stale wave is still refused for the bound RUN.
        status, response = self.tool_call(
            "task_control",
            {"action": "handoff", "handoff_action": "record", "run_id": run_id,
             "wave_id": "old-wave", "payload": {}},
            request_id=53, extra_headers=PANEL_HEADERS,
        )
        self.assertEqual(status, 200)
        self.assertTrue(response["result"]["isError"], response)
        error = response["result"]["structuredContent"]["error"]
        self.assertEqual(error["code"], "HANDOFF_PANEL_BINDING_MISMATCH")
        self.assertIn(
            "caller_wave_mismatch", (error.get("details") or {}).get("failed_checks") or []
        )

        # A RUN that does not exist in the ledger at all is refused too.
        status, response = self.tool_call(
            "task_control",
            {"action": "handoff", "handoff_action": "record", "run_id": "missing-run", "payload": {}},
            request_id=54, extra_headers=PANEL_HEADERS,
        )
        self.assertEqual(status, 200)
        self.assertTrue(response["result"]["isError"], response)
        self.assertEqual(
            response["result"]["structuredContent"]["error"]["code"],
            "HANDOFF_PANEL_BINDING_MISMATCH",
        )
        self.assertIsNone(self.runtime.orchestration_ledger.latest_handoff_capsule(run_id=orphan_run))
        self.assertIsNone(self.runtime.orchestration_ledger.latest_handoff_capsule(run_id=run_id))


if __name__ == "__main__":
    unittest.main()
