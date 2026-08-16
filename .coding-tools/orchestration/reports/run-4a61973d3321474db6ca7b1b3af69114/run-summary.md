# Orchestration Run Summary

- Run: `4a61973d3321474db6ca7b1b3af69114`
- Task: `a2f803de64c04f6abf2a8a85622c378e`
- Objective: Run proof-only focused R2A behavior validation on the current accepted source. Do not modify files. Verify both tests matching exact_source_capable_: full clean HEAD source identity is attached to the durable validation Job, and dirty source fails before enqueue.
- Status: **accepted**
- Started: `2026-08-16T12:24:08.290Z`
- Finished: `2026-08-16T14:25:00.840Z`

## Outcome metrics

- Waves: **10**
- Route decisions: **9**
- Failures observed: **9**
- REPLAN transitions: **9**
- Proof stages: **15**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `ec5f738d38a44c9a865ca1c2f87ce312` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | replanned |
| 2 | `587c710f43cc4351a1ef03bf8046d53d` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | replanned |
| 3 | `6fd8e7f19bf44ef080b348a26c1736f7` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | replanned |
| 4 | `1afafe4acdda4a96a0af2b6a7ea4bc89` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | replanned |
| 5 | `77f9c9e40828418d822c7b5dd3beb8cb` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | replanned |
| 6 | `f6e053e69a494f09a317d3daab1e318f` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | replanned |
| 7 | `c9e563b844d742b59e130ffa256b13f5` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | replanned |
| 8 | `c4517b046fbb45c3a2831530107fe205` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | replanned |
| 9 | `24889b031e894a53b7142e29a5273486` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | replanned |
| 10 | `7a7cdb6a29a94e29b8f4fbda659250cc` | `mcp_only` | `cf6cb6ddbf29d90515d003ce72490ffda985c37f` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| bfbce23980284582bafcac49b0069272 | 7a7cdb6a29a94e29b8f4fbda659250cc | accepted | cf6cb6ddbf29d90515d003ce72490ffda985c37f | dfb27833ba01959b3c1cc5cc9136ea540826268840255fbc63a2b4a2bc21a857 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 7912 | `deterministic` | `deterministic` | explicit_request |
| 7922 | `deterministic` | `deterministic` | explicit_request |
| 7985 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 8492 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 8519 | `deterministic` | `deterministic` | explicit_request |
| 8537 | `deterministic` | `deterministic` | explicit_request |
| 8560 | `deterministic` | `deterministic` | explicit_request |
| 8577 | `deterministic` | `deterministic` | explicit_request |
| 8673 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 7914 | `BASE_DRIFT` | `ROUTED` |  |
| 7949 | `SOL_REJECTED` | `ACCEPTING` | Focused R2A behavior test command reached the 600s workflow budget during root test-binary link and returned status=timeout. Treat this as PROOF_TIMEOUT, not a behavior pass or test failure. No files were modified in this proof-only wave. Compile/type-check evidence remains independently green from cargo check --lib and fresh cargo check --tests. |
| 7957 | `BASE_DRIFT` | `PREFLIGHT` |  |
| 8006 | `CHECK_FAILED` | `PROVING` |  |
| 8513 | `CHECK_FAILED` | `PROVING` |  |
| 8531 | `SOL_REJECTED` | `ACCEPTING` | Read-only PID inspection succeeded, but the overall bugfix is not yet acceptable: the sole managed blocker is a live cmd.exe PID 22244 with parent 18972, so it must not be quiesced or killed until its process-tree ownership is identified. Continue the same run with a new diagnostic wave. |
| 8554 | `SOL_REJECTED` | `ACCEPTING` | Process-tree inspection proves the sole blocker is a live long-lived Node service spawned through cmd.exe by the Coding MCP pythonw runtime, not a dead proof process. The run is not yet acceptable: we must identify the service ownership path and prevent runtime-internal persistent services from being misclassified as active managed workload, without weakening fail-closed handling of real commands. |
| 8571 | `CHECK_FAILED` | `PROVING` |  |
| 8588 | `CHECK_FAILED` | `PROVING` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `231`
- Chain head: `d0592b6682f02168e4b61d96656e05803ad9313b2f91ed63fc2cf738b972ca3a`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
