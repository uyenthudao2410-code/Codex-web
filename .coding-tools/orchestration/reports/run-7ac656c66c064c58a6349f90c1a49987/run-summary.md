# Orchestration Run Summary

- Run: `7ac656c66c064c58a6349f90c1a49987`
- Task: `1080823908fb455e8d8801f702753b8f`
- Objective: Fix only case.py so normalize_score clamps values below 0 to 0, values above 100 to 100, and leaves values in [0,100] unchanged. Do not modify test_case.py. The deterministic acceptance oracle is `python test_case.py`. This is the Sol-xhigh paired benchmark fixture, not production source.
- Status: **active**
- Started: `2026-08-14T06:07:42.316Z`
- Finished: `None`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `8858c189ac194b84a82cd549fc499705` | `deep_single_lane` | `5f756b5f9a4ab29ca84401314bcc72efc17ae31b` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 1281 | `sol_xhigh` | `sol_xhigh` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 1287 | `CANDIDATE_MODEL_NOT_COMPLETED` | `ROUTED` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `13`
- Chain head: `3c408e5b2423297ba7dd46d3dfaa550fa1f76cb126820f55298d3e2a45d17802`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
