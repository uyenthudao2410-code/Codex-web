from __future__ import annotations

import unittest

from coding_tools_mcp.restart_ticket import (
    EXACT_STALE_RUN_MAX_IDS,
    SUPERVISOR_RESTART_REASON_MAX_CHARS,
    build_supervisor_restart_ticket,
    is_exact_stale_run_maintenance_reason,
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
        self.assertGreater(len(reason), 500)
        self.assertLessEqual(len(reason), SUPERVISOR_RESTART_REASON_MAX_CHARS)
        self.assertTrue(is_exact_stale_run_maintenance_reason(reason))

        ticket = build_supervisor_restart_ticket(
            ticket_id="restart-exact-stale-ticket-0001",
            now_ms=now_ms,
            workspace="C:\\work\\one",
            process_instance_id="process-one",
            server_instance_id="server-one",
            tool_contract_sha256="e" * 64,
            reason=reason,
            target_workspace="C:\\work\\two",
        )
        self.assertEqual(ticket["reason"], reason)
        self.assertEqual(ticket["target_workspace"], "C:\\work\\two")
        self.assertTrue(
            supervisor_restart_ticket_matches(
                ticket,
                now_ms=now_ms + 3_000,
                workspace="C:\\work\\one",
                process_instance_id="process-one",
                server_instance_id="server-one",
                tool_contract_sha256="e" * 64,
                fence_operation_id="restart-exact-stale-ticket-0001",
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
                target_workspace="C:\\work\\three",
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


if __name__ == "__main__":
    unittest.main()
