# Orchestration Wave 5

- Run: `22375c46b4264d0b828570a880263d4d`
- Wave: `8fb0946c6c7040efabd9562fb4209efe`
- Objective: Finish the authorized-root end-to-end regression by registering the synthetic ChatWeb controller client in the same authorized workspace ledger before the public agent_workflow call, then prove the complete multi-workspace boundary.
- Objective revision: `5`
- Objective SHA-256: `5c8c4cdb34e4cfb7cb7c32b4eb0b26f641c4a59127d76b6d5a1ed179ececad09`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `2cc0eefc7d881827ef44e4d1584d84bbd9e494b6`
- Worktree fingerprint: `5a32710e8e854521f61c40ebab0f2c19d1c725e444f1ffa03c64efccf9bda1e8`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 32150 | 2026-08-28T10:26:24.326Z | wave_replanned |  | PREFLIGHT | reason=Fresh retained traceback shows the sole failure is fixture setup: the synthetic ChatWeb identity is assigned to request_context but never upserted into the authorized workspace Execution Hub ledger, so controller claim fails closed with 'controller client is not registered'. Existing restart-isolation fixtures establish the correct pattern: temporarily bind request_context.workspace_root to the authorized root, call _touch_hub_client(identity), then clear the temporary root before public dispatch. |
| 32151 | 2026-08-28T10:26:24.592Z | observation_span_recorded |  |  |  |
| 32152 | 2026-08-28T10:26:24.807Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 32153 | 2026-08-28T10:26:25.049Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 32154 | 2026-08-28T10:26:25.264Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 32155 | 2026-08-28T10:26:25.493Z | state_transition | READY | ROUTED | reason=route_selected |
| 32156 | 2026-08-28T10:26:25.742Z | observation_span_recorded |  |  |  |
| 32157 | 2026-08-28T10:26:26.403Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=5baf6e9cb1424b08838ab45c71aac2d3 |
| 32158 | 2026-08-28T10:26:26.626Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 32159 | 2026-08-28T10:26:27.154Z | patch_surface_observed |  |  |  |
| 32160 | 2026-08-28T10:26:27.400Z | observation_span_recorded |  |  |  |
| 32161 | 2026-08-28T10:26:27.782Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=5baf6e9cb1424b08838ab45c71aac2d3 |
| 32162 | 2026-08-28T10:26:28.000Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 32163 | 2026-08-28T10:26:28.706Z | proof_cache_miss |  |  | reason=cold; stage_id=check:21d3dc42049a8778; input_fingerprint=ff49dee6a7ee3bc2c6cf8bf686b4059a979d4218beb7b35c8e35edb435bfc15a |
| 32164 | 2026-08-28T10:26:29.246Z | managed_process_admitted |  |  | owner=default |
| 32165 | 2026-08-28T10:26:29.613Z | managed_process_started |  |  | owner=default |
| 32166 | 2026-08-28T10:26:49.439Z | managed_process_terminal |  |  | owner=default |
| 32167 | 2026-08-28T10:26:50.042Z | proof_recorded |  |  | stage_id=check:21d3dc42049a8778; status=passed; cache_hit=False; input_fingerprint=ff49dee6a7ee3bc2c6cf8bf686b4059a979d4218beb7b35c8e35edb435bfc15a |
| 32168 | 2026-08-28T10:26:50.255Z | proof_cache_miss |  |  | reason=cold; stage_id=check:aa6d7c839a151f3f; input_fingerprint=83b45dd941afa9489f6b2542353e0c75eabacb8137c4bca8be81ad123df118b4 |
| 32169 | 2026-08-28T10:26:50.781Z | managed_process_admitted |  |  | owner=default |
| 32170 | 2026-08-28T10:26:51.445Z | managed_process_started |  |  | owner=default |
| 32171 | 2026-08-28T10:26:53.289Z | managed_process_terminal |  |  | owner=default |
| 32172 | 2026-08-28T10:26:53.799Z | proof_recorded |  |  | stage_id=check:aa6d7c839a151f3f; status=passed; cache_hit=False; input_fingerprint=83b45dd941afa9489f6b2542353e0c75eabacb8137c4bca8be81ad123df118b4 |
| 32173 | 2026-08-28T10:26:54.024Z | proof_cache_miss |  |  | reason=cold; stage_id=check:1b0f8612837dd33d; input_fingerprint=f0fff84208cd2b2eabb7d090fd92d11c94100437578a42226330330723ac1a05 |
| 32174 | 2026-08-28T10:26:54.388Z | managed_process_admitted |  |  | owner=default |
| 32175 | 2026-08-28T10:26:54.772Z | managed_process_started |  |  | owner=default |
| 32176 | 2026-08-28T10:27:00.806Z | managed_process_terminal |  |  | owner=default |
| 32177 | 2026-08-28T10:27:01.214Z | proof_recorded |  |  | stage_id=check:1b0f8612837dd33d; status=passed; cache_hit=False; input_fingerprint=f0fff84208cd2b2eabb7d090fd92d11c94100437578a42226330330723ac1a05 |
| 32178 | 2026-08-28T10:27:01.457Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:466c2f308b48c766; input_fingerprint=68bde3f03396bab7ffd58f0ae5d49606423599f3510db74f34566508093e76af |
| 32179 | 2026-08-28T10:27:01.963Z | managed_process_admitted |  |  | owner=default |
| 32180 | 2026-08-28T10:27:02.399Z | managed_process_started |  |  | owner=default |
| 32181 | 2026-08-28T10:27:03.865Z | managed_process_terminal |  |  | owner=default |
| 32182 | 2026-08-28T10:27:04.248Z | proof_recorded |  |  | stage_id=check:466c2f308b48c766; status=passed; cache_hit=False; input_fingerprint=68bde3f03396bab7ffd58f0ae5d49606423599f3510db74f34566508093e76af |
| 32183 | 2026-08-28T10:27:05.030Z | observation_span_recorded |  |  |  |
| 32184 | 2026-08-28T10:27:05.261Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 32195 | 2026-08-28T10:28:53.898Z | quality_outcome_recorded |  |  |  |
| 32196 | 2026-08-28T10:28:54.080Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 32197 | 2026-08-28T10:28:54.675Z | observation_span_recorded |  |  |  |
| 32198 | 2026-08-28T10:28:55.417Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:21d3dc42049a8778 | passed | ff49dee6a7ee3bc2c6cf8bf686b4059a979d4218beb7b35c8e35edb435bfc15a | False | 20958 | 0 |
| check:aa6d7c839a151f3f | passed | 83b45dd941afa9489f6b2542353e0c75eabacb8137c4bca8be81ad123df118b4 | False | 3062 | 0 |
| check:1b0f8612837dd33d | passed | f0fff84208cd2b2eabb7d090fd92d11c94100437578a42226330330723ac1a05 | False | 6881 | 0 |
| check:466c2f308b48c766 | passed | 68bde3f03396bab7ffd58f0ae5d49606423599f3510db74f34566508093e76af | False | 2396 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| dc6a6d8fc33d4933894eabb2058ec6a6 | accepted | 2cc0eefc7d881827ef44e4d1584d84bbd9e494b6 | 4e0d8b4e9d2dbd5f0c06193f5a1de856e8adbd9ce12549d9b830b776812c1a95 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `131`
- Chain head: `aeca16276d3a7d3a11d67dd357846421e95283bd0963f7175aefcc239e4640bf`
