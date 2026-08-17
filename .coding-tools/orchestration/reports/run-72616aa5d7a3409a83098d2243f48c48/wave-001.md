# Orchestration Wave 1

- Run: `72616aa5d7a3409a83098d2243f48c48`
- Wave: `d8e6598bcf784f88a90db98c0c2e0e78`
- Objective: Implement P0 Project Finance Overview KPI coverage in the HR repository only. Fix the pfm-management -> visual model/adapter -> ExecutiveFinancialCommandCenter flow so existing authoritative PFM totals are not dropped. Preserve and surface managementRevenue, retentionReceivable, releasedRetentionReceivable, cashConversionRate, collectibleCollectionRate, overdueReceivable, dueSoonReceivable, currentlyPayable, directProjectCost, allocatedCommonCost and existing exact totals where the UI model supports them. Derive only mathematically and semantically valid executive KPIs from exact totals: revenue/contract, collected/revenue, total receivable/revenue, total receivable/contract, project-attributed cost/contract, operating profit/revenue, and unrecognized contract value. Align pfm-management with finance-read presentation where semantics are identical, while preserving source provenance/coverage/fallback behavior. Do not invent values, do not derive ambiguous indirect cost, and do not modify Prisma/DB schema or ingestion. Add focused regression tests proving PFM values no longer fall back to 'Chưa có dữ liệu' when source fields exist, and that missing/zero denominators remain safe. Keep UI changes compact and consistent with the existing Tổng quan design.
- Mode: `mcp_only`
- Base HEAD: `8fbe07b19fe65d7b9cf46b53899f8c7d5116ec72`
- Worktree fingerprint: `8502abd49ee29c52808a3b7fb7d6c554cc819886d87491db65b3fcf27b9d1035`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 14954 | 2026-08-17T17:38:25.929Z | run_started |  | PREFLIGHT |  |
| 14955 | 2026-08-17T17:38:37.746Z | failure_observed | PREFLIGHT | PREFLIGHT | failure_class=BASE_DRIFT |
| 14956 | 2026-08-17T17:38:37.881Z | state_transition | PREFLIGHT | REPLAN | reason=BASE_DRIFT; failure_class=BASE_DRIFT |
| 14957 | 2026-08-17T17:38:38.040Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 14960 | 2026-08-17T17:39:42.856Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 15130 | 2026-08-17T17:52:40.315Z | observation_span_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| - | - | - | - | - | - |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `353`
- Chain head: `c45cb4c5c1574d27ddf326ee8e08179e21b092600857f4900bc38479c110ec30`
