# Orchestration Wave 5

- Run: `21a41bfdbfc44192a82bc10c25e7eefe`
- Wave: `0f2011a7fa93446394764d5f35b11348`
- Objective: Implement and prove the remaining H0/L3 controller-usage sideband closure in exact RUN 21a41bfdbfc44192a82bc10c25e7eefe. Before mutation, verify the six supplied adoption-anchor SHA-256 values and fail closed on drift. Make only the smallest directly necessary changes inside the approved packet. Requirements: (1) make evidence_completeness.py the single Python authority with CURRENT_HOST_OBSERVATION_SCHEMA_VERSION=6 and LEGACY_HOST_OBSERVATION_SCHEMA_VERSIONS={1,2,3,4,5}; evaluation_report.py imports/reuses those constants; only v6 contributes to current percentiles/correlation, v1-v5 remain legacy; current fixtures use v6 and the legacy test retains v1-v5 plus a separate v6 current event. (2) In chatEvaluationJournal.js remove generic Object.values and arbitrary array/object traversal; inspect only a minimal explicit allowlist of response-envelope keys required for response.completed/response shapes and never descend into message/messages/output/content/input/prompt/instructions/reasoning/chain-of-thought or unknown keys; persist numeric usage and correlation metadata only; preserve stable dedupe; wrappers for JSON.parse and Response.json must not stack and dispose must restore the exact originals; add focused hostile nested-usage, double-install/dedupe, and dispose-restoration tests. (3) Electron controllerUsage must carry exact run_id, wave_id, turn_id and trace_id and preserve the authenticated ChatWeb bridge. (4) usage_events controller report validation must accept paired run_id/wave_id, validate bounded text, reject booleans, negative/non-integer and values above JavaScript Number.MAX_SAFE_INTEGER, while preserving unknown-not-zero and exact-idempotent duplicate behavior. (5) controller_usage_ingress must reject implicit_default, partial_headers and spoofed identity before ledger mutation; only explicit_headers or attested_transport with client_type=chatweb and role=controller are eligible. When authoritative RUN/WAVE exists, report RUN/WAVE must be present and exact; turn_id/trace_id must exact-match the authoritative current host/evaluation correlation identity. CHECKPOINTED post-turn ingress is allowed only for the exact current wave while the same existing controller lease remains active/unexpired; do not renew/claim an expired or missing lease before validating this path. Preserve first-agent-workflow deferred usage only when no RUN/WAVE authority exists before prevalidation, then bind the exact created RUN/WAVE before record. Add focused tests for implicit/partial/spoofed provenance, run/wave mismatch, turn/trace mismatch, unsafe integer, duplicate conflict, exact idempotent duplicate, CHECKPOINTED same-wave active-lease success, expired lease rejection, and wave mismatch rejection. Keep smart-v3 public surface exactly 8 tools. Do not modify mcp_http_handler.py, server.py, orchestration_ledger.py, http_hub_identity.py, unrelated dirty work, or accidental dist artifacts. Do not run npm test, npm run dist, build, package, clean, restore, reset, commit, push, tag, publish, release or deploy.
- Objective revision: `5`
- Objective SHA-256: `11232fdc1f4347b794888ed9f4aafe540f102a7d1b6074b6590c1bf01fe6559d`
- Objective source: `replan_request`
- Mode: `deep_single_lane`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `753839c6ce2254b680f3440b0e6ab8143dd0735633ca8b86f31b93e887b11779`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| dbce1de9e5904ea7b29602b9be0e50d5 | CODEX:sol_xhigh | sol_xhigh | sol_xhigh | gpt-5.6-sol | xhigh | blocked |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 36885 | 2026-09-03T09:11:11.844Z | wave_replanned |  | PREFLIGHT | reason=The exact archived RUN is now correctly reattached and the prior PREFLIGHT wave has been driven to canonical REPLAN without source mutation. Change strategy from the read-only deterministic prepare objective to one bounded deep single-lane implementation wave so the approved causal source changes are actually synthesized under EOCL authority. Preserve the six exact current-byte anchors, unrelated dirty work, and accidental dist artifacts; use only the operator-approved proof command and no npm/build/package commands. |
| 36886 | 2026-09-03T09:11:12.078Z | observation_span_recorded |  |  |  |
| 36887 | 2026-09-03T09:11:13.077Z | observation_span_recorded |  |  |  |
| 36888 | 2026-09-03T09:11:13.265Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 36889 | 2026-09-03T09:11:13.694Z | managed_process_admitted |  |  | owner=default |
| 36890 | 2026-09-03T09:11:13.999Z | managed_process_started |  |  | owner=default |
| 36891 | 2026-09-03T09:11:50.121Z | managed_process_terminal |  |  | owner=default |
| 36892 | 2026-09-03T09:11:50.329Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 36893 | 2026-09-03T09:11:50.501Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 36894 | 2026-09-03T09:11:50.693Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 36895 | 2026-09-03T09:11:50.887Z | route_selected | READY | READY | reason=explicit_request; requested=sol_xhigh; resolved=sol_xhigh |
| 36896 | 2026-09-03T09:11:51.068Z | state_transition | READY | ROUTED | reason=route_selected |
| 36897 | 2026-09-03T09:11:51.354Z | observation_span_recorded |  |  |  |
| 36898 | 2026-09-03T09:11:51.669Z | delegation_started | ROUTED | ROUTED | authority_owner=CODEX:sol_xhigh |
| 36899 | 2026-09-03T09:11:51.860Z | model_dispatch_started | ROUTED | ROUTED |  |
| 36900 | 2026-09-03T09:11:52.063Z | model_dispatch_finished | ROUTED | ROUTED | failure_class=PROMPT_TOO_LARGE; status=error |
| 36901 | 2026-09-03T09:11:52.349Z | delegation_finished | ROUTED | ROUTED | reason=PROMPT_TOO_LARGE; status=blocked |
| 36902 | 2026-09-03T09:11:52.592Z | failure_observed | ROUTED | ROUTED | failure_class=PROMPT_TOO_LARGE |
| 36903 | 2026-09-03T09:11:52.766Z | state_transition | ROUTED | REPLAN | reason=PROMPT_TOO_LARGE; failure_class=PROMPT_TOO_LARGE |
| 36904 | 2026-09-03T09:11:52.993Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

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
- Events checked: `477`
- Chain head: `d5d92b6a865dd8405169addd711fceac1741f551a0ecc3cbbc612370d70344c6`
