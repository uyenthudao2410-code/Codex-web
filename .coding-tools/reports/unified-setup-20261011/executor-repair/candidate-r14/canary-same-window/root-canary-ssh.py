"""New-marker canary transport; only root explicitly executes remote phases."""
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
import sys
import tarfile
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SERVER = HERE.parent.parent / "candidate-r11/activation-server"
COMMON_SOURCE = HERE.parent.parent / "candidate-r13/authority-5h/r11_common.py"
SSH_HELPER_SHA = "d6aa00d14128b8905e0edb92df24a02eeb9867a3a032a53f41d8375b023d39ba"
COMMON_SHA = "25f2d15359ff49a50e1ded411d40f1f029fb6067390c68aff9b93bda0130d986"
NATIVE_SHA = "0e4733844a471814a3a6240fa9c0423b56195ab80f6e5283b5c978e28edaaed4"
MIN_CANARY_REMAINING_MS = 720000
AUTHORITY_PRIOR_SHA = "a3c5c2ee239644a3937fa5f81c7fc14b89544bfde82c4bea56a928ddda408487"
R14_SAME_WINDOW_ARCHIVE_SHA = "f2a1e77b08f7109ccbd4072055da8d281a339dd5f32f154285d3696ad11f6324"
R14_SAME_WINDOW_FREEZE_SHA = "a618711528b418db77a901a5b83537bde2d511618ef630ab22670a2e6579625d"
REMOTE_PARENT = "/home/svhome/.local/lib/codex-control-plane/incoming"
PHASES = {"preflight", "dispatch", "observe", "cleanup"}


class Failure(Exception):
    def __init__(self, code):
        self.code = code


def require(ok, code):
    if not ok:
        raise Failure(code)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def fixed_module(name, path, expected):
    require(path.is_file() and not path.is_symlink() and sha(path.read_bytes()) == expected, "FROZEN_LOCAL_HELPER_CHANGED")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reject_private(value):
    if isinstance(value, dict):
        for key, item in value.items():
            require(isinstance(key, str) and not re.search(r"(^|_)(token|secret|password|authorization|credential)(_|$)", key, re.I), "PRIVATE_FIELD_REJECTED")
            reject_private(item)
    elif isinstance(value, list):
        for item in value:
            reject_private(item)
    elif isinstance(value, str):
        require("Bearer " not in value and "PRIVATE KEY" not in value, "PRIVATE_VALUE_REJECTED")


def read_json(path):
    path = Path(path).resolve(strict=True)
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 1024 * 1024, "LOCAL_JSON_INPUT_UNSAFE")
    raw = path.read_bytes()
    value = json.loads(raw)
    require(isinstance(value, dict), "LOCAL_JSON_INPUT_INVALID")
    reject_private(value)
    return path, raw, value


def freeze(path, raw):
    require(not path.exists() and not path.is_symlink(), "LOCAL_IMMUTABLE_ARTIFACT_ALREADY_EXISTS_NO_REPLAY")
    with path.open("xb") as handle:
        handle.write(raw); handle.flush()
        import os
        os.fsync(handle.fileno())


def prepare(args):
    require(args.pins and args.native_preflight and re.fullmatch(r"[a-f0-9]{64}", str(args.expected_native_preflight_sha256)), "EXACT_PINS_AND_NATIVE_RECEIPT_REQUIRED")
    _, pins_raw, pins = read_json(args.pins)
    _, native_raw, native = read_json(args.native_preflight)
    require(sha(native_raw) == args.expected_native_preflight_sha256, "NATIVE_RECEIPT_FILE_HASH_MISMATCH")
    require(pins.get("contract_version") == "sha256:" + NATIVE_SHA
            and pins.get("native_tool_contract_sha256") == NATIVE_SHA, "R14_SAME_WINDOW_NATIVE_CONTRACT_PIN_REQUIRED")
    require(native.get("ok") is True and native.get("kind") == "r14_same_window_query_only_native_preflight"
            and native.get("package", {}).get("app_asar_sha256") == R14_SAME_WINDOW_ARCHIVE_SHA
            and native.get("package", {}).get("source_freeze_sha256") == R14_SAME_WINDOW_FREEZE_SHA
            and native.get("package", {}).get("matched_files") == 17
            and all(native.get(field) == pins.get(field) for field in
                    ("activation_epoch", "runtime_instance_id", "mcp_server_instance_id", "contract_version", "native_tool_contract_sha256")),
            "AUTHENTICATED_R14_SAME_WINDOW_NATIVE_RECEIPT_REQUIRED")
    proof = pins.get("native_preflight")
    require(isinstance(proof, dict) and proof.get("receipt_sha256") == sha(native_raw), "NATIVE_RECEIPT_PIN_MISMATCH")
    native_fields = native.get("native_preflight", native)
    require(isinstance(native_fields, dict)
            and all(native_fields.get(key) == value for key, value in proof.items() if key != "receipt_sha256"), "NATIVE_RECEIPT_FIELDS_MISMATCH")
    now = int(time.time() * 1000)
    require(type(proof.get("observed_at_ms")) is int and 0 <= now - proof["observed_at_ms"] < 60000
            and proof.get("no_active_jobs") is True, "NATIVE_PREFLIGHT_STALE_OR_ACTIVE_JOB")
    require(type(pins.get("requested_at_ms")) is int and type(pins.get("expires_at_ms")) is int
            and pins["expires_at_ms"] - pins["requested_at_ms"] == 18000000
            and pins["requested_at_ms"] <= now and pins["expires_at_ms"] - now >= MIN_CANARY_REMAINING_MS,
            "EXACT_LIVE_60M_WINDOW_REQUIRED")
    require(args.authority_receipt and re.fullmatch(r"[a-f0-9]{64}", str(args.expected_authority_receipt_sha256)),
            "PINNED_R14_SAME_WINDOW_REOPEN_RECEIPT_REQUIRED")
    _, authority_raw, authority = read_json(args.authority_receipt)
    require(sha(authority_raw) == args.expected_authority_receipt_sha256 == pins.get("authority_receipt_sha256"),
            "AUTHORITY_RECEIPT_FILE_HASH_MISMATCH")
    rows = authority.get("public_receipts", [authority])
    require(isinstance(rows, list), "AUTHORITY_RECEIPT_INVALID")
    reopened = [row for row in rows if isinstance(row, dict) and row.get("ok") is True
                and row.get("phase") == "r14_same_window_read_only_observation" and row.get("next_phase") == "intake_reopened"]
    require(len(reopened) == 1, "EXACT_R14_REOPEN_RECEIPT_REQUIRED")
    receipt = reopened[0]
    target = {"host": "100.116.112.22", "service": "codex-control-plane.service", "admission": "scoped_pilot",
        "source_revision": "9cae104420e091811b94f76736a95e94ff333010be344eed7d1274f08601386c",
        "binding_id": "bind_3e05bf64cb3e4bab93d930ae1692bebb", "device_id": "72ceec2d-e3f2-472f-8e3c-99fffe053035",
        "workspace_id": "workspace_dda1d78e9a21402aa6213f72af64f788", "workspace_generation": "generation_c2f13e8d02344cf6a38a3f42ecfa59b6",
        "root": r"E:\Github\Tools-Codex-web", "profile": "web-mcp-assistant", "prior_pilot_revoked": True,
        "replacement_pilot_same_principal": True, "replacement_pilot_same_binding": True,
        "replacement_pilot_expires_at_ms": 1791776571067, "prior_pilot_id": "pilot_b1cb26c319fb489aae24d3b746318447"}
    require(all(receipt.get(field) == value for field, value in target.items())
            and re.fullmatch(r"call_[A-Za-z0-9_-]+", str(pins.get("approval_id")))
            and pins["approval_id"] not in {"call_a60e931056bd402b997c6c10b0796d81", "call_1KzUkF0gMn6uVpHd3QisTzXF"}
            and pins.get("context_id") == "ctx_1e7e2fec6f0e43018db7a51c6980e5c2"
            and pins.get("requested_at_ms") == 1791758571067 and pins.get("expires_at_ms") == 1791776571067
            and pins.get("pilot_id") != "pilot_b1cb26c319fb489aae24d3b746318447"
            and all(receipt.get(field) == pins.get(field) for field in
                    ("requested_at_ms", "expires_at_ms", "context_id", "pilot_id", "service_instance_id", "approval_id",
                     "activation_epoch", "runtime_instance_id", "mcp_server_instance_id", "contract_version"))
            and re.fullmatch(r"[a-f0-9]{64}", str(pins.get("authority_marker_sha256")))
            and receipt.get("next_marker_sha256") == pins["authority_marker_sha256"], "EXACT_R14_SAME_WINDOW_PINS_REQUIRED")
    _, _, frozen = read_json(HERE / "helper-manifest.json")
    records = {record["path"]: record for record in frozen["files"]}
    raw_payload = {}
    for name in ("r14_same_window_mcp_canary.py", "patch-envelope.txt"):
        raw = (HERE / name).read_bytes()
        require(name in records and sha(raw) == records[name]["sha256"]
                and len(raw) == records[name]["bytes"], "FROZEN_CANARY_ARTIFACT_CHANGED")
        raw_payload[name] = raw
    raw_payload["r11_common.py"] = COMMON_SOURCE.read_bytes()
    require(sha(raw_payload["r11_common.py"]) == COMMON_SHA, "FROZEN_COMMON_CHANGED")
    raw_payload["pins.json"], raw_payload["native-preflight.json"] = pins_raw, native_raw
    raw_payload["authority-receipt.json"] = authority_raw
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    remote = REMOTE_PARENT + "/r11-approved-" + timestamp
    expected = {name: {"sha256": sha(raw), "size_bytes": len(raw)} for name, raw in raw_payload.items()}
    binary = io.BytesIO()
    with tarfile.open(fileobj=binary, mode="w") as archive:
        for name, raw in sorted(raw_payload.items()):
            member = tarfile.TarInfo(name)
            member.size, member.mode = len(raw), 0o600
            archive.addfile(member, io.BytesIO(raw))
    packet_dir = HERE / ("prepared-" + timestamp)
    packet_dir.mkdir()
    bundle = binary.getvalue()
    freeze(packet_dir / "canary-bundle.tar", bundle)
    manifest = {"schema_version": 1, "prepared_at_utc": datetime.now(timezone.utc).isoformat(),
                "host": "100.116.112.22", "user": "svhome", "remote_dir": remote, "files": expected,
                "bundle_sha256": sha(bundle), "bundle_size_bytes": len(bundle),
                "root_ssh_sha256": SSH_HELPER_SHA, "root_canary_transport_sha256": sha(Path(__file__).read_bytes()),
                "pins_sha256": sha(pins_raw), "native_preflight_sha256": sha(native_raw),
                "native_preflight_observed_at_ms": proof["observed_at_ms"], "expires_at_ms": pins["expires_at_ms"]}
    freeze(packet_dir / "staging-manifest.json", canonical(manifest))
    return {"phase": "local_canary_bundle_prepared", "ok": True, "manifest_path": str(packet_dir / "staging-manifest.json"),
            "remote_dir": remote, "files": expected, "remote_mutation": False}


def manifest_packet(path):
    path, _, manifest = read_json(path)
    require(path.parent.parent == HERE and path.name == "staging-manifest.json"
            and re.fullmatch(r"prepared-[0-9TZ]+", path.parent.name), "STAGING_MANIFEST_NOT_OWNED")
    require(manifest.get("schema_version") == 1 and manifest.get("host") == "100.116.112.22"
            and manifest.get("user") == "svhome" and manifest.get("root_ssh_sha256") == SSH_HELPER_SHA
            and manifest.get("root_canary_transport_sha256") == sha(Path(__file__).read_bytes()), "STAGING_TRANSPORT_OR_TARGET_CHANGED")
    require(re.fullmatch(re.escape(REMOTE_PARENT) + r"/r11-approved-[0-9TZ]+", str(manifest.get("remote_dir"))), "REMOTE_DIRECTORY_NOT_APPROVED")
    require(set(manifest["files"]) == {"r11_common.py", "r14_same_window_mcp_canary.py", "patch-envelope.txt", "pins.json", "native-preflight.json", "authority-receipt.json"}
            and manifest["files"]["r11_common.py"]["sha256"] == COMMON_SHA
            and manifest["files"]["pins.json"]["sha256"] == manifest["pins_sha256"]
            and manifest["files"]["native-preflight.json"]["sha256"] == manifest["native_preflight_sha256"], "STAGING_MANIFEST_FIELDS_INVALID")
    return path.parent, manifest


def receipts(raw):
    require(len(raw) <= 1024 * 1024, "SSH_PUBLIC_OUTPUT_TOO_LARGE")
    result = []
    for line in raw.decode("utf-8").splitlines():
        value = json.loads(line)
        require(isinstance(value, dict) and isinstance(value.get("phase"), str), "SSH_PUBLIC_RECEIPT_INVALID")
        reject_private(value)
        result.append(value)
    require(result, "SSH_PUBLIC_RECEIPT_MISSING_UNCERTAIN_NO_RETRY")
    return result


def transport(args):
    require(args.execute and args.manifest, "ROOT_EXPLICIT_EXECUTION_AND_MANIFEST_REQUIRED")
    packet_dir, manifest = manifest_packet(args.manifest)
    pinned = fixed_module("r11_canary_pinned_ssh", SERVER / "root-ssh.py", SSH_HELPER_SHA)
    if args.action == "stage":
        binary = (packet_dir / "canary-bundle.tar").read_bytes()
        require(sha(binary) == manifest["bundle_sha256"] and len(binary) == manifest["bundle_size_bytes"], "LOCAL_STAGING_BUNDLE_CHANGED")
        require(0 <= int(time.time() * 1000) - manifest["native_preflight_observed_at_ms"] < 60000, "STAGING_NATIVE_PREFLIGHT_STALE")
        argv = ["/usr/bin/python3", "-B", "-c", pinned.STAGE, manifest["remote_dir"], json.dumps(manifest["files"], separators=(",", ":"))]
    else:
        require(args.action in PHASES, "REMOTE_PHASE_NOT_SUPPORTED")
        binary = b""
        argv = ["/usr/bin/python3", "-B", "-c", pinned.INVOKE, manifest["remote_dir"],
                json.dumps(manifest["files"], separators=(",", ":")), json.dumps(["r14_same_window_mcp_canary.py", args.action])]
    ssh = shutil.which("ssh")
    require(ssh is not None, "SSH_NOT_AVAILABLE")
    if args.action in {"stage", "dispatch", "cleanup"}:
        freeze(packet_dir / ("transport-intent-" + args.action + ".json"), canonical({"phase": args.action,
                "remote_dir": manifest["remote_dir"], "pins_sha256": manifest["pins_sha256"], "created_at_ms": int(time.time()*1000)}))
    try:
        result = subprocess.run([ssh, "-T", "-oBatchMode=yes", "-oStrictHostKeyChecking=yes", "-oConnectTimeout=15",
                                 "svhome@100.116.112.22", shlex.join(argv)], input=binary,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
    except Exception:
        raise Failure("SSH_TRANSPORT_UNCERTAIN_NO_RETRY") from None
    # Never print, persist or echo SSH stderr/raw stdout or command exceptions.
    public = receipts(result.stdout)
    record = {"phase": "root_canary_" + args.action, "ok": result.returncode == 0 and all(row.get("ok") is True for row in public),
              "action": args.action, "remote_dir": manifest["remote_dir"], "captured_at_utc": datetime.now(timezone.utc).isoformat(),
              "ssh_returncode": result.returncode, "public_receipts": public, "stderr_disclosed": False,
              "remote_mutation": args.action in {"stage", "dispatch", "cleanup"}, "replay_forbidden": True}
    directory = HERE / "remote-receipts"
    directory.mkdir(exist_ok=True)
    receipt_path = directory / (args.action + "-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".json")
    freeze(receipt_path, canonical(record))
    return {"receipt_path": str(receipt_path), **record}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "stage", "preflight", "dispatch", "observe", "cleanup"))
    parser.add_argument("--pins")
    parser.add_argument("--native-preflight")
    parser.add_argument("--expected-native-preflight-sha256")
    parser.add_argument("--authority-receipt")
    parser.add_argument("--expected-authority-receipt-sha256")
    parser.add_argument("--manifest")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    result = prepare(args) if args.action == "prepare" else transport(args)
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    if result.get("ok") is not True:
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"phase": "root_canary_transport_failed", "ok": False,
                          "code": getattr(error, "code", "ROOT_CANARY_TRANSPORT_FAILED"),
                          "stderr_disclosed": False, "replay_forbidden": True}, sort_keys=True))
        raise SystemExit(2) from None
