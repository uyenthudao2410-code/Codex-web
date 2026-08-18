# Orchestration Run Summary

- Run: `0e7268b8bc324ebd972ac00819df82fa`
- Task: `8667aedb81614965b4896ad09fd0e65f`
- Objective: Audit whether the local checkout actually contains and proves the claimed PR #17 recovery/runtime identity fixes. Verify: main/HEAD and ancestry for f6018a5420c28b5da3e6effc456ee07da25a14ed, a1c664c2, 75169953; dev installation_id derived from canonical running checkout root without persisting raw path; dev A->B takeover with authenticated exact owner_pid+instance_id and descriptor TOCTOU rejection RECOVERY_DESCRIPTOR_CHANGED; legacy missing installation_id stale/bootstrap behavior; packaged fail-closed across installation identities; development startWithWindows forced false and stale dev supervisor suppression via stop.request; runtimeIdentity.js included in Recovery Host fingerprint; workspace settings passed as --workspace and not reused to infer checkout source; authorizedRoots/canonical alias behavior; .coding-tools untouched by the claimed merge. Locate the exact regression tests and authoritative commands. Do not modify files.
- Status: **accepted**
- Started: `2026-08-18T08:30:43.537Z`
- Finished: `2026-08-18T08:47:04.578Z`

## Outcome metrics

- Waves: **5**
- Route decisions: **4**
- Failures observed: **4**
- REPLAN transitions: **4**
- Proof stages: **17**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Mode | Base | Status |
|---:|---|---|---|---|
| 1 | `91c5488530aa4f4d92ce5f0343ea7442` | `mcp_only` | `f6018a5420c28b5da3e6effc456ee07da25a14ed` | replanned |
| 2 | `1e0c5a66924c4e5bac4d33eb3508d36a` | `auto` | `` | replanned |
| 3 | `77a6002387e743c692c57d8dd4488a7d` | `mcp_only` | `f6018a5420c28b5da3e6effc456ee07da25a14ed` | replanned |
| 4 | `6c0de28ef7c1443e81865607266cd767` | `mcp_only` | `f6018a5420c28b5da3e6effc456ee07da25a14ed` | replanned |
| 5 | `790a9591a02449e59549dc77ae110ff0` | `mcp_only` | `f6018a5420c28b5da3e6effc456ee07da25a14ed` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| fe1b38d65eb8470da3e471356459e388 | 790a9591a02449e59549dc77ae110ff0 | accepted | f6018a5420c28b5da3e6effc456ee07da25a14ed | 20ff1f0c68a7a2b2737ae415dca3c6619b9011b68eba5029e7c55f7f1d6d8330 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 16454 | `deterministic` | `deterministic` | explicit_request |
| 16589 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 16612 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 16651 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 16577 | `SOL_REJECTED` | `ACCEPTING` | Reject full acceptance: focused checkout/recovery authority regressions pass 16/16 and live Recovery Host/Coding MCP are on E:\DEV\Codex-web with the new installation identity/workspace contract, but project-native `npm test` fails 3/227. Two failures are directly attributable to f6018a54 adding runtimeIdentity.js to RECOVERY_HOST_LEGACY_V1_ADDED_FILE_DIGESTS without updating legacy bridge fixtures in tests/component-revision.test.js and tests/recovery-host.test.js; both now throw REVISION_BRIDGE_FILE_MISSING. A third source-bundle failure is environmental/pre-existing nested resources/coding-tools-mcp/.coding-tools state. Therefore the authority implementation is substantially fixed, but the merged source is not fully acceptance-green. |
| 16582 | `BASE_DRIFT` | `PREFLIGHT` |  |
| 16605 | `CHECK_FAILED` | `PROVING` |  |
| 16640 | `SOL_REJECTED` | `ACCEPTING` | Source/test behavior is green, but final status shows resources/coding-tools-mcp/.coding-tools/orchestration/ledger.sqlite3 is a tracked evidence file being deleted. Repository policy requires .coding-tools telemetry/history to remain version-controlled rather than be silently lost. Reject this wave so the exact ledger blob can be relocated under repository-root .coding-tools while keeping the forbidden nested source-state path absent. Then rerun source-bundle and .coding-tools history guards; prior npm test source proof remains otherwise green. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `235`
- Chain head: `060ca0a6268d2b3334e7829b2ea9b22a4448f65faa6dd34c3ef57e625695bb94`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
