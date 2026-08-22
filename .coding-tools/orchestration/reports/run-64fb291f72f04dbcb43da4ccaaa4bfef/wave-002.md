# Orchestration Wave 2

- Run: `64fb291f72f04dbcb43da4ccaaa4bfef`
- Wave: `7af1bbcc4371451f8e0ed97c9636e352`
- Objective: Fix EOCL task/run projection isolation only. A task that already has its own task_id must never adopt a workspace-global active orchestration run that belongs to a different task_id. Preserve legacy workspace-global recovery only for genuinely task-id-less unscoped state. Prove the historical failure mode with task B having no projection while an unrelated active run belongs to task A. Preserve all unrelated dirty work and the accepted completion-report ACK repair. Explicitly exclude mcp_http_handler.py and test_truth_snapshot.py. No restart, commit, push, package, release, deploy, T3 or C1.
- Objective revision: `2`
- Objective SHA-256: `ec5852e9a0c9c3b9f64e85186d20870bcf3d2afd27d3b64ef4042f3a40d6900a`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `9eb05072e54ffca9576e23c2d4a4f4e14034bddc`
- Worktree fingerprint: `412a49bc72bffbfe757a1c0ce2731cef1d02328927be112b1eaa578067a450b8`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 26370 | 2026-08-21T20:39:25.728Z | wave_replanned |  | PREFLIGHT | reason=Wave 1 source patch applied, but the focused unittest command was launched from repository root, so Python failed before test execution with ModuleNotFoundError: No module named 'tests.test_task_state_and_build'. Replan changes the proof environment to resources/coding-tools-mcp and adds only an invariant comment plus a pre-reconcile assertion so both intended files are explicitly touched/receipted by this replacement wave; production behavior and objective remain unchanged. |
| 26371 | 2026-08-21T20:39:25.891Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 26372 | 2026-08-21T20:39:26.076Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 26373 | 2026-08-21T20:39:26.252Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 26374 | 2026-08-21T20:39:26.537Z | state_transition | READY | ROUTED | reason=route_selected |
| 26375 | 2026-08-21T20:39:26.965Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=0c5052fe29da40a98a23189564d85f4d |
| 26376 | 2026-08-21T20:39:27.129Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 26377 | 2026-08-21T20:39:27.519Z | patch_surface_observed |  |  |  |
| 26378 | 2026-08-21T20:39:27.723Z | patch_surface_observed |  |  |  |
| 26379 | 2026-08-21T20:39:28.026Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=0c5052fe29da40a98a23189564d85f4d |
| 26380 | 2026-08-21T20:39:28.190Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 26381 | 2026-08-21T20:39:28.557Z | proof_cache_miss |  |  | reason=cold; stage_id=check:781a4fe621629a53; input_fingerprint=d2216d248136b825f453825572d6a27c0e05dc340499a71bc7fe9f20d3031a0c |
| 26382 | 2026-08-21T20:39:28.953Z | managed_process_admitted |  |  | owner=default |
| 26383 | 2026-08-21T20:39:29.304Z | managed_process_started |  |  | owner=default |
| 26384 | 2026-08-21T20:39:29.836Z | managed_process_terminal |  |  | owner=default |
| 26385 | 2026-08-21T20:39:30.232Z | proof_recorded |  |  | stage_id=check:781a4fe621629a53; status=failed; cache_hit=False; input_fingerprint=d2216d248136b825f453825572d6a27c0e05dc340499a71bc7fe9f20d3031a0c |
| 26386 | 2026-08-21T20:39:30.454Z | failure_observed | PROVING | PROVING | failure_class=CHECK_FAILED |
| 26387 | 2026-08-21T20:39:30.770Z | state_transition | PROVING | REPLAN | reason=CHECK_FAILED; failure_class=CHECK_FAILED |
| 26388 | 2026-08-21T20:39:30.996Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| check:781a4fe621629a53 | failed | d2216d248136b825f453825572d6a27c0e05dc340499a71bc7fe9f20d3031a0c | False | 1261 | 1 |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| - | - | - | - | - |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `67`
- Chain head: `ac7f647355424060b530b16aa6183158621a38c9729fc9936df8eecebe0592c9`
