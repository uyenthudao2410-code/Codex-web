# Coding Web — Đánh giá kỹ thuật, kế hoạch triển khai và nhật ký kiểm soát

> **Baseline đánh giá ban đầu:** 2026-08-20  
> **Chuyển sang active implementation control:** 2026-08-20  
> **Checkpoint cập nhật gần nhất:** 2026-08-20 18:20 +07:00  
> **Workspace canonical:** `E:\DEV\Codex-web`  
> **Topology được operator chốt:** **một checkout canonical, một source writer tại một thời điểm, không dùng Git worktree cho chương trình này**  
> **Product:** Windows Electron Execution Hub + Recovery Host + **một** Coding Tools MCP Runtime  
> **Coding Tools contract:** `smart-v3`, giữ đúng **8 public tools**  
> **Git baseline của chương trình active:** `main` @ `66c2d17b68969c3a413b867cc7281f80fbaf4b45`  
> **Loại tài liệu:** technical assessment + active implementation control log. Tài liệu này không override `AGENTS.md`, `docs/CURRENT_STATE.md`, `docs/ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/MODEL_EXECUTION.md` hoặc authority/security/release docs tương ứng.

---

# 0. Implementation Control — ACTIVE

## 0.1. Mục đích điều hành

Từ checkpoint ngày 2026-08-20, tài liệu này được operator yêu cầu dùng để **theo dõi và kiểm soát triển khai thực tế**, không chỉ làm proposal. Mọi wave material phải cập nhật lại đây với tối thiểu:

- scope thực tế;
- RUN/WAVE hoặc durable execution identity nếu có;
- source baseline/fingerprint liên quan;
- file/surface đã thay đổi;
- proof thực sự đã chạy;
- trạng thái `PLANNED / IN_PROGRESS / REPLAN / ACCEPTING / ACCEPTED / BLOCKED / DEFERRED`;
- claim level: source / focused proof / live active / packaged-released;
- blocker, risk và next critical action.

Không ghi “done” nếu mới có source mà chưa có proof. Không ghi “live” nếu runtime đang chạy chưa load behavior đó. Không ghi “released” nếu package/release boundary chưa được kiểm chứng.

## 0.2. Quy tắc topology đã chốt

Chương trình này **không sử dụng Git worktree để cô lập mutation**. Contract thay thế là:

```text
Read/review/candidate lanes
          |
          | no direct source mutation
          v
+-----------------------------------+
| EOCL + Canonical Mutation Control |
| one active source write lease     |
+----------------+------------------+
                 |
                 | one writer only
                 v
          E:\DEV\Codex-web
               main
                 |
          focused proof
                 |
       ChatWeb/Sol acceptance
                 |
          release write lease
```

Các nguyên tắc bắt buộc:

1. Chỉ **một active source writer/write lease** trên checkout canonical tại một thời điểm.
2. Session/lane không sở hữu lease chỉ được read/search/LSP/review hoặc tạo candidate patch; không tự apply source patch.
3. Writer phải bind với `base_head`, source/workspace fingerprint và dirty-source snapshot trước mutation.
4. Foreign dirty source xuất hiện ngoài ownership đã ghi nhận => fail closed sang `REPLAN` trước mutation tiếp theo.
5. Không đổi route/mode/write owner bằng implication.
6. Một material wave phải proof + acceptance/checkpoint trước khi mở writer wave kế tiếp.
7. Reconnect/restart không được tạo writer thứ hai hoặc replay side effect không an toàn.
8. `.coding-tools` telemetry/evidence volatility không được nhầm với source contention; nhưng evidence vẫn phải được bảo toàn theo repository policy.
9. `coordinated_multi_worktree` không nằm trên critical path của chương trình này; không dùng nó để né single-writer authority.
10. Git commit/push/restart/deploy/release là boundary riêng, không được suy ra từ source acceptance.

## 0.3. Active status board

| Stage | Scope | Status | Evidence / checkpoint | Next gate |
|---|---|---|---|---|
| **S0** | P4 residual closeout | **ACCEPTED** | RUN `f914183e232d4684aab696e81c1144df`, WAVE `5752420f2e44402f885bf9f9b4ec3294`; `test_orchestration_tax.py` **3/3 PASS**; `test_model_extreme_closeout.py` **2/2 PASS**; proof fp `aec5f237b342c5285efc4b83664964c31c9c3c7e30b54716b6a759b05b306365` | Preserve accepted diff; no implicit commit/push |
| **S1** | Convert proposal -> active control plan; replace worktree design | **ACCEPTED** | Active control plan established; single-checkout/single-writer topology, W6 coordinator contract and W14 candidate-only shadow are now authoritative for this program | Keep document synchronized after each accepted/material wave |
| **S2** | W0 baseline + W1/W2/W3 audit and bounded quick wins | **IN_PROGRESS** | **W3 ACCEPTED/CHECKPOINTED** on RUN `405ae4561b174ae9b228fdbdf6a172ec`, WAVE `c5ff66f9602e4bfda9982e7d36938bb1`; W0/W1/W2 remain to close | Finish current-vs-upstream-vs-proposed matrix and evidence-backed W1/W2 deltas |
| **S3** | Semantic provider health + W4 Semantic Repository Graph MVP | **PLANNED** | Native provider currently reported unavailable with `NATIVE_LSP_BINDING_NOT_CONFIGURED`; safe fallback required | Focused graph/provider proof |
| **S4** | W5 Context Compiler + paired evaluation | **PLANNED** | Deterministic context packet, budget/dedupe/stale handling | Representative efficacy gate |
| **S5** | W6 Single-Checkout Mutation Coordinator | **PLANNED** | Single-writer lease, dirty ownership/fingerprint fence, reconnect rules | Concurrency/fail-closed proof |
| **S6** | W7 Capability Policy + Secret Broker foundation | **PLANNED** | Threat model + negative security proof | Security gate before privileged features |
| **S7** | W9 CAS + W10 trace/replay + W11 adapter + W13 job audit | **PLANNED** | Generalize existing foundations only where a concrete gap exists | Subsystem-specific acceptance |
| **S8** | W8 Computer Use + W12 relay/device lease | **GATED** | Requires W7 security minimum and attribution/trace coverage | Privileged-action gate |
| **S9** | W14 shadow evaluation + W15 A2A decision | **GATED / DEFERABLE** | Shadow is candidate-only; A2A requires concrete consumer | Evidence/use-case gate |

## 0.4. S0 checkpoint — P4 residual closeout

Hai defect còn lại sau post-P4-MX acceptance review đã được proof lại trên đúng harness:

- missing provider usage không còn bị diễn giải thành `0`; trạng thái không quan sát được giữ `unknown/null` và làm evaluation `HOLD`;
- model-extreme closeout summary dùng separator ASCII deterministic và regression kiểm `rendered.isascii()`.

Focused proof đã chạy:

```text
resources/coding-tools-mcp/tests/test_orchestration_tax.py
  3 passed

tests/model_eval_pack/test_model_extreme_closeout.py
  2 passed
```

EOCL final acceptance: **ACCEPTED / CHECKPOINTED**. Proof wave không tạo source write mới; nó xác nhận residual diff đã tồn tại trên current source fingerprint. **Chưa suy ra commit/push/restart/deploy/release.**

## 0.5. S1 checkpoint — active control plan / topology migration

**Status: ACCEPTED (document/source-control contract level).**

Tài liệu đã được chuyển từ proposal sang active implementation control log và chốt các quyết định:

- canonical checkout duy nhất là `E:\DEV\Codex-web`;
- không dùng Git worktree làm dependency của chương trình;
- source mutation serialize qua EOCL/write lease; read/review/candidate có thể song song nhưng không có direct write authority;
- W6 được định nghĩa lại thành **Single-Checkout Mutation Coordinator**;
- W14 shadow model được giới hạn **read/candidate-only**, không direct apply/commit/promotion;
- claim `source / focused proof / live active / packaged-released` được tách riêng;
- mỗi material wave phải proof + acceptance trước writer wave kế tiếp.

Checkpoint S1 không phải runtime activation proof; nó là **accepted implementation-control contract** cho các wave tiếp theo.

## 0.6. S2/W3 checkpoint — authenticated caller attribution

**CHECKPOINT:** `S2 / W3 / caller-attribution-and-audit-coverage`  
**TIME:** `2026-08-20T18:20:11+07:00`  
**STATUS:** **ACCEPTED / CHECKPOINTED**  
**BASE:** `66c2d17b68969c3a413b867cc7281f80fbaf4b45`  
**RUN/WAVE:** RUN `405ae4561b174ae9b228fdbdf6a172ec`, accepted WAVE `c5ff66f9602e4bfda9982e7d36938bb1`  
**PROOF FP:** `fba256afea4ff23154eb40fcb91e26f1bee268855ea491033f940debeac03a85`

W3 đã port/adapt các invariant caller-attribution cần thiết vào kiến trúc hiện tại mà không tạo auth plane mới:

- `action_events` lưu nullable snapshot `principal_kind`, `principal_user_id`, `oauth_client_id`;
- historical rows giữ `NULL`, không infer/backfill identity cũ;
- `oauth_client_id` chỉ lấy từ `allowed_client_id` khi `AuthContext::is_oauth_token()` là true; agent token có `allowed_client_id` không bị misattribute thành OAuth client;
- ordinary audit-session event response không expose ba field identity mới;
- `/api/audit/stats` chỉ expose aggregate principal-kind/OAuth-client counts, không expose stable user IDs;
- stats có `events_scanned`, `events_available`, `sessions_scanned`, `truncated_sessions`, `partial`, `truncated`;
- unknown scoped session trả 404;
- DB read lỗi trên selected sessions fail request thay vì silently skip;
- count + bounded rows của một session đến từ một SQLite read transaction/snapshot;
- OAuth client name được resolve cho aggregate stats khi record hợp lệ.

**Changed source surfaces:**

```text
src/action_audit.rs
src/models.rs
src/action_audit_sessions.rs
src/db/schema.rs
src/db/audit.rs
src/audit_http/routes.rs
src/audit_http/tests.rs
```

**Focused proof thực sự đã chạy và PASS:**

```text
cargo fmt -p webcodex -- --check
  PASS
  proof_id: 52dbf1f3b8a34b069c51d8c6f6209b81

cargo check -p webcodex --lib
  PASS
  proof_id: 406d7725e73b4212982763b9bcea4449

cargo test -p webcodex action_audit --lib
  PASS
  proof_id: 7195b72fb8d84ea89e4f58f54daa470f

cargo test -p webcodex audit_http --lib
  PASS
  proof_id: ab8007c9988a46aaab6dbb65daac39c9

cargo test -p webcodex legacy_action_events_gain_nullable_caller_attribution --lib
  PASS
  proof_id: 8e205c09d55c4493ac21de50c0a26a72
```

ChatWeb/Sol final-controller review đã kiểm full 7-file diff và adjacent-risk `agent allowed_client_id != oauth_client_id`. EOCL final state: **CHECKPOINTED / ACCEPTED**.

**Claim:** source + focused proof. **Không claim live-active/package/released. Chưa commit/push/restart/deploy/release.**

**Next critical action:** hoàn tất W0/W1/W2 audit và chỉ implement sparse/artifact delta có evidence trước khi mở S3.

---

# 1. Mục tiêu kỹ thuật

Tài liệu trả lời bốn câu hỏi:

1. Coding Web đang thực sự có gì ở source, focused proof, live runtime và package/release boundary?
2. Kỹ thuật nào còn có ROI sau khi đối chiếu current architecture và upstream WebCodex?
3. Capability nào là mới, capability nào chỉ nên generalize foundation đã có, và capability nào phải defer?
4. Triển khai theo thứ tự nào để giảm rework, giữ EOCL/authority, giữ 8-tool surface và không tạo source-of-truth thứ hai?

Mục tiêu không phải biến Coding Web thành framework tổng quát. Mục tiêu là làm nó mạnh hơn như một **stateful coding operating layer cho nhiều model/client dùng chung một execution authority, có evidence, recovery, deterministic mutation control và policy rõ ràng**.

---

# 2. Kết luận điều hành

## 2.1. Product truth

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

Coding Web không còn nên được đối xử như một WebCodex fork thuần kiến trúc. Upstream là nguồn invariant/feature-family để audit và port có chọn lọc, không phải nguồn diff để broad merge.

## 2.2. Ba khoản đầu tư có ROI cao nhất sau quyết định single-checkout

1. **Semantic Repository Graph + Context Compiler** — giảm search/read/context churn trước khi model thấy tool surface.
2. **Single-Checkout Mutation Coordinator** — biến EOCL/write lease hiện hữu thành deterministic source-mutation contract cho nhiều client mà không cần worktree.
3. **Capability Policy + Secret Broker + isolated worker boundary** — hoàn thiện trust boundary trước Computer Use, privileged network/browser hoặc remote execution capability.

Định hướng:

> **Giữ model-facing surface nhỏ, làm runtime phía sau thông minh hơn.**

## 2.3. Reprioritization đã được operator chấp thuận

Proposal ban đầu yêu cầu một decision gate trước khi mở `Next Runtime Foundation`. Decision đó hiện đã có: operator yêu cầu triển khai toàn diện theo wave, dùng checkout canonical và cập nhật tài liệu này thường xuyên.

“Triển khai toàn diện” không có nghĩa bật mọi speculative feature. Nó có nghĩa:

- triển khai mọi foundation có acceptance contract rõ;
- audit rồi `skip/adapt/port/replace/defer` với evidence;
- giữ Computer Use/relay/shadow/A2A sau đúng security/evidence gate;
- không big-bang refactor;
- không mở writer song song.

---

# 3. Invariant và claim discipline

Mọi capability được đánh giá theo bốn tầng độc lập:

| Tầng | Ý nghĩa |
|---|---|
| **Source present** | Code/module/schema có trong checkout |
| **Focused proof** | Test/check tập trung chứng minh behavior |
| **Live active** | Runtime đang chạy đã load source và behavior quan sát được trên tool plane thật |
| **Packaged/released** | Behavior đã qua package/release boundary tương ứng |

Invariant phải giữ:

- một Coding Tools Runtime authority cho workspace/ledger chính;
- ChatWeb/Sol là semantic controller/final acceptance authority trong coordinated work;
- EOCL + permission + write lease là mutation authority;
- deterministic proof ưu tiên hơn model debate khi có oracle mạnh;
- `execution_route=auto` fail-closed về deterministic cho tới khi evidence gate thay đổi;
- provider/model lane không có write authority chỉ vì router gọi được nó;
- `smart-v3` giữ đúng 8 public tools;
- `.coding-tools` volatility không tham gia source fingerprint;
- không tạo authority/store/ledger thứ hai cho capability mới;
- không gọi source-present là live-active hoặc packaged-released.

---

# 4. Thực trạng kỹ thuật

## 4.1. Nền tảng đã mạnh, không xây lại

| Capability | Trạng thái | Nhận định |
|---|---|---|
| One-runtime authority | Đã xác lập | Recovery Host/Execution Hub sở hữu lifecycle; Coding Tools MCP là mutation/proof authority |
| EOCL / durable orchestration | Đã có sâu | Run/wave state, proof lineage, acceptance boundary, write lease |
| Durable evidence | Đã có | Orchestration ledger là causal audit source |
| Smart surface | Đã có | `smart-v3` = 8 tools |
| Recovery architecture | Đã có mạnh | Recovery Host/Supervisor/MCP/Tunnel và watchdog |
| Structured execution | Đã có | argv/script payload, Job handoff/observation |
| Same-Runner reconciliation | Đã có | Reconcile active/terminal jobs trong semantics hiện tại |
| LSP process/resource governance | Đã có | Identity, memory telemetry, pressure/reaping policy |
| Validation intelligence | Đã có | Structured parser, bounded diagnostics, validation feedback |
| Compute placement | Engineering accepted | `local_only` / `server_preferred`; global server-first evidence-gated |
| Provider routing/economics | Đã có | Explicit routes, provider telemetry, solution economics shadow |
| Evaluation/replay | Đã có foundation | Reuse thay vì xây analytics framework khác |
| Artifact content addressing | Đã có một phần | Content hash/ref foundation |
| Tunnel/recovery connectivity | Đã có một phần | Formalize lease/identity nếu W12 được mở |
| OAuth/auth/audit | Đã có foundation + W3 focused proof | W3 durable caller attribution accepted; không tạo auth plane mới |

## 4.2. Foundation chưa hoàn chỉnh

### Semantic localization

`semantic_localization.py` và LSP infrastructure đã tồn tại, nhưng runtime observation gần nhất báo native semantic provider unavailable vì `NATIVE_LSP_BINDING_NOT_CONFIGURED`. W4 phải xử lý health/fallback như một contract first-class; không giả semantic completeness.

### Canonical mutation coordination

Runtime đã có EOCL, write lease, source/workspace fingerprint và coordination vocabulary. Khoảng trống cần chứng minh/đóng là **single-checkout source ownership**:

- một source writer duy nhất;
- bind mutation vào base HEAD/fingerprint;
- snapshot dirty-source ownership;
- detect foreign dirty source;
- route/candidate lane không tự nâng quyền;
- reconnect không tạo duplicate writer;
- acceptance trước writer wave kế tiếp.

Không xây task-worktree subsystem trong chương trình này.

### Sandbox / code mode

Experimental code mode vẫn phải fail closed khi isolated worker guarantees chưa đủ. Windows Job Object là lifecycle/resource primitive, không phải full sandbox; Landlock hiện hữu chỉ là một layer. W7 cần generalize permission/EOCL/execution-resource controls thành capability decision và secret boundary.

### CAS / Merkle

Artifact content addressing đã có; W9 chỉ generalize khi graph/context/artifact consumers cần cùng identity substrate. Không tạo storage system trùng lặp.

### Tracing / replay

Project đã có `turn_id`, `trace_id`, `span_id`, performance telemetry, host observations và evaluation replay. W10 chuẩn hóa propagation/correlation, không “thêm observability từ đầu”.

## 4.3. Chưa đủ evidence để gọi first-class product subsystem

- persistent **Semantic Repository Graph**;
- **Context Compiler** có budget, `already_seen`, stale/uncertainty contract;
- hardened **Single-Checkout Mutation Coordinator** với foreign-dirty/reconnect fencing được proof;
- unified **Capability Policy** cho filesystem/process/network/computer/secrets;
- first-class **Secret Broker** với opaque handles;
- generalized CAS/Merkle workspace identity;
- OTEL/W3C propagation end-to-end;
- first-class reverse-relay/device-lease orchestration;
- MCP Tasks/Elicitation adapter mapped vào durable ledger;
- A2A gateway;
- shadow-model candidate pipeline có no-write/no-promotion guarantee;
- Computer Use như security-gated subsystem.

---

# 5. Ma trận ưu tiên

| ID | Workstream | Ưu tiên | Giá trị | Rủi ro | Ghi chú active |
|---|---|---:|---:|---:|---|
| W0 | Baseline + upstream feature-family audit | P0 | Cao | Thấp | S2 — in progress |
| W1 | Sparse model-facing projection audit | P0 | Cao | Thấp–TB | S2; port invariant, không broad merge |
| W2 | Artifact bridge/import/export/streaming audit | P0 | Cao | TB | S2; generalize `artifact_refs` |
| W3 | Caller attribution audit | P0 | Cao | Thấp–TB | **S2 ACCEPTED/CHECKPOINTED**; source + focused proof |
| W4 | Semantic Repository Graph | P0 | Rất cao | TB–Cao | S3; provider health + safe fallback |
| W5 | Context Compiler | P0 | Rất cao | TB | S4; treatment trước auto-enable |
| W6 | **Single-Checkout Mutation Coordinator** | P0 | Rất cao | Cao | S5; one writer, no worktree |
| W7 | Capability Policy + Secret Broker | P0 | Rất cao | Cao | S6; security foundation |
| W8 | Computer Use | P1 | Cao | Cao | S8; sau W7 |
| W9 | Generalized CAS + Merkle identity | P1 | Cao | TB | S7; generalize foundation |
| W10 | Trace-context + replay integration | P1 | Cao | TB | S7 |
| W11 | MCP 2026 adapter layer | P1 | TB–Cao | TB | S7; adapter-only |
| W12 | Reverse relay / device lease | P1 | Cao | Cao | S8; sau W7/W10 |
| W13 | Detached Job restart invariant audit | P1 | Cao | TB–Cao | S7; implement only proven gap |
| W14 | Shadow model evaluation | P2 | Cao | TB–Cao | S9; **read/candidate-only** |
| W15 | A2A gateway | P2 | TB | TB–Cao | S9; defer nếu chưa có consumer |

---

# 6. Kiến trúc đích

```text
GPT / Claude / Gemini / Codex / CLI
                  |
          MCP protocol adapter
          A2A adapter (later, gated)
                  |
        +---------+----------+
        |                    |
  Task Coordinator      Durable Ledger / EOCL
        |                    |
  Context Compiler      Trace / Evidence / Replay
        |                    |
 Semantic Repo Graph         |
        |                    |
        +-- Canonical Mutation Control --+
                         |
                 one source writer
                 base/fingerprint fence
                 dirty ownership fence
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
                 proof / acceptance
                         |
                Canonical Repository
```

Các layer mới nằm sau 8-tool surface. Ví dụ:

```text
agent_workflow
 -> context compiler
 -> canonical mutation coordinator
 -> capability evaluator
 -> existing executor/tool primitives
```

Không tạo public tool mới nếu internal primitive đáp ứng được qua contract hiện hữu.

---

# 7. Workstream chi tiết

## W0 — Baseline và feature-family audit

Tạo matrix `current vs upstream vs proposed` ở cấp behavior/invariant cho:

1. sparse model projection (#105 family);
2. artifact bridge/import/export/streaming (#46/#55 family);
3. authenticated caller attribution (#82/#83 family);
4. Computer Use (#45 -> #107 family);
5. detached Job restart-survival (#96/#101 family);
6. release/platform hardening liên quan trực tiếp.

Mỗi family phải nêu:

- current behavior;
- upstream invariant;
- missing invariant;
- conflict với Desktop/Recovery authority;
- quyết định `skip / adapt / port / replace / defer`;
- proof cần thiết.

**Current S2 note:** W3 đã chuyển từ audit sang accepted adapted implementation; W1/W2 vẫn phải đóng bằng exact delta evidence trước khi S2 được accepted.

**Acceptance:** đủ evidence để trả lời “vì sao thay đổi hoặc không thay đổi” trước mutation.

## W1 — Sparse model-facing projection

Đo payload thực tế của `workspace_context`, `agent_workflow prepare`, read/search equivalents, successful process/script execution, validation completion và job observation.

Theo dõi:

- bytes/model turn;
- tool-result tokens nếu measured;
- tool hops đến first causal edit;
- follow-up read rate;
- TTAR / first-pass acceptance.

Chỉ giảm payload nếu vẫn giữ failure class, `timeout/outcome_unknown`, continuation identity, proof/source identity và retry-safety semantics.

**S2 state:** upstream sparse projection invariant đã được xác định là partially present trong fork; exact missing projection surfaces vẫn phải được localized trước patch. Không broad-port PR #105.

## W2 — Artifact pipeline

Generalize `artifact_refs.py` và content-hashed refs thay vì xây Artifact System thứ hai. Audit/bổ sung nếu thiếu:

- conversation attachment -> registered project import;
- authenticated project export/resource;
- streaming + bounded size;
- cancellation/disconnect;
- atomic finalization;
- cleanup partial transfer;
- content hash/provenance xuyên import/export.

Artifact identity tối thiểu: `artifact_id`, `content_hash`, `size`, `media_type`, owner task/run/wave, source kind, creation/retention và safe locator.

**S2 state:** current source đã có conversation import, artifact upload begin/chunk/finish/abort và Runner streaming path; export/resource/provenance invariants còn phải audit chính xác. Không tạo tool hoặc artifact authority mới.

## W3 — Authenticated caller attribution

**Status: ACCEPTED / CHECKPOINTED tại S2.** Xem §0.6.

Action quan trọng giờ có durable snapshot principal attribution ở `action_events` cho các HTTP/MCP action đi qua `ActionAudit`, với nullable legacy compatibility. Attribution chỉ ghi nguồn thực hiện; authorization vẫn thuộc auth/EOCL/policy.

Accepted invariants:

- `principal_kind`, optional `principal_user_id`, OAuth-only `oauth_client_id` được snapshot tại action-event write time;
- agent `allowed_client_id` không bị misreport là OAuth client;
- legacy rows giữ NULL;
- ordinary audit event API không expose stable identity fields;
- audit stats chỉ expose aggregate identity counts và explicit scan/truncation coverage;
- scoped missing session = 404;
- selected-session DB read errors fail closed;
- count + bounded rows lấy từ một SQLite snapshot.

Không lưu raw token/window/path ngoài policy. W3 hiện chỉ claim **source + focused proof**.

## W4 — Semantic Repository Graph

### Mục tiêu

Index read-only, incremental, hash-bound theo source revision trên semantic/LSP foundation.

### V1 model

```text
File
Symbol
Definition
Reference
Import/module relation
Test association
content/source hash
provider + provider version
confidence + completeness
```

Call/implementation edge chỉ thêm khi provider đủ đáng tin. Không bắt đầu bằng general graph database.

### Provider strategy

1. native LSP khi health/binding hợp lệ;
2. language-specific provider khi có concrete need;
3. bounded text fallback khi semantic unavailable.

Không chạy repository code để index.

### Internal API mục tiêu

```text
semantic_graph.resolve_symbols(query, budget)
semantic_graph.references(symbol_id, budget)
semantic_graph.related_tests(symbol_id, budget)
semantic_graph.impact(seed_symbols, depth, budget)
```

### Acceptance

- result project-relative/redacted;
- unavailable/degraded provider có structured fallback;
- stale index không được coi current;
- incremental update có budget;
- confidence/completeness explicit;
- không tăng LSP churn ngoài governance.

## W5 — Context Compiler

```text
task intent
   -> semantic graph + Git/source identity + rules + dirty diff + recent evidence
   -> deterministic context compilation
   -> minimal evidence packet
   -> model
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

`CompiledContext` gồm primary files/symbols, entry points, relevant relations/tests/config/rules, related dirty diff, uncertainty/warnings, omitted candidates + reason và stable fingerprints.

Không auto-enable chỉ vì source tồn tại. Paired representative evaluation phải so current bounded semantic/text path với treatment compiler.

## W6 — Single-Checkout Mutation Coordinator

### Mục tiêu

Dùng một checkout canonical nhưng làm ownership/mutation deterministic và fail-closed cho nhiều client/lane.

### Data contract V1

```text
MutationLease {
  run_id
  wave_id
  owner_session
  base_head
  source_fingerprint
  runtime_worktree_fingerprint   # tên field tương thích nếu runtime hiện dùng worktree_fp
  allowed_paths
  protected_paths
  existing_dirty_source_paths
  started_at
  state
}
```

`runtime_worktree_fingerprint` ở đây là fingerprint của checkout hiện hành, **không** hàm ý tạo Git worktree.

### Admission trước source write

```text
active_source_write_lease_count == 1
current_head == lease.base_head
current_source_fp compatible with expected pre-write state
foreign_dirty_source_paths == empty
requested_paths subset of allowed_paths
requested_paths disjoint from protected_paths
EOCL state == EXECUTING
write_owner/session matches lease
```

Bất kỳ invariant nào sai => typed failure + `REPLAN`; không tự restore/reset/rebase/merge.

### Candidate/reviewer lanes

Candidate/reviewer có thể:

- read/search/LSP;
- review diff/evidence;
- đề xuất exact patch/replacement;
- chạy read-only analysis.

Candidate/reviewer không được:

- apply source patch trực tiếp;
- đổi write owner;
- commit/reset/checkout source;
- bypass EOCL bằng transport/provider khác.

### Acceptance

- hai concurrent client không cùng sở hữu active source lease;
- foreign dirty source được phát hiện trước write tiếp theo;
- reconnect không nhân đôi writer;
- release/terminalization làm lease state deterministic;
- accepted proof bind đúng source fingerprint;
- `.coding-tools` evidence churn không gây false-positive source contention;
- no worktree/promotion subsystem được tạo để giải bài toán này.

## W7 — Capability Policy + Secret Broker + isolated worker

Generalize permission/EOCL/execution-resource controls hiện có:

```text
CapabilitySet {
  filesystem: read_roots / write_roots
  process: executable_class / max_processes / runtime
  network: denied | allowlist
  computer: screen / mouse / keyboard / clipboard
  secrets: opaque_handle_allowlist
  artifact: import/export bounds
}
```

Derived từ:

```text
principal + project + EOCL state + write lease + task policy + tool intent
```

### Secret Broker

Model/tool schema chỉ thấy opaque handle, ví dụ:

```text
secret://github/release
secret://npm/publish
secret://provider/account-x
```

Recovery Host/Electron tiếp tục sở hữu secret. Executor nhận scoped injection tại execution boundary; raw secret không đi vào prompt/tool result/audit.

### Required guarantees

- không inherit full host env mặc định;
- network deny-by-default cho worker nhạy cảm;
- explicit fs roots;
- bounded subprocess;
- framed/bounded IPC;
- timeout/kill ownership rõ;
- capability decision có audit event;
- model-provided field không elevate policy.

## W8 — Computer Use

Chỉ mở production sau W7 minimum security contract.

V1 bounded capability:

- snapshot/screenshot;
- mouse click;
- keyboard input;
- bounded scroll;
- display/window selection;
- clipboard opt-in;
- authenticated artifact/resource ref cho snapshot.

Policy levels:

```text
observe_only
interactive_low_risk
sensitive_action_requires_approval
blocked
```

Credential dialogs, destructive OS controls, financial/payment flows và secret-bearing clipboard là sensitive.

## W9 — Generalized CAS + Merkle identity

Generalize artifact content-addressing có chọn lọc cho:

- artifacts;
- source/file blobs khi policy cho phép;
- semantic index shards;
- compiled-context entries;
- deterministic derived metadata;
- safe reusable read/tool results.

`.coding-tools` evidence, credential và local-only path không tham gia source identity. Không cache command/test result nếu hermetic key chưa đủ mạnh.

## W10 — Trace-context + replay

Chuẩn hóa correlation:

```text
ChatWeb -> MCP -> Runtime -> router/provider -> executor/runner -> LSP/process/job -> proof/acceptance
```

- map trace/span sang W3C Trace Context khi transport hỗ trợ;
- OTEL là exporter/adapter, ledger vẫn canonical;
- không lưu raw prompt/code/secret mặc định;
- giữ `observed`, `derived`, `provider-reported` timing tách biệt.

## W11 — MCP 2026 adapter

MCP Tasks/Elicitation/resume là adapter/projection vào durable Task/Job/EOCL ledger, không thay ledger hoặc core Job semantics. Client cũ phải có fallback; cancellation/reconnect không tự replay side effect.

## W12 — Reverse relay / device lease

Formalize tunnel foundation nếu use case cần:

```text
device identity
+ project grant
+ runtime instance
+ expiring connection lease
+ reconnect token/epoch
```

Stale connection không được giữ authority; reconnect không duplicate job; revocation và project boundary phải explicit.

## W13 — Detached Job restart-survival audit

Audit matrix trước implementation:

| Scenario | Current desired stance |
|---|---|
| transport reconnect, same Runner | reconcile |
| Server restart, Runner còn sống | audit exact inventory/recovery guarantee |
| Runner restart, child còn sống | implement ownership handoff chỉ nếu concrete workload cần |
| host reboot | no implicit exactly-once promise |
| replacement Runner | không inherit old job bừa |

## W14 — Shadow model evaluation, candidate-only

Shadow lane **không có filesystem mutation authority** trong topology này.

```text
Representative task
   |
   +-- Primary lane -> EOCL writer when mutation is needed -> proof/acceptance
   |
   +-- Shadow lane  -> READ ONLY / CANDIDATE ONLY
                         |
                         +-> proposed patch / diagnosis / expected surface
                         +-> NEVER direct apply
                         +-> NEVER direct commit/promotion
```

So sánh shadow candidate với accepted final diff/oracle về quality, touched surface, repair/replan, TTAR, tool hops và usage/cost khi measured. Benchmark/synthetic không auto-authorize routing.

Điều kiện mở: oracle mạnh, usage provenance đủ, candidate no-write enforcement proven và W6 single-writer contract ổn định.

## W15 — A2A gateway

Chỉ mở khi có consumer thật. Nếu mở, map vào existing Task Coordinator/EOCL; external agent không có writer authority song song. Nếu chưa có consumer: **DEFER là kết quả triển khai hợp lệ**, không phải thiếu sót.

---

# 8. Kế hoạch theo execution stage

## S0 — P4 residual closeout

**Status: ACCEPTED.** Xem §0.4.

## S1 — Active plan + topology migration

**Status: ACCEPTED.** Xem §0.5.

1. Chuyển tài liệu thành control log.
2. Loại worktree khỏi active critical path.
3. Chốt single-writer/fail-closed contract.
4. Đổi W14 thành candidate-only shadow.
5. Cập nhật dependency, risk, metrics, rollback, DoD.

**Exit đã đạt:** tài liệu nhất quán, không còn yêu cầu worktree như active execution architecture.

## S2 — W0/W1/W2/W3

**Status: IN_PROGRESS. W3 đã ACCEPTED.**

1. Snapshot baseline đại diện.
2. Feature-family audit.
3. Port/adapt chỉ gap có evidence.
4. Focused proof cho mỗi delta.

Current checkpoint:

```text
W0  feature-family matrix      IN_PROGRESS
W1  sparse projection          AUDIT / LOCALIZE EXACT DELTA
W2  artifact pipeline          AUDIT / LOCALIZE EXACT DELTA
W3  caller attribution         ACCEPTED / CHECKPOINTED
```

**Exit:** W0/W1/W2/W3 đều có quyết định rõ; quick win không phá P4/P5 semantics; mọi implemented delta có focused proof + acceptance.

## S3 — Semantic health + W4

1. Audit native semantic binding/configuration path.
2. Không bypass credential/origin/security contract để “bật cho chạy”.
3. Implement Semantic Repository Graph MVP với fallback.
4. Focused stale/incremental/confidence tests.

**Exit:** graph hữu ích ngay cả khi native provider degraded; claim live chỉ sau runtime activation proof.

## S4 — W5

1. Implement Context Compiler internal contract.
2. Budget/dedupe/`already_seen`/uncertainty/fingerprint tests.
3. Treatment flag/internal gate.
4. Paired representative evaluation.

**Exit:** chỉ auto-inject nếu efficacy gate đạt; nếu không, giữ compiler internal/manual treatment.

## S5 — W6

1. Audit existing write-lease/coordination implementation để tránh duplicate authority.
2. Bổ sung missing source-ownership/fingerprint/foreign-dirty fences.
3. Candidate no-write enforcement.
4. Reconnect/terminalization tests.
5. EOCL acceptance.

**Exit:** single-checkout nhiều client vẫn chỉ có một writer; contamination fail closed.

## S6 — W7

1. Chốt threat model V1.
2. Capability decision contract.
3. Opaque secret handles + scoped injection boundary.
4. Isolated-worker guarantees theo platform thực tế.
5. Negative tests.

**Exit:** no-secret-leak, denied capability không bypass qua child/process/network, crash không để orphan authority.

## S7 — W9/W10/W11/W13

Triển khai theo concrete consumer/gap, không platform rewrite. Mỗi subsystem có acceptance riêng.

## S8 — W8/W12

Chỉ sau W7/W10 gates. Mọi privileged action phải policy-gated, attributed, traceable, fail-closed.

## S9 — W14/W15

Shadow candidate-only sau W6/oracle gate. A2A chỉ khi consumer được xác định.

---

# 9. Dependency graph

```text
S0 P4 closeout [ACCEPTED]
 |
 v
W0 audit
 |
 +--> W1 sparse
 +--> W2 artifacts
 +--> W3 attribution [ACCEPTED]
 |
 +--> semantic provider health --> W4 semantic graph --> W5 context compiler
 |                                                   |
 |                                                   +--> paired efficacy
 |
 +--> W6 single-checkout mutation coordinator ------+--> W14 candidate-only shadow
 |
 +--> W7 capability/secret --> W8 computer use
 |            |
 |            +--------------> W12 privileged relay policy
 |
 +--> W9 CAS ------> graph/context/artifact identity consumers
 |
 +--> W10 tracing --> W12 / W14 / A2A observability
 |
 +--> W11 MCP adapters
 +--> W13 job restart audit
 `--> W15 A2A only with concrete consumer
```

Critical path:

```text
P4 closeout
 -> W0 audit
 -> semantic provider health
 -> Semantic Repository Graph
 -> Context Compiler
 -> Single-Checkout Mutation Coordinator
 -> Capability/Secret boundary
```

W6 có thể được audit sớm nếu writer contention trở thành blocker, nhưng không mở parallel source writers trong lúc chờ W6.

---

# 10. Mapping codebase

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
- transport/auth/Electron/Recovery Host modules tương ứng.

| Capability | Tích hợp ưu tiên |
|---|---|
| Semantic graph | `semantic_localization` + provider/LSP boundary |
| Context compiler | `agent_workflow` preparation + bounded handoff/startup projections |
| Single-checkout mutation | orchestration ledger/control + task state + workspace truth + coordination + write lease |
| Capability policy | permission/EOCL/execution resources |
| Secret broker | Recovery Host/Electron secret authority + executor injection boundary |
| CAS | artifact refs/storage + source fingerprint utilities |
| Trace | performance/telemetry + MCP/HTTP/runner boundaries |
| Shadow evaluation | solution economics/evaluation plumbing; candidate-only |

WebCodex core vẫn protocol-independent; Job semantics không phụ thuộc MCP Apps/Tasks/UI. Electron/Recovery Host tiếp tục sở hữu lifecycle, secrets, runtime activation, tunnels và operator control.

---

# 11. Upstream sync strategy

Không broad merge/cherry-pick range dài.

```text
upstream invariant
 -> current implementation audit
 -> minimal adapted patch hoặc explicit skip
 -> focused proof
 -> live activation proof nếu cần
 -> accept/reject
```

Thứ tự audit: sparse projection -> artifact pipeline -> caller attribution -> Computer Use sau W7 -> detached Job invariants -> release/platform hardening liên quan trực tiếp.

W3 caller attribution đã hoàn thành theo chiến lược `adapt`, không broad cherry-pick. W1/W2 tiếp tục theo cùng quy tắc.

---

# 12. Metrics và evaluation contract

Theo dõi:

- first-pass acceptance;
- repair/replan count;
- TTAR;
- critical defect / acceptance regression;
- model-facing bytes/tokens khi measured;
- tool hops đến causal change;
- semantic hit/fallback/degraded rate;
- Context Compiler precision/miss/omission categories;
- **write contention count**;
- **write-lease rejection count/reason**;
- **foreign-dirty source incidence**;
- **base/fingerprint drift rejection**;
- candidate attempted-write rejection;
- artifact transfer/dedupe;
- trace correlation completeness;
- secret/policy denial correctness;
- job recovery/lost classification;
- provider/controller cost chỉ khi measured/reported; missing luôn là unknown, không phải zero.

Mỗi treatment preregister:

```text
source/task class
oracle
baseline/control behavior
treatment flag
required invariants
measured metrics
activation/promotion gate
rollback condition
```

Representative khác benchmark/synthetic; experiment không tự đổi authority.

---

# 13. Acceptance gates

### G0 — Contract
Problem, non-goals, owner/boundary, no duplicate authority.

### G1 — Source
Smallest coherent implementation + compatibility/schema + focused tests.

### G2 — Proof
Exact changed behavior + negative/edge cases; không chạy full-suite vô điều kiện.

### G3 — EOCL acceptance
Proof lineage hoàn chỉnh; one-writer ownership rõ; no unresolved source contamination/conflict/job state.

### G4 — Live activation
Runtime-affecting change phải chứng minh running instance load accepted source; real tool path smoke; 8-tool contract nếu relevant; no raw internal exception leakage.

### G5 — Package/release
Chỉ claim sau package boundary tương ứng.

### G6 — Efficacy promotion
Representative evidence + stable oracle + no quality regression + preregistered threshold.

---

# 14. Rủi ro và control

| Rủi ro | Control |
|---|---|
| Overengineering semantic/CAS/policy | V1 chỉ implement concrete consumer/use case |
| Duplicate source of truth | Adapter/projection only; ledger/authority hiện hữu vẫn canonical |
| Context compiler bỏ sót dependency | Uncertainty + fallback + paired eval |
| Hai session cùng mutation canonical checkout | One active source lease; non-owner read/candidate-only; fail closed |
| Foreign dirty source làm proof sai fingerprint | Pre/post-write dirty snapshot + base/source fingerprint fence + REPLAN |
| Reconnect tạo duplicate writer | Durable owner/lease identity + terminalization/recovery reconciliation |
| Secret exfiltration | Opaque handles + scoped injection + deny-by-default + negative tests |
| CAS/cache sai môi trường | Cache deterministic data trước; execution cache chỉ khi hermetic key đủ |
| Retry duplicate side effect | Exactly-once identity; explicit unknown/recovering/lost; no unsafe replay |
| Roadmap drift | Status board + per-wave acceptance + frequent update vào tài liệu này |
| Attribution bị biến thành authorization plane | W3 chỉ snapshot nguồn thực hiện; auth/EOCL/policy vẫn quyết định authority |

---

# 15. Rollback strategy

```text
context compiler          -> fallback current semantic/text path
semantic index             -> discard/rebuild derived index; source untouched
single-checkout coordinator-> fallback serialized MCP-only writer; never add second writer
capability worker          -> disable privileged code mode
OTEL export                -> disable exporter; ledger remains canonical
MCP Tasks adapter          -> disable negotiation; core Job path unchanged
Computer Use               -> policy disabled
shadow evaluation          -> disable shadow enrollment; primary path unchanged
A2A                        -> keep gateway disabled/deferred
```

Rollback không xóa evidence ledger và không giả side effect chưa xảy ra.

---

# 16. Không làm

- tăng `smart-v3` từ 8 tool lên hàng chục internal primitives;
- thay EOCL/ledger bằng MCP Tasks/A2A/UI orchestration;
- cho session/lane thứ hai mutation canonical checkout trong cùng thời điểm;
- dùng Git worktree làm dependency bắt buộc của chương trình này;
- dùng CRDT làm default source-code concurrency layer;
- cho shadow model direct write/commit/promotion;
- gọi Windows Job Object hoặc Landlock riêng lẻ là complete sandbox;
- cache test/build khi chưa có hermetic identity;
- build P2P mesh/QUIC fabric trước concrete reverse-relay need;
- mở A2A nếu chưa có consumer;
- broad upstream merge;
- chỉnh `.coding-tools` evidence để report đẹp hơn;
- reset/rebase/clean unrelated WIP để tạo “clean baseline” giả;
- gọi source-present là live/released.

---

# 17. Kế hoạch hành động active

Thứ tự hiện hành:

```text
S0  P4 residual closeout                         ACCEPTED
S1  Active control plan + no-worktree topology  ACCEPTED
S2  W0 + W1/W2/W3 audit/quick wins              IN_PROGRESS
    W3 caller attribution                       ACCEPTED
    W0/W1/W2                                     NEXT
S3  Semantic provider health + W4               QUEUED
S4  W5 Context Compiler                         QUEUED
S5  W6 Single-Checkout Mutation Coordinator     QUEUED
S6  W7 Capability/Secret boundary               QUEUED
S7  W9/W10/W11/W13                              QUEUED
S8  W8/W12 privileged/distributed capabilities GATED
S9  W14/W15 empirical/external-agent layer      GATED/DEFERABLE
```

Mỗi stage được chia thành wave nhỏ đủ để:

```text
preflight
 -> one writer lease nếu cần
 -> causal change
 -> focused proof
 -> acceptance
 -> update document
 -> stage/wave tiếp theo
```

Không giữ source writer xuyên nhiều wave không liên quan.

---

# 18. Definition of Done — Next Runtime Foundation

Phase chỉ hoàn thành khi chứng minh được:

1. **Context intelligence:** semantic provider health/fallback rõ; Semantic Graph hữu ích; Context Compiler giảm discovery overhead trên representative tasks mà không làm quality xấu đi.
2. **Deterministic mutation:** một active source writer; base/source fingerprint fence; foreign dirty fail closed; candidate/reviewer không tự nâng quyền; reconnect không nhân đôi writer.
3. **Privilege boundary:** process/network/computer/secrets qua capability evaluation thống nhất; raw secret không đi vào model context/tool result/audit.
4. **Provenance:** artifact/index/context/source identity đủ phát hiện stale data; runtime evidence không làm source identity biến động giả.
5. **Observability:** task có causal trace caller -> route -> tool/executor -> proof/acceptance không join bằng timestamp heuristic.
6. **Recovery:** reconnect/restart giữ fail-closed retry semantics, không duplicate unsafe side effects hoặc writer authority.
7. **Surface discipline:** `smart-v3` vẫn đúng 8 public tools; internal intelligence không thành tool sprawl.
8. **Evidence discipline:** source, focused proof, live activation, package/release và empirical efficacy là claim riêng.
9. **Shadow discipline:** shadow/model evaluation candidate-only, không direct filesystem mutation hoặc promotion.
10. **Control discipline:** tài liệu này có checkpoint đủ để operator biết stage nào accepted, stage nào gated và proof nào thực sự tồn tại.

---

# 19. Quyết định kiến trúc active

### A — Triển khai toàn diện theo wave, không big-bang
Operator đã chấp thuận `Next Runtime Foundation` theo evidence gate. “Toàn diện” bao gồm cả quyết định defer khi gate/use case chưa đạt.

### B — Semantic Graph + Context Compiler là khoản đầu tư intelligence lớn nhất
Dùng semantic/LSP foundation đã có; không mở thêm model-facing tools.

### C — Single-checkout/single-writer thay thế worktree isolation
Multi-client không đồng nghĩa multi-writer. Parallelism được giữ ở read/review/candidate plane; source mutation được serialize qua EOCL/write lease trên checkout canonical. Foreign dirty/base drift/reconnect đều phải fail closed.

### D — Capability/Secret boundary đi trước Computer Use
Computer Use là privileged executor, không phải UI feature thuần túy.

### E — Generalize cái đã có
Artifact refs -> CAS khi có consumer; semantic localization -> graph; evaluation replay -> trace/replay; tunnel -> device lease khi cần; P4/P5 measurement -> context/router/shadow evaluation.

### F — Shadow là candidate-only
Không cần filesystem clone/worktree để đo candidate quality; so sánh proposed change/diagnosis với accepted final result và oracle, nhưng không cấp direct mutation authority.

### G — Caller attribution đã đóng ở source + focused proof
W3 đã accepted với durable nullable attribution, aggregate-only audit reporting và OAuth-only client identity. Live activation/package claim vẫn tách riêng và chưa được suy ra.

---

# Appendix A — `smart-v3` public contract phải bảo toàn

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

`restart_runtime` là action của `task_control`, không phải tool thứ chín.

---

# Appendix B — Current roadmap constraints

- P0 runtime/error boundary: engineering closed; chỉ claim live trên instance đã xác minh.
- P1 measurement integrity: engineering closed; economics evidence-gated.
- P2 rework diagnosis: closed; historical evidence limitations không tự mở lại architecture.
- P3 compute placement: engineering accepted; global server-first OFF nếu gate chưa đổi.
- P4 Solution Economics Shadow: source/gate accepted; evidence/predictive readiness vẫn phải theo recorded gate.
- P4 residual defects ngày 2026-08-20: focused proof accepted tại S0; commit/push/live/package là boundary riêng.
- P5 Controlled Rework Reduction: treatment gated; không auto-start chỉ vì S0 accepted.
- `execution_route=auto`: deterministic fail-closed cho tới khi evidence gate thay đổi.
- auto-handoff: OFF nếu maintained source-of-truth chưa đổi.
- provider/model write authority không được cấp chỉ nhờ telemetry/routing.
- W3 caller attribution: source + focused proof accepted; không đồng nghĩa runtime hiện chạy đã load behavior hoặc release artifact đã chứa nó.

---

# Appendix C — Source-of-truth precedence khi implementation

1. `AGENTS.md`
2. `docs/CURRENT_STATE.md`
3. `docs/ROADMAP.md`
4. `docs/ARCHITECTURE.md`
5. `docs/MODEL_EXECUTION.md` trong phạm vi core execution subsystem
6. `docs/TESTING.md`
7. authority/security/release docs tương ứng
8. tài liệu này dùng làm **active control log cho chương trình được operator ủy quyền**, nhưng không override maintained product truth nếu hai bên xung đột.

Khi phát hiện conflict giữa tài liệu này và source-of-truth maintained docs: ghi conflict vào control log, chuyển wave sang `REPLAN`, rồi sửa plan hoặc maintained docs theo authority phù hợp; không silently chọn một bên.

---

# Appendix D — Checkpoint template

Mỗi lần cập nhật tiến độ, thêm hoặc cập nhật entry theo mẫu:

```text
CHECKPOINT: Sx / Wx / wave-name
TIME: ISO-8601 + timezone
STATUS: IN_PROGRESS | REPLAN | ACCEPTING | ACCEPTED | BLOCKED | DEFERRED
BASE: HEAD/source fingerprint
RUN/WAVE: ids nếu runtime có
CHANGED: paths/surfaces
PROOF: exact commands/checks + pass/fail
CLAIM: source | focused proof | live active | packaged/released
RISKS: remaining material risk
NEXT: one next critical action
```

Không lưu private chain-of-thought. Chỉ lưu structured authority, state, evidence identity, proof, timing provenance và outcome.
