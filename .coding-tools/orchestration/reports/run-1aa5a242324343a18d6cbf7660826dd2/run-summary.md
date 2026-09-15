# Orchestration Run Summary

- Run: `1aa5a242324343a18d6cbf7660826dd2`
- Task: `31a8aaa6518b4862bbb3bec9f8fac527`
- Objective: Pre-package provenance wave for current C01/runtime reconnection source under Parent Problem prl-22e670302757c9b7663170e226ed7c26 revision 1. Exact-byte adopt, without modifying, the current dirty causal runtime route and identity-observation files plus their focused tests: electron/services/recoveryHost.js SHA256 a291bfb2082341a98b013bf6e69e839a191026be0a1844c851234e6c7eaace43; electron/services/recoveryIpc.js SHA256 d87bc31981ece871a1a3188fd9f04af991cb1d911d39850999e108df445bee16; scripts/dev-ui-lifecycle.js SHA256 6843b4628c8db344c0a7e1946d0d390e2ae26e2efd73f2f30de65403d967cd50; tests/dev-ui-lifecycle.test.js SHA256 5f7ca63155cfc5bfa9cf6a9a00a3f29bc35967cb894052180156e9bbfb39d738; tests/recovery-host.test.js SHA256 0abef2e6c6c744bf4c49fc2df5b714cdd8f1d61f998327670b69509c1c9f756a. Prove the packaged-host guarded cold-start routing and read-only exact MCP identity observation boundary. Run only tests/dev-ui-lifecycle.test.js and tests/recovery-host.test.js. Do not alter bytes unless a focused oracle proves a defect. Do not touch unrelated dirty backend/control-plane/docs paths. No package/install/reboot/runtime restart/commit/push/publish/release/deploy in this wave.
- Status: **accepted**
- Started: `2026-09-15T03:57:50.329Z`
- Finished: `2026-09-15T04:01:55.025Z`

## Outcome metrics

- Waves: **2**
- Route decisions: **2**
- Failures observed: **1**
- REPLAN transitions: **1**
- Proof stages: **2**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `d1dc9be1af39482f9e31fdc2f9734ac4` | 1 | `run_initial_objective` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | replanned |
| 2 | `fa935237c50a48eb8e18b9890ae605dd` | 1 | `replan_request` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| ca53e98742bf48e09494b929835a3c2b | fa935237c50a48eb8e18b9890ae605dd | accepted | a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6 | 7b7f8e92e6014dc70863d4cca46e02e44e96dab3fe42e6fdb3520c17da1bdea9 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 55833 | `deterministic` | `deterministic` | explicit_request |
| 55854 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 55836 | `BASE_DRIFT` | `ROUTED` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `52`
- Chain head: `c34f300e94e284cea989cf597ab919ec88b1aa5bf1c0dd740c9d6a737b3cbb5b`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
