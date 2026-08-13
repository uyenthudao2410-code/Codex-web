# Runtime Activation & Production Telemetry Validation — 2026-08-14

## 0. Phạm vi và nguyên tắc bằng chứng

Workspace: `E:\Github\Tools-Codex-web`

Base HEAD quan sát: `d3c6f184b8f5b2b3f603615f0e5a3abb889b9d0c`

Mục tiêu của vòng này là triển khai activation protocol sau audit, restart/reconnect runtime một cách có kiểm soát, và đo lại các KPI theo denominator đúng để tránh lặp lại các kết luận quá mạnh từ simulation hoặc raw aggregate.

Báo cáo phân biệt bốn lớp bằng chứng:

1. **Live runtime measurement** — số đọc trực tiếp từ runtime/ledger sau activation.
2. **Deterministic integration test** — semantics được chứng minh bằng test trong runtime tạm, không đồng nghĩa production usage.
3. **Scenario simulation** — router production được gọi thật nhưng cost/probability là giả định explicit.
4. **Prior real-model evidence** — số liệu Codex thật từ báo cáo đã cung cấp; không chạy lại trong vòng này để tránh tiêu credits không cần thiết.

Không trộn bốn lớp này thành một KPI duy nhất.

---

## 1. Thay đổi measurement trước activation

### 1.1 Performance trace v3

`resources/coding-tools-mcp/coding_tools_mcp/performance_trace.py`

Bổ sung:

- `schema_version = 3`;
- `idempotency_eligible_calls`;
- `idempotency_eligible_key_calls`;
- `proof_cache_saved_ms`;
- bounded `run_metrics` tối đa 200 run;
- per-event `idempotency_eligible`;
- per-run tool calls, errors, local execution, wait proxy, request/response bytes, idempotency coverage, proof reuse và route/mode buckets.

Mục tiêu là sửa denominator. `idempotency_key_calls / all_tool_calls` không trả lời đúng câu hỏi vận hành. KPI mới là:

```text
idempotency_coverage =
  idempotency_eligible_key_calls / idempotency_eligible_calls
```

`eligible` chỉ gồm mutation hoặc execution đủ đắt/rủi ro để cần durable operation identity. Read-only observation/poll không pha loãng denominator.

### 1.2 Proof reuse savings

`resources/coding-tools-mcp/coding_tools_mcp/proof_ledger.py`

Cache hit trả thêm:

```text
cache_saved_ms = duration_ms của proof gốc
```

Server cộng số này vào `proof_summary.cache_saved_ms`, sau đó performance trace cộng vào `proof_cache_saved_ms`.

Điều này tránh đánh giá cache chỉ bằng hit-rate. Một hit 50 ms và một hit 90 s không có cùng giá trị kinh tế.

### 1.3 Runtime activation identity

`workspace_context` source được bổ sung runtime identity không chứa secret:

- `server_instance_id`;
- `process_instance_id`;
- `performance_trace_version`;
- stale/orphan/recovery counters.

Mục đích là chứng minh process thật đã reload source, không dùng “port mở” làm proxy.

### 1.4 Machine-readable activation snapshot

Thêm:

`resources/coding-tools-mcp/benchmarks/runtime_activation.py`

Snapshot đọc `.coding-tools/performance.json` và orchestration SQLite ở chế độ quan sát, không instantiate `Runtime`, không mutate ledger.

Nó ghi rõ:

- trace version;
- cumulative calls/errors/local-exec/wait proxy;
- idempotency eligible/keyed coverage;
- proof hits/saved ms;
- route/mode/state buckets;
- run status counts;
- proof/capsule counts;
- accepted-run TTA từ durable `started_at`/`finished_at`.

Notes trong JSON nhấn mạnh:

- `estimated_wait_ms` là runtime gap proxy, **không phải pure model/network latency**;
- accepted-run TTA không phải model-only latency;
- idempotency denominator chỉ là eligible operations.

### 1.5 Focused proof cho measurement patch

Command:

```text
cd resources/coding-tools-mcp &&
python -m pytest tests/test_efficiency_runtime.py tests/test_runtime_activation.py tests/test_proof_ledger.py -q
```

Kết quả:

```text
7 passed in 1.66s
```

EOCL run:

`91dd8a8c0a9f447089605f040b32a12f`

Wave:

`8dea11e5af5d4a29a8412eb30fc2c706`

Proof:

`ab9da91727354bf998b874c32996efce`

Proof fingerprint:

`cd6cb4985fc0ccadfa440b04d0f4815caebcf7e96c86e81bdb595fc30782628b`

Hash-chain integrity: green.

---

## 2. Pre-restart baseline

Report:

`resources/coding-tools-mcp/benchmarks/reports/runtime-activation-pre-restart-20260814-023657.json`

### 2.1 Live trace trước restart

| Metric | Pre-restart |
|---|---:|
| performance file version | **1** |
| tool calls | 1,096 |
| errors | 74 |
| local execution | 4,461,915 ms |
| estimated wait/gap proxy | 25,944,649 ms |
| idempotency eligible | 0 (field chưa được live runtime ghi) |
| eligible with key | 0 |
| proof cache hits | 0 trong schema measurement mới |
| proof saved ms | 0 |

Finding quan trọng: mặc dù working tree đã có các thay đổi observability trước đó, process phục vụ session **chưa reload source**, nên file live vẫn ở version 1. Vì vậy mọi kết luận trước activation rằng telemetry v2 đã chạy production phải được hạ xuống thành **source implemented, runtime not yet activated**.

### 2.2 Durable ledger baseline

| Metric | Value |
|---|---:|
| accepted runs | 14 |
| active runs | 36 |
| accepted waves | 14 |
| active waves | 36 |
| replanned waves | 6 |
| proof records | 38 |
| handoff capsules | 0 |
| idempotency records | 0 |
| completed background ops | 13 |
| active/waiting lanes | 0 |
| accepted-run TTA n | 14 |
| accepted-run TTA p50 | **90.291 s** |
| accepted-run TTA p90 | **339.099 s** |

Các TTA này là historical durable sample. Chúng **không** được dùng làm post-activation improvement nếu không có accepted run mới sau restart.

---

## 3. Controlled restart chronology

### 3.1 Probe đầu tiên bị bác bỏ về mặt safety

Một Electron helper probe được chạy ban đầu trong default secondary-app userData và trả:

```text
user_data = C:\Users\daoth\AppData\Roaming\Electron
configured_workspace = ""
native_pid = null
```

Nó còn lộ một bug trong guard helper: `path.resolve('')` có thể resolve về cwd, làm `expected_workspace_match=true` khi configured workspace rỗng.

**Không restart ở trạng thái này.**

Đây là một failure có giá trị: nếu bỏ bước probe, helper có thể ra quyết định dựa trên userData sai.

### 3.2 Xác định đúng product userData

Kiểm tra tồn tại tối thiểu cho thấy runtime state thật ở:

`%APPDATA%\web-mcp-assistant`

Probe với explicit Electron user-data directory trả:

```text
user_data = C:\Users\daoth\AppData\Roaming\web-mcp-assistant
configured_workspace = E:\Github\Tools-Codex-web
expected_workspace_match = true
native_pid = 13676
native_alive = true
native_port = 18766
tunnel_pid_present = true
```

### 3.3 Không dùng helper tự-khởi động để restart

Phân tích Windows process ownership cho thấy helper được spawn từ MCP có nguy cơ bị Job Object/process ownership giết cùng parent nếu tự stop MCP rồi cố restart.

Thay vì dùng đường này, activation dùng chính recovery topology của sản phẩm:

1. xác minh PID 13676 là owned MCP PID từ đúng product runtime state;
2. fault-inject kill **chỉ PID 13676**;
3. Electron owner supervisor phát hiện MCP process đã thoát;
4. supervisor dùng built-in `restart({automatic:true})`;
5. MCP + tunnel health được khôi phục theo logic sản phẩm.

Command fault injection:

```text
taskkill.exe /PID 13676 /F
```

Tool call trả 502 vì server đang phục vụ chính call bị dừng. Đây là expected transport consequence, không phải bằng chứng restart thất bại.

Reconnect đầu tiên còn 502. Reconnect tiếp theo thành công.

### 3.4 Strong post-restart identity proof

`workspace_context` sau reconnect trả:

```text
performance_trace_version = 3
process_instance_id = S7XLHXXT0xZ3G4mC
server_instance_id = nUXw2OzJye9pV251
stale_orchestration_runs = 0
orphaned_background_operations = 0
orphaned_idempotency_records = 0
agent_lanes_waiting_after_restart = 0
```

Đây là bằng chứng source mới đã được process mới load.

### 3.5 Owner probe sau recovery

Probe cuối:

```text
native_pid = 22508
native_alive = true
native_port = 18766
tunnel_pid_present = true
configured_workspace = E:\Github\Tools-Codex-web
```

PID đổi:

```text
13676 -> 22508
```

Kết luận: supervisor recovery/restart thành công và runtime owner state khớp workspace.

---

## 4. Stale-run reconciliation: kết quả thật

Pre restart:

```text
active runs = 36
```

Post restart:

```text
stale_orchestration_runs = 0
active runs = 36
```

Không có run nào bị đóng stale trong lần startup này.

Diễn giải đúng:

- **không** kết luận stale reconciliation không hoạt động;
- chỉ kết luận **không có run nào thỏa điều kiện inactivity >24h + không có live ownership trong snapshot hiện tại**;
- 36 active runs vẫn là hygiene backlog cần theo dõi, nhưng không được tự động gọi là “36 stale runs”.

Đây sửa một dạng suy luận dễ sai từ raw count.

---

## 5. Connector schema refresh: runtime reload != client schema reload

Sau runtime restart, Coding Tools MCP source schema đã có các action/fields mới như:

- `task_control accept/reject/handoff/...`;
- `run_id`, `wave_id`;
- `agent_workflow replan_reason`;
- `idempotency_key` trong object schemas.

Nhưng connector tool wrapper trong ChatGPT session hiện tại **vẫn chỉ expose schema cũ**, ví dụ `task_control` chỉ có:

```text
get | operation | start | update | pause | stop | resume | clear | history
```

Nó không expose `accept`, `handoff`, `run_id`, và wrapper `agent_workflow` không expose `idempotency_key`/`replan_reason`.

Kết luận:

```text
runtime source reload = PASS
connector schema refresh = FAIL / cached outside runtime
```

Restart MCP/tunnel không đủ để refresh tool contract đã được host/session materialize.

---

## 6. Live idempotency coverage sau activation

Post-restart early snapshot:

`runtime-activation-post-restart-live-20260814-024221.json`

Khi đó:

```text
eligible calls = 4
eligible with operation key = 0
coverage = 0%
```

Final snapshot:

`runtime-activation-final-post-owner-probe-20260814-024559.json`

```text
eligible calls = 16
eligible with operation key = 0
coverage = 0%
```

Đây là **live activation finding**, không phải test failure.

Core runtime có idempotency implementation, nhưng connected client hiện không thể truyền key qua stale tool schema.

Vì vậy cách viết đúng là:

> Durable idempotency semantics are implemented and integration-tested, but operation-key coverage for the currently connected ChatGPT tool schema is 0% in the activation window.

Không được viết:

> Idempotency production đã được bật hoàn toàn.

### 6.1 Semantic canary độc lập connector

Focused semantic set:

```text
python -m pytest \
  tests/test_universal_idempotency.py \
  tests/test_agent_workflow_idempotency.py \
  tests/test_proof_ledger.py \
  tests/test_system_capability_suite.py \
  tests/test_efficiency_runtime.py \
  tests/test_runtime_activation.py -q
```

Kết quả:

```text
55 passed in 12.60s
```

Set này bao gồm durable replay semantics, agent-workflow idempotency, proof cache, handoff/long-horizon/transport capability, telemetry-v3 và snapshot denominator.

Hai lớp bằng chứng phải tách biệt:

```text
core semantics: green
live connector operation-key coverage: 0%
```

---

## 7. Proof reuse: không được suy từ test sang production

Final live snapshot:

```text
proof_cache_hits = 0
proof_cache_saved_ms = 0
```

Điều này **không** có nghĩa proof cache hỏng.

Focused/integration tests chứng minh exact reuse + invalidation semantics xanh, nhưng activation window không tạo một production proof opportunity đủ điều kiện để hit.

Cách viết đúng:

```text
proof reuse semantics verified
production reuse opportunity observed in this window = 0
production savings measured = 0 ms
```

Không được ngoại suy test hit thành production savings.

---

## 8. Handoff effectiveness: chưa có production sample

Ledger trước và sau:

```text
handoff_capsules = 0
```

Capability tests về capsule round-trip/8 KiB bound vẫn xanh trong semantic canary.

Nhưng wrapper session không expose `task_control action=handoff`, nên không thực hiện manual live capsule canary qua connector này.

Kết luận:

```text
handoff mechanism works when invoked in integration tests
live handoff usage = 0
live handoff effectiveness = not measured
```

Không bật auto-handoff trong vòng này.

Lý do kinh tế vẫn giữ nguyên: prior real Codex benchmark đã cho thấy same-thread continuation có thể đạt 96.6% cached input và giảm credits 0.0507 -> 0.0221 (~56%). Vì vậy fresh-window handoff phải A/B với continuation trước khi tự động hóa.

---

## 9. Full regression sau activation

### 9.1 Python MCP

Command:

```text
npm run test:mcp
```

Collected:

```text
172 tests
```

Kết quả:

```text
172 passed in 44.34s
```

Baseline trước wave này: 169 Python tests.

Tăng 3 regression tests mới trong full suite; không double-count 55 focused canary vì chúng nằm trong full suite.

### 9.2 Node/Electron

Command:

```text
npm test
```

Kết quả:

```text
57/57 pass
TAP duration 1970.7931 ms
source root clean
```

### 9.3 Combined acceptance test count

```text
Python 172/172
Node   57/57
Total 229/229
```

Baseline trước activation: 226/226.

Kết luận: telemetry-v3 + runtime activation không làm vỡ regression suites.

---

## 10. Serialized tool-result bytes: phát hiện regression nhỏ nhưng thật

Benchmark:

`resources/coding-tools-mcp/benchmarks/reports/tool-result-bytes-20260814-024412.json`

Current:

| Metric | Current |
|---|---:|
| completion | 3/3 |
| calls/run | 9 |
| median bytes/call | 549 |
| mean bytes/call | **670.2** |
| bytes/run | **6032** |
| median time/run | 0.516 s |

Previous accepted baseline:

| Metric | Previous |
|---|---:|
| completion | 3/3 |
| calls/run | 9 |
| median bytes/call | 549 |
| mean bytes/call | 641.6 |
| bytes/run | 5774 |
| median time/run | 0.531 s |

Delta:

```text
median bytes/call: 549 -> 549        unchanged
mean bytes/call:   641.6 -> 670.2    +28.6 B (~+4.5%)
bytes/run:         5774 -> 6032      +258 B (~+4.55%)
median time/run:   0.531 -> 0.516 s  -0.015 s
```

Completion không đổi.

Benchmark workload có 9 calls; source change duy nhất trực tiếp làm tool-result structure lớn hơn trong workload này là runtime identity block được thêm vào `workspace_context`.

Vì total tăng 258 B/run và median không đổi, **strong inference** là runtime identity block chiếm gần như toàn bộ tăng trưởng. Tuy nhiên benchmark hiện chưa emit per-tool byte breakdown, nên không gọi đây là independently decomposed proof.

### Quyết định kỹ thuật

Không nên trả runtime activation identity trong mọi common compact context call.

Follow-up hợp lý:

```text
workspace_context(detail=compact) -> giữ payload cũ
workspace_context(detail=full)    -> thêm runtime activation identity
```

Mục tiêu sau follow-up: đưa deterministic benchmark về gần baseline 5774 B/run mà vẫn giữ debug/activation identity khi explicit full context được yêu cầu.

Patch này **chưa được áp dụng trong vòng hiện tại** vì EOCL measurement wave vẫn chờ durable final acceptance và connector schema hiện không expose `task_control accept`.

---

## 11. Routing economics: vẫn là scenario, không đổi evidence class

Run mới:

`resources/coding-tools-mcp/benchmarks/reports/routing-economics-20260813-194406.json`

Harness gọi production router thật.

Distribution:

```text
deterministic 30
mini          35
luna          20
sol_xhigh     15
```

Scenario result:

| Strategy | Credits | Accepted | Credits/accepted | TTA h | Wasted |
|---|---:|---:|---:|---:|---:|
| adaptive | 45.2597 | 98.3875 | 0.4600 | 0.3404 | 11.75 |
| all-Sol for model tasks | 92.1900 | 96.7500 | 0.9529 | 0.2453 | 0 |

Scenario saving:

```text
50.91%
```

Evidence class từ harness:

```text
scenario_simulation_not_production_ab
```

Không thay đổi class này sau activation.

Nó chứng minh regression của policy/economic model, **không chứng minh hóa đơn production giảm 50.91%**.

---

## 12. Prior real-model evidence: không chạy lại trong vòng này

Báo cáo real Codex đã cung cấp trước vòng activation đo cùng localized packet:

```text
Mini low:     0.0507 credits, oracle 3/3
Mini continue:0.0221 credits, 96.6% cached input
Luna high:    0.2276 credits, oracle 3/3
Sol xhigh:    1.2482 credits, oracle 3/3
```

Sol khoảng 24.6x Mini trên packet này.

Vòng hiện tại **không chạy lại paid model benchmark** vì mục tiêu là activation/telemetry validation và không cần tiêu thêm credits để chứng minh runtime reload.

Các số real-model trên được giữ ở evidence class “prior real-model measurement”, không trộn với routing scenario 50.91%.

---

## 13. Activation-window cumulative delta: dùng rất thận trọng

Pre snapshot:

```text
tool_calls = 1096
errors = 74
local_execution_ms = 4,461,915
estimated_wait_ms = 25,944,649
```

Final snapshot trước khi snapshot-call tự được trace:

```text
tool_calls = 1127
errors = 75
local_execution_ms = 4,524,302
estimated_wait_ms = 26,466,562
```

Observed delta:

```text
tool calls: +31
errors: +1
local execution: +62,387 ms
estimated gap proxy: +521,913 ms
```

Không dùng `+521,913 ms` để suy ra model/network latency. Activation window có intentional restart, reconnect gaps, full test execution và operator/tool scheduling.

Đây chính là lý do `estimated_wait_ms` chỉ là gap proxy.

---

## 14. Accepted-run TTA: chưa có post-activation sample mới

Ledger final:

```text
accepted runs = 14
active runs = 36
accepted TTA n = 14
p50 = 90.291 s
p90 = 339.099 s
```

Các số hoàn toàn giống pre-restart.

Do không có accepted run mới trong activation window, không được viết:

> TTA sau restart = 90.291 s.

Cách viết đúng:

> Historical durable accepted-run baseline remains p50 90.291 s / p90 339.099 s (n=14). Post-activation accepted-run sample size is zero in this window.

Cần thu accepted tasks mới sau khi connector schema hoạt động đầy đủ mới có thể A/B TTA.

---

## 15. EOCL final acceptance state

Run report chính thức:

`.coding-tools/orchestration/reports/run-91dd8a8c0a9f447089605f040b32a12f/run-summary.md`

Nó ghi:

```text
Status: active
Waves: 1
Failures: 0
REPLAN: 0
Proof stages: 1
Proof cache hits: 0
Acceptance checkpoints: 0
Hash chain valid: True
```

Wave đã đạt state `ACCEPTING` trong execution result và focused proof xanh.

ChatWeb semantic review kết luận diff measurement không làm yếu routing/high-cost/auth/permission gates.

Tuy nhiên durable `task_control action=accept` **không được ghi** vì connected tool schema không expose action đó. Một attempt dùng wrapper bị client-side schema validation từ chối trước khi tới runtime.

Do đó trạng thái phải viết là:

```text
source proof: PASS
ChatWeb semantic review: PASS
runtime activation: PASS
durable EOCL acceptance checkpoint: BLOCKED BY STALE CLIENT TOOL SCHEMA
```

Không gọi run này là checkpointed/accepted.

Không sửa SQLite thủ công, không fake task status để thay acceptance.

---

## 16. Controlled restart helper status

File thử nghiệm:

`scripts/mcp_controlled_restart.js`

Nó hữu ích để probe đúng product userData khi chạy với explicit:

```text
--user-data-dir=%APPDATA%\web-mcp-assistant
```

Nhưng initial probe phát hiện guard bug khi configured workspace rỗng có thể false-match cwd.

Vì vậy:

```text
status = research/probe helper, NOT production-ready
```

Không dùng helper này để thực hiện actual restart trong vòng này.

Không nên ship như operator command trước khi:

1. reject empty configured workspace;
2. require exact non-empty workspace match;
3. require explicit expected product userData or prove app identity;
4. có regression test cho empty-workspace false-positive;
5. quyết định rõ MCP-only restart hay product full restart.

---

## 17. Go / No-Go sau activation

### GO

- runtime process mới load telemetry v3;
- process identity/PID đổi đã được chứng minh;
- product supervisor recovery qua MCP process exit hoạt động;
- tunnel trở lại reachable và owner probe thấy tunnel PID;
- 55/55 semantic canary xanh;
- 172/172 Python xanh;
- 57/57 Node xanh;
- machine-readable pre/post snapshots hoạt động;
- stale reconciliation không đóng nhầm run nào trong startup này.

### NO-GO / chưa đủ bằng chứng

- **không** gọi live idempotency “activated”: coverage hiện 0%;
- **không** bật auto-handoff: production sample 0 và continuation cache có prior real savings lớn;
- **không** claim proof savings: live saved ms = 0 trong window;
- **không** tune routing từ 50.91% scenario như thể đó là production saving;
- **không** claim TTA improvement: không có accepted-run sample mới;
- **không** ship controlled-restart helper hiện tại;
- **không** gọi EOCL wave accepted/checkpointed khi checkpoint = 0.

---

## 18. Thứ tự follow-up có bằng chứng

### P0 — Refresh connector/tool schema

Cần fresh connector/tool-contract materialization để client expose source schema hiện tại:

- `task_control accept/reject/handoff`;
- `run_id/wave_id`;
- `agent_workflow replan_reason`;
- `idempotency_key`.

Sau đó việc đầu tiên là record durable acceptance cho run đang `ACCEPTING`, nếu state vẫn hợp lệ.

### P0 — Idempotency live three-case canary

Sau khi connector có key:

1. same operation id + same request -> deduplicated;
2. same operation id + different normalized request -> collision/reject;
3. new operation id + same request -> intentional repeat executes.

Acceptance:

```text
eligible coverage = 100% cho mutation/expensive canary
false dedup = 0
intentional repeat suppression = 0
```

### P0 — Remove compact-context payload tax

Move activation identity to explicit full/debug context.

Rerun serialized-result benchmark.

Target:

```text
completion unchanged
bytes/run <= previous 5774 baseline or documented justified delta
```

### P1 — Proof live reuse experiment

Tạo exact same proof opportunity:

```text
first -> miss + real oracle
second exact fingerprint -> hit
relevant source change -> miss
volatile .coding-tools change -> source fingerprint unchanged
```

Đo:

```text
proof_cache_hits
proof_cache_saved_ms
false reuse incidents = 0
```

### P1 — Handoff shadow/A-B

Không auto-switch ngay.

So sánh:

```text
same-thread continuation
vs
capsule -> fresh window -> resume
```

Đo:

- credits;
- cache percentage;
- model-visible bytes;
- TTA;
- duplicate work;
- resume success;
- missing state.

### P1 — New accepted-run production sample

Chỉ so TTA sau khi có accepted runs mới.

Tối thiểu phải tách:

- entry surface;
- route;
- task class;
- accepted/repair status.

Không so raw global average khi workload mix thay đổi.

### P2 — Routing calibration

Giữ production router thresholds hiện tại cho đến khi route ledger có đủ representative samples. Dùng cost per accepted result, first-pass accepted, repair turns và critical defects; scenario harness là regression guard, không phải billing estimator.

---

## 19. Evidence artifacts

### Activation snapshots

- `resources/coding-tools-mcp/benchmarks/reports/runtime-activation-pre-restart-20260814-023657.json`
- `resources/coding-tools-mcp/benchmarks/reports/runtime-activation-post-restart-live-20260814-024221.json`
- `resources/coding-tools-mcp/benchmarks/reports/runtime-activation-final-activation-window-20260814-024531.json`
- `resources/coding-tools-mcp/benchmarks/reports/runtime-activation-final-post-owner-probe-20260814-024559.json`

### Routing scenario

- `resources/coding-tools-mcp/benchmarks/reports/routing-economics-20260813-194406.json`

### Payload

- `resources/coding-tools-mcp/benchmarks/reports/tool-result-bytes-20260814-024412.json`

### EOCL

- `.coding-tools/orchestration/reports/run-91dd8a8c0a9f447089605f040b32a12f/run-summary.md`

---

## 20. Files của activation/measurement wave

Modified source:

- `package.json`
- `resources/coding-tools-mcp/coding_tools_mcp/performance_trace.py`
- `resources/coding-tools-mcp/coding_tools_mcp/proof_ledger.py`
- `resources/coding-tools-mcp/coding_tools_mcp/server.py`
- `resources/coding-tools-mcp/tests/test_efficiency_runtime.py`

New research/test utilities:

- `resources/coding-tools-mcp/benchmarks/runtime_activation.py`
- `resources/coding-tools-mcp/tests/test_runtime_activation.py`
- `scripts/mcp_controlled_restart.js` — probe/research only, not production-ready due guard finding above.

Working tree còn nhiều concurrent changes khác. Không quy các thay đổi Electron/renderer/control-panel độc lập cho activation wave này.

---

## 21. Delivery state

- Controlled runtime activation: **performed**.
- Old MCP PID: **13676**.
- New MCP PID: **22508**.
- Runtime v3 loaded: **yes**.
- Tunnel present after recovery: **yes**.
- Focused semantic canary: **55/55 pass**.
- Full Python: **172/172 pass**.
- Node/Electron: **57/57 pass**.
- Combined unique full-suite count: **229/229 pass**.
- Live idempotency coverage in activation window: **0% (0/16)**.
- Live proof reuse: **0 hits / 0 ms saved in this window**.
- Live handoff capsules: **0**.
- New accepted-run TTA sample after activation: **0**.
- Historical accepted TTA baseline: **p50 90.291 s / p90 339.099 s, n=14**.
- Payload: **+258 B/run (+4.55%)** vs prior baseline; follow-up optimization required.
- Routing scenario: **50.91% simulated credit saving**, still explicitly not production A/B.
- Durable EOCL acceptance checkpoint for measurement wave: **not recorded due stale client tool schema**.
- Commit: **not performed**.
- Push: **not performed**.
- Release/external deployment: **not performed**.

---

## 22. Kết luận khoa học/kỹ thuật

Activation thành công ở lớp runtime nhưng đồng thời loại bỏ ba ngộ nhận có thể xảy ra nếu chỉ nhìn test xanh:

1. **Core idempotency green không đồng nghĩa production coverage green.** Live connected schema hiện cho 0/16 eligible operations có key.
2. **Proof cache green trong test không đồng nghĩa production đang tiết kiệm thời gian.** Window này đo được 0 live hit và 0 saved ms.
3. **Historical TTA không phải post-activation TTA.** Không có accepted run mới, nên không có bằng chứng latency improvement production.

Ngoài ra, observability itself có cost: runtime identity thêm vào common `workspace_context` làm deterministic serialized-result workload tăng khoảng 4.55% bytes/run. Đây là regression nhỏ nhưng thật và nên được sửa bằng on-demand/full-detail identity thay vì luôn trả trong compact context.

Điểm tích cực mạnh nhất là controlled restart/recovery đã chứng minh process mới thực sự load telemetry v3 và toàn bộ regression suites vẫn xanh 229/229. Hệ thống hiện đo đúng hơn trước; kết quả đo cũng cho thấy những cơ chế cần activation phía client vẫn chưa tạo production value.

Vì vậy vòng tiếp theo không nên thêm model/router complexity. Ưu tiên đúng là:

```text
1. refresh connector schema / durable EOCL acceptance
2. live operation-key coverage
3. remove compact payload tax
4. live proof reuse + saved-ms measurement
5. handoff continuation A/B
6. accepted-run production TTA/cost sample
7. chỉ sau đó mới tune routing thresholds
```

Đây là trạng thái evidence-calibrated: những gì đã đo được ghi là measured; những gì chỉ test được ghi là test; những gì là scenario vẫn giữ nhãn scenario; những gì chưa có sample được ghi là not measured.