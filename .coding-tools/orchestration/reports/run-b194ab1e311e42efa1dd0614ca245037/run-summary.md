# Orchestration Run Summary

- Run: `b194ab1e311e42efa1dd0614ca245037`
- Task: `24b5dae59fd649e6978bc86960184154`
- Objective: Arm durable pre-reboot evidence for C01/M02 machine-A Restart sample 1 under Problem prl-22e670302757c9b7663170e226ed7c26 revision 1, using accepted packaged cold-start checkpoint 6fb3de41a26349f5995a6a2bd92d82f2. Record a privacy-safe receipt at .coding-tools/reboot-acceptance/c01-m02-machine-a-restart-1-pre.json with UTC capture time, Windows LastBootUpTime, exact packaged manifest/root/executable identities, installed executable and supervisor script SHA-256, live supervisor and packaged Recovery Host PID/instance, zero-failure status, Scheduled Task action/state plus boolean same-user principal match and trigger class names, and the expected post-reboot assertions. Do not store tokens, raw descriptor content, username/SID, credentials, or PII. Require exact executable SHA cf9235c1398d009762e9de5b25588e7fa85347a075ff6f18f2c4a5712558827c and supervisor script SHA 9f6cd06422484cb4911ea47c822dd6e4c5040dc6647ce283bb024b7b861a0dab; manifest/status must be packaged/healthy with live processes and zero failures. Verify the receipt parses and matches live state, then unregister only the completed one-shot canary task if its LastTaskResult is 0. Do not reboot yet, edit source, reinstall, commit, push, release, publish or deploy.
- Status: **accepted**
- Started: `2026-09-15T11:33:43.162Z`
- Finished: `2026-09-15T11:36:06.770Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `95f130cde253439fb7b40aeeca757ba9` | 1 | `run_initial_objective` | `mcp_only` | `cffd2acee24a4f38f4a83ddfea4c40f766de7a63` | replanned |
| 2 | `09a6713523104d3b8057cf36b23e6fdf` | 2 | `replan_request` | `mcp_only` | `cffd2acee24a4f38f4a83ddfea4c40f766de7a63` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| c8f32a66c7714204bcdd64162dc20ee1 | 09a6713523104d3b8057cf36b23e6fdf | accepted | cffd2acee24a4f38f4a83ddfea4c40f766de7a63 | 04d9f19cb0112e060c88cc025a61110cdc7fca49144492e14b49f231776cd28c | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 59766 | `deterministic` | `deterministic` | explicit_request |
| 59791 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 59780 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `60`
- Chain head: `ebaf7354400066ee3ea7815d2f1ccb51a16da0f36c69239a967c75fd4f1b6011`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
