# Orchestration Wave 2

- Run: `a2f3ab42a4ab408ea7350eddaf952933`
- Wave: `ce13e273dabb4a449d34bd90107309a6`
- Objective: Implement the prepared L3E controller quantification without contaminating canonical exact accounting. Add a content-free controller_token_estimate projection to accepted-result operations analytics. For accepted RUNs missing exact controller UsageEvents, use empirical exact-controller-total-token/model_visible_bytes ratios when at least 5 positive exact calibration pairs exist, returning measurement=CALIBRATED_ESTIMATE, p10/p50/p90 missing-controller total-token estimate, confidence, calibration sample count, and provenance. When fewer than 5 calibration pairs exist but missing accepted RUNs have positive model_visible_bytes, return a separate measurement=CONTEXT_ESTIMATE using the existing explicit context-estimate prior semantics (2-6 bytes/token interval, p50=4 bytes/token), label it LOW confidence and not_controller_total=true; never call this controller total. If evidence is insufficient return UNKNOWN/unknown_not_zero. Exact UsageEvents always remain authoritative and no estimate is written into usage_analytics/ledger/cost. Wire renderer dashboard trust strip to show exact, calibrated missing-controller estimate, or context estimate numerically with interval/confidence; keep six canonical KPI totals exact and unchanged. Technical provenance remains in analytics but not surfaced on default Overview. Add focused Python behavior tests plus dashboard contract assertions. Do not restart runtime, modify ledger schema/controller ingress/Electron journal, commit, push, release, or deploy.
- Objective revision: `1`
- Objective SHA-256: `954a154e13e03be6862fae9a544b2ecf1a2239ce9f88f00df75b91e0ea2b1077`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `80aceb583202ad381c25687969fb48adbf74622c`
- Worktree fingerprint: `c0f826c94fd886a1b1012fe04fc121f2866d26653087f0a34fc8a7ce7c403899`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 39201 | 2026-09-04T00:55:23.300Z | wave_replanned |  | PREFLIGHT | reason=Previous verification failed during pytest collection only because it ran from repository root, causing ModuleNotFoundError for the local coding_tools_mcp package. Exact traceback has now been read. Source patch and git diff --check were clean; this corrective wave changes only the proof working directory to the package root and makes no additional source write. |
| 39202 | 2026-09-04T00:55:23.556Z | observation_span_recorded |  |  |  |
| 39203 | 2026-09-04T00:55:23.823Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 39204 | 2026-09-04T00:55:24.072Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 39205 | 2026-09-04T00:55:24.327Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 39206 | 2026-09-04T00:55:24.572Z | state_transition | READY | ROUTED | reason=route_selected |
| 39207 | 2026-09-04T00:55:24.844Z | observation_span_recorded |  |  |  |
| 39208 | 2026-09-04T00:55:26.002Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=4c34c7776fc146c0b542cba8d2041a68 |
| 39209 | 2026-09-04T00:55:26.247Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 39210 | 2026-09-04T00:55:27.157Z | observation_span_recorded |  |  |  |
| 39211 | 2026-09-04T00:55:27.612Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=4c34c7776fc146c0b542cba8d2041a68 |
| 39212 | 2026-09-04T00:55:27.839Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 39213 | 2026-09-04T00:55:28.777Z | proof_cache_miss |  |  | reason=cold; stage_id=check:6250985ac71611cb; input_fingerprint=f5e82068c026c861727bb4ee586d8da561de3f702fe4e6b204cf33f072b48420 |
| 39214 | 2026-09-04T00:55:29.272Z | managed_process_admitted |  |  | owner=default |
| 39215 | 2026-09-04T00:55:29.669Z | managed_process_started |  |  | owner=default |
| 39216 | 2026-09-04T00:55:30.169Z | managed_process_terminal |  |  | owner=default |
| 39217 | 2026-09-04T00:55:30.595Z | proof_recorded |  |  | stage_id=check:6250985ac71611cb; status=passed; cache_hit=False; input_fingerprint=f5e82068c026c861727bb4ee586d8da561de3f702fe4e6b204cf33f072b48420 |
| 39218 | 2026-09-04T00:55:30.844Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=27acad834aa11758219278b713fbc4f6856f49d10ce7aa3b128be93e9287bb97 |
| 39219 | 2026-09-04T00:55:31.101Z | observation_span_recorded |  |  |  |
| 39220 | 2026-09-04T00:55:31.331Z | failure_observed | PROVING | PROVING | failure_class=PERMISSION_REQUIRED |
| 39221 | 2026-09-04T00:55:31.547Z | state_transition | PROVING | REPLAN | reason=PERMISSION_REQUIRED; failure_class=PERMISSION_REQUIRED |
| 39222 | 2026-09-04T00:55:32.016Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:6250985ac71611cb | passed | f5e82068c026c861727bb4ee586d8da561de3f702fe4e6b204cf33f072b48420 | False | 1392 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `116`
- Chain head: `5376c3d7fa2375e155d9985cb045c5ae3b61d89c934de589dbdae996684e022c`
