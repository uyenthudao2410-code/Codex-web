from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.rework_diagnosis import stratified_rework_diagnosis


class ReworkDiagnosisTests(unittest.TestCase):
    def test_stratifies_rework_and_preserves_unknown_causal_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))

            feature = ledger.create_run(objective='feature first pass', metadata={'workflow': 'feature'})
            feature_wave = ledger.create_wave(feature, execution_mode='mcp_only')
            ledger.append_event(
                feature, wave_id=feature_wave, event_type='context_prepared',
                state_before='PREFLIGHT', state_after='PREFLIGHT',
                payload={'selected_paths': ['a.py', 'b.py']},
            )
            ledger.append_event(
                feature, wave_id=feature_wave, event_type='oracle_preflight',
                state_before='PREFLIGHT', state_after='PREFLIGHT',
                payload={'strong_oracle': True, 'verification': 'tests'},
            )
            ledger.finish_wave(feature_wave, status='accepted')
            ledger.finish_run(feature, status='accepted')

            bugfix = ledger.create_run(objective='bugfix repaired', metadata={'workflow': 'bugfix'})
            bugfix_wave = ledger.create_wave(bugfix, execution_mode='mcp_only')
            ledger.append_event(
                bugfix, wave_id=bugfix_wave, event_type='context_prepared',
                state_before='PREFLIGHT', state_after='PREFLIGHT',
                payload={'selected_paths': ['x.py', 'y.py', 'z.py']},
            )
            ledger.append_event(
                bugfix, wave_id=bugfix_wave, event_type='oracle_preflight',
                state_before='PREFLIGHT', state_after='PREFLIGHT',
                payload={'strong_oracle': False, 'verification': 'tests'},
            )
            ledger.append_event(
                bugfix, wave_id=bugfix_wave, event_type='failure_observed',
                state_before='EXECUTING', state_after='REPLAN',
                payload={'failure_class': 'PATCH_CONTEXT_NOT_FOUND'},
            )
            ledger.finish_wave(bugfix_wave, status='replanned')
            repaired_wave = ledger.create_wave(bugfix, execution_mode='mcp_only')
            ledger.finish_wave(repaired_wave, status='accepted')
            ledger.finish_run(bugfix, status='accepted')

            unknown_cause = ledger.create_run(objective='diagnose repaired', metadata={'workflow': 'diagnose'})
            unknown_wave = ledger.create_wave(unknown_cause, execution_mode='mcp_only')
            ledger.append_event(
                unknown_cause, wave_id=unknown_wave, event_type='failure_observed',
                state_before='PROVING', state_after='REPLAN', payload={'failure_class': 'CHECK_FAILED'},
            )
            ledger.finish_wave(unknown_wave, status='replanned')
            unknown_wave_2 = ledger.create_wave(unknown_cause, execution_mode='mcp_only')
            ledger.finish_wave(unknown_wave_2, status='accepted')
            ledger.finish_run(unknown_cause, status='accepted')

            ledger.claim_idempotency(
                idempotency_key='preflight-avoid', operation='agent_workflow',
                request_hash='preflight-hash', process_instance_id='process',
            )
            ledger.finish_idempotency(
                'preflight-avoid', request_hash='preflight-hash', status='failed',
                summary={
                    'error_code': 'PATCH_CONTEXT_AMBIGUOUS', 'outcome_unknown': False,
                    'workflow_patch_preflight': True,
                },
            )

            report = stratified_rework_diagnosis(ledger)
            strata = {item['workflow']: item for item in report['workflow_strata']}
            self.assertEqual(strata['feature']['n'], 1)
            self.assertEqual(strata['feature']['first_pass_rate'], 1.0)
            self.assertEqual(strata['feature']['scope_size']['p50_paths'], 2)
            self.assertEqual(strata['feature']['oracle_strength']['strong_runs'], 1)
            self.assertEqual(strata['bugfix']['repaired_rate'], 1.0)
            self.assertEqual(strata['bugfix']['replan_count'], 1)
            self.assertEqual(strata['bugfix']['repair_failure_classes'], {'PATCH_CONTEXT_NOT_FOUND': 1})
            self.assertEqual(strata['bugfix']['repair_causes']['event_counts']['patch_context_ambiguity'], 1)
            self.assertEqual(strata['bugfix']['repair_causes']['affected_run_counts']['patch_context_ambiguity'], 1)
            self.assertEqual(strata['bugfix']['scope_size']['p50_paths'], 3)
            self.assertEqual(strata['bugfix']['oracle_strength']['not_strong_runs'], 1)
            self.assertEqual(strata['diagnose']['oracle_strength']['unknown_runs'], 1)
            self.assertEqual(
                strata['diagnose']['repair_causes']['unclassified_structured_failure_classes'],
                {'CHECK_FAILED': 1},
            )
            self.assertEqual(report['overall_repair_causes']['event_counts']['wrong_root_cause'], 0)
            self.assertEqual(report['overall_repair_causes']['event_counts']['oracle_weakness'], 0)
            self.assertEqual(report['causal_classification']['total_failure_events'], 2)
            self.assertEqual(report['causal_classification']['mapped_failure_events'], 1)
            self.assertEqual(report['causal_classification']['unclassified_failure_events'], 1)
            self.assertEqual(report['causal_classification']['mapped_event_coverage'], 0.5)
            self.assertEqual(report['causal_classification']['largest_unclassified_failure_class'], 'CHECK_FAILED')
            self.assertEqual(report['oracle_observation']['eligible_runs'], 3)
            self.assertEqual(report['oracle_observation']['observed_runs'], 2)
            self.assertEqual(report['oracle_observation']['strong_runs'], 1)
            self.assertEqual(report['oracle_observation']['not_strong_runs'], 1)
            self.assertEqual(report['oracle_observation']['unknown_runs'], 1)
            self.assertEqual(report['oracle_observation']['coverage'], 0.666667)
            self.assertTrue(report['oracle_observation']['unknown_not_imputed'])
            self.assertEqual(report['preflight_avoided']['count'], 1)
            patch_preflight = next(
                item for item in report['countermeasure_evaluation'] if item['intervention'] == 'patch_preflight'
            )
            self.assertEqual(patch_preflight['intervention_evidence']['preflight_avoided_count'], 1)
            self.assertIsNone(patch_preflight['effect_estimate'])
            self.assertEqual(patch_preflight['status'], 'hold_not_causally_estimable')
            self.assertTrue(report['policy']['not_a_causal_treatment_effect_estimate'])
            self.assertTrue(report['policy']['zero_planned_cause_without_evidence_is_not_proof_of_absence'])

    def test_durable_reason_classifies_ambiguous_build_failure_without_inventing_repair_cause(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective='formatting-only repaired', metadata={'workflow': 'bugfix'})
            wave_id = ledger.create_wave(run_id, execution_mode='mcp_only')
            ledger.append_event(
                run_id,
                wave_id=wave_id,
                event_type='failure_observed',
                state_before='PROVING',
                state_after='REPLAN',
                payload={'failure_class': 'BUILD_VERIFICATION_FAILED'},
            )
            ledger.finish_wave(wave_id, status='replanned')
            repair_wave = ledger.create_wave(run_id, execution_mode='mcp_only')
            ledger.append_event(
                run_id,
                wave_id=repair_wave,
                event_type='wave_replanned',
                state_after='PREFLIGHT',
                payload={
                    'reason': 'The intended patch was correct but rustfmt --check found one formatting-only delta.',
                    'execution_mode': 'mcp_only',
                },
            )
            ledger.finish_wave(repair_wave, status='accepted')
            ledger.finish_run(run_id, status='accepted')

            report = stratified_rework_diagnosis(ledger)
            bugfix = next(item for item in report['workflow_strata'] if item['workflow'] == 'bugfix')
            self.assertEqual(bugfix['repair_failure_classes'], {'BUILD_VERIFICATION_FAILED': 1})
            self.assertEqual(bugfix['repair_causes']['unclassified_structured_failure_classes'], {})
            self.assertEqual(
                bugfix['repair_causes']['durable_reason_category_counts'],
                {'formatting_only_repair': 1},
            )
            self.assertEqual(sum(bugfix['repair_causes']['event_counts'].values()), 0)
            classification = report['causal_classification']
            self.assertEqual(classification['total_failure_events'], 1)
            self.assertEqual(classification['mapped_failure_events'], 1)
            self.assertEqual(classification['unclassified_failure_events'], 0)
            self.assertEqual(classification['mapped_event_coverage'], 1.0)
            self.assertEqual(classification['durable_reason_fallback_events'], 1)
            self.assertEqual(
                classification['high_confidence_reason_rule_counts'],
                {'rustfmt_formatting_only': 1},
            )


if __name__ == '__main__':
    unittest.main()
