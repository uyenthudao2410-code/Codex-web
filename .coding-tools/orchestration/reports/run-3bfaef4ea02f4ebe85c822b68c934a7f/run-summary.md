# Orchestration Run Summary

- Run: `3bfaef4ea02f4ebe85c822b68c934a7f`
- Task: `30ee948c12514e5c98c75670dd36f6a5`
- Objective: Build a fresh local Windows NSIS installer candidate for Parent C01 from the exact currently accepted package-relevant source bytes on HEAD a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6. Bind the build to these exact existing dirty production files without modifying them: electron/services/recoveryBootstrap.js SHA256 bc15b1691813d424cd96854703e195c84070dcba49caf4180b2a0e5b6fda2b13; electron/services/recoveryHost.js SHA256 a291bfb2082341a98b013bf6e69e839a191026be0a1844c851234e6c7eaace43; electron/services/recoveryIpc.js SHA256 d87bc31981ece871a1a3188fd9f04af991cb1d911d39850999e108df445bee16; resources/coding-tools-mcp/coding_tools_mcp/continuity_telemetry.py SHA256 613b8a9243c87fc6e8e687e5121449272ccdfc25e874e043155e9fee9c32d1ce; resources/coding-tools-mcp/coding_tools_mcp/operator_report.py SHA256 f7ed54ef5d0aacee9e9091165ddc110071e33995faa33cc32228e0d12d15f5cd; scripts/dev-ui-lifecycle.js SHA256 6843b4628c8db344c0a7e1946d0d390e2ae26e2efd73f2f30de65403d967cd50. The package census has shown no other tracked or untracked package-runtime paths. Run the official npm run dist build, which includes test:all and Windows NSIS packaging. Capture exact installer artifact path, size, and SHA256. This is a local candidate only: no install, launch, reboot, runtime restart, commit, push, publish, tag, release, or deploy.
- Status: **accepted**
- Started: `2026-09-15T04:08:57.182Z`
- Finished: `2026-09-15T04:21:40.626Z`

## Outcome metrics

- Waves: **3**
- Route decisions: **1**
- Failures observed: **2**
- REPLAN transitions: **2**
- Proof stages: **3**
- Proof cache hits: **0**
- Acceptance checkpoints: **1**

## Waves

| # | Wave | Objective rev | Objective source | Mode | Base | Status |
|---:|---|---:|---|---|---|---|
| 1 | `96043c953efa4c8da3576a68e4cb4244` | 1 | `run_initial_objective` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | replanned |
| 2 | `8869a92be62d48258151da0bc6b598c7` | 2 | `replan_request` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | replanned |
| 3 | `c1aa788c20174a26b0d92074a5189139` | 3 | `replan_request` | `mcp_only` | `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6` | accepted |

## Acceptance checkpoints

| Checkpoint | Wave | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|---|
| cb380161714943048b0deeec55218f6b | c1aa788c20174a26b0d92074a5189139 | accepted | a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6 | 54ea11eacd142f384ca69864c4e2fde3a8fbad388a70252aa727a1698ddfc631 | chatweb |

## Route decisions

| Seq | Requested | Resolved | Reason |
|---:|---|---|---|
| 55996 | `deterministic` | `deterministic` | explicit_request |

## Failures / replans

| Seq | Failure class | State | Evidence |
|---:|---|---|---|
| 55950 | `COMPLETION_READINESS_BLOCKED` | `PREFLIGHT` |  |
| 55963 | `COMPLETION_READINESS_BLOCKED` | `PREFLIGHT` |  |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `67`
- Chain head: `257f11dae00a53b867698a8cc6bf5c1f8854bf5a375f998eb4e13141989be4b3`

> This file is generated from the append-only orchestration ledger. Do not hand-maintain it as a second source of truth.
