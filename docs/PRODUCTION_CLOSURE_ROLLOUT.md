# Production Closure & Orchestration Rollout Control Plan

> Status date: 2026-08-17
> Baseline HEAD at plan start: `3059b218989fda8ebf217d121cd6e8f74a71587d`
> Current delivered HEAD before packaging remediation: `bae11481a54c5ec9ecd2c724b15ee2e4539e3bdf`
> Product: `web-mcp-assistant 0.3.4`
> Control authority: ChatWeb GPT-5.6 Sol
> Deterministic execution/proof authority: Coding Tools MCP / EOCL
> Canonical causal audit: `.coding-tools/orchestration/ledger.sqlite3`

## 1. Purpose

This file is the living implementation-control document for the final production-closure and orchestration-rollout program. It is updated after each material wave with exact evidence, commit, blockers, rollback notes, and next action. It is not a replacement for the EOCL ledger or generated run/wave reports.

The goal is to finish the current product without adding unnecessary architecture:

1. close repository/runtime-evidence hygiene;
2. prove installed Windows logon/session recovery behavior;
3. prove production Recovery fault handling with ownership/orphan checks;
4. establish an exact-fingerprint release-candidate gate;
5. collect representative paired routing economics from real accepted tasks;
6. promote only evidence-qualified automatic routes, otherwise remain fail-closed deterministic;
7. evaluate semantic localization/LSP integration only if measured benefit justifies the operational cost.

## 2. Safety and evidence invariants

- No two peer Coding Tools runtimes may independently own the same workspace/ledger.
- `execution_route=auto` remains deterministic until representative accepted paired evidence clears the runtime promotion gate.
- No synthetic/benchmark row can promote production routing.
- No paid provider canary may run without explicit external-cost authorization.
- Installed Windows/Scheduled Task/fault injection steps must verify exact target, current owner identity, rollback path, and quiescent EOCL/managed jobs before mutation.
- Recovery faults must never kill or adopt a foreign/unverified process.
- `ledger.sqlite3` remains tracked and must be included in delivery commits; SQLite `-wal`/`-shm` sidecars remain runtime-only.
- One-shot host-correlation files (`chatweb-host-turn-pending.json`, `chatweb-host-turn-binding.json`) are runtime-only and must not be source-controlled.
- Source proof, live activation, packaged proof, installed-session proof, and release/publish claims are separate states.
- A green test is not final EOCL acceptance until the relevant wave reaches `CHECKPOINTED` when EOCL acceptance is available and required.
- Wrapper/orchestration projection errors are recorded separately from the underlying terminal command result; neither is allowed to overwrite the other.

## 3. Program status

| ID | Priority | Workstream | Status | Completion gate |
|---|---|---|---|---|
| P0.1 | P0 | Repository/runtime-evidence hygiene | **COMPLETE / DELIVERED** | one-shot files ignored/untracked; source-root clean; ledger preserved |
| P0.2 | P0 | Installed Windows logon/session acceptance | **IN PROGRESS — PACKAGING BLOCKER REMEDIATED, DELIVERY PENDING** | installer exact HEAD; supervisor task installed; logon/session resurrection proven; rollback proven |
| P0.3 | P0 | Production Recovery fault matrix | PENDING | controlled fault cases pass with no foreign adoption, duplicate owner/listener, orphan, or state corruption |
| P1.1 | P1 | Exact-fingerprint release candidate | PENDING | source + MCP + Recovery E2E + packaged + installer/provenance gates pass on one exact accepted fingerprint |
| P1.2 | P1 | Representative routing economics | PENDING | homogeneous accepted paired cohorts by task class/oracle/environment with measured quality/time/cost |
| P1.3 | P1 | Selective auto-routing promotion | GATED | only task classes that satisfy representative promotion thresholds may change from deterministic |
| P2.1 | P2 | Semantic localization optimization | PENDING | benchmark demonstrates material positive value; otherwise retain text fallback and record KEEP_CURRENT |
| D1 | Delivery | Commit/push accepted waves | ACTIVE | each accepted source/docs wave pushed with ledger, excluding transient SQLite sidecars |

## 4. Current baseline evidence

### Already closed before this plan

- P2/P3 LSP/resource hardening closed on 2026-08-16 with live Connector/Runner/rust-analyzer soak and fail-closed resource controls.
- Device Identity + Recovery ownership + controlled Recovery activation closed technically and delivered.
- Packaged Recovery Host/Supervisor isolated smoke exists via `npm run test:recovery:packaged`.
- Organic host-turn correlation lifetime race was fixed so pending identity survives until `host_turn_span` finalization.
- Windows live-supervisor E2E cleanup was hardened by waiting for child `close`; broad `npm test` subsequently passed 187/187.

### Current intentional gates

- Automatic non-deterministic routing: OFF / deterministic fail-closed.
- Auto-handoff: OFF.
- Paid OpenCode Flash terminal canary: not authorized by this plan.
- Native semantic localization: currently unavailable with `NATIVE_LSP_BINDING_NOT_CONFIGURED`; bounded text fallback remains functional.

## 5. P0.1 — Repository/runtime-evidence hygiene

### Implemented

- Added exact runtime-only ignore rules for:
  - `.coding-tools/evaluation/chatweb-host-turn-pending.json`
  - `.coding-tools/evaluation/chatweb-host-turn-binding.json`
  - `.coding-tools/orchestration/ledger.sqlite3-wal`
  - `.coding-tools/orchestration/ledger.sqlite3-shm`
- Preserved `.coding-tools/orchestration/ledger.sqlite3` as a tracked canonical evidence file.
- Preserved live one-shot binding state on disk while removing it from source-control concerns.
- Removed the accidentally tracked pending-turn snapshot from source control.

### Proof and delivery

EOCL run `4755a66728bf42ed92e2692d15212391`, wave `0f2ce962fa8b4dcdbb1e1087cfcad7e7` reached `CHECKPOINTED`.

Passed:

- exact `git check-ignore -v --no-index` for all four runtime-only paths;
- canonical ledger `git ls-files` tracking proof;
- `node scripts/check-source-root-clean.js` -> `source root clean`;
- scoped `git diff --check`.

Delivered commit:

- `bae11481 chore: close runtime evidence hygiene`
- pushed to `origin/main`.

## 6. P0.2 — Installed Windows logon/session acceptance

### 6.1 First installed acceptance attempt — FAILED AS DESIGNED

Exact delivered source used for the first installer attempt:

- HEAD: `bae11481a54c5ec9ecd2c724b15ee2e4539e3bdf`
- version: `0.3.4`
- NSIS installer: `dist/web-mcp-assistant-setup-0.3.4.exe`
- installer size: `128661526` bytes
- installer SHA-256: `66a2455bfed8c9b8da4b1d755b1c27513ef04285e8412a761334734b3b455481`

Preflight proved there was no existing `Trợ lý Web MCP` installation and no existing `WebMCP Recovery Supervisor` Scheduled Task. Development primary/recovery planes were alive and were not modified by the installation step.

The installer was installed silently into the controlled per-user acceptance location:

`%LOCALAPPDATA%/Programs/WebMcpAcceptance-0.3.4`

Installed executable SHA-256:

`d0b66abd4770effea83d581ba76ba5f4d598218db80e9aa4be16ca940769c07b`

The Scheduled Task was created with the expected same-user Limited principal, logon + minute heartbeat triggers, fixed PowerShell action, packaged manifest, fixed `--recovery-host` argv, and executable hash. However its runtime acceptance failed:

- Task state: `Ready`
- `LastTaskResult = 1`
- installed supervisor `Action Once` returned `RECOVERY_SUPERVISOR_FAILED`
- message: `Recovery Supervisor executable missing.`

The manifest itself contained the correct Unicode executable path and Python confirmed the executable existed. The root cause was packaged-source drift:

- current source Recovery Supervisor SHA-256: `540730e485fb6ddf802c6df5be1a638fa920d4d1531144a8d6bb75d4fc42090f`
- packaged/installed Recovery Supervisor SHA-256: `7c2e89822a78b647e6d979a9dc052da6c404172bb5527f90380feb121f2d9ca8`
- current source contained explicit UTF-8 `ReadAllText(..., UTF8)` handling;
- packaged copy did not.

Therefore the installer built from the delivered HEAD was not byte-identical to current `resources/` and the installed Unicode-path test correctly exposed the stale package.

Rollback was executed immediately:

- `WebMCP Recovery Supervisor` unregistered successfully;
- task presence after rollback: false;
- persistent app settings/secrets/runtime state and project ledger were not deleted.

The controlled acceptance installation directory remains available only for comparison until the fixed installer is rebuilt and installed.

### 6.2 Packaging integrity remediation — SOURCE PROOF PASS / DELIVERY PENDING

Current WIP changes:

1. `scripts/clean-dist.js` removes `dist/` with bounded Windows retries before every Electron Builder package.
2. `package.json` routes both `dist` and `dist:dir` through the clean step.
3. `scripts/verify-packaged-resources.js` now builds an allowed source/package file projection and fails closed on missing, unexpected, size-different, or SHA-256-different packaged resources while preserving cache/runtime/report exclusions.
4. `scripts/packaged-recovery-smoke.js` additionally checks that the packaged Recovery Supervisor hash equals current source before spawning packaged processes.
5. `tests/build-verification.test.js` covers the clean-output requirement and stale packaged byte rejection.

Authoritative standalone proof after clearing prior quiesced packager contention:

- no stale `electron-builder`/`app-builder`/7zip packager child remained; only the development Electron Node process matched the repository and was not touched;
- one first package retry failed with Windows `EBUSY` on `dist/win-unpacked/LICENSES.chromium.html` while prior packaging activity was settling; process inspection established the contention was gone before retry;
- subsequent `npm run test:recovery:packaged` exited `0` after full Electron Builder packaging;
- packaged Recovery smoke returned `ok=true`;
- packaged Recovery Host ready: PASS;
- device identity present: PASS;
- recovery mode `independent_mcp_tunnel_v1`: PASS;
- Recovery MCP alive: PASS;
- Recovery Supervisor healthy: PASS;
- live-owner fail-closed: PASS;
- executable hash mismatch fail-closed: PASS;
- Scheduled Task mutation during packaged smoke: false;
- focused `build-verification + recovery-supervisor` tests: **13/13 PASS**;
- explicit full resource source/package identity: `exact_source=true`, **249 files**;
- `git diff --check`: PASS.

EOCL note: several wrapper-managed package waves were quiesced/replanned before their package child reached terminal output, and one generic build-verification lane also reported a false-negative because `dist:dir` did not create the artifact shape expected by its generic collector. Those wrapper projections are not being used as package PASS evidence. The standalone managed terminal commands above are the source proof for this remediation. A clean EOCL checkpoint/delivery boundary is still required before calling the remediation delivered.

### 6.3 Remaining installed acceptance sequence

After packaging remediation is delivered on an exact HEAD:

1. build a fresh NSIS installer from that exact HEAD and record SHA-256;
2. remove/replace the controlled stale acceptance installation;
3. reinstall the fixed package to the controlled per-user location;
4. install `WebMCP Recovery Supervisor` from the installed package;
5. prove Task action/principal/triggers/manifest/executable identity;
6. prove installed supervisor `Action Once` sees the existing healthy owned Recovery Host rather than spawning/killing anything;
7. prove current-session packaged Recovery health/device identity;
8. prove supervisor uninstall/rollback again;
9. perform true logon/reboot resurrection only if the current control topology can survive and verify it. Otherwise record the exact manual/external acceptance blocker; do not infer PASS.

## 7. P0.3 — Production Recovery fault matrix

Run only after P0.2 fixed-package current-session acceptance is green, against verified owned PIDs and after capturing baseline identity/state. Every fault has a bounded timeout and post-condition checks.

| Case | Fault | Expected recovery | Critical assertions |
|---|---|---|---|
| F1 | Kill primary Coding MCP owned PID | primary restart only as policy requires | new process/server identity; same workspace/device; tunnel continuity or documented restart semantics |
| F2 | Kill primary Tunnel owned PID | tunnel-only recovery | Coding MCP process identity preserved; tunnel new PID; healthy port |
| F3 | Kill Recovery Host owned PID | Windows Supervisor resurrects host | new host PID/instance; Recovery MCP/Tunnel ownership preserved/adopted only with proof |
| F4 | Exit/restart Electron UI | UI reconnect only | Recovery Host + primary/recovery planes survive; no duplicate authority |
| F5 | Simulated live-but-unhealthy MCP | bounded defer then escalation | no premature kill; escalation only after threshold; no duplicate process |
| F6 | stale/foreign ownership fixture | fail closed | no adopt/kill; typed ownership error |
| F7 | executable/manifest hash mismatch | fail closed | Supervisor refuses spawn; no arbitrary executable path |
| F8 | crash during Recovery Host handoff | rollback/resume old or validated new owner | single lock owner; no orphan/duplicate listener; activation terminal state |
| F9 | reboot/logon persistence | installed supervisor/runtime returns | only if safely verifiable in current control topology |

Post-case invariant: no active orphan/overlap/stale EOCL run, no duplicate listeners on primary/recovery MCP and health ports, and all owned state identities are coherent.

## 8. P1.1 — Exact-fingerprint release candidate

Run once after P0 source changes stop:

- `git diff --check`
- `npm test`
- `npm run test:mcp`
- `npm run test:recovery:e2e`
- `npm run test:recovery:packaged`
- `npm run canary:opencode-flash:preflight`
- `npm audit --omit=dev`
- `npm run dist`
- installer/resource/provenance verification
- controlled live activation/instance verification for any runtime-affecting source delta

Record exact HEAD, worktree/source fingerprint, package version, installer SHA-256, test counts, skipped tests, and any accepted external blocker.

Do not create a release/tag/publish artifact unless explicitly authorized separately.

## 9. P1.2 — Representative routing economics

### Principle

Do not create synthetic work just to reach a sample count. Enroll real accepted engineering tasks when they naturally occur. A pair is eligible only when source/task semantics/oracle/environment are comparable and provenance is `representative`.

### Initial task classes

- localized strong-oracle bugfix;
- cross-file bounded change;
- deep integration/debugging;
- test-failure repair;
- read-only research/diagnosis.

### Per-pair fields

- `pair_id`, `task_class`, `oracle_id`, `environment_id`, `cache_stratum`, `replicate_id`;
- route/policy/topology;
- accepted/rejected result;
- TTA/wall time;
- measured or provider-reported tokens/cost when available;
- critical/noncritical defects, manual repair, rollback, regression escape;
- host-observed latency only when explicit trace/turn binding exists.

### Promotion rule

A task class remains deterministic unless the runtime's representative promotion gate is satisfied. Benchmark/synthetic evidence may guide experiments but never authorize production promotion.

## 10. P1.3 — Selective routing promotion

- Query runtime promotion readiness by task class.
- Promote only explicitly supported task classes with sufficient accepted representative pairs and quality/cost/time advantage.
- Keep other classes deterministic.
- Never auto-promote `sol_max`/`sol_ultra`.
- Auto-handoff remains independently gated even if a routing class is promoted.

If no class qualifies, record `KEEP_DETERMINISTIC` as the accepted result; that is a successful evidence-based decision, not an incomplete implementation.

## 11. P2.1 — Semantic localization optimization

Current runtime status: `NATIVE_LSP_BINDING_NOT_CONFIGURED`.

Evaluate before implementing:

1. identify the exact provider/binding configuration required by the current runtime;
2. run a bounded benchmark comparing semantic-first localization vs bounded text fallback on representative repository queries;
3. measure latency, tool hops, result quality/recall, memory/process pressure, and operational fragility;
4. enable/configure only if benefit is material and does not reopen the closed P2/P3 memory/resource risk;
5. otherwise record `KEEP_TEXT_FALLBACK` and leave correctness path unchanged.

## 12. Progress log

### 2026-08-17 — Plan initialized

- Baseline HEAD: `3059b218989fda8ebf217d121cd6e8f74a71587d`.
- Maintained docs confirm packaged Recovery exists but installed logon/session proof remains a release boundary.
- `execution_route=auto` intentionally remains deterministic pending representative paired evidence.
- Native semantic localization reports `NATIVE_LSP_BINDING_NOT_CONFIGURED`.

### 2026-08-17 — P0.1 complete and delivered

- Runtime-only host-correlation + SQLite sidecar Git hygiene closed.
- Canonical `ledger.sqlite3` tracking proven intact.
- Source-root cleanliness PASS.
- EOCL final acceptance `CHECKPOINTED`.
- Delivered: `bae11481 chore: close runtime evidence hygiene`.

### 2026-08-17 — P0.2 first installed attempt found release blocker

- Exact NSIS installer from `bae11481` built and installed to controlled per-user target.
- Real Scheduled Task registration succeeded structurally but runtime `Action Once` failed.
- Root cause proven: packaged Recovery Supervisor bytes were stale versus source, so Unicode executable path decoding fix was absent from installer.
- Scheduled Task rollback PASS; no persistent project/runtime evidence deleted.

### 2026-08-17 — Packaging exact-source remediation proven

- Clean-dist prepackage boundary added.
- Full allowed `resources/` byte-identity afterPack gate added.
- Packaged Recovery smoke gains source hash guard.
- 13/13 focused tests PASS.
- Full exact-source identity PASS for 249 files.
- Full packaged Recovery smoke PASS after terminal Electron Builder run.
- Delivery/clean EOCL checkpoint still pending before P0.2 can resume.

## 13. Next action

1. establish a clean acceptance/delivery boundary for the packaging integrity remediation;
2. commit/push the remediation with the updated control plan and canonical ledger, excluding volatile runtime projections/SQLite sidecars;
3. build a fresh NSIS installer from the new exact HEAD;
4. replace the controlled stale acceptance installation and rerun P0.2 Scheduled Task/current-session acceptance;
5. only after P0.2 current-session acceptance is green, proceed to the production Recovery fault matrix.
