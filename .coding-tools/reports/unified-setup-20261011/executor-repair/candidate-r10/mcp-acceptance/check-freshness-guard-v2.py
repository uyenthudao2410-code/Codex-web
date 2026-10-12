"""Focused actual authority-guard regression; synthetic read-only inputs only."""
import ast
import base64
import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
NOW = 1791723000000
EXPIRY = NOW + 3600000


class Refused(Exception):
    pass


def require(condition, code):
    if not condition:
        raise Refused(code)


def guard_function(path):
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    compile(tree, str(path), "exec")
    values = {node.targets[0].id: ast.literal_eval(node.value) for node in tree.body
              if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
              and node.targets[0].id in {"GUARD_SOURCE_BASE64", "GUARD_SHA256"}}
    embedded = base64.b64decode(values["GUARD_SOURCE_BASE64"])
    assert hashlib.sha256(embedded).hexdigest() == values["GUARD_SHA256"]
    compile(embedded, "embedded-reviewed-guard", "exec")
    node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "authority_guard")
    namespace = {"require": require, "time": SimpleNamespace(time=lambda: NOW / 1000), "EXPIRY": EXPIRY,
                 "CONTEXT": "ctx-reviewed", "PILOT": "pilot-reviewed", "EPOCH": "activation-r10-reviewed",
                 "NATIVE_PROCESS": "process-r10-reviewed", "NATIVE_SERVER": "server-r10-reviewed",
                 "_guard": {"BINDING": "binding-reviewed", "PRINCIPAL": "principal-reviewed", "DEVICE": "device-reviewed"}}
    exec(compile(ast.Module(body=[node], type_ignores=[]), "actual-authority-guard", "exec"), namespace)
    return namespace["authority_guard"]


def fixture():
    return {"admission": {"admission_mode": "scoped_pilot"},
            "contexts": [{"context_id": "ctx-reviewed", "binding_id": "binding-reviewed", "expires_at_ms": EXPIRY, "closed_at_ms": None}],
            "scoped_pilot_decisions": [{"decision_id": "pilot-reviewed", "binding_id": "binding-reviewed", "principal_id": "principal-reviewed",
                                        "expires_at_ms": EXPIRY, "revoked_at_ms": None}],
            "nodes": [{"device_id": "device-reviewed", "activation_epoch": "activation-r10-reviewed", "readiness": "ready", "policy_state": "enabled",
                       "last_seen_at_ms": NOW - 10000, "policy_expires_at_ms": NOW + 50000,
                       "runtime_instance_id": "process-r10-reviewed", "mcp_server_instance_id": "server-r10-reviewed"}]}


guard = guard_function(HERE / "r10-mcp-canary-v2.py")
old_guard = guard_function(HERE / "r10-mcp-canary.py")
grant = {"expires_at_ms": EXPIRY + 1000}
passed = []
guard(fixture(), grant)
passed.append("distinct_fresh_observation_horizon_accepted")
try:
    old_guard(fixture(), grant)
except Refused:
    passed.append("original_equality_regression_reproduced")
else:
    raise AssertionError("old equality regression not reproduced")

for label, field, value in (
    ("expired_policy", "policy_expires_at_ms", NOW - 1),
    ("policy_at_now", "policy_expires_at_ms", NOW),
    ("disabled_policy", "policy_state", "expired_or_disabled"),
    ("unobserved_policy", "policy_state", "unobserved"),
    ("malformed_policy_horizon", "policy_expires_at_ms", "later"),
    ("boolean_policy_horizon", "policy_expires_at_ms", True),
    ("stale_heartbeat", "last_seen_at_ms", NOW - 60000),
    ("future_heartbeat", "last_seen_at_ms", NOW + 1),
    ("wrong_epoch", "activation_epoch", "activation-r9"),
    ("wrong_native_process", "runtime_instance_id", "another-process"),
    ("unready_node", "readiness", "blocked"),
):
    overview = fixture()
    overview["nodes"][0][field] = value
    try:
        guard(overview, grant)
    except Refused as error:
        assert str(error) == "R10_FRESH_READY_NODE_UNPROVEN"
        passed.append(label + "_rejected")
    else:
        raise AssertionError(label + " was accepted")

for table, code in (("contexts", "APPROVED_STANDING_CONTEXT_CHANGED"), ("scoped_pilot_decisions", "APPROVED_PILOT_CHANGED")):
    overview = fixture()
    overview[table][0]["expires_at_ms"] = EXPIRY + 1
    try:
        guard(overview, grant)
    except Refused as error:
        assert str(error) == code
        passed.append(table + "_exact_approved_expiry_preserved")
    else:
        raise AssertionError("approved authority expiry weakened")

report = {"phase": "r10_v2_standing_freshness_guard_proof", "ok": True, "focused_actual_guard_cases": len(passed), "cases": passed,
          "python_syntax": True, "helper_main_invoked": False, "embedded_guard_inspect_invoked": False, "live_operations": False,
          "policy_observation_horizon_ms": 60000, "approved_window_ms": 3600000,
          "helper_sha256": hashlib.sha256((HERE / "r10-mcp-canary-v2.py").read_bytes()).hexdigest(),
          "original_helper_sha256": hashlib.sha256((HERE / "r10-mcp-canary.py").read_bytes()).hexdigest()}
print(json.dumps(report, separators=(",", ":")))
