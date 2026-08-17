# Orchestration Wave 1

- Run: `78c02031bba54724a61293f6b7618aa4`
- Wave: `fdcfbec98c664bb6946091dbc95c2d85`
- Objective: Fix Recovery Host replacement race RECOVERY_TUNNEL_CANDIDATE_OWNER_UNVERIFIED without weakening ownership safety. A live legacy Recovery Tunnel candidate may be left by the old host's in-flight RecoveryPlane.ensure during handoff. The new host may migrate it only after exact legacy fingerprint + tunnel readiness/PID proof. Stamp its device owner atomically with other proven legacy recovery processes, then ensureTunnel must stop/clear known-owned stale candidate or primary tunnel processes before treating the health port as unrecognized. Foreign or unproven candidates remain fail-closed.
- Mode: `mcp_only`
- Base HEAD: `4e5a5165e063b1b1816ef438babb19ca38d379d4`
- Worktree fingerprint: `cf2ba5abcc702f863b14c52cb2895cf21b6d0c25d8fb8e2be2002bf6cf314df6`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 11587 | 2026-08-17T05:22:44.756Z | run_started |  | PREFLIGHT |  |
| 11588 | 2026-08-17T05:22:44.969Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 11589 | 2026-08-17T05:22:45.165Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 11590 | 2026-08-17T05:22:45.324Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 11591 | 2026-08-17T05:22:45.499Z | state_transition | READY | ROUTED | reason=route_selected |
| 11592 | 2026-08-17T05:22:46.056Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=fb4a5e4c19414d689837af12d84951af |
| 11593 | 2026-08-17T05:22:46.207Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 11594 | 2026-08-17T05:22:47.151Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=fb4a5e4c19414d689837af12d84951af |
| 11595 | 2026-08-17T05:22:47.316Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 11596 | 2026-08-17T05:22:47.917Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:cf10ac5b7f4532c7; input_fingerprint=acec3811e04fd3de1140c543487f4840fbf624a613cba631e025761352afc3b7 |
| 11597 | 2026-08-17T05:22:48.245Z | managed_process_admitted |  |  | owner=default |
| 11598 | 2026-08-17T05:22:48.506Z | managed_process_started |  |  | owner=default |
| 11599 | 2026-08-17T05:22:48.949Z | managed_process_terminal |  |  | owner=default |
| 11600 | 2026-08-17T05:22:49.276Z | proof_recorded |  |  | stage_id=check:cf10ac5b7f4532c7; status=passed; cache_hit=False; input_fingerprint=acec3811e04fd3de1140c543487f4840fbf624a613cba631e025761352afc3b7 |
| 11601 | 2026-08-17T05:22:49.438Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:9f3f83d6b46d2388; input_fingerprint=e72a3633679a76e306d1a58aac99bd91662d26329ba5284344c41ad782dacb34 |
| 11602 | 2026-08-17T05:22:49.882Z | managed_process_admitted |  |  | owner=default |
| 11603 | 2026-08-17T05:22:50.131Z | managed_process_started |  |  | owner=default |
| 11604 | 2026-08-17T05:22:50.990Z | managed_process_terminal |  |  | owner=default |
| 11605 | 2026-08-17T05:22:51.331Z | proof_recorded |  |  | stage_id=check:9f3f83d6b46d2388; status=passed; cache_hit=False; input_fingerprint=e72a3633679a76e306d1a58aac99bd91662d26329ba5284344c41ad782dacb34 |
| 11606 | 2026-08-17T05:22:51.523Z | proof_cache_miss |  |  | reason=cold; stage_id=check:376945b1f083047c; input_fingerprint=0d784881b33c24fa3a177efea42111aa107c229c0dc62997e9e6bd86ac796345 |
| 11607 | 2026-08-17T05:22:52.033Z | managed_process_admitted |  |  | owner=default |
| 11608 | 2026-08-17T05:22:52.382Z | managed_process_started |  |  | owner=default |
| 11609 | 2026-08-17T05:22:53.431Z | managed_process_terminal |  |  | owner=default |
| 11610 | 2026-08-17T05:22:53.800Z | proof_recorded |  |  | stage_id=check:376945b1f083047c; status=passed; cache_hit=False; input_fingerprint=0d784881b33c24fa3a177efea42111aa107c229c0dc62997e9e6bd86ac796345 |
| 11611 | 2026-08-17T05:22:54.056Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:4e484c871a44ba1c; input_fingerprint=4c076bb31622a7653d783d1eed19418383117d6b1cb88a61155e34b45ae1e802 |
| 11612 | 2026-08-17T05:22:54.431Z | managed_process_admitted |  |  | owner=default |
| 11613 | 2026-08-17T05:22:54.732Z | managed_process_started |  |  | owner=default |
| 11614 | 2026-08-17T05:22:55.315Z | managed_process_terminal |  |  | owner=default |
| 11615 | 2026-08-17T05:22:55.681Z | proof_recorded |  |  | stage_id=check:4e484c871a44ba1c; status=passed; cache_hit=False; input_fingerprint=4c076bb31622a7653d783d1eed19418383117d6b1cb88a61155e34b45ae1e802 |
| 11616 | 2026-08-17T05:22:56.448Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 11617 | 2026-08-17T05:23:13.931Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 11618 | 2026-08-17T05:23:14.372Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:cf10ac5b7f4532c7 | passed | acec3811e04fd3de1140c543487f4840fbf624a613cba631e025761352afc3b7 | False | 1030 | 0 |
| check:9f3f83d6b46d2388 | passed | e72a3633679a76e306d1a58aac99bd91662d26329ba5284344c41ad782dacb34 | False | 1584 | 0 |
| check:376945b1f083047c | passed | 0d784881b33c24fa3a177efea42111aa107c229c0dc62997e9e6bd86ac796345 | False | 1902 | 0 |
| check:4e484c871a44ba1c | passed | 4c076bb31622a7653d783d1eed19418383117d6b1cb88a61155e34b45ae1e802 | False | 1278 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| da8cbb5365d7424e96865aba9d4c822d | accepted | 4e5a5165e063b1b1816ef438babb19ca38d379d4 | 0871e395874e477d960f2552da5ab7f6e2a5d5097e3c8e588bac46c4b7432618 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `32`
- Chain head: `fe70ef2c3a5f08198dbf6dcbd8f2772b4e363de0415645f32421b6d44e32e85c`
