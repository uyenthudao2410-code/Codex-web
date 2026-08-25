# Problem Resolution Lineage v11 — C4 canary and cohort-control protocol

This is the maintained operating protocol for the **Problem Resolution Lineage
(PRL) v11** instrument in the Windows Electron Execution Hub + Coding Tools MCP
product. It complements current source and focused tests; it does not replace
them, activate a connector, or authorize an experiment.

The strategic rationale and staged roadmap live in
[`../research/260825_CODING_WEB_PRL_RESOLUTION_DECISION_PROTOCOL_STRATEGIC_CRITIQUE_AND_OPTIMAL_ROADMAP.md`](../research/260825_CODING_WEB_PRL_RESOLUTION_DECISION_PROTOCOL_STRATEGIC_CRITIQUE_AND_OPTIMAL_ROADMAP.md).
The append-only operational receipt belongs in
[`../research/260823_CODING_WEB_GATE0_PRL_IMPLEMENTATION_AND_VALIDATION_TRACKER.md`](../research/260823_CODING_WEB_GATE0_PRL_IMPLEMENTATION_AND_VALIDATION_TRACKER.md).

## 1. Boundary and current non-claims

PRL v11 is an authority-safe measurement and continuity instrument in the
canonical `.coding-tools/orchestration/ledger.sqlite3`; it is not a ninth MCP
tool, a planner, a Resolution Compiler, a routing engine, or a second database.

The C4 canary checks whether a snapshot has mechanically usable PRL v11 data.
It does **not** create a task, problem, run, wave, host turn, annotation,
decision card, P4 record, RDP record, or trial assignment. A synthetic fixture
or a ledger row cannot be relabelled “natural” by the report.

| Claim | Required evidence | C4 does not establish it |
| --- | --- | --- |
| Source mechanics | Exact source + focused tests | It only reads a snapshot. |
| Loaded runtime / connector | Controlled activation plus target-client receipt | A disk snapshot is not loaded-runtime proof. |
| Natural-system integration | Authorized real problem through the full lifecycle | No workload is manufactured for the canary. |
| Measurement validity | Preregistered independent review and reliability results | Aggregate rows do not decide semantic identity. |
| C5 observation or C6 efficacy | Prospective cohort / preregistered controlled comparison | No RDP shadow, hard gate, routing, or promotion is enabled. |

## 2. Frozen C4 protocol surface

Before collecting a C4 cohort, record these versions in its receipt:

| Element | Frozen value | Change rule |
| --- | --- | --- |
| PRL schema | `11` | Requires the supported migration/activation boundary and a new source/runtime proof. |
| PRL event schema | `2` | Legacy v1 events remain preserved but policy-ineligible. |
| Identity codebook | `1.0.0` | Semantic change starts a new cohort or is explicitly stratified. |
| Action-kind codebook | `1.0.0` | Semantic change starts a new cohort or is explicitly stratified. |
| Cohort rules | `1.0.0` | Semantic change starts a new cohort or is explicitly stratified. |
| C4 receipt schema | `2` | A semantic measurement fix: a full-problem unit is now independently rebuilt from exact revision, criterion manifest/disposition, passed proof, accepted checkpoint, and provisional bridge evidence. |

Only a privacy, integrity, or measurement-defect hotfix may occur within a
cohort. Record the defect, the affected interval, test proof, and whether the
cohort was restarted or stratified. Do not silently edit the codebook to improve
a metric.

## 3. Annotation codebooks

### Problem identity v1.0.0

Classify using the stable user-level intended outcome, acceptance contract,
target/domain, and causal continuity — never attempt count alone.

| Label | Use when | Do not use when |
| --- | --- | --- |
| `SAME_PROBLEM` | Original intended outcome and acceptance contract are unchanged; new symptom/evidence may exist. | The user has materially changed outcome, target, or constraints. |
| `REVISION` | Same thread has an authorized material contract/constraint/target-outcome change. | A prior attempt merely failed. |
| `CHILD_DEPENDENCY` | A separate acceptance contract must be solved to unblock a parent. | It is only an internal implementation step. |
| `NEW_PROBLEM` | The user-level intended outcome is independent. | A new symptom remains inside the original contract. |
| `AMBIGUOUS` | Evidence cannot distinguish the alternatives. | A label is forced for denominator convenience. |

Annotators retain only an evidence reference and bounded reason code. They must
not retain raw prompts, transcripts, source, command output, credentials, or
personal/business data in the annotation record.

### Action kind v1.0.0

Record one **primary decision intent**. A secondary tag may be used only in
offline analysis; it does not enlarge the runtime schema.

| Action | Primary intent |
| --- | --- |
| `clarify` | Obtain missing user or contract information. |
| `diagnose` | Discriminate causal hypotheses. |
| `localize` | Narrow target or scope without changing target behavior. |
| `intervene` | Change behavior/state to address a causal mechanism. |
| `verify` | Test whether the acceptance/oracle is satisfied. |

The C4 review sample must include problem identity; exact link and
`work_origin`; transition authority; capsule privacy; criterion-to-proof
attribution; action kind; and timestamp authority. `false_split` and
`false_merge` are reviewer findings, not aggregate-ledger inferences.

## 4. C4 runbook

1. Record repository path, disk `HEAD`, capture time, source status, and the
   frozen versions. A dirty worktree is evidence to disclose, not a reason to
   rewrite ledger history.
2. Run the read-only reporter from `resources/coding-tools-mcp`:

   ```powershell
   python scripts/report_problem_lineage_canary.py --workspace E:\DEV\Codex-web
   ```

3. Archive only the content-free JSON receipt or its digest. The reporter
   creates one SQLite Backup-API copy, instantiates no canonical writer, and
   writes no problem event.
4. Require `status=C4_SOURCE_READY_AWAITING_NATURAL_CANARY` before enrolling a
   natural canary. `PRL_SCHEMA_INACTIVE` requires supported activation;
   `C4_INTEGRITY_BLOCKED` requires diagnosis/reconciliation; and
   `C4_MECHANICS_BLOCKED` requires repair of the exact source/proof/checkpoint
   bridge. Neither is repairable by editing a report.
5. Collect only authorized real problem events. `30–50` is a mechanics
   calibration range, never an efficacy threshold. Freeze versions before
   review, then calculate raw agreement, class prevalence, Cohen's kappa or
   Krippendorff's alpha as appropriate, disagreement matrix, and ambiguous rate.
6. State only the strongest result: source mechanics, controlled activation,
   natural integration, measurement validity, or internal efficacy. C4 can
   establish at most mechanics readiness plus a descriptive natural snapshot.

## 5. Receipt interpretation and stop conditions

Wilson intervals in this receipt describe mechanics coverage only; they are not
treatment effects and do not replace a preregistered error bound. Receipt v2
must report the immutable Backup-API copy's capture timestamp plus physical and
logical SHA-256 values, integrity/FK result, event chain, typed-capsule privacy
and revision-projection validity, exact revision binding, and independently
verified criterion-to-proof/checkpoint/bridge coverage. A nonempty manifest,
persisted fingerprint, or aggregate event alone is not completion evidence.

Stop or demote the protocol and write a typed blocker when a secret, personal
data, raw transcript, source payload, or private reasoning is proposed for
durable storage; a shadow/unknown authority changes canonical state; chain/FK/
capsule integrity fails; an unattested clock is proposed for policy or TTPR;
codebook/schema drift is unversioned; or false split/merge, burden, false-block,
or compliance bounds fail.

Do not proceed from C4 to C5 merely because a count has been reached. C5 needs a
separate prospective observation decision and remains shadow-only; C6 needs its
own preregistration, control, safety floors, allocation mechanism, and operator
authority.

## 6. Activation authority boundary

The guarded `v9/v10 -> v11` CLI is deliberately not a runtime controller. Its
`--runtime-stopped` argument is an attestation of a fact established by the
**target** Recovery Host; it is not evidence by itself and must never be guessed.

Before reconciling a durable operation or stopping a writer, the operator must
obtain a fresh, redacted Recovery Host receipt that proves all of the following:

1. the host is healthy and owns the Coding MCP process to be changed;
2. the runtime snapshot's configured workspace is the exact ledger workspace;
3. the MCP process/runtime identity is current enough to be the authority for
   that workspace, rather than merely a different live desktop instance; and
4. the lifecycle census and activation preflight are from a new immutable
   snapshot after any supported operation transition.

An otherwise healthy Recovery Host configured for another workspace is not a
fallback authority. Do not change that other workspace, stop its runtime, reuse
its connector receipt, or create a temporary `Runtime` merely to force a durable
row terminal. When the actual target MCP has no in-memory handle for a durable
`running` operation, only its owned recovery surfaces may record the operation
as `orphaned`: `task_control(action="operation", operation_id=...)` or the
runtime's own startup/workspace-recovery boundary after it has become the target
workspace authority. Both paths are canonical ledger transitions, not direct
SQLite maintenance.

Only after the fresh census is clean may the target owner stop its writer. The
operator then acknowledges the exact physical and logical snapshot digests to
the guarded CLI, performs the additive activation once, and separately proves
the restarted loaded-runtime and external connector boundaries. A disk v11
schema is not either of those later proofs.

## 7. Connector freshness is a real-client receipt

Connector freshness is intentionally narrower than MCP reachability. The loaded
runtime records a discovery receipt only when its `list_tools()` path is reached
by the real `chatweb` client. The receipt is bound to the current tool-contract
SHA-256, MCP process instance, and server instance; changing any of those makes
an earlier receipt stale.

A generic SDK/CLI client, direct HTTP request, a `tools/call`, an old persisted
acknowledgement SHA, or a caller-supplied `chatweb` label cannot satisfy this
gate. Before connector-facing acceptance, a fresh Recovery Host snapshot must
show all three conditions:

```text
connector_rediscovered=true
connector_rediscovered_at=<current-process timestamp>
connector_refresh_required=false
```

Only then may the Recovery Host's official acknowledgement operation persist
the contract acknowledgement. This connector receipt is still distinct from
C4's natural-system evidence and does not authorize C5 or C6.
