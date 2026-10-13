"""Observe only non-identifying token security facts with the Windows API."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

REPOSITORY = Path(__file__).resolve().parents[3]
SOURCE = REPOSITORY / "resources" / "coding-tools-mcp"
sys.path.insert(0, str(SOURCE))
from coding_tools_mcp.server import Runtime

TOKEN_SCRIPT = r'''
import ctypes as c
from ctypes import wintypes as w
import json
k=c.WinDLL('kernel32',use_last_error=True)
a=c.WinDLL('advapi32',use_last_error=True)
k.GetCurrentProcess.restype=w.HANDLE
k.CloseHandle.argtypes=[w.HANDLE]
a.OpenProcessToken.argtypes=[w.HANDLE,w.DWORD,c.POINTER(w.HANDLE)]
a.OpenProcessToken.restype=w.BOOL
a.GetTokenInformation.argtypes=[w.HANDLE,c.c_int,c.c_void_p,w.DWORD,c.POINTER(w.DWORD)]
a.GetTokenInformation.restype=w.BOOL
a.GetSidSubAuthorityCount.argtypes=[c.c_void_p]
a.GetSidSubAuthorityCount.restype=c.POINTER(c.c_ubyte)
a.GetSidSubAuthority.argtypes=[c.c_void_p,w.DWORD]
a.GetSidSubAuthority.restype=c.POINTER(w.DWORD)
a.CreateWellKnownSid.argtypes=[c.c_int,c.c_void_p,c.c_void_p,c.POINTER(w.DWORD)]
a.CreateWellKnownSid.restype=w.BOOL
a.EqualSid.argtypes=[c.c_void_p,c.c_void_p]
a.EqualSid.restype=w.BOOL
a.LookupPrivilegeNameW.argtypes=[w.LPCWSTR,c.c_void_p,w.LPWSTR,c.POINTER(w.DWORD)]
a.LookupPrivilegeNameW.restype=w.BOOL
class SidAttrs(c.Structure):
    _fields_=[('Sid',c.c_void_p),('Attributes',w.DWORD)]
class TokenGroups(c.Structure):
    _fields_=[('Count',w.DWORD),('Groups',SidAttrs*1)]
class Luid(c.Structure):
    _fields_=[('LowPart',w.DWORD),('HighPart',w.LONG)]
class LuidAttrs(c.Structure):
    _fields_=[('Luid',Luid),('Attributes',w.DWORD)]
class TokenPrivileges(c.Structure):
    _fields_=[('Count',w.DWORD),('Privileges',LuidAttrs*1)]
t=w.HANDLE()
out={'token_query_opened':False,'errors':{}}
def query(info):
    needed=w.DWORD()
    a.GetTokenInformation(t,info,None,0,c.byref(needed))
    if needed.value==0:
        out['errors'][str(info)]=c.get_last_error()
        return None
    b=c.create_string_buffer(needed.value)
    if not a.GetTokenInformation(t,info,b,needed,c.byref(needed)):
        out['errors'][str(info)]=c.get_last_error()
        return None
    return b
if not a.OpenProcessToken(k.GetCurrentProcess(),0x8,c.byref(t)):
    out['errors']['open']=c.get_last_error()
else:
    out['token_query_opened']=True
    try:
        for field,info in [('elevated',20),('app_container',29)]:
            b=query(info)
            out[field]=bool(c.cast(b,c.POINTER(w.DWORD))[0]) if b else None
        b=query(25)
        if b:
            sa=c.cast(b,c.POINTER(SidAttrs)).contents
            count=a.GetSidSubAuthorityCount(sa.Sid)[0]
            rid=a.GetSidSubAuthority(sa.Sid,count-1)[0]
            out['integrity_rid']=rid
            out['high_or_system_integrity']=rid>=12288
        b=query(2)
        if b:
            count=c.cast(b,c.POINTER(w.DWORD))[0]
            groups=c.cast(c.addressof(b)+TokenGroups.Groups.offset,c.POINTER(SidAttrs))
            admin=c.create_string_buffer(68)
            size=w.DWORD(68)
            if a.CreateWellKnownSid(26,None,admin,c.byref(size)):
                matches=[groups[i].Attributes for i in range(count) if a.EqualSid(groups[i].Sid,admin)]
                out['administrator_group_present']=bool(matches)
                out['administrator_group_enabled']=any(bool(x&4) and not bool(x&16) for x in matches)
                out['administrator_group_deny_only']=any(bool(x&16) for x in matches)
            else:
                out['errors']['admin_sid']=c.get_last_error()
        b=query(3)
        if b:
            count=c.cast(b,c.POINTER(w.DWORD))[0]
            privs=c.cast(c.addressof(b)+TokenPrivileges.Privileges.offset,c.POINTER(LuidAttrs))
            names={'SeDebugPrivilege','SeImpersonatePrivilege','SeAssignPrimaryTokenPrivilege','SeTcbPrivilege','SeBackupPrivilege','SeRestorePrivilege','SeTakeOwnershipPrivilege','SeLoadDriverPrivilege','SeCreateTokenPrivilege','SeSecurityPrivilege','SeSystemEnvironmentPrivilege'}
            out['sensitive_privileges']=[]
            for i in range(count):
                name=c.create_unicode_buffer(128)
                size=w.DWORD(128)
                if a.LookupPrivilegeNameW(None,c.byref(privs[i].Luid),name,c.byref(size)) and name.value in names:
                    out['sensitive_privileges'].append({'name':name.value,'enabled':bool(privs[i].Attributes&2)})
    finally:
        k.CloseHandle(t)
print(json.dumps(out))
'''


def capture():
    started = datetime.now(timezone.utc).isoformat()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPOSITORY, text=True).strip()
    host = subprocess.run([r"C:\Program Files\Python311\python.exe", "-c", TOKEN_SCRIPT], check=True, capture_output=True, text=True, timeout=20)
    with tempfile.TemporaryDirectory(prefix="codex-native-token-api-", dir=str(Path(__file__).anchor)) as directory:
        script = Path(directory) / "token_facts.py"
        script.write_text(TOKEN_SCRIPT, encoding="utf-8")
        runtime = Runtime(Path(directory))
        runtime.request_context.hub_client = {"client_id": "electron-control-plane-exec-bridge", "client_type": "electron", "attestation_verified": True}
        try:
            argv = ["python", str(script)]
            with patch("coding_tools_mcp.exec_tools.build_mxc_windows_sandbox_invocation", side_effect=AssertionError("VM adapter forbidden")) as vm:
                result = runtime.exec_command({"cmd": "python", "argv": argv, "_windows_execution_mode": "native_only", "_windows_native_argv_prefixes": [argv], "yield_time_ms": 30000, "verbosity": "full"})
                while result["status"] == "running":
                    result = runtime.command_control({"action": "poll", "command_id": result["command_id"], "yield_time_ms": 1000, "verbosity": "full"})
                token = json.loads(result["stdout"]) if result.get("exit_code") == 0 else None
                receipt = {key: result.get(key) for key in ("command_id", "job_id", "status", "exit_code", "execution_backend", "isolation_level", "policy_decision")}
                receipt.update({"vm_adapter_calls": vm.call_count, "stderr_empty": not bool(result.get("stderr")), "stderr_sha256": hashlib.sha256(result.get("stderr", "").encode()).hexdigest()})
            return {"schema_version": 1, "observed_git_head": head, "capture_started_utc": started, "capture_finished_utc": datetime.now(timezone.utc).isoformat(), "scope": "source-runtime approved Python script temporary workspace, WinAPI token facts; no VM/live services", "host_token": json.loads(host.stdout), "native_token": token, "job_receipt": receipt, "probe_script_sha256": hashlib.sha256(TOKEN_SCRIPT.encode()).hexdigest(), "adapter_sha256": hashlib.sha256((SOURCE / "coding_tools_mcp/windows_mxc_sandbox.py").read_bytes()).hexdigest(), "limitations": ["Current host is not elevated; this is not evidence for elevated-host behavior", "Token facts do not replace filesystem/network escape tests"]}
        finally:
            runtime.close()


if __name__ == "__main__":
    report = capture()
    with Path(__file__).with_name("native-token-winapi-proof.json").open("x", encoding="utf-8") as output:
        json.dump(report, output, indent=2)
        output.write("\n")
    print(json.dumps(report, indent=2))
