# Coding Web Server-First Compute Orchestration

## Nghiên cứu tính khả thi, phương pháp luận và thiết kế điều phối để tạo accepted code nhanh nhất, rẻ nhất

**Ngày nghiên cứu:** 2026-08-16  
**Workspace:** `E:\Github\Tools-Codex-web`  
**Branch:** `main`  
**HEAD quan sát:** `415cb658f43cbd1d2456f65bf5649ed52b87ab25`  
**Ứng dụng:** `web-mcp-assistant 0.3.4`  
**MCP surface:** `smart-v3` — 8 public tools  
**Loại tài liệu:** research synthesis / feasibility assessment / methodology / target architecture / rollout gates  
**Trạng thái:** tài liệu ra quyết định; không phải tuyên bố rằng server-first scheduler đã được triển khai hoặc nghiệm thu production.

---

# 0. Mục tiêu chiến lược

Mục tiêu của hướng phát triển này được chuẩn hóa như sau:

> **Coding Web tự động phối hợp trí tuệ của ChatWeb với toàn bộ tài nguyên compute sẵn có để tạo accepted code nhanh nhất và rẻ nhất, trong khi máy người dùng chỉ chịu những workload thực sự cần chạy tại đó.**

Mục tiêu này không đồng nghĩa với:

- đẩy mọi command lên server;
- mở nhiều agent/worker nhất có thể;
- luôn chọn model rẻ nhất;
- luôn chạy song song;
- biến máy chủ thành mutation authority thứ hai;
- xây một hệ thống cluster/fleet-management tổng quát;
- tối ưu CPU utilization nhưng làm time-to-accepted-result xấu hơn.

Đích cần tối ưu là **accepted engineering outcome**, không phải một model call, một command, một cache hit, một benchmark xanh hoặc một dashboard đẹp.

---

# 1. Kết luận điều hành

## 1.1 Phán quyết tổng thể

Hướng server-first compute orchestration là **khả thi và phù hợp với kiến trúc hiện tại**, vì Coding Web đã có phần lớn primitive nền:

- ChatWeb giữ semantic/control plane và final acceptance;
- một Coding Tools Runtime giữ mutation authority;
- durable RUN/WAVE/ledger, controller lease, write fencing và proof lineage;
- Runner/project registry và cross-machine dispatch;
- QUIC/WebSocket/polling với Job reconciliation;
- structured process/script execution và durable Job observation;
- LIGHT/MEDIUM/HEAVY resource governor;
- managed process ownership, quiescence barrier và Windows Job Object;
- semantic localization, bounded context packet và focused proof.

Tuy nhiên, hệ thống **chưa có đủ bằng chứng để bật một scheduler tự học hoặc server-first auto-placement toàn diện**. Những phần còn thiếu có tính quyết định là:

1. **Compute Placement Contract:** mô tả task cần tài nguyên gì, node nào đủ điều kiện và vì sao được chọn.
2. **Exact Snapshot/Environment Identity:** chứng minh server đang phân tích, build hoặc test đúng source và đúng môi trường cần nghiệm thu.
3. **Remote Replica/Worktree Lifecycle:** tạo, đồng bộ, kiểm tra và dọn isolated remote checkout an toàn.
4. **Portable Proof Bundle:** proof remote chỉ được reuse khi source, command, parser, toolchain và platform fingerprint khớp.
5. **Accepted-result Economics:** đo queue, transfer, execution, proof, repair, review, human intervention và local burden theo cùng một RUN.
6. **Representative Paired Evaluation:** so sánh local-first và server-first trên cùng task/source/oracle thay vì suy luận từ vài sample không đối chứng.

## 1.2 Quyết định kiến trúc đề xuất

Kiến trúc đích nên là:

```text
USER INTENT
    |
    v
CHATWEB GPT-5.6 SOL
semantic brain + architecture + risk + final acceptance
    |
    v
CODING WEB CONTROL PLANE
EOCL + authority + task DAG + placement + economics
    |
    +-------------------------+--------------------------+
    |                         |                          |
    v                         v                          v
SERVER COMPUTE          SERVER COMPUTE              LOCAL EDGE
search/LSP/index        build/test/benchmark         GUI/device/secrets
static analysis         isolated candidate          local-only runtime
cache/proof             artifact/proof               final local-specific gate
    |                         |                          |
    +-------------------------+--------------------------+
                              |
                              v
                     EVIDENCE AGGREGATOR
                  exact identity + proof lineage
                              |
                              v
                       CHATWEB ACCEPT/REJECT
```

Nguyên tắc mặc định:

```text
DETERMINISTIC BEFORE MODEL
SERVER FIRST WHEN ELIGIBLE
LOCAL ONLY WHEN REQUIRED OR CHEAPER END-TO-END
ONE AUTHORITATIVE WRITER
EXACT IDENTITY BEFORE PROOF REUSE
ACCEPTED RESULT BEFORE UTILIZATION
```

## 1.3 Thứ tự đầu tư có ROI cao nhất

Thứ tự nên triển khai:

1. **Measurement plane cho TTAR/CAR và local burden.**
2. **Compute-node registry + shadow placement.**
3. **Exact source/environment identity.**
4. **Remote read-only analysis và semantic/cache warming.**
5. **Remote isolated worktree + focused proof bundle.**
6. **Server-first deterministic auto-placement có fallback.**
7. **Adaptive/contextual routing sau khi đủ paired evidence.**
8. **CAS/REAPI hoặc scheduler đa tenant chỉ khi quy mô thực tế biện minh.**

Không nên bắt đầu bằng Kubernetes, full Bazel REAPI, local LLM farm, GPU scheduling hoặc multi-agent fan-out.

---

# 2. Định nghĩa “accepted code” và North Star

## 2.1 Accepted code không đồng nghĩa test xanh

Một kết quả chỉ được coi là accepted khi đồng thời thỏa mãn:

```text
requested outcome exists
+ source identity is exact
+ patch/diff is coherent and within authority
+ required proof is valid for that identity
+ no unresolved hard blocker
+ local-affinity gates, if any, passed
+ acceptance owner reviewed evidence
+ final acceptance was recorded
```

Có thể biểu diễn:

```yaml
accepted_result:
  outcome_satisfied: true
  source_identity_complete: true
  patch_reviewed: true
  proof_set_complete: true
  hard_blockers: []
  local_specific_gate:
    required: false
    passed: null
  acceptance_owner: chatweb
  decision: accepted
```

Remote build/test xanh nhưng source local đã đổi là **không accepted**.  
Focused test xanh nhưng public behavior còn sai là **không accepted**.  
Model nói đã sửa xong nhưng không có proof là **không accepted**.  
Proof đúng nhưng chạy trên sai OS/toolchain cho contract cần nghiệm thu là **không accepted**.

## 2.2 North Star: Time to Accepted Result

Định nghĩa:

\[
TTAR = T_{context} + T_{queue} + T_{transfer} + T_{execution} + T_{proof} + T_{review} + T_{repair} + T_{handoff}
\]

Trong đó:

- `T_context`: localization, repository inspection và context packet;
- `T_queue`: chờ model/node/resource slot;
- `T_transfer`: sync source/input và trả artifact/proof;
- `T_execution`: edit/build/test/analysis thực tế;
- `T_proof`: focused, integration, release hoặc local-specific proof;
- `T_review`: semantic review và acceptance;
- `T_repair`: replan, retry có thêm evidence, sửa candidate;
- `T_handoff`: chuyển node/client/worker khi thật sự cần.

## 2.3 Cost per Accepted Result

\[
CAR = C_{model} + C_{remote\_compute} + C_{local\_opportunity} + C_{transfer} + C_{retry} + C_{review} + C_{maintenance}
\]

`C_local_opportunity` là chi phí thực tế của việc làm máy người dùng lag, chiếm CPU/RAM/I/O, làm gián đoạn công việc và kéo dài các task khác. Nó không nhất thiết là tiền mặt nhưng phải được theo dõi bằng:

- local CPU-minutes;
- local HEAVY-minutes;
- memory pressure/paging window;
- user-interactive slowdown;
- thời gian task khác bị block.

## 2.4 Hàm mục tiêu tổng hợp

Với một execution plan `p`:

\[
J(p) = E[TTAR_p] + \lambda_c E[CAR_p] + \lambda_l E[LocalBurden_p] + \lambda_r RiskPenalty_p
\]

Tối ưu phải tuân theo hard constraints trước. Không được dùng score để vượt:

- path/workspace boundary;
- write lease;
- secret locality;
- OS/hardware requirement;
- exact source identity;
- proof portability;
- destructive-action policy;
- final acceptance authority.

---

# 3. Bằng chứng nội bộ hiện tại

## 3.1 Phương pháp đọc dữ liệu

Nguồn canonical cho causal history là:

```text
.coding-tools/orchestration/ledger.sqlite3
```

Các file sau là projection hỗ trợ, không thay thế ledger:

```text
.coding-tools/performance.json
.coding-tools/task-history.json
.coding-tools/task-state.json
```

Số liệu dưới đây được quan sát ngày 2026-08-16 trên HEAD nêu đầu tài liệu. Runtime artifacts là dữ liệu volatile. Không dùng internal credit estimates như provider billing và không coi `unknown` là `0`.

## 3.2 Organic accepted-result baseline

Script repository-native:

```text
resources/coding-tools-mcp/scripts/report_rework_baseline.py
```

Kết quả scan 200 accepted runs gần nhất, loại 12 explicit-model-route runs, còn 188 model-free ChatWeb+MCP accepted runs:

| Chỉ số | Giá trị |
|---|---:|
| Accepted runs phân tích | 188 |
| First-pass accepted | 130 |
| First-pass rate | **69.15%** |
| Repaired accepted | 58 |
| Repaired rate | **30.85%** |
| Replan count trong nhóm repaired | 92 |
| First-pass TTA p50 | **36.357 s** |
| First-pass TTA p90 | **212.636 s** |
| Repaired TTA p50 | **192.319 s** |
| Repaired TTA p90 | **427.723 s** |
| Repaired/first-pass p50 multiplier | **5.29x** |
| Repaired/first-pass p90 multiplier | **2.01x** |

### Diễn giải

Đây là dữ kiện kinh tế quan trọng nhất của hệ thống hiện tại:

> Một run phải sửa lại có median TTAR gấp khoảng 5,29 lần run accepted first-pass.

Vì vậy, server offload chỉ tạo ROI khi nó:

- tăng first-pass acceptance;
- giảm repair/replan;
- giảm TTAR tổng;
- hoặc giảm local burden mà không làm TTAR/CAR xấu đi quá mức.

Chạy remote nhanh hơn 20 giây nhưng làm xác suất repair tăng là một placement xấu.

## 3.3 Performance projection hiện tại

Snapshot `performance.json` v5 trong lần phân tích này:

| Chỉ số | Giá trị quan sát | Ý nghĩa |
|---|---:|---|
| Tool calls | 1,511 | Aggregate calls, không phải unique tasks |
| Errors | 107 | Cần phân lớp theo workload/dev-test/prod |
| Generic cache hits | 8 | Không đồng nghĩa proof reuse |
| Local execution | 7,623,580 ms | Khoảng 2.12 giờ |
| Estimated wait | 30,845,984 ms | Khoảng 8.57 giờ |
| Wait/local-execution ratio | **~4.05x** | Queue/model/tool round-trip là bottleneck lớn |
| Request bytes | 1,267,562 | Input vào tool plane |
| Raw response bytes | 88,795,570 | Internal output trước model shaping |
| Model-visible bytes | 2,457,296 | Phần thật sự vào model context |
| Proof-cache eligible | 94 | Có thể cân nhắc reuse |
| Proof-cache hits | **0** | Chưa tạo saved time |
| Proof-cache misses | 94 | 64 fingerprint changed, 30 cold |
| Proof-cache saved time | **0 ms** | Không được claim ROI |

### Phân tích phase/localization

Trên 61 phase samples:

- workspace phase tổng khoảng `60,000 ms`;
- localization phase tổng khoảng `910,655 ms`;
- materialization khoảng `823 ms`;
- localization trung bình xấp xỉ `14.9 s/sample` và là phần chi phối trong nhóm phase được đo.

Localization counters:

| Chỉ số | Giá trị |
|---|---:|
| Localization queries | 255 |
| LSP attempted queries | 161 |
| LSP handled queries | **5** |
| Text fallback queries | **250** |
| LSP available samples | 20 |

P3 đã sửa scope single-file và warm/cold concurrency, nhưng current projection cho thấy semantic provider vẫn chưa mang lại tỷ lệ handled đủ cao để gọi là production accelerator. Đây là một workload rất phù hợp để offload server và giữ index warm, nhưng phải đo lại sau activation thật.

## 3.4 Model-route evidence còn quá mỏng

Current route-resolved counts quan sát trong performance projection:

```text
deterministic: 490
mini:            1
luna:            1
terra:           1
sol_xhigh:       2
```

Script:

```text
resources/coding-tools-mcp/scripts/compare_route_policies.py
```

cho `chatweb_mcp` so với `mini` hiện trả:

```text
pair_count = 0
automatic_activation = false
hold = insufficient_paired_results
hold = insufficient_task_class_diversity
controller_cost_unobserved
```

Do đó không có cơ sở để dùng ML/router policy học từ model lanes ngay lúc này. Server-first placement nên khởi đầu bằng deterministic heuristics + shadow evaluation.

## 3.5 Kết luận từ baseline

Các bottleneck thực tế theo thứ tự ưu tiên:

1. **Rework/repair:** median penalty rất lớn.
2. **Wait/queue/round-trip:** estimated wait lớn hơn local execution khoảng 4 lần.
3. **Localization:** semantic handled thấp, fallback cao.
4. **Proof reuse:** 0/94 hit, chưa tạo giá trị.
5. **Routing evidence:** chưa đủ paired data.
6. **Raw result amplification:** raw response lớn hơn model-visible rất nhiều, gợi ý cần server-side aggregation và bounded evidence packet.

Hướng server-first phải xử lý chính các bottleneck này, không chỉ chuyển CPU từ local sang server.

---

# 4. Tính thực tế theo kiến trúc hiện tại

## 4.1 Primitive đã có

### Control/authority

- ChatWeb có thể giữ controller/final acceptance.
- One Runtime authority và write lease tách biệt controller semantics.
- RUN/WAVE/EOCL, replan, proof và acceptance được durable hóa.
- Managed process ownership và quiescence đã đưa OS lifecycle vào orchestration contract.

### Cross-machine execution

- Runner đăng ký project dưới dạng `agent:<client_id>:<project_id>`.
- Server có thể dispatch file/Git/validation/process/Job tới Runner sở hữu project.
- QUIC/WebSocket/polling dùng cùng execution envelope.
- Runtime status đã có online/stale/offline, transport, last seen, pending requests và active jobs.

### Durable execution

- Structured executable/argv và script payload tránh shell quoting không cần thiết.
- Một execution có thể chuyển từ synchronous grace sang cùng một durable Job mà không restart.
- Observation token và batch Job observation giảm model turns.
- Reconnect reconciliation giữ state trong giới hạn same Runner instance.

### Resource control

- LIGHT/MEDIUM/HEAVY classification.
- HEAVY semaphore theo checkout.
- memory/foreign-heavy gate.
- Windows Job Object/process group.
- terminal-wave quiescence barrier.

### Context/proof

- Bounded repository fingerprint.
- semantic LSP bridge + text fallback.
- bounded candidate packet.
- proof identity/reuse framework đã có nhưng hit rate chưa đạt.

## 4.2 Khoảng trống không thể bỏ qua

| Khoảng trống | Tác động nếu bỏ qua |
|---|---|
| Node capability/capacity chưa thành placement contract | Chọn node bằng phỏng đoán |
| Không có exact remote snapshot identity đủ mạnh | Proof trên sai source có thể bị reuse |
| Chưa có remote worktree lifecycle chuẩn | Dirty/cross-run contamination |
| Environment/toolchain fingerprint chưa thống nhất | False cache hit, proof không portable |
| Queue/transfer/cache timing chưa nối vào TTAR | Server “nhanh” trên giấy nhưng chậm end-to-end |
| Không có local-affinity classifier | Đẩy GUI/secret/device task lên sai node |
| Không có placement shadow/counterfactual log | Không biết quyết định router đúng hay sai |
| Không có accepted-result cost đầy đủ | Cost model bị lệch, unknown bị hiểu nhầm là free |
| Cross-runner migration chưa có | Không được giả định Job có thể tự chuyển node |
| Same execution có thể outcome unknown | Retry remote có nguy cơ duplicate side effect |

## 4.3 Đánh giá khả thi theo loại workload

| Workload | Khả thi server-first | Điều kiện |
|---|---:|---|
| Text/AST/LSP search | **Rất cao** | Snapshot đúng, index/cache warm |
| Dependency/call graph | **Rất cao** | Toolchain/index compatible |
| Static analysis/lint | **Cao** | Config và platform match |
| Unit tests platform-neutral | **Cao** | Lockfile/toolchain/env identity |
| Rust/Node/Python build | **Cao** | Cache + target/profile/toolchain exact |
| Cross-platform integration tests | **Trung bình** | Node đúng OS/arch hoặc matrix proof |
| Remote candidate patch | **Trung bình-cao** | Isolated worktree, no direct authoritative write |
| Release/package/sign | **Trung bình-thấp** | Secret/signing/OS constraints |
| Electron GUI acceptance | **Thấp trên Linux server** | Cần Windows/desktop runner hoặc local edge |
| Device/hardware integration | **Thấp** | Phải chạy node gắn thiết bị |
| Local production reproduction | **Thấp** | Trạng thái thực chỉ có ở local |
| Tiny command 1–2 giây | **Thường không đáng offload** | Transfer/queue có thể lớn hơn exec |

---

# 5. Bài học từ các dự án và nghiên cứu đã thảo luận

## 5.1 Tools-Codex-web / WebCodex

### Phần nên giữ nguyên

- ChatWeb Sol là semantic/control plane.
- Coding Tools MCP là deterministic writer/oracle plane.
- 8-tool smart surface.
- one-runtime authority.
- explicit lease/fencing.
- proof-first acceptance.
- fail-closed routing và recovery.

### Phần cần mở rộng

- từ model routing sang **model + compute + proof routing**;
- từ host resource governor sang **multi-node placement**;
- từ project registry sang **node capability/cache/replica registry**;
- từ proof fingerprint cục bộ sang **portable execution snapshot identity**;
- từ operational telemetry sang **accepted-result economics**.

## 5.2 M365-Copilot2API

Dự án `HEXUXIU/M365-Copilot2API` có giá trị tham khảo ở:

- account/endpoint health;
- concurrency limit;
- cooldown/circuit breaker;
- API key lifecycle;
- usage aggregation;
- operational dashboard.

Bài học đưa vào Coding Web:

```text
node/lane health
+ cooldown
+ failover
+ per-node concurrency
+ usage/economics projection
```

Không nên copy:

- M365 private protocol/reverse engineering;
- generic account round-robin;
- một API key đồng nghĩa toàn quyền;
- conversation reuse heuristic làm nguồn continuity cho coding authority.

## 5.3 repository-harness

Dự án `hoangnb24/repository-harness` nhấn mạnh:

- repository là system of record;
- phân biệt Authoritative / Observed / Derived / Decision required / Unknown;
- invariant phải nối authority với mechanical proof;
- harness improvement phải có baseline, intervention và fresh rerun;
- không tạo task database/orchestrator thứ hai.

Áp dụng cho server-first:

- remote snapshot/proof không thay thế repository truth;
- node cache là derived state;
- scheduler policy không tự tạo product policy;
- mọi improvement phải được giữ/revise/remove theo representative rerun;
- không xây parallel lifecycle ngoài EOCL/ledger.

## 5.4 DeepSeek/OpenCode-style lower-cost execution

Các provider/model rẻ hơn có thể tạo candidate hoặc analysis packet với chi phí thấp, nhưng dữ liệu nội bộ trước đây cho thấy:

- provider path có thể hoạt động end-to-end và có cost telemetry tốt;
- autonomous execution vẫn chịu prompt-size, timeout, capacity và harness failures;
- chi phí mỗi call thấp không đảm bảo cost per accepted result thấp;
- model lane phải giữ candidate-only cho đến khi có representative accepted-work evidence.

Hướng đúng là:

```text
ChatWeb settles semantics
-> deterministic server collects evidence
-> bounded candidate packet to lower-cost model when justified
-> server/local oracle proves
-> ChatWeb accepts
```

Không dùng lower-cost model để thay thế exact proof hoặc authority.

## 5.5 Bazel Remote Execution API

Remote Execution API đưa ra các nguyên tắc rất phù hợp:

- một `Action` phải chứa đủ dữ kiện để tái lập execution;
- action được định danh bằng digest;
- `command_digest`, `input_root_digest`, timeout và platform requirements thuộc identity;
- input/output lưu trong content-addressable storage;
- action result có thể cache;
- server chỉ chạy trên worker thỏa platform requirements;
- cùng một request/action không tự động đồng nghĩa exactly-once side effect.

Bài học cho Coding Web:

1. Tạo `ExecutionSnapshotIdentity`, không chỉ `HEAD`.
2. Cache proof theo full action identity.
3. Platform/toolchain/timeout là một phần identity.
4. Remote execution chỉ an toàn cho reproducible/bounded actions.
5. Không cần triển khai full REAPI ngay; có thể học contract trước.

## 5.6 sccache

`sccache` cung cấp:

- local/remote compiler cache;
- multi-level cache;
- distributed compilation cho Rust/C/C++;
- authentication, transport encryption và sandboxed build servers.

Giá trị thực dụng:

- triển khai compiler cache có thể tạo ROI sớm hơn full remote execution;
- server warm cache giảm build latency;
- cache hit phải xét target/profile/compiler/flags/path normalization;
- Rust incremental/final link có giới hạn cacheability, nên không được ước lượng savings từ compile units như thể toàn build cache được.

## 5.7 HEFT, DRF và Ray

### HEFT

HEFT xem workload là DAG trên heterogeneous processors và ưu tiên task theo upward rank/critical path, rồi chọn processor có earliest finish time. Coding task cũng có DAG tự nhiên:

```text
localize
-> diagnose
-> candidate
-> focused proof
-> integration proof
-> accept
```

HEFT phù hợp cho placement v2 khi đã có execution-time estimates và transfer costs.

### DRF

Dominant Resource Fairness hữu ích khi có nhiều project/user cùng cạnh tranh CPU, RAM, disk hoặc GPU. Với một operator/số node nhỏ, DRF chưa phải P0; HEAVY semaphore + queue policy đơn giản đủ trước.

### Ray

Ray cho thấy giá trị của:

- task/actor abstraction;
- distributed scheduler;
- fault-tolerant control/object state;
- separation giữa task graph và worker execution.

Coding Web không cần trở thành Ray, nhưng nên giữ cùng nguyên tắc: control state ở một plane, worker execution ở node, output/evidence có identity và recovery semantics rõ.

## 5.8 RouteLLM, FrugalGPT và adaptive routing

RouteLLM/FrugalGPT chứng minh tiềm năng route giữa strong/weak models để giảm chi phí, nhưng điểm quan trọng nhất cho dự án này là:

- threshold phải calibrate trên query distribution thực;
- quality floor phải được giữ;
- benchmark savings không tự chuyển thành local coding savings;
- cascade dài có thể làm TTAR xấu;
- outcome của route phải là accepted result, không phải judge score riêng lẻ.

Hệ thống hiện chưa đủ paired samples để học router. Giai đoạn đầu nên dùng deterministic hierarchical router; contextual bandit chỉ mở sau.

## 5.9 SWE-agent và Agent-Computer Interface

SWE-agent cho thấy interface/tool design ảnh hưởng mạnh tới hiệu năng agent. Điều này củng cố:

- giữ smart-v3 nhỏ;
- structured process/patch/proof thay vì raw shell/text;
- server trả compact evidence thay vì raw logs;
- rõ trạng thái success/no-output/error;
- không expose compute nodes/models thành hàng chục public tools.

Compute placement phải internalize trong Coding MCP/EOCL, không tăng selection entropy cho ChatWeb.

---

# 6. Phương pháp luận cốt lõi

## 6.1 Tối ưu accepted work, không tối ưu activity

Một feature chỉ được giữ nếu cải thiện ít nhất một metric mà không phá quality floor:

- TTAR;
- CAR;
- first-pass acceptance;
- repair rate;
- human-intervention rate;
- local burden;
- accepted tasks/hour.

Không dùng làm success metric độc lập:

- số agent;
- số model calls;
- CPU utilization;
- cache hit count;
- số tools;
- số tests;
- lines of code;
- số task được “dispatch”.

## 6.2 Tách bốn quyết định

Không gộp tất cả thành một opaque router.

```text
1. SEMANTIC ROUTE
   ai quyết định/viết candidate?

2. COMPUTE PLACEMENT
   node nào chạy deterministic workload?

3. CONTEXT PLAN
   evidence nào cần đưa cho model?

4. PROOF PLAN
   proof rẻ nhất nhưng đủ authoritative là gì?
```

Ví dụ:

```yaml
plan:
  controller: chatweb_sol
  context:
    node: server_a
    method: lsp_plus_targeted_search
  candidate:
    route: deterministic_mcp
    node: server_a
  proof:
    focused: server_a
    windows_gui: local_pc
  acceptance: chatweb
```

## 6.3 Server-first là prior, không phải absolute rule

Chính sách:

```text
eligible remote node exists
AND expected accepted-result utility is better
AND no local-affinity constraint
THEN prefer server
ELSE local
```

Không được viết:

```text
if server online -> remote
```

## 6.4 Deterministic evidence trước model reasoning

Server nên làm:

- search/LSP;
- compiler/test/lint;
- dependency graph;
- Git diff/history;
- log parsing;
- artifact hashing;
- environment fingerprint;
- benchmark execution.

ChatWeb nên làm:

- user intent;
- architecture;
- ambiguity resolution;
- risk and integration reasoning;
- conflict resolution;
- final acceptance.

## 6.5 Một authority, nhiều compute nodes

Remote node không có quyền tự nhận authoritative write. Topology mặc định:

```text
local authoritative checkout
        |
        | exact snapshot bundle
        v
remote isolated worktree
        |
        | candidate patch + proof bundle
        v
Coding MCP validates
        |
        | apply under write lease
        v
local authoritative checkout
        |
        v
final proof / acceptance
```

## 6.6 Exact identity trước cache/reuse

Không reuse proof dựa trên:

- cùng file name;
- cùng HEAD nhưng dirty diff khác;
- cùng command text nhưng toolchain khác;
- cùng tests nhưng parser/version khác;
- “gần giống” environment;
- timestamp gần nhau.

## 6.7 Parallelism phải có positive expected value

Chỉ parallelize khi:

```text
independent READY tasks
+ disjoint write ownership
+ stable shared interfaces
+ enough review/proof capacity
+ expected saved critical-path time > startup + sync + merge + review cost
```

Không chạy hai HEAVY builds cùng checkout chỉ vì có hai node.

## 6.8 Shadow → paired → canary → promote

Mọi policy mới đi qua bốn bước:

1. `shadow`: tính placement nhưng không thay behavior;
2. `paired`: cùng task/source/oracle trên baseline và candidate policy;
3. `canary`: giới hạn task classes và budget;
4. `promote`: chỉ khi quality floor, sample diversity và economics đạt gate.

---

# 7. Target architecture chi tiết

## 7.1 Các plane

### A. Semantic Control Plane

Owner: ChatWeb Sol.

Chịu trách nhiệm:

- hiểu objective;
- xác định accepted outcome;
- phân loại risk/ambiguity;
- settle shared contracts;
- quyết định cần model candidate hay deterministic path;
- review và final acceptance.

### B. Orchestration and Placement Plane

Owner: EOCL/Coding Tools Runtime.

Chịu trách nhiệm:

- RUN/WAVE state;
- task DAG;
- node eligibility;
- queue/admission;
- placement reason;
- write/process ownership;
- retries/replans;
- economics/provenance.

### C. Compute Plane

Node types:

```text
server_compute
server_gpu_optional
windows_build_runner
local_workstation
specialized_device_runner
```

Chịu trách nhiệm:

- deterministic execution;
- isolated candidate execution;
- cache/index;
- bounded artifact/proof return.

### D. Data and Cache Plane

Các lớp:

```text
repository mirror
snapshot/patch CAS-lite
semantic index
package/dependency cache
compiler cache
artifact cache
proof cache
```

### E. Evidence and Acceptance Plane

Chịu trách nhiệm:

- source/environment identity;
- proof bundle;
- timing provenance;
- diff/patch identity;
- hard blockers;
- acceptance event.

### F. Operator Plane

Execution Control Center hiển thị:

- Brain/controller;
- current RUN/WAVE;
- node chosen và reason;
- node health/queue/cache;
- local protection state;
- proof identity;
- estimated vs observed savings;
- fallback/replan;
- no hidden worker.

## 7.2 Không tạo public tool mới

Model-facing smart surface vẫn 8 tools. Compute placement là internal concern của:

```text
agent_workflow
task_control
exec_command/Job execution
```

ChatWeb có thể truyền intent/constraints, nhưng không phải tự chọn bằng cách gọi `server_a_tool`, `server_b_tool`, `local_tool`.

---

# 8. Core data contracts

## 8.1 WorkloadDescriptor

```yaml
workload:
  id: wl_...
  run_id: ...
  wave_id: ...
  kind: search | lsp | static_analysis | build | test | benchmark | candidate
  task_class: rust_cross_file_bug
  resource_class: LIGHT | MEDIUM | HEAVY

  estimates:
    cpu_cores: 8
    memory_mb: 8192
    disk_mb: 4096
    expected_exec_ms: 120000
    output_mb: 20

  requirements:
    os: windows | linux | any
    arch: x86_64
    toolchains:
      rustc: exact_fingerprint
    network: denied | allowed | required
    gui: false
    device_tags: []
    secrets_scope: none

  source:
    snapshot_identity: sha256:...
    write_mode: read_only | isolated_candidate | authoritative

  proof:
    oracle_id: ...
    portability: platform_neutral | platform_specific

  policy:
    server_first: true
    local_allowed: true
    deadline_ms: 600000
    idempotency_class: pure | retry_safe | side_effecting
```

## 8.2 ComputeNodeSnapshot

```yaml
node:
  node_id: server-a
  role: server_compute
  observed_at: ...
  status: healthy | degraded | cooldown | offline

  platform:
    os: linux
    arch: x86_64
    cpu_cores: 32
    memory_total_mb: 65536
    disk_free_mb: 800000

  capabilities:
    rust: true
    nodejs: true
    python: true
    docker: true
    windows_gui: false
    gpu_cuda: false

  dynamic:
    cpu_load: 0.31
    memory_pressure: 0.24
    disk_pressure: 0.10
    active_jobs: 2
    queued_jobs: 1
    heavy_slots_free: 1

  locality:
    repo_snapshots:
      - repo_id: tools-codex-web
        head: 415cb...
        snapshot_digest: sha256:...
    cache:
      cargo: warm
      semantic_index: warm
      npm: cold

  transport:
    mode: quic
    latency_ms: 18
    recent_error_rate: 0.01
```

## 8.3 ExecutionSnapshotIdentity

Đề xuất:

```text
ExecutionSnapshotIdentity = SHA256(
  schema_version
  + repository_id
  + canonical_base_commit
  + normalized_tracked_diff_digest
  + bounded_relevant_untracked_digest
  + instruction_fingerprint
  + dependency_lock_fingerprints
  + command/argv/script_digest
  + cwd
  + declared_environment_allowlist_digest
  + toolchain_manifest_digest
  + OS/arch/target/profile/features
  + sandbox/policy identity
  + timeout
  + proof parser/version
  + output contract
)
```

Không đưa raw secret vào fingerprint/log. Với secret-dependent proof, dùng secret-scope identity/epoch do secret owner phát hành, không hash raw secret vào telemetry.

## 8.4 ProofBundle

```yaml
proof_bundle:
  proof_id: ...
  snapshot_identity: sha256:...
  node_id: server-a
  runner_instance_id: ...
  command_identity: sha256:...
  oracle_id: ...
  parser_version: ...
  platform_manifest: sha256:...

  result:
    status: passed | failed | unknown
    exit_code: 0
    assertions: 42
    failures: 0

  timing:
    queued_ms: ...
    transfer_ms: ...
    execution_ms: ...
    collection_ms: ...

  outputs:
    bounded_summary: ...
    artifact_digests: []

  completeness:
    complete: true
    truncation: false
    missing_fields: []
```

## 8.5 PlacementDecision

```yaml
placement:
  decision_id: ...
  workload_id: ...
  policy: server_first_v1
  eligible_nodes: [server-a, local-pc]
  rejected_nodes:
    server-b: RUNNER_DEGRADED

  selected_node: server-a
  reason_codes:
    - REMOTE_CACHE_WARM
    - REMOTE_EXPECTED_FINISH_LOWER
    - LOCAL_INTERACTIVE_PROTECTION

  estimates:
    queue_ms: 10000
    transfer_ms: 7000
    execution_ms: 90000
    total_to_proof_ms: 107000
    local_alternative_ms: 260000

  confidence: low | medium | high
  shadow_only: true
```

## 8.6 Stable reason codes

Tối thiểu:

```text
LOCAL_AFFINITY_GUI
LOCAL_AFFINITY_DEVICE
LOCAL_AFFINITY_SECRET
LOCAL_AFFINITY_RUNTIME_STATE
REMOTE_PLATFORM_MISMATCH
REMOTE_TOOLCHAIN_MISMATCH
REMOTE_CACHE_WARM
REMOTE_QUEUE_SHORTER
REMOTE_EXPECTED_FINISH_LOWER
LOCAL_TINY_TASK_FASTER
LOCAL_INTERACTIVE_PROTECTION
SNAPSHOT_IDENTITY_INCOMPLETE
PROOF_NOT_PORTABLE
RUNNER_DEGRADED
RUNNER_CAPACITY_EXHAUSTED
TRANSPORT_UNHEALTHY
WRITE_AUTHORITY_LOCAL_ONLY
SIDE_EFFECT_RETRY_UNSAFE
PLACEMENT_EVIDENCE_INSUFFICIENT
```

---

# 9. Eligibility filter trước khi scoring

Mọi placement phải đi qua hard filter.

## 9.1 Local-affinity filter

Workload bắt buộc local khi cần:

- Electron/desktop GUI thật;
- physical device;
- local browser profile/session;
- credential/signing key không được phép rời máy;
- trạng thái production/runtime chỉ tồn tại local;
- local network/service không accessible từ server;
- Windows-only behavior nhưng không có Windows remote runner đủ chuẩn;
- user-facing latency nhỏ đến mức offload overhead chắc chắn lớn hơn.

## 9.2 Source eligibility

Remote chỉ eligible khi:

- base commit có thể fetch/verify;
- dirty patch được đóng gói deterministic;
- relevant untracked inputs được liệt kê/hash;
- ignored state có owner và policy rõ;
- instruction/config/lockfile fingerprints đầy đủ;
- replica apply sạch và post-apply digest khớp.

## 9.3 Environment eligibility

Node phải khớp:

- OS/arch/target triple;
- compiler/runtime version;
- feature/profile flags;
- system dependency contract;
- sandbox/network mode;
- environment allowlist;
- secret/device capability;
- proof parser version.

## 9.4 Authority eligibility

- isolated candidate không được có authoritative write lease;
- authoritative mutation chỉ qua one Runtime owner;
- active checkout write fence phải được tôn trọng;
- remote node không tự apply vào local checkout;
- task/wave/process ownership phải được ghi trước spawn.

## 9.5 Retry/idempotency eligibility

- pure/read-only: retry/hedge có thể cho phép;
- retry-safe exact action: retry với cùng idempotency key;
- side-effecting/outcome unknown: không auto retry;
- same execution Job handoff: observe same Job, không restart.

---

# 10. Thuật toán placement đề xuất

## 10.1 Giai đoạn 1: deterministic weighted placement

Không dùng ML ở P0/P1.

Với mỗi node eligible `n`:

\[
EFT(n) = Queue(n) + Transfer(n) + Exec(w,n) + Proof(w,n) + Return(n)
\]

Thêm expected repair:

\[
E[TTAR(n)] = EFT(n) + P_{fail}(w,n) \times E[RepairCost(w,n)]
\]

Score:

\[
Score(n) = E[TTAR(n)] + \lambda_c Cost(n) + \lambda_l LocalBurden(n) + \lambda_r Risk(n)
\]

Chọn node có score thấp nhất sau hard filter.

### Ước lượng ban đầu

- `Queue(n)`: active/queued jobs + resource class slots;
- `Transfer(n)`: missing bytes / observed throughput + setup;
- `Exec(w,n)`: median của `(task_class, workload_kind, node, cache_stratum)`;
- `Proof(w,n)`: historical median theo oracle;
- `P_fail`: smoothed empirical rate; thiếu data dùng conservative prior;
- `LocalBurden`: cao nếu `local_interactive=true` và workload HEAVY;
- `Risk`: platform mismatch uncertainty, partial identity, degraded transport.

## 10.2 Pseudocode placement v1

```python
def choose_node(workload, nodes, policy):
    eligible = []

    for node in nodes:
        rejection = hard_constraint_violation(workload, node)
        if rejection:
            record_rejection(node, rejection)
            continue

        estimate = estimate_plan(workload, node)
        score = (
            estimate.expected_ttar_ms
            + policy.cost_weight * estimate.expected_cost
            + policy.local_burden_weight * estimate.local_burden
            + policy.risk_weight * estimate.risk_penalty
        )
        eligible.append((score, node, estimate))

    if not eligible:
        return blocked_or_local_fallback(workload)

    score, node, estimate = min(eligible, key=lambda item: item[0])
    return auditable_decision(node, estimate, score)
```

## 10.3 Server-first prior

Không cộng ưu tiên server tùy tiện. Dùng prior nhỏ hoặc tie-break:

```text
nếu expected score gần tương đương
AND remote eligible
AND local interactive
THEN server wins tie
```

Như vậy server-first không làm tiny task chậm chỉ để tăng offload ratio.

## 10.4 Break-even condition

Remote có lợi khi:

\[
T_{sync} + T_{queue,remote} + T_{exec,remote} + T_{return} + E[T_{repair,remote}]
<
T_{queue,local} + T_{exec,local} + E[T_{repair,local}] + InteractivePenalty
\]

Nếu command local 2 giây và remote setup 8 giây, chạy local.  
Nếu release build local 10 phút và server warm cache 2 phút + transfer 20 giây, remote.

## 10.5 Task DAG và HEFT-like scheduling

Khi một RUN có nhiều READY nodes:

```text
localize ----> diagnose ----> patch ----> focused proof ----> integration proof
      \---------------------> static analysis --------------------/
```

Dùng HEFT-like approach:

1. tính upward rank theo estimated execution + communication;
2. ưu tiên task trên critical path;
3. với mỗi task, chọn node có earliest finish time;
4. không parallelize nodes có dependency hoặc write overlap;
5. cache/data locality thuộc communication cost.

Không cần triển khai full HEFT ngay. V1 có thể dùng:

```text
critical path first
+ earliest eligible finish
+ cache-locality bonus
+ HEAVY admission
```

## 10.6 Queue policy

Single operator/small fleet:

- LIGHT: bounded concurrent;
- MEDIUM: bounded theo CPU/memory;
- HEAVY: một slot/checkout hoặc node capacity-aware;
- urgent critical-path proof ưu tiên hơn speculative background analysis;
- short deterministic reads có thể đi trước long queued HEAVY nếu không starve.

Multi-project/multi-user sau này:

- áp dụng DRF hoặc weighted dominant-share;
- project priority và budget;
- tránh một project chiếm toàn RAM/CPU/GPU.

## 10.7 Health/circuit breaker

Mỗi node/lane có state:

```text
HEALTHY
DEGRADED
CAPACITY_LIMITED
RATE_LIMITED
AUTH_EXPIRED
TIMEOUT_PRONE
CIRCUIT_OPEN
COOLING_DOWN
OFFLINE
```

Circuit mở khi:

- consecutive transport failures;
- repeated capacity rejection;
- timeout rate vượt threshold;
- snapshot/proof corruption;
- runner instance churn;
- resource pressure vượt safe limit.

Không retry unchanged failure trên cùng node; phải thêm evidence, đổi node hoặc replan.

## 10.8 Hedged execution

Chỉ cân nhắc cho:

- pure read-only search;
- deterministic idempotent query;
- tail latency cao;
- output nhỏ;
- không HEAVY;
- không side effect.

Không hedge build/test/candidate write mặc định vì tăng compute cost và có thể tạo duplicate/ambiguous outcomes.

---

# 11. Joint model–compute–proof routing

## 11.1 Không giải bài toán tổ hợp bằng brute force

Không thử mọi tổ hợp:

```text
model x node x proof strategy x context strategy
```

Dùng hierarchical decision:

```text
A. classify semantics/risk/oracle
B. choose semantic route
C. choose compute node for deterministic stages
D. choose cheapest sufficient proof
E. replan only when new evidence changes classification
```

## 11.2 Semantic route

```text
deterministic
mini candidate
luna candidate
terra experiment
sol_xhigh deep lane
chatweb sol control/acceptance
```

Runtime authorization luôn thắng semantic suggestion.

## 11.3 Context route

Server tạo evidence packet:

```text
objective
affected symbols
call/dependency chain
exact source snippets
failing oracle
constraints/invariants
expected proof
stop conditions
```

Không gửi toàn repo/raw logs nếu server có thể tổng hợp deterministic.

## 11.4 Proof route

Ladder:

1. syntax/static/diff;
2. focused behavior/reproduction;
3. affected subsystem/consumer boundary;
4. platform/local-specific proof;
5. broad release gate chỉ khi cần.

Dừng ở mức thấp nhất đủ authoritative.

## 11.5 Contextual bandit — chỉ sau khi đủ dữ liệu

Sau deterministic v1 và representative cohorts, có thể mô hình hóa action:

```text
action = (semantic_route, compute_node_class, proof_policy)
```

Context:

```text
task_class
integration_width
oracle_strength
risk
estimated resource profile
cache state
node health
network
local interactive state
```

Reward ví dụ:

\[
R = w_a Accepted - w_t \log(1 + TTAR) - w_c CAR - w_h HumanIntervention - w_l LocalBurden
\]

Các constraint:

- rejected/hard-safety violation có penalty rất lớn;
- exploration chỉ trên low-risk task classes;
- no exploration với secrets/destructive/public-contract work;
- confidence interval và minimum sample gate;
- shadow decisions trước auto action;
- model cost unknown không được coi là zero.

Thompson Sampling/UCB có thể phù hợp hơn supervised router ban đầu vì policy phải học online, nhưng chỉ khi logging đủ causal và action space được giới hạn.

---

# 12. Remote repository replica và proof reuse

## 12.1 Không sync tùy tiện toàn máy local

Remote replica nên được dựng từ:

```text
verified Git base
+ normalized tracked patch
+ explicitly included relevant untracked inputs
+ bounded instruction/config/lockfile set
```

Không copy:

- secrets;
- global user config không cần thiết;
- arbitrary ignored directories;
- local caches như source truth;
- process/runtime state không portable.

## 12.2 Replica workflow

```text
1. resolve repository id and base commit
2. ensure server mirror has commit
3. create isolated worktree for run/wave
4. apply normalized patch bundle
5. verify post-apply snapshot digest
6. materialize declared environment/toolchain
7. run read-only/candidate/proof workload
8. return patch/artifact/proof bundle
9. mark terminal and clean according to retention policy
```

## 12.3 Proof reuse gate

Reuse chỉ khi:

```text
current_snapshot_identity == proof.snapshot_identity
AND oracle_id matches
AND parser_version matches
AND proof complete
AND required platform contract matches
AND no relevant file/config/toolchain drift
```

Nếu fingerprint partial/unknown:

```text
reuse = false
reason = IDENTITY_INCOMPLETE
```

## 12.4 Cache hierarchy

### Layer 1 — Repository mirror

Giảm fetch/sync base commits.

### Layer 2 — Dependency/package cache

Cargo registry/git, npm/pnpm, pip/wheels theo policy; không biến cache thành undeclared input.

### Layer 3 — Compiler cache

`sccache` hoặc tương đương; đo actual hit/saved time.

### Layer 4 — Semantic index

Warm LSP/index theo exact repo/toolchain config.

### Layer 5 — Artifact cache

Chỉ output contract đã khai báo.

### Layer 6 — Proof cache

Key bằng exact execution/proof identity.

## 12.5 Khi nào cân nhắc CAS/REAPI

Chỉ khi dữ liệu cho thấy:

- nhiều repo/nodes lặp input lớn;
- transfer trở thành bottleneck;
- proof/artifact reuse đủ thường xuyên;
- cần interoperability với build tools;
- maintenance cost được biện minh.

P0/P1 chỉ cần CAS-lite bằng digest-addressed snapshot/artifact store, không cần full protocol.

---

# 13. Local-affinity policy

## 13.1 Matrix

| Affinity | Server | Local | Ghi chú |
|---|---:|---:|---|
| Source search/LSP | ưu tiên | fallback | Server index warm có lợi |
| Static analysis | ưu tiên | fallback | Platform/config phải match |
| Unit tests portable | ưu tiên | fallback | Snapshot exact |
| Linux build | ưu tiên Linux server | không cần | Nếu release target Linux |
| Windows build | Windows server nếu có | local fallback | Linux proof không thay Windows proof |
| Electron GUI | chỉ desktop runner | **ưu tiên** | Cần real UI/runtime |
| USB/device | node gắn thiết bị | **thường local** | Capability tag bắt buộc |
| Code signing | secret-owner node | thường local | Không chuyển private key tùy tiện |
| Local service reproduction | chỉ nếu tunnel/replica đủ | **ưu tiên** | State locality |
| Tiny command | tùy break-even | thường local | Queue/transfer overhead |

## 13.2 Interactive Protection

Khi người dùng đang dùng máy:

```yaml
local_interactive:
  active: true
  heavy_penalty: high
  memory_pressure_limit: ...
  background_cpu_budget: ...
```

HEAVY local placement chỉ khi:

- local-affinity bắt buộc;
- không có remote eligible;
- hoặc remote end-to-end dự kiến tệ hơn đáng kể.

## 13.3 Local burden metrics

```text
local_cpu_minutes
local_heavy_minutes
local_peak_working_set
local_page_fault_pressure
local_disk_busy_time
interactive_slowdown_events
local_jobs_avoided
```

Server offload ratio chỉ là supporting metric; không phải North Star.

---

# 14. Observability và Execution Control Center

## 14.1 Cần hiển thị gì

```text
RUN / WAVE
controller / acceptance owner
semantic route
selected compute node
workload/resource class
snapshot identity status
queue / transfer / execute / proof phase
node health and cache state
local interactive protection
estimated saving vs observed result
fallback/replan reason
proof completeness
```

Ví dụ:

```text
RUN #1042 — focused Rust repair

Brain:           ChatWeb Sol
Writer:          Coding MCP
Compute:         server-a
Resource:        HEAVY
Placement:       local -> server-a
Reason:          cache warm + local interactive + lower EFT
Snapshot:        exact
Proof:           focused PASS, Windows GUI not required
Estimated TTAR:  112s
Observed TTAR:   126s
Local saved:     4.8 HEAVY-min
Acceptance:      pending ChatWeb review
```

## 14.2 Provenance bắt buộc

Mọi timing/cost phải gắn:

```text
observed
provider_reported
derived
estimated
unknown
```

Không relabel inter-tool gap thành model latency. Không cộng unknown cost như zero.

## 14.3 Metrics

### North Star

- `ttar_ms`;
- `cost_per_accepted_result`;
- `accepted_tasks_per_active_hour`.

### Quality

- first-pass acceptance;
- repair/replan rate;
- post-accept defect evidence;
- human intervention;
- acceptance by task class.

### Placement

- server offload ratio;
- local-required ratio;
- placement regret;
- node fallback rate;
- circuit-open events;
- queue prediction error;
- execution prediction error.

### Local burden

- local HEAVY-minutes saved;
- local CPU-minutes saved;
- local interactive protection activations;
- local resource-pressure incidents.

### Cache/data

- snapshot transfer bytes;
- mirror hit;
- dependency-cache hit;
- compiler-cache hit/saved time;
- semantic-index hit;
- proof-cache hit/saved time;
- raw/model-visible byte ratio.

### Model economics

- model calls/accepted result;
- provider-reported cost where available;
- candidate blocked/timeout/capacity;
- route regret;
- context bytes/accepted result.

---

# 15. Thiết kế thí nghiệm và phương pháp đánh giá

## 15.1 Task corpus đại diện

Tối thiểu bao phủ:

```text
local bug + strong oracle
local bug + weak oracle
cross-file semantic change
large-file deep symbol
test failure
build failure
static analysis
repository onboarding
long-running command
resource-heavy release build
Windows-specific behavior
Electron GUI behavior
resume after restart
multi-client handoff
stale schema
unsafe path/security rejection
```

Không chỉ dùng synthetic microbenchmarks.

## 15.2 Paired evaluation

Mỗi pair phải giữ:

```text
same source snapshot
same task semantics
same acceptance oracle
same relevant environment
same cache stratum label
same risk policy
```

So sánh:

```text
A: current local-first/control policy
B: server-first candidate policy
```

Randomize order khi có thể để giảm warm-cache/order bias.

## 15.3 Cold/warm strata

Tách:

- cold repo mirror;
- warm repo mirror;
- cold dependencies;
- warm compiler cache;
- cold semantic index;
- warm semantic index.

Không trộn cold và warm rồi báo một median duy nhất.

## 15.4 Acceptance gate cho policy

Một policy chỉ promote khi:

```text
quality floor not worse
+ enough paired accepted results
+ enough task-class diversity
+ TTAR improvement meaningful
+ CAR/local burden improvement observed
+ no safety/authority regression
+ rollback works
```

Initial practical gate đề xuất:

- ít nhất 10 pairs cho canary technical validation;
- ít nhất 3 task classes;
- trước broad auto-placement nên có khoảng 30+ representative pairs ở các class chính;
- task high-risk cần gate riêng, không gộp với low-risk average.

Đây là initial governance threshold, không phải định luật thống kê; phải điều chỉnh theo variance thực.

## 15.5 Causal caveats

Router chỉ quan sát outcome của action đã chọn, nên dễ selection bias. Giải pháp:

- paired/randomized low-risk studies;
- shadow counterfactual estimates;
- propensity/action logging nếu dùng bandit;
- không học từ benchmark/synthetic rows như production truth;
- không promote từ accepted-only survivor sample;
- tách capacity/availability failure khỏi capability nhưng vẫn tính vào deployed TTAR.

## 15.6 Fresh rerun rule

Mỗi optimization intervention phải có:

```text
baseline
hypothesis
intervention
native proof
fresh representative rerun
keep | revise | remove
```

Ví dụ:

```text
Hypothesis:
Warm remote semantic index giảm median localization từ 15s xuống <6s,
không làm first-pass acceptance giảm quá 2 điểm phần trăm.
```

Nếu chỉ giảm 15s xuống 13.8s nhưng thêm subsystem lớn, quyết định có thể là remove.

---

# 16. Roadmap triển khai theo gate

## Phase R0 — Baseline và measurement contract

### Deliverables

- chuẩn hóa TTAR/CAR/local burden fields trong ledger/projection;
- timing queue/transfer/exec/proof/review/repair;
- provider/derived/observed provenance;
- task-class/cache-stratum tags;
- current local-first baseline report;
- không đổi placement behavior.

### Acceptance

- một accepted RUN có timeline không chồng nghĩa;
- unknown cost không thành zero;
- first-pass/repaired classification tái lập từ ledger;
- UI/report đọc được cùng projection.

### Stop

Dừng nếu timing clock domains hoặc run↔host-turn binding chưa đủ chính xác.

## Phase R1 — Compute Node Registry + shadow placement

### Deliverables

- static capabilities;
- dynamic load/memory/disk/active jobs;
- transport health;
- repo/cache locality;
- local interactive state;
- deterministic placement score;
- shadow decision/reason codes.

### Acceptance

- không thay execution node;
- mọi quyết định có eligible/rejected reasons;
- prediction error được đo;
- không lộ secret/config path.

## Phase R2 — Remote read-only analysis

### Scope

- search;
- LSP/index;
- dependency graph;
- static analysis;
- log parsing;
- no remote mutation.

### Deliverables

- verified repository mirror;
- exact read snapshot;
- bounded evidence packet;
- node/cache timing;
- server-first canary cho read-only task classes.

### Acceptance

- same semantic result với local baseline;
- no source drift;
- context bytes/model turns giảm hoặc TTAR tốt hơn;
- fallback local deterministic.

## Phase R3 — Isolated remote worktree + focused proof

### Deliverables

- normalized patch bundle;
- run/wave-scoped remote worktree;
- exact post-apply digest;
- toolchain/platform manifest;
- ProofBundle;
- cleanup/retention/reconciliation;
- no authoritative remote write.

### Acceptance

- proof reuse chỉ exact identity;
- fault injection không reuse sai proof;
- outcome unknown không auto replay;
- remote failure không làm bẩn local;
- local apply vẫn dưới write lease.

## Phase R4 — Server-first deterministic auto-placement

### Scope ban đầu

- read-only analysis;
- focused tests/builds portable;
- no GUI/device/secret/signing;
- bounded task classes có paired evidence.

### Deliverables

- actual placement;
- queue/admission/circuit breaker;
- local interactive protection;
- fallback/replan;
- economics dashboard.

### Acceptance

- quality floor giữ;
- TTAR/CAR hoặc local burden cải thiện theo paired cohort;
- no hidden duplicate execution;
- rollback về local-first một flag/policy change.

## Phase R5 — Remote candidate lane

### Deliverables

- candidate patch trong isolated remote worktree;
- deterministic remote proof;
- compact patch/evidence về ChatWeb;
- local authoritative apply và selective final proof.

### Acceptance

- first-pass acceptance không giảm;
- repair/candidate-block rate trong gate;
- remote candidate không được quyền tự accept/write local;
- task classes và cost cap rõ.

## Phase R6 — Adaptive learning

### Prerequisite

- đủ representative pairs;
- model/node/proof costs observable;
- stable task taxonomy;
- placement reason/prediction quality tốt;
- safety classes cố định.

### Deliverables

- contextual bandit hoặc nearest-similar-task policy;
- confidence/uncertainty;
- shadow and constrained exploration;
- route/placement regret analysis.

### Acceptance

- outperform deterministic baseline trên held-out representative tasks;
- quality floor và high-risk constraints giữ;
- no opaque unexplainable promotion.

## Phase R7 — Optional scale extensions

Chỉ khi thực tế yêu cầu:

- CAS/REAPI interoperability;
- multiple server pools;
- DRF/multi-tenant fairness;
- GPU/local model lanes;
- distributed compilation at scale;
- richer fleet operations.

---

# 17. Failure modes và risk register

| Rủi ro | Hậu quả | Mitigation |
|---|---|---|
| Source snapshot drift | Proof sai source | Exact digest + post-apply verification |
| Environment drift | False portability/cache hit | Toolchain/platform/env manifest |
| Secret leakage | Security incident | Local affinity + secret scope + redaction |
| Duplicate side effect | Corrupt state | Idempotency + outcome states + no blind retry |
| Remote worker stale | Wrong result/lost job | Instance identity + reconciliation + cooldown |
| Server overload | TTAR tail tăng | Capacity-aware admission + circuit breaker |
| Queue prediction sai | Placement regret | Observed prediction error + conservative prior |
| Cache poisoning | Reuse incorrect output | Salt/schema/tool version + invalidation |
| Cross-run contamination | Flaky proof | Run/wave isolated worktree |
| Local UI vẫn lag | Mục tiêu thất bại | Interactive protection + local burden telemetry |
| Linux proof thay Windows proof | Compatibility defect | Platform-specific proof contract |
| ML router overfit | Cost/quality regression | Representative paired gate + shadow |
| Too much orchestration | TTAR tăng | Fast path + fewer decisions/handoffs |
| Feature accumulation | Maintenance cost | Keep/revise/remove after rerun |
| Raw telemetry explosion | Context/storage waste | Bounded summaries + source refs |
| Scheduler becomes second authority | Safety regression | EOCL remains sole lifecycle/write authority |

---

# 18. Điều không nên xây ở giai đoạn hiện tại

Không nên:

- xây Kubernetes-like scheduler;
- triển khai full Bazel REAPI trước khi có transfer/cache pressure thật;
- thêm public MCP tools cho từng node/model;
- cho server ghi trực tiếp authoritative checkout;
- bật autonomous multi-agent fan-out mặc định;
- dùng ML scheduler khi route pairs bằng 0;
- dùng utilization làm North Star;
- sync toàn bộ home directory/ignored state;
- coi remote test xanh là portable proof mặc định;
- mở remote secrets chỉ để tăng offload ratio;
- hedge HEAVY/side-effecting jobs;
- retry khi execution có thể đã bắt đầu;
- chạy local LLM chỉ vì server có GPU nếu deterministic tool đủ;
- copy nguyên khối M365-Copilot2API, repository-harness, Ray hoặc Bazel vào core.

---

# 19. Kịch bản vận hành mẫu

## 19.1 Localized Rust bug, strong oracle

```text
ChatWeb classifies bug
-> server-a warm LSP localizes symbols
-> Coding MCP prepares minimal patch
-> server-a isolated worktree runs focused test
-> proof identity matches
-> local authoritative checkout applies patch
-> exact same focused proof may reuse if identity remains exact
-> ChatWeb accepts
```

Local PC không chạy cold index/build, trừ khi source drift hoặc platform-specific gate yêu cầu.

## 19.2 Electron UI bug

```text
server-a: search, static analysis, candidate, unit tests
local Windows: launch packaged/dev UI, reproduce animation/freeze, inspect real process
ChatWeb: synthesize evidence and accept/reject
```

Không cố ép GUI proof lên Linux server.

## 19.3 Release build nặng

```text
server/windows-runner eligible?
  yes -> warm cache release build + artifact digest
  no  -> local under interactive protection / scheduled HEAVY slot
```

Nếu signing key local-only:

```text
server produces unsigned verified artifact
-> local signs under secret-owner policy
-> local final signature verification
```

## 19.4 Tiny diagnostic

```text
git status / small targeted read
expected local 200ms
remote setup 2s
=> local
```

Server-first không được biến thành remote-all.

## 19.5 Remote node failure giữa build

```text
Job status = outcome_unknown?
  yes -> do not blindly restart side-effecting action
  read-only/reproducible build action with exact identity?
    replan to another eligible node using same action identity
  otherwise -> BLOCKED/REPLAN with explicit reason
```

---

# 20. Quyết định đề xuất cho dự án

## 20.1 Nên triển khai

### P0

1. Accepted-result economics schema.
2. Node/capability/health registry.
3. Shadow placement engine.
4. Exact snapshot/environment/proof identity.
5. Local interactive protection metrics.

### P1

1. Remote read-only semantic/static workloads.
2. Remote isolated worktree.
3. Focused proof bundle.
4. Compiler/semantic cache measurement.
5. Execution Control Center placement view.

### P2

1. Server-first auto-placement cho task classes đã chứng minh.
2. Remote candidate patch lane.
3. Proof reuse promotion nếu hit/saved-time thật.
4. Queue/circuit-breaker tuning.

### Hold

- learned model/node router;
- multi-agent parallel implementation;
- full CAS/REAPI;
- GPU/local-model orchestration;
- rich fleet management;
- distributed write authority.

## 20.2 Phán quyết tính thực tế

| Trục | Đánh giá |
|---|---|
| Kiến trúc nền | **Sẵn sàng để mở rộng** |
| Remote deterministic analysis | **Khả thi cao** |
| Remote build/test | **Khả thi cao nếu identity/platform đúng** |
| Remote candidate implementation | **Khả thi theo isolated worktree** |
| Remote authoritative mutation | **Không nên** |
| Automatic server-first v1 | **Khả thi sau shadow/paired gate** |
| Adaptive ML placement | **Chưa đủ dữ liệu** |
| Full distributed compute fabric | **Chưa cần** |
| ROI tiềm năng | **Cao**, chủ yếu từ giảm repair, wait, localization và local HEAVY load |

## 20.3 Thesis cuối

Thành công của hướng này không nằm ở việc “server chạy được Cargo”. Điều đó tương đối dễ. Phần khó và tạo khác biệt là:

```text
đúng task
-> đúng semantic owner
-> đúng source snapshot
-> đúng compute node
-> đúng cache/environment
-> đúng proof
-> đúng acceptance owner
-> ít repair nhất
```

Do baseline hiện tại cho thấy repaired run có median TTAR gấp 5,29 lần first-pass, ưu tiên cao nhất phải là **tăng xác suất accepted first-pass và giảm orchestration/identity errors**. Offload CPU chỉ là một trong các phương tiện.

Kiến trúc nên được phát triển thành:

> **AI Coding Compute Orchestrator có một semantic brain, một authoritative execution/control plane, nhiều compute nodes có capability rõ, exact evidence identity và một optimization loop học từ accepted results.**

---

# 21. Các quyết định owner cần xác lập trước implementation sâu

Những câu hỏi này không chặn tài liệu nghiên cứu nhưng cần được trả lời trước R2–R4:

1. Máy chủ hiện có OS, CPU, RAM, disk, GPU và network nào?
2. Có thể cài Runner/Toolchain lâu dài hay chỉ chạy container/VM?
3. Có Windows server/VM runner để thay local Windows build không?
4. Repository nào được phép replicate lên server?
5. Loại secret nào bắt buộc local?
6. Có workload/data nào không được rời máy cá nhân?
7. Server compute là sunk cost hay cần tính electricity/cloud cost?
8. Retention của remote worktree/artifact/proof là bao lâu?
9. Có bao nhiêu project/user cạnh tranh cùng server?
10. Mức quality floor và acceptable local-interactive degradation là gì?

Mọi answer phải trở thành policy/config authority, không để scheduler tự suy đoán.

---

# 22. Nguồn nội bộ

- `README.md`
- `AGENTS.md`
- `docs/ARCHITECTURE.md`
- `docs/ROADMAP.md`
- `docs/MODEL_EXECUTION.md`
- `docs/AGENT_PROJECTS.md`
- `docs/AGENT_TRANSPORTS.md`
- `docs/research/EXECUTOR_ROUTING_BENCHMARK_2026-08-12.md`
- `docs/research/MODEL_ORCHESTRATION_RESEARCH_PHASE2_2026-08-12.md`
- `docs/research/260815_TOOLS_CODEX_WEB_ACTIVITY_COORDINATION_PERFORMANCE_COST.md`
- `docs/research/260815_TOOLS_CODEX_WEB_CURRENT_PRACTICAL_ASSESSMENT_AND_REMEDIATION_PLAN.md`
- `docs/research/260816_P2-P3-orchestration-resource-analysis.md`
- `.coding-tools/orchestration/ledger.sqlite3`
- `.coding-tools/performance.json`
- `.coding-tools/task-history.json`
- `.coding-tools/task-state.json`
- `resources/coding-tools-mcp/scripts/report_rework_baseline.py`
- `resources/coding-tools-mcp/scripts/compare_route_policies.py`

---

# 23. Nguồn nghiên cứu và dự án tham khảo

## Remote execution, cache và distributed systems

1. Bazel Remote Execution APIs — distributed execution, Action Cache và Content Addressable Storage.  
   https://github.com/bazelbuild/remote-apis

2. Remote Execution v2 protocol — Action/Command/input root/platform/timeout identity.  
   https://github.com/bazelbuild/remote-apis/blob/main/build/bazel/remote/execution/v2/remote_execution.proto

3. Mozilla sccache — shared compiler cache và distributed compilation.  
   https://github.com/mozilla/sccache

4. Topcuoglu, Hariri & Wu, “Performance-effective and low-complexity task scheduling for heterogeneous computing”, IEEE TPDS, 2002 — HEFT/CPOP.  
   https://doi.org/10.1109/71.993206

5. Ghodsi et al., “Dominant Resource Fairness: Fair Allocation of Multiple Resource Types”, NSDI/UC Berkeley, 2011.  
   https://www2.eecs.berkeley.edu/Pubs/TechRpts/2011/EECS-2011-18.html

6. Moritz et al., “Ray: A Distributed Framework for Emerging AI Applications”, OSDI 2018.  
   https://arxiv.org/abs/1712.05889

## LLM routing và cost-quality optimization

7. Chen, Zaharia & Zou, “FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance”, 2023.  
   https://arxiv.org/abs/2305.05176

8. Ong et al., “RouteLLM: Learning to Route LLMs with Preference Data”, 2024.  
   https://arxiv.org/abs/2406.18665

9. RouteLLM implementation and calibration framework.  
   https://github.com/lm-sys/RouteLLM

10. Yang et al., “SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering”, NeurIPS 2024.  
    https://arxiv.org/abs/2405.15793

11. SWE-agent Agent-Computer Interface documentation.  
    https://swe-agent.com/0.7/background/aci/

## Các dự án đã trao đổi

12. M365-Copilot2API — gateway/control-plane patterns, health, keys, concurrency và usage.  
    https://github.com/HEXUXIU/M365-Copilot2API

13. repository-harness — repository authority, invariant proof và evidence-backed harness improvement.  
    https://github.com/hoangnb24/repository-harness

14. Tools-Codex-web — project under evaluation.  
    https://github.com/uyenthudao2410-code/Tools-Codex-web

---

# 24. Ghi chú về độ tin cậy

- Các số liệu nội bộ là snapshot của workspace/runtime ngày 2026-08-16, không phải benchmark độc lập trên một server fleet đã triển khai.
- Báo cáo chưa đo transfer bandwidth, server queue, cache warmth hoặc remote build trên phần cứng máy chủ thực của người dùng.
- Các con số tiết kiệm trong paper bên ngoài là kết quả trong setup của tác giả; không được dùng làm forecast trực tiếp cho Coding Web.
- Tính khả thi kỹ thuật được đánh giá cao, nhưng mức ROI phải được chứng minh bằng paired accepted-result evaluation trong chính dự án.
- Current worktree có các thay đổi ngoài phạm vi tài liệu này; báo cáo không sửa hoặc đánh giá lại các source changes đó.
