from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path

from coding_tools_mcp.evaluation_report import evaluation_plane_report, host_visible_summary
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.server import Runtime


class EvaluationReportTests(unittest.TestCase):
    def test_host_visible_summary_is_independent_and_never_called_model_latency(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            journal = root / '.coding-tools' / 'evaluation' / 'chatweb-host-observations.jsonl'
            journal.parent.mkdir(parents=True)
            events = [
                {'schema_version': 5, 'event_type': 'host_turn_span', 'measurement': 'observed_user_visible_to_first_assistant_visible', 'duration_ms': 10.0},
                {'schema_version': 5, 'event_type': 'host_turn_span', 'measurement': 'observed_user_visible_to_first_assistant_visible', 'duration_ms': 20.0},
                {'schema_version': 5, 'event_type': 'host_turn_span', 'measurement': 'observed_user_visible_to_first_assistant_visible', 'duration_ms': 30.0},
            ]
            journal.write_text('\n'.join(json.dumps(item) for item in events) + '\n', encoding='utf-8')
            summary = host_visible_summary(root)
            self.assertEqual(summary['turn_span_count'], 3)
            self.assertEqual(summary['duration_ms']['p50'], 20.0)
            self.assertEqual(summary['duration_ms']['p90'], 30.0)
            self.assertTrue(summary['not_model_latency'])

    def test_legacy_host_observations_are_preserved_but_excluded_from_current_percentiles(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            journal = root / '.coding-tools' / 'evaluation' / 'chatweb-host-observations.jsonl'
            journal.parent.mkdir(parents=True)
            events = [
                {'schema_version': 1, 'event_type': 'host_turn_span', 'measurement': 'observed_user_visible_to_first_assistant_visible', 'duration_ms': 0.0},
                {'schema_version': 2, 'event_type': 'host_turn_span', 'measurement': 'observed_user_visible_to_first_assistant_visible', 'duration_ms': 0.2},
                {'schema_version': 3, 'event_type': 'host_turn_span', 'measurement': 'observed_user_visible_to_first_assistant_visible', 'duration_ms': 0.0},
                {'schema_version': 4, 'event_type': 'host_turn_span', 'measurement': 'observed_user_visible_to_first_assistant_visible', 'duration_ms': 0.0},
                {'schema_version': 5, 'event_type': 'host_turn_span', 'measurement': 'observed_user_visible_to_first_assistant_visible', 'duration_ms': 25.0},
            ]
            journal.write_text('\n'.join(json.dumps(item) for item in events) + '\n', encoding='utf-8')
            summary = host_visible_summary(root)
            self.assertEqual(summary['event_count'], 1)
            self.assertEqual(summary['ignored_legacy_event_count'], 4)
            self.assertEqual(summary['turn_span_count'], 1)
            self.assertEqual(summary['duration_ms']['p50'], 25.0)

    def test_report_refuses_timestamp_proximity_correlation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            run_id = ledger.create_run(objective='uncorrelated host evidence')
            ledger.record_observation_span(run_id=run_id, span={
                'span_id': 'tool',
                'stage': 'tool',
                'source': 'mcp',
                'measurement': 'observed',
                'clock_domain': 'mcp:1',
                'start_ms': 1,
                'end_ms': 6,
            })
            report = evaluation_plane_report(root, run_id=run_id)
            self.assertTrue(report['causal_run']['complete'])
            self.assertEqual(report['host_to_run_correlation']['status'], 'unlinked_no_stable_turn_to_run_identity')
            self.assertTrue(report['host_to_run_correlation']['inference_forbidden'])

    def test_explicit_trace_identity_must_match_current_host_journal_span(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            run_id = ledger.create_run(objective='explicit host evidence')
            journal = root / '.coding-tools' / 'evaluation' / 'chatweb-host-observations.jsonl'
            journal.parent.mkdir(parents=True)
            journal.write_text(json.dumps({
                'schema_version': 5,
                'event_type': 'host_turn_span',
                'span_id': 'host',
                'measurement': 'observed_user_visible_to_first_assistant_visible',
                'duration_ms': 10.0,
                'run_id': run_id,
                'wave_id': 'wave-1',
                'trace_id': 'trace-1',
                'turn_id': 'turn-1',
            }) + '\n', encoding='utf-8')
            ledger.record_observation_span(run_id=run_id, span={
                'span_id': 'host',
                'stage': 'assistant_response_visible',
                'source': 'electron',
                'measurement': 'observed_host_visible',
                'clock_domain': 'electron:1',
                'start_ms': 10,
                'end_ms': 20,
                'trace_id': 'trace-1',
                'turn_id': 'turn-1',
                'observer_plane': 'electron_chatgpt_dom',
            })
            report = evaluation_plane_report(root, run_id=run_id)
            self.assertEqual(report['host_to_run_correlation']['status'], 'explicit_host_run_identity_present')
            self.assertEqual(report['host_to_run_correlation']['explicit_host_span_count'], 1)
            self.assertFalse(report['host_to_run_correlation']['inference_forbidden'])

            journal.write_text(journal.read_text(encoding='utf-8').replace('trace-1', 'trace-mismatch'), encoding='utf-8')
            mismatched = evaluation_plane_report(root, run_id=run_id)
            self.assertEqual(mismatched['host_to_run_correlation']['status'], 'unlinked_no_stable_turn_to_run_identity')
            self.assertTrue(mismatched['host_to_run_correlation']['inference_forbidden'])

    def test_new_run_claims_exact_pending_host_identity_and_publishes_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pending = root / '.coding-tools' / 'evaluation' / 'chatweb-host-turn-pending.json'
            pending.parent.mkdir(parents=True)
            pending.write_text(json.dumps({
                'schema_version': 1, 'turn_id': 'turn-organic', 'trace_id': 'trace-organic',
                'staged_at_unix_ms': int(time.time() * 1000),
            }), encoding='utf-8')
            runtime = Runtime(root, permission_mode='dangerous')
            runtime._orchestration_workspace_identity = lambda _path: {'branch': 'test', 'base_head': 'head', 'worktree_fp': 'worktree'}
            try:
                ctx, _ = runtime._agent_orchestration_context(
                    {'workflow': 'diagnose', 'phase': 'prepare', 'execution_mode': 'mcp_only'},
                    objective='correlate organic turn',
                )
                run = runtime.orchestration_ledger.get_run(ctx.run_id)
                self.assertEqual(run['metadata']['evaluation']['turn_id'], 'turn-organic')
                self.assertEqual(run['metadata']['evaluation']['trace_id'], 'trace-organic')
                binding = json.loads((root / '.coding-tools' / 'evaluation' / 'chatweb-host-turn-binding.json').read_text(encoding='utf-8'))
                self.assertEqual(binding['turn_id'], 'turn-organic')
                self.assertEqual(binding['trace_id'], 'trace-organic')
                self.assertEqual(binding['run_id'], ctx.run_id)
                self.assertEqual(binding['wave_id'], ctx.wave_id)
                self.assertFalse(pending.exists())
            finally:
                runtime.close()

    def test_controlled_evaluation_identity_takes_precedence_without_stale_host_claim(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pending = root / '.coding-tools' / 'evaluation' / 'chatweb-host-turn-pending.json'
            pending.parent.mkdir(parents=True)
            pending.write_text(json.dumps({
                'schema_version': 1, 'turn_id': 'turn-organic', 'trace_id': 'trace-organic',
                'staged_at_unix_ms': int(time.time() * 1000),
            }), encoding='utf-8')
            runtime = Runtime(root, permission_mode='dangerous')
            runtime._orchestration_workspace_identity = lambda _path: {'branch': 'test', 'base_head': 'head', 'worktree_fp': 'worktree'}
            try:
                ctx, _ = runtime._agent_orchestration_context({
                    'workflow': 'diagnose', 'phase': 'prepare', 'execution_mode': 'mcp_only',
                    'evaluation': {'turn_id': 'turn-controlled', 'trace_id': 'trace-controlled'},
                }, objective='controlled evaluation')
                evaluation = runtime.orchestration_ledger.get_run(ctx.run_id)['metadata']['evaluation']
                self.assertEqual(evaluation['turn_id'], 'turn-controlled')
                self.assertEqual(evaluation['trace_id'], 'trace-controlled')
                self.assertFalse(pending.exists())
                self.assertFalse((root / '.coding-tools' / 'evaluation' / 'chatweb-host-turn-binding.json').exists())
            finally:
                runtime.close()

    def test_existing_run_never_claims_later_pending_host_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runtime = Runtime(root, permission_mode='dangerous')
            runtime._orchestration_workspace_identity = lambda _path: {'branch': 'test', 'base_head': 'head', 'worktree_fp': 'worktree'}
            try:
                ctx, _ = runtime._agent_orchestration_context(
                    {'workflow': 'diagnose', 'phase': 'prepare', 'execution_mode': 'mcp_only', 'evaluation': {'turn_id': 'controlled-turn', 'trace_id': 'controlled-trace'}},
                    objective='existing run',
                )
                pending = root / '.coding-tools' / 'evaluation' / 'chatweb-host-turn-pending.json'
                pending.parent.mkdir(parents=True, exist_ok=True)
                pending.write_text(json.dumps({
                    'schema_version': 1, 'turn_id': 'late-turn', 'trace_id': 'late-trace',
                    'staged_at_unix_ms': int(time.time() * 1000),
                }), encoding='utf-8')
                reused, _ = runtime._agent_orchestration_context(
                    {'workflow': 'diagnose', 'phase': 'prepare', 'execution_mode': 'mcp_only'},
                    objective='existing run',
                )
                self.assertEqual(reused.run_id, ctx.run_id)
                self.assertTrue(pending.exists())
            finally:
                runtime.close()


if __name__ == '__main__':
    unittest.main()
