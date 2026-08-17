# Orchestration Run Summary

- Run: `72616aa5d7a3409a83098d2243f48c48`
- Task: `c9f1e47271ab467abf8db5653c400703`
- Objective: Implement P0 Project Finance Overview KPI coverage in the HR repository only. Fix the pfm-management -> visual model/adapter -> ExecutiveFinancialCommandCenter flow so existing authoritative PFM totals are not dropped. Preserve and surface managementRevenue, retentionReceivable, releasedRetentionReceivable, cashConversionRate, collectibleCollectionRate, overdueReceivable, dueSoonReceivable, currentlyPayable, directProjectCost, allocatedCommonCost and existing exact totals where the UI model supports them. Derive only mathematically and semantically valid executive KPIs from exact totals: revenue/contract, collected/revenue, total receivable/revenue, total receivable/contract, project-attributed cost/contract, operating profit/revenue, and unrecognized contract value. Align pfm-management with finance-read presentation where semantics are identical, while preserving source provenance/coverage/fallback behavior. Do not invent values, do not derive ambiguous indirect cost, and do not modify Prisma/DB schema or ingestion. Add focused regression tests proving PFM values no longer fall back to 'Chưa có dữ liệu' when source fields exist, and that missing/zero denominators remain safe. Keep UI changes compact and consistent with the existing Tổng quan design.
- Status: **accepted**
- Started: `2026-08-17T17:38:25.718Z`
- Finished: `2026-08-17T18:05:07.654Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **2**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `d8e6598bcf784f88a90db98c0c2e0e78` | `mcp_only` | `8fbe07b19fe65d7b9cf46b53899f8c7d5116ec72` | replanned |
| 2 | `0e1318a909714635b2ede3983603230b` | `mcp_only` | `db4e295cdd2cf71c0a4d0b91f1e5dcb5f9e6e4dc` | replanned |
| 3 | `da847ca77d7a4d19bc4af6e1377b3e3d` | `mcp_only` | `db4e295cdd2cf71c0a4d0b91f1e5dcb5f9e6e4dc` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| d9b8b78cc7664979b9fff549a26a9a4e | da847ca77d7a4d19bc4af6e1377b3e3d | accepted | db4e295cdd2cf71c0a4d0b91f1e5dcb5f9e6e4dc | 4f405f745b6a2e0c5b942aecb560471ce4226d76beff71819993297bfb64d9a0 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 14995 | `deterministic` | `deterministic` | explicit_request |
| 15046 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 14955 | `BASE_DRIFT` | `PREFLIGHT` |  |
| 15006 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `353`
- Chain head: `c45cb4c5c1574d27ddf326ee8e08179e21b092600857f4900bc38479c110ec30`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
