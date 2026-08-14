# Orchestration Run Summary

- Run: `5852c6811ede46a6ba744f3db02cf143`
- Task: `f32399a0b85744069e1750d8291208c5`
- Objective: Fix the one full-suite regression caused by the accepted task-epoch idempotency contract. Update the old efficiency test so agent_workflow execute derives from durable TaskState task epoch + request hash: changing only wave within the same task must not change its key; completing the task and starting a new task epoch must change the key. Preserve task_control accept/reject run+wave+caller+fence assertions and add an explicit same-caller/fence different-wave accept key difference. No production source change.
- Status: **accepted**
- Started: `2026-08-14T18:18:34.957Z`
- Finished: `2026-08-14T18:18:51.958Z`

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
| 1 | `cceaba0cd2f8421a95038d86c286ea43` | `mcp_only` | `5decaa48300b10a6df39676c677745bc881cd7d9` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| ce3ddd96de65434baa88e7e854502dc0 | cceaba0cd2f8421a95038d86c286ea43 | accepted | 5decaa48300b10a6df39676c677745bc881cd7d9 | 91dc0d6108352981d1cad2cf1d195289e46554315b3a95ed4060f8a3335fb02f | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 3351 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `13`
- Chain head: `618202f20c2e29f0e5e38260e0b989045d35f876c194fc3e5391d586e85f5f10`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
