# Orchestration Run Summary

- Run: `a4435fa80470436db09bbd18beb34d1b`
- Task: `1750d6e3e42c49f6941625eaad9354e5`
- Objective: Harden runtime activation without touching unrelated stale Execution Hub lineages. Preserve explicit stale-run reconciliation semantics for operator calls, but make Runtime startup/workspace-switch reconciliation repair only terminal-parent lifecycle contradictions and leave stale active runs as read-only health candidates. Add loaded behavior bytecode fingerprints to workspace_context detail=full for provider attribution, patch preflight, verification workdir, stale reconciliation, routing policy, and external-review policy. Add a model-free organic ChatWeb+MCP rework summary and CLI that excludes benchmark/synthetic and explicit model-routed accepted runs, reports first-pass/repaired/replan counts, preflight-avoided failures, and TTA percentiles/multipliers. Update focused regressions. Do not call providers/reviewers, do not restart in this wave, and preserve all unrelated dirty files.
- Status: **accepted**
- Started: `2026-08-15T05:48:20.229Z`
- Finished: `2026-08-15T05:51:25.278Z`

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
| 1 | `a5cf93f4f495410f86fb07dcbb00a686` | `mcp_only` | `dff81e251836666fc825c40bf86e4167afd29c39` | replanned |
| 2 | `daf6a17e12ce470fa061ec82e3380b79` | `mcp_only` | `dff81e251836666fc825c40bf86e4167afd29c39` | replanned |
| 3 | `8f53d90637c1458aace5d0699f42c7c5` | `mcp_only` | `dff81e251836666fc825c40bf86e4167afd29c39` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| d6d5c6d8c4fd49f0b53dca8170445f43 | 8f53d90637c1458aace5d0699f42c7c5 | accepted | dff81e251836666fc825c40bf86e4167afd29c39 | 235c1eec3b4adceaae0c53a052e72e23c37b634cf5930d2722c829a9f12f0d21 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 4485 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 4498 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 4510 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 4493 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |
| 4505 | `INVALID_ARGUMENT` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `38`
- Chain head: `3a0435b03b4936a5154746b486690c380d1221844b2d4ae105645798e55d5866`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
