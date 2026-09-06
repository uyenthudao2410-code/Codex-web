# Orchestration Wave 5

- Run: `46ebec3dce7c4b4cb83ed3c503a1bdc8`
- Wave: `623448108a3343f8b610c8e701689d1f`
- Objective: G2 Wave 5 same-RUN closure on current settled HEAD 8697ace8204e7e3da55d250d4a52d9b2b930116c and source/worktree fingerprint 35ac1f2fa8f2d12a81dab8d03c90db81f8bb64430d5463980119892f2a736a96. Preserve all concurrent WIP and production behavior. Adopt only resources/coding-tools-mcp/tests/test_exception_group_boundary.py at exact SHA-256 912269c5fd0c87a34bddbf9010ba828215461785b697e281db8cf3d43e8a7408 with no source mutation. Wave 4 CHECK_FAILED was concretely diagnosed as Windows temp-tree cleanup contention during parallel cross-file Node test execution: behavioral recovery assertions were not the failure, isolated suspect case passed, and serial execution of the same three cases passed locally. Wave 5 therefore runs the same three Recovery-E2E cases serially with --test-concurrency=1, without weakening or changing assertions, then the focused regression, full test:all, module-size, diff-check, and exact target diff/hash gates. Reuse any earlier proof only if runtime proves exact current input-fingerprint identity. Stop on any HEAD, target, source fingerprint, authority, quiescence, or proof drift.
- Objective revision: `4`
- Objective SHA-256: `ca4b3fc1d6b0965785016a6d4e76adf6cd81503a93487324c327d27e208e52bc`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `8697ace8204e7e3da55d250d4a52d9b2b930116c`
- Worktree fingerprint: `35ac1f2fa8f2d12a81dab8d03c90db81f8bb64430d5463980119892f2a736a96`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 40124 | 2026-09-04T15:04:31.371Z | wave_replanned |  | PREFLIGHT | reason=Wave 4 CHECK_FAILED is now concretely attributed to cross-file Windows temp-tree cleanup contention under parallel Node test-file execution: the failing case exited on fs.rmSync/removeTempTree EPERM rather than a recovery assertion, 2/3 parallel cases passed, the suspect case alone subsequently passed and cleaned its temp tree, and all same three named cases passed when executed serially with --test-concurrency=1. This materially changes the proof strategy while the exact G2 target byte remains unchanged. Wave 5 binds the current settled source fingerprint and reruns Recovery-E2E serially first, then the remaining gates; no source behavior or assertion is weakened. |
| 40125 | 2026-09-04T15:04:31.543Z | observation_span_recorded |  |  |  |
| 40126 | 2026-09-04T15:04:31.801Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 40127 | 2026-09-04T15:04:31.989Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 40128 | 2026-09-04T15:04:32.174Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 40129 | 2026-09-04T15:04:32.307Z | state_transition | READY | ROUTED | reason=route_selected |
| 40130 | 2026-09-04T15:04:32.507Z | observation_span_recorded |  |  |  |
| 40131 | 2026-09-04T15:04:33.060Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=857fd73ea9a34de0868f3f23831fb1bd |
| 40132 | 2026-09-04T15:04:33.276Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 40133 | 2026-09-04T15:04:33.753Z | existing_file_adoption_observed |  |  |  |
| 40134 | 2026-09-04T15:04:33.961Z | observation_span_recorded |  |  |  |
| 40135 | 2026-09-04T15:04:34.274Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=857fd73ea9a34de0868f3f23831fb1bd |
| 40136 | 2026-09-04T15:04:34.641Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 40137 | 2026-09-04T15:04:35.250Z | proof_cache_miss |  |  | reason=cold; stage_id=check:da1175c5b08faf8a; input_fingerprint=a9d4151821d279b6d91a684d5e54f91c954a4d6d2a004a443b2f7c9f025cc16b |
| 40138 | 2026-09-04T15:04:35.574Z | managed_process_admitted |  |  | owner=default |
| 40139 | 2026-09-04T15:04:35.908Z | managed_process_started |  |  | owner=default |
| 40140 | 2026-09-04T15:04:53.458Z | managed_process_terminal |  |  | owner=default |
| 40141 | 2026-09-04T15:04:53.815Z | proof_recorded |  |  | stage_id=check:da1175c5b08faf8a; status=passed; cache_hit=False; input_fingerprint=a9d4151821d279b6d91a684d5e54f91c954a4d6d2a004a443b2f7c9f025cc16b |
| 40142 | 2026-09-04T15:04:53.984Z | proof_cache_miss |  |  | reason=cold; stage_id=check:fb09fb2911a48e48; input_fingerprint=c257f5caa558596aa50ef64bfaa034a9fd0c5571c7d5c58152acda6179b0df74 |
| 40143 | 2026-09-04T15:04:54.460Z | managed_process_admitted |  |  | owner=default |
| 40144 | 2026-09-04T15:04:54.826Z | managed_process_started |  |  | owner=default |
| 40145 | 2026-09-04T15:04:59.490Z | managed_process_terminal |  |  | owner=default |
| 40146 | 2026-09-04T15:04:59.908Z | proof_recorded |  |  | stage_id=check:fb09fb2911a48e48; status=passed; cache_hit=False; input_fingerprint=c257f5caa558596aa50ef64bfaa034a9fd0c5571c7d5c58152acda6179b0df74 |
| 40147 | 2026-09-04T15:05:00.090Z | proof_cache_miss |  |  | reason=cold; stage_id=check:535f1a87fc400c35; input_fingerprint=c88e2f0d8883ce13c9bdcaf6702bf85be3f134ac2ac084ff684de06982abfbbd |
| 40148 | 2026-09-04T15:05:00.461Z | managed_process_admitted |  |  | owner=default |
| 40149 | 2026-09-04T15:05:00.782Z | managed_process_started |  |  | owner=default |
| 40150 | 2026-09-04T15:12:54.179Z | managed_process_terminal |  |  | owner=default |
| 40151 | 2026-09-04T15:12:54.551Z | proof_recorded |  |  | stage_id=check:535f1a87fc400c35; status=passed; cache_hit=False; input_fingerprint=c88e2f0d8883ce13c9bdcaf6702bf85be3f134ac2ac084ff684de06982abfbbd |
| 40152 | 2026-09-04T15:12:54.780Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:80a1a46bd01d26a3; input_fingerprint=8d0b6150a1eebf3fc5954be36083e0413a12736e54ba38bdbf8216b690b897da |
| 40153 | 2026-09-04T15:12:55.205Z | managed_process_admitted |  |  | owner=default |
| 40154 | 2026-09-04T15:12:55.565Z | managed_process_started |  |  | owner=default |
| 40155 | 2026-09-04T15:12:55.993Z | managed_process_terminal |  |  | owner=default |
| 40156 | 2026-09-04T15:12:56.299Z | proof_recorded |  |  | stage_id=check:80a1a46bd01d26a3; status=passed; cache_hit=False; input_fingerprint=8d0b6150a1eebf3fc5954be36083e0413a12736e54ba38bdbf8216b690b897da |
| 40157 | 2026-09-04T15:12:56.445Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:466c2f308b48c766; input_fingerprint=3deb034639cbf68fe37c34834543516f4eb3719e12cb3350b85736317782c953 |
| 40158 | 2026-09-04T15:12:56.777Z | managed_process_admitted |  |  | owner=default |
| 40159 | 2026-09-04T15:12:57.088Z | managed_process_started |  |  | owner=default |
| 40160 | 2026-09-04T15:12:58.285Z | managed_process_terminal |  |  | owner=default |
| 40161 | 2026-09-04T15:12:58.549Z | proof_recorded |  |  | stage_id=check:466c2f308b48c766; status=passed; cache_hit=False; input_fingerprint=3deb034639cbf68fe37c34834543516f4eb3719e12cb3350b85736317782c953 |
| 40162 | 2026-09-04T15:12:58.795Z | proof_cache_miss |  |  | reason=cold; stage_id=check:8856fe3f0b72564c; input_fingerprint=199e46ed9d8c53acd9201d6c6d5740c37c365e0f42e73525ec1155986e237d4f |
| 40163 | 2026-09-04T15:12:59.195Z | managed_process_admitted |  |  | owner=default |
| 40164 | 2026-09-04T15:12:59.446Z | managed_process_started |  |  | owner=default |
| 40165 | 2026-09-04T15:13:00.116Z | managed_process_terminal |  |  | owner=default |
| 40166 | 2026-09-04T15:13:00.472Z | proof_recorded |  |  | stage_id=check:8856fe3f0b72564c; status=passed; cache_hit=False; input_fingerprint=199e46ed9d8c53acd9201d6c6d5740c37c365e0f42e73525ec1155986e237d4f |
| 40167 | 2026-09-04T15:13:00.654Z | observation_span_recorded |  |  |  |
| 40168 | 2026-09-04T15:13:00.860Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 40169 | 2026-09-04T15:26:18.231Z | managed_process_admitted |  |  | owner=chatweb-g2-wave5-final-preflight |
| 40170 | 2026-09-04T15:26:18.555Z | managed_process_started |  |  | owner=chatweb-g2-wave5-final-preflight |
| 40171 | 2026-09-04T15:26:19.073Z | managed_process_terminal |  |  | owner=chatweb-g2-wave5-final-preflight |
| 40172 | 2026-09-04T15:26:53.187Z | quality_outcome_recorded |  |  |  |
| 40173 | 2026-09-04T15:26:53.390Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 40174 | 2026-09-04T15:26:53.661Z | observation_span_recorded |  |  |  |
| 40175 | 2026-09-04T15:26:53.908Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:da1175c5b08faf8a | passed | a9d4151821d279b6d91a684d5e54f91c954a4d6d2a004a443b2f7c9f025cc16b | False | 18212 | 0 |
| check:fb09fb2911a48e48 | passed | c257f5caa558596aa50ef64bfaa034a9fd0c5571c7d5c58152acda6179b0df74 | False | 5466 | 0 |
| check:535f1a87fc400c35 | passed | c88e2f0d8883ce13c9bdcaf6702bf85be3f134ac2ac084ff684de06982abfbbd | False | 474145 | 0 |
| check:80a1a46bd01d26a3 | passed | 8d0b6150a1eebf3fc5954be36083e0413a12736e54ba38bdbf8216b690b897da | False | 1110 | 0 |
| check:466c2f308b48c766 | passed | 3deb034639cbf68fe37c34834543516f4eb3719e12cb3350b85736317782c953 | False | 1682 | 0 |
| check:8856fe3f0b72564c | passed | 199e46ed9d8c53acd9201d6c6d5740c37c365e0f42e73525ec1155986e237d4f | False | 1305 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| bf188b4106c9465196549d9e91f92818 | accepted | 8697ace8204e7e3da55d250d4a52d9b2b930116c | f0ed75e90295fbc734eba2dfe8d96b48abcb117612b804e39266d41a14ac3996 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `183`
- Chain head: `caab9385981a9d5463256d69b81b22c011156d1dfafcff04b6eee2cce6d10fc2`
