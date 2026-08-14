# 260814 — Non-UI Technical Completion Status

**Date:** 2026-08-14  
**Workspace:** `E:\DEV\Tools-Codex-web`  
**Branch / baseline HEAD:** `main` / `bc820986e383391e36d243e0252e23b0aef8d5b8`  
**Status:** **NON-UI SOURCE ROADMAP COMPLETE / FOCUSED PROOFS PASS / LIVE RELOAD + ACCEPTANCE EVIDENCE PENDING**  
**Public MCP contract:** unchanged: `smart-v3`, 8 top-level tools.

This document is the authoritative delta after the earlier Execution Hub and multi-provider design/status snapshots. The older documents remain useful as historical implementation records, but statements that P-MP1/P-MP2/P-MP3 are future work are superseded by this status.

---

## 1. Source roadmap completed

### P0 — Measurement Truth: COMPLETE

Implemented and focused-proven:

- exact model-facing `model_visible_bytes` via PerformanceTrace v4;
- canonical provider `UsageEvent` schema with source provenance;
- measured vs unobserved semantics instead of fake zero values;
- input/cached/uncached/output/reasoning/cache-read/cache-write usage counters;
- provider-reported cost identity;
- queue/provider/total timing fields with explicit unknown/unobserved state;
- typed provider error class without raw provider error text;
- idempotent usage-event persistence by `usage_id`;
- recent usage projection in the internal orchestration snapshot.

Accepted EOCL run: `ff4a12a96ce549d4871195fc9d77428f`  
Final proof fingerprint: `06c01612bc4ab94253b3cc9647b44b7bc18735245b00c3dd795b47f1d1eca571`.

### P-MP1 — Exact OpenCode run/model telemetry: COMPLETE

Implemented and focused-proven:

- OpenCode project plugin observes assistant `message.updated` metadata only;
- non-blocking, debounced/coalesced active updates and immediate terminal delivery;
- bounded per-message state;
- exact provider/model/session/message identity;
- measured token/cache/reasoning counters and provider-reported cost;
- Electron loopback gateway keeps the real MCP bearer private;
- strict telemetry schema rejects content fields and unexpected metadata;
- adapter correlation IDs are optional and bounded;
- internal provider telemetry maps to canonical external delegation/evidence.

No prompt, transcript, reasoning text, message parts, tool input/output, file contents, or MCP bearer is intentionally persisted in provider telemetry.

### P-MP2 — OpenCode read-only Provider Adapter: COMPLETE

Implemented and focused-proven:

- exact allowlist: `opencode-go/deepseek-v4-flash` and `opencode-go/deepseek-v4-pro`;
- bounded prompt packet sent over stdin instead of process argv;
- `opencode run --model ... --format json --agent execution-hub-readonly --dir <workspace>` lifecycle;
- highest-priority inline read-only OpenCode permissions: wildcard deny, allow only `read`, `glob`, `grep`, `list`, `lsp`;
- native edit/bash/task/web/custom/MCP side-effect tools remain denied by the adapter policy;
- process-group / Windows Job lifecycle reuse;
- deterministic dispatch identity, dedup/conflict detection, timeout and cancellation;
- bounded output parsing and session correlation;
- fail-closed `side_effect_policy_violation` if a non-safe tool-use event is observed;
- supervisor-only internal `provider_dispatch`, `provider_observe`, `provider_cancel` actions;
- dispatch is bound fail-closed to the current task-projected active wave;
- provider terminal state can project to the ledger without requiring operator polling;
- raw prompt/result text is not stored in durable delegation metadata; only hash/byte/count/timing/error-class/model/correlation metadata is stored;
- late measured terminal telemetry can correlate to the adapter delegation and record canonical usage exactly once.

Accepted EOCL run: `ffad0a34bd9d4980b9c5abeb5d97b848`  
Final proof fingerprint: `8832acc935fd5613d9dad203610fa5935e78750e8e5cee54ab1d4981c0975b97`.

No real Flash/Pro inference was executed solely for implementation proof; adapter tests use a local fake provider process.

### P-MP3 — Shadow provider routing: COMPLETE

Implemented and focused-proven:

- strict bounded task-feature schema;
- deterministic shadow recommendations for MCP / Mini / Luna / Terra / OpenCode Flash / OpenCode Pro / manual controller gate;
- high/critical risk and consequential mutation fail to manual-controller gate;
- every recommendation declares `mode=shadow_only`, `automatic_dispatch=false`, `mutation_allowed=false`;
- deterministic recommendation identity and idempotent audit event;
- internal supervisor-only `shadow_route` action;
- durable `routing_evidence` projection combines shadow recommendations, actual delegations across all run waves, and canonical UsageEvents;
- explicit regression proof confirms shadow routing does **not** modify orchestration state/route, controller lease, write fence, task orchestration projection, or dispatch a provider.

Accepted EOCL run: `dba11cf58e14482bb22b52ae453840fc`  
Final proof fingerprint: `08db762f5462608f86fb50e829047d2ed629de27c9d9b979b9c747e11dc2fbcd`.

---

## 2. Invariants preserved

- `smart-v3` remains an 8-tool public MCP surface; no ninth tool was added for provider routing or telemetry.
- ChatWeb remains the semantic controller/final acceptance authority in the current topology.
- OpenCode remains worker-only; no OpenCode controller promotion was introduced.
- MCP remains the canonical workspace writer/proof authority.
- Provider Adapter is read-only/proposal-oriented and does not create a second write plane.
- Production routing thresholds were not changed by shadow recommendations.
- No automatic fallback ladder was introduced.
- No auto-handoff was enabled.

---

## 3. What remains is live activation or evidence, not missing source architecture

### A. Reload latest source into live processes

The latest Python runtime source must be loaded by a future authorized MCP runtime restart. The latest Electron gateway correlation schema must be loaded by a future authorized Electron main-process reload/restart. An earlier activation probe proved the telemetry route itself was live in the Electron process, but that probe predates the newest optional provider-dispatch/delegation correlation fields.

No restart is performed by this completion wave because service restart requires explicit operational authorization.

### B. Real OpenCode Provider Adapter canary

Run one bounded read-only Flash or Pro dispatch through the real provider path and verify:

```text
Hub provider_dispatch
-> OpenCode read-only adapter
-> exact model/session
-> plugin telemetry
-> Electron gateway
-> canonical delegation
-> UsageEvent
```

This can incur provider cost, so it was not executed solely for proof.

### C. Real Codex Desktop / ChatWeb two-client acceptance

Still requires operational acceptance on the real clients:

- Codex Desktop thin-proxy online against the same Runtime;
- shared task/run/capsule visibility;
- manual ChatWeb -> Desktop controller handoff and fencing verification;
- reconnect/continuity canary;
- controller returned to ChatWeb before final semantic acceptance when required.

### D. Permission-mode cleanup

The current running MCP process was last observed in `trusted` permission mode after earlier diagnostics. Returning it to `safe` should use the supported Settings flow and then a runtime restart; do not manually edit the settings JSON.

### E. P-MP4 cohort collection

The source now contains the required evidence plumbing (`UsageEvent` + `routing_evidence`). The next requirement is real accepted-task data, not another router implementation:

- representative Flash/Pro/Terra/Mini/Luna/Sol cohorts;
- first-pass acceptance;
- total cost per accepted task;
- TTA;
- repair/proof-failure rate;
- critical defects.

The evidence must come from real accepted work; it must not be fabricated from synthetic completion counts.

---

## 4. Intentionally OFF until evidence gates pass

The following remain intentionally disabled and are **not source-completion blockers**:

- auto-handoff;
- bounded automatic provider routing;
- deep automatic routing / automatic Pro/Terra/Sol escalation;
- Traffic Governor / RPM/TPM admission control;
- controller promotion for OpenCode;
- direct OpenCode workspace writes outside MCP.

They should be enabled only after representative cohort/A-B evidence demonstrates that the safety and accepted-result economics gates are satisfied.

---

## 5. Operations performed in this completion pass

```text
Source implementation: YES
Focused deterministic/fake-provider proof: YES
Public MCP tool change: NO
Renderer/UI work: NO
Real provider inference: NO
MCP runtime restart: NO
Electron restart/reload: NO
Permission setting change: NO
Commit: NO
Push: NO
Release/deploy: NO
```

The worktree remains intentionally dirty because it contains the accepted implementation plus unrelated/concurrent user work that must be preserved.
