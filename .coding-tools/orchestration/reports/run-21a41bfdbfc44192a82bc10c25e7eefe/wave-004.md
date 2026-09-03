# Orchestration Wave 4

- Run: `21a41bfdbfc44192a82bc10c25e7eefe`
- Wave: `1c1580a02cc84d78a06fd366fa28726f`
- Objective: Prepare the smallest exact patch for RUN 21a. Read current source and callsites only. Determine: (1) the minimal single Python authority for host-observation schema v6 without circular imports; (2) the exact response envelope keys actually needed to discover response.completed/response while never traversing message/output/content or arbitrary arrays/objects; (3) the actual HTTP identity/provenance fields used before controller usage ledger mutation; (4) the authoritative current RUN/WAVE and host/evaluation turn/trace correlation surfaces; (5) how _require_hub_controller proves the same controller lease is active and how to test expiry/mismatch. Preserve first-call compatibility only where there is genuinely no RUN/WAVE authority; once authority exists, incomplete or mismatched provenance must fail closed. Do not mutate or run verification in prepare.
- Objective revision: `4`
- Objective SHA-256: `e4b89b15b2714ab7b6276df13b13b18054b86c3f94ae34549b23dedaf86ff154`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `753839c6ce2254b680f3440b0e6ab8143dd0735633ca8b86f31b93e887b11779`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 36795 | 2026-09-03T08:57:20.235Z | wave_replanned |  | PREFLIGHT | reason=Fresh operator-approved proof c7100287b838432ea6edca774f24ac2d passed git diff --check and JS 7/7 but failed Python 56-pass/5-fail because current evaluation fixtures still emit schema v5. Current semantic materialization separately proves evidence_completeness.py still hard-codes current host schema v5 and chatEvaluationJournal.js still uses generic Object.values traversal. Replan this same RUN to mutate only the approved packet/directly necessary shared authority and close these concrete gaps plus strict controller provenance, authoritative RUN/WAVE/turn/trace correlation, unsafe-integer/duplicate-conflict handling, and same-wave active-lease CHECKPOINTED ingress. Preserve accidental dist artifacts and unrelated dirty work; do not run npm/build/package. |
| 36796 | 2026-09-03T08:57:20.408Z | observation_span_recorded |  |  |  |
| 36797 | 2026-09-03T08:57:22.541Z | observation_span_recorded |  |  |  |
| 36798 | 2026-09-03T08:57:22.749Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 36805 | 2026-09-03T09:02:00.208Z | managed_process_admitted |  |  | owner=chatweb-run21a-read |
| 36806 | 2026-09-03T09:02:01.564Z | managed_process_started |  |  | owner=chatweb-run21a-read |
| 36807 | 2026-09-03T09:02:03.035Z | managed_process_terminal |  |  | owner=chatweb-run21a-read |
| 36812 | 2026-09-03T09:04:14.610Z | managed_process_admitted |  |  | owner=chatweb-run21a-verify |
| 36813 | 2026-09-03T09:04:14.908Z | managed_process_started |  |  | owner=chatweb-run21a-verify |
| 36816 | 2026-09-03T09:04:16.191Z | managed_process_terminal |  |  | owner=chatweb-run21a-verify |
| 36819 | 2026-09-03T09:05:33.118Z | managed_process_admitted |  |  | owner=chatweb-run21a-read |
| 36820 | 2026-09-03T09:05:33.380Z | managed_process_started |  |  | owner=chatweb-run21a-read |
| 36821 | 2026-09-03T09:05:33.822Z | managed_process_terminal |  |  | owner=chatweb-run21a-read |
| 36826 | 2026-09-03T09:07:26.653Z | managed_process_admitted |  |  | owner=chatweb-run21a-control-inspect |
| 36827 | 2026-09-03T09:07:26.860Z | managed_process_started |  |  | owner=chatweb-run21a-control-inspect |
| 36828 | 2026-09-03T09:07:27.336Z | managed_process_terminal |  |  | owner=chatweb-run21a-control-inspect |
| 36829 | 2026-09-03T09:07:41.019Z | managed_process_admitted |  |  | owner=chatweb-run21a-control-inspect |
| 36830 | 2026-09-03T09:07:41.325Z | managed_process_started |  |  | owner=chatweb-run21a-control-inspect |
| 36831 | 2026-09-03T09:07:41.825Z | managed_process_terminal |  |  | owner=chatweb-run21a-control-inspect |
| 36832 | 2026-09-03T09:07:52.626Z | managed_process_admitted |  |  | owner=chatweb-run21a-control-inspect |
| 36833 | 2026-09-03T09:07:52.908Z | managed_process_started |  |  | owner=chatweb-run21a-control-inspect |
| 36834 | 2026-09-03T09:07:53.495Z | managed_process_terminal |  |  | owner=chatweb-run21a-control-inspect |
| 36835 | 2026-09-03T09:09:13.110Z | managed_process_admitted |  |  | owner=chatweb-run21a-control-inspect |
| 36836 | 2026-09-03T09:09:13.409Z | managed_process_started |  |  | owner=chatweb-run21a-control-inspect |
| 36837 | 2026-09-03T09:09:14.001Z | managed_process_terminal |  |  | owner=chatweb-run21a-control-inspect |
| 36838 | 2026-09-03T09:09:23.494Z | managed_process_admitted |  |  | owner=chatweb-run21a-control-inspect |
| 36839 | 2026-09-03T09:09:23.785Z | managed_process_started |  |  | owner=chatweb-run21a-control-inspect |
| 36840 | 2026-09-03T09:09:24.370Z | managed_process_terminal |  |  | owner=chatweb-run21a-control-inspect |
| 36841 | 2026-09-03T09:09:33.834Z | managed_process_admitted |  |  | owner=chatweb-run21a-control-inspect |
| 36842 | 2026-09-03T09:09:34.117Z | managed_process_started |  |  | owner=chatweb-run21a-control-inspect |
| 36843 | 2026-09-03T09:09:34.692Z | managed_process_terminal |  |  | owner=chatweb-run21a-control-inspect |
| 36844 | 2026-09-03T09:09:41.186Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 36845 | 2026-09-03T09:09:41.360Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 36846 | 2026-09-03T09:09:41.535Z | route_selected | READY | READY | reason=explicit_request; requested=deterministic; resolved=deterministic |
| 36847 | 2026-09-03T09:09:41.692Z | state_transition | READY | ROUTED | reason=route_selected |
| 36848 | 2026-09-03T09:09:42.025Z | observation_span_recorded |  |  |  |
| 36849 | 2026-09-03T09:09:43.028Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=9d61db93f6de4e7e95f92cb7a5dc2d47 |
| 36850 | 2026-09-03T09:09:43.314Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 36851 | 2026-09-03T09:09:44.060Z | managed_process_admitted |  |  | owner=chatweb-run21a-control-inspect |
| 36852 | 2026-09-03T09:09:44.322Z | managed_process_started |  |  | owner=chatweb-run21a-control-inspect |
| 36853 | 2026-09-03T09:09:44.530Z | existing_file_adoption_observed |  |  |  |
| 36854 | 2026-09-03T09:09:44.708Z | observation_span_recorded |  |  |  |
| 36855 | 2026-09-03T09:09:45.197Z | managed_process_terminal |  |  | owner=chatweb-run21a-control-inspect |
| 36856 | 2026-09-03T09:09:45.458Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=9d61db93f6de4e7e95f92cb7a5dc2d47 |
| 36857 | 2026-09-03T09:09:45.647Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 36858 | 2026-09-03T09:09:46.367Z | managed_process_admitted |  |  | owner=chatweb-run21a-hash |
| 36859 | 2026-09-03T09:09:46.711Z | managed_process_started |  |  | owner=chatweb-run21a-hash |
| 36860 | 2026-09-03T09:09:46.879Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=120b88a408a4d48a534417a32ed8c6ace3764726b89cc385ce393b136c8a6b7a |
| 36861 | 2026-09-03T09:09:47.305Z | managed_process_admitted |  |  | owner=default |
| 36862 | 2026-09-03T09:09:47.750Z | managed_process_terminal |  |  | owner=chatweb-run21a-hash |
| 36863 | 2026-09-03T09:09:47.954Z | managed_process_started |  |  | owner=default |
| 36864 | 2026-09-03T09:09:55.167Z | managed_process_admitted |  |  | owner=chatweb-run21a-diff |
| 36865 | 2026-09-03T09:09:55.462Z | managed_process_started |  |  | owner=chatweb-run21a-diff |
| 36866 | 2026-09-03T09:09:55.982Z | managed_process_terminal |  |  | owner=chatweb-run21a-diff |
| 36867 | 2026-09-03T09:09:57.624Z | managed_process_admitted |  |  | owner=chatweb-run21a-control-inspect |
| 36868 | 2026-09-03T09:09:57.929Z | managed_process_started |  |  | owner=chatweb-run21a-control-inspect |
| 36869 | 2026-09-03T09:09:58.608Z | managed_process_terminal |  |  | owner=chatweb-run21a-control-inspect |
| 36870 | 2026-09-03T09:10:07.104Z | managed_process_admitted |  |  | owner=chatweb-run21a-read2 |
| 36871 | 2026-09-03T09:10:07.395Z | managed_process_started |  |  | owner=chatweb-run21a-read2 |
| 36872 | 2026-09-03T09:10:08.384Z | managed_process_terminal |  |  | owner=chatweb-run21a-read2 |
| 36873 | 2026-09-03T09:10:13.576Z | managed_process_admitted |  |  | owner=chatweb-run21a-read |
| 36874 | 2026-09-03T09:10:13.860Z | managed_process_started |  |  | owner=chatweb-run21a-read |
| 36875 | 2026-09-03T09:10:14.592Z | managed_process_terminal |  |  | owner=chatweb-run21a-read |
| 36876 | 2026-09-03T09:10:20.351Z | managed_process_admitted |  |  | owner=chatweb-run21a-callsite |
| 36877 | 2026-09-03T09:10:20.660Z | managed_process_started |  |  | owner=chatweb-run21a-callsite |
| 36878 | 2026-09-03T09:10:21.483Z | managed_process_terminal |  |  | owner=default |
| 36879 | 2026-09-03T09:10:21.724Z | managed_process_terminal |  |  | owner=chatweb-run21a-callsite |
| 36880 | 2026-09-03T09:10:22.148Z | proof_recorded |  |  | stage_id=verify:tests; status=failed; cache_hit=False; input_fingerprint=120b88a408a4d48a534417a32ed8c6ace3764726b89cc385ce393b136c8a6b7a |
| 36881 | 2026-09-03T09:10:22.369Z | observation_span_recorded |  |  |  |
| 36882 | 2026-09-03T09:10:22.399Z | failure_observed | PROVING | PROVING | failure_class=BUILD_VERIFICATION_FAILED |
| 36883 | 2026-09-03T09:10:22.614Z | state_transition | PROVING | REPLAN | reason=BUILD_VERIFICATION_FAILED; failure_class=BUILD_VERIFICATION_FAILED |
| 36884 | 2026-09-03T09:10:22.834Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | failed | 120b88a408a4d48a534417a32ed8c6ace3764726b89cc385ce393b136c8a6b7a | False | 34656 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `477`
- Chain head: `d5d92b6a865dd8405169addd711fceac1741f551a0ecc3cbbc612370d70344c6`
