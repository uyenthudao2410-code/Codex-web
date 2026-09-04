# CODING-WEB — TRUSTED GOAL PURSUIT, SESSION CONTINUITY & PROBLEM RESOLUTION ECONOMICS MASTER PLAN

**Ngày:** 2026-09-01  
**Workspace:** `E:\DEV\Codex-web`  
**Git snapshot khi lập kế hoạch:** `main @ 30b7d1b971b65034d3e4c95568c970fcc0e9380c`, `origin/main` khớp tại thời điểm capture  
**Runtime quan sát:** Coding Tools MCP `0.4.3`, `smart-v3`, đúng `8` public tools  
**Trạng thái tài liệu:** `PLAN_ONLY / NO_RUNTIME_OR_EXPERIMENT_AUTHORITY`  
**Revision:** `R2 — UPSTREAM PRIMITIVE INTEGRATION OVERLAY`  
**Upstream evidence snapshot:** `yyjeqhc/webcodex main @ 039fecfe73b98506c0fc3b0df7e47be8a4233bac`; PR `#244` open tại thời điểm nghiên cứu, head `800fce417234e8e3b99b5a71f91eae12e2d396e8`. Trạng thái upstream là mutable evidence và phải revalidate trước khi port.  
**Phạm vi:** Hợp nhất bài toán theo đuổi mục tiêu dài hạn, ChatWeb session/context limit, ChatWeb/UI lag hoặc mất progress, resumption xuyên session, Goal-level economics, EGRI/P5 evaluation và các upstream primitives có positive expected value.  
**North Star:** `TTPR = Time to Trusted Problem Resolution` dưới correctness/security/business/authority floors.

---

# 0. Executive decision

## 0.1 Kết luận kiến trúc

Ba vấn đề đang được nhìn như ba feature riêng:

1. ChatWeb đôi khi dừng khi một RUN/WAVE hoặc một lần sửa đã xong dù Problem thực tế chưa được giải quyết;
2. ChatWeb có giới hạn session/context, session dài có thể lag hoặc buộc tạo chat mới;
3. tool card/progress UI có thể mất, lag hoặc không phản ánh đầy đủ execution đang chạy.

Thực chất đây là **một bài toán lifecycle và optimization chung**:

> **Logical Goal phải sống lâu hơn physical ChatWeb session, và execution/proof truth phải sống độc lập với ChatWeb UI.**

Kiến trúc hiện tại không cần thay controller. ChatWeb/Sol tiếp tục là semantic controller và final-acceptance authority cho coordinated work. Coding Tools MCP tiếp tục là durable execution/proof/authority plane. Codex/OpenCode/Mini/Luna/Terra/Sol lanes tiếp tục chỉ là executor/reviewer theo runtime policy.

Không xây thêm một “AI brain”, Goal Engine, second PRL database, peer Runtime hoặc public tool thứ chín.

Mapping chuẩn:

```text
Problem Thread          = durable Goal identity
Problem Revision        = exact current definition of DONE
EOCL RUN                = one engineering pursuit lineage
EOCL WAVE               = one attempt under a stable strategy/base/authority
ChatWeb Session         = replaceable controller endpoint/context carrier
Codex/provider lane     = delegated executor/reviewer
Proof/checkpoint        = technical evidence
Outcome receipt         = authoritative resolution evidence
RESOLVED_CONFIRMED      = Goal finish line
```

## 0.2 Optimization correction

Accepted-Result Economics không bị bỏ. Nó trở thành **sub-ledger** của Problem Resolution Economics.

Không tối ưu đơn vị cuối cùng là:

```text
accepted RUN
```

Mà là:

```text
Problem Revision
  -> Trusted Resolution
```

Một Problem có thể đi qua nhiều ChatWeb sessions, RUNs, WAVEs, model lanes, tool calls, replans và recoveries. Tất cả resource/time/rework của chúng phải được quy về cùng Problem Revision khi exact linkage tồn tại.

Objective lexicographic:

```text
1. correctness / safety / business / authority floors
2. Trusted Problem Resolution
3. minimize TTPR / tail TTPR
4. minimize expected total resolution resource cost
5. minimize human/operator burden
6. minimize complexity / maintenance burden
```

Session count, token count, number of tools, number of model calls, LOC hoặc raw tool latency không được trở thành North Star độc lập.

## 0.3 Quyết định quan trọng về Resolution Capsule

Resolution Capsule phải tách thành hai lớp semantic:

### Continuity Core — infrastructure chung

Bắt buộc để session mới tiếp tục đúng Goal:

- Problem/Revision exact identity;
- objective + acceptance-criteria identity;
- protected invariants/constraints identity;
- current RUN/WAVE nếu có;
- accepted criterion/subclaim coverage;
- unresolved gap;
- latest material counterevidence/reopen state;
- current authority/write/acceptance state;
- source/runtime freshness;
- next critical action/discriminator;
- explicit omissions/refresh requirements.

Continuity Core là infrastructure, không phải một treatment AI riêng.

### EGRI Enrichment — treatment/advisory

Có thể bao gồm:

- richer Problem Frame;
- ranked hypotheses;
- Workspace Evidence Index packet;
- retrieved Case Memory;
- contrast/negative-transfer warnings;
- decision-changing discriminator assistance.

Phân tách này bắt buộc để P5 sau này không nhầm causal effect của “resume đúng” với causal effect của “reasoning intelligence tốt hơn”.

## 0.4 Upstream adoption doctrine

Upstream chỉ được dùng như **evidence source + primitive library**, không phải canonical architecture authority của Codex-web.

Adoption rule:

```text
UPSTREAM IDEA/COMMIT/PR
  -> identify local bottleneck it might reduce
  -> parity audit current local capability
  -> define local invariant/contract
  -> port the smallest primitive only when a real gap exists
  -> prove against current local Goal/TTPR oracle
  -> retain, simplify, or reject from evidence
```

Không được:

- cherry-pick hàng loạt chỉ vì upstream mới hơn;
- đưa upstream AgentTask/Agent/Conversation state machine vào local khi Problem/RUN/WAVE đã sở hữu semantics tương đương;
- tăng từ 8 tool lên upstream public surface lớn hơn chỉ để đạt parity tên API;
- chuyển authority từ ChatWeb/EOCL sang subsystem upstream;
- coi PR chưa merge là stable specification;
- biến upstream comparison thành feature-count competition.

---

# 1. Current baseline và các constraint phải giữ

## 1.1 Current live/source snapshot dùng để lập kế hoạch

Tại capture R2 của kế hoạch:

- workspace: `E:\DEV\Codex-web`;
- branch: `main`;
- HEAD: `30b7d1b971b65034d3e4c95568c970fcc0e9380c`;
- `origin/main` cùng HEAD;
- worktree dirty và live snapshot R2 ghi nhận `71` changed/untracked entries, bao gồm runtime ledgers/reports, PRL, usage/accounting, live-control và research docs;
- Runtime: `0.4.3`, `smart-v3`, đúng `8` public tools;
- current workspace projection không có active task;
- PRL/Problem Resolution, usage accounting và live-control source đang cùng có uncommitted changes;
- semantic localization hiện `unavailable` với typed reason `NATIVE_LSP_BINDING_NOT_CONFIGURED`.

Do đó implementation không được reset/clean/rewrite unrelated work. Mỗi source wave phải xác định exact owned paths và dùng write lease/adoption semantics hiện hành.

## 1.2 Authority invariants

Không thay đổi:

```text
User Contract
  -> Problem Revision / PRL
  -> ChatWeb/Sol CONTROL_OWNER + ACCEPTANCE_OWNER
  -> EOCL RUN/WAVE + WRITE_LEASE
  -> deterministic proof/checkpoint
  -> runtime/live currentness
  -> independent/user outcome
```

Không layer mới nào được tự:

- grant write authority;
- accept RUN/WAVE;
- change Problem Revision;
- override business semantics;
- promote route/model;
- declare Trusted Resolution;
- manufacture context/token certainty;
- infer current source/runtime from stale history.

## 1.3 Public contract invariant

Giữ đúng 8 smart-v3 tools:

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

Goal pursuit, controller-knowledge checkpoint, session reattach, rotation readiness, Problem economics, typed large-result handoff và EGRI projector phải nằm sau existing tools/actions hoặc internal projection. Chỉ thay public contract nếu natural evidence chứng minh không thể giải bài toán bằng current surface.

## 1.4 Host boundaries

Không claim khả năng mà ChatWeb host không cung cấp:

- không tăng hard ChatGPT context limit từ MCP;
- không tùy ý tạo một ChatGPT model turn mới sau khi browser/session đã dừng nếu host không có wake API;
- không gọi heuristic là exact context pressure;
- không dùng DOM/OCR để giả structured usage authority.

Mục tiêu là làm cho session limit **không còn là lifetime limit của Goal**, không phải “unlock ChatGPT context window”.

---

# 2. Unified causal model

## 2.1 Failure chain hiện cần phá

```text
Long-lived Problem
  -> ChatWeb accumulates transcript/tool payload
  -> context pressure / UI lag / model-visible bloat
  -> progress card lost or session deteriorates
  -> new chat/session required
  -> manual history reconstruction
  -> stale/wrong assumptions or duplicated localization
  -> wrong frame / rework / extra RUNs
  -> Accepted RUN may still occur
  -> Problem still not resolved
  -> TTPR and total cost rise
```

## 2.2 Target chain

```text
Problem Revision remains durable
  -> ChatWeb Session A controls
  -> material controller knowledge advances only at durable checkpoints
  -> read/search/poll hot paths do not manufacture knowledge revisions
  -> execution/proof persists in Runtime
  -> Continuity Core stays current
  -> Session A can be rotated when safe
  -> ChatWeb Session B reattaches exact Goal
  -> stale/missing controller knowledge is recovered by bounded delta/current handoff
  -> only bounded decision state is reconstructed
  -> active jobs/results are re-observed, not restarted
  -> same Goal pursuit continues
  -> full criteria + falsifier + independent outcome
  -> RESOLVED_CONFIRMED
```

## 2.3 Goal is not RUN

Critical invariant:

```text
Wave failure      != Goal failure
RUN failure       != Goal failure
Session end       != Goal failure
UI card loss      != Goal failure
Runtime reconnect != Goal failure
```

Goal stops only through a legitimate Problem-level state:

```text
RESOLVED_CONFIRMED
BLOCKED with explicit external/missing-authority reason
ABANDONED / superseded by explicit user authority
```

Technical checkpoint hoặc accepted RUN không tự đóng Goal.

---

# 3. Canonical correlation model — Problem first

## 3.1 Không dùng tree Session-first làm truth tối cao

Token master hiện có Session -> Turn -> TaskContext -> RUN/WAVE correlation. Điều đó hữu ích cho host telemetry nhưng không đủ làm resolution denominator vì một Problem có thể span nhiều sessions, và một session cũng có thể chứa nhiều Problems.

Cần một **derived correlation graph**, không phải authority database mới:

```text
Workspace
  |
  +-- Problem Thread P
       |
       +-- Problem Revision R
            |
            +-- Controller Knowledge Checkpoints
            +-- exact host turns / conversation epochs
            +-- ChatWeb session/endpoint observations
            +-- TaskContexts
            +-- one or more primary/secondary RUNs
            |    +-- WAVEs
            |    +-- delegated lanes/jobs
            |    +-- proof/checkpoint
            |
            +-- reopen/revise/counterevidence events
            +-- outcome receipt
            +-- resolution economics projection
```

Exact linkage only. Timestamp proximity không được cấp canonical attribution.

## 3.2 Required identities

Reuse existing identities wherever possible:

```text
workspace_id
problem_id
problem_revision
contract_fingerprint
criteria_fingerprint
controller_knowledge_revision / continuity_revision
task_context_id
task_id
run_id
wave_id
session_id when host exposes it
conversation_epoch
turn_id
trace_id
invocation_id
operation_id / command_id / job_id
delegation_id
checkpoint_id
proof_id / proof_fingerprint
```

Nếu host không expose a stable `session_id`, keep it `unknown` and use attested turn/trace + local conversation epoch without pretending exact product-session identity.

## 3.3 Controller-knowledge identity is not token identity

`controller_knowledge_revision` là durable semantic watermark, không phải:

- turn counter;
- tool-call counter;
- token counter;
- approximate context usage;
- session age;
- EventLog sequence copied mechanically.

Nó chỉ advance khi canonical policy xác định rằng một durable state transition làm thay đổi material decision knowledge mà một resumed controller cần biết.

---

# 4. Goal Pursuit semantic layer

## 4.1 Không thêm Goal state machine mới

Canonical Problem states vẫn thuộc PRL. Goal Pursuit chỉ là bounded **derived projection**.

Suggested projection:

```yaml
goal_pursuit:
  problem_id:
  problem_revision:
  contract_fingerprint:
  resolution_state:

  completion:
    criteria_total:
    criteria_satisfied:
    criteria_unresolved:
    criteria_blocked:
    exact_coverage_status:

  execution:
    primary_run_id:
    current_wave_id:
    run_state:
    active_operation_count:
    active_delegation_count:

  next:
    next_critical_gap:
    next_action_type:
    next_action_summary:
    decision_state_provenance:

  continuity:
    current_knowledge_revision:
    controller_ack_revision:
    continuity_status:
    controller_status:
    safe_to_rotate_chatweb:
    capsule_status:
    resume_ready:

  stop:
    legitimate_stop: true|false
    reason: RESOLVED|BLOCKED|ABANDONED|NONE
```

## 4.2 Pursuit rule

```text
IF current Problem Revision is not RESOLVED_CONFIRMED,
not BLOCKED by a valid explicit condition,
and not ABANDONED/superseded,
THEN the Goal is not finished.
```

Within an active controller turn, the system must return/derive the next critical action instead of silently treating completion of one workflow as completion of the Goal.

## 4.3 No silent idle

An unfinished Goal may be:

- executing;
- waiting for proof;
- waiting for acceptance;
- waiting for controller/session reattach;
- waiting for external/user input;
- blocked by explicit condition.

It may **not** become semantically “done/idle” solely because the most recent tool call returned successfully.

Because ChatGPT cannot necessarily be auto-woken, `WAITING_CONTROLLER` is a projection/presentation condition, not a new PRL authority state.

## 4.4 Next Critical Action rules

Priority:

```text
1. currentness/authority blocker
2. controller-knowledge recovery required
3. unresolved acceptance criterion
4. material counterevidence contradiction
5. missing decision-changing discriminator
6. required execution/proof
7. closure falsifier
8. independent/user outcome
9. resolution confirmation
```

The next action must be derived from exact Goal state or explicitly `UNKNOWN`; it must not be generated from a generic narrative summary and stored as fact.

---

# 5. Continuity Core Capsule v1

## 5.1 Purpose

Enable a new ChatWeb context/session to reconstruct **decision state**, not transcript.

No raw chat replay, private reasoning, giant logs or source dumps.

## 5.2 Mandatory core

Within existing bounded handoff contract, priority order:

1. exact workspace + Problem/Revision identity;
2. contract/criteria fingerprints;
3. current controller-knowledge revision and capsule generation identity;
4. objective and protected invariants when bounded representation is available;
5. current resolution state;
6. current RUN/WAVE + authority state;
7. accepted criteria/subclaims + exact proof refs;
8. material counterevidence/reopen flags;
9. unresolved gap;
10. next critical action/discriminator;
11. source/runtime currentness at record time;
12. read-time `MATCHED|MISMATCHED|UNKNOWN` currentness;
13. explicit omission/refresh receipts.

## 5.3 Existing 8 KiB boundary

Do not raise the 8 KiB outer handoff cap by default.

Algorithm:

```text
mandatory identity/authority/currentness core
  -> controller-knowledge watermark
  -> mandatory decision state
  -> proof/event refs
  -> bounded contract embed
  -> optional Frame detail
```

A section that does not fit is omitted whole with exact identity/byte count/reason/refresh requirement; never silently truncate semantics.

## 5.4 Core vs enrichment

Persist explicit section provenance:

```text
CONTINUITY_CORE
EGRI_ENRICHMENT
```

A session resume may proceed when Continuity Core is valid even if EGRI enrichment is absent, disabled or experiment-control assigned.

This is essential for scientific separation.

## 5.5 Capsule is snapshot; knowledge revision is continuity watermark

Hai primitive bổ trợ nhau nhưng không trùng:

```text
Continuity Core Capsule
  = bounded current decision-state snapshot

Controller Knowledge Revision
  = durable watermark telling what material state the controller has acknowledged
```

Resume có thể dùng:

```text
ack == current
  -> use current capsule, no recovery delta needed

ack behind current
  -> bounded material-state delta + current capsule

ack missing/invalid/future/history-lost
  -> fail-open for read, fail-closed before dependent mutation;
     return compact current handoff + explicit recovery status
```

---

# 6. Same-role ChatWeb controller reattach

## 6.1 Objective

New ChatWeb session becomes a new endpoint/context carrier for the **same logical control role**, not a new architecture authority.

## 6.2 Preferred flow

```text
SESSION A
  -> request/derive rotation readiness
  -> record exact handoff/continuity capsule
  -> ACK current controller-knowledge revision when protocol permits
  -> ensure active execution state is durable
  -> preserve RUN/WAVE/jobs/proofs
  -> release or expire outgoing controller lease according to current contract

SESSION B
  -> workspace_context exact workspace
  -> resolve explicit Problem ID or one unambiguous active Goal
  -> fetch current Problem Revision
  -> present last-known controller knowledge revision when available
  -> fetch Continuity Core + bounded recovery if behind/unknown
  -> inspect active RUN/WAVE/jobs/proofs
  -> explicit same-role controller reattach/fencing transition
  -> continue next critical action
```

## 6.3 No unsafe implicit selection

If multiple open Goals exist for the workspace, “resume active Goal” must fail closed to a bounded candidate list/selection requirement. Never pick “latest RUN” by timestamp.

If the Problem is explicit, resolve only that exact Problem/Revision.

## 6.4 Reattach preconditions

- workspace identity exact and authorized;
- Problem Revision current or explicit refresh performed;
- controller-knowledge continuity reconciled;
- capsule mandatory core valid;
- source/runtime currentness not contradicted;
- active controller lease transfer legal;
- no acceptance ownership ambiguity;
- no unbound conflicting write authority;
- active jobs bound to exact RUN/WAVE or reported separately as unknown/unowned.

## 6.5 Failure behavior

Typed outcomes, for example:

```text
GOAL_SELECTION_REQUIRED
GOAL_ALREADY_RESOLVED
PROBLEM_REVISION_STALE
CONTROLLER_KNOWLEDGE_BEHIND
CONTROLLER_KNOWLEDGE_INVALID
CONTROLLER_KNOWLEDGE_HISTORY_LOST
CAPSULE_MISSING
CAPSULE_STALE
CAPSULE_CONFLICTED
CONTROLLER_TRANSFER_BLOCKED
WORKSPACE_SCOPE_MISMATCH
ACTIVE_ACCEPTANCE_REQUIRES_REATTACH
EXECUTION_IDENTITY_UNCERTAIN
```

No automatic replay/reset/restart.

---

# 7. UI-independent execution and progress truth

## 7.1 Fundamental invariant

```text
CHATWEB TOOL CARD / UI STATE != EXECUTION AUTHORITY
```

Closing/reloading/losing a card cannot be equivalent to cancelling or forgetting execution.

## 7.2 Durable execution handles

Long-running operations must expose/reuse existing durable identities:

- `operation_id`;
- `command_id`/`session_id`;
- managed job ID;
- delegation/lane ID;
- RUN/WAVE owner;
- terminal receipt.

## 7.3 Retained bounded output

Do not send growing stdout/log/history repeatedly into ChatWeb.

Use:

```text
bounded head/tail
output_ref
cursor/continuation
eviction/gap metadata
artifact refs
terminal summary
```

Re-observe from exact handle. Do not restart a job just because the previous model turn lost its display card.

## 7.4 Typed large-result handoff

Current local source-fenced continuation machinery should be enriched so a truncated result tells the controller **how to continue without repeating the broad read**.

Canonical shape should carry at least:

```yaml
large_result_handoff:
  kind: DIFF_PAGE | OUTPUT_PAGE | EVIDENCE_PAGE
  source_identity:
  scope_identity:
  reason: BYTE_BUDGET | HUNK_COUNT | LINE_BUDGET | OUTPUT_RETENTION_BOUND
  next_operation:
  continuation:
  has_more:
  recoverability:
    continuation_recovers_all_omitted_data: true|false
  narrow_scope_hint:
```

If a single hunk/record itself was line-truncated and paging cannot recover omitted bytes, this must be explicit; continuation must never imply completeness it cannot provide.

## 7.5 Live projection

`live_control`/Execution Control Center fast path should expose only bounded current truth:

```text
Goal identity/status
current controller-knowledge revision / continuity status
current RUN/WAVE
current step / next step
active operations/jobs/delegations
last material event sequence/time
write/controller/acceptance authority
proof/acceptance state
continuity/rotation readiness
recent usage/context delta when authoritative
snapshot source/age/freshness
```

No whole-ledger scan, no repeated Git/OS census on every renderer poll.

## 7.6 Presentation semantics

UI state classes should distinguish:

```text
EXECUTING
WAITING_PROOF
WAITING_ACCEPTANCE
WAITING_CONTROLLER
RECOVERY_REQUIRED
BLOCKED
RESOLVED
UNKNOWN/STALE TELEMETRY
```

`UNKNOWN/STALE` presentation does not imply process stopped.

---

# 8. Context pressure, lag and rotation readiness

## 8.1 Exact measurement first

Continue current ChatWeb usage bridge program.

If host exposes structured controller usage:

- bind exact receipts to turn/trace/session/problem/run;
- preserve provider/client provenance;
- calculate exact coverage;
- support context/usage warning policy only under sufficient exact semantics.

If host does not expose exact context/window utilization:

```text
context_pressure = UNKNOWN / UNOBSERVED
```

Do not derive a fake “72% ChatGPT context”.

## 8.2 Heuristic signals are allowed only as heuristic

Useful non-authoritative signals:

- turn count;
- cumulative model-visible tool bytes;
- number/size of large tool results;
- session age;
- host/tool error incidence;
- rolling observed controller-gap latency;
- repeated truncation/continuation;
- explicit user request to rotate.

Label them:

```text
rotation_signal_source = heuristic
```

never `exact_context_pressure`.

## 8.3 Rotation readiness != rotation trigger

Two independent questions:

### Should we rotate?

Based on exact host usage when available or a labelled heuristic/operator decision.

### Can we rotate safely?

Based only on durable state:

- Continuity Core current;
- controller knowledge reconciled or recoverable;
- active job handles durable;
- no uncontrolled acceptance boundary;
- controller/write leases understood;
- next critical action reconstructable;
- no conflicted Problem Revision.

`safe_to_rotate_chatweb` must remain an authority/continuity decision, not a token threshold.

## 8.4 Rollout order

1. manual rotation only;
2. advisory warning;
3. shadow recommendation;
4. controlled study;
5. auto-handoff/rotation only after representative evidence of positive value and zero material state loss.

Current `auto-handoff=OFF` remains correct until the later gate passes.

---

# 9. Problem Resolution Economics vNext

## 9.1 Denominator correction

Current per-RUN Accepted-Result Economics stays available, but new top-level unit is:

```text
(problem_id, problem_revision)
```

## 9.2 Problem-level resource projection

For exact-linked events:

```yaml
problem_resolution_economics:
  outcome:
    resolved_confirmed:
    reopen_count:
    false_closure_count:

  time:
    ttoc_wall_ms:
    restricted_ttpr_active_ms:
    execution_ms:
    proof_ms:
    acceptance_ms:
    controller_gap_ms_observed:
    resume_ms:

  topology:
    chatweb_sessions_observed:
    conversation_epochs:
    controller_knowledge_checkpoints:
    controller_recovery_events:
    run_count:
    wave_count:
    replan_count:
    rejected_wave_count:
    rotation_count:

  resources:
    controller_tokens_exact_when_available:
    provider_tokens:
    model_visible_tool_bytes:
    recovery_delta_bytes:
    large_result_continuation_bytes:
    monetary_cost_complete_when_available:

  continuity:
    capsule_build_ms:
    capsule_bytes:
    resume_attempts:
    resume_successes:
    stale_ack_recoveries:
    invalid_ack_recoveries:
    duplicate_localization_after_resume:
    repeated_tool_reads_after_resume:

  human:
    user_correction_turns:
    manual_resume_actions:
    manual_fix_required:

  coverage:
    controller_usage:
    provider_usage:
    tool_invocation:
    problem_attribution:
    session_identity:
    continuity_revision:
    outcome_receipt:
```

Missing = unknown/null, not zero.

## 9.3 Rework accounting

All exact-linked rejected/REPLAN waves remain part of Problem cost, including resources spent before a later successful RUN.

A new RUN does not reset the cost denominator.

## 9.4 Session overhead accounting

Measure only what can be attributed:

- capsule build/delivery;
- knowledge recovery/delta delivery;
- resume reconstruction time;
- repeated localization queries after resume;
- duplicate model-visible context delivery;
- manual operator action;
- observed controller idle gaps when same clock/provenance exists.

Do not label every time gap as avoidable session cost.

## 9.5 Optimization function

Do not use one blended scalar before correctness/safety gates.

Operating order:

```text
Trusted outcome floor
  -> first-pass trusted / false closure
  -> restricted TTPR tail
  -> total Problem resource economics
  -> continuity overhead
  -> human burden
  -> simplicity
```

Session count is diagnostic. Two short, clean sessions may be superior to one overloaded session.

---

# 10. Experimental-design correction for EGRI/P5

## 10.1 Why current treatment must be refined

If Treatment receives a Resolution Capsule while Control must reconstruct after a session boundary from raw context, observed benefit mixes:

- continuity infrastructure effect;
- EGRI reasoning effect.

This creates causal ambiguity.

## 10.2 New treatment separation

### Common infrastructure for both arms

- Problem Revision;
- EOCL/authority;
- controller-knowledge checkpoint/recovery semantics;
- Continuity Core Capsule;
- exact same-role resume mechanism;
- UI-independent execution/progress;
- counterevidence safety doctrine if accepted as a safety floor;
- same measurement/usage instrumentation.

### Control

- bounded current repository workflow;
- no Workspace Evidence Index injection;
- no Resolution Case Memory injection;
- no EGRI enrichment.

### EGRI Treatment

- Continuity Core plus EGRI Enrichment;
- Workspace Evidence Index;
- <=3 applicability-gated Case Memory records;
- richer decision-state/discriminator support.

## 10.3 Session-boundary stratification

Every natural/P5 row should record:

```text
session_boundary_occurred
rotation_count
resume_core_used
controller_knowledge_revision_before
controller_knowledge_revision_after
controller_recovery_kind
resume_success
controller_usage_coverage
cache_stratum
```

For causal analysis, either stratify by session-boundary condition or freeze a design that makes continuity core common and independent from treatment assignment.

## 10.4 Auto-rotation is a separate treatment

Do not bundle “automatic context/session rotation policy” into EGRI Treatment v1. It is a separate policy question and should receive a distinct manifest/treatment identity only after manual/advisory rotation is proven safe.

---

# 11. Integrated implementation program

The following program supersedes neither `CURRENT_STATE.md` nor accepted source history. It integrates the overlap of current Token/Economics, EGRI plans và selected upstream primitives.

Use prefix `TG` in planning documents to avoid colliding with existing EGRI W0-W9 labels.

---

## TG0 — Semantics freeze, upstream parity inventory and dirty-source reconciliation

### Objective

Freeze the combined architecture before more source work.

### Work

- capture exact branch/HEAD/worktree fingerprint;
- classify current dirty paths by existing workstream/owner;
- record upstream evidence snapshot and exact commit/PR state used for each proposed primitive;
- classify every upstream candidate as `ADOPT_SEMANTICS`, `PARITY_AUDIT`, `DEFER`, or `REJECT_AS_DUPLICATE`;
- review current Resolution Capsule candidate;
- freeze definitions for Goal, Problem Revision, Controller Knowledge Revision, Continuity Core, EGRI Enrichment, session/endpoint, RUN, WAVE, Trusted Resolution;
- freeze Problem-first correlation semantics;
- freeze context-checkpoint policy vocabulary;
- prohibit a second Goal/AgentTask database/state machine;
- freeze missingness/provenance semantics;
- identify exact source owners for PRL, coordination, live-control, edit/continuation and usage changes.

### Exit

- one reviewed semantic contract;
- one upstream adoption matrix bound to exact evidence snapshot;
- no overlapping writer ambiguity;
- current capsule candidate accepted/reworked/rejected under one owned wave;
- 8-tool contract preserved.

---

## TG1 — Problem-first correlation and Goal Pursuit projector

### Objective

Make Problem Revision the resolution denominator and expose current Goal state without new authority.

### Work

- derived exact joins: Problem Revision ↔ controller-knowledge checkpoints ↔ RUN/WAVE ↔ host turns/sessions ↔ proofs/outcome;
- implement `goal_pursuit` bounded projection;
- criterion coverage from canonical proof/coverage facts;
- exact unresolved/blocked/stop semantics;
- next critical gap/action with typed provenance;
- multiple-open-Goal ambiguity handling;
- no latest-timestamp inference;
- surface current knowledge revision and whether controller recovery is required without treating this as authority.

### Candidate surfaces

- `problem_lineage.py` / extracted domain module;
- `coordination.py` / task-control projection;
- `orchestration_ledger.py` or read-only query helpers;
- `live_control.py` bounded consumer;
- tests for Problem/RUN separation.

### Exit

Fixture and current read model can answer:

```text
What Goal is this work serving?
Is it actually finished?
Which criterion/gap remains?
What durable knowledge revision defines the current decision state?
What is the exact next state/action class?
```

without reading transcript.

---

## TG2 — Controller Knowledge Checkpoint + Continuity Core Capsule

### Objective

Close the minimum safe resumption state independently of EGRI enrichment and prevent read/search/poll hot paths from inflating continuity history.

### Work A — controller knowledge policy

Define semantic policy independent of raw tool count:

```text
NO_ADVANCE
ADVANCE
RECOVERY_ONLY
CONSERVATIVE_UNKNOWN
```

Initial intended behavior:

```text
ordinary read/search/discovery/status/poll/page continuation
  -> NO_ADVANCE

material durable Problem/contract/coverage/authority transition
that changes resumed-controller decision state
  -> ADVANCE

reattach/resume/recovery read
  -> RECOVERY_ONLY unless it itself commits a material state change

unclassified mutable/control action
  -> CONSERVATIVE_UNKNOWN until policy is explicit
```

The exact event/tool table must be frozen in TG0 before implementation. Do not copy upstream per-tool names mechanically.

### Work B — checkpoint record

Persist only bounded durable facts required to recover knowledge:

```yaml
controller_knowledge_checkpoint:
  workspace_id:
  problem_id:
  problem_revision:
  revision:
  prior_revision:
  material_event_identity:
  material_state_fingerprint:
  capsule_fingerprint:
  source_fingerprint:
  runtime_behavior_fingerprint:
  created_at:
```

Do not persist raw prompt, transcript, chain-of-thought or large tool outputs.

### Work C — ACK/recovery semantics

```text
ACK exact current
  -> no recovery payload

ACK behind current
  -> bounded material-event delta if retained and complete
  -> current capsule/reference

ACK missing / invalid / future
  -> compact current handoff + typed status
  -> no retroactive mutation permission

retention/history gap
  -> HISTORY_LOST=true
  -> current capsule + refresh requirements
```

ACK acceptance and checkpoint advancement are separate operations. A stale ACK must not itself create a new checkpoint.

### Work D — Continuity Core

- split core/enrichment schema/provenance;
- source-fence all mandatory identities;
- deterministic budget/omission order under 8 KiB outer limit;
- exact-read refresh status;
- stale/conflicted blocking;
- prevent caller override;
- no transcript/private reasoning.

### Required resumption fixture

Context A creates a Problem state with:

- at least one satisfied criterion;
- one invalidated assumption/counterevidence;
- one unresolved gap;
- one active or recently terminal RUN/WAVE;
- at least two durable knowledge revisions;
- exact next action.

Context B receives only last ACK + Continuity Core/bounded recovery + current repository packet and must reconstruct sealed expected facts.

### Exit

- `CONTROLLER_KNOWLEDGE_CHECKPOINT_POLICY_PASS`;
- `STALE_ACK_BOUNDED_RECOVERY_PASS`;
- `READ_HOT_PATH_NO_REVISION_INFLATION_PASS`;
- `CONTINUITY_CORE_RESUMPTION_PASS` on exact source fingerprint.

---

## TG3 — Same-role ChatWeb reattach protocol

### Objective

A new ChatWeb session can take over the same Goal without changing semantic authority topology.

### Work

- define exact controller endpoint/session observation contract;
- bind new task context to same workspace + Problem;
- accept/reconcile last-known controller knowledge revision;
- explicit controller fencing transition/reacquisition;
- preserve RUN/WAVE/jobs/proof;
- one-unambiguous-Goal auto-resolution only; otherwise selection required;
- capsule/currentness preflight;
- active acceptance state handling;
- stale source/runtime handling;
- exact replay/idempotency identity for reattach so response loss cannot produce competing controllers;
- replacement endpoint increments/fences controller generation where current lease model requires it.

### Tests

- Session A -> B on idle Goal;
- Session A -> B with exact current ACK;
- Session A -> B with stale ACK;
- Session A -> B with missing/future ACK;
- Session A -> B with active command/job;
- Session A -> B during PROVING;
- Session A -> B during ACCEPTING;
- source drift between A/B;
- multiple open Goals;
- stale/missing capsule;
- old session attempts stale controller mutation after fencing;
- lost reattach response + exact replay does not create duplicate authority transfer.

### Exit

No duplicate RUN/job, no authority ambiguity, old controller generation fenced, new session reaches exact same Goal state with bounded recovery.

---

## TG4 — UI-independent execution/progress, bounded output, typed handoff and edit safety

### Objective

Loss/lag of ChatWeb card does not lose work or force replay; bounded source/result handling reduces context and repair cost.

### Work A — durable operation truth

- normalize durable operation/job/delegation handles across relevant flows;
- retained bounded output refs and cursor semantics;
- typed terminal snapshots;
- re-observe rather than restart;
- live-control Goal/RUN/job projection;
- renderer consumes bounded projection only;
- analytics stays off fast path.

### Work B — typed large-result handoff inspired by upstream #243

Local already has source-fenced continuations. Extend result contracts, not public tool count, so a truncation declares:

- why data is incomplete;
- canonical existing operation/path for continuation;
- whether continuation recovers all omitted data or only later pages;
- when caller must narrow path/scope or increase a local bound;
- exact source/scope fingerprint that makes stale continuation fail closed.

Never tell the controller to repeat the original broad diff/read when an exact continuation exists.

### Work C — scoped exact-edit fence inspired by upstream #241

Before broad adoption, add a parity audit of current patch/edit conflict handling. If local still permits ambiguous exact-match edits, introduce an internal source-scope fence:

```yaml
edit_scope:
  path:
  source_fingerprint:
  start_line:
  end_line:
  occurrence_global:
```

Rules:

- line numbers are source-relative to the exact pre-edit fingerprint;
- occurrence identity remains global, not scope-relative;
- `occurrence` and `line_scope` must agree;
- no eligible match -> typed not-found;
- multiple eligible matches -> typed ambiguity;
- requested occurrence outside scope -> typed stale/unsafe conflict;
- source fingerprint drift invalidates the fence before mutation.

Use behind `agent_workflow`/current edit primitives; do not create a ninth tool.

### Work D — durable-job parity audit inspired by upstream #88

Test current local execution against boundaries:

```text
ChatWeb card loss
ChatWeb session replacement
MCP reconnect
Coding Tools MCP process restart
Recovery Host/runtime replacement
terminal-result retention after producer/log loss
```

If the same logical job survives all required current product boundaries, do not port a detached supervisor.

If a proven boundary still kills/replaces long-running execution, port only the minimum ownership-handoff substrate needed for that boundary, preserving existing Job/operation identity and bounded logs. Machine-reboot survival remains a separate requirement unless explicitly added.

### Work E — anti-lag patterns inspired by upstream #236

Audit and adopt only when local evidence supports them:

- bounded background diagnostic writer so trace compression/I/O cannot backpressure tool request;
- dropped diagnostic capture gets explicit typed omission, not request failure;
- deduplicate in-flight refreshes;
- render only when bounded projection fingerprint changes;
- separate UI refresh cadence from lease/authority heartbeat cadence;
- do not increase poll interval blindly if operator freshness would regress.

### Tests

- tool card logically disappears but operation remains retrievable;
- browser/UI reconnect gets current progress;
- terminal result stable after later job-log loss where supported;
- output truncation provides explicit source-fenced continuation;
- line-scope stale/ambiguous edit fails before write;
- repeated poll does not increase ledger/history load unboundedly;
- trace/diagnostic saturation does not materially increase tool latency;
- unchanged projection does not trigger unnecessary full renderer rebuild.

### Exit

Execution truth is reconstructable entirely from Runtime/ledger/retained handle state, and bounded-result/edit safety reduces repeated broad reads and accidental repair work.

---

## TG5 — ChatWeb context/usage/lag observability

### Objective

Measure rotation-related signals without fabricating precision and correlate them with durable semantic checkpoints.

### Work

Continue current token master W0-W5 seams:

- exact structured controller receipt feasibility;
- turn/session/trace/invocation correlation;
- provider usage normalization;
- 8-tool invocation telemetry;
- tool-card token receipt only if host supports;
- rolling host/UI/controller-gap observations with clock provenance;
- separate exact vs heuristic rotation signals;
- record current knowledge revision at material host observations when exact linkage exists;
- never equate knowledge revision count with token/context usage.

### Exit

Capability matrix clearly states:

```text
exact controller usage: supported|unobserved
exact session identity: supported|partial|unobserved
exact context pressure: supported|unobserved
controller knowledge revision: supported with exact durable semantics
heuristic rotation signals: available with explicit label
```

No bytes/token fallback enters canonical usage.

---

## TG6 — Rotation readiness and manual cross-session E2E

### Objective

Prove the real product journey before any auto-handoff policy.

### Required real scenario

1. open exact Problem Revision with >=5 criteria;
2. ChatWeb Session A starts Goal pursuit;
3. at least one WAVE fails and enters evidence-driven REPLAN;
4. create at least one material controller-knowledge checkpoint;
5. run several read/search/status operations and prove they do not inflate checkpoint revision when policy says `NO_ADVANCE`;
6. a durable command/delegated execution exists;
7. progress remains visible in Execution Control Center even if ChatWeb card is not relied on;
8. Continuity Core recorded;
9. Session A is intentionally ended/rotated;
10. Session B binds same workspace/Problem;
11. Session B presents an exact-current or intentionally stale ACK according to test arm;
12. bounded recovery reconciles to current knowledge;
13. Session B reattaches controller role legally;
14. active/terminal execution is re-observed, not duplicated;
15. Session B reconstructs exact criteria/gap/proofs/next action without transcript replay;
16. remaining criterion is solved and proved;
17. closure falsifier passes;
18. independent/user outcome confirms or same-revision reopen occurs;
19. all session/RUN/WAVE/checkpoint/economics events remain correlated to same Problem Revision.

### Exit

One accepted real cross-session continuity receipt with controller-knowledge recovery evidence. No auto rotation yet.

---

## TG7 — Problem Resolution Economics projector

### Objective

Move the optimization denominator above RUN while preserving per-RUN diagnostics.

### Work

- aggregate exact-linked accepted/rejected/replan RUN economics by Problem Revision;
- session/rotation/resume overhead;
- controller-knowledge checkpoint and recovery overhead;
- problem-level coverage vector;
- TTPR/TTOC and restricted active time;
- human correction/friction;
- nested per-RUN economics;
- no cross-plane token double-count;
- bounded indexed queries;
- measure avoided duplicate read/localization only when causal linkage is observable, otherwise leave unknown.

### Exit

For one real multi-session Problem, report can answer:

```text
How long did this Problem take to Trusted Resolution?
How many sessions/RUNs/WAVEs were required?
How many material knowledge checkpoints and recoveries occurred?
How much measured controller/provider/tool resource did the full journey consume?
How much was rework/resume/recovery overhead?
Which measurements are unknown?
```

---

## TG8 — Operator UI: Goal, Knowledge and Continuity view

### Objective

Show the real unit of work instead of making operator infer it from RUN lists.

### UI target

```text
GOAL
────────────────────────────────────
Problem          P-...
Revision         ...
Status           IN PROGRESS / BLOCKED / RESOLVED
Criteria         4 / 6 proven
Current RUN      ...
Current WAVE     ...
Controller       ChatWeb attached / waiting
Execution        running / proving / accepting

NEXT CRITICAL GAP
...

CONTINUITY
Knowledge rev    current=... / controller_ack=...
Recovery         current / behind / required / history-lost
Capsule          current / stale / missing
Safe to rotate   yes / no / unknown
Reason           ...
Context pressure exact  — / value
Rotation signals heuristic ...

ECONOMICS
TTPR active      ...
Sessions         ...
RUNs/WAVEs       ...
Replans          ...
Resume overhead  ...
Coverage         ...
```

### Performance rule

The Goal view must consume the same bounded fast projection and not introduce whole-ledger scans on every refresh.

### Exit

No measurable material regression against accepted live UI latency baseline; all unknowns display as unknown, not green/zero.

---

## TG9 — Natural cohort with real session-boundary instrumentation

### Objective

Collect 5-10 consecutive natural Problems with the new denominator and continuity telemetry.

### Required metrics

- Problem Revision before first material write coverage;
- Trusted Resolution / reopen / false closure;
- TTPR;
- sessions/problem;
- rotations/problem;
- controller-knowledge checkpoints/problem;
- stale/missing recovery events;
- resume attempts/success;
- resume reconstruction time;
- duplicate localization/read after resume;
- large-result continuation incidence;
- edit ambiguity/stale-scope rejection incidence;
- user correction turns;
- controller/provider/tool usage coverage;
- governance friction;
- Continuity Core overhead;
- EGRI enrichment present/absent;
- session-boundary condition.

### Decision at n=5 and n=10

Retain raw rows and missingness. Decide whether continuity core/checkpointing:

- materially reduces reconstruction without wrong-frame increase;
- is neutral but necessary safety infrastructure;
- adds excessive ceremony/overhead and needs simplification.

No causal claim from descriptive cohort alone.

---

## TG10 — Auto-rotation/advisory policy study

### Objective

Only after manual continuity is safe, evaluate whether proactive rotation reduces TTPR/rework/lag cost.

### Arms/example

```text
CONTROL
manual rotation only

TREATMENT
advisory rotation recommendation
```

Automatic hard rotation is a later policy if advisory proves value and host UX permits safe action.

### Inputs

- exact context/usage when available;
- otherwise pre-registered heuristic policy;
- same Goal/route/oracle/source strata;
- Continuity Core and knowledge-recovery semantics common to both arms.

### Outcomes

- TTPR;
- resume success;
- wrong-frame/reopen;
- controller lag/control gaps;
- total resource economics;
- user/operator burden.

### Exit

Promote only if state loss/duplicate work remains zero on qualifying sample and outcome economics improve materially.

---

## TG11 — EGRI treatment refactor and P5 integration

### Objective

Run EGRI causal evaluation without continuity confounding.

### Common baseline

- Goal Pursuit projector;
- Controller Knowledge Checkpoint/recovery;
- Continuity Core;
- same-role resume;
- UI-independent execution;
- counterevidence safety floor if accepted;
- same usage/economics instrumentation.

### EGRI Treatment only

- Workspace Evidence Index;
- Case Memory;
- enriched Frame/discriminator packet.

### Semantic navigation condition

Current live runtime reports `NATIVE_LSP_BINDING_NOT_CONFIGURED`. Therefore EGRI must not depend on semantic localization until a supported binding is configured and proven.

When available, borrow upstream bounded semantic-navigation philosophy behind existing `agent_workflow`/evidence-index surfaces:

- bounded definition/reference/call hierarchy;
- explicit depth/edge budgets;
- source identity/freshness;
- deterministic fallback to text/search evidence when unavailable.

Do not add a public `code_impact` tool solely for parity.

### P5 updates

- version treatment identity;
- update manifest/analyzer to record session-boundary/continuity strata;
- keep A/A instrumentation health before A/B;
- no automatic promotion.

### Exit

Causal estimand measures incremental EGRI reasoning benefit, not basic resume capability.

---

## TG12 — Promotion / simplification / removal

Promote only features that improve trusted outcome/TTPR/economics without violating safety and authority.

Possible outcomes:

- retain Goal Pursuit + Knowledge Checkpoint + Continuity Core, remove Case Memory;
- retain Goal/continuity, keep EGRI advisory-only;
- retain manual rotation, reject auto-rotation;
- retain typed diff/output handoff but reject line-scope extension if current edit preflight already provides equivalent protection;
- reject detached-job substrate if local runtime already preserves all required execution boundaries;
- retain UI-independent progress regardless of rotation policy;
- simplify capsule if overhead exceeds reconstruction benefit;
- keep exact usage observation but never enable token-based rotation if host semantics remain incomplete.

---

# 12. Test matrix

## 12.1 Contract and authority

- Problem Revision is the Goal denominator;
- accepted RUN does not auto-resolve Problem;
- changed contract requires REVISE;
- same problem still failing REOPENs same revision;
- old session/controller generation cannot mutate after reattach;
- secondary provider never gains acceptance authority;
- controller-knowledge ACK does not grant mutation/acceptance authority;
- 8-tool count unchanged.

## 12.2 Controller knowledge checkpoint

- first durable material state creates expected revision;
- ordinary read/search/discovery/status/poll does not advance revision under `NO_ADVANCE`;
- one logical invocation through a wrapper/gateway cannot accidentally double-advance;
- stale ACK gets bounded delta when retained;
- missing/invalid/future ACK gets compact current handoff, not failure of unrelated read;
- history-loss is explicit;
- ACK retry is idempotent and does not create checkpoint;
- checkpoint identity survives supported runtime/database reopen boundaries;
- checkpoint payload excludes transcript/private reasoning/large logs.

## 12.3 Capsule

- deterministic fingerprint;
- mandatory core fits or fails with typed budget error;
- optional sections omit whole with reason;
- current knowledge revision agrees with capsule identity;
- stale source -> MISMATCHED;
- missing observation -> UNKNOWN;
- no raw transcript/private reasoning;
- caller cannot forge reserved decision/proof/authority fields.

## 12.4 Session continuity

- A->B idle;
- A->B exact ACK;
- A->B stale ACK;
- A->B missing/future ACK;
- A->B active command;
- A->B active provider lane;
- A->B proving;
- A->B accepting;
- A->B after base drift;
- A->B after Problem Revision changed;
- A old endpoint mutation rejected;
- B exact resume succeeds only on correct workspace/Goal;
- lost reattach response exact replay does not duplicate ownership.

## 12.5 UI/progress and durable jobs

- lost card does not cancel job;
- renderer reload reconstructs progress;
- telemetry stale shows UNKNOWN, not STOPPED;
- bounded poll does not repeat heavyweight census;
- output continuation recovers omitted pages without replaying command;
- runtime/process restart parity is classified explicitly as survive/reconcile/lost;
- no detached-supervisor implementation unless a required boundary demonstrably fails.

## 12.6 Large-result/edit safety

- truncated diff/read returns typed handoff;
- continuation is source/scope fenced;
- stale continuation fails closed;
- line-truncated single record does not claim continuation can recover omitted lines when it cannot;
- scoped edit isolates only eligible exact match;
- global occurrence + scope mismatch fails before write;
- source fingerprint drift invalidates edit fence;
- multiple eligible matches return bounded candidate evidence.

## 12.7 Usage/economics

- controller/provider/tool planes separate;
- unknown != 0;
- no timestamp-proximity attribution;
- multi-session same Problem aggregates correctly;
- multiple Problems in same ChatWeb session stay separated by exact turn/problem linkage;
- rejected/replan resources remain charged to Problem;
- session rotation does not double-count usage events;
- knowledge revision count is never used as token estimate;
- recovery delta/capsule bytes are measured separately.

## 12.8 Goal pursuit

- incomplete criteria -> Goal remains active;
- all engineering criteria pass but no independent outcome -> at most provisional;
- closure falsifier fails -> no resolution;
- user says still failing -> same revision reopen;
- explicit external blocker -> BLOCKED with next dependency;
- user cancels/supersedes -> ABANDONED/revised under authority.

---

# 13. Performance budgets and anti-lag design

## 13.1 Fast vs analytics plane

Fast projection:

- Goal identity/status;
- controller knowledge current/ack status;
- active RUN/WAVE/job;
- current authority;
- next critical action;
- continuity readiness;
- recent usage delta.

Analytics plane:

- multi-session Problem economics;
- longitudinal usage;
- routing/evaluation reports;
- cohort statistics;
- upstream parity/adoption evidence.

Do not run analytics on 2s/5s UI heartbeat.

## 13.2 Initial performance acceptance principle

Use the accepted live UI/IPC sample in `CURRENT_STATE.md` as a regression reference, not a universal SLO. Freeze exact performance budgets before implementation acceptance.

Initial proposal for test gates:

- no material regression (>20% without documented cause) against comparable exact-source baseline;
- dashboard/Goal refresh remains under the maintained interactive budget;
- direct Recovery/Runtime health polling remains lightweight;
- capsule/checkpoint build and read-time currentness remain bounded and not on every renderer tick;
- SQL queries have explicit indexed/problem-window bounds;
- no N+1 per criterion/RUN/session on fast path;
- diagnostics/tracing must not synchronously compress/write large payloads on request critical path when evidence shows material backpressure;
- renderer should skip equivalent projections when a stable bounded signature proves no visible state change.

## 13.3 Context payload budgets

- preserve existing 8 KiB outer handoff cap unless measured evidence proves insufficient;
- controller knowledge delta is bounded independently and falls back to current capsule on retention loss;
- large logs never embedded in capsule/checkpoint;
- large diffs/results use continuation/reference;
- Workspace Evidence Index remains separately bounded and experiment-controlled;
- only delta state is sent after resume where possible.

---

# 14. Metrics and decision dictionary

## Primary outcome

```text
Trusted Resolution under fixed safety/correctness floors
```

## Primary time metric

```text
TTPR / restricted active TTPR per exact Problem Revision
```

## Primary quality metrics

- first-pass trusted;
- same-revision reopen;
- false closure;
- user correction turns;
- critical/noncritical defect and rollback/safety outcomes.

## Continuity metrics

- session/endpoint observations per Problem;
- rotation count;
- controller knowledge checkpoint count;
- no-advance hot-path count;
- stale/missing/future/history-lost recovery count;
- resume attempt/success;
- resume correctness;
- capsule current/stale rate;
- reconstruction time;
- recovery delta bytes;
- duplicate localization/read after resume;
- manual resume actions;
- stale-controller rejection count.

## Resource metrics

- controller tokens exact when available;
- provider tokens/cost;
- tool call count;
- model-visible bytes;
- retained output bytes;
- continuation/handoff bytes;
- rework resource ratio;
- continuity overhead;
- proof/acceptance time.

## Safety/ergonomics metrics

- ambiguous edit conflicts caught pre-write;
- stale line-scope/fingerprint rejections;
- repeated broad diff/read avoided via continuation;
- duplicated execution avoided after reconnect;
- diagnostic capture omissions vs request latency;
- refresh dedup hits where implemented.

## Lag metrics

Keep distinct:

```text
presentation/render latency
Runtime/MCP tool latency
controller-observed gap latency
provider-reported latency
session/context heuristic degradation signals
```

Do not call inter-tool gap “model latency” without provenance.

---

# 15. Scientific evaluation plan

## 15.1 Baseline before policy change

Freeze:

- source/runtime revision;
- Goal/Problem semantics version;
- Controller Knowledge Checkpoint policy version;
- Continuity Core version;
- controller usage capability/coverage;
- current UI latency distribution;
- current TTPR/rework where natural data exists;
- session-boundary incidence;
- route/model/oracle/cache strata;
- upstream evidence snapshot used to justify each borrowed primitive.

## 15.2 Natural first

Before auto-rotation or EGRI policy promotion:

- run real user-origin Problems;
- record all screened Problems including failures/censored/blockers;
- do not create synthetic tasks to fill sample;
- preserve unknown/missing.

## 15.3 A/A before A/B

A/A confirms that instrumentation, checkpoint/ACK recording, session-boundary recording, resume handling and Goal attribution do not create artificial differences.

## 15.4 Separate causal questions

Do not combine these into one experiment:

1. Does Controller Knowledge Checkpoint + Continuity Core correctly/safely support resume? — infrastructure/resumption test.
2. Does typed large-result handoff/scoped edit reduce repeat work/rework? — execution ergonomics study or natural evidence.
3. Does proactive rotation improve outcomes? — rotation policy study.
4. Does EGRI enrichment improve reasoning/TTPR? — EGRI treatment study.
5. Does routing/model policy improve economics? — later routing study.

---

# 16. Source map — candidate, not mandatory all-at-once edits

## PRL / Goal / capsule / controller knowledge

```text
resources/coding-tools-mcp/coding_tools_mcp/problem_lineage.py
resources/coding-tools-mcp/coding_tools_mcp/problem_lineage_control.py
resources/coding-tools-mcp/coding_tools_mcp/resolution_contract.py
possible focused resolution_capsule.py / goal_pursuit.py / controller_continuity.py
```

## EOCL / coordination / session handoff

```text
resources/coding-tools-mcp/coding_tools_mcp/coordination.py
resources/coding-tools-mcp/coding_tools_mcp/orchestration_ledger.py
resources/coding-tools-mcp/coding_tools_mcp/workflow_tools.py
resources/coding-tools-mcp/coding_tools_mcp/session_control.py
resources/coding-tools-mcp/coding_tools_mcp/tool_schema.py
```

## Bounded diff/edit/output

```text
resources/coding-tools-mcp/coding_tools_mcp/git_tools.py
resources/coding-tools-mcp/coding_tools_mcp/workflow_tools.py
resources/coding-tools-mcp/coding_tools_mcp/tool_results.py
existing patch/edit preflight modules
focused tests for continuation and patch ambiguity
```

## Usage / economics

```text
resources/coding-tools-mcp/coding_tools_mcp/usage_events.py
resources/coding-tools-mcp/coding_tools_mcp/usage_ledger.py
resources/coding-tools-mcp/coding_tools_mcp/usage_pricing.py
resources/coding-tools-mcp/coding_tools_mcp/accepted_result_economics_report.py
resources/coding-tools-mcp/coding_tools_mcp/problem_resolution_economics.py
resources/coding-tools-mcp/coding_tools_mcp/performance_trace.py
```

## Host / live control

```text
resources/coding-tools-mcp/coding_tools_mcp/live_control.py
resources/coding-tools-mcp/coding_tools_mcp/mcp_http_handler.py
electron/services/hubProxyGateway.js
Recovery Host projection consumers only when exact causal need exists
```

## Renderer

```text
renderer/control-center.js
renderer/dashboard.js
related HTML/CSS only after backend projection semantics are frozen
```

Do not UI-first this program.

---

# 17. Delivery and acceptance ladder

Every implementation packet remains subject to separate gates:

```text
1. upstream/local parity evidence frozen when borrowing a primitive
2. source contract implemented
3. focused/affected proof passes
4. exact EOCL acceptance/checkpoint
5. controlled runtime activation when runtime-affecting
6. current connector/workspace authority
7. real ChatWeb cross-session proof
8. natural workload evidence
9. A/A/A-B evidence when making efficacy/policy claim
10. package/release/deploy/production separate
```

A source unit test does not prove ChatWeb session continuity. A successful manual resume does not prove auto-rotation efficacy. A Trusted Resolution does not automatically prove EGRI causal benefit. An upstream green test does not prove the local port is useful or compatible.

---

# 18. Risk register and kill criteria

## Risk: build a new orchestration layer

Mitigation: Goal is Problem Thread/Revision; pursuit is derived; no new public tool/database/state machine.

## Risk: blindly reproduce upstream AgentTask/Agent runtime

Mitigation: map upstream semantics against Problem/RUN/WAVE/controller lease first. Borrow only missing fence/generation/replay primitives.

## Risk: dual controller authority

Mitigation: same-role reattach uses existing controller lease/fencing; Codex never becomes implicit controller.

## Risk: stale resume looks successful

Mitigation: mandatory knowledge recovery + read-time currentness and exact source/Problem Revision checks; `UNKNOWN/MISMATCHED` fail closed for dependent mutation.

## Risk: checkpoint revision inflates on every tool call

Mitigation: semantic `NO_ADVANCE/ADVANCE/RECOVERY_ONLY` policy; read/search/poll hot paths do not advance; wrapper/gateway cannot double-advance one logical invocation.

## Risk: ACK becomes hidden authority

Mitigation: ACK is knowledge receipt only; it grants no write/acceptance/Problem-revision authority.

## Risk: auto-rotation makes work worse

Mitigation: manual -> advisory -> experiment -> promotion. Auto remains off by default.

## Risk: session count metric gaming

Mitigation: session count diagnostic only; optimize Trusted Resolution/TTPR/economics.

## Risk: capsule overcompression

Mitigation: mandatory invariants/gap/authority/currentness, omission receipts and exact refresh.

## Risk: capsule/context creates more token cost than it saves

Mitigation: measure build/delivery/reconstruction and compare with duplicate localization/context avoided.

## Risk: telemetry causes new UI lag

Mitigation: bounded fast projection, independent analytics cadence, indexed problem-window queries, background best-effort diagnostics only when needed.

## Risk: continuation lies about completeness

Mitigation: typed truncation reason and recoverability; line-truncated content never claims later-page continuation restores omitted lines.

## Risk: scoped edit fence becomes stale after source drift

Mitigation: bind to exact pre-edit source fingerprint; mismatch fails before write.

## Risk: detached execution introduces orphan processes

Mitigation: do not implement unless parity audit proves required; if needed, explicit owned supervisor/handshake/reconciliation only, never generic detach escape hatch.

## Risk: EGRI experiment confounded by continuity

Mitigation: Knowledge Checkpoint + Continuity Core common infrastructure; EGRI enrichment separate treatment; session boundary stratified.

## Risk: semantic navigation becomes hard dependency while LSP unavailable

Mitigation: capability-gated bounded semantic evidence; deterministic text/search fallback; no fake semantic authority.

## Risk: multiple dirty workstreams overwrite each other

Mitigation: TG0 exact ownership, no reset/clean, exact adopted bytes/write lease and scoped acceptance.

## Kill/simplify criteria

Simplify/remove a capability when:

- resume correctness cannot be kept deterministic;
- checkpoint/recovery overhead >= comparable reconstruction benefit without safety gain;
- capsule overhead >= comparable reconstruction benefit;
- fast projection causes material UI/Runtime regression;
- auto-rotation increases rework/false closure/operator burden;
- EGRI enrichment produces negative transfer or no TTPR benefit;
- typed handoff does not reduce repeated broad reads in representative workloads;
- line-scope edit fence duplicates an already-equivalent local safety oracle;
- detached-job substrate provides no additional required survival boundary;
- a new data structure duplicates canonical ledger/PRL without changing a measurable decision.

---

# 19. Definition of Done — whole program

The program is not complete when a Goal card appears in UI or when one session-resume unit test passes.

A representative real scenario must prove all of the following:

1. a user-origin Problem Revision is opened before material work;
2. acceptance criteria and protected invariants are explicit;
3. ChatWeb/Sol controls the Goal and EOCL creates RUN/WAVE attempts;
4. at least one attempt fails/replans without losing Goal identity;
5. material Goal state advances a durable controller-knowledge revision;
6. ordinary read/search/status operations do not advance that revision when classified `NO_ADVANCE`;
7. a long-running execution remains durable independently of ChatWeb card/UI across the required product boundary;
8. progress is reconstructable from Runtime/Execution Control Center;
9. large result truncation, if encountered, provides exact continuation/handoff instead of broad replay;
10. ambiguous/stale exact edit, if encountered, is rejected before mutation;
11. Continuity Core is emitted without transcript/private reasoning;
12. ChatWeb Session A is deliberately replaced;
13. Session B binds exact workspace and same Problem Revision;
14. Session B knowledge ACK is reconciled exactly, including bounded stale recovery when exercised;
15. same-role controller reattach is fenced and old endpoint cannot mutate;
16. Session B recovers criteria coverage, current gap, proofs, authority and next action from bounded state;
17. active/terminal job is re-observed, not duplicated;
18. work continues until all required criteria are proven;
19. closure falsification passes;
20. independent/user outcome yields `RESOLVED_CONFIRMED` or truthful same-revision reopen;
21. Problem Resolution Economics aggregates resources across both sessions and all RUN/WAVEs/checkpoint recovery;
22. unknown controller/context measurements remain unknown;
23. fast UI/live projection stays within accepted performance budget;
24. public tool count remains 8;
25. no second authority/database/Goal/AgentTask engine was introduced.

Only then can Coding-web claim:

> **A Goal can survive ChatWeb session boundaries and UI failure while preserving authority, execution truth, bounded semantic knowledge recovery, context reconstruction and Problem-level optimization.**

---

# 20. Immediate execution order from the current workspace

Given the current dirty worktree, do **not** begin by changing renderer, enabling auto-handoff, copying upstream Agent runtime or opening P5.

Recommended immediate order:

```text
STEP 0 — TG0 upstream/local freeze
Revalidate upstream main/PR state.
Record adoption matrix:
  ADOPT_SEMANTICS
  PARITY_AUDIT
  DEFER
  REJECT_AS_DUPLICATE

STEP 1 — TG0 dirty ownership
Reconcile exact dirty ownership for:
  problem_lineage / capsule
  live_control
  usage_events / usage_ledger / usage_pricing
  continuation/edit surfaces
  related tests/docs

STEP 2 — freeze integrated semantics
Problem = Goal
Problem Revision = DONE contract
Controller Knowledge Revision = durable semantic watermark
Continuity Core != EGRI enrichment
Problem-level economics > RUN-level economics

STEP 3 — TG1/TG2
Goal Pursuit projector
+ controller knowledge checkpoint/ACK/recovery
+ Continuity Core

STEP 4 — TG3
same-role exact reattach + generation/replay fencing

STEP 5 — TG4
UI-independent progress
+ typed large-result handoff
+ exact-edit scope parity/fence
+ durable-job parity audit
+ anti-lag refresh/diagnostic optimizations only where measured

STEP 6 — TG5
finish truthful ChatWeb usage/context/lag measurement boundary

STEP 7 — TG6
real manual Session A -> Session B E2E
including stale/current knowledge recovery

STEP 8 — TG7/TG8
Problem economics + Goal/knowledge/continuity UI

STEP 9 — TG9
5-10 natural Problems

STEP 10 — TG10/TG11
rotation policy and EGRI causal studies

STEP 11 — TG12
promote/simplify/remove from evidence
```

This order deliberately places semantic continuity/resumption before routing expansion, auto-handoff or richer Case Memory platform work.

---

# 21. Relationship to existing plans

This document is an **integration plan**, not a replacement for canonical source/current-state evidence.

- `docs/CURRENT_STATE.md` remains current operational authority.
- `docs/ROADMAP.md` remains maintained product roadmap until accepted source updates it.
- Token/Context Master Plan remains the detailed measurement/accounting authority but must be revised so Problem Revision sits above multi-session resolution economics and Knowledge Revision is not confused with token/context usage.
- EGRI Methodology remains the reasoning/evidence-learning program but must distinguish Continuity Core infrastructure from EGRI Enrichment treatment.
- EGRI Detailed Plan W3 resumption becomes part of TG2/TG6; Case Memory/Index remain EGRI enrichment and are not prerequisites for basic safe session resume.
- P5 A/A and A/B remain explicit/gated and must use revised treatment identities/strata after continuity infrastructure is accepted.
- Upstream WebCodex remains a research comparator and source of candidate primitives, not an authority over local accepted architecture.

No historical research file should be rewritten to pretend it originally contained these conclusions; update maintained current-state/roadmap and version future research revisions explicitly.

---

# 22. Final strategic judgment

The correct product thesis is now:

```text
SESSION MAY END
UI MAY LAG OR DISAPPEAR
WORKER MAY FAIL
WAVE MAY FAIL
RUN MAY REPLAN
RUNTIME MAY RECONNECT
CONTROLLER KNOWLEDGE MAY BE STALE

BUT THE PROBLEM/GOAL REMAINS
AND KNOWLEDGE CAN BE RECONCILED
UNTIL TRUSTED RESOLUTION,
EXPLICIT BLOCK,
OR USER-AUTHORIZED ABANDONMENT.
```

The value proposition is not infinite ChatWeb context and not more orchestration machinery.

It is:

> **A durable, evidence-grounded Goal journey in which ChatWeb remains the semantic controller, sessions are replaceable, execution/proof are independent from UI, material controller knowledge advances only at durable checkpoints, stale knowledge is recovered from bounded decision state, and optimization is measured from Problem Revision to Trusted Resolution.**

This directly unifies the previously separate concerns of Goal pursuit, session/context limits, ChatWeb lag, progress loss, EGRI resumption, upstream continuity primitives and Accepted-Result Economics into one falsifiable product program.

---

# 23. Upstream primitive integration program

## 23.1 Purpose

This section converts current upstream research into executable local decisions. It is deliberately written as an **overlay on TG0-TG12**, not as a parallel upstream-sync roadmap.

The question for every upstream primitive is:

> **Does this reduce Trusted Problem Resolution time/cost/rework or continuity failure under current local invariants?**

Not:

> “Is upstream newer or does it have more features?”

## 23.2 Evidence snapshot used by R2

At the 2026-09-01 research snapshot:

```text
Upstream repository: yyjeqhc/webcodex
main: 039fecfe73b98506c0fc3b0df7e47be8a4233bac

recent main commits:
#243 039fecfe Improve large diff review handoff
#242 2b3f9354 Add durable AgentTask and fenced TaskAttempt foundation
#241 f50593f6 Add scoped exact edit safety fences
#240 85bd82f3 Converge runtime model specs into ToolDefinition
#239 326c06bc Orthogonalize runtime tool semantics
#236 773f168f Reduce runtime tracing and console overhead

open PR at snapshot:
#244 Advance model context at durable checkpoints
  head: 800fce417234e8e3b99b5a71f91eae12e2d396e8
  base: 039fecfe...

other relevant upstream boundaries:
#88 detached Job ownership handoff — closed/completed upstream
#92 resume host inference from terminal Job events — open design issue
#228 natural durable Agent conversation flow — implemented upstream substrate
```

Before implementing any upstream-derived packet, refresh this snapshot. A changed upstream state may alter evidence, but must not overwrite accepted local invariants automatically.

## 23.3 Adoption matrix

| Upstream primitive | Local decision | Priority | Local destination | Reason |
|---|---|---:|---|---|
| #244 durable model-context checkpoints | `ADOPT_SEMANTICS` | P0 | TG2/TG3 | Fills missing controller knowledge watermark |
| explicit durable resume identity (`task_resume` philosophy) | `ADOPT_SEMANTICS` | P0 | existing `workspace_context`/`task_control`/Problem IDs | Avoid session/transport-implied continuity |
| #243 typed large-diff handoff | `ADOPT_SEMANTICS` | P0/P1 | current continuation/result projection | Reduce broad rereads/context amplification |
| #241 scoped exact edit fence | `PARITY_AUDIT -> ADOPT_IF_GAP` | P1 | current patch/edit preflight | Reduce wrong-edit/rework |
| #239 semantic effect/risk/idempotency separation | `ADOPT_CONCEPT` | P1 | local tool metadata/policy | Needed for semantic checkpoint/replay policy |
| #240 canonical ToolDefinition | `ADOPT_CONCEPT_ONLY` | P1 | local single-source metadata where duplication exists | Avoid schema/policy drift |
| #236 tracing/refresh overhead reductions | `ADOPT_BY_MEASUREMENT` | P1 | performance trace/live renderer | Direct anti-lag value |
| #88 detached Job ownership | `PARITY_AUDIT` | P1/P2 | execution substrate only if local gap proven | Do not create duplicate supervisor unnecessarily |
| #92 terminal Job -> host continuation | `DEFER_HOST_GATE` | P2 | future Host adapter boundary | No proven arbitrary ChatGPT wake primitive |
| #228 Durable Agent/Conversation/Wake | `REJECT_SUBSYSTEM_PORT` | — | borrow only endpoint/generation/replay invariants | Would duplicate local controller/PRL/EOCL domains |
| #242 AgentTask/TaskAttempt | `REJECT_DOMAIN_PORT` | — | borrow fence/generation semantics only if needed | Problem/RUN/WAVE already own pursuit/attempt semantics |
| adaptive larger public tool surface | `REJECT_PUBLIC_PARITY` | — | keep smart-v3/8 | Tool-count growth is not product value |
| semantic code impact/navigation | `CAPABILITY_GATED_CONCEPT` | P1 | EGRI Workspace Evidence Index behind existing tool | Useful, but local LSP currently unavailable |
| cross-owner artifact grant (#94) | `DEFER` | P3+ | none in current program | Not current TTPR/session bottleneck |

## 23.4 P0 primitive U1 — Controller Knowledge Checkpoint

### Local problem it solves

Local already has:

- durable Problem/RUN/WAVE state;
- Resolution/Handoff Capsule;
- source-fenced continuations;
- `safe_to_rotate_chatweb` projection;
- task context/workspace binding.

But local currently lacks an exact durable answer to:

> “The currently attached/resuming ChatWeb controller has acknowledged material Goal state through which revision?”

Without this watermark, a new session either trusts a whole capsule as if no prior knowledge existed or risks reconstructing/re-reading too much.

### Local invariant

```text
CONTROLLER KNOWLEDGE REVISION
  = monotonic durable semantic watermark
  != raw event sequence
  != tool count
  != token/context count
```

### Material checkpoint candidates

TG0 must freeze the exact table, but likely categories are:

- Problem opened/revised/reopened/blocked/resolved state changes;
- acceptance contract/criteria fingerprint change;
- criterion/proof coverage change that alters closure decision;
- RUN/WAVE state transition only when it changes next critical action/authority materially;
- controller/acceptance authority handoff;
- Resolution Capsule material decision-state refresh.

Likely `NO_ADVANCE` categories:

- repository read/search;
- repeated workspace/status poll;
- diff/output page continuation;
- unchanged live-control refresh;
- evidence read that does not commit canonical decision state.

### Correctness rule

One logical material operation may advance at most once. Nested wrapper/gateway paths must resolve one policy owner and cannot create outer + inner revisions.

### Recovery rule

A behind/missing ACK never grants authority and never changes the success semantics of an independent safe read. It only causes bounded continuity metadata/recovery to be returned.

A dependent mutation may fail closed if the controller cannot prove/recover the material decision state required by that mutation.

## 23.5 P0 primitive U2 — Explicit same-Goal resume identity

Borrow the upstream Stateless-MCP principle:

```text
same chat != continuity proof
same connection != continuity proof
same credential != continuity proof
same project != continuity proof
```

Local continuity must be explicit through existing exact identities:

```text
workspace_id
problem_id + problem_revision
task_context_id
run_id/wave_id when active
controller generation/lease
knowledge revision/capsule fingerprint
```

Do not create `task_resume` as a ninth tool solely to copy upstream. If current `task_control(handoff/reattach)` vocabulary is insufficient, extend its internal/action contract under the same public tool.

## 23.6 P0/P1 primitive U3 — Typed large-result handoff

### Current local advantage

Local already has signed/source-fenced continuation for large diffs. Preserve it.

### Missing ergonomic layer

A result should explain exactly:

```text
WHY incomplete
WHAT existing operation continues it
WHETHER continuation restores all omitted data
WHICH source/scope fingerprint is frozen
WHEN narrowing is required instead of paging
```

### Acceptance oracle

Representative large dirty-worktree review should show fewer repeated broad diff calls/model-visible bytes than baseline, with no missed required hunk evidence.

## 23.7 P1 primitive U4 — Scoped exact-edit safety fence

### Adoption gate

First prove current edit/patch preflight lacks equivalent protection. If already equivalent, record `PARITY_PASS_NO_PORT`.

### If gap exists

Add source-fenced line scope to internal exact edit selection. Preserve global occurrence numbering and fail closed when:

- scope has zero eligible exact matches;
- more than one eligible exact match remains;
- requested global occurrence lies outside scope;
- source fingerprint changed;
- multi-line match is not fully contained in the scope.

### Expected value

Reduce:

- patch ambiguity;
- accidental duplicate-symbol edit;
- wrong-region changes after file drift;
- downstream proof reruns/replan caused by avoidable patch error.

## 23.8 P1 primitive U5 — Tool semantic contract normalization

Local live metadata already exposes:

- risk;
- mutation class;
- concurrency;
- authority owner;
- capability profile.

Do not rewrite metadata wholesale to mimic upstream.

Add only missing axes needed for actual policy decisions:

```yaml
tool_semantics:
  effect: OBSERVE | MUTATE | EXECUTE | UNKNOWN
  checkpoint_policy: NO_ADVANCE | ADVANCE | RECOVERY_ONLY | CONSERVATIVE_UNKNOWN
  replay_semantics: PURE_READ | DESIRED_STATE | KEYED | FENCED_REPLAY | NON_IDEMPOTENT | UNKNOWN
```

Keep authority separate. `OBSERVE` does not automatically mean low privacy risk; `MUTATE` does not automatically mean a new permission prompt if existing EOCL authority already covers it.

Canonicalize declarations only where duplicate local definitions are currently a real drift source.

## 23.9 P1 primitive U6 — UI/trace anti-lag patterns

Borrow #236 only after baseline measurement.

Candidate treatments:

1. async bounded diagnostic writer;
2. explicit `diagnostic_capture_omitted` state when queue/disk budget saturated;
3. in-flight refresh coalescing;
4. renderer projection fingerprinting to avoid unnecessary rebuild;
5. slower noncritical data refresh while keeping lease/control heartbeat independent;
6. no synchronous expensive trace compression on request path.

Do not conflate:

```text
UI refresh frequency
controller lease heartbeat
runtime liveness probe
analytics refresh
```

They have different correctness/freshness requirements.

## 23.10 P1/P2 primitive U7 — Durable-job parity audit before detached ownership

Upstream #88 demonstrates a safe pattern for Runner-restart survival, but local has a Recovery Host/execution architecture that is not identical.

Required parity table:

| Boundary | Expected local behavior | Evidence |
|---|---|---|
| ChatWeb tool-card disappears | same logical operation survives | required |
| ChatWeb session rotates | same logical operation survives | required |
| MCP transport reconnect | exact operation is re-observable | required |
| Coding Tools MCP process restart | classify survive/reconcile/lost | audit |
| Recovery Host/runtime replacement | classify survive/reconcile/lost | audit |
| producer log retention expires | terminal receipt remains if contract promises | audit |
| machine reboot | non-goal unless separately approved | explicit |

Only if a required boundary fails should a detached-supervisor/ownership-handoff design enter implementation.

If implemented, preserve:

- same logical job ID;
- exact process-identity fencing, not PID alone;
- bounded stdout/stderr;
- atomic terminal result;
- explicit cancellation;
- no generic unmanaged `detach=true`.

## 23.11 P2 primitive U8 — Terminal Job continuation / host wake

Upstream #92 is directionally aligned but host-gated.

Local may prepare a **durable continuation intent contract** only when there is a real supported host adapter or explicit product requirement.

Potential future record:

```yaml
continuation_intent:
  exact_job_id:
  problem_revision:
  controller_endpoint_generation:
  terminal_event_identity:
  state: PENDING | CLAIMED | DELIVERED | FAILED | DELIVERY_UNKNOWN
  bounded_resume_evidence_ref:
```

Invariants:

- job terminal truth remains authoritative regardless of continuation outcome;
- duplicate terminal events converge on one logical continuation;
- `DELIVERY_UNKNOWN` is not blindly retried;
- unsupported ChatWeb host falls back to manual explicit reattach;
- no raw transcript/log/secret is persisted for callback convenience.

Do not implement fake wake by polling cards/browser state.

## 23.12 What to borrow from Durable Agent/Task without porting the subsystem

Borrow only these invariants when local evidence needs them:

```text
logical controller identity != physical browser/session endpoint
endpoint replacement increments/fences controller generation
exact replay identity survives response loss
lease expiry != authority transfer by implication
old generation cannot mutate after replacement
```

Do not port:

- Durable Agent database;
- Conversation/Inbox as Goal truth;
- AgentTask as a second RUN domain;
- Wake engine as a fake ChatGPT callback;
- global task scheduler.

## 23.13 Semantic navigation / Workspace Evidence Index

Upstream bounded semantic navigation is useful for EGRI localization, but current local live state says:

```text
semantic_localization.available = false
reason = NATIVE_LSP_BINDING_NOT_CONFIGURED
```

Therefore implementation rule:

```text
if supported semantic provider is exact/current:
  use bounded definition/reference/call-hierarchy packet
else:
  deterministic grep/read/test/navigation fallback
```

Never mark fallback as semantic-LSP evidence.

Enable semantic provider only as a separate capability/configuration task with its own proof; do not block Goal continuity on it.

## 23.14 Upstream-watch protocol during implementation

Before each material TG wave that borrows upstream:

1. re-read upstream main SHA;
2. re-check referenced PR/issue state;
3. compare only the specific primitive delta;
4. record `upstream_evidence_sha` / PR head in research or wave evidence;
5. inspect local parity;
6. freeze local contract before mutation;
7. never silently widen scope because upstream added adjacent features.

After local acceptance, later upstream changes are new research evidence, not automatic invalidation of local proof.

## 23.15 Implementation packets

### Packet U1 — Knowledge checkpoint domain

**Objective:** durable semantic watermark with no hot-path inflation.  
**Likely scope:** coordination/ledger/continuity module + schema/projection tests.  
**Proof:** policy table, one-advance-per-material-operation, read-hot-path stays revision-stable, database/reopen durability.  
**Stop:** requires new public tool or duplicates an already accepted local primitive.

### Packet U2 — ACK recovery + Capsule integration

**Objective:** bounded exact/current/behind/missing/future/history-lost recovery.  
**Likely scope:** task-control/handoff/goal projection + tests.  
**Proof:** sealed Context A -> B fixtures and stale/future ACK cases.  
**Stop:** recovery can inject unbounded history or alter authority.

### Packet U3 — Reattach fencing

**Objective:** same-role controller replacement with exact replay identity.  
**Likely scope:** controller/client registry/session-control/coordination.  
**Proof:** A->B, old generation rejected, lost-response replay idempotent.  
**Stop:** competing control/acceptance owner can exist.

### Packet U4 — Bounded result/edit ergonomics

**Objective:** reduce repeated broad reads and ambiguous patches.  
**Likely scope:** `git_tools.py`, `workflow_tools.py`, result schema, patch/edit preflight.  
**Proof:** large diff continuation, unrecoverable line-truncation honesty, scoped-edit ambiguity/stale-source tests.  
**Stop:** current local primitive already has equivalent safety/value.

### Packet U5 — Job parity + anti-lag

**Objective:** prove execution/UI independence and remove measured fast-path overhead.  
**Likely scope:** command/session lifecycle, Recovery Host projections, performance trace, renderer refresh coordinator.  
**Proof:** survival/reconciliation matrix + comparative latency sample.  
**Stop:** optimization lacks baseline or weakens freshness/authority.

### Packet U6 — Semantic evidence capability

**Objective:** bounded semantic localization only when supported.  
**Likely scope:** configuration/provider binding + Evidence Index adapter.  
**Proof:** source-fenced bounded results + unavailable fallback.  
**Stop:** requires ambient network/filesystem authority or cannot prove provider freshness.

## 23.16 Upstream-specific acceptance criteria

The upstream integration program is successful only when:

- at least one real continuity session uses material knowledge revisions and bounded recovery;
- ordinary read/search/poll traffic does not create continuity-revision churn;
- local 8-tool public contract remains unchanged;
- large-result continuation avoids at least one repeated broad read in representative evidence without losing required data;
- edit-scope primitive is either proven useful and accepted or explicitly rejected because local parity is already sufficient;
- job restart/survival boundary is documented from real local evidence before any detached-supervisor work;
- no Durable Agent/AgentTask parallel authority plane is introduced;
- all adopted primitives improve or protect a measurable Goal/TTPR/continuity decision;
- unadopted upstream features remain explicitly out of scope rather than silently accumulating technical debt.

---

# 24. Final implementation doctrine

The integrated program must be executed with this priority:

```text
FIRST
Protect Goal identity, authority and durable semantic knowledge.

THEN
Make session replacement and execution recovery exact.

THEN
Reduce context amplification, patch ambiguity and UI/trace overhead.

THEN
Measure Problem-level economics on natural work.

ONLY THEN
Experiment with proactive rotation, richer EGRI, routing expansion or host continuation.
```

Every proposed addition must answer at least one of these with evidence:

```text
Does it reduce repeated scans?
Does it reduce context reconstruction?
Does it reduce duplicate execution?
Does it reduce wrong edits/rework?
Does it reduce proof reruns/replans?
Does it reduce controller/session lag cost?
Does it improve trusted resolution probability?
Does it reduce TTPR or total Problem cost under fixed safety floors?
```

If the answer is no or unmeasurable, do not add the mechanism merely because upstream has it.
