# CODING WEB — KẾ HOẠCH TỔNG THỂ TIẾP THEO VỀ EXECUTION INTELLIGENCE, CHỌN LỌC UPSTREAM VÀ TRIỂN KHAI HOÀN THIỆN

> **Bản hợp nhất và diễn giải chi tiết bằng tiếng Việt:** 2026-08-22  
> **Workspace:** `E:\DEV\Codex-web`  
> **Phân loại tài liệu:** chiến lược kỹ thuật hợp nhất + phân tích kiến trúc + kế hoạch triển khai + tiêu chí nghiệm thu  
> **Phạm vi:** Coding Web / Codex-web, WebCodex upstream, EOCL, P4/P5/P7/P8, execution lifecycle, mutation reliability, deterministic review  
> **Nguyên tắc ưu tiên sự thật:** implementation hiện tại + proof đúng fingerprint + runtime/EOCL live + `docs/CURRENT_STATE.md` + `docs/ROADMAP.md` luôn có quyền ưu tiên cao hơn tài liệu nghiên cứu có ngày này  
> **Mục đích:** thay thế cách hiểu cũ rằng T2/T3/C1 còn là backlog tương lai, đồng thời tạo một kế hoạch triển khai tiếp theo đủ chi tiết để có thể đi thẳng vào engineering wave mà không phải dựng thêm một kiến trúc trung gian mới.

---

# 0. KẾT LUẬN ĐIỀU HÀNH

Chương trình **Truth / Traceability Hardening** được hình thành ngày 21/08/2026 đã hoàn thành đúng mục đích ban đầu của nó.

Chuỗi:

```text
T0  Truth Reconciliation
 -> T1  Wave Objective Provenance
 -> T2  TruthSnapshot
 -> T2.1 Integration Repair
 -> T3  Operator Truth Console
 -> C1  Executable Engineering Casebook
 -> STOP / EVALUATE
```

không còn là một backlog kiến trúc cần tiếp tục mở rộng.

Quyết định chính thức của giai đoạn tiếp theo là:

> **ĐÓNG BĂNG T0–T3–C1 ở cấp kiến trúc.**  
> Không xây thêm Truth Platform, Truth Database, second ledger, second identity authority, generic replay engine, public MCP tool thứ 9 hoặc một hệ thống đồng bộ upstream toàn diện.

Lý do rất quan trọng: Coding Web hiện không thiếu thêm một tầng điều khiển. Hệ thống đã có đủ các thành phần nền tảng như một Runtime authority, một writer, EOCL, proof identity, source/workspace/runtime truth, Recovery Host, deterministic-first execution và public surface `smart-v3 = 8 tools`.

Vấn đề có giá trị kinh tế cao hơn nằm ở một causal chain khác:

```text
execution truth chính xác
        +
mutation chính xác ngay lần đầu trên Windows
        +
review/localization deterministic trên exact committed range
        +
context đưa cho Sol được thu nhỏ theo bằng chứng
        +
EOCL acceptance hiện có
        ↓
ít retry hơn
ít replan hơn
ít rework hơn
TTAR thấp hơn
accepted-result cost thấp hơn
```

Sau khi đối chiếu source hiện tại với upstream `yyjeqhc/webcodex`, chương trình tiếp theo được chia thành bốn wave có cơ chế nhân quả và acceptance oracle tách biệt:

1. **Wave A — Execution Truth & Long-Run Robustness**  
   Adapt upstream **#113 ContinuousPipeDrain** và chỉ lấy các lifecycle invariant còn thiếu từ **#112**.

2. **Wave B — Windows Mutation Reliability**  
   Port/adapt upstream **#90 CRLF-aware guarded edits**, nhưng không làm yếu exact matching và không biến patching thành fuzzy editing.

3. **Wave C — Deterministic Committed-Review Intelligence**  
   Adapt **#116 `git_review_summary`** và **#117 exact committed-range `git_diff_hunks`** thành deterministic internal evidence plane nằm dưới `agent_workflow`; tuyệt đối không mở rộng `smart-v3` thành 9 hoặc 10 public tools.

4. **Wave D — Accepted-Result Economics Rebaseline**  
   Đo lại tác động của A/B/C lên rework, retry, TTAR, tool hops, review bytes, infrastructure failure và human intervention trước khi quyết định có nên mở thêm một tranche upstream hay không.

Các capability khác tiếp tục bị gate:

- **#111 Managed OAuth:** defer đến khi có nhu cầu hosted/multi-user thật.
- **#114 Local MCP Gateway:** chưa port; hiện tại tạo nhiều authority/credential/context risk hơn giá trị.
- **#115 Onboarding:** chỉ học UX, không bê nguyên architecture.
- **Computer Use:** giữ là last-mile fallback; không biến thành core coding execution plane.

North Star vẫn là:

> **Accepted Result đáng tin cậy với chi phí kỳ vọng thấp nhất**, không phải số feature, số agent, số tool, số token, số dòng code hay mức độ giống upstream.

---

# 1. TÀI LIỆU NÀY HỢP NHẤT NHỮNG GÌ

Tài liệu này hợp nhất ý nghĩa triển khai hiện hành của các nguồn sau:

1. `docs/research/260821_TRUTH_RECONCILIATION_CHECKPOINT.md`
2. `docs/research/260821_CODING_WEB_LEAN_CONTROL_RICH_EVIDENCE_ACCEPTED_RESULT_SYNTHESIS.md`
3. `docs/research/260821_CODING_WEB_MASTER_ENGINEERING_STRATEGY_AND_HISTORY.md`
4. hai phân tích upstream bổ sung ngày 22/08/2026
5. `docs/CURRENT_STATE.md`
6. `docs/ROADMAP.md`
7. current source / live runtime / EOCL evidence của checkout đang vận hành

Ba file ngày 21/08 **không bị xóa**. Chúng tiếp tục là historical decision record và forensic evidence. Tài liệu này chỉ thay thế cách hiểu “phần nào còn phải làm tiếp”.

## 1.1. Bản đồ supersession

| Phát biểu cũ | Cách hiểu mới ngày 22/08 |
|---|---|
| T2 TruthSnapshot chưa triển khai | **Đã lỗi thời — T2 đã implemented + accepted** |
| T3 Operator Truth Console chưa triển khai | **Đã lỗi thời — T3 đã implemented + recertified sau T2.1** |
| C1 Casebook chưa triển khai | **Đã lỗi thời — bounded 7-case casebook đã accepted** |
| “Next wave = T2” | **Đã lỗi thời — toàn chuỗi T0–T3–C1 đã tới STOP/EVALUATE** |
| Truth hardening là chương trình engineering chính hiện tại | **Không còn đúng — chỉ reopen nếu có regression cụ thể** |
| Lean Control + Rich Evidence + Rework-First Economics | **Giữ nguyên làm doctrine** |
| Upstream R0→R5 | **Giữ nguyên và áp dụng trực tiếp cho #90/#112/#113/#116/#117** |
| One Runtime / one writer / EOCL / smart-v3 = 8 | **Giữ nguyên, không thương lượng** |

## 1.2. Thứ tự ưu tiên nguồn sự thật

Khi có mâu thuẫn:

```text
1. Current implementation + exact focused/live proof
2. Live EOCL/runtime contract
3. AGENTS.md
4. docs/CURRENT_STATE.md
5. docs/ROADMAP.md
6. Maintained subsystem docs
7. Tài liệu master này
8. Older research/history
```

Điều này ngăn một lỗi rất thường gặp trong các dự án agent dài ngày:

> một tài liệu từng đúng về mechanism nhưng cũ về status không được phép kéo dự án quay lại một backlog đã hoàn tất.

---

# 2. BASELINE QUAN SÁT TẠI THỜI ĐIỂM HỢP NHẤT

Baseline đã quan sát khi xây tài liệu này:

```text
workspace: E:\DEV\Codex-web
branch: main
local HEAD: c9648f524d3eccb5ad257ff00748a1fbcb7fe40f
tracking: origin/main
local ahead: 2 commits
runtime version: 0.4.3
smart-v3 public tool count: 8
runtime source dirty: false
stale orchestration runs: 0
orphaned background operations: 0
orphaned idempotency records: 0
```

Hai commit local đi trước origin tại checkpoint đó là evidence/closure commits, không phải production source implementation delta mới.

Vì vậy phải giữ hai khái niệm tách biệt:

```text
SOURCE IDENTITY
!=
EVIDENCE/HISTORY COMMIT IDENTITY
```

Điều này đặc biệt quan trọng với P5, vì P5 dùng exact source identity để xác định experiment epoch. Một evidence-only commit dưới `.coding-tools/**` không được tự động biến thành “execution substrate mới” nếu canonical source-identity policy hiện hành đã loại loại commit đó khỏi source fingerprint.

Tài liệu này cũng **không** khẳng định package/release hiện tại chứa toàn bộ current source byte. Source present, proof pass, EOCL accepted, live activated, packaged và released luôn là sáu claim riêng.

---

# 3. T0–T3–C1: TRẠNG THÁI HỢP NHẤT CUỐI CÙNG

## 3.1. Ma trận closure

| Hạng mục | Trạng thái hiện tại | Bằng chứng mạnh nhất | Quyết định |
|---|---|---|---|
| T0 Truth Reconciliation | hoàn thành đúng scope claim-plane | precedence + source/proof/live/package/release separation đã được duy trì | **CLOSED** |
| T1 Wave Objective Provenance | source implemented | run `25941039edd44267a04e3fbcd4f4f860`; later fail-closed behavior chứng minh objective revision/hash/source có tác dụng | **CLOSED / ACCEPTED** |
| T2 TruthSnapshot | read-only projection implemented | run `14799bbc694f49d09e6b7277acf8b41e` accepted/checkpointed | **CLOSED / ACCEPTED** |
| T2.1 integration repair | active-wave/fallback integration đã sửa | canonical repair run `df773562c37d42e6ae5c90505544e408` accepted | **CLOSED / ACCEPTED** |
| T3 Operator Truth Console | renderer consume canonical TruthSnapshot | recertification run `480c6330137c44e1932347ed796c251f` checkpointed | **CLOSED / RECERTIFIED** |
| C1 Executable Engineering Casebook | 7 deterministic case đã có | run `79fe8b39b18d48b9be16f2786d06e2dc` focused + full proof trước checkpoint | **CLOSED / ACCEPTED** |

## 3.2. Tại sao T1 có giá trị thực tế

T1 không đơn thuần là thêm metadata.

Trước T1, một run có thể giữ “initial objective”, nhưng REPLAN sau đó có thể thay đổi mục tiêu thực tế của wave. Nếu report vẫn mang objective cũ thì proof có thể đúng về code nhưng sai về causal history.

Sau T1, mô hình đúng là:

```text
RUN initial objective
    = lịch sử ban đầu, không rewrite

WAVE effective objective
    = mục tiêu causal thực của attempt hiện tại

REPLAN làm đổi intent
    = objective revision mới

Proof / report / acceptance
    = phải gắn với effective wave objective
```

Điều này đã được kiểm chứng bằng một failure mode thật: wave có objective diagnose/no-mutation nhưng lại mutation source đã bị reject thay vì được accept “ké”.

Đó là behavior đúng của một evidence-governed execution system.

## 3.3. T2 TruthSnapshot đã làm đúng vai trò projection

TruthSnapshot được thiết kế theo nguyên tắc:

> **projection, not system**.

Nó không phải database mới, không phải authority mới, không có writer mới.

Nó chỉ compose các truth source hiện có để trả lời:

```text
source trên disk là gì?
runtime đang chạy byte/revision nào?
runtime phục vụ workspace nào?
package evidence có tồn tại không?
proof/acceptance nào hỗ trợ claim?
```

Các trạng thái comparison được giới hạn:

```text
MATCHED
MISMATCHED
UNKNOWN
NOT_APPLICABLE
```

Điểm mấu chốt là **missing evidence không bao giờ được chuyển thành green**.

## 3.4. T3 làm UI thành consumer, không phải truth authority

Operator Truth Console phải hiển thị:

```text
transport online
runtime/source match
workspace match
package truth
smart-v3 contract
process/server identity
run/wave/proof state
```

nhưng renderer không được tự suy luận lại truth từ các field rời rạc.

Đúng architecture:

```text
Canonical truth sources
        ↓
TruthSnapshot
        ↓
Operator UI
```

Không phải:

```text
UI tự đoán truth
```

## 3.5. C1 dừng ở 7 case là có chủ đích

Current casebook bao phủ bảy failure/invariant có ROI cao:

1. REPLAN đổi wave objective nhưng không rewrite run history.
2. Mismatch hoặc thiếu package evidence không được thành green.
3. `UNKNOWN` và `NOT_APPLICABLE` phải khác nhau.
4. Active run của task khác không được adopt.
5. Stale-run reconciliation phải bảo toàn live owner hợp lệ.
6. Final acceptance phải fail-closed và operator-visible.
7. Operator projection chỉ consume read-only TruthSnapshot.

Bản kế hoạch cũ từng liệt kê 13 scenario. Không có lý do khoa học để tạo thêm test trùng chỉ để “đủ 13”. Nếu invariant tương đương đã được specialized regression khác bảo vệ, duplication không làm proof mạnh hơn nhưng làm maintenance surface lớn hơn.

## 3.6. Stop condition của chương trình cũ đã đạt

Chương trình cũ nói rất rõ:

```text
T0 -> T1 -> T2 -> T3 -> C1 -> STOP/EVALUATE
```

Vì vậy tiếp tục xây Truth framework sau khi stop condition đạt sẽ vi phạm chính anti-overengineering doctrine của dự án.

Reopen chỉ khi có trigger mới:

- reproducible regression;
- trust boundary mới;
- source/runtime/package defect cụ thể;
- security/reliability issue;
- product requirement mà projection hiện tại không biểu diễn được.

---

# 4. THESIS SẢN PHẨM SAU KHI ĐÓNG TRUTH HARDENING

Coding Web không còn là một dự án đang cố trả lời:

> “Làm sao để ChatGPT gọi được tool trên máy?”

Hệ thống hiện đã có:

- ChatWeb/Sol semantic controller;
- final acceptance authority;
- một shared Runtime;
- one-writer/write-lease semantics;
- EOCL;
- durable proof/ledger;
- Recovery Host;
- compact `smart-v3`;
- deterministic execution/proof;
- context/result sparsification;
- source/runtime/workspace truth;
- solution-shadow economics;
- P5 experiment machinery;
- routing/placement gates.

Bài toán mới là:

> **Làm thế nào để Sol phải suy luận trên ít thông tin hơn nhưng thông tin đó giàu bằng chứng hơn; máy tính xử lý tối đa phần deterministic, Sol chỉ xử lý semantic uncertainty.**

Tôi gọi hướng này là **Execution Intelligence**.

Target architecture:

```text
                deterministic localization
                exact committed range
                exact guarded mutation
                execution lifecycle truth
                bounded stdout/stderr
                compiler/tests/proof
                evidence aggregation
                       |
User -> Sol semantic controller
                       |
                       v
              smallest causal repair
                       |
                       v
                     EOCL
                       |
                       v
                ACCEPTED RESULT
```

Vai trò Sol nên dịch chuyển từ:

> “shell operator thông minh”

sang:

> **semantic controller + architect + risk judge + final acceptor**.

Máy làm hash, diff, merge-base, classification, search, bounded output, test, compiler, execution state.

Sol làm root cause, architecture, semantic interaction, conflict resolution, trade-off và acceptance.

---

# 5. ACCEPTED-RESULT ECONOMICS VÀ LÝ DO CHỌN ĐÚNG CÁC WAVE NÀY

## 5.1. TTAR không chỉ là runtime latency

Một mô hình thực tế:

```text
TTAR = Time To Accepted Result

TTAR ≈ localization
     + reasoning
     + mutation
     + execution
     + verification
     + review
     + recovery
     + rework
     + final acceptance
```

Nếu tối ưu riêng một thành phần mà làm tăng repair/replan thì tổng TTAR có thể xấu hơn.

## 5.2. Expected Accepted Cost

```text
Expected Accepted Cost
  = model cost
  + tool/runtime cost
  + waiting cost
  + retry cost
  + rework cost
  + recovery cost
  + review cost
  + human intervention
```

Đây là lý do upstream #113 có thể rất đáng giá dù không giảm một token reasoning trực tiếp.

Nếu #113 loại bỏ một class deadlock/timeout/recovery:

```text
AI reasoning đúng
+ test chạy dài
+ output lớn
+ process vẫn terminalize đúng
```

thì hệ thống tránh được cả một chuỗi:

```text
timeout
-> uncertainty
-> retry
-> context reload
-> rerun
-> reproof
-> reacceptance
```

Tương tự, #90 không làm model “thông minh hơn”, nhưng nó giảm patch retry chỉ vì CRLF.

#116/#117 không làm model reasoning nhanh hơn theo tốc độ token, nhưng giảm lượng dữ liệu model phải đọc trước khi reasoning.

Đây là **accepted-result economics**, không phải micro-benchmark.

---

# 6. CHECKPOINT UPSTREAM HIỆN TẠI

Upstream:

```text
yyjeqhc/webcodex
```

Mốc upstream mới nhất đã quan sát trong nghiên cứu:

```text
8dd6b6ca24e29d5d8bdb08d5d29e665eb651aaa6
Add exact committed-range diff hunks (#117)
```

Các upstream delta được chọn:

| PR / capability | Commit upstream | Đánh giá local |
|---|---|---|
| #90 CRLF-aware guarded edits | `7a82fdd9a8f573300c67dbbcffd3912742d955d2` | gap thật, rất hợp Windows-first |
| #112 durable execution/lifecycle evidence | `ea97ca7d977c87bfc2566ec563655a3c8abcc240` | local có nhiều semantic tương đương; chỉ adapt phần thiếu |
| #113 continuous structured output drain | `2a77ba69be09eb4902b41939b619d18539a1bb8b` | gap robustness thật, ưu tiên cao |
| #116 deterministic committed review summary | `95fab7e5485b89e9dfbda351e9699519b28e627e` | local chưa có primitive tương đương |
| #117 exact committed-range diff hunks | `8dd6b6ca24e29d5d8bdb08d5d29e665eb651aaa6` | current local hunks chưa có exact base/head committed contract |
| #111 Managed OAuth | `085265f70c84772afb59ed537dbe3f21ea0280dd` | productization, chưa phải execution bottleneck |
| #114 local MCP gateway | `0187f97d33cfc0700c01f29d5c7741fae12e0bfa` | authority/context risk cao, chưa có consumer |
| #115 onboarding | `9d63542c7f19b95495e55330fb03f6e80bdf92a6` | học UX, không copy architecture |

Quy tắc:

> Upstream không phải roadmap owner. Upstream là nguồn primitive, invariant và test đã được người khác đầu tư xây dựng.

---

# 7. TAXONOMY R0–R5 VÀ CÁCH ÁP DỤNG

Giữ nguyên taxonomy đã chốt:

```text
R0 COPY
R1 COPY + ADAPTER
R2 SEMANTIC PORT
R3 REIMPLEMENT only with evidence
R4 DEFER
R5 REJECT / NOT APPLICABLE
```

## 7.1. Ý nghĩa thực tế

### R0 — COPY

Dùng khi local và upstream có cùng:

- language/runtime;
- authority boundary;
- dependency;
- failure semantics;
- API shape.

### R1 — COPY + ADAPTER

Dùng khi upstream algorithm tốt nhưng cần adapter nhỏ cho:

- local EOCL;
- principal attribution;
- Recovery lifecycle;
- tool surface;
- storage/identity contract.

### R2 — SEMANTIC PORT

Dùng khi không thể copy code nguyên nhưng có thể giữ:

- state machine;
- invariant;
- failure semantics;
- test cases;
- algorithm.

### R3 — REIMPLEMENT

Chỉ khi R0/R1/R2 không thể dùng. Phải có lý do rõ.

### R4 — DEFER

Feature có giá trị nhưng hiện chưa có consumer/prerequisite.

### R5 — REJECT

Feature xung đột authority architecture hoặc maintenance cost lớn hơn value.

## 7.2. Phân loại cụ thể

| Capability | Class | Quyết định |
|---|---:|---|
| #113 ContinuousPipeDrain | **R1/R2** | giữ algorithm/test, adapt vào local Runner |
| #112 lifecycle refinements | **R2** | port invariant, không copy whole architecture |
| #90 CRLF edit | **R1** | copy logic nhỏ, adapt local exact-edit API |
| #116 review summary | **R1/R2** | giữ deterministic map/bounds/trust controls |
| #117 committed hunks | **R1** | giữ exact SHA + isolated Git + continuation security |
| #111 OAuth | **R4** | defer |
| #114 MCP gateway | **R4/R5** | chưa dùng |
| #115 onboarding | **R2 concept-only** | chỉ học UX |
| Computer Use | **R4** | last-mile fallback |

Doctrine:

> **Reuse aggressively — integrate conservatively. Copy code/tests/invariants, không copy conflicting authority plane.**

---

# 8. NGUYÊN TẮC KIẾN TRÚC KHÓA CHẶT TRƯỚC WAVE MỚI

## 8.1. One Runtime authority

Không tạo thêm một peer Runtime có khả năng mutation cùng canonical workspace.

## 8.2. One writer

Mọi source mutation phải thông qua một write lease hợp lệ.

## 8.3. EOCL giữ quyền mutation/proof/acceptance

Upstream primitive không được tự trở thành orchestration authority.

## 8.4. Recovery Host giữ lifecycle authority

Không port một upstream supervisor để tạo peer lifecycle owner.

## 8.5. `smart-v3 = 8`

Không thêm public tool chỉ vì upstream thêm tool mới.

## 8.6. Deterministic-first

Nếu merge-base, diff, test, compiler, path classification hoặc exact source identity có thể tính bằng máy thì không dùng Sol token để tự suy ra lại.

## 8.7. Source/proof/live/package/release tách biệt

Một change accepted ở EOCL không đồng nghĩa package hiện tại đã chứa change.

---

# 9. GATE 0 — P5 / SOURCE IDENTITY SAFETY TRƯỚC MỌI CODE-BEARING WAVE

Gate 0 phải được chạy trước A/B/C.

## 9.1. Tại sao cần Gate 0

P5 là experiment framework gắn với exact source/runtime/analyzer identity.

Nếu đang có một epoch thu mẫu và ta thay execution substrate giữa chừng:

```text
cohort đầu chạy substrate cũ
cohort sau chạy substrate mới
```

thì kết quả rework/TTAR không còn comparable.

Một improvement infrastructure có thể bị nhầm là treatment effect hoặc ngược lại.

## 9.2. Quy trình

```text
READ canonical P5 state
        |
        +-- không có active/open epoch bị ảnh hưởng
        |       -> PROCEED
        |
        +-- có active/open epoch
                -> pause/close/rebaseline đúng contract
                -> giữ nguyên outcome đã thu
                -> source-bearing change chỉ bắt đầu sau boundary rõ
```

## 9.3. Quy tắc

1. Không đọc epoch state từ research doc cũ.
2. Không trộn execution substrate trong một cohort.
3. Evidence-only `.coding-tools/**` commit không tự động là source drift nếu canonical source identity loại nó.
4. Code-bearing commit phải đi qua current P5 identity contract.
5. Automatic treatment/promotion luôn OFF nếu chưa được explicit gate.
6. Nếu connector schema stale, không được “coi như” action P5 đã xảy ra.

Gate 0 chỉ là safety precondition, không được biến thành một phase framework mới.

---

# 10. WAVE A — EXECUTION TRUTH & LONG-RUN ROBUSTNESS

Wave A giải quyết lớp thấp nhất nhưng có ảnh hưởng lớn nhất đến autonomy:

> Hệ thống phải biết chính xác command có start chưa, có thể đã gây side effect chưa, còn chạy không, terminal thế nào, retry có an toàn không và output có thể làm process tự block không.

---

# 11. WAVE A1 — UPSTREAM #113 CONTINUOUS OUTPUT DRAIN

## 11.1. Vấn đề

Một child process có `stdout`/`stderr` qua OS pipe.

Pipe có capacity hữu hạn. Nếu parent không drain liên tục:

```text
child write nhiều
-> pipe đầy
-> child block tại write()
-> process không tiến
-> timeout/recovery
-> controller tưởng command chậm/treo
```

Điểm quan trọng của upstream #113 là **thời điểm drain**.

Không phải đợi khi model gọi log/read mới đọc.

Phải drain ngay sau `spawn`.

## 11.2. Kiến trúc đích

```text
spawn child
  |
  +--> stdout reader chạy ngay
  |
  +--> stderr reader chạy ngay
  |
  +--> bounded tail retention
  |
  +--> observer/model có thể đọc hoặc không đọc
  |
  +--> process progress không phụ thuộc observer
  |
  +--> terminal/stop/timeout/shutdown
```

## 11.3. Vì sao bounded tail vẫn cần

Continuous drain không được biến thành unbounded memory log buffer.

Phải giữ:

```text
max_output_bytes
truncation marker
UTF-8-safe tail
stdout/stderr tách biệt
```

Output cũ có thể được discard theo policy, nhưng process vẫn phải được drain.

## 11.4. Failure mode cần loại bỏ

### F1 — Model không poll log

Process vẫn phải complete.

### F2 — Output quá lớn

Không được deadlock.

### F3 — Stop sau khi output lớn

Không được redispatch.

### F4 — Timeout sau output lớn

Terminal state phải là timeout của chính execution đó.

### F5 — Runtime shutdown

Phải reap đúng child đã spawn, không tạo orphan.

## 11.5. Invariant

- no unbounded buffering;
- no output-driven deadlock;
- drain stdout/stderr độc lập;
- progress không phụ thuộc model observation;
- bounded tail đúng policy;
- terminal exact-once;
- no redispatch;
- không tạo public tool mới;
- không đổi EOCL authority.

## 11.6. Oracle tối thiểu

1. Large stdout + stderr, không consume log -> complete đúng 1 lần.
2. Large output -> stop -> terminal stopped, bounded tail, start count = 1.
3. Large output -> timeout -> timed out, start count = 1.
4. Large output -> shutdown -> same execution được reap.
5. Tail không vượt output_limit.
6. UTF-8/truncation semantics giữ đúng.
7. Small normal output không regression.

## 11.7. Tác động kinh tế kỳ vọng

#113 không nhất thiết giảm token trực tiếp.

Nó giảm:

- duplicate command;
- timeout recovery;
- context reload;
- rerun proof;
- human debugging;
- false infrastructure failure;
- contaminated P4/P5 data.

---

# 12. WAVE A2 — CHỈ LẤY LIFECYCLE INVARIANT CÒN THIẾU TỪ #112

Local đã có vocabulary:

```text
NotStarted
OutcomeUnknown
Completed
TimedOut
command_execution_state
state_changed
```

Vì vậy không port #112 wholesale.

## 12.1. Invariant quan trọng nhất

```text
BEFORE successful spawn
  -> NotStarted có thể đúng

AFTER successful spawn
  -> không được quay lại NotStarted
  -> nếu chưa có terminal truth thì OutcomeUnknown

OBSERVED terminal exit
  -> Completed / TimedOut theo contract
```

## 12.2. Vì sao `NotStarted` và `OutcomeUnknown` khác nhau sống còn

`NotStarted` hàm ý:

> command chưa effect, retry có thể an toàn.

`OutcomeUnknown` hàm ý:

> command đã có thể chạy và gây side effect; retry mù có thể duplicate mutation.

Ví dụ:

```text
AI yêu cầu migration command
spawn thành công
connection bị mất
```

Nếu trả `NotStarted` sai:

```text
controller retry
-> migration có thể chạy hai lần
```

Nếu trả `OutcomeUnknown`:

```text
controller phải investigate/reconcile
```

Đây là autonomy safety, không chỉ status UX.

## 12.3. Oracle

- pre-spawn validation failure -> NotStarted;
- post-spawn interruption -> không NotStarted;
- lost terminal truth -> OutcomeUnknown;
- observed nonzero exit -> completed-with-failure semantics, không “never started”;
- retry-safe projection không được reuse stale pre-spawn state sau successful spawn.

## 12.4. Quan hệ với EOCL

```text
accurate low-level execution state
        ↓
accurate retry semantics
        ↓
accurate proof lineage
        ↓
accurate EOCL REPLAN/acceptance
        ↓
safe autonomous recovery
```

EOCL ở tầng cao chỉ đáng tin nếu execution truth ở tầng thấp đúng.

---

# 13. EXIT GATE WAVE A

Wave A chỉ accepted khi:

```text
[ ] verbose job không phụ thuộc model log observation
[ ] bounded output
[ ] stop exact-once
[ ] timeout exact-once
[ ] shutdown exact-once
[ ] pre-spawn NotStarted đúng
[ ] post-spawn uncertainty không bao giờ trở về NotStarted
[ ] OutcomeUnknown propagates fail-closed
[ ] job/process projection tương thích
[ ] no orphan/duplicate execution
[ ] smart-v3 vẫn = 8
[ ] EOCL/Recovery authority không đổi
```

Wave A phải có checkpoint riêng trước Wave B.

Không bundle A+B+C thành một giant wave vì khi có regression sẽ không biết mechanism nào chịu trách nhiệm.

---

# 14. WAVE B — WINDOWS MUTATION RELIABILITY / UPSTREAM #90

## 14.1. Bài toán thực tế

Model thường sinh string với LF:

```text
foo\nbar
```

Trong khi file Windows có thể là:

```text
foo\r\nbar
```

Semantic text giống nhau, byte-level newline khác.

Nếu guarded edit chỉ exact-match raw bytes:

```text
model patch đúng semantic
-> match not found
-> reread
-> repatch
-> retry
```

Hoặc tệ hơn:

```text
rewrite whole file
-> CRLF thành LF toàn file
-> huge diff
-> review noise
```

## 14.2. Mục tiêu

Giữ exact guarded edit, nhưng line-ending-aware.

Không fuzzy matching.

## 14.3. Semantics cần giữ

```text
LF file
  -> hành vi hiện tại giữ nguyên

CRLF file
  -> canonicalize line ending CHỈ để match
  -> apply exact semantic edit
  -> restore CRLF convention

mixed line endings
  -> reject fail-closed

bare CR
  -> reject fail-closed
```

## 14.4. Điều không được làm

- Không trim whitespace tùy tiện.
- Không fuzzy search.
- Không approximate context.
- Không normalize cả file chỉ vì patch input dùng LF.
- Không làm yếu hash/conflict guard.
- Không biến `state_changed=false` thành true khi conflict.

## 14.5. Protected invariants

- exact semantic text vẫn exact;
- file encoding policy giữ nguyên;
- batch atomicity giữ nguyên;
- hash guard giữ nguyên;
- CRLF original được preserve;
- mixed line ending không tự repair âm thầm;
- Git diff chỉ chứa intended change.

## 14.6. Oracle

```text
1. LF + LF edit -> PASS, file vẫn LF
2. CRLF + LF-shaped edit -> PASS, file vẫn CRLF
3. CRLF + CRLF edit -> PASS
4. mixed LF/CRLF -> deterministic reject
5. bare CR -> deterministic reject
6. hash mismatch -> conflict + state_changed=false
7. batch edit -> atomic
8. git diff -> không line-ending churn ngoài intended lines
```

## 14.7. Tác động accepted-result

```text
first-pass patch success ↑
patch retry ↓
full-file rewrite ↓
diff noise ↓
review bytes ↓
repair/replan ↓
TTAR ↓
```

Wave B đặc biệt có ROI vì Coding Web là Windows-first.

---

# 15. WAVE C — DETERMINISTIC COMMITTED-REVIEW INTELLIGENCE

Wave C là phần có tiềm năng giảm token/context mạnh nhất, nhưng phải triển khai đúng architecture.

## 15.1. Cách review hiện nay thường tốn context

Một yêu cầu:

> “Kiểm tra commit vừa sửa có vấn đề gì không.”

có thể dẫn đến:

```text
git status
-> git log
-> git diff
-> diff lớn
-> search
-> read file
-> read caller
-> read tests
-> model tự phân loại
```

LLM đang dùng token để làm việc mà Git/parser có thể làm deterministic.

## 15.2. Kiến trúc đích

```text
BASE SHA + HEAD SHA
        ↓
validate exact committed range
        ↓
merge-base
        ↓
review summary deterministic
        +
exact bounded hunks
        ↓
small evidence packet
        ↓
Sol semantic review
        ↓
proof
        ↓
EOCL accept/reject
```

Đây không chỉ là “compression”.

Nó là **pre-model deterministic localization**.

---

# 16. CONSTRAINT QUAN TRỌNG NHẤT CỦA WAVE C: KHÔNG CÓ TOOL THỨ 9

Upstream có thể expose tool primitive riêng.

Nhưng product contract hiện tại của Coding Web là:

```text
smart-v3 = exactly 8 public tools
```

Vì vậy hướng đúng:

```text
agent_workflow
      ↓
internal deterministic review primitives
      ↓
bounded packet
      ↓
Sol
```

Không phải:

```text
add git_review_summary public tool
add committed_diff public tool
add review_selector public tool
...
```

Một trong các thành tựu lớn của dự án là giảm tool/context bloat. Không được tự phá nó chỉ để “bắt kịp upstream”.

---

# 17. WAVE C0 — SHARED EXACT COMMITTED GIT SCOPE

#116 và #117 có hai consumer thật, nên một helper nhỏ dùng chung là hợp lý.

Không cần framework.

## 17.1. Contract

Input:

```text
base_commit
head_commit
```

Yêu cầu:

- exact 40-hex SHA;
- object tồn tại local;
- object type là commit;
- không implicit fetch;
- merge-base deterministic;
- missing/ambiguous merge-base fail closed;
- effective range = merge-base..head;
- dirty worktree không làm đổi committed result.

## 17.2. Vì sao exact SHA quan trọng

Không dùng:

```text
HEAD~2
main
origin/main
feature/foo
```

cho evidence contract nếu mục tiêu là reproducible review.

Ref mutable có thể dịch chuyển giữa hai call.

Exact SHA tạo stable evidence identity.

## 17.3. Vì sao merge-base

Nếu base không ancestor trực tiếp của head, diff `base..head` có thể không phản ánh branch changes theo intended review semantics.

Merge-base giúp tạo:

```text
common ancestor -> head
```

và report rõ requested base có ancestor hay không.

---

# 18. WAVE C1 — #117 EXACT COMMITTED-RANGE `git_diff_hunks`

## 18.1. Gap local

Current local `git_diff_hunks` có:

```text
paths
max_hunks
max_hunk_lines
cached
```

Nó tốt cho worktree/staged review.

Nhưng chưa có exact committed:

```text
base_commit
head_commit
continuation
```

## 18.2. Trust controls phải giữ từ upstream

### Exact object identity

Không abbreviated SHA cho evidence-grade range.

### `--no-ext-diff`

Không cho Git gọi external executable để render diff.

### `--no-textconv`

Không cho custom text conversion thay đổi evidence.

### Isolated Git attribute view

Dirty/mutable `.gitattributes` ở worktree không được làm thay đổi cách đọc committed evidence.

### No lazy fetch

Review không được tự network-fetch object rồi biến read-only inspection thành network side effect.

### Secret path suppression

Một deterministic review tool không được trở thành đường vô tình leak secret-like file.

### Bounded output

Không trả diff vô hạn.

### Continuation integrity

Continuation phải bị bind vào:

```text
base SHA
head SHA
paths
limits/mode
scope version
```

và có integrity protection phù hợp.

Continuation của committed scope không được dùng cho worktree scope và ngược lại.

## 18.3. Oracle

- cùng base/head -> same evidence dù dirty worktree thay đổi;
- invalid SHA -> reject;
- ref expression -> reject;
- missing merge-base -> fail closed;
- external diff/textconv không tác động;
- mutable attributes không tác động;
- continuation tamper -> reject;
- cross-scope continuation -> reject;
- sensitive path không leak;
- existing worktree/cached mode không regression.

---

# 19. WAVE C2 — #116 DETERMINISTIC `git_review_summary`

## 19.1. Mục tiêu

`git_review_summary` không phải AI review.

Contract phải thể hiện:

```text
deterministic = true
llm_summary = false
```

Nó là một **evidence map** giúp quyết định phần nào đáng đưa cho Sol.

## 19.2. Output nên chứa

- requested base/head;
- effective merge-base;
- commit count;
- changed file count;
- line/stat aggregates;
- binary file signals;
- subsystem/path classes;
- risk/attention signals;
- symbol/function hints có bound;
- production/test/docs coverage observations;
- truncation/partiality metadata;
- warnings.

## 19.3. Risk surface classification

Ví dụ deterministic classifier có thể đánh dấu:

```text
auth/scope
protocol/wire schema
tool contract
runtime config
persistence/migration
execution lifecycle
CLI/HTTP/public interface
```

Nhưng signal chỉ có nghĩa:

> “đây là vùng cần attention”.

Không được suy ra:

> “có bug”.

## 19.4. Symbol hints

Mục tiêu không phải parser perfect.

Chỉ cần bounded hints giúp Sol localize:

```text
file X
function Y
struct Z
public handler Q
```

Nếu parser không chắc, phải report uncertainty, không fabricate symbol.

---

# 20. WAVE C3 — TÍCH HỢP VÀO `agent_workflow`

Giá trị của #116/#117 chỉ xuất hiện khi workflow thực sự dùng chúng để giảm model-visible context.

## 20.1. Flow đề nghị

```text
agent_workflow
  ↓
exact committed scope
  ↓
git_review_summary
  ↓
select high-value paths/symbols
  ↓
committed git_diff_hunks
  ↓
bounded evidence packet
  ↓
Sol semantic review
  ↓
deterministic proof
  ↓
EOCL acceptance
```

## 20.2. Không chạy cho mọi task

Chỉ dùng khi:

- review một committed implementation range;
- audit một branch/PR-like range đã có local object;
- cần chọn risk-focused review targets;
- cần integration-width evidence cho future routing economics.

Dirty worktree review vẫn dùng current worktree diff/show changes path.

## 20.3. Context economics

Phân biệt:

### Output sparsification

```text
100 KB
-> compress còn 70 KB
```

### Deterministic localization

```text
100 KB potential source
-> machine chọn 12 KB relevant
-> model chỉ nhận 12 KB
```

Cách thứ hai có leverage lớn hơn.

---

# 21. EXIT GATE WAVE C

```text
[ ] exact 40-hex commit contract
[ ] commit object validation
[ ] deterministic merge-base
[ ] dirty worktree không ảnh hưởng committed result
[ ] no lazy fetch
[ ] no ext-diff
[ ] no textconv
[ ] committed attributes isolated
[ ] output bounded/truncation explicit
[ ] sensitive paths protected
[ ] continuation scope-bound
[ ] continuation integrity-protected
[ ] worktree review compatibility giữ nguyên
[ ] review summary deterministic, không giả LLM review
[ ] agent_workflow chỉ feed bounded selected evidence
[ ] smart-v3 vẫn = 8
[ ] không thêm authority mới
```

---

# 22. WAVE D — ACCEPTED-RESULT ECONOMICS REBASELINE

Wave D không viết thêm feature.

Nó trả lời:

> A/B/C có thực sự giúp hệ thống hay chỉ làm code phức tạp hơn?

## 22.1. Metrics ưu tiên

### Outcome

- first-pass accepted rate;
- repaired/replan rate;
- critical defect;
- manual fix.

### Time

- TTAR p50/p90;
- proof time;
- waiting/recovery time khi quan sát được.

### Infrastructure

- stuck/timeout incidence;
- output-related failure;
- orphan/duplicate execution;
- patch retry.

### Context/review

- candidate source bytes;
- model-visible review bytes;
- tool hops trước semantic review;
- review invocation rate.

### Cost

Token/money chỉ ghi khi measured/provider-reported.

Unknown vẫn là unknown.

## 22.2. Không overclaim causality

Một before/after nhỏ với workload khác nhau không đủ để nói:

> “#116 làm TTAR giảm X%”.

Wave D trước hết là:

- mechanism validation;
- instrumentation validation;
- descriptive economics;
- input cho later representative study.

Policy promotion vẫn chịu P4/P5/P7 gate.

## 22.3. Stop condition

Sau A+B+C accepted và D có evaluation đủ bounded:

```text
STOP
```

Không tự động chuyển sang OAuth, MCP Gateway hay Computer Use.

Feature tranche tiếp theo cần trigger mới.

---

# 23. QUAN HỆ VỚI P4

P4 đang cố học:

> Những signal nào trước mutation dự báo repair/rework?

Nếu infrastructure gây lỗi ngẫu nhiên:

- pipe deadlock;
- timeout giả;
- patch CRLF fail;
- review localization quá rộng;

thì outcome repair bị nhiễu.

A/B/C làm data P4 sạch hơn bằng cách giảm infrastructure-induced repair.

Không có nghĩa A/B/C tự động là P4 treatment.

---

# 24. QUAN HỆ VỚI P5

P5 là prospective experiment, source-bound.

A/B/C thay substrate nên phải đi qua Gate 0.

Sau A/B/C, nếu mở epoch mới:

```text
old substrate cohort
```

phải tách khỏi:

```text
new substrate cohort
```

Không backfill hoặc reinterpret old outcomes.

Automatic activation vẫn OFF.

---

# 25. QUAN HỆ VỚI P7 ROUTING ECONOMICS

#116 có thể tạo deterministic routing features như:

```text
integration_width
risk_surfaces
changed_subsystems
symbol_count
protocol_touch
persistence_touch
auth_touch
test_coverage
```

Đây là signal tốt hơn prompt impression.

Ví dụ prompt nói:

> “fix login nhỏ”.

Nhưng summary cho thấy:

```text
auth + protocol + storage + migration
```

thì task không còn nhỏ.

Ngược lại prompt nghe lớn nhưng diff chỉ 1 symbol + strong oracle thì có thể bounded.

Tuy nhiên:

> deterministic review signal chỉ là input candidate cho P7, không tự cấp routing authority.

---

# 26. QUAN HỆ VỚI P8 ACCEPTED-COST OPTIMIZER

P8 cần các thành phần đáng tin:

```text
Expected Accepted Cost
 = localization_cost
 + model_reasoning_cost
 + mutation_cost
 + execution_cost
 + proof_cost
 + expected_repair_cost
 + failure/recovery_cost
 + review_cost
```

A/B/C làm deterministic substrate sạch hơn.

Nếu execution truth sai hoặc review bytes nhiễu, P8 sẽ tối ưu noise.

Vì vậy A/B/C là infrastructure-quality prerequisite, không phải shortcut tới optimizer.

---

# 27. CÁC UPSTREAM FEATURE KHÔNG PORT BÂY GIỜ

## 27.1. #111 Managed OAuth

**R4 DEFER**.

Chỉ mở khi có nhu cầu:

- hosted multi-user;
- organization identity;
- revoke/rotation nhiều device;
- external hosted server;
- user lifecycle mà Electron SecretStore hiện tại không giải được.

OAuth không trực tiếp cải thiện:

- first-pass acceptance;
- repair;
- TTAR;
- proof quality.

## 27.2. #114 Local MCP Gateway

**R4/R5 hiện tại**.

Lợi ích dài hạn có thể là capability bus, nhưng port bây giờ có nguy cơ:

```text
provider explosion
+ tool/schema explosion
+ credential audience mới
+ authority ambiguity
+ context bloat
```

Nếu sau này có consumer thật, architecture nên là:

```text
providers
  ↓
capability registry
  ↓
deterministic selection
  ↓
agent_workflow
  ↓
chỉ inject schema cần thiết
```

Không expose toàn bộ MCP provider tool cho model mặc định.

## 27.3. #115 Onboarding

Chỉ học:

- one-click first connection;
- readiness rõ;
- credential instruction đơn giản;
- setup error actionable.

Không copy Unix/share architecture vì product local là Windows/Electron-first.

## 27.4. Computer Use

Ưu tiên execution interface:

```text
Structured API
> CLI
> file/Git primitive
> GUI automation
```

Computer Use chỉ khi ba tầng trên không tồn tại.

---

# 28. THỨ TỰ TRIỂN KHAI CUỐI CÙNG

```text
GATE 0
P5/source identity safety
        ↓
WAVE A1
#113 continuous drain
        ↓
WAVE A2
missing #112 lifecycle invariants
        ↓
CHECKPOINT A
        ↓
WAVE B
#90 CRLF-aware exact editing
        ↓
CHECKPOINT B
        ↓
WAVE C0
shared exact committed range
        ↓
WAVE C1
#117 committed hunks
        ↓
WAVE C2
#116 review summary
        ↓
WAVE C3
agent_workflow integration
        ↓
CHECKPOINT C
        ↓
WAVE D
accepted-result economics
        ↓
STOP / EVALUATE
```

## 28.1. Vì sao A trước B

Execution truth ảnh hưởng toàn bộ proof/retry/autonomy.

## 28.2. Vì sao B trước C

Review intelligence không giúp nhiều nếu mutation vẫn fail vô lý do CRLF.

## 28.3. Vì sao C sau substrate

Deterministic intelligence nên đứng trên một execution/mutation substrate đáng tin.

## 28.4. Vì sao D cuối

Phải đo economics sau khi substrate đã ổn định.

---

# 29. EOCL DELIVERY CONTRACT CHO MỖI MATERIAL WAVE

Mỗi A/B/C phải là một normal EOCL lineage.

Trước mutation phải chốt:

```text
OBJECTIVE
DONE
NON-GOALS
PROTECTED INVARIANTS
BASE HEAD
WORKTREE IDENTITY
UPSTREAM COMMIT
R0-R5 CLASS
CHEAPEST SUFFICIENT ORACLE
```

Execution discipline:

1. PREPARE/localize current source.
2. Bind effective objective.
3. Acquire write lease.
4. Implement smallest coherent causal delta.
5. Focused proof.
6. Affected-boundary proof nếu cần.
7. Inspect diff + one credible adjacent risk.
8. `ACCEPTING`.
9. ChatWeb/Sol accept/reject.
10. CHECKPOINT rồi mới delivery.

Failure rules:

- không unchanged retry;
- REPLAN phải có changed evidence/scope/strategy;
- không reuse stale proof khi fingerprint drift;
- không silent owner transfer;
- không mở wave implementation mới khi wave cũ còn `ACCEPTING`;
- completion report phải operator-visible.

---

# 30. GIT / DELIVERY POLICY

Khi triển khai source sau này:

1. Preserve concurrent work.
2. Không reset/rebase/clean workstream khác.
3. Commit `.coding-tools/**` history theo repo policy.
4. Exclude duy nhất:
   - `.coding-tools/orchestration/ledger.sqlite3-shm`
   - `.coding-tools/orchestration/ledger.sqlite3-wal`
5. Heavy generated Excel test artifacts để local.
6. Chạy `check:coding-tools-history` / delivery guard trước push.
7. Phân biệt source commit và evidence-only commit.
8. Verify `HEAD == origin/main` sau push khi delivery yêu cầu.
9. Không package/release claim nếu chưa có package/release proof.

---

# 31. UPSTREAM PROVENANCE — REGISTRY-ON-TOUCH

A/B/C tạo ra real upstream maintenance trigger.

Nhưng không cần full CMDB.

Mỗi capability khi được port lần đầu chỉ cần record:

```text
capability_id
reuse_mode
upstream repo
exact upstream commit/PR
upstream source paths
local destination paths
authority delta
protected tests
semantic delta
accepted run/wave/fingerprint
last reviewed date
```

Nếu comments/docs/test reference hiện tại đủ để bảo tồn provenance, chưa cần tạo registry file mới.

Chỉ tạo machine-readable registry khi xuất hiện consumer thứ hai thật sự.

---

# 32. RISK REGISTER

| Mã | Rủi ro | Cơ chế hỏng | Kiểm soát |
|---|---|---|---|
| A-R1 | continuous drain unbounded | memory tăng vô hạn | bounded tail + stress test |
| A-R2 | post-spawn trả `NotStarted` | unsafe retry | lifecycle regression + OutcomeUnknown |
| A-R3 | stop/timeout duplicate | command effect hai lần | exact-once marker + execution ID |
| A-R4 | drain thread leak | orphan process/thread | shutdown/reap tests |
| B-R1 | CRLF support thành fuzzy | sai target mutation | normalize newline only |
| B-R2 | whole-file newline churn | huge diff | restore original convention |
| B-R3 | mixed ending bị đoán | silent corruption | fail closed |
| C-R1 | committed review bị dirty worktree ảnh hưởng | evidence không reproducible | isolated committed view |
| C-R2 | ext diff/textconv chạy code | unexpected side effect | disable both |
| C-R3 | mutable attributes thay evidence | review drift | committed attribute context |
| C-R4 | continuation replay/tamper | wrong-range evidence | scope bind + integrity |
| C-R5 | secret path leak | data exposure | sensitive-path suppression |
| C-R6 | public tool surface phình | context/orchestration bloat | keep smart-v3 = 8 |
| P5-R1 | mixed source epoch | invalid experiment | Gate 0 |
| GOV-R1 | upstream parity thành backlog vô hạn | feature accumulation | STOP after D |
| GOV-R2 | stale doc reopen T0–C1 | overengineering | supersession rule |

---

# 33. ACCEPTANCE SCORECARD

## 33.1. Wave A

```text
[ ] large output không block process
[ ] output bounded
[ ] no-log-consumer still completes
[ ] stop exact-once
[ ] timeout exact-once
[ ] shutdown exact-once
[ ] pre-spawn NotStarted đúng
[ ] post-spawn uncertainty != NotStarted
[ ] OutcomeUnknown fail-closed
[ ] no orphan
[ ] no duplicate execution
[ ] smart-v3 = 8
```

## 33.2. Wave B

```text
[ ] LF preserved
[ ] CRLF preserved
[ ] LF model text match CRLF semantic source
[ ] mixed endings reject
[ ] bare CR reject
[ ] hash conflict unchanged
[ ] batch atomicity unchanged
[ ] no line-ending diff noise
```

## 33.3. Wave C

```text
[ ] exact commit IDs
[ ] commit object validation
[ ] deterministic merge-base
[ ] dirty worktree independent
[ ] no lazy fetch
[ ] no ext-diff/textconv
[ ] attribute isolation
[ ] bounded output
[ ] sensitive path protection
[ ] continuation scope-bound
[ ] continuation integrity
[ ] worktree diff compatibility
[ ] review summary deterministic
[ ] bounded model packet
[ ] smart-v3 = 8
```

## 33.4. Wave D

```text
[ ] measurement provenance explicit
[ ] unknown != 0
[ ] infra failure tách solution failure khi có thể
[ ] repair/replan/TTAR reported
[ ] context/tool-hop reported
[ ] không overclaim causality
[ ] không auto-promote policy
[ ] STOP decision recorded
```

---

# 34. DECISION CARD CHO MỌI UPSTREAM FEATURE SAU NÀY

```text
1. Có defect/consumer/security delta thật không?
   NO -> DEFER

2. Local đã có equivalent behavior chưa?
   YES -> delta audit only

3. Copy được upstream + thin adapter không?
   YES -> R0/R1

4. Chỉ invariant/algorithm dùng được?
   YES -> R2

5. Có tạo peer authority/credential/runtime target không?
   YES -> explicit trust analysis hoặc R5

6. Có làm phình model-facing tool/context không?
   YES -> internal aggregation trước

7. Deterministic evidence trả lời được không?
   YES -> không dùng model để suy ra lại

8. P5 epoch có source-bound không?
   YES -> Gate 0 trước mutation

9. DONE + proof đã pass chưa?
   YES -> STOP

10. Lý do duy nhất là upstream có feature mới?
   YES -> KHÔNG LÀM
```

---

# 35. CÁCH HIỂU ROADMAP P0–P9 SAU TÀI LIỆU NÀY

```text
P0-P3 engineering
  = CLOSED, không reopen theo cảm tính

P3 representative efficacy
  = parallel evidence only

P4 solution economics
  = collecting, không thêm framework mặc định

P5 experiment integrity
  = implemented, epoch/source fail-closed

NEXT BOUNDED HARDENING
  = A execution truth
  = B mutation reliability
  = C deterministic review intelligence
  = D economics rebaseline

P7 routing economics
  = later, evidence-gated

P8 accepted-cost optimizer
  = deferred đến khi input validated

P9 capacity scaling
  = chỉ khi telemetry chứng minh active bottleneck
```

A/B/C là một bounded hardening tranche, không phải một phase ontology mới.

---

# 36. QUY TẮC GIỮ LỊCH SỬ CÁC FILE NGÀY 21/08

```text
260821_TRUTH_RECONCILIATION_CHECKPOINT.md
  -> historical T0/T1 checkpoint

260821_CODING_WEB_LEAN_CONTROL_RICH_EVIDENCE_ACCEPTED_RESULT_SYNTHESIS.md
  -> doctrine: Lean Control + Rich Evidence + Rework-First Economics

260821_CODING_WEB_MASTER_ENGINEERING_STRATEGY_AND_HISTORY.md
  -> historical strategy/governance/ledger + R0-R5

260822_CODING_WEB_EXECUTION_INTELLIGENCE_UPSTREAM_ADOPTION_AND_NEXT_IMPLEMENTATION_MASTER_PLAN.md
  -> kế hoạch bounded tiếp theo
```

Không rewrite file lịch sử để làm như nó đã biết trước trạng thái tương lai.

Chronology có giá trị forensic.

---

# 37. HÀNH ĐỘNG KỸ THUẬT TIẾP THEO KHI BẮT ĐẦU TRIỂN KHAI

Không phải “port tất cả upstream”.

Đúng trình tự:

```text
1. Đọc canonical live P5 state.
2. Reconcile source identity / active epoch.
3. Mở EOCL lineage cho Wave A.
4. Pin upstream #113 và #112 exact commits.
5. Localize current Runner/job implementation.
6. Port ContinuousPipeDrain.
7. Port chỉ missing post-spawn lifecycle invariants.
8. Focused stress/exact-once/lifecycle proof.
9. Affected-boundary proof.
10. Final acceptance Wave A.
11. CHECKPOINT.
12. Sau đó mới Wave B.
```

Điểm quan trọng nhất:

> **A, B, C không được bundle thành một giant wave.**

Mỗi wave có cơ chế nhân quả khác nhau và oracle khác nhau. Separate fingerprint giúp regression attribution và economics về sau sạch hơn.

---

# 38. TẠI SAO KHÔNG MERGE UPSTREAM WHOLESALE

Codex-web hiện không còn là một fork WebCodex “thấp hơn version”.

Nó đã phát triển theo một trục riêng:

```text
Electron Execution Hub
Recovery Host
Coding Tools MCP smart-v3
EOCL
proof/evidence ledger
Codex Desktop proxy
provider lanes
P4/P5 evaluation
accepted-result economics
```

Trong khi upstream phát triển WebCodex product primitives.

Do đó “upstream newer” không đồng nghĩa “local thiếu”.

Correct rule:

```text
upstream delta
   ↓
semantic comparison
   ↓
existing local equivalent?
   ↓
R0/R1/R2/R4/R5
   ↓
smallest causal adoption
```

Không phải:

```text
git upstream newer
-> merge all
```

---

# 39. TRIẾT LÝ KỸ THUẬT RÚT RA TỪ UPSTREAM LẦN NÀY

Điểm có giá trị nhất không phải 5 feature cụ thể.

Mà là một nguyên tắc:

> **Đẩy càng nhiều phần có thể chứng minh khỏi LLM sang deterministic substrate.**

Thay vì:

```text
Sol
 ↓
search/diff/read/classify/test manually
 ↓
reason
```

mục tiêu:

```text
deterministic substrate
  - localization
  - exact range
  - exact edit
  - lifecycle truth
  - execution state
  - test/compiler
  - diff classification
        ↓
small evidence packet
        ↓
Sol semantic reasoning
        ↓
EOCL acceptance
```

Đây là cách vừa tăng reliability vừa giảm token/context.

---

# 40. DOCTRINE DÀI HẠN SAU KHI HỢP NHẤT

## D1 — Accepted result over activity

Không đo thành công bằng số tool call hoặc số feature.

## D2 — One authority, many projections

Nhiều read-only view được phép; writer/authority chỉ một.

## D3 — Unknown is not zero

Không quan sát được thì để unknown.

## D4 — Source/proof/live/package/release tách biệt

Không collapse claim plane.

## D5 — Deterministic before model

Máy trả lời được thì không dùng model debate.

## D6 — Single-lane default

Parallelism chỉ khi earn coordination cost.

## D7 — Adaptive compute

Không Max-only.

## D8 — Upstream-first reuse

Copy invariant/test trước khi tự viết lại.

## D9 — Exact execution truth

Retry safety phụ thuộc việc biết điều gì thực sự đã xảy ra.

## D10 — Exact mutation

Smallest causal patch phải apply được lần đầu, không tạo diff noise.

## D11 — Deterministic localization

Đừng nén dữ liệu dư; đừng gửi dữ liệu dư cho model từ đầu.

## D12 — Stop when DONE

Sau A/B/C/D phải STOP, trừ khi trigger mới xuất hiện.

---

# 41. KẾT LUẬN CUỐI CÙNG

Coding Web đã đi qua một giai đoạn rất quan trọng: từ việc xây authority, orchestration, recovery và evidence framework sang giai đoạn phải chứng minh **giá trị biên** của từng thay đổi tiếp theo.

T0–T3–C1 đã làm xong nhiệm vụ làm sạch “truth và traceability”. Tiếp tục mở rộng nó thành một platform lớn sẽ làm dự án quay lại đúng failure mode đã nhiều lần gặp: thêm state, thêm surface, thêm reconciliation và thêm context nhưng không làm accepted result tốt hơn tương ứng.

Upstream WebCodex ngày 21–22/08 cung cấp một nhóm primitive có giá trị đặc biệt vì chúng nằm đúng critical path của một coding turn:

```text
#113
  -> command không bị output làm block

#112 refinements
  -> biết chính xác retry có an toàn không

#90
  -> patch Windows apply đúng ngay lần đầu

#117
  -> exact committed evidence

#116
  -> deterministic map để chỉ đọc phần đáng review
```

Khi kết hợp đúng:

```text
EXECUTION TRUTH
    ↓
EXACT MUTATION
    ↓
DETERMINISTIC EVIDENCE
    ↓
BOUNDED CONTEXT
    ↓
SOL SEMANTIC JUDGMENT
    ↓
EOCL ACCEPTANCE
    ↓
MEASURE
    ↓
STOP
```

Đây không phải là “thêm 5 feature”.

Đây là việc rút ngắn causal path tới một accepted result đáng tin.

Lợi thế cạnh tranh của Coding Web không nên là có nhiều tool hơn upstream hay nhiều agent hơn đối thủ.

Lợi thế nên là:

> **Execution Intelligence — máy xử lý phần có thể chứng minh, Sol chỉ tiêu token cho phần thực sự cần trí tuệ, và EOCL biến kết quả thành một accepted result có provenance đầy đủ.**

---

# 42. SOURCE INDEX

## 42.1. Internal

- `AGENTS.md`
- `docs/CURRENT_STATE.md`
- `docs/ROADMAP.md`
- `docs/research/260821_TRUTH_RECONCILIATION_CHECKPOINT.md`
- `docs/research/260821_CODING_WEB_LEAN_CONTROL_RICH_EVIDENCE_ACCEPTED_RESULT_SYNTHESIS.md`
- `docs/research/260821_CODING_WEB_MASTER_ENGINEERING_STRATEGY_AND_HISTORY.md`
- `.coding-tools/orchestration/ledger.sqlite3`
- generated run/wave reports

## 42.2. Upstream WebCodex

Repository:

`yyjeqhc/webcodex`

Selected commits:

- #90 `7a82fdd9a8f573300c67dbbcffd3912742d955d2` — Make guarded text edits CRLF-aware
- #112 `ea97ca7d977c87bfc2566ec563655a3c8abcc240` — Improve harness evidence and durable long execution handoff
- #113 `2a77ba69be09eb4902b41939b619d18539a1bb8b` — Continuously drain structured execution output
- #116 `95fab7e5485b89e9dfbda351e9699519b28e627e` — Add deterministic committed review summary
- #117 `8dd6b6ca24e29d5d8bdb08d5d29e665eb651aaa6` — Add exact committed-range diff hunks

## 42.3. Quy tắc diễn giải nguồn

Upstream trả lời:

```text
mechanism nào đã có implementation tốt?
invariant/test nào đáng reuse?
```

Local evidence trả lời:

```text
Codex-web có nên adopt không?
adapt vào authority hiện tại ra sao?
implementation có làm accepted result tốt hơn không?
```

Không đảo ngược hai tầng này.

---

**HẾT — BẢN KẾ HOẠCH TỔNG THỂ DIỄN GIẢI CHI TIẾT BẰNG TIẾNG VIỆT**

---

# 43. PHỤ LỤC THỰC THI VÀ ĐIỀU CHỈNH ƯU TIÊN — 2026-08-22

> Phụ lục này là snapshot vận hành sau kế hoạch, không viết lại chronology hay
> thay đổi ý nghĩa của các evidence snapshot ở phần 1–42. Mọi số liệu dưới đây
> được đọc lại từ canonical ledger và source/runtime đang vận hành tại thời
> điểm chụp. Một báo cáo tư vấn được tham khảo đã mô tả một HEAD upstream-matched
> và P5 epoch active; hai trạng thái đó **không còn đúng** trong checkout hiện
> tại, nên không được dùng để mở P5 hay làm bằng chứng promotion.

## 43.1. Quyết định điều hành đã điều chỉnh

```text
Không xây thêm P5 framework/table/tool trong wave kế tiếp.
Không dùng P4 predictive PASS làm điều kiện chặn P5-A0.
Không backfill hoặc suy diễn nguyên nhân cho historical failure.

Ưu tiên:
  A. hoàn tất integration/source identity có kiểm soát;
  B. để P2 taxonomy v3 thu prospective data trên event tự nhiên;
  C. chỉ mở một P5-A0 A/A mới khi toàn bộ gate runtime + source + operator
     + natural task đã đồng thời thỏa;
  D. theo dõi TTAR tail theo feature/bugfix, không chỉ repaired rate.
```

Lý do là nút thắt đã chuyển từ thiếu primitive sang thiếu observation có chất
lượng. Tạo synthetic workload, tự tạo assignment, hoặc mở epoch khi chưa có
natural feature/bugfix sẽ làm đẹp funnel nhưng không tạo evidence causal.

## 43.2. Những phần source đã được triển khai và kiểm chứng

Các candidate được tích hợp theo từng causal wave vào `main` tại:

```text
b8d8716ee22eadb1e3a1e6a53f9da1e6dc72c7f0
```

Chuỗi commit implementation:

```text
ec52f8c  continuously drain structured command pipes
278ceeb  preserve guarded text-edit line endings
a90a02e  add prospective P2 failure taxonomy
b8d8716  add deterministic committed review evidence
```

Nội dung có hiệu lực:

1. Runner đọc pipe liên tục, có bounded reader và cleanup process tree để
   command output lớn không block lifecycle.
2. Guarded `apply_text_edits` giữ CRLF/LF, từ chối mixed/bare CR nguy hiểm và
   vẫn atomic khi text canonical tương đương.
3. P2 v3 tạo detail **prospective, content-free, unattributed** cho
   `CHECK_FAILED` (command family) và `BUILD_VERIFICATION_FAILED`
   (verification stage). Cơ chế này không biến detail thành repair label và
   không suy diễn dữ liệu lịch sử.
4. `agent_workflow(phase=prepare)` nhận committed review xác định bằng local
   SHA/merge-base/HMAC continuation; không thêm tool thứ chín, không cho alias,
   fetch, external diff hay textconv làm thay đổi authority surface.

Focused source proof đã đạt trên exact source tree này:

```text
rustfmt (affected Rust files)                                  PASS
webcodex-runner runner_lifecycle_tests                         28/28 PASS
webcodex-runner file_apply_text_edits                          15/15 PASS
webcodex apply_text_edits --lib                                20/20 PASS
cargo check webcodex-runner --all-targets                      PASS
cargo check webcodex --all-targets                             PASS
selected Coding Tools MCP pytest                               129 passed
module-size guard + git diff --check                           PASS
coding-tools delivery guard on integration candidate           PASS
```

Đây là source/focused-test proof. Nó không tự chứng minh package, remote
release, hay hiệu quả causal ở production.

## 43.3. Runtime và authority đã được reconciliation

Controlled activation đã đưa Coding Tools MCP và Recovery Host về revision
source hiện hành; sau supervised restart, connector đã thực hiện discovery lại
và acknowledgement thành công. Runtime hiện vẫn giữ đúng public smart-v3
surface gồm tám tool:

```text
workspace_context, agent_workflow, task_control, document_workflow,
exec_command, command_control, request_permissions, view_image
```

Contract discovery SHA-256 hiện được runtime báo là:

```text
ab122032f504f960a0f3dc33af6d8d0996f6aca927f2b849be389e51c2820e36
```

Run EOCL objective-binding `088f7fb2b94647088eaac26b32595372` đã terminal
`accepted` bởi ChatWeb, checkpoint
`73e22b0976a84d4eb778830035b4474b`, với event-chain verification pass.
Không còn active execution run trong canonical ledger tại snapshot này.

Đây là live-contract/runtime proof; không phải là nghiệm thu release hay bằng
chứng P5 treatment.

## 43.4. Baseline economics: bài toán rework là có thật, nhưng là observational

Canonical `chatweb_mcp`, model-free accepted cohort hiện có:

| Metric | Giá trị hiện tại |
| --- | ---: |
| Accepted eligible | 455 |
| First-pass accepted | 267 (58,68%) |
| Repaired accepted | 188 (41,32%) |
| Replan | 359 |
| First-pass TTAR p50 / p90 | 66,458 s / 445,815 s |
| Repaired TTAR p50 / p90 | 302,914 s / 3.011,437 s |
| Repaired : first-pass p50 / p90 | 4,56x / 6,75x |

Vì thế objective lâu dài phải được đo theo:

```text
first-pass success
+ repair/replan incidence
+ accepted-result time (TTAR)
+ TTAR tail
+ quality floor
```

Không được biến các số observational này thành treatment effect hoặc ROI
causal. `preflight_avoided=151` chỉ có nghĩa là 151 known no-write patch
failure bị chặn trước run creation; nó không phải counterfactual “151 task
được cứu”.

### Stratum P5 phù hợp

`feature` và `bugfix` vẫn là cohort P5 hợp lý, nhưng phải randomized/analysed
theo stratum, không pooled-only:

| Workflow | n | Repaired | Repaired rate | First-pass p90 | Repaired p90 |
| --- | ---: | ---: | ---: | ---: | ---: |
| feature | 129 | 70 | 54,26% | 580,301 s | 2.648,443 s |
| bugfix | 98 | 39 | 39,80% | 259,577 s | 3.039,746 s |

Feature có repair incidence cao hơn; bugfix có tail repair penalty lớn hơn.
`diagnose` (28 repaired / 88; repaired p90 19.348,140 s) là một long-tail
problem đáng điều tra sau này, nhưng không nên trộn vào A0 hiện tại vì đổi
population và làm nhiễu causal estimand.

## 43.5. P2 taxonomy là leverage point số một, với ranh giới đúng

Snapshot P2 hiện có 365 failure event: 177 mapped/classified và 188
unclassified, tương đương mapped coverage 48,49%. Trong phần historical
generic detail không thể suy diễn lại có:

```text
CHECK_FAILED              114
BUILD_VERIFICATION_FAILED  56
-----------------------------
total                     170
```

Hai class này chiếm 90,43% `legacy_generic_detail_unavailable` (170/188), nên
đầu tư đúng vào boundary event creation có lợi suất cao hơn thiết kế P4 v6 lúc
này. Tuy nhiên phải giữ các ranh giới sau:

```text
historical unknown     -> vẫn unknown
P2 v3 detail           -> prospective only
detail bucket          -> measurement context, không phải root cause
failure taxonomy       -> không tự biến thành causal repair label
```

Từ đây không mở thêm “taxonomy framework”. Việc cần làm là để event tự nhiên
đi qua hai điểm instrumentation đã có, theo dõi coverage/detail bucket mới, rồi
đánh giá sau khi số mẫu mới đủ lớn. Nếu schema v3 không tạo variation thực tế,
thay đổi sau đó phải là patch nhỏ vào đúng point ghi event, kèm test; không
backfill ledger.

## 43.6. P4 tiếp tục collect, nhưng không là critical path của P5-A0

P4 có 70 representative terminal shadow task, trong đó causal-solution
outcome known là 2 repair / 50 nonrepair, 18 unknown. Predictive gate vẫn là:

```text
representative_descriptive_comparison_available_but_unvalidated
```

Rolling temporal holdout mới evaluable 1/8 window; family và source-state
holdout chưa đủ outcome variation. `oracle_strength` luôn `strong` và
`root_cause_confidence` luôn `high`, nên cả hai là low-variance metadata và
Brier gain hiện bằng 0. `expected_repair_risk`, scope fields còn variation,
nhưng chưa có validated signal.

Quy tắc vận hành:

1. Không sửa P4 v5 giữa lúc đang collect prospectively.
2. Không tự tạo shadow label/task chỉ để tăng variation.
3. Ghi nhận low-variance fields là candidate cần reconsider **sau** khi P4 v5
   đủ observational evidence; chưa loại bỏ hoặc dùng làm policy input.
4. P4 không được bật automatic routing/treatment và không chặn P5-A0 A/A.

## 43.7. P5: engineering có mặt, empirical funnel vẫn bằng không

Canonical P5 ledger chứa bốn epoch lịch sử, và cả bốn đang `EPOCH_CLOSED`.
Không có active P5 epoch, active execution run, enrollment decision,
randomized assignment, arm-protocol start, workflow binding hay outcome:

| P5 funnel | Count |
| --- | ---: |
| epochs recorded | 4 |
| live epochs | 0 |
| enrollment decisions | 0 |
| assignments | 0 |
| protocol starts | 0 |
| workflow bindings | 0 |
| outcomes | 0 |

Seed runtime đã được provision qua opaque handle
`secret://experiment/p5/a`; raw seed không được và sẽ không được ghi vào
ledger, source, log, report hay chat. Điều này chỉ chứng minh secret delivery
path, không chứng minh P5 evidence.

P5-A0 hiện **HOLD**, không phải FAIL của code và cũng không phải `EPOCH_ACTIVE`:

```text
source worktree clean excluding runtime evidence = true
HEAD == origin/main                              = false
automatic start / policy activation              = false
active epoch                                     = false
natural eligible task + stable oracle            = absent
```

Do đó không tạo manifest mới, không mở epoch, không gán arm, và không thực
hiện P5-A treatment ở wave này. Đây là fail-closed đúng thiết kế.

## 43.8. Trình tự ngắn nhất để P5-A0 thực sự bắt đầu

```text
1. Chủ sở hữu explicit-authorize destination để publish integration source.
2. Commit/push theo policy, fetch lại và xác nhận HEAD == named upstream;
   worktree source sạch (runtime evidence được đánh giá theo scope riêng).
3. Tạo manifest A0 từ template v2, với identity/runtime contract hiện hành,
   opaque secret handle, seed commitment và tất cả guard frozen.
4. Xác nhận không có writer lease và operator authority cho đúng epoch.
5. Chờ một natural feature hoặc bugfix có stable quality oracle; enrollment
   arm-neutral xảy ra trước assignment và trước write.
6. Chạy A/A control protocol; ghi assignment, binding và outcome theo ITT.
7. Kiểm tra funnel integrity: missingness, crossover, adherence, quality floor,
   replan/no-harm và TTAR theo feature/bugfix.
8. Chỉ khi A0 có evidence mạnh, operator review riêng mới được cân nhắc P5-A
   treatment canary. Không automatic promotion.
```

Mỗi epoch cần một immutable manifest mới khi source/runtime identity đổi; không
tái sử dụng chứng cứ A0 cũ sau fingerprint drift. Giữ nguyên nguyên tắc một
writer, một authority và một epoch live per experiment.

## 43.9. Trạng thái delivery hiện tại và điều kiện ngoài repository

`main` đang ở `b8d8716…`, trong khi `origin/main` ở `ea4dc6b…`; các source
commit integration chưa được push. Ngoài các runtime-evidence artifacts dưới
`.coding-tools/`, phụ lục này tạo một documentation change chưa commit. Không
có push, package, release, deploy hoặc external production change nào được
thực hiện bởi wave này.

Vì vậy, P5 không thể hợp lệ chuyển từ HOLD sang start-ready cho đến khi có hai
authority/external input cụ thể:

```text
A. explicit authorization cho target publish, ví dụ: git push origin main
B. natural feature/bugfix đầu tiên cùng stable quality oracle để quan sát
```

Khi A và B xuất hiện, controller phải re-run Gate 0 trên đúng checkout/runtime
thời điểm đó trước khi mở P5-A0; không tái sử dụng kết luận readiness ở phụ
lục này.

---

**KẾT LUẬN PHỤ LỤC:** hướng ngắn nhất không phải thêm hạ tầng. Source hardening
và P2 prospective instrumentation đã có; việc có giá trị tiếp theo là đóng
source identity đúng policy, thu natural A/A observation sạch, đồng thời để P2
taxonomy v3 giảm vùng unknown một cách prospective. P4 tiếp tục đo nhưng không
được trở thành cổng giả cho causal learning.
