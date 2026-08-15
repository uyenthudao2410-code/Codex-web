# Orchestration Run Summary

- Run: `628450bec80c4b5f94876959b67568f9`
- Task: `a8b953b9e49c43d8881f1865d6e55cf7`
- Objective: Re-establish an auditable EOCL run for the already-applied P0 solution after the prior acceptance run disappeared from the task projection. Read only: verify the P0 source changes are still present, HEAD remains 8581b8331e83cc600c2b813629875639e48a8245, Smart-v3 remains exactly 8 tools with SHA 4283e098c315d015c457ce2ab781257491ef70607c6c577f7699969fb8c3f754, and unrelated AGENTS/renderer/runtime artifacts are preserved. Then prepare focused proof; do not mutate source in this phase.
- Status: **active**
- Started: `2026-08-15T00:07:47.793Z`
- Finished: `None`

## Outcome metrics

- Waves: **2**
- Route decisions: **1**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `f2c45d0ffecb4517b17b4397c4504bdc` | `mcp_only` | `c8633e717312a53083755a220f7845316c73478a` | replanned |
| 2 | `a5ceead78576487b91e243a8d484fffa` | `deep_single_lane` | `dff81e251836666fc825c40bf86e4167afd29c39` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 3663 | `auto` | `sol_xhigh` | deep_or_broad_context |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 3655 | `BASE_DRIFT` | `PREFLIGHT` |  |
| 3669 | `PROMPT_TOO_LARGE` | `ROUTED` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `18`
- Chain head: `a20111b6ae83b8af8ccb4b149b7819617af5333d9af11b646d2b2e942f0e86d7`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
