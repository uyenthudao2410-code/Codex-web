# Orchestration Wave 1

- Run: `acc6fee6a77c41238e0cbdc7ee732b12`
- Wave: `1356baf9d16e4acbbd34b9803314cfdf`
- Objective: Apply one owner-approved exact local patch.
- Objective revision: `1`
- Objective SHA-256: `4eeedbc0220f5e63e04e69598363e92378f3246e371efb9cf5ca46f2a66b7555`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `7999c4151cb501db86f2e4d0a2275d33fc248324`
- Worktree fingerprint: `5f73f724af5f5a13dcc32f8efe213a73bf7a26752e2933bc80d859b4bf697899`
- Contract fingerprint: `d4163f217e681b413b27c432334bf607e77467876a418df351f4af9ec9bf382d`
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 60375 | 2026-10-12T17:06:19.340Z | run_started |  | PREFLIGHT |  |
| 60376 | 2026-10-12T17:06:19.709Z | observation_span_recorded |  |  |  |
| 60377 | 2026-10-12T17:06:20.023Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 60378 | 2026-10-12T17:06:20.230Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 60379 | 2026-10-12T17:06:20.462Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 60380 | 2026-10-12T17:06:20.636Z | state_transition | READY | ROUTED | reason=route_selected |
| 60381 | 2026-10-12T17:06:20.931Z | observation_span_recorded |  |  |  |
| 60382 | 2026-10-12T17:06:21.704Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=c89c137777a147cca278652a670206d9 |
| 60383 | 2026-10-12T17:06:21.917Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 60384 | 2026-10-12T17:06:22.646Z | patch_surface_observed |  |  |  |
| 60385 | 2026-10-12T17:06:22.854Z | observation_span_recorded |  |  |  |
| 60386 | 2026-10-12T17:06:23.169Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=c89c137777a147cca278652a670206d9 |
| 60387 | 2026-10-12T17:06:23.377Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 60388 | 2026-10-12T17:06:24.601Z | observation_span_recorded |  |  |  |
| 60389 | 2026-10-12T17:06:24.875Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 60390 | 2026-10-12T17:06:25.203Z | observation_stage_anchor_recorded | ACCEPTING | ACCEPTING |  |
| 60639 | 2026-10-12T19:08:25.367Z | controller_transferred | ACCEPTING | ACCEPTING |  |
| 60640 | 2026-10-12T19:08:26.559Z | observation_span_recorded |  |  |  |
| 60641 | 2026-10-12T19:08:26.748Z | failure_observed | ACCEPTING | ACCEPTING | reason=Original exact patch and readback passed; this original wave has no independently executed proof. Preserve patch and replan proof only, without applying it again.; failure_class=SOL_REJECTED |
| 60642 | 2026-10-12T19:08:26.975Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 60643 | 2026-10-12T19:08:27.250Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 60934 | 2026-10-12T19:24:29.432Z | controller_transferred | REPLAN | REPLAN |  |

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
- Events checked: `50`
- Chain head: `99f147f51f151d58789c79c1989cdaf003746bd13478aa7ebf6473f847fd6de6`
