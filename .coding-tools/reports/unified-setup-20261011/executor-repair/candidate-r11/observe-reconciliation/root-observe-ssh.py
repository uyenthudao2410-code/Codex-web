"""Root-only fixed two-helper staging, observation and rejected cleanup."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tarfile

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REMOTE_DIR = "/home/svhome/.local/lib/codex-control-plane/incoming/r11-approved-20261011T164200000001Z"
SSH_SHA = "d6aa00d14128b8905e0edb92df24a02eeb9867a3a032a53f41d8375b023d39ba"
HELPERS = {"observe-r11.py": "6525b2c6069c474c1c0c6e45084f19e4700246d2262b087c633e3692983caf73",
    "cleanup-r11.py": "1d679771282690585912b83782cd3ff5f9d3f06e3b5ab78aa3de10e110266610"}


class Failure(Exception):
    def __init__(self, code):
        self.code = code


def require(condition, code):
    if not condition:
        raise Failure(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def frozen_ssh():
    path = HERE.parent / "activation-server/root-ssh.py"
    require(path.is_file() and not path.is_symlink() and sha(path.read_bytes()) == SSH_SHA, "FROZEN_SSH_HELPER_CHANGED")
    spec = importlib.util.spec_from_file_location("r11_observer_root_pinned_ssh", path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def exclusive(path, value):
    require(not path.exists() and not path.is_symlink(), "IMMUTABLE_TRANSPORT_INTENT_EXISTS_NO_REPLAY")
    with path.open("xb") as handle:
        handle.write(json.dumps(value, sort_keys=True).encode())
        handle.flush()
        import os
        os.fsync(handle.fileno())


def transport(action, execute):
    require(execute is True and action in {"stage", "observe", "cleanup"}, "ROOT_EXPLICIT_FIXED_ACTION_REQUIRED")
    pinned = frozen_ssh()
    payload = {}
    for name, expected in HELPERS.items():
        path = HERE / name
        require(path.is_file() and not path.is_symlink(), "LOCAL_HELPER_UNSAFE")
        payload[name] = path.read_bytes()
        require(sha(payload[name]) == expected, "LOCAL_HELPER_CHANGED")
    records = {name: {"sha256": sha(raw), "size_bytes": len(raw)} for name, raw in payload.items()}
    binary = b""
    if action == "stage":
        bundle = io.BytesIO()
        with tarfile.open(fileobj=bundle, mode="w") as archive:
            for name, raw in sorted(payload.items()):
                member = tarfile.TarInfo(name)
                member.size, member.mode = len(raw), 0o600
                archive.addfile(member, io.BytesIO(raw))
        binary = bundle.getvalue()
        remote = ["/usr/bin/python3", "-B", "-c", pinned.STAGE, REMOTE_DIR, json.dumps(records)]
    else:
        argv = ["observe-r11.py", "observe"] if action == "observe" else ["cleanup-r11.py", "cleanup", "--execute"]
        remote = ["/usr/bin/python3", "-B", "-c", pinned.INVOKE, REMOTE_DIR, json.dumps(records), json.dumps(argv)]
    ssh = shutil.which("ssh")
    require(ssh is not None, "SSH_UNAVAILABLE")
    if action in {"stage", "cleanup"}:
        exclusive(HERE / ("transport-intent-" + action + ".json"), {"action": action, "remote_dir": REMOTE_DIR, "files": records})
    try:
        result = subprocess.run([ssh, "-T", "-oBatchMode=yes", "-oStrictHostKeyChecking=yes", "-oConnectTimeout=15",
            "svhome@100.116.112.22", shlex.join(remote)], input=binary, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
    except Exception:
        raise Failure("SSH_TRANSPORT_UNCERTAIN_NO_RETRY") from None
    require(len(result.stdout) <= 1024 * 1024 and b"Bearer " not in result.stdout and b"PRIVATE KEY" not in result.stdout,
        "UNSAFE_PUBLIC_OUTPUT_REJECTED")
    public = pinned.safe_receipt(result.stdout)
    record = {"phase": "root_rejected_canary_" + action, "ok": result.returncode == 0 and all(row.get("ok") is True for row in public),
        "remote_dir": REMOTE_DIR, "public_receipts": public, "ssh_returncode": result.returncode,
        "stderr_disclosed": False, "remote_mutation": action != "observe", "replay_forbidden": True}
    exclusive(HERE / ("receipt-" + action + "-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".json"), record)
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("stage", "observe", "cleanup"))
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    try:
        result = transport(args.action, args.execute)
        print(json.dumps(result, sort_keys=True))
        if result["ok"] is not True:
            raise SystemExit(1)
    except Exception as error:
        print(json.dumps({"ok": False, "phase": "root_reconciliation_transport_failed",
            "code": getattr(error, "code", "ROOT_RECONCILIATION_TRANSPORT_FAILED"), "replay_forbidden": True,
            "stderr_disclosed": False}, sort_keys=True))
        raise SystemExit(2) from None
