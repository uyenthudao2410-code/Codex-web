# Orchestration Wave 3

- Run: `87165b2f947b42fea97fb7996d10f947`
- Wave: `3478f13633cd494084da86ada8d729db`
- Objective: Implement the bounded bootstrap stabilization bridge for first device-aware Recovery Host replacement. Current live legacy host starts replacement from recoveryTunnelCandidatePid=0, but an in-flight old-host ensure races a legacy candidate into recovery-plane-state before new-host preflightLegacyOwnershipMigration and replacement refuses immediately. Localize candidate verification/state reread APIs and tests. Design requirement: only when candidate ownership is legacy/empty and its stored candidate fingerprint equals the exact computed legacy fingerprint may replacement wait a short bounded window for candidate readiness or for candidate state to clear/promote; reread state each iteration and then apply the existing proof rules. Foreign owner, fingerprint mismatch, PID change to unproven candidate, or timeout remains fail-closed. No general compatibility mode.
- Mode: `mcp_only`
- Base HEAD: `4e5a5165e063b1b1816ef438babb19ca38d379d4`
- Worktree fingerprint: `2ee6aa157e842b7c87fcb5c1b4c3975732661c34b7801a1c2d5773719f7dceba`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 11790 | 2026-08-17T06:34:13.379Z | wave_replanned |  | PREFLIGHT | reason=The isolated recovery-plane failure now proves the concrete cause: after promotion/clear the candidate PID is null, Number(null) becomes 0, and the existing isAlive(0) guard can enter the legacy-candidate branch. Change the implementation to require a positive PID before any liveness probe, then rerun the split focused proof. |
| 11791 | 2026-08-17T06:34:13.516Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 11792 | 2026-08-17T06:34:13.658Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 11793 | 2026-08-17T06:34:13.846Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 11794 | 2026-08-17T06:34:13.963Z | state_transition | READY | ROUTED | reason=route_selected |
| 11795 | 2026-08-17T06:34:14.471Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=7f40aeb8e80b432c805a8d9e5bdc2598 |
| 11796 | 2026-08-17T06:34:14.611Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 11797 | 2026-08-17T06:34:15.206Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=7f40aeb8e80b432c805a8d9e5bdc2598 |
| 11798 | 2026-08-17T06:34:15.372Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 11799 | 2026-08-17T06:34:15.843Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:cf10ac5b7f4532c7; input_fingerprint=eda90d7fd188baebd3e3deac30bb64196529190c311d97b98f9e290248307139 |
| 11800 | 2026-08-17T06:34:16.186Z | managed_process_admitted |  |  | owner=default |
| 11801 | 2026-08-17T06:34:16.461Z | managed_process_started |  |  | owner=default |
| 11802 | 2026-08-17T06:34:17.013Z | managed_process_terminal |  |  | owner=default |
| 11803 | 2026-08-17T06:34:17.301Z | proof_recorded |  |  | stage_id=check:cf10ac5b7f4532c7; status=passed; cache_hit=False; input_fingerprint=eda90d7fd188baebd3e3deac30bb64196529190c311d97b98f9e290248307139 |
| 11804 | 2026-08-17T06:34:17.504Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:4e484c871a44ba1c; input_fingerprint=a63ef61f96f1040675df6a3be940862f2ef9cb46337331723f0ded22bb3c49ed |
| 11805 | 2026-08-17T06:34:17.821Z | managed_process_admitted |  |  | owner=default |
| 11806 | 2026-08-17T06:34:18.069Z | managed_process_started |  |  | owner=default |
| 11807 | 2026-08-17T06:34:18.513Z | managed_process_terminal |  |  | owner=default |
| 11808 | 2026-08-17T06:34:18.784Z | proof_recorded |  |  | stage_id=check:4e484c871a44ba1c; status=passed; cache_hit=False; input_fingerprint=a63ef61f96f1040675df6a3be940862f2ef9cb46337331723f0ded22bb3c49ed |
| 11809 | 2026-08-17T06:34:18.952Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:9f3f83d6b46d2388; input_fingerprint=9d7e76f47b29c6c06af58872ef97db6532b0aa154707d21826635e4fa0ea65a9 |
| 11810 | 2026-08-17T06:34:19.257Z | managed_process_admitted |  |  | owner=default |
| 11811 | 2026-08-17T06:34:19.537Z | managed_process_started |  |  | owner=default |
| 11812 | 2026-08-17T06:34:20.327Z | managed_process_terminal |  |  | owner=default |
| 11813 | 2026-08-17T06:34:20.605Z | proof_recorded |  |  | stage_id=check:9f3f83d6b46d2388; status=passed; cache_hit=False; input_fingerprint=9d7e76f47b29c6c06af58872ef97db6532b0aa154707d21826635e4fa0ea65a9 |
| 11814 | 2026-08-17T06:34:20.757Z | proof_cache_miss |  |  | reason=cold; stage_id=check:7d5b860507e0bcd6; input_fingerprint=19c1254b7be4d6581011a653dbfa2cfbb86c64df5317b0130f2ede470c6cfa80 |
| 11815 | 2026-08-17T06:34:21.134Z | managed_process_admitted |  |  | owner=default |
| 11816 | 2026-08-17T06:34:21.384Z | managed_process_started |  |  | owner=default |
| 11817 | 2026-08-17T06:34:22.779Z | managed_process_terminal |  |  | owner=default |
| 11818 | 2026-08-17T06:34:23.074Z | proof_recorded |  |  | stage_id=check:7d5b860507e0bcd6; status=passed; cache_hit=False; input_fingerprint=19c1254b7be4d6581011a653dbfa2cfbb86c64df5317b0130f2ede470c6cfa80 |
| 11819 | 2026-08-17T06:34:23.650Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 11820 | 2026-08-17T06:35:26.136Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 11821 | 2026-08-17T06:35:26.639Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:cf10ac5b7f4532c7 | passed | eda90d7fd188baebd3e3deac30bb64196529190c311d97b98f9e290248307139 | False | 1121 | 0 |
| check:4e484c871a44ba1c | passed | a63ef61f96f1040675df6a3be940862f2ef9cb46337331723f0ded22bb3c49ed | False | 977 | 0 |
| check:9f3f83d6b46d2388 | passed | 9d7e76f47b29c6c06af58872ef97db6532b0aa154707d21826635e4fa0ea65a9 | False | 1396 | 0 |
| check:7d5b860507e0bcd6 | passed | 19c1254b7be4d6581011a653dbfa2cfbb86c64df5317b0130f2ede470c6cfa80 | False | 2006 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 1052e5d307b04328ba5763080268ac3a | accepted | 4e5a5165e063b1b1816ef438babb19ca38d379d4 | 94f92a93cdd3ccb027f94720860b7aada46fdf45ae050760bc8e36eaf804c46e | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `77`
- Chain head: `d1771c24b39226da1ddfd9a88007fe964ddf6c295cb2bb30068cb33567fa9eb4`
