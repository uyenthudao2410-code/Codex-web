# CODING-WEB — EVIDENCE-GROUNDED RESOLUTION INTELLIGENCE
## Phương pháp luận đột phá và chương trình triển khai để biến lịch sử dự án thành năng lực giải quyết vấn đề tích lũy

**Ngày:** 2026-09-01  
**Workspace:** `E:\DEV\Codex-web`  
**Trạng thái tài liệu:** Strategic research / implementation methodology  
**North Star:** `TTPR = Time to Trusted Problem Resolution`  
**Mục đích:** Chọn hướng đi tiếp theo sau khi P0/P0.6 đã hội tụ, dựa trên dữ liệu máy, lịch sử Codex-web, Golden HR cases và các nền tảng nghiên cứu khoa học; tránh mở rộng machinery nếu chưa chứng minh giảm rework/TTPR.

---

# 0. Executive decision

## 0.1. Kết luận ngắn

Bài toán hiện tại **không phải thiếu dữ liệu, thiếu log, thiếu model hay thiếu control-plane**. Codex-web đã tích lũy rất nhiều event, RUN/WAVE, proof, telemetry, Git history, chat history, PRL và kinh nghiệm từ HR. Điểm nghẽn là:

> **Hệ thống lưu được rất nhiều “điều đã xảy ra”, nhưng chưa chuyển hóa đủ tốt thành “tri thức quyết định” để lần giải tiếp theo tránh lặp lại cùng một sai lầm về framing, localization, oracle và causal diagnosis.**

Do đó hướng đột phá được lựa chọn trong tài liệu này là:

> **Evidence-Grounded Resolution Intelligence — EGRI**  
> Một vòng lặp học giải quyết vấn đề dựa trên bằng chứng, trong đó lịch sử được nén thành trạng thái quyết định hiện hành, tri thức repository có thể truy vấn, và Resolution Case Memory có điều kiện áp dụng/negative-transfer; toàn bộ vẫn nằm dưới authority hiện hữu của Problem Revision + PRL + EOCL.

EGRI **không phải** một subsystem authority mới, không phải “AI brain”, không phải vector-memory tổng quát, không phải Knowledge Graph platform và không thêm public MCP tool. Phiên bản đầu chỉ gồm ba projection/advisory layer có thể rebuild:

1. **Resolution State Capsule** — nén trạng thái problem hiện hành thành dữ liệu đủ để quyết định bước tiếp theo;
2. **Workspace Evidence Index** — chỉ mục derived về source/symbol/dependency/owner/oracle/test/recent-change để giảm repeated localization;
3. **Resolution Case Memory** — kinh nghiệm đã chưng cất từ các problem trước, gồm applicability và negative-transfer warning, không lưu raw transcript/private reasoning.

Ba lớp này tạo thành một vòng khép kín:

```text
RAW HISTORY / RUNTIME / SOURCE
            ↓
      EVIDENCE NORMALIZE
            ↓
  RESOLUTION STATE CAPSULE
            ↓
  WORKSPACE EVIDENCE LOOKUP
            ↓
   CASE RETRIEVE + CONTRAST
            ↓
 HYPOTHESIS / DISCRIMINATOR
            ↓
       CAUSAL CHANGE
            ↓
 PROOF + OUTCOME + FALSIFIER
            ↓
  DISTILL / REVISE / RETAIN
            └──────────────→ lần problem sau
```

Mục tiêu không phải “AI nhớ nhiều hơn”, mà là:

> **AI cần đọc ít lịch sử hơn nhưng ra quyết định tốt hơn.**

---

# 1. Baseline hiện tại: dự án đã đi tới đâu

## 1.1. Những gì đã đủ mạnh để coi là nền móng

Theo current state và live runtime tại thời điểm nghiên cứu:

- P0 Operational Convergence đã đóng;
- P0.6 immutable accepted local baseline đã đóng;
- accepted source baseline nằm tại `main @ 30b7d1b971b65034d3e4c95568c970fcc0e9380c`, `origin/main` khớp;
- source packet P0.6 gồm 27 file đã được exact hash/reverify trước acceptance;
- checkpoint accepted: `e3b6c1a07b3f4524af8d0bef967fc7d5`;
- runtime local đã chứng minh READY/OPEN, Electron UI và Coding MCP current;
- connector hiện ở `CURRENT_COMPATIBLE_ACKNOWLEDGED`, không refresh/ack pending;
- stale ordinary orchestration, unresolved stale và orphan residue ở baseline đã về 0;
- smart-v3 public surface vẫn giữ đúng 8 tool;
- Problem Revision / PRL / provisional resolution / Resolution Envelope / closure falsification đã có machinery;
- automatic nondeterministic routing và production promotion vẫn fail-closed — đúng chủ đích.

Điều này cho phép thay đổi trọng tâm phát triển. Từ đây, việc đầu tư thêm vào recovery/connector/control chỉ hợp lý khi có **defect thật** hoặc khi natural workload chứng minh chúng đang là critical path.

## 1.2. P0.6 không đồng nghĩa Trusted Problem Resolution

P0.6 chỉ chứng minh rằng hệ thống có thể biết và kiểm soát:

- source nào được chấp nhận;
- runtime nào đang chạy;
- ai có authority;
- proof nào gắn đúng fingerprint;
- lifecycle nào đã checkpoint;
- connector nào hiện hành.

Nó không chứng minh:

- user problem được hiểu đúng ngay lần đầu;
- problem boundary được chọn đúng;
- oracle đúng abstraction;
- user outcome đã đạt;
- same-problem reopen giảm;
- TTPR giảm;
- P4/P5 có predictive/causal efficacy.

Đây là ranh giới cần giữ nghiêm để tránh false closure ở cấp chiến lược.

---

# 2. Dữ liệu nội bộ đang nói gì

## 2.1. Rework là chi phí lớn nhất đã quan sát được

Revision 4 đã khóa một cohort lịch sử có:

- accepted organic runs: `188`;
- first-pass: `130` ≈ `69.15%`;
- repaired: `58` ≈ `30.85%`;
- first-pass TTA p50 ≈ `36.357 s`;
- repaired TTA p50 ≈ `192.319 s`;
- repair penalty p50 ≈ `5.29×`.

Đây là bằng chứng mạnh để thay đổi objective. Nếu một execution nhanh hơn 20% nhưng vẫn rơi vào wrong-frame repair, lợi ích đó nhỏ hơn nhiều so với việc tránh một lần repair 5.29×.

**Hệ quả:** ưu tiên phải là **first-pass causal correctness + trusted outcome**, không phải raw execution throughput.

## 2.2. Localization là critical path lặp lại

Telemetry hiện hành cho thấy hàng nghìn localization queries, gần như toàn bộ vẫn fallback search; LSP chỉ xử lý được một phần cực nhỏ. Điều này không chứng minh rằng phải “LSP-first”. Nó chứng minh một vấn đề rộng hơn:

> Mỗi context/model đang phải tái tạo lại quá nhiều mental model của repository.

Việc repeatedly tìm file/symbol/caller/test/route/schema/owner/recent-change là **knowledge reconstruction cost**.

## 2.3. Proof cache không phải leverage point

Proof-cache hit lịch sử gần như bằng 0; nguyên nhân chính là cold input hoặc fingerprint thay đổi. Vì vậy tăng sophistication của cache lúc này khó tạo ROI. Muốn reuse proof tốt hơn trước hết phải làm source/problem identity và natural task stability tốt hơn.

## 2.4. P4/P5 cho thấy machinery đi trước efficacy

P4 có descriptive shadows nhưng chưa có `validated_signals`; P5 vẫn chưa có enrollment/assignment/outcome đủ để nói causal effect. Vì vậy không có bằng chứng để tự động hóa router hay treatment.

Đây là trạng thái lành mạnh nếu hiểu đúng: **đã có instrumentation để học, nhưng chưa được phép biến instrumentation thành policy**.

---

# 3. Golden HR cases: bằng chứng mạnh nhất về failure mode thật

Golden HR calibration hiện có 7 case tự nhiên. Chúng không phải benchmark nhân tạo mà là các vấn đề user đã thực sự gặp trong HR STA.

## 3.1. Pattern xuyên 7 case

Các failure dimension nổi bật:

- state/runtime mismatch: GHR-02, GHR-03, GHR-04, GHR-07;
- semantic/causal boundary: GHR-02, GHR-03, GHR-07;
- identity/authority: GHR-01, GHR-04, GHR-05, GHR-06;
- oracle mismatch: **cả 7 case**;
- control friction: GHR-01, GHR-02, GHR-03, GHR-05, GHR-07.

Đặc biệt, 6/7 case có technical accepted wave nhưng calibration vẫn không có independent user-success đủ để gọi Trusted Resolution; ít nhất 2 case bị reopen bởi counterevidence của user.

## 3.2. GHR-03 là case kinh điển của false closure

Dạng failure:

```text
proof generic/read-model PASS
        ↓
technical acceptance
        ↓
actual live PFM projection vẫn sai
        ↓
user counterevidence
        ↓
reopen / settlement scope gap
```

Vấn đề không nằm ở test runner. Vấn đề nằm ở việc **oracle không cùng abstraction với desired outcome**.

## 3.3. GHR-02/GHR-07 cho thấy problem boundary quan trọng hơn patch size

Khi lỗi xuất hiện ở Finance hero/status/save, patch tại một component có thể đúng cục bộ nhưng không đủ vì causal chain có thể đi qua:

```text
Project metadata
→ canonical persistence
→ contract/appendix ownership
→ finance projection
→ aggregation
→ UI rendering
```

Điều này giải thích vì sao nguyên tắc đúng phải là:

> **Think broad enough to frame correctly; intervene as narrowly as causally sufficient.**

Không phải “luôn sửa ít file nhất”.

---

# 4. Chẩn đoán gốc: từ Data Abundance sang Decision Intelligence

## 4.1. Ba dạng “memory” đang bị trộn lẫn

Dự án hiện có nhiều dữ liệu nhưng phần lớn thuộc ba lớp khác nhau:

### Event memory

- tool calls;
- RUN/WAVE events;
- Git commits;
- command outputs;
- runtime receipts;
- chat turns.

Trả lời câu hỏi: **“Đã xảy ra gì?”**

### Evidence memory

- proof fingerprint;
- test result;
- runtime identity;
- source hash;
- counterevidence;
- user outcome observation.

Trả lời: **“Điều gì đã được chứng minh/bác bỏ?”**

### Decision memory

- causal frame nào đã thất bại;
- invariant nào là governing;
- discriminator nào đã thay đổi quyết định;
- owner nào là canonical;
- intervention nào thật sự làm outcome đổi;
- khi nào case cũ áp dụng và khi nào không.

Trả lời: **“Lần tới nên suy luận khác đi thế nào?”**

Codex-web hiện rất mạnh ở Event/Evidence memory nhưng còn yếu ở Decision memory.

## 4.2. Mục tiêu của EGRI

EGRI chuyển:

```text
history volume ↑
```

thành:

```text
decision entropy ↓
```

Một resolution state tốt không phải chứa nhiều dữ liệu nhất. Nó phải giảm số giả thuyết còn hợp lý và làm rõ discriminator tiếp theo.

---

# 5. Nền tảng khoa học và cách chuyển hóa vào Codex-web

Tài liệu này không coi các nghiên cứu dưới đây là “proof rằng EGRI chắc chắn hiệu quả”. Chúng là **research priors / design basis**. Hiệu quả trong Codex-web vẫn phải được chứng minh bằng natural workload.

## 5.1. Scientific method và falsification

Tư duy khoa học yêu cầu một hypothesis phải có khả năng bị phản bác. Trong debugging, một test chỉ có giá trị chẩn đoán nếu kết quả của nó phân biệt được các nguyên nhân cạnh tranh.

**Chuyển hóa:**

- Problem Frame giữ `H = {H1, H2, ...}`;
- mỗi H phải có predicted observations/falsifier;
- không chạy diagnostic chỉ để “có thêm dữ liệu”;
- counterevidence bắt buộc cập nhật Frame trước mutation cùng causal family.

Revision 4 `Decision Delta Test` chính là operationalization nhẹ của Value of Information:

> Nếu X và Y đều dẫn đến cùng một next action, phép đo đó không đáng nằm trên critical path.

## 5.2. Delta debugging — Zeller & Hildebrandt (2002)

Delta debugging tự động thu nhỏ failing input và cô lập khác biệt giữa passing/failing configuration. Ý tưởng quan trọng không phải thuật toán cụ thể mà là **systematic discrimination**: thay vì đoán, giảm không gian nguyên nhân bằng thử nghiệm có khả năng phân biệt.

**Chuyển hóa:**

- ưu tiên discriminator có thể cô lập boundary/owner/path;
- so sánh failing vs passing state;
- với state/runtime: exact source identity, runtime revision, consumer projection;
- với business semantics: minimal example phân biệt hai cách hiểu.

## 5.3. Developer mental models — LaToza, Venolia & DeLine (ICSE 2006)

Nghiên cứu developer work habits cho thấy developer tốn nhiều công sức khôi phục implicit knowledge bằng khám phá code và hỏi người khác, trong khi tri thức đó chủ yếu nằm trong memory cá nhân.

**Chuyển hóa:**

Workspace Evidence Index không nhằm thay model, mà externalize phần mental model ổn định/rebuildable:

- symbol ownership;
- dependency edges;
- relevant tests/oracles;
- route/schema/data ownership;
- recent changed surfaces.

## 5.4. Task interruption/resumption — Parnin & Rugaber (2011)

Nghiên cứu hàng nghìn programming sessions cho thấy resumed programming thường cần navigation/context reconstruction trước khi bắt đầu edit.

**Chuyển hóa:**

Resolution State Capsule phải tối ưu cho **resumption**:

- không replay chat dài;
- không serialize private reasoning;
- giữ exact known facts, unresolved hypotheses, counterevidence, current authority, next discriminator;
- có source/runtime freshness.

## 5.5. Programming change questions — Sillito, Murphy & De Volder (IEEE TSE 2008)

Developer trong change task cần trả lời nhiều loại câu hỏi về codebase và mối quan hệ giữa các thành phần. Code search thuần text không đủ cho mọi câu hỏi.

**Chuyển hóa:**

Workspace Intelligence phải phục vụ câu hỏi, không phục vụ graph vì graph:

- “Ai sở hữu field này?”
- “Từ persistence nào dữ liệu đến UI này?”
- “Consumers nào dùng aggregation này?”
- “Oracle nào quan sát đúng behavior này?”
- “Change gần đây nào chạm causal path?”

## 5.6. Case-Based Reasoning — Aamodt & Plaza (1994)

CBR mô tả vòng `retrieve → reuse → revise → retain`. Đây là nền tảng trực tiếp cho Resolution Case Memory.

**Chuyển hóa quan trọng:**

Không retrieve theo keyword đơn thuần. Một case chỉ có thể được reuse khi current context vượt qua **Applicability Gate**.

Case Memory cần chứa cả:

- what worked;
- what failed;
- why it failed;
- when not to reuse.

Điều này giúp chống negative transfer.

## 5.7. Design Science — Hevner, March, Park & Ram (MISQ 2004)

Design Science coi việc xây artifact và đánh giá artifact trong môi trường sử dụng là nguồn tạo tri thức. Điều này phù hợp Codex-web hơn việc tranh luận architecture bằng lý thuyết.

**Chuyển hóa:**

Mỗi capability mới phải đi theo:

```text
observed problem
→ minimal artifact
→ natural HR evaluation
→ measured consequence
→ retain / revise / remove
```

Không build full platform rồi mới đi tìm use case.

## 5.8. Empirical software engineering — Runeson & Höst (2009); Kitchenham et al. (2002)

Case study trong software engineering phù hợp khi cần nghiên cứu hiện tượng trong context thật; empirical guidelines nhấn mạnh thiết kế, data collection, analysis và reporting rõ ràng.

**Chuyển hóa:**

Golden HR cases phải có:

- case selection rationale;
- protocol trước mutation;
- exact outcome oracle;
- provenance;
- threats to validity;
- không đổi metric sau khi thấy kết quả.

## 5.9. Causal inference trong software engineering

Systematic mapping năm 2023 về causal inference trong SE cho thấy causal graphical approaches đang được dùng để tránh nhầm correlation với causal effect, nhưng practice còn nonuniform. Nghiên cứu 2026 về omitted-variable bias nhấn mạnh cần explicit causal model và sensitivity analysis trước khi kết luận từ observational data.

**Chuyển hóa:**

- lịch sử observational chỉ tạo hypothesis/ranking;
- không dùng correlation của P4 để tự động routing;
- treatment policy chỉ được promote sau A/A instrumentation health và A/B/quasi-experimental evidence;
- model/route/oracle/source/task class cần được hold constant hoặc stratify khi so policy.

## 5.10. GQM — Goal/Question/Metric

GQM đi từ goal → questions → metrics thay vì đo tất cả rồi tìm ý nghĩa sau.

**Chuyển hóa:**

Không thêm metric nếu chưa trả lời được:

> Metric này sẽ thay đổi decision nào?

Ví dụ:

- Goal: giảm TTPR;
- Question: repeated localization có nằm trên critical path không?;
- Metric: localization time/problem + duplicate localization queries;
- Decision: promote/remove Workspace Evidence Index.

---

# 6. Formal epistemic model — mô hình tư duy logic

Để tránh “reasoning bằng narrative”, EGRI dùng một state model nhỏ.

Với Problem Revision `R` tại thời điểm `t`:

```text
S_t = <C, I, O, F_t, E_t, X_t, U_t, A_t>
```

Trong đó:

- `C` — Contract: desired outcome + constraints;
- `I` — protected/governing invariants;
- `O` — current observed manifestation;
- `F_t` — current Problem Frame;
- `E_t` — supporting evidence;
- `X_t` — counterevidence;
- `U_t` — unresolved uncertainty;
- `A_t` — authority/freshness/source/runtime state.

Problem Frame:

```text
F_t = <A, A*, G, Owner, H, Pred, Falsifier>
```

- `A`: observed affected surface;
- `A*`: Minimal Sufficient Problem Boundary;
- `G`: Governing Invariant;
- `Owner`: canonical ownership/data authority;
- `H`: ranked causal hypotheses;
- `Pred`: predicted observations;
- `Falsifier`: evidence that would invalidate each hypothesis/claim.

## 6.1. Không gán “xác suất giả” nếu chưa có calibration

Có thể xếp `H1 > H2 > H3` theo evidence strength, nhưng không được ghi “H1 = 82%” nếu chưa có calibration model. Dùng ordinal confidence:

```text
LOW / MEDIUM / HIGH / UNKNOWN
```

và bắt buộc kèm `why` theo observed evidence.

## 6.2. Evidence ladder

```text
E0 UNKNOWN
E1 OBSERVED
E2 DETERMINISTIC / exact state
E3 INDEPENDENT ORACLE
E4 USER / BUSINESS OUTCOME AUTHORITY
```

Không phải mọi problem cần E4, nhưng nếu claim là user-visible full_problem thì technical proof không được tự nâng lên E4.

## 6.3. Counterevidence rule

Material counterevidence xảy ra khi evidence mới làm sai ít nhất một trong:

- current boundary;
- governing invariant interpretation;
- canonical owner;
- leading hypothesis;
- oracle sufficiency;
- source/runtime truth assumption.

Khi đó:

```text
Material Counterevidence
        ↓
BLOCK same-frame mutation retry
        ↓
Explain contradiction
        ↓
Revise Frame or discriminator
        ↓
Only then mutate
```

---

# 7. Core methodology — Resolution Intelligence Loop

## Bước 1 — CONTRACT

Mục đích: khóa **problem contract**, không khóa solution.

Bắt buộc:

- desired outcome;
- acceptance criteria;
- protected invariants;
- constraints;
- unresolved conditions;
- user/business authority fields.

Rule:

> Contract change → `REVISE`; same contract still failing → `REOPEN` same Problem Revision.

## Bước 2 — RECONSTRUCT CURRENT TRUTH

Trước diagnosis phải phân biệt:

- source truth;
- runtime truth;
- persistence truth;
- projection truth;
- UI truth;
- external/user outcome.

Không cho phép inference từ source sang runtime nếu currentness chưa được chứng minh.

## Bước 3 — RETRIEVE, BUT DO NOT COPY

Query Workspace Evidence Index + Case Memory để lấy:

- canonical owners;
- likely relevant symbols/files;
- related invariants;
- prior similar frames;
- known wrong interpretations;
- prior counterevidence;
- relevant oracles.

Sau đó chạy Applicability Gate.

## Bước 4 — FRAME

Xây `A* / G / H`.

Frame tốt phải giải thích được:

- tại sao symptom xảy ra;
- tại sao các observation liên quan cùng causal chain;
- evidence nào phân biệt H1/H2;
- what would prove frame wrong.

## Bước 5 — DISCRIMINATE

Chọn phép đo bằng Decision Delta Test.

Một discriminator tốt:

1. rẻ hơn mutation sai;
2. kết quả X/Y dẫn đến action khác nhau;
3. đo đúng abstraction;
4. không tạo side effect không cần thiết.

## Bước 6 — INTERVENE CAUSALLY

Patch nhỏ nhất **sufficient for governing invariant**, không phải patch ít dòng nhất.

Tránh:

- symptom patch;
- defensive fallback che owner sai;
- duplicate data path;
- broad refactor khi causal link chưa rõ.

## Bước 7 — VERIFY BY ORACLE LADDER

Oracle phải match acceptance level:

```text
syntax/static
→ focused behavior
→ subsystem/consumer
→ live/runtime projection
→ independent outcome
→ user/business confirmation (khi cần)
```

## Bước 8 — FALSIFY CLOSURE

Trước `RESOLVED_CONFIRMED`, hỏi:

> “Điều đáng tin cậy nhất có thể vẫn khiến claim này sai là gì?”

Chạy một closure-falsification probe có positive value.

## Bước 9 — RESOLVE / REOPEN

- technical acceptance → tối đa `PROVISIONALLY_RESOLVED`;
- independent/user outcome đạt → `RESOLVED_CONFIRMED`;
- same-contract counterevidence → `REOPEN`;
- changed contract → `REVISE`.

## Bước 10 — DISTILL

Chưng cất case thành reusable knowledge; loại bỏ noise.

---

# 8. Resolution Case Memory — từ lịch sử thành tri thức

## 8.1. Case record tối thiểu

```yaml
case_id:
problem_family:
contract_signature:
manifestation:
governing_invariants:
minimal_sufficient_boundary:
canonical_owners:
initial_frame:
wrong_hypotheses:
counterevidence:
decision_changing_discriminators:
causal_intervention:
oracles:
outcome:
applicability:
negative_transfer_warnings:
source/runtime_assumptions:
confidence_level:
```

Không lưu:

- raw transcript;
- private chain-of-thought;
- large source dumps;
- arbitrary model prose;
- stale PID/ephemeral IDs như stable knowledge.

## 8.2. Retrieve theo mechanism, không chỉ symptom

Một bug “doanh thu sai” có thể có mechanism:

- aggregation double-count;
- stale projection;
- wrong contract scope;
- UI using wrong source;
- settlement semantics misunderstood.

Hai symptom giống nhau nhưng mechanism khác thì không được reuse patch.

Ranking key nên ưu tiên:

```text
same invariant
+ same owner/data-flow
+ same causal mechanism
+ compatible source/runtime assumptions
+ similar oracle
```

hơn là chỉ `same words`.

## 8.3. Negative transfer gate

Case cũ bị reject nếu:

- contract semantics khác;
- owner khác;
- source generation/fingerprint làm assumption không còn đúng;
- prior solution chỉ provisional;
- case từng bị reopen bởi counterevidence chưa được reconciled;
- oracle cũ đã chứng minh là yếu.

---

# 9. Resolution State Capsule — nén trạng thái để tiếp tục xuyên context

Capsule không phải “summary chat”. Nó là **decision state**.

Mẫu:

```yaml
problem:
  id:
  revision:
  objective:
  acceptance:
truth:
  workspace:
  source_identity:
  runtime_identity:
  persistence_state:
frame:
  boundary:
  governing_invariant:
  owners:
  hypotheses:
evidence:
  supporting:
  counterevidence:
  invalidated_proofs:
resolution:
  accepted_subclaims:
  unresolved_gap:
next:
  discriminator:
  expected_decision_delta:
authority:
  writer:
  acceptance_owner:
freshness:
  observed_at:
```

## Capsule invariants

1. derived/rebuildable;
2. bounded;
3. no private reasoning;
4. exact source/freshness labels;
5. old proof giữ valid cho exact subclaim nhưng không masquerade thành current full-problem proof;
6. current contradiction phải visible.

---

# 10. Workspace Evidence Index — “runtime remembers code” ở mức vừa đủ

## 10.1. Không xây universal code intelligence platform

MVP chỉ cần trả lời nhanh các câu hỏi lặp lại trong Golden HR:

- field/entity này canonical ở đâu?;
- write path nào?;
- read projection nào?;
- consumers nào?;
- test/oracle nào cover đúng behavior?;
- recent changes chạm path nào?;
- UI nào đang render dữ liệu này?;

## 10.2. Data model derived

```text
File
Symbol
Import/Dependency
Route/IPC
Schema/Table/Entity
Config
Test/Oracle
UI Consumer
Recent Change
```

Edges ví dụ:

```text
DEFINES
IMPORTS
READS_FROM
WRITES_TO
PROJECTS_TO
RENDERS
TESTED_BY
CHANGED_WITH
```

Không cần graph database ở MVP. Một deterministic compact index/cache là đủ nếu query latency và update cost hợp lý.

## 10.3. LSP là provider, không foundation

Nếu LSP available, dùng semantic result; nếu không, parser/static extraction/fallback vẫn hoạt động. Đây là yêu cầu quan trọng vì live runtime hiện chưa có native LSP binding đáng tin cậy.

---

# 11. Architecture decision

## 11.1. Giữ authority hiện hữu

Canonical authority tiếp tục là:

```text
User Contract
→ Problem Revision / PRL
→ EOCL execution authority
→ exact proof/checkpoint
→ runtime/outcome evidence
```

EGRI chỉ advisory/derived:

```text
Resolution State Capsule
Workspace Evidence Index
Resolution Case Memory
```

Không layer nào trong EGRI được tự:

- grant write authority;
- accept run;
- change Problem Revision;
- promote route;
- declare Trusted Resolution;
- override user business meaning.

## 11.2. Không thêm public MCP tool

EGRI nên được expose như projector/query capability bên trong 8-tool surface hiện tại hoặc như internal derived data consumed bởi existing workflow. Chỉ thêm public contract nếu natural evaluation chứng minh current surface không thể hỗ trợ mà không tạo governance friction đáng kể.

---

# 12. Chương trình triển khai — từ research sang artifact

## Phase A — Freeze & doctrine enforcement

**Mục tiêu:** không để project quay lại feature-first expansion.

Thực hiện:

- đóng băng public tool/state/router expansion;
- fix only real blockers;
- bắt buộc `Problem Revision` cho prospective natural case;
- controller-level enforce rule: material counterevidence → no same-frame mutation retry;
- metric mới phải gắn với explicit decision.

**Exit:** một natural case có contract + F0 + oracle trước first write.

## Phase B — Historical Resolution Distillation

**Mục tiêu:** biến 7 Golden HR case và một số Codex-web incidents thành Case Memory prototype offline/derived.

Không backfill “user confirmation” giả.

Với mỗi case:

- exact contract đã biết;
- observed manifestation;
- initial frame;
- wrong hypothesis;
- counterevidence;
- governing invariant;
- canonical owner;
- decision-changing discriminator;
- causal fix nếu đã đủ evidence;
- oracle gap;
- outcome state;
- applicability/negative transfer.

**Exit:** 7/7 case có structured distilled case; ambiguous fields = UNKNOWN, không đoán.

## Phase C — Workspace Evidence Index MVP cho một family

Chỉ chọn **một family HR**: Finance project revenue/settlement/status/projection.

Index tối thiểu:

- project/contract/payment/settlement entities;
- persistence owners;
- finance projection symbols;
- UI consumers;
- tests/oracles;
- recent changes.

Đo:

- localization time;
- duplicate search count;
- bytes/context read trước mutation;
- wrong-target navigation.

**Exit:** cùng một family, index giúp localization nhưng không làm stale/wrong-owner tăng.

## Phase D — Resolution State Capsule projector

Không tạo database authority mới. Project từ PRL + current runtime/source + evidence store.

Kiểm tra bằng “context resumption test”:

1. Context A dừng ở giữa diagnosis;
2. Context B chỉ nhận capsule + bounded repository packet;
3. B phải xác định đúng current gap, invalidated hypothesis và next discriminator;
4. không replay raw chat.

**Exit:** resumption correctness đạt trước natural mutation.

## Phase E — First Prospective Natural Trusted Resolution

Ưu tiên một **problem HR mới**. Nếu không có problem mới đủ tiêu chuẩn, recapture current HR state rồi mới cân nhắc GHR-07; không giả định GHR-07 vẫn open chỉ vì calibration lịch sử.

Protocol:

```text
OPEN Problem Revision
→ capture contract
→ F0 A*/G/H
→ Workspace Evidence lookup
→ relevant prior Case Memory
→ discriminator
→ minimal causal patch
→ focused proof
→ live projection proof
→ closure falsifier
→ independent/user outcome
→ resolve or reopen
→ distill case
```

**Exit:** case có complete lineage từ contract đến outcome, kể cả nếu kết quả là reopen.

## Phase F — Natural cohort

Chạy 5–10 case tự nhiên liên tiếp trước khi kết luận broad efficacy.

Mục tiêu không phải thắng mọi case mà thu được distribution thật:

- TTPR;
- first-pass trusted;
- reopen;
- user correction turns;
- localization time;
- governance friction;
- frame revision count;
- false closure.

## Phase G — A/A rồi mới A/B

P5-A0 trước hết phải chứng minh instrumentation/randomization không tạo difference giả.

Sau A/A health:

- Control: current workflow;
- Treatment: EGRI protocol;
- hold constant/stratify: task family, source identity, oracle, model route, review policy, cache stratum, environment;
- primary outcome: TTPR;
- secondary: first-pass trusted/reopen/localization/corrections/friction;
- safety floors: defect/regression/data/security/business invariants.

Không promote treatment từ observational correlation.

---

# 13. Thiết kế thí nghiệm và statistical discipline

## 13.1. Phân biệt ba tầng evidence

### Descriptive

Cho biết “đã xảy ra gì”.

### Predictive

Signal dự đoán repair/reopen tốt hơn chance/out-of-sample.

### Causal

Thay policy X làm outcome Y thay đổi khi confounders được kiểm soát đủ.

Không được dùng descriptive evidence để claim causal benefit.

## 13.2. Với sample nhỏ

Ở 5–10 natural cases, tập trung:

- raw case table;
- median/p90;
- paired deltas nếu có matched pair;
- exact proportions;
- confidence interval rộng phải được giữ nguyên;
- qualitative mechanism trace.

Không dùng p-value để tạo cảm giác certainty giả từ n nhỏ.

## 13.3. Khi có cohort lớn hơn

Có thể dùng:

- bootstrap confidence intervals cho TTPR median/quantiles;
- Fisher/exact hoặc Wilson intervals cho first-pass/reopen proportions;
- paired randomization/permutation khi design là paired;
- stratification theo task family;
- causal DAG để liệt kê confounders trước analysis;
- sensitivity analysis cho omitted variables.

## 13.4. Pre-registration nội bộ

Trước treatment:

- primary metric;
- secondary metrics;
- exclusion rules;
- stop rules;
- safety floors;
- source/task/oracle pairing;
- analysis method.

Sau khi thấy kết quả không được đổi success metric để “thắng”.

---

# 14. Success gates và kill criteria

Các threshold dưới đây là **engineering targets**, không phải định luật khoa học.

## 14.1. Promote EGRI khi

Trên cohort representative đủ lớn:

- TTPR giảm material, target tham khảo ≥ ~30% median hoặc hiệu quả tương đương có ý nghĩa vận hành;
- repair/reopen giảm target ~25–30% trở lên;
- first-pass trusted tăng;
- user correction turns giảm;
- localization time giảm rõ;
- false closure không tăng;
- governance friction không tăng material;
- hard safety/business invariants non-inferior.

## 14.2. Simplify/remove khi

- capsule construction overhead lớn hơn localization saved;
- retrieval gây negative transfer;
- case memory chủ yếu trả stale/wrong-owner hints;
- workflow tăng ceremony nhưng TTPR không giảm;
- metrics không thay đổi decision;
- Workspace Index đòi maintenance gần bằng việc search trực tiếp;
- treatment chỉ “trông thông minh hơn” nhưng trusted outcome không cải thiện.

---

# 15. Hard rules nên áp dụng ngay

## Rule 1 — No same-frame retry after material counterevidence

```text
SAME PROBLEM + MATERIAL COUNTEREVIDENCE
→ explain contradiction
→ update Frame
→ new discriminator
→ only then mutate
```

Đây là rule có direct linkage mạnh nhất với Golden HR false closure/rework.

## Rule 2 — No oracle below the claim abstraction

Nếu claim là UI/live finance outcome, generic helper/unit proof không đủ.

## Rule 3 — No memory reuse without applicability check

Case similarity không cấp authority.

## Rule 4 — No new metric without a decision

Metric không đổi decision = telemetry debt.

## Rule 5 — No new architecture without natural bottleneck evidence

Mọi capability mới phải trả lời:

```text
Observed bottleneck?
Why current mechanism insufficient?
What smallest artifact can test the hypothesis?
Which metric decides retain/remove?
```

---

# 16. Những thứ KHÔNG nên xây lúc này

1. Public “problem framing” MCP tool thứ 9;
2. Problem Governance Engine mới;
3. universal AI memory service;
4. vector database cho toàn bộ transcript;
5. full code knowledge graph platform;
6. LSP-first rewrite;
7. second PRL database;
8. giant smart router;
9. multi-agent expansion mặc định;
10. proof-cache optimization program;
11. additional RUN/WAVE states;
12. automatic treatment/promotion trước P5 evidence;
13. full upstream merge chỉ để “có feature”.

---

# 17. First implementation slice đề xuất

Nếu phải chọn **một** artifact để bắt đầu ngay sau tài liệu này, không chọn Case DB hay Graph Engine.

Chọn:

> **Resolution State Capsule + bounded Workspace Evidence lookup cho một natural HR Finance problem.**

Lý do:

- capsule giải quyết context reconstruction trực tiếp;
- bounded evidence lookup giải quyết localization trực tiếp;
- case memory có thể bắt đầu bằng 7 Golden HR records dạng file/research artifact, chưa cần service;
- hai artifact này đủ để kiểm hypothesis trên một problem thật;
- nếu không giảm TTPR/localization/rework, có thể dừng mà không tạo platform debt.

Minimal treatment package:

```text
1 Problem Revision
1 current Capsule
1 bounded Evidence Index slice
≤ 3 retrieved prior cases
1 explicit F0
1 decision-changing discriminator
1 causal intervention
1 matching live oracle
1 closure falsifier
1 independent outcome
```

Đây là kích thước đủ nhỏ để falsify ý tưởng EGRI.

---

# 18. Decision matrix — so sánh các hướng có thể chọn

| Hướng | Evidence nội bộ | Expected leverage | Risk overengineering | Quyết định |
|---|---:|---:|---:|---|
| Thêm recovery/control | thấp sau P0.6 | thấp | cao | Freeze, chỉ fix defect |
| Smart router/model expansion | P4/P5 chưa đủ | chưa biết | cao | Không promote |
| Proof cache | hit gần 0 | thấp | trung bình | Không đầu tư |
| LSP-first | live binding chưa ready | trung bình | cao | Không chọn |
| Full Workspace Intelligence platform | localization bottleneck có thật | cao tiềm năng | rất cao | Chỉ MVP slice |
| Raw conversation memory | dữ liệu đã quá nhiều | thấp | cao | Không chọn |
| Resolution Case Memory | Golden HR rất phù hợp | cao | trung bình | Làm derived prototype |
| Resolution State Capsule | context reconstruction có thật | cao | thấp | **Ưu tiên** |
| Counterevidence hard gate | false closure/reopen có thật | cao | thấp | **Áp dụng ngay ở controller** |
| Natural HR prospective cohort | thiếu trusted outcome evidence | rất cao | thấp | **Ưu tiên số 1 về validation** |

---

# 19. Logic tree cho mọi problem mới

```text
USER PROBLEM
│
├─ Contract rõ chưa?
│   ├─ Không → productive clarification
│   └─ Có
│
├─ Current truth known?
│   ├─ Không → source/runtime/persistence/projection discriminator
│   └─ Có
│
├─ Prior case applicable?
│   ├─ Có → use as hypothesis prior, never authority
│   └─ Không → fresh frame
│
├─ A*/G/Owner/H settled enough?
│   ├─ Không → decision-changing discriminator
│   └─ Có
│
├─ Small causal intervention exists?
│   ├─ Không → revise boundary/architecture hypothesis
│   └─ Có → execute under EOCL as required
│
├─ Matching oracle passes?
│   ├─ Không → counterevidence → frame update
│   └─ Có
│
├─ Closure falsifier passes?
│   ├─ Không → reopen frame
│   └─ Có
│
└─ Independent/user outcome?
    ├─ confirmed → RESOLVED_CONFIRMED → distill
    ├─ same problem failing → REOPEN SAME REVISION → revise frame
    └─ contract changed → REVISE
```

---

# 20. Tư duy điều phối model/tool

EGRI không thay routing policy hiện hữu. Nó làm packet tốt hơn để bất kỳ executor hợp lệ nào ít phải reconstruct hơn.

## Deterministic tools

Dùng cho:

- exact state;
- index build/update;
- source/hash/dependency lookup;
- tests/oracles;
- diff/proof.

## Model

Dùng cho:

- semantic contract synthesis;
- causal frame;
- competing hypotheses;
- interpretation of counterevidence;
- scope/architecture tradeoff.

## Sol/controller

Giữ:

- authority;
- business semantic reconciliation;
- integration width;
- acceptance;
- false-closure judgment;
- policy promotion.

Mục tiêu không phải route sang model rẻ hơn ngay; mục tiêu đầu tiên là **giảm context/rework cho cùng chất lượng route**.

---

# 21. Threats to validity

## 21.1. Selection bias

Golden HR cases được chọn vì có evidence tốt có thể không đại diện toàn bộ workload. Cần prospective consecutive cases.

## 21.2. Historical reconstruction bias

Các case cũ thiếu outcome timestamps/common clocks; không được backfill false precision.

## 21.3. Hawthorne/learning effect

Operator/model có thể tốt lên theo thời gian bất kể treatment. Dùng paired/blocked design và hold source/task/oracle càng nhiều càng tốt.

## 21.4. Confounding từ model/version/cache

Thay model/runtime cùng lúc với methodology sẽ làm attribution mơ hồ.

## 21.5. Negative transfer

Case Memory có thể khiến AI bám vào solution cũ. Applicability + falsifier + counterevidence phải mạnh hơn retrieval similarity.

## 21.6. Overcompression

Capsule quá ngắn có thể mất constraint quan trọng. Vì vậy protected invariants và unresolved conditions là mandatory.

## 21.7. Metric gaming

Giảm TTPR bằng cách hạ acceptance quality là thất bại. Trusted outcome và safety floors phải lexicographically đứng trước speed.

---

# 22. Bản đồ tri thức cần giữ lâu dài

Tri thức lâu dài nên chia:

```text
DOMAIN KNOWLEDGE
  business invariants / terminology / authority

WORKSPACE KNOWLEDGE
  owner / symbol / data flow / oracle / test

PROBLEM KNOWLEDGE
  revision / frame / counterevidence / current gap

RESOLUTION EXPERIENCE
  case / discriminator / intervention / outcome / applicability

EXECUTION EVIDENCE
  exact source/runtime/proof/checkpoint
```

Không một lớp nào được masquerade thành lớp khác.

Ví dụ:

- “quyết toán là final entitlement” = domain invariant;
- “Finance hero đọc selector X” = workspace knowledge;
- “R1 vẫn sai sau patch A” = problem counterevidence;
- “double-count từng xảy ra khi aggregation Y + settlement Z” = case experience;
- “test 123 pass trên SHA abc” = execution evidence.

Sự phân tách này là nền tảng để tránh stale knowledge và false proof reuse.

---

# 23. Breakthrough thesis

Điểm đột phá tiềm năng của Codex-web không nằm ở việc có nhiều tool/model hơn.

Nó nằm ở khả năng thực hiện chu trình sau tốt hơn coding agents thông thường:

```text
Understand contract
→ remember exact problem state
→ retrieve only applicable prior experience
→ locate causal surface quickly
→ run discriminator before expensive mutation
→ change minimum sufficient boundary
→ prove at the same abstraction as the claim
→ use user counterevidence as authoritative reopen signal
→ retain the lesson in reusable decision memory
```

Nếu chu trình này làm được qua nhiều natural cases, Codex-web chuyển từ:

> **Trusted Execution Platform**

sang:

> **Learning Trusted Problem Resolution System**.

Đây mới là moat đáng theo đuổi.

---

# 24. Definition of Done cho giai đoạn tiếp theo

Không coi EGRI “xong” khi code được merge.

Giai đoạn tiếp theo chỉ hoàn thành khi có:

1. ≥ 5 natural HR cases có Problem Revision trước first material write;
2. 100% case có explicit F0 (`A* / G / H`);
3. material counterevidence không có same-frame mutation retry không giải thích;
4. 100% full-problem claims có oracle matching abstraction;
5. Resolution Capsule dùng được trong ít nhất một context-resumption test;
6. Workspace Evidence Index MVP chứng minh giảm repeated localization trên target family;
7. case distillation chứa applicability + negative transfer;
8. ít nhất một independent/user confirmed Trusted Resolution;
9. measurement packet đủ để chạy P5 A/A mà không hard-stop vì instrumentation/source drift;
10. không thêm public tool/state/authority object nếu chưa có natural evidence bắt buộc.

Sau đó mới được hỏi:

> “Treatment EGRI có causal benefit không?”

và chuyển sang A/A → A/B.

---

# 25. Recommended implementation order

```text
M0  Freeze new machinery
    ↓
M1  Distill 7 Golden HR cases
    ↓
M2  Enforce counterevidence doctrine at controller level
    ↓
M3  Resolution State Capsule MVP
    ↓
M4  Bounded Workspace Evidence Index for HR Finance family
    ↓
M5  First prospective natural case
    ↓
M6  5–10 case natural cohort
    ↓
M7  P5 A/A instrumentation validation
    ↓
M8  Controlled A/B methodology experiment
    ↓
M9  Promote / simplify / remove based on TTPR + trusted outcome
```

Không đảo M7/M8 lên trước M5/M6. Không build M4 thành full platform trước khi M5 chứng minh leverage.

---

# 26. Research questions chính thức

## RQ1 — Knowledge conversion

**Một Resolution State Capsule có giảm thời gian context reconstruction/localization mà không làm tăng wrong-frame rate không?**

## RQ2 — Repository intelligence

**Một bounded Workspace Evidence Index có giảm localization time và wrong-target navigation trên HR Finance family không?**

## RQ3 — Case learning

**Resolution Case Memory có làm giảm repeated causal mistakes mà không tăng negative transfer không?**

## RQ4 — Counterevidence discipline

**No-same-frame-retry rule có giảm avoidable repair/reopen không?**

## RQ5 — Combined system effect

**EGRI treatment có giảm TTPR và tăng First-Pass Trusted Resolution so với current control khi model/route/oracle/source được giữ tương đương không?**

---

# 27. Research references

Các nguồn dưới đây là nền tảng thiết kế; chúng không thay thế empirical proof nội bộ.

1. **Aamodt, A., & Plaza, E. (1994).** *Case-Based Reasoning: Foundational Issues, Methodological Variations, and System Approaches.* AI Communications, 7(1), 39–59. DOI: https://doi.org/10.3233/AIC-1994-7104  
   → Cơ sở cho retrieve–reuse–revise–retain và Resolution Case Memory.

2. **Hevner, A. R., March, S. T., Park, J., & Ram, S. (2004).** *Design Science in Information Systems Research.* MIS Quarterly, 28(1), 75–106. DOI: https://doi.org/10.2307/25148625  
   → Build artifact + evaluate in real environment; phù hợp natural HR validation.

3. **LaToza, T. D., Venolia, G., & DeLine, R. (2006).** *Maintaining Mental Models: A Study of Developer Work Habits.* ICSE 2006, 492–501. DOI: https://doi.org/10.1145/1134285.1134355  
   → Evidence về chi phí reconstruct implicit repository knowledge.

4. **Parnin, C., & Rugaber, S. (2011).** *Resumption Strategies for Interrupted Programming Tasks.* Software Quality Journal, 19(1), 5–34.  
   → Cơ sở cho bounded resumption capsule thay vì replay lịch sử.

5. **Sillito, J., Murphy, G. C., & De Volder, K. (2008).** *Asking and Answering Questions during a Programming Change Task.* IEEE Transactions on Software Engineering, 34(4), 434–451. DOI: https://doi.org/10.1109/TSE.2008.26  
   → Repository intelligence nên answer developer questions, không chỉ search text.

6. **Zeller, A., & Hildebrandt, R. (2002).** *Simplifying and Isolating Failure-Inducing Input.* IEEE Transactions on Software Engineering, 28(2), 183–200. DOI: https://doi.org/10.1109/32.988498  
   → Nền tảng systematic discrimination/delta debugging.

7. **Runeson, P., & Höst, M. (2009).** *Guidelines for Conducting and Reporting Case Study Research in Software Engineering.* Empirical Software Engineering, 14, 131–164. DOI: https://doi.org/10.1007/s10664-008-9102-8  
   → Thiết kế Golden HR natural case studies và threats to validity.

8. **Kitchenham, B. A., Pfleeger, S. L., Pickard, L. M., Jones, P. W., Hoaglin, D. C., El Emam, K., & Rosenberg, J. (2002).** *Preliminary Guidelines for Empirical Research in Software Engineering.* IEEE Transactions on Software Engineering. DOI: https://doi.org/10.1109/TSE.2002.1027796  
   → Discipline cho study design, measurement và reporting.

9. **Basili, V. R., Caldiera, G., & Rombach, H. D. (1994).** *Goal Question Metric Paradigm / GQM Approach.*  
   → Metric phải bắt đầu từ goal và question; hỗ trợ rule “no metric without decision”.

10. **Applications of statistical causal inference in software engineering (2023).** Information and Software Technology, 159, 107198. DOI: https://doi.org/10.1016/j.infsof.2023.107198  
    → Phân biệt causal inference và association; hỗ trợ P4 descriptive → P5 experimental boundary.

11. **Furia, C. A., & Torkar, R. (2026).** *Mitigating omitted variable bias in empirical software engineering.* Empirical Software Engineering, 31, Article 123.  
    → Explicit causal models, confounders và sensitivity analysis trước causal claims.

12. **Coding-web internal evidence.** `docs/CURRENT_STATE.md`, `docs/ROADMAP.md`, Revision 4 methodology, Breakthrough Implementation Methodology, Target-State Gap Analysis, Golden HR Resolution Cases Calibration V1.  
    → Dữ liệu nội bộ là authority cho current project diagnosis; external literature chỉ là design/research basis.

---

# 28. Final strategic judgment

Dự án không cần thêm một tầng “trí tuệ” mang tính khẩu hiệu. Nó cần một cơ chế nhỏ nhưng có kỷ luật để biến bằng chứng thành learning.

Phương án được chọn là:

> **EGRI = Resolution State Capsule + Bounded Workspace Evidence Index + Resolution Case Memory + Counterevidence Discipline + Natural Causal Evaluation.**

Nó tận dụng trực tiếp những thứ Codex-web đã xây tốt:

- exact identity;
- PRL;
- EOCL;
- proof/checkpoint;
- runtime currentness;
- telemetry;
- Golden HR cases.

Và nó tấn công trực tiếp phần còn yếu:

- repeated localization;
- stale mental model;
- wrong Problem Frame;
- oracle mismatch;
- same-frame repair;
- false closure;
- context reconstruction;
- failure to turn history into reusable knowledge.

Nếu EGRI không làm TTPR/rework/localization tốt lên trên natural workload, phải **thu nhỏ hoặc loại bỏ**, không mở rộng thêm machinery.

Nếu nó làm được, Codex-web sẽ có một khác biệt thực chất: mỗi problem được giải không chỉ tạo code mới, mà còn làm hệ thống **giỏi hơn một cách kiểm chứng được ở problem tiếp theo**.

Đó là hướng đột phá đáng theo đuổi nhất từ bằng chứng hiện tại.
