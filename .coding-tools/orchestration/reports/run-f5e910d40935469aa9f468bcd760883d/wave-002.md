# Orchestration Wave 2

- Run: `f5e910d40935469aa9f468bcd760883d`
- Wave: `986f52e5cba643178e2a8d66031be9a1`
- Objective: Investigate Project Finance -> Project detail -> Overview in the HR app. Identify every overview KPI/card/table value that is currently hardcoded, mocked, placeholder, seeded only for UI, or falls back to fake numbers. Trace the real data contracts and calculation sources available in the current finance frontend/BFF/backend. Do not mutate files yet. Financial invariant: displayed monetary/percentage/status values must be derived from the selected project's real persisted/read-model data and must not fabricate a value when source data is missing; missing data should be represented truthfully. Return the smallest coherent implementation scope and authoritative focused verification commands.
- Mode: `mcp_only`
- Base HEAD: `788c0f33470611be3d50727a5b23c29ef2169070`
- Worktree fingerprint: `08d2a211d125629da5f463c3afe2487fade0034ebac81bedf444921c3d4b5d0a`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 19246 | 2026-08-19T04:30:07.634Z | wave_replanned |  | PREFLIGHT | reason=Orchestration preflight detected live base/worktree/contract drift, likely from concurrent edits in another tab/agent. Replan from the current worktree, preserve all unrelated edits, and restrict mutation to the smallest causal dashboard realtime-metrics scope. |
| 19247 | 2026-08-19T04:30:09.067Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 19248 | 2026-08-19T04:30:09.232Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 19249 | 2026-08-19T04:30:09.381Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 19250 | 2026-08-19T04:30:09.721Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 19251 | 2026-08-19T04:30:09.949Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 19252 | 2026-08-19T04:30:10.133Z | state_transition | READY | ROUTED | reason=route_selected |
| 19253 | 2026-08-19T04:30:10.958Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=c173a63c94464733974fd7cc8ef5fdae |
| 19254 | 2026-08-19T04:30:11.106Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 19255 | 2026-08-19T04:30:11.633Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=c173a63c94464733974fd7cc8ef5fdae |
| 19256 | 2026-08-19T04:30:11.765Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 19257 | 2026-08-19T04:30:12.213Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:all; input_fingerprint=1757208f5f7c1b007de709ae4110b36e5676f6523316d8f7fe4742951d2a994c |
| 19258 | 2026-08-19T04:30:12.517Z | managed_process_admitted |  |  | owner=default |
| 19259 | 2026-08-19T04:30:12.737Z | managed_process_started |  |  | owner=default |
| 19260 | 2026-08-19T04:30:20.011Z | managed_process_admitted |  |  | owner=chatweb |
| 19261 | 2026-08-19T04:30:20.454Z | managed_process_started |  |  | owner=chatweb |
| 19262 | 2026-08-19T04:30:21.152Z | managed_process_terminal |  |  | owner=chatweb |
| 19263 | 2026-08-19T04:30:39.402Z | managed_process_terminal |  |  | owner=default |
| 19264 | 2026-08-19T04:30:39.792Z | managed_process_admitted |  |  | owner=default |
| 19265 | 2026-08-19T04:30:40.036Z | managed_process_started |  |  | owner=default |
| 19266 | 2026-08-19T04:30:40.714Z | managed_process_admitted |  |  | owner=chatweb |
| 19267 | 2026-08-19T04:30:40.964Z | managed_process_started |  |  | owner=chatweb |
| 19268 | 2026-08-19T04:30:41.697Z | managed_process_terminal |  |  | owner=chatweb |
| 19269 | 2026-08-19T04:30:59.610Z | failure_observed | PROVING | PROVING | reason=A non-terminal wave was recovered outside its original synchronous execution.; failure_class=RUNTIME_RESUME_REQUIRED |
| 19270 | 2026-08-19T04:30:59.781Z | state_transition | PROVING | REPLAN | reason=RUNTIME_RESUME_REQUIRED; failure_class=RUNTIME_RESUME_REQUIRED |
| 19271 | 2026-08-19T04:31:00.366Z | managed_process_terminal |  |  | owner=default |
| 19272 | 2026-08-19T04:31:00.724Z | proof_recorded |  |  | stage_id=verify:all; status=failed; cache_hit=False; input_fingerprint=1757208f5f7c1b007de709ae4110b36e5676f6523316d8f7fe4742951d2a994c |
| 19273 | 2026-08-19T04:31:00.859Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 19274 | 2026-08-19T04:31:01.016Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 19275 | 2026-08-19T04:31:01.182Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 19276 | 2026-08-19T04:31:01.431Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:all | failed | 1757208f5f7c1b007de709ae4110b36e5676f6523316d8f7fe4742951d2a994c | False | 48014 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `197`
- Chain head: `b7269eb4089c09255400b81b4981a53bcbe1a4a2fccfe75cabcc724afe37087e`
