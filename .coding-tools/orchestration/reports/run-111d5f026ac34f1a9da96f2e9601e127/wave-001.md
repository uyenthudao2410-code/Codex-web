# Orchestration Wave 1

- Run: `111d5f026ac34f1a9da96f2e9601e127`
- Wave: `a8d37e45b4fc424f94b81babdde3f5f6`
- Objective: Close the final Phase 2.5 TTL gap found during final review: an already-running Electron UI can receive restart_required from registerUiRevision and call app.relaunch/app.exit without rechecking the activation expiry at that exact self-relaunch mutation boundary. Inspect the minimal current code needed to patch this path and add a discriminating regression. Preserve all unrelated work; no mutation in prepare.
- Mode: `mcp_only`
- Base HEAD: `597170860118a847b7e8a6f06903c37da8432d82`
- Worktree fingerprint: `6fbad61bc0b240f29072f2a22478492358d746d26717cb593a305b87714518c8`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 5774 | 2026-08-16T04:38:19.494Z | run_started |  | PREFLIGHT |  |
| 5775 | 2026-08-16T04:39:22.727Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 5776 | 2026-08-16T04:39:56.808Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 5777 | 2026-08-16T04:39:57.153Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 5778 | 2026-08-16T04:39:57.452Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 5779 | 2026-08-16T04:39:57.971Z | state_transition | READY | ROUTED | reason=route_selected |
| 5780 | 2026-08-16T04:39:59.434Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=df042fe602184fc5bc76c8c7246e395c |
| 5781 | 2026-08-16T04:39:59.680Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 5782 | 2026-08-16T04:40:01.131Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=df042fe602184fc5bc76c8c7246e395c |
| 5783 | 2026-08-16T04:40:01.452Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 5784 | 2026-08-16T04:40:01.998Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=5b589ce8c821a6fc6f1e2f1ab2225d562327750e097e8fe38af9b3f8168a495a |
| 5785 | 2026-08-16T04:40:02.706Z | managed_process_admitted |  |  | owner=default |
| 5786 | 2026-08-16T04:40:03.313Z | managed_process_started |  |  | owner=default |
| 5787 | 2026-08-16T04:40:04.838Z | managed_process_terminal |  |  | owner=default |
| 5788 | 2026-08-16T04:40:05.394Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=5b589ce8c821a6fc6f1e2f1ab2225d562327750e097e8fe38af9b3f8168a495a |
| 5789 | 2026-08-16T04:40:06.355Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 5790 | 2026-08-16T04:40:20.162Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 5791 | 2026-08-16T04:40:20.801Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | 5b589ce8c821a6fc6f1e2f1ab2225d562327750e097e8fe38af9b3f8168a495a | False | 2813 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| bbfbdd15cf85473ba106421fc4433b50 | accepted | 597170860118a847b7e8a6f06903c37da8432d82 | 8af68a8b2bdaf29b052a58c622b5a3fc3c1c206fe68552622afbe44944c934fc | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `18`
- Chain head: `be21ff0f53c86597b1b6567b4f8f77d7824a03b59fd0791fbcc7820548e9b055`
