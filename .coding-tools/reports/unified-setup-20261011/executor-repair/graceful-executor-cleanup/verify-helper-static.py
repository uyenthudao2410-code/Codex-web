"""Static and pure-function proof only; never invokes a live helper main."""
import ast
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import zlib

HERE = Path(__file__).resolve().parent
canary_path = HERE / "r9-timeout-canary.py"
observer_path = HERE / "r9-timeout-native-observer.py"
census_path = HERE / "observe-r9-current.cjs"
canary = canary_path.read_text(encoding="utf-8")
tree = ast.parse(canary)
compile(tree, str(canary_path), "exec")
values = {node.targets[0].id: ast.literal_eval(node.value) for node in tree.body
          if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
          and node.targets[0].id in {"GUARD_SOURCE_BASE64", "GUARD_SHA256"}}
guard = base64.b64decode(values["GUARD_SOURCE_BASE64"])
assert hashlib.sha256(guard).hexdigest() == values["GUARD_SHA256"]
compile(guard, "embedded-authority-guard", "exec")
assert 'deadline = time.monotonic() + 240' in canary
assert 'mcp_task_open_idempotency WHERE principal_id=? AND idempotency_key=?' in canary
assert 'run_nonce=arguments.run_nonce' not in canary
assert 'code=error.code' in canary
spec = importlib.util.spec_from_file_location("reviewed_observer", observer_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
assert hashlib.sha256(census_path.read_bytes()).hexdigest() == module.CENSUS_SHA256
passed = 0


def refusal(callback):
    global passed
    try:
        callback()
    except module.Refusal:
        passed += 1
    else:
        raise AssertionError("expected refusal")


value = {"tool_result": {"structuredContent": {"command_id": "command", "status": "timeout", "timed_out": True}}}
assert module.decode_summary({"summary_codec": "plain_json", "summary_json": json.dumps(value)}) == value
passed += 1
assert module.decode_summary({"summary_codec": "zlib_json", "summary_blob": zlib.compress(json.dumps(value).encode())}) == value
passed += 1
refusal(lambda: module.decode_summary({"summary_codec": "unsupported", "summary_json": "{}"}))
module.identity({"activation_epoch_id": module.EPOCH, "process_instance_id": module.PROCESS, "server_instance_id": module.SERVER})
passed += 1
refusal(lambda: module.identity({"activation_epoch_id": "other", "process_instance_id": module.PROCESS, "server_instance_id": module.SERVER}))
refusal(lambda: module.identity({"activation_epoch_id": module.EPOCH, "process_instance_id": "other", "server_instance_id": module.SERVER}))
request = {"action_id": "action", "attempt_id": "attempt", "writer_lease_generation": 1, "operation": "exec_run",
           "argv": module.ARGV, "timeout_ms": 5000, "max_output_bytes": 32768, "facade_contract": {"sha256": "contract"},
           "yield_time_ms": 5000, "wait_ms": None, "task_id": "task", "command_id": None, "job_id": None,
           "local_handle": None, "consumer_id": None, "signal": None, "run_id": None, "wave_id": None, "cwd": ""}
assert module.native_key(request) == module.native_key(dict(reversed(list(request.items()))))
passed += 1
assert module.native_key(request) != module.native_key({**request, "attempt_id": "another"})
passed += 1
assert module.native_key(request) != module.native_key({**request, "timeout_ms": 6000})
passed += 1
node = Path(r"C:\Program Files\nodejs\node.exe")
assert subprocess.run([str(node), "--check", str(census_path)], capture_output=True, check=False).returncode == 0
report = {"phase": "timeout_helper_static_proof", "ok": True, "pure_function_cases": passed,
          "python_syntax": True, "node_syntax": True, "embedded_guard_sha256": values["GUARD_SHA256"],
          "canary_main_invoked": False, "observer_main_invoked": False, "live_operations": False,
          "files": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in (canary_path, observer_path, census_path)}}
print(json.dumps(report, separators=(",", ":")))
