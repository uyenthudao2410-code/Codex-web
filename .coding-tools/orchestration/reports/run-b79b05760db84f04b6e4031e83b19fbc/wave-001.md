# Orchestration Wave 1

- Run: `b79b05760db84f04b6e4031e83b19fbc`
- Wave: `a0ea656f23eb4d74bbbfe092c5a73cc6`
- Objective: Correct Codex-web observability so it distinguishes MCP tools/list discovery from the per-invocation token counts shown on Coding-VP Live Tool call cards. The canonical per-tool-call metric must consume an exact invocation/tool-call token receipt from the ChatWeb/Coding-VP client/transport when such metadata is actually exposed; provider/controller model-usage receipts stay separate. Never derive per-tool-call tokens from tools/list, serialized byte size, elapsed time, or aggregate analytics, and never convert missing measurement to zero. Preserve the exact 8-tool smart-v3 contract and bounded non-mutating fast Overview path. Add focused regression coverage and provenance. User screenshot shows card-level counts such as agent_workflow 64,143 tokens and exec_command 895 tokens; determine whether current request metadata, host observation, performance events, or durable tool-call events already carry that exact card count; if not, identify the smallest authoritative ingress needed rather than fabricate it.
- Objective revision: `1`
- Objective SHA-256: `39863134d4068fddad7937f6d075110127a3d19b821cd8b64114ee74dc621c3a`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `9b766f241432b9b5bfa8aa75ae2f1816709a2c2d`
- Worktree fingerprint: `da4bde021da882b709da1ff1fe4ac79d23913268830125ef8e0c0cb193caa9a0`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 32741 | 2026-08-30T15:22:06.618Z | run_started |  | PREFLIGHT |  |
| 32742 | 2026-08-30T15:22:07.009Z | observation_span_recorded |  |  |  |
| 32743 | 2026-08-30T15:22:07.218Z | solution_shadow_recommended |  |  |  |
| 32744 | 2026-08-30T15:22:09.147Z | observation_span_recorded |  |  |  |
| 32745 | 2026-08-30T15:22:10.058Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 33398 | 2026-08-31T13:58:01.708Z | state_transition | PREFLIGHT | ABORTED | reason=operator_authorized_superseded_inactive_run_p0_6 |
| 33399 | 2026-08-31T13:58:02.217Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

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
- Events checked: `7`
- Chain head: `ad00ecce5c505436cd009c3c25355fa683e833a110b4a184bfb7ec2d365acf4e`
