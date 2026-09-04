# Orchestration Wave 1

- Run: `ba277a72100c4d75aa8c5c58445dedf3`
- Wave: `fc2acdc9fcb440dfa4e02b0061502e45`
- Objective: Prove the remaining L3 controller-usage transport gap on the current post-activation runtime without modifying source. Determine, from current repository contracts/tests and durable evidence only, whether exact ChatWeb controller usage can be produced or forwarded by any supported Codex-web surface after an attested ChatWeb tools/call, whether missing controllerUsage metadata is explicitly classified, whether a received-but-invalid controllerUsage envelope leaves a durable rejection signal, and whether there is any legitimate repo-side corrective change left. Do not fabricate token values and do not broaden into correlation code already proven live.
- Objective revision: `1`
- Objective SHA-256: `74dcf3a21ae6f8667263f94b99a25d3b134aeab6a5968bf39a90cad245c8653e`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `80aceb583202ad381c25687969fb48adbf74622c`
- Worktree fingerprint: `6b5fb2badfbcfa32b95881356c90eb51b89d687739b0b7df90dd27ec25209209`
- Contract fingerprint: ``
- Status: **aborted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 38247 | 2026-09-03T17:03:55.052Z | run_started |  | PREFLIGHT |  |
| 38248 | 2026-09-03T17:03:55.480Z | observation_span_recorded |  |  |  |
| 38249 | 2026-09-03T17:03:57.026Z | observation_span_recorded |  |  |  |
| 38250 | 2026-09-03T17:03:58.148Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 38251 | 2026-09-03T17:05:36.222Z | state_transition | PREFLIGHT | ABORTED | reason=Read-only L3 transport-gap diagnosis is complete. Source evidence proves controllerUsage envelope presence is recorded before validation, correlation/ingress paths are implemented and tested, and no server-side causal defect is proven. Terminalize this diagnostic PREPARE run without source mutation before any further action. |
| 38252 | 2026-09-03T17:05:36.951Z | wave_processes_quiesced |  |  | reason=orchestration_state:aborted |

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
- Chain head: `d6f995ee70d1eb9262c805b752db705e86fa47993383e23503d5107cfdbfc35e`
