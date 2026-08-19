# Orchestration Wave 1

- Run: `a0d2ac478bcf4455be58e36271d80dbe`
- Wave: `a17c1b8d04eb4c94b7b2f44574d4430c`
- Objective: Implement token-accounting wave 2 only: make pricing consume canonical non-overlapping token categories without cache/reasoning double count; make durable ledger expose exact 7-day UsageEvent analytics across all runs (hourly UTC, by actor/provider/model, rolling 5 minutes, measured-vs-derived cost provenance) without any LIMIT=8/500 truncation; reject same usage_id with conflicting evidence; keep recent_usage_events(limit=8) as debug-only; exclude controller actor events from provider_economics; expose the 7-day analytics in the existing control orchestration snapshot. Add focused deterministic tests. Preserve accepted UsageEvent v2 semantics and all unrelated dirty source. No ChatWeb ingress/dashboard changes yet. No commit/push/restart.
- Mode: `mcp_only`
- Base HEAD: `930d3e1e67f2b413aa32d5da99d1a01d22d0bddc`
- Worktree fingerprint: `af51dd99ac8dcb2d7867a94c63e109eca4cd6fcf72168580485ad7d02c25751e`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 21044 | 2026-08-19T08:53:57.335Z | run_started |  | PREFLIGHT |  |
| 21045 | 2026-08-19T08:53:58.324Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 21046 | 2026-08-19T08:54:10.757Z | solution_shadow_recommended |  |  |  |
| 21047 | 2026-08-19T08:54:11.513Z | managed_process_admitted |  |  | owner=default |
| 21048 | 2026-08-19T08:54:11.777Z | managed_process_started |  |  | owner=default |
| 21049 | 2026-08-19T08:54:12.188Z | managed_process_terminal |  |  | owner=default |
| 21050 | 2026-08-19T08:54:33.544Z | state_transition | PREFLIGHT | ABORTED | reason=Pre-restart coordination stop before any write. This token-accounting wave 2 run was auto-opened by another controller/tab while the known stateless global projection bug is still active; this tab's unrelated module-guard command was incorrectly attributed into it, reproducing the live cross-tab leak. Preserve the token-accounting objective for replan after the accepted isolation source is runtime-activated. The run has no write lease and no modified files. |
| 21051 | 2026-08-19T08:54:33.891Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

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
- Events checked: `8`
- Chain head: `478bdfb0fd0f4c4c25454a3d904a2b38878329dcae4c779144a3dc3b190a2e84`
