# Orchestration Wave 1

- Run: `d80200b23a6144ff8d8a9d9fc8c111ef`
- Wave: `44da2aa89ae840b18932f7c420559954`
- Objective: G2-P6 provenance closure only for the exact durable Full Clean epoch-monitor packet. Adopt without changing source bytes exactly electron/services/recoveryActionStore.js at SHA-256 6b9ddd28aa29ca81ad6c5a3b2586847762839d7aabf076837b7ba392aaab62e5, electron/services/recoveryActivation.js at SHA-256 b0696cf3eae0523e04d2b1ae2a4095c0314d4e7f22eb46932ebaa8ed19f2274a, and tests/recovery-activation.test.js at SHA-256 e07a9c22ae26eaeb401c13f8139fb5070fb1e888f8de9169c6863ac28e8085a0. Prove the sole causal objective: separate the short request-admission TTL from the bounded durable Full Clean epoch-monitor lifetime; bind the durable invariant to exact operation_id + activation_epoch_id + expiry; validate it on reload; reject malformed, mismatched, conflicting, over-bound, or tampered evidence; and use the durable deadline only after the exact accepted action has been bound. Preserve request expiry as audit data. Replay must reattach the same epoch and must not create a second transaction. Preserve all concurrent WIP and every path outside this exact three-file scope. Do not run live restart, activation, process kill, process adoption, bulk adoption, direct SQLite, force-release, stale-run reconciliation, reset, restore, clean, rebase, commit, push, tag, release, publish, or deploy. ChatWeb Sol remains controller and final-acceptance owner.
- Objective revision: `1`
- Objective SHA-256: `455b19c9a6ed7a7f8925e7e8eeac0cf8d0b87ccadfd4dbfab7f2785f0fb17963`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `80aceb583202ad381c25687969fb48adbf74622c`
- Worktree fingerprint: `6b5fb2badfbcfa32b95881356c90eb51b89d687739b0b7df90dd27ec25209209`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 38210 | 2026-09-03T16:57:30.413Z | run_started |  | PREFLIGHT |  |
| 38211 | 2026-09-03T16:57:30.837Z | observation_span_recorded |  |  |  |
| 38212 | 2026-09-03T16:57:31.972Z | observation_span_recorded |  |  |  |
| 38213 | 2026-09-03T16:57:32.215Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 38214 | 2026-09-03T16:57:32.581Z | managed_process_admitted |  |  | owner=default |
| 38215 | 2026-09-03T16:57:32.916Z | managed_process_started |  |  | owner=default |
| 38216 | 2026-09-03T16:57:34.107Z | managed_process_terminal |  |  | owner=default |
| 38217 | 2026-09-03T16:57:34.334Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 38218 | 2026-09-03T16:57:34.539Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 38219 | 2026-09-03T16:57:34.764Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 38220 | 2026-09-03T16:57:35.015Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 38221 | 2026-09-03T16:57:35.231Z | state_transition | READY | ROUTED | reason=route_selected |
| 38222 | 2026-09-03T16:57:35.455Z | observation_span_recorded |  |  |  |
| 38223 | 2026-09-03T16:57:36.451Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=258868139ba9456c839fe9f0f4ca2705 |
| 38224 | 2026-09-03T16:57:36.705Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 38225 | 2026-09-03T16:57:37.590Z | existing_file_adoption_observed |  |  |  |
| 38226 | 2026-09-03T16:57:37.818Z | observation_span_recorded |  |  |  |
| 38227 | 2026-09-03T16:57:38.161Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=258868139ba9456c839fe9f0f4ca2705 |
| 38228 | 2026-09-03T16:57:38.625Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 38229 | 2026-09-03T16:57:39.514Z | proof_cache_miss |  |  | reason=cold; stage_id=check:32213fb48afa717c; input_fingerprint=bb424ff7ad806bbdbb1f399cb9a819768b67086c67f2e4827f16305d0c106a88 |
| 38230 | 2026-09-03T16:57:39.999Z | managed_process_admitted |  |  | owner=default |
| 38231 | 2026-09-03T16:57:40.366Z | managed_process_started |  |  | owner=default |
| 38232 | 2026-09-03T16:57:40.783Z | managed_process_terminal |  |  | owner=default |
| 38233 | 2026-09-03T16:57:41.190Z | proof_recorded |  |  | stage_id=check:32213fb48afa717c; status=passed; cache_hit=False; input_fingerprint=bb424ff7ad806bbdbb1f399cb9a819768b67086c67f2e4827f16305d0c106a88 |
| 38234 | 2026-09-03T16:57:41.422Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=aa6b8e105b85e13d4f9c50a9ec231f8163fd94e862a5806cef81ac49e04aaefe |
| 38235 | 2026-09-03T16:57:41.832Z | managed_process_admitted |  |  | owner=default |
| 38236 | 2026-09-03T16:57:42.225Z | managed_process_started |  |  | owner=default |
| 38237 | 2026-09-03T16:57:43.374Z | managed_process_terminal |  |  | owner=default |
| 38238 | 2026-09-03T16:57:44.208Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=aa6b8e105b85e13d4f9c50a9ec231f8163fd94e862a5806cef81ac49e04aaefe |
| 38239 | 2026-09-03T16:57:44.475Z | observation_span_recorded |  |  |  |
| 38240 | 2026-09-03T16:57:44.722Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 38241 | 2026-09-03T16:58:44.406Z | quality_outcome_recorded |  |  |  |
| 38242 | 2026-09-03T16:58:44.628Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 38243 | 2026-09-03T16:58:44.936Z | observation_span_recorded |  |  |  |
| 38244 | 2026-09-03T16:58:45.159Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:32213fb48afa717c | passed | bb424ff7ad806bbdbb1f399cb9a819768b67086c67f2e4827f16305d0c106a88 | False | 1259 | 0 |
| verify:tests | passed | aa6b8e105b85e13d4f9c50a9ec231f8163fd94e862a5806cef81ac49e04aaefe | False | 2375 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 1299c60deec2490c8950f4d72857353f | accepted | 80aceb583202ad381c25687969fb48adbf74622c | 58ad77a5338a55a51571b00b149a37bd8b84d80479a4b341938e510ec6e3724e | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `35`
- Chain head: `30afe4ac1835769d6e2eb6ae906be452c3ab6bf7e8785b9d125ad79403d9a574`
