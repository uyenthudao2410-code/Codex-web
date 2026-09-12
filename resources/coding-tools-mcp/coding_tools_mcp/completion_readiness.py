"""Read-only completion readiness and baseline-oracle classification.

These projections deliberately answer whether the *next* verification step is
well formed.  They neither execute a command nor turn static availability into
proof, acceptance, or an independently confirmed product outcome.
"""

from __future__ import annotations

import hashlib
import shlex
import shutil
from pathlib import Path
from typing import Any

from .build_verify import detect_project


_SETUP_FAILURE_MARKERS = (
    "command not found",
    "is not recognized as an internal or external command",
    "no such file or directory",
    "file or directory not found",
    "can't open file",
    "cannot find the path",
    "modulenotfounderror",
    "no module named",
    "pytest: error: file or directory not found",
)

_DEFAULT_VERIFICATION_BY_WORKFLOW = {
    "bugfix": "tests",
    "feature": "tests",
    "greenfield": "all",
    "refactor": "tests",
    "test_failure": "tests",
    "build_release": "all",
    "diagnose": "none",
    "custom": "tests",
}


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def _command_argv(command: str) -> list[str] | None:
    if not command.strip():
        return None
    try:
        values = shlex.split(command, posix=False)
    except ValueError:
        return None
    argv = [item.strip("'\"") for item in values if item.strip("'\"")]
    if any(item in {"&&", "||", "|", ">", "<"} for item in argv):
        return None
    return argv


def _tool_available(tool: str, *, root: Path) -> bool:
    candidate = Path(tool)
    if candidate.is_absolute() or "/" in tool or "\\" in tool:
        return candidate.is_file() if candidate.is_absolute() else (root / candidate).is_file()
    return shutil.which(tool) is not None


def _command_readiness(command: str, *, root: Path, kind: str) -> dict[str, Any]:
    command_hash = _hash_text(command) if command else None
    if not command:
        return {
            "kind": kind,
            "status": "MISSING",
            "command_sha256": None,
            "reason_code": f"{kind.upper()}_COMMAND_MISSING",
        }
    argv = _command_argv(command)
    if not argv:
        return {
            "kind": kind,
            "status": "UNAVAILABLE",
            "command_sha256": command_hash,
            "reason_code": "COMMAND_INTERPRETER_NOT_STATICALLY_IDENTIFIABLE",
        }
    tool = argv[0]
    if not _tool_available(tool, root=root):
        return {
            "kind": kind,
            "status": "UNAVAILABLE",
            "command_sha256": command_hash,
            "reason_code": "VERIFICATION_TOOL_UNAVAILABLE",
        }
    module_requested = len(argv) >= 2 and argv[1] == "-m"
    if module_requested and len(argv) < 3:
        return {
            "kind": kind,
            "status": "UNAVAILABLE",
            "command_sha256": command_hash,
            "reason_code": "VERIFICATION_MODULE_TARGET_MISSING",
        }
    readiness: dict[str, Any] = {
        "kind": kind,
        "status": "AVAILABLE",
        "command_sha256": command_hash,
        "reason_code": None,
        # Retain the established field for non-module commands; a true value
        # is no longer emitted because this process cannot verify the later
        # command environment.
        "module_checked": False,
    }
    if module_requested:
        # The command runs later through ExecTools with its declared shell,
        # workdir and filtered environment.  Checking this process's import
        # path here would answer a different question and can both reject a
        # valid project interpreter and accept an invalid one.  Readiness is
        # intentionally non-executing, so retain the static executable check
        # above and make the remaining environment proof explicit.
        readiness.update({
            "module_checked": False,
            "execution_environment": {
                "status": "PREFLIGHT_REQUIRED",
                "reason_code": "MODULE_AVAILABILITY_REQUIRES_DECLARED_EXECUTION_ENV",
                "next_action": (
                    "Run the declared verification command in its declared working directory "
                    "and use that result as the execution-environment proof."
                ),
            },
        })
    return readiness


def completion_readiness(
    root: Path,
    args: dict[str, Any],
    *,
    command_root: Path | None = None,
) -> dict[str, Any]:
    """Return static readiness for the same command selection as verify_build."""
    root = root.resolve(strict=False)
    command_root = (command_root or root).resolve(strict=False)
    project = detect_project(root)
    verification = str(args.get("verification") or "tests").strip().lower()
    valid_modes = {"none", "tests", "build", "all"}
    required_test = verification in {"tests", "all"}
    required_build = verification in {"build", "all"}
    test_command = str(args.get("test_command") or project.get("test_command") or "").strip()
    build_command = str(args.get("build_command") or project.get("build_command") or "").strip()
    steps = [
        _command_readiness(test_command, root=command_root, kind="test")
        for _ in range(int(required_test))
    ] + [
        _command_readiness(build_command, root=command_root, kind="build")
        for _ in range(int(required_build))
    ]
    blockers = [
        str(step["reason_code"])
        for step in steps
        if step.get("status") != "AVAILABLE" and step.get("reason_code")
    ]
    if verification not in valid_modes:
        blockers.append("VERIFICATION_MODE_INVALID")
    artifact_paths = [str(item) for item in args.get("artifact_paths", []) if str(item).strip()]
    if not artifact_paths:
        artifact_paths = [str(item) for item in project.get("artifact_paths", []) if str(item).strip()]
    return {
        "schema_version": 2,
        "status": "BLOCKED" if blockers else "READY_FOR_EXECUTION",
        "blocking_reason_codes": list(dict.fromkeys(blockers)),
        "project": {
            "type": str(project.get("type") or "unknown"),
            "package_manager": str(project.get("package_manager") or ""),
        },
        "command_root_is_workspace_relative": command_root == root or root in command_root.parents,
        "verification": {
            "mode": verification,
            "steps": steps,
            "commands_are_hashed": True,
            "commands_are_not_execution_proof": True,
            "execution_environment_preflight_required": any(
                step.get("execution_environment", {}).get("status") == "PREFLIGHT_REQUIRED"
                for step in steps
            ),
        },
        "artifacts": {
            "required_after_build": required_build,
            "status": "PENDING_POST_BUILD" if required_build else "NOT_REQUIRED",
            "configured_path_count": len(artifact_paths),
            "artifact_identity_not_proven": required_build,
        },
        "acceptance": {
            "status": "NOT_PROVEN",
            "missing": [
                *(["passed_test_or_build_proof"] if verification != "none" else []),
                *(["artifact_receipt"] if required_build else []),
                "chatweb_sol_final_acceptance",
            ],
            "business_outcome_not_inferred_from_build": True,
        },
    }


def workflow_completion_readiness(
    root: Path,
    args: dict[str, Any],
    *,
    command_root: Path,
    workspace_identity: dict[str, Any],
    problem_resolution: dict[str, Any],
    prepared: dict[str, Any] | None,
    planned_write_paths: list[str],
    oracle_preflight: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Attach bounded workflow provenance without making it an authority grant."""
    readiness = completion_readiness(root, args, command_root=command_root)
    workspace = workspace_identity.get("workspace_identity") if isinstance(workspace_identity.get("workspace_identity"), dict) else {}
    selected_paths = list(prepared.get("selected_paths") or []) if isinstance(prepared, dict) else []
    origin = str(problem_resolution.get("work_origin") or "unknown")
    readiness["workspace"] = {
        "bound": bool(workspace),
        "base_head": str(workspace_identity.get("base_head") or "") or None,
        "worktree_fingerprint": str(workspace_identity.get("worktree_fp") or "") or None,
        "recheck_before_write_and_acceptance": True,
    }
    readiness["problem_revision"] = {
        "work_origin": origin,
        "exact_binding_required": origin == "problem",
        "binding_status": "EXACT" if origin == "problem" else "NOT_REQUIRED",
        "business_outcome_confirmation_required": origin == "problem",
    }
    readiness["scope"] = {
        "understood_path_count": len(selected_paths),
        "understood_paths": selected_paths[:40],
        "planned_write_paths": sorted(dict.fromkeys(str(item) for item in planned_write_paths if str(item))),
        "dirty_worktree_adoption_automatic": False,
        "write_lease_not_granted_by_readiness": True,
    }
    if oracle_preflight is not None:
        readiness["oracle_preflight"] = dict(oracle_preflight)
        if oracle_preflight.get("blocking"):
            codes = list(readiness.get("blocking_reason_codes") or [])
            reason = str(oracle_preflight.get("reason_code") or "BASELINE_ENVIRONMENT_UNAVAILABLE")
            if reason not in codes:
                codes.append(reason)
            readiness["blocking_reason_codes"] = codes
            readiness["status"] = "BLOCKED"
    else:
        readiness["oracle_preflight"] = classify_baseline_oracle(None)
    return readiness


class CompletionReadinessWorkflowMixin:
    """Workflow glue for readiness that keeps the main workflow module bounded."""

    def _workflow_completion_readiness(
        self,
        args: dict[str, Any],
        *,
        workflow: str,
        ctx: Any,
        workspace_identity: dict[str, Any],
        prepared: dict[str, Any] | None,
        explicit_patches: list[str],
    ) -> tuple[str, dict[str, Any], dict[str, Any], Path, list[str]]:
        run = self.orchestration_ledger.get_run(ctx.run_id) or {}
        metadata = run.get("metadata") if isinstance(run.get("metadata"), dict) else {}
        problem_resolution = metadata.get("problem_resolution") if isinstance(metadata.get("problem_resolution"), dict) else {}
        command_root = self.resolve_existing(str(args.get("workdir", args.get("path", ".")))).path
        planned_write_paths = self._source_write_paths(explicit_patches) if explicit_patches else []
        verification, readiness = workflow_readiness_for_request(
            self.workspace.root,
            args,
            workflow=workflow,
            command_root=command_root,
            workspace_identity=workspace_identity,
            problem_resolution=problem_resolution,
            prepared=prepared,
            planned_write_paths=planned_write_paths,
        )
        return verification, readiness, problem_resolution, command_root, planned_write_paths

    def _candidate_oracle_readiness(
        self,
        args: dict[str, Any],
        *,
        workflow: str,
        ctx: Any,
        verification: str,
        command_root: Path,
        workspace_identity: dict[str, Any],
        problem_resolution: dict[str, Any],
        prepared: dict[str, Any] | None,
        planned_write_paths: list[str],
        candidate_proof: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        oracle_preflight, readiness = candidate_oracle_readiness(
            self.workspace.root,
            args,
            workflow=workflow,
            command_root=command_root,
            workspace_identity=workspace_identity,
            problem_resolution=problem_resolution,
            prepared=prepared,
            planned_write_paths=planned_write_paths,
            candidate_proof=candidate_proof,
        )
        candidate_proof["oracle_preflight"] = oracle_preflight
        self.orchestration_ledger.append_event(
            ctx.run_id,
            wave_id=ctx.wave_id,
            event_type="oracle_preflight",
            state_before=ctx.state,
            state_after=ctx.state,
            payload={
                "strong_oracle": bool(oracle_preflight["strong_oracle"]),
                "verification": verification,
                "classification": oracle_preflight["classification"],
                "reason_code": oracle_preflight["reason_code"],
                "command_sha256": oracle_preflight["command_sha256"],
            },
        )
        return oracle_preflight, readiness

    def _completion_readiness_blocked(
        self,
        ctx: Any,
        *,
        workflow: str,
        phase: str,
        prepared: dict[str, Any] | None,
        readiness: dict[str, Any],
        event: str,
        next_step: str,
        static: bool,
        oracle_preflight: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "reason_codes": list(readiness.get("blocking_reason_codes") or [])[:8],
            "static": static,
        }
        if oracle_preflight is not None:
            payload["oracle_classification"] = oracle_preflight["classification"]
        self.orchestration_control.record_failure(ctx, "COMPLETION_READINESS_BLOCKED", payload=payload)
        self._project_orchestration(ctx, event=event)
        self.task_state.update(completion_readiness_waiting_state(next_step))
        return completion_readiness_blocked_response(
            workflow=workflow,
            phase=phase,
            prepared=prepared,
            readiness=readiness,
            orchestration=self._orchestration_result(ctx),
            task=self.task_state.get(),
        )

    def _preflight_candidate_readiness(
        self,
        args: dict[str, Any],
        *,
        workflow: str,
        phase: str,
        ctx: Any,
        verification: str,
        command_root: Path,
        workspace_identity: dict[str, Any],
        problem_resolution: dict[str, Any],
        planned_write_paths: list[str],
        objective: str,
        prepared: dict[str, Any] | None,
        candidate_proof: dict[str, Any],
    ) -> tuple[dict[str, Any] | None, bool, dict[str, Any], dict[str, Any] | None]:
        """Run the one baseline check before model dispatch, then classify it."""
        if prepared is None:
            prepared = self.prepare_coding_context({
                "objective": objective,
                "path": args.get("path", "."),
                "queries": args.get("queries", []),
                "paths": args.get("paths", []),
                "max_files": args.get("max_files", 12),
                "max_entries": args.get("max_entries", 120),
                "max_matches_per_query": args.get("max_matches_per_query", 20),
                "max_total_bytes": args.get("max_total_bytes", 262144),
                "max_lines_per_file": args.get("max_lines_per_file", 2000),
                "force_refresh": args.get("force_refresh", False),
            })
        timeout_ms = min(max(int(args.get("timeout_seconds", 600)) * 1_000, 1_000), 120_000)
        workdir = str(args.get("workdir", args.get("path", ".")))
        if candidate_proof["test_command"]:
            candidate_proof["preflight_test"] = self._run_continuous_check(candidate_proof["test_command"], workdir, timeout_ms)
        elif candidate_proof["build_command"]:
            candidate_proof["preflight_build"] = self._run_continuous_check(candidate_proof["build_command"], workdir, timeout_ms)
        oracle_preflight, readiness = self._candidate_oracle_readiness(
            args,
            workflow=workflow,
            ctx=ctx,
            verification=verification,
            command_root=command_root,
            workspace_identity=workspace_identity,
            problem_resolution=problem_resolution,
            prepared=prepared,
            planned_write_paths=planned_write_paths,
            candidate_proof=candidate_proof,
        )
        if oracle_preflight["blocking"]:
            return prepared, False, readiness, self._completion_readiness_blocked(
                ctx,
                workflow=workflow,
                phase=phase,
                prepared=prepared,
                readiness=readiness,
                event="baseline_environment_blocked",
                next_step="Correct the baseline verification environment or target and provide replan_reason; do not dispatch a candidate model.",
                static=False,
                oracle_preflight=oracle_preflight,
            )
        return prepared, bool(oracle_preflight["strong_oracle"]), readiness, None


def workflow_readiness_for_request(
    root: Path,
    args: dict[str, Any],
    *,
    workflow: str,
    command_root: Path,
    workspace_identity: dict[str, Any],
    problem_resolution: dict[str, Any],
    prepared: dict[str, Any] | None,
    planned_write_paths: list[str],
    oracle_preflight: dict[str, Any] | None = None,
) -> tuple[str, dict[str, Any]]:
    """Choose workflow verification and build its non-authorizing readiness view."""
    requested_verification = args.get("verification")
    raw_adoptions = args.get("adopt_existing_files")
    adoption_only = (
        isinstance(raw_adoptions, list)
        and bool(raw_adoptions)
        and not planned_write_paths
        and not any(str(item).strip() for item in args.get("directories", []) if str(item).strip())
    )
    # Adoption records provenance for bytes that already exist; it is not a
    # source patch and must not silently escalate a bounded recovery into a
    # repository/package verification lane. Explicit user/caller selection
    # remains authoritative, including an explicit "all".
    if requested_verification is None:
        verification = "none" if adoption_only else _DEFAULT_VERIFICATION_BY_WORKFLOW[workflow]
    else:
        verification = str(requested_verification).lower()
    readiness = workflow_completion_readiness(
        root,
        {**args, "verification": verification},
        command_root=command_root,
        workspace_identity=workspace_identity,
        problem_resolution=problem_resolution,
        prepared=prepared,
        planned_write_paths=planned_write_paths,
        oracle_preflight=oracle_preflight,
    )
    return verification, readiness


def candidate_oracle_readiness(
    root: Path,
    args: dict[str, Any],
    *,
    workflow: str,
    command_root: Path,
    workspace_identity: dict[str, Any],
    problem_resolution: dict[str, Any],
    prepared: dict[str, Any] | None,
    planned_write_paths: list[str],
    candidate_proof: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Classify the executed baseline and refresh readiness from that fact."""
    preflight_result = next(
        (
            candidate_proof[key]
            for key in ("preflight_test", "preflight_build")
            if isinstance(candidate_proof.get(key), dict)
        ),
        None,
    )
    oracle_preflight = classify_baseline_oracle(preflight_result)
    _verification, readiness = workflow_readiness_for_request(
        root,
        args,
        workflow=workflow,
        command_root=command_root,
        workspace_identity=workspace_identity,
        problem_resolution=problem_resolution,
        prepared=prepared,
        planned_write_paths=planned_write_paths,
        oracle_preflight=oracle_preflight,
    )
    return oracle_preflight, readiness


def completion_readiness_waiting_state(next_step: str) -> dict[str, str]:
    """Use one consistent operator-visible waiting state for invalid readiness."""
    return {
        "status": "waiting",
        "failure": "COMPLETION_READINESS_BLOCKED",
        "current_step": "Completion readiness blocked",
        "next_step": next_step,
    }


def completion_readiness_blocked_response(
    *,
    workflow: str,
    phase: str,
    prepared: dict[str, Any] | None,
    readiness: dict[str, Any],
    orchestration: dict[str, Any],
    task: dict[str, Any],
) -> dict[str, Any]:
    """Return a stable, non-dispatch response for both static and dynamic blocks."""
    return {
        "workflow": workflow,
        "phase": "run" if phase == "run" else "execute",
        "prepared": prepared,
        "completion_readiness": readiness,
        "execution": {"ok": False, "status": "blocked", "reason": "COMPLETION_READINESS_BLOCKED"},
        "orchestration": orchestration,
        "task": task,
    }


def classify_baseline_oracle(result: dict[str, Any] | None) -> dict[str, Any]:
    """Classify one executed baseline without treating setup failure as a bug oracle."""
    if not isinstance(result, dict):
        return {
            "classification": "NOT_RUN",
            "strong_oracle": False,
            "blocking": False,
            "reason_code": "BASELINE_NOT_RUN",
            "command_sha256": None,
        }
    command = str(result.get("command") or "")
    command_hash = _hash_text(command) if command else None
    status = str(result.get("status") or "").strip().lower()
    if status == "passed":
        classification, strong, blocking, reason = "VERIFICATION_PASSED", False, False, None
    elif result.get("cancelled") or result.get("timed_out") or status in {"cancelled", "timed_out", "timeout"}:
        classification, strong, blocking, reason = "ENVIRONMENT_UNAVAILABLE", False, True, "BASELINE_COMMAND_NOT_COMPLETED"
    else:
        summary = str(result.get("summary") or "").lower()
        exit_code = result.get("exit_code")
        if exit_code is None or any(marker in summary for marker in _SETUP_FAILURE_MARKERS):
            classification, strong, blocking, reason = "ENVIRONMENT_UNAVAILABLE", False, True, "BASELINE_COMMAND_SETUP_OR_TARGET_INVALID"
        else:
            classification, strong, blocking, reason = "PRODUCT_ORACLE_REPRODUCED", True, False, "BASELINE_NONZERO_PRODUCT_ORACLE"
    return {
        "classification": classification,
        "strong_oracle": strong,
        "blocking": blocking,
        "reason_code": reason,
        "command_sha256": command_hash,
    }
