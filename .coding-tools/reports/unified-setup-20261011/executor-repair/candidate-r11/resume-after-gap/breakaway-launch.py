"""Exact r11 one-shot launch. Root invokes it only through resume.cjs guards."""
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(r"E:\Github\Tools-Codex-web")
PACKAGE = ROOT / "dist/windows-candidate-mxc-wsb-cbe1774-initial-proof-1011-r11/win-unpacked"
EXE = PACKAGE / "Coding Tools MCP.exe"
PROFILE = Path(r"C:\Users\daoth\AppData\Roaming\web-mcp-assistant")


class Basic(ctypes.Structure):
    _fields_ = [("process_time", ctypes.c_longlong), ("job_time", ctypes.c_longlong),
                ("flags", wintypes.DWORD), ("min_working", ctypes.c_size_t), ("max_working", ctypes.c_size_t),
                ("active_limit", wintypes.DWORD), ("affinity", ctypes.c_size_t),
                ("priority", wintypes.DWORD), ("scheduling", wintypes.DWORD)]


class Extended(ctypes.Structure):
    _fields_ = [("basic", Basic), ("io", ctypes.c_ulonglong * 6),
                ("process_memory", ctypes.c_size_t), ("job_memory", ctypes.c_size_t),
                ("peak_process", ctypes.c_size_t), ("peak_job", ctypes.c_size_t)]


def job(process=None):
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.IsProcessInJob.argtypes = [wintypes.HANDLE, wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL)]
    kernel.QueryInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p]
    handle = process if process is not None else kernel.GetCurrentProcess()
    associated = wintypes.BOOL()
    if not kernel.IsProcessInJob(handle, None, ctypes.byref(associated)):
        raise OSError(ctypes.get_last_error(), "JOB_QUERY_FAILED")
    flags = 0
    if associated.value and process is None:
        limits = Extended()
        if not kernel.QueryInformationJobObject(None, 9, ctypes.byref(limits), ctypes.sizeof(limits), None):
            raise OSError(ctypes.get_last_error(), "JOB_LIMIT_QUERY_FAILED")
        flags = limits.basic.flags
    return {"associated": bool(associated.value), "limit_flags": flags,
            "breakaway_allowed": not associated.value or bool(flags & (0x800 | 0x1000))}


def main():
    request = json.loads(sys.stdin.buffer.read(32769))
    mode = request.get("mode")
    parent = job()
    if mode == "observe":
        print(json.dumps({"ok": True, "parent_job": parent, "mutated": False}))
        return
    if mode not in ("runtime", "agent") or request.get("operator_approved") is not True or not parent["breakaway_allowed"]:
        raise ValueError("EXACT_APPROVED_BREAKAWAY_REQUIRED")
    env = dict(os.environ)
    for name in list(env):
        if re.search(r"(?:AUTHORIZATION|ACCESS_TOKEN|BEARER_TOKEN|PASSWORD|PASSWD|COOKIE|PRIVATE_KEY|SECRET_KEY|API_KEY|AUTH_TOKEN|MCP_AUTH_TOKEN|P5_A0_SEED)", name, re.I):
            env.pop(name, None)
    for name in ("ELECTRON_RUN_AS_NODE", "NODE_OPTIONS", "NODE_EXTRA_CA_CERTS", "FULL_CLEAN_DEFERRED_WORKER", "FULL_CLEAN_SOURCE_CHECKPOINT_JSON", "CODING_TOOLS_MCP_ACTIVATION_EPOCH_ID", "WEBCODEX_PROCESS_ROLE"):
        env.pop(name, None)
    if mode == "runtime":
        argv, cwd = [str(EXE), "--recovery-host"], str(PACKAGE)
        stdout = stderr = subprocess.DEVNULL
    else:
        count = request.get("max_iterations")
        if type(count) is not int or not 1 <= count <= 240:
            raise ValueError("BOUNDED_AGENT_ITERATIONS_REQUIRED")
        python = str(PACKAGE / "resources/resources/native-python/python.exe")
        project = str(PACKAGE)
        argv = [python, "-B", "-I", "-u", str(PACKAGE / "resources/resources/control-plane/node_agent.py"), "run-connected-agent",
                "--config", str(PROFILE / "control-plane-node.json"), "--workspace-registry", str(PROFILE / "control-plane-workspaces.json"),
                "--project-root", project, "--node", str(EXE), "--runtime-mode", "packaged",
                "--interval-seconds", "15", "--max-backoff-seconds", "60", "--max-iterations", str(count)]
        cwd = project
        stdout = open(Path(__file__).parent / "agent.stdout.jsonl", "ab", buffering=0)
        stderr = subprocess.DEVNULL
    startup = subprocess.STARTUPINFO()
    startup.dwFlags = subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = 0
    flags = subprocess.CREATE_BREAKAWAY_FROM_JOB | subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    try:
        child = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                 close_fds=True, creationflags=flags, startupinfo=startup)
        child_job = job(wintypes.HANDLE(int(child._handle)))
        if child_job["associated"]:
            # Do not kill or repeat an ambiguously launched process.
            print(json.dumps({"ok": False, "code": "CHILD_JOB_ASSOCIATED_RECONCILE_EXACT_PID", "pid": child.pid, "mutated": True}))
            raise SystemExit(2)
        print(json.dumps({"ok": True, "pid": child.pid, "parent_job": parent, "child_job": child_job,
                          "creation_flags": flags, "mode": mode, "mutated": True}))
    finally:
        if mode == "agent":
            stdout.close()


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as error:
        print(json.dumps({"ok": False, "code": "WINDOWS_ACCESS_DENIED" if getattr(error, "winerror", None) == 5 else "BREAKAWAY_LAUNCH_REFUSED",
                          "winerror": getattr(error, "winerror", None), "no_automatic_retry": True}))
        raise SystemExit(2) from None
