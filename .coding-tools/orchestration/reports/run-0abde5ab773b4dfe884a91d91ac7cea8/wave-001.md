# Orchestration Wave 1

- Run: `0abde5ab773b4dfe884a91d91ac7cea8`
- Wave: `b5c5494dc9434917b511262bfd26af28`
- Objective: P1.A2: expose trusted content-free observation spans through task_control action=observation and return the current critical-path projection. Add strict public schema and focused runtime/schema tests. Measurement only; no routing or acceptance changes.
- Mode: `mcp_only`
- Base HEAD: `7236cd6a72c27e6eb7679585c115220cc54ae842`
- Worktree fingerprint: `eaec21a8d55d3026c192ed4e37dc2c0a4ff7c56e4b67c21d7c25a71ad044461c`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 4869 | 2026-08-15T08:05:58.836Z | run_started |  | PREFLIGHT |  |
| 4870 | 2026-08-15T08:05:59.404Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 4871 | 2026-08-15T08:05:59.633Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 4872 | 2026-08-15T08:05:59.941Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 4873 | 2026-08-15T08:06:00.161Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 4874 | 2026-08-15T08:06:00.356Z | state_transition | READY | ROUTED | reason=route_selected |
| 4875 | 2026-08-15T08:06:01.067Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=044708c742ab4ab4ae04bbcf7fc6e3ef |
| 4876 | 2026-08-15T08:06:01.272Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 4877 | 2026-08-15T08:06:02.054Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=044708c742ab4ab4ae04bbcf7fc6e3ef |
| 4878 | 2026-08-15T08:06:02.250Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 4879 | 2026-08-15T08:06:02.999Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=924327a524ebaabfce17481ee6e605ce4bec3cf6af8ef1498d04aa054e68fb5c |
| 4880 | 2026-08-15T08:06:34.361Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=924327a524ebaabfce17481ee6e605ce4bec3cf6af8ef1498d04aa054e68fb5c |
| 4881 | 2026-08-15T08:06:35.044Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 4882 | 2026-08-15T08:06:43.852Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 924327a524ebaabfce17481ee6e605ce4bec3cf6af8ef1498d04aa054e68fb5c | False | 31047 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 295f385aede04b039ea386774d33a3ea | accepted | 7236cd6a72c27e6eb7679585c115220cc54ae842 | b52592ce2c663fe30eb5528fd1b0fd23cd4458f00afdc4c01b8aeea06482c356 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `14`
- Chain head: `797c3095b18b9506923097c86a218e843afa0f6734d5ec0181cb7844790eab7c`
