# Orchestration Wave 1

- Run: `143c13264fc642228619533a13ea38ff`
- Wave: `606d17e73be448adb4dd8b9db8905fc9`
- Objective: Continue canonical RUN 321da27a9dd24556abd9e7da8632d0eb / WAVE 59aae429531941aeb09c9d7831203511. The smallest causal fixture correction is already present in the worktree: production coordination.py remains exact unchanged bytes; test_operator_report_isolation.py now directly edits the temporary backing TaskStateStore under its lock because public update intentionally cannot clear an issued report latch. Do not patch again. Exact-byte adopt only these two current files into this wave, preserving all other dirty work. Run the single regression once; only if it passes run the exact focused operator_report/exact_run group. No broader proof, no restart, no commit/push/release/deploy.
- Objective revision: `1`
- Objective SHA-256: `3d9f610c4dec3d6efa5bc9b504a1441b127025b15cfab00f795086deada63a3d`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `0bfdfcc495e703e0ca6f14ab181d6a5c3f8d4c863966e592bbcf94a2b1cd8fe9`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 35651 | 2026-09-02T08:08:05.845Z | run_started |  | PREFLIGHT |  |
| 35652 | 2026-09-02T08:08:06.200Z | observation_span_recorded |  |  |  |
| 35653 | 2026-09-02T08:08:06.413Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 35654 | 2026-09-02T08:08:06.577Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 35655 | 2026-09-02T08:08:06.785Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 35656 | 2026-09-02T08:08:06.952Z | state_transition | READY | ROUTED | reason=route_selected |
| 35657 | 2026-09-02T08:08:07.149Z | observation_span_recorded |  |  |  |
| 35658 | 2026-09-02T08:08:08.060Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=1174cfcf3feb40d6a4342550877c6fb3 |
| 35659 | 2026-09-02T08:08:08.223Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 35660 | 2026-09-02T08:08:09.038Z | existing_file_adoption_observed |  |  |  |
| 35661 | 2026-09-02T08:08:09.212Z | observation_span_recorded |  |  |  |
| 35662 | 2026-09-02T08:08:09.509Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=1174cfcf3feb40d6a4342550877c6fb3 |
| 35663 | 2026-09-02T08:08:09.693Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 35664 | 2026-09-02T08:08:10.500Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:205a9c5f7702557c; input_fingerprint=b30dd2a5cc0a9aa77d27112bcfb505ca52bd69e2d575f37d96ef1c50a4b2bdd5 |
| 35665 | 2026-09-02T08:08:10.908Z | managed_process_admitted |  |  | owner=default |
| 35666 | 2026-09-02T08:08:11.243Z | managed_process_started |  |  | owner=default |
| 35667 | 2026-09-02T08:08:14.817Z | managed_process_terminal |  |  | owner=default |
| 35668 | 2026-09-02T08:08:15.149Z | proof_recorded |  |  | stage_id=check:205a9c5f7702557c; status=passed; cache_hit=False; input_fingerprint=b30dd2a5cc0a9aa77d27112bcfb505ca52bd69e2d575f37d96ef1c50a4b2bdd5 |
| 35669 | 2026-09-02T08:08:15.354Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=22ecbc0de06bc5c4afc22ef2ecba7c44071e9992cfecbcd66deb5ef5dfca73bd |
| 35670 | 2026-09-02T08:08:15.914Z | managed_process_admitted |  |  | owner=default |
| 35671 | 2026-09-02T08:08:16.246Z | managed_process_started |  |  | owner=default |
| 35672 | 2026-09-02T08:08:33.481Z | managed_process_terminal |  |  | owner=default |
| 35673 | 2026-09-02T08:08:34.675Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=22ecbc0de06bc5c4afc22ef2ecba7c44071e9992cfecbcd66deb5ef5dfca73bd |
| 35674 | 2026-09-02T08:08:34.944Z | observation_span_recorded |  |  |  |
| 35675 | 2026-09-02T08:08:35.161Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 35676 | 2026-09-02T08:20:50.315Z | observation_span_recorded |  |  |  |
| 35677 | 2026-09-02T08:20:50.494Z | failure_observed | ACCEPTING | ACCEPTING | reason=Reject to REPLAN because RUN 143c13264fc642228619533a13ea38ff is an unintended replacement lineage. Its green proofs must not substitute for the authorized canonical repair lineage RUN 321da27a9dd24556abd9e7da8632d0eb. Preserve source; do not accept, stop, adopt, or force-release this run.; failure_class=SOL_REJECTED |
| 35678 | 2026-09-02T08:20:50.703Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 35679 | 2026-09-02T08:20:50.890Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 35680 | 2026-09-02T08:50:44.165Z | state_transition | REPLAN | ABORTED | reason=task_stopped |
| 35681 | 2026-09-02T08:50:44.629Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:205a9c5f7702557c | passed | b30dd2a5cc0a9aa77d27112bcfb505ca52bd69e2d575f37d96ef1c50a4b2bdd5 | False | 4295 | 0 |
| verify:tests | passed | 22ecbc0de06bc5c4afc22ef2ecba7c44071e9992cfecbcd66deb5ef5dfca73bd | False | 18750 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `31`
- Chain head: `ea32ebcb08e93e090f71e688a192b5762c8b9bc6eab3d720eb00de1ca063b4f9`
