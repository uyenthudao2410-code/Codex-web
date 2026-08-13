import json, os, subprocess, sys
root = r"E:\DEV\Tools-Codex-web"
py = os.path.join(root, "resources", "native-python", "python.exe")
env = os.environ.copy()
env["PYTHONPATH"] = os.path.join(root, "resources", "coding-tools-mcp")
env["CODING_TOOLS_MCP_TOOL_MODE"] = "smart"
p = subprocess.Popen([py, "-m", "coding_tools_mcp", "--stdio", "--workspace", root, "--permission-mode", "safe"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
def rpc(obj):
    p.stdin.write(json.dumps(obj, separators=(",", ":")) + "\n")
    p.stdin.flush()
    line = p.stdout.readline()
    if not line:
        raise RuntimeError("stdio server closed: " + p.stderr.read())
    return json.loads(line)
try:
    rpc({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"eocl-fresh-schema-probe","version":"1"}}})
    tools = rpc({"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}})["result"]["tools"]
    by = {t["name"]: t for t in tools}
    aw = by["agent_workflow"]["inputSchema"]["properties"]
    tc = by["task_control"]["inputSchema"]["properties"]
    req = ["execution_mode", "replan_reason", "contract_fingerprint"]
    missing_aw = [k for k in req if k not in aw]
    actions = tc["action"].get("enum", [])
    missing_actions = [k for k in ["audit", "accept", "reject"] if k not in actions]
    out = {"tool_count":len(tools),"tool_names":[t["name"] for t in tools],"agent_workflow_fields":{k:aw.get(k) for k in req},"task_control_actions":actions,"missing_aw":missing_aw,"missing_actions":missing_actions}
    print(json.dumps(out, indent=2))
    if len(tools) != 8 or missing_aw or missing_actions:
        sys.exit(3)
finally:
    try: p.stdin.close()
    except Exception: pass
    p.terminate()
    try: p.wait(timeout=5)
    except subprocess.TimeoutExpired: p.kill()
