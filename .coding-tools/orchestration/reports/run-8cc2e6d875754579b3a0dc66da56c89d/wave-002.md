# Orchestration Wave 2

- Run: `8cc2e6d875754579b3a0dc66da56c89d`
- Wave: `694692871e75418eb1692aa65fd09ece`
- Objective: Diagnose why the production WebMCP Recovery Supervisor Scheduled Task invoking the installed recovery-supervisor.ps1 -Action Run does not publish a fresh capability-bearing heartbeat after the official Install. Determine the exact production-only failure cause using read-only evidence, including reconciling the newly observed current-source versus installed-script drift before any lifecycle retry. Do not retry Install, do not start/stop/delete tasks, do not edit source/runtime files, and do not restart runtime in this wave.
- Objective revision: `2`
- Objective SHA-256: `d79d2d1011c9cfbc52fa37f41b7cdc3587ee1fb493cd68513296b3432091b5d8`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6`
- Worktree fingerprint: `eafe54a3298b253bd7d724c15ebc58d1ff48fc18a0739c43cb1cdcfb3b13b9a6`
- Contract fingerprint: `270e9a76c407a40e3a8d7c9151f355841314d54e778559402beef4517ffe282f`
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 58005 | 2026-09-15T07:47:23.993Z | wave_replanned |  | PREFLIGHT | reason=The previous wave established a materially changed state: current source SHA 9f6cd064... differs from installed production SHA a2a56210..., while the full focused test failed only on the roaming-install/legacy-cleanup source-shape assertion. This new wave reconciles those concurrent bytes instead of repeating the failed full test or retrying lifecycle operations. |
| 58006 | 2026-09-15T07:47:24.361Z | observation_span_recorded |  |  |  |
| 58007 | 2026-09-15T07:47:24.659Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 58008 | 2026-09-15T07:47:24.855Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 58009 | 2026-09-15T07:47:25.112Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 58010 | 2026-09-15T07:47:25.351Z | state_transition | READY | ROUTED | reason=route_selected |
| 58011 | 2026-09-15T07:47:25.598Z | observation_span_recorded |  |  |  |
| 58012 | 2026-09-15T07:47:26.270Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=18d4907e19eb47a6b9d1d359c3713594 |
| 58013 | 2026-09-15T07:47:26.485Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 58014 | 2026-09-15T07:47:27.034Z | observation_span_recorded |  |  |  |
| 58015 | 2026-09-15T07:47:27.354Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=18d4907e19eb47a6b9d1d359c3713594 |
| 58016 | 2026-09-15T07:47:27.598Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 58017 | 2026-09-15T07:47:28.227Z | proof_cache_miss |  |  | reason=cold; stage_id=check:825ca227eeb53b27; input_fingerprint=c96947a2fcef8c77ba429db9b4d7c1fc5875a681dcffa8961c93ea0cff7bcc7e |
| 58018 | 2026-09-15T07:47:28.669Z | managed_process_admitted |  |  | owner=default |
| 58019 | 2026-09-15T07:47:29.029Z | managed_process_started |  |  | owner=default |
| 58020 | 2026-09-15T07:47:29.410Z | managed_process_terminal |  |  | owner=default |
| 58021 | 2026-09-15T07:47:29.918Z | proof_recorded |  |  | stage_id=check:825ca227eeb53b27; status=passed; cache_hit=False; input_fingerprint=c96947a2fcef8c77ba429db9b4d7c1fc5875a681dcffa8961c93ea0cff7bcc7e |
| 58022 | 2026-09-15T07:47:30.203Z | proof_cache_miss |  |  | reason=cold; stage_id=check:8145ec2f63eb74b4; input_fingerprint=c9cf2a7782b6d77415e1dc6c170155eea131d0ddb746b5794691cfb36d83a97b |
| 58023 | 2026-09-15T07:47:30.718Z | managed_process_admitted |  |  | owner=default |
| 58024 | 2026-09-15T07:47:31.137Z | managed_process_started |  |  | owner=default |
| 58025 | 2026-09-15T07:47:32.156Z | managed_process_terminal |  |  | owner=default |
| 58026 | 2026-09-15T07:47:32.716Z | proof_recorded |  |  | stage_id=check:8145ec2f63eb74b4; status=passed; cache_hit=False; input_fingerprint=c9cf2a7782b6d77415e1dc6c170155eea131d0ddb746b5794691cfb36d83a97b |
| 58027 | 2026-09-15T07:47:32.897Z | proof_cache_miss |  |  | reason=cold; stage_id=check:a86ad5afa6cd079a; input_fingerprint=3835bb88f1ff909c8225005322272a81176ee9eaf7a94013ed452c6612598182 |
| 58028 | 2026-09-15T07:47:33.296Z | managed_process_admitted |  |  | owner=default |
| 58029 | 2026-09-15T07:47:33.662Z | managed_process_started |  |  | owner=default |
| 58030 | 2026-09-15T07:47:34.269Z | managed_process_terminal |  |  | owner=default |
| 58031 | 2026-09-15T07:47:34.717Z | proof_recorded |  |  | stage_id=check:a86ad5afa6cd079a; status=failed; cache_hit=False; input_fingerprint=3835bb88f1ff909c8225005322272a81176ee9eaf7a94013ed452c6612598182 |
| 58032 | 2026-09-15T07:47:35.024Z | observation_span_recorded |  |  |  |
| 58033 | 2026-09-15T07:47:35.315Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 58034 | 2026-09-15T07:47:35.576Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 58035 | 2026-09-15T07:47:35.831Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 58036 | 2026-09-15T07:47:58.232Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:825ca227eeb53b27 | passed | c96947a2fcef8c77ba429db9b4d7c1fc5875a681dcffa8961c93ea0cff7bcc7e | False | 1236 | 0 |
| check:8145ec2f63eb74b4 | passed | c9cf2a7782b6d77415e1dc6c170155eea131d0ddb746b5794691cfb36d83a97b | False | 2028 | 0 |
| check:a86ad5afa6cd079a | failed | 3835bb88f1ff909c8225005322272a81176ee9eaf7a94013ed452c6612598182 | False | 1396 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `117`
- Chain head: `50b0fb572d5b96878be3a397fa5e21771d786a44f19bc6f096daea79d3f68634`
