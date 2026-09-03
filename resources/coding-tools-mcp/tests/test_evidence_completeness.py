from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from coding_tools_mcp.evaluation_report import current_ledger_baseline_report, evaluation_plane_report
from coding_tools_mcp.evidence_completeness import evidence_completeness_run_report
from coding_tools_mcp.orchestration_ledger import OrchestrationLedger


class EvidenceCompletenessTests(unittest.TestCase):
    def test_representative_and_historical_observational_are_kept_separate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OrchestrationLedger(root)
            identity = {
                'schema_version': 1,
                'root_id': 'workspace-a',
                'workspace_id': 'workspace-a',
                'session_workspace_id': 'workspace-a',
                'scope_matches_session_workspace': True,
                'content_free': True,
            }
            run_id = ledger.create_run(
                objective='representative bugfix',
                metadata={
                    'workflow': 'bugfix',
                    'measurement_integrity_epoch': 'workspace_identity_v1',
                    'workspace_identity': identity,
                    'evaluation': {'provenance': 'representative'},
                },
            )
            wave_id = ledger.create_wave(run_id, execution_mode='mcp_only', base_head='head', worktree_fp='worktree')
            ledger.append_event(
                run_id,
                wave_id=wave_id,
                event_type='solution_shadow_recommended',
                payload={'recommendation_id': 'before-write'},
            )
            ledger.append_event(run_id, wave_id=wave_id, event_type='write_lease_acquired', payload={})
            ledger.append_event(
                run_id,
                wave_id=wave_id,
                event_type='patch_surface_observed',
                payload={'complete': True, 'file_count': 1, 'line_changes': 2},
            )
            ledger.record_proof(
                run_id=run_id,
                wave_id=wave_id,
                stage_id='verify:test',
                stage_version='1',
                input_fingerprint='proof-input',
                status='passed',
                command_hash='proof-command',
                duration_ms=10,
                exit_code=0,
                metadata={'workspace_identity': identity},
            )
            ledger.record_quality_outcome(
                run_id=run_id,
                wave_id=wave_id,
                outcome={'source': 'test', 'oracle_pass': True, 'critical_defect_count': 0},
            )
            ledger.record_checkpoint(
                run_id=run_id,
                wave_id=wave_id,
                git_head='head',
                proof_fingerprint='proof-fp',
                status='accepted',
                metadata={'workspace_identity': identity, 'accepted_files': []},
            )
            ledger.record_observation_span(run_id=run_id, span={
                'span_id': 'host-span',
                'stage': 'assistant_response_visible',
                'source': 'electron',
                'measurement': 'observed_host_visible',
                'clock_domain': 'electron:1',
                'start_ms': 10,
                'end_ms': 20,
                'trace_id': 'trace-a',
                'turn_id': 'turn-a',
                'observer_plane': 'electron_chatgpt_dom',
            })
            ledger.finish_wave(wave_id, status='accepted')
            ledger.finish_run(run_id, status='accepted')
            host_event = {
                'schema_version': 6,
                'event_type': 'host_turn_span',
                'span_id': 'host-span',
                'measurement': 'observed_user_visible_to_first_assistant_visible',
                'duration_ms': 10.0,
                'run_id': run_id,
                'wave_id': wave_id,
                'trace_id': 'trace-a',
                'turn_id': 'turn-a',
            }
            journal = root / '.coding-tools' / 'evaluation' / 'chatweb-host-observations.jsonl'
            journal.parent.mkdir(parents=True, exist_ok=True)
            journal.write_text(json.dumps(host_event) + '\n', encoding='utf-8')

            representative = evidence_completeness_run_report(
                root, run_id, ledger=ledger, host_events=[host_event]
            )
            self.assertEqual(representative['workspace_identity'], 'PASS')
            self.assertEqual(representative['host_turn_correlation'], 'PASS')
            self.assertEqual(representative['solution_shadow'], 'PASS')
            self.assertEqual(representative['pre_write_order'], 'PASS')
            self.assertEqual(representative['actual_patch_surface'], 'PASS')
            self.assertEqual(representative['proof'], 'PASS')
            self.assertEqual(representative['quality_outcome'], 'PASS')
            self.assertEqual(representative['cost_usage'], 'UNKNOWN')
            self.assertEqual(representative['cross_project_contaminated'], 'NO')
            self.assertEqual(representative['promotion_eligible'], 'YES')
            self.assertEqual(representative['cohort'], 'representative')

            legacy_run = ledger.create_run(objective='legacy organic bugfix', metadata={'workflow': 'bugfix'})
            ledger.finish_run(legacy_run, status='accepted')
            historical = evidence_completeness_run_report(root, legacy_run, ledger=ledger, host_events=[host_event])
            self.assertEqual(historical['workspace_identity'], 'FAIL')
            self.assertEqual(historical['solution_shadow'], 'MISSING')
            self.assertEqual(historical['cross_project_contaminated'], 'UNKNOWN')
            self.assertEqual(historical['promotion_eligible'], 'NO')
            self.assertEqual(historical['cohort'], 'historical_observational')
            self.assertTrue(historical['policy']['historical_observational_is_not_p4_predictor_validation'])

            baseline = current_ledger_baseline_report(root)['evidence_completeness']
            self.assertEqual(baseline['cohort_counts']['representative'], 1)
            self.assertEqual(baseline['cohort_counts']['historical_observational'], 1)
            self.assertEqual(baseline['promotion_eligible_runs'], 1)

            plane = evaluation_plane_report(root, run_id=legacy_run)
            self.assertEqual(plane['evidence_completeness']['cohort'], 'historical_observational')
            self.assertEqual(plane['evidence_completeness']['promotion_eligible'], 'NO')


if __name__ == '__main__':
    unittest.main()
