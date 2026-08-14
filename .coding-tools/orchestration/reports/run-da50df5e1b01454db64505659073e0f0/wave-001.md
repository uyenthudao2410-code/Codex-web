# Orchestration Wave 1

- Run: `da50df5e1b01454db64505659073e0f0`
- Wave: `d4f717a776ec45a6bdc39841ecbbca47`
- Objective: P2A lifecycle reconciliation: make OrchestrationLedger.reconcile_stale_runs preserve live ownership and repair parent/child terminal consistency. A non-expired controller lease must protect an active run from stale reconciliation. When a run becomes stale, every active child wave must become aborted with finished_at and a bounded lifecycle-reconcile event. Also repair pre-existing terminal parents with lingering active child waves idempotently: accepted->accepted/CHECKPOINTED, blocked->blocked/BLOCKED, stale|aborted->aborted/ABORTED. Preserve all evidence, return contract (only newly stale run ids), integrity chain, and live background/lane/write-fence protection. Add focused tests for child terminalization, controller protection, historical terminal-parent repair, and idempotency. No TaskState projection change in this wave.
- Mode: `mcp_only`
- Base HEAD: `5decaa48300b10a6df39676c677745bc881cd7d9`
- Worktree fingerprint: `f19839c353e80c4ae5da555ad20d9561808c3f77a07c4513ae7c39af2802c4c9`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 3221 | 2026-08-14T18:03:42.496Z | run_started |  | PREFLIGHT |  |
| 3222 | 2026-08-14T18:03:42.757Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 3223 | 2026-08-14T18:03:42.883Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 3224 | 2026-08-14T18:03:43.040Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 3225 | 2026-08-14T18:03:43.173Z | state_transition | READY | ROUTED | reason=route_selected |
| 3226 | 2026-08-14T18:03:43.658Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=981a0f141d7545cb946afc991853305b |
| 3227 | 2026-08-14T18:03:43.808Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 3228 | 2026-08-14T18:03:44.359Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=981a0f141d7545cb946afc991853305b |
| 3229 | 2026-08-14T18:03:44.473Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 3230 | 2026-08-14T18:03:44.812Z | proof_cache_miss |  |  | reason=cold; stage_id=check:5706c0a1bcfa7919; input_fingerprint=1d7cf176b18ef04d573f2ece5614ced2e528d645fdd4002249687c18a4d2f30e |
| 3231 | 2026-08-14T18:03:46.125Z | proof_recorded |  |  | stage_id=check:5706c0a1bcfa7919; status=passed; cache_hit=False; input_fingerprint=1d7cf176b18ef04d573f2ece5614ced2e528d645fdd4002249687c18a4d2f30e |
| 3232 | 2026-08-14T18:03:46.430Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 3233 | 2026-08-14T18:03:56.816Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:5706c0a1bcfa7919 | passed | 1d7cf176b18ef04d573f2ece5614ced2e528d645fdd4002249687c18a4d2f30e | False | 1008 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 278aed550e0948a8962417d318f8a536 | accepted | 5decaa48300b10a6df39676c677745bc881cd7d9 | b31005bca9d6425970fd7a64931b9e82ce3d0a0bdef46de4f8cfde79f51ebdf5 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `13`
- Chain head: `8607226011bd96e51f42a6646bdd118e0bcb1d961d0da7007c39762c7811eb0d`
