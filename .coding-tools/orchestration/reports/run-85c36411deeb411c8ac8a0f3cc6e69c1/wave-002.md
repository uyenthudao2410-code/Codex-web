# Orchestration Wave 2

- Run: `85c36411deeb411c8ac8a0f3cc6e69c1`
- Wave: `7ade2b7ad26843978ea4d63c89246cf0`
- Objective: Within current REPLAN RUN 85c36411deeb411c8ac8a0f3cc6e69c1, author and apply the smallest exact patch for the Full clean activation race. In RecoveryHost.superviseOnce, replacement watchdog final-census is eligible only when the current durable activation epoch state is STARTING or VERIFYING. STOPPING, HANDOFF, PREPARING, ADMISSION_CLOSED, and FROZEN must never enter finalCensus/recordPendingCensus/finalize from the watchdog. In FullCleanActivation.recordPendingCensus, validate current state before any update: allow STARTING (transition to VERIFYING) and VERIFYING (evidence refresh remaining VERIFYING); reject every other state fail-closed with a typed error and no durable mutation. Add deterministic tests: STOPPING watchdog calls no final census and leaves the epoch unchanged; pre-handoff/pre-start states reject recordPendingCensus without mutation; STARTING and VERIFYING remain valid; preserve duplicate contender and finalize semantics. Do not alter unrelated behavior. Preserve dirty worktree and .coding-tools. No adoption/force-release/commit/push/tag/release/deploy/restart/activation.
- Objective revision: `2`
- Objective SHA-256: `5883d67fce6807bf78ef6f084fd07c42edebd8ce32db1822d07176db1c288e61`
- Objective source: `replan_request`
- Mode: `bounded_candidate`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `7573c9037fbba39777f4190f8c36d72b39ae76215e3e88b786f80e097ad4a3a2`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| a8cc8fc9abcf4c9db43a374ab15d4794 | CODEX:luna | luna | luna | gpt-5.6-luna | high | blocked |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 34630 | 2026-09-01T16:03:35.315Z | wave_replanned |  | PREFLIGHT | reason=Previous deterministic wave only ran the old oracle and made no mutation. Strategy now changes to a bounded candidate that must author the exact four-file causal patch plus discriminating regressions; MCP remains authoritative writer and proof owner. The prior auto-idempotent post-rejection request was blocked before execution by operator-report ACK and its key is not replayed. |
| 34631 | 2026-09-01T16:03:35.538Z | observation_span_recorded |  |  |  |
| 34632 | 2026-09-01T16:03:37.077Z | managed_process_admitted |  |  | owner=default |
| 34633 | 2026-09-01T16:03:37.460Z | managed_process_started |  |  | owner=default |
| 34634 | 2026-09-01T16:03:42.035Z | managed_process_terminal |  |  | owner=default |
| 34635 | 2026-09-01T16:03:42.413Z | oracle_preflight | PREFLIGHT | PREFLIGHT |  |
| 34636 | 2026-09-01T16:03:42.599Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 34637 | 2026-09-01T16:03:42.800Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 34638 | 2026-09-01T16:03:43.013Z | route_selected | READY | READY | reason=explicit_request; requested=luna; resolved=luna |
| 34639 | 2026-09-01T16:03:43.199Z | state_transition | READY | ROUTED | reason=route_selected |
| 34640 | 2026-09-01T16:03:43.458Z | observation_span_recorded |  |  |  |
| 34641 | 2026-09-01T16:03:43.802Z | delegation_started | ROUTED | ROUTED | authority_owner=CODEX:luna |
| 34642 | 2026-09-01T16:03:44.033Z | model_dispatch_started | ROUTED | ROUTED |  |
| 34643 | 2026-09-01T16:03:51.789Z | model_dispatch_finished | ROUTED | ROUTED | status=completed |
| 34644 | 2026-09-01T16:03:52.140Z | delegation_finished | ROUTED | ROUTED | reason=candidate_reported_blocked; status=blocked |
| 34645 | 2026-09-01T16:03:52.325Z | failure_observed | ROUTED | ROUTED | failure_class=CANDIDATE_REPORTED_BLOCKED |
| 34646 | 2026-09-01T16:03:52.531Z | state_transition | ROUTED | REPLAN | reason=CANDIDATE_REPORTED_BLOCKED; failure_class=CANDIDATE_REPORTED_BLOCKED |
| 34647 | 2026-09-01T16:03:52.762Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

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
- Events checked: `132`
- Chain head: `1a2cafc28aa67b8ed4ddb35ed93dec2b08d9613e2c333c12109e21dacdfd1b55`
