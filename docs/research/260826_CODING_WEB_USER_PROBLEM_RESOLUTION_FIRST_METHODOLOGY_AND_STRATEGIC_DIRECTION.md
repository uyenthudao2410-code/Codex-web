# CODING WEB — USER-PROBLEM-RESOLUTION-FIRST METHODOLOGY AND STRATEGIC DIRECTION

**Ngày tổng hợp:** 2026-08-26  
**Bản sửa đổi:** REVISION 2 — tích hợp evidence trực tiếp từ `E:\DEV\HR STA\HR\.coding-tools`  
**Loại tài liệu:** methodological proposition / strategic doctrine / research working paper  
**Trạng thái:** tài liệu để tiếp tục phản biện và kiểm chứng; **không tự động tạo runtime policy mới**  
**Mục đích:** tổng hợp tri thức từ lịch sử triển khai Coding Web/Coding Tools, các postmortem, audit định lượng, PRL/EOCL, các nghiên cứu Resolution Compiler/Problem Algebra, **ledger thực tế của dự án HR**, và tinh thần trao đổi mới nhất để xác định lại **đúng bài toán cần tối ưu**.

> **Mệnh đề trung tâm:** Coding Tools không tồn tại để tạo ra nhiều technical acceptance hơn. Nó tồn tại để **giải quyết đúng vấn đề thực tế mà người dùng cần giải quyết, với ít quyết định sai, ít rework và thời gian đến kết quả tin cậy ngắn nhất**.

---

# 0. Executive thesis

## 0.1. Đích tối ưu phải được nâng từ “accepted engineering outcome” lên “trusted user problem resolution”

Lịch sử dự án đã đi qua nhiều giai đoạn:

```text
coding assistant
    ↓
execution/orchestration tool
    ↓
authority + recovery + proof harness
    ↓
evidence-driven accepted-result platform
    ↓
NEXT:
user-problem-resolution optimization system
```

Các primitive kỹ thuật như EOCL, RUN/WAVE, proof fingerprint, source identity, Recovery, exact-source packaging, workspace authority và deterministic MCP đã giải quyết nhiều vấn đề thật. Nhưng chính kinh nghiệm thực tế ở Coding Web và các dự án được Coding Tools phục vụ chỉ ra một giới hạn quan trọng:

```text
CODE CORRECT
    ≠
TECHNICAL ACCEPTANCE
    ≠
USER PROBLEM RESOLVED
```

Một task có thể:

- build PASS;
- tests PASS;
- diff hợp lệ;
- EOCL ACCEPTED;
- package đúng fingerprint;

nhưng người dùng vẫn nói:

> “Vẫn sai.”  
> “Vẫn không hiển thị.”  
> “Logic vẫn chưa đúng.”  
> “Tôi yêu cầu giải quyết triệt để, không phải sửa từng đoạn.”

Trong trường hợp đó, kết luận đúng ở cấp problem là:

```text
PROBLEM = UNRESOLVED
```

Technical proof vẫn có giá trị như evidence, nhưng **không được dùng để thay thế outcome mà người dùng cần**.

---

## 0.2. North Star mới

Từ nay, North Star nên được hiểu là:

> **Minimize Time to Trusted Problem Resolution while preserving correctness, security, authority, business semantics and truthful evidence.**

Ký hiệu làm việc:

```text
TTPR = Time to Trusted Problem Resolution
```

Không tối ưu trực tiếp:

```text
model latency
cost/call
tokens/call
worker count
test count
LOC
CPU utilization
server offload ratio
accepted RUN count
```

Các chỉ số trên chỉ có ý nghĩa nếu cuối cùng giúp:

```text
problem understood correctly
+ causal intervention correct
+ user-visible outcome achieved
+ proof truthful
+ rework reduced
+ TTPR reduced
```

---

## 0.3. Thứ tự ưu tiên chính thức

```text
1. SOLVE THE ACTUAL USER PROBLEM
2. SOLVE IT CAUSALLY / FIRST-PASS WHEN POSSIBLE
3. SOLVE IT FAST
4. PROVE IT TRUTHFULLY
5. ONLY THEN OPTIMIZE MODEL / COMPUTE / TOKEN / ROUTING ECONOMICS
```

Nếu mục 1 thất bại, các tối ưu phía sau gần như vô nghĩa đối với người dùng.

---

## 0.4. HR phải được coi là natural laboratory cho research về problem resolution

Dự án HR tại:

```text
E:\DEV\HR STA\HR
```

không phải benchmark được tạo để làm đẹp một metric. Đây là hệ thống có đủ những điều kiện làm long-horizon engineering trở nên khó trong thực tế:

- business semantics thật: dự án, doanh thu, thanh toán, quyết toán, công nợ, hồ sơ, nhân sự, đơn vị quản lý;
- UI và backend cùng thay đổi;
- SharePoint/external state và local runtime cùng tồn tại;
- worktree có concurrent changes;
- runtime generation có thể stale;
- multi-workspace/authority từng gây nhầm context;
- user liên tục kiểm tra outcome thật và sửa lại cách hiểu khi technical implementation chưa phản ánh đúng nghiệp vụ;
- cùng một user problem có thể bị chia thành nhiều RUN kỹ thuật khác nhau.

Vì vậy HR có giá trị đặc biệt cho thesis của Coding Tools:

> **Nếu một phương pháp không làm những vấn đề HR thật được hiểu đúng hơn, giải quyết first-pass nhiều hơn và đi tới outcome tin cậy nhanh hơn, thì chưa có lý do gọi nó là bước tiến cho Coding Tools.**

HR không thay thế controlled experiment. Nó đóng vai trò **representative natural workload** để tìm failure pattern, first divergence point, false closure và hidden orchestration tax trước khi thiết kế experiment sạch hơn.

---

# 1. Evidence lịch sử dẫn tới thay đổi phương pháp luận

Phần này không trình bày các con số như trạng thái live ngày 26/08. Đây là **các snapshot lịch sử có provenance riêng**, dùng để rút ra bài học phương pháp luận.

## 1.1. Incident 13/08 — policy đúng nhưng execution drift

Postmortem PFM ngày 13/08 chỉ ra một vấn đề nền tảng:

> **Policy đúng nhưng runtime không enforce policy.**

Trong execution thật từng xuất hiện:

- Desktop/coordination được dự kiến nhưng readiness không đủ;
- deep-code lane thất bại nhưng không luôn bắt buộc REPLAN trước khi strategy thay đổi;
- controller dần biến thành writer;
- packet bị chia theo file/hunk thay vì behavior có oracle;
- shared checkout drift làm candidate patch mất context;
- proof wrapper dài khiến phần proof đã PASS bị chạy lại;
- telemetry chưa đủ để định lượng accepted-result economics.

Kết quả quan trọng nhất từ incident đó là EOCL:

```text
PREFLIGHT
→ READY
→ ROUTED
→ EXECUTING
→ PROVING
→ ACCEPTING
→ CHECKPOINTED

exception:
REPLAN / BLOCKED / ABORTED
```

Bài học còn nguyên giá trị:

> **Các nguyên tắc quan trọng phải nằm trong state/evidence/authority, không chỉ trong lời nhắc.**

Nhưng bài học mới hơn là: authority correctness vẫn chưa đồng nghĩa user-problem correctness.

---

## 1.2. Audit 17/08 — rework đắt hơn execution optimization

Một cohort lịch sử gồm 188 accepted organic ChatWeb+MCP runs ghi nhận:

```text
first-pass accepted = 130 / 188 = 69.15%
repaired            = 58 / 188 = 30.85%
first-pass TTA p50  = 36.357 s
repaired TTA p50    = 192.319 s
median penalty      ≈ 5.29x
```

Một cohort khác có task mix khác ghi first-pass 59.8% và repaired 40.2%. Hai cohort không đồng nhất nên không được dùng để kết luận regression causal. Tuy nhiên chúng cùng chỉ ra một sự thật kinh tế:

> **Nếu một optimization tiết kiệm vài giây execution nhưng làm xác suất rework tăng, tổng thời gian tới kết quả có thể xấu đi mạnh.**

Điều này thay đổi objective:

```text
NOT:
minimize execution_ms

BUT:
minimize expected total work to trusted resolution
```

---

## 1.3. Audit 17/08 — localization và orchestration là chi phí material

Snapshot lịch sử cũng ghi:

```text
local execution ≈ 7.59 h
estimated wait  ≈ 24.95 h
wait/local      ≈ 3.28x
```

và trong measured phase timing:

```text
localization ≈ 59.5%
workspace    ≈ 8.3%
materialize  ≈ 0.2%
```

Các con số không chứng minh toàn bộ wait là model latency, nhưng đủ bác bỏ giả thuyết đơn giản:

> “Muốn nhanh thì chỉ cần model nhanh hơn hoặc server mạnh hơn.”

Nếu thời gian mất ở:

- tìm sai nơi;
- đọc quá rộng;
- chẩn đoán sai;
- patch sớm;
- review/proof dư;
- context reconstruction;
- replan;

thì tối ưu model-call latency không đánh đúng critical path.

---

## 1.4. Một subsystem kỹ thuật ổn không đồng nghĩa có ROI

Ví dụ lịch sử:

```text
LSP attempted = 963
LSP handled   = 5
```

Resource lifecycle của LSP được harden tốt, nhưng semantic usefulness chưa được chứng minh tương ứng.

Generic proof-cache cũng từng có:

```text
eligible = 563
hits     = 1
saved    = 996 ms
```

Bài học:

> **Không đánh giá feature bằng mức độ hoàn thiện kỹ thuật; đánh giá bằng contribution vào problem resolution economics.**

---

## 1.5. PRL/ledger 25/08 — execution history lớn nhưng problem-level truth còn mỏng

Một immutable ledger snapshot ngày 25/08 ghi:

```text
RUN total          = 923
WAVE total         = 1,430
WAVE replanned     = 511
failure_observed   = 656
```

Trong snapshot PRL v10 tại thời điểm đó:

```text
problem_threads    = 0
problem_events     = 1
policy-eligible    = 0
exact primary bind = 0
```

Các phiên sau đã tiếp tục phát triển PRL v11/source-ready natural canary, nhưng bài học không thay đổi:

> **Execution telemetry rất lớn không tự biến thành knowledge về việc problem của người dùng đã được giải quyết hay chưa.**

Đây là lý do đơn vị phân tích phải chuyển dần từ:

```text
RUN / WAVE
```

sang:

```text
Problem Revision / User Outcome
```

RUN/WAVE vẫn là đơn vị execution authority. Chúng không phải đơn vị cuối cùng của product success.

---

## 1.6. Evidence trực tiếp từ HR `.coding-tools` — technical ledger dày nhưng problem truth còn thiếu

Ngày 26/08/2026, một read-only transaction được thực hiện trực tiếp trên:

```text
E:\DEV\HR STA\HR\.coding-tools\orchestration\ledger.sqlite3
```

Snapshot được khóa trong cùng transaction tại:

```text
max event seq  = 4481
max event time = 2026-08-26T04:18:03.551Z
```

Các số liệu dưới đây là **snapshot của ledger tại thời điểm query**, không phải claim bất biến về trạng thái sau thời điểm đó.

### 1.6.1. Execution activity rất lớn so với số accepted closure

```text
RUN total      = 256
  accepted     = 34
  active       = 169
  stale        = 36
  aborted      = 17

WAVE total     = 278
  accepted     = 34
  active       = 169
  replanned    = 22
  aborted      = 53

EVENT total    = 4481
PROOF total    = 161
  passed       = 134
  failed       = 27

CHECKPOINT     = 34
  accepted     = 34
```

Có 16/256 runs có nhiều hơn một wave.

Accepted RUN có elapsed time trung bình khoảng:

```text
avg ≈ 156.7 s
min ≈ 15.0 s
max ≈ 366.9 s
```

Nhưng **không được suy diễn** từ con số này rằng user problem được giải trong 156.7 giây. Đó chỉ là thời gian của technical RUN đã terminal accepted.

### 1.6.2. 134 proof PASS nhưng chỉ 34 accepted RUN — và accepted vẫn chưa phải user resolution

Quan hệ thực tế trong HR ledger là:

```text
134 passed proofs
        ↓
34 accepted technical checkpoints
        ↓
? confirmed user problem resolutions
```

Dấu `?` là điểm quan trọng nhất.

Trong inventory tables của ledger tại snapshot này không có một problem-lineage table độc lập chứa confirmed user-resolution denominator. Event inventory cũng chưa cung cấp một lớp user outcome đủ để biến accepted RUN thành resolved Problem Revision.

Do đó ledger HR trực tiếp chứng minh một giới hạn:

> **Execution proof density có thể rất cao trong khi product-resolution truth vẫn không đo được.**

Đây không phải lỗi của EOCL. EOCL đang làm đúng việc của nó: execution authority, proof và technical closure. Thiếu hụt nằm ở **problem/outcome plane**.

### 1.6.3. `quality_outcome_recorded` hiện chưa phải user-outcome evidence

Snapshot có:

```text
quality_outcome_recorded = 31
oracle_pass=true         = 31
```

Nhưng sample payload cho thấy provenance:

```json
{
  "oracle_pass": true,
  "source": "accepted_proof_auto_v1"
}
```

Nghĩa là quality signal này được auto-derived từ accepted technical proof.

Vì vậy:

```text
quality_outcome_recorded
!= independent user outcome confirmation
```

Nếu dùng nó làm numerator cho Trusted Problem Resolution, ta sẽ tạo circular metric:

```text
technical proof accepted
→ auto quality oracle_pass
→ dùng oracle_pass để chứng minh technical acceptance là user resolution
```

Cách đó không hợp lệ.

**Phương pháp luận bắt buộc phải phân biệt provenance của oracle:**

```text
TECHNICAL_ORACLE
INTEGRATION_ORACLE
RUNTIME_ORACLE
USER_OUTCOME_ORACLE
BUSINESS_SEMANTIC_ORACLE
```

Chỉ những oracle phù hợp với acceptance contract của Problem Revision mới được phép đóng user problem.

### 1.6.4. Strong oracle còn hiếm trong observed preflight

Trong 36 `oracle_preflight` events ở snapshot:

```text
strong_oracle = true   : 2
strong_oracle = false  : 34
verification = none    : 14
```

Không được diễn giải 34 weak-oracle preflight là 34 sai lầm, vì nhiều technical wave có thể hợp lệ mà không cần broad verification.

Nhưng nó củng cố một câu hỏi nghiên cứu rất quan trọng:

> **Trong các user problems bị reopen hoặc phải sửa nhiều lượt, strong outcome oracle đã được xác định từ đầu hay chưa?**

Đây cần trở thành một annotation field trong divergence study.

### 1.6.5. Failure telemetry hiện mô tả operational symptom tốt hơn causal meaning

Snapshot có 61 `failure_observed` events.

Các lớp lớn nhất:

```text
CHECK_FAILED                  21
SOL_REJECTED                   6
BUILD_VERIFICATION_FAILED      6
CANDIDATE_MODEL_NOT_COMPLETED  5
PROMPT_TOO_LARGE               4
PERMISSION_REQUIRED            4
CANDIDATE_SCOPE_MISSING        4
BASE_DRIFT                     3
RUNTIME_RESUME_REQUIRED        2
PATCH_CONTEXT_NOT_FOUND        1
PATCH_AMBIGUOUS                1
MODE_ROUTE_MISMATCH            1
EXECUTION_OWNER_INVALID        1
...
```

Quan trọng hơn, trong chính 61 failure observations:

```text
p2 causal attribution = unattributed : 27
p2 causal attribution = absent       : 34
```

Tức tại snapshot này, **không có failure observation nào trong cohort 61 được materialize thành causal attribution đủ cụ thể trong P2 field**.

Điều đó không có nghĩa agent không biết nguyên nhân trong prose/replan reason. Nhiều replan reason thực tế rất cụ thể. Nhưng machine-usable telemetry chưa biến được chúng thành causal knowledge.

Bài học:

> **Error code history chưa phải decision science.**

Để học cách giải user problem nhanh hơn, cần biết:

```text
what was uncertain?
what observation was taken?
what hypothesis was eliminated?
what action followed?
did user outcome improve?
```

chứ không chỉ:

```text
CHECK_FAILED
BUILD_FAILED
SOL_REJECTED
```

### 1.6.6. Replan history cho thấy một lượng đáng kể work dùng để vượt qua transport/control-plane friction

Representative `wave_replanned` reasons trong HR bao gồm:

- Node test-runner IPC deserialization;
- test fixture MST sai format làm validator trả 400 trước cardinality logic;
- `.txt` entrypoint bị Node 24 từ chối;
- monolithic patch hunks sai source order;
- unified-diff hunk count bị corrupt;
- command chạy trước khi helper file được materialize;
- PowerShell quoting;
- HTTP health proof cần scoped network permission;
- repository HEAD advanced nên phải rebind fingerprint;
- missing Solution Shadow gate;
- workflow admission mismatch;
- Sol lane `ExceptionGroup` trước write lease rồi chuyển deterministic exact-source patch.

Đây là những recovery hợp lý và EOCL đã buộc strategy delta thay vì retry mù.

Nhưng từ perspective user problem:

```text
transport recovery work
+ governance recovery work
+ harness recovery work
```

là **resolution overhead** nếu nó không trực tiếp làm giảm uncertainty của user problem.

Do đó TTPR phải tính loại work này vào denominator kinh tế; không được ẩn nó ngoài technical execution time.

### 1.6.7. Technical proof, acceptance governance và user resolution là ba tầng khác nhau

HR ledger có những failure samples kiểu:

```text
all source-hardening proofs pass
BUT
final acceptance blocked by ACCEPTANCE_FILE_ATTESTATION_REQUIRED
```

và:

```text
deterministic behavior proof is green
BUT
acceptance blocked because source mutation lacks accepted file receipts
```

Điều này là **tốt** về governance: proof không được tự vượt qua provenance gate.

Nhưng nó cũng làm rõ ba tầng:

```text
TECHNICAL BEHAVIOR PROVEN
        ≠
EXECUTION ACCEPTANCE VALID
        ≠
USER PROBLEM RESOLVED
```

Coding Tools phải giữ cả ba, nhưng product North Star phải nằm ở tầng thứ ba.

### 1.6.8. HR cho thấy semantic problem bị fragment thành nhiều technical RUN

Keyword activity trong 256 RUN tại snapshot:

```text
US-123       : 17 runs
ManagingUnits: 19 runs
finance      : 114 runs
revenue      : 72 runs
payment      : 58 runs
settlement   : 62 runs
```

Các cluster này **chồng lấn nhau**, nên tuyệt đối không được đọc như số problem độc lập.

Chính sự chồng lấn là evidence quan trọng:

> **RUN identity không khớp semantic problem identity.**

Một user problem về finance/revenue/settlement có thể sinh ra:

```text
implementation RUN
proof-only RUN
runtime activation RUN
fresh closure RUN
formatting repair RUN
source-attestation closure RUN
live dry-run RUN
controlled external mutation RUN
```

Accepted objectives thực tế trong HR cho thấy đúng cấu trúc này. Ví dụ quanh PFM đã có các accepted RUN riêng cho:

- narrow modal responsiveness;
- settlement auto-calculation;
- combined responsiveness + settlement work;
- broad verification only;
- user-visible PFM correctness defects;
- formatting-only repair.

Ở US-123/ManagingUnits lại có các accepted RUN riêng cho:

- runtime activation;
- package-script proof support;
- read-only closure verification;
- canonical baseline;
- source closure;
- live dry-run;
- controlled production backfill.

Không run nào tự nó đại diện đầy đủ cho toàn bộ user journey.

### 1.6.9. Exact-objective equality không đủ để nối problem history

Trong ledger snapshot, exact duplicate objective rất ít; trong một query chỉ thấy một duplicate pair rõ ràng, trong khi semantic clusters finance/revenue/payment/settlement chứa hàng chục RUN.

Điều này bác bỏ cách linkage ngây thơ:

```text
same objective text
→ same problem
```

Problem continuity cần dựa trên:

```text
semantic contract
+ target/outcome continuity
+ user feedback
+ acceptance criteria
+ causal lineage
```

không dựa trên string equality.

### 1.6.10. Stale truth có nhiều projection — không được ép thành một con số duy nhất

Runtime snapshot ở cùng workspace báo:

```text
stale_orchestration_runs            = 70
unresolved_stale_orchestration_runs = 70
task_orchestration_projection_reconciled = false
```

Trong read transaction của `runs` table:

```text
status='stale' = 36
```

Hai con số này không được gọi là “mâu thuẫn” khi chưa chứng minh chúng cùng definition/time window/projection.

Đây là một ví dụ sống cho methodological hierarchy of truth:

> **Observed runtime projection, persisted ledger state và derived census phải giữ provenance riêng; không hợp nhất chúng thành một metric chỉ vì cùng mang nhãn “stale”.**

### 1.6.11. Các plane nâng cao hầu như chưa tạo evidence trong HR cohort này

Tại snapshot:

```text
coordination_messages  = 0
handoff_capsules        = 0
agent_lanes             = 0
experiment_assignments  = 0
p5_assignment_outcomes  = 0
```

Điều này rất quan trọng khi diễn giải lịch sử:

- không được claim HR đã chứng minh multi-agent economics;
- không được claim HR đã có P5 treatment evidence;
- không được claim handoff capsule đã giảm TTPR;
- không được suy ra routing policy tối ưu từ ledger này.

HR hiện mạnh nhất ở vai trò:

```text
natural engineering trajectory evidence
```

chứ chưa phải:

```text
clean causal experiment evidence
```

---

## 1.7. Điều HR bổ sung vào thesis: “technical closure bias” là vấn đề thực, không chỉ lý thuyết

Lịch sử tương tác quanh HR/PFM đã nhiều lần xuất hiện pattern:

```text
technical change completed
→ tests/proof reported green
→ user checks actual screen/business behavior
→ “vẫn sai / vẫn không hiển thị / logic vẫn như cũ”
→ another engineering loop
```

Các nhóm problem từng lặp lại gồm:

- thông tin dự án không truyền/hiển thị nhất quán giữa Project và Finance;
- revenue/payment/settlement semantics bị hiểu lẫn hoặc cộng gộp sai;
- công nợ chuyển qua các phase quyết toán/thanh lý không đúng business meaning;
- trạng thái dự án/hồ sơ chỉnh sửa nhưng UI/runtime không phản ánh như người dùng cần;
- canonical personnel/unit relationships và live runtime generation có thể đúng ở source nhưng không đúng ở process đang phục vụ request;
- UI correctness và business correctness cần kiểm bằng actual data flow, không chỉ component/build proof.

Không nên biến từng câu user correction thành một technical bug class riêng. Pattern chung là:

> **Acceptance contract kỹ thuật đã hẹp hơn problem contract thực tế của người dùng.**

Vì vậy HR làm rõ rằng False Closure không chỉ là:

```text
bad test
```

mà còn có thể là:

```text
wrong problem boundary
wrong outcome oracle
wrong runtime generation
incomplete solution scope
business semantic mismatch
technical proof at the wrong layer
```

Đây là lý do Outcome-First phải đứng **trước** implementation plan, không đứng cuối verification.

---

# 2. Mệnh đề phương pháp luận cốt lõi

## 2.1. Mệnh đề M0 — Technical acceptance là điều kiện cần, không phải điều kiện đủ

```text
TECHNICAL_ACCEPTED(task)
```

chỉ chứng minh rằng một technical claim cụ thể đã đạt proof theo contract của task.

Nó không tự chứng minh:

```text
USER_PROBLEM_RESOLVED(problem_revision)
```

Do đó:

```text
technical acceptance
→ preserves evidence
→ may support outcome resolution
→ never automatically closes user problem
```

---

## 2.2. Mệnh đề M1 — Bắt đầu từ outcome, không bắt đầu từ code

Khi người dùng nêu vấn đề, câu hỏi đầu tiên không phải:

> “Sửa file nào?”

mà là:

> **“Thực tế quan sát được nào sẽ chứng minh vấn đề này đã được giải quyết?”**

Cần xác lập tối thiểu:

```text
USER PROBLEM
DESIRED OUTCOME
RESOLUTION ORACLE
PROTECTED SEMANTICS / INVARIANTS
```

Ví dụ:

```text
Problem:
thông tin dự án mất khi sang tab tài chính

Desired outcome:
thông tin đúng xuất hiện trong tab tài chính

Oracle:
create/edit project
→ save
→ navigate finance
→ expected fields visible
→ reload
→ values remain correct

Protected semantics:
không đổi business meaning của project/revenue/payment
```

Oracle này đồng thời là:

- finish line;
- localization anchor;
- proof target;
- stop condition.

Một thông tin phục vụ bốn chức năng, giúp giảm context và giảm work thừa.

---

## 2.3. Mệnh đề M2 — Tìm divergence boundary trước khi patch

Đối với user-visible problem, trace ngược outcome:

```text
USER OUTCOME
     ↑
UI / consumer
     ↑
normalized state
     ↑
API / transport
     ↑
domain semantics
     ↑
persistence / external source
```

Mục tiêu không phải đọc toàn bộ stack.

Mục tiêu là tìm boundary đầu tiên nơi:

```text
EXPECTED != ACTUAL
```

Boundary đó là localization anchor mạnh hơn việc search repository theo cấu trúc thư mục.

---

## 2.4. Mệnh đề M3 — Discriminator trước intervention khi uncertainty còn material

Nếu tồn tại nhiều nguyên nhân hợp lý:

```text
H1 UI mapper
H2 API response
H3 persistence
H4 stale runtime/cache
```

không nên mặc định patch H1 chỉ vì tìm thấy code nhanh.

Hãy chọn:

> **Cheapest discriminator — phép quan sát rẻ nhất có thể loại bỏ nhiều nhánh sai nhất hoặc thay đổi quyết định tiếp theo mạnh nhất.**

Ví dụ:

```text
inspect persisted record
+ API payload
+ frontend normalized state
```

Nếu:

```text
DB    ✓
API   ✓
state ✗
```

search space co lại ngay trước khi mutation bắt đầu.

---

## 2.5. Mệnh đề M4 — Tối ưu “Expected Remaining Work”, không tối ưu activity

Mục tiêu tại mỗi decision point:

```text
choose next action
that minimizes expected remaining work
to trusted resolution
```

Không dùng score giả precision nếu chưa có calibration.

Không cần một numeric EIG engine ở giai đoạn hiện nay.

Dùng ranking bảo thủ:

```text
HARD FILTERS
1. authority/source/workspace valid?
2. safety/business invariants protected?
3. oracle meaningful?

THEN PREFER
1. action that most reduces decision-relevant uncertainty
2. action that narrows target/root cause
3. cheaper/faster action when equivalent
4. read-only/reversible before mutation when equivalent
5. action that moves directly toward outcome oracle
```

Tên nghiên cứu làm việc:

```text
Resolution Gradient
```

Đây là **principle**, chưa phải một subsystem.

---

## 2.6. Mệnh đề M5 — Mutation phải causal, nhỏ nhưng coherent

Không tối ưu LOC thuần.

Một good intervention là:

```text
smallest coherent change
that fixes demonstrated cause
while preserving required invariants
```

Không:

```text
smallest diff at any cost
```

Một patch 3 dòng tạo reopen có thể đắt hơn một change 50 dòng giải đúng root cause.

---

## 2.7. Mệnh đề M6 — Verify bằng cùng outcome contract đã định nghĩa từ đầu

Proof ladder:

```text
1. focused causal proof
2. affected boundary proof
3. representative consumer/runtime proof
4. broad/release proof only when risk requires
5. user/problem outcome proof
```

Không chạy broad suite như nghi lễ sau mọi patch.

Không coi unit test xanh là user outcome proof nếu failure nằm ở integration/runtime/business semantics.

---

## 2.8. Mệnh đề M7 — User correction có quyền lực epistemic cao hơn technical claim

Nếu technical work được ACCEPTED nhưng người dùng cung cấp evidence rằng original outcome vẫn sai:

```text
technical proof = still valid for what it proved
problem outcome = unresolved
```

Hệ thống phải:

```text
REOPEN same Problem Revision
```

hoặc:

```text
REVISE Problem Revision
```

nếu contract thực sự thay đổi.

Không được tự bảo vệ closure cũ bằng cách viện dẫn test xanh.

---

## 2.9. Mệnh đề M8 — Stop là một decision quan trọng

Hệ thống nhanh phải biết khi nào **không làm thêm**.

Khi:

```text
root cause sufficiently established
+ minimal causal change applied
+ outcome oracle passes
+ required adjacent risk checked
+ no unresolved hard blocker
```

thì:

```text
STOP
```

Không tự động:

```text
review thêm
search thêm
refactor thêm
spawn thêm agent
run broad suite lần nữa
```

nếu acceptance contract không yêu cầu.

---

# 3. Outcome-First Resolution Loop

Đây là loop phương pháp luận đề xuất, không phải runtime FSM mới.

```text
USER REPORTS PROBLEM
        │
        ▼
1. DEFINE OBSERVABLE OUTCOME
        │
        ▼
2. VERIFY TRUTH PLANE
   workspace/source/runtime/authority
        │
        ▼
3. REPRODUCE / OBSERVE FAILURE
        │
        ▼
4. TRACE OUTCOME BACKWARDS
   locate divergence boundary
        │
        ▼
5. CHEAPEST DISCRIMINATOR
   reduce material uncertainty
        │
        ▼
6. CAUSAL INTERVENTION
   smallest coherent change
        │
        ▼
7. TECHNICAL PROOF
        │
        ▼
8. OUTCOME PROOF
   same user-observable contract
        │
        ├── PASS → TRUSTED RESOLUTION → STOP
        │
        └── FAIL → REOPEN / REVISE / NEW EVIDENCE
```

---

# 4. False Closure — failure class phải được theo dõi riêng

## 4.1. Định nghĩa

```text
FALSE CLOSURE =
    technical acceptance or completion claim
followed by
    credible user/runtime evidence
that the original problem remains unresolved
```

False Closure khác:

- new requirement;
- scope expansion;
- independent new bug;
- later regression sau thời gian dài;
- changed external environment.

Cần phân loại để không biến mọi reopen thành lỗi agent.

---

## 4.2. Vì sao False Closure quan trọng hơn test-pass rate

Ví dụ:

```text
technical acceptance rate = 98%
first-pass trusted problem resolution = 63%
false closure rate = 22%
```

Nếu chỉ nhìn acceptance rate, hệ thống có vẻ gần hoàn hảo.

Nếu nhìn user outcome, hệ thống còn vấn đề nghiêm trọng.

Do đó cần metric:

```text
FCR = False Closure Rate
```

trên problem revisions có outcome observation phù hợp.

---

## 4.3. HR bổ sung một dạng bias nguy hiểm: proof-derived outcome

Nếu hệ thống tự tạo:

```text
accepted proof
→ quality_outcome oracle_pass=true
```

thì signal đó hữu ích cho technical quality bookkeeping nhưng **không được phép đóng Problem Revision** nếu user outcome chưa được quan sát ở tầng phù hợp.

Do đó mỗi resolution oracle phải có provenance tối thiểu:

```text
oracle_type
oracle_source
observed_target
problem_revision
contract_fingerprint
source/runtime fingerprint where applicable
independent_from_acceptance? true/false
```

Mục tiêu không phải tạo schema phức tạp. Mục tiêu là ngăn một lỗi logic rất cơ bản:

> **Không dùng chính technical acceptance làm bằng chứng độc lập rằng technical acceptance đã giải user problem.**

---

# 5. Primary unit of analysis: Problem Revision

## 5.1. RUN/WAVE vẫn cần, nhưng không phải product denominator

RUN/WAVE trả lời:

```text
ai thực thi?
trên source nào?
authority nào?
proof nào?
trạng thái execution gì?
```

Problem Revision trả lời:

```text
người dùng đang cần giải vấn đề gì?
contract nào?
outcome nào?
đã thật sự resolved chưa?
```

Do đó:

```text
RUN/WAVE = execution unit
Problem Revision = outcome unit
```

---

## 5.2. Terminal Success Bias

Nếu chỉ phân tích accepted RUN:

```text
accepted tail looks healthy
```

nhưng các trajectory:

```text
active
stale
aborted
awaiting user
reopened
unbound
```

có thể biến mất khỏi denominator.

Problem-level funnel khắc phục bias này.

---

## 5.3. HR chứng minh RUN fragmentation là structural, không phải edge case

Trong HR snapshot, semantic activity về `finance`, `revenue`, `payment`, `settlement`, `US-123` và `ManagingUnits` trải qua nhiều RUN khác nhau, trong khi exact objective duplicate rất ít.

Vì vậy linkage tương lai phải làm được:

```text
many technical runs
        ↓
one semantic Problem Revision
        ↓
one observable user outcome
```

và cũng phải làm được chiều ngược lại:

```text
one RUN
   ↓
may support multiple criteria
BUT
must not silently close unrelated problem revisions
```

Đây là ranh giới quan trọng giữa **execution provenance** và **product truth**.

---

# 6. Problem Resolution Funnel

```text
PROBLEM REPORTED
       ↓
OUTCOME UNDERSTOOD
       ↓
FAILURE OBSERVED / REPRODUCED
       ↓
TARGET LOCALIZED
       ↓
CAUSE DISCRIMINATED
       ↓
INTERVENTION APPLIED
       ↓
TECHNICAL PROOF
       ↓
OUTCOME PROOF
       ↓
TRUSTED RESOLUTION
```

Các exit khác phải typed:

```text
BLOCKED
ABANDONED
SUPERSEDED
NON_PROBLEM
DUPLICATE
EXTERNAL_DEPENDENCY
```

Không ép tất cả thành success/failure nhị phân.

---

# 7. Metrics hierarchy

## 7.1. Tier 0 — Hard floors

Không trade-off:

```text
security
data integrity
financial/business semantics
authority
exact source/workspace identity
destructive-action policy
privacy/secrets
```

---

## 7.2. Tier 1 — Product resolution metrics

Primary:

```text
First-Pass Trusted Resolution Rate
TTPR p50 / p90
False Closure Rate
False Closure Gap p50 / p90
Problem Reopen Rate attributable to unresolved original outcome
Trusted Resolution Rate under censoring
User correction turns/problem
Independent Outcome Evidence Coverage
Problem-to-RUN Linkage Coverage / Ambiguity Rate
```

---

## 7.3. Tier 2 — Decision/rework economics

```text
rework probability
repair count/problem
mutation attempts/problem
replan count/problem
avoidable work estimate
first divergence decision category
wrong-target incidence
wrong-cause incidence
weak-oracle incidence
oracle-provenance mismatch incidence
technical-acceptance-before-outcome incidence
semantic RUN fragmentation/problem
transport/control-plane overhead/problem
no-state-delta retry incidence
```

---

## 7.4. Tier 3 — Process efficiency

```text
context reconstruction time
localization time
tool hops
files inspected
bytes surfaced to model
proof stages
broad proof reruns
handoff latency
wait/queue time
replan transport/harness ratio
technical-proof-to-user-outcome lag
```

---

## 7.5. Tier 4 — Model/compute economics

```text
model cost/problem
tokens/problem
route/model usage
local CPU burden
remote compute burden
cache value
server placement
```

Chỉ tối ưu Tier 4 sau khi Tier 1 không bị xấu đi.

---

# 8. Time metric: từ TTAR tới TTPR

TTAR vẫn hữu ích cho engineering attempt:

```text
TTAR = time to accepted result
```

Nhưng North Star problem-level cần:

```text
TTPR =
T_understand
+ T_truth_preflight
+ T_reproduce
+ T_localize
+ T_discriminate
+ T_intervene
+ T_prove
+ T_user_outcome
+ T_repair
+ T_handoff/context
```

Nếu technical acceptance tới sớm nhưng user outcome vẫn fail, TTPR tiếp tục chạy.

---

# 9. Failure history → Decision Debt taxonomy

Thay vì coi failure history như một danh sách error code, cần đọc nó như **những nơi hệ thống trả “decision debt”**.

| Decision debt | Pattern lịch sử | Cheap early check | Desired prevention |
|---|---|---|---|
| Wrong problem/contract | hiểu sai ý user, missing requirement | outcome restatement + acceptance oracle | không implement khi finish line mơ hồ |
| Wrong target/workspace | sửa nhầm repo/path/module | exact workspace/source/target binding | mutation blocked nếu truth không chắc |
| Premature intervention | patch trước causal diagnosis | boundary discriminator | diagnose trước mutation khi ambiguity material |
| Wrong root cause | patch symptom | hypothesis separation | causal intervention |
| Weak oracle | test xanh nhưng flow vẫn sai | outcome-level reproduction | proof đúng tầng |
| False closure | ACCEPTED nhưng user vẫn lỗi | problem-level outcome gate | no full-resolution claim |
| Retry without learning | replan nhưng cùng strategy | decision-relevant delta check | no unchanged loop |
| Runtime/product confusion | connector/runtime fail bị hiểu là code bug | environment/oracle preflight | fix truth plane first |
| Context loss | restart/handoff/compaction phải đọc lại | compact decision state | no transcript replay |
| Proof overkill | broad tests lặp | proof fingerprint/staged proof | cheapest sufficient proof |
| Over-orchestration | fan-out/switching nhiều | seriality/integration-width check | single lane by default |
| Tool entropy | search/read quá nhiều | stop/next-best-action rule | fewer higher-value observations |
| Transport/control-plane debt | quoting, patch transport, attestation, permission, stale runtime, workspace projection | preflight execution path + simplest authorized mechanism | user-problem work không bị che bởi harness recovery |
| Oracle provenance confusion | technical proof auto-derived thành quality outcome | classify oracle source/type | không false-close problem bằng circular evidence |
| Semantic fragmentation | một problem bị chia nhiều RUN với objective khác nhau | Problem Revision linkage | denominator theo user problem, không theo task text |

HR ledger làm rõ rằng ba hàng cuối không phải hypothetical. Chúng xuất hiện trực tiếp trong natural workload và cần được tính vào TTPR/rework economics.

---

# 10. Discriminator-First Execution

## 10.1. Khái niệm

Một discriminator tốt là observation:

```text
cheap
+ low-risk
+ fast
+ separates plausible hypotheses
+ changes next action
```

Ví dụ user nói:

> “Data tab tài chính vẫn mất.”

Candidate hypotheses:

```text
H1 persistence fail
H2 API mapping fail
H3 normalized-state fail
H4 render fail
H5 stale runtime/cache
```

Discriminator sequence:

```text
persisted value?
→ API value?
→ client normalized value?
→ rendered prop?
```

Không đọc 30 files trước.

---

## 10.2. Khi nào không cần discriminator riêng

Không biến nguyên tắc thành ceremony.

Có thể action trực tiếp khi:

- failure location đã được exact oracle chứng minh;
- target/source/authority chắc chắn;
- root cause causal và local;
- mutation reversible/low-risk;
- proof rẻ và mạnh.

Nguyên tắc là:

> **Discriminate material uncertainty, không tạo uncertainty ritual.**

---

# 11. Resolution Gradient — chọn Next Best Action

Không cần một “Resolution Compiler brain” mới hiện nay.

Mỗi decision có thể dùng protocol mỏng:

```text
CURRENT_BLOCKER
KNOWN_EVIDENCE
LEADING_HYPOTHESES
CHEAPEST_DISCRIMINATOR
EXPECTED_DECISION_DELTA
SELECTED_ACTION
ORACLE
INVALIDATED_STRATEGIES
STOP_CONDITION
```

Ví dụ:

```yaml
CURRENT_BLOCKER: root cause ambiguous
KNOWN_EVIDENCE:
  - save succeeds
  - UI loses value after reload
HYPOTHESES:
  - API mapping
  - persistence
  - client state
CHEAPEST_DISCRIMINATOR:
  - inspect persisted row + API response
EXPECTED_DECISION_DELTA:
  - eliminate persistence or isolate it
SELECTED_ACTION: diagnose
ORACLE:
  - save → reload → expected field persists
INVALIDATED_STRATEGIES:
  - direct cosmetic UI patch
STOP_CONDITION:
  - do not mutate until persistence/API boundary separated
```

Protocol này phải nhẹ hơn work nó điều phối.

---

# 12. Context and history: biến history thành decision state, không replay transcript

## 12.1. Vấn đề

Long-horizon work tốn thời gian vì model phải tái dựng:

```text
mục tiêu hiện tại là gì?
đã thử gì?
hypothesis nào chết?
source nào đang đúng?
proof nào còn valid?
user đã đổi yêu cầu chưa?
```

---

## 12.2. State capsule đề xuất

```text
PROBLEM_ID / REVISION
USER_OUTCOME
ACCEPTANCE_ORACLE
PROTECTED_INVARIANTS
TARGET / SOURCE / WORKSPACE
KNOWN_FACTS
LEADING_HYPOTHESES
ELIMINATED_HYPOTHESES + evidence refs
LAST_CAUSAL_CHANGE
VALID_PROOFS + fingerprints
USER_CORRECTIONS
CURRENT_BLOCKER
NEXT_DISCRIMINATOR
INVALIDATED_STRATEGIES
STOP / REOPEN CONDITION
```

State capsule:

- không thay history;
- không thay raw evidence;
- chỉ là index/summary của decision-relevant truth;
- mọi claim quan trọng phải truy về evidence id/source.

---

## 12.3. History không tự thành playbook

Historical path chỉ có thể tạo:

```text
candidate hint
candidate discriminator
candidate negative-transfer warning
```

Không tự tạo causal policy.

Promotion path:

```text
History
→ Pattern Mining
→ Candidate Decision Hint
→ Prospective Shadow
→ Controlled/Natural Outcome Measurement
→ Keep / Revise / Remove
```

---

# 13. Vai trò đúng của các kiến trúc hiện có

## 13.1. EOCL — KEEP

EOCL giải quyết:

```text
authority
write ownership
source/worktree identity
execution lifecycle
replan
proof lineage
acceptance checkpoint
```

Không có bằng chứng cần redesign EOCL để giải bài toán mới.

EOCL không nên trở thành user-intent reasoner.

---

## 13.2. PRL — KEEP, nhưng mục tiêu là problem identity/outcome, không phải “brain”

PRL nên trả lời:

```text
What problem is this?
Which revision?
Was contract revised or merely reopened?
What outcome evidence belongs to this revision?
Is resolution confirmed, disputed, blocked or superseded?
```

PRL không nên tự quyết định implementation strategy.

---

## 13.3. Resolution Compiler — giữ như research concept

Ý tưởng “history influences next decision” có giá trị.

Nhưng không nên xây authoritative Compiler engine khi:

- natural outcome denominator còn mỏng;
- policy transfer chưa được chứng minh;
- calibrated expected-information model chưa tồn tại;
- Sol/EOCL authority đã có.

Trong giai đoạn hiện tại:

```text
Resolution Compiler = conceptual future layer
NOT a new runtime brain
```

---

## 13.4. Problem Algebra — research lens, không phải roadmap architecture

Bài học hữu ích:

```text
normalize messy surface
preserve invariants
avoid illegal/premature transformations
```

Nhưng chưa có lý do xây:

```text
Problem Algebra Engine
6-state FSM
operator DSL
second policy database
```

Giữ nó để đặt câu hỏi nghiên cứu, không dùng làm lý do refactor.

---

## 13.5. Model routing — secondary optimization

Không chạy theo model mới chỉ vì benchmark đẹp hơn.

Đơn vị economics phải là:

```text
cost/problem resolved
```

không phải:

```text
cost/model call
```

Ví dụ model rẻ hơn nhưng tạo 3 repair turns trước khi Sol phải sửa cuối cùng có thể đắt hơn direct Sol.

Model routing chỉ được promote nếu:

```text
trusted resolution non-inferior
+ first-pass non-inferior
+ TTPR/CAR better
```

---

# 14. Acceptance architecture mới về mặt phương pháp luận

Không nhất thiết thay EOCL schema ngay. Nhưng cần phân biệt bốn tầng:

```text
LEVEL 1 — ENGINEERING FLOOR
source / authority / security / build basics

LEVEL 2 — TECHNICAL ACCEPTANCE
specific implementation claim proved

LEVEL 3 — OUTCOME PROOF
requested observable behavior verified

LEVEL 4 — TRUSTED PROBLEM RESOLUTION
problem revision has adequate outcome evidence
and no unresolved contradiction
```

Chỉ Level 4 là product success cuối cùng.

---

# 15. Reopen và revise

## 15.1. REOPEN

Dùng khi:

```text
same user problem
same acceptance contract
outcome still not achieved
```

Ví dụ:

> “Vẫn không hiển thị.”

Không tạo problem mới chỉ để làm số liệu đẹp.

---

## 15.2. REVISE

Dùng khi contract thay đổi thật:

> “Ngoài phần này, thêm luôn chủ đầu tư.”

Khi đó:

```text
Problem R1 → R2
```

Technical proof của R1 không bị xóa, nhưng không thể tự chứng minh R2.

---

# 16. Retry / replan doctrine

Không dùng hard rule kiểu:

```text
2 failures → mandatory diagnose
```

Rule tốt hơn:

```text
repeat same operator only when:
    decision-relevant delta exists
OR  typed transient condition justifies bounded retry
```

Decision-relevant delta:

```text
new evidence
new hypothesis
new target
new scope
new oracle
new contract
new source/runtime state
new capacity state
```

Typed transient:

```text
network timeout
provider capacity
file lock
bounded startup race
other classified transient
```

Không retry unchanged semantic failure.

---

# 17. Proof doctrine

## 17.1. Tests là oracle, không phải ritual

Test chỉ hữu ích khi nó phân biệt behavior cần chứng minh.

Không yêu cầu mọi worker viết test mới.

Không dùng số lượng test như metric completion.

---

## 17.2. Exact proof lineage vẫn quan trọng

Các incident package/runtime trước đây chứng minh:

```text
source proof
≠ package proof
≠ installed runtime proof
```

Do đó outcome-first không có nghĩa bỏ engineering rigor.

Ngược lại:

> **Outcome proof phải đứng trên một truth plane đáng tin.**

Nếu workspace/source/runtime sai, user-visible proof cũng có thể giả.

---

# 18. Research program đúng: tìm “first divergence point”

Thay vì tiếp tục thêm architecture, bước nghiên cứu có leverage cao nhất là mổ trajectory.

## 18.1. Cohort đề xuất

Chọn tối thiểu:

```text
30–50 repaired/reopened representative problems
30–50 first-pass trusted/near-trusted problems
```

Stratify theo:

```text
localized strong-oracle bug
UI/data-flow bug
weak-oracle semantic bug
cross-file change
runtime/environment
build/release
multi-workspace/targeting
business/financial semantics
```

---

## 18.2. Với mỗi trajectory, annotate

```text
PROBLEM_STATEMENT
USER_DESIRED_OUTCOME
FIRST_ORACLE
FIRST_TARGET_ASSUMPTION
FIRST_CAUSAL_HYPOTHESIS
FIRST_MUTATION
FIRST_TECHNICAL_ACCEPTANCE
FIRST_USER_CORRECTION
FIRST_DIVERGENCE_POINT
DIVERGENCE_CLASS
CHEAPER_DISCRIMINATOR_AVAILABLE?
AVOIDABLE_WORK_AFTER_DIVERGENCE
FALSE_CLOSURE?
FINAL_TRUSTED_OUTCOME
```

Không lưu private chain-of-thought.

Chỉ dùng observable decision/evidence/action/outcome fields.

---

## 18.3. HR-first reconstruction protocol

HR nên là cohort đầu tiên để làm divergence study vì đã có đồng thời:

```text
.coding-tools execution ledger
+ source/proof history
+ technical acceptance
+ rich user correction history
+ business-semantic problems
```

Nhưng vì problem/outcome lineage trong HR ledger hiện chưa đủ, nghiên cứu phải **reconstruct** chứ không giả vờ đã có canonical labels.

Cho mỗi selected user problem:

1. lấy user problem statement/correction làm semantic anchor;
2. xác định desired observable outcome;
3. link các RUN/WAVE có bằng chứng hỗ trợ hoặc tác động tới problem đó;
4. giữ ambiguous links là `AMBIGUOUS`, không ép exact;
5. phân biệt technical accepted time và first trusted outcome time;
6. tìm technical closure nào xảy ra trước user correction;
7. annotate first divergence và avoidable work sau divergence;
8. chỉ sau human-reviewed linkage mới dùng cohort để đánh giá candidate policy.

Đặc biệt phải tạo hai timestamps khác nhau:

```text
T_TECHNICAL_ACCEPTED
T_TRUSTED_USER_RESOLUTION
```

Khoảng cách:

```text
FALSE_CLOSURE_GAP = T_TRUSTED_USER_RESOLUTION - T_TECHNICAL_ACCEPTED
```

chỉ được tính khi cùng Problem Revision và technical acceptance thực sự đã claim/được hiểu như closure trước khi user correction xuất hiện.

## 18.4. Câu hỏi nghiên cứu chính

> **Ở decision point đầu tiên nào repaired trajectory bắt đầu đi lệch, và một phép quan sát rẻ hơn lúc đó có thể tránh được bao nhiêu work phía sau?**

Đây là câu hỏi quan trọng hơn:

> model nào tốt hơn?

---

# 19. Candidate micro-policies để shadow trước

Không hard-gate ngay.

## MP1 — Ambiguous target

```text
IF target/workspace/source materially ambiguous
THEN cheapest target discriminator before mutation
```

## MP2 — Multiple plausible causes

```text
IF >=2 materially plausible causal branches
THEN separating observation before broad patch
```

## MP3 — Failed intervention

```text
IF previous causal intervention failed
THEN no same-family retry without decision-relevant delta
EXCEPT typed transient failure
```

## MP4 — Weak oracle

```text
IF proof cannot observe requested outcome
THEN improve oracle before broad implementation
```

## MP5 — Technical pass ≠ resolution

```text
IF technical proof passes but user outcome not observed
THEN no full problem-resolution claim
```

## MP6 — Early stop

```text
IF sufficient outcome proof + required invariants pass
THEN stop extra search/review/refactor
```

---

## MP7 — Oracle provenance

```text
IF quality/proof signal is derived from technical acceptance itself
THEN it may support technical closure
BUT it cannot independently confirm user problem resolution
```

## MP8 — Semantic continuity across RUNs

```text
IF multiple RUNs serve the same user outcome
THEN evaluate them as one Problem Revision trajectory
AND charge all repair/replan/transport work to that problem's resolution economics
```

Không hard-gate MP8 trước khi linkage quality được chứng minh.

---

# 20. Experimental rollout — không refactor trước evidence

## Stage A — Retrospective divergence audit

Không đổi runtime.

Output:

```text
divergence taxonomy
frequency by task class
avoidable work estimate
false closure cases
candidate discriminators
```

---

## Stage B — Shadow decision packet

Record only:

```text
current blocker
candidate discriminator
selected action
oracle
outcome
```

Không block agent.

Mục tiêu:

- coverage;
- classification stability;
- protocol overhead;
- whether suggested discriminator was useful.

---

## Stage C — Advisory Discriminator-First treatment

Baseline:

```text
CURRENT WORKFLOW
```

Treatment:

```text
OUTCOME-FIRST
+ DISCRIMINATOR-FIRST ADVISORY
+ EARLY-STOP RULE
```

Không thay model và compute placement cùng lúc.

---

## Stage D — Bounded hard gates

Chỉ promote hard gates có machine-verifiable semantics, ví dụ:

```text
workspace/source mismatch → no mutation
write authority missing → no mutation
proof fingerprint mismatch → no reuse
```

Epistemic gate như “root cause đủ chắc chưa” chỉ harden sau khi calibration/prospective evidence đủ mạnh.

---

## Stage E — Learned/adaptive decision policy

Chỉ xem xét khi đã có:

```text
problem-level outcome population
representative task classes
clean decision/outcome linkage
negative-transfer data
sufficient treatment/control observations
```

Không học router từ execution volume đơn thuần.

---

# 21. Breakthrough criteria

Không gọi một thay đổi là “đột phá” chỉ vì code hay hoặc architecture đẹp.

Economic targets làm việc:

```text
median TTPR reduction              ≥ 30% on target strata
repair/reopen attributable rate    reduction ≥ 25–30%
false closure                      material reduction
first-pass trusted resolution      material increase
quality/security/authority         no meaningful regression
protocol overhead                  small vs work saved
```

Các số này là **research/economic targets**, không phải statistical significance thresholds.

Nếu một subsystem:

```text
adds substantial complexity
but improves TTPR only 5–10%
or does not reduce false closure/rework
```

thì ưu tiên:

```text
REVISE or REMOVE
```

---

# 22. What NOT to build now

Không dùng tài liệu này để biện minh cho:

- Problem Algebra Engine;
- 6-state hard FSM;
- authoritative Resolution Compiler brain;
- second analytics database;
- new public MCP tool chỉ để expose internal policy;
- full learned router khi outcome data chưa đủ;
- default multi-agent fan-out;
- Mini/Luna/Terra auto-routing chỉ vì model mới;
- transcript memory store khổng lồ;
- generic proof-cache expansion khi ROI thấp;
- server thành second authoritative writer;
- Kubernetes-like scheduler;
- hard numeric EIG optimizer chưa calibrated;
- process-mining playbook được coi là causal truth;
- refactor lớn chỉ vì taxonomy mới đẹp hơn.

Nguyên tắc:

> **Measured bottleneck first; architecture second.**

---

# 23. How to evaluate model / compute / routing from now on

Một route/model chỉ thắng nếu thắng ở cấp problem.

Ví dụ:

```text
Route A:
10 min
1 attempt
trusted resolution

Route B:
3 min candidate
+ 3 min repair
+ 5 min reroute
+ 10 min final Sol
= 21 min + context/review cost
```

Route B không rẻ chỉ vì call đầu rẻ hơn.

Metric:

```text
Cost per Trusted Problem Resolution
```

không phải:

```text
Cost per Model Call
```

---

# 24. How to evaluate orchestration from now on

Orchestration chỉ có ROI nếu nó:

- giảm TTPR;
- giảm rework;
- giảm false closure;
- giảm context reconstruction;
- giữ hoặc tăng quality floor.

Nếu coordination tạo:

```text
more handoffs
more packets
more state transitions
more review
```

nhưng user outcome không tốt hơn, đó là overhead.

Single-lane là default khi task sequential/tool-dense/integration-width cao.

Parallelism chỉ khi independent work thật sự tồn tại.

---

# 25. Methodological hierarchy of truth

Khi kết luận problem đã được giải quyết, ưu tiên evidence:

```text
1. USER/ENVIRONMENT OUTCOME
   exact requested behavior observed

2. INTEGRATION / RUNTIME PROOF
   same relevant source/runtime

3. TECHNICAL ORACLE
   focused tests/schema/build

4. SOURCE/DIFF REASONING

5. MODEL NARRATIVE
```

Model narrative không được tự promote lên tầng trên.

User statement “vẫn lỗi” không tự chứng minh root cause mới, nhưng đủ để bác claim “problem resolved” nếu phản ánh cùng acceptance contract và đúng environment.

---

# 26. Decision contract cho một problem thực tế

Một packet tối thiểu:

```yaml
problem:
  id:
  revision:
  statement:

outcome:
  desired_observable_behavior:
  oracle:

truth:
  workspace:
  source_identity:
  runtime_identity:
  authority:

invariants:
  -

current_evidence:
  -

hypotheses:
  leading:
  eliminated:

next_decision:
  blocker:
  cheapest_discriminator:
  expected_decision_delta:
  selected_action:
  stop_condition:

proof:
  technical:
  outcome:

resolution:
  status:
  evidence_refs:
```

Đây là conceptual schema để phân tích. Chưa phải yêu cầu thêm database/schema ngay.

---

# 27. Research questions cho giai đoạn tiếp theo

## RQ1 — User problem understanding

Liệu explicit outcome/oracle trước mutation có giảm false closure và rework không?

## RQ2 — First divergence

Những repaired trajectories bắt đầu lệch chủ yếu ở:

```text
contract
target
cause
intervention
proof
outcome
```

hay ở runtime/authority?

## RQ3 — Discriminator value

Discriminator-first có giảm:

- localization time;
- inspected files;
- mutation attempts;
- user correction turns;
- TTPR?

## RQ4 — History reuse

Compact prior decision evidence giúp next decision tốt hơn transcript/history replay ở task classes nào?

## RQ5 — False closure

Bao nhiêu technical acceptance thực tế không trở thành trusted problem resolution?

## RQ6 — Early stop

Bao nhiêu tool/proof/review work xảy ra sau khi evidence đã đủ cho accepted outcome?

## RQ7 — Model routing

Sau khi giữ problem/oracle/source giống nhau, model route nào tối ưu cost/TTPR theo task class?

Model routing nằm sau RQ1–RQ6, không trước.

---

# 28. Standing principles — “hiến pháp” phương pháp luận

1. **Accepted is not Resolved.**
2. **User outcome outranks internal completion narrative.**
3. **Define observable finish line before broad implementation.**
4. **Truth plane before mutation.**
5. **Discriminate material uncertainty before expensive action.**
6. **Fix demonstrated cause, not nearest symptom.**
7. **Preserve business/security/authority invariants.**
8. **Technical proof remains evidence even when problem reopens.**
9. **Reopen same problem when contract unchanged; revise only when contract changes.**
10. **No unchanged semantic retry without new decision-relevant information.**
11. **History suggests; prospective evidence promotes.**
12. **Model benchmark does not grant production authority.**
13. **Do not add architecture without a measured bottleneck.**
14. **Optimize total remaining work, not work per step.**
15. **Stop when sufficient trusted evidence exists.**
16. **False closure is a product failure class.**
17. **Problem Revision is the outcome denominator; RUN/WAVE is execution provenance.**
18. **Cheap models are only cheap if the problem is resolved cheaply.**
19. **Fast execution is only fast if it does not create repair debt.**
20. **The best tool call may be the one that prevents ten future tool calls.**
21. **Proof-derived quality is not independent user-outcome evidence.**
22. **Charge transport, harness and governance recovery to problem-resolution economics when they delay outcome.**
23. **Semantic problem continuity outranks exact objective-text equality.**
24. **Natural user correction is evidence about outcome failure, not an inconvenience to be normalized away.**

---

# 29. Strategic direction

## 29.1. Không tái cấu trúc lớn ngay

Current authority/recovery/proof architecture đã đủ trưởng thành để tiếp tục nghiên cứu.

Không cần đảo kiến trúc quanh Problem Algebra hay Compiler.

---

## 29.2. Chuyển trọng tâm nghiên cứu

Từ:

```text
How do we orchestrate more intelligently?
How do we route to more models?
How do we offload more compute?
```

sang:

```text
Why did this user problem require another repair?
Where did the trajectory first diverge?
Which cheap observation would have prevented it?
Why did technical acceptance fail to become user resolution?
How much work was performed after resolution evidence was already sufficient?
```

---

## 29.3. Cơ chế ứng viên có khả năng tạo bước nhảy

Ba ứng viên hiện mạnh nhất:

```text
A. OUTCOME-FIRST RESOLUTION
B. DISCRIMINATOR-FIRST EXECUTION
C. RESOLUTION GRADIENT + EARLY STOP
```

Tất cả đều có thể thử với một protocol mỏng trên machinery hiện tại.

Không cần subsystem lớn để test hypothesis.

---

# 30. Final methodological proposition

Có thể cô đọng toàn bộ hướng đi thành mệnh đề sau:

> **Coding Tools phải tối ưu cho việc chuyển một vấn đề thực tế của người dùng thành một trạng thái được chứng minh là đã giải quyết đúng vấn đề đó. Mọi model, agent, tool, RUN, WAVE, proof, server, cache, router và protocol chỉ là phương tiện. Giá trị của chúng được đo bằng mức giảm work còn lại, rework, false closure và Time to Trusted Problem Resolution — không bằng lượng hoạt động kỹ thuật mà chúng tạo ra.**

Và phương pháp thực thi:

> **Bắt đầu từ outcome quan sát được; xác nhận truth plane; tìm divergence boundary; dùng phép phân biệt rẻ nhất để loại nhánh sai; chỉ sau đó can thiệp causal; chứng minh bằng đúng outcome contract ban đầu; dừng ngay khi evidence đủ; nếu user outcome bác closure thì reopen/revise problem chứ không bảo vệ technical acceptance.**

Đây là hướng đi hiện tại có khả năng tạo khác biệt thực sự:

```text
NOT:
more orchestration
more models
more agents
more tests
more telemetry

BUT:
fewer wrong decisions
fewer false closures
less avoidable work
faster trusted resolution
```

HR natural-workload evidence làm mệnh đề này cụ thể hơn:

```text
34 accepted technical RUNs
134 passed proofs
31 auto-derived oracle-pass quality events

DO NOT imply

34 resolved user problems
```

Khoảng trống giữa hai vế chính là research target trung tâm của giai đoạn tiếp theo.

---

# 31. Immediate next research action

Bước tiếp theo **không phải triển khai architecture mới**.

Thực hiện **HR-first Problem Trajectory Divergence Study** trước, sau đó mới mở rộng sang Codex-web cohort.

## 31.1. Cohort đầu tiên

```text
30–50 HR repaired/reopened/user-corrected Problem Revisions
vs
30–50 HR first-pass trusted/near-trusted Problem Revisions
```

Không chọn cohort bằng `RUN status=accepted` đơn thuần.

Phải reconstruct Problem Revision từ:

```text
user feedback/history
+ .coding-tools runs/waves/events/proofs
+ source/runtime evidence
+ acceptance criteria
```

## 31.2. Câu hỏi duy nhất cần trả lời trước khi xây gì mới

> **Ở decision point đầu tiên nào trajectory bắt đầu lệch khỏi user outcome, và observation/discriminator nào rẻ hơn đã có thể ngăn phần work phía sau?**

## 31.3. Deliverables

1. HR problem-to-run linkage map có confidence/provenance;
2. divergence taxonomy;
3. false-closure sample với technical-accepted vs user-resolved timestamps;
4. top 5 expensive decision debts;
5. orchestration/transport overhead tách khỏi user-problem progress;
6. candidate discriminators;
7. counterfactual avoidable-work estimate với uncertainty rõ ràng;
8. 3–5 micro-policies cho shadow prospective test;
9. preregistered treatment/control experiment;
10. kill criteria nếu protocol tạo overhead mà không giảm TTPR.

## 31.4. Hai kết quả đều có giá trị

Nếu nghiên cứu không tìm được pattern tập trung:

```text
DO NOT BUILD Resolution Optimizer
DO NOT FORCE Problem Algebra
DO NOT INVENT POLICY FROM NOISE
```

Nếu nghiên cứu cho thấy một số first-divergence classes chi phối phần lớn avoidable work:

```text
promote only those micro-policies
→ prospective shadow
→ paired treatment
→ measure TTPR / false closure / rework
```

Đó mới là cơ sở cho **bước đột phá tiếp theo của Coding Tools**.

---

# 32. Evidence basis của tài liệu

Tài liệu này tổng hợp các lớp evidence sau:

## Project internal historical evidence

- `PFM_ORCHESTRATION_RUNTIME_POSTMORTEM_AND_ENFORCED_CONTROL_LOOP_RESEARCH_2026-08-13.md`
- `260817_PROJECT_REAL_STATE_SCIENTIFIC_EVIDENCE_AND_FULL_EXECUTION_PLAN.md`
- `260825_CODING_WEB_PRL_RESOLUTION_DECISION_PROTOCOL_STRATEGIC_CRITIQUE_AND_OPTIMAL_ROADMAP.md`
- các tài liệu PRL / EOCL / Resolution Compiler / upstream adoption / causal intervention trong `docs/research`
- các projection/ledger snapshots được ghi rõ trong từng research document

## HR representative natural-workload evidence — 2026-08-26

Read-only evidence được lấy trực tiếp từ:

```text
E:\DEV\HR STA\HR\.coding-tools\orchestration\ledger.sqlite3
```

và runtime/workspace snapshot của `E:\DEV\HR STA\HR`.

Các facts chính được đưa vào Revision 2:

- 256 RUN / 278 WAVE / 4481 events tại final read transaction;
- 34 accepted RUN, 169 active, 36 persisted stale, 17 aborted;
- 161 proofs: 134 passed, 27 failed;
- 34 accepted checkpoints;
- 61 `failure_observed`, phần lớn causal attribution field absent/unattributed;
- 22 replanned waves với nhiều transport/harness/runtime recovery reasons;
- 31 technical quality outcomes đều `oracle_pass=true`, sample provenance `accepted_proof_auto_v1`;
- 36 oracle preflights: 2 strong, 34 not strong, 14 `verification=none`;
- runtime projection đồng thời báo 70 unresolved stale orchestration runs, vì vậy stale metrics phải giữ provenance riêng;
- coordination/handoff/agent-lane/P5 outcome tables đều 0 trong cohort này;
- semantic activity tập trung mạnh ở finance/revenue/payment/settlement và canonical identity nhưng không thể coi keyword counts là Problem Revision counts.

Những số liệu này là **observed execution facts**, không phải causal proof và không phải user-resolution denominator.

## Current discussion synthesis — 2026-08-26

- Problem Algebra được hạ thành research lens, chưa phải architecture;
- không tái cấu trúc chỉ vì taxonomy đẹp;
- đột phá phải tạo problem resolution nhanh hơn, không chỉ process correctness;
- Discriminator-First, Resolution Gradient, Outcome-First và Early Stop là hypotheses có ROI trực tiếp hơn;
- technical acceptance không được phép thay user outcome;
- False Closure và Trusted Problem Resolution trở thành trọng tâm nghiên cứu.

## Evidence boundary

Các snapshot lịch sử của Codex-web và snapshot live-read của HR phải được giữ provenance riêng.

Đối với HR Revision 2:

- workspace được xác nhận trực tiếp là `E:\DEV\HR STA\HR`;
- `.coding-tools/orchestration/ledger.sqlite3` được mở read-only;
- final numeric snapshot được query trong một read transaction tại `max_seq=4481`;
- ledger vẫn là live database nên các query trước/sau transaction có thể tăng event count; tài liệu dùng final transaction cho các headline counts;
- keyword clusters chồng lấn, không phải problem counts;
- persisted `status='stale'` và runtime `unresolved_stale_orchestration_runs` là hai projections khác nhau cho tới khi chứng minh cùng contract;
- không có đủ problem-level confirmed outcome evidence để tính Trusted Problem Resolution Rate từ HR ledger một mình;
- user-conversation history chỉ được dùng như source cho reconstruction/human review, không được silently biến thành machine-labelled causal truth.

Tài liệu vẫn được giữ như artifact để tiếp tục phản biện trước khi promote bất kỳ methodology nào thành runtime policy.

**Intended repository location after review/approval:**

```text
docs/research/260826_CODING_WEB_USER_PROBLEM_RESOLUTION_FIRST_METHODOLOGY_AND_STRATEGIC_DIRECTION.md
```

---

# 33. Status of this document

```text
METHODOLOGY SYNTHESIS: REVISION 2 COMPLETE FOR REVIEW
HR .CODING-TOOLS EVIDENCE: INTEGRATED
RUNTIME POLICY CHANGE: NONE
ARCHITECTURE REFACTOR: NONE
CLAIM OF BREAKTHROUGH: NONE YET
NEXT STEP: HR-FIRST PROBLEM TRAJECTORY DIVERGENCE STUDY
```

**End of working methodology.**
