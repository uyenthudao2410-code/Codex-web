# Tools-Codex-web — Rework Cause Analysis and Remediation

**Evaluation date:** 2026-08-15  
**Workspace:** `E:\DEV\Tools-Codex-web`  
**Observed HEAD:** `dff81e251836666fc825c40bf86e4167afd29c39`  
**Branch:** `main`  
**Historical cohort cutoff:** `2026-08-15T05:25:22.371Z`  
**Fixed historical repaired cohort:** 52 accepted runs  
**Purpose:** reduce time-to-accepted-result and expected cost by preventing avoidable REPLAN/rework without weakening EOCL, proof, security, routing, or final acceptance gates.

## Executive conclusion

The largest repeatable rework sources in the fixed 52-run cohort are:

1. `PATCH_AMBIGUOUS`: 17/52 primary failures (32.7%).
2. `BUILD_VERIFICATION_FAILED`: 11/52 (21.2%).
3. `SOL_REJECTED`: 9/52 (17.3%).

Together they account for 37/52, or 71.2%, of repaired runs.

The first two have repeatable mechanical prevention opportunities and were targeted in source. `SOL_REJECTED` is heterogeneous and is intentionally not weakened: it caught multiple distinct real-world/invariant problems, so reducing it by relaxing final acceptance would trade latency for quality/security risk.

## Historical taxonomy

### Primary first-failure class

| Failure class | Runs | Share of repaired cohort |
|---|---:|---:|
| PATCH_AMBIGUOUS | 17 | 32.7% |
| BUILD_VERIFICATION_FAILED | 11 | 21.2% |
| SOL_REJECTED | 9 | 17.3% |
| PROMPT_TOO_LARGE | 2 | 3.8% |
| PATCH_CONTEXT_NOT_FOUND | 2 | 3.8% |
| INVALID_ARGUMENT | 2 | 3.8% |
| CHECK_FAILED | 2 | 3.8% |
| CANDIDATE_SCOPE_MISSING | 2 | 3.8% |
| RUNTIME_RESUME_REQUIRED | 1 | 1.9% |
| CANDIDATE_TARGET_MISSING | 1 | 1.9% |
| CANDIDATE_REPORTED_BLOCKED | 1 | 1.9% |
| CANDIDATE_MODEL_NOT_COMPLETED | 1 | 1.9% |
| BASE_DRIFT | 1 | 1.9% |

### All failure events inside repaired runs

| Failure class | Events |
|---|---:|
| PATCH_AMBIGUOUS | 23 |
| BUILD_VERIFICATION_FAILED | 19 |
| SOL_REJECTED | 15 |
| PATCH_CONTEXT_NOT_FOUND | 7 |
| INVALID_ARGUMENT | 3 |
| CHECK_FAILED | 3 |
| RUNTIME_RESUME_REQUIRED | 2 |
| PROMPT_TOO_LARGE | 2 |
| CANDIDATE_SCOPE_MISSING | 2 |
| CANDIDATE_REPORTED_BLOCKED | 2 |
| PERMISSION_REQUIRED | 1 |
| PATCH_FAILED | 1 |
| CANDIDATE_TARGET_MISSING | 1 |
| CANDIDATE_MODEL_NOT_COMPLETED | 1 |
| BASE_DRIFT | 1 |

This difference between primary and all-event counts matters: one repaired task can suffer more than one failed wave, so preventing an early mechanical failure can eliminate downstream re-localization, proof reruns, and acceptance work as well.

## Estimated TTA contribution

The following is an **estimate**, not a causal latency decomposition. For each repaired run, excess TTA was approximated as its TTA minus the historical median first-pass TTA of the same task class, floored at zero.

| Primary class | n | Median repaired TTA | Estimated excess TTA sum | Median estimated excess |
|---|---:|---:|---:|---:|
| PATCH_AMBIGUOUS | 17 | 106.558 s | ~2,216.167 s | ~76.144 s |
| SOL_REJECTED | 9 | 231.660 s | ~2,145.987 s | ~195.303 s |
| BUILD_VERIFICATION_FAILED | 11 | 132.964 s | ~1,357.618 s | ~96.607 s |

These figures support prioritization only. They must not be interpreted as exact savings attributable to a future fix.

## Cluster 1 — PATCH_AMBIGUOUS

### Historical failure mode

Patch context was valid text but matched multiple locations. EOCL correctly refused to guess. Historically, the failure occurred after orchestration had already been created, often causing a repaired run even though the failure was predictable from the source snapshot before any write.

### Remediation implemented

Source now normalizes caller patch inputs before EOCL creation and preflights predictable patch failures before creating a run/wave or acquiring write authority:

- `_agent_patch_inputs(args)` builds the exact caller patch sequence, including new-file patches.
- `_preflight_patch_sequence(patches)` parses the sequence and dry-runs disjoint patch envelopes against the same source snapshot.
- A single multi-file patch envelope retains the patcher's existing atomic behavior.
- Cross-envelope same-path dependencies are not guessed or reordered; preflight reports them as a dependency case and preserves existing execution semantics.
- Ambiguous update hunks expose bounded `candidate_lines` (maximum 8) plus `candidate_lines_truncated`, allowing a caller to re-anchor precisely without a broad search.
- The patcher still never selects an ambiguous match automatically.

### Rework avoided vs failure hidden

Preflight rejection is intentionally **not** treated as success. It is a known no-write terminal failure. The difference is that the caller can correct the patch before EOCL mutation/orchestration begins, avoiding an unnecessary REPLAN lineage and write-authority lifecycle.

Durable idempotency now records such failures as `failed`, not `unknown`, because the failure occurs before any side effect. Generic crashes after possible side effects remain `unknown` and fail closed.

A content-free durable summary field is recorded:

`workflow_patch_preflight: true`

This provides an organic post-activation counter for patch failures diverted before orchestration without creating synthetic workloads.

## Cluster 2 — BUILD_VERIFICATION_FAILED

### Historical substructure

The 11 primary failures were not one homogeneous implementation problem. A substantial majority were proof/oracle/harness/setup issues, including:

- nested Python package tests executed from an incorrect working directory;
- stale Smart-v3 SHA/routing expectations after an intentional schema/policy change;
- stale test assumptions in Code Mode / Execution Hub scenarios;
- test-fixture assumptions that did not match the actual runtime contract;
- documentation whitespace failures.

Other cases were genuine defects and must continue to fail proof, including Windows provenance assertion issues, hub proxy transport handling, and direct CLI bootstrap/import behavior.

### Remediation implemented

The existing `agent_workflow.workdir` contract is now honored by build verification:

- `build_verify.verify_build(..., command_root=...)` separates project detection/artifact root from command cwd.
- Runtime `verify_build` resolves `workdir`, defaulting to `path`.
- `apply_changes_and_verify` passes the workflow workdir through to verification.
- Tests/builds therefore run from the explicit requested directory rather than unconditionally from the project root.

This removes a repeatable proof-setup mismatch without guessing a working directory from command text.

### What was deliberately not changed

- Failed tests/builds still fail the wave.
- No stale oracle is auto-rewritten by production runtime.
- No test result is reclassified as success because it appears to be infrastructure-related.
- Proof-cache fingerprints are unchanged.

## Cluster 3 — SOL_REJECTED

### Why no mechanical suppression was added

The 9 primary `SOL_REJECTED` cases were heterogeneous. Historical rejection reasons included distinct issues such as:

- boundedness of deep evidence packets;
- Windows JSONC environment escaping;
- OpenCode output-schema compatibility;
- panel identity/liveness truthfulness;
- orphan authority/cursor referential integrity;
- acceptance-state/protocol behavior;
- trailing-whitespace hygiene;
- paid-canary safety preflight;
- artifact references omitted from compact payloads.

There is no single safe source-level relaxation that addresses these without weakening final acceptance. Therefore:

- ChatWeb Sol remains final-acceptance authority.
- No `SOL_REJECTED` bypass, auto-accept, or lower acceptance threshold was introduced.
- The proper strategy is to move repeated specific invariants into earlier deterministic/focused oracles when a stable repeated pattern emerges.

## Proof of remediation

Focused and broad validation performed on the dirty exact worktree:

- Core patch-preflight/workdir focused suite: **50 passed, 3 subtests passed**.
- Full Python MCP after core changes: **283 passed, 1 skipped** in 118.58 s.
- Idempotency + task-state focused suite: **56 passed, 3 subtests passed**.
- Agent/universal idempotency + task-state after parse-edge hardening: **70 passed, 5 subtests passed**.
- Latest observability-only focused check: **6 passed**.
- Root Node/Electron `npm test`: PASS.
- `git diff --check`: PASS.
- Conflict check: none.

The remediation implementation runs were deterministic, external review remained disabled, and checked implementation waves recorded zero provider usage events.

## Cohort integrity

The historical baseline is frozen at:

`2026-08-15T05:25:22.371Z`

At that cutoff there were exactly **52 repaired accepted runs**.

After remediation development, the ledger has one additional repaired run because the first implementation attempt deliberately reproduced the old `PATCH_CONTEXT_AMBIGUOUS` behavior before source mutation and then materially replanned with unique function anchors. This implementation run must not be mixed into the historical cohort when judging improvement.

## Activation boundary

The current long-running runtime process has **not** been restarted after these source changes. Therefore the live process does not yet load:

- the earlier cost-attribution guard;
- the new patch-preflight behavior;
- the workdir verification fix;
- the preflight idempotency/observability fields.

No claim of live behavioral improvement should be made until a future **explicitly authorized runtime restart** loads the new source and runtime/source identity is verified.

## Organic post-activation measurement plan

After an explicitly authorized restart:

1. Record new process/server instance IDs and source/worktree identity.
2. Do not create synthetic tasks to fill a quota.
3. For organic ChatWeb+MCP work, track:
   - accepted first-pass vs repaired runs;
   - primary failure class;
   - `workflow_patch_preflight=true` durable idempotency outcomes as avoided orchestration replans;
   - `BUILD_VERIFICATION_FAILED` with explicit command/workdir context;
   - TTA p50/p90 by task class;
   - provider economics only when causal attribution is complete.
4. Compare the post-activation organic cohort with the fixed historical cohort, stratified by task class where sample size permits.
5. Do not infer improvement from a few convenient successes; preserve all accepted and failed organic observations.

A practical observation checkpoint is roughly 20–30 accepted organic tasks, but this is an observation window, not an automatic promotion threshold.

## Routing/cost policy remains unchanged

- ChatWeb + deterministic MCP remains the default path.
- Mini/Luna stay explicit until representative paired same-base/same-oracle/same-semantics evidence exists.
- Sol xhigh/Terra remain explicit and outside the automatic critical path.
- External reviewer remains off by default.
- No paid provider workload is generated to manufacture evidence.
- Proof-cache/continuation optimization remains HOLD because current evidence does not show sufficient ROI.

## Expected effect, stated carefully

The changes are designed to reduce **avoidable orchestration replans**, particularly the largest historical mechanical class (`PATCH_AMBIGUOUS`), and to remove a demonstrated verification-CWD mismatch. Source/tests prove the prevention mechanisms, but the magnitude of real TTA/cost improvement remains an empirical question for the next organic post-activation cohort.
