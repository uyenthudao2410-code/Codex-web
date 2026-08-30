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

## 22. P1 authority-matrix checkpoint — 2026-08-28

Đã hoàn tất artifact P1.3 ở mức source/documentation:
[`docs/AUTHORITY_MATRIX.md`](../AUTHORITY_MATRIX.md) liệt kê các identity hiện
đang có trong runtime (workspace/task/run/wave/lease/activation/process/device,
checkpoint/proof/problem/capsule/connector), nêu rõ identity nào được phép cấp
authority ở gate nào, ai tạo/vô hiệu hóa, khả năng sống qua restart, và vì sao
không được suy luận từ projection/UI/process proximity. Matrix dùng đúng
precedence hiện tại: implementation + focused tests là authority; report chỉ là
inventory có timestamp/HEAD.

Validation cho wave này:

```text
docs/AUTHORITY_MATRIX.md       added (bounded documentation artifact)
git diff --check               PASS
source/runtime/process state   unchanged by this wave
```

Artifact này đóng phần inventory P1.3 nhưng không tự đóng P0.2/P0.3/P0.6,
không biến `task_context_id`, capsule, proof hash hay connector hash thành
quyền mutation, và không cấp phép restart/adopt/kill/reconcile ledger,
commit/push/release/deploy. Các blocker runtime được giữ nguyên như receipt ở
§21: runtime hiện đang dừng/không fully ready, UI process stale so với disk,
connector chưa có current-process discovery receipt, lifecycle census còn cần
được xử lý qua supported authority trước khi tạo accepted baseline.

## 23. Fresh read-only lifecycle receipt — 2026-08-28T10:14:44Z

Một immutable Backup-API/query-only census mới đã chạy sau khi runtime hiện tại
đã dừng các process Coding MCP/Tunnel. Census không khởi tạo writer/runtime/
governor và xác nhận `mutated_canonical_ledger=false`:

```text
schema_version                         11
physical snapshot SHA-256              ace311839643334d19be0e2831ac9d30e1ee271228074c33427d1bb262230701
logical snapshot SHA-256                bb2908d50673b5746b55cca53f387255105d7cb520392385914dd340c3febd36
ordinary active runs                    102
threshold stale candidates              88
awaiting acceptance                    10
grace-period inactive                   4
managed job residues (not live)         2
unbound live resource residues          0
unexplained active runs                 0
projection classification               PROJECTION_DRIFT
projection context count                289
projection missing relevant runs       3
mutated canonical ledger                false
```

Ba run còn thiếu contextual projection là các exact tuple sau; chúng không
được tự tạo hoặc gán lại vì census chỉ quan sát:

```text
7f852fd7a0fa4c17838eedb41826e706 / b4841039b1304780b4b421621b0b28ed / PREFLIGHT
a572b052953f43df92919ebc0bf923af / d9c44485e9404b339af43be2002d1336 / PREFLIGHT
e917aad443df43cba0540cac77805759 / 56802762c9644fb692ed20dfea0c414e / PREFLIGHT
```

Receipt này làm rõ blocker hiện tại: unbound live sidecar residue đã biến mất
theo quan sát (hai managed-job rows còn lại đều `NOT_RUNNING`), nhưng P0.2 vẫn
chưa đạt vì 88 stale candidates chưa qua supported reconciliation và projection
vẫn thiếu ba binding. P0.3 cũng chưa đạt: `npm run dev:status` tiếp tục báo
`state=STALE`, `update_pending=true`, còn runtime snapshot báo MCP/Tunnel
stopped và `connector_state=UNAVAILABLE`. Chỉ owner có authority mới được
reconcile các run/rows này hoặc thực hiện full-clean activation; không có mutation
hay restart nào được thực hiện trong wave này.

## 24. Completion-goal checkpoint — 2026-08-28T10:54:54Z

Đây là receipt hiện tại sau khi tiếp tục goal với quyền thao tác repository và
runtime có kiểm soát. Các thay đổi source đúng phạm vi P0.5 đã hiện diện trên
worktree hiện tại, gồm:

```text
renderer/control-center.js
  Overview refresh dùng lightweightSnapshot + liveOrchestration cho mọi đường
  force/manual/initial/visibility/dashboard-request; không còn force full API
  trên Overview.
renderer/dashboard.js
  canonicalControllerUsageState, canonicalOperationsAnalytics và
  canonicalMeasuredUsage chỉ đọc analyticsSnapshot.
electron/main.js
  PANEL_ANALYTICS_TIMEOUT_MS = 10000.
mcp_http_handler.py
  /__control/orchestration/analytics trả generated_at/window_days=7 và truyền
  cùng generated_at vào usage_analytics(now=...) và operations_analytics(now=...).
```

Focused proof thực tế trên cùng worktree:

```text
python -m pytest tests/test_execution_hub.py -q                  PASS 11
python -m pytest tests/test_lifecycle_census.py tests/test_projection_rebuild.py -q
                                                                  PASS 18 (+8 subtests)
node --test tests/dashboard-analytics.test.js tests/control-center-manager.test.js
          tests/runtime-lifecycle.test.js                         PASS 99
node --test tests/recovery-bootstrap.test.js ...                  PASS (included in prior 116-test run)
git diff --check                                                PASS
```

Test HTTP analytics còn xác nhận hai helper nhận đúng cùng một timestamp
`generated_at`; endpoint không thực hiện reconciliation. Đây là source/focused
proof, chưa phải packaged/released proof.

Runtime đã từng đạt một epoch `READY/open` sau census sạch, với process/server
identity mới và revision MCP/UI khớp disk. Sau đó source tiếp tục drift bởi
worktree song song, vì vậy receipt đó không được tái sử dụng. Một full-clean
refresh mới đã được gọi qua `npm run dev:refresh`; Recovery Host từ chối khi
census lại xuất hiện work đang tiến hành song song. Census immutable gần nhất:

```text
physical snapshot SHA-256              f4d828fcdd8a37b1a415a96dab737205f082bdf8399bc8cd39d9d7f3a4c9fb44
logical snapshot SHA-256                7a18719f3bed9c0d655d1205b96e520e0807b9185833463f5abfcc990a3358fd
integrity / foreign keys                ok / 0
ordinary active runs                    103
awaiting acceptance                     13
grace-period inactive                   1
threshold stale candidates              89
managed job residue                     1 (identity NOT_RUNNING; unbound)
unbound live resources                  0
unexplained active runs                 0
projection classification               PROJECTION_DRIFT
projection context count                297
projection missing relevant runs       1
missing exact run                       61087e690a0544628b9657a1719e2b6b
missing exact wave/state                 7dadb4e0f1ca4db3bc53340f04ad1edf / PREFLIGHT
```

Run `61087…` được tạo bởi một task song song và đang trong grace period; không
được tự gán contextual projection, accept/reject/stop, hay adopt managed job.
`npm run dev:status` hiện tại là `MISSING` (host available, runtime process
không còn được chứng minh), do đó P0.3/P0.6 vẫn mở. Connector probe đã được
thực hiện trước đó trên current process (`server/discover`, HTTP 200, token
không lộ ra), nhưng vì source/runtime drift và refresh chưa đạt current epoch
mới nên không dùng nó để đóng connector gate hiện tại.

Trạng thái gate sau checkpoint này:

```text
P0.1 task_control contract/binding        SOURCE + focused proof COMPLETE
P0.2 lifecycle/projection convergence     OPEN / BLOCKED by concurrent PREFLIGHT + managed residue
P0.3 source/runtime convergence           OPEN / runtime MISSING after refused refresh
P0.4 operational evidence retention       GOVERNED; .coding-tools preserved
P0.5 UI read-model/analytics mechanics     SOURCE + focused proof COMPLETE
P0.6 immutable accepted baseline           NOT CREATED
P1.3 authority matrix                     SOURCE/documentation COMPLETE
P2/P3/P4 natural outcome, canary, delivery NOT PROVEN; no push/release/deploy occurred
```

Không có direct SQLite edit, process kill/adopt, bulk stale reconciliation,
commit, push, package, release hoặc deployment trong checkpoint này. Next
critical action là đợi task `61087…` và managed-job residue đi qua supported
lifecycle boundary, recapture one clean immutable census, rồi chạy lại
full-clean refresh trên exact current source. Chỉ sau `READY/open`, matching
running/disk revision, fresh current-process discovery và connector ACK hợp lệ
mới được tạo accepted baseline; không được suy luận natural HR outcome từ
technical proof.

## 25. Current completion-goal receipt — 2026-08-28T11:10:45Z

Receipt mới nhất sau khi thử tiếp tục activation trên đúng checkout hiện tại:

```text
HEAD                                      2cc0eefc7d881827ef44e4d1584d84bbd9e494b6
immutable census observed_at              2026-08-28T11:10:45.708Z
physical snapshot SHA-256                 0ee862fb511eff51c340cbac6a5b4d66e7d3ea8396609c28718bbc056272bc58
logical snapshot SHA-256                  c9a2e8f3cfa9452c0c9069f81922f4dd7bca84aa1df6b793c001cbc535fcdb02
integrity / foreign keys                  ok / 0
projection classification                 CONTEXTUAL_PROJECTIONS
projection missing relevant runs          0
unexplained active runs                   0
unbound live resources                    0
managed jobs                              0
awaiting acceptance                       13
active agent lanes                        1
lane owner                                run 54290b6f078c43bdabe921de358a5d3a
lane state                                ACCEPTING (task remains active)
```

`npm run dev:refresh` đã đi qua đường full-clean chính thức nhưng receipt
`recovery-host-bootstrap.full-clean-refresh-mtcuk6fz-595629e84fd8299eac04130f.result.json`
trả:

```text
state                                     failed
code                                      ORCHESTRATION_STATE_UNCERTAIN
message                                   Canonical ledger census refused stopped-runtime activation.
activation_epoch_id                       null
admission_open / fully_ready              false / false
```

Nguyên nhân được tái hiện bằng canonical census helper là
`active_runtime_work`, cụ thể `active_agent_lanes=1` của run `54290…`; đây là
lane của task song song đang ở `ACCEPTING`. Không có quyền hợp lệ để tự
accept/reject/stop/adopt lane hoặc sửa canonical ledger, vì vậy P0.2/P0.3
không được đóng bằng suy luận. `npm run dev` sau đó xác nhận UI không đủ:

```text
DEV_UI STATUS state=MISSING host=available installation=current
running_revision=none update_pending=false
connector_state=UNAVAILABLE connector_rediscovered=false
```

Kết luận wave: lifecycle snapshot đã đạt các điều kiện integrity/projection và
không còn residue tài nguyên, nhưng runtime admission vẫn đóng bởi active
lane; connector freshness chưa có current-process `tools/list`/`server/discover`
receipt. Không tạo accepted baseline, không claim `fullyReady`, natural outcome,
delivery, release hoặc production. Next exact action là để owner của run
`54290…` hoàn tất checkpoint/giải phóng lane theo supported lifecycle, sau đó
recapture census mới và lặp lại full-clean activation; chỉ khi epoch mới
`READY/open` và connector tuple `rediscovered=true`, timestamp khác rỗng,
`refresh_required=false`, `ack_pending=false` mới tiếp tục ACK/baseline.

## 26. Review-driven remediation receipt — 2026-08-28T11:28:29Z

Một review độc lập read-only cho packet Dashboard/UI đã trả `VERDICT: fix` và
chỉ ra năm vi phạm có thể tái hiện. Các sửa chữa nhỏ nhất đã được áp dụng trên
worktree hiện tại:

```text
resources/coding-tools-mcp/coding_tools_mcp/orchestration_control.py
  snapshot(..., recover_if_missing=False) cho phép live path không cold-recover.
resources/coding-tools-mcp/coding_tools_mcp/live_control.py
  live control gọi snapshot(..., recover_if_missing=False), không replay
  waves/events hoặc assert_write_fence khi context cache lạnh.
renderer/app.js
  top-bar #refreshButton phát coding-tools:overview-refresh-request để
  Control Center sở hữu cặp lightweightSnapshot + liveOrchestration.
renderer/dashboard.js
  bỏ api.snapshot() trực tiếp; cấu hình đọc từ snapshot của overview pulse;
  renderAll() chạy trước analytics IPC và analytics rerender độc lập;
  animateText hủy requestAnimationFrame chain trước đó.
tests/*
  thêm regression cho cold-context live path, top-bar routing, shared pulse,
  analytics independence và animation cancellation.
```

Focused proof sau remediation:

```text
node --test tests/control-panel.test.js tests/dashboard-analytics.test.js
  tests/control-center-manager.test.js tests/runtime-lifecycle.test.js
  tests/recovery-bootstrap.test.js                       PASS 119
python -m pytest tests/test_execution_hub.py
  tests/test_orchestration_control.py -q                  PASS 20
git diff --check                                           PASS
```

Một lần chạy HTTP test trung gian gặp `ConnectionAbortedError` tại nhánh
401 unauthorized; chạy lại đúng test đơn lẻ và toàn bộ packet đều pass, nên
được phân loại là flaky transient chứ không phải failure mới.

HEAD đã tiến lên đồng thời trong worktree bởi commit ngoài wave này:

```text
HEAD                                      e4075d81e5de465837e501e28016ccc7b2afa7ce
```

Immutable census cùng thời điểm vẫn giữ:

```text
physical snapshot SHA-256                 0ee862fb511eff51c340cbac6a5b4d66e7d3ea8396609c28718bbc056272bc58
logical snapshot SHA-256                  c9a2e8f3cfa9452c0c9069f81922f4dd7bca84aa1df6b793c001cbc535fcdb02
projection                                CONTEXTUAL_PROJECTIONS
missing / unexplained / unbound / managed 0 / 0 / 0 / 0
active agent lanes                        1 (run 54290… vẫn ACCEPTING)
awaiting acceptance                       13
```

Remediation source đã hoàn tất ở mức focused proof, nhưng live closure chưa
thể thực hiện: lane `54290…` vẫn là active authority residue, Recovery
Host/runtime chưa có admission `READY/open`, và connector chưa có
current-process discovery receipt. Không accept/reject/stop lane, không sửa
ledger, không tạo synthetic workload, không tạo accepted baseline, và không có
push/release/deploy. Next action vẫn là để owner của lane hoàn tất supported
checkpoint, recapture census, rồi chạy full-clean activation và connector
rediscovery từ đầu trên HEAD mới.

## 27. Repeated `npm start` failure — exact current cause and authority boundary — 2026-08-28T11:39:42Z

Lỗi người dùng quan sát được tái hiện nguyên văn trên `HEAD=e4075d81e5de465837e501e28016ccc7b2afa7ce`:

```text
DEV_UI REFRESH action=full_clean
DEV_UI ERROR code=ORCHESTRATION_STATE_UNCERTAIN
message=Canonical ledger census refused stopped-runtime activation.
exit_code=1
```

Đây không phải lỗi thiếu Python, lỗi cổng, hay lỗi source patch. Recovery Host
đã được xác thực nhưng Coding MCP/Tunnel đang dừng; proxy trả `503` vì durable
activation admission vẫn đóng. Census query-only mới nhất (`observed_at`
`2026-08-28T11:39:42.202Z`) giữ các điều kiện integrity:

```text
physical snapshot SHA-256                 0ee862fb511eff51c340cbac6a5b4d66e7d3ea8396609c28718bbc056272bc58
logical snapshot SHA-256                  c9a2e8f3cfa9452c0c9069f81922f4dd7bca84aa1df6b793c001cbc535fcdb02
integrity / foreign keys                 ok / 0
projection                               CONTEXTUAL_PROJECTIONS
projection missing / unexplained         0 / 0
unbound / managed residue                0 / 0
awaiting acceptance                      13
active agent lanes                       1
```

Lane duy nhất còn sống là exact row sau:

```text
run_id                                   54290b6f078c43bdabe921de358a5d3a
lane_id                                  F-GzPsj9YBqqCDj_
thread_id                                01a047fe-32e3-7652-8734-b03f658a8b4c
semantic_key                             dashboard-ui-performance-independent-review-v1
lifecycle                                active
latest bridge status                     inProgress
parent run state                         ACCEPTING
```

Thread review đã thực sự trả `VERDICT: fix` và hiện idle/completed, nhưng lane
ledger chưa nhận được terminal outcome. Tôi đã gửi yêu cầu chính thức cho
thread owner tự terminalize; owner xác nhận task hiện không expose
`task_control`, `coordination`, hay `checkpoint` surface. Do đó không có
authority surface hợp lệ để đóng exact lane từ task hiện tại. Sửa trực tiếp
SQLite, tự accept/reject/stop/adopt run, hoặc nới census để bỏ qua lane sẽ là
false-green và vi phạm boundary của ledger.

Kết luận hiện tại: source remediation và focused proof vẫn COMPLETE; live
activation P0.2/P0.3 vẫn BLOCKED bởi authority residue thật, không phải do
patch chưa sửa. Next action bắt buộc là owner/controller có supported
task-control surface đóng lane `F-GzPsj9YBqqCDj_` và hoàn tất/giải quyết run
`54290…`; sau đó recapture immutable census và chạy lại `npm start`. Chỉ khi
epoch mới `READY/open`, process identities/revision khớp, và connector có
fresh current-process `tools/list` hoặc `server/discover` mới được ACK hoặc
tạo accepted baseline. Không có direct SQLite edit, process kill, commit,
push, release, deploy, hay production action trong checkpoint này.

## 28. Live activation and connector closure — 2026-08-29T09:03:37Z

Blocker activation/connector của các checkpoint trước đã được giải quyết bằng
current-process evidence. Repository vẫn ở `branch=main`,
`HEAD=e4075d81e5de465837e501e28016ccc7b2afa7ce`, worktree dirty được bảo toàn;
không có reset/restore/clean hoặc direct ledger edit.

Official Recovery Host capture qua các read-only action `recovery.status`,
`runtime.lightweight_snapshot`, `runtime.activation_epoch_status` và durable
activation receipt xác nhận cùng một epoch:

```text
activation_epoch_id                    activation-mte4v3zt-96dafc173b4553ca8bd5d69b81fb5f45
operation_id                           full-clean-refresh-mte4uoyr-902fccedaaf005d6ebbe2272
epoch state                            READY
admission_open                         true
update_incomplete                      false
ready_commit_digest                    93cd38fb10d36ee35e8346a75af376cb94201e19ef72d6e0af2afc0634db0f5f
ready_at                               2026-08-29T08:44:25.692Z
error                                  null
workspace                              E:\DEV\Codex-web
mcp / native / tunnel                  true / true / true
componentsReady / connectorReady       true / true
fullyReady                             true
Recovery Host state                    healthy/current
Electron UI PID / instance             29308 / 2a088accf701f2b0b69020bf8252b3dd
Electron UI running/disk revision      cb6c9bf6945e9b4e8aa41c12826ba8953adba7fcb1ac091c7d8e1cde80e21f90
Coding MCP running/disk revision       8efa200a45a1bac182f61a15d467de81932fc0ba299d4c45287de68b875a0d70
update_pending                         false
```

Current activation receipt binds the external discovery to the replacement
MCP identity instead of relying on response text, persisted hash, raw HTTP, or
`workspace_context`:

```text
process_instance_id                    Xk7ni_BgTxMQmN-q
server_instance_id                     JTB1LgSgIqB8WU3m
connector validation                   valid=true, code=READY, reasons=[]
connector state                        CURRENT_ACKNOWLEDGED
connector freshness                    current_process_discovery
connector_rediscovered                 true
connector_rediscovered_at              2026-08-29T08:44:10.850647+00:00
connector_refresh_required             false
connector_ack_pending                  false
current contract SHA-256               c244ed297f707f9df48c1e5d6c7e204693f281a755c2e6344bde78e94abb8251
acknowledged contract SHA-256          c244ed297f707f9df48c1e5d6c7e204693f281a755c2e6344bde78e94abb8251
public profile / tool count            smart-v3 / 8
```

Không gọi ACK lần nữa vì state đã là `CURRENT_ACKNOWLEDGED` và
`connector_ack_pending=false`. `recovery.status.gateway_metrics.by_kind.mcp.n`
ở capture này là `0`, nhưng metric đó có scope riêng
`electron_loopback_proxy_to_local_mcp`; nó không thay thế hoặc phủ định durable
current-process discovery receipt nêu trên. Coding Tunnel log có forward
traffic trong current runtime window, còn receipt activation là authority
ràng buộc epoch/process/server/contract.

Sau khi một real ChatWeb controller ngắn hạn tự terminalize và lease tự được
release/expire, immutable Backup-API/query-only census cuối tại
`2026-08-29T09:03:37.737Z` trả:

```text
schema_version                         11
physical snapshot SHA-256              3e932f77eaec7c441e68bc770770dfb82607a39092fad0a057d5db6b977beb02
logical snapshot SHA-256               187f33e2f9bed5fffb90350215871679e44f95109706e4e5c61f5918dc9d5b03
integrity / foreign keys               ok / 0
query_only / immutable                 true / true
mutated_canonical_ledger               false
active agent lanes                     0
active controller leases               0
active write fences                    0
live managed jobs                      0
running background operations          0
unexplained active runs                0
unbound live resource residues         0
stale background residues              0
projection                             CONTEXTUAL_PROJECTIONS
projection missing/conflicting         0 / 0
projection_drift                       false
```

Do đó activation admission, process replacement, connector freshness/ACK và
live ownership convergence hiện PASS. Danh sách RUN lịch sử còn lại không phải
lỗi kết nối hoặc live authority: census phân loại `93` ordinary active rows là
`THRESHOLD_SENSITIVE_STALE_CANDIDATE`, tất cả không có live ownership. Chúng
vẫn là housekeeping cần supported exact-ID reconciliation; không bulk-close,
force-release hoặc sửa SQLite chỉ để tạo false-green.

### 28.1. Accepted-baseline decision

Read-only `report_p5_baseline.py` quan sát được baseline lịch sử hữu cơ nhưng
không tạo sample, assignment, treatment hoặc production behavior:

```text
baseline kind                          organic_rework_observational_v1
baseline_observed                      true
accepted runs                          480
first-pass / repaired accepted         281 / 199
first-pass / repaired rate             0.585417 / 0.414583
P5 canonical start readiness           false
P5 epoch lifecycle                     EPOCH_HARD_STOPPED
treatment_started / samples_created    false / false
current-source accepted runs           0
exact current-source window            false
current-source decision                insufficient_head_window_volume
monetary CAR coverage                  0.0
CAR status                             unavailable
promotion evaluation                   NOT_STARTED
```

Đây chỉ là descriptive observational evidence, không phải treatment effect và
không phải P0.6 immutable accepted baseline. P0.6 vẫn `NOT CREATED` vì các exit
criteria trong §P0.6 chưa đồng thời đạt:

```text
Git/workspace/runtime/contract identity current   PASS
connector discovery/ack current-process           PASS
proof bundle                                      existing focused proof; no new source proof in this docs-only wave
live ownership and projection convergence         PASS
historical stale-run count=0                      FAIL (93 exact candidates remain)
measured real-machine UI performance baseline     NOT ESTABLISHED
exact-current-source accepted-result window       NOT ESTABLISHED
complete monetary CAR                             NOT ESTABLISHED; missing remains unknown, not zero
```

Vì vậy không tạo accepted baseline, không mở P5, không enroll/assign, không tạo
synthetic/natural outcome giả và không claim production readiness. Next exact
actions là: (1) reconcile từng historical stale candidate qua supported
authority với exact guard; (2) recapture census yêu cầu stale-run count `0`;
(3) đo UI event-loop/IPC/read-model trên representative real-machine window;
và (4) chỉ khi source/proof/runtime/contract/performance cùng immutable mới ghi
accepted P0.6 baseline. Không commit, push, package, release hoặc deploy trong
checkpoint này; chronology `260826` không bị sửa.

## 29. Superseding runtime/connector diagnosis — 2026-08-29T09:47:00Z

Section 28 là một receipt lịch sử của epoch `activation-mte4v3zt` và không còn
được dùng làm authority sau khi process replacement. Sau khi HEAD tiến tới
`2e254b2b4478be7fb803a3bb2366dba5e6fe8a37`, tôi đã giữ nguyên worktree dirty và
thực hiện exact-ID reconciliation qua primitive được hỗ trợ, không sửa SQLite
trực tiếp, không bulk-close và không dùng synthetic workload. Bốn RUN vừa vượt
ngưỡng theo thời gian đã được xử lý tuần tự với stopped-runtime fence:

```text
9b9c604cd5654cc1935ac97c594a98a0
af372393fff74ef6b359955fb09bc0c7
16b4d39038944365811da1da85bca3ce
045b4a0b336640d88a275a4fba2894d2
```

Mỗi receipt trả `changed=true`, `idempotent=false`, `chain_ok=true`. Census
độc lập cuối tại `2026-08-29T09:47:00.702Z` xác nhận:

```text
physical / logical SHA-256              48eb937580b0084142f15d1f70d1fd58a8055f57f9c82fbbb27b6672489cb1cf / cc86d753b6252828d682fc8f351ce53c6e2aa676c5f3802dd983d2cd52ae32a7
integrity / foreign keys                ok / 0
ordinary active runs                    11 (đều threshold-sensitive, chưa đủ 24 giờ)
eligible_stale_count                    0
active agent lanes / leases / fences    0 / 0 / 0
live jobs / background operations       0 / 0
unexplained / unbound / stale residue   0 / 0 / 0
projection_drift / mutated ledger       false / false
```

`npm start` sau đó đã tạo epoch mới
`activation-mte6px42-b67cd1c63b45adb65f234bf76e54951a` với Recovery Host
`9d3c1d40887b1994c26aaaf606bf0cec`, UI `d06a7614d2f93ad04679d5d38d0fe6de`,
Coding MCP/Tunnel mới (PID lần lượt `15424`/`43632`), và running/disk revision
Coding MCP cùng là
`8efa200a45a1bac182f61a15d467de81932fc0ba299d4c45287de68b875a0d70`. Tuy
nhiên epoch đã hết hạn lúc `2026-08-29T09:45:01.329Z` với
`ACTIVATION_REQUEST_EXPIRED`, `epoch_state=FAILED`, `admission_open=false` và
`update_incomplete=true`.

Nguyên nhân đã được xác định ở ranh giới connector, không phải tool registry
hay source remediation:

1. `Server.list_tools()` gọi `_record_tool_discovery()` trước khi trả payload,
   nhưng receipt chỉ được lưu khi request đã đi qua HTTP identity context. Bộ
   lọc `connector_tool_discovery()` chỉ chọn receipt có
   `client_type == "chatweb"`, sau đó buộc khớp `contract_sha256`,
   `process_instance_id` và `server_instance_id` của process hiện tại
   (`resources/coding-tools-mcp/coding_tools_mcp/server.py`).
2. Danh sách 8 tool là payload được cache trong lifetime của Runtime và
   `tool_contract`/`tool_count` là metadata deterministic. Vì vậy câu trả lời
   bằng chữ hoặc danh sách 8 tên không chứng minh request `tools/list` đã chạm
   process mới.
3. Browser ChatWeb tại thời điểm kiểm tra hiển thị `Coding-VP` ở trạng thái
   host-disabled; các tool-card thực tế được quan sát là `GitHub Fetch`/
   `Coding_MCP`, không có một lời gọi `Coding-VP tools/list` hoặc
   `server/discover` được ghi nhận. Do đó Recovery Host giữ đúng
   `connector_state=UNCHANGED_ACKNOWLEDGED`,
   `connector_rediscovered=false`, `connector_rediscovered_at=null`,
   `connector_refresh_required=false`, `connector_ack_pending=false`.
4. Nếu request đi qua `hubProxyGateway`, allowlist chỉ cho
   `codex-desktop|codex_desktop` và `opencode|opencode`; các receipt đó không
   phải `chatweb` và bị loại khỏi strict discovery. Ngược lại, một HTTP call
   thủ công không header có thể bị server suy ra là `chatweb`, nhưng không có
   provenance chứng minh đó là ChatWeb thật; không được dùng làm acceptance
   proof hoặc ACK.
5. Full-clean epoch có TTL 600 giây. Khi không có current-process real-client
   discovery trong cửa sổ này, supervisor phải đóng admission và để epoch
   fail-closed; việc lặp `npm start` trước khi connector được bật thật chỉ tạo
   thêm các epoch hết hạn cùng một nguyên nhân.

Vì vậy phần phân tích trước đây rằng “đã gọi HTTP trực tiếp không header nên
`mte4v3zt` là proof thật” là không đủ cơ sở provenance và không được kế thừa.
Receipt `mte4v3zt` vẫn được giữ như chronology, nhưng chỉ một discovery mới từ
ChatWeb/Coding-VP thật, khớp process/server/epoch hiện tại và sau đó qua guard
ACK mới có thể mở admission. Accepted baseline, P5 treatment và production
claim tiếp tục **NOT CREATED / NOT STARTED / NOT CLAIMED**. Bước mở duy nhất
còn lại là bật lại host `Coding-VP`, thực hiện đúng một `tools/list` hoặc
`server/discover` thực từ ChatWeb, rồi recapture official Recovery Host; không
được thay bằng `workspace_context`, `tools/call`, raw HTTP, persisted SHA hoặc
textual response.

## 30. Đính chính phân tích được dán — 2026-08-29T10:00:00Z

Phân tích được dán là một đầu vào tư vấn, không phải receipt runtime. Sau khi
đối chiếu với source và epoch mới, cần chốt lại các mệnh đề theo bảng sau:

| Mệnh đề | Kết luận chuẩn | Phạm vi bằng chứng |
| --- | --- | --- |
| ChatWeb hiển thị đúng 8 tên tool | Không đủ để chứng minh discovery | Đây chỉ là catalog/schema có thể được cache ở connector host; không chứng minh `tools/list` hoặc `server/discover` đã chạy trong MCP process hiện tại. |
| Receipt phải có `client_type=chatweb` và khớp SHA/process/server | Đúng nhưng chưa đủ cho provenance bên ngoài | Đây là điều kiện cần của `connector_tool_discovery()`; nó vẫn dựa trên identity mà HTTP request cung cấp hoặc server suy ra. |
| `CURRENT_COMPATIBLE_ACKNOWLEDGED` tương đương strict full-clean READY | Sai | Runtime có thể phân loại compatibility bootstrap là một continuity state, nhưng `validateConnectorReadyGate()` của full-clean cố ý thêm `STRICT_CONNECTOR_REDISCOVERY_REQUIRED`; state này không đáp ứng acceptance tuple bắt buộc của nhiệm vụ. |
| Gọi loopback `/mcp` không header rồi nhận receipt `chatweb` là proof ChatWeb | Sai về provenance | `http_hub_identity.py` hiện suy ra `chatweb` khi thiếu header. Vì vậy request local có bearer token có thể tạo receipt trông hợp lệ. Receipt đó chỉ chứng minh MCP đã nhận request được gán identity `chatweb`, không chứng minh ChatGPT/Coding-VP là caller. |
| Proxy `codex-desktop`/`opencode` có thể đóng strict ChatWeb gate | Sai | `hubProxyGateway` chỉ cho phép các identity đó ở vai trò proxy riêng; chúng không phải `client_type=chatweb` và không được bộ lọc strict tính là ChatWeb discovery. |
| Epoch cũ có thể dùng lại sau khi process replacement | Sai | `connector_rediscovered_at`, `process_instance_id` và `server_instance_id` của `activation-mte4v3zt` chỉ là chronology. Epoch mới `activation-mte6px42-…` đã hết hạn với `ACTIVATION_REQUEST_EXPIRED`; không có current receipt để kế thừa. |

Một chi tiết schema cũng phải ghi đúng: receipt do `Server._record_tool_discovery()`
hiện lưu trực tiếp các field SHA/process/server/thời gian và **không** có
`activation_epoch_id`. Guard strict đạt được liên kết epoch bằng cách đối chiếu
`health.activation_epoch_id` của process hiện tại với durable activation epoch,
đồng thời đối chiếu discovery với chính process/server đó. Vì vậy không được
diễn đạt rằng bản thân discovery receipt đã là một epoch attestation độc lập;
đó là một liên kết hai lớp của health snapshot và Recovery Host guard.

Điểm cần phân biệt rõ là **runtime state**, **strict activation gate** và
**provenance của caller** là ba lớp độc lập:

```text
catalog 8 tool
    != current-process tools/list/server/discover
    != official Recovery Host acknowledgement
    != bằng chứng độc lập rằng caller là ChatGPT/Coding-VP thật
```

Vì vậy không nên sửa hiện tượng bằng cách gọi raw HTTP, tự đặt header
`chatweb`, copy SHA, hoặc chấp nhận văn bản “discovery receipt”. Một bản sửa
provenance thực sự phải có hợp đồng giữa tunnel/client và MCP (attestation có
thể xác minh, bind với epoch/process/server/contract và được tunnel cấp), kèm
producer/consumer tests. Source hiện tại chưa có hợp đồng attestation đó; chỉ
đổi bộ lọc phía MCP sẽ làm mất khả năng phân biệt hoặc phá client hợp lệ. Do
đó wave này **không giả vờ đã sửa provenance trong source** và không tạo ACK.

Trạng thái vận hành chốt theo bằng chứng mới nhất:

```text
clean census:          active_agent_lanes=0; live jobs/leases/fences=0
current process:       đã thay thế nhưng epoch mte6px42 đã FAILED/expired
connector discovery:  connector_rediscovered=false; timestamp=null
strict admission:     CLOSED
accepted baseline:     NOT CREATED
```

Next action duy nhất để đóng gate là: bật host `Coding-VP`, chạy một full-clean
activation mới sau census sạch, để chính ChatWeb thực hiện đúng một
`tools/list` hoặc `server/discover`, rồi đọc **official Recovery Host receipt**.
Chỉ chấp nhận khi đồng thời có:

```text
connector_rediscovered=true
connector_rediscovered_at != empty
connector_refresh_required=false
connector_ack_pending=false
```

Ngoài bốn cờ trên, receipt phải khớp `activation_epoch_id`,
`process_instance_id`, `server_instance_id`, contract SHA và running/disk
revision. Chỉ sau đó mới xem xét ACK và accepted baseline. Tài liệu chronology
`260826` không bị sửa.

## 31. Checkpoint census/reconciliation superseding — 2026-08-29T10:07:07Z

Sau §30, tôi recapture một Backup-API lifecycle census mới thay vì dùng lại
hash của receipt cũ. Census tại `2026-08-29T10:05:20.327Z` đã xác nhận một
RUN duy nhất vừa vượt ngưỡng stale `24h`:

```text
physical snapshot SHA-256              62505f4ecf0dd91c2cf13d3c86ca610dffa136148f87e00ad053e42f9e21920a
logical snapshot SHA-256               d2cc0acb53104460e50b95b3c05e30100b8614812eb2dd3842af510c5269ad11
integrity / foreign keys               ok / 0
ordinary active runs                   6
eligible stale candidates              1 (7f852fd7a0fa4c17838eedb41826e706)
active agent lanes                     0 (mọi ownership.live_agent_lanes đều 0)
active controller leases / write fences 0 / 0
live managed jobs / background ops     0 / 0
unexplained / unbound / stale residue  0 / 0 / 0
projection_drift / mutated ledger      false / false
```

Preflight exact-ID ban đầu đúng về lifecycle nhưng lần apply đầu bị guard từ
chối vì snapshot acknowledgement đã cũ (`exact stale-run physical snapshot
changed or was not acknowledged`). Tôi không bỏ qua guard và không sửa SQLite
trực tiếp. Preflight mới ngay sau đó vẫn khớp cả hai SHA nêu trên; lệnh được
ủy quyền qua `reconcile_exact_stale_run.py` với stopped-runtime authority cho
duy nhất RUN `7f852fd7a0fa4c17838eedb41826e706` và trả:

```text
changed=true
idempotent=false
chain_ok=true
```

Census hậu kiểm tại `2026-08-29T10:07:07.759Z` xác nhận RUN trên đã chuyển
sang `status=stale`, `classification=RECONCILED_STALE` với receipt exact-ID;
không có live child/ownership. Hash snapshot hậu kiểm là:

```text
physical snapshot SHA-256              ad263fb5025db491a855ae9b994de26d9256457e24babf6f6e2c6fa19c913d33
logical snapshot SHA-256               f48a5e473c7690592ff23e2a8032d9ca903e931756a0ff11f0e61f0975151a1e
integrity / foreign keys               ok / 0
ordinary active runs                   5
eligible stale candidates              0
active agent lanes                     0
active controller leases / write fences 0 / 0
live managed jobs / background ops     0 / 0
unexplained / unbound / stale residue  0 / 0 / 0
projection_drift / mutated ledger      false / false
remaining RUNs                         5, tất cả below_current_stale_threshold
```

Một read-only recapture ngay sau đó tại `2026-08-29T10:12:21Z` vẫn giữ nguyên
hai SHA hậu kiểm và xác nhận trực tiếp `active_agent_lanes=0`,
`active_controller_leases=0`, `active_write_fences=0`, `eligible_stale_count=0`,
`projection_drift=false`, `mutated_canonical_ledger=false`, integrity `ok` và
foreign-key violations `0`.

Không reconcile tiếp năm RUN còn lại: mỗi RUN đều là
`THRESHOLD_SENSITIVE_STALE_CANDIDATE` nhưng chưa đáp ứng
`meets_current_stale_threshold` tại census hậu kiểm. Đây là kết quả fail-closed
đúng; không bulk-close và không coi `ordinary_active_runs=5` là lỗi connector.

Runtime receipt ngay sau hậu kiểm vẫn là:

```text
state=CURRENT
host=available / installation=current
UI pid=5280 / instance=d06a7614d2f93ad04679d5d38d0fe6de
running_revision == disk_revision
  cb6c9bf6945e9b4e8aa41c12826ba8953adba7fcb1ac091c7d8e1cde80e21f90
update_pending=false
connector_state=UNAVAILABLE
connector_rediscovered=false
connector_rediscovered_at=none
connector_refresh_required=false
connector_ack_pending=false
connector_current_sha=none
connector_ack_sha=c244ed297f707f9df48c1e5d6c7e204693f281a755c2e6344bde78e94abb8251
error_code=none
```

Do đó checkpoint này chỉ đóng được phần lifecycle maintenance của một RUN và
giữ được `active_agent_lanes=0`; nó **không** mở strict connector admission.
Coding MCP/Tunnel/UI chưa có process identity/epoch receipt mới được chứng minh
qua real ChatWeb/Coding-VP `tools/list` hoặc `server/discover`. Vì vậy vẫn giữ:

P5 baseline report recapture lúc `2026-08-29T10:16:07.468Z` cũng không mở được
gate: `baseline_kind=organic_rework_observational_v1`,
`baseline_observed=true` nhưng `canonical_readiness_passed=false`, CAR
`unavailable`/coverage `false`, current-source accepted runs `0`, exact current
source window `false`, monetary cost coverage `0`, `p5_epoch=EPOCH_HARD_STOPPED`,
`treatment_started=false`, `samples_created=false` và promotion
`NOT_STARTED`. Đây là observational history, không phải accepted treatment
baseline; thiếu dữ liệu vẫn là **unknown**, không được diễn giải thành zero.

```text
strict admission                 CLOSED
connector ACK                    NOT CREATED
accepted baseline / P5           NOT CREATED / NOT STARTED
production/readiness claim       NOT CLAIMED
```

Next action có điều kiện duy nhất: khi host Coding-VP thật đã bật, recapture
census sạch, chạy một full-clean activation, để chính client ChatWeb thực hiện
đúng một `tools/list` hoặc `server/discover`, rồi đọc official Recovery Host
snapshot. Chỉ chấp nhận ACK khi đồng thời có
`connector_rediscovered=true`, `connector_rediscovered_at` không rỗng,
`connector_refresh_required=false`, `connector_ack_pending=false` và mọi
contract/process/server/epoch/revision đều khớp. Không chạy `npm start` trước
khi điều kiện external này thay đổi; không dùng raw HTTP, `workspace_context`,
`tools/call`, textual receipt hoặc persisted SHA để thay thế discovery.

## 32. Current superseding checkpoint and provenance hardening — 2026-08-29T10:24:04Z

§31 đã đúng cho thời điểm `10:12:21Z` nhưng không còn là census mới nhất. Tôi
đã recapture lại bằng `report_lifecycle_census.py` sau khi áp dụng hardening
provenance; không dùng lại snapshot cũ và không sửa SQLite trực tiếp.

Census query-only mới nhất (`snapshot_at=2026-08-29T10:23:16.641Z`) xác nhận:

```text
physical snapshot SHA-256              ad263fb5025db491a855ae9b994de26d9256457e24babf6f6e2c6fa19c913d33
logical snapshot SHA-256               f48a5e473c7690592ff23e2a8032d9ca903e931756a0ff11f0e61f0975151a1e
integrity / foreign keys               ok / 0
ordinary active runs                   5
eligible_stale_count                   0
active_agent_lanes                     0
active controller leases / write fences 0 / 0
live managed jobs / background ops     0 / 0
unexplained / unbound residues         0 / 0
projection_drift / mutated ledger      false / false
```

Năm RUN còn lại vẫn là `THRESHOLD_SENSITIVE_STALE_CANDIDATE` và đều có
`below_current_stale_threshold`; không bulk-close chúng. Đây là trạng thái
lifecycle sạch theo nghĩa ownership (`active_agent_lanes=0`), không phải bằng
chứng connector đã hoạt động.

Read-only `npm run dev:status` tại `2026-08-29T10:24:04.105Z` vẫn cho:

```text
state=CURRENT
host=available / installation=current
UI pid=5280 / instance=d06a7614d2f93ad04679d5d38d0fe6de
running_revision == disk_revision
  cb6c9bf6945e9b4e8aa41c12826ba8953adba7fcb1ac091c7d8e1cde80e21f90
update_pending=false
connector_state=UNAVAILABLE
connector_rediscovered=false
connector_rediscovered_at=none
connector_freshness_mode=none
connector_refresh_required=false
connector_ack_pending=false
connector_current_sha=none
connector_ack_sha=c244ed297f707f9df48c1e5d6c7e204693f281a755c2e6344bde78e94abb8251
error_code=none
```

Durable epoch mới nhất của lần full-clean gần đây nhất không mở admission:

```text
activation_epoch_id                    activation-mte6px42-b67cd1c63b45adb65f234bf76e54951a
operation_id                           full-clean-refresh-mte6ppe4-2c01282364cbc4de0e751e86
state / admission                      FAILED / CLOSED
error                                  ACTIVATION_REQUEST_EXPIRED
failed_at                              2026-08-29T09:45:05.343Z
process_instance_id / server_instance  M9MqwT-31L8F-8x8 / uDKIVLSVKjXXPrqE
tunnel_instance_id                     7a8d470eb50c69b218ba9709
Coding MCP running == disk revision    true (8efa200a45a1bac182f61a15d467de81932fc0ba299d4c45287de68b875a0d70)
connector_rediscovered_at              none
connector_freshness_mode               none
```

Để sửa đúng phần false-positive đã nêu trong phân tích được dán, source hiện
đã có một hardening hẹp và backward-compatible:

* `http_hub_identity.py` ghi `identity_source` là
  `explicit_headers`, `partial_headers` hoặc `implicit_default`;
* `_record_tool_discovery()` chỉ đưa receipt vào strict candidate khi caller
  chuyển **đồng thời** `X-Coding-Tools-Client-Id` và
  `X-Coding-Tools-Client-Type`, và receipt giữ lại nguồn identity;
* `electron/services/tunnelService.js` cấu hình managed Coding Tunnel chuyển
  rõ hai header `chatweb` cho cả `mcp.extra-headers` và
  `mcp.discovery-extra-headers`;
* loopback HTTP thiếu identity vẫn được phục vụ, nhưng không còn tạo
  `connector_rediscovered` authoritative.

Hardening này giải quyết chính đường tắt “raw localhost không header tự được
gán ChatWeb”. Nó **chưa phải attestation mật mã của tunnel**: một caller cục
bộ có thể tự biết và tự gửi hai header explicit. Vì vậy strict acceptance vẫn
phải dựa trên official Recovery Host + tunnel/client contract; không được gọi
explicit header, SHA, process ID hoặc timestamp riêng lẻ là bằng chứng ChatGPT
thật. Bước attestation bind `activation_epoch_id + process_instance_id +
server_instance_id + contract_sha256 + nonce/timestamp` vẫn là backlog kiến
trúc, cần producer/consumer contract với tunnel trước khi triển khai tiếp.

Focused proof của hardening:

```text
pytest test_connector_bootstrap_identity.py test_stateless_http_2026.py  24 passed
pytest test_activation_epoch.py test_multi_workspace_http_matrix.py        7 passed
pytest test_execution_hub.py test_execution_hub_faults.py
      test_hub_proxy_stdio.py test_exception_group_boundary.py
      test_live_transport_failures.py                                      35 passed
node --test tests/hub-proxy-gateway.test.js tests/runtime-lifecycle.test.js
                 tests/dev-ui-lifecycle.test.js                            116 passed
```

Các lớp còn lại không thay đổi: catalog 8 tool vẫn không phải discovery,
compatibility bootstrap không phải strict rediscovery, `connector_rediscovered`
vẫn `false`, admission vẫn `CLOSED`, accepted baseline/P5 vẫn
`NOT CREATED`/`NOT STARTED`. Không gọi `tools/call`, không ACK, không
restart/deploy trong checkpoint này. Next action chỉ được mở sau khi host
Coding-VP thật phát sinh request `tools/list`/`server/discover` mới qua managed
transport và Recovery Host trả đúng tuple bốn cờ cùng identity/epoch/revision
khớp; khi đó mới cân nhắc attestation contract và accepted baseline.

## 33. Attestation contract hardening — 2026-08-29T10:50:43Z

Phân tích được dán đã chỉ đúng root defect còn lại: cặp header
`X-Coding-Tools-Client-Id/Type=chatweb` có thể do một caller local tự đặt, nên
SHA/process/server/timestamp khớp vẫn chưa chứng minh được provenance của
ChatWeb. Hardening bước một ở §32 chỉ chặn trường hợp **thiếu** header; nó
không chặn impersonation bằng header explicit.

Source hiện đã bổ sung hợp đồng attestation tối thiểu cho managed Coding
Tunnel:

* `connector_attestation.py` định nghĩa giá trị HMAC `v1` bind đồng thời
  `client_id`, `client_type`, `activation_epoch_id`, `process_instance_id`,
  `server_instance_id`, `contract_sha256`, `issued_at_unix_ms` và nonce;
  secret không bao giờ đi vào wire receipt/health/tool output.
* Native MCP process nhận secret one-shot từ Electron qua
  `CODING_TOOLS_MCP_CONNECTOR_ATTESTATION_SECRET`; Electron xoay secret mỗi
  lần thay process.
* Coding Tunnel ký một giá trị tĩnh bằng secret và gắn nó vào
  `mcp.extra-headers` cho traffic MCP được forward. `mcp.discovery-extra-headers`
  của tunnel-client (probe nội bộ) **không** nhận attestation, vì probe nội bộ
  không được phép tự tạo ChatWeb discovery receipt.
* MCP chỉ nâng `identity_source` thành `attested_transport` khi chữ ký, tuple
  hiện tại và cửa sổ thời gian đều hợp lệ. `tools/list/server/discover`,
  compatibility bootstrap và ordinary successful `tools/call` contact không có
  attestation vẫn phục vụ/quan sát như MCP bình thường nhưng không thể mở
  strict connector gate.
* Recovery Host/RuntimeOrchestrator kiểm tra `attestation_verified=true` trên
  discovery/contact/bootstrap trước khi ACK hoặc tính freshness; receipt cũ,
  replay khác process/server/epoch/contract và explicit header không chữ ký đều
  fail-closed.

Đây là provenance contract thực thi được giữa Electron-managed tunnel và MCP,
không phải tuyên bố rằng mọi local administrator đều không thể đọc process
environment. Vì vậy vẫn phải giữ official Recovery Host snapshot và real
ChatWeb/Coding-VP request làm acceptance authority; attestation không biến
catalog tám tool, raw HTTP, `workspace_context` hay textual receipt thành
discovery proof.

Focused proof sau hardening:

```text
Python attestation/identity/stateless discovery                  30 passed
Python activation/workspace matrix                                7 passed
Python hub/fault/proxy/exception/transport                       35 passed
Node connector-attestation helper                                  1 passed
Node runtime-lifecycle/full-clean activation                     108 passed
Python compileall + module-size guard                             PASS
git diff --check                                                   PASS
```

Runtime live **chưa** được restart để áp dụng source mới và chưa có request
`tools/list/server/discover` từ ChatWeb/Coding-VP thật sau epoch mới. Vì vậy
checkpoint này chỉ đóng source/provenance remediation; nó không nâng trạng
thái hiện tại thành `READY/open`, không ACK connector và không tạo accepted
baseline/P5. Chuỗi external còn bắt buộc vẫn là:

```text
census active_agent_lanes=0
-> full-clean activation mới
-> real ChatWeb/Coding-VP tools/list hoặc server/discover qua managed tunnel
-> Recovery Host snapshot khớp epoch/process/server/contract/revision
-> chỉ ACK khi bốn cờ strict đồng thời đạt
-> sau đó mới xem xét accepted baseline
```

## 34. Superseding source closure after attestation integration — 2026-08-29

§33 mô tả đúng hợp đồng attestation ban đầu, nhưng chưa bao phủ bốn lỗi tích
hợp được phát hiện khi kiểm tra toàn bộ đường lifecycle. Source hiện đã đóng
thêm các điểm sau:

1. **Soft recovery giữ đúng attestation dependency.** Tunnel-only recovery chỉ
   được phép khi Recovery Host hiện tại còn sở hữu secret/binding của đúng MCP
   process hiện tại; nếu không có authority đó, nó fail-closed bằng
   `CONNECTOR_ATTESTATION_BINDING_UNAVAILABLE` và yêu cầu full-clean activation.
   MCP-only recovery xoay secret cùng process mới và refresh đúng dependent
   Coding Tunnel; Recovery Host, UI và recovery plane không bị thay ngoài scope.
2. **Receipt authoritative không bị raw observation ghi đè.** Discovery receipt
   được partition theo provenance. `attested_transport` và
   `implicit_default`/`explicit_headers` dùng các slot khác nhau, nên một raw
   loopback `tools/list` sau discovery hợp lệ không thể xóa proof đã attested.
3. **Revision fingerprint bao phủ trust-boundary helper.** Recovery Host
   `COMPONENT_SPECS` đã sở hữu `electron/services/connectorAttestation.js`, nên
   `running_revision == disk_revision` không thể bỏ sót thay đổi byte của helper
   bảo mật này.
4. **Recovery Supervisor test harness không đọc stop sentinel cài đặt thật.**
   Invocation có `StatusPath`/`ManifestPath` explicit đặt sentinel cạnh harness;
   chỉ invocation cài đặt thực mới dùng global install-root sentinel. Sentinel
   thật không bị xóa hoặc sửa.

Guard package sau đó phát hiện `server.py` tăng lên 3.505 dòng, vượt budget
3.500. Đây là lỗi source thật mà checkpoint trước chưa phản ánh. Hai method
discovery-receipt đã được chuyển nguyên semantics sang `RuntimeActivityMixin`,
module sở hữu connector activity. Kết quả hiện tại:

```text
server.py / runtime_activity.py                         3414 / 447 lines
Python focused attestation/bootstrap/stateless                  31 passed
Python full MCP suite                            738 passed, 4 skipped
Node full repository suite                                   533 passed
Node live recovery set                                         73 passed
Recovery Supervisor set                                        10 passed
Python compileall / module-size guard                         PASS / PASS
git diff --check / source-root / secret check              PASS / PASS / PASS
coding-tools history guard                         PASS (2438 files)
```

`HEAD c0aa335c7c12746a1f4ff42e84234f8c54914658` đã xuất hiện trên `main`
và `origin/main` trước extraction module-size ở trên; lượt hiện tại không tạo,
amend hoặc push commit đó. Worktree sau extraction được giữ dirty có chủ đích,
không reset/clean và không đụng hai file bằng chứng durable ngoài các writer
runtime bình thường.

Đây vẫn chỉ là **source + deterministic proof**. Runtime chưa được full-clean
activation lại trên exact worktree sau extraction, chưa có attested
ChatWeb/Coding-VP discovery của process mới, chưa ACK và chưa tạo accepted
baseline/P5. Gate live tiếp theo không đổi:

```text
fresh immutable lifecycle census
-> full-clean activation của exact disk revision
-> real ChatWeb/Coding-VP tools/list hoặc server/discover qua managed tunnel
-> official receipt attestation_verified=true và exact epoch/process/server/SHA
-> ACK chỉ khi rediscovered=true, timestamp!=empty,
   refresh_required=false, ack_pending=false
-> accepted baseline chỉ được xem xét sau strict gate
```

## 35. Compatibility projection alignment — 2026-08-29

Đối chiếu advisory đính kèm với source hiện tại cho thấy advisory đúng khi
không coi catalog tám tool là discovery proof và khi từ chối raw localhost
impersonation. Tuy nhiên, nó còn bỏ sót một lệch tích hợp: một số projection
chung trước đây vẫn trả `ready=true`/`LIVE_CLOSED` cho
`CURRENT_COMPATIBLE_ACKNOWLEDGED`, trong khi full-clean validator đã yêu cầu
`STRICT_CONNECTOR_REDISCOVERY_REQUIRED`.

Source hiện đã thống nhất semantics trên mọi bề mặt:

* `connectorContractFreshness()` trả `ready=false` với reason
  `STRICT_CONNECTOR_REDISCOVERY_REQUIRED` cho compatibility bootstrap;
* `activationClosure` không còn coi `CURRENT_COMPATIBLE_ACKNOWLEDGED` là
  `connector_contract_current`;
* Recovery Host `connectorReady` và wrapper V5 chỉ nhận
  `CURRENT_ACKNOWLEDGED` cùng `connector_rediscovered=true` và timestamp hợp
  lệ;
* Command Center hiển thị compatibility như continuity evidence đang chờ
  strict discovery, không tô xanh hoặc gọi đó là full-clean readiness.

Compatibility bootstrap vẫn được giữ để không phá continuity contract và vẫn
được ghi nhận riêng; nó không mở admission, không đóng `LIVE_CLOSED`, không
đặt `connector_rediscovered`, và không thay thế request
`tools/list`/`server/discover` từ ChatWeb/Coding-VP thật.

Proof source sau alignment:

```text
Node repository suite                          543/543 PASS
connector/runtime/closure/UI focused subset    144/144 PASS
git diff --check                               PASS
```

Runtime hiện tại phải được full-clean activate lại trên exact source sau wave
này. Chưa ACK, chưa accepted baseline/P5, chưa package/release/deploy; mọi
claim live tiếp theo vẫn cần fresh census và attested real-client receipt.

## 36. Lightweight supervision projection and live refresh — 2026-08-29

Sau §35, kiểm tra trên exact worktree cho thấy một blocker hiệu năng còn sót:
`runtime.lightweight_snapshot` vẫn đi qua `decorate()` và `hostStatus()` trên
mỗi heartbeat. Đường này đọc lại durable activation epoch, UI presence/revision
và các projection liên quan, làm IPC nhẹ bị kéo theo các probe nặng và khiến
`normal_ipc_p95` vượt budget.

Đã sửa theo hướng giữ nguyên fail-closed semantics nhưng dời thao tác nặng ra
ngoài đường IPC:

* Recovery Host dựng `lastSupervisionProjection` một lần sau mỗi observation
  của supervisor;
* `cachedRuntimeSnapshot()` và `cachedActivationSnapshot()` chỉ sao chép
  projection đã hoàn tất, cập nhật `snapshotAgeMs`, `snapshotBusy` và
  `signalStale`, không gọi lại `fullCleanActivation.current()`, component hash
  hoặc blocking process-identity probe;
* nếu projection chưa có hoặc bị lỗi, IPC trả `telemetryAvailable=false`,
  `signalStale=true`, `fullyReady=false`, `updateIncomplete=true`, không suy
  diễn cache cũ thành healthy/ready;
* regression test đếm exact durable-epoch/revision/UI-identity reads trong
  lightweight IPC và chứng minh chúng không tăng sau khi projection đã dựng.

Proof source và runtime của wave:

```text
Node repository suite                                      543/543 PASS
Recovery Host + runtime/closure/UI focused subset           144/144 PASS
git diff --check / secret check                             PASS / PASS
coding-tools history guard                                 PASS (2438 files)
fresh query-only census                                    active_agent_lanes=0
active leases/fences/jobs/background operations             0 / 0 / 0 / 0
projection_drift / mutated_canonical_ledger                 false / false
SQLite integrity / foreign_key_check                        ok / 0 rows
```

`npm start` đã hoàn tất full-clean refresh cho epoch
`activation-mtef5pxm-affcc3ab2a36dfe85eed1f9618725869`, tạo Recovery Host
`07fabd3a57c1493e01fd62d28bb697ac`, UI
`c385d43b6bd1827521f2400c570731b4` và MCP/Tunnel process mới. Runtime snapshot
đồng thời xác nhận host/MCP/UI revision của từng component khớp disk; Tunnel
và MCP đang chạy. Epoch vẫn ở `VERIFYING`/`admission=CLOSED`,
`connector_state=UNCHANGED_ACKNOWLEDGED`, `connector_rediscovered=false` vì
chưa có request discovery thật từ ChatWeb/Coding-VP.

Cửa sổ hiệu năng real-machine của chính UI/epoch mới đã đủ mẫu:

```text
renderer/main/event-loop samples                         25 / 50 / 568
normal IPC p95                                           17.2 ms  PASS (<100)
lightweight snapshot p95                                  21.3 ms  PASS
snapshot apply p95                                         0.1 ms  PASS (<50)
dashboard refresh p95                                      35.0 ms  PASS (<500)
event-loop p95                                            15.8 ms  PASS (<50)
```

Vì vậy blocker hiệu năng đã đóng ở source và real-machine measurement. Gate
cuối vẫn mở có chủ ý: phải gửi đúng một `tools/list` hoặc `server/discover`
qua connector ChatWeb/Coding-VP thật, đọc official attested receipt khớp exact
epoch/process/server/SHA/revision, rồi mới ACK khi đồng thời có
`connector_rediscovered=true`, timestamp không rỗng,
`connector_refresh_required=false`, `connector_ack_pending=false`. Chưa ACK,
chưa accepted baseline/P5, chưa package/release/deploy.

## 37. Đối chiếu advisory và recapture fail-closed hiện tại — 2026-08-29T13:52:44Z

Advisory được cung cấp đã chỉ đúng hai lớp lỗi ban đầu: catalog tám tool không
chứng minh request đã chạm MCP process mới, và raw localhost bị gán identity
`chatweb` không phải provenance của ChatWeb thật. Tuy nhiên hai kết luận trong
advisory không còn mô tả đúng target/source hiện tại sau các wave §33-§36:

1. `CURRENT_COMPATIBLE_ACKNOWLEDGED` vẫn tồn tại để ghi continuity evidence,
   nhưng **không** phải đường hợp lệ để full-clean chuyển `READY/open`.
   `validateConnectorReadyGate()` luôn thêm
   `STRICT_CONNECTOR_REDISCOVERY_REQUIRED` cho compatibility-only receipt;
   Recovery Host, activation closure và UI đều giữ readiness fail-closed.
2. Provenance không còn dựa vào việc có hay thiếu hai header identity. Raw
   request thiếu header và request tự đặt explicit `chatweb` header đều có thể
   lấy tool catalog nhưng không được đưa vào authoritative discovery. Chỉ
   identity `attested_transport` với `attestation_verified=true` mới được tính;
   HMAC `v1` bind exact activation epoch, MCP process instance, server instance,
   contract SHA, timestamp và nonce của managed Coding Tunnel.

Focused recapture trên worktree hiện tại xác nhận semantics này:

```text
Node connector/runtime/full-clean/Recovery/UI focused         168/168 PASS
Python connector attestation/bootstrap/stateless               31/31 PASS
git diff --check                                               PASS
```

Census query-only mới tại `2026-08-29T13:47:50.244Z` giữ:

```text
ordinary active runs                         3, đều dưới stale threshold 24h
active agent lanes / leases / fences         0 / 0 / 0
live managed jobs / background operations   0 / 0
unexplained / unbound / stale residue        0 / 0 / 0
projection drift / mutated canonical ledger false / false
SQLite integrity / foreign keys              ok / 0 rows
```

Không reconcile ba RUN threshold-sensitive này. Epoch full-clean mới nhất
`activation-mtefja7g-eab34afccae5db73bee23540af684af2` đã tạo exact process
identity mới và giữ Coding MCP running revision bằng disk revision, nhưng hết
hạn fail-closed lúc `2026-08-29T13:51:46.250Z`:

```text
epoch / admission                         FAILED / CLOSED
error                                     ACTIVATION_REQUEST_EXPIRED
Recovery Host instance                    e348d3c7711945b5c916bf422b8d1198
MCP process / server                      fcfjm450lzcMidB- / M3UX6K1UiLCpfPCQ
Coding Tunnel instance                    a04f7827f39059f0c9b2c184
Electron UI instance                      468bebaad29363592335bdfac144352a
connector rediscovered / timestamp        false / none
connector ACK attempted / completed       false / false
```

Đây là missing external discovery trong TTL, không phải bằng chứng attestation
source bị lỗi. Cửa sổ UI của epoch này hiện chỉ có `10/20/214`
renderer/main/event-loop samples; normal IPC, snapshot apply và event-loop đều
đạt budget, nhưng dashboard refresh p95 `733.6 ms` chưa đạt budget `500 ms` do
một cold-start sample. Không loại outlier và không nâng cửa sổ này thành PASS;
measurement PASS `25/50/568` ở §36 vẫn là proof của epoch trước, không phải
proof thay thế cho epoch đã hết hạn này.

Chuỗi tiếp tục chuẩn là: xin action-time confirmation ngay trước khi gửi tin
nhắn đại diện trên ChatWeb, sau đó recapture census, tạo một full-clean epoch
mới, gửi đúng một `tools/list` hoặc `server/discover` qua Coding-VP thật, rồi
đọc official receipt. Chỉ ACK khi receipt có đồng thời
`identity_source=attested_transport`, `attestation_verified=true`, exact
epoch/process/server/SHA/revision, `connector_rediscovered=true`, timestamp
không rỗng, `connector_refresh_required=false` và
`connector_ack_pending=false`. Chưa đủ tuple thì không ACK, không accepted
baseline/P5 và không dùng raw HTTP, `workspace_context`, `tools/call`, catalog
hoặc textual receipt để thay thế.

## 38. Exact discovery receipt tuple hardening — 2026-08-29T14:08:59Z

Kiểm tra tiếp advisory với toàn bộ producer, health projection và các consumer
Node phát hiện ba khe hở exactness còn lại sau §37:

1. Python đã lưu `identity_source` trong receipt nhưng health projection chưa
   chiếu trường này, nên consumer không thể tự chứng minh receipt đến từ
   `attested_transport` thay vì chỉ tin cờ tổng hợp.
2. Một số guard Node tin `current_contract_observed` và exact process/server/SHA
   nhưng chưa so trực tiếp `receipt.activation_epoch_id` với epoch đang được
   full-clean xác minh.
3. Compatibility contact/bootstrap đã yêu cầu chữ ký verify nhưng chưa độc lập
   yêu cầu `identity_source=attested_transport`; đây là ambiguity không cần
   thiết ở trust boundary.

Source hiện đã đóng cả ba khe hở:

* `runtime_activity.py` chiếu `identity_source` nhất quán cho discovery,
  ordinary contact và activation bootstrap; busy/unavailable projection trả
  đầy đủ provenance null/false thay vì để consumer suy đoán;
* chỉ `attested_transport` cùng `attestation_verified=true` mới được ghi hoặc
  tính là current contact/bootstrap có quyền tham gia connector state;
* `fullCleanActivation.js`, `runtimeOrchestrator.js` và `recoveryHost.js` đều
  kiểm tra exact `identity_source`, `activation_epoch_id`, process instance,
  server instance, contract SHA và timestamp trước freshness, wake-up hoặc ACK;
* sai provenance trả `DISCOVERY_IDENTITY_SOURCE_INVALID` hoặc
  `COMPATIBILITY_BOOTSTRAP_IDENTITY_SOURCE_INVALID`; receipt của epoch khác trả
  `DISCOVERY_ACTIVATION_EPOCH_ID_MISMATCH` và không thể mở admission.

Regression mới chứng minh attestation không có explicit identity header vẫn là
`implicit_default` và không authoritative, kể cả khi HMAC hợp lệ; explicit
`chatweb` header cũng không authoritative; managed discovery hợp lệ mới chiếu
`identity_source=attested_transport`; receipt sai epoch và compatibility
bootstrap sai provenance đều bị từ chối fail-closed.

Proof của exact source wave:

```text
Node runtime/full-clean/Recovery focused                    132/132 PASS
Python attestation/bootstrap/stateless focused                33/33 PASS
Node repository suite                                       543/543 PASS
Python MCP full suite                740 PASS, 4 SKIPPED, 106 subtests PASS
Python module-size guard                                         PASS
source-root clean guard / repository secret check           PASS / PASS
```

Patch này supersede phần kiến trúc cũ trong advisory, nhưng chưa tự tạo live
proof. Epoch gần nhất vẫn là epoch đã hết hạn ở §37, còn runtime đang chạy chưa
được activate lại trên exact disk revision mới. Do đó trạng thái chấp nhận vẫn
là `admission=CLOSED`, strict current-process discovery chưa được chứng minh,
ACK chưa được phép và accepted baseline/P5 chưa được tạo.

Next live wave giữ đúng một chuỗi:

```text
fresh query-only census với active_agent_lanes=0
-> full-clean activation của exact disk revision
-> một real ChatWeb/Coding-VP tools/list hoặc server/discover qua managed tunnel
-> official receipt identity_source=attested_transport + attestation verified
-> exact epoch/process/server/SHA/revision + bốn strict connector flags
-> guarded ACK
-> current-epoch UI performance budget
-> mới xem xét immutable accepted baseline/P5
```

Không dùng raw HTTP, proxy identity, `workspace_context`, `tools/call`, catalog
tám tool hoặc textual receipt làm proof; không ACK giả và không reuse epoch đã
terminal.

## 39. Immutable baseline and P5 gate audit — 2026-08-29T14:21:41Z

Sau source/connector hardening, completion audit không thu hẹp P0.6 thành một
cờ `connector_rediscovered`. P0.6 yêu cầu một bundle bất biến gồm Git source,
workspace/runtime/contract identity, proof, lifecycle/projection convergence
và UI performance. P5 causal treatment là gate riêng, không phải phần được tự
mở chỉ vì P0.6 hoặc connector đã xanh.

Các reporter read-only chính thức cho trạng thái hiện tại:

```text
git HEAD / upstream                       c0aa335... / exact match
source_worktree_clean                     false
P4 state                                  COLLECTING
representative terminal shadows           99
repaired / nonrepaired / unknown          1 / 72 / 26
validated_signals                         []
p4_empirically_complete                   false
p5_baseline_ready                         false
p5_experiment_engineering_ready           false
p5_experiment_start_ready                 false
p5 controlled treatment may be opened     false
p5 causal efficacy ready                  false
latest P5 epoch                           EPOCH_HARD_STOPPED
```

`report_p5_baseline.py` tiếp tục chỉ quan sát organic history và không tạo
assignment/sample. Nó trả `canonical_readiness_passed=false`, current-source
accepted runs `0`, exact current-source window `false`, CAR unavailable và
monetary coverage `0`. `report_current_ledger_baseline.py` quan sát cohort rộng
hơn có `505` accepted runs (`297` first-pass, `208` repaired), nhưng đây vẫn là
descriptive history; không được dùng làm current-source incidence hoặc causal
effect. `report_accepted_result_economics.py` giữ
`decision_status=insufficient_head_window_volume` và
`missing_monetary_cost_is_zero=false`.

P5 arm-neutral planner được gọi không kèm bất kỳ claim eligibility nào và trả
`HOLD_ARM_NEUTRAL_ELIGIBILITY`, `production_behavior_changed=false`. Các cờ
false trong lượt plan này là facts chưa được caller khẳng định, không phủ định
census query-only đã chứng minh zero live owner; planner không enroll, assign,
open epoch hoặc reveal arm.

UI reporter của process/epoch hiện tại vẫn là receipt chưa đủ:

```text
activation epoch                   activation-mtefja7g-eab34afccae5db73bee23540af684af2
renderer/main/event-loop samples   10 / 20 / 214
normal IPC p95                     6.4 ms PASS
snapshot apply p95                 0.1 ms PASS
event-loop p95                     15.8 ms PASS
dashboard refresh p95              733.6 ms FAIL (<500)
overall readiness                  fail
```

Không loại cold-start outlier, không dùng cửa sổ PASS của epoch khác và không
backfill current-source accepted runs. Worktree có code-bearing WIP nên chưa
thể tạo Git/source identity bất biến; nhiệm vụ hiện cũng không ủy quyền commit.
Vì vậy accepted baseline và P5 vẫn `NOT CREATED / NOT STARTED`, đúng fail-closed
contract.

Thứ tự causal còn lại:

```text
1. real ChatWeb/Coding-VP strict discovery + guarded ACK trong fresh epoch
2. đủ UI samples và tất cả current-epoch budgets PASS
3. exact accepted/checkpointed source bundle
4. explicit scoped commit authority nếu cần clean upstream-matched baseline
5. recapture P0.6 bundle; chỉ ghi accepted baseline khi mọi field exact
6. P5 chỉ mở bằng explicit manifest/operator action cho natural eligible task;
   không synthetic enrollment, automatic start hoặc production promotion
```

Ba ordinary RUN dưới stale threshold vẫn được giữ nguyên; không biến chúng
thành false-green bằng early reconciliation hay direct SQLite edit.

## 40. Advisory verification: transport, supervisor and real-client provenance — 2026-08-29T14:42Z

Bản advisory mới đúng ở các điểm kiến trúc: raw localhost/identity header
không đủ; attestation phải bind client, epoch, MCP process, server process,
contract SHA, timestamp và nonce; compatibility bootstrap không thể đóng
full-clean; `blocked_live_owner` là fail-closed chứ không phải healthy; việc
respawn chỉ hợp lệ khi owner/lock đã chết; `tunnelId` là cấu hình chứ không tự
định danh vật lý; và `mcpAuthToken` không thay thế connector-attestation
binding. `npm start` cũng đúng là full-system refresh/reconcile surface.

Hai nhận định trong advisory không phải current proof:

1. `tunnel_client_not_seen >300s` không được xác nhận trên máy này. Cấu hình
   hiện tại là primary `tunnel_6a83e588bd788191b54a254c6a8d0d1d` và recovery
   `tunnel_6a83ea198fb88191997c0b508b5b56c1`; cả hai PID đang sống, `/healthz`
   và `/readyz` trả `200`, `metrics` có control-plane poll mới và lệnh
   `tunnel-client health --require-control-plane-poll` trả exit `0`. ID
   `tunnel_6a76a869a8088191aeeaf1628ac5e4fe` chỉ xuất hiện trong log cũ ngày
   08/08, nên không được dùng làm trạng thái hiện hành.
2. Runtime hiện không ở `blocked_live_owner`: trước khi sửa vận hành,
   `%LOCALAPPDATA%\\WebMcpRecoverySupervisor\\stop.request` còn tồn tại và
   Scheduled Task thoát ngay ở nhánh `stopping`, khiến `last_check_at=null`.
   Đây là sentinel suppression có chủ ý của development handoff, không phải
   health verdict. `npm run recovery:supervisor:install` đã được chạy qua
   installer hỗ trợ; sau đó script cài đặt khớp SHA checkout, sentinel biến
   mất, task `Running`, state `healthy`, `last_host_pid=50024`, không có restart
   attempt và không có lỗi.

Lượt kiểm tra Browser chỉ đọc trên đúng cuộc ChatGPT Work hiện có cho thấy
`Coding-VP` đã thực sự được chọn và đã gọi các tool `read_resource`,
`list_resources`, sau đó lặp `workspace_context` (call 6–15). Không thấy một
call `tools/list` hay `server/discover` mới trong danh sách call. Output cuối
của `workspace_context` là compatibility bootstrap với
`accepted=true`, `completed=false`, `retry_required=true`,
`workspace_accessed=false` cho epoch
`activation-mtefja7g-eab34afccae5db73bee23540af684af2`. Đây là bằng chứng
client/tunnel có đường tới MCP nhưng client đang dùng compatibility/schema
cache, chưa tạo strict discovery receipt; không được nâng thành
`connector_rediscovered=true`.

Fresh local evidence sau khi khôi phục supervisor:

```text
dev:status                 CURRENT / host=available / installation=current
running_revision == disk_revision                                      true
connector_state            UNCHANGED_ACKNOWLEDGED
connector_rediscovered     false; timestamp=none
connector_refresh_required false; connector_ack_pending=false
latest epoch               activation-mtefja7g... FAILED / CLOSED
failure                    ACTIVATION_REQUEST_EXPIRED at recovery_host_supervise

query-only census          2026-08-29T14:40:10.625Z
active_agent_lanes         0
active leases/fences/jobs/background operations                         0
unexplained active runs / unbound residues                              0 / 0
projection_drift / mutated_canonical_ledger                             false / false
integrity / foreign-key rows                                             ok / 0
physical snapshot SHA       a6c23d344b4fa2731dac796467d6bc75a9f050d92e7753404fd48559c2b0343a
logical snapshot SHA        3d6bfecf14bda3741dac796467d6bc75a9f050d92e7753404fd48559c2b0343a
```

Vì vậy advisory được hiệu chỉnh thành: source hardening đã đúng và transport
local hiện healthy; blocker thực tế là epoch cũ đã hết hạn và ChatWeb chưa
phát `tools/list`/`server/discover` xuyên Coding-VP cho process mới. Chưa chạy
`npm start` lần nữa để tránh mở một TTL mới khi chưa sẵn sàng gửi discovery;
chưa ACK và chưa tạo accepted baseline. Chuỗi còn lại vẫn bắt buộc:

```text
fresh census -> npm start (one full-clean epoch)
-> one real Coding-VP tools/list or server/discover
-> official attested receipt, exact epoch/process/server/SHA/revision
-> guarded ACK only on all strict flags
-> current-epoch UI budget
-> only then baseline/P5 consideration
```

## 41. Attested connector and current-epoch UI performance closure — 2026-08-29T20:15:03Z

Action-time confirmation đã được dùng để gửi follow-up kỹ thuật read-only tới
Coding-VP thật. Tin nhắn xuất hiện trong ChatWeb và không chứa secret/token hay
quyền ghi. Phản hồi `REJECT` của reviewer chỉ nói connector scratch không mở
được `E:\DEV\Codex-web`; nó không có source evidence và vì vậy không được dùng
để phủ định hoặc chấp nhận patch.

Live investigation sau đó đóng hai nguyên nhân còn lại của P0.5:

1. `live_control_snapshot()` trước đây tự chọn newest ledger row khi task-state
   projection không bind `run_id`. Ba row `active` dưới stale threshold vì thế
   bị biến từ durable observation thành UI authority, vừa sai semantics vừa tạo
   nhiều ledger reads trên mỗi poll. Live path nay chỉ theo exact projected
   `run_id`; không có binding thì trả `NO_ACTIVE_EXECUTION` và không đọc run đó.
2. `runtime_activity_snapshot()` trước đây gọi resource `snapshot()` có
   `reconcile()` và load toàn bộ `1053` hub clients, `6149` managed jobs cùng
   `427` claims rồi mới cắt cho UI. Read-model nay không reconcile/mutate; hub
   clients được limit trong SQL, job/claim counts dùng aggregate, visible rows
   dùng bounded `ORDER BY ... DESC LIMIT`, và managed job/claim reads dùng một
   connection/transaction.

Focused source proof của wave cuối:

```text
Recovery Plane / activation / host / runtime Node tests     162/162 PASS
Execution Hub / resources / coordination Python tests        49/49 PASS
Python module-size guard                                         PASS
git diff --check                                                  PASS
```

Census query-only ngay trước final activation:

```text
observed_at                       2026-08-29T20:09:05.374Z
physical SHA-256                  39fd23e8587eda19406d8c2542d167bff2292732a737b9699cc81b43eff3aa34
logical SHA-256                   e434419c6a1e18244c68ca72466d16f43d3ac526e43764808efc2396ab40dfc9
immutable / query_only            true / true
integrity                         ok
mutated_canonical_ledger          false
active_agent_lanes                0
managed_jobs                      0
unexplained active runs           0
unbound live residues             0
stale background residues         0
projection_drift                  false
ordinary active rows              3 THRESHOLD_SENSITIVE_STALE_CANDIDATE
```

Ba row dưới threshold không có controller lease, write fence, agent lane,
managed job hoặc background operation. Chúng được giữ nguyên; không early
reconcile và không direct SQLite edit.

Final full-clean/current-process receipt:

```text
activation_epoch_id               activation-mtetdl86-68c08c2f914e8049a4ebb4bf69833539
epoch / admission                 READY / OPEN
ready_at                          2026-08-29T20:10:41.630Z
Recovery Host instance            fb059ea3c630e1359f7c3b67b72eeba5
Coding MCP process/server         9RkQbeqAUay5_LRD / 4OtFTiY9AnN5C8Po
Coding Tunnel instance            607c0265ca2aad89c508836f
Electron UI instance              2709389fe3f50d3202ae67a25b3b7218
MCP running_revision == disk      68f0a59095855c4250f85bc72a7784ffafca99b424e73158a95948d1112ceff6
UI running_revision == disk       e7cd3ef84da65ea0165ab657c7968334873436359b30ec65447771c9857dae74
process/tunnel identity changed   true / true
```

Discovery được tạo bằng đúng một lần `Làm mới` trên connection Coding-VP Live
cho process mới, không gửi model text để giả catalog, không raw localhost và
không ACK thủ công. Official status sau Recovery Host guarded ACK:

```text
state / installation              CURRENT / current
connector_state                   CURRENT_ACKNOWLEDGED
connector_rediscovered            true
connector_rediscovered_at         2026-08-29T20:10:30.820587Z
connector_freshness_mode          current_process_discovery
connector_refresh_required        false
connector_ack_pending             false
connector_current_sha == ack_sha  c244ed297f707f9df48c1e5d6c7e204693f281a755c2e6344bde78e94abb8251
error_code                        none
```

Direct official Recovery IPC có `n=20`, p50 `1.92 ms`, p95 `3.07 ms`, max
`12.79 ms`. Exact current UI/epoch window giữ cả cold-start outlier và đạt:

```text
renderer / main / event-loop samples   25 / 50 / 558
event-loop p95                          15.6 ms  PASS (<50)
normal IPC p95                          44.2 ms  PASS (<100)
snapshot apply p95                       0.0 ms  PASS (<50)
dashboard refresh p95                   66.2 ms  PASS (<500)
overall readiness                       pass
```

Vì vậy P0.3 live runtime/connector convergence và P0.5 current-epoch UI
performance hiện đóng cho exact local process này. P0.6 vẫn chưa được tạo:
worktree chứa code-bearing WIP chưa có immutable accepted/checkpointed Git
identity, nhiệm vụ chưa cấp scoped commit authority, và strict baseline vẫn
phải xử lý ba ordinary active rows qua đúng threshold/authority thay vì làm
false-green. P5 treatment/efficacy tiếp tục `HOLD_NATURAL_EVIDENCE`; không tạo
synthetic enrollment/workload và không suy causal outcome từ technical PASS.

Không commit, push, package, release, deploy hoặc production operation xảy ra
trong checkpoint này.
