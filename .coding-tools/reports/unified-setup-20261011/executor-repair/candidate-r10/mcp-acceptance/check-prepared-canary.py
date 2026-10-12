"""Syntax and pure pin/key/TAP checks; no helper main or live operation."""
import ast
import base64
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
path = HERE / "r10-mcp-canary.py"
source = path.read_text(encoding="utf-8")
tree = ast.parse(source)
compile(tree, str(path), "exec")
values = {node.targets[0].id: ast.literal_eval(node.value) for node in tree.body
          if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
          and node.targets[0].id in {"GUARD_SHA256", "GUARD_SOURCE_BASE64"}}
guard = base64.b64decode(values["GUARD_SOURCE_BASE64"])
assert hashlib.sha256(guard).hexdigest() == values["GUARD_SHA256"]
compile(guard, "embedded-authority-guard", "exec")
assert "exec_stop" not in source and 'choices=("cold", "warm")' in source
assert 'mcp_task_open_idempotency WHERE principal_id=? AND idempotency_key=?' in source
assert 'time.monotonic() + 540' in source and '300000' in source
names = {"mode_keys", "check_pins", "tap_proof"}
functions = ast.Module(body=[node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names], type_ignores=[])


def require(condition, code):
    if not condition:
        raise ValueError(code)


ns = {"re": re, "require": require, "digest": lambda value: hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest(),
      "EPOCH": "activation-r10-test-epoch", "CONTEXT": "ctx_" + "a" * 32, "PILOT": "pilot_" + "b" * 32}
exec(compile(functions, "pure-checks", "exec"), ns)
pins = {"service_instance_id": "cp_" + "a" * 32, "context_id": "ctx_" + "b" * 32, "pilot_id": "pilot_" + "c" * 32,
        "activation_epoch_id": "activation-r10-test-epoch", "process_instance_id": "r10-process", "server_instance_id": "r10-server",
        "native_contract_sha256": "d" * 64, "rollout_receipt_sha256": "e" * 64, "native_observation_sha256": "f" * 64,
        "requested_at_ms": 1000000, "expires_at_ms": 4600000,
        "facade_contract": {"schema_version": 32, "profile": "control-plane-test-v1", "sha256": "a" * 64}}
ns["check_pins"](pins)
cases = 1
for changed in ({**pins, "expires_at_ms": 4600001}, {**pins, "activation_epoch_id": "activation-mv3qe36p-991f11f44f47d32ea2e217b1db882ff7"},
                {**pins, "extra": True}, {**pins, "native_contract_sha256": "invalid"}):
    try:
        ns["check_pins"](changed)
    except ValueError:
        cases += 1
    else:
        raise AssertionError("negative pin accepted")
tap = "TAP version 13\n1..4\n# tests 4\n# suites 0\n# pass 4\n# fail 0\n# cancelled 0\n# skipped 0\n# todo 0\n"
assert ns["tap_proof"](tap)["tap"]["pass"] == 4
cases += 1
for invalid in (tap.replace("# pass 4", "# pass 3"), tap.replace("# fail 0", "# fail 1"), tap + "# tests 4\n"):
    try:
        ns["tap_proof"](invalid)
    except ValueError:
        cases += 1
    else:
        raise AssertionError("negative TAP accepted")
assert ns["mode_keys"]("cold") == ns["mode_keys"]("cold") and ns["mode_keys"]("cold") != ns["mode_keys"]("warm")
cases += 1
observer = HERE / "verify-r10-native-job.py"
compile(observer.read_text(), str(observer), "exec")
report = {"phase": "r10_canary_preparation_proof", "ok": True, "pure_function_cases": cases, "python_syntax": True,
          "embedded_guard_sha256": values["GUARD_SHA256"], "helper_main_invoked": False, "live_operations": False,
          "helper_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "native_correlator_sha256": hashlib.sha256(observer.read_bytes()).hexdigest()}
print(json.dumps(report, separators=(",", ":")))
