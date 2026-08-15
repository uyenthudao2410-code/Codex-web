# Orchestration Run Summary

- Run: `170c7aa1bdfe4da4827ea9101dadfda7`
- Task: `94ffc6f2bfbf431d8ff0b4f37aea72d4`
- Objective: P1C inspect the existing Windows build/package/install-smoke path and identify the smallest exact-source provenance insertion point. Required identity: exact Git SHA plus clean/source fingerprint, app version, Coding Tools MCP version/build identity, native artifact SHA-256 values, the actual npm/installer candidate SHA-256, and canonical proof identity. The smoke-tested candidate bytes must be the provenance-described bytes. Do not mutate in prepare and do not publish/release/tag/push.
- Status: **accepted**
- Started: `2026-08-15T02:29:40.071Z`
- Finished: `2026-08-15T02:35:03.215Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `4be5f54ef42344c3b4a0b5e23e34ccb8` | `mcp_only` | `dff81e251836666fc825c40bf86e4167afd29c39` | replanned |
| 2 | `ef2a385de5a8458797af720bf49bf2b3` | `mcp_only` | `dff81e251836666fc825c40bf86e4167afd29c39` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 207332b11a064acc9cbfe517d17a45f2 | ef2a385de5a8458797af720bf49bf2b3 | accepted | dff81e251836666fc825c40bf86e4167afd29c39 | 6db36ca46cb055b4cc116365fd1088d419b8267ac3c032b4d232db6dac396c20 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 3830 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 3843 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 3838 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `27`
- Chain head: `3e031afd248135cd62d49908953ac61389ac44f7f441bece70a4f7e20391781c`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
