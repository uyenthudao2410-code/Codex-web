# Orchestration Run Summary

- Run: `521621b23fea4487a0509fff3f62ea7a`
- Task: `91aab7518e654664a2c30d2baa561128`
- Objective: Diagnose why the live Recovery Host inspectCodeActivation rejects with WORKSPACE_MISMATCH even though Recovery Host settings, runtime health, and Coding MCP workspace_context all report E:\DEV\Tools-Codex-web. Focus on the Coding MCP /__control/activation GET response workspace field versus /__control/health and JavaScript workspaceKey normalization. Do not mutate files. Identify exact root cause and smallest safe fix if code defect.
- Status: **accepted**
- Started: `2026-08-17T05:01:43.828Z`
- Finished: `2026-08-17T05:10:10.984Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **5**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `0c24e7b07dd64306a238a35893fad0b6` | `mcp_only` | `4e5a5165e063b1b1816ef438babb19ca38d379d4` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 24364f8a1737484e947a8a804a31f165 | 0c24e7b07dd64306a238a35893fad0b6 | accepted | 4e5a5165e063b1b1816ef438babb19ca38d379d4 | 43b4ed2638de078e535e93ef4e95b20810b914ad753d956309f57997ea202e17 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 11545 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `71`
- Chain head: `37f2cce6b0eb76f85fac3c172ec06f2c47fd886704c497ff8ef7d4e774ab27fd`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
