# Orchestration Wave 2

- Run: `0fa5f45514794455a4c744805629e555`
- Wave: `efb16aeb0bd94c1a8ab2eebb08d1fb23`
- Objective: Implement the production-safe remaining portion of the 9router-inspired upgrade on the current Tools-Codex-web HEAD, using the existing backend/read models rather than duplicating them. Scope is renderer/operator UX plus focused tests only. Requirements: 1) Add a top-level `Traffic & Usage` page to the Electron Control Center navigation. It must consume the existing `api.orchestration()` + `api.performanceTrace()` data and existing `provider_traffic`, delegation economics, usage/flight-recorder/cooldown state; do not add a public MCP tool or new remote unauthenticated endpoint. Show operator-useful KPIs and route/provider rows with provenance labels (provider-reported/measured/estimated/unknown), active/queued/cooldown/limits and recent bounded request/usage evidence. Unknown quota must remain UNKNOWN, never fabricated. 2) Upgrade both existing 9-node Live Execution Fabric SVGs without introducing React/React Flow: replace simple straight `<line>` active animation with semantic SVG `<path>` routing plus a restrained halo/core/2-3 directional particle effect created only while evidence says an edge is active. Preserve current node layout/IDs where practical. Direction/state must be evidence-driven: frontend connectivity alone is not model activity; compute dispatch can animate hub->lane only for active delegation; explicit streaming/responding can reverse lane->hub; write lease can animate hub->writer; PROVING can project proof flow writer->hub; waiting/blocked/cooldown remain distinct and non-electric. 3) Preserve `prefers-reduced-motion`: no continuous particle/filter motion under reduced motion or hidden document, and remove/stop particle animation when edge is no longer active. Avoid persistent hidden animations. 4) Extend `control-center.js` polling to the Traffic page but keep visibility gating. Do not change provider dispatch, automatic route selection, traffic admission enforcement, EOCL/controller/write-lease semantics, tool schemas, Smart-v3 contract, restart behavior, or Codex bridge behavior. 5) Keep Command Center usable; do not move/remove existing IDs required by current bindings unless tests are updated coherently. 6) Add/adjust focused Node tests so they assert the Traffic & Usage page exists, uses existing read APIs/provider_traffic, preserves UNKNOWN semantics/reduced motion, and the router uses SVG path/particle semantics instead of only dashed lines. 7) Preserve all unrelated source/runtime files and do not reset/clean `.coding-tools/*`. Do not restart services, call paid providers, commit, push, or deploy. The exact Smart-v3 tool contract fingerprint must remain 4283e098c315d015c457ce2ab781257491ef70607c6c577f7699969fb8c3f754 with tool_count=8.
- Mode: `mcp_only`
- Base HEAD: `84775ab9a610de90704e00d5b89f5b2865332f7e`
- Worktree fingerprint: `5f0cc0faee194dc517a216b2ce9807f0e4442aab0bba8edb19439354414d0416`
- Contract fingerprint: `4283e098c315d015c457ce2ab781257491ef70607c6c577f7699969fb8c3f754`
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 2943 | 2026-08-14T17:02:35.866Z | wave_replanned |  | PREFLIGHT | reason=The prior Sol xhigh candidate was blocked before mutation because the broad packet exceeded prompt limits. Scope is now materially narrowed to five renderer/test files with exact deterministic patches. Existing provider_traffic, usage_events, flight_recorder, cooldown and EOCL read models are reused unchanged; no model candidate is needed. |
| 2944 | 2026-08-14T17:02:36.002Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 2945 | 2026-08-14T17:02:36.128Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 2946 | 2026-08-14T17:02:36.264Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 2947 | 2026-08-14T17:02:36.379Z | state_transition | READY | ROUTED | reason=route_selected |
| 2948 | 2026-08-14T17:02:36.859Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=06c71cc9a5bf4e8f8e322384fb3f8227 |
| 2949 | 2026-08-14T17:02:37.212Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 2950 | 2026-08-14T17:02:37.665Z | failure_observed | EXECUTING | EXECUTING | failure_class=PATCH_AMBIGUOUS |
| 2951 | 2026-08-14T17:02:37.957Z | write_lease_revoked | EXECUTING | EXECUTING | reason=state_transition:replan; owner=MCP; lease_id=06c71cc9a5bf4e8f8e322384fb3f8227 |
| 2952 | 2026-08-14T17:02:38.070Z | state_transition | EXECUTING | REPLAN | reason=PATCH_AMBIGUOUS; failure_class=PATCH_AMBIGUOUS |

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
