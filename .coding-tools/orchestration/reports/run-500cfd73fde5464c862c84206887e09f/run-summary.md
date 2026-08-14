# Orchestration Run Summary

- Run: `500cfd73fde5464c862c84206887e09f`
- Task: `620a1cc3122846f89f3f46e653774c5c`
- Objective: Capture a fresh runtime-activation/cohort-v2 snapshot after the completed P1.5 activation and candidate-packet hardening. Run only the canonical benchmark command, do not modify source, do not change routing thresholds, and report accepted-route cohort coverage including whether any representative accepted Mini/Luna/Sol samples now exist.
- Status: **accepted**
- Started: `2026-08-14T04:14:19.867Z`
- Finished: `2026-08-14T04:14:51.817Z`

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
| 1 | `ea1720485d7d4ff99f66097361e37b96` | `mcp_only` | `5f756b5f9a4ab29ca84401314bcc72efc17ae31b` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 106a987d272549fb9383e60e60214026 | ea1720485d7d4ff99f66097361e37b96 | accepted | 5f756b5f9a4ab29ca84401314bcc72efc17ae31b | acbadc37d971a81c9ba2ae2f8e07fd863006b678f5ef56cf949cd9fdb81c5fd2 | ChatWeb Sol |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 874 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `14`
- Chain head: `dc1707d7bad6e8d414fddf609dcf67cb422f36353fafd973cdc196ce748146ce`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
