"""Focused offline helper proof. No SSH, service, policy, or network operation."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
from unittest import mock
sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
REPAIR = OUT.parents[1]
BASE = REPAIR / "store-delta/codex-control-plane-395c7868931729249e66654132c8734a404c22cfa6c74a85f3cc7fdc56e5d4d5"
R11 = REPAIR / "initial-proof-server/codex-control-plane-9cae104420e091811b94f76736a95e94ff333010be344eed7d1274f08601386c"
sys.modules.setdefault("fcntl", types.SimpleNamespace())
sys.modules.setdefault("pwd", types.SimpleNamespace())
sys.path.insert(0, str(OUT))
import r11_common as common

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main():
    checks=[]
    for path in OUT.glob("*.py"):
        compile(path.read_bytes(), str(path), "exec")
    checks.append("all_helpers_compile")
    store28 = load("frozen28_helpers_proof", BASE / "control-plane/control_plane/store.py")
    store29 = load("frozen29_helpers_proof", R11 / "control-plane/control_plane/store.py")
    with tempfile.TemporaryDirectory(prefix="r11-helper-proof-") as temp:
        database = Path(temp) / "fixture.sqlite3"
        legacy=store28.ControlPlaneStore(database,clock=lambda:1700000000000)
        legacy.enroll_node(owner_id="owner-default",device_id="helper-fixture-device",endpoint_id="helper-fixture-endpoint",display_name="Fixture")
        legacy.register_node_workspace(device_id="helper-fixture-device",workspace_id="helper-fixture-workspace",workspace_generation="helper-fixture-generation",display_name="Fixture",capabilities={"read":True,"write":True,"exec":True})
        binding=legacy.create_binding(owner_id="owner-default",device_id="helper-fixture-device",workspace_id="helper-fixture-workspace",workspace_generation="helper-fixture-generation",display_name="Fixture")["binding_id"]
        principal=legacy.link_oauth_principal(owner_id="owner-default",issuer="https://identity.example.test/helper",subject="fixture-subject")["principal_id"]
        legacy.request_mcp_patch_permission(owner_id="owner-default",principal_id=principal,binding_id=binding,path="fixture.cjs",preimage_sha256="a"*64,patch_sha256="b"*64,validation_profile="targeted",idempotency_key="helper-legacy-permission",facade_contract={"schema_version":32,"profile":"workspace_context","sha256":"c"*64})
        with mock.patch.object(common,"HISTORICAL_IDS",()),mock.patch.object(common,"FAMILY_DIGEST",common.digest([])):
            before=common.state(database)
            store29.ControlPlaneStore(database,clock=lambda:1700000000000)
            after=common.state(database)
            common.compare_history(before,after,migration=True)
            assert before["all_action_task_intent_families_sha256"]==after["all_action_task_intent_families_sha256"]
            assert before["schema_version"]==28 and after["schema_version"]==29
    checks.append("nullable_schema29_plan_columns_preserve_legacy_execution_permission_context_fingerprints")
    authority=load("authority_helper_proof",OUT/"ubuntu-r11-authority.py")
    now=1700000000000
    overview={"observed_at_ms":now,"admission":{"admission_mode":"recovery"},"contexts":[{"context_id":"old-context","binding_id":common.BINDING,"closed_at_ms":None,"expires_at_ms":now-1}],"scoped_pilot_decisions":[]}
    marker={"old_context_ids":["old-context"],"phase":"intake_closed"}
    calls=[]
    def api(_origin,_token,route,body=None):
        calls.append((route,body))
        if route=="/v1/ui/overview":return overview
        if route.endswith("/close"):
            overview["contexts"][0]["closed_at_ms"]=now
            return overview["contexts"][0]
        if route=="/v1/contexts":
            row={**body,"context_id":"new-context","device_id":common.DEVICE,"workspace_id":common.WORKSPACE,"workspace_generation":common.GENERATION,"closed_at_ms":None}
            overview["contexts"].append(row);return row
        if route=="/v1/scoped-pilot-decisions":
            row={**body,"decision_id":"new-pilot","device_id":common.DEVICE,"workspace_id":common.WORKSPACE,"workspace_generation":common.GENERATION,"revoked_at_ms":None}
            overview["scoped_pilot_decisions"].append(row);return row
        raise AssertionError(route)
    with mock.patch.object(authority,"api",api),mock.patch.object(authority,"save",lambda value:None),mock.patch.object(authority.time,"time",lambda:now/1000):
        grant={"expires_at_ms":now+7200000}
        authority.renew("http://fixture","test-only",overview,marker,grant)
        first=(marker["requested_at_ms"],marker["expires_at_ms"],marker["context_id"],marker["pilot_id"])
        authority.renew("http://fixture","test-only",overview,marker,grant)
        assert first==(marker["requested_at_ms"],marker["expires_at_ms"],marker["context_id"],marker["pilot_id"])
        assert marker["expires_at_ms"]-marker["requested_at_ms"]==3600000
        assert sum(route=="/v1/contexts" for route,_ in calls)==1
        assert sum(route=="/v1/scoped-pilot-decisions" for route,_ in calls)==1
        assert not any("grant" in route for route,_ in calls)
        overview["scoped_pilot_decisions"][0]["binding_id"]="other-binding"
        try:authority.renew("http://fixture","test-only",overview,marker,grant)
        except common.GuardFailure:pass
        else:raise AssertionError("wrong-target pilot was not blocked")
    checks.append("one_exact60m_window_retry_creates_no_duplicate_context_pilot_or_grant")
    checks.append("wrong_target_pilot_rejected")
    transport=load("transport_helper_proof",OUT/"root-ssh.py")
    assert transport.safe_receipt(b'{"phase":"public","ok":true}\n')[0]["ok"]
    try:transport.safe_receipt(b'{"phase":"private","operator_token":"fixture"}\n')
    except ValueError:pass
    else:raise AssertionError("private stdout accepted")
    checks.append("binary_ssh_transport_rejects_private_stdout_fields")
    print(json.dumps({"checks_passed":checks,"check_count":len(checks),"network_or_ssh_used":False,"external_mutation":False},sort_keys=True))

if __name__=="__main__":main()
