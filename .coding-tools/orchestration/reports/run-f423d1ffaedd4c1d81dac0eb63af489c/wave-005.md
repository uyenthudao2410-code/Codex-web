# Orchestration Wave 5

- Run: `f423d1ffaedd4c1d81dac0eb63af489c`
- Wave: `0746c50d1fb9449f80513758c9b25deb`
- Objective: Repair the WAVE4 regression cluster on the existing canonical RUN only. Modify only resources/coding-tools-mcp/coding_tools_mcp/coordination.py with the supplied exact causal patch so requested-run projection replacement is used only for task_control action=get, while all other actions still perform ordinary current-projection reconciliation. Preserve all unrelated WIP, docs, .coding-tools evidence, the two PRL receipts, and the five prior checkpoint-backed recovery files. Do not restart, commit, push, tag, publish, release, deploy, force-release, edit SQLite/state directly, create synthetic workload, create a new RUN, or mutate job 71f8e9646b644839bbd4f95be7dba7d5. If the focused oracle fails, fail closed into REPLAN and do not continue to the full suite.
- Objective revision: `5`
- Objective SHA-256: `86016fd6ac7d2f1b0fd5fde3a055a4dde64ff01b48fc754b40c83d610de656f1`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `937a1686036cdf3ad4ee41158c5e7b6af14c844742b2fe8e0c76a7848b820297`
- Contract fingerprint: ``
- Status: **replanned**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 34221 | 2026-09-01T03:28:29.934Z | wave_replanned |  | PREFLIGHT | reason=REGRESSION_CLUSTER after WAVE4 CHECK_FAILED: exact-run projection replacement was applied to all task_control actions; restrict requested-run replacement to action=get while retaining ordinary current-projection reconciliation for every action. Six observed failures provide the strong oracle. |
| 34222 | 2026-09-01T03:28:30.161Z | observation_span_recorded |  |  |  |
| 34223 | 2026-09-01T03:28:30.381Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 34224 | 2026-09-01T03:28:30.540Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 34225 | 2026-09-01T03:28:30.684Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 34226 | 2026-09-01T03:28:30.882Z | state_transition | READY | ROUTED | reason=route_selected |
| 34227 | 2026-09-01T03:28:31.095Z | observation_span_recorded |  |  |  |
| 34228 | 2026-09-01T03:28:31.912Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=120c16261a5c4a1b8cde80c90760ed71 |
| 34229 | 2026-09-01T03:28:32.124Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 34230 | 2026-09-01T03:28:32.930Z | patch_surface_observed |  |  |  |
| 34231 | 2026-09-01T03:28:33.145Z | observation_span_recorded |  |  |  |
| 34232 | 2026-09-01T03:28:33.395Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=120c16261a5c4a1b8cde80c90760ed71 |
| 34233 | 2026-09-01T03:28:33.601Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 34234 | 2026-09-01T03:28:34.385Z | proof_cache_miss |  |  | reason=cold; stage_id=check:2f4fa9770f383502; input_fingerprint=1a7fc0c0634fb95e959bb047cccdb619762f2914ca9efd8a04940e728c068cfa |
| 34235 | 2026-09-01T03:28:34.581Z | observation_span_recorded |  |  |  |
| 34236 | 2026-09-01T03:28:34.782Z | failure_observed | PROVING | PROVING | failure_class=INVALID_ARGUMENT |
| 34237 | 2026-09-01T03:28:34.953Z | state_transition | PROVING | REPLAN | reason=INVALID_ARGUMENT; failure_class=INVALID_ARGUMENT |
| 34238 | 2026-09-01T03:28:35.186Z | wave_processes_quiesced |  |  | reason=orchestration_state:replan |

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
- Events checked: `204`
- Chain head: `855850803062800611e9d45e3c4ddd2517e83caefea8b866fb59ecf9ff4bddbf`
