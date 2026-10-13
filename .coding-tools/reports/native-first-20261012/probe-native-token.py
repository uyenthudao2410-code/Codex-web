"""Sanitized, source-runtime token observation; never starts a VM or service."""
from __future__ import annotations

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

# Raw whoami data exists only in the subprocess memory. No account, host,
# arbitrary group name, environment value, or credential is emitted.
TOKEN_SCRIPT = r"""const cp=require('node:child_process'); const exe='C:\\Windows\\System32\\whoami.exe'; const rows=(s)=>s.trim().split(/\r?\n/).filter(Boolean).map(l=>Array.from(l.matchAll(/\"((?:[^\"]|\"\")*)\"|([^,]+)/g),m=>(m[1]===undefined?m[2]:m[1].replace(/\"\"/g,'\"')))); const run=(kind)=>{const r=cp.spawnSync(exe,[kind,'/fo','csv','/nh'],{encoding:'utf8',timeout:10000,windowsHide:true});return {status:r.status,error:r.error?r.error.code:null,data:r.status===0?rows(r.stdout):[]};}; const g=run('/groups'),p=run('/priv');const integrity=g.data.map(r=>r.find(x=>/^S-1-16-\d+$/.test(x))).filter(Boolean);const admin=g.data.find(r=>r.includes('S-1-5-32-544'));const attrs=admin?admin[admin.length-1]:'';const names=['SeDebugPrivilege','SeImpersonatePrivilege','SeAssignPrimaryTokenPrivilege','SeTcbPrivilege','SeBackupPrivilege','SeRestorePrivilege','SeTakeOwnershipPrivilege','SeLoadDriverPrivilege','SeCreateTokenPrivilege','SeSecurityPrivilege','SeSystemEnvironmentPrivilege'];const sensitive=p.data.filter(r=>names.includes(r[0])).map(r=>({name:r[0],enabled:/^Enabled$/i.test(r[r.length-1]),disabled:/^Disabled$/i.test(r[r.length-1])}));console.log(JSON.stringify({groups_status:g.status,groups_error:g.error,privileges_status:p.status,privileges_error:p.error,integrity_sids:integrity,high_or_system_integrity:integrity.some(x=>Number(x.split('-').pop())>=12288),administrator_group_present:Boolean(admin),administrator_group_enabled:attrs.includes('Enabled group')&&!attrs.includes('Deny only'),administrator_group_deny_only:attrs.includes('Deny only'),sensitive_privileges:sensitive}));"""


def capture() -> dict:
    started = datetime.now(timezone.utc).isoformat()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPOSITORY, text=True).strip()
    host = subprocess.run([r"C:\Program Files\nodejs\node.exe", "-e", TOKEN_SCRIPT], check=True, capture_output=True, text=True, timeout=20)
    host_token = json.loads(host.stdout)
    with tempfile.TemporaryDirectory(prefix="codex-native-token-", dir=str(Path(__file__).anchor)) as directory:
        runtime = Runtime(Path(directory))
        runtime.request_context.hub_client = {"client_id": "electron-control-plane-exec-bridge", "client_type": "electron", "attestation_verified": True}
        try:
            script_path = Path(directory) / "sanitized-token.js"
            script_path.write_text(TOKEN_SCRIPT, encoding="utf-8")
            argv = ["node", str(script_path)]
            with patch("coding_tools_mcp.exec_tools.build_mxc_windows_sandbox_invocation", side_effect=AssertionError("VM adapter forbidden in token fixture")) as vm:
                result = runtime.exec_command({"cmd": "node", "argv": argv, "_windows_execution_mode": "native_only", "_windows_native_argv_prefixes": [argv], "yield_time_ms": 30000, "verbosity": "full"})
                while result["status"] == "running":
                    result = runtime.command_control({"action": "poll", "command_id": result["command_id"], "yield_time_ms": 1000, "verbosity": "full"})
                native_token = json.loads(result["stdout"]) if result.get("exit_code") == 0 else None
                receipt = {key: result.get(key) for key in ("command_id", "job_id", "status", "exit_code", "execution_backend", "isolation_level", "policy_decision")}
                receipt["stderr_sha256"] = hashlib.sha256(result.get("stderr", "").encode()).hexdigest()
                receipt["stderr_empty"] = not bool(result.get("stderr"))
                receipt["vm_adapter_calls"] = vm.call_count
            return {
                "schema_version": 1,
                "observed_git_head": head,
                "capture_started_utc": started,
                "capture_finished_utc": datetime.now(timezone.utc).isoformat(),
                "scope": "source runtime native-only isolated temporary workspace, sanitized whoami child token; no VM/live service",
                "host_token": host_token,
                "native_token": native_token,
                "job_receipt": receipt,
                "probe_script_sha256": hashlib.sha256(TOKEN_SCRIPT.encode()).hexdigest(),
                "adapter_sha256": hashlib.sha256((SOURCE / "coding_tools_mcp/windows_mxc_sandbox.py").read_bytes()).hexdigest(),
                "limitations": ["whoami reports the spawned child token; no arbitrary account/group names or raw privilege descriptions retained", "leastPrivilege controls LPAC and cannot be represented by the required BaseContainer/PSEC tier"],
            }
        finally:
            runtime.close()


if __name__ == "__main__":
    report = capture()
    output = Path(__file__).with_name("native-token-proof.json")
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps(report, indent=2))
