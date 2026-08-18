# Orchestration Run Summary

- Run: `1792024eddad473ebad50e3bd3e5351d`
- Task: `16d8ce5eaea7429b8b2d29def3900b30`
- Objective: Verify the committed P1 ITT hardening at HEAD bc17700e before any P3 treatment. Do not modify source. Confirm the regression test for a nonaccepted SERVER_FIRST_DETERMINISTIC_V1 candidate that replanned remains in the intention-to-treat denominator and yields candidate_acceptance_rate=0, candidate_first_pass_rate=0, candidate_repair_rate=1. Then run the paired-policy CLI help/current no-pair comparison for LOCAL_FIRST_V1 vs SERVER_FIRST_DETERMINISTIC_V1 and confirm missing controller token/monetary cost remains unknown rather than zero. This is verification only, not representative enrollment.
- Status: **accepted**
- Started: `2026-08-17T23:27:03.122Z`
- Finished: `2026-08-17T23:29:20.734Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `e5e4281ebdbd4229b83b1e41916e3b57` | `mcp_only` | `bc17700e475ce74c96a9547117aade58823f0811` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| c6e180efd7b54427ab83e330a7f5942a | e5e4281ebdbd4229b83b1e41916e3b57 | accepted | bc17700e475ce74c96a9547117aade58823f0811 | 0b718bb9f58e1897308e1335d33ed8a0b7d22e76f96be233d22c673f6ac545e8 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 15900 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `32`
- Chain head: `c8e2d004be59b322a8575217778b20f20db9e90ef313adc5d5982e703570011e`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
