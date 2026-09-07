# Orchestration Wave 1

- Run: `36fb52098d964028a3dd3827c57a1e96`
- Wave: `11d01005d8404381b204193661504e65`
- Objective: Continue the prepared read-only preflight. Locate the exact full-clean sequence around stopping canonical Coding MCP and starting its replacement, and any existing bounded maintenance seam. Also locate the exact stale-run CLI entry contract. Do not modify source, Git, ledger, runtime, or machine state.
- Objective revision: `1`
- Objective SHA-256: `89c95236683220ddcd77addda3e5bd92ea582588722930db2ff15844077230ed`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `9255f94c9beff33f8c6c53d6745a08968f5a12bb`
- Worktree fingerprint: `8e37ce49b4e1956ed036390bc8fd6202f719090e25b3a841ef4e1d71fd2ae4a4`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 42780 | 2026-09-07T02:42:01.009Z | run_started |  | PREFLIGHT |  |
| 42781 | 2026-09-07T02:42:01.523Z | observation_span_recorded |  |  |  |
| 42782 | 2026-09-07T02:42:01.949Z | observation_span_recorded |  |  |  |
| 42783 | 2026-09-07T02:42:02.134Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 42784 | 2026-09-07T02:42:02.327Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 42785 | 2026-09-07T02:42:02.641Z | execution_mode_resolved | PREFLIGHT | PREFLIGHT | requested=auto; resolved=mcp_only |
| 42786 | 2026-09-07T02:42:02.849Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 42787 | 2026-09-07T02:42:03.002Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 42788 | 2026-09-07T02:42:03.218Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 42789 | 2026-09-07T02:42:03.389Z | state_transition | READY | ROUTED | reason=route_selected |
| 42790 | 2026-09-07T02:42:03.639Z | observation_span_recorded |  |  |  |
| 42791 | 2026-09-07T02:42:04.099Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=3231d6ec23cc4a1da6941ec6fb14b944 |
| 42792 | 2026-09-07T02:42:04.259Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 42793 | 2026-09-07T02:42:04.604Z | observation_span_recorded |  |  |  |
| 42794 | 2026-09-07T02:42:04.851Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=3231d6ec23cc4a1da6941ec6fb14b944 |
| 42795 | 2026-09-07T02:42:05.000Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 42796 | 2026-09-07T02:42:05.362Z | proof_cache_miss |  |  | reason=cold; stage_id=check:44e047b3debf7549; input_fingerprint=4062df7f182d184922292b43177a852fc960657ecc2c1b78db8f8c2d77495043 |
| 42797 | 2026-09-07T02:42:05.700Z | managed_process_admitted |  |  | owner=default |
| 42798 | 2026-09-07T02:42:05.981Z | managed_process_started |  |  | owner=default |
| 42799 | 2026-09-07T02:42:06.444Z | managed_process_terminal |  |  | owner=default |
| 42800 | 2026-09-07T02:42:06.796Z | proof_recorded |  |  | stage_id=check:44e047b3debf7549; status=passed; cache_hit=False; input_fingerprint=4062df7f182d184922292b43177a852fc960657ecc2c1b78db8f8c2d77495043 |
| 42801 | 2026-09-07T02:42:07.003Z | proof_cache_miss |  |  | reason=cold; stage_id=check:e98c353ba5f9add4; input_fingerprint=d2631ce2deaddbeb3be4507de397e51f9df31fdb4f4dd4ccfc34d1b52beb9d84 |
| 42802 | 2026-09-07T02:42:07.312Z | managed_process_admitted |  |  | owner=default |
| 42803 | 2026-09-07T02:42:07.582Z | managed_process_started |  |  | owner=default |
| 42804 | 2026-09-07T02:42:07.958Z | managed_process_terminal |  |  | owner=default |
| 42805 | 2026-09-07T02:42:08.367Z | proof_recorded |  |  | stage_id=check:e98c353ba5f9add4; status=passed; cache_hit=False; input_fingerprint=d2631ce2deaddbeb3be4507de397e51f9df31fdb4f4dd4ccfc34d1b52beb9d84 |
| 42806 | 2026-09-07T02:42:08.548Z | observation_span_recorded |  |  |  |
| 42807 | 2026-09-07T02:42:08.777Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 42808 | 2026-09-07T02:42:53.376Z | quality_outcome_recorded |  |  |  |
| 42809 | 2026-09-07T02:42:53.568Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 42810 | 2026-09-07T02:42:53.866Z | observation_span_recorded |  |  |  |
| 42811 | 2026-09-07T02:42:54.049Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:44e047b3debf7549 | passed | 4062df7f182d184922292b43177a852fc960657ecc2c1b78db8f8c2d77495043 | False | 1096 | 0 |
| check:e98c353ba5f9add4 | passed | d2631ce2deaddbeb3be4507de397e51f9df31fdb4f4dd4ccfc34d1b52beb9d84 | False | 1029 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| f4448033db9b4ea297649e36c599b5df | accepted | 9255f94c9beff33f8c6c53d6745a08968f5a12bb | c835775911d11015d1996ac4f2304a43098c680b83839ed600cde142a57f15fc | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `32`
- Chain head: `b4ef148ee8ad27217a2d226314f751326b1fb364d9895241145590eb8357501b`
