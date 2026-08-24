from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.ledger_access import open_existing_ledger_analysis, open_existing_ledger_readonly
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger
from coding_tools_mcp.rework_diagnosis import (
    P2_FAILURE_OBSERVATION_SCHEMA,
    p2_build_verification_failure_detail,
    p2_check_failure_detail,
    stratified_rework_diagnosis,
)


class ReworkDiagnosisTests(unittest.TestCase):
    def snapshot_report(self, root: Path) -> dict[str, object]:
        with open_existing_ledger_analysis(root) as snapshot:
            self.assertEqual(snapshot.statement_count, 8)
            report = stratified_rework_diagnosis(snapshot.ledger)
            self.assertEqual(snapshot.statement_count, 8)
        return report

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

            report = self.snapshot_report(Path(temp))
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
            prospective = report['overall_repair_causes']['prospective_failure_detail']
            self.assertEqual(prospective['schema'], P2_FAILURE_OBSERVATION_SCHEMA)
            self.assertEqual(prospective['detail_counts'], {})
            self.assertEqual(prospective['legacy_generic_detail_unavailable'], {'CHECK_FAILED': 1})
            self.assertFalse(prospective['historical_backfill'])
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

            report = self.snapshot_report(Path(temp))
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

    def test_prospective_generic_failure_details_are_distinct_from_legacy_and_causal_labels(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective='prospective taxonomy', metadata={'workflow': 'bugfix'})
            first_wave = ledger.create_wave(run_id, execution_mode='mcp_only')
            ledger.append_event(
                run_id,
                wave_id=first_wave,
                event_type='failure_observed',
                state_before='EXECUTING',
                state_after='REPLAN',
                payload={
                    'failure_class': 'CHECK_FAILED',
                    'p2_failure_detail': p2_check_failure_detail('npm test -- --runInBand'),
                },
            )
            ledger.finish_wave(first_wave, status='replanned')
            second_wave = ledger.create_wave(run_id, execution_mode='mcp_only')
            ledger.append_event(
                run_id,
                wave_id=second_wave,
                event_type='failure_observed',
                state_before='PROVING',
                state_after='REPLAN',
                payload={
                    'failure_class': 'BUILD_VERIFICATION_FAILED',
                    'p2_failure_detail': p2_build_verification_failure_detail(
                        {
                            'test_result': {'status': 'passed'},
                            'build_result': {'status': 'passed'},
                            'commands': {'test': 'npm test', 'build': 'npm run build'},
                            'artifacts': [],
                        },
                        'all',
                    ),
                },
            )
            ledger.finish_wave(second_wave, status='replanned')
            terminal_wave = ledger.create_wave(run_id, execution_mode='mcp_only')
            ledger.finish_wave(terminal_wave, status='accepted')
            ledger.finish_run(run_id, status='accepted')

            report = self.snapshot_report(Path(temp))
            prospective = report['overall_repair_causes']['prospective_failure_detail']
            self.assertEqual(prospective['schema'], P2_FAILURE_OBSERVATION_SCHEMA)
            self.assertEqual(
                prospective['detail_counts'],
                {
                    'BUILD_VERIFICATION_FAILED:artifact_missing': 1,
                    'CHECK_FAILED:node_test': 1,
                },
            )
            self.assertEqual(prospective['legacy_generic_detail_unavailable'], {})
            self.assertFalse(prospective['historical_backfill'])
            self.assertEqual(
                report['overall_repair_causes']['unclassified_structured_failure_classes'],
                {'BUILD_VERIFICATION_FAILED': 1, 'CHECK_FAILED': 1},
            )
            self.assertTrue(report['policy']['generic_failure_details_are_prospective_only'])
            self.assertTrue(report['policy']['generic_failure_detail_is_not_a_causal_repair_label'])

    def test_generic_failure_unknown_reasons_are_explicit_and_not_root_cause_labels(self) -> None:
        unrecognized = p2_check_failure_detail('opaque_runner --verify')
        self.assertEqual(unrecognized['command_family'], 'other')
        self.assertEqual(unrecognized['unknown_reason'], 'unrecognized_command_family')
        unspecified = p2_build_verification_failure_detail(
            {'test_result': {'status': 'passed'}, 'build_result': {'status': 'passed'}, 'commands': {'build': 'build'}, 'artifacts': ['artifact']},
            'all',
        )
        self.assertEqual(unspecified['verification_failure_stage'], 'verification_unspecified')
        self.assertEqual(unspecified['unknown_reason'], 'verification_evidence_insufficient')
        from coding_tools_mcp.rework_diagnosis import p2_failure_detail_bucket
        self.assertEqual(p2_failure_detail_bucket('CHECK_FAILED', unrecognized), 'CHECK_FAILED:other')
        self.assertEqual(p2_failure_detail_bucket('BUILD_VERIFICATION_FAILED', unspecified), 'BUILD_VERIFICATION_FAILED:verification_unspecified')
        self.assertIsNone(p2_failure_detail_bucket('CHECK_FAILED', {**unrecognized, 'unknown_reason': 'guessed_cause'}))
        self.assertIsNone(p2_failure_detail_bucket('BUILD_VERIFICATION_FAILED', {**unspecified, 'unknown_reason': 'guessed_cause'}))

    def test_preflight_projection_has_plain_and_compressed_decoded_scalar_parity(self) -> None:
        def report_for(*, compressed: bool) -> dict[str, object]:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                ledger = OrchestrationLedger(root)
                ledger.claim_idempotency(
                    idempotency_key='preflight-parity',
                    operation='agent_workflow',
                    request_hash='preflight-parity-hash',
                    process_instance_id='process',
                )
                summary = {
                    'error_code': 'PATCH_CONTEXT_AMBIGUOUS',
                    'outcome_unknown': False,
                    'workflow_patch_preflight': True,
                }
                if compressed:
                    summary['padding'] = 'fixture-padding-' * 1_000
                ledger.finish_idempotency(
                    'preflight-parity',
                    request_hash='preflight-parity-hash',
                    status='failed',
                    summary=summary,
                )
                with open_existing_ledger_readonly(root) as reader:
                    row = reader.one(
                        'SELECT summary_codec FROM idempotency_records WHERE idempotency_key=?',
                        ('preflight-parity',),
                    )
                self.assertEqual(str(row['summary_codec']), 'zlib_json' if compressed else 'plain_json')
                return self.snapshot_report(root)

        plain = report_for(compressed=False)
        compressed = report_for(compressed=True)
        projection = plain['preflight_avoided']
        compressed_projection = compressed['preflight_avoided']
        for field in ('count', 'error_codes', 'projection', 'decoded_scalar_mismatch_rows', 'mismatched_rows_excluded'):
            self.assertEqual(projection[field], compressed_projection[field])
        self.assertEqual(projection['projection'], 'decoded_scalar_v1')
        self.assertEqual(projection['count'], 1)
        self.assertEqual(projection['error_codes'], {'PATCH_CONTEXT_AMBIGUOUS': 1})
        self.assertEqual(projection['decoded_scalar_mismatch_rows'], 0)
        self.assertEqual(projection['current_plain_decoded_preflight_rows'], 1)
        self.assertEqual(projection['compressed_decoded_preflight_rows'], 0)
        self.assertEqual(compressed_projection['current_plain_decoded_preflight_rows'], 0)
        self.assertEqual(compressed_projection['compressed_decoded_preflight_rows'], 1)

    def test_preflight_projection_uses_decoded_legacy_plain_when_scalar_columns_are_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            ledger.claim_idempotency(
                idempotency_key='legacy-preflight',
                operation='agent_workflow',
                request_hash='legacy-preflight-hash',
                process_instance_id='process',
            )
            ledger.finish_idempotency(
                'legacy-preflight',
                request_hash='legacy-preflight-hash',
                status='failed',
                summary={
                    'error_code': 'PATCH_CONTEXT_NOT_FOUND',
                    'outcome_unknown': False,
                    'workflow_patch_preflight': True,
                },
            )
            # Temporary-fixture migration simulation only: older plain rows
            # predate the scalar projection and must remain decoded, not
            # discarded or rewritten by the reporter.
            with ledger._lock, ledger._connect() as connection:
                connection.execute(
                    "UPDATE idempotency_records SET error_code='', workflow_patch_preflight=0 WHERE idempotency_key=?",
                    ('legacy-preflight',),
                )
            report = self.snapshot_report(root)
            projection = report['preflight_avoided']
            self.assertEqual(projection['count'], 1)
            self.assertEqual(projection['error_codes'], {'PATCH_CONTEXT_NOT_FOUND': 1})
            self.assertEqual(projection['legacy_plain_decoded_preflight_rows'], 1)
            self.assertEqual(projection['decoded_scalar_mismatch_rows'], 0)
            self.assertFalse(projection['mismatched_rows_excluded'])


if __name__ == '__main__':
    unittest.main()
