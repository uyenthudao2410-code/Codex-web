from __future__ import annotations

import hashlib
import json
import os
import random
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any


REPLAY_SCHEMA_VERSION = 1
REQUIRED_IDENTITY_FIELDS = (
    "task_spec_fp",
    "base_head",
    "contract_fp",
    "oracle_id",
    "task_class",
    "environment_fp",
    "tool_contract_fp",
    "evaluation_schema_fp",
    "runtime_version",
    "cache_stratum",
)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _bounded_text(value: Any, max_length: int, *, field: str) -> str:
    text = str(value or "").strip()
    if not text or len(text) > max_length or any(ord(char) < 32 for char in text):
        raise ValueError(f"{field} must be a non-empty bounded string")
    return text


def _positive_even(value: Any, *, field: str, maximum: int = 100) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 2 or value > maximum or value % 2:
        raise ValueError(f"{field} must be an even integer between 2 and {maximum}")
    return value


def validate_replay_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be an object")
    if manifest.get("schema_version") != REPLAY_SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {REPLAY_SCHEMA_VERSION}")

    study_id = _bounded_text(manifest.get("study_id"), 100, field="study_id")
    baseline_policy = _bounded_text(manifest.get("baseline_policy"), 100, field="baseline_policy").lower()
    candidate_policy = _bounded_text(manifest.get("candidate_policy"), 100, field="candidate_policy").lower()
    if baseline_policy == candidate_policy:
        raise ValueError("baseline_policy and candidate_policy must differ")
    pair_count = _positive_even(manifest.get("pair_count"), field="pair_count")
    seed = manifest.get("seed", 0)
    if isinstance(seed, bool) or not isinstance(seed, int) or abs(seed) > 2**63 - 1:
        raise ValueError("seed must be a signed 64-bit integer")

    provenance = _bounded_text(manifest.get("provenance"), 32, field="provenance").lower()
    if provenance not in {"representative", "benchmark"}:
        raise ValueError("provenance must be representative or benchmark; synthetic replay is intentionally unsupported")

    identity_source = manifest.get("identity")
    if not isinstance(identity_source, dict):
        raise ValueError("identity must be an object")
    identity: dict[str, Any] = {}
    for field in REQUIRED_IDENTITY_FIELDS:
        identity[field] = _bounded_text(identity_source.get(field), 160, field=f"identity.{field}")
    identity["cache_stratum"] = identity["cache_stratum"].lower()
    if identity["cache_stratum"] not in {"cold", "warm"}:
        raise ValueError("identity.cache_stratum must be cold or warm; unknown is not controlled replay evidence")

    command = manifest.get("command")
    if command is not None:
        if not isinstance(command, list) or not command or len(command) > 64:
            raise ValueError("command must be a non-empty argv array when supplied")
        command = [_bounded_text(item, 4096, field="command item") for item in command]

    source_repo = str(manifest.get("source_repo") or "").strip()
    timeout_seconds = manifest.get("timeout_seconds", 900)
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, int) or not 1 <= timeout_seconds <= 7200:
        raise ValueError("timeout_seconds must be an integer between 1 and 7200")

    return {
        "schema_version": REPLAY_SCHEMA_VERSION,
        "study_id": study_id,
        "seed": seed,
        "pair_count": pair_count,
        "baseline_policy": baseline_policy,
        "candidate_policy": candidate_policy,
        "provenance": provenance,
        "identity": identity,
        "source_repo": source_repo,
        "command": command,
        "timeout_seconds": timeout_seconds,
    }


def build_counterbalanced_plan(manifest: dict[str, Any]) -> dict[str, Any]:
    validated = validate_replay_manifest(manifest)
    pair_count = validated["pair_count"]
    baseline = validated["baseline_policy"]
    candidate = validated["candidate_policy"]
    orders = ["AB"] * (pair_count // 2) + ["BA"] * (pair_count // 2)
    random.Random(validated["seed"]).shuffle(orders)
    pair_basis = {
        **validated["identity"],
        "provenance": validated["provenance"],
        "baseline_policy": baseline,
        "candidate_policy": candidate,
    }
    pair_basis_sha256 = _sha256_json(pair_basis)

    pairs: list[dict[str, Any]] = []
    trials: list[dict[str, Any]] = []
    order_index = 0
    for pair_index, order in enumerate(orders, start=1):
        pair_id = f"{validated['study_id']}-pair-{pair_index:03d}"
        replicate_id = f"{validated['study_id']}-replicate-{pair_index:03d}"
        policies = (baseline, candidate) if order == "AB" else (candidate, baseline)
        pair_trials: list[dict[str, Any]] = []
        for position, policy in enumerate(policies, start=1):
            trial_id = f"{pair_id}-{position}-{policy}"
            evaluation = {
                "pair_id": pair_id,
                "policy": policy,
                "task_class": validated["identity"]["task_class"],
                "oracle_id": validated["identity"]["oracle_id"],
                "provenance": validated["provenance"],
                "replicate_id": replicate_id,
                "order_index": order_index,
                "cache_stratum": validated["identity"]["cache_stratum"],
            }
            trial = {
                "trial_id": trial_id,
                "pair_id": pair_id,
                "replicate_id": replicate_id,
                "policy": policy,
                "order": order,
                "position": position,
                "order_index": order_index,
                "evaluation": evaluation,
            }
            pair_trials.append(trial)
            trials.append(trial)
            order_index += 1
        pairs.append({"pair_id": pair_id, "replicate_id": replicate_id, "order": order, "trials": pair_trials})

    plan: dict[str, Any] = {
        "schema_version": REPLAY_SCHEMA_VERSION,
        "study_id": validated["study_id"],
        "seed": validated["seed"],
        "pair_count": pair_count,
        "trial_count": len(trials),
        "baseline_policy": baseline,
        "candidate_policy": candidate,
        "provenance": validated["provenance"],
        "pair_basis": pair_basis,
        "pair_basis_sha256": pair_basis_sha256,
        "counterbalance": {
            "ab_pairs": sum(1 for item in orders if item == "AB"),
            "ba_pairs": sum(1 for item in orders if item == "BA"),
            "assignment": "seeded_shuffle_of_equal_ab_ba_blocks",
        },
        "pairs": pairs,
        "trials": trials,
        "execution": {
            "default": "plan_only",
            "requires_explicit_execute": True,
            "fresh_detached_worktree_per_trial": True,
            "sequential": True,
            "acceptance_not_inferred_from_exit_code": True,
        },
        "automatic_activation": False,
        "promotion_eligible": validated["provenance"] == "representative",
    }
    plan["plan_sha256"] = _sha256_json(plan)
    return plan


def _run_git(repo: Path, *args: str, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def _format_command(argv: list[str], *, trial: dict[str, Any], workspace: Path) -> list[str]:
    values = {
        "policy": str(trial["policy"]),
        "pair_id": str(trial["pair_id"]),
        "replicate_id": str(trial["replicate_id"]),
        "order_index": str(trial["order_index"]),
        "trial_id": str(trial["trial_id"]),
        "workspace": str(workspace),
    }
    formatted: list[str] = []
    for item in argv:
        try:
            formatted.append(item.format(**values))
        except KeyError as exc:
            raise ValueError(f"unsupported command placeholder: {exc.args[0]}") from exc
    return formatted


def execute_controlled_replay(manifest: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    validated = validate_replay_manifest(manifest)
    source_repo_text = validated["source_repo"]
    command = validated["command"]
    if not source_repo_text or command is None:
        raise ValueError("explicit execution requires source_repo and caller-supplied command argv")
    source_repo = Path(source_repo_text).resolve()
    if not source_repo.is_dir():
        raise ValueError("source_repo does not exist")

    base_head = validated["identity"]["base_head"]
    resolved = _run_git(source_repo, "rev-parse", f"{base_head}^{{commit}}")
    if resolved.returncode != 0 or resolved.stdout.strip() != base_head:
        raise ValueError("identity.base_head is not the exact resolved source commit")

    trial_results: list[dict[str, Any]] = []
    study_temp = Path(tempfile.mkdtemp(prefix=f"coding-tools-replay-{validated['study_id']}-"))
    try:
        for trial in plan.get("trials") or []:
            workspace = study_temp / str(trial["trial_id"])
            setup = _run_git(source_repo, "worktree", "add", "--detach", str(workspace), base_head, timeout=120)
            infrastructure_error: str | None = None
            command_result: subprocess.CompletedProcess[bytes] | None = None
            duration_ms: float | None = None
            start_head_verified = False
            clean_start_verified = False
            cleanup_ok = False
            try:
                if setup.returncode != 0:
                    infrastructure_error = "git_worktree_add_failed"
                else:
                    head = _run_git(workspace, "rev-parse", "HEAD")
                    status = _run_git(workspace, "status", "--porcelain")
                    start_head_verified = head.returncode == 0 and head.stdout.strip() == base_head
                    clean_start_verified = status.returncode == 0 and not status.stdout.strip()
                    if not start_head_verified or not clean_start_verified:
                        infrastructure_error = "isolated_worktree_identity_mismatch"
                    else:
                        argv = _format_command(command, trial=trial, workspace=workspace)
                        env = os.environ.copy()
                        env.update({
                            "CODING_TOOLS_EVAL_STUDY_ID": validated["study_id"],
                            "CODING_TOOLS_EVAL_PAIR_ID": str(trial["pair_id"]),
                            "CODING_TOOLS_EVAL_REPLICATE_ID": str(trial["replicate_id"]),
                            "CODING_TOOLS_EVAL_POLICY": str(trial["policy"]),
                            "CODING_TOOLS_EVAL_ORDER_INDEX": str(trial["order_index"]),
                            "CODING_TOOLS_EVAL_PAIR_BASIS_SHA256": str(plan["pair_basis_sha256"]),
                        })
                        started = time.monotonic_ns()
                        try:
                            command_result = subprocess.run(
                                argv,
                                cwd=workspace,
                                env=env,
                                check=False,
                                capture_output=True,
                                timeout=validated["timeout_seconds"],
                            )
                        except subprocess.TimeoutExpired as exc:
                            command_result = subprocess.CompletedProcess(argv, 124, exc.stdout or b"", exc.stderr or b"")
                        duration_ms = round((time.monotonic_ns() - started) / 1_000_000, 6)
            finally:
                if workspace.exists():
                    removed = _run_git(source_repo, "worktree", "remove", "--force", str(workspace), timeout=120)
                    cleanup_ok = removed.returncode == 0
                    if not cleanup_ok:
                        shutil.rmtree(workspace, ignore_errors=True)
                        _run_git(source_repo, "worktree", "prune")

            stdout = bytes(command_result.stdout or b"") if command_result is not None else b""
            stderr = bytes(command_result.stderr or b"") if command_result is not None else b""
            trial_results.append({
                "trial_id": trial["trial_id"],
                "pair_id": trial["pair_id"],
                "policy": trial["policy"],
                "order_index": trial["order_index"],
                "start_head_verified": start_head_verified,
                "clean_start_verified": clean_start_verified,
                "infrastructure_error": infrastructure_error,
                "command_exit_code": command_result.returncode if command_result is not None else None,
                "duration_ms": duration_ms,
                "stdout_bytes": len(stdout),
                "stderr_bytes": len(stderr),
                "stdout_sha256": hashlib.sha256(stdout).hexdigest() if command_result is not None else None,
                "stderr_sha256": hashlib.sha256(stderr).hexdigest() if command_result is not None else None,
                "cleanup_ok": cleanup_ok,
                "accepted_result": None,
                "acceptance_policy": "never_infer_acceptance_from_process_exit_code",
            })
    finally:
        shutil.rmtree(study_temp, ignore_errors=True)
        _run_git(source_repo, "worktree", "prune")

    infrastructure_complete = all(item["infrastructure_error"] is None and item["cleanup_ok"] for item in trial_results)
    return {
        "schema_version": REPLAY_SCHEMA_VERSION,
        "study_id": validated["study_id"],
        "plan_sha256": plan["plan_sha256"],
        "mode": "explicit_execution",
        "infrastructure_complete": infrastructure_complete,
        "trial_count": len(trial_results),
        "trials": trial_results,
        "accepted_result_evidence_complete": False,
        "accepted_result_evidence_reason": "caller_oracle_and_causal_route_attestation_required",
        "automatic_activation": False,
    }
