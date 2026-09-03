# Orchestration Run Summary

- Run: `4b1f597e74d54742b04f726cab5e665e`
- Task: `dbc7a1d5a47a4d888aba62819ca48e5b`
- Objective: Fresh EOCL RUN/WAVE only; do not reuse or mutate any prior accepted-code activation intent. Residual bugfix: close the fail-closed persistence gap in RecoveryActionStore durable_epoch_binding. PRE-MUTATION HARD GATE: the two owned dirty files must exactly match accepted checkpoint c213617ecc4941ac907433e69bc64e6c receipts before any write: electron/services/recoveryActionStore.js sha256=0e857c5e7d3932bcbc08832e5d9fff4737db0d01c489dac3f06e208d0e661872 and tests/recovery-activation.test.js sha256=062e6653574e8be1966f26215f121843fdfcf64d57a870918c309cc7ade658c4. Use exact-byte adoption as the preimage gate and stop on mismatch. Own and mutate ONLY those two paths; acquire a write lease scoped to exactly those two paths; do not touch recoveryActivation.js or any other concurrent WIP.

Required semantics: (1) preserve the existing compatible three-field durable_epoch_binding shape across Recovery Host handoff; do not add required persisted fields. (2) At load/use time, durableEpochBinding must require safe created_at_unix_ms from the action record and reject a durable expiry beyond a deterministic persisted lifetime cap derived from action creation + MAX_DURABLE_EPOCH_TTL_MS + at most the authenticated request admission window of 60 seconds. Introduce an explicitly named constant for that admission allowance; cap must stay bounded and fail-closed. (3) bindDurableEpoch must enforce the same persisted cap in addition to its existing now-relative 10-minute check; preserve immutable request expires_at_unix_ms and exact operation/epoch validation. (4) Malformed, identity-mismatched, or over-bound stored binding is non-authoritative: replay/get/active fall back to request expiry and, once that expires, terminalize ACTIVATION_REQUEST_EXPIRED; never trust the tampered durable deadline. (5) Add focused regressions proving a valid existing three-field binding remains active after request expiry but before epoch expiry, and a tampered over-bound stored three-field binding is rejected as authority and expires on the original request deadline. Implement the smallest coherent patch.

Proof must run in this exact order after mutation: node --test tests/recovery-activation.test.js; then node --test tests/accepted-code-activation.test.js; then scoped git diff --check for the two owned paths. Produce exact-byte receipts/fingerprints, reach ACCEPTING, release/quiesce write resources, and STOP for ChatWeb Sol/user explicit acceptance. Do NOT self-accept or reject. No direct ledger/projection/runtime-state edits, force release, restart, commit, push, tag, package, publish, release, or deploy.
- Status: **accepted**
- Started: `2026-09-02T10:20:50.054Z`
- Finished: `2026-09-03T02:07:54.086Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **6**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `eb7ba8e957cf49f68a6ca12dcf0d8cd8` | 1 | `run_initial_objective` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 2 | `d888327e231144408a5f3b949327234c` | 2 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | replanned |
| 3 | `e614b70c0d0e4e68a07b10c6b3c1dfcf` | 3 | `replan_request` | `mcp_only` | `30b7d1b971b65034d3e4c95568c970fcc0e9380c` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 6bc0ff33dd8440aa80631f53e4662341 | e614b70c0d0e4e68a07b10c6b3c1dfcf | accepted | 30b7d1b971b65034d3e4c95568c970fcc0e9380c | 7cd505c302ef467fecf1d076de8ca4d67a22d49c27fff06de69aaca67669b187 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 35812 | `deterministic` | `deterministic` | explicit_request |
| 35864 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 35874 | `deterministic` | `deterministic` | caller_supplied_change_set |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 35839 | `SOL_REJECTED` | `ACCEPTING` | REPLAN_REQUIRED_ZERO_DIFF_RESIDUAL_GAP_UNIMPLEMENTED: exact c213 preimages were adopted and all requested baseline proofs passed, but this wave produced affected_files=[] / modified_files=0, so it did not implement the required persisted durable-epoch cap. Preserve the fresh RUN and open a corrective wave with an explicit exact two-path patch; do not reuse proof from this zero-diff fingerprint as implementation proof. |
| 35867 | `RUNTIME_RESUME_REQUIRED` | `ROUTED` | A non-terminal wave was recovered outside its original synchronous execution. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `106`
- Chain head: `379005b6f4927cf124fc210388ababb4c878ae24f951c8efdee77d8497e744c7`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
