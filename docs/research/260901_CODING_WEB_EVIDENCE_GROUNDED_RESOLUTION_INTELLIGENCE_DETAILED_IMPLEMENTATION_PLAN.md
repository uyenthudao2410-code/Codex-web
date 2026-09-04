# CODING-WEB — EGRI DETAILED IMPLEMENTATION PLAN

## Kế hoạch triển khai chi tiết cho Evidence-Grounded Resolution Intelligence

**Ngày lập kế hoạch:** 2026-09-01

**Workspace nguồn:** `E:\DEV\Codex-web`

**Tài liệu phương pháp luận:** [`260901_CODING_WEB_EVIDENCE_GROUNDED_RESOLUTION_INTELLIGENCE_BREAKTHROUGH_METHODOLOGY_AND_IMPLEMENTATION_PROGRAM.md`](260901_CODING_WEB_EVIDENCE_GROUNDED_RESOLUTION_INTELLIGENCE_BREAKTHROUGH_METHODOLOGY_AND_IMPLEMENTATION_PROGRAM.md)

**SHA-256 tài liệu nguồn đã đọc:** `611c7ad35ae2f50612c0e78c49ecb32bf2449be534f203f56c91532d795e011d`

**Git snapshot khi lập kế hoạch:** `main @ 30b7d1b971b65034d3e4c95568c970fcc0e9380c`, khớp `origin/main`

**Evidence window:** 2026-09-01 local time; snapshot được chốt trước khi tạo tài liệu này và không được dùng như live-runtime receipt cho wave sau.

**Trạng thái tài liệu này:** `PLAN_ONLY / NO_RUNTIME_OR_EXPERIMENT_AUTHORITY`

**North Star:** `TTPR = Time to Trusted Problem Resolution`

---

# 0. Quyết định triển khai

## 0.1. Kết luận

Chương trình tiếp theo phải triển khai theo thứ tự bắt buộc `M0 → M9`, nhưng không bắt đầu lại từ số 0. Repository hiện đã có:

- Problem Revision, PRL, exact RUN/WAVE/proof/checkpoint và independent outcome receipt;
- typed Problem Frame, Resolution Envelope và counterevidence advisory;
- bounded semantic graph, semantic/text localization và content/context compiler;
- observation spans và descriptive Problem Resolution Economics;
- P5 manifest, enrollment, assignment, pre-write binding, ITT retention, A/A integrity analyzer và lifecycle controls.

Vì vậy, critical path không phải tạo thêm control plane. Critical path là đóng sáu khoảng trống sau:

1. biến bảy Golden HR case thành Case Memory có schema, applicability và negative-transfer gate;
2. chuyển counterevidence advisory thành một safety guard được controller thực thi trên managed problem-bound write path;
3. hoàn tất và chấp nhận Resolution Capsule đang là source candidate, rồi chứng minh context resumption;
4. tạo Workspace Evidence Index bounded cho đúng một HR Finance family bằng cách tái sử dụng semantic/localization foundation hiện có;
5. tạo cohort reporter read-only có quy tắc chọn natural case auditable và raw rows giữ nguyên missingness;
6. chỉ sau natural cohort mới chạy P5 A/A, rồi đăng ký một treatment EGRI mới và chạy A/B.

Không được dùng treatment hiện tại `lean-causal-fix-gate-v1` để tuyên bố đã thử EGRI. Không được mở lại epoch đã hard-stop. Không được dùng 480 accepted runs lịch sử, bảy Golden HR calibration case hoặc P4 descriptive shadows làm denominator ITT của EGRI.

## 0.2. Treatment contrast được chọn

`No same-frame retry after material counterevidence` là safety doctrine dùng chung cho cả hai arm sau khi M2 được chấp nhận. Không thiết kế control arm bằng cách cố ý cho phép hành vi đã được xác định là dễ tạo false closure.

```text
COMMON TO BOTH ARMS
  Problem Revision + exact authority
  typed contract / F0 / oracle declaration
  counterevidence safety guard
  model, route, review, source, environment and safety floors

CONTROL
  current bounded repository workflow
  no EGRI packet injection

TREATMENT
  exact Resolution Capsule
  bounded Workspace Evidence Index packet
  <= 3 applicable Case Memory records with contrast/warnings
  explicit decision-changing discriminator protocol
```

Do đó:

- RQ4 được đánh giá như safety/process effect bằng prospective natural evidence, không randomize việc vi phạm safety rule;
- P5 A/B đo causal effect gia tăng của information/protocol package EGRI trên nền safety doctrine chung;
- báo cáo không được gọi kết quả A/B này là causal effect của toàn bộ PRL/EOCL/control plane.

## 0.3. Thứ tự gate không được đảo

```text
W0  Reconcile source candidate and freeze scope
 ↓
W1  Distill Case Memory v1
 ↓
W2  Enforce counterevidence doctrine
 ↓
W3  Accept Resolution Capsule + prove resumption
 ↓
W4  Build bounded HR Finance Workspace Evidence Index
 ↓
W5  Run one prospective natural case
 ↓
W6  Collect 5-10 consecutive natural cases
 ↓
W7  Run fresh P5-A0 A/A instrumentation study
 ↓
W8  Register and run EGRI P5-A feasibility, then P5-B if eligible
 ↓
W9  Promote, simplify, retain as advisory, or remove
```

`W7/W8` tuyệt đối không đi trước `W5/W6`.

---

# 1. Current truth dùng để lập kế hoạch

## 1.1. Git và concurrent work

Snapshot đầu phiên lập kế hoạch chứng minh:

- root đúng là `E:\DEV\Codex-web`;
- branch `main`;
- `HEAD == origin/main == 30b7d1b971b65034d3e4c95568c970fcc0e9380c`;
- worktree đang dirty bởi runtime evidence và source/documentation work đồng thời;
- không có commit, push, activation, restart, P5 mutation hay workload nào được tạo trong phiên lập kế hoạch.

Concurrent source candidate liên quan trực tiếp gồm:

- `resources/coding-tools-mcp/coding_tools_mcp/problem_lineage.py`;
- `resources/coding-tools-mcp/tests/test_problem_lineage.py`;
- `docs/CURRENT_STATE.md`;
- `docs/ROADMAP.md`;
- volatile `.coding-tools/**` evidence.

Candidate đó bổ sung `derived_resolution_capsule` vào handoff projection. Nó có exact Problem Revision/criteria fingerprints, bounded contract, latest event, reopen/outcome receipt state, content-free Problem Frame projection và explicit no-authority flags. Đây là **source candidate chưa được chấp nhận và chưa phải runtime-loaded truth**.

Kế hoạch này không ghi đè candidate, không nhận nó là implementation hoàn tất và không đưa nó vào P5 source contract trước khi W0 đóng.

## 1.2. Read-only reporter observations used for planning

Planning handoff cung cấp output từ các read-only reporters chạy trên immutable/query-only ledger snapshot với trạng thái sau:

| Reporter | Trạng thái mạnh nhất | Bằng chứng / giới hạn |
| --- | --- | --- |
| `report_problem_lineage_canary.py` | `C4_SOURCE_READY_AWAITING_NATURAL_CANARY` | `problem_revisions=0`; 10 current-policy events đều ambiguous/unlinked; exact revision binding `0/10`; `natural_evidence.attested=false` |
| `report_problem_resolution_economics.py` | `DESCRIPTIVE_ONLY` | 0 problem revision, 0 Trusted Resolution; mọi denominator TTPR/first-pass/reopen/frame/receipt đều chưa có |
| `report_p5_baseline.py` | `IMPLEMENTED_GATED` | latest lifecycle `EPOCH_HARD_STOPPED`; control/treatment observations đều 0; historic 480 accepted runs không phải treatment evidence |
| `report_p4_readiness.py` | `COLLECTING` | `validated_signals=[]`; predictive validation chưa có; không chặn A0 instrumentation nhưng chặn predictive policy promotion |

Framing Regret định lượng hiện vẫn `UNAVAILABLE` vì material-counterevidence clock và avoidable-work attribution chưa nằm trên một common attested clock. Kế hoạch không điền `0`, không backfill theo timestamp/keyword và không biến missing thành success.

Các counters/status trong bảng này **không phải auditable current receipt** vì companion plan không có exact Backup-API snapshot identity, capture timestamp, report artifact hash hoặc full command-output receipt để bind độc lập chúng vào HEAD. Chúng chỉ định hướng scope. W0/W5 phải recapture reporters tuần tự và ghi exact snapshot/report fingerprints trước khi dùng bất kỳ counter nào làm gate.

## 1.3. Maturity board M0-M9

| Milestone | Trạng thái hiện tại | Quyết định |
| --- | --- | --- |
| M0 Freeze new machinery | `PARTIAL` | Giữ đúng 8 tool; không thêm state/router/database; W0 phải đóng source candidate và scope |
| M1 Distill 7 Golden HR cases | `PROSE_CALIBRATION_ONLY` | Có calibration nhưng 0 independently confirmed Trusted Resolution; cần structured Case Memory 7/7 |
| M2 Counterevidence enforcement | `ADVISORY_ONLY` | Frame/advisory đã có; `materiality_inferred=false`, `automatic_mutation_gate=false`; cần managed guard |
| M3 Resolution Capsule | `DIRTY_SOURCE_CANDIDATE` | Reconcile semantics, extract bounded composer nếu cần, rồi prove context resumption |
| M4 Workspace Evidence Index | `FOUNDATION_ONLY` | `SemanticRepositoryGraph` đã bounded/derived; chưa có HR family packet, owner/entity/UI/recent-change proof và natural measurement |
| M5 First natural case | `NOT_STARTED` | Bắt đầu bằng problem HR mới; không mặc định GHR-07 còn open |
| M6 5-10 natural cases | `NOT_STARTED` | Chưa có cohort identity auditable hoặc raw-row reporter |
| M7 P5 A/A | `SOURCE_IMPLEMENTED / EMPIRICALLY_NOT_STARTED` | Epoch cũ hard-stop; cần source/runtime exact và fresh manifest |
| M8 EGRI A/B | `NOT_IMPLEMENTED_AS_EGRI` | P5 machinery có nhưng treatment/analyzer hiện tại không phải EGRI |
| M9 Promote/simplify/remove | `NOT_APPLICABLE` | Chỉ quyết định sau representative causal evidence |

---

# 2. Invariants và ranh giới bắt buộc

## 2.1. Authority

Canonical authority không thay đổi:

```text
User Contract
→ Problem Revision / PRL
→ EOCL controller + exact RUN/WAVE/write lease
→ proof/checkpoint
→ runtime projection
→ independent/user outcome receipt
```

Capsule, Index và Case Memory chỉ là derived/advisory. Chúng không được tự:

- grant write authority;
- accept wave/run;
- đổi Problem Revision;
- đổi route/model;
- tuyên bố Trusted Resolution;
- override business semantics hoặc canonical data owner.

## 2.2. Public contract

Smart-v3 tiếp tục đúng tám public tools:

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

EGRI được tích hợp phía sau existing `agent_workflow`/`task_control`/handoff path. Không tạo tool thứ chín, second PRL database, new Problem Governance Engine hoặc extra RUN/WAVE state.

## 2.3. Workspace boundary

Implementation source thuộc `E:\DEV\Codex-web`. Prospective HR evaluation dự kiến chạy trên một HR checkout riêng, ví dụ `E:\DEV\HR STA\HR`, nhưng đây là external target độc lập.

Trước bất kỳ HR mutation nào phải có:

- explicit user authorization cho đúng HR workspace;
- exact `task_context_id`/workspace identity;
- không fallback sang `last_active_workspace`, UI workspace, recent task hoặc global task;
- HR source/runtime/oracle authority riêng;
- evidence ghi vào đúng target ledger, không nhập nhằng với Codex-web ledger.

Kế hoạch này không cấp sẵn authority cho HR write.

## 2.4. Evidence and privacy

- Ledger là causal audit source; projection JSON chỉ hỗ trợ.
- Raw transcript, private reasoning, credentials, authorization headers, personal data và large source dumps không được đưa vào Case Memory/Capsule/durable metrics.
- Model-visible repository packet có thể chứa bounded current source/path/symbol dưới read authority hiện hữu; durable telemetry chỉ giữ fingerprints/counts/status cần cho decision.
- Historical ambiguous fields phải là `UNKNOWN`, không suy đoán.
- Silence là censored/unknown, không phải resolution.

## 2.5. Delivery

Source proof, accepted checkpoint, Git commit, push, runtime activation, connector freshness, A/A open, A/B open, release và production là các gate riêng.

Không wave nào được tự động chuyển sang wave kế tiếp chỉ vì tests pass.

---

# 3. Target artifact architecture

## 3.1. Resolution Case Memory v1

Versioned, offline/derived JSON records; không database/service.

Case Memory source được version-control trong Codex-web. Khi dùng trên một HR workspace riêng, controller chỉ inject tối đa ba bounded retrieved records cùng exact casebook fingerprint; target runtime không được tự tìm qua recent workspace/path fallback.

Minimum record:

```yaml
schema_version: 1
case_id:
case_fingerprint:
problem_family:
contract_signature:
manifestation:
governing_invariants:
minimal_sufficient_boundary:
canonical_owners:
initial_frame:
wrong_hypotheses:
counterevidence:
decision_changing_discriminators:
causal_intervention:
oracles:
outcome:
applicability:
negative_transfer_warnings:
source_runtime_assumptions:
confidence_level: UNKNOWN|LOW|MEDIUM|HIGH
```

Retriever rules:

1. hard reject incompatible contract semantics, owner/data-flow, source/runtime assumptions, unresolved reopen hoặc weak oracle;
2. rank theo invariant → owner/data-flow → causal mechanism → source/runtime assumptions → oracle;
3. trả tối đa ba records;
4. luôn trả reject/uncertainty reasons;
5. historical case không có independent outcome chỉ được dùng làm contrast/warning, không làm “successful solution template”.

## 3.2. Resolution State Capsule v1

Project từ exact PRL + RUN/WAVE/proof + current source/runtime truth. Candidate hiện tại là đầu vào để reconcile, không phải lý do tạo representation thứ hai.

Capsule phải có:

- exact problem/revision/contract/criteria identity;
- current frame identity và revision;
- accepted subclaims, invalidated hypothesis và unresolved gap;
- latest counterevidence/reopen/outcome receipt state;
- next discriminator + expected decision delta;
- source/runtime/freshness labels;
- writer/acceptance authority labels;
- explicit omissions và exact-refresh requirement.

Semantic decision-state không được tự xuất hiện từ narrative. Producer contract phải tách rõ:

- accepted subclaim/criterion IDs chỉ derive từ exact proof/checkpoint/coverage facts;
- invalidated hypothesis IDs phải tham chiếu typed hypotheses của exact Frame revision;
- unresolved gap, next discriminator và expected decision delta là bounded controller-attested decision state, được runtime validate/bind/hash nhưng không nâng thành causal truth hoặc authority;
- provenance/status cho từng field là `DERIVED_EXACT`, `CONTROLLER_ATTESTED`, `UNKNOWN` hoặc `CONFLICTED`;
- `UNKNOWN/CONFLICTED` ở mandatory resumption fields chặn W3 exit, không được fixture/model tự điền;
- ambiguous/unlinked primary binding trả explicit blocked projection;
- historical Problem Revision luôn `policy_eligible=false` và đòi exact current-revision refresh trước mutation.

Outer handoff budget algorithm:

1. outer handoff giữ existing 8 KiB contract;
2. serialize mandatory runtime core trước: identity, provenance, authority, freshness-at-record, decision-state status và omission receipts;
3. nếu caller payload + minimum mandatory core vượt 8 KiB, reject toàn bộ record bằng typed budget error;
4. allocate remaining bytes theo deterministic priority: decision-state values cần cho resumption → latest exact event/proof references → contract embed → optional Frame details;
5. contract section có per-section max 4 KiB nhưng không được giả định đã có sẵn 4 KiB trong outer budget;
6. section không fit bị omit nguyên vẹn kèm identity, byte count, reason và exact-refresh flag; không truncate im lặng.

Stored capsule bytes/SHA remain immutable. `handoff get/resume` phải trả thêm một read-time observation, không rewrite stored capsule, so sánh current PRL/source/runtime với recorded identities:

```text
MATCHED | MISMATCHED | UNKNOWN
```

Mỗi domain có reason/fingerprint/observed-at riêng. Missing current observation là `UNKNOWN`, không phải matched.

## 3.3. Workspace Evidence Index MVP

Tái sử dụng `SemanticRepositoryGraph`, `semantic_localization`, `context_tools` và context compiler. Bổ sung một in-memory, source-fenced projector chỉ khi existing graph không thể tạo packet quyết định được.

Target family duy nhất:

```text
HR Finance:
project revenue / contract / payment / settlement / status / projection
```

Record/edge classes cần đủ dùng:

- file/symbol/import/dependency;
- route/IPC;
- schema/table/entity/config;
- persistence owner/read/write path;
- projection/UI consumer;
- test/oracle;
- recent change;
- source identity/current/stale/uncertain.

Every record must carry:

```yaml
record_kind:
claim_status: CANDIDATE | AMBIGUOUS | UNKNOWN | OBSERVED_CANONICAL
provider:
confidence:
completeness:
currentness: MATCHED | MISMATCHED | UNKNOWN
source_fingerprint:
evidence_refs:
```

`OBSERVED_CANONICAL` chỉ hợp lệ khi structural/source-declared evidence trực tiếp chứng minh owner/relationship. Current path/name/text match vẫn chỉ là `CANDIDATE`. Typed edges chỉ emit từ observed relationship; heuristic similarity không được masquerade thành `WRITES_TO`, `PROJECTS_TO`, `RENDERS` hoặc `TESTED_BY`.

Proposed MVP budgets, freeze trước M5:

- model-visible packet ≤ 32 KiB;
- ≤ 64 records;
- ≤ 96 edges;
- depth tối đa 2;
- no durable raw query/source/author identity;
- stale record không được xếp thành canonical owner.

Integration nằm sau existing `agent_workflow prepare/resume` behavior; không mở public schema chỉ để expose Index.

Index stays default-off. Internal enrollment receipt is bound to exact `{problem_id, problem_revision, family_id, source_fingerprint, protocol_id}`. Before P5, only an explicitly accepted natural-evaluation enrollment may inject the packet. During P5 A/B, only an immutable treatment assignment may inject it; control remains packet-free. Objective/query keywords never activate EGRI.

Current Context Compiler remains `OFF/SHADOW`, `auto_inject=false`, `KEEP_SHADOW/NO_PROMOTION`. EGRI packet injection is a separate exact protocol action with a content-free receipt, not hidden Context Compiler auto-promotion.

## 3.4. Natural cohort reporter

Thêm một immutable read-only projection, không writer/table authority mới:

```text
preregistered cohort manifest
+ immutable PRL snapshot
+ LedgerFacts / exact run-wave-proof joins
+ content-free localization observations
→ screening rows
→ eligible raw case rows
→ missingness-preserving descriptive summary
```

Reporter không tự gọi case là natural bằng keyword/timestamp. Naturality phải có exact host-turn/user intake evidence và preregistered classification rule.

## 3.5. P5 EGRI treatment and efficacy report

Giữ current P5 feasibility/integrity analyzer cho A/A. Sau A/A mới thêm:

- treatment ID mới, ví dụ `egri-resolution-intelligence-v1`;
- exact implementation fingerprint;
- P5-A/P5-B manifest builder;
- assignment-to-Problem-Revision bridge derived từ canonical ledger;
- separate efficacy analyzer/report, không đổi A0 `efficacy_decision=NOT_EVALUATED`;
- no renderer treatment button mặc định; opening dùng explicit current-controller authority trên existing `task_control(action="p5")` path.

---

# 4. Detailed implementation waves

# W0 — Reconcile source candidate and freeze scope

## Objective

Tạo một exact source baseline có ownership rõ trước khi phát triển EGRI.

## Required work

1. Re-read current branch/HEAD/status và exact dirty diff.
2. Tách ba loại thay đổi:
   - accepted P0.6 baseline;
   - concurrent Resolution Capsule candidate;
   - volatile `.coding-tools/**` evidence.
3. Review candidate theo contract:
   - exact Problem Revision binding;
   - bounded output;
   - privacy scan;
   - reopen/outcome receipt semantics;
   - no caller-forged reserved field;
   - no mutation/acceptance authority.
4. Chấp nhận, sửa hoặc reject candidate bằng exact owned wave; không tạo capsule implementation cạnh tranh.
5. Nếu candidate được giữ, extract pure capsule composition/helper sang module riêng khi cần để giữ `problem_lineage.py` dưới 1,600 lines và làm M2/M3 có owner rõ.
6. Update maintained docs chỉ sau source acceptance; dated research source không bị rewrite.

## Likely source surfaces

- `coding_tools_mcp/problem_lineage.py`;
- optional new `coding_tools_mcp/resolution_capsule.py`;
- `coding_tools_mcp/coordination.py` handoff integration;
- `coding_tools_mcp/truth_snapshot.py` current source/runtime projection;
- `tests/test_problem_lineage.py`;
- focused handoff/coordination tests.

## Focused proof

```powershell
Set-Location E:\DEV\Codex-web\resources\coding-tools-mcp
python -m pytest tests/test_problem_lineage.py -q
python -m pytest tests/test_resolution_contract.py tests/test_orchestration_workflow.py -q
python scripts/check_module_size.py
Set-Location E:\DEV\Codex-web
git diff --check
```

Nếu có extraction, package guide bắt buộc chạy full package suite vì import/re-export failure là adjacent risk chính:

```powershell
Set-Location E:\DEV\Codex-web\resources\coding-tools-mcp
python -m pytest tests/
```

Focused-only proof hợp lệ khi W0 không extraction và không thay composition/public import boundary.

## Exit gate

- candidate ownership và exact diff được chấp nhận hoặc reject rõ;
- focused proof pass trên exact fingerprint;
- module-size guard pass;
- source docs không claim runtime-loaded nếu chưa activation;
- không active write lease/job còn treo từ wave;
- không P5 epoch được mở.

---

# W1 — Distill Resolution Case Memory v1

## Objective

Chuyển bảy Golden HR cases thành 7/7 structured records, giữ unknown và historical limitations trung thực.

## Required work

1. Freeze schema v1 và reject unknown keys.
2. Distill từng GHR-01..GHR-07 từ calibration evidence.
3. Ghi `UNKNOWN` cho mọi field không có evidence.
4. Không backfill independent outcome/user confirmation.
5. Tạo deterministic fingerprints cho record và full casebook.
6. Implement pure validator/retriever:
   - no network/database;
   - deterministic order;
   - max 3 accepted records;
   - explicit applicability/rejection reasons;
   - negative-transfer warnings bắt buộc.
7. Tạo privacy/oversize/encoded-secret tests.

## Proposed artifacts

- `docs/research/260901_GOLDEN_HR_RESOLUTION_CASE_MEMORY_V1.json`;
- `resources/coding-tools-mcp/coding_tools_mcp/resolution_case_memory.py`;
- `resources/coding-tools-mcp/scripts/validate_resolution_case_memory.py`;
- `resources/coding-tools-mcp/tests/test_resolution_case_memory.py`.

## Acceptance tests

- 7/7 IDs present và unique;
- stable fingerprint bất kể JSON formatting;
- raw transcript/private reasoning/source dump bị reject;
- outcome thiếu receipt không được nâng thành trusted;
- owner/source/oracle mismatch hard-rejects reuse;
- reopened/unreconciled case không được dùng làm positive template;
- retrieval ≤3 và stable;
- all unknowns remain explicit.

## Exit gate

`CASE_MEMORY_V1_SOURCE_PASS`, nhưng chưa có claim rằng retrieval cải thiện outcome.

---

# W2 — Enforce counterevidence doctrine

## Objective

Trên managed problem-bound mutation path, material hoặc unresolved counterevidence phải chặn same-frame retry cho tới khi frame/explanation/discriminator được cập nhật.

## Contract decision

Không để runtime tự “đoán” materiality từ prose. Typed review phải có:

```yaml
review_status: MATERIAL | NON_MATERIAL | UNKNOWN
invalidated_dimensions:
  - BOUNDARY
  - GOVERNING_INVARIANT
  - CANONICAL_OWNER
  - LEADING_HYPOTHESIS
  - ORACLE_SUFFICIENCY
  - SOURCE_RUNTIME_TRUTH
basis_evidence_refs: []
contradiction_explanation_fingerprint:
next_discriminator_fingerprint:
```

Rules:

- `MATERIAL` hoặc `UNKNOWN` fail closed;
- `NON_MATERIAL` cần explicit bounded rationale/fingerprint;
- guard không cấp write authority; nó chỉ từ chối mutation eligibility;
- new frame revision hoặc explicit contradiction explanation + new discriminator mới clear pending guard;
- exact same Problem Revision được giữ khi contract không đổi;
- changed contract phải đi qua `REVISE`.

## Required work

1. Version typed Frame/review contract mà vẫn đọc được historical v1 shadows.
2. Persist content-free materiality review identity, status và frame relationship.
3. Add one shared problem-bound mutation-admission guard, không đặt riêng trong một workflow implementation.
4. Invoke it before write lease/spawn/mutation trên every write-capable smart-v3 path, gồm ít nhất:
   - `agent_workflow` write/apply path;
   - mutating hoặc unknown-risk `exec_command` bound to the RUN/WAVE;
   - write-capable `document_workflow` create/convert/rebuild path;
   - follow-up `command_control` input nếu nó có thể kích hoạt mutation/retry trong an admitted active process.
5. Nếu một write-capable path chưa thể gọi guard với exact problem/frame state, server phải reject path đó cho EGRI-bound run; runbook prohibition không đủ để claim enforcement.
6. Non-problem work và read-only actions không bị block.
7. Same event/key remains idempotent; conflicting reuse fails closed.
8. Reporter emits:
   - material/unknown events;
   - guarded retry attempts;
   - frame update/explanation coverage;
   - unresolved missingness.

## Likely source surfaces

- `coding_tools_mcp/resolution_contract.py`;
- `coding_tools_mcp/workflow_tools.py`;
- a small shared `coding_tools_mcp/problem_mutation_admission.py` or equivalent domain-owned guard;
- `coding_tools_mcp/exec_tools.py`;
- `coding_tools_mcp/document_tools.py`;
- `coding_tools_mcp/session_control.py`/command-control owner when follow-up input can mutate;
- `coding_tools_mcp/problem_lineage_control.py`;
- `coding_tools_mcp/problem_resolution_economics.py`;
- related tool schema only if an existing nested field must be versioned; public tool count remains 8.

## Focused tests

- material counterevidence + same frame + write → deterministic rejection;
- unknown materiality + write → rejection;
- non-material + explicit rationale → no automatic frame change, write still requires ordinary authority;
- higher frame revision + new discriminator → guard clears;
- changed contract without `REVISE` → reject;
- no counterevidence → no new ceremony;
- read-only and non-problem work unaffected;
- mutating/unknown-risk `exec_command` cannot bypass guard;
- document create/convert/rebuild cannot bypass guard;
- active-process follow-up cannot become a same-frame retry bypass;
- guard cannot be bypassed by caller-forged payload;
- ledger event remains content-free/privacy-safe.

## Exit gate

- 100% write-capable smart-v3 paths available to an EGRI-bound RUN either invoke the shared guard or are server-rejected;
- no unsupported direct path is treated as protected by documentation alone;
- no same-frame mutation after material/unknown counterevidence in focused proof;
- RQ4 metric has a truthful numerator/denominator or remains explicitly unavailable.

---

# W3 — Resolution Capsule MVP and resumption proof

## Objective

Chấp nhận một bounded capsule projection và chứng minh context B tiếp tục đúng mà không replay chat.

## Required work

1. Reuse W0 capsule semantics; không tạo representation cạnh tranh.
2. Compose capsule bằng pure deterministic function.
3. Join only exact revision/run/wave/proof identities.
4. Derive accepted criterion/subclaim IDs from canonical coverage; validate typed invalidated hypothesis IDs against the exact Frame revision.
5. Accept bounded controller-attested unresolved gap/next discriminator/decision delta only with exact provenance/hash; missing/conflicted mandatory state blocks resumption.
6. Emit explicit blocked projections for ambiguous/unlinked primary binding and policy-ineligible historical revisions.
7. Emit stored-at and read-time currentness separately; never rewrite immutable stored capsule to look current.
8. Preserve deterministic section priority/omission receipts and exact-refresh behavior under the shared 8 KiB outer budget.
9. Prevent caller override of reserved `problem_lineage`/capsule fields.
10. Add a deterministic contract test and one live/context-resumption evaluation.

## Context-resumption protocol

```text
Context A:
  exact Problem Revision + F0
  one hypothesis invalidated
  one unresolved gap
  next discriminator selected
  emit capsule

Context B receives only:
  capsule
  bounded repository packet
  no raw chat/transcript/private reasoning

Context B must return machine-checkable:
  exact problem_id/revision
  current gap
  invalidated hypothesis
  next discriminator
  authority/freshness limitations
```

Source tests chỉ chứng minh contract. `resumption correctness` chỉ đạt sau một separate evaluated receipt đối chiếu với sealed expected facts.

## Metrics

- capsule build latency;
- capsule bytes;
- exact-refresh count;
- reconstruction time;
- missing/incorrect state fields;
- wrong-frame outcome after resumption;
- raw-history bytes avoided, nếu cùng measurement boundary.

## Exit gate

- bounded/source-fenced/privacy-safe;
- deterministic fingerprint;
- mandatory semantic state has authoritative provenance or the result is explicitly blocked;
- ambiguous/unlinked/historical revision cannot be policy-eligible;
- caller payload plus mandatory core has a tested reject path; optional omission order is deterministic;
- read-time `MATCHED|MISMATCHED|UNKNOWN` is observed beside immutable stored bytes;
- one accepted resumption receipt;
- no mutation/acceptance authority;
- overhead được đo, không giả định là rẻ.

---

# W4 — Bounded Workspace Evidence Index for HR Finance

## Objective

Giảm repeated localization trên đúng một HR Finance family mà không tạo stale/wrong-owner guidance.

## Required work

1. Freeze family profile và query questions trước natural case:
   - canonical entity/owner ở đâu?;
   - write path?;
   - read/projection path?;
   - UI consumer?;
   - matching test/oracle?;
   - recent relevant change?
2. Reuse `SemanticRepositoryGraph` and existing semantic-first/text-fallback execution.
3. Add only missing record/edge projection needed to answer those questions.
4. Source-fence every record; stale/uncertain remains visible.
5. Key cache/Index identity by canonical workspace root + exact source fingerprint + bounded request identity, not workspace root/args alone.
6. Replace/reset graph and cache on canonical workspace-root change; force refresh on source-fingerprint mismatch.
7. Partial/prefix-suffix large-file identity projects currentness `UNKNOWN`, never `CURRENT`.
8. Bounded packet and ambiguity section are mandatory.
9. Sanitize recent-change projection: no Git author name/email or commit message prose in durable or model-visible Index packet; retain only required path/change/fingerprint/time facts.
10. Enforce default-off exact enrollment and record a content-free injection/no-injection receipt; control arm remains packet-free.
11. Add content-free per-run localization observation:
   - uncached query fingerprints/count;
   - duplicate query count;
   - semantic handled/fallback count;
   - selected candidate count;
   - model-visible bytes before first write;
   - index build/query latency;
   - stale/uncertain/rejected-owner counts.
7. Wrong-target navigation remains `UNKNOWN` unless an explicit observed/controller/human adjudication event exists.

## Likely source surfaces

- `coding_tools_mcp/semantic_graph.py`;
- optional `coding_tools_mcp/workspace_evidence_index.py` as an in-memory source-fenced projector;
- `coding_tools_mcp/context_tools.py`;
- `coding_tools_mcp/context_compiler.py`;
- `coding_tools_mcp/workflow_tools.py` integration behind prepare/resume;
- `tests/test_semantic_graph.py`;
- `tests/test_context_compiler.py`;
- focused composite-context tests.

## Acceptance tests

- current source change marks prior records stale/uncertain;
- same root + changed HEAD/worktree source fingerprint cannot hit a prior current cache entry;
- workspace A → workspace B switch replaces graph/cache and cannot leak records;
- partial large-file identity remains `UNKNOWN`;
- owner/data-flow ambiguity is returned, not guessed;
- current path/name match cannot become canonical without structural/source-declared evidence;
- typed edges require observed evidence refs;
- LSP unavailable still yields bounded fallback;
- budgets truncate explicitly;
- no source/query/author identity leaks into durable metrics;
- no author name/email leaks through recent-change model packet;
- default-off/no-enrollment path injects nothing;
- exact treatment enrollment injects once and records its receipt; control assignment stays packet-free;
- Context Compiler remains shadow/no-auto-inject;
- cached delivery does not masquerade as zero context bytes;
- duplicate queries count only comparable uncached operations;
- no tool/schema count expansion.

## Exit gate

Source exit:

- packet answers the six frozen HR Finance questions on a controlled fixture;
- stale/wrong-owner fails closed;
- module-size/focused tests pass.

Natural exit, required before M4 is considered empirically useful:

- at least one authorized HR natural case uses the exact packet;
- localization measurement is complete;
- no observed stale/wrong-owner navigation;
- no claim of causal reduction from one case.

---

# W5 — First prospective natural Trusted Resolution case

## Objective

Run one real HR problem through full lineage. Success includes an honest reopen; it does not require forcing a positive outcome.

## Eligibility

- prefer a new user-origin HR Finance problem;
- if none exists, recapture GHR-07 current state and contract before deciding it is still open;
- target workspace and mutation authority explicitly authorized;
- exact current source/runtime/connector identity;
- natural task, not created to fill evidence;
- problem class and oracle are eligible for the intended protocol.

## Mandatory protocol

```text
OPEN exact Problem Revision before first material write
→ capture typed contract
→ F0 A* / G / H + closure falsifier
→ declare matching oracle
→ build current Capsule
→ Workspace Evidence lookup
→ retrieve <= 3 applicable prior cases with warnings
→ choose decision-changing discriminator
→ acquire exact RUN/WAVE/write lease
→ minimal causal patch
→ focused proof
→ subsystem/live projection proof at claim abstraction
→ closure falsifier
→ provisional resolution only
→ independent/user outcome receipt OR same-revision reopen
→ distill prospective case
```

## Hard stops

- Problem Revision not open before first write;
- wrong/stale workspace authority;
- runtime/source currentness unknown for a live claim;
- no matching oracle;
- material/unknown counterevidence with pending same-frame retry;
- safety/security/data/business invariant defect;
- external target owner revokes authority.

## Exit gate

One raw case row has complete contract-to-outcome lineage. Final state may be:

- `TRUSTED_CONFIRMED` with independent receipt;
- `REOPENED_SAME_REVISION`;
- `REVISED_CONTRACT`;
- `RIGHT_CENSORED_UNKNOWN`;
- `BLOCKED/ABANDONED` as non-success.

Only the first state counts as Trusted Resolution.

---

# W6 — Consecutive natural cohort of 5-10 cases

## Objective

Collect a prospective descriptive distribution and close measurement readiness before A/A.

## Preregistration timing

Freeze cohort manifest before the first eligible case in the window. Không chọn case IDs sau khi biết outcome.

## Cohort manifest minimum fields

```yaml
schema_version: 1
cohort_id:
created_at:
controller_acceptance_receipt:
target_workspace_identity:
target_problem_family: hr-finance-project-revenue-settlement-status-projection-v1
natural_task_class_policy: all_explicit_target_family_problem_revisions
p5_eligible_task_classes: [feature, bugfix]
start_event_seq_or_attested_boundary:
max_eligible_cases: 10
decision_checkpoints: [5, 10]
inclusion_rules:
exclusion_reason_vocabulary:
metric_contract_sha256:
oracle_contract_sha256:
safety_floor_sha256:
source_runtime_grouping_policy:
missingness_policy: unknown_not_zero
automatic_promotion: false
```

## Consecutive selection rule

Order by canonical Problem Revision OPEN event sequence within the preregistered window, not by keyword or timestamp proximity.

Every screened intake is retained in a screening table. Natural methodology cohort membership requires:

1. exact user/ChatWeb host-turn-backed Problem Revision;
2. target workspace identity;
3. explicit target family classification bound to the Problem Revision contract/manifest;
4. open event before first material write;
5. no experiment-created/synthetic/calibration-only task.

Task-class/F0/oracle/authority/high-risk failures do not disappear. They remain natural cohort rows and count as mechanics/missingness failures when the user-origin target-family problem otherwise satisfies the rule. Outcome cannot be an exclusion reason.

Reporter đồng thời projects một **nested P5-eligible subset** requiring `feature|bugfix`, prewrite F0/oracle, bounded scope, no high-risk exclusion, common execution contract và exact authority. `diagnose`, `test_failure`, high-risk hoặc otherwise ineligible natural cases remain in the methodology cohort but do not enter P5 enrollment. Insufficient nested P5 volume is an evidence result; không thay bằng case khác sau khi biết outcome.

## Decision at case 5

Report raw five rows, missingness and mechanics. Continue to case 10 only if:

- no critical safety defect;
- cohort rule was applied without outcome-based exclusion;
- source/runtime groups are still interpretable;
- required mechanics failures have an explicit repair plan;
- continued collection changes a named retain/simplify/A0 decision.

If instrumentation changes, freeze a new cohort version. Do not rewrite prior five rows.

## Decision at case 10

Choose exactly one:

- `MEASUREMENT_PACKET_READY_FOR_AA`;
- `EXTEND_WITH_NEW_PREREGISTERED_COHORT`;
- `SIMPLIFY_CAPSULE_OR_INDEX`;
- `REMOVE_CASE_RETRIEVAL`;
- `BLOCKED_EXTERNAL_NATURAL_VOLUME`;
- `STOP_SAFETY_OR_NEGATIVE_TRANSFER`.

No p-value hoặc causal efficacy claim ở W6.

---

# 5. Metric dictionary

## 5.1. Units and denominator policy

Primary descriptive unit là exact `(problem_id, problem_revision)`. Thread state chỉ là compatibility projection.

Screening unit là exact user-origin host-turn intake. Một target-family intake thiếu Problem Revision/prewrite ordering vẫn ở screening denominator với failure reason; nó không thể bị biến thành revision row bằng inference. `Problem-Revision-before-first-write coverage` dùng toàn bộ screened target-family intakes làm denominator và phải đạt gate trước khi A/A.

- natural-methodology denominator gồm mọi user-origin target-family revision trong frozen consecutive cohort;
- P5-readiness denominator là nested arm-neutral eligible subset và luôn được báo riêng;
- blocked, failed, aborted, reopened và censored cases không bị drop;
- source/runtime strata được hiển thị, không pool im lặng;
- historical calibration rows không đi vào denominator;
- missing clock/proof/outcome là missing reason, không là `0`;
- n ≤ 10 luôn xuất raw ordered rows.

## 5.2. Natural cohort metrics

| Metric | Definition | Numerator / denominator | Missingness / caveat |
| --- | --- | --- | --- |
| `TTOC_wall_ms` | attested revision start → authoritative confirmation | observed exact duration per natural-methodology revision | confirmation time không phải exact real-world resolution; unconfirmed is right-censored |
| `resolution_interval` | latest valid technical full pass → authoritative confirmation | exact interval per confirmed revision | interval-censored truth; không tạo point estimate giả |
| `restricted_TTPR_active_ms` | union active `preflight/localization/routing/execution/replan/proof/acceptance` spans của exact primary RUNs | one value per revision khi same-clock spans đủ | cross-clock domains không cộng |
| `first_pass_trusted` | provisional + independent confirmation, exactly one primary run, no same-revision reopen | trusted first-pass revisions / all natural-methodology revisions | silent/no receipt = not observed, không phải success |
| `reopen_rate` | any same-revision `REOPEN` | reopened revisions / all natural-methodology revisions | changed contract `REVISE` báo riêng |
| `false_closure_rate` | provisional resolution followed by same-revision reopen | false-closure revisions / all natural-methodology revisions | technical pass alone không phải closure |
| `user_correction_turns` | distinct host-attested feedback turns with correction/still-failing intents after intake | raw count per revision; distribution | dedupe by exact turn/trace, không text inference |
| `localization_active_ms` | union localization spans before first write | one value per revision | same clock only |
| `duplicate_localization_queries` | repeated uncached query fingerprint before first write | duplicate count / comparable uncached queries | cached delivery reported separately |
| `prewrite_model_visible_bytes` | bytes delivered to decision context before first material write | raw bytes per revision | includes cached deliveries; no assumption bytes=thinking quality |
| `wrong_target_navigation` | explicit controller/human observed target/owner correction | count per revision | absent adjudication = `UNKNOWN`, not zero |
| `frame_revision_count` | distinct frame revisions bound to exact Problem Revision | raw count per revision | invalid/mismatched shadows excluded with reason |
| `governance_friction` | typed replan/authority/lease/permission events caused by control workflow | raw reason counts per revision | time only if attested spans exist |
| `capsule_overhead_ms/bytes` | build + delivery overhead | raw per use | compare with localization saved only on comparable boundary |
| `index_overhead_ms` | build/query/update overhead | raw per use | stale refresh cost retained |
| `case_retrieval_accept/reject` | applicable/rejected case records and reasons | raw per revision | high rejection may be healthy gate behavior |
| `negative_transfer` | retrieved case influenced action and later explicit material counterevidence invalidated that reuse | affected revisions / revisions using retrieval | requires explicit adjudication; otherwise unknown |
| `independent_outcome_coverage` | host-attested receipt-bound confirmations | receipt-bound confirmations / all natural-methodology revisions | legacy confirmation not backfilled |

## 5.3. Small-sample reporting

At n=5-10:

- raw case table;
- exact counts/proportions;
- median and p90 only when values exist;
- ordered values for audit;
- exact/Wilson interval where appropriate, with wide interval preserved;
- qualitative mechanism trace;
- no cosmetic p-value;
- no causal wording.

## 5.4. Metrics deliberately deferred

Quantitative Framing Regret remains unavailable until material-counterevidence availability và avoidable-work attribution share a valid attested clock. True sibling recurrence remains unavailable until explicit semantic sibling linkage exists.

Không thêm instrumentation cho hai metrics này chỉ để làm dashboard xanh. Chỉ implement nếu kết quả sẽ thay đổi W2/W9 decision.

---

# 6. W7 — P5-A0 A/A instrumentation validation

## 6.1. Preconditions

Tất cả điều kiện sau phải đồng thời đúng:

- W0-W6 accepted;
- ≥5 natural HR cases đạt DoD mechanics;
- measurement packet frozen;
- exact source accepted, worktree source-scope clean và upstream relation thỏa manifest hiện hành;
- current runtime loads exact source/tool/analyzer identity;
- connector/target authority đủ cho actual current path;
- no active workspace writer/lease conflict;
- external SecretStore seed available through `secret://experiment/p5/a`;
- previous hard-stopped epoch remains terminal and is never reopened;
- operator explicitly prepares and opens a new manifest.

P4 predictive readiness không phải A0 integrity prerequisite. Nó vẫn là prerequisite cho later predictive targeting/policy use.

## 6.2. A/A contract

- phase `P5-A0`;
- study `shadow_aa`;
- labels `control_a` / `control_b`;
- both receive actual `eocl-current-control-v1`;
- assignment before protocol and first write;
- block 2/2 within `feature` and `bugfix` strata;
- all assigned rows retained ITT;
- no routing/treatment/promotion change;
- existing feasibility analyzer keeps `efficacy_decision=NOT_EVALUATED`.

## 6.3. Horizon decision rule

Current production A0 horizon is four hours. Không mở epoch rồi kéo dài ad hoc.

Sau W6, estimate natural eligible arrival distribution without outcome labels:

- nếu frozen four-hour window có khả năng thực tế tạo ít nhất một completed 2/2 block trong mỗi preregistered stratum, giữ current contract và có thể chạy các epoch bốn giờ riêng biệt;
- nếu không, không lặp hàng loạt empty epochs. Version A0 manifest/horizon trước khi open, dựa trên blinded arrival-rate evidence và một explicit upper bound; giữ nguyên drift/hard-stop rules;
- partial blocks của epoch khác nhau không được ghép giả thành một completed block.

## 6.4. A/A health gate

`AA_HEALTHY` chỉ khi:

- ≥1 completed valid 2/2 block trong mỗi included stratum;
- 100% assignments có prior arm-neutral enrollment;
- 100% assignments có protocol start đúng arm-neutral control;
- 100% write-capable assignments có exact RUN/WAVE/lease pre-write binding trước first write;
- 100% assigned rows có terminal ITT outcome row, kể cả failed/blocked/aborted;
- required immediate quality/follow-up states complete hoặc epoch remains paused, không silent close;
- zero assignment conflict, late assignment, crossover, orphan row, invalid block, source/runtime/analyzer/environment drift hoặc critical safety event;
- seed material không lộ và không reseed within epoch;
- raw funnel/missingness by arm and stratum được review;
- outcome differences chỉ được mô tả, không efficacy claim.

## 6.5. A/A pause and hard-stop

Pause:

- temporary oracle/external outcome unavailability;
- delayed follow-up pending;
- natural volume temporarily insufficient;
- review required for noncritical instrumentation anomaly.

Hard-stop:

- source/runtime/analyzer/environment fingerprint drift;
- conflicting writer/authority loss;
- assignment conflict/late assignment;
- control/treatment crossover hoặc non-control behavior in A/A;
- orphan table/event row;
- invalid completed block schedule;
- pre-write binding/first-write inconsistency;
- critical security, data loss, privacy hoặc business-invariant defect.

Insufficient volume là evidence result, không phải lý do tạo synthetic task.

---

# 7. W8 — EGRI P5-A feasibility and P5-B confirmatory study

## 7.1. Source work permitted only after A/A health

Implement:

1. new treatment ID `egri-resolution-intelligence-v1`;
2. exact fingerprint of capsule/index/case-memory/protocol versions;
3. P5-A/P5-B manifest builder;
4. protocol registry mapping that preserves A0 control semantics;
5. immutable assignment ↔ exact Problem Revision/RUN/WAVE bridge;
6. read-only efficacy analyzer separated from current integrity analyzer;
7. explicit controller-only open path; no automatic activation, no default renderer treatment control;
8. focused compatibility reader for terminal historical v2 manifests if a manifest version bump is required.

Do not rename `lean-causal-fix-gate-v1` to EGRI. A materially different treatment needs a new identity and manifest.

## 7.2. A/B preregistration fields

Freeze before first assignment:

- scientific question and estimand;
- phase/study type;
- treatment/control IDs and fingerprints;
- exact source/runtime/environment/analyzer identities;
- eligible workspace/problem family/task classes;
- inclusion/exclusion reason vocabulary;
- randomization unit, strata, block algorithm and seed commitment;
- assignment timing relative to Problem Revision, protocol and first write;
- common execution contract;
- model/route/review/cache/oracle policy;
- outcome horizon and follow-up matrix;
- primary/secondary metrics;
- missing/intercurrent-event handling;
- safety floors and noninferiority margins approved by domain owner;
- pause/hard-stop rules;
- analysis method;
- sample-size/precision rule;
- promotion/simplification rule;
- automatic activation/promotion false.

## 7.3. Primary causal estimand

P5 outcome phải bắt đầu sau randomization. Vì vậy causal primary không dùng toàn bộ pre-assignment history.

Recommended estimand:

```text
assignment-to-independent Trusted Resolution time,
restricted to frozen horizon H,
under intention-to-treat,
stratified by feature/bugfix and frozen source/oracle groups
```

Unresolved assignments remain right-censored/unsuccessful under the preregistered method; they are never dropped.

Natural-cohort `revision-open → confirmation` TTPR remains key descriptive context but không masquerade thành post-randomization causal endpoint.

## 7.4. Secondary outcomes

- first-pass trusted;
- same-revision reopen;
- false closure;
- user correction turns;
- localization active time;
- duplicate localization queries;
- prewrite model-visible bytes;
- frame revisions;
- governance friction;
- capsule/index overhead;
- negative transfer;
- immediate and delayed quality/safety outcomes.

## 7.5. P5-A feasibility gate

P5-A is a small randomized canary. It proves feasibility/safety and produces variance/arrival/missingness evidence; it does not need to force a definitive efficacy decision.

Advance to P5-B only when:

- funnel/integrity remains healthy;
- adherence and follow-up coverage are sufficient under frozen rule;
- zero critical safety/business regression;
- no material negative-transfer signal;
- treatment packet overhead is not already greater than any plausible localization saving;
- raw arm results do not show a clear harm signal;
- P5-B sample size/precision can be calculated from blinded or preregistered evidence without outcome peeking.

## 7.6. P5-B analysis

Only after P5-A closes:

- freeze representative target population;
- compute sample size/precision from observed control scale/variance and arrival rate;
- report stratified ITT results;
- use RMST/quantile bootstrap or randomization method compatible with the frozen censored-time design;
- use exact/Wilson intervals for first-pass/reopen proportions;
- keep per-protocol analysis secondary;
- report sensitivity to source/model/cache/review strata;
- do not change metric or exclusion rule after seeing treatment result.

The methodology's ~30% median TTPR and ~25-30% repair/reopen reduction are engineering targets, not universal laws. Exact materiality/noninferiority margins must be frozen after W6/P5-A and before P5-B, with domain-owner approval.

---

# 8. W9 — Promotion, simplification or removal

## Promote EGRI only when

- representative P5-B evidence shows material TTPR improvement under frozen estimand;
- first-pass trusted improves and/or reopen/corrections materially fall;
- false closure does not increase;
- hard security/data/business floors are noninferior;
- governance friction does not materially increase;
- capsule/index/case overhead remains below measured benefit;
- no material negative transfer;
- exact source/runtime/protocol version is identified.

Promotion here means methodology/capability promotion only. Routing default, product release, deployment và production adoption require separate decisions.

## Simplify or remove when

- capsule overhead ≥ comparable reconstruction/localization saved;
- Index maintenance/refresh approaches direct-search cost;
- stale/wrong-owner hints recur;
- Case Memory creates negative transfer or mostly returns unusable records;
- ceremony rises but TTPR/trusted outcome does not improve;
- metric does not change a retain/remove decision;
- treatment looks more sophisticated but independent outcome does not improve.

Possible partial decisions:

- retain Capsule, remove Case retrieval;
- retain deterministic HR query profile, remove graph extensions;
- retain counterevidence safety guard as common doctrine, remove EGRI treatment;
- keep all artifacts advisory-only;
- delete experimental adapter while preserving canonical ledger evidence.

---

# 9. Test and validation strategy

## 9.1. Source tests by wave

| Wave | Minimum focused proof |
| --- | --- |
| W0/W3 Capsule | `test_problem_lineage.py`, `test_resolution_contract.py`, focused handoff/orchestration consumer tests, module-size guard |
| W1 Case Memory | new schema/validator/retrieval/privacy tests |
| W2 Counterevidence | frame contract + workflow guard + bypass/idempotency + economics reporter tests |
| W4 Index | `test_semantic_graph.py`, `test_context_compiler.py`, focused composite context/localization tests |
| W5/W6 Cohort | `test_problem_lineage_canary.py`, `test_problem_resolution_economics.py`, new natural-cohort reporter fixtures |
| W7 A/A | `test_p5_experiment.py`, A0 Electron/control-panel source tests only if operator UI changes, baseline reporter |
| W8 A/B | P5 manifest/protocol/store/ITT bridge, new EGRI efficacy analyzer, compatibility and hard-stop tests |

Unit fixtures may test code paths. Chúng không được nhập vào natural/P5 empirical denominator.

## 9.2. Progressive validation ladder

```text
schema/static/diff
→ focused behavior
→ affected subsystem consumers
→ exact source acceptance
→ controlled runtime activation
→ current connector/workspace authority
→ natural case evidence
→ A/A integrity
→ A/B causal evidence
→ delivery/release/production gates
```

Không chạy full suite/release build mặc định nếu focused proof đủ; nêu lý do trước khi mở rộng validation.

## 9.3. Reporter discipline

- immutable Backup-API/query-only snapshot;
- SQLite-heavy reports chạy tuần tự;
- record HEAD, workspace, capture time, schema và snapshot fingerprint;
- no direct ledger edit;
- no synthetic enrollment/assignment/outcome;
- raw rows and missing reasons retained;
- projection disagreement resolved in favor of canonical ledger with explanation.

---

# 10. Delivery and runtime gates

## 10.1. Before any future commit or push

Only when separately authorized:

```powershell
npm run stage:coding-tools-delivery
npm run check:coding-tools-delivery
npm run check:coding-tools-history
git diff --cached --check
```

Requirements:

- complete `.coding-tools/**` evidence retained;
- only `ledger.sqlite3-shm` and `ledger.sqlite3-wal` ignored/untracked;
- canonical ledger index snapshot and delivery receipt agree;
- no credentials/secrets;
- unrelated WIP not mixed;
- exact source packet and proof fingerprint reviewed.

## 10.2. Runtime activation

After accepted source and only with explicit operation authority:

- use supported Recovery Host/full-clean activation path for code revision changes;
- preserve durable `ledger.sqlite3`;
- require one activation epoch with matching running/disk/source revisions;
- distinguish Electron UI currentness, Coding MCP currentness and aggregate readiness;
- establish connector/workspace receipt under current contract;
- do not ACK from persisted hash or generic tool call;
- recapture immutable lifecycle census.

## 10.3. P5 opening

Commit/push/runtime currentness do not automatically authorize P5. Opening requires a new explicit action against a fresh exact manifest and seed commitment.

## 10.4. Explicit non-authorizations in this plan

Tài liệu này không thực hiện hoặc cho phép ngầm:

- commit/push/tag/release/deploy;
- service/runtime restart;
- connector ACK;
- HR workspace mutation;
- experiment open/reopen/enroll/assign/outcome;
- synthetic workload;
- production promotion.

---

# 11. Risk register

| Risk | Trigger | Mitigation / decision |
| --- | --- | --- |
| Concurrent dirty source | capsule/docs change outside owned wave | W0 exact diff ownership; no overwrite; rebase/restore prohibited without authority |
| Historical false precision | missing outcome/clock fields | `UNKNOWN`, no backfill, calibration stays noncausal |
| Selection bias | choosing only successful/nice cases | preregistered consecutive screening rule; retain exclusions and failures |
| Synthetic evidence | tasks created to fill funnel | reject from natural/P5 denominator; keep fixtures test-only |
| Cross-workspace mutation | ambiguous HR target/context | exact task context and explicit HR authorization; fail closed |
| Stale Index | source fingerprint changes | source-fence/invalidate; stale never canonical |
| Negative transfer | old case drives wrong action | applicability hard gate, contrast, falsifier, explicit metric and kill rule |
| Overcompression | capsule loses invariant/gap | mandatory protected invariants/unresolved gap/omission flags; resumption test |
| Metric gaming | faster closure with lower quality | trusted outcome and safety lexicographically before speed |
| Low natural volume | no completed 4-hour A0 blocks | treat as evidence; version horizon before open, never extend live epoch |
| Treatment contamination | A0 receives non-control or arm crossover | immediate hard-stop; preserve ITT evidence |
| Model/runtime/cache confounding | multiple components change with arm | hold constant or preregister strata; exact manifest fingerprints |
| Privacy/secret leakage | case/capsule/index contains sensitive data | bounded validator/privacy scan; stop delivery and remediate, never silently omit evidence |
| Module growth | generic module >1,600 lines | extract domain-owned pure module before accepting wave |

---

# 12. Definition of Done mapping

| Methodology DoD | Required evidence | Closing wave |
| --- | --- | --- |
| ≥5 natural HR cases with Problem Revision before first write | cohort screening + exact PRL/RUN/WAVE/write-order rows | W6 |
| 100% explicit F0 | typed frame identity and complete `A*/G/H` before write | W5-W6 |
| no unexplained same-frame retry after material counterevidence | guard events + zero bypass on managed path | W2/W6 |
| 100% full-problem claim has matching oracle | Resolution Envelope/oracle coverage rows | W5-W6 |
| Capsule works in at least one resumption | accepted machine-checkable resumption receipt | W3 |
| Index reduces repeated localization on target family | comparable natural metrics; no stale/wrong-owner increase | W4-W6 |
| case distillation has applicability + negative transfer | 7/7 historical + prospective record validator | W1/W5 |
| ≥1 independently confirmed Trusted Resolution | receipt-bound PRL confirmation | W5-W6 |
| measurement packet can run P5 A/A without source/instrumentation hard-stop | frozen cohort/report/manifest checks | W6/W7 |
| no unnecessary public tool/state/authority object | eight-tool contract tests + architecture review | every wave |

EGRI source code merge alone không đóng DoD.

---

# 13. Research question mapping

| RQ | Design | Primary evidence | Decision |
| --- | --- | --- | --- |
| RQ1 Capsule | context A/B resumption + natural cases | reconstruction/localization time, correctness, wrong-frame, overhead | retain/simplify/remove Capsule |
| RQ2 Index | HR Finance bounded index usage | localization time, duplicate queries, wrong-target adjudication, stale-owner events | retain profile/projector or return to direct search |
| RQ3 Case Memory | applicability-gated retrieval ≤3 | repeated mechanism mistakes, negative transfer, reject reasons | retain retrieval, warnings-only, or remove |
| RQ4 Counterevidence | common safety doctrine | guarded retries, frame-update coverage, avoidable reopen/repair trace | retain/tighten guard; not randomized unsafe control |
| RQ5 Combined effect | P5-A then P5-B | post-assignment restricted TTPR + trusted outcomes + safety | promote/simplify/remove EGRI treatment |

---

# 14. Operator decision board

## Immediate next action after plan approval

```text
ACTION 1
Review and accept/reject the current dirty Resolution Capsule candidate.

ACTION 2
Open one owned W0 source wave on the exact current HEAD/diff.

ACTION 3
Run only W0 focused proof and checkpoint source status.

ACTION 4
Proceed to W1; do not open runtime/P5 or touch HR workspace.
```

## Decision points requiring explicit user/operator authority

- acceptance of concurrent capsule source;
- commit/push of any implementation packet;
- controlled runtime activation/restart;
- access/mutation of the HR target workspace;
- opening a natural cohort window;
- storing P5 seed and opening A0;
- registering/opening EGRI A/B;
- release/deploy/production promotion.

## Status checkpoint template for every wave

```text
Completed/changed:
Exact Git/source/runtime state:
Strongest proof:
Failure/blocker classification:
Remaining work:
Exact next action:
Commit/push/restart/experiment/release actions performed: yes/no + receipt
```

---

# 15. Final planning judgment

Kế hoạch khả thi nhất không phải xây một “AI memory platform”. Nó là một chuỗi artifact nhỏ, falsifiable và có kill gate:

```text
structured cases
→ enforced counterevidence discipline
→ exact bounded capsule
→ one-family evidence index
→ one natural case
→ 5-10 consecutive cases
→ A/A instrumentation
→ versioned EGRI A/B
→ promote / simplify / remove
```

Nếu W5/W6 cho thấy Capsule/Index/Case Memory không giảm reconstruction/localization hoặc tạo negative transfer, dừng và thu nhỏ trước P5. Nếu A/A không healthy, sửa instrumentation hoặc dừng; không chạy treatment. Nếu P5-B không cải thiện Trusted Resolution dưới safety floors, không mở rộng machinery.

Đây là chương trình triển khai “evidence first”: mỗi wave chỉ được phép mạnh hơn khi wave trước đã tạo đúng loại bằng chứng mà claim kế tiếp cần.
