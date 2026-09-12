from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import time
from datetime import datetime, timezone
from typing import Any

from .errors import ToolFailure
from .goal_pursuit import GoalPursuitError
from .runtime_behavior_identity import stable_python_code_sha256
from .controller_reattach import (
    CONTROLLER_REATTACH_MAX_ACTIVE_RUNS,
    attachment_row as _attachment_row,
    controller_identity as _controller_identity,
    ensure_controller_reattach_schema, problem_event_revision_schema_active,
    reattach_row as _reattach_row,
    run_binding_from_metadata as _controller_run_binding_from_metadata,
)

CONTROLLER_CONTINUITY_SCHEMA_VERSION = 1
CONTINUITY_CORE_SCHEMA_VERSION = 1
CONTINUITY_CORE_OUTER_BUDGET_BYTES = 8 * 1024
CONTINUITY_RECOVERY_MAX_REVISIONS = 32

CONTROLLER_KNOWLEDGE_ADVANCE_EVENTS = frozenset(
    {
        "PROBLEM_OPENED",
        "PROBLEM_REVISED",
        "PROBLEM_REOPENED",
        "PROBLEM_BLOCKED",
        "PROBLEM_PROVISIONAL_RESOLVED",
        "PROBLEM_RESOLVED_CONFIRMED",
        "PROBLEM_ABANDONED",
        "CONTRACT_CHANGED",
        "CRITERION_COVERAGE_CHANGED",
        "AUTHORITY_CHANGED",
        "NEXT_CRITICAL_ACTION_CHANGED",
        "CONTINUITY_CAPSULE_REFRESHED",
    }
)
CONTROLLER_KNOWLEDGE_NO_ADVANCE_EVENTS = frozenset(
    {
        "REPOSITORY_READ",
        "REPOSITORY_SEARCH",
        "WORKSPACE_DISCOVERY",
        "STATUS_POLL",
        "OUTPUT_PAGE_CONTINUATION",
        "LIVE_REFRESH_UNCHANGED",
        "EVIDENCE_READ",
    }
)
CONTROLLER_KNOWLEDGE_RECOVERY_EVENTS = frozenset(
    {
        "CONTINUITY_ACK",
        "CONTINUITY_READ",
        "CONTROLLER_REATTACH_READ",
    }
)

CONTINUITY_OMISSION_ORDER = (
    ("correlation_bindings", "CORRELATION_OMITTED_FOR_BUDGET"),
    ("execution_attempts", "EXECUTION_ATTEMPTS_OMITTED_FOR_BUDGET"),
    ("criterion_details", "CRITERION_DETAILS_OMITTED_FOR_BUDGET"),
    ("objective_summary", "OBJECTIVE_SUMMARY_OMITTED_FOR_BUDGET"),
)

_OPAQUE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:@/+\-=]{0,511}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


class ControllerContinuityError(ValueError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        category: str = "validation",
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.category = category
        self.retryable = retryable
        self.details = dict(details or {})


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha(value: Any) -> str:
    encoded = value if isinstance(value, bytes) else _json(value).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _opaque(value: Any, name: str, *, limit: int = 128) -> str:
    text = str(value or "").strip()
    if not text:
        raise ControllerContinuityError("CONTINUITY_IDENTITY_REQUIRED", f"{name} is required")
    if len(text) > limit or not _OPAQUE_RE.fullmatch(text):
        raise ControllerContinuityError("CONTINUITY_IDENTITY_INVALID", f"{name} is invalid")
    return text


def _digest(value: Any, name: str) -> str:
    text = str(value or "").strip().lower()
    if not _DIGEST_RE.fullmatch(text):
        raise ControllerContinuityError("CONTINUITY_FINGERPRINT_INVALID", f"{name} must be a SHA-256 digest")
    return text


def _revision(value: Any, name: str, *, optional: bool = False) -> int | None:
    if value is None and optional:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ControllerContinuityError("CONTINUITY_REVISION_INVALID", f"{name} must be a positive integer")
    return value


def controller_knowledge_policy(material_event_kind: Any) -> str:
    kind = str(material_event_kind or "").strip().upper()
    if kind in CONTROLLER_KNOWLEDGE_ADVANCE_EVENTS:
        return "ADVANCE"
    if kind in CONTROLLER_KNOWLEDGE_NO_ADVANCE_EVENTS:
        return "NO_ADVANCE"
    if kind in CONTROLLER_KNOWLEDGE_RECOVERY_EVENTS:
        return "RECOVERY_ONLY"
    return "CONSERVATIVE_UNKNOWN"


def _checkpoint_row(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "checkpoint_id": str(row["checkpoint_id"]),
        "workspace_id": str(row["workspace_id"]),
        "problem_id": str(row["problem_id"]),
        "problem_revision": int(row["problem_revision"]),
        "knowledge_revision": int(row["knowledge_revision"]),
        "prior_revision": int(row["prior_revision"]),
        "material_event_kind": str(row["material_event_kind"]),
        "material_event_id": str(row["material_event_id"]),
        "material_state_fingerprint": str(row["material_state_fingerprint"]),
        "capsule_fingerprint": str(row["capsule_fingerprint"]),
        "source_fingerprint": str(row["source_fingerprint"]),
        "runtime_behavior_fingerprint": str(row["runtime_behavior_fingerprint"]),
        "created_at": str(row["created_at"]),
    }


def _ack_row(row: sqlite3.Row) -> dict[str, Any]:
    recovery = json.loads(str(row["recovery_json"] or "{}"))
    return {
        "ack_id": str(row["ack_id"]),
        "workspace_id": str(row["workspace_id"]),
        "problem_id": str(row["problem_id"]),
        "problem_revision": int(row["problem_revision"]),
        "knowledge_revision": int(row["knowledge_revision"]) if row["knowledge_revision"] is not None else None,
        "current_knowledge_revision": int(row["current_knowledge_revision"]),
        "controller_endpoint_id": str(row["controller_endpoint_id"]),
        "status": str(row["status"]),
        "recovery": recovery,
        "created_at": str(row["created_at"]),
    }


class ControllerContinuityLedgerMixin:
    @staticmethod
    def _controller_continuity_ensure_schema(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS controller_continuity_meta (
                singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                schema_version INTEGER NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS controller_knowledge_checkpoints (
                checkpoint_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                problem_id TEXT NOT NULL,
                problem_revision INTEGER NOT NULL CHECK(problem_revision>=1),
                knowledge_revision INTEGER NOT NULL CHECK(knowledge_revision>=1),
                prior_revision INTEGER NOT NULL CHECK(prior_revision>=0),
                material_event_kind TEXT NOT NULL,
                material_event_id TEXT NOT NULL,
                material_state_fingerprint TEXT NOT NULL,
                capsule_fingerprint TEXT NOT NULL,
                source_fingerprint TEXT NOT NULL,
                runtime_behavior_fingerprint TEXT NOT NULL,
                request_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(workspace_id,problem_id,knowledge_revision),
                UNIQUE(workspace_id,material_event_kind,material_event_id),
                FOREIGN KEY(problem_id,problem_revision)
                    REFERENCES problem_revisions(problem_id,revision) ON DELETE RESTRICT
            );
            CREATE INDEX IF NOT EXISTS idx_controller_knowledge_problem_revision
                ON controller_knowledge_checkpoints(workspace_id,problem_id,knowledge_revision DESC);
            CREATE TABLE IF NOT EXISTS controller_knowledge_acks (
                ack_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                problem_id TEXT NOT NULL,
                problem_revision INTEGER NOT NULL CHECK(problem_revision>=1),
                knowledge_revision INTEGER,
                current_knowledge_revision INTEGER NOT NULL CHECK(current_knowledge_revision>=0),
                controller_endpoint_id TEXT NOT NULL,
                status TEXT NOT NULL,
                request_hash TEXT NOT NULL,
                recovery_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_controller_ack_problem_endpoint
                ON controller_knowledge_acks(workspace_id,problem_id,controller_endpoint_id,created_at DESC);
            """
        )
        ensure_controller_reattach_schema(connection)
        row = connection.execute(
            "SELECT schema_version FROM controller_continuity_meta WHERE singleton=1"
        ).fetchone()
        if row is None:
            connection.execute(
                "INSERT INTO controller_continuity_meta(singleton,schema_version,updated_at) VALUES(1,?,?)",
                (CONTROLLER_CONTINUITY_SCHEMA_VERSION, _now()),
            )
        elif int(row["schema_version"]) != CONTROLLER_CONTINUITY_SCHEMA_VERSION:
            raise ControllerContinuityError(
                "CONTROLLER_CONTINUITY_SCHEMA_UNSUPPORTED",
                "controller continuity schema version is unsupported",
            )

    def controller_continuity_schema_version(self) -> int:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT schema_version FROM controller_continuity_meta WHERE singleton=1"
            ).fetchone()
            return int(row["schema_version"]) if row is not None else 0

    def controller_goal_attachment(
        self, *, workspace_id: str, problem_id: str
    ) -> dict[str, Any] | None:
        workspace = _opaque(workspace_id, "workspace_id", limit=512)
        problem = _opaque(problem_id, "problem_id")
        with self._lock, self._connect() as connection:
            self._controller_continuity_ensure_schema(connection)
            row = connection.execute(
                """SELECT * FROM controller_goal_attachments
                   WHERE workspace_id=? AND problem_id=?""",
                (workspace, problem),
            ).fetchone()
        return _attachment_row(row)

    def controller_reattach_receipt(self, reattach_id: str) -> dict[str, Any] | None:
        reattach = _opaque(reattach_id, "reattach_id")
        with self._lock, self._connect() as connection:
            self._controller_continuity_ensure_schema(connection)
            row = connection.execute(
                "SELECT * FROM controller_reattach_receipts WHERE reattach_id=?",
                (reattach,),
            ).fetchone()
        return _reattach_row(row) if row is not None else None

    @staticmethod
    def _controller_assert_goal_run_precondition(
        connection: sqlite3.Connection,
        precondition: dict[str, Any],
    ) -> dict[str, Any] | None:
        workspace = str(precondition.get("workspace_id") or "").strip()
        problem = str(precondition.get("problem_id") or "").strip()
        revision = precondition.get("problem_revision")
        expected_generation = precondition.get("expected_generation")
        if (
            not workspace
            or not problem
            or isinstance(revision, bool)
            or not isinstance(revision, int)
            or revision < 1
            or isinstance(expected_generation, bool)
            or not isinstance(expected_generation, int)
            or expected_generation < 0
        ):
            raise ControllerContinuityError(
                "GOAL_CONTROLLER_PRECONDITION_INVALID",
                "Problem-bound RUN creation requires an exact controller-generation precondition",
                category="security",
            )
        row = connection.execute(
            """SELECT * FROM controller_goal_attachments
               WHERE workspace_id=? AND problem_id=?""",
            (workspace, problem),
        ).fetchone()
        attachment = _attachment_row(row)
        observed_generation = int((attachment or {}).get("generation") or 0)
        if observed_generation != expected_generation:
            raise ControllerContinuityError(
                "GOAL_CONTROLLER_GENERATION_STALE",
                "Goal controller generation changed before Problem-bound RUN creation",
                category="security",
                retryable=True,
                details={
                    "problem_id": problem,
                    "expected_generation": expected_generation,
                    "observed_generation": observed_generation,
                },
            )
        if attachment is None:
            return None
        owner = str(precondition.get("owner_client_id") or "").strip()
        endpoint = str(precondition.get("controller_endpoint_id") or "").strip()
        if int(attachment["problem_revision"]) != revision:
            raise ControllerContinuityError(
                "GOAL_CONTROLLER_REVISION_REATTACH_REQUIRED",
                "The current Problem Revision must be reattached before creating a new RUN",
                category="security",
                retryable=True,
            )
        if attachment["owner_client_id"] != owner or attachment["controller_endpoint_id"] != endpoint:
            raise ControllerContinuityError(
                "GOAL_CONTROLLER_FENCE_STALE",
                "This controller endpoint is fenced from the durable Goal",
                category="security",
                retryable=True,
                details={"problem_id": problem, "generation": observed_generation},
            )
        return attachment

    def controller_goal_run_precondition(
        self,
        *,
        workspace_id: str,
        problem_id: str,
        problem_revision: int,
        owner_client_id: str = "",
        controller_endpoint_id: str = "",
    ) -> dict[str, Any]:
        workspace = _opaque(workspace_id, "workspace_id", limit=512)
        problem = _opaque(problem_id, "problem_id")
        revision = int(_revision(problem_revision, "problem_revision") or 0)
        with self._lock, self._connect() as connection:
            self._controller_continuity_ensure_schema(connection)
            row = connection.execute(
                """SELECT * FROM controller_goal_attachments
                   WHERE workspace_id=? AND problem_id=?""",
                (workspace, problem),
            ).fetchone()
            attachment = _attachment_row(row)
            precondition = {
                "workspace_id": workspace,
                "problem_id": problem,
                "problem_revision": revision,
                "expected_generation": int((attachment or {}).get("generation") or 0),
                "owner_client_id": str(owner_client_id or "").strip(),
                "controller_endpoint_id": str(controller_endpoint_id or "").strip(),
            }
            self._controller_assert_goal_run_precondition(connection, precondition)
        return precondition

    def controller_run_problem_binding(self, run_id: str) -> dict[str, Any] | None:
        run = _opaque(run_id, "run_id", limit=256)
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT metadata_json FROM runs WHERE run_id=?", (run,)
            ).fetchone()
            if row is None:
                return None
            try:
                metadata = json.loads(str(row["metadata_json"] or "{}"))
            except (TypeError, json.JSONDecodeError):
                metadata = {}
            binding = _controller_run_binding_from_metadata(metadata)
            if binding is not None:
                return binding
            if not problem_event_revision_schema_active(connection):
                return None
            rows = connection.execute(
                """SELECT DISTINCT problem_id,problem_revision
                   FROM problem_events
                   WHERE run_id=? AND link_status='EXACT' AND link_role='PRIMARY'
                     AND problem_id IS NOT NULL AND problem_revision IS NOT NULL
                   ORDER BY problem_id,problem_revision""",
                (run,),
            ).fetchall()
        if not rows:
            return None
        identities = {(str(row["problem_id"]), int(row["problem_revision"])) for row in rows}
        if len(identities) != 1:
            raise ControllerContinuityError(
                "CONTROLLER_RUN_GOAL_AMBIGUOUS",
                "RUN has more than one exact primary Problem binding",
                category="security",
            )
        problem, revision = next(iter(identities))
        return {"workspace_id": "", "problem_id": problem, "problem_revision": revision}

    def controller_assert_goal_owner(
        self,
        *,
        workspace_id: str,
        problem_id: str,
        owner_client_id: str,
        controller_endpoint_id: str,
    ) -> dict[str, Any] | None:
        attachment = self.controller_goal_attachment(
            workspace_id=workspace_id, problem_id=problem_id
        )
        if attachment is None:
            return None
        if (
            attachment["owner_client_id"] != str(owner_client_id or "").strip()
            or attachment["controller_endpoint_id"] != str(controller_endpoint_id or "").strip()
        ):
            raise ControllerContinuityError(
                "GOAL_CONTROLLER_FENCE_STALE",
                "This controller endpoint is fenced from the durable Goal",
                category="security",
                retryable=True,
                details={
                    "problem_id": problem_id,
                    "generation": attachment["generation"],
                },
            )
        return attachment

    def controller_reattach_goal(
        self,
        *,
        reattach_id: str,
        workspace_id: str,
        problem_id: str,
        problem_revision: int,
        controller_endpoint_id: str,
        owner_client_id: str,
        ack_id: str,
        ack_status: str,
        continuity_core_fingerprint: str,
        source_fingerprint: str,
        runtime_behavior_fingerprint: str,
        ttl_seconds: float = 60.0,
    ) -> dict[str, Any]:
        reattach = _opaque(reattach_id, "reattach_id")
        workspace = _opaque(workspace_id, "workspace_id", limit=512)
        problem = _opaque(problem_id, "problem_id")
        revision = int(_revision(problem_revision, "problem_revision") or 0)
        endpoint = _opaque(controller_endpoint_id, "controller_endpoint_id")
        owner = _opaque(owner_client_id, "owner_client_id")
        ack = _opaque(ack_id, "ack_id")
        status = str(ack_status or "").strip().upper()
        if status not in {"CURRENT", "BEHIND", "MISSING"}:
            raise ControllerContinuityError(
                "CONTROLLER_REATTACH_ACK_UNSAFE",
                "Controller reattach requires a current, bounded-behind, or explicitly missing ACK",
                details={"ack_status": status},
            )
        core_fp = _digest(continuity_core_fingerprint, "continuity_core_fingerprint")
        source_fp = _digest(source_fingerprint, "source_fingerprint")
        runtime_fp = _digest(runtime_behavior_fingerprint, "runtime_behavior_fingerprint")
        request_hash = _sha(
            {
                "reattach_id": reattach,
                "workspace_id": workspace,
                "problem_id": problem,
                "problem_revision": revision,
                "controller_endpoint_id": endpoint,
                "owner_client_id": owner,
                "ack_id": ack,
                "ack_status": status,
                "continuity_core_fingerprint": core_fp,
                "source_fingerprint": source_fp,
                "runtime_behavior_fingerprint": runtime_fp,
            }
        )
        now = _now()
        expires_at = time.time() + max(1.0, float(ttl_seconds))
        with self._lock, self._connect() as connection:
            self._controller_continuity_ensure_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT * FROM controller_reattach_receipts WHERE reattach_id=?",
                (reattach,),
            ).fetchone()
            if existing is not None:
                if str(existing["request_hash"]) != request_hash:
                    raise ControllerContinuityError(
                        "CONTROLLER_REATTACH_IDENTITY_CONFLICT",
                        "reattach_id was reused with a different exact request",
                        category="security",
                    )
                connection.commit()
                return {"status": "IDEMPOTENT", "idempotent": True, **_reattach_row(existing)}
            thread = connection.execute(
                "SELECT current_revision FROM problem_threads WHERE problem_id=?", (problem,)
            ).fetchone()
            if thread is None or int(thread["current_revision"]) != revision:
                raise ControllerContinuityError(
                    "CONTINUITY_PROBLEM_REVISION_STALE",
                    "exact current Problem revision is required for controller reattach",
                )
            ack_row = connection.execute(
                "SELECT * FROM controller_knowledge_acks WHERE ack_id=?", (ack,)
            ).fetchone()
            if (
                ack_row is None
                or str(ack_row["workspace_id"]) != workspace
                or str(ack_row["problem_id"]) != problem
                or int(ack_row["problem_revision"]) != revision
                or str(ack_row["controller_endpoint_id"]) != endpoint
                or str(ack_row["status"]) != status
            ):
                raise ControllerContinuityError(
                    "CONTROLLER_REATTACH_ACK_MISMATCH",
                    "reattach ACK does not match the exact controller, Goal, and Problem Revision",
                    category="security",
                )
            client = connection.execute(
                "SELECT * FROM hub_clients WHERE client_id=?", (owner,)
            ).fetchone()
            if (
                client is None
                or str(client["client_type"]) != "chatweb"
                or str(client["role"]) != "controller"
                or str(client["status"]) != "online"
            ):
                raise ControllerContinuityError(
                    "CONTROLLER_REATTACH_CLIENT_UNAVAILABLE",
                    "the exact target ChatWeb controller is not registered online",
                    category="security",
                    retryable=True,
                )
            current_row = connection.execute(
                """SELECT * FROM controller_goal_attachments
                   WHERE workspace_id=? AND problem_id=?""",
                (workspace, problem),
            ).fetchone()
            prior_generation = int(current_row["generation"]) if current_row is not None else 0
            generation = prior_generation + 1
            active_run_revisions: dict[str, set[int]] = {}
            run_rows = connection.execute(
                "SELECT run_id,metadata_json FROM runs WHERE status='active' ORDER BY run_id"
            ).fetchall()
            for run_row in run_rows:
                try:
                    metadata = json.loads(str(run_row["metadata_json"] or "{}"))
                except (TypeError, json.JSONDecodeError):
                    metadata = {}
                binding = _controller_run_binding_from_metadata(metadata)
                if binding is not None and binding["problem_id"] == problem:
                    binding_workspace = str(binding.get("workspace_id") or "").strip()
                    if binding_workspace and binding_workspace != workspace:
                        raise ControllerContinuityError(
                            "WORKSPACE_SCOPE_MISMATCH",
                            "active Problem-bound RUN belongs to a different workspace identity",
                            category="security",
                        )
                    active_run_revisions.setdefault(str(run_row["run_id"]), set()).add(
                        int(binding["problem_revision"])
                    )
            event_rows = connection.execute(
                """SELECT DISTINCT r.run_id,e.problem_revision
                   FROM runs r JOIN problem_events e ON e.run_id=r.run_id
                   WHERE r.status='active' AND e.problem_id=?
                     AND e.link_status='EXACT' AND e.link_role='PRIMARY'""",
                (problem,),
            ).fetchall()
            for row in event_rows:
                active_run_revisions.setdefault(str(row["run_id"]), set()).add(
                    int(row["problem_revision"])
                )
            active_run_ids = set(active_run_revisions)
            if len(active_run_ids) > CONTROLLER_REATTACH_MAX_ACTIVE_RUNS:
                raise ControllerContinuityError(
                    "CONTROLLER_REATTACH_RUN_SET_UNBOUNDED",
                    "too many active RUNs are bound to the Goal for one bounded reattach",
                    category="security",
                    details={"active_run_count": len(active_run_ids)},
                )
            conflicts = [
                {"run_id": run_id, "problem_revisions": sorted(revisions)}
                for run_id, revisions in sorted(active_run_revisions.items())
                if revisions != {revision}
            ]
            if conflicts:
                raise ControllerContinuityError(
                    "CONTROLLER_REATTACH_ACTIVE_RUN_REVISION_CONFLICT",
                    "active RUN identity does not match the exact current Problem Revision",
                    category="security",
                    details={"conflicts": conflicts},
                )
            transfers: list[dict[str, Any]] = []
            for run_id in sorted(active_run_ids):
                lease_row = connection.execute(
                    "SELECT * FROM controller_leases WHERE run_id=?", (run_id,)
                ).fetchone()
                if (
                    lease_row is not None
                    and str(lease_row["status"]) == "active"
                    and float(lease_row["expires_at"] or 0) > time.time()
                    and str(lease_row["owner_client_id"] or "") != owner
                ):
                    raise ControllerContinuityError(
                        "CONTROLLER_HANDOFF_REQUIRED",
                        "active foreign controller lease must be released or expire before reattach",
                        category="security",
                        retryable=True,
                        details={
                            "run_id": run_id,
                            "owner_client_id": str(lease_row["owner_client_id"] or ""),
                            "fencing_token": int(lease_row["fencing_token"] or 0),
                        },
                    )
                token = int(lease_row["fencing_token"] or 0) + 1 if lease_row is not None else 1
                lease_id = "reattach:" + _sha(
                    {"reattach_id": reattach, "run_id": run_id, "generation": generation}
                )[:40]
                connection.execute(
                    """INSERT INTO controller_leases(
                           run_id,fencing_token,lease_id,owner_client_id,status,expires_at,updated_at
                       ) VALUES(?,?,?,?,?,?,?)
                       ON CONFLICT(run_id) DO UPDATE SET
                           fencing_token=excluded.fencing_token,lease_id=excluded.lease_id,
                           owner_client_id=excluded.owner_client_id,status='active',
                           expires_at=excluded.expires_at,updated_at=excluded.updated_at""",
                    (run_id, token, lease_id, owner, "active", expires_at, now),
                )
                transfers.append(
                    {
                        "run_id": run_id,
                        "prior_owner_client_id": str(lease_row["owner_client_id"] or "")
                        if lease_row is not None
                        else "",
                        "owner_client_id": owner,
                        "lease_id": lease_id,
                        "fencing_token": token,
                        "status": "active",
                    }
                )
            connection.execute(
                """INSERT INTO controller_goal_attachments(
                       workspace_id,problem_id,problem_revision,generation,controller_endpoint_id,
                       owner_client_id,last_reattach_id,updated_at
                   ) VALUES(?,?,?,?,?,?,?,?)
                   ON CONFLICT(workspace_id,problem_id) DO UPDATE SET
                       problem_revision=excluded.problem_revision,generation=excluded.generation,
                       controller_endpoint_id=excluded.controller_endpoint_id,
                       owner_client_id=excluded.owner_client_id,
                       last_reattach_id=excluded.last_reattach_id,updated_at=excluded.updated_at""",
                (workspace, problem, revision, generation, endpoint, owner, reattach, now),
            )
            connection.execute(
                """INSERT INTO controller_reattach_receipts(
                       reattach_id,workspace_id,problem_id,problem_revision,prior_generation,generation,
                       controller_endpoint_id,owner_client_id,ack_id,ack_status,continuity_core_fingerprint,request_hash,
                       active_run_transfers_json,source_fingerprint,runtime_behavior_fingerprint,created_at
                   ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    reattach,
                    workspace,
                    problem,
                    revision,
                    prior_generation,
                    generation,
                    endpoint,
                    owner,
                    ack,
                    status,
                    core_fp,
                    request_hash,
                    _json(transfers),
                    source_fp,
                    runtime_fp,
                    now,
                ),
            )
            receipt = connection.execute(
                "SELECT * FROM controller_reattach_receipts WHERE reattach_id=?",
                (reattach,),
            ).fetchone()
            connection.commit()
        assert receipt is not None
        return {"status": "REATTACHED", "idempotent": False, **_reattach_row(receipt)}

    @staticmethod
    def controller_knowledge_policy(material_event_kind: Any) -> str:
        return controller_knowledge_policy(material_event_kind)

    def controller_current_knowledge(self, *, workspace_id: str, problem_id: str) -> dict[str, Any] | None:
        workspace = _opaque(workspace_id, "workspace_id", limit=512)
        problem = _opaque(problem_id, "problem_id")
        with self._lock, self._connect() as connection:
            row = connection.execute(
                """SELECT * FROM controller_knowledge_checkpoints
                   WHERE workspace_id=? AND problem_id=?
                   ORDER BY knowledge_revision DESC LIMIT 1""",
                (workspace, problem),
            ).fetchone()
            return _checkpoint_row(row)

    def controller_record_knowledge_checkpoint(
        self,
        *,
        workspace_id: str,
        problem_id: str,
        problem_revision: int,
        material_event_kind: str,
        material_event_id: str,
        material_state_fingerprint: str,
        capsule_fingerprint: str,
        source_fingerprint: str,
        runtime_behavior_fingerprint: str,
        created_at: str | None = None,
    ) -> dict[str, Any]:
        workspace = _opaque(workspace_id, "workspace_id", limit=512)
        problem = _opaque(problem_id, "problem_id")
        revision = int(_revision(problem_revision, "problem_revision") or 0)
        kind = _opaque(str(material_event_kind or "").upper(), "material_event_kind", limit=96)
        event_id = _opaque(material_event_id, "material_event_id")
        state_fp = _digest(material_state_fingerprint, "material_state_fingerprint")
        capsule_fp = _digest(capsule_fingerprint, "capsule_fingerprint")
        source_fp = _digest(source_fingerprint, "source_fingerprint")
        runtime_fp = _digest(runtime_behavior_fingerprint, "runtime_behavior_fingerprint")
        policy = controller_knowledge_policy(kind)
        if policy != "ADVANCE":
            return {
                "status": policy,
                "advanced": False,
                "idempotent": False,
                "policy": policy,
                "checkpoint": self.controller_current_knowledge(workspace_id=workspace, problem_id=problem),
            }
        timestamp = str(created_at or _now())
        request = {
            "workspace_id": workspace,
            "problem_id": problem,
            "problem_revision": revision,
            "material_event_kind": kind,
            "material_event_id": event_id,
            "material_state_fingerprint": state_fp,
            "capsule_fingerprint": capsule_fp,
            "source_fingerprint": source_fp,
            "runtime_behavior_fingerprint": runtime_fp,
        }
        request_hash = _sha(request)
        with self._lock, self._connect() as connection:
            self._controller_continuity_ensure_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            thread = connection.execute(
                "SELECT current_revision FROM problem_threads WHERE problem_id=?", (problem,)
            ).fetchone()
            revision_row = connection.execute(
                "SELECT 1 FROM problem_revisions WHERE problem_id=? AND revision=?", (problem, revision)
            ).fetchone()
            if thread is None or revision_row is None or int(thread["current_revision"]) != revision:
                raise ControllerContinuityError(
                    "CONTINUITY_PROBLEM_REVISION_STALE",
                    "knowledge checkpoint requires the exact current Problem revision",
                )
            existing = connection.execute(
                """SELECT * FROM controller_knowledge_checkpoints
                   WHERE workspace_id=? AND material_event_kind=? AND material_event_id=?""",
                (workspace, kind, event_id),
            ).fetchone()
            if existing is not None:
                if str(existing["request_hash"]) != request_hash:
                    raise ControllerContinuityError(
                        "MATERIAL_EVENT_STATE_CONFLICT",
                        "material event identity is already bound to different durable state",
                    )
                return {
                    "status": "IDEMPOTENT",
                    "advanced": False,
                    "idempotent": True,
                    "policy": policy,
                    "checkpoint": _checkpoint_row(existing),
                }
            latest = connection.execute(
                """SELECT * FROM controller_knowledge_checkpoints
                   WHERE workspace_id=? AND problem_id=?
                   ORDER BY knowledge_revision DESC LIMIT 1""",
                (workspace, problem),
            ).fetchone()
            if latest is not None and str(latest["material_state_fingerprint"]) == state_fp:
                return {
                    "status": "NO_ADVANCE_UNCHANGED_STATE",
                    "advanced": False,
                    "idempotent": False,
                    "policy": policy,
                    "checkpoint": _checkpoint_row(latest),
                }
            prior = int(latest["knowledge_revision"]) if latest is not None else 0
            knowledge_revision = prior + 1
            checkpoint_id = "kcp-" + _sha({"request_hash": request_hash, "revision": knowledge_revision})[:40]
            connection.execute(
                """INSERT INTO controller_knowledge_checkpoints(
                       checkpoint_id,workspace_id,problem_id,problem_revision,knowledge_revision,prior_revision,
                       material_event_kind,material_event_id,material_state_fingerprint,capsule_fingerprint,
                       source_fingerprint,runtime_behavior_fingerprint,request_hash,created_at
                   ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    checkpoint_id,
                    workspace,
                    problem,
                    revision,
                    knowledge_revision,
                    prior,
                    kind,
                    event_id,
                    state_fp,
                    capsule_fp,
                    source_fp,
                    runtime_fp,
                    request_hash,
                    timestamp,
                ),
            )
            inserted = connection.execute(
                "SELECT * FROM controller_knowledge_checkpoints WHERE checkpoint_id=?", (checkpoint_id,)
            ).fetchone()
            return {
                "status": "ADVANCED",
                "advanced": True,
                "idempotent": False,
                "policy": policy,
                "checkpoint": _checkpoint_row(inserted),
            }

    def controller_ack_knowledge(
        self,
        *,
        ack_id: str,
        workspace_id: str,
        problem_id: str,
        problem_revision: int,
        knowledge_revision: int | None,
        controller_endpoint_id: str,
        recovery_limit: int = CONTINUITY_RECOVERY_MAX_REVISIONS,
        created_at: str | None = None,
    ) -> dict[str, Any]:
        ack = _opaque(ack_id, "ack_id")
        workspace = _opaque(workspace_id, "workspace_id", limit=512)
        problem = _opaque(problem_id, "problem_id")
        supplied_problem_revision = int(_revision(problem_revision, "problem_revision") or 0)
        endpoint = _opaque(controller_endpoint_id, "controller_endpoint_id", limit=256)
        if knowledge_revision is not None and (
            isinstance(knowledge_revision, bool) or not isinstance(knowledge_revision, int)
        ):
            raise ControllerContinuityError(
                "CONTINUITY_REVISION_INVALID", "knowledge_revision must be a positive integer or null"
            )
        limit = max(1, min(int(recovery_limit), CONTINUITY_RECOVERY_MAX_REVISIONS))
        request = {
            "workspace_id": workspace,
            "problem_id": problem,
            "problem_revision": supplied_problem_revision,
            "knowledge_revision": knowledge_revision,
            "controller_endpoint_id": endpoint,
        }
        request_hash = _sha(request)
        with self._lock, self._connect() as connection:
            self._controller_continuity_ensure_schema(connection)
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT * FROM controller_knowledge_acks WHERE ack_id=?", (ack,)
            ).fetchone()
            if existing is not None:
                if str(existing["request_hash"]) != request_hash:
                    raise ControllerContinuityError(
                        "CONTROLLER_ACK_IDENTITY_CONFLICT",
                        "ack_id is already bound to different acknowledgement bytes",
                    )
                return {"recorded": False, "idempotent": True, "ack": _ack_row(existing)}
            thread = connection.execute(
                "SELECT current_revision FROM problem_threads WHERE problem_id=?", (problem,)
            ).fetchone()
            current_row = connection.execute(
                """SELECT * FROM controller_knowledge_checkpoints
                   WHERE workspace_id=? AND problem_id=?
                   ORDER BY knowledge_revision DESC LIMIT 1""",
                (workspace, problem),
            ).fetchone()
            current = _checkpoint_row(current_row)
            current_revision = int(current["knowledge_revision"]) if current is not None else 0
            recovery: dict[str, Any] = {
                "delta": [],
                "delta_complete": True,
                "history_lost": False,
                "current_checkpoint": current,
                "authority_granted": False,
            }
            if thread is None or current is None:
                status = "MISSING"
            elif (
                int(thread["current_revision"]) != supplied_problem_revision
                or int(current["problem_revision"]) != supplied_problem_revision
            ):
                status = "INVALID"
            elif knowledge_revision is None:
                status = "MISSING"
            elif knowledge_revision < 1:
                status = "INVALID"
            elif knowledge_revision > current_revision:
                status = "FUTURE"
            elif knowledge_revision == current_revision:
                status = "CURRENT"
            else:
                delta_rows = connection.execute(
                    """SELECT * FROM controller_knowledge_checkpoints
                       WHERE workspace_id=? AND problem_id=? AND knowledge_revision>?
                       ORDER BY knowledge_revision LIMIT ?""",
                    (workspace, problem, knowledge_revision, limit + 1),
                ).fetchall()
                expected_first = knowledge_revision + 1
                complete = (
                    len(delta_rows) <= limit
                    and bool(delta_rows)
                    and int(delta_rows[0]["knowledge_revision"]) == expected_first
                    and int(delta_rows[-1]["knowledge_revision"]) == current_revision
                )
                if complete:
                    status = "BEHIND"
                    recovery["delta"] = [_checkpoint_row(row) for row in delta_rows]
                else:
                    status = "HISTORY_LOST"
                    recovery["delta_complete"] = False
                    recovery["history_lost"] = True
            recovery["status"] = status
            recovery["exact_read_refresh_required"] = status not in {"CURRENT", "BEHIND"}
            timestamp = str(created_at or _now())
            connection.execute(
                """INSERT INTO controller_knowledge_acks(
                       ack_id,workspace_id,problem_id,problem_revision,knowledge_revision,
                       current_knowledge_revision,controller_endpoint_id,status,request_hash,recovery_json,created_at
                   ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    ack,
                    workspace,
                    problem,
                    supplied_problem_revision,
                    knowledge_revision,
                    current_revision,
                    endpoint,
                    status,
                    request_hash,
                    _json(recovery),
                    timestamp,
                ),
            )
            inserted = connection.execute(
                "SELECT * FROM controller_knowledge_acks WHERE ack_id=?", (ack,)
            ).fetchone()
            return {"recorded": True, "idempotent": False, "ack": _ack_row(inserted)}


def _bounded_text(value: Any, limit: int) -> str:
    return str(value or "").strip()[:limit]


def _section_receipt(section: str, code: str, value: Any) -> dict[str, Any]:
    encoded = _json(value).encode("utf-8")
    count = len(value) if isinstance(value, (list, dict)) else (1 if value not in {None, ""} else 0)
    return {
        "section": section,
        "reason": code,
        "item_count": count,
        "omitted_bytes": len(encoded),
        "omitted_identity": _sha(encoded),
        "exact_refresh_required": True,
    }


def _core_size(value: dict[str, Any], outer_budget: int) -> int:
    candidate = dict(value)
    candidate["continuity_core_fingerprint"] = "0" * 64
    candidate["serialized_bytes"] = outer_budget
    return len(_json(candidate).encode("utf-8"))


def _core_fingerprint(value: dict[str, Any]) -> str:
    basis = {
        key: item
        for key, item in value.items()
        if key not in {"continuity_core_fingerprint", "serialized_bytes"}
    }
    return _sha(basis)


def _normalize_attempts(items: Any) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []
    result: list[dict[str, Any]] = []
    for item in items[:50]:
        if not isinstance(item, dict):
            continue
        result.append(
            {
                "run_id": _bounded_text(item.get("run_id"), 128),
                "wave_id": _bounded_text(item.get("wave_id"), 128),
                "status": _bounded_text(
                    item.get("status")
                    or item.get("checkpoint_status")
                    or item.get("wave_status")
                    or item.get("run_status"),
                    64,
                )
                or "UNKNOWN",
                "checkpoint_id": _bounded_text(item.get("checkpoint_id"), 128) or None,
            }
        )
    return result


def _normalize_correlations(items: Any) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []
    result: list[dict[str, Any]] = []
    for item in items[:50]:
        if not isinstance(item, dict):
            continue
        result.append(
            {
                "run_id": _bounded_text(item.get("run_id"), 128) or None,
                "turn_id": _bounded_text(item.get("turn_id"), 128) or None,
                "trace_id": _bounded_text(item.get("trace_id"), 128) or None,
                "relation": _bounded_text(item.get("relation"), 64) or "EXACT",
            }
        )
    return result


def build_continuity_core(
    *,
    workspace_id: str,
    problem_projection: dict[str, Any],
    knowledge_checkpoint: dict[str, Any] | None,
    source_identity: dict[str, Any],
    runtime_behavior_fingerprint: str,
    goal_projection: dict[str, Any] | None = None,
    execution_attempts: list[dict[str, Any]] | None = None,
    correlation_bindings: list[dict[str, Any]] | None = None,
    outer_budget: int = CONTINUITY_CORE_OUTER_BUDGET_BYTES,
) -> dict[str, Any]:
    if not isinstance(problem_projection, dict):
        raise ControllerContinuityError("CONTINUITY_PROBLEM_REQUIRED", "exact Problem projection is required")
    thread = problem_projection.get("thread") if isinstance(problem_projection.get("thread"), dict) else {}
    revision = (
        problem_projection.get("current_revision")
        if isinstance(problem_projection.get("current_revision"), dict)
        else {}
    )
    problem_id = _opaque(thread.get("problem_id"), "problem_id")
    problem_revision = int(_revision(thread.get("current_revision"), "problem_revision") or 0)
    contract_fp = _digest(revision.get("contract_fingerprint"), "contract_fingerprint")
    criteria_fp = _digest(revision.get("criteria_fingerprint"), "criteria_fingerprint")
    workspace = _opaque(workspace_id, "workspace_id", limit=512)
    source_fp = _digest(source_identity.get("source_fingerprint"), "source_fingerprint")
    worktree_fp = _digest(source_identity.get("worktree_fp"), "worktree_fp")
    runtime_fp = _digest(runtime_behavior_fingerprint, "runtime_behavior_fingerprint")
    goal = goal_projection if isinstance(goal_projection, dict) else {}
    checkpoint = knowledge_checkpoint if isinstance(knowledge_checkpoint, dict) else {}
    capsule = revision.get("capsule") if isinstance(revision.get("capsule"), dict) else {}
    criteria = capsule.get("acceptance_criteria") if isinstance(capsule.get("acceptance_criteria"), list) else []
    normalized_criteria: list[dict[str, str]] = []
    for item in criteria[:100]:
        if not isinstance(item, dict):
            continue
        criterion_id = _bounded_text(item.get("criterion_id"), 128)
        if criterion_id:
            normalized_criteria.append(
                {"criterion_id": criterion_id, "summary": _bounded_text(item.get("summary"), 800)}
            )
    coverage_raw = goal.get("criterion_coverage") if isinstance(goal.get("criterion_coverage"), dict) else {}
    accepted: list[dict[str, Any]] = []
    remaining: list[str] = []
    details: dict[str, str] = {}
    for item in normalized_criteria:
        criterion_id = item["criterion_id"]
        details[criterion_id] = item["summary"]
        coverage = coverage_raw.get(criterion_id) if isinstance(coverage_raw.get(criterion_id), dict) else {}
        status = str(coverage.get("status") or "UNRESOLVED").upper()
        if status in {"PROVEN", "SATISFIED", "SATISFIED_NON_CODE"}:
            proof_refs = coverage.get("proof_refs") if isinstance(coverage.get("proof_refs"), list) else []
            accepted.append(
                {
                    "criterion_id": criterion_id,
                    "status": status,
                    "proof_refs": [_bounded_text(ref, 128) for ref in proof_refs[:8] if _bounded_text(ref, 128)],
                }
            )
        else:
            remaining.append(criterion_id)
    objective_summary = _bounded_text(capsule.get("objective_summary"), 20_000)
    invariants_raw = capsule.get("protected_invariants") if isinstance(capsule.get("protected_invariants"), list) else []
    protected_invariants = [_bounded_text(item, 512) for item in invariants_raw[:32] if _bounded_text(item, 512)]
    knowledge_revision = int(checkpoint.get("knowledge_revision") or 0)
    material_state_fp = str(checkpoint.get("material_state_fingerprint") or "")
    capsule_fp = str(checkpoint.get("capsule_fingerprint") or "")
    if knowledge_revision:
        _digest(material_state_fp, "material_state_fingerprint")
        _digest(capsule_fp, "capsule_fingerprint")
    core: dict[str, Any] = {
        "schema_version": CONTINUITY_CORE_SCHEMA_VERSION,
        "provenance": "CONTINUITY_CORE",
        "workspace_id": workspace,
        "problem_id": problem_id,
        "problem_revision": problem_revision,
        "contract_fingerprint": contract_fp,
        "criteria_fingerprint": criteria_fp,
        "problem_state": _bounded_text(thread.get("resolution_state"), 64) or "UNKNOWN",
        "resolution_status": _bounded_text(goal.get("resolution_status"), 96)
        or _bounded_text(thread.get("resolution_state"), 64)
        or "UNKNOWN",
        "next_action": _bounded_text(goal.get("next_action"), 256) or "REFRESH_GOAL_PURSUIT_PROJECTION",
        "next_critical_gap": _bounded_text(goal.get("next_critical_gap"), 512) or None,
        "knowledge_revision": knowledge_revision,
        "material_state_fingerprint": material_state_fp or None,
        "capsule_fingerprint": capsule_fp or None,
        "base_head": _bounded_text(source_identity.get("base_head"), 128) or None,
        "worktree_fp": worktree_fp,
        "source_fingerprint": source_fp,
        "runtime_behavior_fingerprint": runtime_fp,
        "source_currentness_at_record": "MATCHED",
        "runtime_currentness_at_record": "MATCHED",
        "protected_invariants": protected_invariants,
        "accepted_criteria": accepted,
        "remaining_criteria": remaining,
        "objective_summary": objective_summary,
        "criterion_details": details,
        "execution_attempts": _normalize_attempts(execution_attempts),
        "correlation_bindings": _normalize_correlations(correlation_bindings),
        "omissions": [],
        "exact_read_refresh_required": False,
        "enrichment_included": False,
        "authority": {
            "mutation_authority_granted": False,
            "acceptance_authority_granted": False,
            "problem_revision_authority_granted": False,
        },
    }
    budget = int(outer_budget)
    if budget < 1024 or budget > CONTINUITY_CORE_OUTER_BUDGET_BYTES:
        raise ControllerContinuityError(
            "CONTINUITY_CORE_BUDGET_INVALID", "continuity outer budget must be between 1024 and 8192 bytes"
        )
    mandatory = dict(core)
    for key, _code in CONTINUITY_OMISSION_ORDER:
        mandatory.pop(key, None)
    mandatory.pop("remaining_criteria", None)
    if _core_size(mandatory, budget) > budget:
        raise ControllerContinuityError(
            "CONTINUITY_CORE_MANDATORY_BUDGET_EXCEEDED",
            "mandatory Continuity Core cannot fit within the existing outer budget",
        )
    for section, code in CONTINUITY_OMISSION_ORDER:
        if _core_size(core, budget) <= budget:
            break
        value = core.pop(section, None)
        core["omissions"].append(_section_receipt(section, code, value))
    if _core_size(core, budget) > budget:
        original_remaining = list(core.get("remaining_criteria") or [])
        omitted: list[str] = []
        receipt_index = len(core["omissions"])
        while core.get("remaining_criteria"):
            if omitted:
                ordered_omitted = list(reversed(omitted))
                receipt = _section_receipt(
                    "remaining_criteria",
                    "REMAINING_CRITERIA_TRUNCATED_FOR_BUDGET",
                    ordered_omitted,
                )
                if len(core["omissions"]) == receipt_index:
                    core["omissions"].append(receipt)
                else:
                    core["omissions"][receipt_index] = receipt
                if _core_size(core, budget) <= budget:
                    break
            omitted.append(core["remaining_criteria"].pop())
        if omitted and len(core["omissions"]) == receipt_index:
            core["omissions"].append(
                _section_receipt(
                    "remaining_criteria",
                    "REMAINING_CRITERIA_TRUNCATED_FOR_BUDGET",
                    list(reversed(omitted)),
                )
            )
        if _core_size(core, budget) > budget:
            raise ControllerContinuityError(
                "CONTINUITY_CORE_MANDATORY_BUDGET_EXCEEDED",
                "Continuity Core mandatory identities and omission receipts exceed the outer budget",
            )
        if len(original_remaining) != len(core.get("remaining_criteria") or []) + len(omitted):
            raise AssertionError("remaining criteria omission accounting drifted")
    core["exact_read_refresh_required"] = bool(core["omissions"])
    core["continuity_core_fingerprint"] = _core_fingerprint(core)
    core["serialized_bytes"] = 0
    for _ in range(4):
        actual = len(_json(core).encode("utf-8"))
        if core["serialized_bytes"] == actual:
            break
        core["serialized_bytes"] = actual
    if len(_json(core).encode("utf-8")) > budget:
        raise ControllerContinuityError(
            "CONTINUITY_CORE_BUDGET_ACCOUNTING_ERROR", "serialized Continuity Core exceeded its outer budget"
        )
    return core


def validate_continuity_core_currentness(
    capsule: dict[str, Any],
    *,
    current_source_fingerprint: str | None,
    current_runtime_behavior_fingerprint: str | None,
) -> dict[str, Any]:
    if not isinstance(capsule, dict) or capsule.get("schema_version") != CONTINUITY_CORE_SCHEMA_VERSION:
        raise ControllerContinuityError("CONTINUITY_CORE_INVALID", "Continuity Core schema is invalid")
    expected_fp = str(capsule.get("continuity_core_fingerprint") or "")
    if not _DIGEST_RE.fullmatch(expected_fp) or _core_fingerprint(capsule) != expected_fp:
        raise ControllerContinuityError("CONTINUITY_CORE_FINGERPRINT_MISMATCH", "Continuity Core bytes changed")
    if not current_source_fingerprint or not current_runtime_behavior_fingerprint:
        return {
            "status": "UNKNOWN",
            "exact_read_refresh_required": True,
            "authority_granted": False,
        }
    source = _digest(current_source_fingerprint, "current_source_fingerprint")
    runtime = _digest(current_runtime_behavior_fingerprint, "current_runtime_behavior_fingerprint")
    if source != str(capsule.get("source_fingerprint") or ""):
        raise ControllerContinuityError("CONTINUITY_SOURCE_STALE", "Continuity Core source fingerprint is stale")
    if runtime != str(capsule.get("runtime_behavior_fingerprint") or ""):
        raise ControllerContinuityError("CONTINUITY_RUNTIME_STALE", "Continuity Core runtime behavior fingerprint is stale")
    return {
        "status": "CURRENT",
        "exact_read_refresh_required": bool(capsule.get("exact_read_refresh_required")),
        "authority_granted": False,
    }


class ControllerContinuityControlMixin:
    @staticmethod
    def _continuity_tool_failure(exc: ControllerContinuityError) -> ToolFailure:
        return ToolFailure(
            exc.code,
            str(exc),
            category=exc.category,
            retryable=exc.retryable,
            details=exc.details,
        )

    def _continuity_current_controller_identity(
        self, *, required: bool = True
    ) -> dict[str, str] | None:
        client = self._current_hub_client() or {}
        identity = _controller_identity(client, self._hub_client_record_id(client) if client else "")
        if identity is None and required:
            raise ControllerContinuityError(
                "CONTINUITY_CONTROLLER_REQUIRED",
                "continuity mutation requires the current ChatWeb controller endpoint",
                category="security",
            )
        return identity

    def _continuity_controller_endpoint_id(self) -> str:
        identity = self._continuity_current_controller_identity(required=True)
        assert identity is not None
        return identity["controller_endpoint_id"]

    def _continuity_goal_controller_precondition(
        self, *, problem_id: str, problem_revision: int
    ) -> dict[str, Any]:
        source = self._orchestration_workspace_identity(".")
        workspace_identity = (
            source.get("workspace_identity")
            if isinstance(source.get("workspace_identity"), dict)
            else {}
        )
        workspace_id = str(workspace_identity.get("workspace_id") or "").strip()
        if not workspace_id:
            workspace_id = str(self._workspace_identity_for_request(".")[2].get("workspace_id") or "")
        workspace_id = _opaque(workspace_id, "workspace_id", limit=512)
        identity = self._continuity_current_controller_identity(required=False) or {}
        return self.orchestration_ledger.controller_goal_run_precondition(
            workspace_id=workspace_id,
            problem_id=problem_id,
            problem_revision=problem_revision,
            owner_client_id=str(identity.get("owner_client_id") or ""),
            controller_endpoint_id=str(identity.get("controller_endpoint_id") or ""),
        )

    def _continuity_assert_run_controller(self, run_id: str) -> dict[str, Any] | None:
        try:
            binding = self.orchestration_ledger.controller_run_problem_binding(run_id)
            if binding is None:
                return None
            workspace_id = str(binding.get("workspace_id") or "").strip()
            if not workspace_id:
                source = self._orchestration_workspace_identity(".")
                workspace_identity = (
                    source.get("workspace_identity")
                    if isinstance(source.get("workspace_identity"), dict)
                    else {}
                )
                workspace_id = str(workspace_identity.get("workspace_id") or "").strip()
                if not workspace_id:
                    workspace_id = str(self._workspace_identity_for_request(".")[2].get("workspace_id") or "")
                workspace_id = _opaque(workspace_id, "workspace_id", limit=512)
            identity = self._continuity_current_controller_identity(required=False) or {}
            return self.orchestration_ledger.controller_assert_goal_owner(
                workspace_id=workspace_id,
                problem_id=str(binding["problem_id"]),
                owner_client_id=str(identity.get("owner_client_id") or ""),
                controller_endpoint_id=str(identity.get("controller_endpoint_id") or ""),
            )
        except ControllerContinuityError as exc:
            raise self._continuity_tool_failure(exc) from exc

    def _continuity_exact_problem(self, event: dict[str, Any]) -> dict[str, Any]:
        raw_problem = event.get("problem_id")
        raw_revision = event.get("problem_revision")
        if raw_problem is None and raw_revision is None:
            try:
                identity = self.orchestration_ledger.goal_pursuit_resolve_identity()
            except GoalPursuitError as exc:
                raise ControllerContinuityError(
                    exc.code,
                    str(exc),
                    details=exc.details,
                ) from exc
            problem_id = str(identity["problem_id"])
            problem_revision = int(identity["problem_revision"])
        else:
            problem_id = _opaque(raw_problem, "problem_id")
            problem_revision = int(_revision(raw_revision, "problem_revision") or 0)
        problem = self.orchestration_ledger.problem_get(problem_id)
        if (
            problem is None
            or int((problem.get("thread") or {}).get("current_revision") or 0) != problem_revision
            or problem.get("legacy_or_missing_contract") is True
        ):
            raise ControllerContinuityError(
                "CONTINUITY_PROBLEM_REVISION_STALE", "exact current Problem revision is required"
            )
        return problem

    def _continuity_goal_projection(self, problem: dict[str, Any]) -> dict[str, Any]:
        thread = problem.get("thread") if isinstance(problem.get("thread"), dict) else {}
        problem_id = str(thread.get("problem_id") or "")
        problem_revision = int(thread.get("current_revision") or 0)
        projector = getattr(self.orchestration_ledger, "goal_pursuit_projection", None)
        if callable(projector):
            return projector(problem_id=problem_id, problem_revision=problem_revision)
        state = str(thread.get("resolution_state") or "UNKNOWN")
        return {
            "resolution_status": state,
            "next_action": "REFRESH_GOAL_PURSUIT_PROJECTION",
            "next_critical_gap": None,
            "criterion_coverage": {},
            "execution_attempts": [],
            "correlation_bindings": [],
        }

    def _continuity_runtime_identity(self) -> tuple[dict[str, Any], str, str]:
        source = self._orchestration_workspace_identity(".")
        workspace_identity = source.get("workspace_identity") if isinstance(source.get("workspace_identity"), dict) else {}
        workspace_id = _opaque(workspace_identity.get("workspace_id"), "workspace_id", limit=512)
        behavior = self._loaded_behavior_identity()
        continuity_code_fp = stable_python_code_sha256(
            type(self)._controller_continuity_control.__code__
        )
        runtime_fp = _sha(
            {
                "loaded_behavior_fingerprint": _digest(
                    behavior.get("fingerprint"), "loaded_behavior_fingerprint"
                ),
                "controller_continuity_code_fingerprint": continuity_code_fp,
            }
        )
        return source, workspace_id, runtime_fp

    def _continuity_build_current_core(
        self,
        *,
        problem: dict[str, Any],
        source: dict[str, Any],
        workspace_id: str,
        runtime_fingerprint: str,
    ) -> dict[str, Any]:
        thread = problem.get("thread") if isinstance(problem.get("thread"), dict) else {}
        problem_id = str(thread.get("problem_id") or "")
        goal = self._continuity_goal_projection(problem)
        checkpoint = self.orchestration_ledger.controller_current_knowledge(
            workspace_id=workspace_id, problem_id=problem_id
        )
        return build_continuity_core(
            workspace_id=workspace_id,
            problem_projection=problem,
            knowledge_checkpoint=checkpoint,
            source_identity=source,
            runtime_behavior_fingerprint=runtime_fingerprint,
            goal_projection=goal,
            execution_attempts=goal.get("execution_attempts"),
            correlation_bindings=goal.get("correlation_bindings"),
        )

    def _controller_continuity_control(self, args: dict[str, Any]) -> dict[str, Any]:
        action = str(args.get("continuity_action") or "get").strip().lower()
        event = args.get("continuity_event")
        if not isinstance(event, dict):
            raise ToolFailure(
                "CONTINUITY_EVENT_REQUIRED", "continuity_event is required", category="validation"
            )
        try:
            if action == "policy":
                kind = str(event.get("material_event_kind") or "").strip().upper()
                return {
                    "material_event_kind": kind,
                    "policy": controller_knowledge_policy(kind),
                    "authority_granted": False,
                }
            problem = self._continuity_exact_problem(event)
            source, workspace_id, runtime_fp = self._continuity_runtime_identity()
            thread = problem["thread"]
            problem_id = str(thread["problem_id"])
            problem_revision = int(thread["current_revision"])
            if action == "get":
                core = self._continuity_build_current_core(
                    problem=problem,
                    source=source,
                    workspace_id=workspace_id,
                    runtime_fingerprint=runtime_fp,
                )
                return {
                    "continuity_core": core,
                    "currentness": validate_continuity_core_currentness(
                        core,
                        current_source_fingerprint=str(source.get("source_fingerprint") or ""),
                        current_runtime_behavior_fingerprint=runtime_fp,
                    ),
                    "authority_granted": False,
                }
            controller_identity = self._continuity_current_controller_identity(required=True)
            assert controller_identity is not None
            endpoint = controller_identity["controller_endpoint_id"]
            if action == "checkpoint":
                kind = str(event.get("material_event_kind") or "").strip().upper()
                event_id = _opaque(event.get("material_event_id"), "material_event_id")
                goal = self._continuity_goal_projection(problem)
                material_state = {
                    "problem_id": problem_id,
                    "problem_revision": problem_revision,
                    "contract_fingerprint": str(problem["current_revision"].get("contract_fingerprint") or ""),
                    "criteria_fingerprint": str(problem["current_revision"].get("criteria_fingerprint") or ""),
                    "problem_state": str(thread.get("resolution_state") or "UNKNOWN"),
                    "resolution_status": str(goal.get("resolution_status") or "UNKNOWN"),
                    "next_action": str(goal.get("next_action") or "UNKNOWN"),
                    "controller_endpoint_id": endpoint,
                    "source_fingerprint": str(source.get("source_fingerprint") or ""),
                    "runtime_behavior_fingerprint": runtime_fp,
                }
                material_state_fp = _sha(material_state)
                capsule_fp = _sha(
                    {
                        "material_state_fingerprint": material_state_fp,
                        "source_fingerprint": source.get("source_fingerprint"),
                        "runtime_behavior_fingerprint": runtime_fp,
                    }
                )
                recorded = self.orchestration_ledger.controller_record_knowledge_checkpoint(
                    workspace_id=workspace_id,
                    problem_id=problem_id,
                    problem_revision=problem_revision,
                    material_event_kind=kind,
                    material_event_id=event_id,
                    material_state_fingerprint=material_state_fp,
                    capsule_fingerprint=capsule_fp,
                    source_fingerprint=str(source.get("source_fingerprint") or ""),
                    runtime_behavior_fingerprint=runtime_fp,
                )
                core = self._continuity_build_current_core(
                    problem=problem,
                    source=source,
                    workspace_id=workspace_id,
                    runtime_fingerprint=runtime_fp,
                )
                return {
                    "knowledge_checkpoint": recorded,
                    "continuity_core": core,
                    "authority_granted": False,
                }
            if action == "ack":
                acked = self.orchestration_ledger.controller_ack_knowledge(
                    ack_id=_opaque(event.get("ack_id"), "ack_id"),
                    workspace_id=workspace_id,
                    problem_id=problem_id,
                    problem_revision=problem_revision,
                    knowledge_revision=event.get("knowledge_revision"),
                    controller_endpoint_id=endpoint,
                )
                core = self._continuity_build_current_core(
                    problem=problem,
                    source=source,
                    workspace_id=workspace_id,
                    runtime_fingerprint=runtime_fp,
                )
                return {
                    "knowledge_ack": acked,
                    "continuity_core": core,
                    "authority_granted": False,
                }
            if action == "reattach":
                core = self._continuity_build_current_core(
                    problem=problem,
                    source=source,
                    workspace_id=workspace_id,
                    runtime_fingerprint=runtime_fp,
                )
                currentness = validate_continuity_core_currentness(
                    core,
                    current_source_fingerprint=str(source.get("source_fingerprint") or ""),
                    current_runtime_behavior_fingerprint=runtime_fp,
                )
                expected_core_fp = _digest(
                    event.get("continuity_core_fingerprint"),
                    "continuity_core_fingerprint",
                )
                if expected_core_fp != str(core.get("continuity_core_fingerprint") or ""):
                    raise ControllerContinuityError(
                        "CAPSULE_STALE",
                        "reattach requires the exact current Continuity Core fingerprint",
                        retryable=True,
                    )
                reattach_id = _opaque(event.get("reattach_id"), "reattach_id")
                ack_id = _opaque(event.get("ack_id"), "ack_id")
                previous = self.orchestration_ledger.controller_reattach_receipt(reattach_id)
                expected_identity = {
                    "workspace_id": workspace_id,
                    "problem_id": problem_id,
                    "problem_revision": problem_revision,
                    "controller_endpoint_id": endpoint,
                    "owner_client_id": controller_identity["owner_client_id"],
                    "ack_id": ack_id,
                    "continuity_core_fingerprint": expected_core_fp,
                }
                if previous is not None and any(
                    previous.get(key) != value for key, value in expected_identity.items()
                ):
                    raise ControllerContinuityError(
                        "CONTROLLER_REATTACH_IDENTITY_CONFLICT",
                        "reattach_id was reused with a different exact request",
                        category="security",
                    )
                acked = self.orchestration_ledger.controller_ack_knowledge(
                    ack_id=ack_id,
                    workspace_id=workspace_id,
                    problem_id=problem_id,
                    problem_revision=problem_revision,
                    knowledge_revision=event.get("knowledge_revision"),
                    controller_endpoint_id=endpoint,
                )
                ack_record = acked["ack"]
                if ack_record["status"] not in {"CURRENT", "BEHIND", "MISSING"}:
                    raise ControllerContinuityError(
                        "CONTROLLER_REATTACH_ACK_UNSAFE",
                        "controller knowledge cannot be recovered safely for reattach",
                        details={
                            "ack_status": ack_record["status"],
                            "recovery": ack_record.get("recovery"),
                        },
                    )
                reattached = self.orchestration_ledger.controller_reattach_goal(
                    reattach_id=reattach_id,
                    workspace_id=workspace_id,
                    problem_id=problem_id,
                    problem_revision=problem_revision,
                    controller_endpoint_id=endpoint,
                    owner_client_id=controller_identity["owner_client_id"],
                    ack_id=ack_record["ack_id"],
                    ack_status=ack_record["status"],
                    continuity_core_fingerprint=expected_core_fp,
                    source_fingerprint=str(source.get("source_fingerprint") or ""),
                    runtime_behavior_fingerprint=runtime_fp,
                )
                auto_resumed: list[dict[str, Any]] = []
                for transfer in reattached.get("active_run_transfers") or []:
                    if not isinstance(transfer, dict) or not str(transfer.get("run_id") or ""):
                        continue
                    auto_resumed.append(
                        self._run_continuation_try_auto_resume(
                            run_id=str(transfer["run_id"]),
                            trigger="reattach",
                            marker=reattach_id,
                        )
                    )
                return {
                    "controller_reattach": reattached,
                    "knowledge_ack": acked,
                    "continuity_core": core,
                    "currentness": currentness,
                    "goal_controller_attachment_granted": True,
                    "write_authority_granted": False,
                    "acceptance_authority_granted": False,
                    "authority_granted": False,
                    "continuation_auto_resume": auto_resumed,
                }
            raise ControllerContinuityError(
                "CONTINUITY_ACTION_INVALID", f"unsupported continuity_action: {action}"
            )
        except ControllerContinuityError as exc:
            raise self._continuity_tool_failure(exc) from exc
