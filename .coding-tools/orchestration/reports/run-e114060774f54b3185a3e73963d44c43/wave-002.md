# Orchestration Wave 2

- Run: `e114060774f54b3185a3e73963d44c43`
- Wave: `fc2df36aed2e44d88a6aa59d5ee8ffd2`
- Objective: Fix Recovery Host replacement startup ordering. Two live activation attempts began with recoveryTunnelCandidatePid=0, then replacement failed within ~0.2s as RECOVERY_TUNNEL_CANDIDATE_LEGACY_MIGRATION_UNVERIFIED, proving the replacement path creates a recovery tunnel candidate before legacy ownership preflight. Localize RecoveryHost.start ordering, RecoveryPlaneService start/ensureTunnel candidate creation, and existing replacement/migration tests. Preserve existing one-time same-install legacy migration and foreign-device fail-closed behavior. Do not modify source in prepare.
- Mode: `mcp_only`
- Base HEAD: `4e5a5165e063b1b1816ef438babb19ca38d379d4`
- Worktree fingerprint: `0b1c0c748a09c8538ab1514bef16b30f60cb34e266e811260a95ea074adc7fb7`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 11718 | 2026-08-17T06:14:02.841Z | wave_replanned |  | PREFLIGHT | reason=The prior production change passed syntax/diff and 39/40 focused tests. The sole failure was caused by the new regression fixture blocking every Recovery Plane ensure after the first, including the old-host rollback start, so the activation record remained accepted. Change only the fixture to block the intended second ensure; production semantics are unchanged. |
| 11719 | 2026-08-17T06:14:03.024Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 11720 | 2026-08-17T06:14:03.226Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 11721 | 2026-08-17T06:14:03.400Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 11722 | 2026-08-17T06:14:03.605Z | state_transition | READY | ROUTED | reason=route_selected |
| 11723 | 2026-08-17T06:14:04.148Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=891bb6afd7dd4746a24cc419a3f6f575 |
| 11724 | 2026-08-17T06:14:04.371Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 11725 | 2026-08-17T06:14:04.988Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=891bb6afd7dd4746a24cc419a3f6f575 |
| 11726 | 2026-08-17T06:14:05.155Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 11727 | 2026-08-17T06:14:05.654Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:8be7cde4d81ebb48; input_fingerprint=d9a8725367f65037e25b3a264b31950367c38c052580ad5953a56c40e96d6855 |
| 11728 | 2026-08-17T06:14:06.085Z | managed_process_admitted |  |  | owner=default |
| 11729 | 2026-08-17T06:14:06.471Z | managed_process_started |  |  | owner=default |
| 11730 | 2026-08-17T06:14:07.040Z | managed_process_terminal |  |  | owner=default |
| 11731 | 2026-08-17T06:14:07.360Z | proof_recorded |  |  | stage_id=check:8be7cde4d81ebb48; status=passed; cache_hit=False; input_fingerprint=d9a8725367f65037e25b3a264b31950367c38c052580ad5953a56c40e96d6855 |
| 11732 | 2026-08-17T06:14:07.560Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:23bff18b9aaa12d4; input_fingerprint=bb046c4a313b845aab67500d83355852df57927229d6c789b6daa623d5ba0583 |
| 11733 | 2026-08-17T06:14:07.923Z | managed_process_admitted |  |  | owner=default |
| 11734 | 2026-08-17T06:14:08.192Z | managed_process_started |  |  | owner=default |
| 11735 | 2026-08-17T06:14:08.706Z | managed_process_terminal |  |  | owner=default |
| 11736 | 2026-08-17T06:14:09.103Z | proof_recorded |  |  | stage_id=check:23bff18b9aaa12d4; status=passed; cache_hit=False; input_fingerprint=bb046c4a313b845aab67500d83355852df57927229d6c789b6daa623d5ba0583 |
| 11737 | 2026-08-17T06:14:09.275Z | proof_cache_miss |  |  | reason=cold; stage_id=check:62a49c9f53181b4d; input_fingerprint=71d007dd7d3be8c35f22722fd6ec8e512fff161aaeb211442eb40f9ae4421097 |
| 11738 | 2026-08-17T06:14:09.658Z | managed_process_admitted |  |  | owner=default |
| 11739 | 2026-08-17T06:14:09.988Z | managed_process_started |  |  | owner=default |
| 11740 | 2026-08-17T06:14:11.613Z | managed_process_terminal |  |  | owner=default |
| 11741 | 2026-08-17T06:14:12.031Z | proof_recorded |  |  | stage_id=check:62a49c9f53181b4d; status=passed; cache_hit=False; input_fingerprint=71d007dd7d3be8c35f22722fd6ec8e512fff161aaeb211442eb40f9ae4421097 |
| 11742 | 2026-08-17T06:14:12.688Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 11743 | 2026-08-17T06:15:25.419Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 11744 | 2026-08-17T06:15:25.804Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:8be7cde4d81ebb48 | passed | d9a8725367f65037e25b3a264b31950367c38c052580ad5953a56c40e96d6855 | False | 1362 | 0 |
| check:23bff18b9aaa12d4 | passed | bb046c4a313b845aab67500d83355852df57927229d6c789b6daa623d5ba0583 | False | 1170 | 0 |
| check:62a49c9f53181b4d | passed | 71d007dd7d3be8c35f22722fd6ec8e512fff161aaeb211442eb40f9ae4421097 | False | 2368 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 82f05cdd611442188d5d1e8abb859c83 | accepted | 4e5a5165e063b1b1816ef438babb19ca38d379d4 | c36751474ba4733afb720c37313beac6131fed8d65bd4de6427e9f0ff78a36b6 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `55`
- Chain head: `0e64ef7fecde779d3bc45a89158a8730ba06fad438db958c35f3c30e3a59fc7e`
