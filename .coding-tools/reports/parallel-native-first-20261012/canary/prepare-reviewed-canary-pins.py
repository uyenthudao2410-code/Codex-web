"""Construct new pins from fresh sanitized evidence; no live or database call."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import time


def require(condition, code):
    if not condition:
        raise RuntimeError(code)


def read(path):
    file = Path(path)
    require(file.is_absolute() and file.is_file() and file.stat().st_size <= 2 * 1024 * 1024, "BOUNDED_ABSOLUTE_EVIDENCE_REQUIRED")
    return json.loads(file.read_text(encoding="utf-8-sig"))


def construct(server, approvals, manifest, quarantine, kind, now):
    approvals = approvals.get("receipt", approvals)
    require(server.get("ok") is True and server.get("service_stable") is True
            and server.get("source_startup_disk_attestation_matches") is True
            and server.get("serving_source", {}).get("release_file_integrity_verified") is True
            and server.get("sqlite_integrity_ok") is True, "EXACT_SERVING_READINESS_REQUIRED")
    require(0 <= now - server.get("capture_completed_at_ms", 0) <= 120000
            and 0 <= now - approvals.get("observed_at_ms", 0) <= 120000, "FRESH_SERVER_AND_APPROVAL_EVIDENCE_REQUIRED")
    node, grant, contract = server["node"], server["service_grant"], server["tool_contract"]
    require(node["readiness"] == "ready" and node.get("revoked_at_ms") is None
            and 0 <= now - node["last_seen_at_ms"] <= 90000 and grant.get("live") is True,
            "LIVE_READY_NODE_AND_GRANT_REQUIRED")
    require(node["activation_epoch"] == approvals["activation_epoch_id"], "APPROVAL_AND_HEARTBEAT_EPOCH_DIFFER")
    local = str(node["contract_version"]).removeprefix("sha256:")
    require(re.fullmatch(r"[a-f0-9]{64}", local), "LOCAL_CONTRACT_DIGEST_INVALID")
    sources = server["serving_source"]["python_files_sha256"]
    pins = {"schema_version": 1, "principal_id": server["principal_id"], "grant_id": grant["grant_id"],
            "device_id": node["device_id"], "activation_epoch": node["activation_epoch"],
            "process_instance_id": node["runtime_instance_id"], "server_instance_id": node["mcp_server_instance_id"],
            "local_tool_contract_sha256": local, "facade_schema_version": contract["schema_version"],
            "facade_contract_sha256": contract["sha256"], "service_pid": server["service_pid"],
            "serving_mcp_facade_sha256": sources["mcp_facade.py"], "serving_node_agent_sha256": sources["node_agent.py"],
            "serving_store_sha256": sources["store.py"]}
    require(manifest.get("prepared") is True, "PREPARED_FIXTURE_MANIFEST_REQUIRED")
    targets = []
    labels = ["Codex-web"] if kind == "codex-full" else ["Codex-web", "Autocad"]
    require(approvals.get("approval_set") == ("codex-build" if kind == "codex-full" else "overlap"), "EXACT_APPROVAL_SET_REQUIRED")
    for label in labels:
        scope = server["expected_current_scopes"][label]
        bindings = scope["active_bindings"]
        require(len(bindings) == 1 and len(scope["active_registrations"]) == 1, "CURRENT_SCOPE_NOT_UNIQUE")
        binding = bindings[0]
        inventory = [item for item in server["delegated_inventory_targets"] if item["binding_id"] == binding["binding_id"]]
        require(len(inventory) == 1 and inventory[0]["readiness"] == "ready"
                and inventory[0]["presence_state"] == "online" and inventory[0]["dispatch_state"] == "dispatchable",
                "EXACT_CURRENT_TARGET_NOT_DISPATCHABLE")
        pilots = [item for item in server["live_pilots"] if item["principal_id"] == pins["principal_id"]
                  and item["binding_id"] == binding["binding_id"] and item["workspace_id"] == binding["workspace_id"]
                  and item["workspace_generation"] == binding["workspace_generation"]]
        require(len(pilots) == 1 and pilots[0]["expires_at_ms"] > now + 1800000, "EXACT_CURRENT_PILOT_NOT_FRESH")
        matches = [item for item in approvals["targets"] if item["workspace_label"] == label
                   and item["workspace_id"] == binding["workspace_id"] and item["workspace_generation"] == binding["workspace_generation"]]
        require(len(matches) == 1 and matches[0]["policy"]["state"] == "enabled"
                and matches[0]["policy"]["facade_contract"] == contract, "EXACT_INSTALLED_POLICY_NOT_CURRENT")
        approved = matches[0]
        target = {"workspace_label": label, "workspace_id": binding["workspace_id"],
                  "workspace_generation": binding["workspace_generation"], "binding_id": binding["binding_id"],
                  "pilot_decision_id": pilots[0]["decision_id"], "activation_verified": True,
                  "exec_policy_sha256": approved["policy"]["policy_sha256"]}
        if kind == "codex-full":
            files = [item for item in manifest["files"] if item["path"] == "tests/fixtures/native-first-canary/trusted-build.js"]
            require(manifest.get("fixture") == "tests/fixtures/native-first-canary"
                    and approved["added_native_argv"] == ["node", "trusted-build.js"]
                    and approved["added_native_cwd"] == manifest["fixture"] and len(files) == 1
                    and approved["native_source_sha256"] == files[0]["sha256"], "EXACT_CODEX_BUILD_APPROVAL_REQUIRED")
            pins.update(target, trusted_build_explicitly_approved=True)
        else:
            prepared = [item for item in manifest["targets"] if item["workspace_label"] == label]
            require(len(prepared) == 1 and prepared[0]["native_source_sha256"] == approved["native_source_sha256"]
                    and prepared[0]["native_argv"] == approved["added_native_argv"]
                    and prepared[0]["native_cwd"] == approved["added_native_cwd"],
                    "EXACT_OVERLAP_FIXTURE_SOURCE_REQUIRED")
            target.update(native_fixture_explicitly_approved=True, native_argv=approved["added_native_argv"],
                          native_cwd=approved["added_native_cwd"], native_source_sha256=approved["native_source_sha256"])
            if label == "Autocad":
                require(quarantine.get("ok") is True and quarantine.get("actions_settled") is False
                        and quarantine.get("actions_replayed") is False and len(quarantine.get("quarantined_action_ids", [])) == 3,
                        "EXACT_PRESERVED_QUARANTINE_RECEIPT_REQUIRED")
                target["retained_unknown_actions"] = quarantine["quarantined_action_ids"]
            targets.append(target)
    if kind == "overlap":
        pins["targets"] = targets
    return pins


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server-readiness", required=True)
    parser.add_argument("--approval-receipt", required=True)
    parser.add_argument("--fixture-manifest", required=True)
    parser.add_argument("--quarantine-receipt")
    parser.add_argument("--kind", choices=("codex-full", "overlap"), required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    require(output.is_absolute() and output.parent.resolve() == Path(__file__).resolve().parent, "NEW_CANARY_PINS_OUTPUT_REQUIRED")
    inputs = [args.server_readiness, args.approval_receipt, args.fixture_manifest]
    server, approvals, manifest = [read(path) for path in inputs]
    quarantine = read(args.quarantine_receipt) if args.quarantine_receipt else {}
    if args.quarantine_receipt:
        inputs.append(args.quarantine_receipt)
    pins = construct(server, approvals, manifest, quarantine, args.kind, int(time.time() * 1000))
    pins["evidence_sha256"] = {Path(path).name: hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in inputs}
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(pins, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"operation": "reviewed_canary_pins_prepared", "ok": True, "kind": args.kind, "pins_path": str(output)}))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        code = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print(json.dumps({"operation": "reviewed_canary_pins_prepared", "ok": False, "error_code": code}))
        sys.exit(1)
