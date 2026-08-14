# Orchestration Wave 1

- Run: `ffad0a34bd9d4980b9c5abeb5d97b848`
- Wave: `3302df8699404fc3afd36ded809f30d3`
- Objective: P-MP2 integration: connect the already-proven standalone read-only OpenCode Provider Adapter into Execution Hub without changing the Smart-v3 public 8-tool contract or routing thresholds. Add explicit adapter correlation IDs from child env through the existing OpenCode telemetry plugin and Electron strict gateway; correlate telemetry to the adapter delegation even if telemetry races CLI stdout. Make canonical UsageEvent recording idempotent so late measured terminal telemetry attaches exactly once after adapter lifecycle terminalization. Instantiate/cancel the adapter with Runtime lifecycle and block workspace switches while an adapter dispatch is active. Add supervisor-only internal /__control/hub provider_dispatch/provider_observe/provider_cancel actions bound fail-closed to the current task-projected active wave for dispatch, while observation/cancellation can truthfully finish an existing dispatch. Persist only prompt hash/bytes, bounded counts/timing/error class and exact model/dispatch/session IDs; never raw prompt or provider result text. Keep OpenCode worker-only, no controller transfer. Prove with fake provider and focused Node/Python tests only; no real provider/network inference, no UI, restart, settings, commit, push, release, or deploy.
- Mode: `mcp_only`
- Base HEAD: `bc820986e383391e36d243e0252e23b0aef8d5b8`
- Worktree fingerprint: `de82d0d5be5f7a326eb1c9a40a57b7e1fa3171ea5b770d05543a303614878817`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1800 | 2026-08-14T09:51:31.281Z | run_started |  | PREFLIGHT |  |
| 1801 | 2026-08-14T09:51:31.730Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 1802 | 2026-08-14T09:51:31.900Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1803 | 2026-08-14T09:51:32.067Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1804 | 2026-08-14T09:51:32.225Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 1805 | 2026-08-14T09:51:32.373Z | state_transition | READY | ROUTED | reason=route_selected |
| 1806 | 2026-08-14T09:51:32.925Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=1ed1e504790d45f6ac6e4d97ebbe49ac |
| 1807 | 2026-08-14T09:51:33.091Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 1808 | 2026-08-14T09:51:34.490Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=1ed1e504790d45f6ac6e4d97ebbe49ac |
| 1809 | 2026-08-14T09:51:34.658Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 1810 | 2026-08-14T09:51:35.867Z | proof_recorded |  |  | stage_id=check:ff4bcf92fdd7357c; status=passed; cache_hit=False; input_fingerprint=115d8ad487939947c7f170d1d2f4f4dc597c1c05ae333d304f84d14250fff25c |
| 1811 | 2026-08-14T09:51:36.917Z | proof_recorded |  |  | stage_id=check:094df351d1da782a; status=passed; cache_hit=False; input_fingerprint=de1d89ca417d72dbc8437b1c9d44c9255c8c096a85ceafb722c05d2b989fc83a |
| 1812 | 2026-08-14T09:51:41.209Z | proof_recorded |  |  | stage_id=check:5dc2b817cec38207; status=passed; cache_hit=False; input_fingerprint=2fb4c6840960b1d9eb68e8e209b8171b3cd5b5f44874a07d9da6c023fb890467 |
| 1813 | 2026-08-14T09:51:42.219Z | proof_recorded |  |  | stage_id=check:d2c1648d3ba83b43; status=passed; cache_hit=False; input_fingerprint=e31733262ab93a3fce137ccfd54ff4d06f596cec9664113aca2799e249291b66 |
| 1814 | 2026-08-14T09:51:44.042Z | proof_recorded |  |  | stage_id=check:94a8a740323528c0; status=passed; cache_hit=False; input_fingerprint=07c83ba63cc7ed0067bcd823d8979069e1791db966eb5aa8a6c1d4cda5046b83 |
| 1815 | 2026-08-14T09:51:50.741Z | proof_recorded |  |  | stage_id=check:d68f99d3d141b6d7; status=failed; cache_hit=False; input_fingerprint=e4e4dc9391c7e8229f6227941bbc1f5e6fddc88d135e06a4ee13738af5502a44 |
| 1816 | 2026-08-14T09:51:50.899Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 1817 | 2026-08-14T09:51:51.080Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:ff4bcf92fdd7357c | passed | 115d8ad487939947c7f170d1d2f4f4dc597c1c05ae333d304f84d14250fff25c | False | 318 | 0 |
| check:094df351d1da782a | passed | de1d89ca417d72dbc8437b1c9d44c9255c8c096a85ceafb722c05d2b989fc83a | False | 722 | 0 |
| check:5dc2b817cec38207 | passed | 2fb4c6840960b1d9eb68e8e209b8171b3cd5b5f44874a07d9da6c023fb890467 | False | 3889 | 0 |
| check:d2c1648d3ba83b43 | passed | e31733262ab93a3fce137ccfd54ff4d06f596cec9664113aca2799e249291b66 | False | 605 | 0 |
| check:94a8a740323528c0 | passed | 07c83ba63cc7ed0067bcd823d8979069e1791db966eb5aa8a6c1d4cda5046b83 | False | 1448 | 0 |
| check:d68f99d3d141b6d7 | failed | e4e4dc9391c7e8229f6227941bbc1f5e6fddc88d135e06a4ee13738af5502a44 | False | 6230 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `45`
- Chain head: `f2a7663ec986ae9ae472f9f1aec99fa641cc5bad4a6a51a39af7bc4a33f6990f`
