# Orchestration Wave 2

- Run: `c4159c9d6ea94654887b89c7851dfbe4`
- Wave: `271a8b902b164888b62fa972752b01c5`
- Objective: Prepare R3B production wiring only; do not modify files or run implementation/proof commands. Inspect the verified current R3A source_snapshot contract/module and the exact current R2B structured validation path. Identify current symbol names and the minimal edits to: add an internal synchronous source-snapshot capture request with explicit capability gate; capture bounded dirty source at a full base HEAD; carry only the validated snapshot payload transiently on the start_validation_job request while retaining only base-head + snapshot digest in durable/public validation metadata; make snapshot-aware placement require the new capability and permit a dirty primary checkout because execution materializes a private clone; choose a distinct server_compute target when eligible, otherwise execute the same snapshot on the source Runner; materialize the snapshot in the Runner before validation and redirect cwd to the private clone plus project-relative cwd; keep the materialization RAII owner alive through terminal/stop then cleanup; and preserve the existing clean R2B path unchanged. Fail closed for old runners, oversize/malformed snapshot, source capture drift, target capability loss, target base-head mismatch, materialization failure, and outcome-unknown. No public MCP tool, no auto Git commit, no git worktree, no authoritative checkout write, no raw snapshot contents in job/status/inventory. Determine exact tests that can prove production wiring without running root monolithic cargo test; prefer core placement/protocol tests + runner focused tests + compile of root tests, and if a small existing server test target is available use it. Return one concrete change set.
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
| 8856 | 2026-08-16T15:02:00.807Z | wave_replanned |  | PREFLIGHT | reason=The prior R3A corrective wave created the real source-snapshot foundation but stopped at rustfmt --check before any tests ran. Apply the exact rustfmt-only changes to the two new snapshot source files, then run the settled bounded proof chain. This is not an unchanged retry. |
| 8857 | 2026-08-16T15:02:00.931Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 8858 | 2026-08-16T15:02:01.094Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 8859 | 2026-08-16T15:02:01.194Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 8860 | 2026-08-16T15:02:01.354Z | state_transition | READY | ROUTED | reason=route_selected |
| 8861 | 2026-08-16T15:02:01.792Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=1a819c2b27c24fbca9b91db3b8c3b89d |
| 8862 | 2026-08-16T15:02:01.904Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 8863 | 2026-08-16T15:02:02.409Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=1a819c2b27c24fbca9b91db3b8c3b89d |
| 8864 | 2026-08-16T15:02:02.540Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 8865 | 2026-08-16T15:02:02.946Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:810e75f0d3dee10e; input_fingerprint=c5f45ba74537e4b00648d3d02fd34837bc0dc414868625bac8612151e996b39c |
| 8866 | 2026-08-16T15:02:03.261Z | managed_process_admitted |  |  | owner=default |
| 8867 | 2026-08-16T15:02:03.531Z | managed_process_started |  |  | owner=default |
| 8868 | 2026-08-16T15:02:09.161Z | managed_process_terminal |  |  | owner=default |
| 8869 | 2026-08-16T15:02:09.528Z | proof_recorded |  |  | stage_id=check:810e75f0d3dee10e; status=passed; cache_hit=False; input_fingerprint=c5f45ba74537e4b00648d3d02fd34837bc0dc414868625bac8612151e996b39c |
| 8870 | 2026-08-16T15:02:09.687Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:7fc03c251493acf9; input_fingerprint=7a41b67df15b61a3c28087ada76140607bd3ad4628681ad483bef6fe7e68cc51 |
| 8871 | 2026-08-16T15:02:10.028Z | managed_process_admitted |  |  | owner=default |
| 8872 | 2026-08-16T15:02:10.314Z | managed_process_started |  |  | owner=default |
| 8873 | 2026-08-16T15:02:23.693Z | managed_process_terminal |  |  | owner=default |
| 8874 | 2026-08-16T15:02:23.965Z | proof_recorded |  |  | stage_id=check:7fc03c251493acf9; status=passed; cache_hit=False; input_fingerprint=7a41b67df15b61a3c28087ada76140607bd3ad4628681ad483bef6fe7e68cc51 |
| 8875 | 2026-08-16T15:02:24.103Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:a9833a296abd8634; input_fingerprint=fcd838fbfb73620308ab0a20566e45c562121fdaff31f07e79f15fa2183638c5 |
| 8876 | 2026-08-16T15:02:24.426Z | managed_process_admitted |  |  | owner=default |
| 8877 | 2026-08-16T15:02:24.822Z | managed_process_started |  |  | owner=default |
| 8878 | 2026-08-16T15:03:23.952Z | managed_process_terminal |  |  | owner=default |
| 8879 | 2026-08-16T15:03:24.208Z | proof_recorded |  |  | stage_id=check:a9833a296abd8634; status=passed; cache_hit=False; input_fingerprint=fcd838fbfb73620308ab0a20566e45c562121fdaff31f07e79f15fa2183638c5 |
| 8880 | 2026-08-16T15:03:24.339Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:bcb9509776b8d535; input_fingerprint=b0234e11cad46c280ba83f6bdf62687bfc02148a15647d8cf4c3b6b8e2987b95 |
| 8881 | 2026-08-16T15:03:24.915Z | managed_process_admitted |  |  | owner=default |
| 8882 | 2026-08-16T15:03:25.158Z | managed_process_started |  |  | owner=default |
| 8883 | 2026-08-16T15:04:55.224Z | managed_process_terminal |  |  | owner=default |
| 8884 | 2026-08-16T15:04:55.491Z | proof_recorded |  |  | stage_id=check:bcb9509776b8d535; status=passed; cache_hit=False; input_fingerprint=b0234e11cad46c280ba83f6bdf62687bfc02148a15647d8cf4c3b6b8e2987b95 |
| 8885 | 2026-08-16T15:04:55.631Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:731a566acabcb042; input_fingerprint=95d60a886f4ba6f0b390b9fda9c079e34ab3b29d515f791b12c5dbab2c4b1b72 |
| 8886 | 2026-08-16T15:04:55.997Z | managed_process_admitted |  |  | owner=default |
| 8887 | 2026-08-16T15:04:56.224Z | managed_process_started |  |  | owner=default |
| 8888 | 2026-08-16T15:07:17.007Z | managed_process_terminal |  |  | owner=default |
| 8889 | 2026-08-16T15:07:17.260Z | proof_recorded |  |  | stage_id=check:731a566acabcb042; status=passed; cache_hit=False; input_fingerprint=95d60a886f4ba6f0b390b9fda9c079e34ab3b29d515f791b12c5dbab2c4b1b72 |
| 8890 | 2026-08-16T15:07:17.801Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 8891 | 2026-08-16T15:08:09.856Z | managed_process_admitted |  |  | owner=default |
| 8892 | 2026-08-16T15:08:10.075Z | managed_process_started |  |  | owner=default |
| 8893 | 2026-08-16T15:08:11.206Z | managed_process_terminal |  |  | owner=default |
| 8894 | 2026-08-16T15:08:20.275Z | managed_process_admitted |  |  | owner=default |
| 8895 | 2026-08-16T15:08:20.598Z | managed_process_started |  |  | owner=default |
| 8896 | 2026-08-16T15:08:21.742Z | managed_process_terminal |  |  | owner=default |
| 8897 | 2026-08-16T15:08:37.163Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 8898 | 2026-08-16T15:08:37.495Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:810e75f0d3dee10e | passed | c5f45ba74537e4b00648d3d02fd34837bc0dc414868625bac8612151e996b39c | False | 6197 | 0 |
| check:7fc03c251493acf9 | passed | 7a41b67df15b61a3c28087ada76140607bd3ad4628681ad483bef6fe7e68cc51 | False | 14004 | 0 |
| check:a9833a296abd8634 | passed | fcd838fbfb73620308ab0a20566e45c562121fdaff31f07e79f15fa2183638c5 | False | 59857 | 0 |
| check:bcb9509776b8d535 | passed | b0234e11cad46c280ba83f6bdf62687bfc02148a15647d8cf4c3b6b8e2987b95 | False | 90621 | 0 |
| check:731a566acabcb042 | passed | 95d60a886f4ba6f0b390b9fda9c079e34ab3b29d515f791b12c5dbab2c4b1b72 | False | 141348 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 629c67795f0048b3a1f85c7bed3a5a15 | accepted | 6b5d16e980058d51585f039eff918d938bbb66e9 | 1f317fb7dc607f9fb532243a904fb2cbd5bd3b5af1b0c99f9a088dc784d1c90a | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `61`
- Chain head: `fa3d5c9513ac34e06a5f218e6d7d0fab31e3a73b2babcf748a70859fce76e1c4`
