"""Prepare an immutable v3 helper from the pinned v2; never call a service."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = ROOT / "ubuntu-r10-store-authority-v2-pinned.py"
DEST = ROOT / "ubuntu-r10-store-authority-v3-local-proof.py"
BASE_SHA = "ab182f47b605e5edac1e30cb9cdf48ca53a571f0cbb5367a0f6fb837cbe0c9af"
raw = BASE.read_bytes()
assert hashlib.sha256(raw).hexdigest() == BASE_SHA, "V2_SOURCE_CHANGED"
source = raw.decode("utf-8").replace("\r\n", "\n")
source = source.replace("from __future__ import annotations\n", "from __future__ import annotations\n\nimport sys\nfrom datetime import datetime\n", 1)
source = source.replace("prepare authority only while the pinned r9 predecessor has a fresh heartbeat.",
    "prepare authority from a fresh owner-transmitted, independently pinned local r9 proof.\nA stale/unreported central predecessor is never relabeled ready, and no old agent is started.")
source = source.replace("r10-store395-60m-v2-pinned", "r10-store395-60m-v3-local-proof")
source = source.replace("owner_approved_r10_store395_same_scope_60m_v2_pinned", "owner_approved_r10_store395_same_scope_60m_v3_local_proof")
validation = r'''

LOCAL_ROOT = r"E:\Github\Tools-Codex-web"
LOCAL_HEAD = "2c554f59cb7b8ffc86ce5e0e28076c792777642f"
LOCAL_PARITY = "c9f6fe1313b6004519a61bebf3f8f173a74cfd1d563bef48fce87908ed72f57c"
LOCAL_PACKAGE = {"archive_sha256": "3bc75601041ef35b9fd894878b9f1905117512e3fc6f74d6102575b0f1edb226",
                 "executable_sha256": "fadc2feb4bb566b3fa22f22ea918c7175f39fa6b74eb7ccb9d2a1d6bab1b6211"}
LOCAL_DESCRIPTOR = {"installation_id": "e65d60602938af2f1c6e8cd9e8c59352ff2a5e24a268a45a98114726cdd8210d",
    "instance_id": "6006092b7a061f47b20a0b27c1f34f1d", "owner_pid": 1128,
    "owner_process_start_token": "134361911908524600"}
LOCAL_PROCESSES = {"owner": {"pid": 1128, "process_start_token": "134361911908524600"},
    "ui": {"pid": 25296, "process_start_token": "134361911886531150"},
    "native": {"pid": 9212, "process_start_token": "134361911931895600"}}
LOCAL_PENDING = {"run_id": "95e909f0040a448faa9f1f3257e2ee2c", "wave_id": "c101beadfc6d4f2fbc13845052c84693",
    "run_record_sha256": "a167681ee42f25bc76a6eb03f63dfd91ef382924573205835f07d5ab01eef590",
    "wave_record_sha256": "59d351b7afbc33b8e8f8f2f35bf5dfdd1c8a319bab93dd005481f4df36862bce", "unchanged": True}
LOCAL_DURABLE = {"activation_epoch_id": PREDECESSOR_EPOCH,
    "operation_id": "full-clean-mv3qdvfq-a83d4dacc8a5de0588fb6ba5", "state": "READY", "admission_state": "OPEN",
    "ready_commit_digest": "f85415b88bd6b9b1442a40fbb308d69d6aa4d7e0a8c9ee690a86ef5a5f22fe3e"}
LOCAL_RAW_EPOCH = {**{key: value for key, value in LOCAL_DURABLE.items() if key != "admission_state"},
                   "admission_open": True, "update_incomplete": False}
LOCAL_POLICY_HASHES = {"file_read": "62bd90f00fc6ab196afe07ddea82996a22a2686cd82e7d3c83c12914f99df6e6",
    "approved_patch": "3e78ebb89ab90ef2b33964d922bd1294c17fd741c218322cf4efb4ee7f574d2b",
    "exec": "31125fd75f5147770eecde7b926e3c46efd1f5ee83a55b58d180f8b200966367"}
LOCAL_ARGV_HASH = "6c67e3aa54d9dae49c41feff2d2b5c56100760b60cdef6a2a4eca392d9063597"
OTHER_VARIANT_MARKERS = tuple(HOME_DIR / ".local/state/codex-control-plane/owner-operations" / name / "authority-renewal-public.json"
    for name in ("r10-store395-60m-v2-pinned", "r10-store395-60m-v2", "r10-store395-60m"))


def partial_exact(value: object, expected: dict, code: str) -> None:
    require(isinstance(value, dict) and all(type(value.get(key)) is type(item) and value.get(key) == item
            for key, item in expected.items()), code)


def validate_local_preparation(raw: bytes, expected_sha: object, *, now_ms: int) -> dict:
    require(isinstance(expected_sha, str) and re.fullmatch(r"[a-f0-9]{64}", expected_sha) is not None,
            "EXPECTED_LOCAL_PREPARATION_SHA256_REQUIRED")
    require(0 < len(raw) <= 131072 and hashlib.sha256(raw).hexdigest() == expected_sha,
            "LOCAL_PREPARATION_BYTES_CHANGED")
    try:
        proof = json.loads(raw)
        require(isinstance(proof, dict), "LOCAL_PREPARATION_SCHEMA_INVALID")
        timestamp = str(proof.get("observed_at") or "")
        require(timestamp.endswith("Z"), "LOCAL_PREPARATION_TIMESTAMP_INVALID")
        observed = int(datetime.fromisoformat(timestamp.replace("Z", "+00:00")).timestamp() * 1000)
    except (ValueError, TypeError, OverflowError):
        raise GuardFailure("LOCAL_PREPARATION_SCHEMA_INVALID") from None
    require(0 <= now_ms - observed < 60000, "LOCAL_PREPARATION_NOT_FRESH")
    partial_exact(proof, {"kind": "r9_local_authority_preparation_v1", "schema_version": 1,
        "repository_head": LOCAL_HEAD, "parity_sha256": LOCAL_PARITY,
        "runtime_mutated": False, "server_mutated": False, "sandbox_probe_performed": False},
        "LOCAL_PREPARATION_SCHEMA_OR_SOURCE_CHANGED")
    partial_exact(proof.get("target"), {"binding_id": BINDING, "device_id": DEVICE, "workspace_id": WORKSPACE,
        "workspace_generation": GENERATION, "root": LOCAL_ROOT, "profile": "web-mcp-assistant"}, "LOCAL_TARGET_CHANGED")
    partial_exact((proof.get("packages") or {}).get("r9"), LOCAL_PACKAGE, "LOCAL_PACKAGE_CHANGED")
    partial_exact(proof.get("descriptor"), LOCAL_DESCRIPTOR, "LOCAL_DESCRIPTOR_CHANGED")
    for role, expected in LOCAL_PROCESSES.items():
        partial_exact(proof.get(role), {**expected, "state": "live"}, "LOCAL_" + role.upper() + "_IDENTITY_CHANGED")
    require(proof.get("ui_instance_id") == "2d80b88288e54bcc40f86f6ad45adcf6", "LOCAL_UI_INSTANCE_CHANGED")
    partial_exact(proof.get("agent"), {"state": "absent", "pid": 7108}, "OLD_AGENT_MUST_REMAIN_ABSENT")
    partial_exact(proof.get("durable"), LOCAL_DURABLE, "LOCAL_DURABLE_READY_CHANGED")
    partial_exact(proof.get("raw_epoch"), LOCAL_RAW_EPOCH, "LOCAL_RAW_EPOCH_CHANGED")
    partial_exact(proof.get("pending_acceptance"), LOCAL_PENDING, "LOCAL_PENDING_ACCEPTANCE_CHANGED")
    policies = proof.get("policies")
    require(isinstance(policies, dict) and policies.get("workspace_root_verified") is True
            and policies.get("standalone_probe_performed") is False, "LOCAL_POLICY_OBSERVATION_INVALID")
    for role, policy_hash in LOCAL_POLICY_HASHES.items():
        partial_exact(policies.get(role), {"state": "enabled", "enabled": True, "workspace_id": WORKSPACE,
            "workspace_generation": GENERATION, "policy_sha256": policy_hash}, "LOCAL_STANDING_POLICY_CHANGED")
    partial_exact(policies.get("exec"), {"allowed_argv_prefix_count": 6,
        "allowed_argv_prefixes_sha256": LOCAL_ARGV_HASH}, "LOCAL_EXEC_ALLOWLIST_CHANGED")
    census = proof.get("census")
    require(isinstance(census, dict) and census.get("ledger_mutated") is False
            and census.get("content_free") is True, "LOCAL_CENSUS_INVALID")
    partial_exact(census.get("counts"), {key: 0 for key in ("active_tool_calls", "active_commands", "starting_commands",
        "active_background_operations", "active_managed_processes", "foreign_heavy_processes", "active_agent_lanes")},
        "LOCAL_ACTIVE_JOB_OR_LANE")
    partial_exact(census.get("lifecycle"), {"unexplained_active_runs": 0, "unbound_live_resource_residues": 0,
        "projection_drift": False, "awaiting_acceptance_runs": [LOCAL_PENDING["run_id"]],
        "live_owned_runs": [], "active_p5_runs": [], "blockers": ["live_runtime_state_process"]}, "LOCAL_LIFECYCLE_CHANGED")
    partial_exact(census, {"safe": False, "code": "RUNTIME_BUSY", "reason": "live_runtime_state_process"},
        "LOCAL_CENSUS_BOUNDARY_CHANGED")
    require((census.get("snapshot") or {}).get("integrity_check") == ["ok"]
            and re.fullmatch(r"[a-f0-9]{64}", str((census.get("snapshot") or {}).get("logical_sha256") or "")) is not None,
            "LOCAL_LEDGER_INTEGRITY_INVALID")
    vm = proof.get("vm_zero_proof")
    partial_exact(vm, {"phase": "independent_vm_zero_proof", "ok": True,
        "vm_termination_performed": False, "sandbox_probe_performed": False}, "LOCAL_VM_ZERO_PROOF_INVALID")
    for role, observer in (("host", "GetProcessWindowsSandbox"), ("daemon", "CimMxcBackend")):
        row = vm.get(role)
        partial_exact(row, {"observer": observer, "count": 0, "content_free": True}, "LOCAL_VM_NOT_ZERO")
        require(type(row.get("begun_at_ms")) is int and type(row.get("observed_at_ms")) is int
                and 0 <= now_ms - row["observed_at_ms"] < 60000
                and row["begun_at_ms"] <= row["observed_at_ms"] <= observed,
                "LOCAL_VM_ZERO_OBSERVATION_NOT_FRESH")
    return {"sha256": expected_sha, "observed_at_ms": observed, "proof": proof}


def persist_local_preparation(raw: bytes, preparation: dict) -> None:
    destination = OPERATION_DIR / ("local-preparation-" + preparation["sha256"] + ".json")
    if destination.exists():
        require(protected_file(destination) == raw, "LOCAL_PROOF_ARCHIVE_CHANGED")
        return
    descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
'''
source = source.replace("\ndef main() -> None:\n", validation + "\n\ndef main() -> None:\n", 1)
source = source.replace('    parser.add_argument("--expected-activation-epoch")\n',
    '    parser.add_argument("--expected-activation-epoch")\n    parser.add_argument("--local-preparation-stdin", action="store_true")\n    parser.add_argument("--expected-local-preparation-sha256")\n', 1)
old_guard = '''    if arguments.action in {"close", "renew"}:
        nodes = [row for row in overview["nodes"] if row.get("device_id") == DEVICE]
        require(arguments.expected_activation_epoch == PREDECESSOR_EPOCH and len(nodes) == 1
                and nodes[0].get("activation_epoch") == PREDECESSOR_EPOCH
                and 0 <= overview["observed_at_ms"] - nodes[0].get("last_seen_at_ms", 0) < 60000,
                "EXPECTED_FRESH_R9_PREDECESSOR_REQUIRED_FOR_AUTHORITY_PREPARATION")
'''
new_guard = '''    local_preparation = None
    local_preparation_raw = b""
    if arguments.action in {"close", "renew"}:
        require(arguments.expected_activation_epoch == PREDECESSOR_EPOCH and arguments.local_preparation_stdin,
                "EXACT_LOCAL_R9_PREPARATION_REQUIRED")
        local_preparation_raw = sys.stdin.buffer.read(131073)
        local_preparation = validate_local_preparation(local_preparation_raw,
            arguments.expected_local_preparation_sha256, now_ms=int(time.time() * 1000))
'''
assert source.count(old_guard) == 1, "PREDECESSOR_GUARD_CHANGED"
source = source.replace(old_guard, new_guard, 1)
source = source.replace('            require(arguments.action == "close", "CLOSE_PREPARATION_REQUIRED")\n',
    '            require(arguments.action == "close", "CLOSE_PREPARATION_REQUIRED")\n            require(not any(path.exists() for path in OTHER_VARIANT_MARKERS), "OTHER_VARIANT_MARKER_EXISTS_DO_NOT_REANCHOR")\n', 1)
anchor = '        if arguments.action == "close":\n'
assert source.count(anchor) == 1
source = source.replace(anchor, '''        if local_preparation is not None:
            require(0 <= int(time.time() * 1000) - local_preparation["observed_at_ms"] < 60000,
                    "LOCAL_PREPARATION_EXPIRED_BEFORE_OWNER_MUTATION")
            persist_local_preparation(local_preparation_raw, local_preparation)
            if "initial_local_preparation_sha256" not in marker:
                marker["initial_local_preparation_sha256"] = local_preparation["sha256"]
            marker["local_preparation_sha256"] = local_preparation["sha256"]
            marker["local_preparation_observed_at_ms"] = local_preparation["observed_at_ms"]
            save(marker)
        if arguments.action == "close":
''', 1)
source = source.replace('             context_id=marker.get("context_id"), pilot_id=marker.get("pilot_id"), duration_ms=3600000,\n',
    '             context_id=marker.get("context_id"), pilot_id=marker.get("pilot_id"), duration_ms=3600000,\n             local_preparation_sha256=marker.get("local_preparation_sha256"),\n             local_preparation_observed_at_ms=marker.get("local_preparation_observed_at_ms"),\n             initial_local_preparation_sha256=marker.get("initial_local_preparation_sha256"),\n', 1)
compile(source, str(DEST), "exec")
with DEST.open("xb") as handle:
    handle.write(source.encode("utf-8"))
manifest = {"kind": "immutable_r10_store_authority_v3_local_proof", "base_helper": BASE.name,
    "base_sha256": BASE_SHA, "helper": DEST.name, "helper_sha256": hashlib.sha256(DEST.read_bytes()).hexdigest(),
    "prepared_only": True, "runtime_executed": False, "authority_mutated": False,
    "scope": "same existing Tools-Codex-web target/grant; one 60-minute renewal; reopen fresh r10 only",
    "input": {"transport": "exact raw proof bytes on stdin", "max_bytes": 131072,
        "hash_argument": "--expected-local-preparation-sha256", "freshness_ms": 60000},
    "unchanged": "v2 source/Store package/service/source/quarantine/full action families/grant/reopen/window routines"}
with (ROOT / "r10-authority-v3-local-proof-manifest.json").open("x", encoding="utf-8", newline="\n") as handle:
    json.dump(manifest, handle, indent=2)
    handle.write("\n")
print(json.dumps(manifest, separators=(",", ":")))
