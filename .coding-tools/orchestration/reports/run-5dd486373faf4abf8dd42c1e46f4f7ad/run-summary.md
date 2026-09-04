# Orchestration Run Summary

- Run: `5dd486373faf4abf8dd42c1e46f4f7ad`
- Task: `7211572add7b4d0c8db3a13c7047911d`
- Objective: G4 read-only semantic-then-text-fallback measurement only. Localize the three exact-text identifiers terminateExactProcessTree, captureSpawnedProcessIdentity, serviceSupervisorRestartRequest. No regex. Keep localization/materialization bounded to at most 5 files, at most 120000 total source bytes, and at most 10 matches per query. Do not mutate files, do not create or execute an EOCL RUN/WAVE, do not run proofs/tests/builds, do not create Problems/outcomes. Return observed semantic-localization attempt/handling/fallback engine and timing/read/materialization/truncation metadata when available; missing metrics remain unknown.
- Status: **aborted**
- Started: `2026-09-03T21:05:14.564Z`
- Finished: `2026-09-03T21:08:51.187Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **0**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `648bbf0262e74ca084f990d66e9f15f5` | 1 | `run_initial_objective` | `auto` | `80aceb583202ad381c25687969fb48adbf74622c` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `6`
- Chain head: `02778b1032fbcb5ee7715895c8c1c540605ca4fa92d98c464ebf275e919493ba`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
