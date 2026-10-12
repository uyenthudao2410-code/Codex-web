"""Root-only small r11 follow-up renewal transport; never invokes release operations."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tarfile

OUT = Path(__file__).resolve().parent
FROZEN = OUT.parent / "activation-server/root-ssh.py"
FROZEN_SHA = "d6aa00d14128b8905e0edb92df24a02eeb9867a3a032a53f41d8375b023d39ba"
if hashlib.sha256(FROZEN.read_bytes()).hexdigest() != FROZEN_SHA:
    print('{"phase":"r11_next_transport_failed","ok":false,"code":"FROZEN_TRANSPORT_CHANGED"}')
    raise SystemExit(2)
spec = importlib.util.spec_from_file_location("r11_next_frozen_transport", FROZEN)
transport = importlib.util.module_from_spec(spec); spec.loader.exec_module(transport)
REMOTE_PARENT, HOST, USER = transport.REMOTE_PARENT, transport.HOST, transport.USER


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def exclusive_receipt(value):
    directory = OUT / "remote-receipts"; directory.mkdir(exist_ok=True)
    destination = directory / (value["action"] + "-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".json")
    with destination.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, sort_keys=True, indent=2); handle.write("\n")
    print(json.dumps({"receipt_path": str(destination), **value}, separators=(",", ":")))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("stage", "observe", "close", "renew", "reopen"))
    parser.add_argument("--remote-dir")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--operator-approved", action="store_true")
    parser.add_argument("--approval-id")
    parser.add_argument("--approved-duration-ms", type=int)
    for name in ("expected-service-instance", "expected-state-sha256", "expected-grant-sha256", "observed-at-ms",
                 "expected-prior-marker-sha256", "expected-next-marker-sha256", "expected-activation-epoch",
                 "expected-runtime-instance", "expected-mcp-instance", "expected-contract-version"):
        parser.add_argument("--" + name)
    args = parser.parse_args()
    remote = args.remote_dir or REMOTE_PARENT + "/r11-approved-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    if not re.fullmatch(re.escape(REMOTE_PARENT) + r"/r11-approved-[0-9TZ]+", remote):
        raise ValueError("REMOTE_DIRECTORY_NOT_APPROVED")
    manifest = json.loads((OUT / "helper-manifest.json").read_bytes())
    if set(manifest["helpers"]) != {"r11_common.py", "ubuntu-r11-renewal-next.py"} or manifest.get("archives") != []:
        raise ValueError("SMALL_RENEWAL_HELPERS_ONLY")
    payload = {}
    for name, record in manifest["helpers"].items():
        raw = (OUT / name).read_bytes()
        if len(raw) != record["size_bytes"] or sha(raw) != record["sha256"]:
            raise ValueError("LOCAL_RENEWAL_HELPER_CHANGED")
        payload[name] = raw
    records = manifest["helpers"]
    if args.action == "stage":
        binary = io.BytesIO()
        with tarfile.open(fileobj=binary, mode="w") as archive:
            for name, raw in sorted(payload.items()):
                member = tarfile.TarInfo(name); member.size, member.mode = len(raw), 0o600
                archive.addfile(member, io.BytesIO(raw))
        stdin = binary.getvalue()
        if len(stdin) > 256 * 1024:
            raise ValueError("RENEWAL_HELPER_BUNDLE_TOO_LARGE")
        remote_argv = ["/usr/bin/python3", "-B", "-c", transport.STAGE, remote, json.dumps(records, separators=(",", ":"))]
    else:
        if not args.remote_dir:
            raise ValueError("EXISTING_STAGED_DIRECTORY_REQUIRED")
        argv = ["ubuntu-r11-renewal-next.py", args.action]
        if args.execute:
            if args.action == "observe" or not args.operator_approved or args.approved_duration_ms != 3600000:
                raise ValueError("EXPLICIT_NEW_60M_APPROVAL_REQUIRED")
            if not args.approval_id or not re.fullmatch(r"[A-Za-z0-9_-]{8,128}", args.approval_id):
                raise ValueError("NEW_APPROVAL_ID_REQUIRED")
            argv += ["--execute", "--operator-approved", "--confirm-target", HOST,
                     "--approval-id", args.approval_id, "--approved-duration-ms", "3600000"]
            fields = ["expected_service_instance", "expected_state_sha256", "expected_grant_sha256", "observed_at_ms",
                      "expected_prior_marker_sha256", "expected_next_marker_sha256"]
            if args.action == "reopen":
                fields += ["expected_activation_epoch", "expected_runtime_instance", "expected_mcp_instance", "expected_contract_version"]
            for field in fields:
                value = getattr(args, field)
                if not value:
                    raise ValueError("FRESH_EXACT_NEXT_WINDOW_PINS_REQUIRED")
                argv += ["--" + field.replace("_", "-"), value]
        remote_argv = ["/usr/bin/python3", "-B", "-c", transport.INVOKE, remote,
                       json.dumps(records, separators=(",", ":")), json.dumps(argv)]
        stdin = b""
    ssh = shutil.which("ssh")
    if not ssh:
        raise ValueError("SSH_NOT_AVAILABLE")
    base = {"action": args.action, "remote_dir": remote, "captured_at_utc": datetime.now(timezone.utc).isoformat(),
            "stderr_disclosed": False, "archives_transferred": False, "deployment_or_restart_requested": False}
    try:
        result = subprocess.run([ssh, "-T", "-oBatchMode=yes", "-oStrictHostKeyChecking=yes", "-oConnectTimeout=15",
                                 "-oServerAliveInterval=15", "-oServerAliveCountMax=4", USER + "@" + HOST,
                                 shlex.join(remote_argv)], input=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=600)
    except subprocess.TimeoutExpired:
        exclusive_receipt({**base, "ssh_returncode": None, "public_receipts": [], "effect_known": False,
                           "remote_mutation_possible": args.action == "stage" or args.execute,
                           "code": "TRANSPORT_TIMEOUT_OUTCOME_UNKNOWN_NO_REPLAY", "next_action": "READ_ONLY_INSPECT_EXACT_REMOTE_MARKER_AND_STATE"})
        raise SystemExit(2) from None
    try:
        receipts = transport.safe_receipt(result.stdout)
    except (ValueError, UnicodeError, json.JSONDecodeError):
        exclusive_receipt({**base, "ssh_returncode": result.returncode, "public_receipts": [], "effect_known": False,
                           "remote_mutation_possible": args.action == "stage" or args.execute,
                           "code": "PUBLIC_RECEIPT_UNAVAILABLE_OUTCOME_UNKNOWN_NO_REPLAY",
                           "next_action": "READ_ONLY_INSPECT_EXACT_REMOTE_MARKER_AND_STATE"})
        raise SystemExit(2) from None
    exclusive_receipt({**base, "ssh_returncode": result.returncode, "public_receipts": receipts})
    if result.returncode:
        raise SystemExit(result.returncode)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"phase": "r11_next_transport_failed", "ok": False,
                          "code": str(error) if isinstance(error, ValueError) else "NEXT_TRANSPORT_FAILED", "stderr_disclosed": False}))
        raise SystemExit(2) from None
