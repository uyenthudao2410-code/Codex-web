# Orchestration Wave 2

- Run: `f8fecacd91d14d84925d87d688bf7199`
- Wave: `3b440b68b41a42db811477a98a1ec35a`
- Objective: Complete the truthful token-metering correction in the same RUN. Preserve the already-applied Control Center slice. Separate three evidence planes: MCP tools/list is exact 8-tool contract discovery; controller/provider UsageEvents are model usage/cost receipts; ChatWeb/Coding-VP Tool-call-card tokens are per-invocation host metrics. Current MCP transport has no exact post-call host receipt for the card total, so expose card metering as unknown/— and never derive it from bytes/time/analytics. Make the visible Dashboard token/cost path canonical UsageEvent-only, remove the byte/token UI control, fail closed secondary model/fleet token economics without canonical lane mapping, and update focused tests. Preserve unrelated dirty work.
- Objective revision: `2`
- Objective SHA-256: `4959a7bf5da870dbef552e31098b281d23991557013e5bed40dbefb4226ec3d5`
- Objective source: `replan_request`
- Mode: `mcp_only`
- Base HEAD: `9b766f241432b9b5bfa8aa75ae2f1816709a2c2d`
- Worktree fingerprint: `3cecd01950ca189c768d8f641a0d24edc857ba9e12e2e2ae9851f82cfa4940eb`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 32767 | 2026-08-30T15:44:04.623Z | wave_replanned |  | PREFLIGHT | reason=The previous wave was intentionally rejected because it contained only the Control Center display slice and zero proof. The first wave-2 attempt performed zero writes due to one ambiguous test hunk. Changed evidence/strategy now anchors every test replacement by its unique test name while preserving the same causal solution; this creates a new wave in the same RUN and completes backend + Dashboard + focused proof. |
| 32768 | 2026-08-30T15:44:04.897Z | observation_span_recorded |  |  |  |
| 33400 | 2026-08-31T13:58:12.557Z | state_transition | PREFLIGHT | ABORTED | reason=operator_authorized_superseded_inactive_run_p0_6 |
| 33401 | 2026-08-31T13:58:13.140Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

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
- Events checked: `25`
- Chain head: `20d5ee27aba2e18813565098be2b8f37d0ee32d0f4894d20aa5683a6f4691b12`
