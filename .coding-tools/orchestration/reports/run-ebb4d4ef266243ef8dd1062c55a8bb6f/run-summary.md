# Orchestration Run Summary

- Run: `ebb4d4ef266243ef8dd1062c55a8bb6f`
- Task: `52ea5ae5be9342408b5f37c796298974`
- Objective: Close W5 as an evidence-only unsupported-capability result because current source already implements the required fail-closed behavior. Prove that the live control projection keeps exact tool-card tokens unobserved/null with reason client_receipt_not_exposed_by_mcp_transport and unknown_not_zero, that the Control Center renders client receipt unavailable without byte-derived inference, and that the public MCP inventory remains exactly 8 tools. Do not mutate source.
- Status: **accepted**
- Started: `2026-09-01T10:07:44.471Z`
- Finished: `2026-09-01T10:33:45.130Z`

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
| 1 | `ff186561767a4a62842fbebf524a627c` | 1 | `run_initial_objective` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 2 | `fe8cdd3f5f504daeabd0b4690542f7b9` | 2 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| df5a78635aa64675a523557d4c2f9d1d | fe8cdd3f5f504daeabd0b4690542f7b9 | accepted | 30b7d1b971b65034d3e4c95568c970fcc0e9380c | 87243bf33ca9d29556ed8f45e0d6d647f1d38bfb35e2506b153105fd36500605 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 34483 | `deterministic` | `deterministic` | explicit_request |
| 34500 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 34493 | `PERMISSION_REQUIRED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `40`
- Chain head: `f234628ad42dd279558eddcdd11b64a7a12839bdf76db6d14a90e62341ba3140`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
