# CODING WEB — ĐỐI CHIẾU BẰNG CHỨNG, CAN THIỆP NHÂN QUẢ, PROBLEM RESOLUTION LINEAGE VÀ LỘ TRÌNH THỰC THI TỐI ƯU

> **Decision / Research Synthesis ID:** `CW-ERCIP-20260823-v2`
> **Ngày:** 2026-08-23, `Asia/Saigon`
> **Workspace chính:** `E:\DEV\Codex-web`
> **Representative external workload:** `E:\DEV\HR STA\HR` — chỉ dùng như population/ledger riêng, không pooled assignment
> **Vị trí repository hiện tại:** `E:\DEV\Codex-web\docs\research\260823_CODING_WEB_EVIDENCE_RECONCILIATION_CAUSAL_INTERVENTION_AND_OPTIMAL_EXECUTION_PLAN.md`
> **Companion scientific doctrine:** `docs/research/260823_CODING_WEB_PROBLEM_RESOLUTION_LINEAGE_AND_INTERACTIVE_ENGINEERING_SCIENCE.md`
> **Trạng thái:** `REPOSITORY_SYNTHESIS_FOR_REVIEW — SNAPSHOT-BOUND / NO IMPLEMENTATION AUTHORITY`
> **Phạm vi:** evidence reconciliation, lifecycle truth, causal execution intelligence, Problem Resolution Lineage (PRL), accepted-result/problem-resolution economics, P4/P5, routing economics, reliability/release hardening
> **Không tự động kích hoạt:** source mutation, P5 enrollment/treatment, routing policy, runtime restart, package/release, commit/push

---

# 0. KẾT LUẬN ĐIỀU HÀNH

Tài liệu này hợp nhất hai hướng nghiên cứu tưởng như khác nhau nhưng thực chất là **hai tầng của cùng một bài toán**:

1. **Evidence Reconciliation / Causal Execution Intelligence** trả lời:
   - execution nào thực sự xảy ra;
   - source/runtime/proof nào là canonical;
   - lifecycle có sạch không;
   - accepted-result loss nằm ở mechanism nào;
   - intervention nào đủ bằng chứng để thử nghiệm.

2. **Problem Resolution Lineage (PRL)** trả lời:
   - nhiều user/assistant turn và nhiều EOCL RUN/WAVE có thuộc cùng một vấn đề của người dùng không;
   - feedback là requirement mới, clarification hợp lệ hay avoidable correction;
   - một engineering RUN đã `ACCEPTED` có thực sự giải quyết vấn đề người dùng chưa;
   - khi nào problem được `RESOLVED`, `REOPENED`, `SUPERSEDED` hay vẫn `UNCONFIRMED`.

Luận điểm hợp nhất là:

> **`ACCEPTED ENGINEERING RUN != ACCEPTED PROBLEM RESOLUTION`.**

Một RUN có thể có proof đúng, source đúng và được EOCL accept, nhưng người dùng vẫn phản hồi “vẫn lỗi”, “không phải trường hợp tôi nói”, “sửa sai workspace”, hoặc “app thật vẫn chưa hoạt động”. Khi đó engineering evidence của attempt có thể hợp lệ trong phạm vi oracle của nó, nhưng **problem-level outcome vẫn chưa resolved**.

Do đó Coding Web không nên bỏ Accepted-Result Economics. Ngược lại, phải đặt nó vào đúng vị trí:

```text
Accepted-Result Economics
    = economics của một execution attempt / engineering result

Accepted Problem Resolution Economics
    = economics end-to-end của một vấn đề người dùng
      có thể chứa nhiều attempts / accepted results / corrections / reopen
```

## 0.1. North Star đã được nâng một tầng

North Star chiến lược từ đây là:

> **Minimize Accepted Problem Resolution Loss under fixed quality, security, authority and correctness floors.**

Nhưng **không đổi thành một scalar giả**. Decision order vẫn lexicographic:

```text
0. security / data / authority / correctness hard floors
1. trusted engineering correctness + proof khi task có execution/mutation
2. user problem resolution state
3. avoidable correction / reopen burden
4. Time to Problem Resolution (TTPR) tail
5. execution first-pass / TTAR / repair burden
6. resource vector
7. monetary + human/operator burden khi thật sự measured
8. simplicity / maintainability
```

Một route rẻ hơn nhưng làm tăng critical defect bị loại ở tầng 0. Một RUN nhanh hơn nhưng người dùng phải sửa hướng thêm hai lần cũng không được gọi là cải tiến end-to-end.

## 0.2. Kiến trúc lõi tiếp tục freeze tương đối

Không xây thêm một orchestration platform, agent manager, second ledger, transcript database, generic memory platform, routing framework, P4/P5 service, public MCP tool thứ chín, proof-cache v2 hay telemetry subsystem chỉ vì muốn hệ thống “đầy đủ hơn”.

Hướng chính thức:

```text
Observe
  → Attribute
  → Intervene
  → Measure
  → Retain / Revert
```

với ba vòng lặp tách biệt nhưng liên kết:

```text
LOOP 1 — USER PROBLEM / CONVERSATION
problem → interpretation → response → feedback → revision → resolution/reopen

LOOP 2 — ENGINEERING / EOCL
objective → preflight → execute → proof → replan → accept/reject

LOOP 3 — LEARNING / ECONOMICS
problem outcome → causal loss → intervention → prospective comparison → retain/revert
```

EOCL vẫn là execution/proof/acceptance authority. PRL chỉ là **semantic correlation + evaluation layer** nằm phía trên, không có quyền tự accept source hay bypass proof.

## 0.3. Causal order mới được khóa

```text
GATE 0 — LIFECYCLE + EVIDENCE TRUTH
        ↓
A1 — FAILURE DETAIL COVERAGE      PRL-A — PROBLEM IDENTITY / EXACT LINKAGE
        \                         /
         \                       /
          └───── measurement foundations ─────┘
                         ↓
A2 — STAGE ATTRIBUTION + PRL-B/C — FEEDBACK / RESOLUTION / REOPEN
                         ↓
UNIFIED EXECUTION + PROBLEM-RESOLUTION LOSS MODEL
                         ↓
A3 — TARGETED CAUSAL INTERVENTION
                         ↓
PRL-D — PROBLEM ECONOMICS REPORTER
                         ↓
P5 — FUTURE PROBLEM-LEVEL EXPERIMENT ENDPOINTS AFTER VALIDATION
                         ↓
ROUTING ECONOMICS / ADAPTIVE POLICY — ONLY AFTER LOCAL EVIDENCE
```

Track B — Reliability/Release Hardening — vẫn độc lập nhưng dùng chung Gate 0.

## 0.4. Repository-state reconciliation của chính tài liệu này

Bản v1 ban đầu được tạo ngoài repository vì snapshot `CW-S1` ghi P5-A0 `EPOCH_ACTIVE` với funnel bằng zero. Sau đó bản report và tài liệu PRL đã xuất hiện trong `docs/research`, tức repository có docs/source-scoped drift sau thời điểm epoch mở.

### Post-snapshot delivery note — current only at its own receipt

Tại thời điểm note này, file là **repository-local untracked draft**, không phải artefact đã được stage, commit, push hay release. Receipt vận hành mới hơn nằm trong execution tracker `260823_CODING_WEB_GATE0_PRL_IMPLEMENTATION_AND_VALIDATION_TRACKER.md`, không thay số `CW-S1`/`HR-S1` bên dưới:

- `C0-P5-CONTAINMENT` đã dùng authority P5 chính thức để `hard_stop` A0 có post-open source-scope drift, với funnel lịch sử giữ nguyên `0/0/0/0/0`; không có efficacy outcome;
- `G0-AR1` đã hoàn thành Gate 0 theo immutable snapshot và exact-ID reconciliation; các ordinary row dưới ngưỡng stale vẫn chỉ là `THRESHOLD_SENSITIVE_STALE_CANDIDATE`, không phải bằng chứng health hoặc zombie;
- disk/upstream/source, runtime-loaded identity, package và release truth phải lấy từ tracker/current source/authority receipt mới nhất. Loaded-runtime identity trong wave này vẫn là `UNKNOWN`.

Do đó bản report này là doctrine và historical reconciliation; nó không được dùng làm current lifecycle, runtime, package hoặc release claim.

V1 phải được hiểu chính xác tại snapshot của nó:

- tại `CW-S1` và final recapture lịch sử `2026-08-23T14:01:41Z`, enrollment/assignment/protocol/binding/outcome vẫn `0/0/0/0/0`;
- vì vậy **không có observed A/A/treatment outcome nào được chứng minh là contaminated** trong snapshot đó;
- nhưng post-open docs/source drift có nghĩa **không được mặc định epoch vẫn enrollment-ready**;
- v1 không recapture P5 lifecycle bằng P5 authority, không close/pause/hard-stop/open epoch và không tạo assignment;
- ở receipt sau đó, C0 đã `hard_stop` qua official authority vì manifest yêu cầu source cleanliness và `stop_on_source_identity_violation=true`; không được re-open, rebaseline ngầm hoặc tạo epoch thay thế từ report này;
- trước bất kỳ P5 enrollment hoặc source-writing wave tương lai, phải fresh-recapture exact source/runtime/manifest/P5 identity và xử lý theo official P5 authority với manifest mới và authority riêng.

Các con số `CW-S1`, `HR-S1`, `PKG-S1` dưới đây tiếp tục là **snapshot facts**, không được đọc như live-state guarantee tại thời điểm sau này.

---

# 1. EVIDENCE EPISTEMOLOGY — CÁCH PHÂN BIỆT “BIẾT”, “SUY RA” VÀ “CHƯA BIẾT”

## 1.1. Claim labels

| Label | Nghĩa |
|---|---|
| `VERIFIED_CURRENT @ SNAPSHOT` | Được xác minh từ exact snapshot đã định danh. “Current” chỉ đúng tại snapshot đó. |
| `VERIFIED_SNAPSHOT` | Historical exact evidence; không tự động mô tả live state hôm nay. |
| `EXTERNAL_SOURCE_FACT` | Fact từ paper/spec/vendor/standard; không chứng minh local implementation. |
| `INFERENCE` | Kết luận logic từ evidence; không giả làm direct measurement. |
| `PROPOSED` | Thiết kế/intervention chưa triển khai. |
| `UNKNOWN` | Thiếu identity/measurement/authority/coverage. |
| `REFUTED_CURRENT` | Bị current evidence hoặc source mới hơn bác bỏ/supersede. |

## 1.2. Evidence precedence

Khi nguồn mâu thuẫn:

```text
1. exact current implementation + focused/live proof cho đúng checkout/process
2. canonical ledger / exact authority receipts
3. AGENTS.md + maintained CURRENT_STATE / ROADMAP
4. maintained subsystem docs
5. dated research snapshots
6. attachments/advisory
7. external research cho methodology
```

`.coding-tools/performance.json`, `task-history.json`, `task-state.json` là projections/supporting evidence. Khi projection mâu thuẫn canonical ledger/Git/process identity, canonical source thắng và contradiction phải được ghi nhận chứ không sửa projection để “làm xanh”.

## 1.3. Proof ladder bắt buộc

```text
source present
  → focused proof
  → EOCL semantic acceptance
  → loaded-runtime identity / live contract
  → isolated package/process proof
  → exact installer/provenance
  → installed-session / reboot-logon proof
  → pilot / UAT
  → release / publication
  → production / SLO
```

Không collapse các plane này thành “đã xong”.

---

# 2. PHƯƠNG PHÁP SNAPSHOT VÀ CAUSAL GUARDRAILS

## 2.1. One-snapshot rule

Một decision snapshot phải dùng một immutable evidence plane:

```text
canonical SQLite ledger
  → mode=ro
  → query_only
  → explicit transaction
  → Backup API temporary copy
  → close live source connection
  → sequential projections trên immutable copy
  → delete temporary copy
```

Không ghép các CLI report chạy ở thời điểm khác nhau rồi gọi đó là một coherent snapshot nếu live ledger đã drift giữa các lượt.

## 2.2. Hai workspace không được pooled sai cách

`E:\DEV\Codex-web` và `E:\DEV\HR STA\HR` có source, ledger, runtime, authority và experiment epoch riêng.

- HR có thể là representative external domain;
- nhưng không assignment xuyên hai ledgers;
- không dùng historical HR corpus như current-head treatment cohort;
- cross-workspace synthesis chỉ sau khi từng cohort riêng đã terminal và khóa missingness/source/runtime/oracle.

## 2.3. Statistical rules

1. Accepted-only observational cohort không ước lượng treatment effect.
2. Replan/repaired là process-history label, không tự là solution failure.
3. `preflight_avoided` không phải counterfactual “task được cứu”.
4. `active` không tự là zombie; `stale=0` không chứng minh liveness.
5. Host-visible duration không phải model latency.
6. Inter-tool gap không phải provider/model time hay avoidable waste.
7. Missing money/token/controller usage = `UNKNOWN`, không phải zero.
8. Không backfill root cause lịch sử từ command name hoặc intuition.
9. Cross-clock spans chỉ correlate bằng identity/dependency, không trừ timestamp tùy tiện.
10. Không cộng milliseconds + dollars + defect risk + human burden thành scalar khi chưa có conversion contract.

---

# 3. FRESH SNAPSHOT REGISTER — CÁC FACT DÙNG CHO QUYẾT ĐỊNH NÀY

## 3.1. Coding Web `CW-S1`

Snapshot canonical tại `2026-08-23T13:29:10.252787Z`:

```text
workspace                 E:\DEV\Codex-web
branch                    main
disk HEAD / upstream      8ffa8bf279ad7296ff1402fbc2ce2b59069c36c5
code-bearing HEAD         ea6abcb3ab0f3a4cc9dbf94d34c685a4806760ba
ledger integrity          ok
ledger user_version       9
```

### Accepted-result cohort

```text
accepted candidates       493
explicit-model excluded    20
representative included   473
first-pass                274 / 473 = 57.9281%
repaired                  199 / 473 = 42.0719%
replanned waves           378
```

TTAR descriptive association:

```text
first-pass p50 / p90      66,458 / 454,390 ms
repaired p50 / p90        298,213 / 3,358,854 ms
ratio                     4.487x / 7.392x
```

Đây là strong economic signal rằng repaired accepted paths thường đắt hơn trong corpus này; không phải causal proof rằng mọi replan gây delay.

### Failure causality

```text
failure_observed          385
mapped                    181
unclassified              204
mapping coverage          47.013%
legacy generic detail     CHECK_FAILED=114, BUILD_VERIFICATION_FAILED=56
prospective v3 detail      11 rows
oracle observed            91 / 473 = 19.2389%
```

Kết luận: schema P2 đã có; bottleneck là emitter/detail/oracle coverage, không phải thiếu taxonomy framework.

### P4 / P5 / economics

```text
P4 representative terminal        78
P4 validated_signals              []
P4 state                          COLLECTING
P5 epochs                         6
P5 at CW-S1                       5 closed + 1 A0 active
P5 funnel at CW-S1                0 enrollment / 0 assignment / 0 protocol / 0 binding / 0 outcome
resource telemetry coverage       91 / 473 = 19.2389%
monetary/controller/token         0 / 473 coverage
proof cache                       4 / 1,563 hits = 0.2559%, known saved 9,810 ms
```

Không được nói cost = 0; chỉ được nói cost coverage = 0.

### Host evidence

```text
valid host-visible spans          142
exact bound                        38 / 142 = 26.7606%
p50 / p90                         394,888.6 / 1,854,736.1 ms
```

Đây là user-turn → first assistant-visible span theo host plane, **không phải model latency**.

## 3.2. HR `HR-S1`

```text
workspace                 E:\DEV\HR STA\HR
branch                    V_Finance
disk HEAD / upstream      1a95965e6cfdf90455bcc300d910976e62a4816d
all 50 run first-wave     base HEAD 17e6d04c..., không phải current HEAD
runs total                50
active                    36
accepted                   8
aborted                    6
```

Accepted cohort nhỏ:

```text
first-pass                  5
repaired                    3
first-pass p50/p90          260,408 / 366,896 ms
repaired p50/p90            270,653 / 360,611 ms
```

Chỉ được kết luận: **không quan sát repair penalty lớn trong cohort n=5/n=3 này**. Không generalize thành “repair không tốn thời gian”.

Failure:

```text
failure events              6
mapped                      1 / 6 = 16.6667%
CHECK_FAILED                4
EXECUTION_OWNER_INVALID     1
RUNTIME_RESUME_REQUIRED     1
```

Workspace identity cohort:

```text
workspace identity          PASS 50/50
cross-project contamination NO 50/50
```

Do đó không xây provenance/isolation subsystem mới trên critical path; giữ guard và reopen chỉ khi fresh evidence falsify.

## 3.3. Package snapshot `PKG-S1`

Local `dist/win-unpacked` có artifact, nhưng cũ hơn code-bearing source và không bind exact Git/build provenance. Local `dist` snapshot không thấy NSIS setup candidate ngoài unpacked tree. Do đó:

```text
package bytes exist                 yes
exact-source package provenance     UNKNOWN
exact-source NSIS installer         UNPROVEN
installed-session proof             UNKNOWN
release/publication                 UNKNOWN
production/SLO                      NOT CLAIMED
```

---

# 4. CURRENT PROBLEM MODEL — TẠI SAO RUN-CENTRIC EVALUATION CHƯA ĐỦ

Coding Web đã có các execution units mạnh:

```text
TASK
RUN
WAVE
DELEGATION
PROOF
CHECKPOINT
QUALITY_OUTCOME
OBSERVATION_SPAN
```

Nhưng user thường nghĩ theo một vấn đề:

```text
“Không lưu được dự án.”
“Dashboard không cập nhật.”
“Codex dùng sai workspace.”
“Đồng bộ tài chính/dự án chưa đúng.”
```

Một problem có thể đi qua:

```text
U1 problem
  → A1 diagnosis
  → RUN R1
  → proof pass
  → assistant says done
  → U2 “vẫn lỗi”
  → RUN R2
  → U3 “đúng nhưng còn constraint X”
  → problem revision
  → RUN R3
  → user confirms / no confirm / later reopen
```

Nếu chỉ nhìn RUN:

```text
R1 accepted
R2 accepted
R3 accepted
```

Nhưng problem truth có thể là:

```text
ONE PROBLEM
R1 = accepted engineering attempt, user problem unresolved
R2 = partial resolution
R3 = final resolution
```

Do đó **unit of execution** và **unit of end-to-end evaluation** phải khác nhau:

```text
RUN          = execution unit
PROBLEM      = user-resolution evaluation unit
```

---

# 5. PROBLEM RESOLUTION LINEAGE (PRL) — LỚP SEMANTIC MỎNG PHÍA TRÊN EOCL

Chi tiết nền tảng khoa học, conversational repair, requirements traceability, SWE-Together, SWE-Interact, RECODE-H, HULA và community failure hypotheses được giữ trong companion document:

`docs/research/260823_CODING_WEB_PROBLEM_RESOLUTION_LINEAGE_AND_INTERACTIVE_ENGINEERING_SCIENCE.md`

Tài liệu vận hành này chỉ lấy những contract ảnh hưởng roadmap.

## 5.1. Những primitive đã có

Current source/evidence architecture đã có gần đủ atoms:

```text
turn_id / trace_id
conversation_epoch
objective_revision / objective_source / objective_sha256
run_id / wave_id
replan
proof / checkpoint
quality_outcome
accept/reject
observation spans + clock domain
durable handoff capsule
solution shadow
```

Gap không phải thiếu observability platform hay memory platform. Gap là thiếu một **canonical same-problem semantic spine**.

## 5.2. Không được overload identity hiện có

```text
turn_id             != problem_id
session_id          != problem_id
conversation_epoch  != problem_id
RUN                 != problem_id
quality_outcome     != problem_resolved
```

Một problem có thể span nhiều RUN và nhiều conversation epoch; một conversation cũng có thể chứa nhiều problems.

## 5.3. Minimal Problem Resolution Thread

PRL v1 chỉ cần content-free structure:

```text
problem_id
problem_revision
problem_state
turn_id / trace_id
turn_relation
feedback_intent
feedback_cause
feedback_economic_class
classification_provenance
run_id / wave_id
proof / quality refs
resolution / reopen event
```

Không lưu raw user prompt, assistant response, chain-of-thought, source content, command output hay secrets.

Không tạo second DB nếu canonical ledger có thể chứa bounded problem records/events. Không thêm public tool thứ chín; ưu tiên existing internal host correlation / `task_control` surface.

## 5.4. Same-problem linking phải fail-closed

Relation tối thiểu:

```text
SAME_PROBLEM
NEW_REVISION_OF_SAME_PROBLEM
NEW_SUBPROBLEM
NEW_PROBLEM
CONFIRM_OR_REOPEN_EXISTING
AMBIGUOUS
```

Không link bằng timestamp proximity. Không hash raw prompt làm semantic identity. Nếu ambiguous, không merge histories để dùng làm policy evidence.

---

# 6. USER FEEDBACK KHÔNG ĐỒNG NGHĨA AI FAILURE

Đây là nguyên tắc bắt buộc để PRL không tạo metric sai.

## 6.1. Feedback intent

Vocab có thể rộng ở research layer, nhưng operational core cần phân biệt tối thiểu:

```text
CONFIRM_RESOLVED
SAME_PROBLEM_STILL_FAILING
CORRECT_UNDERSTANDING_OR_SCOPE
CORRECT_TECHNICAL_RESULT
CORRECT_PROOF_OR_VERIFICATION
ADD_REQUIREMENT_OR_CONSTRAINT
PROVIDE_NEW_EVIDENCE
PREFERENCE_CHANGE
NEW_PROBLEM
SUPERSEDE_OR_CANCEL
UNKNOWN
```

## 6.2. Cause

```text
ASSISTANT_MISUNDERSTANDING
WRONG_ROOT_CAUSE
WRONG_TARGET_OR_WORKSPACE
INSUFFICIENT_SOLUTION_SCOPE
IMPLEMENTATION_DEFECT
PROOF_ORACLE_GAP
RUNTIME_OR_ENVIRONMENT_FAILURE
SOURCE_OR_STATE_DRIFT
STALE_CONTEXT_OR_REPLAY
USER_NEW_INFORMATION
REQUIREMENT_EVOLUTION
USER_PREFERENCE_CHANGE
EXTERNAL_DEPENDENCY_CHANGE
UNKNOWN
```

## 6.3. Economic interpretation

```text
AVOIDABLE_CORRECTION
PRODUCTIVE_CLARIFICATION
LEGITIMATE_REQUIREMENT_GROWTH
NEUTRAL_FOLLOWUP
UNCERTAIN
```

Mục tiêu không phải “giảm số user reply”. Mục tiêu là:

> **minimize avoidable correction burden while preserving problem-resolution and engineering quality floors.**

Ví dụ user bổ sung một constraint chưa từng cung cấp là requirement growth, không phải assistant failure. Nhưng user nhắc lại workspace đã explicit từ đầu sau khi agent sửa nhầm target là avoidable correction.

## 6.4. Feedback label authority

Precedence:

```text
1. explicit user semantic feedback
2. deterministic source/proof/runtime evidence
3. EOCL structured events
4. exact turn/run/problem linkage
5. bounded human annotation khi cần
6. model-derived classifier chỉ shadow/advisory
```

Unknown phải giữ unknown. Không dùng same model vừa trả lời vừa tự cấp authority rằng correction “không phải lỗi của mình”.

---

# 7. PROBLEM RESOLUTION STATE — KHÔNG DÙNG “ASSISTANT NÓI XONG” LÀM CLOSURE

State model tối thiểu nên biểu diễn semantic facts, không biến thành orchestration state machine thứ hai:

```text
OPEN / IN_PROGRESS
  → PROVISIONALLY_RESOLVED
  → RESOLVED_CONFIRMED
  → RESOLVED_UNCONFIRMED
  → REOPENED
  → SUPERSEDED / BLOCKED / ABANDONED
```

Rules:

1. Assistant completion report không tự tạo `RESOLVED_CONFIRMED`.
2. User silence không phải confirmation.
3. Explicit same-problem “still failing” có thể reopen provisional/confirmed outcome nếu exact linkage đủ.
4. Với coding/mutation task, problem resolution không bypass engineering proof/acceptance floor.
5. Một diagnosis/config/explanation task có thể resolve mà engineering acceptance là `NOT_APPLICABLE`.

Resolution matrix:

| Engineering trusted | User/problem resolution | Interpretation |
|---|---|---|
| no | no | unresolved |
| yes | no | engineering accepted, problem unresolved/reopened |
| no | yes | user may feel resolved but trusted technical resolution chưa đủ nếu task cần proof |
| yes | yes | resolved confirmed |

---

# 8. UNIFIED LOSS MODEL — HAI TẦNG, KHÔNG MỘT SCALAR GIẢ

## 8.1. Execution loss plane

```text
useful execution / proof          [không phải loss mặc định]
solution repair
orchestration repair
proof / oracle repair
runtime / environment repair
source / control drift
wait / recovery
model / controller resource
human intervention
unattributed
```

## 8.2. Problem-resolution loss plane

```text
unresolved problem / quality failure
assistant misunderstanding
wrong scope / workspace
wrong root cause
insufficient solution scope
proof/oracle gap exposed by user path
avoidable correction
reopen
stale context / replay
problem-resolution waiting/tail
legitimate requirement growth       [tracked, không mặc định là loss]
unknown / unattributed
```

## 8.3. Problem Resolution Loss Vector

```text
(
  trusted_correctness_failure,
  unresolved_problem_state,
  avoidable_correction_burden,
  reopen_burden,
  TTPR,
  engineering_repair_burden,
  runtime_or_proof_loss,
  human_intervention,
  measured_resource_and_money
)
```

Dùng lexicographic/Pareto analysis. Chỉ xây scalar nếu sau này có calibrated utility weights và complete enough measurement.

---

# 9. GATE 0 — TRUTH VÀ LIFECYCLE RECONCILIATION

Gate 0 vẫn là prerequisite cho **mọi** code-bearing causal measurement layer, kể cả PRL implementation.

Snapshot cho thấy lifecycle ambiguity đủ lớn để ưu tiên, nhưng chưa đủ để gọi tất cả active rows là zombie.

## 9.1. Read-only classifier trước ontology mới

Dùng primitives hiện có để classify:

```text
LIVE_OWNED
P5_EXPERIMENT_ANCHOR
AWAITING_ACCEPTANCE
GRACE_PERIOD_INACTIVE
THRESHOLD_SENSITIVE_STALE_CANDIDATE
TERMINAL_PARENT_CONTRADICTION
ORPHANED_OR_FOREIGN_MANAGED_JOB
PROJECTION_DRIFT
UNEXPLAINED_ACTIVE
```

Không thêm durable lifecycle enum trước khi projection classifier chứng minh existing facts không đủ.

## 9.2. Gate 0 exit criteria

PASS khi:

- ordinary active execution không còn `UNEXPLAINED_ACTIVE`;
- mọi active row còn lại có exact live owner/reason hoặc P5 anchor hợp lệ;
- no active foreign/orphan managed job;
- supporting projections reconcile canonical ledger/Git/process identity;
- P5 anchor tách rõ ordinary execution;
- ledger integrity/hash/event-chain/FK checks applicable vẫn pass;
- release/maintenance freeze không còn active lease/fence residue;
- mọi reconciliation mutation nếu có đi qua official authority, không direct SQLite/JSON surgery.

Gate 0 không yêu cầu “làm đẹp” toàn bộ historical rows; nó yêu cầu current active state có nghĩa và authority rõ.

---

# 10. WAVE A1 — FAILURE DETAIL COVERAGE, KHÔNG TAXONOMY FRAMEWORK MỚI

`p2_failure_observation_v3` đã có. Vì vậy:

```text
NEW TAXONOMY FRAMEWORK        = REJECT_CURRENT
EMITTER / DETAIL COVERAGE     = ADOPT
```

A1-R0 phải reconcile reporter semantics trước khi ranking subtype nếu raw JSON và decoded/scalar facts breakdown khác nhau.

Mỗi generic failure event mới cần factual detail hoặc explicit unknown reason:

```text
stage
command_family / verification_stage khi biết
baseline observation khi measured
environment observation khi measured
unknown_reason
```

Causal label/root cause tách riêng.

Acceptance:

- new generic failure events có v3 detail hoặc explicit unknown reason;
- zero historical causal backfill;
- content-free;
- legacy unknown vẫn unknown;
- emitter/reporter focused proof pass;
- current-source denominator/missingness rõ.

---

# 11. PRL-A — PROBLEM IDENTITY & EXACT LINKAGE

Sau Gate 0, PRL-A có thể tiến cùng tranche với A1 vì hai phần giải hai measurement gaps khác nhau. Không nhất thiết chạy concurrent writers; causal order chỉ yêu cầu cả hai foundation có mặt trước unified analysis.

## 11.1. Scope tối thiểu

```text
problem_id
problem_revision
problem state metadata
exact turn/trace relation
run/wave link khi có execution
handoff capsule active_problem pointer
```

Không classifier feedback ở PRL-A. Không routing. Không policy. Không raw transcript.

## 11.2. Acceptance

- one problem spans multiple runs;
- one problem spans conversation epochs;
- same conversation có thể có multiple problem IDs;
- exact identity, no timestamp proximity;
- ambiguous links fail closed for policy evidence;
- no second ledger/authority;
- no ninth public tool;
- raw user/assistant content absent from persisted PRL records.

---

# 12. A2 + PRL-B/C — STAGE ATTRIBUTION PHẢI ĐO TỚI RESOLUTION, KHÔNG DỪNG Ở `report_visible`

A2 ban đầu có execution vocabulary:

```text
turn_received
preflight
localization
routing
execution
replan
proof
acceptance
report_visible
```

Điều này vẫn đúng cho execution path nhưng `report_visible` **không phải terminal point của problem-level science**.

Extension boundary phải biểu diễn, khi có exact observable event:

```text
report_visible
  → user_feedback_received
  → feedback_relation_classified
  → problem_state_updated
  → provisionally_resolved / confirmed / reopened / new_revision
```

Không suy `user_observed` chỉ vì UI đã render. Chỉ dùng host-visible event và actual user feedback/turn khi quan sát được.

## 12.1. A2 measurement contract

- every duration declares clock domain;
- exact turn/run/wave binding cho EOCL turns;
- no-run turn có explicit content-free reason;
- zero timestamp-proximity joining;
- required-stage missingness explicit;
- problem events dùng exact problem/turn identity, không raw text;
- cross-clock ordering cần dependency identity.

## 12.2. PRL-B feedback shadow

Feedback classification phải shadow-first:

- observed / derived-high-confidence / inferred / unknown provenance;
- new requirement không tự tính assistant failure;
- avoidable correction phải có evidence;
- no production behavior change.

## 12.3. PRL-C resolution/reopen

- assistant “done” → provisional at most;
- user explicit confirmation → confirmed;
- silence → unconfirmed, không confirmed;
- same-problem corrective feedback → unresolved/reopened khi linkage đủ;
- coding task vẫn cần engineering floor.

## 12.4. Measurement readiness

Để dùng inferentially cho decision:

- natural current-source workload;
- exact binding coverage cao theo preregistered threshold;
- stage/problem event completeness đủ;
- manual-reviewed sample chứng minh same-problem and feedback-label quality;
- không systematic bias biến requirement growth thành AI failure;
- nếu throughput/coverage không đạt trong horizon thì `INSUFFICIENT_THROUGHPUT_OR_COVERAGE`, không synthetic-fill production evidence.

---

# 13. UNIFIED MECHANISM RANKING VÀ A3 TARGETED INTERVENTION

Sau A1 + PRL-A + A2/PRL-B/C, loss ranking mới đủ chiều.

Không chỉ hỏi:

> “stage nào tốn thời gian?”

mà hỏi:

> “mechanism nào làm accepted-result hoặc problem-resolution path xấu đi, với evidence và khả năng can thiệp thực sự?”

Ranking dùng Pareto dimensions:

- exact-current-source frequency;
- affected results/problems;
- same-domain excess delay;
- TTPR/TTAR tail contribution;
- avoidable-correction/reopen contribution;
- defect/authority severity;
- measurement coverage/missingness;
- reversibility/change size;
- confidence in mechanism.

Chỉ mở intervention nhỏ nhất cho 1–2 mechanisms. Không mở framework/refactor tổng quát.

Mỗi intervention packet phải khóa:

```text
baseline identities
causal hypothesis
smallest change
quality/security/authority guardrails
measurement horizon
population/enrollment
stop/revert condition
source/runtime/oracle/problem-evaluator fingerprint
evidence/acceptance owner
```

Before/after observational comparison không đủ để claim causal treatment effect khi randomized/ITT design khả thi.

---

# 14. PRL-D — PROBLEM ECONOMICS REPORTER

Reporter read-only, descriptive-first:

```text
problems opened
resolved confirmed
resolved unconfirmed
reopened
problem resolution rate
first-response resolution rate
avoidable corrections / problem
productive clarifications / problem
TTPR p50 / p90
runs / waves / replans / proofs per problem
accepted runs before final problem resolution
correction cause mix
problem linkage / label coverage
```

Không dùng một “user quality score” scalar. Không gọi unconfirmed là confirmed success.

Metric đặc biệt quan trọng:

> **accepted_runs_before_final_resolution**

Nó đo blind spot mà RUN-centric economics không thấy: bao nhiêu engineering attempts đã được accept nhưng user problem vẫn tiếp tục.

---

# 15. P4 / P5 — TỪ EXECUTION OUTCOME TỚI FUTURE PROBLEM-LEVEL ENDPOINTS

## 15.1. P4

P4 tiếp tục `COLLECTING / PASSIVE`.

PRL có thể tạo future outcomes tốt hơn như:

```text
avoidable problem correction
reopen
problem-level first-response resolution
```

nhưng **không đổi P4 endpoint/policy trước khi PRL label/link quality được validate**.

## 15.2. P5 current/history boundary

`CW-S1` ghi A0 active zero-funnel; final historical recapture lúc `14:01:41Z` vẫn zero. Bản docs synthesis này không recapture current P5 authority state và không được dùng để nói epoch hiện giờ đang active/closed.

Do đó trước P5 action tương lai:

```text
fresh P5/source/runtime recapture
  → reconcile post-open source/docs drift
  → exact manifest/source-clean decision
  → only then enrollment or new epoch
```

Không reinterpret old P5 rows bằng PRL metric mới.

## 15.3. Future P5 experiment endpoints

Chỉ future manifest sau PRL measurement validation mới được preregister thêm:

```text
problem-level first-response resolution
avoidable correction burden
reopen rate
TTPR distribution
```

bên cạnh execution-level:

```text
quality
first-pass/repaired
restricted TTAR
resources
cost when measured
```

P5 treatment vẫn cần separate authorization; PRL không cấp treatment authority.

---

# 16. ROUTING ECONOMICS — VẪN HOLD

Automatic Mini/Luna/Terra/Sol routing chưa admissible vì:

- P4 chưa validated signals;
- HR representative pair counts = 0 trong snapshot;
- CW paired-policy denominator không recaptured trong integrated snapshot;
- monetary/controller cost attribution thiếu;
- problem-level outcome chưa có validated measurement.

Future routing cần local representative pairs/cohorts cùng:

```text
same task/problem semantics
same source fingerprint
same oracle
same environment/cache stratum
quality hard floor
repair/reopen/TTPR noninferiority
resource noninferiority
monetary evidence when complete
deterministic fallback
router version/fingerprint/drift monitoring
```

Router phải được đánh giá như một model/policy riêng. Vendor benchmark hoặc model mới không phải reopen trigger.

---

# 17. TRACK B — RELIABILITY / RELEASE HARDENING

Track B độc lập với causal-learning promotion nhưng share Gate 0.

Sequence:

| Step | Required evidence |
|---:|---|
| B1 Credential remediation | rotation/revocation receipt từ owning service; no raw secret in report/Git/chat |
| B2 Git-history decision | explicit retain-vs-rewrite decision; history rewrite cần destructive authority riêng |
| B3 Lifecycle reconciliation | Gate 0 PASS; no unexplained active/foreign job residue |
| B4 Recovery P0.3 | isolated packaged F1–F9; reboot/logon proof khi release scope yêu cầu |
| B5 Exact source/evidence freeze | exact code-bearing HEAD, worktree/evidence boundary, P5 reconciliation |
| B6 Focused/affected proof | exact-fingerprint proof cho actual delta |
| B7 Loaded-runtime proof | source↔loaded runtime/process/workspace/device match |
| B8 Exact-source package/NSIS | artifact hash + source/builder/config/dependency provenance |
| B9 Installed session | install/start/logon/recovery/safe rollback proof |
| B10 Publish/release | explicit user authority naming destination/version/artifact; verify downloaded bytes |

Không dùng old `win-unpacked` làm release candidate cho current source.

---

# 18. HOLD / ANTI-OVERENGINEERING REGISTER

Các hạng mục mặc định `HOLD` cho tới explicit evidence trigger:

| HOLD | Lý do / reopen trigger |
|---|---|
| Agent-manager/default multi-agent | Chỉ reopen khi repeated natural tasks chứng minh sequential single-lane capacity là bottleneck và disjoint parallel work có positive expected value. |
| Public MCP tool #9 | Chỉ khi named external consumer không thể compose capability qua 8-tool surface với acceptable risk/cost. |
| Second problem/orchestration DB | PRL phải reuse canonical ledger/event plane; reopen chỉ khi real second consumer/scale constraint chứng minh need. |
| Transcript database / conversation knowledge graph | Privacy/context bloat; PRL content-free đủ cho current research. |
| Generic memory platform | Handoff/state capsule + PRL pointer trước; reopen khi repeated failure không giải được. |
| Automatic LLM feedback judge | Chỉ shadow until independently validated; never authority by default. |
| Automatic routing | §16 evidence gates. |
| RL router / P8 joint optimizer | Inputs/causal effects/costs chưa đủ. |
| Proof-cache v2 | Current hit 4/1,563; reopen khi prospective proof repetition đóng ≥10% relevant tail và expected benefit rõ. |
| Native semantic/LSP expansion | Named consumer + configured binding + representative benefit study. |
| Server-first promotion | Natural powered placement evidence + quality/TTAR/resource gates. |
| General vector DB | Chỉ khi canonical indexed facts không đáp ứng repeated query SLA sau optimization. |
| Computer Use | Chỉ khi structured API/CLI/file/Git không thể đáp ứng và có isolated safety contract. |
| A2A/remote-device lease/hosted OAuth | Named product requirement + identity/authority/security contract. |
| Dashboard-only work | Chỉ khi operators có repeated decision gap mà existing reports không trả lời; data authority phải sound trước. |
| New P5 service/framework | Existing manifest/funnel tables chưa được chứng minh thiếu; zero natural data không phải architecture gap. |
| Broad upstream merge | Feature-by-feature R0–R5 only. |
| MCP 2026 Tasks adapter | Named host/consumer + compatibility/migration proof, không chỉ vì spec mới tồn tại. |

`HOLD` không nghĩa “không bao giờ”; nó nghĩa không tiêu critical-path effort trước observed trigger.

---

# 19. FALSIFICATION CONTRACT — KHI NÀO CHIẾN LƯỢC NÀY PHẢI ĐỔI

## F1 — Lifecycle priority

Nếu fresh exact-source census cho thấy gần như toàn bộ active rows có valid owner/liveness/reason, zero contradiction và `UNEXPLAINED_ACTIVE` residual negligible, hạ Gate-0 lifecycle work xuống maintenance.

## F2 — A1 failure detail

Nếu ≥30 new generic events có actionable detail ≥95%, unknown/other ≤5% và unclassified mechanism không đóng góp material loss, không mở taxonomy work thêm.

## F3 — A2 stage attribution

Nếu coverage/binding pass nhưng top tail chủ yếu là explicit unavoidable external/operator wait ngoài product authority, hạ stage optimization và chuyển sang expectation/UI/reporting.

## F4 — PRL unit-of-analysis thesis

PRL bị yếu đi nếu prospective representative data cho thấy:

- accepted engineering results hầu như luôn đồng thời resolve problem;
- same-problem corrective feedback/reopen sau accepted attempt cực hiếm;
- problem-level measurement không thay ranking/intervention decision.

Khi đó giữ PRL nhỏ như correlation/reporting layer; không mở rộng ontology.

## F5 — Feedback taxonomy usefulness

Nếu reviewed sample cho label agreement thấp hoặc categories không tạo distinct engineering/economic decisions, simplify taxonomy. Không xây dashboard trên false precision.

## F6 — P5 throughput

Nếu natural workload qua predeclared horizon vẫn không tạo completed blocks dù eligibility/instrumentation đúng, kết luận `INSUFFICIENT_THROUGHPUT`; không synthetic-fill production evidence.

## F7 — Architecture freeze

Chỉ mở architecture mới khi ≥3 independent natural occurrences cùng class hoặc một critical defect chứng minh primitives hiện tại không thể giải quyết an toàn.

---

# 20. UPDATED DECISION LOG

| ID | Quyết định |
|---|---|
| `D-01` | Freeze relative core architecture; complexity mới phải có observed trigger. |
| `D-02` | Gate 0 lifecycle/evidence truth là prerequisite cho source-bearing causal work và release freeze. |
| `D-03` | North Star lexicographic; không scalar CAR/loss khi units/missingness chưa reconciled. |
| `D-04` | Enforce existing P2 v3 emitters; no taxonomy framework/backfill. |
| `D-05` | Reuse observation spans; no new telemetry subsystem. |
| `D-06` | P4 passive/collecting; no predictor tuning to green. |
| `D-07` | P5 natural/explicit; no synthetic funnel; separate workspace epochs. |
| `D-08` | Automatic routing/cost optimizer HOLD. |
| `D-09` | Reliability/release là Track B riêng, share Gate 0. |
| `D-10` | MCP 2026-07-28 compatibility là future bounded assessment, không product-migration authority. |
| `D-11` | RUN là execution unit; Problem Resolution Thread là end-to-end user-resolution evaluation unit. |
| `D-12` | `ACCEPTED RUN != PROBLEM RESOLVED`; engineering acceptance không tự đóng problem. |
| `D-13` | EOCL authority không đổi; PRL chỉ correlation/evaluation. |
| `D-14` | User follow-up không tự là failure; optimize avoidable correction, không optimize low interaction. |
| `D-15` | Problem linkage/feedback labeling prospective, content-free, unknown-preserving. |
| `D-16` | Gate 0 phải đi trước PRL source implementation; sau đó A1 và PRL-A là hai measurement foundations. |
| `D-17` | A2 stage model phải có extension boundary tới feedback/resolution/reopen; `report_visible` không là problem terminal state. |
| `D-18` | Accepted-Result Economics được giữ làm execution subsystem của Accepted Problem Resolution Economics. |
| `D-19` | P5 problem-level endpoint chỉ dùng future manifest sau PRL validation; không reinterpret old/current A0 data. |
| `D-20` | Post-open repository docs drift yêu cầu fresh P5/source reconciliation trước future enrollment/source-writing; docs update này không tự thao tác P5. |

---

# 21. EXACT NEXT ACTIONS SAU TÀI LIỆU NÀY

Không được nhảy thẳng vào router/P5 treatment/PRL mega-implementation.

## Step 1 — `G0-R1`: fresh one-snapshot lifecycle census

Recapture, không reuse `CW-S1/HR-S1` như current operation authority.

Output:

```text
class counts
residual opaque IDs
threshold sensitivity
projection contradictions
exact owner/liveness evidence
P5 anchor separation
official-authority reconciliation proposal
```

Zero mutation trong census.

## Step 2 — `G0-LC1`: read-only lifecycle classifier nếu existing facts API chưa đủ projection

Ưu tiên integrate vào existing ledger-analysis/maintenance facts thay vì tạo module duplicate. Không schema/public tool/state change.

## Step 3 — official authority reconciliation

Chỉ sau operator review. Không direct SQLite/JSON edit.

## Step 4 — source/P5 recapture decision

Trước bất kỳ code-bearing A1/PRL/A2 wave:

- fresh Git/code-bearing/worktree status;
- exact current P5 lifecycle/manifest/source identity qua supported authority;
- quyết định xử lý docs/source drift;
- confirm no conflicting writer/lease/fence.

## Step 5 — measurement foundation tranche

Sau Gate 0/P5-source gate:

```text
A1-R0 reporter coherence
A1-E1 generic failure emitter coverage
PRL-A problem identity/exact linkage
```

Chúng có thể cùng tranche chiến lược nhưng mỗi source mutation/proof phải giữ causal boundary rõ; không giant wave.

## Step 6 — integrated interaction measurement

```text
A2 execution stage coverage
+ PRL-B feedback shadow
+ PRL-C resolution/reopen
```

Thiết kế chung contract identity/clock/privacy nhưng implementation nhỏ, testable.

## Step 7 — PRL-D + unified loss analysis

Chỉ descriptive trước. Đo xem problem-level metrics có thay decision ranking thật không.

## Step 8 — targeted intervention

Chọn 1–3 mechanisms có evidence mạnh nhất; preregister stop/revert.

## Step 9 — P5 future experiment

Chỉ sau measurement/integrity gates; future problem endpoints nếu validated.

## Step 10 — routing economics

Chỉ sau representative paired evidence + quality/problem-resolution/resource/cost gates.

---

# 22. IMPLEMENTATION ACCEPTANCE CONTRACT CHO PRL TƯƠNG LAI

Nếu PRL-A/B/C được triển khai, tối thiểu phải có deterministic tests cho:

1. same problem spans two runs;
2. problem spans conversation epochs;
3. same conversation contains a new separate problem;
4. ambiguous relation không auto-merge policy history;
5. silence remains unconfirmed;
6. explicit same-problem failure reopens;
7. new requirement không bị tính avoidable correction;
8. explicit wrong-workspace correction được classify đúng khi evidence đủ;
9. problem-resolution state không cấp EOCL acceptance authority;
10. raw prompt/response/CoT không persist;
11. no public tool #9;
12. handoff/recovery preserves exact active problem pointer without transcript replay.

Manual-reviewed natural sample dùng để validate semantic labels; unit tests không thể chứng minh taxonomy quality trên real interaction.

---

# 23. RESEARCH BASIS — TẠI SAO PROBLEM-LEVEL LAYER HỢP LÝ NHƯNG VẪN PHẢI LOCAL-VALIDATE

Companion PRL review tổng hợp bốn dòng nghiên cứu:

1. **Conversational repair:** correction là normal mechanism để khôi phục mutual understanding, không phải noise.
2. **Requirements traceability:** requirement evolution phải nối tới artifact/decision/implementation; problem thread gần với một live issue có revision/reopen.
3. **Human-in-the-loop software engineering:** human refinement/guidance là control input thực, không tự động là model failure.
4. **Interactive coding-agent evaluation 2026:** SWE-Together, SWE-Interact, RECODE-H và các interactive/closed-loop evaluations đều chuyển khỏi one-shot “prompt → patch” sang multi-turn correction/adaptation/outcome.

Community Codex issues về compaction/stale state/premature completion được dùng như **failure hypotheses**, không prevalence statistics.

External research không thay local evidence. Promotion vẫn cần natural representative prospective data của Coding Web/HR.

---

# 24. PRIVACY, SAFETY VÀ ANTI-GAMING

## 24.1. Content-free by design

Không persist:

- raw prompt/user text;
- raw assistant response;
- chain-of-thought/private reasoning;
- source contents;
- long stdout/stderr;
- secrets/credentials;
- HR/Finance business payload không cần thiết.

## 24.2. Correction metric anti-gaming

Không tối ưu correction count bằng cách:

- không hỏi clarification cần thiết;
- ít báo tiến độ;
- spam user xin “confirm” để làm đẹp resolution rate;
- over-scope patch lần đầu để né follow-up.

Quality/problem resolution floors luôn đứng trước low-interaction metric.

## 24.3. Confirmation semantics

```text
assistant says done          != confirmed
no user reply                != confirmed
user explicit confirms       = strong confirmation evidence
later same-problem failure   = reopen evidence khi linkage đủ
```

---

# 25. DELIVERY / SNAPSHOT RECONCILIATION

## 25.1. Historical v1 state được giữ như chronology

V1 ghi:

- report bytes ban đầu ở external draft;
- `CW-S1` P5 A0 active, zero funnel;
- final recapture `2026-08-23T14:01:41Z` vẫn A0 active/zero funnel;
- PRL file xuất hiện concurrent untracked docs delta;
- intended target report khi đó chưa tồn tại.

Những câu đó là **historical snapshot facts** tại thời điểm v1 soạn.

## 25.2. Repository state sau đó

Tài liệu report và PRL hiện đã nằm trong `docs/research` dưới dạng **untracked repository drafts**. Vì vậy metadata “external draft/current draft target outside repo” của v1 đã stale và được thay bằng note post-snapshot ở §0.4.

Việc file nằm trong repository **không tự chứng minh**:

- P5 đã closed (trạng thái này chỉ được khẳng định bởi receipt C0 mới hơn, không phải bởi vị trí file);
- source-clean gate đã pass;
- current loaded runtime identity;
- package/release readiness;
- commit/push status.

Bản synthesis v2 ban đầu không gọi P5 lifecycle mutation và không recertify `CW-S1` thành live truth. Correction note sau snapshot cũng không sửa số liệu snapshot hoặc biến source proof thành runtime/package/release proof.

## 25.3. Git/delivery

Đây là documentation write. Không có claim rằng file đã staged/committed/pushed. Khi sau này delivery được yêu cầu, phải tuân thủ repository `.coding-tools` evidence policy và delivery guards trên exact current checkout.

---

# 26. FINAL DOCTRINE

Coding Web đã có một execution substrate đủ trưởng thành để bước sang giai đoạn **decision science**, nhưng execution truth chỉ là tầng giữa của giá trị cuối cùng.

Kiến trúc mục tiêu:

```text
USER PROBLEM
  ↓
PROBLEM IDENTITY / INTENT REVISION
  ↓
ASSISTANT ATTEMPT
  ↓
EOCL EXECUTION / PROOF / ACCEPTANCE
  ↓
ASSISTANT RESULT
  ↓
USER FEEDBACK
  ├── productive clarification / new requirement
  └── avoidable correction / reopen
  ↓
PROBLEM STATE UPDATE
  ↓
RESOLVED_CONFIRMED / UNCONFIRMED / REOPENED
  ↓
UNIFIED EXECUTION + PROBLEM-RESOLUTION ECONOMICS
  ↓
CAUSAL INTERVENTION SCIENCE
  ↓
P5 PROSPECTIVE LEARNING
  ↓
ADAPTIVE ROUTING — ONLY WHEN LOCALLY PROVEN
```

Không tối ưu số model calls.
Không tối ưu số RUN accepted độc lập.
Không tối ưu “ít user reply” bằng cách giảm collaboration hữu ích.
Không tối ưu token/cost trước correctness và resolution.

Tối ưu:

> **Một vấn đề thực của người dùng được hiểu đúng, giải quyết đúng, có engineering evidence đáng tin khi cần, ít avoidable correction/reopen, tail thấp, resource/cost hợp lý và không làm phình architecture quá mức cần thiết.**

Đây là cách hợp nhất đầy đủ giữa Evidence-Governed Execution và Problem-Centric Interactive Engineering mà không phá doctrine one-runtime, one-writer, EOCL authority, `smart-v3=8`, prospective evidence và anti-overengineering hiện tại.

---

# 27. SOURCE / RESEARCH INDEX

## Internal canonical/maintained

- `AGENTS.md`
- `docs/CURRENT_STATE.md`
- `docs/ROADMAP.md`
- `docs/ARCHITECTURE.md`
- `docs/RELEASE_CHECKLIST.md`
- `docs/REMEDIATION_ACCEPTANCE_RUNBOOK.md`
- `.coding-tools/orchestration/ledger.sqlite3`
- host evaluation journal / performance projections theo snapshot contract

## Internal research companions

- `docs/research/260822_CODING_WEB_EXECUTION_INTELLIGENCE_UPSTREAM_ADOPTION_AND_NEXT_IMPLEMENTATION_MASTER_PLAN.md`
- `docs/research/260822_CODING_WEB_REWORK_DECISION_SCIENCE_AND_EXECUTION_DOCTRINE.md`
- `docs/research/260823_CODING_WEB_PROBLEM_RESOLUTION_LINEAGE_AND_INTERACTIVE_ENGINEERING_SCIENCE.md`

## External methodological families retained from v1/PRL review

- Anthropic — Building effective agents; Demystifying evals for AI agents
- AI Agents That Matter / TMLR
- METR experienced-developer AI productivity studies and experiment-design updates
- SWE-Lancer
- RouteLLM / FrugalGPT
- W3C Trace Context
- OpenTelemetry GenAI semantic conventions — optional projection only
- NIST AI RMF
- SLSA
- MCP official specifications
- conversational repair literature
- requirements traceability literature
- Human-In-the-Loop Software Development Agents
- RECODE-H
- SWE-Together
- SWE-Interact
- interactive multi-requirement software engineering evaluation
- closed-loop coding-agent evaluation
- Codex/community issue reports only as failure hypotheses

External evidence informs methodology; **local exact prospective evidence remains authority for Coding Web policy promotion.**

---

**END — CW-ERCIP-20260823-v2**
