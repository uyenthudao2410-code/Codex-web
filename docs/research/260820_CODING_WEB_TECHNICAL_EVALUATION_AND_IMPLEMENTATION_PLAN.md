# Coding Web — Đánh giá kỹ thuật và kế hoạch triển khai kiến trúc tiếp theo

> **Baseline đánh giá:** 2026-08-20  
> **Workspace:** `E:\DEV\Codex-web`  
> **Product hiện hành:** Windows Electron Execution Hub + Recovery Host + **một** Coding Tools MCP Runtime  
> **Desktop package:** `web-mcp-assistant 0.3.4`  
> **Coding Tools runtime quan sát:** `0.4.3`, contract `smart-v3`  
> **Git baseline khi lập tài liệu:** `main` @ `5f059a1a53ff2beb9adfa4f2df9ee42907141816`, worktree đang có WIP và local branch đang ahead upstream 1 commit  
> **Loại tài liệu:** proposal/implementation plan. Tài liệu này **không** thay thế `docs/CURRENT_STATE.md` hoặc `docs/ROADMAP.md`; khi có xung đột, precedence trong `AGENTS.md` vẫn áp dụng.

---

## 1. Mục tiêu của tài liệu

Tài liệu này trả lời bốn câu hỏi:

1. Coding Web **đang thực sự có gì** ở source, proof, live runtime và product boundary hiện tại?
2. Những kỹ thuật nào còn có giá trị thực sự ngoài các feature đã khảo sát từ upstream WebCodex?
3. Phần nào là **capability mới**, phần nào chỉ là **generalize/nâng cấp nền tảng đã có**, và phần nào nên hoãn?
4. Nếu triển khai, thứ tự nào giảm rủi ro nhất, không phá authority/EOCL hiện hữu và không biến `smart-v3` thành một surface có hàng chục tool?

Mục tiêu không phải biến Coding Web thành một framework tổng quát. Mục tiêu là làm nó mạnh hơn theo đúng hướng sản phẩm đang hình thành: **một stateful coding operating layer cho nhiều model/client cùng sử dụng một execution authority, có bằng chứng, recovery, isolation và policy rõ ràng**.

---

## 2. Kết luận điều hành

### 2.1. Coding Web không còn là một WebCodex fork theo nghĩa kiến trúc

Product truth hiện tại đã là:

```text
ChatWeb / ChatGPT
      |
      | MCP qua primary tunnel
      v
Recovery Host / Execution Hub authority
      |
      +---- ONE Coding Tools MCP Runtime ---- workspace / Git / commands / proof
      |              ^
      |              |
      |        Codex Desktop thin proxy
      |
      +---- Electron Execution Control Center
      |
      +---- independent Recovery MCP / Recovery Tunnel

Secondary lanes:
Codex App Server / OpenCode -> candidate/review/read-only/bounded work
Coding Tools MCP / EOCL      -> mutation/proof/ledger/final acceptance boundary
```

Điểm khác biệt cốt lõi là **one-runtime authority + durable orchestration + EOCL + evidence-first execution**. Vì vậy không nên merge một loạt upstream feature như thể source tree vẫn cùng kiến trúc. Các feature upstream chỉ nên được xem như **feature families / invariants để audit và port có chọn lọc**.

### 2.2. Ba hướng kiến trúc có ROI tiềm năng cao nhất

Nếu mở một engineering phase mới, thứ tự kiến trúc ưu tiên được đề xuất là:

1. **Semantic Repository Graph + Context Compiler** — biến semantic localization hiện hữu thành repository intelligence layer bền vững và giảm search/read/context churn trước khi model thấy tool surface.
2. **Transactional Task Workspace bằng Git worktree** — biến multi-window/multi-model từ “nhiều client cùng gọi một runtime” thành parallel engineering an toàn, không để nhiều lane mutation trực tiếp trên một checkout.
3. **Capability Policy + Secret Broker + isolated worker boundary** — hoàn thiện trust boundary trước khi Computer Use, remote relay hoặc model-driven network/browser capability trở thành first-class production feature.

Định hướng tổng quát:

> **Giữ model-facing surface nhỏ, làm runtime phía sau thông minh hơn.**

### 2.3. Không nên mở ngay một “đại refactor”

`docs/ROADMAP.md` hiện ưu tiên P4/P5 accepted-result/rework economics và chủ động hạn chế orchestration architecture mới nếu chưa có concrete regression. Do đó cần một **decision gate**:

- **Mặc định:** tiếp tục P4/P5 là program chính; chỉ làm audit/measurement/low-risk plumbing cho kiến trúc mới.
- **Chỉ khi có quyết định reprioritize rõ ràng:** mở một phase mới, ví dụ `Next Runtime Foundation`, với từng workstream nhỏ, độc lập và có acceptance gate riêng.

Không nên dùng tài liệu này để âm thầm thay thế roadmap hiện tại.

---

## 3. Nguyên tắc đánh giá

Mọi capability được đánh giá theo bốn tầng độc lập:

| Tầng | Ý nghĩa |
|---|---|
| **Source present** | Code/module/schema đã tồn tại trong checkout |
| **Focused proof** | Có test/check tập trung chứng minh behavior liên quan |
| **Live active** | Runtime đang chạy đã load đúng source và behavior được quan sát trên tool plane thật |
| **Packaged/released** | Behavior đã đi qua package/release boundary cần thiết |

Không được nâng một claim lên tầng cao hơn chỉ vì source file tồn tại.

Các invariant phải giữ:

- chỉ **một Coding Tools Runtime authority** cho workspace/ledger chính;
- ChatWeb/Sol là semantic controller/final acceptance authority trong coordinated work;
- EOCL + permission + write lease vẫn là mutation authority; không tạo authority model thứ hai;
- deterministic proof ưu tiên hơn model debate khi compiler/test/tool có thể trả lời;
- `execution_route=auto` vẫn fail-closed về deterministic cho đến khi evidence gate thay đổi;
- secondary provider không tự nhận write authority chỉ vì router gọi được nó;
- model-facing `smart-v3` vẫn giữ đúng 8 public tools trừ khi có lý do sản phẩm rất mạnh để thay đổi;
- không đưa `.coding-tools` volatility vào source/worktree fingerprint;
- không mở rộng framework cho hypothetical tenant/fleet/trust boundary khi chưa có use case thật.

---

## 4. Thực trạng kỹ thuật hiện tại

### 4.1. Những nền tảng đã mạnh và không nên xây lại

| Capability | Trạng thái hiện tại | Nhận định |
|---|---|---|
| One-runtime authority | **Đã xác lập** | Recovery Host/Execution Hub sở hữu lifecycle; một Coding Tools MCP Runtime là mutation/proof authority |
| EOCL / durable orchestration | **Đã có sâu** | Có orchestration ledger, task/run/wave state, proof lineage, acceptance boundary |
| Durable evidence | **Đã có** | `.coding-tools/orchestration/ledger.sqlite3` là canonical causal audit source |
| Smart tool surface | **Đã có** | `smart-v3` công khai đúng 8 tool |
| Recovery architecture | **Đã có và đã qua live/package gates quan trọng** | Recovery Host, Recovery Supervisor, Recovery MCP/Tunnel, semantic tool-plane watchdog |
| Structured process/script execution | **Code-complete/accepted trong core execution** | Native argv, script payload, sync-to-Job handoff, batch Job observation |
| Same-Runner job reconciliation | **Đã có** | Runner reconnect có thể reconcile active/terminal job trong phạm vi semantics hiện tại |
| LSP process/resource governance | **Đã có mạnh** | Process identity, memory telemetry, pressure/reaping policy, Rust/Python/TS LSP |
| Validation intelligence | **Đã có** | Structured parser, bounded diagnostics, validation events, continuation feedback |
| Compute placement | **Engineering accepted** | `local_only` / `server_preferred`; global server-first vẫn evidence-gated |
| Provider routing/economics plumbing | **Đã có** | Explicit routes, provider telemetry, P4 solution economics shadow |
| Evaluation/replay foundation | **Đã có một phần** | Có evaluation replay/measurement infrastructure; không nên gọi đây là greenfield |
| Artifact content hashes | **Đã có một phần** | Artifact references đã có content hash/content-addressed semantics ở phạm vi artifact |
| Tunnel/recovery connectivity | **Đã có một phần** | Primary/recovery tunnel tồn tại; package còn có tunnel client |
| OAuth/auth/audit foundation | **Đã có** | Core WebCodex có auth/OAuth/audit; Desktop có authority/secrets ownership riêng |

### 4.2. Những capability có foundation nhưng chưa đủ để coi là hoàn chỉnh

#### Semantic localization

Project đã có `semantic_localization.py`, LSP infrastructure và semantic-first policy. Tuy nhiên runtime observation tại thời điểm lập tài liệu báo semantic localization **không available** vì native LSP binding chưa được cấu hình (`NATIVE_LSP_BINDING_NOT_CONFIGURED`).

Kết luận: không nên mô tả project là “không có semantic intelligence”, nhưng cũng chưa thể coi project có **persistent semantic repository map/context compiler** phục vụ ổn định cho mọi task. Đây là foundation tốt nhất để nâng cấp thành Repository Graph.

#### Worktree / parallel mutation

Runtime vocabulary đã có `coordinated_multi_worktree`, nhưng execution mode này được fail-closed nếu coordination readiness chưa được chứng minh. Không có evidence hiện tại cho thấy mọi mutation task đã được isolate mặc định theo per-task worktree.

Kết luận: concept đã xuất hiện, nhưng **transactional task workspace chưa phải default production contract**.

#### Sandbox / code mode

Experimental code mode hiện bị gate vì chưa có isolated worker runtime đáp ứng đủ guarantee. Windows Job Object giải quyết process lifecycle/resource grouping chứ không phải full security sandbox; Linux Landlock hiện tại chỉ giải quyết một phần write confinement. Code mode còn cần các guarantee như no direct filesystem, no network, no inherited secrets, bounded IPC và process restrictions.

Kết luận: **Capability Policy + isolated worker + Secret Broker** là khoảng trống thực tế, không phải speculative feature.

#### CAS / Merkle identity

Artifact layer đã có content addressing. Nhưng chưa có evidence rằng source blobs, semantic-index shards, context compiler cache, reusable safe tool results và workspace identity đều dùng chung một content-addressed substrate.

Kết luận: nên **generalize foundation hiện tại**, không tạo một storage subsystem trùng lặp.

#### Tracing / replay

Project đã có `turn_id`, `trace_id`, `span_id`, performance telemetry, host observations và evaluation replay. Khoảng trống là **chuẩn hóa propagation và correlation xuyên boundary** theo một contract thống nhất, không phải “thêm observability từ đầu”.

#### Remote connectivity

Tunnel đã là product boundary, và package có tunnel client. Khoảng trống tiềm năng là formalize device identity, outbound reverse connection lifecycle, project-bound lease, reconnect/resume semantics và per-device authority/audit thành một subsystem có contract rõ ràng.

### 4.3. Capability chưa có evidence đủ để gọi là first-class product subsystem

- persistent **Semantic Repository Graph**;
- **Context Compiler** có token budget và `already_seen` awareness;
- default **transactional task worktree** + promotion gate;
- unified **Capability Policy** cho filesystem/process/network/computer/secrets;
- first-class **Secret Broker** với opaque secret handles;
- generalized CAS/Merkle workspace identity;
- OpenTelemetry/W3C trace propagation end-to-end;
- first-class reverse-relay/device-lease orchestration;
- MCP Tasks/Elicitation adapter mapped vào durable ledger;
- A2A gateway;
- isolated shadow-model execution pipeline có worktree riêng và no-promotion guarantee;
- Computer Use như một security-gated product subsystem ở Desktop stack hiện tại.

---

## 5. Ma trận ưu tiên đề xuất

| ID | Workstream | Ưu tiên | Giá trị | Rủi ro | Ghi chú |
|---|---|---:|---:|---:|---|
| W0 | Baseline + upstream feature-family audit | P0 | Cao | Thấp | Làm trước mọi port/refactor |
| W1 | Sparse model-facing projection audit | P0 | Cao | Thấp–TB | Audit trước vì `smart-v3` đã sparse ở nhiều điểm |
| W2 | Artifact bridge/import/export/streaming audit | P0 | Cao | TB | Nâng cấp foundation hiện có, không duplicate |
| W3 | Caller attribution audit | P0 | Cao | Thấp–TB | Cần cho multi-window/multi-model/Computer Use |
| W4 | Semantic Repository Graph | P0 | Rất cao | TB–Cao | Generalize semantic localization/LSP foundation |
| W5 | Context Compiler | P0 | Rất cao | TB | Chỉ mở sau W4 minimum viable graph |
| W6 | Transactional Task Workspaces | P0 | Rất cao | Cao | Foundation cho parallel mutation/shadow models |
| W7 | Capability Policy + Secret Broker | P0 | Rất cao | Cao | Foundation bảo mật cho các capability quyền lực |
| W8 | Computer Use | P1 | Cao | Cao | Chỉ sau W7 minimum security gate |
| W9 | Generalized CAS + Merkle workspace identity | P1 | Cao | TB | Build trên artifact content addressing hiện có |
| W10 | Trace-context standardization + replay integration | P1 | Cao | TB | Build trên telemetry/replay hiện có |
| W11 | MCP 2026 adapter layer | P1 | TB–Cao | TB | Adapter-only; không làm core Job phụ thuộc optional MCP feature |
| W12 | Reverse relay / device lease | P1 | Cao | Cao | Formalize tunnel/device semantics hiện có |
| W13 | Detached Job restart invariant audit | P1 | Cao | TB–Cao | So với upstream; tránh copy nếu current recovery tốt hơn |
| W14 | Shadow model evaluation | P2 | Cao | Cao | Chỉ sau worktree isolation + strong oracle |
| W15 | A2A gateway | P2 | TB | TB–Cao | Chỉ khi có external-agent use case thật |

---

## 6. Kiến trúc đích đề xuất

```text
GPT / Claude / Gemini / Codex / CLI
                  |
          MCP protocol adapter
          A2A adapter (later)
                  |
        +---------+----------+
        |                    |
  Task Coordinator      Durable Ledger / EOCL
        |                    |
  Context Compiler      Trace / Evidence / Replay
        |                    |
 Semantic Repo Graph         |
        |                    |
        +------ Task Workspace ------+
                     |
          Capability Policy
             Secret Broker
                     |
                 Executor
          +----------+----------+
          |          |          |
       Process      LSP     Computer Use
          |          |          |
          +----- CAS / Artifacts ----+
                     |
              Promotion Gate
                     |
            Canonical Repository
```

Các layer mới nên **nằm sau 8-tool surface**, không nhất thiết tạo public tool mới. Ví dụ `agent_workflow -> context compiler -> task workspace -> capability evaluator -> existing executor/tool primitives`.

---

# 7. Workstream chi tiết

## W0 — Baseline và feature-family audit

Trước khi port upstream hoặc mở architecture phase mới, tạo matrix “current vs upstream vs proposed” ở cấp behavior/invariant.

Audit các family:

1. Sparse output/model projection từ upstream PR #105.
2. Artifact bridge/import/export/streaming từ #46/#55.
3. Authenticated caller attribution #82/#83.
4. Computer Use từ bounded control đến authenticated snapshot links (#45 → #107 family).
5. Detached Job ownership/restart-survival invariants (#96/#101 family).
6. Release/platform hardening chỉ sau khi runtime capability sync cần nó.

Nguyên tắc: không merge upstream range dài; không assume file cùng tên nghĩa behavior cùng nhau; port **invariant** chứ không port “diff vì upstream có”. Mỗi family phải nêu current behavior, upstream behavior, missing invariant, conflict với Desktop authority và quyết định `skip/adapt/port/replace`.

**Acceptance:** đủ evidence để trả lời “vì sao port/không port” trước mutation.

---

## W1 — Sparse model-facing projection audit

Coding Web đã có `smart-v3` 8 tools, lightweight startup profile, bounded continuation/handoff briefs, repository-rule hashing và bounded output schemas. Vì vậy upstream sparse projection không được coi là hoàn toàn mới.

Đo model-facing payload thực tế của `workspace_context`, `agent_workflow prepare`, read/search equivalents, successful process/script execution, validation completion và job observation. Chỉ port rule giúp giảm payload mà vẫn giữ failure classification, timeout/outcome_unknown, continuation token, proof identity và source/revision identity cần cho retry safety.

Baseline metrics:

- bytes/model turn;
- tool-result tokens nếu host/provider đo được;
- tool hops đến first useful edit;
- follow-up read rate do sparse quá mức;
- TTAR / first-pass acceptance.

Không đặt tỷ lệ tiết kiệm tùy ý trước khi có baseline đại diện.

---

## W2 — Artifact pipeline: streaming + import/export + provenance

Project đã có `artifact_refs.py` và content-hashed artifact references. Cần nâng cấp foundation đó, không tạo “Artifact System v2”.

Audit/bổ sung nếu thiếu:

- conversation attachment -> registered project import không cần base64/local path trong model;
- project file -> authenticated artifact resource export;
- streaming;
- bounded size/cancellation/disconnect;
- atomic finalization;
- cleanup partial transfer;
- content hash/provenance xuyên upload/import/export.

Artifact ref nên có `artifact_id`, `content_hash`, `size`, `media_type`, owner task/run/wave, source kind, created_at, retention/expiry và safe resource locator.

**Acceptance:** interrupted transfer không tạo success giả; duplicate content có thể reuse khi policy cho phép; model không nhận raw secret; audit lưu identity/provenance chứ không lưu body.

---

## W3 — Authenticated caller attribution

Mỗi action quan trọng phải truy ra được principal, client/window identity hash, transport, session/task/run/wave, provider/model lane nếu có, runtime instance và executor/runner.

Attribution **không** được trở thành authorization plane thứ hai:

- auth/EOCL quyết định quyền;
- attribution chỉ ghi nguồn thực hiện;
- raw window id/token/path vẫn phải theo privacy/hash pattern hiện có;
- action event và proof lineage phải có caller attribution tương ứng.

---

## W4 — Semantic Repository Graph

### Mục tiêu

Tạo index read-only, incremental, hash-bound theo source revision trên foundation semantic localization/LSP hiện có.

### V1 data model

```text
File
Symbol
Definition
Reference
Import/module relation
Call edge khi provider đáng tin
Implementation relation khi provider đáng tin
Test association
content/source hash
provider + provider version
confidence/completeness
```

Không bắt đầu bằng graph database tổng quát.

### Provider strategy

1. native LSP semantic provider;
2. language-specific index khi có concrete need;
3. bounded text fallback khi semantic unavailable.

Không chạy repository code để index. Giữ security posture read-only/no dependency execution.

### Persistence

Index shard bind với canonical repo identity, Git HEAD/source fingerprint slice, file content hash, provider identity/version và schema version. Invalidate theo hash, không tin timestamp.

### Internal API gợi ý

```text
semantic_graph.resolve_symbols(query, budget)
semantic_graph.references(symbol_id, budget)
semantic_graph.related_tests(symbol_id, budget)
semantic_graph.impact(seed_symbols, depth, budget)
```

Không nhất thiết public thành MCP tools.

### Acceptance

- result project-relative/redacted;
- semantic unavailable có fallback structured;
- stale index không được coi là current;
- update incremental có budget;
- confidence/completeness structured;
- không tăng LSP process/resource churn ngoài governance hiện hành.

---

## W5 — Context Compiler

Mục tiêu chuyển từ `model -> search -> read -> search -> LSP -> read` thành:

```text
task intent
   -> semantic graph + Git diff + rules + recent evidence
   -> deterministic context compilation
   -> model nhận context tối thiểu cần thiết
```

Interface nội bộ:

```text
compile_context(
    task_intent,
    repo_revision,
    token_budget,
    current_evidence,
    already_seen,
    requested_scope
) -> CompiledContext
```

`CompiledContext` nên có primary symbols/files, entry points, relevant callers/callees, tests, config/rules, dirty diff liên quan, uncertainty/warnings, omitted candidates + reason và stable fingerprints để dedupe.

Không nên vector-search mọi thứ rồi dump context dài; không auto-read toàn repo; không giấu uncertainty; không cache nếu không bind source/provider fingerprint; không lặp raw repository rules khi hash không đổi.

### Evaluation

Paired representative tasks:

```text
Control: current semantic-first + bounded search
Treatment: context compiler enabled
```

Đo tool hops trước first causal edit, model-facing bytes/tokens, file reads, rework/replan, first-pass acceptance, TTAR và false-focus/miss. Reuse P4/P5 measurement discipline thay vì xây analytics framework mới.

---

## W6 — Transactional Task Workspaces bằng Git worktree

Một runtime authority không tự động giải quyết concurrent filesystem mutation. Mỗi mutation task nên có isolated worktree:

```text
Canonical checkout @ HEAD A
      |
      +-- Task A worktree @ A
      +-- Task B worktree @ A
      +-- Shadow worktree @ A
```

Automation worktree/nested repository **không được đặt dưới `.coding-tools`**. Dùng external/sibling worktree root theo repo hash + task id.

Data model tối thiểu:

```text
TaskWorkspace {
  task_id
  base_revision
  worktree_id/path_ref
  branch/ref
  current_revision
  write_intents
  last_verified_revision
  state
}
```

Promotion:

```text
mutate isolated worktree
 -> focused validation
 -> EOCL/proof completeness
 -> verify canonical/base relationship
 -> conflict/rebase decision
 -> promotion
 -> canonical branch
```

V1 dùng bounded write intents (paths, symbols nếu semantic graph available, scope fingerprint) để cảnh báo/serialize/replan overlap; chưa cần pessimistic lock toàn repo.

**Acceptance:** task không mutation worktree khác nếu không explicit handoff; canonical không đổi trước promotion; base drift fail-closed; cleanup không xóa active worktree; restart vẫn truy ra ownership; no nested gitlink dưới `.coding-tools`; EOCL vẫn là promotion authority.

---

## W7 — Capability Policy + Secret Broker + isolated worker

Experimental code mode hiện fail-closed vì isolated worker guarantee chưa đủ. Đây là nơi cần generalize permission/EOCL/execution-resource controls hiện có thành runtime capability evaluation, không tạo auth system mới.

```text
CapabilitySet {
  filesystem: read_roots / write_roots
  process: executable class / max processes / runtime
  network: denied | allowlist
  computer: screen / mouse / keyboard / clipboard
  secrets: allowed opaque handles
  artifact: import/export bounds
}
```

CapabilitySet derive từ:

```text
principal + project + EOCL state + write lease + task policy + tool intent
```

### Secret Broker

Model/tool schema không nhận raw secret. Chỉ thấy opaque handles như:

```text
secret://github/release
secret://npm/publish
secret://provider/account-x
```

Recovery Host/Electron boundary tiếp tục sở hữu secret; executor chỉ nhận scoped injection ở execution boundary.

### Required guarantees

- không inherit full host env mặc định;
- secret không xuất hiện trong model output/audit/log;
- network deny-by-default cho worker nhạy cảm;
- explicit filesystem roots;
- bounded subprocess policy;
- framed bounded IPC;
- timeout/kill/lifecycle ownership rõ;
- capability decision có audit event.

Windows Job Object vẫn là lifecycle/resource primitive chứ không phải complete sandbox. Linux Landlock chỉ là một layer. Threat model V1 phải được chốt trước khi chọn OS primitive cuối cùng.

### Acceptance

Positive/negative test phải chứng minh allowed read thành công; out-of-root bị deny; network deny không bypass qua child; secret không xuất hiện trong env dump/tool result/audit; forbidden subprocess bị deny; worker crash/timeout không giữ write lease/child orphan; model-provided fields không thể elevate policy.

---

## W8 — Computer Use

Chỉ mở production sau khi W7 có minimum security contract.

V1: bounded snapshot/screenshot, mouse click, keyboard input, bounded scroll, window/display selection, clipboard opt-in và authenticated artifact/resource link cho snapshot.

Policy levels:

```text
observe_only
interactive_low_risk
sensitive_action_requires_approval
blocked
```

Sensitive action gồm credential dialogs, destructive OS controls, financial/payment flows hoặc secret-bearing clipboard. Mỗi action phải có caller attribution + task/run/wave + target window/display identity + policy decision.

Non-goal V1: arbitrary desktop automation framework.

---

## W9 — Generalized Content-Addressed Store + Merkle workspace identity

Artifact layer đã content-addressed; cần generalize có chọn lọc cho artifact blobs, source/file blobs nếu policy cho phép, semantic index shards, compiled-context entries, deterministic derived metadata và safe reusable tool results.

Workspace identity:

```text
workspace_root = hash(path + blob_hash, ...)
```

Invariant: `.coding-tools` runtime evidence, credential và local-only path không tham gia source/worktree fingerprint; symlink/large-file handling giữ bounded/conservative semantics hiện tại.

Không cache command/test result trừ khi key đủ gồm source identity, command/tool, args, cwd, relevant env fingerprint, lockfiles/toolchain, sandbox/policy và executor/platform khi cần. Nếu chưa chứng minh hermeticity, chỉ cache read/derived metadata an toàn.

---

## W10 — Trace-context standardization + replay integration

Project đã có trace/span/turn IDs, telemetry, performance trace, host observations và evaluation replay. Mục tiêu là chuẩn hóa correlation xuyên ChatWeb -> MCP -> Runtime -> router/provider -> executor/runner -> LSP/process/job -> proof/acceptance.

- map current `trace_id`/`span_id` vào W3C Trace Context khi transport hỗ trợ;
- OTEL export là adapter, không phải source of truth;
- durable orchestration ledger vẫn canonical cho run/wave/authority;
- không lưu raw prompt/code/secret mặc định;
- span attributes dùng opaque/repository-safe identity.

Phân biệt rõ:

1. **Evidence replay:** dựng causal timeline từ ledger/events.
2. **Tool/execution replay:** tái chạy deterministic operation khi policy cho phép.
3. **Evaluation replay:** reuse framework hiện có cho controlled comparison.
4. **Model rerun:** experiment mới, không phải deterministic guarantee.

**Acceptance:** từ một task/run có thể trace principal/window hash, route/provider, tool/executor spans, job/proof/acceptance và source/workspace identity mà không join bằng timestamp heuristic.

---

## W11 — MCP 2026 adapter: Tasks / Elicitation / resume

`docs/MODEL_EXECUTION.md` đã đúng khi không phụ thuộc core Job semantics vào optional host feature. Giữ invariant đó.

Khi client hỗ trợ:

```text
MCP Task facade
      |
      v
Coding Web durable Task/Job/EOCL ledger
```

MCP feature là adapter/projection, không thay durable ledger. Elicitation dùng cho structured approval/input; sensitive credential flow phải out-of-band/brokered; client không hỗ trợ extension vẫn có fallback.

**Acceptance:** negotiation fail-safe; client cũ vẫn hoạt động; reconnect không duplicate execution; external task state không mâu thuẫn internal truth; cancellation không tự retry side effects.

---

## W12 — Outbound reverse relay / device lease

Tunnel đã là part of product, nên đây là formalization chứ không phải networking greenfield.

```text
Device/Runner
  -> outbound authenticated persistent connection
  -> relay
  -> Execution Hub
```

Identity/lease:

```text
device identity
+ project grant
+ runtime instance
+ expiring connection lease
+ reconnect token/epoch
```

Recovery MCP vẫn là bounded recovery plane, không biến relay thành arbitrary remote process/service manager.

**Acceptance:** stale connection không chiếm replacement; reconnect không duplicate job; project grant không bleed; revocation có effect rõ; caller attribution/trace xuyên relay; tunnel failure tạo typed degraded/recovering state chứ không silent retry mutation.

---

## W13 — Detached Job restart-survival audit

Current core đã có same-Runner reconciliation và Server restart/reconnect semantics. Runner-process restart chưa có universal guarantee vì process mới không sở hữu old child handles.

Trước khi port upstream, lập invariant matrix:

| Scenario | Current behavior | Desired behavior |
|---|---|---|
| transport reconnect, same Runner | reconcile | giữ nguyên |
| Server restart, Runner còn sống | inventory/recovery path | audit exact guarantees |
| Runner restart, child còn sống | chưa general guarantee | quyết định có cần ownership handoff |
| host reboot | no implicit exactly-once promise | explicit lost/recovery semantics |
| replacement Runner instance | không inherit old job bừa | giữ fail-closed |

Chỉ implement ownership handoff nếu có concrete workload mà current semantics không đáp ứng.

---

## W14 — Shadow model evaluation

Project đã có provider routing, solution economics shadow, paired-evaluation plumbing và fail-closed evidence policy. Không xây analytics framework mới.

Điều kiện mở: W6 worktree isolation đủ an toàn, oracle mạnh, cost/usage provenance rõ và shadow lane có no-promotion enforcement.

```text
Representative task
   |
   +-- Primary lane -> isolated task worktree -> eligible for promotion
   |
   +-- Shadow lane  -> separate worktree -> NEVER direct promotion
```

So sánh accepted quality, first-pass acceptance, repair/replan, TTAR, tool hops, provider usage/cost khi measured, change-surface quality và critical defect rate. Benchmark/synthetic không tự authorize routing.

---

## W15 — A2A gateway

Chỉ đáng làm khi có consumer cụ thể:

```text
External agent/service
  -> giao task
  -> Coding Web durable task
  -> execution/proof
  -> artifact/PR/result
```

Nếu chưa có external-agent use case thật, defer. Nếu mở, A2A phải map vào existing Task Coordinator/EOCL, không tạo writer authority song song.

---

# 8. Kế hoạch triển khai theo wave

## Wave 0 — Preserve, baseline, audit

1. Hoàn tất/terminalize WIP hiện tại theo đúng owner/acceptance; không reset/rebase/clean để lấy “clean repo”.
2. Khi mở engineering phase mới, tạo clean baseline/branch riêng sau khi current WIP được xử lý đúng cách.
3. Snapshot metrics: model-facing bytes/hops, TTAR/first-pass/replan, semantic availability/fallback, artifact transfer, caller attribution completeness, trace coverage và contention incidents nếu có.
4. Audit upstream feature families W1–W3 + Computer Use + detached jobs.
5. Viết decision record port/skip/adapt.

**Exit gate:** không còn assumption “upstream có = project thiếu”; mỗi proposed port có evidence.

## Wave 1 — Low-risk surface/runtime efficiency

1. W1 sparse projection audit + missing rules.
2. W2 artifact streaming/import/export delta.
3. W3 caller attribution delta.

**Exit gate:** focused proof + live activation checks nếu runtime-affecting; không tăng public tool count nếu behavior có thể nằm trong existing smart tools.

## Wave 2 — Core intelligence

1. W4 minimum viable Semantic Repository Graph.
2. Enable/repair native semantic provider cho current Desktop runtime.
3. W5 Context Compiler sau internal treatment gate.
4. Paired representative evaluation với current flow.

**Exit gate:** giảm discovery work mà không tăng rework/critical defect; nếu không đạt, giữ graph như internal intelligence và không auto-inject context.

## Wave 3 — Transactional mutation isolation

1. W6 task worktree lifecycle.
2. External/sibling worktree root.
3. Base revision + ownership + write intents.
4. Promotion gate integrated với EOCL/proof.
5. Restart/recovery cleanup semantics.
6. Chỉ sau đó cân nhắc `coordinated_multi_worktree` cho task class phù hợp.

**Exit gate:** hai concurrent tasks không mutation canonical checkout trước promotion và conflict/base drift fail-closed.

## Wave 4 — Trust/runtime foundation

1. W7 unified capability decision.
2. Secret Broker.
3. Isolated worker boundary cho code mode/high-risk operations.
4. W9 generalized CAS/Merkle ở phạm vi cần thiết.
5. W10 trace-context standardization.

**Exit gate:** negative security tests + provenance/trace + no-secret-leak + recovery correctness.

## Wave 5 — Privileged/distributed capabilities

1. W8 Computer Use.
2. W12 reverse relay/device leases.
3. W11 MCP adapter extensions.
4. W13 detached-job restart chỉ nếu audit chứng minh gap đáng giải quyết.

**Exit gate:** privileged action đều policy-gated, attributed, traceable và fail-closed.

## Wave 6 — Empirical multi-model platform

1. W14 shadow model isolated evaluation.
2. Router evidence promotion only after representative gate.
3. W15 A2A chỉ khi có concrete external-agent consumer.

**Exit gate:** shadow lane không có direct promotion authority; router activation vẫn cần accepted evidence.

---

# 9. Dependency graph

```text
W0 audit
 |
 +--> W1 sparse
 +--> W2 artifacts
 +--> W3 attribution
 |
 +--> W4 semantic graph --> W5 context compiler
 |
 +--> W6 worktrees ---------------------> W14 shadow models
 |
 +--> W7 capability/secret --> W8 computer use
 |            |
 |            +--------------> W12 privileged relay policy
 |
 +--> W9 CAS ------> context/index cache + artifact dedupe
 |
 +--> W10 tracing --> W12 / W14 / A2A observability
 |
 +--> W11 MCP adapters
 +--> W13 job restart only after invariant audit
 `--> W15 A2A only after concrete consumer
```

Critical path nếu đầu tư một chuỗi lớn:

```text
Semantic provider health
 -> Semantic Repository Graph
 -> Context Compiler
 -> Transactional Worktrees
 -> Capability/Secret boundary
```

---

# 10. Mapping vào codebase hiện tại

Integration landmarks:

- `resources/coding-tools-mcp/coding_tools_mcp/orchestration_ledger.py`
- `resources/coding-tools-mcp/coding_tools_mcp/coordination.py`
- `resources/coding-tools-mcp/coding_tools_mcp/orchestration_control.py`
- `resources/coding-tools-mcp/coding_tools_mcp/proof_ledger.py`
- `resources/coding-tools-mcp/coding_tools_mcp/task_state.py`
- `resources/coding-tools-mcp/coding_tools_mcp/workspace_truth.py`
- `resources/coding-tools-mcp/coding_tools_mcp/execution_resources.py`
- `resources/coding-tools-mcp/coding_tools_mcp/provider_routing.py`
- `resources/coding-tools-mcp/coding_tools_mcp/solution_economics.py`
- `resources/coding-tools-mcp/coding_tools_mcp/semantic_localization.py`
- `resources/coding-tools-mcp/coding_tools_mcp/artifact_refs.py`
- `resources/coding-tools-mcp/coding_tools_mcp/performance_trace.py`
- `resources/coding-tools-mcp/coding_tools_mcp/telemetry.py`
- `resources/coding-tools-mcp/coding_tools_mcp/evaluation_replay.py`
- `resources/coding-tools-mcp/coding_tools_mcp/code_mode.py`
- transport/auth modules tương ứng.

Suggested ownership:

| Capability | Nên tích hợp với |
|---|---|
| Semantic graph | `semantic_localization` + provider/LSP boundary; module mới chỉ khi graph có state riêng |
| Context compiler | `agent_workflow` preparation + startup/handoff projections |
| Task worktree | orchestration ledger + workspace truth + coordination + write lease |
| Capability policy | permission/EOCL/execution resources; không bypass |
| Secret broker | Recovery Host/Electron secrets authority + executor injection boundary |
| CAS | artifact refs/storage + source fingerprint utilities |
| Trace context | performance/telemetry + MCP/HTTP/runner boundaries |
| Shadow evaluation | solution economics/evaluation plumbing hiện có |

### WebCodex Rust/core

Giữ `tool_runtime` protocol-independent; runner LSP giữ read-only semantic/security posture; HTTP/MCP adapters không thành source of execution truth; Job semantics không phụ thuộc MCP Apps/Tasks/UI.

### Electron / Recovery Host

Tiếp tục sở hữu lifecycle, secrets, runtime activation, primary/recovery tunnel ownership và operator control. Không chuyển các responsibility này sang model-facing MCP tool chỉ để tiện implementation.

---

# 11. Upstream WebCodex: chiến lược sync

Không broad merge/cherry-pick range dài. Mỗi feature family:

```text
upstream invariant
 -> current implementation audit
 -> minimal adapted patch
 -> focused proof
 -> live activation proof nếu cần
 -> accept/reject
```

Thứ tự delta: sparse model projection -> artifact bridge/streaming -> caller attribution -> Computer Use sau security gate -> detached-job restart invariant audit -> release/platform hardening liên quan trực tiếp.

---

# 12. Metrics và evaluation contract

Theo dõi:

- first-pass acceptance;
- repair/replan count;
- TTAR;
- critical defect / acceptance regression;
- model-facing payload bytes/tokens khi đo được;
- tool hops đến causal change;
- semantic hit/fallback rate;
- context compiler precision/miss categories;
- worktree conflict/base-drift incidence;
- promotion failure reasons;
- artifact bytes transferred vs deduped;
- trace correlation completeness;
- secret/policy denial correctness;
- job recovery/lost classification;
- provider cost chỉ khi provider/controller-reported, không suy diễn missing thành zero.

Mỗi treatment cần preregistered contract:

```text
source/task class
oracle
baseline/control behavior
treatment flag
required invariants
measured metrics
promotion gate
rollback condition
```

Reuse P4/P5 evidence discipline: representative khác benchmark/synthetic; missing là unknown; ghi source/runtime activation identity; không promote từ small/synthetic cohort; experiment không tự thay đổi authority.

---

# 13. Release/acceptance gate chuẩn

### G0 — Contract
Problem cụ thể, non-goals, owner/boundary, không duplicate authority.

### G1 — Source
Smallest coherent implementation, compatibility/schema cần thiết, focused tests.

### G2 — Proof
Negative/edge cases và exact changed behavior; không chạy unrelated full-suite chỉ vì thói quen nếu focused proof đã đủ cho change surface.

### G3 — EOCL acceptance
Proof lineage hoàn chỉnh, write lease/ownership rõ, no unresolved conflict/job state.

### G4 — Live activation
Với runtime-affecting change: running instance loads accepted source; real tool path smoke; contract/tool count nếu relevant; no raw internal exception leakage.

### G5 — Package/release
Chỉ claim khi package boundary tương ứng đã được kiểm chứng.

### G6 — Efficacy promotion
Representative evidence, stable oracle, no quality regression và threshold preregistered sau baseline hợp lý.

---

# 14. Rủi ro và control

| Rủi ro | Control |
|---|---|
| Overengineering semantic/CAS/policy | V1 chỉ implement use case có consumer thật |
| Duplicate source of truth | Adapter/projection only; ledger vẫn canonical |
| Context compiler bỏ sót dependency | Uncertainty + fallback + paired eval |
| Orphan/wrong-base worktree | Durable ownership + base revision + lease/job fence + idempotent cleanup |
| Secret exfiltration | Opaque handles + scoped injection + deny-by-default + negative tests |
| CAS/cache sai môi trường | Chỉ cache deterministic data; execution cache cần hermetic key đủ mạnh |
| Reconnect retry duplicate side effect | Giữ exactly-once execution identity; explicit unknown/recovering/lost; no unsafe replay |
| Roadmap drift | Explicit decision trước Wave 2+; Wave 0/1 bounded hardening/audit |

---

# 15. Rollback strategy

```text
context compiler -> fallback current semantic/text path
semantic index    -> discard/rebuild index; source untouched
worktree mode     -> fallback canonical single-task mode
capability worker -> disable privileged code mode
OTEL export       -> disable exporter; ledger remains canonical
MCP Tasks adapter -> disable negotiation; core Job path unchanged
Computer Use      -> policy disabled
shadow evaluation -> disable shadow enrollment; primary behavior unchanged
```

Rollback không được xóa evidence ledger hoặc giả rằng side effect chưa xảy ra.

---

# 16. Việc không nên làm trong phase này

- tăng public MCP tools từ 8 lên hàng chục chỉ để expose internal primitives;
- thay EOCL/ledger bằng MCP Tasks;
- thay Job semantics bằng UI/App orchestration;
- dùng CRDT làm default source-code concurrency layer khi Git worktree + promotion phù hợp hơn;
- build P2P mesh/QUIC fabric trước khi reverse relay use case đòi hỏi;
- gọi Windows Job Object hoặc Landlock riêng lẻ là complete sandbox;
- cache test/build không hermetic;
- cho shadow model mutation canonical checkout;
- mở A2A nếu chưa có external consumer thật;
- broad upstream merge;
- mở lại P0–P3 chỉ vì một evidence cohort khác còn đang thu thập;
- chỉnh `.coding-tools` evidence để report “đẹp hơn”.

---

# 17. Kế hoạch hành động ngay sau tài liệu

## Nếu giữ roadmap hiện tại làm primary

1. Không mở architecture rewrite ngay.
2. Hoàn tất current WIP theo owner/acceptance hiện hành.
3. Làm W0 feature-family audit.
4. Đo current model-facing payload/semantic fallback/caller attribution baseline.
5. Chỉ lấy quick win W1–W3 nếu không phá P4/P5.
6. Chuẩn bị ADR/roadmap change riêng nếu muốn mở Wave 2.

## Nếu reprioritize sang `Next Runtime Foundation`

1. Mở W4 Semantic Repository Graph trước.
2. Chỉ làm W5 Context Compiler khi graph/provider health đủ ổn định.
3. Sau paired evaluation, mở W6 transactional worktrees.
4. Sau worktree proof, mở W7 capability/secret boundary.
5. Chỉ sau W7 mới mở Computer Use production.
6. CAS/tracing được generalize theo nhu cầu thực tế, không làm platform rewrite độc lập.
7. Shadow models/A2A để sau isolation + evidence.

---

# 18. Definition of Done cho `Next Runtime Foundation`

Phase chỉ hoàn thành khi chứng minh được:

1. **Context intelligence:** semantic localization + safe fallback hoạt động; Context Compiler giảm discovery overhead trên representative tasks mà không làm quality xấu đi.
2. **Transactional mutation:** concurrent lanes không trực tiếp đạp canonical checkout; promotion có base/proof/EOCL gate.
3. **Privilege boundary:** process/network/computer/secrets qua capability evaluation thống nhất; secret không đi vào model context.
4. **Provenance:** artifact/index/context/workspace identity có content/source fingerprint đủ phát hiện stale data.
5. **Observability:** task có causal trace caller -> route -> tool/executor -> proof/acceptance không cần timestamp heuristic.
6. **Recovery:** reconnect/restart giữ fail-closed retry semantics, không duplicate unsafe side effects.
7. **Surface discipline:** `smart-v3` vẫn nhỏ/coherent; internal intelligence không thành hàng loạt public tools.
8. **Evidence discipline:** source, focused proof, live activation, packaging và empirical efficacy vẫn là claim riêng.

---

# 19. Quyết định kiến trúc được khuyến nghị

### A — Đồng ý về hướng, chưa mở toàn bộ implementation cùng lúc
Triển khai theo capability nhỏ và evidence gate, không big-bang rewrite.

### B — Semantic Graph + Context Compiler là khoản đầu tư intelligence lớn nhất
Project đã có semantic/LSP foundation, nên đây là nơi leverage cao nhất mà không cần mở thêm model-facing tool surface.

### C — Worktree isolation là điều kiện để multi-model trở thành parallel engineering thật
Không mở autonomous multi-lane mutation trên canonical checkout trước khi task workspace/promotion contract đủ rõ.

### D — Capability/Secret boundary phải đi trước Computer Use
Computer Use phải được coi là privileged executor, không phải UI feature thuần túy.

### E — Generalize cái đã có, không xây subsystem trùng lặp
Artifact content addressing -> CAS khi cần; semantic localization -> repository graph; evaluation replay -> tracing/replay integration; tunnel -> device/lease khi use case cần; P4/P5 measurement -> context/router/shadow evaluation.

---

## Appendix A — `smart-v3` public contract cần bảo toàn

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

`restart_runtime` là action của `task_control`, không phải public tool thứ chín.

---

## Appendix B — Current roadmap constraints

- P0 runtime/error boundary: engineering closed, live activation accepted cho instance đã xác minh.
- P1 measurement integrity: engineering closed; economics vẫn evidence-gated.
- P2 rework diagnosis: closed; historical evidence limitations không mở lại architecture.
- P3 compute-placement control: engineering accepted; representative server-first efficacy vẫn deferred; global server-first OFF.
- P4 Solution Economics Shadow: source/gate accepted, evidence collecting; predictive readiness chưa được phép suy diễn.
- P5 Controlled Rework Reduction: treatment gated; không auto-start.
- `execution_route=auto`: deterministic fail-closed cho đến khi evidence gate thay đổi.
- auto-handoff: OFF.
- provider/model write authority: không được cấp chỉ nhờ telemetry/routing.

---

## Appendix C — Source-of-truth docs khi bắt đầu implementation

1. `AGENTS.md`
2. `docs/CURRENT_STATE.md`
3. `docs/ROADMAP.md`
4. `docs/ARCHITECTURE.md`
5. `docs/MODEL_EXECUTION.md` trong phạm vi WebCodex core execution subsystem
6. `docs/TESTING.md` cho validation scope
7. authority/security/release docs tương ứng với subsystem được thay đổi

Dated documents dưới `docs/research/` là historical evidence; không dùng chúng để override current product truth.
