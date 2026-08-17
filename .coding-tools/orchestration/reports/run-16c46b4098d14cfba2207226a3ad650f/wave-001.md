# Orchestration Wave 1

- Run: `16c46b4098d14cfba2207226a3ad650f`
- Wave: `50dc3fd12732494d9597e08b8ee5dd74`
- Objective: P2 final readiness reporting closure before P3: add aggregate causal-classification coverage and oracle-observation coverage to the existing rework diagnosis report, using only already observed ledger evidence. Preserve CHECK_FAILED and other unmapped structured failures as unclassified; preserve unknown oracle as unknown; do not change remediation behavior or public schema.
- Mode: `mcp_only`
- Base HEAD: `775d92716f90ada3cfa909d8f0069c46d204ab51`
- Worktree fingerprint: `c8e09216432e7ead7ec2792b7f3a354b61d9ca7fc4bb2bc610f5136e9976bfca`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 15601 | 2026-08-17T19:24:44.110Z | run_started |  | PREFLIGHT |  |
| 15602 | 2026-08-17T19:24:49.740Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 15603 | 2026-08-17T19:25:20.287Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 15604 | 2026-08-17T19:25:20.421Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 15605 | 2026-08-17T19:25:20.555Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 15606 | 2026-08-17T19:25:20.670Z | state_transition | READY | ROUTED | reason=route_selected |
| 15607 | 2026-08-17T19:25:21.081Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=29c1c347c8c44062a6ddd74601cd4b40 |
| 15608 | 2026-08-17T19:25:21.229Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 15609 | 2026-08-17T19:25:21.711Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=29c1c347c8c44062a6ddd74601cd4b40 |
| 15610 | 2026-08-17T19:25:21.814Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 15611 | 2026-08-17T19:25:22.121Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:80a1a46bd01d26a3; input_fingerprint=b8c22b5a3d795e325d651c2083150e3c78a6a65bc2d9d85dcf118a62cf41391e |
| 15612 | 2026-08-17T19:25:22.577Z | managed_process_admitted |  |  | owner=default |
| 15613 | 2026-08-17T19:25:22.805Z | managed_process_started |  |  | owner=default |
| 15614 | 2026-08-17T19:25:23.161Z | managed_process_terminal |  |  | owner=default |
| 15615 | 2026-08-17T19:25:23.377Z | proof_recorded |  |  | stage_id=check:80a1a46bd01d26a3; status=passed; cache_hit=False; input_fingerprint=b8c22b5a3d795e325d651c2083150e3c78a6a65bc2d9d85dcf118a62cf41391e |
| 15616 | 2026-08-17T19:25:23.516Z | proof_cache_miss |  |  | reason=cold; stage_id=check:20af4e8e69d7c88b; input_fingerprint=f6acbae9871cd6ba4a4510feebfbc600b54a785fcff68654b417df3086a2834d |
| 15617 | 2026-08-17T19:25:23.927Z | managed_process_admitted |  |  | owner=default |
| 15618 | 2026-08-17T19:25:24.160Z | managed_process_started |  |  | owner=default |
| 15619 | 2026-08-17T19:25:24.517Z | managed_process_terminal |  |  | owner=default |
| 15620 | 2026-08-17T19:25:24.765Z | proof_recorded |  |  | stage_id=check:20af4e8e69d7c88b; status=passed; cache_hit=False; input_fingerprint=f6acbae9871cd6ba4a4510feebfbc600b54a785fcff68654b417df3086a2834d |
| 15621 | 2026-08-17T19:25:24.889Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=766a19770753af05478ef16da8e6a865904745d499bc68a92b2b2004c158beec |
| 15622 | 2026-08-17T19:25:25.299Z | managed_process_admitted |  |  | owner=default |
| 15623 | 2026-08-17T19:25:25.511Z | managed_process_started |  |  | owner=default |
| 15624 | 2026-08-17T19:25:26.144Z | managed_process_terminal |  |  | owner=default |
| 15625 | 2026-08-17T19:25:27.319Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=766a19770753af05478ef16da8e6a865904745d499bc68a92b2b2004c158beec |
| 15626 | 2026-08-17T19:25:27.812Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 15627 | 2026-08-17T19:28:14.746Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 15628 | 2026-08-17T19:28:15.018Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:80a1a46bd01d26a3 | passed | b8c22b5a3d795e325d651c2083150e3c78a6a65bc2d9d85dcf118a62cf41391e | False | 861 | 0 |
| check:20af4e8e69d7c88b | passed | f6acbae9871cd6ba4a4510feebfbc600b54a785fcff68654b417df3086a2834d | False | 840 | 0 |
| verify:tests | passed | 766a19770753af05478ef16da8e6a865904745d499bc68a92b2b2004c158beec | False | 1906 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 5f21ad9ac88842c7a3e7aa976d9fd8a3 | accepted | 775d92716f90ada3cfa909d8f0069c46d204ab51 | 2345035d0849a5379a5c28630492e11d8e30836ad4c7d852694fe328b666260a | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `28`
- Chain head: `388b5aea128dc1d8281337a6e9e896e1123d17909878dbe58cbe1c6cf6d4c0a9`
