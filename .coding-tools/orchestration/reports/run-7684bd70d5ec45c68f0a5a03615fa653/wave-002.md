# Orchestration Wave 2

- Run: `7684bd70d5ec45c68f0a5a03615fa653`
- Wave: `e8bd790c2ecc4aeb9f45c736c7a2b772`
- Objective: Terminal C5 closure after historical prior-artifact reproduction was truthfully blocked. Continue the same historical C5 RUN after Wave 3618a4ff5cc4417ab52ea48ee0856d92 CHECK_FAILED: the external worktree at exact prior commit 026f79b3ab5997cb15f38a3b41769da6a79d790b was created and npm ci --offline passed, but the repository-supported npm run dist stopped at npm test with 259 tests / 251 pass / 8 fail, all in recovery-supervisor.test.js, before electron-builder ran. Do not bypass tests or build a synthetic prior installer. Upgrade and rollback remain NOT_PROVEN also because no disposable Windows sandbox exists and the prior/current packages share appId com.gptwebcodex.assistant while a real legacy Start Menu shortcut SHA256 393337c654c77795dad8a847a259391364635ed058e75603314b8321200c5957 must remain untouched. Record the exact blocker under the existing C5 temp evidence, remove only the external historical worktree created by C5, and prove final invariants: current HEAD/origin remain 9e752e34db745cd4fb2d0830a517910eced9c37f, current verified installer hash remains e7e91a4340fb388d36f6e24d5b7b58dbd697142b1f3b3fd1a392477d0ed9a440, C5 install root/current registry/current shortcuts/current C5 install processes are absent after the already accepted current lifecycle, the legacy shortcut remains byte-identical, production descriptor identity/hash and Recovery Supervisor task remain equal to the C5 baseline, and all C5 profile/evidence remains retained. Final classification must explicitly preserve current clean silent install/uninstall + isolated descriptor/process/listener proof as PASS, authenticated loopback recovery.ping/status as BLOCKED_BY_SERVER_POLICY, prior artifact as NOT_PRODUCED, and upgrade/rollback as NOT_PROVEN. No C4 rerun, no installer execution, no normal UI, no production/startup/task writes, no network, no source mutation, no publish/tag/release/deploy, and never ACK the forbidden report.
- Objective revision: `2`
- Objective SHA-256: `3fb524d13ec12b69d805435f172a2e722d328c8a542b55b1091e509b94374607`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `9e752e34db745cd4fb2d0830a517910eced9c37f`
- Worktree fingerprint: `6546f235f77e31e7b47a1f6c568d1f6291fec2c3fce76edc6b85030cc9b5259e`
- Contract fingerprint: `7d952928e7a108a2de650bdde55d1604c48fc20cd333a964cefa8701b825693e`
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 41776 | 2026-09-06T06:04:02.810Z | wave_replanned |  | PREFLIGHT | reason=Historical Wave 3618a4ff5cc4417ab52ea48ee0856d92 established changed evidence: exact prior worktree creation PASS (proof c9f9867b4bbc402f8913dcbff3c3f41e), npm ci --offline PASS (proof 9160ac6553054f3789de671766ace1ce), and repository-supported npm run dist FAIL (proof 433fc54459e746b18853dade99b8d2e0) because 8 Recovery Supervisor tests failed out of 259 before electron-builder ran. The new strategy does not retry or bypass tests; it terminalizes C5 with an explicit prior-artifact/upgrade/rollback blocker, cleans only the C5-created external worktree, and re-proves final invariants. |
| 41777 | 2026-09-06T06:04:03.047Z | observation_span_recorded |  |  |  |
| 41778 | 2026-09-06T06:04:04.694Z | observation_span_recorded |  |  |  |
| 41779 | 2026-09-06T06:04:04.907Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 41780 | 2026-09-06T06:04:05.130Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 41781 | 2026-09-06T06:04:05.296Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 41782 | 2026-09-06T06:04:05.506Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 41783 | 2026-09-06T06:04:05.746Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 41784 | 2026-09-06T06:04:05.971Z | state_transition | READY | ROUTED | reason=route_selected |
| 41785 | 2026-09-06T06:04:06.242Z | observation_span_recorded |  |  |  |
| 41786 | 2026-09-06T06:04:07.265Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=2a7ec7b57ed046d29428177062fda377 |
| 41787 | 2026-09-06T06:04:07.543Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 41788 | 2026-09-06T06:04:08.492Z | observation_span_recorded |  |  |  |
| 41789 | 2026-09-06T06:04:08.806Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=2a7ec7b57ed046d29428177062fda377 |
| 41790 | 2026-09-06T06:04:08.990Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 41791 | 2026-09-06T06:04:09.934Z | proof_cache_miss |  |  | reason=cold; stage_id=check:a138d3d3991a2faf; input_fingerprint=1410721598e7b354465a84d3d438020679c6eb6e4acdcfd061776e02b4685051 |
| 41792 | 2026-09-06T06:04:10.352Z | managed_process_admitted |  |  | owner=default |
| 41793 | 2026-09-06T06:04:10.714Z | managed_process_started |  |  | owner=default |
| 41794 | 2026-09-06T06:04:12.073Z | managed_process_terminal |  |  | owner=default |
| 41795 | 2026-09-06T06:04:12.465Z | proof_recorded |  |  | stage_id=check:a138d3d3991a2faf; status=passed; cache_hit=False; input_fingerprint=1410721598e7b354465a84d3d438020679c6eb6e4acdcfd061776e02b4685051 |
| 41796 | 2026-09-06T06:04:12.684Z | proof_cache_miss |  |  | reason=cold; stage_id=check:ff53c087086ef59a; input_fingerprint=8e58fd1fd3a357d214ccbaac6493a7f343e8395323651ef945a371bb4118c02e |
| 41797 | 2026-09-06T06:04:12.956Z | managed_process_admitted |  |  | owner=default |
| 41798 | 2026-09-06T06:04:13.361Z | managed_process_started |  |  | owner=default |
| 41799 | 2026-09-06T06:04:16.566Z | managed_process_terminal |  |  | owner=default |
| 41800 | 2026-09-06T06:04:16.970Z | proof_recorded |  |  | stage_id=check:ff53c087086ef59a; status=passed; cache_hit=False; input_fingerprint=8e58fd1fd3a357d214ccbaac6493a7f343e8395323651ef945a371bb4118c02e |
| 41801 | 2026-09-06T06:04:17.154Z | proof_cache_miss |  |  | reason=cold; stage_id=check:1c659014b1313aa1; input_fingerprint=eefb2e3fe0f9fbbeb8922674402d0e9cc32cd5f2698aa71137833a778c1c5d64 |
| 41802 | 2026-09-06T06:04:17.870Z | managed_process_admitted |  |  | owner=default |
| 41803 | 2026-09-06T06:04:18.175Z | managed_process_started |  |  | owner=default |
| 41804 | 2026-09-06T06:04:20.434Z | managed_process_terminal |  |  | owner=default |
| 41805 | 2026-09-06T06:04:20.875Z | proof_recorded |  |  | stage_id=check:1c659014b1313aa1; status=passed; cache_hit=False; input_fingerprint=eefb2e3fe0f9fbbeb8922674402d0e9cc32cd5f2698aa71137833a778c1c5d64 |
| 41806 | 2026-09-06T06:04:21.109Z | observation_span_recorded |  |  |  |
| 41807 | 2026-09-06T06:04:21.323Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 41808 | 2026-09-06T06:04:34.929Z | quality_outcome_recorded |  |  |  |
| 41809 | 2026-09-06T06:04:35.146Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 41810 | 2026-09-06T06:04:35.460Z | observation_span_recorded |  |  |  |
| 41811 | 2026-09-06T06:04:35.696Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:a138d3d3991a2faf | passed | 1410721598e7b354465a84d3d438020679c6eb6e4acdcfd061776e02b4685051 | False | 2086 | 0 |
| check:ff53c087086ef59a | passed | 8e58fd1fd3a357d214ccbaac6493a7f343e8395323651ef945a371bb4118c02e | False | 3896 | 0 |
| check:1c659014b1313aa1 | passed | eefb2e3fe0f9fbbeb8922674402d0e9cc32cd5f2698aa71137833a778c1c5d64 | False | 3356 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| f549bc0102e24c028c07e9ad48c034a7 | accepted | 9e752e34db745cd4fb2d0830a517910eced9c37f | 8cdbebc9f4796a5d0d324214f7656aa3e5d433f9feb27402c0f2861fb6243b80 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `70`
- Chain head: `2673ebda23130a050414a5f0813b71cd51f7d7274ff913d95f592f9674d45129`
