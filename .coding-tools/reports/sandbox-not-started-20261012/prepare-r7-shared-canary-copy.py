"""Copy reviewed r2 canary with only distinct r7 artifact/idempotency paths."""
import ast
import hashlib
import json
from pathlib import Path
import time

ROOT = Path(r"E:\DEV\Codex-web")
BASE = ROOT / ".coding-tools/reports/shared-write-exec-20261012"
DEST = ROOT / ".coding-tools/reports/shared-write-exec-20261012-r7"
old_target = b"new-machine-shared-write-proof-20261012.txt"
new_target = b"new-machine-shared-write-proof-20261012-r7.txt"
old_report = b"shared-write-exec-20261012/"
new_report = b"shared-write-exec-20261012-r7/"
recipes = {
    "run-shared-write-exec-canary-r2.py": (
        "run-shared-write-exec-canary-r7.py", "a0aa5b81df0c54b66c17cce0647121585ef297b7d16039f7a59ac90e555148f8",
        [(old_report, new_report, 1), (b"shared-write-exec-check-r2.cjs", b"shared-write-exec-check-r7.cjs", 1),
         (old_target, new_target, 1), (b"shared-write-exec-r2-20261012:", b"shared-write-exec-r7-20261012:", 1)]),
    "invoke-shared-write-exec-canary-r2.ps1": (
        "invoke-shared-write-exec-canary-r7.ps1", "8e41c719e42b9d7bfb714777cca44906ff22b6369798d5414f05b3d310828032",
        [(b"shared-write-exec-20261012'", b"shared-write-exec-20261012-r7'", 1),
         (b"run-shared-write-exec-canary-r2.py", b"run-shared-write-exec-canary-r7.py", 1),
         (b"shared-write-exec-receipt-r2-", b"shared-write-exec-receipt-r7-", 1), (old_target, new_target, 1)]),
    "shared-write-exec-check-r2.cjs": (
        "shared-write-exec-check-r7.cjs", "ba39e6aa6927711a1f85a3aa1df5fed5f72d594eea85ed7d1544c07b1bcabcc6",
        [(old_target, new_target, 1)])}

def sha(data): return hashlib.sha256(data).hexdigest()

assert not (ROOT / "tests/fixtures/new-machine-shared-write-proof-20261012-r7.txt").exists(), "SCRATCH_TARGET_ALREADY_EXISTS"
prepared = []
for source_name, (dest_name, expected, replacements) in recipes.items():
    original = (BASE / source_name).read_bytes()
    assert sha(original) == expected, "REVIEWED_SOURCE_CHANGED"
    assert not (DEST / dest_name).exists(), "ADDITIVE_TARGET_ALREADY_EXISTS"
    data = original
    for old, new, count in replacements:
        assert data.count(old) == count, "EXACT_REPLACEMENT_COUNT_CHANGED"
        data = data.replace(old, new)
    reversed_data = data
    for old, new, count in reversed(replacements):
        assert reversed_data.count(new) == count
        reversed_data = reversed_data.replace(new, old)
    assert reversed_data == original, "NON_PATH_BEHAVIOR_CHANGED"
    if dest_name.endswith(".py"): ast.parse(data.decode("utf-8-sig"))
    prepared.append((dest_name, data, {"source": str(BASE / source_name), "source_sha256": expected,
                                    "prepared": str(DEST / dest_name), "prepared_sha256": sha(data),
                                    "only_replacements": [{"old": old.decode(), "new": new.decode(), "count": count}
                                                          for old, new, count in replacements],
                                    "reverse_copy_exact_original": True}))
DEST.mkdir(exist_ok=True)
for name, data, metadata in prepared:
    with (DEST / name).open("xb") as output: output.write(data)
receipt = {"schema_version": 1, "operation": "prepare_additive_r7_shared_write_read_patch_read_exec_canary",
           "observed_at_ms": int(time.time() * 1000), "files": [metadata for name, data, metadata in prepared],
           "distinct_target": "tests/fixtures/new-machine-shared-write-proof-20261012-r7.txt",
           "distinct_idempotency_prefix": "shared-write-exec-r7-20261012:",
           "live_execution_identities": "required CLI arguments supplied by root after r7 READY",
           "mutation_guards": {"document_overwrite": False, "exact_one_attempt_per_lane": True,
                               "effect_unknown_preserves_task_writer": True, "no_action_replay": True,
                               "exact_preimage_postimage_hashes": True, "cleanup_verified": True},
           "canary_executed": False, "runtime_jobs_started": False, "remote_system_changed": False,
           "prior_reviewed_controller_behavior_preserved_byte_for_byte_except_paths": True}
receipt_path = DEST / "r7-canary-copy-preparation.json"
with receipt_path.open("x", encoding="utf-8", newline="\n") as output:
    json.dump(receipt, output, indent=2); output.write("\n")
print(json.dumps({"ok": True, "files": receipt["files"], "receipt": str(receipt_path),
                  "receipt_sha256": sha(receipt_path.read_bytes()), "canary_executed": False}))
