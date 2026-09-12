# Orchestration Run Summary

- Run: `2ebde6e68fcb4ab9b7114913a11c7cd3`
- Task: `3c063c967c114045a547b2ada19a3423`
- Objective: Durably adopt and prove the exact current production bytes that complete the Recovery Host deferred-restart race fix and the narrowly-scoped self-controller activation-preflight allowance for existing Problem prl-a5bf3e0510b110459e4cf57f5bcde24b revision 1. Do not rewrite source in this engineering attempt. Adopt only the four still-unaccepted dirty paths: electron/services/recoveryHost.js, tests/recovery-host.test.js, resources/coding-tools-mcp/coding_tools_mcp/activation_lifecycle.py, and resources/coding-tools-mcp/coding_tools_mcp/coordination.py. Re-prove both Recovery Host and activation-preflight focused oracles on the exact adopted bytes. Preserve unrelated dirty worktree content. This is an implementation/proof checkpoint only; do not claim full Problem resolution, do not reconcile stale RUNs yet, and do not commit/push/package/release/deploy.
- Status: **accepted**
- Started: `2026-09-12T02:27:02.684Z`
- Finished: `2026-09-12T02:58:52.762Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `9a82b7a4666a4a608132c2b7a3e31d66` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 368fd26fca4f46478accf730df1dee70 | 9a82b7a4666a4a608132c2b7a3e31d66 | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | 3d0d74827cdf5409f8692586d2a668c53c792fe862887c320317c010598951a2 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 50000 | `auto` | `deterministic` | roi_gate_hold_insufficient_paired_evidence |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `30`
- Chain head: `85f3f9c90cd9b3da754719d195c936094058273ed7f0c52dcc15b658a5b29edb`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
