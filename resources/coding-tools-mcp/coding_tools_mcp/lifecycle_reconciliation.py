"""Bounded, guarded lifecycle maintenance for terminal-parent lane residue."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from .ledger_event_chain import append_hash_chained_event


_LIVE_LANE_LIFECYCLES = frozenset({"starting", "active", "waiting", "idle"})
_TERMINAL_PARENT_STATUSES = frozenset({"accepted", "blocked", "aborted", "stale", "completed", "failed"})


class LifecycleReconciliationError(RuntimeError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _bounded_text(value: Any, limit: int) -> str:
    text = str(value or "")
    return text if len(text) <= limit else text[:limit] + "..."


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def logical_ledger_sha256(connection: Any) -> str:
    """Hash the committed logical database without exposing any row contents."""
    digest = hashlib.sha256()
    for statement in connection.iterdump():
        digest.update(statement.encode("utf-8", errors="surrogatepass"))
        digest.update(b"\n")
    return digest.hexdigest()


class LifecycleReconciliationLedgerMixin:
    """Official, exact-ID reconciliation that preserves canonical evidence."""

    def reconcile_exact_stale_run(
        self,
        *,
        run_id: str,
        expected_logical_sha256: str,
        expected_run_status: str,
        expected_latest_activity_at: str,
        expected_run_last_event_seq: int,
        expected_run_last_event_hash: str,
        observed_at_unix_seconds: float,
        stale_after_seconds: float,
        authority: str,
        reason: str = "inactivity_timeout",
    ) -> dict[str, Any]:
        """Terminalize one exact inactive run after all current guards agree.

        This is deliberately distinct from the historical bulk
        ``reconcile_stale_runs`` helper.  It never expires leases, never selects
        more than the supplied opaque ID, and compares the caller's immutable
        snapshot identity plus the target's exact activity/event guards in the
        same immediate transaction before writing any lifecycle evidence.
        """
        identifier = _bounded_text(run_id, 256).strip()
        expected_logical = _bounded_text(expected_logical_sha256, 64).strip().lower()
        expected_status = _bounded_text(expected_run_status, 64).strip().lower()
        expected_activity = _bounded_text(expected_latest_activity_at, 64).strip()
        expected_hash = _bounded_text(expected_run_last_event_hash, 64).strip().lower()
        operator = _bounded_text(authority, 128).strip()
        bounded_reason = _bounded_text(reason, 256).strip()
        try:
            observed_at = float(observed_at_unix_seconds)
            stale_after = max(60.0, float(stale_after_seconds))
        except (TypeError, ValueError) as exc:
            raise LifecycleReconciliationError("exact stale-run reconciliation requires numeric observation and threshold guards") from exc
        if (
            not identifier
            or not expected_activity
            or not operator
            or not bounded_reason
            or expected_status not in {"active", "stale"}
            or observed_at < 0
            or expected_run_last_event_seq < 0
        ):
            raise LifecycleReconciliationError("exact stale-run reconciliation requires complete exact guards")
        if len(expected_logical) != 64 or any(char not in "0123456789abcdef" for char in expected_logical):
            raise LifecycleReconciliationError("expected logical ledger SHA-256 is invalid")
        if expected_hash and (len(expected_hash) != 64 or any(char not in "0123456789abcdef" for char in expected_hash)):
            raise LifecycleReconciliationError("expected run event guard is invalid")

        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            if logical_ledger_sha256(connection) != expected_logical:
                connection.rollback()
                raise LifecycleReconciliationError("logical ledger snapshot changed before exact stale-run reconciliation")
            run = connection.execute("SELECT * FROM runs WHERE run_id=?", (identifier,)).fetchone()
            if run is None:
                connection.rollback()
                raise LifecycleReconciliationError("stale-run target was not found")
            last = connection.execute(
                "SELECT seq,event_hash,event_type,state_after,event_time FROM events WHERE run_id=? ORDER BY seq DESC LIMIT 1",
                (identifier,),
            ).fetchone()
            actual_seq = int(last["seq"] or 0) if last is not None else 0
            actual_hash = str(last["event_hash"] or "") if last is not None else ""
            event_time = str(last["event_time"] or "") if last is not None else ""
            activity_rows = [
                connection.execute("SELECT started_at AS value FROM runs WHERE run_id=?", (identifier,)).fetchone(),
                connection.execute("SELECT MAX(event_time) AS value FROM events WHERE run_id=?", (identifier,)).fetchone(),
                connection.execute("SELECT MAX(started_at) AS value FROM waves WHERE run_id=?", (identifier,)).fetchone(),
                connection.execute("SELECT MAX(finished_at) AS value FROM waves WHERE run_id=?", (identifier,)).fetchone(),
                connection.execute("SELECT MAX(updated_at) AS value FROM agent_lanes WHERE run_id=?", (identifier,)).fetchone(),
                connection.execute("SELECT MAX(updated_at) AS value FROM background_operations WHERE run_id=?", (identifier,)).fetchone(),
                connection.execute("SELECT MAX(updated_at) AS value FROM managed_process_jobs WHERE run_id=?", (identifier,)).fetchone(),
                connection.execute("SELECT MAX(created_at) AS value FROM handoff_capsules WHERE run_id=?", (identifier,)).fetchone(),
            ]
            actual_activity = max((str(row["value"] or "") for row in activity_rows if row is not None and str(row["value"] or "")), default="")
            actual_status = str(run["status"] or "").lower()
            if (
                actual_status != expected_status
                or actual_activity != expected_activity
                or actual_seq != int(expected_run_last_event_seq)
                or actual_hash != expected_hash
            ):
                connection.rollback()
                raise LifecycleReconciliationError("exact stale-run guard changed before reconciliation")
            if actual_status == "stale":
                if str(last["event_type"] or "") != "run_stale_reconciled":
                    connection.rollback()
                    raise LifecycleReconciliationError("terminal stale run lacks exact stale reconciliation receipt")
                connection.commit()
                return {
                    "changed": False,
                    "idempotent": True,
                    "run_id": identifier,
                    "status": "stale",
                    "event_seq": actual_seq,
                    "event_hash": actual_hash,
                }
            if actual_status != "active":
                connection.rollback()
                raise LifecycleReconciliationError("stale-run target is not active")
            if last is not None and str(last["state_after"] or "").upper() == "ACCEPTING":
                connection.rollback()
                raise LifecycleReconciliationError("accepting run is not an exact stale-run target")
            if connection.execute("SELECT 1 FROM p5_experiment_epochs WHERE ledger_run_id=? LIMIT 1", (identifier,)).fetchone():
                connection.rollback()
                raise LifecycleReconciliationError("P5 experiment anchor is not an exact stale-run target")
            live_checks = (
                "SELECT 1 FROM controller_leases WHERE run_id=? AND status='active' AND expires_at>? LIMIT 1",
                "SELECT 1 FROM write_fences WHERE run_id=? AND status='active' AND expires_at>? LIMIT 1",
                "SELECT 1 FROM background_operations WHERE run_id=? AND status='running' LIMIT 1",
                "SELECT 1 FROM agent_lanes WHERE run_id=? AND lifecycle IN ('starting','active','waiting','idle') LIMIT 1",
                "SELECT 1 FROM managed_process_jobs WHERE run_id=? AND lifecycle_state IN ('starting','active','waiting','idle','running') LIMIT 1",
            )
            if (
                connection.execute(live_checks[0], (identifier, observed_at)).fetchone()
                or connection.execute(live_checks[1], (identifier, observed_at)).fetchone()
                or connection.execute(live_checks[2], (identifier,)).fetchone()
                or connection.execute(live_checks[3], (identifier,)).fetchone()
                or connection.execute(live_checks[4], (identifier,)).fetchone()
            ):
                connection.rollback()
                raise LifecycleReconciliationError("stale-run target acquired live ownership before reconciliation")
            try:
                activity_ts = datetime.fromisoformat(actual_activity.replace("Z", "+00:00")).timestamp()
            except ValueError as exc:
                connection.rollback()
                raise LifecycleReconciliationError("stale-run target has no parseable guarded activity timestamp") from exc
            if observed_at - activity_ts < stale_after:
                connection.rollback()
                raise LifecycleReconciliationError("stale-run target has not crossed the guarded inactivity threshold")

            now = _utc_now()
            for wave in connection.execute("SELECT * FROM waves WHERE run_id=? AND status='active' ORDER BY ordinal", (identifier,)).fetchall():
                wave_metadata = json.loads(wave["metadata_json"] or "{}")
                wave_metadata = wave_metadata if isinstance(wave_metadata, dict) else {}
                wave_metadata["lifecycle_reconciliation"] = {
                    "reason": bounded_reason,
                    "authority": operator,
                    "run_status": "stale",
                    "stale_after_seconds": stale_after,
                }
                wave_id = str(wave["wave_id"] or "")
                connection.execute(
                    "UPDATE waves SET status='aborted',finished_at=?,metadata_json=? WHERE wave_id=?",
                    (now, _json(wave_metadata), wave_id),
                )
                append_hash_chained_event(
                    connection,
                    run_id=identifier,
                    event_type="wave_lifecycle_reconciled",
                    wave_id=wave_id or None,
                    delegation_id=None,
                    state_before="active",
                    state_after="ABORTED",
                    payload={
                        "reason": bounded_reason,
                        "authority": operator,
                        "run_status": "stale",
                        "wave_status": "aborted",
                    },
                    event_time=now,
                    sanitize=lambda value: value,
                    serialize=_json,
                    bounded_text=_bounded_text,
                )
            run_metadata = json.loads(run["metadata_json"] or "{}")
            run_metadata = run_metadata if isinstance(run_metadata, dict) else {}
            run_metadata["lifecycle_reconciliation"] = {
                "reason": bounded_reason,
                "authority": operator,
                "latest_activity_at": actual_activity,
                "stale_after_seconds": stale_after,
            }
            connection.execute(
                "UPDATE runs SET status='stale',finished_at=?,metadata_json=? WHERE run_id=?",
                (now, _json(run_metadata), identifier),
            )
            event = append_hash_chained_event(
                connection,
                run_id=identifier,
                event_type="run_stale_reconciled",
                wave_id=None,
                delegation_id=None,
                state_before="active",
                state_after="ABORTED",
                payload={
                    "reason": bounded_reason,
                    "authority": operator,
                    "stale_after_seconds": stale_after,
                },
                event_time=now,
                sanitize=lambda value: value,
                serialize=_json,
                bounded_text=_bounded_text,
            )
            connection.commit()
        return {
            "changed": True,
            "idempotent": False,
            "run_id": identifier,
            "status": "stale",
            "event_seq": int(event["seq"]),
            "event_hash": str(event["event_hash"]),
        }

    def reconcile_exact_completed_agent_lane(
        self,
        *,
        lane_id: str,
        expected_logical_sha256: str,
        expected_run_id: str,
        expected_wave_id: str,
        expected_semantic_key: str,
        expected_thread_id: str,
        expected_session_id: str,
        expected_lane_last_turn_id: str,
        expected_lane_lifecycle: str,
        expected_lane_updated_at: str,
        expected_run_status: str,
        expected_run_state: str,
        expected_run_last_event_seq: int,
        expected_run_last_event_hash: str,
        external_completed_turn_id: str,
        external_thread_status: str,
        externally_observed_at: str,
        runtime_stopped: bool,
        authority: str,
        reason: str = "completed_external_agent_lane_stopped_runtime_deadlock",
    ) -> dict[str, Any]:
        """Close one exact external lane after its real client task completed.

        This is an operator-only stopped-runtime escape hatch for the activation
        deadlock where Coding MCP cannot expose ``task_control`` until the last
        live lane is closed.  It never changes the parent RUN/WAVE lifecycle or
        acceptance state.  Every ledger identity and the caller's independently
        observed terminal turn are bound into one durable receipt.
        """
        identifier = _bounded_text(lane_id, 256).strip()
        expected_logical = _bounded_text(expected_logical_sha256, 64).strip().lower()
        run_guard = _bounded_text(expected_run_id, 256).strip()
        wave_guard = _bounded_text(expected_wave_id, 256).strip()
        semantic_guard = _bounded_text(expected_semantic_key, 512).strip()
        thread_guard = _bounded_text(expected_thread_id, 256).strip()
        session_guard = _bounded_text(expected_session_id, 256).strip()
        lane_turn_guard = _bounded_text(expected_lane_last_turn_id, 256).strip()
        lifecycle_guard = _bounded_text(expected_lane_lifecycle, 64).strip().lower()
        updated_guard = _bounded_text(expected_lane_updated_at, 64).strip()
        status_guard = _bounded_text(expected_run_status, 64).strip().lower()
        state_guard = _bounded_text(expected_run_state, 64).strip().upper()
        event_hash_guard = _bounded_text(expected_run_last_event_hash, 64).strip().lower()
        completed_turn = _bounded_text(external_completed_turn_id, 256).strip()
        thread_status = _bounded_text(external_thread_status, 64).strip().lower()
        observed_at = _bounded_text(externally_observed_at, 64).strip()
        operator = _bounded_text(authority, 128).strip()
        bounded_reason = _bounded_text(reason, 256).strip()
        required = (
            identifier,
            run_guard,
            wave_guard,
            semantic_guard,
            thread_guard,
            session_guard,
            lane_turn_guard,
            lifecycle_guard,
            updated_guard,
            status_guard,
            state_guard,
            completed_turn,
            thread_status,
            observed_at,
            operator,
            bounded_reason,
        )
        if not all(required):
            raise LifecycleReconciliationError("completed-agent lane reconciliation requires complete exact guards")
        if runtime_stopped is not True:
            raise LifecycleReconciliationError("completed-agent lane reconciliation requires explicit stopped-runtime authority")
        if len(expected_logical) != 64 or any(char not in "0123456789abcdef" for char in expected_logical):
            raise LifecycleReconciliationError("expected logical ledger SHA-256 is invalid")
        if expected_run_last_event_seq < 0 or (
            event_hash_guard
            and (len(event_hash_guard) != 64 or any(char not in "0123456789abcdef" for char in event_hash_guard))
        ):
            raise LifecycleReconciliationError("expected run event guard is invalid")
        if lifecycle_guard not in _LIVE_LANE_LIFECYCLES | {"closed"}:
            raise LifecycleReconciliationError("completed-agent lane lifecycle guard is not reconcilable")
        if status_guard != "active" or state_guard != "ACCEPTING":
            raise LifecycleReconciliationError("completed-agent lane parent must remain active and ACCEPTING")
        if thread_status not in {"idle", "completed"}:
            raise LifecycleReconciliationError("external agent thread is not in an observed terminal status")
        if completed_turn == lane_turn_guard:
            raise LifecycleReconciliationError("external completion proof must be a later turn than the lane's interrupted turn")
        try:
            parsed_observation = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise LifecycleReconciliationError("external completion observation timestamp is invalid") from exc
        if parsed_observation.tzinfo is None:
            raise LifecycleReconciliationError("external completion observation timestamp must include a timezone")

        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            if logical_ledger_sha256(connection) != expected_logical:
                connection.rollback()
                raise LifecycleReconciliationError("logical ledger snapshot changed before completed-agent lane reconciliation")
            row = connection.execute(
                """SELECT l.*,r.status AS run_status,w.run_id AS wave_run_id
                   FROM agent_lanes l
                   JOIN runs r ON r.run_id=l.run_id
                   JOIN waves w ON w.wave_id=l.wave_id
                   WHERE l.lane_id=?""",
                (identifier,),
            ).fetchone()
            if row is None:
                connection.rollback()
                raise LifecycleReconciliationError("completed-agent lane target was not found")
            last = connection.execute(
                "SELECT seq,event_hash,event_type,state_after FROM events WHERE run_id=? ORDER BY seq DESC LIMIT 1",
                (run_guard,),
            ).fetchone()
            actual_seq = int(last["seq"] or 0) if last is not None else 0
            actual_hash = str(last["event_hash"] or "") if last is not None else ""
            actual_state = str(last["state_after"] or "").upper() if last is not None else ""
            exact_lane_guards = (
                str(row["run_id"] or "") == run_guard,
                str(row["wave_id"] or "") == wave_guard,
                str(row["wave_run_id"] or "") == run_guard,
                str(row["semantic_key"] or "") == semantic_guard,
                str(row["thread_id"] or "") == thread_guard,
                str(row["session_id"] or "") == session_guard,
                str(row["last_turn_id"] or "") == lane_turn_guard,
                str(row["lifecycle"] or "").lower() == lifecycle_guard,
                str(row["updated_at"] or "") == updated_guard,
                str(row["run_status"] or "").lower() == status_guard,
                actual_state == state_guard,
                actual_seq == int(expected_run_last_event_seq),
                actual_hash == event_hash_guard,
            )
            if not all(exact_lane_guards):
                connection.rollback()
                raise LifecycleReconciliationError("completed-agent lane guard changed before reconciliation")

            metadata = json.loads(row["metadata_json"] or "{}")
            metadata = metadata if isinstance(metadata, dict) else {}
            receipt = metadata.get("completed_agent_lane_reconciliation")
            receipt = receipt if isinstance(receipt, dict) else {}
            if lifecycle_guard == "closed":
                if (
                    str(receipt.get("run_id") or "") != run_guard
                    or str(receipt.get("wave_id") or "") != wave_guard
                    or str(receipt.get("thread_id") or "") != thread_guard
                    or str(receipt.get("external_completed_turn_id") or "") != completed_turn
                ):
                    connection.rollback()
                    raise LifecycleReconciliationError("closed lane lacks the exact completed-agent reconciliation receipt")
                connection.commit()
                return {
                    "changed": False,
                    "idempotent": True,
                    "lane_id": identifier,
                    "run_id": run_guard,
                    "wave_id": wave_guard,
                    "lifecycle": "closed",
                    "parent_state": "ACCEPTING",
                    "external_completed_turn_id": completed_turn,
                }

            if connection.execute(
                "SELECT 1 FROM p5_experiment_epochs WHERE ledger_run_id=? LIMIT 1",
                (run_guard,),
            ).fetchone():
                connection.rollback()
                raise LifecycleReconciliationError("P5 experiment anchor is not a completed-agent lane target")
            live_checks = (
                connection.execute(
                    "SELECT 1 FROM controller_leases WHERE run_id=? AND status='active' LIMIT 1",
                    (run_guard,),
                ).fetchone(),
                connection.execute(
                    "SELECT 1 FROM write_fences WHERE (run_id=? OR wave_id=?) AND status='active' LIMIT 1",
                    (run_guard, wave_guard),
                ).fetchone(),
                connection.execute(
                    "SELECT 1 FROM background_operations WHERE (run_id=? OR wave_id=?) AND status='running' LIMIT 1",
                    (run_guard, wave_guard),
                ).fetchone(),
                connection.execute(
                    """SELECT 1 FROM managed_process_jobs
                       WHERE (run_id=? OR wave_id=?)
                       AND lifecycle_state IN ('starting','active','waiting','idle','running') LIMIT 1""",
                    (run_guard, wave_guard),
                ).fetchone(),
                connection.execute(
                    """SELECT 1 FROM agent_lanes
                       WHERE run_id=? AND lane_id<>?
                       AND lifecycle IN ('starting','active','waiting','idle') LIMIT 1""",
                    (run_guard, identifier),
                ).fetchone(),
            )
            if any(live_checks):
                connection.rollback()
                raise LifecycleReconciliationError("completed-agent lane target has competing live ownership")

            now = _utc_now()
            receipt = {
                "schema_version": 1,
                "reason": bounded_reason,
                "authority": operator,
                "runtime_stopped_attested": True,
                "run_id": run_guard,
                "wave_id": wave_guard,
                "semantic_key": semantic_guard,
                "thread_id": thread_guard,
                "session_id": session_guard,
                "lane_last_turn_id": lane_turn_guard,
                "external_completed_turn_id": completed_turn,
                "external_thread_status": thread_status,
                "externally_observed_at": observed_at,
                "reconciled_at": now,
                "parent_status": status_guard,
                "parent_state": state_guard,
            }
            metadata["completed_agent_lane_reconciliation"] = receipt
            connection.execute(
                "UPDATE agent_lanes SET lifecycle='closed',metadata_json=?,updated_at=? WHERE lane_id=?",
                (_json(metadata), now, identifier),
            )
            event = append_hash_chained_event(
                connection,
                run_id=run_guard,
                event_type="completed_agent_lane_reconciled",
                wave_id=wave_guard,
                delegation_id=None,
                state_before="ACCEPTING",
                state_after="ACCEPTING",
                payload={
                    "lane_id": identifier,
                    "reason": bounded_reason,
                    "authority": operator,
                    "lane_lifecycle_before": lifecycle_guard,
                    "lane_lifecycle_after": "closed",
                    "thread_id": thread_guard,
                    "lane_last_turn_id": lane_turn_guard,
                    "external_completed_turn_id": completed_turn,
                    "external_thread_status": thread_status,
                    "externally_observed_at": observed_at,
                    "runtime_stopped_attested": True,
                    "parent_status": status_guard,
                    "parent_state": state_guard,
                },
                event_time=now,
                sanitize=lambda value: value,
                serialize=_json,
                bounded_text=_bounded_text,
            )
            connection.execute(
                """INSERT INTO coordination_messages(
                    message_id,run_id,wave_id,lane_id,direction,kind,status,base_head,worktree_fp,
                    created_at,acknowledged_at,payload_json
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    uuid.uuid4().hex,
                    run_guard,
                    wave_guard,
                    identifier,
                    "system",
                    "completed_agent_lane_reconciled",
                    "pending",
                    str(row["base_head"] or ""),
                    str(row["worktree_fp"] or ""),
                    now,
                    None,
                    _json(receipt),
                ),
            )
            connection.commit()
        return {
            "changed": True,
            "idempotent": False,
            "lane_id": identifier,
            "run_id": run_guard,
            "wave_id": wave_guard,
            "lifecycle": "closed",
            "parent_state": "ACCEPTING",
            "external_completed_turn_id": completed_turn,
            "event_seq": int(event["seq"]),
            "event_hash": str(event["event_hash"]),
        }

    def reconcile_terminal_parent_lane(
        self,
        *,
        lane_id: str,
        expected_logical_sha256: str,
        expected_lane_updated_at: str,
        expected_run_status: str,
        expected_run_last_event_seq: int,
        expected_run_last_event_hash: str,
        authority: str,
        reason: str = "terminal_parent_lane_residue",
    ) -> dict[str, Any]:
        """Close one live lane whose exact parent run is already terminal.

        The operation is deliberately narrow: all optimistic guards must match
        inside one transaction, no wildcard update is possible, and a successful
        change records both a hash-chained run event and a coordination receipt.
        """
        identifier = _bounded_text(lane_id, 256).strip()
        expected_logical = _bounded_text(expected_logical_sha256, 64).strip().lower()
        expected_updated = _bounded_text(expected_lane_updated_at, 64).strip()
        expected_status = _bounded_text(expected_run_status, 64).strip().lower()
        expected_hash = _bounded_text(expected_run_last_event_hash, 64).strip().lower()
        operator = _bounded_text(authority, 128).strip()
        bounded_reason = _bounded_text(reason, 256).strip()
        if not identifier or not expected_updated or not operator or not bounded_reason:
            raise LifecycleReconciliationError("terminal-parent lane reconciliation requires complete exact guards")
        if len(expected_logical) != 64 or any(char not in "0123456789abcdef" for char in expected_logical):
            raise LifecycleReconciliationError("expected logical ledger SHA-256 is invalid")
        if expected_status not in _TERMINAL_PARENT_STATUSES:
            raise LifecycleReconciliationError("expected parent status is not terminal")
        if expected_run_last_event_seq < 0 or (expected_hash and (len(expected_hash) != 64 or any(char not in "0123456789abcdef" for char in expected_hash))):
            raise LifecycleReconciliationError("expected run event guard is invalid")

        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            if logical_ledger_sha256(connection) != expected_logical:
                connection.rollback()
                raise LifecycleReconciliationError("logical ledger snapshot changed before terminal-parent reconciliation")
            row = connection.execute(
                """SELECT l.*, r.status AS run_status
                   FROM agent_lanes l JOIN runs r ON r.run_id=l.run_id
                   WHERE l.lane_id=?""",
                (identifier,),
            ).fetchone()
            if row is None:
                connection.rollback()
                raise LifecycleReconciliationError("terminal-parent lane was not found")
            run_id = str(row["run_id"] or "")
            wave_id = str(row["wave_id"] or "")
            last = connection.execute(
                "SELECT seq,event_hash FROM events WHERE run_id=? ORDER BY seq DESC LIMIT 1",
                (run_id,),
            ).fetchone()
            actual_seq = int(last["seq"] or 0) if last is not None else 0
            actual_hash = str(last["event_hash"] or "") if last is not None else ""
            if (
                str(row["updated_at"] or "") != expected_updated
                or str(row["run_status"] or "").lower() != expected_status
                or actual_seq != int(expected_run_last_event_seq)
                or actual_hash != expected_hash
            ):
                connection.rollback()
                raise LifecycleReconciliationError("terminal-parent lane guard changed before reconciliation")
            lifecycle = str(row["lifecycle"] or "").lower()
            if lifecycle == "closed":
                connection.commit()
                return {
                    "changed": False,
                    "idempotent": True,
                    "lane_id": identifier,
                    "run_id": run_id,
                    "wave_id": wave_id,
                    "lifecycle": "closed",
                }
            if lifecycle not in _LIVE_LANE_LIFECYCLES:
                connection.rollback()
                raise LifecycleReconciliationError("terminal-parent lane is not in a reconcilable live lifecycle")
            metadata = json.loads(row["metadata_json"] or "{}")
            metadata = metadata if isinstance(metadata, dict) else {}
            metadata["lifecycle_reconciliation"] = {
                "reason": bounded_reason,
                "authority": operator,
                "parent_status": expected_status,
            }
            now = _utc_now()
            connection.execute(
                "UPDATE agent_lanes SET lifecycle='closed',metadata_json=?,updated_at=? WHERE lane_id=?",
                (_json(metadata), now, identifier),
            )
            event = append_hash_chained_event(
                connection,
                run_id=run_id,
                event_type="terminal_parent_lane_reconciled",
                wave_id=wave_id or None,
                delegation_id=None,
                state_before=lifecycle.upper(),
                state_after="CLOSED",
                payload={
                    "lane_id": identifier,
                    "reason": bounded_reason,
                    "authority": operator,
                    "parent_status": expected_status,
                },
                event_time=now,
                sanitize=lambda value: value,
                serialize=_json,
                bounded_text=_bounded_text,
            )
            connection.execute(
                """INSERT INTO coordination_messages(
                    message_id,run_id,wave_id,lane_id,direction,kind,status,base_head,worktree_fp,
                    created_at,acknowledged_at,payload_json
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    uuid.uuid4().hex,
                    run_id,
                    wave_id,
                    identifier,
                    "system",
                    "lane_closed",
                    "pending",
                    str(row["base_head"] or ""),
                    str(row["worktree_fp"] or ""),
                    now,
                    None,
                    _json({"reason": bounded_reason, "authority": operator}),
                ),
            )
            connection.commit()
        return {
            "changed": True,
            "idempotent": False,
            "lane_id": identifier,
            "run_id": run_id,
            "wave_id": wave_id,
            "lifecycle": "closed",
            "event_seq": int(event["seq"]),
            "event_hash": str(event["event_hash"]),
        }

    def reconcile_gone_managed_process_job(
        self,
        *,
        job_id: str,
        expected_logical_sha256: str,
        expected_job_updated_at: str,
        expected_lifecycle_state: str,
        expected_checkout_id: str,
        authority: str,
        reason: str = "dead_or_recycled_process_identity",
    ) -> dict[str, Any]:
        """Quiesce one exact job only after its original process identity is gone.

        This never terminates a process.  A live PID with its expected creation
        token is an ownership boundary and fails closed; a missing PID or token
        mismatch is evidence that the recorded process is gone/recycled.
        """
        identifier = _bounded_text(job_id, 256).strip()
        expected_logical = _bounded_text(expected_logical_sha256, 64).strip().lower()
        expected_updated = _bounded_text(expected_job_updated_at, 64).strip()
        expected_state = _bounded_text(expected_lifecycle_state, 64).strip()
        expected_checkout = _bounded_text(expected_checkout_id, 128).strip()
        operator = _bounded_text(authority, 128).strip()
        bounded_reason = _bounded_text(reason, 256).strip()
        if not all((identifier, expected_updated, expected_state, expected_checkout, operator, bounded_reason)):
            raise LifecycleReconciliationError("managed-process reconciliation requires complete exact guards")
        if len(expected_logical) != 64 or any(char not in "0123456789abcdef" for char in expected_logical):
            raise LifecycleReconciliationError("expected logical ledger SHA-256 is invalid")

        # Delay this import until the parent ledger module has completed loading.
        from .execution_resources import ACTIVE_LIFECYCLES, process_identity_token, process_is_alive

        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            if logical_ledger_sha256(connection) != expected_logical:
                connection.rollback()
                raise LifecycleReconciliationError("logical ledger snapshot changed before managed-process reconciliation")
            row = connection.execute(
                "SELECT * FROM managed_process_jobs WHERE job_id=?",
                (identifier,),
            ).fetchone()
            if row is None:
                connection.rollback()
                raise LifecycleReconciliationError("managed process job was not found")
            state = str(row["lifecycle_state"] or "")
            if state not in ACTIVE_LIFECYCLES:
                connection.commit()
                return {"changed": False, "idempotent": True, "job_id": identifier, "lifecycle_state": state}
            if (
                str(row["updated_at"] or "") != expected_updated
                or state != expected_state
                or str(row["checkout_id"] or "") != expected_checkout
            ):
                connection.rollback()
                raise LifecycleReconciliationError("managed-process job guard changed before reconciliation")
            pid = int(row["root_pid"] or 0)
            expected_token = str(row["root_process_token"] or "")
            process_exists = bool(pid > 0 and process_is_alive(pid))
            observed_token = str(process_identity_token(pid) or "") if process_exists else ""
            if process_exists and expected_token and observed_token == expected_token:
                connection.rollback()
                raise LifecycleReconciliationError("managed process remains live with its expected identity")
            if process_exists and (not expected_token or not observed_token):
                connection.rollback()
                raise LifecycleReconciliationError("managed process identity is unavailable; refusing to cross ownership boundary")
            recovery_reason = "root_process_gone" if not process_exists else "root_process_identity_mismatch"
            metadata = json.loads(row["metadata_json"] or "{}")
            metadata = metadata if isinstance(metadata, dict) else {}
            metadata["lifecycle_reconciliation"] = {
                "reason": bounded_reason,
                "recovery_reason": recovery_reason,
                "authority": operator,
            }
            now = _utc_now()
            connection.execute(
                """UPDATE managed_process_jobs
                   SET lifecycle_state='quiesced',updated_at=?,finished_at=?,metadata_json=?
                   WHERE job_id=?""",
                (now, now, _json(metadata), identifier),
            )
            owner_hash = hashlib.sha256(
                f"webcodex-resource-claim-v1\0MANAGED_JOB\0{identifier}".encode("utf-8", errors="replace")
            ).hexdigest()
            connection.execute(
                """UPDATE checkout_resource_claims SET lifecycle_state='released',updated_at=?
                   WHERE owner_type='MANAGED_JOB' AND owner_id_hash=? AND lifecycle_state='active'""",
                (now, owner_hash),
            )
            run_id = str(row["run_id"] or "")
            wave_id = str(row["wave_id"] or "")
            event: dict[str, Any] | None = None
            if run_id:
                event = append_hash_chained_event(
                    connection,
                    run_id=run_id,
                    event_type="managed_process_reconciled",
                    wave_id=wave_id or None,
                    delegation_id=None,
                    state_before=state.upper(),
                    state_after="QUIESCED",
                    payload={
                        "job_id": identifier,
                        "reason": bounded_reason,
                        "recovery_reason": recovery_reason,
                        "authority": operator,
                    },
                    event_time=now,
                    sanitize=lambda value: value,
                    serialize=_json,
                    bounded_text=_bounded_text,
                )
            connection.execute(
                """INSERT INTO coordination_messages(
                    message_id,run_id,wave_id,lane_id,direction,kind,status,base_head,worktree_fp,
                    created_at,acknowledged_at,payload_json
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    uuid.uuid4().hex,
                    run_id,
                    wave_id,
                    "",
                    "system",
                    "managed_process_reconciled",
                    "pending",
                    "",
                    "",
                    now,
                    None,
                    _json({"job_id": identifier, "reason": bounded_reason, "recovery_reason": recovery_reason, "authority": operator}),
                ),
            )
            connection.commit()
        return {
            "changed": True,
            "idempotent": False,
            "job_id": identifier,
            "lifecycle_state": "quiesced",
            "recovery_reason": recovery_reason,
            "event_seq": int(event["seq"]) if event is not None else None,
            "out_of_run_receipt": event is None,
        }

    def reconcile_unbound_agent_lane(
        self,
        *,
        lane_id: str,
        expected_logical_sha256: str,
        expected_lane_updated_at: str,
        authority: str,
        reason: str = "unbound_live_lane_residue",
    ) -> dict[str, Any]:
        """Close one exact live lane that has no canonical parent run.

        Out-of-run rows cannot append to a per-run hash chain; they therefore
        retain a bounded metadata receipt plus a durable coordination message.
        """
        identifier = _bounded_text(lane_id, 256).strip()
        expected_logical = _bounded_text(expected_logical_sha256, 64).strip().lower()
        expected_updated = _bounded_text(expected_lane_updated_at, 64).strip()
        operator = _bounded_text(authority, 128).strip()
        bounded_reason = _bounded_text(reason, 256).strip()
        if not all((identifier, expected_updated, operator, bounded_reason)):
            raise LifecycleReconciliationError("unbound lane reconciliation requires complete exact guards")
        if len(expected_logical) != 64 or any(char not in "0123456789abcdef" for char in expected_logical):
            raise LifecycleReconciliationError("expected logical ledger SHA-256 is invalid")
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            if logical_ledger_sha256(connection) != expected_logical:
                connection.rollback()
                raise LifecycleReconciliationError("logical ledger snapshot changed before unbound lane reconciliation")
            row = connection.execute("SELECT * FROM agent_lanes WHERE lane_id=?", (identifier,)).fetchone()
            if row is None:
                connection.rollback()
                raise LifecycleReconciliationError("unbound lane was not found")
            run_id = str(row["run_id"] or "")
            parent = connection.execute("SELECT 1 FROM runs WHERE run_id=?", (run_id,)).fetchone() if run_id else None
            if run_id and parent is not None:
                connection.rollback()
                raise LifecycleReconciliationError("lane has a canonical parent and is not an unbound reconciliation target")
            lifecycle = str(row["lifecycle"] or "").lower()
            if str(row["updated_at"] or "") != expected_updated:
                connection.rollback()
                raise LifecycleReconciliationError("unbound lane guard changed before reconciliation")
            if lifecycle == "closed":
                connection.commit()
                return {"changed": False, "idempotent": True, "lane_id": identifier, "lifecycle": "closed"}
            if lifecycle not in _LIVE_LANE_LIFECYCLES:
                connection.rollback()
                raise LifecycleReconciliationError("unbound lane is not in a reconcilable live lifecycle")
            metadata = json.loads(row["metadata_json"] or "{}")
            metadata = metadata if isinstance(metadata, dict) else {}
            metadata["lifecycle_reconciliation"] = {
                "reason": bounded_reason,
                "authority": operator,
                "parent": "missing",
            }
            now = _utc_now()
            connection.execute(
                "UPDATE agent_lanes SET lifecycle='closed',metadata_json=?,updated_at=? WHERE lane_id=?",
                (_json(metadata), now, identifier),
            )
            connection.execute(
                """INSERT INTO coordination_messages(
                    message_id,run_id,wave_id,lane_id,direction,kind,status,base_head,worktree_fp,
                    created_at,acknowledged_at,payload_json
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    uuid.uuid4().hex,
                    run_id,
                    str(row["wave_id"] or ""),
                    identifier,
                    "system",
                    "lane_closed",
                    "pending",
                    str(row["base_head"] or ""),
                    str(row["worktree_fp"] or ""),
                    now,
                    None,
                    _json({"reason": bounded_reason, "authority": operator, "parent": "missing"}),
                ),
            )
            connection.commit()
        return {"changed": True, "idempotent": False, "lane_id": identifier, "lifecycle": "closed", "out_of_run_receipt": True}
