# Orchestration Wave 1

- Run: `4046fb1438234a5f8ac6b67a2b4f6a3f`
- Wave: `042f74305d9b4c27bd6cf6e767a156d6`
- Objective: C4 corrective wave only: preserve an explicit --user-data-dir for isolated packaged Recovery Host launches instead of unconditionally resetting userData to the production APPDATA profile; add the smallest focused regression oracle. Preserve default version-1.0 production profile behavior when no explicit override is supplied. No unrelated edits, no publish/deploy, and do not touch .coding-tools evidence.
- Objective revision: `1`
- Objective SHA-256: `c1a6a3964880ccb294145e1cfcc5146323011961f6056131a9ef855da5962288`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `9b3241ddc963a77d916edc453ea7b7e8e4ae5391`
- Worktree fingerprint: `fdd8e149738afdf61018d6d549f8cfa27ec4acd6f0b714ea56d1e423ae2eeeb6`
- Contract fingerprint: `4aada5917b37cd5c5064b1b1917a78d3ac21fae6f1d94004fcc6dc3222202822`
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 41234 | 2026-09-06T04:18:11.993Z | run_started |  | PREFLIGHT |  |
| 41235 | 2026-09-06T04:18:12.483Z | observation_span_recorded |  |  |  |
| 41236 | 2026-09-06T04:18:18.332Z | observation_span_recorded |  |  |  |
| 41237 | 2026-09-06T04:18:18.512Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 41238 | 2026-09-06T04:19:20.159Z | state_transition | PREFLIGHT | ABORTED | reason=Abort accidental prepare-only orchestration created by task-context mismatch. No source mutation, no proof, no lease. User requires continuation only on existing RUN 3ddeec792a9e4ad589567f0e147c2630. |
| 41239 | 2026-09-06T04:19:20.604Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

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
- Events checked: `6`
- Chain head: `9e555cd7bd5ca353929430f26caa76d478e5640c2476f0dacd46d0230f6e5cdc`
