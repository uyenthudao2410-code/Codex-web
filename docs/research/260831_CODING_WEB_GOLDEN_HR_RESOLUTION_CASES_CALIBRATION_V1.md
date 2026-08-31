# CODING WEB — Golden HR Resolution Cases Calibration V1

## 0. Purpose and evidence boundary

This packet supplies the first bounded 5–10-case calibration set required by
the Revision 4 methodology. It does not backfill PRL events, manufacture user
confirmation, or turn an accepted technical wave into Trusted Resolution.

Observation snapshot:

```text
observed_at                  2026-08-31 (Asia/Saigon)
HR workspace                 E:\DEV\HR STA\HR
HR branch                    V_Finance
HR HEAD                      bb6d9b009a2d4c40463d51d409f780f2f5a80302
HR worktree                  dirty; pre-existing PFM source changes preserved
HR orchestration ledger      .coding-tools/orchestration/ledger.sqlite3
HR task continuity           .coding-tools/task-history.json
HR generated run reports     .coding-tools/orchestration/reports/run-*/
HR ledger schema             9
Revision 4 PRL availability  inactive on this historical ledger
canonical mutation           none from this calibration
```

The immutable Codex-web reporter therefore truthfully returns
`PRL_SCHEMA_INACTIVE` for the HR ledger. This document is a research/calibration
manifest over existing evidence, not a second canonical writer. A future
prospective cohort must create native Problem Revision/Frame/outcome events in
the current schema instead of importing these annotations as causal facts.

## 1. Calibration rules

Every case below has all Revision 4 fields, but fields may be `AMBIGUOUS` or
`UNOBSERVED`. In particular:

- `technical acceptance` proves only the exact RUN/WAVE and proof fingerprint;
- a live API, SharePoint, database, process, or rendered-path check may be a
  strong semantic/runtime oracle, but it is not automatically user outcome
  confirmation;
- an operator screenshot or explicit correction can reopen a same-contract
  case, but the persisted task objective is only an attested description of
  that counterevidence when the original media is not in this evidence packet;
- timestamp proximity, shared keywords, and a similar project code are not
  enough to link a RUN to a Problem Revision;
- hidden reasoning is not reconstructed;
- quantitative Framing Regret remains unavailable unless the availability time
  of material counterevidence and avoidable-work attribution are recorded on a
  common attested clock.

Outcome vocabulary:

| State | Meaning |
|---|---|
| `PROVISIONAL_EXTERNAL_PROOF` | Technical acceptance plus an external semantic/runtime receipt; no independent user confirmation. |
| `REOPENED_BY_USER_COUNTEREVIDENCE` | A later operator observation contradicts the technically accepted result under the same desired outcome. |
| `OPEN_TECHNICAL` | The exact implementation lineage is active/replanned/unaccepted. |
| `AMBIGUOUS` | Evidence cannot defend an exact link, frame transition, or final outcome. |
| `TRUSTED_RESOLUTION` | Reserved for authoritative outcome confirmation with a defensible bounded envelope; none of these historical cases qualifies. |

## 2. Case index

| Case | Natural user problem trajectory | Exact primary RUN/WAVE lineage | Current calibration outcome | Independent user outcome |
|---|---|---|---|---|
| GHR-01 | Project create/save failed through the real HR persistence path | `ac6950.../0bfd58...`, `16c1c9.../1488b8...` | `PROVISIONAL_EXTERNAL_PROOF` | `UNOBSERVED` |
| GHR-02 | Project master metadata did not reach the Finance hero | `6c9fb3.../8a99b3...`, then `a30269.../cf1a35...` | `REOPENED_BY_USER_COUNTEREVIDENCE` | `UNCONFIRMED` |
| GHR-03 | DA2201.1 settlement was summed as history instead of a cumulative snapshot | `dc6d5e.../f06e5a...`, `9fbd31.../c75e4e...`, then open follow-up | `REOPENED_BY_USER_COUNTEREVIDENCE` | `UNCONFIRMED` |
| GHR-04 | Personnel canonical create failed after source/schema appeared fixed because live runtime was stale | `93f428.../49a9a6...`, `42709b.../ae74b9...`, `985bb8.../e71e6a...` | `PROVISIONAL_EXTERNAL_PROOF` | `UNOBSERVED` |
| GHR-05 | Personnel-to-ManagingUnit representative relation was absent/mismatched | `01d2ca.../5d8f05...`, `38d20c.../4d10a4...` | `PROVISIONAL_EXTERNAL_PROOF` | `UNOBSERVED` |
| GHR-06 | Canonical IDs required a guarded zero-ambiguity production backfill | `e8ee43.../f1fa1e...`, `dbf948.../09ab12...`, `b89d4e.../4c1a5c...` | `PROVISIONAL_EXTERNAL_PROOF` | `UNOBSERVED` |
| GHR-07 | Finance hero/project status and dossier status saved or rendered from the wrong projection | `a8b10e.../e8b86e... -> 14c64c...`, `ba6535.../605c02...` | `OPEN_TECHNICAL` | `UNOBSERVED` |

This is a seven-case calibration set. It is not a denominator of seven resolved
problems: zero cases currently carry independent user-success confirmation in
the evidence packet.

## 3. GHR-01 — Project create/save through real persistence

### Problem Revision

```text
problem_id       GHR-01
revision         1
user_job         Create and update an HR Project with investor information.
desired_outcome  The real API/RBAC/SharePoint path persists and reads the data,
                 and a temporary smoke record/folder is removed completely.
revision_state   PROVISIONAL_EXTERNAL_PROOF
```

### Frame trajectory

| Frame | A* boundary | G invariants | H hypothesis / counterevidence | Decision delta |
|---|---|---|---|---|
| F0 | `POST /api/projects` response mapping and Projects list schema | No auth weakening; no silent investor-data loss; preserve unrelated work | A successful Graph create without expanded fields may be translated into HTTP 500; required investor/canonical columns may be missing | Move from UI/source speculation to real schema and API persistence proof |
| F1 | One-shot live CRUD harness through actual router/RBAC/SharePoint | Use a real active authorized account; self-clean temporary record/folder; no persistent auth bypass | Source proof alone cannot prove tenant persistence or cleanup | Run isolated create/read/update/read/delete and verify cleanup |
| F2 | Smoke-process lifecycle only | Product behavior/auth unchanged | A successful smoke could hang after cleanup and hide terminal truth | Bound server shutdown and require natural process exit |

### Exact execution lineage

| RUN | WAVE | State | Evidence role |
|---|---|---|---|
| `bd050e74aa39460fb042d6a030314f9a` | historical single wave | `aborted` | Source repair lineage; not used as final outcome proof |
| `ac6950cf81134b8f93d199d555d9ac30` | `95ba97931b7748c398d9bdf3255a6cb7` | `replanned` | First live-smoke attempt |
| `ac6950cf81134b8f93d199d555d9ac30` | `0bfd586b24a64a16a375fd60191efda6` | `accepted` | Live CRUD/RBAC/SharePoint/cleanup checkpoint |
| `16c1c9b85c324876a69a75745e4a0a24` | `1488b807a68b43d8b8ae973cee68846a` | `accepted` | One-shot smoke lifecycle/terminal-exit closure |

### Oracle and outcome

```text
code oracle          focused source tests and build
semantic oracle      read-back of created and updated investor/project fields
runtime oracle       actual projects router + RBAC + configured SharePoint
cleanup oracle       temporary list item and canonical folder absent afterward
user outcome oracle  UNOBSERVED
final classification PROVISIONAL_EXTERNAL_PROOF
```

The external live receipt is stronger than a unit test, but it is still a
controlled smoke initiated as proof. No later independent user-success receipt
is bound to this revision.

### Failure and friction classification

- Failure dimensions: `STATE`, `CONTRACT`, `ORACLE`, `CONTROL`.
- Necessary governance: real RBAC, canonical identity, self-cleanup, no auth
  weakening, exact live schema verification.
- Avoidable friction: the first source-level repair did not itself establish
  live persistence; smoke lifecycle initially lacked a clean terminal exit.
- Qualitative Framing Regret: `MEDIUM`; the live persistence oracle should have
  been selected earlier, but no defensible avoidable-work duration is recorded.

## 4. GHR-02 — Project master metadata to Finance hero

### Problem Revision

```text
problem_id       GHR-02
revision         1
user_job         See authoritative Project master metadata in the Finance hero.
desired_outcome  Investor, Bên A and Project Manager are resolved distinctly
                 without changing Finance identity, money, ledger or KPI facts.
revision_state   REOPENED_BY_USER_COUNTEREVIDENCE
```

### Frame trajectory

| Frame | A* boundary | G invariants | H hypothesis / counterevidence | Decision delta |
|---|---|---|---|---|
| F0 | Presentation overlay keyed by unique normalized project code | Project master wins only for shared nonblank display fields; Finance owns IDs/money; Investor and Bên A remain distinct | Finance display strings were stale or blank | Add canonical display-only overlay and regression |
| F1 | Actual Finance hero relation-resolution path | Resolve relation IDs through ManagingUnit/Personnel; blank/placeholder values cannot erase valid fallback | Operator later observed the live hero still showing missing metadata; earlier mapping existed in another workspace/path | Inspect and exercise the actual `getPfmProjectSummary -> live workspace -> hero` path |
| F2 | Current active workspace source and durable file receipts | Do not accept verification-only work with `modified_files=[]` | RUN `a302...` was SOL-rejected because tests/build passed without durable source receipts | Require an implementation/adoption wave bound to the active workspace |

### Exact execution lineage

| RUN | WAVE | State | Evidence role |
|---|---|---|---|
| `6c9fb3accdde48d3841da091b138b185` | `8a99b33b595f492c9cf97791640e21fa` | `accepted` | Live-path regression: Project fields reach Finance model while ID/money stay unchanged |
| `a302698864ab4824bad96f62e53e95af` | `cf1a3579467249c2886db8bf6a9cae75` | `active`, SOL-rejected at acceptance | Same desired outcome reopened by operator screenshot; verification-only wave lacked durable modified-file receipts |

Some earlier task-history entries reference implementation runs whose generated
run reports are absent from this HR checkout. Those links stay `AMBIGUOUS` and
are not promoted into the exact lineage table.

### Oracle and outcome

```text
technical oracle     accepted regression for the model path
counterevidence      operator-described live screenshot with missing hero fields
media receipt        not embedded in this calibration packet
user outcome oracle  UNCONFIRMED
final classification REOPENED_BY_USER_COUNTEREVIDENCE
```

### Failure and friction classification

- Failure dimensions: `BOUNDARY`, `STATE`, `WORKSPACE_AUTHORITY`, `ORACLE`.
- Necessary governance: preserve Finance-owned money/identity and fail closed on
  duplicate/unmapped project codes.
- Avoidable friction: a correct helper in one workspace/path was mistaken for
  current live-path convergence; verification without durable source receipts
  reached acceptance review.
- Qualitative Framing Regret: `HIGH`; counterevidence shows the initial frame
  omitted the actual rendered/live path. Quantitative time remains unavailable.

## 5. GHR-03 — DA2201.1 cumulative settlement and PFM projection

### Problem Revision

```text
problem_id       GHR-03
revision         1
user_job         See correct project-lifetime recognized/approved revenue while
                 retaining installment history and independent collected cash.
desired_outcome  Final settlement is a cumulative snapshot, not an extra row to
                 add over prior installments; active non-final projects remain additive.
revision_state   REOPENED_BY_USER_COUNTEREVIDENCE
```

The later multi-contract/settlement-scope requirement may be a clarification of
the same desired outcome or a genuine Revision 2. Historical evidence is not
strong enough to decide that contract boundary, so `revision_2_status` remains
`REVIEW_REQUIRED` rather than being inferred automatically.

### Frame trajectory

| Frame | A* boundary | G invariants | H hypothesis / counterevidence | Decision delta |
|---|---|---|---|---|
| F0 | Financial summary lifetime aggregation | Exact decimal arithmetic; preserve all detail rows; cash stays independent | Generic final-settlement resolver was missing/divergent | Implement and accept settlement snapshot semantics |
| F1 | Live PFM management projection and certified manifest stitching | Approved manifest coverage remains admission authority; period reads remain additive | Operator observed `697,015,751` after source proof, with `364,136,816` actual cash; live path used a different/persisted management projection | Move from generic summary code to `PfmManagementRefreshService` and live adapter |
| F2 | Native R2C final-settlement semantics inside approved coverage | Revenue amount derives from native ledger facts; no production literal/project hardcode | Additive certified chunks double-count a later cumulative settlement | Resolve latest eligible final-settlement application for period `ALL` |
| F3 | Settlement scope across multiple contracts/appendices | A settlement closes only its assigned scope; legacy unassigned rows never become project-wide override | Later natural work exposed a pump-station settlement versus main-package boundary | Introduce explicit scope metadata and require complete-scope coverage before project-wide replacement |

### Exact execution lineage

| RUN | WAVE | State | Evidence role |
|---|---|---|---|
| `dc6d5e918499484c9d138f0a370a6dc1` | `f06e5a4ec75c44d5a57d503c385c31e3` | `accepted` | Initial cumulative-settlement source/UI correction |
| `9fbd31f021a34fb4b995a2a2086cac12` | `7bcff0aec2a14829b832776e4a0ebf52` | `replanned` | Prompt-size failure before bounded implementation |
| `9fbd31f021a34fb4b995a2a2086cac12` | `c75e4e6235994b9c97fe32db7165a142` | `accepted` | PFM management certified-lifetime resolver and live-path regression |
| `31db048b841948309f17853c01e0a40e` | report absent | `waiting` in task history | Later live mismatch diagnosis; not exact acceptance lineage |
| `3a72d66423804ef0b5f0f85e6286f95c` | report absent | `waiting` in task history | Continued live projection diagnosis; link retained as `AMBIGUOUS` |
| `95069c054b994bb28b22ad727455fe61` | four historical waves | `active` | Settlement-scope correction; no accepted checkpoint as of observed snapshot |

### Oracle and outcome

```text
technical oracle     focused backend/frontend tests and accepted checkpoints
semantic oracle      exact settlement/cash fixture behavior
counterevidence      operator-described live DA2201.1 values after source proof
current scope proof  active/unaccepted
user outcome oracle  UNCONFIRMED
final classification REOPENED_BY_USER_COUNTEREVIDENCE
```

This is the clearest false-closure calibration case: technical acceptance was
real, but the user-visible outcome contradicted it and exposed both a live read
path gap and a later scope-model gap.

### Failure and friction classification

- Failure dimensions: `SEMANTIC`, `CAUSAL`, `STATE`, `ORACLE`, `SCOPE`.
- Necessary governance: exact decimals, certified-manifest coverage,
  preservation of history, independent cash semantics, no unassigned scope
  inference.
- Avoidable friction: accepting a generic/read-model fixture before proving the
  actual live PFM projection; duplicated aggregation semantics; initially
  treating a project-wide settlement without explicit scope.
- Qualitative Framing Regret: `HIGH`; multiple accepted technical frames were
  contradicted by live observations. No common-clock avoidable-work duration is
  available, so `Framing Regret ms = null`.

## 6. GHR-04 — Personnel canonical sync and stale runtime generation

### Problem Revision

```text
problem_id       GHR-04
revision         1
user_job         Create personnel through the canonical sync contract.
desired_outcome  CanonicalPersonnelId schema/backfill are valid and the live
                 API runs the source generation that emits the current contract.
revision_state   PROVISIONAL_EXTERNAL_PROOF
```

### Frame trajectory

| Frame | A* boundary | G invariants | H hypothesis / counterevidence | Decision delta |
|---|---|---|---|---|
| F0 | SharePoint canonical schema, backfill and focused create contract | No duplicate canonical ID; no live write during verification; fail closed on missing schema | Schema/cache may be absent or stale | Verify live schema, zero pending backfill/quarantine, tests and build |
| F1 | Process owning the live API port | Do not kill/adopt an unowned process; compare process generation to source | Live API still returned the old 500 message while source had a new typed 503 and schema existed | Attribute mismatch to stale runtime rather than modify schema/source again |
| F2 | Post-restart current process | Restart only verified owner; recheck schema and focused behavior | Process generation was older than source | Verify fresh PID/generation and rerun semantic proof |

### Exact execution lineage

| RUN | WAVE | State | Evidence role |
|---|---|---|---|
| `93f42832aaa14f98a5bc2284097f2362` | `49a9a6ffa67e48ddb531ac6897922aaa` | `accepted` | Exact worktree + live schema/backfill + tests/build closure |
| `42709ba913064090840e76fef3db52d6` | `ae74b9cb219a4bdb933e30346f4695e5` | `accepted` | Root-cause attribution to stale live process generation |
| `985bb8acb60e4e44ae94d8be8fb7dd85` | `e71e6a0657b4426f9d66c6c534d7c399` | `accepted` | Post-restart live schema and focused regression verification |

### Oracle and outcome

```text
contract oracle      current typed error/schema contract
runtime oracle       listener/process generation newer than relevant source
semantic oracle      live schema + zero pending backfill/quarantine + regression
user outcome oracle  UNOBSERVED
final classification PROVISIONAL_EXTERNAL_PROOF
```

### Failure and friction classification

- Failure dimensions: `STATE`, `RUNTIME_IDENTITY`, `CONTRACT`, `CONTROL`.
- Necessary governance: process ownership, schema fail-closed behavior,
  canonical uniqueness, post-restart verification.
- Avoidable friction: source/schema work was reconsidered after the actual
  contradiction was a stale process generation.
- Qualitative Framing Regret: `MEDIUM`; runtime/source discrimination materially
  changed the next action, but no avoidable-work clock is recorded.

## 7. GHR-05 — Personnel to ManagingUnit canonical representative relation

### Problem Revision

```text
problem_id       GHR-05
revision         1
user_job         Set a Personnel record as the canonical representative of a ManagingUnit.
desired_outcome  One idempotent authorized relation is persisted and read through
                 the real SharePoint field without conflating Personnel unit history.
revision_state   PROVISIONAL_EXTERNAL_PROOF
```

### Frame trajectory

| Frame | A* boundary | G invariants | H hypothesis / counterevidence | Decision delta |
|---|---|---|---|---|
| F0 | Canonical relation contract, dedicated upsert and permissions | Both create/update authority; no placeholder Unit; no Personnel history mutation | Legacy behavior conflated representation and unit history | Establish ADR/story and bounded relation endpoint/UI |
| F1 | Live SharePoint field provisioning and storage name | Only the target schema field; no business-record mutation during schema proof | Actual internal storage name differed from the public field name | Map internal storage name while preserving public contract |
| F2 | Current source/live field verification | Preserve Finance and unrelated data; exact focused oracle | Prior timeout/acceptance gaps did not prove final live mapping | Run representative-only live check plus builds/tests |

### Exact execution lineage

| RUN | WAVE | State | Evidence role |
|---|---|---|---|
| `0e9c225a20ae4d6c9db10471d8f7d594` | `d72c6f09b7b842bda3960d4efef778f8` | `accepted` | High-risk decision/story contract only |
| `01d2ca74c9de4c5485a6ce58453703c5` | `5d8f059ea5204b1faef2e06bfbeacaa8` | `accepted` | Targeted schema provisioning and focused proof |
| `38d20c6e45984d3296f4afd93f7049cb` | `4d10a432edbd4bb39ff9396b4498807b` | `accepted` | Final source fingerprint, representative oracle, build and live field check |

### Oracle and outcome

```text
contract oracle      accepted ADR/story and dedicated relation semantics
external oracle      live SharePoint representative column check
technical oracle     focused Personnel relation tests + Finance builds
user outcome oracle  UNOBSERVED
final classification PROVISIONAL_EXTERNAL_PROOF
```

### Failure and friction classification

- Failure dimensions: `IDENTITY`, `CONTRACT`, `STATE`, `AUTHORIZATION`.
- Necessary governance: dedicated canonical relation, dual permission boundary,
  idempotency, targeted schema mutation and exact field verification.
- Avoidable friction: public/internal SharePoint field-name mismatch and prior
  cross-workspace/task-control projection problems.
- Qualitative Framing Regret: `MEDIUM`; storage-name evidence changed the frame,
  but quantitative attribution is unavailable.

## 8. GHR-06 — Canonical master backfill under production authority

### Problem Revision

```text
problem_id       GHR-06
revision         1
user_job         Give existing Project and ManagingUnit masters canonical IDs safely.
desired_outcome  Only blank, unambiguous targets are assigned under CAS; rerun
                 reports zero remaining assignments/blockers/quarantine.
revision_state   PROVISIONAL_EXTERNAL_PROOF
```

### Frame trajectory

| Frame | A* boundary | G invariants | H hypothesis / counterevidence | Decision delta |
|---|---|---|---|---|
| F0 | Whole-master dry-run and strong-key matching | CCCD/MaDA/MST only; no timestamp/name inference; no write | Existing rows may be ambiguous or drift before apply | Require zero blockers and exact candidate set |
| F1 | Four selected blank canonical IDs | Re-read all targets; validate ETag/source drift before first PATCH; never replace valid ID | Dry-run showed Projects 2/3/5 and ManagingUnits 9 as eligible | Apply exact bounded migration with CAS |
| F2 | Post-apply convergence and metadata | No rollback of successful IDs; rerun is recovery; no Finance mutation | Partial or wrong-shape apply would leave debt | Immediate dry-run must show zero; metadata audit validates column shape |

### Exact execution lineage

| RUN | WAVE | State | Evidence role |
|---|---|---|---|
| `e8ee4387c5774328bb0e7a61b7aac88b` | `f1fa1ef108164b958967a545ca47ce6e` | `accepted` | Live read-only zero-ambiguity dry-run |
| `dbf948056f15496bb49c82b72089295c` | `09ab12f4e9594e36b78b7459f4171292` | `accepted` | Exact controlled production backfill + immediate zero rerun |
| `b89d4eef7e7f4021908abdd3f4072747` | `4c1a5c3b47b9472b90dc84701a6a0831` | `accepted` | Read-only live metadata audit of canonical columns |

### Oracle and outcome

```text
precondition oracle  zero ambiguity/blockers/quarantine for exact candidates
mutation oracle      CAS-bound assignment of only four blank IDs
postcondition oracle zero assignments/blockers/quarantine on immediate rerun
metadata oracle      live column type/index/unique/required/hidden/readOnly audit
user outcome oracle  UNOBSERVED
final classification PROVISIONAL_EXTERNAL_PROOF
```

### Failure and friction classification

- Failure dimensions: `DATA_IDENTITY`, `AUTHORITY`, `CONCURRENCY`, `ORACLE`.
- Necessary governance: strong-key matching, all-target reread, ETag/CAS,
  exact-target apply, idempotent rerun, no automatic rollback.
- Avoidable friction: none proven material in the selected accepted chain; most
  control cost is necessary data-governance cost.
- Qualitative Framing Regret: `LOW/UNKNOWN`; do not treat disciplined dry-run
  and CAS overhead as avoidable friction without comparative evidence.

## 9. GHR-07 — Finance status save and stale/wrong projection

### Problem Revision

```text
problem_id       GHR-07
revision         1
user_job         Edit and see the authoritative Project and revenue-dossier statuses.
desired_outcome  Project status persists through the canonical Project store;
                 dossier stages/statuses round-trip from actual records; every
                 Finance tab reads the bounded common revenue ledger it needs.
revision_state   OPEN_TECHNICAL
```

### Frame trajectory

| Frame | A* boundary | G invariants | H hypothesis / counterevidence | Decision delta |
|---|---|---|---|---|
| F0 | Finance hero presentation and write callback | One canonical Project store; no second status store; no fabricated milestones | Hero inferred five milestones and dossier completion from one status string | Replace with editable Project status and actual dossier stage projection |
| F1 | Dossier status normalization and round-trip | Exact UI values precede fuzzy mapping; preserve `Chờ phê duyệt`; Finance money remains unchanged | UI label normalization could change status on save/reload | Share one normalizer across editor/save/adapter/revalidation |
| F2 | Cross-tab bounded read demand | `revenueLedger` is common detail input; receivable aging remains revenue-tab-specific | Overview lacked facts that another tab loaded | Load common ledger for every detail tab without broadening financial formulas |

### Exact execution lineage

| RUN | WAVE | State | Evidence role |
|---|---|---|---|
| `a8b10ecfb23f46d782c68ae40537451b` | `e8b86e8bef9b41e1bbcb49d2378e9175` | `replanned` | First implementation attempt |
| `a8b10ecfb23f46d782c68ae40537451b` | `14c64c3b565742d1a3021534013ff23e` | `active` | Replanned implementation; no checkpoint |
| `ba6535953acc4a8b90d3e39f1bc5e2ae` | `605c0205219e477b85a23e4f6925bb0c` | `active`, proof failed | Final-verification attempt; no checkpoint |
| `b8c88b64e9c844bcac3cf56e3cf60f98` | historical active wave | `active` | Cross-tab hero consistency change; no checkpoint |
| `7aff337537d54376ac4e0082bf27b04c` | two historical waves | `active` | Parallel/replanned cross-tab lineage; no checkpoint |

### Oracle and outcome

```text
technical acceptance  none for the exact complete trajectory
runtime oracle         none bound to current desired outcome
user outcome oracle    UNOBSERVED
final classification   OPEN_TECHNICAL
```

### Failure and friction classification

- Failure dimensions: `STATE`, `PROJECTION`, `CONTRACT`, `ORACLE`, `CONTROL`.
- Necessary governance: one canonical write store, exact status vocabulary,
  bounded reads and separation of Finance money from presentation metadata.
- Avoidable friction: inferred/fabricated milestones, divergent tab read sets,
  repeated uncheckpointed waves and a proof command that failed before closure.
- Qualitative Framing Regret: `HIGH`; the initial UI abstraction obscured the
  authoritative state sources. Quantitative attribution is unavailable.

## 10. Cross-case calibration results

### 10.1 Failure dimensions

The seven trajectories are annotatable with the Revision 4 dimensions without
adding another service or public tool:

| Dimension | Cases | Calibration observation |
|---|---|---|
| State/runtime generation mismatch | GHR-02, GHR-03, GHR-04, GHR-07 | Source-correct or test-correct state did not imply the loaded/rendered state was current. |
| Semantic/causal boundary error | GHR-02, GHR-03, GHR-07 | The wrong rendered path, aggregation boundary or settlement scope survived narrow proof. |
| Identity/authority | GHR-01, GHR-04, GHR-05, GHR-06 | Canonical IDs, RBAC, process ownership and CAS materially constrained the valid intervention. |
| Oracle mismatch | all cases | Technical proof was useful but insufficient; external/live/user-outcome layers must remain distinct. |
| Control friction | GHR-01, GHR-02, GHR-03, GHR-05, GHR-07 | Missing receipts, stale workspace/process, prompt size and uncheckpointed waves created measurable-looking but not fully attributable rework. |

### 10.2 Necessary governance versus avoidable friction

Necessary governance across the set:

- RBAC and canonical identity validation;
- exact workspace/process/source ownership;
- ETag/CAS and zero-ambiguity migration preflight;
- exact decimal and manifest-coverage rules;
- preservation of audit/history rows and independent cash meaning;
- fail-closed duplicate/unmapped/scope-unknown handling;
- exact RUN/WAVE/file/proof attestation before acceptance.

Candidate avoidable friction, still descriptive rather than causal:

- proving a helper or generic read model instead of the actual live/render path;
- revisiting source/schema when a stale runtime generation caused the contradiction;
- divergent aggregation and tab-read implementations;
- verification-only waves without durable file receipts;
- project-wide settlement inference before explicit scope evidence;
- unbounded/oversized packets that failed before reaching implementation;
- accepting proof-derived quality as if it could stand in for user outcome.

### 10.3 Framing Regret

Qualitative calibration is now possible:

```text
HIGH        GHR-02, GHR-03, GHR-07
MEDIUM      GHR-01, GHR-04, GHR-05
LOW/UNKNOWN GHR-06
```

Quantitative Framing Regret is deliberately not computed. Required missing
facts are:

```text
material_counterevidence_available_at
counterevidence_authority
frame_update_at
avoidable_work_intervals
necessary_governance_intervals
common_clock_authority
```

Without those facts, elapsed time between tasks/RUNs cannot be relabeled as
avoidable work.

### 10.4 Outcome-evidence coverage

```text
selected cases                         7
cases with accepted technical waves    6
cases with external/live receipts       4 or more, depending on claim boundary
cases reopened by user counterevidence  2
cases with independent user success     0
trusted resolutions                     0
```

The `4 or more` external/live count is intentionally not promoted to a metric:
external checks differ in abstraction and some are proof commands inside an
accepted wave. Prospective instrumentation must bind typed outcome receipts to
the exact Problem Revision before computing coverage.

## 11. Field utility and removal candidates

Fields that changed or constrained a decision in these cases:

- Problem Revision contract and desired outcome;
- A* boundary;
- governing invariants versus causal hypotheses;
- ownership/source/runtime identity;
- counterevidence and Decision Delta;
- exact RUN/WAVE/checkpoint/proof lineage;
- oracle abstraction and provenance;
- excluded scope and falsifier;
- outcome state distinct from technical acceptance.

Fields/policies that should remain shadow/advisory until measured:

- qualitative materiality of counterevidence;
- Framing Regret duration;
- semantic sibling recurrence;
- automatic frame-update-before-retry;
- automatic micro-policy promotion.

No field is removed solely from this seven-case packet. The prospective cohort
must measure whether each advisory field changes decisions or merely creates
ceremony.

## 12. What this closes and what remains

This packet closes the following calibration work at research/source-evidence
level:

- select seven natural Golden HR trajectories;
- record defensible exact RUN/WAVE links where reports exist;
- preserve `AMBIGUOUS` for absent reports or undefended revision transitions;
- classify failure dimensions;
- compute qualitative, not quantitative, Framing Regret;
- separate necessary governance from candidate avoidable friction;
- demonstrate two same-contract reopen/false-closure examples.

It does not close:

- native PRL v11 backfill into the HR schema-9 ledger;
- quantitative Framing Regret;
- independent outcome-evidence coverage;
- true semantic sibling recurrence;
- the open GHR-07 technical lineage;
- the active settlement-scope lineage in GHR-03;
- a prospective control/treatment cohort;
- causal promotion/removal of micro-policies;
- commit, push, package, release, deployment or production outcome.

## 13. Prospective handoff

For each new natural case, create the Problem Revision before the first material
write and record:

```text
problem_id + revision
attested start clock
user job + desired outcome
F0 A*/G/H + ownership
oracle abstraction and independence
counterevidence available_at + authority
frame revision and changed decision
exact RUN/WAVE/proof/checkpoint links
provisional resolution
independent outcome receipt or same-revision reopen
bounded Resolution Envelope + falsifier
```

Only after a representative prospective cohort contains these facts may the
project calculate Framing Regret, independent outcome coverage, true sibling
recurrence, or promote/remove individual micro-policies.
