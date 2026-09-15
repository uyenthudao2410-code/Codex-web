# Orchestration Wave 2

- Run: `2375a022574e497eaebdc49a519ee537`
- Wave: `ecae76662a1441008c04b85f7056c844`
- Objective: Complete the read-only diagnosis of RUN_CONTINUATION_CHECK_HASH_MISMATCH by recomputing the exact approved-check definition hash on the current worktree after the preflight drift. Do not create a continuation grant, mutate source/runtime/task lifecycle beyond this diagnostic wave, or restart anything.
- Objective revision: `2`
- Objective SHA-256: `31c48b7174874e7ae0894dee37273611ddd39de8f90c20d68bb5428be7fd90a8`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6`
- Worktree fingerprint: `d2e486a7b092e42750726a978c14d1364d146e99be33a9e652ae61581f8344e1`
- Contract fingerprint: `270e9a76c407a40e3a8d7c9151f355841314d54e778559402beef4517ffe282f`
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 58224 | 2026-09-15T08:03:47.263Z | wave_replanned |  | PREFLIGHT | reason=The prepared diagnostic wave entered REPLAN because current workspace/source identity changed after preflight. Recompute the deterministic check hash on the current worktree in a fresh same-task wave instead of retrying the stale prepared wave. |
| 58225 | 2026-09-15T08:03:47.823Z | observation_span_recorded |  |  |  |
| 58226 | 2026-09-15T08:03:48.526Z | observation_span_recorded |  |  |  |
| 58227 | 2026-09-15T08:03:48.952Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 58228 | 2026-09-15T08:03:49.254Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 58229 | 2026-09-15T08:03:49.528Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 58230 | 2026-09-15T08:03:49.897Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 58231 | 2026-09-15T08:03:50.246Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 58232 | 2026-09-15T08:03:50.537Z | state_transition | READY | ROUTED | reason=route_selected |
| 58233 | 2026-09-15T08:03:51.141Z | observation_span_recorded |  |  |  |
| 58234 | 2026-09-15T08:03:51.961Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=1de1c609809441939722e27478a0eea4 |
| 58235 | 2026-09-15T08:03:52.240Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 58236 | 2026-09-15T08:03:53.101Z | observation_span_recorded |  |  |  |
| 58237 | 2026-09-15T08:03:53.765Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=1de1c609809441939722e27478a0eea4 |
| 58238 | 2026-09-15T08:03:54.145Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 58239 | 2026-09-15T08:03:54.892Z | proof_cache_miss |  |  | reason=cold; stage_id=check:fc1360afa72cb4dd; input_fingerprint=3e53b59d49ec09479fcc92da0282f67e58eaf3db82464081048694aafc0d663a |
| 58240 | 2026-09-15T08:03:55.252Z | observation_span_recorded |  |  |  |
| 58241 | 2026-09-15T08:03:55.511Z | failure_observed | PROVING | PROVING | failure_class=PERMISSION_REQUIRED |
| 58242 | 2026-09-15T08:03:55.726Z | state_transition | PROVING | REPLAN | reason=PERMISSION_REQUIRED; failure_class=PERMISSION_REQUIRED |
| 58243 | 2026-09-15T08:03:56.110Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

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
- Events checked: `51`
- Chain head: `a55b99b40c1cac41f57d952513da210ed51f36ba717c67a933a623d852ae3a48`
