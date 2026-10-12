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
SERVER = HERE.parent / "activation-server"
SSH_HELPER_SHA = "d6aa00d14128b8905e0edb92df24a02eeb9867a3a032a53f41d8375b023d39ba"
COMMON_SHA = "c55d9d07144654ca0216d55c8de8b20c1a238a9a722ac455d6c83ec0d406e36f"
NATIVE_SHA = "0e4733844a471814a3a6240fa9c0423b56195ab80f6e5283b5c978e28edaaed4"
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
            and pins.get("native_tool_contract_sha256") == NATIVE_SHA, "R11_NATIVE_CONTRACT_PIN_REQUIRED")
    proof = pins.get("native_preflight")
    require(isinstance(proof, dict) and proof.get("receipt_sha256") == sha(native_raw), "NATIVE_RECEIPT_PIN_MISMATCH")
    native_fields = native.get("native_preflight", native)
    require(isinstance(native_fields, dict)
            and all(native_fields.get(key) == value for key, value in proof.items() if key != "receipt_sha256"), "NATIVE_RECEIPT_FIELDS_MISMATCH")
    now = int(time.time() * 1000)
    require(type(proof.get("observed_at_ms")) is int and 0 <= now - proof["observed_at_ms"] < 60000
            and proof.get("no_active_jobs") is True, "NATIVE_PREFLIGHT_STALE_OR_ACTIVE_JOB")
    require(type(pins.get("requested_at_ms")) is int and type(pins.get("expires_at_ms")) is int
            and pins["expires_at_ms"] - pins["requested_at_ms"] == 3600000
            and pins["requested_at_ms"] <= now < pins["expires_at_ms"] - 120000, "EXACT_LIVE_60M_WINDOW_REQUIRED")
    require(pins["requested_at_ms"] == 1791735729910 and pins["expires_at_ms"] == 1791739329910
            and pins.get("context_id") == "ctx_71ae5c01e2de4df6874d401263a310c0"
            and pins.get("pilot_id") == "pilot_b294f82a6cf64b098268322b9106d8c7", "EXACT_NEW_AUTHORITY_PINS_REQUIRED")
    _, _, frozen = read_json(HERE / "helper-manifest.json")
    records = {record["path"]: record for record in frozen["files"]}
    raw_payload = {}
    for name in ("r11_mcp_canary.py", "patch-envelope.txt"):
        raw = (HERE / name).read_bytes()
        require(name in records and sha(raw) == records[name]["sha256"]
                and len(raw) == records[name]["bytes"], "FROZEN_CANARY_ARTIFACT_CHANGED")
        raw_payload[name] = raw
    raw_payload["r11_common.py"] = (SERVER / "r11_common.py").read_bytes()
    require(sha(raw_payload["r11_common.py"]) == COMMON_SHA, "FROZEN_COMMON_CHANGED")
    raw_payload["pins.json"], raw_payload["native-preflight.json"] = pins_raw, native_raw
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
    require(set(manifest["files"]) == {"r11_common.py", "r11_mcp_canary.py", "patch-envelope.txt", "pins.json", "native-preflight.json"}
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
                json.dumps(manifest["files"], separators=(",", ":")), json.dumps(["r11_mcp_canary.py", args.action])]
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
