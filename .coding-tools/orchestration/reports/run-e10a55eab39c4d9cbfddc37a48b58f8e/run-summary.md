# Orchestration Run Summary

- Run: `e10a55eab39c4d9cbfddc37a48b58f8e`
- Task: `868965d201ab46edad2cf055649cc2f9`
- Objective: W3 Provider UsageEvent Hardening: adopt the exact pre-existing W3 source bytes only; prove pricing_revision provenance, attribution status exact/partial/unassigned, provider-reported cost precedence, and exact fixture-to-ledger-to-analytics round trip. Do not alter any file bytes. Preserve unrelated dirty state. No commit/push/release/deploy.
- Status: **accepted**
- Started: `2026-08-31T19:32:47.264Z`
- Finished: `2026-09-01T00:39:34.781Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `c40ff646a8004a5fbf2382a12603cf28` | 1 | `run_initial_objective` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 2 | `afe720d9cfdc41aaaf2bbc2155182bc5` | 2 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 6bd72d7f283644f0a9783255ffb02740 | afe720d9cfdc41aaaf2bbc2155182bc5 | accepted | 30b7d1b971b65034d3e4c95568c970fcc0e9380c | e94c704c28ade64438de3198d8c3dd6220820a32090c4d8b3136a82eeb4dd4d0 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 33709 | `deterministic` | `deterministic` | explicit_request |
| 33840 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 33833 | `SOL_REJECTED` | `ACCEPTING` | PROVENANCE_ATTRIBUTION_FAIL_OPEN — build_usage_event accepts attribution_status=exact while run_id, wave_id and delegation_id are all empty; completion report does not prove the required mismatch cases. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `54`
- Chain head: `100cc2034f3311290fffb3b73256b3f48c639a826531baa7c376f74a97898ca2`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
