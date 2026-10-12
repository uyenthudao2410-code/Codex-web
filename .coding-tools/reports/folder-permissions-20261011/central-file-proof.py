"""Live fixture proof; pipe into remote Ubuntu Python, never copy credentials."""
import base64
import hashlib
import json
import pathlib
import shlex
import stat
import sys
import time
import urllib.error
import urllib.request
import uuid
import zlib

BINDING = "bind_3e05bf64cb3e4bab93d930ae1692bebb"
FIXTURE = "tests/fixtures/folder-permissions-20261011.txt"
INITIAL = b"folder permission read/write verification pending\n"
UPDATED = b"folder permission read/write verification passed\n"
PHASE = sys.argv[1]
STEP = PHASE
def env(path):
    values = {}
    for line in pathlib.Path(path).read_text().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, value = line.split("=", 1)
        parsed = shlex.split(value, comments=True)
        values[key.strip()] = parsed[0] if parsed else ""
    return values

def emit(value):
    print(json.dumps(value, separators=(",", ":")), flush=True)

def require(condition, code):
    if not condition:
        raise RuntimeError(code)

configuration = env("/home/svhome/.config/codex-control-plane/control-plane.env")
tunnel = env("/home/svhome/.config/codex-control-plane/mcp-tunnel.env")
header_file = pathlib.Path(tunnel["CONTROL_PLANE_MCP_AUTH_HEADER_FILE"])
require(header_file.is_file() and not header_file.is_symlink()
        and stat.S_IMODE(header_file.stat().st_mode) in (0o400, 0o600), "HEADER_FILE_MODE_INVALID")
authorization = header_file.read_text().strip()
require(authorization.startswith("Bearer "), "HEADER_FORMAT_INVALID")
mcp_origin = "http://127.0.0.1:" + configuration.get("CONTROL_PLANE_MCP_PORT", "8766")
operator_bind = configuration["CONTROL_PLANE_BIND"]
if operator_bind in ("0.0.0.0", "::"):
    operator_bind = "127.0.0.1"
operator_origin = "http://" + operator_bind + ":" + configuration["CONTROL_PLANE_PORT"]
request_number = 0

def rpc(method, params):
    global request_number
    request_number += 1
    request = urllib.request.Request(mcp_origin + "/mcp", data=json.dumps({
        "jsonrpc": "2.0", "id": request_number, "method": method, "params": params,
    }).encode(), headers={"Authorization": authorization, "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.load(response)
    require("error" not in payload, "MCP_RPC_ERROR")
    result = payload["result"]
    if result.get("isError"):
        code = result.get("structuredContent", {}).get("code", "MCP_CALL_FAILED")
        raise RuntimeError(str(code))
    return result

def call(tool, arguments):
    return rpc("tools/call", {"name": tool, "arguments": arguments})["structuredContent"]

def await_action(tool, operation, action_id, success):
    deadline = time.monotonic() + 90
    last = None
    while time.monotonic() < deadline:
        result = call(tool, {"operation": operation, "action_id": action_id})
        action = result.get("action", {})
        state = (result.get("execution"), action.get("delivery_state"), action.get("receipt_status"))
        if state != last:
            emit({"phase": operation, "action_id": action_id, "execution": state[0],
                  "delivery_state": state[1], "receipt_status": state[2]})
            last = state
        require(action.get("delivery_state") != "reconcile_required" and result.get("patch_effect_state") != "unknown",
                "ACTION_RECONCILIATION_REQUIRED")
        if success(result):
            return result
        require(action.get("receipt_status") not in ("rejected", "failed", "denied"), "ACTION_RECEIPT_REJECTED")
        time.sleep(2)
    raise RuntimeError("ACTION_PROOF_TIMEOUT")

def accept(action_id):
    global STEP
    origin = configuration["CONTROL_PLANE_WEB_ORIGIN"]
    login = urllib.request.Request(operator_origin + "/v1/ui/login", data=json.dumps({
        "operator_token": configuration["CONTROL_PLANE_OPERATOR_TOKEN"],
    }).encode(), headers={"Origin": origin, "Content-Type": "application/json"}, method="POST")
    STEP = 'operator_login'
    with urllib.request.urlopen(login, timeout=15) as response:
        cookie = response.headers["Set-Cookie"].split(";", 1)[0]
        csrf = json.load(response)["csrf_token"]
    def session_post(route, body):
        request = urllib.request.Request(operator_origin + route, data=json.dumps(body).encode(), headers={
            "Origin": origin, "Cookie": cookie, "X-Control-Plane-CSRF": csrf, "Content-Type": "application/json",
        }, method="POST")
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.load(response)
    try:
        STEP = 'patch_acceptance'
        result = session_post("/v1/ui/patch-acceptances/" + action_id, {
            "decision": "accepted", "note": "Fixture read/write result independently verified",
        })
        emit({"phase": "patch_acceptance", "action_id": action_id, "decision": result.get("decision")})
    finally:
        session_post("/v1/ui/logout", {})

task_id = None
try:
    if PHASE == "accept":
        accept(sys.argv[2])
    elif PHASE == "close":
        task_id = sys.argv[2]
    elif PHASE == "proof":
        contract = rpc("tools/list", {})["_meta"]["control_plane"]["tool_contract"]
        emit({"phase": "discovery", "contract": contract})
        task = call("workspace_context", {"operation": "task_open", "binding_id": BINDING,
                    "label": "Folder permission fixture read/write", "idempotency_key": "folder-proof-" + uuid.uuid4().hex})
        task_id = task["task"]["task_id"]
        emit({"phase": "task_open", "task_id": task_id})
        call("task_control", {"operation": "writer_claim", "task_id": task_id})
        def read(expected):
            queued = call("workspace_context", {"operation": "read_file", "binding_id": BINDING,
                          "task_id": task_id, "path": FIXTURE, "idempotency_key": "read-" + uuid.uuid4().hex,
                          "expected_facade_contract": contract, "start_line": 1, "max_lines": 20, "max_bytes": 4096})
            action_id = queued["action_id"]
            result = await_action("workspace_context", "read_status", action_id, lambda row: row.get("file_accessed") is True)
            file = result["file_read"]["file"]
            digest = hashlib.sha256(expected).hexdigest()
            require(file["content_sha256"] == digest and file["content"].encode() == expected, "FIXTURE_READ_MISMATCH")
            emit({"phase": "file_verified", "action_id": action_id, "content_sha256": digest, "content_matches": True})
        read(INITIAL)
        preimage = hashlib.sha256(INITIAL).hexdigest()
        postimage = hashlib.sha256(UPDATED).hexdigest()
        patch = "\n".join(("*** Begin Patch", "*** Write Exact File: " + FIXTURE,
            "@@ encoding=zlib-base64 preimage_sha256=" + preimage + " postimage_sha256=" + postimage,
            "+" + base64.b64encode(zlib.compress(UPDATED)).decode(), "*** End Patch", ""))
        queued = call("agent_workflow", {"operation": "apply_patch", "binding_id": BINDING,
            "task_id": task_id, "path": FIXTURE, "preimage_sha256": preimage,
            "patch_sha256": hashlib.sha256(patch.encode()).hexdigest(), "validation_profile": "targeted",
            "patch_envelope": patch, "idempotency_key": "patch-" + uuid.uuid4().hex,
            "expected_facade_contract": contract})
        action_id = queued["action_id"]
        await_action("agent_workflow", "patch_status", action_id,
                     lambda row: row.get("patch_applied") is True and row.get("patch_effect_state") == "verified_applied")
        emit({"phase": "patch_verified", "action_id": action_id, "postimage_sha256": postimage})
        read(UPDATED)
        emit({"phase": "proof", "ok": True, "task_id": task_id, "patch_action_id": action_id,
              "expected_local_sha256": postimage})
    else:
        raise RuntimeError("UNKNOWN_PHASE")
except urllib.error.HTTPError as error:
    emit({"phase": PHASE, "step": STEP, "ok": False, "error": "HTTP_ERROR", "http_status": error.code})
    sys.exit(1)
except Exception as error:
    emit({"phase": PHASE, "ok": False, "error": str(error) if isinstance(error, RuntimeError) else type(error).__name__})
    sys.exit(1)
finally:
    if task_id:
        for tool, args in (("task_control", {"operation": "writer_release", "task_id": task_id, "reason": "fixture_complete"}),
                           ("workspace_context", {"operation": "task_close", "task_id": task_id})):
            try:
                result = call(tool, args)
                emit({"phase": args["operation"], "task_id": task_id,
                      "closed": result.get("task", {}).get("closed_at_ms") is not None})
            except Exception:
                emit({"phase": args["operation"], "ok": False, "task_id": task_id, "error": "CLEANUP_FAILED"})
