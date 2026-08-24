# CODING WEB — PROBLEM RESOLUTION LINEAGE & INTERACTIVE ENGINEERING SCIENCE

> **Research / Decision Doctrine ID:** `CW-PRL-20260823-v1`
> **Ngày:** 2026-08-23, Asia/Saigon
> **Workspace:** `E:\DEV\Codex-web`
> **Loại tài liệu:** nghiên cứu khoa học ứng dụng + phương pháp luận + phân tích kiến trúc + chiến lược đo lường + roadmap triển khai
> **Phạm vi:** ChatWeb / Coding Web / EOCL / host-turn correlation / quality outcome / user feedback / multi-turn coding-agent evaluation / requirements traceability / causal rework / accepted-result economics
> **Trạng thái:** RESEARCH SYNTHESIS + PROPOSED STRATEGIC DOCTRINE; **không tự động thay đổi production behavior, routing, P4/P5 treatment hoặc public tool surface**
> **Evidence boundary nội bộ khi audit:** disk/upstream HEAD được quan sát ở `8ffa8bf279ad7296ff1402fbc2ce2b59069c36c5`; code-bearing HEAD riêng là `ea6abcb3ab0f3a4cc9dbf94d34c685a4806760ba`. Source worktree hiện dirty (bao gồm các source/documentation delta của chương trình này); vì vậy các kết luận source-level dưới đây là **code-present / architecture-present**, không phải clean-commit, loaded-runtime, package hay release claim.
> **Post-snapshot operational correction:** P5 A0 có post-open source-scope drift đã được `hard_stop` qua official P5 authority với funnel `0/0/0/0/0`; Gate 0 lifecycle reconciliation sau đó đạt receipt PASS. Đây là current operational correction được theo dõi trong `260823_CODING_WEB_GATE0_PRL_IMPLEMENTATION_AND_VALIDATION_TRACKER.md`, không làm thay đổi số snapshot lịch sử trong doctrine. Loaded-runtime identity vẫn `UNKNOWN`.
> **North Star đề xuất:** từ **Accepted Result Economics** nâng lên **Accepted Problem Resolution Economics**, nhưng triển khai theo lớp bổ sung, không rewrite toàn bộ hệ thống hiện tại.

---

# 0. KẾT LUẬN ĐIỀU HÀNH

Coding Web hiện đã giải quyết khá sâu một bài toán quan trọng:

> **Làm thế nào để một execution kỹ thuật từ objective đi qua preflight, mutation, proof, replan, acceptance và tạo ra một accepted result có provenance đáng tin?**

EOCL, run/wave lineage, objective revision, proof identity, accepted checkpoint, `quality_outcome`, host `turn_id` / `trace_id`, `conversation_epoch`, durable handoff và solution-shadow đã tạo thành một execution/evidence plane tương đối trưởng thành.

Nhưng một bài toán cao hơn vẫn chưa được mô hình hóa đầy đủ:

> **Một vấn đề mà người dùng thực sự muốn giải quyết sống qua nhiều lượt chat, nhiều lần assistant trả lời, nhiều lần người dùng sửa/đính chính/bổ sung yêu cầu, nhiều RUN/WAVE kỹ thuật và thậm chí nhiều conversation epoch như thế nào; và khi nào có thể nói vấn đề đó thực sự đã được giải quyết?**

Đây là ranh giới giữa:

```text
ACCEPTED ENGINEERING RUN
```

và:

```text
ACCEPTED PROBLEM RESOLUTION
```

Hai khái niệm liên quan nhưng không tương đương.

Một RUN có thể `CHECKPOINTED / ACCEPTED`, test xanh và source đúng, nhưng người dùng vẫn phản hồi:

```text
“Vẫn lỗi.”
“Không phải trường hợp tôi nói.”
“Phần này sửa rồi nhưng app thật vẫn không lưu được.”
“Bạn sửa sai workspace.”
“Ý tôi là phải đồng bộ ngược nữa.”
```

Trong các trường hợp đó, **engineering evidence của một attempt có thể hợp lệ nhưng problem-level outcome vẫn chưa resolved**.

Các nguồn evaluation interactive gần đây là **source-reported methodological evidence**, không phải consensus, local prevalence, local ROI hay expected uplift cho Coding Web. SWE-Together mô tả benchmark từ các phiên developer-agent và đo ngoài final repository correctness còn có corrective-feedback burden. SWE-Interact báo cáo rằng score single-turn không tự động chuyển thành score multi-turn trong benchmark của họ. RECODE-H và các framework interactive evaluation báo cáo kết quả theo feedback richness, đồng thời nêu các giới hạn về adaptation, memory, code quality và iterative repair. Các công trình này hỗ trợ việc đo interaction/correction như một trục riêng; chỉ prospective PRL evidence mới có thể kết luận prevalence hoặc effect cục bộ.

Cộng đồng sử dụng coding agent cũng báo cáo đúng failure mode mà Coding Web phải bảo vệ: session dài vẫn nhớ “mục tiêu lớn” nhưng mất execution frontier; instruction cũ sống lại sau correction; compaction khiến model đọc lại cùng file và lặp lại kế hoạch; hoặc model báo hoàn thành khi người dùng vẫn phải tiếp tục sửa. Các báo cáo này là anecdotal, không phải controlled evidence, nhưng chúng cung cấp failure hypotheses rất phù hợp với nhu cầu đo lường nội bộ.

**Quyết định đề xuất của tài liệu này:**

1. **Giữ EOCL làm execution authority.** Không tạo một orchestration framework cạnh tranh.
2. Bổ sung một lớp mỏng **Problem Resolution Lineage (PRL)** nằm phía trên và xuyên qua RUN/WAVE.
3. PRL liên kết content-free:
   - problem identity;
   - user/assistant turn identity;
   - problem/intent revision;
   - engineering run/wave/proof;
   - user feedback/correction;
   - resolution/reopen outcome.
4. Không coi mọi user correction là AI failure. Phải tách:
   - requirement evolution / new information / preference change;
   - assistant misunderstanding / technical error / proof gap / system failure.
5. Không dùng silence làm `CONFIRMED_RESOLVED`.
6. Không dùng một LLM judge duy nhất làm authority. User feedback + deterministic proof + exact source/run identity có precedence cao hơn synthetic score.
7. Đổi metric từ “bao nhiêu RUN accepted?” sang một hierarchy hoàn chỉnh hơn:

```text
problem resolved?
  -> engineering result correct?
  -> user correction burden?
  -> avoidable correction burden?
  -> problem-resolution time / tail?
  -> engineering rework / proof/runtime loss?
  -> measured cost?
```

8. Accepted-Result Economics vẫn giữ nguyên giá trị ở tầng execution; nó trở thành **thành phần** của Accepted Problem Resolution Economics, không bị xóa.
9. Triển khai theo shadow-first, prospective-only, không backfill causal label lịch sử bằng suy đoán.
10. Chỉ khi PRL measurement đã chứng minh chính xác và tạo insight mới thì mới cho phép nó ảnh hưởng P4/P5 policy learning.

Luận điểm trung tâm của tài liệu:

> **Coding agent không nên được đánh giá chỉ bởi việc nó có tạo ra một patch đúng hay một RUN accepted hay không. Nó phải được đánh giá bởi khả năng đưa một vấn đề của người dùng từ trạng thái chưa hiểu / chưa giải quyết, qua các vòng clarification-correction-engineering-proof, tới một resolution có bằng chứng và có chi phí sửa hướng thấp.**

---

# 1. BÀI TOÁN THỰC SỰ: ĐƠN VỊ ĐÁNH GIÁ ĐANG QUÁ THẤP

## 1.1. Đơn vị hiện tại của execution system

Coding Web hiện có các đơn vị rất mạnh ở tầng kỹ thuật:

```text
TASK
RUN
WAVE
DELEGATION
PROOF
CHECKPOINT
QUALITY OUTCOME
OBSERVATION SPAN
```

Chúng trả lời tốt các câu hỏi:

- execution đang ở state nào;
- source base/fingerprint nào được dùng;
- objective của wave hiện tại là gì;
- có REPLAN không;
- proof nào đã chạy;
- accepted hay rejected;
- critical defect/manual fix/rollback có được ghi nhận không;
- một host turn nào bind chính xác với run/wave nào.

Đây là foundation rất tốt.

## 1.2. Nhưng người dùng không nghĩ theo RUN

Người dùng thường nghĩ theo một **vấn đề**:

```text
“Không lưu được dự án.”
“Dashboard không cập nhật.”
“Codex đang dùng sai workspace.”
“Đồng bộ tài chính/dự án chưa đúng.”
“Runtime cứ lặp lại sau compaction.”
```

Một vấn đề như vậy có thể tạo chuỗi:

```text
Turn U1: nêu vấn đề
  ↓
Response A1: chẩn đoán ban đầu
  ↓
RUN R1: sửa attempt 1
  ↓
Proof P1: pass
  ↓
Response A2: báo đã sửa
  ↓
Turn U2: “vẫn lỗi ở trường hợp X”
  ↓
RUN R2: sửa attempt 2
  ↓
Response A3
  ↓
Turn U3: “đúng rồi, nhưng còn đồng bộ ngược”
  ↓
phân loại: cùng problem revision hay requirement mới?
  ↓
RUN R3
  ↓
final response
  ↓
user confirms / no confirm / later reopen
```

Nếu phân tích từng RUN độc lập, ta có thể thấy:

```text
R1 accepted
R2 accepted
R3 accepted
```

và kết luận 3 accepted results.

Nhưng problem-level truth có thể là:

```text
ONE PROBLEM
  attempt 1 = technically green nhưng không resolve user problem
  attempt 2 = resolve partial
  attempt 3 = final resolution
```

Đây là khác biệt về **unit of analysis**, không chỉ là thêm một metric.

## 1.3. Rủi ro khi chọn sai đơn vị phân tích

Nếu unit quá thấp, hệ thống có thể tối ưu sai:

- tăng accepted-run count nhưng người dùng phải sửa hướng nhiều hơn;
- giảm replan nội bộ nhưng assistant chẩn đoán sai từ đầu;
- proof xanh nhưng oracle không đại diện cho lỗi người dùng thấy;
- completion report chính xác cho RUN nhưng tổng vấn đề vẫn reopen;
- session compaction giữ objective chung nhưng làm mất các correction quan trọng;
- mỗi user correction tạo RUN mới và bị coi như task độc lập, làm mất causal chain.

Nói cách khác:

> **Local correctness không đảm bảo global resolution.**

---

# 2. NỀN TẢNG LÝ THUYẾT I — CONVERSATIONAL REPAIR

## 2.1. Repair là cấu trúc bình thường của hội thoại

Công trình kinh điển của Schegloff, Jefferson và Sacks về repair trong hội thoại mô tả một “organization of repair” dùng để xử lý các vấn đề trong speaking, hearing và understanding. Điểm quan trọng không phải tên gọi lịch sử của lý thuyết, mà là nguyên lý:

> **Một hội thoại có cơ chế riêng để phát hiện và sửa breakdown của mutual understanding.**

Trong human-human interaction, repair không phải ngoại lệ hiếm; nó là phần bình thường để hội thoại hội tụ.

Đối với coding agent, điều này gợi ý:

```text
user correction
!= nuisance
!= prompt noise

user correction
= observable evidence về breakdown hoặc requirement evolution
```

Nếu không ghi nhận repair lineage, ta đang loại bỏ đúng loại evidence cho biết assistant hiểu sai ở đâu.

## 2.2. User repair strategy có thể phân loại

Alloatti và cộng sự xây taxonomy/tagging methodology để phát hiện repair strategies của người dùng trong task-oriented conversational agents. Kết luận có ý nghĩa trực tiếp với Coding Web:

- repair attempt của user có thể được nhận diện;
- các repair attempt không đồng nhất về ý nghĩa;
- việc phân loại giúp tìm “problematic spots” của agent;
- presence của repair strategy là tín hiệu breakdown, nhưng loại breakdown phải được contextualize.

Coding Web cần dùng nguyên lý này nhưng với domain-specific taxonomy cho software engineering.

## 2.3. Không phải correction nào cũng là error của assistant

Đây là điểm quan trọng nhất khi chuyển repair theory sang engineering.

Ví dụ:

```text
U1: “Thêm chức năng tạo dự án.”
A1: triển khai.
U2: “Thêm luôn chủ đầu tư.”
```

`U2` có thể là **new requirement**, không phải assistant failure.

Trong khi:

```text
U1: “Làm ở workspace E:\Github\HR.”
A1: sửa E:\DEV\...
U2: “Sao lại sửa sai workspace?”
```

đây là **avoidable interpretation/target error**.

Vì vậy hệ thống không được tối ưu bằng một biến thô:

```text
number_of_user_followups
```

Mà phải phân biệt **productive interaction** và **avoidable correction**.

---

# 3. NỀN TẢNG LÝ THUYẾT II — MULTI-TURN CODING AGENT EVALUATION

## 3.1. SWE-Together: correctness + corrective feedback burden

SWE-Together (2026) là bằng chứng bên ngoài sát nhất với bài toán này.

Benchmark được dựng từ 11.260 recorded user-agent coding sessions, chọn 109 repository-level tasks có recoverable state, clear goal và observable outcome. Điểm thiết kế quan trọng:

- task được reveal qua nhiều turn;
- user simulator replay clarification, course correction và review;
- đánh giá không chỉ final repository correctness;
- còn đo user correction burden.

Repository của benchmark biểu diễn user correction bằng một metric riêng và thậm chí phân biệt “correction” với “nudge”. Điều này củng cố một luận điểm:

> **Hai agent có cùng final correctness nhưng agent cần ít user corrections hơn là hai trải nghiệm khác nhau về chất lượng.**

Coding Web nên học ý tưởng, nhưng không copy nguyên weight vào production. Local burden vector phải được validate với workload thật của dự án.

## 3.2. SWE-Interact: single-turn success không chuyển tự động sang multi-turn

SWE-Interact (2026) thiết kế user simulator bắt đầu từ instruction mơ hồ/chưa đủ, sau đó progressive reveal requirement, feedback, revision và constraint.

Kết quả nổi bật được nhóm tác giả báo cáo:

- best models khoảng 50% ở single-turn baseline;
- chỉ khoảng 25% trên multi-turn interactive counterpart.

Các failure mode bao gồm:

- quên requirement;
- technical mistakes;
- over-agentic coding;
- bỏ cuộc sớm;
- rework nhiều hơn khi yêu cầu được reveal dần.

Điều này rất quan trọng cho Coding Web vì current EOCL chủ yếu chứng minh execution correctness **sau khi objective đã được formalize đủ**. Nhưng nhiều lỗi thật nằm ở trước đó:

```text
objective discovery
intent revision
requirement retention
feedback integration
```

PRL chính là lớp nối phần này với EOCL.

## 3.3. RECODE-H: feedback richness làm thay đổi outcome

RECODE-H (ICLR 2026) đánh giá research-code implementation qua multi-turn feedback hierarchy. Kết quả cho thấy richer feedback tạo performance gains đáng kể.

Hàm ý:

> Feedback không chỉ là hậu kiểm; feedback là một control signal có causal effect lên solution trajectory.

Nếu Coding Web không phân biệt feedback loại nào dẫn tới repair nào, hệ thống bỏ mất dữ liệu để học:

- feedback nào đáng giá;
- correction nào tránh được;
- correction nào do thiếu oracle;
- correction nào do requirement mới.

## 3.4. Interactive Evaluation AAAI 2026

Rontogiannis và cộng sự mô hình hóa multi-requirement programming task như requirement dependency graph và dùng structured feedback-driven dialogue. Giá trị với Coding Web là nguyên tắc:

> Requirement không nhất thiết được biết toàn bộ ngay từ turn đầu; evaluation phải đo khả năng thích nghi và hoàn thiện constraints qua dialogue.

## 3.5. Closed-loop coding evaluation

Nghiên cứu closed-loop embedded software development năm 2026 đánh giá agent qua build-test-runtime-repair-stopping loops thay vì one-shot code generation.

Coding Web đã đi xa theo trục closed-loop execution. Bước tiếp theo là closed-loop **user problem resolution**.

---

# 4. NỀN TẢNG LÝ THUYẾT III — HUMAN-IN-THE-LOOP SOFTWARE ENGINEERING

## 4.1. HULA: human feedback là một phần của SDLC agentic

HULA được triển khai nội bộ tại Atlassian, tích hợp human refinement/guidance vào planning và coding. Nghiên cứu báo cáo perceived reduction về time/effort ở một số task straightforward nhưng vẫn còn concern về code quality.

Điểm cần lấy:

- human feedback không phải fallback thất bại;
- feedback có thể là normal control input;
- nhưng phải biết feedback đang làm gì để không đánh đồng human involvement với model failure.

## 4.2. User satisfaction không thể thu gọn thành một điểm chung chung

Nghiên cứu task-oriented dialogue cho thấy satisfaction chịu ảnh hưởng bởi task completion, relevance, understanding, efficiency và nhiều yếu tố user experience khác nhau.

Tương tự, Coding Web không nên dùng:

```text
“user satisfied = 1/0”
```

làm metric duy nhất.

Một user có thể hài lòng với final result nhưng vẫn phải mất 8 correction turns. Đó là final success nhưng interaction cost cao.

Ngược lại, user có thể bổ sung nhiều requirement mới vì hợp tác tốt; nhiều turn không đồng nghĩa failure.

---

# 5. NỀN TẢNG LÝ THUYẾT IV — REQUIREMENTS TRACEABILITY

## 5.1. Requirement thay đổi là trạng thái bình thường

Requirements Engineering từ lâu đã xem traceability là khả năng liên kết requirement với artifact và lịch sử thay đổi.

Systematic literature reviews nhấn mạnh các câu hỏi:

- requirement đến từ đâu;
- tại sao requirement đổi;
- artifact nào thực hiện requirement;
- commit/test/issue nào liên quan;
- context nào tạo ra thay đổi.

PRL cần làm điều tương tự nhưng ở tốc độ hội thoại:

```text
user turn
  -> intent revision
  -> engineering objective
  -> run/wave
  -> source/proof
  -> assistant response
  -> user feedback
```

## 5.2. Issue-based traceability là analogue rất gần

Issue report thường là artifact mô tả changed requirement và được trace tới commit/source/test.

Trong coding-agent interaction, một **problem thread** có vai trò tương tự một live issue:

- ban đầu chưa hoàn chỉnh;
- được refine bằng interaction;
- có implementation attempts;
- có test/proof;
- có reopen/closure.

Khác biệt là cadence nhanh hơn và feedback có thể xảy ra ngay sau từng assistant response.

## 5.3. Không nên biến traceability thành paperwork

Literature cũng chỉ ra cost chính của traceability là tạo và duy trì link.

Do đó PRL phải:

- tự động lấy exact identities đã có;
- không yêu cầu user điền form;
- không lưu raw transcript;
- không yêu cầu thêm một tool call cho mọi turn;
- không ép model tạo narrative log dài.

Mục tiêu là **low-cost structural traceability**.

---

# 6. BẰNG CHỨNG CỘNG ĐỒNG / DIỄN ĐÀN: FAILURE HYPOTHESES THỰC TẾ

> Các nguồn phần này là issue/forum/community reports, không phải controlled experiments. Chúng được dùng để hình thành failure taxonomy và test hypotheses, không dùng để ước lượng prevalence toàn cầu.

## 6.1. Compaction giữ broad goal nhưng mất execution frontier

OpenAI Codex issue #25900 mô tả long-running session sau compaction quay về semantic point cũ, đọc lại file, lặp analysis và rơi vào compaction/restart loop. Người báo đề xuất structured checkpoint gồm current task, phase, progress, confirmed facts, rejected paths, next action và stop condition.

Điều này gần như trùng với khái niệm state capsule mà Coding Web đã xây.

Nhưng PRL bổ sung một field quan trọng:

```text
ACTIVE PROBLEM + LATEST USER CORRECTION
```

Không chỉ active execution phase.

## 6.2. Obsolete state sống lại sau user correction

Issue #32863 mô tả Codex lặp lại obsolete response sau khi user đã correction và chuyển sang prompt mới. Impact được báo gồm duplicate/conflicting work, wrong context và repeated user correction burden.

Đây là bằng chứng vận hành cho nguyên tắc:

> `latest raw prompt in retained context` không phải lúc nào cũng là `active semantic problem state`.

PRL phải có explicit active-problem pointer và relation giữa turn mới với problem hiện tại.

## 6.3. Broad objective survive, convergence fail

Issue #34095 mô tả sau 24 compactions, model vẫn nhớ broad objective nhưng execution frontier degraded; nó liên tục tuyên bố “còn vài mục cuối” rồi mở lại việc đã xong.

Đây là một distinction quan trọng:

```text
memory of goal
!=
state of convergence
```

Một system có thể “nhớ” nhưng vẫn không hội tụ.

PRL phải đo **resolution progress**, không chỉ context retention.

## 6.4. Stale prompt được coi là active prompt

Issue #27731 mô tả stale latest user prompt được đưa lại như instruction đang active sau compaction.

Đây là lý do không nên suy active intent chỉ bằng “turn text gần nhất” trong compacted transcript.

## 6.5. Partial completion nhưng assistant tuyên bố xong

Một thảo luận r/codex tháng 3/2026 mô tả user đưa spec nhiều phần nhưng agent thường dừng sớm và tuyên bố finished khi mới hoàn thành một phần; user phải lặp lại để làm tiếp.

Dù anecdotal, failure shape rất quan trọng:

```text
assistant completion claim
!=
problem completion
```

Coding Web đã cải thiện operator-visible completion report ở run-level. PRL cần làm tương tự ở problem-level.

## 6.6. Self-review loop và moving target

Một thảo luận r/codex tháng 7/2026 ghi nhận nếu để model tự review liên tục, nó có thể liên tục đổi ý và đề xuất thêm thay đổi.

Hàm ý:

> Nhiều correction nội bộ không tự động đồng nghĩa quality tăng.

Stop condition phải dựa trên verified problem criteria, không phải model còn nghĩ ra điều gì để sửa.

## 6.7. Bài học phương pháp luận từ chính issue discussion

Trong issue #14347 về compaction prompt, một maintainer hỏi người đề xuất đã kiểm chứng improvement ra sao và có bao nhiêu test run, thay vì chấp nhận “cảm giác tốt hơn”.

Đây là nguyên tắc Coding Web phải giữ:

> Community report tạo hypothesis; local prospective evidence quyết định promotion.

---

# 7. CURRENT CODING WEB: NHỮNG GÌ ĐÃ CÓ

Audit source ngày 23/08 cho thấy nền tảng PRL **không bắt đầu từ số 0**.

## 7.1. EOCL run/wave + objective revision

Trong:

`resources/coding-tools-mcp/coding_tools_mcp/orchestration_ledger.py`

đã có:

- `create_run(...)`;
- `create_wave(...)`;
- `wave_objective_provenance(...)`;
- `objective_revision`;
- `objective_sha256`;
- `objective_source`;
- `objective_changed_from_previous`.

Điều này giải quyết tốt:

> Một engineering objective thay đổi qua REPLAN nhưng run history ban đầu không bị rewrite.

## 7.2. Exact turn / trace identities

Host observation path trong:

- `electron/services/chatEvaluationJournal.js`;
- `electron/main.js`;
- `resources/coding-tools-mcp/coding_tools_mcp/orchestration_ledger.py`;

đã mang:

```text
turn_id
trace_id
run_id
wave_id
span_id
clock_domain
```

và current-state document xác nhận correlation path là content-free, không copy prompt/response text.

Đây là prerequisite quan trọng nhất để nối user interaction với execution mà không tạo transcript database.

## 7.3. Conversation epoch và handoff

Trong `coordination.py` và `handoff_capsules` đã có `conversation_epoch`.

Handoff capsule lưu compact runtime state để rollover conversation mà không replay transcript.

Đây là nền tảng cho continuity nhưng **conversation epoch không phải problem identity**.

## 7.4. Quality outcome

`quality_outcomes.py` đã hỗ trợ:

```text
oracle_pass
regression_escape
rollback_required
manual_fix_required
critical_defect_count
noncritical_defect_count
maintainability_gate
observation_window_end
```

Đây là outcome plane tốt cho engineering quality.

## 7.5. Acceptance/rejection

`task_control action=accept/reject` đã phân biệt final acceptance của RUN và bắt REPLAN khi Sol reject.

## 7.6. Observation spans và critical path

Ledger hỗ trợ `record_observation_span(...)` và `critical_path_analysis(...)` với explicit dependencies/clock-domain policy.

Đây là nền tảng để sau này đo problem-level user-visible time mà không gọi nhầm inter-tool gap là model latency.

## 7.7. Solution shadow / P4

P4 đã ghi pre-mutation solution descriptors nhưng không thay production behavior.

Đây là precedent tốt cho cách PRL nên được triển khai:

> **shadow evidence first, policy later.**

---

# 8. CURRENT GAP: NHỮNG PRIMITIVE ĐÃ CÓ NHƯNG CHƯA TẠO THÀNH “SAME PROBLEM LINEAGE”

Các primitive hiện tại chưa trả lời canonical các câu:

```text
Turn U2 có phải cùng vấn đề với U1 không?
U2 là correction hay requirement mới?
Correction do assistant hiểu sai hay do user bổ sung data mới?
RUN R2 sửa R1 hay giải một subproblem khác?
Accepted RUN R1 có bị user reopen không?
Final response nào thực sự đóng problem?
User đã confirm hay chỉ không nói nữa?
Problem này cần bao nhiêu avoidable correction turns?
```

## 8.1. `turn_id` không phải `problem_id`

`turn_id` cho biết lượt chat nào.

Nó không nói semantic continuity.

## 8.2. `session_id` không phải `problem_id`

Trong code hiện tại, `session_id` có thể là provider/thread/process session identity.

Dùng nó làm problem identity sẽ trộn hai lớp hoàn toàn khác nhau.

## 8.3. `conversation_epoch` không phải `problem_id`

Một problem có thể đi qua nhiều conversation epoch.

Một conversation epoch cũng có thể chứa nhiều problem.

## 8.4. `RUN` không phải `problem_id`

Một problem có thể cần nhiều run.

Một run có thể là diagnostic/proof/recovery attempt chỉ phục vụ một phần của problem.

## 8.5. `quality_outcome` chưa phải user-resolution outcome

`oracle_pass=true` chứng minh oracle kỹ thuật.

Nó không chứng minh user problem đã hết.

---

# 9. KHÁI NIỆM ĐỀ XUẤT: PROBLEM RESOLUTION THREAD (PRT)

## 9.1. Định nghĩa

**Problem Resolution Thread (PRT)** là một lineage causal, content-free, kéo dài từ lúc một user problem được nhận diện cho tới khi problem đó:

- resolved confirmed;
- resolved unconfirmed;
- reopened;
- superseded;
- abandoned/blocked.

PRT không phải chat transcript.

PRT không phải execution authority.

PRT không thay EOCL.

PRT là **semantic/evaluation correlation layer**.

## 9.2. Một PRT có thể chứa

```text
problem_id
  ├── user turns
  ├── assistant responses
  ├── intent revisions
  ├── feedback events
  ├── engineering RUN/WAVE attempts
  ├── proof/quality outcomes
  ├── provisional resolution claims
  ├── reopen events
  └── final resolution outcome
```

## 9.3. Quan hệ với EOCL

```text
PRT = “WHY / FOR WHOM / IS THE PROBLEM RESOLVED?”
EOCL = “WHAT EXECUTION HAPPENED / WAS IT PROVEN / ACCEPTED?”
```

Architecture:

```text
USER / CHAT
    |
    v
Problem Resolution Thread
    |
    +---- user correction / requirement revision
    |
    v
EOCL RUN -> WAVE -> EXECUTE -> PROOF -> ACCEPT/REJECT
    |
    v
Engineering outcome
    |
    v
Assistant response
    |
    v
User feedback / confirm / reopen
    |
    +---- back into same PRT if semantically same problem
```

EOCL vẫn là writer/proof/acceptance authority.

---

# 10. BA VÒNG LẶP CẦN PHÂN BIỆT

## 10.1. Loop 1 — Problem / Conversation Loop

```text
problem statement
 -> assistant understanding
 -> response/plan
 -> user feedback
 -> revised understanding
 -> engineering/action
 -> revised response
 -> resolution / reopen
```

Question:

> **Có giải quyết đúng vấn đề người dùng không?**

## 10.2. Loop 2 — Engineering / EOCL Loop

```text
objective
 -> preflight
 -> execute
 -> prove
 -> replan
 -> accept/reject
```

Question:

> **Giải pháp kỹ thuật có đúng và có bằng chứng không?**

## 10.3. Loop 3 — Learning / Economics Loop

```text
problem outcome
 -> correction causes
 -> TTAR/cost
 -> intervention
 -> prospective comparison
 -> retain/revert/promote
```

Question:

> **Làm thế nào lần sau giải quyết cùng loại problem ít correction và ít cost hơn?**

Current Coding Web mạnh ở Loop 2, đang xây Loop 3, và mới có primitive rời rạc của Loop 1.

PRL làm nhiệm vụ khép Loop 1 với Loop 2.

---

# 11. ONTOLOGY TỐI THIỂU

Không cần ontology khổng lồ. Chỉ cần các khái niệm sau.

## 11.1. `problem_id`

Random durable identity của một problem thread.

Không derive từ raw prompt.

Không dùng hash nội dung user làm public identity.

## 11.2. `problem_revision`

Tăng khi **semantic requirement của cùng problem** thay đổi đáng kể.

Ví dụ:

```text
rev 1: project create fails
rev 2: create works, but update/save same payload also must be fixed
```

Nếu user mở một feature khác độc lập, tạo problem mới thay vì tăng revision.

## 11.3. `turn_link`

Quan hệ giữa `turn_id`/`trace_id` và `problem_id`:

```text
opens_problem
continues_problem
corrects_prior_attempt
adds_requirement
confirms_resolution
reopens_problem
supersedes_problem
new_problem
```

## 11.4. `attempt`

Một assistant/engineering attempt nhằm tiến problem tới resolution.

Một attempt có thể có:

```text
response_turn_id
run_id
wave_id
proof_ref
quality_outcome_ref
```

## 11.5. `feedback_event`

Một user feedback có relation tới attempt trước.

## 11.6. `resolution_event`

Một event chuyển trạng thái problem.

---

# 12. TAXONOMY USER FEEDBACK ĐỀ XUẤT

Không dùng một label duy nhất. Tách tối thiểu ba trục.

## 12.1. Trục A — Intent của feedback

```text
CONFIRM_RESOLVED
PARTIAL_RESOLUTION
SAME_PROBLEM_STILL_FAILING
CORRECT_UNDERSTANDING
CORRECT_TARGET_OR_SCOPE
CORRECT_TECHNICAL_RESULT
CORRECT_PROOF_OR_VERIFICATION
ADD_CONSTRAINT
ADD_REQUIREMENT
PROVIDE_NEW_EVIDENCE
PREFERENCE_CHANGE
ASK_EXPLANATION
NEW_PROBLEM
SUPERSEDE_OR_CANCEL
UNKNOWN
```

## 12.2. Trục B — Causal mechanism

```text
ASSISTANT_MISUNDERSTANDING
WRONG_ROOT_CAUSE
WRONG_TARGET_OR_WORKSPACE
INSUFFICIENT_SOLUTION_SCOPE
OVERBROAD_CHANGE
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

## 12.3. Trục C — Economic interpretation

```text
AVOIDABLE_CORRECTION
PRODUCTIVE_CLARIFICATION
LEGITIMATE_REQUIREMENT_GROWTH
NEUTRAL_FOLLOWUP
UNCERTAIN
```

Một event có thể có:

```text
intent = ADD_REQUIREMENT
cause  = REQUIREMENT_EVOLUTION
economics = LEGITIMATE_REQUIREMENT_GROWTH
```

không tính là assistant failure.

Một event khác:

```text
intent = CORRECT_TARGET_OR_SCOPE
cause = WRONG_TARGET_OR_WORKSPACE
economics = AVOIDABLE_CORRECTION
```

là loss rõ ràng.

---

# 13. TẠI SAO KHÔNG NÊN DÙNG MỘT LLM JUDGE ĐỂ GÁN “AI FAILURE”

## 13.1. Latent intent không hoàn toàn observable

Không phải mọi correction đều có ground truth tự động.

## 13.2. LLM judge có thể circular

Nếu cùng class model vừa tạo response vừa tự giải thích correction, evaluation dễ bị self-serving hoặc unstable.

## 13.3. Precedence đề xuất — chỉ cho provenance/label, không phải authority

```text
1. Explicit user semantic feedback
2. Deterministic source/proof/runtime evidence
3. EOCL structured events
4. Exact turn/run linkage
5. Human/operational annotation khi cần
6. LLM-derived classification ở shadow/advisory level
```

Đây là thứ tự xác định **nguồn và độ tin cậy của feedback label**. Nó không cấp quyền mutate source, write lease, proof, EOCL `accept`, P5 assignment hay release. EOCL authority, deterministic proof và các security/data floors vẫn độc lập và không bị user confirmation override.

## 13.4. Ba mức evidence cho feedback label

```text
OBSERVED
  user nói explicit hoặc deterministic event trực tiếp chứng minh

DERIVED_HIGH_CONFIDENCE
  relation có structured evidence đủ mạnh

INFERRED / UNKNOWN
  chỉ có model interpretation hoặc evidence chưa đủ
```

Policy learning chỉ dùng label có provenance phù hợp.

---

# 14. PROBLEM STATE MACHINE ĐỀ XUẤT

State ontology v1 giữ nhỏ; engineering progress được derive từ EOCL RUN/WAVE đã exact-link, không nhân bản thành `ENGINEERING_ACTIVE`:

```text
OPEN → PROVISIONALLY_RESOLVED → RESOLVED_CONFIRMED
  │              │                 │
  ├──────────────┴── same-problem correction → REOPENED → PROVISIONALLY_RESOLVED
  ├── explicit observation-horizon closure → RESOLVED_UNCONFIRMED
  └── explicit terminal disposition → SUPERSEDED | BLOCKED | ABANDONED
```

## 14.1. `PROVISIONALLY_RESOLVED` là cần thiết

Assistant vừa báo xong không được nhảy thẳng tới confirmed.

## 14.2. Silence không phải confirmation

Không user reply có thể là:

- user bận;
- chưa kiểm tra;
- bỏ cuộc;
- chuyển topic.

Do đó:

```text
silence != RESOLVED_CONFIRMED
```

## 14.3. Reopen là outcome có giá trị cao

Nếu problem đã provisional/confirmed rồi user quay lại cùng lỗi, đây là `REOPENED`.

Reopen rate là metric chất lượng mạnh hơn raw run acceptance.

---

# 15. SAME-PROBLEM LINKING: VẤN ĐỀ KHÓ NHẤT

## 15.1. Không được semantic-hash raw prompt

Raw text vừa privacy-sensitive vừa dễ sai vì user diễn đạt lại.

## 15.2. Không được dựa chỉ vào proximity

Hai turn gần nhau có thể là hai problem khác.

Hai turn cách xa nhiều giờ/conversation có thể là cùng problem.

## 15.3. Linking policy đề xuất

Tại mỗi user turn, semantic controller phân loại relation với active problem(s):

```text
SAME_PROBLEM
NEW_REVISION_OF_SAME_PROBLEM
NEW_SUBPROBLEM
NEW_PROBLEM
CONFIRM_OR_REOPEN_EXISTING
AMBIGUOUS
```

Persist **relation result + confidence/provenance**, không persist raw reasoning.

## 15.4. Fail-closed cho ambiguous relation

Nếu không chắc:

```text
do not merge histories automatically for policy evidence
```

Có thể giữ `AMBIGUOUS_LINK` và chỉ dùng descriptive analysis.

## 15.5. One active primary problem mặc định

Để tránh ontology nổ:

- mỗi material task có một primary problem;
- chỉ tạo child/subproblem khi user tách rõ requirement độc lập;
- không xây arbitrary problem graph ở v1.

---

# 16. MINIMAL DATA MODEL — MỘT LEDGER, KHÔNG CÓ SECOND AUTHORITY

Có hai phương án khả thi.

## 16.1. Phương án khuyến nghị: thêm hai minimal tables typed vào canonical ledger

Không tạo database thứ hai, arbitrary `metadata_json`/`payload_json`, transcript store hoặc semantic hash của prompt. V1 dùng **strict typed/allowlisted fields**; raw prompt/response, CoT, arbitrary nested payload, raw unresolved criteria và business/source content đều bị reject.

```text
problem_threads
  opaque random problem_id; current_revision; resolution_state
  bounded existing task_class; engineering_floor = REQUIRED | NOT_APPLICABLE | UNKNOWN
  created_at; updated_at; closed_at; latest_problem_event_seq; latest_problem_event_hash

problem_events
  monotonic seq; unique event_id; nullable problem_id only for AMBIGUOUS/UNLINKED
  exact task_id; turn_id; trace_id; run_id; wave_id; capsule_id; conversation_epoch
  relation_type; link_status = EXACT | AMBIGUOUS | UNLINKED; link_role = PRIMARY | SECONDARY
  feedback_intent; causal_mechanism; economic_class; provenance; evidence_level
  eligible_for_policy; state_before; state_after; bounded reason_code
  criteria_count; criteria_fingerprint; event_time; prev_hash; event_hash
```

`task_id` là exact linkage khi có, nhưng không alias thành `problem_id`: task có thể terminal/supersede trước khi cùng problem reopen. Một run chỉ có tối đa một primary problem; secondary relation không double-count duration/resource/cost trước khi có allocation contract. `event_id` giống bytes là idempotent; reuse khác bytes fail closed. Không có historical causal backfill.

## 16.2. Tại sao không chỉ nhét `problem_id` vào run metadata?

Vì problem tồn tại:

- trước RUN đầu tiên;
- giữa hai RUN;
- sau RUN accepted nhưng trước user confirmation;
- qua conversation rollover.

Do đó cần một problem-level object thật, nhưng vẫn nằm trong **same canonical ledger**.

## 16.3. Không thêm public tool thứ 9

Problem evidence nên đi qua nested `task_control(action="problem")`/internal host correlation path. Nó là public schema delta của tool hiện có, không phải tool thứ chín; vì vậy cần exact contract SHA, connector/schema refresh, loaded-runtime proof và manifest mới cho mọi future P5 epoch.

Public `smart-v3=8` giữ nguyên.

---

# 17. PRIVACY / DATA MINIMIZATION

PRL không được biến ledger thành transcript archive.

## 17.1. Không lưu

- raw user prompt;
- raw assistant response;
- chain-of-thought;
- private reasoning;
- full source code;
- stdout/stderr dài;
- secrets;
- personal content không cần cho causal evaluation.

## 17.2. Chỉ lưu structured metadata

```text
problem_id
problem_revision
turn_id / trace_id
relation_type
feedback_type
cause_code
confidence/provenance
run_id/wave_id/proof ids
resolution state
bounded task class
```

## 17.3. Content-free vẫn đủ để nghiên cứu

Ta không cần biết câu user viết chính xác là gì để đo:

- correction count;
- correction cause;
- problem duration;
- number of attempts;
- reopen;
- proof/run linkage.

---

# 18. ĐỊNH NGHĨA “KẾT QUẢ TỐT HƠN”

Không nên chấm hai assistant responses bằng prose similarity hay một overall LLM score.

Response/attempt sau tốt hơn nếu evidence cho thấy một ordering rõ.

## 18.1. Lexicographic ordering đề xuất

```text
1. user intent alignment
2. engineering correctness / no critical defect
3. proof/oracle coverage
4. unresolved problem reduction
5. avoidable correction reduction
6. problem-resolution time/tail
7. engineering rework burden
8. measured resource/cost
9. simplicity / maintainability
```

## 18.2. Ví dụ

Attempt A:

```text
diagnosis = service layer
unit proof = pass
user says = still failing in actual app
```

Attempt B:

```text
diagnosis = BFF payload normalization
unit + integration path = pass
user confirms actual app works
```

B tốt hơn A không phải vì prose hay hơn, mà vì:

- oracle gần user path hơn;
- problem state đi từ unresolved -> resolved;
- correction requirement được đóng;
- không regression.

---

# 19. KHÔNG DÙNG MỘT SCALAR LOSS QUÁ SỚM

Một công thức kiểu:

```text
problem loss = time + corrections + cost + defects
```

trông hấp dẫn nhưng sai dimension nếu chưa có utility weights.

## 19.1. Loss vector tốt hơn

```text
Problem Resolution Loss Vector = (
  unresolved_or_quality_failure,
  avoidable_correction_burden,
  problem_resolution_time,
  engineering_repair_burden,
  runtime/proof loss,
  human intervention,
  measured monetary/resource cost
)
```

Dùng lexicographic hoặc Pareto analysis.

Chỉ tạo scalar economics khi operator có calibrated weights.

## 19.2. Đây là mở rộng tự nhiên của doctrine hiện tại

Current project đã dùng lexicographic objective cho accepted-result economics.

PRL nên giữ cùng triết lý, không quay lại một điểm score mơ hồ.

---

# 20. METRICS ĐỀ XUẤT

## 20.1. Primary problem outcome

### Problem Resolution Rate

```text
resolved_confirmed / eligible_problem_threads
```

Báo riêng confirmed và unconfirmed.

### First-Response Resolution Rate

Problem resolved mà không có avoidable corrective feedback sau first substantive attempt.

Không trộn new requirement vào denominator correction.

### Reopen Rate

```text
reopened / provisionally_or_confirmed_resolved
```

## 20.2. Interaction burden

### Raw correction counts

Giữ vector theo type.

### Avoidable Correction Count

Chỉ feedback được causal/provenance label là avoidable.

### Nudge count

User phải nhắc agent tiếp tục/hoàn thiện nhưng không cung cấp substantive new info.

SWE-Together dùng weighting correction + 0.2*nudge. Coding Web có thể report metric tương thích nghiên cứu ở **shadow analytics**, nhưng không dùng weight 0.2 làm production policy nếu chưa local-calibrate.

## 20.3. Time

### Time to Problem Resolution (TTPR)

Từ first problem turn visible tới resolution event.

Phải ghi measurement provenance.

### TTPR p50/p90

Tail quan trọng hơn mean.

### Time to First Correct Technical Attempt

Nếu có oracle/user evidence phân biệt.

## 20.4. Engineering burden per problem

```text
runs_per_problem
waves_per_problem
replans_per_problem
proofs_per_problem
accepted_runs_before_final_resolution
```

Metric cuối rất hữu ích:

> Có bao nhiêu accepted engineering attempts nhưng problem vẫn tiếp tục?

## 20.5. Causal correction mix

```text
assistant misunderstanding
wrong root cause
proof/oracle gap
runtime failure
source/workspace mismatch
requirement evolution
user new info
preference change
unknown
```

## 20.6. Resolution confirmation coverage

```text
confirmed
unconfirmed
reopened
unknown
```

Không biến unconfirmed thành success tuyệt đối.

---

# 21. ACCEPTED PROBLEM RESOLUTION ECONOMICS

Current Accepted-Result Economics không cần bỏ.

Mô hình mới:

```text
Accepted Problem Resolution
    |
    +-- conversation/intent correctness
    +-- accepted engineering result(s)
    +-- user correction burden
    +-- reopen outcome
    +-- problem-level time
    +-- measured cost
```

## 21.1. Relationship

```text
Accepted Result Economics
  = execution-attempt economics

Accepted Problem Resolution Economics
  = end-to-end user-problem economics
```

## 21.2. Một problem có thể chứa nhiều accepted results

Do đó tổng economic loss không được tính bằng cách lấy mỗi RUN là independent task.

Phải group theo problem thread trước khi tính:

```text
attempt count
repair chain
user correction chain
final resolution
```

---

# 22. CAUSAL MODEL

Một DAG khái niệm:

```text
Initial user problem / latent intent
        |
        v
Assistant interpretation ---- Context quality
        |                          |
        v                          |
Engineering objective             |
        |                          |
        v                          |
Implementation / execution <------+
        |
        v
Proof / oracle strength
        |
        v
Assistant completion response
        |
        v
User observation / feedback
        |
        +--> requirement evolution / new evidence
        |
        +--> correction due to assistant/system defect
        |
        v
Revised problem state
```

Confounders:

- source drift;
- environment drift;
- user reveals information only later;
- task scope actually changes;
- external system changes;
- conversation compaction/recovery;
- oracle coverage.

Vì vậy không thể nói:

```text
“user sent follow-up -> assistant failed”
```

mà không classify mechanism.

---

# 23. PROSPECTIVE-ONLY CAUSAL LABELING

Dự án đã học bài học tương tự với P2 failure taxonomy.

## 23.1. Không backfill lịch sử bằng guess

Lịch sử có thể dùng case study và descriptive reconstruction.

Nhưng causal promotion data phải prospective.

## 23.2. Tại event source

Khi user feedback tới, controller có đủ context semantic ngay lúc đó để ghi:

```text
same_problem?
intent_delta?
feedback_type?
known correction cause?
```

Đây là thời điểm tốt hơn nhiều so với đọc transcript cũ sau vài tháng.

## 23.3. Unknown giữ unknown

Nếu cause không chứng minh được:

```text
UNKNOWN
```

không ép vào `assistant_error` để tăng coverage.

---

# 24. METHODOLOGY CHO CLASSIFIER / LABEL QUALITY

## 24.1. Shadow classifier trước

Nếu dùng model/rules để gán feedback taxonomy:

- không ảnh hưởng routing;
- không ảnh hưởng acceptance;
- không ảnh hưởng user response;
- chỉ ghi shadow recommendation.

## 24.2. Manual validation sample

Định kỳ lấy bounded sample các correction events và human-review:

- same-problem link đúng chưa;
- requirement-new vs correction đúng chưa;
- causal mechanism đúng chưa.

## 24.3. Reliability gates

Không cần coi threshold là universal truth, nhưng có thể preregister local gates như:

```text
same-problem link precision >= 0.95 on reviewed sample
major feedback-category agreement >= 0.85
no systematic bias converting new requirement into assistant failure
```

Nếu không đạt, classifier chỉ descriptive.

## 24.4. Không optimize label coverage bằng cách làm label rộng

Một classifier 100% coverage nhưng gom mọi thứ vào “assistant error” là vô dụng.

---

# 25. SESSION / COMPACTION CONTINUITY

PRL tạo thêm một lợi ích lớn: chống context drift.

Current handoff capsule đã chứa:

- task objective;
- current step;
- next step;
- run/wave;
- source/proof identities;
- active lanes;
- pending messages.

Đề xuất bổ sung content-free:

```text
active_problem_id
problem_revision
latest_feedback_relation
latest_correction_class
problem_state
unresolved_acceptance_criteria
```

Không cần replay transcript.

## 25.1. Sau compaction/reconnect

Controller phải reconcile:

```text
latest turn identity
+ problem state
+ EOCL state
+ source/proof state
```

trước khi action.

## 25.2. Detect convergence loop

Nếu cùng problem liên tục có:

```text
same correction class
same files reread
same objective re-announced
no reduction in unresolved criteria
```

có thể flag `NON_CONVERGENT_LOOP` để force replan, không tiếp tục unchanged attempt.

Điều này trực tiếp phản ánh các community failure reports.

---

# 26. USER RESOLUTION KHÔNG ĐƯỢC LÀM QUYỀN ACCEPT SOURCE

Một user có thể nói “ok” nhưng code có critical defect.

Một proof có thể xanh nhưng user nói vẫn lỗi.

Hai mặt phải độc lập.

## 26.1. Coding task resolution matrix

| Engineering accepted | User resolution | Problem state |
|---|---|---|
| no | no | unresolved |
| yes | no | engineering accepted, problem unresolved/reopened |
| no | yes | insufficient engineering evidence; cannot claim trusted technical resolution |
| yes | yes | resolved confirmed |

Đây là lý do cần hai planes.

---

# 27. MỘT PROBLEM CÓ THỂ ĐƯỢC “RESOLVED” MÀ KHÔNG CÓ CODE

PRL không nên quá code-centric.

Một problem có thể kết thúc bằng:

- correct diagnosis;
- user instruction;
- configuration change;
- explanation;
- external permission blocker identified.

Do đó `engineering_accepted` có thể `NOT_APPLICABLE`.

Nhưng với coding/mutation task, engineering proof vẫn là hard floor.

---

# 28. TÁC ĐỘNG TỚI P2

P2 hiện đang phân loại system/solution rework ở RUN level.

PRL bổ sung signal:

```text
user correction cause
```

Điều này giúp phân biệt một số case chưa rõ:

```text
CHECK_FAILED + user says “wrong behavior”
```

với:

```text
CHECK_FAILED + user adds a new constraint
```

Nhưng PRL không thay P2 failure taxonomy.

Hai nguồn join lại mới mạnh.

---

# 29. TÁC ĐỘNG TỚI P4

P4 hiện hỏi:

> pre-mutation signal nào predict repair?

Sau PRL, outcome phong phú hơn:

```text
predict avoidable problem correction?
predict reopen?
predict problem-level first-pass resolution?
```

Tuy nhiên:

- không mở P4 model mới ngay;
- tiếp tục shadow;
- chỉ đổi endpoint khi PRL labels đã validated.

---

# 30. TÁC ĐỘNG TỚI P5

P5 treatment effect hiện nhìn first-pass/rework/TTAR ở execution level.

PRL có thể cho future endpoint tốt hơn:

```text
problem-level first-pass resolution
avoidable correction burden
problem TTPR
reopen rate
```

Nhưng **không sửa P5-A0 hiện tại để chờ PRL**.

Đúng sequence:

1. PRL shadow instrumentation.
2. Validate measurement.
3. Chỉ future epoch mới preregister problem-level endpoints.
4. Không reinterpret old P5 data bằng metric mới.

---

# 31. TÁC ĐỘNG TỚI ROUTING / MODEL CHOICE

Không dùng PRL để auto-route ngay.

Sau đủ data, PRL có thể trả lời:

- task class nào gây nhiều avoidable user correction;
- loại correction nào giảm khi dùng route/model khác;
- high integration width có liên quan reopen không;
- model mạnh hơn có thực sự giảm user burden hay chỉ giảm internal replan.

Đây là evidence tốt hơn raw benchmark score.

---

# 32. ROADMAP TRIỂN KHAI TỐI THIỂU

Không tạo một chương trình architecture khổng lồ. Chỉ năm bounded waves.

## PRL-A — Problem Identity & Exact Linkage

### Mục tiêu

Tạo `problem_id`, `problem_revision`, exact turn/run relation.

### Scope

- canonical ledger minimal schema;
- host turn binding reuse;
- task/run metadata carry problem identity;
- handoff capsule carries active problem state.

### Không làm

- không classifier;
- không routing;
- không policy;
- không raw transcript.

### Acceptance

```text
one problem can span multiple runs
one problem can span conversation epochs
turn/run link exact, no timestamp-proximity inference
no second ledger
no public tool addition
```

## PRL-B — Feedback Taxonomy Shadow

### Mục tiêu

Ghi prospective feedback relation/type/cause/economic class.

### Policy

- observed/derived/inferred provenance;
- unknown preserved;
- no production behavior change.

### Acceptance

- new requirement không bị auto-count là assistant failure;
- same-problem correction có parent attempt;
- manual-reviewed sample đạt quality gate định trước.

## PRL-C — Resolution / Reopen Outcome

### Mục tiêu

Bổ sung:

```text
PROVISIONALLY_RESOLVED
RESOLVED_CONFIRMED
RESOLVED_UNCONFIRMED
REOPENED
SUPERSEDED
```

### Acceptance

- assistant completion không auto-confirm;
- user explicit correction reopens đúng problem;
- silence không confirm;
- coding resolution yêu cầu engineering floor phù hợp.

## PRL-D — Problem Economics Reporter

### Mục tiêu

Read-only report:

```text
problem resolution rate
first-response resolution
correction mix
avoidable correction burden
reopen rate
TTPR p50/p90
runs/waves/replans per problem
accepted-runs-before-final-resolution
```

### Policy

- descriptive first;
- coverage explicit;
- unknown not zero;
- no scalar loss without calibrated utility.

## PRL-E — Experimental Integration

Chỉ sau measurement validation.

Potential future:

- P4 problem-level predictive endpoint;
- P5 problem-level treatment endpoint;
- routing economics.

Không automatic policy activation.

---

# 33. TRIỂN KHAI KHÔNG ĐƯỢC LÀM GÌ

Freeze list:

- second orchestration ledger;
- transcript database;
- public MCP tool thứ 9;
- generic “memory platform”;
- knowledge graph toàn bộ conversation;
- automatic LLM judge làm authority;
- retroactive labeling hàng nghìn historical turns bằng guess;
- auto-routing từ correction score;
- scalar “user quality score” chưa calibrate;
- forced confirmation prompt sau mọi task;
- user-visible bureaucracy;
- multi-agent evaluator fleet.

---

# 34. FALSIFIABLE HYPOTHESES

Một nghiên cứu tốt phải có điều kiện bác bỏ.

## H1 — Run acceptance is insufficient

**Hypothesis:** một tỷ lệ vật chất problem có ≥1 accepted engineering run nhưng sau đó vẫn có same-problem corrective feedback/reopen.

**Bác bỏ nếu:** prospective data cho thấy gần như mọi accepted run đồng thời resolve problem và correction sau acceptance cực hiếm.

Nếu H1 bị bác bỏ, PRL economics có thể không đáng complexity lớn.

## H2 — Avoidable correction burden là cost center thật

**Hypothesis:** problem có avoidable corrections có TTPR và engineering attempts cao hơn rõ rệt.

**Bác bỏ nếu:** corrections hầu hết là low-cost/legitimate requirement growth và không kéo problem economics.

## H3 — Proof/oracle gap tạo user reopen

**Hypothesis:** một phần đáng kể same-problem “still failing” feedback xảy ra sau proof xanh nhưng oracle không bao phủ actual user path.

**Bác bỏ nếu:** reopen chủ yếu do new requirements/environment changes.

## H4 — Exact problem checkpoint giảm context-recovery loss

**Hypothesis:** sau handoff/compaction, problem threads có exact checkpoint ít stale-context/repeated-correction hơn.

Cần paired/natural comparison, không claim từ anecdote.

## H5 — User correction taxonomy có actionable separation

**Hypothesis:** các categories tạo distinct engineering mechanisms và economics.

**Bác bỏ nếu:** label agreement thấp hoặc categories không thay decision.

## H6 — Problem-level metrics thay đổi prioritization

**Hypothesis:** một số task class nhìn tốt ở RUN-level nhưng xấu ở problem correction/reopen.

Nếu không có ranking change, giữ PRL chỉ làm reporting layer nhỏ.

---

# 35. EVALUATION PLAN

## 35.1. Stage 1 — Measurement integrity

Không cần chờ hàng trăm problem mới implement.

Sau khi instrumentation có mặt, collect natural workload ngay.

Review khi có bounded sample đủ kiểm tra integrity, ví dụ:

```text
30–50 problem threads / correction events để kiểm tra link + taxonomy mechanics
```

Đây không phải efficacy sample size.

## 35.2. Stage 2 — Descriptive stability

Khi có khoảng 100+ representative problem threads, bắt đầu tin hơn vào:

- correction mix;
- reopen rate;
- TTPR distribution;
- task-class strata.

Không coi 100 là universal statistical magic number; nó là operational review threshold.

## 35.3. Stage 3 — Causal intervention

Chỉ khi mechanism đủ rõ mới preregister treatment.

Ví dụ:

```text
problem checkpoint treatment
oracle expansion treatment
pre-response completion gate
```

Compare problem outcomes, không chỉ RUN outcomes.

---

# 36. ANTI-GAMING

Khi metric trở thành target, agent có thể tối ưu sai.

## 36.1. Correction count có thể bị game bằng cách hỏi ít user hơn

Agent có thể tránh correction bằng cách không báo tiến độ hoặc không hỏi clarification.

Do đó quality/resolution floor đứng trước correction burden.

## 36.2. First-response resolution có thể khuyến khích over-scoping

Agent cố sửa quá nhiều ngay lần đầu để tránh follow-up.

Cần penalize regression/overbroad change.

## 36.3. Confirmation rate có thể bị game bằng UX prompt

Không spam “đã đúng chưa?” chỉ để lấy confirmed flag.

Confirmation phải xuất hiện tự nhiên hoặc ở meaningful terminal boundary.

## 36.4. Reopen có observation censoring

Nếu user không quay lại, không biết chắc problem không tái phát.

Do đó report confirmed/unconfirmed và observation window.

---

# 37. QUALITY FLOOR

Problem-level optimization không được làm yếu engineering floors.

Order:

```text
security/data/authority
 -> engineering correctness
 -> trusted proof
 -> user problem resolution
 -> correction/time/cost economics
```

Không được đóng problem chỉ để đẹp metric nếu proof còn fail.

---

# 38. “PRODUCTIVE REPLAN” VÀ “PRODUCTIVE USER FEEDBACK”

HR evidence trước đó đã cho thấy không phải mọi REPLAN đều đắt hơn; một số replan là correction hữu ích.

PRL mở rộng cùng nguyên tắc:

> Không phải mọi user correction đều là loss.

## 38.1. Productive feedback

- user cung cấp hidden constraint;
- new evidence không thể biết trước;
- requirement legitimately evolves;
- preference changes.

## 38.2. Avoidable feedback

- assistant quên explicit constraint;
- sửa sai workspace;
- report done nhưng actual path chưa test;
- stale instruction replay;
- root cause sai mà evidence ban đầu đủ để phân biệt;
- assistant bỏ sót phần objective đã explicit.

Mục tiêu:

```text
minimize avoidable feedback burden
```

không phải:

```text
minimize user interaction
```

---

# 39. PRACTICAL EXAMPLES

## Case A — New requirement, không phải failure

```text
U1: sửa create project
R1: create works
U2: thêm investor field
```

Nếu investor chưa từng được yêu cầu:

```text
relation = NEW_REVISION / ADD_REQUIREMENT
avoidability = legitimate growth
```

## Case B — Wrong target

```text
U1: fix workspace A
agent changes workspace B
U2: “sao lại sửa B?”
```

```text
cause = WRONG_TARGET_OR_WORKSPACE
avoidability = avoidable correction
```

## Case C — Green unit test, actual UI vẫn lỗi

```text
proof = service unit pass
user = actual app still fails
```

Potential cause:

```text
PROOF_ORACLE_GAP
```

Nếu next attempt adds integration path và user confirms, đây là strong learning case.

## Case D — Compaction replay

User correction đã được xử lý nhưng sau rollover assistant quay lại instruction cũ.

```text
cause = STALE_CONTEXT_OR_REPLAY
```

PRL checkpoint có thể làm exact regression oracle.

---

# 40. REPORTING CHO OPERATOR

Problem-level dashboard nên rất nhỏ.

## 40.1. Current period

```text
problems opened
resolved confirmed
resolved unconfirmed
reopened
first-response resolution
TTPR p50/p90
```

## 40.2. User burden

```text
avoidable corrections / problem
productive clarifications / problem
nudges / problem
```

## 40.3. Root causes

Top correction causes:

- wrong scope;
- wrong root cause;
- oracle gap;
- runtime failure;
- stale context;
- requirement evolution.

## 40.4. Engineering coupling

```text
accepted runs before resolution
replans per problem
proof count per problem
```

---

# 41. QUAN HỆ VỚI MASTER ROADMAP HIỆN TẠI

PRL không phủ định:

- DRE;
- P2 prospective taxonomy;
- P4 passive collection;
- P5 natural experiment;
- Tail Economics;
- exact execution/proof identity.

Nó sửa unit of analysis ở tầng cao hơn.

Roadmap logic trở thành:

```text
EXECUTION TRUTH
  ↓
EXACT MUTATION / PROOF
  ↓
ACCEPTED ENGINEERING RESULT
  ↓
PROBLEM RESOLUTION LINEAGE
  ↓
USER CORRECTION / REOPEN OUTCOME
  ↓
ACCEPTED PROBLEM RESOLUTION ECONOMICS
  ↓
CAUSAL LEARNING
```

Không cần dừng P5 hiện tại để chờ PRL.

---

# 42. THAY ĐỔI NORTH STAR — NHƯNG KHÔNG RENAME CODE VỘI

Strategic language nên được nâng:

> **Minimize Accepted Problem Resolution Loss under fixed quality, security, authority and correctness floors.**

Nhưng không cần rename ngay:

- function;
- table;
- report;
- P5 schema;
- docs cũ.

Accepted-Result Economics vẫn là một subsystem đúng.

Chỉ khi PRL measurement proven useful mới migrate terminology ở maintained docs.

---

# 43. DECISION RULES CHO MỌI USER FOLLOW-UP

Một decision card có thể chạy semantic, không cần public tool:

```text
1. Follow-up có liên quan active problem không?
   NO -> new problem.

2. User đang thêm requirement/new evidence hay sửa một lỗi cũ?
   NEW -> problem revision / productive feedback.

3. Nếu correction: correction nhắm vào understanding, target, solution, proof hay runtime?
   -> structured type.

4. Có evidence để gán cause không?
   NO -> UNKNOWN.

5. Prior attempt có accepted engineering result không?
   YES + same-problem still failing -> mark problem unresolved/reopened.

6. New engineering work cần thiết?
   -> open/reuse EOCL lineage theo authority hiện tại.

7. Khi engineering accepted:
   -> PROVISIONALLY_RESOLVED, không auto CONFIRMED.

8. User explicit confirms?
   -> RESOLVED_CONFIRMED.

9. User supplies same-problem failure later?
   -> REOPENED.
```

---

# 44. FAILURE TAXONOMY CỦA PRL ITSELF

PRL cũng có thể sai.

## PRL-F1 — False merge

Hai problem khác bị gộp.

## PRL-F2 — False split

Cùng problem bị tách thành nhiều thread.

## PRL-F3 — Requirement growth mislabeled as failure

Làm metric bất công với agent.

## PRL-F4 — Avoidable correction mislabeled as new requirement

Che lỗi agent.

## PRL-F5 — Confirmation inference

Silence bị coi là confirm.

## PRL-F6 — Cross-conversation stale active pointer

Problem cũ được reactivated sai.

## PRL-F7 — Transcript leakage

Structured logging vô tình chứa raw content.

## PRL-F8 — Policy feedback loop quá sớm

Classifier chưa validated nhưng đã thay routing.

Mỗi failure cần focused regression nếu PRL được implement.

---

# 45. PROOF / TEST STRATEGY CHO IMPLEMENTATION TƯƠNG LAI

## 45.1. Deterministic unit tests

- same problem spans two runs;
- problem spans two conversation epochs;
- new problem in same conversation;
- silence remains unconfirmed;
- explicit user correction reopens;
- new requirement not counted as avoidable correction;
- wrong-workspace correction is avoidable when explicit target evidence exists;
- raw prompt/response not persisted.

## 45.2. Integration tests

- host turn bind -> problem -> run -> proof -> response -> correction;
- handoff/restart preserves active problem pointer;
- EOCL authority unchanged;
- no extra public tool.

## 45.3. Historical replay tests

Use anonymized/synthetic state transitions, không replay private conversation.

## 45.4. Manual annotation audit

Review representative real correction events to validate taxonomy.

---

# 46. WHY THIS IS NOT OVERENGINEERING

Một proposal mới chỉ hợp lý nếu tạo decision mới với chi phí thấp.

PRL pass test này vì:

1. `HYPOTHESIS / MEASUREMENT_GAP`: existing task/run history cho thấy canonical same-problem grouping chưa tồn tại, nhưng local prevalence của user correction/multiple attempts chỉ được xác minh prospectively bằng PRL exact-link evidence; không được suy ra từ prose hoặc historical text.
2. Existing primitives giảm implementation cost mạnh.
3. Unit of analysis hiện tại có demonstrable blind spot.
4. External 2026 research independently chuyển sang multi-turn correction metrics.
5. Community failure reports align với same problem.
6. PRL có thể triển khai content-free, shadow-first, không thêm tool/authority.
7. Nó trực tiếp nâng chất lượng P2/P4/P5 economics.

PRL sẽ trở thành overengineering nếu:

- build knowledge graph lớn;
- store transcript;
- thêm generic memory engine;
- tạo second DB/service;
- bắt user quản lý problem IDs;
- dùng nó để auto-route trước validation.

---

# 47. PHƯƠNG PHÁP NGHIÊN CỨU NỘI BỘ SAU KHI IMPLEMENT

## 47.1. Research questions

### RQ1

Bao nhiêu accepted engineering results thật sự là final problem resolution?

### RQ2

Correction burden phân bố thế nào theo task class?

### RQ3

Bao nhiêu correction là avoidable vs requirement evolution?

### RQ4

Correction mechanism nào đóng góp lớn nhất vào TTPR tail?

### RQ5

Proof/oracle strength có liên quan reopen không?

### RQ6

Compaction/handoff có liên quan stale-context correction không?

### RQ7

Problem-level measurement có thay ranking ưu tiên model/routing/intervention so với run-level economics không?

## 47.2. Design

- prospective observational first;
- stratify feature/bugfix/diagnose;
- exact source/runtime identity;
- report censoring/missingness;
- no historical causal backfill;
- paired/randomized only khi testing intervention.

---

# 48. INTERPRETATION RULES

## Rule 1

`Accepted RUN` là necessary evidence cho coding attempt, không phải sufficient evidence cho user problem resolution.

## Rule 2

User follow-up không tự động là failure.

## Rule 3

User explicit correction là strong semantic evidence, nhưng cause vẫn có thể unknown.

## Rule 4

Silence không phải confirmation.

## Rule 5

`quality_outcome.oracle_pass` không được đổi tên thành `problem_resolved`.

## Rule 6

Problem link không dùng timestamp proximity.

## Rule 7

PRL không có write/proof authority.

## Rule 8

Unknown không phải zero/nonfailure.

## Rule 9

Policy promotion chỉ dựa prospective validated evidence.

## Rule 10

Nếu PRL không tạo decision khác biệt sau đủ dữ liệu, giữ nó nhỏ hoặc retire phần không cần thiết.

---

# 49. KẾT LUẬN KHOA HỌC

Bài toán mà Coding Web đang tiến tới không còn là “coding agent có sửa được code không?”.

Nó là một bài toán **interactive control + software engineering + requirements evolution + causal evaluation**.

Một coding-agent session thực tế có ba loại uncertainty:

```text
1. user-intent uncertainty
2. engineering-solution uncertainty
3. execution/proof/runtime uncertainty
```

EOCL đã xử lý rất tốt loại 3 và một phần loại 2.

P2/P4/P5 đang học loại 2.

PRL là cơ chế cần thiết để biểu diễn loại 1 và nối nó với hai loại còn lại.

Research bên ngoài hỗ trợ mạnh luận điểm này:

- conversational repair cho thấy correction là cơ chế hội tụ của mutual understanding;
- requirements traceability cho thấy requirement phải được nối xuyên vòng đời artifact;
- HULA cho thấy human guidance là phần thật của software-agent workflow;
- RECODE-H cho thấy feedback richness tác động outcome;
- SWE-Together đo user correction burden bên cạnh correctness;
- SWE-Interact chứng minh single-turn score không đủ đại diện multi-turn engineering;
- closed-loop evaluation cho thấy iterative repair/stopping là năng lực riêng;
- community issue reports cho thấy context retention không đồng nghĩa convergence retention.

Do đó một hệ thống evidence-governed coding agent trưởng thành cần phân biệt:

```text
“model generated an answer”
“code passed a test”
“RUN was accepted”
“user problem was resolved”
```

Bốn statement không được collapse.

---

# 50. QUAN ĐIỂM CUỐI CÙNG VÀ HƯỚNG ĐI

Quan điểm đề xuất:

> **Coding Web nên tiếp tục là lean execution system, nhưng đổi điểm nhìn từ RUN-centric evaluation sang Problem-centric evaluation ở lớp analytics/causal lineage.**

Không cần xây lại kiến trúc.

Ta đã có gần đủ atoms:

```text
turn_id / trace_id
conversation_epoch
objective revision
run / wave
replan
proof
quality outcome
accept/reject
observation spans
handoff capsule
```

Phần thiếu là một semantic spine mỏng:

```text
problem_id
problem_revision
turn relation
feedback type/cause
resolution/reopen state
```

Khi spine này có mặt, Coding Web có thể lần đầu trả lời đầy đủ:

> Một vấn đề người dùng được hiểu như thế nào?
> Lần đầu hệ thống đã giải đúng chưa?
> Người dùng phải sửa hướng ở đâu?
> Correction đó do requirement mới hay lỗi tránh được?
> Engineering attempt nào thực sự đóng problem?
> Proof nào hỗ trợ nó?
> Problem có reopen không?
> Tổng thời gian/cost/human burden để đi tới resolution là bao nhiêu?
> Intervention nào thực sự giảm burden ở problem level?

Đây là tầng cần thiết trước khi gọi một routing/model/agent architecture là “tối ưu cho người dùng”.

North Star chiến lược vì vậy nên là:

> **Accepted Problem Resolution — đúng vấn đề, đúng kỹ thuật, đủ bằng chứng, ít avoidable correction, tail thấp, cost hợp lý.**

Và doctrine triển khai:

```text
DO NOT BUILD A NEW ORCHESTRATOR
  ↓
ADD MINIMAL PROBLEM LINEAGE
  ↓
SHADOW-CLASSIFY FEEDBACK
  ↓
MEASURE RESOLUTION + REOPEN
  ↓
JOIN WITH EOCL / QUALITY / ECONOMICS
  ↓
VALIDATE LABEL QUALITY
  ↓
ONLY THEN USE FOR P4/P5 / ROUTING LEARNING
```

Nếu triển khai đúng, đây không phải một feature phụ.

Nó là việc **đổi đúng đơn vị tối ưu từ execution activity sang user problem resolution**.

---

# 51. DECISION LOG ĐỀ XUẤT

## D-PRL-01 — Problem thread là unit of end-to-end evaluation

**Decision:** RUN tiếp tục là execution unit; problem thread là user-resolution evaluation unit.

## D-PRL-02 — EOCL authority không đổi

**Decision:** PRL chỉ correlation/evaluation.

## D-PRL-03 — Correction taxonomy đa trục

**Decision:** không dùng follow-up count = failure count.

## D-PRL-04 — Prospective labeling

**Decision:** historical data dùng descriptive case study, causal labels thu prospective.

## D-PRL-05 — Confirmation semantics

**Decision:** silence ≠ confirmed resolved.

## D-PRL-06 — Content-free by design

**Decision:** không lưu raw transcript/CoT.

## D-PRL-07 — Shadow first

**Decision:** PRL không ảnh hưởng routing/P5 treatment trước measurement validation.

## D-PRL-08 — Accepted-result economics retained

**Decision:** existing economics trở thành execution component của problem-level economics.

## D-PRL-09 — No scalar utility without calibration

**Decision:** dùng lexicographic/loss vector trước.

## D-PRL-10 — Stop condition

**Decision:** nếu sau prospective study PRL không tạo actionable separation hoặc unit-of-analysis gap nhỏ không đáng kể, không mở rộng framework.

---

# 52. NGUỒN NỘI BỘ ĐÃ ĐỐI CHIẾU

1. `docs/CURRENT_STATE.md`
2. `docs/research/260822_CODING_WEB_EXECUTION_INTELLIGENCE_UPSTREAM_ADOPTION_AND_NEXT_IMPLEMENTATION_MASTER_PLAN.md`
3. `docs/research/260822_CODING_WEB_REWORK_DECISION_SCIENCE_AND_EXECUTION_DOCTRINE.md`
4. `resources/coding-tools-mcp/coding_tools_mcp/orchestration_ledger.py`
5. `resources/coding-tools-mcp/coding_tools_mcp/quality_outcomes.py`
6. `resources/coding-tools-mcp/coding_tools_mcp/coordination.py`
7. `resources/coding-tools-mcp/coding_tools_mcp/solution_shadow_control.py`
8. `electron/services/chatEvaluationJournal.js`
9. `electron/main.js`
10. `.coding-tools/task-history.json` — dùng như historical continuity/evidence projection, không thay canonical ledger.

---

# 53. TÀI LIỆU NGHIÊN CỨU / HỌC THUẬT THAM KHẢO

## R1 — Conversational repair foundation

E. A. Schegloff, G. Jefferson, H. Sacks. **The Preference for Self-Correction in the Organization of Repair in Conversation.** Language, 1977.
https://www.cambridge.org/core/journals/language/article/preference-for-selfcorrection-in-the-organization-of-repair-in-conversation/5549B861FDE7180B75FA5C382821875E

## R2 — User repair taxonomy in conversational agents

F. Alloatti et al. **A tag-based methodology for the detection of user repair strategies in task-oriented conversational agents.** Computer Speech & Language, 2024.
https://www.sciencedirect.com/science/article/pii/S0885230823001225

## R3 — Multi-turn conversational-agent evaluation survey

S. Guan et al. **Evaluating LLM-based Agents for Multi-Turn Conversations: A Survey.** 2025.
https://arxiv.org/abs/2503.22458

## R4 — Requirements Traceability systematic review

T. Koboyatshwene, Y. Ayalew. **Requirements Traceability: A Systematic Literature Review.** ACM SAC 2025.
https://doi.org/10.1145/3672608.3707952

## R5 — Pre-requirements traceability

J. Mucha, A. Kaufmann, D. Riehle. **A systematic literature review of pre-requirements specification traceability.** Requirements Engineering, 2024.
https://link.springer.com/article/10.1007/s00766-023-00412-z

## R6 — Issue-based requirements traceability

Y. Lyu, H. Cho, P. Jung, S. Lee. **A Systematic Literature Review of Issue-Based Requirement Traceability.** IEEE Access, 2023.
https://doi.org/10.1109/ACCESS.2023.3242294

## R7 — User feedback / requirements engineering

**Specifying requirements for collection and analysis of online user feedback.**
https://pmc.ncbi.nlm.nih.gov/articles/PMC9483507/

## R8 — Human-in-the-loop software development agents

W. Takerngsaksiri et al. **Human-In-the-Loop Software Development Agents.** 2024.
https://arxiv.org/abs/2411.12924

## R9 — RECODE-H

C. Miao et al. **RECODE-H: A Benchmark for Research Code Development with Interactive Human Feedback.** ICLR 2026.
https://arxiv.org/abs/2510.06186

## R10 — SWE-Together

Y. Wu et al. **SWE-Together: Evaluating Coding Agents in Interactive User Sessions.** 2026.
https://arxiv.org/abs/2606.29957
Project/benchmark design: https://togetherbench.com/design.html
Repository: https://github.com/Togetherbench/SWE-Together

## R11 — SWE-Interact

M. Raghavendra et al. **SWE-INTERACT: Reimagining SWE Benchmarks as User-Driven Long-Horizon Coding Sessions.** 2026.
https://arxiv.org/abs/2606.30573
Repository: https://github.com/scaleapi/SWE-Interact

## R12 — Interactive multi-requirement software engineering evaluation

D. Rontogiannis et al. **Interactive Evaluation of Large Language Models for Multi-Requirement Software Engineering Tasks.** AAAI 2026.
https://ojs.aaai.org/index.php/AAAI/article/view/40564

## R13 — Closed-loop coding agents

**Closed-loop evaluation of LLM agents for embedded software development.** Journal of Systems Architecture, 2026.
https://www.sciencedirect.com/science/article/pii/S1383762126002559

## R14 — User satisfaction in task-oriented dialogue

C. Siro, M. Aliannejadi, M. de Rijke. **Understanding User Satisfaction with Task-oriented Dialogue Systems.** 2022.
https://arxiv.org/abs/2204.12195

## R15 — Error taxonomy in dialogue systems

R. Higashinaka et al. **Integrated taxonomy of errors in chat-oriented dialogue systems.** SIGDIAL 2021.
https://aclanthology.org/2021.sigdial-1.10/

## R16 — Repair after imperfect AI interventions

**To Err is AI: Imperfect Interventions and Repair in a Conversational Agent Facilitating Group Chat Discussions.** PACM HCI, 2023.
https://doi.org/10.1145/3579532

## R17 — Human-agent repair taxonomy preprint

**The Art of Repair in Human-Agent Conversations: A Taxonomy of Repair Strategies by Users and LLM-Based Conversational Agents.**
https://sciety.org/articles/activity/10.21203/rs.3.rs-7301450/v1

## R18 — EvoCode-Bench

**EvoCode-Bench: Evaluating Coding Agents in Multi-Turn Iterative Interactions.** 2026.
https://github.com/UniPat-AI/EvoCodeBench

---

# 54. COMMUNITY / ENGINEERING DISCUSSION SOURCES

> Các nguồn dưới đây được dùng như operational signals và failure hypotheses; không được xem như thống kê đại diện toàn bộ người dùng.

## C1 — Compaction loses current task checkpoint

OpenAI Codex issue #25900.
https://github.com/openai/codex/issues/25900

## C2 — Stale conversation state resurfaces after correction

OpenAI Codex issue #32863.
https://github.com/openai/codex/issues/32863

## C3 — Repeated compaction degrades execution frontier / convergence

OpenAI Codex issue #34095.
https://github.com/openai/codex/issues/34095

## C4 — Stale prompt treated as active instruction after resume

OpenAI Codex issue #27731.
https://github.com/openai/codex/issues/27731

## C5 — Long-session handoff / continuity-risk discussion

OpenAI Codex issue #36584.
https://github.com/openai/codex/issues/36584

## C6 — Progressive context loss / request for empirical verification

OpenAI Codex issue #14347.
https://github.com/openai/codex/issues/14347

## C7 — Community report: partial completion + premature “finished”

r/codex discussion, March 2026.
https://www.reddit.com/r/codex/comments/1rhntb3/how_are_people_getting_codex_to_run_for_5_minutes/

## C8 — Community discussion: repeated self-review / changing mind

r/codex weekly/community discussion, July 2026.
https://www.reddit.com/r/codex/comments/1v1mgws/codex_weekly_discussion_megathread/

## C9 — Community discussion: context/loop/usage symptoms

r/codex discussion, July 2026.
https://www.reddit.com/r/codex/comments/1v2j087/can_we_talk_about_the_recent_actions/

---

# 55. SOURCE INTERPRETATION POLICY

Tài liệu dùng bốn loại evidence với weight khác nhau:

```text
A. Current Coding Web source / canonical runtime evidence
   -> architecture/status local

B. Peer-reviewed / published research
   -> general mechanisms/methodology

C. Preprints / new 2026 benchmarks
   -> current research direction, cần local validation

D. GitHub/Reddit/community reports
   -> failure hypotheses, không prevalence/causal effect
```

Không dùng category D để claim “Codex thường xuyên lỗi X%”.

Không dùng category B/C để tự động thay local architecture.

Local prospective evidence vẫn là authority cho promotion.

---

# 56. FINAL DOCTRINE

```text
USER PROBLEM
  ↓
PROBLEM IDENTITY / INTENT REVISION
  ↓
ASSISTANT ATTEMPT
  ↓
EOCL EXECUTION / PROOF / ACCEPTANCE
  ↓
ASSISTANT RESPONSE
  ↓
USER FEEDBACK
  ├── productive clarification / new requirement
  └── avoidable correction / reopen
  ↓
PROBLEM STATE UPDATE
  ↓
RESOLVED_CONFIRMED / UNCONFIRMED / REOPENED
  ↓
PROBLEM-LEVEL ECONOMICS
  ↓
CAUSAL LEARNING
```

**Không tối ưu “số lần model làm việc”.**
**Không tối ưu “số RUN accepted” độc lập.**
**Không tối ưu “ít follow-up” bằng cách giảm tương tác cần thiết.**

Tối ưu:

> **Một vấn đề thực của người dùng được giải quyết đúng, với engineering evidence đáng tin, ít avoidable correction, ít reopen, tail thấp và chi phí tổng hợp hợp lý.**

Đó là đơn vị đánh giá phù hợp cho giai đoạn trưởng thành tiếp theo của Coding Web.

---

**END — CW-PRL-20260823-v1**
