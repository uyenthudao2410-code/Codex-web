# Orchestration Run Summary

- Run: `03e4ff4dad8b4cc38d77ee7a10da6d09`
- Task: `4316c90695384d4e91f3e4fbf270134d`
- Objective: Strict-timing mini-canary retry for Problem prl-terminal-projection-clear-restart-drift-20260912 revision 2. Create one normal read-only RUN, obtain final acceptance, ACK its accepted report, clear the request-scoped projection, then immediately use the already-live observer RUN 8aa174e6591a4bec975916556dc0e508 / WAVE 7a38a7e9628a49f59a4a612773be8284 to run the full immutable lifecycle census. This retry exists because the previous attempt's first observer call used stale owner IDs and lost the <60-second acceptance window. Measure from final_acceptance_recorded to observer census observed_at; require <60 seconds. No source mutation, restart, ledger-history rewrite, commit, push, clean, reset, package, release, or deploy.
- Status: **accepted**
- Started: `2026-09-12T10:42:37.623Z`
- Finished: `2026-09-12T10:43:46.107Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **1**
- Proof cache hits: **1**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `f51e17c461c64322b5a25655418c01be` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 115379d8018849279c7ee3688a567e22 | f51e17c461c64322b5a25655418c01be | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | 5d11b5d1033eb13377d050e45fb8bc7ad6bae3fd7d4239d46f474b306f187cec | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 51618 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `26`
- Chain head: `f0a83830f41d62f4448dd9887a4063fafaeb10a98d0890eced62a5bfc63f1f1e`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
