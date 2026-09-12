# Orchestration Wave 4

- Run: `6f62b7ad85034167a3889a4dd996f6bc`
- Wave: `036dadac44d244d1b5048b50eca2e1ea`
- Objective: Continue N21 with a controller-authored deterministic patch, not another candidate-model attempt. Implement an atomic exact stale-run batch maintenance path for up to 64 explicit IDs: one immutable batch preflight for all targets, one BEGIN IMMEDIATE all-target guard revalidation followed by all-or-none mutation, one batch postflight/hash-chain proof; update the CLI and FullCleanActivation to invoke the complete batch rather than per-RUN loops; keep ordinary restart reasons capped separately; align RuntimeOrchestrator acceptance of the exact batch envelope. Preserve unrelated dirty bytes and verify, but do not rewrite, the existing RecoveryHost HANDOFF-yield reconnect repair. No runtime restart in this wave; no reset/clean/commit/push/package/release/deploy.
- Objective revision: `4`
- Objective SHA-256: `9776f3f239fd167645fc9c0171b39da591e01e7d3934762abaac007d229d94c5`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `7bc1caee37107a15e74eb078b52fe314e5fa33ab`
- Worktree fingerprint: `5ba63d33962971b8e2ca868861f040f4708602dc43f9ce95ae7cda05257a1942`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 48679 | 2026-09-11T03:24:35.375Z | wave_replanned |  | PREFLIGHT | reason=Wave 003 changed no source and the Sol candidate timed out before producing a patch. The causal source surface is already localized and baseline tests are green, so change strategy to a controller-authored deterministic patch on the exact known files, with focused proof after mutation; do not invoke another model lane. |
| 48680 | 2026-09-11T03:24:35.600Z | observation_span_recorded |  |  |  |
| 48681 | 2026-09-11T03:24:39.486Z | observation_span_recorded |  |  |  |
| 48682 | 2026-09-11T03:24:39.668Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 48684 | 2026-09-11T03:25:28.688Z | managed_process_admitted |  |  | owner=default |
| 48685 | 2026-09-11T03:25:29.178Z | managed_process_started |  |  | owner=default |
| 48686 | 2026-09-11T03:25:29.666Z | managed_process_terminal |  |  | owner=default |
| 48687 | 2026-09-11T03:25:45.098Z | managed_process_admitted |  |  | owner=default |
| 48688 | 2026-09-11T03:25:45.500Z | managed_process_started |  |  | owner=default |
| 48689 | 2026-09-11T03:25:46.031Z | managed_process_terminal |  |  | owner=default |
| 48690 | 2026-09-11T03:25:52.131Z | managed_process_admitted |  |  | owner=default |
| 48691 | 2026-09-11T03:25:52.558Z | managed_process_started |  |  | owner=default |
| 48692 | 2026-09-11T03:25:53.028Z | managed_process_terminal |  |  | owner=default |
| 48693 | 2026-09-11T03:26:00.017Z | managed_process_admitted |  |  | owner=default |
| 48694 | 2026-09-11T03:26:00.413Z | managed_process_started |  |  | owner=default |
| 48695 | 2026-09-11T03:26:00.864Z | managed_process_terminal |  |  | owner=default |
| 48696 | 2026-09-11T03:26:28.806Z | managed_process_admitted |  |  | owner=default |
| 48697 | 2026-09-11T03:26:29.232Z | managed_process_started |  |  | owner=default |
| 48698 | 2026-09-11T03:26:31.748Z | managed_process_terminal |  |  | owner=default |
| 48699 | 2026-09-11T03:26:40.354Z | managed_process_admitted |  |  | owner=default |
| 48700 | 2026-09-11T03:26:40.680Z | managed_process_started |  |  | owner=default |
| 48701 | 2026-09-11T03:26:41.129Z | managed_process_terminal |  |  | owner=default |
| 48702 | 2026-09-11T03:27:23.897Z | managed_process_admitted |  |  | owner=default |
| 48703 | 2026-09-11T03:27:24.258Z | managed_process_started |  |  | owner=default |
| 48704 | 2026-09-11T03:27:24.690Z | managed_process_terminal |  |  | owner=default |
| 48705 | 2026-09-11T03:27:33.167Z | managed_process_admitted |  |  | owner=default |
| 48706 | 2026-09-11T03:27:33.501Z | managed_process_started |  |  | owner=default |
| 48707 | 2026-09-11T03:27:35.200Z | managed_process_terminal |  |  | owner=default |
| 48708 | 2026-09-11T03:27:41.644Z | managed_process_admitted |  |  | owner=default |
| 48709 | 2026-09-11T03:27:41.977Z | managed_process_started |  |  | owner=default |
| 48710 | 2026-09-11T03:27:43.861Z | managed_process_terminal |  |  | owner=default |
| 48711 | 2026-09-11T03:28:24.877Z | managed_process_admitted |  |  | owner=default |
| 48712 | 2026-09-11T03:28:25.223Z | managed_process_started |  |  | owner=default |
| 48713 | 2026-09-11T03:28:25.706Z | managed_process_terminal |  |  | owner=default |
| 48714 | 2026-09-11T03:29:08.790Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 48715 | 2026-09-11T03:29:08.964Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 48716 | 2026-09-11T03:29:09.206Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 48717 | 2026-09-11T03:29:09.422Z | state_transition | READY | ROUTED | reason=route_selected |
| 48718 | 2026-09-11T03:29:09.612Z | observation_span_recorded |  |  |  |
| 48719 | 2026-09-11T03:29:10.661Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=7a295df92b644e5698e647e7d031471a |
| 48720 | 2026-09-11T03:29:10.832Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 48721 | 2026-09-11T03:29:11.535Z | patch_surface_observed |  |  |  |
| 48722 | 2026-09-11T03:29:11.719Z | observation_span_recorded |  |  |  |
| 48723 | 2026-09-11T03:29:11.947Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=7a295df92b644e5698e647e7d031471a |
| 48724 | 2026-09-11T03:29:12.112Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 48725 | 2026-09-11T03:29:13.520Z | observation_span_recorded |  |  |  |
| 48726 | 2026-09-11T03:29:13.678Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 48727 | 2026-09-11T03:29:21.085Z | managed_process_admitted |  |  | owner=default |
| 48728 | 2026-09-11T03:29:21.384Z | managed_process_started |  |  | owner=default |
| 48729 | 2026-09-11T03:29:21.774Z | managed_process_terminal |  |  | owner=default |
| 48730 | 2026-09-11T03:29:25.623Z | observation_span_recorded |  |  |  |
| 48731 | 2026-09-11T03:29:25.858Z | failure_observed | ACCEPTING | ACCEPTING | reason=Reject partial N21 wave: only the atomic ledger batch authority was added; CLI, immutable batch preflight/postflight wrapper, FullClean single-batch invocation, 64-ID exact maintenance envelope, and regression proof are still missing. Preserve the current source bytes for exact adoption in the next wave; no rollback/reset/clean.; failure_class=SOL_REJECTED |
| 48732 | 2026-09-11T03:29:26.380Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 48733 | 2026-09-11T03:29:26.697Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| - | - | - | - | - | - |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `230`
- Chain head: `8472b3a1abb2df938d5130adc92d4598067a4a18c83329f943f5b0d9660cc601`
