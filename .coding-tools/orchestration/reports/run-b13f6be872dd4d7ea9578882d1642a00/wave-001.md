# Orchestration Wave 1

- Run: `b13f6be872dd4d7ea9578882d1642a00`
- Wave: `5af6621f6f3c4fc286478b6b4414602b`
- Objective: Live L3 controller-usage observability canary after accepted runtime activation. Read-only only: establish an exact ChatWeb RUN/WAVE binding for the current real user turn, inspect the current controller-usage observation/ingress surfaces needed for later proof, and do not modify source, evidence, ledger files manually, restart runtime, commit, push, release, or deploy.
- Objective revision: `1`
- Objective SHA-256: `11754b0d2c1e038eef519210d03177d9d61d0bf7520032c3a170156f7a605979`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`
- Worktree fingerprint: `ab3d1d86c101619e6433761052e15758ea73f9036b22f77ff9d2b1cea7388bd1`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 37302 | 2026-09-03T10:40:12.124Z | run_started |  | PREFLIGHT |  |
| 37303 | 2026-09-03T10:40:12.460Z | observation_span_recorded |  |  |  |
| 37304 | 2026-09-03T10:40:14.834Z | observation_span_recorded |  |  |  |
| 37305 | 2026-09-03T10:40:15.648Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 37306 | 2026-09-03T10:41:26.825Z | managed_process_admitted |  |  | owner=chatweb-l3-canary-read |
| 37307 | 2026-09-03T10:41:27.430Z | managed_process_started |  |  | owner=chatweb-l3-canary-read |
| 37308 | 2026-09-03T10:41:28.579Z | managed_process_terminal |  |  | owner=chatweb-l3-canary-read |
| 37309 | 2026-09-03T10:42:04.139Z | managed_process_admitted |  |  | owner=chatweb-l3-correlation-diagnose |
| 37310 | 2026-09-03T10:42:04.521Z | managed_process_started |  |  | owner=chatweb-l3-correlation-diagnose |
| 37311 | 2026-09-03T10:42:05.115Z | managed_process_terminal |  |  | owner=chatweb-l3-correlation-diagnose |
| 37312 | 2026-09-03T10:42:19.924Z | managed_process_admitted |  |  | owner=chatweb-l3-correlation-callsite |
| 37313 | 2026-09-03T10:42:20.249Z | managed_process_started |  |  | owner=chatweb-l3-correlation-callsite |
| 37314 | 2026-09-03T10:42:20.782Z | managed_process_terminal |  |  | owner=chatweb-l3-correlation-callsite |
| 37315 | 2026-09-03T10:42:35.973Z | managed_process_admitted |  |  | owner=chatweb-l3-correlation-callsite2 |
| 37316 | 2026-09-03T10:42:36.298Z | managed_process_started |  |  | owner=chatweb-l3-correlation-callsite2 |
| 37317 | 2026-09-03T10:42:37.082Z | managed_process_terminal |  |  | owner=chatweb-l3-correlation-callsite2 |
| 37318 | 2026-09-03T10:43:14.711Z | state_transition | PREFLIGHT | ABORTED | reason=Read-only L3 live canary is non-qualifying because the staged ChatWeb host turn was 274 seconds old when claim began, beyond HOST_CORRELATION_PENDING_TTL_MS=120000. No source mutation or proof was performed; terminalize diagnostic run before a fresh-turn canary. |
| 37319 | 2026-09-03T10:43:15.244Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

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
- Events checked: `18`
- Chain head: `0508f9167f376fe55c262c294430df665467f2d35a1625580a8b83706965d5a2`
