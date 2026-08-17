# Orchestration Wave 2

- Run: `72616aa5d7a3409a83098d2243f48c48`
- Wave: `0e1318a909714635b2ede3983603230b`
- Objective: Implement P0 Project Finance Overview KPI coverage in the HR repository only. Fix the pfm-management -> visual model/adapter -> ExecutiveFinancialCommandCenter flow so existing authoritative PFM totals are not dropped. Preserve and surface managementRevenue, retentionReceivable, releasedRetentionReceivable, cashConversionRate, collectibleCollectionRate, overdueReceivable, dueSoonReceivable, currentlyPayable, directProjectCost, allocatedCommonCost and existing exact totals where the UI model supports them. Derive only mathematically and semantically valid executive KPIs from exact totals: revenue/contract, collected/revenue, total receivable/revenue, total receivable/contract, project-attributed cost/contract, operating profit/revenue, and unrecognized contract value. Align pfm-management with finance-read presentation where semantics are identical, while preserving source provenance/coverage/fallback behavior. Do not invent values, do not derive ambiguous indirect cost, and do not modify Prisma/DB schema or ingestion. Add focused regression tests proving PFM values no longer fall back to 'Chưa có dữ liệu' when source fields exist, and that missing/zero denominators remain safe. Keep UI changes compact and consistent with the existing Tổng quan design.
- Mode: `mcp_only`
- Base HEAD: `db4e295cdd2cf71c0a4d0b91f1e5dcb5f9e6e4dc`
- Worktree fingerprint: `083b4fd5b3aa009c536d25cef57f40cb7a3e5ff3e0b49328be88e5fbcb3f64d8`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 14958 | 2026-08-17T17:38:51.971Z | wave_replanned |  | PREFLIGHT | reason=The initial read-only preflight became stale because the worktree/contract fingerprint changed after P1.5 checkpoint. Re-read the current source without mutation and establish the exact remaining P1 regret-reporting gap against the new fingerprint. |
| 14959 | 2026-08-17T17:39:36.694Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 14961 | 2026-08-17T17:39:55.316Z | managed_process_admitted |  |  | owner=default |
| 14962 | 2026-08-17T17:39:55.554Z | managed_process_started |  |  | owner=default |
| 14963 | 2026-08-17T17:39:55.962Z | managed_process_terminal |  |  | owner=default |
| 14964 | 2026-08-17T17:39:57.866Z | managed_process_admitted |  |  | owner=default |
| 14965 | 2026-08-17T17:39:58.115Z | managed_process_started |  |  | owner=default |
| 14966 | 2026-08-17T17:39:58.504Z | managed_process_terminal |  |  | owner=default |
| 14967 | 2026-08-17T17:40:06.878Z | managed_process_admitted |  |  | owner=default |
| 14968 | 2026-08-17T17:40:07.073Z | managed_process_started |  |  | owner=default |
| 14969 | 2026-08-17T17:40:07.737Z | managed_process_terminal |  |  | owner=default |
| 14970 | 2026-08-17T17:40:10.887Z | managed_process_admitted |  |  | owner=default |
| 14971 | 2026-08-17T17:40:11.123Z | managed_process_started |  |  | owner=default |
| 14972 | 2026-08-17T17:40:11.698Z | managed_process_terminal |  |  | owner=default |
| 14973 | 2026-08-17T17:40:19.845Z | managed_process_admitted |  |  | owner=default |
| 14974 | 2026-08-17T17:40:20.065Z | managed_process_started |  |  | owner=default |
| 14975 | 2026-08-17T17:40:20.486Z | managed_process_terminal |  |  | owner=default |
| 14976 | 2026-08-17T17:40:21.498Z | managed_process_admitted |  |  | owner=default |
| 14977 | 2026-08-17T17:40:21.765Z | managed_process_started |  |  | owner=default |
| 14978 | 2026-08-17T17:40:22.178Z | managed_process_terminal |  |  | owner=default |
| 14979 | 2026-08-17T17:40:33.285Z | managed_process_admitted |  |  | owner=default |
| 14980 | 2026-08-17T17:40:33.864Z | managed_process_started |  |  | owner=default |
| 14981 | 2026-08-17T17:40:34.412Z | managed_process_terminal |  |  | owner=default |
| 14982 | 2026-08-17T17:40:44.163Z | managed_process_admitted |  |  | owner=default |
| 14983 | 2026-08-17T17:40:44.996Z | managed_process_started |  |  | owner=default |
| 14984 | 2026-08-17T17:40:45.854Z | managed_process_terminal |  |  | owner=default |
| 14985 | 2026-08-17T17:43:04.065Z | managed_process_admitted |  |  | owner=default |
| 14986 | 2026-08-17T17:43:04.453Z | managed_process_started |  |  | owner=default |
| 14987 | 2026-08-17T17:43:05.158Z | managed_process_terminal |  |  | owner=default |
| 14988 | 2026-08-17T17:43:06.698Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 14989 | 2026-08-17T17:43:07.248Z | managed_process_admitted |  |  | owner=default |
| 14990 | 2026-08-17T17:43:07.998Z | managed_process_started |  |  | owner=default |
| 14991 | 2026-08-17T17:43:08.565Z | managed_process_terminal |  |  | owner=default |
| 14992 | 2026-08-17T17:43:08.760Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 14993 | 2026-08-17T17:43:08.975Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 14994 | 2026-08-17T17:43:09.253Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 14995 | 2026-08-17T17:43:09.545Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 14996 | 2026-08-17T17:43:09.759Z | state_transition | READY | ROUTED | reason=route_selected |
| 14997 | 2026-08-17T17:43:10.544Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=29f0f5122aa743ae9e484b0223c25246 |
| 14998 | 2026-08-17T17:43:10.742Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 14999 | 2026-08-17T17:43:11.691Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=29f0f5122aa743ae9e484b0223c25246 |
| 15000 | 2026-08-17T17:43:11.908Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 15001 | 2026-08-17T17:43:12.556Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=9d59c43139ad7bba9787dbef50af8d09d34c9977df533e5ba4ba4044bd5ac499 |
| 15002 | 2026-08-17T17:43:12.858Z | managed_process_admitted |  |  | owner=default |
| 15003 | 2026-08-17T17:43:13.261Z | managed_process_started |  |  | owner=default |
| 15004 | 2026-08-17T17:43:13.664Z | managed_process_terminal |  |  | owner=default |
| 15005 | 2026-08-17T17:43:13.916Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=9d59c43139ad7bba9787dbef50af8d09d34c9977df533e5ba4ba4044bd5ac499 |
| 15006 | 2026-08-17T17:43:14.019Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 15007 | 2026-08-17T17:43:14.133Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 15008 | 2026-08-17T17:43:14.298Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | 9d59c43139ad7bba9787dbef50af8d09d34c9977df533e5ba4ba4044bd5ac499 | False | 1092 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `353`
- Chain head: `c45cb4c5c1574d27ddf326ee8e08179e21b092600857f4900bc38479c110ec30`
