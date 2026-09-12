# Orchestration Run Summary

- Run: `6a0264ba134f4f8790ce17a52b73df37`
- Task: `abdff8ddf43a4e7fb274859ca48a4e62`
- Objective: Natural #10: bind final acceptance to the exact proof-covered source bytes while tolerating unrelated dirty-path drift. Persist a bounded proof-source binding for the affected paths at proof time, validate it at final acceptance before checkpoint, reject proof-covered source drift with a typed error, and preserve existing explicit SHA/adoption/write-lease/PRL guards.
- Status: **accepted**
- Started: `2026-09-09T17:41:35.578Z`
- Finished: `2026-09-09T17:47:00.099Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **4**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `452a5b1cb742493a824566921bb7463a` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 220eb43e8ebc45e1abc2ee06460bc613 | 452a5b1cb742493a824566921bb7463a | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | 989743e36bdb832d5f14444b47906ae1f7ae6ebe32e7a8855a6a1c02e924edb8 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 46083 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `48`
- Chain head: `5485ff134586b08e93d9e8333f9ca3e8f78d16b7db5543b3c55dc26e0b91d96f`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
