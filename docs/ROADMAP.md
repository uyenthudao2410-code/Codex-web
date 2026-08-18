# Roadmap — Current Desktop Product

This roadmap describes the current **Tools-Codex-web Windows Desktop Execution Hub**, not the historical WebCodex product roadmap. For exact current-state precedence, see [`CURRENT_STATE.md`](CURRENT_STATE.md).

## Current baseline

The maintained product boundary now includes Electron Execution Control Center; one shared Coding Tools MCP Runtime; ChatWeb primary-tunnel access; Codex Desktop thin-proxy access into the same authority; the verified `smart-v3` eight-tool surface; EOCL/controller/write-fencing/proof/handoff/observation/restart controls; Recovery Host + Windows Recovery Supervisor + independent Recovery MCP/Tunnel; bounded Codex/OpenCode provider lanes; semantic-first localization; closed LSP process telemetry/resource governance; an isolated packaged-Windows Recovery acceptance lane; and accepted explicit validation compute-placement control for `local_only` and `server_preferred`.

## Policy already decided

1. **One Runtime authority.** ChatWeb and Codex Desktop do not run peer primary runtimes over the same workspace/ledger.
2. **Deterministic proof first.** Tests/compiler/tool evidence outrank model debate when they can answer the question.
3. **Automatic routing is evidence-gated.** `execution_route=auto` currently resolves to `deterministic` while representative accepted paired evidence is insufficient.
4. **High-cost routes are explicit.** `sol_max`/`sol_ultra` require acknowledgement.
5. **Secondary providers are not primary writers.** Codex/OpenCode lanes do not gain primary-checkout authority from routing or telemetry.
6. **Auto-handoff stays off** until representative real-task A/B evidence demonstrates stable benefit without duplicate work or state loss.
7. **Automatic global server-first stays off** until representative compute-placement evidence supports promotion.
8. **No fabricated observability.** Unknown quota, billing, ChatGPT context percentage or host state stays unknown.

## Immediate hardening and acceptance priorities

### P1 — exact-source activation and release boundaries

- Keep source proof, controlled activation, live canary and packaged/released claims separate.
- Verify exact running revision/process identity after controlled activation when current Recovery/Coding MCP/Electron changes require live proof.
- The isolated packaged-Windows Recovery Host/Supervisor lane is covered by `npm run test:recovery:packaged`; before calling a release complete, still prove any required installed Windows logon/session behavior and production-only fault scenarios that cannot safely be represented in isolation.
- Keep restart/activation fail-closed around active commands, background work, provider/agent lanes and EOCL acceptance.

### P2 — representative routing economics

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

## Operational blocker outside P3 semantics

A raw `ExceptionGroup: unhandled errors in a TaskGroup` is currently being returned by the ChatWeb Coding MCP connector before normal typed tool-error handling can be observed. Current source already contains an ExceptionGroup normalization boundary, so this is treated as a runtime/activation/transport incident until exact live process identity and the child exception are observed. It does **not** reopen accepted P3 compute-placement semantics, but it must be resolved before claiming a new live activation/release acceptance.

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

A semantic engineering item is complete when its relevant source contract, focused/affected-boundary proof and EOCL final acceptance are satisfied. Live activation, packaging/release, and representative efficacy are separate gates and must be reported separately rather than being used to reopen an already accepted implementation wave. Tool count, raw test count, LOC or model-call count are not completion metrics by themselves.
