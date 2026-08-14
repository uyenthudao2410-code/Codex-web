# Orchestration Run Summary

- Run: `ffad0a34bd9d4980b9c5abeb5d97b848`
- Task: `ae013a80c9594eaaa180c5653c29098d`
- Objective: P-MP2 integration: connect the already-proven standalone read-only OpenCode Provider Adapter into Execution Hub without changing the Smart-v3 public 8-tool contract or routing thresholds. Add explicit adapter correlation IDs from child env through the existing OpenCode telemetry plugin and Electron strict gateway; correlate telemetry to the adapter delegation even if telemetry races CLI stdout. Make canonical UsageEvent recording idempotent so late measured terminal telemetry attaches exactly once after adapter lifecycle terminalization. Instantiate/cancel the adapter with Runtime lifecycle and block workspace switches while an adapter dispatch is active. Add supervisor-only internal /__control/hub provider_dispatch/provider_observe/provider_cancel actions bound fail-closed to the current task-projected active wave for dispatch, while observation/cancellation can truthfully finish an existing dispatch. Persist only prompt hash/bytes, bounded counts/timing/error class and exact model/dispatch/session IDs; never raw prompt or provider result text. Keep OpenCode worker-only, no controller transfer. Prove with fake provider and focused Node/Python tests only; no real provider/network inference, no UI, restart, settings, commit, push, release, or deploy.
- Status: **accepted**
- Started: `2026-08-14T09:51:30.984Z`
- Finished: `2026-08-14T09:56:15.947Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **12**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `3302df8699404fc3afd36ded809f30d3` | `mcp_only` | `bc820986e383391e36d243e0252e23b0aef8d5b8` | replanned |
| 2 | `cea24c2e14084dbcaaa66c09dc5cbdaa` | `mcp_only` | `bc820986e383391e36d243e0252e23b0aef8d5b8` | replanned |
| 3 | `d59f355338ca431a83622b410ba1c4db` | `mcp_only` | `bc820986e383391e36d243e0252e23b0aef8d5b8` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 0969e12236c84d05bcc1314d54116b70 | d59f355338ca431a83622b410ba1c4db | accepted | bc820986e383391e36d243e0252e23b0aef8d5b8 | d370286e94930f9b7437d04cde9424afcaeb1c898c979a9b1fecbb14b8dc7768 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 1804 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 1821 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 1831 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 1816 | `CHECK_FAILED` | `PROVING` |  |
| 1825 | `PATCH_AMBIGUOUS` | `EXECUTING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `45`
- Chain head: `f2a7663ec986ae9ae472f9f1aec99fa641cc5bad4a6a51a39af7bc4a33f6990f`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
