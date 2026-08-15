# Tools-Codex-web — Practical Fit Audit of Advisory Recommendations

**Ngày đánh giá gốc:** 2026-08-15  
**Ngày cập nhật phương án:** 2026-08-15  
**Repository:** `uyenthudao2410-code/Tools-Codex-web`  
**Workspace quan sát:** `E:\Github\Tools-Codex-web`  
**Audit baseline HEAD:** `main` / `e45bed968bee6db46bb3041de179cbcf23e3906b`  
**Current update HEAD:** `main` / `8581b8331e83cc600c2b813629875639e48a8245`  
**Desktop version:** `web-mcp-assistant 0.3.4`  
**Smart contract:** `smart-v3`, **8 public tools**, SHA-256 `4283e098c315d015c457ce2ab781257491ef70607c6c577f7699969fb8c3f754`  
**Loại tài liệu:** independent practical-fit audit / advisory validation / evidence-driven solution blueprint  
**Phạm vi:** hai tài liệu tư vấn do người dùng cung cấp, source/runtime hiện tại, `.coding-tools` production evidence, CI/release truth, WebCodex upstream ideas và phương án triển khai theo evidence.

> **Revision note.** Bản cập nhật này giữ nguyên các snapshot đã dùng làm evidence trong audit gốc thay vì ghi đè chúng bằng telemetry live luôn biến động. Mọi số liệu ở **Audit baseline** phải được hiểu là evidence tại thời điểm audit; mọi số liệu ở **Current-state delta** là observation mới trước wave ghi tài liệu. Các quyết định triển khai dùng trạng thái source/runtime mới nhất quan sát được, không dùng một snapshot cũ như “current truth”.

---

# 0. Kết luận điều hành

## 0.1 Phán quyết tổng thể

Hai bản tư vấn **đúng hướng ở tầng chiến lược**, đặc biệt ở bốn luận điểm:

1. Tools-Codex-web đã qua giai đoạn thiếu capability cơ bản; bottleneck tiếp theo là **evidence quality, causal measurement và simplification**.
2. `smart-v3` 8-tool surface, deterministic-first và one-runtime authority là những lựa chọn nên bảo vệ.
3. Routing/caching/parallelism không nên được promote bằng simulation hoặc vài sample nhỏ; phải tối ưu **accepted result**, không tối ưu model-call price riêng lẻ.
4. Upstream WebCodex nên được **port chọn lọc theo bottleneck thật**, không merge/cherry-pick toàn bộ.

Một phần mô tả trạng thái trong hai bản tư vấn đã trễ so với source hiện tại. Dự án đã có PerformanceTrace v5, accepted-run cohort/economics, routing promotion-readiness, canonical provider usage events, proof-cache opportunity counters, idempotency required/optional policy, phase timing, orchestration ledger, capability metadata và native semantic bridge primitives.

Vì vậy, hướng đúng hiện nay không còn là:

```text
build telemetry / build idempotency / build routing science
```

mà là:

```text
make source/runtime identity trustworthy
→ activate existing primitives consistently
→ measure opportunities and causal outcomes
→ close remaining reliability/coverage gaps
→ simplify or defer components that do not earn their cost
```

### Điểm phù hợp thực tiễn

| Tài liệu | Mức phù hợp tổng thể | Nhận định |
|---|---:|---|
| Tư vấn A — evidence/scientific optimization | **8.8/10** | Thesis và methodology rất phù hợp; nhiều số liệu snapshot đã stale và một số capability đã được triển khai sau thời điểm viết. |
| Tư vấn B — chọn lọc WebCodex | **7.8/10** | Selective-port principle đúng; source-fenced continuation rất phù hợp, nhưng Call Hierarchy/E2E reuse không nên đứng trước prerequisite của desktop hot path. |
| Hướng kết hợp sau audit + current update | **9.4/10** | Giữ core, làm release/evidence truth trước, xử lý large-result continuation + idempotency fault-proofing, activate semantic bridge rồi mới chạy Call Hierarchy/router experiments. |

## 0.2 Những quyết định nên lấy ngay

### KEEP — không thay đổi

- `smart-v3` đúng 8 public tools;
- Electron giữ one-runtime authority;
- Coding Tools MCP Python là desktop execution hot path;
- deterministic-first;
- Mini/Luna là bounded candidate lanes;
- Sol giữ high-width semantic/integration/final-acceptance role;
- EOCL/write lease vẫn là authority boundary;
- routing-v2 promotion tiếp tục **không automatic activation**;
- Terra tiếp tục explicit/shadow cho đến khi có causal evidence.

### FIX / PROVE NOW

1. Có **authoritative exact-HEAD CI/release proof**; không kế thừa trạng thái CI từ một SHA cũ.
2. Không package raw runtime/research snapshots vào installer.
3. Hoàn thiện telemetry truth: true wall timestamps + source/runtime identity + explicit activation state.
4. Reconcile/đóng operational stale state còn sót; current observation còn **1 stale orchestration run**.
5. Freeze speculative feature expansion trong khi các gate evidence/reliability chưa đóng.

### IMPLEMENT NEXT

6. Source-fenced continuation trong Python/internal `agent_workflow` evidence path, không thêm public tool thứ 9.
7. Required-idempotency fault-proofing theo **current policy epoch**, không lấy historical cumulative ratio làm go/no-go.
8. Result-tail metrics và proof-cache opportunity study.
9. Exact-source Windows release provenance.

### ACTIVATE / EXPERIMENT ONLY AFTER PREREQUISITE

10. Bind native semantic provider an toàn vào live Python MCP; prove end-to-end read-only/workspace/auth boundary.
11. Đo semantic workload thực rồi mới thử bounded Call Hierarchy.
12. Chạy paired real-task routing experiments; giữ `automatic_activation=false` cho tới khi promotion-readiness thực sự thỏa.

## 0.3 Solution in one page

```text
WAVE 0  BASELINE + OPERATIONAL HYGIENE
  current HEAD/source/runtime identity
  reconcile stale orchestration state
  freeze speculative feature growth
           │
           ▼
WAVE 1  RELEASE / EVIDENCE TRUTH
  exact-HEAD CI proof
  installer sanitation
  true telemetry timestamps
  runtime/source identity
           │
           ▼
WAVE 2  RELIABILITY + LARGE-RESULT HOT PATH
  current-policy idempotency closure + fault injection
  source-fenced continuation
  result-tail metrics
  proof-cache opportunity truth
           │
           ├──────────────► exact-source Windows release provenance
           │
           ▼
WAVE 3  SEMANTIC ACTIVATION
  configure native read-only semantic binding
  smoke authorization/workspace/fallback
  collect live semantic localization evidence
           │
           ▼
WAVE 4  BOUNDED EXPERIMENTS
  Call Hierarchy experiment
  paired route experiments
  Terra remains shadow/explicit
           │
           ▼
WAVE 5  SIMPLIFY / KEEP / REMOVE
  keep only accelerators that improve accepted-work value
  defer demand-driven features without evidence
```

**North-star:**

```text
MINIMIZE TIME AND COST TO A CORRECT ACCEPTED RESULT
UNDER CORRECTNESS, SECURITY, AUTHORITY AND PROOF-TRUTH CONSTRAINTS.
```

---

# 1. Nguồn và phương pháp đánh giá

## 1.1 Hai tài liệu tư vấn đầu vào

### Advisory A

File người dùng cung cấp:

```text
Đã dán markdown (1)(20260814-182713).md
```

Luận điểm trung tâm: dự án đã chuyển bottleneck từ engineering capability sang scientific evidence, simplification và causal measurement. Tài liệu đề xuất evidence ladder, paired real-task experiment, TTA/first-pass acceptance, CI split, benchmark sanitation, idempotency, large-result continuation, semantic localization và empirical router calibration.

### Advisory B

File người dùng cung cấp:

```text
Đã dán markdown (2).md
```

Tài liệu đối chiếu WebCodex và ưu tiên các ý tưởng:

```text
source-fenced git diff continuation
LSP Call Hierarchy
E2E prebuilt binary reuse
focused Go validation
structured delete
exact-source release provenance
```

với nguyên tắc không biến `smart-v3` thành một tool surface 10–12 public tools.

## 1.2 Runtime evidence bắt buộc

Audit coi các artefact sau là evidence production quan trọng:

```text
.coding-tools/orchestration/ledger.sqlite3
.coding-tools/performance.json
.coding-tools/task-history.json
.coding-tools/task-state.json
```

| Nguồn | Vai trò |
|---|---|
| `orchestration/ledger.sqlite3` | Canonical causal/audit source cho run/wave/delegation/proof/EOCL/idempotency/handoff. |
| `performance.json` | Materialized performance/usage view; có historical + active runtime counters. |
| `task-history.json` | Task outcome/history projection. |
| `task-state.json` | Current-state projection; không phải forensic authority. |

Các file này là **volatile runtime evidence**, không phải source code và không được dùng làm source-worktree fingerprint.

## 1.3 Evidence hierarchy

```text
E6  production randomized / holdout
E5  live dogfood observational evidence
E4  paired real-task replay
E3  controlled local integration
E2  synthetic benchmark / scenario simulation
E1  unit/property/static proof
E0  design hypothesis
```

Claim labels:

- **CONFIRMED** — source + runtime/evidence trực tiếp hỗ trợ;
- **MOSTLY CONFIRMED** — hướng đúng, có caveat;
- **PARTIAL** — chỉ đúng một lớp hoặc dependency chưa thỏa;
- **STALE** — từng đúng nhưng state/số liệu đã đổi;
- **CONDITIONAL** — chỉ đáng làm nếu prerequisite/workload tồn tại;
- **REJECT** — không phù hợp hot path/mục tiêu hiện tại.

## 1.4 Quy tắc chống “evidence drift”

Tài liệu này phân biệt bốn trạng thái:

```text
IMPLEMENTED  source có capability
TESTED       có proof focused/full cho source boundary
ACTIVE       live runtime đang sử dụng capability
PROVEN       có representative accepted-work evidence
```

Không được suy:

```text
IMPLEMENTED => ACTIVE
ACTIVE      => PROVEN
UNIT PASS   => CI GREEN
OBSERVED    => CAUSAL
```

Đây là nguyên tắc quan trọng nhất của bản solution blueprint.

---

# 2. Kiến trúc production thực tế của app

## 2.1 Desktop hot path

Electron không dùng Rust WebCodex Server làm execution kernel chính cho desktop app. Production path thực tế:

```text
ChatGPT / ChatWeb
       │
       ▼
Tunnel / local transport
       │
       ▼
Electron supervisor
       │
       ▼
ONE Coding Tools MCP Python Runtime
       │
       ├── deterministic tools / writer / proof
       ├── agent_workflow internal evidence/orchestration
       ├── orchestration ledger / task state
       └── Codex App Server sidecar, bounded/read-only candidate/review
```

`smart-v3` public tools:

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

## 2.2 Rust có vai trò gì?

Rust vẫn chứa:

```text
Server
Runner
ToolRuntime
Tool metadata/capability authorization
Workflow Session
LSP
Jobs
Connector runtime
release/npm substrate
```

Do đó không nên gọi Rust là dead code. Correct classification phải là per-subsystem:

```text
PRODUCTION
SUPPORTING
RELEASE-GATE
COMPATIBILITY
REFERENCE
DEPRECATED
```

Mục tiêu không phải xóa Rust để “đơn giản hóa” bằng cảm tính, mà là tránh duplicate authority/maintenance không tạo accepted-work value.

## 2.3 Authority boundary không thay đổi

Future acceleration phải nằm dưới current authority:

```text
semantic lookup
continuation
cache
routing candidate
call hierarchy
```

không được tạo mutation authority thứ hai.

```text
MCP/EOCL/write lease
      │
      ├── owns project mutation authority
      └── owns final deterministic proof/acceptance transition
```

---

# 3. Current-state delta so với audit baseline

## 3.1 Source identity đã đổi

Audit baseline dùng:

```text
e45bed968bee6db46bb3041de179cbcf23e3906b
```

Current update quan sát:

```text
8581b8331e83cc600c2b813629875639e48a8245
feat: harden routing promotion and native LSP bridge
```

Do đó mọi câu “current HEAD” trong audit baseline phải được hiểu theo SHA cũ, trừ khi section này hoặc các section solution phía sau nói rõ current update HEAD.

## 3.2 Live PerformanceTrace observation trước document-write wave

Telemetry là volatile và chính audit cũng tạo thêm tool calls. Observation dùng để xác định direction, **không thay thế Appendix A baseline**:

```text
PerformanceTrace version          5
tool calls                    2,583
error-result events              213
cache hits                        10
deduplicated calls                 0
request bytes               3,831,145
response bytes             80,548,263
model-visible bytes          6,209,070
local execution ms           5,551,859
estimated inter-tool gap    47,772,867
```

Derived, chỉ để định hướng:

```text
error-result rate                ≈ 8.25%
response/request ratio           ≈ 21.0x
model-visible/response ratio     ≈ 7.71%
gap/local execution ratio        ≈ 8.60x
```

`estimated_wait_ms` vẫn chỉ là **inter-tool gap proxy**, tuyệt đối không gọi là model latency.

## 3.3 Route vẫn conservative

Current observed route aggregates:

```text
deterministic  829
mini            11
luna            10
sol_xhigh       36
terra            8
```

Current execution-mode aggregates:

```text
mcp_only           1,120
deep_single_lane      89
bounded_candidate      23
auto                   35
```

Kết luận không đổi: broad aggressive routing chưa được evidence hỗ trợ.

## 3.4 Current historical idempotency aggregate

Observed persisted aggregate:

```text
required calls        76
required keyed        57
historical coverage 75.0%

optional calls       241
optional keyed        10
auto-generated keys   54
```

Nhưng source hiện đã có:

```text
IDEMPOTENCY_POLICY_EPOCH = task_epoch_v1
idempotency_current_policy_required_calls
idempotency_current_policy_required_key_calls
idempotency_current_policy_by_operation
```

và runtime-activation gate được thiết kế để dùng:

```text
coverage_source = required_current_policy
coverage_target = 0.95
```

khi current policy epoch được materialize.

**Điểm sửa quan trọng:** `57/76 = 75%` là historical cumulative required view, **không được dùng làm promotion/release gate mới**. Gate đúng cần evidence post-policy-epoch. Current persisted observation chưa đủ để tuyên bố current-policy gate đã pass.

## 3.5 Proof cache vẫn chưa chứng minh ROI

Current aggregate:

```text
proof_cache_eligible       51
proof_cache_hits            1
proof_cache_misses         51
proof_cache_saved_ms      999
miss reasons:
  cold                     34
  input_fingerprint_changed 17
```

Điều chắc chắn có thể nói:

> Chỉ một observed hit và 999 ms saved; không có cơ sở để quảng bá proof cache như performance winner.

Correct task là opportunity study, không làm fingerprint lỏng hơn để tăng hit-rate.

## 3.6 Semantic localization: source-ready hơn, live vẫn chưa active

Current source đã có native semantic bridge primitives và Python semantic provider abstraction. Boundary source hiện đã bao gồm các nguyên tắc:

```text
loopback-only native endpoint
project credential
project/workspace binding
read-only semantic actions
bounded request/response
no proxy / no redirect
fail closed on invalid binding
```

Nhưng live runtime observation vẫn báo:

```text
provider.available = false
reason = NATIVE_LSP_BINDING_NOT_CONFIGURED
```

Current aggregate:

```text
localization_samples      19
localization_queries     149
lsp_available_samples      0
lsp_attempted_queries      0
lsp_handled_queries        0
fallback_search_queries  149
```

Do đó trạng thái chính xác là:

```text
SOURCE-READY / TESTABLE BOUNDARY
≠
LIVE-ACTIVE SEMANTIC LOCALIZATION
```

## 3.7 Routing-v2 promotion safety đã mạnh hơn

Current source giữ các invariant:

```text
shadow_only recommendation
mutation_allowed = false
automatic_dispatch = false
automatic_activation = false
synthetic/benchmark evidence excluded from production promotion
representative accepted cohorts required
quality/economics evidence required
```

Điều này giảm rủi ro auto-promote từ sample đẹp nhưng nhỏ. Causal experiment vẫn cần; chỉ là safety posture hiện tốt hơn audit baseline.

## 3.8 Operational state

Current assessment quan sát:

```text
orphaned background operations: none observed
orphaned idempotency record:    none observed
waiting lane after restart:     none observed
stale orchestration runs:       1
```

Một stale run không làm app “hỏng”, nhưng cần reconcile/close hoặc có explicit explanation trước khi gọi operational state hoàn toàn green.

---

# 4. Đánh giá tổng thể Advisory A

## 4.1 Luận điểm trung tâm

> Dự án đã chuyển từ thiếu capability sang bottleneck về scientific evidence, simplification và causal measurement.

**Verdict: CONFIRMED. Fit: 8.8/10 overall.**

Current source thậm chí củng cố luận điểm này: nhiều primitive đã tồn tại, nhưng activation/evidence vẫn không đồng đều.

## 4.2 Những phần Advisory A đã trở nên stale

Không còn chính xác nếu nói:

```text
telemetry chưa có
idempotency chưa có
routing science chưa có
handoff dormant hoàn toàn
accepted TTA chưa materialize
```

Correct current interpretation:

```text
telemetry: implemented + active, nhưng identity/timestamp/epoch activation còn phải prove
idempotency: policy + auto-key có; current-policy coverage/fault proof chưa đủ
routing: instrumentation/promotion safety mạnh; causal evidence còn mỏng
handoff: đã có live records trong audit baseline; ROI vẫn chưa đủ sample
TTA: durable accepted-run measurement đã tồn tại
```

## 4.3 Những phần vẫn cực kỳ đúng

- evidence classes phải tách;
- simulation không phải production savings;
- TTA/accepted result phải là north-star;
- large-result tail phải đo trên workload thật;
- `estimated_wait_ms` không causal;
- CI/release proof phải exact-source;
- feature complexity phải justify bằng accepted-work value;
- paired experiments cần cùng task/base/environment;
- proof truth không được hy sinh để chase cache hit.

---

# 5. Đánh giá tổng thể Advisory B

## 5.1 Selective upstream adoption

**Verdict: CONFIRMED.** Không merge upstream toàn bộ.

Giá trị của upstream là idea inventory / tested concept, không phải mandatory architecture.

## 5.2 Source-fenced continuation

**Fit: 9.6/10.** Đây vẫn là một trong các idea upstream đáng triển khai nhất vì audit có large-result evidence thật.

Correct target:

```text
Python Coding Tools MCP
  → internal agent_workflow evidence layer
  → bounded page/cursor
  → source/worktree fence
  → stale continuation fails closed
```

Không thêm tool thứ 9.

## 5.3 Call Hierarchy

Concept fit cao, immediate priority thấp hơn continuation.

Correct sequence đã thay đổi thêm sau current HEAD:

```text
source trust boundary primitives     substantially implemented
      ↓
configure/bind live semantic provider
      ↓
prove auth/workspace/read-only/fallback end-to-end
      ↓
collect real semantic-eligible workload
      ↓
Call Hierarchy experiment
```

Không cần “xây lại trust boundary” từ đầu; cần **activate và prove** boundary hiện có.

## 5.4 E2E prebuilt binary reuse

Có giá trị nếu Rust vẫn là RELEASE-GATE/SUPPORTING subsystem. Không phải desktop runtime P0.

## 5.5 Focused Go / structured delete / disconnect

Demand-driven. Không được đưa lên trước các bottleneck có telemetry thật.

---

# 6. `smart-v3` 8 tools — hard design invariant

Current contract:

```text
profile    = smart-v3
tool_count = 8
sha256     = 4283e098c315d015c457ce2ab781257491ef70607c6c577f7699969fb8c3f754
```

**Decision: KEEP CORE. Fit of advisory recommendation: 10/10.**

Lý do:

1. `agent_workflow` đã là aggregation boundary.
2. Continuation/LSP/proof lookup/call hierarchy có thể internalize.
3. Public tool fingerprint là deployment/schema compatibility surface.
4. Không có evidence cho tool thứ 9.
5. More tools tăng schema/context/selection burden mà chưa có accepted-work ROI.

---

# 7. Audit baseline telemetry — giữ như evidence, không gọi là live-current

Audit baseline đọc `.coding-tools/performance.json` tại snapshot có:

```text
PerformanceTrace version      5
tool calls                    2,471
errors                          201
cache hits                       10
deduplicated calls                0
request bytes              3,654,191
response bytes            71,065,969
model-visible bytes         5,983,100
local execution ms          5,348,626
estimated inter-tool gap   45,351,236
```

Derived:

```text
error-result rate               ≈ 8.13%
response/request bytes ratio    ≈ 19.45x
gap/local execution ratio       ≈ 8.48x
model-visible/response bytes    ≈ 8.42%
```

Baseline route counts:

```text
deterministic  785
mini            11
luna            10
sol_xhigh       36
terra            8
```

Baseline required metrics:

```text
required calls          60
required keyed          46
required coverage     ≈ 76.7%
```

Sau current-policy epoch work, ratio này là **historical evidence only**, không phải release gate.

---

# 8. Large-result tail — bottleneck có evidence mạnh nhất

Audit baseline có 172 run metrics. `response_bytes/run`:

```text
p50      150,425 B
p90      737,458 B
p95    1,150,922 B
p99    1,750,683 B
max    3,557,410 B
```

Đây là evidence trực tiếp rằng result/evidence transport tail đáng tối ưu.

Hai dimensions phải tách:

```text
transport/result volume
model-visible context volume
```

Không được suy:

```text
large response_bytes == same amount of model tokens
```

## 8.1 KPI cần chuẩn hóa

```text
response_bytes/run p50/p90/p95/p99
model_visible_bytes/run p50/p90/p95/p99
max result
truncation rate
continuation rate
artifact spill rate
re-read calls after truncation
duplicate evidence bytes
stale continuation rate
```

## 8.2 Why continuation outranks Call Hierarchy

Continuation giải quyết bottleneck **đã quan sát**. Call Hierarchy giải quyết bottleneck **có khả năng tồn tại nhưng semantic provider live còn chưa active**.

Đây là lý do sequencing phải là evidence-first.

---

# 9. Source-fenced continuation — implementation contract

## 9.1 Mục tiêu

Cho phép đọc tiếp large diff/evidence mà không:

- trộn hai source/worktree states;
- duplicate hunks;
- buộc model đọc một payload khổng lồ;
- thêm public MCP tool;
- làm authority plane phức tạp hơn.

## 9.2 Internal contract đề xuất

Một continuation token tối thiểu cần bind:

```text
schema_version
operation_kind
workspace/source fingerprint
scope fingerprint
query/options fingerprint
page position
bounded page size/version
```

Không cần biến token thành framework general-purpose ở wave đầu. Chỉ triển khai cho use case lớn đã có evidence: diff/evidence pagination trong `agent_workflow`.

## 9.3 Hard invariants

```text
NO MIXED SOURCE BETWEEN PAGES
STALE CONTINUATION FAILS CLOSED
NO DUPLICATE HUNKS ACROSS PAGES
NO SKIPPED HUNK DUE TO PAGINATION
BOUNDED MODEL-VISIBLE PAGE SIZE
PUBLIC SMART-V3 TOOL COUNT REMAINS 8
ACCEPTANCE/CORRECTNESS DOES NOT REGRESS
```

## 9.4 Suggested result shape

Internal result có thể gồm:

```text
items / preview
truncated
continuation
source_fingerprint
scope_fingerprint
```

Không expose implementation details không cần thiết cho model nếu presenter/internal workflow có thể consume chúng.

## 9.5 Experiment

```text
A = current bounded/truncated path
B = source-fenced continuation
```

Corpus: real large-diff / large-evidence tasks có tail thật.

Measure:

```text
accepted rate
TTA
model-visible bytes
tool calls
re-read calls
transport p90/p95/p99
stale-source incidents
repair/replan rate
```

**Keep rule:** correctness/accepted rate non-regression và có meaningful reduction ở TTA, re-read hoặc model-visible/transport tail trên representative corpus.

**Kill rule:** thêm complexity nhưng không giảm accepted-work cost/time hoặc gây stale/mixed-source risk.

---

# 10. Idempotency — từ “build” sang “policy activation + fault proof”

## 10.1 Semantics hiện có

Policy phân biệt:

```text
none
optional
required
```

Required dùng cho operations cần replay protection mạnh. Optional giữ khả năng intentional repeat.

## 10.2 Current policy epoch

Source hiện định nghĩa:

```text
task_epoch_v1
```

Production-relevant gate phải dùng current-policy counters nếu epoch active:

```text
idempotency_current_policy_required_calls
idempotency_current_policy_required_key_calls
idempotency_current_policy_by_operation
```

Historical counters vẫn giữ cho audit, nhưng không backfill vào new policy gate.

## 10.3 Hai acceptance conditions khác nhau

### Policy completeness

```text
100% operations được policy phân loại đúng
100% operations classified required có deterministic/explicit key strategy
```

Đây là code/design invariant.

### Observed activation coverage

Current runtime activation logic target:

```text
>= 95% current-policy required calls keyed
```

Đây là measurement gate, phải có representative samples và explicit `n`.

Không được thay một gate cho gate kia.

## 10.4 Fault injection matrix

Bắt buộc test ít nhất các fault boundaries:

```text
F0 before operation start
F1 after admission / before side effect
F2 after side effect starts
F3 after side effect completes / before response materialization
F4 after response materialization / before client delivery
F5 reconnect with outcome unknown
F6 runtime restart with durable record
F7 repeated accept/reject across controller fencing epoch
```

Expected invariant:

```text
required side effect <= once
same task epoch + same semantic operation => stable replay identity
new task/authority epoch => new identity when semantics require
unknown outcome never masquerades as safe pre-start
optional intentional repeats remain possible
```

## 10.5 Release gate

Không release/promote dựa trên historical `57/76` hoặc `46/60`.

Require:

```text
current policy epoch visible in runtime evidence
representative required-call sample exists
coverage target passes
zero known at-most-once violation in fault suite
zero authority-fencing key collision
```

---

# 11. Proof cache — opportunity study, không chase hit-rate

Current evidence chỉ chứng minh một hit và 999 ms saved.

Correct questions:

```text
How many proof stages are truly eligible?
Why are misses cold vs changed fingerprint vs stage-version change?
How much wall/TTA does a hit actually save?
Does reuse preserve exact proof truth?
```

Decision options sau representative window:

```text
KEEP as meaningful accelerator
KEEP as low-frequency correctness reuse primitive
DEMOTE performance expectations
```

Không có option:

```text
weaken fingerprint to inflate hit rate
```

---

# 12. Semantic localization — source boundary gần hoàn thiện, activation chưa hoàn thiện

## 12.1 Source state

Current source đã có substantial trust-boundary primitives:

```text
native internal semantic route
project credential
loopback-only URL requirement
workspace/project binding
read-only semantic action allowlist
bounded payload
no proxy / no redirect
fail-closed validation
```

Python side supports semantic-first/text-fallback orchestration.

## 12.2 Live state

Live runtime:

```text
NATIVE_LSP_BINDING_NOT_CONFIGURED
semantic_available = false
semantic_attempted = 0
semantic_handled = 0
fallback remains active
```

Do đó P2.1 phải đổi từ:

```text
build semantic trust boundary
```

thành:

```text
bind existing boundary
→ prove boundary end-to-end
→ activate safely
→ measure
```

## 12.3 Activation acceptance

Require all of:

```text
A1 provider reports available in fresh live runtime
A2 only authenticated/project-bound requests succeed
A3 workspace mismatch/path escape fails closed
A4 actions remain read-only
A5 response remains bounded
A6 provider unavailable => deterministic text fallback, not task failure
A7 semantic attempts and handled queries become nonzero on eligible tasks
A8 no new public tool
A9 no second mutation authority
```

## 12.4 Do not enable Call Hierarchy yet

Call Hierarchy starts only after semantic definition/reference/symbol path has representative live use.

---

# 13. LSP Call Hierarchy — bounded experiment after activation

## 13.1 Use case

Call Hierarchy may help:

```text
cross-file impact analysis
caller/callee ownership uncertain
API refactor blast radius
control-flow relationship localization
```

Không dùng mặc định cho every task.

## 13.2 Experiment design

```text
Control:
  current semantic definition/reference + text fallback

Candidate:
  same path + bounded Call Hierarchy on qualified cases
```

Measure:

```text
localization recall
files read
prepare calls
model-visible bytes
TTA to first correct edit
accepted rate
repair/replan rate
```

Hard boundaries:

```text
bounded depth/results
read-only
workspace-scoped
internal to agent_workflow
no public tool count change
```

**Concept fit:** 8.5/10.  
**Immediate priority before semantic activation:** low/conditional.

---

# 14. Routing science — implementation mạnh hơn evidence

## 14.1 Current source strengths

Current source includes:

```text
route requested/resolved
model/profile/economics metadata
accepted-result cohorts
promotion-readiness
provenance filters
shadow recommendation
representative cohort conditions
quality/economics gates
automatic_activation = false
```

## 14.2 Current weakness

Causal evidence vẫn thiếu broad paired trajectories:

```text
same task
same base SHA
same environment
actual A route trajectory
actual B route trajectory
same acceptance criteria
```

Observational cohorts chịu selection bias.

## 14.3 Policy giữ nguyên

```text
Deterministic default
Mini bounded localized candidate
Luna bounded harder candidate
Sol xhigh deep/integration lane
Terra explicit/shadow
Sol max/ultra explicit high-cost only
```

## 14.4 Promotion acceptance

Không promote vì:

```text
aggregate TTA looks good
a few model-route wins
synthetic benchmark
simulation
route frequency alone
```

Promotion chỉ được xem xét khi runtime `promotion_readiness` có representative accepted evidence, provenance hợp lệ, quality non-regression và economics outcome đủ tốt.

`automatic_activation=false` phải giữ cho tới khi policy riêng được phê duyệt bằng causal evidence; current roadmap không yêu cầu bật auto activation.

---

# 15. TTA là north-star

Accepted-run Time To Accepted là metric đúng vì nó bao gồm:

```text
localization
candidate/model work
mutation
proof
repair/replan
acceptance
```

Audit baseline ledger:

```text
accepted runs n = 109
p50 TTA = 79.791 s
p90 TTA = 326.287 s
```

Hard constraints đứng trước TTA:

```text
correctness
security/authority
truthful proof
no data loss
no known critical defect
```

Primary outcomes:

```text
first-pass accepted rate
TTA p50/p90/p95
```

Secondary:

```text
provider cost / accepted
model-visible bytes / accepted
tool calls / accepted
replans / accepted
proof tail
queue/dispatch tail
```

---

# 16. `estimated_wait_ms` — giữ đúng semantics

`estimated_wait_ms` là gap giữa previous tool completion và next tool start.

Nó có thể chứa:

```text
model reasoning
host/client scheduling
UI/user delay
MCP transport
serialization
network
other hidden work
```

Do đó:

```text
estimated_wait_ms != model latency
```

Con số gap/local lớn chỉ chứng minh critical path không nằm hoàn toàn trong local execution.

Schema dài hạn nên ưu tiên tên/semantics rõ hơn:

```text
inter_tool_gap_ms
```

và measured phases khi thật sự có clock boundary:

```text
queue_ms
dispatch_transport_ms
provider_ms
model_wall_ms
proof_ms
accept_wait_ms
replan_ms
```

Không đo được thì để unknown; không backfill bằng inference.

---

# 17. PerformanceTrace wall timestamps — vẫn là P0 evidence correctness

Duration dùng monotonic clock là đúng.

Vấn đề: `started_at` và `finished_at` được materialize từ `utc_now()` tại record-time thay vì true operation entry/exit wall instants.

Target:

```text
entry:
  start_monotonic
  start_wall_utc

exit:
  end_monotonic
  end_wall_utc

duration:
  monotonic delta
```

Acceptance:

```text
duration monotonic remains authoritative
wall timeline corresponds to actual entry/exit
start <= end
cross-ledger correlation no longer uses pseudo-simultaneous record timestamps
```

---

# 18. Runtime/source identity — một phần đã có, cần đóng activation gap

Current source/runtime context đã expose nhiều non-secret identity fields hơn audit baseline, gồm:

```text
server instance / process identity
performance trace version
tool contract profile/count/hash
tool metadata schema/risk ownership
semantic localization availability/reason
```

Đây là progress thực.

Remaining requirement:

```text
source/git identity when trustworthy
runtime package/build identity
policy epoch identity
explicit source-vs-live mismatch visibility
```

Không được giả định:

```text
workspace source HEAD == currently loaded runtime code
```

nếu chưa có matching runtime evidence.

---

# 19. CI/release truth — sửa cách phát biểu sau khi HEAD đã đổi

Audit baseline từng xác minh GitHub Actions run cho SHA:

```text
e45bed968bee6db46bb3041de179cbcf23e3906b
```

bị failure **trước khi execute step** do account payment/spending condition.

Điều này chứng minh:

```text
that SHA did not have independent green GitHub proof
```

và **không** chứng minh test regression.

Nhưng current HEAD đã là:

```text
8581b8331e83cc600c2b813629875639e48a8245
```

Do đó bản cập nhật này **không được gọi run của `e45bed...` là “current HEAD CI”**.

Correct current conclusion:

> Exact-current-HEAD authoritative CI proof chưa được chứng minh trong evidence của revision này; trạng thái billing blocker phải được re-check thay vì mặc định kế thừa.

## 19.1 P0 release gate

Require một trong hai:

```text
GitHub Actions exact-HEAD proof
```

hoặc canonical self-hosted equivalent với exact-SHA provenance.

Acceptance:

```text
jobs actually start
required Linux/Windows steps execute
result binds exact source SHA
failure classification distinguishes infra vs test
artifacts bind the same source/build identity
```

Không dùng local pass như substitute cho independent release proof khi release policy yêu cầu CI.

---

# 20. CI split — fast proof vs canonical release proof

Current broad workflow có nhiều release-grade work.

Recommended structure:

```text
FAST PR/PUSH CI
  MCP focused/default tests
  Electron tests
  frontend typecheck/test
  touched Rust packages when relevant
  schema/static guards

CANONICAL SHA / RELEASE PROOF
  full MCP suite
  required Rust workspace/package gates
  Windows artifact smoke
  installer/package sanitation
  exact-source provenance manifest
```

Điều kiện:

- role audit phải quyết định Rust package nào thật sự canonical release-gate;
- fast CI không masquerade thành release proof;
- release/tag/manual canonical proof dùng exact candidate bytes.

---

# 21. Installer sanitation — P0

Electron Builder copies `resources` broadly. Raw timestamped benchmark/runtime snapshots trong `resources/.../benchmarks/reports` có nguy cơ đi vào installer nếu không explicit filter/move.

Correct outcome:

```text
source repo may retain:
  benchmark code
  schemas
  sanitized canonical fixtures

installer must exclude:
  timestamped local benchmark reports
  production-like runtime snapshots
  local workspace paths
  ad-hoc research artefacts
```

Acceptance:

```text
built installer/resource manifest contains zero raw benchmark report files
zero volatile .coding-tools snapshots packaged
zero unintended local absolute workspace identity in bundled research output
```

Prefer smallest direct fix: explicit packaging filter nếu đó là current build convention; không tạo artifact-management framework mới chỉ cho một exclusion use case.

---

# 22. Exact-source Windows release provenance

Target manifest tối thiểu:

```text
source_sha
app_version
MCP package/version
runtime/native artifact hashes
installer SHA256
built_at
canonical proof run id
```

Flow:

```text
exact SHA
→ canonical proof
→ build once
→ smoke exact bytes
→ publish same bytes
```

Hard invariant:

```text
DO NOT rebuild a “same version” candidate after proof and call it the proved artifact.
```

---

# 23. Handoff — keep, measure, do not overstate

Audit baseline materialized:

```text
handoff_capsules = 5
```

Nó không còn dormant hoàn toàn, nhưng sample vẫn nhỏ.

Measure:

```text
eligible long-task count
capsule trigger rate
resume success
repeated work avoided
model-visible bytes before/after
TTA after resume
```

Decision: KEEP as reliability/continuity primitive; performance ROI remains unproven.

---

# 24. EOCL — measure overhead without weakening authority

Không đọc raw event/state counts như task failure counts.

Metrics nên chuẩn hóa:

```text
replans / accepted run
replan → accepted conversion
unchanged retry attempts
control-plane calls / accepted
control-plane model-visible bytes / accepted
TTA added by authority gates
stale-write conflicts prevented
write-without-lease = 0
```

EOCL state machine có thể tạo reliability value mà không cần mỗi transition thành user/model round-trip.

No recommendation in this report weakens write lease or final acceptance authority.

---

# 25. Rust/Python product-role audit

Đây là maintainability task, không phải “rewrite”.

Mỗi subsystem nên có matrix:

| Subsystem | Runtime role | Release role | Owner | Removal consequence | CI gate |
|---|---|---|---|---|---|
| Python Coding Tools MCP | PRODUCTION | RELEASE-GATE | Python/MCP | desktop execution breaks | yes |
| Electron supervisor | PRODUCTION | RELEASE-GATE | Electron | desktop host breaks | yes |
| Rust ToolRuntime/LSP/connector | SUPPORTING / capability provider | conditional gate | Rust/native | semantic/native path affected | targeted |
| Rust legacy/server surfaces | classify explicitly | classify explicitly | Rust | unknown until dependency audit | based on role |
| npm/native packaging | SUPPORTING/RELEASE | RELEASE-GATE where shipped | release | package install breaks | canonical |

Không xóa Rust trước khi matrix này chứng minh dependency.

Không giữ full broad CI cho một subsystem chỉ vì “đã luôn chạy” nếu role audit chứng minh nó chỉ còn reference.

---

# 26. Maturity score cập nhật

| Trục | Assessment | Lý do |
|---|---:|---|
| Product direction | **9.0/10** | Desktop/Execution Hub target rõ. |
| Model-facing interface | **9.5/10** | 8-tool surface ổn định. |
| Execution architecture | **8.9/10** | One runtime authority, EOCL, durable ledger, bounded mutation/proof. |
| Safety boundaries | **9.0/10** | Lease/authority/high-cost/read-only bridge primitives mạnh. |
| Context efficiency | **8.4/10** | Model-visible shaping tốt; large-result tail vẫn có evidence. |
| Observability implementation | **8.2/10** | v5 metrics, phase/localization counters, cohort/economics, policy epoch source. |
| Observability activation/identity | **6.8/10** | Current-policy/runtime/source activation chưa chứng minh đồng đều. |
| Benchmark validity | **6.3/10** | Real telemetry tốt hơn; paired real-task causal corpus còn thiếu. |
| Routing implementation/safety | **8.0/10** | Promotion-readiness và automatic activation fail-closed mạnh hơn. |
| Routing causal evidence | **5.8/10** | Cheap/model lanes vẫn thiếu paired representative evidence. |
| Semantic source readiness | **8.0/10** | Native boundary substantial. |
| Semantic live activation | **4.0/10** | Binding currently not configured; attempts = 0. |
| Maintainability | **6.5/10** | Rust/Python role overlap vẫn cần ownership classification. |
| Release evidence maturity | **6.0/10** | Exact current HEAD CI proof chưa có trong revision evidence. |

### Overall interpretation

```text
Engineering/product maturity          ~8/10
Scientific/causal evidence maturity   ~6–6.5/10
Release-proof maturity                ~6/10 until exact-HEAD proof closes
```

Không dùng các điểm này như KPI; chúng là prioritization aid.

---

# 27. Claim-by-claim matrix — Advisory A

| Claim / recommendation | Verdict | Fit | Current correction |
|---|---|---:|---|
| Chuyển từ feature-building sang evidence/simplification | **CONFIRMED** | 10/10 | Vẫn là thesis chính. |
| Tách implemented/tested/measured/simulated/causal | **CONFIRMED** | 10/10 | Bổ sung ACTIVE/PROVEN distinction. |
| Electron + Python MCP là desktop hot path | **CONFIRMED** | 10/10 | Không đổi. |
| Rust/Python tạo ownership ambiguity | **MOSTLY CONFIRMED** | 9.2/10 | Role audit, không xóa Rust mù. |
| Giữ smart-v3 8 tools | **CONFIRMED** | 10/10 | Hard invariant. |
| Minimum sufficient interaction | **CONFIRMED** | 9.5/10 | Tránh workflow ritual. |
| Bounded candidate context | **CONFIRMED** | 9.5/10 | Chỉ tăng context khi miss evidence chứng minh cần. |
| Semantic localization có ROI tiềm năng | **CONDITIONAL** | 8/10 | Source boundary mạnh hơn; live binding vẫn absent. |
| Simulation không phải production routing proof | **CONFIRMED** | 10/10 | Promotion source hiện cũng fail-closed hơn. |
| Snapshot 610 calls | **STALE** | — | Audit baseline đã 2,471; current live observation >2,500. |
| Idempotency là P1 | **MOSTLY CONFIRMED** | 9.5/10 | Task đúng là current-policy activation + fault proof. |
| Broad historical idempotency ratio là gate | **REJECT** | — | Gate phải dùng current policy epoch. |
| Proof cache chưa chứng minh ROI | **CONFIRMED** | 10/10 | 1 observed hit / 999ms. |
| `estimated_wait_ms` không causal | **CONFIRMED** | 10/10 | Vẫn đúng. |
| PerformanceTrace wall timestamps cần sửa | **CONFIRMED** | 9.8/10 | Vẫn open. |
| Tiny payload benchmark không đại diện tail | **STRONGLY CONFIRMED** | 10/10 | p95 >1.15MB/run baseline. |
| Diff continuation đáng làm | **CONFIRMED** | 9.6/10 | Top P1 hot-path improvement. |
| Raw benchmark reports không nên ship | **CONFIRMED** | 10/10 | P0 packaging. |
| Baseline CI billing failure là test regression | **REJECT** | 10/10 clarity | Là infra pre-start failure. |
| Exact current HEAD có CI green proof | **UNPROVEN** | — | HEAD đã đổi; re-check/run exact SHA. |
| CI nên split fast/canonical | **MOSTLY CONFIRMED** | 8.8/10 | Sau subsystem role audit. |
| TTA là north-star | **CONFIRMED** | 10/10 | Ledger supports durable TTA. |
| Real-task paired routing cần thiết | **CONFIRMED** | 9.5/10 | Instrumentation có, causal sample còn thiếu. |
| Freeze feature expansion một cycle | **CONFIRMED** | 9.5/10 | Ngoại lệ reliability/evidence blocker. |

---

# 28. Claim-by-claim matrix — Advisory B

| Upstream recommendation | Current state | Fit | Correct priority |
|---|---|---:|---|
| Source-fenced Git diff continuation | Gap còn rõ ở Python hot path | **9.6/10** | **P1-high**. |
| Bounded LSP Call Hierarchy | Capability gap còn; prerequisite source bridge improved | concept **8.5/10** | **P2 experiment after activation**. |
| E2E prebuilt binary reuse | Depends on Rust release role | **7/10** | P1/P2 CI optimization if justified. |
| Focused Go validation | No demand evidence | **4.5/10 immediate** | P3 demand-driven. |
| Structured file delete | Safety capability, no strong current demand | **6/10** | P3/demand-driven. |
| Skip duplicate Python search retry port | Python already has centralized retry | **9.5/10** | Correct: skip. |
| `webcodex disconnect` | Not desktop hot path | **3.5/10** | Defer. |
| Exact-source release provenance | Still valuable | **9/10** | P1 after CI truth. |
| Copy multi-platform release framework | Unnecessary for Windows-first target | **1/10 desirability** | Do not copy wholesale. |
| Do not increase public tool count | Smart-v3 stable | **10/10** | Hard invariant. |

---

# 29. Những corrections bắt buộc để implementation không đi sai

## 29.1 Không dùng old HEAD CI status như current HEAD truth

CI evidence phải bind exact SHA.

## 29.2 Không gọi historical required coverage là current policy gate

Historical auditability và promotion coverage là hai views khác nhau.

## 29.3 Không gọi source-ready semantic bridge là live-active LSP

`NATIVE_LSP_BINDING_NOT_CONFIGURED` là evidence rõ ràng.

## 29.4 Không gọi raw `response_bytes` là token usage

Tách transport bytes, model-visible bytes, provider tokens/cost.

## 29.5 Không port Call Hierarchy trước khi live semantic path có workload

Không thêm Rust code chỉ để zero desktop hot-path calls dùng nó.

## 29.6 Không broaden proof cache fingerprint để chase hits

Proof truth > hit rate.

## 29.7 Không tăng public tools

Continuation/LSP/call hierarchy là internal acceleration.

## 29.8 Không xóa Rust trước dependency-role audit

Simplification phải dựa trên dependency, không dựa trên trực giác.

---

# 30. Dependency graph của phương án

```text
[Current source HEAD + runtime identity]
                │
                ▼
      [Exact-HEAD evidence truth]
        ├────────┼─────────┐
        ▼        ▼         ▼
   [CI proof] [Packaging] [True timestamps]
        │        │         │
        └────────┴────┬────┘
                     ▼
           [Reliable measurement base]
             ├───────────────┐
             ▼               ▼
 [Current-policy idempotency] [Large-result continuation]
             │               │
             ▼               ▼
       [Fault proof]    [Tail experiment]
             └────────┬──────┘
                      ▼
              [Release-ready core]
                      │
                      ▼
          [Semantic binding activation]
                      │
                      ▼
             [Live localization data]
               ├─────────────┐
               ▼             ▼
      [Call Hierarchy] [Router paired trials]
               └──────┬──────┘
                      ▼
              [KEEP / REMOVE / DEFER]
```

Critical path không yêu cầu Call Hierarchy để hoàn thành release/evidence truth.

---

# 31. Execution Wave 0 — Baseline lock + operational hygiene

## Objective

Đảm bảo mọi wave sau có một starting point rõ và không lẫn source/runtime/stale-state.

## Actions

```text
W0.1 record current source HEAD
W0.2 record live runtime identity / performance schema / process instance
W0.3 classify source-vs-runtime mismatch if present
W0.4 reconcile or explicitly close/account for stale orchestration run
W0.5 freeze speculative feature expansion
W0.6 preserve unrelated worktree/runtime state; no cleanup/reset
```

## Exit criteria

```text
one explicit baseline SHA
one explicit runtime identity
no unexplained stale active authority state
feature backlog frozen except reliability/evidence blockers
```

## Rollback

No product behavior change; this wave is operational/evidence hygiene.

---

# 32. Execution Wave 1 — Release and evidence truth

## W1.1 Exact-HEAD CI

Goal:

```text
current candidate SHA has independently executable proof
```

Acceptance:

```text
jobs start
steps execute
infra failure vs test failure classified
Linux/Windows required gates bind same SHA
```

## W1.2 Installer sanitation

Goal: raw benchmark/runtime snapshots absent from product bytes.

Acceptance: inspect canonical built resources/manifest, not source assumption only.

## W1.3 True wall timestamps

Goal: PerformanceTrace forensic wall timeline becomes real.

Acceptance: monotonic duration preserved + true entry/exit wall instants.

## W1.4 Runtime/source identity

Goal: source/runtime mismatch visible without exposing secrets.

Acceptance:

```text
runtime build/package identity visible
source identity visible when trustworthy
policy epoch visible
process/server identity visible
```

## Wave 1 exit gate

Do not proceed to performance promotion decisions until evidence emitted by the running candidate can be attributed to the correct source/runtime.

---

# 33. Execution Wave 2A — Required idempotency closure

## Entry

Wave 1 identity/timestamp foundation available enough to attribute observations.

## Actions

1. Enumerate all `required` operations.
2. Verify stable semantic key derivation/explicit key per operation.
3. Ensure `task_epoch_v1` current-policy counters are actually materialized by live runtime.
4. Run focused fault injection around all required operation classes.
5. Validate controller/authority fencing changes identity where required.
6. Confirm optional repeat semantics unchanged.

## Exit

```text
policy completeness: 100% required operations mapped
current policy epoch: visible
current-policy measured coverage: >= configured target (currently 95%) with n reported
at-most-once fault invariants: pass
known key collision: 0
```

## Stop conditions

- any duplicate required side effect;
- outcome-unknown classified as safe pre-start;
- authority/fencing collision;
- optional semantics accidentally converted into required dedup.

---

# 34. Execution Wave 2B — Source-fenced continuation + result-tail metrics

## Entry

Large-result bottleneck already has audit evidence; no new feature-need proof required.

## Actions

1. Implement first concrete continuation use case in internal diff/evidence path.
2. Bind cursor to source/worktree + scope/options.
3. Fail closed on stale cursor.
4. Bound page/model-visible output.
5. Add continuation/truncation/re-read metrics.
6. Run paired real-task large-diff corpus.

## Exit

```text
mixed-source page incident = 0
stale cursor returns explicit failure
page duplication/skip = 0 in focused tests
smart-v3 remains 8 tools
accepted rate non-regression
p90/p95 tail or re-read/TTA shows meaningful improvement on target corpus
```

## Rollback design

Keep first-page behavior backward compatible. If continuation path fails or underperforms, revert internal continuation use while preserving existing bounded result behavior; no public tool schema rollback should be necessary.

---

# 35. Execution Wave 2C — Proof-cache opportunity study

Do not optimize proof-cache implementation until opportunity is quantified.

Capture per proof stage:

```text
eligible
hit
miss reason
fingerprint class
stage version
saved_ms
accepted-run relation
```

After representative window:

```text
if opportunity and savings meaningful -> keep accelerator
if opportunity low -> retain exact reuse semantics, demote performance claim
```

No fingerprint weakening.

---

# 36. Execution Wave 2D — Exact-source Windows release provenance

Requires Wave 1 CI/build truth.

Acceptance manifest:

```text
source_sha
app_version
MCP version/build identity
native artifact hashes if shipped
installer sha256
canonical proof id
built_at
```

Same candidate bytes must be smoked and published.

---

# 37. Execution Wave 3 — Semantic provider live activation

## Entry

Source bridge exists; live binding currently absent.

## Actions

1. Configure project-scoped native semantic endpoint/credential through existing intended configuration path.
2. Start/fresh-load runtime under controlled conditions when operationally authorized.
3. Smoke `symbol`, `definition`, `references` through Python internal semantic-first path.
4. Test auth failure, workspace mismatch, invalid action/path, provider unavailable.
5. Verify fallback search remains functional.
6. Capture live localization telemetry.

## Exit

```text
semantic_available samples > 0 on eligible workloads
semantic_attempted > 0
semantic_handled > 0 on at least some real eligible cases
unauthenticated request succeeds = 0
workspace escape succeeds = 0
mutation via semantic bridge = 0
fallback failure when provider absent = 0
public tool count = 8
```

This report does **not** authorize a runtime restart/deploy by itself; operational activation is a separate explicit action.

---

# 38. Execution Wave 4A — Call Hierarchy experiment

## Entry

Do not start until Wave 3 produces live semantic evidence.

Select only qualified cross-file impact-analysis cases.

Compare:

```text
A semantic definition/reference + fallback
B same + bounded Call Hierarchy
```

Keep if:

- accepted rate non-regression;
- localization recall or TTA improves;
- model-visible/read amplification does not regress materially;
- no new authority surface.

Defer/remove if it mostly adds calls/context without accepted-work benefit.

---

# 39. Execution Wave 4B — Paired routing experiments

## Entry

Evidence identity/canonical accepted-run metrics stable.

Task classes may include:

```text
localized bugfix
test failure
bounded feature
cross-file feature/refactor
integration
recovery
security/authority-sensitive
```

Pairing requirement:

```text
same task
same base SHA
same environment
same acceptance contract
actual route A
actual route B
```

Report:

```text
n
first-pass accepted delta
TTA paired delta
cost/accepted delta
model-visible bytes delta
repair/replan delta
95% CI where appropriate
```

Do not infer route policy from global averages.

### Terra

Remains:

```text
shadow / explicit
```

No automatic promotion in this roadmap.

---

# 40. Execution Wave 5 — Simplification decision

Sau các experiments, mỗi accelerator phải được phân loại:

```text
KEEP
KEEP BUT DEMOTE CLAIM
FIX
REMOVE
DEFER
```

Examples:

- continuation: KEEP if tail/TTA benefit confirmed;
- proof cache: potentially KEEP but demote performance claim if opportunity low;
- Call Hierarchy: KEEP only if target workload benefits;
- Terra: remain shadow if evidence insufficient;
- unused Rust subsystem: consider reduced CI/maintenance only after dependency-role proof.

Đây là wave biến “scientific evidence” thành actual simplification, không chỉ thêm dashboards.

---

# 41. Acceptance matrix — hard gates

| Area | Must be true before calling complete |
|---|---|
| Source identity | Candidate SHA explicitly recorded; runtime/source relation visible. |
| CI | Canonical exact-SHA jobs actually execute; infra/test failure classified. |
| Packaging | No raw benchmark/runtime snapshots in installer. |
| Performance timestamps | True entry/exit wall timestamps; monotonic duration retained. |
| Idempotency policy | Every required operation has correct key strategy. |
| Idempotency activation | Current policy epoch visible; configured coverage gate passes with sample count. |
| Idempotency reliability | Fault injection finds no duplicate required side effect. |
| Continuation | Source-fenced, stale fails closed, no page duplicate/skip. |
| Tool contract | Smart-v3 remains exactly 8 public tools. |
| Semantic binding | Authenticated, workspace-scoped, read-only, bounded, fail-closed. |
| Semantic activation | Nonzero live availability/attempt/handled evidence on eligible tasks. |
| Call Hierarchy | Only after semantic activation; target-corpus accepted-work benefit. |
| Routing | Paired representative evidence; no synthetic auto-promotion. |
| Terra | Explicit/shadow until separate promotion decision. |
| Proof cache | Exact fingerprint semantics preserved. |
| Release provenance | Published candidate bytes match proved candidate hashes. |
| Operational state | No unexplained stale/active authority state. |

---

# 42. Measurement plan

## 42.1 Hard constraints

```text
correctness
security
write authority
proof truth
source consistency
```

Any violation kills an optimization regardless of speed/cost.

## 42.2 Primary product metrics

```text
first-pass accepted rate
TTA p50/p90/p95
```

## 42.3 Context/result metrics

```text
response_bytes/run p50/p90/p95/p99
model_visible_bytes/run p50/p90/p95/p99
continuation rate
truncation rate
re-read rate
artifact spill rate
```

## 42.4 Reliability metrics

```text
current-policy required coverage + n
at-most-once violations
unknown-outcome events
replan/accepted
stale-run count
write-without-lease
```

## 42.5 Semantic metrics

```text
localization samples
semantic availability rate
semantic attempted
semantic handled
fallback queries
fallback rate
localization bytes/time
```

## 42.6 Routing metrics

```text
accepted cohort coverage
route/task-class n
first-pass acceptance by paired task
TTA paired delta
cost/accepted
repair/replan delta
```

## 42.7 Release metrics

```text
exact SHA proof status
artifact hash match
installer sanitation status
```

---

# 43. Canonical experiment framework

Mỗi optimization PR phải trả lời:

1. Bottleneck nào đã được quan sát?
2. Evidence source/class nào chứng minh nó?
3. Baseline exact SHA là gì?
4. Candidate thay đúng biến nào?
5. Hard invariant nào không được regress?
6. Primary accepted-work outcome là gì?
7. Secondary TTA/cost/context metrics nào?
8. Task corpus/class nào?
9. Sample `n` là bao nhiêu?
10. Effect size / uncertainty là gì?
11. Keep rule là gì?
12. Kill/rollback rule là gì?

Suggested record:

```yaml
experiment_id: ...
baseline_sha: ...
candidate_sha: ...
evidence_class: E4
task_class: ...
corpus_hash: ...
primary_metric: accepted
secondary:
  - tta_ms
  - model_visible_bytes
  - response_bytes
  - provider_cost
hard_invariants:
  - correctness
  - proof_truth
  - authority
  - source_consistency
keep_rule: ...
kill_rule: ...
```

Workload skewed nên report:

```text
median
p90
p95
paired deltas
bootstrap 95% CI when useful
```

Binary paired acceptance có thể dùng paired outcome matrix/McNemar khi sample phù hợp.

Không publish percentage mà không có `n`.

---

# 44. Rollout / rollback strategy

## 44.1 General rule

Ưu tiên additive/internal changes không phá public contract.

```text
public smart-v3 contract stable
internal acceleration can be disabled/reverted independently
fallback path remains deterministic
```

## 44.2 Continuation

Rollout:

- first-page semantics giữ compatible;
- continuation chỉ xuất hiện khi result vượt bound;
- source fence checked every page.

Rollback:

- stop consuming/producing continuation internally;
- return current bounded result path;
- không cần connector/tool-schema migration.

## 44.3 Idempotency

Rollout:

- new current policy epoch isolates new measurement;
- preserve cumulative historical counters for audit;
- fail closed on conflicting key identity.

Rollback:

- không rollback bằng cách bỏ replay protection;
- nếu policy bug, revert affected operation mapping/key derivation to last known correct policy and start a new explicit epoch if semantics changed.

## 44.4 Semantic provider

Rollout:

- internal binding only;
- read-only;
- fallback to text when unavailable.

Rollback:

- remove/disable binding configuration;
- Python path returns to deterministic text fallback;
- no public tool change.

## 44.5 Routing

Rollout:

- shadow recommendation / explicit route experiments;
- no automatic activation.

Rollback:

- disable experiment/shadow decision use;
- deterministic-first remains default.

## 44.6 Release evidence

No rollback from proven artifact to rebuilt unproven bytes. If candidate fails, create a new candidate SHA/build and prove it again.

---

# 45. Ownership boundaries

| Concern | Canonical owner | Non-owner roles |
|---|---|---|
| Project mutation authority | EOCL + permission + write lease | model/provider may propose only |
| Public model-facing tool schema | Python ToolContract/ToolSpec surface | Rust capability must not silently expand it |
| Native execution risk metadata | Rust ToolMetadata/ToolRisk where native | Python maps presentation/public contract |
| Accepted-run causal ledger | Orchestration ledger | performance.json is materialized view |
| Runtime performance view | PerformanceTrace | not causal authority by itself |
| Semantic mutation | none | semantic bridge is read-only |
| Routing promotion | evidence/policy gate | benchmark/simulation cannot self-promote |
| Final acceptance | Sol/control plane + deterministic proof contract | candidates/reviewers do not self-accept |
| Release provenance | canonical release workflow | local ad-hoc build not substitute |

This table prevents future “capability exists => authority owns it” drift.

---

# 46. Risk register cập nhật

## R1 — Source/runtime activation mismatch

**Risk:** source has policy/bridge metadata but live process may not materialize the same state.

**Mitigation:** runtime/source/policy identity + exact activation proof.

## R2 — Exact-current-HEAD CI unknown

**Risk:** old billing-blocked SHA is incorrectly called current.

**Mitigation:** exact-HEAD CI proof; never inherit status across SHA.

## R3 — Installer contamination

**Risk:** raw benchmark/runtime snapshots shipped via broad `resources` copy.

**Mitigation:** explicit filter/move + inspect built artifact.

## R4 — Large result tail

**Risk:** transport/evidence amplification increases latency/context/tool turns.

**Mitigation:** source-fenced continuation + tail metrics.

## R5 — Historical idempotency ratio misused

**Risk:** cumulative old misses depress/mislead current gate, or old success masks current bugs.

**Mitigation:** named policy epoch + current-policy gate + fault proof.

## R6 — Semantic source capability without live binding

**Risk:** project claims LSP value while hot path never calls it.

**Mitigation:** explicit ACTIVE state and live telemetry.

## R7 — Router overfit

**Risk:** cheap/model lane tiny cohorts promoted.

**Mitigation:** paired real tasks + `automatic_activation=false`.

## R8 — Proof-cache pressure weakens correctness

**Risk:** broader fingerprints increase false reuse.

**Mitigation:** exact fingerprint is hard invariant.

## R9 — Rust/Python maintenance tax

**Risk:** duplicate capability/CI without clear product role.

**Mitigation:** subsystem role matrix before removal or broad gate retention.

## R10 — Stale orchestration state

**Risk:** audit/control plane reports active/stale history ambiguously.

**Mitigation:** use existing reconciliation semantics; account for current stale run before green declaration.

---

# 47. Updated North-Star architecture

```text
                         USER
                          │
                          ▼
                     ChatWeb Sol
              semantic/final authority
                          │
                          ▼
                  ┌───────────────┐
                  │ smart-v3 / 8  │
                  └───────┬───────┘
                          │
                          ▼
                  agent_workflow
                          │
        ┌─────────────────┼──────────────────┐
        ▼                 ▼                  ▼
 deterministic       Mini/Luna            Sol deep
 evidence/proof       bounded         integration/high-width
        │                 │                  │
        └─────────────────┴──────────────────┘
                          │
                          ▼
                    MCP write lease
                          │
                          ▼
                  deterministic proof
                          │
                          ▼
                     acceptance

Internal read-only accelerators:
  source-fenced continuation
  semantic localization
  bounded Call Hierarchy (only if proven)
  proof reuse with exact fingerprint

Cross-cutting evidence/control:
  EOCL
  canonical ledger
  current-policy idempotency epoch
  runtime/source identity
  usage/economics provenance
  routing promotion-readiness
  bounded result shaping
```

Không có accelerator nào tạo authority plane mới.

---

# 48. Final decision matrix

## KEEP CORE

```text
smart-v3 8 tools
one Coding Tools MCP runtime authority
deterministic-first
bounded candidate packets
EOCL/write lease
canonical orchestration ledger
read-only candidate/review roles
high-cost explicit gates
provider usage provenance
routing automatic_activation=false
```

## FIX / PROVE NOW

```text
exact-current-HEAD CI/release truth
installer benchmark/runtime snapshot sanitation
true PerformanceTrace wall timestamps
runtime/source/policy identity
stale orchestration-state hygiene
current-policy idempotency activation evidence
```

## IMPLEMENT NEXT WITH STRONG EXISTING EVIDENCE

```text
source-fenced continuation
result-tail metrics
required idempotency fault-proofing
exact-source Windows release provenance
```

## MEASURE BEFORE OPTIMIZING

```text
proof-cache ROI
handoff ROI
EOCL overhead
```

## ACTIVATE THEN EXPERIMENT

```text
native semantic binding
Call Hierarchy
empirical route calibration
```

## DEMAND-DRIVEN / DEFER

```text
focused Go validation
structured file delete
webcodex disconnect
MCP Tasks adapter
other upstream capabilities without observed local demand
```

## DO NOT DO

```text
merge WebCodex upstream wholesale
increase smart-v3 public tool count
call simulation production savings
interpret inter-tool gap as model latency
use historical required coverage as current policy gate
auto-promote Terra from tiny samples
weaken proof fingerprint to chase cache hits
ship raw production/research snapshots
remove Rust before dependency-role audit
call source-ready semantic code “live LSP” before binding
call old-SHA CI status current after HEAD changes
```

---

# 49. Phương án ưu tiên cuối cùng

## P0 — Release/evidence truth

```text
P0.0 baseline source/runtime identity + reconcile stale run
P0.1 exact-current-HEAD CI proof
P0.2 exclude raw benchmark/runtime snapshots from installer
P0.3 true PerformanceTrace wall timestamps
P0.4 runtime/source/policy identity activation
P0.5 freeze speculative feature expansion
```

## P1 — Demonstrated bottlenecks and reliability

```text
P1.1 source-fenced continuation in Python/internal agent_workflow
P1.2 required idempotency current-policy activation + fault proof
P1.3 result-tail telemetry
P1.4 proof-cache opportunity study
P1.5 exact-source Windows release provenance
```

## P2 — Activate existing semantic capability, then experiment

```text
P2.1 bind/prove native semantic provider end-to-end
P2.2 measure semantic localization workload
P2.3 bounded Call Hierarchy experiment
P2.4 paired real-task routing experiments
P2.5 Terra remains shadow/explicit
P2.6 Rust E2E prebuilt reuse only if role audit keeps Rust as material release gate
```

## P3 — Demand-driven

```text
focused Go
structured delete
MCP Tasks adapter
webcodex disconnect
other upstream convenience capabilities
```

---

# 50. Definition of Done cho toàn phương án

Không gọi roadmap này “hoàn thành” chỉ vì code merged.

Toàn phương án chỉ đạt Done khi:

1. **Evidence truth:** current candidate có exact-source CI/release proof hoặc canonical equivalent.
2. **Packaging:** built product không chứa raw research/runtime snapshots.
3. **Telemetry:** wall timestamps và runtime/source/policy identity đáng tin.
4. **Idempotency:** required operations policy-complete, current-policy gate có representative samples và fault suite chứng minh at-most-once.
5. **Large results:** continuation source-fenced hoạt động, tail/re-read/TTA được đo, không regress acceptance.
6. **Semantic:** live binding chỉ được gọi active sau khi telemetry có semantic attempts/handled và security boundary smoke pass.
7. **Call Hierarchy:** chỉ được giữ nếu experiment chứng minh target-workload value.
8. **Routing:** promotion dựa trên real paired accepted evidence; no automatic activation từ synthetic/tiny cohorts.
9. **Proof cache/handoff:** claim performance khớp opportunity data; không marketing bằng implementation existence.
10. **Maintainability:** Rust/Python subsystem roles rõ đủ để quyết định CI/ownership/deprecation.
11. **Operational hygiene:** không còn unexplained stale authority/run state.
12. **Public contract:** Smart-v3 vẫn 8 tools trừ khi một future independent evidence review chứng minh cần thay đổi.

---

# 51. Kết luận cuối

Kết luận quan trọng nhất sau khi nối audit baseline với current HEAD là:

> **Tools-Codex-web không còn thiếu nhiều primitive; nó đang thiếu bằng chứng activation và causal value đủ mạnh để biết primitive nào nên trở thành product policy lâu dài.**

Bottleneck ưu tiên không phải:

```text
new agent
new route
new provider
new graph
more orchestration
```

mà là:

```text
exact evidence truth
→ reliable replay semantics
→ large-result hot-path efficiency
→ prove existing semantic capability live
→ causal experiments
→ simplification
```

Current source đã tiến thêm một bước quan trọng: routing promotion fail-closed hơn và native semantic trust boundary đã có nhiều primitive thực. Nhưng điều này **không làm mất giá trị của evidence-first thesis**; ngược lại, nó làm thesis rõ hơn:

```text
source capability is no longer the scarce resource;
credible activation + accepted-work evidence is.
```

Nếu thực hiện đúng dependency order trong tài liệu này, Tools-Codex-web có thể cải thiện đồng thời:

- Time To Accepted Result;
- result/context efficiency;
- retry/reconnect reliability;
- release provenance;
- routing scientific validity;
- semantic localization usefulness;
- maintenance simplicity;

mà không tăng public tool surface hoặc tạo thêm authority plane.

### Final north-star

```text
OPTIMIZE THE COST AND TIME OF A CORRECT ACCEPTED RESULT,
AND REQUIRE EACH COMPLEXITY LAYER TO PROVE ITS VALUE.
```

---

# Appendix A — Audit baseline evidence snapshot

## Repository baseline

```text
HEAD: e45bed968bee6db46bb3041de179cbcf23e3906b
branch: main
app: web-mcp-assistant 0.3.4
smart-v3 tool count: 8
smart-v3 SHA256: 4283e098c315d015c457ce2ab781257491ef70607c6c577f7699969fb8c3f754
```

## Performance baseline

```text
version 5
tool_calls 2471
errors 201
cache_hits 10
deduplicated_calls 0
idempotency_eligible 1674
idempotency_eligible_keyed 384
idempotency_required 60
idempotency_required_keyed 46
idempotency_optional 74
idempotency_optional_keyed 3
idempotency_auto_keys 43
proof_cache_eligible 34
proof_cache_hits 1
proof_cache_saved_ms 999
local_execution_ms 5348626
estimated_wait_ms 45351236
request_bytes 3654191
response_bytes 71065969
model_visible_bytes 5983100
phase_timing_samples 15
localization_samples 8
lsp_available_samples 0
lsp_attempted_queries 0
lsp_handled_queries 0
fallback_search_queries 62
```

## Route baseline

```text
deterministic 785
mini 11
luna 10
sol_xhigh 36
terra 8
```

## Response bytes / run, n=172

```text
p50 150425
p90 737458
p95 1150922
p99 1750683
max 3557410
```

## Ledger materialized baseline

```text
accepted runs 109
accepted run TTA p50 79.791s
accepted run TTA p90 326.287s
proof records 211
handoff capsules 5
idempotency completed 345
idempotency failed 12
idempotency unknown 41
```

---

# Appendix B — Current-state observation before this revision write

## Repository

```text
HEAD: 8581b8331e83cc600c2b813629875639e48a8245
branch: main
smart-v3 tool count: 8
performance trace: v5
semantic provider live status: NATIVE_LSP_BINDING_NOT_CONFIGURED
```

## Performance observation

```text
tool_calls 2583
errors 213
cache_hits 10
response_bytes 80548263
model_visible_bytes 6209070
local_execution_ms 5551859
estimated_wait_ms 47772867
historical_required_calls 76
historical_required_keyed 57
optional_calls 241
optional_keyed 10
auto_key_calls 54
proof_cache_eligible 51
proof_cache_hits 1
proof_cache_misses 51
proof_cache_saved_ms 999
localization_samples 19
localization_queries 149
lsp_available_samples 0
lsp_attempted_queries 0
lsp_handled_queries 0
fallback_search_queries 149
```

## Current route observation

```text
deterministic 829
mini 11
luna 10
sol_xhigh 36
terra 8
```

### Caveat

Các counters này tiếp tục tăng khi runtime được sử dụng. Appendix B chỉ chứng minh direction/status tại observation point, không phải immutable benchmark result.

---

# Appendix C — Current source deltas materially affecting the solution

## Idempotency policy epoch

```text
IDEMPOTENCY_POLICY_EPOCH = task_epoch_v1
```

Current source supports current-policy required counters and a runtime-activation coverage target of `0.95`. Historical cumulative required counters remain audit history and must not be substituted for current-policy gate.

## Semantic bridge

Current source provides production-oriented boundary primitives including loopback/project credential/workspace/read-only/bounded/fail-closed checks, but live provider binding is not configured in the observation.

## Routing promotion

Current source keeps routing-v2 promotion fail-closed with `automatic_activation=false` and excludes synthetic/benchmark evidence from production promotion decisions.

---

# Appendix D — External references from the original audit

These references are retained as the sources checked by the original audit. “Latest” claims are scoped to the audit time unless re-verified separately.

1. Yang et al. **SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering.** NeurIPS 2024 / arXiv:2405.15793.  
   `https://arxiv.org/abs/2405.15793`

2. Xia et al. **Agentless: Demystifying LLM-based Software Engineering Agents.** arXiv:2407.01489.  
   `https://arxiv.org/abs/2407.01489`

3. Ong et al. **RouteLLM: Learning to Route LLMs with Preference Data.** arXiv:2406.18665.  
   `https://arxiv.org/abs/2406.18665`

4. Liu et al. **Lost in the Middle: How Language Models Use Long Contexts.** arXiv:2307.03172.  
   `https://arxiv.org/abs/2307.03172`

5. Model Context Protocol maintainers. **The 2026-07-28 Specification.**  
   `https://blog.modelcontextprotocol.io/posts/2026-07-28/`

6. WebCodex upstream release **v0.3.7**, as checked at original audit time.  
   `https://github.com/yyjeqhc/webcodex/releases/tag/v0.3.7`

---

# Appendix E — Provenance and caveats

- `.coding-tools/*` là dynamic runtime evidence; số liệu thay đổi theo tool calls trong và sau audit.
- Audit baseline và current-state observation được giữ tách biệt để tránh evidence drift.
- `estimated_wait_ms` là runtime gap proxy, không phải model/network latency.
- `response_bytes` là transport/result volume, không phải provider billing tokens.
- PerformanceTrace broad/historical idempotency counters là audit view; current policy epoch counters mới là production gate khi active.
- Proof-cache hit/miss counters phải được hiểu theo eligibility/fingerprint/stage-version semantics.
- Route counts là event/tool aggregates, không phải task acceptance probability.
- EOCL state counts là observations/events, không phải failed-task counts.
- Cohort comparison với `n` nhỏ không đủ cho automatic route promotion.
- CI status phải bind exact SHA; một run của `e45bed...` không được gọi là current status cho `8581b83...`.
- Source-ready native semantic bridge không đồng nghĩa live semantic provider active.
- External papers/upstream releases là design priors/reference; không thay local paired evidence.
- Revision này chỉ cập nhật tài liệu nghiên cứu/phương án; không tự nó authorize production restart, deploy, route promotion hoặc external release.

---

# Appendix F — Change log của revision này

Revision này bổ sung/correct các điểm sau so với bản audit ban đầu:

1. Tách **Audit baseline HEAD** và **Current update HEAD**.
2. Không gọi CI run của SHA cũ là current HEAD status.
3. Bổ sung current live PerformanceTrace delta mà không ghi đè baseline.
4. Phân biệt historical required-idempotency ratio với `task_epoch_v1` current-policy gate.
5. Ghi nhận routing promotion source hiện fail-closed hơn với `automatic_activation=false`.
6. Ghi nhận native semantic trust boundary đã substantial source-ready nhưng live binding vẫn `NATIVE_LSP_BINDING_NOT_CONFIGURED`.
7. Bổ sung stale orchestration state như operational hygiene gate.
8. Chuyển roadmap P0–P3 thành execution waves có dependency, entry/exit criteria, stop conditions và rollback semantics.
9. Bổ sung hard acceptance matrix và Definition of Done toàn phương án.
10. Bổ sung ownership matrix để ngăn duplicate authority giữa Python/Rust/provider layers.
11. Bổ sung rollout/rollback strategy cho continuation, idempotency, semantic binding, routing và release proof.
12. Giữ invariant `smart-v3 = 8 tools` xuyên suốt toàn bộ phương án.
