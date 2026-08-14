# 260814 — Non-UI Technical Completion Status

**Date:** 2026-08-14  
**Current workspace:** `E:\Github\Tools-Codex-web`  
**Branch:** `main`  
**Status:** **NON-UI + OPERATOR OBSERVABILITY SOURCE CLOSURE COMPLETE / TRAFFIC GOVERNOR + FLIGHT RECORDER + RECOVERY UI PASS / POST-FIX FLASH TERMINAL REPROOF + COHORT EVIDENCE PENDING**
**Public MCP contract:** `smart-v3`, 8 top-level tools; PerformanceTrace v5 source, controlled live activation pending.

This document is the authoritative current-state delta for the Execution Hub / multi-provider non-UI work. Older implementation and architecture documents remain historical references; statements in them that P-MP1/P-MP2/P-MP3, Electron activation, permission cleanup, or two-client handoff are still pending are superseded by this status.

---

## 1. Source roadmap status

### P0 — Measurement Truth: COMPLETE

Implemented and focused-proven:

- exact model-facing `model_visible_bytes` via PerformanceTrace v4;
- canonical provider `UsageEvent` with source/provenance and measured-vs-unobserved semantics;
- input/cached/uncached/output/reasoning/cache read/write counters;
- provider-reported cost identity;
- queue/provider/total timing with explicit unknown/unobserved state;
- typed provider error class without raw provider error text;
- idempotent usage persistence;
- internal usage projection for routing/economics evidence.

### P-MP1 — Exact OpenCode run/model telemetry: COMPLETE

Implemented and focused-proven:

- assistant `message.updated` metadata observation only;
- bounded non-blocking debounce/coalescing and terminal delivery;
- exact provider/model/session/message identity;
- measured token/cache/reasoning/cost telemetry;
- strict Electron loopback gateway with MCP bearer isolation;
- bounded adapter correlation IDs;
- durable external-delegation and UsageEvent projection.

No prompt, transcript, reasoning text, message parts, tool input/output, file contents, or MCP bearer is intentionally persisted by provider telemetry.

### P-MP2 — OpenCode read-only Provider Adapter: COMPLETE

Implemented and focused-proven:

- exact model allowlist: `opencode-go/deepseek-v4-flash` and `opencode-go/deepseek-v4-pro`;
- prompt over stdin rather than argv;
- `execution-hub-readonly` OpenCode agent;
- wildcard deny with only read/glob/grep/list/lsp allowed;
- native edit/bash/task/web/custom/MCP side-effect tools denied by adapter policy;
- process-group / Windows Job lifecycle;
- deterministic dispatch identity, dedup/conflict detection, timeout/cancel;
- supervisor-only internal `provider_dispatch`, `provider_observe`, `provider_cancel`;
- run/wave-bound dispatch context;
- terminal synchronization into the canonical delegation ledger;
- raw prompt/result text excluded from durable delegation metadata;
- measured economics and canonical UsageEvent correlation.

### P-MP3 — Shadow provider routing: COMPLETE

Implemented and focused-proven:

- bounded task-feature schema;
- deterministic recommendations for MCP / Mini / Luna / Terra / OpenCode Flash / OpenCode Pro / manual controller gate;
- `mode=shadow_only`, `automatic_dispatch=false`, `mutation_allowed=false`;
- idempotent routing evidence;
- supervisor-only internal `shadow_route`;
- durable comparison of recommendation vs actual delegation/UsageEvent;
- regression proof that shadow routing does not change execution route, orchestration state, controller lease, write fence, task projection, or dispatch a provider.

---

## 2. Paid Flash live canary and lifecycle correction

One authorized real OpenCode Flash canary was executed through the Hub read-only Provider Adapter.

Observed measured evidence from that single paid call:

```text
model:          opencode-go/deepseek-v4-flash
input_tokens:   4753
output_tokens:  56
reasoning:      0
provider_time:  8418 ms
provider_cost:  0.00034055
```

The call proved the real credential, model selection, provider transport, telemetry gateway, correlation, measured economics and UsageEvent plumbing.

It also exposed a real lifecycle defect: an assistant message with `finish=tool-calls` was being treated as terminal for the whole provider dispatch even though OpenCode continued to the next assistant step. The provider telemetry had already recorded measured economics, while the CLI process remained alive until the adapter timeout window.

The source has been corrected and focused-proven without a second paid inference:

- correlated `finish=tool-calls` is intermediate, not delegation terminal;
- measured economics aggregate idempotently per `message_id` and across multiple assistant messages;
- duplicate streaming updates cannot inflate token/cost totals;
- canonical UsageEvent closes only at true delegation terminal or adapter terminal failure;
- terminal delegation metadata is frozen against conflicting later status updates;
- bounded adapter lifecycle evidence records event counts / last step finish / last tool state;
- the observed lifecycle failure is typed as `provider_cli_idle_timeout_after_tool_calls`.

Final focused lifecycle/economics verification passed with Node telemetry/canary tests, Python UsageEvent/ledger/Provider Adapter/Execution Hub tests, syntax checks, source-root cleanliness and `git diff --check`.

EOCL final fix run: `6d2f15fe1c6d46708ed75551fa13ffb4`  
Final accepted wave: `cc8e77a60c12468794bc7937e4266f23`  
State: `CHECKPOINTED`, audit integrity PASS.

A second paid Flash call has **not** been executed after the lifecycle correction. Therefore the remaining provider proof is a post-fix live terminal repro, not a missing source feature.

---

## 3. Live activation / operational acceptance

### Electron gateway: PASS

Current activation probe returns the expected live route behavior:

```text
route_loaded = true
HTTP status  = 403 for the deliberately non-OpenCode telemetry canary
```

This proves the Electron telemetry gateway route is loaded while the canary remains non-forwarding by design.

### MCP runtime contract: PASS

Current runtime reports:

- `smart-v3`;
- 8 public tools;
- PerformanceTrace v4;
- no additional top-level provider-routing tool.

### Permission mode: PASS / SAFE

The live MCP process is running in `safe` permission mode. The earlier diagnostic `trusted` state has been cleaned up through the supported application settings/runtime lifecycle; manual settings-file editing is not required.

### Codex Desktop single-runtime topology: PASS for proxy/config path

On the current machine the Codex MCP entry was corrected from a direct full runtime to the Execution Hub thin proxy. Live process evidence observed the intended topology:

```text
ChatGPT.exe -> codex.exe -> python.exe hub_proxy_stdio
```

and no direct `coding_tools_mcp --stdio` runtime was observed for Codex Desktop.

### ChatWeb ⇄ Codex Desktop controller acceptance: PASS

Live two-client acceptance completed on the shared Hub transport:

- ChatWeb and Codex Desktop visible as separate Hub clients;
- shared run/capsule continuity verified through the thin proxy;
- manual `ChatWeb -> Codex Desktop` transfer succeeded;
- fencing token advanced `1 -> 2`;
- capsule remained readable through the Desktop proxy while Desktop held controller authority;
- manual `Codex Desktop -> ChatWeb` transfer succeeded;
- fencing advanced `2 -> 3`;
- audit integrity remained PASS;
- controller was returned to ChatWeb after the canary.

The native Codex host was also observed spawning the thin proxy. Its idle process lifetime is a frontend lifecycle concern; it does not reintroduce a second canonical runtime.

---

## 4. Invariants preserved

- One Electron-owned Coding Tools Runtime remains the execution truth for the workspace.
- `smart-v3` remains an 8-tool public MCP surface.
- ChatWeb remains the semantic controller/final acceptance authority in the default topology.
- Codex Desktop can receive explicit fenced controller handoff but does not become a second runtime/writer.
- OpenCode remains worker-only.
- MCP remains the canonical workspace writer/proof authority.
- Provider Adapter remains read-only/proposal-oriented and cannot create a second mutation plane.
- Real MCP bearer remains isolated to the Electron/runtime secret boundary.
- No fixed provider fallback ladder has been introduced.
- No automatic controller handoff is enabled.
- No production routing threshold has been auto-promoted from limited evidence.

---

## 5. Post-audit Traffic & Operator Observability closure

The post-audit implementation closed the remaining actionable source gaps that did not require fabricated provider limits, paid inference, host-only ChatGPT telemetry, or representative production cohorts.

### A. Provider Traffic & Usage Control Plane: COMPLETE

Implemented and full-suite-proven:

- runtime-scoped `ProviderTrafficGovernor` for already-authorized manual provider dispatch;
- explicit configured limits only: `rpm`, `tpm`, `concurrency`;
- configuration source: `CODING_TOOLS_MCP_PROVIDER_LIMITS_JSON`;
- absent provider limits remain `observe_only` / unknown rather than becoming invented quota;
- TPM admission requires an explicit request `token_budget`; prompt size or provider usage is not guessed into a token limit;
- invalid explicit limit configuration fails closed;
- deterministic request reservation/dedup, rolling 60-second RPM/TPM accounting, active concurrency release on terminal provider state, and reservation abort on provider-start failure;
- retry-after is emitted only for a real RPM/TPM denial, not merely because traffic exists;
- automatic provider routing remains explicitly `enabled=false`, `mode=evidence_gated`.

The governor therefore protects manual provider dispatch without silently promoting Flash/Pro/Mini/Luna/Terra/Sol into an automatic routing policy.

### B. Provider capacity/cooldown projection: COMPLETE

Execution Hub now exposes bounded local capacity evidence without starting a new provider turn:

- OpenCode active-request count, retained-dispatch count/limit, allowlisted models and read-only enforcement state;
- Codex App Server model capacity cooldown rows with retry-after and observed failure count;
- provider quota that is not configured or not reported remains unknown.

### C. Bounded history / flight recorder / phase timing: COMPLETE

No second orchestration database was added. Existing durable EOCL ledger evidence is projected through bounded read models:

- recent run history is capped and exposes only run identity, lifecycle status and timestamps in the Hub UI projection;
- flight-recorder event views reuse the existing sanitized ledger payloads and stable sequence cursor;
- default/tail and `after_seq` delta reads are bounded to at most 100 events per call;
- oversized projected event payloads are replaced by bounded byte count + SHA-256 identity;
- phase durations are derived only from recorded EOCL transition timestamps and terminal `finished_at`;
- the final active phase has `duration_ms=null` rather than using current wall time as fabricated measurement.

The current renderer still polls the authenticated Hub snapshot. A dedicated push/event-stream transport was **not** added merely to satisfy the older 9router proposal; the durable delta primitive now exists for a later transport if operational evidence justifies it.

### D. Local recovery and Control Center observability: COMPLETE for current milestone

Electron supervisor state now projects its already-existing local recovery truth:

- recovering flag;
- consecutive failure count and typed failure kind;
- recovery-attempt count and next recovery time;
- recovery-blocked state;
- last start failure;
- deferred-recovery count.

Control Center / Live Routing now renders:

- provider policy/admission mode and capacity/cooldown evidence;
- automatic-routing gate state;
- bounded flight-recorder events and recent run history;
- EOCL phase timing;
- local runtime/tunnel recovery state;
- explicit context-pressure provenance.

The UI continues to separate OpenCode frontend connectivity from actual DeepSeek/model activity and does not fabricate streaming, provider billing, quota, or context percentage. Existing reduced-motion behavior remains intact.

### E. Context-pressure and remote-monitoring boundary

ChatGPT conversation context pressure is still returned as:

```text
status = unknown
source = host_not_exposed
```

The UI states this explicitly and does **not** estimate a percentage. A separate authenticated remote-status channel for phones was not added in this closure; current recovery/health evidence remains local to the Electron/Hub control plane. Building a remote channel is a separate security/deployment feature, not a reason to invent host telemetry or expose an unauthenticated endpoint.

### F. Boundary verification

Canonical current-worktree verification after the implementation:

```text
npm test:             61 / 61 Node tests PASS
npm run test:mcp:    228 / 228 Python MCP tests PASS
total:               289 / 289 tests PASS
git diff --check:    PASS
```

Additional focused backend proof for provider traffic / Hub / ledger / Codex / OpenCode / UsageEvent passed `43/43` before the full-suite gate.

No paid provider call, runtime restart, connector refresh, commit, push, release, or deployment was performed for this post-audit source closure.

---

## 6. Remaining work

### A. Post-fix real Flash terminal repro

The highest-value remaining live proof is one bounded paid Flash run after the `tool-calls` lifecycle correction, verifying:

```text
provider_dispatch
-> Flash
-> intermediate tool-calls/message telemetry if present
-> true terminal delegation
-> aggregated exact economics
-> one canonical terminal UsageEvent
```

This is an external-cost acceptance proof and requires explicit authorization for a new paid call. It is not a source blocker.

### B. P-MP4 cohort collection

Representative accepted-task data is still required before automatic routing promotion:

- Flash / Pro / Terra / Mini / Luna / Sol representative cohorts;
- first-pass acceptance rate;
- total cost per accepted task;
- TTA / median / P90;
- repair and proof-failure rate;
- critical defect count;
- cold/warm cache conditions where material.

Evidence must come from real accepted work and must not be fabricated from synthetic counts.

### C. Evidence-gated routing phases remain OFF

The following remain intentionally disabled until cohort thresholds are satisfied:

- bounded automatic Flash/Mini routing;
- automatic Pro/Terra/Sol escalation;
- deep auto-routing;
- auto-handoff;
- automatic-router consumption of configured provider limits / governor state;
- OpenCode controller promotion;
- direct OpenCode workspace writes outside MCP.

These are future optimization/evidence phases, not missing implementation required for the current non-UI source milestone.

### D. External/host evidence remains unavailable by design

- real ChatGPT context-pressure percentage remains unavailable because the host does not expose it;
- a remote authenticated phone-monitoring channel is not part of the current local execution milestone;
- push transport for the existing bounded Hub delta/flight-recorder evidence remains an optional operational optimization.

### E. Proposal-only abstractions are not current blockers

The research methodology proposed broader names/contracts such as generic `CompositeReadPlan`, generic `ExecutionArtifactRef`, full Python/Rust ToolSpec convergence and semantic parallel-planner metadata. The current source already has bounded output references, durable jobs/sessions, semantic navigation, proof fingerprints and structured execution primitives. Those broader abstractions remain optional benchmark-driven refactors; they were not added merely to satisfy proposal names because doing so would expand framework surface without a proven current blocker.

---

## 7. Current completion assessment

```text
P0 Measurement Truth:                    COMPLETE
P-MP1 exact OpenCode telemetry:          COMPLETE
P-MP2 read-only Provider Adapter:        COMPLETE
P-MP3 shadow routing:                    COMPLETE
Electron telemetry gateway live:         PASS
MCP Smart-v3 / 8 tools / PT v5 source:   PASS
Permission mode safe:                    PASS
Codex Desktop thin-proxy topology:       PASS
ChatWeb <-> Desktop fenced handoff:       PASS
Real Flash provider/economics evidence:  PASS (one call)
Provider Traffic Governor/manual gate:   COMPLETE
Provider capacity/cooldown projection:   COMPLETE
Hub flight recorder + sanitized history: COMPLETE
EOCL timestamp phase timing:             COMPLETE
Local recovery/operator UI:              COMPLETE
Full boundary suite:                     PASS (93 Node + 240 Python; +3 subtests)
Live PerformanceTrace v5 activation:     PENDING controlled restart
Context pressure:                         UNKNOWN / host_not_exposed by design
Post-fix Flash terminal repro:            PENDING external-cost proof
P-MP4 representative cohorts:            PENDING evidence collection
Bounded/deep auto-routing:                OFF by design
Auto-handoff:                             OFF by design
UI traffic/history/recovery continuation: COMPLETE for current milestone
```

There is no known implementation blocker for the current non-UI + operator-observability milestone. Remaining work is external/evidence-gated or optional optimization: representative accepted cohorts before production routing promotion, one explicitly authorized post-fix paid Flash terminal proof if full provider live closure is required, host context telemetry if the product ever exposes it, and separately reviewed remote/push transports if they become operational priorities.

---

## 8. PerformanceTrace v5 / idempotency / attribution completion delta

This section supersedes only the current-state parts above that still refer to PerformanceTrace v4 or the older boundary-test count. Historical chronology and prior live evidence remain unchanged.

### Source closure completed

- PerformanceTrace source schema is now `v5` with separate `required / optional / none` idempotency policy and `explicit / derived / none` key provenance. The broad v4 eligible denominator is retained for historical comparison only; v5 production evidence uses required-key coverage.
- Deterministic auto-keys are limited to durable identities currently proven safe: `agent_workflow phase=execute` and `task_control accept/reject`. Accept/reject keys include caller identity plus controller fencing epoch; commands, stdin, restart, handoff-record and document mutations are not silently auto-deduplicated.
- A bounded structured error taxonomy is recorded from code/category, not message text. Measured timing now accepts the broader methodology phase vocabulary without inventing missing values.
- EOCL terminal evidence now exposes `tta_ms`, `observed_ms`, `unattributed_ms`, `tta_coverage`, a `0.90` floor and `0.95` target. EOCL `EXECUTING` remains `execution_window_ms`, not model latency.
- Provider `queue_ms / provider_ms / total_ms` stay separate overlapping delegation evidence and are never added to EOCL observed time.
- The Electron Hub proxy now keeps a bounded 256-sample resident loopback RTT window for MCP, heartbeat and telemetry and reports `n / p50 / p90 / p99 / max`, status classes and failures without retaining request body, headers, bearer/token or transcript content. It is explicitly gateway-to-local-MCP RTT, not provider/model latency.
- Python `ToolSpec` now shares the Rust risk vocabulary (`read_only`, `project_write`, `job_run`, `account_manage`, `unknown`) and publishes ownership: Python owns MCP annotation/projection, Rust `ToolMetadata/ToolRisk` owns native execution-risk semantics, and EOCL + permission + write lease remain the authority boundary. Smart-v3 stays exactly **8 public tools**; mixed `task_control` deliberately remains `unknown`.
- Runtime activation snapshot schema is now `v3`, separating legacy-v4 coverage from v5 required coverage and reporting optional/auto-key counts, error `UNKNOWN` share and measured phase-timing availability. v5 counters are a post-activation epoch and are not backfilled from historical v4 events.

### Regression evidence

The first complete Python run after auto-key introduction found one real multi-client regression (`1 failed, 239 passed`): a fenced ChatWeb `accept` could claim the same derived key later needed by the transferred Codex Desktop controller. The derivation was corrected to scope `accept/reject` by `client_id + fencing_token`; the direct fault oracle then passed `10/10`, followed by the full boundary suites.

Final current-worktree verification:

```text
Python MCP:        240 / 240 PASS (+3 subtests PASS)
Node / Electron:    93 / 93 PASS
top-level total:   333 / 333 PASS
git diff --check:  PASS
source-root check: PASS
```

No test or security/authority guard was disabled or weakened to obtain this result.

### Live activation boundary

No controlled Runtime/Electron restart was performed for this v5 source closure. The currently running process and existing `.coding-tools/performance.json` therefore remain pre-v5/legacy evidence until activation. The historical live value `304 / 1291 = 23.5476%` is the old broad legacy denominator and is **not** the new required-v5 coverage result.

A clean post-activation v5 epoch is required before claiming the methodology `>=95%` required-idempotency target. Resident gateway percentiles likewise become live operational evidence only after Electron loads the new source. No synthetic backfill is allowed.

Operations deliberately not performed in this delta:

```text
runtime/Electron restart: no
paid provider call:       no
connector refresh:        no
route threshold change:   no
auto-handoff enablement:  no
commit / push / release:  no
deployment:               no
```

The post-fix paid Flash terminal repro and P-MP4 representative accepted cohorts remain pending evidence gates. Routing-v2 automatic dispatch, deep escalation and auto-handoff remain **OFF by design** until those gates are satisfied. `context_pressure` remains `unknown / host_not_exposed`; authenticated remote-phone monitoring and push transport remain separately reviewed optional product/operations work.
