# Orchestration Wave 1

- Run: `21ebc20b13434504a94294200ad0da9a`
- Wave: `caecfe68727b412cbf8c5da2565da76a`
- Objective: G2 controlled proof-only production-surface ownership proof. From current bytes only: (1) prove every Electron production path that loads/opens renderer/token-dashboard.html; (2) classify renderer/token-dashboard.html under current electron_ui/componentRevision ownership as INCLUDED, EXCLUDED, or AMBIGUOUS; (3) prove source identity unchanged; (4) prove superseded ownership RUNs remain inactive and no write lease owns this surface. Read-only evidence only: no commands/tests, no source/asset/font/todo/ledger/projection edits, no restart/ACK/checkpoint/acceptance/delivery.
- Objective revision: `1`
- Objective SHA-256: `e2b5a202c3af93489b9034e73b919c01bdf1034fa6a71190b67d37d089ce7ab8`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `8697ace8204e7e3da55d250d4a52d9b2b930116c`
- Worktree fingerprint: `e8d01624191f2e2a09b336df8f3f992794a49d81e37d85895f6127dc9c3ca98a`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 40243 | 2026-09-04T20:41:17.062Z | run_started |  | PREFLIGHT |  |
| 40244 | 2026-09-04T20:41:17.470Z | observation_span_recorded |  |  |  |
| 40245 | 2026-09-04T20:41:18.095Z | observation_span_recorded |  |  |  |
| 40246 | 2026-09-04T20:41:18.311Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 40247 | 2026-09-04T20:41:42.336Z | state_transition | PREFLIGHT | ABORTED | reason=read_only_proof_complete_no_source_acceptance; hard-stop because renderer/dashboard.js materialization was truncated (2000/2076 lines), so exact-five evidence packet is not qualified. No source acceptance, checkpoint, proof reuse, command/test, restart, ACK, or delivery. |
| 40248 | 2026-09-04T20:41:42.792Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

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
- Events checked: `6`
- Chain head: `781201ededb2813609ade0af0e41f9b7376cf344a6595d2d0cae5eb24e736ef3`
