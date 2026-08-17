# Orchestration Wave 1

- Run: `c6235e7dfefe4df9938bf6d0b4c11bca`
- Wave: `b344e00d5ef64bc49668727834bf9e30`
- Objective: Build the fresh P0.2 NSIS acceptance installer from exact delivered HEAD acaa3582052ab6836ade7b55bd1ff2178ebc5117 after the sparse persisted-state Recovery Supervisor remediation. Do not modify source or external system state. Run the hardened npm run dist pipeline, collect the generated installer and packaged resource artifacts, and require terminal build success. The final proof must identify installer SHA-256/size and confirm the packaged recovery-supervisor script is byte-identical to the current source SHA-256 E0B906C1EC9AB5C3E9F1F52BA7B3D05F6FEFE42259F15A48AB3077A730076420.
- Mode: `mcp_only`
- Base HEAD: `acaa3582052ab6836ade7b55bd1ff2178ebc5117`
- Worktree fingerprint: `d616be680020a4a08fc31fc3faebeb18de79383ed04796edf35604d5e0d7e857`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 12597 | 2026-08-17T08:29:45.546Z | run_started |  | PREFLIGHT |  |
| 12598 | 2026-08-17T08:29:45.791Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 12599 | 2026-08-17T08:29:46.128Z | managed_process_admitted |  |  | owner=default |
| 12600 | 2026-08-17T08:29:46.430Z | managed_process_started |  |  | owner=default |
| 12601 | 2026-08-17T08:30:09.845Z | managed_process_terminal |  |  | owner=default |
| 12602 | 2026-08-17T08:30:10.030Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 12603 | 2026-08-17T08:30:10.211Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 12604 | 2026-08-17T08:30:10.400Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 12605 | 2026-08-17T08:30:10.628Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 12606 | 2026-08-17T08:30:10.786Z | state_transition | READY | ROUTED | reason=route_selected |
| 12607 | 2026-08-17T08:30:11.338Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=8f316b587f6b4037a23d4ba4ff2ff5d3 |
| 12608 | 2026-08-17T08:30:11.500Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 12609 | 2026-08-17T08:30:12.087Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=8f316b587f6b4037a23d4ba4ff2ff5d3 |
| 12610 | 2026-08-17T08:30:12.277Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 12611 | 2026-08-17T08:30:12.711Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:build; input_fingerprint=01110c7960d14cce3e4f6c6421fdb6073ec7c589748e545a0d404ef86d242bc8 |
| 12612 | 2026-08-17T08:30:13.130Z | managed_process_admitted |  |  | owner=default |
| 12613 | 2026-08-17T08:30:13.416Z | managed_process_started |  |  | owner=default |
| 12630 | 2026-08-17T08:31:27.718Z | managed_process_terminal |  |  | owner=default |
| 12631 | 2026-08-17T08:31:29.190Z | proof_recorded |  |  | stage_id=verify:build; status=passed; cache_hit=False; input_fingerprint=01110c7960d14cce3e4f6c6421fdb6073ec7c589748e545a0d404ef86d242bc8 |
| 12632 | 2026-08-17T08:31:29.541Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 12633 | 2026-08-17T08:34:00.244Z | managed_process_admitted |  |  | owner=chatweb-measurement |
| 12634 | 2026-08-17T08:34:00.575Z | managed_process_started |  |  | owner=chatweb-measurement |
| 12635 | 2026-08-17T08:34:01.110Z | managed_process_terminal |  |  | owner=chatweb-measurement |
| 12636 | 2026-08-17T08:35:01.544Z | managed_process_admitted |  |  | owner=chatweb-measurement |
| 12637 | 2026-08-17T08:35:01.895Z | managed_process_started |  |  | owner=chatweb-measurement |
| 12638 | 2026-08-17T08:35:02.485Z | managed_process_terminal |  |  | owner=chatweb-measurement |
| 12639 | 2026-08-17T08:35:17.152Z | managed_process_admitted |  |  | owner=chatweb-measurement |
| 12640 | 2026-08-17T08:35:17.541Z | managed_process_started |  |  | owner=chatweb-measurement |
| 12641 | 2026-08-17T08:35:37.130Z | managed_process_terminal |  |  | owner=chatweb-measurement |
| 12642 | 2026-08-17T08:36:54.600Z | managed_process_admitted |  |  | owner=default |
| 12643 | 2026-08-17T08:36:54.959Z | managed_process_started |  |  | owner=default |
| 12644 | 2026-08-17T08:36:55.411Z | managed_process_terminal |  |  | owner=default |
| 12645 | 2026-08-17T08:37:07.579Z | managed_process_admitted |  |  | owner=default |
| 12646 | 2026-08-17T08:37:07.891Z | managed_process_started |  |  | owner=default |
| 12647 | 2026-08-17T08:37:08.535Z | managed_process_terminal |  |  | owner=default |
| 12648 | 2026-08-17T08:37:11.993Z | managed_process_admitted |  |  | owner=chatweb-measurement |
| 12649 | 2026-08-17T08:37:12.343Z | managed_process_started |  |  | owner=chatweb-measurement |
| 12650 | 2026-08-17T08:37:12.824Z | managed_process_terminal |  |  | owner=chatweb-measurement |
| 12651 | 2026-08-17T08:37:23.202Z | managed_process_admitted |  |  | owner=chatweb-measurement |
| 12652 | 2026-08-17T08:37:23.517Z | managed_process_started |  |  | owner=chatweb-measurement |
| 12653 | 2026-08-17T08:37:23.980Z | managed_process_terminal |  |  | owner=chatweb-measurement |
| 12654 | 2026-08-17T08:37:31.676Z | managed_process_admitted |  |  | owner=default |
| 12655 | 2026-08-17T08:37:32.017Z | managed_process_started |  |  | owner=default |
| 12656 | 2026-08-17T08:37:32.876Z | managed_process_terminal |  |  | owner=default |
| 12657 | 2026-08-17T08:37:33.862Z | managed_process_admitted |  |  | owner=chatweb-measurement |
| 12658 | 2026-08-17T08:37:34.285Z | managed_process_started |  |  | owner=chatweb-measurement |
| 12659 | 2026-08-17T08:37:34.783Z | managed_process_terminal |  |  | owner=chatweb-measurement |
| 12660 | 2026-08-17T08:37:44.201Z | managed_process_admitted |  |  | owner=default |
| 12661 | 2026-08-17T08:37:44.551Z | managed_process_started |  |  | owner=default |
| 12662 | 2026-08-17T08:37:45.243Z | managed_process_terminal |  |  | owner=default |
| 12663 | 2026-08-17T08:37:53.418Z | managed_process_admitted |  |  | owner=chatweb-measurement |
| 12664 | 2026-08-17T08:37:53.759Z | managed_process_started |  |  | owner=chatweb-measurement |
| 12665 | 2026-08-17T08:37:54.326Z | managed_process_terminal |  |  | owner=chatweb-measurement |
| 12666 | 2026-08-17T08:38:02.860Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 12667 | 2026-08-17T08:38:03.309Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:build | passed | 01110c7960d14cce3e4f6c6421fdb6073ec7c589748e545a0d404ef86d242bc8 | False | 75953 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| 602eec726c7e405fbd8c536867c46501 | accepted | acaa3582052ab6836ade7b55bd1ff2178ebc5117 | 6465e12b8e3cc1f426b40b72528ae0000791641d553f731a1b7dca3481370e9d | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `55`
- Chain head: `b7902a13f4a21e5fe67443f454bd1e7c653b9702e5ba20cfaabec288fccd3fa6`
