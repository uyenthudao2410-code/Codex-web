# Current status recapture — `main@ca24c0b0`

**Observed:** 2026-09-23 12:15 +07
**Workspace:** `E:\DEV\Codex-web`
**Mode:** read-only status/recovery assessment; no restart, reboot, tunnel CRUD,
connector ACK, epoch quarantine, ledger write, or new RUN was performed.

This snapshot supplements the earlier dated research files. It does not rewrite
their historical measurements and does not promote a historical receipt into a
current live acceptance.

## 1. Git and delivery state

```text
branch                  = main
HEAD                    = ca24c0b0409a3573365ada5b1263210699bb7539
origin/main             = ca24c0b0409a3573365ada5b1263210699bb7539
divergence              = 0/0
source/test worktree    = clean
dirty evidence          = .coding-tools/orchestration/ledger.sqlite3 only
worktree mode           = direct main; no worktree
```

The current source and test packets are already delivered on `main`. The
canonical ledger remains dirty because it is live runtime evidence and must be
retained; it is not an unrelated source change and was not reset or edited.

## 2. Live runtime and connector

Fresh `npm run dev:status` returned:

```text
state                    = MISSING
host / installation      = available / current
pid / instance           = none / none
mode                     = development
running_revision         = none
mcp_revision_state       = stopped
components_ready         = false
fully_ready              = false
runtime_update_incomplete= true
runtime_telemetry        = available; signal_stale=false
connector_state          = UNAVAILABLE
connector_rediscovered   = false
connector_refresh        = false
connector_ack_pending    = false
error_code               = none
```

The cached Recovery Host/lifecycle observation is therefore not a usable
primary MCP/Tunnel session. `state=MISSING` is a fail-closed stopped-runtime
state, not evidence that the P1/P2 invariants have regressed.

Computer Use inventory currently has no supported app/browser surface and
reports `Codex auth token is unavailable`. Consequently there is no
current-process receipt for `tools/list`, `server/discover`, client
attestation, or a real `workspace_context` call. We must not substitute raw
HTTP, a stale receipt, a manual ACK, or a local health projection for that
proof.

## 3. Canonical ledger census

Read-only Backup-API census at `2026-09-23T05:12:10.686Z` (`12:12:10 +07`):

```text
schema_version                 = 12
integrity_check                = ok
foreign_key_check_rows         = 0
physical snapshot SHA-256      = 7c675c9518982f71d4521ecf8ac35a8ca14c42e4e5476b9fd8aa6d2ef0b68418
logical snapshot SHA-256       = 6f436257385c871f09e3e922b1a3aa2e2aae055c29eb92435397187d21d992fc
mutated_canonical_ledger       = false
projection                     = CONTEXTUAL_PROJECTIONS; drift=false
context_count                  = 1079
ordinary_active_runs           = 17 (all THRESHOLD_SENSITIVE_STALE_CANDIDATE)
p5_epochs                      = 6
unexplained / unbound / stale  = 0 / 0 / 0
goal_continuations             = 0
run_continuations              = 1 (belongs to another Problem)
```

The 17 active RUNs are retained as evidence and are not bulk-terminalized.
They do not provide write authority or justify reopening an old recovery
candidate.

## 4. Two Problems remain separate and OPEN

The current read-only query by exact `problem_id` and revision confirms:

| Problem | Revision / criteria | RUN history | Latest event | Outcome receipt | Authority |
|---|---:|---|---:|---:|---|
| `prl-22e670302757c9b7663170e226ed7c26` | rev1 / 12 | 47 accepted, 16 aborted, 3 active = 66 | 320 | 0 | `OPEN` |
| `prl-e918c7d33e70c2d304d0797e11b05fcb` | rev2 / 18 | 16 accepted, 10 aborted, 13 active = 39 | 316 | 0 | `OPEN` |

For both revisions, existing events are engineering-attempt/open/revision
history (the first also has user-feedback events), not criterion coverage or
closure. Accepted RUN counts are not a natural outcome and do not authorize
closing either Problem.

### `prl-22e…` rev1 — packaged/recovery/reboot acceptance

Already proven at source/focused level: P1 semantic stop refusal handling, P2
rollback startup-intent preservation, role-aware lifecycle readiness,
installation/process identity guards, development/packaged mutex isolation,
foreign-installation refusal, fallback read-only behavior, and packaged
Recovery Host smoke in its isolated historical snapshot.

Still missing: one controlled activation bound to the current installation and
epoch; current-process `tools/list`/`server/discover`; real
`workspace_context`; receipt binding PID/process instance/MCP server instance,
activation epoch and contract SHA; packaged cold-start/logon/reboot; startup
intent matrix; Machine B/right endpoint; host-only and central-route/Tunnel
fault matrix; runtime rollback/partial-effect proof; canonical natural-use
window; independent user outcome; exact C01–C12 coverage and closure authority.

### `prl-e918…` rev2 — durable Goal continuation

Source implementation and focused tests cover the durable provider bridge,
persistent App Server session, response-end worker observation, parent/child
continuation and budget, effect journal/backup, unknown-effect reconciliation,
restart/reconnect/rebind guards, exact controller/Problem/revision/epoch/source
binding, and fail-closed unknown dispatch outcomes.

Still missing: a natural Goal with provider/worker dispatch after response end,
no-manual-relay continuation, reconnect/restart, real unknown-effect fault
reconciliation, parent-budget continuity, controller delivery/ack, review and
progress semantics, an independent Goal outcome, exact BG01–BG14 coverage, and
closure authority. The ledger has no `goal_continuations` for this revision.

## 5. Current engineering/evidence ladder

```text
SOURCE_PRESENT             = PASS
FOCUSED_PROOF              = PASS (latest identity/recovery/lifecycle/UI packet: 198 passed)
DELIVERED_MAIN             = PASS (HEAD == origin/main)
PACKAGED_SMOKE             = PASS in an historical isolated snapshot only
CONTROLLED_ACTIVATION      = NOT PROVEN for current process
STRICT_REDISCOVERED        = NOT PROVEN
REAL_WORKSPACE_CONTEXT     = NOT PROVEN
REBOOT / MACHINE B         = NOT PROVEN
NATURAL C01–C12 OUTCOME    = NOT PROVEN
DURABLE BG01–BG14 OUTCOME  = NOT PROVEN
P4/P5 promotion/economics  = NOT PROVEN
Problem closure             = OPEN / no closure authority
```

The continuation/bridge focused suites also passed (`89 passed + 10
subtests`; provider restart/durable coordination `41 passed + 8 subtests`).
These are source/stub-provider proofs, not live provider or natural Goal
acceptance.

## 6. P4/P5 and measurement signals

Current read-only P4/P5 report:

```text
P4 state / empirical complete       = collecting / false
representative shadow tasks         = 100
raw repaired tasks                  = 20
causal-solution repair tasks        = 0
causal-solution unknown tasks       = 29
predictive targeting                = false
P5 baseline ready                   = true
P5 lifecycle                        = EPOCH_HARD_STOPPED
P5 experiment start                 = false
```

The accepted-result economics report still treats missing provider/controller
usage and monetary cost as **unknown**, not zero. The historical proof-cache
observation remains descriptive (`6/983` hits, about `0.6104%`); it is not a
promotion or a causal efficiency claim.

## 7. Decision and exact next action

The current blocker is classified as `WAITING_FOR_SUPPORTED_CONNECTOR`, not
`P1/P2_REGRESSION` and not `CONTROL_PLANE_IMPLEMENTATION_BUG`.

When a supported connector surface is available, execute exactly one gated
wave in this order:

1. Verify the exact installation, source/package revision and create a fresh
   activation epoch through the existing lifecycle authority.
2. Collect strict current-process `tools/list` and `server/discover` receipts
   bound to PID, process instance, MCP server instance, epoch and contract SHA.
3. Call a real `workspace_context` for `E:\DEV\Codex-web`; only a valid
   attestation may open admission.
4. For `prl-22e…`, run reboot/logon, startup-intent, Machine B and fault
   matrices, then canonical natural-use and independent outcome collection.
5. For `prl-e918…`, run one natural Goal through response-end dispatch,
   restart/reconnect, unknown-effect reconciliation, budget continuity and
   independent outcome.
6. Build exact C01–C12 and BG01–BG14 coverage manifests, then request closure
   authority. Do not create artificial RUNs, receipts or outcomes to fill a
   gap.

**Operator checkpoint:** this recapture changed no source, runtime, or ledger
state. The strongest current result is `SOURCE_PRESENT + FOCUSED_PROOF +
DELIVERED_MAIN + historical PACKAGED_SMOKE`; both Problems remain OPEN because
current connector, strict discovery, real workspace access, natural outcomes,
and closure receipts are absent.
