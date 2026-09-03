# Orchestration Wave 8

- Run: `21a41bfdbfc44192a82bc10c25e7eefe`
- Wave: `d8275650b9f240b99be1b47c09ad7561`
- Objective: Complete the rejected H0/L3 acceptance scope in the same RUN without altering the four valid schema-v6 changes: harden the ChatGPT structured-usage observer to an explicit content-free response-envelope allowlist with transparent non-stacking hooks and exact restore; carry exact RUN/WAVE in Electron controllerUsage metadata; enforce strict trusted ChatWeb provenance plus authoritative RUN/WAVE/turn/trace matching and read-only active controller-lease validation for CHECKPOINTED post-turn ingress; enforce JavaScript-safe exact token integers and paired run/wave binding while preserving unknown-not-zero and canonical duplicate semantics; add only focused tests in existing dedicated controller-usage/JS test files, preserve the already-dirty test_usage_accounting_v2.py unchanged, and prove with git diff --check plus the focused JS/Python suites including test_stateless_http_2026.py, test_usage_accounting_v2.py, and test_accepted_result_economics_report.py. Do not modify mcp_http_handler.py, server.py, orchestration_ledger.py, http_hub_identity.py, test_usage_accounting_v2.py, dist/build artifacts, or unrelated dirty work.
- Objective revision: `8`
- Objective SHA-256: `94bc9e6a16455f78786c57fc72c7f0910e849ab4c9f6759df616f80945b4af38`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `f8e54e7051a8a08ec30c4eb11d1c0fb10440337e0c86ea7b433b700ac7f04efc`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 36989 | 2026-09-03T09:22:29.248Z | wave_replanned |  | PREFLIGHT | reason=Final acceptance of WAVE 18a05fc6ad584af3852cc8cabb9bcfc9 was explicitly rejected at event 36986 because the acceptance oracle and hardening scope were incomplete despite green schema-v6 tests. Preserve those four valid changes, broaden only to the exact rejected gaps, and use a stronger non-build oracle: git diff --check; JS journal tests; controller-usage post-turn tests; stateless HTTP tests; existing usage-accounting tests; accepted-result economics tests. No npm test/dist/build. |
| 36990 | 2026-09-03T09:22:29.442Z | observation_span_recorded |  |  |  |
| 36991 | 2026-09-03T09:22:31.774Z | observation_span_recorded |  |  |  |
| 36992 | 2026-09-03T09:22:31.978Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 36993 | 2026-09-03T09:24:09.325Z | managed_process_admitted |  |  | owner=chatweb-run21a-contract-final |
| 36994 | 2026-09-03T09:24:09.631Z | managed_process_started |  |  | owner=chatweb-run21a-contract-final |
| 36995 | 2026-09-03T09:24:10.161Z | managed_process_terminal |  |  | owner=chatweb-run21a-contract-final |
| 36996 | 2026-09-03T09:24:11.808Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 36997 | 2026-09-03T09:24:12.092Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 36998 | 2026-09-03T09:24:12.408Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 36999 | 2026-09-03T09:24:12.660Z | state_transition | READY | ROUTED | reason=route_selected |
| 37000 | 2026-09-03T09:24:12.915Z | observation_span_recorded |  |  |  |
| 37001 | 2026-09-03T09:24:20.569Z | managed_process_admitted |  |  | owner=chatweb-run21a-contract-final |
| 37002 | 2026-09-03T09:24:20.881Z | managed_process_started |  |  | owner=chatweb-run21a-contract-final |
| 37003 | 2026-09-03T09:24:21.791Z | managed_process_terminal |  |  | owner=chatweb-run21a-contract-final |
| 37004 | 2026-09-03T09:24:39.281Z | managed_process_admitted |  |  | owner=chatweb-run21a-handler-read |
| 37005 | 2026-09-03T09:24:39.549Z | managed_process_started |  |  | owner=chatweb-run21a-handler-read |
| 37006 | 2026-09-03T09:24:40.252Z | managed_process_terminal |  |  | owner=chatweb-run21a-handler-read |
| 37007 | 2026-09-03T09:25:59.623Z | failure_observed | ROUTED | ROUTED | reason=A non-terminal wave was recovered outside its original synchronous execution.; failure_class=RUNTIME_RESUME_REQUIRED |
| 37008 | 2026-09-03T09:25:59.784Z | state_transition | ROUTED | REPLAN | reason=RUNTIME_RESUME_REQUIRED; failure_class=RUNTIME_RESUME_REQUIRED |
| 37009 | 2026-09-03T09:26:00.002Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| - | - | - | - | - | - |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `477`
- Chain head: `d5d92b6a865dd8405169addd711fceac1741f551a0ecc3cbbc612370d70344c6`
