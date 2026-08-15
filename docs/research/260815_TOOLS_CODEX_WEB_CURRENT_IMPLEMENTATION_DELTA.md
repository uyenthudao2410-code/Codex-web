# Tools-Codex-web — Current Implementation Delta

**Observed date:** 2026-08-15  
**Companion audit:** `docs/research/260815_TOOLS_CODEX_WEB_PRACTICAL_FIT_AUDIT_OF_ADVISORY_RECOMMENDATIONS.md`  
**Subsystem role contract:** `docs/RUST_PYTHON_PRODUCT_ROLES.md`  
**Purpose:** current-status delta only. This companion does not rewrite historical audit snapshots. When an older “current status” statement conflicts with this file, use this file for the latest source/worktree status described below.

## Current source baseline

```text
workspace: E:\DEV\Tools-Codex-web
branch:    main
HEAD:      dff81e251836666fc825c40bf86e4167afd29c39
smart-v3:  8 public tools
contract:  8fbee29c8de9788bedb09caf1b2fc4317f26ba7ab85ef35ebc4a7288558940d4
```

The worktree is intentionally dirty with accepted P0/P1/P5/semantic/CI/Code-Mode prerequisite changes, volatile `.coding-tools/*` state, and unrelated/concurrent UI work. No reset/clean/rebase is implied by this delta.

## Source-complete + regression-proven

- Source-fenced continuation is implemented inside the existing `agent_workflow`; no ninth public tool was added.
- Continuation binds source/worktree, scope/options and byte position; stale or mismatched state fails closed. Canonical Base64URL validation rejects equivalent-encoding token tampering.
- Result-tail telemetry records truncation, continuation offered/read/re-read and stale continuation events.
- Required idempotency uses the `task_epoch_v1` current-policy view and has focused fault proof for workflow execution plus `task_control accept/reject`: exact duplicate replay is at-most-once, conflicting key fails closed, and previous-process unknown outcome is not replayed as a fresh side effect.
- Windows exact-source provenance separates `exact_source` from `publishable`; development smoke cannot label itself publishable.
- Product packaging excludes `coding-tools-mcp/benchmarks/reports/**`; source-bundle tests also protect private runtime state.
- PerformanceTrace captures operation-entry/exit wall timestamps while monotonic duration remains authoritative.
- Runtime identity exposes non-secret runtime/process/server identity, Git source identity when available, PerformanceTrace version, Smart-v3 contract identity, semantic status and idempotency policy epoch.
- Stale-orchestration health separates currently unresolved stale active runs from runs reconciled during startup/switch. Reconciliation and read-only health reuse the same live-ownership predicate; ledger history is retained.
- Native semantic activation readiness is self-diagnosing without exposing secrets: status keeps existing reason codes and adds only allowlisted binding state, configuration booleans, safe missing-component names and an allowlisted invalid component name. URL/port, credential path/content, project identifiers, env values and raw errors are not projected.
- Rust/Python product roles are source-grounded in `docs/RUST_PYTHON_PRODUCT_ROLES.md`. All Rust workspace packages remain in the dependency closure of shipped native binaries or the real Linux Server runtime; no package has evidence for blind removal.
- Windows selected Rust CI directly tests `webcodex-workspace`, because it owns a real `cfg(windows)` portable project-root identity used by the authenticated Python <-> Rust semantic bridge. Focused Windows drive and extended-UNC normalization tests exist; the root Server suite remains Linux-only.
- Code Mode now has an **internal, model-hidden host-binding proxy prerequisite** with exactly four read-only operations: `read_text`, `list_files`, `search_text`, and `semantic_search`. The proxy is not a generic Runtime/tool dispatcher and is not a ninth Smart/MCP tool.
- Code Mode binding requests use schema v1 with exact operation/argument allowlists plus hard serialized request/response caps. Paths are restricted to the primary workspace, not `authorized_roots`; absolute, drive, UNC, home, parent traversal, NUL, symlink escape, NTFS ADS/colon syntax and Windows reserved device names fail closed.
- Code Mode semantic matches are revalidated as primary-workspace-relative before return. Provider configuration details are not projected through this binding.
- The Code Mode isolation feasibility audit is now encoded as a fail-closed source-owned readiness contract. The worker backend remains `null`/blocked until one implementation proves every required guarantee; current process-control or write-confinement primitives are explicitly not promoted to a security boundary.

## Verification evidence

Current broad Python MCP regression after the Code Mode binding addition:

```text
Python Coding Tools MCP full pytest            274 passed, 1 skipped, 16 subtests passed
git diff --check                               PASS
```

Focused/adjacent proofs:

```text
CodeModeHostBindingTests                       6/6 PASS
Code Mode isolation-readiness + identity       PASS
workspace_context non-secret identity test     PASS
Code Mode Windows namespace hardening          PASS
NativeSemanticLocalizationTests                PASS (host-dependent symlink test may skip)
cargo check -p webcodex-workspace --tests      PASS on Windows host
Windows provenance/CI contract Node test       PASS
root npm test baseline                         99/99 PASS before latest Python-only Code Mode changes
```

The Code Mode changes do not modify the JavaScript/renderer path or public tool definitions; Smart-v3 remains 8 tools with contract SHA `8fbee29c8de9788bedb09caf1b2fc4317f26ba7ab85ef35ebc4a7288558940d4` in focused proof.

These local proofs do not constitute independent GitHub CI proof.

## Current-policy idempotency activation — PASS

Persisted `task_epoch_v1` snapshot observed during this continuation:

```text
current-policy required calls        41
current-policy required keyed        41
coverage                         100.0%
target                             95.0%
```

Historical cumulative audit view at the same observation point:

```text
historical required calls           121
historical required keyed           102
```

The historical ratio is retained for audit only and is not the current-policy gate. Combined with the duplicate/conflict/unknown-outcome fault suite, the current-policy activation coverage gate is satisfied for the observed sample. Future semantic changes to required operations must declare an appropriate new policy epoch instead of backfilling this one.

## Result-tail continuation — IMPLEMENTED, REPRESENTATIVE ROI STILL UNPROVEN

Persisted counters observed during this continuation:

```text
result-tail samples                   6
truncated calls                       0
continuation offered                  0
continuation reads                    0
continuation re-reads                 0
stale continuation                    0
```

Instrumentation is active, but the observed workload still contains no real truncation/continuation use. Do not manufacture a large-diff corpus merely to make counters nonzero. Keep the implementation and wait for representative large-result tasks.

## Proof-cache opportunity — HOLD

Persisted opportunity counters observed during this continuation:

```text
proof-cache eligible                 93
observed hits                         1
observed misses                      93
saved ms                            999
miss reason: cold                    41
miss reason: input fingerprint       52
```

One observed hit / 999 ms remains insufficient justification for broader cache machinery or weaker fingerprints. Exact proof identity remains a hard invariant; performance promotion stays **HOLD**.

## Rust / Python product-role decision

The role audit used Cargo metadata, current release scripts, npm package contract, Electron runtime startup and CI configuration.

```text
Desktop mutation authority       Electron + one Python Coding Tools MCP runtime
Rust Server / ToolRuntime        real Linux/server product + optional native capability provider
npm native contract              webcodex + webcodex-server + webcodex-runner
canonical Linux Rust proof       full workspace remains justified
Windows Rust proof               selected packages, not full Server workspace
```

Direct Windows package tests:

```text
webcodex-agent-config
webcodex-process
webcodex-persistent-shell
webcodex-workspace
webcodex-cli
webcodex-runner
```

`webcodex-admin`, `webcodex-core`, and `webcodex-sandbox` continue to compile transitively on Windows. The current audit found no separate Windows implementation requiring a direct package-test gate: `core` Windows-form checks are platform-independent string logic, `sandbox` has Linux Landlock code, and `admin` has no Windows branch observed. Revisit the selected list when evidence changes, not by convention.

## Operational stale-state — CURRENTLY GREEN

During this continuation, obsolete historical authorities were audited and terminalized without deleting ledger history, including a superseded Code Mode REPLAN lineage and older prepare-only runtime-schema diagnostics. Latest verified live recovery projection before this document update:

```text
stale_orchestration_runs             0
unresolved_stale_orchestration_runs  0
reconciled_stale_orchestration_runs  2
```

No live write lease/lane/proof authority was discarded. Terminalization used explicit `ABORTED` history for superseded runs.

## Exact-HEAD CI truth — BLOCKED EXTERNALLY

GitHub Actions run `31852696347` is bound to HEAD `dff81e251836666fc825c40bf86e4167afd29c39`, but it is **not green CI proof**.

```text
Linux job:   94931355344
Windows job: 94931355365
runner_id:   0
steps:       []
classification: pre-run external billing/account gate
```

The jobs did not start because the account/spending prerequisite blocked runner allocation. With no runner and no test step, this is an external CI/account blocker, not evidence of a source regression. Local PASS is not a substitute for independent exact-SHA CI when release policy requires it.

## Intentionally open gates

### Native semantic live activation — BLOCKED BY REAL PREREQUISITE

The Python <-> Rust semantic boundary is source-ready, authenticated/project-scoped, read-only, bounded and fail-closed in focused tests. The live provider remains unavailable with the existing reason:

```text
NATIVE_LSP_BINDING_NOT_CONFIGURED
```

Do not infer or fabricate endpoint URL, project credential, grant or token. Activate only against a real Rust Connector instance bound to the correct project/trust boundary with explicit configuration. The sanitized binding diagnostics are source-complete; an already-running Python process must load that source before those added details can be claimed live.

### Code Mode worker isolation — HOLD / FAIL-CLOSED

The host-binding side is source-ready and fail-closed. The source-owned isolation readiness contract now reports:

```text
host binding proxy      ready
binding schema          1
operations              read_text, list_files, search_text, semantic_search
worker status           blocked
worker reason           verified_binding_only_backend_unavailable
worker backend          null
Code Mode enabled       false
```

A qualifying backend must prove all five guarantees:

```text
no_direct_filesystem
no_network
no_inherited_environment_secrets
no_unrestricted_subprocess
bounded_framed_host_binding_only_ipc
```

Repository evidence currently contains only nonqualifying controls:

```text
Windows Job Object      process_lifecycle_only
Linux Landlock          write_confinement_only
embedded capability runtime / WASM sandbox    not configured
```

Windows Job Objects provide process-tree ownership/kill-on-close, not a restricted token or AppContainer capability boundary. The current Linux Landlock policy intentionally permits reads, environment and network while restricting writes. The repository has no seccomp/namespaces isolation layer and no Wasmtime/Wasmer execution runtime. Therefore no existing primitive is sufficient for arbitrary generated-code execution.

Do not enable Code Mode using Python `exec/eval`, Node VM/worker threads, the current Rust sandbox, Job Objects alone, or an unrestricted subprocess. Promotion requires a real isolated worker that receives only the serialized host-binding protocol and proves every guarantee above with attack-oriented tests.

### Call Hierarchy — HOLD

Do not implement/promote Call Hierarchy until the live semantic path has representative nonzero `semantic_attempted` / `semantic_handled` evidence and qualified cross-file workloads demonstrate accepted-work ROI.

### Routing-v2 / Terra — HOLD / SHADOW / EXPLICIT

Do not promote from benchmark fixtures, synthetic cohorts or tiny samples. Automatic dispatch/activation stays off until representative paired accepted-task cohorts satisfy promotion readiness.

## Operations performed in this continuation

No commit, push, release, deploy, tag, external-provider paid call, or ChatGPT-initiated runtime restart was performed while producing this current-status delta.
