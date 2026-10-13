"""Derive the reviewed source-only handoff with an existing recovery fence."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / 'native-first-20261012/deploy-server-metadata-overlay.py'

def change(source, old, new):
    if source.count(old) != 1:
        raise RuntimeError('DEPLOYMENT_SOURCE_ANCHOR_DRIFT')
    return source.replace(old, new)

source = BASE.read_text(encoding='utf-8')
source = change(source, 'def census(database, approved, allow_live=False):', 'def census(database, approved, allow_live=False, admission_mode="scoped_pilot"):')
source = change(source, '== "scoped_pilot", "ADMISSION_CHANGED")', '== admission_mode, "ADMISSION_CHANGED")')
source = change(source,
    'active_actions = connection.execute("SELECT COUNT(*) FROM actions WHERE settled_at_ms IS NULL AND delivery_state IN (\'queued\',\'dispatch_unconfirmed\',\'accepted\')").fetchone()[0]',
    '''historical_ids = [item["action_id"] for item in approved.get("expected_historical_dispatch_actions", [])]
        for item in approved.get("expected_historical_dispatch_actions", []):
            row = connection.execute("SELECT action_id,device_id,workspace_id,workspace_generation,tool_name,delivery_state,expires_at_ms,settled_at_ms FROM actions WHERE action_id=?", (item["action_id"],)).fetchone()
            require(row is not None and dict(row) == item and row["expires_at_ms"] <= now and row["settled_at_ms"] is None, "HISTORICAL_DISPATCH_DRIFT")
        active_actions = connection.execute("SELECT COUNT(*) FROM actions WHERE settled_at_ms IS NULL AND delivery_state IN ('queued','dispatch_unconfirmed','accepted')" + (" AND action_id NOT IN (" + ",".join("?" for _ in historical_ids) + ")" if historical_ids else ""), historical_ids).fetchone()[0]''')
source = change(source, 'history_ids = expected_ids\n        hashes = {}', 'history_ids = expected_ids + historical_ids\n        placeholders = ",".join("?" for _ in history_ids)\n        hashes = {}')
source = change(source, 'for table in ("actions", "action_reconciliations", "delivery_attempts", "receipts"):', 'for table in ("actions", "action_reconciliations", "action_dispatch_dispositions", "delivery_attempts", "receipts"):')
source = change(source, 'def same_state(left, right, after_start=False):', 'def same_state(left, right, after_start=False, fence_change=False):')
source = change(source, 'keys = set(left["immutable_row_hashes"])', 'keys = set(left["immutable_row_hashes"])\n    if fence_change:\n        keys -= {"control_plane_state", "scoped_pilot_decisions"}')
source = change(source, 'codex-control-plane-native-first-1012-[a-f0-9]{12}', 'codex-control-plane-parallel-native-1012-[a-f0-9]{12}')
source = change(source,
    '== ["control-plane/control_plane/mcp_facade.py", "control-plane/control_plane/node_agent.py"], "UNAPPROVED_SOURCE_DELTA")',
    'and set(changed) <= set(approved["allowed_runtime_files"]), "UNAPPROVED_SOURCE_DELTA")')
# Closing admission is a transaction in the operated server; it also records
# revocation of old pilots. They are reissued through supported APIs separately.
source = change(source,
    'STAGE = "stop_exact_service_then_final_census"\n        systemctl("stop")',
    '''STAGE = "atomic_recovery_admission_fence"
        token = environment.get("CONTROL_PLANE_OPERATOR_TOKEN", "")
        require(32 <= len(token) <= 512, "OPERATOR_CREDENTIAL_UNAVAILABLE")
        url = environment.get("CONTROL_PLANE_OPERATOR_URL", "https://svhome.tail0e4032.ts.net").rstrip("/")
        require(url == "https://svhome.tail0e4032.ts.net", "OPERATOR_ENDPOINT_DRIFT")
        request = urllib.request.Request(url + "/v1/maintenance/admission", method="POST", headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"}, data=b'{"mode":"recovery"}')
        with urllib.request.urlopen(request, timeout=10) as response:
            fence = json.loads(response.read(65536))
        require(fence.get("admission_mode") == "recovery", "RECOVERY_FENCE_NOT_PROVEN")
        fenced = census(database, approved, admission_mode="recovery")
        require(same_state(before, fenced, fence_change=True), "NEW_WORK_ARRIVED_BEFORE_FENCE")
        before = fenced
        STAGE = "stop_exact_fenced_service_then_final_census"
        systemctl("stop")''')
source = change(source, 'stopped = census(database, approved)', 'stopped = census(database, approved, admission_mode="recovery")')
source = change(source, 'same_state(stopped, census(database, approved))', 'same_state(stopped, census(database, approved, admission_mode="recovery"))')
source = change(source, 'post = census(database, approved, allow_live=True)', 'post = census(database, approved, allow_live=True, admission_mode="recovery")')
source = change(source,
    '"authority_and_history_unchanged": True,',
    '"history_preserved": True, "old_pilots_revoked_by_recovery_fence": True, "fenced": True, "live_work_idle": post["live_tasks"] == post["live_writers"] == post["active_actions"] == 0, "historical_unknown_preserved": True, "observed_at_ms": post["observed_at_ms"], "targets": approved["targets"],')
source = change(source, '"database_restored": False, "authority_mutated": False,\n            "explicit_pythonpath', '"database_restored": False, "authority_mutated": True, "admission_mode": "recovery",\n            "explicit_pythonpath')
source = change(source, '"operator_action": "Inspect source/config/service and preserved causal history; no database restore or action replay."', '"operator_action": "Admission may remain recovery with old pilots revoked. Inspect exact service/source and reissue authorized scopes through supported APIs; no database restore or action replay."')
ast.parse(source)
with (HERE / 'deploy-server-candidate.py').open('x', encoding='utf-8', newline='\n') as target:
    target.write(source)
receipt = {'operation': 'recovery_fenced_deployment_helper_preparation', 'sha256': hashlib.sha256(source.encode()).hexdigest(),
    'execute_performed': False, 'fence': 'existing authenticated atomic recovery API',
    'historical_dispatch_exception': 'exact immutable approved IDs only; expiry and unchanged row required',
    'rollback': 'source only; never restore SQLite; old pilots require supported reissue'}
with (HERE / 'deployment-helper-preparation.json').open('x', encoding='utf-8') as target:
    json.dump(receipt, target, indent=2)
    target.write('\n')
print(json.dumps(receipt))
