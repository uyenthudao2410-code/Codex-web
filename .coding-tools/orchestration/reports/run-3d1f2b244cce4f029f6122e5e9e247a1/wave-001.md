# Orchestration Wave 1

- Run: `3d1f2b244cce4f029f6122e5e9e247a1`
- Wave: `5c59c237603448129ceae0265665f2d5`
- Objective: Prepare the final test-only repair for the three remaining legacy Execution Hub failures on main checkout. Read and obey resources/coding-tools-mcp/AGENTS.md. Preserve the already-written panel fail-visible changes and unrelated P4-MX/evaluation/telemetry dirt. Do not write yet. Localize post_stateless and only the three failing tests, plus the current acquire_controller_lease and events/run_id contract. Production Python must remain unchanged.
- Mode: `mcp_only`
- Base HEAD: `2c29a7c8af82215c3c332c8f26902f1eb8d1c894`
- Worktree fingerprint: `9b5e04403a82c728a7273b196d7368a73f2102a71308fb9fffaec9ebf1636ddc`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 23111 | 2026-08-20T06:44:57.377Z | run_started |  | PREFLIGHT |  |
| 23112 | 2026-08-20T06:44:59.004Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 23113 | 2026-08-20T06:45:21.810Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 23114 | 2026-08-20T06:46:33.047Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 23115 | 2026-08-20T06:47:52.009Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 23116 | 2026-08-20T06:47:52.325Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 23117 | 2026-08-20T06:47:52.753Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 23118 | 2026-08-20T06:47:53.000Z | state_transition | READY | ROUTED | reason=route_selected |
| 23119 | 2026-08-20T06:47:53.837Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=bbf86fb466a243be82b1117042772e95 |
| 23120 | 2026-08-20T06:47:54.026Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 23121 | 2026-08-20T06:47:54.769Z | patch_surface_observed |  |  |  |
| 23122 | 2026-08-20T06:47:55.191Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=bbf86fb466a243be82b1117042772e95 |
| 23123 | 2026-08-20T06:47:55.441Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 23124 | 2026-08-20T06:47:56.098Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:31f0b0a006eeeb45; input_fingerprint=b5d7b693141870ab447239609d37e0826c79e32454717cce312296be84931e41 |
| 23125 | 2026-08-20T06:47:57.084Z | managed_process_admitted |  |  | owner=default |
| 23126 | 2026-08-20T06:47:57.604Z | managed_process_started |  |  | owner=default |
| 23127 | 2026-08-20T06:47:58.421Z | managed_process_terminal |  |  | owner=default |
| 23128 | 2026-08-20T06:47:58.911Z | proof_recorded |  |  | stage_id=check:31f0b0a006eeeb45; status=passed; cache_hit=False; input_fingerprint=b5d7b693141870ab447239609d37e0826c79e32454717cce312296be84931e41 |
| 23129 | 2026-08-20T06:47:59.283Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:5c4daf617fdbcc8a; input_fingerprint=41b9d76ad3e0a3cd70f223ddce07c46bb5e93aa143a5e55996240e3228cd3f3d |
| 23130 | 2026-08-20T06:48:00.382Z | managed_process_admitted |  |  | owner=default |
| 23131 | 2026-08-20T06:48:00.938Z | managed_process_started |  |  | owner=default |
| 23132 | 2026-08-20T06:48:01.821Z | managed_process_terminal |  |  | owner=default |
| 23133 | 2026-08-20T06:48:02.310Z | proof_recorded |  |  | stage_id=check:5c4daf617fdbcc8a; status=passed; cache_hit=False; input_fingerprint=41b9d76ad3e0a3cd70f223ddce07c46bb5e93aa143a5e55996240e3228cd3f3d |
| 23134 | 2026-08-20T06:48:02.729Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=58bfd630bcac39a13b6f1581f92380bcf40d7e669f3753dcc93151e4475938fc |
| 23135 | 2026-08-20T06:48:03.809Z | managed_process_admitted |  |  | owner=default |
| 23136 | 2026-08-20T06:48:04.360Z | managed_process_started |  |  | owner=default |
| 23137 | 2026-08-20T06:48:19.885Z | managed_process_terminal |  |  | owner=default |
| 23138 | 2026-08-20T06:48:28.541Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=58bfd630bcac39a13b6f1581f92380bcf40d7e669f3753dcc93151e4475938fc |
| 23139 | 2026-08-20T06:48:29.238Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 23140 | 2026-08-20T06:51:39.285Z | managed_process_admitted |  |  | owner=default |
| 23141 | 2026-08-20T06:51:39.802Z | managed_process_started |  |  | owner=default |
| 23142 | 2026-08-20T06:51:40.720Z | managed_process_terminal |  |  | owner=default |
| 23143 | 2026-08-20T06:52:01.359Z | managed_process_admitted |  |  | owner=default |
| 23144 | 2026-08-20T06:52:02.067Z | managed_process_started |  |  | owner=default |
| 23145 | 2026-08-20T06:52:02.815Z | managed_process_terminal |  |  | owner=default |
| 23146 | 2026-08-20T06:55:36.388Z | managed_process_admitted |  |  | owner=default |
| 23147 | 2026-08-20T06:55:36.984Z | managed_process_started |  |  | owner=default |
| 23148 | 2026-08-20T06:55:37.772Z | managed_process_terminal |  |  | owner=default |
| 23149 | 2026-08-20T06:59:05.860Z | managed_process_admitted |  |  | owner=default |
| 23150 | 2026-08-20T06:59:06.533Z | managed_process_started |  |  | owner=default |
| 23151 | 2026-08-20T06:59:07.559Z | managed_process_terminal |  |  | owner=default |
| 23152 | 2026-08-20T07:02:38.692Z | managed_process_admitted |  |  | owner=default |
| 23153 | 2026-08-20T07:02:39.310Z | managed_process_started |  |  | owner=default |
| 23154 | 2026-08-20T07:02:40.231Z | managed_process_terminal |  |  | owner=default |
| 23155 | 2026-08-20T07:05:16.159Z | managed_process_admitted |  |  | owner=default |
| 23156 | 2026-08-20T07:05:17.543Z | managed_process_started |  |  | owner=default |
| 23157 | 2026-08-20T07:05:18.552Z | managed_process_terminal |  |  | owner=default |
| 23158 | 2026-08-20T07:07:35.135Z | managed_process_admitted |  |  | owner=default |
| 23159 | 2026-08-20T07:07:35.951Z | managed_process_started |  |  | owner=default |
| 23160 | 2026-08-20T07:07:37.084Z | managed_process_terminal |  |  | owner=default |
| 23161 | 2026-08-20T07:08:11.234Z | managed_process_admitted |  |  | owner=default |
| 23162 | 2026-08-20T07:08:11.918Z | managed_process_started |  |  | owner=default |
| 23163 | 2026-08-20T07:08:20.962Z | managed_process_terminal |  |  | owner=default |
| 23164 | 2026-08-20T07:08:42.257Z | managed_process_admitted |  |  | owner=default |
| 23165 | 2026-08-20T07:08:42.875Z | managed_process_started |  |  | owner=default |
| 23166 | 2026-08-20T07:08:43.670Z | managed_process_terminal |  |  | owner=default |
| 23167 | 2026-08-20T07:09:11.056Z | managed_process_admitted |  |  | owner=default |
| 23168 | 2026-08-20T07:09:12.018Z | managed_process_started |  |  | owner=default |
| 23169 | 2026-08-20T07:09:20.659Z | managed_process_terminal |  |  | owner=default |
| 23170 | 2026-08-20T07:17:44.180Z | quality_outcome_recorded |  |  |  |
| 23171 | 2026-08-20T07:17:44.392Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 23172 | 2026-08-20T07:17:45.213Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:31f0b0a006eeeb45 | passed | b5d7b693141870ab447239609d37e0826c79e32454717cce312296be84931e41 | False | 2294 | 0 |
| check:5c4daf617fdbcc8a | passed | 41b9d76ad3e0a3cd70f223ddce07c46bb5e93aa143a5e55996240e3228cd3f3d | False | 2626 | 0 |
| verify:tests | passed | 58bfd630bcac39a13b6f1581f92380bcf40d7e669f3753dcc93151e4475938fc | False | 25092 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 299aece714384479965a013a998574ee | accepted | 2c29a7c8af82215c3c332c8f26902f1eb8d1c894 | 4458f43b35217d24a59bb71d2bc487d6275706c264784d98a9f19310b11ce2bc | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `62`
- Chain head: `d6ee3be3ea9805150fa1037a5ad4df0ce598101f865b2dc56165ef4389a7cdf3`
