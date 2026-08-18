# Orchestration Run Summary

- Run: `2b994e7dbafc4b0980a7d4791009c160`
- Task: `dcd56f5bacb3492a99a5897286b753b7`
- Objective: Create and push a consistent point-in-time snapshot of all current deliverable repository changes to origin/main. Preserve all .coding-tools evidence except exactly ledger.sqlite3-shm and ledger.sqlite3-wal, keep ledger.sqlite3 tracked, use an alternate Git index to avoid concurrent real-index lock races, atomically synchronize the finished index into .git/index, then push and verify.
- Status: **aborted**
- Started: `2026-08-18T11:48:23.778Z`
- Finished: `2026-08-18T11:56:32.557Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **5**
- REPLAN transitions: **5**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `e71b08a2aef04936aa86980a93359c41` | `mcp_only` | `128afd79a1dfe2b607de4ec519a053a2ab050d0f` | replanned |
| 2 | `43f7154d42e14b38bd71f3642b1ece95` | `mcp_only` | `128afd79a1dfe2b607de4ec519a053a2ab050d0f` | replanned |
| 3 | `c5489f973a75465c91f909f358910b2b` | `mcp_only` | `128afd79a1dfe2b607de4ec519a053a2ab050d0f` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 17638 | `deterministic` | `deterministic` | explicit_request |
| 17671 | `deterministic` | `deterministic` | explicit_request |
| 17692 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 17647 | `RUNTIME_RESUME_REQUIRED` | `PROVING` | A non-terminal wave was recovered outside its original synchronous execution. |
| 17665 | `SOL_REJECTED` | `ACCEPTING` | Post-run verification contradicts the proof command's exit code 0: workspace HEAD is still 128afd79a1dfe2b607de4ec519a053a2ab050d0f, ahead/behind are 0, and the original source/.coding-tools changes remain staged/dirty. Command stdout contains only ALT_INDEX and lacks COMMITTED_HEAD/REAL_INDEX_SYNCED/PUSH markers. The PowerShell function likely terminated early because `return` was used inside ForEach-Object while enumerating excluded sidecars. Reject this wave and replan with explicit foreach/continue plus stage markers and independent post-run Git verification. |
| 17680 | `RUNTIME_RESUME_REQUIRED` | `PROVING` | A non-terminal wave was recovered outside its original synchronous execution. |
| 17686 | `SOL_REJECTED` | `ACCEPTING` | The explicit-foreach command again returned exit 0 but stdout contains only ALT_INDEX and stderr only git fetch output; none of the mandatory STAGE1_DONE/GUARD/COMMIT/PUSH/SCRIPT_DONE markers appeared. Therefore the long powershell -Command invocation is not reliable evidence of executing the full script. Reject and replan to execute the same logic from a temporary .ps1 file that self-deletes before staging, with explicit markers and independent workspace verification. |
| 17712 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `84`
- Chain head: `2eba10faff8fb98b47956c7fdcf3282439f6385814daa05e8b5d3a7d6e72d9ef`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
