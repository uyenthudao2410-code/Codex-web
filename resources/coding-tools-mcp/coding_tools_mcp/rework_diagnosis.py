from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from .ledger_analysis import LedgerFacts


WORKFLOW_ORDER = ("feature", "diagnose", "bugfix", "test_failure", "build_release", "custom", "refactor")
P2_FAILURE_OBSERVATION_SCHEMA = "p2_failure_observation_v3"
P2_GENERIC_FAILURE_CLASSES = frozenset({"CHECK_FAILED", "BUILD_VERIFICATION_FAILED"})
P2_REQUEST_CONTROL_SHAPE_FAILURE_CLASSES = frozenset({
    "EXISTING_FILE_ADOPTION_PREEXISTING_DIRTY_REQUIRED",
    "INVALID_ARGUMENT",
    "MODE_ROUTE_MISMATCH",
})
P2_REQUEST_CONTROL_SHAPE_CAUSE = "request_contract_correction"
P2_PERMISSION_REASONS = frozenset({
    "destructive_command",
    "filesystem_escape",
    "inline_script",
    "network",
    "privileged_executable",
    "sensitive_env",
    "shell_expansion",
})
P2_CHECK_COMMAND_FAMILIES = frozenset({
    "cargo_test",
    "go_test",
    "node_test",
    "pytest",
    "python_unittest",
    "java_test",
    "dotnet_test",
    "lint",
    "format",
    "typecheck",
    "other",
})
P2_BUILD_VERIFICATION_STAGES = frozenset({
    "test_command_failed",
    "build_command_failed",
    "build_command_missing",
    "artifact_missing",
    "verification_unspecified",
})
P2_ENGINEERING_ACTIVE_PHASE_KEYS = (
    "preflight_ms",
    "ready_wait_ms",
    "dispatch_window_ms",
    "execution_window_ms",
    "proof_ms",
)
REPAIR_CAUSE_CODES = {
    "patch_context_ambiguity": {
        "PATCH_AMBIGUOUS",
        "PATCH_CONTEXT_AMBIGUOUS",
        "PATCH_CONTEXT_NOT_FOUND",
        "PATCH_HUNKS_OVERLAP",
    },
    "source_base_drift": {"ACCEPTANCE_FILE_SHA_MISMATCH", "BASE_DRIFT", "CONTRACT_DRIFT"},
    "environment_workdir": {"NOT_A_DIRECTORY", "RUNTIME_DIR_UNWRITABLE"},
    "runtime_tool_failure": {
        "BACKGROUND_OPERATION_FAILED",
        "RUNTIME_ACTIVATION_PENDING",
        "RUNTIME_BUSY",
        "RUNTIME_RESUME_REQUIRED",
        "SEMANTIC_PROVIDER_CALL_FAILED",
        "SEMANTIC_PROVIDER_STATUS_FAILED",
        "WORKFLOW_RUNTIME_EXCEEDED",
    },
    "provider_capacity": {"CAPACITY", "CODEX_CAPACITY", "MODEL_CAPACITY_COOLDOWN", "OPENCODE_PROVIDER_CAPACITY"},
    "proof_timeout": {"PROOF_TIMEOUT"},
    "acceptance_correction": {"SOL_REJECTED"},
}
PLANNED_REPAIR_CAUSES = (
    "patch_context_ambiguity",
    "source_base_drift",
    "wrong_root_cause",
    "oracle_weakness",
    "environment_workdir",
    P2_REQUEST_CONTROL_SHAPE_CAUSE,
    "runtime_tool_failure",
    "missing_requirement",
    "provider_capacity",
    "proof_timeout",
    "acceptance_correction",
)


def _normalized_text(value: object) -> str:
    return " ".join(str(value or "").lower().split())


def p2_check_failure_detail(command: object) -> dict[str, str]:
    """Return bounded, content-free prospective detail for a failed explicit check.

    This is a measurement label, not a root-cause or repair label.  In
    particular, it never persists the command, output, path, or a free-text
    failure message.
    """
    text = _normalized_text(command)
    if "pytest" in text:
        family = "pytest"
    elif "unittest" in text:
        family = "python_unittest"
    elif "cargo test" in text:
        family = "cargo_test"
    elif "go test" in text:
        family = "go_test"
    elif "dotnet test" in text:
        family = "dotnet_test"
    elif "mvn test" in text or "gradle test" in text:
        family = "java_test"
    elif any(marker in text for marker in ("eslint", "clippy", "lint")):
        family = "lint"
    elif any(marker in text for marker in ("rustfmt", "prettier", "black --check", "gofmt")):
        family = "format"
    elif any(marker in text for marker in ("tsc", "mypy", "pyright", "typecheck")):
        family = "typecheck"
    elif any(marker in text for marker in ("npm test", "pnpm test", "yarn test", "vitest", "jest")):
        family = "node_test"
    else:
        family = "other"
    detail = {
        "schema": P2_FAILURE_OBSERVATION_SCHEMA,
        "stage": "checks",
        "command_family": family,
        "causal_attribution": "unattributed",
    }
    if family == "other":
        detail["unknown_reason"] = "unrecognized_command_family"
    return detail


def p2_build_verification_failure_detail(report: object, verification: object) -> dict[str, str]:
    """Return bounded, content-free prospective detail for failed verification."""
    value = report if isinstance(report, dict) else {}
    test_result = value.get("test_result") if isinstance(value.get("test_result"), dict) else {}
    build_result = value.get("build_result") if isinstance(value.get("build_result"), dict) else {}
    commands = value.get("commands") if isinstance(value.get("commands"), dict) else {}
    artifacts = value.get("artifacts") if isinstance(value.get("artifacts"), list) else []
    test_status = _normalized_text(test_result.get("status"))
    build_status = _normalized_text(build_result.get("status"))
    if test_status == "failed":
        failure_stage = "test_command_failed"
    elif build_status == "failed":
        failure_stage = "build_command_failed"
    elif not _normalized_text(commands.get("build")):
        failure_stage = "build_command_missing"
    elif build_status == "passed" and not artifacts:
        failure_stage = "artifact_missing"
    else:
        failure_stage = "verification_unspecified"
    mode = _normalized_text(verification)
    detail = {
        "schema": P2_FAILURE_OBSERVATION_SCHEMA,
        "stage": "verification",
        "verification_mode": mode if mode in {"tests", "build", "all"} else "unknown",
        "verification_failure_stage": failure_stage,
        "causal_attribution": "unattributed",
    }
    if failure_stage == "verification_unspecified":
        detail["unknown_reason"] = "verification_evidence_insufficient"
    return detail


def p2_permission_failure_detail(failure_class: object, details: object) -> dict[str, str] | None:
    """Project an allowlisted permission discriminator without raw command/path text."""
    if str(failure_class or "").strip().upper() != "PERMISSION_REQUIRED":
        return None
    value = details if isinstance(details, dict) else {}
    permission = str(value.get("permission") or "").strip().lower()
    if permission not in P2_PERMISSION_REASONS:
        return None
    return {
        "schema": P2_FAILURE_OBSERVATION_SCHEMA,
        "stage": "permission_policy",
        "permission_reason": permission,
        "causal_attribution": "unattributed",
    }


def p2_failure_detail_bucket(failure_class: object, detail: object) -> str | None:
    """Validate and render a prospective generic-failure detail bucket.

    Historical rows that predate the v3 schema intentionally return ``None``;
    callers must report them as unavailable rather than infer a detail later.
    """
    failure = str(failure_class or "").strip().upper()
    value = detail if isinstance(detail, dict) else {}
    if value.get("schema") != P2_FAILURE_OBSERVATION_SCHEMA:
        return None
    if value.get("causal_attribution") != "unattributed":
        return None
    if failure == "CHECK_FAILED" and value.get("stage") == "checks":
        family = str(value.get("command_family") or "")
        if family in P2_CHECK_COMMAND_FAMILIES and (
            (family != "other" and "unknown_reason" not in value)
            or (family == "other" and value.get("unknown_reason") == "unrecognized_command_family")
        ):
            return f"{failure}:{family}"
    if failure == "BUILD_VERIFICATION_FAILED" and value.get("stage") == "verification":
        stage = str(value.get("verification_failure_stage") or "")
        if stage in P2_BUILD_VERIFICATION_STAGES and (
            (stage != "verification_unspecified" and "unknown_reason" not in value)
            or (stage == "verification_unspecified" and value.get("unknown_reason") == "verification_evidence_insufficient")
        ):
            return f"{failure}:{stage}"
    if failure == "PERMISSION_REQUIRED" and value.get("stage") == "permission_policy":
        expected_keys = {"schema", "stage", "permission_reason", "causal_attribution"}
        permission = str(value.get("permission_reason") or "")
        if set(value) == expected_keys and permission in P2_PERMISSION_REASONS:
            return f"{failure}:{permission}"
    return None


def _generic_failure_proof_link(
    failure_class: str,
    event: dict[str, Any],
    proofs: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, str]:
    """Link a generic failure only through an exact durable proof key."""
    payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
    wave_id = str(event.get("wave_id") or "").strip()
    if not wave_id:
        return None, "missing_exact_key"
    failed = [
        proof for proof in proofs
        if str(proof.get("wave_id") or "") == wave_id
        and str(proof.get("status") or "").strip().lower() == "failed"
    ]
    normalized = str(failure_class or "").strip().upper()
    if normalized == "CHECK_FAILED":
        command_hash = str(payload.get("command_hash") or "").strip()
        if not command_hash:
            return None, "missing_exact_key"
        candidates = [proof for proof in failed if str(proof.get("command_hash") or "") == command_hash]
        exact_link = "exact_wave_command_hash"
    elif normalized == "BUILD_VERIFICATION_FAILED":
        verification = _normalized_text(payload.get("verification"))
        if verification not in {"tests", "build", "all"}:
            return None, "missing_exact_key"
        stage_id = f"verify:{verification}"
        candidates = [proof for proof in failed if str(proof.get("stage_id") or "") == stage_id]
        exact_link = "exact_wave_verify_stage"
    else:
        return None, "not_applicable"
    if len(candidates) == 1:
        return candidates[0], exact_link
    if not candidates:
        return None, "missing_exact_proof"
    return None, "ambiguous_exact_proof"


def _generic_process_outcome(
    failure_class: str,
    payload: dict[str, Any],
    proof: dict[str, Any],
) -> str | None:
    """Project content-free process outcome without assigning semantic cause."""
    normalized = str(failure_class or "").strip().upper()
    if normalized == "CHECK_FAILED":
        exit_code = proof.get("exit_code")
        if not isinstance(exit_code, int) or isinstance(exit_code, bool):
            return None
        return "CHECK_FAILED:process_exit_zero" if exit_code == 0 else "CHECK_FAILED:process_exit_nonzero"
    if normalized != "BUILD_VERIFICATION_FAILED":
        return None
    detail = payload.get("p2_failure_detail") if isinstance(payload.get("p2_failure_detail"), dict) else {}
    if detail.get("schema") != P2_FAILURE_OBSERVATION_SCHEMA or detail.get("causal_attribution") != "unattributed":
        return None
    failure_stage = str(detail.get("verification_failure_stage") or "")
    result_key = {
        "test_command_failed": "test_result",
        "build_command_failed": "build_result",
    }.get(failure_stage)
    if result_key is None:
        return None
    metadata = proof.get("metadata") if isinstance(proof.get("metadata"), dict) else {}
    result = metadata.get("result") if isinstance(metadata.get("result"), dict) else {}
    selected = result.get(result_key) if isinstance(result.get(result_key), dict) else {}
    if _normalized_text(selected.get("status")) != "failed":
        return None
    exit_code = selected.get("exit_code")
    if not isinstance(exit_code, int) or isinstance(exit_code, bool):
        return None
    exit_bucket = "process_exit_zero" if exit_code == 0 else "process_exit_nonzero"
    return f"BUILD_VERIFICATION_FAILED:{failure_stage}:{exit_bucket}"


def _percentile(values: list[int], percentile: int) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, min(len(ordered), (len(ordered) * percentile + 99) // 100))
    return int(ordered[rank - 1])


def _phase_timing_observation(economics: object) -> dict[str, int | None] | None:
    """Project complete EOCL phase timing without relabeling it as model latency.

    ``engineering_active_ms`` is deliberately limited to lifecycle stages where
    the engineering packet is being prepared, dispatched, executed, or proven.
    ACCEPTING wait and REPLAN occupancy are reported separately because either
    may include operator/runtime/external delay that the ledger cannot causally
    attribute.
    """
    value = economics if isinstance(economics, dict) else {}
    phase_timing = value.get("phase_timing") if isinstance(value.get("phase_timing"), dict) else {}
    if not phase_timing.get("complete"):
        return None
    methodology = (
        phase_timing.get("methodology_phase_ms")
        if isinstance(phase_timing.get("methodology_phase_ms"), dict)
        else {}
    )
    active_values: list[int] = []
    for key in P2_ENGINEERING_ACTIVE_PHASE_KEYS:
        phase_ms = methodology.get(key)
        if not isinstance(phase_ms, int) or isinstance(phase_ms, bool) or phase_ms < 0:
            return None
        active_values.append(phase_ms)
    accept_wait_ms = methodology.get("accept_wait_ms")
    if not isinstance(accept_wait_ms, int) or isinstance(accept_wait_ms, bool) or accept_wait_ms < 0:
        return None
    replan_ms = methodology.get("replan_ms")
    if replan_ms is not None and (
        not isinstance(replan_ms, int) or isinstance(replan_ms, bool) or replan_ms < 0
    ):
        return None
    return {
        "engineering_active_ms": sum(active_values),
        "accept_wait_ms": accept_wait_ms,
        "replan_ms": replan_ms,
    }


def _workflow_name(metadata: dict[str, Any]) -> str:
    workflow = str(metadata.get("workflow") or "").strip().lower()
    return workflow if workflow in WORKFLOW_ORDER else "unknown"


def repair_cause_for_failure_class(failure_class: str) -> str | None:
    """Map a durable structured failure class to the existing rework cause taxonomy."""
    normalized = str(failure_class or "").strip().upper()
    for cause, codes in REPAIR_CAUSE_CODES.items():
        if normalized in codes:
            return cause
    return None


def p2_repair_cause_for_failure_class(failure_class: str) -> str | None:
    """Extend P2 diagnosis only where the typed failure class is itself causal."""
    cause = repair_cause_for_failure_class(failure_class)
    if cause is not None:
        return cause
    normalized = str(failure_class or "").strip().upper()
    if normalized in P2_REQUEST_CONTROL_SHAPE_FAILURE_CLASSES:
        return P2_REQUEST_CONTROL_SHAPE_CAUSE
    return None


def p2_request_contract_cause_from_replan_reason(
    failure_class: object,
    reason: object,
) -> tuple[str | None, str | None]:
    """Map only evidence-backed permission/protected-path strategy corrections.

    The guard failure itself is not causal: PERMISSION_REQUIRED and
    PROTECTED_PATH_WRITE are expected fail-closed policy outcomes.  P2 may
    attribute avoidable request-shape rework only when the index-paired durable
    ``wave_replanned`` reason proves that the subsequent strategy changed to a
    workspace-safe/supported alternative.  Missing or permission-seeking-only
    reasons therefore remain unknown.
    """
    failure = str(failure_class or "").strip().upper()
    if failure not in {"PERMISSION_REQUIRED", "PROTECTED_PATH_WRITE"}:
        return (None, None)
    text = _normalized_text(reason)
    if not text:
        return (None, None)

    if failure == "PROTECTED_PATH_WRITE":
        protected_marker = any(
            marker in text
            for marker in ("protected_path_write", "protected-path", "protected path")
        )
        supported_strategy = any(
            marker in text
            for marker in (
                "legal public-surface strategy",
                "supported public-surface strategy",
                "supported source strategy",
                "supported write strategy",
            )
        )
        if protected_marker and supported_strategy:
            return (P2_REQUEST_CONTROL_SHAPE_CAUSE, "protected_path_strategy_correction")
        return (None, None)

    filesystem_marker = any(
        marker in text
        for marker in (
            "filesystem_escape",
            "filesystem escape",
            "parent traversal",
            "parent-traversal",
        )
    )
    workspace_safe_strategy = any(
        marker in text
        for marker in (
            "repository root",
            "repo root",
            "workspace root",
            "workspace-relative",
            "workspace relative",
            "workspace-safe",
            "without parent traversal",
            "without parent-path",
            "without parent path",
        )
    )
    if filesystem_marker and workspace_safe_strategy:
        return (P2_REQUEST_CONTROL_SHAPE_CAUSE, "permission_filesystem_escape_strategy_correction")

    inline_marker = any(
        marker in text
        for marker in ("inline_script", "inline script", "inline python", "python -c")
    )
    supported_command_strategy = any(
        marker in text
        for marker in (
            "remove inline",
            "existing repository",
            "existing script",
            "supported read-only powershell",
            "supported powershell",
            "replace with powershell",
            "replace the inline",
        )
    )
    if inline_marker and supported_command_strategy:
        return (P2_REQUEST_CONTROL_SHAPE_CAUSE, "permission_inline_script_strategy_correction")

    network_marker = any(
        marker in text
        for marker in ("network_permission_required", "network permission", "network access", "http/network")
    )
    removed_network_probe = any(
        marker in text
        for marker in ("remove all http/network", "removes all http/network", "without network")
    )
    local_evidence_strategy = any(
        marker in text
        for marker in ("os-local", "os local", "local os", "local-only", "local only")
    )
    if network_marker and removed_network_probe and local_evidence_strategy:
        return (P2_REQUEST_CONTROL_SHAPE_CAUSE, "permission_network_probe_strategy_correction")
    return (None, None)


def high_confidence_replan_reason_category(reason: Any) -> tuple[str | None, str | None]:
    """Classify only durable replan reasons covered by narrow evidence-backed rules."""
    text = " ".join(str(reason or "").strip().lower().split())
    if not text:
        return (None, None)
    if "rustfmt" in text and "formatting-only" in text:
        return ("formatting_only_repair", "rustfmt_formatting_only")
    if "oracle selection" in text and "cargo package" in text and "binary target name" in text:
        return ("oracle_selection_repair", "cargo_binary_name_used_as_package")
    baseline_markers = (
        "19 unrelated", "19 errors", "compute_placement_policy", "broken root lib-test harness",
    )
    if any(marker in text for marker in baseline_markers) and (
        "unrelated" in text or "known" in text or "root lib-test" in text or "cfg(test)" in text
    ):
        return ("environment_or_baseline_repair", "known_unrelated_test_baseline")
    if "wrong root cause" in text:
        return ("causal_solution_repair", "explicit_wrong_root_cause")
    if "missing requirement" in text:
        return ("causal_solution_repair", "explicit_missing_requirement")
    if "supervisor_not_ready" in text or "provider capacity" in text:
        return ("orchestration_repair", "explicit_orchestration_failure")
    return (None, None)


def p2_generic_replan_reason_category(
    failure_class: object,
    reason: object,
) -> tuple[str | None, str | None]:
    """Classify only generic P2 failures with exact paired durable reason evidence.

    CHECK_FAILED and BUILD_VERIFICATION_FAILED are deliberately non-causal by
    themselves.  These rules therefore consume only the index-paired durable
    ``wave_replanned`` reason and require narrow corroborating markers for the
    strategy or implementation correction.  Permission/protected failures and
    every other failure class are rejected before text classification.
    """
    failure = str(failure_class or "").strip().upper()
    if failure not in P2_GENERIC_FAILURE_CLASSES:
        return (None, None)

    existing = high_confidence_replan_reason_category(reason)
    if existing != (None, None):
        return existing

    text = _normalized_text(reason)
    if not text:
        return (None, None)

    workdir_marker = any(
        marker in text
        for marker in (
            "workdir",
            "working directory",
            "repository root",
            "repo root",
            "component cwd",
            "package cwd",
        )
    )
    proof_marker = any(
        marker in text
        for marker in ("proof", "verification", "oracle", "pytest", "test command")
    )
    invocation_failure_marker = any(
        marker in text
        for marker in (
            "not importable",
            "import error",
            "import failure",
            "file-not-found",
            "file not found",
            "invocation error",
            "oracle/workdir defect",
        )
    )
    workdir_correction_marker = any(
        marker in text
        for marker in (
            "change proof workdir",
            "change only verification workdir",
            "verification workdir",
            "rerun from",
            "re-run from",
            "rerun the proof from",
            "rerun python proof from",
        )
    )
    if workdir_marker and proof_marker and invocation_failure_marker and workdir_correction_marker:
        return ("oracle_selection_repair", "verification_workdir_correction")

    cleanup_marker = any(
        marker in text
        for marker in (
            "temp-tree",
            "temp tree",
            "temp cleanup",
            "temporary directory",
            "cleanup",
            "teardown",
            "rmsync",
            "removetemptree",
        )
    )
    contention_evidence = any(
        marker in text
        for marker in (
            "contention",
            "parallel",
            "serial",
            "isolated",
            "unrelated",
            "nondeterministic",
            "file-lock",
            "file lock",
            "assertion",
        )
    )
    if "eperm" in text and cleanup_marker and contention_evidence:
        return ("environment_or_baseline_repair", "windows_temp_cleanup_contention")

    module_size_marker = "module-size" in text or "module size" in text
    module_guard_marker = "guard" in text or "budget" in text
    extraction_marker = any(
        marker in text
        for marker in ("extract", "dedicated module", "domain module", "move the projection", "move helpers")
    )
    if module_size_marker and module_guard_marker and extraction_marker:
        return ("causal_solution_repair", "module_size_architecture_correction")

    command_too_long = "command line is too long" in text or "command-line is too long" in text
    split_marker = "split" in text and any(marker in text for marker in ("bounded", "sequential", "commands", "steps"))
    if command_too_long and split_marker:
        return ("oracle_selection_repair", "windows_command_line_split")

    fsync_descriptor_marker = any(
        marker in text
        for marker in ("writable descriptor", "writable file descriptor", "o_rdwr")
    )
    fsync_failure_marker = any(
        marker in text
        for marker in ("errno 9", "bad file descriptor", "windows", "_commit")
    )
    if "fsync" in text and fsync_descriptor_marker and fsync_failure_marker:
        return ("causal_solution_repair", "windows_fsync_writable_descriptor")

    expectation_marker = "test expectation" in text or "regression expectation" in text
    if expectation_marker and "toolfailure" in text and "jsonrpcerror" in text:
        return ("oracle_selection_repair", "public_validation_exception_expectation")

    return (None, None)


def _repair_cause(failure_class: str) -> str | None:
    return p2_repair_cause_for_failure_class(failure_class)


def _scope_observation(events: list[dict[str, Any]]) -> tuple[int | None, bool]:
    selected: set[str] = set()
    observed = False
    censored = False
    for event in events:
        if event.get("event_type") != "context_prepared":
            continue
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        paths = payload.get("selected_paths")
        if not isinstance(paths, list):
            continue
        observed = True
        normalized = [str(item).strip() for item in paths if str(item).strip()]
        selected.update(normalized)
        if len(paths) >= 40:
            censored = True
    if not observed:
        return None, False
    return len(selected), censored


def _oracle_observation(events: list[dict[str, Any]]) -> bool | None:
    values: list[bool] = []
    for event in events:
        if event.get("event_type") != "oracle_preflight":
            continue
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        if isinstance(payload.get("strong_oracle"), bool):
            values.append(bool(payload["strong_oracle"]))
    if not values:
        return None
    return any(values)


def _countermeasure_report(
    *,
    repair_events: dict[str, int],
    affected_runs: dict[str, int],
    preflight_avoided: dict[str, Any],
) -> list[dict[str, Any]]:
    definitions = (
        ("patch_preflight", "patch_context_ambiguity"),
        ("workdir_resolution", "environment_workdir"),
        ("semantic_localization", "runtime_tool_failure"),
        ("exact_source", "source_base_drift"),
        ("recovery_fencing", "runtime_tool_failure"),
        ("solution_minimization_later", None),
    )
    result: list[dict[str, Any]] = []
    for name, category in definitions:
        active_later = name == "solution_minimization_later"
        direct_evidence: dict[str, Any] = {"status": "not_directly_attributed"}
        if name == "patch_preflight":
            direct_evidence = {
                "status": "guardrail_observed",
                "preflight_avoided_count": int(preflight_avoided.get("count") or 0),
                "error_codes": dict(preflight_avoided.get("error_codes") or {}),
                "meaning": "known no-write patch failures stopped before orchestration run creation",
            }
        elif active_later:
            direct_evidence = {"status": "not_active_in_p2"}
        current = {
            "repair_cause_events": int(repair_events.get(category, 0)) if category else None,
            "affected_repaired_runs": int(affected_runs.get(category, 0)) if category else None,
        }
        result.append({
            "intervention": name,
            "monitored_repair_category": category,
            "baseline": {"status": "missing_comparable_pre_intervention_epoch"},
            "intervention_evidence": direct_evidence,
            "fresh_rerun": current,
            "effect_estimate": None,
            "status": "not_active" if active_later else "hold_not_causally_estimable",
            "hold_reasons": (
                ["intervention_not_active_in_p2"]
                if active_later
                else ["no_comparable_pre_intervention_cohort", "no_frozen_activation_epoch_for_effect_estimation"]
            ),
        })
    return result


def stratified_rework_diagnosis(ledger: LedgerFacts, *, limit: int = 5000) -> dict[str, Any]:
    """Diagnose accepted-result rework from one immutable, decoded fact set."""
    bounded_limit = max(1, min(int(limit), 5000))
    candidate_rows: list[dict[str, Any]] = []
    for run in ledger._runs.values():
        metadata = run.get("metadata") if isinstance(run.get("metadata"), dict) else {}
        evaluation = metadata.get("evaluation") if isinstance(metadata.get("evaluation"), dict) else {}
        if run.get("status") != "accepted":
            continue
        if str(evaluation.get("provenance") or "").lower() not in {"", "representative"}:
            continue
        if str(evaluation.get("policy") or "").lower() not in {"", "chatweb_mcp"}:
            continue
        candidate_rows.append(dict(run))
    candidate_rows.sort(key=lambda item: (str(item.get("started_at") or ""), str(item.get("run_id") or "")))
    truncated = len(candidate_rows) > bounded_limit
    selected = candidate_rows[:bounded_limit]

    preflight_errors: Counter[str] = Counter()
    decoded_scalar_mismatch_rows = 0
    decoded_preflight_rows = 0
    legacy_plain_scalar_unavailable_rows = 0
    legacy_plain_decoded_preflight_rows = 0
    current_plain_decoded_preflight_rows = 0
    compressed_decoded_preflight_rows = 0
    for row in ledger.idempotency_records:
        if str(row.get("operation") or "") != "agent_workflow" or str(row.get("status") or "") != "failed":
            continue
        summary = row.get("summary") if isinstance(row.get("summary"), dict) else {}
        decoded_preflight = summary.get("workflow_patch_preflight") in {True, 1}
        scalar_preflight = row.get("workflow_patch_preflight") in {True, 1}
        decoded_error_code = str(summary.get("error_code") or "unknown")
        scalar_error_code = str(row.get("error_code") or "")
        codec = str(row.get("summary_codec") or "plain_json")
        scalar_projection_available = bool(scalar_error_code) or scalar_preflight
        legacy_plain_scalar_unavailable = codec == "plain_json" and not scalar_projection_available
        if legacy_plain_scalar_unavailable:
            legacy_plain_scalar_unavailable_rows += 1
            if decoded_preflight:
                legacy_plain_decoded_preflight_rows += 1
                decoded_preflight_rows += 1
                preflight_errors[decoded_error_code] += 1
            continue
        if decoded_preflight != scalar_preflight or scalar_error_code != decoded_error_code:
            decoded_scalar_mismatch_rows += 1
            continue
        if decoded_preflight:
            decoded_preflight_rows += 1
            if codec == "zlib_json":
                compressed_decoded_preflight_rows += 1
            else:
                current_plain_decoded_preflight_rows += 1
            preflight_errors[decoded_error_code] += 1
    preflight_avoided = {
        "count": sum(preflight_errors.values()),
        "error_codes": dict(sorted(preflight_errors.items())),
        "projection": "decoded_scalar_v1",
        "decoded_preflight_rows": decoded_preflight_rows,
        "decoded_scalar_mismatch_rows": decoded_scalar_mismatch_rows,
        "mismatched_rows_excluded": decoded_scalar_mismatch_rows > 0,
        "legacy_plain_scalar_unavailable_rows": legacy_plain_scalar_unavailable_rows,
        "legacy_plain_decoded_preflight_rows": legacy_plain_decoded_preflight_rows,
        "current_plain_decoded_preflight_rows": current_plain_decoded_preflight_rows,
        "compressed_decoded_preflight_rows": compressed_decoded_preflight_rows,
    }

    buckets: dict[str, dict[str, Any]] = {}
    overall_failure_classes: Counter[str] = Counter()
    overall_cause_events: Counter[str] = Counter({cause: 0 for cause in PLANNED_REPAIR_CAUSES})
    overall_cause_runs: dict[str, set[str]] = defaultdict(set)
    overall_unclassified: Counter[str] = Counter()
    overall_prospective_failure_details: Counter[str] = Counter()
    overall_legacy_generic_detail_unavailable: Counter[str] = Counter()
    overall_reason_categories: Counter[str] = Counter()
    overall_reason_rules: Counter[str] = Counter()
    overall_classification_sources: Counter[str] = Counter()
    overall_direct_structured_mapped = 0
    overall_reason_fallback_structured = 0
    overall_reason_fallback_events = 0
    overall_unclassified_replan_events = 0
    overall_generic_process_eligible = 0
    overall_generic_process_observed = 0
    overall_generic_process_eligible_by_class: Counter[str] = Counter()
    overall_generic_process_observed_by_class: Counter[str] = Counter()
    overall_generic_process_linkage: Counter[str] = Counter()
    overall_generic_process_outcomes: Counter[str] = Counter()
    explicit_model_route = 0

    def bucket(workflow: str) -> dict[str, Any]:
        if workflow not in buckets:
            buckets[workflow] = {
                "n": 0,
                "first_pass": 0,
                "repaired": 0,
                "replans": 0,
                "all_ttar": [],
                "first_ttar": [],
                "repaired_ttar": [],
                "phase_timing_observed": 0,
                "phase_timing_unknown": 0,
                "all_engineering_active": [],
                "first_engineering_active": [],
                "repaired_engineering_active": [],
                "all_accept_wait": [],
                "first_accept_wait": [],
                "repaired_accept_wait": [],
                "all_replan_time": [],
                "repaired_replan_time": [],
                "failure_classes": Counter(),
                "cause_events": Counter({cause: 0 for cause in PLANNED_REPAIR_CAUSES}),
                "cause_runs": defaultdict(set),
                "unclassified": Counter(),
                "prospective_failure_details": Counter(),
                "legacy_generic_detail_unavailable": Counter(),
                "reason_categories": Counter(),
                "reason_rules": Counter(),
                "classification_sources": Counter(),
                "scope_values": [],
                "scope_observed": 0,
                "scope_unknown": 0,
                "scope_censored": 0,
                "oracle_observed": 0,
                "oracle_strong": 0,
                "oracle_not_strong": 0,
                "oracle_unknown": 0,
            }
        return buckets[workflow]

    for row in selected:
        run_id = str(row["run_id"])
        actual_routes = {
            str(delegation.get("route_resolved") or "").strip().lower()
            for wave in ledger.list_waves(run_id)
            for delegation in ledger.list_delegations(str(wave["wave_id"]))
            if str(delegation.get("route_resolved") or "").strip()
        }
        if any(route not in {"unknown", "deterministic", "mcp_deterministic"} for route in actual_routes):
            explicit_model_route += 1
            continue
        economics = ledger.accepted_result_economics(run_id)
        route = str((economics.get("route") or {}).get("resolved") or "unknown").strip().lower()
        if route not in {"", "unknown", "deterministic", "mcp_deterministic"}:
            explicit_model_route += 1
            continue
        metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
        workflow = _workflow_name(metadata)
        target = bucket(workflow)
        target["n"] += 1
        replan_count = int((economics.get("repair") or {}).get("replan_count") or 0)
        target["replans"] += replan_count
        ttar = economics.get("tta_ms")
        if isinstance(ttar, int) and not isinstance(ttar, bool) and ttar >= 0:
            target["all_ttar"].append(ttar)
        repaired = replan_count > 0
        if repaired:
            target["repaired"] += 1
            if isinstance(ttar, int) and not isinstance(ttar, bool) and ttar >= 0:
                target["repaired_ttar"].append(ttar)
        else:
            target["first_pass"] += 1
            if isinstance(ttar, int) and not isinstance(ttar, bool) and ttar >= 0:
                target["first_ttar"].append(ttar)

        phase_observation = _phase_timing_observation(economics)
        if phase_observation is None:
            target["phase_timing_unknown"] += 1
        else:
            target["phase_timing_observed"] += 1
            engineering_active_ms = int(phase_observation["engineering_active_ms"] or 0)
            accept_wait_ms = int(phase_observation["accept_wait_ms"] or 0)
            target["all_engineering_active"].append(engineering_active_ms)
            target["all_accept_wait"].append(accept_wait_ms)
            if repaired:
                target["repaired_engineering_active"].append(engineering_active_ms)
                target["repaired_accept_wait"].append(accept_wait_ms)
            else:
                target["first_engineering_active"].append(engineering_active_ms)
                target["first_accept_wait"].append(accept_wait_ms)
            replan_ms = phase_observation.get("replan_ms")
            if isinstance(replan_ms, int) and not isinstance(replan_ms, bool):
                target["all_replan_time"].append(replan_ms)
                if repaired:
                    target["repaired_replan_time"].append(replan_ms)

        events = ledger.list_events(run_id)
        scope_size, scope_censored = _scope_observation(events)
        if scope_size is None:
            target["scope_unknown"] += 1
        elif scope_censored:
            target["scope_observed"] += 1
            target["scope_censored"] += 1
        else:
            target["scope_observed"] += 1
            target["scope_values"].append(scope_size)
        oracle = _oracle_observation(events)
        if oracle is None:
            target["oracle_unknown"] += 1
        else:
            target["oracle_observed"] += 1
            if oracle:
                target["oracle_strong"] += 1
            else:
                target["oracle_not_strong"] += 1

        if not repaired:
            continue
        proofs = ledger.list_proofs(run_id)
        causes_for_run: set[str] = set()
        failure_events = sorted(
            [event for event in events if event.get("event_type") == "failure_observed"],
            key=lambda event: int(event.get("seq") or 0),
        )
        reason_events = sorted(
            [event for event in events if str(event.get("event_type") or "") == "wave_replanned"],
            key=lambda event: int(event.get("seq") or 0),
        )
        for index, event in enumerate(failure_events):
            payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
            failure_class = str(payload.get("failure_class") or "UNKNOWN").strip().upper() or "UNKNOWN"
            target["failure_classes"][failure_class] += 1
            overall_failure_classes[failure_class] += 1
            if failure_class in P2_GENERIC_FAILURE_CLASSES:
                overall_generic_process_eligible += 1
                overall_generic_process_eligible_by_class[failure_class] += 1
                linked_proof, linkage = _generic_failure_proof_link(failure_class, event, proofs)
                overall_generic_process_linkage[linkage] += 1
                if linked_proof is not None:
                    process_outcome = _generic_process_outcome(failure_class, payload, linked_proof)
                    if process_outcome is not None:
                        overall_generic_process_observed += 1
                        overall_generic_process_observed_by_class[failure_class] += 1
                        overall_generic_process_outcomes[process_outcome] += 1
                detail_bucket = p2_failure_detail_bucket(failure_class, payload.get("p2_failure_detail"))
                if detail_bucket is None:
                    target["legacy_generic_detail_unavailable"][failure_class] += 1
                    overall_legacy_generic_detail_unavailable[failure_class] += 1
                else:
                    target["prospective_failure_details"][detail_bucket] += 1
                    overall_prospective_failure_details[detail_bucket] += 1
            elif failure_class == "PERMISSION_REQUIRED":
                detail_bucket = p2_failure_detail_bucket(failure_class, payload.get("p2_failure_detail"))
                if detail_bucket is not None:
                    target["prospective_failure_details"][detail_bucket] += 1
                    overall_prospective_failure_details[detail_bucket] += 1
            cause = _repair_cause(failure_class)
            if cause is not None:
                target["cause_events"][cause] += 1
                overall_cause_events[cause] += 1
                causes_for_run.add(cause)
                target["classification_sources"]["structured_failure_class"] += 1
                overall_classification_sources["structured_failure_class"] += 1
                overall_direct_structured_mapped += 1
                continue

            reason_payload = (
                reason_events[index].get("payload")
                if index < len(reason_events) and isinstance(reason_events[index].get("payload"), dict)
                else {}
            )
            request_cause, request_rule = p2_request_contract_cause_from_replan_reason(
                failure_class,
                reason_payload.get("reason"),
            )
            if request_cause is not None and request_rule is not None:
                target["cause_events"][request_cause] += 1
                overall_cause_events[request_cause] += 1
                causes_for_run.add(request_cause)
                target["reason_categories"][request_cause] += 1
                target["reason_rules"][request_rule] += 1
                target["classification_sources"]["durable_wave_replanned_reason_high_confidence"] += 1
                overall_reason_categories[request_cause] += 1
                overall_reason_rules[request_rule] += 1
                overall_classification_sources["durable_wave_replanned_reason_high_confidence"] += 1
                overall_reason_fallback_structured += 1
                overall_reason_fallback_events += 1
                continue
            category, rule = p2_generic_replan_reason_category(
                failure_class,
                reason_payload.get("reason"),
            )
            if category is not None and rule is not None:
                target["reason_categories"][category] += 1
                target["reason_rules"][rule] += 1
                target["classification_sources"]["durable_wave_replanned_reason_high_confidence"] += 1
                overall_reason_categories[category] += 1
                overall_reason_rules[rule] += 1
                overall_classification_sources["durable_wave_replanned_reason_high_confidence"] += 1
                overall_reason_fallback_structured += 1
                overall_reason_fallback_events += 1
                continue

            target["unclassified"][failure_class] += 1
            overall_unclassified[failure_class] += 1
            target["classification_sources"]["unclassified"] += 1
            overall_classification_sources["unclassified"] += 1
            overall_unclassified_replan_events += 1
        for cause in causes_for_run:
            target["cause_runs"][cause].add(run_id)
            overall_cause_runs[cause].add(run_id)

    ordered_names = [name for name in WORKFLOW_ORDER if name in buckets]
    if "unknown" in buckets:
        ordered_names.append("unknown")
    strata: list[dict[str, Any]] = []
    for name in ordered_names:
        item = buckets[name]
        n = int(item["n"])
        strata.append({
            "workflow": name,
            "n": n,
            "first_pass_accepted": int(item["first_pass"]),
            "repaired_accepted": int(item["repaired"]),
            "first_pass_rate": round(item["first_pass"] / n, 6) if n else None,
            "repaired_rate": round(item["repaired"] / n, 6) if n else None,
            "replan_count": int(item["replans"]),
            "ttar_ms": {
                "all_p50": _percentile(item["all_ttar"], 50),
                "all_p90": _percentile(item["all_ttar"], 90),
                "first_pass_p50": _percentile(item["first_ttar"], 50),
                "first_pass_p90": _percentile(item["first_ttar"], 90),
                "repaired_p50": _percentile(item["repaired_ttar"], 50),
                "repaired_p90": _percentile(item["repaired_ttar"], 90),
            },
            "phase_aware_timing": {
                "measurement": "accepted_result_economics.phase_timing.methodology_phase_ms",
                "observed_runs": int(item["phase_timing_observed"]),
                "unknown_runs": int(item["phase_timing_unknown"]),
                "engineering_active_definition": list(P2_ENGINEERING_ACTIVE_PHASE_KEYS),
                "engineering_active_ms": {
                    "all_p50": _percentile(item["all_engineering_active"], 50),
                    "all_p90": _percentile(item["all_engineering_active"], 90),
                    "first_pass_p50": _percentile(item["first_engineering_active"], 50),
                    "first_pass_p90": _percentile(item["first_engineering_active"], 90),
                    "repaired_p50": _percentile(item["repaired_engineering_active"], 50),
                    "repaired_p90": _percentile(item["repaired_engineering_active"], 90),
                },
                "accept_wait_ms": {
                    "all_p50": _percentile(item["all_accept_wait"], 50),
                    "all_p90": _percentile(item["all_accept_wait"], 90),
                    "first_pass_p50": _percentile(item["first_accept_wait"], 50),
                    "first_pass_p90": _percentile(item["first_accept_wait"], 90),
                    "repaired_p50": _percentile(item["repaired_accept_wait"], 50),
                    "repaired_p90": _percentile(item["repaired_accept_wait"], 90),
                },
                "replan_ms": {
                    "all_p50": _percentile(item["all_replan_time"], 50),
                    "all_p90": _percentile(item["all_replan_time"], 90),
                    "repaired_p50": _percentile(item["repaired_replan_time"], 50),
                    "repaired_p90": _percentile(item["repaired_replan_time"], 90),
                },
                "not_model_latency": True,
                "not_cpu_time": True,
                "accept_wait_cause_inferred": False,
                "unknown_not_imputed": True,
            },
            "repair_failure_classes": dict(sorted(item["failure_classes"].items())),
            "repair_causes": {
                "event_counts": {cause: int(item["cause_events"].get(cause, 0)) for cause in PLANNED_REPAIR_CAUSES},
                "affected_run_counts": {cause: len(item["cause_runs"].get(cause, set())) for cause in PLANNED_REPAIR_CAUSES},
                "unclassified_structured_failure_classes": dict(sorted(item["unclassified"].items())),
                "prospective_failure_detail": {
                    "schema": P2_FAILURE_OBSERVATION_SCHEMA,
                    "detail_counts": dict(sorted(item["prospective_failure_details"].items())),
                    "legacy_generic_detail_unavailable": dict(sorted(item["legacy_generic_detail_unavailable"].items())),
                    "historical_backfill": False,
                },
                "durable_reason_category_counts": dict(sorted(item["reason_categories"].items())),
                "high_confidence_reason_rule_counts": dict(sorted(item["reason_rules"].items())),
                "classification_source_counts": dict(sorted(item["classification_sources"].items())),
            },
            "scope_size": {
                "measurement": "context_prepared.selected_paths_unique",
                "observed_runs": int(item["scope_observed"]),
                "unknown_runs": int(item["scope_unknown"]),
                "censored_at_event_path_cap_runs": int(item["scope_censored"]),
                "p50_paths": _percentile(item["scope_values"], 50),
                "p90_paths": _percentile(item["scope_values"], 90),
            },
            "oracle_strength": {
                "measurement": "oracle_preflight.strong_oracle",
                "observed_runs": int(item["oracle_observed"]),
                "strong_runs": int(item["oracle_strong"]),
                "not_strong_runs": int(item["oracle_not_strong"]),
                "unknown_runs": int(item["oracle_unknown"]),
            },
        })

    overall_events = {cause: int(overall_cause_events.get(cause, 0)) for cause in PLANNED_REPAIR_CAUSES}
    overall_runs = {cause: len(overall_cause_runs.get(cause, set())) for cause in PLANNED_REPAIR_CAUSES}
    included = sum(int(item["n"]) for item in buckets.values())
    mapped_failure_events = overall_direct_structured_mapped + overall_reason_fallback_structured
    unclassified_failure_events = sum(int(count) for count in overall_unclassified.values())
    classified_failure_events = mapped_failure_events + unclassified_failure_events
    oracle_observed_runs = sum(int(item["oracle_observed"]) for item in buckets.values())
    oracle_strong_runs = sum(int(item["oracle_strong"]) for item in buckets.values())
    oracle_not_strong_runs = sum(int(item["oracle_not_strong"]) for item in buckets.values())
    oracle_unknown_runs = sum(int(item["oracle_unknown"]) for item in buckets.values())
    return {
        "schema_version": 2,
        "analysis_source": "immutable_ledger_facts_v1",
        "cohort": "accepted_representative_chatweb_mcp_model_free",
        "accepted_runs_scanned": len(selected),
        "accepted_runs": included,
        "accepted_runs_truncated": truncated,
        "excluded": {"explicit_model_route": explicit_model_route},
        "workflow_strata": strata,
        "overall_repair_failure_classes": dict(sorted(overall_failure_classes.items())),
        "overall_repair_causes": {
            "event_counts": overall_events,
            "affected_run_counts": overall_runs,
            "unclassified_structured_failure_classes": dict(sorted(overall_unclassified.items())),
            "prospective_failure_detail": {
                "schema": P2_FAILURE_OBSERVATION_SCHEMA,
                "detail_counts": dict(sorted(overall_prospective_failure_details.items())),
                "legacy_generic_detail_unavailable": dict(sorted(overall_legacy_generic_detail_unavailable.items())),
                "historical_backfill": False,
            },
            "durable_reason_category_counts": dict(sorted(overall_reason_categories.items())),
            "high_confidence_reason_rule_counts": dict(sorted(overall_reason_rules.items())),
            "classification_source_counts": dict(sorted(overall_classification_sources.items())),
        },
        "causal_classification": {
            "basis": "structured_failure_class_then_high_confidence_durable_replan_reason_on_repaired_accepted_runs",
            "total_failure_events": classified_failure_events,
            "mapped_failure_events": mapped_failure_events,
            "unclassified_failure_events": unclassified_failure_events,
            "mapped_event_coverage": (
                round(mapped_failure_events / classified_failure_events, 6)
                if classified_failure_events
                else None
            ),
            "largest_unclassified_failure_class": (
                overall_unclassified.most_common(1)[0][0] if overall_unclassified else None
            ),
            "durable_reason_fallback_events": overall_reason_fallback_events,
            "classified_replan_events": overall_direct_structured_mapped + overall_reason_fallback_events,
            "unclassified_replan_events": overall_unclassified_replan_events,
            "classification_source_counts": dict(sorted(overall_classification_sources.items())),
            "high_confidence_reason_category_counts": dict(sorted(overall_reason_categories.items())),
            "high_confidence_reason_rule_counts": dict(sorted(overall_reason_rules.items())),
            "unclassified_zero_means_absent": False,
            "prospective_failure_detail_schema": P2_FAILURE_OBSERVATION_SCHEMA,
            "legacy_generic_detail_not_inferred": True,
        },
        "generic_failure_process_outcome": {
            "measurement": "durable_failed_proof_process_outcome_v1",
            "eligible_failure_events": overall_generic_process_eligible,
            "observed_events": overall_generic_process_observed,
            "unknown_events": overall_generic_process_eligible - overall_generic_process_observed,
            "coverage": (
                round(overall_generic_process_observed / overall_generic_process_eligible, 6)
                if overall_generic_process_eligible
                else None
            ),
            "eligible_by_failure_class": dict(sorted(overall_generic_process_eligible_by_class.items())),
            "observed_by_failure_class": dict(sorted(overall_generic_process_observed_by_class.items())),
            "linkage_counts": dict(sorted(overall_generic_process_linkage.items())),
            "outcome_counts": dict(sorted(overall_generic_process_outcomes.items())),
            "causal_attribution": "unattributed",
            "historical_events_mutated": False,
            "unknown_not_imputed": True,
        },
        "oracle_observation": {
            "measurement": "oracle_preflight.strong_oracle",
            "eligible_runs": included,
            "observed_runs": oracle_observed_runs,
            "strong_runs": oracle_strong_runs,
            "not_strong_runs": oracle_not_strong_runs,
            "unknown_runs": oracle_unknown_runs,
            "coverage": round(oracle_observed_runs / included, 6) if included else None,
            "unknown_not_imputed": True,
        },
        "preflight_avoided": {
            **preflight_avoided,
            "meaning": "known no-write patch failures stopped before orchestration run creation",
        },
        "countermeasure_evaluation": _countermeasure_report(
            repair_events=overall_events,
            affected_runs=overall_runs,
            preflight_avoided=preflight_avoided,
        ),
        "policy": {
            "accepted_only_observational_cohort": True,
            "not_a_causal_treatment_effect_estimate": True,
            "repair_cause_requires_structured_failure_evidence": True,
            "unknown_scope_or_oracle_not_imputed": True,
            "unmatched_structured_failures_remain_unclassified": True,
            "generic_failure_details_are_prospective_only": True,
            "generic_failure_detail_is_not_a_causal_repair_label": True,
            "generic_process_outcome_is_not_a_causal_repair_label": True,
            "generic_process_outcome_uses_exact_durable_proof_linkage": True,
            "permission_failure_details_are_prospective_only": True,
            "permission_failure_detail_is_not_a_causal_repair_label": True,
            "permission_or_protected_request_correction_requires_paired_replan_reason": True,
            "zero_planned_cause_without_evidence_is_not_proof_of_absence": True,
            "countermeasure_effect_requires_comparable_pre_post_or_paired_evidence": True,
            "scope_path_cap_censored_runs_excluded_from_scope_percentiles": True,
            "phase_aware_timing_is_not_model_latency": True,
            "phase_aware_timing_unknown_not_imputed": True,
        },
    }
