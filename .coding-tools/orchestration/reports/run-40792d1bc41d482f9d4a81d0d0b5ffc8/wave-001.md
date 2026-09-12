# Orchestration Wave 1

- Run: `40792d1bc41d482f9d4a81d0d0b5ffc8`
- Wave: `741844f3041244a8a4250b446356e13a`
- Objective: Establish byte-exact accepted recovery_host provenance for the trusted mixed-version bootstrap, prove the selector and handoff safeguards, and prepare one safe full-clean replacement without changing the existing source bytes.
- Objective revision: `1`
- Objective SHA-256: `a2a376a0a50c3e3cac1410e90acf24d004400208002c2a19e4dfc8438c18166a`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `55652b7f675ffef67b7c29b8edf29f9dcb1f596f9220a32f33a82814971a6972`
- Contract fingerprint: `48bf51ec5b78d91e5c83035589ffe868fdce216a6b5d7bc2206fa7891f7f910b`
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 43851 | 2026-09-08T12:58:07.325Z | run_started |  | PREFLIGHT |  |
| 43852 | 2026-09-08T12:58:07.871Z | observation_span_recorded |  |  |  |
| 43853 | 2026-09-08T12:58:08.097Z | solution_shadow_recommended |  |  |  |
| 43854 | 2026-09-08T12:58:08.270Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 43855 | 2026-09-08T12:58:08.455Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 43856 | 2026-09-08T12:58:08.662Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 43857 | 2026-09-08T12:58:08.864Z | state_transition | READY | ROUTED | reason=route_selected |
| 43858 | 2026-09-08T12:58:09.077Z | observation_span_recorded |  |  |  |
| 43859 | 2026-09-08T12:58:09.872Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=e2a5ab794d7b4bbdb1989d41d30d5930 |
| 43860 | 2026-09-08T12:58:10.052Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 43861 | 2026-09-08T12:58:10.792Z | existing_file_adoption_observed |  |  |  |
| 43862 | 2026-09-08T12:58:10.957Z | observation_span_recorded |  |  |  |
| 43863 | 2026-09-08T12:58:11.215Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=e2a5ab794d7b4bbdb1989d41d30d5930 |
| 43864 | 2026-09-08T12:58:11.368Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 43865 | 2026-09-08T12:58:12.040Z | proof_cache_miss |  |  | reason=cold; stage_id=check:ab3e5982ab79e3d6; input_fingerprint=51c457d731f23b588ce797a5b95c056d7e339721f45627bcbc32973308d61d29 |
| 43866 | 2026-09-08T12:58:12.436Z | managed_process_admitted |  |  | owner=default |
| 43867 | 2026-09-08T12:58:12.754Z | managed_process_started |  |  | owner=default |
| 43868 | 2026-09-08T12:58:17.421Z | managed_process_terminal |  |  | owner=default |
| 43869 | 2026-09-08T12:58:17.806Z | proof_recorded |  |  | stage_id=check:ab3e5982ab79e3d6; status=passed; cache_hit=False; input_fingerprint=51c457d731f23b588ce797a5b95c056d7e339721f45627bcbc32973308d61d29 |
| 43870 | 2026-09-08T12:58:18.023Z | proof_cache_miss |  |  | reason=cold; stage_id=check:1a46f0fadadf887b; input_fingerprint=45e3210d71e954eb0ae28c056082ecb4eaeb598ffb29c3405a9463339cba4304 |
| 43871 | 2026-09-08T12:58:18.453Z | managed_process_admitted |  |  | owner=default |
| 43872 | 2026-09-08T12:58:18.928Z | managed_process_started |  |  | owner=default |
| 43873 | 2026-09-08T12:58:19.505Z | managed_process_terminal |  |  | owner=default |
| 43874 | 2026-09-08T12:58:19.789Z | proof_recorded |  |  | stage_id=check:1a46f0fadadf887b; status=passed; cache_hit=False; input_fingerprint=45e3210d71e954eb0ae28c056082ecb4eaeb598ffb29c3405a9463339cba4304 |
| 43875 | 2026-09-08T12:58:20.392Z | proof_cache_miss |  |  | reason=cold; stage_id=check:fb57f580333ccaca; input_fingerprint=a5347a2932e7549173e063418931c0b585afdce33edf3dd2b709bb99b6b66b92 |
| 43876 | 2026-09-08T12:58:20.928Z | managed_process_admitted |  |  | owner=default |
| 43877 | 2026-09-08T12:58:21.230Z | managed_process_started |  |  | owner=default |
| 43878 | 2026-09-08T12:58:25.995Z | managed_process_terminal |  |  | owner=default |
| 43879 | 2026-09-08T12:58:26.402Z | proof_recorded |  |  | stage_id=check:fb57f580333ccaca; status=passed; cache_hit=False; input_fingerprint=a5347a2932e7549173e063418931c0b585afdce33edf3dd2b709bb99b6b66b92 |
| 43880 | 2026-09-08T12:58:26.646Z | proof_cache_miss |  |  | reason=cold; stage_id=check:9273835c18178321; input_fingerprint=0ea101b6a381e95e0a37b9855a895afc1b9572b3c3ac36af9d75d806115178f3 |
| 43881 | 2026-09-08T12:58:27.045Z | managed_process_admitted |  |  | owner=default |
| 43882 | 2026-09-08T12:58:27.438Z | managed_process_started |  |  | owner=default |
| 43883 | 2026-09-08T12:58:32.919Z | managed_process_terminal |  |  | owner=default |
| 43884 | 2026-09-08T12:58:33.252Z | proof_recorded |  |  | stage_id=check:9273835c18178321; status=passed; cache_hit=False; input_fingerprint=0ea101b6a381e95e0a37b9855a895afc1b9572b3c3ac36af9d75d806115178f3 |
| 43885 | 2026-09-08T12:58:33.441Z | proof_cache_miss |  |  | reason=cold; stage_id=check:10113b3f8fc4b7e9; input_fingerprint=d77092052caf75016dda9a0dc17b9c5e6b29f2f2ab0e52be6b7c81e111287a0c |
| 43886 | 2026-09-08T12:58:33.837Z | managed_process_admitted |  |  | owner=default |
| 43887 | 2026-09-08T12:58:34.187Z | managed_process_started |  |  | owner=default |
| 43888 | 2026-09-08T12:58:34.754Z | managed_process_terminal |  |  | owner=default |
| 43889 | 2026-09-08T12:58:35.134Z | proof_recorded |  |  | stage_id=check:10113b3f8fc4b7e9; status=passed; cache_hit=False; input_fingerprint=d77092052caf75016dda9a0dc17b9c5e6b29f2f2ab0e52be6b7c81e111287a0c |
| 43890 | 2026-09-08T12:58:35.364Z | observation_span_recorded |  |  |  |
| 43891 | 2026-09-08T12:58:35.618Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 43892 | 2026-09-08T12:59:00.471Z | quality_outcome_recorded |  |  |  |
| 43893 | 2026-09-08T12:59:00.674Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 43894 | 2026-09-08T12:59:00.990Z | observation_span_recorded |  |  |  |
| 43895 | 2026-09-08T12:59:01.201Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:ab3e5982ab79e3d6 | passed | 51c457d731f23b588ce797a5b95c056d7e339721f45627bcbc32973308d61d29 | False | 5362 | 0 |
| check:1a46f0fadadf887b | passed | 45e3210d71e954eb0ae28c056082ecb4eaeb598ffb29c3405a9463339cba4304 | False | 1456 | 0 |
| check:fb57f580333ccaca | passed | a5347a2932e7549173e063418931c0b585afdce33edf3dd2b709bb99b6b66b92 | False | 5604 | 0 |
| check:9273835c18178321 | passed | 0ea101b6a381e95e0a37b9855a895afc1b9572b3c3ac36af9d75d806115178f3 | False | 6280 | 0 |
| check:10113b3f8fc4b7e9 | passed | d77092052caf75016dda9a0dc17b9c5e6b29f2f2ab0e52be6b7c81e111287a0c | False | 1327 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 21d887b0bf674a139b532a2fc158ca16 | accepted | 7bc1caee37107a15e74eb078b52fe314e5fa33ab | d761db687262a3378e3cdaf690eb7197d9b10d97c72beaf9110b800db681ac37 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `45`
- Chain head: `cd6c95abb9aba86cef98dafcdb1a011c5101d2840cf147f4424cf495e6a25886`
