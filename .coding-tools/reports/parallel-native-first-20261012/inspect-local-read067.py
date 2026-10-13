"""Exact original timeout correlations from local retained evidence; no mutation."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
PROFILE = Path(os.environ["APPDATA"]) / "web-mcp-assistant"
ACTION = "act_1de2cef3dc304d6e8b3f90237d7c136a"
ATTEMPT = "try_8d31c7cfb661441aadb9e620e47508a3"
FILE_POLICY_SHA = "b09b5cf34b6e09489aaf34431dfa6931755dd7c69d41d01bf1e3d825fd686c36"
SCOPE = {"workspace_id": "workspace_f93b5bac9dc74fae9cea66f44c4ebc94", "workspace_generation": "generation_a420c8bfcfcb4e42b5bb7fc5e5cec097"}
FACADE = {"schema_version": 32, "profile": "control-plane-private-tunnel-service-v1",
          "sha256": "3664b70740d8d7359a3605b5ce42d7cbf3329e27dcfeec27d22b23ec9c631f66"}


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":"), sort_keys=True).encode()).hexdigest()


def read(file):
    raw = file.read_bytes()
    return json.loads(raw.decode("utf-8-sig")), {"sha256": hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw)}


def main():
    output = Path(__file__).with_name(sys.argv[1])
    if output.exists() or output.parent != Path(__file__).parent:
        raise RuntimeError("NEW_ADDITIVE_REPORT_REQUIRED")
    context = "cpfr_" + digest({"action_id": ACTION, "attempt_id": ATTEMPT, "policy_sha256": FILE_POLICY_SHA,
                                **SCOPE, "facade_contract": FACADE})[:56]
    fingerprint = digest({"action_id": ACTION, "attempt_id": ATTEMPT, "policy_sha256": FILE_POLICY_SHA,
                          "path": "tests/fixtures/native-first-canary/file-067.txt", "start_line": 1,
                          "max_lines": 20, "max_bytes": 4096, "facade_contract": FACADE})
    request_ids = ["control-plane-file-read-" + phase + "-" + fingerprint[:24] for phase in ("bind", "read")]
    journal, journal_evidence = read(PROFILE / "control-plane-node.json.file-read-bridge-journal.json")
    entry = journal["entries"][ACTION + "|" + ATTEMPT]
    receipt = entry["receipt"]
    payload = receipt["payload"]
    owner, owner_evidence = read(PROFILE / "recovery-host.json")
    runtime, runtime_evidence = read(PROFILE / "runtime-state.json")
    performance, performance_evidence = read(ROOT / ".coding-tools/performance.json")
    recent = []
    for event in performance.get("recent", []):
        invocation = event.get("invocation") or {}
        if invocation.get("request_id") in request_ids or invocation.get("task_context_id") == context:
            recent.append({key: event.get(key) for key in ("tool", "started_at", "finished_at", "duration_ms", "ok", "error_class", "outcome")}
                          | {"invocation": {key: invocation.get(key) for key in ("request_id", "task_context_id", "client_id", "client_type", "invocation_id")}})
    contexts, contexts_evidence = read(ROOT / ".coding-tools/orchestration/task-context-workspaces.json")
    # Persist only exact presence/path digest; task registry may contain other roots.
    def matches(value):
        if isinstance(value, dict):
            return any(key == context or key == "mcp2026:" + context or value.get("task_context_id") == context
                       or matches(item) for key, item in value.items())
        if isinstance(value, list):
            return any(matches(item) for item in value)
        return False
    expected_unknown = entry["state"] == "unknown" and receipt["receipt_state"] == "unknown" \
        and receipt["receipt_submitted"] is True and receipt["local_handle"] == "" \
        and payload.get("diagnostic_code") == "CONTROL_PLANE_FILE_READ_TIMEOUT"
    report = {"schema_version": 1, "operation": "local_original_read067_timeout_evidence", "ok": expected_unknown,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(), "action_id": ACTION, "attempt_id": ATTEMPT,
        "read_only": True, "journal_evidence": journal_evidence,
        "journal_projection": {"state": entry["state"], "receipt_state": receipt["receipt_state"],
            "receipt_submitted": receipt["receipt_submitted"], "has_local_handle": bool(receipt["local_handle"]),
            "payload": {key: payload.get(key) for key in ("schema_version", "operation_kind", "code", "diagnostic_code")}},
        "expected_local_task_context_id": context, "expected_transport_request_ids": request_ids,
        "expected_workspace_scope": SCOPE, "file_policy_sha256": FILE_POLICY_SHA,
        "performance_evidence": performance_evidence, "matching_retained_performance_events": recent,
        "task_registry_evidence": contexts_evidence, "local_task_context_present": matches(contexts),
        "owner": {key: owner.get(key) for key in ("owner_pid", "owner_process_start_token", "instance_id", "installation_id")},
        "owner_evidence": owner_evidence, "runtime_evidence": runtime_evidence,
        "runtime": {key: runtime.get(key) for key in ("nativePid", "nativeInstanceId", "nativeActivationEpochId", "nativeProcessStartToken")},
        "proof_limit": "Recent performance events are bounded dynamic projections. Matching read completion does not repair the missing exact bounded-result receipt or turn UNKNOWN into success.",
        "journal_modified": False, "reconciliation_performed": False, "action_redispatched": False}
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"ok": expected_unknown, "report_path": str(output), "local_task_context_present": report["local_task_context_present"],
                      "matching_retained_performance_events": recent}))


if __name__ == "__main__":
    main()
