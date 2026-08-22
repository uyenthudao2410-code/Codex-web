from __future__ import annotations

"""P5 task-control extension; it adds no top-level MCP tool."""

import hashlib
import json
import subprocess
import time
from typing import Any

from . import __version__
from .errors import ToolFailure
from .p5_experiment import P5ExperimentError, analyzer_source_fingerprint


P5_A0_SEED_HANDLE = "secret://experiment/p5/a"


class P5ControlMixin:
    """The parent supplies runtime identity, secret broker, workspace, and ledger."""

    def _p5_runtime_contract(self) -> dict[str, Any]:
        """Return content-free live identities required by a P5 manifest."""
        policy = {
            "tool_mode": self.tool_mode,
            "permission_mode": self.permission_mode,
            "transport": str(getattr(getattr(self, "telemetry", None), "transport", "unknown")),
        }
        policy_fp = hashlib.sha256(json.dumps(policy, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        return {
            "runtime_version": str(__version__),
            "runtime_policy_fp": policy_fp,
            "tool_contract_fp": str(self.tool_contract.get("sha256") or ""),
            "evaluation_schema_fp": str((self.tool_contract.get("evaluation") or {}).get("sha256") or ""),
            "public_tool_count": int(self.tool_contract.get("tool_count") or 0),
            "analyzer_sha256": analyzer_source_fingerprint(),
        }

    def _p5_source_contract(self) -> dict[str, Any]:
        identity = self._orchestration_workspace_identity(".")
        root = self.workspace.root
        def git_text(*git_args: str) -> str:
            try:
                result = subprocess.run(
                    ["git", "-C", str(root), *git_args],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
            except (OSError, subprocess.SubprocessError):
                return ""
            return result.stdout.strip() if result.returncode == 0 else ""
        source_status = git_text(
            "status", "--porcelain=v1", "--untracked-files=all", "--", ".", ":(exclude).coding-tools", ":(exclude).coding-tools/**"
        )
        head = git_text("rev-parse", "HEAD")
        upstream = git_text("rev-parse", "@{upstream}")
        return {
            "control_plane_source_head": head,
            "upstream_identity": upstream,
            "source_worktree_clean": not bool(source_status),
            "head_matches_upstream": bool(head and upstream and head == upstream),
            "worktree_fp": identity.get("worktree_fp"),
        }

    def _p5_assert_open_contract(self, manifest: dict[str, Any]) -> dict[str, Any]:
        runtime = manifest.get("runtime_contract") if isinstance(manifest.get("runtime_contract"), dict) else {}
        source = manifest.get("source_contract") if isinstance(manifest.get("source_contract"), dict) else {}
        analysis = manifest.get("analysis") if isinstance(manifest.get("analysis"), dict) else {}
        observed_runtime = self._p5_runtime_contract()
        observed_source = self._p5_source_contract()
        workspace_fence = self.orchestration_ledger.get_write_fence("workspace")
        conflicting_writer = bool(
            workspace_fence
            and workspace_fence.get("status") == "active"
            and float(workspace_fence.get("expires_at") or 0) > time.time()
        )
        mismatches = [
            name
            for name in ("runtime_version", "runtime_policy_fp", "tool_contract_fp", "evaluation_schema_fp", "public_tool_count")
            if runtime.get(name) != observed_runtime.get(name)
        ]
        if analysis.get("analyzer_sha256") != observed_runtime["analyzer_sha256"]:
            mismatches.append("analysis.analyzer_sha256")
        if source.get("control_plane_source_head") != observed_source["control_plane_source_head"]:
            mismatches.append("source_contract.control_plane_source_head")
        if source.get("upstream_identity") != observed_source["upstream_identity"]:
            mismatches.append("source_contract.upstream_identity")
        if source.get("source_worktree_clean_required") is True and not observed_source["source_worktree_clean"]:
            mismatches.append("source_worktree_clean")
        if source.get("source_worktree_clean_required") is True and not observed_source["head_matches_upstream"]:
            mismatches.append("head_matches_upstream")
        if source.get("no_conflicting_writer_required") is True and conflicting_writer:
            mismatches.append("active_workspace_write_fence")
        if mismatches:
            raise ToolFailure(
                "P5_MANIFEST_RUNTIME_DRIFT",
                "The frozen P5 manifest does not match the currently loaded source/runtime contract.",
                category="runtime",
                details={
                    "mismatches": mismatches,
                    "observed": {
                        "runtime": observed_runtime,
                        "source": observed_source,
                        "active_workspace_write_fence": conflicting_writer,
                    },
                },
            )
        return {"runtime": observed_runtime, "source": observed_source}

    def _p5_secret(self, handle: object) -> tuple[str, str]:
        seed_handle = str(handle or "").strip()
        if not seed_handle.startswith("secret://"):
            raise ToolFailure("P5_SEED_HANDLE_REQUIRED", "P5 assignment requires a secret:// seed handle.", category="validation")
        try:
            seed = self.secret_broker.resolve(seed_handle)
        except ValueError as exc:
            raise ToolFailure("P5_SEED_HANDLE_INVALID", "P5 assignment seed handle is invalid.", category="validation") from exc
        if not seed:
            raise ToolFailure(
                "P5_SEED_UNAVAILABLE",
                "The requested P5 assignment seed is not available in the process secret broker.",
                category="runtime",
                retryable=True,
                details={"seed_handle": seed_handle},
            )
        return seed_handle, seed

    def _p5_seed_status(self) -> dict[str, object]:
        """Expose only whether the designated P5-A0 handle is resolvable."""
        broker_status = self.secret_broker.status()
        seed = self.secret_broker.resolve(P5_A0_SEED_HANDLE)
        return {
            "seed_handle": P5_A0_SEED_HANDLE,
            "available": seed is not None,
            "seed_commitment_sha256": hashlib.sha256(seed.encode("utf-8")).hexdigest() if seed else None,
            "content_free": broker_status.get("content_free") is True,
        }

    def _p5_control(self, args: dict[str, Any]) -> dict[str, Any]:
        request = args.get("p5_experiment")
        if not isinstance(request, dict):
            raise ToolFailure("P5_EXPERIMENT_REQUIRED", "p5_experiment is required for task_control action=p5.", category="validation")
        operation = str(request.get("operation") or "status").strip().lower()
        epoch_id = str(request.get("activation_epoch_id") or "").strip()
        authority = str((self._current_hub_client() or {}).get("client_id") or "operator")
        try:
            if operation == "status":
                epoch = self.orchestration_ledger.p5_epoch_snapshot(epoch_id) if epoch_id else None
                if epoch is None:
                    latest = self.orchestration_ledger.p5_latest_epoch()
                    epoch = self.orchestration_ledger.p5_epoch_snapshot(str(latest["activation_epoch_id"])) if latest else None
                return {
                    "p5": epoch,
                    "runtime_contract": self._p5_runtime_contract(),
                    "source_contract": self._p5_source_contract(),
                    "p5_seed": self._p5_seed_status(),
                    "automatic_activation": False,
                    "automatic_production_promotion": False,
                }
            if operation == "open":
                manifest = request.get("manifest")
                if not isinstance(manifest, dict):
                    raise ToolFailure("P5_MANIFEST_REQUIRED", "P5 open requires an exact manifest object.", category="validation")
                verified = self._p5_assert_open_contract(manifest)
                seed_handle, seed = self._p5_secret(request.get("seed_handle"))
                result = self.orchestration_ledger.p5_open_epoch(
                    manifest=manifest,
                    seed_material=seed,
                    seed_handle=seed_handle,
                    authority=authority,
                )
                return {"p5": result, "verified_contract": verified, "automatic_activation": False}
            if operation in {"pause", "resume", "close", "hard_stop"}:
                result = self.orchestration_ledger.p5_transition_epoch(
                    activation_epoch_id=epoch_id,
                    transition=operation,
                    reason=str(request.get("reason") or ""),
                    authority=authority,
                )
                return {"p5": result}
            if operation == "enroll":
                candidate = request.get("candidate")
                if not isinstance(candidate, dict):
                    raise ToolFailure("P5_CANDIDATE_REQUIRED", "P5 enrollment requires candidate identity and eligibility facts.", category="validation")
                result = self.orchestration_ledger.p5_record_enrollment(
                    activation_epoch_id=epoch_id,
                    candidate=candidate,
                    enrolled=request.get("enrolled") is True,
                    authority=authority,
                )
                return {"p5": result}
            if operation == "assign":
                candidate = request.get("candidate")
                if not isinstance(candidate, dict):
                    raise ToolFailure("P5_CANDIDATE_REQUIRED", "P5 assignment requires the pre-enrolled stable task identity.", category="validation")
                seed_handle, seed = self._p5_secret(request.get("seed_handle"))
                result = self.orchestration_ledger.p5_assign(
                    activation_epoch_id=epoch_id,
                    candidate=candidate,
                    manifest_sha256=str(request.get("manifest_sha256") or ""),
                    seed_material=seed,
                    pre_arm_action_attested=request.get("pre_arm_action_attested") is True,
                    authority=authority,
                )
                return {"p5": result, "seed_handle": seed_handle}
            if operation == "protocol_start":
                if str(request.get("first_write_at") or "").strip():
                    raise ToolFailure(
                        "P5_FIRST_WRITE_RUNTIME_OWNED",
                        "P5 first-write timing is recorded only when agent_workflow binds the assignment to a live write lease.",
                        category="validation",
                    )
                result = self.orchestration_ledger.p5_record_arm_protocol_start(
                    assignment_id=str(request.get("assignment_id") or ""),
                    received_arm=str(request.get("received_arm") or ""),
                    protocol_id=str(request.get("protocol_id") or ""),
                    authority=authority,
                )
                return {"p5": result}
            if operation == "outcome":
                outcome = request.get("outcome")
                if not isinstance(outcome, dict):
                    raise ToolFailure("P5_OUTCOME_REQUIRED", "P5 outcome requires a bounded terminal outcome object.", category="validation")
                result = self.orchestration_ledger.p5_record_outcome(
                    assignment_id=str(request.get("assignment_id") or ""),
                    outcome=outcome,
                    authority=authority,
                )
                return {"p5": result}
            if operation == "analyze":
                return {"p5": self.orchestration_ledger.p5_analyze_epoch(epoch_id)}
        except P5ExperimentError as exc:
            raise ToolFailure("P5_CONTRACT_VIOLATION", str(exc), category="validation") from exc
        raise ToolFailure("P5_OPERATION_UNSUPPORTED", "P5 operation is unsupported.", category="validation")
