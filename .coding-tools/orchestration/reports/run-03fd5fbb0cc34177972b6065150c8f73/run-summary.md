# Orchestration Run Summary

- Run: `03fd5fbb0cc34177972b6065150c8f73`
- Task: `3902c6cded2141adb19ed598e66adf21`
- Objective: Continue the accepted token-usage master-plan implementation. Implement the smallest coherent W2 correctness delta proven by prepare: controller turn usage must deduplicate across reconnect/REPLAN wave boundaries within the same RUN, instead of deriving the controller economic identity from wave_id. Preserve the first exact attribution event; retrying the same exact controller turn receipt in a later wave must return duplicate and must not double-count economics, while a conflicting receipt for the same RUN+turn identity must still fail closed as different evidence. Keep provider UsageEvent identity behavior unchanged. Do not add a database/framework, do not fabricate session/coverage data, preserve unknown_not_zero and all unrelated dirty work. No commit, push, restart, package, release or deploy.
- Status: **aborted**
- Started: `2026-08-31T18:36:15.844Z`
- Finished: `2026-08-31T19:03:29.603Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **2**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **0**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `af3c06c1bc6e4ad09ab18c891c4376dc` | 1 | `run_initial_objective` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 2 | `14ecacaeb4784d2492fae7a9a5dbf363` | 2 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 3 | `26734c18978f4c99b0766be318f1252a` | 3 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | aborted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 33567 | `deterministic` | `deterministic` | explicit_request |
| 33613 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 33603 | `SOL_REJECTED` | `ACCEPTING` | W2 acceptance rejected: exact current source still derives build_usage_event usage_id from run_id + wave_id + identity_key, while controller identity_key=turn_id. Therefore the same exact ChatWeb controller turn retried after REPLAN/new wave within the same RUN receives a different usage_id and can double-count economics. The passing proof did not exercise this cross-wave invariant, and the wave has no durable file receipts on the causal W2 files. REPLAN same RUN with a controller-specific wave-independent economic identity plus discriminating cross-wave duplicate/conflict tests; preserve provider UsageEvent identity behavior. |
| 33627 | `BUILD_VERIFICATION_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `66`
- Chain head: `68eebbb3d4ed53474a066a82e2b7ed4159dd304a63399378475eb04de5050a26`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
