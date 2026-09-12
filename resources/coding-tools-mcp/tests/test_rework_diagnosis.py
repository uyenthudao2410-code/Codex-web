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
    p2_failure_detail_bucket,
    p2_generic_replan_reason_category,
    p2_permission_failure_detail,
    p2_request_contract_cause_from_replan_reason,
    p2_repair_cause_for_failure_class,
    repair_cause_for_failure_class,
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
            self.assertEqual(strata['feature']['phase_aware_timing']['observed_runs'], 0)
            self.assertEqual(strata['feature']['phase_aware_timing']['unknown_runs'], 1)
            self.assertTrue(report['policy']['phase_aware_timing_unknown_not_imputed'])

    def test_phase_aware_timing_separates_accept_wait_from_engineering_active(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))

            def record_transition(run_id: str, wave_id: str, state: str, second: int) -> None:
                ledger.append_event(
                    run_id,
                    wave_id=wave_id,
                    event_type='state_transition',
                    state_after=state,
                    event_time=f'2026-01-01T00:{second // 60:02d}:{second % 60:02d}+00:00',
                )

            first_pass = ledger.create_run(
                objective='first pass with external accept wait', metadata={'workflow': 'bugfix'}
            )
            first_wave = ledger.create_wave(first_pass, execution_mode='mcp_only')
            for state, second in (
                ('PREFLIGHT', 0), ('READY', 1), ('ROUTED', 2), ('EXECUTING', 3),
                ('PROVING', 5), ('ACCEPTING', 7), ('CHECKPOINTED', 607),
            ):
                record_transition(first_pass, first_wave, state, second)
            ledger.finish_wave(first_wave, status='accepted')
            ledger.finish_run(first_pass, status='accepted')

            repaired = ledger.create_run(
                objective='repaired with short accept wait', metadata={'workflow': 'bugfix'}
            )
            repair_wave_1 = ledger.create_wave(repaired, execution_mode='mcp_only')
            for state, second in (
                ('PREFLIGHT', 0), ('READY', 1), ('ROUTED', 2), ('EXECUTING', 3),
                ('PROVING', 5), ('REPLAN', 7),
            ):
                record_transition(repaired, repair_wave_1, state, second)
            ledger.finish_wave(repair_wave_1, status='replanned')
            repair_wave_2 = ledger.create_wave(repaired, execution_mode='mcp_only')
            for state, second in (
                ('PREFLIGHT', 9), ('READY', 10), ('ROUTED', 11), ('EXECUTING', 12),
                ('PROVING', 14), ('ACCEPTING', 16), ('CHECKPOINTED', 21),
            ):
                record_transition(repaired, repair_wave_2, state, second)
            ledger.finish_wave(repair_wave_2, status='accepted')
            ledger.finish_run(repaired, status='accepted')

            with ledger._lock, ledger._connect() as connection:
                connection.execute(
                    "UPDATE runs SET started_at=?, finished_at=? WHERE run_id=?",
                    ('2026-01-01T00:00:00+00:00', '2026-01-01T00:10:07+00:00', first_pass),
                )
                connection.execute(
                    "UPDATE runs SET started_at=?, finished_at=? WHERE run_id=?",
                    ('2026-01-01T00:00:00+00:00', '2026-01-01T00:00:21+00:00', repaired),
                )
                connection.commit()

            report = self.snapshot_report(Path(temp))
            bugfix = next(item for item in report['workflow_strata'] if item['workflow'] == 'bugfix')
            self.assertEqual(bugfix['first_pass_accepted'], 1)
            self.assertEqual(bugfix['repaired_accepted'], 1)
            self.assertEqual(bugfix['ttar_ms']['first_pass_p50'], 607_000)
            phase = bugfix['phase_aware_timing']
            self.assertEqual(phase['observed_runs'], 2)
            self.assertEqual(phase['unknown_runs'], 0)
            self.assertEqual(phase['engineering_active_ms']['first_pass_p50'], 7_000)
            self.assertEqual(phase['accept_wait_ms']['first_pass_p50'], 600_000)
            self.assertEqual(phase['engineering_active_ms']['repaired_p50'], 14_000)
            self.assertEqual(phase['accept_wait_ms']['repaired_p50'], 5_000)
            self.assertEqual(phase['replan_ms']['repaired_p50'], 2_000)
            self.assertTrue(phase['not_model_latency'])
            self.assertTrue(phase['not_cpu_time'])
            self.assertFalse(phase['accept_wait_cause_inferred'])
            self.assertTrue(phase['unknown_not_imputed'])

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

    def test_p2_generic_replan_reason_rules_are_narrow_and_fail_closed(self) -> None:
        positive_cases = (
            (
                'CHECK_FAILED',
                'The failure proof launched from the repository root where coding_tools_mcp was not importable. Change proof workdir to the component cwd and rerun from there.',
                ('oracle_selection_repair', 'verification_workdir_correction'),
            ),
            (
                'CHECK_FAILED',
                'Windows temp-tree cleanup hit EPERM under parallel test execution; the isolated assertion passes, so rerun serially.',
                ('environment_or_baseline_repair', 'windows_temp_cleanup_contention'),
            ),
            (
                'BUILD_VERIFICATION_FAILED',
                'The module-size guard exceeded its budget. Extract the projection into a dedicated module without weakening the guard.',
                ('causal_solution_repair', 'module_size_architecture_correction'),
            ),
            (
                'CHECK_FAILED',
                'Windows reported The command line is too long before proof execution; split the frozen proof into bounded sequential commands.',
                ('oracle_selection_repair', 'windows_command_line_split'),
            ),
            (
                'CHECK_FAILED',
                'Windows fsync raised Errno 9 because the helper did not use a writable descriptor; reopen with O_RDWR.',
                ('causal_solution_repair', 'windows_fsync_writable_descriptor'),
            ),
            (
                'BUILD_VERIFICATION_FAILED',
                'Schema behavior is correct; patch only the regression expectation from internal ToolFailure to public JsonRpcError.',
                ('oracle_selection_repair', 'public_validation_exception_expectation'),
            ),
        )
        for failure_class, reason, expected in positive_cases:
            self.assertEqual(p2_generic_replan_reason_category(failure_class, reason), expected)

        strong_generic_reason = positive_cases[0][1]
        for failure_class in ('PERMISSION_REQUIRED', 'PROTECTED_PATH_WRITE', 'INVALID_ARGUMENT'):
            self.assertEqual(p2_generic_replan_reason_category(failure_class, strong_generic_reason), (None, None))
        for reason in (
            'pytest failed from the repository root.',
            'EPERM while removing a temporary directory.',
            'The module-size budget was exceeded.',
            'The command line is too long.',
            'fsync failed.',
            'The test expectation changed.',
        ):
            self.assertEqual(p2_generic_replan_reason_category('CHECK_FAILED', reason), (None, None))

    def test_p2_generic_reason_integration_preserves_permission_and_ambiguous_unknowns(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective='paired generic reason evidence', metadata={'workflow': 'bugfix'})
            failures = (
                'CHECK_FAILED',
                'BUILD_VERIFICATION_FAILED',
                'PERMISSION_REQUIRED',
                'CHECK_FAILED',
            )
            reasons = (
                'The failure proof launched from the repository root where coding_tools_mcp was not importable. Change proof workdir to the component cwd and rerun from there.',
                'The module-size guard exceeded its budget. Extract the projection into a dedicated module without weakening the guard.',
                'The failure proof launched from the repository root where coding_tools_mcp was not importable. Change proof workdir to the component cwd and rerun from there.',
                'A generic check failed; investigate further.',
            )
            for failure_class in failures:
                wave_id = ledger.create_wave(run_id, execution_mode='mcp_only')
                ledger.append_event(
                    run_id,
                    wave_id=wave_id,
                    event_type='failure_observed',
                    state_before='PROVING',
                    state_after='REPLAN',
                    payload={'failure_class': failure_class},
                )
                ledger.finish_wave(wave_id, status='replanned')
            for reason in reasons:
                wave_id = ledger.create_wave(run_id, execution_mode='mcp_only')
                ledger.append_event(
                    run_id,
                    wave_id=wave_id,
                    event_type='wave_replanned',
                    state_after='PREFLIGHT',
                    payload={'reason': reason, 'execution_mode': 'mcp_only'},
                )
                ledger.finish_wave(wave_id, status='replanned')
            terminal_wave = ledger.create_wave(run_id, execution_mode='mcp_only')
            ledger.finish_wave(terminal_wave, status='accepted')
            ledger.finish_run(run_id, status='accepted')

            report = self.snapshot_report(Path(temp))
            classification = report['causal_classification']
            self.assertEqual(classification['total_failure_events'], 4)
            self.assertEqual(classification['mapped_failure_events'], 2)
            self.assertEqual(classification['unclassified_failure_events'], 2)
            self.assertEqual(classification['mapped_event_coverage'], 0.5)
            self.assertEqual(
                report['overall_repair_causes']['unclassified_structured_failure_classes'],
                {'CHECK_FAILED': 1, 'PERMISSION_REQUIRED': 1},
            )
            self.assertEqual(
                classification['high_confidence_reason_rule_counts'],
                {
                    'module_size_architecture_correction': 1,
                    'verification_workdir_correction': 1,
                },
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

    def test_permission_detail_is_allowlisted_content_free_and_not_a_causal_label(self) -> None:
        detail = p2_permission_failure_detail(
            'PERMISSION_REQUIRED',
            {'permission': 'inline_script', 'command': 'do-not-persist', 'path': 'secret-path'},
        )
        self.assertEqual(
            detail,
            {
                'schema': P2_FAILURE_OBSERVATION_SCHEMA,
                'stage': 'permission_policy',
                'permission_reason': 'inline_script',
                'causal_attribution': 'unattributed',
            },
        )
        self.assertEqual(p2_failure_detail_bucket('PERMISSION_REQUIRED', detail), 'PERMISSION_REQUIRED:inline_script')
        self.assertIsNone(p2_permission_failure_detail('INVALID_ARGUMENT', {'permission': 'inline_script'}))
        self.assertIsNone(p2_permission_failure_detail('PERMISSION_REQUIRED', {'permission': 'unknown_policy'}))
        self.assertIsNone(p2_failure_detail_bucket('PERMISSION_REQUIRED', {**detail, 'command': 'forbidden'}))
        self.assertEqual(repair_cause_for_failure_class('ACCEPTANCE_FILE_SHA_MISMATCH'), 'source_base_drift')
        self.assertIsNone(repair_cause_for_failure_class('EXISTING_FILE_ADOPTION_PREEXISTING_DIRTY_REQUIRED'))

    def test_request_contract_correction_maps_only_typed_request_control_failures(self) -> None:
        self.assertEqual(p2_repair_cause_for_failure_class('INVALID_ARGUMENT'), 'request_contract_correction')
        self.assertEqual(p2_repair_cause_for_failure_class('MODE_ROUTE_MISMATCH'), 'request_contract_correction')
        self.assertEqual(
            p2_repair_cause_for_failure_class('EXISTING_FILE_ADOPTION_PREEXISTING_DIRTY_REQUIRED'),
            'request_contract_correction',
        )
        for failure_class in (
            'CHECK_FAILED',
            'BUILD_VERIFICATION_FAILED',
            'PERMISSION_REQUIRED',
            'PROTECTED_PATH_WRITE',
        ):
            self.assertIsNone(p2_repair_cause_for_failure_class(failure_class))

        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective='typed request contract repair', metadata={'workflow': 'bugfix'})
            failure_classes = (
                'INVALID_ARGUMENT',
                'MODE_ROUTE_MISMATCH',
                'CHECK_FAILED',
                'BUILD_VERIFICATION_FAILED',
                'PERMISSION_REQUIRED',
                'PROTECTED_PATH_WRITE',
                'EXISTING_FILE_ADOPTION_PREEXISTING_DIRTY_REQUIRED',
            )
            for failure_class in failure_classes:
                wave_id = ledger.create_wave(run_id, execution_mode='mcp_only')
                ledger.append_event(
                    run_id,
                    wave_id=wave_id,
                    event_type='failure_observed',
                    state_before='PREFLIGHT',
                    state_after='REPLAN',
                    payload={'failure_class': failure_class},
                )
                ledger.finish_wave(wave_id, status='replanned')

            terminal_wave = ledger.create_wave(run_id, execution_mode='mcp_only')
            ledger.finish_wave(terminal_wave, status='accepted')
            ledger.finish_run(run_id, status='accepted')

            report = self.snapshot_report(Path(temp))
            causes = report['overall_repair_causes']
            self.assertEqual(causes['event_counts']['request_contract_correction'], 3)
            self.assertEqual(causes['affected_run_counts']['request_contract_correction'], 1)
            self.assertEqual(
                causes['unclassified_structured_failure_classes'],
                {
                    'BUILD_VERIFICATION_FAILED': 1,
                    'CHECK_FAILED': 1,
                    'PERMISSION_REQUIRED': 1,
                    'PROTECTED_PATH_WRITE': 1,
                },
            )
            classification = report['causal_classification']
            self.assertEqual(classification['total_failure_events'], 7)
            self.assertEqual(classification['mapped_failure_events'], 3)
            self.assertEqual(classification['unclassified_failure_events'], 4)
            self.assertEqual(classification['mapped_event_coverage'], 0.428571)

    def test_paired_permission_and_protected_replan_reasons_map_request_contract_correction(self) -> None:
        positive_cases = (
            (
                'PERMISSION_REQUIRED',
                'filesystem_escape rejected the parent traversal; rerun from the repository root with workspace-relative paths.',
                'permission_filesystem_escape_strategy_correction',
            ),
            (
                'PERMISSION_REQUIRED',
                'python -c requires unsupported inline_script permission. Remove inline code and use an existing repository script.',
                'permission_inline_script_strategy_correction',
            ),
            (
                'PERMISSION_REQUIRED',
                'NETWORK_PERMISSION_REQUIRED blocked the probe; remove all HTTP/network calls and replace them with OS-local evidence.',
                'permission_network_probe_strategy_correction',
            ),
            (
                'PROTECTED_PATH_WRITE',
                'PROTECTED_PATH_WRITE blocked the protected artifact before durable write; use a legal public-surface strategy instead.',
                'protected_path_strategy_correction',
            ),
        )
        for failure_class, reason, rule in positive_cases:
            self.assertEqual(
                p2_request_contract_cause_from_replan_reason(failure_class, reason),
                ('request_contract_correction', rule),
            )

        negative_cases = (
            ('PERMISSION_REQUIRED', 'Network access requires approval; request permission and retry.'),
            ('PERMISSION_REQUIRED', 'filesystem_escape blocked the command; investigate further.'),
            ('PERMISSION_REQUIRED', 'Use a workspace-relative command for an unrelated validation failure.'),
            ('PROTECTED_PATH_WRITE', 'Protected path write was blocked by policy.'),
            ('CHECK_FAILED', 'filesystem_escape blocked traversal; rerun from repository root.'),
        )
        for failure_class, reason in negative_cases:
            self.assertEqual(p2_request_contract_cause_from_replan_reason(failure_class, reason), (None, None))
        self.assertIsNone(p2_repair_cause_for_failure_class('PERMISSION_REQUIRED'))
        self.assertIsNone(p2_repair_cause_for_failure_class('PROTECTED_PATH_WRITE'))

        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective='paired request strategy corrections', metadata={'workflow': 'bugfix'})
            for failure_class, _reason, _rule in positive_cases:
                wave_id = ledger.create_wave(run_id, execution_mode='mcp_only')
                ledger.append_event(
                    run_id,
                    wave_id=wave_id,
                    event_type='failure_observed',
                    state_before='PROVING',
                    state_after='REPLAN',
                    payload={'failure_class': failure_class},
                )
                ledger.finish_wave(wave_id, status='replanned')
            for _failure_class, reason, _rule in positive_cases:
                wave_id = ledger.create_wave(run_id, execution_mode='mcp_only')
                ledger.append_event(
                    run_id,
                    wave_id=wave_id,
                    event_type='wave_replanned',
                    state_after='PREFLIGHT',
                    payload={'reason': reason, 'execution_mode': 'mcp_only'},
                )
                ledger.finish_wave(wave_id, status='replanned')
            terminal_wave = ledger.create_wave(run_id, execution_mode='mcp_only')
            ledger.finish_wave(terminal_wave, status='accepted')
            ledger.finish_run(run_id, status='accepted')

            report = self.snapshot_report(Path(temp))
            causes = report['overall_repair_causes']
            self.assertEqual(causes['event_counts']['request_contract_correction'], 4)
            self.assertEqual(causes['affected_run_counts']['request_contract_correction'], 1)
            self.assertEqual(causes['unclassified_structured_failure_classes'], {})
            self.assertEqual(
                causes['high_confidence_reason_rule_counts'],
                {
                    'permission_filesystem_escape_strategy_correction': 1,
                    'permission_inline_script_strategy_correction': 1,
                    'permission_network_probe_strategy_correction': 1,
                    'protected_path_strategy_correction': 1,
                },
            )
            classification = report['causal_classification']
            self.assertEqual(classification['total_failure_events'], 4)
            self.assertEqual(classification['mapped_failure_events'], 4)
            self.assertEqual(classification['unclassified_failure_events'], 0)
            self.assertEqual(classification['mapped_event_coverage'], 1.0)
            self.assertEqual(
                classification['classification_source_counts'],
                {'durable_wave_replanned_reason_high_confidence': 4},
            )
            self.assertTrue(report['policy']['permission_or_protected_request_correction_requires_paired_replan_reason'])

    def test_generic_process_outcome_links_only_exact_durable_failed_proofs(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective='generic process outcome observation', metadata={'workflow': 'bugfix'})

            linked_check = ledger.create_wave(run_id, execution_mode='mcp_only')
            check_hash = 'a' * 64
            ledger.record_proof(
                run_id=run_id,
                wave_id=linked_check,
                stage_id='check:aaaaaaaaaaaaaaaa',
                stage_version='1',
                input_fingerprint='1' * 64,
                status='failed',
                command_hash=check_hash,
                exit_code=1,
                metadata={'result': {'status': 'failed', 'exit_code': 1, 'timed_out': False, 'cancelled': False}},
            )
            ledger.append_event(
                run_id,
                wave_id=linked_check,
                event_type='failure_observed',
                state_before='PROVING',
                state_after='REPLAN',
                payload={
                    'failure_class': 'CHECK_FAILED',
                    'command_hash': check_hash,
                    'p2_failure_detail': p2_check_failure_detail('python -m unittest'),
                },
            )
            ledger.finish_wave(linked_check, status='replanned')

            linked_build = ledger.create_wave(run_id, execution_mode='mcp_only')
            build_report = {
                'test_result': {'status': 'failed', 'exit_code': 2, 'timed_out': False, 'cancelled': False},
                'build_result': {'status': 'not_run'},
                'commands': {'test': 'test-command', 'build': 'build-command'},
                'artifacts': [],
            }
            ledger.record_proof(
                run_id=run_id,
                wave_id=linked_build,
                stage_id='verify:tests',
                stage_version='1',
                input_fingerprint='2' * 64,
                status='failed',
                metadata={'result': build_report},
            )
            ledger.append_event(
                run_id,
                wave_id=linked_build,
                event_type='failure_observed',
                state_before='PROVING',
                state_after='REPLAN',
                payload={
                    'failure_class': 'BUILD_VERIFICATION_FAILED',
                    'verification': 'tests',
                    'p2_failure_detail': p2_build_verification_failure_detail(build_report, 'tests'),
                },
            )
            ledger.finish_wave(linked_build, status='replanned')

            missing = ledger.create_wave(run_id, execution_mode='mcp_only')
            ledger.append_event(
                run_id,
                wave_id=missing,
                event_type='failure_observed',
                state_before='PROVING',
                state_after='REPLAN',
                payload={
                    'failure_class': 'CHECK_FAILED',
                    'command_hash': 'b' * 64,
                    'p2_failure_detail': p2_check_failure_detail('pytest'),
                },
            )
            ledger.finish_wave(missing, status='replanned')

            ambiguous = ledger.create_wave(run_id, execution_mode='mcp_only')
            ambiguous_hash = 'c' * 64
            for index in range(2):
                ledger.record_proof(
                    run_id=run_id,
                    wave_id=ambiguous,
                    stage_id=f'check:ambiguous{index}',
                    stage_version='1',
                    input_fingerprint=str(index + 3) * 64,
                    status='failed',
                    command_hash=ambiguous_hash,
                    exit_code=3,
                    metadata={'result': {'status': 'failed', 'exit_code': 3}},
                )
            ledger.append_event(
                run_id,
                wave_id=ambiguous,
                event_type='failure_observed',
                state_before='PROVING',
                state_after='REPLAN',
                payload={
                    'failure_class': 'CHECK_FAILED',
                    'command_hash': ambiguous_hash,
                    'p2_failure_detail': p2_check_failure_detail('opaque_runner --verify'),
                },
            )
            ledger.finish_wave(ambiguous, status='replanned')

            terminal_wave = ledger.create_wave(run_id, execution_mode='mcp_only')
            ledger.finish_wave(terminal_wave, status='accepted')
            ledger.finish_run(run_id, status='accepted')

            report = self.snapshot_report(Path(temp))
            observation = report['generic_failure_process_outcome']
            self.assertEqual(observation['eligible_failure_events'], 4)
            self.assertEqual(observation['observed_events'], 2)
            self.assertEqual(observation['unknown_events'], 2)
            self.assertEqual(observation['coverage'], 0.5)
            self.assertEqual(observation['eligible_by_failure_class'], {'BUILD_VERIFICATION_FAILED': 1, 'CHECK_FAILED': 3})
            self.assertEqual(observation['observed_by_failure_class'], {'BUILD_VERIFICATION_FAILED': 1, 'CHECK_FAILED': 1})
            self.assertEqual(
                observation['linkage_counts'],
                {
                    'ambiguous_exact_proof': 1,
                    'exact_wave_command_hash': 1,
                    'exact_wave_verify_stage': 1,
                    'missing_exact_proof': 1,
                },
            )
            self.assertEqual(
                observation['outcome_counts'],
                {
                    'BUILD_VERIFICATION_FAILED:test_command_failed:process_exit_nonzero': 1,
                    'CHECK_FAILED:process_exit_nonzero': 1,
                },
            )
            self.assertEqual(observation['causal_attribution'], 'unattributed')
            self.assertFalse(observation['historical_events_mutated'])
            self.assertTrue(observation['unknown_not_imputed'])
            self.assertTrue(report['policy']['generic_process_outcome_is_not_a_causal_repair_label'])
            self.assertTrue(report['policy']['generic_process_outcome_uses_exact_durable_proof_linkage'])
            self.assertEqual(report['causal_classification']['total_failure_events'], 4)
            self.assertEqual(report['causal_classification']['mapped_failure_events'], 0)
            self.assertEqual(report['causal_classification']['unclassified_failure_events'], 4)

    def test_permission_detail_is_reported_prospectively_while_sha_mismatch_is_causal(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            ledger = OrchestrationLedger(Path(temp))
            run_id = ledger.create_run(objective='permission detail repaired', metadata={'workflow': 'bugfix'})
            first_wave = ledger.create_wave(run_id, execution_mode='mcp_only')
            ledger.append_event(
                run_id,
                wave_id=first_wave,
                event_type='failure_observed',
                state_before='PROVING',
                state_after='REPLAN',
                payload={
                    'failure_class': 'PERMISSION_REQUIRED',
                    'p2_failure_detail': p2_permission_failure_detail(
                        'PERMISSION_REQUIRED', {'permission': 'filesystem_escape', 'path': 'not-retained'}
                    ),
                },
            )
            ledger.finish_wave(first_wave, status='replanned')
            second_wave = ledger.create_wave(run_id, execution_mode='mcp_only')
            ledger.append_event(
                run_id,
                wave_id=second_wave,
                event_type='failure_observed',
                state_before='EXECUTING',
                state_after='REPLAN',
                payload={'failure_class': 'ACCEPTANCE_FILE_SHA_MISMATCH'},
            )
            ledger.finish_wave(second_wave, status='replanned')
            terminal_wave = ledger.create_wave(run_id, execution_mode='mcp_only')
            ledger.finish_wave(terminal_wave, status='accepted')
            ledger.finish_run(run_id, status='accepted')

            report = self.snapshot_report(Path(temp))
            causes = report['overall_repair_causes']
            self.assertEqual(causes['event_counts']['source_base_drift'], 1)
            self.assertEqual(causes['unclassified_structured_failure_classes'], {'PERMISSION_REQUIRED': 1})
            self.assertEqual(
                causes['prospective_failure_detail']['detail_counts'],
                {'PERMISSION_REQUIRED:filesystem_escape': 1},
            )
            self.assertEqual(report['causal_classification']['mapped_failure_events'], 1)
            self.assertEqual(report['causal_classification']['unclassified_failure_events'], 1)
            self.assertTrue(report['policy']['permission_failure_details_are_prospective_only'])
            self.assertTrue(report['policy']['permission_failure_detail_is_not_a_causal_repair_label'])

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
