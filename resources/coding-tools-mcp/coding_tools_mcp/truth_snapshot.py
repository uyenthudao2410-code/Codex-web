from __future__ import annotations

from typing import Any

TRUTH_MATCH_STATES = ("MATCHED", "MISMATCHED", "UNKNOWN", "NOT_APPLICABLE")


def _present(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def match_state(observed: Any, expected: Any, *, applicable: bool = True) -> str:
    """Return a fail-closed comparison state without inventing missing evidence."""
    if not applicable:
        return "NOT_APPLICABLE"
    if not _present(observed) or not _present(expected):
        return "UNKNOWN"
    return "MATCHED" if str(observed) == str(expected) else "MISMATCHED"


def build_truth_snapshot(
    *,
    source: dict[str, Any] | None,
    runtime_identity: dict[str, Any] | None,
    orchestration: dict[str, Any] | None,
    objective: dict[str, Any] | None,
    proof: dict[str, Any] | None,
    checkpoint: dict[str, Any] | None,
    package: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compose existing authorities into one read-only operator truth projection."""
    source = source if isinstance(source, dict) else {}
    runtime_identity = runtime_identity if isinstance(runtime_identity, dict) else {}
    orchestration = orchestration if isinstance(orchestration, dict) else {}
    objective = objective if isinstance(objective, dict) else {}
    proof = proof if isinstance(proof, dict) else {}
    checkpoint = checkpoint if isinstance(checkpoint, dict) else {}
    package = package if isinstance(package, dict) else {}

    source_head = str(source.get("base_head") or source.get("git_head") or "")
    source_fp = str(source.get("source_fingerprint") or source.get("worktree_fp") or "")
    wave_base = str(orchestration.get("base_head") or "")
    wave_fp = str(orchestration.get("worktree_fp") or "")
    loaded_revision = str(runtime_identity.get("code_revision") or "")
    package_revision = str(package.get("revision") or "")
    dirty_paths = [str(item) for item in (source.get("dirty_source_paths") or source.get("dirty_paths") or []) if str(item)]

    return {
        "schema_version": 1,
        "read_only": True,
        "state_vocabulary": list(TRUTH_MATCH_STATES),
        "source": {
            "git_head": source_head or None,
            "worktree_fp": source_fp or None,
            "dirty": bool(dirty_paths),
            "dirty_path_count": len(dirty_paths),
            "observed_at": source.get("observed_at"),
            "observation_source": source.get("observation_source"),
        },
        "runtime": {
            "runtime_version": runtime_identity.get("runtime_version"),
            "process_instance_id": runtime_identity.get("process_instance_id"),
            "server_instance_id": runtime_identity.get("server_instance_id"),
            "code_revision": loaded_revision or None,
            "tool_contract": runtime_identity.get("tool_contract"),
        },
        "orchestration": {
            "run_id": orchestration.get("run_id") or None,
            "wave_id": orchestration.get("wave_id") or None,
            "state": orchestration.get("state") or None,
            "run_status": orchestration.get("run_status") or None,
            "wave_status": orchestration.get("wave_status") or None,
            "base_head": wave_base or None,
            "worktree_fp": wave_fp or None,
            "run_initial_objective": objective.get("run_initial_objective") or None,
            "effective_objective": objective.get("effective_objective") or None,
            "objective_revision": objective.get("objective_revision"),
            "objective_sha256": objective.get("objective_sha256") or None,
            "objective_hash_valid": objective.get("objective_hash_valid"),
            "objective_source": objective.get("objective_source") or None,
            "objective_changed_from_previous": bool(objective.get("objective_changed_from_previous", False)),
        },
        "evidence": {
            "latest_proof": {
                "proof_id": proof.get("proof_id") or None,
                "stage_id": proof.get("stage_id") or None,
                "status": proof.get("status") or None,
                "finished_at": proof.get("finished_at") or None,
            },
            "latest_checkpoint": {
                "checkpoint_id": checkpoint.get("checkpoint_id") or None,
                "status": checkpoint.get("status") or None,
                "git_head": checkpoint.get("git_head") or None,
                "proof_fingerprint": checkpoint.get("proof_fingerprint") or None,
                "created_at": checkpoint.get("created_at") or None,
            },
        },
        "package": {
            "state": str(package.get("state") or "UNKNOWN"),
            "revision": package_revision or None,
            "identity": package.get("identity") or None,
        },
        "comparisons": {
            "runtime_code_vs_source_head": match_state(loaded_revision, source_head),
            "wave_base_vs_source_head": match_state(wave_base, source_head),
            "wave_worktree_vs_source_worktree": match_state(wave_fp, source_fp),
            "package_revision_vs_source_head": match_state(package_revision, source_head),
        },
    }
