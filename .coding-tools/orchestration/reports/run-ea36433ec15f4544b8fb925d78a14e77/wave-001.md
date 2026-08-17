# Orchestration Wave 1

- Run: `ea36433ec15f4544b8fb925d78a14e77`
- Wave: `f7e417aceda547f2b72229595326ee50`
- Objective: Implement and close P1.3 Controller Usage Coverage only. Starting from the accepted P1.2 state, inspect the current evaluation/run creation/reporting path and determine the smallest coherent implementation needed so eligible experimental runs can record controller.started_at plus token usage and monetary_cost only when actually observable, preserving unknown rather than converting missing values to zero. The canonical report must expose eligible experimental runs, coverage with started_at, token usage coverage, monetary-cost coverage, provenance/source, and must not enable promotion economics when materially incomplete. Prefer existing agent_workflow evaluation.controller fields and ledger schema if already present; do not add public MCP tools or a second analytics store unless strictly necessary. Add focused regression tests and update the authoritative P1.3 documentation/closure after proof. Do not implement P1.4 quality-outcome population, do not change routing policy, do not restart runtime unless user explicitly requested it.
- Mode: `mcp_only`
- Base HEAD: `db4e295cdd2cf71c0a4d0b91f1e5dcb5f9e6e4dc`
- Worktree fingerprint: `b4557a1b5fa4280fbf3c1c7f9a6ba92c485b37a76bad91cfb4333b152db50991`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 14475 | 2026-08-17T16:21:05.726Z | run_started |  | PREFLIGHT |  |
| 14476 | 2026-08-17T16:21:11.148Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 14477 | 2026-08-17T16:21:41.197Z | managed_process_admitted |  |  | owner=default |
| 14478 | 2026-08-17T16:21:41.436Z | managed_process_started |  |  | owner=default |
| 14479 | 2026-08-17T16:21:41.820Z | managed_process_terminal |  |  | owner=default |
| 14480 | 2026-08-17T16:21:50.938Z | managed_process_admitted |  |  | owner=default |
| 14481 | 2026-08-17T16:21:51.164Z | managed_process_started |  |  | owner=default |
| 14482 | 2026-08-17T16:21:51.535Z | managed_process_terminal |  |  | owner=default |
| 14483 | 2026-08-17T16:21:57.076Z | managed_process_admitted |  |  | owner=default |
| 14484 | 2026-08-17T16:21:57.451Z | managed_process_started |  |  | owner=default |
| 14485 | 2026-08-17T16:21:57.894Z | managed_process_terminal |  |  | owner=default |
| 14486 | 2026-08-17T16:22:30.294Z | managed_process_admitted |  |  | owner=default |
| 14487 | 2026-08-17T16:22:30.513Z | managed_process_started |  |  | owner=default |
| 14488 | 2026-08-17T16:22:30.898Z | managed_process_terminal |  |  | owner=default |
| 14489 | 2026-08-17T16:22:38.310Z | managed_process_admitted |  |  | owner=default |
| 14490 | 2026-08-17T16:22:38.529Z | managed_process_started |  |  | owner=default |
| 14491 | 2026-08-17T16:22:38.927Z | managed_process_terminal |  |  | owner=default |

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
- Events checked: `17`
- Chain head: `2bd086cc9e9eb4ae8e47d91c6d9ae7e2fe4bc92bc9ea740920ed1745a662c1f5`
