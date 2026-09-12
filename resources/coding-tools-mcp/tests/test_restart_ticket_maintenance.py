from __future__ import annotations

import unittest

from coding_tools_mcp.restart_ticket import (
    EXACT_STALE_RUN_MAX_IDS,
    PROBLEM_LINEAGE_SCHEMA_V12_REASON,
    SUPERVISOR_RESTART_REASON_MAX_CHARS,
    build_supervisor_restart_ticket,
    is_exact_stale_run_maintenance_reason,
    is_problem_lineage_schema_v12_maintenance_reason,
    is_workspace_maintenance_reason,
    supervisor_restart_ticket_matches,
)


class RestartTicketMaintenanceTests(unittest.TestCase):
    @staticmethod
    def _reason(count: int) -> str:
        run_ids = [f"{index:032x}" for index in range(count)]
        return "exact_stale_runs:" + ",".join(run_ids)

    def test_full_exact_stale_batch_is_preserved_without_truncation(self) -> None:
        now_ms = 1_700_000_000_000
        reason = self._reason(EXACT_STALE_RUN_MAX_IDS)
        self.assertGreater(len(reason), SUPERVISOR_RESTART_REASON_MAX_CHARS)
        self.assertTrue(is_exact_stale_run_maintenance_reason(reason))

        ticket = build_supervisor_restart_ticket(
            ticket_id="restart-exact-stale-ticket-0001",
            now_ms=now_ms,
            workspace="C:\\work\\one",
            process_instance_id="process-one",
            server_instance_id="server-one",
            tool_contract_sha256="e" * 64,
            reason=reason,
            allow_acceptance_pending=True,
            target_workspace="C:\\work\\two",
        )
        self.assertEqual(ticket["reason"], reason)
        self.assertEqual(ticket["target_workspace"], "C:\\work\\two")
        self.assertIs(ticket["allow_acceptance_pending"], True)
        self.assertTrue(
            supervisor_restart_ticket_matches(
                ticket,
                now_ms=now_ms + 3_000,
                workspace="C:\\work\\one",
                process_instance_id="process-one",
                server_instance_id="server-one",
                tool_contract_sha256="e" * 64,
                fence_operation_id="restart-exact-stale-ticket-0001",
                allow_acceptance_pending=True,
                target_workspace="C:\\work\\two",
            )
        )
        self.assertFalse(
            supervisor_restart_ticket_matches(
                ticket,
                now_ms=now_ms + 3_000,
                workspace="C:\\work\\one",
                process_instance_id="process-one",
                server_instance_id="server-one",
                tool_contract_sha256="e" * 64,
                fence_operation_id="restart-exact-stale-ticket-0001",
                allow_acceptance_pending=True,
                target_workspace="C:\\work\\three",
            )
        )
        self.assertFalse(
            supervisor_restart_ticket_matches(
                ticket,
                now_ms=now_ms + 3_000,
                workspace="C:\\work\\one",
                process_instance_id="process-one",
                server_instance_id="server-one",
                tool_contract_sha256="e" * 64,
                fence_operation_id="restart-exact-stale-ticket-0001",
                allow_acceptance_pending=False,
                target_workspace="C:\\work\\two",
            )
        )

    def test_invalid_exact_stale_batches_fail_before_ticket_installation(self) -> None:
        invalid = (
            "exact_stale_runs:not-a-run-id",
            self._reason(EXACT_STALE_RUN_MAX_IDS + 1),
            "exact_stale_runs:" + "a" * 32 + "," + "a" * 32,
        )
        for reason in invalid:
            with self.subTest(reason=reason[:80]):
                self.assertFalse(is_exact_stale_run_maintenance_reason(reason))
                with self.assertRaises(ValueError):
                    build_supervisor_restart_ticket(
                        ticket_id="restart-exact-stale-ticket-0002",
                        now_ms=1_700_000_000_000,
                        workspace="C:\\work\\one",
                        process_instance_id="process-one",
                        server_instance_id="server-one",
                        tool_contract_sha256="e" * 64,
                        reason=reason,
                    )

    def test_ordinary_restart_reason_limit_is_unchanged(self) -> None:
        long_reason = "x" * (SUPERVISOR_RESTART_REASON_MAX_CHARS + 100)
        ticket = build_supervisor_restart_ticket(
            ticket_id="restart-ordinary-reason-0001",
            now_ms=1_700_000_000_000,
            workspace="C:\\work\\one",
            process_instance_id="process-one",
            server_instance_id="server-one",
            tool_contract_sha256="e" * 64,
            reason=long_reason,
        )
        self.assertEqual(len(ticket["reason"]), SUPERVISOR_RESTART_REASON_MAX_CHARS)

    def test_problem_lineage_v12_maintenance_preserves_exact_target_workspace(self) -> None:
        now_ms = 1_700_000_000_000
        reason = PROBLEM_LINEAGE_SCHEMA_V12_REASON
        self.assertTrue(is_problem_lineage_schema_v12_maintenance_reason(reason))
        self.assertTrue(is_workspace_maintenance_reason(reason))
        ticket = build_supervisor_restart_ticket(
            ticket_id="restart-problem-lineage-v12-0001",
            now_ms=now_ms,
            workspace="C:\\work\\one",
            process_instance_id="process-one",
            server_instance_id="server-one",
            tool_contract_sha256="e" * 64,
            reason=reason,
            target_workspace="C:\\work\\two",
        )
        self.assertEqual(ticket["target_workspace"], "C:\\work\\two")
        self.assertTrue(
            supervisor_restart_ticket_matches(
                ticket,
                now_ms=now_ms + 3_000,
                workspace="C:\\work\\one",
                process_instance_id="process-one",
                server_instance_id="server-one",
                tool_contract_sha256="e" * 64,
                fence_operation_id="restart-problem-lineage-v12-0001",
                target_workspace="C:\\work\\two",
            )
        )
        self.assertFalse(
            supervisor_restart_ticket_matches(
                ticket,
                now_ms=now_ms + 3_000,
                workspace="C:\\work\\one",
                process_instance_id="process-one",
                server_instance_id="server-one",
                tool_contract_sha256="e" * 64,
                fence_operation_id="restart-problem-lineage-v12-0001",
                target_workspace="C:\\work\\three",
            )
        )

    def test_malformed_problem_lineage_maintenance_reason_is_rejected(self) -> None:
        for reason in ("problem_lineage_schema_v12:extra", "problem_lineage_schema_v120"):
            with self.subTest(reason=reason):
                self.assertFalse(is_problem_lineage_schema_v12_maintenance_reason(reason))
                with self.assertRaises(ValueError):
                    build_supervisor_restart_ticket(
                        ticket_id="restart-problem-lineage-v12-0002",
                        now_ms=1_700_000_000_000,
                        workspace="C:\\work\\one",
                        process_instance_id="process-one",
                        server_instance_id="server-one",
                        tool_contract_sha256="e" * 64,
                        reason=reason,
                        target_workspace="C:\\work\\two",
                    )


if __name__ == "__main__":
    unittest.main()
