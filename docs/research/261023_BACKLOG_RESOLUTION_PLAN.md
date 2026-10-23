# Backlog Resolution Plan — Codex-web (2026-10-23)

Verified against the five 22/10 research documents, GitHub, the Ubuntu
Control Plane and the live Windows runtime on 2026-10-23. Status words are
used strictly: DONE means evidence exists at the cited place; OPEN means
real work remains; DEFERRED means the governing document itself gates the
item behind evidence that does not exist yet.

## Closed since the last review (not backlog)

- Parity M0–M5 implementation and advisory waves 1–4: DONE (GitHub `main`
  `15bdbbc6`).
- Control Plane reconciliation blocker `act_81e2…`: DONE, settled centrally.
- GUI E2E on packaged r18: DONE — operator acceptance 2026-10-23 13:34 +07;
  exact release binding recorded in `261023_R18_RELEASE_ACCEPTANCE.md`.
- svhome `codex-autopull` and CP healthcheck services: DONE (repaired and
  re-run green, 2026-10-23 12:44 +07).
- GitHub issues "#15 / #16" cited by the review: NOT FOUND. The repository
  has zero issues (GitHub API, state=all, checked 2026-10-23). The citation
  appears to reference another tracker or is stale; no action is planned
  unless the operator identifies the real tracker.

## P0 — done in this wave

1. **Exact release acceptance.** One record binding HEAD ↔ package ↔
   installation ↔ epoch ↔ component revisions ↔ test logs ↔ runtime
   snapshots ↔ operator acceptance: `261023_R18_RELEASE_ACCEPTANCE.md`.

## Status updates (2026-10-23, full-authority execution)

- **P1.3 CI — in progress, and the premise corrected.** The repository
  already has a CI workflow; it is `workflow_dispatch`-only by design
  (zero Actions minutes during ordinary development), which is why HEAD
  showed 0 check runs. The workflow was dispatched manually on 2026-10-23
  (run `39918780739`, HEAD `89a164c0`): the ubuntu job failed at the MCP
  test step with exactly 6 failures (1244 passed). Root causes, all in
  test code: a stale tool-contract golden hash (left behind by the wave-3
  schema change), four Windows-only simulations that cannot run on a
  POSIX host, and one case patching the optional `psutil` dependency that
  CI does not install. Fixed in commit `e92fd98f` and re-dispatched
  (2026-10-23 15:07 +07); the re-run's conclusion is recorded when it
  finishes. The standing trigger policy is unchanged.
  **Second and third layers (same day).** The re-run moved past the MCP
  step and failed later: the control-plane suite had 22 failures — 18
  node-E2E fixtures that resolve the electron executable from the root
  `node_modules` the ubuntu job never installed, 3 facade tests still
  asserting the pre-feedback JSON-RPC error envelope for tool refusals
  (the shipped contract returns complete `isError` results with the code
  in `structuredContent`; verified side-effect-free), and 1 tarfile
  extraction missing the filter Python 3.12 requires under `-W error`.
  The Windows job failed at checkout itself: archived `.coding-tools`
  report paths exceed MAX_PATH on the runner. Fixes: `c7de5872` (facade
  assertions + tarfile filter; full control-plane suite 505 tests OK
  locally) and `7e6ffd44` (workflow: `npm ci` before the control-plane
  step; `core.longpaths` before Windows checkout). Re-dispatched
  2026-10-23 15:36 +07 at HEAD `7e6ffd44`.
  **Fourth layer (run `39925799723`, completed FAILURE — correction:
  this run's conclusion was initially misreported in chat as still
  running; it had finished).** Both jobs advanced: ubuntu passed MCP,
  control-plane and frontend, then failed at "Verify workspace
  boundaries" — the checker scanned an archived verbatim upstream
  snapshot under `.coding-tools/reports/` and flagged its Rust `#[path]`
  lines. Windows passed checkout and failed at the MCP step with 8
  failures sharing one root family: the runner TEMP uses the Windows
  8.3 short form (`RUNNER~1`) while resolved paths use the long form,
  and several comparisons mixed the two (bridge workspace containment,
  runtime-activity projection, artifact relativization, a test's
  path-equality fault injection), plus one test denied earlier than
  expected because the runner host is elevated. Fixes in `61d50d0a`:
  canonical (realpath) comparison in `codex_bridge._norm_path`,
  `runtime_activity`, and `build_verify.collect_artifacts`; a
  canonical-path comparison in the restart-ticket test; an
  elevation-aware expectation in the attested-bridge test; and the
  boundary checker now prunes the `.coding-tools/reports` evidence
  subtree (self-test extended). Verified before dispatch: boundary
  self-tests pass, repo scan clean, affected suites green on the VM
  (125 passed) and on Windows non-elevated (129 passed). Re-dispatched
  2026-10-23 16:52 +07 as run `39935048641` at HEAD `61d50d0a`.
- **P1.4 Rollback drill — DONE 2026-10-23.** r18 → r17 → r18, both legs
  READY/OPEN with `fully_ready=true`; recorded as Addendum 2 of the r18
  release acceptance file. (This renumbers the drill from item 3 above.)
- **P1.2 Goal continuation — machinery verified, live natural proof still
  NOT_RUN by the plan's own gate.** The continuation suites pass on
  Windows (36 tests + 8 subtests: consent HTTP, codex bridge, continuity
  telemetry). The live ledger holds exactly one continuation run — a
  canary fixture case (`case-g2-clamp-001`) with a chatweb consent
  receipt, bounded grant (6 turns / 600s / 2 patch attempts) and one
  patch effect `applied` with pre/post image hashes. No natural-problem
  continuation exists yet; per B6, that proof requires a real Goal from
  the operator's provider session and is recorded as NOT_RUN, gate open,
  rather than claimed.
- **CI layers 5–7 (2026-10-23 evening).** Run `39936946988` reached the
  formatting step and exposed two residuals: one pre-existing rustfmt
  deviation, and the attested-bridge test hitting a second designed
  denial because runner posture varies by allocation. Fixed in
  `d5f0bec6`. Run `39939097645` then cleared every earlier stage in
  both jobs and failed at the deepest layers: the Rust suite with 19
  failures (18 sharing one root — see below — plus a Cloudflare
  tunnel log race) and the Windows MCP step with one failure (the
  attested half of the bridge test proceeded into a designed elevated
  denial). The 18-failure root was a half-landed local change
  (`1db8ea4e`, 2026-08-23) that hid `start_coding_task` from the
  registry and MCP discovery and adjusted three MCP assertions,
  without updating the registered-contract suite; the repository's own
  schema gate documents the hidden set as fixed and deliberate, so
  the registered contract was restored (`13fff493`: visibility,
  registry spec, discovery groups, audit intent, the three assertions
  reverted, the tunnel reader-flush race fixed, and the bridge test
  gated on host posture itself). Run `39949261296` at `13fff493`:
  Ubuntu 2310 passed with exactly one failure left (below); Windows
  attempt 1 hit four stateless-HTTP timeouts on a slow runner
  allocation (suite 719s vs ~540–670s typical) — a rerun of the failed
  jobs turned the MCP step green, confirming environmental flake —
  and the rerun then failed at `audit:prod` because a new advisory
  (GHSA-2883-xcg3-v3hh) had been published against the locked js-yaml
  4.1 (fixed by a lockfile-only bump to 4.2, `d84e15e1`).
- **The last Rust failure — root-caused and fixed (`35c84bd4`).**
  `partial_agent_job_logs_null_complete_validation_counts_everywhere`
  failed on the job_LOG assertion, not job_status: the agent job_log
  path derived the validation `truncated` flag solely from the
  unbounded analysis stream, so a 200-line page of a 601-line log
  claimed complete validation counts. The status path (bounded fetch
  + incompleteness check) and the local job_log path (tail-bounded
  analysis) both treat a bounded view as partial; the agent job_log
  path now ORs the page projections' truncated flags in. Module
  35/35, job clusters 171/171 locally. Fresh full run `39955938797`
  at `d84e15e1` dispatched 2026-10-23 19:47 +07.
- **P1.2 update — natural Goal E2E now demonstrated with a real
  provider.** A Codex provider went live on the Windows node
  (Codex CLI + the pre-existing account auth), and a fresh
  non-fixture problem was driven end-to-end unattended: the provider
  authored the PATCH proposal through the production bridge (locked
  `continuation_proposal` profile), the production parser validated
  it, the effect applied inside scope, and the protected oracle
  passed 8/8 (baseline 3 failed / 5 passed) → ACCEPTING. Full record:
  `261023_NATURAL_GOAL_E2E_PILOT.md`. Two items remain operator acts
  by design: the attested ChatWeb grant (consent was bound at the
  ledger layer, as in the product's own tests) and the B7 final
  outcome confirmation.
- **Quantitative Problem→Outcome evaluation — DONE 2026-10-23.**
  `261023_PROBLEM_OUTCOME_QUANTITATIVE_EVALUATION.md`: lineage
  mechanics measured sound (exact-revision binding 91.5%,
  criterion→proof 34/34, zero false closures); effectiveness
  formally rejected by the pre-registered cohort gate (3/10
  typed-natural eligible — the blocker is missing typed natural
  provenance on organic runs; cost/token coverage 0%).

## P1 — next, in order

2. **Bounded background Goal continuation proof** (Outcome roadmap M2;
   plan `SINGLE_GOAL_BACKGROUND_CONTINUATION_PLAN.md` B0–B7).
   Protocol: one real Goal with a recoverable failing step, started in the
   packaged app; the initial chat turn ends; the system must dispatch the
   next action itself. Pass criteria (from the roadmap): no duplicate
   mutation on lost/duplicate responses; STOP/revoke/expiry wins over
   continuation; budget is not reset by continuation; without an outcome
   receipt the result is recorded as PROVISIONAL, not accepted.
   Owner: operator (starts the Goal) + Muse (ledger observation and
   evidence record). Needs one joint session.
3. **CI check runs.** GitHub currently shows 0 check runs for HEAD.
   Add one workflow running the Node work-hub suites and the Python
   local-mode suite on push. Constraint: the stored PAT cannot write
   `.github/workflows/*` (missing `workflow` scope), so the workflow commit
   must be pushed over git/SSH from svhome (route already proven on the
   attendance repository). Exit: a green check run attached to a real push. **Rollback drill.** r18 → r17 → r18 using the proven full-clean
   activation path, ending on r18 READY/OPEN with a snapshot record.
   Exit: both activations READY, record appended to the release file.
   Scheduled in a maintenance window chosen by the operator, because the
   drill restarts the live runtime twice.

## P2 — evidence-gated

5. **Natural Problem cases and effectiveness review** (Outcome M3–M4).
   Capture cases with the roadmap's fields (symptom, baseline, scope,
   acceptance criteria, independent oracle, falsifier, interventions,
   rework, time). The four advisory waves and the r18 E2E are retro-captured
   as the first cases. Exit: at ≥5 cases, a KEEP/MODIFY/REMOVE review per
   mechanism; no ROI claim before that sample exists. **Multi-node expansion** (Outcome M5). Current topology is one executor
   node (Windows) + Control Plane host (svhome). The roadmap gates this
   behind M1–M4 evidence of a bottleneck; DEFERRED by design until case
   data exists. **B01–B12 contract backlog** (parity assessment §8). Per the assessment's
   own decision (§14), these are candidates, not a build mandate.
   Coverage today: B02 (single-claim handoff) — implemented via capsule +
   steering states; B03/B10 (job input/reconciliation) — implemented via
   the CP exec journal + terminal-receipt settlement path; B07
   (source-bound review/acceptance) — implemented via the atomic Git guard
   and delivery ritual; B01/B04/B05/B06/B08/B09/B11/B12 — partial or open.
   Rule: build a gap only when a P2 case exposes it. **Electron-UI destructive approval channel** (user-presence attestation
   for destructive commands). The token mechanism proves challenge
   possession and binds redemption to command + workspace, and redemption
   now writes a durable approval receipt into the job record. A native
   in-app approval dialog is the remaining upgrade; it changes the
   operator's daily flow, so it waits for an explicit operator decision.
