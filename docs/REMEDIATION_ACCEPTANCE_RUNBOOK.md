# Targeted remediation and acceptance runbook

## Purpose and truth boundary

This runbook closes the findings in the current fork/upstream assessment in a
safe order. It is an operator checklist, not a release claim. Every status,
metric, runtime identity, and Git identity must be re-observed at the time of
the corresponding gate. Historical reports and a disk `HEAD` do not prove the
loaded runtime or a production result.

The maintained product boundary is the Windows Electron Execution Hub plus
Coding Tools MCP. The retained Rust WebCodex server/runner code is a subsystem;
an upstream Rust PR is not a reason to port it without a local need and a
compatible product boundary.

This file deliberately uses repository-relative paths. Do not replace them
with a machine-specific workspace path in a durable report.

## Completion contract

The program may be called complete only when every required row below has
fresh, recorded evidence. A passing source test is not a substitute for a
security revocation, a loaded-runtime identity, natural experiment evidence, or
an approved delivery.

| Gate | Current source/worktree disposition | Required final evidence | Must not be substituted with |
| --- | --- | --- | --- |
| P0 credential exposure | The tracked raw HTTP artefact `1786778360` is deleted from the current worktree; the repository scanner now detects high-signal raw credential captures. | Owning service has rotated/revoked every credential or session that might have appeared there; record only service, credential class, time, owner, and outcome. | A clean scanner result, deletion from current tip, or a statement that a credential is probably expired. |
| P0 Git history | No history rewrite has been requested or performed. | An explicit owner decision: retain history with completed revocation evidence, or authorize a coordinated rewrite and clone/branch recovery plan. | An ordinary cleanup commit. |
| P1 Windows Job persistence | Atomic persistence avoids Windows directory `sync_all` after rename while retaining file sync before replacement. | Focused Windows regression proof on the exact delivery source. | POSIX-only execution or a compile-only result. |
| P1 `work_on_project` portability | Test support uses Windows-compatible Git/shell/path handling. | Focused `work_on_project` proof on the exact delivery source. | A shell-specific happy path or a synthetic POSIX path. |
| #121/#122/#123 adaptation | Model discovery, caller-controlled bootstrap projection, and cursor-aware job observation are implemented in the current worktree. | Focused MCP, `work_on_project`, local/agent log, schema, and `observe_jobs` proofs on the exact delivery source. | Upstream merge status or an old local test result after source drift. |
| #118 targeted inventory | Deferred. | A measured model-visible inventory/context cost tied to a bounded lookup, with a defined caller and authorization-preserving acceptance test. | Aggregate response-byte telemetry. |
| #119 project inventory scale | Deferred. | A real Runner inventory above 64 projects or an observed admission/synchronization failure, plus a rollout/compatibility plan. | The existence of the source limit alone. |
| #120/#124 collaboration | Deferred as one dependency chain. The local product already has a coordination plane but not upstream's `complete_session_message` contract. | An authorized cross-session consumer, then an integrated #120-style atomic completion contract followed by stateless-provenance coverage. | A schema-only recorder field or source presence of a related upstream PR. |
| P4 predictive policy | Shadow collection is available; predictive promotion remains collecting. | Canonical reporter returns `EMPIRICALLY_COMPLETE` with validated signals from representative, natural work and required temporal/source/task-family holdouts. | Synthetic/benchmark rows, an aggregate repair rate, or descriptive correlation. |
| P5 causal experiment | Source is implemented and fail-closed; epochs and treatment remain off. | An explicit A0 then treatment lifecycle under approved manifest/runtime/authority, natural eligible work, quality oracle, ITT funnel integrity, and preregistered economics gates. | Framework tests, a nonempty synthetic funnel, or missing cost treated as zero. |

## Phase 0 — preserve the delivery boundary

1. Before any new mutation, capture root, branch, `HEAD`, source dirty state,
   relevant concurrent owners, and the canonical ledger observation time.
2. Do not reset, clean, rebase, stage, or commit other owners' work. In
   particular, retain `.coding-tools/**`, including
   `.coding-tools/orchestration/ledger.sqlite3`; only the two documented SQLite
   sidecars are transient exceptions.
3. Keep source proof separate from volatile runtime evidence. A dirty ledger
   does not invalidate a matching source proof, but it also does not prove a
   runtime is loaded from that source.
4. Before a delivery attempt, isolate the intended source changes from
   concurrent Electron, P5, and orchestration work. Do not stage the whole
   current worktree merely to make a local commit possible.

## Phase 1 — close the credential incident

This phase needs the security owner for the relevant credential providers. Do
not read, print, paste, or copy raw credential values while performing it.

### External-provider scope boundary

On 2026-08-23, the owner explicitly removed Cloudflare credentials, sessions,
and account resources from this repository task because they belong to other
projects. No Cloudflare token/session inspection, creation, roll, revocation,
logout, deployment, DNS, Worker, or account change is authorized by this
runbook or this delivery. The repository-local P0 work remains the current-tip
artifact removal, prevention guard, and content-free incident documentation;
it must not be represented as proof that any external Cloudflare credential
was rotated or revoked. The owner of those separate projects remains
responsible for their provider-side incident response.

### Local, content-free incident inventory

The historical artefact `1786778360` remains reachable from commit
`f64abe25a85e6abaa9fe9eeacd3665eb29a82515`, even though it is deleted from the
current worktree. A content-free classifier processed the blob without emitting
its contents and found 75 HTTP-frame markers plus these credential-bearing
header families:

| Credential/session class | Marker count |
| --- | ---: |
| `authorization` | 64 |
| `set-cookie` | 12 |
| `api-key` | 64 |

The counts are triage evidence only, not credential values or a provider
identification. Treat every credential or session represented by these three
families as potentially exposed until its owning service records a successful
rotation or revocation. GitHub Secret Scanning is currently disabled for the
private `origin` repository, so it cannot supply the provider identity or an
alert receipt for this incident. The current-tip scanner was also run directly
against this historical blob in content-free mode and returned only the
`raw_http_credential_dump` rule, proving that the new guard covers the actual
incident shape as well as its synthetic regression tests.

A second content-free provider classifier found only the `cloudflare` provider
label (12 markers). Local Wrangler authentication was verified as an OAuth
credential, and an in-memory equality check established that this *current*
OAuth credential is not present in the historical blob. Its scope is also
insufficient to verify or list user API tokens (`401` for token verification
and `403` for token listing). Do not revoke that current OAuth credential as a
substitute for the incident response.

Read-only Cloudflare Dashboard inventory then confirmed ten active personal API
tokens. Five have a dashboard-reported, parseable last-use time before the
2026-08-15 exposure commit and five have no displayed last-use value; none has
a displayed last-use time on or after that commit. All ten are scoped to
specific resources in the table. This narrows the immediate service-impact
assessment but does not prove that a token was never exposed, because the
capture can also contain API-key and session material and dashboard last-use
metadata is not a cryptographic match. The local repository has no tracked `CLOUDFLARE_API_TOKEN`,
`CF_API_*`, `TUNNEL_TOKEN`, `cloudflared` token, or Wrangler configuration
reference. Its `TunnelService` invokes the separately configured OpenAI MCP
Tunnel client, not `cloudflared`. Therefore the repository cannot identify
which of those ten external tokens (if any) backed the capture, and must not
revoke all of them blindly: they may serve workloads outside this repository.
Before a destructive token action, the owner must map each affected token to
its workload, provision and validate the narrowest replacement, update that
workload's secret/configuration path, and then explicitly confirm the final
roll/revoke action. If no safe mapping is possible, treat all ten active user
API tokens and active dashboard sessions from the exposure period as
candidates, schedule a coordinated replacement window, and record the
resulting service impact.

1. Inventory the affected credential/session *classes* from the original
   capture without exporting their values into a ticket, terminal output, chat,
   Git, or `.coding-tools`.
2. Rotate or revoke through each owning service. Verify the old credential
   cannot authenticate and that the replacement follows the intended secret
   store/configuration path.
3. Record an external, content-free incident receipt with owner, provider,
   credential class, action time, and revocation/rotation result.
4. Decide whether historical Git objects must be purged. This is a destructive
   maintenance operation and requires explicit authorization, a remote/branch
   communication plan, and recovery instructions for existing clones. It is
   never implied by deleting `1786778360` from the current tip. At the latest
   local audit, the path occurs in one historical commit, but that commit is
   reachable from `main`, multiple local preservation branches, and seven
   remote-tracking refs. A rewrite therefore requires a coordinated all-ref
   plan; it is not a one-branch force-push.
5. Run the current-tip guard only after the source changes are present:

   ```powershell
   npm.cmd run test:repository-secrets
   npm.cmd run check:repository-secrets
   ```

The guard is source proof only. It is insufficient until revocation evidence
from steps 1–3 exists.

## Phase 2 — freeze and deliver the source remediation

Run the smallest relevant checks after the exact delivery tree is frozen:

```powershell
cargo check -p webcodex
cargo test -p webcodex work_on_project -- --test-threads=1
cargo test -p webcodex observe_jobs -- --test-threads=1
cargo test -p webcodex local_job_log_ -- --test-threads=1
cargo test -p webcodex job_log_wait_ -- --test-threads=1
npm.cmd run test:repository-secrets
npm.cmd run check:repository-secrets
git diff --check
```

If source changes include Rust formatting, first run a scoped formatter check
on the modified Rust files. A failure in an unrelated dirty file is not a
reason to reformat that owner's work; record the exact path and keep the
delivery scope separated.

Only immediately before an explicitly authorized commit or push, execute the
repository evidence policy in this order:

```powershell
npm.cmd run stage:coding-tools-delivery
npm.cmd run check:coding-tools-delivery
npm.cmd run check:coding-tools-history
git diff --cached --check
```

Do not run the staging command early on a shared dirty worktree: it snapshots
and stages the mandatory evidence tree. No commit, push, package, release, or
deployment is authorized by this runbook alone.

## Phase 3 — controlled runtime activation

Source proof and a runtime claim are separate gates.

1. Obtain explicit authority for a controlled Electron/Coding MCP restart and
   name the exact development/production target. Do not infer authorization
   from a passing local test.
2. Recheck the exact code-bearing source commit, upstream identity, immutable
   runtime paths, and expected app/user-data identities before restart.
3. After restart, inspect the live runtime rather than disk alone. Record its
   loaded Git/source identity, runtime instance identity, exact eight-tool
   `smart-v3` contract, and health/reconciliation state.
4. If the loaded identity, tool contract, or configured product root differs,
   stop and reconcile; do not call a disk revision an activation success.
5. Run the narrow smoke appropriate to the changed behavior. This validates
   the current instance only; packaging, release, pilot, and production remain
   separately authorized gates.

## Phase 4 — natural P4 collection

P4 remains shadow-only until its own canonical reporter permits a stronger
claim.

1. Use only natural `feature` and `bugfix` work. Capture the shadow
   recommendation before the first write, and retain the real quality/outcome
   evidence that later arrives.
2. Never create tasks, replan rows, assignments, or oracles merely to make a
   funnel nonempty. Unknown outcomes remain unknown.
3. At a recorded observation time, run the reporters sequentially against the
   canonical ledger:

   ```powershell
   python resources/coding-tools-mcp/scripts/report_p2_rework_diagnosis.py --workspace .
   python resources/coding-tools-mcp/scripts/report_p4_readiness.py --workspace .
   npm.cmd run report:accepted-result-economics
   ```

4. Do not activate policy merely because the report is descriptive. P4 closes
   only when the reporter establishes predictive validity and all required
   holdouts, provenance, and coverage conditions pass.

## Phase 5 — P5-A0, then only a separately authorized treatment

Do not start this phase until the runtime owner provides explicit authority and
a real natural-workload window. The raw A0 seed must arrive only through the
external secret-delivery channel used by the controlled restart; it must never
appear in a command line, manifest, repository file, telemetry, or chat.

1. Re-establish a clean, upstream-matched code-bearing baseline and record the
   exact runtime/analyzer/environment identities. Check that no workspace write
   fence is active.
2. Use `prepare_a0` as a read-only manifest preparation check. It must prove
   the opaque seed-handle commitment and four-hour A0 horizon without opening
   an epoch.
3. An authorized operator may then open exactly the frozen A0 manifest. Both
   labels run the control protocol; treatment and automatic policy activation
   stay off.
4. Allow only natural eligible work. Validate the full durable funnel by arm
   and feature/bugfix stratum: assessed, eligible, enrolled, assigned,
   protocol-started, pre-write binding/first write, terminal outcome, immediate
   quality, and delayed follow-up/interference.
5. Use pause, close, or hard-stop on any source/runtime/analyzer drift,
   authority failure, completed-block mismatch, orphaned row, arm crossover,
   write-binding mismatch, or quality/oracle failure.
6. A treatment canary is a new authorization and a new registered manifest. It
   may start only after healthy A0 integrity plus its own preregistered quality,
   repair/replan, restricted-TTAR, resource-overhead, and available monetary
   cost noninferiority criteria. Missing monetary coverage remains unavailable,
   never zero.

## Required final acceptance record

The final operator report must state, for the exact accepted source/runtime
pair:

1. Git source identity, source-cleanliness scope, delivery-snapshot receipt,
   and canonical-ledger observation time.
2. Credential incident action receipt and the explicit Git-history decision.
3. Focused source proof results and any excluded unrelated failures.
4. Loaded runtime identity, contract identity, smoke result, and any remaining
   package/release/pilot/production gates.
5. P4 reporter status and evidence window; P5 manifest/epoch/funnel status,
   explicitly separating source implementation, A0 integrity, treatment
   feasibility, causal efficacy, and production promotion.
6. A clear `ACCEPTED`, `NOT_ACCEPTED`, or `BLOCKED` decision. `ACCEPTED`
   is allowed only if every row in the completion contract has its stated proof.
