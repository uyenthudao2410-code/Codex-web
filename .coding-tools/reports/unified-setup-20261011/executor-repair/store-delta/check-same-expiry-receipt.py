"""AST-only receipt checks after adding source/grant pins; no live operation."""
import ast
import hashlib
import json
from pathlib import Path

base = Path(__file__).resolve().parent
helper = base / "ubuntu-r10-same-expiry-recovery-intake.py"
raw = helper.read_bytes()
compile(raw, str(helper), "exec")
tree = ast.parse(raw)
calls = [row for row in ast.walk(tree) if isinstance(row, ast.Call)
         and isinstance(row.func, ast.Subscript)
         and isinstance(row.func.value, ast.Name) and row.func.value.id == "g"
         and isinstance(row.func.slice, ast.Constant) and row.func.slice.value == "emit"
         and row.args and isinstance(row.args[0], ast.IfExp)]
assert len(calls) == 1
receipt = {item.arg: item.value for item in calls[0].keywords}
required = {
    "source_revision": 'g["REVISION"]',
    "package_source_sha256": 'g["PACKAGE"]',
    "service_grant_preserved": 'g["GRANT"]',
    "observed_at_ms": 'final_overview["observed_at_ms"]',
    "requested_at_ms": "REQUESTED",
    "expires_at_ms": "EXPIRY",
    "original_pilot_id": "PILOT",
    "authority_renewed": "False",
    "original_marker_modified": "False",
    "service_grant_changed": "False",
    "command_replayed": "False",
    "pending_acceptance_changed": "False",
}
for name, expression in required.items():
    assert ast.dump(receipt[name]) == ast.dump(ast.parse(expression, mode="eval").body), name
frozen = base / "ubuntu-r10-store-authority-v3-local-proof.py"
assert hashlib.sha256(frozen.read_bytes()).hexdigest() == "a312575854fee785158fa21624a096d7b09ae3701ded38f449a7330ba089ebec"
prior = json.loads((base / "r10-same-expiry-recovery-static-proof.json").read_text())
result = {
    "kind": "pure_same_expiry_recovery_final_receipt_proof",
    "helper_sha256": hashlib.sha256(raw).hexdigest(),
    "syntax_passed": True,
    "receipt_fields_verified": list(required),
    "prior_guard_proof": "r10-same-expiry-recovery-static-proof.json",
    "prior_guard_helper_sha256": prior["helper_sha256"],
    "prior_guard_positive_cases": prior["positive_cases"],
    "prior_guard_negative_cases": len(prior["negative_cases"]),
    "guard_cases_rerun": False,
    "v3_unchanged": True,
    "main_invoked": False,
    "live_operations": False,
}
with (base / "r10-same-expiry-recovery-final-proof.json").open("x", encoding="utf-8") as handle:
    json.dump(result, handle, indent=2)
    handle.write("\n")
manifest = json.loads((base / "r10-same-expiry-recovery-intake-manifest.json").read_text())
manifest.update(helper_sha256=result["helper_sha256"], supersedes_manifest="r10-same-expiry-recovery-intake-manifest.json",
                change="Add exact source, package and preserved grant to close/reopen receipts")
with (base / "r10-same-expiry-recovery-final-manifest.json").open("x", encoding="utf-8") as handle:
    json.dump(manifest, handle, indent=2)
    handle.write("\n")
print(json.dumps(result, separators=(",", ":")))
