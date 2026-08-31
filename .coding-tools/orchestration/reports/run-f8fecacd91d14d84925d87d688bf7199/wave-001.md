# Orchestration Wave 1

- Run: `f8fecacd91d14d84925d87d688bf7199`
- Wave: `01947bc07f6f4eabbcef096499d3eeef`
- Objective: Apply only the exact-current Control Center slice of the truthful token-metering fix: render host Tool-call-card tokens as a separate evidence plane from MCP tools/list and controller/provider UsageEvents. Because the current MCP transport does not expose an exact post-call host receipt, render Tool-card tokens as unavailable rather than estimated. Preserve all unrelated bytes.
- Objective revision: `1`
- Objective SHA-256: `72e31c61af5df3bc803c6742fd5f0363b79b1cce1c72937b06ec00a2fd45660f`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `9b766f241432b9b5bfa8aa75ae2f1816709a2c2d`
- Worktree fingerprint: `da4bde021da882b709da1ff1fe4ac79d23913268830125ef8e0c0cb193caa9a0`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 32746 | 2026-08-30T15:38:24.563Z | run_started |  | PREFLIGHT |  |
| 32747 | 2026-08-30T15:38:24.986Z | observation_span_recorded |  |  |  |
| 32748 | 2026-08-30T15:39:29.701Z | solution_shadow_recommended |  |  |  |
| 32749 | 2026-08-30T15:39:29.880Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 32750 | 2026-08-30T15:39:30.088Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 32751 | 2026-08-30T15:39:30.308Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 32752 | 2026-08-30T15:39:30.515Z | state_transition | READY | ROUTED | reason=route_selected |
| 32753 | 2026-08-30T15:39:30.738Z | observation_span_recorded |  |  |  |
| 32754 | 2026-08-30T15:39:31.738Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=40cfe4fcf5544bd29afabc7a9d98ac67 |
| 32755 | 2026-08-30T15:39:31.956Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 32756 | 2026-08-30T15:39:32.857Z | patch_surface_observed |  |  |  |
| 32757 | 2026-08-30T15:39:33.091Z | patch_surface_observed |  |  |  |
| 32758 | 2026-08-30T15:39:33.335Z | observation_span_recorded |  |  |  |
| 32759 | 2026-08-30T15:39:33.680Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=40cfe4fcf5544bd29afabc7a9d98ac67 |
| 32760 | 2026-08-30T15:39:33.880Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 32761 | 2026-08-30T15:39:35.642Z | observation_span_recorded |  |  |  |
| 32762 | 2026-08-30T15:39:35.823Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 32763 | 2026-08-30T15:40:15.173Z | observation_span_recorded |  |  |  |
| 32764 | 2026-08-30T15:40:15.358Z | failure_observed | ACCEPTING | ACCEPTING | reason=Reject this partial wave as incomplete/unproven: it changed only Control Center and its source assertion, recorded zero proof, and does not yet implement the backend tool_call_metering projection or remove visible Dashboard byte-derived token fallback. Preserve the two applied files and replan the same RUN to complete the causal scope with focused Node/Python proof.; failure_class=SOL_REJECTED |
| 32765 | 2026-08-30T15:40:15.586Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 32766 | 2026-08-30T15:40:15.847Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

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
- Events checked: `25`
- Chain head: `20d5ee27aba2e18813565098be2b8f37d0ee32d0f4894d20aa5683a6f4691b12`
