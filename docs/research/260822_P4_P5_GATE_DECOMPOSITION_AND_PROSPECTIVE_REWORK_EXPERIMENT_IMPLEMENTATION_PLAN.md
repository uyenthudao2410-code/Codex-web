# P4/P5 Gate Decomposition and Prospective Rework Experiment — Implementation Control Plan v2

- **Plan ID:** P4-P5-20260822-v2
- **Ngày cập nhật:** 2026-08-22, Asia/Bangkok
- **Workspace:** `E:\DEV\Codex-web`
- **Trạng thái:** IMPLEMENTATION CONTROL PLAN — NOT ACTIVATED
- **Automatic treatment activation:** `false`
- **Automatic production promotion:** `false`
- **Public MCP tool count target:** `8`

Tài liệu này là kế hoạch triển khai chuẩn hóa cho việc tách P4 predictive validation khỏi P5 prospective experiment. Nó hợp nhất các kết quả audit code, EOCL/ledger, P2/P4/P5 historical evidence và các nguyên tắc experimental design đã được nghiên cứu trước đó.

Tài liệu này **không phải current-state authority**. Thứ tự ưu tiên sự thật vẫn là:

1. implementation hiện tại + focused tests + live runtime contract;
2. `docs/CURRENT_STATE.md`;
3. `docs/ROADMAP.md` và maintained product docs;
4. dated research docs, bao gồm tài liệu này.

Mọi số liệu lịch sử trong tài liệu phải được hiểu là **timestamped evidence**, không phải live invariant. Gate 0 bắt buộc chụp lại root/HEAD/status/run/wave/runtime trước mỗi material implementation wave hoặc experiment epoch.

---

# 0. NORMATIVE V1 CRITICAL PATH

Đây là phần duy nhất phải nằm trên critical path cho tới khi P5-A canary hoàn tất. Các workstream P4-E, taxonomy v3, P5-B statistics nâng cao và P5-C targeting không được làm chậm critical path nếu không tạo blocker trực tiếp.

```text
Gate 0  Reconcile exact source / active authority
  ↓
Wave 1  Gate Semantics v2
  ↓
Wave 2  Frozen Manifest + Atomic Assignment
  ↓
Wave 3  All-assigned ITT + Outcome Projection
  ↓
Wave 4  Canary Analyzer + Pause/Hard-stop Controller
  ↓
P5-A0   Shadow A/A Instrumentation Epoch
  ↓
Wave 6  Casebook Replay / Protocol Dry Proof
  ↓
P5-A    Treatment Feasibility Canary
  ↓
Close canary epoch
  ↓
Freeze confirmatory P5-B contract
```

Song song nhưng **không blocking mặc định**:

```text
P4-C strict natural collection
P4-E coverage-first economic analysis
Taxonomy v3 deterministic classification
```

Chưa mở:

```text
P5-B efficacy     until P5-A closes cleanly
P5-U promotion    until P5-B efficacy + economics + quality
P5-C targeting    until P5-B + P4-C + treatment-benefit heterogeneity
P7/P8             remain HOLD
```

## 0.1. Core decision

Không dùng P4 strict causal-repair predictor làm điều kiện bắt buộc để **bắt đầu** randomized P5 experiment.

Giữ P4 strict và tách thành các claim riêng:

| Projection | Câu hỏi | Evidence cần |
| --- | --- | --- |
| `p4_c_predictive_targeting_ready` | Signal trước mutation có dự báo causal repair đủ robust không? | Strict P4-C |
| `p4_e_descriptive_ready` | Economic rework descriptive cohort có tái lập được không? | Frozen historical cohort |
| `p4_e_advisory_ready` | Economic predictor có đủ coverage/leakage-safe để advisory không? | Feature-contract-specific validation |
| `p5_experiment_start_ready` | Runtime/source/manifest/assignment/measurement có đủ để operator mở experiment epoch không? | Engineering integrity, **không cần P4-C** |
| `p5_experiment_epoch_active` | Exact epoch đã được operator mở rõ ràng chưa? | Explicit durable activation |
| `p5_causal_efficacy_ready` | Treatment có causal efficacy theo frozen prospective RCT không? | P5-B randomized ITT |
| `p5_universal_policy_promotion_ready` | Universal eligible treatment có đáng promotion không? | P5-B + MERD/economics + quality + release acceptance |
| `p5_targeted_policy_ready` | Có bằng chứng để target treatment theo signal không? | P5-B + P4-C + HTE/policy value |

`automatic_start=false` và `automatic_promotion=false` là invariant của v2.

---

# 1. Evidence reconciliation và claim boundaries

## 1.1. Live state là snapshot động

Không hard-code một run cụ thể đang `ACTIVE`, `REPLAN`, `ACCEPTING` hay `CHECKPOINTED` thành điều kiện của P5. Trong cùng ngày, live task projection đã thay đổi nhiều lần do concurrent controller work. Vì vậy mọi current-state statement phải có:

```text
observed_at
workspace_root
branch
HEAD
upstream_head
source_worktree_fingerprint
runtime_loaded_fingerprints
current run/wave/state
active write lease / source owner
```

Dated research docs chỉ lưu chronology. `CURRENT_STATE.md` chỉ cập nhật sau source acceptance + runtime activation proof tương ứng.

## 1.2. Frozen P2 evidence

Frozen historical snapshot đã tái lập:

| Metric | Value | Claim allowed |
| --- | ---: | --- |
| Raw accepted ledger rows | 479 | Raw history only |
| Canonical filtered accepted cohort | 449 | P2 deterministic/model-free cohort |
| First-pass accepted | 266 | Descriptive |
| Accepted with replan | 183 | Economic/process rework |
| Accepted rework rate | 40.7572% | Descriptive, not treatment effect |
| Replanned waves | 347 | Historical orchestration |
| `failure_observed` events | 353 | Event count, not unique tasks |
| Deterministically mapped failure events | 173 | Structured/fallback taxonomy |
| Unknown failure events | 180 | Must remain unknown without evidence |

TTAR historical accepted-only:

| Cohort | P50 | P90 |
| --- | ---: | ---: |
| First-pass accepted | 65.703 s | 434.493 s |
| Accepted with replan | 298.213 s | 2,393.707 s |
| Ratio | 4.538803x | 5.509196x |

Feature + bugfix cohort:

| Workflow | N | With replan | Rate |
| --- | ---: | ---: | ---: |
| Feature | 128 | 70 | 54.6875% |
| Bugfix | 94 | 35 | 37.2340% |
| Combined | 222 | 105 | 47.30% |

Những số này chứng minh **rework là cost center lớn**. Chúng không chứng minh Lean Causal Fix Gate v1 có causal efficacy.

## 1.3. Historical rows không phải predictor-ready matrix

449 rows là accepted outcome history, không phải 449 supervised P4-E rows.

Coverage audit trên frozen snapshot:

| Field | Coverage |
| --- | ---: |
| Workflow + accepted outcome + TTAR timestamps | 449/449 |
| Initial base HEAD + worktree identity | 449/449 |
| Strict pre-first-write selected paths | 335/449 |
| Strict pre-first-write oracle observation | 74/449 |
| Strict pre-first-write P4 shadow recommendation | 38/449 |
| First-wave contract fingerprint | 21/449 |
| Explicit objective provenance | 6/449 |
| Full defect + rollback + manual-fix quality | 0/449 |
| Joint context + oracle + shadow common support | 0/449 |

Admissible claim:

> Frozen historical evidence supports workflow-level economic diagnosis and selected feature-specific analyses.

Inadmissible claim:

> A 449-row multifeature predictive matrix already exists.

## 1.4. P4-C rare-event constraint

Observed strict P4 cohort đã có khoảng 65 representative terminal tasks nhưng chỉ 2 known causal-repair positives và `validated_signals=[]`.

P4-C v5 yêu cầu conjunction của:

- positive pooled Brier gain;
- Bonferroni/Wilson separation;
- task-family holdout;
- source-state holdout;
- latest-third temporal holdout;
- all required rolling windows evaluable;
- positive minimum rolling gain;
- representative evidence only.

Với 2 positives, rolling validation hiện không đủ event distribution để đạt gate. Không hạ P4-C, không synthesize repairs, không oversample để tạo production evidence.

P4-C tiếp tục shadow-only và được dùng về sau cho targeting/heterogeneity, không khóa P5-A experiment engineering.

## 1.5. Patch-preflight evidence boundary

148 patch-preflight failed records đã được chặn trước orchestration run creation. Đây là **guardrail-observed evidence**, không phải 148 unique tasks saved và không phải causal effect estimate.

---

# 2. Gate topology và state machine

## 2.1. Gate equations

```text
p5_experiment_start_ready =
    source_epoch_ready
AND manifest_frozen
AND assignment_runtime_proven
AND arm_enforcement_proven
AND all_assigned_itt_path_proven
AND quality_guardrail_path_proven
AND no_active_hard_stop
```

```text
p5_experiment_epoch_active =
    p5_experiment_start_ready
AND explicit_operator_epoch_open_for_exact_manifest
AND runtime_loaded_fingerprints_match
AND no_active_hard_stop
```

```text
p5_causal_efficacy_ready =
    confirmatory_epoch_terminal
AND preregistered_primary_boundary_crossed
AND quality_noninferiority_or_hard_floor_holds
AND assignment_epoch_integrity_holds
AND missingness_and_schedule_integrity_acceptable
AND no_safety_stop
```

```text
p5_universal_policy_promotion_ready =
    p5_causal_efficacy_ready
AND effect_meets_frozen_MERD_or_materiality_rule
AND randomized_restricted_time_economics_hold
AND quality_safety_integrity_hold
AND separate_operator_release_acceptance
AND automatic_promotion_is_false
```

```text
p5_targeted_policy_ready =
    p5_causal_efficacy_ready
AND p4_c_predictive_targeting_ready
AND treatment_by_signal_benefit_validated
AND target_source_generalization_holds
AND policy_value_exceeds_materiality_floor
AND separate_operator_promotion_acceptance
```

## 2.2. Experiment epoch state machine

```text
NOT_READY
  -> START_READY
  -> EPOCH_ACTIVE
  <-> EPOCH_PAUSED
  -> EPOCH_CLOSED
       -> FEASIBILITY_ACCEPTED
        | REPLAN
        | ABORT
        | INSUFFICIENT_FEASIBILITY_VOLUME

EPOCH_ACTIVE / EPOCH_PAUSED
  -> EPOCH_HARD_STOPPED
       -> REPLAN or ABORT
```

Semantics:

- `START_READY` không activate treatment;
- chỉ durable `p5_epoch_opened` với exact manifest authority tạo `EPOCH_ACTIVE`;
- `PAUSED` cấm assignment mới nhưng tiếp tục follow-up existing ITT rows;
- `CLOSED`/`HARD_STOPPED` cấm resume enrollment;
- protocol semantic change luôn tạo manifest/epoch mới;
- closeout là durable report/event, không suy từ UI state.

---

# 3. Scientific question, treatment contrast và common execution contract

## 3.1. P5-B scientific question

Trên natural eligible feature/bugfix tasks có exact source identity và observed oracle:

> Lean Causal Fix Gate v1 có làm tăng first-pass accepted work và/hoặc giảm economic rework/time mà không làm giảm quality, safety hoặc authority integrity so với EOCL control workflow hiện tại hay không?

## 3.2. Arm-neutral safety invariants

Cả control và treatment đều giữ:

- exact source/target verification;
- patch preflight;
- write ownership/lease;
- deterministic route policy hiện hành;
- public 8-tool contract;
- proof + final acceptance authority;
- permission/security invariants;
- operator-visible terminal report;
- no synthetic promotion evidence.

Không randomize việc tắt safety.

## 3.3. Common execution contract — BẮT BUỘC

Để tránh co-intervention/performance bias, manifest phải freeze những biến không thuộc treatment:

```yaml
common_execution_contract:
  execution_route: deterministic
  model_policy: SAME_BOTH_ARMS
  effort_policy: SAME_BOTH_ARMS
  review_policy: SAME_BOTH_ARMS
  max_attempts: SAME_BOTH_ARMS
  max_auto_steps: SAME_BOTH_ARMS
  max_tool_hops: SAME_BOTH_ARMS
  timeout_policy: SAME_BOTH_ARMS
  verification_budget_policy: SAME_BOTH_ARMS
  operator_intervention_policy: SAME_BOTH_ARMS
```

Nếu treatment protocol yêu cầu một discriminator/falsifier riêng, overhead đó là một phần treatment. Mọi compute/review/verification ngoài bundle phải giống control theo contract.

## 3.4. Control arm

Control = EOCL workflow hiện hành + shared safety invariants.

Control không nhận trước:

- causal hypothesis template;
- competing-cause discriminator;
- treatment-only surface budget form;
- treatment-only proof-plan formality.

## 3.5. Treatment arm — Lean Causal Fix Gate v1

Treatment bundle cố định:

1. Causal hypothesis: `X -> Y via Z`.
2. Smallest discriminator/falsifier giữa root cause chính và competing cause.
3. Oracle expectation settled trước first write.
4. Bounded change surface: exact path/symbol hoặc scope cap.
5. Predeclared proof plan: focused proof + credible adjacent risk.
6. Scope breach -> deviation + REPLAN; không silent expansion.
7. Protocol-start/protocol-complete/first-write spans để đo overhead.

Thay bundle => policy version mới + epoch mới.

---

# 4. Eligibility, enrollment và interference

## 4.1. Arm-neutral eligibility

Eligibility được ghi trước arm reveal:

- `task_class in {feature, bugfix}`;
- representative natural task;
- exact source identity available;
- observed oracle exists hoặc oracle availability/stability được xác minh bằng server-owned check;
- bounded scope feasible;
- no conflicting writer/lease;
- no stale/recovery/unreconciled task state;
- no high-risk exclusion;
- common execution contract available.

Không dùng `solution_shadow.oracle_strength == strong` như bằng chứng external oracle.

## 4.2. Enrollment riêng với eligibility

Durable event:

```text
p5_enrollment_decision_recorded
```

Fields:

- eligible / ineligible;
- enrolled / not_enrolled;
- reason code;
- decision authority;
- policy/version;
- timestamp/seq;
- recorded before assignment and before inferable arm reveal.

Report phải hiển thị:

```text
assessed
eligible
ineligible by reason
eligible but not enrolled
assigned
assigned without finalized outcome
```

## 4.3. Controller/session interference

Task-local treatment vẫn có thể leak qua context.

V1:

- fresh/isolated task context per assignment when possible;
- treatment artifacts không được đưa vào next-task eligibility/enrollment context;
- record `controller_context_fp`, `session/cluster_id`, isolation status;
- nếu isolation không chứng minh được: cluster randomization/switchback trở thành fallback trong epoch mới, không hot-swap.

## 4.4. Quality-follow-up source interference — BỔ SUNG

Một accepted task có thể bị task sau sửa trùng file/symbol trước khi delayed quality follow-up đóng. Vì vậy mỗi accepted assignment phải project:

```yaml
quality_followup_interference:
  status: none|nonoverlapping_mutation|overlapping_mutation|attribution_unknown
  accepted_surface_fp: ...
  intervening_assignment_ids: [...]
  overlap_surface_fp: ...
```

Nếu later mutation overlap surface trước follow-up closure:

- không tự quy latent defect cho assignment trước;
- delayed-quality outcome trở thành `attribution_unknown` theo frozen rule;
- analyzer báo riêng rate theo arm;
- sensitivity strategy phải freeze trước confirmatory epoch.

Để giảm delay/interference, **confirmatory primary endpoint không phụ thuộc delayed post-acceptance follow-up**. Delayed quality/rollback/regression là hard guardrail/NI outcome riêng. Immediate qualifying acceptance vẫn phải có required oracle/proof tại acceptance.

---

# 5. Frozen manifest và epoch identity

## 5.1. Manifest v2 — minimum normative fields

```yaml
schema_version: 2
experiment_id: p5-lean-causal-fix-<phase>-v1
phase: P5-A0|P5-A|P5-B
study_type: shadow_aa|randomized_feasibility|randomized_confirmatory

automatic_activation: false
automatic_production_promotion: false

control_policy:
  id: eocl-current-control-v1

treatment_policy:
  id: lean-causal-fix-gate-v1
  implementation_fingerprint: TO_FREEZE
  vary_only: prewrite_causal_fix_protocol

source_contract:
  control_plane_source_head: TO_FREEZE
  upstream_identity: TO_FREEZE
  source_worktree_clean_required: true
  no_conflicting_writer_required: true

runtime_contract:
  runtime_version: TO_FREEZE
  runtime_policy_fp: TO_FREEZE
  tool_contract_fp: TO_FREEZE
  evaluation_schema_fp: TO_FREEZE
  public_tool_count: 8

environment_contract:
  environment_fp: TO_FREEZE
  method_version: p5-environment-v1

common_execution_contract:
  policy_sha256: TO_FREEZE

eligibility_contract:
  version: p5-eligibility-v2
  reason_vocabulary_sha256: TO_FREEZE
  high_risk_exclusion_sha256: TO_FREEZE

enrollment_contract:
  version: p5-enrollment-v1
  policy_sha256: TO_FREEZE

assignment:
  randomization_unit: stable_task_assignment
  unit_canonicalization_version: p5-assignment-unit-v1
  algorithm: stratified_permuted_block_v1
  strata: [feature, bugfix]
  block_size: 4
  allocation: {control: 0.5, treatment: 0.5}
  seed_commitment_sha256: TO_FREEZE
  restart_safe_seed_contract_sha256: TO_FREEZE
  never_reseed_within_epoch: true
  assignment_before_first_arm_action: true
  assignment_before_first_write: true

outcome_contract:
  horizon_H: TO_FREEZE
  horizon_anchor: assignment_at
  immediate_oracle_required: true
  delayed_quality_followup_duration: TO_FREEZE
  intercurrent_event_matrix_sha256: TO_FREEZE
  followup_interference_policy_sha256: TO_FREEZE

analysis:
  analyzer_sha256: TO_FREEZE
  intention_to_treat: true
  survivor_filter: false
  target_population_weights_sha256: TO_FREEZE

missing_data:
  missing_is_unknown_not_zero: true
  missing_quality_is_not_pass: true
  missing_cost_is_not_zero: true

stop_rule:
  stop_on_assignment_conflict: true
  stop_on_late_assignment: true
  stop_on_manifest_epoch_drift: true
  stop_on_authority_or_write_lease_violation: true
  stop_on_source_identity_violation: true
  stop_on_critical_security_or_data_loss_defect: true
```

## 5.2. Environment fingerprint

Environment fingerprint chỉ bao gồm dependency/runtime dimensions có khả năng ảnh hưởng material đến behavior/TTAR, không fingerprint toàn máy:

```text
environment_fp = SHA256(canonical_json({
  os_family_and_build_class,
  python_runtime,
  node_runtime,
  relevant_lockfile_fingerprints,
  required_runtime_configuration_class
}))
```

Environment drift material => pause/close epoch theo manifest. Non-material host telemetry không tự đóng epoch.

## 5.3. Activation epoch identity

```text
activation_epoch_id = SHA256(
    manifest_sha256
  + treatment_implementation_fp
  + common_execution_contract_fp
  + tool_contract_fp
  + evaluation_schema_fp
  + runtime_policy_fp
  + environment_fp
  + assignment_algorithm_version
  + analyzer_sha256
)
```

Task target source evolution giữa natural tasks **không** tự đóng epoch nếu control-plane/treatment/analyzer/runtime contract không đổi và pre-task source identity được ghi. Control-plane source drift luôn đóng enrollment.

---

# 6. Atomic assignment — storage contract bắt buộc

## 6.1. Problem

Current `events` table chỉ unique theo `event_id`; nó không có DB-level uniqueness cho:

```text
(experiment_id, assignment_unit_fp)
(experiment_id, epoch_id, stratum, block_id, block_slot)
```

Read-then-append không đủ để gọi là immutable assignment.

## 6.2. V2 quyết định storage

**Không tạo experiment database/service mới.**

Cho phép một **minimal canonical-ledger uniqueness table/index** nếu đó là cách đơn giản nhất để enforce invariant atomically. Đây không được coi là một source-of-truth thứ hai; ledger assignment event vẫn là causal audit record, table chỉ là durable uniqueness/lookup constraint.

Recommended schema shape:

```sql
CREATE TABLE IF NOT EXISTS experiment_assignments (
    assignment_id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    activation_epoch_id TEXT NOT NULL,
    assignment_unit_fp TEXT NOT NULL,
    task_class TEXT NOT NULL,
    block_id TEXT NOT NULL,
    block_slot INTEGER NOT NULL,
    assigned_arm TEXT NOT NULL,
    assignment_probability REAL NOT NULL,
    manifest_sha256 TEXT NOT NULL,
    created_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    UNIQUE(experiment_id, assignment_unit_fp),
    UNIQUE(experiment_id, activation_epoch_id, task_class, block_id, block_slot)
);
```

Nếu implementation chứng minh được cùng invariants gọn hơn bằng generic idempotency records **trong cùng transaction**, table riêng có thể bỏ. Không được chọn giải pháp khó audit chỉ để tránh một table nhỏ.

## 6.3. Transaction invariant

Một atomic assignment transaction phải:

1. `BEGIN IMMEDIATE`;
2. verify epoch `EPOCH_ACTIVE`;
3. verify durable eligibility + enrolled decision + exact manifest;
4. verify assignment before first arm-specific action/write;
5. reserve exactly one block slot;
6. enforce unique `(experiment_id, assignment_unit_fp)`;
7. write assignment uniqueness row/claim;
8. append hash-chained authoritative `p5_assignment_recorded` event **trong cùng transaction boundary**;
9. commit.

Nếu existing event append helper không hỗ trợ shared transaction, Wave 2 được phép refactor tối thiểu thành internal transactional append helper. Không đổi event hash semantics.

## 6.4. Stable assignment unit

```text
assignment_unit_fp = SHA256(canonical_json_v1({
  task_assignment_id,
  repository_identity_fp,
  initial_task_spec_fp,
  initial_target_source_block_id
}))
```

Không dùng:

- `run_id`;
- `wave_id`;
- mutable objective revision;
- post-assignment state.

Invariants:

- retry/replan/resume/new run của cùng durable task -> same arm;
- duplicate identical request -> idempotent no-op;
- conflicting arm/manifest -> fail closed;
- late assignment -> fail closed;
- successful successor không được thay thế failed predecessor outcome.

---

# 7. Randomization và target population

## 7.1. V1 algorithm

Default:

- 1:1 stratified permuted blocks;
- strata: `feature`, `bugfix`;
- block size 4;
- concealed active block composition;
- seed commitment published, seed secret during active epoch;
- restart-safe deterministic replay;
- never reseed within epoch.

Nếu active-block concealment không chứng minh kỹ thuật được, fixed block size 4 là **NO-GO**; epoch mới phải dùng concealed variable blocks hoặc cluster/switchback design.

## 7.2. Allocation != estimand population weights

Canary có thể intentionally cân bằng 16 feature / 16 bugfix để kiểm thử feasibility. Điều đó không có nghĩa target population là 50/50.

Confirmatory manifest phải freeze riêng:

```text
randomization allocation within strata
≠
target-population stratum weights
```

Report P5-B bắt buộc có:

- feature stratum effect;
- bugfix stratum effect;
- weighted target-population effect;
- exact frozen weighting rule.

Target weights lấy từ blinded eligible population/rule pre-specified, không chọn sau khi thấy arm effect.

---

# 8. P5-A0 — Shadow A/A Instrumentation Epoch

Đây là bổ sung bắt buộc trước treatment canary.

## 8.1. Purpose

P5-A0 kiểm tra end-to-end experimentation plumbing mà **không tạo treatment contrast**.

Randomizer vẫn assignment A/A', nhưng cả hai received protocol đều là control EOCL workflow.

```text
eligible
  -> enrollment
  -> assignment A/A'
  -> same control behavior
  -> all-assigned ITT projection
  -> terminal + quality projection
```

## 8.2. What A/A may prove

- exact-once assignment;
- block replay/restart safety;
- no assignment after first write;
- arm persistence qua replan/resume;
- ITT join completeness;
- outcome finalization completeness;
- funnel parity diagnostics;
- no treatment wrapper contamination;
- report/analyzer determinism;
- runtime epoch lifecycle.

## 8.3. What A/A may NOT prove

- treatment efficacy;
- treatment safety;
- treatment overhead;
- treatment noninferiority;
- P5-B readiness beyond instrumentation integrity.

## 8.4. Minimal progression

A/A không cần chờ 32 task. Recommended minimum operational progression:

- at least one completed assignment block in feature **if natural eligible feature tasks arrive**;
- at least one completed block in bugfix **if natural eligible bugfix tasks arrive**;
- 100% critical instrumentation invariants;
- zero unexplained assignment loss;
- zero late/duplicate/conflicting assignment;
- complete terminal/outcome projection for finalized rows.

Nếu một stratum không có đủ natural eligible volume trước max horizon, report `INSUFFICIENT_FEASIBILITY_VOLUME`; không manufacture tasks.

A/A epoch đóng trước P5-A treatment canary.

---

# 9. P5-A treatment feasibility canary

## 9.1. Default target

Recommended operational target: 32 natural assigned tasks:

- 16 feature;
- 16 bugfix;
- 16 control;
- 16 treatment;
- four complete blocks per stratum if workload permits.

Target này là feasibility target, không power claim.

## 9.2. Canary progression criteria

| Invariant | Requirement |
| --- | --- |
| Assessed-task eligibility/exclusion projection | 100% |
| Exactly one authoritative assignment | 100% |
| Eligibility < enrollment < assignment < arm action < first write | 100% |
| Manifest/source/runtime/environment identity complete | 100% |
| Assignment retained in ITT | 100% |
| Terminal/by-H status finalized | 100% for closed canary rows |
| Immediate quality/oracle fields | 100% |
| Delayed follow-up status/interference status | 100% before closeout or explicitly pending until horizon |
| Assigned/received/adherence | 100% |
| Treatment overhead spans | 100% treatment; corresponding control clock available |
| Completed block schedule | exact 2/2 |
| Unexplained eligible-not-enrolled | 0 |
| Observed critical/security/data-loss harm | 0 |

Canary không claim absence of rare harm và không có efficacy p-value/boundary.

## 9.3. Canary pooling

Default: **do not pool** into P5-B.

Pooling chỉ được phép nếu confirmatory estimand, treatment, eligibility, assignment, H, quality, Nmax và alpha-spending contract đã freeze trước first canary assignment. V2 default không làm internal-pilot pooling.

---

# 10. Estimand and Intercurrent Event Matrix — normative

Confirmatory manifest phải freeze một bảng duy nhất; analyzer không suy semantics từ prose phân tán.

| Post-assignment event | Primary endpoint strategy | Secondary/guardrail |
| --- | --- | --- |
| Any REPLAN | Primary non-success | Count/cause secondary |
| Accepted after H | Primary non-success | Time-to-terminal secondary |
| Failed/rejected | Primary non-success | Typed terminal cause |
| Blocked | Primary non-success | Cause |
| Aborted | Primary non-success | Cause |
| Timeout | Primary non-success | Time/cause |
| Activation failed after assignment | Remain ITT; primary non-success | Integrity cause |
| Epoch drift after assignment | Remain ITT; primary non-success unless qualifying acceptance already achieved under frozen rule | Drift guardrail |
| Crossover | Analyze assigned arm | Received-arm secondary |
| Noncompliance | Analyze assigned arm | Per-protocol secondary |
| Manual rescue/fix | Primary non-success | Operator burden secondary |
| Rollback | Quality hard-fail | Safety/quality event |
| Critical/security/data-loss defect | Immediate hard stop | Independent of efficacy |
| Missing immediate required quality/oracle | Primary non-success | Missingness report |
| Missing cost | Unknown, not zero | Cost unavailable |
| Later overlapping source mutation during delayed follow-up | Primary remains based on immediate qualifying acceptance; delayed quality attribution = unknown per frozen policy | Follow-up interference sensitivity |

This matrix is part of the **estimand contract**. Any semantic change => new confirmatory manifest/epoch.

---

# 11. Outcome and ITT contract

## 11.1. Primary endpoint — simplified to avoid delayed-attribution distortion

Recommended confirmatory primary:

```text
first_pass_accepted_by_H =
    qualifying_acceptance_by_H
AND post_assignment_replan_count == 0
AND required_immediate_oracle_and_proof_observed == true
```

Where:

- rejected/failed/blocked/aborted/timeout => failure;
- accepted after H => failure;
- any post-assignment replan => failure;
- missing immediate required oracle/proof => failure.

Delayed regression/rollback/manual-fix follow-up is **not hidden inside primary**. It is a lexicographically prior quality/safety guardrail for promotion decisions.

Reason: delayed follow-up in a continuously changing source tree can be confounded by later overlapping tasks. Separating efficacy from delayed quality attribution makes the estimand clearer while preserving fail-closed promotion.

## 11.2. Quality decision hierarchy

```text
1. assignment/source/authority integrity
2. critical safety hard stop
3. delayed quality hard floor / noninferiority
4. primary first-pass acceptance superiority
5. restricted-time economics
6. monetary/token cost when coverage complete
```

A positive primary result never overrides quality/safety failure.

## 11.3. Economic key-secondary endpoint

```text
restricted_time_to_qualifying_acceptance_H =
    min(assignment_to_qualifying_acceptance, H)

if no qualifying acceptance by H:
    value = H
```

This includes treatment preparation overhead in the same clock and retains nonaccepted tasks.

Also report:

- assignment-to-terminal P50/P90;
- accepted-only TTAR P50/P90 as descriptive only;
- restricted mean;
- log-time sensitivity;
- terminal status composition;
- missingness by arm.

## 11.4. Post-assignment replan scope

```text
post_assignment_replan_count =
  count(replan transitions with seq > assignment_event_seq)
```

Pre-assignment replan không phải treatment outcome.

## 11.5. ITT population

Primary denominator = every immutable assignment, including:

- accepted;
- failed/rejected;
- blocked;
- aborted;
- timeout;
- oracle lost;
- activation failed;
- epoch drift after assignment;
- crossover/noncompliance;
- operator intervention.

Never replace a failed assignment with a successful retry/successor.

---

# 12. SRM and funnel-integrity diagnostics

Không chỉ test assignment 50/50. Mỗi epoch phải report funnel theo arm/stratum:

```text
assessed
  ↓
eligible
  ↓
enrolled
  ↓
assigned
  ↓
arm protocol started
  ↓
first write
  ↓
terminal
  ↓
immediate quality complete
  ↓
delayed follow-up complete / interfered
```

Diagnostics:

- completed-block schedule integrity;
- assignment loss;
- protocol-start loss;
- first-write loss;
- terminal-outcome loss;
- immediate quality missingness;
- delayed follow-up missing/interference;
- eligible-but-not-enrolled imbalance;
- received-arm crossover.

Low-power canary SRM p-value không được dùng làm proof randomizer đúng; structural block replay + exact event accounting là primary integrity evidence.

---

# 13. P5-B confirmatory statistical design

## 13.1. Freeze only after P5-A closes

Before first P5-B assignment, freeze:

- eligible population;
- target-population weights;
- primary endpoint + H;
- immediate quality requirements;
- delayed quality estimand/NI/hard-floor;
- intercurrent-event matrix;
- MERD;
- statistical MDE;
- Nmax / maximum information;
- group-sequential rule;
- missingness thresholds;
- funnel/SRM rules;
- environment/source/runtime epoch;
- analyzer hash + golden vectors.

## 13.2. Group-sequential v1

Recommended default:

- binary primary endpoint;
- stratified feature/bugfix estimator;
- two-sided total alpha 0.05 unless product decision freezes another valid rule;
- Lan–DeMets O'Brien–Fleming-like spending;
- registered looks at finalized observed-information fractions (for example 25/50/75/100% after exact design calculation);
- nonbinding futility by default;
- continuous hard safety/integrity monitoring;
- deterministic analyzer + golden vectors.

Effect inspection outside registered looks is prohibited for confirmatory decision-making.

## 13.3. Blinded sample-size re-estimation — BỔ SUNG

Because prospective eligible baseline rate is unknown, manifest may preregister blinded SSR:

```yaml
blinded_sample_size_reestimation:
  enabled: true
  uses_arm_labels: false
  nuisance_parameter: pooled_primary_event_rate
  trigger_information_fraction: TO_FREEZE
  min_nmax: TO_FREEZE
  max_nmax: TO_FREEZE
  alpha_change_allowed: false
  merd_change_allowed: false
  endpoint_change_allowed: false
  method_sha256: TO_FREEZE
```

Blinded SSR may update information/N requirement. It may **not** change desired effect, endpoint, alpha or decision threshold after observing unblinded treatment effect.

## 13.4. Operating-characteristic simulation — REQUIRED before P5-B

A deterministic offline simulation must verify the exact frozen design under scenarios:

- null effect;
- MERD effect;
- large benefit;
- harm;
- multiple baseline rates;
- unequal feature/bugfix mix;
- missing outcomes;
- crossover/noncompliance;
- delayed outcomes;
- partial blocks;
- cluster/interference if applicable.

Required outputs:

- empirical Type-I error;
- power at MERD;
- expected N/information;
- early efficacy probability;
- futility probability;
- inconclusive probability;
- quality false-pass/harm behavior;
- deterministic seed + analyzer version.

No new statistics platform is needed: one versioned script/module + golden summaries is sufficient.

## 13.5. MERD, MDE and break-even remain separate

- `MERD`: product decision threshold on exact estimand;
- `statistical MDE`: detectable effect under N/alpha/power/design;
- historical break-even tables: scenario-only descriptive economics.

Do not conflate them.

---

# 14. P4-E — coverage-first economic predictor

P4-E is non-blocking for P5-A v1.

## 14.1. P4-E0 frozen cohort/coverage

Every report records:

- Git HEAD;
- ledger schema/version;
- observed window;
- query hash/version;
- ordered run-id digest;
- included/excluded counts;
- feature coverage;
- strict pre-first-write ordering;
- instrumentation epoch compatibility;
- leakage verdict.

## 14.2. Leakage rules

Allowed only if pre-assignment/pre-first-write:

- task class;
- initial source identity;
- selected-path count if observed;
- observed oracle type if observed;
- P4 shadow estimate if recorded prewrite;
- compatible source/instrumentation epoch.

Prohibited as predictors:

- post-replan source drift;
- final objective revision count;
- post-write patch failure;
- proof result;
- final touched surface;
- adherence;
- final repair taxonomy.

Missing remains missing, not zero.

## 14.3. P4-E authority boundary

```text
advisory_only = true
assignment_input_allowed = false
treatment_targeting_allowed = false
route_change_allowed = false
automatic_policy_activation = false
```

Do not add Firth/Bayesian/GAM/new model dependency before the actual compatible matrix justifies it.

---

# 15. Taxonomy v3 and casebook workstreams

## 15.1. Taxonomy v3

180 unknown historical `failure_observed` events include 103 `CHECK_FAILED` and 49 `BUILD_VERIFICATION_FAILED`; these two groups dominate unknown count.

Classifier must be evidence-graph based:

```text
objective/source
 -> preflight/shadow
 -> first write
 -> check/build failure
 -> replan
 -> post-replan receipt/proof change
 -> acceptance
```

Output:

```yaml
cause: ...
confidence: ...
evidence_event_ids: [...]
label_version: taxonomy-v3
abstained: true|false
```

Rules:

- ambiguous => abstain;
- source mutation requires durable receipt/evidence;
- test-only correction != causal solution repair;
- probabilistic weak supervision only triages audit queue;
- no gaming positives for P4-C.

## 15.2. Casebook replay

Use only replayable incidents with same:

- task semantics;
- source snapshot;
- oracle;
- environment/tool contract;
- risk policy.

`provenance=benchmark` mandatory.

Casebook can prove:

- protocol feasibility;
- treatment overhead instrumentation;
- outcome recorder;
- contamination controls.

It cannot provide P5-B production efficacy evidence.

---

# 16. Implementation waves

## Wave 0 — Reconcile and freeze exact source

Objective:

- recheck root/branch/HEAD/upstream;
- reconcile any active/pending completion report;
- identify concurrent source owner/write lease;
- no conflicting writer on owned paths;
- source/product worktree clean excluding only canonical `.coding-tools` runtime-evidence fingerprint scope;
- freeze exact source/runtime proof identity.

No destructive reset/clean/rebase.

`.coding-tools/**` remains retained; only `ledger.sqlite3-shm` and `ledger.sqlite3-wal` are transient exceptions.

## Wave 1 — Semantic Gate Decomposition

Owned surfaces:

- `report_p4_readiness.py`;
- `p5_treatment.py`;
- `p5_measurement.py`;
- focused tests.

Output:

- separate P4-C/P4-E/P5-A/P5-B/P5-U/P5-C projections;
- legacy field/CLI compatibility explicit;
- no epoch opening;
- `automatic_start=false`.

Acceptance:

- P4-C strict fixtures unchanged;
- P4-C false may coexist with P5 experiment engineering readiness only when all non-P4 experiment gates pass;
- P5-C remains false without P5-B + P4-C + heterogeneity;
- public tool count remains 8.

## Wave 2 — Manifest + Atomic Assignment

Owned surfaces:

- `orchestration_ledger.py`;
- `workflow_tools.py`;
- `coordination.py`;
- `tool_schema.py` only if existing action schema requires extension;
- canonical JSON manifest;
- tests.

Required:

- minimal DB-level uniqueness contract or equally strong same-transaction idempotency proof;
- atomic block-slot consumption;
- stable assignment unit;
- epoch open/pause/close/hard-stop events;
- allocation concealment;
- restart-safe randomization sequence;
- common execution contract binding;
- environment fingerprint binding.

## Wave 3 — All-assigned ITT + Outcome Projection

Output:

- all assigned denominator;
- post-assignment replan count;
- primary first-pass endpoint;
- restricted-time endpoint;
- immediate quality fields;
- delayed quality/interference fields;
- adherence/crossover;
- funnel/SRM projection;
- organic P2 baseline remains separate.

## Wave 4 — Canary Analyzer + Stop Controller

Output:

- deterministic feasibility report;
- block replay;
- funnel integrity;
- missingness/adherence/overhead;
- pause/hard-stop;
- no efficacy decision.

Analyzer drift closes epoch.

## Wave 5 — P5-A0 Shadow A/A

Prerequisites:

- Waves 0–4 accepted;
- runtime-loaded fingerprints match;
- explicit operator epoch activation.

No treatment behavior. Close epoch after instrumentation criteria or max horizon.

## Wave 6 — Casebook Replay

Use P5 instrumentation in isolated benchmark pairs. Protocol defect => REPLAN before live treatment canary.

## Wave 7 — P5-A Treatment Canary

Prerequisites:

- P5-A0 accepted or explicitly terminal with understood nonblocking feasibility gap;
- casebook protocol proof accepted;
- exact source/runtime/manifest match;
- explicit operator activation.

Target 32 natural assigned tasks or lower honest count at max horizon.

Exit:

- FEASIBILITY_ACCEPTED;
- REPLAN;
- ABORT;
- INSUFFICIENT_FEASIBILITY_VOLUME.

No efficacy claim.

## Wave 8 — P5-B Confirmatory Experiment

Prerequisites:

- canary epoch closed;
- treatment bundle stable;
- estimand/intercurrent matrix frozen;
- target weights frozen;
- quality gate frozen;
- MERD/MDE/Nmax/spending frozen;
- blinded SSR rule frozen if enabled;
- operating-characteristic simulation accepted;
- analyzer golden tests pass;
- new explicit epoch.

No historical control and no silent epoch pooling.

## Wave 8B — P5-U Universal Policy Review

Separate from efficacy closeout.

Requires:

- P5-B positive under frozen primary;
- MERD/economics achieved;
- delayed quality/safety/integrity acceptable;
- operational overhead acceptable;
- separate operator/release acceptance.

## Wave 9 — P5-C Targeted Policy — HOLD

Requires:

- P5-B efficacy;
- P4-C strict signal;
- frozen predictor;
- treatment-by-signal interaction/HTE or policy-value evidence;
- generalization/economics/quality;
- separate production acceptance.

If universal policy is already simple, cheap and beneficial, do not force targeting complexity.

---

# 17. Test strategy — invariant-driven, not test-count-driven

Các cases dưới đây là **acceptance invariants**, không phải yêu cầu one-function-per-line. Ưu tiên parameterized/state-machine tests để giảm maintenance.

## 17.1. P4-C preservation

Must prove:

- rare-event snapshot does not fabricate validation;
- Wilson/Bonferroni/family/source/temporal/rolling gates remain strict;
- benchmark/synthetic/unlabeled never promote;
- no P5-A implication;
- automatic activation remains false.

## 17.2. Gate topology

Must prove:

- P5 experiment readiness can be independent of P4-C;
- readiness does not activate epoch;
- P5-B efficacy does not auto-promote universal policy;
- P5-C false without P4-C + randomized benefit heterogeneity;
- legacy fields/CLI are explicit aliases/deprecated, never silently redefined.

## 17.3. Assignment state-machine suite

Parameterize:

- duplicate identical assignment;
- conflicting assignment;
- duplicate slot;
- concurrent assignment;
- epoch close vs assignment race;
- restart/replay;
- retry/replan/resume/new run same task;
- late assignment;
- closed epoch;
- manifest drift;
- control contamination;
- treatment deviation;
- successor cannot replace predecessor failure.

## 17.4. A/A and canary analyzer

Must prove:

- A/A executes same control behavior in both shadow arms;
- assignment/output joins remain complete;
- no efficacy claim;
- same event prefix + manifest => same result;
- critical event stops enrollment;
- missing instrumentation pauses;
- analyzer hash mismatch fails closed.

## 17.5. ITT/outcome

Must prove:

- all assigned terminal states retained;
- crossover analyzed by assigned arm;
- pre-assignment replan excluded from treatment outcome;
- immediate missing quality not success;
- delayed follow-up overlap gets explicit interference status;
- missing cost != zero;
- accepted-only TTAR never replaces all-assigned economics;
- benchmark/historical rows never join confirmatory population.

## 17.6. Statistical analyzer

Must prove with independent golden vectors/simulation:

- registered information fractions map to correct boundary;
- unregistered efficacy look rejected;
- alpha budget not exceeded;
- harm/quality dominates efficacy;
- max-information inconclusive does not promote;
- blinded SSR cannot use arm labels or modify MERD/alpha/endpoint;
- null simulations preserve target Type-I error within frozen tolerance;
- MERD simulations achieve planned power within frozen tolerance.

## 17.7. Validation ladder

For each wave:

1. smallest affected unit/state-machine test;
2. relevant schema/contract check;
3. affected boundary integration;
4. exact-source EOCL acceptance;
5. broader suite only if cross-cutting boundary requires it.

Do not rerun unchanged proof on unchanged fingerprint.

---

# 18. Runtime artifacts and evidence retention

Canonical causal source remains ledger. Projection files are read models only.

Recommended projection tree:

```text
.coding-tools/evaluation/p5/<experiment_id>/
  activation-epoch.json
  eligibility-projection.jsonl
  enrollment-projection.jsonl
  assignment-projection.jsonl
  adherence-projection.jsonl
  outcome-projection.jsonl
  interference-projection.jsonl
  aa-report.json
  canary-report.json
  confirmatory-look-<n>.json
  closeout-report.json
```

Every report includes:

- observed Git HEAD;
- manifest hash;
- epoch id;
- analyzer hash;
- environment fp;
- ledger window/schema;
- ordered assignment digest;
- source/tool/evaluation/runtime fingerprints;
- assessed/eligible/enrolled/assigned/finalized counts;
- missingness/interference;
- open/incomplete blocks;
- decision vocabulary;
- claim allowed/forbidden.

No raw prompt, secret or private chain-of-thought in events.

---

# 19. Operator runbook

## 19.1. Before an implementation wave

1. Verify root/branch/HEAD/upstream.
2. Inspect relevant status/diff only.
3. Identify concurrent owners/write leases.
4. Reconcile pending completion reports.
5. Freeze objective, allowed paths and cheapest sufficient proof.
6. Preserve unrelated source and `.coding-tools` evidence.

## 19.2. Before A/A or treatment epoch activation

Required:

- source HEAD accepted;
- source/product worktree clean under canonical scope;
- no conflicting writer;
- manifest hash frozen;
- common execution contract frozen;
- assignment/analyzer golden tests pass;
- runtime-loaded source/manifest/tool/evaluation/environment/analyzer match;
- eight public tools observed;
- dry-run/prepare path does not activate treatment;
- operator explicitly authorizes exact experiment/epoch;
- pause/close/hard-stop path proven.

## 19.3. Enrolling a task

1. Assess arm-neutral eligibility.
2. Record eligibility/exclusion.
3. Record enrollment decision.
4. Atomically assign if enrolled.
5. Return authoritative assignment event/arm.
6. Enforce common execution + arm-specific protocol.
7. Reject write if ordering/contract invalid.
8. Record adherence/deviation.
9. Project terminal/immediate quality/delayed quality/interference.
10. Finalize outcomes according to frozen horizons.

## 19.4. Monitoring

A/A/canary operator sees:

- funnel counts;
- completed/open blocks;
- assignment/order violations;
- adherence;
- terminal/quality coverage;
- interference;
- critical harm;
- treatment overhead (P5-A only);
- source/runtime drift.

Confirmatory operator sees arm-level efficacy only at registered looks.

---

# 20. Pause, hard-stop and recovery

Immediate hard stop new enrollment on:

- critical/security/data-loss defect;
- authority/write-lease violation;
- wrong-source execution;
- assignment conflict or late assignment;
- corrupted assignment history;
- manifest/epoch/analyzer/control-plane drift;
- unsafe treatment breach.

Pause/investigate on:

- block mismatch;
- unexplained assignment/outcome loss;
- missing outcomes above frozen threshold;
- contamination/adherence anomaly;
- eligible-not-enrolled anomaly;
- runtime identity uncertainty;
- unexpected follow-up interference rate.

Recovery invariants:

- never delete failed assignment;
- never reassign to replace bad outcome;
- never rewrite ledger history;
- never treat unknown quality/cost as pass/zero;
- never reuse stale proof after fingerprint drift;
- never relax P4-C to recover P5;
- never pool protocol-changed epochs automatically.

---

# 21. P4-E / Taxonomy / Statistics — nonblocking research appendix boundary

Until P5-A closes, the following are **non-blocking unless they reveal a concrete integrity defect**:

- P4-E model choice;
- rare-event Firth/Bayesian experiments;
- weak-supervision implementation;
- GRF/EconML/HTE;
- switchback design;
- always-valid/e-process v2;
- broad cost optimizer;
- model-routing P7/P8.

Their findings may update later manifest versions but must not widen active Wave 1–4 scope.

---

# 22. Acceptance checklist

## Gate 0 — Source/authority

- [ ] Fresh root/branch/HEAD/upstream.
- [ ] Relevant concurrent edits reconciled.
- [ ] No conflicting writer/lease.
- [ ] Pending completion report reconciled.
- [ ] Exact-source required proof accepted.
- [ ] Source/product worktree clean under canonical scope.
- [ ] Freeze fingerprint recorded.

## Gate 1 — Semantics

- [ ] P4-C strict unchanged.
- [ ] P4-E separated.
- [ ] P5 experiment readiness independent of P4-C.
- [ ] P5-U separate from P5-B efficacy.
- [ ] P5-C requires P4-C + HTE/policy value.
- [ ] Legacy compatibility explicit.
- [ ] Automatic activation/promotion false.

## Gate 2 — Assignment/manifest

- [ ] Canonical JSON manifest frozen.
- [ ] Common execution contract frozen.
- [ ] Environment fp frozen.
- [ ] Stable assignment unit defined.
- [ ] DB-level uniqueness or equally strong same-transaction claim proven.
- [ ] Eligibility + enrollment before arm reveal.
- [ ] Assignment before arm action/write.
- [ ] Retry/replan/resume preserve arm.
- [ ] Block sequence replayable after restart.
- [ ] Close-vs-assign race serialized.
- [ ] Public tool count remains 8.

## Gate 3 — Measurement

- [ ] Every assignment remains ITT.
- [ ] Post-assignment replan scoped.
- [ ] Primary endpoint + H defined.
- [ ] Immediate quality/oracle fields defined.
- [ ] Delayed quality follow-up + interference explicit.
- [ ] Missing quality/cost semantics correct.
- [ ] Restricted-time endpoint exists.
- [ ] Funnel/SRM projection complete.
- [ ] Assigned vs received arm separate.

## Gate 4 — Analyzer/stop

- [ ] A/A/canary analyzer makes no efficacy claim.
- [ ] Deterministic golden vectors pass.
- [ ] Pause/hard-stop proven.
- [ ] Same prefix/manifest => same result.
- [ ] Analyzer drift closes epoch.

## Gate 5 — P5-A0 A/A

- [ ] Same control protocol both shadow arms.
- [ ] Assignment/order integrity complete.
- [ ] Funnel/outcome projection complete.
- [ ] No unexplained assignment loss.
- [ ] Epoch closed before treatment canary.

## Gate 6 — P5-A treatment canary

- [ ] Natural tasks only.
- [ ] No assignment/integrity violation.
- [ ] Treatment bundle executed as frozen.
- [ ] Overhead observable.
- [ ] Immediate quality complete.
- [ ] Delayed follow-up/interference tracked.
- [ ] No observed critical harm.
- [ ] No efficacy claim.
- [ ] Canary epoch closed before protocol change.

## Gate 7 — P5-B confirmatory

- [ ] Estimand/intercurrent matrix frozen.
- [ ] Target-population weights frozen.
- [ ] MERD/MDE/Nmax exact design frozen.
- [ ] Blinded SSR rule frozen if used.
- [ ] Operating-characteristic simulation passes.
- [ ] Alpha spending/harm/futility frozen.
- [ ] Efficacy viewed only at registered looks.
- [ ] Quality/safety/integrity hold.
- [ ] Decision reports uncertainty and claim boundary.

## Gate 8 — P5-U universal policy

- [ ] P5-B efficacy established.
- [ ] MERD/economics acceptable.
- [ ] Delayed quality/safety/integrity acceptable.
- [ ] Operational overhead acceptable.
- [ ] Separate release/operator acceptance.
- [ ] Automatic promotion remains false.

## Gate 9 — P5-C targeted policy

- [ ] P5-B efficacy established.
- [ ] P4-C strict signal validated.
- [ ] Predictor frozen.
- [ ] Treatment-by-signal/HTE or policy-value evidence validated.
- [ ] Generalization/economics/quality accepted.
- [ ] Separate production acceptance.

No checkbox may be waived by prose. Semantic waiver => authority + reason + new manifest/epoch.

---

# 23. Risk register

| Risk | Failure mode | Mitigation |
| --- | --- | --- |
| Stale state | Dated run status treated as current | Gate 0 fresh snapshot |
| Assignment race | Same task or slot gets two arms | DB-level uniqueness + one transaction |
| Re-randomization | Retry/replan gets new arm | Stable assignment unit |
| Control contamination | Treatment artifact leaks | Context isolation + common execution contract |
| Co-intervention | Treatment gets more compute/review | Freeze common execution contract |
| Selection bias | Easy tasks selectively enrolled | Eligibility/enrollment before reveal + funnel report |
| Survivor bias | Accepted-only RCT analysis | All-assigned ITT |
| Source follow-up interference | Later task changes same surface | Explicit overlap attribution status |
| Delayed outcome ambiguity | Follow-up silently changes primary | Primary immediate; delayed quality separate guardrail |
| Oracle scarcity | Historical workload != eligible workload | Prospective eligibility funnel |
| Optional stopping | Dashboard peeking | Registered looks only |
| Wrong Nmax | Historical rate differs from eligible cohort | Blinded SSR + OC simulation |
| Wrong target mix | 50/50 canary treated as production mix | Separate target-population weights |
| SRM blind spot | 50/50 assignment but differential attrition | Full funnel diagnostics |
| Rare harm | Canary zero harm overinterpreted | Hard stop + no absence-of-harm claim |
| P4-E leakage | Post-outcome features used | Strict prewrite ordering |
| Taxonomy gaming | Generic failures mapped to repair | Deterministic evidence + abstain |
| Cost fiction | Missing cost=0 | Unknown/unavailable |
| Overengineering | Experiment framework grows | V1 critical path only; no service/platform/tool #9 |
| Evidence loss | Runtime history ignored | `.coding-tools` retention invariant |
| False targeting | Prognostic risk != benefit | P5-C requires HTE/policy value |

---

# 24. Definition of Done

## Source implementation done

- Waves 1–4 accepted on exact source.
- Focused/state-machine/schema tests pass.
- P4-C unchanged.
- Eight-tool contract preserved.
- Manifest + assignment + ITT + analyzer + stop surfaces complete.
- No unrelated source changes.

## P5-A0 done

- Shadow A/A epoch explicitly activated and terminal.
- Both shadow arms received control workflow.
- Assignment/funnel/outcome instrumentation integrity established or exact feasibility blocker documented.
- No efficacy claim.

## P5-A done

- Treatment canary epoch explicitly activated and terminal.
- Every assignment retained.
- Protocol/adherence/overhead/quality/interference reported.
- No efficacy claim.

## P5-B done

- Confirmatory epoch reaches preregistered terminal decision.
- ITT effect + uncertainty reported.
- Quality/integrity/missingness/interference reported.
- Restricted-time economics reported.
- Claim limited to frozen population/epoch.

## P5-U done

- Universal-policy review separate from efficacy closeout.
- MERD/economics/quality/integrity pass.
- Separate release/operator acceptance.
- Automatic activation false.

## P5-C done

- P4-C + P5-B + treatment-benefit heterogeneity/policy value all exist.
- Target/source generalization accepted.
- Separate production acceptance.

`Code exists`, `source proof pass`, `runtime activated`, `A/A healthy`, `canary feasible`, `causal efficacy`, `universal promotion`, and `targeted promotion` are different states.

---

# 25. Immediate next action

Next material implementation workstream remains:

```text
P5 Gate Decomposition and Prospective Experiment Contract
```

Exact sequence:

1. Wait only for overlapping source owner/critical active wave to quiesce; do not wait for P4-C data.
2. Run fresh Gate 0.
3. Freeze Wave 1 owned files.
4. Implement semantic gate decomposition only.
5. Prove P4-C strict unchanged.
6. Implement Wave 2 atomic assignment with DB-level uniqueness or equivalent same-transaction invariant.
7. Implement Wave 3 all-assigned outcome/funnel projection.
8. Implement Wave 4 feasibility analyzer + stop controller.
9. Run P5-A0 shadow A/A before any treatment exposure.
10. Run casebook replay.
11. Open P5-A treatment canary only with explicit operator activation.
12. Close canary; freeze P5-B estimand, target weights, SSR/Nmax/spending and operating-characteristic simulation before confirmatory assignment.

Do **not** begin by training P4-E, importing an experimentation platform, creating synthetic repair tasks, building HTE, or changing model routing.

---

# 26. Method references

- King & Zeng — Logistic Regression in Rare Events Data.
- Wang — Logistic Regression for Massive Data with Rare Events, ICML/PMLR 2020.
- Pocock & Simon — Sequential treatment assignment with balancing for prognostic factors.
- Lan & DeMets — Discrete sequential boundaries for clinical trials.
- Johari, Pekelis & Walsh — Always Valid Inference: Continuous Monitoring of A/B Tests.
- Howard et al. — Time-uniform, nonparametric, nonasymptotic confidence sequences.
- Lin — Agnostic notes on regression adjustments to experimental data.
- CONSORT extension for randomized pilot/feasibility trials.
- ICH E9(R1) — Estimands and Sensitivity Analysis.
- Bojinov, Simchi-Levi & Zhao — Design and analysis of switchback experiments.
- Microsoft Experimentation Platform — A/A testing, SRM and data-quality diagnostics.
- ConfSeq — reference/golden implementation only, not production dependency v1.
- Snorkel — weak-supervision triage pattern only.
- Generalized Random Forests / EconML — P5-C research only after sufficient randomized data.

---

# 27. Final decision

Coding Web đã có đủ descriptive evidence để ưu tiên rework intervention research. Nó chưa có:

- a predictor-ready full historical P4-E matrix;
- randomized treatment evidence;
- confirmatory Nmax calibrated to the actual eligible population;
- treatment-benefit targeting evidence.

Hướng triển khai chuẩn:

```text
keep P4-C strict
  + keep P4-E coverage-first and advisory-only
  + implement P5 experiment integrity independently
  + prove instrumentation with P5-A0 A/A
  + run feasibility-only P5-A treatment canary
  + freeze and simulate P5-B confirmatory design
  + run prospective randomized ITT
  + evaluate universal policy separately
  + keep targeted policy locked until causal benefit heterogeneity is proven
```

Đây là tách đúng cấp bằng chứng: **không chờ thụ động, không hạ chuẩn, không thêm platform không cần thiết, và không biến statistical caution thành orchestration bureaucracy.**

---

# 28. Implementation status checkpoint — 2026-08-22

## 28.1 Scope and evidence classification

This checkpoint records the requested source implementation. It is **not** a claim that any live P5 epoch, treatment canary, efficacy result, promotion, package, release, or service activation occurred. The implementation deliberately leaves `execution_route=auto` fail-closed to deterministic and keeps the public `smart-v3` surface at eight tools.

| Boundary | Status at this checkpoint | Evidence / interpretation |
| --- | --- | --- |
| Gate 0 control plane | **OBSERVED; source dirty during implementation** | The checkout was on `main` at `0415538a0c8212d0d7e4b7217faad5b289020cff`; concurrent `.coding-tools` and test mutations were preserved. A manifest that requires clean, upstream-matched source cannot be opened from this implementation worktree. |
| P4-C | **UNCHANGED / SHADOW-ONLY** | The readiness reporter keeps validated predictive signals empty and does not treat P5 source availability as P4 predictive evidence. |
| P4-E | **ADVISORY / DEFERRED** | No predictive model, target, routing, or production action was enabled. |
| Wave 1 — semantic decomposition | **IMPLEMENTED + focused proof** | P5 source readiness is independent from legacy P4 predictive readiness; the old coupled treatment readiness remains explicitly deprecated and cannot activate an epoch. |
| Wave 2 — manifest and assignment | **IMPLEMENTED + focused proof** | Manifest v2 validation, secret-handle seed commitment, arm-neutral eligibility/enrollment, stable task assignment identity, DB uniqueness, and same-transaction event/table recording are implemented. |
| Wave 3 — ITT measurement | **IMPLEMENTED + focused proof** | Every assignment has an immutable outcome projection; missing outcomes remain `unknown_not_finalized`, never success/zero, and P5-A0 maps both labels to the control protocol. |
| Wave 4 — analyzer and stop controller | **IMPLEMENTED + focused proof** | The deterministic analyzer evaluates funnel/integrity only, detects analyzer-source drift, and supports pause/close/hard-stop. Critical security/data-loss outcomes hard-stop the epoch. |
| P5-A0 | **HOLD — no production/runtime epoch opened** | Requires an explicit frozen manifest, secret-handle seed in the live broker, natural eligible work, stable oracle, source/runtime identity match, no active workspace writer, and named operator authority. |
| P5-A / P5-B / P5-U / P5-C | **NOT STARTED** | No treatment assignment, causal estimate, confirmatory decision, universal promotion, targeted-policy evidence, or release acceptance exists. |

## 28.2 Delivered source contract

The source implementation is intentionally small and uses the existing control plane:

1. `task_control(action="p5")` is the only new entry point; no ninth tool, automatic activation, automatic routing, or automatic production promotion was introduced.
2. A P5 manifest freezes source/upstream identity, runtime/tool/evaluation identities, analyzer fingerprint, common execution contract, arm-neutral enrollment contract, blocked 1:1 allocation, seed commitment, outcome contract, missing-data semantics, and stop rules. The published JSON file is a `template_only` example and is rejected if used to open an epoch.
3. The raw randomization seed is resolved only through a `secret://` broker handle. Only its commitment and the opaque handle are durable; raw seed material, prompt, patch, stdout, and stderr are rejected from P5 event payloads.
4. Enrollment is persisted before reveal. Assignment is idempotent for the same stable task unit and is atomically assigned to a unique block slot. P5-A0 receives control for both assigned labels; P5-A/P5-B retain assigned-vs-received arm and protocol/adherence records.
5. Opening verifies actual source/runtime/analyzer identities and rejects an active `workspace` write fence when the manifest requires writer quiescence. Assignment/order, source identity, analyzer drift, and critical security/data-loss violations produce integrity evidence and hard-stop where required.
6. The analyzer intentionally reports feasibility/integrity/funnel/ITT accounting only. It contains no efficacy estimator and cannot create a universal or targeted promotion decision.
7. A P5 assignment can reach `agent_workflow` only as `p5_assignment_id` on `feature`/`bugfix` `execute` or `run`. After the normal workspace write fence is acquired and before any directory or patch operation, the runtime atomically records `p5_workflow_prewrite_bound` with the P5 assignment, workflow, EOCL run/wave, and lease id. The binding rejects a missing protocol start, epoch pause/close, terminal outcome, task-class mismatch, or conflicting prior lease. A pre-write binding is evidence of write authority, not a claim that a physical mutation later succeeded; the terminal outcome retains that distinction.
8. `first_write_at` is runtime-owned: direct `task_control` calls cannot set it. The P5 store only fills it as part of the immutable pre-write lease binding. Electron's trusted native parent may map an externally delivered `CODING_TOOLS_P5_A0_SEED` value into the content-free `secret://experiment/p5/a` broker handle. The child MCP environment does not receive the raw environment name, and no raw seed is written to source, manifest, `.coding-tools`, log, or chat.

## 28.3 Proof executed on the implementation source

Focused source tests cover manifest validation, non-automatic secret-backed epoch opening, enrollment-before-assignment, idempotence, four-way concurrent block allocation, A/A control receipt, all-assigned ITT accounting, critical hard-stop, public-tool count, task-control dispatch, source/runtime drift, active-writer rejection, P4 readiness semantics, legacy planner decoupling, measurement separation, ledger chain compatibility, durable coordination state, runtime activation boundaries, solution economics, and rework diagnosis.

Final focused command, run from `resources/coding-tools-mcp` on the final source, was:

```text
python -m pytest tests/test_p5_experiment.py tests/test_p5_treatment.py tests/test_p5_measurement.py tests/test_p4_readiness.py tests/test_orchestration_ledger.py tests/test_coordination_state.py tests/test_durable_coordination_runtime.py tests/test_efficiency_runtime.py tests/test_runtime_activation.py tests/test_solution_economics.py tests/test_rework_diagnosis.py -q
```

It passed **124 tests in 32.00 seconds** at the original source checkpoint. The follow-on P5 write-binding/runtime-secret wave added focused P5 and Electron checks, then moved provider-telemetry, P4 solution-shadow control, and HTTP-origin validation into their owning modules. The final focused Python set passed **126/126 in 28.32 seconds**; `npm test` passed **247/247**; and `python scripts/check_module_size.py` now passes with `server.py` at 3,492 lines, `coordination.py` at 1,600, and `mcp_http_handler.py` at 1,579. The canonical ledger remains exactly 5,000 and every dedicated P5 module remains below the generic 1,600-line budget. Commit/source identity and live activation must still be observed at delivery time rather than inferred from this source checkpoint.

## 28.4 Explicit non-claims and next operator action

- No P5 epoch was opened in the repository's canonical runtime ledger; temporary test epochs existed only in temporary test directories.

- No P5-A0 A/A task, P5-A treatment task, causal effect, safety conclusion, CAR, TTAR improvement, confirmatory Nmax decision, or production promotion was measured.
- The local reporter may prepare the ledger schema when it opens the canonical database, but schema preparation is not experiment activation and creates no enrollment or assignment.
- Before P5-A0, create a real manifest from the template with fresh source/runtime/environment identities and the externally managed `secret://experiment/p5/a` handle; run Gate 0 again on a clean, upstream-matched checkout; verify no active writer; obtain explicit operator authority and natural representative tasks; then open exactly one epoch and retain its ledger evidence. An Electron development launch may receive its opaque handle only by externally injecting `CODING_TOOLS_P5_A0_SEED` into the trusted parent process; it must never be persisted in project files or ordinary settings.
- P5-A treatment remains conditional on a terminal P5-A0 integrity/feasibility review. P5-C remains locked until P4-C and randomized treatment-benefit heterogeneity/policy value are separately proven.

## 29. Continuation checkpoint — Wave 3 funnel completion and rebaseline

This section records a later implementation boundary; it does not rewrite the earlier checkpoint above.

- An explicit P5-A0 epoch (`e91c6b09…85073`) was opened only after its frozen manifest, upstream-matched code-bearing source, no active writer, and opaque seed handle were verified. Its analyzer reported zero assessed/enrolled/assigned rows and no integrity event.
- Before any enrollment, the epoch was deliberately closed with the durable reason `zero_enrollment_rebaseline_for_wave3_funnel_integrity_completion`. There was no assignment, arm action, write binding, outcome, treatment exposure, or efficacy claim to discard. Closing it avoids carrying incomplete instrumentation into a live natural cohort.
- Wave 3 now projects the complete durable funnel by immutable assignment arm and workflow stratum: protocol start, pre-write binding, runtime-owned first-write record, terminal outcome, immediate quality, delayed follow-up, and interference. It also reports stage losses, received-arm crossover, orphan rows, and the enrolled-to-assigned reconciliation.
- The SRM control is structural rather than an underpowered p-value: every completed feature/bugfix block must contain slots `0..3` and the frozen 2/2 arm allocation. A partial live block is explicitly pending; an invalid completed block, orphan row, arm mismatch/crossover, or pre-write binding without a runtime first-write record is a hard-stop reason. The ledger analyzer terminalizes a live epoch on such a hard-stop result.
- New focused golden/state-machine coverage proves a valid concurrent 2/2 block, complete funnel projection through an A/A control receipt, and hard-stop on a malformed completed block. This remains source proof only until a newly activated runtime reports the same analyzer fingerprint and a fresh A/A epoch is explicitly opened.

The next action is therefore operational, not another source claim: commit/push this bounded Wave 3 change with the required `.coding-tools` evidence, controlled-restart the owned MCP so it loads the new source, verify the encrypted secret-handle commitment without exposing its value, and open a new P5-A0 manifest. Only a natural feature/bugfix first created after that opening can enter the A/A cohort.
