# Coding Web — Accepted Engineering Outcome & Solution Economics

## Phương pháp luận, nghiên cứu thực nghiệm và kế hoạch triển khai để tối ưu accepted code nhanh nhất, rẻ nhất

**Ngày nghiên cứu:** 2026-08-16  
**Workspace quan sát:** `E:\Github\Tools-Codex-web`  
**Branch:** `main`  
**HEAD quan sát khi bắt đầu tài liệu:** `cf6cb6ddbf29d90515d003ce72490ffda985c37f`  
**Trạng thái worktree:** dirty, có công việc khác đang tiếp diễn; tài liệu này **không** coi các thay đổi chưa accepted trong worktree là production truth.  
**Tài liệu nền trực tiếp:** `docs/research/260816_CHATWEB_SERVER_FIRST_COMPUTE_ORCHESTRATION_RESEARCH.md`  
**Loại tài liệu:** methodology / research synthesis / decision framework / experiment design / implementation roadmap  
**Trạng thái:** proposal + research plan; không tự động thay đổi routing, placement, proof policy hoặc runtime authority.

---

# 0. Mục tiêu chiến lược đã chuẩn hóa

Mục tiêu của hướng phát triển này được chuẩn hóa như sau:

> **Coding Web tự động phối hợp trí tuệ của ChatWeb với toàn bộ tài nguyên compute sẵn có để tạo accepted code nhanh nhất và rẻ nhất, trong khi máy người dùng chỉ chịu những workload thực sự cần chạy tại đó.**

Mục tiêu này không đồng nghĩa với:

- đẩy mọi command lên server;
- mở nhiều agent/worker nhất có thể;
- luôn chọn model rẻ nhất;
- luôn chạy song song;
- biến máy chủ thành mutation authority thứ hai;
- xây một hệ thống cluster/fleet-management tổng quát;
- tối ưu CPU utilization nhưng làm time-to-accepted-result xấu hơn;
- tối thiểu hóa số dòng code bằng mọi giá;
- dùng YAGNI như lý do bỏ error handling, robustness hoặc extension quality cần thiết;
- thêm một “persona tối giản” vào mọi model/worker rồi giả định hệ thống tốt hơn.

Đích cần tối ưu là **accepted engineering outcome**. Một model call rẻ, một patch ngắn, một build server nhanh, một cache hit hay một benchmark xanh chỉ là tín hiệu cục bộ. Chúng chỉ có giá trị khi đóng góp vào kết quả accepted cuối cùng với tổng thời gian, tổng chi phí, rework và maintenance burden thấp hơn.

---

# 1. Kết luận điều hành

## 1.1 Thesis chính

Báo cáo server-first trước đã tối ưu câu hỏi:

```text
workload đã tồn tại
        ↓
model nào?
        ↓
node nào?
        ↓
proof nào?
```

Nghiên cứu Ponytail và các nghiên cứu harness gần đây cho thấy còn một lớp phải đặt **trước toàn bộ pipeline đó**:

```text
workload này có thực sự cần tồn tại không?
```

Do đó pipeline mục tiêu nên trở thành:

```text
USER REQUEST
    |
    v
UNDERSTAND ACTUAL BEHAVIOR / AUTHORITY
    |
    v
SOLUTION ECONOMICS
  - eliminate unnecessary work
  - reuse existing behavior
  - stdlib/native/already-installed capability
  - choose smallest causal solution
  - preserve robustness/security/extension quality
    |
    v
WORK GRAPH
    |
    +--> semantic/model route
    +--> context plan
    +--> compute placement
    +--> proof plan
    |
    v
EXECUTION
    |
    v
ACCEPT / REJECT
    |
    v
LEDGER LEARNING
```

**Ponytail không nên được tích hợp nguyên plugin hoặc persona.** Giá trị của nó là một hypothesis mạnh: nhiều coding workload bị phình trước khi execution bắt đầu, và một disciplined solution-selection policy có thể cắt lượng code, token, tool work, build/proof surface và compute. Nhưng independent evidence cũng cho thấy aggressive minimality có thể làm giảm hidden-edge robustness. Vì repaired accepted outcome hiện đắt hơn first-pass rất nhiều trong baseline nội bộ trước đây, một policy giảm 20% work nhưng tăng repair probability có thể làm tổng TTAR xấu đi.

Phương pháp đúng là:

> **Biến minimality thành một policy có thể quan sát, fingerprint, shadow, A/B, non-inferiority gate và rollback — không biến nó thành niềm tin mặc định.**

## 1.2 Bốn nguyên tắc kiến trúc

1. **Quality floor trước economics.** Security, correctness, data/financial semantics, compatibility, authority và truthful proof là hard constraints.
2. **Minimize engineering work, không minimize LOC.** LOC chỉ là secondary diagnostic.
3. **Policy là một phần của system route.** `model + harness + policy + context + topology + proof` mới là đơn vị benchmark đúng.
4. **Không mua complexity nếu không có evidence rằng complexity đó giảm expected engineering cost hoặc bảo vệ invariant thật.** Đây là phiên bản rộng hơn, thực dụng hơn của YAGNI.

## 1.3 Thứ tự triển khai đề xuất

```text
S0  Measurement + policy identity
S1  Solution-Economics shadow assessment
S2  Deterministic reuse / causal-scope helpers
S3  Representative paired experiments
S4  Conservative lean-policy canary
S5  Joint solution + model + compute + proof optimization
S6  Historical/adaptive policy learning
```

Không thay đổi public Smart-v3 tool surface. Không tạo database/orchestrator thứ hai. Không bật automatic non-deterministic model routing hoặc remote placement chỉ vì tài liệu này tồn tại.

---

# 2. Câu hỏi nghiên cứu cần trả lời

Tài liệu này không bắt đầu từ “thêm tính năng nào”, mà từ các research questions có khả năng bị bác bỏ.

## RQ1 — Work elimination có giảm accepted-result economics thật không?

**Hypothesis H1:** một `solution_economics` policy có thể giảm median TTAR và/or total cost per accepted result trên task có over-build opportunity mà không làm first-pass acceptance giảm quá quality margin.

Phản chứng:

- LOC giảm nhưng repair tăng;
- output token giảm nhưng prompt/policy overhead tăng;
- patch ngắn hơn nhưng proof phải rộng hơn;
- native shortcut ép verification về local và làm local burden tăng;
- reuse existing abstraction nhưng hiểu sai contract, tạo rework.

## RQ2 — Minimality nên áp dụng với task nào?

**Hypothesis H2:** benefit phụ thuộc mạnh vào task shape. UI/native-capability, routine CRUD, localized strong-oracle bugs và duplicated helpers có expected value cao; distributed state, auth, recovery, parsers/input handling, migrations và weak-oracle work cần lean pressure thấp hơn.

## RQ3 — Minimality có tương tác với model tier không?

**Hypothesis H3:** cùng một policy có thể giúp model mạnh nhưng làm weaker model under-implement. Vì vậy policy intensity phải được calibration cùng model/harness, không phải global prompt.

## RQ4 — Minimality có tương tác với server-first placement không?

**Hypothesis H4:** giảm work trước placement có thể tạo lợi ích lớn hơn tối ưu placement sau khi work đã phình. Nhưng một giải pháp ít code hơn đôi khi tạo local affinity hoặc platform-specific proof, làm server-first kém đi.

## RQ5 — Có thể dự báo over-build trước mutation không?

**Hypothesis H5:** server/LSP/repository evidence có thể tạo đủ tín hiệu `reuse/native/stdlib/existing_dependency/causal_scope` để ChatWeb chọn giải pháp nhỏ hơn mà không cần thêm một agent tự do mới.

## RQ6 — “Simple” có giảm maintenance cost dài hạn không?

**Hypothesis H6:** lợi ích chỉ xuất hiện khi simplicity giảm change surface/coupling mà không làm extension quality xấu. Một hack 20 LOC ở hotspot có thể đắt hơn một extension point 50 LOC nếu subsystem thay đổi liên tục.

---

# 3. Evidence hierarchy và phương pháp nghiên cứu

Mọi kết luận trong chương trình này phải ghi loại evidence.

## 3.1 Evidence classes

### A. `MEASURED_LOCAL`

Bằng chứng từ chính Coding Web:

- `.coding-tools/orchestration/ledger.sqlite3`;
- `performance.json`;
- task history/state;
- exact RUN/WAVE/proof;
- paired evaluations;
- server/local workload timings;
- accepted/repaired outcome.

Đây là evidence mạnh nhất để promote production policy.

### B. `REPRODUCIBLE_EXTERNAL`

Benchmark/repository bên ngoài có code, raw/aggregate data hoặc repeatable harness. Ví dụ:

- Ponytail agentic benchmark;
- independent PonyBench v3;
- SWE-agent;
- repository-harness;
- Harness Handbook implementation.

Dùng để thiết kế hypothesis/method, không dùng trực tiếp làm production threshold.

### C. `SCIENTIFIC_EXTERNAL`

Paper peer-reviewed hoặc preprint có experimental method rõ:

- The Scaffold Effect;
- Harness Handbook;
- CodeFlowBench;
- EGSS;
- Timely Machine;
- AI-generated-code technical-debt/readability studies.

Dùng để hiểu mechanism, confounders và evaluation design.

### D. `FIELD_REPORT`

Issue/community report. Có giá trị cảnh báo operational, nhưng không được dùng như controlled causal evidence.

### E. `DERIVED_HYPOTHESIS`

Suy luận của dự án từ các evidence ở trên. Phải ghi rõ là hypothesis cho đến khi có local experiment.

## 3.2 Quy tắc không trộn evidence

Không được:

- lấy Ponytail `-54% LOC` làm forecast của Coding Web;
- lấy independent Opus benchmark làm threshold cho Mini/Luna/Sol;
- lấy synthetic server speedup làm TTAR production;
- lấy model judge score thay executable proof nếu oracle có thể chạy;
- lấy accepted-only sample để suy ra toàn bộ outcome distribution;
- coi internal estimated credits là provider billing;
- coi unknown cost là zero.

---

# 4. Nghiên cứu Ponytail — điều gì đã được chứng minh và điều gì chưa

## 4.1 Cơ chế thực sự của Ponytail

Ponytail không chỉ nói “viết ít code”. Core policy là một ladder chạy sau khi hiểu flow:

```text
1. Có cần tồn tại không?
2. Đã có trong codebase chưa?
3. Stdlib làm được không?
4. Native platform làm được không?
5. Dependency đã cài có làm được không?
6. Có thể cực nhỏ không?
7. Chỉ sau đó mới custom implementation tối thiểu.
```

Bugfix còn có rule root-cause/shared-path thay vì vá symptom. Policy cũng giữ explicit safety floor: trust-boundary validation, data-loss handling, security, accessibility và các yêu cầu được user chỉ định không được cắt.

**Điểm đáng học:** solution-selection trước code generation.

**Điểm không nên copy máy móc:** shortest LOC/files, always-on persona, một “intensity” chung cho mọi task.

## 4.2 Official agentic benchmark đã sửa methodological flaw

Ponytail ban đầu dùng single-shot benchmark và bị issue #126 chỉ ra rằng baseline quá chatty, nên “lines of answer” phóng đại lợi ích. Tác giả công nhận và rebuild thành real headless Claude Code session trên repository thật, cùng agent có/không plugin, `git diff` làm output measure và executable adversarial cases cho safety.

Trong benchmark agentic công bố trên Haiku 4.5, 12 feature tasks cho kết quả trung bình khoảng:

| Metric | Ponytail vs no-skill |
|---|---:|
| Added LOC | -54% |
| Tokens | -22% |
| Cost | -20% |
| Time | -27% |
| Safety trong suite | 100% |

Nhưng distribution rất không đồng đều:

- native-feature traps như date/color picker giảm rất mạnh;
- irreducible backend tasks gần như hội tụ;
- do đó “benefit conditional on reducibility” là conclusion tốt hơn “Ponytail luôn tiết kiệm 54%”.

## 4.3 Contamination bug là bài học lớn hơn headline number

Trong quá trình rebuild, benchmark từng bị contamination vì lifecycle hook/plugin có thể chạy ở baseline arm. Điều này làm baseline vô tình nhận treatment. Họ phải isolate setting sources và plugin directory per arm.

Đây là bài học trực tiếp cho Coding Web:

```text
source identity
+ model identity
+ policy identity
+ hook/plugin identity
+ environment identity
+ cache stratum
+ oracle identity
+ topology identity
```

phải thuộc pair eligibility. Nếu một treatment “rò” sang control, pair bị invalid.

## 4.4 Independent PonyBench v3 — bằng chứng quan trọng nhất về trade-off

Independent benchmark sau khi sửa chính methodology của họ chạy:

```text
24 jobs
x 4 conditions (baseline/lite/full/ultra)
x 5 repetitions
= 480 builds
```

Đặc điểm đáng học:

- dùng real installed plugin, không paste SKILL vào prompt;
- activation verify out-of-band;
- executable hidden correctness tests;
- real security attacks;
- robustness probes cho edge cases không nêu rõ;
- parser-based logical statement counting;
- intention-to-treat principle;
- non-inferiority margins;
- cluster/bootstrap + hierarchical-statistics thinking;
- frozen analysis plan trước paid run.

Kết quả được báo cáo:

- Full khoảng 44% ít code hơn baseline;
- khoảng 53% fewer logical statements;
- correctness gần tương đương trong setup;
- tested security attacks không thấy regressions;
- **robustness giảm trên 5/24 tasks có unstated edge cases**;
- higher intensity làm nhóm robustness-sensitive xấu hơn.

Đây là bằng chứng chống lại “maximize minimality”.

## 4.5 Điều Ponytail chưa chứng minh

Không có đủ bằng chứng để nói:

- SWE-Bench/Terminal-Bench resolution rate sẽ không giảm;
- lợi ích giống nhau trên mọi model family/tier;
- full/ultra luôn tốt hơn lite;
- maintenance cost dài hạn giảm;
- distributed/server-first execution hưởng cùng tỷ lệ;
- native/stdlib choice luôn tạo accepted outcome rẻ hơn;
- one small test luôn đủ proof.

Chính thảo luận project cũng ghi nhận model dependence và yêu cầu benchmark full agentic success.

---

# 5. Nghiên cứu harness và coding-agent liên quan

## 5.1 The Scaffold Effect — harness là hidden variable

**Vats & Golev, 2026, arXiv:2607.22585.**

Paper so sánh cùng model trên ba harness khác nhau và báo cáo harness choice có thể tạo khác biệt rất lớn về tokens-per-solved-task, tới khoảng 40x trong setup của họ; failure fingerprints còn có xu hướng lặp theo harness. Kết luận quan trọng không phải con số 40x áp cho Coding Web, mà là:

> **Model name không phải đơn vị đánh giá đủ. Harness-model pair mới quyết định chi phí, latency và oversight burden thực tế.**

Áp dụng:

```text
route_identity = model
               + system/policy
               + context strategy
               + tool surface
               + execution topology
               + proof policy
```

Do đó `lean-v1 + Mini` phải được coi là route khác `baseline-policy + Mini`.

## 5.2 Harness Handbook — behavior localization là bottleneck

**Wang et al., 2026, arXiv:2607.13285.**

Harness Handbook tổ chức code theo behavior thay vì file/module và dùng Behavior-Guided Progressive Disclosure (BGPD): system overview → behavior units → verifiable implementation evidence. Evaluation của tác giả cho thấy planning/localization tốt hơn và planner token thấp hơn, đặc biệt với scattered implementation sites và cross-module behavior.

Áp dụng:

- solution minimization phải chạy **sau behavior localization**, không trước;
- “reuse existing” chỉ an toàn khi biết existing behavior nằm ở đâu và contract gì;
- server semantic plane nên đưa candidate behavior/symbol, không đẩy cả repo vào ChatWeb;
- behavior map chỉ đáng triển khai nếu local data chứng minh localization/context waste là bottleneck đáng kể.

## 5.3 CodeFlowBench — reuse existing code là khó thật

**Wang et al., ACL 2026, CodeFlowBench.**

Benchmark formalize multi-turn iterative code generation với reuse existing functions. Kết quả cho thấy performance giảm khi dependency complexity tăng.

Implication:

> “Reuse trước khi write” là nguyên lý tốt, nhưng retrieval/reuse không miễn phí và không nên hoàn toàn giao cho model tự mò.

Coding Web nên dùng LSP/call graph/dependency evidence để giảm search entropy trước semantic decision.

## 5.4 EGSS — adaptive scaling tốt hơn brute-force ensemble

**Mao et al., ACL 2026.**

EGSS nhắm test-time scaling trong software engineering, vì brute-force large ensemble rất tốn compute. Paper báo cáo vừa tăng resolved ratio vừa giảm token so với các TTS baselines trong setup của họ.

Implication:

- không fan-out nhiều candidate mặc định;
- minimality, model escalation và worker count đều phải adaptive;
- khi uncertainty thấp, dừng sớm;
- khi uncertainty/entropy cao và oracle mạnh, mới mua thêm compute.

## 5.5 Timely Machine — wall-clock quan trọng hơn generation length

**Ma et al., ACL 2026.**

Paper chỉ ra trong agentic setting, tool latency làm test-time không còn tương đương generation length. Smaller model có thể lợi khi feedback nhanh; larger model có thể thắng khi tool feedback latency cao do interaction quality tốt hơn.

Implication trực tiếp:

- không tối ưu token/model price riêng;
- remote server có queue/transfer latency phải đi vào route economics;
- một model rẻ nhưng cần nhiều tool turns có thể TTAR xấu;
- workload elimination có leverage cao vì nó loại cả tool latency, không chỉ output token.

## 5.6 AI-generated code debt/readability studies — simplicity proxy không đủ

Các empirical studies 2026 cho thấy:

- AI-authored commits có thể tạo issue/technical debt tồn tại dài hạn trong large-scale datasets;
- readability-focused agent refactoring không đảm bảo traditional maintainability metrics tốt hơn; có nghiên cứu thấy Maintainability Index giảm hoặc Cyclomatic Complexity tăng trong nhiều commits.

Implication:

> Code ngắn hơn hoặc “trông đơn giản hơn” không được dùng làm acceptance signal.

Change surface, extension quality, hotspot frequency và proof phải được xét riêng.

---

# 6. Định nghĩa Accepted Engineering Outcome

Một task chỉ được coi là accepted engineering outcome khi:

```text
requested behavior satisfied
AND authoritative source identity is known
AND change respects authority/security/data/compatibility invariants
AND sufficient proof passed on the right identity/environment
AND no unresolved hard blocker
AND acceptance owner explicitly accepts
```

## 6.1 Quality floor

Các dimension sau là hard gates, không phải weighted preferences:

```text
correctness
security / trust boundaries
privacy / secrets
financial/data meaning
compatibility / public contract
recovery / durability when relevant
authority / write ownership
proof truthfulness
```

Nếu một strategy vi phạm quality floor, `score = invalid`, không phải “score cao hơn”.

## 6.2 TTAR

```text
TTAR = context
     + decision
     + queue
     + transfer
     + execution
     + proof
     + review
     + repair
     + handoff
```

## 6.3 CAR — Cost per Accepted Result

```text
CAR = model cost
    + remote compute cost
    + local opportunity cost
    + transfer/cache cost
    + retry/repair cost
    + review cost
```

## 6.4 Maintenance horizon

Để tránh tối ưu “rẻ hôm nay, đắt tháng sau”, thêm expected maintenance term:

\[
EMC(s) = P(change\_again \mid surface) \times E(future\_change\_cost \mid strategy)
\]

Tổng expected engineering economics:

\[
EEE(s,r,p,v) = E[TTAR] + \lambda_c E[CAR] + \lambda_l E[LocalBurden] + \lambda_m EMC + \lambda_o OperationalRisk
\]

với:

- `s`: solution strategy;
- `r`: semantic/model route;
- `p`: compute placement;
- `v`: proof strategy.

Quality floor được áp trước hàm này.

---

# 7. Solution Economics — layer mới cần formalize

## 7.1 Mục tiêu

`Solution Economics` trả lời:

> Với behavior/invariant đã hiểu, chiến lược triển khai nào tạo expected accepted-result cost thấp nhất?

Không trả lời:

> Viết ít code nhất bằng cách nào?

## 7.2 Strategy taxonomy

```text
NO_CHANGE_REQUIRED
DELETE_EXISTING
REUSE_EXISTING
CONFIGURE_EXISTING
STDLIB
NATIVE_PLATFORM
EXISTING_DEPENDENCY
SMALL_CUSTOM
STRUCTURED_EXTENSION
ARCHITECTURAL_CHANGE
```

`STRUCTURED_EXTENSION` và `ARCHITECTURAL_CHANGE` không phải “thất bại YAGNI”; chúng hợp lệ nếu hiện tại có evidence cần complexity đó.

## 7.3 Structured assessment

Đề xuất internal object:

```yaml
solution_economics:
  schema_version: 1

  behavior:
    objective: ...
    confidence: high
    integration_width: medium
    input_uncertainty: low
    oracle_strength: strong

  candidates:
    - strategy: REUSE_EXISTING
      evidence:
        symbol: existing_helper
        behavior_match: high
      expected:
        files_touched: 1
        new_dependencies: 0
        proof_tier: focused
        remote_portability: high
        local_affinity: none
        maintenance_risk: low
        robustness_risk: low

    - strategy: SMALL_CUSTOM
      expected:
        files_touched: 2
        new_dependencies: 0
        proof_tier: subsystem
        maintenance_risk: medium

  selected: REUSE_EXISTING
  decision_reason_codes:
    - EXISTING_BEHAVIOR_MATCH
    - LOWER_CHANGE_SURFACE
    - SAME_QUALITY_FLOOR

  rejected:
    SMALL_CUSTOM: DUPLICATES_EXISTING_BEHAVIOR

  confidence: medium
  mutation_gate: allowed
```

## 7.4 Không cần public tool mới

Object này là projection/internal step của `agent_workflow.prepare` hoặc policy evaluator. Smart-v3 vẫn giữ surface nhỏ.

---

# 8. Solution Gate — thứ tự quyết định

## 8.1 Gate 0 — Finish line

Xác định:

- behavior cần thấy;
- invariants phải giữ;
- source/worktree;
- acceptance owner;
- cheapest sufficient oracle.

## 8.2 Gate 1 — Behavior localization

Không tối giản khi chưa hiểu implementation boundary.

Evidence ưu tiên:

```text
failing test / stack / exact symbol
LSP definitions/references
call/dependency graph
config/schema key
maintained architecture/authority docs
current implementation
```

## 8.3 Gate 2 — Can the work disappear?

Các câu hỏi:

```text
request đã được đáp ứng chưa?
feature có thật sự cần tồn tại riêng không?
change có thể là deletion/configuration không?
existing behavior có thể reuse không?
```

## 8.4 Gate 3 — Platform/library reuse

Theo thứ tự evidence-driven:

```text
stdlib
native platform
already-installed dependency
```

Nhưng phải tính:

- portability;
- proof locality;
- compile/runtime overhead;
- security surface;
- future compatibility.

## 8.5 Gate 4 — Smallest causal change

Bugfix phải target demonstrated cause/shared point nếu có. Không chọn smallest diff ở sai layer.

## 8.6 Gate 5 — Extension-quality check

Nếu surface có:

- high change frequency;
- repeated modifications;
- stable public boundary;
- known second consumer;
- process/security/authority boundary;

thì một abstraction/extension point có thể economically đúng ngay cả khi LOC nhiều hơn.

## 8.7 Gate 6 — Route/placement/proof

Chỉ sau khi strategy đã chọn mới quyết định:

```text
model route
context packet
remote/local placement
proof tier
```

---

# 9. Evidence-Gated Complexity thay cho YAGNI tuyệt đối

## 9.1 Rule

> **Không mua complexity nếu không có evidence hiện tại rằng complexity đó giảm expected engineering cost hoặc bảo vệ invariant thật.**

## 9.2 Evidence hợp lệ để mua complexity

- second real consumer;
- repeated change history;
- known near-term contracted requirement;
- authority/trust boundary;
- process/transport boundary;
- test seam cần thiết cho deterministic proof;
- performance bottleneck đã đo;
- portability/platform split thật;
- compatibility/public contract;
- recovery/durability semantics;
- data migration/versioning.

## 9.3 Evidence không đủ

- “sau này có thể cần”;
- “best practice nói nên có interface”;
- framework generality không có consumer;
- config option không ai dùng;
- feature flag không có rollout need;
- abstraction chỉ để code “trông enterprise”.

---

# 10. Lean Pressure phải adaptive

Không thêm manual global mode `lite/full/ultra` vào product. Runtime suy ra `lean_pressure` từ task characteristics.

## 10.1 Dimensions

```text
risk
oracle_strength
integration_width
input_uncertainty
behavior_localization_confidence
change_frequency
local_affinity
robustness_sensitivity
```

## 10.2 Suggested policy matrix

| Task shape | Lean pressure | Lý do |
|---|---:|---|
| Native UI control / obvious platform feature | HIGH | Over-build opportunity lớn |
| Simple CRUD / duplicated helper | HIGH | Reuse dễ chứng minh |
| Localized strong-oracle bug | MEDIUM-HIGH | Causal patch dễ verify |
| Routine cross-file feature | MEDIUM | Giữ extension quality |
| Parser / input handling | LOW | Hidden-edge risk cao |
| Auth/security/privacy | LOW | Trust-boundary guards |
| Recovery/state machine | LOW | Latent state-space risk |
| Distributed concurrency | LOW | Small diff dễ sai semantics |
| Migration/compatibility | LOW | Future states quan trọng |
| Weak oracle / ambiguous requirement | VERY LOW | Under-implementation khó phát hiện |
| Deterministic transform | HIGH | Low semantic risk |

## 10.3 Formula gợi ý

```text
LeanPressure = reducibility_signal
             + reuse_confidence
             + oracle_strength
             - robustness_risk
             - integration_width
             - authority_risk
             - future_change_risk
```

Không cần ML ban đầu. Dùng reason codes và deterministic buckets.

---

# 11. Causal Fix Gate cho bugfix

## 11.1 Lý do

Một “small patch” tại symptom có thể rẻ lúc viết nhưng tạo sibling bugs và repair sau. Vì rework penalty lớn, root-cause targeting là economic optimization.

## 11.2 Gate

Trước mutation bugfix, nếu target symbol/shared function có nhiều callers:

```text
1. locate failing path
2. identify candidate cause
3. inspect bounded callers/references
4. decide shared-cause vs path-specific behavior
5. patch smallest causal surface
```

Không grep toàn repo mặc định. Chỉ mở reference expansion khi nó có khả năng đổi location của fix.

## 11.3 Metrics

```text
symptom_patch_rate
shared_cause_patch_rate
sibling_regression_rate
repair_due_to_wrong_layer
```

---

# 12. Repository reuse và Behavior Map

## 12.1 Server nên làm phần deterministic

Để ChatWeb không tốn context tự tìm “đã có gì trong repo”, server/LSP có thể cung cấp:

```yaml
reuse_evidence:
  symbols:
    - name: ...
      definition: ...
      references: ...
      semantic_similarity: ...
  dependencies:
    - package: ...
      installed: true
  native_capabilities:
    - platform: ...
  call_chain:
    - ...
```

## 12.2 Behavior Map chỉ build khi data biện minh

Harness Handbook cho thấy behavior-centric representation có thể giảm planner tokens/localization failures. Nhưng Coding Web đã có LSP/search và project-specific maintained docs. Vì vậy:

```text
IF localization/context waste remains material after semantic activation
AND cross-module behavior misses are a frequent repair cause
THEN prototype behavior map
ELSE do not add another index/knowledge system
```

Generated map là derived cache, repository vẫn là source of truth.

---

# 13. Change Surface thay vì LOC

LOC không phản ánh maintenance burden đầy đủ.

## 13.1 Change Surface vector

```yaml
change_surface:
  files_added: 0
  files_modified: 2
  public_interfaces_added: 0
  dependencies_added: 0
  config_keys_added: 0
  persistent_states_added: 0
  processes_added: 0
  protocols_changed: 0
  migrations_added: 0
  permissions_changed: 0
```

## 13.2 Weighted diagnostic score

\[
CS = w_f F + w_i I + w_d D + w_c C + w_s S + w_p P + w_m M
\]

Không dùng score này để auto reject. Dùng để:

- trigger review;
- compare candidate strategies;
- stratify experiments;
- estimate maintenance burden.

## 13.3 Overbuild risk

Signals:

- new dependency cho tiny task;
- many new files với low integration width;
- wrapper chỉ delegate;
- interface có một implementation **mà không phải boundary**;
- config key không có current variation;
- duplicate helper;
- speculative compatibility layer;
- new process/state machine không có current requirement.

Counter-signals phải giữ:

- security/authority boundary;
- process boundary;
- stable public contract;
- platform abstraction thật;
- deterministic test seam;
- repeated change hotspot.

---

# 14. Maintenance Economics

## 14.1 Hotspot-aware complexity

Git history có thể cung cấp:

```text
change_frequency
co-change frequency
bug-fix density
repeated touch by subsystem
```

Một minimal solution ở hotspot có thể cần extension quality cao hơn.

## 14.2 Simplification debt

Không cần dùng source comment `ponytail:` làm primary storage. Dùng durable structured record:

```yaml
simplification_decision:
  run_id: ...
  wave_id: ...
  scope: ...
  chosen_strategy: SMALL_CUSTOM
  deferred_strategy: STRUCTURED_EXTENSION
  ceiling: "single worker; no cross-account concurrency"
  upgrade_trigger: "p95 queue > 2s or second writer appears"
  evidence: ...
  accepted_at: ...
```

Khi trigger xuất hiện, system có thể surface debt. Không auto refactor chỉ vì time passed.

---

# 15. Tích hợp với Server-First Compute

## 15.1 Solution first, placement second

Sai:

```text
request
-> server/local placement
-> execute whatever plan model invented
```

Đúng:

```text
request
-> understand
-> shrink/eliminate work
-> materialize work graph
-> place each remaining workload
```

## 15.2 Native/stdlib không luôn thắng

Ví dụ native Windows API có thể ít code hơn portable implementation nhưng buộc proof local Windows. Solution economics phải tính:

```text
implementation work
+ portability
+ remote eligibility
+ local affinity
+ proof cost
```

## 15.3 Existing dependency không luôn thắng

Dependency đã cài có thể làm code ngắn hơn nhưng kéo:

- compile time;
- binary size;
- startup;
- security surface;
- platform restrictions.

Do đó `existing dependency` là candidate, không phải automatic winner.

## 15.4 Avoided Engineering Work

KPI tốt hơn saved LOC:

```text
avoided_model_calls
avoided_context_bytes
avoided_tool_hops
avoided_files
avoided_dependencies
avoided_build_ms
avoided_proof_ms
avoided_remote_compute_ms
avoided_local_heavy_ms
avoided_repair_ms
```

Cuối cùng quy về TTAR/CAR/quality.

---

# 16. Joint optimization nhưng không brute force

Không thử mọi tổ hợp:

```text
solution x model x node x proof
```

Dùng hierarchical decision:

```text
1. define accepted outcome
2. localize behavior
3. generate 1-3 realistic solution strategies
4. hard quality/authority filter
5. select strategy by expected engineering economics
6. select semantic route
7. select compute placement
8. select cheapest sufficient proof
9. execute once
10. replan only with new evidence
```

## 16.1 Candidate strategy count

Không cần model brainstorm 10 architectures. Mặc định tối đa:

```text
1 obvious reuse/minimal strategy
+ 1 direct custom strategy
+ 1 structured extension only when evidence exists
```

Nếu một strategy rõ ràng dominates sau hard filter, không tạo thêm alternatives.

---

# 17. Policy Capsule cho model/worker lanes

Ponytail phải re-inject policy vào subagents vì parent context không tự truyền. Coding Web có bounded packet/handoff nên có thể truyền structured constraints thay vì full persona prose.

```yaml
policy_capsule:
  solution_policy: lean_solution_v1
  solution_policy_fp: ...
  selected_strategy: REUSE_EXISTING

  objective: ...
  scope: ...

  protected_invariants:
    - ...

  expansion_budget:
    files_soft: 2
    dependencies_soft: 0

  stop_conditions:
    - UNKNOWN_INPUT_CONTRACT
    - AUTHORITY_AMBIGUITY
    - REQUIRED_SCOPE_EXPANDS
    - EXISTING_REUSE_CONTRACT_MISMATCH

  proof: ...
```

`soft` budget chỉ trigger review/replan, không chặn một correct fix cần vượt budget.

---

# 18. Proof Economics và Robustness Gate

## 18.1 “One check” không đủ là universal policy

Ponytail’s “one runnable check” là useful minimum heuristic, nhưng Coding Web có state/authority/recovery/distributed boundaries. Proof vẫn theo progressive ladder:

```text
static/diff
-> focused behavior
-> affected subsystem/consumer
-> platform/local-specific
-> release-wide only when needed
```

## 18.2 Hidden-edge robustness

Independent PonyBench cho thấy minimality có thể bỏ defensive handling khi input edge không được spec rõ. Vì vậy task có `input_uncertainty` cao cần robustness probe hoặc lean pressure thấp.

## 18.3 Robustness taxonomy

```text
TRUST_BOUNDARY        hard gate
DATA_LOSS             hard gate
PUBLIC_INPUT          strong gate
INTERNAL_BUT_UNSTABLE medium gate
CONTROLLED_INTERNAL   lower gate
```

## 18.4 Proof-selection economics

Proof plan phải xét strategy. Một strategy ít code nhưng đụng public parser có thể cần nhiều proof hơn direct internal change.

---

# 19. Measurement schema cần bổ sung

Dùng canonical ledger, không tạo analytics DB mới.

## 19.1 Policy identity

```yaml
policy_identity:
  solution_policy: baseline | lean_solution_v1
  solution_policy_version: ...
  solution_policy_fp: sha256:...
  lean_pressure: none | low | medium | high
```

## 19.2 Strategy observation

```yaml
solution_observation:
  candidate_count: 2
  selected_strategy: REUSE_EXISTING
  reuse_found: true
  native_candidate: false
  stdlib_candidate: false
  existing_dependency_candidate: true
  rejected_complexity_count: 1
  decision_confidence: medium
```

## 19.3 Change surface

```yaml
change_surface:
  added_lines:
  deleted_lines:
  files_added:
  files_modified:
  dependencies_added:
  public_interfaces_added:
  config_keys_added:
  state_machines_added:
  processes_added:
```

## 19.4 Economics

```yaml
accepted_economics:
  accepted:
  first_pass:
  ttar_ms:
  repair_ms:
  model_cost:
  model_calls:
  context_bytes:
  tool_hops:
  proof_ms:
  local_heavy_ms:
  remote_compute_ms:
  human_intervention:
```

## 19.5 Policy contamination fields

Pair-eligibility fingerprint phải có:

```text
source/worktree fp
runtime/tool contract fp
solution policy fp
routing policy fp
verification runner fp
environment id
oracle id
model/route
review policy
topology id
cache stratum
hook/plugin set when relevant
```

---

# 20. Experimental Methodology

Đây là phần quyết định việc policy có được promote hay không.

## 20.1 Không chạy một mega factorial ngay

Nếu ngay lập tức test:

```text
3 policies x 5 models x 3 placements x 4 proof modes
```

thì sample bị loãng, chi phí lớn và khó attribution.

Dùng staged causal design.

## 20.2 Experiment E1 — Policy effect, fixed route/topology

Mục tiêu: minimality policy có giúp hay hại khi mọi thứ khác cố định?

```text
A: current baseline solution policy
B: lean_solution_v1
```

Giữ cố định:

- same source snapshot;
- same task semantics;
- same ChatWeb/controller topology;
- deterministic route hoặc cùng explicit model;
- same oracle;
- same environment;
- same placement;
- randomized execution order/cache stratum.

## 20.3 Experiment E2 — Model interaction

Chỉ sau E1.

Test một số task classes trên:

```text
strong route vs lower-cost candidate route
```

Mục tiêu:

- policy benefit có giữ trên lower tier không?
- under-implementation có tăng không?
- policy × model interaction magnitude.

Không promote Mini/Luna auto từ experiment này nếu runtime evidence gate khác chưa đạt.

## 20.4 Experiment E3 — Placement interaction

Test cùng accepted strategy với:

```text
local execution
vs
eligible remote server
```

Mục tiêu:

- solution minimization giảm amount of remote compute bao nhiêu;
- strategy có làm local affinity thay đổi không;
- placement break-even thay đổi thế nào.

## 20.5 Experiment E4 — Maintenance follow-up

Mỗi selected solution nhận một pre-written follow-up change request.

Measure:

```text
follow-up success
follow-up TTAR
follow-up change surface
new repair
```

Đây là proxy thực dụng cho future change cost, tốt hơn suy từ LOC.

---

# 21. Task Corpus

Corpus phải đại diện và có task “khó cho minimality”.

## 21.1 Strata

```text
A. over-build opportunity
B. irreducible simple work
C. localized bug strong oracle
D. wrong-layer/root-cause trap
E. input/robustness trap
F. security/trust boundary
G. cross-file semantic change
H. recovery/state machine
I. distributed/concurrency
J. platform-specific UI/device
K. build/release/performance
L. repeated-hotspot extension
```

## 21.2 Positive controls

Mỗi over-build stratum cần vài task mà native/reuse solution rõ ràng để chứng minh policy có khả năng tạo effect.

## 21.3 Harm probes

Mỗi robustness/security stratum cần `antiref` hoặc known-underdefended implementation để oracle chứng minh nó có khả năng phát hiện harm. Nếu baseline pass 100% vì probe quá dễ, không được dùng “không thấy regression” làm bằng chứng mạnh.

## 21.4 Representative tasks

Promotion evidence phải đến từ real project tasks hoặc realistically replayable tasks, không chỉ microbenchmarks.

---

# 22. Statistical Design

## 22.1 Primary principle: Intention-to-Treat

Nếu treatment policy không activate, route blocked, candidate incomplete hoặc execution fail, không silently drop. Đây là outcome của deployed policy.

## 22.2 Primary endpoints

### Hard no-harm

- accepted correctness;
- security/trust-boundary behavior;
- robustness for declared task classes;
- authority/proof integrity.

### Economics

- TTAR;
- cost per accepted result;
- first-pass acceptance;
- repair rate;
- local burden.

## 22.3 Secondary endpoints

- output tokens;
- LOC/statements;
- change surface;
- dependencies;
- context bytes;
- tool hops;
- proof time;
- remote/local compute minutes.

## 22.4 Non-inferiority before superiority

Policy B chỉ được xét economics superiority sau khi quality non-inferiority pass.

Initial governance margins **không nên hardcode production ngay**; cần pilot để estimate variance. Nhưng structure phải là:

```text
correctness delta >= -margin_correctness
security regressions = 0 for hard canaries
robustness delta >= -margin_robustness per relevant stratum
authority/proof regressions = 0
```

## 22.5 Hierarchical analysis

Do task difficulty và repeated runs cluster mạnh:

- within-task paired ratios/differences;
- task random effects;
- replicate within task/policy;
- cluster bootstrap by task;
- report CI, not just mean;
- stratify by task class;
- do not pool high-risk and low-risk into one reassuring average.

## 22.6 Randomization / cache

- randomize A/B order within pair when feasible;
- label cold/warm cache;
- never blend without reporting strata;
- exact source/policy/env/oracle identity required for pair eligibility.

## 22.7 Multiple comparisons

Pre-register:

- primary no-harm family;
- primary TTAR/CAR endpoints;
- exploratory subgroup metrics.

Exploratory findings không được trở thành promotion trigger nếu không có confirmatory rerun.

---

# 23. Success / Failure Rules

## 23.1 KEEP

Một intervention được `KEEP` khi:

```text
quality floor passes
AND representative TTAR/CAR/local burden improves materially
AND maintenance/robustness signals do not deteriorate beyond margin
AND implementation complexity is justified by observed benefit
```

## 23.2 REVISE

`REVISE` khi:

- benefit chỉ ở một task class;
- robustness loss tập trung ở identifiable class;
- lower model tier chịu negative interaction;
- cold-cache economics xấu nhưng warm-cache tốt;
- policy too aggressive.

Ví dụ revise bằng cách giảm lean pressure cho `input_uncertainty=high`.

## 23.3 REMOVE

`REMOVE` khi:

- effect nhỏ hơn maintenance cost;
- first-pass acceptance giảm;
- repair tăng enough để TTAR xấu;
- policy overhead/context cost ăn hết savings;
- solution layer trùng logic với existing router nhưng không tạo incremental value;
- operator/agent complexity tăng mà không cải thiện accepted work.

---

# 24. Algorithms v1

## 24.1 Deterministic solution classifier

```python
def classify_solution(context):
    if outcome_already_satisfied(context):
        return NO_CHANGE_REQUIRED

    if safe_deletion_or_config_satisfies(context):
        return CONFIGURE_EXISTING

    reuse = find_verified_existing_behavior(context)
    if reuse.high_confidence:
        return REUSE_EXISTING

    if stdlib_candidate(context).valid:
        return STDLIB

    if native_candidate(context).valid:
        return NATIVE_PLATFORM

    if installed_dependency_candidate(context).valid:
        return EXISTING_DEPENDENCY

    if needs_real_boundary_or_repeated_extension(context):
        return STRUCTURED_EXTENSION

    return SMALL_CUSTOM
```

Đây là conceptual logic; implementation thực tế không nên gọi mọi probe nếu earlier evidence đã đủ.

## 24.2 Strategy score

Sau hard constraints:

\[
Score(s) = E[Implementation] + E[Proof] + E[Repair] + E[Placement] + \lambda_m EMC + \lambda_r Risk
\]

Không đưa `LOC` trực tiếp như dominant term. LOC/change surface chỉ giúp estimate các thành phần.

## 24.3 Lean-review trigger

Không chạy semantic lean review mọi diff.

```text
IF overbuild_risk >= threshold
OR new_dependency_on_low_width_task
OR speculative_state/config/interface signal
THEN ask acceptance owner for lean review
ELSE skip
```

Review chỉ hỏi:

```text
có work nào có thể delete/reuse/native/stdlib không?
complexity nào thiếu evidence?
```

Không duplicate correctness review.

---

# 25. Learning v2 — chỉ khi đủ dữ liệu

Sau representative samples, có thể dùng nearest-similar-task hoặc contextual bandit.

## 25.1 Context

```text
task_class
integration_width
oracle_strength
risk
input_uncertainty
change_frequency
reuse confidence
model route
node/cache state
local interactive state
```

## 25.2 Action

Không để action space quá lớn. Ví dụ:

```text
solution_policy_bucket
semantic_route_bucket
placement_bucket
proof_tier
```

## 25.3 Reward

\[
R = AcceptedReward
  - w_t \log(1+TTAR)
  - w_c CAR
  - w_r Repair
  - w_l LocalBurden
  - w_m MaintenancePenalty
\]

Hard safety violation có penalty effectively terminal, không cân bằng bằng savings.

## 25.4 Exploration boundary

Chỉ exploration trên low-risk representative tasks. Không exploration trên:

- destructive migration;
- auth/privacy;
- financial meaning;
- production secrets;
- unstable public contract;
- recovery-critical state.

---

# 26. Roadmap triển khai chi tiết

## Phase S0 — Measurement & Policy Identity

### Mục tiêu

Đảm bảo có thể biết policy nào tạo outcome nào trước khi thay behavior.

### Deliverables

- `solution_policy`, version, fingerprint trong evaluation/ledger;
- change-surface projection;
- first-pass/repair classification;
- TTAR/CAR/local burden fields;
- policy/topology/cache/oracle pair eligibility;
- contamination detection.

### Acceptance

- cùng run có full policy provenance;
- unknown cost không thành zero;
- pair mismatch bị reject;
- documentation-only/current behavior không thay đổi.

### Stop condition

Nếu host/model policy identity không xác định đủ, không chạy paired promotion study.

---

## Phase S1 — Solution-Economics Shadow Assessment

### Mục tiêu

Tính `what would we choose?` nhưng không đổi code path.

### Deliverables

- solution strategy taxonomy;
- reason codes;
- reuse/native/stdlib candidate evidence;
- overbuild-risk signals;
- predicted change/proof/placement surface;
- `shadow_only=true`.

### Acceptance

- không mutation behavior mới;
- latency overhead nhỏ so với task;
- decision explainable;
- false-positive review trên sample manual thấp enough để tiếp tục.

### Stop

Nếu assessment cost lớn hơn expected saved work trên routine tasks, simplify/remove probes.

---

## Phase S2 — Deterministic Reuse & Causal-Scope Helpers

### Mục tiêu

Tạo evidence tốt hơn, không tăng model count.

### Deliverables

- bounded LSP/reference expansion cho root-cause candidate;
- existing helper/dependency inventory theo scope;
- behavior/source evidence packet;
- no new public tool;
- server-friendly read-only probes.

### Acceptance

- giảm localization/context/tool hops trên controlled tasks;
- không làm full-repo scan mặc định;
- exact source binding.

---

## Phase S3 — Paired Experiment Harness

### Mục tiêu

Đo causal effect của `lean_solution_v1`.

### Deliverables

- task corpus + strata;
- frozen prompts/oracles;
- A/B policy arms;
- random order/cache strata;
- ITT analysis;
- non-inferiority quality gates;
- report generator;
- raw/derived evidence separation.

### Initial sample strategy

- pilot để estimate variance;
- sau pilot mới freeze power/sample target;
- tránh hardcode “30 pairs là đủ” nếu variance lớn;
- mỗi high-risk stratum có gate riêng.

### Acceptance

- reproducible report từ ledger/artifacts;
- no manual headline numbers;
- contamination checks green;
- quality gates executable.

---

## Phase S4 — Conservative Canary

### Scope ban đầu

Chỉ task classes có evidence tốt, ví dụ:

```text
native UI capability
obvious existing helper reuse
routine CRUD
localized strong-oracle bug
```

Exclude:

```text
security
parser/input robustness
recovery
concurrency
migration
weak-oracle architecture
```

### Behavior

- lean strategy recommendation có thể ảnh hưởng implementation;
- ChatWeb vẫn semantic owner;
- MCP vẫn writer/oracle;
- auto model/compute authorization không đổi;
- rollback bằng policy flag/version.

### Acceptance

- quality non-inferior;
- TTAR/CAR improvement representative;
- repair không tăng;
- no policy leakage into excluded classes.

---

## Phase S5 — Joint Solution + Compute Economics

### Mục tiêu

Nối output của solution layer vào server-first placement.

### Deliverables

- strategy informs workload DAG;
- expected proof/local-affinity included;
- avoided engineering work metrics;
- compare `before minimization` vs `after minimization` workload cost;
- remote/local break-even includes strategy choice.

### Acceptance

- lower total compute, không chỉ offload ratio;
- local burden giảm hoặc không xấu;
- TTAR không regression;
- exact identity/proof remains intact.

---

## Phase S6 — Adaptive Policy Learning

### Prerequisites

- đủ representative accepted/rejected/repaired data;
- stable taxonomy;
- policy fingerprints;
- model and compute cost observability;
- quality strata.

### Deliverables

- nearest-similar-task policy v1 hoặc constrained bandit;
- uncertainty;
- shadow learning;
- class-specific lean pressure;
- route/policy regret.

### Acceptance

- beats deterministic baseline on held-out/forward period;
- no high-risk exploration;
- explainable reason codes retained;
- rollback immediate.

---

# 27. Risk Register

| Risk | Cơ chế | Hậu quả | Mitigation |
|---|---|---|---|
| Under-implementation | Lean pressure cắt edge handling | Repair/production bug | Input-uncertainty class + robustness gates |
| Wrong reuse | Similar helper khác semantics | Silent wrong behavior | Behavior/source verification + oracle |
| Wrong-layer small patch | Symptom patch | Sibling regressions | Causal Fix Gate |
| Policy/model interaction | Weaker model obey minimality quá literal | Pass rate giảm | Per-route calibration |
| Prompt/context overhead | Policy dài | Cost/latency tăng | Structured capsule, small policy |
| Native shortcut localizes proof | Native solution cần local OS/device | Local burden tăng | Strategy includes placement cost |
| Dependency shortcut | Reuse package làm build/security cost tăng | CAR/maintenance tăng | Total dependency economics |
| Over-minimized architecture | Xóa boundary thật | Security/testability xấu | Evidence-Gated Complexity |
| LOC gaming | Model format/compress code | Fake savings | AST/change-surface + accepted metrics |
| Benchmark contamination | Treatment leaks into baseline | False causal claim | Policy/hook fingerprint + isolation |
| Survivorship bias | Drop failed treatment runs | Fake savings | Intention-to-treat |
| Judge bias | LLM likes concise output | False quality | Executable oracle first |
| Cache/order bias | Treatment always runs warm | Fake TTAR benefit | Randomized order + strata |
| Maintenance blind spot | Short now, costly later | Long-term cost | Follow-up task + hotspot signals |
| New policy complexity | Harness itself bloats | Net negative | KEEP/REVISE/REMOVE gate |

---

# 28. Những thứ không nên xây

Không nên:

- cài Ponytail nguyên plugin vào Coding Web core;
- thêm public `ponytail`/`lean` tool;
- thêm global always-on lazy persona;
- inject full policy prose vào mọi worker;
- dùng LOC làm optimization target;
- dùng “one implementation interface” làm auto-delete rule;
- dùng “fewest files possible” làm invariant;
- dùng native/stdlib/dependency priority mà không tính portability/proof;
- chạy lean semantic reviewer trên mọi diff;
- tạo second debt database;
- tạo behavior-map subsystem trước khi localization data chứng minh ROI;
- dùng model judge làm primary correctness/security oracle;
- bật learned policy trước paired representative evidence;
- fan-out candidates để “tìm minimal solution”;
- đổi one-runtime/write-authority architecture.

---

# 29. Operator / UI chỉ nên hiển thị signal có giá trị

Execution Control Center có thể hiển thị sau khi backend evidence đủ:

```text
Solution strategy:  REUSE_EXISTING
Lean pressure:      MEDIUM
Reason:             existing helper + strong oracle
Avoided work:       1 dependency, 2 files, est. 48s proof
Compute:            server-a for focused test
Local required:     no
Quality gate:       PASS
Policy:             lean_solution_v1 / fp:...
```

Không cần dashboard “minimality score” trang trí. UI chỉ materialize causal decisions đã có trong ledger.

---

# 30. Decision Matrix thực dụng

| Tình huống | Strategy prior | Lean pressure | Compute prior | Proof prior |
|---|---|---:|---|---|
| Date/color/file input đơn giản | Native | High | Server analysis, local UI only if needed | Focused UI/DOM |
| Existing helper match exact | Reuse | High | Server search/test | Focused + caller |
| Tiny CRUD | Direct/reuse | High | Local if tiny, remote if warm and heavier | Focused API test |
| Localized bug shared caller | Root-cause direct | Med-high | Server LSP/test | Failing reproduction + sibling caller |
| Parser bad input | Direct robust | Low | Server portable | Happy + malformed/edge |
| Auth boundary | Explicit secure | Low | server/local by secret affinity | Security canary + subsystem |
| Recovery state | Structured extension | Low | platform-specific | Fault/restart matrix |
| Distributed scheduler | Architecture-aware | Low | multi-node proof | deterministic + failure cases |
| Hotspot modified weekly | Structured extension candidate | Medium | depends | follow-up/change-quality |
| One-off cold script | Small custom/stdlib | High | local if remote overhead | one focused check |

---

# 31. Initial hypotheses để đưa vào experiment registry

## H-LEAN-001 — Over-build opportunity

```text
If lean_solution_v1 is enabled on reducible feature tasks,
median change surface and TTAR decrease >= meaningful threshold,
without first-pass acceptance or robustness falling beyond non-inferiority margins.
```

## H-LEAN-002 — Robustness interaction

```text
If input_uncertainty is high,
high lean pressure increases robustness failures.
Therefore low lean pressure should dominate high pressure on this stratum.
```

## H-LEAN-003 — Model interaction

```text
Policy effect differs by model route;
a lower-tier model may suffer more under-implementation under the same lean policy.
```

## H-LEAN-004 — Upstream workload elimination

```text
For reducible tasks, solution minimization reduces total deterministic compute/proof work
more than compute placement optimization alone.
```

## H-LEAN-005 — Causal bugfix

```text
Bounded reference expansion before bugfix reduces wrong-layer repairs
without adding enough localization latency to worsen median TTAR.
```

## H-LEAN-006 — Follow-up cost

```text
A solution with slightly larger initial change surface can have lower two-step total cost
on high-change-frequency hotspots than the minimal first patch.
```

---

# 32. Báo cáo experiment bắt buộc phải có

Mỗi policy report cần:

```text
1. exact source/head/worktree identity
2. runtime/tool/policy fingerprints
3. task corpus + strata
4. sample sizes / failed runs
5. cache/order/environment
6. accepted / rejected / incomplete
7. first-pass vs repaired
8. TTAR distribution
9. cost provenance
10. quality/robustness/security gates
11. change surface
12. local/remote burden
13. follow-up maintenance proxy if measured
14. CI / uncertainty
15. decision: KEEP / REVISE / REMOVE
```

Không được chỉ có screenshot dashboard hoặc mean savings.

---

# 33. Quan hệ với các tài liệu/dự án đã bàn luận

## repository-harness

Học:

- repository truth;
- authority classification;
- baseline → intervention → rerun → KEEP/REVISE/REMOVE;
- không tạo orchestrator/DB thứ hai.

Ứng dụng: policy experiment và behavior evidence.

## Ponytail

Học:

- eliminate/reuse/std/native before custom;
- root cause over symptom;
- explicit safety floor;
- benchmark honestly và sửa method khi bị critique.

Không copy: persona/intensity/LOC objective.

## Harness Handbook

Học:

- behavior localization/progressive disclosure;
- live source verification.

Ứng dụng có điều kiện nếu localization remains bottleneck.

## Scaffold Effect

Học:

- harness-policy-model pair là comparison unit;
- failure modes có thể thuộc scaffold;
- report full harness specs.

## CodeFlowBench

Học:

- reuse existing code là real capability challenge;
- dependency complexity làm multi-turn work khó hơn.

## EGSS / adaptive TTS

Học:

- mua thêm compute/candidates chỉ khi uncertainty justify;
- stop scaling khi marginal value âm.

## Timely Machine

Học:

- wall-clock + tool latency là first-class;
- token count không đại diện agentic time.

## Server-first research hiện tại

Học/giữ:

- exact snapshot/proof identity;
- one authority, multiple compute nodes;
- shadow → paired → canary → promote;
- server-first là prior, không absolute rule.

---

# 34. Nguồn nghiên cứu

## Coding Web nội bộ

1. `docs/research/260816_CHATWEB_SERVER_FIRST_COMPUTE_ORCHESTRATION_RESEARCH.md`
2. `docs/CURRENT_STATE.md`
3. `AGENTS.md`
4. `.coding-tools/orchestration/ledger.sqlite3`
5. `.coding-tools/performance.json`
6. các route/evaluation scripts hiện có trong `resources/coding-tools-mcp/scripts/`

## Ponytail và independent evaluation

7. DietrichGebert/ponytail — README.  
   https://github.com/DietrichGebert/ponytail

8. Ponytail skill definition.  
   https://github.com/DietrichGebert/ponytail/blob/main/skills/ponytail/SKILL.md

9. Ponytail official agentic benchmark, 2026-06-18.  
   https://github.com/DietrichGebert/ponytail/blob/main/benchmarks/results/2026-06-18-agentic.md

10. Ponytail issue #126 — baseline/benchmark critique and rebuild discussion.  
    https://github.com/DietrichGebert/ponytail/issues/126

11. Ponytail issue #236 — independent benchmark discussion.  
    https://github.com/DietrichGebert/ponytail/issues/236

12. Deepusleepy/ponytail-benchmark v3 — 480-run execution-graded benchmark.  
    https://github.com/Deepusleepy/ponytail-benchmark

13. PonyBench v3 design/preregistration.  
    https://github.com/Deepusleepy/ponytail-benchmark/blob/main/DESIGN.md

## Harness / coding-agent research

14. Vats, N.; Golev, O. “The Scaffold Effect in Coding Agents: Harness Choice as a Hidden Variable in Coding-Agent Evaluation”, 2026.  
    https://arxiv.org/abs/2607.22585

15. Wang, R. et al. “Harness Handbook: Making Evolving Agent Harnesses Readable, Navigable, and Editable”, 2026.  
    https://arxiv.org/abs/2607.13285

16. Harness Handbook project page.  
    https://ruhan-wang.github.io/Harness-Handbook/

17. Wang, S. et al. “CodeFlowBench: A Multi-turn, Iterative Benchmark for Complex Code Generation”, ACL 2026.  
    https://aclanthology.org/2026.acl-long.201/

18. Mao, C. et al. “EGSS: Entropy-guided Stepwise Scaling for Reliable Software Engineering”, ACL 2026.  
    https://aclanthology.org/2026.acl-long.1359/

19. Ma, Y. et al. “Timely Machine: Awareness of Time Makes Test-Time Scaling Agentic”, ACL 2026.  
    https://aclanthology.org/2026.acl-long.211/

20. Horikawa, K. et al. “Do AI Agents Really Improve Code Readability?”, 2026.  
    https://arxiv.org/abs/2603.13723

21. Liu, Y. et al. “Debt Behind the AI Boom: A Large-Scale Empirical Study of AI-Generated Code in the Wild”, 2026.  
    https://arxiv.org/abs/2603.28592

---

# 35. Research-quality caveats

1. Ponytail official benchmark là creator-run; independent benchmark là bằng chứng bổ sung nhưng vẫn chỉ đại diện một model/setup cụ thể.
2. Independent PonyBench dùng task/harness riêng; không suy trực tiếp effect size sang Coding Web.
3. Scaffold Effect và Harness Handbook là 2026 research; một số nguồn là arXiv preprint, không phải tất cả đã peer-reviewed.
4. ACL 2026 papers phản ánh benchmark setup của tác giả, không tự tạo threshold production.
5. AI-code technical-debt/readability studies dùng dataset/metrics khác Coding Web; dùng làm risk prior, không làm causal proof local.
6. Current Coding Web worktree có thay đổi đang tiếp diễn. Tài liệu này không claim source-in-progress là accepted/released.
7. Tài liệu đề xuất architecture/methodology; mọi production promotion phải dựa local representative evidence.

---

# 36. Phán quyết cuối

Hướng phát triển phù hợp nhất không phải:

```text
Ponytail inside Coding Web
```

mà là:

```text
Ponytail's strongest idea
        +
Coding Web authority/proof/economics
        +
server-first compute placement
        +
behavior-aware repository evidence
        +
causal paired evaluation
```

thành một layer mới:

> **Solution Economics — chọn lượng engineering work nhỏ nhất nhưng đủ tạo accepted outcome bền vững, trước khi mua model reasoning, server compute, local compute và proof.**

North Star hoàn chỉnh vì vậy là:

> **Coding Web tự động hiểu behavior và invariant cần đạt; loại bỏ work không cần thiết; reuse capability hiện hữu khi đúng; chọn giải pháp có expected engineering economics thấp nhất; sau đó phối hợp ChatWeb, model lanes, server compute, local edge và proof plane để tạo accepted code nhanh nhất, rẻ nhất, với ít rework và maintenance burden nhất.**

Nếu một “optimization” chỉ làm code ngắn hơn, server bận hơn, token ít hơn hoặc dashboard đẹp hơn nhưng không cải thiện accepted-result economics sau quality floor, hệ thống phải có khả năng **REVISE hoặc REMOVE nó**.
