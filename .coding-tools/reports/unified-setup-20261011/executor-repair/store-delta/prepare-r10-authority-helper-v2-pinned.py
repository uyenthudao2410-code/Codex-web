"""Pin pre-activation authority preparation to the observed r9 predecessor."""

import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


out = Path(__file__).resolve().parent
base = (out / "ubuntu-r10-store-authority-v2.py").read_bytes()
assert hashlib.sha256(base).hexdigest() == "86b52cb09148960760b13875b7ac8775ffeebc7eb27b72cb8bb8edf56bae3cb9"
base_manifest = json.loads((out / "r10-authority-helper-v2-manifest.json").read_bytes())
proof_bytes = (out.parent / "rollout-r9/server-intake-reopened.json").read_bytes()
proof = json.loads(proof_bytes)
predecessor = "activation-mv3qe36p-991f11f44f47d32ea2e217b1db882ff7"
assert proof["phase"] == "intake_reopened" and proof["ok"] is True
assert proof["source_revision"] == "5ce5c51fc97584501d5d091e8c21df88250f55eb42e6e756384b234da8837b1f"
assert proof["activation_epoch"] == predecessor and proof["binding_id"] == base_manifest["binding_id"]
assert proof["policy_assignment"]["device_id"] == base_manifest["device_id"]
assert proof["policy_assignment"]["workspace_id"] == base_manifest["workspace_id"]
assert proof["policy_assignment"]["workspace_generation"] == base_manifest["workspace_generation"]
helper = base.decode()


def once(before: str, after: str) -> None:
    global helper
    assert helper.count(before) == 1
    helper = helper.replace(before, after, 1)


once('prepare authority while the predecessor runtime remains alive.',
     'prepare authority only while the pinned r9 predecessor has a fresh heartbeat.')
once('OPERATION_DIR = HOME_DIR / ".local/state/codex-control-plane/owner-operations/r10-store395-60m-v2"',
     'OPERATION_DIR = HOME_DIR / ".local/state/codex-control-plane/owner-operations/r10-store395-60m-v2-pinned"\n'
     'PREDECESSOR_EPOCH = "' + predecessor + '"')
helper = helper.replace('owner_approved_r10_store395_same_scope_60m_v2', 'owner_approved_r10_store395_same_scope_60m_v2_pinned')
once('    require(arguments.expected_service_instance == health["service_instance_id"], "EXPECTED_SERVICE_INSTANCE_REQUIRED")\n',
     '    require(arguments.expected_service_instance == health["service_instance_id"], "EXPECTED_SERVICE_INSTANCE_REQUIRED")\n'
     '    if arguments.action in {"close", "renew"}:\n'
     '        nodes = [row for row in overview["nodes"] if row.get("device_id") == DEVICE]\n'
     '        require(arguments.expected_activation_epoch == PREDECESSOR_EPOCH and len(nodes) == 1\n'
     '                and nodes[0].get("activation_epoch") == PREDECESSOR_EPOCH\n'
     '                and 0 <= overview["observed_at_ms"] - nodes[0].get("last_seen_at_ms", 0) < 60000,\n'
     '                "EXPECTED_FRESH_R9_PREDECESSOR_REQUIRED_FOR_AUTHORITY_PREPARATION")\n'
     '    else:\n'
     '        require(arguments.expected_activation_epoch and arguments.expected_activation_epoch != PREDECESSOR_EPOCH,\n'
     '                "NEW_R10_ACTIVATION_REQUIRED_FOR_REOPEN")\n')
once('                "operator_approved": True,\n',
     '                "operator_approved": True, "predecessor_epoch": PREDECESSOR_EPOCH,\n')
once('            require(marker.get("operator_approved") is True, "OPERATOR_APPROVAL_MARKER_CHANGED")\n',
     '            require(marker.get("operator_approved") is True and marker.get("predecessor_epoch") == PREDECESSOR_EPOCH,\n'
     '                    "OPERATOR_APPROVAL_OR_PREDECESSOR_MARKER_CHANGED")\n')
ast.parse(helper)
with (out / "ubuntu-r10-store-authority-v2-pinned.py").open("xb") as handle:
    handle.write(helper.encode())
manifest = {**base_manifest, "operation": "guarded_r10_store_60m_authority_helper_v2_pinned_preparation",
            "captured_at_utc": datetime.now(timezone.utc).isoformat(), "helper_sha256": hashlib.sha256(helper.encode()).hexdigest(),
            "base_helper_sha256": hashlib.sha256(base).hexdigest(), "predecessor_epoch": predecessor,
            "r9_activation_proof_sha256": hashlib.sha256(proof_bytes).hexdigest(),
            "fresh_pinned_r9_epoch_and_heartbeat_required_at_close_renew": True,
            "activation_epoch_not_required_before_activation": False,
            "reopen_epoch_must_differ_from_predecessor": True, "remote_execution": False}
with (out / "r10-authority-helper-v2-pinned-manifest.json").open("xb") as handle:
    handle.write((json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode())
print(json.dumps(manifest, sort_keys=True, indent=2))
