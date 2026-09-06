# Orchestration Wave 4

- Run: `afd57ba0d9d34a6b9b9d7b5e65775590`
- Wave: `1a8d87e465b14b229b47fae6485dd6cf`
- Objective: Continue the same C5 material RUN from the already-installed current 1.0.0 state created by Wave 6380d0a4c21246a6bb753bb3b12cb829. Do not reinstall. Correct the stale registry oracle: the actual NSIS DisplayName is 'Coding Tools MCP 1.0.0', with DisplayVersion 1.0.0 and an UninstallString rooted under C:\Users\Admin\AppData\Local\Temp\codex-web-c5-9e752e34\install. Capture that install proof, run Recovery Host only with isolated APPDATA/LOCALAPPDATA/user-data and no tunnel/autostart, prove descriptor owner/process/loopback listener without HTTP, kill only that isolated process tree, silently uninstall, verify current shortcuts/registry/install root are removed, locate and preserve the pre-existing legacy shortcut by its immutable SHA256 393337c654c77795dad8a847a259391364635ed058e75603314b8321200c5957 rather than its corrupted JSON path string, and verify production descriptor and Recovery Supervisor definition equal baseline. Authenticated HTTP ping remains BLOCKED_BY_SERVER_POLICY. No C4 rerun, historical installer, normal UI, publish/tag/release/deploy, or forbidden ACK.
- Objective revision: `4`
- Objective SHA-256: `6594aa2cbae848bc3a40906a2550ed8cc3a29e9a85e2c80e2d5e9425a9f1a6f0`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `9e752e34db745cd4fb2d0830a517910eced9c37f`
- Worktree fingerprint: `6546f235f77e31e7b47a1f6c568d1f6291fec2c3fce76edc6b85030cc9b5259e`
- Contract fingerprint: `4d349d411b8887238ad4a1f9f43404a9bef00c6de368373ca6d72f1c271aea86`
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 41666 | 2026-09-06T05:58:16.207Z | wave_replanned |  | PREFLIGHT | reason=Wave 6380d0a4c21246a6bb753bb3b12cb829 successfully created the isolated test root and installed current 1.0.0 with installer exit 0, then failed only because the registry oracle required DisplayName exactly 'Coding Tools MCP'. Read-only reconciliation proved one legitimate HKCU entry exists with DisplayName='Coding Tools MCP 1.0.0', DisplayVersion=1.0.0 and uninstaller rooted under the C5 install directory; install process count=0; current Desktop and Start Menu shortcuts were created; production descriptor remained d2705139ef748fa373576ee9ab78ac11c845e70dc076f459685ecf5b136a7faa; Recovery Supervisor hash remained 593b511132d10acd3d675c867a498525354d0eeab7c8c8c3ccfebe302e4e3d61; and the pre-existing legacy shortcut still exists byte-identically at SHA256 393337c654c77795dad8a847a259391364635ed058e75603314b8321200c5957. Continue from installed state without reinstall and correct only the stale oracle/path-encoding assumptions. |
| 41667 | 2026-09-06T05:58:16.453Z | observation_span_recorded |  |  |  |
| 41668 | 2026-09-06T05:58:17.882Z | observation_span_recorded |  |  |  |
| 41669 | 2026-09-06T05:58:18.200Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 41670 | 2026-09-06T05:58:18.417Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 41671 | 2026-09-06T05:58:18.683Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 41672 | 2026-09-06T05:58:19.014Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 41673 | 2026-09-06T05:58:19.408Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 41674 | 2026-09-06T05:58:19.840Z | state_transition | READY | ROUTED | reason=route_selected |
| 41675 | 2026-09-06T05:58:20.236Z | observation_span_recorded |  |  |  |
| 41676 | 2026-09-06T05:58:21.416Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=992ac55ff1d7493196c34b7489f16cfa |
| 41677 | 2026-09-06T05:58:21.705Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 41679 | 2026-09-06T05:58:23.200Z | observation_span_recorded |  |  |  |
| 41680 | 2026-09-06T05:58:23.891Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=992ac55ff1d7493196c34b7489f16cfa |
| 41681 | 2026-09-06T05:58:24.141Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 41683 | 2026-09-06T05:58:25.304Z | proof_cache_miss |  |  | reason=cold; stage_id=check:4cad43a2958f6fb4; input_fingerprint=a46312e3d390546bfea2a16364a845dc2272bd979b22c6523c7e42a57c794726 |
| 41684 | 2026-09-06T05:58:25.799Z | managed_process_admitted |  |  | owner=default |
| 41685 | 2026-09-06T05:58:26.439Z | managed_process_started |  |  | owner=default |
| 41686 | 2026-09-06T05:58:28.642Z | managed_process_terminal |  |  | owner=default |
| 41687 | 2026-09-06T05:58:29.310Z | proof_recorded |  |  | stage_id=check:4cad43a2958f6fb4; status=passed; cache_hit=False; input_fingerprint=a46312e3d390546bfea2a16364a845dc2272bd979b22c6523c7e42a57c794726 |
| 41688 | 2026-09-06T05:58:29.540Z | proof_cache_miss |  |  | reason=cold; stage_id=check:a179fdbfc86ef952; input_fingerprint=934fe7e8c604ed79f21d12b964b1aaa7c7c2867b5efa3699da82875a6516bb37 |
| 41690 | 2026-09-06T05:58:30.555Z | managed_process_admitted |  |  | owner=default |
| 41692 | 2026-09-06T05:58:31.232Z | managed_process_started |  |  | owner=default |
| 41693 | 2026-09-06T05:58:37.764Z | managed_process_terminal |  |  | owner=default |
| 41694 | 2026-09-06T05:58:39.568Z | proof_recorded |  |  | stage_id=check:a179fdbfc86ef952; status=passed; cache_hit=False; input_fingerprint=934fe7e8c604ed79f21d12b964b1aaa7c7c2867b5efa3699da82875a6516bb37 |
| 41695 | 2026-09-06T05:58:40.908Z | proof_cache_miss |  |  | reason=cold; stage_id=check:44a49412fa7b0ddd; input_fingerprint=a557485c76ac8dd95d997a8214674e285eb6735118ff0598dd950432fb018edb |
| 41696 | 2026-09-06T05:58:43.182Z | managed_process_admitted |  |  | owner=default |
| 41697 | 2026-09-06T05:58:44.030Z | managed_process_started |  |  | owner=default |
| 41698 | 2026-09-06T05:58:52.142Z | managed_process_terminal |  |  | owner=default |
| 41699 | 2026-09-06T05:58:53.076Z | proof_recorded |  |  | stage_id=check:44a49412fa7b0ddd; status=passed; cache_hit=False; input_fingerprint=a557485c76ac8dd95d997a8214674e285eb6735118ff0598dd950432fb018edb |
| 41700 | 2026-09-06T05:58:53.391Z | proof_cache_miss |  |  | reason=cold; stage_id=check:03ae778e17b1e464; input_fingerprint=e7cd3d51e19dacb2e70e82a73c18ea55c65fa805bea87cf6a8b13bd2f123cb02 |
| 41701 | 2026-09-06T05:58:53.932Z | managed_process_admitted |  |  | owner=default |
| 41702 | 2026-09-06T05:58:54.250Z | managed_process_started |  |  | owner=default |
| 41703 | 2026-09-06T05:58:56.419Z | managed_process_terminal |  |  | owner=default |
| 41704 | 2026-09-06T05:58:56.969Z | proof_recorded |  |  | stage_id=check:03ae778e17b1e464; status=passed; cache_hit=False; input_fingerprint=e7cd3d51e19dacb2e70e82a73c18ea55c65fa805bea87cf6a8b13bd2f123cb02 |
| 41705 | 2026-09-06T05:58:57.211Z | observation_span_recorded |  |  |  |
| 41706 | 2026-09-06T05:58:57.554Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 41723 | 2026-09-06T05:59:15.437Z | quality_outcome_recorded |  |  |  |
| 41724 | 2026-09-06T05:59:15.681Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 41725 | 2026-09-06T05:59:16.058Z | observation_span_recorded |  |  |  |
| 41726 | 2026-09-06T05:59:16.376Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:4cad43a2958f6fb4 | passed | a46312e3d390546bfea2a16364a845dc2272bd979b22c6523c7e42a57c794726 | False | 3422 | 0 |
| check:a179fdbfc86ef952 | passed | 934fe7e8c604ed79f21d12b964b1aaa7c7c2867b5efa3699da82875a6516bb37 | False | 8972 | 0 |
| check:44a49412fa7b0ddd | passed | a557485c76ac8dd95d997a8214674e285eb6735118ff0598dd950432fb018edb | False | 9915 | 0 |
| check:03ae778e17b1e464 | passed | e7cd3d51e19dacb2e70e82a73c18ea55c65fa805bea87cf6a8b13bd2f123cb02 | False | 3079 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| b51dd665a3dc4db7ac5c73d93f160f02 | accepted | 9e752e34db745cd4fb2d0830a517910eced9c37f | 1fd81f1423b2515edc64e3639141226cdf80749c5bf57664db747b87fd20a5bc | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `114`
- Chain head: `5612743aa5665c91bcb01266569110632f1972baf496a720e10100a01c621dfe`
