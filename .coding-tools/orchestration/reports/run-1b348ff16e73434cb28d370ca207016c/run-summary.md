# Orchestration Run Summary

- Run: `1b348ff16e73434cb28d370ca207016c`
- Task: `a886f01373ee4f50b5036773281bed47`
- Objective: Create a fresh activation-safe accepted checkpoint for the already-proved recovery hotfix without rewriting source bytes. The authoritative five runtime source files must be explicitly attested by exact current SHA-256 at final acceptance so the checkpoint metadata uses source=explicit_acceptance_attestations and receipt_kind=explicit_existing_file. Preserve all unrelated dirty work. Runtime source scope only: electron/services/activationEpoch.js; electron/services/fullCleanActivation.js; electron/services/recoveryHost.js; resources/coding-tools-mcp/coding_tools_mcp/activation_lifecycle.py; resources/coding-tools-mcp/coding_tools_mcp/http_hub_identity.py. Proof consumers may include tests/activation-self-recovery.test.js, tests/activation-epoch.test.js, tests/recovery-host.test.js, resources/coding-tools-mcp/tests/test_activation_restart_escape.py, and resources/coding-tools-mcp/tests/test_connector_bootstrap_identity.py. Do not patch or rewrite any file. Reach ACCEPTING only after focused proof demonstrates the attested bytes still satisfy activation expiry, connector-pending recovery, confirmed restart escape, connector identity fallback, syntax, and diff hygiene.
- Status: **aborted**
- Started: `2026-08-27T19:50:03.502Z`
- Finished: `2026-08-27T20:41:35.621Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **4**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `27859e21aeb64463b5420013f19afb5c` | 1 | `run_initial_objective` | `mcp_only` | `b64c43c7e092301dd9abdfad32d4dc1910192485` | replanned |
| 2 | `64ec818513ab4b0d803969cd16d5bde6` | 2 | `replan_request` | `mcp_only` | `b64c43c7e092301dd9abdfad32d4dc1910192485` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 31339 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 31382 | `SOL_REJECTED` | `ACCEPTING` | Final acceptance correctly failed because explicit_existing_file cannot claim pre-existing dirty source without a durable same-wave authority surface. The current runtime has no content-addressed/no-write adoption primitive: patch_surface_observed is emitted only after apply_patch and apply_patch necessarily stages/commits bytes. Replan to add a bounded existing-file adoption event bound to active write lease, exact path identity, and exact SHA-256, with no file write; preserve the anti-source-laundering invariant and add wrong-SHA/out-of-scope/drift regression coverage. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `65`
- Chain head: `c8ca0bce245fa374680fb7d63c1a48063d9c5d71608e2c31bb9155f17445b31a`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
