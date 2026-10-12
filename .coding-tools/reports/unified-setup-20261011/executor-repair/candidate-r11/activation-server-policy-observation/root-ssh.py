"""Root-only binary SSH staging/invocation. This file is prepared locally, not auto-executed."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tarfile

OUT = Path(__file__).resolve().parent
REMOTE_PARENT = "/home/svhome/.local/lib/codex-control-plane/incoming"
HOST, USER = "100.116.112.22", "svhome"

STAGE = r'''
import hashlib,io,json,os,pathlib,pwd,re,stat,subprocess,sys,tarfile
target=pathlib.Path(sys.argv[1]); expected=json.loads(sys.argv[2]); parent=pathlib.Path("/home/svhome/.local/lib/codex-control-plane/incoming")
def need(ok,code):
 if not ok: raise RuntimeError(code)
try:
 need(pwd.getpwuid(os.getuid()).pw_name=="svhome","USER_MISMATCH")
 address=subprocess.run(["tailscale","ip","-4"],capture_output=True,timeout=15)
 need(address.returncode==0 and "100.116.112.22" in address.stdout.decode().split(),"HOST_MISMATCH")
 need(parent.is_dir() and not parent.is_symlink() and stat.S_IMODE(parent.stat().st_mode)==0o700 and parent.stat().st_uid==os.getuid(),"PARENT_UNSAFE")
 need(target.parent==parent and re.fullmatch(r"r11-approved-[0-9TZ]+",target.name) and not target.exists() and not target.is_symlink(),"STAGE_TARGET_UNSAFE_OR_EXISTS")
 data=sys.stdin.buffer.read(16*1024*1024+1); need(len(data)<=16*1024*1024,"BUNDLE_TOO_LARGE")
 payload={}
 with tarfile.open(fileobj=io.BytesIO(data),mode="r:") as archive:
  for member in archive.getmembers():
   need(member.isfile() and member.name in expected and member.name not in payload and pathlib.PurePosixPath(member.name).name==member.name,"BUNDLE_MEMBER_INVALID")
   raw=archive.extractfile(member).read()
   need(len(raw)==expected[member.name]["size_bytes"] and hashlib.sha256(raw).hexdigest()==expected[member.name]["sha256"],"BUNDLE_HASH_CHANGED")
   payload[member.name]=raw
 need(set(payload)==set(expected),"BUNDLE_INCOMPLETE")
 target.mkdir(mode=0o700)
 for name,raw in payload.items():
  descriptor=os.open(target/name,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
  with os.fdopen(descriptor,"wb") as handle: handle.write(raw);handle.flush();os.fsync(handle.fileno())
 print(json.dumps({"phase":"r11_artifacts_staged","ok":True,"host":"100.116.112.22","remote_dir":str(target),"files":expected,"remote_mutation":True},separators=(",",":")))
except Exception as error:
 print(json.dumps({"phase":"r11_staging_failed","ok":False,"code":str(error) if isinstance(error,RuntimeError) else "STAGE_FAILED","remote_mutation_possible":True},separators=(",",":")))
 sys.exit(2)
'''

INVOKE = r'''
import hashlib,json,os,pathlib,stat,subprocess,sys
target=pathlib.Path(sys.argv[1]);expected=json.loads(sys.argv[2]);argv=json.loads(sys.argv[3])
try:
 if target.is_symlink() or not target.is_dir() or stat.S_IMODE(target.stat().st_mode)!=0o700 or target.stat().st_uid!=os.getuid(): raise RuntimeError("ARTIFACT_DIRECTORY_UNSAFE")
 for name,pin in expected.items():
  path=target/name
  if path.is_symlink() or not path.is_file() or stat.S_IMODE(path.stat().st_mode)!=0o600 or path.stat().st_uid!=os.getuid() or hashlib.sha256(path.read_bytes()).hexdigest()!=pin["sha256"]: raise RuntimeError("HELPER_HASH_CHANGED")
 os.execv("/usr/bin/python3",["/usr/bin/python3","-B",str(target/argv[0]),*argv[1:]])
except Exception as error:
 print(json.dumps({"phase":"r11_invocation_failed","ok":False,"code":str(error) if isinstance(error,RuntimeError) else "INVOCATION_FAILED"},separators=(",",":")))
 sys.exit(2)
'''

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def safe_receipt(stdout):
    values = []
    for line in stdout.decode("utf-8").splitlines():
        row = json.loads(line)
        if not isinstance(row, dict) or not isinstance(row.get("phase"), str):
            raise ValueError("INVALID_PUBLIC_RECEIPT")
        def check(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    if re.search(r"(^|_)(token|secret|password|authorization|credential)(_|$)", key, re.I):
                        raise ValueError("PRIVATE_FIELD_IN_STDOUT")
                    check(item)
            elif isinstance(value, list):
                for item in value: check(item)
        check(row)
        values.append(row)
    if not values:
        raise ValueError("NO_PUBLIC_RECEIPT")
    return values

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("stage", "observe", "close", "deploy", "renew", "reopen", "recovery-observe", "recover"))
    parser.add_argument("--remote-dir")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--expected-service-instance")
    parser.add_argument("--expected-state-sha256")
    parser.add_argument("--expected-grant-sha256")
    parser.add_argument("--observed-at-ms", type=int)
    parser.add_argument("--expected-current-link")
    for name in ("activation-epoch", "runtime-instance", "mcp-instance", "contract-version"):
        parser.add_argument("--expected-" + name)
    args = parser.parse_args()
    remote = args.remote_dir or (REMOTE_PARENT + "/r11-approved-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    if not re.fullmatch(re.escape(REMOTE_PARENT) + r"/r11-approved-[0-9TZ]+", remote):
        raise ValueError("REMOTE_DIRECTORY_NOT_APPROVED")
    manifest = json.loads((OUT / "helper-manifest.json").read_text())
    payload = {}
    for name, record in manifest["helpers"].items():
        raw = (OUT / name).read_bytes()
        if len(raw) != record["size_bytes"] or sha(raw) != record["sha256"]:
            raise ValueError("LOCAL_HELPER_PIN_CHANGED")
        payload[name] = raw
    if args.action == "stage":
        for record in manifest["archives"]:
            raw = (OUT / record["relative_path"]).read_bytes()
            if sha(raw) != record["sha256"] or len(raw) != record["size_bytes"]:
                raise ValueError("LOCAL_ARCHIVE_PIN_CHANGED")
            payload[record["name"]] = raw
        records = {name: {"sha256": sha(raw), "size_bytes": len(raw)} for name, raw in payload.items()}
        binary = io.BytesIO()
        with tarfile.open(fileobj=binary, mode="w") as archive:
            for name, raw in sorted(payload.items()):
                member = tarfile.TarInfo(name); member.size, member.mode = len(raw), 0o600
                archive.addfile(member, io.BytesIO(raw))
        remote_argv = ["/usr/bin/python3", "-B", "-c", STAGE, remote, json.dumps(records, separators=(",", ":"))]
        stdin = binary.getvalue()
    else:
        if not args.remote_dir:
            raise ValueError("EXISTING_STAGED_DIRECTORY_REQUIRED")
        argv = ["ubuntu-r11-recovery.py"] if args.action in {"recover", "recovery-observe"} else ["ubuntu-r11-rollout.py"] if args.action == "deploy" else ["ubuntu-r11-authority.py", args.action]
        if args.execute:
            argv += ["--execute", "--operator-approved", "--confirm-target", HOST]
            names = ("expected_state_sha256", "observed_at_ms", "expected_current_link") if args.action == "recover" else ("expected_service_instance", "expected_state_sha256", "expected_grant_sha256", "observed_at_ms")
            for name in names:
                value = getattr(args, name)
                if value is None: raise ValueError("FRESH_PINS_REQUIRED")
                argv += ["--" + name.replace("_", "-"), str(value)]
            if args.action == "reopen":
                for name in ("expected_activation_epoch", "expected_runtime_instance", "expected_mcp_instance", "expected_contract_version"):
                    value = getattr(args, name)
                    if not value: raise ValueError("NEW_NODE_PINS_REQUIRED")
                    argv += ["--" + name.replace("_", "-"), value]
        remote_argv = ["/usr/bin/python3", "-B", "-c", INVOKE, remote, json.dumps(manifest["helpers"], separators=(",", ":")), json.dumps(argv)]
        stdin = b""
    ssh = shutil.which("ssh")
    if not ssh: raise ValueError("SSH_NOT_AVAILABLE")
    result = subprocess.run([ssh, "-T", "-oBatchMode=yes", "-oStrictHostKeyChecking=yes", "-oConnectTimeout=15",
                             USER + "@" + HOST, shlex.join(remote_argv)], input=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
    # stderr is deliberately never printed or copied into repository evidence.
    receipts = safe_receipt(result.stdout)
    receipt = {"action": args.action, "remote_dir": remote, "captured_at_utc": datetime.now(timezone.utc).isoformat(),
               "ssh_returncode": result.returncode, "public_receipts": receipts, "stderr_disclosed": False}
    receipt_dir = OUT / "remote-receipts"
    receipt_dir.mkdir(exist_ok=True)
    receipt_path = receipt_dir / (args.action + "-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".json")
    with receipt_path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(receipt, handle, sort_keys=True, indent=2); handle.write("\n")
    print(json.dumps({"receipt_path": str(receipt_path), **receipt}, separators=(",", ":")))
    if result.returncode:
        raise SystemExit(result.returncode)

if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"phase": "root_transport_failed", "ok": False, "code": str(error) if isinstance(error, ValueError) else "ROOT_TRANSPORT_FAILED", "stderr_disclosed": False}, separators=(",", ":")))
        raise SystemExit(2) from None
