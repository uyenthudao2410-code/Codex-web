"""Build a bounded, read-only production evidence report from retained receipts."""

import argparse
import hashlib
import json
import time
from pathlib import Path


MAX_BYTES = 8 * 1024 * 1024


def load(path_value):
    path = Path(path_value)
    if not path.is_absolute() or not path.is_file() or path.is_symlink():
        raise RuntimeError("ABSOLUTE_SOURCE_REQUIRED")
    raw = path.read_bytes()
    if not raw or len(raw) > MAX_BYTES:
        raise RuntimeError("SOURCE_SIZE_OUT_OF_BOUNDS")
    if path.suffix == ".ndjson":
        values = [json.loads(line) for line in raw.decode("utf-8-sig").splitlines() if line.strip()]
        finals = [v for v in values if v.get("phase") == "final"]
        if len(finals) != 1:
            raise RuntimeError("SINGLE_FINAL_RECEIPT_REQUIRED")
        value = finals[0]
    else:
        value = json.loads(raw.decode("utf-8-sig"))
    return value, {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw)}


def select(value, keys):
    return {key: value.get(key) for key in keys}


def build(args):
    semantic, semantic_src = load(args.semantic)
    overlap, overlap_src = load(args.overlap)
    idle, idle_src = load(args.idle)
    policy, policy_src = load(args.policy)
    readiness, readiness_src = load(args.readiness)
    local_ready, local_ready_src = load(args.local_ready)
    discovery, discovery_src = load(args.discovery)
    joined, joined_src = load(args.joined)
    if semantic.get("ok") is not True or semantic.get("source_final_audit_accepted_count") != 20 or semantic.get("proof_waves", {}).get("distinct_count") != 20 or semantic.get("rows_checked") != 20 or not all(semantic.get("checks", {}).values()):
        raise RuntimeError("SEMANTIC_ACCEPTANCE_NOT_20_OF_20")
    if overlap.get("ok") is not True or overlap.get("overlap", {}).get("overlap_duration_ms", 0) <= 0:
        raise RuntimeError("POSITIVE_PARALLEL_OVERLAP_NOT_PROVEN")
    if joined.get("status") != "lanes_complete_semantic_gate_separate":
        raise RuntimeError("NATIVE_CONTINUATION_JOIN_NOT_COMPLETE")
    if policy.get("ok") is not True:
        raise RuntimeError("CURRENT_POLICY_RECEIPT_NOT_SUCCESSFUL")
    if readiness.get("ok") is not True:
        raise RuntimeError("CURRENT_READINESS_RECEIPT_NOT_SUCCESSFUL")
    if discovery.get("connector_state") != "CHANGED_NEEDS_DISCOVERY" or discovery.get("connector_applicability") != "not_applicable_central_executor" or discovery.get("strict_discovery_required") is not False or discovery.get("central_runtime_ready") is not True:
        raise RuntimeError("CENTRAL_CONNECTOR_CLASSIFICATION_NOT_VERIFIED")
    expected_identity = joined.get("runtime_identity", {})
    if policy.get("receipt", {}).get("activation_epoch_id") != expected_identity.get("activation_epoch_id"):
        raise RuntimeError("POLICY_ACTIVATION_EPOCH_CHANGED")
    node = readiness.get("node", {})
    if {"activation_epoch_id": node.get("activation_epoch"), "process_instance_id": node.get("runtime_instance_id"),
        "server_instance_id": node.get("mcp_server_instance_id"), "tool_contract_sha256": str(node.get("contract_version", "")).removeprefix("sha256:")} != expected_identity:
        raise RuntimeError("CURRENT_READINESS_RUNTIME_IDENTITY_CHANGED")
    if idle.get("ok") is not True or idle.get("terminal", {}).get("runtime_identity") != expected_identity:
        raise RuntimeError("IDLE_RUNTIME_IDENTITY_OR_RESULT_INVALID")
    targets = overlap.get("targets", [])
    if len(targets) != 2 or any(target.get("proofs", {}).get("node_overlap", {}).get("runtime_identity") != expected_identity for target in targets):
        raise RuntimeError("OVERLAP_RUNTIME_IDENTITY_CHANGED")
    if len({target.get("proofs", {}).get("node_overlap", {}).get("job_id") for target in targets}) != 2:
        raise RuntimeError("OVERLAP_JOBS_NOT_UNIQUE")
    target_policies = {value.get("workspace_label"): value for value in policy.get("receipt", {}).get("targets", [])}
    if set(target_policies) != {"Codex-web", "Autocad"} or any(value.get("policy", {}).get("execution_mode") != "native_first" for value in target_policies.values()):
        raise RuntimeError("BOTH_SCOPE_NATIVE_FIRST_POLICIES_REQUIRED")
    local_receipt = local_ready.get("receipt", {})
    activation = local_receipt.get("activation", {})
    runtime = local_receipt.get("runtime", {})
    if local_ready.get("ok") is not True or activation.get("activation_epoch_id") != expected_identity.get("activation_epoch_id") or activation.get("state") != "READY" or activation.get("admission_open") is not True:
        raise RuntimeError("LOCAL_ACTIVATION_NOT_READY_AND_OPEN")
    if any(runtime.get(key) is not True for key in ("fullyReady", "mcpRunning", "nativeAlive", "authorityReady", "centralConnected")):
        raise RuntimeError("LOCAL_RUNTIME_NOT_READY")
    scopes = readiness.get("expected_current_scopes", {})
    scope_summary = {}
    for label, scope in scopes.items():
        census = scope.get("census", {})
        binding = (scope.get("active_bindings") or [{}])[0]
        scope_summary[label] = {
            "workspace_id": binding.get("workspace_id"),
            "workspace_generation": binding.get("workspace_generation"),
            "binding_id": binding.get("binding_id"),
            "exact_scope_idle": scope.get("exact_scope_idle"),
            "census": {key: census.get(key) for key in
                        ("unclosed_tasks", "live_open_tasks", "unreleased_writers", "live_writers",
                         "unsettled_actions", "queued_actions", "active_dispatch_actions", "reconciliation_required_actions")},
        }
    return {
        "schema_version": 1,
        "operation": "native_first_production_evidence_checkpoint",
        "observed_at_ms": int(time.time() * 1000),
        "status": "production_runtime_ready_with_acceptance_gates_preserved",
        "production_activation": {
            "policy_ok": True,
            "candidate": policy.get("candidate"),
            "activation_epoch_id": policy.get("receipt", {}).get("activation_epoch_id"),
            "codex_web_execution_mode": target_policies["Codex-web"].get("policy", {}).get("execution_mode"),
            "autocad_execution_mode": target_policies["Autocad"].get("policy", {}).get("execution_mode"),
            "policy_cross_package_restoration": policy.get("receipt", {}).get("cross_package_restoration"),
        },
        "ubuntu_readiness": {
            "ok": True,
            "service_pid": readiness.get("service_pid"),
            "service_stable": readiness.get("service_stable"),
            "node_readiness": node.get("readiness"),
            "runtime_instance_id": node.get("runtime_instance_id"),
            "mcp_server_instance_id": node.get("mcp_server_instance_id"),
            "activation_epoch": node.get("activation_epoch"),
            "connector_contract_state": runtime.get("connectorContractState"),
            "connector_applicability": discovery.get("connector_applicability"),
            "scopes": scope_summary,
            "whole_device_census": select(readiness.get("whole_device_census", {}),
                ("unclosed_tasks", "unreleased_writers", "unsettled_actions", "reconciliation_required_actions")),
            "unknown_projection_truncated": readiness.get("unknown_projection_truncated"),
            "historical_unknown_count": len(readiness.get("historical_unknown_actions_preserved", [])),
        },
        "windows_readiness": {
            "activation": select(activation, ("activation_epoch_id", "state", "admission_open", "ready_commit_digest")),
            "runtime": select(runtime, ("fullyReady", "mcpRunning", "nativeAlive", "authorityReady", "centralConnected", "connectorContractState")),
            "active_job_counts": local_receipt.get("census", {}).get("counts"),
            "census_safe": local_receipt.get("census", {}).get("safe"),
            "census_code": local_receipt.get("census", {}).get("code"),
            "census_reason": local_receipt.get("census", {}).get("reason"),
        },
        "parallel_overlap": select(overlap, ("ok", "attempt_id", "observation_client_recreated", "reconnect_scope", "no_second_exec_verified", "overlap")),
        "idle_observation": select(idle, ("ok", "expected_idle_seconds", "deprovision_phase_bound_seconds", "owned_record_absent", "owned_daemon_absent", "original_owned_hosts_absent", "sandbox_named_memory_aggregate_absent", "peak_observed_sandbox_working_set_bytes", "final_sandbox_working_set_bytes", "terminal_to_teardown_ms", "limitation")),
        "native_continuation": select(joined, ("status", "semantic_acceptance_performed", "replayed_original_actions", "combined_proof_counts", "counts_derived_from_exact_unique_lanes", "distinct_proven_native_job_count", "separate_gates_not_evaluated")),
        "semantic_acceptance": select(semantic, ("ok", "source_final_audit_accepted_count", "rows_checked", "proof_waves", "checks")),
        "remaining_acceptance_gates": [
            {"gate": "autocad_unknown_reconciliation", "status": "preserved_quarantine_required"},
            {"gate": "real_dotnet_autocad_build", "status": "not_executed"},
            {"gate": "connector_contract_discovery", "status": "closed_for_central_executor", "diagnostic_state": runtime.get("connectorContractState"), "applicability": discovery.get("connector_applicability")},
            {"gate": "dedicated_idle_teardown_receipt", "status": "observation_limitation"},
        ],
        "sources": [semantic_src, overlap_src, idle_src, policy_src, readiness_src, local_ready_src, discovery_src, joined_src],
        "no_live_mutation_performed": True,
    }


def main():
    parser = argparse.ArgumentParser()
    for name in ("semantic", "overlap", "idle", "policy", "readiness", "local-ready", "discovery", "joined"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    if not output.is_absolute() or output.exists() or not output.parent.is_dir():
        raise RuntimeError("NEW_ABSOLUTE_OUTPUT_REQUIRED")
    report = build(args)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"operation": report["operation"], "status": report["status"], "output": str(output)}))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"operation": "native_first_production_evidence_checkpoint_failed", "code": str(error)}))
        raise SystemExit(1)
