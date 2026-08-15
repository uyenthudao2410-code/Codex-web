# Orchestration Run Summary

- Run: `cabac3c58fdd4de1a0f43075c28d4c08`
- Task: `6d413540c1c9492f8d7e8587ce6691e6`
- Objective: Remove evaluation window bias without weakening normal history caps. paired_policy_evaluation must scan up to its declared bounded limit (max 500) directly from the durable ledger instead of calling list_runs(), whose UI/history safety cap is 100. Report scanned_runs explicitly and classify zero-pair Pareto state as indeterminate_no_pairs. Preserve all routing/cost-control behavior and do not call providers.
- Status: **accepted**
- Started: `2026-08-15T04:24:14.930Z`
- Finished: `2026-08-15T04:24:47.052Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `ddb2879ffb634b8e87fce2fd90aa556b` | `mcp_only` | `dff81e251836666fc825c40bf86e4167afd29c39` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 12bf39c95d4f429cad2117d461f51f51 | ddb2879ffb634b8e87fce2fd90aa556b | accepted | dff81e251836666fc825c40bf86e4167afd29c39 | 911f5b1b5031cef4ea05e2ec9f8b8138d3c52844a349eca96c9730ed3f175340 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 4182 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `13`
- Chain head: `777ab7d4087739346815b7f03cb0e1129d93b85fd44980c75f60b421778fe44d`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
