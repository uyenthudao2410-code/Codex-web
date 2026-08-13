from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(r"E:\DEV\Tools-Codex-web")
PY = ROOT / "resources" / "native-python" / "python.exe"
PKG = ROOT / "resources" / "coding-tools-mcp"
FIXTURE = ROOT / ".coding-tools" / f"eocl-stdio-smoke-{uuid.uuid4().hex}"
EXPECTED_TOOLS = {
    "workspace_context", "agent_workflow", "task_control", "document_workflow",
    "exec_command", "command_control", "request_permissions", "view_image",
}

proc = None
req_id = 0

def send(method: str, params: dict | None = None, *, notification: bool = False):
    global req_id
    msg = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        msg["params"] = params
    if not notification:
        req_id += 1
        msg["id"] = req_id
    assert proc is not None and proc.stdin is not None and proc.stdout is not None
    proc.stdin.write(json.dumps(msg, separators=(",", ":")) + "\n")
    proc.stdin.flush()
    if notification:
        return None
    deadline = time.time() + 90
    while time.time() < deadline:
        line = proc.stdout.readline()
        if not line:
            err = proc.stderr.read() if proc.stderr else ""
            raise RuntimeError(f"stdio server closed while waiting for {method}: {err}")
        payload = json.loads(line)
        if payload.get("id") == msg["id"]:
            if "error" in payload:
                raise RuntimeError(f"RPC {method} failed: {payload['error']}")
            return payload["result"]
    raise TimeoutError(method)

def structured(call_result: dict) -> dict:
    if isinstance(call_result.get("structuredContent"), dict):
        return call_result["structuredContent"]
    content = call_result.get("content")
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                try:
                    value = json.loads(item.get("text", ""))
                    if isinstance(value, dict):
                        return value
                except Exception:
                    pass
    return call_result

def tool_call(name: str, args: dict) -> dict:
    return structured(send("tools/call", {"name": name, "arguments": args}))

summary = {}
try:
    FIXTURE.mkdir(parents=True, exist_ok=False)
    (FIXTURE / "README.txt").write_text("isolated EOCL stdio smoke fixture\n", encoding="utf-8")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PKG)
    env["CODING_TOOLS_MCP_TOOL_MODE"] = "smart"
    env["CODING_TOOLS_MCP_AUTHORIZED_ROOTS"] = str(ROOT)
    proc = subprocess.Popen(
        [str(PY), "-m", "coding_tools_mcp", "--stdio", "--workspace", str(FIXTURE), "--permission-mode", "safe"],
        cwd=str(ROOT), env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace", bufsize=1,
    )
    init = send("initialize", {
        "protocolVersion": "2025-11-25",
        "clientInfo": {"name": "fresh-eocl-gate", "version": "1"},
        "capabilities": {},
    })
    send("notifications/initialized", {}, notification=True)
    listing = send("tools/list", {})
    tools = listing.get("tools", [])
    names = {t.get("name") for t in tools}
    if names != EXPECTED_TOOLS:
        raise AssertionError(f"smart tool surface mismatch: {sorted(names)}")
    by_name = {t["name"]: t for t in tools}
    aw_props = by_name["agent_workflow"]["inputSchema"]["properties"]
    missing_aw = [x for x in ("execution_mode", "replan_reason", "contract_fingerprint") if x not in aw_props]
    if missing_aw:
        raise AssertionError(f"agent_workflow schema missing {missing_aw}")
    tc_actions = set(by_name["task_control"]["inputSchema"]["properties"]["action"]["enum"])
    if not {"audit", "accept", "reject"}.issubset(tc_actions):
        raise AssertionError(f"task_control schema missing EOCL actions: {sorted(tc_actions)}")

    workflow = tool_call("agent_workflow", {
        "workflow": "build_release",
        "phase": "run",
        "objective": "Isolated safe EOCL stdio acceptance smoke; execute only a deterministic echo and do not modify source.",
        "commands": ["cmd /d /c echo EOCL_STDIO_SMOKE_OK"],
        "verification": "none",
        "execution_mode": "mcp_only",
        "contract_fingerprint": "sol-lean-codex-v5-eocl-smoke-2026-08-13",
        "timeout_seconds": 60,
    })
    orch = workflow.get("orchestration", {})
    if orch.get("orchestration_state") != "ACCEPTING":
        raise AssertionError(f"workflow did not reach ACCEPTING: {orch}")
    run_id = orch.get("run_id")
    wave_id = orch.get("wave_id")
    if not run_id or not wave_id:
        raise AssertionError("missing run/wave identity")

    audit1 = tool_call("task_control", {"action": "audit", "run_id": run_id, "limit": 100})
    a = audit1.get("audit", {})
    integrity = a.get("integrity", {})
    if integrity.get("ok") is not True:
        raise AssertionError(f"audit integrity failed: {integrity}")
    proofs = a.get("proofs", [])
    if not proofs:
        raise AssertionError("no proof records")
    events = a.get("events", [])
    states = []
    for e in events:
        for key in ("state_after", "state"):
            value = e.get(key)
            if isinstance(value, str) and value and value not in states:
                states.append(value)
        details = e.get("details")
        if isinstance(details, dict):
            value = details.get("state")
            if isinstance(value, str) and value and value not in states:
                states.append(value)
    required = ["PREFLIGHT", "READY", "ROUTED", "EXECUTING", "PROVING", "ACCEPTING"]
    pos = -1
    for state in required:
        try:
            pos = states.index(state, pos + 1)
        except ValueError:
            raise AssertionError(f"missing ordered state {state}; observed={states}")

    accepted = tool_call("task_control", {"action": "accept", "run_id": run_id, "reason": "Fresh stdio smoke proof and audit are green; no source mutation."})
    accept_orch = accepted.get("orchestration", {})
    if accepted.get("accepted") is not True or accept_orch.get("orchestration_state") != "CHECKPOINTED":
        raise AssertionError(f"accept failed: {accepted}")
    audit2 = tool_call("task_control", {"action": "audit", "run_id": run_id, "limit": 100})
    if audit2.get("orchestration", {}).get("orchestration_state") != "CHECKPOINTED":
        raise AssertionError("post-accept audit not CHECKPOINTED")
    if audit2.get("audit", {}).get("integrity", {}).get("ok") is not True:
        raise AssertionError("post-accept integrity failed")

    summary = {
        "ok": True,
        "protocol_version": init.get("protocolVersion"),
        "tool_count": len(tools),
        "tool_names": sorted(names),
        "agent_workflow_fields": {k: True for k in ("execution_mode", "replan_reason", "contract_fingerprint")},
        "task_control_actions": sorted({"audit", "accept", "reject"} & tc_actions),
        "run_id": run_id,
        "wave_id": wave_id,
        "states": required + ["CHECKPOINTED"],
        "route_requested": orch.get("route_requested"),
        "route_resolved": orch.get("route_resolved"),
        "execution_mode": orch.get("execution_mode"),
        "base_head": orch.get("base_head"),
        "proof_ids": [p.get("proof_id") for p in proofs],
        "proof_input_fingerprints": [p.get("input_fingerprint") for p in proofs],
        "audit_integrity_head": audit2.get("audit", {}).get("integrity", {}).get("head_hash"),
        "final_state": audit2.get("orchestration", {}).get("orchestration_state"),
    }
finally:
    if proc is not None:
        try:
            if proc.stdin:
                proc.stdin.close()
        except Exception:
            pass
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
            proc.wait(timeout=5)
    shutil.rmtree(FIXTURE, ignore_errors=True)
    summary["fixture_deleted"] = not FIXTURE.exists()
    print(json.dumps(summary, indent=2, sort_keys=True))

