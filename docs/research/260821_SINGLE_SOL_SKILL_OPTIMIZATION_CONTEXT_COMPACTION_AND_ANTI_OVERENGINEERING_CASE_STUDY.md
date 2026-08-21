# CASE STUDY: TINH GỌN SKILL, ĐƠN AGENT SOL VÀ CHỐNG OVER-ENGINEERING CHO CODING WEB

> **Đánh giá lịch sử - thực chứng - phương pháp luận biện chứng - thiết kế triển khai**  
> **Workspace nghiên cứu:** `E:\DEV\Codex-web`  
> **Ngày chốt dữ liệu:** 21/08/2026  
> **Trạng thái:** Nghiên cứu và phương án triển khai; chưa tự động gỡ/cài/ghi đè skill đang vận hành  
> **Đối tượng áp dụng:** ChatWeb/Coding Web, Codex, Coding-VP/Coding MCP, hệ thống skill và control plane của dự án

---

## 0. Tuyên bố kết luận

Case study này xuất phát từ một quan sát thực tế có giá trị:

> Sau khi tắt subagent, giữ một Sol, thêm nguyên tắc chống over-engineering và tinh gọn skill, một phiên sử dụng khoảng 6 giờ chỉ tiêu thụ khoảng 4% hạn mức gói 5x, trong khi cảm nhận tốc độ làm việc tăng khoảng 2 lần.

Quan sát trên **đủ mạnh để hình thành giả thuyết kỹ thuật**, nhưng **chưa đủ để chứng minh quan hệ nhân quả**. Chưa có một thí nghiệm A/B đồng nhất về nhiệm vụ, commit, cache, độ dài ngữ cảnh, reasoning effort, số vòng kiểm chứng, thời gian chờ tool và trạng thái runtime. Vì vậy, báo cáo không kết luận giản đơn rằng “OpenAI không bóp gói” hoặc “cài nhiều skill là nguyên nhân duy nhất”.

Kết luận có độ tin cậy cao hơn là:

1. **Đơn agent là cấu hình mặc định phù hợp với Coding Web hiện tại.** Dự án chủ yếu thao tác trên một workspace có trạng thái dùng chung, một Git history, một task-state và một acceptance boundary. Việc chia nhiều agent thường nhân bản ngữ cảnh, tạo chi phí giao tiếp, làm tăng nguy cơ cạnh tranh ghi file, lệch workspace, lệch run/wave và lặp kiểm chứng.
2. **Nên giữ một Sol làm quyền điều khiển và quyền chấp nhận cuối.** Coding-VP/Coding MCP, shell, test runner, Git, file system và các verifier tất định là công cụ thực thi, không phải agent phụ.
3. **Không nên đồng nhất “một Sol” với “luôn dùng Sol Max”.** Trong telemetry hiện có của dự án, chỉ một lượt `sol_max` đã dùng 105.287 token, tương đương 39,51% tổng token được ghi nhận và nhiều hơn tổng 8 lượt `sol` cộng lại 12.995 token. Max là mức reasoning effort, không phải điều kiện bắt buộc để giữ agent ổn định.
4. **Nén ngữ cảnh đã là năng lực native của Responses API/Codex.** Codex tự động dùng `/responses/compact` khi vượt `auto_compact_limit`; không nên tạo một skill “nén suy nghĩ” để thay thế cơ chế này.
5. **Skill vẫn hữu ích, nhưng chỉ khi đúng phạm vi, đúng phiên bản và đúng thời điểm.** Nghiên cứu mới cho thấy skill chuyên biệt có thể cải thiện mạnh; đồng thời nhiều skill phần mềm không tăng pass rate, có thể tăng token tới 451%, hoặc làm giảm chất lượng khi hướng dẫn lệch phiên bản.
6. **Vấn đề không phải chỉ là số lượng skill đã cài, mà là diện tích hướng dẫn đang hoạt động.** Chi phí phát sinh từ metadata luôn hiện diện, trigger quá rộng, body dài, skill chồng lấn, policy mâu thuẫn, output tool quá lớn, vòng replan/review lặp lại và cache prefix bị phá vỡ.
7. **StateM có tư tưởng phù hợp nhưng chưa nên cài chồng vào Coding Web.** Coding Web đã có `task-state`, `task-history`, ledger, run/wave, checkpoint và acceptance gate. Cài StateM như một authority thứ hai sẽ tạo duplicate state. Nên hấp thụ các nguyên tắc tốt của StateM vào state model hiện hữu, hoặc pilot cô lập trước khi quyết định thay thế.
8. **Nên tạo một anti-over-engineering control nhỏ, nhưng về production nên hợp nhất nó vào `sol-lean-codex` thay vì giữ thêm một skill thường trực.** Skill thử nghiệm có thể tồn tại độc lập để đo; sau khi được chứng minh, các quy tắc ổn định nên được nhập vào control skill duy nhất và retire bản thử nghiệm.
9. **Mục tiêu tối ưu đúng không phải là token thấp nhất.** Mục tiêu là giảm `token trên một kết quả được chấp nhận`, giảm thời gian hoàn thành, giảm rework và giữ nguyên hoặc tăng tỷ lệ đạt acceptance oracle.
10. **Phương án đề nghị:** một Sol authority, compute thích ứng, native compaction, skill progressive disclosure, một state authority, deterministic evidence trước model review, một vòng verification tương xứng rủi ro, stop ngay khi điều kiện DONE đạt.

---

## 1. Bài toán nghiên cứu

### 1.1. Câu hỏi trung tâm

Báo cáo trả lời tám câu hỏi:

1. Quan sát “4% hạn mức sau 6 giờ và tốc độ x2” có thể được giải thích bằng cơ chế nào?
2. Codex/GPT-5.6 đã có nén ngữ cảnh native hay phải tạo skill?
3. “Tắt sạch subagent” có phù hợp với bản chất kiến trúc và lịch sử Coding Web không?
4. “Chỉ dùng Sol Max” có thực sự tiết kiệm token hơn không?
5. Skill nào trong bề mặt hiện tại nên giữ, rút gọn, hợp nhất hoặc retire?
6. StateM nên cài, tích hợp khái niệm hay không dùng?
7. Skill chống over-engineering phải chứa quy tắc gì để không tự trở thành một lớp over-engineering mới?
8. Phải đo thế nào để phân biệt cải thiện thật với cảm giác nhanh hơn do workload, cache hoặc trạng thái hệ thống khác nhau?

### 1.2. Phạm vi

Phạm vi vật chất được xem xét gồm:

- Source, docs, telemetry và state dưới `E:\DEV\Codex-web`.
- Các tài liệu lịch sử tại `docs/research`.
- `.coding-tools/performance.json`, `task-history.json`, `task-state.json` và các observation/evaluation artifacts.
- Bề mặt skill hiện được expose trong phiên ChatGPT/Coding-VP.
- Repository `blavkgokuvnn/single-agent-skills`.
- Repository và paper StateM.
- Tài liệu chính thức OpenAI về GPT-5.6, Codex agent loop, compaction, tools và skills.
- Hơn 50 nghiên cứu gần đây về skill injection, skill routing, context compression, memory, adaptive compute, early stopping, single-agent/multi-agent, verification, software-engineering agent và harness scaling.

### 1.3. Giới hạn kiểm kê

Trong repository hiện tại không phát hiện thư mục skill cục bộ chuẩn như:

- `.agents/skills`
- `.codex/skills`

Do đó, báo cáo phân biệt rõ:

- **Skill bề mặt đang thấy trong runtime hiện tại:** có thể đánh giá nội dung và độ dài.
- **Skill Codex được cài toàn cục trên máy người dùng:** chưa được coi là đã kiểm kê hoàn toàn chỉ bằng source repository này.
- **Instruction/policy nằm trong code và state của Coding Web:** không mang tên skill nhưng vẫn tiêu thụ context và tạo hành vi tương tự skill.

Không được dùng kết luận “repo không có `.codex/skills`” để suy ra “máy không có skill toàn cục”.

---

## 2. Phương pháp luận biện chứng và thang bằng chứng

### 2.1. Luận đề - phản đề - tổng hợp

**Luận đề:** càng ít agent và càng ít skill thì càng ít token, ít xung đột và nhanh hơn.

**Phản đề:** skill chuyên biệt có thể cung cấp tri thức thủ tục quan trọng; multi-agent có thể đem lại đa dạng độc lập, song song hóa hoặc kiểm tra chéo; state machine có thể ngăn drift và premature stop.

**Tổng hợp:** không tối ưu bằng cách xóa cơ học. Tối ưu bằng bốn nguyên tắc:

1. Một authority duy nhất.
2. Chỉ tải đúng tri thức cần thiết tại đúng thời điểm.
3. Chi tiêu compute theo rủi ro và độ bất định.
4. Mọi lớp bổ sung phải chứng minh lợi ích biên bằng paired evaluation.

Đây là phép tổng hợp biện chứng giữa **tối giản** và **độ tin cậy**, chứ không phải cực đoan hóa một phía.

### 2.2. Thang bằng chứng

| Mức | Loại bằng chứng | Vai trò trong kết luận |
|---|---|---|
| E0 | Cảm nhận/quan sát người dùng | Phát hiện giả thuyết, không đủ kết luận nhân quả |
| E1 | Telemetry nội bộ chưa ghép cặp | Cho biết cấu trúc chi phí, không tự chứng minh phương án tốt hơn |
| E2 | Source/log/state có thể tái kiểm tra | Chứng minh cơ chế đang tồn tại và failure mode lịch sử |
| E3 | Matched A/B cùng commit, oracle, cache stratum | Chứng minh lợi ích tương đối trong dự án |
| E4 | Replication nhiều task class, nhiều lần chạy | Đủ căn cứ promotion policy |
| E5 | Tài liệu chính thức/primary research | Giải thích cơ chế và đối chiếu ngoại bộ |

Quan sát 4%/6 giờ hiện ở E0-E1. Muốn biến thành policy production phải đạt tối thiểu E3, tốt nhất E4.

### 2.3. Nguyên tắc phản chứng

Một khuyến nghị chỉ được giữ nếu có thể nêu điều kiện làm nó sai:

- “Single agent tốt hơn” bị bác bỏ nếu multi-agent có pass rate cao hơn đáng kể sau khi tính đủ token, thời gian và lỗi hợp nhất.
- “Skill này hữu ích” bị bác bỏ nếu paired runs không tăng acceptance hoặc không giảm chi phí trên kết quả được chấp nhận.
- “StateM không cần cài” bị bác bỏ nếu pilot chứng minh recovery/phase integrity tốt hơn rõ rệt và có kế hoạch thay thế authority cũ.
- “Max không nên mặc định” bị bác bỏ nếu Max giảm tổng số lượt, tổng token và wall-clock trên cùng oracle đủ lớn để bù chi phí mỗi lượt.

---

## 3. Tái dựng lịch sử vật chất của Coding Web

### 3.1. Dự án không thất bại vì thiếu năng lực model đơn thuần

Lịch sử dự án cho thấy phần lớn chi phí và ma sát không nằm ở một lỗi “model không đủ thông minh”, mà nằm tại giao diện giữa:

- ChatWeb và Codex/Coding MCP.
- Workspace được cấp quyền và workspace thực tế.
- Runtime đang chạy và source đang sửa.
- Run state, wave state, completion report và operator acknowledgement.
- Git/index/ledger/SQLite và tiến trình nền.
- Source engineering đã xong và activation/runtime chưa đồng bộ.

Các phase P0-P3 đã lần lượt giải quyết runtime exception, measurement plumbing, rework diagnosis và control plane. Đến P4, trọng tâm chuyển sang evidence, representative evaluation, phase closure và tính nhất quán của run projection. Đây là dấu hiệu của một dự án đã vượt qua bài toán “viết được code” và bước vào bài toán khó hơn: **điều khiển, chứng minh và dừng đúng lúc**.

### 3.2. Các failure mode lịch sử liên quan trực tiếp tới over-engineering

#### A. Nhiều authority cùng mô tả một sự thật

Dự án từng phải đối chiếu:

- workspace setting;
- current workspace;
- runtime launch target;
- Git worktree;
- task-state;
- orchestration run;
- completion report;
- UI projection.

Khi mỗi lớp có một biến thể “sự thật”, hệ thống tốn vòng xác minh để tìm lớp nào stale. Đây là biểu hiện điển hình của **state duplication**.

#### B. Verification trở thành một workflow tự thân

P4 và phase closure cho thấy kiểm chứng là cần thiết, nhưng cũng xuất hiện hiện tượng:

- kiểm tra lại cùng trạng thái qua nhiều bề mặt;
- restart rồi kiểm tra schema/binding;
- kiểm tra source xong lại kiểm tra runtime;
- report đã có nhưng ACK không khả dụng;
- completion run bị chặn bởi projection defect.

Bài học không phải bỏ verification, mà là tạo **một acceptance oracle**, một bằng chứng canonical và một lần kiểm tra tương xứng rủi ro.

#### C. Điều phối tạo rework thay vì giảm rework

Task history lưu các vòng `REPLAN`, command retry, Windows file lock (`os error 32`), relaunch, stale process và command slot. Khi orchestration mở thêm lane hoặc thêm retry mà không làm rõ ownership, hệ thống chuyển từ “giải quyết việc” sang “quản lý việc quản lý”.

#### D. Workspace contamination

Lịch sử từng ghi nhận tín hiệu từ workspace HR đi vào run của Codex-web trước khi isolation được hoàn thiện. Điều này cho thấy multi-project/multi-lane không chỉ có chi phí token; nó còn có **rủi ro sai bằng chứng**.

#### E. Kết thúc phiên không rõ

Người dùng nhiều lần yêu cầu:

- không dừng đột ngột;
- phải có kết luận tổng hợp;
- phải báo trạng thái trước khi kết thúc;
- xử lý gọn tồn đọng;
- không mở lại phase đã đóng chỉ để “hoàn thiện thêm”.

Đây là yêu cầu nghiệp vụ trực tiếp cho một anti-over-engineering policy: hệ thống phải có DONE rõ, stop rule và terminal report.

### 3.3. Mâu thuẫn nền tảng của dự án

| Mâu thuẫn | Mặt tích cực | Mặt tiêu cực khi quá mức | Tổng hợp cần đạt |
|---|---|---|---|
| Quan sát sâu vs. context gọn | Phát hiện lỗi thật | Đọc quá nhiều file, lặp history | Targeted evidence + durable index |
| Nhiều agent vs. một agent | Song song/đa dạng | Coordination, duplicated context, merge conflict | Single default, escalation có gate |
| Nhiều verifier vs. một verifier | Tăng độ tin cậy | Lặp model review, tốn token | Deterministic oracle trước, LLM verifier khi cần |
| Nhiều state store vs. khả năng phục hồi | Không mất tiến độ | Authority drift | Một state authority, nhiều view read-only |
| Max reasoning vs. hiệu quả | Giải bài khó | Chi phí cao cho việc đơn giản | Adaptive reasoning effort |
| Skill đầy đủ vs. skill gọn | Bao phủ trường hợp | Trigger rộng, conflict, cache bloat | Router nhỏ + references theo nhu cầu |

### 3.4. Điểm ngoặt của case study

Quan sát “tắt subagent + tinh gọn skill + một Sol” có ý nghĩa vì nó chạm đúng điểm nghẽn lịch sử: **chi phí điều khiển và phục hồi ngữ cảnh đang tăng nhanh hơn lợi ích từ việc thêm cơ chế**.

Tuy nhiên, nếu phản ứng bằng cách cài thêm StateM, thêm hai skill, thêm verifier và ép Max cho mọi việc, dự án có thể tái tạo chính vòng xoáy mà nó muốn loại bỏ. Vì vậy, giải pháp phải là **thay thế và hợp nhất**, không phải **chồng thêm**.

---

## 4. Phân tích telemetry nội bộ

### 4.1. Snapshot từ `.coding-tools/performance.json`

| Chỉ số | Giá trị |
|---|---:|
| Tổng model calls | 14 |
| High-cost calls | 10 |
| Tỷ lệ high-cost calls | 71,43% |
| Tổng token | 266.487 |
| `codex_standard` | 5 calls / 68.908 token |
| `sol` | 8 calls / 92.292 token |
| `sol_max` | 1 call / 105.287 token |
| Coding phase | 11 calls / 166.563 token |
| Review phase | 3 calls / 99.924 token |

### 4.2. Kết luận từ số liệu

Một call `sol_max`:

- chiếm **39,51%** tổng token;
- dùng **1,1408 lần** tổng token của cả 8 call `sol` cộng lại;
- nhiều hơn 8 call `sol` cộng lại **12.995 token**.

Số liệu này không chứng minh Max luôn kém. Có thể call Max đã xử lý một nhiệm vụ khó hơn nhiều. Nhưng nó đủ để bác bỏ mệnh đề không điều kiện:

> “Chỉ dùng Sol Max đương nhiên tiết kiệm token.”

Mệnh đề đúng hơn là:

> “Chỉ dùng một Sol authority có thể giảm coordination overhead; mức reasoning phải được chọn thích ứng. Max chỉ tiết kiệm tổng chi phí nếu chất lượng của một lượt Max làm giảm đủ số lượt replan, retry và review.”

### 4.3. Review là một trung tâm chi phí lớn

3 lượt review dùng 99.924 token, trung bình khoảng 33.308 token/lượt; 11 lượt coding dùng 166.563 token, trung bình khoảng 15.142 token/lượt. Điều này không có nghĩa review là lãng phí, nhưng cho thấy:

- review bằng model có thể đắt hơn coding;
- review lặp hoặc review trên context quá lớn là đòn bẩy tối ưu quan trọng;
- deterministic test, schema validation, diff check và acceptance oracle nên chạy trước model review;
- chỉ đưa phần bất định còn lại cho Sol.

### 4.4. Công thức chi phí thực tế

Tổng token không chỉ là “model token” hay “skill token”:

```text
T_total = Σ_calls (
    base_instructions
  + active_skill_metadata
  + loaded_skill_bodies
  + task_input
  + retained_history_or_compaction
  + tool_output_returned_to_model
  + model_reasoning_and_answer
  + inter-agent_messages
  + verifier_context
)
```

Wall-clock gần đúng:

```text
L_total = inference
        + tool_execution
        + orchestration_wait
        + coordination
        + retry/replan
        + verification
        + state_recovery
        + human_interruption_cost
```

Xóa một skill body dài có thể giảm token. Nhưng nếu task-history, tool output hoặc verifier loop lớn hơn nhiều, chỉ xóa skill sẽ không giải quyết gốc rễ.

---

## 5. Đánh giá quan sát “4% sau 6 giờ, tốc độ x2”

### 5.1. Vì sao quan sát có thể đúng

Tổ hợp thay đổi có thể đồng thời tạo lợi ích:

1. **Không spawn subagent:** bỏ duplicated prompt, handoff, result merge và reviewer communication.
2. **Một thread/authority ổn định:** tăng khả năng tái sử dụng cache và giảm tái giải thích mục tiêu.
3. **Skill ít và trigger hẹp:** ít instruction conflict, ít body bị tải nhầm.
4. **Stop rule rõ:** giảm xu hướng “kiểm tra thêm cho chắc”.
5. **Scope hẹp:** ít file read, ít tool output quay lại context.
6. **Không cài thêm state engine:** giảm authority mismatch.
7. **Workload sau thay đổi có thể đơn giản hơn:** đây là biến nhiễu cần kiểm soát.
8. **Cache đã ấm:** phiên sau có thể nhanh hơn không phải do policy.
9. **Runtime vừa restart/đã sạch:** giảm stale process và file lock.
10. **Model/harness mới:** GPT-5.6 và Codex native compaction có thể tự cải thiện hiệu suất.

### 5.2. Vì sao chưa thể kết luận OpenAI “bóp” hay “không bóp” gói

Hạn mức gói và token telemetry không đồng nhất với nhau. Tỷ lệ phần trăm hiển thị có thể phụ thuộc loại tác vụ, độ phức tạp, route, cache, khung thời gian và accounting của sản phẩm. Không có matched baseline thì không thể tách:

- thay đổi của platform;
- thay đổi của model;
- thay đổi policy;
- thay đổi workload;
- thay đổi cache;
- thay đổi số tool calls;
- thay đổi cách sản phẩm tính hạn mức.

Case study nên ghi nhận phát hiện như sau:

> “Một cấu hình single-authority, lean-skill đã cho tín hiệu sử dụng hạn mức thấp và throughput cao trong một phiên quan sát. Tín hiệu phù hợp với cơ chế được tài liệu và nghiên cứu dự đoán, nhưng cần paired evaluation trước khi quy kết nguyên nhân.”

### 5.3. Giả thuyết nhân quả ưu tiên

Theo dữ liệu dự án, thứ tự đáng kiểm tra là:

1. Giảm số model calls và reviewer calls.
2. Giảm inter-agent duplicated context.
3. Giảm tool output/large artifact đưa vào context.
4. Giảm skill body nạp sai hoặc chồng lấn.
5. Tăng cache stability.
6. Giảm reasoning effort trung bình.
7. Native compaction/harness improvement.
8. Thay đổi quota/accounting của nền tảng.

Không nên mặc định nguyên nhân số 4 là duy nhất.

---

## 6. Nén ngữ cảnh: đã native hay phải tạo skill?

### 6.1. Kết luận kỹ thuật

**Không cần tạo skill để thay thế compaction native.**

Tài liệu chính thức OpenAI cho biết:

- Responses API có native compaction.
- Model tạo một compaction item ở dạng biểu diễn mã hóa, tiết kiệm token, giữ trạng thái quan trọng.
- Codex dựa vào cơ chế này cho long-running coding tasks.
- Codex tự gọi `/responses/compact` khi vượt `auto_compact_limit`.
- Compaction có thể chạy server-side hoặc qua endpoint riêng.

Do đó, skill không thể và không nên hứa “nén mà không mất suy nghĩ” theo nghĩa thay thế latent compaction của model.

### 6.2. Skill có thể làm gì quanh compaction

Một control skill tốt chỉ nên:

1. Ghi durable objective, DONE, non-goals và constraints ngoài transcript.
2. Chỉ đọc lại đúng evidence cần thiết sau compaction/recovery.
3. Dùng stable IDs cho task/run/wave/checkpoint.
4. Hạn chế tool output quay lại model.
5. Giữ system/developer/skill prefix ổn định để không phá prompt cache.
6. Tách execution state khỏi semantic truth.
7. Tạo resume anchor ngắn, không tạo một bản tóm tắt khổng lồ sau mỗi bước.
8. Không gọi `/clear` hoặc manual compact theo thói quen nếu runtime native đang xử lý tốt.

### 6.3. Mô hình ngữ cảnh đề nghị

```text
Native model context
├── Stable base instructions
├── Metadata của skill có khả năng liên quan
├── Body của đúng skill đã route
├── Current task contract
├── Recent high-value actions
└── Native compaction item khi cần

External durable context
├── Canonical task-state
├── Decision log
├── Evidence index
├── Test reports
├── Git diff/commit identity
└── Artifact paths
```

Nguyên tắc: **context là working set; filesystem/ledger là backing store**.

### 6.4. Anti-pattern cần cấm

- Nhét toàn bộ source hoặc toàn bộ docs vào prompt.
- Tóm tắt lại mọi tool call bằng model.
- Reload cả task-history để tìm một event.
- Dùng nhiều bản “current state” ở nhiều file có quyền ghi ngang nhau.
- Đưa raw logs hàng MB vào model thay vì grep/query/bounded output.
- Tạo “compression skill” dài hơn lượng context nó tiết kiệm.

---

## 7. Skill có thực sự làm tốn token không?

### 7.1. Cơ chế progressive disclosure

Trong kiến trúc skill hiện đại:

1. Tên và mô tả skill được dùng để quyết định routing.
2. Body `SKILL.md` được tải khi skill được chọn.
3. Reference/script/asset được đọc hoặc chạy khi cần.

Vì vậy, **skill đã cài không đồng nghĩa toàn bộ body luôn nằm trong prompt**. Tuy nhiên, vẫn có ba loại overhead:

- metadata của skill registry;
- lỗi routing khiến tải body không liên quan;
- body hoặc references quá dài sau khi đã route.

### 7.2. Kết quả nghiên cứu quan trọng

- `SWE-Skills-Bench` báo cáo 39/49 skill không tăng pass rate; mức tăng trung bình chỉ +1,2%; token có trường hợp tăng 451% dù pass rate không đổi; một số skill làm giảm hiệu năng do hướng dẫn lệch phiên bản.
- `SkillsBench` lại cho thấy curated skills tăng pass rate trung bình đáng kể, và các skill tập trung với tối đa ba module tốt hơn bundle lớn/toàn diện.
- `SkillsInjector`, `SkillRouter`, `SkillRAE` và `SkillRet` cùng chỉ ra rằng bài toán cốt lõi là chọn đúng, giới hạn số lượng, trình bày đúng và compile context đúng; không phải bơm toàn bộ library.

Hai nhóm kết quả không mâu thuẫn. Chúng chỉ ra quy luật:

> Skill có lợi khi là tri thức thủ tục chuyên biệt, đúng context và có verifier; skill có hại khi rộng, lỗi thời, chồng lấn hoặc được nạp tĩnh.

### 7.3. Chỉ số cần quản trị cho mỗi skill

Mỗi skill production nên có manifest đo được:

| Trường | Ý nghĩa |
|---|---|
| `trigger_scope` | Những yêu cầu cụ thể được phép kích hoạt |
| `negative_triggers` | Trường hợp không được kích hoạt |
| `entrypoint_lines` | Độ dài body lõi |
| `metadata_words` | Chi phí discovery thường trực |
| `references_loaded_p50/p95` | Lượng context phụ thực tế |
| `activation_rate` | Tần suất được route |
| `false_activation_rate` | Route sai |
| `paired_pass_delta` | Chênh lệch pass rate có/không skill |
| `paired_token_delta` | Chênh lệch token trên accepted task |
| `last_validated_version` | Phiên bản model/harness/project đã kiểm chứng |
| `expiry_review_date` | Mốc đánh giá lại |
| `owner` | Người/chức năng chịu trách nhiệm |

Skill không có acceptance benefit và không có safety necessity nên bị retire hoặc chuyển thành reference không tự kích hoạt.

---

## 8. Kiểm kê và phương án tinh gọn skill hiện thấy

> Số dòng dưới đây là snapshot entrypoint đã đọc trong runtime nghiên cứu, không phải tuyên bố rằng đây là toàn bộ skill toàn cục trên máy.

| Skill | Snapshot body | Vai trò | Chẩn đoán | Quyết định đề nghị |
|---|---:|---|---|---|
| `spreadsheets` | 127 dòng | Cơ chế Excel/CSV chung | Hữu ích, tương đối gọn; một số style rules dài | **GIỮ**, tách finance/style sâu sang reference |
| `slides` | 110 dòng | Tạo/QA PPTX | Trigger rõ, công cụ chuyên biệt | **GIỮ**, không nhập vào skill khác |
| `skill-creator` | 346 dòng | Tạo/cập nhật skill | Platform capability; dài nhưng progressive | **GIỮ**, không auto-load ngoài yêu cầu skill |
| `docx` | 334 dòng | Tạo/edit/QA DOCX | Entry point chứa nhiều design rules, lặp nhắc render/QA | **RÚT GỌN MẠNH** còn router + golden path; chuyển design rules sang reference |
| `pdfs` | 196 dòng | PDF render/edit/extract | Lặp khối design standards của DOCX; có routing tốt | **RÚT GỌN**, giữ phần PDF-specific, tham chiếu document-design chung |
| `attendance-link-reader` | 176 dòng | Chấm công 8 nhân sự | Chuyên biệt, rủi ro cao, canonical roster rõ | **GIỮ**, vì giá trị nằm ở quy tắc không được suy diễn |
| `sol-lean-codex` | policy dài | Điều phối coding/control authority | Phù hợp dự án nhưng còn topology/subagent gates và nhiều policy | **REWRITE** thành single-authority control, bỏ delegation mặc định |
| `stacorp-excel-designer` | >400 dòng | Excel STACORP cao cấp | Lặp nhiều lần cùng dashboard principles; chồng `spreadsheets` | **RÚT GỌN LỚN** thành domain overlay 80-150 dòng + references theo loại dashboard |

### 8.1. `docx`

Giữ trong entrypoint:

- trigger;
- golden path `author/edit -> render -> inspect -> fix -> deliver`;
- route tới task guides;
- hard shipping gate.

Chuyển ra reference:

- toàn bộ design standards dài;
- table aesthetics;
- form aesthetics;
- spacing checklist;
- OOXML chi tiết;
- troubleshooting.

Không cần lặp cùng nguyên tắc “render và kiểm tra” ở nhiều đoạn.

### 8.2. `pdfs`

Giữ:

- render-first;
- PDF-specific inspect/extract/edit/forms/OCR/redaction/diff;
- lựa chọn DOCX/PPTX khi phù hợp;
- two-renderer rule cho case khó.

Loại khỏi entrypoint:

- khối document aesthetics trùng DOCX;
- hướng dẫn bảng/font/spacing không đặc thù PDF.

### 8.3. `stacorp-excel-designer`

Đây là ứng viên lớn nhất cho context compression ở lớp skill. Cấu trúc production nên là:

```text
stacorp-excel-designer/
├── SKILL.md                         # router 80-150 dòng
├── references/
│   ├── theme.md
│   ├── compact-dashboard.md
│   ├── finance.md
│   ├── boq.md
│   ├── hr-payroll.md
│   ├── operations.md
│   └── layout-qa.md
├── scripts/
│   └── build_compact_dashboard_canvas.py
└── assets/
    └── stacorp-logo.png
```

`SKILL.md` chỉ quyết định loại workbook, story, module và reference cần đọc. Không nên lặp “dashboard phải gọn”, “4 KPI cards”, “alignment QA” ở nhiều section.

### 8.4. `sol-lean-codex`

Mục tiêu rewrite:

- ChatWeb Sol là control/final acceptance authority.
- Deep single lane là mặc định.
- Coding-VP/Coding MCP là deterministic execution/proof plane.
- Không tạo subagent hoặc parallel model lane theo thói quen.
- Max/Ultra chỉ sau explicit gate.
- Một task contract, một state authority, một completion report.
- Không reopen phase đã accepted nếu không có defect mới.
- Bổ sung stop rule và terminal report bắt buộc.

### 8.5. `attendance-link-reader`

Không nên rút gọn cơ học vì nhiều dòng là safety/domain invariants:

- không dùng Teams timestamp;
- không suy diễn punch;
- phân biệt `UNAVAILABLE` với thiếu chấm công;
- roster mapping cố định;
- ảnh không dùng nhận diện khuôn mặt.

Đây là ví dụ về skill dài hợp lý: nội dung giảm sai nghiệp vụ và rủi ro, không phải trang trí.

---

## 9. Đơn agent và multi-agent: kết luận có điều kiện

### 9.1. Vì sao single agent phù hợp Coding Web

Nghiên cứu `Rethinking the Value of Multi-Agent Workflow: A Strong Single Agent Baseline` cho thấy một agent mạnh có thể đạt hiệu năng của nhiều workflow multi-agent đồng nhất, đồng thời hưởng lợi từ KV-cache reuse và chi phí thấp hơn. Điều này phù hợp với Coding Web vì:

- cùng một base model;
- cùng workspace;
- cùng tool set;
- cùng mục tiêu;
- cùng mutable state;
- cùng acceptance oracle.

Nếu chỉ khác “vai trò prompt”, việc tách agent thường không tạo tri thức mới; nó tạo thêm handoff.

### 9.2. Multi-agent vẫn có miền hợp lý

Không nên biến “single agent default” thành định luật tuyệt đối. Multi-agent có thể có lợi khi:

- task thật sự độc lập và có thể ghi vào worktree riêng;
- cần model/tool dị thể;
- cần independent adversarial review cho security/safety;
- latency quan trọng hơn tổng token;
- có coordinator và merge oracle đã chứng minh;
- giá trị đa dạng lớn hơn chi phí giao tiếp.

Các nghiên cứu về beta testing, incident response và multi-agent benchmark cho thấy một số cấu hình committee/heterogeneous có thể tăng chất lượng. Nhưng đó là những topology có mục tiêu cụ thể, không phải lý do spawn agent cho mọi task.

### 9.3. Policy đề nghị

```text
DEFAULT: one Sol authority, one mutable workspace, one task contract.
TOOLS: deterministic executors and verifiers are not subagents.
NO DELEGATION: do not spawn model agents for search, review, planning or coding by default.
EXCEPTION GATE: multi-agent requires explicit user authorization plus:
  - independent scopes;
  - isolated writes;
  - merge oracle;
  - expected measurable payoff;
  - token/runtime cap.
```

### 9.4. Tắt subagent trong Coding Web phải hiểu đúng

“Tắt sạch subagent” nên có nghĩa:

- không có model lane phụ;
- không reviewer model riêng;
- không planner/coder/tester personas chạy độc lập;
- không auto-fanout.

Nó **không** có nghĩa:

- tắt test runner;
- tắt static analysis;
- tắt parallel shell commands an toàn;
- tắt web/file search;
- bỏ deterministic verification;
- bỏ human approval cho tác vụ rủi ro.

---

## 10. Sol Max: ổn định, chất lượng và chi phí

### 10.1. Phân biệt model với effort

GPT-5.6 Sol là model; `none/low/medium/high/xhigh/max` là các mức reasoning. “Sol Max” không phải một agent khác. Vì vậy có thể giữ **một Sol identity** trong khi chọn effort thích ứng.

### 10.2. Tại sao Max-only có thể làm sai mục tiêu

- Mọi task đều trả chi phí suy luận cao, kể cả rename, docs, formatter và deterministic fix.
- Max có thể tạo nhiều phương án và verification loop hơn nếu stop rule yếu.
- Max không tự sửa duplicated state, stale runtime hoặc skill conflict.
- Token tiết kiệm do bỏ subagent có thể bị ăn lại bởi reasoning dài.

### 10.3. Policy khuyến nghị

| Loại công việc | Effort mặc định | Điều kiện tăng |
|---|---|---|
| Docs, rename, cấu hình thuận nghịch | medium/high | Mâu thuẫn nguồn hoặc acceptance mơ hồ |
| Bug có repro/test rõ | high | Hai lần deterministic repair thất bại |
| Refactor nhiều boundary | xhigh | Kiến trúc bất định, migration khó rollback |
| Security, destructive, finance/live | xhigh/max | Rủi ro cao và cần acceptance sâu |
| Phase closure/strategic synthesis | xhigh/max | Bằng chứng phân tán, quyết định khó đảo ngược |

### 10.4. Nếu vẫn chọn Max-only

Có thể thiết kế một profile Max-only nhưng phải thừa nhận đây là **ưu tiên chất lượng/ổn định**, không phải mặc định tiết kiệm token. Profile phải có:

- một model call chính cho mỗi wave;
- không reviewer model phụ;
- max 5 active steps, 1 work-in-progress;
- deterministic tools trước;
- output cap;
- một verification pass;
- stop ngay khi DONE đạt;
- không sinh abstraction/skill mới ngoài scope;
- không reread history nếu state canonical đủ;
- cap model calls và tool hops.

Cần A/B profile này với `Sol xhigh single-agent`, không so với một workload khác.

---

## 11. Đánh giá repository `single-agent-skills`

Repository chỉ có hai skill lõi:

1. `anti-over-engineering`
2. `statem-single-agent`

### 11.1. Điểm tốt của `anti-over-engineering`

- Buộc ghi `OBJECTIVE`, `DONE`, `NON-GOALS`, `CONSTRAINTS`.
- Dùng smallest sufficient intervention.
- Hỏi liệu một bước thất bại có thật sự chặn DONE không.
- Giới hạn 5 active steps và 1 WIP.
- Mặc định một capable agent.
- Dừng sau một verification pass tương xứng rủi ro.
- Cho phép “no change needed”.
- Không dùng minimalism để cắt safety/correctness.

Đây là bộ nguyên tắc đúng và gọn.

### 11.2. Điểm còn thiếu nếu đưa vào Coding Web

- Chưa gắn với run/wave/workspace identity.
- Chưa định nghĩa một state authority.
- Chưa có policy về phase đã accepted.
- Chưa có budget cho model calls/tool hops/context bytes.
- Chưa phân biệt deterministic verifier và model verifier.
- Chưa có paired evaluation/promotion gate.
- Chưa có terminal report bắt buộc.
- Chưa xử lý cache stability và bounded tool output.

### 11.3. `statem-single-agent`

Skill này có một điểm rất đúng: để native compaction quản lý context và không dùng agent phụ. Tuy nhiên, nếu cài nguyên xi vào Coding Web, nó yêu cầu `.statem/`, runbook và CLI state song song với `.coding-tools` state. Đó là một authority mới.

Kết luận:

- Dùng repository này làm **nguồn thiết kế**.
- Không cài cả plugin vào production ngay.
- Port các nguyên tắc chống over-engineering vào control skill hiện có.
- Chỉ pilot StateM trong môi trường cô lập.

---

## 12. StateM: có nên cài không?

### 12.1. StateM giải quyết gì

StateM là state-aware runbook/CLI cho long-running agent:

- durable states;
- phase-local prompts;
- checked transitions;
- repair loop;
- dynamic checks;
- execution history;
- resume/compaction support;
- versioned runbook.

Paper báo cáo kết quả rất đáng chú ý trên Terminal-Bench 2.1 và nhấn mạnh harness scaling. Tuy nhiên, headline 95,3% là raw/pre-adjudication; đánh giá thận trọng phải phân biệt raw score, conservative adjustments, benchmark transfer và adaptation cost.

### 12.2. Bản đồ chồng lấn với Coding Web

| StateM | Coding Web hiện có | Nguy cơ nếu cùng ghi |
|---|---|---|
| Run ID | orchestration run ID | Hai danh tính run |
| Current node | task-state/current step | Hai current state |
| Transition history | task-history/ledger | Hai history |
| Checks | proof/acceptance gates | Check lặp/mâu thuẫn |
| Runbook | workflow/profile/policy docs | Hai workflow contract |
| `.statem/` | `.coding-tools/` | Duplicate recovery store |
| Handoff | completion report | Hai terminal report |

### 12.3. Quyết định đề nghị

**Không cài StateM vào production ở thời điểm này.**

Lý do:

1. Bài toán statefulness đã được Coding Web đầu tư sâu.
2. Failure mode lớn hiện tại là inconsistency giữa các projection; thêm projection mới làm rủi ro tăng.
3. Mục tiêu case study là tinh gọn, không chồng thêm framework.
4. Các nguyên tắc tốt có thể áp dụng mà không cần dependency mới.

### 12.4. Những gì nên hấp thụ ngay

- Phase-local context.
- Transition có gate.
- Repair quay về đúng boundary.
- History không phải semantic truth.
- Runbook versioned.
- Runtime state không commit nếu không cần lịch sử canonical.
- Stop/handoff là state thật, không phải câu cuối tùy hứng.

### 12.5. Điều kiện cho pilot StateM

Pilot chỉ được mở khi:

- dùng một task dài, cô lập;
- StateM là authority duy nhất trong pilot;
- không đồng bộ hai chiều với `task-state.json`;
- output cuối map một chiều về completion report;
- có profile đối chứng không StateM;
- đo token, wall-clock, transition failures, recovery success và acceptance;
- pilot có rollback bằng cách xóa environment/state riêng.

### 12.6. Điều kiện cho adoption

Chỉ adopt khi StateM **thay thế** một lớp hiện hữu, không bổ sung song song. Cần quyết định rõ lớp nào retire:

- task-state engine;
- workflow transition engine;
- completion/handoff projection;
- hoặc chỉ dùng StateM như dev-evaluation harness hoàn toàn tách production.

---

## 13. Tổng hợp hơn 50 nghiên cứu gần đây

### 13.1. Nhóm A - Context compression, memory và cache

| # | Nghiên cứu | Kết luận liên quan | Hàm ý cho Coding Web |
|---:|---|---|---|
| 1 | Memex(RL), arXiv:2603.04257 | Index full-fidelity history ngoài working context | Lưu evidence có index, chỉ dereference khi cần |
| 2 | MAGE / Memory as Execution State, arXiv:2606.06090 | State tree giảm token và cô lập nhánh lỗi | Giữ active path, không trộn failed branch vào current state |
| 3 | Adaptive Context Compression, arXiv:2603.29193 | Importance-aware compression cho long-running interactions | Nén theo giá trị quyết định, không theo tuổi đơn thuần |
| 4 | Active Context Compression, arXiv:2601.07190 | Agent tự quản memory budget | Cho phép query targeted evidence, không reload toàn bộ |
| 5 | 500xCompressor, arXiv:2408.03094 | Prompt compression có thể rất mạnh nhưng phụ thuộc task | Không áp dụng compression ratio cứng cho code/evidence |
| 6 | ACON, arXiv:2510.00615 | Tối ưu context cho long-horizon agent | Đo task success cùng token, không chỉ độ ngắn |
| 7 | Empirical Prompt Compression, arXiv:2505.00019 | Compression có trade-off khác nhau theo task/model | Cần benchmark nội bộ trước khi cắt instructions |
| 8 | Dynamic Compressing Prompts, arXiv:2504.11004 | Budget động tốt hơn một mức nén cố định | Context budget thích ứng theo phase/risk |
| 9 | Don’t Break the Cache, arXiv:2601.06007 | Prompt cache nhạy với prefix thay đổi | Giữ base instructions và skill metadata ổn định |
| 10 | MemGym, arXiv:2605.20833 | Memory phải được đo trên long-horizon environment | Tạo recovery benchmark, không chỉ test một turn |
| 11 | Long-Term Memory Security Survey, arXiv:2604.16548 | Memory tạo attack/governance surface | State/evidence cần provenance, retention và trust boundary |
| 12 | OpenAI native compaction | Compaction item giữ latent understanding | Không tự xây skill thay thế compaction native |

### 13.2. Nhóm B - Adaptive compute, early stopping và overthinking

| # | Nghiên cứu | Kết luận liên quan | Hàm ý |
|---:|---|---|---|
| 13 | Adaptive Test-Time Compute via Constrained Policy Optimization, arXiv:2604.14853 | Phân bổ compute theo độ khó | Không dùng Max đồng loạt |
| 14 | Reasoning on a Budget survey, arXiv:2507.02076 | Adaptive/controllable TTC là hướng chính | Effort là policy variable |
| 15 | Every Rollout Counts, arXiv:2506.15707 | Phân bổ rollout tối ưu quan trọng hơn tăng đều | Chỉ mở thêm attempt khi expected value dương |
| 16 | Learning When to Plan, arXiv:2509.03581 | Không phải bước nào cũng cần planning sâu | Bỏ plan ceremony cho task nhỏ |
| 17 | A*-Thought, arXiv:2505.24550 | Nén reasoning hai chiều cho low-resource | Giữ intermediate state ngắn và có cấu trúc |
| 18 | Efficient Reasoning Survey, arXiv:2503.21614 | Nhiều kỹ thuật giảm reasoning dư thừa | Tách quality gate khỏi verbosity |
| 19 | Efficient Inference Survey, arXiv:2503.23077 | Hiệu quả là bài toán hệ thống, không chỉ model | Tối ưu tool/harness/cache cùng model |
| 20 | Missing Premise Exacerbates Overthinking, arXiv:2504.06514 | Thiếu premise có thể làm model suy luận vòng | Khi thiếu dữ liệu quyết định, tìm đúng evidence thay vì nghĩ lâu hơn |
| 21 | Entropy After `</Think>` Early Exit, arXiv:2509.26522 | Có tín hiệu cho early exit | Dùng confidence/acceptance signal để stop |
| 22 | Dynamic Early Exit in Reasoning Models, arXiv:2504.15895 | Exit động giảm compute | Không đặt budget một cỡ cho mọi task |
| 23 | Conformal Thinking, arXiv:2602.03814 | Risk-controlled upper/lower stopping thresholds | Stop khi đủ tin cậy hoặc khi tiếp tục ít khả năng cứu task |
| 24 | Program-of-Layers, arXiv:2606.06574 | Nhiều input đạt kết quả với path ngắn hơn | Bằng chứng kiến trúc cho adaptive depth, không phải lý do tạo skill nén |
| 25 | Test-Time Depth Adaptation, arXiv:2507.07996 | Skip/loop layer có thể đổi accuracy-compute | Củng cố nguyên tắc compute theo input |
| 26 | Full-bandwidth Transformer, arXiv:2608.08888 | Latent feedback cho trace ngắn hơn ở cùng/chất lượng tốt hơn | Đây là cải tiến kiến trúc model, không thể tái tạo bằng prompt skill |

### 13.3. Nhóm C - Single-agent, multi-agent và coordination

| # | Nghiên cứu | Kết luận liên quan | Hàm ý |
|---:|---|---|---|
| 27 | OneFlow / Strong Single Agent Baseline, arXiv:2601.12307 | Single agent có thể khớp homogeneous workflows với KV reuse | Single Sol là baseline bắt buộc |
| 28 | MultiAgentBench, arXiv:2503.01935 | Topology/protocol ảnh hưởng collaboration | Multi-agent cần thiết kế và benchmark, không auto-spawn |
| 29 | Multi-Agent Committees for Beta Testing, arXiv:2512.21352 | Committee dị thể có thể tăng bug detection | Giữ làm ngoại lệ cho testing độc lập |
| 30 | Multi-Agent Incident Response, arXiv:2511.15755 | Một số workflow có lợi lớn từ role decomposition | Kết quả domain-specific, cần xem threats to validity |
| 31 | CommCP, arXiv:2602.06038 | Có thể tối ưu communication với uncertainty control | Coordination là chi phí phải quản trị |
| 32 | Coordination as an Architectural Layer, arXiv:2605.03310 | Coordination cần là lớp thiết kế thật | Nếu không có lớp này, không nên dùng multi-agent |
| 33 | More Agents Improve Math..., arXiv:2511.07112 | Nhiều agent có diminishing returns và robustness gap | Không lấy số agent làm proxy cho chất lượng |
| 34 | MasRouter, arXiv:2502.11133 | Routing đúng topology/model quan trọng | Không cố định multi-agent cho mọi task |
| 35 | OpenAI GPT-5.6 builder guidance | Multi-agent “where appropriate”, có steering chống spawn không cần thiết | Single default phù hợp hướng platform |

### 13.4. Nhóm D - Verification và test-time scaling

| # | Nghiên cứu | Kết luận liên quan | Hàm ý |
|---:|---|---|---|
| 36 | LLM-as-a-Verifier, arXiv:2607.05391 | Fine-grained probabilistic verifier tăng khả năng chọn candidate | Chỉ dùng khi deterministic oracle không đủ |
| 37 | Scaling Agentic Verifier for Competitive Coding, arXiv:2602.04254 | Verifier có thể là trục scaling | Verifier cũng cần token budget và stop rule |
| 38 | Scaling Test-Time Compute for Agentic Coding, arXiv:2604.16529 | Sampling/selection tăng coding performance | Không áp dụng nếu task có test đủ mạnh và candidate đầu đã pass |
| 39 | ThinkBooster, arXiv:2606.06915 | Framework thống nhất TTC | Compute policy nên tách khỏi task logic |
| 40 | Scaling Test-time Compute for LLM Agents, arXiv:2506.12928 | Agent benefit phụ thuộc cách phân bổ compute | Không tăng attempt mù quáng |

### 13.5. Nhóm E - Software-engineering agents và harness

| # | Nghiên cứu | Kết luận liên quan | Hàm ý |
|---:|---|---|---|
| 41 | StateM, arXiv:2608.15089 | Harness/state/runbook có thể tạo gain lớn | Tối ưu control plane là đòn bẩy thật |
| 42 | SWE-Dev, arXiv:2506.07636 | Training và inference scaling cho SWE agents | Model và harness phải đánh giá cùng nhau |
| 43 | Skywork-SWE, arXiv:2506.19290 | Data scaling laws cho SWE | Chất lượng data/task matters hơn instruction volume |
| 44 | StructAgent, arXiv:2607.11388 | Causal structure cho long-horizon agents | State phải phản ánh dependency, không chỉ timeline |
| 45 | TUA-Bench, arXiv:2606.28480 | Terminal-use cần benchmark thực tế | Dùng task thật của Coding Web làm representative set |
| 46 | SWE-Exp, arXiv:2507.23361 | Experience-driven issue resolution | Reuse evidence/experience có chọn lọc |
| 47 | Efficient Agents, arXiv:2508.02694 | Agent effectiveness và cost phải cùng tối ưu | KPI là accepted outcome per cost |

### 13.6. Nhóm F - Skill effectiveness, retrieval và compilation

| # | Nghiên cứu | Kết luận liên quan | Hàm ý |
|---:|---|---|---|
| 48 | SWE-Skills-Bench, arXiv:2603.15401 | Nhiều skill không tăng pass; overhead có thể rất lớn | Mỗi skill phải có paired evidence |
| 49 | SkillsBench, arXiv:2602.12670 | Curated, focused skill tăng pass đáng kể | Không xóa skill chuyên biệt tốt |
| 50 | SkillRouter, arXiv:2603.22455 | Routing library lớn là bài toán khó | Mô tả/metadata phải giàu tín hiệu và ngắn |
| 51 | SkillsInjector, arXiv:2605.29794 | Số skill và cách render context phải thích ứng | Không dùng fixed injection budget |
| 52 | SkillRAE, arXiv:2605.10114 | Compile đúng subunit tốt hơn prompt addition thô | Chỉ nạp đoạn hướng dẫn cần thiết |
| 53 | SkillRet, arXiv:2605.05726 | Retrieval trên library thực tế còn khó | Library càng lớn càng cần taxonomy/test |

### 13.7. Tổng hợp từ corpus

Corpus không ủng hộ khẩu hiệu “xóa hết skill”. Corpus ủng hộ:

- focused skill;
- adaptive selection;
- compact compilation;
- deterministic verifier;
- adaptive compute;
- durable state có một authority;
- single-agent baseline mạnh;
- multi-agent chỉ khi topology có lợi ích riêng;
- paired evaluation trên task thật.

---

## 14. Thiết kế anti-over-engineering control cho Coding Web

### 14.1. Không để skill chống over-engineering tự trở thành over-engineering

Skill production phải:

- entrypoint ngắn;
- không chứa 50-paper literature review;
- không thêm state database;
- không thêm agent;
- không bắt lập kế hoạch dài cho task nhỏ;
- không bắt chạy exhaustive verification;
- không tạo ceremony mới.

Nghiên cứu nằm trong tài liệu này; runtime skill chỉ giữ các control có tác dụng quyết định.

### 14.2. Tên và lifecycle đề nghị

**Tên pilot:** `anti-overengineering-sol`  
**Mục đích production:** sau paired validation, merge các rule ổn định vào `sol-lean-codex`, sau đó retire pilot để không tăng skill count dài hạn.

### 14.3. Candidate `SKILL.md`

```markdown
---
name: anti-overengineering-sol
description: Keep significant coding, debugging, research, refactoring, and long-running repository work scoped, single-agent, evidence-driven, and stoppable. Use when a task has multiple material steps, broad solution space, repeated verification risk, architectural temptation, or long runtime. Do not use for tiny edits, direct factual answers, or emergency containment where the minimal safe action is already known.
---

# Anti-overengineering for Sol

## Establish the task contract

Before material work, record only:

- OBJECTIVE: one accepted outcome.
- DONE: observable acceptance condition.
- NON-GOALS: adjacent work excluded from this run.
- CONSTRAINTS: safety, authority, compatibility, workspace, files, and rollback.

Do not expand scope without a new defect, changed requirement, or failed acceptance condition.

## Keep one authority

Use one Sol authority end to end. Deterministic tools, searches, tests, linters, and file operations are not agents. Do not spawn planner, coder, reviewer, researcher, or verifier agents unless the user explicitly authorizes a separately measured multi-agent experiment.

Use one canonical workspace, one task identity, one mutable state authority, and one completion report. Treat other projections as read-only views. Do not add a new state store when an existing authority can represent the task.

## Choose the smallest sufficient intervention

Try in order:

1. No change or direct answer.
2. Existing configuration or workflow.
3. Narrow local edit.
4. Small reusable helper.
5. New abstraction, subsystem, dependency, or skill.

Move down only when evidence shows the earlier level cannot satisfy DONE.

Before each proposed step ask: If this step fails, can DONE still pass? If yes, park it in one line and continue without it.

Keep at most five active steps and one step in progress.

## Control context and compute

Prefer targeted reads, indexed evidence, bounded command output, and stable instruction prefixes. Let the host's native compaction manage conversation context. Do not manually summarize every action or reload full histories when canonical state and targeted evidence are available.

Use the lowest reasoning effort that safely satisfies DONE. Escalate to max only for a concrete ambiguity, high-risk boundary, failed deterministic repair, or final decision whose error cost justifies the additional compute. Never use max merely because the task is long.

## Block speculative engineering

Do not add an abstraction for one hypothetical future use. Require at least two concrete current callers or three repeated real uses before creating a generalized helper or new skill, unless safety or compatibility requires it now.

Do not install a new framework that duplicates an existing state, workflow, routing, verification, or persistence authority. Adoption must replace or measurably simplify an existing layer.

Do not reopen an accepted phase without a new reproducible defect, changed requirement, or invalidated acceptance oracle.

## Verify once, proportionally, then stop

Run deterministic acceptance checks first. Use model review only for residual judgment that tests cannot decide.

When DONE first passes, run one verification pass proportional to risk:

- Reversible docs/config: targeted validation and negative scope scan.
- Shared code: affected tests plus integration boundary.
- Destructive, security, money, or live work: all mandatory safety, recovery, and authorization checks.

Repeat verification only when the first pass is ambiguous, contradicts other evidence, or exposes a concrete defect.

Stop after DONE and the proportional verification pass succeed. Return a terminal report containing outcome, evidence, changed files, residual risk, and explicitly parked non-goals.

## Preserve correctness

Minimalism never removes correctness, safety, privacy, authorization, data-loss protection, required evidence, or rollback capability. "No change needed" is valid when the current system already satisfies DONE.
```

### 14.4. Điểm khác với bản upstream

Bản đề nghị bổ sung:

- one canonical workspace;
- one state authority;
- phase closure rule;
- native compaction rule;
- adaptive effort/Max gate;
- abstraction/new-skill admission gate;
- deterministic-first verification;
- terminal report;
- replacement-not-layering rule cho framework mới.

### 14.5. Không nhét các chi tiết sau vào skill

- danh sách 53 paper;
- số liệu telemetry lịch sử;
- hướng dẫn StateM CLI;
- toàn bộ phase architecture;
- giải thích dài về phương pháp luận;
- bảng A/B.

Các nội dung đó thuộc docs/research hoặc reference được đọc khi audit, không thuộc runtime control.

---

## 15. Kiến trúc đích cho Coding Web

### 15.1. Sơ đồ authority

```text
User / Operator
       |
       v
ChatWeb GPT-5.6 Sol
(control + reasoning + final acceptance)
       |
       v
Coding-VP / Coding MCP
(deterministic execution + proof plane)
       |
       +--> filesystem / source / docs
       +--> tests / build / lint / verifier
       +--> Git / diff / commit identity
       +--> canonical task-state + ledger
       |
       v
One completion report
```

Không có subagent model mặc định.

### 15.2. Skill layers

```text
Layer 0: platform-native behavior
- native compaction
- tool calling
- prompt caching

Layer 1: one control skill
- sol-lean-codex, rewritten for single authority
- anti-overengineering rules merged here after validation

Layer 2: artifact/mechanism skills
- spreadsheets
- slides
- docx
- pdfs

Layer 3: domain overlays
- stacorp-excel-designer
- attendance-link-reader

Layer 4: on-demand references/scripts/assets
- loaded only for the current task branch
```

### 15.3. Một state authority

Canonical state tối thiểu:

```text
task_id
workspace_id/root_fingerprint
objective
done_condition
non_goals
constraints
current_phase
current_step
run_id/wave_id when material
accepted_evidence[]
changed_files[]
parked_items[]
terminal_status
```

Mọi UI/report khác phải là projection read-only hoặc update qua một transaction owner duy nhất.

### 15.4. Một acceptance oracle

Acceptance oracle phải được định nghĩa trước mutation khi có thể:

- test command;
- expected UI behavior;
- schema validation;
- exact document path/content requirement;
- benchmark result;
- operator approval cho judgment-only case.

Không được thay oracle giữa chừng chỉ để làm run “pass”.

---

## 16. Kế hoạch triển khai theo smallest sufficient intervention

### Phase 0 - Chốt baseline, không sửa skill

**Mục tiêu:** có số đo đối chứng trước khi thay đổi.

Thu thập trên một tập nhỏ task đại diện:

- token input/output/reasoning nếu có;
- model calls;
- tool hops;
- wall-clock;
- skill activated;
- context bytes/body lines loaded;
- replan count;
- verifier count;
- pass/fail acceptance;
- files touched;
- state divergence/recovery event.

**DONE:** tối thiểu 8 matched tasks có dữ liệu đủ, gồm docs, bugfix, refactor và research.

### Phase 1 - Kiểm kê toàn bộ skill thật trên máy/runtime

Tạo manifest, không xóa ngay:

```text
skill_name
location
version/commit
trigger description
entrypoint lines/bytes
references/scripts/assets
last used
last validated model/harness
overlap candidates
paired evidence
safety necessity
```

Phân loại:

- KEEP;
- NARROW_TRIGGER;
- SPLIT_TO_REFERENCES;
- MERGE;
- RETIRE;
- QUARANTINE_VERSION_MISMATCH.

**DONE:** 100% skill có owner và quyết định sơ bộ.

### Phase 2 - Rút gọn entrypoint, chưa thay logic

Ưu tiên:

1. `stacorp-excel-designer`.
2. `docx`.
3. `pdfs`.
4. `sol-lean-codex`.

Mục tiêu nội bộ đề nghị:

- control skill: 80-150 dòng;
- artifact router: 80-180 dòng;
- metadata description: đủ trigger nhưng không viết như tài liệu;
- reference một cấp từ `SKILL.md`;
- không lặp cùng rule ở nhiều file.

**DONE:** render/test/behavior không giảm; body loaded p50 giảm; trigger false positive không tăng.

### Phase 3 - Single-Sol policy

- Disable auto-fanout/subagent dispatch.
- Giữ deterministic parallel commands nếu an toàn.
- Một task contract.
- Một completion report.
- Bổ sung anti-overengineering pilot.
- Reasoning effort mặc định `high/xhigh`; Max gate explicit.

**DONE:** không có model subagent trong profile mặc định; long-run vẫn recovery được.

### Phase 4 - State simplification

- Lập data-flow map cho `task-state`, history, ledger, run/wave và UI projection.
- Chọn canonical writer.
- Loại hoặc chuyển read-only các projection trùng.
- Hấp thụ phase-local context, checked transition, repair boundary từ StateM.

**DONE:** không còn hai current-state có quyền ghi ngang nhau; run/completion identity nhất quán.

### Phase 5 - Paired evaluation

So sánh bốn policy để tách nguyên nhân:

| Policy | Agent topology | Skill surface | Effort |
|---|---|---|---|
| A | Hiện tại | Hiện tại | Hiện tại |
| B | Single Sol | Hiện tại | xhigh |
| C | Single Sol | Lean skills | xhigh |
| D | Single Sol | Lean skills | max |

So sánh A-B để đo topology; B-C để đo skill; C-D để đo Max.

**DONE:** có kết luận theo task class, không chỉ trung bình tổng.

### Phase 6 - Promotion/retirement

Một skill/policy được promote khi:

- acceptance không giảm;
- token trên accepted task giảm có ý nghĩa, hoặc acceptance tăng đủ bù chi phí;
- recovery và safety không xấu đi;
- không tăng state divergence;
- kết quả lặp lại ở representative tasks.

Skill retire phải có rollback và changelog.

---

## 17. Thiết kế thí nghiệm A/B tối thiểu nhưng đủ tin cậy

### 17.1. Hai tầng, tránh over-engineer benchmark

#### Tầng 1 - Smoke paired study

- 8 task.
- 4 task class.
- Cùng source commit.
- Cùng acceptance oracle.
- AB/BA order để giảm order effect.
- Tách cache `cold` và `warm`.
- Dừng nếu policy mới fail safety hoặc acceptance rõ ràng.

#### Tầng 2 - Representative promotion study

Chỉ chạy nếu tầng 1 có tín hiệu:

- 20-30 task thật.
- Có replicate cho task biến động.
- Bao phủ docs, UI/code, runtime diagnosis, refactor, phase closure.
- Ghi provenance `representative`; synthetic/benchmark không dùng làm bằng chứng promotion duy nhất.

### 17.2. Primary metrics

```text
accepted_task_rate
input_tokens_per_accepted_task
output_tokens_per_accepted_task
reasoning_tokens_per_accepted_task
wall_clock_per_accepted_task
model_calls_per_accepted_task
replan_count
verification_passes
state_divergence_incidents
human_interventions
```

### 17.3. Guardrail metrics

- regression count sau 24-48 giờ;
- missed requirement;
- safety/authorization violation;
- wrong workspace event;
- uncommitted/incorrect file mutation;
- terminal report completeness;
- phase reopened without defect.

### 17.4. Không dùng metric dễ bị game

Không promote chỉ vì:

- số token thấp nhưng task fail;
- thời gian nhanh nhưng bỏ verification bắt buộc;
- ít file touched nhưng workaround không đúng;
- câu trả lời ngắn nhưng không có evidence;
- 100% pass trên synthetic set không đại diện.

### 17.5. KPI tổng hợp đề nghị

```text
Accepted Outcome Efficiency =
    accepted_tasks
    / (normalized_token_cost + normalized_wall_clock + rework_penalty)
```

Không cần cố định một trọng số production ngay. Trước hết hiển thị ba thành phần riêng để tránh che giấu trade-off.

---

## 18. Quy tắc quản trị skill sau tối ưu

### 18.1. Admission gate cho skill mới

Chỉ tạo/cài skill mới khi ít nhất một điều kiện đúng:

1. Workflow đã lặp ít nhất ba lần và mỗi lần phải tái khám phá thủ tục.
2. Có safety/domain invariant khó nhớ nhưng cần thực thi nhất quán.
3. Có script/reference/asset tái sử dụng làm giảm lỗi rõ rệt.
4. Paired pilot cho thấy gain.
5. Skill mới thay thế hoặc hợp nhất ít nhất một instruction surface cũ.

### 18.2. Không tạo skill cho

- một task duy nhất;
- kiến thức phổ thông model đã biết;
- một checklist dài nhưng không có trigger riêng;
- việc native platform đã xử lý, như compaction;
- workaround cho bug tạm thời không có expiry;
- hướng dẫn trùng với skill khác.

### 18.3. Expiry và revalidation

- Review skill khi đổi major model/harness.
- Quarantine nếu project/tool version lệch.
- Retire nếu 90 ngày không dùng và không có safety necessity.
- Re-run paired tests khi body thay đổi lớn.
- Ghi `validated_against` và `last_reviewed` ngoài frontmatter nếu platform cho phép qua manifest riêng; không làm frontmatter trigger phình to.

### 18.4. Similarity/overlap audit

Tìm các nhóm rule trùng:

- render/verify artifacts;
- dashboard aesthetics;
- file path/output rules;
- single-agent authority;
- final report/closure;
- web/source citations;
- safety/authorization.

Một rule chung chỉ nên có một canonical source; skill khác tham chiếu hoặc chỉ giữ rule đặc thù.

---

## 19. Risk register

| Rủi ro | Cơ chế | Mitigation |
|---|---|---|
| Under-engineering | Stop quá sớm, bỏ edge case | Risk-proportional verification và safety exceptions |
| Xóa skill hữu ích | Tinh gọn cơ học | Paired evaluation và rollback |
| Trigger false negative | Description quá hẹp | Query set test cho routing |
| Single-agent bottleneck | Task thật sự song song/heterogeneous | Explicit exception gate |
| Max cost spike | Max mặc định mọi task | Adaptive effort và cap calls |
| Duplicate state | Cài StateM chồng `.coding-tools` | Replacement-only policy |
| Benchmark overfit | Tối ưu cho synthetic test | Representative provenance |
| Cache confounding | Prefix/order khác nhau | Cold/warm strata, AB/BA |
| Quality hidden by average | Một task class giảm mạnh | Báo cáo stratified metrics |
| Skill version drift | Hướng dẫn cũ | `validated_against`, expiry, quarantine |
| Verification bloat | LLM verifier lặp | Deterministic-first, one-pass rule |
| Loss of audit history | Xóa state/log quá mức | Retention policy, canonical evidence index |

---

## 20. Quyết định từng yêu cầu ban đầu

| Yêu cầu | Kết luận | Mức tin cậy |
|---|---|---|
| Tắt sạch subagent | **Đồng ý làm default** cho Coding Web | Cao |
| Chỉ dùng một Sol | **Đồng ý về authority** | Cao |
| Chỉ dùng Sol Max | **Không đồng ý như policy tiết kiệm mặc định**; chỉ Max theo gate hoặc chạy profile đối chứng | Cao từ telemetry nội bộ, cần paired test cho task class |
| Tạo skill chống over-engineering | **Đồng ý**, pilot nhỏ rồi merge vào `sol-lean-codex` | Cao |
| Xóa skill chia việc | **Đồng ý retire/disable delegation skill** nếu không có use case đã đo | Trung bình-cao |
| Tối ưu toàn bộ skill | **Đồng ý**, theo audit/paired evaluation, không xóa hàng loạt | Cao |
| Tạo skill nén ngữ cảnh | **Không cần**; dùng native compaction | Rất cao |
| Cài StateM ngay | **Không**; hấp thụ nguyên tắc hoặc pilot cô lập | Cao với kiến trúc hiện tại |
| 4%/6h chứng minh không bị bóp gói | **Chưa chứng minh**; là tín hiệu tốt | Cao |
| Đọc khoảng 50 nghiên cứu | Đã tổng hợp 53 nguồn nghiên cứu/chính thức liên quan | Cao |

---

## 21. Phương án chốt đề nghị cho dự án

### 21.1. Chính sách production mục tiêu

> **Single Sol Authority / Lean Skill Surface / Native Compaction / One State Authority / Adaptive Compute / Deterministic Evidence / Stop-on-Done**

Cụ thể:

1. Tắt auto subagent và model reviewer phụ trong profile mặc định.
2. Giữ ChatWeb GPT-5.6 Sol là authority cuối.
3. Dùng Coding-VP/Coding MCP làm execution/proof plane.
4. Không ép Max cho mọi task; Max có explicit gate.
5. Rút gọn `sol-lean-codex`, `stacorp-excel-designer`, `docx`, `pdfs`.
6. Giữ các skill chuyên biệt có safety/domain value.
7. Không cài compression skill.
8. Không cài StateM production ở wave đầu.
9. Pilot anti-overengineering skill, sau đó merge và retire pilot.
10. Dùng paired evaluation trước khi tuyên bố giảm token hoặc tăng tốc.

### 21.2. Thứ tự triển khai nhỏ nhất

1. Baseline 8 task.
2. Rewrite `sol-lean-codex` thành single-authority.
3. Thêm anti-overengineering pilot.
4. Disable subagent dispatch.
5. A/B single vs current.
6. Rút gọn hai skill dài nhất.
7. A/B lean skills.
8. So sánh xhigh vs Max.
9. Sau cùng mới xét StateM pilot.

Thứ tự này cô lập biến và tránh thay 5 thứ cùng lúc rồi không biết nguyên nhân.

### 21.3. Điều không nên làm

- Không xóa toàn bộ skill trong một commit.
- Không cài `single-agent-skills` và StateM cùng lúc rồi đo.
- Không đổi model, effort, skill và topology trong cùng một cặp A/B.
- Không lấy quota percentage làm duy nhất metric.
- Không tuyên bố x2 nếu workload không matched.
- Không thêm dashboard/telemetry mới trước khi dùng được telemetry hiện có.
- Không mở một phase kiến trúc mới chỉ để tối ưu vài kilobyte instruction.

---

## 22. Acceptance criteria cho wave triển khai tương lai

Wave được coi là hoàn thành khi:

- [ ] Profile mặc định không spawn model subagent.
- [ ] Một Sol authority xuyên suốt task.
- [ ] Có một canonical task-state writer.
- [ ] Native compaction không bị thay bằng manual-summary loop.
- [ ] Max chỉ dùng sau explicit gate hoặc trong profile thí nghiệm.
- [ ] `sol-lean-codex` có anti-overengineering rules và stop rule.
- [ ] Skill body dài đã chuyển phần chi tiết sang references theo nhu cầu.
- [ ] Không giảm acceptance rate trên paired study.
- [ ] Token trên accepted task giảm hoặc quality gain đủ bù chi phí.
- [ ] Không tăng wrong-workspace/state-divergence incident.
- [ ] Terminal report luôn có outcome, evidence, changed files, residual risk và parked items.
- [ ] Có rollback manifest cho mọi skill bị retire/merge.

---

## 23. Kết luận cuối

Case study cho thấy trực giác của người dùng chạm đúng một vấn đề thật: trong hệ thống agentic coding trưởng thành, năng lực model không còn là biến duy nhất. **Instruction surface, topology agent, state authority, verification policy, cache stability và stop behavior** có thể quyết định hiệu quả nhiều không kém việc đổi model.

Lịch sử Coding Web chứng minh rằng độ phức tạp bổ sung từng cần thiết để vượt qua P0-P3, nhưng khi hệ thống bước vào P4/phase closure, cùng loại cơ chế có thể trở thành chi phí nếu tiếp tục nhân bản. Phương pháp đúng không phải phủ định toàn bộ kiến trúc đã xây, mà là chuyển từ giai đoạn **mở rộng năng lực** sang giai đoạn **hợp nhất authority và tối ưu lợi ích biên**.

Cấu hình hợp lý nhất hiện nay là:

- **một Sol authority**;
- **không subagent mặc định**;
- **compute thích ứng thay vì Max đồng loạt**;
- **native compaction**;
- **skill chuyên biệt, trigger hẹp, entrypoint gọn**;
- **một state authority**;
- **deterministic verification trước model verification**;
- **một vòng kiểm chứng tương xứng rủi ro**;
- **stop ngay khi DONE đạt**.

StateM là bằng chứng quan trọng rằng harness scaling có giá trị, nhưng bài học đúng cho Coding Web không phải “cài thêm StateM”. Bài học là: **đưa trạng thái ra khỏi trí nhớ tạm, làm transition có kiểm chứng, giữ context theo phase và dừng có chủ đích**. Những điều này nên được hợp nhất vào nền tảng hiện hữu trước khi cân nhắc dependency mới.

Quan sát 4%/6 giờ và x2 tốc độ nên được giữ như một case discovery có giá trị. Bước trưởng thành tiếp theo là biến nó thành thí nghiệm ghép cặp, rồi chỉ promotion những thay đổi thực sự giảm chi phí trên kết quả được chấp nhận. Khi đó, kết luận không còn là một lời truyền miệng về việc “cài linh tinh”, mà trở thành một policy kỹ thuật có thể tái lập, đo lường và quản trị.

---

## 24. Nguồn nội bộ đã đối chiếu

- `AGENTS.md`
- `README.md`
- `package.json`
- `opencode.json`
- `docs/PRODUCTION_CLOSURE_ROLLOUT.md`
- `docs/research/CODING_WEB_MASTER_ENGINEERING_STRATEGY_AND_HISTORY.md`
- `docs/research/260817_CURRENT_LEDGER_BASELINE.md`
- `docs/research/260817_PROJECT_REAL_STATE_SCIENTIFIC_EVIDENCE_AND_FULL_EXECUTION_PLAN.md`
- `docs/research/260816_ACCEPTED_ENGINEERING_OUTCOME_SOLUTION_ECONOMICS_METHODOLOGY_AND_IMPLEMENTATION_PLAN.md`
- `docs/research/260816_CHATWEB_SERVER_FIRST_COMPUTE_ORCHESTRATION_RESEARCH.md`
- `docs/research/260814_TOOLS_CODEX_WEB_OPTIMAL_PERFORMANCE_COST_UPGRADE_METHODOLOGY.md`
- `docs/research/260815_TOOLS_CODEX_WEB_ACTIVITY_COORDINATION_PERFORMANCE_COST.md`
- `docs/research/260818_CODING_WEB_NGHIEN_CUU_KHOA_HOC_TOAN_DIEN_AI_AGENT_VA_LO_TRINH.md`
- `docs/research/260814_REAL_CODEX_BENCHMARK_AND_TOKEN_USAGE.md`
- `docs/research/260814_EXECUTION_HUB_LIVE_BENCHMARK_HIEU_SUAT_CHI_PHI.md`
- `.coding-tools/performance.json`
- `.coding-tools/task-history.json`
- `.coding-tools/task-state.json`
- `.coding-tools/evaluation/chatweb-host-observations.jsonl`
- `.coding-tools/evaluation/chatweb-host-turn-pending.json`

---

## 25. Tài liệu chính thức và repositories

1. OpenAI, *Builder's guide to GPT-5.6*: https://openai.com/index/builders-guide-to-gpt-5-6/
2. OpenAI, *From model to agent: Equipping the Responses API with a computer environment*: https://openai.com/index/equip-responses-api-computer-environment/
3. OpenAI, *Unrolling the Codex agent loop*: https://openai.com/index/unrolling-the-codex-agent-loop/
4. OpenAI model documentation: https://developers.openai.com/api/docs/models
5. Single-Agent Skills: https://github.com/blavkgokuvnn/single-agent-skills
6. StateM: https://github.com/henryqin1997/statem
7. StateM project page: https://henryqin1997.github.io/statem/
8. LLM-as-a-Verifier: https://llm-as-a-verifier.com/

---

## 26. Danh mục nghiên cứu

1. https://arxiv.org/abs/2603.04257
2. https://arxiv.org/abs/2606.06090
3. https://arxiv.org/abs/2603.29193
4. https://arxiv.org/abs/2601.07190
5. https://arxiv.org/abs/2408.03094
6. https://arxiv.org/abs/2510.00615
7. https://arxiv.org/abs/2505.00019
8. https://arxiv.org/abs/2504.11004
9. https://arxiv.org/abs/2601.06007
10. https://arxiv.org/abs/2605.20833
11. https://arxiv.org/abs/2604.16548
12. https://arxiv.org/abs/2604.14853
13. https://arxiv.org/abs/2507.02076
14. https://arxiv.org/abs/2506.15707
15. https://arxiv.org/abs/2509.03581
16. https://arxiv.org/abs/2505.24550
17. https://arxiv.org/abs/2503.21614
18. https://arxiv.org/abs/2503.23077
19. https://arxiv.org/abs/2504.06514
20. https://arxiv.org/abs/2509.26522
21. https://arxiv.org/abs/2504.15895
22. https://arxiv.org/abs/2602.03814
23. https://arxiv.org/abs/2606.06574
24. https://arxiv.org/abs/2507.07996
25. https://arxiv.org/abs/2608.08888
26. https://arxiv.org/abs/2601.12307
27. https://arxiv.org/abs/2503.01935
28. https://arxiv.org/abs/2512.21352
29. https://arxiv.org/abs/2511.15755
30. https://arxiv.org/abs/2602.06038
31. https://arxiv.org/abs/2605.03310
32. https://arxiv.org/abs/2511.07112
33. https://arxiv.org/abs/2502.11133
34. https://arxiv.org/abs/2607.05391
35. https://arxiv.org/abs/2602.04254
36. https://arxiv.org/abs/2604.16529
37. https://arxiv.org/abs/2606.06915
38. https://arxiv.org/abs/2506.12928
39. https://arxiv.org/abs/2608.15089
40. https://arxiv.org/abs/2506.07636
41. https://arxiv.org/abs/2506.19290
42. https://arxiv.org/abs/2607.11388
43. https://arxiv.org/abs/2606.28480
44. https://arxiv.org/abs/2507.23361
45. https://arxiv.org/abs/2508.02694
46. https://arxiv.org/abs/2603.15401
47. https://arxiv.org/abs/2602.12670
48. https://arxiv.org/abs/2603.22455
49. https://arxiv.org/abs/2605.29794
50. https://arxiv.org/abs/2605.10114
51. https://arxiv.org/abs/2605.05726

> Ghi chú: danh mục trên gồm các paper trực tiếp và các nguồn nền tảng được nhóm lại trong 53 mục phân tích ở phần 13; tài liệu chính thức OpenAI và website LLM-as-a-Verifier được tách riêng ở phần 25.
