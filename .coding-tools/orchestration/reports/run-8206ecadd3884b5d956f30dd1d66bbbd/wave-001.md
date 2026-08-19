# Orchestration Wave 1

- Run: `8206ecadd3884b5d956f30dd1d66bbbd`
- Wave: `2fc401881df846248b289bf8e77f8806`
- Objective: Diagnose the single failing multi-root regression only. Do not modify source. Run the focused workspace/session isolation test verbosely so the exact assertion/error is captured before the correction wave continues.
- Mode: `mcp_only`
- Base HEAD: `7c1c93ea72fa3465d718f7826494629426c1a9e8`
- Worktree fingerprint: `109c2d82d04f83197647a5d1a295bcd3edbd06d8724634041a64d7674ceefb78`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 19721 | 2026-08-19T05:04:54.313Z | run_started |  | PREFLIGHT |  |
| 19722 | 2026-08-19T05:04:54.453Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 19723 | 2026-08-19T05:04:54.572Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 19724 | 2026-08-19T05:04:54.724Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 19725 | 2026-08-19T05:04:54.847Z | state_transition | READY | ROUTED | reason=route_selected |
| 19726 | 2026-08-19T05:04:55.288Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=cdc84d5f1ec744c9966f7013f1d0b07a |
| 19727 | 2026-08-19T05:04:55.424Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 19728 | 2026-08-19T05:04:55.869Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=cdc84d5f1ec744c9966f7013f1d0b07a |
| 19729 | 2026-08-19T05:04:56.030Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 19730 | 2026-08-19T05:04:56.387Z | proof_cache_miss |  |  | reason=cold; stage_id=check:1ab2dfef371fbd33; input_fingerprint=1f3b4893134c4042c150d2f6c3af026b2de65d4a2b268748c86f4273548def5b |
| 19731 | 2026-08-19T05:04:56.652Z | managed_process_admitted |  |  | owner=default |
| 19732 | 2026-08-19T05:04:56.918Z | managed_process_started |  |  | owner=default |
| 19733 | 2026-08-19T05:04:57.506Z | failure_observed | PROVING | PROVING | reason=A non-terminal wave was recovered outside its original synchronous execution.; failure_class=RUNTIME_RESUME_REQUIRED |
| 19734 | 2026-08-19T05:04:57.722Z | state_transition | PROVING | REPLAN | reason=RUNTIME_RESUME_REQUIRED; failure_class=RUNTIME_RESUME_REQUIRED |
| 19735 | 2026-08-19T05:04:58.168Z | managed_process_terminal |  |  | owner=default |
| 19736 | 2026-08-19T05:04:58.474Z | proof_recorded |  |  | stage_id=check:1ab2dfef371fbd33; status=passed; cache_hit=False; input_fingerprint=1f3b4893134c4042c150d2f6c3af026b2de65d4a2b268748c86f4273548def5b |
| 19737 | 2026-08-19T05:04:58.624Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 19738 | 2026-08-19T05:04:58.789Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 19739 | 2026-08-19T05:05:11.671Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 19740 | 2026-08-19T05:05:12.092Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:1ab2dfef371fbd33 | passed | 1f3b4893134c4042c150d2f6c3af026b2de65d4a2b268748c86f4273548def5b | False | 1800 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| a2335fb64fc04928924c1be47645ed8b | accepted | 7c1c93ea72fa3465d718f7826494629426c1a9e8 | adfcb4584e938d016a8e611003f2e6e112b7b1b10ff3b24f618a1576855fbbaf | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `20`
- Chain head: `c6c7542beaaccedf225ff274729c6a2a46fb176ab7aed436b1065d231aa454e5`
