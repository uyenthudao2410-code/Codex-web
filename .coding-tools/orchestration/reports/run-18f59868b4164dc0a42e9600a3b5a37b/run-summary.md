# Orchestration Run Summary

- Run: `18f59868b4164dc0a42e9600a3b5a37b`
- Task: `768cbe946fe04d4fa0cf74a028fd2a84`
- Objective: P1.2 only: define the controlled eligible-run denominator for host-binding coverage from the existing evaluation/host-correlation contract before calculating the metric. The denominator must be rule-based and evidence-calibrated, not chosen to maximize coverage. Determine which run metadata fields prove that a run was eligible for ChatWeb host observation/correlation (for example explicit trace_id/turn_id and any activation/provenance constraints), how legacy pre-activation runs are excluded, and how to compute eligible_runs_total, eligible_runs_with_host_span, eligible_run_host_coverage plus existing span-level binding without timestamp proximity. Identify the smallest implementation/test/report change needed. Do not mutate in prepare; do not solve P1.3 controller usage or P1.4 quality population here.
- Status: **accepted**
- Started: `2026-08-17T15:04:46.605Z`
- Finished: `2026-08-17T15:13:23.845Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **1**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `87f0749155104aab8c3e609ea481a27b` | `mcp_only` | `db4e295cdd2cf71c0a4d0b91f1e5dcb5f9e6e4dc` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 919f3da563434786847f76524beaca9f | 87f0749155104aab8c3e609ea481a27b | accepted | db4e295cdd2cf71c0a4d0b91f1e5dcb5f9e6e4dc | 1827c47b87a439a3ac5ad1282add2e8e141100561c253f7f1437e3c74c1593c6 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 14386 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `54`
- Chain head: `5dbab40bb1573d22a15c4ff53eb931f674c6a2a229ddc46916631e734a989e57`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
