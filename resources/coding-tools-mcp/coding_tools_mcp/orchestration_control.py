from __future__ import annotations

import copy
import hashlib
import json
import threading
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .orchestration_ledger import OrchestrationLedger


WRITE_LEASE_TTL_SECONDS = 60.0
WRITE_FENCE_SCOPE = "workspace"


STATES = frozenset({
    "PREFLIGHT",
    "READY",
    "ROUTED",
    "EXECUTING",
    "PROVING",
    "ACCEPTING",
    "CHECKPOINTED",
    "REPLAN",
    "BLOCKED",
    "ABORTED",
})

_ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "PREFLIGHT": frozenset({"READY", "REPLAN", "BLOCKED", "ABORTED"}),
    "READY": frozenset({"ROUTED", "REPLAN", "BLOCKED", "ABORTED"}),
    "ROUTED": frozenset({"EXECUTING", "REPLAN", "BLOCKED", "ABORTED"}),
    "EXECUTING": frozenset({"PROVING", "REPLAN", "BLOCKED", "ABORTED"}),
    "PROVING": frozenset({"ACCEPTING", "REPLAN", "BLOCKED", "ABORTED"}),
    "ACCEPTING": frozenset({"CHECKPOINTED", "REPLAN", "BLOCKED", "ABORTED"}),
    "REPLAN": frozenset({"READY", "ROUTED", "BLOCKED", "ABORTED"}),
    "CHECKPOINTED": frozenset(),
    "BLOCKED": frozenset(),
    "ABORTED": frozenset(),
}

_FAILURE_ALIASES = {
    "CODEX_CAPACITY": "CAPACITY",
    "CODEX_RATE_LIMIT": "CAPACITY",
    "CODEX_SERVER_OVERLOADED": "CAPACITY",
    "HIGH_COST_ACK_REQUIRED": "POLICY_BLOCK",
    "CANDIDATE_SCOPE_VIOLATION": "PATCH_AMBIGUOUS",
    "CANDIDATE_REPLACEMENT_NOT_UNIQUE": "PATCH_AMBIGUOUS",
    "CANDIDATE_REPLACEMENT_NOT_FOUND": "PATCH_CONTEXT_NOT_FOUND",
}


class OrchestrationControlError(RuntimeError):
    def __init__(self, code: str, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.details = details or {}


@dataclass
class WriteLease:
    lease_id: str
    owner: str
    mode: str
    base_head: str
    worktree_fp: str
    fencing_token: int
    expires_at: float
    scope_key: str = WRITE_FENCE_SCOPE
    allowed_paths: tuple[str, ...] = ()
    delegation_id: str | None = None


@dataclass
class RunContext:
    run_id: str
    wave_id: str
    state: str
    execution_mode: str
    base_head: str
    worktree_fp: str
    contract_fp: str = ""
    route_requested: str = ""
    route_resolved: str = ""
    delegation_id: str | None = None
    write_lease: WriteLease | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def projection(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "wave_id": self.wave_id,
            "orchestration_state": self.state,
            "execution_mode": self.execution_mode,
            "route_requested": self.route_requested,
            "route_resolved": self.route_resolved,
            "write_owner": self.write_lease.owner if self.write_lease else "",
            "write_lease_id": self.write_lease.lease_id if self.write_lease else "",
            "delegation_id": self.delegation_id or "",
            "base_head": self.base_head,
            "worktree_fp": self.worktree_fp,
            "contract_fp": self.contract_fp,
        }


def normalize_failure_class(value: object) -> str:
    raw = str(value or "UNKNOWN").strip().upper().replace("-", "_").replace(" ", "_")
    if raw in _FAILURE_ALIASES:
        return _FAILURE_ALIASES[raw]
    if "PROMPT" in raw and ("LARGE" in raw or "SIZE" in raw):
        return "PROMPT_TOO_LARGE"
    if "DEADLINE" in raw or "TIMEOUT" in raw:
        return "DEADLINE" if "PROOF" not in raw else "PROOF_TIMEOUT"
    if "CAPACITY" in raw or "OVERLOAD" in raw or "RATE_LIMIT" in raw:
        return "CAPACITY"
    if "PATCH" in raw and "AMBIG" in raw:
        return "PATCH_AMBIGUOUS"
    if "NOT_FOUND" in raw and "PATCH" in raw:
        return "PATCH_CONTEXT_NOT_FOUND"
    if "BASE" in raw and "DRIFT" in raw:
        return "BASE_DRIFT"
    if "CONTRACT" in raw and "DRIFT" in raw:
        return "CONTRACT_DRIFT"
    return raw[:100]


class OrchestrationControl:
    """State/authority guard over the append-only orchestration ledger."""

    def __init__(
        self,
        workspace: Path,
        ledger: OrchestrationLedger,
        *,
        on_wave_terminal: Callable[[RunContext, str], Any] | None = None,
        assert_wave_quiescent: Callable[[str, str], None] | None = None,
    ) -> None:
        self.workspace = workspace.resolve(strict=False)
        self.ledger = ledger
        self._on_wave_terminal = on_wave_terminal
        self._assert_wave_quiescent = assert_wave_quiescent
        self._lock = threading.RLock()
        self._contexts: dict[str, RunContext] = {}

    def begin(
        self,
        *,
        objective: str,
        task_id: str,
        execution_mode: str,
        base_head: str,
        worktree_fp: str,
        contract_fp: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> RunContext:
        run_id = self.ledger.create_run(objective=objective, task_id=task_id, metadata=metadata)
        wave_id = self.ledger.create_wave(
            run_id,
            execution_mode=execution_mode,
            base_head=base_head,
            worktree_fp=worktree_fp,
            contract_fp=contract_fp,
            metadata=metadata,
        )
        ctx = RunContext(
            run_id=run_id,
            wave_id=wave_id,
            state="PREFLIGHT",
            execution_mode=execution_mode,
            base_head=base_head,
            worktree_fp=worktree_fp,
            contract_fp=contract_fp,
            metadata=copy.deepcopy(metadata or {}),
        )
        with self._lock:
            self._contexts[run_id] = ctx
        self.ledger.append_event(
            run_id,
            wave_id=wave_id,
            event_type="run_started",
            state_after="PREFLIGHT",
            payload={"execution_mode": execution_mode, "base_head": base_head, "worktree_fp": worktree_fp, "contract_fp": contract_fp},
        )
        return ctx

    def transition(
        self,
        ctx: RunContext,
        to_state: str,
        *,
        reason: str = "",
        payload: dict[str, Any] | None = None,
    ) -> RunContext:
        to_state = str(to_state).upper()
        if to_state not in STATES:
            raise OrchestrationControlError("INVALID_ORCHESTRATION_STATE", f"Unknown orchestration state: {to_state}")
        with self._lock:
            current = ctx.state
            if to_state == current:
                self._contexts[ctx.run_id] = ctx
                return ctx
            if to_state not in _ALLOWED_TRANSITIONS.get(current, frozenset()):
                raise OrchestrationControlError(
                    "INVALID_ORCHESTRATION_TRANSITION",
                    f"Orchestration transition {current} -> {to_state} is not allowed.",
                    details={"run_id": ctx.run_id, "wave_id": ctx.wave_id, "from": current, "to": to_state},
                )
            if to_state in {"REPLAN", "BLOCKED", "ABORTED"} and ctx.write_lease is not None:
                self._revoke_write_lease_locked(ctx, reason=f"state_transition:{to_state.lower()}")
            ctx.state = to_state
            self.ledger.append_event(
                ctx.run_id,
                wave_id=ctx.wave_id,
                delegation_id=ctx.delegation_id,
                event_type="state_transition",
                state_before=current,
                state_after=to_state,
                payload={"reason": reason, **(payload or {})},
            )
            if to_state == "BLOCKED":
                self.ledger.finish_wave(ctx.wave_id, status="blocked", metadata={"reason": reason})
                self.ledger.finish_run(ctx.run_id, status="blocked", metadata={"reason": reason})
            elif to_state == "ABORTED":
                self.ledger.finish_wave(ctx.wave_id, status="aborted", metadata={"reason": reason})
                self.ledger.finish_run(ctx.run_id, status="aborted", metadata={"reason": reason})
            elif to_state == "CHECKPOINTED":
                self.ledger.finish_wave(ctx.wave_id, status="accepted")
                self.ledger.finish_run(ctx.run_id, status="accepted")
            if to_state in {"REPLAN", "BLOCKED", "ABORTED", "CHECKPOINTED"}:
                callback = self._on_wave_terminal
                if callback is not None:
                    callback(ctx, to_state)
            self._contexts[ctx.run_id] = ctx
            return ctx

    def mark_ready(self, ctx: RunContext, *, readiness: dict[str, Any] | None = None) -> RunContext:
        self.ledger.append_event(
            ctx.run_id,
            wave_id=ctx.wave_id,
            event_type="readiness_checked",
            state_before=ctx.state,
            state_after=ctx.state,
            payload=readiness or {"ready": True},
        )
        return self.transition(ctx, "READY", reason="preflight_ready")

    def select_route(self, ctx: RunContext, route: dict[str, Any]) -> RunContext:
        if ctx.state == "REPLAN":
            self.assert_quiescent(ctx)
            self.transition(ctx, "READY", reason="replan_route_ready")
        if ctx.state != "READY":
            raise OrchestrationControlError("ROUTE_OUTSIDE_READY", "Route selection requires READY state.")
        ctx.route_requested = str(route.get("requested") or "")
        ctx.route_resolved = str(route.get("selected") or "")
        self.ledger.append_event(
            ctx.run_id,
            wave_id=ctx.wave_id,
            event_type="route_selected",
            state_before="READY",
            state_after="READY",
            payload={
                "requested": ctx.route_requested,
                "resolved": ctx.route_resolved,
                "reason": route.get("reason"),
                "profile": route.get("profile"),
                "model": route.get("model"),
                "effort": route.get("effort"),
                "high_cost": bool(route.get("high_cost", False)),
            },
        )
        return self.transition(ctx, "ROUTED", reason="route_selected")

    def resolve_execution_mode(self, ctx: RunContext, execution_mode: str) -> RunContext:
        execution_mode = str(execution_mode or "auto").strip().lower() or "auto"
        if ctx.execution_mode == execution_mode:
            return ctx
        previous = ctx.execution_mode
        ctx.execution_mode = execution_mode
        self.ledger.set_wave_execution_mode(ctx.wave_id, execution_mode)
        self.ledger.append_event(
            ctx.run_id,
            wave_id=ctx.wave_id,
            event_type="execution_mode_resolved",
            state_before=ctx.state,
            state_after=ctx.state,
            payload={"requested": previous, "resolved": execution_mode},
        )
        return ctx

    def start_delegation(
        self,
        ctx: RunContext,
        *,
        authority_owner: str,
        route: dict[str, Any],
        allowed_scope: list[str] | None = None,
        parent_delegation_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        delegation_id = self.ledger.create_delegation(
            ctx.wave_id,
            parent_delegation_id=parent_delegation_id,
            authority_owner=authority_owner,
            route_requested=str(route.get("requested") or ctx.route_requested),
            route_resolved=str(route.get("selected") or ctx.route_resolved),
            model=str(route.get("model") or ""),
            effort=str(route.get("effort") or ""),
            allowed_scope=allowed_scope or [],
            metadata=metadata,
        )
        ctx.delegation_id = delegation_id
        self.ledger.append_event(
            ctx.run_id,
            wave_id=ctx.wave_id,
            delegation_id=delegation_id,
            event_type="delegation_started",
            state_before=ctx.state,
            state_after=ctx.state,
            payload={"authority_owner": authority_owner, "allowed_scope": allowed_scope or []},
        )
        return delegation_id

    def finish_delegation(self, ctx: RunContext, *, status: str, metadata: dict[str, Any] | None = None) -> None:
        if not ctx.delegation_id:
            return
        self.ledger.finish_delegation(ctx.delegation_id, status=status, metadata=metadata)
        self.ledger.append_event(
            ctx.run_id,
            wave_id=ctx.wave_id,
            delegation_id=ctx.delegation_id,
            event_type="delegation_finished",
            state_before=ctx.state,
            state_after=ctx.state,
            payload={"status": status, **(metadata or {})},
        )

    def acquire_write_lease(
        self,
        ctx: RunContext,
        *,
        owner: str,
        mode: str,
        allowed_paths: list[str] | None = None,
        delegation_id: str | None = None,
        ttl_seconds: float = WRITE_LEASE_TTL_SECONDS,
    ) -> WriteLease:
        with self._lock:
            if ctx.state != "ROUTED":
                raise OrchestrationControlError("WRITE_LEASE_OUTSIDE_ROUTED", "Write lease can only be acquired in ROUTED state.")
            if ctx.write_lease is not None:
                raise OrchestrationControlError("WRITE_LEASE_CONFLICT", "A write lease is already active for this wave.")
            lease_id = uuid.uuid4().hex
            fence = self.ledger.acquire_write_fence(
                scope_key=WRITE_FENCE_SCOPE,
                lease_id=lease_id,
                owner=str(owner),
                run_id=ctx.run_id,
                wave_id=ctx.wave_id,
                ttl_seconds=ttl_seconds,
            )
            if not fence.get("acquired"):
                raise OrchestrationControlError(
                    "WRITE_LEASE_CONFLICT",
                    "Another unexpired writer already holds the workspace fence.",
                    details={"current": fence.get("current")},
                )
            lease = WriteLease(
                lease_id=lease_id,
                owner=str(owner),
                mode=str(mode),
                base_head=ctx.base_head,
                worktree_fp=ctx.worktree_fp,
                fencing_token=int(fence["fencing_token"]),
                expires_at=float(fence["expires_at"]),
                allowed_paths=tuple(sorted({str(item).replace("\\", "/") for item in (allowed_paths or []) if str(item).strip()})),
                delegation_id=delegation_id or ctx.delegation_id,
            )
            ctx.write_lease = lease
            self.ledger.append_event(
                ctx.run_id,
                wave_id=ctx.wave_id,
                delegation_id=lease.delegation_id,
                event_type="write_lease_acquired",
                state_before="ROUTED",
                state_after="ROUTED",
                payload={
                    "lease_id": lease.lease_id,
                    "owner": lease.owner,
                    "mode": lease.mode,
                    "fencing_token": lease.fencing_token,
                    "expires_at": lease.expires_at,
                    "scope_key": lease.scope_key,
                    "base_head": lease.base_head,
                    "worktree_fp": lease.worktree_fp,
                    "allowed_paths": list(lease.allowed_paths),
                },
            )
            self.transition(ctx, "EXECUTING", reason="write_authority_acquired")
            return lease

    def assert_write_allowed(
        self,
        ctx: RunContext,
        *,
        owner: str,
        paths: list[str] | None = None,
        base_head: str | None = None,
        worktree_fp: str | None = None,
    ) -> None:
        lease = ctx.write_lease
        if ctx.state != "EXECUTING" or lease is None:
            raise OrchestrationControlError(
                "WRITE_WITHOUT_ACTIVE_LEASE",
                "Mutation requires EXECUTING state and an active write lease.",
                details={"state": ctx.state, "owner": owner},
            )
        if lease.owner != owner:
            raise OrchestrationControlError(
                "WRITE_OWNER_MISMATCH",
                f"Write owner {owner!r} does not match active lease owner {lease.owner!r}.",
            )
        if base_head is not None and lease.base_head and base_head != lease.base_head:
            raise OrchestrationControlError("BASE_DRIFT", "Base HEAD changed after the write lease was acquired.")
        if worktree_fp is not None and lease.worktree_fp and worktree_fp != lease.worktree_fp:
            raise OrchestrationControlError("BASE_DRIFT", "Worktree fingerprint changed before the authorized mutation.")
        fence = self.ledger.assert_write_fence(
            scope_key=lease.scope_key,
            lease_id=lease.lease_id,
            fencing_token=lease.fencing_token,
            owner=lease.owner,
        )
        if not fence.get("valid"):
            reason = str(fence.get("reason") or "stale")
            code = "WRITE_LEASE_EXPIRED" if reason == "expired" else "STALE_WRITE_FENCE"
            raise OrchestrationControlError(
                code,
                "The workspace write fence is no longer valid; the attempt must not mutate state.",
                details={"reason": reason, "lease_id": lease.lease_id, "fencing_token": lease.fencing_token, "current": fence.get("current")},
            )
        if lease.allowed_paths:
            allowed = set(lease.allowed_paths)
            for raw in paths or []:
                path = str(raw).replace("\\", "/")
                if path not in allowed:
                    raise OrchestrationControlError(
                        "WRITE_SCOPE_VIOLATION",
                        f"Path {path!r} is outside the active write lease.",
                        details={"allowed_paths": sorted(allowed)},
                    )

    def renew_write_lease(
        self,
        ctx: RunContext,
        *,
        owner: str,
        ttl_seconds: float = WRITE_LEASE_TTL_SECONDS,
    ) -> WriteLease:
        lease = ctx.write_lease
        if lease is None or lease.owner != owner:
            raise OrchestrationControlError("WRITE_OWNER_MISMATCH", "Only the active write owner may renew the lease.")
        renewed = self.ledger.renew_write_fence(
            scope_key=lease.scope_key,
            lease_id=lease.lease_id,
            fencing_token=lease.fencing_token,
            owner=lease.owner,
            ttl_seconds=ttl_seconds,
        )
        if not renewed.get("renewed"):
            raise OrchestrationControlError(
                "STALE_WRITE_FENCE",
                "The workspace write fence could not be renewed because it is stale or expired.",
                details=renewed,
            )
        lease.expires_at = float(renewed["expires_at"])
        self.ledger.append_event(
            ctx.run_id,
            wave_id=ctx.wave_id,
            delegation_id=lease.delegation_id,
            event_type="write_lease_renewed",
            state_before=ctx.state,
            state_after=ctx.state,
            payload={"lease_id": lease.lease_id, "fencing_token": lease.fencing_token, "expires_at": lease.expires_at},
        )
        return lease

    def revoke_write_lease(self, ctx: RunContext, *, reason: str) -> None:
        with self._lock:
            self._revoke_write_lease_locked(ctx, reason=reason)

    def _revoke_write_lease_locked(self, ctx: RunContext, *, reason: str) -> None:
        lease = ctx.write_lease
        if lease is None:
            return
        self.ledger.release_write_fence(
            scope_key=lease.scope_key,
            lease_id=lease.lease_id,
            fencing_token=lease.fencing_token,
            owner=lease.owner,
        )
        self.ledger.append_event(
            ctx.run_id,
            wave_id=ctx.wave_id,
            delegation_id=lease.delegation_id,
            event_type="write_lease_revoked",
            state_before=ctx.state,
            state_after=ctx.state,
            payload={"lease_id": lease.lease_id, "owner": lease.owner, "reason": reason},
        )
        ctx.write_lease = None

    def begin_proof(self, ctx: RunContext) -> RunContext:
        if ctx.state != "EXECUTING":
            raise OrchestrationControlError("PROOF_OUTSIDE_EXECUTION", "Proof can only begin after execution.")
        self.revoke_write_lease(ctx, reason="execution_complete")
        return self.transition(ctx, "PROVING", reason="execution_complete")

    def record_failure(
        self,
        ctx: RunContext,
        failure: object,
        *,
        payload: dict[str, Any] | None = None,
        block: bool = False,
    ) -> str:
        failure_class = normalize_failure_class(failure)
        self.ledger.append_event(
            ctx.run_id,
            wave_id=ctx.wave_id,
            delegation_id=ctx.delegation_id,
            event_type="failure_observed",
            state_before=ctx.state,
            state_after=ctx.state,
            payload={"failure_class": failure_class, **(payload or {})},
        )
        target = "BLOCKED" if block else "REPLAN"
        self.transition(ctx, target, reason=failure_class, payload={"failure_class": failure_class})
        return failure_class

    def begin_replan_wave(
        self,
        ctx: RunContext,
        *,
        execution_mode: str,
        base_head: str,
        worktree_fp: str,
        contract_fp: str,
        reason: str,
    ) -> RunContext:
        if ctx.state != "REPLAN":
            raise OrchestrationControlError("REPLAN_REQUIRED", "A replacement wave requires REPLAN state.")
        self.assert_quiescent(ctx)
        self.ledger.finish_wave(ctx.wave_id, status="replanned", metadata={"reason": reason})
        wave_id = self.ledger.create_wave(
            ctx.run_id,
            execution_mode=execution_mode,
            base_head=base_head,
            worktree_fp=worktree_fp,
            contract_fp=contract_fp,
            metadata={"replan_reason": reason},
        )
        ctx.wave_id = wave_id
        ctx.state = "PREFLIGHT"
        ctx.execution_mode = execution_mode
        ctx.base_head = base_head
        ctx.worktree_fp = worktree_fp
        ctx.contract_fp = contract_fp
        ctx.route_requested = ""
        ctx.route_resolved = ""
        ctx.delegation_id = None
        ctx.write_lease = None
        self.ledger.append_event(
            ctx.run_id,
            wave_id=wave_id,
            event_type="wave_replanned",
            state_after="PREFLIGHT",
            payload={"reason": reason, "execution_mode": execution_mode},
        )
        with self._lock:
            self._contexts[ctx.run_id] = ctx
        return ctx

    def assert_quiescent(self, ctx: RunContext) -> None:
        gate = self._assert_wave_quiescent
        if gate is None:
            return
        try:
            gate(ctx.run_id, ctx.wave_id)
        except Exception as exc:
            code = str(getattr(exc, "code", "WAVE_NOT_QUIESCENT"))
            details = dict(getattr(exc, "details", {}) or {})
            raise OrchestrationControlError(
                code,
                str(exc),
                details={"run_id": ctx.run_id, "wave_id": ctx.wave_id, **details},
            ) from exc

    def mark_accepting(self, ctx: RunContext, *, proof_summary: dict[str, Any] | None = None) -> RunContext:
        if ctx.state != "PROVING":
            raise OrchestrationControlError("ACCEPT_OUTSIDE_PROOF", "Final acceptance can only follow PROVING state.")
        return self.transition(ctx, "ACCEPTING", reason="required_proof_green", payload=proof_summary or {})

    def checkpoint(self, ctx: RunContext, *, reason: str = "chatweb_sol_acceptance") -> RunContext:
        if ctx.state != "ACCEPTING":
            raise OrchestrationControlError("CHECKPOINT_OUTSIDE_ACCEPTANCE", "Checkpoint requires ACCEPTING state.")
        return self.transition(ctx, "CHECKPOINTED", reason=reason)

    def accept(self, ctx: RunContext, *, proof_summary: dict[str, Any] | None = None) -> RunContext:
        self.mark_accepting(ctx, proof_summary=proof_summary)
        return self.checkpoint(ctx)

    def snapshot(self, run_id: str) -> RunContext | None:
        with self._lock:
            current = self._contexts.get(run_id)
            if current is not None:
                return copy.deepcopy(current)
        return self.recover(run_id)

    def recover(self, run_id: str) -> RunContext | None:
        waves = self.ledger.list_waves(run_id)
        if not waves:
            return None
        wave = waves[-1]
        events = self.ledger.list_events(run_id, wave_id=wave["wave_id"])
        state = "PREFLIGHT"
        route_requested = ""
        route_resolved = ""
        delegation_id: str | None = None
        lease: WriteLease | None = None
        for event in events:
            if event.get("state_after"):
                state = str(event["state_after"])
            payload = event.get("payload") or {}
            if event["event_type"] == "route_selected":
                route_requested = str(payload.get("requested") or "")
                route_resolved = str(payload.get("resolved") or "")
            elif event["event_type"] == "delegation_started":
                delegation_id = event.get("delegation_id") or delegation_id
            elif event["event_type"] == "write_lease_acquired":
                lease = WriteLease(
                    lease_id=str(payload.get("lease_id") or ""),
                    owner=str(payload.get("owner") or ""),
                    mode=str(payload.get("mode") or ""),
                    base_head=str(payload.get("base_head") or ""),
                    worktree_fp=str(payload.get("worktree_fp") or ""),
                    fencing_token=int(payload.get("fencing_token") or 0),
                    expires_at=float(payload.get("expires_at") or 0),
                    scope_key=str(payload.get("scope_key") or WRITE_FENCE_SCOPE),
                    allowed_paths=tuple(payload.get("allowed_paths") or []),
                    delegation_id=event.get("delegation_id"),
                )
            elif event["event_type"] == "write_lease_revoked":
                lease = None
        if lease is not None:
            fence = self.ledger.assert_write_fence(
                scope_key=lease.scope_key,
                lease_id=lease.lease_id,
                fencing_token=lease.fencing_token,
                owner=lease.owner,
            )
            if not fence.get("valid"):
                lease = None
        ctx = RunContext(
            run_id=run_id,
            wave_id=wave["wave_id"],
            state=state,
            execution_mode=wave["execution_mode"],
            base_head=wave["base_head"],
            worktree_fp=wave["worktree_fp"],
            contract_fp=wave["contract_fp"],
            route_requested=route_requested,
            route_resolved=route_resolved,
            delegation_id=delegation_id,
            write_lease=lease,
        )
        with self._lock:
            self._contexts[run_id] = ctx
        return copy.deepcopy(ctx)

    @staticmethod
    def stable_contract_fingerprint(value: object) -> str:
        if not value:
            return ""
        if isinstance(value, str) and len(value) == 64 and all(ch in "0123456789abcdefABCDEF" for ch in value):
            return value.lower()
        raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
