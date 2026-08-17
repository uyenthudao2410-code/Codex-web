# Production Closure & Orchestration Rollout Control Plan

> Status date: 2026-08-17
> Baseline HEAD at plan start: `3059b218989fda8ebf217d121cd6e8f74a71587d`
> Current delivered HEAD before sparse-state remediation delivery: `d5d4bbb533b21937041c1b48a2005583f2652383`
> Product: `web-mcp-assistant 0.3.4`
> Control authority: ChatWeb GPT-5.6 Sol
> Deterministic execution/proof authority: Coding Tools MCP / EOCL
> Canonical causal audit: `.coding-tools/orchestration/ledger.sqlite3`

## 1. Purpose

This file is the living implementation-control document for the final production-closure and orchestration-rollout program. It is updated after each material wave with exact evidence, commit, blockers, rollback notes, and next action. It is not a replacement for the EOCL ledger or generated run/wave reports.

The goal is to finish the current product without adding unnecessary architecture:

1. close repository/runtime-evidence hygiene;
2. prove installed Windows current-session and persistence recovery behavior;
3. prove Recovery fault handling with exact ownership/orphan checks;
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
- Once source bytes change, every previously built installer/package is stale for final acceptance even if it was valid for the prior exact HEAD.
- True reboot/logon persistence is not inferred from current-session proof. If the active control topology cannot survive logout/reboot and verify the result, it remains an explicit external acceptance item.

## 3. Program status

| ID | Priority | Workstream | Status | Completion gate |
|---|---|---|---|---|
| P0.1 | P0 | Repository/runtime-evidence hygiene | **COMPLETE / DELIVERED** | one-shot files ignored/untracked; source-root clean; ledger preserved |
| P0.2 | P0 | Installed Windows Recovery Supervisor acceptance | **CURRENT-SESSION COMPLETE / PERSISTENCE EXTERNAL** | exact installer + real Scheduled Task + `Action Once` + rollback proven; reboot/logon persistence explicitly remains external/unverified |
| P0.3 | P0 | Production Recovery fault matrix | PENDING | controlled isolated/installed fault cases pass with no foreign adoption, duplicate owner/listener, orphan, or state corruption |
| P1.1 | P1 | Exact-fingerprint release candidate | PENDING | source + MCP + Recovery E2E + packaged + installer/provenance gates pass on one exact accepted fingerprint |
| P1.2 | P1 | Representative routing economics | PENDING | homogeneous accepted paired cohorts by task class/oracle/environment with measured quality/time/cost |
| P1.3 | P1 | Selective auto-routing promotion | GATED | only task classes that satisfy representative promotion thresholds may change from deterministic |
| P2.1 | P2 | Semantic localization optimization | **BLOCKED_CONFIG / ASSESSMENT PENDING** | configure only if exact binding exists and benchmark shows material value; otherwise keep bounded text fallback |
| D1 | Delivery | Commit/push accepted waves | ACTIVE | each accepted source/docs wave pushed with ledger, excluding transient SQLite sidecars/runtime projections |

## 4. Current baseline evidence

### Already closed before this plan

- P2/P3 LSP/resource hardening closed on 2026-08-16 with live Connector/Runner/rust-analyzer soak and fail-closed resource controls.
- Device Identity + Recovery ownership + controlled Recovery activation closed technically and delivered.
- Packaged Recovery Host/Supervisor isolated smoke exists via `npm run test:recovery:packaged`.
- Organic host-turn correlation lifetime race was fixed so pending identity survives until `host_turn_span` finalization.
- Windows live-supervisor E2E cleanup was hardened by waiting for child `close`; broad root Node verification had previously passed.

### Current intentional gates

- Automatic non-deterministic routing: OFF / deterministic fail-closed.
- Auto-handoff: OFF.
- Paid OpenCode Flash terminal canary: not authorized by this plan.
- Native semantic localization: currently unavailable with `NATIVE_LSP_BINDING_NOT_CONFIGURED`; runtime reports missing binding origin and credential-file configuration. Bounded text fallback remains functional.

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

## 6. P0.2 — Installed Windows Recovery Supervisor acceptance

### 6.1 First installed acceptance attempt — FAILED AS DESIGNED

Exact delivered source used for the first installer attempt:

- HEAD: `bae11481a54c5ec9ecd2c724b15ee2e4539e3bdf`
- version: `0.3.4`
- NSIS installer: `dist/web-mcp-assistant-setup-0.3.4.exe`
- installer size: `128661526` bytes
- installer SHA-256: `66a2455bfed8c9b8da4b1d755b1c27513ef04285e8412a761334734b3b455481`

Preflight proved there was no existing acceptance installation and no existing `WebMCP Recovery Supervisor` Scheduled Task. Development primary/recovery planes were alive and were not modified by the installation step.

The installer was installed silently into a controlled per-user acceptance location. The Scheduled Task was created with the expected same-user Limited principal, logon + minute heartbeat triggers, fixed PowerShell action, packaged manifest, fixed `--recovery-host` argv, and executable hash. However its runtime acceptance failed:

- Task state: `Ready`
- `LastTaskResult = 1`
- installed supervisor `Action Once` returned `RECOVERY_SUPERVISOR_FAILED`
- message: `Recovery Supervisor executable missing.`

The manifest itself contained the correct Unicode executable path and independent filesystem proof showed the executable existed. The root cause was packaged-source drift:

- current source Recovery Supervisor SHA-256 at diagnosis: `540730e485fb6ddf802c6df5be1a638fa920d4d1531144a8d6bb75d4fc42090f`
- packaged/installed Recovery Supervisor SHA-256: `7c2e89822a78b647e6d979a9dc052da6c404172bb5527f90380feb121f2d9ca8`
- current source contained explicit UTF-8 file-reading handling;
- packaged copy did not.

Therefore the installer was not byte-identical to current `resources/` and the installed Unicode-path test correctly exposed the stale package.

Rollback was executed immediately:

- `WebMCP Recovery Supervisor` unregistered successfully;
- task presence after rollback: false;
- persistent app settings/secrets/runtime state and project ledger were not deleted.

### 6.2 Packaging integrity remediation — COMPLETE / DELIVERED

Implemented:

1. `scripts/clean-dist.js` removes `dist/` with bounded Windows retries before every Electron Builder package.
2. `package.json` routes both `dist` and `dist:dir` through the clean step.
3. `scripts/verify-packaged-resources.js` builds an allowed source/package file projection and fails closed on missing, unexpected, size-different, or SHA-256-different packaged resources while preserving cache/runtime/report exclusions.
4. `scripts/packaged-recovery-smoke.js` checks that the packaged Recovery Supervisor hash equals current source before spawning packaged processes.
5. `tests/build-verification.test.js` covers the clean-output requirement and stale packaged-byte rejection.

Proof:

- standalone `npm run test:recovery:packaged` terminal run exited `0` after Electron Builder packaging;
- packaged Recovery smoke returned `ok=true`;
- Recovery Host/device/recovery MCP/Supervisor/fail-closed guards passed;
- focused `build-verification + recovery-supervisor` tests: **13/13 PASS**;
- full allowed resource source/package identity: `exact_source=true`, **249 files**;
- scoped/global diff hygiene passed.

EOCL acceptance for the packaging remediation reached a clean checkpoint before delivery.

Delivered commit:

- `d5d4bbb5 fix: enforce exact-source packaged resources`
- pushed to `origin/main`.

### 6.3 Fresh exact-HEAD installer from packaging-hardened source — BUILD ACCEPTED

EOCL build run:

- run: `3ca4f890a8ae4090ac9858c0b0e68d46`
- wave: `16b3281053d24c32941153b9ab1fc428`
- final state: `CHECKPOINTED`

Exact source/artifact:

- HEAD: `d5d4bbb533b21937041c1b48a2005583f2652383`
- version: `0.3.4`
- `npm run dist`: exit `0`
- installer: `dist/web-mcp-assistant-setup-0.3.4.exe`
- installer size: `128670087` bytes
- installer SHA-256: `A81AAB1C1399F4E8D57E090CBA25E5B6A939EDE2F9EB60E9C2C8A8E10C723AE2`
- packaged Recovery Supervisor SHA-256: `540730E485FB6DDF802C6DF5BE1A638FA920D4D1531144A8D6BB75D4FC42090F`

The packaged supervisor was byte-identical to the source for that exact HEAD. This installer was valid for the second installed acceptance attempt, but became stale for final acceptance once the sparse-state source remediation below changed supervisor bytes.

### 6.4 Second installed acceptance attempt — FAILED AS DESIGNED ON PERSISTED-STATE COMPATIBILITY

Preflight immediately before mutation proved:

- exact HEAD `d5d4bbb533b21937041c1b48a2005583f2652383`;
- installer SHA/size exactly matched the accepted build above;
- controlled acceptance installation `%LOCALAPPDATA%\WebMcpAcceptance-0.3.4` was absent;
- Scheduled Task `WebMCP Recovery Supervisor` was absent;
- supervisor install root was absent;
- persisted supervisor status existed in the sparse `uninstalled` shape created by prior uninstall;
- Recovery Host descriptor owner PID `32536`, instance `f021dea5f56a9e72b7cce8b59908c003`;
- primary MCP listener: port `18766`, PID `24420`;
- Recovery MCP listener: port `18767`, PID `38980`;
- primary Tunnel listener: health port `18082`, PID `24932`;
- Recovery Tunnel listener: health port `18083`, PID `29972`.

The accepted NSIS installer was installed silently into `%LOCALAPPDATA%\WebMcpAcceptance-0.3.4`:

- NSIS exit: `0`;
- installed executable SHA-256: `37A63DC1BBA170353D0E0355ADCC4FF44D06179532547C66CACC610613BA5DFB`;
- installed Recovery Supervisor SHA-256: `540730E485FB6DDF802C6DF5BE1A638FA920D4D1531144A8D6BB75D4FC42090F`;
- installed `app.asar` SHA-256: `0918156F6AAA6CC2F296ACE30D82818F899DEA8194FBBEC9610AA8DEE4D95574`;
- uninstaller present.

Real Scheduled Task registration succeeded structurally:

- task name: `WebMCP Recovery Supervisor`;
- same-user Interactive logon;
- Limited run level;
- fixed PowerShell action invoking installed supervisor with `-Action Run`;
- logon + minute heartbeat triggers;
- packaged manifest arguments exactly `['--recovery-host']`;
- installed supervisor copy hash matched package/source for `d5d4bbb5`.

Runtime acceptance then failed:

- Task state after launch: `Ready`;
- `LastTaskResult = 1`;
- persisted status still `uninstalled`;
- direct installed `Action Once` exited `1`;
- typed code: `RECOVERY_SUPERVISOR_FAILED`;
- exact error: `The property 'last_healthy_at' cannot be found on this object. Verify that the property exists.`

Root cause:

- the script runs with `Set-StrictMode -Version Latest`;
- `Uninstall` intentionally writes a sparse persisted `uninstalled` status;
- `New-State` directly dereferenced optional historical properties such as `last_healthy_at` that are absent in that sparse schema;
- therefore a legitimate persisted state created by the product itself could not be rehydrated on the next install/run.

This is a real persisted-state schema-compatibility bug. It is independent from the first Unicode/packaging blocker.

Rollback was executed immediately and verified:

- Scheduled Task absent;
- `%LOCALAPPDATA%\WebMcpRecoverySupervisor` absent;
- persisted supervisor status returned to `uninstalled`;
- primary/recovery runtime ownership was not intentionally modified.

The acceptance application itself remains installed only as a stale controlled comparison artifact until replacement by the next exact-HEAD installer.

### 6.5 Sparse persisted-state compatibility remediation — COMPLETE / DELIVERED

Implementation is deliberately minimal:

- added a bounded optional-property accessor used only while materializing `New-State` from persisted JSON;
- missing optional legacy/sparse fields receive safe defaults;
- present malformed values still pass through existing casts/logic and therefore retain existing fail-closed behavior;
- ownership verification, manifest/executable identity, restart thresholds, cooldowns, suppression, mutex handling, and live-owner rules are unchanged.

Normalized optional fields:

- `last_healthy_at`;
- `last_host_pid`;
- `last_host_instance_id`;
- `consecutive_failures` -> default `0`;
- `restart_attempts` -> default empty list;
- `next_attempt_after`;
- `suppressed_until`.

Regression added:

- writes the exact sparse persisted `uninstalled` status shape;
- presents an authenticated healthy Recovery Host with exact PID/instance identity;
- runs `Action Once`;
- requires `healthy`, same host PID/instance, zero consecutive failures, empty restart attempts, populated `last_healthy_at`, and no spawned replacement PID.

Proof:

- `node --test tests/recovery-supervisor.test.js`: **12/12 PASS**;
- `git diff --check -- resources/recovery-supervisor/recovery-supervisor.ps1 tests/recovery-supervisor.test.js`: PASS;
- current remediated supervisor source SHA-256: `E0B906C1EC9AB5C3E9F1F52BA7B3D05F6FEFE42259F15A48AB3077A730076420`;
- source delta: 2 files, 3 insertions, 1 deletion.

EOCL acceptance:

- run: `274bd626bfb44943afedb3e755002ad0`;
- wave: `62183559c12943ec8e9a9dec25c4f257`;
- final state: `CHECKPOINTED`;
- integrity check: PASS (`checked=76`).

Delivered commit:

- `acaa3582 fix: normalize recovery supervisor persisted state`
- pushed/aligned with `origin/main` before the final P0.2 installer build.

The old `A81A...` installer is intentionally retained as **STALE HISTORICAL EVIDENCE ONLY** because its supervisor bytes predate this remediation.

### 6.6 Final exact-HEAD installed acceptance — CURRENT-SESSION COMPLETE

Exact source/artifact used for final current-session acceptance:

- HEAD: `acaa3582052ab6836ade7b55bd1ff2178ebc5117`;
- installer: `dist/web-mcp-assistant-setup-0.3.4.exe`;
- installer size: `128670108` bytes;
- installer SHA-256: `0371F160B33621556F16F537297D60E5575690BE076BE053A5802E2A1532C879`;
- Recovery Supervisor source/package SHA-256: `E0B906C1EC9AB5C3E9F1F52BA7B3D05F6FEFE42259F15A48AB3077A730076420`;
- exact packaged resource projection: `249` files, `exact_source=true`;
- accepted build run `c6235e7dfefe4df9938bf6d0b4c11bca`, wave `b344e00d5ef64bc49668727834bf9e30` -> `CHECKPOINTED`.

Installed-session evidence:

- stale NSIS self-delete residue was proven to be an empty target with no process before conditional removal: run `1151d304b5864708ad6f694d9fd91b6c`, wave `fc5cc270eec8419b93c57e78b2871d0f`;
- fresh controlled installation and exact installed Supervisor hash: run `dfc0f3be347540989489dbf10574b48f`, wave `9406a7adde4b4fadb459237cd6fba1ce`;
- real Scheduled Task principal/action/triggers/manifest identity: run `44add57e789e4b14bcef1588f0e371b9`, wave `730ddc9e526b4c4981ca1c82e257196c`; raw Task Scheduler `UserId=Admin` and Windows identity `DESKTOP-63643J4\Admin` resolved to the same canonical SID;
- continuous Supervisor reached `healthy` on the existing Recovery Host without replacement;
- installed `Action Once` observed the exact existing Recovery Host and returned `last_spawned_pid=null`; scheduled-loop resume again reached `healthy`: run `f8219ca3acf8470ca39a86bedf546dad`, wave `6682903e59f549b3b721275a99788fe8`;
- authenticated product-native Recovery Host IPC plus independent Recovery/listener checks proved primary `mcpRunning/nativeAlive/tunnelRunning/fullyReady=true`, Recovery Host/MCP/Tunnel healthy, exact device lifecycle identity, and one expected listener each on ports `18766`, `18767`, `18082`, and `18083`: run `0d3dc1349077416680946c08c76875ef`, wave `68c8cab1593f46249c3f801d7e85cdcf` -> `CHECKPOINTED`;
- acceptance baseline Recovery Host remained PID `32536`, instance `399ea2ec2d751b606a2ffe7788727ac6` throughout the installed-session proof;
- mandatory Supervisor rollback removed the Scheduled Task and `%LOCALAPPDATA%\WebMcpRecoverySupervisor`, persisted status returned to `uninstalled`, the controlled acceptance app was preserved for isolated packaged fault testing, and primary/recovery runtime health remained intact;
- final rollback verification: run `f64f9aac35d8459e903524953b3e0943`, wave `855626394161448fa5ea98ed60c61c62`, accepted P0.2 proof fingerprint `886ab2d4e0bbee7c89d62fb7124a979aae241f6cd849983193efa77899697d2f` -> `CHECKPOINTED`.

Harness/control observations explicitly excluded from product-regression classification:

- Task Scheduler normalizes the same-user principal string (`Admin` vs `DESKTOP-63643J4\Admin`); canonical SID equality proved identity;
- anonymous `GET /__control/health` correctly returned `401 Unauthorized`; final proof used shipped authenticated Recovery Host IPC;
- a temporary Electron `safeStorage` helper produced no result and was abandoned/cleaned rather than used as evidence;
- one post-rollback PowerShell check used the reserved automatic `$PID` variable and failed with `VariableNotWritable`; the corrected `$ownerPid` read-only check passed without repeating rollback.

Current external state after P0.2 rollback:

- `WebMCP Recovery Supervisor` Scheduled Task: absent;
- `%LOCALAPPDATA%\WebMcpRecoverySupervisor`: absent;
- persisted Supervisor state: `uninstalled`;
- `%LOCALAPPDATA%\WebMcpAcceptance-0.3.4`: preserved for P0.3 isolated packaged fault testing;
- development Recovery Host, primary/recovery MCP, and both Tunnels: healthy/coherent at final proof.

**Persistence boundary:** true reboot/logon resurrection has not been executed from a control topology that can survive and independently verify the reboot/logon result. It remains an explicit external acceptance item and is not inferred from the current-session proof.

## 7. P0.3 — Recovery fault matrix

Run only after P0.2 fixed-package current-session acceptance is green. Destructive faults that could sever the current Coding MCP control plane must run in an isolated packaged real-process harness rather than against the active control connection. Do not label an isolated proof as a live-production kill.

Every case requires exact target PID/process fingerprint, bounded timeout, post-condition identity checks, and rollback/cleanup.

| Case | Fault | Expected recovery | Critical assertions |
|---|---|---|---|
| F1 | UI/Electron process exit/restart | Recovery Host + primary/recovery planes survive; UI reconnect is independent | no duplicate authority; primary/recovery listeners remain coherent |
| F2 | Recovery Host owned PID exit | installed Supervisor restores exact fixed `--recovery-host` | new host PID/instance; no foreign adoption; existing healthy subordinate ownership preserved/proof-gated |
| F3 | Recovery MCP owned PID exit | Recovery Host restores Recovery MCP | new Recovery MCP PID; expected port/device identity; no duplicate listener |
| F4 | Recovery Tunnel owned PID exit | Recovery Host restores Recovery Tunnel | new Tunnel PID; Recovery MCP preserved; health endpoint returns |
| F5 | primary MCP owned PID exit | Recovery Host restores primary MCP per policy | same workspace/device identity; healthy primary Tunnel preserved unless policy explicitly requires otherwise |
| F6 | primary Tunnel owned PID exit | restore only primary Tunnel | primary MCP PID preserved; new Tunnel PID; healthy port |
| F7 | stale lock/ownership fixture | stale lock safely reclaimed only with proof | no foreign kill/adoption; single owner after recovery |
| F8 | live-but-unhealthy/hung owner fixture | fail closed before any replacement | no premature kill; no duplicate process/listener; typed blocked-live-owner evidence |
| F9 | repeated Recovery Host crash | bounded backoff/suppression | no crash loop; restart limit/window/suppression respected |

Additional immutable guard cases already covered by packaged/focused tests remain required in the RC suite:

- executable/manifest hash mismatch -> fail closed, no arbitrary spawn;
- handoff failure -> one owner/lock, terminal activation state, no orphan/duplicate listener.

True reboot/logon persistence is tracked separately as the P0.2/P1 external persistence acceptance boundary when it cannot be safely verified in-session.

Post-case invariant: no active orphan/overlap/stale EOCL run, no duplicate listeners on primary/recovery MCP and health ports, and all owned state identities are coherent.

## 8. P1.1 — Exact-fingerprint release candidate

Run once after P0 source changes stop:

- `git diff --check`
- `npm test`
- full Coding MCP pytest with terminal summary preserved
- `npm run test:recovery:e2e`
- `npm run test:recovery:packaged`
- `npm run canary:opencode-flash:preflight`
- `npm audit --omit=dev`
- final `npm run dist` after all source is frozen
- installer/resource/provenance verification
- controlled live activation/instance verification for any runtime-affecting source delta
- orchestration audit: no active/overlap/orphan/stale/fence residue.

Record exact HEAD, worktree/source fingerprint, package version, installer SHA-256, test counts, skipped tests, and any accepted external blocker.

`npm run test:recovery:packaged` may regenerate/clean `dist/`; therefore the final NSIS artifact used for release-candidate identity must be built after the source/test surface is frozen.

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

If the current ledger does not contain sufficient comparable representative pairs or controller cost is unobserved, record `KEEP_DETERMINISTIC / NO_PROMOTION` as the accepted gate result instead of manufacturing evidence.

## 10. P1.3 — Selective routing promotion

- Query runtime promotion readiness by task class.
- Promote only explicitly supported task classes with sufficient accepted representative pairs and quality/cost/time advantage.
- Keep other classes deterministic.
- Never auto-promote `sol_max`/`sol_ultra`.
- Auto-handoff remains independently gated even if a routing class is promoted.

If no class qualifies, record `KEEP_DETERMINISTIC` as the accepted result; that is a successful evidence-based decision, not an incomplete implementation.

## 11. P2.1 — Semantic localization optimization

Current runtime status: `NATIVE_LSP_BINDING_NOT_CONFIGURED`.

Current binding report indicates missing origin and credential-file configuration. Do not invent credentials or expose secrets.

Evaluate before implementing:

1. identify the exact provider/binding configuration required by the current runtime;
2. if the required external configuration exists, run a bounded benchmark comparing semantic-first localization vs bounded text fallback on representative repository queries;
3. measure latency, tool hops, result quality/recall, memory/process pressure, and operational fragility;
4. enable/configure only if benefit is material and does not reopen the closed P2/P3 memory/resource risk;
5. if binding configuration is absent externally, record the exact `BLOCKED_CONFIG` boundary;
6. if configured but benefit is not material, record `KEEP_TEXT_FALLBACK` and leave the correctness path unchanged.

## 12. Progress log

### 2026-08-17 — Plan initialized

- Baseline HEAD: `3059b218989fda8ebf217d121cd6e8f74a71587d`.
- Maintained docs confirmed packaged Recovery existed but installed persistence proof remained a release boundary.
- `execution_route=auto` intentionally remained deterministic pending representative paired evidence.
- Native semantic localization reported `NATIVE_LSP_BINDING_NOT_CONFIGURED`.

### 2026-08-17 — P0.1 complete and delivered

- Runtime-only host-correlation + SQLite sidecar Git hygiene closed.
- Canonical `ledger.sqlite3` tracking proven intact.
- Source-root cleanliness PASS.
- EOCL final acceptance `CHECKPOINTED`.
- Delivered: `bae11481 chore: close runtime evidence hygiene`.

### 2026-08-17 — P0.2 first installed attempt found packaging blocker

- Exact NSIS installer from `bae11481` built and installed to a controlled per-user target.
- Real Scheduled Task registration succeeded structurally but runtime `Action Once` failed.
- Root cause proven: packaged Recovery Supervisor bytes were stale versus source, so the Unicode-path handling fix was absent from installer.
- Scheduled Task rollback PASS; no persistent project/runtime evidence deleted.

### 2026-08-17 — Packaging exact-source remediation delivered

- Clean-dist prepackage boundary added.
- Full allowed `resources/` byte-identity afterPack gate added.
- Packaged Recovery smoke gained source hash guard.
- 13/13 focused tests PASS.
- Full exact-source identity PASS for 249 files.
- Full packaged Recovery smoke PASS after terminal Electron Builder run.
- Delivered: `d5d4bbb5 fix: enforce exact-source packaged resources`.

### 2026-08-17 — Fresh `d5d4bbb5` NSIS build accepted

- EOCL run `3ca4f890a8ae4090ac9858c0b0e68d46`, wave `16b3281053d24c32941153b9ab1fc428` -> `CHECKPOINTED`.
- `npm run dist` exit `0`.
- Installer size `128670087` bytes.
- Installer SHA-256 `A81AAB1C1399F4E8D57E090CBA25E5B6A939EDE2F9EB60E9C2C8A8E10C723AE2`.
- Packaged supervisor exactly matched source hash `540730E4...`.

### 2026-08-17 — P0.2 second installed attempt found persisted-state blocker

- Fresh exact-source package installed successfully to `%LOCALAPPDATA%\WebMcpAcceptance-0.3.4`.
- Installed supervisor hash matched package/source exactly.
- Real Scheduled Task structure/principal/triggers/manifest were correct.
- Task runtime returned `LastTaskResult=1`.
- Direct installed `Action Once` proved exact failure: missing `last_healthy_at` on sparse persisted `uninstalled` status under StrictMode.
- Scheduled Task rollback PASS; supervisor install root removed; persisted state returned to `uninstalled`.

### 2026-08-17 — Sparse persisted-state remediation source accepted

- `New-State` now normalizes only missing optional persisted fields to safe defaults.
- Existing fail-closed casts, ownership checks, thresholds, manifest identity, mutex and restart policy remain unchanged.
- Exact sparse-uninstalled regression added.
- Focused Recovery Supervisor test: **12/12 PASS**.
- Scoped diff hygiene: PASS.
- Remediated source SHA-256: `E0B906C1EC9AB5C3E9F1F52BA7B3D05F6FEFE42259F15A48AB3077A730076420`.
- EOCL run `274bd626bfb44943afedb3e755002ad0`, wave `62183559c12943ec8e9a9dec25c4f257` -> `CHECKPOINTED`.
- Delivered as `acaa3582 fix: normalize recovery supervisor persisted state`; `origin/main` aligned before the final P0.2 installer build.

### 2026-08-17 — P0.2 current-session installed acceptance complete

- Fresh exact-HEAD installer from `acaa3582`: `128670108` bytes, SHA-256 `0371F160B33621556F16F537297D60E5575690BE076BE053A5802E2A1532C879`.
- Packaged Supervisor exactly matched source SHA-256 `E0B906C1...`; exact packaged resource projection passed for 249 files.
- Real same-user Limited Scheduled Task reached continuous `healthy` on the existing Recovery Host.
- Installed `Action Once` observed PID `32536` / instance `399ea2ec2d751b606a2ffe7788727ac6` with no replacement; scheduled-loop resume returned healthy again.
- Product-native authenticated Recovery Host IPC + independent listener/Recovery checks proved primary/recovery planes coherent and fully ready.
- Mandatory Supervisor rollback PASS: task/root absent, status `uninstalled`, controlled acceptance app preserved, runtime remained healthy.
- Final accepted rollback proof: run `f64f9aac35d8459e903524953b3e0943`, wave `855626394161448fa5ea98ed60c61c62`, proof fingerprint `886ab2d4e0bbee7c89d62fb7124a979aae241f6cd849983193efa77899697d2f` -> `CHECKPOINTED`.
- True reboot/logon persistence remains an external/unverified acceptance boundary; no persistence PASS is inferred.

## 13. Next action

1. selectively deliver this accepted P0.2 evidence boundary with the living plan, canonical `ledger.sqlite3`, and relevant accepted reports while preserving unrelated concurrent work and excluding SQLite sidecars/runtime projections;
2. execute P0.3 F1-F9, reusing exact existing deterministic/E2E coverage where sufficient and using an isolated packaged real-process harness for destructive cases that could sever the active Coding MCP control plane;
3. update this file with per-case fault evidence, post-case ownership/listener/orphan invariants, and any minimal remediation required by a reproducible fault;
4. freeze source and execute the exact-fingerprint RC gate, rebuilding the final NSIS artifact only after the source/test surface is frozen;
5. evaluate representative routing evidence; if comparable accepted cohorts are insufficient or cost remains unknown, record `KEEP_DETERMINISTIC / NO_PROMOTION` rather than manufacture evidence;
6. close semantic localization as `BLOCKED_CONFIG` unless the required external origin + credential-file binding exists, and benchmark it only if that binding is actually available;
7. record the true reboot/logon persistence boundary as external/unverified unless it is independently executed and observed;
8. make the final selective delivery commit/push including the canonical ledger and accepted closure reports; do not create a release/tag/publish artifact without separate authorization.
