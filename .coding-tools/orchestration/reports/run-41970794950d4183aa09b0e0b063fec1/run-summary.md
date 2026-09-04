# Orchestration Run Summary

- Run: `41970794950d4183aa09b0e0b063fec1`
- Task: `2c3cd47b2cc64743bb1d1e7b2996f643`
- Objective: Post-activation live L3 token-observability canary only. Run exactly the read-only runtime oracle npm run dev:status on E:\DEV\Codex-web under the current attested ChatWeb transport. Do not mutate source, do not trust or accept caller-supplied evaluation turn_id/trace_id, do not commit/push/release/deploy. The purpose is to let the runtime derive authoritative content-free host correlation from the current attested ChatWeb transport trace and later verify exact controller usage if a valid receipt arrives.
- Status: **accepted**
- Started: `2026-09-03T16:47:36.626Z`
- Finished: `2026-09-03T16:48:19.658Z`

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
| 1 | `6efc6cda64044c829525eadc446c70e8` | 1 | `run_initial_objective` | `mcp_only` | `80aceb583202ad381c25687969fb48adbf74622c` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 2ee99c6523b746feb64bdcaa80993aeb | 6efc6cda64044c829525eadc446c70e8 | accepted | 80aceb583202ad381c25687969fb48adbf74622c | a7d1826acc455f285726cb2253e0ab573114ccb6daac4df75e66f94e891e54c0 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 38070 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `26`
- Chain head: `0b76c2e3aabec1a5213cbc2493b2e04db9d2f2f3e6dc6fe5b4575afb82715f3b`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
