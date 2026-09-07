# Orchestration Wave 1

- Run: `eb18c2678720433daa1e5c9f84a42835`
- Wave: `5ec74b303bec4accae8c25f8a5fad043`
- Objective: Resolve the remaining ambiguity in the first-install READY-commit bug. Inspect only electron/services/recoveryHostLauncher.js, electron/recoveryHost.js, electron/services/runtimeOrchestrator.js, and electron/services/nativeService.js. Trace ensureRecoveryHost() on a packaged fresh install with no descriptor/no prior epoch: what process is spawned, whether a recovery bootstrap envelope or activation epoch is created, what activationGate/epoch values are passed to NativeService.start, and whether RuntimeOrchestrator.start({automatic:true}) can launch MCP with CODING_TOOLS_MCP_ACTIVATION_GATE=CLOSED without a FullCleanActivation transaction capable of producing ready_commit_digest. Return the exact fresh-install state sequence and one causal fix point; do not mutate.
- Objective revision: `1`
- Objective SHA-256: `f85a94312e22db5f2effbefd2af63d9887902ad8789c219233d7cb439df23dad`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `9e752e34db745cd4fb2d0830a517910eced9c37f`
- Worktree fingerprint: `6546f235f77e31e7b47a1f6c568d1f6291fec2c3fce76edc6b85030cc9b5259e`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 41567 | 2026-09-06T05:51:44.238Z | run_started |  | PREFLIGHT |  |
| 41568 | 2026-09-06T05:51:44.863Z | observation_span_recorded |  |  |  |
| 41569 | 2026-09-06T05:51:48.424Z | observation_span_recorded |  |  |  |
| 41570 | 2026-09-06T05:51:48.599Z | context_prepared | PREFLIGHT | PREFLIGHT |  |

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
- Events checked: `4`
- Chain head: `0c17737844ece7d033104d11446b4fb319cf5cb8d15cf875942916aa2d5756a4`
