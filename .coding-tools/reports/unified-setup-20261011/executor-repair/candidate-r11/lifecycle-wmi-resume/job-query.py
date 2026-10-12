"""Query one existing process Job membership, with no process mutation."""
import ctypes
from ctypes import wintypes
import json
import sys
sys.dont_write_bytecode = True
try:
    pid = int(sys.argv[1])
    if pid <= 0:
        raise ValueError()
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.IsProcessInJob.argtypes = [wintypes.HANDLE, wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL)]
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle:
        raise ValueError()
    try:
        associated = wintypes.BOOL()
        if not kernel.IsProcessInJob(handle, None, ctypes.byref(associated)):
            raise ValueError()
        print(json.dumps({"ok": True, "pid": pid, "associated": bool(associated.value), "mutated": False}))
    finally:
        kernel.CloseHandle(handle)
except (OSError, ValueError, IndexError):
    print(json.dumps({"ok": False, "code": "EXACT_PROCESS_JOB_QUERY_UNAVAILABLE", "mutated": False}))
    raise SystemExit(2) from None
