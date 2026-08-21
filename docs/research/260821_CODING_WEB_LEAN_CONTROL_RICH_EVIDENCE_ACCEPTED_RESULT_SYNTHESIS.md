# CODING WEB — LEAN CONTROL, RICH EVIDENCE VÀ CHIẾN LƯỢC ACCEPTED-RESULT

> **Bài phân tích hợp nhất từ nghiên cứu ngày 18/08/2026, case study Single-Sol ngày 21/08/2026 và trạng thái canonical hiện tại của dự án**  
> **Workspace:** `E:\DEV\Codex-web`  
> **Ngày tổng hợp:** 21/08/2026  
> **Loại tài liệu:** strategic synthesis / engineering doctrine / evidence-based roadmap  
> **Phạm vi:** Coding Web / Tools-Codex-web, ChatWeb GPT-5.6 Sol, Coding-VP/Coding MCP, EOCL, P4–P9, skill surface, context management, accepted-result economics  
> **Quy tắc sử dụng:** tài liệu này là bản phân tích chiến lược. Trạng thái vận hành thực tế vẫn phải ưu tiên current source + live runtime + EOCL + `docs/CURRENT_STATE.md` + `docs/ROADMAP.md`.

---

# 0. KẾT LUẬN ĐIỀU HÀNH

Hai tài liệu được đối chiếu trong bài này phản ánh hai giai đoạn tư duy khác nhau của cùng một dự án.

Tài liệu ngày **18/08/2026** — `260818_CODING_WEB_NGHIEN_CUU_KHOA_HOC_TOAN_DIEN_AI_AGENT_VA_LO_TRINH.md` — trả lời câu hỏi:

> **Coding Web cuối cùng nên trở thành hệ thống gì?**

Câu trả lời của tài liệu là một **Accepted-Result Learning Control System**: một hệ thống không chỉ thực thi code mà còn quan sát quyết định trước mutation, cưỡng chế authority/proof trong execution, liên kết prediction với outcome sau acceptance và chỉ promote policy khi representative local evidence chứng minh improvement thực sự.

Tài liệu ngày **21/08/2026** — `260821_SINGLE_SOL_SKILL_OPTIMIZATION_CONTEXT_COMPACTION_AND_ANTI_OVERENGINEERING_CASE_STUDY.md` — trả lời một câu hỏi khác:

> **Làm thế nào để đi tới mục tiêu trên mà không biến Coding Web thành một hệ thống orchestration quá phức tạp, nhiều agent, nhiều skill, nhiều state authority và nhiều lớp kiểm tra đến mức chi phí điều khiển lớn hơn giá trị tạo ra?**

Câu trả lời của tài liệu là:

> **Single Sol Authority / Lean Skill Surface / Native Compaction / One State Authority / Adaptive Compute / Deterministic Evidence / Stop-on-Done.**

Sau khi đối chiếu hai tài liệu với trạng thái canonical mới nhất của dự án, kết luận tổng hợp của bài này là:

> **Hai tài liệu không mâu thuẫn. Tài liệu 18/8 xác định đúng North Star; tài liệu 21/8 xác định đúng anti-complexity doctrine. Tuy nhiên không được triển khai nguyên văn cả hai như hai roadmap song song. Hướng đúng là: LEAN CONTROL + RICH EVIDENCE + REWORK-FIRST ECONOMICS.**

Nói ngắn gọn:

```text
Control plane: càng gọn càng tốt, miễn giữ đúng authority/safety/proof.
Evidence plane: càng giàu và chính xác càng tốt, miễn không biến thành authority thứ hai.
Optimization target: accepted result, không phải token, agent count, LOC hay tool calls.
Primary economic problem: rework.
```

Trạng thái thực tế hiện tại củng cố kết luận này rất mạnh:

- P0–P3 engineering/control đã trưởng thành và không cần mở lại để tiếp tục xây framework.
- P4 source/gate engineering đã accepted; canonical collection đã có **57 representative terminal tasks**.
- Trong số đó có **44 predictive terminal outcomes** đủ dữ liệu cho phân tích hiện tại.
- Nhưng causal-solution repair chỉ có **2**, nonrepair **42**, unknown **13**; vì vậy `validated_signals=[]` vẫn là kết quả đúng và trung thực.
- P5 implementation hiện là **`OPEN_DORMANT`**, treatment là **`GATED_OFF`** — tức code/infrastructure đã có, nhưng chưa được phép treatment.
- Baseline P5 trên **442 accepted runs** cho thấy first-pass khoảng **59,95%**, repaired khoảng **40,05%**.
- Median TTAR first-pass khoảng **65,7 giây**, repaired khoảng **296,2 giây** — repaired work mất khoảng **4,51×** median TTAR của first-pass.
- P90 repaired cũng xấu hơn khoảng **4,37×**.

Từ đây xuất hiện một kết luận kinh tế rất quan trọng:

> **Nếu một optimization giảm vài phần trăm token hoặc vài giây tool latency nhưng làm repair tăng, optimization đó có thể làm hệ thống tệ hơn. Ngược lại, giảm repair có khả năng tạo leverage lớn hơn nhiều so với việc thêm router, worker, server-first hoặc skill mới.**

Vì vậy, ưu tiên chiến lược nên là:

1. hoàn tất truth/traceability hardening nhỏ, không mở thêm authority;
2. giữ single Sol authority mặc định, deterministic execution/proof plane;
3. không rewrite hoặc thêm skill nếu hiện trạng đã đáp ứng phần lớn mục tiêu;
4. tiếp tục thu P4/P6 representative evidence một cách tự nhiên;
5. chỉ mở P5 treatment khi canonical gate thực sự xanh;
6. chỉ mở P7 khi rework economics đã hiểu đủ;
7. chỉ mở P8 khi P4–P7 tạo validated inputs;
8. chỉ mở P9 khi telemetry chứng minh capacity là active bottleneck.

Đây là thesis trung tâm của tài liệu:

> **Coding Web đã đi qua giai đoạn “xây đủ năng lực”. Giai đoạn hiện tại phải chuyển sang “chứng minh lợi ích biên”. Mọi complexity mới phải trả lời được: nó làm accepted-result tốt hơn ở đâu, với bằng chứng nào, và có đáng với chi phí điều khiển hay không?**

---

# 1. NGUỒN PHÂN TÍCH VÀ THỨ TỰ BẰNG CHỨNG

## 1.1. Hai nguồn nghiên cứu chính

### Nguồn A — Nghiên cứu khoa học toàn diện ngày 18/08/2026

File:

`docs/research/260818_CODING_WEB_NGHIEN_CUU_KHOA_HOC_TOAN_DIEN_AI_AGENT_VA_LO_TRINH.md`

Đóng góp chính:

- xác định North Star là accepted engineering outcome;
- tổng hợp kiến trúc authority/EOCL/recovery/evaluation;
- chứng minh rework là cost center lớn;
- đưa ra khái niệm pre-mutation decision accountability;
- định hướng P4 solution economics thành prediction → outcome learning loop;
- phân tích repository memory, oracle, localization, routing, server-first, long-horizon quality;
- đề xuất Accepted-Result Learning Control System;
- cảnh báo learned router, multi-agent, server-first, proof-cache, generic orchestration đều phải evidence-gated.

### Nguồn B — Single-Sol / skill / context / anti-overengineering ngày 21/08/2026

File:

`docs/research/260821_SINGLE_SOL_SKILL_OPTIMIZATION_CONTEXT_COMPACTION_AND_ANTI_OVERENGINEERING_CASE_STUDY.md`

Đóng góp chính:

- phân biệt single authority với Max-only;
- phân tích coordination overhead từ subagent và reviewer;
- phân tích skill surface, progressive disclosure, skill leakage và context cost;
- khuyến nghị native compaction thay vì compression framework riêng;
- khuyến nghị one state authority;
- cảnh báo StateM hoặc framework mới có thể duplicate state;
- khuyến nghị deterministic-first verification;
- đưa ra stop-on-DONE và smallest sufficient intervention;
- biến anti-overengineering thành governance principle thay vì khẩu hiệu tối giản.

## 1.2. Nguồn canonical hiện tại dùng để hiệu chỉnh hai tài liệu

Tài liệu nghiên cứu có giá trị lịch sử nhưng không được dùng thay current truth. Phân tích này hiệu chỉnh bằng các nguồn vận hành mới nhất của repo:

- `docs/CURRENT_STATE.md`;
- `docs/ROADMAP.md`;
- `docs/research/260821_CODING_WEB_MASTER_ENGINEERING_STRATEGY_AND_HISTORY.md`;
- `.coding-tools/orchestration/ledger.sqlite3`;
- canonical P4 readiness reporter;
- P5 baseline reporter;
- current Git/runtime identity tại thời điểm kiểm tra.

Tại snapshot sử dụng trong bài:

```text
workspace: E:\DEV\Codex-web
branch: main
HEAD: 36ce22300aa4cb628d84d895942aeafd35b6bde6
HEAD == origin/main: true
smart-v3 tool count: 8
P4 state: COLLECTING
P5 implementation: OPEN_DORMANT
P5 treatment: GATED_OFF
```

## 1.3. Evidence hierarchy sử dụng trong bài

```text
E1 — current source/live runtime/EOCL exact checkout
E2 — canonical ledger + canonical reporters
E3 — maintained CURRENT_STATE/ROADMAP
E4 — accepted historical run/wave/proof
E5 — dated research synthesis
E6 — external research / open-source evidence
E7 — operator observation / anecdotal signal
```

Một nguyên tắc quan trọng:

> **Research document có thể đúng về mechanism nhưng cũ về status.**

Do đó một recommendation ngày 18/8 có thể vẫn đúng về khoa học nhưng không còn là công việc phải implement nếu đến 21/8 source đã hoàn thành phần đó.

---

# 2. HAI TÀI LIỆU KHÔNG MÂU THUẪN — CHÚNG ĐÓNG HAI VAI TRÒ KHÁC NHAU

## 2.1. Tài liệu 18/8 là scientific architecture thesis

Tài liệu 18/8 xuất hiện ở thời điểm dự án vừa chuyển từ một Execution Hub có authority sang một hệ thống bắt đầu đặt câu hỏi về quality of decision trước mutation.

Thesis chính của nó là:

```text
Execution accountability đã có.
Decision accountability chưa đủ.
```

EOCL đã biết:

```text
ai có quyền write?
run/wave nào đang active?
source fingerprint nào được proof?
proof nào dẫn tới acceptance?
```

Nhưng hệ thống còn thiếu:

```text
trước mutation, root cause giả định là gì?
solution scope dự kiến là gì?
oracle mạnh hay yếu?
expected repair risk là gì?
```

Từ đó hình thành P4 Solution Economics Shadow và hướng Accepted-Result Learning Control System.

Đây vẫn là thesis đúng ở cấp chiến lược.

## 2.2. Tài liệu 21/8 là complexity-control thesis

Sau vài ngày triển khai rất nhanh, dự án gặp một loại bottleneck mới:

- nhiều trạng thái cần reconcile;
- nhiều lần kiểm tra cùng một sự thật qua nhiều surface;
- risk của stale workspace/runtime projection;
- completion/ACK semantics;
- nhiều tài liệu nghiên cứu có thể trở thành nhiều roadmap;
- subagent, reviewer và skill có thể tăng overhead;
- framework mới dễ duplicate authority đã có.

Case study 21/8 nhận ra một điều đúng:

> **Một hệ thống agent trưởng thành có thể bị giảm hiệu quả không phải vì model yếu, mà vì control surface quá lớn.**

Vì vậy nó tập trung vào:

```text
one authority
one state authority
lean skill surface
bounded context
adaptive compute
one proportional verification pass
stop when DONE
```

## 2.3. Synthesis đúng

Hai tài liệu nên được phân vai như sau:

| Tài liệu | Vai trò đúng |
|---|---|
| 18/8 scientific report | Research foundation / North Star / hypothesis map |
| 21/8 Single-Sol case study | Anti-complexity doctrine / operating filter |
| CURRENT_STATE | Current operational truth |
| ROADMAP | Current execution sequencing |
| Master Strategy 21/8 | Historical/strategic consolidation |
| EOCL + ledger | Causal execution truth |

Không nên biến hai research docs thành hai backlog độc lập.

---

# 3. NORTH STAR ĐÚNG: ACCEPTED RESULT, KHÔNG PHẢI TOKEN HOẶC AGENT COUNT

Một trong những điểm nhất quán nhất giữa hai tài liệu là phản đối tối ưu proxy.

Các proxy hấp dẫn nhưng dễ gây sai hướng:

- token thấp nhất;
- model rẻ nhất;
- model mạnh nhất;
- nhiều agent nhất;
- ít agent nhất;
- nhiều tests nhất;
- ít LOC nhất;
- ít file nhất;
- cache hit cao nhất;
- CPU utilization cao nhất;
- server offload cao nhất;
- tool-call count thấp nhất.

Các biến này có thể hữu ích nhưng không phải objective tối hậu.

Objective đúng là:

```text
correct accepted result
+ quality floor
+ low repair probability
+ low TTAR
+ low expected total cost
+ low local/human burden
+ maintainable extension quality
```

Tối ưu nên mang tính lexicographic:

1. correctness/security/data/authority/proof;
2. accepted/first-pass outcome;
3. expected TTAR/cost/rework;
4. maintainability khi relevant;
5. simplicity nếu các phương án gần tương đương.

Đây cũng là lý do “ít token hơn” không thể tự động được gọi là thành công.

---

# 4. DỮ LIỆU HIỆN TẠI CHO THẤY REWORK LÀ COST CENTER QUAN TRỌNG NHẤT

## 4.1. P5 observational baseline mới nhất

Canonical P5 baseline hiện ghi:

```text
accepted_runs: 442
first_pass_accepted: 265
repaired_accepted: 177
replan_count: 340
```

Derived:

```text
first_pass_rate = 265 / 442 = 59.95%
repaired_rate   = 177 / 442 = 40.05%
```

TTAR:

```text
first_pass_p50 = 65,703 ms
repaired_p50   = 296,221 ms
ratio          = 4.508×

first_pass_p90 = 431,210 ms
repaired_p90   = 1,882,930 ms
ratio          = 4.367×
```

## 4.2. Ý nghĩa kinh tế

Đây là chênh lệch quá lớn để xem rework như một metric phụ.

Một repaired task không chỉ tốn thêm một model call. Nó có thể kéo theo:

- reload context;
- thêm localization/search;
- thêm wave;
- thêm patch;
- thêm proof;
- thêm acceptance cycle;
- source/base drift risk;
- human wait;
- review cost;
- runtime/tool interaction;
- risk của adjacent regression.

Do đó:

> **Giảm repair probability một cách an toàn có expected leverage lớn hơn nhiều micro-optimization ở tool latency hoặc token count.**

## 4.3. Hệ quả cho roadmap

Một optimization chỉ nên được ưu tiên nếu nó có khả năng tác động lên ít nhất một trong các biến:

```text
P(first-pass accepted)
P(repair)
TTAR
critical defect
accepted-result cost
human/local burden
```

Nếu một subsystem mới chỉ làm “dashboard nhiều hơn”, “routing đẹp hơn”, “context thông minh hơn” nhưng không có đường causal hợp lý tới các outcome trên, nó chưa đáng ưu tiên.

---

# 5. P4 HIỆN KHÔNG CÒN THIẾU FRAMEWORK — NÓ THIẾU OUTCOME VARIATION CÓ CHẤT LƯỢNG

## 5.1. Snapshot P4 mới nhất

Canonical P4 reporter hiện có:

```text
representative_terminal_shadow_tasks = 57
bugfix = 29
feature = 28
predictive representative terminal outcomes = 44
```

Causal label:

```text
causal_solution_repair_tasks = 2
causal_solution_nonrepair_tasks = 42
unknown = 13
```

Causal repair rate trên known repair/nonrepair:

```text
2 / (2 + 42) = 4.545%
```

## 5.2. Tại sao `validated_signals=[]` là kết quả đúng

Một số signal có pooled LOOCV Brier gain dương rất nhỏ:

```text
candidate_solution_scope        +0.000022
expected_repair_risk            +0.000089
smallest_causal_solution_scope  +0.000022
oracle_strength                  0
root_cause_confidence            0
```

Nhưng validation contract còn yêu cầu:

- familywise Wilson separation;
- task-family holdout;
- source-state holdout;
- temporal holdout;
- rolling temporal holdout;
- positive predictive gain đủ bền.

Hiện tại các điều kiện này chưa đồng thời đạt.

Vì vậy:

```text
p4_gate.can_answer_which_signals_predict_repair = false
validated_signals = []
p4_empirically_complete = false
```

là kết luận khoa học đúng.

## 5.3. Bài học quan trọng

Khi sample count tăng từ mức vài chục lên 57 nhưng gate vẫn chưa pass, phản ứng sai sẽ là:

- thêm hàng loạt predictor;
- đổi repair label cho nhiều repair hơn;
- nới Wilson threshold;
- đổi validation method để signal xanh;
- tạo synthetic tasks;
- chọn workload có chủ đích để tạo separation.

Tất cả đều làm hỏng evidence integrity.

Phản ứng đúng:

> **Tiếp tục organic representative workload và cải thiện measurement completeness tự nhiên, không manipulate evidence.**

Nút thắt hiện tại không còn là “P4 thiếu code”.

---

# 6. P5: IMPLEMENTATION ĐÃ CÓ, TREATMENT CHƯA ĐƯỢC PHÉP

Tài liệu 18/8 mô tả P5 như một bước tương lai. Trạng thái hiện tại đã tiến xa hơn.

Canonical reporter:

```text
implementation_status = OPEN_DORMANT
treatment_status      = GATED_OFF
treatment_active      = false
automatic_start       = false
```

P5 đã có:

- controlled rework-reduction mode;
- explicit enrollment semantics;
- stable quality oracle requirement;
- causal-fix gate;
- oracle settlement before mutation;
- bounded change surface;
- TTAR/CAR/repair quality promotion contract.

Nói cách khác:

> **Không cần xây tiếp “P5 infrastructure” để cảm thấy phase đang tiến.**

Điều cần là chờ readiness gate.

Ba requirement hiện tại:

```text
clean_upstream_matched_baseline = false
p4_gate_can_answer_which_signals_predict_repair = false
validated_predictive_signal_present = false
```

Kể cả Git baseline được làm sạch, P5 treatment vẫn chưa thể mở nếu P4 predictive gate còn false.

Đây là fail-closed governance đúng.

---

# 7. SINGLE SOL AUTHORITY: ĐÚNG, NHƯNG KHÔNG ĐỒNG NGHĨA SOL MAX-ONLY

## 7.1. Cần tách topology khỏi reasoning effort

Hai khái niệm thường bị nhập làm một:

```text
ONE SOL AUTHORITY
```

và

```text
SOL MAX FOR EVERY TASK
```

Chúng hoàn toàn khác nhau.

Single Sol authority nghĩa là:

- một semantic controller;
- một final acceptance authority;
- không có các peer planner/coder/reviewer cùng tranh quyền;
- deterministic tool plane làm execution/proof.

Reasoning effort lại là budget variable:

- high;
- xhigh;
- max;
- ultra.

## 7.2. Evidence nội bộ phản bác Max-only như policy tiết kiệm mặc định

Case study 21/8 ghi một snapshot trong đó:

- 1 `sol_max` call dùng khoảng 105.287 token;
- tổng 8 `sol` calls dùng ít token hơn call Max đó.

Đây không chứng minh Max kém vì task difficulty không đồng nhất.

Nhưng nó đủ để bác bỏ mệnh đề:

> “Max-only mặc nhiên tiết kiệm token.”

Policy đúng hơn:

> **Một Sol identity, adaptive compute.**

Max được dùng khi marginal expected value hợp lý:

- consequential architecture;
- high-risk security/data/finance;
- khó rollback;
- repeated cheaper attempt đã thất bại có ý nghĩa;
- final synthesis với integration width cao.

Không dùng Max chỉ vì task dài.

---

# 8. SINGLE-LANE DEFAULT ĐÚNG HƠN “CẤM MULTI-AGENT”

## 8.1. Vì sao Coding Web phù hợp single-lane default

Phần lớn task của Coding Web có:

- một canonical workspace;
- mutable shared state;
- one write lease;
- cross-file integration;
- EOCL run/wave;
- one final acceptance boundary.

Trong topology như vậy, việc spawn nhiều model thường thêm:

```text
prompt duplication
+ handoff
+ state synchronization
+ merge/review
+ stale assumptions
+ conflict risk
+ context replay
```

Nếu work không thực sự độc lập, parallelism chỉ biến sequential dependency thành coordination overhead.

## 8.2. Nhưng multi-agent vẫn có miền hữu ích

Không nên biến single-agent thành giáo điều.

Parallel model lane có thể có positive expected value khi:

- workstream thật sự độc lập;
- disjoint isolated worktrees;
- interfaces đã settled;
- independent oracle;
- security adversarial review;
- latency critical hơn token;
- merge/integration authority rõ;
- expected gain lớn hơn coordination cost.

Do đó policy phù hợp nhất là câu đã có trong `sol-lean-codex`:

> **Stay single-lane until parallelism earns its cost.**

Câu này tốt hơn “disable all subagents forever”.

---

# 9. ĐÁNH GIÁ `sol-lean-codex`: KHÔNG NÊN REWRITE TOÀN DIỆN

Case study 21/8 đề nghị rewrite `sol-lean-codex` để single-authority và anti-overengineering hơn.

Sau khi đối chiếu entrypoint hiện tại, phần lớn policy mong muốn đã tồn tại:

- accepted-result optimization;
- fast path;
- deterministic-first;
- explicit route authorization;
- single lane mặc định;
- parallelism chỉ khi positive expected value;
- bounded packet;
- compact state capsule;
- no unchanged retry;
- progressive verification;
- stop khi finish line được chứng minh;
- Max/Ultra explicit gate;
- final acceptance trên Sol.

Vì vậy rewrite toàn bộ có risk lớn hơn value.

Hướng đúng:

```text
Case-study principles
        ↓
semantic diff với sol-lean-codex hiện tại
        ↓
chỉ patch rule thực sự thiếu
```

Các rule có thể cân nhắc bổ sung nếu chưa đủ explicit:

1. DONE/NON-GOALS contract cho material task;
2. không reopen accepted phase nếu không có defect/change/invalidation;
3. terminal report rõ outcome/evidence/residual risk/parked items;
4. framework mới phải replace/simplify layer cũ, không được chỉ layer thêm.

Đây là **smallest sufficient intervention**.

---

# 10. KHÔNG NÊN TẠO PERMANENT `anti-overengineering-sol` SKILL RIÊNG

Ý tưởng tạo một pilot skill chống overengineering có giá trị trong thí nghiệm, nhưng production architecture phải thận trọng.

Nếu production có:

```text
sol-lean-codex
+
anti-overengineering-sol
```

thì lập tức sinh:

- overlap trigger;
- duplicate instructions;
- conflict precedence;
- metadata overhead;
- maintenance/versioning;
- policy split.

Đây là nghịch lý:

> **Skill chống overengineering có thể tự trở thành overengineering.**

Cách phù hợp:

- nếu cần A/B, dùng experimental policy/profile riêng;
- nếu rule chứng minh giá trị, merge vào control skill duy nhất;
- retire experimental layer sau evaluation.

Production target nên vẫn là **one control skill**, không phải một stack control skills.

---

# 11. SKILL OPTIMIZATION LÀ ĐÚNG, NHƯNG KHÔNG PHẢI PRIORITY SỐ 1

## 11.1. Skill overhead là real nhưng cần đặt cạnh rework economics

Case study 21/8 đúng khi nói skill có thể làm tăng:

- metadata;
- body context;
- false trigger;
- version conflict;
- cache prefix instability;
- instruction surface;
- duplicated policy.

Research external cũng cho kết quả trái chiều hợp lý:

- skill tốt, focused, đúng version có thể tăng success;
- skill rộng/lỗi thời/chồng lấn có thể tăng token mà không tăng pass rate.

Nhưng trong project hiện tại ta có một effect size rất rõ:

```text
repair → ~4.5× median TTAR
```

Trong khi chưa có effect size tương tự cho:

```text
rút 200 dòng skill → accepted-result improvement bao nhiêu?
```

Do đó skill optimization nên là **supporting efficiency program**, không được lấn át rework-first roadmap.

## 11.2. Cách audit skill đúng

Không xóa hàng loạt.

Mỗi skill nên được đánh giá theo:

```text
safety/domain necessity
activation frequency
false activation
body size / references loaded
version freshness
overlap
paired acceptance delta
paired token delta
maintenance cost
```

Decision:

```text
KEEP
NARROW_TRIGGER
SPLIT_TO_REFERENCE
MERGE
RETIRE
QUARANTINE_VERSION_MISMATCH
```

Không dùng line count làm sole criterion.

---

# 12. NATIVE COMPACTION + DURABLE STATE: HƯỚNG ĐÚNG

Một kết luận rất đáng giữ của tài liệu 21/8 là:

> **Không xây một compression/memory framework chỉ để làm việc mà model/runtime đã có native compaction.**

Mô hình đúng:

```text
Model context = working set
Ledger/filesystem = backing store
```

Context chỉ nên mang:

- current objective;
- protected invariants;
- accepted decisions;
- latest relevant evidence;
- active owner/run/wave;
- current uncertainty;
- next critical action.

Durable store giữ:

- full historical execution evidence;
- proof identity;
- reports;
- artifacts;
- source/workspace identity;
- prior accepted outcomes.

Anti-pattern:

- reload toàn task-history;
- dump repository vào prompt;
- tóm tắt mỗi tool call bằng model;
- giữ failed branches trong working context;
- tạo memory DB thứ hai;
- coi transcript là source of truth.

---

# 13. STATEM: NÊN HỌC NGUYÊN LÝ, KHÔNG CÀI LÀM PRODUCTION AUTHORITY THỨ HAI

StateM đưa ra nhiều ý tưởng tốt:

- durable phase state;
- checked transitions;
- runbook;
- repair boundary;
- resume;
- phase-local context;
- explicit terminal state.

Nhưng Coding Web đã có:

- task state;
- task history;
- EOCL RUN/WAVE;
- ledger;
- write lease;
- proof;
- checkpoint;
- completion report;
- handoff.

Nếu thêm `.statem` production song song:

```text
EOCL current state
Task projection
StateM current node
```

thì phải thêm reconciliation logic — đúng loại complexity mà dự án đang muốn giảm.

Quyết định đúng:

> **Absorb principles, not authority.**

StateM chỉ nên được pilot nếu nó **thay thế** một layer cụ thể hoặc chạy hoàn toàn cô lập như research harness.

---

# 14. LEAN CONTROL + RICH EVIDENCE: KIẾN TRÚC TỔNG HỢP ĐÚNG NHẤT

Có một hiểu lầm cần loại bỏ:

> “Lean” không có nghĩa là ít telemetry hay evidence nghèo.

Thực tế architecture tốt có thể đồng thời:

## Lean control plane

```text
one Sol authority
one Runtime authority
one writer
one EOCL
small public tool surface
one completion report
single-lane default
adaptive compute
few handoffs
small instruction surface
```

## Rich evidence plane

```text
source identity
workspace identity
run/wave identity
pre-mutation prediction
oracle identity
proof identity
quality outcome
repair/replan
TTAR
cost when observed
causal classification
```

Evidence plane có thể rất sâu mà không làm control plane phức tạp, miễn:

- evidence là append/derived;
- không thêm writer/authority thứ hai;
- không ép model đọc toàn bộ evidence mỗi turn;
- query theo need;
- current truth có projection rõ.

Đây là synthesis quan trọng nhất của hai tài liệu.

---

# 15. TRUTH/TRACABILITY HARDENING LÀ MỘT TRONG SỐ ÍT COMPLEXITY MỚI CÓ ROI RÕ

Master Strategy ngày 21/8 thu nhỏ future hardening thành:

1. Truth Reconciliation;
2. Wave Objective Provenance;
3. TruthSnapshot;
4. Operator Truth Console;
5. Executable Engineering Casebook;
6. STOP / EVALUATE.

Đây là hướng hợp lý vì nó giải quyết failure mode đã quan sát nhiều lần:

```text
transport online
≠ runtime đúng source
≠ workspace đúng
≠ package đúng
≠ accepted proof đúng source
```

Ngay trong quá trình đánh giá gần nhất đã xuất hiện một ví dụ:

- một MCP surface trả `ExceptionGroup`;
- nhưng authoritative Coding-VP surface trên đúng workspace vẫn đọc được runtime/canonical state bình thường.

Nếu UI chỉ hiển thị “MCP ERROR”, operator dễ suy ra sai “project/runtime đang hỏng”.

TruthSnapshot không phải overengineering nếu nó chỉ là **read-only composition của các truth source đã có**.

Nó trở thành overengineering nếu biến thành:

- DB riêng;
- authority riêng;
- state machine riêng;
- ninth public tool;
- background sync engine.

Do đó requirement đúng là:

```text
projection, not system
```

---

# 16. P6–P9 DƯỚI LĂNG KÍNH HỢP NHẤT NÀY

## P6 — Server-first representative evidence

Có thể tiếp tục song song.

Đây là evidence lane, không phải architecture lane.

Policy:

- frozen experiment identity;
- organic eligible workload;
- exact-source pairing;
- global server-first OFF;
- không reopen P3 architecture.

**Status đề nghị:** PARALLEL COLLECTION.

## P7 — Model-routing economics

Không nên mở mạnh trước khi P5/rework economics rõ hơn.

Lý do:

Nếu solution quality còn là dominant factor, routing model tốt hơn vài giây không giải quyết repair penalty 4,5×.

**Status:** HOLD / later.

## P8 — Joint optimizer

P8 cần validated inputs từ:

- solution risk;
- rework treatment;
- placement;
- routing;
- proof/review economics.

Nếu build optimizer trước, hệ thống sẽ tối ưu noise hoặc proxy.

**Status:** DEFERRED.

## P9 — Capacity scaling

Chỉ mở nếu capacity telemetry chứng minh capacity là bottleneck thực sự.

Không scale worker/provider/fleet trước chỉ vì architecture cho phép.

**Status:** EVIDENCE-TRIGGERED ONLY.

---

# 17. ROADMAP TỔNG HỢP ĐỀ NGHỊ

## Lane A — Truth hardening nhỏ và đóng nhanh

Mục tiêu:

- reconcile claim planes;
- effective wave objective;
- TruthSnapshot;
- operator truth separation;
- casebook regressions.

Nguyên tắc:

- không thêm authority;
- không thêm public tool;
- không làm generic framework;
- sau Sequence 5 phải STOP/EVALUATE.

## Lane B — P4 organic evidence

Tiếp tục mọi representative feature/bugfix thật.

Không:

- fabricate tasks;
- target predictor buckets;
- relabel repairs;
- đổi statistical method để pass.

Mỗi organic accepted task là evidence opportunity; collection không được làm workload biến dạng.

## Lane C — P6 server-first evidence

Thu song song trên genuinely eligible workloads.

Không promote global server-first từ pilot nhỏ.

## Lane D — P5 dormant readiness

Không viết thêm framework chỉ để “đẩy P5”.

Khi:

```text
validated predictive signal present
AND P4 can answer predictors of repair
AND clean upstream-matched baseline
```

thì semantic controller mới explicit mở controlled treatment.

## Lane E — Skill/context efficiency, low-intensity

Chỉ làm:

- audit overlaps;
- narrow obvious triggers;
- move clearly duplicated detail to references;
- patch missing anti-OE control rule.

Không biến thành major phase trước khi đo được leverage.

---

# 18. MÔ HÌNH QUYẾT ĐỊNH CHO MỌI COMPLEXITY MỚI

Trước một đề xuất mới, hỏi theo thứ tự:

### Gate 1 — Có real defect/consumer không?

Nếu không:

```text
DEFER
```

### Gate 2 — Primitive hiện tại đã giải được chưa?

Nếu có:

```text
USE EXISTING
```

### Gate 3 — Giải pháp mới replace hay layer thêm?

Nếu chỉ layer thêm một authority/state/control framework:

```text
REJECT BY DEFAULT
```

### Gate 4 — Có causal path tới accepted result không?

Ví dụ:

```text
new context selector
→ better localization
→ fewer wrong-target repairs
→ lower TTAR
```

Nếu không diễn giải được path:

```text
HOLD
```

### Gate 5 — Có smallest experiment không?

Nếu có, chạy bounded measurement trước architecture promotion.

---

# 19. ANTI-OVERENGINEERING NÊN LÀ DECISION FILTER, KHÔNG PHẢI PROGRAM MỚI

Các rule đủ dùng:

```text
OBJECTIVE
DONE
NON-GOALS
CONSTRAINTS
```

Sau đó:

1. dùng existing capability trước;
2. narrow local fix trước helper;
3. helper trước subsystem;
4. subsystem chỉ khi current need chứng minh;
5. deterministic oracle trước model review;
6. một proportional verification pass;
7. stop khi DONE pass;
8. không reopen accepted phase nếu không có trigger mới;
9. framework mới phải retire/replace một layer cũ hoặc chứng minh benefit rõ.

Đây nên là policy nội tại của `sol-lean-codex`, không cần một bureaucracy mới.

---

# 20. PHÂN TÍCH RỦI RO NẾU CỰC ĐOAN HÓA TÀI LIỆU 21/8

## 20.1. Under-engineering

Nếu “minimal” bị hiểu thành “patch nhỏ nhất”, có thể:

- bỏ caller;
- bỏ persistent semantics;
- bỏ migration;
- bỏ rollback;
- bỏ adjacent contract.

Correct formulation:

> **smallest coherent causal solution**, không phải shortest diff.

## 20.2. Single-agent bottleneck

Nếu cấm mọi parallelism, một số independent workstream có thể chậm hơn không cần thiết.

Correct policy:

> default single-lane, explicit positive-value parallel exception.

## 20.3. Stop quá sớm

Stop-on-DONE phải đi cùng:

- protected invariants;
- proportional verification;
- credible adjacent risk.

Không dùng DONE để bỏ safety/quality.

## 20.4. Skill trimming phá domain safety

Một skill dài có thể dài vì chứa safety invariant, ví dụ attendance/domain workflow.

Không cắt chỉ vì line count.

## 20.5. Native compaction bị hiểu là “không cần durable state”

Sai.

Native compaction xử lý conversational context; nó không thay:

- source identity;
- EOCL state;
- proof ledger;
- accepted outcome history.

---

# 21. PHÂN TÍCH RỦI RO NẾU TRIỂN KHAI NGUYÊN VĂN VISION 18/8

## 21.1. Predictor explosion

Mỗi hypothesis tạo một field mới có thể dẫn tới schema bureaucracy.

Control:

> chỉ thêm predictor có plausible decision value và measurable provenance.

## 21.2. Service explosion

Các khái niệm như Oracle Strength Service, Repository Memory, Pre-Mutation Assessor có thể hữu ích về mặt conceptual nhưng không cần biến thành daemon/public service riêng.

Nên implement dưới dạng:

- internal function;
- ledger event;
- derived projection;
- optional report.

## 21.3. Learned router quá sớm

Local data còn sparse và drift theo source/runtime.

Nearest-history/simple empirical policy phải thắng simple baseline trước.

## 21.4. Review plane quá lớn

Independent review có giá trị ở high-risk uncertainty, nhưng always-on reviewer tạo cost center mới.

Review phải conditional.

## 21.5. Memory trở thành second truth

Repository memory chỉ là retrieval aid.

Nó không được override source/current contract.

---

# 22. MINIMAL EXPERIMENT CHO SKILL/CONTEXT — CHỈ KHI CẦN

Nếu sau này telemetry cho thấy context/skill overhead đáng kể, dùng experiment nhỏ.

Không cần một chương trình 6 phase ngay.

## 22.1. Research question

```text
Lean control-skill surface có giảm accepted-result cost/TTAR mà không giảm quality không?
```

## 22.2. Arms

```text
A = current control skill
B = same topology/effort + lean entrypoint
```

Giữ nguyên:

- source;
- task semantics;
- oracle;
- model/effort;
- cache stratum;
- runtime;
- tool contract.

## 22.3. Metrics

Primary:

- accepted rate;
- first-pass rate;
- TTAR;
- model calls;
- replan;
- total observed tokens.

Guardrail:

- missed requirement;
- wrong workspace;
- proof omission;
- terminal-report completeness;
- recovery failure.

## 22.4. Promotion

Lean version chỉ promote nếu outcome non-inferior và efficiency tốt hơn đủ rõ.

Không promote chỉ vì prompt ngắn hơn.

---

# 23. DECISION MATRIX CUỐI CÙNG

| Hạng mục | Quyết định | Lý do |
|---|---|---|
| Accepted-Result Learning thesis | **KEEP** | North Star đúng |
| EOCL / one writer / proof fingerprint | **KEEP** | Core moat / safety |
| Single Sol semantic authority | **KEEP DEFAULT** | Giảm coordination và split authority |
| Multi-agent tuyệt đối bị cấm | **REJECT** | Có niche positive-value cases |
| Sol Max-only | **REJECT DEFAULT** | Effort phải adaptive |
| Lean skill surface | **KEEP PRINCIPLE** | Giảm conflict/context khi có evidence |
| Rewrite toàn `sol-lean-codex` | **DO NOT** | Existing skill đã chứa phần lớn doctrine |
| Patch missing anti-OE rules | **GO, bounded** | Smallest coherent delta |
| Permanent anti-OE skill riêng | **DO NOT** | Duplicate control surface |
| Compression skill | **DO NOT** | Native compaction đã tồn tại |
| Durable external state | **KEEP** | Context ≠ history truth |
| StateM production authority | **DO NOT** | Duplicate state/transition owner |
| StateM principles | **ADOPT SELECTIVELY** | Phase-local state/checks hữu ích |
| TruthSnapshot | **GO** | Giải quyết real truth ambiguity |
| Truth DB/system mới | **DO NOT** | Projection đủ |
| P4 additional framework | **DO NOT** | Framework đã đủ; cần evidence |
| P4 organic collection | **CONTINUE** | Predictive gate còn thiếu natural variation |
| P5 implementation expansion | **HOLD** | OPEN_DORMANT đã đủ |
| P5 treatment | **GATED** | Chờ canonical readiness |
| P6 evidence | **RUN IN PARALLEL** | Evidence lane |
| P7 routing economics | **HOLD** | Rework economics ưu tiên trước |
| P8 joint optimizer | **DEFER** | Inputs chưa validated |
| P9 capacity scaling | **EVIDENCE-TRIGGERED** | Không pre-build fleet |
| Proof-cache expansion | **LOW PRIORITY** | Historical leverage thấp |
| Broad LSP expansion | **HOLD** | Semantic value chưa chứng minh |
| Skill cleanup as top project | **NO** | Rework effect lớn hơn và đã đo được |

---

# 24. TARGET ARCHITECTURE SAU KHI HỢP NHẤT TƯ DUY

```text
User / Operator
      |
      v
ChatWeb GPT-5.6 Sol
semantic controller + final acceptance
      |
      | lean decision contract
      v
Coding-VP / Coding MCP / EOCL
execution + mutation + proof + causal ledger
      |
      +--> deterministic tools
      +--> Git / filesystem
      +--> tests / build / schema
      +--> exact source/workspace truth
      |
      v
Accepted Result
      |
      v
Rich Outcome Evidence
      |
      +--> P4 prediction/outcome
      +--> repair/replan diagnostics
      +--> TTAR
      +--> quality
      +--> cost when observed
      +--> placement/routing evidence
      |
      v
Evidence-gated future policy
```

Điểm đặc biệt của kiến trúc này là:

> **Intelligence/control surface có thể nhỏ dần trong khi evidence corpus ngày càng giàu.**

Đây là một direction tốt vì mature system thường chuyển complexity từ “nhiều hành vi động khó kiểm soát” sang “dữ liệu quan sát giàu nhưng query được”.

---

# 25. CHỈ SỐ NORTH-STAR VÀ SUPPORTING METRICS

## 25.1. Primary

```text
first_pass_accepted_rate
repaired_rate
critical_defect_rate
TTAR p50/p90
accepted-result cost when observable
manual-fix/human-intervention
```

## 25.2. Decision-quality

```text
pre-mutation prediction coverage
repair-risk calibration
oracle strength/provenance
solution scope calibration
no-change correctness
```

## 25.3. Supporting

```text
token per accepted result
model calls per accepted result
tool hops
review calls
cache reuse
context bytes
placement burden
```

Supporting metric không được promote policy một mình.

---

# 26. STOP CONDITIONS CHO GIAI ĐOẠN HARDENING HIỆN TẠI

Truth/traceability hardening phải dừng khi:

- source/runtime/workspace/package/evidence truth được phân biệt rõ;
- wave effective objective audit được;
- UI không còn đồng nhất ONLINE với MATCHED;
- major historical incidents có deterministic casebook coverage;
- không còn concrete truth/provenance defect yêu cầu framework mới.

Sau đó:

> **STOP. Không biến hardening thành một platform con.**

P4 evidence collection tiếp tục tự nhiên mà không cần engineering wave mới.

---

# 27. CÁC NGUYÊN TẮC KỸ THUẬT NÊN ĐƯỢC XEM LÀ DOCTRINE DÀI HẠN

## D1 — Accepted result over activity

Không đo thành công bằng việc “hệ thống đã làm nhiều”.

## D2 — One authority, many read-only projections

Một writer/semantic authority rõ; UI/report là projection.

## D3 — Unknown is not zero

Cost/token/package/quality không quan sát được phải để unknown.

## D4 — Source/proof/live/package/release are separate claims

Không collapse.

## D5 — Single lane is default, not religion

Parallelism phải earn its coordination cost.

## D6 — Adaptive compute

Reasoning effort theo risk/uncertainty, không Max-only.

## D7 — Native before custom

Nếu platform/runtime đã có capability phù hợp, không xây duplicate.

## D8 — Evidence before abstraction

Abstraction mới phải giải quyết repeated current need hoặc safety boundary.

## D9 — Deterministic proof before model debate

Test/schema/compiler/invariant trả lời được thì không cần committee review.

## D10 — Stop on proven DONE

Không tiếp tục “hoàn thiện thêm” khi acceptance và risk-proportional verification đã đạt.

## D11 — Rich evidence, bounded context

Lưu sâu ngoài model context; chỉ project phần decision-relevant.

## D12 — Rework-first economics

Một improvement không thể được gọi là tốt nếu làm repair/TTAR xấu đi.

---

# 28. KẾT LUẬN CUỐI CÙNG

Nghiên cứu ngày 18/8 và case study ngày 21/8 thực chất mô tả hai nửa cần thiết của một hệ thống agent engineering trưởng thành.

Nửa thứ nhất nói:

> **Hệ thống phải biết học từ accepted results.**

Nửa thứ hai nói:

> **Hệ thống không được tự biến việc học đó thành một mạng lưới agent/skill/state/framework phức tạp hơn công việc nó đang giải quyết.**

Thực tế của Coding Web ngày 21/8 làm cho synthesis này trở nên rõ hơn.

Dự án đã có:

- authority;
- EOCL;
- recovery;
- proof;
- durable ledger;
- solution shadow;
- P5 dormant treatment machinery;
- routing/placement capability;
- compact public tool surface.

Dự án **không thiếu framework**.

Dự án đang thiếu:

- validated predictive repair signal;
- đủ natural causal outcome variation;
- treatment evidence;
- truth/provenance presentation hoàn toàn rõ;
- accepted-result evidence cho các optimization tiếp theo.

Dữ liệu 442 accepted runs và repaired TTAR khoảng 4,5× first-pass đưa ra một chỉ dấu kinh tế rất mạnh:

> **Rework mới là bài toán cần đánh trước.**

Vì vậy roadmap không nên quay lại “thêm nhiều capability” mà phải chuyển sang:

```text
truthful control
→ organic evidence
→ validated prediction
→ bounded P5 treatment
→ measured rework reduction
→ routing/placement optimization sau
```

Từ đây có thể chốt doctrine toàn dự án bằng một công thức:

> **LEAN CONTROL + RICH EVIDENCE + REWORK-FIRST ECONOMICS.**

Và một rule quyết định cho mọi feature/framework mới:

> **Nếu không chứng minh được một đường causal hợp lý tới accepted-result quality, repair, TTAR, cost hoặc safety — HOLD.**

Đây là bước chuyển từ một dự án “có rất nhiều năng lực agentic” sang một hệ thống engineering có kỷ luật kinh tế và khoa học: không hỏi “còn gì có thể xây?”, mà hỏi “thứ gì còn đáng xây?”.

---

# 29. SOURCE INDEX

## 29.1. Internal primary sources

1. `docs/research/260818_CODING_WEB_NGHIEN_CUU_KHOA_HOC_TOAN_DIEN_AI_AGENT_VA_LO_TRINH.md`
2. `docs/research/260821_SINGLE_SOL_SKILL_OPTIMIZATION_CONTEXT_COMPACTION_AND_ANTI_OVERENGINEERING_CASE_STUDY.md`
3. `docs/research/260821_CODING_WEB_MASTER_ENGINEERING_STRATEGY_AND_HISTORY.md`
4. `docs/CURRENT_STATE.md`
5. `docs/ROADMAP.md`
6. `.coding-tools/orchestration/ledger.sqlite3`
7. canonical `report_p4_readiness.py`
8. canonical `report_p5_baseline.py`
9. current `sol-lean-codex` skill entrypoint

## 29.2. Selected external research themes inherited from the two studies

Các external source dưới đây được hai research documents dùng để hình thành mechanism/hypothesis. Chúng không thay local evidence trong production decision.

### Single-agent / topology / routing

- *Towards a Science of Scaling Agent Systems*.
- *Rethinking the Value of Multi-Agent Workflow / Strong Single Agent Baseline*.
- MultiAgentBench.
- LLMRouterBench.
- ContextualRouter / past-performance retrieval.
- Conformal LLM routing.

### Context / memory / compaction

- OpenAI Codex/Responses native compaction guidance.
- MAGE / hierarchical execution-state memory.
- Repository Memory research.
- Adaptive/active context compression work.
- Prompt-cache stability research.

### Software-engineering harness / oracle / verification

- GitTaskBench.
- RepoReason / RepoReasoner.
- LogicHunter.
- RETRACE independent patch verification.
- SWE-ReX / mini-swe-agent.
- SlopCodeBench / RoadmapBench.

### Skills / instructions

- SWE-Skills-Bench.
- SkillsBench.
- SkillRouter.
- SkillsInjector.
- SkillRAE.
- SkillRet.
- AGENTS.md efficiency studies.

### Harness/state

- StateM.
- LangGraph and durable-state workflow patterns.
- Microsoft/OpenAI guidance on agentic workflows and meta-tools.

## 29.3. Interpretation rule

External research answers:

```text
what mechanism may matter?
what hypothesis should be tested?
what design pattern is plausible?
```

Local representative evidence answers:

```text
should Coding Web actually promote this policy?
```

Không đảo ngược hai tầng này.

---

# 30. OPERATOR DECISION CARD

```text
1. Có defect/consumer thật không?
   NO  -> DEFER

2. Primitive hiện tại giải được không?
   YES -> USE EXISTING

3. Có đang thêm authority/state/framework song song không?
   YES -> REJECT unless it replaces an old layer

4. Có đường causal tới accepted-result outcome không?
   NO  -> HOLD

5. Deterministic oracle trả lời được không?
   YES -> run it before model review

6. Work có thực sự parallel độc lập không?
   NO  -> single lane

7. Max có marginal expected value rõ không?
   NO  -> lower sufficient effort

8. DONE đã pass + proportional verification chưa?
   YES -> STOP

9. Policy cần promotion không?
   -> representative local evidence first

10. Unknown evidence?
   -> keep UNKNOWN, never fabricate green
```

---

**END OF SYNTHESIS**
