# Orchestration Wave 1

- Run: `6bf97685f35c41bc8fbf556550c96eab`
- Wave: `07265af168e04b3eb452bb9e21350b7e`
- Objective: Repair the accepted-code Full Clean lifetime boundary so a valid short-lived authenticated activation request (max 60s) can create and monitor the separate durable Full Clean epoch (designed for 10 minutes) without RecoveryActionStore terminalizing the linked action at the original request deadline. Preserve normalizeActivationRequest/MAX_REQUEST_TTL_MS=60000 and immutable original request expiry; after FullCleanActivation returns the exact operation-bound durable epoch, bind the linked action to a separately named bounded durable epoch expiry only after exact operation/epoch identity validation; replay/get/active and accepted-code monitoring may use that expiry only for a valid exact durable epoch binding, otherwise retain request-expiry behavior; terminal/failed epochs remain fail-closed. Modify only electron/services/recoveryActivation.js, electron/services/recoveryActionStore.js, tests/recovery-activation.test.js. Do not touch concurrent WIP in fullCleanActivation.js, recoveryHost.js, full-clean-activation.test.js, recovery-host.test.js. Reach ACCEPTING after focused proof; do not self-accept.
- Objective revision: `1`
- Objective SHA-256: `f685214d0e0684f4dee88ebb8ead9cc14b4a6acf303ddba14db82c6bd05e5b3b`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `0bfdfcc495e703e0ca6f14ab181d6a5c3f8d4c863966e592bbcf94a2b1cd8fe9`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 35760 | 2026-09-02T09:52:26.666Z | run_started |  | PREFLIGHT |  |
| 35761 | 2026-09-02T09:52:27.091Z | observation_span_recorded |  |  |  |
| 35762 | 2026-09-02T09:52:27.332Z | solution_shadow_recommended |  |  |  |
| 35763 | 2026-09-02T09:52:27.558Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 35764 | 2026-09-02T09:52:27.741Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 35765 | 2026-09-02T09:52:27.941Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 35766 | 2026-09-02T09:52:28.157Z | state_transition | READY | ROUTED | reason=route_selected |
| 35767 | 2026-09-02T09:52:28.395Z | observation_span_recorded |  |  |  |
| 35768 | 2026-09-02T09:52:29.525Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=d430f48c5ccc40c18461fce00ee32461 |
| 35769 | 2026-09-02T09:52:29.723Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 35770 | 2026-09-02T09:52:30.594Z | patch_surface_observed |  |  |  |
| 35771 | 2026-09-02T09:52:30.840Z | patch_surface_observed |  |  |  |
| 35772 | 2026-09-02T09:52:31.048Z | patch_surface_observed |  |  |  |
| 35773 | 2026-09-02T09:52:31.229Z | observation_span_recorded |  |  |  |
| 35774 | 2026-09-02T09:52:31.515Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=d430f48c5ccc40c18461fce00ee32461 |
| 35775 | 2026-09-02T09:52:31.669Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 35776 | 2026-09-02T09:52:33.102Z | proof_cache_miss |  |  | reason=cold; stage_id=check:044f5d92d303a4d9; input_fingerprint=a753f0b31bc73986808e4ac5b65a08869439d7d8066442136c35959bc4d41125 |
| 35777 | 2026-09-02T09:52:33.527Z | managed_process_admitted |  |  | owner=default |
| 35778 | 2026-09-02T09:52:33.893Z | managed_process_started |  |  | owner=default |
| 35779 | 2026-09-02T09:52:35.334Z | managed_process_terminal |  |  | owner=default |
| 35780 | 2026-09-02T09:52:35.675Z | proof_recorded |  |  | stage_id=check:044f5d92d303a4d9; status=passed; cache_hit=False; input_fingerprint=a753f0b31bc73986808e4ac5b65a08869439d7d8066442136c35959bc4d41125 |
| 35781 | 2026-09-02T09:52:35.837Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=58f5833477877317dd6989ef1c6bdecc1a59ce2325d3fe06f312647e77c09345 |
| 35782 | 2026-09-02T09:52:36.233Z | managed_process_admitted |  |  | owner=default |
| 35783 | 2026-09-02T09:52:36.561Z | managed_process_started |  |  | owner=default |
| 35784 | 2026-09-02T09:53:39.917Z | managed_process_terminal |  |  | owner=default |
| 35785 | 2026-09-02T09:53:41.499Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=58f5833477877317dd6989ef1c6bdecc1a59ce2325d3fe06f312647e77c09345 |
| 35786 | 2026-09-02T09:53:42.549Z | managed_process_admitted |  |  | owner=default |
| 35787 | 2026-09-02T09:53:42.913Z | managed_process_started |  |  | owner=default |
| 35788 | 2026-09-02T09:53:43.126Z | observation_span_recorded |  |  |  |
| 35789 | 2026-09-02T09:53:43.416Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 35790 | 2026-09-02T09:53:43.594Z | managed_process_terminal |  |  | owner=default |
| 35791 | 2026-09-02T09:53:49.941Z | managed_process_admitted |  |  | owner=default |
| 35792 | 2026-09-02T09:53:50.240Z | managed_process_started |  |  | owner=default |
| 35793 | 2026-09-02T09:53:50.649Z | managed_process_terminal |  |  | owner=default |
| 35794 | 2026-09-02T09:53:58.751Z | managed_process_admitted |  |  | owner=default |
| 35795 | 2026-09-02T09:53:59.133Z | managed_process_started |  |  | owner=default |
| 35796 | 2026-09-02T09:53:59.607Z | managed_process_terminal |  |  | owner=default |
| 35797 | 2026-09-02T09:54:06.241Z | managed_process_admitted |  |  | owner=default |
| 35798 | 2026-09-02T09:54:06.592Z | managed_process_started |  |  | owner=default |
| 35799 | 2026-09-02T09:55:32.678Z | managed_process_terminal |  |  | owner=default |
| 35800 | 2026-09-02T10:06:22.099Z | quality_outcome_recorded |  |  |  |
| 35801 | 2026-09-02T10:06:22.264Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 35802 | 2026-09-02T10:06:22.534Z | observation_span_recorded |  |  |  |
| 35803 | 2026-09-02T10:06:22.751Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:044f5d92d303a4d9 | passed | a753f0b31bc73986808e4ac5b65a08869439d7d8066442136c35959bc4d41125 | False | 2211 | 0 |
| verify:tests | passed | 58f5833477877317dd6989ef1c6bdecc1a59ce2325d3fe06f312647e77c09345 | False | 65172 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| c213617ecc4941ac907433e69bc64e6c | accepted | 30b7d1b971b65034d3e4c95568c970fcc0e9380c | b2c51aa749f2e70c31a3a6d37dda91794875842f7602cec979524d8f1a6a7bb3 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `44`
- Chain head: `c806532929fa3f6fb4ca4cd0670f6be6aa08962a54a928a12973d203c729f6c2`
