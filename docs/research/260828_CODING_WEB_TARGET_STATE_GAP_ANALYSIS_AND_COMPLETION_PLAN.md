# CODING WEB — TARGET STATE, CURRENT REALITY, GAP ANALYSIS AND COMPLETION PLAN

**Ngày đánh giá:** 2026-08-28  
**Workspace:** `E:\DEV\Codex-web`  
**Loại tài liệu:** Strategic architecture decision / live-state assessment / upstream adoption matrix / completion roadmap  
**Mục tiêu sử dụng:** Làm tài liệu quyết định trước khi tiếp tục triển khai lớn; dùng để đánh giá cái gì phải giữ, cái gì phải sửa, cái gì nên port từ upstream, cái gì phải hoãn hoặc loại bỏ.

---

# 0. Executive decision

## 0.1. Mục tiêu của Coding Web

Coding Web không nên được định nghĩa là “một MCP server nhiều tool hơn”, cũng không nên trở thành “một WebCodex fork nhiều orchestration hơn”. Mục tiêu đúng của dự án là:

> **Xây dựng một Trusted Software Problem-Resolution Platform cho phép ChatGPT/Codex và các client AI làm việc trên repository thật — local hoặc remote — với đúng workspace/source, đúng authority, đúng business semantics, đúng execution boundary, có evidence đáng tin cậy và chỉ kết luận hoàn thành khi user problem thực tế đã được giải quyết trong một Resolution Envelope xác định.**

North Star giữ nguyên:

```text
TTPR = Time to Trusted Problem Resolution
```

Dự án phải tối ưu:

```text
Trusted outcome
→ first-pass correctness
→ lower rework
→ lower false closure
→ lower operator intervention
→ lower total expected work
→ lower TTPR p50/p90
```

Không tối ưu cuối cùng cho:

```text
số RUN
số WAVE
số model
số tool
số proof
số automation state
số control-plane feature
model call latency riêng lẻ
LOC
```

Các metric trên chỉ là diagnostic hoặc secondary economics.

---

## 0.2. Kết luận về trạng thái hiện tại

Coding Web đã vượt xa giai đoạn POC. Execution/control architecture hiện đã có:

- endpoint/device/process identity;
- workspace identity + generation;
- smart-v3 8-tool model-facing surface;
- EOCL, write ownership, proof, checkpoint;
- model routing và Codex lanes;
- activation/recovery/tunnel;
- runtime/source fingerprint;
- performance telemetry;
- Problem Resolution Lineage;
- bounded context/task continuation;
- Electron operator UI.

Tuy nhiên dự án **chưa operationally converged**.

Snapshot live ngày 2026-08-28 cho thấy:

```text
Git HEAD:
148de18795787e820ef1bc51d0f2591052d24238

Git branch:
main

ahead / behind origin/main:
0 / 0

worktree:
DIRTY

runtime_version:
0.4.3

smart tool profile:
smart-v3

tool_count:
8

stale_orchestration_runs:
71

unresolved_stale_orchestration_runs:
71

task_orchestration_projection_reconciled:
false

semantic localization:
unavailable / NATIVE_LSP_BINDING_NOT_CONFIGURED
```

`npm run dev:status` cùng ngày cho thấy:

```text
DEV_UI STATUS state=STALE
update_pending=true
running_revision=871ef6c777ddde3eb6ca8ba6c6a5f25b14c52c366db745ff8ac79ceee48514b7
disk_revision=228762f8316e119984ef0cc43e94f04ee58df2248d913f7236f3b9d66f8c7026
```

Connector hiện không phải blocker số một:

```text
connector_state=CURRENT_COMPATIBLE_ACKNOWLEDGED
connector_current_sha=c244ed297f707f9df48c1e5d6c7e204693f281a755c2e6344bde78e94abb8251
connector_ack_sha=c244ed297f707f9df48c1e5d6c7e204693f281a755c2e6344bde78e94abb8251
connector_refresh_required=false
connector_ack_pending=false
```

Nhưng `task_control` đang có defect contract/authority thực:

```text
Client schema:
  không nhận task_context_id

Server workspace binding:
  yêu cầu task_context_id hoặc run_id khi nhiều root có thể tồn tại

Kết quả:
  read-only observation có thể rơi vào deadlock schema/target binding
```

Kết luận:

> **Dự án hiện không thiếu capability; nó thiếu convergence, identity simplification, runtime/source alignment và một fast path đủ đơn giản để biến capability thành trusted outcome ổn định.**

---

## 0.3. Quyết định chiến lược

Trong giai đoạn hiện tại:

1. **Không mở rộng public tool surface.** Giữ smart-v3 8 tools.
2. **Không thêm orchestration object mới** nếu chưa chứng minh giảm TTPR/rework/false closure.
3. **Không merge toàn bộ upstream** `yyjeqhc/webcodex` hoặc `xyTom/coding-tools-mcp`.
4. **Ưu tiên xóa/hợp nhất/chuẩn hóa state hiện có.**
5. **Port invariant, không port architecture nguyên khối.**
6. **Đóng Operational Convergence trước các feature lớn.**
7. Sau convergence mới triển khai context recovery, Skill runtime và distributed Runner theo từng lớp.

---

# 1. Product North Star và ranh giới sản phẩm

## 1.1. User job mà Coding Web phải giải

Một operator cần có khả năng nói:

```text
“Sửa lỗi này trong project X cho tôi.”
```

và hệ thống tự đảm bảo:

```text
1. hiểu đúng user problem;
2. chọn đúng workspace/project;
3. xác định đúng running/source/data truth;
4. dùng đúng executor;
5. không tranh write authority;
6. mutate đúng causal scope;
7. chạy oracle phù hợp;
8. không reuse proof trên source drift;
9. deployment/runtime generation thực sự nhận source mới;
10. observable behavior đúng;
11. user problem không bị false-close;
12. context có thể tiếp tục ở phiên khác mà không replay toàn bộ lịch sử.
```

Đây mới là sản phẩm.

RUN/WAVE, lane, lease, activation epoch, proof ID, checkpoint ID chỉ là implementation machinery phục vụ job đó.

---

## 1.2. Trusted Problem Resolution

Một problem chỉ được coi là trusted-resolved khi:

```text
A. User outcome đạt.
B. Governing invariants liên quan được thỏa.
C. Source/runtime/data state phù hợp với claim.
D. Technical proof có provenance đúng.
E. Không còn material counterevidence chưa giải thích.
F. Khi risk yêu cầu, falsification probe không bác được closure claim.
```

Điều này có nghĩa:

```text
unit test PASS
!=
user problem resolved
```

và:

```text
checkpoint accepted
!=
running app updated
```

và:

```text
running app updated
!=
observable user outcome correct
```

Cần giữ ba lớp claim tách biệt:

```text
SOURCE CORRECT
RUNTIME CURRENT
USER OUTCOME RESOLVED
```

---

## 1.3. Target operating experience

Ideal fast path:

```text
USER PROBLEM
    ↓
WORKSPACE SYNC
    ↓
PROBLEM CAPSULE
    ↓
LOCALIZE CAUSE
    ↓
ONE CANONICAL MUTATION PATH
    ↓
FOCUSED PROOF
    ↓
RUNTIME CURRENT
    ↓
OUTCOME CHECK
    ↓
TRUSTED RESOLUTION
```

Không nên là:

```text
USER PROBLEM
→ RUN
→ WAVE
→ recovery object
→ task-context object
→ hidden session
→ route object
→ candidate object
→ proof object
→ activation object
→ connector object
→ another RUN
→ another WAVE
→ user says still broken
```

---

# 2. Current architecture: cái đã đạt được

## 2.1. Workspace/endpoint identity

Runtime live đã expose:

```text
endpoint_id
workspace_id
workspace_generation
device_instance_id
process_instance_id
server_instance_id
activation_epoch_id
```

Đây là nền tảng tốt cho distributed execution và stale-process fencing.

Điểm mạnh:

- workspace không chỉ còn là path string;
- process replacement có identity riêng;
- endpoint có route key;
- workspace generation có thể dùng để chặn stale writes;
- runtime/source fingerprint có thể dùng để bảo vệ proof reuse.

Điểm còn thiếu:

- authority hierarchy chưa đủ đơn giản;
- một số client/server path vẫn hiểu target binding khác nhau;
- operator UI/runtime/source chưa luôn hội tụ cùng generation.

---

## 2.2. Model-facing surface

Smart-v3 hiện chỉ expose 8 tools. Đây là một thành công kiến trúc đáng giữ.

Target lâu dài:

```text
workspace_context
agent_workflow
exec_command
command_control
task_control
document_workflow
view_image
request_permissions
```

Các capability phía sau như:

```text
Codex lanes
routing
proof
LSP
Skill store
context recovery
Runner lifecycle
problem lineage
```

không nên mặc định trở thành public tools mới.

---

## 2.3. EOCL và truthful proof

EOCL giải đúng một lớp vấn đề thật:

- write ownership;
- lease/fencing;
- explicit REPLAN;
- exact proof lineage;
- acceptance owner;
- base/worktree drift;
- deterministic evidence;
- no silent topology change.

EOCL phải giữ.

Nhưng phải thay đổi vai trò:

> **EOCL là authority/concurrency mechanism cho work có material risk, không phải ceremony bắt buộc cho mọi thao tác nhỏ.**

Fast path phải được ưu tiên cho bounded work có oracle mạnh.

---

## 2.4. Problem Resolution Lineage

PRL là khác biệt chiến lược của Codex-web so với coding runtimes thông thường.

Nó giúp tách:

```text
Problem Revision
≠ RUN
≠ WAVE
≠ proof
≠ deployment
```

Đây là hướng đúng vì economics thật nằm ở user problem, không nằm ở execution unit.

Tuy nhiên PRL chỉ có giá trị nếu:

- không biến thành thêm một orchestration state machine nặng;
- không lưu raw reasoning/transcript;
- không tự suy user outcome từ technical proof;
- không buộc task nhỏ phải đi qua ceremony dài;
- tạo được compact context capsule dùng thật cho continuation.

---

# 3. Current reality: các gap phải đóng

# 3.1. Gap A — Runtime/source divergence

Hiện tại:

```text
DEV_UI state=STALE
running_revision != disk_revision
update_pending=true
```

Đây là blocker mức P0.

Vì nếu source/test đã đúng nhưng runtime vẫn cũ thì:

```text
source fix PASS
→ running app stale
→ user still sees bug
→ diagnosis incorrectly reopens code problem
→ duplicate fixes
→ control-plane noise
→ TTPR tăng
```

### Required invariant

```text
When UI/runtime claims CURRENT:
  running_revision == intended_disk_revision
  runtime source identity == proof source identity when closure depends on runtime
```

### Exit criteria

- `dev:status state=CURRENT`;
- `update_pending=false`;
- no ambiguous running/disk source identity;
- UI displays same current generation as runtime authority;
- stale process cannot report CURRENT after replacement.

---

# 3.2. Gap B — `task_control` contract/target binding mismatch

Observed live defect:

```text
client schema rejects task_context_id
server workspace authority requires task_context_id or run_id
```

### Why this matters

`task_control` is a core authority surface. Nếu surface chính không thể bind workspace rõ ràng, các feature ở trên nó đều có nguy cơ:

- wrong target;
- stale target;
- hidden inference;
- manual workaround;
- repeated RUN creation chỉ để lấy target identity;
- raw protocol temptation.

### Required design

Một trong hai hướng phải được chọn và enforce end-to-end:

#### Option A — task_control receives explicit task_context_id

```text
workspace_context
→ task_context_id
→ task_control(task_context_id=...)
```

#### Option B — task_control only accepts run_id, and run_id always carries immutable workspace binding

```text
workspace_context
→ task start
→ run_id(workspace-bound)
→ task_control(run_id=...)
```

Không được tồn tại trạng thái:

```text
client cannot send field
AND
server requires field
```

### Preferred direction

Cho read-only/get/observation path, **explicit task context** phù hợp hơn vì không nên tạo RUN chỉ để đọc authority state.

Cho mutation/acceptance path, `run_id + wave_id` có thể là canonical execution authority.

---

# 3.3. Gap C — 71 unresolved stale orchestration runs

Live runtime:

```text
stale_orchestration_runs=71
unresolved_stale_orchestration_runs=71
task_orchestration_projection_reconciled=false
```

Không được chỉ “xóa cho sạch”.

Cần phân loại:

```text
1. terminal-but-unreconciled
2. lost controller
3. stale lease
4. superseded source
5. pre-write abandoned
6. proof completed but acceptance missing
7. runtime/restart interruption
8. corrupted/inconsistent state
```

Mỗi class phải có canonical authority path:

```text
reconcile
abort
checkpoint restore
mark superseded
require human review
```

### Exit criteria

```text
unresolved_stale_orchestration_runs = 0
projection_reconciled = true
no stale lease grants write authority
no stale run appears active in UI
```

### Important

Nếu hệ thống luôn tiếp tục sản sinh stale runs nhanh hơn khả năng reconcile thì phải sửa lifecycle semantics trước khi cleanup lịch sử.

---

# 3.4. Gap D — Operational files contaminate source worktree

Worktree hiện chứa nhiều operational state:

```text
.coding-tools/orchestration/ledger.sqlite3
.coding-tools/performance.json
.coding-tools/evaluation/*.jsonl
.coding-tools/task-contexts/*.json
.coding-tools/orchestration/reports/*
```

cùng với source modifications.

Điều này làm khó:

- exact source fingerprint;
- review;
- clean baseline;
- accepted checkpoint;
- Git status UX;
- proof reuse;
- upstream comparison.

### Target

Tách rõ:

```text
REPOSITORY SOURCE STATE
vs
LOCAL RUNTIME STATE
vs
DURABLE AUDIT STATE
vs
GENERATED REPORTS
```

Có thể vẫn đặt dưới `.coding-tools`, nhưng Git policy phải nhất quán:

```text
tracked canonical config/spec
untracked runtime state
ignored transient files
immutable exported evidence only when explicitly promoted
```

Không để runtime mutation khiến repository luôn dirty nếu file đó không phải source artifact.

---

# 3.5. Gap E — UI và control plane còn coupled quá mạnh

Current symptoms đã từng xuất hiện:

- UI lag/đơ khi system đang xử lý;
- dashboard không đo được live metrics đáng tin;
- refresh/recovery ảnh hưởng render;
- source/runtime mismatch khó nhìn.

### Target architecture

UI phải trở thành **read model**:

```text
runtime events
    ↓
incremental projection
    ↓
immutable/bounded snapshot
    ↓
IPC
    ↓
UI render
```

Mutation đi đường khác:

```text
UI command
    ↓
runtime handler
    ↓
durable state/event
    ↓
projection update
    ↓
new snapshot
```

Không để render path trực tiếp trigger:

```text
git scan
filesystem scan
SQLite aggregation
network health loop
full task ledger reconstruction
```

### Required performance metrics

- UI event-loop lag p50/p95/p99;
- IPC roundtrip p50/p95;
- snapshot build time;
- snapshot size;
- render commit time;
- dashboard refresh latency;
- dropped/coalesced update count;
- stale snapshot age.

---

# 4. Upstream reference model

# 4.1. `xyTom/coding-tools-mcp` — Execution Kernel reference

Repository:

```text
https://github.com/xyTom/coding-tools-mcp
```

Điểm đáng học:

- model-neutral coding runtime;
- stable tool catalog;
- bounded output/context economy;
- one canonical direct mutation primitive;
- workspace-bound safety;
- permission modes;
- explicit retryability/error categories;
- stateless MCP support;
- no attempt to own model loop/orchestration.

### Principle to adopt

```text
Small stable model-facing surface
+ deterministic execution semantics
+ truthful annotations
+ bounded results
+ canonical mutation path
```

### Không nên copy nguyên

- 18 tools không phù hợp với smart-v3 abstraction hiện tại;
- single-workspace trust-domain assumptions không đủ cho multi-endpoint future;
- Windows execution limitations không phù hợp target;
- runtime này không giải problem semantics/acceptance/routing.

### Decision

**Adopt kernel discipline, not product architecture.**

---

# 4.2. `yyjeqhc/webcodex` — Distributed Runtime reference

Repository:

```text
https://github.com/yyjeqhc/webcodex
```

Điểm đáng học:

```text
AI Client
  ↓
Server
  ↓
Runner
  ↓
Registered Project
```

Runner gần repository là execution trust boundary.

Server sở hữu:

- identity/policy;
- routing;
- durable Task/Job metadata;
- remote project registry;
- recovery semantics.

Runner sở hữu:

- actual filesystem;
- Git;
- shell/process;
- project execution.

### Strategic fit

Rất phù hợp mục tiêu dài hạn:

```text
ChatGPT web
→ Coding Web server/control plane
→ Runner trên máy A
→ repo A

ChatGPT web
→ Coding Web server/control plane
→ Runner trên máy B
→ repo B
```

Host server không cần clone tất cả source.

---

# 4.3. WebCodex PR #200 — Explicit Session targeting

Upstream đã xóa:

```text
bind_current
new_session
allow_cross_project_session
implicit current-binding fallback
```

và buộc explicit target.

Đây là một reference cực kỳ phù hợp với Codex-web.

### Principle to port

```text
Never infer authority from ambient state when exact identity is available.
```

Áp dụng cho:

- workspace;
- execution target;
- writer;
- proof;
- acceptance;
- runtime generation;
- problem revision.

---

# 4.4. WebCodex PR #202 — Assignment fencing

Pattern:

```text
READ current assignment
→ receive exact assignment_fence
→ COMPLETE(expected_assignment_fence)
```

Stale assignment:

```text
zero mutation
```

### Port concept

Mọi write quan trọng nên có expected revision/fence khi có stale-risk:

```text
workspace generation
write lease
acceptance state
activation epoch
problem revision
checkpoint transition
model assignment
```

---

# 4.5. WebCodex PR #201 — Context recovery + Skill runtime

Phần phù hợp:

### Context recovery

Khi context ACK missing/invalid/future:

```text
DO NOT assume revision zero
DO NOT replay entire history
RETURN compact current handoff
```

### Skill runtime

- immutable revisions;
- project-scoped skills;
- operator-installed skills;
- CAS fencing;
- replay-safe install/activation;
- exact Runner instance/capability binding.

### Decision

**Phù hợp nhưng chỉ làm sau P0/P1 convergence.**

Context recovery phải thay thế context replay, không tạo thêm một state machine nặng.

Skill store phải cung cấp knowledge/procedure, không được trở thành authority plane mới.

---

# 5. Target architecture

Coding Web nên được chuẩn hóa thành 4 lớp.

```text
┌──────────────────────────────────────────────────────────────┐
│ L3 — OPERATOR / UX                                           │
│ Electron UI · Dashboard · Health · Human approval            │
│                                                              │
│ Chỉ command + projection. Không sở hữu business authority.   │
└─────────────────────────────┬────────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────────┐
│ L2 — TRUSTED RESOLUTION PLANE                 [CODEX-WEB]    │
│                                                              │
│ Problem / Problem Revision                                   │
│ User intent / business semantics                             │
│ Resolution Envelope                                          │
│ Risk / permission policy                                     │
│ Executor routing                                             │
│ Evidence lineage                                             │
│ Acceptance / checkpoint                                      │
│ TTPR / false closure / reopen measurement                    │
└─────────────────────────────┬────────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────────┐
│ L1 — DISTRIBUTED RUNTIME FABRIC              [WEBCODEX-LIKE] │
│                                                              │
│ Endpoint / Runner                                            │
│ Workspace / Project identity                                 │
│ Task / Operation                                             │
│ Durable Jobs                                                 │
│ Context recovery                                             │
│ Skill store                                                  │
│ Revisions / fences                                           │
│ Remote-machine connectivity                                  │
└─────────────────────────────┬────────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────────┐
│ L0 — EXECUTION KERNEL                    [CODING-TOOLS STYLE]│
│                                                              │
│ read/search                                                   │
│ edit/patch                                                    │
│ Git                                                           │
│ command/PTTY                                                  │
│ test/build                                                    │
│ bounded result                                                │
│ permission enforcement                                       │
│ process/OS containment                                       │
└──────────────────────────────────────────────────────────────┘
```

---

# 6. Canonical identity model

Mỗi câu hỏi chỉ có một authority.

| Concern | Canonical identity / authority |
|---|---|
| Machine endpoint | `endpoint_id` |
| Live process | `process_instance_id` / instance fence |
| Workspace | `workspace_id + workspace_generation` |
| User problem | `problem_id + problem_revision` |
| Execution intent | `task_id` hoặc canonical task identity |
| Concrete process/job | `operation_id` / `job_id` |
| Mutation authority | current write lease/fence |
| Source state | Git HEAD + worktree fingerprint |
| Runtime generation | running revision/generation identity |
| Evidence | proof ID + source/runtime fingerprints |
| Accepted technical state | checkpoint ID |
| Context continuation | context capsule revision; **không cấp authority** |

## 6.1. Demote các identity phụ

### `task_context_id`

Vai trò:

```text
request/application-state continuation handle
```

Không nên trở thành business authority.

### RUN/WAVE

Vai trò:

```text
execution coordination/audit units
```

Không phải user-facing problem identity.

### Session/lane

Vai trò:

```text
collaboration/executor continuity
```

Không tự cấp write authority.

### activation_epoch

Vai trò:

```text
runtime replacement/recovery authority
```

Không phải project-work identity.

---

# 7. Feature/adoption decision matrix

| Item | Necessity | Strategic fit | Timing | Decision |
|---|---:|---:|---|---|
| Fix `task_control` target/schema contract | Critical | Critical | P0 | **DO NOW** |
| Reconcile 71 stale runs | Critical | Critical | P0 | **DO NOW** |
| Runtime/disk revision convergence | Critical | Critical | P0 | **DO NOW** |
| UI read-model/snapshot architecture | Critical | Very high | P0 | **DO NOW** |
| Separate operational state from source Git state | Critical | Very high | P0 | **DO NOW** |
| Stable 8-tool surface | Critical | Very high | continuous | **KEEP** |
| Typed error/retryability/next-action | High | Very high | P1 | **HARDEN** |
| Explicit workspace/authority identity | High | Very high | P1 | **HARDEN** |
| Expected-revision/fence semantics | High | Very high | P1 | **PORT PRINCIPLE** |
| Remove implicit target fallback | High | Very high | P1 | **PORT PRINCIPLE** |
| Compact context recovery | High | Very high | P2 | **IMPLEMENT** |
| Immutable Skill revisions | High | High | P2 | **IMPLEMENT BOUNDED** |
| Project/operator Skill scopes | Medium-high | High | P2 | **IMPLEMENT BOUNDED** |
| Windows persistent shell | Medium-high | High | P2/P3 | **EVALUATE/PORT** |
| Distributed Runner | High long-term | Very high | P3 | **IMPLEMENT AFTER CONVERGENCE** |
| Durable MCP Task protocol | Medium | Medium-high | P3 | **BENCHMARK FIRST** |
| CodingAgentRun as second orchestrator | Low | Low | none | **REJECT WHOLESALE** |
| New Session authority plane | Low | Low | none | **REJECT** |
| More public MCP tools | Very low | Low | none | **REJECT BY DEFAULT** |
| New RUN/WAVE states | Very low | Low | none | **REJECT BY DEFAULT** |
| Full WebCodex merge/rebase | No | Low | none | **DO NOT DO** |
| Full xyTom runtime replacement | No | Low | none | **DO NOT DO** |

---

# 8. Completion roadmap

# P0 — OPERATIONAL CONVERGENCE

## Objective

Đưa hệ thống từ “feature-rich but operationally divergent” sang một baseline duy nhất, measurable, current và có thể tin cậy.

## P0.1 — Fix `task_control` contract

Tasks:

1. Chọn canonical target semantics cho read-only control calls.
2. Đồng bộ client schema và server handler.
3. Add regression:
   - multiple workspace roots;
   - explicit task context;
   - missing target;
   - stale target;
   - read-only observation;
   - run-bound mutation.
4. Cấm hidden ambient fallback.
5. `server/discover/tools/list` contract phải phản ánh đúng runtime handler.

Exit:

```text
workspace_context → task_control observation works
without creating RUN/WAVE
and without raw protocol workaround
```

---

## P0.2 — Stale orchestration reconciliation

Tasks:

1. Inventory 71 stale runs.
2. Classify by stale cause.
3. Add/verify canonical reconciliation transitions.
4. Reconcile each record through official authority path.
5. Verify stale leases cannot mutate.
6. Rebuild task projection.
7. Ensure startup performs bounded idempotent reconciliation.

Exit:

```text
stale_orchestration_runs = 0
unresolved_stale_orchestration_runs = 0
task_orchestration_projection_reconciled = true
```

---

## P0.3 — Source/runtime convergence

Tasks:

1. Define `disk_revision` algorithm.
2. Define `running_revision` algorithm.
3. Ensure replacement runtime reports exact loaded revision.
4. Ensure stale Electron/Recovery Host process cannot publish current state.
5. Define `CURRENT`, `STALE`, `UPDATING`, `FAILED` unambiguously.
6. UI displays exact generation/revision.
7. Acceptance requiring runtime proof must bind runtime revision.

Exit:

```text
state=CURRENT
update_pending=false
running_revision == intended disk revision
```

---

## P0.4 — Operational state hygiene

Tasks:

1. Classify every `.coding-tools` file:
   - source/config;
   - runtime state;
   - durable audit;
   - generated report;
   - temporary.
2. Apply Git policy.
3. Stop routine runtime activity from dirtying source worktree unnecessarily.
4. Preserve intentional immutable evidence separately.
5. Make source fingerprint exclude non-source operational churn when semantically correct.

Exit:

```text
normal runtime use does not make source appear modified
unless actual source/config changed
```

---

## P0.5 — UI read-model and latency closure

Tasks:

1. Trace event-loop blocking.
2. Trace IPC calls by duration/size.
3. Remove synchronous expensive aggregation from render path.
4. Build bounded snapshot projection.
5. Coalesce high-frequency telemetry updates.
6. Virtualize large tables/logs.
7. Incremental dashboard metrics.
8. Add performance budgets.

Suggested initial budgets:

```text
UI event-loop p95              < 50 ms
normal IPC p95                 < 100 ms
snapshot apply p95             < 50 ms
operator action feedback       < 150 ms perceived start
full dashboard refresh         < 500 ms for cached/read-model data
no unbounded synchronous ledger scan on render path
```

Budgets phải được hiệu chỉnh bằng benchmark máy thực, không coi số trên là dogma.

---

## P0.6 — Immutable baseline

P0 kết thúc bằng một accepted baseline:

```text
Git source identity
runtime revision
workspace identity
contract SHA
proof bundle
UI performance baseline
stale-run count=0
projection reconciled=true
```

Không bắt đầu architectural expansion lớn trước baseline này.

---

# P1 — IDENTITY AND AUTHORITY SIMPLIFICATION

## Objective

Giảm số nơi có thể “đoán” target/authority.

## Tasks

### P1.1 Explicit targeting

- workspace explicit;
- project explicit;
- execution target explicit;
- no implicit current binding for authority decisions.

### P1.2 Revision fences

Add expected revision/fence where stale mutation is material:

```text
workspace generation
write lease
problem revision
activation epoch
assignment
acceptance transition
checkpoint transition
```

### P1.3 One authority per concern

Audit all state IDs and produce:

```text
AUTHORITY_MATRIX.md
```

Every ID must answer:

- what fact does it identify?
- can it grant authority?
- who creates it?
- who invalidates it?
- can it survive restart?
- can it be inferred?

### P1.4 Typed recovery

Every important failure returns:

```yaml
code:
category:
retryable:
current_effect_committed:
next_action:
required_identity:
```

Do not make model infer whether retry is safe.

---

# P2 — CONTEXT RECOVERY AND SKILLS

## Objective

Giải quyết long-context continuity mà không replay transcript và không tạo authority plane mới.

## P2.1 Problem Context Capsule

Minimal capsule:

```yaml
problem:
  problem_id:
  revision:
  objective:
  acceptance_criteria:
  protected_invariants:

workspace:
  endpoint_id:
  workspace_id:
  generation:
  source_head:
  worktree_fp:

current_frame:
  observation:
  boundary:
  hypotheses:
  counterevidence:

execution:
  active_task:
  active_authority:
  latest_checkpoint:

proof:
  valid:
  invalidated:

open_conditions:
  - ...

next_causal_action:
  ...
```

Rules:

- bounded;
- deterministic projection where possible;
- no chain-of-thought;
- no raw transcript;
- no secret leakage;
- stale capsule clearly rejected/refreshed;
- context identity cannot grant mutation authority.

---

## P2.2 Context recovery

Fresh ChatWeb flow:

```text
workspace_context
→ recover compact problem capsule
→ verify workspace/source freshness
→ continue
```

Không:

```text
re-read full conversation
re-scan entire repo
reconstruct state from old reports
```

---

## P2.3 Skill runtime

Implement only capabilities with measurable value:

```text
project skill discovery/read
operator skill discovery/read
immutable revision
active revision pointer
CAS update
rollback to known revision
bounded metadata
```

Skill authority rule:

```text
Skill may recommend workflow.
Skill may not grant permissions.
Skill may not override workspace authority.
Skill may not bypass EOCL/write lease.
Skill may not declare acceptance.
```

---

# P3 — DISTRIBUTED RUNNER / MULTI-MACHINE

## Objective

Cho phép control/model ở một nơi, execution tại đúng máy chứa workspace.

Target:

```text
                 Coding Web Server
                /       |        \
               /        |         \
      Runner Windows  Runner Linux  Runner Mac
           |               |           |
       Workspace A      Workspace B Workspace C
```

## Required invariants

### Device identity

```text
endpoint_id = stable logical endpoint
process_instance_id = current live runner process
```

Second process with stale/replaced instance cannot continue authoritative work.

### Workspace registry

Runner registers allowed workspace roots explicitly.

Server does not invent/discover arbitrary remote filesystem paths.

### Execution ownership

Actual file/shell/Git operations execute on Runner that owns workspace.

### Recovery

Disconnect:

```text
liveness loss != automatic work loss
```

But process restart must not claim child processes it cannot prove still owns.

### Security

- workspace-root containment;
- per-endpoint policy;
- bounded environment;
- secrets filtering;
- process lifecycle isolation;
- explicit remote authorization.

---

# P4 — TRUSTED RESOLUTION AUTOMATION

## Objective

Sau khi runtime execution ổn định, chuyển lợi thế riêng của Codex-web thành product value.

## First-class objects

```text
Problem Revision
Problem Frame
Observation
Counterevidence
Technical Attempt
Proof
Runtime Verification
Resolution Claim
Trusted Resolution
Reopen
```

## Metrics

Tier 1 — product:

```text
TTPR p50/p90
First-Pass Trusted Resolution Rate
Trusted Resolution Rate
False Closure Rate
Same-problem Reopen Rate
User correction turns/problem
```

Tier 2 — learning:

```text
Problem Boundary Error Rate
Frame Revisions / Problem
Wrong-target incidence
Same-frame retry after counterevidence
Underframing-attributable work
```

Tier 3 — execution:

```text
replan rate
proof rerun rate
patch first-attempt success
workspace/source drift incidence
runtime stale incidence
control-plane wait
UI/IPC latency
```

---

# 9. Fast path vs material orchestration

## 9.1. Fast path

Dùng khi:

- localized problem;
- exact workspace;
- no competing writer;
- strong oracle;
- low risk;
- causal patch small.

Flow:

```text
workspace sync
→ localize
→ change
→ focused validate
→ accept
```

RUN/WAVE machinery có thể tồn tại bên dưới nhưng không được tạo thêm operator ceremony.

---

## 9.2. Material path

Dùng khi:

- multi-writer;
- long-running;
- high integration width;
- risky migration;
- auth/privacy/financial semantics;
- multiple independent workstreams;
- distributed runner;
- handoff required.

Flow:

```text
Problem
→ Task
→ EOCL coordination
→ bounded waves/lanes
→ proof
→ acceptance
→ runtime verification
→ Resolution Claim
```

---

# 10. What to delete or collapse

Dự án cần một explicit **subtraction backlog**.

Mỗi mechanism phải trả lời:

```text
Does it reduce TTPR?
Does it reduce false closure?
Does it reduce rework?
Does it reduce unsafe mutation?
Does it reduce operator intervention?
Does it provide authority that no existing mechanism already provides?
```

Nếu tất cả là `no/unknown`, candidate để:

```text
remove
collapse
make internal
make diagnostic-only
defer
```

Priority audit candidates:

1. duplicate workspace/session target inference;
2. duplicate task/run/context identity roles;
3. UI-side runtime authority assumptions;
4. recovery scripts that duplicate canonical supervisor behavior;
5. reports generated automatically into source-visible worktree;
6. overlapping restart/recovery state machines;
7. model route state not used in acceptance decisions;
8. telemetry fields with no demonstrated decision value;
9. proof cache mechanisms with negligible hit/ROI;
10. LSP paths that remain effectively unused unless a clear workload justifies them.

---

# 11. Architecture admission gate for every new feature

Trước khi thêm feature, PR/decision phải trả lời 10 câu hỏi:

```text
1. User problem nào feature này giải?
2. Nó giảm TTPR ở stage nào?
3. Existing mechanism nào chưa đủ?
4. Có tạo source-of-truth thứ hai không?
5. Có thêm identity/authority state không?
6. Có tăng public tool/context surface không?
7. Failure/recovery semantics là gì?
8. Nó được benchmark trên representative natural workload nào?
9. Có deletion/collapse opportunity tương ứng không?
10. Exit metric nào chứng minh feature có ROI?
```

Nếu không trả lời được 1–3 hoặc 8–10:

```text
DEFER
```

---

# 12. Upstream adoption procedure

Không cherry-pick feature chỉ vì upstream mới hơn.

Mỗi upstream change phải đi qua:

```text
UPSTREAM CHANGE
      ↓
IDENTIFY INVARIANT
      ↓
MAP TO CURRENT GAP
      ↓
CHECK EXISTING LOCAL MECHANISM
      ↓
PORT / ADAPT / REJECT
      ↓
REPRESENTATIVE PROOF
      ↓
MEASURE TTPR / REWORK EFFECT
```

Adoption labels:

```text
PORT_CODE
PORT_INVARIANT
PORT_TEST
PORT_DOC_PATTERN
DESIGN_REFERENCE_ONLY
REJECT_OVERLAP
DEFER_NO_ROI
```

---

# 13. Recommended immediate implementation order

## Wave A — Contract and convergence

```text
A1 task_control target/schema
A2 stale-run reconciliation
A3 runtime/disk currentness
A4 operational-state Git hygiene
A5 immutable accepted baseline
```

Không chạy các phần này như năm project độc lập. Chúng là một convergence chain.

---

## Wave B — UI performance/read model

```text
B1 event-loop/IPC instrumentation
B2 snapshot projection
B3 remove synchronous heavyweight render dependencies
B4 dashboard live metrics
B5 performance acceptance gate
```

---

## Wave C — Identity simplification

```text
C1 authority matrix
C2 remove implicit fallback
C3 revision fences
C4 typed recovery contract
C5 tests for stale/ambiguous target
```

---

## Wave D — Context/Skills

```text
D1 problem capsule
D2 context recovery
D3 immutable skill revisions
D4 bounded project/operator skill scopes
```

---

## Wave E — Distributed Runner

```text
E1 endpoint registry
E2 runner process fencing
E3 workspace registry
E4 remote command/job ownership
E5 disconnect/reconnect recovery
E6 Windows execution hardening
```

---

# 14. Definition of Done for “Coding Web core complete”

Không gọi core complete chỉ vì tests pass.

Core completion cần đồng thời:

## Runtime

```text
[ ] one canonical active runtime generation
[ ] running revision == intended deployed revision
[ ] stale process cannot claim authority
[ ] connector/tool contract current and usable
```

## Workspace/authority

```text
[ ] explicit workspace target everywhere authority matters
[ ] no client/server target schema deadlock
[ ] zero implicit cross-workspace authority fallback
[ ] write fence stale mutation = zero effect
```

## Orchestration

```text
[ ] stale_orchestration_runs = 0 or only explicitly exempted records
[ ] task projection reconciled
[ ] no orphan active lease
[ ] fast path does not require unnecessary ceremony
```

## Source/proof

```text
[ ] source worktree state distinguishable from runtime state
[ ] proof exact-source binding works
[ ] proof invalidation on drift works
[ ] accepted checkpoint immutable
```

## UI

```text
[ ] operator UI state=CURRENT on baseline
[ ] dashboard derives from bounded read model
[ ] no long synchronous control-plane scan on render
[ ] event-loop/IPC budgets pass
[ ] UI shows runtime/source mismatch explicitly
```

## Problem resolution

```text
[ ] Problem Revision distinct from RUN/WAVE
[ ] technical acceptance does not auto-equal trusted resolution
[ ] problem capsule can continue work across fresh context
[ ] false closure/reopen can be measured
```

## Natural workload

At least one representative HR problem phải chứng minh end-to-end:

```text
user reports real issue
→ problem contract captured
→ correct workspace/source
→ causal fix
→ proof
→ runtime current
→ UI/data outcome correct
→ no same-problem correction required in acceptance window
```

---

# 15. Stop conditions / anti-patterns

Dừng và re-evaluate nếu gặp:

```text
1. Feature requires another public MCP tool without strong reason.
2. New object duplicates authority of an existing object.
3. New recovery path bypasses canonical runtime supervisor.
4. UI creates its own workspace/runtime truth.
5. A RUN is created only to read state.
6. “Pass” is claimed while running generation is stale.
7. Technical proof is used as independent user-outcome evidence.
8. Same failed plan is retried without new evidence.
9. Whole upstream branch is merged to obtain one invariant.
10. More telemetry is added before existing telemetry changes decisions.
11. Context solution stores/replays raw transcript instead of compact state.
12. Skill can override security/authority.
13. Distributed Runner begins before single-host convergence is stable.
```

---

# 16. Evaluation scorecard

Đánh giá hiện tại theo 5 mức:

```text
0 = absent
1 = prototype
2 = functional but fragile
3 = operationally usable
4 = mature
5 = production-converged
```

| Dimension | Current assessment | Target |
|---|---:|---:|
| Basic repo execution | 4 | 5 |
| Model-facing tool surface | 4 | 5 |
| Workspace identity | 3.5 | 5 |
| Write authority/fencing | 3.5 | 5 |
| Proof/acceptance lineage | 4 | 5 |
| Runtime activation/recovery | 3 | 5 |
| Client/server contract convergence | 2.5 | 5 |
| Orchestration hygiene | 2 | 5 |
| Source/runtime currentness | 2.5 | 5 |
| UI responsiveness/read model | 2–3 | 5 |
| Long-context continuation | 2.5 | 5 |
| Skill runtime | 2–3 | 4.5 |
| Multi-machine runner | 1–2 | 4.5 |
| Trusted problem-resolution semantics | 3 | 5 |
| TTPR outcome measurement | 2–3 | 5 |

### Interpretation

Coding Web hiện ở trạng thái:

> **Advanced execution/control platform, but not yet a production-converged trusted-resolution system.**

Khoảng cách lớn nhất không nằm ở reasoning model hoặc số feature. Nó nằm ở:

```text
operational convergence
identity/authority simplification
runtime/source truth
UI projection/performance
problem-level outcome closure
```

---

# 17. Final recommendation

## 17.1. Giữ nguyên đích đến

Không đổi North Star.

```text
TTPR
Trusted Problem Resolution
```

là hướng phù hợp và có tính khác biệt so với upstream.

---

## 17.2. Không tiếp tục “feature-first”

Trong giai đoạn hiện tại:

```text
SUBTRACT / CONVERGE / SIMPLIFY
before
EXPAND
```

Ước tính chiến lược: phần lớn ROI ngắn hạn sẽ đến từ việc hợp nhất/xóa/chuẩn hóa state hiện có hơn là thêm capability mới.

---

## 17.3. Vai trò của hai upstream

### `xyTom/coding-tools-mcp`

Dùng làm reference cho:

```text
execution kernel discipline
stable contract
bounded context
canonical mutation
error/retry semantics
```

### `yyjeqhc/webcodex`

Dùng làm reference cho:

```text
distributed runner
explicit identity
revision fencing
context recovery
skill runtime
remote project topology
```

### Codex-web

Chỉ nên sở hữu phần khác biệt:

```text
user problem semantics
resolution contract
routing/authority integration
truthful evidence
acceptance
TTPR
false-closure prevention
```

---

# 18. One-line architecture doctrine

> **Keep the execution kernel small, make runtime identity explicit, keep authority fenced, project UI from immutable live state, recover context compactly, distribute execution through Runners only after single-host convergence, and optimize every architectural decision for Time to Trusted Problem Resolution rather than orchestration complexity.**

---

# 19. Implementation checklist for the next engineering cycle

```text
P0 — MUST CLOSE BEFORE EXPANSION
[ ] task_control schema/target binding
[ ] 71 stale orchestration runs reconciled
[ ] projection_reconciled=true
[ ] source/runtime revision converged
[ ] DEV_UI CURRENT
[ ] operational files separated from source truth
[ ] UI snapshot/read-model path
[ ] latency baseline and budgets
[ ] immutable accepted baseline

P1 — SIMPLIFY
[ ] authority matrix
[ ] explicit target only
[ ] expected-revision fences
[ ] typed retry/recovery contract
[ ] delete duplicate fallback mechanisms

P2 — CONTINUITY
[ ] problem context capsule
[ ] context recovery
[ ] immutable Skill revisions
[ ] project/operator Skill scopes

P3 — DISTRIBUTED EXECUTION
[ ] Runner identity
[ ] workspace registry
[ ] remote process/job ownership
[ ] reconnect/recovery semantics
[ ] Windows hardening

P4 — PRODUCT OUTCOME
[ ] TTPR dashboard
[ ] first-pass trusted resolution
[ ] false closure
[ ] reopen attribution
[ ] representative natural HR validation
```

---

# 20. Sources and reference points

Internal project doctrine:

```text
docs/research/260826_CODING_WEB_USER_PROBLEM_RESOLUTION_FIRST_METHODOLOGY_AND_STRATEGIC_DIRECTION.md
```

Upstream references:

```text
https://github.com/yyjeqhc/webcodex
https://github.com/xyTom/coding-tools-mcp
```

WebCodex reference areas evaluated:

```text
PR #200 — explicit Workflow Session targeting
PR #201 — explicit model context recovery and Skill runtime
PR #202 — assignment-fenced Session completion
```

Live evidence source:

```text
Coding-VP workspace_context
Coding-VP dev:status
Coding-VP task_control contract validation
2026-08-28
```

---

**Decision status:** `RECOMMENDED FOR ARCHITECTURE REVIEW AND P0 IMPLEMENTATION`  
**Next critical action:** Đóng `Operational Convergence` trước khi tiếp tục upstream feature adoption quy mô lớn.

---

# 21. Execution checkpoint — 2026-08-28

Đây là phụ lục bằng chứng của lần đối chiếu repository hiện tại; nó không sửa
đổi các snapshot lịch sử ở trên và không biến source/focused proof thành live,
delivery hoặc production proof.

## 21.1. Repository and source proof

```text
workspace                              E:\DEV\Codex-web
branch                                main
HEAD                                  148de18795787e820ef1bc51d0f2591052d24238
worktree                              DIRTY (concurrent source and .coding-tools WIP preserved)
Node focused lifecycle/recovery/UI    134 passed, 0 failed
Python execution-hub proof             10 passed, 0 failed
Multi-workspace/session isolation      19 passed, 0 failed
HTTP multi-workspace matrix            1 passed, 0 failed
MCP-2026 stateless HTTP                19 passed, 0 failed
module-size guard                      PASS after explicit bounded allowlist
git diff --check                       PASS
```

The allowlist entries are explicit and reasoned for the Revision-4
task-control/read-model/analytics bridge; they do not disable the guard or
permit unbounded growth. No unrelated WIP was reset, cleaned, restored or
staged by this checkpoint.

## 21.2. P0 status after current read-only recheck

```text
P0.1 task_control contract/binding       SOURCE + focused proof COMPLETE
P0.2 stale lifecycle/projection          BLOCKED: current census has live/unbound residue
P0.3 source/runtime convergence          OPEN: DEV_UI state=STALE, update_pending=true
P0.4 operational state policy            GOVERNED by AGENTS.md retention invariant; not split/untracked
P0.5 UI read-model mechanics              SOURCE + focused proof COMPLETE; live latency budget unmeasured
P0.6 immutable accepted baseline         NOT CREATED
```

The current `npm run dev:status` receipt is:

```text
state=STALE
running_revision=871ef6c777ddde3eb6ca8ba6c6a5f25b14c52c366db745ff8ac79ceee48514b7
disk_revision=228762f8316e119984ef0cc43e94f04ee58df2248d913f7236f3b9d66f8c7026
update_pending=true
connector_state=CURRENT_COMPATIBLE_ACKNOWLEDGED
connector_rediscovered=false
connector_refresh_required=false
connector_ack_pending=false
```

The immutable, query-only lifecycle census observed at
`2026-08-28T09:59:33.719Z` reports:

```text
schema_version                         11
physical snapshot SHA-256              2755b133c1c87a998c77aba4ae47126006f37b1fccc9bfd9a6f7acfbddf4e128
logical snapshot SHA-256                c98e62b1668af461cd9c9974f657197a0624b3245ff9f174727e46cc55293de5
ordinary active runs                    99
threshold stale candidates              84
awaiting acceptance                    9
managed job live-owned                 1
unbound live resource residue          1
projection classification              PROJECTION_DRIFT
mutated canonical ledger                false
```

The unbound managed job has no canonical `run_id`; it is therefore
`UNEXPLAINED_ACTIVE` until the owning controller/runtime supplies an exact
authority receipt. It must not be adopted, killed, force-released or
bulk-reconciled from this task. The `P0.2` exit criteria remain unproven:
`stale_orchestration_runs=0`, `unresolved_stale_orchestration_runs=0`, and
`task_orchestration_projection_reconciled=true`.

## 21.3. Exact next actions and gates

Repository-local implementation for the current P0 contract/read-model slice
is sufficiently proven by the focused checks above. The next causal actions
are external/authority-gated:

1. The owner of the unbound managed process must provide an exact current
   lifecycle/run binding, after which the supported census and exact-ID
   reconciliation path may be reconsidered.
2. An explicitly authorized controlled Recovery Host/full-clean refresh is
   required to load the source revision shown on disk; only then may
   `dev:status` be recaptured for `state=CURRENT` and
   `running_revision == disk_revision`.
3. A real current-process `tools/list` or `server/discover` receipt is still
   required before treating connector freshness as rediscovered, regardless
   of the compatible acknowledgement tuple.
4. A measured UI event-loop/IPC/read-model latency window and one immutable
   accepted baseline are still required. A natural HR problem with an
   independent outcome receipt remains a separate product-outcome gate.

No restart, process adoption, stale-run mutation, connector ACK, commit, push,
package, release, deployment, or production operation occurred in this
checkpoint.

## 21.4. Final concurrent-drift receipt

Một lần `npm run dev:status` ngay trước khi kết thúc wave cho thấy worktree đã
nhận thêm source WIP concurrent trong khi Electron process không được thay thế:

```text
state=STALE
running_revision=871ef6c777ddde3eb6ca8ba6c6a5f25b14c52c366db745ff8ac79ceee48514b7
disk_revision=1bc326442e0cb72383eab8c2ce2c9ed437fc8d58fd7665701547c8aa3b612dc5
update_pending=true
connector_state=CURRENT_COMPATIBLE_ACKNOWLEDGED
connector_rediscovered=false
connector_refresh_required=false
connector_ack_pending=false
```

Receipt này làm mất hiệu lực mọi suy luận rằng source hiện tại đã được loaded
vào process đang chạy; nó không phải lý do để tự động restart hoặc nhận process
foreign. Báo cáo giữ nguyên nguyên tắc: mỗi source drift cần một activation
operation được ủy quyền và một receipt mới trước khi đánh giá `CURRENT` hay
đóng immutable baseline.
