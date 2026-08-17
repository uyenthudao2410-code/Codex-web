from __future__ import annotations

import hashlib
import json
import os
import secrets
import time
from pathlib import Path
from typing import Any

from . import __version__
from .errors import ToolFailure
from .git_utils import DIFF_CONTINUATION_OPERATION
from .orchestration_control import OrchestrationControlError, RunContext
from .patching import parse_patch
from .tool_contract import AGENT_EXECUTION_ROUTES
from .tool_schema import EVALUATION_SCHEMA_VERSION


HOST_CORRELATION_SCHEMA_VERSION = 1
HOST_CORRELATION_PENDING_TTL_MS = 120_000
HOST_CORRELATION_PENDING_RELATIVE = Path('.coding-tools') / 'evaluation' / 'chatweb-host-turn-pending.json'
HOST_CORRELATION_BINDING_RELATIVE = Path('.coding-tools') / 'evaluation' / 'chatweb-host-turn-binding.json'


class AgentWorkflowMixin:
    @staticmethod
    def _host_correlation_record(value: Any) -> dict[str, Any] | None:
        if not isinstance(value, dict):
            return None
        allowed = {"schema_version", "turn_id", "trace_id", "staged_at_unix_ms"}
        if set(value) - allowed or value.get("schema_version") != HOST_CORRELATION_SCHEMA_VERSION:
            return None
        turn_id = str(value.get("turn_id") or "").strip()
        trace_id = str(value.get("trace_id") or "").strip()
        staged_at = value.get("staged_at_unix_ms")
        if not turn_id or len(turn_id) > 128 or not trace_id or len(trace_id) > 128:
            return None
        if any(ord(char) < 32 for char in turn_id + trace_id):
            return None
        if isinstance(staged_at, bool) or not isinstance(staged_at, (int, float)):
            return None
        now_ms = time.time() * 1000
        if float(staged_at) > now_ms + 5_000 or now_ms - float(staged_at) > HOST_CORRELATION_PENDING_TTL_MS:
            return None
        return {"turn_id": turn_id, "trace_id": trace_id, "staged_at_unix_ms": float(staged_at)}

    def _claim_pending_host_turn(self) -> dict[str, Any] | None:
        pending = self.workspace.root / HOST_CORRELATION_PENDING_RELATIVE
        claim = pending.with_name(f".{pending.name}.{self.process_instance_id}.{secrets.token_urlsafe(6)}.claim")
        try:
            os.replace(pending, claim)
        except FileNotFoundError:
            return None
        except OSError:
            return None
        try:
            value = json.loads(claim.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            value = None
        record = self._host_correlation_record(value)
        if record is None:
            try:
                claim.unlink(missing_ok=True)
            except OSError:
                pass
            return None
        return {**record, "_claim_path": claim}

    def _discard_pending_host_turn(self) -> None:
        claimed = self._claim_pending_host_turn()
        claim_path = claimed.get("_claim_path") if claimed else None
        if isinstance(claim_path, Path):
            try:
                claim_path.unlink(missing_ok=True)
            except OSError:
                pass

    def _restore_pending_host_turn(self, claimed: dict[str, Any]) -> None:
        claim = claimed.get("_claim_path")
        if not isinstance(claim, Path) or not claim.exists():
            return
        pending = self.workspace.root / HOST_CORRELATION_PENDING_RELATIVE
        try:
            if pending.exists():
                claim.unlink(missing_ok=True)
            else:
                os.replace(claim, pending)
        except OSError:
            try:
                claim.unlink(missing_ok=True)
            except OSError:
                pass

    def _publish_host_turn_binding(self, claimed: dict[str, Any], ctx: RunContext) -> bool:
        target = self.workspace.root / HOST_CORRELATION_BINDING_RELATIVE
        temporary = target.with_name(f".{target.name}.{self.process_instance_id}.{secrets.token_urlsafe(6)}.tmp")
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "schema_version": HOST_CORRELATION_SCHEMA_VERSION,
                "turn_id": claimed["turn_id"],
                "trace_id": claimed["trace_id"],
                "run_id": ctx.run_id,
                "wave_id": ctx.wave_id,
                "bound_at_unix_ms": int(time.time() * 1000),
            }
            temporary.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")
            os.replace(temporary, target)
            return True
        except OSError:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            return False
        finally:
            claim = claimed.get("_claim_path")
            if isinstance(claim, Path):
                try:
                    claim.unlink(missing_ok=True)
                except OSError:
                    pass

    def _agent_patch_inputs(self, args: dict[str, Any]) -> tuple[list[str], list[str]]:
        directories = [str(item).strip() for item in args.get("directories", []) if str(item).strip()]
        patches = [str(item) for item in args.get("patches", []) if str(item).strip()]
        if str(args.get("patch", "")).strip():
            patches.insert(0, str(args["patch"]))
        new_file_patch = self._new_files_patch(list(args.get("files", [])))
        if new_file_patch:
            patches.insert(0, new_file_patch)
        return directories, patches

    def _preflight_patch_sequence(self, patches: list[str]) -> dict[str, Any]:
        """Reject predictable disjoint-patch failures before EOCL or workspace writes."""
        parsed: list[tuple[str, set[str]]] = []
        seen_paths: set[str] = set()
        overlapping_paths: set[str] = set()
        operation_count = 0
        for patch_text in patches:
            operations = parse_patch(patch_text)
            touched: set[str] = set()
            for operation in operations:
                operation_count += 1
                touched.add(str(operation.path).replace("\\", "/"))
                if operation.move_to:
                    touched.add(str(operation.move_to).replace("\\", "/"))
            overlapping_paths.update(seen_paths.intersection(touched))
            seen_paths.update(touched)
            parsed.append((patch_text, touched))
        if operation_count == 0:
            return {"checked": False, "reason": "empty_patch_sequence", "patch_count": len(patches)}
        if overlapping_paths:
            return {
                "checked": False,
                "reason": "cross_patch_path_dependency",
                "patch_count": len(patches),
                "overlap_count": len(overlapping_paths),
            }
        for patch_text, _touched in parsed:
            self.apply_patch({"patch": patch_text, "dry_run": True})
        return {"checked": True, "patch_count": len(patches), "operation_count": operation_count}

    @staticmethod
    def _new_files_patch(files: list[Any]) -> str:
        sections = ["*** Begin Patch"]
        added = 0
        for item in files[:100]:
            if not isinstance(item, dict):
                raise ToolFailure("INVALID_ARGUMENT", "Each files item must contain path and content.", category="validation")
            path = str(item.get("path", "")).strip().replace("\\", "/")
            if not path or path.startswith("/") or ".." in Path(path).parts:
                raise ToolFailure("INVALID_ARGUMENT", f"Invalid new file path: {path!r}", category="validation")
            content = str(item.get("content", ""))
            sections.append(f"*** Add File: {path}")
            lines = content.splitlines()
            sections.extend(f"+{line}" for line in lines)
            if content.endswith(("\n", "\r")) is False and lines:
                pass
            if not lines:
                sections.append("+")
            added += 1
        if not added:
            return ""
        sections.append("*** End Patch")
        return "\n".join(sections)

    def _agent_orchestration_context(
        self,
        args: dict[str, Any],
        *,
        objective: str,
    ) -> tuple[RunContext, dict[str, Any]]:
        current_task = self.task_state.get()
        projection = current_task.get("orchestration") if isinstance(current_task.get("orchestration"), dict) else {}
        run_id = str(projection.get("run_id") or "")
        current_ctx = self.orchestration_control.snapshot(run_id) if run_id else None

        if not current_task.get("task_id") or (
            str(current_task.get("status") or "") in {"completed", "stopped"}
            and (current_ctx is None or current_ctx.state in {"CHECKPOINTED", "BLOCKED", "ABORTED"})
        ):
            current_task = self.task_state.ensure_started(objective, current_step="Orchestration preflight")
            projection = current_task.get("orchestration") if isinstance(current_task.get("orchestration"), dict) else {}
            run_id = str(projection.get("run_id") or "")
            current_ctx = self.orchestration_control.snapshot(run_id) if run_id else None

        identity = self._orchestration_workspace_identity(args.get("path", "."))
        requested_mode = str(args.get("execution_mode", "auto")).strip().lower() or "auto"
        contract_fp = self.orchestration_control.stable_contract_fingerprint(args.get("contract_fingerprint", ""))
        replan_reason = str(args.get("replan_reason", "")).strip()

        if current_ctx is not None:
            if current_ctx.state == "ACCEPTING":
                raise ToolFailure(
                    "FINAL_ACCEPTANCE_REQUIRED",
                    "The previous proven wave is waiting for ChatWeb Sol acceptance. Use task_control action=accept or reject before another implementation wave.",
                    category="runtime",
                    retryable=True,
                    details={"run_id": current_ctx.run_id, "wave_id": current_ctx.wave_id},
                )
            if current_ctx.state in {"ROUTED", "EXECUTING", "PROVING"}:
                self.orchestration_control.record_failure(
                    current_ctx,
                    "RUNTIME_RESUME_REQUIRED",
                    payload={"reason": "A non-terminal wave was recovered outside its original synchronous execution."},
                )
                self._project_orchestration(current_ctx, event="orchestration_replan_required")
                raise ToolFailure(
                    "REPLAN_REQUIRED",
                    "Recovered orchestration state requires an explicit replan_reason before execution can continue.",
                    category="runtime",
                    retryable=True,
                    details={"run_id": current_ctx.run_id, "wave_id": current_ctx.wave_id},
                )
            if current_ctx.state == "REPLAN":
                if not replan_reason:
                    raise ToolFailure(
                        "REPLAN_REASON_REQUIRED",
                        "The current orchestration run is in REPLAN. Provide replan_reason to create a new wave; route/ownership may not change silently.",
                        category="runtime",
                        retryable=True,
                        details={"run_id": current_ctx.run_id, "wave_id": current_ctx.wave_id},
                    )
                current_ctx = self.orchestration_control.begin_replan_wave(
                    current_ctx,
                    execution_mode=requested_mode,
                    base_head=str(identity.get("base_head") or ""),
                    worktree_fp=str(identity.get("worktree_fp") or ""),
                    contract_fp=contract_fp,
                    reason=replan_reason,
                )
            elif current_ctx.state in {"CHECKPOINTED", "BLOCKED", "ABORTED"}:
                current_ctx = None
            elif current_ctx.state in {"PREFLIGHT", "READY"}:
                base_changed = bool(current_ctx.base_head and current_ctx.base_head != str(identity.get("base_head") or ""))
                worktree_changed = bool(current_ctx.worktree_fp and current_ctx.worktree_fp != str(identity.get("worktree_fp") or ""))
                contract_changed = bool(current_ctx.contract_fp and contract_fp and current_ctx.contract_fp != contract_fp)
                if base_changed or worktree_changed or contract_changed:
                    self.orchestration_control.record_failure(
                        current_ctx,
                        "CONTRACT_DRIFT" if contract_changed else "BASE_DRIFT",
                        payload={
                            "base_changed": base_changed,
                            "worktree_changed": worktree_changed,
                            "contract_changed": contract_changed,
                        },
                    )
                    self._project_orchestration(current_ctx, event="orchestration_drift_detected")
                    if not replan_reason:
                        raise ToolFailure(
                            "REPLAN_REASON_REQUIRED",
                            "Base/worktree/contract changed after orchestration preflight. Provide replan_reason to create a new wave.",
                            category="runtime",
                            retryable=True,
                            details={"run_id": current_ctx.run_id, "wave_id": current_ctx.wave_id},
                        )
                    current_ctx = self.orchestration_control.begin_replan_wave(
                        current_ctx,
                        execution_mode=requested_mode,
                        base_head=str(identity.get("base_head") or ""),
                        worktree_fp=str(identity.get("worktree_fp") or ""),
                        contract_fp=contract_fp,
                        reason=replan_reason,
                    )

        if current_ctx is None:
            if current_task.get("task_id") and str(current_task.get("status") or "") in {"completed", "failed", "stopped"}:
                current_task = self.task_state.update(
                    {"objective": objective, "status": "active", "failure": None, "current_step": "Orchestration preflight", "new_task": True},
                    event="task_started",
                )
            run_metadata: dict[str, Any] = {
                "workflow": str(args.get("workflow", "custom")),
                "phase": str(args.get("phase", "prepare")),
                "branch": identity.get("branch"),
            }
            evaluation = dict(args["evaluation"]) if isinstance(args.get("evaluation"), dict) else {}
            explicit_evaluation_identity = bool(
                str(evaluation.get("trace_id") or "").strip()
                or str(evaluation.get("turn_id") or "").strip()
            )
            claimed_host_turn = None
            if explicit_evaluation_identity:
                self._discard_pending_host_turn()
            else:
                claimed_host_turn = self._claim_pending_host_turn()
                if claimed_host_turn:
                    evaluation["trace_id"] = claimed_host_turn["trace_id"]
                    evaluation["turn_id"] = claimed_host_turn["turn_id"]
                    run_metadata["host_correlation"] = {
                        "schema_version": 1,
                        "source": "electron_pending_host_turn",
                        "eligible": True,
                    }
            if evaluation:
                environment_id = str(evaluation.pop("environment_id", "") or "").strip()
                evaluation.update({
                    "schema_version": EVALUATION_SCHEMA_VERSION,
                    "task_spec_fp": self._evaluation_task_spec_fingerprint(args),
                    "environment_fp": hashlib.sha256(environment_id.encode("utf-8")).hexdigest() if environment_id else "",
                    "tool_contract_fp": str(self.tool_contract.get("sha256") or ""),
                    "evaluation_schema_fp": str((self.tool_contract.get("evaluation") or {}).get("sha256") or ""),
                    "runtime_version": __version__,
                })
                run_metadata["evaluation"] = evaluation
            try:
                current_ctx = self.orchestration_control.begin(
                    objective=objective,
                    task_id=str(current_task.get("task_id") or ""),
                    execution_mode=requested_mode,
                    base_head=str(identity.get("base_head") or ""),
                    worktree_fp=str(identity.get("worktree_fp") or ""),
                    contract_fp=contract_fp,
                    metadata=run_metadata,
                )
            except Exception:
                if claimed_host_turn:
                    self._restore_pending_host_turn(claimed_host_turn)
                raise
            if claimed_host_turn:
                self._publish_host_turn_binding(claimed_host_turn, current_ctx)

        self._project_orchestration(current_ctx, event="orchestration_context_ready")
        return current_ctx, identity

    def _validate_execution_mode_route(self, requested_mode: str, route: dict[str, Any]) -> str:
        requested_mode = str(requested_mode or "auto").strip().lower() or "auto"
        selected = str(route.get("selected") or "deterministic")
        derived = self._orchestration_mode_for_route(selected)
        if requested_mode == "auto":
            return derived
        if requested_mode == "coordinated_multi_worktree":
            return requested_mode
        if requested_mode == "mcp_only" and selected != "deterministic":
            raise ToolFailure("MODE_ROUTE_MISMATCH", "mcp_only execution requires deterministic routing.", category="validation")
        if requested_mode == "bounded_candidate" and selected not in {"mini", "luna"}:
            raise ToolFailure("MODE_ROUTE_MISMATCH", "bounded_candidate execution requires Mini or Luna routing.", category="validation")
        if requested_mode == "deep_single_lane" and selected not in {"terra", "sol_xhigh", "sol_max", "sol_ultra"}:
            raise ToolFailure("MODE_ROUTE_MISMATCH", "deep_single_lane execution requires a deep model route.", category="validation")
        return requested_mode

    @staticmethod
    def _evaluation_task_spec_fingerprint(args: dict[str, Any]) -> str:
        stable = {
            "objective": str(args.get("objective") or "").strip(),
            "workflow": str(args.get("workflow") or "custom").strip().lower(),
            "path": str(args.get("path") or ".").strip(),
            "workdir": str(args.get("workdir") or args.get("path") or ".").strip(),
            "verification": str(args.get("verification") or "").strip().lower(),
            "test_command": str(args.get("test_command") or "").strip(),
            "build_command": str(args.get("build_command") or "").strip(),
        }
        encoded = json.dumps(stable, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8", errors="replace")).hexdigest()

    @staticmethod
    def _request_hash(args: dict[str, Any]) -> str:
        stable = {key: value for key, value in args.items() if key != "idempotency_key" and not key.startswith("_")}
        encoded = json.dumps(stable, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(encoded.encode("utf-8", errors="replace")).hexdigest()

    def _agent_workflow_request_hash(self, args: dict[str, Any]) -> str:
        return self._request_hash(args)

    @staticmethod
    def _agent_admission_budget(args: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        max_auto_steps = max(1, min(int(args.get("max_auto_steps", 64)), 256))
        max_tool_hops = max(1, min(int(args.get("max_tool_hops", 96)), 512))
        max_attempts = max(1, min(int(args.get("max_attempts", 1)), 10))
        max_runtime_seconds = max(1, min(int(args.get("max_runtime_seconds", 600)), 600))
        try:
            max_estimated_credits = max(0.0, float(args.get("max_estimated_credits", 0.0) or 0.0))
        except (TypeError, ValueError) as exc:
            raise ToolFailure("INVALID_ARGUMENT", "max_estimated_credits must be a non-negative number.", category="validation") from exc
        patches = len(args.get("patches", []) if isinstance(args.get("patches"), list) else []) + (1 if str(args.get("patch", "")).strip() else 0)
        files = len(args.get("files", []) if isinstance(args.get("files"), list) else [])
        directories = len(args.get("directories", []) if isinstance(args.get("directories"), list) else [])
        commands = len(args.get("commands", []) if isinstance(args.get("commands"), list) else [])
        requested_route = str(args.get("execution_route", "auto")).strip().lower() or "auto"
        candidate = 1 if requested_route in AGENT_EXECUTION_ROUTES and not patches else 0
        planned_auto_steps = 2 + patches + files + directories + commands + candidate
        if str(args.get("test_command", "")).strip():
            planned_auto_steps += 1
        if str(args.get("build_command", "")).strip():
            planned_auto_steps += 1
        planned_tool_hops = 2 + commands + (1 if patches or files or directories else 0) + candidate
        if planned_auto_steps > max_auto_steps or planned_tool_hops > max_tool_hops:
            raise ToolFailure(
                "WORKFLOW_BUDGET_EXCEEDED",
                "The planned workflow exceeds the deterministic admission budget.",
                category="policy",
                retryable=False,
                details={
                    "planned_auto_steps": planned_auto_steps,
                    "max_auto_steps": max_auto_steps,
                    "planned_tool_hops": planned_tool_hops,
                    "max_tool_hops": max_tool_hops,
                },
            )
        normalized = dict(args)
        normalized["timeout_seconds"] = min(int(args.get("timeout_seconds", 600)), max_runtime_seconds)
        budget = {
            "max_auto_steps": max_auto_steps,
            "planned_auto_steps": planned_auto_steps,
            "max_tool_hops": max_tool_hops,
            "planned_tool_hops": planned_tool_hops,
            "max_attempts": max_attempts,
            "attempts_used": 1,
            "retry_mode": "manual_replan_only",
            "max_runtime_seconds": max_runtime_seconds,
            "max_estimated_credits": max_estimated_credits,
        }
        normalized["_admission_budget"] = budget
        return normalized, budget

    @staticmethod
    def _agent_idempotency_summary(result: dict[str, Any]) -> dict[str, Any]:
        execution = result.get("execution") if isinstance(result.get("execution"), dict) else {}
        orchestration = result.get("orchestration") if isinstance(result.get("orchestration"), dict) else {}
        proof = execution.get("proof_summary") if isinstance(execution.get("proof_summary"), dict) else {}
        review = result.get("external_review") if isinstance(result.get("external_review"), dict) else {}
        return {
            "workflow": result.get("workflow"),
            "phase": result.get("phase"),
            "execution_status": execution.get("status"),
            "execution_ok": execution.get("ok"),
            "run_id": orchestration.get("run_id"),
            "wave_id": orchestration.get("wave_id"),
            "orchestration_state": orchestration.get("orchestration_state"),
            "proof_fingerprint": proof.get("proof_fingerprint"),
            "external_review_status": review.get("status"),
            "reports": orchestration.get("reports"),
        }

    def agent_workflow(self, args: dict[str, Any]) -> dict[str, Any]:
        normalized, budget = self._agent_admission_budget(args)
        phase = str(normalized.get("phase", "prepare")).lower()
        idempotency_key = str(normalized.get("idempotency_key", "") or "").strip()
        if idempotency_key and len(idempotency_key) > 128:
            raise ToolFailure("INVALID_ARGUMENT", "idempotency_key must be at most 128 characters.", category="validation")
        if phase not in {"execute", "run"} or not idempotency_key:
            result = self._agent_workflow_impl(normalized)
            result["admission_budget"] = budget
            if idempotency_key:
                result["idempotency"] = {"active": False, "reason": "prepare_resume_not_mutating"}
            return result

        request_hash = self._agent_workflow_request_hash(args)
        projection = self.task_state.get().get("orchestration", {})
        run_id = str(projection.get("run_id") or "") if isinstance(projection, dict) else ""
        wave_id = str(projection.get("wave_id") or "") if isinstance(projection, dict) else ""
        claim = self.orchestration_ledger.claim_idempotency(
            idempotency_key=idempotency_key,
            operation="agent_workflow",
            request_hash=request_hash,
            process_instance_id=self.process_instance_id,
            run_id=run_id,
            wave_id=wave_id,
        )
        if not claim.get("claimed"):
            reason = str(claim.get("reason") or "")
            record = claim.get("record") if isinstance(claim.get("record"), dict) else {}
            if reason == "conflict":
                raise ToolFailure(
                    "IDEMPOTENCY_CONFLICT",
                    "The idempotency_key was already used for a different agent_workflow request.",
                    category="validation",
                    details={"idempotency_key": idempotency_key, "status": record.get("status")},
                )
            if reason == "completed":
                return {
                    "workflow": record.get("summary", {}).get("workflow"),
                    "phase": record.get("summary", {}).get("phase"),
                    "deduplicated": True,
                    "durable_idempotency": True,
                    "idempotency": record,
                    "admission_budget": budget,
                    "recommended_next_action": "Use the recorded run/wave/report pointers; do not repeat the mutation.",
                }
            if reason == "failed":
                raise ToolFailure(
                    "IDEMPOTENT_REQUEST_FAILED",
                    "This exact idempotent workflow request already reached a known terminal failure; do not repeat it unchanged.",
                    category="runtime",
                    details={"idempotency_key": idempotency_key, "summary": record.get("summary")},
                )
            if reason == "unknown":
                raise ToolFailure(
                    "IDEMPOTENCY_OUTCOME_UNKNOWN",
                    "A previous process may have started this idempotent workflow but its outcome is unknown. Reconcile evidence before any replay.",
                    category="runtime",
                    details={"idempotency_key": idempotency_key, "summary": record.get("summary")},
                )
            raise ToolFailure(
                "IDEMPOTENCY_IN_PROGRESS",
                "This idempotent workflow is already in progress; observe the existing task instead of starting another copy.",
                category="runtime",
                retryable=True,
                details={"idempotency_key": idempotency_key, "run_id": record.get("run_id"), "wave_id": record.get("wave_id")},
            )

        try:
            result = self._agent_workflow_impl(normalized)
        except Exception as exc:
            preflight_known_terminal = bool(
                isinstance(exc, ToolFailure)
                and isinstance(exc.details, dict)
                and exc.details.get("workflow_patch_preflight") is True
            )
            known_terminal = preflight_known_terminal or (isinstance(exc, ToolFailure) and exc.code in {
                "WORKFLOW_BUDGET_EXCEEDED", "WORKFLOW_CREDIT_BUDGET_EXCEEDED", "INVALID_ARGUMENT", "MODE_ROUTE_MISMATCH"
            })
            self.orchestration_ledger.finish_idempotency(
                idempotency_key,
                request_hash=request_hash,
                status="failed" if known_terminal else "unknown",
                summary={
                    "error_code": getattr(exc, "code", type(exc).__name__),
                    "category": getattr(exc, "category", "runtime"),
                    "outcome_unknown": not known_terminal,
                    "workflow_patch_preflight": preflight_known_terminal,
                },
            )
            raise
        summary = self._agent_idempotency_summary(result)
        orchestration = result.get("orchestration") if isinstance(result.get("orchestration"), dict) else {}
        record = self.orchestration_ledger.finish_idempotency(
            idempotency_key,
            request_hash=request_hash,
            status="completed",
            summary=summary,
            run_id=str(orchestration.get("run_id") or ""),
            wave_id=str(orchestration.get("wave_id") or ""),
        )
        result["idempotency"] = record
        result["durable_idempotency"] = True
        result["admission_budget"] = budget
        return result

    def _agent_workflow_impl(self, args: dict[str, Any]) -> dict[str, Any]:
        """End-to-end workflow with durable wave audit, explicit authority, proof, and final acceptance state."""
        workflow = str(args.get("workflow", "custom")).lower()
        phase = str(args.get("phase", "prepare")).lower()
        dedup_key = self._fast_cache_key("agent_workflow_execute", args)
        if phase in {"execute", "run"}:
            cached_execution = self._fast_cache_get(dedup_key, 30)
            current_projection = self.task_state.get().get("orchestration", {})
            if cached_execution is not None and str(current_projection.get("orchestration_state") or "") != "REPLAN":
                cached_execution["deduplicated"] = True
                return cached_execution
        supported = {"bugfix", "feature", "greenfield", "refactor", "test_failure", "build_release", "diagnose", "document", "resume", "custom"}
        if workflow not in supported:
            raise ToolFailure("INVALID_ARGUMENT", f"Unknown workflow: {workflow}", category="validation")
        if phase not in {"prepare", "execute", "run", "resume"}:
            raise ToolFailure("INVALID_ARGUMENT", f"Unknown workflow phase: {phase}", category="validation")

        continuation = str(args.get("continuation", "") or "").strip()
        if continuation:
            if phase != "resume":
                raise ToolFailure(
                    "INVALID_ARGUMENT",
                    "agent_workflow continuation is only valid with phase=resume.",
                    category="validation",
                )
            continuation_args: dict[str, Any] = {"continuation": continuation}
            if "paths" in args:
                continuation_args["paths"] = args.get("paths")
            page = self.git_diff(continuation_args)
            return {
                "workflow": workflow,
                "phase": "resume",
                "continuation_kind": DIFF_CONTINUATION_OPERATION,
                "git_diff": page,
                "task": self.task_state.get(),
                "recommended_next_action": (
                    "Continue with the returned continuation while truncated=true; do not repeat the original broad diff read."
                    if page.get("truncated")
                    else "The source-fenced diff continuation is complete."
                ),
            }

        objective = str(args.get("objective", "")).strip() or str(self.task_state.get().get("objective", "")).strip()
        if workflow == "resume" or phase == "resume":
            state = self.task_state.get()
            orchestration = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
            context_args = {
                "objective": objective,
                "path": args.get("path", "."),
                "queries": args.get("queries", []),
                "paths": args.get("paths", []),
                "max_files": args.get("max_files", 12),
                "max_total_bytes": args.get("max_total_bytes", 262144),
                "force_refresh": True,
            }
            context = self.prepare_coding_context(context_args)
            context["task_resume"] = {
                "task_id": state.get("task_id"),
                "status": state.get("status"),
                "current_step": state.get("current_step"),
                "next_step": state.get("next_step"),
                "orchestration": dict(orchestration),
            }
            run_id = str(orchestration.get("run_id") or "").strip()
            wave_id = str(orchestration.get("wave_id") or "").strip()
            if run_id:
                try:
                    evidence = self.orchestration_ledger.session_query(run_id, wave_id=wave_id, limit=12)
                except ValueError as exc:
                    evidence = {
                        "schema_version": 1,
                        "status": "unavailable",
                        "run_id": run_id,
                        "wave_id": wave_id or None,
                        "reason": str(exc),
                        "query": {"run_id": run_id, "wave_id": wave_id or None, "limit": 12, "mode": "model_free_priority"},
                        "model_free": True,
                        "raw_transcript_included": False,
                    }
            else:
                evidence = {
                    "schema_version": 1,
                    "status": "unlinked",
                    "run_id": None,
                    "wave_id": None,
                    "query": {"run_id": None, "wave_id": None, "limit": 12, "mode": "model_free_priority"},
                    "model_free": True,
                    "raw_transcript_included": False,
                }
            return {
                "workflow": workflow,
                "phase": "resume",
                "task": state,
                "context": context,
                "evidence": evidence,
                "recommended_next_action": "Continue from task.next_step. Do not repeat completed searches, reads, commands, tests, or builds.",
            }

        if workflow == "document":
            document_args = dict(args.get("document", {}))
            if not document_args:
                document_args = {key: args[key] for key in ("action", "path", "paths", "source", "target", "title", "content", "overwrite", "max_chars") if key in args}
            result = self.document_workflow(document_args)
            return {"workflow": workflow, "phase": phase, "result": result, "task": self.task_state.get()}

        objective = objective or f"Complete {workflow} workflow"
        directories, explicit_patches = self._agent_patch_inputs(args)
        if phase in {"execute", "run"} and explicit_patches:
            try:
                self._preflight_patch_sequence(explicit_patches)
            except ToolFailure as exc:
                exc.details = {**exc.details, "workflow_patch_preflight": True}
                raise
        ctx, initial_identity = self._agent_orchestration_context(args, objective=objective)
        requested_mode = str(args.get("execution_mode", "auto")).strip().lower() or "auto"
        requested_execution_route = str(args.get("execution_route", "auto")).strip().lower() or "auto"
        if requested_mode == "mcp_only":
            requested_execution_route = "deterministic"
        elif requested_mode == "deep_single_lane" and requested_execution_route == "auto":
            requested_execution_route = "sol_xhigh"
        if requested_mode == "coordinated_multi_worktree" and phase in {"execute", "run"}:
            self.orchestration_control.record_failure(
                ctx,
                "SUPERVISOR_NOT_READY",
                payload={"reason": "No production multi-worktree supervisor adapter is registered in Coding Tools MCP."},
            )
            self._project_orchestration(ctx, event="coordination_not_ready")
            self.task_state.update({
                "status": "waiting",
                "failure": "SUPERVISOR_NOT_READY",
                "current_step": "Replan execution mode",
                "next_step": "Provide replan_reason and select deep_single_lane or activate a verified coordination adapter.",
            })
            return {
                "workflow": workflow,
                "phase": phase,
                "execution": {"ok": False, "status": "blocked", "reason": "SUPERVISOR_NOT_READY"},
                "orchestration": self._orchestration_result(ctx),
                "task": self.task_state.get(),
            }

        should_prepare = phase in {"prepare", "run"}
        should_execute = phase in {"execute", "run"}
        prepared = None
        if should_prepare:
            prepared = self.prepare_coding_context({
                "objective": objective,
                "path": args.get("path", "."),
                "queries": args.get("queries", []),
                "paths": args.get("paths", []),
                "regex": args.get("regex", False),
                "case_sensitive": args.get("case_sensitive", False),
                "include_globs": args.get("include_globs", []),
                "exclude_globs": args.get("exclude_globs", []),
                "max_files": args.get("max_files", 12),
                "max_entries": args.get("max_entries", 120),
                "max_matches_per_query": args.get("max_matches_per_query", 20),
                "max_total_bytes": args.get("max_total_bytes", 262144),
                "force_refresh": args.get("force_refresh", False),
            })
            self.orchestration_ledger.append_event(
                ctx.run_id,
                wave_id=ctx.wave_id,
                event_type="context_prepared",
                state_before=ctx.state,
                state_after=ctx.state,
                payload={
                    "selected_paths": list(prepared.get("selected_paths") or [])[:40] if isinstance(prepared, dict) else [],
                    "total_content_bytes": int(prepared.get("total_content_bytes") or 0) if isinstance(prepared, dict) else 0,
                    "queries": len(args.get("queries", [])),
                    "composite_read": {
                        "plan_sha256": str((((prepared.get("composite_read") or {}).get("plan") or {}).get("plan_sha256") or "")) if isinstance(prepared, dict) else "",
                        "operation_count": int((((prepared.get("composite_read") or {}).get("execution") or {}).get("operation_count") or 0)) if isinstance(prepared, dict) else 0,
                        "phase_timing": dict((((prepared.get("composite_read") or {}).get("execution") or {}).get("phase_timing") or {})) if isinstance(prepared, dict) else {},
                        "cache_hit": bool(((prepared.get("composite_read") or {}).get("cache") or {}).get("hit")) if isinstance(prepared, dict) else False,
                    },
                },
            )
        if not should_execute:
            self._project_orchestration(ctx, event="orchestration_prepared")
            return {
                "workflow": workflow,
                "phase": "prepare",
                "context": prepared,
                "orchestration": self._orchestration_result(ctx, write_reports=False),
                "recommended_next_action": "Reason once over this bundle, then call agent_workflow phase=execute with the complete change set and verification plan.",
            }

        patches = list(explicit_patches)
        default_verification = {
            "bugfix": "tests", "feature": "tests", "greenfield": "all", "refactor": "tests",
            "test_failure": "tests", "build_release": "all", "diagnose": "none", "custom": "tests",
        }[workflow]
        verification = str(args.get("verification", default_verification)).lower()

        explicit_model_route = requested_execution_route not in {"auto", "deterministic"}
        execution_route: dict[str, Any]
        candidate_result: dict[str, Any] | None = None
        candidate_proof: dict[str, Any] = {
            "verification": verification,
            "commands": list(args.get("commands", args.get("checks", [])))[:6],
            "test_command": str(args.get("test_command", "")),
            "build_command": str(args.get("build_command", "")),
        }
        strong_oracle = False
        candidate_branch = not patches and (phase == "run" or explicit_model_route) and not directories
        if candidate_branch:
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
                    "force_refresh": args.get("force_refresh", False),
                })
            preflight_timeout_ms = min(max(int(args.get("timeout_seconds", 600)) * 1_000, 1_000), 120_000)
            candidate_workdir = str(args.get("workdir", args.get("path", ".")))
            if candidate_proof["test_command"]:
                candidate_proof["preflight_test"] = self._run_continuous_check(candidate_proof["test_command"], candidate_workdir, preflight_timeout_ms)
            elif candidate_proof["build_command"]:
                candidate_proof["preflight_build"] = self._run_continuous_check(candidate_proof["build_command"], candidate_workdir, preflight_timeout_ms)
            strong_oracle = any(
                isinstance(candidate_proof.get(key), dict) and candidate_proof[key].get("exit_code") not in {None, 0}
                for key in ("preflight_test", "preflight_build")
            )
            self.orchestration_ledger.append_event(
                ctx.run_id,
                wave_id=ctx.wave_id,
                event_type="oracle_preflight",
                state_before=ctx.state,
                state_after=ctx.state,
                payload={"strong_oracle": strong_oracle, "verification": verification},
            )

        if patches:
            execution_route = {
                "requested": requested_execution_route,
                "selected": "deterministic",
                "reason": "caller_supplied_change_set",
                "profile": None,
                "model": None,
                "effort": None,
                "high_cost": False,
            }
        else:
            execution_route = self._select_agent_execution_route(
                workflow=workflow,
                prepared=prepared,
                requested=requested_execution_route,
                allow_high_cost=bool(args.get("allow_high_cost", False)),
                strong_oracle=strong_oracle,
            )

        try:
            resolved_mode = self._validate_execution_mode_route(requested_mode, execution_route)
        except ToolFailure as exc:
            self.orchestration_control.record_failure(ctx, exc.code, payload={"selected_route": execution_route.get("selected")})
            self._project_orchestration(ctx, event="mode_route_mismatch")
            raise
        self.orchestration_control.resolve_execution_mode(ctx, resolved_mode)
        if ctx.state == "PREFLIGHT":
            self.orchestration_control.mark_ready(ctx, readiness={"ready": True, "base_head": ctx.base_head, "worktree_fp": ctx.worktree_fp})
        self.orchestration_control.select_route(ctx, execution_route)
        self._project_orchestration(ctx, event="orchestration_routed")

        if candidate_branch and execution_route.get("selected") != "deterministic":
            allowed_scope = list(prepared.get("selected_paths") or []) if isinstance(prepared, dict) else []
            self.orchestration_control.start_delegation(
                ctx,
                authority_owner=f"CODEX:{execution_route.get('selected')}",
                route=execution_route,
                allowed_scope=allowed_scope,
                metadata={"candidate_only": True, "authoritative_write": False},
            )
            candidate_result = self._generate_agent_candidate(
                workflow=workflow,
                objective=objective,
                prepared=prepared or {},
                requested_route=requested_execution_route,
                allow_high_cost=bool(args.get("allow_high_cost", False)),
                proof=candidate_proof,
                routing=execution_route,
                orchestration_ctx=ctx,
            )
            self.orchestration_control.finish_delegation(
                ctx,
                status="accepted_candidate" if candidate_result.get("status") == "ready" else "blocked",
                metadata={
                    "candidate_status": candidate_result.get("status"),
                    "reason": candidate_result.get("reason"),
                    "wall_time_ms": candidate_result.get("wall_time_ms"),
                    "economics": candidate_result.get("economics"),
                },
            )
            execution_route = dict(candidate_result.get("routing") or execution_route)
            execution_route.update({
                "candidate_status": candidate_result.get("status"),
                "model_status": candidate_result.get("model_status"),
                "wall_time_ms": candidate_result.get("wall_time_ms"),
                "economics": candidate_result.get("economics"),
                "deadline_hit": candidate_result.get("deadline_hit", False),
                "summary": candidate_result.get("summary"),
                "confidence": candidate_result.get("confidence"),
            })
            if candidate_result.get("status") == "ready":
                budget = args.get("_admission_budget") if isinstance(args.get("_admission_budget"), dict) else {}
                economics = candidate_result.get("economics") if isinstance(candidate_result.get("economics"), dict) else {}
                estimated_credits = economics.get("estimated_credits")
                credit_cap = float(budget.get("max_estimated_credits") or 0.0)
                if credit_cap > 0 and isinstance(estimated_credits, (int, float)) and float(estimated_credits) > credit_cap:
                    self.orchestration_control.record_failure(
                        ctx,
                        "WORKFLOW_CREDIT_BUDGET_EXCEEDED",
                        payload={"estimated_credits": float(estimated_credits), "max_estimated_credits": credit_cap},
                        block=True,
                    )
                    self._project_orchestration(ctx, event="credit_budget_exceeded")
                    raise ToolFailure(
                        "WORKFLOW_CREDIT_BUDGET_EXCEEDED",
                        "The candidate route exceeded the configured estimated-credit budget before mutation.",
                        category="policy",
                        details={"estimated_credits": float(estimated_credits), "max_estimated_credits": credit_cap},
                    )
                patches.extend(str(item) for item in candidate_result.get("patches", []) if str(item).strip())
            elif candidate_result.get("status") != "deterministic":
                if ctx.state not in {"REPLAN", "BLOCKED", "ABORTED"}:
                    self.orchestration_control.record_failure(ctx, candidate_result.get("reason", "CANDIDATE_NOT_READY"))
                self._project_orchestration(ctx, event="candidate_blocked")
                self.task_state.update({
                    "status": "waiting",
                    "failure": str(candidate_result.get("reason") or "candidate_not_ready"),
                    "current_step": "Replan required",
                    "next_step": "Provide replan_reason with new evidence/scope/route; do not retry unchanged.",
                })
                execution = {
                    "ok": False,
                    "status": "blocked",
                    "reason": candidate_result.get("reason", "candidate_not_ready"),
                    "recommended_next_action": candidate_result.get(
                        "recommended_next_action",
                        "Return the blocked candidate evidence to ChatWeb Sol and explicitly replan; do not run a serial model cascade.",
                    ),
                }
                return {
                    "workflow": workflow,
                    "phase": "run" if phase == "run" else "execute",
                    "prepared": prepared,
                    "directories": None,
                    "execution_route": execution_route,
                    "execution": execution,
                    "external_review": {"plane": "none", "status": "skipped", "reason": "execution_not_accepted"},
                    "orchestration": self._orchestration_result(ctx),
                    "task": self.task_state.get(),
                }

        identity_before_write = self._orchestration_workspace_identity(args.get("path", "."))
        if (
            (ctx.base_head and ctx.base_head != str(identity_before_write.get("base_head") or ""))
            or (ctx.worktree_fp and ctx.worktree_fp != str(identity_before_write.get("worktree_fp") or ""))
        ):
            self.orchestration_control.record_failure(ctx, "BASE_DRIFT", payload={"stage": "before_write"})
            self._project_orchestration(ctx, event="base_drift_before_write")
            self.task_state.update({"status": "waiting", "failure": "BASE_DRIFT", "next_step": "Replan against the current base/worktree."})
            return {
                "workflow": workflow,
                "phase": "run" if phase == "run" else "execute",
                "prepared": prepared,
                "execution_route": execution_route,
                "execution": {"ok": False, "status": "blocked", "reason": "BASE_DRIFT"},
                "orchestration": self._orchestration_result(ctx),
                "task": self.task_state.get(),
            }

        allowed_write_paths = list(candidate_result.get("allowed_paths") or []) if isinstance(candidate_result, dict) else []
        self.orchestration_control.acquire_write_lease(
            ctx,
            owner="MCP",
            mode=resolved_mode,
            allowed_paths=allowed_write_paths,
            delegation_id=ctx.delegation_id,
        )
        self._project_orchestration(ctx, event="mcp_write_lease_active")

        directory_result = None
        try:
            if directories:
                self.orchestration_control.assert_write_allowed(ctx, owner="MCP")
                directory_result = self.file_batch({
                    "operations": [{"action": "mkdir", "path": path, "parents": True, "exist_ok": True} for path in directories],
                    "dry_run": args.get("dry_run", False),
                })
            execution = self.apply_changes_and_verify({
                "objective": objective,
                "patches": patches,
                "checks": args.get("commands", args.get("checks", [])),
                "path": args.get("path", "."),
                "workdir": args.get("workdir", args.get("path", ".")),
                "verification": verification,
                "test_command": args.get("test_command", ""),
                "build_command": args.get("build_command", ""),
                "artifact_paths": args.get("artifact_paths", []),
                "hash_algorithm": args.get("hash_algorithm", "sha256"),
                "timeout_ms": args.get("timeout_ms", 600000),
                "timeout_seconds": args.get("timeout_seconds", 600),
                "include_diff": args.get("include_diff", True),
                "max_diff_bytes": args.get("max_diff_bytes", 131072),
                "dry_run": args.get("dry_run", False),
                "_orchestration_context": ctx,
            })
        except (ToolFailure, OrchestrationControlError) as exc:
            code = getattr(exc, "code", type(exc).__name__)
            if ctx.state not in {"REPLAN", "BLOCKED", "ABORTED"}:
                self.orchestration_control.record_failure(ctx, code)
            self._project_orchestration(ctx, event="execution_exception")
            self.task_state.update({"status": "waiting", "failure": str(code), "current_step": "Replan required", "next_step": "Provide replan_reason after correcting the failure cause."})
            raise

        if not execution.get("ok"):
            error = execution.get("error") if isinstance(execution.get("error"), dict) else {}
            if ctx.state not in {"REPLAN", "BLOCKED", "ABORTED"}:
                self.orchestration_control.record_failure(ctx, error.get("code") or execution.get("reason") or "EXECUTION_FAILED")
            self._project_orchestration(ctx, event="execution_failed")
            result = {
                "workflow": workflow,
                "phase": "run" if phase == "run" else "execute",
                "prepared": prepared,
                "directories": directory_result,
                "execution_route": execution_route,
                "execution": execution,
                "external_review": {"plane": "none", "status": "skipped", "reason": "execution_not_accepted"},
                "orchestration": self._orchestration_result(ctx),
                "task": self.task_state.get(),
            }
            return result

        self._invalidate_fast_cache()
        external_review = self._maybe_agent_workflow_external_review(
            workflow=workflow,
            objective=objective,
            verification=verification,
            execution=execution,
            dry_run=bool(args.get("dry_run", False)),
        )
        if ctx.state == "PROVING":
            self.orchestration_control.mark_accepting(
                ctx,
                proof_summary={
                    **(execution.get("proof_summary") or {}),
                    "external_review_plane": external_review.get("plane"),
                    "external_review_status": external_review.get("status"),
                },
            )
        self._project_orchestration(ctx, event="awaiting_final_acceptance")
        self.task_state.update({
            "status": "waiting",
            "current_step": "Waiting for ChatWeb Sol acceptance",
            "next_step": "Present orchestration.completion_report to the operator, inspect diff/proof/review, then call task_control action=accept or reject.",
            "failure": None,
            "orchestration": ctx.projection(),
        }, event="final_acceptance_required")
        result = {
            "workflow": workflow,
            "phase": "run" if phase == "run" else "execute",
            "prepared": prepared,
            "directories": directory_result,
            "execution_route": execution_route,
            "execution": execution,
            "external_review": external_review,
            "orchestration": self._orchestration_result(ctx),
            "task": self.task_state.get(),
        }
        self._fast_cache_put(dedup_key, result)
        return result
