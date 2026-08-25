from __future__ import annotations

import os
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamable_http_client

from coding_tools_mcp.server import MCPHandler, Runtime, RuntimeHTTPServer


EXPECTED_SMART_TOOLS = {
    "workspace_context",
    "agent_workflow",
    "task_control",
    "document_workflow",
    "exec_command",
    "command_control",
    "request_permissions",
    "view_image",
}
PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def assert_smart_task_control_schema(tools: list[object]) -> None:
    task_control = next(tool for tool in tools if str(getattr(tool, "name", "")) == "task_control")
    schema = getattr(task_control, "inputSchema")
    assert isinstance(schema, dict)
    action = schema["properties"]["action"]
    assert isinstance(action, dict)
    actions = action["enum"]
    assert isinstance(actions, list)
    assert actions.count("problem") == 1
    assert actions.count("p5") == 1
    assert "allOf" not in json.dumps(schema, ensure_ascii=False, sort_keys=True)


class OfficialMcpSdkSmokeTests(unittest.IsolatedAsyncioTestCase):
    async def test_official_sdk_stdio_initialize_list_and_call(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            child_env = dict(os.environ)
            child_env["CODING_TOOLS_MCP_TOOL_MODE"] = "smart"
            existing_pythonpath = child_env.get("PYTHONPATH", "")
            child_env["PYTHONPATH"] = os.pathsep.join(
                part for part in (str(PACKAGE_ROOT), existing_pythonpath) if part
            )
            parameters = StdioServerParameters(
                command=sys.executable,
                args=[
                    "-m",
                    "coding_tools_mcp.server",
                    "--stdio",
                    "--workspace",
                    temp,
                ],
                env=child_env,
            )
            async with stdio_client(parameters) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    initialized = await session.initialize()
                    self.assertTrue(initialized.protocolVersion)
                    tools = await session.list_tools()
                    self.assertEqual({tool.name for tool in tools.tools}, EXPECTED_SMART_TOOLS)
                    assert_smart_task_control_schema(list(tools.tools))
                    result = await session.call_tool(
                        "workspace_context", {"detail": "compact", "path": "."}
                    )
                    self.assertFalse(result.isError)

    async def test_official_sdk_streamable_http_initialize_list_and_call(self) -> None:
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            os.environ, {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}
        ):
            runtime = Runtime(Path(temp), transport="http")
            runtime.orchestration_ledger.migrate_problem_lineage_schema()
            server = RuntimeHTTPServer(
                ("127.0.0.1", 0),
                MCPHandler,
                runtime,
                runtime_factory=None,
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            port = int(server.server_address[1])
            try:
                async with streamable_http_client(
                    f"http://127.0.0.1:{port}/mcp"
                ) as (read_stream, write_stream, get_session_id):
                    async with ClientSession(read_stream, write_stream) as session:
                        initialized = await session.initialize()
                        self.assertTrue(initialized.protocolVersion)
                        self.assertTrue(get_session_id())
                        tools = await session.list_tools()
                        self.assertEqual({tool.name for tool in tools.tools}, EXPECTED_SMART_TOOLS)
                        assert_smart_task_control_schema(list(tools.tools))
                        missing_problem = await session.call_tool(
                            "task_control",
                            {"action": "problem", "problem_event": {"operation": "get", "problem_id": "missing-problem"}},
                        )
                        self.assertTrue(missing_problem.isError)
                        self.assertEqual(missing_problem.structuredContent["error"]["code"], "PRL_PROBLEM_NOT_FOUND")
                        result = await session.call_tool(
                            "workspace_context", {"detail": "compact", "path": "."}
                        )
                        self.assertFalse(result.isError)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
                self.assertFalse(thread.is_alive())


if __name__ == "__main__":
    unittest.main()
