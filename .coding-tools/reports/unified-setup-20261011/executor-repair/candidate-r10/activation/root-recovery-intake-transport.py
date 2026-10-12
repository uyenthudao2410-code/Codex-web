"""Pinned supported owner intake recovery transport; no renewal or code deployment."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import shlex
import subprocess
import sys

BASE = Path(__file__).resolve().parent
HELPER = BASE.parent.parent / "store-delta/ubuntu-r10-same-expiry-recovery-intake.py"
REMOTE = "/home/svhome/.local/lib/codex-control-plane/incoming/r10-approved-20261011T123342Z/ubuntu-r10-same-expiry-recovery-intake.py"
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=10", "svhome@100.116.112.22"]
SERVICE = "cp_6766892f5ada47d1862a0d24334f1116"

def need(value, code):
    if not value: raise RuntimeError(code)

def sha(raw): return hashlib.sha256(raw).hexdigest()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["stage", "observe", "close", "reopen"])
    p.add_argument("--helper-sha256", required=True)
    p.add_argument("--epoch")
    p.add_argument("--native-process")
    p.add_argument("--native-server")
    a = p.parse_args()
    raw = HELPER.read_bytes()
    need(sha(raw) == a.helper_sha256, "REVIEWED_HELPER_CHANGED")
    stdin = b""
    if a.action == "stage":
        code = """from pathlib import Path
import os,sys,hashlib,json,stat
p=Path(sys.argv[1]); expected=sys.argv[2]; raw=sys.stdin.buffer.read(131073)
assert len(raw)<=131072 and hashlib.sha256(raw).hexdigest()==expected
s=p.parent.lstat(); assert stat.S_ISDIR(s.st_mode) and not p.parent.is_symlink() and s.st_uid==os.getuid() and s.st_mode & 0o077 == 0
if p.exists():
 assert not p.is_symlink() and p.stat().st_uid==os.getuid() and p.stat().st_mode & 0o077 == 0 and p.read_bytes()==raw
else:
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
 with os.fdopen(fd,'wb') as h: h.write(raw)
print(json.dumps({'phase':'r10_recovery_helper_staged','ok':True,'sha256':expected}))
"""
        argv = ["python3", "-B", "-c", code, REMOTE, a.helper_sha256]
        stdin = raw
    else:
        argv = ["python3", "-B", REMOTE, a.action]
        if a.action in {"close", "reopen"}:
            observation = json.loads((BASE / "server-recovery-observation.json").read_bytes())
            need(observation["ok"] and observation["service_instance_id"] == SERVICE, "OBSERVATION_SERVICE_CHANGED")
            argv += ["--execute", "--operator-approved", "--expected-service-instance", SERVICE,
                "--expected-state-sha256", observation["state_sha256"],
                "--expected-authority-marker-sha256", observation["authority_marker_sha256"]]
            if a.action == "reopen":
                need(a.epoch and a.native_process and a.native_server, "FRESH_NATIVE_IDENTITY_REQUIRED")
                argv += ["--expected-activation-epoch", a.epoch, "--expected-process-instance", a.native_process,
                    "--expected-server-instance", a.native_server, "--expected-native-contract",
                    "bc44c044a0b08dfdea80b8ba0dfcc080e180e21a5460dbf9726b49ac1fa769b0"]
    result = subprocess.run(SSH + [shlex.join(argv)], input=stdin, capture_output=True, timeout=60)
    need(0 < len(result.stdout) <= 131072, "BOUNDED_PUBLIC_RECEIPT_REQUIRED")
    rows = [json.loads(line) for line in result.stdout.splitlines() if line]
    need(len(rows) == 1 and rows[0].get("phase", "").startswith("r10_"), "EXACT_PUBLIC_RECEIPT_REQUIRED")
    row = rows[0]
    good = result.returncode == 0 and row.get("ok") is True
    if a.action != "stage":
        names = {"observe":"server-recovery-observation.json", "close":"server-recovery-closed.json", "reopen":"server-recovery-reopened.json"}
        name = names[a.action] if good else "server-recovery-" + a.action + "-failed-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".json"
        with (BASE / name).open("xb") as f: f.write(result.stdout)
        print(json.dumps({"ok":good,"receipt":name,"sha256":sha(result.stdout),"public_receipt":row,"no_automatic_retry":True}))
    else: print(json.dumps(row))
    if not good: raise SystemExit(2)

if __name__ == "__main__":
    try: main()
    except Exception as e:
        print(json.dumps({"ok":False,"code":str(e) if isinstance(e,RuntimeError) else "RECOVERY_TRANSPORT_UNCERTAIN", "no_automatic_retry":True}))
        raise SystemExit(2) from None
