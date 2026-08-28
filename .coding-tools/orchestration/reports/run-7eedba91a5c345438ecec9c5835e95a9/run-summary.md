# Orchestration Run Summary

- Run: `7eedba91a5c345438ecec9c5835e95a9`
- Task: `6eabbf3069ef48b695da9a7244b186c4`
- Objective: Diagnose why a task_control restart_runtime ticket was accepted with expected_disconnect=true but was not consumed before expires_at: ticket restart-Tk0y31JsQ9krhgaQ, accepted on live workspace E:\Github\Tools-Codex-web, old process_instance_id Eij1iUBrbn3u68n5 and server_instance_id OA4T9S_Np868eRD1 remained unchanged after expiry. Read only. Trace the exact enqueue persistence, supervisor polling/consumption, eligibility/fence checks, expiry handling, and any runtime log/state surfaces that distinguish ticket absent, expired, unconsumed, or consume failure. Do not mutate files, do not restart, do not reconcile acceptance state, and do not create broad cleanup.
- Status: **aborted**
- Started: `2026-08-27T19:30:36.840Z`
- Finished: `2026-08-27T19:41:40.415Z`

## Outcome metrics

- Waves: **1**
- Route decisions: **0**
- Failures observed: **0**
- REPLAN transitions: **0**
- Proof stages: **0**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `e686890be3a64600ba007fec19f9bdde` | 1 | `run_initial_objective` | `mcp_only` | `b64c43c7e092301dd9abdfad32d4dc1910192485` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|

## Audit integrity

- Hash chain valid: **True**
- Events checked: `6`
- Chain head: `d773367e47c2fc62033d68bf68236b41850f71bbca01cb1c3697e96120db36f4`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
