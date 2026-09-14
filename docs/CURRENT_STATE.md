# Current Project State — Tools-Codex-web

> **Status date:** 2026-09-06
> **Desktop package:** `coding-tools-mcp 1.0.0`
> **Purpose:** canonical operational snapshot for the current repository. This is not a release note and does not imply that every source change has been activated, packaged, or released.

## 0. Current convergence guidance — 2026-09-04

The current engineering strategy is **convergence, not architecture expansion**. Do not build more system merely because a historical plan contains another layer or because an evidence gate is still open. Existing implementation should be closed by exact provenance, a real end-to-end Problem continuity observation, natural evidence, and accepted-result economics before another framework or control plane is authorized.

Use the following evidence ladder. Each row is a distinct claim and a stronger row must never be inferred from a weaker one:

| Evidence state | What it proves |
|---|---|
| `SOURCE_PRESENT` | Exact bytes exist in the current checkout. This is not proof, acceptance, or runtime evidence. |
| `FOCUSED_PROOF` | A bounded oracle passed for those exact bytes. This is still not final acceptance or live activation. |
| `EOCL_ACCEPTED` | The semantic controller accepted exact receipts at a stable checkpoint. This is not proof that a process loaded them. |
| `LIVE_COMPATIBLE` | A current development process/revision is live under the compatible activation path, for example `CURRENT_COMPATIBLE_ACKNOWLEDGED`. This is process-bound local evidence and is **not** strict connector rediscovery. |
| `STRICT_REDISCOVERED` | An official current-process discovery receipt (`tools/list` or `server/discover`) exists and is acknowledged under the strict path. Compatible bootstrap/current access must never be relabeled as this state. |
| `PACKAGED_RELEASED` | Required package/installer/release evidence has passed. Local source, EOCL, or live-development evidence does not imply this state, deployment, production, or SLO proof. |
| `NATURAL_PROBLEM_OUTCOME` | A real natural Problem Revision preserves exact RUN/WAVE continuity and ends in independent outcome confirmation or a truthful same-revision reopen. Accepted execution alone is not this outcome. |
| `ECONOMICS_POLICY` | Representative natural evidence has enough measured accepted-result economics to justify a policy decision. Missing usage, money, outcome, or coverage stays unknown rather than zero. |

The convergence sequence is intentionally finite:

1. converge the implementation and exact provenance already present; do not add another system layer;
2. prove continuity on **one real natural Problem** from Problem Revision through exact RUN/WAVE/checkpoint to independent outcome or truthful reopen;
3. gather **5-10 natural Problems** with the same provenance discipline instead of synthetic filler;
4. measure accepted-result economics, coverage, rework, TTAR/TTPR and operator burden without converting missing evidence to zero;
5. only then decide whether EGRI/P5 should advance, remain gated, or be simplified;
6. classify the surviving surface explicitly as **KEEP / MODIFY / REMOVE**.

`KEEP` means retain a mechanism with unique authority/value and current evidence. `MODIFY` means correct a demonstrated defect or evidence gap using the smallest existing surface. `REMOVE` means delete or collapse redundant policy/framework surface only after its authority/evidence role is demonstrably unnecessary; never erase durable evidence or rewrite dated research chronology to make the present look cleaner.

This section is the current sequencing and provenance authority for this maintained document. Older dated runtime paragraphs below remain immutable observation snapshots. If a historical block says `current`, `update_pending`, `connector blocked`, `source-only`, or names a process/epoch, read that language in the timestamped observation window unless a fresh supported runtime receipt re-establishes it. A present-day `CURRENT`/`fully_ready` local observation is still only local runtime evidence; compatible current access is not strict rediscovery, and neither is a package/release/production claim.

### Current 1.0 engineering/release-candidate receipt — 2026-09-06

The local Windows 1.0 engineering candidate is closed through source, full
Python proof, an exact-current NSIS build, packaged and installed Recovery
smoke, and a sufficient fresh UI performance window. This is a local
release-candidate claim only: no tag, GitHub release, publication, deployment,
production claim, independent new-machine run, or upgrade from a historically
published installer is implied.

- `npm run test:mcp` completed with `936 passed, 5 skipped` in `371.66s`
  (exit `0`). The earlier 300-second timeout was a proof-window limitation, not
  a retained Python failure.
- The current-source Node release lane completed with `714` tests passed plus
  source-root and tracked-secret guards passed. One Windows temporary-tree
  cleanup produced `EPERM`; its exact focused retry passed `4/4`. The final
  `npx electron-builder --win nsis` node then completed with exit `0` and
  produced `dist/coding-tools-mcp-setup-1.0.0.exe`. The exact installer used
  for the final local smoke was `121,636,941` bytes with SHA-256
  `20f740bac29522d634bbfc4708040538f0cab8528d907e03ac46b7dd47f8af0c`;
  its blockmap SHA-256 was
  `d0d8a0348eace3969715e11da79a856c8e576c8c7b881e314dc88fa375ba104b`.
- The final packaged smoke proved byte-exact allowed resources, only `en-US`
  and `vi` locales, `smart-v3` with exactly eight public tools, Recovery Host
  and independent Recovery MCP readiness, supervisor health, live-owner and
  executable-hash fail-closed behavior, no Scheduled Task mutation, and an
  unchanged production Recovery descriptor.
- `node scripts/installed-recovery-smoke.js` then installed the exact NSIS
  candidate silently into an isolated temporary path, verified its registered
  installation and the same packaged Recovery/contract surface, uninstalled it
  with exit `0`, removed installed files and registration, and proved that the
  production Recovery descriptor and existing Recovery Supervisor Scheduled
  Task definition did not change. This is same-machine isolated-install proof,
  not an independent new-machine receipt.
- The release-harness source was accepted by Coding-VP at checkpoint
  `e5673e0ded354257a7c3309dfc1691b0` and corrected after lifecycle postflight at
  checkpoint `84b65096ab0c4a4e98bcf07362f94540`. The correction removed an unnecessary
  `package.json` alias that made the Electron revision appear stale without an
  activatable component; the direct installed-smoke command remains the
  supported test entry point. Current `npm run dev:status` again reports equal
  Electron running/disk revisions, `CURRENT`, `fully_ready=true`, and
  `CURRENT_COMPATIBLE_ACKNOWLEDGED`. Compatible bootstrap remains distinct from
  strict connector rediscovery.
- A fresh Electron UI instance collected 20 renderer, 40 main-process, and 445
  event-loop samples. Readiness is `pass`: event-loop p95 `15.5ms`, normal IPC
  p95 `85.1ms`, snapshot-apply p95 `0.1ms`, and dashboard-refresh p95 `110.6ms`.
  The older long-lived window's insufficient/stale sample set is superseded for
  this local candidate, not rewritten.
- A query-only canonical lifecycle census reports zero managed jobs, zero
  unexplained active RUNs, zero awaiting-acceptance RUNs, and no projection
  drift. Thirty-three inactive RUNs remain below the 86,400-second stale
  threshold and are therefore not eligible for forced reconciliation. Six P5
  experiment anchors remain retained historical evidence.
- The two `260905_*` research/checkpoint documents referenced below were
  restored byte-for-byte from their verified retained Git object. They remain
  dated chronology and do not override this maintained current receipt.

Natural Problem continuity/outcome, representative accepted-result economics,
automatic non-deterministic routing promotion, strict connector rediscovery,
an independent new-machine run, and publication/deployment remain separate
evidence gates. They are not blockers to this bounded local engineering
release-candidate closure and must not be reported as completed without their
own real evidence.

### Baseline correction source checkpoint — 2026-09-05

The implementation follow-up to the [05 September finish-line assessment](research/260905_COMPREHENSIVE_PROJECT_ASSESSMENT_AND_FINISH_LINE.md)
is tracked in the [source/test checkpoint](research/260905_FINISH_LINE_IMPLEMENTATION_CHECKPOINT.md).
The user-approved closure decision on 06 September is recorded in checkpoint
section 20: finish M1 engineering convergence separately from empirical M2/M3,
upstream accounting and destination-specific delivery. Freeze source/features
and these progress documents during the proof → acceptance → controlled activation
batch. Compare accepted bytes once, close only demonstrated gaps in a combined
integration scope, classify/reconcile eligible control debt through supported
authority, and obtain exact live-current proof. Sections 21–22 supersede the early
20.5–20.6 observations: the product 1.0.0 normalization is present in the existing
version RUN. Node, Python and Rust commands are terminal exit 0, but consolidated
exact-byte acceptance is still open. Python's retained task projection records
930 passed, 5 skipped and 218 subtests; skips are not passes. The audited build
verification has build_result=null and an existing older artifact inventory, so
a fresh package build is not proven. Of 40 accepted receipt paths rehashed, 38
still match and two have the requested version/policy drift. Section 22 records
successful public exact-run context recovery: task_control get with the exact
RUN and no supplied context returned its persisted owner handle, bound to the
correct task/RUN/WAVE. Continue with that returned handle; no manual handoff or
new RUN is required. Do not create a parallel writer or repeat completed broad
commands to work around a missing canonical proof record.
The latest advice retains mandatory .coding-tools evidence in Git; migration or
untracking is not part of M1. Keep product-source cleanliness separate from
allowed evidence mutations. This does not waive acceptance
guards or authorize rerouting a denied oracle. Do not
hold M1 open merely for natural-cohort counts, upstream billing or rendered 900px
proof, and do not report any of those deferred claims as completed.
That checkpoint's sections 9 and 12 record exact two-file dashboard and parser
EOCL acceptance, respectively. Section 12 corrects the earlier unverified client
block diagnosis and records successful current-context reads and revalidation
after documentation-only worktree drift. Section 13 records exact-file acceptance
of the Recovery Host and release runbooks, including the corrected strict versus
attested compatibility ACK guidance. That document acceptance is not runtime
proof; the independent Python metadata proof attempt stopped at the server's
inline-script permission gate without a grant or accepted proof.
Section 14 adds exact producer-measurement and three-file command-core acceptance.
Section 15 separately closes exact two-file `live_control.py`/endpoint acceptance
and its report ACK, backed by four focused temporary HTTP tests and four subtests.
This current successful request does not erase the unverified historical refusal
or clear the separate metadata permission gate. The latest recorded development
check after the producer change reports Coding MCP `update_pending`; source and
HTTP-harness acceptance are not loaded-revision or live-user journal proof.
Section 16 closes the initial donut placeholder correction and its focused Node
proof/ACK without reaccepting the dashboard core. The six hard-coded model rings
are absent before the first snapshot. This does not accept the entire Electron
integration. Section 17 closes the three-file responsive correction and static
regressions: narrow KPI cards use the existing breakpoint, inner metadata no longer
inherits outer-card sizing, and narrow split panels/tool rows remain reachable.
Section 18 closes exact 16-file font/distributor-identity and renderer-revision
adoption, focused proof and final report ACK. Historical distributor byte checks
remain dated evidence, not a fresh font fetch or legal/rendering/installer proof.
No rendered 900px/CSS-engine proof has been obtained; the browser URL-policy denial
remains respected. Section 19 closes the exact main/preload window/bridge packet
with focused source/VM proof and report ACK, without a live-window claim. Metadata
official proof, consolidated provenance/control hygiene and accepted-to-loaded
still have independent gates. Direct version-literal alignment review is not
installed-distribution or executed runtime parity proof.
Section 19.4 verifies that public `task_control audit` with `run_id` and without
`wave_id`/`after_seq` exposes canonical checkpoint `metadata.accepted_files`;
the wave-filtered projection omits those aggregate fields. Audit regenerates the
target RUN reports, so it is not strictly read-only. This supported receipt source
enables baseline comparison; one audited RUN is not whole-baseline/G1 closure.
No-write adoption still requires exact passed proof; source review or verification
`none` is not an exemption for the unresolved metadata acceptance.
The latest recorded development check (2026-09-05T16:26:27.742Z) reports Electron
`STALE` and MCP `update_pending` with fresh telemetry; no activation occurred in
these waves. All further progress belongs in the existing checkpoint, not a new
progress or handoff report; sections 18.4 and 19.3–19.4 distinguish the remaining gates.
An explicit null/undefined performance pulse now clears the previous dashboard
trace and reports unavailable data; an omitted field preserves the existing
trace and a measured zero remains observed. The Codex-web product version is
`1.0.0` across the Electron package and Python MCP package/runtime metadata.
Protocol, schema, tool-contract, and data-format versions remain independent
compatibility identities.
The release checklist now uses `npm start`/`npm run dev` for start/focus and
`npm run dev:refresh` for full refresh, with explicit Python proof when a release
candidate changes MCP behavior.

For EOCL-scoped commands, `task_control(get)`, `task_state_get`, and live control
now derive command presentation from an exact checkout-local managed Job with
matching command/RUN/WAVE identity. A verified terminal Job clears the presented
active command and supplies `current_command_observation`; missing or conflicting
identity stays unknown without disclosing another Job's result. This does not
write task-state, append completion events, or synthesize proof/results. Raw
persisted projection and `CHECKPOINTED` authority remain intact; ordinary
commands without EOCL ownership keep their existing behavior. Focused source
proof is recorded in the linked checkpoint; no loaded-runtime claim is made.

The command path scanner now separates the filesystem prefix from a pytest node
selector for explicit `python`/`python3 -m pytest` invocations when the candidate
is the first node argument, optionally preceded by `-q`/`-v`/`-s`/`-x` flags.
Interpreter operands, ambiguous/plugin option operands, response files and
redirection targets keep their original path syntax and authority checks.
This is a bounded selector correction, not a full pytest CLI parser or endpoint
proof. The release checklist also distinguishes process-bound compatible
connector freshness from strict rediscovery; retained contract ACK alone is not
new-epoch readiness, and stale/missing telemetry remains unknown.

These local changes do not extend an earlier EOCL acceptance receipt or prove
that the running development processes loaded the new bytes. Consolidated
baseline acceptance, accepted-to-loaded activation, natural Problem continuity
and outcomes, controller accounting, and package/release evidence retain their
own gates. See the linked checkpoint for exact scope, proof and remaining work;
historical runtime observations below remain bound to their recorded timestamps.

## 1. Source of truth and document precedence

When repository documents disagree, use this order:

1. **Current implementation + focused tests + live runtime contract** for the exact checkout being operated.
2. **This file (`docs/CURRENT_STATE.md`)** for the current product boundary and operating policy.
3. `README.md`, `docs/ARCHITECTURE.md`, `docs/RECOVERY_HOST.md`, `docs/TESTING.md`, `docs/ROADMAP.md`, `docs/RELEASE_CHECKLIST.md`, and `SECURITY.md` for maintained product guidance.
4. `docs/MODEL_EXECUTION.md` and `docs/agent/*` for the WebCodex core/subsystem they explicitly describe.
5. Dated files under `docs/research/*` as historical evidence, plans, benchmarks, and decision snapshots. They do **not** override later source or this current-state document.

A source implementation can be newer than the process currently running. For Electron, Recovery Host, Coding Tools MCP, and other supervised components, distinguish **source present**, **focused proof passed**, **EOCL accepted**, **controlled activation completed**, and **packaged/released**.

Development startup has two explicit contracts. `npm start` and `npm run dev` use the same stable start/focus lifecycle: they inspect the authenticated Recovery Host receipt for this exact development installation, classify Electron UI as `CURRENT`, `STALE`, or `MISSING`, focus a current UI, use component activation for a stale UI, or launch a missing UI. Success requires `running_revision == disk_revision` with PID/instance/mode metadata and a ready runtime postflight. Stale code activation remains authorized only from an eligible accepted closure checkpoint. `npm run dev:refresh` is the separate operator full-system refresh: it authenticates the current Recovery Host, creates a durable `full_clean_refresh` activation epoch, replaces Recovery Host, Coding MCP/Tunnel, configured Recovery MCP/Tunnel and Electron UI, then verifies fresh process identities, matching revisions and epoch binding. It never deletes durable truth; it fails closed if ownership, canonical ledger state or postflight cannot be proven. `npm run dev:stop` suppresses UI watchdog recovery and asks the exact registered single instance to quit while preserving Recovery Host, MCP, and Tunnel. It refuses an initially unavailable Recovery Host and reports success only after that exact host reports the UI `MISSING` or the previously bound PID is proven dead; transient host loss is not stop proof. `npm run dev:replace` applies the same exact-instance stop postflight, then relaunches and verifies a different UI instance. Connector discovery/ACK remains a separate gate; a refresh does not invent a connector receipt or open admission early.

The Command Center exposes loaded-source status for the three revisioned components—Electron UI, Recovery Host, and Coding MCP—and reports Tunnel health separately as `READY` or `STOPPED`. `CURRENT` is process/revision evidence only and never derives from Tunnel availability; it is not EOCL acceptance, release, deployment, production, or SLO proof. A source-update notice remains visible whenever a running component revision differs from disk.

The five-second Electron heartbeat is a read-only consumer of the latest completed Recovery Host supervision projection; it does not launch a second MCP/Tunnel/Git/OS-identity census. Recovery Host publishes the projection source, observation timestamp, age, busy flag, and freshness state, while Electron keeps heartbeat publication single-flight. Missing or older-than-30-second telemetry is `UNKNOWN/WARN` and appears yellow while retaining the last receipt for context; it is not evidence that MCP, Coding Tunnel, or Recovery Tunnel has stopped. Red is reserved for a confirmed stopped/error state or a deterministic `blocked_*` Recovery condition. This presentation rule does not weaken lifecycle recovery thresholds, process-identity checks, activation gates, or aggregate `fullyReady` semantics.

### Accepted-to-live activation closure

The supported development closure is `ACCEPTED/CHECKPOINTED -> ACTIVATABLE -> controlled component activation -> schema-v2 component postflight -> LIVE_CLOSED`. Each activation is authorized by one exact, non-normalized five-field `source_checkpoint`: `checkpoint_id`, `run_id`, `wave_id`, `proof_fingerprint`, and `git_head`. The Coding MCP preflight must return `ok=true`, `code=ACTIVATABLE`, and the same five values; partial, trimmed, case-folded, or otherwise reconstructed identities are not authority.

A schema-v2 postflight is accepted only when its operation, component, checkpoint lineage, expected/running/disk revision, instance transition, timestamps, health result, and fresh post-cancel lifecycle decision all verify. That final lifecycle decision must come from a new immutable, query-only SQLite Backup-API snapshot with `integrity_check=["ok"]`, zero foreign-key rows, valid physical/logical SHA-256 values, the exact operation/checkpoint, no fence, and zero blocking lifecycle counts, unexplained active RUNs, or unbound live residues. A contradictory `clean=true` flag cannot override those facts; the same lifecycle rule applies when an accepted checkpoint affects zero runtime components.

`LIVE_CLOSED` means only that this exact accepted local source is loaded and locally ready under the verified lifecycle and connector contract. Its projection deliberately remains `release_state=NOT_RELEASED` and `production_state=NOT_CLAIMED`. Connector continuity is separate: persisted SHA equality alone is not process-freshness proof for a new full-clean epoch. A breaking contract, meaning the acknowledged SHA is not the exact current SHA and is not a declared compatible predecessor under the same schema/profile boundary, still requires an attested current-process `tools/list` or `server/discover` receipt plus official Recovery Host acknowledgement. For an exact current SHA or declared compatible predecessor, an admission-closed no-workspace bootstrap may instead close the connector gate only after an attested ChatWeb `workspace_context` call is bound to the exact activation epoch, MCP process instance, server instance and contract SHA, reports `workspace_accessed=false`, and the Recovery Host guarded ACK persists that exact receipt. Raw HTTP, implicit or explicit identity headers without managed-tunnel attestation, catalog metadata, arbitrary `tools/call`, or textual receipts cannot satisfy either path. The compatible acknowledged state is `CURRENT_COMPATIBLE_ACKNOWLEDGED`; it remains truthful with `connectorRediscovered=false`, carries its own compatibility acknowledgement timestamp, and may reach `READY` / admission `OPEN` without inventing a discovery receipt.

### Superseding P0.6 accepted baseline and live receipt — 2026-09-01

The current accepted source baseline is `main @ 30b7d1b971b65034d3e4c95568c970fcc0e9380c`, and the observed
`origin/main` ref matches that commit. The P0.6 source packet contains exactly
27 source/documentation files with packet SHA-256
`b64a9704a73ea78fd3f330f12712b03090f8082765b3befd4b52eaa849d8d739`.
Its immutable candidate and acceptance receipts are
`.coding-tools/orchestration/baselines/p0.6-20260831T141719Z-b64a9704.candidate.json`
and `.coding-tools/orchestration/baselines/p0.6-20260831T141719Z-b64a9704.acceptance.json`.
ChatWeb accepted the exact-file wave at checkpoint
`e3b6c1a07b3f4524af8d0bef967fc7d5`; the canonical proof fingerprint is
`702139edffa332d62604af2b57e63c9ca65828207f92c589608f2c83df546fba`,
and completion report
`7a4ec1350c3a3ba58fb61926088e8f12f965a02de248a950b88de6d48483114c`
is acknowledged. This supersedes earlier paragraphs that describe P0.6,
full-component acceptance, or the scoped delivery commit as still open; those
paragraphs remain historical receipts for the observations made at their own
timestamps.

The accepted-baseline process receipt immediately after delivery reported
Electron UI and Coding MCP `CURRENT`, `components_ready=true`,
`fully_ready=true`, `runtime_update_incomplete=false`, and `error_code=none`.
Connector continuity at that accepted identity is
`CURRENT_COMPATIBLE_ACKNOWLEDGED` through the managed-attested
`compatible_activation_bootstrap` path, with
`connector_refresh_required=false`, `connector_ack_pending=false`, and
`connector_rediscovered=false`; no strict discovery is inferred. Windows
Recovery Supervisor reports `Running` / `healthy` with zero consecutive
failures. A fresh immutable Backup-API lifecycle census reports schema 12,
SQLite integrity `ok`, zero foreign-key rows, zero ordinary active RUNs, no
managed jobs, no projection drift, no unexplained active RUNs, no unbound live
resources, and no stale background-operation residue. Six terminal P5 epoch
anchors remain retained as evidence and do not constitute active work.

P0 Operational Convergence and the P0.6 immutable local baseline are therefore
closed for this accepted source/runtime identity. This does not promote the
separate product-evidence or delivery gates: independent natural Golden HR
outcomes, prospective causal evidence, P4 predictive validity, P5-A0 natural
instrumentation health, Windows installer/release acceptance, deployment,
production, and SLO claims remain open until their own authority and evidence
requirements are satisfied.

### Post-baseline P2 source slice — 2026-09-01

The current post-P0.6 worktree adds a source-only derived Resolution Capsule to
the existing `task_control(handoff)` path; it does not add a ninth public tool or
a second authority/database plane. The projector binds the exact RUN to its
primary Problem Revision, emits the typed contract and criteria fingerprints,
bounded latest-event identity, same-revision reopen and independent-outcome
receipt observations, and a content-free Problem Frame shadow/advisory. It
explicitly states that transcript, raw source and private reasoning are absent
and that the capsule grants neither mutation nor acceptance authority. The
outer handoff remains capped at 8 KiB: a contract of at most 4 KiB is embedded;
a larger valid contract is represented by its exact identity plus
`exact_revision_refresh_required=true`, so callers must fetch the exact revision
instead of receiving silently truncated content.

Focused source proof for this slice is `17 passed, 3 subtests passed` in
`tests/test_problem_lineage.py`, `18 passed` across the durable coordination and
coordination-state consumers, plus the module-size and scoped diff-hygiene
guards. This is not yet an accepted or loaded-runtime claim. A fresh
`npm run dev:status` after the runtime-affecting source edit reports Electron UI
`CURRENT`, but Coding MCP `mcp_revision_state=update_pending`,
`components_ready=false`, `fully_ready=false`, and
`runtime_update_incomplete=true`; the exact running and disk revisions differ.
Recovery Supervisor independently remains `Running` / `healthy` with zero
consecutive failures. Controlled activation and a new exact acceptance receipt
are separate next gates; natural Golden HR outcome evidence remains uncreated.

### Historical operational recency override — 2026-08-27

The maintained execution tracker at [`research/260823_CODING_WEB_GATE0_PRL_IMPLEMENTATION_AND_VALIDATION_TRACKER.md`](research/260823_CODING_WEB_GATE0_PRL_IMPLEMENTATION_AND_VALIDATION_TRACKER.md) was the operational receipt for the volatile lifecycle, connector, PRL, and packaged-harness claims in that observation window. The superseding P0.6 section above is the current maintained receipt; this historical section must not override it.

- The checked-out Git identity observed on 2026-08-29 is `main @ c0aa335c7c12746a1f4ff42e84234f8c54914658`, matching `origin/main`. The current full-clean activation-closure, PRL v11, managed-tunnel attestation, exact discovery-receipt and lightweight-UI waves remain newer uncommitted source until an exact accepted checkpoint says otherwise; therefore the P5 source baseline is not clean even though HEAD matches upstream. PRL fails public caller-derived authority closed, records immutable non-code dispositions and checkpoint-bound reconciliation, reports revision-scoped clocks/intervals, and emits C4 receipt schema `2` with Backup-API snapshot identity plus independently rebuilt proof/checkpoint/bridge coverage. Neither a matched source revision nor a fresh runtime receipt is a package, installer, release, deployment, production, or SLO claim.
- Earlier P0/P4 connector acknowledgements and tool calls are `VERIFIED_SNAPSHOT`, not current-process authority. The current connector claim must be read from a fresh Recovery Host closure receipt under the unchanged-versus-changed SHA rules above; no persisted hash, generic tool call, or historical rediscovery timestamp may substitute for it.
- P5 anchors remain terminal and the earlier A0 source-drift epoch retains its truthful zero funnel. Volatile ordinary-RUN, managed-job, and residue counts are not frozen in this maintained source document: recapture them from one immutable `report_lifecycle_census.py` snapshot before activation or stale-run reconciliation, and use only the official exact-ID path for a genuinely eligible stale RUN.
- PRL-D and A2 remain `HOLD_NATURAL_EVIDENCE`; missing natural observations, TTPR, stage coverage, and measured money remain unknown rather than zero.
- The isolated P0.3 packaged Recovery lane is source/package-local evidence, not an exact-frozen release candidate, installed-session, reboot/logon, connector, or production claim.

### PRL v12 typed outcome-receipt source checkpoint — 2026-08-31

The current uncommitted worktree advances PRL storage from schema v11 to v12
and new problem events from schema 2 to schema 3 without changing the public
eight-tool `smart-v3` contract. `problem.confirm` remains a semantic input: the
runtime, not the public caller, claims the exact one-shot ChatWeb host turn and
derives `CHATWEB_EXPLICIT_USER_OUTCOME_V1` from the event ID, Problem Revision,
turn ID and trace ID. The resulting receipt is written under
`RUNTIME_OUTCOME_RECEIPT`, participates in the event hash chain, and is counted
by the read-only economics reporter only when the digest and provenance binding
recompute exactly. Direct caller receipt fields, missing host identity, a
mismatched digest, or tampered event bytes fail closed.

The guarded v11-to-v12 path preserves historical schema-2 event hashes and
leaves their receipt fields empty; it never backfills independent outcome
evidence. The current focused/affected packet passes `39` tests plus `7`
subtests, module-size validation and Python compilation, and the disk contract
remains the exact eight-tool SHA
`c244ed297f707f9df48c1e5d6c7e204693f281a755c2e6344bde78e94abb8251`.
The source packet was subsequently migrated under the guarded v11-to-v12 path
and loaded by the current development process. The following current receipt
supersedes the source-only qualification above for the live local epoch; it
does not rewrite the historical checkpoint.

### Current PRL v12 runtime and connector receipt — 2026-08-31T04:46Z

The full-clean development epoch
`activation-mtgqx4ha-2d70125bdcf3f1654d0c2de29361823a` is `READY` with admission
`OPEN`. Recovery Host, Coding MCP and Tunnel are running; Coding MCP
`running_revision == disk_revision ==
e5d120eb38e89f195dd504d77e64f5081dd5737710dd088cfe71e6b0a2b3c897`; the
Electron UI is also current. Coding-VP Live produced one managed-attested,
no-workspace `workspace_context` compatibility bootstrap at
`2026-08-31T04:45:19.154620+00:00`, bound to the current epoch/process/server
and contract SHA. The guarded Recovery Host acknowledgement is
`CURRENT_COMPATIBLE_ACKNOWLEDGED` with
`connector_freshness_mode=compatible_activation_bootstrap`,
`connector_refresh_required=false`, `connector_ack_pending=false`, and
`fully_ready=true`. This is intentionally not claimed as strict
`tools/list`/`server/discover`: `connector_rediscovered=false` remains truthful.

The PRL v12 canary was read-only and returned
`C4_SOURCE_READY_AWAITING_NATURAL_CANARY`; SQLite integrity and foreign-key
checks passed, while no natural cohort was inferred. The PRL-D economics
reporter returned schema version `5` against canonical PRL schema `12`, with
zero problem revisions and `null`/unavailable outcome, TTPR and efficacy
denominators. Missing natural evidence remains `unknown`/`null`; no synthetic
problem, outcome receipt or policy promotion was created.

This receipt closes current local runtime activation only. Full-component
source acceptance for the entire dirty Coding MCP component, an immutable
accepted Git baseline (P0.6), natural HR outcome evidence, commit, package,
release, deployment and production claims remain separate open gates.

### Current local activation and UI performance receipt — 2026-08-29T20:15:03Z

The exact current development process has now closed the local connector and UI
performance gates for the uncommitted source on disk. Query-only lifecycle
census observed `active_agent_lanes=0`, no managed jobs, unexplained active
runs, unbound resources, stale background residue or projection drift, and did
not mutate the canonical ledger. Three ordinary `active` rows remain classified
`THRESHOLD_SENSITIVE_STALE_CANDIDATE`; each has zero live ownership and remains
untouched until the supported stale threshold/authority permits reconciliation.

Full-clean epoch
`activation-mtetdl86-68c08c2f914e8049a4ebb4bf69833539` is `READY` with
admission `OPEN`. Coding MCP process/server identities are
`9RkQbeqAUay5_LRD` / `4OtFTiY9AnN5C8Po`, and its running revision equals disk
revision `68f0a59095855c4250f85bc72a7784ffafca99b424e73158a95948d1112ceff6`.
The real Coding-VP Live connection produced current-process discovery at
`2026-08-29T20:10:30.820587Z`; Recovery Host guarded acknowledgement reports
`CURRENT_ACKNOWLEDGED`, `connector_rediscovered=true`,
`connector_refresh_required=false`, `connector_ack_pending=false`, and exact
current/acknowledged contract SHA
`c244ed297f707f9df48c1e5d6c7e204693f281a755c2e6344bde78e94abb8251`.

On Electron UI instance `2709389fe3f50d3202ae67a25b3b7218`, the retained
25-renderer/50-main/558-event-loop sample window passes all current budgets:
event-loop p95 `15.6 ms`, normal IPC p95 `44.2 ms`, snapshot-apply p95 `0 ms`,
and dashboard-refresh p95 `66.2 ms`. Direct Recovery IPC also passes with 20
samples and p95 `3.07 ms`.

This is exact local runtime/connector/UI evidence for the present dirty
worktree, not an immutable accepted source baseline. P0.6 remains open until an
accepted/checkpointed Git identity exists under explicit scoped commit
authority and the remaining threshold-sensitive lifecycle rows can be handled
through supported authority. P5 remains gated on natural eligible workload and
an explicit frozen manifest/operator action. No commit, push, package, release,
deployment, or production operation is implied by this receipt.

### Operational follow-up — 2026-08-29T23:39:08Z

A new authenticated Recovery Host snapshot for the same checkout confirms that
the local control plane has not regressed: the epoch above remains `READY` with
admission `OPEN`; MCP, Tunnel and aggregate readiness are true; failures are
zero; connector state remains `CURRENT_ACKNOWLEDGED`; the strict discovery
receipt is still bound to the current process at
`2026-08-29T20:10:30.820587Z`; and both Coding MCP and Electron UI still report
`running_revision == disk_revision` with `update_pending=false`. The installed
development Recovery Supervisor is also `Running` / `healthy` with zero
consecutive failures. Consequently, an error observed through an older
ChatGPT connector or tunnel ID is not evidence that this active Electron
runtime is offline.

The ChatGPT Business workspace now shows the developer-mode app
`Coding-VP Live` as connected and exposes the expected eight-tool schema.
However, neither the app-details **Refresh** action nor a new normal ChatWeb
conversation advanced `connector_rediscovered_at`; the conversation reported
that protocol-level `tools/list` and `server/discover` are not exposed as model
callable operations, and no business tool fallback was used. The schema view,
the textual response, and the unchanged timestamp are therefore **not** a new
discovery receipt. They do not invalidate the accepted receipt for the current
process, but they leave rediscovery of a future replacement process unproven.
Do not stop this healthy epoch or run another full-clean merely to probe that
external client limitation.

The immutable/query-only census captured at
`2026-08-29T23:39:08.645Z` again reports `integrity_check=ok`, zero foreign-key
rows, `mutated_canonical_ledger=false`, no managed jobs, no unexplained active
RUN, no unbound live resource, no stale background residue and no projection
drift. The three ordinary active rows still have zero controller lease, write
fence, live agent lane, managed job and background operation, but remain
`below_current_stale_threshold`. Their earliest eligible times are
`2026-08-30 09:34:34`, `09:36:13` and `09:50:58` Asia/Saigon. No reconciliation,
runtime stop, activation, connector ACK, accepted-baseline creation, P5 action,
commit, push, package, release or deployment was performed in this follow-up.
The active completion monitor must recapture fresh hashes and exact-ID
preflight after those thresholds; it must also prove a managed-attested
discovery route before replacing the current process.

### Causal correction and live recapture — 2026-08-29T23:43:51Z

The discovery prerequisite above means a demonstrably connected official
route, not an impossible receipt for a process that does not yet exist.  The
same `Coding-VP Live` route already produced the managed-attested receipt for
the current replacement process at `2026-08-29T20:10:30.820587Z`.  A later
same-process app refresh that did not advance the timestamp does not invalidate
that receipt; it only fails to prove another protocol discovery occurred.  A
future replacement must therefore create its own receipt *after* the process
exists and before guarded acknowledgement.  If it does not, the new epoch must
remain fail-closed with admission closed; neither model text nor another
full-clean loop is a substitute.

Fresh local checks also disprove the attached claim that the active Coding
Tunnel is currently offline.  `npm run dev:status` reports `CURRENT`,
`host=available`, matching Electron running/disk revisions,
`CURRENT_ACKNOWLEDGED`, current-process discovery, no connector refresh/ACK
pending state, and no error.  The independent Recovery Supervisor briefly
reported `blocked_live_owner / LIVE_OWNER_UNRESPONSIVE` for one 1.5-second ping
while concurrent status/census reads were running, correctly refused to kill a
live owner, and returned on its next poll to `Running / healthy` with zero
consecutive failures and no restart attempt.  This is a transient uncertain
observation, not proof of a stopped tunnel or authority to replace the owner.

The immutable/query-only census at `2026-08-29T23:43:04.726Z` retained SQLite
integrity, zero foreign-key rows, no managed jobs, unexplained active RUNs,
unbound resources, stale background residues or projection drift.  Its
physical/logical SHA-256 values are respectively
`b556ead11a7ddb5fb303a47c98e9bb74ebb575202da8b65dc2e4c87a58d07107` and
`ed2cb592030ddefbcf5459475dcd9f4a67757e6654a8fd27c2e594c3ba426b5c`.
All three ordinary rows still had zero controller leases, write fences, live
agent lanes, managed jobs and running background operations, but their ages
were only `75123`–`76108` seconds against the supported `86400`-second
threshold.  These hashes are observation-only and must be recaptured after the
last threshold at `2026-08-30 09:50:58` Asia/Saigon; they are not authority for
later reconciliation.

### Recovery Supervisor false-owner remediation — 2026-08-30T00:04:36Z

The one-poll `blocked_live_owner / LIVE_OWNER_UNRESPONSIVE` transition above is
now reproducible and has a bounded source cause.  Both `recovery.ping` and
`recovery.status` previously built `hostStatus()` synchronously on the Recovery
Host IPC event loop.  That path performs Windows process-identity observation,
forced component-revision work and durable activation-state reads.  A normal
`npm run dev:status` can therefore overlap the independent Supervisor's
1.5-second liveness deadline and make an exact live owner temporarily
unresponsive.  The Supervisor response remains correct and fail-closed: the
live owner is not killed or adopted, the failure streak is one, no restart is
attempted, and the following poll returns to `healthy`.

The dirty source now separates liveness, cached presentation and mutation
authority.  `recovery.ping` is an in-memory exact host identity receipt;
`recovery.status` copies the most recent completed supervision projection and
adds bounded age/staleness metadata.  Activation and mutation paths retain
their fresh exact-identity, revision, epoch and ledger preflights.  A real
process harness race exposed by the faster ping was also corrected: the harness
must wait for a projection carrying the expected positive MCP/Tunnel PIDs and
must never probe or signal PID `0` during cleanup.

Current focused proof is `71/71 PASS` for Recovery Host and lifecycle status,
and `152/152 PASS` for the affected Supervisor, full-clean, runtime-lifecycle
and real-process boundary.  The real-process subset is `3/3 PASS` and
`git diff --check` passes.  A live recapture at `2026-08-30T00:04:10Z` still
reports `CURRENT`, `CURRENT_ACKNOWLEDGED`, current-process rediscovery, exact
connector SHA equality, no refresh/ACK pending state and no error.  The next
Supervisor poll reproduced the old one-failure state and the poll at
`2026-08-30T00:04:36Z` returned to `healthy` with the same host identity and no
restart attempt.  This proves the source cause against the still-running old
process; it does not claim that the new source is active.  Loading the fix
remains part of the single supported post-threshold full-clean sequence.

The same dirty source fingerprint now also has broad repository proof.  The
Node repository suite originally reported `547/547 PASS`, followed by the source-root
policy guard and repository secret check passing.  The complete Coding Tools
MCP suite reports `741 PASS` with `4` environment-conditional skips out of
`745` collected tests.  These broader results strengthen source acceptance but
do not create a checkpointed Git identity, mutate lifecycle state, activate the
new Recovery Host source, or promote P0.6/P5 by themselves.

### Development Supervisor suppression correction — 2026-08-30T00:38:27Z

A later live recapture found a second, independent resilience cause. The
previous Recovery Host was last observed healthy at `2026-08-30T00:09:31Z`,
but `%LOCALAPPDATA%\WebMcpRecoverySupervisor\stop.request` was written at
`2026-08-30T00:09:37.473Z`. Every subsequent Scheduled Task invocation
therefore exited in `stopping`; by `2026-08-30T00:38:25Z`, `npm run dev:status`
correctly reported `MISSING / RECOVERY_DESCRIPTOR_STALE`. The task remained
installed and its manifest still identified this exact checkout, so this was
not a `blocked_live_owner`, connector-cache result, or foreign-checkout
takeover.

The source cause was `ensureRecoveryHost()` suppressing any installed
development Supervisor *before* it checked whether the UI could simply attach
to the already healthy exact-checkout Recovery Host. That ordinary attachment
created the stop sentinel even though no host mutation or handoff followed;
when the Host later disappeared, the deliberately suppressed Supervisor could
not resurrect it. The dirty source now defers the decision until immediately
before an actual stale-host retirement or missing-host spawn and preserves an
installed Supervisor whose app-root/executable identity already matches the
current checkout. An exact healthy attachment never reaches suppression.
Focused launcher coverage is `15/15 PASS`, and the scoped diff check passes. The
current stopped runtime has not loaded this correction, and no restart or
Supervisor reinstall was performed during the diagnosis. The full Node
repository suite for this corrected source reports `550/550 PASS`, and the
source-root policy guard plus repository secret check also pass.

The same census also explains the fourth ordinary active RUN
`037b642a187e4f098dc66e6dd1c9b3c1`. It was not created by a status poll or
background cleanup. A distinct ChatWeb task context explicitly invoked the
destructive/project-write `agent_workflow(phase="prepare")` at
`2026-08-29T23:52:54Z`, which intentionally created a durable `PREFLIGHT` RUN,
then ended after read-only commands without using exact-context
`task_control(action="stop")`. That caller action contradicted its own stated
"do not create RUN/WAVE" constraint. The RUN has zero controller lease, write
fence, live lane, managed job and background operation, but the current
controller is not authorized to forge the old task context or reconcile below
the supported 24-hour threshold. Its earliest stale-reconciliation time is
approximately `2026-08-31 06:53:20` Asia/Saigon. This is a caller lifecycle
contract violation, not evidence that a read-only status or census path
spontaneously creates RUN rows.

### Long-lived managed-Tunnel discovery correction — 2026-08-30

The unchanged rediscovery timestamp after the later real `Coding-VP Live`
refresh was not merely a model-binding limitation. Sanitized Tunnel chronology
shows that the official control plane forwarded `openai-mcp-discover` at about
`2026-08-30 03:10:30` and again at `06:27:17` Asia/Saigon for the same exact
activation epoch, MCP process/server identities and contract SHA. The first
request created the strict receipt at `2026-08-29T20:10:30.820587Z`; the second
request reached MCP but did not advance it.

The repository-side cause was a mismatch between producer and verifier
semantics. `tunnel-client` supports one static `--mcp.extra-headers` value for a
managed Tunnel lifecycle, while the MCP verifier expired that same HMAC after
15 minutes. Legitimate discovery on a long-lived exact process was therefore
served but downgraded from `attested_transport` with `timestamp_expired`, so it
could not update the authoritative receipt. The source now models the primitive
truthfully as a lifecycle-bound capability: it retains HMAC-SHA256, exact
client/epoch/process/server/contract binding, future-timestamp rejection,
tamper rejection and secret rotation on MCP replacement, but does not expire an
otherwise exact live-lifecycle capability solely by wall-clock age. Direct
regressions prove that an exact 24-hour-old capability remains valid, while
cross-epoch/process/server/SHA replay, secret rotation, tamper and future
timestamps remain rejected.

The Tunnel launch contract is also covered directly: the attestation reference
appears only under `--mcp.extra-headers`; local
`--mcp.discovery-extra-headers` probes receive no attestation and cannot
manufacture a ChatWeb receipt. Recovery Host now ignores even an exact
compatibility `workspace_context` bootstrap when deciding whether to wake the
strict final-census/finalize path. Bootstrap leaves the epoch
`VERIFYING` / admission `CLOSED`; only an exact managed-attested current-tuple
`tools/list` or `server/discover` receipt can lead to strict ACK and
`READY` / `OPEN`.

Focused source proof for this correction is `42 passed, 4 subtests passed` in
the Python connector/protocol/HTTP/activation suite and `213 passed` in the
affected Node Tunnel/lifecycle/full-clean/Recovery Host/development-status
suite. Module-size budgets and `git diff --check` pass. These results prove the
dirty source behavior only. A read-only `npm run dev:status` at the end of the
wave reports `state=MISSING`, `host=unavailable`,
`error_code=RECOVERY_DESCRIPTOR_STALE`; no live process has loaded this fix.
The status line now labels its legacy revision fields
`revision_scope=electron_ui` and separately reports Coding MCP revision,
aggregate readiness and snapshot freshness, preventing a UI `CURRENT` result
from being misread as whole-stack currency. No restart, activation, connector
ACK, commit, push, package, release or deployment was performed by this source
correction.

### Strict discovery authority hardening and live recapture — 2026-08-30T07:22:22Z

The current dirty source now closes the remaining authority gaps around MCP
replacement and connector projection. Every epoch-bound Native/Python launch
normalizes to admission `closed`; explicit `open` or unknown gates are rejected.
Durable epoch authority that is missing or unreadable fails closed before
process mutation, and `READY_COMMITTED`, `READY`, or `FAILED` epochs cannot be
reused for another MCP spawn. A direct eligible MCP replacement rotates the
attestation secret and replaces the dependent Coding Tunnel with an attestation
bound to the new MCP epoch/process/server/contract tuple; failure to rebind the
Tunnel rolls the new MCP back. Live connector projections compare discovery,
contact, and bootstrap receipts to the exact health tuple, so a receipt from a
retired process cannot be presented as current. Detached hash/synchronization
helpers no longer persist an acknowledgement; the mutating path requires the
complete current health receipt.

The final core affected Node packet is `239/239 PASS`, and the broader lifecycle
packet is `340/340 PASS`. The focused Python activation packet is `9/9 PASS`
with `2` passing subtests; JavaScript syntax, Python compilation, and
`git diff --check` also pass. This is source proof for the dirty worktree, not
loaded-runtime or delivery proof.

A read-only `npm run dev:status` recapture reports `state=CURRENT` and
`host=available` for Electron UI, with its running/disk revisions equal and
`update_pending=false`. Coding MCP is still the older loaded source:
`mcp_revision_state=update_pending`, running revision
`23b6aa33d59083a9706289a4d4cdbf261b84cebe1a59d758d903079e0e3101af`, disk
revision `84f0f941c46386812746d0b6f3bcace449475b5106551c980e0be476d68da800`.
Therefore `components_ready=false`, `fully_ready=false`, and
`runtime_update_incomplete=true`. Connector state is
`UNCHANGED_COMPATIBLE_NEEDS_ACK` with `connector_rediscovered=false`, no
rediscovery timestamp, `connector_ack_pending=true`, and
`connector_refresh_required=false`. The last field does not cancel the pending
strict gate. This recapture supersedes older live-looking receipts above only
for current process state; it does not rewrite their historical chronology.
No restart, activation, connector ACK, commit, push, package, release, or
deployment was performed in this hardening wave.

### Source validation update — 2026-08-27

Before the automatic endpoint-identity packet below, the then-current uncommitted source fingerprint had a green Node repository suite (`482/482`) and a green complete Coding Tools MCP result (`698` tests, `4` environment-conditional skips, `106` subtests), including the focused full-clean/activation, acceptance, orchestration, PRL, and projection packet (`120` tests, `1` skip, `43` subtests). The newer endpoint packet has focused source proof for installation separation, workspace-generation invalidation, stateless discovery metadata, unchanged tool-contract SHA, and Python compilation. These remain source-level results only; they do not establish current-process connector discovery/ACK, controlled activation, package, release, deployment, or production readiness. Live process-refresh evidence remains a separate receipt.

At `2026-08-27T16:37:26Z`, a controlled `npm start` process refresh from this
checkout exited successfully after replacing Recovery Host, Coding MCP, Coding
Tunnel, Recovery MCP, Recovery Tunnel, and Electron UI. The replacement Coding
MCP (`pid=20916`, component revision
`c6f1c2f2bb0c92ff46a5e3002cb58b9c358af9d4b27f7d3fd4b057661e29bd92`)
and Coding Tunnel (`pid=21484`) were both ready; the former stopped-runtime
`ORCHESTRATION_STATE_UNCERTAIN` refusal did not recur. The durable activation
epoch `activation-mtbqsh83-094c596a51df8d2f827d01936dbda21a` remains
truthfully `VERIFYING` with admission closed because the real external client
has not yet produced current-process discovery for tool-contract SHA
`57ed56a4f008287d9d9fdef035fa248f91cce4d58e935280b28963e4126a8053`;
the retained acknowledgement names older SHA
`3e37f9fed85bd80f46ee79a820291f617584b6b6ba65b43c16f163adf37993fd`.
This is live component/process proof, not connector ACK, `LIVE_CLOSED`, package,
release, deployment, or production proof.

### Live reconciliation — 2026-08-26

The Recovery Host receipt captured at `2026-08-26T02:06:12Z` for `E:\DEV\Codex-web` remains historical live evidence for that loaded process. It reported the then-existing component-local `fullyReady=true`, Coding MCP `running_revision == disk_revision == cbcab4d0e5382431d1193724c7e13c128de319bceea7baae2e617a05decc3db5`, and the exact eight-tool `smart-v3` contract SHA `fb159d403ef490caeb29b1b54111c2b0353a7544bb2ecad564cfec3b2f878585`. It simultaneously reported `connectorRediscovered=false`, `connectorRediscoveredAt=null`, `connectorRefreshRequired=true`, with acknowledged SHA `34cbb4c3ce3668f86ef6340dcb210d07425814c40ba734180ee1c026c96d409c`. Under the maintained aggregate readiness contract below, that tuple is `UPDATE_INCOMPLETE` and must project `fullyReady=false`; the historical green field is not current activation authority. Focused transport/stateless/fault validation was green (`22/22`), the SDK contract/exception boundary was green (`8/8`), and an HTTP-level `tools/call` regression confirmed raw `ExceptionGroup` text could not escape the JSON-RPC boundary (`6/6`). A model-text inventory or ordinary `tools/call` cannot replace real current-process `tools/list`/`server/discover`, official acknowledgement, or C4 natural evidence.

## 2. Current product boundary

The product currently operated from this repository is the **Windows Electron Execution Hub + Coding Tools MCP** stack. The repository still contains substantial WebCodex Rust/server/runner functionality inherited from and developed beyond the upstream project; that code is a foundation/subsystem, not the only description of the desktop product.

```text
ChatWeb / ChatGPT
      |
      | MCP over primary tunnel
      v
Recovery Host / Execution Hub authority
      |
      +--> ONE Coding Tools MCP Runtime -----> workspace / Git / commands / proof
      |            ^
      |            |
      |       Codex Desktop thin stdio proxy
      |
      +--> Electron Execution Control Center
      |
      +--> independent Recovery MCP + Recovery Tunnel

Secondary reasoning/provider lanes:
  Codex App Server / OpenCode -> bounded candidate, review, or read-only provider work
  Coding Tools MCP / EOCL      -> mutation, proof, durable ledger, acceptance boundary
```

There must not be two peer Coding Tools runtimes independently mutating the same workspace/ledger. ChatWeb and Codex Desktop share the Execution Hub truth; they do not synchronize transcripts.

## 3. Current `smart-v3` MCP contract

The current `smart` profile intentionally exposes exactly these eight public tools:

- `workspace_context`
- `agent_workflow`
- `task_control`
- `document_workflow`
- `exec_command`
- `command_control`
- `request_permissions`
- `view_image`

### Automatic installed-endpoint identity (source contract)

Every Electron installation already creates a durable random `device_id` and
passes it, the current Recovery Host instance, and the OS display name to Coding
MCP. Coding MCP now derives a non-secret `endpoint_id` and collision-resistant
`route_key` automatically from that installation identity, while each canonical
root retains its separate content-free `workspace_id` and
`workspace_generation`. A standalone MCP process that has no Electron-provided
device identity falls back to a workspace-scoped endpoint identity rather than
collecting an implicit hardware fingerprint.

Legacy initialize, authenticated stateless responses, `server/discover`, and
`workspace_context` expose the same endpoint projection. The public unauthenticated
server card remains generic and never exposes device/workspace identity. The dynamic server title
includes the detected device display name and current workspace; routing
instructions tell the client to reuse the endpoint already pinned to the task
instead of probing peer Coding Tools connectors just to compare identities.
Process/server/activation fields remain freshness invalidators, and mutation must
never silently fail over to another endpoint. Dynamic endpoint metadata is kept
outside the eight-tool schema, so installing the same build on another machine
does not create a machine-specific `tools/list` SHA or unnecessary contract ACK.

This removes any requirement to configure labels such as Home/Office manually.
A first installation still requires the operator to select/authorize a workspace
and supply its separately created Tunnel ID and runtime credential; those are
authorization inputs that cannot be inferred safely from hostname or local disk.

### BOOT_HOST_TRANSITION_RECONNECTION_LOOP — working-tree source fixed / current-device live pass

The remaining implementation packets, acceptance matrix, and closure boundaries
are defined in [the detailed closure plan](BOOT_HOST_TRANSITION_CLOSURE_PLAN.md).
That plan is not a claim that the whole product problem has been closed.

This product problem tracks repeated manual repair, refresh, login, or connector
recovery after a same-device cold start or after returning on a device that
skipped one or more compatible releases. Account session, endpoint/workspace
identity, and connector-contract acknowledgement remain three separate layers:
the Electron ChatGPT view uses the durable `persist:chatgpt-session` partition;
each installation keeps its own device-bound endpoint identity; and connector
freshness stays bound to the exact current process, server, activation epoch,
workspace generation, and public contract SHA. A new device may still require
one real account login and separately provisioned local credentials. Credentials
or mutation authority must never be copied or silently failed over between
devices.

The Problem is closed only when all of the following are demonstrated:

- a same-device cold boot reuses a non-revoked ChatGPT session and the saved
  workspace/device identity without source repair or repeated refresh;
- Recovery Host, Coding MCP, and the device's own Tunnel start or recover into
  the exact configured workspace, with admission opened only after the guarded
  connector path completes;
- a client that skipped one or more reviewed additive releases can bootstrap
  through the reviewed compatibility closure, while a breaking or unknown
  contract still requires real discovery;
- a new device asks for account login and local credential/workspace setup only
  when they are genuinely absent or revoked, never by copying another device's
  token or authority;
- Coding-VP Live and a separately tunnelled Coding MCP remain distinct routes,
  and no write-capable task silently fails over between them; and
- focused cold-start/skipped-version/two-device tests plus an installed Windows
  logon smoke pass for the exact release candidate.

The `ae04947` public contract changed from `d52c889...` to `d69436c...` by adding
only optional `candidate_cursor` and `candidate_limit` fields to
`task_control.goal_event` plus a descriptive pagination update. The committed
source omitted the reviewed compatibility edge and retained the stale exact-SHA
test, so an already acknowledged client correctly fell into
`CHANGED_NEEDS_DISCOVERY`. The current working tree now records the reviewed direct
`d69436c... -> d52c889...` edge and publishes the deterministic transitive
closure of the existing reviewed additive-edge graph. This lets a device skip
multiple compatible releases without manual per-release discovery. Unknown or
malformed hashes and any reachable graph cycle return no compatibility; an
undeclared or schema/profile-changing contract still requires real current-
process `tools/list` or `server/discover`.

Compatibility metadata alone never opens admission. The narrow bootstrap still
requires an attested ChatWeb `workspace_context` contact with no workspace read,
matching current contract/process/server/epoch identity, and the final activation
census independently requires the exact device and workspace binding. Focused
Python tests cover exact SHA, multi-hop order, unknown hashes, malformed edges,
and cycles. Electron tests cover skipped-version acknowledgement plus negative
process/server/epoch/client/workspace-access cases, while the existing connector
binding and full-clean suites retain their independent fail-closed gates.

The controlled development refresh captured on 2026-09-14 completed epoch
`activation-mu0nwtkj-5b558ae4a52562fb6c739de983b52912` as `READY`, with
MCP and Tunnel ready, admission open, `fully_ready=true`, and
`CURRENT_COMPATIBLE_ACKNOWLEDGED`; both current and acknowledged contract SHA are
`d69436cabfbb6dca7b365df507f4b507857d9b29c11a44883fab77de54f67810`.
This is a current-device development live pass, not an installed Windows logon,
two-device, package, release, deployment, or production claim. Those boundary
smokes remain required before closing the whole cross-machine product problem.

### Authorized-root workspace projection (source contract)

When the Runtime has more than one authorized root, `workspace_context(path)`
canonicalizes the requested root and reports that root's `workspace_id`, project
metadata, Git summary, and task projection. The task projection is loaded from
the selected root and current MCP execution context; it never falls back to the
primary Runtime task or to another project. A context that has been bound by a
workspace read cannot be rebound to a different root (`TASK_CONTEXT_WORKSPACE_MISMATCH`).
Mutating public calls without an explicit path/workdir or an already-bound task
context fail closed with `WORKSPACE_TARGET_REQUIRED` when multiple roots are
authorized. This is source and focused-test proof only; it does not by itself
prove controlled live activation, packaging, release, or production readiness.
The binding is persisted as server-derived state in
`.coding-tools/orchestration/task-context-workspaces.json`; after Runtime
restart the canonical root, current authorization set, and content-free
`workspace_id` are revalidated before reuse. Missing, malformed, legacy, or
unauthorized mappings fail closed as `UNKNOWN_LEGACY_WORKSPACE`,
`WORKSPACE_NOT_AUTHORIZED`, or `WORKSPACE_SCOPE_INCONSISTENT`.
Handoff capsules include the bound workspace identity, authority transition,
source/diff fingerprints, lease/delegation IDs, bounded dirty paths, proof IDs,
and unresolved-risk projection; they do not replace the canonical ledger or
carry transcript/raw command output.
The repository also has a public stateless-HTTP matrix that binds two temporary
workspace roots, creates separate task/run projections, rejects cross-workspace
`task_control`, then recreates the Runtime and verifies the authorized context
and task projection are restored.

`restart_runtime` is an action of `task_control`, not a ninth public tool. The runtime publishes a deterministic contract fingerprint and tool count so Electron can detect a stale ChatGPT connector schema.
The action is a deferred post-tool-call full-clean request: MCP returns a short-lived
ticket after fencing the exact operation, and Recovery Host later consumes the
same ticket ID as the full-clean operation ID. Recovery Host revalidates the
ticket's workspace/process/server identity and resolves source authority only
from the current accepted closure; it never treats the ticket itself as a
checkpoint. The signed Recovery Host census may reuse that exact fence identity,
but it does not discount the initiating active tool call. It returns
`RUNTIME_BUSY` and keeps the `.processing` journal until the MCP active-call count
is actually zero, then retries the same operation. This proves the caller has
left its tool boundary before process mutation while preserving fail-closed
checkpoint authority.

Runtime activation has two explicit modes. `soft_recovery` remains component-scoped
for automatic local fault recovery (for example, a dead Tunnel or a crashed MCP)
and is revision-continuity guarded. When the durable epoch is eligible for an
in-place replacement, repeated semantic MCP failures replace the exact owned
MCP process and restart only its dependent Coding Tunnel process so
the managed attestation is rebound to the new MCP process/server tuple; Tunnel
configuration and the Recovery Host/UI/Recovery Plane stay in place. The MCP
replacement is stopped again if disk revision drifts across its spawn boundary.
This path is legal only while durable epoch authority is readable and
nonterminal. `READY_COMMITTED`, `READY`, and `FAILED` epochs cannot be reused for
another MCP spawn, even with a closed gate; a new full-clean epoch is required,
and missing/unreadable epoch authority fails closed before Native or Tunnel
mutation. Operator `restart`, accepted code/revision
activation, and controlled updates use `full_clean_activation`: a durable
`activation_epoch_id` is created, admission closes, durable state is checkpointed,
Electron UI/Coding Tunnel/Coding MCP and configured Recovery MCP/Tunnel are stopped,
and a replacement Recovery Host starts fresh processes with the same epoch. The
epoch remains `UPDATE_INCOMPLETE` until a final current-process census verifies
workspace, persistent device identity plus fresh lifecycle instance identity,
disk/runtime revisions, process/server/supervisor identities, real tunnel health,
UI and Recovery Plane identities, and a fresh connector discovery/ACK. For the
deferred `task_control` route, Recovery Host performs that ACK itself only after
the exact post-preflight health receipt binds `tools/list`/`server/discover` to
the current epoch, process ID, server ID and contract SHA; persisted hashes,
compatibility-only contact and ordinary `tools/call` are insufficient. Only a
verified `READY` epoch with `admission_open=true` may report `fullyReady=true`.
The ledger, task history, acceptance state, settings, secrets handles,
authorized roots, and device identity are never deleted by this transaction.

The development `npm run dev:refresh` command treats exact process refresh completion and
connector acceptance as separate observable boundaries. It exits successfully
after the new Recovery Host, Coding MCP/Tunnel, Recovery MCP/Tunnel and Electron
UI have passed their exact identity/epoch/revision/health/projection census. If
real-client discovery has not happened yet, the durable epoch remains
`VERIFYING`, admission remains closed, and the CLI reports
`fully_ready=false connector=pending`; it does not wait until TTL and misreport
the completed process refresh as a startup failure. While only this external
connector gate remains, Recovery Host serves a bounded cached read-only runtime
snapshot and polls the MCP discovery receipt without repeating OS-identity and
Tunnel census probes every five seconds. Exact current-process discovery is the
event that re-enters the authoritative final census/ACK/READY transaction. The
watchdog persists that exact passing census while admission is still closed
before `finalize()` performs its independent census. If the otherwise valid
cached projection receipt crosses its five-minute TTL at this boundary, the
coordinator rebuilds the projection and captures a new health receipt; workspace,
ledger, process, server, epoch or receipt-integrity mismatch still fails closed.

When a failed activation left Coding MCP stopped, an explicit retry is admitted
only after Recovery Host obtains an independent immutable/query-only
Backup-API ledger census, validates quiescence and unresolved-acceptance gates,
and confirms the same census fingerprint on a second read immediately before
epoch creation while holding the application ledger gate exclusively through
the durable epoch-store create. A ledger hash, workspace, source-checkpoint, or runtime-state
identity change fails closed before any process stop; the durable ledger and
the failed epoch remain untouched.

Because background workflows are process-scoped, a stopped-runtime census does
not treat an old `running` row as live forever. Rows with a parseable activity
timestamp older than the census grace window are retained as stale residue and
the replacement runtime marks them orphaned during startup. Managed-process
rows are likewise restart-reconcilable only when an exact OS identity probe
proves that the original PID is gone or has been recycled. Recent or malformed
background evidence, a live matching process, an unverifiable process identity,
leases, fences, live lanes, projection drift, and integrity failures still
block activation.

Contextual task files are current views, not a complete index of historical
RUNs. An `AWAITING_ACCEPTANCE` RUN with a valid canonical wave/state, no live
ownership and activity older than the census grace window may have no remaining
context binding without causing `PROJECTION_DRIFT`. The read-only census reports
this as `unprojected_historical_acceptance_count`; the RUN remains active and
awaiting acceptance. The separate acceptance gate still blocks accepted-code
activation unless the existing explicit process-refresh policy preserves pending
acceptance. Fresh missing bindings, present-but-conflicting projections and live
ownership remain fail-closed. Stopped-runtime refusals include the bounded census
`reason` in the CLI error instead of discarding it at the bootstrap boundary.

Low-level/legacy tools may still exist in compatibility or non-smart modes, but new agent workflows should prefer the compact smart surface.

## 4. Authority, EOCL, routing, and handoff

`agent_workflow` is the primary end-to-end coding path. Mutation/proof workflows are governed by the EOCL state machine and durable orchestration ledger. A successful command or green test does not by itself equal final acceptance; an `ACCEPTING` wave still requires the authorized semantic controller to accept or reject it.

Bounded RUN continuation has two explicit consent adapters over the same exact descriptor contract. The embedded Electron ChatGPT view can stage its existing one-shot DOM-observed command receipt. An attested external ChatWeb controller that cannot produce that Electron event instead receives a short-lived loopback approval URL: its fragment token is process-local and absent from HTTP request targets/logs, the page renders the exact RUN/WAVE/workspace/epoch/fingerprint/scope/check/budget terms, and an explicit local button press grants and starts only that continuation. The endpoint rejects forwarded/tunnel-shaped traffic, controller transfer, runtime or WAVE drift, expiry, and replay. Neither a generic visible turn nor a copied descriptor grants background authority, and final acceptance remains controller-owned.

For a selected read-only review, `agent_workflow(phase="prepare")` also accepts an optional `committed_review` object. It requires exact local 40-hex base/head commits, computes an explicit local merge-base range, disables external diff/textconv and system/global attributes, bounds and redacts returned evidence, and signs any continuation to the immutable range. It adds no ninth MCP tool, cannot run in a mutation/resume phase, does not fetch history, and does not itself establish execution or acceptance evidence.

For ordinary context collection, `agent_workflow` phase `prepare`/`run` exposes the existing bounded context controls and forwards them unchanged to `prepare_coding_context`. The public `smart-v3` surface remains exactly eight tools; this does not create a second index or authority.

The split `prepare -> execute` path is explicitly lineage-bound. `prepare` returns `prepared_binding.run_id` and `prepared_binding.wave_id`; callers should pass both values to `execute`. The runtime requires the pair to match the caller-scoped current `PREFLIGHT`/`READY` prepare lineage and fails closed before creating a new RUN or write lease when a refined execute objective omits or mismatches that binding. The prepare RUN objective remains the immutable authority; an execute objective is only a narrower implementation plan.

Current authority rules:

- ChatWeb/Sol remains the normal semantic controller and final-acceptance authority for coordinated work.
- Electron/Recovery Host owns service lifecycle and secrets.
- Coding Tools MCP owns deterministic workspace mutation, verification, durable task/run/proof state, and write fencing.
- Codex Desktop is a second client of the same Runtime through the thin proxy; controller transfer is explicit and does not automatically grant a repository write lease.
- Codex App Server and OpenCode are secondary lanes, not an independent authoritative writer of the primary checkout.

### Routing policy currently in force

Supported explicit routes include `deterministic`, `mini`, `luna`, `terra`, `sol_xhigh`, `sol_max`, and `sol_ultra`. However, **`execution_route=auto` is currently fail-closed to `deterministic`** while representative accepted paired evidence is insufficient. The runtime reason is the ROI/evidence gate, not an inability to invoke the other routes.

Consequences:

- do not describe Mini/Luna/Terra/Sol as automatically selected in production today;
- non-deterministic lanes are explicit/evaluation lanes until the accepted representative cohort gate changes;
- `sol_max` and `sol_ultra` still require explicit high-cost acknowledgement;
- provider traffic/capacity telemetry does not itself authorize automatic routing;
- OpenCode automatic routing remains off/evidence-gated;
- automatic global server-first compute placement remains off until representative P3 evidence supports promotion.

Auto-handoff is also kept off until enough representative real-task A/B evidence shows a stable benefit without state loss or duplicate work. Durable handoff capsules remain available for rollover/recovery.

## 5. Runtime evidence and measurement

For repository-local evaluation and postmortems, the durable orchestration ledger is the canonical causal source:

```text
.coding-tools/orchestration/ledger.sqlite3
```

Supporting projections include `.coding-tools/performance.json`, `.coding-tools/task-history.json`, and `.coding-tools/task-state.json`. These are runtime evidence, not source-code inputs, and must not be folded into source/worktree fingerprints.

Current measurement policy:

- distinguish provider-reported/measured tokens, cost, and timing from estimates;
- never present internal estimated credits as provider billing;
- keep representative, benchmark, and synthetic evidence separate;
- do not promote routing or placement from small or synthetic samples;
- host-visible latency claims require an explicit host observation bound to the exact EOCL run/wave, not timestamp proximity.

### Accepted-Result Economics measurement layer

The current source adds a read-only Accepted-Result Economics layer on top of the existing canonical ledger and performance projection. Its operating North Star is:

> **Minimize Accepted-Result Economic Loss under fixed quality, security, authority and correctness floors.**

The decision order is deliberately lexicographic rather than a single blended score:

```text
quality floor
  -> first-pass outcome
  -> restricted TTAR p90
  -> accepted-result resource cost
  -> human/operator burden
  -> simplicity
```

`npm run report:accepted-result-economics` is read-only. It reports accepted deterministic representative runs, bounded retained per-run resource telemetry, first-pass versus repaired resource distributions, top-tail workflow forensics, proof-cache economics, monetary/token coverage, and an exact-HEAD DRE window for `source_base_drift` and `acceptance_correction`.

Evidence semantics are fail-closed:

- missing money/tokens/resource observations remain **unknown**, never zero;
- monetary CAR remains unavailable until accepted-result monetary-cost coverage is complete;
- `estimated_wait_ms` is the capped gap between consecutive MCP tool calls and may include controller/model/network/operator time; it is **not** proven avoidable loss and is **not** provider billing;
- bounded `performance.run_metrics` retention means an observed resource subset is descriptive and its coverage must be reported rather than silently extrapolated to every accepted run;
- historical DRE counts identify mechanisms, but only natural accepted work on an exact clean current source revision may justify another current hardening wave;
- a low proof-cache hit rate is measurement evidence, not by itself a reason to build a new cache architecture.

P5 source now carries the same economics boundary. Promotion requires accepted-result resource economics and resource-overhead noninferiority; monetary-cost noninferiority is required when complete monetary coverage exists. No missing cost is converted to zero and no partial resource vector is relabeled as monetary CAR. P5 remains explicit, gated, arm-neutral before assignment, and non-automatic.

The current host-observation path uses content-free identities (`turn_id`, `trace_id`, `span_id`) and explicit run binding; prompt/response text is not copied into the correlation record.

## 6. P0-P3 closure and evidence boundary

The P0-P3 program is no longer one undifferentiated implementation gate. Engineering closure, live activation, and representative efficacy are tracked separately so an evidence program cannot silently reopen accepted architecture and a source fix cannot be mistaken for a running-process acceptance.

| Phase | Engineering/source | Live / evidence boundary | Current interpretation |
|---|---|---|---|
| P0 — runtime truth/error boundary | **CLOSED (source)** | **Historical live receipt; current connector discovery blocked** | ExceptionGroup normalization and self-recovery hardening are implemented. The 2026-08-18 connector acceptance is retained as `VERIFIED_SNAPSHOT`; the current process still requires its own real-client `tools/list` or `server/discover` receipt before connector acceptance can be current. |
| P1 — measurement integrity | **CLOSED** | **ECONOMICS DEFERRED** | Controlled plumbing is sufficient for experiments. Missing controller/provider usage or money remains unknown, never zero; it does not authorize automatic routing. |
| P2 — rework diagnosis | **CLOSED** | **CAUSAL EFFICACY DEFERRED** | The diagnostic phase identified rework as a material cost. Generic `CHECK_FAILED` and `BUILD_VERIFICATION_FAILED` observations now receive prospective, content-free stage/family detail; historic rows without that detail remain unclassified rather than being backfilled into a causal repair cause. Incomplete historical causal/oracle coverage is a measurement limitation for later experiments, not a reason to expand P2 architecture indefinitely. |
| P3 — compute-placement control | **CLOSED / ACCEPTED** | **REPRESENTATIVE EFFICACY DEFERRED** | Explicit placement control is implemented; the representative 10–20-pair pilot remains separate and global server-first stays off. |

The P0 **live activation acceptance** below was satisfied on 2026-08-18. The program may move to a new engineering roadmap item while P1/P2/P3 evidence programs continue in parallel without reopening their closed implementation waves.

### P4 — Solution Economics Shadow — SOURCE/GATE ACCEPTED / EVIDENCE COLLECTING

P4 engineering is now split into three explicit boundaries: source contract, live collection health, and empirical predictive readiness. Current source provides the shadow evidence path for `feature` and `bugfix` runs:

- one task-level recommendation is recorded before the first `write_lease_acquired` event;
- recommendation evidence is structured and content-free: candidate scope, estimated touched surface, root-cause confidence, oracle strength, expected repair risk, and smallest causal solution scope;
- the recommendation is joined after execution to durable accepted-result evidence including first-pass acceptance, repair/replan count, TTAR, accepted file receipts, proof duration, explicit local/wait observation spans, and explicit manual-fix outcome when available;
- lines/symbols touched, cost, wait, or intervention remain unknown when they were not actually observed; absent telemetry is never converted to zero;
- representative rows alone are eligible for predictive promotion; benchmark, synthetic, and unlabeled rows remain descriptive evidence only;
- predictive validation requires representative terminal outcome variation plus positive leave-one-out Brier gain and Bonferroni-adjusted Wilson interval separation; the result remains association evidence, not a causal treatment claim;
- LOC/touched surface remains an explanatory variable, not the optimization target.

P4 does **not** add another public MCP tool and does not change routing, model choice, compute placement, write authority, proof policy, acceptance authority, or production mutation behavior. `solution_shadow` is an action inside `task_control` on the existing eight-tool `smart-v3` surface.

The development supervisor has also been hardened so development Coding MCP launches are pinned to the current Electron checkout (`appRoot/resources/coding-tools-mcp`), with that module root first in `PYTHONPATH`, used as `cwd`, persisted as launch provenance, and mismatches refused rather than silently reusing a foreign/stale runtime.

The population/readiness window is fail-closed against unrelated run churn. `solution_shadow_population_report` now selects the latest enrolled shadow runs directly (`population_scope=latest_shadow_runs_v2`) instead of selecting the latest generic runs and filtering afterward. This prevents diagnose/telemetry workload from evicting genuine P4 evidence from the analysis window.

Repository operators can evaluate the canonical committed ledger with:

```text
python resources/coding-tools-mcp/scripts/report_p4_readiness.py --workspace .
python resources/coding-tools-mcp/scripts/report_p4_readiness.py --workspace . --require-ready
python resources/coding-tools-mcp/scripts/report_p4_readiness.py --workspace . --require-p5-experiment-active
npm run check:p5-readiness
```

The manual-only GitHub workflow `.github/workflows/p4-readiness.yml` exposes the P4 gate without enabling ordinary push/PR Actions consumption. `--require-ready` succeeds only when `p4_gate.can_answer_which_signals_predict_repair=true`; missing or insufficient evidence cannot be converted into a green P4 closure claim. `--require-p5-experiment-active` is an observation assertion for an already explicit P5 epoch, not an activation command. `npm run check:p5-readiness` and the deprecated `--require-p5-ready` retain the legacy P4-predictive treatment readiness meaning and must not be used to claim P5-A0 integrity readiness.

**The 2026-08-19 live collection receipt is historical (`VERIFIED_SNAPSHOT`), not a current P4 outcome.** At that snapshot the ChatWeb/Coding-VP plane exposed `task_control.solution_shadow`, exactly 8 `smart-v3` public tools, contract SHA `bd5c09aeffe02bb60d0f548ed02912e8a21e78b91404186e6896f6d6cbdedd70`, and no reported stale/orphan residue. A later process had a genuine rediscovery and official acknowledgement, but the newest target-process snapshot requires fresh real-client discovery again; neither receipt proves a current `solution_shadow` call or P4 outcome. Source support and later natural evidence remain separate gates.

The P4 empirical gate remains **COLLECTING unless the canonical ledger reporter says `EMPIRICALLY_COMPLETE`**. The 2026-08-19 snapshot (9 representative terminal shadow tasks, 0 representative causal-solution repairs, and `validated_signals=[]`) remains historical evidence that predictive validity was not established; it must not be reused as an activation proof for later source. P4-C therefore remains strict/shadow-only and P4-E remains coverage-first/advisory-only.

**Current P4 readiness (`VERIFIED_CURRENT`, descriptive) remains `COLLECTING`.** The immutable canonical-ledger report captured at `2026-08-29T14:19:17.492306Z` contains `99` representative terminal shadows: causal-solution repair `n=1`, nonrepair `n=72`, and repair-unknown `n=26`; raw post-replan patched observations were `n=26`. `validated_signals=[]`, `p4_empirically_complete=false`, and predictive-policy activation remains false. The source implementation exists, but the upstream-matched P5 baseline is not ready because code-bearing source is dirty. These imbalanced labels do not establish a prediction effect or causal intervention result. The current connector now has the attested current-process discovery receipt recorded above, but that connector pass is not a P4 outcome and does not authorize automatic policy, P5 treatment, or routing.

P5 has a separately gated **source implementation**: manifest v2, secret-handle seed commitment, pre-assignment arm-neutral eligibility/enrollment, restart-safe block randomization, immutable all-assigned ITT outcome rows, analyzer/source-identity checks, and pause/close/hard-stop controls are exposed as `task_control(action="p5")` inside the unchanged eight-tool `smart-v3` surface. A write-capable `agent_workflow` can carry `p5_assignment_id` only for the immutable `feature`/`bugfix` task class; after the ordinary workspace fence is acquired and before any mkdir/patch call, the runtime records an immutable P5 pre-write binding to the exact run, wave, and lease. Caller-supplied first-write time is rejected. The feasibility analyzer projects the complete durable funnel (`assessed → eligible → enrolled → assigned → protocol started → pre-write binding/first-write record → terminal → immediate quality → delayed follow-up/interference`) by assigned arm and workflow stratum. It verifies completed 2/2 block shape and exact table joins instead of pretending that a low-power canary SRM p-value proves randomization; completed-block mismatch, orphaned rows, arm crossover, or a write-binding/first-write mismatch hard-stops a live epoch. Incomplete live blocks are reported as pending, not claimed as imbalance. It does not loosen P4-C or require P4 predictive readiness before a P5-A0 instrumentation epoch. An operator must still explicitly open a frozen, source/runtime-matching manifest, with a clean upstream-matched control-plane source when the manifest requires it and with no active workspace write fence. `p5_automatic_start=false`, `automatic_policy_activation=false`, and automatic production promotion remain invariants. No source proof substitutes for a live P5-A0 A/A epoch, a P5-A treatment canary, an efficacy conclusion, or promotion.

For a development Electron runtime, the trusted parent process may receive `CODING_TOOLS_P5_A0_SEED` only from an external secret-delivery channel during a fail-closed controlled restart. The helper immediately writes that one-time value to Electron `safeStorage` under the `p5A0Seed` SecretStore entry; every normal start, primary-MCP recovery, controlled restart, and code activation reads that encrypted entry and maps it to the opaque `secret://experiment/p5/a` broker handle. Native launch deliberately omits the raw environment name from the child MCP environment and refuses to fall back to it when no SecretStore seed is present, so an incidental restart cannot change experiment identity. Do not place the raw value in the repository, tracked `.coding-tools` evidence, manifest, chat, or ordinary application settings; restart-safe live provisioning remains an operator/runtime operation, not source evidence. The MCP-only controlled-restart helper is fail-closed: it requires exact non-empty `--expect-app-root`, `--expect-workspace`, and `--expect-user-data` identities; binds its RuntimePaths to that verified development product root; then verifies the persisted `nativeDeviceId` and `nativeDeviceInstanceId`, before reading the secret store or terminating a runtime PID.

P5 source identity is the latest code-bearing commit of `HEAD` and upstream, excluding `.coding-tools/**`; evidence-only commits and live runtime projections remain mandatory Git history but do not create a false source-drift event. Any actual source-code commit still requires a new frozen P5 epoch before enrollment or assignment.

The P5-A0 operator path is intentionally narrow. The runtime can prepare a production A0 manifest only from the current code-bearing source/upstream identity, loaded eight-tool runtime contract, a material content-free environment fingerprint, the deterministic analyzer identity, and the SHA-256 commitment of `secret://experiment/p5/a`. `prepare_a0` is read-only and never opens an epoch. `open` rechecks source, runtime, analyzer, environment and writer quiescence, so a prepared manifest cannot be reused across environment drift. The production A0 horizon is four hours. Electron exposes only `status / prepare / open / analyze / pause / resume / close / hard-stop`; it keeps the prepared manifest in the trusted main process, never accepts raw seed material from the renderer, and exposes no P5-A treatment activation control. This remains shadow A/A instrumentation: both assigned labels receive the current control protocol and no automatic routing or promotion is enabled.

### P0 historical live activation incident — source CLOSED / prior receipt accepted

During an earlier 2026-08-18 closure check, every ChatWeb Coding MCP action attempted through that connected tool surface (`workspace_context`, `task_control restart_runtime`, and `agent_workflow`) returned a raw `ExceptionGroup: unhandled errors in a TaskGroup` before a normal typed tool result could be observed. The incident and the later acceptance are historical evidence for that source/runtime instance; neither establishes the identity or connector state of the current process.

Two source-side gaps are now addressed:

1. The MCP protocol boundary normalizes an `ExceptionGroup` into typed `ASYNC_TASK_GROUP_FAILED` JSON-RPC evidence instead of stringifying the raw group.
2. Recovery Host now has a throttled **semantic tool-plane watchdog**. It first performs a bounded five-second HTTP health preflight, then performs a read-only local `workspace_context` canary only when that health receipt is ready and reports no active command or snapshot contention. A transiently unavailable HTTP health response, or an MCP that is already serving work, skips the semantic canary and clears its semantic-failure streak instead of converting liveness uncertainty into a restart. Three consecutive eligible semantic failures are required before component-scoped MCP replacement. Recovery still delegates only through the existing `RuntimeOrchestrator.restart({ automatic: true })` lifecycle authority, and the watchdog is suppressed while the lifecycle controller is busy, recovering, handing off, or manually stopped. The canary does not create a second writer or recovery authority.

Focused source regression proves the semantic canary accepts a real `workspace_context` response, rejects an HTTP-200 raw TaskGroup JSON-RPC failure, skips while HTTP health is temporarily unavailable or the runtime is busy, restarts only after the three-failure threshold, and does not restart while the lifecycle controller is busy.

**Historical live acceptance (`VERIFIED_SNAPSHOT`).** On 2026-08-18 the then-connected instance demonstrated the accepted behavior on the real tool path:

- delivered/source HEAD `0cf1eec7366f09d52235ca235d92ccd8b3ea4e18` contains `beb2dc51` (protocol normalization) and `c7841920` (boundary regression) in its ancestry;
- the primary Coding MCP process observed as PID `18444` was created at `2026-08-18 15:28:53 +07:00`, after both P0 source commits, and runs `E:\DEV\Codex-web\resources\native-python\pythonw.exe -m coding_tools_mcp --workspace E:\DEV\Codex-web`;
- `workspace_context(detail=full)` succeeds through the real connector and reports the current source identity plus live `process_instance_id` / `server_instance_id`;
- `agent_workflow` prepare succeeds through the same live tool plane;
- `task_control` audit succeeds with hash-chain integrity PASS and quiescent execution resources;
- the live `smart-v3` contract reports exactly 8 public tools;
- focused ExceptionGroup boundary regression passes `4/4` from the Coding MCP component root;
- no raw `ExceptionGroup` escaped any of the live acceptance calls;
- the live runtime reported zero stale orchestration runs, unresolved stale runs, orphaned background operations, and orphaned idempotency records.

No Runtime restart was performed for this acceptance. A restart was unnecessary because the observed primary Coding MCP process itself started after the accepted P0 fix commits and then passed the live checklist. Future runtime-affecting changes still require their own source-versus-live activation proof; this acceptance does not collapse that distinction.

### P3 Engineering / Control Plane — CLOSED / ACCEPTED

The explicit validation compute-placement implementation is accepted at source commit `2c990332` (`feat: control validation compute placement`). P3 engineering is no longer a semantic roadmap blocker.

Accepted behavior:

- `compute_placement_policy = local_only | server_preferred` is available only for eligible long structured `cargo_check` / `cargo_test` validation.
- Explicit placement requires an Agent-backed project, no sandbox, structured asynchronous validation support, and a clean exact-source Runner checkout.
- Invalid explicit contexts fail closed before enqueue/process execution.
- `local_only` keeps execution on the source Runner and never selects server compute.
- `server_preferred` uses exact-source target selection and revalidation; if no valid target remains, execution safely falls back to the source Runner.
- Placement evidence records requested policy, actual placement, fallback, source Runner and executor Runner and is preserved through Job metadata, handoff/terminal result, `job_status`, and `job_log` projection.
- Omitting the selector preserves the established production behavior, including the pre-existing dirty-snapshot auto-offload path.
- Focused R3B2 integration regression covered server dispatch, local-only source execution, safe fallback, invalid-context pre-enqueue rejection, evidence projection, and selector-absent regression behavior before acceptance.

The preregistered analyzer remains frozen under the identity recorded in `docs/research/260818_P3_SERVER_FIRST_PAIRED_EXPERIMENT_MANIFEST.md`. Existing pilot outcomes must not be reinterpreted under an edited analyzer without a new manifest/version.

### P3 Representative Efficacy Pilot — DEFERRED

The frozen experiment `p3-server-first-pilot-v1` targets **10–20 genuinely eligible representative paired tasks**. Its purpose is instrumentation/variance/failure-mix/break-even/power planning before any confirmatory promotion claim.

This evidence program is intentionally separate from the engineering completion gate:

- it does not block moving to another engineering roadmap item after P0 live activation acceptance;
- it does not authorize claiming server-first is faster, cheaper, or better;
- it does not auto-promote global server-first;
- automatic activation remains `false`;
- missing controller/provider monetary cost is unknown, never zero;
- a confirmatory cohort is still required before broad promotion.

## 7. Recovery architecture

Persisted MCP/Tunnel PIDs are not live ownership proof across reboot or profile
migration. Stopped-runtime activation census and primary/Recovery service
lifecycle compare each PID with its OS process-start token. A verified different
token means the stored process has exited; census remains read-only and service
cleanup clears only the unchanged stale receipt, without adopting or terminating
the unrelated replacement PID. Missing tokens, malformed observations and
unavailable identity probes still fail closed. Device-ownership checks and legacy
Recovery migration apply only after the exact stored process is proven live.
The canonical ledger and durable history are never cleared to recover a PID.

Independent recovery is no longer only a roadmap concept. The current source contains:

- a headless Recovery Host that owns primary Runtime/Tunnel/Execution-Hub lifecycle;
- a Windows user-session Recovery Supervisor that resurrects the Recovery Host under bounded, fail-closed rules;
- a separate Recovery MCP process and, when configured, a separate Recovery Tunnel;
- a semantic Coding MCP tool-plane watchdog that can distinguish control-health success from failed `tools/call` behavior and delegates restart to the existing orchestrator;
- `recovery_plane_mode=independent_mcp_tunnel_v1` state;
- bounded `recovery_status` / confirmed `repair_primary_runtime` behavior rather than arbitrary remote shell/process control;
- controlled component activation and accepted-code activation gates.

The Recovery Tunnel must use a distinct tunnel identity from the primary Coding Tunnel. If a second tunnel resource is not configured, the independent local Recovery MCP may still exist while remote Recovery Tunnel status remains `not_configured`.

Development-startup note: the current checkout intentionally writes a bounded
`%LOCALAPPDATA%\\WebMcpRecoverySupervisor\\stop.request` sentinel only before an
actual development Recovery Host retirement/handoff or missing-host spawn when
the installed development Supervisor is not proven to match the current
app-root/executable identity, so another checkout cannot resurrect the wrong runtime.
Attaching an Electron UI to the already healthy exact-checkout Host must not
write this sentinel. The sentinel is operational suppression, not a health
result and not evidence of `blocked_live_owner`. After a development handoff,
re-enable supervision only through the supported
`npm run recovery:supervisor:install` installer for the exact current checkout;
it refreshes the installed script/manifest identity and removes the sentinel.
Packaged supervision has a separate installed identity and is not affected by
this development-only guard.

Implementation in source is not the same as a packaged/live proof. Recovery changes still require the relevant process-boundary, activation, packaged-Windows/login, and fault-matrix acceptance appropriate to the change.

The current checkout also has a repeatable isolated packaged-Windows Recovery lane: `npm run test:recovery:packaged`. It builds `dist/win-unpacked`, launches the packaged `--recovery-host` under a temporary Electron user-data root, proves device identity plus independent Recovery MCP, exercises the packaged Recovery Supervisor in healthy and fail-closed fault cases, cleans only isolated PIDs, and verifies that the production Recovery descriptor identity is unchanged. This is packaged runtime evidence, not publication of an installer and not a substitute for an actual installed-logon/session smoke when that boundary is required for release.

## 8. Semantic localization and LSP resource policy

Coding Tools MCP uses semantic-first localization when the native WebCodex LSP provider is available and falls back to bounded text search per query when semantic localization is unavailable, denied by resource admission, or cannot handle a query.

The current worktree also contains LSP process telemetry/resource-governance work: process instance identity, PID/start identity, current and peak working set, pending-request state, memory-pressure classification, restart/drain counters, bounded idle reaping, and soft/hard pressure behavior. Pressure policy is internal and testable; it must not be documented as one universal production memory number derived from a historical sample.

The P2/P3 LSP/resource hardening was technically closed on 2026-08-16. Its 10-cycle real Connector/Runner/rust-analyzer acceptance window recorded distinct process identities for every cold restart, final `STOPPED`, zero active HEAVY claim/write fence/stale run/orphan/overlap, and p95 peak LSP working set below 30 MiB on that Windows host. This host-scoped sample supports keeping the existing 2 GiB/3 GiB soft/hard defaults; it is evidence for that acceptance window, not a universal memory guarantee.

## 9. Validation, security, and release boundary

For ordinary changes, validate only the behavior changed. The current top-level entry points are:

```text
npm test
npm run test:mcp
npm run test:all
npm run test:recovery:e2e
npm run test:recovery:packaged
npm run canary:opencode-flash:preflight
npm run dist
npm run dist:dir
```

The paid/real provider canary `npm run canary:opencode-flash` may create external provider cost and must run only with explicit authorization for that cost. Its `:preflight` variant performs readiness validation without provider dispatch.

Runtime-affecting source changes need a separate activation/instance check after source tests. A release claim needs source proof, required live/process proof, exact accepted fingerprint, packaging checks, and rollback guidance appropriate to the component.

Account credential snapshots under `docs/ac/` are local-only data and must never be tracked. They have been removed from the current `main` tree and `/docs/ac/` is ignored. Credentials that were previously committed must be treated as exposed and rotated/revoked. Purging them from existing Git history is a separate destructive history-rewrite action and is not implied by ordinary cleanup commits.

## 10. Known evidence gates that remain intentional

The following are deliberate evidence/authority gates, not documentation bugs:

- P0 source activation and multi-workspace control plane: source implementation and earlier live receipts are retained, but no static documentation line is a current-process `LIVE_PASS`. The current local verdict is authoritative only when a fresh Recovery Host projection for the exact accepted checkpoint reports `closure_state=LIVE_CLOSED`; even that verdict is local runtime/control-plane evidence, not a package, release, deployment, or production claim;
- automatic non-deterministic routing: **OFF / deterministic fail-closed** pending representative accepted paired evidence;
- automatic global server-first: **OFF** pending representative compute-placement evidence;
- P3 representative efficacy: **DEFERRED**, separate from the closed engineering gate;
- P4 source/gate engineering: **ACCEPTED**; development launch authority is pinned to the current checkout and `solution_shadow` schema publication has been observed;
- P4 live tool-call health: the 2026-08-19 `solution_shadow` call remains **VERIFIED_SNAPSHOT**. The current target process requires a fresh discovery receipt before its connector status can be promoted, and P4 collection remains unobserved until a natural task actually records a P4 outcome;
- P4 predictive validity: **COLLECTING unless `report_p4_readiness.py` reports `EMPIRICALLY_COMPLETE`**; benchmark, synthetic, and unlabeled shadow rows are not promotion evidence;
- P5 experiment integrity source: **IMPLEMENTED / FAIL-CLOSED.** A prior explicit P5-A0 epoch was closed transparently with zero enrollment, assignment, write binding, or outcome when the Wave 3 funnel gap above was discovered; it is evidence of operator/seed/manifest control only, never A/A health, treatment feasibility, or efficacy. `task_control(action="p5")` validates a frozen manifest, source/runtime identity, secret-backed seed commitment, assignment/enrollment order, and the absence of an active workspace writer before opening a rebaselined epoch. P5-A0 may be explicitly opened for instrumentation before P4 predictive completion; P5-A treatment remains separately gated by its own registered manifest, natural eligible task/oracle funnel, and explicit operator authority. Neither starts automatically, and neither is a production-promotion signal;
- auto-handoff: **OFF** pending more real A/B evidence;
- paid Flash terminal reproduction: **requires explicit external-cost authorization**;
- provider/model write authority over the primary checkout: **not granted by telemetry or routing alone**;
- ChatGPT context-pressure percentage: **unknown unless the host exposes a real source**; do not fabricate one.

## 11. Historical WebCodex material

WebCodex core documents, Rust crates, server/runner deployment material, and dated research remain useful and should not be deleted merely because the desktop product has moved further. Their scope must be explicit. When a historical plan says something is future work but current source now implements it, preserve the historical record and update this current-state document or the maintained product guide instead of rewriting chronology.

## 12. Current exact-file EOCL acceptance and live recheck — 2026-08-31

The bounded EOCL wave `f8bb0fcf65a94e929b600b67e0413e6a` /
`52e3d5abc9c247ea945a9e7089ba5254` reached `CHECKPOINTED` and received final
ChatWeb operator acceptance at checkpoint
`95468d1606764d768151ea1b047381e3`. The checkpoint is bound to base HEAD
`a357e1bb45a68cfaf25b8a2aa99a133ab256102c`, worktree fingerprint
`2878151e13221a8c6c9f6f8506b25c30b29d083e9b1f5435883452e508f77413`, and
canonical checkpoint proof fingerprint
`a77efcee64e4503ce7ff2519b6c5c2811ef7d4ede07945b4bb6caae9897b9dc5`.

The exact accepted-file receipt is complete (`schema_version=2`, `count=3`)
and contains only these component-owned existing files:

| Path | SHA-256 | Size (bytes) |
|---|---|---:|
| `electron/services/recoveryActionStore.js` | `18c6a2b99ed2535324f0547030c2b65c4c573d98d6d6ff1846a0002812d4bdbf` | 75717 |
| `electron/services/recoveryHost.js` | `8ed02caf81f451c9c78c9e4cffeb8a916c8c472985b778f4e674435a9a9072d0` | 130667 |
| `resources/coding-tools-mcp/coding_tools_mcp/tool_schema.py` | `fd21ea595592388abb62dca6b4cb89db8dd8b52b7d25498c2c19bbb9cca53ecd` | 68738 |

Five focused deterministic proof stages passed, with no source edit in this
wave; the wave adopted exact bytes already present in the authorized worktree.
The earlier checkpoint `9411d3aec777422c89b25ef4837da86f` remains immutable and
is not widened retroactively. This therefore closes exact-file EOCL acceptance
for the three listed files only. It is not a single accepted packet for every
code-bearing file currently dirty in the Coding MCP component.

A fresh read-only runtime recheck at `2026-08-31T05:19:22.575Z` reports
Electron UI and Coding MCP `CURRENT`, `running_revision == disk_revision`,
`components_ready=true`, `fully_ready=true`, `runtime_update_incomplete=false`,
and `error_code=none`. The connector is
`CURRENT_COMPATIBLE_ACKNOWLEDGED` through the managed-attested
`compatible_activation_bootstrap` path, with
`connector_rediscovered=false`, `connector_refresh_required=false`, and
`connector_ack_pending=false`; no strict `tools/list` or `server/discover`
receipt is claimed.

The immutable query-only lifecycle census at `2026-08-31T05:19:30.478Z`
reported SQLite schema `12`, `integrity_check=["ok"]`, zero foreign-key rows,
`projection_drift=false`, `mutated_canonical_ledger=false`, zero managed jobs,
zero unexplained active runs and zero unbound live resources. It also observed
nine ordinary active RUN rows: seven `THRESHOLD_SENSITIVE_STALE_CANDIDATE`, one
`GRACE_PERIOD_INACTIVE`, and one `AWAITING_ACCEPTANCE` (`275a340f190e43ffb7feeb47a0698109`).
They have no live ownership, but the stale candidates are below the current
86400-second threshold and the awaiting-acceptance row lacks a safe exact
acceptance packet. None may be force-reconciled or accepted blindly.

Accordingly, current local runtime readiness and the three-file EOCL checkpoint
are closed, while the full-component accepted baseline/P0.6, natural Golden HR
outcomes, prospective efficacy, commit, package/release, deployment and
production gates remain open. No restart, commit, push, package, release,
deployment or production operation occurred in this recheck.
