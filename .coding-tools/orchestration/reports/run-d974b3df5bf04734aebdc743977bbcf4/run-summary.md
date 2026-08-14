# Orchestration Run Summary

- Run: `d974b3df5bf04734aebdc743977bbcf4`
- Task: `78c57c4197dd46e6993b3aa0f1102637`
- Objective: Fix only case.py so remaining_capacity(limit, used) returns the non-negative remaining capacity: limit-used when positive, otherwise 0. Do not modify test_case.py. Deterministic oracle: `python test_case.py`. Localized strong-oracle benchmark only.
- Status: **accepted**
- Started: `2026-08-14T06:15:01.473Z`
- Finished: `2026-08-14T06:16:21.264Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `1c69e890ea104637859c3781ef68ad9c` | `bounded_candidate` | `5f756b5f9a4ab29ca84401314bcc72efc17ae31b` | replanned |
| 2 | `08390e8c72954710bc125203cd7bca06` | `bounded_candidate` | `5f756b5f9a4ab29ca84401314bcc72efc17ae31b` | replanned |
| 3 | `4f75b43ae4ee4b3295527b7deec26672` | `mcp_only` | `5f756b5f9a4ab29ca84401314bcc72efc17ae31b` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| df1838623d0c4a8c8e2df2c2f58ae644 | 4f75b43ae4ee4b3295527b7deec26672 | accepted | 5f756b5f9a4ab29ca84401314bcc72efc17ae31b | ae565948a7cd0ea72eb709ac0852546b56c006cdabfe03d87e4859dda660b812 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 1307 | `mini` | `mini` | explicit_request |
| 1320 | `mini` | `mini` | explicit_request |
| 1336 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 1313 | `CANDIDATE_TARGET_MISSING` | `ROUTED` |  |
| 1331 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `43`
- Chain head: `374e9bd8bd7434cc08e34611d4632ce00084eb2bb0dc53d6c9bb0032fef0122c`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
