# Current Project State — Tools-Codex-web

> **Status date:** 2026-08-26
> **Desktop package:** `coding-tools-mcp 1.0.0`
> **Purpose:** canonical operational snapshot for the current repository. This is not a release note and does not imply that every source change has been activated, packaged, or released.

## 1. Source of truth and document precedence

When repository documents disagree, use this order:

1. **Current implementation + focused tests + live runtime contract** for the exact checkout being operated.
2. **This file (`docs/CURRENT_STATE.md`)** for the current product boundary and operating policy.
3. `README.md`, `docs/ARCHITECTURE.md`, `docs/RECOVERY_HOST.md`, `docs/TESTING.md`, `docs/ROADMAP.md`, `docs/RELEASE_CHECKLIST.md`, and `SECURITY.md` for maintained product guidance.
4. `docs/MODEL_EXECUTION.md` and `docs/agent/*` for the WebCodex core/subsystem they explicitly describe.
5. Dated files under `docs/research/*` as historical evidence, plans, benchmarks, and decision snapshots. They do **not** override later source or this current-state document.

A source implementation can be newer than the process currently running. For Electron, Recovery Host, Coding Tools MCP, and other supervised components, distinguish **source present**, **focused proof passed**, **EOCL accepted**, **controlled activation completed**, and **packaged/released**.

Development startup has two explicit contracts. `npm start` (and its alias `npm run dev:refresh`) is the operator full-system refresh: it authenticates the current Recovery Host, creates a durable `full_clean_refresh` activation epoch, replaces Recovery Host, Coding MCP/Tunnel, configured Recovery MCP/Tunnel and Electron UI, then verifies fresh process identities, matching revisions and epoch binding. It never deletes durable truth; it fails closed if ownership, canonical ledger state or postflight cannot be proven. `npm run dev` inspects the authenticated Recovery Host receipt for this exact development installation, classifies Electron UI as `CURRENT`, `STALE`, or `MISSING`, uses component activation for a stale UI, launches a missing UI, and succeeds only after `running_revision == disk_revision` is observed with PID/instance/mode metadata. Stale code activation remains authorized only from an eligible accepted closure checkpoint. `npm run dev:stop` suppresses UI watchdog recovery and asks the exact registered single instance to quit while preserving Recovery Host, MCP, and Tunnel. It refuses an initially unavailable Recovery Host and reports success only after that exact host reports the UI `MISSING` or the previously bound PID is proven dead; transient host loss is not stop proof. `npm run dev:replace` applies the same exact-instance stop postflight, then relaunches and verifies a different UI instance. Connector discovery/ACK remains a separate gate; a refresh does not invent a connector receipt or open admission early.

The Command Center exposes loaded-source status for the three revisioned components—Electron UI, Recovery Host, and Coding MCP—and reports Tunnel health separately as `READY` or `STOPPED`. `CURRENT` is process/revision evidence only and never derives from Tunnel availability; it is not EOCL acceptance, release, deployment, production, or SLO proof. A source-update notice remains visible whenever a running component revision differs from disk.

The five-second Electron heartbeat is a read-only consumer of the latest completed Recovery Host supervision projection; it does not launch a second MCP/Tunnel/Git/OS-identity census. Recovery Host publishes the projection source, observation timestamp, age, busy flag, and freshness state, while Electron keeps heartbeat publication single-flight. Missing or older-than-30-second telemetry is `UNKNOWN/WARN` and appears yellow while retaining the last receipt for context; it is not evidence that MCP, Coding Tunnel, or Recovery Tunnel has stopped. Red is reserved for a confirmed stopped/error state or a deterministic `blocked_*` Recovery condition. This presentation rule does not weaken lifecycle recovery thresholds, process-identity checks, activation gates, or aggregate `fullyReady` semantics.

### Accepted-to-live activation closure

The supported development closure is `ACCEPTED/CHECKPOINTED -> ACTIVATABLE -> controlled component activation -> schema-v2 component postflight -> LIVE_CLOSED`. Each activation is authorized by one exact, non-normalized five-field `source_checkpoint`: `checkpoint_id`, `run_id`, `wave_id`, `proof_fingerprint`, and `git_head`. The Coding MCP preflight must return `ok=true`, `code=ACTIVATABLE`, and the same five values; partial, trimmed, case-folded, or otherwise reconstructed identities are not authority.

A schema-v2 postflight is accepted only when its operation, component, checkpoint lineage, expected/running/disk revision, instance transition, timestamps, health result, and fresh post-cancel lifecycle decision all verify. That final lifecycle decision must come from a new immutable, query-only SQLite Backup-API snapshot with `integrity_check=["ok"]`, zero foreign-key rows, valid physical/logical SHA-256 values, the exact operation/checkpoint, no fence, and zero blocking lifecycle counts, unexplained active RUNs, or unbound live residues. A contradictory `clean=true` flag cannot override those facts; the same lifecycle rule applies when an accepted checkpoint affects zero runtime components.

`LIVE_CLOSED` means only that this exact accepted local source is loaded and locally ready under the verified lifecycle and connector contract. Its projection deliberately remains `release_state=NOT_RELEASED` and `production_state=NOT_CLAIMED`. Connector continuity is separate: persisted SHA equality alone is not process-freshness proof for a new full-clean epoch. Freshness is satisfied either by current-process `tools/list` / `server/discover` followed by official Recovery Host acknowledgement, or by the admission-closed, no-workspace compatibility bootstrap for an exact declared predecessor/current SHA. That bootstrap is accepted only from the real ChatWeb `workspace_context` call, is bound to the current contract/process/server/activation epoch, returns `completed=false`, `retryable=true`, and `workspace_accessed=false`, and is recorded separately from discovery and ordinary successful tool contact. The first exact bootstrap receipt is immutable for that process/server/epoch boundary, so connector retries cannot advance its timestamp after Recovery Host has durably acknowledged it. Its acknowledged state is `CURRENT_COMPATIBLE_ACKNOWLEDGED`; it never sets `connectorRediscovered=true` or invents a rediscovery timestamp.

### Operational recency override — 2026-08-27

The maintained execution tracker at [`research/260823_CODING_WEB_GATE0_PRL_IMPLEMENTATION_AND_VALIDATION_TRACKER.md`](research/260823_CODING_WEB_GATE0_PRL_IMPLEMENTATION_AND_VALIDATION_TRACKER.md) is the current operational receipt for volatile lifecycle, connector, PRL, and packaged-harness claims. It supersedes older uses of “current”, “active”, or “accepted” in this document when those terms describe a live process or connector rather than a source implementation.

- The checked-out baseline is `main @ f85082b7b016dfd20dc9c1f769362c9a9942cb61`. The current full-clean activation-closure and PRL v11 hardening waves are newer uncommitted source until an exact accepted checkpoint says otherwise. PRL now fails public caller-derived authority closed, records immutable non-code dispositions and checkpoint-bound reconciliation, reports revision-scoped clocks/intervals, and emits C4 receipt schema `2` with Backup-API snapshot identity plus independently rebuilt proof/checkpoint/bridge coverage. Neither a matched source revision nor a fresh runtime receipt is a package, installer, release, deployment, production, or SLO claim.
- Earlier P0/P4 connector acknowledgements and tool calls are `VERIFIED_SNAPSHOT`, not current-process authority. The current connector claim must be read from a fresh Recovery Host closure receipt under the unchanged-versus-changed SHA rules above; no persisted hash, generic tool call, or historical rediscovery timestamp may substitute for it.
- P5 anchors remain terminal and the earlier A0 source-drift epoch retains its truthful zero funnel. Volatile ordinary-RUN, managed-job, and residue counts are not frozen in this maintained source document: recapture them from one immutable `report_lifecycle_census.py` snapshot before activation or stale-run reconciliation, and use only the official exact-ID path for a genuinely eligible stale RUN.
- PRL-D and A2 remain `HOLD_NATURAL_EVIDENCE`; missing natural observations, TTPR, stage coverage, and measured money remain unknown rather than zero.
- The isolated P0.3 packaged Recovery lane is source/package-local evidence, not an exact-frozen release candidate, installed-session, reboot/logon, connector, or production claim.

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
and is revision-continuity guarded. Repeated semantic MCP failures replace only
the exact owned MCP PID while preserving Tunnel identity; the replacement is
stopped again if disk revision drifts across its spawn boundary. Operator
`restart`, accepted code/revision
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

The development `npm start` command treats exact process refresh completion and
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

Low-level/legacy tools may still exist in compatibility or non-smart modes, but new agent workflows should prefer the compact smart surface.

## 4. Authority, EOCL, routing, and handoff

`agent_workflow` is the primary end-to-end coding path. Mutation/proof workflows are governed by the EOCL state machine and durable orchestration ledger. A successful command or green test does not by itself equal final acceptance; an `ACCEPTING` wave still requires the authorized semantic controller to accept or reject it.

For a selected read-only review, `agent_workflow(phase="prepare")` also accepts an optional `committed_review` object. It requires exact local 40-hex base/head commits, computes an explicit local merge-base range, disables external diff/textconv and system/global attributes, bounds and redacts returned evidence, and signs any continuation to the immutable range. It adds no ninth MCP tool, cannot run in a mutation/resume phase, does not fetch history, and does not itself establish execution or acceptance evidence.

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

**Current P4 readiness (`VERIFIED_CURRENT`, descriptive) remains `COLLECTING`.** At the `2026-08-24T02:19:09.4513934Z` immutable ledger projection, there were `89` representative terminal shadows: causal-solution repair `n=2`, nonrepair `n=64`, and repair-unknown `n=23`; raw post-replan patched observations were `n=27`. `validated_signals=[]`, familywise/holdout validation was not evaluable, and predictive-policy activation remained false. These small/imbalanced labels do not establish a prediction effect or causal intervention result. The newest connector receipt is blocked pending current-process discovery; even a future connector pass would not be a P4 outcome or authorize automatic policy, P5 treatment, or routing.

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

Independent recovery is no longer only a roadmap concept. The current source contains:

- a headless Recovery Host that owns primary Runtime/Tunnel/Execution-Hub lifecycle;
- a Windows user-session Recovery Supervisor that resurrects the Recovery Host under bounded, fail-closed rules;
- a separate Recovery MCP process and, when configured, a separate Recovery Tunnel;
- a semantic Coding MCP tool-plane watchdog that can distinguish control-health success from failed `tools/call` behavior and delegates restart to the existing orchestrator;
- `recovery_plane_mode=independent_mcp_tunnel_v1` state;
- bounded `recovery_status` / confirmed `repair_primary_runtime` behavior rather than arbitrary remote shell/process control;
- controlled component activation and accepted-code activation gates.

The Recovery Tunnel must use a distinct tunnel identity from the primary Coding Tunnel. If a second tunnel resource is not configured, the independent local Recovery MCP may still exist while remote Recovery Tunnel status remains `not_configured`.

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
