# CODING WEB — REWORK DECISION SCIENCE & EXECUTION DOCTRINE

> **Decision Doctrine ID:** `CW-RDS-20260822-v1`
>
> **Ngày:** 2026-08-22, Asia/Bangkok
>
> **Workspace:** `E:\DEV\Codex-web`
>
> **Loại tài liệu:** phương pháp luận quyết định + phân tích định lượng + chiến lược thực thi + anti-overengineering control
>
> **Trạng thái:** NORMATIVE STRATEGIC DECISION — không tự động kích hoạt treatment/promotion
>
> **North Star:** **minimize Time-to-Accepted-Result under fixed quality/safety/authority floors**
>
> **Automatic P5 activation:** `false`
>
> **Automatic production promotion:** `false`
>
> **Public MCP tool target:** `smart-v3 = 8`

---

# 0. QUYẾT ĐỊNH ĐIỀU HÀNH

Coding Web đã có đủ dữ liệu để **quyết định hướng tối ưu**, dù chưa có đủ dữ liệu để tuyên bố một treatment cụ thể giảm chính xác bao nhiêu phần trăm rework.

Đây là hai câu hỏi hoàn toàn khác nhau:

```text
QUESTION A — Strategy selection
Dữ liệu hiện có đủ để biết nên đánh vào đâu trước hay chưa?

ANSWER: CÓ.

QUESTION B — Causal treatment effect
Một treatment cụ thể giảm rework/TTAR bao nhiêu với uncertainty bao nhiêu?

ANSWER: CHƯA; cần randomized prospective evidence.
```

Sai lầm cần chấm dứt là dùng sự chưa hoàn thiện của Question B để trì hoãn Question A. Với 456 accepted runs, 188 repaired accepted results, 359 replans, 365 observed failure events, 71 representative P4 terminal tasks, 4 P5 lifecycle epochs và hàng trăm EOCL histories, dự án **không còn thiếu dữ liệu để chọn chiến lược**.

Quyết định chuẩn từ đây là:

> **STOP BUILDING NEW CONTROL ARCHITECTURE → ELIMINATE KNOWN DETERMINISTIC REWORK → RUN REAL P5 RANDOMIZED LEARNING → OPTIMIZE TTAR TAIL.**

Chiến lược được khóa thành ba chương trình duy nhất:

1. **Deterministic Rework Elimination (DRE)** — loại bỏ source/base drift, acceptance/proof correction và generic failure ambiguity bằng engineering deterministic.
2. **P5 Causal Learning (P5-CL)** — dùng prospective randomized experiment để đo phần rework thực sự có thể giảm bằng causal-solution discipline; P4 predictor không còn là blocker của A/A/treatment learning.
3. **Tail Economics (TE)** — tối ưu P90/P95 Time-to-Accepted-Result và forensic các workflow có runaway latency; không dùng average/replan count làm proxy duy nhất.

P4 từ đây là:

> **PASSIVE MEASUREMENT SENSOR, NOT CRITICAL-PATH DECISION ENGINE.**

Không xây thêm P4 model/framework trong giai đoạn hiện tại. Chỉ mở lại modeling khi positive causal outcomes đạt một ngưỡng đã định trước và có đủ variation theo family/source/time.

P5 từ đây là:

> **EXPERIMENT SYSTEM READY IN PRINCIPLE; THE BOTTLENECK IS REAL FUNNEL THROUGHPUT, NOT MORE FRAMEWORK.**

Không thêm P5 service/tool/database/abstraction mới nếu không có một observed integrity defect mà primitives hiện tại không xử lý được.

---

# 1. PHẠM VI, THẨM QUYỀN VÀ THỨ TỰ SỰ THẬT

## 1.1. Vai trò của tài liệu này

Tài liệu này không thay thế current-state authority. Nó khóa **phương pháp ra quyết định** để tránh thay đổi chiến lược liên tục theo từng snapshot mới.

Thứ tự sự thật vẫn là:

1. current implementation + exact focused/live proof;
2. runtime contract + EOCL authority;
3. `AGENTS.md`;
4. `docs/CURRENT_STATE.md`;
5. `docs/ROADMAP.md`;
6. maintained subsystem docs;
7. tài liệu này cho decision doctrine và interpretation;
8. historical ledger/reports cho forensic reconstruction;
9. dated research docs cũ hơn.

## 1.2. Quan hệ với các tài liệu trước

Tài liệu này **không xóa lịch sử** và không tuyên bố các research docs trước sai toàn bộ.

Nó chốt các điều chỉnh quan trọng:

- Giữ doctrine **LEAN CONTROL + RICH EVIDENCE + REWORK-FIRST ECONOMICS**.
- Giữ P4 strict statistical integrity.
- Giữ P4/P5 v2 gate decomposition: **P4 predictive readiness không phải prerequisite của P5 experiment integrity/A0**.
- Giữ P5-A0 trước treatment.
- Giữ automatic activation/promotion = false.
- Thay cách ưu tiên: **known deterministic rework + P5 evidence acquisition + tail economics** trở thành critical path; additional P4 model work bị đưa ra khỏi critical path.

## 1.3. Quy tắc không hồi tố

Một finding mới không được tự động mở lại architecture đã accepted.

Chỉ mở lại khi có ít nhất một trigger:

- defect quan sát được;
- invariant bị vi phạm;
- source/runtime contract thay đổi;
- treatment evidence bác bỏ giả định hiện tại;
- consumer/product requirement mới;
- security/data/authority concern mới;
- effect-size/economic evidence chứng minh một workstream khác có expected value cao hơn rõ rệt.

Không mở lại chỉ vì:

- có thêm sample;
- một metric dao động nhỏ;
- một mô hình mới hấp dẫn;
- upstream có feature mới;
- muốn đạt “100% completeness”.

---

# 2. SNAPSHOT DỮ LIỆU QUYẾT ĐỊNH HIỆN TẠI

Snapshot dùng để xây doctrine này được tái-baseline tại HEAD:

```text
main = origin/main
HEAD = 12e0de80681a248060ed82e69813aa0c90c6d98f
runtime = 0.4.3
smart-v3 public tools = 8
active EOCL runs = 0
stale orchestration runs = 0
orphaned background operations = 0
orphaned idempotency records = 0
```

Một hygiene artifact ngoài canonical root đang tồn tại:

```text
resources/coding-tools-mcp/.coding-tools/orchestration/ledger.sqlite3
```

Artifact này làm current P5 clean-source gate fail. Đây là path/workdir hygiene issue, không phải bằng chứng P5 architecture hỏng.

## 2.1. P2/P5 observational baseline

```text
accepted_runs          = 456
first_pass_accepted    = 268
repaired_accepted      = 188
replan_count           = 359
first_pass_rate        = 58.7719%
repaired_rate          = 41.2281%
```

TTAR:

```text
first_pass_p50         = 66.458 s
first_pass_p90         = 454.390 s
repaired_p50           = 302.914 s
repaired_p90           = 3,011.437 s
p50 repaired penalty  = 4.558x
p90 repaired penalty  = 6.627x
```

## 2.2. Historical trajectory

| Snapshot | Accepted | Repaired | Repaired rate | Replans |
|---|---:|---:|---:|---:|
| Frozen P2 | 449 | 183 | 40.7572% | 347 |
| Intermediate | 450 | 184 | 40.8889% | 351 |
| Later | 454 | 187 | 41.1894% | 356 |
| **Current** | **456** | **188** | **41.2281%** | **359** |

Từ frozen 449 tới current 456:

```text
+7 accepted
+2 first-pass
+5 repaired
+12 replans
```

Cohort mới quá nhỏ để dùng như một formal trend estimate, nhưng đủ để kết luận:

> **Không có bằng chứng rằng rework tự biến mất nhờ hardening hiện tại.**

## 2.3. Workflow strata

### Feature

```text
n = 129
first-pass = 59
repaired = 70
repaired rate = 54.2636%
first-pass p90 = 580.301 s
repaired p90 = 2,648.443 s
```

### Bugfix

```text
n = 99
first-pass = 60
repaired = 39
repaired rate = 39.3939%
first-pass p90 = 259.577 s
repaired p90 = 3,039.746 s
```

Bugfix repair tail multiplier:

```text
3,039.746 / 259.577 ≈ 11.71x
```

### Diagnose

```text
n = 88
repaired rate = 31.8182%
first-pass p90 = 445.815 s
repaired p90 = 19,348.140 s ≈ 5.37 h
```

Diagnose repair incidence không cao nhất, nhưng tail latency là anomaly rất lớn.

## 2.4. P4 current state

```text
representative_terminal_tasks = 71
causal_solution_repair        = 2
causal_solution_nonrepair     = 51
causal_unknown                = 18
validated_signals             = []
```

Known causal repair prevalence:

```text
2 / (2 + 51) = 3.7736%
```

Measurement drift:

```text
representative_base_head_count = 23
representative_worktree_fingerprint_count = 90
source_state_drift_observed = true
IID assumption = false
```

Low-variance signals:

```text
oracle_strength = strong for 71/71
root_cause_confidence = high for 71/71
```

Hai signal này có Brier gain bằng 0 vì không có discriminative variation.

## 2.5. Failure taxonomy

```text
total failure events     = 365
mapped/classified        = 177
unclassified             = 188
mapped coverage          = 48.4932%
```

Trong 188 unclassified:

```text
CHECK_FAILED               = 107
BUILD_VERIFICATION_FAILED  = 53
combined                   = 160 / 188 = 85.1%
```

Prospective schema đã được triển khai:

```text
p2_failure_observation_v3
historical_backfill = false
legacy generic detail is not inferred
```

Đây là đúng: không bịa causal history để làm tỷ lệ đẹp hơn.

## 2.6. Known mapped causes

```text
source_base_drift events       = 66
acceptance_correction events   = 56
patch_context_ambiguity        = 35
runtime_tool_failure           = 8
proof_timeout                  = 2
```

Patch preflight đã chặn:

```text
151 known no-write failures
```

bao gồm 104 ambiguous context, 39 context-not-found, 5 patch-failed và 3 not-found.

## 2.7. P5 empirical state

```text
P5 experiment epochs              = 4
P5 enrollment decisions           = 0
P5 assignments                    = 0
P5 arm protocol starts            = 0
P5 assignment outcomes            = 0
P5 workflow bindings              = 0
```

Cả bốn epoch đều đã đóng; epoch cuối cùng được đóng zero-data đúng fail-closed.

Điều này chứng minh lifecycle/integration control, **không chứng minh A/A health hoặc treatment efficacy**.

---

# 3. PHÂN TÍCH CỐT LÕI: 41% REWORK KHÔNG PHẢI 41% “AI CHỌN SAI LỜI GIẢI”

Đây là kết luận quan trọng nhất của toàn bộ chương trình.

Ta đang quan sát hai đại lượng:

```text
A. Process/economic rework rate ≈ 41.23%
B. Known causal-solution repair prevalence ≈ 3.77%
```

Chúng không mâu thuẫn. Chúng đo hai cấp khác nhau.

## 3.1. Mô hình phân rã

```text
TOTAL ACCEPTED-RESULT REWORK
│
├── SYSTEM / CONTROL-PLANE REWORK
│   ├── source/base drift
│   ├── stale/mismatched execution identity
│   ├── acceptance/proof correction
│   ├── verification/build/check semantics
│   ├── patch-context mechanics
│   ├── runtime/environment/recovery
│   └── permissions/ownership/contract errors
│
└── SOLUTION-QUALITY REWORK
    ├── wrong causal root cause
    ├── wrong solution scope
    ├── inadequate discriminator
    ├── incomplete oracle expectation
    └── over/under-sized change surface
```

Phần trên phải được xử lý bằng deterministic control-plane engineering. Phần dưới mới là target hợp lý của P5 Lean Causal Fix treatment.

## 3.2. Tại sao distinction này thay đổi roadmap

Nếu coi mọi replan là model reasoning failure, dự án sẽ liên tục:

- thêm predictor;
- đổi model;
- tăng reasoning effort;
- thêm reviewer;
- thêm context;
- thêm routing logic.

Trong khi rất nhiều failure thực tế có causal mechanism hoàn toàn deterministic.

Ví dụ:

```text
HEAD drift giữa execution và proof
```

không được chữa bằng model thông minh hơn.

```text
Filtered test green nhưng intended test không chạy
```

không được chữa bằng thêm context.

```text
Acceptance phát hiện no-op sau khi đã chạy broad proof
```

không được chữa bằng model router.

Vì vậy từ đây phải dùng nguyên tắc:

> **Match intervention class to failure mechanism.**

Không để một treatment chịu trách nhiệm cho failure class mà nó không tác động causal lên được.

---

# 4. NORTH STAR VÀ HỆ THỐNG ĐO LƯỜNG CHUẨN

## 4.1. North Star

Tối ưu:

> **Time-to-Accepted-Result (TTAR) dưới quality, security, data, authority và proof floors cố định.**

Không tối ưu riêng:

- token;
- tool calls;
- model calls;
- LOC;
- agent count;
- replan count;
- average latency;
- CPU utilization.

Các biến trên là explanatory/supporting metrics.

## 4.2. Lexicographic objective

Thứ tự quyết định:

1. correctness/security/data integrity;
2. authority/write/proof integrity;
3. quality noninferiority/hard floor;
4. first-pass accepted outcome;
5. TTAR distribution, đặc biệt P90/P95;
6. repair/replan burden;
7. total accepted-result cost khi coverage đủ;
8. human/operator burden;
9. simplicity/maintainability khi các phương án gần tương đương.

Một optimization giảm token nhưng làm P90 TTAR xấu đi không được gọi là cải tiến.

## 4.3. Primary operational metrics

```text
first_pass_accepted_rate
repaired_rate
TTAR p50
TTAR p90
TTAR p95 khi đủ sample
restricted_time_to_acceptance_H
critical_defect_rate
rollback/manual_rescue rate
```

## 4.4. Supporting metrics

```text
replan_count
proof duration
source-drift frequency
acceptance-correction frequency
failure taxonomy coverage
tool/model calls
token/provider cost when observed
operator interventions
```

Supporting metric không được tự promotion policy.

---

# 5. TẠI SAO TAIL ECONOMICS PHẢI ĐƯỢC NÂNG LÊN PRIMARY

Median penalty hiện khoảng 4.56x, nhưng P90 penalty đã lên 6.63x.

Từ frozen P2 tới hiện tại:

```text
repaired p90:
2,393.707 s -> 3,011.437 s

increase:
617.730 s ≈ 10.30 min ≈ 25.8%
```

First-pass p90 không tăng tương ứng.

Điều này gợi ý distribution không chỉ bị shift toàn bộ; **right tail đang kéo dài**.

Một hệ thống agent production có thể chấp nhận một tỷ lệ repair nhất định nếu repair nhỏ và bounded. Nó trở nên đắt khi repair tạo runaway sequence:

```text
repair
 -> re-localize
 -> new wave
 -> broader test
 -> drift
 -> reproof
 -> acceptance correction
 -> another wave
```

Do đó mục tiêu khoa học đúng không phải:

```text
minimize P(replan)
```

mà là:

```text
minimize E(TTAR)
+ constrain upper-tail TTAR
+ preserve quality/safety
```

Đây là lý do Diagnose cần một forensic tail study riêng dù repaired rate của nó thấp hơn Feature.

---

# 6. QUYẾT ĐỊNH NÀO ĐÃ ĐỦ BẰNG CHỨNG — KHÔNG CHỜ THÊM

Các quyết định dưới đây được xem là **strategy-closed** cho tới khi có falsifying evidence.

## D1 — Rework là cost center vật chất

Đủ bằng chứng từ 456 accepted results và TTAR penalty.

**Không nghiên cứu lại câu hỏi “rework có đáng quan tâm không?”**

## D2 — Feature + Bugfix là population đúng cho P5 initial experiment

Feature có incidence cao; Bugfix có severe tail penalty. Cả hai tạo expected value rõ.

Giữ stratification theo workflow.

## D3 — P4 predictive readiness không chặn P5-A0/P5-A learning

P4 predictor trả lời prognostic question; P5 randomized experiment trả lời treatment-effect question.

Không buộc prediction phải hoàn hảo trước khi học causal treatment.

## D4 — P4 modeling không còn là critical-path engineering

Với 2 positives, 23 source states, 90 fingerprints và constant predictors, thêm modeling bây giờ có marginal expected value thấp.

P4 chuyển thành passive collection.

## D5 — Không thêm P5 architecture trước real sample

P5 đã có đủ primitives. Zero enrollment/assignment là funnel-throughput problem.

## D6 — Source/base drift và acceptance correction là deterministic priorities

66 + 56 mapped events đủ để justify engineering intervention mà không cần randomized trial.

## D7 — Generic taxonomy ambiguity phải được giải prospective tại event source

160/188 unknown nằm trong CHECK/BUILD generic classes. Không backfill suy đoán.

## D8 — Tail latency cần workstream riêng

Diagnose p90 repaired ~5.37 giờ và Bugfix ~50.7 phút đủ để justify forensic tail analysis.

---

# 7. QUYẾT ĐỊNH NÀO CHƯA ĐƯỢC PHÉP TUYÊN BỐ

Không được claim:

- Lean Causal Fix Gate giảm rework X%;
- P5 treatment noninferior về quality;
- feature hay bugfix hưởng lợi treatment nhiều hơn;
- P4 predictor đủ để target treatment;
- patch preflight “cứu” 151 tasks;
- source-drift fix đã giảm causal rework bao nhiêu;
- CAR giảm bao nhiêu khi cost coverage chưa đầy đủ;
- P5-A0 instrumentation healthy khi chưa có natural assignments.

Đây là claim boundaries, không phải blocker của strategy execution.

---

# 8. CHƯƠNG TRÌNH 1 — DETERMINISTIC REWORK ELIMINATION (DRE)

Mục tiêu DRE:

> **Loại các rework mechanism mà ta đã biết nguyên nhân và không cần randomized model experiment để hành động.**

Không biến DRE thành một architecture phase mới. Đây là một tập small causal fixes có metric rõ.

## 8.1. DRE-R1 — Source/Base Drift Suppression

Evidence:

```text
66 mapped source_base_drift events
37 affected repaired runs trong historical reporter
```

### Required invariant

Mỗi material wave phải freeze:

```text
base_head
source/worktree fingerprint
owned surface
contract fingerprint
runtime/evaluation fingerprint khi relevant
```

### Decision rule

Nếu fingerprint drift trước proof/acceptance:

```text
DO NOT reuse stale proof
DO NOT silently rebase
DO NOT continue under old causal interpretation
CLASSIFY drift
REPLAN only with explicit new base/evidence
```

### Engineering direction

Ưu tiên:

- exact-source proof binding;
- source-owner fencing;
- early base-drift detection;
- explicit stale-proof rejection;
- avoid full rerun nếu unaffected exact proof remains valid;
- distinguish P5 lifecycle anchor from real execution owner;
- prevent workdir/path leakage that creates secondary ledgers/checkouts.

### Success metric

Không cần “0 forever” ngay lập tức. Theo dõi prospective:

```text
BASE_DRIFT events per 100 accepted tasks
BASE_DRIFT-induced replans per 100 tasks
tail TTAR of drift-affected tasks
```

Nếu sau đủ prospective volume rate không giảm, re-open mechanism analysis; không thêm abstraction trước.

## 8.2. DRE-R2 — Acceptance Correction Shift-Left

Evidence:

```text
56 acceptance_correction events
44 affected runs
```

Đây là loại rework đắt vì lỗi thường được phát hiện muộn sau mutation/proof.

### Goal

Dịch càng nhiều acceptance discriminators càng tốt về PREFLIGHT/early PROVING.

### Required preflight contract

```text
OBJECTIVE
OBSERVABLE DONE
PROTECTED INVARIANTS
EXACT SOURCE/BASE
EXPECTED MATERIAL CHANGE
CHEAPEST DISCRIMINATING ORACLE
CREDIBLE ADJACENT RISK
NON-GOALS
```

### Anti-false-green rule

Trước broad proof, verify một trong các điều sau tùy task:

- intended source symbol/path thực sự thay đổi;
- expected invariant changed;
- exact test identity tồn tại và chạy;
- no-op outcome được detect;
- proof binds đúng fingerprint;
- generated report binds đúng effective wave objective.

### Economic rationale

Phát hiện no-op hoặc wrong-scope ở phút 1 tốt hơn phát hiện ở phút 20 sau broad tests.

### Success metric

```text
acceptance_correction events per 100 accepted tasks
median/p90 time spent before acceptance correction is detected
false-green/no-op correction count
```

## 8.3. DRE-R3 — Prospective Failure Detail at Event Source

Evidence:

```text
188 unknown
160 (85.1%) = CHECK_FAILED + BUILD_VERIFICATION_FAILED
```

### Principle

Không dùng ML classifier để đoán generic historical failure.

Ghi structured detail tại nơi failure sinh ra:

```yaml
failure_detail:
  stage: preflight|build|test|proof|acceptance|runtime
  family: compile|lint|format|unit_test|integration_test|schema|environment|dependency|timeout|assertion|unknown
  command_class: ...
  exit_class: ...
  oracle_id: ...
  source_changed_since_start: true|false|unknown
  baseline_failure_known: true|false|unknown
  environment_change_observed: true|false|unknown
  timeout_observed: true|false
  deterministic_subtype: ...
```

Content-free, bounded, no raw prompt/output required.

### Success metric

Prospective detail coverage, **không phải historical coverage**:

```text
new_generic_failure_detail_coverage >= 90%
```

sau khi đủ volume hợp lý.

Nếu coverage thấp, sửa instrumentation. Không backfill lịch sử bằng inference.

## 8.4. DRE-R4 — Patch Layer: Maintenance Mode

Patch preflight đã chặn 151 no-write failures và ambiguity count không tiếp tục tăng trong latest delta.

Kết luận:

> Patch layer chuyển sang maintenance, không còn là primary innovation target.

Chỉ mở lại nếu prospective patch ambiguity rate tăng hoặc xuất hiện failure mechanism mới.

---

# 9. CHƯƠNG TRÌNH 2 — P5 CAUSAL LEARNING (P5-CL)

## 9.1. Scientific question

Trên natural eligible Feature/Bugfix tasks, giữ nguyên common execution/safety contract:

> **Lean Causal Fix discipline có làm tăng first-pass acceptance và/hoặc giảm restricted TTAR mà không làm xấu quality/safety/integrity hay không?**

Không hỏi:

> “P5 có chữa toàn bộ rework không?”

Treatment không được kỳ vọng chữa source drift, runtime crash hay permission failure.

## 9.2. P5 bottleneck hiện tại

Hiện là:

```text
0 enrollment decisions
0 assignments
0 outcomes
```

Ta chưa biết funnel nghẽn ở đâu vì chưa có assessed-stage accounting cho mọi natural task.

Do đó thay đổi duy nhất đáng ưu tiên ở P5 trước A0 là:

> **AUTO-ASSESS, NOT AUTO-ENROLL.**

### Policy

```text
AUTO ASSESS natural feature/bugfix       = YES
AUTO RECORD eligible/ineligible reason   = YES
AUTO ENROLL                              = NO
AUTO ASSIGN without enrollment           = NO
AUTO TREAT                               = NO
AUTO PROMOTE                             = NO
```

Auto-assess là measurement, không phải treatment authority.

## 9.3. A0 minimum evidence horizon

A/A không dùng để prove efficacy. Nó chỉ prove instrumentation integrity.

Do đó không cần hàng trăm samples.

Default progression:

```text
Feature: >= 1 complete randomized block
Bugfix:  >= 1 complete randomized block
```

Nếu block size 4 được giữ:

```text
minimum structural A/A target ≈ 8 natural assignments
```

Có thể tiếp tục tới ~16 nếu thuận lợi, nhưng không biến A/A thành một cohort nghiên cứu vô hạn.

### A0 exit criteria

```text
duplicate assignment = 0
late assignment = 0
assignment loss = 0
conflicting block slot = 0
unexplained arm crossover = 0
ITT join loss = 0
unknown silently converted to success = 0
restart/replay corruption = 0
funnel projection completeness = 100% for finalized rows
```

Nếu một stratum không có volume trong predeclared horizon:

```text
INSUFFICIENT_FEASIBILITY_VOLUME
```

Không manufacture tasks.

## 9.4. Treatment canary sau A0

Sau A0 integrity pass, mở P5-A treatment canary.

Recommended operational target:

```text
~32 natural assigned tasks
16 feature
16 bugfix
16 control
16 treatment
```

Đây là **feasibility target**, không phải confirmatory power claim.

Canary trả lời:

- treatment có execute đúng không;
- overhead có đo được không;
- có safety/quality signal xấu không;
- repair/TTAR direction có đáng để tiếp tục không;
- có unexpected failure mechanism không.

Canary không tuyên bố production efficacy.

## 9.5. Confirmatory P5-B

Chỉ freeze sau canary.

Phải preregister:

- estimand;
- horizon H;
- primary endpoint;
- target population weights;
- feature/bugfix strata;
- quality floor/noninferiority;
- intercurrent event matrix;
- missingness;
- Nmax/information;
- MERD;
- sequential look rule;
- analyzer hash/golden vectors.

## 9.6. P5 không được phụ thuộc P4 target predictor ở giai đoạn learning

P4 answers:

```text
Which pre-mutation signals predict repair risk?
```

P5 answers:

```text
Does treatment change outcome?
```

Một prognostic signal không chứng minh treatment benefit; một treatment có thể beneficial ngay cả khi ta chưa biết target ai.

Do đó:

```text
P5-A0/P5-A/P5-B learning
    independent from P4-C predictor readiness

P5-C targeted policy
    requires P4-C + P5-B + treatment heterogeneity/policy value
```

Khóa distinction này để không quay lại circular waiting.

---

# 10. CHƯƠNG TRÌNH 3 — TAIL ECONOMICS (TE)

## 10.1. Objective

Không chỉ giảm average/median. Tìm và loại runaway latency mechanisms.

## 10.2. TE-1 — Top-tail forensic cohort

Tạo analysis trên top-N slowest accepted/repaired runs theo workflow, bắt đầu với:

- Diagnose;
- Bugfix;
- Feature.

Recommended first pass:

```text
top 10 Diagnose TTAR
top 10 Bugfix repaired TTAR
top 10 Feature repaired TTAR
```

Không cần model. Dùng ledger timeline.

### Timeline decomposition

```text
assignment/start
preflight
first mutation
verification
replan #1..n
wait / managed command
runtime recovery
source drift
acceptance correction
final acceptance
```

Phân biệt:

- compute time;
- tool time;
- wait time;
- operator wait;
- retry/replan time;
- recovery/stall time.

## 10.3. TE-2 — Tail-specific failure mechanisms

Nếu top tail tập trung vào 1–2 mechanism, ưu tiên deterministic fix trước bất kỳ optimizer tổng quát nào.

Ví dụ plausible nhưng **không được giả định trước khi forensic**:

- stalled command/process;
- proof timeout;
- repeated broad suite;
- source drift loop;
- acceptance correction loop;
- recovery/resume;
- waiting for operator report/ACK;
- duplicate/foreign task projection.

## 10.4. Success metric

Theo dõi:

```text
TTAR p90
TTAR p95 when stable
workflow-specific p90
share of accepted tasks > fixed high-latency threshold
```

Không tối ưu tail bằng cách bỏ quality/proof.

---

# 11. P4: POLICY MỚI — PASSIVE COLLECTION, KHÔNG MODEL-TUNING

## 11.1. Tại sao dừng P4 engineering

Current known causal positives = 2.

Source churn:

```text
23 base HEADs
90 worktree fingerprints
```

Predictor variance:

```text
oracle_strength 71/71 strong
root_cause_confidence 71/71 high
```

Validation:

- no familywise bucket separation;
- task-family holdout incomplete;
- source-state holdout unevaluable;
- temporal holdout unevaluable;
- rolling temporal windows mostly unevaluable.

Thêm model bây giờ sẽ tăng degrees of freedom nhanh hơn information.

## 11.2. Reopen threshold

Không dùng sample count tổng đơn thuần.

Mốc review lại P4 modeling:

```text
minimum causal positives to reconsider model structure: ~20
preferred serious modeling range: 30–50+ positives
```

Kèm điều kiện:

- positives không tập trung vào một source state duy nhất;
- có variation trong feature/bugfix;
- predictor có nontrivial variance;
- temporal/source-state holdout trở nên evaluable.

Đây là **review threshold**, không phải guarantee pass.

## 11.3. Không đổi v5 giữa collection để “làm xanh”

Cấm:

- hạ Wilson threshold;
- relabel generic replan thành positive;
- synthesize/oversample production evidence;
- chọn workload để tạo separation;
- đổi outcome sau khi thấy dữ liệu;
- bỏ holdout khó.

---

# 12. DECISION THRESHOLDS — CƠ CHẾ CHỐNG “ĐẼO CÀY GIỮA ĐƯỜNG”

Một chiến lược chỉ được đổi khi trigger định trước xảy ra.

| Quyết định | Trigger mở lại/chuyển bước |
|---|---|
| Mở lại P4 modeling | ~20+ causal positives + có variation đủ để reevaluate |
| Dừng A0 | ≥1 complete block/stratum nếu volume tới + 100% critical integrity |
| Mở P5-A | A0 integrity accepted / exact feasibility exception documented |
| Dừng treatment canary | target/horizon reached + safety/integrity/overhead review complete |
| Mở P5-B | canary feasible + treatment bundle stable + confirmatory contract frozen |
| Universal promotion P5-U | efficacy + quality + economics + separate operator/release acceptance |
| Targeted P5-C | P5-B efficacy + P4-C predictive validity + treatment-benefit heterogeneity/policy value |
| Thêm architecture | observed repeated need không giải bằng existing primitive |
| Mở P7/P8 | P5/rework economics đã đủ; inputs validated |
| Capacity scaling P9 | telemetry chứng minh capacity bottleneck thực |

## 12.1. No threshold shopping

Sau khi một epoch bắt đầu, không thay threshold vì kết quả không đẹp.

Nếu semantic contract phải đổi:

```text
close epoch
record reason
new manifest/version
new epoch
```

---

# 13. PRIORITIZATION BẰNG EXPECTED VALUE, KHÔNG BẰNG SỐ LƯỢNG ISSUE

## 13.1. Leverage model

Một intervention đáng ưu tiên khi:

```text
Expected Value ≈
  event frequency
× avoidable cost per event
× probability intervention affects mechanism
× confidence in mechanism
- implementation/maintenance/risk cost
```

Không cần giả precision số học; framework dùng để xếp hạng.

## 13.2. Current ranking

### Rank 1 — Source/base drift

- frequency lớn;
- causal mechanism rõ;
- deterministic intervention;
- tail/reproof cost cao;
- không cần experimental platform.

### Rank 2 — Acceptance correction

- frequency lớn;
- phát hiện muộn nên cost/event cao;
- có thể shift-left;
- EOCL/proof primitives đã có.

### Rank 3 — P5 real experiment throughput

- rework economic problem rất lớn;
- treatment effect unknown;
- architecture gần đủ;
- giá trị thông tin của real randomized observations rất cao.

### Rank 4 — Generic CHECK/BUILD prospective taxonomy

- vùng mù lớn;
- instrumentation v3 đã có;
- cần natural failures để giảm uncertainty.

### Rank 5 — Tail forensic

- potential payoff rất cao nếu vài mechanisms tạo phần lớn p90/p95;
- low architecture cost.

### Lower priority — thêm P4 model, routing optimizer, skill platform, new agent topology

Marginal information/value hiện thấp hơn.

---

# 14. ROADMAP THỰC THI — KHÔNG BIẾN THÀNH MỘT PHASE ONTOLOGY MỚI

Đây là sequence ưu tiên, không phải runtime state machine mới.

## STEP 0 — Restore a valid experimental baseline

1. xác định và loại nguyên nhân tạo nested `resources/coding-tools-mcp/.coding-tools`;
2. không commit secondary ledger như source;
3. verify canonical root-only runtime evidence behavior;
4. fresh P4/P5 readiness;
5. freeze exact current HEAD/runtime/tool/evaluation identities.

Exit:

```text
source_worktree_clean = true under canonical scope
HEAD == origin/main
no active writer/run conflict
```

## STEP 1 — DRE-R1 + R2 focused hardening

Không broad refactor.

Chỉ implement khi source audit chỉ ra missing invariant cụ thể cho:

- early drift detection;
- proof/source binding;
- acceptance shift-left;
- no-op/wrong-scope early discrimination.

Nếu current source đã có invariant, không viết lại; chuyển sang measurement.

## STEP 2 — P5 AUTO-ASSESS funnel visibility

Trước khi mở epoch, bảo đảm natural Feature/Bugfix tasks có thể được assessed arm-neutral và reason-coded mà không auto-enroll.

Không thêm public tool.

## STEP 3 — New exact P5-A0 epoch

- new manifest trên exact current code-bearing revision;
- external secret handle;
- explicit operator open;
- natural tasks only;
- target one full block each feature/bugfix;
- close khi integrity criterion/horizon đạt.

## STEP 4 — P5-A treatment canary

Nếu A0 healthy:

- separate manifest;
- ~32 natural tasks target;
- monitor quality, overhead, integrity;
- no efficacy claim.

## STEP 5 — Tail forensic in parallel

Read-only ledger analysis, không làm chậm P5 cohort.

## STEP 6 — P5-B design and confirmatory run

Chỉ sau canary.

## STEP 7 — Re-evaluate strategy

Chỉ khi data mới có thể thay decision:

- treatment harmful/neutral/beneficial;
- DRE rates không giảm;
- causal positives P4 đạt threshold;
- tail mechanism mới xuất hiện.

Không re-plan toàn project theo từng delta nhỏ.

---

# 15. EXPERIMENTAL INTEGRITY VÀ BIAS CONTROL

## 15.1. Selection bias

Eligibility phải arm-neutral và ghi trước assignment.

Auto-assess giúp quan sát:

```text
assessed
eligible
ineligible reason
eligible not enrolled
assigned
```

Nếu chỉ ghi assigned tasks, ta không biết selection process.

## 15.2. Survivor bias

P5-B denominator là all assigned, không accepted-only.

Failed/blocked/aborted/timeout/replan vẫn ở ITT.

## 15.3. Performance bias

Common execution contract phải giống hai arms ngoài treatment bundle.

Không cho treatment thêm compute/review rồi gọi outcome là effect của causal-fix discipline.

## 15.4. Source drift confounding

Epoch freezes control-plane/treatment/runtime identities. Natural target source của từng task được recorded, nhưng code-bearing experiment machinery drift thì đóng enrollment.

## 15.5. Missingness

```text
missing quality != pass
missing cost != zero
missing outcome != success
unknown != nonrepair
```

## 15.6. Optional stopping

Confirmatory efficacy chỉ xem theo registered looks. Canary/A0 không được biến thành informal p-hacking.

---

# 16. TẠI SAO KHÔNG CẦN “PHƯƠNG ÁN TỐI ƯU TOÀN CỤC” NGAY BÂY GIỜ

Một joint optimizer P8 đòi inputs đáng tin:

- treatment effect;
- repair risk;
- quality impact;
- placement economics;
- routing economics;
- cost coverage.

Hiện treatment effect = unknown.

Nếu build optimizer bây giờ, nó sẽ tối ưu proxy/noise.

Phương án khoa học tốt không phải luôn là giải phương trình lớn nhất. Nó là **giải đúng biến có information value cao nhất tiếp theo**.

Current highest-value unknown là:

> **Can Lean Causal Fix discipline reduce first-pass failure/restricted TTAR on natural feature/bugfix work without quality harm?**

P5 prospective experiment trả lời trực tiếp hơn mọi optimizer hay retrospective predictor hiện tại.

---

# 17. ANTI-OVERENGINEERING FREEZE LIST

Trong giai đoạn này mặc định **không làm**:

- P4 predictor v6 chỉ để tìm signal;
- Bayesian/Firth/GAM/HTE/GRF/EconML production integration;
- synthetic repair production evidence;
- historical CHECK/BUILD causal backfill bằng inference;
- experimentation service riêng;
- experiment database thứ hai;
- public tool thứ 9;
- routing optimizer P7/P8;
- automatic non-deterministic routing;
- global server-first promotion;
- permanent anti-overengineering skill thứ hai;
- memory/state authority mới;
- broad LSP expansion;
- model-worker fleet scaling;
- generic replay platform;
- refactor chỉ để giảm LOC nếu không có maintenance defect.

Mỗi item chỉ được mở khi có explicit evidence trigger.

---

# 18. FALSIFICATION — KHI NÀO DOCTRINE NÀY BỊ BÁC BỎ?

Một doctrine tốt phải nêu điều kiện nó sai.

## 18.1. DRE thesis bị yếu đi nếu

Prospective detail cho thấy source drift/acceptance correction gần như biến mất nhưng total rework vẫn giữ ~40% và solution-quality failure chiếm đa số.

Khi đó tăng weight P5/model-quality work.

## 18.2. P5 priority bị yếu đi nếu

A0 cho thấy natural eligibility throughput cực thấp hoặc treatment canary cho thấy overhead/safety cost vượt plausible benefit.

Khi đó close/replan; không ép experiment.

## 18.3. Tail strategy bị yếu đi nếu

Forensic chứng minh p90 anomaly chủ yếu là legitimate unavoidable long compute chứ không phải avoidable rework/wait/recovery.

Khi đó không tối ưu bằng control-plane changes.

## 18.4. P4 passive policy bị bác bỏ nếu

Natural collection nhanh chóng tạo đủ causal positives + predictor variation + evaluable holdouts.

Khi đó mở lại P4 modeling theo threshold định trước.

---

# 19. DASHBOARD / OPERATOR REPORT NÊN HIỂN THỊ GÌ

Một management report tốt không nên chỉ có aggregate repair rate.

## 19.1. Current-period outcomes

```text
accepted count
first-pass rate
repair rate
TTAR p50/p90
workflow-specific p90
```

## 19.2. Rework mechanism

```text
source/base drift rate
acceptance correction rate
patch-context rate
runtime/tool rate
CHECK/BUILD detailed coverage
unknown rate
```

## 19.3. P5 funnel

```text
assessed
eligible
ineligible by reason
eligible not enrolled
enrolled
assigned
protocol started
first write
terminal
outcome finalized
```

Zero phải có nghĩa rõ; không trộn “không assess” với “assessed but ineligible”.

## 19.4. Tail board

```text
Top slow accepted runs
Top slow repaired runs
TTAR contribution by failure mechanism
workflow p90/p95
```

---

# 20. DEFINITION OF DONE CHO GIAI ĐOẠN NÀY

Không dùng “tất cả code đã viết” làm DONE.

Giai đoạn rework decision program được coi là hoàn tất vòng đầu khi:

1. nested/noncanonical runtime evidence leakage được loại và ngăn tái tạo;
2. prospective DRE metrics hoạt động;
3. source/base drift + acceptance correction có prospective trend đo được;
4. generic CHECK/BUILD failures mới có structured detail coverage cao;
5. P5-A0 có natural assignments và integrity closeout, hoặc honest insufficient-volume outcome;
6. P5-A treatment canary đóng với safety/feasibility report;
7. top-tail forensic xác định được mechanism hoặc kết luận evidence-based rằng tail là largely unavoidable;
8. quyết định P5-B GO/NO-GO có dữ liệu;
9. không thêm authority/public tool/framework ngoài trigger.

Sau đó mới quyết định phase tiếp theo từ evidence.

---

# 21. OPERATOR DECISION CARD — QUY TẮC DÙNG HÀNG NGÀY

```text
1. Task mới thất bại/replan?
   -> classify mechanism first.

2. Deterministic control-plane cause?
   -> fix deterministic invariant; do not blame model.

3. Solution-quality uncertainty?
   -> retain as P5-relevant evidence.

4. P4 signal chưa pass?
   -> continue passive collection; do not tune to green.

5. P5 no samples?
   -> inspect funnel throughput; do not add architecture.

6. Tail TTAR tăng?
   -> forensic top-tail timeline before broad optimization.

7. New framework proposed?
   -> require repeated observed need + causal path to accepted result.

8. New metric changes slightly?
   -> do not change strategy unless a predeclared threshold is crossed.

9. Missing evidence?
   -> UNKNOWN, never zero/pass.

10. DONE/proof achieved?
    -> STOP. Do not polish by inertia.
```

---

# 22. DECISION LOG — 2026-08-22

## D-2026-08-22-RDS-01 — North Star TTAR under quality floors

**Decision:** TTAR distribution + first-pass/quality become primary accepted-result economics.

**Reason:** repaired p50 4.56x và p90 6.63x first-pass; tail worsening is material.

**Status:** normative.

## D-2026-08-22-RDS-02 — Decompose process rework from solution-quality repair

**Decision:** do not attribute ~41% process rework to model-solution failure.

**Reason:** mapped failures and P4 causal label show large control-plane component.

**Status:** normative.

## D-2026-08-22-RDS-03 — P4 passive collection

**Decision:** no additional P4 model/framework on current critical path.

**Reopen trigger:** ~20+ causal positives with useful variation, preferably 30–50+ for serious modeling.

**Status:** active policy.

## D-2026-08-22-RDS-04 — P5 experiment learning independent of P4 predictor readiness

**Decision:** P4-C remains required for targeted P5-C, not for P5-A0/A/B causal learning.

**Status:** locked.

## D-2026-08-22-RDS-05 — Auto-assess, explicit enroll

**Decision:** natural feature/bugfix tasks should be assessable automatically for funnel visibility while enrollment/assignment/treatment remain explicit and gated.

**Status:** implementation direction, subject to smallest coherent delta.

## D-2026-08-22-RDS-06 — DRE priorities

**Decision:** source/base drift and acceptance correction are first deterministic targets; generic taxonomy detail is prospective.

**Status:** active priority.

## D-2026-08-22-RDS-07 — Tail economics workstream

**Decision:** forensic p90/p95 outliers separately, especially Diagnose and Bugfix.

**Status:** active analytical priority.

## D-2026-08-22-RDS-08 — Architecture freeze

**Decision:** no new P5/P4/orchestration platform layer without observed failure that existing primitives cannot solve.

**Status:** anti-overengineering invariant.

---

# 23. FINAL EXECUTION THESIS

Coding Web hiện không thiếu framework để tiếp tục tiến.

Nó đã có:

- one-writer/EOCL authority;
- exact source/proof history;
- runtime/recovery controls;
- shadow measurement;
- P5 manifest/assignment/ITT/analyzer/lifecycle primitives;
- eight-tool compact contract;
- prospective failure taxonomy;
- accepted-result historical corpus đủ lớn để xác định economic priorities.

Điểm cần thay đổi là **cách dùng dữ liệu**.

Không hỏi tiếp:

> “Còn framework nào có thể xây?”

Mà hỏi:

> “Observed accepted-result loss đang đến từ mechanism nào, mechanism đó deterministic hay causal-treatment, và intervention nhỏ nhất có thể làm giảm TTAR là gì?”

Dữ liệu hiện tại trả lời đủ rõ:

```text
1. Rework là material economic defect.
2. Phần lớn rework không thể quy đơn giản cho model-solution quality.
3. Source/base drift và acceptance correction có đủ evidence để hành động deterministic ngay.
4. P4 predictor hiện information-limited, không architecture-limited.
5. P5 hiện data-throughput-limited, không framework-limited.
6. Tail latency đang xấu hơn median và cần forensic riêng.
7. Feature và Bugfix phải stratify vì failure economics khác nhau.
8. Diagnose có extreme tail và không nên contaminate P5 initial population.
9. Unknown taxonomy phải giảm prospectively, không bằng historical guesswork.
10. Mọi strategy change phải đi qua predeclared decision threshold.
```

Do đó phương án tối ưu cho giai đoạn hiện tại là:

```text
CLEAN BASELINE
   ↓
DETERMINISTIC REWORK ELIMINATION
   ├── source/base drift
   ├── acceptance shift-left
   └── prospective CHECK/BUILD detail
   ↓
REAL P5 A/A FUNNEL
   ↓
P5 TREATMENT CANARY
   ↓
CONFIRMATORY CAUSAL LEARNING

PARALLEL:
TAIL FORENSICS + PASSIVE P4 COLLECTION
```

Và nguyên tắc chống “đẽo cày giữa đường” là:

> **New data updates confidence/effect size by default; it does not rewrite architecture or strategy unless a predeclared decision threshold is crossed.**

Đây là phương pháp chuyển Coding Web từ trạng thái “nhiều dữ liệu, nhiều framework, nhiều câu hỏi” sang trạng thái **decision-science engineering**: tập trung vào vài mechanisms có expected value lớn nhất, hành động deterministic khi causal mechanism đã rõ, dùng randomized experiment khi treatment effect chưa biết, và dừng đúng lúc khi evidence không còn justify complexity mới.

---

# 24. SOURCE / EVIDENCE INDEX

Internal evidence used to formulate this doctrine:

1. `docs/research/260821_CODING_WEB_MASTER_ENGINEERING_STRATEGY_AND_HISTORY.md`
2. `docs/research/260821_CODING_WEB_LEAN_CONTROL_RICH_EVIDENCE_ACCEPTED_RESULT_SYNTHESIS.md`
3. `docs/research/260822_P4_P5_GATE_DECOMPOSITION_AND_PROSPECTIVE_REWORK_EXPERIMENT_IMPLEMENTATION_PLAN.md`
4. `docs/CURRENT_STATE.md`
5. `docs/ROADMAP.md`
6. canonical `.coding-tools/orchestration/ledger.sqlite3`
7. `report_p2_rework_diagnosis.py` current output at HEAD `12e0de8...`
8. `report_p4_readiness.py` current output at HEAD `12e0de8...`
9. `report_p5_baseline.py` current output at HEAD `12e0de8...`

Interpretation rule:

```text
Historical observational evidence
    -> choose mechanisms and priorities

Prospective deterministic telemetry
    -> verify deterministic fixes

Randomized P5 evidence
    -> estimate treatment effect

P4 predictive evidence
    -> only later decide targeting/personalization
```

Không đảo ngược bốn tầng bằng chứng này.

---

# 25. IMPLEMENTATION AMENDMENT — 2026-08-22/23 — ACCEPTED-RESULT ECONOMICS GATE

Phần này là amendment vận hành mới hơn cho doctrine, không viết lại các snapshot lịch sử ở các mục trước. Các con số và kết luận lịch sử vẫn được giữ để forensic; khi có xung đột về quyết định hiện tại, amendment này cùng current source / `docs/CURRENT_STATE.md` / `docs/ROADMAP.md` có độ ưu tiên cao hơn các diễn giải snapshot cũ trong chính tài liệu này.

## 25.1. North Star được mở rộng từ TTAR sang economic loss

North Star vận hành hiện tại là:

> **Minimize Accepted-Result Economic Loss under fixed quality, security, authority and correctness floors.**

TTAR vẫn là biến primary nhưng không còn được hiểu là toàn bộ economics. Thứ tự quyết định chuẩn:

```text
quality floor
  -> first-pass outcome
  -> restricted TTAR p90
  -> accepted-result resource cost
  -> human/operator burden
  -> simplicity
```

Resource/cost vector hiện bao gồm tối thiểu local execution, estimated inter-tool wait, tool calls, errors, request/response/model-visible bytes, proof economics và monetary/token coverage khi thực sự quan sát được. Missing measurement = `UNKNOWN`, không phải `0`.

## 25.2. Reporter read-only đã được triển khai

Source hiện có:

```text
npm run report:accepted-result-economics
```

Reporter đọc canonical ledger + `.coding-tools/performance.json`, không activate routing, không mở P5 epoch, không thay đổi production behavior. Nó tách first-pass/repaired resource distributions, top-tail forensic theo Feature/Bugfix/Diagnose, proof-cache opportunity, coverage của monetary/token measurements và current-source DRE window.

`performance.run_metrics` có bounded retention. Vì vậy nếu chỉ một phần accepted cohort có per-run resource telemetry thì phải báo coverage và giữ diễn giải descriptive; không ngoại suy ngầm ra toàn cohort.

`estimated_wait_ms` là khoảng cách bị cap giữa các MCP tool call liên tiếp. Nó có thể chứa controller/model/network/operator time. Do đó:

```text
estimated_wait != proven avoidable waste
estimated_wait != provider billing
```

Monetary CAR chỉ available khi accepted-result cost coverage đầy đủ. Partial token/resource evidence không được đổi tên thành CAR.

## 25.3. Điều chỉnh DRE: historical mechanism != current causal incidence

Các snapshot trước ghi nhận `source_base_drift=66` và `acceptance_correction=56` historical events. Chúng vẫn hữu ích để biết mechanism từng tồn tại, nhưng **không đủ để tự động justify thêm hardening trên source hiện tại**.

Quy tắc mới:

```text
historical count
  -> mechanism hypothesis / forensic context

natural accepted tasks on exact clean current source
  -> current incidence

current incidence + material economic impact
  -> permission to open a smallest-causal DRE fix wave
```

Nếu exact current-source window chưa có volume thì kết luận đúng là `INSUFFICIENT_CURRENT_SOURCE_VOLUME`, không phải dùng cumulative history thay thế. STEP 0 snapshot cũ trong tài liệu này là historical baseline; sau source mutation phải re-prove trên code-bearing revision sạch mới.

## 25.4. Tail interpretation được siết lại

Các historical snapshot cho thấy repair tail lớn và Diagnose có anomaly rất nặng. Điều được phép nói ở hiện tại là:

> **Tail remains a large cost center; Diagnose anomaly persists in the observed historical/current descriptive corpus.**

Không dùng câu `tail continues worsening` nếu chưa có comparable current trend estimate trên cùng definition/window. Tail forensic vẫn ưu tiên vì expected value cao, nhưng intervention chỉ được mở sau khi timeline decomposition chỉ ra mechanism có thể tác động.

## 25.5. Proof-cache: đo trước, không xây cache v2 theo phản xạ

Reporter đưa proof-cache opportunity/hit economics vào cùng accepted-result resource evidence. Một hit rate thấp tự nó chỉ chứng minh reuse thấp; nó **không** chứng minh cache architecture mới sẽ giảm accepted-result loss. Chỉ mở cache workstream nếu prospective data cho thấy repeated proof là bottleneck vật chất, có reuse opportunity thực và expected saving vượt implementation/maintenance risk.

## 25.6. P5 economics gate

P5 implementation contract bổ sung các gate:

```text
accepted_result_resource_economics_required = true
resource_overhead_noninferiority_required = true
monetary_cost_noninferiority_when_complete = true
missing_cost_is_zero = false
```

P5-A0 vẫn là natural shadow A/A và **không bật treatment**. A0 đo assignment/funnel/integrity và stability của measurement trên exact revision. Chỉ sau A0 healthy mới xem xét P5-A treatment canary với contract preregistered gồm quality floor, repair/replan no-harm, restricted TTAR, resource-overhead noninferiority và monetary-cost noninferiority khi coverage đầy đủ.

P4 tiếp tục passive/shadow-only. P7/P8 chỉ được mở sau khi P5 có effect evidence phù hợp **và** cost/resource coverage đủ để optimizer không tối ưu proxy/noise. Automatic non-deterministic routing, auto-handoff, global server-first, P5 automatic start và automatic production promotion tiếp tục `OFF`.

## 25.7. No-new-architecture freeze

Chuỗi thực thi hiện tại được khóa thành:

```text
MEASURE CURRENT LOSS
  -> FIX ONLY ACTIVE DETERMINISTIC LOSS
  -> RUN REAL P5 A0 / CANARY UNDER EXPLICIT GATES
  -> MEASURE COST + TTAR + QUALITY
  -> THEN CONSIDER ROUTING OPTIMIZATION
```

Không build cache v2, P4 model mới, LSP expansion, routing optimizer, experiment service hay public tool mới nếu chưa có repeated observed need và causal path rõ tới accepted-result economics.

## 25.8. Closure evidence policy

Implementation wave của reporter/P5 economics gate chỉ được gọi CLOSED khi cùng exact source đã qua focused proof, affected/full component proof phù hợp, reporter smoke, diff/review, EOCL final acceptance và Git delivery. Sau commit phải chạy lại clean-source reporters để phân biệt **implementation closure** với **future natural-data evidence gates**. Thiếu natural current-source tasks hoặc monetary coverage sau đó là evidence gate, không phải lý do tiếp tục viết architecture.

---

**END OF DECISION DOCTRINE — CW-RDS-20260822-v1 + 2026-08-22/23 IMPLEMENTATION AMENDMENT**
