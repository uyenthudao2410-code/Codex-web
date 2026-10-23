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
