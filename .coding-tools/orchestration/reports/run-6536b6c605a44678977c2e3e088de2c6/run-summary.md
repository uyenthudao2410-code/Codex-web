# Orchestration Run Summary

- Run: `6536b6c605a44678977c2e3e088de2c6`
- Task: `20d01ffb1ec2432a83fd2d2c8835fbfc`
- Objective: Adopt and prove the exact P0.6 immutable baseline candidate and complete 27-file current source packet without editing source; stop at ACCEPTING for ChatWeb final acceptance.
- Status: **accepted**
- Started: `2026-08-31T14:34:23.528Z`
- Finished: `2026-08-31T14:52:06.278Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `325e2ee61065441baa99c04b0e72845f` | 1 | `run_initial_objective` | `mcp_only` | `a357e1bb45a68cfaf25b8a2aa99a133ab256102c` | replanned |
| 2 | `5d7ce5685cf848028c6aaaa51403e4fe` | 2 | `replan_request` | `mcp_only` | `a357e1bb45a68cfaf25b8a2aa99a133ab256102c` | replanned |
| 3 | `88202f359cf24063a2f622c0136205c1` | 2 | `replan_request` | `mcp_only` | `a357e1bb45a68cfaf25b8a2aa99a133ab256102c` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| e3b6c1a07b3f4524af8d0bef967fc7d5 | 88202f359cf24063a2f622c0136205c1 | accepted | a357e1bb45a68cfaf25b8a2aa99a133ab256102c | 702139edffa332d62604af2b57e63c9ca65828207f92c589608f2c83df546fba | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 33423 | `deterministic` | `deterministic` | explicit_request |
| 33440 | `deterministic` | `deterministic` | explicit_request |
| 33466 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 33429 | `PROTECTED_PATH_WRITE` | `EXECUTING` |  |
| 33456 | `PERMISSION_REQUIRED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `75`
- Chain head: `07bf488dd2c638fd867456565aaa858df0de60f9867d53fbd07b3b7963bb4c5f`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
