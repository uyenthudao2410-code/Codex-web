"""One-dispatch r13_5h trial bound to a new receipt-pinned exact-scope window."""
from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import sqlite3
import stat
import sys
import time
import urllib.request
import zlib

sys.dont_write_bytecode = True
COMMON_SHA256 = "25f2d15359ff49a50e1ded411d40f1f029fb6067390c68aff9b93bda0130d986"
NATIVE_TOOL_SHA256 = "0e4733844a471814a3a6240fa9c0423b56195ab80f6e5283b5c978e28edaaed4"
HERE = Path(__file__).resolve().parent
HEAD = "2c554f59cb7b8ffc86ce5e0e28076c792777642f"
TARGET = "tests/fixtures/initial-proof-canary-target.cjs"
CHECKER = "tests/fixtures/initial-proof-canary-check.cjs"
PRE = "90363c394e12dd67f9003ef96b033e739c7837b34c238238966df623d9e55650"
POST = "d1edd529d09c7d4f71dfbb9e9b9e53010cc43a616cf1247594ddf4d705b84a1e"
PATCH = "77f2c282c91f3627e721d0d68bf1fa821bad21575ec136204353894b18ce5e4a"
CHECK = "059c4e83fcbeb07b293312988975b7267d8ab8428872e5ff1211dbf059800230"
PLAN_SHA = "235ecd2dc1bf8b49b21648ffd24df378088916e65e2420cb383fa79a6439afe7"
PLAN = {"argv": ["node", "--test", CHECKER], "cwd": "", "timeout_ms": 60000, "max_output_bytes": 32768}
OLD_RUN = "95e909f0040a448faa9f1f3257e2ee2c"
OLD_WAVE = "c101beadfc6d4f2fbc13845052c84693"
OLD_RUN_SHA = "a167681ee42f25bc76a6eb03f63dfd91ef382924573205835f07d5ab01eef590"
OLD_WAVE_SHA = "59d351b7afbc33b8e8f8f2f35bf5dfdd1c8a319bab93dd005481f4df36862bce"
SERVICE_SCOPE = "private_tunnel_service"
NEXT_OPERATION_DIR = Path("/home/svhome/.local/state/codex-control-plane/owner-operations/r13-initial-verification-5h")
NEXT_AUTHORITY_MARKER = NEXT_OPERATION_DIR / "authority-renewal-public.json"
CANARY_OPERATION_DIR = NEXT_OPERATION_DIR / "canary"
NEXT_OPERATION = "owner_approved_r13_initial_verification_5h"
PRIOR_AUTHORITY_MARKER = NEXT_OPERATION_DIR.parent / "r12-initial-verification-60m/authority-renewal-public.json"
PRIOR_AUTHORITY_SHA256 = "a3c5c2ee239644a3937fa5f81c7fc14b89544bfde82c4bea56a928ddda408487"
MIN_CANARY_REMAINING_MS = 720000
EXPIRED_APPROVAL = "call_flEpmLChKJPZsbnlAAXR5byS"
_prior_marker_path = None
_prior_marker_sha256 = None


class Failure(Exception):
    def __init__(self, code):
        self.code = code


def require(condition, code):
    if not condition:
        raise Failure(code)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def digest(value):
    return sha(canonical(value))


def load_common():
    path = HERE / "r11_common.py"
    require(path.is_file() and not path.is_symlink() and sha(path.read_bytes()) == COMMON_SHA256,
            "COMMON_GUARD_HASH_MISMATCH")
    require(os.name == "posix" and path.stat().st_uid == os.getuid()
            and stat.S_IMODE(path.stat().st_mode) == 0o600, "COMMON_GUARD_ACL_INVALID")
    spec = importlib.util.spec_from_file_location("r11_pinned_canary_common", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def packet():
    raw = (HERE / "patch-envelope.txt").read_bytes()
    require(sha(raw) == PATCH and not raw.endswith(b"\n"), "PATCH_PACKET_CHANGED")
    lines = raw.decode("utf-8").splitlines()
    require(len(lines) == 5 and lines[0] == "*** Begin Patch"
            and lines[1] == "*** Write Exact File: " + TARGET
            and lines[2] == "@@ encoding=zlib-base64 preimage_sha256=" + PRE + " postimage_sha256=" + POST
            and lines[4] == "*** End Patch", "PATCH_PACKET_INVALID")
    post = zlib.decompress(base64.b64decode(lines[3][1:], validate=True))
    require(sha(post) == POST and len(post) == 414 and digest(PLAN) == PLAN_SHA, "POSTIMAGE_OR_PLAN_CHANGED")
    return raw.decode(), post


def stage(workspace):
    _, post = packet()
    root = Path(workspace).resolve(strict=True)
    require(str(root).lower().replace("/", "\\") == r"e:\github\tools-codex-web", "LOCAL_WORKSPACE_MISMATCH")
    before = (root / TARGET).read_bytes()
    require(sha(before) == PRE and sha((root / CHECKER).read_bytes()) == CHECK, "LOCAL_SOURCE_OR_CHECKER_CHANGED")
    require(before.replace(b"['passed', 'failed', 'timed_out']", b"['passed']", 1) == post,
            "PATCH_IS_NOT_EXACT_ONE_CONDITION_FIX")
    return {"phase": "stage", "source_head_expected": HEAD, "target": TARGET, "checker": CHECKER,
            "preimage_sha256": PRE, "postimage_sha256": POST, "patch_sha256": PATCH,
            "checker_sha256": CHECK, "plan_sha256": PLAN_SHA, "local_only": True, "remote_mutation": False}


def private_json(path):
    require(path.is_absolute() and path.is_file() and not path.is_symlink(), "PRIVATE_INPUT_UNSAFE")
    info = path.stat()
    require(info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) in (0o400, 0o600), "PRIVATE_INPUT_ACL_INVALID")
    value = json.loads(path.read_bytes())
    require(isinstance(value, dict), "PRIVATE_INPUT_INVALID")
    return value


def pins_input(common):
    global _prior_marker_path, _prior_marker_sha256
    pins = private_json(HERE / "pins.json")
    expected = {"requested_at_ms", "expires_at_ms", "context_id", "pilot_id", "service_instance_id",
                "activation_epoch", "runtime_instance_id", "mcp_server_instance_id", "contract_version",
                "native_tool_contract_sha256", "native_preflight", "approval_id",
                "authority_receipt_sha256", "authority_marker_sha256"}
    require(set(pins) == expected, "PINS_FIELDS_INVALID")
    require(all(isinstance(pins[field], str) and 1 <= len(pins[field]) <= 128
                for field in ("context_id", "pilot_id", "service_instance_id", "activation_epoch",
                              "runtime_instance_id", "mcp_server_instance_id", "contract_version")), "PINS_IDENTITY_INVALID")
    require(pins["approval_id"] == "call_a60e931056bd402b997c6c10b0796d81", "NEW_R13_5H_APPROVAL_REQUIRED")
    require(all(re.fullmatch(r"[a-f0-9]{64}", str(pins[field]))
                for field in ("authority_receipt_sha256", "authority_marker_sha256")), "AUTHORITY_DIGEST_INVALID")
    authority_receipt_path = HERE / "authority-receipt.json"
    require(sha(common.protected_file(authority_receipt_path)) == pins["authority_receipt_sha256"],
            "AUTHORITY_RECEIPT_HASH_CHANGED")
    authority_receipt = private_json(authority_receipt_path)
    rows = authority_receipt.get("public_receipts", [authority_receipt])
    require(isinstance(rows, list), "AUTHORITY_RECEIPT_INVALID")
    receipts = [row for row in rows if isinstance(row, dict) and row.get("ok") is True
                and row.get("phase") == "r13_5h_intake_reopened"]
    require(len(receipts) == 1, "EXACT_R13_5H_REOPEN_RECEIPT_REQUIRED")
    receipt = receipts[0]
    require(sha(common.protected_file(NEXT_AUTHORITY_MARKER)) == pins["authority_marker_sha256"]
            == receipt.get("next_marker_sha256"), "NEW_AUTHORITY_MARKER_HASH_CHANGED")
    authority = private_json(NEXT_AUTHORITY_MARKER)
    require(authority.get("phase") == "intake_reopened", "AUTHORITY_NOT_REOPENED")
    target = {"operation": NEXT_OPERATION, "binding_id": common.BINDING, "device_id": common.DEVICE,
              "workspace_id": common.WORKSPACE, "workspace_generation": common.GENERATION,
              "root": common.LOCAL_ROOT, "profile": common.LOCAL_PROFILE, "source_revision": common.REVISION,
              "approval_id": pins["approval_id"], "approved_duration_ms": 18000000}
    require(all(authority.get(key) == value for key, value in target.items()), "NEXT_AUTHORITY_SCOPE_OR_APPROVAL_CHANGED")
    require(receipt.get("host") == common.HOST and receipt.get("service") == common.SERVICE
            and receipt.get("admission") == "scoped_pilot" and receipt.get("duration_ms") == 18000000
            and receipt.get("prior_marker_unchanged") is True
            and receipt.get("deployed") is False and receipt.get("service_restarted") is False
            and all(receipt.get(key) == value for key, value in target.items()
                    if key not in {"operation", "approved_duration_ms"}), "R13_5H_REOPEN_RECEIPT_SCOPE_CHANGED")
    for field in ("requested_at_ms", "expires_at_ms", "context_id", "pilot_id", "service_instance_id"):
        require(authority.get(field) == pins[field] == receipt.get(field), "AUTHORITY_PIN_MISMATCH")
    require(pins["context_id"] != "ctx_d7a539dd85264a62951fddad0ffa2f23"
            and pins["pilot_id"] != "pilot_98c0b502568a4f888b3106838004c117", "EXPIRED_R12_AUTHORITY_CANNOT_BE_REUSED")
    for field in ("activation_epoch", "runtime_instance_id", "mcp_server_instance_id", "contract_version"):
        require(authority.get(field) == pins[field], "REOPENED_NATIVE_PIN_MISMATCH")
    prior = private_json(PRIOR_AUTHORITY_MARKER)
    prior_sha = sha(common.protected_file(PRIOR_AUTHORITY_MARKER))
    require(authority.get("prior_marker_sha256") == receipt.get("prior_marker_sha256") == prior_sha == PRIOR_AUTHORITY_SHA256
            and prior.get("operation") == "owner_approved_r12_initial_verification_60m"
            and prior.get("phase") == "intake_reopened"
            and prior.get("requested_at_ms") == 1791747735200 and prior.get("expires_at_ms") == 1791751335200
            and prior.get("binding_id") == common.BINDING and prior.get("root") == common.LOCAL_ROOT
            and prior.get("profile") == common.LOCAL_PROFILE, "PREVIOUS_AUTHORITY_MARKER_CHANGED")
    _prior_marker_path, _prior_marker_sha256 = PRIOR_AUTHORITY_MARKER, prior_sha
    require(type(pins["requested_at_ms"]) is int and type(pins["expires_at_ms"]) is int
            and pins["expires_at_ms"] - pins["requested_at_ms"] == 18000000, "AUTHORITY_WINDOW_INVALID")
    require(re.fullmatch(r"[a-f0-9]{64}", str(pins["native_tool_contract_sha256"])), "NATIVE_CONTRACT_SHA_INVALID")
    require(pins["native_tool_contract_sha256"] == NATIVE_TOOL_SHA256
            and pins["contract_version"] == "sha256:" + NATIVE_TOOL_SHA256, "R13_5H_NATIVE_CONTRACT_NOT_PINNED")
    return pins


def authority_guard(common, pins, health, overview, grant, *, dispatch):
    now = overview["observed_at_ms"]
    require(health.get("declared_source_revision") == common.REVISION and health.get("schema_version") == 29
            and health.get("ok") is True and health.get("package_source_sha256") == common.PACKAGE
            and health.get("expected_package_source_sha256") == common.PACKAGE
            and health.get("service_instance_id") == pins["service_instance_id"], "R13_5H_SERVICE_PIN_CHANGED")
    common.renewed_authority(overview, pins)
    require(overview["admission"]["admission_mode"] == "scoped_pilot"
            and grant["expires_at_ms"] >= pins["expires_at_ms"], "SCOPED_TRIAL_OR_GRANT_CHANGED")
    rows = [row for row in overview["nodes"] if row.get("device_id") == common.DEVICE]
    require(len(rows) == 1, "NODE_NOT_UNIQUE")
    node = rows[0]
    for field in ("activation_epoch", "runtime_instance_id", "mcp_server_instance_id", "contract_version"):
        require(node.get(field) == pins[field], "NATIVE_INSTANCE_OR_CONTRACT_CHANGED")
    require(node.get("readiness") == "ready" and node.get("policy_state") == "enabled"
            and type(node.get("last_seen_at_ms")) is int and 0 <= now - node["last_seen_at_ms"] < 60000
            and type(node.get("policy_expires_at_ms")) is int
            and now < node["policy_expires_at_ms"] <= node["last_seen_at_ms"] + 60000,
            "NODE_NOT_READY_OR_POLICY_TELEMETRY_EXPIRED")
    if dispatch:
        native = pins["native_preflight"]
        require(set(native) == {"observed_at_ms", "source_head", "preimage_sha256", "checker_sha256",
                                "old_run_sha256", "old_wave_sha256", "no_active_jobs", "receipt_sha256"},
                "NATIVE_PREFLIGHT_FIELDS_INVALID")
        require(0 <= now - native["observed_at_ms"] < 60000 and pins["expires_at_ms"] - now >= MIN_CANARY_REMAINING_MS,
                "PREFLIGHT_STALE_OR_TRIAL_TOO_SHORT")
        require(native["source_head"] == HEAD and native["preimage_sha256"] == PRE
                and native["checker_sha256"] == CHECK and native["old_run_sha256"] == OLD_RUN_SHA
                and native["old_wave_sha256"] == OLD_WAVE_SHA and native["no_active_jobs"] is True
                and re.fullmatch(r"[a-f0-9]{64}", str(native["receipt_sha256"])), "NATIVE_PREFLIGHT_MISMATCH")


def mcp_credentials(common):
    raw = common.protected_file(common.HOME_DIR / ".config/codex-control-plane/mcp-tunnel.env").decode()
    values = {}
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        require(key not in values, "TUNNEL_CONFIG_DUPLICATE_KEY")
        parts = shlex.split(value, comments=True)
        require(len(parts) <= 1, "TUNNEL_CONFIG_VALUE_INVALID")
        values[key] = parts[0] if parts else ""
    header = Path(values["CONTROL_PLANE_MCP_AUTH_HEADER_FILE"])
    require(header.is_absolute() and header.is_file() and not header.is_symlink()
            and header.resolve().is_relative_to(common.HOME_DIR), "HEADER_PATH_UNSAFE")
    info = header.stat()
    require(info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) in (0o400, 0o600), "HEADER_ACL_INVALID")
    authorization = header.read_text().strip()
    require(authorization.startswith("Bearer ") and len(authorization) > 7
            and "\n" not in authorization and "\r" not in authorization, "HEADER_FORMAT_INVALID")
    port = common.environment().get("CONTROL_PLANE_MCP_PORT", "8766")
    require(port.isdigit() and 1 <= int(port) <= 65535, "MCP_PORT_INVALID")
    return "http://127.0.0.1:" + port, authorization


def rpc(origin, authorization, method, params):
    request_id = str(time.time_ns())
    request = urllib.request.Request(origin + "/mcp", data=canonical({"jsonrpc": "2.0", "id": request_id,
        "method": method, "params": params}), headers={"Authorization": authorization,
        "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read(1024 * 1024 + 1)
        require(len(raw) <= 1024 * 1024, "MCP_RESPONSE_TOO_LARGE")
        result = json.loads(raw)
    except Failure:
        raise
    except Exception:
        raise Failure("MCP_TRANSPORT_UNCERTAIN_NO_RETRY") from None
    require(isinstance(result, dict) and result.get("id") == request_id and "error" not in result,
            "MCP_PROTOCOL_ERROR_NO_RETRY")
    result = result.get("result")
    require(isinstance(result, dict) and result.get("isError") is not True, "MCP_TOOL_REJECTED_NO_RETRY")
    return result


def call(origin, authorization, name, arguments):
    result = rpc(origin, authorization, "tools/call", {"name": name, "arguments": arguments})
    value = result.get("structuredContent")
    require(isinstance(value, dict), "MCP_STRUCTURED_RESPONSE_INVALID")
    return value


def branch(tools, name, operation):
    selected = [tool for tool in tools if tool.get("name") == name]
    require(len(selected) == 1, "LIVE_TOOL_MISSING_OR_DUPLICATE")
    variants = [item for item in selected[0]["inputSchema"].get("oneOf", [])
                if item.get("properties", {}).get("operation", {}).get("enum") == [operation]]
    require(len(variants) == 1 and variants[0].get("additionalProperties") is False, "LIVE_OPERATION_SCHEMA_CHANGED")
    return selected[0], variants[0]


def live_contract(listed, inventory, binding, principal):
    meta = listed.get("_meta", {}).get("control_plane", {})
    contract = meta.get("tool_contract")
    require(isinstance(contract, dict) and set(contract) == {"schema_version", "profile", "sha256"}
            and type(contract["schema_version"]) is int and contract["schema_version"] >= 1
            and isinstance(contract["profile"], str) and len(contract["profile"]) >= 3
            and re.fullmatch(r"[a-f0-9]{64}", str(contract["sha256"])), "LIVE_FACADE_CONTRACT_INVALID")
    require(contract == inventory.get("tool_contract") and meta.get("access_scope") == SERVICE_SCOPE
            and inventory.get("principal_id") == principal, "LIST_INVENTORY_CONTRACT_OR_PRINCIPAL_MISMATCH")
    targets = inventory.get("targets")
    require(isinstance(targets, list) and len(targets) == 1 and targets[0].get("binding_id") == binding,
            "MCP_TARGET_SCOPE_CHANGED")
    tool, schema = branch(listed["tools"], "agent_workflow", "apply_patch")
    cp = tool.get("_meta", {}).get("control_plane", {})
    require(cp.get("capability_state") == "standing_write"
            and cp.get("implemented_operations") == ["apply_patch", "patch_status"]
            and cp.get("access_scope") == SERVICE_SCOPE, "STANDING_WRITE_NOT_ADVERTISED")
    fields = {"operation", "binding_id", "task_id", "path", "preimage_sha256", "patch_sha256",
              "validation_profile", "patch_envelope", "idempotency_key", "expected_facade_contract", "verification"}
    require(set(schema["properties"]) == fields and set(schema["required"]) == fields - {"verification"},
            "APPLY_PATCH_SCHEMA_CHANGED")
    verification = schema["properties"]["verification"]
    require(set(verification.get("properties", {})) == set(PLAN)
            and set(verification.get("required", [])) == set(PLAN)
            and verification.get("additionalProperties") is False, "INITIAL_VERIFICATION_SCHEMA_CHANGED")
    for name, operation, required, allowed in (
        ("workspace_context", "task_open", {"operation", "binding_id", "label", "idempotency_key"}, None),
        ("workspace_context", "task_close", {"operation", "task_id"}, None),
        ("task_control", "writer_claim", {"operation", "task_id"}, None),
        ("task_control", "writer_release", {"operation", "task_id"}, {"operation", "task_id", "reason"}),
        ("agent_workflow", "patch_status", {"operation", "action_id"}, None),
    ):
        _, part = branch(listed["tools"], name, operation)
        require(set(part["required"]) == required and set(part["properties"]) == (allowed or required),
                "TASK_OR_STATUS_SCHEMA_CHANGED")
    return contract


def exclusive(path, value):
    require(not path.exists() and not path.is_symlink(), "IMMUTABLE_RECEIPT_ALREADY_EXISTS_NO_REPLAY")
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(canonical(value)); handle.flush(); os.fsync(handle.fileno())
    if os.name == "posix":
        directory = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory)
        finally:
            os.close(directory)


def own_context_view(common, pins, database, overview):
    path = CANARY_OPERATION_DIR / "canary-dispatch.json"
    if not path.exists():
        return overview
    marker = private_json(path)
    require(marker.get("pins_sha256") == digest(pins), "TRIAL_PINS_CHANGED_NO_REPLAY")
    family = ids(common, database, marker)
    if family.get("action_id") is None:
        return overview
    connection = sqlite3.connect(database.as_uri() + "?mode=ro", uri=True, timeout=5)
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only=ON")
        connection.execute("BEGIN")
        action = connection.execute("SELECT * FROM actions WHERE action_id=?", (family["action_id"],)).fetchone()
        require(action is not None, "OWN_ACTION_CONTEXT_LINK_MISSING")
        action = dict(action)
        request = connection.execute("SELECT * FROM work_requests WHERE request_id=?", (family["request_id"],)).fetchone()
        context = connection.execute("SELECT * FROM contexts WHERE context_id=?", (action["context_id"],)).fetchone()
        owner_context = connection.execute("SELECT * FROM contexts WHERE context_id=?", (pins["context_id"],)).fetchone()
        require(request is not None and context is not None and owner_context is not None, "OWN_ACTION_CONTEXT_LINK_MISSING")
        request, context, owner_context = map(dict, (request, context, owner_context))
        require(action["request_id"] == family["request_id"] == request["request_id"]
            and action["context_id"] == request["context_id"] == context["context_id"] != pins["context_id"]
            and action["owner_id"] == request["owner_id"] == context["owner_id"] == owner_context["owner_id"],
            "OWN_ACTION_CONTEXT_CAUSAL_LINK_CHANGED")
        require(all(row["binding_id"] == common.BINDING and row["device_id"] == common.DEVICE
            and row["workspace_id"] == common.WORKSPACE and row["workspace_generation"] == common.GENERATION
            for row in (action, context, owner_context))
            and action["endpoint_id"] == context["endpoint_id"] == owner_context["endpoint_id"], "OWN_ACTION_CONTEXT_TARGET_CHANGED")
        require(action["created_at_ms"] == request["created_at_ms"] == context["created_at_ms"]
            and pins["requested_at_ms"] <= context["created_at_ms"] < pins["expires_at_ms"]
            and action["expires_at_ms"] == request["expires_at_ms"] == context["expires_at_ms"] <= pins["expires_at_ms"]
            and context["expires_at_ms"] - context["created_at_ms"] == 600000
            and context["closed_at_ms"] is None and request["canceled_at_ms"] is None,
            "OWN_ACTION_CONTEXT_WINDOW_CHANGED")
        require(connection.execute("SELECT COUNT(*) FROM actions WHERE context_id=?", (context["context_id"],)).fetchone()[0] == 1
            and connection.execute("SELECT COUNT(*) FROM work_requests WHERE context_id=?", (context["context_id"],)).fetchone()[0] == 1,
            "OWN_ACTION_CONTEXT_REUSED")
    finally:
        connection.close()
    rows = [row for row in overview["contexts"] if row.get("context_id") == context["context_id"]]
    require(len(rows) == 1 and all(rows[0].get(key) == value for key, value in context.items()), "OWN_CONTEXT_OVERVIEW_CHANGED")
    # ids() has proved this trial's immutable intent/task/action family and
    # protected history. The original guard still checks every other context.
    return {**overview, "contexts": [row for row in overview["contexts"] if row.get("context_id") != context["context_id"]]}


def operator_observation(common, pins, *, initial):
    if initial:
        origin, token, database, health, snapshot, overview, grant = common.inspect()
    else:
        config = common.environment()
        bind = config.get("CONTROL_PLANE_BIND", "127.0.0.1")
        require(bind in {"127.0.0.1", "0.0.0.0", "::", common.HOST}, "SERVICE_BIND_CHANGED")
        origin = "http://" + (common.HOST if bind == common.HOST else "127.0.0.1") + ":" + config.get("CONTROL_PLANE_PORT", "8765")
        token = config["CONTROL_PLANE_OPERATOR_TOKEN"]
        database = Path(config["CONTROL_PLANE_DB"])
        health, overview = common.api(origin, token, "/healthz"), common.api(origin, token, "/v1/ui/overview")
        grant, snapshot = common.target(overview), None
    if not initial:
        overview = own_context_view(common, pins, database, overview)
    authority_guard(common, pins, health, overview, grant, dispatch=initial)
    return database, health, snapshot, overview, grant


def preflight(common, pins):
    packet()
    database, health, snapshot, overview, grant = operator_observation(common, pins, initial=True)
    origin, auth = mcp_credentials(common)
    listed = rpc(origin, auth, "tools/list", {})
    inventory = call(origin, auth, "workspace_context", {"operation": "inventory"})
    contract = live_contract(listed, inventory, common.BINDING, common.PRINCIPAL)
    public = common.public_observation(health, snapshot, overview, grant)
    return database, origin, auth, contract, public


def ids(common, database, marker):
    require(database.is_absolute() and database.is_file() and not database.is_symlink(), "DATABASE_TARGET_UNSAFE")
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True, timeout=5) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only=ON"); connection.execute("BEGIN")
        tasks = [dict(row) for row in connection.execute("SELECT * FROM mcp_task_open_idempotency WHERE principal_id=? AND idempotency_key=?",
                    (common.PRINCIPAL, marker["task_key"]))]
        intents = [dict(row) for row in connection.execute("SELECT * FROM mcp_standing_patch_intents WHERE principal_id=? AND idempotency_key=?",
                    (common.PRINCIPAL, marker["patch_key"]))]
        require(len(tasks) <= 1 and len(intents) <= 1, "CANARY_FAMILY_NOT_UNIQUE")
        task_id = tasks[0]["task_id"] if tasks else None
        action_id = intents[0]["action_id"] if intents else None
        if task_id:
            task = connection.execute("SELECT * FROM mcp_task_sessions WHERE task_id=?", (task_id,)).fetchone()
            require(task is not None and task["principal_id"] == common.PRINCIPAL
                    and task["binding_id"] == common.BINDING and task["device_id"] == common.DEVICE
                    and task["workspace_id"] == common.WORKSPACE and task["workspace_generation"] == common.GENERATION,
                    "CANARY_TASK_TARGET_CHANGED")
        open_tasks = [row[0] for row in connection.execute("SELECT task_id FROM mcp_task_sessions WHERE closed_at_ms IS NULL")]
        open_writers = [row[0] for row in connection.execute("SELECT task_id FROM mcp_task_writer_leases WHERE released_at_ms IS NULL")]
        require(all(item == task_id for item in open_tasks + open_writers)
                and len(open_tasks) <= 1 and len(open_writers) <= 1, "UNRELATED_OPEN_TASK_OR_WRITER")
        history = []
        for action in connection.execute("SELECT * FROM actions WHERE delivery_state!='settled' AND action_id!=? ORDER BY action_id", (action_id or "",)):
            value = dict(action); family = {"action": value}
            for table, ordering in (("delivery_attempts", "attempt_number, attempt_id"), ("receipts", "received_at_ms, receipt_id"),
                                    ("action_reconciliations", "action_id"), ("action_dispatch_dispositions", "action_id")):
                family[table] = [dict(row) for row in connection.execute(f"SELECT * FROM {table} WHERE action_id=? ORDER BY {ordering}", (value["action_id"],))]
            history.append(family)
        require(tuple(row["action"]["action_id"] for row in history) == common.HISTORICAL_IDS
                and digest(history) == marker["historical_action_families_sha256"], "HISTORICAL_FAMILY_CHANGED")
        require(int(connection.execute("PRAGMA user_version").fetchone()[0]) == 29, "DATABASE_SCHEMA_CHANGED")
        require(connection.execute("SELECT COUNT(*) FROM actions").fetchone()[0] == marker["baseline_actions"] + bool(action_id)
                and connection.execute("SELECT COUNT(*) FROM mcp_task_sessions").fetchone()[0] == marker["baseline_tasks"] + bool(task_id), "UNRELATED_ACTION_OR_TASK_CREATED")
        acceptances = [dict(row) for row in connection.execute("SELECT * FROM mcp_patch_acceptances ORDER BY action_id")]
        require(digest(acceptances) == marker["patch_acceptances_sha256"], "CENTRAL_ACCEPTANCE_CHANGED")
        if not action_id:
            return {"task_id": task_id, "action_id": None, "settled": False, "state": "dispatch_effect_not_located_do_not_replay"}
        intent = intents[0]
        require(intent["task_id"] == task_id and intent["binding_id"] == common.BINDING
                and intent["relative_path"] == TARGET and intent["preimage_sha256"] == PRE
                and intent["patch_sha256"] == PATCH and intent["patch_envelope"] == packet()[0]
                and json.loads(intent["verification_json"]) == PLAN
                and {"schema_version": intent["facade_schema_version"], "profile": intent["facade_profile"], "sha256": intent["facade_contract_sha256"]} == marker["facade_contract"], "CANARY_INTENT_CHANGED")
        action = dict(connection.execute("SELECT * FROM actions WHERE action_id=?", (action_id,)).fetchone())
        require(action["binding_id"] == common.BINDING and action["request_id"] == intent["request_id"]
                and action["expires_at_ms"] <= marker["expires_at_ms"], "CANARY_ACTION_SCOPE_CHANGED")
        link = connection.execute("SELECT task_id FROM mcp_task_action_links WHERE action_id=?", (action_id,)).fetchone()
        require(link is not None and link[0] == task_id, "CANARY_TASK_LINK_CHANGED")
        attempts = [dict(row) for row in connection.execute("SELECT * FROM delivery_attempts WHERE action_id=? ORDER BY attempt_number", (action_id,))]
        require(len(attempts) <= 1, "MULTIPLE_DELIVERY_ATTEMPTS_REQUIRE_REVIEW")
        receipts = [dict(row) for row in connection.execute("SELECT * FROM receipts WHERE action_id=? ORDER BY received_at_ms, receipt_id", (action_id,))]
        completed = [row for row in receipts if row["receipt_state"] == "completed"]
        require(len(completed) <= 1, "MULTIPLE_COMPLETED_RECEIPTS_REQUIRE_REVIEW")
        return {"task_id": task_id, "action_id": action_id, "request_id": intent["request_id"],
                "writer_lease_generation": intent["writer_lease_generation"], "state": action["delivery_state"],
                "settled": action["delivery_state"] == "settled" and action["settled_at_ms"] is not None,
                "attempt_ids": [row["attempt_id"] for row in attempts], "receipt_states": [row["receipt_state"] for row in receipts],
                "receipt": completed[0] if completed else None}


def verified_payload(family, marker, pins):
    require(family["settled"] and family["state"] != "reconcile_required", "ACTION_NOT_SETTLED_NO_CLEANUP")
    if family["receipt"] is None:
        return None
    payload = json.loads(family["receipt"]["payload_json"])
    require(isinstance(payload, dict) and set(payload) == {"schema_version", "operation_kind", "patch_applied", "local_handle",
            "local_semantic_acceptance", "task_id", "writer_lease_generation", "run_id", "wave_id", "policy_sha256",
            "actor", "runtime_identity", "facade_contract", "file", "response_sha256", "initial_verification"}
            and payload.get("schema_version") == 1 and payload.get("operation_kind") == "control_plane_approved_patch"
            and payload.get("patch_applied") is True and payload.get("local_semantic_acceptance") == "pending"
            and payload.get("task_id") == family["task_id"]
            and payload.get("writer_lease_generation") == family["writer_lease_generation"]
            and payload.get("actor") == {"client_id": "electron-control-plane-approved-patch-bridge", "client_type": "electron"}
            and payload.get("facade_contract") == marker["facade_contract"], "COMPLETED_RECEIPT_INVALID")
    identity = {"activation_epoch_id": pins["activation_epoch"], "process_instance_id": pins["runtime_instance_id"],
                "server_instance_id": pins["mcp_server_instance_id"], "tool_contract_sha256": pins["native_tool_contract_sha256"]}
    require(payload.get("runtime_identity") == identity, "RECEIPT_NATIVE_INSTANCE_CHANGED")
    require(type(payload["schema_version"]) is int and type(payload["writer_lease_generation"]) is int
            and payload["writer_lease_generation"] >= 1 and type(payload.get("file", {}).get("bytes_written")) is int,
            "RECEIPT_INTEGER_FIELDS_INVALID")
    require(re.fullmatch(r"cp_ap_[a-f0-9]{48}", str(payload.get("local_handle")))
            and re.fullmatch(r"[a-f0-9]{64}", str(payload.get("policy_sha256"))), "RECEIPT_SEALED_IDENTITY_INVALID")
    file = {"path": TARGET, "preimage_sha256": PRE, "postimage_sha256": POST, "bytes_written": 414}
    require(payload.get("file") == file, "PATCH_EFFECT_MISMATCH")
    proof = payload.get("initial_verification")
    proof_fields = {"plan_sha256", "proof_status", "proof_ids", "proof_fingerprint"}
    require(isinstance(proof, dict) and set(proof) in (proof_fields, proof_fields | {"command_id", "job_id"})
            and proof["plan_sha256"] == PLAN_SHA and proof["proof_status"] in {"passed", "failed", "timed_out"}, "INITIAL_PROOF_RECEIPT_INVALID")
    require(isinstance(proof["proof_ids"], list) and len(set(proof["proof_ids"])) == len(proof["proof_ids"])
            and all(re.fullmatch(r"[a-f0-9]{32}", str(item)) for item in proof["proof_ids"]), "PROOF_IDS_INVALID")
    if "command_id" in proof:
        for key in ("command_id", "job_id"):
            require(isinstance(proof[key], str) and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", proof[key]), "COMMAND_OR_JOB_ID_INVALID")
    require(proof["proof_status"] != "passed" or "command_id" in proof, "PASSED_PROOF_MISSING_COMMAND_JOB")
    require((proof["proof_status"] == "passed" and proof["proof_ids"] and re.fullmatch(r"[a-f0-9]{64}", str(proof["proof_fingerprint"])))
            or (proof["proof_status"] != "passed" and proof["proof_fingerprint"] is None), "PROOF_FINGERPRINT_INVALID")
    require(all(re.fullmatch(r"[a-f0-9]{32}", str(payload.get(key))) for key in ("run_id", "wave_id"))
            and payload["run_id"] != OLD_RUN and payload["wave_id"] != OLD_WAVE, "RUN_WAVE_INVALID_OR_HISTORICAL")
    require(payload.get("response_sha256") == digest({"file": file, "initial_verification": proof}), "RESPONSE_DIGEST_MISMATCH")
    return {"file": file, "initial_verification": proof, "run_id": payload["run_id"], "wave_id": payload["wave_id"],
            "receipt_id": family["receipt"]["receipt_id"], "response_sha256": payload["response_sha256"],
            "native_proof_correlation": "root_local_read_only_verifier_required", "checker_4_of_4": "not_observed_here"}


def public_family(family):
    return {key: family.get(key) for key in ("task_id", "action_id", "request_id", "writer_lease_generation", "state", "settled", "attempt_ids", "receipt_states")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("stage", "preflight", "dispatch", "observe", "cleanup"))
    parser.add_argument("--workspace", default=r"E:\Github\Tools-Codex-web")
    args = parser.parse_args()
    if args.phase == "stage":
        return stage(args.workspace)
    common = load_common()
    pins = pins_input(common)
    common.private_directory(CANARY_OPERATION_DIR)
    marker_path = CANARY_OPERATION_DIR / "canary-dispatch.json"
    if args.phase in {"preflight", "dispatch"}:
        database, origin, auth, contract, observed = preflight(common, pins)
        if args.phase == "preflight":
            return {"phase": "preflight", "remote_mutation": False, "facade_contract": contract,
                    "preflight_sha256": digest(observed), "pins_sha256": digest(pins), "observed_at_ms": observed["observed_at_ms"]}
        marker = {"schema_version": 1, "provenance": "central_mcp_service_trial", "pins_sha256": digest(pins),
                  "expires_at_ms": pins["expires_at_ms"], "facade_contract": contract, "preflight_sha256": digest(observed),
                  "historical_action_families_sha256": observed["state"]["historical_action_families_sha256"],
                  "patch_acceptances_sha256": observed["state"]["patch_acceptances_sha256"],
                  "baseline_actions": observed["state"]["actions"], "baseline_tasks": observed["state"]["tasks"],
                  "task_key": "r13_5h-initial-task-" + digest(pins)[:32], "patch_key": "r13_5h-initial-patch-" + digest(pins)[:32],
                  "created_at_ms": int(time.time() * 1000), "patch_sha256": PATCH, "plan_sha256": PLAN_SHA}
        exclusive(marker_path, marker)  # Durable irreversible no-replay gate before task_open.
        task = call(origin, auth, "workspace_context", {"operation": "task_open", "binding_id": common.BINDING,
                    "label": "r13_5h exact patch initial verification", "idempotency_key": marker["task_key"]}).get("task", {})
        task_id = task.get("task_id")
        require(re.fullmatch(r"task_[a-f0-9]{32}", str(task_id)) and task.get("binding_id") == common.BINDING, "TASK_OPEN_RESPONSE_INVALID")
        exclusive(CANARY_OPERATION_DIR / "canary-task-open.json", {"task_id": task_id, "pins_sha256": digest(pins)})
        exclusive(CANARY_OPERATION_DIR / "canary-writer-claim-intent.json", {"task_id": task_id})
        lease = call(origin, auth, "task_control", {"operation": "writer_claim", "task_id": task_id})
        require(lease.get("task_id") == task_id and lease.get("execution") == "writer_lease_claimed", "WRITER_CLAIM_RESPONSE_INVALID")
        exclusive(CANARY_OPERATION_DIR / "canary-writer-claimed.json", {"task_id": task_id,
                    "lease_generation": lease.get("writer_lease", {}).get("lease_generation")})
        _, fresh_health, _, fresh_overview, fresh_grant = operator_observation(common, pins, initial=False)
        authority_guard(common, pins, fresh_health, fresh_overview, fresh_grant, dispatch=True)
        exclusive(CANARY_OPERATION_DIR / "canary-patch-dispatch-intent.json", {"task_id": task_id, "patch_key": marker["patch_key"]})
        result = call(origin, auth, "agent_workflow", {"operation": "apply_patch", "binding_id": common.BINDING,
                    "task_id": task_id, "path": TARGET, "preimage_sha256": PRE, "patch_sha256": PATCH,
                    "validation_profile": "targeted", "patch_envelope": packet()[0], "verification": PLAN,
                    "idempotency_key": marker["patch_key"], "expected_facade_contract": contract})
        require(result.get("replayed") is False and result.get("facade_contract") == contract
                and re.fullmatch(r"act_[a-f0-9]{32}", str(result.get("action_id"))), "PATCH_DISPATCH_RESPONSE_INVALID")
        exclusive(CANARY_OPERATION_DIR / "canary-dispatch-response.json", {"task_id": task_id, "action_id": result["action_id"],
                    "request_id": result.get("request_id"), "intent_digest": result.get("intent_digest")})
        return {"phase": "dispatch", "task_id": task_id, "action_id": result["action_id"], "remote_mutation": True,
                "next_action": "observe_same_action_only", "replay_forbidden": True}
    marker = private_json(marker_path)
    require(marker.get("pins_sha256") == digest(pins), "TRIAL_PINS_CHANGED_NO_REPLAY")
    database, _, _, _, _ = operator_observation(common, pins, initial=False)
    family = ids(common, database, marker)
    origin, auth = mcp_credentials(common)
    if family.get("action_id"):
        status = call(origin, auth, "agent_workflow", {"operation": "patch_status", "action_id": family["action_id"]})
        require(status.get("action", {}).get("action_id") == family["action_id"], "PATCH_STATUS_ACTION_CHANGED")
        require(status.get("reconciliation_required") is not True and family["state"] != "reconcile_required",
                "PATCH_EFFECT_UNKNOWN_RECONCILE_REQUIRED_NO_REPLAY")
    verified = verified_payload(family, marker, pins) if family.get("settled") else None
    if args.phase == "cleanup":
        require(family.get("settled") is True, "ACTION_NOT_SETTLED_NO_CLEANUP")
        exclusive(CANARY_OPERATION_DIR / "canary-cleanup-intent.json", {"task_id": family["task_id"], "action_id": family["action_id"]})
        release = call(origin, auth, "task_control", {"operation": "writer_release", "task_id": family["task_id"], "reason": "r13_5h canary settled; native semantic acceptance remains pending"})
        require(release.get("execution") == "writer_lease_released", "WRITER_RELEASE_RESPONSE_INVALID")
        exclusive(CANARY_OPERATION_DIR / "canary-writer-released.json", {"task_id": family["task_id"]})
        closed = call(origin, auth, "workspace_context", {"operation": "task_close", "task_id": family["task_id"]}).get("task", {})
        require(closed.get("task_id") == family["task_id"] and closed.get("closed_at_ms") is not None, "TASK_CLOSE_RESPONSE_INVALID")
        exclusive(CANARY_OPERATION_DIR / "canary-task-closed.json", {"task_id": family["task_id"], "closed_at_ms": closed["closed_at_ms"]})
        with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True, timeout=5) as connection:
            connection.execute("PRAGMA query_only=ON")
            require(connection.execute("SELECT closed_at_ms FROM mcp_task_sessions WHERE task_id=?", (family["task_id"],)).fetchone()[0] is not None
                    and connection.execute("SELECT COUNT(*) FROM mcp_task_writer_leases WHERE task_id=? AND released_at_ms IS NULL", (family["task_id"],)).fetchone()[0] == 0,
                    "CLEANUP_STATE_NOT_TERMINAL")
    return {"phase": args.phase, "provenance": "central_mcp_service_trial", "family": public_family(family),
            "verified_patch_and_initial_proof_summary": verified, "native_semantic_acceptance": "pending",
            "acceptance_blocker": "NATIVE_CHATWEB_ACCEPTANCE_TRANSPORT_UNAVAILABLE", "replay_forbidden": True,
            "remote_mutation": args.phase == "cleanup"}


def run_guarded():
    try:
        return main()
    finally:
        if _prior_marker_path is not None:
            require(sha(_prior_marker_path.read_bytes()) == _prior_marker_sha256, "PREVIOUS_AUTHORITY_MARKER_CHANGED_DURING_TRIAL")


if __name__ == "__main__":
    try:
        result = run_guarded()
        print(json.dumps({"ok": True, **result}, ensure_ascii=False, sort_keys=True))
    except Exception as error:
        print(json.dumps({"ok": False, "phase": "r13_5h_canary_failed", "code": getattr(error, "code", "LOCAL_CANARY_GUARD_FAILED"),
                          "replay_forbidden": True}, sort_keys=True))
        raise SystemExit(1)
