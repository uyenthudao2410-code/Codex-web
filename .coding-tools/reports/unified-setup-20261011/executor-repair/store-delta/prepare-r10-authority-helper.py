"""Freeze a separately approved r10 + Store 60-minute authority helper.

Preparation is local-only and depends exclusively on frozen artifacts.
"""

import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


out = Path(__file__).resolve().parent
packet_bytes = (out / "packet-manifest.json").read_bytes()
packet = json.loads(packet_bytes)
assert packet["source_revision"] == "395c7868931729249e66654132c8734a404c22cfa6c74a85f3cc7fdc56e5d4d5"
assert packet["package_source_sha256"] == "sha256:83611914241508ad1f5ca96d017902cb6675fa15ea082f3aa4698f7cffe74419"
release_manifest = out / packet["release_name"] / "release-manifest.json"
assert hashlib.sha256(release_manifest.read_bytes()).hexdigest() == packet["manifest_sha256"]
base = (out.parent / "rollout-r9/ubuntu-r9-authority.py").read_bytes()
assert hashlib.sha256(base).hexdigest() == "c86ff98e315651225a9f125132ce4ac4c84fe64a537d3021971d5333c9abf869"
helper = base.decode()


def once(before: str, after: str) -> None:
    global helper
    assert helper.count(before) == 1, "frozen base helper substitution mismatch"
    helper = helper.replace(before, after, 1)


once('REVISION = "5ce5c51fc97584501d5d091e8c21df88250f55eb42e6e756384b234da8837b1f"',
     'REVISION = "' + packet["source_revision"] + '"')
once('PACKAGE = "sha256:bb529f710342bf064fb5d2259ab1ad49e3733a6ca6db0c60b60ed67f119a7566"',
     'PACKAGE = "' + packet["package_source_sha256"] + '"')
once('OPERATION_DIR = HOME_DIR / ".local/state/codex-control-plane/owner-operations/rollout-r9"',
     'OPERATION_DIR = HOME_DIR / ".local/state/codex-control-plane/owner-operations/r10-store395-60m"\n'
     'PRIOR_R9_MARKER = HOME_DIR / ".local/state/codex-control-plane/owner-operations/rollout-r9/authority-renewal-public.json"\n'
     'PRIOR_CONTEXT = "ctx_655e717e5c634cc1922d0f0d2e9d33c6"')
once('REASON = "Owner-approved Windows r9 activation: same Tools-Codex-web read/write/sandboxed exec scope for 60 minutes"',
     'REASON = "Owner-approved Windows r10 activation and Store395 deployment: same exact Tools-Codex-web read/write/sandboxed exec scope for one 60-minute window"')
helper = helper.replace("owner_approved_r9_same_scope_60m", "owner_approved_r10_store395_same_scope_60m")
helper = helper.replace("r9_read_only_preflight", "r10_store_read_only_preflight")
helper = helper.replace("r9_guarded_operation_failed", "r10_store_guarded_operation_failed")
helper = helper.replace("EXPECTED_R9_ACTIVATION_REQUIRED", "EXPECTED_R10_ACTIVATION_REQUIRED")
helper = helper.replace("R9_NODE_NOT_FRESH_READY", "R10_NODE_NOT_FRESH_READY")
helper = helper.replace("R9_OPERATION_FAILED", "R10_STORE_OPERATION_FAILED")
old_doc = helper[:helper.index("from __future__")]
new_doc = '''"""Pending-approval r10 + Store395 exact-scope authority helper.

Default/observe is read-only. Mutations require --execute, --operator-approved,
fresh exact service/state/activation pins and the unchanged prior grant digest.
One protected operation marker anchors exactly one 60-minute context/pilot
window at the first renewal; retries never extend it or create duplicates.
Only supported owner APIs close the prior owner context, revoke prior pilots,
create one replacement context/pilot, and reopen scoped_pilot. No deployment,
restart, SQL data writes, local standing-policy changes, standalone Sandbox
probe, command replay, pending RUN acceptance, or credential output occurs.
"""

'''
once(old_doc, new_doc)
tables = ("work_requests", "actions", "delivery_attempts", "receipts", "action_reconciliations",
          "action_dispatch_dispositions", "mcp_task_sessions", "mcp_task_writer_leases",
          "mcp_patch_acceptances", "mcp_file_read_intents", "mcp_approved_patch_intents",
          "mcp_standing_patch_intents", "mcp_exec_intents", "mcp_artifact_intents",
          "mcp_document_write_intents", "mcp_read_only_intents")
fingerprint = '        protected_tables = ' + repr(tables) + '\n'
fingerprint += '        protected_rows = {table: [dict(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY rowid")] for table in protected_tables}\n'
fingerprint += '        result["all_action_task_intent_families_sha256"] = digest(protected_rows)\n'
once('        result["historical_action_families_sha256"] = digest(families)\n',
     '        result["historical_action_families_sha256"] = digest(families)\n' + fingerprint)
once('    parser.add_argument("--execute", action="store_true")\n',
     '    parser.add_argument("--execute", action="store_true")\n'
     '    parser.add_argument("--operator-approved", action="store_true")\n')
once('    require(arguments.expected_service_instance == health["service_instance_id"], "EXPECTED_SERVICE_INSTANCE_REQUIRED")\n',
     '    require(arguments.operator_approved, "EXPLICIT_R10_STORE_60M_OWNER_APPROVAL_REQUIRED")\n'
     '    require(arguments.expected_service_instance == health["service_instance_id"], "EXPECTED_SERVICE_INSTANCE_REQUIRED")\n'
     '    require(arguments.expected_activation_epoch, "EXPECTED_R10_ACTIVATION_REQUIRED")\n'
     '    nodes = [row for row in overview["nodes"] if row.get("device_id") == DEVICE]\n'
     '    require(len(nodes) == 1 and nodes[0].get("activation_epoch") == arguments.expected_activation_epoch\n'
     '            and 0 <= overview["observed_at_ms"] - nodes[0].get("last_seen_at_ms", 0) < 60000,\n'
     '            "R10_NODE_EPOCH_OR_FRESHNESS_CHANGED")\n'
     '    prior_r9 = json.loads(protected_file(PRIOR_R9_MARKER))\n'
     '    require(prior_r9.get("operation") == "owner_approved_r9_same_scope_60m"\n'
     '            and prior_r9.get("binding_id") == BINDING and prior_r9.get("device_id") == DEVICE\n'
     '            and prior_r9.get("workspace_id") == WORKSPACE and prior_r9.get("workspace_generation") == GENERATION\n'
     '            and prior_r9.get("context_id") == PRIOR_CONTEXT and prior_r9.get("service_grant_sha256") == digest(grant),\n'
     '            "EXISTING_R9_SCOPE_OR_GRANT_CHANGED")\n')
once('            require(arguments.action == "close", "CLOSE_PREPARATION_REQUIRED")\n',
     '            require(arguments.action == "close", "CLOSE_PREPARATION_REQUIRED")\n'
     '            unclosed_contexts = [row for row in overview["contexts"] if row.get("binding_id") == BINDING\n'
     '                                and row.get("closed_at_ms") is None]\n'
     '            require(all(row.get("context_id") == PRIOR_CONTEXT for row in unclosed_contexts),\n'
     '                    "UNEXPECTED_UNCLOSED_CONTEXTS_BLOCK_AUTHORITY_RENEWAL")\n')
once('                "reason": REASON, "service_instance_id": health["service_instance_id"], "initial_state": snapshot,\n',
     '                "reason": REASON, "service_instance_id": health["service_instance_id"], "initial_state": snapshot,\n'
     '                "operator_approved": True, "activation_epoch": arguments.expected_activation_epoch,\n')
once('            marker_identity(marker, health, snapshot, grant)\n',
     '            marker_identity(marker, health, snapshot, grant)\n'
     '            require(marker.get("operator_approved") is True and marker.get("activation_epoch") == arguments.expected_activation_epoch,\n'
     '                    "OPERATOR_APPROVAL_OR_ACTIVATION_MARKER_CHANGED")\n')
once('                "old_context_ids": [row["context_id"] for row in overview["contexts"] if row.get("binding_id") == BINDING\n'
     '                                    and row.get("closed_at_ms") is None],\n',
     '                "old_context_ids": [row["context_id"] for row in overview["contexts"] if row.get("binding_id") == BINDING\n'
     '                                    and row.get("context_id") == PRIOR_CONTEXT and row.get("closed_at_ms") is None],\n')
once('                    and node.get("readiness") == "ready" and node.get("policy_state") == "enabled", "R10_NODE_NOT_FRESH_READY")\n',
     '                    and node.get("readiness") == "ready" and node.get("policy_state") == "enabled"\n'
     '                    and node.get("policy_expires_at_ms", 0) > overview["observed_at_ms"], "R10_NODE_NOT_FRESH_READY")\n')
once('    require(len(contexts) == 1 and contexts[0]["context_id"] == marker.get("context_id")\n'
     '            and contexts[0]["expires_at_ms"] == expiry, "RENEWED_CONTEXT_CHANGED")\n',
     '    require(len(contexts) == 1 and contexts[0]["context_id"] == marker.get("context_id")\n'
     '            and contexts[0]["device_id"] == DEVICE and contexts[0]["workspace_id"] == WORKSPACE\n'
     '            and contexts[0]["workspace_generation"] == GENERATION and contexts[0]["expires_at_ms"] == expiry,\n'
     '            "RENEWED_CONTEXT_CHANGED")\n')
once('            and pilots[0]["expires_at_ms"] == expiry, "RENEWED_PILOT_CHANGED")\n',
     '            and pilots[0]["device_id"] == DEVICE and pilots[0]["workspace_id"] == WORKSPACE\n'
     '            and pilots[0]["workspace_generation"] == GENERATION and pilots[0]["expires_at_ms"] == expiry,\n'
     '            "RENEWED_PILOT_CHANGED")\n')
ast.parse(helper)
destination = out / "ubuntu-r10-store-authority.py"
with destination.open("xb") as handle:
    handle.write(helper.encode())
receipt = {"operation": "guarded_r10_store_60m_authority_helper_preparation", "captured_at_utc": datetime.now(timezone.utc).isoformat(),
           "source_revision": packet["source_revision"], "package_source_sha256": packet["package_source_sha256"],
           "packet_manifest_sha256": hashlib.sha256(packet_bytes).hexdigest(), "helper_sha256": hashlib.sha256(helper.encode()).hexdigest(),
           "base_helper_sha256": hashlib.sha256(base).hexdigest(), "operator_approval_flag_required": True,
           "fresh_service_state_activation_pins_required": True, "duration_ms": 3600000,
           "time_anchor": "first approved renewal persisted once in protected operation marker",
           "target_host": "100.116.112.22", "target_user": "svhome", "target_service": "codex-control-plane.service",
           "binding_id": "bind_3e05bf64cb3e4bab93d930ae1692bebb", "device_id": "72ceec2d-e3f2-472f-8e3c-99fffe053035",
           "workspace_id": "workspace_dda1d78e9a21402aa6213f72af64f788", "workspace_generation": "generation_c2f13e8d02344cf6a38a3f42ecfa59b6",
           "service_grant_id": "mcpsvcgrant_bf8c94291a1b448abcfdaaba5531a5bd", "service_grant_mutation": False,
           "standing_policy_mutation": False, "sql_data_writes": False, "command_replay": False,
           "sandbox_probe": False, "pending_run_acceptance": False, "remote_execution": False, "syntax": "pass",
           "fixed_deadline_observe_reopen_helper_preserved": True, "post_r10_source_dependency": False}
with (out / "r10-authority-helper-manifest.json").open("xb") as handle:
    handle.write((json.dumps(receipt, sort_keys=True, indent=2) + "\n").encode())
print(json.dumps(receipt, sort_keys=True, indent=2))
