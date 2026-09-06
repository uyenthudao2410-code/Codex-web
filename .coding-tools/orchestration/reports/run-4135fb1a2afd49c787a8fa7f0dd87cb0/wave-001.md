# Orchestration Wave 1

- Run: `4135fb1a2afd49c787a8fa7f0dd87cb0`
- Wave: `73b0f849954e4660beee87e99919650d`
- Objective: Add a focused isolated HTTP fixture regression test for latest-turn measurement envelope preservation, reader exception unknown state, and admission-closed journal non-read. Test-only maintenance; not usage instrumentation, real outcome, or natural Problem evidence.
- Objective revision: `1`
- Objective SHA-256: `42ef8ea4c710c1b5ef955021e016a29d61f5d353ffe8fd2ce345ca4ba4c63b08`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `8697ace8204e7e3da55d250d4a52d9b2b930116c`
- Worktree fingerprint: `41793d958050554095dba761787b145975bc6c97bde19c66b2cae0a8136f674f`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 40325 | 2026-09-05T04:43:14.845Z | run_started |  | PREFLIGHT |  |
| 40326 | 2026-09-05T04:43:15.174Z | observation_span_recorded |  |  |  |
| 40327 | 2026-09-05T04:43:15.480Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 40328 | 2026-09-05T04:43:15.680Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 40329 | 2026-09-05T04:43:15.893Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 40330 | 2026-09-05T04:43:16.062Z | state_transition | READY | ROUTED | reason=route_selected |
| 40331 | 2026-09-05T04:43:16.258Z | observation_span_recorded |  |  |  |
| 40332 | 2026-09-05T04:43:16.903Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=aef44cfdd3eb437b87f99bdfd04f877c |
| 40333 | 2026-09-05T04:43:17.077Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 40334 | 2026-09-05T04:43:17.693Z | patch_surface_observed |  |  |  |
| 40335 | 2026-09-05T04:43:17.876Z | observation_span_recorded |  |  |  |
| 40336 | 2026-09-05T04:43:18.263Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=aef44cfdd3eb437b87f99bdfd04f877c |
| 40337 | 2026-09-05T04:43:18.432Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 40338 | 2026-09-05T04:43:18.982Z | proof_cache_miss |  |  | reason=cold; stage_id=check:543cc2bfb83a18e9; input_fingerprint=7c4992505ae751757fcce34c4a89eee94fa267a5e6dd9c600f92ed4018d1d4d0 |
| 40339 | 2026-09-05T04:43:19.213Z | observation_span_recorded |  |  |  |
| 40340 | 2026-09-05T04:43:19.390Z | failure_observed | PROVING | PROVING | failure_class=INVALID_ARGUMENT |
| 40341 | 2026-09-05T04:43:19.625Z | state_transition | PROVING | REPLAN | reason=INVALID_ARGUMENT; failure_class=INVALID_ARGUMENT |
| 40342 | 2026-09-05T04:43:19.896Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| - | - | - | - | - | - |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `78`
- Chain head: `736a38f27e21bad55f4e9565dd11f6d227579187eb511c818545be70a128a251`
