from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import coding_tools_mcp.cross_session_continuity_report as cross_report
from coding_tools_mcp.controller_reattach import controller_identity
from coding_tools_mcp.cross_session_continuity_report import (
    CrossSessionContinuityFacts,
    cross_session_continuity_report,
)
from coding_tools_mcp.ledger_analysis import open_ledger_analysis_snapshot
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.problem_lineage import problem_outcome_receipt_id
from coding_tools_mcp.problem_resolution_economics import ProblemLineageFacts
from coding_tools_mcp.product_session_receipts import record_problem_product_session
from coding_tools_mcp.resolution_contract import (
    contract_sha256,
    normalize_resolution_envelope,
)


WORKSPACE_ID = "workspace-tg6"
SOURCE_FP = hashlib.sha256(b"source").hexdigest()
RUNTIME_FP = hashlib.sha256(b"runtime").hexdigest()
CORE_FP = hashlib.sha256(b"continuity-core").hexdigest()
SNAPSHOT_FP = hashlib.sha256(b"control-center-snapshot").hexdigest()

ENVELOPE = {
    "schema_version": 1,
    "direct_outcomes": [
        {"outcome_id": "outcome-1", "summary": "The exact Goal is resolved"}
    ],
    "relevant_invariants": ["No duplicate execution"],
    "truth_domains": ["source", "runtime"],
    "adjacent_risks": [],
    "excluded_scope": ["Unrelated problems"],
    "required_evidence": [
        {
            "evidence_id": "evidence-1",
            "kind": "runtime_read",
            "provenance": "exact accepted wave",
            "status": "observed",
        }
    ],
    "closure_falsification_probe": {
        "probe_id": "probe-tg6",
        "method": "Re-read the bounded outcome",
        "expected_failure_signal": "The exact outcome is contradicted",
        "executed": True,
        "result": "passed",
    },
}


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def contract(criteria: int = 5) -> dict[str, object]:
    return {
        "objective_summary": "Prove the TG6 cross-session journey",
        "acceptance_criteria": [
            {"criterion_id": f"criterion-{index}", "summary": f"Criterion {index} passes"}
            for index in range(1, criteria + 1)
        ],
        "protected_invariants": ["Eight public tools", "No duplicate execution"],
        "constraints": ["No transcript replay"],
        "unresolved_conditions": [],
    }


def gate(report: dict[str, object], identifier: str) -> dict[str, object]:
    return next(item for item in report["gates"] if item["gate_id"] == identifier)  # type: ignore[index,union-attr]


class CrossSessionContinuityReportTests(unittest.TestCase):
    def _fixture(
        self,
        root: Path,
        *,
        problem_id: str = "problem-tg6",
        criteria: int = 5,
    ) -> tuple[OrchestrationLedger, str, str]:
        ledger = OrchestrationLedger(root)
        ledger.migrate_problem_lineage_schema()
        opened = ledger.problem_record_event(
            {
                "operation": "open",
                "event_id": f"open-{problem_id}",
                "problem_id": problem_id,
                "task_id": f"task-{problem_id}",
                "task_class": "feature",
                "engineering_floor": "REQUIRED",
                "contract_capsule": contract(criteria),
                "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER",
                "evidence_level": "OBSERVED",
                "occurred_at": "2026-09-01T00:00:00Z",
                "occurred_at_source": "EXPLICIT_USER",
            },
            now="2026-09-01T00:00:01Z",
            authority_context="RUNTIME_EXPLICIT_USER",
        )
        fingerprint = opened["event"]["contract_fingerprint"]
        context = {
            "schema_version": 1,
            "work_origin": "problem",
            "resolution_claim": "full_problem",
            "problem_id": problem_id,
            "problem_revision": 1,
            "contract_fingerprint": fingerprint,
            "engineering_floor": "REQUIRED",
            "policy_eligible": False,
        }
        metadata = {
            "problem_resolution": context,
            "workspace_identity": {"workspace_id": WORKSPACE_ID},
        }
        run_id = ledger.create_run(objective="TG6 fixture", metadata=metadata)
        wave_id = ledger.create_wave(
            run_id,
            execution_mode="mcp_only",
            base_head="head",
            worktree_fp="worktree",
            contract_fp=str(fingerprint),
            metadata=metadata,
        )
        ledger.problem_record_event(
            {
                "operation": "link",
                "event_id": f"link-{problem_id}",
                "problem_id": problem_id,
                "problem_revision": 1,
                "run_id": run_id,
                "wave_id": wave_id,
                "relation_type": "ENGINEERING_ATTEMPT_BOUND",
                "provenance": "DETERMINISTIC_EVIDENCE",
                "evidence_level": "OBSERVED",
            },
            now="2026-09-01T00:00:02Z",
            authority_context="RUNTIME_BINDING",
        )
        return ledger, run_id, wave_id

    def _report(
        self,
        root: Path,
        *,
        problem_id: str = "problem-tg6",
        revision: int = 1,
    ) -> dict[str, object]:
        with open_ledger_analysis_snapshot(root) as snapshot:
            problems = ProblemLineageFacts.load(snapshot.reader)
            facts = CrossSessionContinuityFacts.load(snapshot.reader)
            return cross_session_continuity_report(
                snapshot.ledger,
                problems,
                facts,
                problem_id=problem_id,
                problem_revision=revision,
            )

    @staticmethod
    def _append(
        ledger: OrchestrationLedger,
        run_id: str,
        wave_id: str,
        event_type: str,
        payload: dict[str, object],
    ) -> dict[str, object]:
        return ledger.append_event(
            run_id,
            wave_id=wave_id,
            event_type=event_type,
            payload=payload,
        )

    def _session(
        self,
        ledger: OrchestrationLedger,
        run_id: str,
        wave_id: str,
        *,
        role: str,
        receipt_id: str,
        endpoint: str,
    ) -> dict[str, object]:
        return self._append(
            ledger,
            run_id,
            wave_id,
            "cross_session_chatweb_session_started",
            {
                "problem_id": "problem-tg6",
                "problem_revision": 1,
                "workspace_id": WORKSPACE_ID,
                "session_role": role,
                "receipt_type": "CHATWEB_PRODUCT_SESSION_GOAL_PURSUIT_V1",
                "product_session_receipt_id": receipt_id,
                "controller_endpoint_id": endpoint,
            },
        )

    @staticmethod
    def _checkpoint(
        ledger: OrchestrationLedger,
        problem_id: str = "problem-tg6",
        *,
        event_id: str = "knowledge-1",
        state: str = "state-1",
    ) -> dict[str, object]:
        return ledger.controller_record_knowledge_checkpoint(
            workspace_id=WORKSPACE_ID,
            problem_id=problem_id,
            problem_revision=1,
            material_event_kind="PROBLEM_OPENED",
            material_event_id=event_id,
            material_state_fingerprint=digest(state),
            capsule_fingerprint=digest("capsule-" + state),
            source_fingerprint=SOURCE_FP,
            runtime_behavior_fingerprint=RUNTIME_FP,
            created_at="2026-09-01T00:01:00+00:00",
        )

    @staticmethod
    def _client(
        ledger: OrchestrationLedger, label: str = "b"
    ) -> tuple[str, str]:
        owner = f"chatweb-{label}"
        client = ledger.upsert_hub_client(
            client_id=owner,
            client_type="chatweb",
            role="controller",
            status="online",
            session_instance=f"session-{label}",
            runtime_instance_id=f"runtime-{label}",
        )
        identity = controller_identity(client, owner)
        assert identity is not None
        return owner, identity["controller_endpoint_id"]

    def _ack_and_reattach(
        self,
        ledger: OrchestrationLedger,
        *,
        supplied_revision: int,
        label: str = "b",
        ack_id: str = "ack-b",
        reattach_id: str = "reattach-b",
    ) -> tuple[dict[str, object], dict[str, object], str]:
        owner, endpoint = self._client(ledger, label)
        ack = ledger.controller_ack_knowledge(
            ack_id=ack_id,
            workspace_id=WORKSPACE_ID,
            problem_id="problem-tg6",
            problem_revision=1,
            knowledge_revision=supplied_revision,
            controller_endpoint_id=endpoint,
            created_at="2026-09-01T00:02:00+00:00",
        )["ack"]
        receipt = ledger.controller_reattach_goal(
            reattach_id=reattach_id,
            workspace_id=WORKSPACE_ID,
            problem_id="problem-tg6",
            problem_revision=1,
            controller_endpoint_id=endpoint,
            owner_client_id=owner,
            ack_id=ack_id,
            ack_status=ack["status"],
            continuity_core_fingerprint=CORE_FP,
            source_fingerprint=SOURCE_FP,
            runtime_behavior_fingerprint=RUNTIME_FP,
        )
        return ack, receipt, endpoint

    @staticmethod
    def _job(
        ledger: OrchestrationLedger,
        run_id: str,
        wave_id: str,
        *,
        job_id: str = "job-tg6",
        command_id: str = "command-tg6",
    ) -> None:
        with ledger._lock, ledger._connect() as connection:
            connection.execute(
                """INSERT INTO managed_process_jobs(
                       job_id,run_id,wave_id,command_id,owner,checkout_id,resource_class,
                       process_instance_id,runtime_instance_id,lifecycle_state,
                       started_at,updated_at,metadata_json
                   ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    job_id,
                    run_id,
                    wave_id,
                    command_id,
                    "fixture",
                    "checkout",
                    "LIGHT",
                    "process",
                    "runtime",
                    "running",
                    "2026-09-01T00:03:00+00:00",
                    "2026-09-01T00:03:01+00:00",
                    "{}",
                ),
            )

    @staticmethod
    def _set_resolution_envelope(
        ledger: OrchestrationLedger, run_id: str, wave_id: str
    ) -> None:
        envelope = normalize_resolution_envelope(ENVELOPE)
        claim = {
            "problem_id": "problem-tg6",
            "problem_revision": 1,
            "resolution_envelope": envelope,
            "resolution_envelope_sha256": contract_sha256(envelope),
        }
        claim_sha = contract_sha256(claim)
        with ledger._lock, ledger._connect() as connection:
            row = connection.execute(
                "SELECT metadata_json FROM waves WHERE wave_id=?", (wave_id,)
            ).fetchone()
            metadata = json.loads(row["metadata_json"] or "{}")
            metadata["problem_resolution"]["resolution_envelope"] = envelope
            metadata["problem_resolution"]["resolution_envelope_sha256"] = contract_sha256(
                envelope
            )
            metadata["problem_resolution"]["outcome_claim"] = claim
            metadata["problem_resolution"]["outcome_claim_sha256"] = claim_sha
            connection.execute(
                "UPDATE waves SET metadata_json=? WHERE wave_id=?",
                (json.dumps(metadata, sort_keys=True, separators=(",", ":")), wave_id),
            )
        ledger.record_checkpoint(
            run_id=run_id,
            wave_id=wave_id,
            git_head="head",
            proof_fingerprint="proof-fingerprint",
            status="accepted",
            metadata={
                "problem_outcome_claim": claim,
                "problem_outcome_claim_sha256": claim_sha,
            },
        )

    @staticmethod
    def _confirm(
        ledger: OrchestrationLedger, run_id: str, wave_id: str
    ) -> None:
        ledger.problem_record_event(
            {
                "operation": "provisional_resolve",
                "event_id": "provisional-tg6",
                "problem_id": "problem-tg6",
                "problem_revision": 1,
                "run_id": run_id,
                "wave_id": wave_id,
                "provenance": "DETERMINISTIC_EVIDENCE",
                "evidence_level": "OBSERVED",
                "occurred_at": "2026-09-01T00:10:00Z",
                "occurred_at_source": "RUNTIME",
            },
            now="2026-09-01T00:10:01Z",
            authority_context="RUNTIME_EOCL",
        )
        receipt_id = problem_outcome_receipt_id(
            receipt_type="CHATWEB_EXPLICIT_USER_OUTCOME_V1",
            event_id="confirm-tg6",
            problem_id="problem-tg6",
            problem_revision=1,
            turn_id="turn-confirm",
            trace_id="trace-confirm",
        )
        ledger.problem_record_event(
            {
                "operation": "confirm",
                "event_id": "confirm-tg6",
                "problem_id": "problem-tg6",
                "problem_revision": 1,
                "feedback_intent": "CONFIRM_RESOLVED",
                "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER",
                "evidence_level": "OBSERVED",
                "turn_id": "turn-confirm",
                "trace_id": "trace-confirm",
                "outcome_receipt_type": "CHATWEB_EXPLICIT_USER_OUTCOME_V1",
                "outcome_receipt_id": receipt_id,
                "occurred_at": "2026-09-01T00:11:00Z",
                "occurred_at_source": "EXPLICIT_USER",
            },
            now="2026-09-01T00:11:01Z",
            authority_context="RUNTIME_OUTCOME_RECEIPT",
        )

    def test_inactive_problem_schema_is_typed_unavailable_and_writer_free(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger = OrchestrationLedger(root)
            before = hashlib.sha256(ledger.path.read_bytes()).hexdigest()
            report = self._report(root, problem_id="missing")
            after = hashlib.sha256(ledger.path.read_bytes()).hexdigest()
            self.assertEqual(report["status"], "INCOMPLETE")
            self.assertEqual(gate(report, "TG6-02")["status"], "UNAVAILABLE")
            self.assertTrue(report["policy"]["no_writer_or_schema_activation"])
            self.assertEqual(before, after)
            connection = sqlite3.connect(ledger.path)
            try:
                self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 9)
            finally:
                connection.close()

    def test_one_session_cannot_pass_as_cross_session(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger, run_id, wave_id = self._fixture(root)
            self._session(
                ledger,
                run_id,
                wave_id,
                role="A",
                receipt_id="product-session-a",
                endpoint="endpoint-a",
            )
            report = self._report(root)
            self.assertEqual(gate(report, "TG6-02")["status"], "PASS")
            self.assertEqual(gate(report, "TG6-10")["status"], "UNAVAILABLE")
            self.assertFalse(report["accepted_real_cross_session_continuity_receipt"])
            self.assertEqual(report["typed_product_session_receipts"]["status"], "UNAVAILABLE")

    def test_two_endpoint_observations_do_not_replace_reattach_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger, run_id, wave_id = self._fixture(root)
            self._checkpoint(ledger)
            _owner_a, endpoint_a = self._client(ledger, "a")
            _owner_b, endpoint_b = self._client(ledger, "b")
            session_a = self._session(
                ledger,
                run_id,
                wave_id,
                role="A",
                receipt_id="product-session-a",
                endpoint=endpoint_a,
            )
            core = self._append(
                ledger,
                run_id,
                wave_id,
                "continuity_core_recorded",
                {
                    "problem_id": "problem-tg6",
                    "problem_revision": 1,
                    "workspace_id": WORKSPACE_ID,
                    "continuity_core_fingerprint": CORE_FP,
                },
            )
            self._append(
                ledger,
                run_id,
                wave_id,
                "cross_session_chatweb_session_rotated",
                {
                    "problem_id": "problem-tg6",
                    "problem_revision": 1,
                    "receipt_type": "CHATWEB_PRODUCT_SESSION_ROTATION_V1",
                    "outgoing_product_session_receipt_id": "product-session-a",
                    "session_event_id": session_a["event_id"],
                    "core_event_id": core["event_id"],
                },
            )
            self._session(
                ledger,
                run_id,
                wave_id,
                role="B",
                receipt_id="product-session-b",
                endpoint=endpoint_b,
            )
            report = self._report(root)
            self.assertEqual(gate(report, "TG6-10")["status"], "PASS")
            self.assertNotEqual(gate(report, "TG6-13")["status"], "PASS")
            self.assertFalse(report["accepted_real_cross_session_continuity_receipt"])

    def test_host_product_session_rotation_records_ordered_typed_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger, run_id, wave_id = self._fixture(root)
            owner, _endpoint = self._client(ledger, "host")
            client = next(
                item for item in ledger.list_hub_clients(limit=20) if item["client_id"] == owner
            )
            problem_resolution = ledger.get_run(run_id)["metadata"]["problem_resolution"]
            first_receipt = "chatweb-product-session:" + "1" * 64
            second_receipt = "chatweb-product-session:" + "2" * 64
            first = record_problem_product_session(
                ledger,
                run_id=run_id,
                wave_id=wave_id,
                problem_resolution=problem_resolution,
                workspace_id=WORKSPACE_ID,
                claimed_host_turn={
                    "turn_id": "turn-a",
                    "trace_id": "trace-a",
                    "product_session_receipt_id": first_receipt,
                    "product_session_transition": "observed",
                },
                hub_client=client,
            )
            self.assertEqual(first["session_event"]["payload"]["session_role"], "A")
            core = self._append(
                ledger,
                run_id,
                wave_id,
                "continuity_core_recorded",
                {
                    "problem_id": "problem-tg6",
                    "problem_revision": 1,
                    "workspace_id": WORKSPACE_ID,
                    "continuity_core_fingerprint": CORE_FP,
                },
            )
            second = record_problem_product_session(
                ledger,
                run_id=run_id,
                wave_id=wave_id,
                problem_resolution=problem_resolution,
                workspace_id=WORKSPACE_ID,
                claimed_host_turn={
                    "turn_id": "turn-b",
                    "trace_id": "trace-b",
                    "product_session_receipt_id": second_receipt,
                    "prior_product_session_receipt_id": first_receipt,
                    "product_session_transition": "rotated",
                },
                hub_client=client,
            )
            rotation = second["rotation_event"]
            session_b = second["session_event"]
            self.assertEqual(rotation["payload"]["core_event_id"], core["event_id"])
            self.assertEqual(
                rotation["payload"]["outgoing_product_session_receipt_id"],
                first_receipt,
            )
            self.assertEqual(session_b["payload"]["session_role"], "B")
            self.assertGreater(session_b["seq"], rotation["seq"])

    def test_current_ack_and_exact_reattach_are_observed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger, _run_id, _wave_id = self._fixture(root)
            self._checkpoint(ledger)
            ack, receipt, _endpoint = self._ack_and_reattach(ledger, supplied_revision=1)
            report = self._report(root)
            self.assertEqual(ack["status"], "CURRENT")
            self.assertEqual(gate(report, "TG6-11")["status"], "PASS")
            self.assertEqual(gate(report, "TG6-12")["status"], "PASS")
            self.assertEqual(gate(report, "TG6-13")["status"], "PASS")
            self.assertIn(receipt["reattach_id"], gate(report, "TG6-13")["exact_receipt_ids"])

    def test_durable_reattach_receipt_survives_later_transport_session_rotation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger, _run_id, _wave_id = self._fixture(root)
            self._checkpoint(ledger)
            _ack, receipt, endpoint = self._ack_and_reattach(
                ledger, supplied_revision=1
            )
            owner = str(receipt["owner_client_id"])
            rotated = ledger.upsert_hub_client(
                client_id=owner,
                client_type="chatweb",
                role="controller",
                status="online",
                session_instance="session-b-rotated",
                runtime_instance_id="runtime-b-rotated",
            )
            self.assertNotEqual(
                controller_identity(rotated, owner)["controller_endpoint_id"], endpoint
            )

            report = self._report(root)
            self.assertEqual(gate(report, "TG6-13")["status"], "PASS")
            self.assertIn(
                receipt["reattach_id"], gate(report, "TG6-13")["exact_receipt_ids"]
            )

    def test_behind_ack_requires_complete_bounded_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger, _run_id, _wave_id = self._fixture(root)
            self._checkpoint(ledger, event_id="knowledge-1", state="state-1")
            self._checkpoint(ledger, event_id="knowledge-2", state="state-2")
            ack, _receipt, _endpoint = self._ack_and_reattach(
                ledger,
                supplied_revision=1,
                ack_id="ack-behind",
                reattach_id="reattach-behind",
            )
            report = self._report(root)
            self.assertEqual(ack["status"], "BEHIND")
            self.assertEqual(gate(report, "TG6-12")["status"], "PASS")
            self.assertEqual(len(gate(report, "TG6-12")["exact_receipt_ids"]), 2)

    def test_missing_no_advance_observation_stays_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger, run_id, wave_id = self._fixture(root)
            checkpoint = self._checkpoint(ledger)["checkpoint"]
            report = self._report(root)
            self.assertEqual(gate(report, "TG6-05")["status"], "UNAVAILABLE")
            self._append(
                ledger,
                run_id,
                wave_id,
                "controller_knowledge_no_advance_observed",
                {
                    "problem_id": "problem-tg6",
                    "problem_revision": 1,
                    "policy": "NO_ADVANCE",
                    "operation_count": 2,
                    "operation_receipt_ids": ["read-1", "status-1"],
                    "knowledge_revision_before": checkpoint["knowledge_revision"],
                    "knowledge_revision_after": checkpoint["knowledge_revision"],
                },
            )
            self.assertEqual(gate(self._report(root), "TG6-05")["status"], "PASS")

    def test_durable_job_identity_not_process_claim_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger, run_id, wave_id = self._fixture(root)
            self._append(
                ledger,
                run_id,
                wave_id,
                "process_seen",
                {"problem_id": "problem-tg6", "problem_revision": 1, "pid": 1234},
            )
            self.assertEqual(gate(self._report(root), "TG6-06")["status"], "INCOMPLETE")
            self._job(ledger, run_id, wave_id)
            report = self._report(root)
            self.assertEqual(gate(report, "TG6-06")["status"], "PASS")
            self.assertIn("job-tg6", gate(report, "TG6-06")["exact_receipt_ids"])

    def test_no_duplicate_execution_claim_requires_reobservation_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger, run_id, wave_id = self._fixture(root)
            self._job(ledger, run_id, wave_id)
            self.assertEqual(gate(self._report(root), "TG6-14")["status"], "UNAVAILABLE")
            self._append(
                ledger,
                run_id,
                wave_id,
                "managed_execution_reobserved",
                {
                    "problem_id": "problem-tg6",
                    "problem_revision": 1,
                    "job_id": "job-tg6",
                    "command_id": "wrong-command",
                    "duplicate_execution_started": False,
                },
            )
            self.assertEqual(gate(self._report(root), "TG6-14")["status"], "UNAVAILABLE")

    def test_at_least_five_criteria_are_required(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._fixture(root, criteria=4)
            report = self._report(root)
            self.assertEqual(gate(report, "TG6-01")["status"], "INCOMPLETE")
            self.assertEqual(gate(report, "TG6-01")["details"]["criteria_count"], 4)

    def test_replan_requires_matching_prior_failure_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger, run_id, wave_id = self._fixture(root)
            self._append(
                ledger,
                run_id,
                wave_id,
                "wave_replanned",
                {"reason": "proof_defect"},
            )
            clean_gate = gate(self._report(root), "TG6-03")
            self.assertEqual(clean_gate["status"], "PASS")
            self.assertFalse(clean_gate["details"]["applicable"])
            failure = self._append(
                ledger,
                run_id,
                wave_id,
                "failure_observed",
                {"failure_class": "contract_drift"},
            )
            self.assertEqual(gate(self._report(root), "TG6-03")["status"], "INCOMPLETE")
            replan = self._append(
                ledger,
                run_id,
                wave_id,
                "wave_replanned",
                {"reason": "contract_drift"},
            )
            matched_gate = gate(self._report(root), "TG6-03")
            self.assertEqual(matched_gate["status"], "PASS")
            receipts = matched_gate["exact_receipt_ids"]
            self.assertIn(failure["event_id"], receipts)
            self.assertIn(replan["event_id"], receipts)

            second_failure = self._append(
                ledger,
                run_id,
                wave_id,
                "failure_observed",
                {"failure_class": "contract_drift"},
            )
            unmatched_gate = gate(self._report(root), "TG6-03")
            self.assertEqual(unmatched_gate["status"], "INCOMPLETE")
            self.assertIn(
                second_failure["event_id"],
                unmatched_gate["details"]["unmatched_failure_event_ids"],
            )

    def test_clean_first_pass_requires_an_exact_problem_linked_run(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger = OrchestrationLedger(root)
            ledger.migrate_problem_lineage_schema()
            ledger.problem_record_event(
                {
                    "operation": "open",
                    "event_id": "open-problem-tg6",
                    "problem_id": "problem-tg6",
                    "task_id": "task-problem-tg6",
                    "task_class": "feature",
                    "engineering_floor": "REQUIRED",
                    "contract_capsule": contract(),
                    "provenance": "CONTROLLER_REPORTED_EXPLICIT_USER",
                    "evidence_level": "OBSERVED",
                    "occurred_at": "2026-09-01T00:00:00Z",
                    "occurred_at_source": "EXPLICIT_USER",
                },
                now="2026-09-01T00:00:01Z",
                authority_context="RUNTIME_EXPLICIT_USER",
            )
            missing_run_gate = gate(self._report(root), "TG6-03")
            self.assertEqual(missing_run_gate["status"], "INCOMPLETE")
            self.assertIsNone(missing_run_gate["details"]["applicable"])
            self.assertEqual(
                missing_run_gate["missing_reason"], "exact_problem_linked_run_missing"
            )

    def test_closure_and_independent_outcome_are_separate_required_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger, run_id, wave_id = self._fixture(root)
            report = self._report(root)
            self.assertEqual(gate(report, "TG6-17")["status"], "INCOMPLETE")
            self.assertEqual(gate(report, "TG6-18")["status"], "INCOMPLETE")
            self._set_resolution_envelope(ledger, run_id, wave_id)
            self._confirm(ledger, run_id, wave_id)
            report = self._report(root)
            self.assertEqual(gate(report, "TG6-17")["status"], "PASS")
            self.assertEqual(gate(report, "TG6-18")["status"], "PASS")

    def test_economics_unknowns_are_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._fixture(root)
            report = self._report(root)
            economics = report["economics"]
            self.assertEqual(economics["status"], "AVAILABLE")
            self.assertTrue(economics["unknowns_preserved"])
            journey = economics["journey"]
            self.assertEqual(journey["topology"]["rotation_count"]["status"], "UNAVAILABLE")
            self.assertIsNone(journey["topology"]["rotation_count"]["value"])

    def test_any_core_fact_truncation_fails_closed_without_partial_claim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger, run_id, wave_id = self._fixture(root)
            self._append(
                ledger,
                run_id,
                wave_id,
                "event-one",
                {"problem_id": "problem-tg6", "problem_revision": 1},
            )
            self._append(
                ledger,
                run_id,
                wave_id,
                "event-two",
                {"problem_id": "problem-tg6", "problem_revision": 1},
            )
            with patch.dict(cross_report._FACT_LIMITS, {"events": 1}, clear=False):
                report = self._report(root)
            self.assertEqual(report["status"], "FACT_WINDOW_TRUNCATED")
            self.assertTrue(report["no_partial_cross_session_claim"])
            self.assertEqual(report["gate_counts"]["FACT_WINDOW_TRUNCATED"], 19)
            self.assertEqual(report["economics"]["status"], "UNAVAILABLE")

    def test_exact_revision_and_problem_isolation_prevent_foreign_leakage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger, _run_id, _wave_id = self._fixture(root)
            foreign, foreign_run, foreign_wave = self._fixture(
                root, problem_id="problem-foreign", criteria=5
            )
            self._append(
                foreign,
                foreign_run,
                foreign_wave,
                "cross_session_chatweb_session_started",
                {
                    "problem_id": "problem-foreign",
                    "problem_revision": 1,
                    "workspace_id": WORKSPACE_ID,
                    "session_role": "A",
                    "receipt_type": "CHATWEB_PRODUCT_SESSION_GOAL_PURSUIT_V1",
                    "product_session_receipt_id": "foreign-session-receipt",
                },
            )
            report = self._report(root)
            encoded = json.dumps(report, sort_keys=True)
            self.assertNotIn("foreign-session-receipt", encoded)
            self.assertNotIn(foreign_run, encoded)
            self.assertEqual(report["problem_identity"]["problem_id"], "problem-tg6")

    def test_full_typed_journey_is_the_only_overall_pass_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger, run_id, first_wave = self._fixture(root)
            _owner_a, endpoint_a = self._client(ledger, "a")
            self._session(
                ledger,
                run_id,
                first_wave,
                role="A",
                receipt_id="product-session-a",
                endpoint=endpoint_a,
            )
            self._append(
                ledger,
                run_id,
                first_wave,
                "failure_observed",
                {"failure_class": "proof_defect"},
            )
            ledger.finish_wave(first_wave, status="replanned", metadata={"reason": "proof_defect"})
            metadata = ledger.get_run(run_id)["metadata"]
            metadata["problem_resolution"]["resolution_envelope"] = ENVELOPE
            second_wave = ledger.create_wave(
                run_id,
                execution_mode="mcp_only",
                base_head="head",
                worktree_fp="worktree-2",
                contract_fp=metadata["problem_resolution"]["contract_fingerprint"],
                metadata=metadata,
            )
            self._append(
                ledger,
                run_id,
                second_wave,
                "wave_replanned",
                {"reason": "proof_defect", "execution_mode": "mcp_only"},
            )
            checkpoint = self._checkpoint(ledger)["checkpoint"]
            self._append(
                ledger,
                run_id,
                second_wave,
                "controller_knowledge_no_advance_observed",
                {
                    "problem_id": "problem-tg6",
                    "problem_revision": 1,
                    "policy": "NO_ADVANCE",
                    "operation_count": 2,
                    "operation_receipt_ids": ["read-receipt", "status-receipt"],
                    "knowledge_revision_before": checkpoint["knowledge_revision"],
                    "knowledge_revision_after": checkpoint["knowledge_revision"],
                },
            )
            self._job(ledger, run_id, second_wave)
            self._append(
                ledger,
                run_id,
                second_wave,
                "execution_control_center_progress_observed",
                {
                    "problem_id": "problem-tg6",
                    "problem_revision": 1,
                    "observer_plane": "execution_control_center",
                    "progress_visible": True,
                    "snapshot_fingerprint": SNAPSHOT_FP,
                },
            )
            core = self._append(
                ledger,
                run_id,
                second_wave,
                "continuity_core_recorded",
                {
                    "problem_id": "problem-tg6",
                    "problem_revision": 1,
                    "workspace_id": WORKSPACE_ID,
                    "continuity_core_fingerprint": CORE_FP,
                },
            )
            self._append(
                ledger,
                run_id,
                second_wave,
                "cross_session_chatweb_session_rotated",
                {
                    "problem_id": "problem-tg6",
                    "problem_revision": 1,
                    "receipt_type": "CHATWEB_PRODUCT_SESSION_ROTATION_V1",
                    "outgoing_product_session_receipt_id": "product-session-a",
                    "core_event_id": core["event_id"],
                },
            )
            ack, reattach, endpoint_b = self._ack_and_reattach(
                ledger, supplied_revision=1
            )
            session_b = self._session(
                ledger,
                run_id,
                second_wave,
                role="B",
                receipt_id="product-session-b",
                endpoint=endpoint_b,
            )
            self._append(
                ledger,
                run_id,
                second_wave,
                "managed_execution_reobserved",
                {
                    "problem_id": "problem-tg6",
                    "problem_revision": 1,
                    "job_id": "job-tg6",
                    "command_id": "command-tg6",
                    "reattach_id": reattach["reattach_id"],
                    "duplicate_execution_started": False,
                    "session_b_event_id": session_b["event_id"],
                },
            )
            proof = ledger.record_proof(
                run_id=run_id,
                wave_id=second_wave,
                stage_id="focused",
                stage_version="1",
                input_fingerprint="tg6-proof",
                status="passed",
            )
            criteria = [f"criterion-{index}" for index in range(1, 6)]
            self._append(
                ledger,
                run_id,
                second_wave,
                "goal_reconstruction_observed",
                {
                    "problem_id": "problem-tg6",
                    "problem_revision": 1,
                    "criteria_total": 5,
                    "criterion_ids": criteria,
                    "proof_ids": [proof],
                    "next_gap_id": "criterion-5",
                    "next_action": "Complete criterion-5",
                    "transcript_replayed": False,
                    "ack_id": ack["ack_id"],
                },
            )
            self._append(
                ledger,
                run_id,
                second_wave,
                "remaining_criterion_completed",
                {
                    "problem_id": "problem-tg6",
                    "problem_revision": 1,
                    "criterion_id": "criterion-5",
                    "proof_id": proof,
                },
            )
            self._set_resolution_envelope(ledger, run_id, second_wave)
            self._confirm(ledger, run_id, second_wave)
            report = self._report(root)
            self.assertEqual(report["status"], "PASS", report["gates"])
            self.assertTrue(report["accepted_real_cross_session_continuity_receipt"])
            self.assertFalse(report["no_partial_cross_session_claim"])
            self.assertEqual(report["gate_counts"]["PASS"], 19)
            self.assertEqual(report["typed_product_session_receipts"]["count"], 2)


if __name__ == "__main__":
    unittest.main()
