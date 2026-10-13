"""Fresh two-root idle pins from actual final and isolated policies; no live calls."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time

SPEC = importlib.util.spec_from_file_location("canary_pin_builder", Path(__file__).with_name("prepare-reviewed-canary-pins.py"))
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)
require = builder.require


def construct(server, final_policy, isolated, plan, quarantine, now, local_state, local_epoch):
    require(final_policy.get("ok") is True and final_policy.get("operation") == "final-policy"
            and isolated.get("ok") is True and isolated.get("operation") == "isolated-idle-policy-isolate",
            "ACTUAL_FINAL_AND_ISOLATED_POLICY_RECEIPTS_REQUIRED")
    require(0 <= now - isolated.get("observed_at_ms", 0) <= 120000, "FRESH_ISOLATED_POLICY_REQUIRED")
    final = final_policy["receipt"]
    require(final_policy["candidate"] == isolated["candidate"] == plan["candidate"]
            and final_policy["parity_proof_sha256"] == isolated["parity_sha256"] == plan["parity_sha256"]
            and final_policy["smoke_proof_sha256"] == isolated["smoke_sha256"] == plan["smoke_sha256"],
            "EXACT_SAME_PACKAGED_POLICY_EVIDENCE_REQUIRED")
    require(plan.get("ok") is True and plan.get("operation") == "isolated-idle-policy-plan" and plan.get("mutations") == 0
            and isolated.get("other_scope_unchanged") is True and isolated["plan_sha256"] == plan["_file_sha256"]
            and isolated["owner_instance_id"] == plan["owner_instance_id"]
            and isolated["other_scope_sha256"] == plan["other_scope_sha256"],
            "EXACT_ISOLATE_PLAN_AND_OTHER_SCOPE_REQUIRED")
    require(final["activation_epoch_id"] == isolated["activation_epoch_id"] == server["node"]["activation_epoch"],
            "CURRENT_POLICY_EPOCH_MISMATCH")
    require(len(final.get("targets", [])) == 2 and len(plan.get("before", [])) == 2, "EXACT_TWO_POLICY_TARGETS_REQUIRED")
    require(server.get("ok") is True and server.get("service_stable") is True
            and server.get("source_startup_disk_attestation_matches") is True
            and server.get("serving_source", {}).get("release_file_integrity_verified") is True
            and server.get("sqlite_integrity_ok") is True, "EXACT_SERVING_READINESS_REQUIRED")
    require(0 <= now - server.get("capture_completed_at_ms", 0) <= 120000, "FRESH_SERVER_READINESS_REQUIRED")
    node, grant, contract = server["node"], server["service_grant"], server["tool_contract"]
    require(node["readiness"] == "ready" and node.get("revoked_at_ms") is None
            and 0 <= now - node["last_seen_at_ms"] <= 90000 and grant.get("live") is True,
            "LIVE_READY_NODE_AND_GRANT_REQUIRED")
    local = str(node["contract_version"]).removeprefix("sha256:")
    sources = server["serving_source"]["python_files_sha256"]
    require(all(re.fullmatch(r"[a-f0-9]{64}", str(value)) for value in [local, contract["sha256"],
                *(sources[name] for name in ("mcp_facade.py", "node_agent.py", "store.py"))]),
            "EXACT_SERVING_CONTRACT_AND_SOURCE_DIGESTS_REQUIRED")
    pins = {"schema_version": 1, "principal_id": server["principal_id"], "grant_id": grant["grant_id"],
            "device_id": node["device_id"], "activation_epoch": node["activation_epoch"],
            "process_instance_id": node["runtime_instance_id"], "server_instance_id": node["mcp_server_instance_id"],
            "local_tool_contract_sha256": local, "facade_schema_version": contract["schema_version"],
            "facade_contract_sha256": contract["sha256"], "service_pid": server["service_pid"],
            "serving_mcp_facade_sha256": sources["mcp_facade.py"], "serving_node_agent_sha256": sources["node_agent.py"],
            "serving_store_sha256": sources["store.py"], "targets": []}
    require(all(isinstance(pins[name], str) and pins[name] for name in ("principal_id", "grant_id", "device_id",
                "activation_epoch", "process_instance_id", "server_instance_id"))
            and isinstance(pins["service_pid"], int) and pins["service_pid"] > 0, "EXACT_LIVE_RUNTIME_IDENTITIES_REQUIRED")
    epoch = local_epoch.get("current", {})
    pathkey = lambda value: str(value).replace("\\", "/").casefold().rstrip("/")
    require(epoch.get("activation_epoch_id") == pins["activation_epoch"] and epoch.get("state") == "READY"
            and epoch.get("admission_state") == "OPEN" and local_state.get("nativeActivationEpochId") == pins["activation_epoch"]
            and pathkey(local_state.get("nativeModuleRoot", "")) == pathkey(plan["candidate"] + "/resources/resources/coding-tools-mcp")
            and re.fullmatch(r"[a-f0-9]{24}", str(local_state.get("nativeInstanceId", "")))
            and type(local_state.get("nativePid")) is int and local_state["nativePid"] > 1
            and re.fullmatch(r"[0-9]{16,20}", str(local_state.get("nativeProcessStartToken", ""))),
            "EXACT_CURRENT_LOCAL_SUPERVISOR_PROJECTION_REQUIRED")
    # Launcher nonce and MCP process identity are different namespaces. The
    # idle observer verifies the exact PID/start token against the live process
    # before dispatch; this constructor preserves the current disk projection.
    pins.update(supervisor_instance_id=local_state["nativeInstanceId"], native_pid=local_state["nativePid"],
                native_process_start_token=str(local_state["nativeProcessStartToken"]))
    policies = []
    for label in ("Codex-web", "Autocad"):
        matches = [item for item in final["targets"] if item["workspace_label"] == label]
        require(len(matches) == 1, "EXACT_FINAL_POLICY_SCOPE_REQUIRED")
        original = matches[0]
        observed = original["policy"]
        require(observed["state"] == "enabled" and observed["execution_mode"] == "native_first", "EXACT_FINAL_NATIVE_FIRST_POLICY_REQUIRED")
        saved = [item for item in plan["before"] if item["workspace_id"] == original["workspace_id"]
                 and item["workspace_generation"] == original["workspace_generation"]]
        require(len(saved) == 1 and saved[0]["policy_sha256"] == observed["policy_sha256"], "ISOLATE_PLAN_NOT_BOUND_TO_FINAL_POLICY")
        current = isolated["after"] if label == "Codex-web" else saved[0]
        require(current["workspace_id"] == original["workspace_id"] and current["workspace_generation"] == original["workspace_generation"]
                and current["execution_mode"] == ("isolated" if label == "Codex-web" else "native_first")
                and current.get("state") == "enabled" and current.get("facade_contract") == contract
                and re.fullmatch(r"[a-f0-9]{64}", str(current.get("policy_sha256", ""))),
                "EXACT_CURRENT_IDLE_POLICY_REQUIRED")
        policies.append({"workspace_label": label, "workspace_id": original["workspace_id"],
                         "workspace_generation": original["workspace_generation"], "policy": current})
    for policy in policies:
        label = policy["workspace_label"]
        scope = server["expected_current_scopes"][label]
        require(len(scope["active_bindings"]) == 1 and len(scope["active_registrations"]) == 1, "CURRENT_SCOPE_NOT_UNIQUE")
        binding, registration = scope["active_bindings"][0], scope["active_registrations"][0]
        fields = ("binding_id", "workspace_id", "workspace_generation")
        require(all(binding.get(name) for name in fields)
                and all(registration.get(name) == binding[name] for name in ("workspace_id", "workspace_generation"))
                and (not binding.get("device_id") or registration.get("device_id") == binding["device_id"] == pins["device_id"])
                and binding["workspace_id"] == policy["workspace_id"]
                and binding["workspace_generation"] == policy["workspace_generation"], "EXACT_POLICY_BINDING_SCOPE_REQUIRED")
        inventory = [item for item in server["delegated_inventory_targets"]
                     if all(item.get(name) == binding[name] for name in fields)]
        require(len(inventory) == 1 and inventory[0]["readiness"] == "ready"
                and inventory[0]["presence_state"] == "online" and inventory[0]["dispatch_state"] == "dispatchable",
                "EXACT_CURRENT_TARGET_NOT_DISPATCHABLE")
        pilots = [item for item in server["live_pilots"] if item["principal_id"] == pins["principal_id"]
                  and all(item.get(name) == binding[name] for name in fields)]
        require(len(pilots) == 1 and pilots[0]["expires_at_ms"] > now + 1800000, "EXACT_CURRENT_PILOT_NOT_FRESH")
        target = {"workspace_label": label, **{name: binding[name] for name in fields},
                  "pilot_decision_id": pilots[0]["decision_id"], "activation_verified": True,
                  "exec_policy_sha256": policy["policy"]["policy_sha256"],
                  "execution_mode": policy["policy"]["execution_mode"]}
        if label == "Autocad":
            actions = quarantine.get("quarantined_action_ids", [])
            require(quarantine.get("ok") is True and quarantine.get("actions_settled") is False
                    and quarantine.get("actions_replayed") is False and len(actions) == 3
                    and len(set(actions)) == 3 and all(re.fullmatch(r"act_[a-f0-9]{32}", str(value)) for value in actions),
                    "EXACT_PRESERVED_QUARANTINE_RECEIPT_REQUIRED")
            target["retained_unknown_actions"] = actions
        pins["targets"].append(target)
    require(len({target["binding_id"] for target in pins["targets"]}) == 2, "EXACT_DISTINCT_TWO_ROOT_BINDINGS_REQUIRED")
    pins.update(purpose="isolated-idle", isolated_idle_approved=True, no_native_fixture_approval_claim=True)
    return pins


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("server-readiness", "final-policy-receipt", "isolated-policy-receipt", "policy-plan", "quarantine-receipt", "output"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    output = Path(args.output)
    require(output.is_absolute() and output.parent.resolve() == Path(__file__).resolve().parent, "NEW_CANARY_PINS_OUTPUT_REQUIRED")
    inputs = [args.server_readiness, args.final_policy_receipt, args.isolated_policy_receipt, args.policy_plan, args.quarantine_receipt]
    server, final, isolated, plan, quarantine = [builder.read(file) for file in inputs]
    profile = Path(os.environ.get("APPDATA", "")) / "web-mcp-assistant"
    local_inputs = [profile / "runtime-state.json", profile / "activation-epoch.json"]
    local_state, local_epoch = [builder.read(file) for file in local_inputs]
    plan["_file_sha256"] = hashlib.sha256(Path(args.policy_plan).read_bytes()).hexdigest()
    pins = construct(server, final, isolated, plan, quarantine, int(time.time() * 1000), local_state, local_epoch)
    pins["evidence_sha256"] = {Path(file).name: hashlib.sha256(Path(file).read_bytes()).hexdigest() for file in inputs + local_inputs}
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(pins, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"operation": "reviewed_idle_pins_prepared", "ok": True, "pins_path": str(output)}))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"operation": "reviewed_idle_pins_prepared", "ok": False,
                          "error_code": str(error) if isinstance(error, RuntimeError) else type(error).__name__}))
        sys.exit(1)
