from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import sqlite3
from typing import Any

from .errors import ToolFailure
from .problem_lineage import PROBLEM_EVENT_SCHEMA_V11, PROBLEM_SCHEMA_VERSION


GOAL_PURSUIT_SCHEMA_VERSION = 1
GOAL_PURSUIT_MAX_CANDIDATES = 10
GOAL_PURSUIT_MAX_CANDIDATE_PAGE_SIZE = 50
GOAL_PURSUIT_CANDIDATE_CURSOR_SCHEMA_VERSION = 1
GOAL_PURSUIT_CANDIDATE_CURSOR_MAX_CHARS = 2048
GOAL_PURSUIT_MAX_ATTEMPTS = 50
GOAL_PURSUIT_MAX_CORRELATIONS = 50
GOAL_PURSUIT_LIVE_MAX_CHECKPOINTS = GOAL_PURSUIT_MAX_ATTEMPTS * 20
GOAL_PURSUIT_LIVE_MAX_PROOF_REFS = 300
_PROCESS_GOAL_CANDIDATE_CURSOR_SECRET = secrets.token_bytes(32)


class GoalPursuitError(ValueError):
    def __init__(self, code: str, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.details = dict(details or {})


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha(value: Any) -> str:
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _opaque(value: Any, name: str, *, required: bool = True, limit: int = 128) -> str:
    text = str(value or "").strip()
    if not text:
        if required:
            raise GoalPursuitError("GOAL_IDENTITY_REQUIRED", f"{name} is required")
        return ""
    if len(text) > limit or any(character.isspace() for character in text):
        raise GoalPursuitError("GOAL_IDENTITY_INVALID", f"{name} is invalid")
    return text


def _positive_revision(value: Any, name: str, *, required: bool = True) -> int | None:
    if value is None and not required:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise GoalPursuitError("GOAL_REVISION_INVALID", f"{name} must be a positive integer")
    return value


def _row_json(value: Any) -> dict[str, Any]:
    try:
        decoded = json.loads(str(value or "{}"))
    except (TypeError, json.JSONDecodeError):
        return {}
    return decoded if isinstance(decoded, dict) else {}


def _goal_candidate(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "problem_id": str(row["problem_id"]),
        "problem_revision": int(row["current_revision"]),
        "problem_state": str(row["resolution_state"]),
    }


def _candidate_page_limit(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise GoalPursuitError(
            "GOAL_CANDIDATE_LIMIT_INVALID",
            "candidate_limit must be an integer",
        )
    if value < 1 or value > GOAL_PURSUIT_MAX_CANDIDATE_PAGE_SIZE:
        raise GoalPursuitError(
            "GOAL_CANDIDATE_LIMIT_INVALID",
            f"candidate_limit must be between 1 and {GOAL_PURSUIT_MAX_CANDIDATE_PAGE_SIZE}",
        )
    return value


def _encode_goal_candidate_cursor(payload: dict[str, Any]) -> str:
    raw = _json(payload).encode("utf-8")
    signature = hmac.new(_PROCESS_GOAL_CANDIDATE_CURSOR_SECRET, raw, hashlib.sha256).digest()
    body = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    proof = base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")
    return f"{body}.{proof}"


def _decode_goal_candidate_cursor(token: Any) -> dict[str, Any]:
    text = str(token or "").strip()
    if (
        not text
        or len(text) > GOAL_PURSUIT_CANDIDATE_CURSOR_MAX_CHARS
        or text.count(".") != 1
        or any(character.isspace() for character in text)
    ):
        raise GoalPursuitError(
            "GOAL_CANDIDATE_CURSOR_INVALID",
            "candidate_cursor is invalid",
        )
    body, proof = text.split(".", 1)
    try:
        raw = base64.urlsafe_b64decode(body + "=" * (-len(body) % 4))
        signature = base64.urlsafe_b64decode(proof + "=" * (-len(proof) % 4))
        if (
            base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=") != body
            or base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=") != proof
        ):
            raise ValueError("non-canonical base64url encoding")
        expected = hmac.new(_PROCESS_GOAL_CANDIDATE_CURSOR_SECRET, raw, hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError("signature mismatch")
        payload = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GoalPursuitError(
            "GOAL_CANDIDATE_CURSOR_INVALID",
            "candidate_cursor is invalid",
        ) from exc
    if (
        not isinstance(payload, dict)
        or payload.get("schema_version") != GOAL_PURSUIT_CANDIDATE_CURSOR_SCHEMA_VERSION
        or payload.get("operation_kind") != "goal_candidate_page"
    ):
        raise GoalPursuitError(
            "GOAL_CANDIDATE_CURSOR_INVALID",
            "candidate_cursor is unsupported",
        )
    numeric_fields = ("candidate_count", "latest_problem_event_seq", "position", "page_limit")
    if any(isinstance(payload.get(name), bool) or not isinstance(payload.get(name), int) for name in numeric_fields):
        raise GoalPursuitError(
            "GOAL_CANDIDATE_CURSOR_INVALID",
            "candidate_cursor contains invalid pagination state",
        )
    after_problem_id = str(payload.get("after_problem_id") or "").strip()
    if (
        int(payload["candidate_count"]) < 2
        or int(payload["latest_problem_event_seq"]) < 1
        or int(payload["position"]) < 1
        or int(payload["position"]) >= int(payload["candidate_count"])
        or int(payload["page_limit"]) < 1
        or int(payload["page_limit"]) > GOAL_PURSUIT_MAX_CANDIDATE_PAGE_SIZE
        or not after_problem_id
        or len(after_problem_id) > 128
        or any(character.isspace() for character in after_problem_id)
    ):
        raise GoalPursuitError(
            "GOAL_CANDIDATE_CURSOR_INVALID",
            "candidate_cursor contains invalid pagination state",
        )
    return {
        "candidate_count": int(payload["candidate_count"]),
        "latest_problem_event_seq": int(payload["latest_problem_event_seq"]),
        "position": int(payload["position"]),
        "page_limit": int(payload["page_limit"]),
        "after_problem_id": after_problem_id,
    }


class GoalPursuitLedgerMixin:
    @staticmethod
    def _require_goal_schema(connection: sqlite3.Connection) -> None:
        version = int(connection.execute("PRAGMA user_version").fetchone()[0])
        if version != PROBLEM_SCHEMA_VERSION:
            raise GoalPursuitError(
                "GOAL_PRL_SCHEMA_INACTIVE",
                "Goal Pursuit requires the activated canonical Problem Revision Ledger",
                details={"required": PROBLEM_SCHEMA_VERSION, "observed": version},
            )

    @staticmethod
    def _goal_run_binding(connection: sqlite3.Connection, run_id: str) -> dict[str, Any] | None:
        rows = connection.execute(
            """SELECT DISTINCT problem_id,problem_revision
               FROM problem_events
               WHERE run_id=? AND link_status='EXACT' AND link_role='PRIMARY'
                 AND relation_type IN ('LINK','ENGINEERING_ATTEMPT_BOUND')
                 AND event_schema_version>=? AND problem_id IS NOT NULL AND problem_revision IS NOT NULL
               ORDER BY problem_id,problem_revision LIMIT 2""",
            (run_id, PROBLEM_EVENT_SCHEMA_V11),
        ).fetchall()
        if not rows:
            return None
        if len(rows) != 1:
            raise GoalPursuitError(
                "GOAL_IDENTITY_AMBIGUOUS",
                "RUN has more than one exact primary Problem identity",
                details={"run_id": run_id, "candidate_count": len(rows)},
            )
        return {
            "problem_id": str(rows[0]["problem_id"]),
            "problem_revision": int(rows[0]["problem_revision"]),
        }

    @staticmethod
    def _goal_candidate_snapshot(connection: sqlite3.Connection) -> dict[str, Any]:
        row = connection.execute(
            """SELECT COUNT(*) AS candidate_count,
                      COALESCE(MAX(latest_problem_event_seq),0) AS latest_problem_event_seq
               FROM problem_threads
               WHERE resolution_state NOT IN ('RESOLVED_CONFIRMED','ABANDONED')"""
        ).fetchone()
        candidate_count = int(row["candidate_count"] if row is not None else 0)
        latest_problem_event_seq = int(row["latest_problem_event_seq"] if row is not None else 0)
        material = {
            "candidate_count": candidate_count,
            "latest_problem_event_seq": latest_problem_event_seq,
        }
        return {**material, "snapshot_fingerprint": _sha(material)}

    def goal_pursuit_resolve_identity(
        self,
        *,
        problem_id: str = "",
        problem_revision: int | None = None,
        run_id: str = "",
        candidate_cursor: str = "",
        candidate_limit: int | None = None,
    ) -> dict[str, Any]:
        explicit_problem = _opaque(problem_id, "problem_id", required=False)
        explicit_revision = _positive_revision(problem_revision, "problem_revision", required=False)
        exact_run = _opaque(run_id, "run_id", required=False)
        page_cursor = str(candidate_cursor or "").strip()
        requested_page_limit = _candidate_page_limit(candidate_limit) if candidate_limit is not None else None
        if explicit_revision is not None and not explicit_problem:
            raise GoalPursuitError(
                "GOAL_IDENTITY_REQUIRED", "problem_revision cannot be supplied without problem_id"
            )
        if (page_cursor or requested_page_limit is not None) and (explicit_problem or exact_run):
            raise GoalPursuitError(
                "GOAL_CANDIDATE_PAGE_CONFLICT",
                "candidate pagination cannot be combined with an exact Problem or RUN identity",
            )
        with self._lock, self._connect() as connection:
            self._require_goal_schema(connection)
            run_binding = self._goal_run_binding(connection, exact_run) if exact_run else None
            if exact_run and run_binding is None:
                raise GoalPursuitError(
                    "GOAL_RUN_UNBOUND",
                    "explicit RUN has no exact primary Problem binding",
                    details={"run_id": exact_run},
                )
            explicit_row = None
            if explicit_problem:
                explicit_row = connection.execute(
                    "SELECT * FROM problem_threads WHERE problem_id=?", (explicit_problem,)
                ).fetchone()
                if explicit_row is None:
                    raise GoalPursuitError(
                        "GOAL_IDENTITY_NOT_FOUND", "explicit Problem identity was not found"
                    )
                current_revision = int(explicit_row["current_revision"])
                if explicit_revision is not None and explicit_revision != current_revision:
                    raise GoalPursuitError(
                        "GOAL_REVISION_STALE",
                        "explicit Problem Revision is not current",
                        details={
                            "problem_id": explicit_problem,
                            "expected_current_revision": current_revision,
                            "received_revision": explicit_revision,
                        },
                    )
                if run_binding and (
                    run_binding["problem_id"] != explicit_problem
                    or (
                        explicit_revision is not None
                        and run_binding["problem_revision"] != explicit_revision
                    )
                ):
                    raise GoalPursuitError(
                        "GOAL_IDENTITY_CONFLICT",
                        "explicit Goal identity conflicts with the exact RUN binding",
                        details={
                            "explicit_problem_id": explicit_problem,
                            "explicit_problem_revision": explicit_revision,
                            "run_id": exact_run,
                            "run_problem_id": run_binding["problem_id"],
                            "run_problem_revision": run_binding["problem_revision"],
                        },
                    )
                reason = "EXPLICIT_GOAL_IDENTITY"
                if run_binding:
                    reason = "EXPLICIT_GOAL_AND_RUN_BINDING"
                return {
                    "status": "EXACT",
                    "reason": reason,
                    "problem_id": explicit_problem,
                    "problem_revision": current_revision,
                    "run_id": exact_run or None,
                    "bound_problem_revision": run_binding["problem_revision"] if run_binding else None,
                    "revision_refreshed": bool(
                        run_binding and run_binding["problem_revision"] != current_revision
                    ),
                    "timestamp_selection_used": False,
                }
            if run_binding:
                thread = connection.execute(
                    "SELECT * FROM problem_threads WHERE problem_id=?", (run_binding["problem_id"],)
                ).fetchone()
                if thread is None:
                    raise GoalPursuitError(
                        "GOAL_IDENTITY_NOT_FOUND", "RUN binding references a missing canonical Problem"
                    )
                current_revision = int(thread["current_revision"])
                return {
                    "status": "EXACT",
                    "reason": "EXACT_RUN_BINDING",
                    "problem_id": str(thread["problem_id"]),
                    "problem_revision": current_revision,
                    "run_id": exact_run,
                    "bound_problem_revision": run_binding["problem_revision"],
                    "revision_refreshed": run_binding["problem_revision"] != current_revision,
                    "timestamp_selection_used": False,
                }
            snapshot = self._goal_candidate_snapshot(connection)
            candidate_count = int(snapshot["candidate_count"])
            latest_problem_event_seq = int(snapshot["latest_problem_event_seq"])
            position = 0
            after_problem_id = ""
            page_limit = requested_page_limit or GOAL_PURSUIT_MAX_CANDIDATES
            if page_cursor:
                cursor = _decode_goal_candidate_cursor(page_cursor)
                if (
                    cursor["candidate_count"] != candidate_count
                    or cursor["latest_problem_event_seq"] != latest_problem_event_seq
                ):
                    raise GoalPursuitError(
                        "GOAL_CANDIDATE_SNAPSHOT_CHANGED",
                        "unresolved Goal backlog changed after the candidate page cursor was issued",
                        details={
                            "candidate_count": candidate_count,
                            "candidate_snapshot_fingerprint": snapshot["snapshot_fingerprint"],
                            "timestamp_selection_used": False,
                        },
                    )
                if requested_page_limit is not None and requested_page_limit != cursor["page_limit"]:
                    raise GoalPursuitError(
                        "GOAL_CANDIDATE_CURSOR_SCOPE_MISMATCH",
                        "candidate_limit does not match the issued candidate page cursor",
                    )
                position = int(cursor["position"])
                after_problem_id = str(cursor["after_problem_id"])
                page_limit = int(cursor["page_limit"])
            if candidate_count == 0:
                raise GoalPursuitError(
                    "GOAL_IDENTITY_NOT_FOUND", "no unresolved Goal exists in the workspace"
                )
            if page_cursor and candidate_count <= 1:
                raise GoalPursuitError(
                    "GOAL_CANDIDATE_CURSOR_INVALID",
                    "candidate_cursor no longer refers to an ambiguous Goal backlog",
                )
            rows = connection.execute(
                """SELECT problem_id,current_revision,resolution_state
                   FROM problem_threads
                   WHERE resolution_state NOT IN ('RESOLVED_CONFIRMED','ABANDONED') AND problem_id>?
                   ORDER BY problem_id LIMIT ?""",
                (after_problem_id, page_limit),
            ).fetchall()
            if candidate_count != 1:
                candidates = [_goal_candidate(row) for row in rows]
                if not candidates or position + len(candidates) > candidate_count:
                    raise GoalPursuitError(
                        "GOAL_CANDIDATE_CURSOR_INVALID",
                        "candidate_cursor does not identify a valid page in the unresolved Goal backlog",
                    )
                next_position = position + len(candidates)
                has_more = next_position < candidate_count
                next_candidate_cursor = ""
                if has_more:
                    next_candidate_cursor = _encode_goal_candidate_cursor(
                        {
                            "schema_version": GOAL_PURSUIT_CANDIDATE_CURSOR_SCHEMA_VERSION,
                            "operation_kind": "goal_candidate_page",
                            "candidate_count": candidate_count,
                            "latest_problem_event_seq": latest_problem_event_seq,
                            "position": next_position,
                            "page_limit": page_limit,
                            "after_problem_id": str(rows[-1]["problem_id"]),
                        }
                    )
                raise GoalPursuitError(
                    "GOAL_IDENTITY_AMBIGUOUS",
                    "more than one unresolved Goal exists; select an exact Problem identity",
                    details={
                        "candidate_count": candidate_count,
                        "candidates": candidates,
                        "candidates_truncated": len(candidates) != candidate_count,
                        "candidate_page_position": position,
                        "candidate_page_limit": page_limit,
                        "candidate_page_has_more": has_more,
                        "candidate_snapshot_fingerprint": snapshot["snapshot_fingerprint"],
                        "next_candidate_cursor": next_candidate_cursor,
                        "timestamp_selection_used": False,
                    },
                )
            return {
                "status": "EXACT",
                "reason": "ONLY_UNRESOLVED_GOAL",
                "problem_id": str(rows[0]["problem_id"]),
                "problem_revision": int(rows[0]["current_revision"]),
                "run_id": None,
                "bound_problem_revision": None,
                "revision_refreshed": False,
                "timestamp_selection_used": False,
            }

    @staticmethod
    def _goal_checkpoint_claim(
        checkpoint: sqlite3.Row,
        *,
        problem_id: str,
        problem_revision: int,
        run_id: str,
        wave_id: str,
    ) -> dict[str, Any] | None:
        metadata = _row_json(checkpoint["metadata_json"])
        claim = metadata.get("problem_outcome_claim")
        claim_sha = str(metadata.get("problem_outcome_claim_sha256") or "")
        if (
            not isinstance(claim, dict)
            or claim_sha != _sha(claim)
            or claim.get("problem_id") != problem_id
            or claim.get("problem_revision") != problem_revision
            or claim.get("run_id") != run_id
            or claim.get("wave_id") != wave_id
        ):
            return None
        return claim

    @staticmethod
    def _goal_criterion_coverage(
        *,
        criteria: list[dict[str, Any]],
        attempts: list[dict[str, Any]],
        proof_rows: dict[tuple[str, str], dict[str, sqlite3.Row]],
        claims: dict[tuple[str, str, str], dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        coverage: dict[str, dict[str, Any]] = {
            str(item["criterion_id"]): {
                "status": "UNRESOLVED",
                "proof_refs": [],
                "attempt_refs": [],
            }
            for item in criteria
        }
        for attempt in attempts:
            run_id = str(attempt["run_id"])
            wave_id = str(attempt["wave_id"])
            checkpoint_id = str(attempt.get("checkpoint_id") or "")
            claim = claims.get((run_id, wave_id, checkpoint_id))
            if claim is None:
                continue
            evidence = claim.get("evidence") if isinstance(claim.get("evidence"), dict) else {}
            if evidence.get("kind") == "proof_coverage":
                manifest = evidence.get("coverage_manifest")
                if not isinstance(manifest, dict) or set(manifest) != set(coverage):
                    continue
                exact_proofs = proof_rows.get((run_id, wave_id), {})
                for criterion_id, references in manifest.items():
                    if not isinstance(references, list) or not references:
                        continue
                    proof_ids = [str(item) for item in references]
                    if any(proof_id not in exact_proofs for proof_id in proof_ids):
                        continue
                    entry = coverage[criterion_id]
                    entry["status"] = "PROVEN"
                    entry["proof_refs"] = sorted(set(entry["proof_refs"]) | set(proof_ids))[:32]
                    entry["attempt_refs"] = sorted(
                        set(entry["attempt_refs"]) | {f"{run_id}:{wave_id}:{checkpoint_id}"}
                    )[:16]
            elif evidence.get("kind") == "non_code_dispositions":
                dispositions = evidence.get("criterion_dispositions")
                if not isinstance(dispositions, dict) or set(dispositions) != set(coverage):
                    continue
                for criterion_id, disposition in dispositions.items():
                    if disposition != "SATISFIED_NON_CODE":
                        continue
                    entry = coverage[criterion_id]
                    entry["status"] = "SATISFIED_NON_CODE"
                    entry["attempt_refs"] = sorted(
                        set(entry["attempt_refs"]) | {f"{run_id}:{wave_id}:{checkpoint_id}"}
                    )[:16]
        return coverage

    def goal_pursuit_live_summary(self, *, run_id: str) -> dict[str, Any]:
        """Project exact Goal truth for the high-frequency live-control path.

        The operator heartbeat may not select a workspace-global Goal or run
        the full per-attempt projector. This summary therefore requires one
        exact primary Problem Revision binding for the supplied RUN and joins
        accepted checkpoint/proof facts through bounded batch queries.
        """
        exact_run = _opaque(run_id, "run_id")
        with self._lock, self._connect() as connection:
            self._require_goal_schema(connection)
            binding = self._goal_run_binding(connection, exact_run)
            if binding is None:
                raise GoalPursuitError(
                    "GOAL_RUN_UNBOUND",
                    "explicit RUN has no exact primary Problem binding",
                    details={"run_id": exact_run},
                )
            problem = str(binding["problem_id"])
            revision_number = int(binding["problem_revision"])
            goal = connection.execute(
                """SELECT t.current_revision,t.resolution_state,t.latest_problem_event_seq,
                          r.contract_fingerprint,r.criteria_fingerprint,r.criteria_count,
                          r.typed_contract_capsule
                   FROM problem_threads AS t
                   JOIN problem_revisions AS r
                     ON r.problem_id=t.problem_id AND r.revision=?
                   WHERE t.problem_id=?""",
                (revision_number, problem),
            ).fetchone()
            if goal is None:
                raise GoalPursuitError(
                    "GOAL_IDENTITY_NOT_FOUND",
                    "exact RUN Problem Revision was not found",
                    details={"run_id": exact_run, "problem_id": problem},
                )
            if int(goal["current_revision"]) != revision_number:
                raise GoalPursuitError(
                    "GOAL_REVISION_STALE",
                    "live Goal projection requires the RUN to bind the current Problem Revision",
                    details={
                        "run_id": exact_run,
                        "problem_id": problem,
                        "bound_problem_revision": revision_number,
                        "current_problem_revision": int(goal["current_revision"]),
                    },
                )
            try:
                capsule = json.loads(str(goal["typed_contract_capsule"] or "{}"))
            except (TypeError, json.JSONDecodeError):
                capsule = {}
            criteria = capsule.get("acceptance_criteria") if isinstance(capsule, dict) else None
            if not isinstance(criteria, list) or not criteria:
                raise GoalPursuitError(
                    "GOAL_CONTRACT_INVALID", "current Problem Revision contract capsule is invalid"
                )
            criterion_by_id = {
                str(item["criterion_id"]): str(item.get("summary") or "")
                for item in criteria
                if isinstance(item, dict) and str(item.get("criterion_id") or "")
            }
            if len(criterion_by_id) != len(criteria):
                raise GoalPursuitError(
                    "GOAL_CONTRACT_INVALID", "current Problem Revision criteria are invalid"
                )

            pair_rows = connection.execute(
                """SELECT DISTINCT run_id,wave_id
                   FROM problem_events
                   WHERE problem_id=? AND problem_revision=? AND link_status='EXACT'
                     AND link_role='PRIMARY'
                     AND relation_type IN ('LINK','ENGINEERING_ATTEMPT_BOUND')
                     AND event_schema_version>=? AND run_id<>'' AND wave_id<>''
                   ORDER BY run_id,wave_id LIMIT ?""",
                (
                    problem,
                    revision_number,
                    PROBLEM_EVENT_SCHEMA_V11,
                    GOAL_PURSUIT_MAX_ATTEMPTS + 1,
                ),
            ).fetchall()
            pair_window_truncated = len(pair_rows) > GOAL_PURSUIT_MAX_ATTEMPTS
            pairs = [
                (str(row["run_id"]), str(row["wave_id"]))
                for row in pair_rows[:GOAL_PURSUIT_MAX_ATTEMPTS]
            ]
            checkpoint_rows: list[sqlite3.Row] = []
            checkpoint_window_truncated = False
            if pairs and not pair_window_truncated:
                values = ",".join("(?,?)" for _item in pairs)
                parameters: list[Any] = [value for pair in pairs for value in pair]
                parameters.append(GOAL_PURSUIT_LIVE_MAX_CHECKPOINTS + 1)
                checkpoint_rows = connection.execute(
                    f"""WITH bound(run_id,wave_id) AS (VALUES {values})
                        SELECT c.*,r.status AS run_status,w.status AS wave_status
                        FROM bound AS b
                        JOIN runs AS r ON r.run_id=b.run_id
                        JOIN waves AS w ON w.run_id=b.run_id AND w.wave_id=b.wave_id
                        JOIN checkpoints AS c
                          ON c.run_id=b.run_id AND c.wave_id=b.wave_id AND c.status='accepted'
                        ORDER BY b.run_id,b.wave_id,c.created_at,c.checkpoint_id
                        LIMIT ?""",
                    parameters,
                ).fetchall()
                checkpoint_window_truncated = (
                    len(checkpoint_rows) > GOAL_PURSUIT_LIVE_MAX_CHECKPOINTS
                )
                checkpoint_rows = checkpoint_rows[:GOAL_PURSUIT_LIVE_MAX_CHECKPOINTS]

            coverage = {
                criterion_id: {
                    "status": "UNRESOLVED",
                    "proof_refs": [],
                    "attempt_refs": [],
                }
                for criterion_id in criterion_by_id
            }
            valid_claims: list[tuple[sqlite3.Row, dict[str, Any]]] = []
            accepted_exact_attempt = False
            requested_proofs: set[tuple[str, str, str]] = set()
            proof_reference_window_truncated = False
            if not pair_window_truncated and not checkpoint_window_truncated:
                for checkpoint in checkpoint_rows:
                    claim = self._goal_checkpoint_claim(
                        checkpoint,
                        problem_id=problem,
                        problem_revision=revision_number,
                        run_id=str(checkpoint["run_id"]),
                        wave_id=str(checkpoint["wave_id"]),
                    )
                    if claim is None:
                        continue
                    valid_claims.append((checkpoint, claim))
                    accepted_exact_attempt = accepted_exact_attempt or (
                        str(checkpoint["run_status"]) == "accepted"
                        and str(checkpoint["wave_status"]) == "accepted"
                    )
                    evidence = claim.get("evidence") if isinstance(claim.get("evidence"), dict) else {}
                    if evidence.get("kind") != "proof_coverage":
                        continue
                    manifest = evidence.get("coverage_manifest")
                    if not isinstance(manifest, dict) or set(manifest) != set(coverage):
                        continue
                    for references in manifest.values():
                        if not isinstance(references, list) or not references:
                            continue
                        for proof_id in references:
                            requested_proofs.add(
                                (
                                    str(checkpoint["run_id"]),
                                    str(checkpoint["wave_id"]),
                                    str(proof_id),
                                )
                            )
                proof_reference_window_truncated = (
                    len(requested_proofs) > GOAL_PURSUIT_LIVE_MAX_PROOF_REFS
                )

            verified_proofs: set[tuple[str, str, str]] = set()
            if requested_proofs and not proof_reference_window_truncated:
                requested = sorted(requested_proofs)
                values = ",".join("(?,?,?)" for _item in requested)
                parameters = [value for proof in requested for value in proof]
                proof_rows = connection.execute(
                    f"""WITH requested(run_id,wave_id,proof_id) AS (VALUES {values})
                        SELECT p.run_id,p.wave_id,p.proof_id
                        FROM requested AS q
                        JOIN proofs AS p
                          ON p.run_id=q.run_id AND p.wave_id=q.wave_id AND p.proof_id=q.proof_id
                        WHERE p.status='passed'
                        ORDER BY p.run_id,p.wave_id,p.proof_id""",
                    parameters,
                ).fetchall()
                verified_proofs = {
                    (str(row["run_id"]), str(row["wave_id"]), str(row["proof_id"]))
                    for row in proof_rows
                }

            fact_window_reason = None
            if pair_window_truncated:
                fact_window_reason = "attempt_pair_window_truncated"
            elif checkpoint_window_truncated:
                fact_window_reason = "accepted_checkpoint_window_truncated"
            elif proof_reference_window_truncated:
                fact_window_reason = "proof_reference_window_truncated"
            if fact_window_reason is None:
                for checkpoint, claim in valid_claims:
                    evidence = claim.get("evidence") if isinstance(claim.get("evidence"), dict) else {}
                    attempt_ref = (
                        f"{checkpoint['run_id']}:{checkpoint['wave_id']}:{checkpoint['checkpoint_id']}"
                    )
                    if evidence.get("kind") == "proof_coverage":
                        manifest = evidence.get("coverage_manifest")
                        if not isinstance(manifest, dict) or set(manifest) != set(coverage):
                            continue
                        for criterion_id, references in manifest.items():
                            if not isinstance(references, list) or not references:
                                continue
                            exact_refs = {
                                (str(checkpoint["run_id"]), str(checkpoint["wave_id"]), str(proof_id))
                                for proof_id in references
                            }
                            if not exact_refs.issubset(verified_proofs):
                                continue
                            entry = coverage[str(criterion_id)]
                            entry["status"] = "PROVEN"
                            entry["proof_refs"] = sorted(
                                set(entry["proof_refs"]) | {proof_id for _run, _wave, proof_id in exact_refs}
                            )[:32]
                            entry["attempt_refs"] = sorted(
                                set(entry["attempt_refs"]) | {attempt_ref}
                            )[:16]
                    elif evidence.get("kind") == "non_code_dispositions":
                        dispositions = evidence.get("criterion_dispositions")
                        if not isinstance(dispositions, dict) or set(dispositions) != set(coverage):
                            continue
                        for criterion_id, disposition in dispositions.items():
                            if disposition != "SATISFIED_NON_CODE":
                                continue
                            entry = coverage[str(criterion_id)]
                            entry["status"] = "SATISFIED_NON_CODE"
                            entry["attempt_refs"] = sorted(
                                set(entry["attempt_refs"]) | {attempt_ref}
                            )[:16]

            problem_state = str(goal["resolution_state"])
            legitimate_stop = False
            stop_reason = "NONE"
            proven: list[str] = []
            unresolved: list[str] = []
            if fact_window_reason is None:
                proven = [
                    criterion_id
                    for criterion_id, value in coverage.items()
                    if value["status"] in {"PROVEN", "SATISFIED_NON_CODE"}
                ]
                unresolved = [
                    criterion_id for criterion_id in criterion_by_id if criterion_id not in proven
                ]
            if problem_state == "RESOLVED_CONFIRMED":
                resolution_status = "RESOLVED_CONFIRMED"
                next_action = "NONE"
                legitimate_stop, stop_reason = True, "RESOLVED"
            elif problem_state == "ABANDONED":
                resolution_status = "ABANDONED"
                next_action = "NONE"
                legitimate_stop, stop_reason = True, "ABANDONED"
            elif problem_state == "BLOCKED":
                resolution_status = "BLOCKED"
                next_action = "WAIT_FOR_EXPLICIT_UNBLOCK"
                legitimate_stop, stop_reason = True, "BLOCKED"
            elif problem_state == "PROVISIONALLY_RESOLVED":
                resolution_status = "PROVISIONAL"
                next_action = "OBTAIN_INDEPENDENT_OUTCOME"
            elif fact_window_reason is not None:
                resolution_status = "IN_PROGRESS"
                next_action = "UNAVAILABLE"
            elif not unresolved and accepted_exact_attempt:
                resolution_status = "ENGINEERING_COMPLETE_AWAITING_RECONCILIATION"
                next_action = "RECONCILE_PROVISIONAL_RESOLUTION"
            else:
                resolution_status = "IN_PROGRESS"
                next_action = "SATISFY_UNRESOLVED_CRITERION"
            next_gap_id = unresolved[0] if fact_window_reason is None and unresolved else None
            completion = {
                "status": "unavailable" if fact_window_reason else "observed",
                "criteria_total": len(criterion_by_id),
                "criteria_proven": None if fact_window_reason else len(proven),
                "criteria_unresolved": None if fact_window_reason else len(unresolved),
                "exact_coverage_status": (
                    "UNAVAILABLE"
                    if fact_window_reason
                    else "COMPLETE"
                    if not unresolved
                    else "PARTIAL"
                    if proven
                    else "NONE"
                ),
                "missing_reason": fact_window_reason,
            }
            return {
                "schema_version": GOAL_PURSUIT_SCHEMA_VERSION,
                "kind": "bounded_live_goal_pursuit_summary",
                "identity": {
                    "problem_id": problem,
                    "problem_revision": revision_number,
                    "contract_fingerprint": str(goal["contract_fingerprint"]),
                    "criteria_fingerprint": str(goal["criteria_fingerprint"]),
                },
                "problem_state": problem_state,
                "resolution_status": resolution_status,
                "completion": completion,
                "next_critical_gap": (
                    criterion_by_id.get(next_gap_id) if next_gap_id else None
                ),
                "next_critical_gap_id": next_gap_id,
                "next_action": next_action,
                "decision_state_provenance": "CANONICAL_PRL_EOCL_PROOF_JOIN_BOUNDED",
                "stop": {"legitimate_stop": legitimate_stop, "reason": stop_reason},
                "fact_window": {
                    "attempt_pair_limit": GOAL_PURSUIT_MAX_ATTEMPTS,
                    "attempt_pair_count": len(pairs),
                    "accepted_checkpoint_limit": GOAL_PURSUIT_LIVE_MAX_CHECKPOINTS,
                    "accepted_checkpoint_count": len(checkpoint_rows),
                    "proof_reference_limit": GOAL_PURSUIT_LIVE_MAX_PROOF_REFS,
                    "proof_reference_count": len(requested_proofs),
                    "truncated": fact_window_reason is not None,
                    "missing_reason": fact_window_reason,
                },
                "derived_projection_only": True,
                "authority": {
                    "mutation_authority_granted": False,
                    "acceptance_authority_granted": False,
                    "problem_revision_authority_granted": False,
                },
                "timestamp_selection_used": False,
            }

    def goal_pursuit_projection(
        self,
        *,
        problem_id: str,
        problem_revision: int,
    ) -> dict[str, Any]:
        problem = _opaque(problem_id, "problem_id")
        revision_number = int(_positive_revision(problem_revision, "problem_revision") or 0)
        with self._lock, self._connect() as connection:
            self._require_goal_schema(connection)
            thread = connection.execute(
                "SELECT * FROM problem_threads WHERE problem_id=?", (problem,)
            ).fetchone()
            revision = connection.execute(
                "SELECT * FROM problem_revisions WHERE problem_id=? AND revision=?",
                (problem, revision_number),
            ).fetchone()
            if (
                thread is None
                or revision is None
                or int(thread["current_revision"]) != revision_number
            ):
                raise GoalPursuitError(
                    "GOAL_REVISION_STALE", "Goal projection requires the exact current Problem Revision"
                )
            try:
                capsule = json.loads(str(revision["typed_contract_capsule"] or "{}"))
            except (TypeError, json.JSONDecodeError):
                capsule = {}
            criteria = capsule.get("acceptance_criteria") if isinstance(capsule, dict) else None
            if not isinstance(criteria, list) or not criteria:
                raise GoalPursuitError(
                    "GOAL_CONTRACT_INVALID", "current Problem Revision contract capsule is invalid"
                )
            bindings = connection.execute(
                """SELECT seq,run_id,wave_id,turn_id,trace_id,relation_type,link_role
                   FROM problem_events
                   WHERE problem_id=? AND problem_revision=? AND link_status='EXACT'
                     AND event_schema_version>=?
                   ORDER BY seq LIMIT 500""",
                (problem, revision_number, PROBLEM_EVENT_SCHEMA_V11),
            ).fetchall()
            run_wave_pairs = sorted(
                {
                    (str(row["run_id"]), str(row["wave_id"]))
                    for row in bindings
                    if str(row["run_id"] or "")
                    and str(row["wave_id"] or "")
                    and str(row["link_role"] or "") == "PRIMARY"
                    and str(row["relation_type"] or "") in {"LINK", "ENGINEERING_ATTEMPT_BOUND"}
                }
            )[:GOAL_PURSUIT_MAX_ATTEMPTS]
            attempts: list[dict[str, Any]] = []
            proof_rows: dict[tuple[str, str], dict[str, sqlite3.Row]] = {}
            claims: dict[tuple[str, str, str], dict[str, Any]] = {}
            for run_id, wave_id in run_wave_pairs:
                run = connection.execute(
                    "SELECT status FROM runs WHERE run_id=?", (run_id,)
                ).fetchone()
                wave = connection.execute(
                    "SELECT status,execution_mode FROM waves WHERE run_id=? AND wave_id=?",
                    (run_id, wave_id),
                ).fetchone()
                if run is None or wave is None:
                    continue
                proofs = connection.execute(
                    """SELECT * FROM proofs
                       WHERE run_id=? AND wave_id=? AND status='passed'
                       ORDER BY proof_id LIMIT 200""",
                    (run_id, wave_id),
                ).fetchall()
                proof_rows[(run_id, wave_id)] = {str(row["proof_id"]): row for row in proofs}
                checkpoints = connection.execute(
                    """SELECT * FROM checkpoints
                       WHERE run_id=? AND wave_id=? AND status='accepted'
                       ORDER BY created_at,checkpoint_id LIMIT 20""",
                    (run_id, wave_id),
                ).fetchall()
                if checkpoints:
                    for checkpoint in checkpoints:
                        checkpoint_id = str(checkpoint["checkpoint_id"])
                        claim = self._goal_checkpoint_claim(
                            checkpoint,
                            problem_id=problem,
                            problem_revision=revision_number,
                            run_id=run_id,
                            wave_id=wave_id,
                        )
                        if claim is not None:
                            claims[(run_id, wave_id, checkpoint_id)] = claim
                        attempts.append(
                            {
                                "run_id": run_id,
                                "wave_id": wave_id,
                                "run_status": str(run["status"]),
                                "wave_status": str(wave["status"]),
                                "execution_mode": str(wave["execution_mode"]),
                                "checkpoint_id": checkpoint_id,
                                "checkpoint_status": str(checkpoint["status"]),
                                "exact_problem_claim": claim is not None,
                            }
                        )
                else:
                    attempts.append(
                        {
                            "run_id": run_id,
                            "wave_id": wave_id,
                            "run_status": str(run["status"]),
                            "wave_status": str(wave["status"]),
                            "execution_mode": str(wave["execution_mode"]),
                            "checkpoint_id": None,
                            "checkpoint_status": None,
                            "exact_problem_claim": False,
                        }
                    )
            attempts = attempts[:GOAL_PURSUIT_MAX_ATTEMPTS]
            coverage = self._goal_criterion_coverage(
                criteria=criteria,
                attempts=attempts,
                proof_rows=proof_rows,
                claims=claims,
            )
            criterion_by_id = {
                str(item["criterion_id"]): str(item.get("summary") or "")
                for item in criteria
                if isinstance(item, dict) and str(item.get("criterion_id") or "")
            }
            proven = [
                criterion_id
                for criterion_id, value in coverage.items()
                if value["status"] in {"PROVEN", "SATISFIED_NON_CODE"}
            ]
            unresolved = [criterion_id for criterion_id in criterion_by_id if criterion_id not in proven]
            accepted_exact_attempt = any(
                attempt["run_status"] == "accepted"
                and attempt["wave_status"] == "accepted"
                and attempt["checkpoint_status"] == "accepted"
                and attempt["exact_problem_claim"]
                for attempt in attempts
            )
            problem_state = str(thread["resolution_state"])
            legitimate_stop = False
            stop_reason = "NONE"
            if problem_state == "RESOLVED_CONFIRMED":
                resolution_status = "RESOLVED_CONFIRMED"
                next_action = "NONE"
                legitimate_stop, stop_reason = True, "RESOLVED"
            elif problem_state == "ABANDONED":
                resolution_status = "ABANDONED"
                next_action = "NONE"
                legitimate_stop, stop_reason = True, "ABANDONED"
            elif problem_state == "BLOCKED":
                resolution_status = "BLOCKED"
                next_action = "WAIT_FOR_EXPLICIT_UNBLOCK"
                legitimate_stop, stop_reason = True, "BLOCKED"
            elif problem_state == "PROVISIONALLY_RESOLVED":
                resolution_status = "PROVISIONAL"
                next_action = "OBTAIN_INDEPENDENT_OUTCOME"
            elif not unresolved and accepted_exact_attempt:
                resolution_status = "ENGINEERING_COMPLETE_AWAITING_RECONCILIATION"
                next_action = "RECONCILE_PROVISIONAL_RESOLUTION"
            else:
                resolution_status = "IN_PROGRESS"
                next_action = "SATISFY_UNRESOLVED_CRITERION"
            next_gap_id = unresolved[0] if unresolved else None
            correlations = [
                {
                    "seq": int(row["seq"]),
                    "run_id": str(row["run_id"] or "") or None,
                    "wave_id": str(row["wave_id"] or "") or None,
                    "turn_id": str(row["turn_id"] or "") or None,
                    "trace_id": str(row["trace_id"] or "") or None,
                    "relation": str(row["relation_type"]),
                    "role": str(row["link_role"]),
                }
                for row in bindings
                if any(str(row[name] or "") for name in ("run_id", "turn_id", "trace_id"))
            ][:GOAL_PURSUIT_MAX_CORRELATIONS]
            knowledge_revision = 0
            knowledge_checkpoint = None
            table = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='controller_knowledge_checkpoints'"
            ).fetchone()
            if table is not None:
                knowledge_checkpoint = connection.execute(
                    """SELECT * FROM controller_knowledge_checkpoints
                       WHERE problem_id=? ORDER BY knowledge_revision DESC LIMIT 1""",
                    (problem,),
                ).fetchone()
                if knowledge_checkpoint is not None:
                    knowledge_revision = int(knowledge_checkpoint["knowledge_revision"])
            return {
                "schema_version": GOAL_PURSUIT_SCHEMA_VERSION,
                "kind": "derived_goal_pursuit_projection",
                "identity": {
                    "problem_id": problem,
                    "problem_revision": revision_number,
                    "contract_fingerprint": str(revision["contract_fingerprint"]),
                    "criteria_fingerprint": str(revision["criteria_fingerprint"]),
                },
                "problem_state": problem_state,
                "resolution_status": resolution_status,
                "completion": {
                    "criteria_total": len(criterion_by_id),
                    "criteria_proven": len(proven),
                    "criteria_unresolved": len(unresolved),
                    "exact_coverage_status": "COMPLETE" if not unresolved else "PARTIAL" if proven else "NONE",
                },
                "criterion_coverage": coverage,
                "next_critical_gap": criterion_by_id.get(next_gap_id) if next_gap_id else None,
                "next_critical_gap_id": next_gap_id,
                "next_action": next_action,
                "decision_state_provenance": "CANONICAL_PRL_EOCL_PROOF_JOIN",
                "knowledge_revision": knowledge_revision,
                "controller_recovery_required": knowledge_checkpoint is None,
                "execution_attempts": attempts,
                "correlation_bindings": correlations,
                "stop": {"legitimate_stop": legitimate_stop, "reason": stop_reason},
                "derived_projection_only": True,
                "authority": {
                    "mutation_authority_granted": False,
                    "acceptance_authority_granted": False,
                    "problem_revision_authority_granted": False,
                },
                "timestamp_selection_used": False,
            }


class GoalPursuitControlMixin:
    def _goal_control(self, args: dict[str, Any]) -> dict[str, Any]:
        action = str(args.get("goal_action") or "get").strip().lower()
        if action not in {"get", "resolve"}:
            raise ToolFailure(
                "GOAL_ACTION_INVALID", f"unsupported goal_action: {action}", category="validation"
            )
        event = args.get("goal_event")
        if event is None:
            event = {}
        if not isinstance(event, dict):
            raise ToolFailure("GOAL_EVENT_INVALID", "goal_event must be an object", category="validation")
        try:
            identity = self.orchestration_ledger.goal_pursuit_resolve_identity(
                problem_id=str(event.get("problem_id") or ""),
                problem_revision=event.get("problem_revision"),
                run_id=str(event.get("run_id") or ""),
                candidate_cursor=str(event.get("candidate_cursor") or ""),
                candidate_limit=event.get("candidate_limit"),
            )
            projection = self.orchestration_ledger.goal_pursuit_projection(
                problem_id=str(identity["problem_id"]),
                problem_revision=int(identity["problem_revision"]),
            )
            return {
                "goal_identity": identity,
                "goal_pursuit": projection,
                "authority_granted": False,
            }
        except GoalPursuitError as exc:
            raise ToolFailure(
                exc.code,
                str(exc),
                category="validation",
                retryable=False,
                details=exc.details,
            ) from exc
