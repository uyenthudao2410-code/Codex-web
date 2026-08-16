# Orchestration Wave 1

- Run: `acddab468da74e4fb876b7e8509b5446`
- Wave: `06e645a4b9dd46b7bd0fb2c60c24c948`
- Objective: Continue the accepted server-first compute plan after R2B. Do not modify files or run implementation commands in prepare. Inspect the implementation-ready research decision record docs/research/260816_CHATWEB_SERVER_FIRST_COMPUTE_ORCHESTRATION_RESEARCH.md only as needed for the R3/R4 acceptance intent, plus current exact-source validation, runner job metadata/protocol, project source identity, artifact/upload primitives, compute placement, and relevant focused tests. Determine the smallest coherent R3 implementation that supports dirty/uncommitted source via an immutable content-addressed source snapshot/manifest without turning the product into a fleet/CAS platform. Preserve these invariants: server-first compute not authority; remote execution read-only/disposable; exact source identity before dispatch/proof reuse; no automatic Git commit; no remote authoritative write; no blind retry on unknown outcome; current clean-head R2B behavior remains unchanged; no new public MCP tool unless strictly necessary; preserve all unrelated WIP and .coding-tools runtime evidence. Identify concrete files/contracts, whether existing artifact/job payloads can carry the snapshot, snapshot digest/manifest rules, dispatch materialization boundary, cleanup/lifetime, backward compatibility for old runners, and the cheapest authoritative focused proof. Also identify the minimal R4 observability/economics follow-up after R3 is accepted. Return one implementation-ready slice, not a broad redesign.
- Mode: `mcp_only`
- Base HEAD: `6b5d16e980058d51585f039eff918d938bbb66e9`
- Worktree fingerprint: `3ffbaff0e9a4276159f7515f2a3e0e862fe05de8a9d642a0a0e580e5e821fb06`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 8800 | 2026-08-16T14:43:13.187Z | run_started |  | PREFLIGHT |  |
| 8801 | 2026-08-16T14:43:18.155Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 8802 | 2026-08-16T14:47:32.194Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 8803 | 2026-08-16T14:47:32.316Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 8804 | 2026-08-16T14:47:32.443Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 8805 | 2026-08-16T14:47:32.566Z | state_transition | READY | ROUTED | reason=route_selected |
| 8806 | 2026-08-16T14:47:32.984Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=c7472b1657464a2b8a34d7a82165f8bd |
| 8807 | 2026-08-16T14:47:33.087Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 8808 | 2026-08-16T14:47:33.558Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=c7472b1657464a2b8a34d7a82165f8bd |
| 8809 | 2026-08-16T14:47:33.678Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 8810 | 2026-08-16T14:47:34.067Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:810e75f0d3dee10e; input_fingerprint=14c7f1efbfd2627a044c8410a632a9a34d4d12890ea0af5f47219c44f74608fe |
| 8811 | 2026-08-16T14:47:34.363Z | managed_process_admitted |  |  | owner=default |
| 8812 | 2026-08-16T14:47:34.599Z | managed_process_started |  |  | owner=default |
| 8813 | 2026-08-16T14:47:40.192Z | managed_process_terminal |  |  | owner=default |
| 8814 | 2026-08-16T14:47:40.449Z | proof_recorded |  |  | stage_id=check:810e75f0d3dee10e; status=passed; cache_hit=False; input_fingerprint=14c7f1efbfd2627a044c8410a632a9a34d4d12890ea0af5f47219c44f74608fe |
| 8815 | 2026-08-16T14:47:40.582Z | proof_cache_miss |  |  | reason=cold; stage_id=check:7fc03c251493acf9; input_fingerprint=bc903d7635257da65de77d7b6769f40b7fb22e70e9309864b8e6022ae74dee48 |
| 8816 | 2026-08-16T14:47:40.883Z | managed_process_admitted |  |  | owner=default |
| 8817 | 2026-08-16T14:47:41.162Z | managed_process_started |  |  | owner=default |
| 8818 | 2026-08-16T14:47:44.800Z | managed_process_terminal |  |  | owner=default |
| 8819 | 2026-08-16T14:47:44.983Z | proof_recorded |  |  | stage_id=check:7fc03c251493acf9; status=passed; cache_hit=False; input_fingerprint=bc903d7635257da65de77d7b6769f40b7fb22e70e9309864b8e6022ae74dee48 |
| 8820 | 2026-08-16T14:47:45.115Z | proof_cache_miss |  |  | reason=cold; stage_id=check:a9833a296abd8634; input_fingerprint=8e029773043846bc9e8817dd1b103a6537a219b03e20b15255429ccc703a6057 |
| 8821 | 2026-08-16T14:47:45.463Z | managed_process_admitted |  |  | owner=default |
| 8822 | 2026-08-16T14:47:45.703Z | managed_process_started |  |  | owner=default |
| 8823 | 2026-08-16T14:48:33.834Z | managed_process_terminal |  |  | owner=default |
| 8824 | 2026-08-16T14:48:34.128Z | proof_recorded |  |  | stage_id=check:a9833a296abd8634; status=passed; cache_hit=False; input_fingerprint=8e029773043846bc9e8817dd1b103a6537a219b03e20b15255429ccc703a6057 |
| 8825 | 2026-08-16T14:48:34.442Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:bcb9509776b8d535; input_fingerprint=5662bb09bf7dfadd758b0710d4a52ad74433322fe9bc961cf0d0efbd283fd6a4 |
| 8826 | 2026-08-16T14:48:34.723Z | managed_process_admitted |  |  | owner=default |
| 8827 | 2026-08-16T14:48:34.967Z | managed_process_started |  |  | owner=default |
| 8828 | 2026-08-16T14:48:56.898Z | managed_process_terminal |  |  | owner=default |
| 8829 | 2026-08-16T14:48:57.101Z | proof_recorded |  |  | stage_id=check:bcb9509776b8d535; status=passed; cache_hit=False; input_fingerprint=5662bb09bf7dfadd758b0710d4a52ad74433322fe9bc961cf0d0efbd283fd6a4 |
| 8830 | 2026-08-16T14:48:57.201Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:731a566acabcb042; input_fingerprint=ffc711c719433b92aa761f27f273908e2185252483c5ecd087f105a4a0286696 |
| 8831 | 2026-08-16T14:48:57.581Z | managed_process_admitted |  |  | owner=default |
| 8832 | 2026-08-16T14:48:57.775Z | managed_process_started |  |  | owner=default |
| 8833 | 2026-08-16T14:50:00.440Z | managed_process_terminal |  |  | owner=default |
| 8834 | 2026-08-16T14:50:00.673Z | proof_recorded |  |  | stage_id=check:731a566acabcb042; status=passed; cache_hit=False; input_fingerprint=ffc711c719433b92aa761f27f273908e2185252483c5ecd087f105a4a0286696 |
| 8835 | 2026-08-16T14:50:00.815Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 8836 | 2026-08-16T14:50:19.877Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 8837 | 2026-08-16T14:50:20.206Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:810e75f0d3dee10e | passed | 14c7f1efbfd2627a044c8410a632a9a34d4d12890ea0af5f47219c44f74608fe | False | 6115 | 0 |
| check:7fc03c251493acf9 | passed | bc903d7635257da65de77d7b6769f40b7fb22e70e9309864b8e6022ae74dee48 | False | 4188 | 0 |
| check:a9833a296abd8634 | passed | 8e029773043846bc9e8817dd1b103a6537a219b03e20b15255429ccc703a6057 | False | 48687 | 0 |
| check:bcb9509776b8d535 | passed | 5662bb09bf7dfadd758b0710d4a52ad74433322fe9bc961cf0d0efbd283fd6a4 | False | 22477 | 0 |
| check:731a566acabcb042 | passed | ffc711c719433b92aa761f27f273908e2185252483c5ecd087f105a4a0286696 | False | 63238 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 5580f9e0a8b74f5abba8ce7b1b0c38f5 | accepted | 6b5d16e980058d51585f039eff918d938bbb66e9 | f88bcb6da52fb234eade6907805a232254059a68cff1d99cd3a5867281580b40 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `38`
- Chain head: `817585556b9c1d8c1cbdd72d4e1887f32c89720240add7bdf614520092bd8839`
