# Orchestration Run Summary

- Run: `97a1a8c55658484aa0263a0445bf3405`
- Task: `852f7d9f01024244a013d7b416e94eda`
- Objective: Stabilize the Recovery Host -> currentMcpHealth() -> /__control/health boundary without touching foreign stale runs or production runtime. Preserve readMcpHealth compatibility, classify deterministic auth/workspace/device/protocol mismatches separately from timeout/transport/not-ready failures, expose the classification through recoveryStatus/lightweight snapshots, and ensure deterministic mismatches fail closed without destructive restart escalation while timeout/hung failures retain the existing bounded restart escalation.
- Status: **accepted**
- Started: `2026-08-26T09:24:22.676Z`
- Finished: `2026-08-26T09:41:27.446Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `788e8c4868d049d8b6af23528a608f59` | 1 | `run_initial_objective` | `mcp_only` | `52faa0e9cfacf582fcf5bc6f40ed230cea7602e9` | replanned |
| 2 | `5e7fc178776148e88a010596b6f7df25` | 2 | `replan_request` | `mcp_only` | `52faa0e9cfacf582fcf5bc6f40ed230cea7602e9` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 17d2f22a6bec4270baaa02b40abe7540 | 5e7fc178776148e88a010596b6f7df25 | accepted | 52faa0e9cfacf582fcf5bc6f40ed230cea7602e9 | 6de4337be26b6ba60809d0e8a7ba317a5230c1b9a0418ce5e2189642ca35dec4 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 30564 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 30586 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 30579 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `55`
- Chain head: `98fb19a3b597a84dc18e1baf987a0f44af78d9ab23642a7d32213f59f93025fd`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
