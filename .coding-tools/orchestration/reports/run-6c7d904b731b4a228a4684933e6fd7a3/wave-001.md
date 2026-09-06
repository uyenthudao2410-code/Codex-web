# Orchestration Wave 1

- Run: `6c7d904b731b4a228a4684933e6fd7a3`
- Wave: `b830e33c0391497f9eef5e788cee2126`
- Objective: Adopt and prove exactly the four reviewed pre-existing release-harness files on main at base HEAD ef5aa3b74f91b5f5167f002b27a04e43c895180f. Do not modify their bytes. Run only the requested bounded proof: Node syntax checks for the three JavaScript files, node --test tests/build-verification.test.js, and npm run test:recovery:installed against the current dist/coding-tools-mcp-setup-1.0.0.exe. The installed harness must preserve the production recovery descriptor and Scheduled Task. Do not touch the two 260905 research docs or unrelated source/evidence; no commit/push/restart/release/publish/tag/deploy/experiments/cohorts/stale reconciliation/report ACK.
- Objective revision: `1`
- Objective SHA-256: `78bd5476dedf4da10defc904e966027d0282061e6f216e66deae86615a8f8d22`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `ef5aa3b74f91b5f5167f002b27a04e43c895180f`
- Worktree fingerprint: `76ccaeec1f14fd1a27221ced37386f8b495dfc6743ae9b5fd01f104c5f39ca72`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 42107 | 2026-09-06T09:57:41.783Z | run_started |  | PREFLIGHT |  |
| 42108 | 2026-09-06T09:57:42.165Z | observation_span_recorded |  |  |  |
| 42109 | 2026-09-06T09:57:42.335Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 42110 | 2026-09-06T09:57:42.605Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 42111 | 2026-09-06T09:57:42.830Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 42112 | 2026-09-06T09:57:43.037Z | state_transition | READY | ROUTED | reason=route_selected |
| 42113 | 2026-09-06T09:57:43.247Z | observation_span_recorded |  |  |  |
| 42114 | 2026-09-06T09:57:44.101Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=904ea2ac958040a08f06a49fa987192a |
| 42115 | 2026-09-06T09:57:44.313Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 42116 | 2026-09-06T09:57:45.114Z | existing_file_adoption_observed |  |  |  |
| 42117 | 2026-09-06T09:57:45.360Z | observation_span_recorded |  |  |  |
| 42118 | 2026-09-06T09:57:45.682Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=904ea2ac958040a08f06a49fa987192a |
| 42119 | 2026-09-06T09:57:45.855Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 42120 | 2026-09-06T09:57:46.663Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:719395034be5a3ca; input_fingerprint=089839a235607e2cb833f0d04102a835a7ea13649bdeec2ff49724186b8930d7 |
| 42121 | 2026-09-06T09:57:47.157Z | managed_process_admitted |  |  | owner=default |
| 42122 | 2026-09-06T09:57:47.456Z | managed_process_started |  |  | owner=default |
| 42123 | 2026-09-06T09:57:47.906Z | managed_process_terminal |  |  | owner=default |
| 42124 | 2026-09-06T09:57:48.313Z | proof_recorded |  |  | stage_id=check:719395034be5a3ca; status=passed; cache_hit=False; input_fingerprint=089839a235607e2cb833f0d04102a835a7ea13649bdeec2ff49724186b8930d7 |
| 42125 | 2026-09-06T09:57:48.535Z | proof_cache_miss |  |  | reason=cold; stage_id=check:89c42cc96b3eb71c; input_fingerprint=b2506534a53aba1a072935bf4c4aef116d67bb825b7a3c693676ed0ee5b86237 |
| 42126 | 2026-09-06T09:57:48.981Z | managed_process_admitted |  |  | owner=default |
| 42127 | 2026-09-06T09:57:49.260Z | managed_process_started |  |  | owner=default |
| 42128 | 2026-09-06T09:57:49.732Z | managed_process_terminal |  |  | owner=default |
| 42129 | 2026-09-06T09:57:50.129Z | proof_recorded |  |  | stage_id=check:89c42cc96b3eb71c; status=passed; cache_hit=False; input_fingerprint=b2506534a53aba1a072935bf4c4aef116d67bb825b7a3c693676ed0ee5b86237 |
| 42130 | 2026-09-06T09:57:50.340Z | proof_cache_miss |  |  | reason=cold; stage_id=check:bdda12fe7067ef68; input_fingerprint=cddb9f73a0577c872710257ff3dd4949dd5bb80a72059b647fec67826f03073c |
| 42131 | 2026-09-06T09:57:50.802Z | managed_process_admitted |  |  | owner=default |
| 42132 | 2026-09-06T09:57:51.121Z | managed_process_started |  |  | owner=default |
| 42133 | 2026-09-06T09:57:51.581Z | managed_process_terminal |  |  | owner=default |
| 42134 | 2026-09-06T09:57:51.921Z | proof_recorded |  |  | stage_id=check:bdda12fe7067ef68; status=passed; cache_hit=False; input_fingerprint=cddb9f73a0577c872710257ff3dd4949dd5bb80a72059b647fec67826f03073c |
| 42135 | 2026-09-06T09:57:52.154Z | proof_cache_miss |  |  | reason=cold; stage_id=check:c258b46a1eabc99b; input_fingerprint=ed8427a879e26caa76dc4f294f8c02c42cb979e4f57d4e3a5f28bd77ce3b95ed |
| 42136 | 2026-09-06T09:57:52.515Z | managed_process_admitted |  |  | owner=default |
| 42137 | 2026-09-06T09:57:52.836Z | managed_process_started |  |  | owner=default |
| 42138 | 2026-09-06T09:57:53.373Z | managed_process_terminal |  |  | owner=default |
| 42139 | 2026-09-06T09:57:53.722Z | proof_recorded |  |  | stage_id=check:c258b46a1eabc99b; status=passed; cache_hit=False; input_fingerprint=ed8427a879e26caa76dc4f294f8c02c42cb979e4f57d4e3a5f28bd77ce3b95ed |
| 42140 | 2026-09-06T09:57:53.902Z | proof_cache_miss |  |  | reason=cold; stage_id=check:2c01020283f3fd63; input_fingerprint=2a54569cff47617d1995e7a210bc60612cf0607635b65adb9b7f442af717fbf9 |
| 42141 | 2026-09-06T09:57:54.307Z | managed_process_admitted |  |  | owner=default |
| 42142 | 2026-09-06T09:57:54.608Z | managed_process_started |  |  | owner=default |
| 42143 | 2026-09-06T09:58:16.369Z | managed_process_terminal |  |  | owner=default |
| 42144 | 2026-09-06T09:58:16.713Z | proof_recorded |  |  | stage_id=check:2c01020283f3fd63; status=passed; cache_hit=False; input_fingerprint=2a54569cff47617d1995e7a210bc60612cf0607635b65adb9b7f442af717fbf9 |
| 42145 | 2026-09-06T09:58:16.952Z | observation_span_recorded |  |  |  |
| 42146 | 2026-09-06T09:58:17.140Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 42147 | 2026-09-06T09:58:44.200Z | quality_outcome_recorded |  |  |  |
| 42148 | 2026-09-06T09:58:44.454Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 42149 | 2026-09-06T09:58:44.694Z | observation_span_recorded |  |  |  |
| 42150 | 2026-09-06T09:58:44.914Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:719395034be5a3ca | passed | 089839a235607e2cb833f0d04102a835a7ea13649bdeec2ff49724186b8930d7 | False | 1224 | 0 |
| check:89c42cc96b3eb71c | passed | b2506534a53aba1a072935bf4c4aef116d67bb825b7a3c693676ed0ee5b86237 | False | 1241 | 0 |
| check:bdda12fe7067ef68 | passed | cddb9f73a0577c872710257ff3dd4949dd5bb80a72059b647fec67826f03073c | False | 1202 | 0 |
| check:c258b46a1eabc99b | passed | ed8427a879e26caa76dc4f294f8c02c42cb979e4f57d4e3a5f28bd77ce3b95ed | False | 1255 | 0 |
| check:2c01020283f3fd63 | passed | 2a54569cff47617d1995e7a210bc60612cf0607635b65adb9b7f442af717fbf9 | False | 22443 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| e5673e0ded354257a7c3309dfc1691b0 | accepted | ef5aa3b74f91b5f5167f002b27a04e43c895180f | 26ff5ae50c7c0ec476c0cae67e605a8b102c900373687df9f5f3e55d7a51e65a | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `44`
- Chain head: `567a8b099b491e607dcbd5c28664719132a5b3793c18eefa27c1de5a14f24bda`
