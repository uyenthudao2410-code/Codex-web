# Orchestration Wave 1

- Run: `5186e82d34ca4c70944f60be06f02cd2`
- Wave: `a431018af36c4046936c6ac6a4bf1b0d`
- Objective: Prepare the actual R3B production wiring against the now-accepted SourceSnapshotV1 foundation. Do not modify files or run proof commands. Inspect only the current shared shell protocol capability/request/job-context structs, shell-client request/waiter and hidden validation job start paths, ToolRuntime exact-source/dirty validation + server-first placement adapter, and Runner request dispatch/start_validation_job lifecycle. Produce the smallest coherent implementation plan with exact existing symbol names and insertion points.

Required behavior: add explicit `source_snapshot_validation` Runner capability default false and advertise true only in current Runner once all R3B support is wired; old runners fail closed. For a long unsandboxed cargo_check/cargo_test on an agent project: clean source keeps current R2B byte-for-byte behavior. Dirty source with full HEAD and source Runner snapshot capability must synchronously capture SourceSnapshotV1 through an internal Agent request (not a public MCP tool), validate it server-side, and then dispatch exactly one hidden structured validation job carrying the raw snapshot only transiently in the start request. Durable/public validation/job metadata must carry only base head + snapshot SHA-256/source mode, never snapshot content/base64. A distinct server_compute target is eligible for snapshot execution only when online/fresh/capable/capacity-available and it has the same base HEAD object/project; its registered checkout may itself be dirty because execution occurs in a private materialized clone. If no eligible distinct compute target exists, dispatch the same snapshot to the source Runner and materialize there; never validate directly against its authoritative dirty checkout. Before start, target Runner validates snapshot/base HEAD/capability, materializes via the accepted Runner source_snapshot module, redirects cwd to private clone + original project-relative cwd, and holds the RAII materialization owner until terminal/stop so cleanup is guaranteed. Snapshot capture/materialization rejection is pre-start, with no automatic cross-runner retry. Clean exact-source validation behavior and clean-target placement remain unchanged. No git worktree, no auto commit, no authoritative checkout writes, no general CAS, no new public MCP tool.

Identify exact structs/fields, request kind/result encoding, capacity/placement changes, durable metadata changes, runner job ownership point needed to hold materialization, compatibility literals needing explicit false, and focused tests that prove dirty source -> distinct snapshot target; dirty source -> source snapshot fallback; old capability/oversize/capture drift fail before validation enqueue; raw snapshot absent from public job/status; runner materialized validation cwd is temp and cleanup happens. Avoid root monolithic cargo test; prefer core protocol/placement tests, Runner focused package tests, root cargo check --tests, and only a small server test if there is a non-monolithic target.
- Mode: `mcp_only`
- Base HEAD: `6b5d16e980058d51585f039eff918d938bbb66e9`
- Worktree fingerprint: `39e1a99a9beb89c60425b5ef1d71f3db4e5bbb23a71d8c6493a0877b529a27c6`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 8899 | 2026-08-16T15:09:16.208Z | run_started |  | PREFLIGHT |  |
| 8900 | 2026-08-16T15:09:24.705Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 8901 | 2026-08-16T15:12:56.596Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 8902 | 2026-08-16T15:12:56.721Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 8903 | 2026-08-16T15:12:56.839Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 8904 | 2026-08-16T15:12:57.025Z | state_transition | READY | ROUTED | reason=route_selected |
| 8905 | 2026-08-16T15:12:57.471Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=a460ccc6656d4226a0b621aedeef4c50 |
| 8906 | 2026-08-16T15:12:57.580Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 8907 | 2026-08-16T15:12:58.071Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=a460ccc6656d4226a0b621aedeef4c50 |
| 8908 | 2026-08-16T15:12:58.204Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 8909 | 2026-08-16T15:12:58.609Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:810e75f0d3dee10e; input_fingerprint=17f211ddfba889e158aac734a8d05cb66be840da1112936083083c237aa94dc6 |
| 8910 | 2026-08-16T15:12:58.910Z | managed_process_admitted |  |  | owner=default |
| 8911 | 2026-08-16T15:12:59.160Z | managed_process_started |  |  | owner=default |
| 8912 | 2026-08-16T15:13:04.851Z | managed_process_terminal |  |  | owner=default |
| 8913 | 2026-08-16T15:13:05.139Z | proof_recorded |  |  | stage_id=check:810e75f0d3dee10e; status=passed; cache_hit=False; input_fingerprint=17f211ddfba889e158aac734a8d05cb66be840da1112936083083c237aa94dc6 |
| 8914 | 2026-08-16T15:13:05.322Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:7fc03c251493acf9; input_fingerprint=ccff3a71bc75fcb164691ad9f53c023dcd0e8a33ce8e188fae2e4a4e61744b06 |
| 8915 | 2026-08-16T15:13:05.673Z | managed_process_admitted |  |  | owner=default |
| 8916 | 2026-08-16T15:13:05.934Z | managed_process_started |  |  | owner=default |
| 8917 | 2026-08-16T15:13:06.623Z | managed_process_terminal |  |  | owner=default |
| 8918 | 2026-08-16T15:13:06.893Z | proof_recorded |  |  | stage_id=check:7fc03c251493acf9; status=passed; cache_hit=False; input_fingerprint=ccff3a71bc75fcb164691ad9f53c023dcd0e8a33ce8e188fae2e4a4e61744b06 |
| 8919 | 2026-08-16T15:13:07.027Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:c6e30766227ab9c6; input_fingerprint=11b8aef2cb875fc8b6afdc4bbcb2cc35b809422b874c9750ec9721bea353bbe6 |
| 8920 | 2026-08-16T15:13:07.349Z | managed_process_admitted |  |  | owner=default |
| 8921 | 2026-08-16T15:13:07.590Z | managed_process_started |  |  | owner=default |
| 8922 | 2026-08-16T15:13:08.131Z | managed_process_terminal |  |  | owner=default |
| 8923 | 2026-08-16T15:13:08.406Z | proof_recorded |  |  | stage_id=check:c6e30766227ab9c6; status=passed; cache_hit=False; input_fingerprint=11b8aef2cb875fc8b6afdc4bbcb2cc35b809422b874c9750ec9721bea353bbe6 |
| 8924 | 2026-08-16T15:13:08.545Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:a9833a296abd8634; input_fingerprint=28dd26bc26e1f76a25e658d31e9c7dcd248f48c681f06f88a28b5f9ace604137 |
| 8925 | 2026-08-16T15:13:08.849Z | managed_process_admitted |  |  | owner=default |
| 8926 | 2026-08-16T15:13:09.099Z | managed_process_started |  |  | owner=default |
| 8927 | 2026-08-16T15:13:13.008Z | managed_process_terminal |  |  | owner=default |
| 8928 | 2026-08-16T15:13:13.322Z | proof_recorded |  |  | stage_id=check:a9833a296abd8634; status=passed; cache_hit=False; input_fingerprint=28dd26bc26e1f76a25e658d31e9c7dcd248f48c681f06f88a28b5f9ace604137 |
| 8929 | 2026-08-16T15:13:13.472Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:bcb9509776b8d535; input_fingerprint=c7cf6baa8ab7431740fd98baf2eeb5d0870e96ffb6fd42f2e44ffeb31fbfa32d |
| 8930 | 2026-08-16T15:13:13.801Z | managed_process_admitted |  |  | owner=default |
| 8931 | 2026-08-16T15:13:14.065Z | managed_process_started |  |  | owner=default |
| 8932 | 2026-08-16T15:13:15.558Z | managed_process_terminal |  |  | owner=default |
| 8933 | 2026-08-16T15:13:15.797Z | proof_recorded |  |  | stage_id=check:bcb9509776b8d535; status=passed; cache_hit=False; input_fingerprint=c7cf6baa8ab7431740fd98baf2eeb5d0870e96ffb6fd42f2e44ffeb31fbfa32d |
| 8934 | 2026-08-16T15:13:15.954Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:731a566acabcb042; input_fingerprint=a539fc2259a323060357a5b42cbee57678db499b706e64606f94f68bc1fd497a |
| 8935 | 2026-08-16T15:13:16.366Z | managed_process_admitted |  |  | owner=default |
| 8936 | 2026-08-16T15:13:16.625Z | managed_process_started |  |  | owner=default |
| 8937 | 2026-08-16T15:13:17.523Z | managed_process_terminal |  |  | owner=default |
| 8938 | 2026-08-16T15:13:17.812Z | proof_recorded |  |  | stage_id=check:731a566acabcb042; status=passed; cache_hit=False; input_fingerprint=a539fc2259a323060357a5b42cbee57678db499b706e64606f94f68bc1fd497a |
| 8939 | 2026-08-16T15:13:17.951Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 8940 | 2026-08-16T15:13:44.787Z | failure_observed | ACCEPTING | ACCEPTING | reason=Implementation objective was not satisfied: affected_files and patch_results are empty and the worktree fingerprint is unchanged. The green checks prove only the pre-existing baseline, not R3B1 transport/capability/placement implementation. Replan with an explicit source change set; do not retry the unchanged no-op wave.; failure_class=SOL_REJECTED |
| 8941 | 2026-08-16T15:13:44.938Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 8942 | 2026-08-16T15:13:45.098Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:810e75f0d3dee10e | passed | 17f211ddfba889e158aac734a8d05cb66be840da1112936083083c237aa94dc6 | False | 6203 | 0 |
| check:7fc03c251493acf9 | passed | ccff3a71bc75fcb164691ad9f53c023dcd0e8a33ce8e188fae2e4a4e61744b06 | False | 1301 | 0 |
| check:c6e30766227ab9c6 | passed | 11b8aef2cb875fc8b6afdc4bbcb2cc35b809422b874c9750ec9721bea353bbe6 | False | 1118 | 0 |
| check:a9833a296abd8634 | passed | 28dd26bc26e1f76a25e658d31e9c7dcd248f48c681f06f88a28b5f9ace604137 | False | 4502 | 0 |
| check:bcb9509776b8d535 | passed | c7cf6baa8ab7431740fd98baf2eeb5d0870e96ffb6fd42f2e44ffeb31fbfa32d | False | 2043 | 0 |
| check:731a566acabcb042 | passed | a539fc2259a323060357a5b42cbee57678db499b706e64606f94f68bc1fd497a | False | 1530 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `71`
- Chain head: `433790551a3559a74460f9f02b5a80ecb014ca524b1f87754e0dfaaff452953c`
