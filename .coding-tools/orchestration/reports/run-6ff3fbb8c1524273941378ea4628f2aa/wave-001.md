# Orchestration Wave 1

- Run: `6ff3fbb8c1524273941378ea4628f2aa`
- Wave: `866b6fd12cc245998a5f3f80719cbb7d`
- Objective: Build and verify the final local NSIS release-candidate artifact from the already accepted source fingerprint. Run the complete dist script, re-run packaged Recovery smoke against the final win-unpacked output, verify git diff/source-root hygiene, and print content-free installer SHA-256, size, and mtime. Local verification only: no release/publish/deploy, no commit/push, no live runtime restart, no provider dispatch.
- Mode: `mcp_only`
- Base HEAD: `640ad37e3e571a0a56af376e9d3bda2b89bf0669`
- Worktree fingerprint: `cae7694780453fd0ca2fa28930eb916ba245fa23e09666d2e3452811354e9050`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 25882 | 2026-08-21T04:27:37.644Z | run_started |  | PREFLIGHT |  |
| 25883 | 2026-08-21T04:27:37.958Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 25884 | 2026-08-21T04:27:38.152Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 25885 | 2026-08-21T04:27:38.308Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 25886 | 2026-08-21T04:27:38.494Z | state_transition | READY | ROUTED | reason=route_selected |
| 25887 | 2026-08-21T04:27:39.600Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=c133c7268b964e37a2b65cefa400801c |
| 25888 | 2026-08-21T04:27:39.744Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 25889 | 2026-08-21T04:27:40.300Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=c133c7268b964e37a2b65cefa400801c |
| 25890 | 2026-08-21T04:27:40.450Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 25891 | 2026-08-21T04:27:41.020Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:e449d13f93c687d1; input_fingerprint=53b6fe7c3806df7f3c5c924514c3f3a5c0e35c9f442600b3d47d2ca18a75d3d8 |
| 25892 | 2026-08-21T04:27:41.535Z | managed_process_admitted |  |  | owner=default |
| 25893 | 2026-08-21T04:27:41.855Z | managed_process_started |  |  | owner=default |
| 25894 | 2026-08-21T04:28:55.021Z | managed_process_admitted |  |  | owner=default |
| 25895 | 2026-08-21T04:28:55.535Z | managed_process_started |  |  | owner=default |
| 25896 | 2026-08-21T04:29:04.325Z | managed_process_terminal |  |  | owner=default |
| 25897 | 2026-08-21T04:29:16.556Z | managed_process_terminal |  |  | owner=default |
| 25898 | 2026-08-21T04:29:16.823Z | proof_recorded |  |  | stage_id=check:e449d13f93c687d1; status=passed; cache_hit=False; input_fingerprint=53b6fe7c3806df7f3c5c924514c3f3a5c0e35c9f442600b3d47d2ca18a75d3d8 |
| 25899 | 2026-08-21T04:29:16.970Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:470e7e0d382448b5; input_fingerprint=de78e93c3d659b72067aeba2377d24af94cf21f01789423b4fa9ddd3a14f7180 |
| 25900 | 2026-08-21T04:29:17.314Z | managed_process_admitted |  |  | owner=default |
| 25901 | 2026-08-21T04:29:17.580Z | managed_process_started |  |  | owner=default |
| 25902 | 2026-08-21T04:29:24.765Z | managed_process_terminal |  |  | owner=default |
| 25903 | 2026-08-21T04:29:25.182Z | proof_recorded |  |  | stage_id=check:470e7e0d382448b5; status=passed; cache_hit=False; input_fingerprint=de78e93c3d659b72067aeba2377d24af94cf21f01789423b4fa9ddd3a14f7180 |
| 25904 | 2026-08-21T04:29:25.359Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:466c2f308b48c766; input_fingerprint=9fc8122f388b3122a39d046072c547747bd91d3a669a1ddc8eee0b66a0b07332 |
| 25905 | 2026-08-21T04:29:26.006Z | managed_process_admitted |  |  | owner=default |
| 25906 | 2026-08-21T04:29:26.282Z | managed_process_started |  |  | owner=default |
| 25907 | 2026-08-21T04:29:26.492Z | managed_process_admitted |  |  | owner=default |
| 25908 | 2026-08-21T04:29:27.000Z | managed_process_started |  |  | owner=default |
| 25909 | 2026-08-21T04:29:27.393Z | managed_process_terminal |  |  | owner=default |
| 25910 | 2026-08-21T04:29:27.599Z | managed_process_terminal |  |  | owner=default |
| 25911 | 2026-08-21T04:29:28.226Z | proof_recorded |  |  | stage_id=check:466c2f308b48c766; status=passed; cache_hit=False; input_fingerprint=9fc8122f388b3122a39d046072c547747bd91d3a669a1ddc8eee0b66a0b07332 |
| 25912 | 2026-08-21T04:29:28.393Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:5d2bd3e0ac5171d0; input_fingerprint=50b51cbc4317523662e0295c260d6f5cabb292919dbbe1a8c9cf631884172f6f |
| 25913 | 2026-08-21T04:29:28.723Z | managed_process_admitted |  |  | owner=default |
| 25914 | 2026-08-21T04:29:28.980Z | managed_process_started |  |  | owner=default |
| 25915 | 2026-08-21T04:29:29.412Z | managed_process_terminal |  |  | owner=default |
| 25916 | 2026-08-21T04:29:29.709Z | proof_recorded |  |  | stage_id=check:5d2bd3e0ac5171d0; status=passed; cache_hit=False; input_fingerprint=50b51cbc4317523662e0295c260d6f5cabb292919dbbe1a8c9cf631884172f6f |
| 25917 | 2026-08-21T04:29:29.956Z | proof_cache_miss |  |  | reason=cold; stage_id=check:bd92fb89df334463; input_fingerprint=9be565f742ed220183383d3de72adc57d13e026e3e082585864f100e735e50af |
| 25918 | 2026-08-21T04:29:30.092Z | failure_observed | PROVING | PROVING | failure_class=PERMISSION_REQUIRED |
| 25919 | 2026-08-21T04:29:30.282Z | state_transition | PROVING | REPLAN | reason=PERMISSION_REQUIRED; failure_class=PERMISSION_REQUIRED |
| 25920 | 2026-08-21T04:29:30.411Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:e449d13f93c687d1 | passed | 53b6fe7c3806df7f3c5c924514c3f3a5c0e35c9f442600b3d47d2ca18a75d3d8 | False | 95334 | 0 |
| check:470e7e0d382448b5 | passed | de78e93c3d659b72067aeba2377d24af94cf21f01789423b4fa9ddd3a14f7180 | False | 7757 | 0 |
| check:466c2f308b48c766 | passed | 9fc8122f388b3122a39d046072c547747bd91d3a669a1ddc8eee0b66a0b07332 | False | 2416 | 0 |
| check:5d2bd3e0ac5171d0 | passed | 50b51cbc4317523662e0295c260d6f5cabb292919dbbe1a8c9cf631884172f6f | False | 1020 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `86`
- Chain head: `c279f696ad227144f73aa3f55d5e2582310ef2d2b424f06a2cdf03a5c8d3ff25`
