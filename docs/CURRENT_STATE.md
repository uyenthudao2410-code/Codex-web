# Current Project State — Tools-Codex-web

> **Status date:** 2026-08-22
> **Desktop package:** `web-mcp-assistant 0.3.4`
> **Purpose:** canonical operational snapshot for the current repository. This is not a release note and does not imply that every source change has been activated, packaged, or released.

## 1. Source of truth and document precedence

When repository documents disagree, use this order:

1. **Current implementation + focused tests + live runtime contract** for the exact checkout being operated.
2. **This file (`docs/CURRENT_STATE.md`)** for the current product boundary and operating policy.
3. `README.md`, `docs/ARCHITECTURE.md`, `docs/RECOVERY_HOST.md`, `docs/TESTING.md`, `docs/ROADMAP.md`, `docs/RELEASE_CHECKLIST.md`, and `SECURITY.md` for maintained product guidance.
4. `docs/MODEL_EXECUTION.md` and `docs/agent/*` for the WebCodex core/subsystem they explicitly describe.
5. Dated files under `docs/research/*` as historical evidence, plans, benchmarks, and decision snapshots. They do **not** override later source or this current-state document.

A source implementation can be newer than the process currently running. For Electron, Recovery Host, Coding Tools MCP, and other supervised components, distinguish **source present**, **focused proof passed**, **EOCL accepted**, **controlled activation completed**, and **packaged/released**.

## 2. Current product boundary

The product currently operated from this repository is the **Windows Electron Execution Hub + Coding Tools MCP** stack. The repository still contains substantial WebCodex Rust/server/runner functionality inherited from and developed beyond the upstream project; that code is a foundation/subsystem, not the only description of the desktop product.

```text
ChatWeb / ChatGPT
      |
      | MCP over primary tunnel
      v
Recovery Host / Execution Hub authority
      |
      +--> ONE Coding Tools MCP Runtime -----> workspace / Git / commands / proof
      |            ^
      |            |
      |       Codex Desktop thin stdio proxy
      |
      +--> Electron Execution Control Center
      |
      +--> independent Recovery MCP + Recovery Tunnel

Secondary reasoning/provider lanes:
  Codex App Server / OpenCode -> bounded candidate, review, or read-only provider work
  Coding Tools MCP / EOCL      -> mutation, proof, durable ledger, acceptance boundary
```

There must not be two peer Coding Tools runtimes independently mutating the same workspace/ledger. ChatWeb and Codex Desktop share the Execution Hub truth; they do not synchronize transcripts.

## 3. Current `smart-v3` MCP contract

The current `smart` profile intentionally exposes exactly these eight public tools:

- `workspace_context`
- `agent_workflow`
- `task_control`
- `document_workflow`
- `exec_command`
- `command_control`
- `request_permissions`
- `view_image`

`restart_runtime` is an action of `task_control`, not a ninth public tool. The runtime publishes a deterministic contract fingerprint and tool count so Electron can detect a stale ChatGPT connector schema.

Low-level/legacy tools may still exist in compatibility or non-smart modes, but new agent workflows should prefer the compact smart surface.

## 4. Authority, EOCL, routing, and handoff

`agent_workflow` is the primary end-to-end coding path. Mutation/proof workflows are governed by the EOCL state machine and durable orchestration ledger. A successful command or green test does not by itself equal final acceptance; an `ACCEPTING` wave still requires the authorized semantic controller to accept or reject it.

Current authority rules:

- ChatWeb/Sol remains the normal semantic controller and final-acceptance authority for coordinated work.
- Electron/Recovery Host owns service lifecycle and secrets.
- Coding Tools MCP owns deterministic workspace mutation, verification, durable task/run/proof state, and write fencing.
- Codex Desktop is a second client of the same Runtime through the thin proxy; controller transfer is explicit and does not automatically grant a repository write lease.
- Codex App Server and OpenCode are secondary lanes, not an independent authoritative writer of the primary checkout.

### Routing policy currently in force

Supported explicit routes include `deterministic`, `mini`, `luna`, `terra`, `sol_xhigh`, `sol_max`, and `sol_ultra`. However, **`execution_route=auto` is currently fail-closed to `deterministic`** while representative accepted paired evidence is insufficient. The runtime reason is the ROI/evidence gate, not an inability to invoke the other routes.

Consequences:

- do not describe Mini/Luna/Terra/Sol as automatically selected in production today;
- non-deterministic lanes are explicit/evaluation lanes until the accepted representative cohort gate changes;
- `sol_max` and `sol_ultra` still require explicit high-cost acknowledgement;
- provider traffic/capacity telemetry does not itself authorize automatic routing;
- OpenCode automatic routing remains off/evidence-gated;
- automatic global server-first compute placement remains off until representative P3 evidence supports promotion.

Auto-handoff is also kept off until enough representative real-task A/B evidence shows a stable benefit without state loss or duplicate work. Durable handoff capsules remain available for rollover/recovery.

## 5. Runtime evidence and measurement

For repository-local evaluation and postmortems, the durable orchestration ledger is the canonical causal source:

```text
.coding-tools/orchestration/ledger.sqlite3
```

Supporting projections include `.coding-tools/performance.json`, `.coding-tools/task-history.json`, and `.coding-tools/task-state.json`. These are runtime evidence, not source-code inputs, and must not be folded into source/worktree fingerprints.

Current measurement policy:

- distinguish provider-reported/measured tokens, cost, and timing from estimates;
- never present internal estimated credits as provider billing;
- keep representative, benchmark, and synthetic evidence separate;
- do not promote routing or placement from small or synthetic samples;
- host-visible latency claims require an explicit host observation bound to the exact EOCL run/wave, not timestamp proximity.

The current host-observation path uses content-free identities (`turn_id`, `trace_id`, `span_id`) and explicit run binding; prompt/response text is not copied into the correlation record.

## 6. P0-P3 closure and evidence boundary

The P0-P3 program is no longer one undifferentiated implementation gate. Engineering closure, live activation, and representative efficacy are tracked separately so an evidence program cannot silently reopen accepted architecture and a source fix cannot be mistaken for a running-process acceptance.

| Phase | Engineering/source | Live / evidence boundary | Current interpretation |
|---|---|---|---|
| P0 — runtime truth/error boundary | **CLOSED** | **LIVE ACTIVATION ACCEPTED** | ExceptionGroup normalization and self-recovery hardening are implemented, and the currently connected Windows runtime has passed the live connector acceptance checklist on post-fix source. |
| P1 — measurement integrity | **CLOSED** | **ECONOMICS DEFERRED** | Controlled plumbing is sufficient for experiments. Missing controller/provider usage or money remains unknown, never zero; it does not authorize automatic routing. |
| P2 — rework diagnosis | **CLOSED** | **CAUSAL EFFICACY DEFERRED** | The diagnostic phase identified rework as a material cost. Generic `CHECK_FAILED` and `BUILD_VERIFICATION_FAILED` observations now receive prospective, content-free stage/family detail; historic rows without that detail remain unclassified rather than being backfilled into a causal repair cause. Incomplete historical causal/oracle coverage is a measurement limitation for later experiments, not a reason to expand P2 architecture indefinitely. |
| P3 — compute-placement control | **CLOSED / ACCEPTED** | **REPRESENTATIVE EFFICACY DEFERRED** | Explicit placement control is implemented; the representative 10–20-pair pilot remains separate and global server-first stays off. |

The P0 **live activation acceptance** below was satisfied on 2026-08-18. The program may move to a new engineering roadmap item while P1/P2/P3 evidence programs continue in parallel without reopening their closed implementation waves.

### P4 — Solution Economics Shadow — SOURCE/GATE ACCEPTED / EVIDENCE COLLECTING

P4 engineering is now split into three explicit boundaries: source contract, live collection health, and empirical predictive readiness. Current source provides the shadow evidence path for `feature` and `bugfix` runs:

- one task-level recommendation is recorded before the first `write_lease_acquired` event;
- recommendation evidence is structured and content-free: candidate scope, estimated touched surface, root-cause confidence, oracle strength, expected repair risk, and smallest causal solution scope;
- the recommendation is joined after execution to durable accepted-result evidence including first-pass acceptance, repair/replan count, TTAR, accepted file receipts, proof duration, explicit local/wait observation spans, and explicit manual-fix outcome when available;
- lines/symbols touched, cost, wait, or intervention remain unknown when they were not actually observed; absent telemetry is never converted to zero;
- representative rows alone are eligible for predictive promotion; benchmark, synthetic, and unlabeled rows remain descriptive evidence only;
- predictive validation requires representative terminal outcome variation plus positive leave-one-out Brier gain and Bonferroni-adjusted Wilson interval separation; the result remains association evidence, not a causal treatment claim;
- LOC/touched surface remains an explanatory variable, not the optimization target.

P4 does **not** add another public MCP tool and does not change routing, model choice, compute placement, write authority, proof policy, acceptance authority, or production mutation behavior. `solution_shadow` is an action inside `task_control` on the existing eight-tool `smart-v3` surface.

The development supervisor has also been hardened so development Coding MCP launches are pinned to the current Electron checkout (`appRoot/resources/coding-tools-mcp`), with that module root first in `PYTHONPATH`, used as `cwd`, persisted as launch provenance, and mismatches refused rather than silently reusing a foreign/stale runtime.

The population/readiness window is fail-closed against unrelated run churn. `solution_shadow_population_report` now selects the latest enrolled shadow runs directly (`population_scope=latest_shadow_runs_v2`) instead of selecting the latest generic runs and filtering afterward. This prevents diagnose/telemetry workload from evicting genuine P4 evidence from the analysis window.

Repository operators can evaluate the canonical committed ledger with:

```text
python resources/coding-tools-mcp/scripts/report_p4_readiness.py --workspace .
python resources/coding-tools-mcp/scripts/report_p4_readiness.py --workspace . --require-ready
python resources/coding-tools-mcp/scripts/report_p4_readiness.py --workspace . --require-p5-experiment-active
npm run check:p5-readiness
```

The manual-only GitHub workflow `.github/workflows/p4-readiness.yml` exposes the P4 gate without enabling ordinary push/PR Actions consumption. `--require-ready` succeeds only when `p4_gate.can_answer_which_signals_predict_repair=true`; missing or insufficient evidence cannot be converted into a green P4 closure claim. `--require-p5-experiment-active` is an observation assertion for an already explicit P5 epoch, not an activation command. `npm run check:p5-readiness` and the deprecated `--require-p5-ready` retain the legacy P4-predictive treatment readiness meaning and must not be used to claim P5-A0 integrity readiness.

**Live collection health remains a separate boundary, and the currently connected process has now passed it.** On 2026-08-19 the live ChatWeb/Coding-VP plane exposes `task_control.solution_shadow`, reports exactly 8 `smart-v3` public tools with contract SHA `bd5c09aeffe02bb60d0f548ed02912e8a21e78b91404186e6896f6d6cbdedd70`, and reports zero stale orchestration runs, unresolved stale runs, orphaned background operations, and orphaned idempotency records. Live P4 collection is therefore active on this runtime instance. Future runtime-affecting changes still require their own activation check; historical raw `ExceptionGroup` incidents remain historical evidence rather than current runtime status.

The P4 empirical gate remains **COLLECTING unless the canonical ledger reporter says `EMPIRICALLY_COMPLETE`**. The 2026-08-19 snapshot (9 representative terminal shadow tasks, 0 representative causal-solution repairs, and `validated_signals=[]`) remains historical evidence that predictive validity was not established; it must not be reused as an activation proof for later source. P4-C therefore remains strict/shadow-only and P4-E remains coverage-first/advisory-only.

P5 has a separately gated **source implementation**: manifest v2, secret-handle seed commitment, pre-assignment arm-neutral eligibility/enrollment, restart-safe block randomization, immutable all-assigned ITT outcome rows, analyzer/source-identity checks, and pause/close/hard-stop controls are exposed as `task_control(action="p5")` inside the unchanged eight-tool `smart-v3` surface. A write-capable `agent_workflow` can carry `p5_assignment_id` only for the immutable `feature`/`bugfix` task class; after the ordinary workspace fence is acquired and before any mkdir/patch call, the runtime records an immutable P5 pre-write binding to the exact run, wave, and lease. Caller-supplied first-write time is rejected. The feasibility analyzer projects the complete durable funnel (`assessed → eligible → enrolled → assigned → protocol started → pre-write binding/first-write record → terminal → immediate quality → delayed follow-up/interference`) by assigned arm and workflow stratum. It verifies completed 2/2 block shape and exact table joins instead of pretending that a low-power canary SRM p-value proves randomization; completed-block mismatch, orphaned rows, arm crossover, or a write-binding/first-write mismatch hard-stops a live epoch. Incomplete live blocks are reported as pending, not claimed as imbalance. It does not loosen P4-C or require P4 predictive readiness before a P5-A0 instrumentation epoch. An operator must still explicitly open a frozen, source/runtime-matching manifest, with a clean upstream-matched control-plane source when the manifest requires it and with no active workspace write fence. `p5_automatic_start=false`, `automatic_policy_activation=false`, and automatic production promotion remain invariants. No source proof substitutes for a live P5-A0 A/A epoch, a P5-A treatment canary, an efficacy conclusion, or promotion.

For a development Electron runtime, the trusted parent process may receive `CODING_TOOLS_P5_A0_SEED` only from an external secret-delivery channel during a fail-closed controlled restart. The helper immediately writes that one-time value to Electron `safeStorage` under the `p5A0Seed` SecretStore entry; every normal start, primary-MCP recovery, controlled restart, and code activation reads that encrypted entry and maps it to the opaque `secret://experiment/p5/a` broker handle. Native launch deliberately omits the raw environment name from the child MCP environment and refuses to fall back to it when no SecretStore seed is present, so an incidental restart cannot change experiment identity. Do not place the raw value in the repository, tracked `.coding-tools` evidence, manifest, chat, or ordinary application settings; restart-safe live provisioning remains an operator/runtime operation, not source evidence. The MCP-only controlled-restart helper is fail-closed: it requires exact non-empty `--expect-app-root`, `--expect-workspace`, and `--expect-user-data` identities; binds its RuntimePaths to that verified development product root; then verifies the persisted `nativeDeviceId` and `nativeDeviceInstanceId`, before reading the secret store or terminating a runtime PID.

P5 source identity is the latest code-bearing commit of `HEAD` and upstream, excluding `.coding-tools/**`; evidence-only commits and live runtime projections remain mandatory Git history but do not create a false source-drift event. Any actual source-code commit still requires a new frozen P5 epoch before enrollment or assignment.

### P0 live activation incident — CLOSED / ACCEPTED

During an earlier 2026-08-18 closure check, every ChatWeb Coding MCP action attempted through that connected tool surface (`workspace_context`, `task_control restart_runtime`, and `agent_workflow`) returned a raw `ExceptionGroup: unhandled errors in a TaskGroup` before a normal typed tool result could be observed. That observation remains historical incident evidence; it no longer describes the currently connected process.

Two source-side gaps are now addressed:

1. The MCP protocol boundary normalizes an `ExceptionGroup` into typed `ASYNC_TASK_GROUP_FAILED` JSON-RPC evidence instead of stringifying the raw group.
2. Recovery Host now has a throttled **semantic tool-plane watchdog**. It performs a read-only local `workspace_context` canary, distinguishes "HTTP health is green" from "tools/call is usable", and delegates recovery only through the existing `RuntimeOrchestrator.restart({ automatic: true })` lifecycle authority. It is suppressed while the lifecycle controller is busy, recovering, handing off, or manually stopped. The canary does not create a second writer or recovery authority.

Focused source regression proves the semantic canary accepts a real `workspace_context` response, rejects an HTTP-200 raw TaskGroup JSON-RPC failure, restarts only after the configured repeated-failure threshold, and does not restart while the lifecycle controller is busy.

**Live acceptance is now CLOSED / ACCEPTED.** On 2026-08-18 the connected instance demonstrated the accepted behavior on the real tool path:

- delivered/source HEAD `0cf1eec7366f09d52235ca235d92ccd8b3ea4e18` contains `beb2dc51` (protocol normalization) and `c7841920` (boundary regression) in its ancestry;
- the primary Coding MCP process observed as PID `18444` was created at `2026-08-18 15:28:53 +07:00`, after both P0 source commits, and runs `E:\DEV\Codex-web\resources\native-python\pythonw.exe -m coding_tools_mcp --workspace E:\DEV\Codex-web`;
- `workspace_context(detail=full)` succeeds through the real connector and reports the current source identity plus live `process_instance_id` / `server_instance_id`;
- `agent_workflow` prepare succeeds through the same live tool plane;
- `task_control` audit succeeds with hash-chain integrity PASS and quiescent execution resources;
- the live `smart-v3` contract reports exactly 8 public tools;
- focused ExceptionGroup boundary regression passes `4/4` from the Coding MCP component root;
- no raw `ExceptionGroup` escaped any of the live acceptance calls;
- the live runtime reported zero stale orchestration runs, unresolved stale runs, orphaned background operations, and orphaned idempotency records.

No Runtime restart was performed for this acceptance. A restart was unnecessary because the observed primary Coding MCP process itself started after the accepted P0 fix commits and then passed the live checklist. Future runtime-affecting changes still require their own source-versus-live activation proof; this acceptance does not collapse that distinction.

### P3 Engineering / Control Plane — CLOSED / ACCEPTED

The explicit validation compute-placement implementation is accepted at source commit `2c990332` (`feat: control validation compute placement`). P3 engineering is no longer a semantic roadmap blocker.

Accepted behavior:

- `compute_placement_policy = local_only | server_preferred` is available only for eligible long structured `cargo_check` / `cargo_test` validation.
- Explicit placement requires an Agent-backed project, no sandbox, structured asynchronous validation support, and a clean exact-source Runner checkout.
- Invalid explicit contexts fail closed before enqueue/process execution.
- `local_only` keeps execution on the source Runner and never selects server compute.
- `server_preferred` uses exact-source target selection and revalidation; if no valid target remains, execution safely falls back to the source Runner.
- Placement evidence records requested policy, actual placement, fallback, source Runner and executor Runner and is preserved through Job metadata, handoff/terminal result, `job_status`, and `job_log` projection.
- Omitting the selector preserves the established production behavior, including the pre-existing dirty-snapshot auto-offload path.
- Focused R3B2 integration regression covered server dispatch, local-only source execution, safe fallback, invalid-context pre-enqueue rejection, evidence projection, and selector-absent regression behavior before acceptance.

The preregistered analyzer remains frozen under the identity recorded in `docs/research/260818_P3_SERVER_FIRST_PAIRED_EXPERIMENT_MANIFEST.md`. Existing pilot outcomes must not be reinterpreted under an edited analyzer without a new manifest/version.

### P3 Representative Efficacy Pilot — DEFERRED

The frozen experiment `p3-server-first-pilot-v1` targets **10–20 genuinely eligible representative paired tasks**. Its purpose is instrumentation/variance/failure-mix/break-even/power planning before any confirmatory promotion claim.

This evidence program is intentionally separate from the engineering completion gate:

- it does not block moving to another engineering roadmap item after P0 live activation acceptance;
- it does not authorize claiming server-first is faster, cheaper, or better;
- it does not auto-promote global server-first;
- automatic activation remains `false`;
- missing controller/provider monetary cost is unknown, never zero;
- a confirmatory cohort is still required before broad promotion.

## 7. Recovery architecture

Independent recovery is no longer only a roadmap concept. The current source contains:

- a headless Recovery Host that owns primary Runtime/Tunnel/Execution-Hub lifecycle;
- a Windows user-session Recovery Supervisor that resurrects the Recovery Host under bounded, fail-closed rules;
- a separate Recovery MCP process and, when configured, a separate Recovery Tunnel;
- a semantic Coding MCP tool-plane watchdog that can distinguish control-health success from failed `tools/call` behavior and delegates restart to the existing orchestrator;
- `recovery_plane_mode=independent_mcp_tunnel_v1` state;
- bounded `recovery_status` / confirmed `repair_primary_runtime` behavior rather than arbitrary remote shell/process control;
- controlled component activation and accepted-code activation gates.

The Recovery Tunnel must use a distinct tunnel identity from the primary Coding Tunnel. If a second tunnel resource is not configured, the independent local Recovery MCP may still exist while remote Recovery Tunnel status remains `not_configured`.

Implementation in source is not the same as a packaged/live proof. Recovery changes still require the relevant process-boundary, activation, packaged-Windows/login, and fault-matrix acceptance appropriate to the change.

The current checkout also has a repeatable isolated packaged-Windows Recovery lane: `npm run test:recovery:packaged`. It builds `dist/win-unpacked`, launches the packaged `--recovery-host` under a temporary Electron user-data root, proves device identity plus independent Recovery MCP, exercises the packaged Recovery Supervisor in healthy and fail-closed fault cases, cleans only isolated PIDs, and verifies that the production Recovery descriptor identity is unchanged. This is packaged runtime evidence, not publication of an installer and not a substitute for an actual installed-logon/session smoke when that boundary is required for release.

## 8. Semantic localization and LSP resource policy

Coding Tools MCP uses semantic-first localization when the native WebCodex LSP provider is available and falls back to bounded text search per query when semantic localization is unavailable, denied by resource admission, or cannot handle a query.

The current worktree also contains LSP process telemetry/resource-governance work: process instance identity, PID/start identity, current and peak working set, pending-request state, memory-pressure classification, restart/drain counters, bounded idle reaping, and soft/hard pressure behavior. Pressure policy is internal and testable; it must not be documented as one universal production memory number derived from a historical sample.

The P2/P3 LSP/resource hardening was technically closed on 2026-08-16. Its 10-cycle real Connector/Runner/rust-analyzer acceptance window recorded distinct process identities for every cold restart, final `STOPPED`, zero active HEAVY claim/write fence/stale run/orphan/overlap, and p95 peak LSP working set below 30 MiB on that Windows host. This host-scoped sample supports keeping the existing 2 GiB/3 GiB soft/hard defaults; it is evidence for that acceptance window, not a universal memory guarantee.

## 9. Validation, security, and release boundary

For ordinary changes, validate only the behavior changed. The current top-level entry points are:

```text
npm test
npm run test:mcp
npm run test:all
npm run test:recovery:e2e
npm run test:recovery:packaged
npm run canary:opencode-flash:preflight
npm run dist
npm run dist:dir
```

The paid/real provider canary `npm run canary:opencode-flash` may create external provider cost and must run only with explicit authorization for that cost. Its `:preflight` variant performs readiness validation without provider dispatch.

Runtime-affecting source changes need a separate activation/instance check after source tests. A release claim needs source proof, required live/process proof, exact accepted fingerprint, packaging checks, and rollback guidance appropriate to the component.

Account credential snapshots under `docs/ac/` are local-only data and must never be tracked. They have been removed from the current `main` tree and `/docs/ac/` is ignored. Credentials that were previously committed must be treated as exposed and rotated/revoked. Purging them from existing Git history is a separate destructive history-rewrite action and is not implied by ordinary cleanup commits.

## 10. Known evidence gates that remain intentional

The following are deliberate evidence/authority gates, not documentation bugs:

- P0 live activation: **ACCEPTED** on the post-fix active Windows instance; future runtime-affecting changes still require their own activation proof;
- automatic non-deterministic routing: **OFF / deterministic fail-closed** pending representative accepted paired evidence;
- automatic global server-first: **OFF** pending representative compute-placement evidence;
- P3 representative efficacy: **DEFERRED**, separate from the closed engineering gate;
- P4 source/gate engineering: **ACCEPTED**; development launch authority is pinned to the current checkout and `solution_shadow` schema publication has been observed;
- P4 live tool-call health: **LIVE ACTIVE / VERIFIED** on the current 2026-08-19 ChatWeb/Coding-VP runtime contract; future runtime-affecting changes still require their own activation proof;
- P4 predictive validity: **COLLECTING unless `report_p4_readiness.py` reports `EMPIRICALLY_COMPLETE`**; benchmark, synthetic, and unlabeled shadow rows are not promotion evidence;
- P5 experiment integrity source: **IMPLEMENTED / FAIL-CLOSED.** A prior explicit P5-A0 epoch was closed transparently with zero enrollment, assignment, write binding, or outcome when the Wave 3 funnel gap above was discovered; it is evidence of operator/seed/manifest control only, never A/A health, treatment feasibility, or efficacy. `task_control(action="p5")` validates a frozen manifest, source/runtime identity, secret-backed seed commitment, assignment/enrollment order, and the absence of an active workspace writer before opening a rebaselined epoch. P5-A0 may be explicitly opened for instrumentation before P4 predictive completion; P5-A treatment remains separately gated by its own registered manifest, natural eligible task/oracle funnel, and explicit operator authority. Neither starts automatically, and neither is a production-promotion signal;
- auto-handoff: **OFF** pending more real A/B evidence;
- paid Flash terminal reproduction: **requires explicit external-cost authorization**;
- provider/model write authority over the primary checkout: **not granted by telemetry or routing alone**;
- ChatGPT context-pressure percentage: **unknown unless the host exposes a real source**; do not fabricate one.

## 11. Historical WebCodex material

WebCodex core documents, Rust crates, server/runner deployment material, and dated research remain useful and should not be deleted merely because the desktop product has moved further. Their scope must be explicit. When a historical plan says something is future work but current source now implements it, preserve the historical record and update this current-state document or the maintained product guide instead of rewriting chronology.
