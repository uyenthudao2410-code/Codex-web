# Orchestration Wave 3

- Run: `f7f34289300d42dda4a8d556a8183459`
- Wave: `c4c108c0cf8945aea7d3e8d7854e222e`
- Objective: Implement the user-authorized bounded exact-stale maintenance seam in Recovery Host full-clean replacement. Parse only a strict reserved reason prefix exact_stale_runs:<comma-separated 32-lowerhex-run-ids>, max 16 unique IDs. In continueReplacement, while the old canonical Coding MCP is already stopped and before orchestrator.start, sequentially run the existing reconcile_exact_stale_run.py through pythonStatus/execFile without shell: fresh preflight per ID, validate physical+logical HEX64 snapshot hashes, then reconcile with --runtime-stopped and exact expected hashes; require schema_version=1, reconciliation.chain_ok=true, and postflight target stale/RECONCILED_STALE/already_reconciled=true. Any malformed request, Python/script failure, receipt mismatch, or deadline expiry must fail the activation closed before MCP start. Ordinary restart reasons remain unchanged/no-op. Add focused tests proving sequential maintenance occurs before MCP start and malformed reserved reasons prevent start. Do not change public MCP tool schema/count, Python ledger logic, unrelated source, Git history, or external services.
- Objective revision: `1`
- Objective SHA-256: `bb863ff4cd2390b87937cb5c9bfa35cc3dd3cca0d821a04c8e4bfa934986cb9c`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `9255f94c9beff33f8c6c53d6745a08968f5a12bb`
- Worktree fingerprint: `887a20b6c043370d054dc0baa696b593400ed9c75ea808a3ead6159f108069db`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 43044 | 2026-09-07T03:16:13.276Z | wave_replanned |  | PREFLIGHT | reason=Code and focused tests are already green, but final acceptance failed closed because fullCleanActivation.js was pre-existing dirty from the prior rejected wave and was not in wave-002's durable mutation surface. Create a fresh wave solely to exact-byte adopt the current two files without changing bytes, rerun diff-check and the same focused suite, then final-accept using exact SHA-256 attestation. |
| 43045 | 2026-09-07T03:16:13.500Z | observation_span_recorded |  |  |  |
| 43046 | 2026-09-07T03:16:14.439Z | observation_span_recorded |  |  |  |
| 43047 | 2026-09-07T03:16:16.078Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 43048 | 2026-09-07T03:17:00.779Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 43049 | 2026-09-07T03:17:00.944Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 43050 | 2026-09-07T03:17:01.122Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 43051 | 2026-09-07T03:17:01.281Z | state_transition | READY | ROUTED | reason=route_selected |
| 43052 | 2026-09-07T03:17:01.485Z | observation_span_recorded |  |  |  |
| 43053 | 2026-09-07T03:17:02.041Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=b9a7712ffcef4a3bbcc2cfa76b043512 |
| 43054 | 2026-09-07T03:17:02.234Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 43055 | 2026-09-07T03:17:02.695Z | existing_file_adoption_observed |  |  |  |
| 43056 | 2026-09-07T03:17:02.896Z | observation_span_recorded |  |  |  |
| 43057 | 2026-09-07T03:17:03.143Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=b9a7712ffcef4a3bbcc2cfa76b043512 |
| 43058 | 2026-09-07T03:17:03.277Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 43059 | 2026-09-07T03:17:03.686Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:fdd8d9bbdabfc13b; input_fingerprint=f22f58d944790e2a43f61542ff97e6bf629db9160d6388e609ed20433da443e1 |
| 43060 | 2026-09-07T03:17:04.041Z | managed_process_admitted |  |  | owner=default |
| 43061 | 2026-09-07T03:17:04.454Z | managed_process_started |  |  | owner=default |
| 43062 | 2026-09-07T03:17:05.345Z | managed_process_terminal |  |  | owner=default |
| 43063 | 2026-09-07T03:17:05.774Z | proof_recorded |  |  | stage_id=check:fdd8d9bbdabfc13b; status=passed; cache_hit=False; input_fingerprint=f22f58d944790e2a43f61542ff97e6bf629db9160d6388e609ed20433da443e1 |
| 43064 | 2026-09-07T03:17:06.032Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=3cff82216b8cfdb560657d50ed11c58465ba5b6595f121c8fbc1064e736d819f |
| 43065 | 2026-09-07T03:17:06.422Z | managed_process_admitted |  |  | owner=default |
| 43066 | 2026-09-07T03:17:06.713Z | managed_process_started |  |  | owner=default |
| 43067 | 2026-09-07T03:17:08.489Z | managed_process_terminal |  |  | owner=default |
| 43068 | 2026-09-07T03:17:09.787Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=3cff82216b8cfdb560657d50ed11c58465ba5b6595f121c8fbc1064e736d819f |
| 43069 | 2026-09-07T03:17:10.258Z | observation_span_recorded |  |  |  |
| 43070 | 2026-09-07T03:17:10.541Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 43071 | 2026-09-07T03:18:49.102Z | quality_outcome_recorded |  |  |  |
| 43072 | 2026-09-07T03:18:49.392Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 43073 | 2026-09-07T03:18:49.733Z | observation_span_recorded |  |  |  |
| 43074 | 2026-09-07T03:18:50.103Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:fdd8d9bbdabfc13b | passed | f22f58d944790e2a43f61542ff97e6bf629db9160d6388e609ed20433da443e1 | False | 1728 | 0 |
| verify:tests | passed | 3cff82216b8cfdb560657d50ed11c58465ba5b6595f121c8fbc1064e736d819f | False | 3421 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 24b489bbb0ba49b5a49bf88008803180 | accepted | 9255f94c9beff33f8c6c53d6745a08968f5a12bb | 2d6f358f5957f62c2f8f4ec0e5804122b6cc8fbf4b8a0e94d03dc2bb04866f40 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `100`
- Chain head: `d131d7d6fc7b04b21d22ab14c6e56caacc5eaa3ccda8de8ab8f99f6586968fad`
