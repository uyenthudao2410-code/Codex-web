# 260814 — Non-UI Technical Completion Status

**Date:** 2026-08-14  
**Current workspace:** `E:\Github\Tools-Codex-web`  
**Branch:** `main`  
**Status:** **NON-UI SOURCE ROADMAP COMPLETE / LIVE HUB + SAFE MODE + TWO-CLIENT HANDOFF PASS / POST-FIX FLASH TERMINAL REPROOF + COHORT EVIDENCE PENDING**  
**Public MCP contract:** `smart-v3`, 8 top-level tools, PerformanceTrace v4.

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

## 5. Remaining work

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
- Traffic Governor / RPM/TPM admission control;
- OpenCode controller promotion;
- direct OpenCode workspace writes outside MCP.

These are future optimization/evidence phases, not missing implementation required for the current non-UI source milestone.

### D. UI remains deferred

No additional UI work is required for this non-UI completion milestone. UI/visual router work can resume separately when prioritized.

---

## 6. Current completion assessment

```text
P0 Measurement Truth:                    COMPLETE
P-MP1 exact OpenCode telemetry:          COMPLETE
P-MP2 read-only Provider Adapter:        COMPLETE
P-MP3 shadow routing:                    COMPLETE
Electron telemetry gateway live:         PASS
MCP Smart-v3 / 8 tools / PT v4:          PASS
Permission mode safe:                    PASS
Codex Desktop thin-proxy topology:       PASS
ChatWeb <-> Desktop fenced handoff:       PASS
Real Flash provider/economics evidence:  PASS (one call)
Post-fix Flash terminal repro:            PENDING external-cost proof
P-MP4 representative cohorts:            PENDING evidence collection
Bounded/deep auto-routing:                OFF by design
Auto-handoff:                             OFF by design
UI continuation:                          DEFERRED
```

The non-UI source architecture is complete. Remaining work is evidence collection and optional production-routing promotion, plus one post-fix paid provider terminal proof if full end-to-end live closure is required.
