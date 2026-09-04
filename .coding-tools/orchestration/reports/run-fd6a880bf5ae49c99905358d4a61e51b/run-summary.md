# Orchestration Run Summary

- Run: `fd6a880bf5ae49c99905358d4a61e51b`
- Task: `769413e976774ded85357d935fbbb6d4`
- Objective: Inspect the single failing source-bundle invariant after the delivery full gate: tests/source-bundle.test.js reports 'private runtime state is not bundled from the source checkout' because resources/coding-tools-mcp/.coding-tools/orchestration/ledger.sqlite3 exists. Read only the exact test and relevant bundle source/filter implementation to determine the intended remediation. Do not mutate files, do not create additional generated state, do not commit or push.
- Status: **aborted**
- Started: `2026-09-04T01:37:16.765Z`
- Finished: `2026-09-04T01:38:47.301Z`

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
| 1 | `2d06285485f848b2b0bed56698ea1693` | 1 | `run_initial_objective` | `mcp_only` | `80aceb583202ad381c25687969fb48adbf74622c` | aborted |

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
- Events checked: `9`
- Chain head: `5f4c5fafe8ee3f40c0feef4d3fffbb8c10f11313953ac997a4821e5bb05ecc27`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
