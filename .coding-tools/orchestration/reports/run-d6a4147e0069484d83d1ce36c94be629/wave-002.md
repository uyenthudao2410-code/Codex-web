# Orchestration Wave 2

- Run: `d6a4147e0069484d83d1ce36c94be629`
- Wave: `d6c0c31020474dbfb950b6819c3936ca`
- Objective: Read-only authoritative mapping for remaining P0.3 F1/F7/F8 on the current worktree. F1 requirement: killing/exiting the real UI/Electron client must not destroy independent Recovery Host ownership, and a replacement UI/client must reattach without replacing healthy Recovery Host/MCP/Tunnel ownership. F7 requirement: stale Recovery Host lock/ownership metadata from a dead owner must be safely reclaimed/recovered without adopting or killing unrelated live processes. F8 requirement: a live but unhealthy/foreign/mismatched owner/listener must fail closed rather than being adopted or killed. Inspect the current production code and exact tests, identify existing test names/assertions that satisfy each requirement, and identify any precise missing assertion or real product gap. Also locate the authoritative F1-F9 section in docs/PRODUCTION_CLOSURE_ROLLOUT.md. Do not mutate files, restart live production processes, or touch Operator Control Panel/UI source.
- Mode: `mcp_only`
- Base HEAD: `885260b404c2c64df1b1afa835963045ac55dbf6`
- Worktree fingerprint: `4d5b4b11860abcf28f1bbf4343aa14a6153c35b8ee5db28616f5ee37f005c65f`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 13764 | 2026-08-17T11:18:30.685Z | wave_replanned |  | PREFLIGHT | reason=The previous deterministic wave was rejected because it only re-ran focused tests and reported modified_files=[]; it never mutated the requested UI. Changed strategy: first gather exact current source anchors and routing implementation, then apply a complete explicit patch (rather than relying on objective-only autonomous mutation), followed by focused tests and controlled restart. |
| 13765 | 2026-08-17T11:18:31.909Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 13766 | 2026-08-17T11:18:42.085Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 13767 | 2026-08-17T11:18:42.318Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 13768 | 2026-08-17T11:18:42.462Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 13769 | 2026-08-17T11:18:42.647Z | state_transition | READY | ROUTED | reason=route_selected |
| 13770 | 2026-08-17T11:18:43.455Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=18283dffd94c4e2fbf6a4a189c71ee0d |
| 13771 | 2026-08-17T11:18:43.599Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 13772 | 2026-08-17T11:18:44.538Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=18283dffd94c4e2fbf6a4a189c71ee0d |
| 13773 | 2026-08-17T11:18:44.704Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 13774 | 2026-08-17T11:18:45.627Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:af6085c4efd56568; input_fingerprint=3fe571f0bec6fde50ef0403390d3fadb35e360c21f27f74b63e7726734c653cf |
| 13775 | 2026-08-17T11:18:46.793Z | managed_process_admitted |  |  | owner=default |
| 13776 | 2026-08-17T11:18:47.912Z | managed_process_started |  |  | owner=default |
| 13777 | 2026-08-17T11:18:49.421Z | managed_process_terminal |  |  | owner=default |
| 13778 | 2026-08-17T11:18:50.706Z | proof_recorded |  |  | stage_id=check:af6085c4efd56568; status=passed; cache_hit=False; input_fingerprint=3fe571f0bec6fde50ef0403390d3fadb35e360c21f27f74b63e7726734c653cf |
| 13779 | 2026-08-17T11:18:51.376Z | proof_cache_miss |  |  | reason=cold; stage_id=check:d3cd01cc730e34e4; input_fingerprint=d30aeb5f22fdc3d4fc825bf1043e0cbee34f2ed2d35cc54e7af03e77f385173f |
| 13780 | 2026-08-17T11:18:52.089Z | managed_process_admitted |  |  | owner=default |
| 13781 | 2026-08-17T11:18:52.387Z | managed_process_started |  |  | owner=default |
| 13782 | 2026-08-17T11:18:56.786Z | managed_process_terminal |  |  | owner=default |
| 13783 | 2026-08-17T11:18:57.249Z | proof_recorded |  |  | stage_id=check:d3cd01cc730e34e4; status=passed; cache_hit=False; input_fingerprint=d30aeb5f22fdc3d4fc825bf1043e0cbee34f2ed2d35cc54e7af03e77f385173f |
| 13784 | 2026-08-17T11:18:57.490Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=661133dd426d1ea963a9d8b9836292a56a8175c1b96d0afa4531f309725600cb |
| 13785 | 2026-08-17T11:18:58.057Z | managed_process_admitted |  |  | owner=default |
| 13786 | 2026-08-17T11:18:58.488Z | managed_process_started |  |  | owner=default |
| 13787 | 2026-08-17T11:19:05.898Z | managed_process_terminal |  |  | owner=default |
| 13788 | 2026-08-17T11:19:07.430Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=661133dd426d1ea963a9d8b9836292a56a8175c1b96d0afa4531f309725600cb |
| 13789 | 2026-08-17T11:19:08.291Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 13790 | 2026-08-17T11:20:14.172Z | managed_process_admitted |  |  | owner=chatweb |
| 13791 | 2026-08-17T11:20:14.566Z | managed_process_started |  |  | owner=chatweb |
| 13792 | 2026-08-17T11:20:15.064Z | managed_process_terminal |  |  | owner=chatweb |
| 13793 | 2026-08-17T11:20:22.565Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 13794 | 2026-08-17T11:20:22.977Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:af6085c4efd56568 | passed | 3fe571f0bec6fde50ef0403390d3fadb35e360c21f27f74b63e7726734c653cf | False | 4041 | 0 |
| check:d3cd01cc730e34e4 | passed | d30aeb5f22fdc3d4fc825bf1043e0cbee34f2ed2d35cc54e7af03e77f385173f | False | 5116 | 0 |
| verify:tests | passed | 661133dd426d1ea963a9d8b9836292a56a8175c1b96d0afa4531f309725600cb | False | 9389 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 4ae5b2b301ea4cd0a02a56e71e1f18f3 | accepted | 885260b404c2c64df1b1afa835963045ac55dbf6 | 4e118fde2a5e808e814bf5b1d86b1e66c45c5bbd7950c2781b9740b8b4126318 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `53`
- Chain head: `81726c3e445d87997fba72ef4ea76e2bf76744d78f3a63928da96ed6df89f3c7`
