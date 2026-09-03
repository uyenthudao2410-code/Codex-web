# Orchestration Run Summary

- Run: `dcb84117b43e4233bc0cb16571b2ff3d`
- Task: `17813c6b605241b9b6d822c0204bec93`
- Objective: Prepare the smallest exact patch for RUN 21a. Read current source and callsites only. Determine: (1) the minimal single Python authority for host-observation schema v6 without circular imports; (2) the exact response envelope keys actually needed to discover response.completed/response while never traversing message/output/content or arbitrary arrays/objects; (3) the actual HTTP identity/provenance fields used before controller usage ledger mutation; (4) the authoritative current RUN/WAVE and host/evaluation turn/trace correlation surfaces; (5) how _require_hub_controller proves the same controller lease is active and how to test expiry/mismatch. Preserve first-call compatibility only where there is genuinely no RUN/WAVE authority; once authority exists, incomplete or mismatched provenance must fail closed. Do not mutate or run verification in prepare.
- Status: **aborted**
- Started: `2026-09-03T09:14:09.437Z`
- Finished: `2026-09-03T09:14:24.064Z`

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
| 1 | `322d3f7db62e4d5a9a5153c5a8033d06` | 1 | `run_initial_objective` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | aborted |

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
- Events checked: `4`
- Chain head: `914f294eb4726ba47df2385a74b33593e65544ff58d3f2e17f37b5c2bbb162cc`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
