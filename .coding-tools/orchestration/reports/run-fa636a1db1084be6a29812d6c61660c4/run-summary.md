# Orchestration Run Summary

- Run: `fa636a1db1084be6a29812d6c61660c4`
- Task: `491fa66cb1b2451d9e8bac6244080e2e`
- Objective: Implement the smallest H4 Codex exact-usage persistence closure on E:\DEV\Codex-web. Preserve the existing Codex App Server thread/tokenUsage/updated authority, but make it fail-closed: only complete non-negative integer inputTokens/cachedInputTokens/outputTokens/reasoningOutputTokens may be marked measured. Persist exact Codex candidate-model usage as a canonical provider UsageEvent bound to the current RUN/WAVE/delegation with provider_reported provenance and source codex_app_server:thread/tokenUsage/updated. Do not claim provider-measured monetary cost; cost may remain derived/unobserved. Missing or incomplete token usage must produce no UsageEvent, never zero. Do not change public 8-tool contract, routing authority, restart behavior, or unrelated dirty hunks. Add focused tests for exact X/Y/Z/R persistence and incomplete-token fail-closed behavior.
- Status: **accepted**
- Started: `2026-09-03T05:09:42.964Z`
- Finished: `2026-09-03T05:14:16.677Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `c8772c2c4dbf40a4a20d93070ad1fc09` | 1 | `run_initial_objective` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| f13cbf4f937944f38393b057c5dbeb98 | c8772c2c4dbf40a4a20d93070ad1fc09 | accepted | 30b7d1b971b65034d3e4c95568c970fcc0e9380c | 5fe77d3e8d06999f420c7d38a4d4675ec1bde06401cc0230d590d0c6121acd88 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 36306 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `33`
- Chain head: `3ad5faca539893c735915a3d6b75295bc4f42cb7f7a8ef4add8d3f3ef4525360`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
