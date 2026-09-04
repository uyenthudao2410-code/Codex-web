# Orchestration Wave 1

- Run: `a2f3ab42a4ab408ea7350eddaf952933`
- Wave: `aedf53c1ab164ac5835e90289d6b853f`
- Objective: Implement the prepared L3E controller quantification without contaminating canonical exact accounting. Add a content-free controller_token_estimate projection to accepted-result operations analytics. For accepted RUNs missing exact controller UsageEvents, use empirical exact-controller-total-token/model_visible_bytes ratios when at least 5 positive exact calibration pairs exist, returning measurement=CALIBRATED_ESTIMATE, p10/p50/p90 missing-controller total-token estimate, confidence, calibration sample count, and provenance. When fewer than 5 calibration pairs exist but missing accepted RUNs have positive model_visible_bytes, return a separate measurement=CONTEXT_ESTIMATE using the existing explicit context-estimate prior semantics (2-6 bytes/token interval, p50=4 bytes/token), label it LOW confidence and not_controller_total=true; never call this controller total. If evidence is insufficient return UNKNOWN/unknown_not_zero. Exact UsageEvents always remain authoritative and no estimate is written into usage_analytics/ledger/cost. Wire renderer dashboard trust strip to show exact, calibrated missing-controller estimate, or context estimate numerically with interval/confidence; keep six canonical KPI totals exact and unchanged. Technical provenance remains in analytics but not surfaced on default Overview. Add focused Python behavior tests plus dashboard contract assertions. Do not restart runtime, modify ledger schema/controller ingress/Electron journal, commit, push, release, or deploy.
- Objective revision: `1`
- Objective SHA-256: `954a154e13e03be6862fae9a544b2ecf1a2239ce9f88f00df75b91e0ea2b1077`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `80aceb583202ad381c25687969fb48adbf74622c`
- Worktree fingerprint: `d46ffaa7a1d456af5147ee8231c223d96b01a34865e3f15ab9ed88b2e8ddeb38`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 39173 | 2026-09-04T00:54:27.560Z | run_started |  | PREFLIGHT |  |
| 39174 | 2026-09-04T00:54:28.183Z | observation_span_recorded |  |  |  |
| 39175 | 2026-09-04T00:54:28.431Z | solution_shadow_recommended |  |  |  |
| 39176 | 2026-09-04T00:54:28.663Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 39177 | 2026-09-04T00:54:28.888Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 39178 | 2026-09-04T00:54:29.157Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 39179 | 2026-09-04T00:54:29.373Z | state_transition | READY | ROUTED | reason=route_selected |
| 39180 | 2026-09-04T00:54:29.618Z | observation_span_recorded |  |  |  |
| 39181 | 2026-09-04T00:54:30.763Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=8f426b64615843e9873d262a6930ceec |
| 39182 | 2026-09-04T00:54:30.974Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 39183 | 2026-09-04T00:54:32.153Z | patch_surface_observed |  |  |  |
| 39184 | 2026-09-04T00:54:32.378Z | observation_span_recorded |  |  |  |
| 39185 | 2026-09-04T00:54:32.686Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=8f426b64615843e9873d262a6930ceec |
| 39186 | 2026-09-04T00:54:32.855Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 39187 | 2026-09-04T00:54:33.796Z | proof_cache_miss |  |  | reason=cold; stage_id=check:27e68038941bd43d; input_fingerprint=493ae9f2a2d9489579ce2d664c64a5f18c06c2321dc331accb5496e03bae266d |
| 39188 | 2026-09-04T00:54:34.207Z | managed_process_admitted |  |  | owner=default |
| 39189 | 2026-09-04T00:54:34.561Z | managed_process_started |  |  | owner=default |
| 39190 | 2026-09-04T00:54:35.076Z | managed_process_terminal |  |  | owner=default |
| 39191 | 2026-09-04T00:54:35.564Z | proof_recorded |  |  | stage_id=check:27e68038941bd43d; status=passed; cache_hit=False; input_fingerprint=493ae9f2a2d9489579ce2d664c64a5f18c06c2321dc331accb5496e03bae266d |
| 39192 | 2026-09-04T00:54:35.782Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=7abe96132333864521d3b02a0905055948ddbec9a25cf214d7f4a9839bb4d611 |
| 39193 | 2026-09-04T00:54:36.240Z | managed_process_admitted |  |  | owner=default |
| 39194 | 2026-09-04T00:54:36.670Z | managed_process_started |  |  | owner=default |
| 39195 | 2026-09-04T00:54:37.920Z | managed_process_terminal |  |  | owner=default |
| 39196 | 2026-09-04T00:54:38.338Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=7abe96132333864521d3b02a0905055948ddbec9a25cf214d7f4a9839bb4d611 |
| 39197 | 2026-09-04T00:54:38.635Z | observation_span_recorded |  |  |  |
| 39198 | 2026-09-04T00:54:38.872Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 39199 | 2026-09-04T00:54:39.096Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 39200 | 2026-09-04T00:54:39.311Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:27e68038941bd43d | passed | 493ae9f2a2d9489579ce2d664c64a5f18c06c2321dc331accb5496e03bae266d | False | 1334 | 0 |
| verify:tests | failed | 7abe96132333864521d3b02a0905055948ddbec9a25cf214d7f4a9839bb4d611 | False | 2110 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `116`
- Chain head: `5376c3d7fa2375e155d9985cb045c5ae3b61d89c934de589dbdae996684e022c`
