# Outcome Cases — Codex-web (retro-captured 2026-10-23)

Cases captured with the structure defined in
`261022_OUTCOME_DRIVEN_INTEGRATED_ASSESSMENT_AND_METHOD.md` §13. These five
are retro-captured from the verified work of 22–23/10/2026; the independent
oracle for cases 1–3 was the external review loop (its reports were checked
against primary sources before any fix was accepted). First
KEEP/MODIFY/REMOVE review is due once the operator schedules it; no
effectiveness claim is made from this sample yet.

## Case 1 — Control Plane action stuck in reconcile_required

```yaml
case_id: act_81e2ae42400f456bad538e98366ce02c
problem_revision: advisory-round-2 item 1
source_scope: Ubuntu Control Plane DB + Windows exec journal
symptom: CP action remained reconcile_required with a single unknown receipt; the auditor's writer lease (task_99e962f, gen 2) could not release (CONFLICT on later calls)
trigger: CP exec_command (node --test suites) rejected by the local MCP policy before spawn (PERMISSION_REQUIRED), so no terminal receipt was ever produced
hypotheses:
  - claim: the command partially executed on Windows
    discriminator: exec policy raises PERMISSION_REQUIRED before any spawn; the same suites run locally afterwards all exited 0
    evidence_status: refuted
  - claim: the journal receipt could be completed locally to a terminal state and the CP agent would submit it
    discriminator: CP record_receipt settles reconcile_required only via a terminal receipt for the same attempt, submitted by the device
    evidence_status: observed
root_cause: policy rejection pre-spawn left the action with an unknown receipt and no terminal outcome recorded anywhere
change_ref: Windows exec journal entry completed with a terminal rejected receipt + evidence payload (backup kept); CP agent submitted it itself
proof_refs: [CP receipts table — unknown 04:05:00Z + rejected 05:09:05Z, delivery_state=settled, lease unresolved count = 0]
technical_acceptance: accepted
activation: current
user_outcome: confirmed
recurrence_window: unobserved since 2026-10-23
lessons:
  - An unknown receipt is not evidence of execution; check the policy layer for a pre-spawn rejection before assuming partial effects.
  - The designed settlement path is a terminal receipt for the same attempt, never a state edit or a blind re-run.
authority_note: advisory_only
```

## Case 2 — Git commit guard and destructive confirmation weaker than claimed

```yaml
case_id: advisory-rounds-2-3-git-destructive
problem_revision: advisory-round-2 items 2-3, refined in round 3
source_scope: E:\DEV\Codex-web @ 75fc1998 → 15bdbbc6
symptom: commits could bypass the delivery ritual; expected_head was optional with no HEAD capture in the UI; destructive confirmation was a boolean the caller set itself; round 3 added — HEAD checked only before the ritual, and failure rollback lost prior staged content
trigger: external source review of workHubFiles.js and exec_tools.py against the claims made for them
hypotheses:
  - claim: adding the checks at entry is sufficient
    discriminator: a stage script that commits during the ritual (test) and a pre-staged file overwritten by the ritual (test)
    evidence_status: refuted — both races were real
root_cause: guard placement and rollback granularity were designed for the single-writer case
change_ref: commits cbbb326c, 1fe66446, c7adddfd (expected_head + UI capture + no-HEAD refusal; token-bound confirmation; atomic re-check + tree-level index rollback; redemption approval receipt in job metadata)
proof_refs: [node work-hub-files 19/19 on VM+Windows+svhome with preserved logs + sha256, python local-mode 8/8 on Windows, token flow re-verified against the shipped r18 python]
technical_acceptance: accepted
activation: current (packaged r18)
user_outcome: confirmed
recurrence_window: unobserved since 2026-10-23
lessons:
  - Verify a guard at the moment of the write it protects, not at the moment of the read that informed it.
  - Rollback must restore the pre-existing index tree, not just unstage the paths the failed attempt touched.
  - Precise guarantee wording matters: a challenge token proves possession and binding, not physical user presence.
authority_note: advisory_only
```

## Case 3 — svhome maintenance services silently red

```yaml
case_id: svhome-autopull-healthcheck-20261023
problem_revision: operator side observation during wave 3
source_scope: svhome systemd user services + ~/DEV/Codex-web checkout
symptom: codex-autopull failed on every run (git pull --ff-only impossible); CP healthcheck failed from 12:03 with "backup stale or not restorable"
trigger: the DEV checkout had diverged (one local commit + one dirty file, 44 behind); the 12:03 backup inspection counted 1 unquarantined unresolved action (case 1, settled 12:09)
hypotheses:
  - claim: the local commit f3168382 is unique work that must be merged
    discriminator: code-only diff vs origin/main — identical except one word's capitalization in a message
    evidence_status: refuted (an earlier draft of a fix that landed upstream refined)
  - claim: the backup itself was corrupt
    discriminator: backup Result=success, sqlite ok; the failing input was the unquarantined count in its inspection
    evidence_status: refuted
root_cause: an ff-only mirror checkout cannot carry local commits; the healthcheck inherits the reconciliation state of the newest backup snapshot
change_ref: backup branch backup/svhome-local-pre-reconcile-20261023 preserved; checkout reset to origin/main; dirty WIP stashed and restored; fresh backup taken after case 1 settled
proof_refs: [autopull Result=success on re-run, healthcheck PASS with package SHA match + sqlite ok]
technical_acceptance: accepted
activation: current
user_outcome: confirmed
recurrence_window: unobserved since 2026-10-23
lessons:
  - Mirror checkouts must stay pure mirrors; any local fix needs an upstream path the same day.
  - A healthcheck message names a symptom class, not the cause; read the inspection fields it actually evaluated.
authority_note: advisory_only
```

## Case 4 — Packaged activation blocked after a hard stop (census gate)

```yaml
case_id: r18-activation-census-gate-20261023
problem_revision: operator incident during the r18 acceptance commit
source_scope: packaged r18, DESKTOP-63643J4
symptom: after stopping the stack to commit a delivery snapshot, the reinstalled host resumed its committed epoch with the MCP running but unbound (update_incomplete); runtime.restart full-clean failed twice with CANONICAL_LEDGER_CENSUS_TIMEOUT
trigger: host resumed its own committed epoch after a hard kill; the unbound MCP held the ledger, and the census child needs the exclusive ledger gate (30s bound)
hypotheses:
  - claim: the ledger is corrupt or too large for the census
    discriminator: WAL checkpointed, size unchanged class (~101MB); the same census completed in ~14s earlier the same day
    evidence_status: refuted
  - claim: killing the unbound MCP lets the restart stop phase free the gate
    discriminator: restart accepted immediately after the MCP process was terminated; new epoch activation-mvkmy4ps reached READY/OPEN, fully_ready=true
    evidence_status: observed
root_cause: recovery cannot replace the MCP in place under a committed epoch, so the stop phase could not free the ledger gate the census requires
change_ref: operational procedure only (terminate MCP python, then runtime.restart full-clean); recorded in the r18 acceptance addendum
proof_refs: [snapshot 2026-10-23T07:16:46Z — epoch activation-mvkmy4ps READY/OPEN, mcp=true, fully_ready=true]
technical_acceptance: accepted
activation: current
user_outcome: confirmed
recurrence_window: unobserved since 2026-10-23
lessons:
  - A delivery snapshot commit requires a quiesced stack: the live app rewrites .coding-tools/performance.json continuously and the delivery check cannot pass against a moving tree.
  - When a full-clean census times out, check who holds the exclusive ledger gate before retrying the same call.
authority_note: advisory_only
```

## Case 5 — Packaged build could not take over from the dev stack

```yaml
case_id: m5-packaged-switch-20261023
problem_revision: parity assessment M5
source_scope: Windows packaged builds r15k–r18 + dev lifecycle
symptom: the packaged build installed but ran with MCP off and a foreign (dev) epoch; the UI restart button, the dev lifecycle handoff and checkpoint activation routes each failed for a different reason
trigger: ledger census blocks stopped-runtime activation while runs await acceptance (acceptance_pending), and the host descriptor file is shared — the last host to start owns it
hypotheses:
  - claim: the dev lifecycle idle handoff can move dev → packaged
    discriminator: observed behaviour — that handoff moves packaged → DEV, not the reverse
    evidence_status: refuted
  - claim: packaged Recovery Host IPC runtime.restart with full_clean_refresh + allowAcceptancePending performs the switch
    discriminator: used successfully for r15k, r16, r17, r18 activations, each reaching READY/OPEN
    evidence_status: observed
root_cause: activation is gated by the ledger census and by which host owns the shared descriptor; neither the UI button (under the wrong epoch) nor the dev lifecycle (wrong direction) addresses both
change_ref: operational procedure (install packaged supervisor → wait for the packaged host → IPC restart against the packaged descriptor with the acceptance-pending flag); accidental deletion of build r15j during cleanup was disclosed and rebuilt byte-identically as r15k
proof_refs: [per-build epoch records r15k mvkfmkaa, r16 mvkhq2en, r17 mvkjf06s, r18 mvkkj43q → mvkmy4ps, each with supervisor healthy + fully_ready snapshots]
technical_acceptance: accepted
activation: current
user_outcome: confirmed (GUI acceptance by the operator)
recurrence_window: unobserved since 2026-10-23
lessons:
  - Verify which host owns the shared descriptor before sending any activation call.
  - Never delete build directories by broad pattern while a switch is in flight.
authority_note: advisory_only
```
