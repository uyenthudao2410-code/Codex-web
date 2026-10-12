from __future__ import annotations

"""Bounded durable execution ledger cursor and runtime driver for an existing RUN.

Immutable proposal, scope, policy, and consent validation live in
continuation_contract.py. This module owns only durable continuation state,
driver fencing, and the runtime-facing continuation flow.
"""

import hashlib
import json
import sqlite3
from typing import Any, Iterable

from .continuation_contract import (
    RUN_CONTINUATION_LEASE_SECONDS,
    RUN_CONTINUATION_MAX_NEW_FILES,
    RUN_CONTINUATION_MAX_REPLACEMENTS,
    RUN_CONTINUATION_PROPOSAL_SCHEMA,
    RUN_CONTINUATION_PROFILE,
    RUN_CONTINUATION_ROUTE,
    RUN_CONTINUATION_SCHEMA_VERSION,
    RunContinuationError,
    _bounded,
    _canonical_json,
    _contains_sensitive_model_content,
    _event_sanitize,
    _normalize_effect_artifact_path,
    _normalize_path,
    _normalize_paths,
    _normalize_technical_replan,
    _now_ms,
    _policy_projection,
    _require_opaque,
    _require_sha256,
    _utc_now,
    bind_run_continuation_consent,
    build_goal_continuation_policy,
    build_run_continuation_policy,
    continuation_consent_descriptor,
    parse_run_continuation_proposal,
)
from .errors import ToolFailure
from .continuation_consent_http import CONTINUATION_CONSENT_HTTP_PATH
from .controller_continuity import ControllerContinuityError
from .controller_reattach import run_binding_from_metadata as _controller_run_binding_from_metadata
from .host_correlation import (
    claim_pending_continuation_consent,
    consume_pending_continuation_consent,
    restore_pending_continuation_consent,
)
from .ledger_event_chain import append_hash_chained_event
from .run_continuation_ledger import GOAL_CONTINUATION_NO_PROGRESS, RunContinuationLedgerMixin  # noqa: F401  # compatibility re-export


class RunContinuationMixin:
    """Grant/control hooks; the separated driver owns model observation and effects."""

    def _run_continuation_value(self, args: dict[str, Any], *, workflow: str, phase: str) -> str | dict[str, Any]:
        raw = args.get("continuation")
        if isinstance(raw, dict):
            return self._run_continuation_grant(args, raw)
        if raw is not None and not isinstance(raw, str):
            raise ToolFailure(
                "INVALID_ARGUMENT",
                "agent_workflow continuation must be either the legacy source-fenced token or an explicit continuation grant request object.",
                category="validation",
            )
        return str(raw or "").strip()

    @staticmethod
    def _run_continuation_tool_failure(exc: RunContinuationError) -> ToolFailure:
        return ToolFailure(exc.code, str(exc), category="security" if "DENIED" in exc.code or "REQUIRED" in exc.code else "validation", retryable=exc.retryable, details=exc.details)

    def _run_continuation_http_challenge(
        self,
        *,
        policy: dict[str, Any],
        controller: dict[str, Any],
        descriptor: dict[str, Any],
    ) -> dict[str, Any]:
        """Issue a local approval only for the current attested ChatWeb turn."""
        host_turn = self._attested_chatweb_transport_turn()
        origin = str(getattr(self, "run_continuation_consent_http_origin", "") or "").rstrip("/")
        store = getattr(self, "run_continuation_consent_challenges", None)
        if host_turn is None or not origin or store is None:
            return {}
        issued = store.issue(
            descriptor=descriptor,
            policy=policy,
            controller=controller,
            host_turn=host_turn,
        )
        return {
            "approval_url": f"{origin}{CONTINUATION_CONSENT_HTTP_PATH}#{issued['token']}",
            "approval_challenge_id": issued["challenge_id"],
            "approval_descriptor_sha256": issued["descriptor_sha256"],
            "approval_expires_at_unix_ms": issued["expires_at_unix_ms"],
            "approval_behavior": "A local explicit button press grants and starts this exact bounded continuation. The page is unavailable through the managed tunnel, and its one-shot token is never sent in the URL request target.",
        }

    def _run_continuation_approve_http_challenge(self, approved: dict[str, Any]) -> dict[str, Any]:
        """Finalize one loopback approval without borrowing a later ChatWeb turn."""
        policy = approved.get("policy") if isinstance(approved.get("policy"), dict) else {}
        receipt = approved.get("receipt") if isinstance(approved.get("receipt"), dict) else {}
        controller = approved.get("controller") if isinstance(approved.get("controller"), dict) else {}
        goal_scope = str(policy.get("scope_kind") or "") == "goal_episode"
        run_id = str(policy.get("origin_run_id") if goal_scope else policy.get("run_id") or "").strip()
        if not run_id:
            raise ToolFailure("RUN_CONTINUATION_APPROVAL_INVALID", "The local approval has no exact RUN binding.", category="security")
        try:
            bound_policy = bind_run_continuation_consent(policy, receipt)
        except RunContinuationError as exc:
            raise self._run_continuation_tool_failure(exc) from exc
        self._run_continuation_assert_runtime(bound_policy)
        current_ctx = self.orchestration_control.snapshot(run_id)
        expected_wave = str(bound_policy.get("origin_wave_id") if goal_scope else bound_policy.get("grant_wave_id") or "")
        if current_ctx is None or str(current_ctx.wave_id) != expected_wave:
            raise ToolFailure("RUN_CONTINUATION_WAVE_STALE", "The RUN/WAVE changed before local approval.", category="security")
        if goal_scope:
            try:
                # The approval POST is loopback HTTP, not an attested ChatWeb
                # transport turn. Revalidate the exact controller identity that
                # was already frozen into the attested challenge instead of
                # re-deriving controller identity from this HTTP request.
                goal_precondition = self.orchestration_ledger.controller_goal_run_precondition(
                    workspace_id=str(bound_policy.get("workspace_id") or ""),
                    problem_id=str(bound_policy.get("problem_id") or ""),
                    problem_revision=int(bound_policy.get("problem_revision") or 0),
                    owner_client_id=str(bound_policy.get("controller_owner_client_id") or ""),
                    controller_endpoint_id=str(bound_policy.get("controller_endpoint_id") or ""),
                )
            except ControllerContinuityError as exc:
                raise self._continuity_tool_failure(exc) from exc
            if (
                int(goal_precondition.get("expected_generation") or 0) != int(bound_policy.get("controller_generation") or 0)
                or str(goal_precondition.get("owner_client_id") or "") != str(bound_policy.get("controller_owner_client_id") or "")
                or str(goal_precondition.get("controller_endpoint_id") or "") != str(bound_policy.get("controller_endpoint_id") or "")
            ):
                raise ToolFailure("RUN_CONTINUATION_CONTROLLER_CHANGED", "Goal controller authority changed after the approval challenge was issued.", category="security")
        current_controller = self.orchestration_ledger.peek_controller_lease(run_id) or {}
        if (
            str(current_controller.get("status") or "") == "active"
            and (
                str(current_controller.get("owner_client_id") or "") != str(controller.get("owner_client_id") or "")
                or int(current_controller.get("fencing_token") or 0) != int(controller.get("fencing_token") or 0)
            )
        ):
            raise ToolFailure("RUN_CONTINUATION_CONTROLLER_CHANGED", "Controller authority changed after the approval challenge was issued.", category="security")
        issuer_receipt = hashlib.sha256(
            _canonical_json({
                "run_id": run_id,
                "episode_id": str(bound_policy.get("episode_id") or ""),
                "controller_generation": int(bound_policy.get("controller_generation") or 0),
                "controller_endpoint_id": str(bound_policy.get("controller_endpoint_id") or ""),
                "controller_lease_id": controller.get("lease_id"),
                "controller_fencing_token": controller.get("fencing_token"),
                "controller_client_id": str(bound_policy.get("issuer_client_id") or ""),
                "tool_contract_sha256": self.tool_contract.get("sha256"),
                "consent_receipt_id": receipt.get("receipt_id"),
                "consent_scope_sha256": continuation_consent_descriptor(bound_policy)["scope_sha256"],
            }).encode("utf-8")
        ).hexdigest()
        try:
            if goal_scope:
                goal_issued = self.orchestration_ledger.issue_goal_continuation(
                    policy=bound_policy,
                    issuer_receipt_sha256=issuer_receipt,
                )
                parent = goal_issued["goal_continuation"]
                materialized = self.orchestration_ledger.materialize_goal_continuation(
                    run_id=run_id,
                    episode_id=str(parent["episode_id"]),
                    grant_wave_id=str(current_ctx.wave_id),
                )
                issued = {
                    "status": goal_issued.get("status"),
                    "idempotent": bool(goal_issued.get("idempotent")) and bool(materialized.get("idempotent")),
                    "continuation": materialized["continuation"],
                    "goal_continuation": parent,
                }
            else:
                issued = self.orchestration_ledger.issue_run_continuation(
                    run_id=run_id,
                    policy=bound_policy,
                    issuer_receipt_sha256=issuer_receipt,
                )
        except RunContinuationError as exc:
            raise self._run_continuation_tool_failure(exc) from exc
        self._project_orchestration(current_ctx, event="goal_continuation_granted" if goal_scope else "run_continuation_granted")
        try:
            started = self._run_continuation_start_driver({"run_id": run_id})
        except ToolFailure as exc:
            return {
                "run_id": run_id,
                "status": "GRANTED_NOT_STARTED",
                "grant_status": issued.get("status"),
                "code": exc.code,
                "message": exc.message,
            }
        return {
            **started,
            "grant_status": issued.get("status"),
            "continuation": issued.get("continuation"),
            **({"goal_continuation": issued.get("goal_continuation")} if goal_scope else {}),
            "approval_challenge_id": approved.get("challenge_id"),
        }

    def _run_continuation_grant(self, args: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
        workflow = str(args.get("workflow") or "custom").strip().lower()
        phase = str(args.get("phase") or "prepare").strip().lower()
        if phase != "prepare" or workflow not in {"bugfix", "feature"}:
            raise ToolFailure(
                "RUN_CONTINUATION_GRANT_PHASE_INVALID",
                "A continuation grant is explicit preflight authority for a bounded bugfix or feature RUN; it cannot be attached to arbitrary execution/resume phases.",
                category="validation",
            )
        objective = str(args.get("objective") or self.task_state.get().get("objective") or "").strip()
        if not objective:
            raise ToolFailure("RUN_CONTINUATION_OBJECTIVE_REQUIRED", "A continuation grant requires a non-empty existing RUN objective.", category="validation")
        ctx, identity = self._agent_orchestration_context(args, objective=objective)
        controller = self._require_hub_controller(ctx.run_id)
        if controller is None:
            raise ToolFailure(
                "RUN_CONTINUATION_CONTROLLER_REQUIRED",
                "A background continuation grant is denied without the authenticated active ChatWeb controller; missing identity is never a trusted-local bypass.",
                category="security",
            )
        hub = self._current_hub_client() or {}
        if (
            str(hub.get("client_type") or "") != "chatweb"
            or str(hub.get("role") or "") != "controller"
            or str(hub.get("identity_source") or "") != "attested_transport"
            or hub.get("attestation_verified") is not True
        ):
            raise ToolFailure(
                "RUN_CONTINUATION_CONTROLLER_ATTESTATION_REQUIRED",
                "A continuation grant requires an attested ChatWeb controller identity, not a copied hub_client object.",
                category="security",
            )
        binding = self.orchestration_ledger.controller_run_problem_binding(ctx.run_id)
        if not isinstance(binding, dict):
            raise ToolFailure(
                "RUN_CONTINUATION_PROBLEM_BINDING_REQUIRED",
                "A continuation grant must bind exactly one current Problem Revision to its RUN.",
                category="security",
            )
        workspace_identity = identity.get("workspace_identity") if isinstance(identity.get("workspace_identity"), dict) else {}
        workspace_id = str(workspace_identity.get("workspace_id") or "").strip()
        if not workspace_id:
            raise ToolFailure("RUN_CONTINUATION_WORKSPACE_REQUIRED", "The current workspace identity is unavailable; grant issuance fails closed.", category="security")
        loaded_identity = self._loaded_behavior_identity()
        admission = self.activation_admission_snapshot()
        admission_state = str(admission.get("admission") or "").lower()
        epoch_id = str(admission.get("activation_epoch_id") or "").strip()
        if admission_state != "open" or not epoch_id:
            raise ToolFailure(
                "RUN_CONTINUATION_ADMISSION_REQUIRED",
                "Continuation grants require a currently admitted runtime epoch; partial startup and stale connector state cannot be used as authority.",
                category="runtime",
                details={"activation": admission},
            )
        claimed_consent: dict[str, Any] | None = None
        try:
            goal_precondition = self._continuity_goal_controller_precondition(
                problem_id=str(binding.get("problem_id") or ""),
                problem_revision=int(binding.get("problem_revision") or 0),
            )
            policy = build_goal_continuation_policy(
                request,
                origin_run_id=ctx.run_id,
                workspace_id=workspace_id,
                problem_id=str(binding.get("problem_id") or ""),
                problem_revision=int(binding.get("problem_revision") or 0),
                contract_fingerprint=ctx.contract_fp,
                tool_contract_sha256=str(self.tool_contract.get("sha256") or ""),
                runtime_behavior_fingerprint=str(loaded_identity.get("fingerprint") or ""),
                activation_epoch_id=epoch_id,
                activation_admission=admission_state,
                issuer_client_id=self._hub_client_record_id(hub),
                controller_generation=int(goal_precondition.get("expected_generation") or 0),
                controller_endpoint_id=str(goal_precondition.get("controller_endpoint_id") or ""),
                controller_owner_client_id=str(goal_precondition.get("owner_client_id") or ""),
                wave_id=ctx.wave_id,
            )
            consent_descriptor = continuation_consent_descriptor(policy)
            current_environment_hash = self._run_continuation_environment_hash()
            mismatched_checks = [
                str(item.get("check_id") or "")
                for item in policy.get("approved_checks") or []
                if isinstance(item, dict) and str(item.get("environment_hash") or "") != current_environment_hash
            ]
            if mismatched_checks:
                raise ToolFailure(
                    "RUN_CONTINUATION_ENVIRONMENT_MISMATCH",
                    "Each immutable approved check must bind the currently admitted continuation execution environment.",
                    category="validation",
                    details={"check_ids": mismatched_checks, "current_environment_hash": current_environment_hash},
                )
            claimed_consent = claim_pending_continuation_consent(
                self.workspace.root,
                process_instance_id=self.process_instance_id,
                expected_descriptor=consent_descriptor,
            )
            if claimed_consent is None:
                approval = self._run_continuation_http_challenge(
                    policy=policy,
                    controller=controller,
                    descriptor=consent_descriptor,
                )
                raise ToolFailure(
                    "RUN_CONTINUATION_CONSENT_REQUIRED",
                    "No current exact host receipt authorizes this bounded background continuation. A visible user turn is provenance only, not consent.",
                    category="security",
                    details={
                        "continuation_consent_request": consent_descriptor,
                        "user_command": "/coding-tools-continue-consent " + _canonical_json(consent_descriptor),
                        **approval,
                    },
                )
            policy = bind_run_continuation_consent(policy, claimed_consent)
            issuer_receipt = hashlib.sha256(
                _canonical_json({
                    "run_id": ctx.run_id,
                    "episode_id": policy["episode_id"],
                    "controller_generation": policy["controller_generation"],
                    "controller_endpoint_id": policy["controller_endpoint_id"],
                    "controller_lease_id": controller.get("lease_id"),
                    "controller_fencing_token": controller.get("fencing_token"),
                    "controller_client_id": self._hub_client_record_id(hub),
                    "tool_contract_sha256": self.tool_contract.get("sha256"),
                    "consent_receipt_id": claimed_consent["receipt_id"],
                    "consent_scope_sha256": consent_descriptor["scope_sha256"],
                }).encode("utf-8")
            ).hexdigest()
            goal_issued = self.orchestration_ledger.issue_goal_continuation(
                policy=policy,
                issuer_receipt_sha256=issuer_receipt,
            )
            parent = goal_issued["goal_continuation"]
            materialized = self.orchestration_ledger.materialize_goal_continuation(
                run_id=ctx.run_id,
                episode_id=str(parent["episode_id"]),
                grant_wave_id=ctx.wave_id,
            )
            issued = {
                "status": goal_issued.get("status"),
                "idempotent": bool(goal_issued.get("idempotent")) and bool(materialized.get("idempotent")),
                "continuation": materialized["continuation"],
                "goal_continuation": parent,
            }
        except ControllerContinuityError as exc:
            if claimed_consent is not None:
                restore_pending_continuation_consent(self.workspace.root, claimed_consent)
            raise self._continuity_tool_failure(exc) from exc
        except RunContinuationError as exc:
            if claimed_consent is not None:
                restore_pending_continuation_consent(self.workspace.root, claimed_consent)
            raise self._run_continuation_tool_failure(exc) from exc
        except ToolFailure:
            if claimed_consent is not None:
                restore_pending_continuation_consent(self.workspace.root, claimed_consent)
            raise
        else:
            assert claimed_consent is not None
            consume_pending_continuation_consent(claimed_consent)
        self._project_orchestration(ctx, event="goal_continuation_granted")
        try:
            auto_start = self._run_continuation_start_driver({"run_id": ctx.run_id})
        except ToolFailure as exc:
            auto_start = {"run_id": ctx.run_id, "status": "GRANTED_NOT_STARTED", "code": exc.code, "message": exc.message}
        return {
            "workflow": workflow,
            "phase": "prepare",
            "continuation": issued,
            "auto_start": auto_start,
            "orchestration": self._orchestration_result(ctx),
            "task": self.task_state.get(),
            "recommended_next_action": "The bounded Goal authority is durable, the current RUN is materialized under its shared budget, and the existing continuation driver was started automatically when possible. MCP owns exact dispatch observation, mutation, proof, and the technical ACCEPTING transition.",
        }

    def _run_continuation_canonical_evidence(
        self,
        policy: dict[str, Any],
        *,
        objective: str,
        selected_read_paths: Iterable[str] = (),
        technical_replan: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], str]:
        """Create the content-bounded packet that a no-tools model may reason over."""
        revision = self.orchestration_ledger.problem_get_exact_revision(
            str(policy["problem_id"]),
            int(policy["problem_revision"]),
            expected_contract_fingerprint=str(policy["contract_fingerprint"]),
        )
        capsule = revision.get("capsule") if isinstance(revision.get("capsule"), dict) else None
        if capsule is None:
            raise ToolFailure("RUN_CONTINUATION_PROBLEM_CONTEXT_INVALID", "The exact bound Problem Revision has no valid contract capsule.", category="runtime")
        if _contains_sensitive_model_content(objective) or _contains_sensitive_model_content(capsule):
            raise ToolFailure(
                "RUN_CONTINUATION_EVIDENCE_SENSITIVE",
                "Problem material contains sensitive-like content and cannot be sent to a continuation proposal model.",
                category="security",
            )
        root = self.workspace.root.resolve(strict=False)
        allowed_read_paths = [_normalize_path(path, "read scope") for path in policy.get("read_paths") or []]
        requested_read_paths = _normalize_paths(list(selected_read_paths), "selected_read_paths")
        denied_read_paths = sorted(set(requested_read_paths).difference(allowed_read_paths))
        if denied_read_paths:
            raise ToolFailure(
                "RUN_CONTINUATION_READ_SCOPE_DENIED",
                "The requested continuation evidence is outside the immutable read scope.",
                category="security",
                details={"paths": denied_read_paths},
            )
        files: list[dict[str, str]] = []
        for path in requested_read_paths:
            normalized = _normalize_path(path, "read scope")
            target = (root / normalized).resolve(strict=False)
            if not target.is_relative_to(root) or not target.is_file():
                raise ToolFailure("RUN_CONTINUATION_EVIDENCE_UNAVAILABLE", "A granted read path is not a current workspace file.", category="runtime", details={"path": normalized})
            try:
                text = target.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                raise ToolFailure("RUN_CONTINUATION_EVIDENCE_UNAVAILABLE", "A granted read path could not be read as UTF-8.", category="runtime", details={"path": normalized}) from exc
            if len(text.encode("utf-8")) > 48_000:
                raise ToolFailure("RUN_CONTINUATION_EVIDENCE_TOO_LARGE", "A granted read path exceeds the bounded continuation packet limit.", category="validation", details={"path": normalized})
            if _contains_sensitive_model_content(text):
                raise ToolFailure(
                    "RUN_CONTINUATION_EVIDENCE_SENSITIVE",
                    "A granted read path contains sensitive-like content and cannot be sent to a continuation proposal model.",
                    category="security",
                    details={"path": normalized},
                )
            files.append({"path": normalized, "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(), "content": text})
        identity = self._orchestration_workspace_identity(".")
        evidence = {
            "schema_version": 1,
            "objective": _bounded(objective, 2_000),
            "problem_contract": capsule,
            "read_files": files,
            "available_read_paths": allowed_read_paths,
            "write_paths": list(policy.get("write_paths") or []),
            "protected_paths": list(policy.get("protected_paths") or []),
            "approved_check_hashes": [str(item.get("definition_hash") or "") for item in policy.get("approved_checks") or [] if isinstance(item, dict)],
            "source_identity": {"base_head": identity.get("base_head"), "worktree_fp": identity.get("worktree_fp")},
        }
        normalized_replan = _normalize_technical_replan(technical_replan)
        if normalized_replan:
            if _contains_sensitive_model_content(normalized_replan):
                raise ToolFailure(
                    "RUN_CONTINUATION_EVIDENCE_SENSITIVE",
                    "Technical replan material contains sensitive-like content and cannot be sent to a continuation proposal model.",
                    category="security",
                )
            evidence["technical_replan"] = normalized_replan
        digest = hashlib.sha256(_canonical_json(evidence).encode("utf-8")).hexdigest()
        return evidence, digest

    def _run_continuation_prompt(self, *, policy: dict[str, Any], evidence: dict[str, Any], evidence_hash: str) -> str:
        packet = {
            "continuation_contract": {
                "route": policy.get("route"),
                "profile": policy.get("profile"),
                "acceptance_mode": policy.get("acceptance_mode"),
                "instruction": "Choose exactly one proposal kind: READ, PATCH, READY, or BLOCKED. Never ask for expanded scope, a new check, a new budget, or authority. Copy evidence_hash exactly.",
                # The observed App Server profile fails a turn when supplied
                # an outputSchema. The response remains typed at the MCP
                # boundary: this inline contract plus
                # parse_run_continuation_proposal() rejects every malformed,
                # stale, out-of-scope, or incomplete proposal before any
                # effect is possible.
                "response_encoding": {
                    "format": "the entire response must be one JSON object: begin with {, end with }, and contain no Markdown, code fence, label, or surrounding prose; invalid JSON is rejected without an effect",
                    "canonical_json_schema": RUN_CONTINUATION_PROPOSAL_SCHEMA,
                    "policy_rules": [
                        "The JSON Schema is part of this prompt, not a provider outputSchema; it defines every nested object and forbids extra fields.",
                        "READ paths must be distinct values from evidence.available_read_paths.",
                        "PATCH replacement and new-file paths must be in evidence.write_paths and outside evidence.protected_paths; every replacement old value must be the exact current preimage.",
                        "PATCH must include at least one replacement or new file and selected_check_hashes must contain every distinct value in evidence.approved_check_hashes exactly once.",
                    ],
                },
            },
            "evidence_hash": evidence_hash,
            "evidence": evidence,
        }
        return "Bounded durable continuation packet:\n" + _canonical_json(packet)

    def _run_continuation_start_driver(self, args: dict[str, Any]) -> dict[str, Any]:
        run_id = str(args.get("run_id") or "").strip()
        if not run_id:
            projection = self.task_state.get().get("orchestration")
            run_id = str((projection or {}).get("run_id") or "") if isinstance(projection, dict) else ""
        if not run_id:
            raise ToolFailure("ORCHESTRATION_RUN_NOT_FOUND", "run_id is required to start a continuation driver.", category="not_found")
        record = self.orchestration_ledger._run_continuation_get_raw(run_id)
        if record is None:
            raise ToolFailure("RUN_CONTINUATION_GRANT_REQUIRED", "A continuation driver requires a prior immutable grant.", category="security")
        policy = record["policy"]
        if record.get("pending_action_id") or record.get("pending_job_id") or record.get("pending_patch_action_id"):
            self._run_continuation_fail_closed_pause(run_id, "restart_pending_dispatch_or_effect_requires_reconciliation")
            raise ToolFailure(
                "RUN_CONTINUATION_RECOVERY_RECONCILE_REQUIRED",
                "A prior continuation dispatch, proof Job, or effect is still pending. Do not resume the App Server lane or start another turn; reconcile the exact pending outcome first.",
                category="runtime",
            )
        try:
            # Dispatch is an externally observable continuation boundary.  Do
            # not claim a driver or start a model turn under an old admitted
            # runtime, behavior fingerprint, base/worktree, or RUN context.
            self._run_continuation_assert_runtime(policy)
            ctx, _identity = self._run_continuation_context(record)
            admission_before_claim = self.activation_admission_snapshot()
            epoch_changed = (
                str(admission_before_claim.get("activation_epoch_id") or "")
                != str(policy.get("activation_epoch_id") or "")
            )
            wave_changed = str(ctx.wave_id) != str(policy.get("grant_wave_id") or "")
            if record.get("thread_id") and (epoch_changed or wave_changed):
                try:
                    self._run_continuation_validate_execution_rebind(record, ctx)
                except ToolFailure as exc:
                    code = "RUN_CONTINUATION_EPOCH_STALE" if epoch_changed else "RUN_CONTINUATION_WAVE_STALE"
                    raise RunContinuationError(code, str(exc)) from exc
            claim = self.orchestration_ledger.claim_run_continuation(
                run_id=run_id,
                runtime_instance_id=self._run_continuation_runtime_instance_id(),
                expected_generation=int(record["driver_generation"]),
            )
            if not claim.get("claimed"):
                raise RunContinuationError("RUN_CONTINUATION_DRIVER_BUSY", "Another admitted runtime currently owns this continuation driver.", retryable=True, details={"reason": claim.get("reason")})
            continuation = claim["continuation"]
            generation = int(continuation["driver_generation"])
            raw_policy = self.orchestration_ledger._run_continuation_get_raw(run_id)
            if raw_policy is None:
                raise RunContinuationError("RUN_CONTINUATION_GRANT_REQUIRED", "Continuation grant disappeared during driver claim.")
            policy = raw_policy["policy"]
            parent_episode_id = str(raw_policy.get("parent_episode_id") or "")
            if parent_episode_id:
                parent = self.orchestration_ledger._goal_continuation_get_raw(parent_episode_id)
                parent = self.orchestration_ledger._assert_goal_continuation_row(
                    parent,
                    episode_id=parent_episode_id,
                )
                authority_policy = parent["policy"]
                consent = authority_policy.get("consent") if isinstance(authority_policy.get("consent"), dict) else {}
                descriptor = continuation_consent_descriptor(authority_policy)
                if (
                    not str(consent.get("receipt_id") or "")
                    or str(consent.get("scope_sha256") or "") != descriptor["scope_sha256"]
                ):
                    raise RunContinuationError(
                        "RUN_CONTINUATION_CONSENT_REQUIRED",
                        "Materialized Goal continuation requires the original exact Goal consent receipt.",
                    )
            restored_lane = False
            if raw_policy.get("thread_id") and not parent_episode_id:
                consent = policy.get("consent") if isinstance(policy.get("consent"), dict) else {}
                descriptor = continuation_consent_descriptor(policy)
                if (
                    not str(consent.get("receipt_id") or "")
                    or str(consent.get("scope_sha256") or "") != descriptor["scope_sha256"]
                ):
                    raise RunContinuationError(
                        "RUN_CONTINUATION_CONSENT_REQUIRED",
                        "Persistent-lane recovery requires the original exact one-shot consent receipt.",
                    )
                session_id = str(raw_policy.get("thread_session_id") or "")
                if not session_id:
                    raise RunContinuationError(
                        "RUN_CONTINUATION_SESSION_REQUIRED",
                        "Persistent-lane recovery requires the durable App Server session identity.",
                    )
                restored = self._codex_bridge.restore_persistent_thread(
                    thread_id=str(raw_policy["thread_id"]),
                    expected_session_id=session_id,
                    profile=RUN_CONTINUATION_PROFILE,
                    model="gpt-5.6-sol",
                    effort="xhigh",
                )
                if str(restored.get("thread_id") or "") != str(raw_policy["thread_id"]) or str(restored.get("session_id") or "") != session_id:
                    raise RunContinuationError(
                        "RUN_CONTINUATION_SESSION_MISMATCH",
                        "The App Server did not restore the exact durable continuation lane/session.",
                    )
                restored_lane = True
            objective = str((self.orchestration_ledger.get_run(run_id) or {}).get("objective") or "").strip()
            # Start with the immutable Problem capsule and a declared bounded
            # read catalogue. The model must explicitly request source bytes;
            # this keeps READ meaningful instead of handing it every granted
            # file and then accepting a no-op request loop.
            evidence, evidence_hash = self._run_continuation_canonical_evidence(
                policy, objective=objective, selected_read_paths=()
            )
            request_hash = hashlib.sha256(_canonical_json({"evidence_hash": evidence_hash, "profile": RUN_CONTINUATION_PROFILE}).encode("utf-8")).hexdigest()
            reservation = self.orchestration_ledger.reserve_run_continuation_action(
                run_id=run_id,
                driver_generation=generation,
                runtime_instance_id=self._run_continuation_runtime_instance_id(),
                action_kind="proposal",
                request_hash=request_hash,
                evidence_hash=evidence_hash,
                evidence_paths=(),
                expected_action_seq=int(continuation["next_action_seq"]),
            )
            if not reservation.get("reserved"):
                raise RunContinuationError("RUN_CONTINUATION_ACTION_PENDING", "The continuation proposal action is already reserved; reconcile it before dispatch.")
            action_id = str(reservation["action_id"])
            prompt = self._run_continuation_prompt(policy=policy, evidence=evidence, evidence_hash=evidence_hash)
            bridge = (
                self._codex_bridge.continue_thread(
                    thread_id=str(raw_policy["thread_id"]),
                    prompt=prompt,
                    output_schema=None,
                )
                if restored_lane
                else self._codex_bridge.run(
                    prompt,
                    profile=RUN_CONTINUATION_PROFILE,
                    lifetime="persistent",
                    # The model has no tool or write capability and its response
                    # is parsed fail-closed before MCP can consider an effect.
                    output_schema=None,
                )
            )
            thread_id, turn_id = str(bridge.get("thread_id") or ""), str(bridge.get("turn_id") or "")
            session_id = str(bridge.get("session_id") or raw_policy.get("thread_session_id") or "")
            if not thread_id or not turn_id or not session_id:
                raise RunContinuationError("RUN_CONTINUATION_DISPATCH_FAILED", "The bridge did not return a durable thread and turn identity.")
            lane_id = hashlib.sha256(f"run-continuation-lane-v1\0{run_id}\0{policy['policy_sha256'] if 'policy_sha256' in policy else evidence_hash}".encode("utf-8")).hexdigest()
            self.orchestration_ledger.set_run_continuation_dispatch(
                run_id=run_id,
                driver_generation=generation,
                runtime_instance_id=self._run_continuation_runtime_instance_id(),
                action_id=action_id,
                lane_id=lane_id,
                thread_id=thread_id,
                turn_id=turn_id,
                session_id=session_id,
            )
            self._run_continuation_start_worker(run_id=run_id, driver_generation=generation)
        except RunContinuationError as exc:
            raise self._run_continuation_tool_failure(exc) from exc
        except Exception as exc:
            code = str(getattr(exc, "code", "RUN_CONTINUATION_DISPATCH_FAILED"))
            raise ToolFailure(code, str(exc), category="runtime", retryable=bool(getattr(exc, "retryable", False))) from exc
        return {
            "run_id": run_id,
            "action_id": action_id,
            "driver_generation": generation,
            "status": "PROPOSING",
            "thread_id": thread_id,
            "turn_id": turn_id,
            "evidence_hash": evidence_hash,
            "recommended_next_action": "The admitted MCP driver is observing this exact bridge turn without copying the ChatWeb controller. Inspect task_control run_continuation=get/observe for a durable status; it will never launch a second turn when dispatch outcome is unknown.",
        }

    def _run_continuation_control(self, args: dict[str, Any]) -> dict[str, Any]:
        action = str(args.get("run_continuation_action") or "get").strip().lower()
        run_id = str(args.get("run_id") or "").strip()
        if not run_id:
            state = self.task_state.get()
            projection = state.get("orchestration") if isinstance(state.get("orchestration"), dict) else {}
            run_id = str(projection.get("run_id") or "").strip()
        if not run_id:
            raise ToolFailure("ORCHESTRATION_RUN_NOT_FOUND", "run_id is required when controlling a continuation grant.", category="not_found")
        if action == "get":
            continuation = self.orchestration_ledger.get_run_continuation(run_id)
            return {
                "run_id": run_id,
                "continuation": continuation,
                "status": "MISSING" if continuation is None else "OK",
                "continuation_environment_hash": self._run_continuation_environment_hash(),
                "environment_hash_schema_version": 1,
            }
        if action == "start":
            controller = self._require_hub_controller(run_id)
            if controller is None:
                raise ToolFailure("RUN_CONTINUATION_CONTROLLER_REQUIRED", "Starting a continuation driver requires the active authenticated ChatWeb controller.", category="security")
            self._run_continuation_record_telemetry(
                run_id, "manual_nudge", outcome="observed", code="EXPLICIT_START", marker=str(controller.get("fencing_token") or "")
            )
            return self._run_continuation_start_driver({**args, "run_id": run_id})
        if action == "observe":
            # Observing an already-issued grant never turns a missing controller
            # into write/acceptance authority. It only lets a caller obtain the
            # exact driver result; the driver itself remains MCP-owned.
            return self._run_continuation_observe_driver(run_id=run_id)
        if action == "reconcile":
            controller = self._require_hub_controller(run_id)
            if controller is None:
                raise ToolFailure("RUN_CONTINUATION_CONTROLLER_REQUIRED", "Effect reconciliation requires the active authenticated ChatWeb controller.", category="security")
            return self._run_continuation_reconcile_driver(
                run_id=run_id,
                controller_fencing_token=controller.get("fencing_token"),
            )
        if action not in {"pause", "resume", "revoke"}:
            raise ToolFailure("RUN_CONTINUATION_CONTROL_INVALID", "Unsupported run_continuation_action.", category="validation")
        controller = self._require_hub_controller(run_id)
        if controller is None:
            raise ToolFailure("RUN_CONTINUATION_CONTROLLER_REQUIRED", "Continuation control requires the active authenticated ChatWeb controller.", category="security")
        try:
            continuation = self.orchestration_ledger.set_run_continuation_state(
                run_id=run_id,
                action=action,
                reason=str(args.get("continuation_reason") or ""),
            )
        except RunContinuationError as exc:
            raise self._run_continuation_tool_failure(exc) from exc
        return {"run_id": run_id, "continuation": continuation, "status": action.upper(), "controller_fencing_token": controller.get("fencing_token")}
