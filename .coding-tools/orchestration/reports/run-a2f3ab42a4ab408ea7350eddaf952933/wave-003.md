# Orchestration Wave 3

- Run: `a2f3ab42a4ab408ea7350eddaf952933`
- Wave: `ada0489eff8542959767dd03f6610a07`
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
| 39223 | 2026-09-04T00:55:44.730Z | wave_replanned |  | PREFLIGHT | reason=The first corrective proof plan used a ../../ path from package workdir and was blocked by filesystem_escape before execution. Changed strategy keeps all commands rooted at the authoritative workspace and supplies PYTHONPATH=resources/coding-tools-mcp so pytest imports the local package without any filesystem escape. No source bytes are changed by this corrective wave. |
| 39224 | 2026-09-04T00:55:44.989Z | observation_span_recorded |  |  |  |
| 39225 | 2026-09-04T00:55:45.265Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 39226 | 2026-09-04T00:55:45.502Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 39227 | 2026-09-04T00:55:45.762Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 39228 | 2026-09-04T00:55:46.006Z | state_transition | READY | ROUTED | reason=route_selected |
| 39229 | 2026-09-04T00:55:46.253Z | observation_span_recorded |  |  |  |
| 39230 | 2026-09-04T00:55:47.447Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=4a483eebdb384e749753f4d186c6ac6a |
| 39231 | 2026-09-04T00:55:47.693Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 39232 | 2026-09-04T00:55:48.803Z | observation_span_recorded |  |  |  |
| 39233 | 2026-09-04T00:55:49.208Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=4a483eebdb384e749753f4d186c6ac6a |
| 39234 | 2026-09-04T00:55:49.431Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 39235 | 2026-09-04T00:55:50.427Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:27e68038941bd43d; input_fingerprint=44e47eda13c3ac8b67fd27d9ddd9a41abe0500e173ae2e92a4a53cb71c52901d |
| 39236 | 2026-09-04T00:55:50.949Z | managed_process_admitted |  |  | owner=default |
| 39237 | 2026-09-04T00:55:51.303Z | managed_process_started |  |  | owner=default |
| 39238 | 2026-09-04T00:55:51.854Z | managed_process_terminal |  |  | owner=default |
| 39239 | 2026-09-04T00:55:52.276Z | proof_recorded |  |  | stage_id=check:27e68038941bd43d; status=passed; cache_hit=False; input_fingerprint=44e47eda13c3ac8b67fd27d9ddd9a41abe0500e173ae2e92a4a53cb71c52901d |
| 39240 | 2026-09-04T00:55:52.528Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=2b45e0895659c60a5c4c4143c75ca6d2b93aa5ff0df4da99580d87142a53fe90 |
| 39241 | 2026-09-04T00:55:53.060Z | managed_process_admitted |  |  | owner=default |
| 39242 | 2026-09-04T00:55:53.452Z | managed_process_started |  |  | owner=default |
| 39243 | 2026-09-04T00:55:56.068Z | managed_process_terminal |  |  | owner=default |
| 39244 | 2026-09-04T00:55:56.976Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=2b45e0895659c60a5c4c4143c75ca6d2b93aa5ff0df4da99580d87142a53fe90 |
| 39245 | 2026-09-04T00:55:57.205Z | observation_span_recorded |  |  |  |
| 39246 | 2026-09-04T00:55:57.397Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 39247 | 2026-09-04T00:56:45.469Z | managed_process_admitted |  |  | owner=chatweb-l3e-final-review |
| 39248 | 2026-09-04T00:56:45.894Z | managed_process_started |  |  | owner=chatweb-l3e-final-review |
| 39249 | 2026-09-04T00:56:46.422Z | managed_process_terminal |  |  | owner=chatweb-l3e-final-review |
| 39250 | 2026-09-04T00:57:00.036Z | managed_process_admitted |  |  | owner=chatweb-l3e-final-review |
| 39251 | 2026-09-04T00:57:00.518Z | managed_process_started |  |  | owner=chatweb-l3e-final-review |
| 39252 | 2026-09-04T00:57:01.110Z | managed_process_terminal |  |  | owner=chatweb-l3e-final-review |
| 39253 | 2026-09-04T00:57:25.236Z | observation_span_recorded |  |  |  |
| 39254 | 2026-09-04T00:57:25.473Z | failure_observed | ACCEPTING | ACCEPTING | reason=Final acceptance is procedurally blocked by ACCEPTANCE_FILE_ATTESTATION_REQUIRED because the four accepted paths were pre-existing dirty relative to the authoritative worktree. Source semantics and proof are accepted, but durable exact-byte adoption provenance must be recorded before checkpoint. Replan to an adoption-only corrective wave on the same current SHAs; no content changes.; failure_class=SOL_REJECTED |
| 39255 | 2026-09-04T00:57:25.706Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 39256 | 2026-09-04T00:57:25.967Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:27e68038941bd43d | passed | 44e47eda13c3ac8b67fd27d9ddd9a41abe0500e173ae2e92a4a53cb71c52901d | False | 1403 | 0 |
| verify:tests | passed | 2b45e0895659c60a5c4c4143c75ca6d2b93aa5ff0df4da99580d87142a53fe90 | False | 4016 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `116`
- Chain head: `5376c3d7fa2375e155d9985cb045c5ae3b61d89c934de589dbdae996684e022c`
