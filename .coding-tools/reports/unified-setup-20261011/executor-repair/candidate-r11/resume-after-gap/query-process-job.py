"""Bounded content-free process Job association query; no process effects."""
import ctypes
from ctypes import wintypes
import json
import sys
pid = json.loads(sys.stdin.buffer.read(1025)).get("pid")
if type(pid) is not int or not 0 < pid < 2 ** 32:
    raise SystemExit(2)
k = ctypes.WinDLL("kernel32", use_last_error=True)
k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
k.OpenProcess.restype = wintypes.HANDLE
k.IsProcessInJob.argtypes = [wintypes.HANDLE, wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL)]
k.CloseHandle.argtypes = [wintypes.HANDLE]
h = k.OpenProcess(0x1000, False, pid)
associated = wintypes.BOOL()
ok = bool(h) and bool(k.IsProcessInJob(h, None, ctypes.byref(associated)))
print(json.dumps({"pid": pid, "query_success": ok, "job_associated": bool(associated.value) if ok else None,
                  "queried_job_identity": False, "mutated": False}))
if h:
    k.CloseHandle(h)
if not ok:
    raise SystemExit(2)
