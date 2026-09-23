# Audit BG01–BG14 — source/focused proof versus live closure

**Observed:** 2026-09-23 12:24 +07
**Source:** `main@b66e0a05c50c2502cc15c57f34c4f4c8f016d884`
**Scope:** `prl-e918c7d33e70c2d304d0797e11b05fcb` revision 2
**Mode:** read-only audit and focused test execution; no live provider dispatch,
connector ACK, restart, reboot, direct ledger edit, artificial RUN, or
artificial outcome.

This document separates implementation evidence from the live/natural gates in
the canonical BG01–BG14 contract. A focused test can prove an invariant in an
isolated ledger/bridge fixture; it cannot prove a current Windows process,
client connector, natural Goal, or independent user outcome.

## 1. Fresh focused proof

Command executed from `E:\DEV\Codex-web\resources\coding-tools-mcp`:

```text
python -m pytest tests/test_run_continuation.py tests/test_codex_bridge.py \
  tests/test_live_codex_provider_restart.py tests/test_controller_continuity.py \
  tests/test_continuation_consent_http.py tests/test_goal_pursuit.py \
  tests/test_problem_lineage.py -q
```

Result:

```text
121 passed, 13 subtests passed in 196.79s
```

This result is valid source/focused evidence for the exact HEAD above. It is
not a live provider acceptance, a current-process connector receipt, or a
natural Goal outcome.

## 2. Criterion matrix

| Criterion | Source/focused evidence now present | Current evidence level | Missing before closure |
|---|---|---|---|
| BG01 exact Problem Revision/workspace/endpoint/owner; retry Start is idempotent | `run_continuation.py`: `issue_goal_continuation`, exact competing-episode guard, `materialize_matching_goal_continuation`; tests `test_goal_episode_contract_is_distinct_exact_and_controller_fenced`, `test_goal_episode_parent_ledger_materializes_exact_child`, `test_matching_goal_episode_materializes_only_exact_child_binding`, `test_problem_bound_public_grant_issues_goal_parent_materializes_child_and_starts_once`; goal resolver ambiguity/cursor tests | `FOCUSED_PASS` | A real current controller/endpoint must issue one grant and prove no duplicate pursuit/RUN in the supported client path |
| BG02 response end does not stop opted-in work; stop/revoke wins | Durable goal state, pause/revoke, parent revocation fence, one-shot consent challenge; tests `test_goal_episode_parent_revocation_fences_existing_child`, `test_explicit_host_consent_is_exact_scoped_and_one_shot`, `test_goal_click_issues_parent_materializes_child_and_starts_once` | `FOCUSED_SAFETY_PASS` | Natural detached host-turn timeline proving progress after response end and explicit stop/revoke in a live supported surface |
| BG03 PASS/FAIL/UNKNOWN comes from real proof, not model text | Exact accepted-coverage and proof identity guards; tests `test_exact_accepted_coverage_then_provisional_transition_changes_next_action`, `test_passed_proof_without_exact_accepted_claim_does_not_satisfy_criterion`, `test_patch_requires_every_approved_check_not_a_model_selected_subset`, `test_task_acceptance_bridges_only_a_covered_exact_full_problem_claim` | `FOCUSED_PASS` | Current Problem Revision must produce a non-empty exact coverage manifest and a real oracle receipt; current ledger has no outcome receipt |
| BG04 recoverable FAIL creates typed proposal and actually dispatches/observes | `continuation_driver.py` start/observe/repair paths, durable action/turn cursor, bridge `continue`; tests `test_terminal_read_dispatches_one_next_turn_on_the_same_owned_thread`, `test_failed_proof_dispatches_one_bounded_repair_turn_then_reaches_accepting`, `test_auto_resume_replans_same_run_and_dispatches_once_after_report_gate`, `test_continue_reuses_only_bridge_owned_thread_and_preserves_route` | `FOCUSED_PASS / LIVE_NOT_RUN` | Provider-backed current process must show a post-response dispatch/observe with exact turn/action/proof receipts and no manual relay |
| BG05 parent budget survives child/restart and never resets | Shared parent counters, atomic action reservation/release, exhaustion guards; tests `test_goal_episode_shared_budget_is_authoritative_across_child_runs`, `test_reserved_action_release_restores_budget_without_reusing_sequence`, `test_patch_budget_is_atomic_per_action_and_exhaustion_blocks_a_second_effect`, `test_regrant_same_runtime_generation_is_aba_fenced_at_execution_boundaries` | `FOCUSED_PASS` | A real continuation must cross restart/reconnect and show the same remaining budget in current receipts |
| BG06 duplicate/lost/unknown effect does not replay mutation | Immutable effect journal, idempotent observation, conflicting terminal rejection, pending-dispatch pause; tests `test_effect_journal_is_written_before_effect_and_is_immutable`, `test_effect_observation_is_idempotent_and_conflicting_terminal_state_is_rejected`, `test_restart_with_pending_dispatch_pauses_without_restoring_or_replaying`, `test_effect_backups_and_reobservation_never_need_a_second_patch_attempt` | `FOCUSED_SAFETY_PASS` | Isolated process fault or supported live fault must provide preimage/postimage/mixed-effect reconciliation receipt |
| BG07 reconnect/replacement revalidates source/epoch/authority and target machine | Exact cross-endpoint/successor activation receipt checks and runtime behavior fingerprint; tests `test_execution_rebind_requires_exact_cross_endpoint_receipt`, `test_execution_rebind_requires_exact_successor_activation_receipt_for_same_owner`, `test_persistent_lane_recovery_rejects_missing_consent_or_stale_epoch_without_dispatch`, `test_persistent_resume_rejects_workspace_or_session_mismatch` | `FOCUSED_PASS / CURRENT_EPOCH_NOT_ACTIVE` | Current managed Recovery Host/MCP must create a fresh activation epoch and produce exact rebind receipt; connector is currently `UNAVAILABLE` |
| BG08 no-progress/expiry/authority drift stops finitely | Typed pause/no-progress guard and idempotent telemetry; tests `test_goal_episode_no_progress_is_proof_driven_idempotent_and_fenced`, `test_auto_resume_failure_telemetry_is_natural_and_idempotent`, `test_missing_expired_revoked_and_takeover_race_are_fail_closed`, `test_claim_owner_expiry_and_renewal_fence_every_execution_boundary` | `FOCUSED_PASS` | A natural/live window must demonstrate bounded stop rather than repeated retries under unchanged evidence |
| BG09 progress/review uses the correct controller; ACCEPTING is not auto-accept | Controller continuity/checkpoint/ACK guards; tests `test_policy_checkpoint_idempotency_conflict_and_reopen_durability`, `test_ack_statuses_are_typed_idempotent_and_never_advance`, `test_runtime_checkpoint_get_and_ack_are_bounded_and_non_authoritative`, `test_patch_proposal_journals_backup_runs_structured_proof_and_stops_at_accepting` | `FOCUSED_PASS / LIVE_REVIEW_NOT_RUN` | Current connector/controller must deliver and read back a review, then show an authorized accept/reject receipt; no current client surface exists |
| BG10 natural work needs no copy or unnecessary nudge | No source test can substitute for this product outcome; the plan requires host/operator-observed intervention counts and an independent natural result | `NOT_RUN` | One predeclared natural Goal window with no manual relay/unnecessary nudge, retained all-sample telemetry and independent outcome |
| BG11 failed/replanned attempts retain causal lineage | Problem event chain, telemetry dedup and RUN/WAVE/action/proof bindings; tests `test_telemetry_without_continuation_uses_exact_problem_handoff_and_deduplicates`, `test_telemetry_without_continuation_never_invents_problem_binding`, `test_problem_run_records_host_product_session_and_continuity_core_receipts`, `test_receipt_tamper_breaks_the_problem_event_hash_chain` | `FOCUSED_PASS / CURRENT_COVERAGE_EMPTY` | Current revision must receive exact coverage/outcome joins. Ledger query currently reports zero outcome receipts for this Problem |
| BG12 idempotent/private data with explicit synthetic/missingness coverage | Strict public eight-tool schema, sensitive-evidence rejection, idempotent challenge/ACK, encoded-credential/PII scans; tests `test_schema_preserves_eight_tools_and_accepts_only_typed_grant`, `test_model_evidence_fails_closed_on_sensitive_problem_or_source_content`, `test_contract_capsule_rejects_bounded_encoded_credentials_and_pii`, `test_ack_statuses_are_typed_idempotent_and_never_advance` | `FOCUSED_PASS` | Live producer/consumer evidence must demonstrate exact provenance and distinguish natural from controlled fixture data |
| BG13 source/proof/acceptance/runtime exact; rollback retains history | Runtime behavior identity, source/epoch rebind, effect backups and acceptance guards; tests `test_runtime_behavior_identity_covers_continuation_execution`, `test_patch_context_drift_creates_no_effect_journal_or_backup`, `test_regrant_same_runtime_generation_is_aba_fenced_at_execution_boundaries`, `test_policy_rejects_scope_shell_and_definition_hash_forgery` | `FOCUSED_PASS / LIVE_NOT_PROVEN` | Current managed runtime activation, process identity and non-destructive rollback/fault receipt are required |
| BG14 confirmation only with exact user outcome; technical pass is insufficient | Problem lineage `reopen/revise/confirm` CAS and receipt-chain guards; tests `test_reopen_keeps_revision_and_revise_uses_compare_and_swap`, `test_receipt_tamper_breaks_the_problem_event_hash_chain`, `test_task_acceptance_bridges_only_a_covered_exact_full_problem_claim`, `test_public_semantic_authority_is_runtime_derived_and_claim_restores_on_failure` | `FOCUSED_GUARD_PASS / OUTCOME_MISSING` | Independent user outcome for this exact revision, absence of mandatory blocker, exact coverage manifest and authorized final transition |

## 3. What this proves and what it does not

The source packet is now substantially covered for safety and deterministic
continuation behavior. In particular, no source regression was found in the
durable grant, budget, effect-journal, rebind, controller, or problem-lineage
paths exercised by the 121-test suite.

The following remain **not run or not proven**, rather than failed:

```text
current provider/App Server dispatch       = not proven
post-response detached continuation        = not proven live
current MCP/Tunnel process identity        = unavailable
strict tools/list/server/discover          = not proven
real workspace_context                     = not proven
current activation epoch/rebind            = not proven
natural BG10 window                        = not run
independent BG14 outcome                  = missing
exact BG01–BG14 current coverage           = missing
```

The canonical ledger currently contains `goal_continuations=0`; this is
consistent with no live Goal grant being issued for the target revision. It is
not evidence that `issue_goal_continuation` is broken, and it must not be fixed
by inserting a row directly into SQLite.

## 4. Exact next implementation/acceptance action

There is no source edit justified by this focused audit alone. The next
authoritative action is a single supported-client wave:

1. Restore a supported connector/authenticated client surface.
2. Activate the current packaged/source identity through lifecycle authority,
   creating a fresh epoch and receipt.
3. Issue one explicit Goal grant for the exact current Problem Revision; keep
   the origin RUN/controller/endpoint binding.
4. Run the natural detached continuation and collect current action/turn,
   proof, budget, rebind and review receipts without calling public `observe`
   during the autonomy window.
5. Only then construct exact BG01–BG14 coverage and request the appropriate
   provisional/confirmed/reopen transition.

Do not treat this document, the focused tests, an accepted RUN count, or a
historical packaged smoke as BG14 confirmation.

**Operator checkpoint:** the source/focused wave completed with 121 tests and
13 subtests passing; it changed no source or canonical ledger state. The exact
blocker remains `WAITING_FOR_SUPPORTED_CONNECTOR`, while the implementation
paths covered by the focused suite remain green.
