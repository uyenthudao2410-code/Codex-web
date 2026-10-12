"""Execute only the pure v3 proof validator locally, with no service/SQL calls."""
from __future__ import annotations
import ast
import copy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
HELPER = ROOT / "ubuntu-r10-store-authority-v3-local-proof.py"
PROOF = ROOT.parent / "candidate-r10/activation/server-preparation-proof-20261011T123902944Z.json"
module = ast.parse(HELPER.read_text(encoding="utf-8"))
names = {"HOST", "USER", "SERVICE", "REVISION", "PACKAGE", "SCHEMA", "HOME_DIR", "PREDECESSOR_EPOCH",
    "BINDING", "DEVICE", "WORKSPACE", "GENERATION", "LOCAL_ROOT", "LOCAL_HEAD", "LOCAL_PARITY", "LOCAL_PACKAGE",
    "LOCAL_DESCRIPTOR", "LOCAL_PROCESSES", "LOCAL_PENDING", "LOCAL_DURABLE", "LOCAL_RAW_EPOCH", "LOCAL_POLICY_HASHES", "LOCAL_ARGV_HASH"}
functions = {"require", "partial_exact", "validate_local_preparation"}
selected = [row for row in module.body if isinstance(row, ast.ClassDef) and row.name == "GuardFailure"
    or isinstance(row, ast.FunctionDef) and row.name in functions
    or isinstance(row, ast.Assign) and len(row.targets) == 1 and isinstance(row.targets[0], ast.Name) and row.targets[0].id in names]
namespace = {"Path": Path, "datetime": datetime, "json": json, "re": re, "hashlib": hashlib}
exec(compile(ast.Module(body=selected, type_ignores=[]), str(HELPER), "exec"), namespace)
raw = PROOF.read_bytes()
proof = json.loads(raw)
observed = int(datetime.fromisoformat(proof["observed_at"].replace("Z", "+00:00")).timestamp() * 1000)
validate = namespace["validate_local_preparation"]
sha = hashlib.sha256(raw).hexdigest()
validate(raw, sha, now_ms=observed + 500)
cases = []

def reject(name, mutation, expected):
    sample = copy.deepcopy(proof)
    mutation(sample)
    material = json.dumps(sample, separators=(",", ":")).encode()
    try:
        validate(material, hashlib.sha256(material).hexdigest(), now_ms=observed + 500)
    except namespace["GuardFailure"] as error:
        assert error.code == expected, (name, error.code, expected)
        cases.append({"name": name, "code": error.code, "passed": True})
        return
    raise AssertionError(name + " WAS NOT REJECTED")

reject("wrong_target", lambda row: row["target"].update(binding_id="bind_wrong"), "LOCAL_TARGET_CHANGED")
reject("wrong_package", lambda row: row["packages"]["r9"].update(archive_sha256="0" * 64), "LOCAL_PACKAGE_CHANGED")
reject("host_pid_reuse", lambda row: row["owner"].update(process_start_token="1"), "LOCAL_OWNER_IDENTITY_CHANGED")
reject("durable_ready_closed", lambda row: row["durable"].update(admission_state="CLOSED"), "LOCAL_DURABLE_READY_CHANGED")
reject("raw_epoch_incomplete", lambda row: row["raw_epoch"].update(update_incomplete=True), "LOCAL_RAW_EPOCH_CHANGED")
reject("old_agent_restart", lambda row: row["agent"].update(state="live"), "OLD_AGENT_MUST_REMAIN_ABSENT")
reject("pending_wave_changed", lambda row: row["pending_acceptance"].update(wave_record_sha256="0" * 64), "LOCAL_PENDING_ACCEPTANCE_CHANGED")
reject("active_job", lambda row: row["census"]["counts"].update(active_managed_processes=1), "LOCAL_ACTIVE_JOB_OR_LANE")
reject("sandbox_present", lambda row: row["vm_zero_proof"]["host"].update(count=1), "LOCAL_VM_NOT_ZERO")
reject("exec_allowlist_changed", lambda row: row["policies"]["exec"].update(allowed_argv_prefixes_sha256="0" * 64), "LOCAL_EXEC_ALLOWLIST_CHANGED")
for name, material, expected_sha, now, code in (
    ("bad_raw_hash", raw, "0" * 64, observed + 500, "LOCAL_PREPARATION_BYTES_CHANGED"),
    ("stale_local_proof", raw, sha, observed + 60000, "LOCAL_PREPARATION_NOT_FRESH"),
    ("future_local_proof", raw, sha, observed - 1, "LOCAL_PREPARATION_NOT_FRESH"),
):
    try:
        validate(material, expected_sha, now_ms=now)
    except namespace["GuardFailure"] as error:
        assert error.code == code, (name, error.code, code)
        cases.append({"name": name, "code": error.code, "passed": True})
    else:
        raise AssertionError(name + " WAS NOT REJECTED")

parent = ROOT / "ubuntu-r10-store-authority-v2-pinned.py"
assert hashlib.sha256(parent.read_bytes()).hexdigest() == "ab182f47b605e5edac1e30cb9cdf48ca53a571f0cbb5367a0f6fb837cbe0c9af"
result = {"kind": "pure_v3_local_preparation_guard_verification", "helper_sha256": hashlib.sha256(HELPER.read_bytes()).hexdigest(),
    "proof_fixture_sha256": sha, "positive": "genuine emitted schema accepted at synthetic fresh time", "negative_cases": cases,
    "production_source_modified": False, "runtime_executed": False, "authority_mutated": False,
    "v2_unchanged": True, "syntax_passed": True, "case_count": len(cases) + 1}
with (ROOT / "r10-authority-v3-guard-verification.json").open("x", encoding="utf-8", newline="\n") as handle:
    json.dump(result, handle, indent=2)
    handle.write("\n")
print(json.dumps(result, separators=(",", ":")))
