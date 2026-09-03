# Orchestration Wave 1

- Run: `a9a729561eb048ca94aa6f5e44da585f`
- Wave: `5a837dd8c1c14fb3bad7fef758cab96c`
- Objective: Fix the post-activation exact-RUN continuity defect that blocks canonical W4. Live reproduction: task_control audit with only run_id=393c55bf91c743988d65cb42ffffda9b resolves the correct durable RUN/WAVE and returns task_context_id ctx_18c5f68da722f4789844de4ff18c5c7c, but the TaskState projection in that context remains bound to the already-aborted duplicate RUN 825b0d02075a4d5294e441bfceead65b. task_control resume changes only that stale task status, agent_workflow phase=resume still returns TASK_STOPPED, and a fresh exact task_control get(run_id=393c...) fails EXACT_RUN_RECOVERY_REFUSED. The archived history contains canonical task_id 6bf9cd89463f4f3a8024502ae7f5b37f with RUN 393c... and current WAVE a4f5bf9b89074d55b6cb399fb0a23ee3. Localize the smallest fail-closed repair so successful exact-RUN stateless recovery rehydrates/persists the canonical TaskState projection (or otherwise makes the returned task_context immediately usable by agent_workflow) only when the conflicting projection is safely terminal and the run/task/controller/workspace binding is exact. Preserve refusal on active conflicts, foreign controller/workspace, ambiguous archive matches, pending operator reports, or mismatched task_id. Add focused regression covering audit recovery followed immediately by resume/agent workflow eligibility or the equivalent TaskState contract. No W4 instrumentation changes, no commit/push/restart/release/deploy.
- Objective revision: `1`
- Objective SHA-256: `159c600cf287c56a91d42c9b38732e1611fd85170d7c0ba5d9facfcca7fb7dd2`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `db9f1f472815d07791ce1199f13a9b805aa4fd71ed82c5e6ebbe036ac0ba7e57`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 34281 | 2026-09-01T07:22:43.803Z | run_started |  | PREFLIGHT |  |
| 34282 | 2026-09-01T07:22:44.223Z | observation_span_recorded |  |  |  |
| 34283 | 2026-09-01T07:22:45.890Z | observation_span_recorded |  |  |  |
| 34284 | 2026-09-01T07:22:46.040Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 34285 | 2026-09-01T07:25:32.056Z | managed_process_admitted |  |  | owner=default |
| 34286 | 2026-09-01T07:25:32.394Z | managed_process_started |  |  | owner=default |
| 34287 | 2026-09-01T07:25:32.860Z | managed_process_terminal |  |  | owner=default |
| 34288 | 2026-09-01T07:25:51.506Z | managed_process_admitted |  |  | owner=default |
| 34289 | 2026-09-01T07:25:51.697Z | managed_process_started |  |  | owner=default |
| 34290 | 2026-09-01T07:25:52.103Z | managed_process_terminal |  |  | owner=default |
| 34291 | 2026-09-01T07:27:02.720Z | managed_process_admitted |  |  | owner=default |
| 34292 | 2026-09-01T07:27:03.008Z | managed_process_started |  |  | owner=default |
| 34293 | 2026-09-01T07:27:03.445Z | managed_process_terminal |  |  | owner=default |

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
- Events checked: `13`
- Chain head: `c058376bb7d9d8f0252ba02f811fa54c6bfbe7d1d199d037717829f6ecb08ba4`
