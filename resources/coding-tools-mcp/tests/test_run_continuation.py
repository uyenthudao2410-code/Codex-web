from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.continuation_driver import (
    continuation_execution_environment_hash,
    materialize_continuation_effect_backups,
    observe_continuation_effect,
)
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.run_continuation import (
    RunContinuationError,
    RunContinuationLedgerMixin,
    build_run_continuation_policy,
    parse_run_continuation_proposal,
)
from coding_tools_mcp.server import Runtime
from coding_tools_mcp.tool_schema import input_schemas, validate_arguments


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def check_definition(check_id: str = "unit") -> dict[str, object]:
    definition = {
        "check_id": check_id,
        "argv": ["python", "-m", "pytest", "tests/test_target.py"],
        "cwd": "resources/coding-tools-mcp",
        "environment_hash": "a" * 64,
    }
    return {**definition, "definition_hash": digest(definition)}


def grant_request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "action": "grant",
        "read_paths": ["resources/coding-tools-mcp/coding_tools_mcp/target.py"],
        "write_paths": ["resources/coding-tools-mcp/coding_tools_mcp/target.py"],
        "protected_paths": ["resources/coding-tools-mcp/coding_tools_mcp/server.py"],
        "approved_checks": [check_definition()],
        "max_duration_seconds": 120,
        "max_decision_turns": 4,
        "max_patch_attempts": 2,
    }
    request.update(overrides)
    return request


def policy(run_id: str, request: dict[str, object] | None = None) -> dict[str, object]:
    return build_run_continuation_policy(
        request or grant_request(),
        run_id=run_id,
        workspace_id="workspace-test",
        problem_id="problem-test",
        problem_revision=1,
        contract_fingerprint="b" * 64,
        tool_contract_sha256="c" * 64,
        runtime_behavior_fingerprint="d" * 64,
        activation_epoch_id="epoch-test",
        activation_admission="open",
        issuer_client_id="chatweb-test",
    )


class RunContinuationLedgerTests(unittest.TestCase):
    def _ledger_with_run(self, root: Path) -> tuple[OrchestrationLedger, str]:
        ledger = OrchestrationLedger(root)
        run_id = ledger.create_run(objective="bounded durable repair")
        ledger.create_wave(run_id, execution_mode="deep_single_lane")
        return ledger, run_id

    def test_existing_continuation_schema_gains_read_and_dispatch_cursor_columns(self) -> None:
        """A pre-cursor ledger must upgrade in place without a second store."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy_dir = root / ".coding-tools" / "orchestration"
            legacy_dir.mkdir(parents=True)
            with closing(sqlite3.connect(legacy_dir / "ledger.sqlite3")) as connection:
                connection.executescript(
                    """
                    CREATE TABLE run_continuations (
                        run_id TEXT PRIMARY KEY REFERENCES runs(run_id) ON DELETE CASCADE,
                        workspace_id TEXT NOT NULL,
                        problem_id TEXT NOT NULL,
                        problem_revision INTEGER NOT NULL CHECK(problem_revision>=1),
                        policy_json TEXT NOT NULL,
                        policy_sha256 TEXT NOT NULL,
                        issuer_receipt_sha256 TEXT NOT NULL,
                        policy_revision INTEGER NOT NULL DEFAULT 1,
                        enabled INTEGER NOT NULL DEFAULT 1,
                        pause_reason TEXT NOT NULL DEFAULT '',
                        revoked_at TEXT,
                        driver_generation INTEGER NOT NULL DEFAULT 0,
                        claimed_runtime_instance TEXT NOT NULL DEFAULT '',
                        claim_expires_at_unix_ms INTEGER NOT NULL DEFAULT 0,
                        next_action_seq INTEGER NOT NULL DEFAULT 1,
                        consumed_event_seq INTEGER NOT NULL DEFAULT 0,
                        pending_action_id TEXT NOT NULL DEFAULT '',
                        pending_job_id TEXT NOT NULL DEFAULT '',
                        lane_id TEXT NOT NULL DEFAULT '',
                        thread_id TEXT NOT NULL DEFAULT '',
                        last_turn_id TEXT NOT NULL DEFAULT '',
                        remaining_decision_turns INTEGER NOT NULL,
                        remaining_patch_attempts INTEGER NOT NULL,
                        expires_at_unix_ms INTEGER NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );
                    """
                )
                connection.commit()
            with closing(sqlite3.connect(legacy_dir / "ledger.sqlite3")) as connection:
                connection.row_factory = sqlite3.Row
                RunContinuationLedgerMixin._run_continuation_ensure_schema(connection)
                columns = {str(row["name"]) for row in connection.execute("PRAGMA table_info(run_continuations)").fetchall()}
                connection.commit()
            self.assertTrue({
                "pending_evidence_hash",
                "pending_evidence_paths_json",
                "pending_replan_json",
                "pending_dispatch_action_id",
                "pending_patch_action_id",
            }.issubset(columns))

    def test_grant_is_durable_idempotent_and_conflicts_on_policy_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger, run_id = self._ledger_with_run(root)
            first = ledger.issue_run_continuation(
                run_id=run_id,
                policy=policy(run_id),
                issuer_receipt_sha256="e" * 64,
                now_unix_ms=1_000_000,
            )
            self.assertEqual(first["status"], "GRANTED")
            self.assertFalse(first["idempotent"])
            self.assertEqual(first["continuation"]["policy"]["route"], "sol_xhigh")
            self.assertNotIn("argv", first["continuation"]["policy"]["approved_checks"][0])

            reopened = OrchestrationLedger(root)
            stored = reopened.get_run_continuation(run_id)
            self.assertIsNotNone(stored)
            self.assertEqual(stored["policy_sha256"], first["continuation"]["policy_sha256"])
            replay = reopened.issue_run_continuation(
                run_id=run_id,
                policy=policy(run_id),
                issuer_receipt_sha256="e" * 64,
                now_unix_ms=1_000_100,
            )
            self.assertTrue(replay["idempotent"])
            with self.assertRaises(RunContinuationError) as changed:
                reopened.issue_run_continuation(
                    run_id=run_id,
                    policy=policy(run_id, grant_request(max_decision_turns=3)),
                    issuer_receipt_sha256="e" * 64,
                    now_unix_ms=1_000_200,
                )
            self.assertEqual(changed.exception.code, "RUN_CONTINUATION_GRANT_CONFLICT")
            self.assertTrue(reopened.verify_chain(run_id)["ok"])

    def test_claim_generation_scope_check_and_cursor_are_fenced(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger, run_id = self._ledger_with_run(root)
            granted = ledger.issue_run_continuation(
                run_id=run_id,
                policy=policy(run_id),
                issuer_receipt_sha256="e" * 64,
            )
            first = ledger.claim_run_continuation(
                run_id=run_id,
                runtime_instance_id="runtime-one",
                expected_generation=0,
            )
            self.assertTrue(first["claimed"])
            generation = first["continuation"]["driver_generation"]
            self.assertEqual(generation, 1)

            with self.assertRaises(RunContinuationError) as no_scope:
                ledger.assert_run_continuation_execution(
                    run_id=run_id,
                    driver_generation=generation,
                    runtime_instance_id="runtime-one",
                    paths=["other.py"],
                )
            self.assertEqual(no_scope.exception.code, "RUN_CONTINUATION_SCOPE_DENIED")
            check_hash = granted["continuation"]["policy"]["approved_checks"][0]["definition_hash"]
            accepted = ledger.assert_run_continuation_execution(
                    run_id=run_id,
                    driver_generation=generation,
                    runtime_instance_id="runtime-one",
                    paths=["resources/coding-tools-mcp/coding_tools_mcp/target.py"],
                check_definition_hash=check_hash,
            )
            self.assertEqual(accepted["policy_sha256"], granted["continuation"]["policy_sha256"])
            with self.assertRaises(RunContinuationError) as no_check:
                ledger.assert_run_continuation_execution(
                    run_id=run_id,
                    driver_generation=generation,
                    runtime_instance_id="runtime-one",
                    check_definition_hash="f" * 64,
                )
            self.assertEqual(no_check.exception.code, "RUN_CONTINUATION_CHECK_DENIED")

            reserved = ledger.reserve_run_continuation_action(
                run_id=run_id,
                driver_generation=generation,
                runtime_instance_id="runtime-one",
                action_kind="proposal",
                request_hash="9" * 64,
                expected_action_seq=1,
            )
            self.assertTrue(reserved["reserved"])
            replay = ledger.reserve_run_continuation_action(
                run_id=run_id,
                driver_generation=generation,
                runtime_instance_id="runtime-one",
                action_kind="proposal",
                request_hash="9" * 64,
                expected_action_seq=1,
            )
            self.assertTrue(replay["idempotent"])
            completed = ledger.complete_run_continuation_action(
                run_id=run_id,
                driver_generation=generation,
                runtime_instance_id="runtime-one",
                action_id=reserved["action_id"],
                consumed_event_seq=42,
            )
            self.assertEqual(completed["consumed_event_seq"], 42)
            self.assertFalse(completed["pending_action_id"])

    def test_missing_expired_revoked_and_takeover_race_are_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger, run_id = self._ledger_with_run(root)
            with self.assertRaises(RunContinuationError) as missing:
                ledger.assert_run_continuation_execution(run_id=run_id, driver_generation=0, runtime_instance_id="runtime-missing")
            self.assertEqual(missing.exception.code, "RUN_CONTINUATION_GRANT_REQUIRED")
            ledger.issue_run_continuation(
                run_id=run_id,
                policy=policy(run_id, grant_request(max_duration_seconds=1)),
                issuer_receipt_sha256="e" * 64,
                now_unix_ms=3_000_000,
            )
            with self.assertRaises(RunContinuationError) as expired:
                ledger.claim_run_continuation(
                    run_id=run_id,
                    runtime_instance_id="runtime-expired",
                    expected_generation=0,
                    now_unix_ms=3_001_000,
                )
            self.assertEqual(expired.exception.code, "RUN_CONTINUATION_EXPIRED")

            # A fresh grant is permitted only after the old grant is explicitly revoked.
            ledger.set_run_continuation_state(run_id=run_id, action="revoke", reason="operator reset")
            regranted = ledger.issue_run_continuation(
                run_id=run_id,
                policy=policy(run_id),
                issuer_receipt_sha256="f" * 64,
                now_unix_ms=4_000_000,
            )
            self.assertEqual(regranted["continuation"]["policy_revision"], 2)

            def claim(name: str) -> dict[str, object]:
                peer = OrchestrationLedger(root)
                return peer.claim_run_continuation(
                    run_id=run_id,
                    runtime_instance_id=name,
                    expected_generation=0,
                    now_unix_ms=4_000_100,
                )

            with ThreadPoolExecutor(max_workers=2) as pool:
                claims = list(pool.map(claim, ("runtime-a", "runtime-b")))
            self.assertEqual(sum(bool(item["claimed"]) for item in claims), 1)
            self.assertEqual(sorted(str(item["reason"]) for item in claims), ["claimed", "stale_generation"])
            active = next(item for item in claims if item["claimed"])
            ledger.set_run_continuation_state(run_id=run_id, action="revoke", reason="user cancellation")
            with self.assertRaises(RunContinuationError) as revoked:
                ledger.assert_run_continuation_execution(
                    run_id=run_id,
                    driver_generation=int(active["continuation"]["driver_generation"]),
                    runtime_instance_id=str(active["continuation"]["claimed_runtime_instance"]),
                )
            self.assertEqual(revoked.exception.code, "RUN_CONTINUATION_REVOKED")

    def test_effect_journal_is_written_before_effect_and_is_immutable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger, run_id = self._ledger_with_run(root)
            ledger.issue_run_continuation(run_id=run_id, policy=policy(run_id), issuer_receipt_sha256="e" * 64)
            claim = ledger.claim_run_continuation(run_id=run_id, runtime_instance_id="runtime", expected_generation=0)
            generation = int(claim["continuation"]["driver_generation"])
            action = ledger.reserve_run_continuation_action(
                run_id=run_id,
                driver_generation=generation,
                runtime_instance_id="runtime",
                action_kind="proposal",
                request_hash="9" * 64,
                evidence_hash="a" * 64,
                expected_action_seq=1,
            )["action_id"]
            manifest = {
                "backup_root": ".coding-tools/orchestration/continuation-effects/test-action",
                "files": [{
                    "path": "resources/coding-tools-mcp/coding_tools_mcp/target.py",
                    "preimage_sha256": "b" * 64,
                    "postimage_sha256": "c" * 64,
                    "backup_path": ".coding-tools/orchestration/continuation-effects/test-action/target.py",
                }],
            }
            first = ledger.prepare_run_continuation_effect(
                run_id=run_id, driver_generation=generation, runtime_instance_id="runtime", action_id=action, effect_kind="patch", manifest=manifest,
            )
            self.assertTrue(first["prepared"])
            replay = ledger.prepare_run_continuation_effect(
                run_id=run_id, driver_generation=generation, runtime_instance_id="runtime", action_id=action, effect_kind="patch", manifest=manifest,
            )
            self.assertTrue(replay["idempotent"])
            changed = {
                "backup_root": ".coding-tools/orchestration/continuation-effects/other",
                "files": [{
                    **manifest["files"][0],
                    "backup_path": ".coding-tools/orchestration/continuation-effects/other/target.py",
                }],
            }
            with self.assertRaises(RunContinuationError) as conflict:
                ledger.prepare_run_continuation_effect(
                    run_id=run_id, driver_generation=generation, runtime_instance_id="runtime", action_id=action, effect_kind="patch", manifest=changed,
                )
            self.assertEqual(conflict.exception.code, "RUN_CONTINUATION_EFFECT_CONFLICT")

    def test_effect_observation_is_idempotent_and_conflicting_terminal_state_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger, run_id = self._ledger_with_run(root)
            ledger.issue_run_continuation(run_id=run_id, policy=policy(run_id), issuer_receipt_sha256="e" * 64)
            claim = ledger.claim_run_continuation(run_id=run_id, runtime_instance_id="runtime", expected_generation=0)
            generation = int(claim["continuation"]["driver_generation"])
            action = ledger.reserve_run_continuation_action(
                run_id=run_id, driver_generation=generation, runtime_instance_id="runtime", action_kind="proposal", request_hash="9" * 64,
                evidence_hash="a" * 64, evidence_paths=["resources/coding-tools-mcp/coding_tools_mcp/target.py"], expected_action_seq=1,
            )["action_id"]
            manifest = {
                "backup_root": ".coding-tools/orchestration/continuation-effects/test-action",
                "files": [{
                    "path": "resources/coding-tools-mcp/coding_tools_mcp/target.py",
                    "preimage_sha256": "b" * 64,
                    "postimage_sha256": "c" * 64,
                    "backup_path": ".coding-tools/orchestration/continuation-effects/test-action/target.py",
                }],
            }
            ledger.prepare_run_continuation_effect(
                run_id=run_id, driver_generation=generation, runtime_instance_id="runtime", action_id=action, effect_kind="patch", manifest=manifest,
            )
            applied = ledger.record_run_continuation_effect_observation(
                run_id=run_id, driver_generation=generation, runtime_instance_id="runtime", action_id=action, status="applied",
            )
            self.assertEqual(applied["status"], "applied")
            replay = ledger.record_run_continuation_effect_observation(
                run_id=run_id, driver_generation=generation, runtime_instance_id="runtime", action_id=action, status="applied",
            )
            self.assertEqual(replay["status"], "applied")
            with self.assertRaises(RunContinuationError) as conflict:
                ledger.record_run_continuation_effect_observation(
                    run_id=run_id, driver_generation=generation, runtime_instance_id="runtime", action_id=action, status="not_applied",
                )
            self.assertEqual(conflict.exception.code, "RUN_CONTINUATION_EFFECT_CONFLICT")

    def test_read_evidence_cursor_and_next_turn_dispatch_identity_are_durable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger, run_id = self._ledger_with_run(root)
            ledger.issue_run_continuation(run_id=run_id, policy=policy(run_id), issuer_receipt_sha256="e" * 64)
            claim = ledger.claim_run_continuation(run_id=run_id, runtime_instance_id="runtime", expected_generation=0)
            generation = int(claim["continuation"]["driver_generation"])
            first = ledger.reserve_run_continuation_action(
                run_id=run_id, driver_generation=generation, runtime_instance_id="runtime", action_kind="proposal", request_hash="9" * 64,
                evidence_hash="a" * 64, evidence_paths=[], expected_action_seq=1,
            )
            action_one = str(first["action_id"])
            ledger.set_run_continuation_dispatch(
                run_id=run_id, driver_generation=generation, runtime_instance_id="runtime", action_id=action_one,
                lane_id="lane-test", thread_id="thread-test", turn_id="turn-one",
            )
            ledger.complete_run_continuation_action(
                run_id=run_id, driver_generation=generation, runtime_instance_id="runtime", action_id=action_one, consumed_event_seq=3,
            )
            raw = ledger._run_continuation_get_raw(run_id)
            assert raw is not None
            second = ledger.reserve_run_continuation_action(
                run_id=run_id, driver_generation=generation, runtime_instance_id="runtime", action_kind="proposal", request_hash="8" * 64,
                evidence_hash="b" * 64, evidence_paths=["resources/coding-tools-mcp/coding_tools_mcp/target.py"],
                expected_action_seq=int(raw["next_action_seq"]),
            )
            action_two = str(second["action_id"])
            record = ledger.set_run_continuation_dispatch(
                run_id=run_id, driver_generation=generation, runtime_instance_id="runtime", action_id=action_two,
                lane_id="lane-test", thread_id="thread-test", turn_id="turn-two",
            )
            self.assertEqual(record["pending_dispatch_action_id"], action_two)
            self.assertEqual(record["pending_evidence_paths"], ["resources/coding-tools-mcp/coding_tools_mcp/target.py"])
            self.assertEqual(record["last_turn_id"], "turn-two")

    def test_claim_owner_expiry_and_renewal_fence_every_execution_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger, run_id = self._ledger_with_run(root)
            ledger.issue_run_continuation(
                run_id=run_id,
                policy=policy(run_id, grant_request(max_duration_seconds=120)),
                issuer_receipt_sha256="e" * 64,
                now_unix_ms=1_000,
            )
            claimed = ledger.claim_run_continuation(
                run_id=run_id,
                runtime_instance_id="runtime-one",
                expected_generation=0,
                now_unix_ms=1_000,
            )
            generation = int(claimed["continuation"]["driver_generation"])
            with self.assertRaises(RunContinuationError) as wrong_owner:
                ledger.assert_run_continuation_execution(
                    run_id=run_id,
                    driver_generation=generation,
                    runtime_instance_id="runtime-two",
                    now_unix_ms=2_000,
                )
            self.assertEqual(wrong_owner.exception.code, "RUN_CONTINUATION_CLAIM_OWNER_MISMATCH")
            renewed = ledger.renew_run_continuation_claim(
                run_id=run_id,
                runtime_instance_id="runtime-one",
                driver_generation=generation,
                now_unix_ms=30_000,
            )
            self.assertGreater(int(renewed["claim_expires_at_unix_ms"]), 80_000)
            ledger.assert_run_continuation_execution(
                run_id=run_id,
                driver_generation=generation,
                runtime_instance_id="runtime-one",
                now_unix_ms=70_000,
            )
            with self.assertRaises(RunContinuationError) as expired:
                ledger.assert_run_continuation_execution(
                    run_id=run_id,
                    driver_generation=generation,
                    runtime_instance_id="runtime-one",
                    now_unix_ms=90_000,
                )
            self.assertEqual(expired.exception.code, "RUN_CONTINUATION_CLAIM_EXPIRED")

    def test_patch_budget_is_atomic_per_action_and_exhaustion_blocks_a_second_effect(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger, run_id = self._ledger_with_run(root)
            ledger.issue_run_continuation(
                run_id=run_id,
                policy=policy(run_id, grant_request(max_patch_attempts=1)),
                issuer_receipt_sha256="e" * 64,
            )
            claimed = ledger.claim_run_continuation(run_id=run_id, runtime_instance_id="runtime", expected_generation=0)
            generation = int(claimed["continuation"]["driver_generation"])
            first = ledger.reserve_run_continuation_action(
                run_id=run_id, driver_generation=generation, runtime_instance_id="runtime", action_kind="proposal",
                request_hash="1" * 64, evidence_hash="a" * 64, expected_action_seq=1,
            )
            spent = ledger.consume_run_continuation_patch_attempt(
                run_id=run_id, driver_generation=generation, runtime_instance_id="runtime", action_id=str(first["action_id"]),
            )
            self.assertTrue(spent["consumed"])
            replay = ledger.consume_run_continuation_patch_attempt(
                run_id=run_id, driver_generation=generation, runtime_instance_id="runtime", action_id=str(first["action_id"]),
            )
            self.assertTrue(replay["idempotent"])
            completed = ledger.complete_run_continuation_action(
                run_id=run_id, driver_generation=generation, runtime_instance_id="runtime", action_id=str(first["action_id"]),
            )
            self.assertEqual(completed["remaining_patch_attempts"], 0)
            second = ledger.reserve_run_continuation_action(
                run_id=run_id, driver_generation=generation, runtime_instance_id="runtime", action_kind="proposal",
                request_hash="2" * 64, evidence_hash="b" * 64, expected_action_seq=int(completed["next_action_seq"]),
            )
            with self.assertRaises(RunContinuationError) as exhausted:
                ledger.consume_run_continuation_patch_attempt(
                    run_id=run_id, driver_generation=generation, runtime_instance_id="runtime", action_id=str(second["action_id"]),
                )
            self.assertEqual(exhausted.exception.code, "RUN_CONTINUATION_PATCH_BUDGET_EXHAUSTED")

    def test_controller_reconciliation_terminalizes_classified_effect_and_unblocks_regrant(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger, run_id = self._ledger_with_run(root)
            ledger.issue_run_continuation(run_id=run_id, policy=policy(run_id), issuer_receipt_sha256="e" * 64)
            claimed = ledger.claim_run_continuation(run_id=run_id, runtime_instance_id="runtime", expected_generation=0)
            generation = int(claimed["continuation"]["driver_generation"])
            action = ledger.reserve_run_continuation_action(
                run_id=run_id, driver_generation=generation, runtime_instance_id="runtime", action_kind="proposal",
                request_hash="9" * 64, evidence_hash="a" * 64, expected_action_seq=1,
            )["action_id"]
            manifest = {
                "backup_root": ".coding-tools/orchestration/continuation-effects/test-reconcile",
                "files": [{
                    "path": "resources/coding-tools-mcp/coding_tools_mcp/target.py",
                    "preimage_sha256": "b" * 64,
                    "postimage_sha256": "c" * 64,
                    "backup_path": ".coding-tools/orchestration/continuation-effects/test-reconcile/target.py",
                }],
            }
            ledger.prepare_run_continuation_effect(
                run_id=run_id, driver_generation=generation, runtime_instance_id="runtime", action_id=str(action), effect_kind="patch", manifest=manifest,
            )
            with self.assertRaises(RunContinuationError) as active_driver:
                ledger.reconcile_run_continuation_pending_action(
                    run_id=run_id,
                    action_id=str(action),
                    effect_status="applied",
                    recovery_reason="effect_reobserved_proof_outcome_unknown",
                    controller_fencing_token=7,
                )
            self.assertEqual(active_driver.exception.code, "RUN_CONTINUATION_DRIVER_ACTIVE")
            ledger.set_run_continuation_state(run_id=run_id, action="revoke", reason="lost driver")
            with self.assertRaises(RunContinuationError) as ordinary_observation:
                ledger.record_run_continuation_effect_observation(
                    run_id=run_id, driver_generation=generation, runtime_instance_id="runtime", action_id=str(action), status="applied",
                )
            self.assertEqual(ordinary_observation.exception.code, "RUN_CONTINUATION_REVOKED")
            reconciled = ledger.reconcile_run_continuation_pending_action(
                run_id=run_id,
                action_id=str(action),
                effect_status="applied",
                recovery_reason="effect_reobserved_proof_outcome_unknown",
                controller_fencing_token=7,
            )
            self.assertFalse(reconciled["pending_action_id"])
            effect = ledger.get_run_continuation_effect(str(action))
            assert effect is not None
            self.assertEqual(effect["status"], "applied")
            regranted = ledger.issue_run_continuation(
                run_id=run_id,
                policy=policy(run_id),
                issuer_receipt_sha256="f" * 64,
            )
            self.assertEqual(regranted["status"], "GRANTED")

    def test_policy_rejects_scope_shell_and_definition_hash_forgery(self) -> None:
        with self.assertRaises(RunContinuationError) as protected:
            policy("run-test", grant_request(write_paths=[".coding-tools/orchestration/ledger.sqlite3"]))
        self.assertEqual(protected.exception.code, "RUN_CONTINUATION_SCOPE_PROTECTED")
        forged = check_definition()
        forged["definition_hash"] = "0" * 64
        with self.assertRaises(RunContinuationError) as check:
            policy("run-test", grant_request(approved_checks=[forged]))
        self.assertEqual(check.exception.code, "RUN_CONTINUATION_CHECK_HASH_MISMATCH")
        shell = check_definition()
        shell["argv"] = ["powershell", "-Command", "pytest"]
        shell["definition_hash"] = digest({key: shell[key] for key in ("check_id", "argv", "cwd", "environment_hash")})
        with self.assertRaises(RunContinuationError) as shell_error:
            policy("run-test", grant_request(approved_checks=[shell]))
        self.assertEqual(shell_error.exception.code, "RUN_CONTINUATION_CHECK_INVALID")


class RunContinuationSurfaceTests(unittest.TestCase):
    def test_prompt_requires_one_json_object_while_mcp_retains_strict_typed_parser(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict("os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
            runtime = Runtime(Path(directory))
            try:
                prompt = runtime._run_continuation_prompt(
                    policy=policy("run-test"),
                    evidence={"source_identity": {"base_head": "a" * 40}},
                    evidence_hash="1" * 64,
                )
                packet = json.loads(prompt.removeprefix("Bounded durable continuation packet:\n"))
                encoding = packet["continuation_contract"]["response_encoding"]
                self.assertIn("one JSON object", encoding["format"])
                self.assertIn("begin with {", encoding["format"])
                self.assertIn("invalid JSON is rejected", encoding["format"])
                self.assertEqual(encoding["common_required"], ["kind", "reason", "evidence_hash"])
                self.assertEqual(encoding["kinds"]["PATCH"]["required"], ["selected_check_hashes"])
                self.assertEqual(packet["evidence_hash"], "1" * 64)
                with self.assertRaises(RunContinuationError) as malformed:
                    parse_run_continuation_proposal(
                        "not a JSON object",
                        expected_evidence_hash="1" * 64,
                        read_paths=[],
                        write_paths=[],
                        protected_paths=[],
                        approved_check_hashes=[],
                    )
                self.assertEqual(malformed.exception.code, "RUN_CONTINUATION_PROPOSAL_INVALID")
            finally:
                runtime.close()

    def test_proposal_contract_binds_current_evidence_and_cannot_expand_scope(self) -> None:
        evidence_hash = "1" * 64
        accepted = parse_run_continuation_proposal(
            {
                "kind": "PATCH",
                "reason": "The exact current preimage needs one bounded replacement.",
                "evidence_hash": evidence_hash,
                "replacements": [{"path": "resources/coding-tools-mcp/coding_tools_mcp/target.py", "old": "before", "new": "after"}],
                "new_files": [],
                "selected_check_hashes": ["2" * 64],
            },
            expected_evidence_hash=evidence_hash,
            read_paths=["resources/coding-tools-mcp/coding_tools_mcp/target.py"],
            write_paths=["resources/coding-tools-mcp/coding_tools_mcp/target.py"],
            protected_paths=["resources/coding-tools-mcp/coding_tools_mcp/server.py"],
            approved_check_hashes=["2" * 64],
        )
        self.assertEqual(accepted["kind"], "PATCH")
        with self.assertRaises(RunContinuationError) as stale:
            parse_run_continuation_proposal(
                {"kind": "READY", "reason": "looks done", "evidence_hash": "3" * 64},
                expected_evidence_hash=evidence_hash,
                read_paths=["resources/coding-tools-mcp/coding_tools_mcp/target.py"],
                write_paths=["resources/coding-tools-mcp/coding_tools_mcp/target.py"],
                protected_paths=[],
                approved_check_hashes=[],
            )
        self.assertEqual(stale.exception.code, "RUN_CONTINUATION_EVIDENCE_STALE")
        with self.assertRaises(RunContinuationError) as scope:
            parse_run_continuation_proposal(
                {"kind": "READ", "reason": "need extra file", "evidence_hash": evidence_hash, "read_requests": [{"path": "other.py"}]},
                expected_evidence_hash=evidence_hash,
                read_paths=["resources/coding-tools-mcp/coding_tools_mcp/target.py"],
                write_paths=["resources/coding-tools-mcp/coding_tools_mcp/target.py"],
                protected_paths=[],
                approved_check_hashes=[],
            )
        self.assertEqual(scope.exception.code, "RUN_CONTINUATION_READ_SCOPE_DENIED")

    def test_patch_requires_every_approved_check_not_a_model_selected_subset(self) -> None:
        first, second = check_definition("unit"), check_definition("integration")
        selected_one = {
            "kind": "PATCH",
            "reason": "The source change is bounded and the first check looks sufficient.",
            "evidence_hash": "a" * 64,
            "replacements": [{"path": "resources/coding-tools-mcp/coding_tools_mcp/target.py", "old": "before", "new": "after"}],
            "new_files": [],
            "selected_check_hashes": [first["definition_hash"]],
        }
        with self.assertRaises(RunContinuationError) as subset:
            parse_run_continuation_proposal(
                selected_one,
                expected_evidence_hash="a" * 64,
                read_paths=["resources/coding-tools-mcp/coding_tools_mcp/target.py"],
                write_paths=["resources/coding-tools-mcp/coding_tools_mcp/target.py"],
                protected_paths=[],
                approved_check_hashes=[first["definition_hash"], second["definition_hash"]],
            )
        self.assertEqual(subset.exception.code, "RUN_CONTINUATION_REQUIRED_CHECK_MISSING")
        accepted = parse_run_continuation_proposal(
            {**selected_one, "selected_check_hashes": [first["definition_hash"], second["definition_hash"]]},
            expected_evidence_hash="a" * 64,
            read_paths=["resources/coding-tools-mcp/coding_tools_mcp/target.py"],
            write_paths=["resources/coding-tools-mcp/coding_tools_mcp/target.py"],
            protected_paths=[],
            approved_check_hashes=[first["definition_hash"], second["definition_hash"]],
        )
        self.assertEqual(accepted["selected_check_hashes"], [first["definition_hash"], second["definition_hash"]])

    def test_schema_preserves_eight_tools_and_accepts_only_typed_grant(self) -> None:
        schemas = input_schemas()
        self.assertIn("run_continuation", schemas["task_control"]["properties"]["action"]["enum"])
        self.assertIn("start", schemas["task_control"]["properties"]["run_continuation_action"]["enum"])
        validate_arguments("agent_workflow", {"workflow": "bugfix", "phase": "prepare", "continuation": grant_request()})
        validate_arguments("agent_workflow", {"workflow": "resume", "phase": "resume", "continuation": "opaque-token"})
        with self.assertRaises(Exception):
            validate_arguments(
                "agent_workflow",
                {"workflow": "bugfix", "phase": "prepare", "continuation": {"action": "grant", "route": "mini"}},
            )

    def test_no_identity_cannot_issue_grant_or_turn_local_object_into_authority(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict("os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
            runtime = Runtime(Path(directory))
            try:
                with self.assertRaises(ToolFailure) as denied:
                    runtime.agent_workflow(
                        {
                            "workflow": "bugfix",
                            "phase": "prepare",
                            "objective": "bounded continuation preflight",
                            "contract_fingerprint": "a" * 64,
                            "problem_context": {"work_origin": "non_problem"},
                            "continuation": grant_request(),
                        }
                    )
                self.assertEqual(denied.exception.code, "RUN_CONTINUATION_CONTROLLER_REQUIRED")
                state = runtime.task_state.get()
                run_id = str((state.get("orchestration") or {}).get("run_id") or "")
                self.assertTrue(run_id)
                self.assertIsNone(runtime.orchestration_ledger.get_run_continuation(run_id))
                status = runtime.task_control({"action": "run_continuation", "run_continuation_action": "get", "run_id": run_id})
                self.assertEqual(status["status"], "MISSING")
            finally:
                runtime.close()

    def test_model_evidence_fails_closed_on_sensitive_problem_or_source_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict("os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
            root = Path(directory)
            source = root / "target.py"
            source.write_text("api" + "_key = 'placeholder'\n", encoding="utf-8")
            runtime = Runtime(root)
            try:
                behavior = runtime._loaded_behavior_identity()
                continuation_policy = build_run_continuation_policy(
                    grant_request(read_paths=["target.py"], write_paths=["target.py"]),
                    run_id="run-test",
                    workspace_id="workspace-test",
                    problem_id="problem-test",
                    problem_revision=1,
                    contract_fingerprint="b" * 64,
                    tool_contract_sha256=str(runtime.tool_contract["sha256"]),
                    runtime_behavior_fingerprint=str(behavior["fingerprint"]),
                    activation_epoch_id="epoch-test",
                    activation_admission="open",
                    issuer_client_id="chatweb-test",
                )
                with patch.object(runtime.orchestration_ledger, "problem_get_exact_revision", return_value={"capsule": {"summary": "bounded source repair"}}):
                    with self.assertRaises(ToolFailure) as source_denied:
                        runtime._run_continuation_canonical_evidence(
                            continuation_policy,
                            objective="repair one bounded source file",
                            selected_read_paths=["target.py"],
                        )
                self.assertEqual(source_denied.exception.code, "RUN_CONTINUATION_EVIDENCE_SENSITIVE")

                source.write_text("VALUE = 'safe'\n", encoding="utf-8")
                with patch.object(
                    runtime.orchestration_ledger,
                    "problem_get_exact_revision",
                    return_value={"capsule": {"summary": "auth" + "orization: Bearer placeholder"}},
                ):
                    with self.assertRaises(ToolFailure) as problem_denied:
                        runtime._run_continuation_canonical_evidence(
                            continuation_policy,
                            objective="repair one bounded source file",
                            selected_read_paths=["target.py"],
                        )
                self.assertEqual(problem_denied.exception.code, "RUN_CONTINUATION_EVIDENCE_SENSITIVE")
            finally:
                runtime.close()

    def test_effect_backups_and_reobservation_never_need_a_second_patch_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target.txt"
            target.write_text("before", encoding="utf-8")
            manifest = {
                "backup_root": ".coding-tools/orchestration/continuation-effects/action",
                "files": [
                    {
                        "path": "target.txt",
                        "preimage_sha256": hashlib.sha256(b"before").hexdigest(),
                        "postimage_sha256": hashlib.sha256(b"after").hexdigest(),
                        "backup_path": ".coding-tools/orchestration/continuation-effects/action/target.txt",
                    },
                    {
                        "path": "new.txt",
                        "preimage_sha256": "absent",
                        "postimage_sha256": hashlib.sha256(b"new").hexdigest(),
                        "backup_path": ".coding-tools/orchestration/continuation-effects/action/new.txt",
                    },
                ],
            }
            first = materialize_continuation_effect_backups(root, manifest)
            self.assertEqual(first["written"], 2)
            second = materialize_continuation_effect_backups(root, manifest)
            self.assertEqual(second["reused"], 2)
            self.assertEqual((root / ".coding-tools/orchestration/continuation-effects/action/target.txt").read_bytes(), b"before")
            target.write_text("after", encoding="utf-8")
            (root / "new.txt").write_text("new", encoding="utf-8")
            observed = observe_continuation_effect(root, manifest)
            self.assertEqual(observed["status"], "applied")
            self.assertTrue(observed["backup_complete"])

    def test_internal_structured_argv_uses_no_shell_and_is_not_a_public_escape_hatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict("os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
            runtime = Runtime(Path(directory))
            try:
                with self.assertRaises(ToolFailure) as denied:
                    runtime.exec_command({"_argv": [sys.executable, "--version"]})
                self.assertEqual(denied.exception.code, "INTERNAL_STRUCTURED_ARGV_DENIED")
                payload = runtime.exec_command({
                    "_continuation_internal": True,
                    "_argv": [sys.executable, "-c", "import sys; print(sys.argv[1])", "literal&&not-a-command"],
                    "yield_time_ms": 30_000,
                })
                self.assertEqual(payload["status"], "exited")
                self.assertEqual(payload["exit_code"], 0)
                self.assertIn("literal&&not-a-command", str(payload.get("stdout") or ""))
                self.assertEqual(len(continuation_execution_environment_hash()), 64)
            finally:
                runtime.close()

    def test_lost_bridge_ownership_pauses_instead_of_starting_a_duplicate_turn(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict("os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
            runtime = Runtime(Path(directory))
            try:
                run_id = runtime.orchestration_ledger.create_run(objective="continuation restart guard")
                runtime.orchestration_ledger.create_wave(run_id, execution_mode="deep_single_lane")
                behavior = runtime._loaded_behavior_identity()
                runtime_policy = build_run_continuation_policy(
                    grant_request(),
                    run_id=run_id,
                    workspace_id="workspace-test",
                    problem_id="problem-test",
                    problem_revision=1,
                    contract_fingerprint="b" * 64,
                    tool_contract_sha256=str(runtime.tool_contract["sha256"]),
                    runtime_behavior_fingerprint=str(behavior["fingerprint"]),
                    activation_epoch_id="epoch-test",
                    activation_admission="open",
                    issuer_client_id="chatweb-test",
                )
                runtime.orchestration_ledger.issue_run_continuation(
                    run_id=run_id, policy=runtime_policy, issuer_receipt_sha256="e" * 64,
                )
                claim = runtime.orchestration_ledger.claim_run_continuation(
                    run_id=run_id, runtime_instance_id=runtime._run_continuation_runtime_instance_id(), expected_generation=0,
                )
                generation = int(claim["continuation"]["driver_generation"])
                reserved = runtime.orchestration_ledger.reserve_run_continuation_action(
                    run_id=run_id, driver_generation=generation, runtime_instance_id=runtime._run_continuation_runtime_instance_id(), action_kind="proposal", request_hash="9" * 64,
                    evidence_hash="a" * 64, evidence_paths=[], expected_action_seq=1,
                )
                runtime.orchestration_ledger.set_run_continuation_dispatch(
                    run_id=run_id, driver_generation=generation, runtime_instance_id=runtime._run_continuation_runtime_instance_id(), action_id=str(reserved["action_id"]),
                    lane_id="lane-test", thread_id="thread-test", turn_id="turn-test",
                )
                with patch.object(runtime, "activation_admission_snapshot", return_value={"admission": "open", "activation_epoch_id": "epoch-current"}), patch.object(runtime._codex_bridge, "owns_thread", return_value=False):
                    observed = runtime._run_continuation_observe_driver(run_id=run_id)
                self.assertEqual(observed["status"], "DISPATCH_UNKNOWN")
                paused = runtime.orchestration_ledger._run_continuation_get_raw(run_id)
                assert paused is not None
                self.assertFalse(paused["enabled"])
                self.assertTrue(paused["pending_action_id"])
            finally:
                runtime.close()

    def test_terminal_read_dispatches_one_next_turn_on_the_same_owned_thread(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict("os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
            root = Path(directory)
            runtime = Runtime(root)
            try:
                identity = runtime._orchestration_workspace_identity(".")
                ctx = runtime.orchestration_control.begin(
                    objective="read one bounded continuation source file",
                    task_id="task-test",
                    execution_mode="deep_single_lane",
                    base_head=str(identity.get("base_head") or ""),
                    worktree_fp=str(identity.get("worktree_fp") or ""),
                    contract_fp="b" * 64,
                )
                behavior = runtime._loaded_behavior_identity()
                continuation_policy = build_run_continuation_policy(
                    grant_request(),
                    run_id=ctx.run_id,
                    workspace_id="workspace-test",
                    problem_id="problem-test",
                    problem_revision=1,
                    contract_fingerprint="b" * 64,
                    tool_contract_sha256=str(runtime.tool_contract["sha256"]),
                    runtime_behavior_fingerprint=str(behavior["fingerprint"]),
                    activation_epoch_id="epoch-test",
                    activation_admission="open",
                    issuer_client_id="chatweb-test",
                )
                runtime.orchestration_ledger.issue_run_continuation(
                    run_id=ctx.run_id, policy=continuation_policy, issuer_receipt_sha256="e" * 64,
                )
                claim = runtime.orchestration_ledger.claim_run_continuation(
                    run_id=ctx.run_id, runtime_instance_id=runtime._run_continuation_runtime_instance_id(), expected_generation=0,
                )
                generation = int(claim["continuation"]["driver_generation"])
                first = runtime.orchestration_ledger.reserve_run_continuation_action(
                    run_id=ctx.run_id,
                    driver_generation=generation,
                    runtime_instance_id=runtime._run_continuation_runtime_instance_id(),
                    action_kind="proposal",
                    request_hash="9" * 64,
                    evidence_hash="a" * 64,
                    evidence_paths=[],
                    expected_action_seq=1,
                )
                first_action_id = str(first["action_id"])
                runtime.orchestration_ledger.set_run_continuation_dispatch(
                    run_id=ctx.run_id,
                    driver_generation=generation,
                    runtime_instance_id=runtime._run_continuation_runtime_instance_id(),
                    action_id=first_action_id,
                    lane_id="lane-test",
                    thread_id="thread-test",
                    turn_id="turn-one",
                )
                proposal = {
                    "kind": "READ",
                    "reason": "The bounded source bytes are needed before proposing a patch.",
                    "evidence_hash": "a" * 64,
                    "read_requests": [{"path": "resources/coding-tools-mcp/coding_tools_mcp/target.py"}],
                }
                observation = {
                    "terminal": True,
                    "status": "completed",
                    "agent_text": json.dumps(proposal),
                    "next_cursor": 9,
                }
                with (
                    patch.object(runtime, "activation_admission_snapshot", return_value={"admission": "open", "activation_epoch_id": "epoch-current"}),
                    patch.object(runtime._codex_bridge, "owns_thread", return_value=True),
                    patch.object(runtime._codex_bridge, "observe", return_value=observation),
                    patch.object(runtime._codex_bridge, "continue_thread", return_value={"thread_id": "thread-test", "turn_id": "turn-two"}) as continued,
                    patch.object(runtime, "_run_continuation_current_evidence", return_value=({}, "b" * 64)),
                ):
                    result = runtime._run_continuation_observe_driver(run_id=ctx.run_id)
                self.assertEqual(result["status"], "PROPOSING")
                self.assertEqual(result["turn_id"], "turn-two")
                continued.assert_called_once()
                self.assertIsNone(continued.call_args.kwargs["output_schema"])
                updated = runtime.orchestration_ledger._run_continuation_get_raw(ctx.run_id)
                assert updated is not None
                self.assertEqual(updated["thread_id"], "thread-test")
                self.assertEqual(updated["last_turn_id"], "turn-two")
                self.assertEqual(updated["pending_evidence_paths"], ["resources/coding-tools-mcp/coding_tools_mcp/target.py"])
                self.assertNotEqual(updated["pending_action_id"], first_action_id)
                self.assertEqual(updated["consumed_event_seq"], 9)
            finally:
                runtime.close()

    def test_patch_context_drift_creates_no_effect_journal_or_backup(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict("os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
            root = Path(directory)
            (root / "target.py").write_text("before\n", encoding="utf-8")
            (root / "checks").mkdir()
            runtime = Runtime(root)
            try:
                identity = runtime._orchestration_workspace_identity(".")
                ctx = runtime.orchestration_control.begin(
                    objective="reject continuation patch after source drift",
                    task_id="task-test",
                    execution_mode="deep_single_lane",
                    base_head=str(identity.get("base_head") or ""),
                    worktree_fp=str(identity.get("worktree_fp") or ""),
                    contract_fp="b" * 64,
                )
                check = {
                    "check_id": "postimage-proof",
                    "argv": [sys.executable, "--version"],
                    "cwd": "checks",
                    "environment_hash": continuation_execution_environment_hash(),
                }
                check["definition_hash"] = digest(check)
                behavior = runtime._loaded_behavior_identity()
                continuation_policy = build_run_continuation_policy(
                    grant_request(
                        read_paths=["target.py"],
                        write_paths=["target.py"],
                        protected_paths=["resources/coding-tools-mcp/coding_tools_mcp/server.py"],
                        approved_checks=[check],
                    ),
                    run_id=ctx.run_id,
                    workspace_id="workspace-test",
                    problem_id="problem-test",
                    problem_revision=1,
                    contract_fingerprint="b" * 64,
                    tool_contract_sha256=str(runtime.tool_contract["sha256"]),
                    runtime_behavior_fingerprint=str(behavior["fingerprint"]),
                    activation_epoch_id="epoch-test",
                    activation_admission="open",
                    issuer_client_id="chatweb-test",
                )
                runtime.orchestration_ledger.issue_run_continuation(
                    run_id=ctx.run_id, policy=continuation_policy, issuer_receipt_sha256="e" * 64,
                )
                claim = runtime.orchestration_ledger.claim_run_continuation(
                    run_id=ctx.run_id, runtime_instance_id=runtime._run_continuation_runtime_instance_id(), expected_generation=0,
                )
                generation = int(claim["continuation"]["driver_generation"])
                reserved = runtime.orchestration_ledger.reserve_run_continuation_action(
                    run_id=ctx.run_id, driver_generation=generation, runtime_instance_id=runtime._run_continuation_runtime_instance_id(), action_kind="proposal", request_hash="9" * 64,
                    evidence_hash="a" * 64, evidence_paths=["target.py"], expected_action_seq=1,
                )
                action_id = str(reserved["action_id"])
                record = runtime.orchestration_ledger._run_continuation_get_raw(ctx.run_id)
                assert record is not None
                proposal = {
                    "kind": "PATCH",
                    "reason": "would replace the supplied preimage only if its run identity remained current",
                    "evidence_hash": "a" * 64,
                    "replacements": [{"path": "target.py", "old": "before", "new": "after"}],
                    "new_files": [],
                    "selected_check_hashes": [check["definition_hash"]],
                }
                drifted_identity = {**identity, "worktree_fp": "worktree-drift"}
                with patch.object(runtime, "_run_continuation_current_evidence", return_value=({}, "a" * 64)), patch.object(runtime, "_orchestration_workspace_identity", return_value=drifted_identity):
                    result = runtime._run_continuation_apply_patch(
                        record=record,
                        action_id=action_id,
                        proposal=proposal,
                        consumed_event_seq=7,
                    )
                self.assertEqual(result["status"], "REPLAN_REQUIRED")
                self.assertEqual(result["reason"], "RUN_CONTINUATION_EVIDENCE_STALE")
                self.assertEqual((root / "target.py").read_text(encoding="utf-8"), "before\n")
                self.assertIsNone(runtime.orchestration_ledger.get_run_continuation_effect(action_id))
                self.assertFalse((root / ".coding-tools/orchestration/continuation-effects" / action_id).exists())
            finally:
                runtime.close()

    def test_patch_proposal_journals_backup_runs_structured_proof_and_stops_at_accepting(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict("os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
            root = Path(directory)
            (root / "target.py").write_text("before\n", encoding="utf-8")
            (root / "checks").mkdir()
            runtime = Runtime(root)
            try:
                identity = runtime._orchestration_workspace_identity(".")
                ctx = runtime.orchestration_control.begin(
                    objective="apply one bounded continuation patch",
                    task_id="task-test",
                    execution_mode="deep_single_lane",
                    base_head=str(identity.get("base_head") or ""),
                    worktree_fp=str(identity.get("worktree_fp") or ""),
                    contract_fp="b" * 64,
                )
                check = {
                    "check_id": "postimage-proof",
                    "argv": [
                        sys.executable,
                        "-c",
                        "from pathlib import Path; assert Path('../target.py').read_text(encoding='utf-8') == 'after\\n'",
                    ],
                    "cwd": "checks",
                    "environment_hash": continuation_execution_environment_hash(),
                }
                check["definition_hash"] = digest(check)
                request = grant_request(
                    read_paths=["target.py"],
                    write_paths=["target.py"],
                    protected_paths=["resources/coding-tools-mcp/coding_tools_mcp/server.py"],
                    approved_checks=[check],
                )
                behavior = runtime._loaded_behavior_identity()
                continuation_policy = build_run_continuation_policy(
                    request,
                    run_id=ctx.run_id,
                    workspace_id="workspace-test",
                    problem_id="problem-test",
                    problem_revision=1,
                    contract_fingerprint="b" * 64,
                    tool_contract_sha256=str(runtime.tool_contract["sha256"]),
                    runtime_behavior_fingerprint=str(behavior["fingerprint"]),
                    activation_epoch_id="epoch-test",
                    activation_admission="open",
                    issuer_client_id="chatweb-test",
                )
                runtime.orchestration_ledger.issue_run_continuation(
                    run_id=ctx.run_id, policy=continuation_policy, issuer_receipt_sha256="e" * 64,
                )
                claim = runtime.orchestration_ledger.claim_run_continuation(
                    run_id=ctx.run_id, runtime_instance_id=runtime._run_continuation_runtime_instance_id(), expected_generation=0,
                )
                generation = int(claim["continuation"]["driver_generation"])
                reserved = runtime.orchestration_ledger.reserve_run_continuation_action(
                    run_id=ctx.run_id, driver_generation=generation, runtime_instance_id=runtime._run_continuation_runtime_instance_id(), action_kind="proposal", request_hash="9" * 64,
                    evidence_hash="a" * 64, evidence_paths=["target.py"], expected_action_seq=1,
                )
                record = runtime.orchestration_ledger._run_continuation_get_raw(ctx.run_id)
                assert record is not None
                proposal = {
                    "kind": "PATCH",
                    "reason": "replace the one supplied preimage and run the approved proof",
                    "evidence_hash": "a" * 64,
                    "replacements": [{"path": "target.py", "old": "before", "new": "after"}],
                    "new_files": [],
                    "selected_check_hashes": [check["definition_hash"]],
                }
                with patch.object(runtime, "_run_continuation_current_evidence", return_value=({}, "a" * 64)):
                    result = runtime._run_continuation_apply_patch(
                        record=record,
                        action_id=str(reserved["action_id"]),
                        proposal=proposal,
                        consumed_event_seq=7,
                    )
                self.assertEqual(result["status"], "ACCEPTING")
                self.assertEqual((root / "target.py").read_text(encoding="utf-8"), "after\n")
                effect = runtime.orchestration_ledger.get_run_continuation_effect(str(reserved["action_id"]))
                assert effect is not None
                self.assertEqual(effect["status"], "applied")
                self.assertTrue((root / effect["manifest"]["files"][0]["backup_path"]).is_file())
                recovered = runtime.orchestration_control.snapshot(ctx.run_id)
                assert recovered is not None
                self.assertEqual(recovered.state, "ACCEPTING")
            finally:
                runtime.close()

    def test_failed_proof_dispatches_one_bounded_repair_turn_then_reaches_accepting(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict("os.environ", {"CODING_TOOLS_MCP_TOOL_MODE": "smart"}):
            root = Path(directory)
            (root / "target.py").write_text("before\n", encoding="utf-8")
            (root / "checks").mkdir()
            runtime = Runtime(root)
            try:
                identity = runtime._orchestration_workspace_identity(".")
                ctx = runtime.orchestration_control.begin(
                    objective="repair one failed continuation proof without another controller request",
                    task_id="task-test",
                    execution_mode="deep_single_lane",
                    base_head=str(identity.get("base_head") or ""),
                    worktree_fp=str(identity.get("worktree_fp") or ""),
                    contract_fp="b" * 64,
                )
                check = {
                    "check_id": "postimage-proof",
                    "argv": [
                        sys.executable,
                        "-c",
                        "from pathlib import Path; assert Path('../target.py').read_text(encoding='utf-8') == 'correct\\n'",
                    ],
                    "cwd": "checks",
                    "environment_hash": continuation_execution_environment_hash(),
                }
                check["definition_hash"] = digest(check)
                behavior = runtime._loaded_behavior_identity()
                continuation_policy = build_run_continuation_policy(
                    grant_request(
                        read_paths=["target.py"],
                        write_paths=["target.py"],
                        protected_paths=["resources/coding-tools-mcp/coding_tools_mcp/server.py"],
                        approved_checks=[check],
                        max_patch_attempts=2,
                    ),
                    run_id=ctx.run_id,
                    workspace_id="workspace-test",
                    problem_id="problem-test",
                    problem_revision=1,
                    contract_fingerprint="b" * 64,
                    tool_contract_sha256=str(runtime.tool_contract["sha256"]),
                    runtime_behavior_fingerprint=str(behavior["fingerprint"]),
                    activation_epoch_id="epoch-test",
                    activation_admission="open",
                    issuer_client_id="chatweb-test",
                )
                runtime.orchestration_ledger.issue_run_continuation(
                    run_id=ctx.run_id, policy=continuation_policy, issuer_receipt_sha256="e" * 64,
                )
                claim = runtime.orchestration_ledger.claim_run_continuation(
                    run_id=ctx.run_id,
                    runtime_instance_id=runtime._run_continuation_runtime_instance_id(),
                    expected_generation=0,
                )
                generation = int(claim["continuation"]["driver_generation"])
                first = runtime.orchestration_ledger.reserve_run_continuation_action(
                    run_id=ctx.run_id,
                    driver_generation=generation,
                    runtime_instance_id=runtime._run_continuation_runtime_instance_id(),
                    action_kind="proposal",
                    request_hash="9" * 64,
                    evidence_hash="a" * 64,
                    evidence_paths=["target.py"],
                    expected_action_seq=1,
                )
                first_action_id = str(first["action_id"])
                runtime.orchestration_ledger.set_run_continuation_dispatch(
                    run_id=ctx.run_id,
                    driver_generation=generation,
                    runtime_instance_id=runtime._run_continuation_runtime_instance_id(),
                    action_id=first_action_id,
                    lane_id="lane-test",
                    thread_id="thread-test",
                    turn_id="turn-one",
                )
                first_record = runtime.orchestration_ledger._run_continuation_get_raw(ctx.run_id)
                assert first_record is not None
                wrong_patch = {
                    "kind": "PATCH",
                    "reason": "The exact preimage is replaced with the first bounded repair candidate.",
                    "evidence_hash": "a" * 64,
                    "replacements": [{"path": "target.py", "old": "before", "new": "wrong"}],
                    "new_files": [],
                    "selected_check_hashes": [check["definition_hash"]],
                }
                original_wave_id = ctx.wave_id
                with (
                    patch.object(runtime, "_run_continuation_current_evidence", return_value=({}, "a" * 64)),
                    patch.object(runtime._codex_bridge, "owns_thread", return_value=True),
                    patch.object(runtime._codex_bridge, "continue_thread", return_value={"thread_id": "thread-test", "turn_id": "turn-two"}) as continued,
                ):
                    failed = runtime._run_continuation_apply_patch(
                        record=first_record,
                        action_id=first_action_id,
                        proposal=wrong_patch,
                        consumed_event_seq=4,
                    )
                self.assertEqual(failed["status"], "PROPOSING")
                self.assertTrue(failed["technical_replan"])
                self.assertNotEqual(failed["wave_id"], original_wave_id)
                self.assertEqual((root / "target.py").read_text(encoding="utf-8"), "wrong\n")
                continued.assert_called_once()
                self.assertIsNone(continued.call_args.kwargs["output_schema"])
                repair_record = runtime.orchestration_ledger._run_continuation_get_raw(ctx.run_id)
                assert repair_record is not None
                self.assertEqual(repair_record["pending_replan"]["failure"], "CHECK_FAILED")
                correct_patch = {
                    "kind": "PATCH",
                    "reason": "The failed postimage is corrected using the same immutable scope and proof set.",
                    "evidence_hash": str(repair_record["pending_evidence_hash"]),
                    "replacements": [{"path": "target.py", "old": "wrong", "new": "correct"}],
                    "new_files": [],
                    "selected_check_hashes": [check["definition_hash"]],
                }
                repair_observation = {
                    "terminal": True,
                    "status": "completed",
                    "agent_text": json.dumps(correct_patch),
                    "next_cursor": 8,
                }
                with (
                    patch.object(runtime, "activation_admission_snapshot", return_value={"admission": "open", "activation_epoch_id": "epoch-current"}),
                    patch.object(runtime, "_run_continuation_current_evidence", return_value=({}, "a" * 64)),
                    patch.object(runtime._codex_bridge, "owns_thread", return_value=True),
                    patch.object(runtime._codex_bridge, "observe", return_value=repair_observation),
                ):
                    repaired = runtime._run_continuation_observe_driver(run_id=ctx.run_id)
                self.assertEqual(repaired["status"], "ACCEPTING")
                self.assertEqual((root / "target.py").read_text(encoding="utf-8"), "correct\n")
                final_record = runtime.orchestration_ledger._run_continuation_get_raw(ctx.run_id)
                assert final_record is not None
                self.assertEqual(final_record["remaining_patch_attempts"], 0)
                accepted = runtime.orchestration_control.snapshot(ctx.run_id)
                assert accepted is not None
                self.assertEqual(accepted.state, "ACCEPTING")
            finally:
                runtime.close()


if __name__ == "__main__":
    unittest.main()
