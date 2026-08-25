# Current Project State — Tools-Codex-web

> **Status date:** 2026-08-25
> **Desktop package:** `coding-tools-mcp 1.0.0`
> **Purpose:** canonical operational snapshot for the current repository. This is not a release note and does not imply that every source change has been activated, packaged, or released.

## 1. Source of truth and document precedence

When repository documents disagree, use this order:

1. **Current implementation + focused tests + live runtime contract** for the exact checkout being operated.
2. **This file (`docs/CURRENT_STATE.md`)** for the current product boundary and operating policy.
3. `README.md`, `docs/ARCHITECTURE.md`, `docs/RECOVERY_HOST.md`, `docs/TESTING.md`, `docs/ROADMAP.md`, `docs/RELEASE_CHECKLIST.md`, and `SECURITY.md` for maintained product guidance.
4. `docs/MODEL_EXECUTION.md` and `docs/agent/*` for the WebCodex core/subsystem they explicitly describe.
5. Dated files under `docs/research/*` as historical evidence, plans, benchmarks, and decision snapshots. They do **not** override later source or this current-state document.

A source implementation can be newer than the process currently running. For Electron, Recovery Host, Coding Tools MCP, and other supervised components, distinguish **source present**, **focused proof passed**, **EOCL accepted**, **controlled activation completed**, and **packaged/released**.

Development startup now has an explicit UI lifecycle contract. `npm run dev` inspects the authenticated Recovery Host receipt for this exact development installation, classifies Electron UI as `CURRENT`, `STALE`, or `MISSING`, uses component activation for a stale UI, launches a missing UI, and succeeds only after `running_revision == disk_revision` is observed with PID/instance/mode metadata. Stale activation is authorized only from `auto_activation.closure_input` when source acceptance, accepted-receipt completeness, activation eligibility, affected-component validity, and `electron_ui` ownership are all explicit; the exact checkpoint/run/wave/proof/accepted-HEAD identity is forwarded as `source_checkpoint`, while missing or ineligible closure state is a typed refusal. `npm run dev:stop` suppresses UI watchdog recovery and asks the exact registered single instance to quit while preserving Recovery Host, MCP, and Tunnel. It refuses an initially unavailable Recovery Host and reports success only after that exact host reports the UI `MISSING` or the previously bound PID is proven dead; transient host loss is not stop proof. `npm run dev:replace` applies the same exact-instance stop postflight, then relaunches and verifies a different UI instance. Direct `npm start` remains a compatibility entry point; when another UI owns the lock it prints an actionable diagnostic instead of silently appearing successful.

The Command Center exposes loaded-source status for the three revisioned components—Electron UI, Recovery Host, and Coding MCP—and reports Tunnel health separately as `READY` or `STOPPED`. `CURRENT` is process/revision evidence only and never derives from Tunnel availability; it is not EOCL acceptance, release, deployment, production, or SLO proof. A source-update notice remains visible whenever a running component revision differs from disk.

### Operational recency override — 2026-08-25

The maintained execution tracker at [`research/260823_CODING_WEB_GATE0_PRL_IMPLEMENTATION_AND_VALIDATION_TRACKER.md`](research/260823_CODING_WEB_GATE0_PRL_IMPLEMENTATION_AND_VALIDATION_TRACKER.md) is the current operational receipt for volatile lifecycle, connector, PRL, and packaged-harness claims. It supersedes older uses of “current”, “active”, or “accepted” in this document when those terms describe a live process or connector rather than a source implementation.

- The final pre-freeze observation was `main @ cab594e4a7a5a4b3189fd36fb009ad44f13da0de`; the resulting PRL/C4 source/docs wave and its `.coding-tools/**` runtime evidence were frozen locally at `81c2e2a49ccf2348ae9b90d28a004bfa281c2ced` (`feat(prl): freeze v11 C4 measurement epoch`). Neither a matched source revision nor a fresh runtime receipt is a package, installer, release, deployment, production, or SLO claim.
- Earlier P0/P4 connector receipts, including the `2026-08-25T03:33:57.999131Z` acknowledgement receipt, are `VERIFIED_SNAPSHOT`. The newest forced Recovery Host snapshot for the current Codex-web process is healthy and target-matched but has `connectorRediscovered=false`, no rediscovery timestamp, and `connectorRefreshRequired=true`. Two fresh real-client read-only calls proved target workspace/tool usability, including scoped nested `task_control(problem.get)` returning the expected `PRL_PROBLEM_NOT_FOUND` without mutation, but ordinary `tools/call` is intentionally not a discovery receipt. Connector-facing `LIVE_PASS` is therefore currently blocked on a real `tools/list` or `server/discover` receipt; no acknowledgement substitution is allowed. The exact checkpoint is in the maintained tracker.
- P5 anchors are terminal; the earlier A0 source-drift epoch has a truthful zero funnel. The newest immutable Gate 0 census has eight threshold-sensitive ordinary rows, all without live owner/resource residue and all below the fixed 86,400-second threshold; they are retained until a fresh exact census demonstrates an actual threshold crossing.
- PRL-D and A2 remain `HOLD_NATURAL_EVIDENCE`; missing natural observations, TTPR, stage coverage, and measured money remain unknown rather than zero.
- The isolated P0.3 packaged Recovery lane is source/package-local evidence, not an exact-frozen release candidate, installed-session, reboot/logon, connector, or production claim.

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

### Authorized-root workspace projection (source contract)

When the Runtime has more than one authorized root, `workspace_context(path)`
canonicalizes the requested root and reports that root's `workspace_id`, project
metadata, Git summary, and task projection. The task projection is loaded from
the selected root and current MCP execution context; it never falls back to the
primary Runtime task or to another project. A context that has been bound by a
workspace read cannot be rebound to a different root (`TASK_CONTEXT_WORKSPACE_MISMATCH`).
Mutating public calls without an explicit path/workdir or an already-bound task
context fail closed with `WORKSPACE_TARGET_REQUIRED` when multiple roots are
authorized. This is source and focused-test proof only; it does not by itself
prove controlled live activation, packaging, release, or production readiness.
The binding is persisted as server-derived state in
`.coding-tools/orchestration/task-context-workspaces.json`; after Runtime
restart the canonical root, current authorization set, and content-free
`workspace_id` are revalidated before reuse. Missing, malformed, legacy, or
unauthorized mappings fail closed as `UNKNOWN_LEGACY_WORKSPACE`,
`WORKSPACE_NOT_AUTHORIZED`, or `WORKSPACE_SCOPE_INCONSISTENT`.
Handoff capsules include the bound workspace identity, authority transition,
source/diff fingerprints, lease/delegation IDs, bounded dirty paths, proof IDs,
and unresolved-risk projection; they do not replace the canonical ledger or
carry transcript/raw command output.
The repository also has a public stateless-HTTP matrix that binds two temporary
workspace roots, creates separate task/run projections, rejects cross-workspace
`task_control`, then recreates the Runtime and verifies the authorized context
and task projection are restored.

`restart_runtime` is an action of `task_control`, not a ninth public tool. The runtime publishes a deterministic contract fingerprint and tool count so Electron can detect a stale ChatGPT connector schema.

Low-level/legacy tools may still exist in compatibility or non-smart modes, but new agent workflows should prefer the compact smart surface.

## 4. Authority, EOCL, routing, and handoff

`agent_workflow` is the primary end-to-end coding path. Mutation/proof workflows are governed by the EOCL state machine and durable orchestration ledger. A successful command or green test does not by itself equal final acceptance; an `ACCEPTING` wave still requires the authorized semantic controller to accept or reject it.

For a selected read-only review, `agent_workflow(phase="prepare")` also accepts an optional `committed_review` object. It requires exact local 40-hex base/head commits, computes an explicit local merge-base range, disables external diff/textconv and system/global attributes, bounds and redacts returned evidence, and signs any continuation to the immutable range. It adds no ninth MCP tool, cannot run in a mutation/resume phase, does not fetch history, and does not itself establish execution or acceptance evidence.

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

### Accepted-Result Economics measurement layer

The current source adds a read-only Accepted-Result Economics layer on top of the existing canonical ledger and performance projection. Its operating North Star is:

> **Minimize Accepted-Result Economic Loss under fixed quality, security, authority and correctness floors.**

The decision order is deliberately lexicographic rather than a single blended score:

```text
quality floor
  -> first-pass outcome
  -> restricted TTAR p90
  -> accepted-result resource cost
  -> human/operator burden
  -> simplicity
```

`npm run report:accepted-result-economics` is read-only. It reports accepted deterministic representative runs, bounded retained per-run resource telemetry, first-pass versus repaired resource distributions, top-tail workflow forensics, proof-cache economics, monetary/token coverage, and an exact-HEAD DRE window for `source_base_drift` and `acceptance_correction`.

Evidence semantics are fail-closed:

- missing money/tokens/resource observations remain **unknown**, never zero;
- monetary CAR remains unavailable until accepted-result monetary-cost coverage is complete;
- `estimated_wait_ms` is the capped gap between consecutive MCP tool calls and may include controller/model/network/operator time; it is **not** proven avoidable loss and is **not** provider billing;
- bounded `performance.run_metrics` retention means an observed resource subset is descriptive and its coverage must be reported rather than silently extrapolated to every accepted run;
- historical DRE counts identify mechanisms, but only natural accepted work on an exact clean current source revision may justify another current hardening wave;
- a low proof-cache hit rate is measurement evidence, not by itself a reason to build a new cache architecture.

P5 source now carries the same economics boundary. Promotion requires accepted-result resource economics and resource-overhead noninferiority; monetary-cost noninferiority is required when complete monetary coverage exists. No missing cost is converted to zero and no partial resource vector is relabeled as monetary CAR. P5 remains explicit, gated, arm-neutral before assignment, and non-automatic.

The current host-observation path uses content-free identities (`turn_id`, `trace_id`, `span_id`) and explicit run binding; prompt/response text is not copied into the correlation record.

## 6. P0-P3 closure and evidence boundary

The P0-P3 program is no longer one undifferentiated implementation gate. Engineering closure, live activation, and representative efficacy are tracked separately so an evidence program cannot silently reopen accepted architecture and a source fix cannot be mistaken for a running-process acceptance.

| Phase | Engineering/source | Live / evidence boundary | Current interpretation |
|---|---|---|---|
| P0 — runtime truth/error boundary | **CLOSED (source)** | **Historical live receipt; current connector discovery blocked** | ExceptionGroup normalization and self-recovery hardening are implemented. The 2026-08-18 connector acceptance is retained as `VERIFIED_SNAPSHOT`; the current process still requires its own real-client `tools/list` or `server/discover` receipt before connector acceptance can be current. |
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

**The 2026-08-19 live collection receipt is historical (`VERIFIED_SNAPSHOT`), not a current P4 outcome.** At that snapshot the ChatWeb/Coding-VP plane exposed `task_control.solution_shadow`, exactly 8 `smart-v3` public tools, contract SHA `bd5c09aeffe02bb60d0f548ed02912e8a21e78b91404186e6896f6d6cbdedd70`, and no reported stale/orphan residue. A later process had a genuine rediscovery and official acknowledgement, but the newest target-process snapshot requires fresh real-client discovery again; neither receipt proves a current `solution_shadow` call or P4 outcome. Source support and later natural evidence remain separate gates.

The P4 empirical gate remains **COLLECTING unless the canonical ledger reporter says `EMPIRICALLY_COMPLETE`**. The 2026-08-19 snapshot (9 representative terminal shadow tasks, 0 representative causal-solution repairs, and `validated_signals=[]`) remains historical evidence that predictive validity was not established; it must not be reused as an activation proof for later source. P4-C therefore remains strict/shadow-only and P4-E remains coverage-first/advisory-only.

**Current P4 readiness (`VERIFIED_CURRENT`, descriptive) remains `COLLECTING`.** At the `2026-08-24T02:19:09.4513934Z` immutable ledger projection, there were `89` representative terminal shadows: causal-solution repair `n=2`, nonrepair `n=64`, and repair-unknown `n=23`; raw post-replan patched observations were `n=27`. `validated_signals=[]`, familywise/holdout validation was not evaluable, and predictive-policy activation remained false. These small/imbalanced labels do not establish a prediction effect or causal intervention result. The newest connector receipt is blocked pending current-process discovery; even a future connector pass would not be a P4 outcome or authorize automatic policy, P5 treatment, or routing.

P5 has a separately gated **source implementation**: manifest v2, secret-handle seed commitment, pre-assignment arm-neutral eligibility/enrollment, restart-safe block randomization, immutable all-assigned ITT outcome rows, analyzer/source-identity checks, and pause/close/hard-stop controls are exposed as `task_control(action="p5")` inside the unchanged eight-tool `smart-v3` surface. A write-capable `agent_workflow` can carry `p5_assignment_id` only for the immutable `feature`/`bugfix` task class; after the ordinary workspace fence is acquired and before any mkdir/patch call, the runtime records an immutable P5 pre-write binding to the exact run, wave, and lease. Caller-supplied first-write time is rejected. The feasibility analyzer projects the complete durable funnel (`assessed → eligible → enrolled → assigned → protocol started → pre-write binding/first-write record → terminal → immediate quality → delayed follow-up/interference`) by assigned arm and workflow stratum. It verifies completed 2/2 block shape and exact table joins instead of pretending that a low-power canary SRM p-value proves randomization; completed-block mismatch, orphaned rows, arm crossover, or a write-binding/first-write mismatch hard-stops a live epoch. Incomplete live blocks are reported as pending, not claimed as imbalance. It does not loosen P4-C or require P4 predictive readiness before a P5-A0 instrumentation epoch. An operator must still explicitly open a frozen, source/runtime-matching manifest, with a clean upstream-matched control-plane source when the manifest requires it and with no active workspace write fence. `p5_automatic_start=false`, `automatic_policy_activation=false`, and automatic production promotion remain invariants. No source proof substitutes for a live P5-A0 A/A epoch, a P5-A treatment canary, an efficacy conclusion, or promotion.

For a development Electron runtime, the trusted parent process may receive `CODING_TOOLS_P5_A0_SEED` only from an external secret-delivery channel during a fail-closed controlled restart. The helper immediately writes that one-time value to Electron `safeStorage` under the `p5A0Seed` SecretStore entry; every normal start, primary-MCP recovery, controlled restart, and code activation reads that encrypted entry and maps it to the opaque `secret://experiment/p5/a` broker handle. Native launch deliberately omits the raw environment name from the child MCP environment and refuses to fall back to it when no SecretStore seed is present, so an incidental restart cannot change experiment identity. Do not place the raw value in the repository, tracked `.coding-tools` evidence, manifest, chat, or ordinary application settings; restart-safe live provisioning remains an operator/runtime operation, not source evidence. The MCP-only controlled-restart helper is fail-closed: it requires exact non-empty `--expect-app-root`, `--expect-workspace`, and `--expect-user-data` identities; binds its RuntimePaths to that verified development product root; then verifies the persisted `nativeDeviceId` and `nativeDeviceInstanceId`, before reading the secret store or terminating a runtime PID.

P5 source identity is the latest code-bearing commit of `HEAD` and upstream, excluding `.coding-tools/**`; evidence-only commits and live runtime projections remain mandatory Git history but do not create a false source-drift event. Any actual source-code commit still requires a new frozen P5 epoch before enrollment or assignment.

The P5-A0 operator path is intentionally narrow. The runtime can prepare a production A0 manifest only from the current code-bearing source/upstream identity, loaded eight-tool runtime contract, a material content-free environment fingerprint, the deterministic analyzer identity, and the SHA-256 commitment of `secret://experiment/p5/a`. `prepare_a0` is read-only and never opens an epoch. `open` rechecks source, runtime, analyzer, environment and writer quiescence, so a prepared manifest cannot be reused across environment drift. The production A0 horizon is four hours. Electron exposes only `status / prepare / open / analyze / pause / resume / close / hard-stop`; it keeps the prepared manifest in the trusted main process, never accepts raw seed material from the renderer, and exposes no P5-A treatment activation control. This remains shadow A/A instrumentation: both assigned labels receive the current control protocol and no automatic routing or promotion is enabled.

### P0 historical live activation incident — source CLOSED / prior receipt accepted

During an earlier 2026-08-18 closure check, every ChatWeb Coding MCP action attempted through that connected tool surface (`workspace_context`, `task_control restart_runtime`, and `agent_workflow`) returned a raw `ExceptionGroup: unhandled errors in a TaskGroup` before a normal typed tool result could be observed. The incident and the later acceptance are historical evidence for that source/runtime instance; neither establishes the identity or connector state of the current process.

Two source-side gaps are now addressed:

1. The MCP protocol boundary normalizes an `ExceptionGroup` into typed `ASYNC_TASK_GROUP_FAILED` JSON-RPC evidence instead of stringifying the raw group.
2. Recovery Host now has a throttled **semantic tool-plane watchdog**. It performs a read-only local `workspace_context` canary, distinguishes "HTTP health is green" from "tools/call is usable", and delegates recovery only through the existing `RuntimeOrchestrator.restart({ automatic: true })` lifecycle authority. It is suppressed while the lifecycle controller is busy, recovering, handing off, or manually stopped. The canary does not create a second writer or recovery authority.

Focused source regression proves the semantic canary accepts a real `workspace_context` response, rejects an HTTP-200 raw TaskGroup JSON-RPC failure, restarts only after the configured repeated-failure threshold, and does not restart while the lifecycle controller is busy.

**Historical live acceptance (`VERIFIED_SNAPSHOT`).** On 2026-08-18 the then-connected instance demonstrated the accepted behavior on the real tool path:

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

- P0 source activation and multi-workspace control plane: **LIVE_PASS** for the current local Coding MCP process. The first controlled restart loaded the earlier `f46022a4…` component receipt; the second allowed restart loaded matching current running/disk revision `34df0931…` after the stateless-background context propagation repair. Fresh Electron-safeStorage discovery exposed exactly eight `smart-v3` tools, Recovery Host acknowledgement is current, cross-workspace context/RUN guards passed without task-state leakage, a pre-restart opaque Codex context restored to the same workspace identity after restart, and the scoped W3 proof/handoff reached `CHECKPOINTED` before its acknowledged projection was cleared to idle. Earlier stale Codex and HR RUN reconciliations remain durable ledger history. This remains local runtime/control-plane evidence, not a package or production claim;
- automatic non-deterministic routing: **OFF / deterministic fail-closed** pending representative accepted paired evidence;
- automatic global server-first: **OFF** pending representative compute-placement evidence;
- P3 representative efficacy: **DEFERRED**, separate from the closed engineering gate;
- P4 source/gate engineering: **ACCEPTED**; development launch authority is pinned to the current checkout and `solution_shadow` schema publication has been observed;
- P4 live tool-call health: the 2026-08-19 `solution_shadow` call remains **VERIFIED_SNAPSHOT**. The current target process requires a fresh discovery receipt before its connector status can be promoted, and P4 collection remains unobserved until a natural task actually records a P4 outcome;
- P4 predictive validity: **COLLECTING unless `report_p4_readiness.py` reports `EMPIRICALLY_COMPLETE`**; benchmark, synthetic, and unlabeled shadow rows are not promotion evidence;
- P5 experiment integrity source: **IMPLEMENTED / FAIL-CLOSED.** A prior explicit P5-A0 epoch was closed transparently with zero enrollment, assignment, write binding, or outcome when the Wave 3 funnel gap above was discovered; it is evidence of operator/seed/manifest control only, never A/A health, treatment feasibility, or efficacy. `task_control(action="p5")` validates a frozen manifest, source/runtime identity, secret-backed seed commitment, assignment/enrollment order, and the absence of an active workspace writer before opening a rebaselined epoch. P5-A0 may be explicitly opened for instrumentation before P4 predictive completion; P5-A treatment remains separately gated by its own registered manifest, natural eligible task/oracle funnel, and explicit operator authority. Neither starts automatically, and neither is a production-promotion signal;
- auto-handoff: **OFF** pending more real A/B evidence;
- paid Flash terminal reproduction: **requires explicit external-cost authorization**;
- provider/model write authority over the primary checkout: **not granted by telemetry or routing alone**;
- ChatGPT context-pressure percentage: **unknown unless the host exposes a real source**; do not fabricate one.

## 11. Historical WebCodex material

WebCodex core documents, Rust crates, server/runner deployment material, and dated research remain useful and should not be deleted merely because the desktop product has moved further. Their scope must be explicit. When a historical plan says something is future work but current source now implements it, preserve the historical record and update this current-state document or the maintained product guide instead of rewriting chronology.
