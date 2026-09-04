# Coding-web Token Usage, Cost, Context Observability and Accepted-Result Efficiency Master Plan

**Ngày:** 2026-09-01  
**Revision:** 3 — ChatWeb Measurement Completeness Gate + Verified Execution Status  
**Workspace:** `E:\DEV\Codex-web`  
**Git HEAD tại lần cập nhật:** `30b7d1b971b65034d3e4c95568c970fcc0e9380c`  
**Runtime quan sát:** Coding Tools MCP `0.4.3`, profile `smart-v3`, public tool count `8`  
**Trạng thái tài liệu:** Implementation master plan / research-to-execution contract / verified execution status  
**Phạm vi:** End-to-end token accounting cho ChatWeb/controller, provider/model, MCP tool invocation, tool-context contribution, cost, RUN/WAVE economics, Dashboard, budget control và acceptance evidence.  

---

# 0. Revision 2 — quyết định kiến trúc bắt buộc trước triển khai

Revision này sửa một điểm trọng yếu của bản kế hoạch ban đầu.

Bản cũ tập trung đúng vào việc hợp nhất `UsageEvent`, provider telemetry, tool telemetry, EOCL và Dashboard, nhưng vẫn có nguy cơ đạt trạng thái:

```text
MCP/provider telemetry = tốt
Dashboard               = đẹp
ChatWeb controller usage = chưa quan sát đầy đủ
```

Nếu như vậy thì sản phẩm **chưa giải quyết yêu cầu thực tế**.

Yêu cầu sản phẩm cuối cùng không phải:

> “Codex-web đo được token phía MCP/provider.”

Mà là:

> **“Codex-web phải đo, phân loại, đối soát và kiểm soát được lượng token/cost/context mà toàn bộ quá trình làm việc trên ChatWeb tạo ra, từ controller turn đến MCP tool, delegated provider/model và accepted result.”**

Do đó Revision 2 đặt thêm một **P0 — ChatWeb Measurement Completeness Gate** trước mọi tối ưu Dashboard hoặc budget.

## 0.1 Quy tắc closure mới

Workstream bị cấm gọi là `DONE`, `CLOSED`, `FULL TOKEN ACCOUNTING` hoặc tương đương nếu chỉ chứng minh được provider/MCP usage mà chưa chứng minh được ChatWeb/controller usage.

Closure phải phân biệt rõ các mức:

```text
L0  TOOL INVENTORY ONLY
    biết 8 MCP tools; không nói được token.

L1  MCP / TOOL OBSERVABILITY
    biết call count, timing, bytes, model-visible bytes.

L2  PROVIDER MODEL ACCOUNTING
    biết provider/model input/output/cache/reasoning/cost có provenance.

L3  CHATWEB CONTROLLER ACCOUNTING
    biết exact controller usage theo turn/session với provenance.

L4  END-TO-END EXECUTION ECONOMICS
    controller + provider + tool + RUN/WAVE + acceptance được correlation,
    có non-overlap semantics, coverage và budget control.
```

**Mục tiêu của chương trình này là L4.**

Nếu upstream ChatWeb không expose một metric exact nào đó, hệ thống phải báo typed limitation và giữ `unknown`; không được tự nâng claim lên L4 bằng estimation.

## 0.2 Điểm phân biệt phải khóa

Ba khái niệm sau không được trộn:

```text
tools/list
    = inventory/capability contract của 8 MCP tools

provider/model tokens
    = usage do model/provider báo cho model request

tool-call card tokens
    = số token host UI gắn lên một invocation/card nếu host có structured receipt
```

Ví dụ các card kiểu:

```text
Tool call agent_workflow   64,143 tokens
Tool call agent_workflow   93,181 tokens
Tool call exec_command        895 tokens
```

không phải output của MCP `tools/list`.

`tools/list` chỉ trả lời:

```text
Có tool nào?
Schema nào?
Contract SHA nào?
Tool count bao nhiêu?
```

Nó không phải token meter.

## 0.3 P0 existential question

Trước khi sửa accounting sâu, phải trả lời bằng proof:

> **ChatWeb/Coding-VP host có structured machine-readable usage receipt cho controller turn và/hoặc tool-call card hay không, và receipt đó có thể được truyền xuống Coding-web bằng connector/tunnel contract chính thức không?**

Nếu `YES`:

```text
Host exact receipt
    -> ChatWeb Usage Bridge
    -> durable ledger
    -> correlation
    -> analytics
    -> Dashboard
```

Nếu `NO`:

```text
controller exact usage = unobserved
exact tool-card tokens  = unobserved
```

và workstream phải báo rõ upstream capability gap; không dùng OCR, DOM scraping, `bytes/4`, text length hay model guess để giả exact usage.

---

# 1. Executive conclusion

Coding-web **không cần xây telemetry từ đầu**. Source/runtime hiện đã có nhiều primitive quan trọng:

- `UsageEvent` cho model/provider economics;
- OpenCode/provider telemetry ingress;
- Codex bridge token/cost primitives;
- input/cached/uncached/output/reasoning token fields;
- provider-reported và pricing-derived cost;
- performance trace cho tool calls, request/response bytes, model-visible bytes, timing, cache/dedup;
- EOCL RUN/WAVE ledger và accepted-result semantics;
- evaluation contract có optional controller usage fields;
- bounded analytics/read-model infrastructure;
- Dashboard đã có một số nhánh `canonical` và `unknown_not_zero`.

Nhưng hệ thống hiện vẫn thiếu một **measurement authority graph** xuyên suốt ChatWeb → controller → MCP → provider → EOCL → accepted result.

Vì vậy vấn đề không phải “đếm thêm một con số token”. Vấn đề là xây một **Token & Execution Economics Control Plane** có đủ:

```text
AUTHORITY
PROVENANCE
CORRELATION
COVERAGE
NON-OVERLAP
BUDGET CONTROL
ACCEPTED-RESULT ECONOMICS
```

Target architecture:

```text
                    CHATWEB / CONTROLLER HOST
                              │
                  structured usage receipts
                              │
                              ▼
                    ChatWeb Usage Bridge
                              │
             ┌────────────────┼────────────────┐
             │                │                │
             ▼                ▼                ▼
     ControllerUsage     ToolCallReceipt   Turn/Trace identity
             │                │                │
             └──────────────┬─┴────────────────┘
                            ▼
                     Canonical Usage Plane
                            ▲
                            │
             Provider/model exact usage
                            │
                MCP / OpenCode / Codex bridge
                            │
        ┌───────────────────┼──────────────────┐
        ▼                   ▼                  ▼
 Provider Usage      ToolInvocationEvent     EOCL RUN/WAVE
        │                   │                  │
        └───────────────────┴─────────┬────────┘
                                      ▼
                         Economics / Efficiency Projector
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
                Dashboard        Budget Gate       Evaluation
```

Nguyên tắc số 1:

> **Không có exact measurement thì canonical value là `unknown`, không phải `0`, không phải `bytes/N`, và không được lấy một measurement plane khác để giả thay.**

---

# 2. Product finish line

Sau khi hoàn thành, operator phải trả lời được các câu hỏi sau cho **một phiên ChatWeb thật**.

## 2.1 ChatWeb/controller consumption

- Turn hiện tại dùng bao nhiêu input token?
- Bao nhiêu input là cached?
- Bao nhiêu output token?
- Bao nhiêu reasoning token nếu host/provider expose?
- Session hiện tại tổng bao nhiêu token?
- Token đó có `client_reported`, `provider_reported`, `estimated` hay `unobserved`?
- Coverage exact của ChatWeb session là bao nhiêu?

## 2.2 Provider/model consumption

- Model/provider nào được gọi?
- Input/cached/uncached/output/reasoning bao nhiêu?
- Cost provider-reported hay pricing-derived?
- Có duplicate/double-count do retry, delegated route hay terminal telemetry không?

## 2.3 Tool/context consumption

- Cả 8 public MCP tools được gọi bao nhiêu lần?
- Invocation nào trả payload lớn nhất?
- `model_visible_bytes` của từng invocation là bao nhiêu?
- p50/p95 latency của từng tool?
- Tool nào tạo context amplification?
- Host có exact tool-card token receipt cho invocation đó không?
- Nếu có, ledger/UI có giữ đúng con số card không?

## 2.4 Causal economics

- Một user objective tiêu bao nhiêu token/cost/thời gian từ đầu đến accepted checkpoint?
- Bao nhiêu token nằm ở controller?
- Bao nhiêu ở delegated provider/model?
- Bao nhiêu tool/context overhead?
- Bao nhiêu bị tiêu trong REPLAN/rejected waves?
- Route/model nào cho cost per accepted result thấp hơn?

## 2.5 Control

- RUN còn bao nhiêu budget?
- Có vượt soft/hard token/cost budget không?
- Context pressure của tool có vượt giới hạn không?
- Khi exact usage mất measurement, budget state có chuyển `indeterminate` thay vì giả còn dư không?

---

# 3. Current source-grounded baseline

## 3.1 Runtime/tool contract

Runtime quan sát tại lần cập nhật:

```text
profile: smart-v3
public tool count: 8
tool contract SHA:
  c244ed297f707f9df48c1e5d6c7e204693f281a755c2e6344bde78e94abb8251
```

8 public tools:

```text
workspace_context
agent_workflow
task_control
document_workflow
exec_command
command_control
request_permissions
view_image
```

`tools/list`/tool contract là inventory authority cho 8 tool này, **không phải token authority**.

## 3.2 Provider/model usage primitives

Các vùng source hiện có:

```text
resources/coding-tools-mcp/coding_tools_mcp/usage_events.py
resources/coding-tools-mcp/coding_tools_mcp/usage_pricing.py
resources/coding-tools-mcp/coding_tools_mcp/codex_bridge.py
resources/coding-tools-mcp/coding_tools_mcp/live_control.py
electron/services/hubProxyGateway.js
```

Các field đã xuất hiện trong measurement paths/tests:

```text
input_tokens
cached_input_tokens
uncached_input_tokens
output_tokens
reasoning_output_tokens
cache_read_tokens
cache_write_tokens
provider_cost
provider_ms
```

Đây là nền tốt để harden, không nên thay bằng telemetry framework khác.

## 3.3 Controller ingress primitive đã tồn tại nhưng chưa đủ chứng minh production completeness

Current tool contract có optional evaluation fields:

```text
evaluation.controller.input_tokens
evaluation.controller.cached_input_tokens
evaluation.controller.output_tokens
evaluation.controller.reasoning_output_tokens
evaluation.controller.monetary_cost
evaluation.controller.source = client_reported | provider_reported
```

Điều này chứng minh hệ thống đã có **một contract shape để nhận controller usage khi caller cung cấp**.

Nhưng nó **không đồng nghĩa** với:

```text
ChatWeb tự động gửi usage cho mọi turn
```

hoặc:

```text
MCP biết exact số token trên mọi Tool call card
```

P0 phải chứng minh hai điều đó bằng runtime receipt thực, không suy diễn từ schema.

## 3.4 Tool/performance telemetry

`.coding-tools/performance.json` và performance trace hiện có các primitive:

```text
tool_calls
errors
request_bytes
response_bytes
model_visible_bytes
local_execution_ms
estimated_wait_ms
cache_hits
deduplicated_calls
run_metrics
```

Các field này là **runtime measured context/tool telemetry**.

Chúng không tự trở thành token count.

## 3.5 Dashboard ambiguity hiện tại

`renderer/dashboard.js` đã có canonical branches, nhưng legacy/fallback paths vẫn có thể sử dụng heuristic tương tự:

```text
tokensFromBytes()
model_visible_bytes / bytesPerToken
```

Heuristic này chỉ được giữ nếu đổi semantic thành explicit context estimate; không được đi vào canonical token/cost KPI.

---

# 4. Measurement authority hierarchy

Mỗi metric phải có source authority riêng.

## 4.1 Canonical provenance vocabulary

```text
provider_reported
client_reported
runtime_measured
derived
estimated
unobserved
```

| Provenance | Ví dụ | Canonical cho gì? |
|---|---|---|
| `provider_reported` | model API usage | Model/provider usage |
| `client_reported` | ChatWeb/controller exact receipt | Controller/tool-card plane |
| `runtime_measured` | bytes, timing, call count | Tool/context telemetry |
| `derived` | cost từ exact token + versioned price | Derived cost |
| `estimated` | tokenizer/bytes ratio | Planning/context estimate only |
| `unobserved` | upstream không gửi receipt | Không có canonical value |

## 4.2 Missing policy

Bắt buộc:

```text
missing_measurement_policy = unknown_not_zero
```

Không có receipt:

```text
value = null
measurement = unobserved
```

Không:

```text
value = 0
```

trừ khi source authority thực sự báo zero.

## 4.3 No cross-plane substitution

Cấm:

```text
controller token missing
    -> dùng provider token thay
```

Cấm:

```text
tool-card token missing
    -> model_visible_bytes / 4
```

Cấm:

```text
provider token missing
    -> lấy tool-card token làm provider input
```

Mỗi plane có coverage riêng.

---

# 5. P0 — ChatWeb Measurement Completeness Gate

Đây là wave đầu tiên bắt buộc sau tài liệu này.

## 5.1 Objective

Chứng minh bằng runtime evidence exact đường dữ liệu:

```text
ChatWeb/controller host
    -> structured usage event/receipt
    -> connector/tunnel
    -> Coding Tools MCP ingress
    -> durable ledger
```

Không sửa Dashboard trước khi gate này rõ.

## 5.2 Questions phải trả lời bằng source/runtime proof

1. ChatWeb host có expose token usage cho controller turn bằng structured API/metadata/callback không?
2. Usage xuất hiện trước call, trong call request, trong tool response acknowledgement hay ở post-turn callback?
3. Có `turn_id`, `trace_id`, `invocation_id` hoặc identity tương đương không?
4. `cached_input_tokens` semantics là subset hay additive?
5. Host có expose exact Tool call card token count không?
6. Tool card token count có semantics gì: serialized tool result, context contribution, request+result, hay UI-specific accounting?
7. Connector/tunnel hiện có điểm extension chính thức để chuyển receipt về MCP không?
8. Có thể ingest mà không thêm public MCP tool thứ 9 không?
9. Có retry/idempotency identity để tránh duplicate receipt không?
10. Có privacy constraint nào cấm lưu một phần metadata không?

## 5.3 Preferred bridge contract

Nếu host support structured usage, target event:

```text
ChatWebUsageReceipt
  schema_version
  receipt_id
  observed_at

  identity
    endpoint_id
    workspace_id
    task_context_id
    session_id
    turn_id
    trace_id
    invocation_id?        # optional khi receipt gắn tool call

  actor
    controller = chatweb
    model_id?
    provider_id?

  usage
    input_total_tokens
    input_cached_tokens
    input_uncached_tokens?
    output_total_tokens
    output_reasoning_tokens?
    total_tokens?

  cost
    monetary_cost?

  tool_card
    tool_name?
    token_count?
    semantics?

  provenance
    usage = client_reported | provider_reported
    tool_card = client_reported | unobserved

  raw_source_identity
    source_event_id
    contract_version
```

Không lưu prompt, response content hay private chain-of-thought.

## 5.4 Bridge transport principles

Bridge phải:

- dùng connector/tunnel contract chính thức;
- append/ingest idempotently;
- giữ exact original number;
- version semantics;
- correlate bằng IDs, không bằng timestamp gần nhau;
- không scrape giao diện text như source of truth;
- không thêm public MCP tool nếu internal observation/metadata channel đủ;
- không block interactive tool execution vì analytics write chậm;
- fail safely nếu ledger ingestion tạm lỗi.

## 5.5 P0 gate outcomes

### Outcome A — Exact bridge supported

Gate PASS khi có ít nhất một representative ChatWeb turn chứng minh:

```text
Host receipt input = X
Ledger input       = X
Dashboard/read model = X
```

và nếu host expose tool-card token:

```text
Host Tool call token = Y
Ledger Y              = Y
UI Y                  = Y
```

### Outcome B — Controller usage supported, tool-card token unsupported

Có thể tiếp tục full controller accounting, nhưng:

```text
tool_card_token_coverage < 100%
unsupported field = explicit
```

Không dùng estimator thay exact card token.

### Outcome C — Host không expose controller usage

Đây là **upstream capability blocker** cho claim “đo toàn bộ ChatWeb token”.

System vẫn có thể đạt provider/MCP observability, nhưng mức capability chỉ được gọi L2, không L4.

Phải trả typed outcome kiểu:

```text
CHATWEB_CONTROLLER_USAGE_UNAVAILABLE
```

và tài liệu/roadmap phải ghi dependency cần thay đổi ở host/client contract.

## 5.6 Forbidden shortcuts

Không dùng:

```text
OCR screenshot
DOM text scraping
bytes / 4
chars / N
rough tokenizer without exact model semantics
copy con số operator nhìn thấy bằng tay
```

để tạo canonical ChatWeb usage.

Tokenizer local có thể tồn tại dưới:

```text
context_estimate
```

nhưng luôn tách plane và provenance.

---

# 6. Measurement completeness model

Mỗi session/RUN phải có coverage vector, không chỉ một phần trăm chung.

```text
MeasurementCoverage
  controller_turns_total
  controller_turns_exact
  provider_requests_total
  provider_requests_exact
  tool_invocations_total
  tool_invocations_traced
  tool_card_receipts_total
  tool_card_receipts_exact
  run_attribution_total
  run_attribution_exact
```

Derived:

```text
controller_usage_coverage
provider_usage_coverage
tool_invocation_coverage
tool_card_token_coverage
exact_run_attribution_coverage
```

Ví dụ:

```text
ChatWeb controller       100.0% exact
Provider usage            97.8% exact
Tool invocation          100.0% traced
Tool-card tokens          74.1% exact
RUN attribution           99.2% exact
```

Một tổng token phải đi cùng coverage.

---

# 7. Canonical UsageEvent vNext

Current `UsageEvent` được evolve, không thay thế.

## 7.1 Logical schema

```text
UsageEvent
  schema_version
  usage_id
  observed_at
  terminal_at

  identity
    workspace_id
    task_context_id
    session_id
    task_id
    run_id
    wave_id
    delegation_id
    request_id
    dispatch_id
    trace_id
    turn_id

  actor
    principal_id
    actor_kind        # controller | provider | delegated_model
    controller_id
    provider_id
    model_id
    route_requested
    route_resolved

  usage
    input_total_tokens
    input_cached_tokens
    input_uncached_tokens
    input_cache_creation_tokens
    output_total_tokens
    output_reasoning_tokens
    total_tokens

  cost
    provider_cost_usd
    client_reported_cost_usd
    derived_cost_usd
    kind
    pricing_revision

  timing
    queue_ms
    dispatch_transport_ms
    provider_ms
    first_token_ms
    total_ms

  provenance
    usage
    cost
    provider_timing
    total_timing

  attribution
    status              # exact | partial | unassigned

  deduplication
    source_event_id
    fingerprint
```

## 7.2 Input semantics

Khi provider/host semantics xác nhận:

```text
input_total = input_cached + input_uncached
```

Nếu không xác nhận, không tự suy component còn thiếu.

## 7.3 Reasoning semantics

Reasoning token là component/subset theo provider semantics; không cộng mù vào output total.

## 7.4 Cost precedence

Trong cùng economic event:

```text
provider_reported
    > client_reported exact cost
    > pricing_derived
    > unobserved
```

Không cộng measured và derived copy của cùng consumption.

## 7.5 Deduplication

Retry/reconnect không được tạo thêm economic contribution.

Dedupe identity phải dựa trên stable source receipt/dispatch ID, không chỉ timestamp.

---

# 8. ControllerUsageEvent

Production accounting cần event riêng hoặc actor-qualified `UsageEvent` cho ChatWeb controller.

Logical form:

```text
ControllerUsageEvent
  schema_version
  receipt_id
  session_id
  task_context_id
  turn_id
  trace_id
  run_id?
  wave_id?

  model_id?
  provider_id?

  input_total_tokens
  cached_input_tokens
  uncached_input_tokens?
  output_tokens
  reasoning_output_tokens?
  monetary_cost?

  source
  observed_at
  attribution_status
```

Nếu host không gửi:

```text
status = unobserved
```

Không phải zero.

---

# 9. ToolInvocationEvent

Provider usage trả lời “model tiêu bao nhiêu”. Tool event trả lời “tooling tạo bao nhiêu overhead/context pressure”.

```text
ToolInvocationEvent
  schema_version
  invocation_id

  identity
    workspace_id
    task_context_id
    session_id
    task_id
    run_id
    wave_id
    trace_id
    turn_id
    span_id

  tool
    name
    operation_or_action
    risk_class
    mutation_class

  timing
    started_at
    finished_at
    duration_ms
    wait_before_ms
    clock_domain

  payload
    request_bytes
    response_bytes
    model_visible_bytes
    retained_result_bytes

  result
    ok
    error_class
    truncated
    continuation_offered
    continuation_used
    cache_hit
    deduplicated

  exact_tool_card_receipt
    token_count
    source
    semantics
    observed_at
```

## 9.1 Coverage

100% public tool calls phải có invocation identity/trace, kể cả khi token usage unobserved.

```text
workspace_context
agent_workflow
task_control
document_workflow
exec_command
command_control
request_permissions
view_image
```

## 9.2 Binary/image path

`view_image` bytes không được đưa qua text token heuristic và gọi là exact token.

---

# 10. Exact ToolCallTokenReceipt

Nếu P0 chứng minh host expose con số card, tạo/ingest receipt:

```text
ToolCallTokenReceipt
  schema_version
  receipt_id
  session_id
  turn_id
  trace_id
  invocation_id
  tool_name
  token_count
  semantics
  source = client_reported
  observed_at
```

Invariant:

```text
host receipt Y == ledger Y == UI Y
```

Nếu không có:

```text
Exact tool-card tokens: —
Reason: client receipt unavailable
```

Không cộng ToolCallTokenReceipt vào provider total trừ khi contract chứng minh non-overlap.

---

# 11. Correlation graph

Canonical hierarchy:

```text
Workspace
  └─ ChatWeb Session
      └─ Turn
          ├─ ControllerUsageEvent
          ├─ ToolInvocationEvent
          │   └─ ToolCallTokenReceipt?
          └─ TaskContext
              └─ Task
                  └─ RUN
                      └─ WAVE
                          ├─ delegation/provider UsageEvent
                          ├─ proof
                          ├─ accept/reject/replan
                          └─ checkpoint
```

Exact linkage keys:

```text
workspace_id
session_id
turn_id
trace_id
invocation_id
task_context_id
run_id
wave_id
delegation_id
dispatch_id
request_id
```

Không canonical-attribution bằng “timestamp gần nhau”.

Attribution state:

```text
exact
partial
unassigned
```

---

# 12. Non-overlap accounting model

Đây là phần quyết định tổng có đúng hay không.

## 12.1 Không tạo một `total_tokens` toàn hệ thống khi chưa biết overlap

Ví dụ:

```text
controller input tokens
provider input tokens
tool-card context tokens
```

có thể biểu diễn cùng content ở các tầng khác nhau.

Không được cộng cả ba rồi gọi “Total”.

## 12.2 Tách totals theo plane

UI/API giữ riêng:

```text
controller_tokens
provider_tokens
tool_card_tokens
context_bytes
```

Chỉ tạo:

```text
non_overlapping_system_tokens
```

nếu contract có formal composition rule.

## 12.3 Cost cũng tương tự

```text
provider_cost
controller_cost
```

chỉ cộng thành system cost khi proven disjoint.

Nếu chưa rõ:

```text
total_system_cost = null
measurement = incomplete
```

---

# 13. Accepted-result economics

Mục tiêu của Coding-web là tối ưu accepted outcome, không tối thiểu token một cách mù quáng.

## 13.1 Denominator

Accepted result dựa trên durable EOCL:

```text
RUN accepted
orchestration CHECKPOINTED
```

không chỉ test pass.

## 13.2 Per-RUN economic ledger

```text
controller_usage
provider_usage
tool_invocation_count
tool_context_bytes
tool_card_exact_tokens_when_available
provider_cost
controller_cost
wall_clock_time
proof_time
wave_count
replan_count
failed_wave_count
accepted
coverage
```

## 13.3 Rework

Tài nguyên wave REPLAN/rejected vẫn được tính:

```text
rework_provider_tokens
rework_controller_tokens
rework_cost
rework_time
```

## 13.4 Core KPIs

```text
provider_tokens_per_accepted_result
controller_tokens_per_accepted_result
cost_per_accepted_result
time_to_accepted_result
rework_token_ratio
first_pass_acceptance_rate
cache_ratio
tool_context_bytes_per_accepted_result
operator_interventions_per_accepted_result
```

Không dùng một scalar tổng hợp để vượt correctness/safety gate.

---

# 14. Fast path vs analytics plane

Token feature không được làm tái phát UI lag.

## 14.1 Fast live projection

Chỉ bounded current state:

```text
current session/turn identity
current RUN/WAVE
recent usage delta
current coverage state
current budget/reservation state
active tool invocation summary
```

Không full history.

## 14.2 Analytics

Cadence độc lập, ví dụ khoảng 30 giây:

```text
usage_analytics(window)
controller_usage_analytics(window)
tool_context_analytics(window)
efficiency_analytics(window)
```

## 14.3 Bounded SQL

Queries bound theo indexed time/identity ranges.

Không:

```text
load whole ledger -> Python filter
```

Không N+1 per RUN.

---

# 15. Dashboard target

Dashboard phải phân biệt rõ bốn lớp.

## 15.1 CHATWEB CONTROLLER USAGE

Ví dụ:

```text
ChatWeb Session
Input                    2.81M   CLIENT-REPORTED
Cached                   1.94M   CLIENT-REPORTED
Uncached                 0.87M   DERIVED-EXACT*
Output                    184K   CLIENT-REPORTED
Reasoning                  62K   CLIENT-REPORTED
Controller coverage      100.0%

* chỉ khi host semantics cho phép exact decomposition
```

Nếu chưa có bridge:

```text
ChatWeb controller usage       —
Coverage                     0%
Reason     host receipt unavailable
```

Không fallback bytes/token.

## 15.2 PROVIDER/MODEL USAGE

```text
Provider
Model
Calls
Input total
Cached
Uncached
Output
Reasoning
Cost
Usage provenance
Cost provenance
Coverage
```

## 15.3 TOOL & CONTEXT

```text
Tool
Calls
p50/p95 duration
Request bytes
Response bytes
Model-visible bytes
Exact tool-card tokens
Tool-card receipt coverage
Truncation
Continuation
Cache/dedup
Errors
```

## 15.4 ACCEPTED-RESULT ECONOMICS

```text
RUN
Outcome
Waves
Replans
Controller tokens
Provider tokens
Provider cost
Controller cost
Tool calls
Context bytes
TTAR
Proof time
Coverage
```

## 15.5 Coverage panel là mandatory

```text
ChatWeb controller usage coverage
Provider usage coverage
Tool invocation coverage
Tool-card token coverage
Cost coverage
Exact RUN attribution
```

Không giấu coverage trong diagnostics.

---

# 16. Legacy bytes-to-token cleanup

## 16.1 `tokensFromBytes()`

Nếu còn dùng cho diagnostics, đổi semantics rõ:

```text
estimateContextTokensFromBytes()
```

Output chỉ vào:

```text
CONTEXT ESTIMATE
```

không vào canonical token total.

## 16.2 Legacy model/tool breakdown

Không render estimated attribution như model usage thật.

Khi không có exact usage:

```text
canonical token = —
context estimate = optional separate series
```

## 16.3 Cost from estimated bytes

Nếu cần scenario planning:

```text
scenario_context_cost_estimate
```

không đặt tên `cost` trần.

---

# 17. Budget and reservation control

Chỉ bật enforcement sau khi measurement authority và coverage đủ tốt.

## 17.1 Scopes

```text
workspace/day
session
task
RUN
WAVE
route
provider
model
tool
principal
```

## 17.2 Budget types

```text
controller token budget
provider token budget
provider cost budget
controller cost budget
wall-clock budget
tool-call count budget
model-visible context budget
result-size budget
replan budget
```

## 17.3 Unknown measurement

Nếu budget phụ thuộc exact usage nhưng receipt mất:

```text
budget_state = indeterminate
```

Policy:

```text
warn
require_reservation
block
```

Không dùng missing=0.

## 17.4 Reservation

Pre-dispatch:

```text
UsageReservation
  reservation_id
  run_id
  wave_id
  request_id
  provider/model
  estimated_input_tokens
  max_output_tokens
  reserved_total_tokens
  estimated_cost_upper_bound
  expires_at
```

Sau exact receipt:

```text
reservation -> reconcile(actual)
```

Reservation không phải actual usage.

---

# 18. Privacy, security and data minimization

Không cần lưu prompt/raw response để accounting token.

Cho phép:

```text
IDs
hashes
counts
timing
model/provider ID
typed status/error
pricing revision
sanitized provenance
```

Không lưu:

```text
secret
credential
bearer token
raw private prompt
raw model response chỉ vì telemetry
private chain-of-thought
```

ChatWeb bridge phải truyền structured usage metadata, không nội dung hội thoại nếu không cần.

---

# 19. Schema evolution

## 19.1 Additive first

Ưu tiên:

```text
new nullable fields
versioned event payload
new focused tables only when needed
```

Không sửa SQLite thủ công.

## 19.2 Logical records

```text
usage_events                    # existing/hardened
controller_usage_events         # new or actor-qualified UsageEvent
chatweb_usage_receipts          # optional depending bridge shape
tool_invocation_events          # durable correlated invocation plane
exact_tool_token_receipts       # only if upstream exact receipt exists
usage_reservations              # later control phase
budget_events                   # later control phase
```

## 19.3 Index candidates

Chỉ thêm theo query-plan evidence:

```text
(observed_at)
(session_id, observed_at)
(turn_id)
(trace_id)
(invocation_id)
(run_id, observed_at)
(wave_id, observed_at)
(tool_name, observed_at)
(provider_id, model_id, observed_at)
```

---

# 20. Historical data policy

Không backfill estimate thành exact measurement.

Được phép:

```text
exact historical provider/client receipts
```

Không được:

```text
model_visible_bytes / 4 -> provider token history
```

Historical chart phải cho thấy coverage theo thời gian để tránh so sánh sai trước/sau telemetry rollout.

---

# 21. Revised implementation program

Revision 2 thay đổi execution order. **Không bắt đầu bằng Dashboard. Không bắt đầu bằng budget. Không tuyên bố full accounting trước P0.**

---

## W0 — Measurement Semantics Freeze

### Objective

Khóa vocabulary, authority và non-overlap.

### Deliverables

- provenance taxonomy;
- `unknown_not_zero` contract;
- provider/controller/tool/tool-card separation;
- exact vs derived vs estimate typing;
- overlap rules;
- coverage schema;
- acceptance tests cho semantics.

### Gate

Không còn hai module hiểu `total token` theo hai cách khác nhau.

---

## W1 — P0 ChatWeb Usage Bridge Feasibility & Contract

### Objective

Trả lời existential question: có thể ingest exact ChatWeb/controller usage hay không.

### Work

- inspect connector/tunnel/client observation contract;
- locate structured usage metadata/callback if any;
- identify turn/session/invocation IDs;
- test exact controller usage receipt;
- test exact tool-card receipt separately;
- define internal ingress contract;
- prove idempotency/dedup requirements;
- record unsupported metrics explicitly.

### Gate A

Exact ChatWeb receipt round-trip được chứng minh.

### Gate B

Nếu upstream không expose, typed blocker được chứng minh và project capability level bị khóa ở L2 cho đến khi host contract thay đổi.

**Không được fake Gate A bằng estimate.**

---

## W2 — ChatWeb Controller Usage Ingestion

### Objective

Biến bridge thành durable production accounting.

### Work

- `ControllerUsageEvent` hoặc actor-qualified `UsageEvent`;
- session/turn/trace correlation;
- exact provenance;
- dedupe/reconnect safety;
- coverage computation;
- bounded current-session read model.

### Gate

Representative ChatWeb session có exact usage receipts được lưu và truy ra 1:1.

---

## W3 — Provider UsageEvent Hardening

### Objective

Mọi model/provider exact usage đi qua normalization path duy nhất.

### Work

- field normalization;
- cached/uncached semantics;
- reasoning semantics;
- provider cost precedence;
- pricing revision;
- dedupe terminal events;
- exact attribution status.

### Gate

Known provider fixture → ledger → analytics giữ nguyên exact values.

---

## W4 — ToolInvocationEvent Instrumentation

### Objective

100% public MCP tool calls có invocation trace.

### Work

- common wrapper/envelope;
- session/turn/task/RUN/WAVE identity;
- timing;
- request/response/model-visible bytes;
- cache/dedup/truncation/continuation;
- typed errors;
- no per-tool duplicate instrumentation when common wrapper suffices.

### Gate

Test matrix cho đủ 8 tools tạo đúng một invocation record/call.

---

## W5 — Exact Tool-Card Receipt Integration

### Objective

Nếu W1 chứng minh upstream support, ingest exact card token count.

### Work

- `ToolCallTokenReceipt`;
- invocation/turn identity;
- semantics version;
- coverage;
- no overlap with provider totals unless proven.

### Gate

Một known host value `Y` round-trip:

```text
Host Y = Ledger Y = UI Y
```

Nếu upstream không support, wave chuyển thành explicit unsupported-state implementation, không estimate.

---

## W6 — Correlation & Accepted-Result Economics

### Objective

Ghép ChatWeb/controller + provider + tool + EOCL.

### Work

- exact RUN/WAVE attribution;
- rework buckets;
- accepted result metrics;
- system-cost completeness state;
- coverage vector;
- bounded SQL aggregation.

### Gate

Synthetic/fixture RUN nhiều waves tính đúng final + rework + coverage.

---

## W7 — Dashboard Semantics Rewrite

### Objective

UI chỉ hiển thị precision mà evidence cho phép.

### Work

- ChatWeb Controller section;
- Provider/Model section;
- Tool & Context section;
- Accepted-result section;
- Coverage panel;
- provenance badges;
- remove canonical bytes→token fallback;
- unknown reason text.

### Gate

Không code path nào biến `model_visible_bytes/N` thành canonical provider/controller token KPI.

---

## W8 — Budget & Reservation Control

### Objective

Từ observability sang control.

### Work

- token/cost budget schema;
- soft warnings;
- reservation/reconciliation;
- context-size policy;
- replan budget;
- indeterminate handling;
- policy audit.

### Gate

Missing usage không thể làm budget tưởng rằng consumption = 0.

---

## W9 — Historical Migration & Longitudinal Analytics

### Objective

Khai thác history mà không rewrite provenance.

### Work

- exact-only backfill;
- preserve estimates as estimates;
- coverage-by-time;
- migration idempotency;
- large-ledger bounded query proof.

### Gate

No data loss, no false-measured history, acceptable analytics latency.

---

## W10 — Representative ChatWeb End-to-End Validation & Closure

### Objective

Chứng minh trên **một phiên ChatWeb thật**, không chỉ unit fixture.

### Required sequence

```text
User turn in ChatWeb
    -> controller usage receipt
    -> one or more MCP tool calls
    -> provider/delegated usage
    -> RUN/WAVE activity
    -> proof/acceptance
    -> CHECKPOINT
    -> Dashboard/ledger reconciliation
```

### Gate

Workstream chỉ CLOSED khi runtime evidence chứng minh supported measurement planes được loaded/working và capability level được công bố đúng.

---

# 22. Test strategy

## 22.1 Contract tests

- `tools/list` inventory không xuất hiện như token usage;
- provider/controller/tool-card schemas tách biệt;
- missing stays null/unknown;
- no cross-plane substitution;
- overlap rules explicit.

## 22.2 ChatWeb bridge tests

Known receipt:

```text
turn_id = T1
input = 64,143
cached = 48,000
output = 895
```

phải round-trip không đổi.

Test:

- duplicate receipt ignored/idempotent;
- reconnect không double-count;
- missing turn_id fails/partial attribution theo contract;
- unsupported host field stays unobserved;
- no raw prompt persistence.

## 22.3 Provider tests

Known provider receipt:

```text
input_total = 3,824
cached = 3,000
output = 14
reasoning = 4
provider_cost = 0.0042
```

phải giữ exact numbers và provider cost precedence.

## 22.4 Tool tests

Cả 8 public tools:

- stable invocation ID;
- exactly one invocation event;
- timing recorded;
- bytes recorded;
- truncation/continuation tracked;
- image/binary path không text-token-estimate như exact.

## 22.5 Tool-card receipt test

Nếu host supports:

```text
card token = 895
```

thì ledger/UI = 895.

Nếu host không supports:

```text
value = null
status = unobserved
```

## 22.6 Correlation tests

- turn → invocation → provider request → RUN/WAVE;
- rejected/replan wave usage không mất;
- unassigned event không gán vào RUN gần nhất bằng timestamp.

## 22.7 Dashboard tests

- exact ChatWeb usage rendered;
- provider usage rendered riêng;
- tool-card token separate;
- context bytes separate;
- coverage visible;
- unknown displays `—` plus reason;
- no canonical bytes/token fallback.

## 22.8 Performance tests

- fast polling bounded;
- analytics independent cadence;
- no full-history scan;
- no N+1;
- large ledger latency budget;
- no renderer timer/listener accumulation.

## 22.9 Runtime proof

Representative ChatWeb session phải đối soát raw structured receipts với ledger/read model/UI.

---

# 23. Non-negotiable acceptance gates

Workstream không được gọi là L4/CLOSED nếu thiếu các gate sau.

1. `tools/list` chỉ được dùng làm tool-contract inventory, không token meter.
2. P0 xác định bằng evidence ChatWeb controller usage có/không structured receipt.
3. Nếu supported, ChatWeb exact receipt round-trip host → bridge → ledger không đổi số.
4. Nếu unsupported, capability được báo `unobserved/typed blocker`, không estimate giả.
5. ChatWeb session/turn identity được correlation ổn định.
6. Provider exact input/output/cache/reasoning round-trip không đổi.
7. Cached input không double-count.
8. Reasoning component không double-count.
9. Provider cost precedence đúng.
10. Unknown usage/cost = null/`—`, không zero.
11. `model_visible_bytes` không lọt vào canonical provider/controller token KPI.
12. Cả 8 public tools có invocation telemetry 100% trên supported path.
13. Exact tool-card receipt nếu upstream expose phải match 1:1.
14. Nếu host không expose tool-card token, UI giữ unknown.
15. Provider/controller/tool-card planes không cộng thành system total nếu chưa có non-overlap proof.
16. RUN/WAVE correlation không dùng timestamp proximity như authority.
17. Replan/rejected-wave usage được tính trong rework.
18. Có provider tokens / accepted result.
19. Có controller tokens / accepted result khi controller coverage hỗ trợ.
20. Có cost / accepted result với completeness/provenance.
21. Có time to accepted result.
22. Measurement coverage vector là first-class UI/API field.
23. Analytics bounded theo window/indexed identity.
24. Fast live path không chạy full history/orchestration analytics.
25. Budget không coi missing usage là zero.
26. Reservation được reconcile với actual receipt.
27. Historical backfill chỉ promote exact measurements.
28. Telemetry không lưu secret/raw private prompt/private chain-of-thought.
29. Focused backend/renderer/bridge tests pass.
30. `git diff --check` pass cho implementation waves.
31. Runtime source revision được chứng minh current trước closure.
32. Representative **ChatWeb** E2E validation pass, không chỉ MCP canary.
33. EOCL implementation RUN/WAVE đạt required final acceptance/checkpoint.
34. Capability level cuối được công bố đúng L0–L4, không overclaim.

---

# 24. First implementation packet — revised

Bản cũ đề xuất bắt đầu bằng provider usage hardening. Revision 2 thay đổi thứ tự.

**Packet đầu tiên phải là W0 + W1 P0 feasibility**, vì nếu ChatWeb host không expose controller usage thì phải biết ngay trước khi đầu tư sâu vào Dashboard/budget.

## Objective

```text
Prove the exact ChatWeb usage boundary and freeze measurement semantics.
```

## Scope

Read/inspect trước:

```text
connector/tunnel ingress
MCP request metadata/_meta path
controller evaluation usage contract
host observation/turn binding
performance trace identity
UsageEvent ingestion
ChatWeb/Coding-VP Live runtime receipts available to connector
```

Chỉ mutate sau khi exact ingress seam được chứng minh.

## Required proof before first production write

1. xác định structured controller usage field có tồn tại hay không;
2. xác định stable turn/trace/session identity;
3. xác định exact tool-card token receipt có hay không;
4. xác định connector transport seam;
5. xác định idempotency key/source event identity;
6. không cần raw conversation payload;
7. xác định unsupported cases typed.

## Stop conditions

- host/client không expose structured usage;
- semantics token card không xác định;
- chỉ có UI text mà không có machine-readable receipt;
- cần raw credential/secret để quan sát;
- concurrent writer chạm cùng causal surface;
- schema change đòi destructive migration.

Nếu stop do upstream không expose usage, output phải là capability blocker + required host contract change, không phải patch ước lượng.

---

# 25. Candidate source map

Đây là candidate map, không phải lệnh sửa tất cả cùng lúc.

## ChatWeb/connector ingress

```text
ChatWeb/controller evaluation/observation ingress
MCP request metadata / _meta normalization
connector/tunnel client contract
electron/tunnel supervision surfaces nếu đó là nơi receipt đi qua
host turn-binding / observation correlation
```

## Backend accounting

```text
resources/coding-tools-mcp/coding_tools_mcp/usage_events.py
resources/coding-tools-mcp/coding_tools_mcp/usage_pricing.py
resources/coding-tools-mcp/coding_tools_mcp/orchestration_ledger.py
resources/coding-tools-mcp/coding_tools_mcp/performance_trace.py
resources/coding-tools-mcp/coding_tools_mcp/accepted_result_economics_report.py
resources/coding-tools-mcp/coding_tools_mcp/mcp_http_handler.py
resources/coding-tools-mcp/coding_tools_mcp/live_control.py
resources/coding-tools-mcp/coding_tools_mcp/codex_bridge.py
```

Potential focused modules chỉ khi causal need được chứng minh:

```text
controller_usage_events.py
chatweb_usage_bridge.py
tool_invocation_events.py
usage_accounting.py
budget_control.py
usage_reservations.py
```

## Provider/client

```text
electron/services/hubProxyGateway.js
OpenCode telemetry integration
Codex bridge
```

## Renderer

```text
renderer/dashboard.js
renderer/control-center.js
relevant HTML/CSS only when needed
```

---

# 26. Rollout

## Stage A — Shadow measurement

- ingest exact receipts;
- no behavior change;
- compare host/provider raw number ↔ ledger;
- report coverage;
- detect duplicate/overlap.

Không budget enforcement.

## Stage B — Operator visibility

- Dashboard exact usage;
- coverage badges;
- tool context pressure;
- accepted-result economics;
- unknown reasons.

## Stage C — Warning

- soft token/cost warnings;
- context size alerts;
- rework alerts.

## Stage D — Controlled enforcement

- reservations;
- hard provider cost cap;
- RUN token budget;
- tool result/context cap.

## Stage E — Routing feedback

Chỉ sau representative accepted-result evidence đủ mạnh mới đưa economics vào routing policy.

---

# 27. Scientific evaluation methodology

## 27.1 Baseline

Trước optimization ghi:

```text
source revision
runtime revision
ChatWeb controller coverage
provider coverage
tool invocation coverage
tool-card coverage
RUN attribution coverage
accepted-run count
provider tokens/cost
controller tokens/cost when observed
rework metrics
```

## 27.2 Representative workloads

```text
localized bugfix
cross-file feature
document/research
runtime recovery
UI/backend integration
high-risk acceptance
```

Không kết luận từ synthetic microbenchmark một mình.

## 27.3 Compare policies only under comparable conditions

```text
same task class
same oracle
same source class
known cache stratum
same acceptance standard
known measurement coverage
```

Nếu controller coverage khác nhau đáng kể, không kết luận route A rẻ hơn B chỉ từ provider usage.

## 27.4 Primary outcome

```text
accepted-result correctness first
then time/cost/token/rework
```

Không dùng token-saving đơn độc làm promotion gate.

---

# 28. Failure modes

## 28.1 False completeness

Provider telemetry xanh nhưng ChatWeb usage missing.

Mitigation:

```text
capability level L0-L4
mandatory controller coverage card
closure gate
```

## 28.2 Double-count

- provider terminal + delegated economics duplicate;
- cached input cộng ngoài total;
- tool-card token cộng với provider token;
- ChatWeb controller token cộng với provider token không có overlap proof.

Mitigation:

```text
stable receipt IDs
plane separation
non-overlap contract
provenance
```

## 28.3 False zero

Missing receipt bị `Number(x || 0)`.

Mitigation:

```text
nullable observed-number helpers
unknown_not_zero tests
```

## 28.4 UI-card scraping temptation

Con số card nhìn thấy nhưng không có structured receipt.

Mitigation:

Không scrape/OCR để làm canonical accounting. Yêu cầu host contract hoặc giữ unobserved.

## 28.5 Telemetry creates latency/context bloat

Không trả raw thousands of receipts vào fast poll.

Mitigation:

```text
bounded projections
pagination
SQL windows
analytics cadence independent
```

## 28.6 Pricing drift

Historical derived cost thay theo price hiện tại.

Mitigation:

```text
pricing revision stored per event
```

## 28.7 Connector reconnect duplication

Same host receipt ingest hai lần.

Mitigation:

```text
source_event_id + idempotency fingerprint
```

---

# 29. Explicit non-goals

Workstream này không nhằm:

- thêm MCP public tool mới chỉ để telemetry nếu internal ingress đủ;
- biến `tools/list` thành token accounting;
- scrape ChatGPT UI để giả exact usage;
- lưu raw prompt/response/private reasoning;
- gọi context byte estimate là provider token;
- cộng mọi plane thành một “total” không có overlap proof;
- route theo model rẻ bất chấp accepted quality;
- bật hard budget trước measurement coverage;
- rewrite toàn bộ ledger khi additive evolution đủ.

---

# 30. Definition of Done — revised

Workstream được coi là hoàn thiện ở mức mục tiêu L4 khi:

> **Coding-web có structured measurement bridge cho ChatWeb/controller trên supported environment; provider/model usage được normalized với provenance; 100% MCP public tool invocations được traced; exact tool-card receipt được ingest nếu host expose và giữ unknown nếu không; mọi event có causal identity đến session/turn/RUN/WAVE khi authority tồn tại; overlap được quản lý nên không double-count; accepted-result economics và measurement coverage được tính bounded; Dashboard không fabricate precision; budget dùng reservation/reconciliation; và representative ChatWeb runtime proof xác nhận exact receipts ↔ ledger ↔ UI khớp.**

Nếu upstream không expose controller usage, Definition of Done phải hạ claim rõ:

```text
L2 Provider/MCP Accounting COMPLETE
L4 ChatWeb End-to-End Accounting BLOCKED
reason = CHATWEB_CONTROLLER_USAGE_UNAVAILABLE
```

Không được gọi L2 là “toàn bộ ChatWeb token accounting”.

---

# 31. Target operator experience

Khi L4 supported:

```text
CHATWEB SESSION S-82F
────────────────────────────────────────────
Controller usage
  Input total              2,810,422  CLIENT-REPORTED
  Cached                   1,942,008  CLIENT-REPORTED
  Output                     184,112  CLIENT-REPORTED
  Reasoning                   62,431  CLIENT-REPORTED
  Coverage                    100.0%

Provider/model usage
  Input total                918,221  PROVIDER-REPORTED
  Cached                     604,330  PROVIDER-REPORTED
  Output                      71,201  PROVIDER-REPORTED
  Provider cost               $3.84  PROVIDER-REPORTED
  Coverage                     98.7%

MCP tools
  Public contract                 8  CONTRACT-REPORTED
  Calls                          127  RUNTIME-MEASURED
  Model-visible payload        8.4MB  RUNTIME-MEASURED
  Tool-card exact coverage     76.4%

Execution economics
  RUNs accepted                  11
  Replans                         3
  Provider token / accepted   89.9K
  Controller token / accepted 277.9K
  Cost / accepted              $0.35
  Median TTAR                   7m12s
────────────────────────────────────────────
```

Nếu ChatWeb bridge unsupported:

```text
ChatWeb controller usage           —
Coverage                           0%
Status         UPSTREAM UNOBSERVED
Reason         structured host receipt unavailable
```

Đó là truthful system behavior, không phải defect che bằng estimation.

---

# 32. Final recommendation before implementation

Triển khai theo thứ tự:

```text
W0 semantics freeze
    ↓
W1 P0 ChatWeb bridge feasibility
    ↓
W2 controller usage ingestion
    ↓
W3 provider normalization
    ↓
W4 tool invocation telemetry
    ↓
W5 exact tool-card receipt if supported
    ↓
W6 correlation + accepted-result economics
    ↓
W7 Dashboard
    ↓
W8 budgets
    ↓
W9 historical analytics
    ↓
W10 representative ChatWeb E2E closure
```

**Quyết định quan trọng nhất của Revision 2:**

> Không đầu tư tiếp vào một “token dashboard” trước khi chứng minh measurement boundary của ChatWeb. Nếu ChatWeb/controller exact usage không đi vào Codex-web, Dashboard dù chính xác ở provider/MCP plane vẫn chưa trả lời được câu hỏi người dùng cần: “toàn bộ công việc trên ChatWeb đã tiêu bao nhiêu token và có hiệu quả hay không?”

Do đó implementation packet tiếp theo phải bắt đầu bằng **W0 + W1**, không phải UI-first và cũng không phải budget-first.

---

# 33. Revision 3 — verified implementation status as of 2026-09-01

Phần này là durable execution status, không thay đổi measurement semantics của Revision 2. Mục tiêu là khóa ranh giới giữa phần đã có source/proof/checkpoint, phần chưa live-activate, và phần vẫn chưa được phép claim.

## 33.1 Accepted baseline carried forward

Các implementation baseline đã được durable acceptance:

```text
W1
  RUN   06a666f5d9fa4b4287614e599bc3f354
  WAVE  a4acc6d8ee2a4bb68ee1fb6b87bccc78
  proof d0cc70e5474344ca9d9e7530a0a45187
  proof 6a3889cc24654429a0372139ee0ad0c6
  state CHECKPOINTED

W2
  RUN   b3273e736aad4928a0631dcad65af8c2
  WAVE  8ea0be9cb8d2498d8661bda24d157fc4
  proof f1b0b0ce50714e869f38c5886c5c480c
  completion_report c669f6b31d43b066461a33b06608e4d665e3d0baff716808f8e92ba12e30c42b
  state CHECKPOINTED

W3 corrective
  RUN   e10a55eab39c4d9cbfddc37a48b58f8e
  WAVE  afe720d9cfdc41aaaf2bbc2155182bc5
  proof dbb6e8058a5144d8ada8d235b33b1576
  checkpoint 6bd72d7f283644f0a9783255ffb02740
  state CHECKPOINTED
```

W3 corrective là canonical semantic baseline. W3 cũ đã bị invalidate vì `PROVENANCE_ATTRIBUTION_FAIL_OPEN`; không được dùng acceptance cũ để overclaim attribution correctness.

## 33.2 W4 canonical lineage và blocker phát hiện trước source write

Canonical W4:

```text
RUN          393c55bf91c743988d65cb42ffffda9b
WAVE         a4f5bf9b89074d55b6cb399fb0a23ee3
task_context ctx_18c5f68da722f4789844de4ff18c5c7c
```

W4 source hiện vẫn **NOT IMPLEMENTED**.

Trong giai đoạn read-only localization, compact `TaskState` của context W4 bị một projection mới ghi đè/đẩy canonical projection vào history. Durable orchestration ledger của W4 vẫn còn nguyên, nhưng runtime pre-repair chỉ tìm exact RUN trong **current** TaskState. Kết quả là stateless caller có exact `run_id` nhưng không còn `task_context_id` không thể recover canonical W4 context từ history.

Một accidental duplicate no-write lineage đã được dừng:

```text
RUN    825b0d02075a4d5294e441bfceead65b
WAVE   446ddd10870e48f5934dfe894e067c66
report f811fd2f7b0438a159a9a64c943f16de28d652a695466ab72d7e0aa4a7d53f00
state  ABORTED / NOT_ACCEPTED
```

Duplicate này không có source write, lease hay proof và không phải authority để tiếp tục W4.

## 33.3 Exact-RUN continuity repair — source, proof và durable acceptance

Canonical repair lineage:

```text
RUN          1bfeefca31874860bc218d9f3041cca3
task_context ctx_6e56d788eae779051fff721c1efa2038
```

Wave đầu:

```text
WAVE   58c03cee6b8f4caba196e83f14b2c7ce
proof  ad01b669b4ba4d58856057766ff9dbdb
result REPLAN
reason oracle/workdir error before source mutation
report 802be4d6e3b256982ae2acfbd0830010b48332f81ebe19274eea5e5908f8e1a3
```

Wave corrective đã source-write và được accepted:

```text
WAVE        493ed8d7fbfb454d9351328b06350d08
write_lease 92cc8fc2a2af4554a33553e43f6417fd
proof       6593248c10ad426a9b16fc3fa9000c24
proof       PASS
checkpoint  44ce31aa6f5e463bbac4da347289f4c7
state       CHECKPOINTED
```

Durable acceptance evidence:

```text
seq 34156  quality_outcome_recorded, oracle_pass=true
seq 34157  ACCEPTING -> CHECKPOINTED
           reason=controller_acceptance
           checkpoint_id=44ce31aa6f5e463bbac4da347289f4c7
seq 34159  wave_processes_quiesced, active_command_count=0
```

Focused oracle:

```text
cwd:
  E:\DEV\Codex-web\resources\coding-tools-mcp

command:
  python -m unittest discover -s tests -p "test_stateless_http_2026.py"

result:
  PASS
```

`git diff --check` cũng PASS trên exact repair surface.

Exact five repaired files:

```text
resources/coding-tools-mcp/coding_tools_mcp/runtime_stateless_context.py
resources/coding-tools-mcp/coding_tools_mcp/projection_rebuild.py
resources/coding-tools-mcp/coding_tools_mcp/server.py
resources/coding-tools-mcp/coding_tools_mcp/coordination.py
resources/coding-tools-mcp/tests/test_stateless_http_2026.py
```

## 33.4 Semantic effect của repair

Repair khóa các invariant sau:

1. Exact stateless RUN lookup giữ current-projection path nhưng có thể consult bounded archived `TaskState` history.
2. Archived candidate chỉ hợp lệ khi đồng thời match canonical ledger `run_id` **và** canonical `task_id`.
3. Current conflicting compact projection chỉ được thay khi safely terminal, không có pending completion report và projected RUN không active.
4. `reconcile_task_orchestration_projection()` nhận optional `requested_run_id`; default path khi không có requested exact RUN giữ nguyên.
5. Exact recovery dùng `TaskStateStore.clear()` + `restore_from_ledger(...)`; canonical orchestration ledger không bị rewrite.
6. Refusal là fail-closed và typed, gồm active conflict, pending operator report, multiple matching contexts, foreign controller ownership và workspace mismatch.
7. Regression tests chứng minh archived recovery, active-conflict refusal và pending-report refusal; prior foreign-controller coverage được giữ lại.

Điểm quan trọng: checkpoint này chứng minh **source repair + focused proof + acceptance**, không tự động chứng minh process MCP đang chạy đã load source mới.

## 33.5 Activation gate trước khi tiếp tục W4

Current live runtime được quan sát trước repair activation với:

```text
activation_epoch_id activation-mthnnjtx-5cb1ab01a1f00eb512ee43997e56abae
process_instance_id B7uGenzNzfsTAr6t
server_instance_id  kRH95JpLsomF0PwZ
runtime              0.4.3
profile              smart-v3
public_tool_count    8
```

Do repair source được viết trong worktree sau khi process trên đã chạy, **không được suy ra code repair đã live-loaded**.

Gate bắt buộc trước W4 write:

```text
1. controlled restart/activation được operator phê duyệt rõ;
2. runtime mới có activation/process/server identity mới và source revision current;
3. exact stateless task_control call chỉ truyền canonical W4 run_id,
   KHÔNG truyền task_context_id;
4. runtime phải recover đúng:
     RUN          393c55bf91c743988d65cb42ffffda9b
     task_context ctx_18c5f68da722f4789844de4ff18c5c7c
5. không mint unrelated RUN/task projection;
6. controller ownership/lease guards vẫn fail-closed;
7. chỉ sau proof này mới resume W4 canonical lineage.
```

Không tự restart dưới một yêu cầu chung chung. Restart/activation là operational transition riêng và phải có explicit operator authorization.

## 33.6 W4 implementation contract sau activation

W4 vẫn giữ scope đã khóa:

- common structural tracing boundary quanh `Runtime.call_tool()`;
- đúng một `ToolInvocationEvent`/performance trace record cho mỗi public invocation;
- đủ 8 smart-v3 tools;
- trace cả early-return path;
- stable invocation identity theo transport identity;
- session/turn/task/RUN/WAVE/W3C correlation khi evidence tồn tại;
- runtime timing;
- measured request/response/model-visible bytes;
- cache/dedup/truncation/continuation states khi available;
- typed error outcome;
- **không có token field suy ra từ bytes**;
- không đổi public tool count 8;
- không lấn sang W5/Dashboard/budget/history.

Candidate implementation surface vẫn là:

```text
resources/coding-tools-mcp/coding_tools_mcp/server.py
resources/coding-tools-mcp/coding_tools_mcp/performance_trace.py
resources/coding-tools-mcp/coding_tools_mcp/mcp_http_handler.py
resources/coding-tools-mcp/tests/test_efficiency_runtime.py
```

Acceptance proof tối thiểu:

```text
- mỗi exact 8 smart-v3 tools increment trace đúng 1 lần;
- early activation-bootstrap return traced đúng 1 lần;
- same transport identity -> stable invocation ID;
- different request identity -> distinct invocation ID;
- correlation chỉ dùng existing content-free evidence;
- ToolInvocationEvent không fabricate token fields;
- tool contract vẫn đúng 8 tools.
```

## 33.7 Measurement completeness status không thay đổi bởi continuity repair

Control-plane repair là prerequisite để tiếp tục W4 an toàn; nó **không trả lời P0 existential question**.

Tại checkpoint này:

```text
W1 bridge/ingress contract primitives     IMPLEMENTED/CHECKPOINTED
W2 controller ingestion semantics         IMPLEMENTED/CHECKPOINTED
W3 provider/provenance hardening          IMPLEMENTED/CHECKPOINTED
exact-RUN continuity repair               IMPLEMENTED/CHECKPOINTED
W4 tool invocation instrumentation        NOT IMPLEMENTED
W5 exact tool-card receipt integration    NOT STARTED
W6-W10                                    NOT STARTED / gated
```

Và measurement claim vẫn phải giữ:

```text
ChatWeb automatic controller receipt emission  UNPROVEN
ChatWeb exact tool-card receipt                 UNPROVEN
controller/tool-card missing usage              unknown_not_zero
L4 end-to-end accounting                        NOT YET CLAIMABLE
```

Không được dùng bytes, OCR, DOM text, UI card copy, tokenizer guess hoặc provider usage của plane khác để lấp khoảng trống này.

## 33.8 Immediate next decision boundary

Current safe next boundary là **activation authorization**, không phải thêm patch W4 trên runtime chưa được chứng minh đã nạp continuity repair.

Sau khi activation gate PASS, chương trình quay lại canonical W4; sau W4 mới tiếp tục W5 theo capability evidence của P0. Nếu host không expose exact receipt, trạng thái phải tiếp tục là `unobserved/unknown_not_zero`, không overclaim L4.
