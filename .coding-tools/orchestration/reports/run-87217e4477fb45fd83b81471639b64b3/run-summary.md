# Orchestration Run Summary

- Run: `87217e4477fb45fd83b81471639b64b3`
- Task: `1105b92745414195bb94a825c509a45a`
- Objective: Protect performance/cost measurement integrity. Prevent uncorrelated OpenCode provider telemetry from being attributed to a non-OpenCode active EOCL wave; preserve intentional uncorrelated telemetry only when the wave itself is explicitly routed to OpenCode. Separate measured provider cost coverage from causal task attribution so total accepted-result cost is incomplete when provider usage is not dispatch-correlated. Harden the OpenCode timeout fixture against broad-suite scheduler delay without weakening the expected timeout classification. Do not call any external model/provider or external review.
- Status: **active**
- Started: `2026-08-15T05:05:18.753Z`
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
| 1 | `189eb4e8f4cd4034a763cbc83c071372` | `mcp_only` | `dff81e251836666fc825c40bf86e4167afd29c39` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 4373 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 4383 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `15`
- Chain head: `869497f91fe3c739c885bdcb1b35f818b05d5b28869f84f9c7e3fe709e9a355d`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
