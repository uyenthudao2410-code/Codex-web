# Tools-Codex-web — Phương pháp luận tối ưu hiệu suất/chi phí và thiết kế nâng cấp

**Ngày:** 2026-08-14  
**Repository:** `Tools-Codex-web`  
**Loại tài liệu:** architecture / performance-cost methodology / production upgrade decision  
**Trạng thái:** proposal có evidence; chưa phải lệnh triển khai  
**Mục tiêu:** xác định bài toán tối ưu đúng cho Tools-Codex-web dựa trên thực tiễn runtime hiện tại, benchmark đã có và các primitive đã triển khai; từ đó đưa ra kiến trúc nâng cấp có ROI cao nhất mà không phá EOCL, authority boundary, Smart-v3 hay tính deterministic của hệ thống.

---

# 0. Executive decision

## 0.1 Kết luận chính

Bài toán tối ưu lớn nhất của Tools-Codex-web **không còn là “chọn model nào rẻ nhất” và cũng không phải “port DeepSeek Harness càng nhiều càng tốt”**.

Bài toán đúng là:

> **Giảm tổng coordination tax trên mỗi accepted result, trong khi giữ nguyên hoặc tăng correctness, first-pass acceptance, authority safety và quality of proof.**

Nói cách khác, hệ thống cần tối ưu:

```text
accepted-result economics
=
model cost
+ context cost
+ tool round-trip cost
+ control-plane cost
+ proof cost
+ repair/replan cost
+ integration cost
+ latency tail
```

chứ không tối ưu riêng:

```text
price_per_model_call
```

Điều này được xác nhận trực tiếp bởi benchmark nội bộ:

- trên hai leaf sạch, Mini thấp hơn Luna khoảng **60,8% credits** và nhanh hơn khoảng **24,2% model wall time**;
- nhưng ở một leaf khác, chỉ hai lỗi control-plane về **candidate target/path** và **proof cwd** đã khiến tổng spend của Mini trở thành **đắt hơn Luna khoảng 23,5%** và chậm hơn khoảng **80,1%** ở cấp accepted result;
- Sol xhigh có thể dùng nhiều credits hơn nhiều nhưng vẫn không tạo accepted candidate nếu topology không phù hợp;
- warm same-thread reuse có thể giảm chi phí rất mạnh so với fresh invocation khi thread còn khỏe;
- proof cache, idempotency, bounded output, capsule và EOCL đã chứng minh là đúng hướng, nhưng chưa được tận dụng đồng đều trên toàn pipeline.

Vì vậy thứ tự tối ưu phải là:

```text
1. loại bỏ false failure / control-plane repair
2. đo đúng coordination tax
3. hợp nhất runtime metadata và execution pipeline
4. dùng semantic localization đã có
5. giảm tool round-trip bằng composite read execution
6. giảm model-visible bytes bằng query/prune/reference
7. route theo accepted-result economics
8. song song hóa chỉ phần thực sự safe
9. mới xét các extension/plugin nâng cao
```

## 0.2 Điều chỉnh quan trọng so với phân tích DeepSeek Harness ban đầu

Sau audit code hiện tại, Tools-Codex-web **đã có nhiều primitive tương đương hoặc gần tương đương DeepSeek Harness**:

- có `ToolRuntime` ở Rust runtime;
- có structured process/argv và structured script payload;
- có durable Jobs và job-state reconciliation;
- có read-only LSP navigation ở Runner protocol;
- có session state / session summary / event recording;
- có output bounding, command/output references và artifact workflows;
- có EOCL, controller fencing, write authority, proof ledger, idempotency và contract fingerprint;
- có Smart-v3 với đúng 8 public tools làm façade ổn định.

Do đó không nên tạo một plugin framework mới từ số 0. Không nên tạo một generic `run_code` mới có quyền filesystem/network/shell. Không nên expose thêm LSP tool chỉ để “giống DeepSeek Harness”.

**Hướng tối ưu là convergence, không phải replacement.**

## 0.3 Target decision

Giữ topology authority hiện tại:

```text
ChatWeb / Sol
    │
    │ semantic authority + final acceptance
    ▼
Smart-v3 façade — 8 public tools, contract stable
    │
    ▼
agent_workflow / task_control
    │
    ▼
Efficiency Planner
    │
    ├── deterministic path
    ├── semantic localization path
    ├── bounded candidate path
    ├── composite read plan
    └── deep lane
    │
    ▼
Unified Tool Runtime Metadata / Execution Pipeline
    │
    ▼
EOCL + permission + write authority gates
    │
    ▼
Rust Runner / typed execution / LSP / Jobs / providers
    │
    ▼
proof + event + session + artifact/reference stores
    │
    ▼
model-free pruning / bounded context projection
    │
    ▼
Sol acceptance
```

Nguyên tắc bất biến:

> **Provider/plugin có thể thay cách thực thi; provider/plugin không được thay authority.**

---

# 1. Phạm vi, non-goals và evidence model

## 1.1 Phạm vi

Tài liệu này tập trung vào bốn câu hỏi:

1. Phương pháp luận hiện tại của dự án đang tối ưu theo cách nào?
2. Thực tiễn runtime và benchmark hiện tại cho thấy bottleneck thật nằm ở đâu?
3. Những ý tưởng nào từ DeepSeek Harness thực sự còn thiếu, những gì đã có và không nên làm lại?
4. Kiến trúc và lộ trình nào cho tỷ lệ performance/cost/quality tốt nhất với rủi ro thấp nhất?

## 1.2 Non-goals

Tài liệu này không đề xuất:

- thay EOCL bằng plugin visibility;
- bỏ Sol final acceptance;
- cho model phụ trực tiếp ghi authoritative checkout;
- biến Smart-v3 thành hàng chục public tools;
- tạo hệ multi-agent mặc định cho mọi task;
- port Cordis hoặc toàn bộ DeepSeek Harness;
- tạo self-modifying production extensions;
- thay structured runtime bằng raw shell text;
- chạy broad verification sau mọi patch nhỏ;
- tối ưu bằng cách giảm proof quality hoặc nới security boundary.

## 1.3 Evidence hierarchy

Các kết luận được chia thành bốn lớp evidence.

### Level A — code/runtime hiện tại

Nguồn chính:

- `README.md`
- `AGENTS.md`
- `resources/coding-tools-mcp/coding_tools_mcp/server.py`
- `resources/coding-tools-mcp/coding_tools_mcp/orchestration_control.py`
- `resources/coding-tools-mcp/coding_tools_mcp/orchestration_ledger.py`
- `resources/coding-tools-mcp/coding_tools_mcp/performance_trace.py`
- `resources/coding-tools-mcp/coding_tools_mcp/tool_results.py`
- `src/tool_runtime/...`
- `src/runtime_http.rs`
- `src/runtime_http_tests.rs`
- `crates/webcodex-core/src/shell_protocol.rs`
- `crates/webcodex-runner/src/webcodex_runner/dispatch.rs`
- Runner LSP/validation/job modules.

### Level B — live benchmark và telemetry nội bộ

Nguồn chính:

- `.coding-tools/performance.json`
- `docs/research/260814_EXECUTION_HUB_LIVE_BENCHMARK_HIEU_SUAT_CHI_PHI.md`
- `docs/research/2026-08-14_POST_P1_FOLLOWUP_TRACKER.md`
- `docs/research/2026-08-14_RUNTIME_ACTIVATION_AND_PRODUCTION_TELEMETRY_LOG.md`
- `docs/research/CONTEXT_TUNNEL_LONGHORIZON_ANALYSIS_2026-08-14.md`
- `docs/research/ORCHESTRATION_METHODOLOGY_EXPERIMENTS_AND_PRODUCTION_DECISION_2026-08-12.md`

### Level C — incident/postmortem nội bộ

Nguồn chính:

- `docs/research/PFM_ORCHESTRATION_RUNTIME_POSTMORTEM_AND_ENFORCED_CONTROL_LOOP_RESEARCH_2026-08-13.md`

Tài liệu này đã chứng minh một nguyên tắc quan trọng:

```text
policy đúng nhưng không được runtime enforce
=> coordination drift
=> duplicated work / patch ambiguity / proof waste
```

### Level D — DeepSeek Harness như kiến trúc tham khảo

Repo tham khảo:

```text
https://github.com/deepseek-ai/deepseek-harness
```

Dùng để so sánh pattern:

- plugin/service definition;
- tool execution pipeline;
- code runtime bindings;
- LSP bounded operations;
- session query;
- compaction;
- spill/output reference;
- concurrency metadata;
- interaction/approval abstractions.

Không dùng nó như source of truth cho authority model của Tools-Codex-web.

---

# 2. Xác định lại bài toán tối ưu

## 2.1 Tối ưu lexicographic trước, kinh tế sau

Thứ tự mục tiêu phải là:

```text
1. correctness / safety / truthful proof
2. first-pass accepted result
3. time-to-accepted-result
4. credits / accepted result
5. model-visible bytes / accepted result
6. repair/replan/tool-call count
7. maintainability
8. simplicity khi các phương án gần tương đương
```

Không chấp nhận trade-off kiểu:

```text
-20% credits
nhưng
+critical defect
```

hay:

```text
faster
nhưng
proof không còn authoritative
```

## 2.2 Cost function đúng

Một mô hình đơn giản:

```text
ExpectedAcceptedCost =
    (
        C_model
      + C_tool
      + C_context
      + C_proof
      + C_review
      + C_repair
      + C_integration
      + C_ops
    )
    / P(accepted)
```

Trong đó:

- `C_model`: generation/inference credits;
- `C_tool`: MCP/Runner/tool execution overhead;
- `C_context`: token/context bytes phải đưa lại cho model;
- `C_proof`: tests/build/schema/DB checks;
- `C_review`: acceptance/reviewer cost;
- `C_repair`: retry, REPLAN, relocalization, fallback;
- `C_integration`: merge/worktree/contract synchronization;
- `C_ops`: stale state, reconnect, lifecycle, restart, operator intervention.

## 2.3 Time-to-accepted decomposition

```text
T_accept =
    T_preflight
  + T_localize
  + T_dispatch
  + T_model
  + T_apply
  + T_proof
  + T_accept_wait
  + T_replan
```

Đây là lý do không được gọi toàn bộ `estimated_wait_ms` là “model latency”. Nó có thể chứa nhiều phần coordination gap khác nhau.

## 2.4 Multi-objective score để router dùng

Một score thực dụng:

```text
J(route | task) =
    E[credits_to_accept]
  + λt * E[T_accept]
  + λr * E[repair_count]
  + λb * E[model_visible_bytes]
  + λo * operational_risk
```

Subject to hard constraints:

```text
critical_safety_regression = 0
false_green_proof = 0
unauthorized_write = 0
EOCL_invariants = preserved
Smart-v3_contract = stable unless explicitly versioned
```

Router không được “mua” latency bằng cách bỏ proof hoặc mở authority.

---

# 3. Thực trạng kiến trúc hiện tại

## 3.1 Public control surface đã đúng hướng

Smart-v3 giữ đúng 8 public tools:

```text
workspace_context
agent_workflow
task_control
exec_command
command_control
document_workflow
request_permissions
view_image
```

Đây là một quyết định tốt vì nó giảm:

- schema entropy;
- tool-selection entropy;
- connector drift;
- prompt/tool manifest size;
- coupling giữa model và implementation detail.

**Không nên tăng public tool count chỉ vì runtime bên dưới được modular hóa.**

## 3.2 EOCL là tài sản cốt lõi

State machine hiện tại:

```text
PREFLIGHT
  -> READY
  -> ROUTED
  -> EXECUTING
  -> PROVING
  -> ACCEPTING
  -> CHECKPOINTED
```

Exceptional states:

```text
REPLAN
BLOCKED
ABORTED
```

Cùng với:

- controller lease/fencing;
- repository write authority riêng;
- task/run/proof/capsule durability;
- handoff bounded;
- final Sol acceptance.

Điểm này **mạnh hơn** việc chỉ ẩn/hiện tool theo plugin scope. Tool visibility không phải security boundary; EOCL/write lease/provider-side validation mới là authority boundary.

## 3.3 Adaptive routing đã có nền đúng

Các lane:

```text
deterministic
mini
luna
terra
sol_xhigh
sol_max
sol_ultra
```

Nguyên tắc hiện tại đã đúng ở cấp phương pháp:

- deterministic nếu không cần fresh judgment;
- Mini/Luna cho bounded leaf có strong oracle;
- Sol xhigh cho deep/high-integration;
- Terra explicit/experimental;
- max/ultra phải có gate;
- không serial cascade không giới hạn;
- candidate không trực tiếp mutate authoritative checkout.

Vấn đề hiện tại không phải thiếu router. Vấn đề là router chưa có đủ **clean feature signals + accepted-result telemetry** để đạt hiệu quả tối đa.

## 3.4 Candidate packet và proof plane đã đúng hướng

Dự án đã có:

- bounded candidate context;
- exact target/path constraints;
- MCP writer/oracle ownership;
- proof ledger;
- proof fingerprint/cache ở một số đường;
- task state + event/capsule;
- idempotency semantics;
- output pagination/reference.

Điểm cần nâng cấp là **coverage và integration**, không phải viết lại triết lý.

## 3.5 Có hai lớp runtime cần convergence

Audit hiện tại cho thấy repository có đồng thời:

1. Python Coding Tools MCP/orchestration package, trong đó `server.py` vẫn rất lớn, khoảng 11,2k dòng / ~517 KB ở snapshot audit;
2. Rust WebCodex runtime với `ToolRuntime`, typed protocol, Runner, durable jobs, LSP và transport-neutral execution.

Đây là một seam quan trọng.

Không nên giả định rằng “Python phải bị thay thế bởi Rust” hoặc ngược lại. Điều cần làm trước là xác định rõ:

```text
orchestration authority
execution authority
schema authority
provider authority
telemetry authority
presentation authority
```

cho từng lớp.

Mục tiêu là **một contract logic**, không nhất thiết một ngôn ngữ hoặc một process.

---

# 4. Baseline thực nghiệm hiện tại

## 4.1 Live trace snapshot đọc trong quá trình phân tích

Snapshot `.coding-tools/performance.json` là dữ liệu động; nó bao gồm cả hoạt động tool trong quá trình audit nên không được xem là benchmark cố định.

Tại thời điểm đọc:

| Metric | Giá trị |
|---|---:|
| tool calls | 802 |
| errors | 105 |
| error rate | ~13,09% |
| cache hits | 1 |
| proof cache hits | 1 |
| proof cache saved | 999 ms |
| deduplicated calls | 0 |
| idempotency eligible calls | 520 |
| eligible calls có key | 141 |
| idempotency key coverage trên eligible | ~27,12% |
| request bytes | 1.118.640 |
| response bytes | 18.328.427 |
| avg request | ~1,36 KiB/call |
| avg response | ~22,3 KiB/call |
| response/request byte ratio | ~16,4x |
| local execution ms | 1.644.117 |
| estimated wait/gap ms | 18.598.289 |
| wait-gap/local ratio | ~11,3x |

Lưu ý:

```text
estimated_wait_ms != model latency
```

Nó chỉ là tín hiệu cho thấy phần thời gian ngoài local execution đủ lớn để đáng được tách thành queue/dispatch/model/accept/reconnect/replan.

## 4.2 Execution/routing snapshot

Trong cùng trace:

```text
execution_mode_counts:
  mcp_only              367
  deep_single_lane       22
  bounded_candidate      14
  auto                   35

route_resolved_counts:
  deterministic          242
  mini                     8
  luna                     6
  sol_xhigh                 3
  terra                     6
```

Các count này không nhất thiết cover toàn bộ 802 calls, nên không được dùng như tỷ lệ route tuyệt đối mà không kiểm tra denominator.

## 4.3 Orchestration-state snapshot

```text
ACCEPTING     107
CHECKPOINTED   76
PREFLIGHT     151
REPLAN         81
ABORTED        23
```

Một lần nữa, đây là event/count snapshot, không phải “81 task thất bại”. Nhưng số lượng REPLAN/ABORTED đủ lớn để khẳng định coordination economics phải được đo như first-class metric.

---

# 5. Benchmark cho thấy điều gì thật sự quyết định cost

## 5.1 Paired leaf sạch: Mini thắng rõ

Trong benchmark normalize + timeout sạch:

```text
Mini total credits:  0.234118
Luna total credits:  0.597400
```

Mini thấp hơn khoảng:

```text
60,8%
```

Model wall:

```text
Mini: 12.047s
Luna: 15.890s
```

Mini nhanh hơn khoảng:

```text
24,2%
```

Cả hai đều 2/2 first-pass accepted trên cohort sạch.

Kết luận:

> Khi packet, path và oracle sạch, small bounded model thực sự tạo lợi thế lớn.

## 5.2 Control-plane defect có thể xóa sạch lợi thế model

Capacity leaf:

```text
Luna:
  first-pass
  4.875s
  0.281800 credits

Mini attempt 1:
  hiểu đúng fix
  CANDIDATE_TARGET_MISSING
  3.827s
  0.174897 credits

Mini attempt 2:
  candidate apply được
  proof false-fail vì cwd
  4.952s
  0.173118 credits
```

Tổng Mini accepted spend:

```text
0.348015 credits
8.779s model wall
```

So với Luna:

- Mini trở thành **~23,5% đắt hơn**;
- Mini trở thành **~80,1% chậm hơn**.

Nhưng nguyên nhân không phải Mini “reason kém”. Hai lỗi là control-plane/path/cwd.

Đây là evidence mạnh nhất cho thứ tự ưu tiên:

> **Sửa control-plane correctness trước khi tối ưu model tier.**

## 5.3 Sol xhigh không cứu topology sai

Một paired leaf ghi nhận Sol xhigh:

```text
~30.015s
~0.948850 credits
deadline
không có accepted candidate
```

Trong khi Mini/Luna bounded path pass.

Kết luận:

```text
stronger model != lower accepted cost
```

Nếu task shape có strong deterministic oracle và localized patch, deep autonomous lane có thể là topology sai.

## 5.4 Same-thread reuse là optimization lớn

Một A/B same-thread benchmark:

```text
warm Mini:
  4.484s
  0.041760 credits
  cache ~94.32%

fresh Mini:
  5.360s
  0.171395 credits
  cache ~14.91%
```

Warm continuation:

- thấp hơn khoảng **75,6% credits**;
- nhanh hơn khoảng **16,3%**;
- cache tăng khoảng **79,41 điểm phần trăm**.

Không được suy ra rằng mọi task phải reuse thread. Thread health và context bloat vẫn phải được gate. Nhưng khi thread còn sạch, cache/session continuity là economic lever lớn.

## 5.5 Hub overhead cần đo resident, không đo cold spawn

Live benchmark đã đo thin-proxy cold one-shot khoảng:

```text
~519,6ms/call
```

trong đó có Python process startup.

Đây **không phải resident steady-state RTT**.

Tối ưu đúng là đo:

```text
resident p50
resident p90
resident p99
queue delay
gateway RTT
upstream wait
```

Không được tối ưu dựa trên một cold-spawn number rồi kết luận transport là bottleneck chính.

---

# 6. Maturity matrix: hiện đã có gì, còn thiếu gì

| Capability | Trạng thái hiện tại | Đánh giá | Hành động tối ưu |
|---|---|---|---|
| Smart-v3 compact façade | Đã có, 8 public tools | Mạnh | Giữ contract ổn định |
| EOCL authority | Đã có | Mạnh | Giữ trên mọi provider/plugin |
| controller/write fencing | Đã có | Mạnh | Không thay bằng tool visibility |
| adaptive routing | Đã có | Khá mạnh | Nâng feature/telemetry, không viết lại router |
| bounded candidate | Đã có | Mạnh | Sửa path/cwd + packet quality |
| idempotency semantics | Đã pass canary | Mạnh nhưng coverage thấp | Tăng eligible-key coverage |
| proof fingerprint/cache | Đã có, exact reuse đã chứng minh | Đúng hướng | Mở rộng eligibility + telemetry |
| output bounding/reference | Có nhiều primitive | Partial/unified chưa đủ | Chuẩn hóa reference contract |
| Python ToolSpec/registry | Đã có mầm metadata | Partial | Extract/evolve, không tạo framework mới |
| Rust ToolRuntime | Đã có | Mạnh | Xác định là execution contract seam |
| typed process/argv | Đã có | Mạnh | Dùng làm nền composite execution |
| typed script payload | Đã có | Mạnh | Không quay lại raw shell orchestration |
| durable jobs/reconciliation | Đã có | Mạnh | Tận dụng cho parallel/proof lifecycle |
| LSP read-only navigation | Đã có ở Runner | Capability tốt, workflow utilization chưa rõ | Integrate vào localization nội bộ |
| session summary/events | Đã có | Partial | Nâng thành query/projection có authorization |
| semantic/model-free compaction | Chưa có đầy đủ | Gap | Chỉ thêm scoped pruning/projection |
| generic ArtifactRef | Một số output/artifact paths nhưng chưa thấy contract chung | Partial | Hợp nhất reference shape |
| per-operation concurrency safety | Job concurrency đã có; per-tool semantic safety chưa rõ | Gap | Thêm metadata tối thiểu khi có use case |
| tool-owned presentation intent | Renderer có nhưng presenter contract chưa chứng minh | Partial/Gap | Chỉ thêm khi giảm duplicate UI logic |
| approval provider abstraction | permission system có; provider seam chưa rõ | Partial | Extract nếu >=2 UI consumers cần cùng policy |
| dynamic model-written extensions | Không nên production | No-go | Không port lúc này |

---

# 7. So sánh DeepSeek Harness: lấy gì, không lấy gì

## 7.1 Tool execution pipeline — nên lấy pattern

DeepSeek Harness tách:

```text
pre-execute
-> guards
-> around execute
-> post-execute
-> finalize
-> observe
```

Tools-Codex-web nên học pattern này để giảm logic rải rác, nhưng **không cần clone framework**.

Target internal pipeline:

```text
resolve ToolSpec
-> validate schema
-> resolve capability
-> EOCL/permission/authority guard
-> idempotency/dedup guard
-> timeout/cancellation policy
-> provider execute
-> normalize typed result
-> output bounding/reference
-> proof/event/telemetry recording
-> presentation projection
```

## 7.2 LSP — không port, vì đã có

DeepSeek Harness có bounded semantic ops như:

```text
goToDefinition
findReferences
goToImplementation
hover
```

Tools-Codex-web đã có read-only LSP capability và explicit Runner dispatch path không fall through vào shell.

Hành động đúng:

```text
không thêm public LSP tool
không tạo generic JSON-RPC escape hatch
```

Mà:

```text
agent_workflow.prepare
  -> semantic localization
  -> LSP first
  -> text search fallback
  -> build bounded candidate packet
```

## 7.3 Code Runtime — lấy composite idea, không lấy generic raw run_code

DeepSeek Harness có model program chạy qua host async bindings.

Tools-Codex-web đã có:

- typed process;
- typed script;
- durable Job;
- LSP;
- shell fallback;
- authority guard.

Do đó thứ còn thiếu không phải “chạy code được”. Thứ có giá trị là:

> **Một bounded composite execution plan có thể thực hiện nhiều read/semantic operations trong một model round-trip.**

Ví dụ:

```text
locate symbol
-> definitions
-> references
-> read exact ranges
-> filter relevant files
-> git inspect
-> return one bounded structured result
```

Thay cho:

```text
model -> search
model -> read
model -> search
model -> read
model -> git
model -> summarize
```

## 7.4 Session Query — nên nâng từ primitive hiện có

Project đã có session store/events/summary, vì vậy không cần import nguyên package.

Gap có giá trị:

```text
query by session/run/wave/tool/status/path/time
relationship query
bounded search
retrieve exact evidence by locator
```

Mục tiêu là giúp model fetch đúng evidence khi cần thay vì replay full history.

## 7.5 Compaction — chỉ lấy model-free pruning

ROADMAP hiện không định hướng trở thành một full prompt-loop/context-budget engine.

Do đó không nên xây “semantic compactor” lớn.

Nên làm:

```text
large logs/diffs/tool outputs
-> deterministic summary/header
-> immutable reference
-> fetch-on-demand
```

Proof authority không được compact thành một đoạn narrative không kiểm chứng được.

## 7.6 Spill/ArtifactRef — nên chuẩn hóa

DeepSeek Harness spill oversized output thành preview + locator.

Tools-Codex-web đã có nhiều cơ chế tương tự nhưng phân tán.

Nên chuẩn hóa một contract chung, ví dụ:

```text
ExecutionArtifactRef
```

thay vì tạo storage system mới.

## 7.7 Dynamic extensions — chưa nên lấy

Self-modifying runtime/plugin packages có authority risk quá cao so với lợi ích hiện tại.

Nếu sau này thử nghiệm:

```text
ephemeral
read-only
isolated
no credentials
no authority registration
no direct write
expire after run
```

Production hiện tại: **NO-GO**.

---

# 8. Root-cause model: coordination tax đến từ đâu

## 8.1 Control-plane correctness tax

Biểu hiện:

- wrong candidate target normalization;
- wrong proof cwd;
- stale/ambiguous target;
- connector/runtime schema drift;
- unsupported permission path;
- controller handoff/restart edge cases.

Đây là loại tax nguy hiểm nhất vì nó:

1. làm model đúng bị chấm sai;
2. tạo replan không cần thiết;
3. làm small model trông tệ hơn thực tế;
4. tăng TTA tail;
5. phá calibration router.

## 8.2 Tool-round-trip tax

Nếu model phải xen kẽ quá nhiều:

```text
reason -> tool -> reason -> tool -> reason
```

thì mỗi vòng có:

- serialization;
- transport;
- context re-ingestion;
- model continuation;
- event/proof bookkeeping;
- potential stale state.

Read-heavy discovery là vùng có thể tối ưu mạnh bằng semantic/composite execution.

## 8.3 Context tax

Trace snapshot có avg response ~22,3 KiB/call và response/request ratio ~16,4x.

Không phải mọi byte đều đi thẳng vào model context, nhưng đây là signal rằng output projection cần được đo riêng:

```text
raw output bytes
transport bytes
stored bytes
model-visible bytes
```

Chỉ metric cuối mới phản ánh token pressure thực tế.

## 8.4 Replan tax

REPLAN là đúng khi state changed hoặc execution route sai. Nhưng REPLAN do:

```text
path bug
cwd bug
stale packet
missing target normalization
```

là pure waste.

Cần tách:

```text
semantic replan
control-plane replan
capacity replan
proof-infra replan
contract-drift replan
```

## 8.5 Acceptance wait tax

Accepted TTA p50/p90 lớn hơn model wall rất nhiều trong một số cohort vì TTA có thể bao gồm:

- control-plane orchestration;
- waiting for proof;
- Sol acceptance;
- handoff;
- transport waits.

Không có phase timing thì router dễ tối ưu nhầm model thay vì queue/accept path.

## 8.6 Proof tax

Proof cache exact reuse đã ghi nhận một hit tiết kiệm 999 ms. Hit count thấp không tự động là lỗi; nếu source/input khác thì đúng ra phải miss.

Metric đúng là:

```text
proof_cache_eligible
proof_cache_hit
proof_cache_valid_miss
proof_cache_invalidated_reason
saved_ms
```

Không tối ưu hit rate bằng cách nới fingerprint.

---

# 9. Kiến trúc mục tiêu

## 9.1 Phân lớp authority và implementation

```text
┌──────────────────────────────────────────────────────┐
│                 ChatWeb / Sol                        │
│ semantic control + final acceptance                  │
└───────────────────────┬──────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────┐
│              Smart-v3 Public Surface                 │
│ 8 tools, stable schema/fingerprint                   │
└───────────────────────┬──────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────┐
│              Orchestration / EOCL                    │
│ task state, route, controller, write lease, replan   │
└───────────────────────┬──────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────┐
│               Efficiency Planner                     │
│ deterministic | semantic | candidate | composite    │
└───────────────────────┬──────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────┐
│         Unified Tool Metadata / Execution Pipe       │
│ schema/risk/capability/idempotency/timeout/output    │
└───────────────────────┬──────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────┐
│         Authority / Permission Enforcement           │
│ EOCL + OAuth/scope + workspace + lease + sandbox     │
└───────────────────────┬──────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────┐
│                 Execution Providers                  │
│ Rust Runner | LSP | typed process/script | Jobs      │
└───────────────────────┬──────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────┐
│ Evidence / Session / Artifact Projection             │
│ proof + events + OutputRef + bounded session query   │
└───────────────────────┬──────────────────────────────┘
                        │
                        ▼
                bounded model context
```

## 9.2 Một luật kiến trúc quan trọng

```text
presentation scope != authority
```

Ví dụ một Mini lane có thể chỉ “nhìn thấy” read/LSP/test tools, nhưng security không được dựa vào việc tool write bị ẩn.

Write vẫn phải fail closed ở:

```text
EOCL
write lease
workspace policy
provider validation
sandbox
```

## 9.3 Một nguồn schema logic

Hiện project có nhiều surfaces: MCP, HTTP/GPT Actions, Rust runtime, Electron, proxy.

Target:

```text
Tool contract metadata
      │
      ├─ MCP projection
      ├─ HTTP projection
      ├─ Smart-v3 projection
      ├─ risk/permission projection
      └─ UI presentation projection
```

Không để mỗi surface tự hard-code riêng risk/tool mode/timeout/output behavior.

---

# 10. Wave 0 — Measurement correctness trước mọi optimization lớn

## 10.1 Mục tiêu

Không còn một metric `estimated_wait_ms` quá rộng khiến mọi latency ngoài local execution bị gom lại.

## 10.2 Phase timings cần ghi

Mỗi accepted run nên có:

```text
preflight_ms
localization_ms
packet_build_ms
queue_ms
dispatch_transport_ms
model_wall_ms
candidate_validate_ms
apply_ms
proof_ms
accept_wait_ms
replan_ms
handoff_ms
total_tta_ms
```

## 10.3 Byte accounting

Ghi riêng:

```text
request_transport_bytes
response_transport_bytes
raw_tool_output_bytes
stored_artifact_bytes
model_visible_bytes
candidate_context_bytes
resume_capsule_bytes
```

Không dùng response bytes làm token metric nếu chưa biết projection.

## 10.4 Route economics row

Mỗi run:

```text
task_id
run_id
wave_id
task_class
route_requested
route_resolved
model
effort
oracle_strength
integration_width
localization_confidence
packet_bytes
path_count
thread_reused
thread_health
cache_ratio
model_credits
first_pass_accepted
repair_count
fallback_count
proof_status
tta_ms
```

## 10.5 Error taxonomy

Tách ít nhất:

```text
CONTROL_PATH
CONTROL_CWD
CONTROL_SCHEMA
CONTROL_CONNECTOR
CAPACITY
DEADLINE
PROMPT_SIZE
MODEL_CANDIDATE_INVALID
BASE_DRIFT
PATCH_AMBIGUOUS
PROOF_INFRA
PROOF_CODE_FAILURE
AUTHORITY_DENIED
USER_BLOCKED
```

## 10.6 Hub benchmark đúng

Đo resident process:

```text
p50 / p90 / p99
```

với:

- no-op/health call;
- small read;
- bounded output;
- concurrent clients.

Cold process spawn chỉ giữ như startup metric.

## 10.7 Exit gate Wave 0

Chỉ qua Wave 0 khi:

- >=90–95% accepted TTA có thể phân bổ vào phase cụ thể;
- model wall và accept wait không còn bị trộn;
- model-visible bytes đo được;
- error taxonomy không còn >10–15% nằm trong “unknown/other” ở benchmark corpus;
- resident Hub p50/p90/p99 có baseline.

---

# 11. Wave 1 — Loại bỏ control-plane waste đã được chứng minh

Đây là **P0**.

## 11.1 Canonical target/path contract

Packet builder, candidate validator, apply path và proof path phải dùng cùng một resolver.

Không có:

```text
packet dùng subproject-relative
apply dùng repo-relative
proof dùng process cwd khác
```

Target resolver nên trả object typed:

```text
ResolvedTarget {
  repository_root
  project_root
  requested_path
  canonical_repo_relative_path
  canonical_project_relative_path
  exists
  sha256
  base_head
}
```

## 11.2 Canonical proof workdir

Proof plan phải lưu explicit:

```text
proof_workdir
command/program
args
relevant_inputs
```

Không infer cwd lại ở execution time nếu packet đã xác định.

## 11.3 Typed false-failure codes

Ít nhất:

```text
CANDIDATE_TARGET_MISSING
CANDIDATE_TARGET_OUTSIDE_SCOPE
PROOF_CWD_INVALID
PROOF_TOOL_UNAVAILABLE
PROOF_INFRA_TIMEOUT
CODE_ASSERTION_FAILED
```

Router không được học rằng “Mini failed” khi code đúng nhưng `PROOF_CWD_INVALID`.

## 11.4 Revalidate benchmark defects trên HEAD hiện tại

P1.7-A/P1.7-B trong benchmark phải được đưa thành regression corpus.

Không giả định chúng vẫn tồn tại y hệt; phải chạy cùng canonical test trên current HEAD trước khi patch.

## 11.5 Tăng idempotency coverage

Current dynamic trace:

```text
141 / 520 eligible calls có key
≈27,12%
```

Semantics đã pass canary, vì vậy next step là coverage.

Target đề xuất:

```text
>=95% eligible mutation/replay-sensitive operations có deterministic idempotency key
```

Không áp key một cách giả tạo cho operation không có semantic identity ổn định.

Key nên derive ở orchestration boundary từ:

```text
task/run/wave
operation type
canonical target
input fingerprint
```

## 11.6 Proof cache telemetry

Không thay fingerprint logic để tăng hit.

Thêm:

```text
cache_eligible
cache_key
hit/miss
miss_reason
invalidated_by
saved_ms
```

## 11.7 Stale-state hygiene

Stale orchestration records nên:

- terminalize theo policy;
- giữ audit evidence;
- không làm active cohort metrics sai;
- không mass-delete chỉ để dashboard đẹp.

## 11.8 Exit gate Wave 1

- benchmark corpus không còn false failure do path/cwd;
- control-plane repair trên canonical candidate corpus = 0;
- idempotency eligible-key coverage đạt mục tiêu đã chọn;
- no unauthorized replay;
- router labels control failure riêng model failure;
- first-pass accepted economics không còn bị control-plane lỗi làm đảo ngược.

---

# 12. Wave 2 — Hợp nhất Tool Runtime metadata/pipeline, không xây framework mới

Đây là **P0/P1**.

## 12.1 Lý do

Python MCP layer đã có `ToolSpec`/registry nhưng central server vẫn ôm nhiều concern.

Rust runtime đã có `ToolRuntime` và typed execution.

Nếu tiếp tục thêm optimization ad-hoc vào `server.py`, sẽ tạo:

- route logic duplication;
- timeout policy drift;
- output policy drift;
- risk metadata drift;
- UI special-case;
- khó benchmark từng stage.

## 12.2 Minimal ToolSpec evolution

Không cần plugin container lớn.

Một definition nội bộ tối thiểu:

```text
ToolDefinition {
  name
  input_schema
  output_schema
  capability
  risk_class
  mutation_class
  idempotency_policy
  timeout_policy
  cancellation_policy
  output_policy
  concurrency_policy
  presentation_intent
  provider
}
```

Không bắt buộc mọi field phải triển khai trong phase đầu.

Ưu tiên:

```text
schema
capability
risk
mutation
idempotency
timeout
output
```

## 12.3 Execution pipeline

```text
resolve
-> strict validate
-> scope/capability
-> EOCL authority
-> permission
-> idempotency
-> execute provider
-> normalize result
-> persist evidence
-> bound/spill output
-> emit telemetry
-> project presentation
```

## 12.4 Provider boundary

Provider có thể là:

```text
Rust Runner
local MCP implementation
LSP
validation bridge
artifact store
future external provider
```

Nhưng provider không được tự grant authority.

## 12.5 Smart-v3 không đổi

Public surface vẫn 8 tools.

`agent_workflow` có thể gọi nhiều internal capabilities nhưng model không cần biết toàn bộ implementation details.

## 12.6 Python/Rust convergence rule

Không yêu cầu rewrite toàn bộ.

Mục tiêu trước mắt:

```text
one semantic contract
multiple implementation processes allowed
```

Phải document rõ:

- ai owns schema;
- ai owns risk;
- ai owns permission;
- ai owns execution;
- ai owns telemetry;
- ai owns final result normalization.

## 12.7 Exit gate Wave 2

- Smart-v3 fingerprint không đổi;
- cùng một operation có cùng risk/mutation/timeout semantics trên các transport;
- không còn hard-coded policy duplication cho các tool được migrate;
- performance không regress đáng kể;
- authority tests vẫn fail closed.

---

# 13. Wave 3 — Semantic localization bằng LSP đã có

Đây là **P1, ROI cao**.

## 13.1 Không xây LSP mới

Runner đã có read-only LSP capability và explicit dispatch branch.

Việc cần làm là đưa nó vào `agent_workflow` như internal localization engine.

## 13.2 Localization pipeline

```text
query / failure / symbol hint
        │
        ▼
exact symbol extraction
        │
        ▼
LSP definition / references / implementation / hover
        │
        ├── high confidence
        │      ▼
        │  exact ranges
        │
        └── insufficient
               ▼
          text search fallback
               │
               ▼
        bounded file/range set
               │
               ▼
        candidate packet
```

## 13.3 Không expose generic JSON-RPC

Lý do:

- giảm protocol attack surface;
- tránh mutation methods;
- tránh arbitrary payload;
- giữ deterministic operation taxonomy.

## 13.4 SemanticLocalizationResult

```text
SemanticLocalizationResult {
  query
  symbol
  provider
  confidence
  definitions[]
  implementations[]
  references[]
  hover_summary
  fallback_search_used
  selected_ranges[]
  total_source_bytes
}
```

## 13.5 Metrics

Đo:

```text
lsp_available_rate
lsp_hit_rate
lsp_high_confidence_rate
fallback_search_rate
read/search_calls_per_accepted
localization_ms
localized_bytes
candidate_first_pass_acceptance
```

## 13.6 Hypothesis cần A/B

Không ghi trước thành fact.

Hypothesis:

```text
LSP-first localization
=> giảm read/search calls
=> giảm packet bytes
=> tăng target accuracy
=> giảm candidate repair
```

Target thử nghiệm có thể là giảm 20–30% discovery calls trên symbol-heavy corpus; quyết định production phải theo A/B.

## 13.7 Exit gate Wave 3

- không thêm public tool;
- LSP unavailable vẫn fallback deterministic;
- no shell fallback cho malformed LSP request;
- candidate quality không giảm;
- measured accepted economics cải thiện hoặc ít nhất không regress.

---

# 14. Wave 4 — Composite Read Execution / “Code Mode Lite”

Đây là **P1 experimental**, có thể tạo bước nhảy lớn về round-trip nếu làm đúng.

## 14.1 Vấn đề hiện tại

Một discovery turn điển hình có thể là:

```text
model
-> search
-> model
-> read
-> model
-> LSP/search
-> model
-> git inspect
-> model
```

Mỗi vòng model↔tool tạo overhead.

## 14.2 Target

Cho model/planner phát một **bounded read-only execution plan**, ví dụ:

```text
plan {
  locate symbol X
  fetch definition
  fetch references
  read ±N lines around relevant ranges
  inspect git state for those files
  filter to max K paths / max B bytes
}
```

Runtime thực thi trong một lane deterministic rồi trả một structured result.

## 14.3 Không phải generic arbitrary code

Phase đầu cấm:

```text
direct filesystem writes
direct network
credential access
raw subprocess
raw shell
permission mutation
lease mutation
provider registration
```

Allowed bindings chỉ là:

```text
read/search
LSP
git read-only
session/evidence query
bounded metadata
```

## 14.4 Reuse structured runtime hiện có

Nếu cần process/script implementation detail, nó phải đi qua typed structured process/script và existing authority policy.

Không cho model bypass bằng một new `run_code` có quyền host.

## 14.5 ExecutionPlan contract

```text
CompositeReadPlan {
  version
  task_id
  base_head
  max_steps
  max_output_bytes
  operations[]
}

Operation {
  id
  kind
  args
  depends_on[]
  output_selector
}
```

Runtime validator giới hạn operation count và output budget.

## 14.6 Fan-out/fan-in

Read-only independent ops có thể:

```text
LSP refs
read metadata
git status
config inspection
```

chạy song song nếu safe.

## 14.7 Metrics

```text
model_round_trips_per_accepted
composite_steps_per_plan
plan_rejection_rate
output_bytes
model_visible_bytes
localization correctness
accepted TTA
credits/accepted
```

## 14.8 Exit gate Wave 4

Chỉ promote nếu paired A/B cho thấy:

- giảm đáng kể round-trip hoặc TTA;
- không tăng false localization;
- no authority bypass;
- output vẫn bounded;
- no write/network/secret escape;
- fallback path rõ ràng.

---

# 15. Wave 5 — Long-horizon context economy

Đây là **P1**.

## 15.1 Mục tiêu

Không replay transcript hoặc long tool outputs nếu runtime đã có durable state/evidence.

## 15.2 Session Query trên primitive hiện có

Nâng session store/event store thành internal query layer:

```text
query events by session/run/wave
query by tool/status/risk
query proof by fingerprint
query artifacts by owner
query latest accepted evidence
query relationship task -> run -> proof -> artifact
```

Không nhất thiết model-facing như một public tool.

## 15.3 Model-free pruning

Ví dụ raw output:

```text
20 KiB test log
40 KiB diff
30 KiB search output
```

Model projection:

```text
test:
  status: failed
  failed: 1
  first_actionable_failure: ...
  artifact_ref: ...

diff:
  files: 4
  additions: 73
  deletions: 18
  artifact_ref: ...
```

Nếu model cần chi tiết thì fetch reference.

## 15.4 ExecutionArtifactRef

Đề xuất chuẩn chung:

```text
ExecutionArtifactRef {
  id
  kind
  source
  mime
  size_bytes
  sha256
  preview
  locator
  retention
  owner_task
  owner_run
  owner_wave
  created_at
}
```

Nó có thể wrap storage primitive hiện có; không nhất thiết tạo storage mới.

## 15.5 Capsule giữ nhỏ

Tiếp tục giữ handoff capsule bounded, ví dụ <=8 KiB như policy hiện tại.

Capsule chứa:

```text
task identity
objective
base/worktree fingerprint
active route/state
write owner
settled invariants
latest proof refs
open blockers
next action
```

Không chứa raw transcript/log.

## 15.6 Thread reuse gate

Same-thread reuse có lợi nhưng phải có health gate:

```text
context_size
recent error rate
cache state
last model/effort
turn count
tool continuity
```

Nếu thread unhealthy:

```text
compact external state
-> fresh thread
```

chứ không giữ thread chỉ vì cache rẻ.

## 15.7 Exit gate Wave 5

- model-visible bytes/accepted giảm rõ;
- resume không mất authority/proof identity;
- no proof semantics lost by pruning;
- fetch-on-demand works;
- same-thread vs fresh policy có measurable benefit.

---

# 16. Wave 6 — Adaptive Routing v2 theo accepted-result economics

Đây là **P1/P2** sau khi data sạch hơn.

## 16.1 Router không cần ML trước

Ban đầu dùng deterministic policy + historical cohorts.

Inputs:

```text
need_fresh_judgment
oracle_strength
localization_confidence
integration_width
seriality
path_count
packet_bytes
expected_edit_size
contract_stability
thread_health
cache_state
control_plane_health
similar_task_history
```

## 16.2 Core decision

Pseudo-policy:

```text
if deterministic_solution_available:
    route = deterministic

elif localized
     and strong_oracle
     and localization_confidence >= threshold
     and packet_within_mini_budget:
    route = mini

elif bounded
     and strong_oracle
     and packet_within_luna_budget:
    route = luna

elif experimental_cross_file_case_explicitly_allows_terra:
    route = terra

else:
    route = sol_xhigh
```

## 16.3 Thread-aware modifier

```text
if route in {mini, luna}
   and healthy_warm_thread_exists
   and contract/model/effort compatible:
       prefer warm continuation
```

Nhưng nếu thread quá lớn hoặc stale:

```text
external capsule + fresh thread
```

## 16.4 Control-plane health modifier

Nếu target/path/workdir state không clean:

```text
do not spend model
```

Preflight phải fail trước model call.

## 16.5 No serial ladder

Cấm mặc định:

```text
Mini -> Luna -> Terra -> Sol -> Max -> Ultra
```

Policy:

```text
one chosen lane
+ at most one evidence-driven fallback/replan
```

Fallback chỉ khi có new evidence:

```text
packet too large
oracle weak
integration width higher than predicted
model candidate invalid for semantic reason
capacity unavailable
```

## 16.6 Historical retrieval

Khi route ledger đủ sạch:

```text
retrieve K similar accepted tasks
-> compare route outcomes
-> estimate first-pass acceptance / credits / TTA
```

Không cần learned router ngay.

## 16.7 Route score

```text
route_score =
    predicted_credits_to_accept
  + λt * predicted_tta
  + λr * predicted_repair
  + λf * fallback_risk
```

## 16.8 Exit gate Wave 6

- router decisions shadow-mode trước;
- no quality/safety regression;
- credits/accepted giảm trên cohort;
- first-pass acceptance không giảm;
- fallback count không tăng;
- high-cost routes vẫn gate.

---

# 17. Wave 7 — Safe parallelism, không phải “nhiều agent hơn”

Đây là **P2**.

## 17.1 Project đã có job concurrency

Runner protocol có job concurrency và durable jobs. Đây là nền tốt.

Gap là semantic concurrency safety theo operation.

## 17.2 Chỉ song song hóa độc lập

Ví dụ read-only:

```text
git status
project metadata
LSP references
read config
test discovery
```

có thể chạy song song.

Writer thì:

```text
one authoritative write owner per mutable surface
```

## 17.3 Minimal metadata

Không cần generic scheduler lớn ngay.

Có thể bắt đầu:

```text
concurrency_class:
  read_parallel
  proof_parallel
  exclusive_write
  exclusive_session
```

hoặc callback per operation khi thật sự cần.

## 17.4 Proof DAG

Independent proof nodes có thể song song nếu:

- cùng source fingerprint;
- không mutate shared state;
- toolchain/cache không conflict;
- resource budget cho phép.

## 17.5 Parallelism KPI

Không đo:

```text
number_of_parallel_agents
```

Mà đo:

```text
critical_path_ms
queue_ms
CPU saturation
proof makespan
accepted TTA
integration defect rate
```

## 17.6 Multi-worktree chỉ khi contract frozen

```text
parallel writer allowed iff:
  interface_frozen
  semantics_settled
  write_sets_disjoint
  worktrees_isolated
  integration_oracle_exists
```

## 17.7 Exit gate Wave 7

- no write overlap;
- no stale-base increase;
- critical path giảm;
- integration defects không tăng;
- CPU/resource contention nằm trong budget.

---

# 18. Wave 8 — Presentation/approval/provider abstractions

Đây là **P2/P3**, không phải ưu tiên performance đầu tiên.

## 18.1 Tool-owned presentation intent

Nếu Electron/ChatWeb đang có nhiều special-case theo tool name, có thể thêm metadata:

```text
presentation:
  generic
  terminal
  diff
  search
  read
  progress
```

UI render theo intent thay vì switch theo tool name.

Chỉ làm nếu có ít nhất hai concrete consumers hoặc duplication hiện hữu.

## 18.2 Approval provider

Permission semantics vẫn nằm ở core policy.

UI interaction có thể là provider:

```text
Electron approval UI
ChatGPT elicitation
CLI/desktop approval
```

Nhưng provider chỉ hỏi/hiển thị; nó không được redefine policy.

## 18.3 Dynamic extensions

P3/no-go hiện tại.

Chỉ reconsider sau khi:

- ToolRuntime contract ổn định;
- authority tests mạnh;
- sandbox boundary được chứng minh;
- plugin provenance/signing/lifecycle rõ.

---

# 19. Data contracts đề xuất

## 19.1 ToolDefinition

```text
ToolDefinition {
  name: str
  input_schema: JSONSchema
  output_schema: JSONSchema
  capability: str
  risk_class: read_only | safe_write | dangerous
  mutation_class: none | workspace | external
  idempotency: none | optional | required
  timeout_ms: int
  cancellation: cooperative | hard
  output_policy: inline | bounded | reference
  concurrency_class: read_parallel | proof_parallel | exclusive
  presentation_intent: optional str
  provider: str
}
```

## 19.2 RouteDecision

```text
RouteDecision {
  task_id
  run_id
  task_class
  route_requested
  route_resolved
  model
  effort
  reason_codes[]
  oracle_strength
  localization_confidence
  integration_width
  packet_bytes
  path_count
  thread_reused
  expected_cost
  expected_tta
  fallback_budget
}
```

## 19.3 CompositeReadPlan

```text
CompositeReadPlan {
  version
  task_id
  base_head
  max_steps
  max_output_bytes
  operations[]
}
```

## 19.4 ExecutionArtifactRef

```text
ExecutionArtifactRef {
  id
  kind
  source
  mime
  size_bytes
  sha256
  preview
  locator
  retention
  owner_task
  owner_run
  owner_wave
}
```

## 19.5 PhaseTiming

```text
PhaseTiming {
  preflight_ms
  localization_ms
  packet_build_ms
  queue_ms
  transport_ms
  model_ms
  apply_ms
  proof_ms
  accept_wait_ms
  replan_ms
  total_ms
}
```

---

# 20. Mô hình route tối ưu đề xuất

## 20.1 Preflight trước model spend

```text
verify project/root/head
verify target resolver
verify proof cwd/tool
verify authority/write lease
verify oracle availability
verify transport/runtime health
```

Nếu fail:

```text
STOP BEFORE MODEL
```

## 20.2 Localize

```text
LSP first
-> exact range
-> search fallback
-> packet budget
```

## 20.3 Determine topology

```text
no judgment needed
    -> deterministic

localized + strong oracle
    -> Mini

bounded but harder
    -> Luna

high integration/deep coherent change
    -> Sol xhigh
```

## 20.4 Execute

Model không trực tiếp trở thành authority.

```text
candidate
-> MCP validate
-> guarded apply
-> proof
-> Sol accept
```

## 20.5 Recovery

```text
control-plane error
-> fix/replan control plane
-> do not blame model

semantic candidate error
-> one evidence-driven replan/fallback

capacity/deadline
-> preserve evidence
-> classify
-> one alternative path
```

---

# 21. Benchmark methodology cho từng wave

## 21.1 Corpus phải đại diện production topology

Tối thiểu gồm:

```text
A. deterministic no-model
B. localized single-file strong-oracle
C. bounded multi-file strong-oracle
D. high-integration/deep-code
E. long-horizon resume/handoff
F. transport/reconnect/replay
G. semantic navigation-heavy
H. proof-heavy
```

## 21.2 Paired A/B

Giữ cố định:

```text
same task
same HEAD/base
same oracle
same candidate acceptance rule
same environment
same model/effort khi đo runtime feature
```

Chỉ thay một biến.

Ví dụ Wave 3:

```text
A = search/read localization
B = LSP-first localization
```

Wave 4:

```text
A = multi-roundtrip tool loop
B = composite read plan
```

## 21.3 Warm/cold phải tách riêng

Không trộn:

```text
fresh thread
warm same-thread
cold process
resident process
```

vào cùng mean.

## 21.4 Metrics bắt buộc

```text
first_pass_acceptance
accepted_rate
critical_defect_rate
model_credits
credits_per_accepted
model_wall_ms
TTA p50/p90/p99
tool_calls
model_round_trips
model_visible_bytes
repair_count
fallback_count
proof_ms
proof_cache_eligible/hit
LSP hit/fallback
idempotency coverage
```

## 21.5 Statistics

Không chỉ dùng mean.

Báo cáo:

```text
n
median/p50
p90
p99 nếu sample đủ
failure rate
accepted-only cost
all-attempt cost
paired delta
bootstrap confidence interval khi sample đủ
```

## 21.6 Evidence labels

Mọi số trong report phải được gắn:

```text
MEASURED
SCENARIO
HYPOTHESIS
TARGET
```

Không biến scenario simulation thành production fact.

---

# 22. KPI/SLO đề xuất

Các target dưới đây là **mục tiêu thử nghiệm**, không phải forecast chắc chắn.

## 22.1 Guardrails

```text
critical safety regression                = 0
false green proof                          = 0
unauthorized authoritative write           = 0
Smart-v3 accidental contract drift         = 0
unbounded model-visible tool output         = 0
```

## 22.2 P0 targets

```text
path/cwd false failure on regression corpus = 0
control-plane repair on clean leaf corpus   = 0
eligible idempotency key coverage           >=95% target
unknown error taxonomy share                <10% target
```

## 22.3 Efficiency targets

Initial targets to validate:

```text
credits / accepted result        -25% initial
                                  -40% stretch on eligible cohorts

TTA p50                          -20%
TTA p90                          -30% on tail-heavy eligible cohorts

model-visible bytes / accepted   -30%
```

Không yêu cầu mọi task class đạt cùng mức.

## 22.4 LSP hypothesis targets

```text
read/search discovery calls       -20% to -30% hypothesis
candidate localization repair     down
first-pass acceptance              non-decreasing
```

## 22.5 Composite read hypothesis targets

```text
model/tool round-trips             -30% to -40% hypothesis
model-visible bytes                down
TTA                                down
```

Production promotion dựa trên measured result, không dựa vào target.

---

# 23. Rủi ro và mitigation

## 23.1 Over-abstraction

**Risk:** biến ToolRuntime thành framework tổng quát lớn.

**Mitigation:** chỉ extract metadata/hook có >=2 concrete consumers hoặc giải quyết measured problem.

## 23.2 Authority confusion

**Risk:** capability scope bị hiểu nhầm là security.

**Mitigation:** EOCL/write lease/provider enforcement luôn authoritative.

## 23.3 Duplicate Python/Rust contracts

**Risk:** thêm một abstraction nữa nhưng không xóa duplication.

**Mitigation:** mỗi metadata field phải có một canonical owner; projection-only ở lớp còn lại.

## 23.4 Composite execution trở thành arbitrary code escape

**Risk:** model chạy code có FS/network/secret access.

**Mitigation:** phase đầu read-only declarative plan, fixed operation set, bounded steps/output, all operations pass authority layer.

## 23.5 Compaction làm mất evidence

**Risk:** summary thay proof.

**Mitigation:** summary chỉ là projection; immutable raw evidence giữ bằng hash/reference.

## 23.6 Aggressive parallelism gây contention/stale writes

**Risk:** TTA tăng hoặc integration fail.

**Mitigation:** only read/proof parallel first; writer isolation + worktree contract.

## 23.7 Router overfits benchmark

**Risk:** small corpus tạo policy sai.

**Mitigation:** shadow mode, cohort split, historical retrieval, confidence gate, one fallback maximum.

## 23.8 Chasing cache hit rate

**Risk:** weaken proof fingerprint hoặc reuse stale state.

**Mitigation:** exact fingerprint remains hard condition; optimize eligibility, không optimize hit bằng semantic weakening.

---

# 24. No-go list

Không làm các việc sau trong đợt tối ưu chính:

1. Port toàn bộ DeepSeek Harness/Cordis.
2. Thay EOCL bằng plugin restriction.
3. Tạo public `run_code` có raw filesystem/network/shell.
4. Expose LSP như public tool thứ 9 chỉ để model tự gọi.
5. Tăng số agent mặc định.
6. Dùng cascade `Mini -> Luna -> Terra -> Sol -> Max -> Ultra`.
7. Xóa stale history hàng loạt chỉ để giảm count.
8. Nới proof fingerprint để tăng cache hit.
9. Semantic compaction làm mất raw proof/evidence.
10. Đưa dynamic self-modifying extensions vào production.
11. Rewrite Python/Rust lớn trước khi đo contract duplication cụ thể.
12. Đo model price mà bỏ qua repair/fallback/integration.

---

# 25. Prioritized backlog

## P0 — làm trước

### P0.1 Phase-level telemetry

- tách queue/transport/model/proof/accept/replan;
- model-visible byte accounting;
- error taxonomy;
- accepted-result linkage.

### P0.2 Canonical path/cwd contract

- một resolver;
- proof workdir explicit;
- regression corpus P1.7-A/B.

### P0.3 Idempotency coverage

- tự động key cho eligible paths;
- conflict fail closed;
- measure coverage.

### P0.4 Tool metadata convergence

- evolve existing `ToolSpec`/`ToolRuntime`;
- schema/risk/mutation/timeout/output canonicalization;
- giữ Smart-v3 stable.

## P1 — ROI cao tiếp theo

### P1.1 LSP-first internal localization

- integrate Runner LSP vào `agent_workflow`;
- search fallback;
- A/B.

### P1.2 Composite Read Plan

- read-only fixed bindings;
- bounded fan-out/filter/reduce;
- không raw run_code.

### P1.3 Session Query + model-free pruning

- query event/proof/artifact;
- bounded projection;
- generic `ExecutionArtifactRef`.

### P1.4 Routing v2

- first-pass accepted economics;
- warm-thread health;
- similar-task retrieval;
- one evidence-driven fallback.

## P2

### P2.1 Safe parallel read/proof scheduling

- semantic concurrency classes;
- proof DAG parallelism;
- writer exclusivity.

### P2.2 Presentation intent

Chỉ nếu giảm duplicate renderer logic.

### P2.3 Approval provider abstraction

Chỉ nếu nhiều frontends thực sự dùng cùng policy với UI khác nhau.

## P3

- ACP/extension adapters;
- experimental ephemeral extensions;
- learned routing sau khi route ledger đủ sạch.

---

# 26. Expected file/module impact khi triển khai

Đây là map định hướng; trước mỗi implementation wave phải re-audit HEAD.

## Python Coding Tools MCP

Khả năng liên quan:

```text
resources/coding-tools-mcp/coding_tools_mcp/server.py
resources/coding-tools-mcp/coding_tools_mcp/performance_trace.py
resources/coding-tools-mcp/coding_tools_mcp/tool_results.py
resources/coding-tools-mcp/coding_tools_mcp/orchestration_control.py
resources/coding-tools-mcp/coding_tools_mcp/orchestration_ledger.py
resources/coding-tools-mcp/coding_tools_mcp/proof_ledger.py
resources/coding-tools-mcp/coding_tools_mcp/task_state.py
```

Mục tiêu không phải chia file cho đẹp, mà di chuyển đúng concern ra seam có ownership rõ.

## Rust runtime / server

Khả năng liên quan:

```text
src/tool_runtime/...
src/runtime_http.rs
crates/webcodex-core/src/shell_protocol.rs
```

## Runner

Khả năng liên quan:

```text
crates/webcodex-runner/src/webcodex_runner/dispatch.rs
crates/webcodex-runner/src/webcodex_runner/lsp/...
validation/job/transport modules
```

## Electron/renderer

Chỉ thay nếu presentation/approval metadata phase được chấp nhận.

---

# 27. Go/No-Go gates theo wave

## Wave 0 -> Wave 1

GO nếu phase timing và attribution đủ tin cậy.

## Wave 1 -> Wave 2

GO nếu regression corpus path/cwd sạch và control-plane false-failure = 0.

## Wave 2 -> Wave 3

GO nếu Tool metadata convergence không làm Smart-v3/schema/authority regress.

## Wave 3 -> Wave 4

GO nếu LSP localization có measured benefit hoặc ít nhất tạo packet quality rõ mà không tăng lỗi.

## Wave 4 -> Wave 5

GO nếu composite plan giảm round-trip và không tạo authority escape.

## Wave 5 -> Wave 6

GO nếu model-visible bytes được đo và pruning không phá proof continuity.

## Wave 6 -> Wave 7

GO nếu router v2 đã ổn định first-pass economics; lúc đó mới tối ưu critical path bằng parallelism.

## Wave 7 -> Wave 8

GO khi core economics đã tốt và UI/provider duplication trở thành bottleneck thực.

---

# 28. Decision tree vận hành sau nâng cấp

```text
TASK ARRIVES
   │
   ▼
PRE-FLIGHT CLEAN?
   │
   ├─ NO -> typed control-plane failure -> repair without model spend
   │
   └─ YES
       │
       ▼
DETERMINISTIC SOLUTION?
   │
   ├─ YES -> MCP/runtime -> proof -> accept
   │
   └─ NO
       │
       ▼
SEMANTIC LOCALIZATION
   │
   ├─ LSP high confidence
   │
   └─ search fallback
       │
       ▼
TASK SHAPE
   │
   ├─ localized + strong oracle -> Mini
   │
   ├─ bounded harder leaf       -> Luna
   │
   ├─ experimental explicit     -> Terra
   │
   └─ deep/high integration     -> Sol xhigh
       │
       ▼
CAN DISCOVERY BE COMPOSITE READ?
   │
   ├─ YES -> bounded composite plan
   │
   └─ NO  -> ordinary tool path
       │
       ▼
CANDIDATE / EXECUTION
       │
       ▼
EOCL + WRITE AUTHORITY
       │
       ▼
DETERMINISTIC PROOF
       │
       ▼
SOL ACCEPT
       │
       ▼
CHECKPOINT + EVIDENCE REFERENCES
```

---

# 29. Bài toán tối ưu cuối cùng

Có thể diễn đạt bài toán production như sau.

Cho một task `x`, chọn:

```text
route r
execution topology e
context projection c
proof plan p
parallel schedule s
```

để tối thiểu:

```text
E[
  credits_to_accept
  + λ1 * time_to_accept
  + λ2 * repair_work
  + λ3 * model_visible_bytes
  + λ4 * operational_overhead
]
```

với các constraint:

```text
correctness >= required quality floor
critical defect probability <= allowed floor
proof remains authoritative
EOCL transitions valid
write lease valid
workspace boundary valid
public Smart-v3 contract stable
one-fallback policy respected
```

Điểm quan trọng:

```text
model tier
```

chỉ là **một biến** trong bài toán này.

Nhiều optimization có ROI cao hơn đổi model:

```text
path correctness
semantic localization
context projection
thread reuse
proof reuse
round-trip reduction
safe parallelism
```

---

# 30. Khuyến nghị triển khai thực tế

Nếu chỉ chọn ba cụm nâng cấp đầu tiên để có ROI cao nhất:

## 1. Control-plane correctness + attribution telemetry

Lý do:

- đã có evidence trực tiếp làm đảo ngược cost ranking Mini/Luna;
- ít rủi ro kiến trúc;
- làm sạch dữ liệu cho mọi optimization sau.

## 2. LSP-first localization + ToolRuntime metadata convergence

Lý do:

- capability đã tồn tại;
- không cần thêm public tool;
- có thể giảm search/read/context;
- giúp candidate packet chính xác hơn.

## 3. Composite Read Plan + model-free context projection

Lý do:

- trực tiếp nhắm vào model↔tool round-trip và model-visible bytes;
- tận dụng typed execution/session/output primitives hiện có;
- có thể tạo bước nhảy performance/cost lớn hơn việc chỉ đổi prompt/model.

Sau đó mới đẩy mạnh Routing v2 và safe parallelism.

---

# 31. Final assessment

## 31.1 Dự án hiện tại đang ở đâu

Tools-Codex-web không phải một MCP wrapper sơ khai cần “cài thêm plugin architecture”. Nó đã có:

- authority model rõ;
- EOCL;
- bounded candidate methodology;
- adaptive routing;
- proof/idempotency/capsule;
- structured execution;
- durable jobs;
- LSP read-only;
- compact public façade.

Đó là nền tốt.

## 31.2 Điểm yếu hiện tại

Nền tảng mạnh nhưng có dấu hiệu **coordination tax**:

- control-plane/path/cwd defect có thể làm đảo ngược routing economics;
- telemetry chưa tách đủ phase;
- idempotency coverage trên trace hiện còn thấp dù semantics đã đúng;
- runtime metadata còn phân tán giữa các layer;
- LSP đã tồn tại nhưng chưa được chứng minh là first-class localization path trong Smart workflow;
- tool round-trip/context projection còn dư địa lớn;
- output/artifact/session evidence chưa có một retrieval/reference contract hoàn toàn thống nhất;
- concurrency ở job level đã có nhưng semantic safe parallelism chưa thành first-class planner concept.

## 31.3 DeepSeek Harness giúp ở đâu

DeepSeek Harness hữu ích nhất như một **pattern catalog** cho:

```text
execution pipeline
service/provider separation
bounded code/composite execution
session query
model-free compaction
spill/reference
concurrency metadata
presentation intent
```

Nhưng Tools-Codex-web nên chỉ lấy các seam còn thiếu.

## 31.4 Phương án tối ưu nhất

Phương án tối ưu nhất không phải rewrite.

Nó là:

> **Converge existing ToolRuntime/ToolSpec/EOCL/Runner primitives thành một execution pipeline có telemetry rõ; loại bỏ control-plane false failures; đưa LSP vào localization; giảm round-trip bằng bounded composite read execution; giảm context bằng session query + model-free projection/reference; sau đó route theo expected accepted-result economics và song song hóa chỉ phần safe.**

Nếu làm đúng thứ tự này, dự án có cơ hội cải thiện đồng thời:

```text
lower credits
lower latency
higher first-pass acceptance
lower tail/replan
lower context pressure
better observability
simpler authority reasoning
```

mà không phải đánh đổi:

```text
proof quality
authority safety
Smart-v3 simplicity
```

---

# 32. Implementation acceptance checklist

Trước khi gọi một wave là production-ready:

- [ ] current HEAD/worktree được pin trong benchmark;
- [ ] baseline trước thay đổi tồn tại;
- [ ] chỉ một optimization dimension chính được A/B;
- [ ] first-pass acceptance không giảm ngoài confidence bound đã chấp nhận;
- [ ] critical defect = 0;
- [ ] false-green proof = 0;
- [ ] authority/write tests pass;
- [ ] Smart-v3 fingerprint không drift ngoài ý muốn;
- [ ] model-visible bytes được đo;
- [ ] credits/accepted được đo, không chỉ credits/call;
- [ ] TTA p50/p90 được đo;
- [ ] warm/cold cohorts tách riêng;
- [ ] control-plane failures không bị gán cho model;
- [ ] fallback count được ghi;
- [ ] proof reuse chỉ khi fingerprint exact;
- [ ] no new generic framework nếu chưa có concrete second use case;
- [ ] rollback path rõ;
- [ ] no commit/push/deploy/restart chỉ để “hoàn thành benchmark” nếu chưa được phép.

---

# 33. Tài liệu nội bộ nên dùng làm baseline khi triển khai

1. `docs/research/260814_EXECUTION_HUB_LIVE_BENCHMARK_HIEU_SUAT_CHI_PHI.md`
2. `docs/research/2026-08-14_POST_P1_FOLLOWUP_TRACKER.md`
3. `docs/research/2026-08-14_RUNTIME_ACTIVATION_AND_PRODUCTION_TELEMETRY_LOG.md`
4. `docs/research/CONTEXT_TUNNEL_LONGHORIZON_ANALYSIS_2026-08-14.md`
5. `docs/research/ORCHESTRATION_METHODOLOGY_EXPERIMENTS_AND_PRODUCTION_DECISION_2026-08-12.md`
6. `docs/research/PFM_ORCHESTRATION_RUNTIME_POSTMORTEM_AND_ENFORCED_CONTROL_LOOP_RESEARCH_2026-08-13.md`
7. `.coding-tools/performance.json` — dynamic trace, chỉ dùng với timestamp/snapshot context.

DeepSeek reference:

```text
https://github.com/deepseek-ai/deepseek-harness
```

---

# 34. One-line production principle

```text
OPTIMIZE THE COST OF A CORRECT ACCEPTED RESULT,
NOT THE PRICE OF AN INDIVIDUAL MODEL CALL.
```

Với Tools-Codex-web, con đường có ROI cao nhất hiện tại là:

```text
control-plane correctness
-> measured execution pipeline
-> semantic localization
-> composite read execution
-> context/reference economy
-> accepted-result routing
-> safe parallelism
```

chứ không phải:

```text
more tools
+ more agents
+ stronger models
+ more retries
```
