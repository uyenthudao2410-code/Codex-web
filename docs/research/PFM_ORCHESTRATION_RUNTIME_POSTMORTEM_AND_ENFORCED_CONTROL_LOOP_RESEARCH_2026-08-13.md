# PFM Orchestration Runtime Postmortem & Enforced Control Loop Research

**Ngày nghiên cứu:** 2026-08-13  
**Repository lưu tài liệu:** `uyenthudao2410-code/Tools-Codex-web`  
**Incident source repository:** `uyenthudao2410-code/HR`  
**Incident branch:** `V_Finance`  
**Authoritative incident commit:** `89bc4baddaa32614b4689c68e09595acc0f78923`  
**Commit message:** `feat(finance): deliver PFM cost control and fast entry`  
**Loại tài liệu:** production postmortem + scientific/field evidence review + orchestration control-loop redesign  
**Mục tiêu:** biến policy phối hợp ChatWeb Sol / Coding Tools MCP / Codex Desktop từ guideline thành **machine-enforced execution control loop**, giảm orchestration drift, duplicated work, patch ambiguity, proof reruns, context waste và accepted-result cost.

---

## 0. Executive decision

### 0.1 Kết luận chính

Lượt PFM vừa hoàn thành **không cho thấy kiến trúc phối hợp trước đây sai về mặt nguyên lý**. Nó cho thấy một vấn đề khác nghiêm trọng hơn:

> **Policy đúng nhưng runtime không enforce policy.**

Các thành phần cần thiết đều đã tồn tại ở mức thiết kế:

- ChatWeb Sol giữ financial semantics, architecture, authorization boundary và final acceptance;
- Coding Tools MCP có deterministic search/test/patch/Git/proof primitives;
- Codex Sol xhigh được định nghĩa là deep-code lane;
- Desktop coordination có supervisor/status/inbox assets;
- packet contract đã có `OBJECTIVE / SCOPE / CONTEXT / PROOF / STOP`;
- skill đã cấm blind retry/cascade và khuyến nghị one-write-owner + isolated worktree.

Nhưng trong execution thật, các điều kiện sau **chưa phải hard runtime invariant**:

1. Desktop coordination được chọn nhưng supervisor/coordination plane chưa ready vẫn không block mutation.
2. Deep-code lane gặp `PROMPT_TOO_LARGE`/deadline nhưng không bắt buộc chuyển sang `REPLAN` trước khi controller tiếp tục mutation.
3. Controller có thể dần trở thành implementation executor thông qua nhiều MCP patches mà không có explicit ownership transfer.
4. Packet bị chia theo file/hunk hơn là theo behavior có oracle.
5. Shared dirty checkout thay đổi liên tục nhưng candidate patch không được pin bằng `BASE_HEAD + WORKTREE_FINGERPRINT`.
6. Proof stages đã pass không có reusable proof identity, nên wrapper timeout ở stage sau vẫn làm orchestration phải chạy lại hoặc chứng minh thủ công phần còn thiếu.
7. Route/model/tool/proof telemetry chưa đủ để lượng hóa waste và tự hiệu chỉnh router.

Do đó thay đổi quan trọng nhất không phải “gọi Codex Desktop nhiều hơn”, “dùng Sol xhigh nhiều hơn”, hoặc “chia nhiều agent hơn”. Thay đổi cần ưu tiên là:

> **Enforced Orchestration Control Loop (EOCL): explicit state machine + readiness gates + write ownership + typed recovery + proof fingerprint + route ledger.**

### 0.2 Target topology

```text
USER
  |
  v
CHATWEB SOL — semantic/control authority
  |
  | establish finish line / invariants / task shape
  v
ONE-TIME PREFLIGHT
  |- BASE / WORKTREE identity
  |- oracle readiness
  |- runtime capabilities
  |- Desktop/App Server readiness when mode requires it
  |- DB/toolchain readiness when proof requires it
  v
EXECUTION MODE CLASSIFIER
  |
  +--> MCP_ONLY
  |
  +--> BOUNDED_CANDIDATE
  |      Mini low / Luna high
  |
  +--> DEEP_SINGLE_LANE
  |      Codex Sol xhigh
  |
  +--> COORDINATED_MULTI_WORKTREE
         only when truly parallelizable
  |
  v
DETERMINISTIC PROOF DAG
  |- stage results keyed by PROOF_FINGERPRINT
  |- reuse valid prior PASS
  |- broad gate once per integrated fingerprint
  v
CHATWEB SOL ACCEPT / REPLAN
  v
CHECKPOINT
```

### 0.3 Production principle after this incident

```text
ROUTER IS NOT ADVICE.
ROUTER IS A STATE TRANSITION AUTHORITY.
```

Nếu runtime đang ở `DEEP_SINGLE_LANE`, controller không được tự chuyển thành writer chỉ vì Codex fail. Nó phải:

```text
EXECUTING
  -> REPLAN
  -> explicit route/mode change
  -> ownership transfer
  -> EXECUTING
```

Không có transition thì không có mutation.

---

# 1. Evidence model

Postmortem này tách bốn cấp evidence để không trộn observation với inference.

## 1.1 Level A — GitHub authoritative evidence

Đã kiểm chứng trực tiếp từ GitHub:

- repo `uyenthudao2410-code/HR` có branch `V_Finance`;
- branch head là `89bc4baddaa32614b4689c68e09595acc0f78923`;
- commit message là `feat(finance): deliver PFM cost control and fast entry`;
- commit parent là `4435aa82e6abd9b1c1beacfd977efb73c20f5cfb`;
- commit API báo `+2803 / -117`, total `2920` changed lines;
- compare parent -> head cho thấy **43 files**;
- scope của commit trải qua OpenAPI, backend DTO/services, capability/auth surface, PostgreSQL proof, frontend, generated routes và story docs US-109 -> US-112;
- backlog ở `V_Finance` giữ US-112 ở `in_progress`;
- US-109/110/111 đã là `implemented`;
- US-112 overview giữ các financial invariants exact-decimal/default-off/project-scoped/atomic/fail-before-persistence.

## 1.2 Level B — operator/session observations

Các facts do operator ghi nhận trong execution vừa rồi:

- `E:\Github\HR_COORD` và `E:\Github\HR-PFM-BE` tồn tại;
- `watch-pfm.ps1` nhiều lần `NOT_RUNNING` / `SUPERVISOR_COUNT=0`;
- Codex deep-code gặp `PROMPT_TOO_LARGE` hoặc deadline;
- có nhiều `PATCH_CONTEXT_AMBIGUOUS`, `PATCH_CONTEXT_NOT_FOUND`, `PATCH_FAILED`;
- một interrupted patch ở US-111 từng để duplicate declarations;
- `verify:pfm-management` và `verify:bff-gate` wrapper timeout ở các stage sau trong khi constituent checks trước đó đã pass;
- constituent BFF/security tail về sau được chạy riêng và xanh;
- local push được operator báo `ahead 0 / behind 0 / working tree clean`.

Các runtime logs này không còn được reconstruct đầy đủ từ máy sau khi máy đã shutdown, nên report coi chúng là **operator-observed production telemetry**, không giả mạo thành GitHub evidence.

## 1.3 Level C — local benchmark evidence của Tools-Codex-web

Từ research trước:

- Phase 1: ChatWeb Sol -> MCP đạt 10/10 accepted; Luna-low autonomous 2/10; Terra-medium autonomous 6/10.
- Naive Luna -> Sol fallback tăng mean TTA khoảng 39.9%; Terra -> Sol khoảng 18.6% so với Sol-only control.
- Phase 2 bounded packet common tasks:
  - Mini low patch-only: 3/3, mean TTA ~9.11s, ~0.1585 credits;
  - Luna high patch-only: 3/3, ~7.89s, ~0.2597 credits;
  - Sol xhigh patch-only: 3/3, ~11.23s, ~1.3173 credits.
- Cùng Sol xhigh nhưng autonomous shell/tool loop: 0/3 accepted trước ~31s stop trên narrow strong-oracle leaves.

Internal reports:

- `docs/research/EXECUTOR_ROUTING_BENCHMARK_2026-08-12.md`
- `docs/research/MODEL_ORCHESTRATION_RESEARCH_PHASE2_2026-08-12.md`
- `docs/research/ORCHESTRATION_METHODOLOGY_EXPERIMENTS_AND_PRODUCTION_DECISION_2026-08-12.md`

## 1.4 Level D — external scientific/official/field evidence

Dùng ba nhóm riêng:

1. **Peer-reviewed / research papers**: ACL/EACL/arXiv research.
2. **Official engineering references**: Git, Bazel, Kubernetes, OpenTelemetry.
3. **Field reports**: public issues trong official `openai/codex`; dùng như operational warning, không coi là controlled causal proof.

---

# 2. Provenance correction: commit thực tế

Operator ban đầu ghi full SHA:

```text
89bc4bad2bd5dc1ba9fced763a8c941dc977cb21
```

GitHub authoritative branch head hiện là:

```text
89bc4baddaa32614b4689c68e09595acc0f78923
```

Hai SHA cùng prefix `89bc4ba` nhưng phần sau khác nhau. Tài liệu này dùng **GitHub SHA**.

Ngoài ra operator report ghi:

```text
34 files
+4,262
-883
```

Trong khi GitHub single-commit API/compare hiện xác nhận:

```text
43 files
+2,803
-117
```

Hai số đo không được dùng thay thế cho nhau. Có thể local summary đã đo một wider working-tree/session/range khác; không đủ evidence để khẳng định nguyên nhân chênh lệch. Postmortem dùng GitHub single-commit stats cho provenance, và giữ operator numbers chỉ như historical session observation.

---

# 3. Commit shape nói gì về orchestration

Single commit không chỉ chứa US-112. Nó gom một integration checkpoint rộng gồm:

## 3.1 Backend/API

- `apps/finance-api/openapi/finance-v1.openapi.json`
- command capability registry
- PFM batch DTO/service/tests
- PFM command DTO/service/tests
- read controller/module/openapi tests
- new project cost-control read service + test

## 3.2 Frontend/client

- `PfmDailyEntryPanel` + tests
- `PfmManagementModule` + tests
- `pfmDailyEntry` + tests
- preview data
- `services/financeApi.ts`
- generated finance routes

## 3.3 Runtime/proof

- Excel parity candidate/test
- PostgreSQL PFM command proof script

## 3.4 Governance

Story docs cho:

- US-109 Cost Control v1
- US-110 Cost Control UI
- US-111 Excel Cost Reconciliation
- US-112 Project Cost Fast Entry

Điều này không chứng minh checkout luôn bẩn trong mọi thời điểm, nhưng nó **xác nhận final checkpoint trải qua nhiều story/integration surfaces cùng một commit**, đúng với observation rằng mutation/proof scope đã tích lũy rộng.

---

# 4. US-112 là high-integration-width task thật sự

US-112 overview trên GitHub xác nhận các semantics:

- generic `PROJECT_COST_TRANSACTION`, không tự biến thành `DIRECT_COST`;
- exact VND decimal strings end-to-end;
- optional cost code, blank = explicitly unclassified;
- supplied cost code phải active và không thuộc company-common classes;
- `pfm.cost.create` default-off + project-scoped;
- caller không sở hữu `commandId`, `projectId`, `transactionCode`, lifecycle fields;
- closed/locked periods fail before persistence;
- capability/scope checks xảy ra trước persisted duplicate lookup;
- persistence + PFM refresh outbox + audit + batch boundary ở cùng atomic transaction.

Đây không phải “feature UI to”. Nó là một behavior spanning:

```text
AUTHORIZATION
+ FINANCIAL SEMANTICS
+ IDEMPOTENT IDENTITY
+ ATOMIC DB WRITE
+ LIFECYCLE STATE
+ PUBLIC OPENAPI CONTRACT
+ GENERATED CLIENT
+ FRONTEND UX
+ POSTGRES PROOF
```

Do đó việc classifier coi US-112 là high integration width là đúng.

---

# 5. Intended orchestration vs actual runtime

## 5.1 Intended

```text
ChatWeb Sol
  -> settle finance semantics/public contract
  -> preflight Desktop/App Server execution mode
  -> Codex Sol xhigh deep implementation packet
  -> MCP deterministic proof
  -> Sol acceptance
```

Nếu backend/frontend có thể parallelize:

```text
freeze contract first
-> isolated BE worktree
-> isolated FE worktree
-> central integration/proof
```

## 5.2 Actual drift

Observed path gần hơn với:

```text
Sol defines semantics
-> Desktop supervisor not active
-> deep-code packet fails/oversizes/deadlines
-> no hard REPLAN gate
-> controller keeps making smaller MCP-driven edits
-> packet granularity shrinks file/hunk-by-file/hunk
-> checkout keeps moving
-> patch ambiguity rises
-> verification wrappers become long sequential tail
-> manual constituent proof recovery
-> broad multi-story checkpoint
```

Correctness có thể vẫn đạt, nhưng topology đã thay đổi mà không có explicit state transition.

---

# 6. Root cause tree

```text
PRIMARY FAILURE
Orchestration policy was advisory, not enforced
|
+-- A. Activation/readiness not a mutation gate
|
+-- B. Executor failure did not force REPLAN
|
+-- C. Write ownership could drift to controller
|
+-- D. Packet boundary optimized for immediate patchability, not behavior coherence
|
+-- E. Shared checkout drift invalidated exact-context assumptions
|
+-- F. Proof validity lacked fingerprints/stage persistence
|
+-- G. Telemetry insufficient for accepted-result economics
```

---

# 7. Root cause A — coordination plane existed but was not ready

Operator observed coordination assets/worktree nhưng supervisor repeatedly not running.

Sai lầm ở đây không phải “Desktop phải luôn luôn chạy”. Desktop coordination **không nên là global precondition**.

Hard rule phải là:

```text
if execution_mode requires desktop coordination:
    coordination_readiness == READY
else:
    desktop state is irrelevant
```

## 7.1 Readiness is different from existence

Có directory, inbox hoặc scripts không có nghĩa executor ready.

Proposed readiness vector:

```text
SUPERVISOR_PROCESS_ALIVE
CONTROL_CHANNEL_RESPONSIVE
EXPECTED_WORKTREE_EXISTS
BASE_HEAD_MATCHES
WORKER_THREAD_OR_APP_SERVER_REACHABLE
MODEL_ROUTE_RESOLVED
WRITE_SCOPE_AVAILABLE
NO_STALE_OWNERSHIP_LEASE
```

## 7.2 Startup / readiness / liveness analogy

Kubernetes phân biệt:

- startup: service đã initialize chưa;
- readiness: có đủ điều kiện nhận traffic/work chưa;
- liveness: đang còn healthy/progress được không.

EOCL nên học pattern này:

```text
COORD_STARTUP
  one-time activation success

COORD_READY
  eligible to receive new packet now

COORD_LIVE
  active lane still healthy during execution
```

Nếu `READY=false`, router không dispatch packet vào lane đó.

Nếu `LIVE=false` mid-task:

```text
EXECUTING -> REPLAN
```

chứ không silently mutate bằng controller.

---

# 8. Root cause B — deep-code failure recovery lacked a state guard

US-112 ban đầu đúng class cho Sol xhigh deep lane.

Operator observed failures như:

```text
PROMPT_TOO_LARGE
deadline
```

Policy đã nói “no unchanged retry”, và execution thực tế có đổi strategy. Nhưng strategy đổi quá xa mà không có explicit reclassification:

```text
DEEP CODE FAILURE
-> many controller-led deterministic patches
```

Đây là **authority drift**.

## 8.1 Correct failure transition

```text
EXECUTING(DEEP_SINGLE_LANE)
  |
  +-- PROMPT_TOO_LARGE
  +-- DEADLINE
  +-- CAPACITY
  +-- TOOL_STATE_FAILURE
  v
REPLAN
```

Trong `REPLAN`:

- freeze feature mutation;
- preserve evidence/diff/partial proof;
- classify failure;
- decide whether packet should be narrowed, split, context-compacted, rerouted or blocked;
- create new route decision record;
- only then transfer write ownership.

## 8.2 Controller write guard

Proposed invariant:

```text
controller_feature_mutation_allowed =
    execution_mode == MCP_ONLY
    OR explicit_replan_transferred_ownership == true
```

When mode is:

```text
DEEP_SINGLE_LANE
COORDINATED_MULTI_WORKTREE
```

controller may:

- inspect;
- collect evidence;
- run proof;
- stop/interrupt;
- accept/reject;

but may not incrementally implement the delegated feature scope unless ownership is explicitly transferred in a `REPLAN` transition.

---

# 9. Root cause C — packet fragmentation optimized the wrong thing

Observed sequence was roughly:

```text
DTO slice
-> capability slice
-> batch type
-> batch map
-> service runtime
-> fixture
-> test
-> frontend type
-> builder
-> panel
-> test
-> OpenAPI
-> PostgreSQL proof slices
```

Việc này giúp controller tiến từng bước và giảm local uncertainty, nhưng tạo ba costs:

1. model/router startup + context selection lặp lại;
2. shared checkout thay đổi giữa các patch;
3. behavior-level acceptance bị phân tán qua nhiều micro-successes.

## 9.1 Better unit of delegation

Packet phải là **behavior with oracle**, không phải file/hunk.

Một packet tốt trả lời:

```text
WHAT BEHAVIOR IS OWNED?
WHAT SEMANTICS ARE SETTLED?
WHAT CODE SURFACE MAY CHANGE?
WHAT PROOF DEFINES DONE?
WHAT CONDITION FORCES STOP?
```

Không phải:

```text
please edit file X
then file Y
then file Z
```

---

# 10. US-112 redesigned as three coherent packets

## Packet A — BACKEND_FINANCIAL_BOUNDARY

```text
OBJECTIVE
Implement governed PROJECT_COST_TRANSACTION write and authoritative cost-control read while preserving settled finance semantics.

SCOPE
- pfm.cost.create capability + project scope
- command/batch DTO validation
- deterministic identity/idempotency
- locked/closed period fail-before-write
- atomic persistence/outbox/audit/batch boundary
- cost-control read semantics
- backend OpenAPI source contract

CONTEXT
- exact VND decimal strings
- cost code/unclassified/company-common rules
- default-off authorization
- DIRECT_COST remains blocked
- server owns identity/lifecycle fields

PROOF
- focused backend unit/integration tests
- authorization/capability tests
- PostgreSQL command proof
- OpenAPI backend contract checks

STOP
- finance meaning ambiguous
- public contract unsettled
- required base/worktree fingerprint changes
- patch leaves allowed scope
```

## Packet B — FRONTEND_CONTRACT_BOUNDARY

Requires backend/public contract frozen.

```text
OBJECTIVE
Implement fast-entry + cost-control UI against server-authoritative contract without client-side official financial aggregation.

SCOPE
- financeApi/generated client
- daily-entry helper
- fast-entry UI
- cost-control management UI
- focused FE tests

CONTEXT
- frozen OpenAPI/types
- server-authoritative semantics
- capability behavior
- exact decimal display/transport rules

PROOF
- focused UI/helper tests
- frontend typecheck
- generated-client/OpenAPI consistency
- frontend build

STOP
- contract fingerprint changed
- new finance semantic decision required
```

## Packet C — INTEGRATION_ACCEPTANCE

```text
OBJECTIVE
Prove A+B integrate without changing settled semantics.

SCOPE
- no architecture redesign
- generated contract parity
- BFF/security tail
- Postgres proof
- focused FE/BE integration
- final broad gate

PROOF
proof DAG all required nodes green on same integrated fingerprint

STOP
any cross-boundary invariant failure -> REPLAN to owning packet
```

---

# 11. When backend/frontend should run in parallel

Không phải cứ có BE và FE là có two-agent parallelism.

## 11.1 Parallel-safe condition

```text
INTERFACE_FROZEN = true
SEMANTICS_SETTLED = true
WRITE_OWNERSHIP_DISJOINT = true
WORKTREES_ISOLATED = true
PROOF_PER_LEAF_EXISTS = true
INTEGRATION_CAPACITY_AVAILABLE = true
SERIALITY = low/medium
```

Only then:

```text
BE worktree || FE worktree
        \      /
         integrate
```

## 11.2 US-112 before contract freeze

Financial semantics, capability, batch payload, atomic lifecycle và public contract ảnh hưởng FE assumptions.

Before these settle:

```text
SERIALITY = high
```

Two persistent workers would increase stale-work/merge risk.

Recommended:

```text
Sol settles contract
-> Backend packet
-> freeze OpenAPI/behavior contract
-> FE packet can then run independently
```

---

# 12. External research: multi-agent gains depend on task shape

Google Research, *Towards a Science of Scaling Agent Systems* (2026), reports a controlled study of 180 agent configurations. Their central result is directly relevant:

- multi-agent coordination helps parallelizable tasks;
- it can degrade sequential tasks;
- centralized orchestration better contains error propagation than independent agents;
- task properties such as decomposability/tool density can predict suitable architecture.

Implication for PFM:

```text
"feature is large" != "use many agents"
```

A large feature with changing financial semantics can be **more sequential** than a smaller feature with independent adapters.

Source:

- Google Research, 2026-01-28, `Towards a science of scaling agent systems: When and why agent systems work`
- https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/

---

# 13. External research: routing should reduce switches, not build ladders

MTRouter (ACL 2026) studies cost-aware multi-turn model routing. It reports improved quality/cost trade-offs and observes that an effective policy makes **fewer model switches** and develops model specialization.

This reinforces our local Phase 1 result that:

```text
Luna -> Sol
Terra -> Sol
```

serial fallback can lose to direct routing once validation/startup/rework is counted.

Implication:

```text
classify once
-> one competent lane
-> at most one evidence-driven replan/fallback
```

not:

```text
Mini -> Luna -> Terra -> Sol -> Max -> Ultra
```

Source:

- Zhang et al., `MTRouter: Cost-Aware Multi-Turn LLM Routing with History–Model Joint Embeddings`, ACL 2026.
- https://aclanthology.org/2026.acl-long.2045/

---

# 14. External research: simple historical route ledger can be enough

ContextualRouter (EACL 2026) reports that retrieval from similar historical tasks, including simple kNN averaging, can be competitive with more complex routers and remain useful with sparse history.

This supports a practical implementation order:

```text
DO NOT build learned router first.

First build:
- reliable route ledger
- normalized task features
- nearest similar accepted tasks
- simple rules
```

Only after enough clean data should a learned router be considered.

Source:

- Varangot-Reille et al., `Generalising LLM Routing using Past Performance Retrieval: A Few-Shot Router is Sufficient`, EACL 2026.
- https://aclanthology.org/2026.eacl-srw.22/

---

# 15. External research: explicit execution state beats raw long history

Ledger (arXiv:2608.00808, 2026-08-01) is unusually close to the failure observed here.

The paper argues long-horizon coding agents often cannot tell from raw interaction history:

- which observations still match current repo state;
- what already changed;
- what work has already been attempted;
- whether an old proof remains valid.

Ledger introduces a deterministic runtime layer with:

- compact explicit execution state;
- `inform` path that injects current state;
- `govern` path that can return still-valid prior results instead of re-executing redundant commands.

Reported results include improved Pass@1 and reduced cost, including when attached to OpenAI Codex.

This is direct support for replacing repeated `Get-Content/Select-String/test wrapper` reconstruction with a compact state ledger.

Source:

- Wang et al., `Turning Interaction History into Execution State: A Runtime Layer for Long-Horizon Coding Agents`, arXiv:2608.00808.
- https://arxiv.org/abs/2608.00808

---

# 16. External research: Manage–Execute–Audit separation

LongHorizon-Harness (arXiv:2608.01964) reframes long-horizon execution as **task-state management**. Its MEA loop separates:

```text
MANAGER
maintains explicit task state / chooses next subtask

EXECUTOR
fresh-context task execution

AUDITOR
read-only verification from environment
```

Crucially, task state is updated only from independently verified environment facts.

This maps closely to desired topology:

```text
ChatWeb Sol / EOCL manager
-> Codex or MCP executor
-> deterministic proof / independent auditor
```

It also supports the rule that executor narrative does not become truth until environment proof updates the ledger.

Source:

- Ma et al., `LongHorizon-Harness: Advancing Long-Horizon Agents for Real-World Tasks`, arXiv:2608.01964.
- https://arxiv.org/abs/2608.01964

---

# 17. External research: context management is a first-class subsystem

COMPASS (ACL 2026) identifies context management as a central long-horizon bottleneck and separates tactical execution, strategic oversight, and context organization.

This supports a short **state capsule** rather than repeatedly replaying repository/history context.

Recommended live capsule:

```text
GOAL
ACCEPTANCE
STORY / TASK
BASE_HEAD
WORKTREE_ID / WORKTREE_FP
EXECUTION_MODE
ROUTE / MODEL / EFFORT
SETTLED_INVARIANTS
FROZEN_CONTRACTS
ACTIVE_PACKET
WRITE_OWNER
LATEST_ACCEPTED_EVIDENCE
VALID_PROOFS
OPEN_UNCERTAINTY
FAILURE_CLASS
NEXT_STATE / NEXT_ACTION
```

Source:

- Wan et al., `COMPASS: Enhancing Agent Long-Horizon Reasoning with Evolving Context`, ACL 2026.
- https://aclanthology.org/2026.acl-long.152/

---

# 18. External research: independent verification beats same-interpretation self-review

RETRACE (arXiv:2608.08950) provides independent patch verification through forward/backward reconstruction and reports Pass@1 gains on SWE-bench Verified.

Key idea relevant here:

> More reasoning by the same interpretation is not the same as independent verification.

Production implication:

- executor can be Sol xhigh;
- proof should still come from deterministic tests/DB/schema checks;
- if semantic review is needed, reviewer should receive evidence/diff and solve a distinct verification question;
- do not spawn multiple Sol agents merely to agree with the primary rationale.

Source:

- Li et al., `Independent Patch Verification for Coding Agents with a Bidirectional Reconstruct-and-Verify Framework`, arXiv:2608.08950.
- https://arxiv.org/abs/2608.08950

---

# 19. External research: tool-call count can become a performance tax

ACL 2026 paper *Rethinking the Role of Entropy in Optimizing Tool-Use Behaviors for Large Language Model Agents* explicitly observes that long agent trajectories can produce excessive low-quality tool calls, increasing latency and degrading inference performance.

This reinforces the tuning order:

```text
1. remove duplicate scans / reruns
2. batch deterministic operations
3. reduce context/tool entropy
4. improve packet boundary
5. only then change model/agent count
```

Source:

- Li et al., ACL 2026, Anthology `2026.acl-long.1288`.
- https://aclanthology.org/2026.acl-long.1288/

---

# 20. External research: parallel coding benefits from isolated workspaces

CAID, *Effective Strategies for Asynchronous Software Engineering Agents* (2026), directly studies multi-agent SWE and highlights the exact problems seen in shared mutable checkout:

- concurrent edits interfere;
- dependencies are hard to synchronize;
- merging partial work is difficult.

Its proposed paradigm uses:

```text
centralized delegation
+ async execution
+ isolated workspaces
+ structured integration
+ executable verification
```

The paper specifically identifies branch-and-merge and Git worktree/commit/merge primitives as central mechanisms.

This supports the rule:

> Concurrent writers must not share authoritative checkout.

Source:

- Geng & Neubig, `Effective Strategies for Asynchronous Software Engineering Agents`, arXiv:2603.21489.
- https://arxiv.org/abs/2603.21489

---

# 21. Git worktree is the right primitive for concurrent write isolation

Official Git documentation supports multiple linked worktrees with separate working trees/HEAD/index state.

For our orchestration:

```text
one mutable surface -> one owner
parallel writer -> separate worktree
```

Proposed ownership packet fields:

```text
BASE_HEAD
WORKTREE_PATH
WORKTREE_ID
WORKTREE_FINGERPRINT
WRITE_OWNER
ALLOWED_PATHS
CONTRACT_FINGERPRINT
```

No agent may write if current base/worktree fingerprint differs from packet baseline.

Source:

- Git `git-worktree` official documentation.
- https://git-scm.com/docs/git-worktree

---

# 22. Root cause D — exact-context patching on a moving checkout

Operator observed:

```text
PATCH_CONTEXT_AMBIGUOUS
PATCH_CONTEXT_NOT_FOUND
PATCH_FAILED
```

These are not random patch syntax errors. In a long shared checkout they often indicate one of:

- context changed since candidate created;
- duplicate similar context exists;
- candidate localized a stale neighborhood;
- prior interrupted patch partially changed the expected target.

## 22.1 Correct response to patch ambiguity

Do not progressively make matching fuzzier.

```text
PATCH_CONTEXT_* failure
-> classify BASE_DRIFT_OR_LOCALIZATION_INVALID
-> compare current BASE_HEAD / WORKTREE_FP
-> reject stale candidate
-> re-localize exact symbol against current state
-> regenerate candidate
```

For delegated work:

```text
candidate patch
+ base fingerprint
+ allowed paths
```

MCP applies atomically only if all guards match.

---

# 23. Root cause E — authoritative checkout remained an integration buffer too long

GitHub confirms final commit spans 43 files and artifacts across US-109 -> US-112.

This increases:

- diff review width;
- exact patch ambiguity;
- difficulty attributing proof to a story;
- probability that later packet reads state produced by earlier uncheckpointed work;
- recovery complexity after interrupted edits.

## 23.1 Checkpoint != governance completion

A key lesson from US-112 is that the team did the right thing by keeping story status `in_progress`.

Git checkpoint and story governance state are independent concepts:

```text
TECHNICAL_CHECKPOINT = stable source/proof base
GOVERNANCE_STATUS = planned | in_progress | implemented | ...
```

Therefore a commit can safely checkpoint an accepted technical boundary while story remains `in_progress` because external gates/UAT/governance are not complete.

## 23.2 Recommended checkpoint policy

Checkpoint after:

- one accepted story-level implementation boundary; or
- one stable shared contract that later packets depend on; or
- before starting a distinct risky story when current proof is green.

Do not checkpoint every hunk.  
Do not hold four stories as one mutable buffer if stable boundaries already exist.

---

# 24. Root cause F — verification wrapper is monolithic

GitHub `package.json` verifies the current wrapper design.

`verify:pfm-management` chains roughly:

```text
test:pfm-candidate
-> check:finance-contract
-> test:pfm-record-read-postgres
-> test:pfm-command-postgres
-> typecheck:frontend
-> typecheck:finance
-> build:frontend
-> build:finance
-> git diff --check
```

`verify:bff-gate` is even broader:

```text
prisma generate
-> frontend typecheck
-> frontend build
-> finance typecheck
-> iam authorization
-> data isolation
-> auth origin
-> bff auth
-> bff finance
-> bff timesheet
-> bff frontend
-> bff guards
-> browser-token guard
-> service-worker guard
-> git diff --check
```

A wrapper timeout late in such a chain is a **transport/orchestration failure**, not evidence that every earlier assertion failed.

---

# 25. Verification should be a DAG of proof stages

Instead of one opaque long command:

```text
                    +-> AUTH/IAM -------+
                    |                   |
BACKEND FOCUSED ----+-> POSTGRES -------+---> INTEGRATION
                    |                   |
                    +-> OPENAPI --------+
                                           \
FRONTEND FOCUSED -> TYPECHECK -> BUILD -----+--> BROAD FINAL
```

Each node emits:

```text
STAGE_ID
STATUS
STARTED_AT
FINISHED_AT
COMMAND
BASE_HEAD
INPUT_FINGERPRINT
PROOF_FINGERPRINT
ARTIFACTS / LOG_REF
```

If a late stage times out:

```text
previous exact-fingerprint PASS != invalidated
```

Only the unfinished/invalidated node and its dependents need run.

---

# 26. Proof fingerprint

Inspired by content-addressed build systems such as Bazel, proof reuse must depend on explicit inputs.

Proposed:

```text
PROOF_FP = SHA256(
    BASE_HEAD
  + relevant_changed_file_hashes
  + command
  + toolchain_versions
  + lockfile_hashes
  + relevant_config_hashes
  + schema/migration_hash
  + env_profile_without_secrets
  + upstream_proof_fingerprints
)
```

Reuse rule:

```text
if proof.status == PASS
and proof.fp == recomputed_fp:
    reuse
else:
    execute
```

## 26.1 Why this matters

Without proof identity, orchestration sees only:

```text
wrapper failed/timed out
```

With proof identity, it sees:

```text
A PASS and still valid
B PASS and still valid
C PASS and still valid
D timed out

resume D
```

This directly eliminates a class of repeated broad work.

Official Bazel docs describe actions with declared inputs, commands, environment and output hashes, and an action cache keyed by hashes of action state. We are applying the same reproducibility principle to proof stages—not claiming Bazel itself is an agent system.

Source:

- Bazel Remote Caching official docs.
- https://bazel.build/remote/caching

---

# 27. Root cause G — missing observability prevents economic tuning

Operator can correctly say topology drifted, but cannot truthfully quantify:

```text
+27% cost
-41% efficiency
```

because required telemetry was not persisted consistently.

This is itself a production defect in the orchestrator.

## 27.1 OpenTelemetry mapping

OpenTelemetry GenAI conventions already define useful metadata around:

- model;
- input/output token counts;
- call duration;
- agent spans;
- tool execution spans.

Recommended trace tree:

```text
orchestration.task
  preflight
  route.select
  packet.build
  agent.invoke
    chat/model
    execute_tool
  candidate.validate
  mutation.apply
  proof.stage[*]
  acceptance
  checkpoint
```

## 27.2 Additional low-cardinality orchestration attributes

```text
orchestration.story_id
orchestration.task_class
orchestration.execution_mode
orchestration.route.requested
orchestration.route.resolved
orchestration.model
orchestration.effort
orchestration.packet_id
orchestration.packet_behavior
orchestration.oracle_strength
orchestration.integration_width
orchestration.seriality
orchestration.base_head
orchestration.worktree_id
orchestration.supervisor.ready
orchestration.failure_class
orchestration.replan_reason
orchestration.fallback_count
orchestration.patch_context_failures
orchestration.proof_stage
orchestration.proof_fp
orchestration.proof_cache_hit
orchestration.broad_gate_run_count
orchestration.accepted
```

Metrics:

```text
TIME_TO_READY
TIME_TO_FIRST_DISPATCH
TIME_TO_FIRST_WRITE
TIME_TO_FIRST_GREEN
TIME_TO_ACCEPTED_RESULT
MODEL_WALL_TIME
MCP_CALL_COUNT
READ/SEARCH_CALL_COUNT
MUTATION_CALL_COUNT
PATCH_FAILURE_COUNT
PROOF_CACHE_HIT_RATE
BROAD_GATE_RERUN_COUNT
REPLAN_COUNT
CAPACITY_FAILURE_COUNT
PROMPT_TOO_LARGE_COUNT
DEADLINE_COUNT
INPUT_TOKENS
CACHED_INPUT_TOKENS
OUTPUT_TOKENS
ESTIMATED_CREDITS
```

## 27.3 Privacy default

Do **not** record full prompt/tool contents by default. OpenTelemetry guidance explicitly notes prompt/tool content can contain sensitive data; metadata is sufficient for most routing economics.

Source:

- OpenTelemetry, `Inside the LLM Call: GenAI Observability with OpenTelemetry`, 2026-05-14.
- https://opentelemetry.io/blog/2026/genai-observability/

---

# 28. Field reports from the international Codex community

These are operational reports, **not controlled scientific evidence**. They are useful because they show the failure classes are plausible in real Codex deployments.

## 28.1 Oversized tool/request payload

`openai/codex#13270` reports a real `invalid_request_error` where a tool argument string exceeded a 1,048,576-character limit.

Implication:

```text
PROMPT_TOO_LARGE / ARG_TOO_LARGE
```

must be a typed failure with packet-splitting/context-reduction recovery, not generic retry.

Source:

- https://github.com/openai/codex/issues/13270

## 28.2 Large session stranded until compaction

`openai/codex#32533` describes a long session where changing reasoning effort caused a full resend and repeated `Request blocked` failures until compaction reduced context.

Implications:

- avoid unnecessary model/effort changes inside huge persistent threads;
- maintain compact external state capsule;
- proactively reduce context before full-resend transitions;
- treat compaction/context reset as explicit recovery strategy.

Source:

- https://github.com/openai/codex/issues/32533

## 28.3 Long tool-heavy turn loses continuity

`openai/codex#14824` reports repeated missing function-call outputs and session restart/resume during long, tool-heavy turns with repeated polling.

Implications:

- shorter behavior packets;
- external task state;
- avoid unbounded single turns with many polling/tool calls;
- preserve proof/session state outside one conversational trajectory.

Source:

- https://github.com/openai/codex/issues/14824

## 28.4 MCP lifecycle/process ownership

`openai/codex#30408` reports per-thread MCP child-process accumulation and argues for explicit ownership/lifecycle cleanup.

This does not prove our Windows supervisor failure had the same cause. It does support treating worker/MCP lifecycle as a first-class managed resource, not assuming process existence/cleanup is automatic.

Source:

- https://github.com/openai/codex/issues/30408

---

# 29. Enforced Orchestration Control Loop (EOCL)

## 29.1 State machine

```text
PREFLIGHT
  |
  v
READY
  |
  v
ROUTED
  |
  v
EXECUTING
  |
  v
PROVING
  |
  v
ACCEPTING
  |
  v
CHECKPOINTED
```

Exceptional states:

```text
BLOCKED
REPLAN
ABORTED
```

## 29.2 Transition table

| From | Event | To | Mutation allowed? |
|---|---|---|---|
| PREFLIGHT | required env/oracle ready | READY | no |
| PREFLIGHT | missing mandatory dependency | BLOCKED/REPLAN | no |
| READY | route selected | ROUTED | no |
| ROUTED | executor + ownership acquired | EXECUTING | route-specific |
| EXECUTING | candidate/implementation complete | PROVING | no new unplanned mutation |
| EXECUTING | typed failure | REPLAN | **no** |
| PROVING | all required proof green | ACCEPTING | no |
| PROVING | implementation defect | REPLAN | no until ownership rerouted |
| PROVING | external infra unavailable | BLOCKED | no |
| ACCEPTING | Sol accepts | CHECKPOINTED | checkpoint only |
| ACCEPTING | Sol rejects | REPLAN | no |
| REPLAN | explicit new route + ownership | EXECUTING | new route-specific |

## 29.3 Invariant

```text
NO ROUTE CHANGE WITHOUT STATE TRANSITION
NO WRITE-OWNER CHANGE WITHOUT OWNERSHIP TRANSFER
NO PROOF REUSE WITHOUT FINGERPRINT MATCH
NO PARALLEL WRITER WITHOUT ISOLATED WORKTREE
```

---

# 30. Execution modes

## 30.1 MCP_ONLY

Use when:

- exact transformation known;
- fresh model judgment unnecessary;
- search/build/test/generator/DB proof only;
- ChatWeb Sol already knows minimal causal patch.

Write owner:

```text
MCP
```

## 30.2 BOUNDED_CANDIDATE

Use for narrow/medium behavior with strong oracle.

```text
Mini low
or
Luna high
```

Model:

```text
no authoritative write
-> structured candidate
```

MCP:

```text
validate paths/base
-> atomic apply
-> proof
```

## 30.3 DEEP_SINGLE_LANE

Use for:

- high integration width;
- substantial implementation;
- long coherent code reasoning;
- high seriality where one lane is better than parallel workers.

Default deep lane:

```text
Codex Sol xhigh
```

Write model:

- preferably isolated worktree; or
- read-only candidate/diff if current bridge design requires it.

## 30.4 COORDINATED_MULTI_WORKTREE

Use only if:

- >=2 independent workstreams;
- contracts frozen;
- disjoint write ownership;
- supervisor ready;
- integration/review capacity sufficient.

This is an execution mode, not a default background service requirement.

---

# 31. Mode classifier

Suggested features:

```text
RISK
JUDGMENT
ORACLE_STRENGTH
INTEGRATION_WIDTH
SERIALITY
TOOL_DENSITY
PACKET_QUALITY
CONTEXT_SIZE
INDEPENDENT_WORKSTREAM_COUNT
CONTRACT_STABILITY
WRITE_OVERLAP
ENV_READY
SUPERVISOR_READY
MODEL_CAPACITY
CACHE_STATE
```

Pseudo-policy:

```text
if deterministic:
    MCP_ONLY

elif localized and strong_oracle and low_width:
    BOUNDED_CANDIDATE(Mini/Luna)

elif high_width or high_seriality or deep_coherent_work:
    DEEP_SINGLE_LANE(Sol xhigh)

elif independent_workstreams >= 2
     and contract_frozen
     and writes_disjoint
     and supervisor_ready:
    COORDINATED_MULTI_WORKTREE

else:
    ChatWeb Sol settles ambiguity before dispatch
```

---

# 32. Supervisor readiness gate

When mode requires Desktop coordination:

```text
assert coordination.startup_ok
assert coordination.ready
```

Before packet dispatch.

Proposed runtime result:

```json
{
  "coordination": {
    "mode": "desktop",
    "startup": "passed",
    "ready": true,
    "live": true,
    "supervisor_pid": 1234,
    "control_channel": "ready",
    "workspace_base": "<sha>",
    "checked_at": "..."
  }
}
```

Cache readiness for a short TTL, but invalidate immediately on:

- process exit;
- failed heartbeat;
- thread/app-server error;
- base/worktree identity change.

Do not re-probe full capability map every tool call.

---

# 33. Write ownership lease

A major missing guard is explicit mutation ownership.

Proposed task state:

```text
WRITE_LEASE
  owner: MCP | CODEX:<lane_id> | NONE
  mode: MCP_ONLY | BOUNDED_CANDIDATE | DEEP_SINGLE_LANE | MULTI_WORKTREE
  base_head
  worktree_id
  worktree_fp
  allowed_paths
  acquired_at
  expires_on_state_change
```

Every mutation operation must satisfy lease.

If deep lane fails:

```text
lease -> NONE
state -> REPLAN
```

Controller cannot simply resume feature writes until a new lease is created.

---

# 34. Typed recovery matrix

| Failure | Meaning | Allowed recovery | Forbidden recovery |
|---|---|---|---|
| `SUPERVISOR_NOT_READY` | chosen coordination lane unavailable | start/recover once or reclassify mode | silently implement via controller |
| `PROMPT_TOO_LARGE` | packet/context boundary invalid | compress state; split behavior packet; reduce evidence | same giant retry |
| `DEADLINE` | completion status unknown | freeze candidate/diff; grade external state; replan from evidence | assume all work useless |
| `CAPACITY` | service unavailable | one policy-approved alternate or Sol | unchanged retry loop |
| `PATCH_CONTEXT_AMBIGUOUS` | stale/ambiguous target | verify base; relocalize symbol; regenerate candidate | fuzzy patch broadening |
| `PATCH_CONTEXT_NOT_FOUND` | base drift/wrong localization | rebuild packet against current state | repeat stale patch |
| `CONTRACT_DRIFT` | downstream assumptions invalid | cancel dependent packet; refreeze contract | continue stale FE/BE branch |
| `PROOF_TIMEOUT` | proof transport/stage incomplete | reuse still-valid prior stages; resume missing node | rerun entire suite blindly |
| `INTEGRATION_DEFECT` | local proof insufficient | Sol replan at owning behavior boundary | patch random failing file |

---

# 35. Recovery for `PROMPT_TOO_LARGE`

This incident makes packet size an explicit runtime concern.

Correct policy:

```text
PROMPT_TOO_LARGE
-> record exact route/model/context estimate
-> classify packet entropy
-> create compact state capsule
-> remove already-settled/raw-history content
-> split by behavior dependency, not file count
-> retry ONCE on revised packet or change execution mode
```

Preferred split:

```text
shared semantic contract
then independent implementation packet(s)
```

Not:

```text
file1
file2
file3
file4
```

---

# 36. Recovery for deadline

Deadline is not equivalent to wrong code.

Based on prior Terra observations and current runtime lessons:

```text
interrupt
-> freeze worktree/diff
-> capture agent last evidence
-> run external focused proof
```

If proof green:

```text
candidate may be accepted despite turn timeout
```

If proof red:

- preserve useful partial evidence;
- replan from first actionable failure;
- do not replay full discovery.

---

# 37. Verification economics

Current wrappers optimize for “one command proves all” but not for agent/runtime time limits.

New optimizer target:

```text
MINIMIZE EXPECTED PROOF COST
subject to same acceptance coverage
```

Rules:

1. focused oracle immediately after behavior packet;
2. affected boundary checks next;
3. expensive build/runtime only when upstream prerequisite green;
4. independent stages can run in parallel if environment allows;
5. stage PASS persists by fingerprint;
6. broad suite once per final integrated fingerprint;
7. wrapper timeout does not erase completed proof.

---

# 38. Why broad suite once matters

Repeated broad suites have three costs:

- CPU/wall time;
- agent polling/tool context;
- noisy evidence that crowds out causal failures.

Broad suite should be treated as **acceptance authority**, not “ritual after every hunk”.

Flow:

```text
packet A -> focused A
packet B -> focused B
integration -> affected boundary
final fingerprint -> broad once
```

If final source fingerprint unchanged, do not run broad again just because another orchestration wrapper failed after the broad result was already proven.

---

# 39. Context discipline

Replace repeated repository/history reconstruction with explicit state.

## 39.1 One-time session preflight cache

Cache:

```text
REPO_ID
HEAD
BRANCH
WORKTREE
TOOLCHAIN
CODEX_BRIDGE_VERSION
AVAILABLE_MODELS/EFFORTS
SUPERVISOR_CAPABILITY
POSTGRES/DOCKER/PRISMA readiness
CANONICAL_PROOF_COMMANDS
```

Refresh only on invalidating event.

## 39.2 Delta context

Worker packet should include:

- exact current relevant code;
- current contract/invariants;
- failing proof;
- changes since previous packet.

Not full transcript.

---

# 40. Route ledger schema

Minimum durable row:

```text
TASK_ID
STORY_ID
TASK_CLASS
BEHAVIOR_PACKET
BASE_HEAD
WORKTREE_FP
EXECUTION_MODE
ROUTE_REQUESTED
ROUTE_RESOLVED
MODEL
EFFORT
ORACLE_STRENGTH
INTEGRATION_WIDTH
SERIALITY
PACKET_CONTEXT_BYTES
INPUT_TOKENS
CACHED_INPUT_TOKENS
OUTPUT_TOKENS
MODEL_WALL_MS
MCP_CALLS
SEARCH_READ_CALLS
MUTATION_CALLS
PATCH_FAILURES
SUPERVISOR_READY_AT_DISPATCH
FAILURE_CLASS
REPLAN_REASON
FALLBACK_COUNT
PROOF_STAGE_COUNT
PROOF_CACHE_HITS
BROAD_GATE_RUNS
TIME_TO_FIRST_DISPATCH
TIME_TO_FIRST_WRITE
TIME_TO_FIRST_GREEN
TIME_TO_ACCEPTED
FIRST_PASS_ACCEPTED
SOL_REPAIR_TURNS
INTEGRATION_DEFECT
CRITICAL_DEFECT
ESTIMATED_CREDITS
```

This enables empirical answer to:

- when does Mini beat Luna?
- when does Sol xhigh reduce rework enough to justify cost?
- when does Desktop parallelism reduce TTA?
- what is the cost of controller drift?
- how much do proof cache hits save?

---

# 41. Accepted-result economics

Do not optimize model price alone.

```text
EXPECTED_ACCEPTED_COST =
    model_generation
  + evidence_collection
  + tool_calls
  + mutation/application
  + verification
  + rework
  + fallback
  + integration
  + critical_path_latency_penalty
```

This incident likely incurred waste from:

- failed deep dispatch;
- micro-packet controller work;
- patch mismatch recovery;
- repeated scans;
- proof wrapper recovery.

But without route ledger we must not invent a percentage.

First objective of telemetry is to make next postmortem quantitative.

---

# 42. Why Desktop coordination should be conditional

Wrong extreme A:

```text
never use Desktop because supervisor can fail
```

Wrong extreme B:

```text
always keep BE/FE Desktop workers because feature is large
```

Correct:

```text
Desktop coordination is an execution mode selected by task shape.
```

Use it when:

- persistent context reuse is valuable;
- two or more leaves are genuinely independent;
- environment startup cost is amortized;
- isolated worktrees exist;
- integration bandwidth is available.

Avoid multi-lane Desktop when:

- semantics are changing step-to-step;
- one result changes assumptions of next;
- writers overlap;
- contract unstable;
- proof/integration is bottleneck.

For high-seriality financial work, one Sol xhigh deep lane + MCP oracle is often better.

---

# 43. Scientific evidence mapped to observed failures

| Observed issue | External evidence | Design consequence |
|---|---|---|
| multi-worker not necessarily useful | Google 180-config study | classify seriality/decomposability before parallelism |
| too many model switches/cascade | MTRouter | fewer switches; direct competent route |
| need route learning | ContextualRouter | route ledger + similar-task retrieval first |
| raw history/context drift | Ledger | explicit execution state + govern redundant re-execution |
| manager/executor truth mixing | LongHorizon-Harness | manager/executor/auditor separation |
| long context distraction | COMPASS | dedicated context/state manager/capsule |
| same-agent self-review | RETRACE | independent semantic/proof channel |
| excessive tool calls | ACL entropy/tool-use paper | reduce scans/reruns before tier tuning |
| concurrent edit interference | CAID | isolated workspaces + centralized integration |
| shared mutable checkout | Git worktree | per-writer worktree/HEAD/index |
| proof reruns | Bazel cache model | proof fingerprints / declared inputs |
| missing routing economics | OpenTelemetry GenAI | spans for model/tool/token/duration + custom orchestration attrs |
| coordination process not usable | Kubernetes readiness analogy | readiness gate before dispatch |

---

# 44. Field evidence mapped to recovery classes

| Codex field report | Reported failure class | Our guard |
|---|---|---|
| openai/codex#13270 | oversized tool argument/request | typed `PROMPT_TOO_LARGE`; packet split |
| openai/codex#32533 | large context/full resend blocked until compaction | compact state; avoid unnecessary effort switch; context-budget recovery |
| openai/codex#14824 | long tool-heavy turn loses tool-call continuity | shorter packet; external state/proof; bounded polling |
| openai/codex#30408 | MCP child lifecycle/resource ownership | explicit supervisor/worker lifecycle ownership |

Again: these issues are anecdotal/field evidence, not proof of the exact incident cause.

---

# 45. Proposed changes in Tools-Codex-web

No new public model-facing tools are required. Keep the compact 8-tool smart surface.

Implement internally under existing `agent_workflow` / task state.

## P0 — enforcement

### P0.1 Explicit execution state

Persist:

```text
orchestration_state
execution_mode
route
write_lease
base_head
worktree_fp
active_packet
replan_reason
```

### P0.2 Mode-specific readiness

Add internal:

```text
coordination.startup
coordination.ready
coordination.live
```

Desktop-coordinated mode may not enter `EXECUTING` until ready.

### P0.3 Controller mutation guard

Server rejects feature-scope mutation when another lane owns write lease or when state is `REPLAN`.

### P0.4 Typed failure normalization

Normalize:

```text
SUPERVISOR_NOT_READY
PROMPT_TOO_LARGE
DEADLINE
CAPACITY
BASE_DRIFT
PATCH_AMBIGUOUS
CONTRACT_DRIFT
PROOF_TIMEOUT
INTEGRATION_DEFECT
```

Each maps to policy, not free-form recovery.

### P0.5 Behavior packet identity

Packet stores:

```text
packet_id
behavior
scope
contract_fp
base_head
allowed_paths
proof_plan
```

---

# 46. P1 — proof DAG and observability

## P1.1 Proof stage registry

Represent broad verify wrappers as named stages.

## P1.2 Fingerprint/cache

Persist exact-input PASS results and reuse only when fingerprint matches.

## P1.3 OTel/route ledger

Record model/tool/proof spans and orchestration attrs.

## P1.4 State capsule output

Expose compact task state to ChatWeb and Codex rather than replaying history.

## P1.5 Checkpoint helper

After Sol accepts a stable behavior/story boundary:

- record proof capsule;
- recommend/create checkpoint according to user policy;
- story governance state remains independent.

---

# 47. P2 — adaptive orchestration after evidence accumulates

Only after P0/P1 make telemetry reliable:

1. nearest-similar-task route lookup;
2. class-specific Mini/Luna/Sol thresholds;
3. measured Desktop parallelism promotion;
4. model capacity/cold-warm cache-aware routing;
5. learned router only if simple retrieval/rules stop being sufficient.

---

# 48. Proposed `agent_workflow` internal contract

Conceptual extension:

```text
EXECUTION_CONTROL
  mode: auto | mcp_only | bounded_candidate | deep_single_lane | coordinated_multi_worktree
  require_coordination_ready: bool
  write_owner
  base_head
  worktree_fp
  packet_id
  proof_plan_id
```

Response:

```text
ORCHESTRATION
  state
  mode_requested
  mode_resolved
  route_requested
  route_resolved
  readiness
  write_lease
  active_packet
  failure_class
  replan_reason
  proof_summary
  telemetry_summary
```

Do not expose Mini/Luna/Terra/Sol as separate ChatWeb tools.

---

# 49. Router control loop pseudocode

```text
finish = Sol.define_finish_line()
state = PREFLIGHT

base = resolve_base_identity()
oracle = validate_oracle()
capabilities = cached_runtime_capabilities()
shape = classify_task_shape()

mode = select_execution_mode(shape)

if mode.requires_coordination:
    ready = check_coordination_readiness()
    if not ready:
        state = REPLAN
        mode = explicit_reclassify_or_block()

state = READY
route = select_route(mode, shape, ledger_history)
state = ROUTED

lease = acquire_write_lease(route, mode, base)
state = EXECUTING

result = execute_behavior_packet()

if result.failure:
    revoke_write_lease()
    state = REPLAN
    recovery = typed_recovery(result.failure)
    if recovery.has_positive_expected_value:
        route, mode = explicit_reclassify(recovery)
        goto ROUTED
    else:
        state = BLOCKED
        return

revoke_write_lease_if_execution_complete()
state = PROVING

proof = execute_missing_proof_nodes_only()

if proof.infrastructure_blocker:
    state = BLOCKED
    return

if proof.behavior_failure:
    state = REPLAN
    goto ROUTED

state = ACCEPTING
accept = Sol.accept(diff, proof, invariants)

if not accept:
    state = REPLAN
    goto ROUTED

state = CHECKPOINTED
record_route_ledger()
```

---

# 50. Mutation lease pseudocode

```text
def mutate(request):
    assert task.state == EXECUTING
    assert write_lease.active
    assert request.owner == write_lease.owner
    assert current_base == write_lease.base_head
    assert current_worktree_fp == write_lease.expected_fp_or_allowed_transition
    assert paths_subset(request.paths, write_lease.allowed_paths)

    apply_atomically(request)
    update_worktree_fp()
```

Controller-led emergency repair requires explicit:

```text
REPLAN
-> transfer lease to MCP
-> new packet/proof plan
```

---

# 51. Proof cache pseudocode

```text
def run_proof(stage):
    fp = fingerprint(stage.inputs, base, toolchain, config, upstream_proofs)

    cached = proof_store.get(stage.id, fp)
    if cached and cached.status == PASS:
        return cached.with(cache_hit=True)

    result = execute(stage.command)
    proof_store.put(stage.id, fp, result)
    return result
```

If wrapper-level timeout occurs:

```text
resume from first missing/invalid stage
```

not from stage 1.

---

# 52. Checkpoint policy for long story sequences

Recommended rule:

```text
CHECKPOINT WHEN:
  Sol accepted stable behavior boundary
  AND downstream packets will rely on it
```

Examples:

- US-109 backend/read control accepted -> checkpoint.
- US-110 UI contract accepted -> checkpoint.
- US-111 reconciliation proof accepted -> checkpoint.
- US-112 technical packet accepted but governance still pending -> checkpoint code with story `in_progress`.

This would reduce the mutation span carried into later stories without falsifying governance.

---

# 53. Harness / governance ordering

Proposed order per story:

```text
IMPLEMENT PACKET
-> FOCUSED PROOF
-> AFFECTED BOUNDARY PROOF
-> SOL ACCEPT
-> UPDATE HARNESS/STORY EVIDENCE
-> CHECKPOINT
```

Broad project-wide gate is placed at integration/release boundary, not repeated after every micro-edit.

Governance metadata updates should reflect truth, not be used to make a commit appear complete.

The choice to leave US-112 `in_progress` is therefore correct.

---

# 54. What should have happened in this incident

A counterfactual execution:

```text
1. Sol reads US-112 settled semantics.
2. Preflight selects DEEP_SINGLE_LANE.
3. Desktop/App Server readiness check fails because supervisor not ready.
4. State becomes REPLAN before any feature mutation.
5. Controller decides:
   a) recover Desktop once; or
   b) use direct App Server Sol xhigh single lane; or
   c) explicitly reclassify to MCP_ONLY only if Sol already has exact coherent implementation.
6. Backend behavior packet dispatched.
7. If prompt too large:
   REPLAN -> compact/split backend behavior, not file hunks.
8. Backend proof DAG green.
9. Freeze backend/OpenAPI contract + checkpoint.
10. Dispatch FE behavior packet.
11. FE proof green.
12. Integration proof executes only missing nodes.
13. Broad final gate once.
14. Sol accepts.
15. Technical checkpoint committed while US-112 can remain in_progress.
16. Route ledger persists timings/tokens/failures/proof cache hits.
```

---

# 55. What not to do next

Do not respond to this postmortem by:

- forcing Desktop on every task;
- adding more persistent workers;
- increasing Sol effort globally;
- turning all failures into Sol Ultra;
- splitting every feature into more files/tasks;
- making patch matching fuzzy;
- rerunning every broad suite after any timeout;
- writing more orchestration prose without server enforcement;
- building an ML router before reliable telemetry exists.

---

# 56. Rollout plan

## Phase A — enforce invariants first

Before next high-risk story:

```text
[ ] execution state machine
[ ] mode-specific readiness gate
[ ] write lease
[ ] explicit REPLAN on executor failure
[ ] base/worktree fingerprint
[ ] typed prompt/deadline/capacity/patch failures
```

## Phase B — proof economics

```text
[ ] split `verify:pfm-management` into registered stages
[ ] split `verify:bff-gate` into registered stages
[ ] proof fingerprints
[ ] proof cache
[ ] broad gate owner + once-per-fingerprint rule
```

## Phase C — observability

```text
[ ] OTel spans/events
[ ] route ledger
[ ] token/cache/wall metrics
[ ] proof cache-hit metrics
[ ] orchestration drift counter
```

## Phase D — behavior packet + checkpoint discipline

```text
[ ] packet behavior field
[ ] contract fingerprint
[ ] story-level checkpoint recommendation
[ ] isolated worktree for concurrent writers
```

## Phase E — tune models/topology only after data

```text
[ ] 20+ real task observations
[ ] paired class-specific comparisons
[ ] Desktop parallel vs single-lane on true parallel tasks
[ ] Mini/Luna/Sol accepted-result economics
```

---

# 57. Acceptance metrics for EOCL itself

Hard correctness metrics:

```text
SILENT_MODE_DRIFT = 0
WRITE_WITHOUT_ACTIVE_LEASE = 0
DEEP_FAILURE_WITHOUT_REPLAN_BEFORE_OWNERSHIP_TRANSFER = 0
PARALLEL_SHARED_CHECKOUT_WRITERS = 0
REUSED_PROOF_WITH_MISMATCHED_FP = 0
```

Efficiency metrics to establish baseline, then optimize:

```text
TIME_TO_FIRST_DISPATCH
TIME_TO_FIRST_GREEN
TIME_TO_ACCEPTED
MCP_CALLS / accepted behavior
SEARCH_READ_CALLS / accepted behavior
PATCH_FAILURES / accepted behavior
PROOF_CACHE_HIT_RATE
BROAD_GATE_RUNS / integrated fingerprint
MODEL_CREDITS / accepted behavior
SOL_REPAIR_TURNS
```

Do not set arbitrary percentage improvement until baseline is measured.

---

# 58. Benchmark plan after implementation

## 58.1 Study A — enforcement before/after

Compare next 10–20 high-integration stories with historical PFM tasks:

- silent mode drift;
- replan count;
- patch failures;
- broad reruns;
- TTA;
- model/tool cost.

## 58.2 Study B — behavior packets vs micro-packets

Matched tasks:

```text
BEHAVIOR_PACKET
vs
FILE/HUNK_PACKET
```

Measure:

- dispatch count;
- context bytes;
- patch ambiguity;
- rework;
- TTA;
- acceptance.

## 58.3 Study C — proof cache

Measure current wrapper baseline vs staged fingerprint DAG:

- executed stages;
- reused stages;
- wall time after late timeout/failure;
- duplicate build/test count.

## 58.4 Study D — Desktop coordination

Only tasks with true independent leaves:

```text
single Sol xhigh lane
vs
2 isolated coordinated worktrees
```

Measure total accepted-result time including integration/review—not worker finish time alone.

---

# 59. Updated decision matrix

| Task shape | Mode | Executor | Desktop supervisor required? |
|---|---|---|---|
| exact deterministic work | MCP_ONLY | MCP | no |
| tiny localized strong-oracle leaf | BOUNDED_CANDIDATE | Mini low | no |
| harder bounded leaf | BOUNDED_CANDIDATE | Luna high | no |
| high-width / high-seriality feature | DEEP_SINGLE_LANE | Sol xhigh | only if using Desktop-backed lane |
| independent frozen-contract leaves | COORDINATED_MULTI_WORKTREE | bounded lanes / Sol xhigh | yes |
| consequential unresolved reasoning | deep escalation | Sol max | mode-dependent |
| true extreme parallel decomposition | explicit extreme | Sol ultra | explicit + budget + readiness |

---

# 60. Updated operational checklist

Before mutation:

```text
[ ] finish line/invariants settled enough
[ ] authoritative branch/base resolved
[ ] task shape classified
[ ] oracle exists/works
[ ] execution mode selected
[ ] mode-specific dependencies READY
[ ] active write lease established
[ ] packet behavior/scope/proof defined
```

During execution:

```text
[ ] base/worktree identity remains valid
[ ] no out-of-scope writer
[ ] typed failures -> REPLAN
[ ] no unchanged retry
[ ] state capsule updated only with verified facts
```

Proof:

```text
[ ] focused proof first
[ ] proof stage fingerprint stored
[ ] cache valid PASS instead of rerun
[ ] broad gate once on final fingerprint
```

Acceptance:

```text
[ ] Sol checks finance/security/public-contract invariant
[ ] technical checkpoint separated from governance status
[ ] route ledger recorded
```

---

# 61. Final diagnosis

## What worked

- finance semantics remained carefully governed;
- US-112 did not falsely claim governance completion;
- implementation ultimately reached a clean GitHub checkpoint;
- constituent proof could be recovered after wrapper timeout;
- existing router/skill principles correctly identified Sol ownership of high-risk semantics and cautioned against blind retry/cascade.

## What failed

- coordination readiness was not enforced;
- selected execution mode could silently degrade;
- controller mutation authority was not state-bounded;
- packet granularity became micro-patch oriented;
- shared checkout accumulated wide mutable state;
- verification was not resumable at proof-stage level;
- telemetry was insufficient for quantitative accepted-result economics.

## Root cause

> **The orchestration layer lacked an executable control state.**

Not enough to know what the policy says. Runtime must know:

```text
what state am I in?
who owns writes?
which executor is ready?
what evidence is still valid?
what failure class occurred?
what transition is legally allowed next?
```

---

# 62. Final recommendation

Keep the model architecture already selected:

```text
CONTROL                  ChatWeb Sol
DETERMINISTIC            Coding Tools MCP
CHEAP PATCH              Mini low/no-tools
HARDER LEAF              Luna high/no-tools
DEEP CODE                Codex Sol xhigh
CROSS-FILE EXPERIMENT    Terra high
CONSEQUENTIAL            Sol max
PARALLEL EXTREME         Sol ultra
FINAL ACCEPTANCE         ChatWeb Sol + deterministic evidence
```

But upgrade its operational meaning:

```text
FROM:
policy-guided orchestration

TO:
state-enforced orchestration
```

The next optimization priority is therefore **not model selection**.

Priority order:

```text
1. enforce execution state + ownership
2. enforce mode-specific readiness
3. make recovery typed and explicit
4. make proof resumable/content-addressed
5. make context/state explicit and compact
6. add route/OTel telemetry
7. improve behavior packet boundaries/checkpoint discipline
8. then tune model/topology with real accepted-result data
```

This order best matches the incident evidence, prior local benchmarks and current external research.

---

# 63. Bibliography / external evidence

## Scientific / peer-reviewed / research

1. Kim, Y.; Liu, X. et al. **Towards a Science of Scaling Agent Systems: When and Why Agent Systems Work.** Google Research, 2026.  
   https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/

2. Zhang, Y. et al. **MTRouter: Cost-Aware Multi-Turn LLM Routing with History–Model Joint Embeddings.** ACL 2026. DOI: `10.18653/v1/2026.acl-long.2045`.  
   https://aclanthology.org/2026.acl-long.2045/

3. Varangot-Reille, C.; Bouvard, C.; Gourru, A. **Generalising LLM Routing using Past Performance Retrieval: A Few-Shot Router is Sufficient.** EACL 2026 SRW. DOI: `10.18653/v1/2026.eacl-srw.22`.  
   https://aclanthology.org/2026.eacl-srw.22/

4. Wang, Z. et al. **Turning Interaction History into Execution State: A Runtime Layer for Long-Horizon Coding Agents.** arXiv:2608.00808, 2026.  
   https://arxiv.org/abs/2608.00808

5. Ma, Z. et al. **LongHorizon-Harness: Advancing Long-Horizon Agents for Real-World Tasks.** arXiv:2608.01964, 2026.  
   https://arxiv.org/abs/2608.01964

6. Wan, G. et al. **COMPASS: Enhancing Agent Long-Horizon Reasoning with Evolving Context.** ACL 2026. DOI: `10.18653/v1/2026.acl-long.152`.  
   https://aclanthology.org/2026.acl-long.152/

7. Li, C. et al. **Independent Patch Verification for Coding Agents with a Bidirectional Reconstruct-and-Verify Framework.** arXiv:2608.08950, 2026.  
   https://arxiv.org/abs/2608.08950

8. Li, Z. et al. **Rethinking the Role of Entropy in Optimizing Tool-Use Behaviors for Large Language Model Agents.** ACL 2026. DOI: `10.18653/v1/2026.acl-long.1288`.  
   https://aclanthology.org/2026.acl-long.1288/

9. Geng, J.; Neubig, G. **Effective Strategies for Asynchronous Software Engineering Agents.** arXiv:2603.21489, 2026.  
   https://arxiv.org/abs/2603.21489

## Official engineering references

10. Git documentation — `git-worktree`.  
    https://git-scm.com/docs/git-worktree

11. Bazel documentation — Remote Caching / action cache and content-addressable outputs.  
    https://bazel.build/remote/caching

12. Kubernetes documentation — Liveness, Readiness, and Startup Probes.  
    https://kubernetes.io/docs/concepts/workloads/pods/probes/

13. OpenTelemetry — **Inside the LLM Call: GenAI Observability with OpenTelemetry**, 2026.  
    https://opentelemetry.io/blog/2026/genai-observability/

## International field reports — OpenAI Codex GitHub

14. `openai/codex#13270` — oversized tool-call argument / request string.  
    https://github.com/openai/codex/issues/13270

15. `openai/codex#32533` — large session/full resend blocked until compaction after effort change.  
    https://github.com/openai/codex/issues/32533

16. `openai/codex#14824` — long tool-heavy turn loses function-call continuity/session restarts.  
    https://github.com/openai/codex/issues/14824

17. `openai/codex#30408` — MCP process/thread lifecycle accumulation report.  
    https://github.com/openai/codex/issues/30408

---

# 64. Internal provenance

## Incident repository

```text
repo: uyenthudao2410-code/HR
branch: V_Finance
commit: 89bc4baddaa32614b4689c68e09595acc0f78923
message: feat(finance): deliver PFM cost control and fast entry
parent: 4435aa82e6abd9b1c1beacfd977efb73c20f5cfb
GitHub single-commit stats: +2803 / -117
compare file count: 43
```

## Governance

At authoritative `V_Finance` head:

```text
US-109 implemented
US-110 implemented
US-111 implemented
US-112 in_progress
```

## Existing Tools-Codex-web research

```text
docs/research/EXECUTOR_ROUTING_BENCHMARK_2026-08-12.md
docs/research/MODEL_ORCHESTRATION_RESEARCH_PHASE2_2026-08-12.md
docs/research/ORCHESTRATION_METHODOLOGY_EXPERIMENTS_AND_PRODUCTION_DECISION_2026-08-12.md
```

---

# 65. Decision record

**DECISION:** Keep adaptive model routing, but make orchestration a server-enforced state machine before further model/topology tuning.

**PRIMARY P0:** readiness gate + `REPLAN` enforcement + write ownership lease + base/worktree fingerprints.

**PRIMARY P1:** proof DAG/fingerprint/cache + OpenTelemetry/route ledger.

**PRIMARY WORKFLOW CHANGE:** behavior-level packets, one write owner, proof immediately after packet, broad gate once, checkpoint at stable story/contract boundaries.

**DESKTOP POLICY:** conditional execution mode; required readiness only when selected; multi-worktree only for genuinely parallel independent leaves.

**MODEL POLICY:** unchanged until telemetry demonstrates a better class-specific route.

**FINAL ACCEPTANCE AUTHORITY:** ChatWeb Sol + deterministic evidence.
