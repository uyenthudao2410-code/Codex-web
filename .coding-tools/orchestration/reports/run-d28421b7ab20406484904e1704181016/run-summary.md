# Orchestration Run Summary

- Run: `d28421b7ab20406484904e1704181016`
- Task: `894e03254b014849a254ce66173d4acc`
- Objective: ONE paid live OpenCode Flash canary, explicitly authorized by the user. Establish a fresh bounded orchestration run/wave only. In execute, run exactly one `npm run canary:opencode-flash` invocation while this exact wave is ROUTED/EXECUTING/PROVING. The canary itself must pass authenticated live preflight first, dispatch exactly once to fixed model opencode-go/deepseek-v4-flash with the fixed read-only package.json prompt and deterministic request_id, poll the same dispatch only, and require a correlated measured UsageEvent with exact model/tokens/provider cost/timing. No Pro. No second provider dispatch or paid retry under any failure condition. No source/settings/service/Git/release mutation.
- Status: **active**
- Started: `2026-08-14T12:49:21.176Z`
- Finished: `None`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `63e0c3ce85c54fe98b731b303ded7e4f` | `mcp_only` | `bf072d9bd08a14768b729c1d209367bc771633a5` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 2059 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 2075 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `22`
- Chain head: `df842f11e4d6d8c64cddcf75531ebbb83c85c11d8ed0bb337017de8f2c829d3d`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
