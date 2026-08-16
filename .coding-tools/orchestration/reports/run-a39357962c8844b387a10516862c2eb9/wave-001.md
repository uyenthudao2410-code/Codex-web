# Orchestration Wave 1

- Run: `a39357962c8844b387a10516862c2eb9`
- Wave: `8f9fed65f850414388724875b8b55bb8`
- Objective: Add first-class Recovery Tunnel configuration UX to the existing Electron app settings and expose its live status in the header. Preserve all existing dirty/concurrent work. Requirements: (1) Settings must contain a Recovery Tunnel section with editable recoveryTunnelId and clear helper text that it must differ from the primary tunnelId; (2) include an OpenAI Secure MCP Tunnel create/manage link pointing to https://platform.openai.com/settings/organization/tunnels, opened externally rather than navigated inside the app; (3) header status group currently showing MCP and Tunnel must add a third status item for Recovery/Tunnel cứu hộ with distinct states not_configured/connecting/connected/error and tooltip/detail text; (4) status must be driven by the existing recovery-plane service/state, never faked from presence of an ID; (5) saving a duplicate recoveryTunnelId equal to primary tunnelId must fail validation; (6) no secret/tokens displayed; (7) do not modify unrelated concurrent research/UI performance work. Identify the exact settings renderer, header renderer, preload/IPC/status plumbing, existing config validation, and relevant tests. Stop after returning a concrete minimal implementation plan and exact paths; do not mutate yet.
- Mode: `mcp_only`
- Base HEAD: `415cb658f43cbd1d2456f65bf5649ed52b87ab25`
- Worktree fingerprint: `b123a82362692bf71454db00af83a095432030ab934833320e2985aab2c34bc9`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 6958 | 2026-08-16T10:18:19.001Z | run_started |  | PREFLIGHT |  |
| 6959 | 2026-08-16T10:18:21.730Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 6960 | 2026-08-16T10:18:39.022Z | managed_process_admitted |  |  | owner=default |
| 6961 | 2026-08-16T10:18:39.221Z | managed_process_started |  |  | owner=default |
| 6962 | 2026-08-16T10:18:39.610Z | managed_process_terminal |  |  | owner=default |
| 6963 | 2026-08-16T10:18:45.619Z | managed_process_admitted |  |  | owner=default |
| 6964 | 2026-08-16T10:18:45.826Z | managed_process_started |  |  | owner=default |
| 6965 | 2026-08-16T10:18:46.148Z | managed_process_terminal |  |  | owner=default |
| 6966 | 2026-08-16T10:19:35.742Z | managed_process_admitted |  |  | owner=default |
| 6967 | 2026-08-16T10:19:35.957Z | managed_process_started |  |  | owner=default |
| 6968 | 2026-08-16T10:19:36.356Z | managed_process_terminal |  |  | owner=default |
| 6969 | 2026-08-16T10:20:35.057Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 6970 | 2026-08-16T10:21:11.858Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 6971 | 2026-08-16T10:21:11.982Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 6972 | 2026-08-16T10:21:12.116Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 6973 | 2026-08-16T10:21:12.232Z | state_transition | READY | ROUTED | reason=route_selected |
| 6974 | 2026-08-16T10:21:12.599Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=24e5951fb12f4efb9977b77af153f3d4 |
| 6975 | 2026-08-16T10:21:12.703Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 6976 | 2026-08-16T10:21:13.323Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=24e5951fb12f4efb9977b77af153f3d4 |
| 6977 | 2026-08-16T10:21:13.412Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 6978 | 2026-08-16T10:21:13.690Z | proof_cache_miss |  |  | reason=cold; stage_id=check:a515c278b0f72ec9; input_fingerprint=6d49e33946892cd8fb9aeae1a41582e4a7e2b1407972bc93e8858a37a240db31 |
| 6979 | 2026-08-16T10:21:13.865Z | managed_process_admitted |  |  | owner=default |
| 6980 | 2026-08-16T10:21:14.066Z | managed_process_started |  |  | owner=default |
| 6981 | 2026-08-16T10:21:14.849Z | managed_process_terminal |  |  | owner=default |
| 6982 | 2026-08-16T10:21:15.049Z | proof_recorded |  |  | stage_id=check:a515c278b0f72ec9; status=passed; cache_hit=False; input_fingerprint=6d49e33946892cd8fb9aeae1a41582e4a7e2b1407972bc93e8858a37a240db31 |
| 6983 | 2026-08-16T10:21:15.171Z | proof_cache_miss |  |  | reason=cold; stage_id=check:c6856677f4e8ee68; input_fingerprint=2e697d44846b46f76456bedb802f49634e0704032cfe95cab6c3eca71a9e3027 |
| 6984 | 2026-08-16T10:21:15.415Z | managed_process_admitted |  |  | owner=default |
| 6985 | 2026-08-16T10:21:15.635Z | managed_process_started |  |  | owner=default |
| 6986 | 2026-08-16T10:21:15.965Z | managed_process_terminal |  |  | owner=default |
| 6987 | 2026-08-16T10:21:16.182Z | proof_recorded |  |  | stage_id=check:c6856677f4e8ee68; status=passed; cache_hit=False; input_fingerprint=2e697d44846b46f76456bedb802f49634e0704032cfe95cab6c3eca71a9e3027 |
| 6988 | 2026-08-16T10:21:16.314Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=921d7a2d38aa9d1da05562c83e5065de5da50dce79d2e8c0fb168cee16597767 |
| 6989 | 2026-08-16T10:21:16.536Z | managed_process_admitted |  |  | owner=default |
| 6990 | 2026-08-16T10:21:16.785Z | managed_process_started |  |  | owner=default |
| 6991 | 2026-08-16T10:21:34.488Z | managed_process_terminal |  |  | owner=default |
| 6992 | 2026-08-16T10:21:34.708Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=921d7a2d38aa9d1da05562c83e5065de5da50dce79d2e8c0fb168cee16597767 |
| 6993 | 2026-08-16T10:21:35.250Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 6994 | 2026-08-16T10:23:17.149Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 6995 | 2026-08-16T10:23:17.408Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:a515c278b0f72ec9 | passed | 6d49e33946892cd8fb9aeae1a41582e4a7e2b1407972bc93e8858a37a240db31 | False | 1185 | 0 |
| check:c6856677f4e8ee68 | passed | 2e697d44846b46f76456bedb802f49634e0704032cfe95cab6c3eca71a9e3027 | False | 835 | 0 |
| verify:tests | passed | 921d7a2d38aa9d1da05562c83e5065de5da50dce79d2e8c0fb168cee16597767 | False | 18172 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| c6653d510b234024955b01f12715eae0 | accepted | 415cb658f43cbd1d2456f65bf5649ed52b87ab25 | 1dea81b9c9a84bad4fb253c5c0c16927078136b4a3d59448361be1de222a4a1d | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `38`
- Chain head: `e74db2ad096250fa5d1b0201deaa5f9407aa1f0609fbfe7ace664744db59a0b5`
