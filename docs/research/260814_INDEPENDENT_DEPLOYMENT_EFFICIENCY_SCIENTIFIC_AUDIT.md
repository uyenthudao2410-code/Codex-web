# Independent Deployment Efficiency & Scientific Audit — Tools-Codex-web / Coding Tools MCP

**Ngày đánh giá:** 2026-08-14  
**Workspace:** `E:\Github\Tools-Codex-web`  
**Nhánh/HEAD quan sát lúc bắt đầu:** `main` / `d3c6f184b8f5b2b3f603615f0e5a3abb889b9d0c`  
**Phiên bản desktop:** `web-mcp-assistant 0.3.4`  
**Phạm vi chính:** Coding Tools MCP Python runtime, Electron supervisor/tunnel, adaptive routing, EOCL/orchestration ledger, proof/cache/idempotency, bounded tool surface/context, long-horizon continuation.  
**Trạng thái working tree:** không sạch; có thay đổi sẵn của người dùng. Không reset, restore, clean, rebase hay ghi đè các thay đổi đó trong lần đánh giá này.

---

## 0. Kết luận điều hành

### Phán quyết tổng thể

**Mô hình triển khai hiện tại là một kiến trúc tốt, có bằng chứng thực nghiệm rõ rằng nó giảm chi phí điều phối và hạn chế failure amplification, nhưng bằng chứng hiện có chưa đủ để kết luận hệ thống đã “tối ưu hoàn toàn”, “Pareto tối ưu”, hay có độ tin cậy 100% ngoài tập test.**

Điểm mạnh quan trọng nhất không phải là “dùng model rẻ”, mà là bốn quyết định kiến trúc:

1. **Deterministic-first:** không gọi model khi test/compiler/tool deterministic đã đủ.
2. **Centralized authority:** ChatWeb/Sol giữ semantic authority và acceptance; worker/candidate không tự quyết định mutation cuối.
3. **Classifier + bounded fallback:** route một lần theo phạm vi/oracle/rủi ro, không chạy ladder dài theo kiểu `cheap -> less cheap -> expensive` cho mọi task.
4. **Compact execution surface:** `agent_workflow` gom nhiều bước và smart mode chỉ public 8 tool, giảm số model round-trip và schema ambiguity.

Các oracle chạy lại trong phiên đánh giá này đều xanh:

| Oracle / benchmark | Kết quả tái chạy | Ý nghĩa |
|---|---:|---|
| Electron/Node suite (`npm test`) | **51/51 pass**, TAP duration **2.482 s**, `source root clean` | Supervisor, tunnel-only recovery, process-tree handling, settings, smart surface, runtime/session behavior đều giữ invariant. |
| Python MCP suite | **131/131 pass + 3 subtests**, **34.98 s** | Routing gates, bridge, budget, idempotency primitives, orchestration/ledger, proof cache, resilience và coordination đều xanh ở test level. |
| Tổng test chính | **182/182 pass** | Bằng chứng mạnh cho implementation invariants; không phải bằng chứng 100% production reliability. |
| Serialized tool-result benchmark | **5/5 runs**, 9 calls/run; median **549 B/call**, mean **641.6 B/call**, median **0.532 s/run** | Tool-result payload nhỏ và deterministic trên workload benchmark. |
| EOCL drift gate | `agent_workflow` bị chặn với **BASE_DRIFT** trước execute | Gate fail-closed hoạt động thật; đồng thời lộ một chi phí vận hành do worktree/runtime state drift. |

**Kết luận kinh tế:** snapshot production trong các báo cáo ngày 12–13/08 cho thấy `mcp_only` chiếm 33/48 wave (68.75%), và wait-time lớn hơn local execution khoảng 5.2 lần. Vì vậy ROI lớn nhất tiếp theo không nằm ở việc đổi model thêm một cấp, mà ở **giảm model/tool round-trip, retry trùng lặp và repeated evidence**.

**Kết luận tối ưu:** ba cơ chế có tiềm năng cao nhưng trace hiện tại chưa khai thác được là:

- idempotency production;
- proof/semantic cache reuse;
- handoff capsule cho long-horizon context.

**Kết luận phương pháp:** mô phỏng 100-task trong báo cáo trước là hữu ích để suy luận kinh tế, nhưng trong tree hiện tại tôi không tìm thấy một harness executable đã commit thông qua các nhãn/strategy được báo cáo. Vì vậy nó phải được phân loại là **scenario/model evidence**, không ngang hàng với test suite hay benchmark có thể tái chạy.

---

## 1. Phương pháp đánh giá và phân cấp bằng chứng

Để tránh trộn “code có chức năng”, “test pass”, “production đã dùng”, “mô phỏng cho kết quả đẹp” thành một loại bằng chứng, báo cáo dùng 5 cấp:

| Cấp | Loại bằng chứng | Mức tin cậy |
|---|---|---|
| **A** | Oracle/benchmark được tái chạy trực tiếp trong phiên này và có kết quả xác định | Rất cao trong phạm vi test/benchmark |
| **A-** | Invariant được xác minh trực tiếp từ code + test liên quan | Cao |
| **B** | Production telemetry/log/ledger snapshot đã được thu thập trong báo cáo trước, có nguồn local rõ nhưng không tái tính toàn bộ trong phiên này | Khá cao, giới hạn bởi mẫu và thời gian |
| **C** | Mô phỏng kinh tế hoặc suy luận dựa trên xác suất/hằng số ước lượng | Trung bình; dùng cho quyết định, không gọi là đo production |
| **D** | Tuyên bố tuyệt đối hoặc benchmark so sánh không có baseline/harness có thể tái tạo | Không nên dùng làm claim chính |

### 1.1 Nguồn nội bộ được đối chiếu

- `README.md`
- `AGENTS.md`
- `docs/ARCHITECTURE.md`
- `docs/MODEL_EXECUTION.md`
- `docs/research/2026-08-14_SYSTEM_EFFICIENCY_BENCHMARK_AND_SCIENTIFIC_EVALUATION.md`
- `docs/research/DEPLOYMENT_PERFORMANCE_COST_EVALUATION_2026-08-14.md`
- `docs/research/CONTEXT_TUNNEL_LONGHORIZON_ANALYSIS_2026-08-14.md`
- `resources/coding-tools-mcp/coding_tools_mcp/server.py`
- `resources/coding-tools-mcp/coding_tools_mcp/orchestration_ledger.py`
- `resources/coding-tools-mcp/coding_tools_mcp/proof_ledger.py`
- `resources/coding-tools-mcp/coding_tools_mcp/performance_trace.py`
- test suite dưới `resources/coding-tools-mcp/tests/`
- Electron/Node tests dưới `tests/`

### 1.2 Nguồn khoa học / kỹ thuật bên ngoài

Ưu tiên paper gốc, ACL Anthology, OpenReview, arXiv, Google Research và nguồn chính thức OpenAI. Không dùng blog tổng hợp làm cơ sở cho claim kỹ thuật chính.

---

## 2. Kiến trúc thực tế đang được đánh giá

### 2.1 Mặt phẳng điều khiển

```text
ChatWeb / GPT-5.6 Sol
  semantic authority + final acceptance
              |
              v
Coding Tools MCP
  compact tool surface
  routing + EOCL + proof + task state
              |
      +-------+---------+
      |                 |
      v                 v
Local deterministic   Codex sidecar
execution/tests       read-only candidate/review
      |
      v
Workspace repository
single controlled mutation path
```

Mẫu này có một thuộc tính quan trọng: **model không phải source of truth của execution state**. State bền vững, proof và gates nằm dưới MCP/runtime. Đây là cách đúng để giảm hallucinated execution state.

### 2.2 Smart mode 8 tool

Public surface được test là:

- `workspace_context`
- `agent_workflow`
- `task_control`
- `exec_command`
- `command_control`
- `document_workflow`
- `request_permissions`
- `view_image`

Điểm đúng ở đây là **compactness và workflow aggregation**. Tuy nhiên, báo cáo trước gọi “8 tool là điểm cân bằng Pareto hoàn hảo” là quá mạnh. ToolScope (ACL 2026) cho thấy filtering/merging tool có thể tăng tool-selection accuracy 8.38%–38.6% trên các thiết lập họ thử, nhưng paper không chứng minh **con số 8** là global optimum cho repository này.

Claim nên dùng:

> Smart mode 8-tool là một compact surface có test bảo vệ và phù hợp với bằng chứng nghiên cứu rằng tool redundancy/context overload làm giảm selection quality; exact optimum cần A/B test nội bộ.

### 2.3 Adaptive route

Code/test hiện xác nhận các route:

```text
deterministic
mini
a luna
terra
sol_xhigh
sol_max
sol_ultra
```

Các invariant quan trọng từ test routing:

- localized bugfix + strong oracle + scope nhỏ -> `mini`;
- cùng scope nhưng thiếu strong oracle -> `luna`;
- feature vừa -> `luna`;
- feature rộng -> `sol_xhigh`;
- explicit `terra` dùng Terra/high;
- `sol_max` và `sol_ultra` fail-closed nếu thiếu `allow_high_cost=true`;
- high-cost route chỉ mở sau explicit acknowledgement.

Đây là **risk-aware classifier**, không đơn thuần là cost ladder.

---

## 3. Kết quả test tái chạy

## 3.1 Node / Electron: 51/51

Lệnh:

```text
npm test
```

Package script thực tế:

```text
node --test tests/*.test.js && node scripts/check-source-root-clean.js
```

Kết quả:

```text
# tests 51
# pass 51
# fail 0
# skipped 0
# duration_ms 2482.4086
source root clean
```

Các test có giá trị cao đối với deployment model gồm:

- live supervisor chỉ recovery tunnel khi MCP vẫn khỏe;
- MCP hung được defer rồi mới escalate sau threshold;
- MCP process chết mới kích hoạt full restart;
- cần ba failure liên tiếp cùng loại trước recovery;
- native/tunnel stop path sở hữu toàn process tree trên Windows;
- proxy normalization và credential rejection;
- smart mode giữ fixed compact surface;
- HTTP sessions chia sẻ một Runtime;
- hot-switch workspace;
- startup failure cleanup;
- UI/task strip phản ánh stage và long-command elapsed time.

### Diễn giải

Đây là bằng chứng A rằng supervisor policy và product invariants không regression tại HEAD đã quan sát. Nó **không** có nghĩa tunnel hạ tầng bên ngoài không thể rớt; nó chỉ chứng minh app xử lý các trạng thái đã mô hình hóa đúng theo test.

---

## 3.2 Python MCP: 131/131 + 3 subtests

Lần gọi đầu tiên từ repository root:

```text
python -m pytest resources/coding-tools-mcp/tests -q
```

bị collection error vì package `coding_tools_mcp` không nằm trên import path. Có 10 `ModuleNotFoundError` trong collection. Đây **không phải code regression**.

Điều kiện chạy được sửa bằng cách chạy từ package root:

```text
cd resources/coding-tools-mcp
python -m pytest tests -q
```

Kết quả:

```text
131 passed, 3 subtests passed in 34.98s
```

### Ý nghĩa thứ nhất: correctness

Các module có oracle cho:

- route and high-cost gates;
- budget deadline/retry policy;
- orchestration state/ledger;
- proof fingerprint/cache;
- agent workflow idempotency primitives;
- coordination state/handoff bounds;
- bridge behavior;
- resilience/fault injection;
- background operation continuation.

### Ý nghĩa thứ hai: developer ergonomics

Test suite Python **không có root-level invocation đủ tự mô tả** trong lần gọi thông thường nếu không thiết lập working directory/PYTHONPATH. Đây là lỗi ergonomics nhỏ nhưng đáng sửa: một `npm run test:mcp`, `scripts/test-mcp.*`, hoặc project config làm import path deterministic sẽ giảm false-negative cho CI/operator/agent.

---

## 3.3 Payload benchmark: 5/5 deterministic

Lệnh:

```text
cd resources/coding-tools-mcp
python -m benchmarks.tool_result_bytes --runs 5
```

Kết quả mới:

```json
{
  "runs": 5,
  "task_completion": "5/5",
  "tool_calls_per_run": 9,
  "serialized_result_bytes": {
    "total": 28870,
    "median": 549,
    "mean": 641.6,
    "min": 274,
    "max": 1689,
    "per_run_totals": [5774, 5774, 5774, 5774, 5774]
  },
  "elapsed_seconds": {
    "total": 2.766,
    "median": 0.532
  }
}
```

So với report cũ:

| Chỉ số | Report cũ | Tái chạy | Chênh lệch |
|---|---:|---:|---:|
| Median bytes/call | 531 | **549** | +18 B (~3.4%) |
| Mean bytes/call | 630.4 | **641.6** | +11.2 B (~1.8%) |
| Bytes/run | 5,674 | **5,774** | +100 B (~1.8%) |
| Median elapsed/run | 0.625 s | **0.532 s** | nhanh hơn ~14.9% |
| Completion | 5/5 | **5/5** | không đổi |

Điểm quan trọng nhất: cả năm run hiện tại vẫn ra đúng `5,774 bytes/run`. Đây là bằng chứng tốt cho **deterministic response shaping** trên benchmark này.

Điểm cần sửa trong claim cũ: benchmark này chứng minh payload nội bộ nhỏ. Nó **không tự nó** chứng minh tiết kiệm “85–94% so với MCP server truyền thống” nếu không có baseline server cụ thể, cùng task, cùng schema và cùng completion criterion được đo trong cùng harness.

---

## 3.4 EOCL thực tế: gate đã chặn BASE_DRIFT

Trong quá trình cố chạy verification qua `agent_workflow`, prepare hoàn tất nhưng execute bị chặn:

```text
execution.status = blocked
reason = BASE_DRIFT
orchestration_state = REPLAN
```

Đây là một kết quả quan trọng, không nên coi là nuisance rồi tắt gate.

### Mặt tích cực

- fail-closed thực sự hoạt động;
- system không tiếp tục write/proof dưới một base/worktree khác với snapshot đã chuẩn bị;
- EOCL đang là enforcement, không chỉ là prompt suggestion.

### Mặt tiêu cực / chi phí vận hành

Working tree có các file local runtime dưới `.coding-tools` đang thay đổi. Các lệnh orchestration của chính hệ thống cũng có thể tạo/update ledger/report/task-state. Điều này tạo nguy cơ **self-induced drift**: control-plane telemetry làm fingerprint thay đổi dù source code mục tiêu chưa đổi.

Trong phiên này chưa trace toàn bộ hàm fingerprint đến tận từng path, nên kết luận root cause cụ thể được xếp mức **B+/likely**, không A. Tuy vậy, hiện tượng đủ rõ để ưu tiên kiểm tra.

### Khuyến nghị

Nếu `.coding-tools` là runtime-local state:

1. không để nó tham gia source/worktree fingerprint cho code acceptance;
2. nếu cần audit integrity, dùng **một audit-state hash riêng**, không trộn vào source fingerprint;
3. nếu các file đó không phải source artifact, tránh track chúng trong Git;
4. proof fingerprint nên phụ thuộc vào `base_head + relevant source inputs + contract + oracle command`, không phụ thuộc volatile observer output.

Mục tiêu là giữ **strict drift detection** nhưng loại bỏ false REPLAN do control plane tự ghi state.

---

## 4. Production evidence hiện có: lợi ích và lỗ hổng

Các số dưới đây là snapshot trong báo cáo production 12–13/08/2026, không phải số được tái tính lại từ SQLite sau các tool call của phiên này.

### 4.1 Deterministic lane đang có giá trị thật

Snapshot:

```text
waves = 48
mcp_only = 33
mcp_only share = 68.75%
```

Nếu definition `mcp_only` đúng là deterministic/no paid candidate model, đây là bằng chứng B rất mạnh cho một nguyên tắc kinh tế:

> Cách rẻ nhất để dùng model là không gọi model khi deterministic evidence đã đủ.

Đây có thể là nguồn savings lớn hơn việc tranh luận Luna vs Mini trên các task vốn không cần LLM.

### 4.2 Nút thắt thời gian là wait/round-trip

Snapshot `performance.json` trước đó:

```text
tool calls             968
local execution        4,067 s
estimated wait        21,240 s
errors                    65
cache hits                 1
deduplicated calls         0
```

Tỷ lệ:

```text
wait / local_exec ~ 5.22 : 1
wait share of (wait + exec) ~ 84%
```

### Hệ quả

Một tối ưu local làm command nhanh hơn 20% chỉ tác động vào phần ~16% của budget wait+exec. Ngược lại, cắt một model/tool round-trip hoặc bundle ba thao tác vào một `agent_workflow` có thể loại bỏ một phần đáng kể của 84% còn lại.

Đây là lý do `agent_workflow` có giá trị kinh tế thực: **round-trip elimination**, không chỉ “API đẹp hơn”.

### 4.3 Cache/dedup: implementation có, production benefit gần bằng 0

Snapshot:

```text
cache_hit = 1 / 968
semantic dedup = 0 / 968
```

Trong code/test:

- proof cache có key/fingerprint;
- ledger có `cache_hit`;
- idempotency table tồn tại;
- test xác nhận cache-hit behavior.

Nhưng production trace không sử dụng đáng kể.

Đây là ví dụ điển hình của **design-to-operation gap**:

```text
feature exists != feature saves money
```

KPI cần đo sau khi tối ưu:

- `proof_reuse_rate`;
- `idempotent_replay_rate`;
- `duplicate_execution_avoided`;
- saved local seconds;
- saved model turns;
- saved input bytes/tokens.

### 4.4 Handoff capsule: đúng kiến trúc, chưa vận hành

Report long-horizon trước ghi:

```text
handoff_capsules = 0
coordination_messages = 0
```

Trong khi implementation có capsule bound 8 KiB và test bảo vệ size.

Khi context dài, giải pháp tốt không phải tiếp tục ép transcript khổng lồ vào model, mà là:

```text
checkpoint state
-> compact handoff capsule
-> fresh conversation/window
-> resume from durable state + bounded replay
```

OpenAI cũng công khai mô tả harness của họ theo hướng tránh context bloat và giữ exact prefix để tăng prompt-cache hit rate. Do đó hướng kiến trúc này rất phù hợp; vấn đề là **activation policy chưa được đưa vào normal operation**.

### 4.5 Idempotency: test có, trace production không chứng minh đã dùng

Ledger schema có `idempotency_records`, runtime có logic xử lý orphaned idempotency, test có idempotency coverage. Nhưng production snapshot trước ghi 0 record/dedup.

Khi tunnel rớt sau lúc command đã start nhưng trước khi client nhận response, retry không có idempotency có thể tạo:

```text
same intent
-> second command execution
-> duplicate build/test/write
-> extra latency + cost + possibly duplicate side effect
```

Đây là P0/P1 tùy mutation class. Với write/deploy-like side effect, idempotency là reliability boundary chứ không chỉ optimization.

---

## 5. Tunnel và long-horizon reliability

Báo cáo trước ghi trong 5 ngày:

- 12 tunnel client restarts;
- nhiều `poll failed` / `poll timed out`;
- 12 `ConnectionAbortedError [WinError 10053]` khi MCP đang ghi response.

### Diễn giải đúng

Supervisor test xanh chứng minh app phân loại và recovery các trạng thái đã mô hình hóa đúng. Nó không thể loại bỏ lỗi control-plane/network bên ngoài.

Điểm app còn kiểm soát được:

1. safe replay/idempotency;
2. expose `request_id`, `execution_state`, `may_have_started`;
3. surfacing tunnel uptime/restart/error counters;
4. compact status/handoff cho remote/mobile;
5. không reset MCP khi chỉ tunnel chết.

Đây là phân tách trách nhiệm hợp lý.

---

## 6. Đánh giá routing kinh tế: cái gì đã chứng minh, cái gì chưa

## 6.1 Mô phỏng 100-task trước đó

Report trước đưa ra:

| Strategy | Credits | TTA | Accepted | Wasted attempts | Critical miss |
|---|---:|---:|---:|---:|---:|
| Adaptive | 46.84 | 0.35 h | 99.4 | 12.9 | 0.65 |
| All-Sol | 96.49 | 0.28 h | 99.8 | 3.3 | 0.16 |
| All-Luna | 41.89 | 0.39 h | 99.1 | 18.0 | 0.90 |
| All-Mini | 54.78 | 0.55 h | 98.3 | 34.2 | 1.71 |
| Ladder | 34.21 | 0.65 h | 99.4 | 46.1 | 0.59 |

### Điều có thể kết luận

Nếu xác suất/hằng số đầu vào đúng, adaptive route có một cost-risk trade-off tốt hơn all-Sol và có latency thấp hơn ladder.

### Điều không được kết luận

Đây **không phải production A/B**. Các `P(success | task class, model)` là giả định/model inputs. Vì vậy số `51.5% cheaper` là kết quả điều kiện, không phải mức tiết kiệm đã đo trên hóa đơn.

Trong lần audit này, search các nhãn chiến lược/100-task/wasted-attempt trong `resources/coding-tools-mcp` và `docs/research` chỉ tìm thấy report, không tìm thấy một committed executable harness có thể gọi lại trực tiếp. Vì vậy reproducibility hiện chưa đạt mức A.

### Khuyến nghị

Commit harness thành:

```text
benchmarks/routing_economics.py
benchmarks/fixtures/task_mix.json
benchmarks/fixtures/model_outcomes.json
benchmarks/reports/<timestamp>.json
```

Mỗi report phải ghi:

- git HEAD;
- input dataset hash;
- task distribution;
- success probability source;
- model cost table version/date;
- random seed;
- confidence intervals;
- scenario vs measured flag.

---

## 6.2 Public model benchmark không đủ để suy ra local routing probability

OpenAI công bố SWE-Bench Pro cho GPT-5.6:

```text
Sol   64.6%
Terra 63.4%
Luna  62.7%
```

Khoảng cách public aggregate tương đối nhỏ. Điều đó **không phủ định** local benchmark nơi một scaffold/topology có thể làm Luna/Terra tệ hơn nhiều, nhưng nó cho thấy không được dùng public tier score để biện minh trực tiếp cho các xác suất như `Sol=0.97` và `Luna=0.35` trên một class cụ thể.

Routing probability phải được hiệu chỉnh từ **local task class + local scaffold + oracle + topology**.

---

## 6.3 Mẫu 10/10 và 4/4 quá nhỏ cho claim mạnh

Một route đạt 10/10 trong benchmark local là đáng khích lệ, nhưng không đồng nghĩa “true success rate = 100%”. Với Clopper–Pearson two-sided 95%, 10/10 có lower bound xấp xỉ **69%**.

Tương tự, 4/4 của Mini có lower 95% bound chỉ khoảng **40%**.

Do đó:

- 10/10 đủ để giữ route promising/default **trong scope benchmark đó**, không đủ để nói universal 100%;
- 4/4 tuyệt đối không đủ để auto-promote lane rộng hơn.

Điều này đồng thuận với Conformal LLM Routing (ACL 2026): cheap-model routing nên dựa trên calibrated safety/violation bounds, không dựa trên raw win rate nhỏ.

---

## 7. Đối chiếu với nghiên cứu khoa học 2023–2026

## 7.1 ToolScope — compact tool surface

**Liu et al., ACL 2026, ToolScope: Enhancing LLM Agent Tool Use through Tool Merging and Context-Aware Filtering.**

Kết quả paper: tool redundancy/context constraints làm tool selection khó hơn; filtering/merging tăng tool-selection accuracy 8.38%–38.6% trên các eval của họ.

**Tác động cho repo:** ủng hộ giữ tool surface nhỏ và workflow-level tools. Không chứng minh `8` là magic number.

## 7.2 Google Research — multi-agent chỉ tốt khi task parallelizable

**Towards a Science of Scaling Agent Systems, Google Research, 2026-01-28.**

Trong 180 agent configurations:

- centralized multi-agent có thể tăng mạnh trên task decomposable/parallel;
- trên sequential planning, multi-agent variants giảm 39–70%;
- independent agents có error amplification đến 17.2x trong setup của nghiên cứu;
- centralized architecture giảm amplification đáng kể.

**Tác động:** repo đúng khi không spawn swarm mặc định, giữ central acceptance và chỉ dùng parallelism khi workstream thực sự độc lập.

## 7.3 MTRouter — ít model switch hơn có thể tốt hơn

**Zhang et al., ACL 2026.**

MTRouter giảm cost 58.7% trên ScienceWorld và 43.4% trên HLE so với GPT-5 baseline trong setup của paper; analysis cho thấy nó thành công với ít model switch hơn một baseline router và chịu transient errors tốt hơn.

**Tác động:** hỗ trợ `classify -> bounded fallback`, phản đối ladder dài không có evidence-triggered escalation.

Không nên suy diễn rằng local rule router tương đương MTRouter; paper dùng learned outcome estimator từ logged trajectories.

## 7.4 LLMRouterBench — router phức tạp chưa chắc hơn baseline đơn giản

**Li et al., Findings ACL 2026.**

Benchmark >400K instances, 21 datasets, 33 models và 10 baselines cho thấy nhiều router có performance gần nhau; một số router phức tạp/commercial không reliably beat simple baseline; model curation quan trọng và larger ensembles có diminishing returns.

**Tác động:** chưa có lý do để nhảy thẳng sang Bayesian/Deep router phức tạp. Trước tiên phải có clean route ledger và simple calibrated baseline.

## 7.5 ContextualRouter — lịch sử ít vẫn hữu ích

**Varangot-Reille et al., EACL 2026.**

Retrieval-based routing, thậm chí kNN đơn giản, có thể comparable/better trong một số setup và generalize với rất ít historical data.

**Tác động:** hướng tốt nhất cho P2 là `nearest similar past tasks` từ ledger trước khi xây ML router riêng.

## 7.6 Conformal LLM Routing — cheap lane cần safety bound

**Uddin & Bauer, ACL 2026 SRW.**

Paper dùng conformal calibration để giữ violation rate của cheap model dưới tolerance với confidence target trong eval.

**Tác động:** promotion Mini nên dùng lower-confidence/safety gate. Raw 4/4 không đủ.

## 7.7 Intrinsic self-correction có giới hạn

**Huang et al., ICLR 2024, Large Language Models Cannot Self-Correct Reasoning Yet.**

Kết luận phù hợp nhất, có nuance: trong reasoning setups họ thử, model struggle với intrinsic self-correction khi thiếu external feedback và đôi lúc performance giảm. Reviewer cũng cảnh báo không nên diễn giải title như một định lý bất khả tổng quát.

**Tác động:** test/compiler/external oracle là đúng. Không nên viết “định lý chứng minh LLM không thể tự sửa sai” như claim tuyệt đối.

## 7.8 RETRACE — independent patch verification

**Li et al., arXiv:2608.08950, 2026-08-09.**

RETRACE dùng independent reconstruct-and-verify; trên SWE-bench Verified tăng Pass@1 7.0 points với GPT-5-mini và 3.6 points với MiniMax-2.5 trong scaffold đánh giá của họ.

**Tác động:** review plane blind/evidence-oriented của repo là hướng rất tốt. Reviewer không nên chỉ đọc narrative mà executor đã dùng để tự thuyết phục chính nó.

## 7.9 SWE-bench “solved” study — green tests chưa đủ

**Wang, Pradel & Liu, arXiv:2503.15223.**

Nghiên cứu phát hiện một phần patch được benchmark đếm đúng nhưng không thực sự thỏa behavior kỳ vọng; resolution rate có thể bị inflate.

**Tác động:** high-risk task phải có semantic/invariant review ngoài focused tests, đặc biệt auth, tenant isolation, finance, migration, deletion, security boundary.

## 7.10 SWE-Effi — effectiveness = outcome / resource

**Fan et al., arXiv:2509.09853.**

Paper nhấn mạnh token snowball, expensive failures và trade-off giữa token budget và time budget.

**Tác động:** metric đúng của repo là `cost/time per accepted solution`, không phải `price per first model call`.

Lưu ý: abstract/paper metadata xác nhận các hiện tượng này, nhưng audit hiện tại **không xác minh** các con số cực mạnh trong report cũ như “input tokens >90% tổng chi phí” hoặc “failure tốn 50x–1000x”. Không nên giữ các multiplier đó nếu chưa trích đúng table/experiment.

## 7.11 OpenAI agentic harness — context bloat và repeated work

OpenAI Engineering ngày 2026-07-29 mô tả:

- deferred discovery để giảm context bloat;
- cap tool output;
- append-only model-visible history;
- deterministic tool order để giữ prompt-cache prefix;
- repeated work trong agent loop là multiplier chi phí.

**Tác động:** bounded payload, compact surface, deterministic ordering, handoff capsule và proof reuse của repo đều đi cùng hướng với production harness practice hiện đại.

---

## 8. Những claim trong report cũ cần hạ mức hoặc sửa

| Claim cũ | Audit | Cách viết nên dùng |
|---|---|---|
| “8 tools là Pareto hoàn hảo” | **Quá mạnh** | 8-tool surface là compact, stable và research-aligned; optimum cần A/B. |
| “Zero Secret Leakage / bảo mật tuyệt đối” | **Không thể chứng minh bằng regex/test suite** | Secret sanitization + scoped runtime là defense-in-depth; tiếp tục fuzz/red-team. |
| “Structured execution loại bỏ 99% lỗi escaping” | **Không có benchmark 99% trong evidence hiện tại** | Structured argv loại bỏ một lớp shell quoting/parsing; cần đo nếu muốn % cụ thể. |
| “85–94% tiết kiệm so với MCP truyền thống” | **Baseline chưa tái tạo** | Current workload ~642 B/call mean; benchmark comparative phải có named baselines cùng task. |
| “Sol->MCP 10/10 = reliability 100%” | **Sai cách diễn giải thống kê** | 10/10 on benchmark; sample small, lower CI còn rộng. |
| “182/182 tests = production 100% reliable” | **Không đúng** | 182/182 confirms covered invariants at this HEAD. |
| “LLM cannot self-correct” như định lý | **Quá tuyệt đối** | Intrinsic self-correction without external feedback is unreliable in studied reasoning setups. |
| “51.5% cheaper” như measured production | **Chỉ là simulation** | 51.5% under stated task mix/probability/credit assumptions. |
| “credit = USD cost” | **Không đúng** | credits là internal estimate unless reconciled to billing. |

Việc hạ claim không làm dự án yếu đi; ngược lại, nó làm báo cáo đủ chặt để dùng cho quyết định kỹ thuật.

---

## 9. Chẩn đoán theo 5 trụ cột

## 9.1 Correctness / Accepted quality — **Tốt, nhưng cần independent semantic gate cho high-risk**

Điểm mạnh:

- deterministic oracle trước model debate;
- proof fingerprint;
- final semantic authority;
- test suite rộng;
- high-cost gates;
- sidecar read-only.

Rủi ro:

- test xanh không đồng nghĩa behavior hoàn toàn đúng;
- benchmark acceptance mẫu nhỏ;
- route quality chưa có production confidence interval theo task class.

**Đánh giá: 8/10.**

## 9.2 Latency — **Kiến trúc tốt, production bottleneck chưa giải quyết hết**

Điểm mạnh:

- agent_workflow bundling;
- background handoff;
- command continuation;
- compact payload.

Rủi ro:

- 84% wait share trong snapshot;
- tunnel can abort responses;
- poll/round-trip vẫn là dominant cost.

**Đánh giá: 7/10.**

## 9.3 Cost efficiency — **Tốt về topology, chưa đủ đo lường về billing**

Điểm mạnh:

- 68.75% mcp_only trong snapshot;
- bounded tool output;
- cheap lanes gated;
- deterministic-first.

Rủi ro:

- simulation không phải A/B;
- cache/dedup gần zero;
- internal credits không phải invoice.

**Đánh giá: 7.5/10.**

## 9.4 Resilience / long-horizon — **Kiến trúc mạnh, activation gap đáng kể**

Điểm mạnh:

- ledger/checkpoints;
- EOCL fail-closed;
- supervisor tunnel-only recovery;
- background operations;
- capsule schema.

Rủi ro:

- handoff capsule chưa được dùng trong snapshot;
- idempotency production chưa chứng minh;
- stale active runs;
- tunnel mid-response abort.

**Đánh giá: 6.5/10.**

## 9.5 Observability / scientific reproducibility — **Cần nâng cấp**

Điểm mạnh:

- performance trace;
- ledger;
- benchmark JSON;
- test output deterministic.

Rủi ro:

- economics harness không thấy committed;
- source/runtime state lẫn vào dirty worktree;
- một số report claim không trace được tới raw experiment;
- số liệu simulation và measurement chưa luôn dán nhãn khác nhau.

**Đánh giá: 6/10.**

---

## 10. Priority roadmap theo ROI

## P0 — Giảm model round-trip, không tối ưu model tier trước

**Vì sao:** wait chiếm ~84% wait+exec trong trace snapshot.

Hành động:

1. đo `round_trips_per_accepted_task`;
2. buộc common coding path đi qua `agent_workflow` thay vì nhiều low-level calls;
3. batch read/observe khi semantics cho phép;
4. không poll nếu operation đã có terminal evidence;
5. compact result ở source, không trả raw rồi mới tóm tắt bằng model.

KPI:

```text
median model/tool round trips per accepted task
p90 TTA
wait_ms / accepted task
```

## P0 — Tách volatile orchestration state khỏi source fingerprint

**Vì sao:** audit này trực tiếp gặp `BASE_DRIFT` trước execute trong khi control-plane state đang thay đổi.

Hành động:

- định nghĩa explicit source fingerprint allowlist/exclusion;
- `.coding-tools` runtime state không tham gia source generation fingerprint;
- audit ledger có integrity hash riêng;
- test: repeated read-only workflow không tự tạo BASE_DRIFT.

KPI:

```text
self_induced_replan_rate
base_drift_false_positive_rate
```

## P1 — Production idempotency cho mọi action có side effect hoặc expensive execution

Key nên bind ít nhất:

```text
principal/session
operation
tool request identity
normalized request hash
base/worktree generation
```

Không chỉ cache result; phải phân biệt:

```text
not_started
in_progress
completed
outcome_unknown
```

KPI:

```text
duplicate_execution_avoided
idempotent_replay_hits
tunnel_retry_without_reexecution
```

## P1 — Kích hoạt handoff capsule như normal policy

Trigger không cần biết exact ChatGPT token count. Có thể dựa trên proxy:

- tool turns;
- cumulative model-visible tool bytes;
- task age;
- wave count;
- explicit long-horizon checkpoint.

Policy:

```text
before context becomes pathological
-> checkpoint
-> capsule <= 8 KiB
-> new chat/window
-> resume from durable state
```

KPI:

```text
capsules_created / long tasks
resume_success_rate
context_bytes_before_handoff
```

## P1 — Proof reuse thật, không chỉ schema/cache test

Chỉ cache khi fingerprint exact:

```text
base_head
relevant_paths_hash
contract_hash
oracle_command_hash
toolchain identity when material
```

Không cache khi:

- dirty relevant file;
- test command changed;
- environment/toolchain affects result;
- upstream proof changed.

KPI:

```text
proof_cache_hit_rate
seconds_saved_by_proof_reuse
false_cache_incidents = 0
```

## P2 — Route ledger + calibrated promotion

Ghi cho từng task:

```text
class
scope files/bytes
oracle strength
selected route
fallback
first-pass accepted
repair turns
TTA
model credits/tokens
critical defect
```

Sau tối thiểu khoảng 50 mẫu/class mới bắt đầu tune threshold; dùng Wilson/Clopper-Pearson/conformal lower bound thay vì raw mean.

Không cần ML router trước khi baseline rule + kNN history được benchmark.

## P2 — Tunnel observability

Expose:

- uptime;
- restart count;
- last poll failure;
- aborted response count;
- current MCP health;
- active operations potentially affected.

KPI:

```text
aborted_responses/day
tunnel_restarts/day
retry_success_without_duplicate
```

## P2 — Root-level reproducible test commands

Thêm một canonical command để agent/CI không gặp import-path false failure:

```text
npm run test:mcp
```

hoặc script equivalent xác lập working dir/PYTHONPATH.

## P3 — Commit routing economics benchmark

Không để số 51.5% tồn tại chỉ trong prose.

Harness phải emit machine-readable JSON + metadata + CI smoke.

## P3 — External patch verification cho high-risk

Áp dụng RETRACE-like independent reasoning hoặc differential/property testing ở class rủi ro cao, không gọi review model cho mọi typo/leaf change.

---

## 11. Bộ benchmark nên dùng cho vòng tối ưu kế tiếp

### B1 — Round-trip ablation

Cùng 30–50 task, so sánh:

```text
A: low-level multi-call
B: agent_workflow bundled
```

Đo:

- accepted rate;
- tool calls;
- model turns;
- input/output tokens;
- TTA;
- p90/p95;
- failure-repair turns.

### B2 — Tool surface ablation

So sánh 8-tool smart vs 12/16/24-tool synthetic/compat surface trên cùng task set.

Mục tiêu: xác minh **8** có thực sự ở gần optimum cho model/client này hay chỉ là lựa chọn hợp lý.

### B3 — Idempotency fault injection

Inject disconnect tại bốn thời điểm:

```text
before start
just after start
mid-output
just before response delivery
```

Success criterion:

```text
side effect executes at most once
client eventually receives truthful state
unknown outcome never presented as safe pre-start retry
```

### B4 — Handoff long-horizon

Task 100+ turns hoặc context proxy lớn:

```text
continuous chat
vs
capsule -> fresh window -> resume
```

Đo:

- TTA after handoff;
- missing state;
- duplicate work;
- model-visible bytes;
- accepted rate.

### B5 — Proof cache reuse

Run same oracle:

1. exact same source;
2. irrelevant file changed;
3. relevant file changed;
4. command changed;
5. toolchain identity changed.

Expected:

- 1/2 reuse only if safety model allows;
- 3/4/5 invalidate.

### B6 — Router production shadow test

Router chỉ **recommend**, không điều khiển production trong giai đoạn đầu.

For each real task:

- current selected route;
- shadow alternatives;
- predicted cost/risk;
- eventual accepted outcome.

Sau đủ sample mới enable auto-routing expansion.

### B7 — Tunnel chaos test

Inject local disconnect/restart around live command and validate:

- MCP not killed unnecessarily;
- operation continues or truthful unknown/lost state;
- no duplicated execution;
- session alias works;
- response replay bounded.

### B8 — High-risk semantic validation

Tạo mutation set cho:

- auth bypass;
- tenant boundary;
- destructive file operation;
- migration idempotency;
- stale cache;
- path traversal;
- secret-redaction bypass.

Focused unit tests + differential/invariant verification; không chỉ compile/pass.

---

## 12. Metric framework đề xuất

Không tối ưu một metric duy nhất.

### 12.1 Primary objective

```text
Expected Accepted Work per Dollar and per Minute
```

Tách thành:

```text
Accepted Rate
First-Pass Accepted Rate
Critical Defect Rate
Credits / Accepted
Wall Time / Accepted
Model Turns / Accepted
Tool Calls / Accepted
Repair Turns / Accepted
```

### 12.2 Reliability

```text
Duplicate Execution Rate
Outcome-Unknown Rate
Tunnel Abort Rate
Resume Success Rate
False REPLAN Rate
Proof Cache False-Reuse Rate
```

### 12.3 Context efficiency

```text
Model-visible bytes / accepted task
Tool-result bytes / call
Prompt-cache hit ratio
Handoff compression ratio
Repeated evidence bytes
```

### 12.4 Router quality

Theo task class:

```text
n
first-pass accepted
fallback rate
repair turns
critical miss
TTA
cost
confidence interval
```

Không publish `%` mà không publish `n`.

---

## 13. Decision matrix: giữ, sửa, thí nghiệm

### GIỮ NGUYÊN

- deterministic-first;
- ChatWeb/Sol final semantic authority;
- read-only/no-network sidecar;
- high-cost explicit gate;
- strong-oracle gate cho cheap lane;
- bounded payload;
- max-one/bounded fallback posture;
- supervisor tunnel-only recovery;
- fail-closed EOCL.

### SỬA ƯU TIÊN

- source fingerprint vs volatile `.coding-tools` state;
- production idempotency;
- stale run lifecycle;
- handoff activation;
- cache/proof reuse instrumentation;
- root-level Python test invocation;
- tunnel observability.

### THÍ NGHIỆM TRƯỚC KHI ĐƯA PRODUCTION

- auto-promote Mini rộng hơn;
- Terra autonomous cross-file;
- Bayesian/ML router;
- multi-agent/ultra ngoài task parallelizable;
- semantic cache rộng;
- remote status endpoint qua tunnel.

---

## 14. Kết luận cuối

Dự án đã làm đúng một điều mà nhiều agent framework làm ngược: **đặt software-engineering control plane lên trên model autonomy**.

Bằng chứng tái chạy cho thấy:

- 182/182 test chính xanh;
- payload benchmark vẫn deterministic và nhỏ;
- route/high-cost/oracle invariants được test;
- EOCL thật sự chặn drift thay vì cho phép silent mutation.

Bằng chứng production snapshot cho thấy:

- deterministic `mcp_only` gánh phần lớn wave;
- wait/round-trip mới là bottleneck kinh tế lớn nhất;
- cache/dedup/handoff/idempotency chưa tạo giá trị tương xứng với implementation;
- tunnel vẫn là failure surface thực.

Do đó, **không nên ưu tiên thêm model tier, thêm agent hay router phức tạp ở vòng tiếp theo**. Thứ tự tối ưu có ROI cao nhất là:

```text
1. giảm round-trip
2. loại self-induced drift
3. idempotent retry
4. activate handoff
5. proof reuse
6. route ledger + confidence calibration
7. sau đó mới xem ML router / multi-agent expansion
```

Nếu làm đúng thứ tự này, hệ thống có khả năng giảm cả latency, token/credit waste và operational failure cùng lúc, thay vì đổi một loại chi phí lấy một loại chi phí khác.

---

# Tài liệu tham khảo chính

1. Liu, M. M. et al. (2026). **ToolScope: Enhancing LLM Agent Tool Use through Tool Merging and Context-Aware Filtering.** ACL 2026. DOI: `10.18653/v1/2026.acl-long.1573`. https://aclanthology.org/2026.acl-long.1573/
2. Zhang, Y. et al. (2026). **MTRouter: Cost-Aware Multi-Turn LLM Routing with History–Model Joint Embeddings.** ACL 2026. DOI: `10.18653/v1/2026.acl-long.2045`. https://aclanthology.org/2026.acl-long.2045/
3. Li, H. et al. (2026). **LLMRouterBench: A Massive Benchmark and Unified Framework for LLM Routing.** Findings ACL 2026. DOI: `10.18653/v1/2026.findings-acl.1881`. https://aclanthology.org/2026.findings-acl.1881/
4. Uddin, I. & Bauer, A. (2026). **Conformal LLM Routing with Distribution-Free Safety Guarantees.** ACL 2026 SRW. DOI: `10.18653/v1/2026.acl-srw.70`. https://aclanthology.org/2026.acl-srw.70/
5. Varangot-Reille, C., Bouvard, C., Gourru, A. (2026). **Generalising LLM Routing using Past Performance Retrieval: A Few-Shot Router is Sufficient.** EACL 2026 SRW. DOI: `10.18653/v1/2026.eacl-srw.22`. https://aclanthology.org/2026.eacl-srw.22/
6. Kim, Y. & Liu, X. et al. (2026). **Towards a science of scaling agent systems: When and why agent systems work.** Google Research. https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/
7. Huang, J. et al. (2024). **Large Language Models Cannot Self-Correct Reasoning Yet.** ICLR 2024. https://openreview.net/forum?id=IkmD3fKBPQ
8. Chen, L., Zaharia, M., Zou, J. (2023). **FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance.** arXiv:2305.05176. https://arxiv.org/abs/2305.05176
9. Ong, I. et al. (2024). **RouteLLM: Learning to Route LLMs with Preference Data.** arXiv:2406.18665. https://arxiv.org/abs/2406.18665
10. Fan, Z. et al. (2025). **SWE-Effi: Re-Evaluating Software AI Agent System Effectiveness Under Resource Constraints.** arXiv:2509.09853. https://arxiv.org/abs/2509.09853
11. Wang, Y., Pradel, M., Liu, Z. (2025). **Are “Solved Issues” in SWE-bench Really Solved Correctly? An Empirical Study.** arXiv:2503.15223. https://arxiv.org/abs/2503.15223
12. Li, C. et al. (2026). **Independent Patch Verification for Coding Agents with a Bidirectional Reconstruct-and-Verify Framework (RETRACE).** arXiv:2608.08950. https://arxiv.org/abs/2608.08950
13. OpenAI (2026-07-29). **How GPT-5.6 fuses frontier intelligence with frontier efficiency.** https://openai.com/index/gpt-5-6-frontier-intelligence-efficiency/
14. OpenAI (2026-07-09, updated 2026-07-30). **GPT-5.6: Frontier intelligence that scales with your ambition.** https://openai.com/index/gpt-5-6/

---

## Audit trail của lần đánh giá này

### Commands đã chạy

```text
npm test
cd resources/coding-tools-mcp && python -m pytest tests -q
cd resources/coding-tools-mcp && python -m benchmarks.tool_result_bytes --runs 5
```

Một invocation Python từ repository root đã fail ở collection do import path và được phân loại là **environment/invocation failure, not implementation failure**.

### Artifact benchmark mới

```text
resources/coding-tools-mcp/benchmarks/reports/tool-result-bytes-20260814-014333.json
```

### Orchestration finding

```text
agent_workflow execute -> BASE_DRIFT -> REPLAN
```

Không bypass gate; verification read-only sau đó dùng focused command execution.

### Thao tác không thực hiện

- không reset/restore/clean working tree;
- không commit;
- không push;
- không release/deploy;
- không thay đổi code production;
- chỉ tạo báo cáo audit này và benchmark JSON do benchmark tool sinh ra.
