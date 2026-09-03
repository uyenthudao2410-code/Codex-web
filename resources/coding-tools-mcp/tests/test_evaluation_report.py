from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path

from coding_tools_mcp.evaluation_report import (
    current_ledger_baseline_report,
    evaluation_plane_report,
    host_binding_summary,
    host_visible_summary,
)
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.server import Runtime


class EvaluationReportTests(unittest.TestCase):
    def test_ledger_backed_reports_fail_closed_without_creating_project_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            plane = evaluation_plane_report(root)
            self.assertEqual(plane['causal_run']['status'], 'not_requested')
            self.assertFalse((root / '.coding-tools').exists())
            with self.assertRaises(FileNotFoundError):
                current_ledger_baseline_report(root)
            with self.assertRaises(FileNotFoundError):
                evaluation_plane_report(root, run_id='missing-run')
            with self.assertRaises(FileNotFoundError):
                host_binding_summary(root)
            self.assertFalse((root / '.coding-tools').exists())

    def test_current_ledger_baseline_reports_population_coverage_and_exact_host_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            run_id = ledger.create_run(
                objective='representative baseline run',
                metadata={'evaluation': {
                    'pair_id': 'pair-1', 'policy': 'chatweb_mcp', 'provenance': 'representative',
                    'trace_id': 'trace-1', 'turn_id': 'turn-1',
                    'controller': {
                        'source': 'client_reported', 'started_at': '2026-08-17T00:00:00Z',
                        'input_tokens': 10, 'cached_input_tokens': 0, 'output_tokens': 2,
                        'reasoning_output_tokens': 0, 'monetary_cost': 0.25,
                    },
                }, 'host_correlation': {
                    'schema_version': 1, 'source': 'electron_pending_host_turn', 'eligible': True,
                }},
            )
            wave_id = ledger.create_wave(run_id, execution_mode='mcp_only', base_head='head', worktree_fp='fp')
            ledger.append_event(
                run_id, wave_id=wave_id, event_type='route_selected', state_before='READY', state_after='ROUTED',
                payload={'resolved': 'deterministic'},
            )
            ledger.append_event(
                run_id, wave_id=wave_id, event_type='failure_observed', state_before='EXECUTING', state_after='REPLAN',
                payload={'failure_class': 'runtime'},
            )
            ledger.record_quality_outcome(run_id=run_id, wave_id=wave_id, outcome={
                'source': 'test', 'oracle_pass': True, 'critical_defect_count': 0,
                'manual_fix_required': False, 'regression_escape': False, 'rollback_required': False,
                'maintainability_gate': 'pass', 'observation_window_end': '2026-08-18T00:00:00Z',
            })
            ledger.record_observation_span(run_id=run_id, span={
                'span_id': 'host-1', 'stage': 'assistant_response_visible', 'source': 'electron',
                'measurement': 'observed_host_visible', 'clock_domain': 'electron:1',
                'start_ms': 10, 'end_ms': 20, 'trace_id': 'trace-1', 'turn_id': 'turn-1',
                'observer_plane': 'electron_chatgpt_dom',
            })
            ledger.finish_wave(wave_id, status='accepted')
            ledger.finish_run(run_id, status='accepted')
            ledger.create_run(objective='still active')

            journal = root / '.coding-tools' / 'evaluation' / 'chatweb-host-observations.jsonl'
            journal.parent.mkdir(parents=True, exist_ok=True)
            journal.write_text(json.dumps({
                'schema_version': 6, 'event_type': 'host_turn_span', 'span_id': 'host-1',
                'measurement': 'observed_user_visible_to_first_assistant_visible', 'duration_ms': 25.0,
                'run_id': run_id, 'wave_id': wave_id, 'trace_id': 'trace-1', 'turn_id': 'turn-1',
            }) + '\n', encoding='utf-8')

            report = current_ledger_baseline_report(root)
            population = report['population']
            self.assertIn('p2_rework_diagnosis', report)
            self.assertEqual(report['p2_rework_diagnosis']['accepted_runs'], 1)
            self.assertTrue(report['p2_rework_diagnosis']['policy']['not_a_causal_treatment_effect_estimate'])
            self.assertEqual(population['run_count'], 2)
            self.assertEqual(population['run_status_counts'], {'accepted': 1, 'active': 1})
            self.assertEqual(population['replan_transitions'], 1)
            self.assertEqual(population['failure_events']['classes'], {'RUNTIME': 1})
            self.assertEqual(population['route_decisions']['resolved_counts'], {'deterministic': 1})
            self.assertEqual(population['pairing']['pair_tagged_runs'], 1)
            self.assertEqual(population['pairing']['unique_pair_ids'], 1)
            self.assertEqual(population['quality_outcomes']['runs_with_outcome'], 1)
            self.assertEqual(population['quality_outcomes']['eligible_experimental_runs'], 1)
            self.assertEqual(population['quality_outcomes']['experimental_runs_with_outcome'], 1)
            self.assertEqual(population['quality_outcomes']['experimental_coverage_rate'], 1.0)
            self.assertEqual(population['quality_outcomes']['runs_with_oracle_observation'], 1)
            self.assertEqual(population['quality_outcomes']['runs_with_critical_defect_count'], 1)
            self.assertEqual(population['quality_outcomes']['source_counts'], {'test': 1})
            self.assertEqual(population['quality_outcomes']['promotion_quality']['status'], 'eligible_for_analysis')
            self.assertEqual(population['controller_coverage']['runs_with_started_at'], 1)
            self.assertEqual(population['controller_coverage']['runs_with_token_usage'], 1)
            self.assertEqual(population['controller_coverage']['runs_with_monetary_cost'], 1)
            self.assertEqual(population['controller_coverage']['eligible_experimental_runs'], 1)
            self.assertEqual(population['controller_coverage']['runs_with_complete_token_usage'], 1)
            self.assertEqual(population['controller_coverage']['source_counts'], {'client_reported': 1})
            self.assertEqual(population['controller_coverage']['denominator'], 'explicit_evaluation_enrollment_v1')
            self.assertEqual(population['controller_coverage']['promotion_economics']['status'], 'eligible_for_analysis')
            self.assertEqual(report['host_binding']['host_spans_with_run_binding'], 1)
            self.assertEqual(report['host_binding']['exact_ledger_correlations'], 1)
            self.assertEqual(report['host_binding']['eligible_runs_total'], 1)
            self.assertEqual(report['host_binding']['eligible_runs_with_host_span'], 1)
            self.assertEqual(report['host_binding']['eligible_run_host_coverage'], 1.0)
            regret = report['routing_placement_regret']
            self.assertEqual(regret['regret_methodology']['source'], 'orchestration_ledger_explicit_representative_pairs')
            self.assertTrue(regret['regret_methodology']['historical_or_similar_task_counterfactual_forbidden'])
            self.assertFalse(regret['automatic_activation'])

    def test_current_baseline_keeps_performance_taxonomy_supplemental_and_prospective(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            OrchestrationLedger(root)
            state_dir = root / '.coding-tools'
            state_dir.mkdir(parents=True, exist_ok=True)
            (state_dir / 'performance.json').write_text(json.dumps({
                'version': 5,
                'error_class_counts': {'RUNTIME': 10, 'UNKNOWN': 5, 'FILESYSTEM': 1},
                'error_taxonomy_epoch': 'causal_error_taxonomy_v1',
                'error_taxonomy_current_counts': {'FILESYSTEM': 1, 'UNKNOWN': 1},
            }), encoding='utf-8')

            report = current_ledger_baseline_report(root)
            taxonomy = report['error_taxonomy']
            self.assertEqual(taxonomy['provenance'], 'supplemental_performance_projection')
            self.assertEqual(taxonomy['causal_source'], 'orchestration_ledger')
            self.assertEqual(taxonomy['cumulative_projection']['samples'], 16)
            self.assertEqual(taxonomy['cumulative_projection']['unknown_samples'], 5)
            self.assertEqual(taxonomy['current_epoch']['epoch'], 'causal_error_taxonomy_v1')
            self.assertEqual(taxonomy['current_epoch']['samples'], 2)
            self.assertEqual(taxonomy['current_epoch']['typed_samples'], 1)
            self.assertEqual(taxonomy['current_epoch']['typed_coverage'], 0.5)
            self.assertEqual(taxonomy['current_epoch']['unknown_share'], 0.5)
            self.assertFalse(taxonomy['historical_backfill'])
            self.assertTrue(taxonomy['historical_unknown_reclassification_forbidden'])
            self.assertTrue(report['policy']['ledger_is_causal_source'])
            self.assertTrue(report['policy']['performance_projection_is_not_causal_source'])

    def test_controller_coverage_uses_explicit_experimental_enrollment_and_preserves_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            ledger.create_run(objective='organic host-correlated turn', metadata={
                'evaluation': {
                    'trace_id': 'organic-trace', 'turn_id': 'organic-turn',
                    'controller': {
                        'source': 'client_reported', 'started_at': '2026-08-17T00:00:00Z',
                        'monetary_cost': 0.0,
                    },
                },
            })
            ledger.create_run(objective='enrolled missing controller telemetry', metadata={
                'evaluation': {
                    'pair_id': 'pair-missing', 'policy': 'chatweb_mcp', 'provenance': 'representative',
                },
            })
            ledger.create_run(objective='enrolled partial controller telemetry', metadata={
                'evaluation': {
                    'pair_id': 'pair-partial', 'policy': 'mini', 'provenance': 'benchmark',
                    'controller': {
                        'source': 'client_reported', 'started_at': '2026-08-17T00:00:01Z',
                    },
                },
            })
            ledger.create_run(objective='pair tag without experimental enrollment', metadata={
                'evaluation': {
                    'pair_id': 'pair-unenrolled', 'controller': {'monetary_cost': 0.0},
                },
            })

            coverage = ledger.current_baseline_summary()['controller_coverage']
            self.assertEqual(coverage['eligible_experimental_runs'], 2)
            self.assertEqual(coverage['runs_observed'], 1)
            self.assertEqual(coverage['runs_with_started_at'], 1)
            self.assertEqual(coverage['runs_with_token_usage'], 0)
            self.assertEqual(coverage['runs_with_complete_token_usage'], 0)
            self.assertEqual(coverage['runs_with_monetary_cost'], 0)
            self.assertEqual(coverage['runs_with_source'], 1)
            self.assertEqual(coverage['source_counts'], {'client_reported': 1})
            self.assertEqual(coverage['observed_rate'], 0.5)
            self.assertEqual(coverage['started_at_rate'], 0.5)
            self.assertEqual(coverage['token_usage_rate'], 0.0)
            self.assertEqual(coverage['monetary_cost_rate'], 0.0)
            self.assertTrue(coverage['unknown_is_not_zero'])
            self.assertEqual(coverage['promotion_economics']['status'], 'hold')
            self.assertIn('controller_cost_coverage_incomplete', coverage['promotion_economics']['hold_reasons'])

    def test_controller_zero_cost_is_observed_not_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            ledger.create_run(objective='zero-cost enrolled controller', metadata={
                'evaluation': {
                    'pair_id': 'pair-zero', 'policy': 'chatweb_mcp', 'provenance': 'synthetic',
                    'controller': {
                        'source': 'provider_reported', 'monetary_cost': 0.0,
                        'input_tokens': 0, 'cached_input_tokens': 0,
                        'output_tokens': 0, 'reasoning_output_tokens': 0,
                    },
                },
            })
            coverage = ledger.current_baseline_summary()['controller_coverage']
            self.assertEqual(coverage['eligible_experimental_runs'], 1)
            self.assertEqual(coverage['runs_with_monetary_cost'], 1)
            self.assertEqual(coverage['monetary_cost_rate'], 1.0)
            self.assertEqual(coverage['runs_with_complete_token_usage'], 1)
            self.assertEqual(coverage['source_counts'], {'provider_reported': 1})
            self.assertEqual(coverage['promotion_economics']['status'], 'eligible_for_analysis')

    def test_quality_coverage_requires_explicit_outcomes_and_never_infers_from_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            complete_run = ledger.create_run(objective='enrolled quality observed', metadata={
                'evaluation': {
                    'pair_id': 'pair-quality-a', 'policy': 'chatweb_mcp', 'provenance': 'representative',
                },
            })
            complete_wave = ledger.create_wave(complete_run, execution_mode='mcp_only')
            ledger.record_quality_outcome(run_id=complete_run, wave_id=complete_wave, outcome={
                'source': 'review-window', 'oracle_pass': True, 'critical_defect_count': 0,
                'noncritical_defect_count': 1, 'manual_fix_required': False,
                'regression_escape': False, 'rollback_required': False,
                'maintainability_gate': 'pass', 'observation_window_end': '2026-08-18T00:00:00Z',
            })
            ledger.finish_wave(complete_wave, status='accepted')
            ledger.finish_run(complete_run, status='accepted')

            accepted_without_quality = ledger.create_run(objective='accepted but quality unknown', metadata={
                'evaluation': {
                    'pair_id': 'pair-quality-b', 'policy': 'mini', 'provenance': 'representative',
                },
            })
            accepted_wave = ledger.create_wave(accepted_without_quality, execution_mode='mcp_only')
            ledger.finish_wave(accepted_wave, status='accepted')
            ledger.finish_run(accepted_without_quality, status='accepted')

            organic = ledger.create_run(objective='organic explicit quality outside experiment')
            ledger.record_quality_outcome(run_id=organic, outcome={
                'source': 'organic-review', 'oracle_pass': True, 'critical_defect_count': 0,
            })

            quality = ledger.current_baseline_summary()['quality_outcomes']
            self.assertEqual(quality['event_count'], 2)
            self.assertEqual(quality['runs_with_outcome'], 2)
            self.assertEqual(quality['eligible_experimental_runs'], 2)
            self.assertEqual(quality['experimental_runs_with_outcome'], 1)
            self.assertEqual(quality['experimental_coverage_rate'], 0.5)
            self.assertEqual(quality['runs_with_oracle_observation'], 1)
            self.assertEqual(quality['runs_with_critical_defect_count'], 1)
            self.assertEqual(quality['source_counts'], {'review-window': 1})
            self.assertTrue(quality['eligibility']['accepted_state_alone_is_not_quality_evidence'])
            self.assertTrue(quality['eligibility']['historical_backfill_requires_exact_evidence'])
            self.assertTrue(quality['unknown_is_not_good'])
            self.assertEqual(quality['promotion_quality']['status'], 'hold')
            self.assertIn('quality_outcome_coverage_incomplete', quality['promotion_quality']['hold_reasons'])
            self.assertIn('oracle_quality_evidence_incomplete', quality['promotion_quality']['hold_reasons'])
            self.assertIn('critical_defect_evidence_incomplete', quality['promotion_quality']['hold_reasons'])

    def test_quality_readiness_holds_on_explicit_adverse_quality_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective='enrolled adverse quality', metadata={
                'evaluation': {
                    'pair_id': 'pair-quality-adverse', 'policy': 'chatweb_mcp', 'provenance': 'synthetic',
                },
            })
            ledger.record_quality_outcome(run_id=run_id, outcome={
                'source': 'fault-injection', 'oracle_pass': False, 'critical_defect_count': 1,
                'regression_escape': True, 'rollback_required': True,
            })
            quality = ledger.current_baseline_summary()['quality_outcomes']
            self.assertEqual(quality['experimental_coverage_rate'], 1.0)
            self.assertEqual(quality['oracle_failed_runs'], 1)
            self.assertEqual(quality['critical_defect_nonzero_runs'], 1)
            self.assertEqual(quality['regression_escape_true_runs'], 1)
            self.assertEqual(quality['rollback_required_runs'], 1)
            self.assertEqual(quality['promotion_quality']['status'], 'hold')
            self.assertIn('oracle_failure_observed', quality['promotion_quality']['hold_reasons'])
            self.assertIn('critical_defect_observed', quality['promotion_quality']['hold_reasons'])
            self.assertIn('regression_escape_observed', quality['promotion_quality']['hold_reasons'])
            self.assertIn('rollback_required_observed', quality['promotion_quality']['hold_reasons'])

    def test_host_binding_eligible_run_without_span_reports_zero_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            ledger.create_run(objective='eligible without host span', metadata={
                'evaluation': {'trace_id': 'trace-missing', 'turn_id': 'turn-missing'},
                'host_correlation': {
                    'schema_version': 1, 'source': 'electron_pending_host_turn', 'eligible': True,
                },
            })
            summary = host_binding_summary(root, ledger=ledger)
            self.assertEqual(summary['eligible_runs_total'], 1)
            self.assertEqual(summary['eligible_runs_with_host_span'], 0)
            self.assertEqual(summary['eligible_run_host_coverage'], 0.0)
            self.assertEqual(summary['eligible_run_coverage_status'], 'observed')

    def test_host_binding_summary_does_not_use_timestamp_proximity(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            run_id = ledger.create_run(objective='unlinked host turn')
            wave_id = ledger.create_wave(run_id, execution_mode='mcp_only')
            journal = root / '.coding-tools' / 'evaluation' / 'chatweb-host-observations.jsonl'
            journal.parent.mkdir(parents=True, exist_ok=True)
            journal.write_text(json.dumps({
                'schema_version': 6, 'event_type': 'host_turn_span',
                'measurement': 'observed_user_visible_to_first_assistant_visible', 'duration_ms': 10.0,
                'run_id': run_id, 'wave_id': wave_id,
            }) + '\n', encoding='utf-8')
            summary = host_binding_summary(root, ledger=ledger)
            self.assertEqual(summary['host_spans_with_run_binding'], 1)
            self.assertEqual(summary['host_spans_with_trace_turn_identity'], 0)
            self.assertEqual(summary['exact_ledger_correlations'], 0)
            self.assertTrue(summary['timestamp_proximity_inference_forbidden'])

    def test_host_visible_summary_is_independent_and_never_called_model_latency(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            journal = root / '.coding-tools' / 'evaluation' / 'chatweb-host-observations.jsonl'
            journal.parent.mkdir(parents=True)
            events = [
                {'schema_version': 6, 'event_type': 'host_turn_span', 'measurement': 'observed_user_visible_to_first_assistant_visible', 'duration_ms': 10.0},
                {'schema_version': 6, 'event_type': 'host_turn_span', 'measurement': 'observed_user_visible_to_first_assistant_visible', 'duration_ms': 20.0},
                {'schema_version': 6, 'event_type': 'host_turn_span', 'measurement': 'observed_user_visible_to_first_assistant_visible', 'duration_ms': 30.0},
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
                {'schema_version': 6, 'event_type': 'host_turn_span', 'measurement': 'observed_user_visible_to_first_assistant_visible', 'duration_ms': 25.0},
            ]
            journal.write_text('\n'.join(json.dumps(item) for item in events) + '\n', encoding='utf-8')
            summary = host_visible_summary(root)
            self.assertEqual(summary['event_count'], 1)
            self.assertEqual(summary['ignored_legacy_event_count'], 5)
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
                'schema_version': 6,
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
                self.assertEqual(run['metadata']['host_correlation'], {
                    'schema_version': 1, 'source': 'electron_pending_host_turn', 'eligible': True,
                })
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
                metadata = runtime.orchestration_ledger.get_run(ctx.run_id)['metadata']
                self.assertEqual(evaluation['turn_id'], 'turn-controlled')
                self.assertEqual(evaluation['trace_id'], 'trace-controlled')
                self.assertNotIn('host_correlation', metadata)
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
