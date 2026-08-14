# Orchestration Wave 3

- Run: `0fa5f45514794455a4c744805629e555`
- Wave: `d0e16aa45d7c448a88427fdf2111f8ee`
- Objective: Implement the production-safe remaining portion of the 9router-inspired upgrade on the current Tools-Codex-web HEAD, using the existing backend/read models rather than duplicating them. Scope is renderer/operator UX plus focused tests only. Requirements: 1) Add a top-level `Traffic & Usage` page to the Electron Control Center navigation. It must consume the existing `api.orchestration()` + `api.performanceTrace()` data and existing `provider_traffic`, delegation economics, usage/flight-recorder/cooldown state; do not add a public MCP tool or new remote unauthenticated endpoint. Show operator-useful KPIs and route/provider rows with provenance labels (provider-reported/measured/estimated/unknown), active/queued/cooldown/limits and recent bounded request/usage evidence. Unknown quota must remain UNKNOWN, never fabricated. 2) Upgrade both existing 9-node Live Execution Fabric SVGs without introducing React/React Flow: replace simple straight `<line>` active animation with semantic SVG `<path>` routing plus a restrained halo/core/2-3 directional particle effect created only while evidence says an edge is active. Preserve current node layout/IDs where practical. Direction/state must be evidence-driven: frontend connectivity alone is not model activity; compute dispatch can animate hub->lane only for active delegation; explicit streaming/responding can reverse lane->hub; write lease can animate hub->writer; PROVING can project proof flow writer->hub; waiting/blocked/cooldown remain distinct and non-electric. 3) Preserve `prefers-reduced-motion`: no continuous particle/filter motion under reduced motion or hidden document, and remove/stop particle animation when edge is no longer active. Avoid persistent hidden animations. 4) Extend `control-center.js` polling to the Traffic page but keep visibility gating. Do not change provider dispatch, automatic route selection, traffic admission enforcement, EOCL/controller/write-lease semantics, tool schemas, Smart-v3 contract, restart behavior, or Codex bridge behavior. 5) Keep Command Center usable; do not move/remove existing IDs required by current bindings unless tests are updated coherently. 6) Add/adjust focused Node tests so they assert the Traffic & Usage page exists, uses existing read APIs/provider_traffic, preserves UNKNOWN semantics/reduced motion, and the router uses SVG path/particle semantics instead of only dashed lines. 7) Preserve all unrelated source/runtime files and do not reset/clean `.coding-tools/*`. Do not restart services, call paid providers, commit, push, or deploy. The exact Smart-v3 tool contract fingerprint must remain 4283e098c315d015c457ce2ab781257491ef70607c6c577f7699969fb8c3f754 with tool_count=8.
- Mode: `mcp_only`
- Base HEAD: `84775ab9a610de90704e00d5b89f5b2865332f7e`
- Worktree fingerprint: `c65410e0c02415fc90e206f9e5945670bde1bcf8e83242fee258e81866d2e8ae`
- Contract fingerprint: `4283e098c315d015c457ce2ab781257491ef70607c6c577f7699969fb8c3f754`
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 2953 | 2026-08-14T17:04:36.905Z | wave_replanned |  | PREFLIGHT | reason=The deterministic Wave 2 patch was rejected atomically before mutation because one control-center.js hunk had ambiguous context. This wave keeps the same safe renderer-only design but materially changes the patch strategy: symbol-anchored, larger unique context blocks are used for control-center.js; no model candidate or backend change is introduced. |
| 2954 | 2026-08-14T17:04:37.101Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 2955 | 2026-08-14T17:04:37.232Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 2956 | 2026-08-14T17:04:37.352Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 2957 | 2026-08-14T17:04:37.466Z | state_transition | READY | ROUTED | reason=route_selected |
| 2958 | 2026-08-14T17:04:37.873Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=191dae41b1624fff8f04f59a1672157e |
| 2959 | 2026-08-14T17:04:38.014Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 2960 | 2026-08-14T17:04:38.335Z | failure_observed | EXECUTING | EXECUTING | failure_class=PATCH_CONTEXT_NOT_FOUND |
| 2961 | 2026-08-14T17:04:38.540Z | write_lease_revoked | EXECUTING | EXECUTING | reason=state_transition:replan; owner=MCP; lease_id=191dae41b1624fff8f04f59a1672157e |
| 2962 | 2026-08-14T17:04:38.656Z | state_transition | EXECUTING | REPLAN | reason=PATCH_CONTEXT_NOT_FOUND; failure_class=PATCH_CONTEXT_NOT_FOUND |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| - | - | - | - | - | - |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `47`
- Chain head: `16342f73102c4ee7f920418fa02958b55707af2995575e5a0c55c3e8c9634ccf`
