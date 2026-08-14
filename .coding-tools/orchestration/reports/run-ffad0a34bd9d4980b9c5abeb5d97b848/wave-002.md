# Orchestration Wave 2

- Run: `ffad0a34bd9d4980b9c5abeb5d97b848`
- Wave: `cea24c2e14084dbcaaa66c09dc5cbdaa`
- Objective: P-MP2 integration: connect the already-proven standalone read-only OpenCode Provider Adapter into Execution Hub without changing the Smart-v3 public 8-tool contract or routing thresholds. Add explicit adapter correlation IDs from child env through the existing OpenCode telemetry plugin and Electron strict gateway; correlate telemetry to the adapter delegation even if telemetry races CLI stdout. Make canonical UsageEvent recording idempotent so late measured terminal telemetry attaches exactly once after adapter lifecycle terminalization. Instantiate/cancel the adapter with Runtime lifecycle and block workspace switches while an adapter dispatch is active. Add supervisor-only internal /__control/hub provider_dispatch/provider_observe/provider_cancel actions bound fail-closed to the current task-projected active wave for dispatch, while observation/cancellation can truthfully finish an existing dispatch. Persist only prompt hash/bytes, bounded counts/timing/error class and exact model/dispatch/session IDs; never raw prompt or provider result text. Keep OpenCode worker-only, no controller transfer. Prove with fake provider and focused Node/Python tests only; no real provider/network inference, no UI, restart, settings, commit, push, release, or deploy.
- Mode: `mcp_only`
- Base HEAD: `bc820986e383391e36d243e0252e23b0aef8d5b8`
- Worktree fingerprint: `633f4d6a4a6f87d68d90abed54f365eaecdaa63ac0cb714f25a31c1979f5adc2`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 1818 | 2026-08-14T09:52:57.083Z | wave_replanned |  | PREFLIGHT | reason=The prior integration wave applied cleanly and all Node/plugin/compile/adapter checks passed, but test_execution_hub exposed TypeError in pre-existing external-delegation metadata merge when the new safe timing field is a dict (`value not in {None, ''}`). Materially fix the actual merge primitive with a non-hash predicate and finish lifecycle truthfulness via terminal callback rather than retrying the failed test unchanged. |
| 1819 | 2026-08-14T09:52:57.256Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 1820 | 2026-08-14T09:52:57.425Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 1821 | 2026-08-14T09:52:57.625Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 1822 | 2026-08-14T09:52:57.800Z | state_transition | READY | ROUTED | reason=route_selected |
| 1823 | 2026-08-14T09:52:58.384Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=d392e38124c84a6c96db50d1260c8b91 |
| 1824 | 2026-08-14T09:52:58.559Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 1825 | 2026-08-14T09:52:59.086Z | failure_observed | EXECUTING | EXECUTING | failure_class=PATCH_AMBIGUOUS |
| 1826 | 2026-08-14T09:52:59.351Z | write_lease_revoked | EXECUTING | EXECUTING | reason=state_transition:replan; owner=MCP; lease_id=d392e38124c84a6c96db50d1260c8b91 |
| 1827 | 2026-08-14T09:52:59.526Z | state_transition | EXECUTING | REPLAN | reason=PATCH_AMBIGUOUS; failure_class=PATCH_AMBIGUOUS |

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
- Events checked: `45`
- Chain head: `f2a7663ec986ae9ae472f9f1aec99fa641cc5bad4a6a51a39af7bc4a33f6990f`
