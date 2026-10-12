"""Reviewed single-attempt SSH transport; no live call occurs on import.

Stage exact canary bytes, discover public facade contract, or run one reviewed
canary preflight/execution. Public stdout is streamed to immutable evidence.
SSH stderr is discarded. No transport or canary execution is retried.
"""
from __future__ import annotations
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys

BASE = Path(__file__).resolve().parent
CANARY = BASE / "r10-mcp-canary-v2.py"
CANARY_SHA = "54f8ee88889e60437c7831410aae7845b2481401ce3f73bf7daa33a77e3ea047"
REMOTE_DIR = "/home/svhome/.local/lib/codex-control-plane/incoming/r10-approved-20261011T123342Z"
REMOTE = REMOTE_DIR + "/r10-mcp-canary-v2.py"
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=10", "svhome@100.116.112.22"]
BINDING = "bind_3e05bf64cb3e4bab93d930ae1692bebb"
SERVICE = "cp_6766892f5ada47d1862a0d24334f1116"
CONTEXT = "ctx_9e58c758a20249479b6ec806970f68ca"
PILOT = "pilot_25fa8c634f7f40e282c30a303b51bfd0"
REQUESTED = 1791722898491
EXPIRES = 1791726498491
PUBLIC_PHASES = {"root_mcp_transport_helper_staged", "root_mcp_transport_discovery", "root_mcp_transport_refused",
    "r10_mcp_canary_preflight", "r10_mcp_canary_task_opened", "r10_mcp_canary_queued", "r10_mcp_canary_observed",
    "r10_mcp_canary_terminal", "r10_mcp_canary_cleanup_complete", "r10_mcp_canary_complete", "r10_mcp_canary_refused"}
PRIVATE_KEYS = {"authorization", "authorization_header", "token", "node_secret", "secret", "password", "credential",
    "credentials", "private_key", "stdout", "stderr", "output", "raw_output", "header", "headers"}

REMOTE_CODE = r'''
from pathlib import Path
import hashlib,json,os,re,runpy,stat,sys
def need(value):
 if not value: raise RuntimeError("REMOTE_PACKET_GUARD_REFUSED")
try:
 p=Path(sys.argv[1]); expected=sys.argv[2]; action=sys.argv[3]
 need(str(p)=="/home/svhome/.local/lib/codex-control-plane/incoming/r10-approved-20261011T123342Z/r10-mcp-canary-v2.py")
 need(p.parent.resolve()==p.parent and p.parent.is_dir())
 parent=p.parent.lstat()
 need(parent.st_uid==os.getuid() and stat.S_IMODE(parent.st_mode)==0o700)
 if action=="stage":
  raw=sys.stdin.buffer.read(131073)
  need(0<len(raw)<=131072 and hashlib.sha256(raw).hexdigest()==expected)
  if p.exists():
   need(not p.is_symlink() and p.is_file() and p.stat().st_uid==os.getuid() and stat.S_IMODE(p.stat().st_mode)==0o600 and p.read_bytes()==raw)
  else:
   fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
   with os.fdopen(fd,"wb") as h: h.write(raw);h.flush();os.fsync(h.fileno())
  need(hashlib.sha256(p.read_bytes()).hexdigest()==expected)
  print(json.dumps({"phase":"root_mcp_transport_helper_staged","ok":True,"sha256":expected,"bytes":len(raw)},separators=(",",":")),flush=True)
 else:
  need(not p.is_symlink() and p.is_file() and p.stat().st_uid==os.getuid() and stat.S_IMODE(p.stat().st_mode)==0o600)
  raw=p.read_bytes();need(0<len(raw)<=131072 and hashlib.sha256(raw).hexdigest()==expected)
  if action=="discover":
   scope={"__name__":"root_mcp_transport_discovery_module","__file__":str(p)}
   exec(compile(raw,str(p),"exec"),scope)
   origin,authorization=scope["mcp_credentials"]()
   inventory=scope["call"](origin,authorization,"workspace_context",{"operation":"inventory"})
   contract=inventory.get("tool_contract")
   need(isinstance(contract,dict) and set(contract)=={"schema_version","profile","sha256"})
   need(type(contract["schema_version"]) is int and contract["schema_version"]>0)
   need(isinstance(contract["profile"],str) and re.fullmatch(r"[A-Za-z0-9_-]{3,96}",contract["profile"]))
   need(isinstance(contract["sha256"],str) and re.fullmatch(r"[a-f0-9]{64}",contract["sha256"]))
   target=[row for row in inventory.get("targets",[]) if isinstance(row,dict) and row.get("binding_id")=="bind_3e05bf64cb3e4bab93d930ae1692bebb"]
   need(len(target)==1)
   safe={"binding_id":"bind_3e05bf64cb3e4bab93d930ae1692bebb"}
   for key,allowed in (("presence_state",{"online","offline","unknown"}),("readiness",{"ready","degraded","blocked","unknown"}),("policy_state",{"enabled","disabled","expired","unobserved","unknown","invalid","absent"})):
    need(target[0].get(key) in allowed);safe[key]=target[0][key]
   print(json.dumps({"phase":"root_mcp_transport_discovery","ok":True,"remote_mutation":False,"tool_contract":contract,"target":safe},separators=(",",":")),flush=True)
  elif action in {"preflight","execute"}:
   sys.argv=[str(p)]+sys.argv[4:]
   scope={"__name__":"__main__","__file__":str(p)}
   exec(compile(raw,str(p),"exec"),scope)
  else: raise RuntimeError("REMOTE_ACTION_INVALID")
except Exception:
 print(json.dumps({"phase":"root_mcp_transport_refused","ok":False,"code":"REMOTE_PACKET_OR_DISCOVERY_REFUSED","no_automatic_retry":True},separators=(",",":")),flush=True)
 raise SystemExit(2) from None
'''

def require(value: object, code: str) -> None:
    if not value:
        raise RuntimeError(code)

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def pins_bytes(path: Path) -> tuple[bytes, dict]:
    resolved = path.resolve(strict=True)
    require(resolved.parent == BASE and resolved.is_file() and not path.is_symlink(), "PUBLIC_PIN_PATH_INVALID")
    raw = resolved.read_bytes()
    require(0 < len(raw) <= 32768, "PUBLIC_PIN_SIZE_INVALID")
    pins = json.loads(raw)
    patterns = {"service_instance_id": r"cp_[a-f0-9]{32}", "context_id": r"ctx_[a-f0-9]{32}", "pilot_id": r"pilot_[a-f0-9]{32}",
        "activation_epoch_id": r"activation-[A-Za-z0-9_-]{8,128}", "process_instance_id": r"[A-Za-z0-9_-]{8,128}",
        "server_instance_id": r"[A-Za-z0-9_-]{8,128}", "native_contract_sha256": r"[a-f0-9]{64}",
        "rollout_receipt_sha256": r"[a-f0-9]{64}", "native_observation_sha256": r"[a-f0-9]{64}"}
    require(isinstance(pins, dict) and set(pins) == set(patterns) | {"requested_at_ms", "expires_at_ms", "facade_contract"}, "EXACT_PUBLIC_PINS_REQUIRED")
    require(all(isinstance(pins[key], str) and re.fullmatch(pattern, pins[key]) for key, pattern in patterns.items()), "PUBLIC_PIN_FORMAT_INVALID")
    require(pins["service_instance_id"] == SERVICE and pins["context_id"] == CONTEXT and pins["pilot_id"] == PILOT
            and type(pins["requested_at_ms"]) is int and pins["requested_at_ms"] == REQUESTED
            and type(pins["expires_at_ms"]) is int and pins["expires_at_ms"] == EXPIRES, "EXACT_APPROVED_WINDOW_CHANGED")
    require(pins["activation_epoch_id"] != "activation-mv3qe36p-991f11f44f47d32ea2e217b1db882ff7", "FRESH_R10_EPOCH_REQUIRED")
    contract = pins["facade_contract"]
    require(isinstance(contract, dict) and set(contract) == {"schema_version", "profile", "sha256"}
        and type(contract["schema_version"]) is int and contract["schema_version"] > 0
        and isinstance(contract["profile"], str) and re.fullmatch(r"[A-Za-z0-9_-]{3,96}", contract["profile"])
        and isinstance(contract["sha256"], str) and re.fullmatch(r"[a-f0-9]{64}", contract["sha256"]), "FACADE_CONTRACT_INVALID")
    return raw, pins

def public_record(raw: bytes) -> dict:
    require(0 < len(raw) <= 131072, "REMOTE_PUBLIC_LINE_SIZE_INVALID")
    row = json.loads(raw)
    require(isinstance(row, dict) and row.get("phase") in PUBLIC_PHASES, "REMOTE_PUBLIC_PHASE_INVALID")
    def walk(value: object) -> None:
        if isinstance(value, dict):
            require(not any(str(key).lower() in PRIVATE_KEYS for key in value), "REMOTE_NONPUBLIC_KEY_REFUSED")
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
    walk(row)
    return row

def emit(row: dict, evidence) -> None:
    material = json.dumps(row, separators=(",", ":"), allow_nan=False).encode() + b"\n"
    evidence.write(material)
    evidence.flush()
    sys.stdout.buffer.write(material)
    sys.stdout.buffer.flush()

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("stage", "discover", "preflight", "execute"))
    parser.add_argument("--pins-file", type=Path)
    parser.add_argument("--mode", choices=("cold", "warm"))
    parser.add_argument("--expected-state-sha256")
    parser.add_argument("--root-execute", action="store_true")
    args = parser.parse_args()
    helper = CANARY.read_bytes()
    require(sha(helper) == CANARY_SHA, "FROZEN_CANARY_V2_CHANGED")
    raw, pins = b"", None
    argv = ["python3", "-B", "-c", REMOTE_CODE, REMOTE, CANARY_SHA, args.action]
    if args.action in {"preflight", "execute"}:
        require(args.pins_file is not None and args.mode is not None, "PINS_FILE_AND_MODE_REQUIRED")
        raw, pins = pins_bytes(args.pins_file)
        argv += ["--pins-b64", base64.b64encode(raw).decode("ascii"), "--mode", args.mode]
        if args.action == "execute":
            require(args.root_execute and isinstance(args.expected_state_sha256, str)
                and re.fullmatch(r"[a-f0-9]{64}", args.expected_state_sha256), "EXPLICIT_EXECUTION_AND_STATE_HASH_REQUIRED")
            argv += ["--root-execute", "--expected-state-sha256", args.expected_state_sha256]
        else:
            require(not args.root_execute and args.expected_state_sha256 is None, "READ_ONLY_PREFLIGHT_FLAGS_INVALID")
    else:
        require(args.pins_file is None and args.mode is None and not args.root_execute and args.expected_state_sha256 is None,
                "NON_CANARY_FLAGS_INVALID")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    name = "transport-" + args.action + ("-" + args.mode if args.mode else "") + "-" + stamp + ".jsonl"
    destination = BASE / name
    with destination.open("xb") as evidence:
        emit({"phase": "root_mcp_transport_started", "action": args.action, "mode": args.mode, "helper_sha256": CANARY_SHA,
            "pins_sha256": sha(raw) if pins is not None else None, "expected_state_sha256": args.expected_state_sha256,
            "evidence": str(destination), "stderr_retained": False, "no_automatic_retry": True}, evidence)
        if args.action == "execute":
            key = sha(json.dumps({"epoch": pins["activation_epoch_id"], "context": CONTEXT, "pilot": PILOT,
                "mode": args.mode}, sort_keys=True, separators=(",", ":")).encode())
            with (BASE / ("transport-execution-once-" + key + ".json")).open("x", encoding="utf-8") as marker:
                json.dump({"action": "execute", "mode": args.mode, "evidence": name, "pins_sha256": sha(raw),
                    "expected_state_sha256": args.expected_state_sha256, "no_automatic_retry": True}, marker)
        process = subprocess.Popen(SSH + [shlex.join(argv)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        require(process.stdin is not None and process.stdout is not None, "BINARY_PROCESS_PIPE_UNAVAILABLE")
        if args.action == "stage":
            process.stdin.write(helper)
        process.stdin.close()
        count, total, last = 0, 0, None
        invalid = False
        for line in process.stdout:
            total += len(line)
            if total > 1048576:
                invalid = True
                continue
            try:
                row = public_record(line)
            except Exception:
                invalid = True
                continue
            count += 1
            last = row
            evidence.write(line)
            evidence.flush()
            sys.stdout.buffer.write(line)
            sys.stdout.buffer.flush()
        code = process.wait()
        require(not invalid and count > 0 and last is not None, "REMOTE_OUTPUT_NOT_VERIFIED_PUBLIC")
        good = code == 0 and last.get("ok") is True
        emit({"phase": "root_mcp_transport_finished", "ok": good, "action": args.action, "mode": args.mode,
            "remote_exit_code": code, "last_public_phase": last["phase"], "public_rows": count,
            "evidence": str(destination), "no_automatic_retry": True,
            "root_reconciliation_required": not good}, evidence)
    print(json.dumps({"phase": "root_mcp_transport_evidence_sealed", "ok": good, "file": str(destination),
        "sha256": sha(destination.read_bytes()), "no_automatic_retry": True}, separators=(",", ":")), flush=True)
    if not good:
        raise SystemExit(2)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        print(json.dumps({"phase": "root_mcp_transport_failed", "ok": False,
            "code": "TRANSPORT_REFUSED_OR_OUTCOME_UNCERTAIN", "stderr_retained": False,
            "no_automatic_retry": True, "root_reconciliation_required": True}, separators=(",", ":")), flush=True)
        raise SystemExit(2) from None
