# Orchestration Wave 2

- Run: `94609e3a8e4748c49a2deaba12d3c840`
- Wave: `c46383f33ad84f4785412a8911d51467`
- Objective: Fresh live L3 controller-usage canary after the successful UI/runtime activation. Bind this exact current ChatWeb turn to the current RUN lineage through the supported content-free host correlation path. Do not mutate source files, do not restart runtime, and do not read or persist prompt/assistant bodies. Preserve the canary long enough for post-response controller_usage to arrive; controller token fields must remain unknown_not_zero unless exact numeric usage is observed. This canary is for live evidence only and must be terminalized after post-response inspection.
- Objective revision: `2`
- Objective SHA-256: `cfa81ab8d3210a849ef2fe89c2a1d2e692e05785828193d8fd457a6cd75edefb`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `80aceb583202ad381c25687969fb48adbf74622c`
- Worktree fingerprint: `6e9a91755453f579b1b44200b78043fb1794a60c0b9770d93484d0c428df5dd2`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 37704 | 2026-09-03T16:08:09.490Z | wave_replanned |  | PREFLIGHT | reason=The immediately preceding canary attempt was rejected before useful execution because it lacked a required read-only check command. This wave adds the smallest supported non-mutating oracle, `npm run dev:status`, while preserving the same live L3 host-correlation objective and zero-write scope. |
| 37705 | 2026-09-03T16:08:09.667Z | observation_span_recorded |  |  |  |
| 37706 | 2026-09-03T16:08:10.561Z | observation_span_recorded |  |  |  |
| 37707 | 2026-09-03T16:08:10.797Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 37708 | 2026-09-03T16:08:10.989Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 37709 | 2026-09-03T16:08:11.190Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 37710 | 2026-09-03T16:08:11.339Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 37711 | 2026-09-03T16:08:11.566Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 37712 | 2026-09-03T16:08:11.764Z | state_transition | READY | ROUTED | reason=route_selected |
| 37713 | 2026-09-03T16:08:11.967Z | observation_span_recorded |  |  |  |
| 37714 | 2026-09-03T16:08:12.917Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=4b27e8fb1f824de993735429ac4c2ed8 |
| 37715 | 2026-09-03T16:08:13.108Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 37716 | 2026-09-03T16:08:14.052Z | observation_span_recorded |  |  |  |
| 37717 | 2026-09-03T16:08:14.609Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=4b27e8fb1f824de993735429ac4c2ed8 |
| 37718 | 2026-09-03T16:08:14.952Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 37719 | 2026-09-03T16:08:15.932Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=check:385f51573288f6e6; input_fingerprint=f0dd3cb3bd95ddb53910586c64d21647cf1c3ee3141eb335b065b615fc3e530b |
| 37720 | 2026-09-03T16:08:16.356Z | managed_process_admitted |  |  | owner=default |
| 37721 | 2026-09-03T16:08:16.732Z | managed_process_started |  |  | owner=default |
| 37722 | 2026-09-03T16:08:17.565Z | managed_process_terminal |  |  | owner=default |
| 37723 | 2026-09-03T16:08:17.961Z | proof_recorded |  |  | stage_id=check:385f51573288f6e6; status=passed; cache_hit=False; input_fingerprint=f0dd3cb3bd95ddb53910586c64d21647cf1c3ee3141eb335b065b615fc3e530b |
| 37724 | 2026-09-03T16:08:18.173Z | observation_span_recorded |  |  |  |
| 37725 | 2026-09-03T16:08:18.382Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 37726 | 2026-09-03T16:09:35.597Z | managed_process_admitted |  |  | owner=chatweb-l3-live-correlation |
| 37727 | 2026-09-03T16:09:35.990Z | managed_process_started |  |  | owner=chatweb-l3-live-correlation |
| 37728 | 2026-09-03T16:09:36.665Z | managed_process_terminal |  |  | owner=chatweb-l3-live-correlation |
| 37729 | 2026-09-03T16:10:27.464Z | observation_span_recorded |  |  |  |
| 37730 | 2026-09-03T16:10:27.689Z | failure_observed | ACCEPTING | ACCEPTING | reason=Reject this read-only L3 canary as non-qualifying live evidence. The content-free journal shows the current user turn was already older than the 120s pending-host-turn TTL when the canary RUN/WAVE executed, both pending and binding files were missing, no host turn/trace was attached to this RUN/WAVE, and usage_event_count remained 0. Preserve controller usage as unknown_not_zero; do not accept or splice this canary into L4.; failure_class=SOL_REJECTED |
| 37731 | 2026-09-03T16:10:27.905Z | state_transition | ACCEPTING | REPLAN | reason=SOL_REJECTED; failure_class=SOL_REJECTED |
| 37732 | 2026-09-03T16:10:28.129Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |
| 37733 | 2026-09-03T16:12:14.958Z | state_transition | REPLAN | ABORTED | reason=Terminalize the rejected read-only L3 canary. It produced no qualifying host correlation or usage evidence and must not remain active before a fresh host-turn canary. |
| 37734 | 2026-09-03T16:12:15.492Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:385f51573288f6e6 | passed | f0dd3cb3bd95ddb53910586c64d21647cf1c3ee3141eb335b065b615fc3e530b | False | 1673 | 0 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `48`
- Chain head: `292b154c4e93b0b544d848b69e6205158521b8963d81912c6207c692e78bd0a3`
