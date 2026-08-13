# Orchestration Run Summary

- Run: `7be656325e1d424b816a0bf5fa6098bc`
- Task: `880d94315bf74ed78ab52eef32aa5f50`
- Objective: Fix EOCL recovered-context cache coherence so a replacement wave that reaches ACCEPTING can be accepted in the same runtime process, and add a regression assertion for the exact REPLAN-to-new-wave-to-CHECKPOINTED path.
- Status: **active**
- Started: `2026-08-13T05:12:43.807Z`
- Finished: `None`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **1**
- Proof cache hits: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `2e0b3299f1514ed392df5375e9cee888` | `mcp_only` | `571d30fc7237379fdc124d1b988054813d98bb45` | active |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 5 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `12`
- Chain head: `65bb3b0ec62f35ac1366d2f1d257019014de97ae4767d7158bc36917c2f9a9f5`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
