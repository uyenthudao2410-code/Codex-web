# Production Closure & Orchestration Rollout Control Plan

> Status date: 2026-08-17
> Baseline HEAD at plan start: `3059b218989fda8ebf217d121cd6e8f74a71587d`
> Product: `web-mcp-assistant 0.3.4`
> Control authority: ChatWeb GPT-5.6 Sol
> Deterministic execution/proof authority: Coding Tools MCP / EOCL
> Canonical causal audit: `.coding-tools/orchestration/ledger.sqlite3`

## 1. Purpose

This file is the living implementation-control document for the final production-closure and orchestration-rollout program. It is updated after each accepted wave with exact evidence, commit, blockers, rollback notes, and next action. It is not a replacement for the EOCL ledger or generated run/wave reports.

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
- A green test is not final acceptance until EOCL reaches `CHECKPOINTED` when the wave requires acceptance.

## 3. Program status

| ID | Priority | Workstream | Status | Completion gate |
|---|---|---|---|---|
| P0.1 | P0 | Repository/runtime-evidence hygiene | ACCEPTED / DELIVERY PENDING | one-shot files ignored/untracked; source-root clean; ledger preserved |
| P0.2 | P0 | Installed Windows logon/session acceptance | PENDING | installer exact HEAD; supervisor task installed; logon/session resurrection proven; rollback proven |
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
- Packaged `win-unpacked` Recovery Host/Supervisor smoke exists via `npm run test:recovery:packaged` and has previously passed in isolated user data.
- Organic host-turn correlation lifetime race was fixed so pending identity survives until `host_turn_span` finalization.
- Windows live-supervisor E2E cleanup was hardened by waiting for child `close`; `npm test` subsequently passed 187/187.
- `main` and `origin/main` matched at plan start (`3059b218`).

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
- Preserved the current live binding file on disk; only Git tracking behavior changed.
- Kept the already-deleted accidentally tracked pending-turn snapshot as a source deletion for the next delivery commit.

### Proof

EOCL run `4755a66728bf42ed92e2692d15212391`, wave `0f2ce962fa8b4dcdbb1e1087cfcad7e7` reached `CHECKPOINTED`.

Passed proof nodes:

- exact `git check-ignore -v --no-index` for all four runtime-only paths;
- `git ls-files --error-unmatch .coding-tools/orchestration/ledger.sqlite3`;
- scoped Git status confirmed only expected hygiene/runtime evidence state;
- `node scripts/check-source-root-clean.js` -> `source root clean`;
- scoped `git diff --check`.

### Delivery status

Accepted technically. Commit/push will include `.gitignore`, the pending-turn tracked deletion, this control-plan update, canonical `ledger.sqlite3`, and the accepted EOCL report. SQLite WAL/SHM remain excluded.

## 6. P0.2 — Installed Windows logon/session acceptance

### Safe sequence

1. Freeze an exact accepted source fingerprint and build NSIS installer from it.
2. Record installer SHA-256 and package version.
3. Verify no active EOCL write lease, managed command, agent lane, or activation fence before installation/lifecycle changes.
4. Install to a controlled per-user location.
5. Install `WebMCP Recovery Supervisor` from the packaged executable/manifest.
6. Verify Scheduled Task identity, principal, fixed argv, executable hash, and status without exposing secrets.
7. Prove current session startup and Recovery Host authenticated ping.
8. Prove logon/session resurrection when a safe session transition can be executed without losing the control channel.
9. If reboot/logoff cannot be safely completed and verified in the current interactive channel, record it as an external manual acceptance blocker; do not mark PASS by inference.
10. Prove uninstall/rollback of the supervisor task without deleting settings, secrets, runtime-state, or ledger.

### Acceptance

- exact installer/source identity recorded;
- Scheduled Task has expected principal/triggers/fixed argv;
- packaged Recovery Host/MCP/Tunnel/device identity healthy after installed startup;
- logon/session resurrection either directly proven or explicitly BLOCKED with concrete missing external proof;
- rollback procedure proven.

## 7. P0.3 — Production Recovery fault matrix

Run only against verified owned PIDs and after capturing baseline identity/state. Every fault must have bounded timeout and post-condition checks.

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
- Native semantic localization currently reports `NATIVE_LSP_BINDING_NOT_CONFIGURED`.

### 2026-08-17 — P0.1 accepted

- Exact runtime-only ignore rules added for host correlation pending/binding and SQLite WAL/SHM sidecars.
- Canonical `ledger.sqlite3` tracking proven intact.
- Source-root cleanliness PASS.
- EOCL final acceptance: `CHECKPOINTED`.
- Delivery commit: pending.

## 13. Next action

Deliver P0.1 and this control-plan baseline to `origin/main`, then build/inspect the exact NSIS installer and prepare the installed Windows acceptance with rollback and quiescence checks before any Scheduled Task mutation.
