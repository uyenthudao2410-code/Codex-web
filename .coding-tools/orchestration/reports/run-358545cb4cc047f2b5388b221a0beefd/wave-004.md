# Orchestration Wave 4

- Run: `358545cb4cc047f2b5388b221a0beefd`
- Wave: `d206b7848ff648ed84c1bae5af199b8d`
- Objective: Continue the same RUN for Problem prl-activation-prepare-timeout-budget-20260912 revision 1 after wave 3 was blocked before verification because its compound shell command was not statically identifiable. Preserve the current exact bytes of electron/services/runtimeOrchestrator.js and tests/runtime-lifecycle.test.js without rewriting them. Adopt those exact current bytes and run a genuinely fresh verification using the single statically identifiable Node command node --test ./tests/runtime-lifecycle.test.js. The accepted source must retain MCP_ACTIVATION_OBSERVATION_TIMEOUT_MS=15000 for activation POST prepare/verify and the delayed prepare regression. Preserve supervisor restart-ticket TTL, activation epoch expiry, prepare-fence expiry, all fail-closed response/workspace checks, and unrelated dirty WIP. Do not restart runtime, commit, push, clean, reset, package, or release in this engineering wave.
- Objective revision: `4`
- Objective SHA-256: `89d58686cc8abd182a4da4984ea295654f90495d7328ffee7ef615c4b13ede0a`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `3afc90dfca1133e4e987b4a279b1fedc0532b5ce46323facea6689e31dbcf716`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 50919 | 2026-09-12T09:08:50.000Z | wave_replanned |  | PREFLIGHT | reason=CHANGED_VERIFICATION_STRATEGY: wave 3 produced no proof because the compound command with shell chaining was rejected as COMMAND_INTERPRETER_NOT_STATICALLY_IDENTIFIABLE. Replan the same RUN using one static Node invocation with a distinct command string so verification can execute and cannot reuse the prior proof key unchanged. |
| 50920 | 2026-09-12T09:08:50.485Z | observation_span_recorded |  |  |  |
| 50921 | 2026-09-12T09:08:51.401Z | observation_span_recorded |  |  |  |
| 50922 | 2026-09-12T09:08:51.641Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 50923 | 2026-09-12T09:08:52.129Z | managed_process_admitted |  |  | owner=default |
| 50924 | 2026-09-12T09:08:52.530Z | managed_process_started |  |  | owner=default |
| 50925 | 2026-09-12T09:09:07.947Z | managed_process_terminal |  |  | owner=default |
| 50926 | 2026-09-12T09:09:08.211Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 50927 | 2026-09-12T09:09:08.461Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 50928 | 2026-09-12T09:09:08.654Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 50929 | 2026-09-12T09:09:08.873Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 50930 | 2026-09-12T09:09:09.114Z | state_transition | READY | ROUTED | reason=route_selected |
| 50931 | 2026-09-12T09:09:09.380Z | observation_span_recorded |  |  |  |
| 50932 | 2026-09-12T09:09:10.392Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=415aa8e89c0c47e2bd8ed9d69f8c0cac |
| 50933 | 2026-09-12T09:09:10.626Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 50934 | 2026-09-12T09:09:11.567Z | existing_file_adoption_observed |  |  |  |
| 50935 | 2026-09-12T09:09:11.848Z | observation_span_recorded |  |  |  |
| 50936 | 2026-09-12T09:09:12.200Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=415aa8e89c0c47e2bd8ed9d69f8c0cac |
| 50937 | 2026-09-12T09:09:12.439Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 50938 | 2026-09-12T09:09:13.383Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=0004983399dd5ab46ca4f6c78986702327d39e4b215a27aa1bfc69bb66ac14ed |
| 50939 | 2026-09-12T09:09:13.864Z | managed_process_admitted |  |  | owner=default |
| 50940 | 2026-09-12T09:09:14.190Z | managed_process_started |  |  | owner=default |
| 50941 | 2026-09-12T09:09:29.413Z | managed_process_terminal |  |  | owner=default |
| 50942 | 2026-09-12T09:09:30.788Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=0004983399dd5ab46ca4f6c78986702327d39e4b215a27aa1bfc69bb66ac14ed |
| 50943 | 2026-09-12T09:09:31.106Z | observation_span_recorded |  |  |  |
| 50944 | 2026-09-12T09:09:31.329Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 50945 | 2026-09-12T09:09:31.571Z | observation_stage_anchor_recorded | ACCEPTING | ACCEPTING |  |
| 50946 | 2026-09-12T09:13:31.207Z | quality_outcome_recorded |  |  |  |
| 50947 | 2026-09-12T09:13:31.478Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 50948 | 2026-09-12T09:13:31.921Z | observation_span_recorded |  |  |  |
| 50949 | 2026-09-12T09:13:32.210Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |
| 50950 | 2026-09-12T09:13:32.418Z | observation_span_recorded |  |  |  |
| 50951 | 2026-09-12T09:13:32.717Z | observation_span_recorded |  |  |  |
| 50952 | 2026-09-12T09:13:32.909Z | continuity_telemetry_recorded |  |  |  |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 0004983399dd5ab46ca4f6c78986702327d39e4b215a27aa1bfc69bb66ac14ed | False | 16952 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| a0e252ae86db419585a07c5c8f0d0178 | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | 064353fe3a9361b5522f2515e74c8949a6820590107fe3ba6d1308eaeb92dee5 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `108`
- Chain head: `c365db16d1afff4352a92781046f9a8dd65a3a9c3ee2bcc9a6536a312049c345`
