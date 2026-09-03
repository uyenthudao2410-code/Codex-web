# Orchestration Wave 2

- Run: `21a41bfdbfc44192a82bc10c25e7eefe`
- Wave: `46c2e05e07604ea68f4f928dde32ce68`
- Objective: Continue exact RUN 21a41bfdbfc44192a82bc10c25e7eefe from REPLAN without creating a new RUN. First verify the recovered six-file adoption anchors still match their supplied SHA-256; if any byte drifted, fail closed and report current bytes/hash without overwriting concurrent work. Then implement the smallest coherent fix for all changed evidence: (1) one Python authority for current host observation schema v6, with v1-v5 legacy and excluded from current percentiles/correlation; update current fixtures to v6 while preserving a separate v5 legacy event plus v6 current event; (2) in chatEvaluationJournal structured usage discovery traverse only explicit allowlisted response-envelope keys required to find response.completed/response, never generic Object.values or arbitrary arrays through message/output/content, and collect numeric usage only without persisting prompt, response, content, or chain-of-thought; wrapper JSON.parse/Response.json instrumentation must not accumulate, must stable-dedupe, and must restore correctly on dispose; (3) controller_usage_ingress must reject implicit-default, partial, mismatched, or spoofed controller provenance before ledger mutation while preserving the valid Electron host bridge/auth contract; (4) Electron receipt and ingress must exact-match authoritative RUN/WAVE/turn/trace identity when present, rejecting mismatch, incomplete identity, unsafe integer, and duplicate conflict while preserving unknown-not-zero and idempotent duplicate semantics; (5) CHECKPOINTED post-turn ingestion is valid only for the exact current wave and while the same controller 60-second lease is actively valid, with tests for expiry and wave/identity mismatch; (6) preserve public smart-v3 exactly 8 tools and unrelated dirty work. The six adopted files are anchors, not a restriction: modify additional files only from the explicitly allowed evidence_completeness.py, usage_events.py, test_evaluation_report.py, test_evidence_completeness.py, test_stateless_http_2026.py, or a directly necessary shared-constant/test file, and only when causally required. Run fresh proof on exact final bytes: root `git diff --check -- <actual changed packet>`; root `node --test tests/chat-evaluation-journal.test.js`; from resources/coding-tools-mcp run `python -m pytest -q tests/test_controller_usage_post_turn.py tests/test_evaluation_report.py tests/test_evidence_completeness.py tests/test_stateless_http_2026.py tests/test_usage_accounting_v2.py tests/test_accepted_result_economics_report.py`. Perform semantic review against all invariants. If any defect remains, return REPLAN evidence; if all pass, leave this same new wave ready for final ACCEPTING/acceptance with exact actual changed paths and hashes. Do not restart runtime, commit, push, tag, package, publish, release, deploy, reset, clean, kill, or adopt a live managed process.
- Objective revision: `2`
- Objective SHA-256: `6d4f982a3bf5d8935ed3a4e583e861f4ba6e9e435301a20783100de01bdf22df`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `753839c6ce2254b680f3440b0e6ab8143dd0735633ca8b86f31b93e887b11779`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 36737 | 2026-09-03T08:47:04.152Z | wave_replanned |  | PREFLIGHT | reason=Adopt the exact current bytes of the recovered six-file capsule and replace stale proof v8 with fresh exact-byte proof. Close the separately verified v6 host-observation, allowlisted numeric-only traversal, strict controller provenance/RUN-WAVE-turn-trace correlation, and same-wave active-lease CHECKPOINTED ingress gaps. Preserve unrelated dirty work. |
| 36738 | 2026-09-03T08:47:04.461Z | observation_span_recorded |  |  |  |
| 36739 | 2026-09-03T08:47:27.130Z | observation_span_recorded |  |  |  |
| 36740 | 2026-09-03T08:47:27.508Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 36741 | 2026-09-03T08:47:27.752Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 36742 | 2026-09-03T08:47:27.969Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 36743 | 2026-09-03T08:47:28.208Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 36744 | 2026-09-03T08:47:28.432Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 36745 | 2026-09-03T08:47:28.688Z | state_transition | READY | ROUTED | reason=route_selected |
| 36746 | 2026-09-03T08:47:29.036Z | observation_span_recorded |  |  |  |
| 36747 | 2026-09-03T08:47:30.364Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=e7ab5d8702844a778dbfe69a4da99e42 |
| 36748 | 2026-09-03T08:47:30.640Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 36749 | 2026-09-03T08:47:33.168Z | existing_file_adoption_observed |  |  |  |
| 36750 | 2026-09-03T08:47:33.447Z | observation_span_recorded |  |  |  |
| 36751 | 2026-09-03T08:47:33.889Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=e7ab5d8702844a778dbfe69a4da99e42 |
| 36752 | 2026-09-03T08:47:34.153Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 36753 | 2026-09-03T08:47:35.411Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:all; input_fingerprint=cbe40e29be7a9b9ecbd4a7824a4c0a72648a868b1fca88f9ad9b8c2c6a3c118b |
| 36754 | 2026-09-03T08:47:36.152Z | managed_process_admitted |  |  | owner=default |
| 36755 | 2026-09-03T08:47:36.632Z | managed_process_started |  |  | owner=default |
| 36756 | 2026-09-03T08:48:54.823Z | managed_process_terminal |  |  | owner=default |
| 36757 | 2026-09-03T08:48:55.566Z | managed_process_admitted |  |  | owner=default |
| 36758 | 2026-09-03T08:48:56.071Z | managed_process_started |  |  | owner=default |
| 36759 | 2026-09-03T08:51:04.917Z | managed_process_terminal |  |  | owner=default |
| 36760 | 2026-09-03T08:51:08.963Z | proof_recorded |  |  | stage_id=verify:all; status=passed; cache_hit=False; input_fingerprint=cbe40e29be7a9b9ecbd4a7824a4c0a72648a868b1fca88f9ad9b8c2c6a3c118b |
| 36761 | 2026-09-03T08:51:09.592Z | observation_span_recorded |  |  |  |
| 36762 | 2026-09-03T08:51:10.772Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 36763 | 2026-09-03T08:51:33.767Z | observation_span_recorded |  |  |  |
| 36764 | 2026-09-03T08:51:34.006Z | failure_observed | ACCEPTING | ACCEPTING | reason=Wave proof is invalid for final acceptance because automatic verification ran out-of-scope commands `npm run test` and `npm run dist`; the latter created build/package artifacts under dist/win-unpacked before being terminated by supported command_control. Preserve all generated artifacts untouched and exclude them from acceptance. Replace proof 1fd4dee62a314933a4de93c6110e36df with fresh proof using only the operator-approved three commands, preserving current source bytes and unrelated dirty work.; failure_class=SOL_REJECTED |
| 36765 | 2026-09-03T08:51:34.230Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 36766 | 2026-09-03T08:51:34.476Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:all | passed | cbe40e29be7a9b9ecbd4a7824a4c0a72648a868b1fca88f9ad9b8c2c6a3c118b | False | 213000 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `477`
- Chain head: `d5d92b6a865dd8405169addd711fceac1741f551a0ecc3cbbc612370d70344c6`
