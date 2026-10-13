"""Offline fixtures only: no native handle, network, VM, or stop effects."""
import ast
import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "owned-sandbox-stop-proof.py"
spec = importlib.util.spec_from_file_location("owned_stop_fixture_subject", SOURCE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
ast.parse(SOURCE.read_text(encoding="utf-8"))
passed = []

inventory = [{"Name": "WindowsSandboxRemoteSession.exe", "ProcessId": 3492},
             {"Name": "WindowsSandboxServer.exe", "ProcessId": 42712},
             {"Name": "vmmemWindowsSandbox", "ProcessId": 28056}]
created = {3492: "134362581522952353", 42712: "134362581528050454"}
handle_pids = []
def identity(pid):
    handle_pids.append(pid)
    assert pid != 28056, "Opaque kernel aggregate must never be opened"
    return {"pid": pid, "creation_time": created[pid], "executable_path": "C:/Windows/System32/" + str(pid)}
completed = SimpleNamespace(returncode=0, stdout=json.dumps(inventory))
with patch.object(m.subprocess, "run", return_value=completed), patch.object(m, "process_identity", side_effect=identity):
    hosts = m.host_processes()
    assert handle_pids == [3492, 42712]
    assert hosts["kernel_memory_observations"] == [{"name": "vmmemWindowsSandbox", "pid": 28056, "ownership_inferred": False}]
    assert {(x["pid"], x["creation_time"]) for x in hosts["user_mode_hosts"]} == set(created.items())
    passed.append("Exact user-mode identities opened; opaque vmmem observed without handle or ownership")
handle_pids.clear()
with patch.object(m.subprocess, "run", return_value=completed), patch.object(m, "process_identity", side_effect=identity):
    observed = m.host_processes(prove_user_mode_identity=False)
    assert handle_pids == []
    assert observed["user_mode_hosts"] == [{"name": x["Name"], "pid": x["ProcessId"]} for x in inventory[:2]]
    passed.append("Post-stop inventory opens zero handles, including exiting user-mode hosts")
with patch.object(m.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout="")):
    assert m.host_processes(prove_user_mode_identity=False) == {"user_mode_hosts": [], "kernel_memory_observations": []}
    passed.append("Empty complete inventory confirms both host and kernel absence")

sid = "wsb:1234abcd"
package = {"backend": str(m.ROOT / "dist/fixture"), "daemon_sha256": "a" * 64}
daemon_exe = str(Path(package["backend"]) / "wxc-windows-sandbox-daemon.exe")
daemon = {"active_sandbox_id": sid, "ready": True, "protocol_version": 1, "nonce": "b" * 32,
          "pid": 41824, "pid_creation_time": "134362581520920385", "ipc_port": 49152,
          "vm_processes": [{"pid": pid, "creation_time": token} for pid, token in created.items()]}
record = {"sandbox_id": sid, "state": "started", "mapped_folders": [{"host": str(m.ROOT), "sandbox": "C:/repo", "read_only": False}]}
args = SimpleNamespace(sandbox_id=sid)
class Socket:
    def __enter__(self): return self
    def __exit__(self, *unused): pass
    def settimeout(self, unused): pass
    def sendall(self, data): assert data == ("PING " + daemon["nonce"] + "\n").encode("ascii")
    def recv(self, unused): return b"PONG\n"
def owned_case(label, mutate=None, expected=None):
    d, r, h = copy.deepcopy(daemon), copy.deepcopy(record), copy.deepcopy(hosts)
    if mutate: mutate(d, r, h)
    def fixture_json(path): return copy.deepcopy(d if path.name == "daemon.json" else r)
    def fixture_process(pid):
        assert pid == 41824
        return {"pid": pid, "creation_time": "134362581520920385", "executable_path": daemon_exe}
    with patch.object(m, "read_json", side_effect=fixture_json), patch.object(m, "process_identity", side_effect=fixture_process), patch.object(m, "host_processes", return_value=h), patch.object(m, "file_sha", return_value="a" * 64), patch.object(m.socket, "create_connection", return_value=Socket()):
        try:
            unused, proof = m.owned_backend(args, package)
        except RuntimeError as error:
            assert expected == str(error), (label, expected, str(error))
        else:
            assert expected is None, label
            assert proof["nonce_saved"] is False and "nonce" not in proof
            assert proof["host_processes"]["kernel_memory_observations"][0]["ownership_inferred"] is False
    passed.append(label)
owned_case("Owned exact user-mode set plus opaque kernel observation accepted")
owned_case("Foreign user-mode PID rejected", lambda d,r,h: h["user_mode_hosts"].append({"pid": 999, "creation_time": "1"}), "FOREIGN_OR_UNPROVEN_VM_PROCESS_PRESENT")
owned_case("Reused user-mode PID with changed exact FILETIME rejected", lambda d,r,h: h["user_mode_hosts"][0].update(creation_time="134362581522952354"), "FOREIGN_OR_UNPROVEN_VM_PROCESS_PRESENT")
owned_case("Kernel presence cannot substitute for owned user-mode set", lambda d,r,h: h["user_mode_hosts"].clear(), "FOREIGN_OR_UNPROVEN_VM_PROCESS_PRESENT")
owned_case("Different daemon exact FILETIME rejected", lambda d,r,h: d.update(pid_creation_time="134362581520920386"), "LIVE_DAEMON_NOT_EXACT_R6_PACKAGE")
owned_case("Foreign writable workspace rejected", lambda d,r,h: r["mapped_folders"][0].update(host="E:/foreign-workspace"), "EXACT_WORKSPACE_MAPPING_REQUIRED")

# Validate the executed shutdown-loop condition from the parsed source with four
# inventories. This evaluates the actual condition and performs no lifecycle call.
tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
main = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == "main")
shutdown_loop = next(x for x in main.body if isinstance(x, ast.While))
condition = next(x.test for x in shutdown_loop.body if isinstance(x, ast.If))
compiled = compile(ast.Expression(condition), str(SOURCE), "eval")
for users, kernel in (([], []), ([{"pid": 1}], []), ([], [{"pid": 2}]), ([{"pid": 1}], [{"pid": 2}])):
    result = eval(compiled, {"after_hosts": {"user_mode_hosts": users, "kernel_memory_observations": kernel}})
    assert result is (not users and not kernel)
passed.append("Actual shutdown-loop success condition requires both inventories empty in all four cases")
receipt = {"schema_version": 1, "operation": "owned_stop_kernel_observation_offline_validation",
           "producer_sha256": m.file_sha(SOURCE), "ast_parse": "PASS", "cases_passed": len(passed),
           "cases": passed, "stop_effect_performed": False, "native_handles_opened": False,
           "network_requests_performed": False, "processes_terminated": False}
saved = m.write_new(HERE / "owned-stop-kernel-observation-validation.json", receipt)
print(json.dumps({"ok": True, "cases_passed": len(passed), "producer_sha256": receipt["producer_sha256"], **saved}))
