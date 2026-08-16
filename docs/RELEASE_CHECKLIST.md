# Release Readiness Checklist — Desktop Execution Hub

This checklist is for the current Windows Electron **Tools-Codex-web / web-mcp-assistant** product. WebCodex core/server/npm release procedures are component-specific.

Do not create tags, push commits, publish artifacts, deploy, rotate credentials, or restart external systems unless explicitly requested.

## 1. Repository preflight

- Verify exact root, branch and HEAD.
- Inspect `git status`; preserve unrelated dirty work.
- Review [`CURRENT_STATE.md`](CURRENT_STATE.md) and `AGENTS.md`.
- Confirm no conflict markers, unintended generated files or secrets are in scope.
- Documentation-only changes normally need scoped `git diff --check` and document/link consistency, not broad code suites.

## 2. Current product contract

Confirm `package.json` version and the verified `smart-v3` eight-tool surface: `workspace_context`, `agent_workflow`, `task_control`, `document_workflow`, `exec_command`, `command_control`, `request_permissions`, `view_image`. `restart_runtime` remains a confirmed `task_control` action. Contract-fingerprint/stale-connector detection must remain intact.

Unless a separately accepted policy change says otherwise, `execution_route=auto` remains deterministic/evidence-gated, high-cost routes require acknowledgement, and provider availability does not silently expand write authority. Public schema changes require a connector-refresh/live-contract plan.

## 3. Focused source validation

Use the smallest relevant lane:

```powershell
npm test
npm run test:mcp
npm run test:all
npm run test:recovery:e2e
npm run canary:opencode-flash:preflight
```

`npm run canary:opencode-flash` performs real provider dispatch and may incur external cost; run only with explicit authorization. Rust/LSP changes use the smallest affected Rust tests required by `AGENTS.md`.

## 4. EOCL and proof integrity

- A green test is not final acceptance by itself; an `ACCEPTING` wave still needs authorized accept/reject.
- Do not accept proof from an older source/worktree fingerprint.
- Check active commands, background operations, provider/agent lanes and write lease before lifecycle operations.
- Preserve canonical evidence in `.coding-tools/orchestration/ledger.sqlite3`; do not manually edit evidence to make a release look clean.

## 5. Controlled activation boundary

Runtime-affecting source tests do not prove the current process loaded new code. Use supported controlled activation and verify expected reconnect, new process/server instance identity, unchanged workspace identity, intended revision/contract, and preserved fail-closed authority state. Do not substitute `taskkill` of the serving MCP for supervised restart.

## 6. Recovery plane checks

For recovery-related releases confirm Recovery Host ownership, bounded Windows Recovery Supervisor behavior, independent Recovery MCP identity, distinct Recovery Tunnel identity when configured, `recovery_plane_mode=independent_mcp_tunnel_v1`, confirmed bounded repair surface, and appropriate packaged Windows/login/fault-matrix proof.

## 7. Measurement and routing claims

Separate representative/benchmark/synthetic provenance, report sample size/strata, use provider-reported or measured facts, never present internal estimated credits as billing, and require explicit host-turn -> run/wave identity for host-visible latency claims. One successful explicit canary does not promote automatic routing.

## 8. Security and documentation consistency

Review artifacts for MCP/tunnel/recovery/loopback tokens, credentials, Authorization headers, `.env`/secret-store contents and raw sensitive provider/workspace telemetry. Confirm thin-proxy/single-Runtime authority remains intact.

Maintained product documents must agree: `docs/CURRENT_STATE.md`, `README.md`, `docs/ARCHITECTURE.md`, `docs/RECOVERY_HOST.md`, `docs/TESTING.md`, `docs/ROADMAP.md`, `SECURITY.md`, and this checklist. Dated `docs/research/*` remains historical chronology/evidence.

## 9. Windows packaging

The current Electron Builder target is Windows NSIS:

```powershell
npm run dist
npm run dist:dir
```

Output root is `dist\`. `package.json` currently names the installer `web-mcp-assistant-setup-${version}.${ext}` and uses `scripts/verify-packaged-resources.js` as `afterPack`. Verify bundled resources and packaged behavior from the exact accepted source.

## 10. Post-package smoke and publish

On a safe local workspace verify Desktop startup, Recovery Host/primary MCP/Tunnel/Execution Hub, `smart-v3` connector freshness, one Runtime authority, Codex Desktop thin-proxy behavior if in scope, independent Recovery MCP/Tunnel, a safe read-only workflow, and secret-free logs.

Only after explicit authorization: accept/review exact source, commit/tag without rewriting unrelated history, build from that source, verify artifact identity/smoke, publish only the authorized artifact, verify downloaded bytes/version, and record rollback evidence. Never move a published tag or force-push merely to make history look linear.
