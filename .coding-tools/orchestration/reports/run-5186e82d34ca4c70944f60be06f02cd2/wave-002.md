# Orchestration Wave 2

- Run: `5186e82d34ca4c70944f60be06f02cd2`
- Wave: `9c65dabcbcc34192954303a1dbf2aec1`
- Objective: Prepare the actual R3B production wiring against the now-accepted SourceSnapshotV1 foundation. Do not modify files or run proof commands. Inspect only the current shared shell protocol capability/request/job-context structs, shell-client request/waiter and hidden validation job start paths, ToolRuntime exact-source/dirty validation + server-first placement adapter, and Runner request dispatch/start_validation_job lifecycle. Produce the smallest coherent implementation plan with exact existing symbol names and insertion points.

Required behavior: add explicit `source_snapshot_validation` Runner capability default false and advertise true only in current Runner once all R3B support is wired; old runners fail closed. For a long unsandboxed cargo_check/cargo_test on an agent project: clean source keeps current R2B byte-for-byte behavior. Dirty source with full HEAD and source Runner snapshot capability must synchronously capture SourceSnapshotV1 through an internal Agent request (not a public MCP tool), validate it server-side, and then dispatch exactly one hidden structured validation job carrying the raw snapshot only transiently in the start request. Durable/public validation/job metadata must carry only base head + snapshot SHA-256/source mode, never snapshot content/base64. A distinct server_compute target is eligible for snapshot execution only when online/fresh/capable/capacity-available and it has the same base HEAD object/project; its registered checkout may itself be dirty because execution occurs in a private materialized clone. If no eligible distinct compute target exists, dispatch the same snapshot to the source Runner and materialize there; never validate directly against its authoritative dirty checkout. Before start, target Runner validates snapshot/base HEAD/capability, materializes via the accepted Runner source_snapshot module, redirects cwd to private clone + original project-relative cwd, and holds the RAII materialization owner until terminal/stop so cleanup is guaranteed. Snapshot capture/materialization rejection is pre-start, with no automatic cross-runner retry. Clean exact-source validation behavior and clean-target placement remain unchanged. No git worktree, no auto commit, no authoritative checkout writes, no general CAS, no new public MCP tool.

Identify exact structs/fields, request kind/result encoding, capacity/placement changes, durable metadata changes, runner job ownership point needed to hold materialization, compatibility literals needing explicit false, and focused tests that prove dirty source -> distinct snapshot target; dirty source -> source snapshot fallback; old capability/oversize/capture drift fail before validation enqueue; raw snapshot absent from public job/status; runner materialized validation cwd is temp and cleanup happens. Avoid root monolithic cargo test; prefer core protocol/placement tests, Runner focused package tests, root cargo check --tests, and only a small server test if there is a non-monolithic target.
- Mode: `mcp_only`
- Base HEAD: `6b5d16e980058d51585f039eff918d938bbb66e9`
- Worktree fingerprint: `39e1a99a9beb89c60425b5ef1d71f3db4e5bbb23a71d8c6493a0877b529a27c6`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 8943 | 2026-08-16T15:14:34.539Z | wave_replanned |  | PREFLIGHT | reason=The prior R3B1 wave was rejected because it was a no-op despite green baseline checks. Replace it with an explicit, smaller source mutation: first implement only the shared transport-safe SourceSnapshot contract additions, prove them, then continue capability/placement in a later accepted wave. |
| 8944 | 2026-08-16T15:14:34.674Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 8945 | 2026-08-16T15:14:34.825Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 8946 | 2026-08-16T15:14:34.954Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 8947 | 2026-08-16T15:14:35.105Z | state_transition | READY | ROUTED | reason=route_selected |
| 8948 | 2026-08-16T15:14:35.586Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=603ea429f270450295c879b1abf86744 |
| 8949 | 2026-08-16T15:14:35.710Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 8950 | 2026-08-16T15:14:36.253Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=603ea429f270450295c879b1abf86744 |
| 8951 | 2026-08-16T15:14:36.395Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 8952 | 2026-08-16T15:14:36.802Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:810e75f0d3dee10e; input_fingerprint=17b4392c9c906660cccfac2e0de7ce4ad1da947d6bd91058777551ae7aa3ec5c |
| 8953 | 2026-08-16T15:14:37.105Z | managed_process_admitted |  |  | owner=default |
| 8954 | 2026-08-16T15:14:37.386Z | managed_process_started |  |  | owner=default |
| 8955 | 2026-08-16T15:14:43.706Z | managed_process_terminal |  |  | owner=default |
| 8956 | 2026-08-16T15:14:44.006Z | proof_recorded |  |  | stage_id=check:810e75f0d3dee10e; status=passed; cache_hit=False; input_fingerprint=17b4392c9c906660cccfac2e0de7ce4ad1da947d6bd91058777551ae7aa3ec5c |
| 8957 | 2026-08-16T15:14:44.163Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:7fc03c251493acf9; input_fingerprint=6ca3eb1ebd2be4c950e3755b7877458d3e07310c722b2e471b8590d2b04b0083 |
| 8958 | 2026-08-16T15:14:44.464Z | managed_process_admitted |  |  | owner=default |
| 8959 | 2026-08-16T15:14:44.736Z | managed_process_started |  |  | owner=default |
| 8960 | 2026-08-16T15:14:59.198Z | managed_process_terminal |  |  | owner=default |
| 8961 | 2026-08-16T15:14:59.463Z | proof_recorded |  |  | stage_id=check:7fc03c251493acf9; status=passed; cache_hit=False; input_fingerprint=6ca3eb1ebd2be4c950e3755b7877458d3e07310c722b2e471b8590d2b04b0083 |
| 8962 | 2026-08-16T15:14:59.590Z | proof_cache_miss |  |  | reason=cold; stage_id=check:e34766b6d5981e99; input_fingerprint=157cdf6d1860a601c975be1e7bdb3b73264aaa7e3ad8807b6fb0e8ac6d55b819 |
| 8963 | 2026-08-16T15:14:59.973Z | managed_process_admitted |  |  | owner=default |
| 8964 | 2026-08-16T15:15:00.223Z | managed_process_started |  |  | owner=default |
| 8965 | 2026-08-16T15:15:07.062Z | managed_process_terminal |  |  | owner=default |
| 8966 | 2026-08-16T15:15:07.387Z | proof_recorded |  |  | stage_id=check:e34766b6d5981e99; status=passed; cache_hit=False; input_fingerprint=157cdf6d1860a601c975be1e7bdb3b73264aaa7e3ad8807b6fb0e8ac6d55b819 |
| 8967 | 2026-08-16T15:15:07.941Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 8968 | 2026-08-16T15:15:31.490Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 8969 | 2026-08-16T15:15:31.785Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:810e75f0d3dee10e | passed | 17b4392c9c906660cccfac2e0de7ce4ad1da947d6bd91058777551ae7aa3ec5c | False | 6903 | 0 |
| check:7fc03c251493acf9 | passed | 6ca3eb1ebd2be4c950e3755b7877458d3e07310c722b2e471b8590d2b04b0083 | False | 15059 | 0 |
| check:e34766b6d5981e99 | passed | 157cdf6d1860a601c975be1e7bdb3b73264aaa7e3ad8807b6fb0e8ac6d55b819 | False | 7431 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| d643f725dee448f8a8b8ef5a80242f9f | accepted | 6b5d16e980058d51585f039eff918d938bbb66e9 | f70e1fdf74a5ab76068fb7b89a41a05ad913f62890914c6a154acba24a36f03e | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `71`
- Chain head: `433790551a3559a74460f9f02b5a80ecb014ca524b1f87754e0dfaaff452953c`
