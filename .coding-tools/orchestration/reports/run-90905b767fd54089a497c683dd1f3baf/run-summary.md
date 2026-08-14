# Orchestration Run Summary

- Run: `90905b767fd54089a497c683dd1f3baf`
- Task: `0788aed490514131b2591f4d90606a3c`
- Objective: Zero-billing live OpenCode Flash canary preflight. Establish a bounded orchestration context only; no provider dispatch. In the execute phase, verify the checkpointed canary script syntax and run npm run canary:opencode-flash:preflight while the wave is in an eligible routed/executing/proving state. Preflight must validate live MCP workspace, Smart-v3, 8 tools, runtime instance and current run/wave, and report provider_dispatches=0. No source mutation, provider inference, settings/services/Git/release operations.
- Status: **active**
- Started: `2026-08-14T12:45:20.179Z`
- Finished: `None`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `baf9895bda2d497da67828113396afc0` | `mcp_only` | `bf072d9bd08a14768b729c1d209367bc771633a5` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 2017 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 2025 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `14`
- Chain head: `4d71906547767251c0babe5fcd71c05c2528af93dfcd95e3d58958ff8397c09f`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
