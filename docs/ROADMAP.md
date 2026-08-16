# Roadmap — Current Desktop Product

This roadmap describes the current **Tools-Codex-web Windows Desktop Execution Hub**, not the historical WebCodex product roadmap. For exact current-state precedence, see [`CURRENT_STATE.md`](CURRENT_STATE.md).

## Current baseline

The maintained product boundary now includes Electron Execution Control Center; one shared Coding Tools MCP Runtime; ChatWeb primary-tunnel access; Codex Desktop thin-proxy access into the same authority; the verified `smart-v3` eight-tool surface; EOCL/controller/write-fencing/proof/handoff/observation/restart controls; Recovery Host + Windows Recovery Supervisor + independent Recovery MCP/Tunnel source implementation; bounded Codex/OpenCode provider lanes; semantic-first localization; and current-worktree LSP process telemetry/resource governance.

## Policy already decided

1. **One Runtime authority.** ChatWeb and Codex Desktop do not run peer primary runtimes over the same workspace/ledger.
2. **Deterministic proof first.** Tests/compiler/tool evidence outrank model debate when they can answer the question.
3. **Automatic routing is evidence-gated.** `execution_route=auto` currently resolves to `deterministic` while representative accepted paired evidence is insufficient.
4. **High-cost routes are explicit.** `sol_max`/`sol_ultra` require acknowledgement.
5. **Secondary providers are not primary writers.** Codex/OpenCode lanes do not gain primary-checkout authority from routing or telemetry.
6. **Auto-handoff stays off** until representative real-task A/B evidence demonstrates stable benefit without duplicate work or state loss.
7. **No fabricated observability.** Unknown quota, billing, ChatGPT context percentage or host state stays unknown.

## Immediate hardening and acceptance priorities

### P1 — exact-source activation and release boundaries

- Keep source proof, controlled activation, live canary and packaged/released claims separate.
- Verify exact running revision/process identity after controlled activation when current Recovery/Coding MCP/Electron changes require live proof.
- Complete relevant packaged-Windows/login and production fault-matrix checks for Recovery before calling that boundary release-complete.
- Keep restart/activation fail-closed around active commands, background work, provider/agent lanes and EOCL acceptance.

### P2 — representative routing economics

- Produce accepted, homogeneous paired cohorts by task class/oracle/environment instead of synthetic no-op volume.
- Compare quality/critical-defect/repair/TTA/cost with explicit sample sizes and provenance.
- Keep automatic non-deterministic routing disabled until the evidence gate is actually satisfied.
- Real paid OpenCode Flash terminal canary requires explicit external-cost authorization; preflight remains the default zero-dispatch check.

### P2 — validate LSP resource hardening

- Finish focused/process-level acceptance of current-worktree LSP process identity, memory-pressure and reaper behavior.
- Confirm soft pressure degrades broad semantic work without killing active requests; hard pressure fails closed before unsafe growth.
- Calibrate policy from representative measurements instead of one historical ~GiB observation.

### P3 — operationalize evidence without inflating architecture

- Continue using `.coding-tools/orchestration/ledger.sqlite3` as canonical causal audit.
- Keep host latency attribution explicitly bound by content-free turn/trace identity.
- Improve summaries only from real measured state; do not add a second truth store.
- Promote optional features only when benchmark/product evidence demonstrates a concrete need.

## Deferred until evidence promotes them

- automatic provider/model routing from small or synthetic samples;
- automatic controller transfer/auto-handoff;
- dual primary Runtime authority;
- broad autonomous provider writes to the primary checkout;
- arbitrary remote process/service management through Recovery;
- fabricated context-pressure percentages;
- large generic fleet/orchestration layers without a second real use case;
- rewriting historical research to pretend it described current source.

## Completion criteria

An item is complete only when the relevant source contract, focused proof, live activation, EOCL final acceptance, packaged/process-boundary acceptance, rollback guidance and representative measurement evidence are satisfied. Tool count, raw test count, LOC or model-call count are not completion metrics by themselves.
