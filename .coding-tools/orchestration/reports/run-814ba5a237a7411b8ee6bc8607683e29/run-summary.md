# Orchestration Run Summary

- Run: `814ba5a237a7411b8ee6bc8607683e29`
- Task: `a32db2a42c6846659b264f42963e7c96`
- Objective: Complete P2 context economics: add durable content-free ArtifactRef projections for orchestration proofs and handoff capsules; add OrchestrationLedger.session_query as a bounded model-free priority projection over failure/acceptance/proof/route/context evidence; switch agent_workflow resume to session_query while preserving top-level task compatibility and compact task_resume. Keep public Smart-v3 tools/actions/schemas unchanged and preserve EOCL authority. No renderer changes, restart, paid provider call, commit, push, or deploy.
- Status: **active**
- Started: `2026-08-14T17:26:01.503Z`
- Finished: `None`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **1**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `032a4236158e498ab082a67edaf58bbb` | `mcp_only` | `5decaa48300b10a6df39676c677745bc881cd7d9` | replanned |
| 2 | `d73730d6124741fbb6b6bccea9a705de` | `mcp_only` | `5decaa48300b10a6df39676c677745bc881cd7d9` | active |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 3008 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 3018 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 3012 | `PATCH_AMBIGUOUS` | `EXECUTING` |  |
| 3026 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `23`
- Chain head: `895fcacd41223dbbb9d81f81cd1064276bafc42f03169bf9097852a3cdb0186c`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
