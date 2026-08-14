# Orchestration Run Summary

- Run: `c3fa1e594e35457680426e04f13a69c7`
- Task: `1be0c78ed43b4aa0b8312f3c25f1e0c4`
- Objective: P3: complete measurable LSP-first localization economics. Extend PerformanceTrace v5 additively with bounded content-free localization counters (samples, total queries, semantic-available samples, semantic attempts, semantic hits, text-fallback queries), extract only live composite-read localization evidence in Runtime.emit_tool_trace, and expose rates in runtime_activation snapshot. Do not record raw query text, do not count cached composite replay twice, do not bump schema version, and preserve public Smart-v3 contract/EOCL authority. Add focused tests. No renderer changes, restart, paid provider call, commit, push, or deploy.
- Status: **accepted**
- Started: `2026-08-14T17:32:08.951Z`
- Finished: `2026-08-14T17:33:36.141Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `22b7271e719441568b8421888e622670` | `mcp_only` | `5decaa48300b10a6df39676c677745bc881cd7d9` | replanned |
| 2 | `28123df290c94c429c5a9027ef92bec9` | `mcp_only` | `5decaa48300b10a6df39676c677745bc881cd7d9` | replanned |
| 3 | `dac8b31f5a7c4e559c21f898c537d45e` | `mcp_only` | `5decaa48300b10a6df39676c677745bc881cd7d9` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 3e390c0878164003ae5b02453025a6a9 | dac8b31f5a7c4e559c21f898c537d45e | accepted | 5decaa48300b10a6df39676c677745bc881cd7d9 | 439eb6fba3ee22246a614d973fc468819a0df00eed1fdc05215e31c02c0bfbdb | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 3059 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 3069 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 3079 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 3063 | `PATCH_AMBIGUOUS` | `EXECUTING` |  |
| 3073 | `PATCH_CONTEXT_NOT_FOUND` | `EXECUTING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `33`
- Chain head: `0b39ab2f575cc7dcd79c516dd45be62e8202dbaad2d818511b225a5d608d54ad`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
