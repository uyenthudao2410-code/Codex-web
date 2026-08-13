import json, os, subprocess, sys, tempfile, shutil
repo = r"E:\DEV\Tools-Codex-web"
fixture = tempfile.mkdtemp(prefix="eocl-live-smoke-", dir=os.path.join(repo, ".coding-tools"))
py = os.path.join(repo, "resources", "native-python", "python.exe")
env = os.environ.copy()
env["PYTHONPATH"] = os.path.join(repo, "resources", "coding-tools-mcp")
env["CODING_TOOLS_MCP_TOOL_MODE"] = "smart"
p = subprocess.Popen([py, "-m", "coding_tools_mcp", "--stdio", "--workspace", fixture, "--permission-mode", "safe"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
def rpc(obj):
    p.stdin.write(json.dumps(obj, separators=(",", ":")) + "\n")
    p.stdin.flush()
    line = p.stdout.readline()
    if not line:
        raise RuntimeError("stdio server closed: " + p.stderr.read())
    resp = json.loads(line)
    if "error" in resp:
        raise RuntimeError(json.dumps(resp["error"]))
    return resp["result"]
def tool(name, args, rid):
    result = rpc({"jsonrpc":"2.0","id":rid,"method":"tools/call","params":{"name":name,"arguments":args}})
    sc = result.get("structuredContent")
    if isinstance(sc, dict):
        return sc
    raise RuntimeError("missing structuredContent: " + json.dumps(result))
try:
    rpc({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"eocl-live-smoke","version":"1"}}})
    run = tool("agent_workflow", {"workflow":"build_release","phase":"run","objective":"Isolated EOCL live smoke; execute one deterministic no-write command and require final acceptance.","commands":["cmd /d /c echo EOCL_LIVE_SMOKE_OK"],"execution_mode":"mcp_only","verification":"none","timeout_seconds":60}, 2)
    orch = run.get("orchestration") or {}
    if orch.get("orchestration_state") != "ACCEPTING":
        raise RuntimeError("expected ACCEPTING, got " + json.dumps(orch))
    run_id = orch["run_id"]
    wave_id = orch["wave_id"]
    audit = tool("task_control", {"action":"audit","run_id":run_id,"limit":100}, 3)
    summary = audit.get("audit") or {}
    events = summary.get("events") or []
    states = []
    for e in events:
        before = e.get("state_before")
        after = e.get("state_after")
        if before and (not states or states[-1] != before): states.append(before)
        if after and (not states or states[-1] != after): states.append(after)
    required = ["PREFLIGHT","READY","ROUTED","EXECUTING","PROVING","ACCEPTING"]
    pos = -1
    for s in required:
        try: pos = states.index(s, pos + 1)
        except ValueError: raise RuntimeError("missing ordered state " + s + " in " + repr(states))
    proofs = summary.get("proofs") or []
    if not proofs:
        raise RuntimeError("audit has no proof")
    integrity = summary.get("integrity") or {}
    if not integrity.get("ok"):
        raise RuntimeError("audit integrity failed: " + json.dumps(integrity))
    accepted = tool("task_control", {"action":"accept","run_id":run_id,"reason":"isolated automation acceptance after proof and audit inspection"}, 4)
    final_orch = accepted.get("orchestration") or {}
    if final_orch.get("orchestration_state") != "CHECKPOINTED" or not accepted.get("accepted"):
        raise RuntimeError("accept failed: " + json.dumps(accepted))
    final_audit = tool("task_control", {"action":"audit","run_id":run_id,"limit":100}, 5)
    fi = (final_audit.get("audit") or {}).get("integrity") or {}
    if not fi.get("ok"):
        raise RuntimeError("final integrity failed")
    out = {"run_id":run_id,"wave_id":wave_id,"state_sequence":states,"proofs":[{"proof_id":x.get("proof_id"),"input_fingerprint":x.get("input_fingerprint"),"status":x.get("status"),"command":x.get("command")} for x in proofs],"accepting_integrity":integrity,"final_state":final_orch.get("orchestration_state"),"final_integrity":fi,"final_acceptance_required":final_orch.get("final_acceptance_required")}
    print(json.dumps(out, indent=2))
finally:
    try: p.stdin.close()
    except Exception: pass
    p.terminate()
    try: p.wait(timeout=5)
    except subprocess.TimeoutExpired: p.kill()
    shutil.rmtree(fixture, ignore_errors=True)
