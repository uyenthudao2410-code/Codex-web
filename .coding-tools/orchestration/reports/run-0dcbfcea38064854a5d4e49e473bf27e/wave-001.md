# Orchestration Wave 1

- Run: `0dcbfcea38064854a5d4e49e473bf27e`
- Wave: `007d7899d451462bba1ad9a68feba80e`
- Objective: Resume final Codex-web completion from the exact observed full-suite result: 3 failed, 869 passed, 4 skipped, 131 subtests passed. Read only the exact three failing tests and the current implementation they exercise. Determine the smallest source-grounded test-only corrections for: (1) the stale smart-v3 tool-contract SHA oracle, where durable accepted evidence identifies current SHA 0a1a837eee066d5098074c7ff2174c472d08a4b1c869a0fce2c21cdb1d685482 and predecessor 6bc9eaf623ada4b15c77f2926eb17a49dbcdb1606c407afddc97b9115ba397c1; (2) the ExceptionGroup boundary fixture, which now reaches _touch_hub_client and needs the minimal established handler.server fixture state without changing production behavior; (3) the previous-generation command restart reconciliation oracle, where command_control poll now returns ok=true and the test must assert the current typed reconciled terminal semantics rather than the obsolete ok=false behavior. Do not mutate any file in this prepare step. Preserve the entire dirty worktree; never reset, clean, checkout, restore, rebase, or overwrite unrelated paths. Return exact relevant snippets/semantics, exact target test paths, and current SHA-256 for those test files so a later exact-byte test-only patch can be safely applied.
- Objective revision: `1`
- Objective SHA-256: `1c6d289bd273357fde09c102205041197cc102dcab21deb90980e1df7ffde291`
- Objective source: `run_initial_objective`
- Mode: `mcp_only`
- Base HEAD: `80aceb583202ad381c25687969fb48adbf74622c`
- Worktree fingerprint: `c7361b64f03bc67290e88e262da6c201a6a4bc123d3b5d6f376a29bd67fffdb9`
- Contract fingerprint: ``
- Status: **active**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 39454 | 2026-09-04T06:07:58.843Z | run_started |  | PREFLIGHT |  |
| 39455 | 2026-09-04T06:07:59.286Z | observation_span_recorded |  |  |  |
| 39456 | 2026-09-04T06:08:30.981Z | observation_span_recorded |  |  |  |
| 39457 | 2026-09-04T06:08:31.636Z | context_prepared | PREFLIGHT | PREFLIGHT |  |

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
- Chain head: `d8654a5ff627924f4947cadb0a514bbdb3cf6295ac1f0742f07437dddeca1697`
