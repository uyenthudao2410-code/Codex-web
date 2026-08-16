# Current Project State — Tools-Codex-web

> **Status date:** 2026-08-16
> **Desktop package:** `web-mcp-assistant 0.3.4`
> **Purpose:** canonical operational snapshot for the current repository. This is not a release note and does not imply that every dirty-worktree change has been packaged or deployed.

## 1. Source of truth and document precedence

When repository documents disagree, use this order:

1. **Current implementation + focused tests + live runtime contract** for the exact checkout being operated.
2. **This file (`docs/CURRENT_STATE.md`)** for the current product boundary and operating policy.
3. `README.md`, `docs/ARCHITECTURE.md`, `docs/RECOVERY_HOST.md`, `docs/TESTING.md`, `docs/ROADMAP.md`, `docs/RELEASE_CHECKLIST.md`, and `SECURITY.md` for maintained product guidance.
4. `docs/MODEL_EXECUTION.md` and `docs/agent/*` for the WebCodex core/subsystem they explicitly describe.
5. Dated files under `docs/research/*` as historical evidence, plans, benchmarks, and decision snapshots. They do **not** override later source or this current-state document.

A source implementation can be newer than the process currently running. For Electron, Recovery Host, Coding Tools MCP, and other supervised components, distinguish **source present**, **focused proof passed**, **controlled activation completed**, and **packaged/released**.

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
- OpenCode automatic routing remains off/evidence-gated.

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
- do not promote routing from small or synthetic samples;
- host-visible latency claims require an explicit host observation bound to the exact EOCL run/wave, not timestamp proximity.

The current host-observation path uses content-free identities (`turn_id`, `trace_id`, `span_id`) and explicit run binding; prompt/response text is not copied into the correlation record.

## 6. Recovery architecture

Independent recovery is no longer only a roadmap concept. The current source contains:

- a headless Recovery Host that owns primary Runtime/Tunnel/Execution-Hub lifecycle;
- a Windows user-session Recovery Supervisor that resurrects the Recovery Host under bounded, fail-closed rules;
- a separate Recovery MCP process and, when configured, a separate Recovery Tunnel;
- `recovery_plane_mode=independent_mcp_tunnel_v1` state;
- bounded `recovery_status` / confirmed `repair_primary_runtime` behavior rather than arbitrary remote shell/process control;
- controlled component activation and accepted-code activation gates.

The Recovery Tunnel must use a distinct tunnel identity from the primary Coding Tunnel. If a second tunnel resource is not configured, the independent local Recovery MCP may still exist while remote Recovery Tunnel status remains `not_configured`.

Implementation in source is not the same as a packaged/live proof. Recovery changes still require the relevant process-boundary, activation, packaged-Windows/login, and fault-matrix acceptance appropriate to the change.

## 7. Semantic localization and LSP resource policy

Coding Tools MCP uses semantic-first localization when the native WebCodex LSP provider is available and falls back to bounded text search per query when semantic localization is unavailable, denied by resource admission, or cannot handle a query.

The current worktree also contains LSP process telemetry/resource-governance work: process instance identity, PID/start identity, current and peak working set, pending-request state, memory-pressure classification, restart/drain counters, bounded idle reaping, and soft/hard pressure behavior. Pressure policy is internal and testable; it must not be documented as one universal production memory number derived from a historical sample.

Until the exact change set has final acceptance and, where required, controlled activation/package validation, describe this as **implemented in the current worktree**, not automatically as a released feature.

## 8. Validation and release boundary

For ordinary changes, validate only the behavior changed. The current top-level entry points are:

```text
npm test
npm run test:mcp
npm run test:all
npm run test:recovery:e2e
npm run canary:opencode-flash:preflight
npm run dist
npm run dist:dir
```

The paid/real provider canary `npm run canary:opencode-flash` may create external provider cost and must run only with explicit authorization for that cost. Its `:preflight` variant performs readiness validation without provider dispatch.

Runtime-affecting source changes need a separate activation/instance check after source tests. A release claim needs source proof, required live/process proof, exact accepted fingerprint, packaging checks, and rollback guidance appropriate to the component.

## 9. Known evidence gates that remain intentional

The following are deliberate evidence/authority gates, not documentation bugs:

- automatic non-deterministic routing: **OFF / deterministic fail-closed** pending representative accepted paired evidence;
- auto-handoff: **OFF** pending more real A/B evidence;
- paid Flash terminal reproduction: **requires explicit external-cost authorization**;
- provider/model write authority over the primary checkout: **not granted by telemetry or routing alone**;
- ChatGPT context-pressure percentage: **unknown unless the host exposes a real source**; do not fabricate one.

## 10. Historical WebCodex material

WebCodex core documents, Rust crates, server/runner deployment material, and dated research remain useful and should not be deleted merely because the desktop product has moved further. Their scope must be explicit. When a historical plan says something is future work but current source now implements it, preserve the historical record and update this current-state document or the maintained product guide instead of rewriting chronology.
