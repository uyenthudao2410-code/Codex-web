# Orchestration Run Summary

- Run: `3e373f0a22414388be48d9fdf61a2f28`
- Task: `235e6ef133824ce5ac30966e2b4501f9`
- Objective: Close H0/H1 for ChatWeb controller token measurement with content-free attested envelope evidence. Reuse the existing connector/runtime observation plane; do not add a public tool or infer tokens. Record only whether the exact io.coding-tools/controllerUsage key was present on attested ChatWeb tools/call envelopes, aggregate current-process present/absent counts, expose this in authenticated health and live ChatWeb measurement projection, and explicitly report that no supported post-turn controller-usage sideband exists yet. Preserve existing exact controller UsageEvent ingress and all unrelated dirty hunks. Add focused regressions proving absent envelopes remain unknown/not-zero, present envelopes are observed alongside existing exact usage ingestion, and live projection stays fail-closed.
- Status: **accepted**
- Started: `2026-09-03T04:57:56.274Z`
- Finished: `2026-09-03T05:03:39.583Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `59b907974c1f45ff8dc8d8ea0c5ff84f` | 1 | `run_initial_objective` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 2 | `cc059b9735c7419a9b80f77129510790` | 1 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 4c26c8e0db9448399d6acc0b0e0275e4 | cc059b9735c7419a9b80f77129510790 | accepted | 30b7d1b971b65034d3e4c95568c970fcc0e9380c | da47a9ea24138318d6bf2b7bbb200184a1be34795c2fe499e1db1698345df109 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 36203 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 36213 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 36206 | `RUNTIME_RESUME_REQUIRED` | `ROUTED` | A non-terminal wave was recovered outside its original synchronous execution. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `41`
- Chain head: `2753f63a47fcafff15213b8a3aa8b83fb318aa46355e7674dbb37363652ac235`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
