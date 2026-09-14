# Orchestration Wave 3

- Run: `68ceae45021b411cb77e7273053d48a1`
- Wave: `46941b0846104c61b615572518ef737e`
- Objective: Localize the smallest causal code path for the reproduced controller lease lifecycle defect. Inspect only the execution hub accept path and orchestration/controller lease methods that reclaim, release, checkpoint, or finalize a controller lease. Identify why an explicitly reclaimed expired historical RUN controller is released immediately after successful accept. Do not modify files or run broad tests in this wave.
- Objective revision: `3`
- Objective SHA-256: `a631f1873e0369297572221ef04e32499b48ae647d586ec38fa342b47a43204f`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `ae04947d5969e9ee92bf1fe7532bf30e186f8280`
- Worktree fingerprint: `74987f7ab6fe7151abc3dec844762710aad996d1d047389a538b2c603087ff73`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 55064 | 2026-09-14T13:13:46.803Z | wave_replanned |  | PREFLIGHT | reason=Focused reproduction proved a deterministic lifecycle defect: accept reaches CHECKPOINTED and preserves the same ChatWeb controller identity, but the reclaimed lease becomes released. Change strategy to source localization only before patching. |
| 55065 | 2026-09-14T13:13:47.229Z | observation_span_recorded |  |  |  |
| 55066 | 2026-09-14T13:13:53.013Z | observation_span_recorded |  |  |  |
| 55067 | 2026-09-14T13:13:53.273Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 55068 | 2026-09-14T13:13:53.492Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 55069 | 2026-09-14T13:13:53.714Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 55070 | 2026-09-14T13:13:53.926Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 55071 | 2026-09-14T13:13:54.162Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 55072 | 2026-09-14T13:13:54.404Z | state_transition | READY | ROUTED | reason=route_selected |
| 55073 | 2026-09-14T13:13:54.688Z | observation_span_recorded |  |  |  |
| 55074 | 2026-09-14T13:13:55.306Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=081aeb6d85fd410fa04a79a6fda841cc |
| 55075 | 2026-09-14T13:13:55.372Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 55076 | 2026-09-14T13:13:55.707Z | observation_span_recorded |  |  |  |
| 55077 | 2026-09-14T13:13:55.962Z | failure_observed | EXECUTING | EXECUTING | failure_class=INVALID_ARGUMENT |
| 55078 | 2026-09-14T13:13:56.304Z | write_lease_revoked | EXECUTING | EXECUTING | reason=state_transition:replan; owner=MCP; lease_id=081aeb6d85fd410fa04a79a6fda841cc |
| 55079 | 2026-09-14T13:13:56.545Z | state_transition | EXECUTING | REPLAN | reason=INVALID_ARGUMENT; failure_class=INVALID_ARGUMENT |
| 55080 | 2026-09-14T13:13:56.840Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 55081 | 2026-09-14T13:14:35.083Z | controller_knowledge_read_observed |  |  |  |

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
- Events checked: `98`
- Chain head: `192bfc885ac0fb77cc6b896ddaaed58c513f1f1ead62c4bba5dd70fff2eb6166`
