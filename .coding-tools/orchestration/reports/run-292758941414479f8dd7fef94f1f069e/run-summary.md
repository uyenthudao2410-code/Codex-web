# Orchestration Run Summary

- Run: `292758941414479f8dd7fef94f1f069e`
- Task: `d0c5cd9c414c4d2d8005f242ea1416c7`
- Objective: M1-CONSOLIDATED-CORRECTION-01: implement one finite closing correction batch in E:/DEV/Codex-web with ROOT-settled semantics only. Preserve all shared dirty WIP. Exact write allowlist only: renderer/panel.html, renderer/panel.js, renderer/browser.js, tests/control-panel.test.js, tests/browser-runtime-truthfulness.test.js, optional one focused new browser VM regression test only if strictly needed, resources/coding-tools-mcp/coding_tools_mcp/operations_analytics.py, resources/coding-tools-mcp/tests/test_operations_analytics.py, docs/RECOVERY_HOST.md. Do not touch main/preloads/chatViewController/browser.html/journal/dashboard/version/permission/activation guards. Implement CSP script-src removal of unsafe-inline only; routing/run truthfulness; stale runtime truthfulness fresh-stale-fresh; transferController object args; copyCodexConfig no renderer clipboard overwrite and require copied true; strict handoff receipt validation; accepted-run analytics malformed accounting-profile handling; RECOVERY_HOST running_baseline_accepted_receipts_v2 wording. Focused proof only after coherent patch: node --test tests/control-panel.test.js tests/browser-runtime-truthfulness.test.js; python -B -m pytest tests/test_operations_analytics.py -q -p no:cacheprovider from resources/coding-tools-mcp; scoped git diff --check. Stop at ACCEPTING; no final acceptance, package build, restart, Git delivery, or permission changes.
- Status: **accepted**
- Started: `2026-09-05T19:45:37.919Z`
- Finished: `2026-09-06T01:30:41.206Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **3**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **4**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `5c3e1060590f45c4be457f52558daefa` | 1 | `run_initial_objective` | `mcp_only` | `8697ace8204e7e3da55d250d4a52d9b2b930116c` | replanned |
| 2 | `889d99f83d33445b82fbf1a1c82b6a55` | 1 | `replan_request` | `mcp_only` | `8697ace8204e7e3da55d250d4a52d9b2b930116c` | replanned |
| 3 | `81088c5da18a4e59a03359cc0e178022` | 1 | `replan_request` | `mcp_only` | `8697ace8204e7e3da55d250d4a52d9b2b930116c` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| 66db260f19a14f61a28aa60c15a38706 | 81088c5da18a4e59a03359cc0e178022 | accepted | 8697ace8204e7e3da55d250d4a52d9b2b930116c | 29457b801a40c0c54e10fb2abd24ca7fc5b5c9ef134b59d2999c1bffea54e8a0 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 41006 | `deterministic` | `deterministic` | caller_supplied_change_set |
| 41028 | `deterministic` | `deterministic` | explicit_request |
| 41058 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 41021 | `PERMISSION_REQUIRED` | `PROVING` |  |
| 41051 | `SOL_REJECTED` | `ACCEPTING` | Final acceptance is blocked because the eight exact source/test/doc bytes were durably mutated in Wave 1, while Wave 2 was proof-only and therefore has no durable mutation/adoption receipts for the current accepting wave. Replan only to adopt the exact current bytes for the same eight allowlisted files without rewriting them, rerun the focused proofs, and final-accept. Preserve unrelated shared dirty WIP; no source rewrite, replacement RUN, restart, or permission change. |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `87`
- Chain head: `48b308f0627e09eb8601c75eb1bc67935d503b8da4cdcfc4e6a07741a82f03ef`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
