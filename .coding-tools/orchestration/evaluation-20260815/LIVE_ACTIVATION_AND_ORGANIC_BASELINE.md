# Tools-Codex-web — Live Activation and Organic Baseline

**Activation date:** 2026-08-15  
**Workspace:** `E:\DEV\Tools-Codex-web`  
**Branch:** `main`  
**Observed Git HEAD:** `dff81e251836666fc825c40bf86e4167afd29c39`  
**Activation boundary:** `2026-08-15T05:58:50.467Z`  

## Scope

This activation loads the already source-complete and regression-proven rework/cost controls into the live Coding Tools MCP runtime. It does not commit, push, publish, release, deploy, enable automatic model routing, enable external review, or create synthetic workload.

Activated behavior includes:

- provider cost-attribution guard;
- pre-EOCL patch preflight and bounded ambiguity diagnostics;
- verification `workdir` semantics;
- known no-write preflight idempotency and `workflow_patch_preflight` observability;
- startup stale-lineage preservation with read-only stale health candidates;
- loaded-behavior runtime identity;
- model-free organic ChatWeb+MCP rework reporting.

## Pre-activation acceptance proof

Exact dirty worktree proof passed before restart:

- full Python MCP suite: **285 passed, 1 skipped**;
- root Node/Electron suite: **99 passed, 0 failed**;
- source-root clean check: passed;
- `git diff --check`: passed;
- Git conflict check: no conflicted paths;
- proof run provider usage events: **0**.

A deterministic race in `test_cancelled_command_has_no_live_child_process` was exposed by the first broad proof. The test previously treated `child.pid` existence as equivalent to complete PID publication. The oracle now waits for a parseable positive PID within the same three-second deadline. The full resilience fault-injection file passed three consecutive runs before the final broad suite passed. Production command-cancellation code was not changed by that repair.

## Runtime activation identity

The Electron supervisor performed one authorized runtime restart.

Previous live identity:

- process instance: `wttnOYlHgwtJXrqx`;
- server instance: `cNqRmaEprI1jpa4j`.

Activated live identity:

- process instance: `2EdVLEHsEBRPxN7A`;
- server instance: `QismhbZaORt6r9ke`;
- runtime version: `0.4.3`;
- performance trace schema: `5`;
- idempotency policy epoch: `task_epoch_v1`;
- Smart-v3 public tool count: **8**;
- Smart-v3 contract SHA-256: `cf1eab62a466b2fb1c8d80f997ac61ef28255d891f13ad2f245d33015d701e86`.

The live runtime now exposes loaded Python behavior identity:

- aggregate fingerprint: `872f7e8379a4a99e0a3b7df81a050f6f44d3bf4402d20b6773a70b6b8073d699`;
- provider cost attribution: `b8ab2d5c110d3ce4ada894d79ce8e6a69913e9fef82b38453c69effe802f8f1e`;
- patch preflight: `b513dc3bd5b461481c49e449f0f4e9978bb62854511d6c8549266c54eb4ebf14`;
- verification workdir: `804690e604da0ecb3e831995fb15d524d84321591a725d0b04ec39530d1ecf06`;
- verification runner: `113415fe640f199961e219d268490b7d3dc8641d731005a1247020728bd5696b`;
- stale reconciliation: `667c9653732ee56ff28eedb6fe22349c43f530c724e720c7bf8f75c7166267f5`;
- routing policy: `53aa7749f7d3fce597593d2963bec3ffb3d1b9e7e5c12ebf844f8c5fb637b5af`;
- external review policy: `41e24bc5efc2cb13df1b263f08da7c62bf2fb7b6171e3248d1ba95a7463f296e`.

This proves that the newly loaded process contains the intended behavior rather than merely observing matching source files on disk.

## Stale-lineage preservation

Startup reconciliation was hardened so stale active runs are not automatically aborted merely because the runtime restarts. Terminal-parent lifecycle contradictions can still be repaired, while stale active runs remain read-only health candidates until explicit operator reconciliation.

The four Execution Hub lineages that were explicitly protected before activation remain `active` after restart:

- `1b8e02ee7fc54798816ad6130d17422a`;
- `2f13838c6ee64d1db4ee08b9e7105461`;
- `31a6106071f744839e8bb775d3d4eb4b`;
- `4fa51cc9f9d740b1ae7abce58c39368c`.

A fifth pre-existing run became a stale health candidate as the 24-hour threshold advanced:

- `22232e07db3749ac924ab0b28a7b34b7` — preparation for a live Execution Hub benchmark, started `2026-08-14T06:01:02.197Z`.

It also remains `active`. The live runtime reports `reconciled_stale_orchestration_runs = 0`; no stale candidate was auto-aborted by activation.

## Organic post-activation baseline

The read-only organic report is bounded to runs started at or after `2026-08-15T05:58:50.467Z` and excludes benchmark/synthetic evidence and explicit model-routed accepted runs.

Immediate post-activation state:

- accepted organic runs: **0**;
- first-pass accepted: **0**;
- repaired accepted: **0**;
- replan count: **0**;
- preflight-avoided known no-write failures: **0**;
- TTA percentiles/multipliers: **not yet measurable**.

This is the expected starting state. No workload was generated to populate the cohort. Rework reduction must not be claimed until real ChatWeb+MCP work produces a representative post-activation sample.

## Policy state after activation

The activation does not promote any model route or paid reviewer:

- Mini/Luna remain HOLD for representative paired same-base/same-oracle/same-semantics evidence;
- Sol xhigh/Terra remain explicit-only and outside the automatic critical path;
- external reviewer remains off by default;
- proof-cache/continuation optimization remains HOLD for lack of demonstrated ROI;
- total cost is usable for ROI only when causal attribution and measurement are complete; missing cost remains unknown, never zero;
- semantic/native LSP activation remains blocked by missing configured loopback binding and credential file.

## Measurement command

Use the read-only reporter against organic work only:

`python resources/coding-tools-mcp/scripts/report_rework_baseline.py --workspace . --since 2026-08-15T05:58:50.467Z --limit 500`

Do not fabricate or synthesize tasks to satisfy a sample quota.
