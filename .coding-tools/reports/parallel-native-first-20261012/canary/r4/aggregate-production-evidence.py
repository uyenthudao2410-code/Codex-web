"""Aggregate bounded public receipt fields offline; never creates acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parent
MAX_BYTES = 2 * 1024 * 1024


def require(value, code):
    if not value:
        raise RuntimeError(code)


def digest(value):
    return hashlib.sha256(value).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def load(file):
    path = Path(file)
    require(path.is_absolute() and path.is_file() and not path.is_symlink()
            and path.stat().st_size <= MAX_BYTES, "BOUNDED_ABSOLUTE_RECEIPT_REQUIRED")
    raw = path.read_bytes()
    text = raw.decode("utf-8-sig")
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        value = [json.loads(line) for line in text.splitlines() if line.strip()]
        require(len(value) <= 10000, "BOUNDED_RECEIPT_ROWS_REQUIRED")
    require(isinstance(value, (dict, list)), "OBJECT_RECEIPT_REQUIRED")
    return value, {"path": str(path), "sha256": digest(raw), "size_bytes": len(raw)}


def selected(value, names):
    return {name: value.get(name) for name in names}


def final(value, operation):
    if isinstance(value, dict):
        require(value.get("operation") == operation and value.get("phase") == "final", "EXACT_FINAL_RECEIPT_REQUIRED")
        return value
    matches = [row for row in value if row.get("operation") == operation and row.get("phase") == "final"]
    require(len(matches) == 1, "EXACT_SINGLE_FINAL_RECEIPT_REQUIRED")
    return matches[0]


JOB_FIELDS = ("action_id", "attempt_id", "receipt_id", "job_id", "command_id", "run_id", "wave_id",
              "execution_backend", "isolation_level", "policy_decision", "stdout_sha256", "output_bytes",
              "started_at_ms", "finished_at_ms", "duration_ms", "pid", "exit_code")
STATE_FIELDS = ("ok", "attempt_id", "observed_at_ms", "task_id", "workspace_id", "workspace_generation",
                "binding_id", "requires_reconciliation", "unresolved_original_actions",
                "task_closed_verified", "writer_released_verified", "elapsed_seconds", "error_code")


def canary(value):
    row = final(value, "native_first_shared_mcp_canary")
    proofs = row.get("proofs", {})
    require(isinstance(proofs, dict) and len(proofs) <= 200, "BOUNDED_CANARY_PROOFS_REQUIRED")
    counts = {name: sum(lane.startswith(prefix) for lane in proofs)
              for name, prefix in (("reads", "read_"), ("patches", "patch_"), ("readbacks", "readback_"),
                                   ("node_jobs", "node_"), ("git_jobs", "git_"))}
    jobs = [{"lane": lane, **selected(proof, JOB_FIELDS)} for lane, proof in proofs.items()
            if lane.startswith(("node_", "git_")) or lane == "build"]
    return {**selected(row, STATE_FIELDS), "proof_counts": counts,
            "receipt_proof_counts": row.get("proof_counts"),
            "counts_agree": counts == row.get("proof_counts") if "proof_counts" in row else None,
            "native_jobs": jobs, "distinct_native_job_count": len({job["job_id"] for job in jobs if job["job_id"]}),
            "build_proof": selected(proofs["build"], JOB_FIELDS) if "build" in proofs else None,
            "build_readback": selected(proofs["build_readback"], ("action_id", "path", "content_sha256"))
                if "build_readback" in proofs else None,
            "semantic_acceptance_performed": row.get("semantic_acceptance_performed")}


def overlap(value):
    row = final(value, "parallel_native_overlap_canary")
    targets = row.get("targets", [])
    require(isinstance(targets, list) and len(targets) <= 2, "BOUNDED_TWO_ROOT_TARGETS_REQUIRED")
    jobs = [selected(target.get("proofs", {}).get("node_overlap", {}), JOB_FIELDS) for target in targets]
    measured = None
    if len(jobs) == 2 and all(type(job.get(name)) is int for job in jobs for name in ("started_at_ms", "finished_at_ms")):
        measured = min(job["finished_at_ms"] for job in jobs) - max(job["started_at_ms"] for job in jobs)
    return {**selected(row, ("ok", "attempt_id", "observed_at_ms", "error_code", "elapsed_seconds",
                            "observation_client_recreated", "reconnect_scope", "no_second_exec_verified")),
            "reported_overlap": row.get("overlap"), "derived_overlap_duration_ms": measured,
            "positive_interval_overlap": measured > 0 if measured is not None else None,
            "distinct_native_job_count": len({job["job_id"] for job in jobs if job["job_id"]}),
            "targets": [{**selected(target, STATE_FIELDS + ("workspace_label", "retained_historical_unknown_actions")),
                         "native_job": jobs[index]} for index, target in enumerate(targets)]}


def idle(value):
    require(isinstance(value, dict) and value.get("operation") == "automatic_owned_sandbox_idle_observation",
            "EXACT_IDLE_OBSERVATION_REQUIRED")
    return {**selected(value, ("ok", "capture_started_at_ms", "capture_finished_at_ms", "sample_count",
                "error_code", "proof_kind", "expected_idle_seconds", "terminal_to_teardown_ms",
                "owned_record_absent", "owned_daemon_absent", "original_owned_hosts_absent",
                "sandbox_named_memory_aggregate_absent", "peak_observed_sandbox_working_set_bytes",
                "final_sandbox_working_set_bytes", "vm_started_by_observer", "lifecycle_mutation_performed", "limitation")),
            "runtime": value.get("runtime"), "terminal": selected(value.get("terminal", {}), JOB_FIELDS),
            "warm": selected(value.get("warm", {}), ("sandbox_id", "observed_at_ms", "record_sha256", "daemon_sha256")),
            "task_cleanup": selected(value.get("task_cleanup", {}), STATE_FIELDS)}


def policy(value):
    require(isinstance(value, dict), "POLICY_RECEIPT_REQUIRED")
    restored = value.get("operation") == "isolated-idle-policy-restore"
    receipt = value.get("receipt", value)
    targets = receipt.get("targets", [])
    require(isinstance(targets, list) and len(targets) <= 2, "BOUNDED_POLICY_TARGETS_REQUIRED")
    names = ("state", "workspace_id", "workspace_generation", "policy_sha256", "execution_mode")
    return {**selected(value, ("operation", "ok", "observed_at_ms", "candidate", "activation_epoch_id",
                              "other_scope_unchanged", "plan_sha256")),
            "restored_policy": selected(value.get("after", {}), names) if restored else None,
            "targets": [{"workspace_label": target.get("workspace_label"),
                         "policy": selected(target.get("policy", {}), names)} for target in targets]}


def ready(value):
    require(isinstance(value, dict), "READY_RECEIPT_REQUIRED")
    receipt = value.get("receipt", value)
    return {**selected(value, ("operation", "ok", "observed_at", "observed_at_ms", "candidate")),
            "runtime": selected(receipt.get("runtime", {}), ("fullyReady", "mcpRunning", "nativeAlive", "centralConnected",
                        "authorityReady", "connectorContractState", "workspace", "updateIncomplete")),
            "activation": selected(receipt.get("activation", {}), ("activation_epoch_id", "state", "admission_open", "ready_commit_digest")),
            "active_job_counts": receipt.get("census", {}).get("counts"),
            "lifecycle": selected(receipt.get("census", {}).get("lifecycle", {}), ("unexplained_active_runs",
                        "unbound_live_resource_residues", "awaiting_acceptance_runs", "live_owned_runs"))}


def server(value):
    require(isinstance(value, dict), "SERVER_RECEIPT_REQUIRED")
    scopes = value.get("expected_current_scopes", {})
    require(isinstance(scopes, dict) and len(scopes) <= 2, "BOUNDED_SERVER_SCOPES_REQUIRED")
    return {**selected(value, ("ok", "capture_completed_at_ms", "service_pid", "service_stable", "sqlite_integrity_ok",
            "source_startup_disk_attestation_matches", "tool_contract", "whole_device_census", "unknown_projection_truncated")),
            "node": selected(value.get("node", {}), ("readiness", "last_seen_at_ms", "activation_epoch", "runtime_instance_id", "mcp_server_instance_id")),
            "serving_source": selected(value.get("serving_source", {}), ("serving_release_root", "package_source_sha256", "release_file_integrity_verified")),
            "scopes": {name: selected(scope, ("expected_workspace_id", "expected_generation", "active_bindings",
                         "active_registrations", "delegated_inventory_targets", "census", "exact_scope_idle"))
                       for name, scope in scopes.items()}}


def unknowns(before, after):
    require(isinstance(before, dict) and isinstance(after, dict), "UNKNOWN_RECEIPTS_REQUIRED")
    rows = before.get("historical_unknown_actions_preserved")
    current = after.get("historical_unknown_actions_preserved")
    if not isinstance(rows, list) or not isinstance(current, list):
        return {"preserved_prior_history": None, "reason": "Exact before/after history rows are absent",
                "before_declared_history_sha256": before.get("immutable_history_sha256"),
                "after_declared_history_sha256": after.get("immutable_history_sha256")}
    require(len(rows) <= 100 and len(current) <= 100 and before.get("unknown_projection_truncated") is False
            and after.get("unknown_projection_truncated") is False, "COMPLETE_BOUNDED_UNKNOWN_PROJECTIONS_REQUIRED")
    names = ("action_id", "binding_id", "workspace_id", "workspace_generation", "tool_name", "delivery_state",
             "created_at_ms", "expires_at_ms", "settled_at_ms", "task_id", "delivery_attempts", "receipts")
    previous = {row["action_id"]: selected(row, names) for row in rows}
    latest = {row["action_id"]: selected(row, names) for row in current}
    require(len(previous) == len(rows) and len(latest) == len(current), "UNIQUE_UNKNOWN_ACTIONS_REQUIRED")
    compared = [{"action_id": action, "before_sha256": digest(canonical(row)),
                 "after_sha256": digest(canonical(latest[action])) if action in latest else None,
                 "preserved": action in latest and row == latest[action]} for action, row in previous.items()]
    return {"preserved_prior_history": all(row["preserved"] for row in compared) if compared else None,
            "prior_sample_count": len(compared), "comparisons": compared,
            "additional_current_unknown_action_ids": sorted(set(latest) - set(previous))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canary", action="append", default=[])
    for name in ("overlap", "idle", "policy", "ready", "server", "parity", "semantic", "unknown-before", "unknown-after", "git-job-state"):
        parser.add_argument("--" + name)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    require(output.is_absolute() and output.parent.resolve() == ROOT and not output.exists(), "NEW_LOCAL_AGGREGATE_REQUIRED")
    report = {"schema_version": 1, "operation": "production_evidence_aggregation", "observed_at_ms": int(time.time() * 1000),
              "scope": "Offline receipt aggregation; no live acceptance or external mutation", "sources": {}, "canaries": []}
    for file in args.canary:
        value, source = load(file)
        report["sources"][source["path"]] = source
        report["canaries"].append(canary(value))
    require(len({row["attempt_id"] for row in report["canaries"]}) == len(report["canaries"]), "DUPLICATE_ATTEMPT_NOT_COUNTED")
    raw = {}
    for name in ("overlap", "idle", "policy", "ready", "server", "parity", "semantic", "unknown_before", "unknown_after", "git_job_state"):
        file = getattr(args, name)
        if file:
            raw[name], source = load(file)
            report["sources"][source["path"]] = source
    for name, formatter in (("overlap", overlap), ("idle", idle), ("policy", policy), ("ready", ready), ("server", server)):
        report[name] = formatter(raw[name]) if name in raw else None
    report["package"] = selected(raw["parity"], ("ok", "proof_kind", "git_head", "candidate", "executable_sha256",
            "app_asar_sha256", "application_code_files", "resource_proof", "adapter_proof")) if "parity" in raw else None
    report["semantic"] = selected(raw["semantic"], ("ok", "operation", "observed_at", "accepted_count", "acceptance_performed",
            "original_actions_replayed", "production_descriptor_stable", "blockers", "code")) if "semantic" in raw else None
    report["unknown_history"] = unknowns(raw["unknown_before"], raw["unknown_after"]) if "unknown_before" in raw and "unknown_after" in raw else None
    report["git_job_state"] = selected(raw["git_job_state"], ("observed_at", "observed_at_ms", "git_head", "branch",
            "dirty", "dirty_path_count", "conflict_path_count", "active_job_counts", "push_performed", "commit_performed")) if "git_job_state" in raw else None
    report["missing_inputs"] = [name for name in ("overlap", "idle", "policy", "ready", "server", "package", "semantic", "unknown_history", "git_job_state") if report[name] is None]
    if not report["canaries"]:
        report["missing_inputs"].append("canary")
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(json.dumps({"operation": report["operation"], "report_path": str(output), "canary_attempt_count": len(report["canaries"]),
                      "missing_inputs": report["missing_inputs"]}))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"operation": "production_evidence_aggregation_failed",
                          "code": str(error) if isinstance(error, RuntimeError) else type(error).__name__}))
        sys.exit(1)
