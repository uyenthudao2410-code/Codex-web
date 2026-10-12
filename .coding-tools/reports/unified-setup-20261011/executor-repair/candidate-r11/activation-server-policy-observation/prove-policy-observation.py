"""Offline proof of the actual derivative reopen guards; no network or effects."""
from __future__ import annotations
import ast
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import types

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
sys.modules.setdefault("fcntl", types.SimpleNamespace())
sys.modules.setdefault("pwd", types.SimpleNamespace())
sys.path.insert(0, str(OUT))
import r11_common as common


def fixture():
    now = 1700000000000
    expiry = now + 3500000
    marker = {"phase": "authority_renewed", "service_instance_id": "fixture-service",
              "requested_at_ms": expiry - 3600000, "expires_at_ms": expiry,
              "context_id": "fixture-context", "pilot_id": "fixture-pilot"}
    overview = {"observed_at_ms": now, "admission": {"admission_mode": "recovery"},
                "contexts": [{"context_id": marker["context_id"], "binding_id": common.BINDING,
                              "device_id": common.DEVICE, "workspace_id": common.WORKSPACE,
                              "workspace_generation": common.GENERATION, "closed_at_ms": None,
                              "expires_at_ms": expiry}],
                "scoped_pilot_decisions": [{"decision_id": marker["pilot_id"], "binding_id": common.BINDING,
                                            "principal_id": common.PRINCIPAL, "device_id": common.DEVICE,
                                            "workspace_id": common.WORKSPACE,
                                            "workspace_generation": common.GENERATION,
                                            "revoked_at_ms": None, "expires_at_ms": expiry}],
                "nodes": [{"device_id": common.DEVICE, "last_seen_at_ms": now - 1000,
                           "readiness": "ready", "policy_state": "enabled",
                           "policy_expires_at_ms": now - 1000 + 60000,
                           "activation_epoch": "fixture-r11-epoch", "runtime_instance_id": "fixture-runtime",
                           "mcp_server_instance_id": "fixture-mcp", "contract_version": "sha256:" + "a" * 64}]}
    args = types.SimpleNamespace(expected_activation_epoch="fixture-r11-epoch", expected_runtime_instance="fixture-runtime",
                                 expected_mcp_instance="fixture-mcp", expected_contract_version="sha256:" + "a" * 64)
    return args, overview, marker


def main():
    checks = []
    for path in OUT.glob("*.py"):
        compile(path.read_bytes(), str(path), "exec")
    checks.append("all_helpers_compile")
    parent = OUT.parent / "activation-server"
    manifest = json.loads((OUT / "helper-manifest.json").read_bytes())
    assert hashlib.sha256((parent / "helper-manifest.json").read_bytes()).hexdigest() == manifest["derived_from_manifest_sha256"]
    for name in ("root-ssh.py", "r11_common.py", "ubuntu-r11-rollout.py", "ubuntu-r11-recovery.py"):
        assert (parent / name).read_bytes() == (OUT / name).read_bytes()
    for name, pin in manifest["helpers"].items():
        raw = (OUT / name).read_bytes()
        assert len(raw) == pin["size_bytes"] and hashlib.sha256(raw).hexdigest() == pin["sha256"]
    for pin in manifest["archives"]:
        raw = (OUT / pin["relative_path"]).read_bytes()
        assert len(raw) == pin["size_bytes"] and hashlib.sha256(raw).hexdigest() == pin["sha256"]
    checks.append("unchanged_common_transport_rollout_recovery_and_archive_pins")
    tree = ast.parse((OUT / "ubuntu-r11-authority.py").read_bytes())
    branches = [node for node in ast.walk(tree) if isinstance(node, ast.If)
                and isinstance(node.test, ast.Compare)
                and isinstance(node.test.left, ast.Attribute) and node.test.left.attr == "action"
                and len(node.test.comparators) == 1 and isinstance(node.test.comparators[0], ast.Constant)
                and node.test.comparators[0].value == "renew"]
    assert len(branches) == 1 and len(branches[0].orelse) >= 8
    guards = branches[0].orelse[:7]
    assert isinstance(guards[1], ast.Expr) and isinstance(guards[1].value, ast.Call)
    assert guards[1].value.func.id == "renewed_authority"
    assert isinstance(guards[-1], ast.Expr) and isinstance(guards[-1].value, ast.Call)
    assert guards[-1].value.args[-1].value == "R11_NODE_NOT_FRESH_READY_OR_POLICY_OBSERVATION"
    code = compile(ast.Module(body=copy.deepcopy(guards), type_ignores=[]), "actual-reopen-guards", "exec")

    def check(change=None, expected_code=None):
        args, overview, marker = fixture()
        if change:
            change(overview, marker)
        namespace = {"args": args, "overview": overview, "marker": marker,
                     "health": {"service_instance_id": "fixture-service"},
                     "DEVICE": common.DEVICE, "require": common.require,
                     "renewed_authority": common.renewed_authority}
        try:
            exec(code, namespace)
        except common.GuardFailure as error:
            assert error.code == expected_code, (error.code, expected_code)
        else:
            assert expected_code is None, "expected guard failure was admitted"

    ttl_error = "R11_NODE_NOT_FRESH_READY_OR_POLICY_OBSERVATION"
    check()
    checks.append("fresh_standing_ttl_admitted_with_exact_anchored_context_and_pilot")
    check(lambda o, m: o["nodes"][0].update(policy_expires_at_ms=o["observed_at_ms"]), ttl_error)
    checks.append("expired_observation_ttl_rejected")
    check(lambda o, m: o["nodes"][0].update(policy_expires_at_ms=True), ttl_error)
    checks.append("boolean_observation_expiry_rejected")
    check(lambda o, m: o["nodes"][0].update(policy_expires_at_ms=o["nodes"][0]["last_seen_at_ms"] + 60001), ttl_error)
    checks.append("observation_ttl_over60s_rejected")
    check(lambda o, m: o["nodes"][0].update(last_seen_at_ms=o["observed_at_ms"] - 60000), ttl_error)
    checks.append("stale_heartbeat_rejected")
    check(lambda o, m: o["nodes"][0].update(last_seen_at_ms=o["observed_at_ms"] + 1), ttl_error)
    checks.append("future_heartbeat_rejected")
    check(lambda o, m: o["nodes"][0].update(runtime_instance_id="other-runtime"), "EXPECTED_R11_NODE_IDENTITY_REQUIRED")
    checks.append("wrong_runtime_identity_rejected")
    check(lambda o, m: o["contexts"][0].update(expires_at_ms=o["observed_at_ms"] - 1), "RENEWED_CONTEXT_CHANGED")
    checks.append("expired_context_rejected_independently_of_fresh_telemetry")
    check(lambda o, m: o["contexts"][0].update(expires_at_ms=m["expires_at_ms"] + 1), "RENEWED_CONTEXT_CHANGED")
    checks.append("context_expiry_must_match_anchored_window")
    check(lambda o, m: o["scoped_pilot_decisions"][0].update(expires_at_ms=o["observed_at_ms"] - 1), "RENEWED_PILOT_CHANGED")
    checks.append("expired_pilot_rejected")
    check(lambda o, m: m.update(expires_at_ms=o["observed_at_ms"], requested_at_ms=o["observed_at_ms"] - 3600000), "RENEWAL_WINDOW_EXPIRED_OR_INVALID")
    checks.append("expired_anchored60m_window_rejected")
    receipt = {"captured_at_utc": datetime.now(timezone.utc).isoformat(), "checks_passed": checks,
               "check_count": len(checks), "authority_sha256": manifest["helpers"]["ubuntu-r11-authority.py"]["sha256"],
               "common_sha256": manifest["helpers"]["r11_common.py"]["sha256"],
               "network_or_ssh_used": False, "external_mutation": False, "source_product_changed": False,
               "context_or_pilot_reanchored": False}
    with (OUT / "proof-receipt.json").open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(receipt, handle, sort_keys=True, indent=2)
        handle.write("\n")
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
