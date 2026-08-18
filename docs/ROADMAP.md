# Roadmap — Current Desktop Product

This roadmap describes the current **Tools-Codex-web Windows Desktop Execution Hub**, not the historical WebCodex product roadmap. For exact current-state precedence, see [`CURRENT_STATE.md`](CURRENT_STATE.md).

## Current baseline

The maintained product boundary now includes Electron Execution Control Center; one shared Coding Tools MCP Runtime; ChatWeb primary-tunnel access; Codex Desktop thin-proxy access into the same authority; the verified `smart-v3` eight-tool surface; EOCL/controller/write-fencing/proof/handoff/observation/restart controls; Recovery Host + Windows Recovery Supervisor + independent Recovery MCP/Tunnel; bounded Codex/OpenCode provider lanes; semantic-first localization; closed LSP process telemetry/resource governance; an isolated packaged-Windows Recovery acceptance lane; accepted explicit validation compute-placement control for `local_only` and `server_preferred`; protocol-level ExceptionGroup normalization; and source-side semantic MCP health supervision that distinguishes control-health success from a broken tool plane.

## Policy already decided

1. **One Runtime authority.** ChatWeb and Codex Desktop do not run peer primary runtimes over the same workspace/ledger.
2. **Deterministic proof first.** Tests/compiler/tool evidence outrank model debate when they can answer the question.
3. **Automatic routing is evidence-gated.** `execution_route=auto` currently resolves to `deterministic` while representative accepted paired evidence is insufficient.
4. **High-cost routes are explicit.** `sol_max`/`sol_ultra` require acknowledgement.
5. **Secondary providers are not primary writers.** Codex/OpenCode lanes do not gain primary-checkout authority from routing or telemetry.
6. **Auto-handoff stays off** until representative real-task A/B evidence demonstrates stable benefit without duplicate work or state loss.
7. **Automatic global server-first stays off** until representative compute-placement evidence supports promotion.
8. **No fabricated observability.** Unknown quota, billing, ChatGPT context percentage or host state stays unknown.

## P0-P3 closure boundary before the next engineering phase

P0-P3 engineering/control work is not to be expanded merely to fill representative evidence gaps. The remaining gates are classified explicitly:

- **P0 engineering/source: CLOSED.** Protocol ExceptionGroup normalization and semantic tool-plane self-recovery are implemented. **P0 live activation is ACCEPTED** on the current post-fix Windows process and real connector path.
- **P1 measurement integrity: CLOSED.** Controlled measurement plumbing is sufficient for experiments. Economics remains an evidence program; missing usage/cost is unknown, never zero.
- **P2 diagnostic phase: CLOSED.** Incomplete historical causal/oracle coverage is a measurement limitation for subsequent intervention studies, not a reason to keep extending P2 architecture.
- **P3 engineering/control plane: CLOSED / ACCEPTED.** Representative efficacy remains deferred; global server-first remains OFF.

The prior P0 live-activation blocker is cleared. The accepted live checks covered current process/source identity, `workspace_context`, `agent_workflow` prepare, `task_control` audit, exactly 8 `smart-v3` public tools, no raw ExceptionGroup leakage on the acceptance calls, and no stale/orphan/conflicting write authority. A new engineering phase is therefore governed by its own task-specific acceptance gates rather than by unfinished P0-P3 architecture.

## P4 — Solution Economics Shadow — source accepted, evidence collection active

P4 is shadow-only. For `feature` and `bugfix` tasks, record a structured recommendation before the first write and compare it later with durable accepted-result outcomes. The pre-mutation predictors are candidate solution scope, estimated touched surface, root-cause confidence, oracle strength, expected repair risk, and smallest causal solution scope. Outcome evidence includes first-pass acceptance, repair/replan count, TTAR, accepted file receipts, proof duration, explicitly observed local/wait spans, and explicit manual-fix outcome when present.

**Engineering/source is accepted.** Evidence collection and live activation are separate gates. The current connected ChatWeb/Coding-VP schema still lacks `task_control.solution_shadow`, so live P4 collection on that connector remains pending an explicitly requested controlled runtime restart/reconnect and post-activation verification. Do not backfill a recommendation after the first write merely to manufacture a sample.

The P4 analysis is descriptive until predictive validity is established. Reports separate `representative` evidence from benchmark/synthetic/unlabeled rows; missing observations remain unknown, LOC is explanatory rather than a target, and no shadow recommendation can change production behavior. The gate stays open until representative data contains enough real repair/non-repair outcome variation to validate which pre-change signals predict repair. No sample-size threshold is invented in advance merely to close the phase.

In parallel, continue collecting frozen P3 server-first representative pairs naturally. Do not reopen P3 engineering and keep global server-first OFF.

## P5 — Controlled Rework-Reduction A/B — gated / not started

Start only after P4 predictive validity is established. Begin with `feature` and `bugfix` tasks under a stable quality oracle. Treatment is the smallest bounded intervention: a causal-fix gate, explicit oracle settlement before mutation, and bounded change surface. Promotion requires the quality floor to hold, repair/replan not to worsen, and TTAR/CAR to improve materially. P4 shadow recommendations alone never activate this treatment.

## P6 — P3 server-first representative evidence — parallel collection only

Continue the frozen P3 representative pilot naturally while P4/P5 progress. Keep global server-first OFF. This workstream supplies evidence; it does not reopen the accepted P3 control-plane architecture.

## P7 — Model-routing economics — later, strong-oracle cohorts first

After rework economics are understood, compare deterministic execution against Mini/Luna first on strong-oracle cohorts. Terra and Sol treatment lanes come later because integration width and review cost are higher. `sol_max` and `sol_ultra` remain explicit-only high-cost escalation and are never automatic evidence shortcuts.

## P8 — Joint accepted-cost optimizer — deferred

Only after P4-P7 provide validated inputs should routing, repair risk, proof cost, latency, and quality be combined into an optimizer for expected accepted cost. Do not optimize raw LOC, model-call count, or isolated tool latency as the North Star.

## P9 — Capacity scaling — evidence-triggered only

Scale workers, providers, runners, or orchestration capacity only when telemetry demonstrates that capacity is the active bottleneck. Do not add fleet/orchestration architecture pre-emptively.

### Side workstreams

- LSP: measure economic value (localization/proof/rework impact) before further architecture expansion.
- Storage/artifact hygiene: keep it maintained, but do not let cleanup displace the accepted-result economics roadmap.
- Approximate engineering allocation while P4 is active: 60–70% rework/accepted-result economics, 15–20% representative evidence, 10–15% operational reliability/telemetry hygiene, and approximately 0% new orchestration architecture without a concrete regression.

## Immediate hardening and acceptance priorities

### Closed — exact-source runtime activation

- Keep source proof, controlled activation, live canary and packaged/released claims separate for future runtime-affecting changes.
- Current live acceptance observed primary Coding MCP PID `18444`, created `2026-08-18 15:28:53 +07:00`, running directly from `E:\DEV\Codex-web` after the accepted ExceptionGroup source commits.
- The real connector passed `workspace_context(detail=full)`, `agent_workflow` prepare and `task_control` audit; the live contract reported exactly 8 `smart-v3` tools, and the focused ExceptionGroup boundary regression passed `4/4`.
- No raw `ExceptionGroup` escaped the live acceptance calls; stale/orphan runtime residue was zero and audit integrity passed.
- No restart was performed or required for this acceptance because the observed process already postdated the source fix. Keep any future restart/activation fail-closed around active commands, background work, provider/agent lanes and EOCL acceptance.
- The isolated packaged-Windows Recovery Host/Supervisor lane remains covered by `npm run test:recovery:packaged`; a release claim still requires any relevant installed Windows logon/session and production-only fault checks.

### Evidence program — representative routing economics

- Produce accepted, homogeneous paired cohorts by task class/oracle/environment instead of synthetic no-op volume.
- Compare quality/critical-defect/repair/TTA/cost with explicit sample sizes and provenance.
- Keep automatic non-deterministic routing disabled until the evidence gate is actually satisfied.
- Real paid OpenCode Flash terminal canary requires explicit external-cost authorization; preflight remains the default zero-dispatch check.

### Closed — LSP resource hardening

- Process identity, memory-pressure telemetry, reaper behavior, cold restart identity and live Connector/Runner/rust-analyzer soak were closed in the 2026-08-16 P2/P3 acceptance window.
- The host-scoped evidence supported keeping the existing 2 GiB/3 GiB soft/hard defaults; future changes require new representative evidence rather than reopening the completed wave from stale roadmap wording.

### Closed — P3 engineering / compute-placement control plane

P3 engineering is **CLOSED / ACCEPTED** at source commit `2c990332` and is no longer a roadmap blocker.

- `compute_placement_policy` supports explicit `local_only` and `server_preferred` for eligible long structured `cargo_check` / `cargo_test` validation.
- `local_only` keeps execution on the source Runner and does not select server compute.
- `server_preferred` uses exact-source server target selection/revalidation and safely falls back to the source Runner.
- Invalid explicit contexts fail closed before enqueue/process execution.
- Placement evidence is retained through Job metadata, handoff/terminal result, `job_status`, and `job_log` projection.
- Omitting the selector preserves the established production behavior, including the pre-existing dirty-snapshot auto-offload path.
- Focused R3B2 integration regression and affected package checks were accepted before the `2c990332` delivery.
- The preregistered analyzer remains frozen; changing it requires a new explicit analysis identity/version.

Do not reopen this implementation wave merely because the representative efficacy cohort is not yet populated.

### Deferred — P3 representative efficacy pilot

The efficacy pilot is intentionally **DEFERRED**, not an implementation blocker.

- Frozen experiment: `p3-server-first-pilot-v1`.
- Target: 10–20 genuinely eligible representative paired tasks before variance/failure-mix/power planning is interpreted.
- Pilot evidence must vary compute placement only and preserve exact source, task semantics, oracle, environment, cache stratum, controller class, proof policy, and risk policy.
- The pilot may not auto-promote server-first globally.
- No claim that server-first is faster, cheaper, or better is allowed until representative evidence supports that claim.
- Missing controller/provider monetary cost remains unknown, never zero.
- Automatic global server-first remains **OFF**.

## P0 operational activation closure

An earlier connected ChatWeb Coding MCP instance returned a raw `ExceptionGroup: unhandled errors in a TaskGroup`. Current `main` contains both protocol normalization and a Recovery Host semantic tool-plane watchdog for that HTTP-green/tool-plane-broken failure mode. The current post-fix process has now demonstrated the accepted source behavior through the real connector, including the live truth/orchestration smoke and eight-tool contract.

Therefore P0 is operationally frozen as **CLOSED / LIVE ACCEPTED** for this source/runtime instance. This does not prove P1/P2/P3 efficacy or economics and does not enable automatic routing or global server-first; those remain evidence-gated. The next engineering phase may proceed without reopening P0-P3 architecture.

Credential snapshots under `docs/ac/` are local-only and must never be tracked. They have been removed from current `main` and `/docs/ac/` is ignored. Any credential that previously entered Git history must be treated as exposed and rotated; a history rewrite is a separate destructive maintenance action and requires explicit authorization.

## Deferred until evidence promotes them

- automatic provider/model routing from small or synthetic samples;
- automatic controller transfer/auto-handoff;
- automatic global server-first from an unpopulated or underpowered pilot;
- dual primary Runtime authority;
- broad autonomous provider writes to the primary checkout;
- arbitrary remote process/service management through Recovery;
- fabricated context-pressure percentages;
- large generic fleet/orchestration layers without a second real use case;
- rewriting historical research to pretend it described current source.

## Completion criteria

A semantic engineering item is complete when its relevant source contract, focused/affected-boundary proof and EOCL final acceptance are satisfied. Live activation, packaging/release, and representative efficacy are separate gates and must be reported separately rather than being used to reopen an already accepted implementation wave. For the current P0-P3 freeze, the P0 live connector acceptance checklist has passed on the active Windows instance. Tool count, raw test count, LOC or model-call count are not completion metrics by themselves.
