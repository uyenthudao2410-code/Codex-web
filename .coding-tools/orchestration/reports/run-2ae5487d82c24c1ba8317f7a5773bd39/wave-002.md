# Orchestration Wave 2

- Run: `2ae5487d82c24c1ba8317f7a5773bd39`
- Wave: `942e5dcd2efb42ea874856fe0e466572`
- Objective: Complete final pre-P3 intention-to-treat paired-analysis readiness without starting P3 treatment. Extend paired_policy_evaluation output so all explicit representative comparable pairs, regardless of terminal status, report symmetric baseline/candidate acceptance rates, first-pass acceptance rates, and repair rates. Keep TTAR conditional on both accepted. Add a regression where baseline is accepted and SERVER_FIRST_DETERMINISTIC_V1 candidate is aborted with a replan, proving the aborted candidate remains in pair_count and yields candidate_acceptance_rate=0, candidate_first_pass_rate=0, candidate_repair_rate=1 instead of being survivor-filtered. Preserve exact pair identity, unknown cost semantics, automatic_activation=false, and existing ledger/public MCP semantics.
- Mode: `mcp_only`
- Base HEAD: `bc07e240740726d9a5ddbd590e01568344a92440`
- Worktree fingerprint: `cd979bc27966ea5669b116a2b9b8e9c7224abd3359a33f20eb722e2c96deded1`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 15748 | 2026-08-17T20:02:20.444Z | wave_replanned |  | PREFLIGHT | reason=The first proof failed only because the new regression fixture emitted a REPLAN event but did not finish a wave with EOCL status replanned. Ledger repair_count is defined from replanned wave status. Preserve production analysis changes and correct the fixture to model one replanned wave followed by an aborted terminal wave. |
| 15749 | 2026-08-17T20:02:20.872Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 15750 | 2026-08-17T20:02:21.071Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 15751 | 2026-08-17T20:02:21.222Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 15752 | 2026-08-17T20:02:21.355Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 15753 | 2026-08-17T20:02:21.481Z | state_transition | READY | ROUTED | reason=route_selected |
| 15754 | 2026-08-17T20:02:21.883Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=fd0d31ee0aab4414a2e5e1bde8f77d3c |
| 15755 | 2026-08-17T20:02:21.995Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 15756 | 2026-08-17T20:02:22.442Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=fd0d31ee0aab4414a2e5e1bde8f77d3c |
| 15757 | 2026-08-17T20:02:22.566Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 15758 | 2026-08-17T20:02:22.889Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:d9a732e581c2f22f; input_fingerprint=58c851def17f3726c3ff156c57c4b1cd9bd191014f49ac72b797d2b1a322d661 |
| 15759 | 2026-08-17T20:02:23.217Z | managed_process_admitted |  |  | owner=default |
| 15760 | 2026-08-17T20:02:23.426Z | managed_process_started |  |  | owner=default |
| 15761 | 2026-08-17T20:02:23.878Z | managed_process_terminal |  |  | owner=default |
| 15762 | 2026-08-17T20:02:24.116Z | proof_recorded |  |  | stage_id=check:d9a732e581c2f22f; status=passed; cache_hit=False; input_fingerprint=58c851def17f3726c3ff156c57c4b1cd9bd191014f49ac72b797d2b1a322d661 |
| 15763 | 2026-08-17T20:02:24.264Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:80a1a46bd01d26a3; input_fingerprint=371a1d01410913b524d82eb9f5485bce72a8f293ba81df1a1806a2a49eb0a358 |
| 15764 | 2026-08-17T20:02:24.579Z | managed_process_admitted |  |  | owner=default |
| 15765 | 2026-08-17T20:02:24.801Z | managed_process_started |  |  | owner=default |
| 15766 | 2026-08-17T20:02:25.173Z | managed_process_terminal |  |  | owner=default |
| 15767 | 2026-08-17T20:02:25.395Z | proof_recorded |  |  | stage_id=check:80a1a46bd01d26a3; status=passed; cache_hit=False; input_fingerprint=371a1d01410913b524d82eb9f5485bce72a8f293ba81df1a1806a2a49eb0a358 |
| 15768 | 2026-08-17T20:02:25.530Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:6f5f72f78509db88; input_fingerprint=4a5fcd75a7497ad56881840adc2dd7329ae060d728b5ebfa3e0de31e5617fd50 |
| 15769 | 2026-08-17T20:02:25.815Z | managed_process_admitted |  |  | owner=default |
| 15770 | 2026-08-17T20:02:26.047Z | managed_process_started |  |  | owner=default |
| 15771 | 2026-08-17T20:02:26.405Z | managed_process_terminal |  |  | owner=default |
| 15772 | 2026-08-17T20:02:26.631Z | proof_recorded |  |  | stage_id=check:6f5f72f78509db88; status=passed; cache_hit=False; input_fingerprint=4a5fcd75a7497ad56881840adc2dd7329ae060d728b5ebfa3e0de31e5617fd50 |
| 15773 | 2026-08-17T20:02:26.786Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=939e78902982e5a0930af2eb21e1a9486e8224796ea71706865441e954fb6dc4 |
| 15774 | 2026-08-17T20:02:27.063Z | managed_process_admitted |  |  | owner=default |
| 15775 | 2026-08-17T20:02:27.376Z | managed_process_started |  |  | owner=default |
| 15776 | 2026-08-17T20:02:33.613Z | managed_process_terminal |  |  | owner=default |
| 15777 | 2026-08-17T20:02:34.763Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=939e78902982e5a0930af2eb21e1a9486e8224796ea71706865441e954fb6dc4 |
| 15778 | 2026-08-17T20:02:35.223Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 15779 | 2026-08-17T20:04:08.605Z | managed_process_admitted |  |  | owner=default |
| 15780 | 2026-08-17T20:04:08.878Z | managed_process_started |  |  | owner=default |
| 15781 | 2026-08-17T20:04:09.261Z | managed_process_terminal |  |  | owner=default |
| 15782 | 2026-08-17T20:04:22.205Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 15783 | 2026-08-17T20:04:22.463Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:d9a732e581c2f22f | passed | 58c851def17f3726c3ff156c57c4b1cd9bd191014f49ac72b797d2b1a322d661 | False | 941 | 0 |
| check:80a1a46bd01d26a3 | passed | 371a1d01410913b524d82eb9f5485bce72a8f293ba81df1a1806a2a49eb0a358 | False | 849 | 0 |
| check:6f5f72f78509db88 | passed | 4a5fcd75a7497ad56881840adc2dd7329ae060d728b5ebfa3e0de31e5617fd50 | False | 819 | 0 |
| verify:tests | passed | 939e78902982e5a0930af2eb21e1a9486e8224796ea71706865441e954fb6dc4 | False | 7655 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 7c5207ad789d4a0f95fd016848737a1f | accepted | bc07e240740726d9a5ddbd590e01568344a92440 | 00fcbe372f23cc3191b278c3b132a6eb094eb7fda3149b9f8179a22a09f8b76b | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `69`
- Chain head: `286be33bc51845409aa2651b2d40993524be52729f737d72d3c1a15045089563`
