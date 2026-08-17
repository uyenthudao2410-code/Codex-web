# Orchestration Wave 2

- Run: `89a8aced08554828a6e13cd07db8ea3a`
- Wave: `1bc5c1b9b3154b08822ad854dee0d635`
- Objective: Map and close P0.3 fault-matrix cases F4 and F6 exactly as defined by docs/PRODUCTION_CLOSURE_ROLLOUT.md. Identify the production Recovery Tunnel and primary Tunnel lifecycle/restart code paths and existing tests. Design the smallest test-only real-process fixture that runs under the production services without contacting an external provider: kill Recovery Tunnel and require a new tunnel PID while Recovery MCP PID remains unchanged; kill primary Tunnel and require a new tunnel PID while Coding MCP PID remains unchanged. Preserve device identity, ports, descriptors, fail-closed ownership, and unrelated UI/local changes. Do not modify production code unless a reproducible product defect is found.
- Mode: `mcp_only`
- Base HEAD: `885260b404c2c64df1b1afa835963045ac55dbf6`
- Worktree fingerprint: `a6bb8a1978cde07bd8c75b99b5b6ce84cc008c4103aae639eacf5bd9aabca06d`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 13459 | 2026-08-17T10:03:06.969Z | wave_replanned |  | PREFLIGHT | reason=The prior wave only re-ran an existing focused test and modified zero files, so it could not address the screenshot defects. This wave uses an explicit scoped CSS/test patch: a final readability override guarantees a non-collapsing Executive Summary, larger typography, a vertical center Hub layout, and responsive restatements so the larger desktop rules do not break narrow widths. |
| 13460 | 2026-08-17T10:03:07.633Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 13461 | 2026-08-17T10:03:07.846Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 13462 | 2026-08-17T10:03:08.051Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 13463 | 2026-08-17T10:03:08.246Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 13464 | 2026-08-17T10:03:08.403Z | state_transition | READY | ROUTED | reason=route_selected |
| 13465 | 2026-08-17T10:03:09.035Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=1f594583b5c64bf6806d55f8f27ea936 |
| 13466 | 2026-08-17T10:03:09.224Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 13467 | 2026-08-17T10:03:09.973Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=1f594583b5c64bf6806d55f8f27ea936 |
| 13468 | 2026-08-17T10:03:10.164Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 13469 | 2026-08-17T10:03:10.748Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=6e3bc2cc562558a98d187fd0eddea4ae8e01678d783b4a0cfd3d8f2b6fa1da4e |
| 13470 | 2026-08-17T10:03:11.139Z | managed_process_admitted |  |  | owner=default |
| 13471 | 2026-08-17T10:03:11.430Z | managed_process_started |  |  | owner=default |
| 13472 | 2026-08-17T10:03:11.924Z | managed_process_terminal |  |  | owner=default |
| 13473 | 2026-08-17T10:03:13.216Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=6e3bc2cc562558a98d187fd0eddea4ae8e01678d783b4a0cfd3d8f2b6fa1da4e |
| 13474 | 2026-08-17T10:03:13.935Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 6e3bc2cc562558a98d187fd0eddea4ae8e01678d783b4a0cfd3d8f2b6fa1da4e | False | 2000 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `40`
- Chain head: `49f3c52210e5191be4a1a33ef6f9f160f0978d72b73d4a275740bd521811e6f4`
