# Orchestration Run Summary

- Run: `cb0a385d21464d02a9cb557a46433dea`
- Task: `c6b58f63d9b14d7795e1c7e257e7a9e7`
- Objective: Resume and finish the isolated compute-first/server-first measurement hardening on branch automation/compute-placement-evaluation-20260817 without touching main/Recovery/installer/external Windows state. Preserve the existing uncommitted Python evaluation-plane WIP in this worktree and treat it as candidate code to validate, not as accepted proof. Complete the smallest coherent implementation that makes local_only versus server_preferred compute placement causally measurable: first ensure tests import the worktree-local coding_tools_mcp package; keep delayed controller observation and actual placement ledger evidence fail-closed and content-free; wire a real study-only compute placement policy into WebCodex read-only Cargo validation with production default server_preferred unchanged; expose actual policy/placement/fallback evidence in validation results without leaking runner/project secrets; correct stale shadow-only semantics if live dispatch proves that field is false; add focused Rust/Python/schema tests; do not change model routing authority and keep automatic activation false. Do not commit, push, tag, release, restart runtime, edit .coding-tools evidence, or touch resources/recovery-supervisor, recovery tests, installer/package files, tmp/P0.2 files, or external system state.
- Status: **accepted**
- Started: `2026-08-17T09:04:42.362Z`
- Finished: `2026-08-17T09:06:05.664Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `2e924c1099fa4197b1497daa97fb9f1a` | `mcp_only` | `acaa3582052ab6836ade7b55bd1ff2178ebc5117` | replanned |
| 2 | `f9e3b31a99c64d098aa2741ff2a158b0` | `mcp_only` | `acaa3582052ab6836ade7b55bd1ff2178ebc5117` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 71c449326e804ff180ba8149cf199876 | f9e3b31a99c64d098aa2741ff2a158b0 | accepted | acaa3582052ab6836ade7b55bd1ff2178ebc5117 | 8291752ffbf0d7171e48c9643234498a8050a86ff73492d6e082a5fdb4029f86 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 13049 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 13042 | `BASE_DRIFT` | `PREFLIGHT` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `28`
- Chain head: `9d3828639581c6a2fc03c00744dae04cb63a1688f4e1b7cd3f7a2ff7883679dc`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
