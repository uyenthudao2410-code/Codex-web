# Tools-Codex-web — Post-Activation Remediation Closure

**Date:** 2026-08-15  
**Workspace:** `E:\DEV\Tools-Codex-web`  
**Branch:** `main`  
**Observed Git HEAD:** `dff81e251836666fc825c40bf86e4167afd29c39`

## 1. Activation state

The original rework/cost remediation is live. The authoritative activation boundary recorded by the existing activation report is `2026-08-15T05:58:50.467Z`.

The originally activated runtime identity was:

- process instance `2EdVLEHsEBRPxN7A`;
- server instance `QismhbZaORt6r9ke`.

During this continuation, a later runtime process replacement was observed without this ChatWeb turn invoking `task_control.restart_runtime`. The current identity at closure is:

- process instance `4hfSLt3fPr4cOuvY`;
- server instance `_Ltd6JrlNOHucC2v`;
- runtime version `0.4.3`;
- performance trace schema `5`.

The current process still reports the intended loaded behavior fingerprints:

- provider cost attribution `b8ab2d5c110d3ce4ada894d79ce8e6a69913e9fef82b38453c69effe802f8f1e`;
- patch preflight `b513dc3bd5b461481c49e449f0f4e9978bb62854511d6c8549266c54eb4ebf14`;
- verification workdir `804690e604da0ecb3e831995fb15d524d84321591a725d0b04ec39530d1ecf06`;
- verification runner `113415fe640f199961e219d268490b7d3dc8641d731005a1247020728bd5696b`;
- stale reconciliation `667c9653732ee56ff28eedb6fe22349c43f530c724e720c7bf8f75c7166267f5`;
- routing policy `53aa7749f7d3fce597593d2963bec3ffb3d1b9e7e5c12ebf844f8c5fb637b5af`;
- external review policy `41e24bc5efc2cb13df1b263f08da7c62bf2fb7b6171e3248d1ba95a7463f296e`.

Aggregate loaded-behavior fingerprint: `872f7e8379a4a99e0a3b7df81a050f6f44d3bf4402d20b6773a70b6b8073d699`.

## 2. Windows TaskStateStore atomic-replace remediation

Run `1e001e8d2c5d4c2f8f53612590168ffc` was already accepted/checkpointed after adding a local bounded retry helper around the two TaskStateStore atomic JSON `os.replace` sites.

The implementation preserves temp-file-plus-replace atomicity and retries only on Windows for retryable access/sharing failures: `EACCES`, `EPERM`, `EBUSY`, or WinError `5`/`32`. Non-retryable failures and the final retryable failure are re-raised. Temp cleanup remains in `finally`.

A later test-only delta adds the missing exhaustion oracle: a persistent retryable Windows access-denied failure must use exactly `WINDOWS_ATOMIC_REPLACE_ATTEMPTS` attempts, sleep only between attempts, re-raise the final `PermissionError`, and clean the temp file. The auxiliary orchestration run that added this test was aborted rather than accepted, so its old command output is not used as proof.

Fresh deterministic exact-worktree proof from this continuation:

- focused `test_task_state_and_build.py`: **53 passed, 3 subtests passed**;
- full Python MCP suite: **288 passed, 1 skipped, 20 subtests passed**;
- `git diff --check -- resources/coding-tools-mcp`: passed;
- conflicted-path check: none;
- only observed Git diagnostic: LF-to-CRLF warning for `test_resilience_fault_injection.py`, non-failing.

The current runtime process identity changed after this TaskStateStore patch was present on disk, giving high confidence that the current Python process reloaded the patched module. However, the runtime's `loaded_behavior` attestation schema does not currently expose a dedicated TaskStateStore/helper fingerprint. Therefore the helper is treated as **source-complete, integrated-regression-proven, and high-confidence reloaded**, not as independently helper-fingerprint-attested.

## 3. Organic post-activation measurement

The model-free organic reporter was run against the exact activation boundary `2026-08-15T05:58:50.467Z`. No workload was synthesized.

Observed cohort:

- accepted organic runs: **3**;
- first-pass accepted: **3**;
- first-pass rate: **100%**;
- repaired accepted: **0**;
- repaired rate: **0%**;
- replan count: **0**;
- `workflow_patch_preflight=true` / known no-write failures avoided before run creation: **0**;
- first-pass TTA p50: **41.558 s**;
- first-pass TTA p90: **127.359 s**;
- repaired TTA: not measurable because there are no repaired accepted runs.

This is a positive observed signal, not a production-rate conclusion. Three accepted runs are not a representative sample and the observed work is remediation-heavy. No claim is made that the live production replan/rework rate has been reduced by a quantified amount.

`workflow_patch_preflight=true = 0` in this window means no organic known no-write patch failure has occurred after activation; it does not imply that the observability path is absent.

## 4. Cost interpretation

The post-activation organic report is `model_free` and excluded zero explicit-model-route accepted runs. There is no accepted paid-candidate cohort in this sample from which to compute causal cost ROI.

Cost remains usable for ROI only when accepted-result causal attribution is complete. Missing cost is unknown, not zero.

## 5. Stale-lineage state

The current runtime reports:

- stale orchestration candidates: **5**;
- reconciled stale orchestration runs: **0**;
- unresolved stale orchestration runs: **5**.

The four previously protected Execution Hub lineages remain untouched:

- `1b8e02ee7fc54798816ad6130d17422a`;
- `2f13838c6ee64d1db4ee08b9e7105461`;
- `31a6106071f744839e8bb775d3d4eb4b`;
- `4fa51cc9f9d740b1ae7abce58c39368c`.

The fifth candidate is the pre-existing `22232e07db3749ac924ab0b28a7b34b7`, which crossed the 24-hour stale threshold. It also remains untouched. No stale candidate was auto-aborted during the observed process replacements.

## 6. Policy state

Policy remains unchanged:

- Mini/Luna: **HOLD** pending representative paired same-base/same-oracle/same-semantics evidence;
- Sol xhigh/Terra: explicit-only, outside automatic critical path;
- external reviewer: off by default;
- proof cache/continuation optimization: HOLD;
- cost ROI: only with complete causal attribution;
- no synthetic workload is to be created merely to improve the metrics.

## 7. Closure judgment

The original remediation is live and fingerprint-attested. The Windows TaskStateStore atomic-replace remediation is source-complete and now has fresh focused plus full-suite integrated proof; a later process replacement provides high-confidence runtime reload, with the explicit limitation that TaskStateStore is not yet a named `loaded_behavior` fingerprint component.

The organic post-activation signal is currently 3/3 first-pass with zero repaired/replan events, but the sample remains too small and remediation-heavy to support a quantified production improvement claim. Continue passive organic collection under the existing policy rather than manufacturing benchmark traffic.
