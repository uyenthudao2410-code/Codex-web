# CODING WEB — BREAKTHROUGH IMPLEMENTATION METHODOLOGY
## From AI Coding Orchestrator to Trusted Problem Resolution Engine

**Ngày ban hành:** 2026-08-28  
**Workspace áp dụng:** `E:\DEV\Codex-web`  
**Representative natural workload:** `E:\DEV\HR STA\HR`  
**Loại tài liệu:** implementation methodology / architecture operating model / migration specification / engineering execution doctrine  
**Trạng thái:** **IMPLEMENTATION-READY — thay thế tư duy feature-first bằng Problem-Resolution-first**

---

# 0. Mục đích tài liệu

Tài liệu này không mở thêm một chương trình nghiên cứu. Nó chuyển toàn bộ evidence đã tích lũy thành **một phương pháp triển khai quyết đoán**.

Hai tài liệu nền vẫn giữ vai trò:

```text
docs/research/260826_CODING_WEB_USER_PROBLEM_RESOLUTION_FIRST_METHODOLOGY_AND_STRATEGIC_DIRECTION.md

docs/research/260828_CODING_WEB_TARGET_STATE_GAP_ANALYSIS_AND_COMPLETION_PLAN.md
```

Tài liệu hiện tại trả lời câu hỏi khác:

> **Từ ngày 28/08/2026, phải tổ chức lại Coding Web như thế nào để biến toàn bộ tri thức, runtime, EOCL, PRL, model lanes và telemetry hiện có thành một hệ thống giải quyết vấn đề phần mềm nhanh, bền vững và ít cần người dùng nhắc lại?**

Mục tiêu không phải mô tả thêm architecture. Mục tiêu là tạo một **engineering operating system** đủ chi tiết để triển khai.

---

# 1. Executive mandate — quyết định chiến lược đã chốt

## 1.1. Dừng tối ưu machinery như sản phẩm

Coding Web không tiếp tục được phát triển theo logic:

```text
thêm tool
→ thêm RUN/WAVE state
→ thêm router
→ thêm model
→ thêm cache
→ thêm dashboard metric
→ thêm recovery object
```

Dữ liệu lịch sử đã đủ để chỉ ra rằng các chi phí lớn nằm ở:

```text
rework / repair
localization lại từ đầu
wait / control friction
runtime/source divergence
wrong target / wrong scope
weak outcome oracle
false closure
context reconstruction
long-lived execution sessions
```

Do đó mandate mới là:

> **Build less machinery. Make the runtime remember more. Make each problem converge faster.**

---

## 1.2. North Star duy nhất

```text
TTPR = Time to Trusted Problem Resolution
```

Secondary economics:

```text
First-Pass Trusted Resolution
Same-Problem Reopen Rate
User Correction Turns / Problem
Total Expected Work / Trusted Resolution
Avoidable Governance Friction
```

Không coi các chỉ số sau là North Star:

```text
model latency riêng lẻ
tool-call count
RUN count
WAVE count
proof count
cache hit rate
LSP use rate
model utilization
worker utilization
```

---

## 1.3. Ba thay đổi tạo đột phá

### Breakthrough A — Runtime remembers code

```text
MODEL SHOULD NOT RE-DISCOVER THE REPOSITORY EVERY TURN.
```

Repository structure, symbols, dependencies, schemas, routes, tests, change map và ownership phải được runtime duy trì như derived intelligence.

### Breakthrough B — System owns the Problem, not the RUN

```text
USER PROBLEM = product/economic unit
RUN/WAVE       = internal execution provenance
```

Một problem có thể sống xuyên:

- nhiều model;
- nhiều context;
- nhiều RUN/WAVE;
- nhiều runtime generation;
- nhiều máy;
- nhiều ngày;

mà vẫn là cùng một Problem Revision nếu user contract không đổi.

### Breakthrough C — Control plane is conditional

EOCL, lease, fencing, multi-wave coordination và deep orchestration chỉ được kích hoạt khi rủi ro thực sự cần chúng.

Default bounded task phải đi:

```text
LOCATE → CHANGE → VERIFY → RESOLVE
```

không phải:

```text
ORCHESTRATE → ORCHESTRATE → ORCHESTRATE → MAYBE CHANGE
```

---

# 2. Evidence đã đủ để chuyển pha

## 2.1. Rework là economic multiplier

Historical Codex cohort:

```text
first-pass accepted     ≈ 69.15%
repaired                ≈ 30.85%
first-pass TTA p50      ≈ 36.4 s
repaired TTA p50        ≈ 192.3 s
median repair penalty   ≈ 5.29x
```

Điều này đủ để chốt:

> **Giảm xác suất repair quan trọng hơn chỉ giảm vài giây một model call.**

---

## 2.2. Localization là critical-path cost

Historical + current telemetry cho thấy localization chiếm tỷ trọng lớn trong các phase có instrumentation; HR có nhiều localization operation kéo hàng chục giây.

Do đó:

> **Repository memory phải chuyển từ model-side transient context sang runtime-side durable derived state.**

---

## 2.3. Proof cache và LSP chưa phải leverage chính

Evidence hiện có cho thấy:

```text
proof cache hit ≈ negligible
LSP handled     ≈ negligible trên tổng localization workload
```

Kết luận triển khai:

- không xóa ngay;
- không đầu tư như P0/P1;
- chỉ giữ như optional datasource/optimization;
- mọi đầu tư mới phải chứng minh TTPR contribution trên natural workload.

---

## 2.4. HR chứng minh orchestration friction là real workload cost

Trong HR, VALIDATION + AUTHORITY_DENIED chiếm tỷ trọng lớn trong error taxonomy. Điều này chứng minh nhiều failure không phải do model không biết code, mà do:

```text
schema mismatch
admission mismatch
authority mismatch
wrong execution contract
runtime/source divergence
workflow friction
```

Do đó control-plane simplification là feature tạo user value trực tiếp.

---

## 2.5. Long-lived Sol/deep-lane run không phải long-context solution

Một persistent HR run có hơn 1.000 tool calls kéo nhiều ngày. Đây là bằng chứng rằng:

```text
persistent model thread != durable project understanding
```

Target phải là:

```text
Disposable model process
+ Durable resolution state
+ Durable workspace intelligence
```

---

# 3. Product definition mới

Coding Web được định nghĩa lại là:

> **Trusted Problem Resolution Engine — một hệ thống nhận problem phần mềm từ người dùng, đồng bộ đúng workspace/runtime, dùng repository intelligence để định vị causal boundary nhanh, thực thi intervention nhỏ nhất qua execution kernel, chỉ dùng coordination khi cần, duy trì state xuyên context/model/máy, và chỉ đóng problem khi outcome thực tế được chứng minh trong bounded Resolution Envelope.**

One-line doctrine:

> **Runtime remembers. Problems persist. Models are disposable. Execution stays small. Authority appears only when risk earns it. Closure is outcome-based.**

---

# 4. Target architecture — 5 engine model

```text
┌────────────────────────────────────────────────────────────┐
│ 1. PROBLEM RESOLUTION ENGINE                              │
│ Problem · Revision · Frame · Outcome · Resolution          │
└──────────────────────────────┬─────────────────────────────┘
                               │
┌──────────────────────────────▼─────────────────────────────┐
│ 2. WORKSPACE INTELLIGENCE ENGINE                          │
│ Symbols · Graph · Schemas · Tests · Change Map · Owners   │
└──────────────────────────────┬─────────────────────────────┘
                               │
┌──────────────────────────────▼─────────────────────────────┐
│ 3. EXECUTION KERNEL                                       │
│ Read · Search · Patch · Git · Command · Test · Build      │
└──────────────────────────────┬─────────────────────────────┘
                               │
┌──────────────────────────────▼─────────────────────────────┐
│ 4. TRUST & COORDINATION                                   │
│ EOCL · Lease · Fence · Proof · Approval · Handoff         │
└──────────────────────────────┬─────────────────────────────┘
                               │
┌──────────────────────────────▼─────────────────────────────┐
│ 5. RUNTIME READ MODEL                                     │
│ Events → Projectors → Snapshots → IPC/UI                  │
└────────────────────────────────────────────────────────────┘
```

Đây là **logical architecture**. Không mặc định tạo 5 service/process/database mới.

Quy tắc implementation:

```text
LOGICAL BOUNDARY FIRST
SERVICE BOUNDARY ONLY IF MEASURED NEED EXISTS
```

---

# 5. Authority map — một fact chỉ có một authority

| Concern | Canonical authority |
|---|---|
| User problem | `problem_id + problem_revision` |
| User-level contract | Problem Revision contract capsule |
| Current causal understanding | Problem Frame revision |
| Workspace | `workspace_id + workspace_generation` |
| Source | Git HEAD + source/worktree fingerprint |
| Runtime | process/runtime generation identity |
| Concrete execution | operation/job identity |
| Concurrent mutation | write lease/fence |
| Technical evidence | proof + exact fingerprint |
| Accepted technical state | checkpoint |
| UI state | derived read-model snapshot only |
| Context continuation | Resolution Capsule; never authority |
| Repository intelligence | derived/rebuildable cache; never authority |

Forbidden:

```text
UI state granting authority
context capsule granting authority
model memory granting authority
ambient current-session inference granting authority
old proof granting authority after source/runtime drift
```

---

# 6. Core ontology

## 6.1. Problem

Problem là identity semantic xuyên suốt.

```yaml
problem:
  problem_id:
  created_at:
  workspace_binding:
  current_revision:
  state:
```

State tối thiểu:

```text
OPEN
PROVISIONALLY_RESOLVED
RESOLVED_CONFIRMED
REOPENED
BLOCKED
SUPERSEDED
ABANDONED
```

Không thêm state nếu state mới không thay đổi một decision/gate thật.

---

## 6.2. Problem Revision

Revision chỉ thay đổi khi **user contract thay đổi vật chất**.

```yaml
problem_revision:
  revision:
  objective:
  desired_outcome:
  acceptance_criteria:
  protected_invariants:
  constraints:
  excluded_scope:
  contract_fingerprint:
```

Không revise chỉ vì:

- hypothesis đổi;
- file target đổi;
- root cause đổi;
- model đổi;
- runtime đổi;
- RUN mới được tạo.

---

## 6.3. Problem Frame

Frame là current causal hypothesis.

```yaml
problem_frame:
  frame_id:
  problem_revision:
  observation:
  boundary:
  governing_invariants:
  ownership:
  hypotheses:
  evidence:
  counterevidence:
  falsifiers:
  next_discriminator:
```

Frame có thể đổi nhiều lần:

```text
R1/F0 → R1/F1 → R1/F2
```

mà Problem Revision vẫn là R1.

---

## 6.4. Attempt

Attempt liên kết execution với Problem Revision.

```yaml
attempt:
  attempt_id:
  problem_id:
  problem_revision:
  frame_id:
  run_id:
  wave_id:
  route:
  source_fingerprint:
  intervention_scope:
  result:
```

RUN/WAVE không còn được dùng như denominator product.

---

## 6.5. Evidence

```yaml
evidence:
  evidence_id:
  type:
    - SOURCE
    - TEST
    - CONTRACT
    - RUNTIME
    - DATA
    - UI
    - USER_OUTCOME
  claim_supported:
  provenance:
  fingerprint:
  status:
  observed_at:
```

Technical evidence không tự promote thành USER_OUTCOME.

---

## 6.6. Resolution Claim

```yaml
resolution_claim:
  problem_id:
  revision:
  statement:
  direct_outcomes:
  governing_invariants:
  relevant_truth_domains:
  required_evidence:
  falsification_probe:
  excluded_scope:
```

`RESOLVED_CONFIRMED` chỉ khi claim đủ evidence tương xứng.

---

# 7. Resolution Capsule — giải bài toán context dài

## 7.1. Nguyên tắc

> **Model must be disposable; state must be durable.**

Không lưu chain-of-thought. Không replay full conversation. Không dựa vào một giant model thread.

Resolution Capsule là compact state có thể tái dựng từ authority + derived state.

```yaml
resolution_capsule:
  capsule_id:

  problem:
    id:
    revision:
    objective:
    acceptance_criteria:
    protected_invariants:

  workspace:
    endpoint_id:
    workspace_id:
    generation:
    head:
    worktree_fingerprint:

  frame:
    current_frame_id:
    observation:
    boundary:
    governing_invariants:
    active_hypotheses:
    material_counterevidence:

  execution:
    current_attempt:
    active_authority:
    write_lease:

  evidence:
    valid_proofs:
    invalidated_proofs:
    runtime_identity:
    outcome_evidence:

  current_gap:
    unresolved_conditions:

  next_action:
    type:
    target:
    reason:
```

---

## 7.2. Capsule lifecycle

Create/update only when material state changes:

```text
problem opened
contract revised
frame changed
source changed
runtime generation changed
proof generated/invalidated
authority changed
problem provisionally resolved
problem reopened
```

Không update sau mỗi log line/tool call.

---

## 7.3. Fresh-context recovery

```text
NEW MODEL / NEW CHAT / RECONNECT
        ↓
workspace_context
        ↓
validate workspace + source freshness
        ↓
load/rebuild compact Resolution Capsule
        ↓
load only relevant Workspace Intelligence slice
        ↓
continue from next causal action
```

Forbidden:

```text
replay thousands of tool calls
re-read entire repository
infer live state from previous narrative
```

---

# 8. Workspace Intelligence Engine

## 8.1. Mục tiêu

Biến localization từ repeated expensive discovery thành **incremental lookup**.

Target:

```text
User asks about revenue mismatch
        ↓
Problem classifier identifies concepts
        ↓
Workspace Intelligence returns:
  canonical finance source
  consumers
  calculation symbols
  schema fields
  tests
  recent changes
  runtime owner
        ↓
model receives bounded causal packet
```

---

## 8.2. Derived intelligence model

```yaml
workspace_intelligence:
  workspace_identity:
  source_fingerprint:

  files:
    path:
      fingerprint:
      language:
      role:

  symbols:
    symbol_id:
    path:
    range:
    kind:
    exported:

  dependencies:
    imports:
    calls:
    consumes:
    produces:

  interfaces:
    http_routes:
    ipc_channels:
    database_tables:
    config_keys:
    events:

  tests:
    test_id:
    target_symbols:
    target_paths:
    command:

  ownership:
    semantic_owner:
    runtime_owner:
    writable_by:

  recent_changes:
    files:
    symbols:
    fingerprints:
```

Derived state phải:

```text
rebuildable
bounded
versioned by source fingerprint
invalidated incrementally
never grant authority
```

---

## 8.3. Incremental update algorithm

### Initial build

```text
1. enumerate repository once
2. fingerprint files
3. parse supported languages
4. extract symbols/imports/routes/tests/schema
5. create dependency edges
6. persist derived snapshot outside source truth
```

### On file change

```text
changed file
  ↓
new fingerprint
  ↓
reparse file only
  ↓
remove old outgoing/incoming derived edges as needed
  ↓
add new edges
  ↓
update impacted symbol/test/route slices
  ↓
increment intelligence revision
```

No full repository scan on every prompt.

---

## 8.4. Intelligence storage policy

Preferred characteristics:

```text
runtime data root, not tracked source
local to workspace/runner
rebuildable
content-safe indexes
versioned by workspace generation + source fingerprint
```

Do not create a second business authority database.

Intelligence store = cache/index.

Ledger/Problem state = durable authority/evidence.

---

## 8.5. LSP role

LSP becomes one optional extractor/provider:

```text
Workspace Intelligence
    ├─ static parser
    ├─ language-specific parser
    ├─ Git/change analyzer
    ├─ schema extractor
    └─ LSP provider (when healthy)
```

Never:

```text
Workspace Intelligence == LSP
```

If LSP unavailable, system remains functional.

---

## 8.6. Intelligence query contract

Queries should be semantic but bounded:

```yaml
query:
  concepts:
  suspected_symbols:
  changed_since:
  evidence_needed:
  max_files:
  max_symbols:
  max_bytes:
```

Result should prioritize:

```text
canonical owners
highest-confidence dependency edges
recently changed relevant surfaces
existing tests/oracles
runtime/source boundaries
```

Not dump raw repository inventory.

---

# 9. Fast Path — default execution model

## 9.1. Eligibility

Fast Path dùng khi tất cả điều kiện sau đúng hoặc không có contradiction material:

```text
workspace exact
problem revision clear
single writer
no destructive/high-risk operation
causal scope bounded
oracle strong or adequate
no unresolved source/runtime ambiguity
no need for distributed coordination
```

---

## 9.2. Fast Path flow

```text
1. SYNC
   workspace/source/runtime identity

2. RESOLVE PROBLEM CONTEXT
   Problem Revision + Resolution Capsule

3. INTELLIGENCE LOOKUP
   get smallest relevant repository slice

4. DISCRIMINATE
   cheapest check separating plausible causes

5. CHANGE
   smallest coherent causal intervention

6. PROVE
   focused authoritative oracle

7. RUNTIME/OUTCOME CHECK
   only relevant truth domains

8. RESOLVE OR REOPEN
   close bounded claim or update frame
```

---

## 9.3. Fast Path must feel atomic to operator

User-facing experience:

```text
“Sửa lỗi X.”

→ system works
→ returns resolved result / exact blocker
```

User không cần nhìn thấy:

```text
RUN created
wave 1
wave 2
routing policy
lease ceremony
proof plumbing
```

trừ khi material risk/blocker cần operator decision.

---

# 10. EOCL Material Path — chỉ khi risk kiếm được chi phí coordination

## 10.1. Activation conditions

EOCL full material path được kích hoạt khi có một hoặc nhiều điều kiện:

```text
multiple writers
parallel independent workstreams
high integration width
financial/business-critical semantics
auth/security/privacy boundary
destructive migration
long-running command/process
cross-machine execution
handoff between controllers
proof reuse across sessions
release/deploy/production action
source/runtime replacement
```

---

## 10.2. Material Path

```text
Problem Revision
      ↓
settled shared invariants
      ↓
Task / bounded workstreams
      ↓
EOCL authority + leases + fences
      ↓
operations / lanes
      ↓
proof
      ↓
technical acceptance
      ↓
runtime/outcome verification
      ↓
Resolution Claim
```

EOCL vẫn là authority/proof mechanism mạnh; chỉ bỏ việc dùng nó như ceremony phổ quát.

---

## 10.3. Escalation from Fast → Material

Fast Path phải escalate nếu phát hiện:

```text
competing writer
source drift
scope expands cross-subsystem
oracle weakens
high-risk data mutation
multiple independent causal leaves
runtime replacement needed
```

Escalation preserves same Problem Revision and current Frame evidence. Không mở problem mới.

---

# 11. Router simplification

## 11.1. Router chỉ trả lời ba câu hỏi

```text
Q1. Can deterministic execution solve it?
Q2. If not, is semantic scope settled and bounded?
Q3. If not, does it require Sol-level integration/reasoning?
```

Conceptual route:

```text
DETERMINISTIC
    ↓ if insufficient
BOUNDED CHEAP MODEL CANDIDATE
    ↓ if insufficient / semantics broad
SOL / DEEP REASONING
```

Exact model names/tier phải tuân runtime authorization; methodology không hard-code availability.

---

## 11.2. Router optimization objective

```text
Minimize Expected Cost to Trusted Resolution
```

Không:

```text
Minimize Cost per Call
```

Model rẻ hơn nhưng tăng repair/reopen không được coi là tốt hơn.

---

## 11.3. No giant persistent run as memory

Hard rule:

> **A model lane must never become the canonical persistence layer for project/problem state.**

Long-running lane chỉ tồn tại vì work execution cần nó, không vì hệ thống chưa có context recovery.

---

# 12. Execution Kernel

## 12.1. Kernel responsibilities

```text
repository reads
bounded search
canonical patch/edit
Git inspection
command execution
job control
test/build
bounded outputs
permissions
workspace containment
```

Kernel không sở hữu:

```text
user problem semantics
final outcome authority
business meaning
routing policy as product truth
UI state
```

---

## 12.2. One canonical mutation path

Mỗi mutation class phải có canonical writer semantics.

Không để tồn tại nhiều đường:

```text
UI edit
raw HTTP edit
shell sed edit
MCP patch
recovery script edit
```

cho cùng một authority class nếu không có lý do rõ.

Preferred:

```text
model/tool proposes causal change
→ runtime validates scope/fingerprint/authority
→ canonical mutation primitive applies atomically
```

---

## 12.3. Bounded result contract

Every potentially large result:

```text
summary
high-value slice
bounded tail/page
continuation handle
source fingerprint
```

No repeated full-output replay.

---

# 13. Runtime Read Model — giải quyết UI lag và truth divergence

## 13.1. UI không được query control plane nặng trong render path

Forbidden render dependencies:

```text
full SQLite scan
Git status reconstruction
filesystem traversal
runtime process census
proof aggregation
network health query fan-out
full task ledger reconstruction
```

---

## 13.2. Target flow

```text
RUNTIME EVENTS
      ↓
INCREMENTAL PROJECTORS
      ↓
READ MODEL
      ↓
IMMUTABLE VERSIONED SNAPSHOT
      ↓
IPC
      ↓
ELECTRON UI
```

Mutation path:

```text
UI COMMAND
   ↓
RUNTIME HANDLER
   ↓
DURABLE EVENT/STATE
   ↓
PROJECTOR UPDATE
   ↓
NEW SNAPSHOT
   ↓
UI
```

---

## 13.3. Snapshot schema

```yaml
runtime_snapshot:
  snapshot_id:
  generated_at:
  source_revision:
  runtime_revision:
  workspace:
  health:
  task_summary:
  problem_summary:
  operations_summary:
  performance_summary:
  alerts:
  stale_age_ms:
```

UI reads snapshot, not authority databases directly.

---

## 13.4. Projector principles

```text
incremental
idempotent
bounded
rebuildable from durable facts
content-minimal
cheap to serialize
coalesce noisy telemetry
```

Separate projectors:

```text
runtime health projector
workspace/source projector
orchestration projector
problem-resolution projector
performance projector
```

Do not force one mega projector if it creates lock contention.

---

## 13.5. Performance acceptance budgets

Initial engineering budgets; calibrate on real operator machine:

```text
UI event-loop p95                    < 50 ms
normal IPC p95                       < 100 ms
snapshot apply p95                   < 50 ms
initial action feedback              < 150 ms perceived
cached dashboard refresh             < 500 ms
no unbounded synchronous scan        REQUIRED
snapshot stale age under active work visible to operator
```

Do not add more UI metrics until these budgets drive a concrete decision.

---

# 14. Operational source/runtime separation

## 14.1. Four classes of state

```text
A. SOURCE STATE
   code, schemas, config intended for version control

B. RUNTIME STATE
   process identity, leases, task contexts, caches

C. DURABLE AUDIT/EVIDENCE
   ledger, checkpoints, proof receipts

D. DERIVED/GENERATED STATE
   indexes, read models, reports, performance summaries
```

These classes must not be conflated.

---

## 14.2. Git/worktree rule

Normal runtime activity must not make the repository appear source-dirty unless a tracked source/config artifact truly changed.

Derived intelligence/read-model/cache must be stored in runtime data root or ignored derived area.

Durable audit evidence may remain local and immutable without being source identity.

---

## 14.3. Source fingerprint rule

Source fingerprint must represent source semantics, not noisy operational churn.

But do not exclude a file merely because it is inconvenient: if it changes behavior/configuration, it belongs in source identity.

---

# 15. Problem Resolution Engine decision loop

## 15.1. Canonical algorithm

```text
INPUT: user problem / follow-up

1. Bind Problem Revision
2. Synchronize workspace/source/runtime
3. Recover current Resolution Capsule
4. Retrieve smallest relevant Workspace Intelligence slice
5. Compare normative contract vs observed state
6. Form/update causal Frame
7. Choose cheapest decision-changing discriminator
8. Execute smallest causal intervention
9. Run focused oracle
10. Verify relevant runtime/data/UI outcome
11. Run credible falsification probe when risk justifies
12. RESOLVE, REOPEN, BLOCK or REVISE
```

---

## 15.2. No same-frame retry after material counterevidence

Hard doctrine:

```text
MATERIAL COUNTEREVIDENCE
        ↓
UPDATE / EXPLAIN FRAME
        ↓
ONLY THEN MUTATE AGAIN
```

Không retry cùng patch family chỉ vì model nghĩ “thử lại”.

---

## 15.3. Boundary expansion discipline

Broaden problem boundary only when current frame cannot explain evidence.

Every expansion must answer:

```text
What contradiction requires wider scope?
What additional fact becomes relevant?
What observation could falsify this wider frame?
```

---

# 16. Natural workload strategy — HR trở thành product benchmark

## 16.1. Vai trò của HR

HR không phải secondary demo app. Nó là **representative natural workload** để chứng minh Coding Web có giải quyết software problems thật hay không.

Nó cung cấp:

```text
React UI
Node backend
PostgreSQL
business finance semantics
cross-tab consistency
runtime issues
persistence issues
real user corrections
repeated reopened problems
natural latency
```

---

## 16.2. Golden natural problem families

Ưu tiên reconstruct/observe các family:

```text
1. Finance revenue consistency
2. Payment / settlement / receivable / warranty semantics
3. Project → Finance data propagation
4. Project status/save/reload consistency
5. Modal open/save latency and persistence
6. PostgreSQL local runtime startup
7. Contract / appendix lifecycle
8. Invoice state/date lifecycle
9. Personnel / ManagingUnit canonical identity
10. Source correct but runtime stale
```

---

## 16.3. Benchmark denominator

Never:

```text
RUN count
WAVE count
model-call count
```

Use:

```text
Problem Revision
```

Each case records:

```yaml
case:
  problem_revision:
  initial_observation:
  first_action_at:
  first_mutation_at:
  technical_acceptance_at:
  runtime_current_at:
  trusted_resolution_at:
  correction_turns:
  reopen:
  total_attempts:
```

---

# 17. Minimal metrics policy — dừng metric proliferation

Only six product/engineering metrics are mandatory for the next architecture cycle:

```text
1. TTPR p50/p90
2. First-Pass Trusted Resolution Rate
3. Same-Problem Reopen Rate
4. User Correction Turns / Problem
5. Localization Time / Problem
6. Avoidable Governance Friction / Problem
```

Optional diagnostic metrics only when they answer a current engineering question.

Hard rule:

> **A new metric requires a documented decision it can change.**

If no decision changes based on a metric, do not add it.

---

# 18. What to freeze, demote, remove or postpone

## 18.1. Freeze feature expansion

Until P0/P1 exit criteria pass:

```text
NO new public MCP tools
NO new RUN/WAVE states
NO new authority objects
NO second Session authority
NO giant router rewrite
NO full upstream merge
NO autonomous multi-agent expansion
NO new proof cache investment
NO LSP-first architecture rewrite
```

---

## 18.2. Demote

```text
task_context_id       → continuation handle, not business authority
RUN/WAVE              → execution provenance
model thread          → disposable execution context
LSP                   → optional intelligence provider
proof cache           → opportunistic optimization
UI state              → projection only
```

---

## 18.3. Remove candidates

Audit and remove/collapse if duplicate:

```text
ambient workspace fallback
implicit target/session binding
recovery scripts duplicating canonical supervisor
reports that dirty source worktree automatically
unused routing states
telemetry with no decision consumer
duplicate runtime health scans
UI-owned authority assumptions
multiple source currentness definitions
```

---

# 19. Migration strategy — Strangler, not rewrite

## 19.1. Không rewrite core hiện tại

Existing strengths must remain:

```text
smart-v3 tool surface
workspace identity
EOCL
write leases/fences
proof/checkpoint
activation/recovery
Problem Resolution Lineage
performance telemetry
Codex lanes
```

New architecture wraps/reassigns responsibilities gradually.

---

## 19.2. Migration sequence

```text
CURRENT SYSTEM
     ↓
1. Converge runtime/source/control contracts
     ↓
2. Add read-model projection in parallel with existing UI reads
     ↓
3. Switch UI surfaces one by one to snapshot reads
     ↓
4. Add Workspace Intelligence as derived cache beside current search
     ↓
5. Route localization to intelligence-first, fallback to current search
     ↓
6. Add durable Resolution Capsule projection from existing PRL/EOCL
     ↓
7. Introduce Fast Path semantics for eligible bounded work
     ↓
8. Keep EOCL material path for risk/coordination
     ↓
9. Introduce distributed Runner only after single-host convergence
```

Every migration step must have rollback to existing behavior until proven.

---

# 20. Phase P0 — Operational Convergence

P0 is not optional. No breakthrough architecture will work on divergent runtime/source/control state.

Live planning snapshot on 2026-08-28 when this document was created:

```text
workspace                          E:\DEV\Codex-web
branch                             main
HEAD                               2cc0eefc7d881827ef44e4d1584d84bbd9e494b6
worktree                           DIRTY
runtime_version                    0.4.3
smart-v3 tools                     8
unresolved stale orchestration     68
task projection reconciled         false
semantic localization              NATIVE_LSP_BINDING_NOT_CONFIGURED
```

These numbers are live planning evidence, not permanent doctrine.

---

## P0.1 — Fix control target contract

Goal:

```text
workspace_context
→ task_control read-only observation
```

must work without creating a RUN and without hidden ambient inference.

Implementation requirements:

```text
- one explicit read-only workspace target contract
- client schema == server schema
- multi-workspace regression tests
- stale/unknown target fails closed
- mutation path still binds run/wave authority
```

Exit:

```text
No schema/authority deadlock.
```

---

## P0.2 — Reconcile stale lifecycle

Do not bulk-delete.

Classify each stale row:

```text
terminal-but-unreconciled
superseded source
abandoned pre-write
lost controller
expired lease
proof complete / acceptance missing
runtime interruption
invalid/corrupt state
```

Canonical actions only:

```text
reconcile
abort
supersede
accept/reject where authority/evidence permits
manual review
```

Exit:

```text
unresolved stale = 0 or documented explicit exempt anchors
projection reconciled
no stale write authority
no stale rows rendered active
```

---

## P0.3 — Source/runtime currentness

Define one truth:

```text
CURRENT iff
running generation corresponds exactly to intended loaded source/package revision
```

Exit:

```text
running_revision == intended_disk_revision
update_pending=false
stale process cannot claim CURRENT
```

---

## P0.4 — Read-model foundation

Before rewriting full dashboard:

```text
1. define runtime snapshot schema
2. implement source/runtime projector
3. implement orchestration summary projector
4. expose one snapshot IPC
5. migrate one dashboard card/surface
6. compare against existing data
7. expand only after correctness + latency proof
```

---

## P0.5 — Source/runtime/derived-state hygiene

Inventory `.coding-tools` and all local operational files.

Every artifact must get classification:

```text
SOURCE
RUNTIME
AUDIT
DERIVED
TEMP
```

Exit:

```text
normal runtime activity no longer creates ambiguous source dirty state
```

---

## P0.6 — Immutable accepted baseline

Baseline bundle:

```yaml
baseline:
  git_head:
  source_fingerprint:
  runtime_revision:
  workspace_id:
  workspace_generation:
  tool_contract_sha:
  stale_count:
  projection_state:
  focused_proof_bundle:
  ui_latency_baseline:
```

No P2/P3 architecture expansion before an accepted baseline exists.

---

# 21. Phase P1 — Workspace Intelligence + Read Model

P1 is the first actual breakthrough implementation phase.

## P1.1 — Build file fingerprint index

Requirements:

```text
path
size
mtime (diagnostic only)
content hash / semantic hash
language
source revision
```

Change detection must use reliable fingerprint, not mtime alone.

---

## P1.2 — Symbol/import graph

Start with languages actually material to Codex-web/HR.

Do not build universal compiler framework.

Minimum useful extraction:

```text
JS/TS imports/exports
functions/classes
React components/hooks
Node service/module references
Python modules/functions/classes
HTTP routes
IPC channel names
SQL/table/schema references
package scripts/test commands
```

---

## P1.3 — Test-to-source mapping

Infer from:

```text
imports
naming conventions
explicit command metadata
historical proof paths
```

Confidence must be explicit:

```text
EXACT
HIGH_CONFIDENCE
HEURISTIC
UNKNOWN
```

No heuristic test mapping may grant acceptance authority.

---

## P1.4 — Change-aware intelligence

Every accepted/source change updates only impacted slices.

Intelligence revision must bind:

```text
workspace generation
source fingerprint
```

Stale intelligence can suggest nothing until refreshed/rebuilt.

---

## P1.5 — Intelligence-first localization

New localization sequence:

```text
Problem concepts
→ intelligence query
→ exact/high-confidence owners/tests
→ bounded source read
→ fallback search only if required
```

Measure only:

```text
Localization Time / Problem
```

No need for dozens of indexing metrics.

---

# 22. Phase P2 — Problem Resolution Engine + Durable Context

## P2.1 — Canonical Problem binding

Every user-originated engineering objective should either:

```text
OPEN new Problem
LINK to existing Problem Revision
or explicitly classify as non-problem/admin/read-only
```

No silent objective-string grouping.

---

## P2.2 — Resolution Capsule projector

Prefer deriving capsule from existing PRL/EOCL/source/runtime evidence instead of creating a second mutable database.

Projector should emit compact versioned capsule.

---

## P2.3 — Frame evolution

Frame packet stays bounded and structured.

Minimum hard rule to promote:

```text
material counterevidence requires frame update/explanation before same-family mutation retry
```

No numeric LLM confidence gate.

---

## P2.4 — Provisional vs confirmed closure

```text
technical acceptance
→ PROVISIONALLY_RESOLVED

independent/relevant outcome evidence
→ RESOLVED_CONFIRMED

same-contract failure
→ REOPENED
```

This bridge is central to preventing false closure.

---

# 23. Phase P3 — Fast Path

## P3.1 — Eligibility classifier

Classifier should be deterministic/rule-first where possible.

```yaml
fast_path_eligibility:
  exact_workspace: true
  single_writer: true
  bounded_scope: true
  strong_oracle: true
  high_risk: false
  runtime_ambiguity: false
  parallelism_needed: false
```

If unknown on a material safety field, default to material path.

---

## P3.2 — Fast Path internal execution

Minimal internal state:

```text
Problem Revision
Attempt
source fingerprint
mutation authority
proof
outcome evidence
```

RUN/WAVE may be implemented internally for compatibility, but operator/model should not need to micromanage them.

---

## P3.3 — Fast Path acceptance tests

At least these cases:

```text
localized single-file bug
localized multi-file bounded bug
strong failing test → patch → pass
no competing lease
source drift mid-run → escalate/fail closed
runtime stale after proof → no false resolution
same problem still failing → reopen same revision
```

---

# 24. Phase P4 — HR Natural Benchmark and policy simplification

## P4.1 — Select natural problems

Use only real/user-originated cases with reconstructable outcome.

No synthetic success rows for policy promotion.

---

## P4.2 — Run methodology, not model competition

Hold model/route as stable as practical while validating:

```text
intelligence-first localization
resolution capsule continuity
fast path
outcome-based closure
```

Only after methodology proves value should model-routing economics be tuned.

---

## P4.3 — Breakthrough success gate

Promote architecture when representative natural workload shows material movement in:

```text
TTPR ↓
First-Pass Trusted Resolution ↑
Same-Problem Reopen ↓
User Correction Turns ↓
Localization Time ↓
Avoidable Governance Friction ↓
```

No requirement that every metric improve equally.

Hard floors:

```text
security non-inferior
data integrity non-inferior
financial/business semantics non-inferior
authority/proof non-inferior
```

---

# 25. Phase P5 — Distributed Runner

Only after single-host architecture is converged.

Target:

```text
ChatWeb / Controller
        ↓
Coding Web Control Plane
        ↓
Endpoint / Runner
        ↓
Workspace on that machine
```

Required identity:

```text
endpoint_id
runner process_instance_id
workspace_id
workspace_generation
source fingerprint
```

Server must never pretend to own remote filesystem it cannot verify.

Runner owns:

```text
filesystem
Git
commands
processes
workspace-local intelligence
```

Control plane owns:

```text
problem semantics
policy
routing
authority coordination
trusted resolution state
```

---

# 26. Event model

Do not add events for every detail. Add events only when they reconstruct authoritative/durable state or materially improve resolution lineage.

Candidate event families:

```text
problem.opened
problem.revised
problem.frame_updated
problem.reopened
problem.resolution_confirmed

workspace.source_changed
runtime.generation_changed

attempt.started
attempt.intervention_applied
attempt.proof_recorded

resolution.provisional
resolution.outcome_observed

lease.acquired
lease.released
```

Derived telemetry does not require durable event if snapshot/cache can rebuild it.

---

# 27. Data ownership and storage

## 27.1. Authoritative durable store

Reuse existing durable ledger/PRL machinery where semantics fit.

Do not create `problem.db` merely because a new conceptual object exists.

---

## 27.2. Derived stores

Separate rebuildable stores are appropriate for:

```text
Workspace Intelligence index
UI read-model cache
performance rollups
search cache
```

Properties:

```text
rebuildable
versioned
safe to delete/rebuild
cannot grant authority
```

---

## 27.3. Evidence retention

Keep exact fingerprints and bounded receipts necessary to prove claims.

Do not retain:

```text
raw chain-of-thought
unbounded transcripts
secrets
full source blobs in analytics
```

---

# 28. Concurrency model

Default:

```text
single lane
```

Parallelism only if:

```text
independent leaves exist
write scopes disjoint
shared interfaces settled
review/proof can keep pace
expected time saved > coordination cost
```

Stop fan-out when:

```text
writes overlap
frame changes
shared contract changes
proof becomes bottleneck
review queue grows
source drift invalidates sibling work
```

---

# 29. Failure recovery doctrine

## 29.1. Typed failure contract

Important failures should return:

```yaml
error:
  code:
  category:
  retryable:
  side_effect_committed:
  source_state:
  authority_state:
  recommended_next_action:
```

Model should not infer whether a failed mutation actually committed.

---

## 29.2. No unchanged retry

```text
same request
same evidence
same strategy
same failed result
```

must not loop.

A retry must add at least one of:

```text
new evidence
narrower scope
changed strategy
corrected environment
new authority
new source/runtime state
```

---

## 29.3. Source drift

On source fingerprint change:

```text
invalidate affected intelligence slice
invalidate stale candidate patches
invalidate proof reuse where fingerprint no longer matches
refresh capsule revision-sensitive fields
```

Do not erase evidence historically; mark it no longer valid for current claim.

---

# 30. Security and trust boundaries

Hard floors:

```text
workspace containment
explicit permission for destructive/sensitive action
no secret persistence in problem/frame/capsule
no raw transcript in durable resolution state
source/proof fingerprint integrity
write lease/fence enforcement
runtime generation fencing
remote runner endpoint identity
```

Fast Path never bypasses security gates. It removes ceremony, not safety.

---

# 31. UI product model

Operator UI should answer five questions immediately:

```text
1. What problem is being solved?
2. What is the current trusted state?
3. What is the next action/blocker?
4. Is source/runtime current?
5. Is there active mutation authority / risk?
```

Do not center UI on:

```text
number of RUNs
number of WAVEs
raw event count
raw proof count
```

Those become drill-down diagnostics.

Primary cards:

```text
Active Problems
Trusted Resolution status
Source/Runtime Currentness
Current Work / Blockers
System responsiveness
```

---

# 32. Dashboard redesign principle

Dashboard values must come from read-model snapshots.

Recommended top-level KPI set:

```text
TTPR p50/p90
First-Pass Trusted Resolution
Reopen Rate
Localization / Problem
Avoidable Governance Friction / Problem
Active unresolved Problems
```

No “data-rich” dashboard that cannot answer an operational decision.

---

# 33. Acceptance strategy

## 33.1. Unit/component acceptance

Each engine gets focused tests for its own contract.

## 33.2. Cross-engine acceptance

Representative path:

```text
Problem open
→ workspace intelligence localization
→ Fast Path attempt
→ patch
→ focused proof
→ runtime current
→ outcome evidence
→ confirmed resolution
```

## 33.3. Natural acceptance

At least one HR case must be resolved end-to-end without manual technical steering beyond user/domain feedback.

---

# 34. Definition of Done — Workspace Intelligence

```text
[ ] index builds from current source
[ ] incremental update after file change
[ ] source fingerprint binding
[ ] stale index rejected/refreshed
[ ] returns bounded relevant slice
[ ] maps at least symbols/imports/routes/tests for primary languages
[ ] no authority side effect
[ ] localization fallback remains available
[ ] measured natural localization reduction
```

---

# 35. Definition of Done — Resolution Capsule

```text
[ ] generated from authoritative/derived current state
[ ] bounded size
[ ] no raw transcript / chain-of-thought
[ ] contains current Problem Revision
[ ] contains source/runtime identity
[ ] contains current frame + counterevidence
[ ] contains valid/invalid proof summary
[ ] contains exact next causal action
[ ] survives fresh model/context
[ ] stale capsule fails closed/refreshed
```

---

# 36. Definition of Done — Fast Path

```text
[ ] eligible bounded task does not require operator RUN/WAVE ceremony
[ ] exact workspace/source enforced
[ ] single writer enforced
[ ] causal patch applied through canonical writer
[ ] focused oracle executed
[ ] runtime current checked when relevant
[ ] same-contract failure reopens problem
[ ] drift/risk escalates to material path
[ ] safety/authority non-inferior to EOCL path
```

---

# 37. Definition of Done — Runtime Read Model

```text
[ ] UI reads bounded snapshot
[ ] expensive scans moved off render path
[ ] projectors incremental/idempotent
[ ] snapshot version visible
[ ] stale snapshot age visible
[ ] source/runtime mismatch visible
[ ] p95 event-loop and IPC budgets pass
[ ] dashboard remains responsive while heavy work runs
```

---

# 38. Definition of Done — Problem Resolution Engine

```text
[ ] Problem Revision is product denominator
[ ] technical acceptance != trusted resolution
[ ] frame can evolve without contract revision
[ ] attempts link to problem/frame/source
[ ] counterevidence preserved
[ ] provisional resolution supported
[ ] independent/relevant outcome confirmation supported
[ ] same-contract reopen supported
[ ] TTPR measurable from problem timeline
```

---

# 39. Architecture admission gate

Every new architecture/feature proposal must answer:

```text
1. Which Problem-Resolution stage is bottlenecked?
2. What evidence demonstrates the bottleneck?
3. Why existing mechanism cannot solve it?
4. Does this add a new source of truth?
5. Does this add a new authority identity?
6. Can it be derived instead of authoritative?
7. Does it reduce TTPR/rework/false closure/operator friction?
8. What natural HR/Codex case will prove it?
9. What old mechanism can be removed/collapsed?
10. What is the explicit rollback/removal criterion?
```

If 1, 2, 7 or 8 cannot be answered:

```text
DEFER
```

---

# 40. Upstream adoption methodology

Use upstream only as design evidence.

```text
UPSTREAM FEATURE
      ↓
extract invariant
      ↓
map to current bottleneck
      ↓
check existing local mechanism
      ↓
PORT PRINCIPLE / PORT TEST / ADAPT / REJECT
      ↓
natural workload proof
```

Never wholesale merge to get one idea.

Preferred learning sources:

```text
coding-tools-mcp  → execution-kernel discipline
webcodex          → explicit identity, runner, context recovery, fencing
Codex-web history → trusted-resolution semantics and real local evidence
HR                → natural workload outcome truth
```

---

# 41. Subtraction backlog

A deliberate deletion cycle is mandatory.

Audit candidates:

```text
[ ] duplicate workspace targeting logic
[ ] ambient task/session fallback
[ ] duplicate runtime revision definitions
[ ] duplicate recovery/restart mechanisms
[ ] UI direct control-plane scans
[ ] automatically generated source-visible reports
[ ] telemetry with no decision consumer
[ ] routing states never used materially
[ ] proof-cache complexity with no ROI
[ ] unused LSP-specific code paths if maintenance cost exceeds value
[ ] giant model-lane persistence assumptions
```

Deletion is a product improvement if it lowers resolution friction without reducing hard floors.

---

# 42. Implementation sequencing — exact order

Do not run these as parallel architecture projects.

```text
STEP 1
P0 control/runtime/source convergence

STEP 2
Runtime Read Model foundation

STEP 3
Workspace Intelligence MVP

STEP 4
Resolution Capsule durable projection

STEP 5
Fast Path

STEP 6
HR natural benchmark

STEP 7
Simplify/remove based on real usage

STEP 8
Distributed Runner
```

Rationale:

```text
Cannot trust intelligence if source identity is ambiguous.
Cannot trust Fast Path if authority is ambiguous.
Cannot evaluate problem resolution if runtime/UI outcome is stale.
Cannot distribute a single-host architecture that is not converged.
```

---

# 43. First engineering wave — concrete implementation backlog

## Wave 1A — Currentness and authority

```text
[ ] close task_control target/schema mismatch
[ ] define explicit read-only workspace target
[ ] regression: multiple workspace roots
[ ] regression: stale context/target
[ ] reconcile current stale lifecycle through supported authority
[ ] projection reconciliation
[ ] current runtime/source invariant
```

## Wave 1B — Read model MVP

```text
[ ] define RuntimeSnapshot v1
[ ] source/runtime projector
[ ] task/problem summary projector
[ ] snapshot IPC endpoint
[ ] migrate one dashboard panel
[ ] benchmark event-loop/IPC before/after
```

## Wave 1C — Intelligence MVP

```text
[ ] file fingerprint index
[ ] JS/TS import/export graph
[ ] Python module/function graph
[ ] HTTP/IPC route extractor
[ ] test mapping
[ ] incremental changed-file update
[ ] bounded semantic query
```

## Wave 1D — Resolution Capsule

```text
[ ] derive from PRL + EOCL + workspace/runtime
[ ] bounded schema
[ ] source/runtime freshness check
[ ] no transcript/private reasoning
[ ] fresh-context recovery test
```

## Wave 1E — Fast Path prototype

```text
[ ] deterministic eligibility gate
[ ] single-writer bounded execution
[ ] focused proof
[ ] runtime/outcome check
[ ] escalation to material path
[ ] same-problem reopen
```

---

# 44. Representative end-to-end acceptance scenario

Use HR finance revenue inconsistency.

```text
USER:
“Tổng quan dự án đang hiển thị doanh thu khác tab Doanh thu.”
```

Expected engine behavior:

```text
1. Bind/open Problem Revision.

2. Workspace Intelligence returns:
   - canonical revenue owner
   - overview consumer
   - revenue tab consumer
   - settlement/payment calculations
   - relevant tests
   - recent changes

3. Compare both consumers against canonical domain invariant.

4. Run cheapest discriminator:
   canonical persisted/derived revenue value vs each projection.

5. Update Frame based on contradiction.

6. Apply smallest coherent fix.

7. Focused financial/domain test.

8. Verify running generation is current.

9. Verify both UI surfaces show same canonical revenue after reload.

10. Run one falsification probe:
    settlement case does not double-count revenue.

11. Resolution Claim confirmed.
```

Success is not “test passed”.

Success is:

```text
user-visible revenue consistency
+ domain invariant preserved
+ runtime current
+ no same-problem correction
```

---

# 45. Representative context-recovery acceptance scenario

```text
1. Problem starts in Chat A.
2. Frame and one technical attempt exist.
3. Chat/model session ends.
4. Fresh Chat B connects.
5. workspace_context identifies exact workspace/source.
6. Resolution Capsule loads current problem/frame/proof/counterevidence.
7. Workspace Intelligence returns only current relevant slice.
8. New model continues from next causal action.
```

Pass criteria:

```text
no full transcript replay
no full repository rescan
no false authority from capsule
no duplicate problem creation
no invalid proof reuse
```

---

# 46. Representative UI acceptance scenario

During a heavy command / deep-code operation:

```text
UI remains interactive
Dashboard keeps displaying last valid snapshot
Snapshot age increases visibly if updates pause
No render-path ledger/Git full scan
When new snapshot arrives, UI applies incrementally
```

Pass criteria:

```text
event-loop p95 within budget
normal controls responsive
dashboard data source explicit
no freeze caused by telemetry reconstruction
```

---

# 47. Representative stale-source scenario

```text
proof passes on source A
source changes to B
runtime still serves A
```

System must show:

```text
technical proof valid only for A
current source = B
runtime = A
problem cannot be RESOLVED_CONFIRMED based on A proof
```

No duplicate “fix the code again” before currentness is resolved.

---

# 48. Operator intervention policy

Operator should be interrupted only for:

```text
permission gate
material ambiguity in user contract
destructive/high-risk operation
external dependency
conflicting authority
release/production decision
```

Do not ask operator merely because internal orchestration changed states.

---

# 49. Model interaction contract

Models receive:

```text
Problem contract
current Frame
bounded Intelligence slice
exact source/runtime identity
relevant proof/counterevidence
next objective
```

Models do not need:

```text
full event ledger
entire transcript
all files
all past RUN narratives
all telemetry
```

This is how long-context reliability improves without unbounded tokens.

---

# 50. Decision packets for delegated lanes

Default packet:

```text
OBJECTIVE
SCOPE
CONTEXT
PROOF
STOP
```

Context packet should reference durable identities rather than narrative replay.

Example:

```text
OBJECTIVE:
Restore canonical revenue projection consistency.

SCOPE:
ProjectOverview revenue projection and exact shared selector only.

CONTEXT:
Problem R3, Frame F2, canonical owner X, source fp Y.

PROOF:
Focused finance selector test + two-surface projection check.

STOP:
Any need to change settlement semantics or canonical revenue owner.
```

---

# 51. Completion criteria for the architecture transition

The transition is complete when the following is true on representative natural work:

```text
[ ] User problem is the top-level unit in UI and analytics.
[ ] Fresh contexts resume from durable capsule.
[ ] Repository localization is intelligence-first and incremental.
[ ] Fast Path handles ordinary bounded changes.
[ ] EOCL full ceremony appears only for material coordination/risk.
[ ] UI reads snapshots and remains responsive during heavy work.
[ ] Runtime/source currentness is explicit and reliable.
[ ] Technical acceptance does not false-close user problem.
[ ] Same-problem corrections reopen the same Problem Revision.
[ ] HR natural cases show materially lower TTPR/rework/correction turns.
[ ] Model lanes can be terminated/replaced without losing problem state.
[ ] No new public tool was required merely to achieve this architecture.
```

---

# 52. Anti-patterns — cấm tái diễn

```text
ANTI-1  Add a metric because it is measurable.
ANTI-2  Add a tool because one subsystem exists.
ANTI-3  Treat RUN as user problem.
ANTI-4  Treat model thread as durable memory.
ANTI-5  Treat test PASS as user outcome.
ANTI-6  Retry same plan without new evidence.
ANTI-7  Broaden scope because repository is complex.
ANTI-8  Scan repository from scratch when derived intelligence is valid.
ANTI-9  Query heavy control-plane state from UI render path.
ANTI-10 Keep runtime state mixed with source identity.
ANTI-11 Create another authority object to work around an authority mismatch.
ANTI-12 Merge full upstream to acquire one invariant.
ANTI-13 Fan out workers before shared semantics are settled.
ANTI-14 Optimize model cost before repair/reopen cost.
ANTI-15 Use synthetic benchmark success as natural outcome evidence.
ANTI-16 Build distributed Runner before single-host convergence.
ANTI-17 Make LSP availability a hard dependency for localization.
ANTI-18 Grow proof-cache complexity before source stability exists.
```

---

# 53. Engineering review checklist

Every implementation review asks:

```text
Does this reduce repeated localization?
Does this reduce repair/reopen?
Does this reduce false closure?
Does this reduce control friction?
Does this simplify authority?
Does this preserve hard floors?
Does this avoid a new source of truth?
Can this be derived/rebuilt instead?
Can an ordinary task still use Fast Path?
Does the UI stay projection-only?
Can a new model/context continue without transcript replay?
```

---

# 54. Standing architecture constitution

1. **Problem Revision is the product/economic unit.**
2. **RUN/WAVE are internal execution provenance.**
3. **Models are disposable; durable state lives outside model context.**
4. **Runtime remembers repository structure incrementally.**
5. **Workspace Intelligence is derived, not authoritative.**
6. **UI is a projection, not a source of truth.**
7. **Fast Path is default for bounded low-risk work.**
8. **EOCL full coordination must earn its cost through risk/concurrency.**
9. **Technical acceptance is only provisional problem resolution.**
10. **Same-contract failure reopens the same Problem Revision.**
11. **Material counterevidence changes the Frame before same-family retry.**
12. **Scope expands only when evidence requires it.**
13. **One canonical authority exists per concern.**
14. **Source/runtime identity must match the claim being made.**
15. **Metrics exist only to change decisions.**
16. **Natural workload outranks synthetic benchmark for product promotion.**
17. **Model routing is secondary to methodology and outcome correctness.**
18. **No new public tool or state machine without measurable TTPR value.**
19. **Derived caches may be deleted and rebuilt without changing authority.**
20. **Distributed execution comes after single-host convergence.**
21. **The system stops when the bounded trusted claim is proven—not when machinery has produced enough activity.**

---

# 55. Final implementation proposition

Coding Web should no longer ask:

```text
“How can we orchestrate coding agents better?”
```

The engineering question becomes:

> **How can the runtime preserve enough durable knowledge about the user problem, repository, source/runtime state and evidence that any competent model can enter, perform the smallest useful causal action, verify the real outcome, and leave without forcing the next model to rediscover the world?**

That proposition yields the implementation architecture:

```text
PROBLEM PERSISTS
      ↓
RUNTIME REMEMBERS WORKSPACE
      ↓
MODEL RECEIVES SMALL RELEVANT CONTEXT
      ↓
FAST CAUSAL ACTION
      ↓
FOCUSED PROOF
      ↓
REAL OUTCOME CHECK
      ↓
TRUSTED RESOLUTION
```

The durable moat is not the number of agents or tools.

It is:

> **A system that accumulates evidence-grounded understanding of real software problems and can carry that understanding across models, sessions, machines and runtime generations without sacrificing authority, source truth or user outcome.**

---

# 56. Immediate decision

From this document forward, the default implementation order is:

```text
CONVERGE
→ PROJECT
→ REMEMBER
→ LOCALIZE
→ FAST-PATH
→ PROVE ON HR
→ DISTRIBUTE
```

Expanded:

```text
1. Operational Convergence
2. Runtime Read Model
3. Workspace Intelligence
4. Resolution Capsule
5. Fast Path
6. HR Natural Resolution Proof
7. Simplification/Deletion Cycle
8. Distributed Runner
```

Any proposal that tries to insert a large new orchestration feature before these gates must demonstrate why it materially reduces TTPR more than this sequence.

---

# 57. Status at issuance

```text
STRATEGIC DIRECTION                CLOSED
BREAKTHROUGH HYPOTHESIS            IMPLEMENTATION-READY
MORE METRIC DISCOVERY              NOT REQUIRED FOR DIRECTION
PROBLEM RESOLUTION ENGINE          TARGET CORE
WORKSPACE INTELLIGENCE             P1 BREAKTHROUGH FEATURE
DURABLE RESOLUTION CAPSULE         P2 CONTEXT CORE
FAST PATH                          P3 EXECUTION CORE
EOCL                               KEEP / CONDITIONAL MATERIAL PATH
UI READ MODEL                      P0/P1 REQUIRED
HR NATURAL WORKLOAD                CANONICAL REPRESENTATIVE BENCHMARK
DISTRIBUTED RUNNER                 AFTER SINGLE-HOST CONVERGENCE
NEW PUBLIC TOOL SURFACE            FROZEN BY DEFAULT
NEW ORCHESTRATION STATES           FROZEN BY DEFAULT
```

**Implementation doctrine:**

> **Stop measuring the machine for its own sake. Make the machine remember enough to solve the next real problem faster, with less rework and with a truthful outcome claim.**
