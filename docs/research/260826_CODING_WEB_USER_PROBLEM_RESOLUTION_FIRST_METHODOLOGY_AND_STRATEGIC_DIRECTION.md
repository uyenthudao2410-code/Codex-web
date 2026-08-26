# CODING WEB — CLOSED-LOOP TRUSTED PROBLEM RESOLUTION METHODOLOGY AND STRATEGIC DIRECTION

**Ngày tổng hợp:** 2026-08-26  
**Bản sửa đổi:** **REVISION 4 — hợp nhất toàn bộ lịch sử Codex-web + HR, Problem Boundary A*, Governing Invariant, Closed-Loop Problem Resolution, Resolution Envelope và kế hoạch triển khai**
**Loại tài liệu:** strategic doctrine / methodological specification / implementation roadmap / research record
**Phạm vi:** `E:\DEV\Codex-web` và lịch sử representative natural workload tại `E:\DEV\HR STA\HR`
**Trạng thái triển khai tại 2026-08-26T08:34Z:** Revision 4 core source, semantic metrics, privacy boundary, module-size guard và focused proof đã hoàn tất; ba proof cũ ở `ACCEPTING` đã được controller chính thức terminalize thành `ABORTED` vì source bị supersede. Recovery Host manifest fix vẫn mới ở source, chưa được load; real-client discovery/acknowledgement, bounded canary, natural HR outcome, independent receipt, integrated delivery và production vẫn mở.
**Runtime policy change tại thời điểm viết:** chưa tự động thay đổi
**Architecture rewrite:** không

> **Mệnh đề trung tâm Revision 4:** Coding Tools không tồn tại để giúp AI tạo ra nhiều technical task, RUN, WAVE, proof hay acceptance hơn. Nó phải tối ưu cho việc **giữ ổn định user outcome contract, duy trì problem model như một hypothesis có thể sửa khi xuất hiện counterevidence, xác định đúng problem boundary nhỏ nhất đủ để giải quyết outcome, dùng observation có khả năng thay đổi quyết định, thực thi intervention causal nhỏ nhất dưới EOCL, và chỉ tuyên bố Trusted Problem Resolution trong một Resolution Envelope hữu hạn có đủ evidence và không còn contradiction trọng yếu chưa giải thích.**

---

# 0. Executive conclusion

## 0.1. Hai dự án đã cung cấp đủ tri thức để chốt hướng chiến lược

Codex-web và HR hiện tạo thành hai nửa của cùng một bài toán.

```text
CODEX-WEB
Execution authority
Workspace/source identity
RUN/WAVE/EOCL
Write fencing
Proof lineage
Recovery / REPLAN
Technical acceptance
PRL problem continuity foundations
        │
        │ operates on
        ▼
HR / V_FINANCE / BUSINESS WORKLOAD
User jobs thật
Business semantics thật
Canonical data/identity
Live SharePoint/runtime/data
Cross-surface UI behavior
User corrections thật
False closure thật
Repeated repair trajectories
```

Codex-web chứng minh hệ thống có thể quản trị **cách thực thi** ngày càng đáng tin. HR chứng minh rằng execution đáng tin chưa đủ nếu hệ thống chưa quản trị đúng **problem semantics và outcome thực tế**.

Kết luận chiến lược:

> **Bottleneck frontier đã dịch chuyển từ “AI có thực thi code đúng không?” sang “AI có đang giải đúng problem ở đúng boundary, cập nhật cách hiểu đúng khi evidence thay đổi, và biết khi nào user job thực sự đã hoàn thành không?”**

Không cần đợi thêm một chương trình nghiên cứu mới mới quyết định có đi hướng này hay không. Research tiếp theo chỉ còn nhiệm vụ:

- đo contribution của từng failure dimension;
- hiệu chỉnh fields/thresholds;
- định lượng ROI;
- loại bỏ ceremony không tạo TTPR value;
- quyết định phần nào đáng harden thành runtime semantics.

---

## 0.2. North Star giữ nguyên: TTPR

```text
TTPR = Time to Trusted Problem Resolution
```

Không tối ưu cuối cùng cho:

```text
model latency
cost per call
tokens per call
accepted RUN count
proof count
worker count
LOC
CPU utilization
cache hit rate
server offload ratio
```

Các metric đó chỉ là diagnostic hoặc secondary economics.

Objective:

> **Minimize TTPR and total expected work per trusted-resolved problem while preserving business semantics, security, data integrity, exact source/runtime authority and truthful evidence.**

---

## 0.3. Định nghĩa Trusted Problem Resolution

Một Problem Revision chỉ được coi là `TRUSTED_RESOLVED` khi trong **Resolution Envelope** của nó:

```text
1. user job / desired outcome đạt;
2. observation A không còn mâu thuẫn với contract;
3. governing invariants liên quan được thỏa;
4. relevant source/authority/runtime/data state khớp với claim;
5. technical proof có provenance phù hợp;
6. representative adjacent risks chỉ được kiểm khi có causal/risk basis;
7. không còn material counterevidence chưa giải thích;
8. một credible closure-falsification probe, khi risk yêu cầu, không bác được claim.
```

Trusted Resolution không có nghĩa toàn bộ domain hoàn hảo. Nó là **một claim hữu hạn, causal-complete và evidence-defensible**.

---

# 1. Evidence lịch sử làm thay đổi trọng tâm dự án

## 1.1. Codex-web: execution control đã giải quyết một lớp vấn đề thật

Lịch sử Codex-web đã chứng minh giá trị của:

```text
exact workspace/source identity
one canonical runtime authority
write lease/fencing
RUN/WAVE lifecycle
PREFLIGHT → READY → ROUTED → EXECUTING → PROVING → ACCEPTING → CHECKPOINTED
REPLAN / BLOCKED / ABORTED
proof fingerprints
exact-source proof reuse
runtime/package/source distinction
recovery host/tunnel
connector freshness
```

Incident 13/08 dẫn tới một bài học còn nguyên giá trị:

> **Policy quan trọng phải được enforce bởi state, authority và evidence chứ không chỉ nằm trong prompt.**

EOCL vì thế phải giữ.

---

## 1.2. Rework economics cho thấy tối ưu execution đơn thuần không đủ

Historical cohort 17/08:

```text
accepted organic runs = 188
first-pass            = 130 / 188 = 69.15%
repaired              = 58 / 188 = 30.85%
first-pass TTA p50    = 36.357 s
repaired TTA p50      = 192.319 s
median repair penalty ≈ 5.29x
```

Một cohort khác có task mix khác ghi first-pass khoảng 59.8%, repaired 40.2%; không được dùng để kết luận regression causal, nhưng cùng chỉ ra một fact kinh tế:

> **Repair probability có thể quan trọng hơn vài giây execution latency.**

Do đó:

```text
NOT:
minimize one attempt

BUT:
minimize total expected work to trusted resolution
```

---

## 1.3. Localization/orchestration là critical path material

Historical measured snapshot:

```text
local execution ≈ 7.59 h
estimated wait  ≈ 24.95 h
wait/local      ≈ 3.28x
localization    ≈ 59.5% measured phase timing
```

Không được coi toàn bộ wait là model latency. Nhưng nó bác bỏ chiến lược:

```text
faster model = solved performance problem
```

Nếu work mất ở:

- hiểu sai job;
- boundary quá hẹp;
- wrong target;
- đọc quá rộng;
- mutate quá sớm;
- oracle yếu;
- replan;
- proof lặp;
- runtime/control friction;

thì model-call speed không đánh đúng bottleneck.

---

## 1.4. Các subsystem kỹ thuật có thể đúng nhưng ROI thấp

Historical examples:

```text
LSP attempted = 963
LSP handled   = 5
```

và generic proof-cache snapshot:

```text
eligible = 563
hits     = 1
saved    = 996 ms
```

Bài học:

> **Technical completeness của một subsystem không chứng minh contribution vào Trusted Problem Resolution.**

---

## 1.5. Codex-web ledger: execution telemetry lớn nhưng problem-level truth từng rất mỏng

Immutable snapshot 25/08:

```text
RUN total        = 923
WAVE total       = 1,430
WAVE replanned   = 511
failure_observed = 656
```

Trong PRL v10 snapshot lúc đó:

```text
problem_threads    = 0
problem_events     = 1
policy-eligible    = 0
exact primary bind = 0
```

Sau đó PRL v11 tiếp tục được phát triển, nhưng lesson không đổi:

> **RUN/WAVE telemetry không tự trở thành knowledge về user problem resolution.**

---

## 1.6. HR `.coding-tools`: natural workload chứng minh technical closure bias

Read-only snapshot từ:

```text
E:\DEV\HR STA\HR\.coding-tools\orchestration\ledger.sqlite3
```

được khóa tại:

```text
max event seq  = 4481
max event time = 2026-08-26T04:18:03.551Z
```

Headline snapshot:

```text
RUN total      = 256
  accepted     = 34
  active       = 169
  stale        = 36
  aborted      = 17

WAVE total     = 278
  accepted     = 34
  active       = 169
  replanned    = 22
  aborted      = 53

EVENT total    = 4481
PROOF total    = 161
  passed       = 134
  failed       = 27

CHECKPOINT     = 34 accepted
```

Accepted RUN elapsed:

```text
avg ≈ 156.7 s
min ≈ 15.0 s
max ≈ 366.9 s
```

Nhưng quan hệ thật là:

```text
134 passed proofs
        ↓
34 technical accepted checkpoints
        ↓
? confirmed user problems resolved
```

Không được biến `34` thành problem-resolution denominator.

---

## 1.7. Proof-derived outcome là circular evidence

HR snapshot có:

```text
quality_outcome_recorded = 31
oracle_pass=true         = 31
```

Representative provenance:

```json
{
  "oracle_pass": true,
  "source": "accepted_proof_auto_v1"
}
```

Do đó:

```text
technical proof accepted
→ auto quality oracle_pass
→ dùng oracle_pass để chứng minh user resolution
```

là circular.

Rule:

> **Technical evidence có thể support một Resolution Claim nhưng không được tự biến thành independent end-to-end outcome evidence.**

---

## 1.8. HR oracle preflight cho thấy outcome-oracle coverage còn yếu

Snapshot:

```text
oracle_preflight total = 36
strong_oracle=true     = 2
strong_oracle=false    = 34
verification=none      = 14
```

Không được kết luận 34 trường hợp là sai. Nhưng đây là evidence rằng instrumentation hiện tại chưa buộc hệ thống phải phân biệt rõ:

```text
CODE ORACLE
CONTRACT ORACLE
RUNTIME ORACLE
SEMANTIC ORACLE
USER-OUTCOME ORACLE
```

---

## 1.9. Failure telemetry mô tả operational symptom tốt hơn causal process

61 `failure_observed` events trong HR gồm:

```text
CHECK_FAILED                  21
SOL_REJECTED                   6
BUILD_VERIFICATION_FAILED      6
CANDIDATE_MODEL_NOT_COMPLETED  5
PROMPT_TOO_LARGE               4
PERMISSION_REQUIRED            4
CANDIDATE_SCOPE_MISSING        4
BASE_DRIFT                     3
RUNTIME_RESUME_REQUIRED        2
PATCH_CONTEXT_NOT_FOUND        1
PATCH_AMBIGUOUS                1
MODE_ROUTE_MISMATCH            1
EXECUTION_OWNER_INVALID        1
...
```

Trong cohort này, P2 causal-attribution field chủ yếu absent/unattributed.

Bài học:

```text
error code history ≠ decision science
```

Muốn học resolution phải biết:

```text
current frame là gì?
what evidence contradicted it?
what hypothesis changed?
what discriminator changed the next decision?
what intervention followed?
did actual user outcome converge?
```

---

## 1.10. Control-plane debt là resolution cost thật

Representative HR replans từng liên quan:

- Node test-runner IPC deserialization;
- invalid fixture khiến validator chặn trước business logic;
- `.txt` entrypoint / Node behavior;
- monolithic patch/hunk ordering;
- malformed diff count;
- helper chưa materialize;
- PowerShell quoting;
- scoped network permission;
- HEAD/base drift;
- Solution Shadow gate;
- workflow admission mismatch;
- Sol lane `ExceptionGroup` trước write lease;
- file-attestation/proof receipt issues;
- workspace rebind;
- runtime generation lifecycle.

EOCL xử lý nhiều case đúng về safety. Nhưng user vẫn trả chi phí thời gian.

Do đó cần tách:

```text
NECESSARY GOVERNANCE COST
vs
AVOIDABLE GOVERNANCE FRICTION
```

Không demonize control plane; tối ưu implementation friction của control plane.

---

## 1.11. Semantic RUN fragmentation là structural

HR keyword activity trong 256 RUN:

```text
finance       114
revenue        72
payment        58
settlement     62
US-123         17
ManagingUnits  19
```

Các cluster chồng lấn, không phải problem counts.

Một user problem có thể sinh:

```text
diagnosis RUN
implementation RUN
proof-only RUN
formatting repair RUN
runtime activation RUN
fresh-source closure RUN
live dry-run RUN
production mutation RUN
```

User vẫn chỉ nhìn thấy **một problem**.

Vì vậy:

```text
RUN/WAVE = execution unit
Problem Revision = outcome/economic unit
```

---

## 1.12. HR business history cho thấy symptom patch không hội tụ

Repeated user-corrected areas gồm:

- Project → Finance information propagation;
- Project/status/header projection consistency;
- revenue/payment/settlement/receivable semantics;
- warranty/liquidation lifecycle;
- completion/collection ratio meaning;
- invoice-date lifecycle;
- canonical Personnel/Project/ManagingUnit identity;
- source correct nhưng running generation stale;
- live SharePoint field/storage truth khác source assumption.

Các trường hợp này cho thấy nhiều failure không phải “AI viết code kém”, mà là mismatch giữa:

```text
user job
business invariant
ownership
source assumptions
runtime/data state
proof abstraction
observable outcome
```

---

# 2. Leading strategic diagnosis — hypothesis, không phải dogma

Current leading strategic problem-frame hypothesis của Codex-web:

> **Execution truth đã trưởng thành nhanh hơn problem/outcome truth. Hệ thống tối ưu technical work ngày càng tốt nhưng semantic user problem, frame evolution, counterevidence và end-to-end resolution claim chưa trở thành first-class resolution objects tương xứng.**

Đây là **strategic hypothesis có evidence mạnh**, không được gọi là root cause duy nhất bất biến.

Nó phải tiếp tục falsifiable. Nếu future measurement cho thấy TTPR chủ yếu bị chi phối bởi một yếu tố khác, priority phải đổi.

---

# 3. Conceptual model Revision 4 — tách các khái niệm từng bị trộn

Revision 3 dùng `A*` gần với “Minimal Governing Problem”. Revision 4 sửa lại để dataset và decision logic không nhập nhằng.

## 3.1. A — User Observation / Manifestation

```text
A = điều người dùng hoặc hệ thống quan sát đang sai
```

Ví dụ:

```text
“Thông tin dự án sang Finance bị mất.”
“Công nợ đang sai.”
“Ngày hóa đơn bị bắt nhập dù chưa xuất hóa đơn.”
```

A **không mặc định** là complete problem boundary.

---

## 3.2. Problem Revision R — stable user contract

Problem Revision chứa phần user-level tương đối ổn định:

```yaml
problem_revision:
  user_job:
  desired_outcome:
  acceptance_contract:
  constraints:
  protected_semantics:
```

Rule:

```text
internal understanding changed ≠ Problem Revision changed
```

Chỉ `REVISE` khi user-level contract thay đổi vật chất.

---

## 3.3. A* — Minimal Sufficient Problem Boundary

Revision 4 định nghĩa:

> **A* là tập nhỏ nhất các domain, phenomena, ownership boundaries và relations cần được đưa vào problem model để có thể giải thích discrepancy hiện tại và xác định một intervention có khả năng làm user outcome đạt lại.**

A* là **problem boundary**, không phải root cause.

```text
A* ≠ Governing Invariant
A* ≠ Causal Hypothesis
A* ≠ Implementation Scope
A* ≠ Proof Scope
A* ≠ Architecture Scope
```

A* phải:

```text
minimal
evidence-supported
falsifiable
```

Nếu không có evidence phải mở rộng:

```text
A* ≈ A/local boundary
```

---

## 3.4. G — Governing Invariant

G trả lời:

> **Nếu system/domain đúng trong boundary này thì điều gì phải luôn đúng?**

Ví dụ Finance:

```text
Settlement establishes/finalizes entitlement;
it is not another additive payment event.

Receivable =
final recognized entitlement
- actual collections
- valid deductions/retentions.

Warranty liquidation settles/releases retained entitlement;
it does not create new revenue.
```

Ví dụ Project:

```text
All consumers of Project core identity/state
must derive from the same canonical ownership/read boundary
across save → navigation → reload.
```

---

## 3.5. Ownership/Control — ai tạo ra sự thật?

Một invariant nhiều khi không đủ nếu không biết ai sở hữu phenomenon.

```yaml
fact_ownership:
  authoritative_owner:
  allowed_writers:
  derived_consumers:
  observers:
```

Các problem canonical identity, shared header, Finance projection, runtime authority đều cần câu hỏi:

```text
WHO CONTROLS THIS FACT?
WHO MAY WRITE?
WHO MAY DERIVE?
WHO MAY ONLY OBSERVE?
```

---

## 3.6. H — Causal Hypotheses

H trả lời:

> Vì sao governing invariant hoặc user outcome đang không đúng?

Ví dụ:

```text
H1 persistence/write path mất dữ liệu
H2 API mapping bỏ field
H3 client normalization diverges
H4 stale runtime generation
H5 business rule itself encoded incorrectly
```

Complex system không bắt buộc có một root cause duy nhất.

Có thể cần minimal causal set:

```text
H2 + H4
```

mới giải thích đủ symptom.

---

## 3.7. F — Problem Frame

Problem Frame là **system hypothesis**, không phải user contract.

```yaml
problem_frame:
  observation_A:
  boundary_A_star:
  governing_invariants_G:
  ownership:
  causal_hypotheses_H:
  assumptions:
  evidence:
  counterevidence:
  falsifiers:
  current_confidence:
```

Frame có thể thay nhiều lần trong cùng Problem Revision:

```text
R1/F0 → R1/F1 → R1/F2
```

Đây là learning trajectory.

---

## 3.8. E — Execution Lineage

EOCL tiếp tục quản trị:

```yaml
execution:
  run:
  wave:
  workspace:
  source:
  authority:
  lease:
  mutation:
  proof:
  checkpoint:
```

Execution Lineage không bị thay thế bởi Problem Frame.

---

## 3.9. C — Resolution Claim

Resolution Claim trả lời:

> **Với evidence hiện tại, chính xác hệ thống được phép tuyên bố điều gì?**

Ví dụ:

```text
“Focused source behavior is correct.”
```

khác với:

```text
“Running production behavior is correct.”
```

khác với:

```text
“User problem is trusted-resolved.”
```

---

## 3.10. Resolution Envelope

Để “triệt để” nhưng không vô hạn:

```yaml
resolution_envelope:
  direct_outcomes:
  governing_invariants:
  relevant_truth_domains:
  representative_adjacent_risks:
  excluded_scope:
  required_evidence:
  credible_falsification_probe:
```

Trusted Resolution chỉ claim trong envelope.

---

# 4. Ba mô hình logic: Contract – State – Causal Model

Five Resolution Alignment Domains rất hữu ích để phân loại, nhưng logic reasoning sâu hơn là:

```text
1. NORMATIVE CONTRACT
   What should be true?

2. OBSERVED STATE
   What is actually true?

3. CAUSAL MODEL
   Why are they different and what can close the gap?
```

Hợp nhất:

```text
               PROBLEM REVISION / USER CONTRACT
                User Job + Desired Outcome
                         │
                         ▼
                 NORMATIVE MODEL
                 Governing invariants
                         │
                      compare
                         │
                         ▼
                  OBSERVED STATE
          source / runtime / data / UI / user
                         │
                   contradiction Δ
                         │
                         ▼
                   PROBLEM FRAME
             A* boundary + hypotheses H
                         │
                  discriminator
                         │
                         ▼
                    INTERVENTION
                         │
                         ▼
                   EOCL EXECUTION
                         │
                         ▼
                  NEW OBSERVATION
                         │
               compare back to contract
                         │
          ┌──────────────┴──────────────┐
          ▼                             ▼
       converged                    contradicted
          │                             │
          ▼                             ▼
 resolution claim                update frame
```

Đây là **closed-loop epistemic architecture**, không phải service architecture.

---

# 5. Five Resolution Alignment Domains

Không gọi tất cả là “truth planes” theo cùng epistemic nghĩa. Revision 4 dùng:

```text
D1 — INTENT / JOB ALIGNMENT
D2 — DOMAIN / SEMANTIC ALIGNMENT
D3 — ARTIFACT / SOURCE / AUTHORITY ALIGNMENT
D4 — OPERATIONAL / RUNTIME / DATA ALIGNMENT
D5 — OBSERVABLE OUTCOME ALIGNMENT
```

Trusted Resolution yêu cầu **không còn material contradiction trong relevant domains của Resolution Envelope**.

Hai trục cắt ngang:

```text
OWNERSHIP / CONTROL
EVIDENCE / ASSURANCE
```

---

# 6. Authority hierarchy

## 6.1. User có authority về outcome, không tự động về mechanism

Invariant:

> **User correction invalidates a resolution claim; it does not automatically validate a causal diagnosis.**

Ví dụ user nói:

> “Vẫn sai, chắc backend lỗi.”

Hệ thống phải tách:

```text
Outcome evidence:
problem still unresolved → authoritative for closure.

Causal claim “backend”:
hypothesis → needs evidence.
```

Authority ordering làm việc:

```text
USER / DOMAIN CONTRACT
        >
OBSERVED ENVIRONMENT / DATA
        >
DETERMINISTIC EVIDENCE
        >
AI-DERIVED FRAME
        >
AI NARRATIVE
```

AI là **frame proposer and discriminator**, không phải sovereign source of domain truth.

---

# 7. Closed-Loop Trusted Problem Resolution

Revision 4 loop:

```text
USER OBSERVATION A
        │
        ▼
1. CONTRACT
   User Job / Desired Outcome / Constraints
        │
        ▼
2. INITIAL FRAME
   A* boundary / G invariants / H hypotheses
        │
        ↕
3. ORACLE PREFLIGHT
   Can we observe the claim at the right abstraction level?
        │
        ▼
4. TRUTH/STATE PREFLIGHT
   workspace/source/authority/runtime/data as relevant
        │
        ▼
5. FIND CONTRADICTION / DIVERGENCE
   where normative != observed?
        │
        ▼
6. DECISION-CHANGING DISCRIMINATOR
   cheapest observation that can alter next action
        │
        ▼
7. UPDATE / FALSIFY FRAME
   incorporate evidence/counterevidence
        │
        ▼
8. CAUSAL MINIMAL INTERVENTION
   smallest coherent change sufficient for envelope
        │
        ▼
9. EOCL TECHNICAL EXECUTION + PROOF
        │
        ▼
10. END-TO-END OUTCOME / INVARIANT EVIDENCE
        │
        ▼
11. CLOSURE FALSIFICATION PROBE
    cheapest credible counterexample check when justified
        │
        ├── PASS → TRUSTED RESOLUTION → STOP
        │
        └── CONTRADICTION
                │
                ▼
        classify failure dimensions
        update frame / reopen / revise contract
```

Không phải mọi local bug cần toàn bộ ceremony. Nếu strong oracle và exact cause đã rõ:

```text
A* ≈ local boundary
→ direct causal change
→ focused proof
→ relevant outcome
→ stop
```

---

# 8. Oracle discipline

## 8.1. Oracle must match the claim abstraction

```text
CODE_ORACLE
CONTRACT_ORACLE
RUNTIME_ORACLE
SEMANTIC_ORACLE
USER_OUTCOME_ORACLE
```

Không phải problem nào cần cả năm.

Rule:

> **Oracle phải đủ để quan sát claim đang xin quyền đóng, không phải chỉ đủ để chứng minh một layer thấp hơn.**

---

## 8.2. Oracle và Frame co-evolve

Không hard-code pipeline:

```text
Frame complete → Oracle complete
```

Thực tế:

```text
INITIAL FRAME ↔ ORACLE PREFLIGHT
```

Ví dụ “công nợ sai” chưa biết công nợ nghĩa là receivable, cash outstanding hay settlement entitlement thì chưa chọn được oracle đúng.

Chỉ yêu cầu frame/oracle settle **đủ** trước mutation.

---

# 9. Decision Delta Test

Một observation chỉ đáng cost khi ít nhất một plausible outcome có thể đổi next decision.

Trước diagnostic action:

```text
If result = X, what will I do?
If result = Y, what will I do?
```

Nếu:

```text
X → same action
Y → same action
```

observation không phải discriminator.

Ví dụ tốt:

```text
Inspect persisted record.

absent → investigate write/persistence
present → eliminate persistence; inspect API/read path
```

Ví dụ thấp giá trị:

```text
read seven nearby components
```

nếu bất kể đọc gì vẫn patch cùng function.

Đây là surrogate rẻ cho information gain, không cần numeric EIG giả precision.

---

# 10. Counterevidence-Driven Frame Update

Sai hypothesis ban đầu là bình thường trong partially observable system.

Failure đáng giảm là:

> **Tiếp tục hành động theo cùng frame sau khi material counterevidence đã xuất hiện mà không giải thích contradiction.**

Hard decision doctrine đủ chín để áp dụng:

```text
NO SAME-FRAME MUTATION RETRY
AFTER MATERIAL COUNTEREVIDENCE
WITHOUT FIRST EXPLAINING THE CONTRADICTION
```

Không dùng rule cơ học:

```text
2 failures → diagnose
```

Mà dùng:

```text
failure compatible with frame → may continue
failure contradicts frame      → update frame first
```

---

# 11. Causal Minimal Intervention

Nguyên tắc:

> **Think broad enough to frame correctly; intervene as narrowly as causally sufficient.**

Không tối ưu:

```text
smallest diff at any cost
```

Mà:

```text
smallest coherent intervention
that restores the implicated invariant / causal relation
inside the Resolution Envelope
```

Một patch 3 dòng tạo sibling recurrence có thể đắt hơn một change 50 dòng phục hồi đúng ownership boundary.

Architecture change chỉ được biện minh khi governing invariant/ownership thực sự yêu cầu.

---

# 12. Closure Falsification Probe

Sau positive proof, trước khi claim Trusted Resolution, hỏi:

> **Observation rẻ nhất nào có khả năng bác resolution claim này?**

Ví dụ:

```text
save works → reload?
Project canonical state fixed → one independent consumer?
settlement calculation looks right → lifecycle reconciliation?
source proof passes → running generation current?
```

Không chạy broad suite như nghi lễ.

Chỉ một hoặc vài probe có causal/risk basis.

---

# 13. False Closure và failure dimensions

## 13.1. False Closure là outcome class

```text
FALSE_CLOSURE =
technical/operational completion claim
followed by credible same-contract evidence
that the user problem remains unresolved
```

False Closure không phải nguyên nhân.

```yaml
false_closure:
  occurred: true
  contributing_dimensions:
    - UNDERFRAMED
    - ORACLE_MISMATCH
    - RUNTIME_MISMATCH
```

---

## 13.2. Failure dimensions

Không dùng hierarchy tuyệt đối. Một problem có thể compound.

```text
P — PROBLEM MODEL / BOUNDARY
    underframed
    overframed
    wrong abstraction

S — SEMANTIC / INVARIANT / OWNERSHIP
    wrong business meaning
    wrong canonical owner
    lifecycle contradiction

C — CAUSAL DIAGNOSIS
    wrong causal boundary
    unsupported root-cause assumption

I — IMPLEMENTATION
    implementation defect
    incomplete coherent change

O — ORACLE / EVIDENCE
    oracle mismatch
    circular evidence
    insufficient end-to-end evidence

T — TRUTH / STATE ALIGNMENT
    wrong workspace/source
    stale runtime
    data/projection mismatch

E — EXECUTION / CONTROL
    transport failure
    attestation friction
    permission/admission
    harness/runtime lifecycle
```

Giai đoạn đầu có thể lưu:

```text
primary_failure_dimension
contributing_dimensions[]
```

không cần schema 7 chiều bắt buộc ngay.

---

# 14. Problem Revision, Frame Revision và Execution Lineage

Một semantic problem có trajectory:

```text
Problem Revision R1
│
├─ Frame F0
│   └─ RUN/WAVE...
│        ↓ counterevidence
│
├─ Frame F1
│   └─ RUN/WAVE...
│        ↓ discriminator
│
└─ Frame F2
    └─ RUN/WAVE...
         ↓
    Trusted Resolution R1
```

`F0 → F1` không phải `R1 → R2` nếu user contract không đổi.

Điều này cho phép đo **framing regret** thay vì che underframing bằng việc tạo problem mới.

---

# 15. Technical Acceptance → Provisional Problem Resolution

Semantic bridge đề xuất:

```text
RUN/WAVE:
ACCEPTED
```

không tự tạo:

```text
Problem:
TRUSTED_RESOLVED
```

Nó chỉ cho phép:

```text
Problem:
PROVISIONALLY_RESOLVED
```

khi technical claim materially supports outcome contract.

Sau outcome/envelope evidence:

```text
Problem:
TRUSTED_RESOLVED
```

Nếu cùng contract còn fail:

```text
Problem:
REOPENED
```

Nếu user contract đổi:

```text
Problem:
REVISION
```

Đây là một trong các semantics đủ chín để triển khai sớm vì nó khớp hướng PRL/EOCL hiện có.

---

# 16. Methodological hierarchy of evidence

Khi claim resolution:

```text
1. USER JOB / ACTUAL OUTCOME
2. GOVERNING-INVARIANT / DOMAIN EVIDENCE
3. RELEVANT RUNTIME / DATA / INTEGRATION EVIDENCE
4. TECHNICAL ORACLE
5. SOURCE / DIFF REASONING
6. AI NARRATIVE
```

Không phải tầng trên luôn “thay thế” tầng dưới; chúng support các subclaims khác nhau.

AI narrative không được tự promote thành truth.

---

# 17. Resolution Assurance Case — claim → argument → evidence

Không cần GSN engine. Chỉ cần tư duy explicit:

```text
TOP CLAIM:
User Job J is resolved within Resolution Envelope E.

SUBCLAIM 1:
Relevant governing invariant G is correct.

SUBCLAIM 2:
Current source implements G.

SUBCLAIM 3:
Running system/data corresponds to relevant source/state.

SUBCLAIM 4:
Observed end-to-end workflow reaches desired outcome.

SUBCLAIM 5:
Credible adjacent/falsification probe does not contradict the claim.
```

Mỗi proof phải trả lời:

> **Nó chứng minh subclaim nào?**

Build PASS không tự chứng minh runtime. Runtime current không tự chứng minh semantics. Unit test không tự chứng minh user journey.

---

# 18. Problem Resolution Funnel Revision 4

```text
OBSERVATION REPORTED
       ↓
USER CONTRACT CAPTURED
       ↓
INITIAL FRAME / A* / G / H
       ↓
ORACLE + TRUTH PREFLIGHT
       ↓
FAILURE OBSERVED
       ↓
CONTRADICTION / DIVERGENCE LOCALIZED
       ↓
DECISION-CHANGING DISCRIMINATOR
       ↓
FRAME UPDATED / FALSIFIED
       ↓
CAUSAL INTERVENTION
       ↓
EOCL TECHNICAL ACCEPTANCE
       ↓
PROVISIONAL PROBLEM RESOLUTION
       ↓
RESOLUTION ENVELOPE EVIDENCE
       ↓
CLOSURE FALSIFICATION PROBE
       ↓
TRUSTED RESOLUTION
```

Typed exits:

```text
BLOCKED
ABANDONED
SUPERSEDED
NON_PROBLEM
DUPLICATE
EXTERNAL_DEPENDENCY
```

---

# 19. Metrics stack

## 19.1. Tier 0 — hard floors

```text
security
data integrity
financial/business semantics
authority
exact workspace/source identity
privacy/secrets
destructive-action policy
```

Không trade-off.

---

## 19.2. Tier 1 — North Star / product resolution

```text
TTPR p50/p90
First-Pass Trusted Resolution Rate
Trusted Resolution Rate
False Closure Rate
Reopen Rate attributable to unresolved same contract
User correction turns/problem
```

---

## 19.3. Tier 2 — framing / learning diagnostics

```text
Problem Boundary Error Rate
Frame Revisions / Problem
Frame Correction Gap
Framing Regret
Underframing Attributable Work
True Sibling Recurrence Rate — OPEN; requires explicit semantic sibling linkage
Multi-Primary-Run Revision Rate — DESCRIPTIVE PROXY currently implemented
Same-Frame Retry After Counterevidence
```

### Framing Regret

```text
avoidable work performed after
material counterevidence against the active frame
became available
```

Không phạt hypothesis đầu tiên chỉ vì sai.

---

## 19.4. Tier 3 — decision diagnostics

```text
Decision Delta Shadow Attestation Rate — DESCRIPTIVE / SHADOW-ATTESTED
Decision-Changing Observation Rate with causal value — OPEN
low-value observation count
Discriminator-to-Mutation Ratio
wrong-target incidence
wrong-causal-boundary incidence
premature-mutation incidence
```

Decision-Changing Observation Rate cao hơn không tự động tốt nếu observation quá đắt; nó là diagnostic.

---

## 19.5. Tier 4 — oracle / evidence diagnostics

```text
Independent Outcome Evidence Coverage — OPEN
Oracle-Level Mismatch Rate
Technical-Acceptance → Outcome Gap
Circular Evidence Incidence
Closure Falsification Coverage
Resolution Envelope Evidence Attestation Coverage
  — DESCRIPTIVE / ATTESTED / NOT INDEPENDENT CONFIRMATION
```

---

## 19.6. Tier 5 — execution/control economics

```text
Necessary Governance Time
Avoidable Control Friction Time
Proof Repetition Cost
Runtime/Source Mismatch Time
Context Reconstruction Time
Handoff/queue/wait time
```

Không dùng một overhead ratio duy nhất nếu chưa decomposition.

---

## 19.7. Tier 6 — model/compute economics

```text
cost/problem resolved
tokens/problem
route/model usage
server/local compute
cache value
worker count
```

Chỉ tối ưu sau khi Tier 1 không xấu đi.

---

# 20. TTPR decomposition

```text
TTPR =
T_contract
+ T_frame
+ T_oracle_preflight
+ T_truth_preflight
+ T_discriminate
+ T_intervene
+ T_verify
+ T_necessary_governance
+ T_avoidable_control_friction
+ T_wait
+ T_repair
+ T_user_outcome
```

Điểm cần giảm đặc biệt:

```text
T_bad_frame / framing regret
T_low_value_observation
T_repair
T_avoidable_control_friction
T_duplicate_proof
```

Không cố xóa necessary governance.

---

# 21. History: từ Transcript/Patch Memory sang Resolution Case Memory

## 21.1. Không replay raw history

Giá trị history không phải:

```text
lần trước sửa file nào?
model nào chạy?
test nào pass?
```

Mà:

```text
manifestation nào?
user contract nào?
problem boundary nào?
invariant nào?
ownership nào?
hypothesis nào?
evidence/counterevidence nào?
frame đã đổi vì sao?
intervention nào?
outcome thế nào?
falsifier nào?
case applicable khi nào?
```

---

## 21.2. Resolution Case

Conceptual unit:

```yaml
resolution_case:
  problem_revision:
  user_observation:
  frames:
    - frame_id:
      boundary_A_star:
      governing_invariants_G:
      ownership:
      causal_hypotheses_H:
      evidence:
      counterevidence:
      falsifiers:
  executions:
  interventions:
  resolution_claims:
  outcome:
  sibling_recurrence:
  applicability_conditions:
  negative_transfer_warning:
```

Chưa cần DB object mới. Đây là target data model cho future learning.

---

## 21.3. History reuse rule

History chỉ được sinh:

```text
candidate frame hint
candidate invariant
candidate discriminator
candidate falsifier
negative-transfer warning
```

Không tự trở thành causal truth.

Path:

```text
History
→ Case Retrieval by Applicability
→ Candidate Hint
→ Current Evidence Check
→ Use / Reject
→ Current Outcome
→ Update Case Memory
```

---

# 22. Có thể tận dụng ngay những gì từ lịch sử hiện tại

## 22.1. EOCL — dùng nguyên trạng làm execution authority

Tận dụng ngay:

```text
RUN/WAVE lifecycle
write lease
exact workspace/source
REPLAN semantics
proof fingerprint
acceptance checkpoint
recovery
```

Không redesign.

---

## 22.2. PRL v11 semantics — làm hạt nhân Problem Revision

Tận dụng các concepts hiện có:

```text
problem identity
problem revision
same problem vs new problem
user feedback intent
confirm / reopen / revise / block / abandon
contract capsule / acceptance criteria / protected invariants
```

Điều cần bổ sung chủ yếu là **frame evolution và resolution-claim bridge**, không xây DB thứ hai.

---

## 22.3. Existing user corrections — high-value outcome evidence

Các câu:

```text
“vẫn sai”
“vẫn không hiển thị”
“logic chưa đúng”
“A đúng nhưng B vẫn sai”
```

có thể dùng ngay để reconstruct:

```text
same-contract unresolved outcome
false closure
frame contradiction candidates
```

Không được tự infer causal cause từ user correction.

---

## 22.4. Existing HR domain artifacts — governing-invariant evidence

Có thể tận dụng:

```text
PFM finance blueprint
canonical identity hardening
Project/Finance lifecycle semantics
SharePoint schema/live data evidence
settlement/payment/receivable/warranty rules
live runtime generation checks
```

Các artifact này là source tốt hơn model guess cho domain semantics.

---

## 22.5. Existing technical proof — giữ nguyên provenance

Technical proof không bị bỏ đi khi problem reopen.

Rule:

```text
proof remains valid for the exact claim/fingerprint it proved
```

Chỉ không được overclaim thành user resolution.

---

## 22.6. Existing replan reasons — source cho control-friction taxonomy

Dùng để phân:

```text
necessary governance
avoidable transport/harness friction
semantic replan
truth-plane correction
```

Không cần thu thập lại từ đầu.

---

# 23. Những gì lịch sử hiện tại chưa đủ và phần đã được triển khai

## 23.1. Canonical Problem-to-RUN linkage — ĐÃ TRIỂN KHAI PRL v11

Cần:

```text
Problem Revision → frames → RUN/WAVE links
```

với confidence/provenance và `AMBIGUOUS` khi không đủ evidence.

Không dùng exact objective-string equality. `agent_workflow` hiện yêu cầu
`problem_id + problem_revision + contract_fingerprint` trước khi tạo một RUN
problem-bearing; runtime ghi `ENGINEERING_ATTEMPT_BOUND` với exact primary
link, còn host identity không đủ thì giữ `AMBIGUOUS/UNLINKED` thay vì đoán.

Evidence source/test:

```text
resources/coding-tools-mcp/coding_tools_mcp/problem_lineage.py
resources/coding-tools-mcp/coding_tools_mcp/workflow_tools.py
resources/coding-tools-mcp/tests/test_problem_lineage.py
```

---

## 23.2. Frame Revision history — ĐÃ TRIỂN KHAI SHADOW-ONLY

Cần capture tối thiểu:

```text
frame_id
boundary A*
G invariants
H hypotheses
material counterevidence
frame-change reason
```

Đã có bounded `problem_frame` packet trong `agent_workflow.problem_context`.
Runtime canonicalize và hash packet, đưa identity/hash vào `problem_frame_shadow`
event; raw transcript, private reasoning, credential/PII và authority side
effects bị từ chối. Frame hiện vẫn shadow/advisory và không hard gate route,
mutation hay acceptance.

---

## 23.3. Oracle provenance — ĐÃ TRIỂN KHAI Ở CLAIM/ENVELOPE TẦNG CƠ BẢN

PRL/EOCL đã tách technical proof khỏi outcome claim; `resolution_envelope` bắt
buộc mỗi evidence item phải mang `kind`, `provenance`, `status`, và claim
reconciliation kiểm tra lại hash. `accepted_proof_auto_v1` vẫn chỉ là technical
quality evidence, không được dùng độc lập để confirm user resolution.

Các lớp oracle đầy đủ hơn vẫn là calibration work; không tuyên bố đã có
semantic/user-outcome oracle tự động.

```text
oracle_type
claim_supported
source
independent_from_acceptance
observed_target
runtime/source fingerprint when relevant
```

---

## 23.4. Resolution Envelope/Claim — ĐÃ TRIỂN KHAI DURABLE TRONG WAVE CLAIM

`task_control(action=accept)` hiện yêu cầu `problem_resolution_envelope` cho
mọi `full_problem` claim. Envelope được bounded/canonicalize, lưu trong wave
metadata và frozen `problem_outcome_claim`, kèm SHA-256; checkpoint bridge chỉ
reconcile khi envelope còn nguyên. Public surface không tăng thêm tool.

Sau calibration mới quyết định durable event/schema.

---

## 23.5. Decision Delta — DONE DESCRIPTIVE / SHADOW-ATTESTED

Cần instrumentation nhẹ:

```text
observation
possible_result_branches
next-action delta? yes/no
```

Frame packet yêu cầu `decision_delta.tested_observation`,
`changed_decision`, `next_action`, `rationale`; runtime chỉ lưu identity/hash
và cờ quyết định có đổi hay không trong ledger event. Không lưu chain-of-thought.

Reporter chỉ đo attestation do caller/controller khai trong shadow packet. Giá
trị causal của observation chưa được retrospective receipt hoặc treatment
comparison chứng minh; vì vậy metric public hiện mang tên
`decision_delta_shadow_attestation_rate`, không phải Decision-Changing
Observation Rate.

Chỉ bounded structured intent.

---

## 23.6. Governance/friction decomposition — ĐÃ CÓ DESCRIPTIVE REPORTING

Reporter Revision 4 hiện xuất counts từ typed `wave_replanned.reason` và giữ
`unknown` là missingness; việc gán nhãn causal chi tiết hơn vẫn phải qua
calibration/annotation, không tự suy ra từ keyword.

```text
necessary_safety
avoidable_transport
avoidable_runtime_lifecycle
semantic_recovery
unknown
```

---

# 24. Kế hoạch triển khai — không đợi nghiên cứu để áp dụng doctrine

## PHASE 0 — Doctrine activation ngay lập tức — ĐÃ ÁP DỤNG

**Mục tiêu:** thay đổi cách reasoning/acceptance, không thay runtime schema.

Áp dụng ngay 10 invariants:

1. Problem Revision chỉ đổi khi user contract đổi.
2. Problem Frame có thể đổi nhiều lần trong một Revision.
3. Tách `A* boundary`, `G invariant`, `H causal hypothesis`.
4. User authority về outcome khác mechanism authority.
5. Không scope expansion nếu chưa có contradiction/evidence.
6. Không same-frame mutation sau material counterevidence mà chưa giải thích.
7. Diagnostic observation phải qua Decision Delta Test khi uncertainty material.
8. Technical ACCEPTED không tự đồng nghĩa Trusted Resolution.
9. Resolution phải nằm trong bounded Resolution Envelope.
10. Risk material thì dùng một cheap credible Closure Falsification Probe.

Doctrine đã được phản ánh trong PRL/EOCL acceptance contract và các guard
reconciliation; không có runtime route/policy tự động mới.

---

## PHASE 1 — Tận dụng machinery hiện có, minimal semantic bridge — ĐÃ TRIỂN KHAI

### 1A. PRL Problem Revision làm user-contract authority

Dùng existing problem-event semantics để:

```text
OPEN        → tạo Problem Revision
LINK        → liên kết RUN/WAVE
FEEDBACK    → same problem correction / new evidence
REOPEN      → same contract still failing
REVISE      → only when contract changes
CONFIRM     → user/outcome confirmation
BLOCK       → external blocker
ABANDON     → explicit abandon
```

### 1B. Technical acceptance chỉ tạo provisional status

Implementation semantics hiện tại:

```text
EOCL ACCEPTED
→ PRL PROVISIONALLY_RESOLVED
```

không tự:

```text
→ TRUSTED_RESOLVED
```

### 1C. User correction tự động ưu tiên reopen path

Nếu feedback intent = same problem still failing và contract fingerprint không đổi:

```text
PROVISIONAL/RESOLVED → REOPENED
```

Technical proofs cũ không bị xóa; contract fingerprint không đổi nên
`REOPEN` giữ nguyên Problem Revision, còn `REVISE` dùng compare-and-swap để
tạo revision mới.

### 1D. Không thêm public tool

Dùng `task_control problem` / `agent_workflow` làm front doors hiện có.

---

## PHASE 2 — Shadow Problem Frame trong existing prepare/analysis path — ĐÃ TRIỂN KHAI

**Mục tiêu:** capture decision state mà không trao authority.

Internal/shadow fields đề xuất:

```yaml
frame:
  frame_id:
  observation_A:
  boundary_A_star:
  governing_invariants_G:
  ownership:
  causal_hypotheses_H:
  evidence_for_scope_expansion:
  counterevidence:
  falsifier:
  oracle_type:
  decision_delta_check:
```

Properties:

- không grant mutation;
- không tự đổi route;
- không tự close problem;
- không hard confidence threshold;
- không public MCP tool mới;
- không database mới nếu existing ledger event/capsule đủ.

Nếu existing schema không phù hợp, shadow trước trong bounded controller state; chỉ materialize schema sau calibration.

---

## PHASE 3 — Resolution Claim + Envelope — ĐÃ TRIỂN KHAI FAIL-CLOSED

Add working object trước acceptance:

```yaml
resolution_claim:
  statement:
  direct_outcomes:
  governing_invariants:
  relevant_truth_domains:
  required_evidence:
  representative_adjacent_risks:
  excluded_scope:
  falsification_probe:
```

Acceptance flow:

```text
technical proof
→ provisional claim
→ outcome/envelope evidence
→ falsification probe
→ trusted resolution OR reopen
```

Đường `full_problem` hiện fail-closed khi thiếu envelope hoặc probe chưa
`executed/passed`; workload không phải `full_problem` vẫn giữ ordinary EOCL
acceptance. Đây là bounded claim gate, không phải global user-resolution claim.

---

## PHASE 4 — Oracle provenance hardening — MỘT PHẦN ĐÃ TRIỂN KHAI

Add type/provenance to outcome observations where possible:

```text
CODE
CONTRACT
RUNTIME
SEMANTIC
USER_OUTCOME
```

Rule đủ mạnh để harden:

```text
proof-derived quality event
CANNOT independently confirm user problem resolution
```

Envelope provenance/status đã được harden ở claim boundary. Phân loại toàn bộ
`CODE/CONTRACT/RUNTIME/SEMANTIC/USER_OUTCOME` và independent reviewer vẫn chưa
được hard-code.

---

## PHASE 5 — Golden Resolution Cases dùng để calibration, không phải permission — CHƯA ĐỦ DỮ LIỆU

Chọn 5–10 HR trajectories rõ:

1. Settlement / Payment / Receivable / Warranty semantics.
2. Project → Finance information propagation.
3. DA2201.1 live PFM end-to-end.
4. Personnel / ManagingUnit canonical identity.
5. Runtime/source mismatch / workspace rebind.
6. Invoice date lifecycle.
7. Status save nhưng projection/runtime vẫn cũ.

Mục đích:

```text
refine vocabulary
test annotatability
remove redundant fields
calibrate failure dimensions
calibrate envelope scope
identify negative-transfer risks
```

Không dùng để quyết định có theo strategic direction hay không — hướng đã được chốt.

---

## PHASE 6 — Backfill Resolution Cases từ lịch sử hiện có — CHƯA TỰ ĐỘNG BACKFILL

Cho mỗi selected case:

```text
Problem Revision
User Job
Desired Outcome
Frame F0/F1/...
A* boundary
G invariants
ownership
H hypotheses
oracle
counterevidence
Decision Delta observations
RUN/WAVE links
technical acceptance
user correction
final outcome
falsification probe if known
```

Giữ `AMBIGUOUS` khi không đủ evidence.

Không fabricate hidden reasoning.

---

## PHASE 7 — Metrics instrumentation — DESCRIPTIVE DONE / CAUSAL UNKNOWN

Tối thiểu:

```text
TTPR
First-Pass Trusted Resolution
False Closure
Frame Revisions / Problem
Framing Regret
Decision Delta Shadow Attestation Rate — DESCRIPTIVE / SHADOW-ATTESTED
Resolution Envelope Evidence Attestation Coverage
  — DESCRIPTIVE / ATTESTED / NOT INDEPENDENT CONFIRMATION
Technical-Accepted → Outcome Gap
Multi-Primary-Run Revision Rate — DESCRIPTIVE PROXY
True Sibling Recurrence — OPEN / NOT CONVERGED
Necessary Governance Time
Avoidable Control Friction Time
```

Reporter schema v3 đã thêm các trường problem-revision denominator cho TTPR
interval, first-pass trusted resolution, false closure, frame revisions,
shadow-attested Decision Delta, envelope evidence attestation, multiple exact
primary RUN proxy và control-friction decomposition. Ba key dễ gây overclaim
`decision_changing_observation_rate`, `outcome_evidence_coverage` và
`sibling_recurrence` đã bị loại bỏ, không giữ alias. Các trường thiếu evidence
trả `null`/censored/unknown, không impute zero; chưa có dashboard, semantic
sibling linkage, independent outcome receipt hay promotion policy.

---

## PHASE 8 — Prospective protocol — SHADOW CONTRACT ĐÃ SẴN SÀNG, CHƯA CHẠY COHORT

Control:

```text
current Outcome-First workflow
```

Treatment:

```text
Outcome Contract
+ A*/G/H separation
+ Oracle Preflight
+ Decision Delta Test
+ Counterevidence-Driven Frame Update
+ Causal Minimal Intervention
+ Resolution Envelope
+ Closure Falsification Probe
```

Giữ model/tool/compute route giống nhau khi đo methodology effect.

---

## PHASE 9 — Promote only measured micro-policies — CHƯA PROMOTE

Candidates:

```text
MP1 Ambiguous target → exact discriminator
MP2 Multiple plausible causes → separating observation
MP3 Material counterevidence → update frame before same-family mutation
MP4 Weak/misaligned oracle → repair oracle before broad mutation
MP5 Technical pass ≠ trusted resolution
MP6 Early stop when envelope sufficient
MP7 Oracle provenance guard
MP8 Semantic continuity across RUNs
MP9 Evidence-gated boundary expansion
MP10 Shared-invariant sibling convergence
MP11 Decision Delta Test
MP12 Closure Falsification Probe
```

Không promote methodology như monolith.

---

# 25. Kế hoạch triển khai theo mức độ chắc chắn

## 25.1. APPLY NOW — đủ evidence

```text
Problem Revision ≠ RUN
Technical Accepted ≠ Trusted Resolved
same contract correction → REOPEN
contract change → REVISE
A* boundary ≠ G invariant ≠ H cause
user outcome authority ≠ mechanism authority
exact source/runtime authority before claim
no unchanged semantic retry
counterevidence must update decision state
Decision Delta Test for material diagnostics
bounded Resolution Envelope
proof provenance preserved
```

---

## 25.2. SHADOW / ADVISORY FIRST

```text
frame_id / frame revisions
A* classification
failure-dimension vector
sibling prediction
frame confidence
closure falsification suggestion
case-memory applicability scoring
```

Lý do: cần calibration để tránh A* hallucination, overframing và ceremony.

---

## 25.3. DO NOT BUILD YET

```text
A* inference engine
Problem Governance Engine
Problem Algebra Engine
Resolution Compiler authoritative brain
Universal Domain Invariant Database
Problem Convergence Graph database
new public MCP framing tool
second PRL-like database
hard LLM confidence gate
full learned policy/router from current history
multi-agent governance committee
```

---

# 26. Anti-overengineering guards

## Guard 1

> **Do not broaden because the system is complex; broaden because the current problem model fails to explain evidence.**

## Guard 2

Mỗi wider A* phải trả lời:

```text
What evidence requires a wider boundary?
What contradiction does the wider boundary explain?
What observation could falsify the wider frame?
```

Không trả lời được:

```text
A* ≈ current/local boundary
```

## Guard 3

Resolution Envelope luôn có:

```text
excluded_scope
```

## Guard 4

Architecture change chỉ khi governing invariant/ownership cần nó.

---

# 27. Examples áp dụng

## 27.1. Project → Finance mất thông tin

```text
A:
fields mất sau Project → Finance / reload

R1:
User Job = quản trị cùng một Project xuyên các surfaces
Desired Outcome = core Project state nhất quán

A* candidate:
Project core state ownership/read boundary

G:
all consumers derive same canonical Project state

H:
H1 Finance normalization drops fields
H2 API mapper drops fields
H3 persistence incomplete
H4 runtime stale

Discriminator:
persisted state → API → normalized client state → render

Intervention:
smallest boundary restoring canonical consumption

Resolution Envelope:
Finance direct fields
reload persistence
one representative shared-header consumer
current runtime generation
excluded: unrelated charts/refactors
```

---

## 27.2. Công nợ / settlement / payment

```text
A:
receivable displayed wrong

R1:
User Job = biết project entitlement, collections and remaining receivable

A*:
financial lifecycle boundary

G:
settlement finalizes recognized entitlement
payments are actual collections
receivable = entitlement - collected - valid deductions/retentions
warranty liquidation settles retained entitlement, not new revenue

H:
UI-local calculation
wrong domain formula
double deduction
mixed management revenue and cash concepts

Oracle:
lifecycle reconciliation, not widget snapshot only
```

---

## 27.3. Canonical identity

```text
A:
Project/Unit/Personnel mapping errors

A*:
cross-system entity identity boundary

G:
immutable canonical identity owns cross-system relation
natural key only reconciliation aid

Ownership:
canonical ID owner explicit

Outcome:
relations resolve unambiguously

Important:
Fixing canonical identity does not automatically prove every Finance remap/downstream flow.
```

---

## 27.4. Source correct nhưng live vẫn sai

```text
A:
source tests green, HTTP still old behavior

A*:
source → running-generation boundary

G:
request must be served by process generation corresponding to accepted source/package

H:
stale process / wrong checkout / supervisor lifecycle

Closure falsifier:
inspect serving PID/generation/source identity
```

---

## 27.5. Invoice date lifecycle

```text
A:
invoice date required before invoice exists

A*:
invoice-state lifecycle boundary

G:
issue date is meaningful/required only when invoice state represents issued invoice

H:
record-exists conflated with invoice-issued

Intervention:
domain/schema/UI requirement alignment
```

---

# 28. Research/calibration program — phục vụ refinement, không quyết định hướng đi

## 28.1. Golden Cases

5–10 cases như Phase 5.

## 28.2. Expanded cohort

Sau taxonomy ổn định:

```text
30–50 repaired/reopened
vs
30–50 first-pass trusted/near-trusted
```

## 28.3. Questions

```text
RQ0: bao nhiêu avoidable work do continuing under contradicted frame?
RQ1: problem-boundary error material đến mức nào?
RQ2: wrong semantic invariant/ownership chiếm bao nhiêu?
RQ3: Decision Delta Test giảm low-value observations không?
RQ4: oracle-level mismatch đóng góp bao nhiêu False Closure?
RQ5: control friction nào necessary vs avoidable?
RQ6: Resolution Envelope giảm sibling recurrence mà không scope creep không?
RQ7: case memory có negative transfer ở task classes nào?
RQ8: sau khi giữ methodology constant, model route nào tối ưu cost/TTPR?
```

Model routing nằm sau resolution-method questions.

---

# 29. Breakthrough criteria

Không gọi “đột phá” chỉ vì conceptual model đẹp.

Candidate methodology đáng promote nếu representative workload cho thấy:

```text
First-Pass Trusted Resolution ↑ material
TTPR p50/p90 ↓ material
False Closure ↓ material
Framing Regret ↓ material
Sibling Recurrence ↓ material
User correction turns/problem ↓ material
Avoidable Control Friction ↓ material
business/security/data/authority non-inferior
protocol overhead bounded
```

Working economic targets để đáng chú ý:

```text
median TTPR improvement ~30%+
repair/reopen reduction ~25–30%+
```

Không phải statistical theorem.

Nếu methodology thêm complexity nhưng chỉ cải thiện 5–10% và không giảm repair/false closure, ưu tiên **simplify/remove**.

---

# 30. Vai trò đúng của các kiến trúc hiện có

## EOCL — KEEP

Execution authority / proof / source / lifecycle.

## PRL — KEEP AND EXTEND SEMANTIC BRIDGE

Problem identity / revision / feedback / reopen / confirmation.

## Resolution Compiler — DO NOT BUILD AS BRAIN

Có thể tồn tại như future conceptual policy layer chỉ sau outcome data đủ mạnh.

## Problem Algebra — RESEARCH LENS

Giữ insight normalize/preserve invariants; không xây FSM/operator DSL.

## Model Routing — SECONDARY OPTIMIZATION

Evaluate bằng:

```text
cost per Trusted Problem Resolution
```

## Multi-agent — EARN PARALLELISM

Không fan-out trước khi frame/contract/shared invariants đủ settled.

> **Framing before fanout. Evidence before scale.**

---

# 31. Standing principles — Revision 4 constitution

1. **Accepted is not Resolved.**
2. **User observation is not automatically the problem boundary.**
3. **Problem Revision is the stable user-level contract; RUN/WAVE is execution provenance.**
4. **Problem Frame is a hypothesis and may change without revising the user contract.**
5. **A* is the Minimal Sufficient Problem Boundary, not the root cause.**
6. **Governing Invariant and Causal Hypothesis are distinct from A*.**
7. **User has authority over desired outcome/business meaning; causal diagnosis remains evidence-driven.**
8. **Problem scope expands only when current model fails to explain evidence.**
9. **Every material wider frame needs evidence and a falsifier.**
10. **Think broad enough; intervene narrowly enough; prove proportionately.**
11. **Oracle must match the abstraction level of the claim.**
12. **Diagnostic observations should change a plausible next decision.**
13. **Material counterevidence must update the frame before same-frame semantic retry.**
14. **Wrong initial hypothesis is acceptable; ignoring counterevidence is avoidable decision debt.**
15. **One problem may require multiple causal mechanisms/interventions; do not force a single root cause.**
16. **Technical proof remains valid for the exact claim/fingerprint it proved even if the problem reopens.**
17. **Proof-derived quality is not independent user-outcome evidence.**
18. **Technical acceptance may only provisionally resolve a user problem.**
19. **Trusted Resolution is bounded by a Resolution Envelope.**
20. **False Closure is an outcome; failure dimensions explain why it happened.**
21. **Necessary governance cost and avoidable control friction must be separated.**
22. **History is reusable only with applicability conditions and current-evidence checks.**
23. **Case memory stores evidence/counterevidence/frame evolution, not private reasoning transcript.**
24. **No new architecture without measured bottleneck and clear TTPR contribution.**
25. **Stop when the bounded trusted claim is sufficiently defended and a credible falsifier does not reveal contradiction.**
26. **Model, router, cache, server and worker topology are subordinate optimizations.**

---

# 32. Strategic target architecture — logical, not service decomposition

```text
┌───────────────────────────────────────┐
│ PROBLEM / OUTCOME GOVERNANCE          │
│                                       │
│ User Job                              │
│ Problem Revision                      │
│ Desired Outcome                       │
│ Constraints / Contract                │
│ Resolution Envelope                   │
│ User feedback / confirmation          │
└─────────────────┬─────────────────────┘
                  │
┌─────────────────▼─────────────────────┐
│ PROBLEM FRAME / CAUSAL DECISION       │
│                                       │
│ Observation A                         │
│ Boundary A*                           │
│ Governing Invariants G                │
│ Ownership                             │
│ Causal Hypotheses H                   │
│ Oracle Preflight                      │
│ Decision Delta                        │
│ Counterevidence / Frame Update        │
└─────────────────┬─────────────────────┘
                  │
┌─────────────────▼─────────────────────┐
│ EOCL EXECUTION / EVIDENCE             │
│                                       │
│ Workspace / Source / Authority        │
│ RUN / WAVE / Lease                    │
│ Mutation                              │
│ Technical Proof / Checkpoint          │
└─────────────────┬─────────────────────┘
                  │
                  ▼
           OBSERVED NEW STATE
                  │
                  └──── feedback ─────► problem/frame
```

Ba logical planes **không đồng nghĩa ba services**.

---

# 33. Strategic direction

Dự án không còn được định nghĩa là:

```text
“AI coding orchestrator”
```

Mục tiêu chính xác hơn:

> **Closed-Loop Trusted Problem Resolution System:** hệ thống giữ ổn định user outcome contract, liên tục ước lượng actual system state, duy trì problem frame như hypothesis có thể sửa, dùng discriminator có khả năng thay đổi quyết định, thực thi intervention nhỏ nhất dưới authority/proof của EOCL, và chỉ kết thúc khi Resolution Envelope được chứng minh mà không còn material contradiction chưa giải thích.

Bản chất bên trong:

```text
Evidence-Governed Problem Convergence
```

Không phải convergence của mọi thứ trong dự án, mà là **convergence của các relevant alignment domains trong bounded problem envelope**.

---

# 34. Moat dài hạn

Nếu moat chỉ là:

```text
model routing
multi-agent
cache
server compute
```

nó dễ bị commoditize.

Moat có giá trị hơn:

> **Một evidence-grounded Resolution Case system biết từ lịch sử real problems: boundary nào từng bị underframe, invariant/ownership nào bị phá, truth domain nào thường diverge, counterevidence nào đáng lẽ phải đổi frame, discriminator nào giảm rework, intervention nào thực sự làm outcome converge, và case đó áp dụng trong điều kiện nào.**

Model mới trở thành executor/reasoner tốt hơn bên trong cùng resolution discipline.

---

# 35. Immediate implementation backlog

## P0 — Documentation/doctrine

- [x] hợp nhất Revision 4 methodology;
- [ ] cập nhật master strategy/reference docs để tránh doctrine cũ mâu thuẫn;
- [x] ghi rõ `A* boundary ≠ G ≠ H` trong terminology;
- [x] chuẩn hóa Trusted Resolution / Provisional Resolution semantics.

## P1 — PRL semantic bridge

- [x] technical acceptance → provisional resolution support;
- [x] same-contract explicit feedback → reopen same revision;
- [x] contract revision only on user-level contract change;
- [x] preserve technical proof on reopen;
- [x] explicit outcome evidence provenance.

## P2 — Shadow frame packet

- [x] frame id/revision;
- [x] A* boundary;
- [x] G invariants;
- [x] ownership;
- [x] H hypotheses;
- [x] counterevidence;
- [x] Decision Delta result;
- [x] falsifier;
- [x] no authority side effects.

## P3 — Resolution Claim / Envelope

- [x] direct outcomes;
- [x] relevant invariants;
- [x] relevant truth domains;
- [x] representative adjacent risks;
- [x] excluded scope;
- [x] required evidence;
- [x] closure falsification probe.

## P4 — History backfill/calibration

- [ ] 5–10 Golden HR Resolution Cases;
- [ ] map Problem Revision → Frames → RUN/WAVE;
- [ ] classify failure dimensions;
- [ ] compute framing regret qualitatively then quantitatively;
- [ ] separate necessary governance vs avoidable friction.

## P5 — Metrics

- [x] TTPR;
- [x] First-Pass Trusted Resolution;
- [x] False Closure;
- [x] Frame Revisions / Problem;
- [ ] Framing Regret;
- [x] Decision Delta Shadow Attestation Rate — DESCRIPTIVE / SHADOW-ATTESTED;
- [x] Resolution Envelope Evidence Attestation Coverage — DESCRIPTIVE / ATTESTED / NOT INDEPENDENT CONFIRMATION;
- [x] Multi-Primary-Run Revision Rate — DESCRIPTIVE PROXY;
- [ ] True Sibling Recurrence — OPEN / NOT CONVERGED;
- [ ] Independent Outcome Evidence Coverage — OPEN / NOT CONVERGED;
- [x] control-friction decomposition.

## P6 — Prospective protocol

- [x] shadow Decision Delta Test — DONE DESCRIPTIVE / SHADOW-ATTESTED;
- [ ] counterevidence frame-update advisory;
- [x] closure falsification gate for bounded full-problem claims — ATTESTED GATE IMPLEMENTED;
- [ ] compare methodology treatment with current workflow keeping model/route constant.

## P7 — Promote/remove

- [ ] promote only micro-policies with material TTPR/rework benefit;
- [ ] remove fields/policies that create ceremony without measurable benefit;
- [ ] do not create new subsystem unless proven necessary.

---

# 36. Definition of Done cho giai đoạn phương pháp luận

Không cần đợi “AI tự học hoàn hảo”. Giai đoạn Revision 4 được đánh giá theo
từng gate; không dùng một PASS tổng để che mất các gate chưa có evidence.

```text
1. **SOURCE DONE / FOCUSED PROOF DONE —** Problem Revision và technical RUN được tách rõ trong source semantics.
2. **SOURCE DONE / FOCUSED PROOF DONE —** Technical acceptance không thể tự claim Trusted Resolution.
3. **SOURCE DONE / FOCUSED PROOF DONE —** Same-contract user correction reopen được cùng problem.
4. **SOURCE DONE / FOCUSED PROOF DONE —** Frame change không tạo revision mới khi contract không đổi.
5. **SOURCE DONE / FOCUSED PROOF DONE / SHADOW ONLY —** A*/G/H separation tồn tại trong bounded working/shadow state.
6. **SOURCE DONE / FOCUSED PROOF DONE / OPEN / NOT CONVERGED —** Resolution Envelope path đã có
   và có fixture/integration proof; representative real-case receipt vẫn cần.
7. **SOURCE DONE / FOCUSED PROOF DONE —** Outcome/oracle provenance không circular ở claim boundary.
8. **SHADOW ONLY —** counterevidence được lưu trong frame packet; automatic
   frame-update-before-retry chưa được hard gate.
9. **DESCRIPTIVE DONE / CAUSAL EFFICACY UNKNOWN —** TTPR/problem-level metrics
   có denominator hợp lệ trên immutable snapshot; chưa phải efficacy evidence.
10. **SOURCE DONE / FOCUSED PROOF DONE —** Không thêm architecture/service/tool mới cho Revision 4 path.
```

---

# 37. Final methodological proposition

> **Coding Tools phải giữ ổn định contract về công việc và outcome mà người dùng cần, nhưng coi cách hệ thống hiểu problem là một hypothesis có thể thay đổi. Với mỗi Problem Revision, hệ thống phải xác định Minimal Sufficient Problem Boundary A*, tách Governing Invariants G khỏi Causal Hypotheses H, so sánh normative contract với observed state, chỉ ưu tiên observations có khả năng thay đổi quyết định, cập nhật frame khi counterevidence xuất hiện, thực thi intervention causal nhỏ nhất dưới EOCL, và chỉ claim Trusted Problem Resolution trong một Resolution Envelope hữu hạn sau khi outcome, invariant và relevant source/runtime/data evidence đủ mạnh và một credible falsification probe không tìm thấy contradiction chưa giải thích.**

Phiên bản ngắn:

> **Keep the outcome contract stable. Keep the problem model revisable. Act on decision-changing evidence. Close only a bounded claim you can defend and try to falsify.**

Phiên bản vận hành:

```text
CONTRACT
→ FRAME
→ ORACLE
→ CONTRADICTION
→ DISCRIMINATE
→ UPDATE FRAME
→ INTERVENE
→ EOCL PROVE
→ ENVELOPE VERIFY
→ FALSIFY CLOSURE
→ TRUSTED RESOLVE
```

---

# 38. Status

```text
METHODOLOGY SYNTHESIS: REVISION 4 COMPLETE
CODEX-WEB HISTORICAL EVIDENCE: INTEGRATED
HR .CODING-TOOLS EVIDENCE: INTEGRATED
CROSS-PROJECT STRATEGIC ANALYSIS: INTEGRATED
A* DEFINITION: REFINED TO MINIMAL SUFFICIENT PROBLEM BOUNDARY
A* / G / H SEPARATION: INTEGRATED
CLOSED-LOOP CONTRACT/STATE/CAUSAL MODEL: INTEGRATED
FIVE RESOLUTION ALIGNMENT DOMAINS: INTEGRATED
OWNERSHIP / ASSURANCE AXES: INTEGRATED
DECISION DELTA TEST: INTEGRATED
COUNTEREVIDENCE-DRIVEN FRAME UPDATE: INTEGRATED
RESOLUTION ENVELOPE: INTEGRATED
CLOSURE FALSIFICATION PROBE: INTEGRATED
FAILURE DIMENSIONS / FALSE-CLOSURE OUTCOME: INTEGRATED
CASE MEMORY WITH APPLICABILITY: INTEGRATED
IMPLEMENTATION PLAN: DEFINED
APPLY-NOW DOCTRINE: DEFINED
SHADOW/CALIBRATION AREAS: DEFINED
DO-NOT-BUILD BOUNDARIES: DEFINED
CLAIM OF PROVEN BREAKTHROUGH: NOT YET
STRATEGIC DIRECTION: CLOSED-LOOP TRUSTED PROBLEM RESOLUTION
```

## 38.1. Implementation checkpoint — 2026-08-26

Đã hoàn thiện và kiểm chứng trong checkout này:

```text
P0 doctrine terminology/semantics                 SOURCE DONE
P1 PRL semantic bridge                            SOURCE DONE / FOCUSED PROOF DONE
P2 bounded Problem Frame packet                   SOURCE DONE / FOCUSED PROOF DONE / SHADOW ONLY
P3 Resolution Claim + Envelope                    SOURCE DONE / FOCUSED PROOF DONE
P3 independent outcome receipt binding            OPEN / NOT CONVERGED
P4 Golden HR backfill/calibration                  OPEN / NOT CONVERGED
P5 descriptive problem-revision metrics           DESCRIPTIVE DONE / schema v3
P5 causal efficacy                                UNKNOWN
P6 Decision Delta                                 DONE DESCRIPTIVE / SHADOW-ATTESTED
P6 closure falsifier                              ATTESTED GATE IMPLEMENTED
P6 controlled methodology comparison              OPEN / NOT CONVERGED
P7 micro-policy promotion/removal                 OPEN / NOT CONVERGED
```

Changed implementation surfaces:

```text
resources/coding-tools-mcp/coding_tools_mcp/resolution_contract.py
resources/coding-tools-mcp/coding_tools_mcp/problem_lineage.py
resources/coding-tools-mcp/coding_tools_mcp/problem_lineage_control.py
resources/coding-tools-mcp/coding_tools_mcp/workflow_tools.py
resources/coding-tools-mcp/coding_tools_mcp/coordination.py
resources/coding-tools-mcp/coding_tools_mcp/problem_resolution_economics.py
resources/coding-tools-mcp/coding_tools_mcp/tool_schema.py
resources/coding-tools-mcp/tests/test_resolution_contract.py
resources/coding-tools-mcp/tests/test_problem_lineage.py
resources/coding-tools-mcp/tests/test_problem_resolution_economics.py
resources/coding-tools-mcp/tests/test_problem_lineage_canary.py
resources/coding-tools-mcp/tests/test_efficiency_runtime.py
```

Focused validation đã chạy:

```text
python -m pytest tests/test_resolution_contract.py \
  tests/test_problem_lineage.py \
  tests/test_problem_resolution_economics.py \
  tests/test_problem_lineage_canary.py \
  tests/test_problem_lineage_activation.py \
  tests/test_mcp_sdk_smoke.py -q
→ 35 passed, 7 subtests passed

Regression mới xác nhận `PRL_FRAME_INVALID` khôi phục pending host-turn và
không tạo RUN khi shadow frame cố mang authority side effect. Privacy regression
cũng xác nhận frame/envelope text từ chối credential/PII được percent-encode,
escaped ASCII, base64 hoặc hex dưới depth/variant/decoded-byte budgets cố định.

python -m compileall -q coding_tools_mcp
→ PASS

python scripts/check_module_size.py
→ BLOCKED: server.py 3541 lines > budget 3500
  (concurrent integration surface; không tăng budget và không sửa chồng)

git diff --check -- <Revision-4 changed paths>
→ PASS; chỉ có cảnh báo Git về chuyển đổi LF/CRLF
```

Full component suite cũng đã được chạy để phát hiện scope interaction:

```text
python -m pytest tests/ -q
→ 665 passed, 4 skipped, 87 subtests passed, 6 failed
```

Đây là receipt của exact worktree snapshot tại lúc lệnh bắt đầu. Sau lệnh này,
một concurrent wave đã thêm thay đổi riêng ở Electron/runtime transport,
`server.py`, `tool_contract.py`, `mcp_http_handler.py` và test tương ứng trong
khi HEAD vẫn giữ `52faa0e9cfacf582fcf5bc6f40ed230cea7602e9`. Revision 4 focused suite được
chạy lại sau semantic/privacy convergence và đạt `35 passed, 7 subtests passed`;
không dùng full suite receipt cũ để claim toàn worktree hiện tại xanh. Post-drift `compileall`
và Revision-4 `diff --check` vẫn PASS; module-size guard hiện bị concurrent
`server.py` chặn ở `3541 > 3500`, còn `coordination.py` đã được giữ trong budget.

Sáu failure còn lại không đi qua Revision 4 focused surface:

```text
1 x performance trace hourly aggregation
    expected tool_calls=2, observed 1
    performance_trace implementation không bị thay đổi trong wave này

5 x ordinary mutation-bearing acceptance fixtures
    fail-closed tại ACCEPTANCE_PROOF_REQUIRED
    thuộc bề mặt acceptance-file/attestation đang có concurrent dirty changes
```

Các failure đó được giữ nguyên để tránh ghi đè công việc đồng thời; focused
Revision 4/PRL contract, envelope reconciliation, canary, descriptive reporter
và public-schema smoke đều xanh. Post-drift targeted check của concurrent
contract-compatibility surface đạt `1 passed, 1 failed`: `tools/call` contact
receipt PASS, còn assertion cũ `compatible_predecessor_sha256` vắng mặt đã
stale sau khi concurrent code thêm field này. Bề mặt đó không được sửa trong
Revision 4 wave.

Reporter regression hiện cover trực tiếp First-Pass Trusted Resolution, False
Closure, frame revisions, Decision Delta shadow attestation, Resolution Envelope
evidence attestation coverage, Multi-Primary-Run Revision Rate và typed control
friction. Logic First-Pass cũng đã được sửa để một Revision bị `REOPEN` sau
confirmation không còn bị đếm nhầm là first-pass trusted. Diagnostic
frame/friction/multi-RUN counts dùng mọi exact primary linked RUN của Revision,
không bỏ sót attempt chỉ vì RUN đó chưa claim `full_problem`; envelope
attestation coverage vẫn chỉ xuất hiện trên full-problem claim. Nó không
receipt-bound và không phải independent user-outcome confirmation.

Resolution Contract privacy boundary hiện có parity thực với capsule scanner:
NFKC normalization, format-character folding và syntax-triggered bounded decode
cho percent encoding, escaped ASCII, base64-like token và hex. Scanner không
đoán entropy, giới hạn depth/variant/decoded bytes và có focused regression cho
cả bốn encoding; vì vậy claim này áp dụng trực tiếp cho frame/envelope mới,
không còn vay proof từ scanner của contract capsule cũ.

Các dòng `DONE` ở đây chỉ là source/focused-test evidence. Chúng không phải
loaded-runtime activation, natural HR cohort, causal efficacy, production
promotion hay release proof. `Framing Regret`, independent user-outcome
confirmation, counterevidence-driven automatic frame update và treatment-vs-
control comparison vẫn để mở cho calibration/prospective evidence.

## 38.2. Convergence checkpoint — source đã hội tụ, real client chưa hội tụ

Source schema và focused proof hiện xác nhận đủ bốn public arguments cần cho
Revision 4:

```text
agent_workflow.problem_context
task_control.problem_resolution_envelope
task_control.problem_coverage_manifest
task_control.problem_criterion_dispositions
```

Exact source contract SHA-256 là
`57ed56a4f008287d9d9fdef035fa248f91cce4d58e935280b28963e4126a8053`.
Đây là source/contract identity, không tự chứng minh wrapper của ChatGPT/Coding-VP
đã chạy `tools/list` hoặc `server/discover` cho current process.

Fresh read-only receipt từ official `RecoveryIpcClient` tại
`2026-08-26T07:08:08.287Z` cho đúng `E:\DEV\Codex-web` báo:

```text
Recovery Host/runtime ready                            TRUE
Coding MCP running revision                           15c63084...d47b5ec
Coding MCP disk revision                              5cb4aefd...df219d4
Coding MCP source update pending                      TRUE
current tool-contract SHA                             57ed56a4...a8053
connector state                                       CHANGED_NEEDS_DISCOVERY
connector_rediscovered                                FALSE
connector_rediscovered_at                             NULL
connector_refresh_required                            TRUE
acknowledged contract SHA                             34cbb4c3...d409c
closure_state                                         LIFECYCLE_NOT_QUIESCENT
release_state                                         NOT_RELEASED
production_state                                      NOT_CLAIMED
```

Sau đó Recovery Host quan sát một concurrent runtime transition không do wave
này yêu cầu hay thực hiện. Fresh full snapshot tại `2026-08-26T07:14:26.160Z`
xác nhận:

```text
Coding MCP running revision == disk revision          5cb4aefd...df219d4
Coding MCP source update pending                      FALSE
runtime running / fully ready                         TRUE / TRUE
tool profile / contract SHA                           smart-v3 / 57ed56a4...a8053
connector state                                       CHANGED_NEEDS_DISCOVERY
connector_rediscovered                                FALSE
connector_rediscovered_at                             NULL
connector_refresh_required                            TRUE
closure_state / lifecycle_clean                       LIFECYCLE_NOT_QUIESCENT / FALSE
release_state / production_state                      NOT_RELEASED / NOT_CLAIMED
```

Receipt sau mạnh hơn cho loaded-component revision nhưng vẫn không phải EOCL
source acceptance hay real-client discovery. Không có restart hoặc connector
acknowledgement nào được thực hiện bởi Revision 4 wave này.

Fresh immutable lifecycle census tiếp theo tại
`2026-08-26T07:09:24.321Z` dùng query-only Backup API, có SQLite integrity `ok`,
zero foreign-key violations và `mutated_canonical_ledger=false`. Census không có
`LIVE_OWNED`, projection drift, unexplained active RUN, unbound live resource hay
managed job; đồng thời còn `3 AWAITING_ACCEPTANCE`, `1 GRACE_PERIOD_INACTIVE`,
`53 THRESHOLD_SENSITIVE_STALE_CANDIDATE` và `6 P5_EXPERIMENT_ANCHOR`. Các row đó
không bị terminalize, force-release hoặc sửa trực tiếp để làm sạch báo cáo.

Evidence-plane verdict:

```text
Source arguments                                     SOURCE DONE
Focused source/schema proof                          FOCUSED PROOF DONE
Loaded component revision                            CURRENT / RECOVERY HOST RECEIPT
EOCL source acceptance + lifecycle clean             OPEN / NOT CONVERGED
Real ChatGPT/Coding-VP discovery receipt             OPEN / NOT CONVERGED
Connector acknowledgement                           NOT PERFORMED
Bounded real-client Revision 4 canary                NOT RUN — GATE CLOSED
Natural HR case                                      NOT RUN — GATE CLOSED
Independent outcome receipt binding                  OPEN / NOT CONVERGED
Causal efficacy                                      UNKNOWN
```

Exact next action không phải một generic `tools/call` và cũng không phải restart
lại component đang current: concurrent source/accepted checkpoint/lifecycle cần
hội tụ qua supported authority, rồi client ChatGPT/Coding-VP thật phải
reconnect/refresh để tạo current-process discovery receipt. Chỉ khi fresh
official receipt có đồng thời `connector_rediscovered=true`, timestamp không rỗng
và `connector_refresh_required=false` mới được dùng official acknowledgement và
chạy bounded canary. Phiên Codex này không expose Coding-VP arguments đó, nên
không fabricate canary, confirmation hoặc natural HR workload.

## 38.3. Fresh convergence receipt — loaded Coding MCP current, closure authority vẫn thiếu

Section 38.2 giữ nguyên như chronology của các receipt trước. Checkpoint này
chỉ append evidence read-only mới hơn; không terminalize RUN, không force-release
lease, không sửa trực tiếp `ledger.sqlite3`, không restart runtime và không
acknowledge connector.

Official `RecoveryIpcClient.runtime.snapshot` cho đúng workspace tại
`2026-08-26T07:27:14.222Z` xác nhận:

```text
Coding MCP runtime running / fully ready              TRUE / TRUE
busy / recovering                                     FALSE / FALSE
Coding MCP running revision == disk revision          5cb4aefd...df219d4
Coding MCP update pending                             FALSE
tool profile / contract SHA                           smart-v3 / 57ed56a4...a8053
connector state                                       CHANGED_NEEDS_DISCOVERY
connector_rediscovered / rediscovered_at              FALSE / NULL
connector_refresh_required                            TRUE
acknowledged contract SHA                             34cbb4c3...d409c
closure state / lifecycle clean                       LIFECYCLE_NOT_QUIESCENT / FALSE
release state / production state                      NOT_RELEASED / NOT_CLAIMED
```

Do đó kết luận `source → loaded Coding MCP` là current cho exact component
revision trên. Nó **không** nâng verdict lên real-client discovery: only a real
ChatGPT/Coding-VP `tools/list` hoặc `server/discover` current-process receipt
có thể thay `connector_rediscovered` thành evidence. Snapshot cũng báo Recovery
Host component riêng đang `update_pending`; vì vậy `components_current=false`
ở outer closure plane. Đây là một blocker integration riêng, không phải lý do
để phủ nhận revision Coding MCP đã load.

Gate-0 lifecycle census read-only tiếp theo tại
`2026-08-26T07:26:34.867Z` dùng immutable Backup API / query-only snapshot:

```text
ledger schema version                                 11
physical / logical snapshot SHA                       f434af6e...80ee3ca / 27f7f182...1471ba
SQLite integrity / foreign-key rows                   ok / 0
mutated_canonical_ledger                              FALSE
LIVE_OWNED / unexplained active RUN                   0 / 0
projection drift / unbound resource / managed job     FALSE / 0 / none
AWAITING_ACCEPTANCE                                   3
THRESHOLD_SENSITIVE_STALE_CANDIDATE                   54
P5_EXPERIMENT_ANCHOR                                  6
```

Từ census `07:09`, `GRACE_PERIOD_INACTIVE=1` đã qua ngưỡng thời gian và được
classify vào `THRESHOLD_SENSITIVE_STALE_CANDIDATE=54`. Đây là một thay đổi
classification do clock trong snapshot, **không** phải reconciliation hay
terminalization.

Ba RUN `AWAITING_ACCEPTANCE` vẫn là:

```text
0ca7f60e56544df9aadb9fb89f7df48f
9489bcc986594ae998b247a39fd9007a
d0900c558b4b4c67a7e13acb8f443d26
```

Chúng là acceptance work có nội dung/source proof cũ, không phải junk để xóa.
Chỉ ChatWeb controller hiện hành với supported `task_control` contract mới có
thể accept/reject/stop từng RUN theo authority semantics; do đó không dùng
direct SQL, bypass lease hay bulk cleanup để làm ledger nhìn sạch hơn.

Read-only exact-ID preflight tại `07:27Z` vẫn trả tất cả năm candidate dưới đây
là `active`, `THRESHOLD_SENSITIVE_STALE_CANDIDATE`, `has_live_ownership=false`
và `already_reconciled=false`:

```text
43bd318fb14d4c0d8adbd89c83c65b1a
63ea32856aca4f5a8333b71253d8d386
d6920717c87f4a358ef871406e46f8f1
fc64964db0e64f8690c2a410be70b841
fcd5714546e341b4b14181438b1b1afa
```

Canonical ledger changed while those five serial read-only preflights were
running, nên chúng không còn chia sẻ một immutable physical/logical digest để
thực hiện batch mutation. Đây là đúng fail-closed behavior. Một reconciliation
chỉ được cân nhắc **sau** một stopped-runtime receipt, fresh exact snapshot
digest và explicit operator authority; nó phải đi từng RUN bằng supported CLI,
không bulk-clean và không sử dụng các digest cũ trong tài liệu này.

### 38.4. Status chuyển pha và thứ tự closure bắt buộc

```text
REVISION 4 CORE SOURCE + FOCUSED PROOF                COMPLETE
LOADED CODING MCP                                     CURRENT
REAL CLIENT DISCOVERY                                 BLOCKED
LIFECYCLE CLEAN IMMUTABLE BASELINE                    NOT CONVERGED
BOUNDED REVISION 4 CANARY                             NOT AUTHORIZED / NOT RUN
NATURAL HR OUTCOME CASE                               NOT AUTHORIZED / NOT RUN
INDEPENDENT OUTCOME RECEIPT + CAUSAL EFFICACY         OPEN / UNKNOWN
INTEGRATED DELIVERY / RELEASE / PRODUCTION            NOT READY
```

Pha tiếp theo có tên chính xác là **Revision 4 Convergence & Natural Resolution
Proof**, không phải một P8 feature/architecture wave. Trình tự không được đảo:

1. Reconcile lifecycle/concurrent work bằng exact owner/authority; mỗi stale
   RUN chỉ được xử lý một-ID-một-lần sau fresh stopped-runtime snapshot nếu có
   user authorization rõ ràng. Ba acceptance RUN cần real current controller,
   không áp quy trình stale-run vào chúng.
2. Để real ChatGPT/Coding-VP chạy `tools/list` hoặc `server/discover`, rồi đọc
   lại Recovery Host cho đến khi đồng thời có
   `connector_rediscovered=true`, timestamp không rỗng và
   `connector_refresh_required=false`.
3. Chỉ sau receipt ở bước 2 mới xem xét official connector acknowledgement và
   chạy đúng một bounded Revision 4 canary bằng public schema hiện hành.
4. Chỉ sau canary mới chạy một natural HR case có authority/outcome thật, bind
   evidence receipt độc lập, rồi mới đo causal efficacy và cân nhắc integration,
   delivery, commit, release hay production.

**Revision 4 core implementation kết thúc ở đây; closure end-to-end vẫn bị
chặn bởi lifecycle authority, current-process client discovery và natural
outcome evidence.**

## 38.5. Lifecycle reconciliation wave — exact stale rows đã đóng, connector vẫn mở

Checkpoint này ghi nhận mutation có authority sau chỉ thị tiếp tục đến mục tiêu.
Trước mutation, official Recovery Host snapshot và Gate-0 census xác nhận đúng
workspace `E:\DEV\Codex-web`, không có managed job, unexplained RUN, projection
drift hoặc unbound live resource. Một concurrent ChatWeb RUN còn controller
lease đã được chờ cho tới khi lease tự giải phóng; runtime không bị dừng khi
`LIVE_OWNED=1`.

Concurrent ChatWeb wave đã sửa MCP-2026 exact-run continuation bằng cách thêm
`stop` vào `TASK_CONTROL_CONTINUATION_ACTIONS`, để
`task_control(action="stop", run_id=...)` khôi phục durable stateless context
thay vì mint context mới. Canonical ledger-generated report xác nhận:

```text
RUN / WAVE                                            8cfd89b6...2327f8 / debb483b...ef8d10
state transition                                     ACCEPTING → CHECKPOINTED
canonical checkpoint                                 e513d927cde245aa9443d23cceb49664
proof stage                                           verify:tests PASS
accepted by                                           chatweb
audit hash chain                                      valid
```

Focused local reproduction độc lập cho exact regression cũng đạt:

```text
python -m pytest \
  tests/test_stateless_http_2026.py::StatelessHttp2026Tests::\
  test_task_control_stop_recovers_exact_run_context_when_connector_omits_handle -q
→ 1 passed
```

Sau khi `LIVE_OWNED=0`, Recovery Host chính thức dừng Coding MCP và tunnel;
postflight xác nhận `runtimeRunning=false`, `fullyReady=false`, `busy=false`,
`manuallyStopped=true` trong khi Recovery Host vẫn healthy. Năm exact stale RUN
sau đó được xử lý **một ID một lần**, mỗi lần bằng fresh physical/logical digest,
`--runtime-stopped` authority và supported CLI:

```text
43bd318fb14d4c0d8adbd89c83c65b1a    active → stale
63ea32856aca4f5a8333b71253d8d386    active → stale
d6920717c87f4a358ef871406e46f8f1    active → stale
fc64964db0e64f8690c2a410be70b841    active → stale
fcd5714546e341b4b14181438b1b1afa    active → stale
```

Tất cả năm receipt đều có `changed=true`, `idempotent=false`, `chain_ok=true`,
SQLite integrity `ok`, zero foreign-key violations và postflight target
`RECONCILED_STALE`. Không dùng bulk reconciliation, force-release, direct SQL
hay digest của ID trước cho ID sau.

Postflight immutable census tại `2026-08-26T07:43:05.940Z` xác nhận:

```text
active rows thuộc năm target                           0
ordinary active RUN                                   54
AWAITING_ACCEPTANCE                                   3
THRESHOLD_SENSITIVE_STALE_CANDIDATE                   50
GRACE_PERIOD_INACTIVE                                 1
P5_EXPERIMENT_ANCHOR                                  6
LIVE_OWNED / unexplained / unbound / managed job      0 / 0 / 0 / 0
projection drift                                      FALSE
physical / logical snapshot SHA                       4a6c7cd9...af4a8de / ad9aad28...51cf2f
```

Fresh census tiếp theo phân loại cả `50` remaining threshold candidates là
`below_current_stale_threshold`; `eligible_stale_count=0`. Vì vậy chúng không
được đưa qua stale reconciliation chỉ để ép lifecycle clean.

Recovery Host đã khởi động lại runtime thành công. Snapshot tại
`2026-08-26T07:44:59.439Z` xác nhận loaded state mới:

```text
Coding MCP running / fully ready                      TRUE / TRUE
running revision == disk revision                     c35ccf65...ff7b0b
update pending                                        FALSE
tool profile / contract SHA                           smart-v3 / 57ed56a4...a8053
connector state                                       CHANGED_NEEDS_DISCOVERY
connector_rediscovered / rediscovered_at              FALSE / NULL
connector_refresh_required                            TRUE
```

Reload conversation ChatGPT/Coding-VP không tự tạo discovery receipt. Điều này
giữ nguyên gate: cần một turn của real client thực sự gọi `tools/list` hoặc
`server/discover`; một page reload, persisted plugin state hay `tools/call`
không đủ. Ba RUN `AWAITING_ACCEPTANCE` cũng chưa bị stop/accept/reject trong
checkpoint này vì thao tác đó phải đến từ current ChatWeb controller sau khi
client contract đã refresh.

```text
EXACT STALE RECONCILIATION                             DONE (5/5 eligible IDs)
EXACT-RUN STOP CONTINUATION FIX                        SOURCE + FOCUSED PROOF + CHECKPOINTED
LOADED RUNTIME WITH FIX                               CURRENT
REMAINING STALE-ELIGIBLE IDS                          0
AWAITING_ACCEPTANCE TERMINALIZATION                   OPEN tại snapshot này; SUPERSEDED bởi §38.11
REAL CLIENT DISCOVERY / CONNECTOR ACK                 OPEN / NOT CONVERGED
REVISION 4 CANARY / NATURAL HR OUTCOME                NOT RUN
```

## 38.6. Module-size closure và fresh post-wave snapshot

Sau khi wave read-only `f861ce694cfd4cf192224cc084771f89` kết thúc với
checkpoint canonical `8d2ffc76cd8d455f88f589ed5d837f32`, phần source hygiene còn
lại đã được xử lý mà không mở thêm taxonomy hay public tool. Hai phương thức
contact-only (`_record_client_contact`, `connector_client_contact`) được chuyển
từ `server.py` sang `runtime_activity.py`, đúng ownership của activity/connector
contact. `Runtime` vẫn kế thừa mixin nên public namespace và hành vi không đổi;
không thêm tool thứ chín và không thay đổi `smart-v3` allowlist.

Proof tại source snapshot hiện hành:

```text
server.py                                             3494 lines (budget 3500)
runtime_activity.py                                   151 lines (budget 1600)
python scripts/check_module_size.py                   PASS
python -m compileall -q coding_tools_mcp              PASS
git diff --check                                      PASS
affected Revision-4/MCP suite                        72 passed, 1 skipped, 13 subtests
Electron runtime-lifecycle suite                     45 passed
```

Đây là refactor để đóng guard module-size, không phải bằng chứng riêng cho
connector discovery hay user outcome. Không có commit, push, tag, publish,
release, deploy hoặc production operation nào được thực hiện.

Official Recovery Host snapshot lúc `2026-08-26T08:02:54.154Z` xác nhận đúng
installation và UI hiện hành; Coding MCP/Tunnel `fully_ready=true`,
`running_revision == disk_revision ==
50bb087bfd0a78416cf30b00f0a86ac0e7ce229e6e04f6ab4693ca1f18789eda`, nhưng
`activationClosure.connector_contract_state=UNAVAILABLE` nên snapshot này không
được dùng để suy ra current-process `tools/list`/`server/discover`. Recovery Host
riêng vẫn có `update_pending=true` (`running_revision=940a7e0c…`,
`disk_revision=5a66a7db…`); vì vậy host source chưa đạt trạng thái current và
không được tự nhận `LIVE_CLOSED`.

Gate-0 census content-free lúc `2026-08-26T08:02:57.7496376Z` không mutate
canonical ledger và không có managed job. Classification hiện hành là:

```text
AWAITING_ACCEPTANCE                         3
GRACE_PERIOD_INACTIVE                       2
THRESHOLD_SENSITIVE_STALE_CANDIDATE         51
P5_EXPERIMENT_ANCHOR                        6
LIVE_OWNED / active write fence             0 / 0
```

Ba RUN acceptance chưa đổi tại snapshot này (`0ca7f60e…`, `9489bcc…`,
`d0900c55…`), còn hai
`GRACE_PERIOD_INACTIVE` là các RUN mới nằm trong grace window; không terminalize
hay bulk-clean chỉ để làm census đẹp hơn. Wave `f861…` đã là RUN thứ tư được
ChatWeb accept từ read-only inspection, không thay thế ba acceptance RUN cũ.

Trạng thái sau checkpoint này:

```text
Revision-4 source + focused proof                 COMPLETE
server.py module-size gate                        COMPLETE
Loaded Coding MCP/Tunnel                          CURRENT / FULLY_READY
Recovery Host source                               UPDATE_PENDING
Real-client discovery + connector acknowledgement  OPEN / NOT CONVERGED
Three exact AWAITING_ACCEPTANCE RUNs               OPEN tại snapshot này; SUPERSEDED bởi §38.11
Bounded Revision-4 canary                         NOT RUN
Natural HR outcome + independent receipt           NOT RUN
Integrated delivery / release / production         NOT READY
```

Next action vẫn bị giới hạn bởi external authority: sau khi có xác nhận rõ ràng
cho hành động gửi follow-up tới đúng conversation Coding-VP, current client phải
refresh/reconnect và tạo receipt `tools/list` hoặc `server/discover`; chỉ khi
đồng thời có `connector_rediscovered=true`, timestamp hiện hành và
`connector_refresh_required=false` mới được ACK. Khi đó mới stop từng RUN cũ
bằng exact `task_control(stop)` và chạy bounded canary; không dùng proof cũ, không
bulk-clean 51 candidate dưới ngưỡng, và không tự tạo natural HR workload.

## 38.7. Post-quiescence diagnostic receipt — không phát sinh source mutation

Một post-quiescence diagnostic RUN mới
`74a9920ba5e748f2a4676e843ebe2339` đã được terminalize đúng là `ABORTED` lúc
`2026-08-26T08:06:07.693Z`. Mục tiêu của RUN chỉ là đọc `dev:status` để kiểm tra
auto-activation/handoff; wave bị ngắt bởi MCP process/server handoff trước command
receipt. Canonical report ghi rõ `source mutation did not occur`, không có
checkpoint và hash chain vẫn hợp lệ; không dùng RUN này làm bằng chứng connector
hay canary. Sau khi lease TTL tự giải phóng, `controller_leases` và
`write_fences` đều rỗng.

Gate-0 census content-free mới nhất lúc `2026-08-26T08:07:51.2478347Z` tiếp tục
xác nhận `mutated_canonical_ledger=false`, `managed_jobs=0`, không còn
`LIVE_OWNED`, `TERMINAL_PARENT_CONTRADICTION` hay `UNEXPLAINED_ACTIVE`. Clock đã
đưa thêm các row cũ qua classification, nên số liệu hiện tại là:

```text
AWAITING_ACCEPTANCE                         3
THRESHOLD_SENSITIVE_STALE_CANDIDATE         52
P5_EXPERIMENT_ANCHOR                        6
LIVE_OWNED / active write fence             0 / 0
```

Đây là thay đổi classification theo thời gian, không phải permission để
reconcile hoặc terminalize hàng loạt. Tại snapshot này, ba RUN acceptance exact
vẫn giữ nguyên và
chỉ current ChatWeb controller với refreshed contract mới được stop/accept/reject
từng RUN. Không có bằng chứng mới cho `tools/list`/`server/discover`, nên
connector acknowledgement, Revision-4 canary và natural HR outcome vẫn chưa được
phép đánh dấu hoàn tất.

## 38.8. Quiescence recheck — lease đã tự giải phóng, connector gate vẫn mở

Sau khi chờ TTL của RUN `167d23370d1e4c66bd64a1ae95a24012`, một immutable
Gate-0 census mới được đọc ở `2026-08-26T08:13:43Z`. Census xác nhận lease đã tự
giải phóng; không có mutation nào vào canonical ledger trong lần đọc này:

```text
AWAITING_ACCEPTANCE                         3
GRACE_PERIOD_INACTIVE                       1
THRESHOLD_SENSITIVE_STALE_CANDIDATE         52
P5_EXPERIMENT_ANCHOR                        6
LIVE_OWNED / controller lease               0 / 0
active write fence / managed job            0 / 0
unexplained active / unbound residue        0 / 0
projection drift / ledger mutation          FALSE / FALSE
ordinary active runs                        56
physical snapshot SHA                       29dda0d1f20af9d09125151b0a08a16ac630b40e8f1bf28f0dd6b72c6f61f3f6
logical snapshot SHA                         96444ed1968569970e5b76051e9d9f95da19bc1881ac565f3bee0b89b006a67d
```

RUN `167d…` hiện chỉ còn là `GRACE_PERIOD_INACTIVE` và không còn ownership; ba
RUN `AWAITING_ACCEPTANCE` exact (`0ca7…`, `9489…`, `d090…`) vẫn active ở trạng
thái `ACCEPTING` và chưa được tự ý stop/accept/reject tại snapshot này. Trạng
thái đó được terminalize hợp lệ sau đó và được correction tại §38.11. Các `52` threshold
candidates tiếp tục được giữ nguyên vì chưa vượt stale threshold; không bulk
reconcile hoặc direct SQL được dùng.

Official Recovery Host `runtime.lightweight_snapshot` tại
`2026-08-26T08:15:01.834Z` tiếp tục bind đúng workspace và source/runtime hiện
hành:

```text
workspace                                        E:\DEV\Codex-web
Coding MCP / Tunnel / fully_ready                TRUE / TRUE / TRUE
Coding MCP running == disk revision              TRUE / TRUE
Coding MCP revision                              50bb087b...18789eda
Recovery Host running revision                   940a7e0c...82bd37cc
Recovery Host disk revision                      5a66a7db...5c067e9
Recovery Host update_pending                     TRUE
activation closure                               valid, source_accepted=true
connector_contract_state                         UNAVAILABLE
connector_rediscovered / timestamp               NULL / NULL
connector_refresh_required                       NULL
lifecycle_decision / lifecycle_clean              NULL / FALSE
closure_state                                     LIFECYCLE_NOT_QUIESCENT
```

Điều này đóng phần **chờ lease/quiescence read-only**, nhưng không đóng
`LIVE_CLOSED`: Recovery Host code vẫn lệch source, và chưa có receipt current
process chứng minh ChatGPT/Coding-VP đã chạy `tools/list` hoặc `server/discover`.
Không có source mutation, commit, push, tag, publish, release, deploy hay
production operation nào trong checkpoint này; thay đổi duy nhất là ghi nhận
evidence vào Markdown.

Trạng thái sau recheck:

```text
Revision-4 source + focused proof                 COMPLETE
Lifecycle lease/quiescence recheck               COMPLETE (read-only)
Loaded Coding MCP/Tunnel                          CURRENT / FULLY_READY
Recovery Host source                               UPDATE_PENDING
Real-client discovery + connector acknowledgement  OPEN / NOT CONVERGED
Three exact AWAITING_ACCEPTANCE RUNs               OPEN tại snapshot này; SUPERSEDED bởi §38.11
Bounded Revision-4 canary                         NOT RUN
Natural HR outcome + independent receipt           NOT RUN
Integrated delivery / release / production         NOT READY
```

Exact next action vẫn là chờ **xác nhận rõ ràng của người dùng** trước khi gửi
follow-up tới đúng Coding-VP conversation. Follow-up đó phải yêu cầu current
client refresh/reconnect và tạo `tools/list`/`server/discover` receipt; chỉ khi
Recovery Host đồng thời báo `connector_rediscovered=true`, timestamp không rỗng
và `connector_refresh_required=false` mới được official acknowledgement. Sau
đó mới xử lý từng RUN acceptance bằng `task_control(stop)` và chạy bounded
Revision-4 canary. Không dùng proof cũ, không tạo synthetic natural HR case,
không bulk-clean threshold candidates.

## 38.9. Fresh C4/PRL read-only receipt — mechanics sẵn sàng, natural evidence bằng 0

Một lần chạy mới của
`python resources/coding-tools-mcp/scripts/report_problem_lineage_canary.py
--workspace .` đã hoàn tất trên immutable Backup-API snapshot tại
`2026-08-26T08:19:41.448Z`. Reporter không khởi tạo canonical writer, dùng đúng
một live backup connection và giữ nguyên query-only boundary. Receipt trả về:

```text
status                                           C4_SOURCE_READY_AWAITING_NATURAL_CANARY
schema_version                                  2 (PRL v11)
sqlite_integrity_check / FK violations          ok / 0
problem-chain invalid / revision invalid        0 / 0
current projection invalid                      0
observed current-v11 events                     3
exact revision binding                           0 / 3
criterion-to-proof structural coverage          0 / 0
authoritative confirmation                       0 / 0
attested occurrence clock                       0 / 0
natural evidence                                attested=false, count=null
```

Ba current-v11 events hiện có là các event mechanics/action chưa tạo thành
problem revision hoặc exact engineering-attempt binding. Reporter vẫn bảo toàn
nguyên tắc `natural_cohort_not_inferred=true`; không tự gán chúng thành natural,
không tạo denominator, không đọc raw problem/capsule content và không dùng
aggregate để suy ra false split/merge hay measurement reliability.

PRL-D descriptive economics report trên cùng canonical evidence tiếp tục trả về
`DESCRIPTIVE_ONLY`. Các đơn vị `problem_revision`, `TTOC`, `TTFP`, `TTPR`,
`RESOLUTION_INTERVAL_WIDTH`, trusted resolution và resolution-envelope
attestation đều chưa có quan sát hợp lệ; các tỷ lệ/p50/p90 tương ứng vẫn là
`null`, không phải zero. `multi_primary_run_revision_rate` cũng giữ đúng nghĩa
proxy mô tả multiple attempts, không được diễn giải thành sibling recurrence.

Do đó checkpoint này đóng thêm **C4 mechanics/read-only readiness**, không đóng
natural canary hay causal efficacy:

```text
Revision-4 source + focused proof                 COMPLETE
C4 integrity/mechanics receipt                    COMPLETE (source-ready)
Natural Revision-4 canary                         NOT RUN
Natural HR problem/revision                       NOT OBSERVED
Independent user/outcome confirmation             NOT OBSERVED
PRL-D descriptive resolution economics             DESCRIPTIVE_ONLY
Causal efficacy / P4/P5 promotion                 UNKNOWN / NOT AUTHORIZED
```

Không có source, runtime, task, RUN/WAVE, connector, workspace hay ledger
mutation nào trong lần chạy này. Không có synthetic problem, synthetic cohort,
manual backfill, C5 shadow, C6 treatment, commit, push, package, release,
deployment hoặc production operation.

Exact next action không đổi: chỉ sau khi người dùng xác nhận gửi follow-up tới
đúng Coding-VP conversation mới yêu cầu current client refresh/reconnect và
chạy `tools/list` hoặc `server/discover`. Sau receipt đồng thời
`connector_rediscovered=true`, timestamp khác rỗng và
`connector_refresh_required=false`, mới được official acknowledgement; sau đó
mới xử lý từng RUN acceptance, chạy bounded canary và chờ một natural HR case
có outcome thật. Không được dùng receipt mechanics này thay cho connector,
user confirmation hoặc independent outcome evidence.

## 38.10. Watchdog recurrence và Recovery Host fingerprint ownership fix

Read-only `logs.read(500)` tại `2026-08-26T08:23:47.108Z` cho thấy semantic
watchdog vẫn gặp timeout lặp lại trong process Recovery Host cũ. Trong cửa sổ
log quan sát được `20` lần restart Coding MCP sau hai lần timeout liên tiếp,
đều có `reason=timeout` và `errorCode=null`; mẫu lặp gồm các cặp probe fail ở
phút thứ nhất/thứ hai rồi restart MCP. HTTP health vẫn reachable, nên đây là
semantic-plane timeout chứ không phải bằng chứng MCP process đã chết. Không có
thao tác restart thủ công nào được thực hiện trong checkpoint này.

Audit source cho thấy nguyên nhân fingerprint chưa bao phủ đủ ownership:
`electron/recoveryHost.js` load `electron/services/mcpSemanticHealth.js`, nhưng
`COMPONENT_SPECS.recovery_host.files` trước đó không hash file watchdog. Một
thay đổi timeout/semantic-probe ở file đó vì vậy có thể nằm ngoài Recovery Host
revision proof. Đã áp dụng patch hẹp:

```text
COMPONENT_SPECS.recovery_host                    + electron/services/mcpSemanticHealth.js
local Recovery Host revision sau patch           292528d825655f1e7aa14395fa3c2baea9c4b0fd2fb1573dbd737750d1a015d5
local Recovery Host file_count                   28
regression test mới                               manifest owns semantic watchdog
```

Focused activation/recovery proof sau patch đạt:

```text
node --test tests/component-revision.test.js \
  tests/runtime-installation-identity.test.js \
  tests/recovery-activation.test.js \
  tests/recovery-host.test.js
→ 54 passed, 0 failed
node --test tests/mcp-semantic-health.test.js
→ semantic probe/watchdog contract PASS (đã có trong focused proof)
git diff --check
→ PASS (chỉ cảnh báo line-ending CRLF chuẩn Windows)
```

Official Recovery Host snapshot tại `2026-08-26T08:26:16.289Z` xác nhận patch
chưa được load vào host đang chạy:

```text
Recovery Host running revision                   940a7e0c...82bd37cc
Recovery Host disk revision                      d8fa0020...494ab0aa
Recovery Host file_count                          27
Recovery Host update_pending                     TRUE
local source revision sau manifest fix            292528d8...d1a015d5 / 28 files
Coding MCP running == disk revision              TRUE / current
activation lifecycle decision                    READY / clean=true
closure_state                                     CONNECTOR_CONTRACT_NOT_CURRENT
connector discovery                              UNAVAILABLE
```

Sự khác biệt `27` file trong host đang chạy với `28` file ở source hiện tại là
bằng chứng trực tiếp rằng Recovery Host còn dùng component manifest cũ; không
được tự nhận source patch đã active. Việc đưa host lên revision mới cần một
controlled Recovery Host replacement qua authority surface và phải được đánh
giá riêng với connector freshness; không thực hiện replacement tự động trong
checkpoint này vì chưa có explicit runtime-operation authorization.

Trạng thái sau wave:

```text
Semantic watchdog ownership manifest              SOURCE FIXED + 54 focused tests PASS
Loaded Recovery Host                              STALE / UPDATE_PENDING
Loaded Coding MCP/Tunnel                          CURRENT / FULLY_READY
Lifecycle decision                                READY / CLEAN
Repeated semantic timeout                        OBSERVED IN OLD HOST; not yet revalidated on patched host
Real-client discovery + acknowledgement           OPEN / NOT CONVERGED
Bounded Revision-4 canary                         NOT RUN
Natural HR outcome + independent receipt           NOT RUN
```

Không có connector acknowledgement, task-control mutation, ledger cleanup,
synthetic canary, natural workload, commit, push, package, release, deployment
hay production operation nào trong wave này. Exact next action là obtain
explicit authorization for the controlled Recovery Host replacement (if the
operator wants that runtime mutation), then recapture the new host revision and
semantic watchdog behavior before attempting connector discovery. The existing
rule remains: no `tools/list`/`server/discover` receipt, no ACK; no ACK, no
bounded canary; no natural outcome, no end-to-end completion claim.

## 38.11. Correction sau concurrent controller transition — lifecycle đã terminalize, host/connector vẫn chưa hội tụ

Checkpoint này sửa lại các bảng ở `§38.5`–`§38.10` vốn ghi ba RUN
`AWAITING_ACCEPTANCE` như thể chúng vẫn còn mở. Đó là trạng thái đúng tại thời
điểm các snapshot cũ, nhưng không còn là trạng thái hiện tại. Canonical ledger
được đọc query-only ở `2026-08-26T08:34Z` ghi nhận controller được hỗ trợ đã
terminalize từng RUN bằng state transition chính thức; không có direct SQL,
bulk stale cleanup, force-release lease hoặc thao tác của agent này:

| RUN | state transition | `finished_at` | quiescence event | lý do |
|---|---|---|---|---|
| `0ca7f60e56544df9aadb9fb89f7df48f` | `ACCEPTING → ABORTED` tại `2026-08-26T08:21:40.131Z` | `2026-08-26T08:21:40.360Z` | `2026-08-26T08:21:40.461Z` | superseded bởi source commit `b408d985e1097d738dcf4cf2cebe2cbcfd840353`; proof cũ không còn attest current bytes |
| `9489bcc986594ae998b247a39fd9007a` | `ACCEPTING → ABORTED` tại `2026-08-26T08:22:32.354Z` | `2026-08-26T08:22:32.579Z` | `2026-08-26T08:22:32.728Z` | cùng lý do superseded-proof, không acceptance |
| `d0900c558b4b4c67a7e13acb8f443d26` | `ACCEPTING → ABORTED` tại `2026-08-26T08:23:20.454Z` | `2026-08-26T08:23:20.695Z` | `2026-08-26T08:23:20.836Z` | cùng lý do superseded-proof, không acceptance |

RUN `167d23370d1e4c66bd64a1ae95a24012` vẫn `active` nhưng không có lease,
fence, lane hay managed job; census phân loại nó là
`THRESHOLD_SENSITIVE_STALE_CANDIDATE` với các reason
`inactive_without_live_ownership` và `below_current_stale_threshold`. Activity
age tại immutable capture là `84350.871s`, vẫn dưới ngưỡng preregistered
`86400s`; vì vậy không có exact stale-reconciliation action hợp lệ và không
được tự ý terminalize RUN này.

Immutable Gate-0 census mới nhất được capture lúc
`2026-08-26T08:32:30Z` (SQLite snapshot thực tế lúc `08:32:28.110Z`) xác nhận
canonical read-only boundary và trạng thái đã quiesced:

```text
schema_version                         11
physical snapshot SHA-256              1378af5ac59f348aafdf89d3d539eaeeb8d942d66957c054d7ec876b37a11a94
logical snapshot SHA-256               1b2b68b7928ac6e94d3533dea0043e58ef1597d5f4a8fbe8734161abad50b52c
integrity_check / foreign_key_check    ok / 0
mutated_canonical_ledger                false
ordinary active runs                    53
THRESHOLD_SENSITIVE_STALE_CANDIDATE    53
P5_EXPERIMENT_ANCHOR                    6
LIVE_OWNED / active lease / fence      0 / 0 / 0
managed jobs / unbound residue         0 / 0
unexplained active runs                 0
projection drift                        false (`NO_ACTIVE_PROJECTION`)
```

Đây là correction của lifecycle state, không phải bằng chứng source/runtime
đã đạt delivery baseline. Các `53` threshold candidates vẫn chỉ là descriptive
maintenance residue dưới threshold; `P5_EXPERIMENT_ANCHOR` là taxonomy riêng,
không trộn vào ordinary stale eligibility.

Official Recovery Host `runtime.lightweight_snapshot` recapture tại
`2026-08-26T08:34:07.753Z` vẫn cho thấy workspace đúng và Coding MCP/Tunnel
đang chạy, nhưng host chưa load manifest fix:

```text
workspace                                  E:\DEV\Codex-web
Git HEAD / dirty                           52faa0e9cfacf582fcf5bc6f40ed230cea7602e9 / TRUE
Coding MCP running == disk                 TRUE == TRUE
Coding MCP revision / files                50bb087b...18789eda / 111
Recovery Host running revision             940a7e0c...82bd37cc
Recovery Host disk revision                d8fa0020608152e46d42e725fae717929496fdb11903c8f87b116610494ab0aa
Recovery Host update_pending / file_count  TRUE / 27
lifecycle decision / clean                 READY / TRUE
connector_contract_state                   UNAVAILABLE
connector_rediscovered / timestamp         NULL / NULL
connector_refresh_required                NULL
closure_state                              CONNECTOR_CONTRACT_NOT_CURRENT
```

Do đó local source fix `292528d825655f1e7aa14395fa3c2baea9c4b0fd2fb1573dbd737750d1a015d5`
với `28` file (bao gồm `electron/services/mcpSemanticHealth.js`) vẫn là
`SOURCE + FOCUSED PROOF`, chưa phải loaded-runtime proof. Logs trả về từ
`logs.read(500)` trong cùng lần đọc có `63` semantic-probe failures,
`63` timeout records và `28` Recovery Host Coding MCP restarts trong rolling
window; record mới nhất là cặp timeout lúc `08:29:47`/`08:30:47Z` rồi restart.
HTTP health reachable trong các record này, nên chỉ kết luận được semantic
tool-plane timeout của host đang chạy cũ, không được suy ra process-death hay
được dùng làm causal verdict cho source fix chưa load.

Fresh C4 reporter receipt trước correction vẫn giữ đúng fail-closed boundary:

```text
status                                  C4_SOURCE_READY_AWAITING_NATURAL_CANARY
snapshot                                2026-08-26T08:28:22Z
physical SHA                            f97d54429814dededf1ce82d3ece05ee22c0edff83a5234582f347b6796ecf6c
logical SHA                             9c305cd1d01ed7d3ca9d89ad62e6fcae56fe51f4e7f78ab75fbd83a4cd654cd0
current-v11 events / exact binding      3 / 0 of 3
natural evidence                        attested=false
PRL-D economics                         DESCRIPTIVE_ONLY; no TTOC/TTFP/TTPR/trusted resolution
```

Không có current-process `tools/list` hoặc `server/discover`, nên không ACK
connector. Không có browser interaction nào trong checkpoint này: conversation
Coding-VP và draft người dùng `Liên hệ thêm` không bị đọc thêm, overwrite, clear
hay gửi đi. Cũng không có Recovery Host replacement/restart thủ công, bounded
canary, synthetic event, natural HR case, outcome receipt, commit, push, stage,
package, release, deploy hoặc production operation.

Trạng thái sau correction này là:

```text
Revision-4 source + focused proof                 COMPLETE
Lifecycle exact-run correction                    COMPLETE (controller-supported, read-only recaptured)
Ordinary stale eligibility                        0 exact eligible; 53 below-threshold candidates retained
Recovery Host manifest ownership fix              SOURCE FIXED / LOADED HOST STALE
Semantic watchdog after patched host              NOT REVALIDATED (replacement not authorized)
Real-client discovery + connector acknowledgement  OPEN / NOT CONVERGED
Bounded Revision-4 canary                         NOT RUN
Natural HR problem + independent outcome          NOT OBSERVED
Integrated delivery / release / production        NOT READY
```

## 38.12. Fresh post-correction C4/lifecycle receipt — source-ready, natural evidence vẫn bằng 0

Sau correction `§38.11`, C4 reporter được chạy lại trên một immutable Backup-API
snapshot lúc `2026-08-26T08:43:37.675Z`. Reporter vẫn không khởi tạo canonical
writer, không mutate schema/ledger và không suy diễn natural cohort:

```text
status                                  C4_SOURCE_READY_AWAITING_NATURAL_CANARY
schema_version                          2 (PRL v11)
physical snapshot SHA-256               9bf7a510350aa3b17e00f970e2f9f3833df25dc7a77074f8dce0dbf3e71f040e
logical snapshot SHA-256                3d60ad9715b17778c2e3e18c5f026eadae4311de35afdd7451f46179ddfc8ee7
SQLite integrity / FK                   ok / 0
current-v11 events                      3
exact revision binding                  0 / 3
criterion/proof, confirmation, clock    0 / 0 / 0
natural evidence                        attested=false, count=null
manual review reliability               not observed until independent annotation
policy                                   no C5 shadow, no C6 treatment, no efficacy promotion
```

Một lifecycle census read-only ngay trước đó tại `08:43:54.155Z` bắt gặp đúng
một managed job mới ở `starting`, không có PID và thuộc `GRACE_PERIOD_INACTIVE`;
đây là grace-window transient chứ không phải unexplained live ownership. Một
census follow-up sau 5 giây, snapshot tại `08:44:16.477Z`, xác nhận trạng thái
ổn định:

```text
schema_version                         11
physical snapshot SHA-256              d90e26bbdacb8017edd3a65661ff532709701b9e25a71d98f6d05b9c7979f763
logical snapshot SHA-256               006af27d7848e3ceb462ba2c578733db0d8204bf869ddf3178ade74eb92d9221
integrity_check / foreign_key_check    ok / 0
managed jobs                            0
ordinary active runs                    53
THRESHOLD_SENSITIVE_STALE_CANDIDATE    53
P5_EXPERIMENT_ANCHOR                    6
unexplained active / unbound residue   0 / 0
projection drift                        false (`NO_ACTIVE_PROJECTION`)
mutated canonical ledger                false
```

Official Recovery Host snapshot tại `2026-08-26T08:44:40.121Z` không thay đổi
quyết định runtime:

```text
workspace                                  E:\DEV\Codex-web
Coding MCP running == disk                 TRUE == TRUE
Coding MCP revision / files                50bb087b...18789eda / 111
Recovery Host running revision             940a7e0c...82bd37cc
Recovery Host disk revision                d8fa0020...494ab0aa
Recovery Host update_pending / file_count  TRUE / 27
fully_ready                                TRUE
lifecycle decision / clean                 READY / TRUE
connector_contract_state                   UNAVAILABLE
connector_rediscovered / timestamp         NULL / NULL
connector_refresh_required                NULL
```

Đây củng cố kết luận: lifecycle hiện không còn ba RUN `ACCEPTING` cũ và không
có live managed residue sau follow-up, nhưng loaded Recovery Host vẫn chưa bao
phủ semantic-watchdog manifest 28-file của source. C4 mechanics đã integrity
pass nhưng chưa có một natural problem revision, user outcome hoặc independent
receipt; không được nâng status thành canary, `PROVISIONALLY_RESOLVED`,
`RESOLVED_CONFIRMED` hay causal efficacy.

Không có source patch mới, runtime replacement, connector discovery, connector
ACK, browser/Coding-VP follow-up, synthetic workload, natural HR workload,
commit, push, package, release, deployment hoặc production operation trong
checkpoint này. Trạng thái hiện tại giữ nguyên:

```text
Revision-4 source + focused proof                 COMPLETE
C4 integrity/mechanics                            COMPLETE (source-ready)
Lifecycle stable read-only census                 COMPLETE (53 candidates + 6 P5 anchors)
Recovery Host patched-manifest activation         OPEN / NOT AUTHORIZED
Real-client discovery + connector acknowledgement  OPEN / NOT CONVERGED
Bounded Revision-4 canary                         NOT RUN
Natural HR problem + independent outcome          NOT OBSERVED
Integrated delivery / release / production        NOT READY
```

## 38.13. Đối chiếu tư vấn live mới — stale debt không còn, projection vẫn là `NO_ACTIVE_PROJECTION`

Tư vấn live mới cung cấp một kết luận đúng hướng rằng stale orchestration debt
đã giảm về `0`, nhưng cần tách rõ ba lớp evidence: stale eligibility, current
live ownership và task-state projection. Tôi recapture Gate-0 query-only sau
khi một diagnostic RUN concurrent kết thúc để không dùng snapshot của tư vấn
thay cho canonical current state.

Trong capture trung gian tại `2026-08-26T08:56:01.662Z`, một RUN chẩn đoán
concurrent `dc4016aa44184da3a41dc1e0fc127796` còn đang giữ lease của chính
client `chatweb:mcp2026:e321e6ed`, nên census hợp lệ phân loại tạm thời
`LIVE_OWNED=1`. Đây không phải RUN của agent này và không được stop/adopt. Sau
khi lease đó tự kết thúc, capture follow-up tại `2026-08-26T08:57:45.685Z`
đã trở lại trạng thái không có live owner:

```text
schema_version                         11
physical snapshot SHA-256              8b184b67236836f9553b9794b37edfa7999b32c1b750c46510c16e6da7bf851f
logical snapshot SHA-256               5ddbb31e431ec5ec3f4134bcab27cfe4543b7b02c8b7df3869df3d817e747e4f
integrity_check / foreign_key_check    ok / 0
ordinary active runs                    54
LIVE_OWNED                             0
GRACE_PERIOD_INACTIVE                  1
THRESHOLD_SENSITIVE_STALE_CANDIDATE    53
P5_EXPERIMENT_ANCHOR                    6
managed jobs                            0
unexplained active / unbound residue   0 / 0
projection drift                        false
projection classification               NO_ACTIVE_PROJECTION
mutated canonical ledger                false
```

Điều này xác nhận phần “stale debt = 0” của tư vấn theo nghĩa không có row nào
được census gán `LIVE_OWNED` hoặc một stale-reconciliation eligibility hiện
hành. Nó không chứng minh mọi task projection đã được reconcile: projection
hiện không tồn tại (`NO_ACTIVE_PROJECTION`), và boolean runtime
`task_orchestration_projection_reconciled` vẫn không thể nâng thành `true` chỉ
bằng cách nhận một active RUN của task khác. Source hiện đã có guard đúng cho
trường hợp này; test regression bảo đảm không adopt foreign task/run.

Official Recovery Host snapshot đồng thời tại `2026-08-26T08:55:48.215Z` vẫn
cho thấy:

```text
Coding MCP running == disk                 TRUE == TRUE
Coding MCP revision / files                50bb087b...18789eda / 111
Recovery Host running revision             940a7e0c...82bd37cc
Recovery Host disk revision                d8fa0020...494ab0aa
Recovery Host update_pending / file_count  TRUE / 27
fully_ready                                TRUE
connector_contract_state                   UNAVAILABLE
connector_rediscovered / timestamp         NULL / NULL
connector_refresh_required                NULL
```

Vì vậy tư vấn mới làm rõ thứ tự convergence, nhưng chưa mở được gate thực tế:

```text
stale lifecycle debt                         VERIFIED CLEAR AT FOLLOW-UP CENSUS
task projection                              NO_ACTIVE_PROJECTION / NOT APPLICABLE TO CURRENT TASK
Recovery Host source manifest                 SOURCE 28 FILES, LOADED HOST 27
ChatGPT/Coding-VP schema discovery            NO CURRENT-PROCESS RECEIPT
bounded real-client canary                   NOT RUN
natural HR outcome                           NOT OBSERVED
independent user/outcome receipt             NOT OBSERVED
immutable integrated baseline                NOT CREATED
```

Không có lifecycle mutation nào được gửi trong checkpoint này; chỉ có
query-only census và chờ đợi tự nhiên để diagnostic RUN concurrent tự giải
phóng lease. Do đó bước repository-local “projection cleanup” không được phép
thực hiện bằng direct SQLite, bulk cleanup hoặc nhận foreign RUN. Bước tiếp
theo vẫn là current-client schema discovery/refresh và controlled Recovery Host
replacement theo authority surface, nhưng cả hai đều cần external authority
chưa được cung cấp.

Exact next action không còn là “terminalize ba RUN acceptance” — việc đó đã
được controller xử lý và proof cũ bị hủy đúng semantics. Bước có giá trị tiếp
theo là xin explicit authorization cho controlled Recovery Host replacement,
nếu operator muốn thực hiện runtime mutation; sau replacement phải recapture
exact active 28-file manifest và semantic watchdog behavior. Song song, chỉ
người dùng mới có thể cho phép gửi follow-up tới Coding-VP bằng xác nhận rõ
`Đồng ý gửi follow-up Coding-VP`. Cho tới khi có đủ ba điều kiện
`connector_rediscovered=true`, timestamp khác rỗng và
`connector_refresh_required=false`, connector acknowledgement, bounded canary,
natural HR outcome và integrated completion vẫn bị khóa fail-closed.

## 38.14. Correction regression test — acceptance chỉ mở sau proof đúng RUN/WAVE

Trong quá trình chạy lại focused proof, `test_engineering_casebook.py` đã lộ
ra một fixture cũ gọi mutation-bearing `task_control(action="accept")` mà
không ghi nhận proof đã pass cho đúng `run_id` và `wave_id`. Source guard trả
về `ACCEPTANCE_PROOF_REQUIRED`, đúng với fail-closed contract; lỗi nằm ở
fixture chứ không phải ở guard.

Fixture đã được sửa bằng cách ghi một proof `status="passed"` với
`stage_id="casebook-acceptance"`, `stage_version="1"` và fingerprint cố định
trước lần accept hợp lệ. Assertion sai-wave vẫn được giữ nguyên và tiếp tục
chứng minh `ORCHESTRATION_WAVE_MISMATCH`; không có nới lỏng authority,
fingerprint hoặc acceptance semantics.

Bằng chứng sau correction:

```text
python -m pytest resources/coding-tools-mcp/tests/test_engineering_casebook.py -q
→ 7 passed

python -m pytest resources/coding-tools-mcp/tests/test_task_state_and_build.py \
  -k 'aborted_canonical_run_repairs_stale_awaiting_acceptance_projection or reconcile_does_not_adopt_active_run_from_different_task' -q
→ 2 passed, 69 deselected

git diff --check
→ PASS
```

Kết luận của checkpoint này chỉ là focused regression đã được khóa đúng
contract. Nó không nâng source/focused proof thành loaded-runtime proof, real
client canary, natural HR outcome, independent receipt, integrated baseline,
delivery, release hoặc production readiness.

## 38.15. Fresh final Gate-0/UI receipt — lifecycle không có live owner, connector vẫn khóa

Sau focused regression, tôi chạy lại lifecycle census qua Backup API bất biến
và chỉ đọc vào lúc `2026-08-26T09:12:12.213Z` (`16:12:12.213+07:00`). Census
không khởi tạo canonical writer/runtime/governor, không terminalize run và
không ghi SQLite:

```text
schema_version                         11
physical snapshot SHA-256              f145a65d1491e37917543c703f09a174d5497c8f238c14ec6f85fbe0ad955322
logical snapshot SHA-256               fb78dfefa48013037dbb6e483ea3378d721e02be635a1c63b20a83197d9f56d9
integrity_check / foreign_key_check    ok / 0
ordinary active runs                    56
LIVE_OWNED                             0
GRACE_PERIOD_INACTIVE                  3
THRESHOLD_SENSITIVE_STALE_CANDIDATE    53
P5_EXPERIMENT_ANCHOR                    6
managed jobs                            0
unexplained active / unbound residue   0 / 0
projection drift                        false
projection classification               NO_ACTIVE_PROJECTION
mutated canonical ledger                false
```

Một lease foreign của client khác đã được quan sát trong lần query thô ngay
trước census nhưng tự hết hạn trước snapshot bất biến; không có stop, adopt,
force-release hoặc bulk cleanup nào được thực hiện. Vì vậy trạng thái hiện tại
được giữ ở mức lifecycle read-only ổn định: không có live owner, nhưng các row
`active` còn lại không được tự động coi là đã reconcile chỉ vì không còn lease.

Receipt `npm run dev:status` cùng cửa sổ thời gian ghi nhận đúng UI development
hiện hành của checkout:

```text
state=CURRENT host=available installation=current
pid=14660 instance=ef73a567dce93a065656594cf102efb5 mode=development
running_revision=0e121e6d2a7b22b14d24670989c5e1cd0cebba99d1247e9ad44c07d676026fe5
disk_revision=0e121e6d2a7b22b14d24670989c5e1cd0cebba99d1247e9ad44c07d676026fe5
update_pending=false connector_state=UNAVAILABLE
connector_rediscovered=false connector_rediscovered_at=none
connector_refresh_required=unknown
```

UI `CURRENT` chỉ chứng minh process/revision của Electron UI; nó không thay
thế current-process `tools/list`/`server/discover`, official connector ACK,
Recovery Host patched-manifest activation hoặc C4 natural evidence. Do đó các
gate còn lại vẫn là:

```text
Lifecycle read-only census                    COMPLETE (no LIVE_OWNED; 3 grace + 53 threshold candidates)
Electron UI process/revision                  CURRENT / CURRENT (local status receipt)
Recovery Host 28-file manifest loaded        NOT PROVEN (loaded host remains 27-file / update pending)
Real-client schema discovery + connector ACK OPEN / NOT CONVERGED
Bounded Revision-4 canary                    NOT RUN
Natural HR problem + independent outcome     NOT OBSERVED
Immutable integrated baseline                 NOT CREATED
Delivery / commit / push / release           NOT PERFORMED
```

Sau receipt bất biến nói trên, một query-only recheck lúc
`2026-08-26T09:14:15.944Z` quan sát lại một lease đang active của RUN
`d229d575bc7d4b2b99f44e27e8c53d52`, owner `chatweb:mcp2026:21886936`. Đây là
client/hoạt động concurrent khác, không thuộc wave hiện tại; không có adopt,
stop, force-release hay mutation nào được thực hiện. Vì vậy receipt 09:12Z
vẫn là bằng chứng census bất biến cuối cùng đã pass, còn workspace live tại
thời điểm kết thúc không được gọi là quiescent cho tới khi controller foreign
tự terminalize hoặc phát hành lease theo authority surface.

## 38.16. Coding-VP follow-up receipt — đã gửi, không phát sinh repository/runtime mutation

Theo ủy quyền rõ ràng của người dùng (`Gửi ngay`), lúc
`2026-08-26T16:23:33.321+07:00` follow-up đã được gửi vào đúng cuộc trò
chuyện Coding-VP `Phân tích và khắc phục EOCL`. Tin nhắn yêu cầu tiếp tục
closure path với các ràng buộc sau:

```text
workspace target                         E:\DEV\Codex-web
causal boundary                          Recovery Host → currentMcpHealth() → /__control/health
required proof                           focused causal patch + exact live identity/discovery receipt
connector ACK gate                       rediscovered=true + timestamp + refresh_required=false
forbidden without new gate               foreign-run adopt/stop/force-release, blind ACK, restart/replacement,
                                          natural HR case, canary, commit, push, release, production mutation
```

Browser receipt xác nhận message đã xuất hiện trong conversation và Coding-VP
đã bắt đầu xử lý, với phản hồi sơ bộ: tiếp tục `causal patch + focused proof`,
không mở diagnostic RUN mới, chỉ đọc lại live identity/discovery/connector
state và dừng trước mọi restart/replacement/ACK hoặc production mutation cần
gate mới.

Không có file, ledger, lease, runtime process, Recovery Host hoặc connector
state nào bị sửa trong hành động gửi này. Ô nháp người dùng `Liên hệ thêm`
không được đọc, clear hoặc overwrite; sau khi gửi, UI hiển thị lại draft đó và
được giữ nguyên.

Trạng thái sau receipt:

```text
Coding-VP follow-up                     SENT / PROCESSING
Repository-local source proof           UNCHANGED
Recovery Host replacement               NOT REQUESTED / NOT PERFORMED
Connector acknowledgement               NOT PERFORMED
Natural HR case / independent outcome   NOT OBSERVED
Commit / push / release                 NOT PERFORMED
```

**End of working methodology.**
