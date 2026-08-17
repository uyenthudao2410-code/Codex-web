# Orchestration Wave 1

- Run: `e114060774f54b3185a3e73963d44c43`
- Wave: `dfff89eca91d4a2cbffaa7a9187c3f65`
- Objective: Fix Recovery Host replacement startup ordering. Two live activation attempts began with recoveryTunnelCandidatePid=0, then replacement failed within ~0.2s as RECOVERY_TUNNEL_CANDIDATE_LEGACY_MIGRATION_UNVERIFIED, proving the replacement path creates a recovery tunnel candidate before legacy ownership preflight. Localize RecoveryHost.start ordering, RecoveryPlaneService start/ensureTunnel candidate creation, and existing replacement/migration tests. Preserve existing one-time same-install legacy migration and foreign-device fail-closed behavior. Do not modify source in prepare.
- Mode: `mcp_only`
- Base HEAD: `4e5a5165e063b1b1816ef438babb19ca38d379d4`
- Worktree fingerprint: `ccb59866f92653570196b5ff64a0cd86ac4cef1d11498f28d3093a6de5692e16`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 11690 | 2026-08-17T06:10:23.042Z | run_started |  | PREFLIGHT |  |
| 11691 | 2026-08-17T06:10:23.997Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 11692 | 2026-08-17T06:13:02.774Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 11693 | 2026-08-17T06:13:02.950Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 11694 | 2026-08-17T06:13:03.151Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 11695 | 2026-08-17T06:13:03.306Z | state_transition | READY | ROUTED | reason=route_selected |
| 11696 | 2026-08-17T06:13:03.980Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=122e0d7400634d3493ec76550ccaa676 |
| 11697 | 2026-08-17T06:13:04.137Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 11698 | 2026-08-17T06:13:05.040Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=122e0d7400634d3493ec76550ccaa676 |
| 11699 | 2026-08-17T06:13:05.229Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 11700 | 2026-08-17T06:13:05.733Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:8be7cde4d81ebb48; input_fingerprint=208b148c8e0eac2fe20744a06a8e2f69349d3cfd486753f82301498038556c27 |
| 11701 | 2026-08-17T06:13:06.144Z | managed_process_admitted |  |  | owner=default |
| 11702 | 2026-08-17T06:13:06.858Z | managed_process_started |  |  | owner=default |
| 11703 | 2026-08-17T06:13:07.311Z | managed_process_terminal |  |  | owner=default |
| 11704 | 2026-08-17T06:13:07.841Z | proof_recorded |  |  | stage_id=check:8be7cde4d81ebb48; status=passed; cache_hit=False; input_fingerprint=208b148c8e0eac2fe20744a06a8e2f69349d3cfd486753f82301498038556c27 |
| 11705 | 2026-08-17T06:13:08.023Z | proof_cache_miss |  |  | reason=cold; stage_id=check:23bff18b9aaa12d4; input_fingerprint=f954960a1c66d98b83a8394e50582580c1d2600b8bdae090c867d3ad2f6ee227 |
| 11706 | 2026-08-17T06:13:08.389Z | managed_process_admitted |  |  | owner=default |
| 11707 | 2026-08-17T06:13:08.702Z | managed_process_started |  |  | owner=default |
| 11708 | 2026-08-17T06:13:09.191Z | managed_process_terminal |  |  | owner=default |
| 11709 | 2026-08-17T06:13:09.536Z | proof_recorded |  |  | stage_id=check:23bff18b9aaa12d4; status=passed; cache_hit=False; input_fingerprint=f954960a1c66d98b83a8394e50582580c1d2600b8bdae090c867d3ad2f6ee227 |
| 11710 | 2026-08-17T06:13:09.706Z | proof_cache_miss |  |  | reason=cold; stage_id=check:62a49c9f53181b4d; input_fingerprint=0226c918a622941bece29aaa528f2fc05e72ca1934169b5408483f9eab602257 |
| 11711 | 2026-08-17T06:13:10.140Z | managed_process_admitted |  |  | owner=default |
| 11712 | 2026-08-17T06:13:10.448Z | managed_process_started |  |  | owner=default |
| 11713 | 2026-08-17T06:13:13.531Z | managed_process_terminal |  |  | owner=default |
| 11714 | 2026-08-17T06:13:13.919Z | proof_recorded |  |  | stage_id=check:62a49c9f53181b4d; status=failed; cache_hit=False; input_fingerprint=0226c918a622941bece29aaa528f2fc05e72ca1934169b5408483f9eab602257 |
| 11715 | 2026-08-17T06:13:14.131Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 11716 | 2026-08-17T06:13:14.340Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 11717 | 2026-08-17T06:13:14.573Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:8be7cde4d81ebb48 | passed | 208b148c8e0eac2fe20744a06a8e2f69349d3cfd486753f82301498038556c27 | False | 1538 | 0 |
| check:23bff18b9aaa12d4 | passed | f954960a1c66d98b83a8394e50582580c1d2600b8bdae090c867d3ad2f6ee227 | False | 1184 | 0 |
| check:62a49c9f53181b4d | failed | 0226c918a622941bece29aaa528f2fc05e72ca1934169b5408483f9eab602257 | False | 3811 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `55`
- Chain head: `0e64ef7fecde779d3bc45a89158a8730ba06fad438db958c35f3c30e3a59fc7e`
