"""Freeze the same approved authority flow with epoch validation at reopen.

The predecessor runtime can remain alive while the new context/pilot is
prepared. The r10 epoch must be freshly observed before reopening admission.
No remote operation is executed and prior helpers remain immutable.
"""

import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


out = Path(__file__).resolve().parent
base = (out / "ubuntu-r10-store-authority.py").read_bytes()
assert hashlib.sha256(base).hexdigest() == "2306b98d3187a43a1ae47599206e38f252a1d22a667dc43f2e39adbd8156c489"
manifest = json.loads((out / "r10-authority-helper-manifest.json").read_bytes())
helper = base.decode()


def once(before: str, after: str) -> None:
    global helper
    assert helper.count(before) == 1
    helper = helper.replace(before, after, 1)


once('fresh exact service/state/activation pins and the unchanged prior grant digest.',
     'fresh exact service/state pins and the unchanged prior grant digest. Reopen\nrequires the fresh r10 activation epoch and a ready node; close/renew can\nprepare authority while the predecessor runtime remains alive.')
once('OPERATION_DIR = HOME_DIR / ".local/state/codex-control-plane/owner-operations/r10-store395-60m"',
     'OPERATION_DIR = HOME_DIR / ".local/state/codex-control-plane/owner-operations/r10-store395-60m-v2"')
helper = helper.replace('owner_approved_r10_store395_same_scope_60m', 'owner_approved_r10_store395_same_scope_60m_v2')
once('    require(arguments.expected_activation_epoch, "EXPECTED_R10_ACTIVATION_REQUIRED")\n'
     '    nodes = [row for row in overview["nodes"] if row.get("device_id") == DEVICE]\n'
     '    require(len(nodes) == 1 and nodes[0].get("activation_epoch") == arguments.expected_activation_epoch\n'
     '            and 0 <= overview["observed_at_ms"] - nodes[0].get("last_seen_at_ms", 0) < 60000,\n'
     '            "R10_NODE_EPOCH_OR_FRESHNESS_CHANGED")\n', '')
once('            require(marker.get("operator_approved") is True and marker.get("activation_epoch") == arguments.expected_activation_epoch,\n'
     '                    "OPERATOR_APPROVAL_OR_ACTIVATION_MARKER_CHANGED")\n',
     '            require(marker.get("operator_approved") is True, "OPERATOR_APPROVAL_MARKER_CHANGED")\n')
once('                "operator_approved": True, "activation_epoch": arguments.expected_activation_epoch,\n',
     '                "operator_approved": True,\n')
once('            require(marker["phase"] in {"authority_renewed", "intake_reopened"}, "REOPEN_PHASE_CHANGED")\n',
     '            require(marker["phase"] in {"authority_renewed", "intake_reopened"}, "REOPEN_PHASE_CHANGED")\n'
     '            require(arguments.expected_activation_epoch and marker.get("activation_epoch") in {None, arguments.expected_activation_epoch},\n'
     '                    "EXPECTED_R10_ACTIVATION_OR_REOPEN_MARKER_CHANGED")\n')
ast.parse(helper)
with (out / "ubuntu-r10-store-authority-v2.py").open("xb") as handle:
    handle.write(helper.encode())
receipt = {**manifest, "operation": "guarded_r10_store_60m_authority_helper_v2_preparation",
           "captured_at_utc": datetime.now(timezone.utc).isoformat(), "helper_sha256": hashlib.sha256(helper.encode()).hexdigest(),
           "base_helper_sha256": hashlib.sha256(base).hexdigest(), "fresh_service_state_activation_pins_required": False,
           "fresh_service_state_pins_always_required": True, "fresh_r10_epoch_and_ready_node_required_at_reopen": True,
           "activation_epoch_not_required_before_activation": True, "prior_authority_helpers_preserved": True,
           "suggested_sequence": ["Store deployment leaves recovery", "observe", "close", "renew", "activate r10 and sync metadata policy", "observe", "reopen with fresh r10 epoch"],
           "remote_execution": False}
with (out / "r10-authority-helper-v2-manifest.json").open("xb") as handle:
    handle.write((json.dumps(receipt, sort_keys=True, indent=2) + "\n").encode())
print(json.dumps(receipt, sort_keys=True, indent=2))
