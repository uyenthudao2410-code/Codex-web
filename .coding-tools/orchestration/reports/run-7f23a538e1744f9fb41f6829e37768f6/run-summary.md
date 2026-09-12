# Orchestration Run Summary

- Run: `7f23a538e1744f9fb41f6829e37768f6`
- Task: `7796926ae5c34b45bbc6d6db7051525d`
- Objective: Implement Problem prl-stale-reconcile-managed-job-scope-20260912 revision 2. In exact stale-run preflight, managed_job_residue must mean actual managed-process residue classifications, not any LIVE_OWNED managed command with a valid canonical RUN parent. Derive managed_job_residue from immutable lifecycle-census managed_jobs so STALE_MANAGED_JOB_RESIDUE and ORPHANED_OR_FOREIGN_MANAGED_JOB still block, while LIVE_OWNED does not become a workspace-global blocker. Preserve unbound_live_resource_residues, target_has_live_ownership, integrity, projection, P5, threshold, exact-ID and idempotency guards unchanged. Add focused regressions for LIVE_OWNED non-blocking and stale/orphan classification blocking. Do not reconcile outsider RUNs in this implementation wave. Do not edit lifecycle_census.py, restart, commit, push, clean, reset, or backfill history.
- Status: **accepted**
- Started: `2026-09-12T07:24:04.514Z`
- Finished: `2026-09-12T07:35:43.890Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `8b7656c9e1e24ff6998d166de918c91f` | 1 | `run_initial_objective` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | replanned |
| 2 | `981c24543d054eaea6ff31c98b61f252` | 2 | `replan_request` | `mcp_only` | `7bc1caee37107a15e74eb078b52fe314e5fa33ab` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 3f1d395d19094c469b3c65c847cf40ac | 981c24543d054eaea6ff31c98b61f252 | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | 99b3cbb617fcfb17ece7ec244a564bf3b1a2b4cae1ccb1080b219c72e535d94e | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 50616 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 50628 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 50619 | `RUNTIME_RESUME_REQUIRED` | `ROUTED` | A non-terminal wave was recovered outside its original synchronous execution. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `79`
- Chain head: `c77b005a4cbacdda8dbafeb1b9c3c03f449e8fcec74d22153f8ac27cbc6d0468`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
