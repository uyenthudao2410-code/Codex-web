# Orchestration Wave Audit Ledger & Optimal EOCL Rollout Plan

**Ngày:** 2026-08-13  
**Repository:** `uyenthudao2410-code/Tools-Codex-web`  
**Base HEAD khi review:** `a153a8984cc2d2e1bfe0e24131e287f491caee19`  
**Loại tài liệu:** design review vòng 2 / observability architecture / rollout plan  
**Phạm vi:** ChatWeb Sol, Coding Tools MCP, Codex App Server/Desktop, adaptive router, EOCL, proof DAG, worktree coordination, event logging, route learning.  
**Production source changed by this document:** **NO**.

---

# 0. Executive decision

## 0.1 Kết luận mới sau khi review lại toàn bộ 4 tài liệu và source hiện tại

Kiến trúc model/routing hiện tại **không cần đảo lại**:

```text
CONTROL                  ChatWeb Sol
DETERMINISTIC            Coding Tools MCP
CHEAP PATCH              Mini low / no-tools
HARDER LEAF              Luna high / no-tools
DEEP CODE                Codex Sol xhigh
CROSS-FILE EXPERIMENT    Terra high
CONSEQUENTIAL            Sol max
PARALLEL EXTREME         Sol ultra
FINAL ACCEPTANCE         ChatWeb Sol + deterministic evidence
```

Điểm cần thay đổi sâu nhất là **execution accountability**.

Postmortem trước đã đúng khi yêu cầu:

```text
policy-guided orchestration
        ->
state-enforced orchestration
```

Nhưng thiết kế đó vẫn còn thiếu một primitive quan trọng:

> **Mọi coordination wave phải có một durable, append-only, reconstructable audit trail trước khi ta tiếp tục tối ưu router.**

Nếu chỉ có `task-state.json`, `performance.json`, product telemetry hoặc final route row thì sau incident vẫn không thể trả lời chắc chắn:

- wave nào bắt đầu từ base nào;
- ai được ủy quyền write ở thời điểm nào;
- route requested và route resolved khác nhau ra sao;
- supervisor/readiness đổi trạng thái lúc nào;
- packet nào bị invalid vì base/contract drift;
- failure nào kích hoạt REPLAN;
- proof nào đã PASS trên fingerprint nào;
- proof nào được reuse và vì sao reuse hợp lệ;
- controller có mutation sau khi authority đã delegate hay không;
- model/tool spend thuộc delegation nào;
- coordination wave nào thực sự tạo accepted result;
- time/cost bị mất ở discovery, waiting, model, mutation, proof, replan hay integration.

Do đó target mới là:

```text
EOCL
+
ORCHESTRATION AUDIT LEDGER
+
PROOF LEDGER
+
OTEL PROJECTION
+
AUTO-GENERATED WAVE REPORT
```

## 0.2 Nguyên tắc nguồn sự thật

```text
CANONICAL AUDIT SOURCE
    SQLite append-only orchestration ledger

CURRENT STATE VIEW
    task-state.json / in-memory projection

PERFORMANCE VIEW
    materialized metrics from ledger

LIVE OBSERVABILITY
    OpenTelemetry spans/logs/metrics

HUMAN DOCUMENTATION
    generated Markdown wave/run reports

REMOTE PRODUCT ANALYTICS
    existing privacy-constrained telemetry
```

Không lớp nào được thay thế nhầm vai trò của lớp khác.

## 0.3 Thay đổi quan trọng về rollout order

Postmortem trước ưu tiên enforcement rồi observability.

Sau review source hiện tại và yêu cầu phải học từ từng đợt phối hợp, rollout tối ưu hơn là:

```text
W0  durable audit substrate + shadow instrumentation
W1  hard state/authority enforcement
W2  proof DAG + proof fingerprint/cache
W3  behavior packets + Desktop/worktree coordination
W4  adaptive routing from empirical wave history
W5  continuous policy evaluation/reporting
```

Điều kiện an toàn:

> **Không chạy story high-risk mới bằng Desktop-coordinated mode trước khi W1 hoàn tất.**

W0 có thể được kiểm thử trên fixture/low-risk tasks để lấy baseline mà không tiếp tục mang coordination drift vào finance/auth/privacy work.

---

# 1. Evidence baseline

Tài liệu này kế thừa bốn decision/research records:

1. `EXECUTOR_ROUTING_BENCHMARK_2026-08-12.md`
2. `MODEL_ORCHESTRATION_RESEARCH_PHASE2_2026-08-12.md`
3. `ORCHESTRATION_METHODOLOGY_EXPERIMENTS_AND_PRODUCTION_DECISION_2026-08-12.md`
4. `PFM_ORCHESTRATION_RUNTIME_POSTMORTEM_AND_ENFORCED_CONTROL_LOOP_RESEARCH_2026-08-13.md`

Các kết luận giữ nguyên:

- autonomous Luna/Terra không được promote cho localized strong-oracle class từ Phase 1;
- packet-only/no-tools Mini/Luna có economics tốt hơn trên bounded localized samples;
- Sol xhigh là deep lane, không phải universal leaf lane;
- serial model ladder bị reject;
- multi-agent chỉ dùng khi task shape thật sự parallelizable;
- final acceptance thuộc ChatWeb Sol + deterministic evidence;
- proof validity phải gắn fingerprint;
- authority drift sau deep-code failure là failure orchestration, không phải finance semantics failure.

---

# 2. Source review: logging hiện tại chưa đủ làm audit ledger

Snapshot source đã kiểm tra trên `main`:

```text
server.py
  SHA 610960113198a15fb4b0046714e6ae85666733d6

task_state.py
  SHA 4b18b74e38c006098e0fa9ceac845e5f62cd7e33

performance_trace.py
  SHA 0e862e537773fb13773b4b462a7b3a7e6ec5b98e

telemetry.py
  SHA 3f32d25ccae9b68fc31d71bb75e91b2c1e52606d
```

## 2.1 `server.py`

Current source đã có:

- compact 8-tool smart surface;
- candidate output schema;
- Mini low route;
- Luna high route;
- Terra high route;
- Sol xhigh/max/ultra route metadata.

Đây là bằng chứng rằng **model routing primitive đã tồn tại**.

Vấn đề hiện tại không phải thiếu model table.

## 2.2 `TaskStateStore`

Current `TaskStateStore`:

- ghi snapshot vào `.coding-tools/task-state.json`;
- archive vào `task-history.json`;
- event list bị cap bởi `MAX_EVENTS = 100`;
- `_event()` giữ rolling tail bằng `[-MAX_EVENTS:]`;
- state được rewrite atomically nhưng **không phải append-only event source**.

Nó phù hợp làm current UX/state snapshot.

Nó không đủ cho:

- full forensic reconstruction;
- multi-wave lineage;
- delegation authority;
- cross-process event ordering;
- proof lineage;
- long-run optimization dataset.

## 2.3 `PerformanceTraceStore`

Current performance store:

- `MAX_RECENT = 100`;
- ghi aggregate tool-call count/errors/cache hits;
- `wait_before_ms` là estimate từ gap giữa previous tool completion và next tool start.

Điều này có ích cho local performance hints nhưng không đủ để suy ra causal timing khi:

- có parallel worker;
- model/App Server đang hoạt động giữa calls;
- một wave có nhiều lanes;
- proof chạy ngoài primary tool sequence;
- task resume sau restart.

## 2.4 Existing product telemetry

`SessionTelemetry` cố ý:

- dùng closed schema;
- không chứa file paths/tool args/command lines/file contents;
- có thể disable bằng env/DNT/CI;
- dùng bounded in-memory queue;
- overflow có thể drop;
- send failure bị swallow;
- không persist execution details ra disk.

Đó là thiết kế đúng cho anonymous product analytics.

Nhưng vì chính các privacy/reliability properties này, nó **không thể là canonical orchestration audit store**.

---

# 3. External research bổ sung cho logging/observability

## 3.1 Delegation identity phải là first-class data

Mishra & Sharad, **Observability for Delegated Execution in Agentic AI Systems** (arXiv:2606.09692, 2026) chỉ ra rằng execution/audit traces thông thường có thể không xác định được delegation assignment. Cùng causal trace có thể tương thích với nhiều authority/delegation interpretation khác nhau.

Implication:

```text
trace_id != delegation_id
span tree != authority tree
```

Ta phải persist riêng:

```text
delegation_id
parent_delegation_id
authority_owner
write_lease_id
allowed_scope
```

Source:

- https://arxiv.org/abs/2606.09692

## 3.2 Full execution visibility cải thiện failure attribution

Chen et al., **Seeing the Whole Elephant: A Benchmark for Failure Attribution in LLM-based Multi-Agent Systems**, ACL 2026, DOI `10.18653/v1/2026.acl-long.912`, báo cáo full execution traces cải thiện failure-attribution accuracy tới 76.5% so với partial-observation counterpart trong setup của benchmark.

Implication:

- final output + task summary không đủ;
- cần state transitions, inputs/context identity, ownership, tool/proof outcomes;
- không nhất thiết lưu raw sensitive content; identity/hash + structured event vẫn phải đầy đủ.

Source:

- https://aclanthology.org/2026.acl-long.912/

## 3.3 Structured runtime logs nên tách operational/contextual surfaces

AlSayyad et al., **AgentTrace: A Structured Logging Framework for Agent System Observability** (arXiv:2602.10133, 2026) đề xuất structured runtime logging across operational/cognitive/contextual surfaces và integration với OpenTelemetry.

Local adaptation:

- **operational:** state, route, model, tool, proof, timing, failures;
- **contextual:** base/worktree/contract/packet identity;
- **decision record:** selected mode/replan reason;
- không log private chain-of-thought.

Source:

- https://arxiv.org/abs/2602.10133

## 3.4 Explicit execution state vẫn là strongest direct coding evidence

Wang et al., **Turning Interaction History into Execution State: A Runtime Layer for Long-Horizon Coding Agents** (arXiv:2608.00808, 2026) duy trì deterministic execution ledger và dùng `inform` + `govern` paths. Paper báo cáo khi gắn với OpenAI Codex, Pass@1 tăng 3.4 điểm và total cost giảm 24.4% trong evaluation của họ.

Implication:

Audit ledger không chỉ dùng sau incident. Nó phải tham gia runtime:

```text
INFORM
  render current verified state to coordinator/executor

GOVERN
  reject/reuse actions based on current ledger
```

Source:

- https://arxiv.org/abs/2608.00808

## 3.5 OpenTelemetry phù hợp làm projection, không phải audit authority

OpenTelemetry hiện có GenAI semantic conventions cho:

- `invoke_agent`;
- `plan`;
- `execute_tool`;
- agent identity;
- model/provider/operation attributes;
- GenAI events.

GenAI semantic conventions đã được tách sang repo riêng:

- https://github.com/open-telemetry/semantic-conventions-genai

Nhưng OTel tracing hỗ trợ sampling; span có thể không được recorded/exported. Vì vậy OTel là live observability/projection, không phải source-of-truth cho control/audit state.

Sources:

- https://opentelemetry.io/docs/specs/otel/trace/sdk/
- https://opentelemetry.io/docs/specs/otel/logs/
- https://www.w3.org/TR/trace-context/

---

# 4. Target architecture — five different data roles

```text
                    ┌─────────────────────┐
                    │ ChatWeb Sol          │
                    │ semantic controller  │
                    └──────────┬──────────┘
                               │
                               v
┌──────────────────────────────────────────────────────────────┐
│ Coding Tools MCP                                             │
│                                                              │
│  EOCL state machine                                          │
│       │                                                      │
│       ├── append -> ORCHESTRATION AUDIT LEDGER (canonical)   │
│       │                     │                                │
│       │                     ├-> current-state projection     │
│       │                     ├-> route ledger materialization │
│       │                     ├-> proof ledger                 │
│       │                     ├-> OTel projection              │
│       │                     └-> Markdown report generator    │
│       │                                                      │
│       ├── MCP deterministic execution                        │
│       └── Codex bridge / Desktop/App Server                  │
└──────────────────────────────────────────────────────────────┘
```

No duplicate manually-maintained truth.

---

# 5. Canonical store choice: SQLite, not rolling JSON

## 5.1 Why SQLite

Use Python stdlib `sqlite3` with WAL mode for the local canonical ledger.

Reasons:

- append-only event transactions;
- crash-safe transactional commits;
- concurrent readers;
- indexes for run/wave/task/event queries;
- easy aggregation/materialized report generation;
- no new external service dependency;
- source package already Python;
- can export JSONL/Markdown deterministically;
- much better than rewriting a huge JSON array.

## 5.2 File location

Recommended:

```text
<workspace>/.coding-tools/orchestration/ledger.sqlite3
```

Local operational artifact; gitignored.

Generated safe reports may be committed under:

```text
docs/orchestration-runs/<YYYY-MM-DD>/<story-or-task>/<run-id>/
```

Only sanitized summaries should be committed.

## 5.3 Why not JSONL as canonical

JSONL is useful export, but not ideal canonical store for:

- concurrent writes;
- querying proof lineage;
- joins between run/wave/packet/delegation;
- materialized metrics;
- crash recovery around multi-record transitions.

Therefore:

```text
SQLite = authority
JSONL  = export/interchange
MD     = human report
OTel   = live observability
```

---

# 6. Identity hierarchy

A run must not be identified only by task ID.

Recommended hierarchy:

```text
run_id
  ├─ wave_id
  │    ├─ delegation_id
  │    │    ├─ packet_id
  │    │    └─ tool/model/proof events
  │    └─ child delegation(s)
  └─ checkpoint(s)
```

## 6.1 `run_id`

One user-visible engineering objective/story execution.

## 6.2 `wave_id`

A coordination wave = one set of work dispatched under the same:

- frozen/known base identity;
- accepted shared invariants;
- contract fingerprint;
- execution-mode decision;
- coordination assumptions.

Wave closes when:

- all wave packets are accepted/rejected; or
- shared base/contract changes; or
- typed failure forces REPLAN; or
- integration stage starts; or
- operator/controller aborts wave.

## 6.3 `delegation_id`

Represents authority assignment, not trace timing.

Examples:

```text
D0 ChatWeb Sol -> MCP executor authority
D1 ChatWeb Sol -> Codex Sol xhigh deep lane
D2 D1 -> isolated FE sub-lane (only if policy allows)
```

For current lean policy, recursive delegation remains normally disabled.

## 6.4 `trace_id` / `span_id`

Use for OTel causal tracing.

Do not infer delegation/authority only from trace parentage.

---

# 7. Minimum event schema

Every event should be immutable after commit.

```json
{
  "schema_version": 1,
  "event_id": "01K...",
  "sequence": 42,
  "recorded_at": "2026-08-13T03:45:12.123Z",
  "monotonic_ns": 123456789,

  "run_id": "run_...",
  "wave_id": "wave_003",
  "task_id": "...",
  "story_id": "US-113",
  "packet_id": "backend-financial-boundary-v2",

  "delegation_id": "del_...",
  "parent_delegation_id": null,
  "trace_id": "...",
  "span_id": "...",
  "causation_event_id": "...",

  "event_type": "route.selected",

  "actor_plane": "mcp",
  "actor_role": "controller",
  "actor_id": "coding-tools-mcp",

  "state_before": "READY",
  "state_after": "ROUTED",

  "base_head": "...",
  "worktree_id": "...",
  "worktree_fp": "...",
  "contract_fp": "...",

  "execution_mode": "deep_single_lane",
  "route_requested": "sol_xhigh",
  "route_resolved": "sol_xhigh",
  "model": "gpt-5.6-sol",
  "effort": "xhigh",

  "write_lease_id": "lease_...",
  "write_owner": "CODEX:lane-1",

  "status": "ok",
  "failure_class": null,
  "duration_ms": 0,

  "payload": {},
  "payload_hash": "sha256:..."
}
```

## 7.1 Important principle

Do not put raw prompts/source/tool stdout into core event rows by default.

Store:

- IDs;
- hashes;
- sizes;
- normalized low-cardinality status;
- artifact refs when detailed evidence must be retained locally.

---

# 8. Event taxonomy

Keep taxonomy stable and low-cardinality.

## 8.1 Run lifecycle

```text
run.started
run.completed
run.blocked
run.aborted
```

## 8.2 Wave lifecycle

```text
wave.started
wave.closed
wave.accepted
wave.rejected
```

## 8.3 Control state

```text
state.transition
mode.selected
route.selected
failure.classified
replan.started
replan.completed
```

## 8.4 Readiness

```text
coord.startup.checked
coord.readiness.checked
coord.liveness.changed
```

## 8.5 Delegation/authority

```text
delegation.created
delegation.closed
write_lease.acquired
write_lease.released
write_lease.denied
```

## 8.6 Packet

```text
packet.built
packet.dispatched
packet.blocked
packet.completed
packet.invalidated
```

## 8.7 Model/runtime

```text
model.dispatch.started
model.dispatch.completed
model.dispatch.interrupted
model.capacity.failed
```

## 8.8 Mutation

```text
mutation.candidate.created
mutation.applied
mutation.rejected
mutation.base_drift
```

## 8.9 Proof

```text
proof.started
proof.passed
proof.failed
proof.cache_hit
proof.invalidated
```

## 8.10 Contract/checkpoint

```text
contract.frozen
contract.invalidated
checkpoint.created
```

Tool-level spans may be represented through OTel and summarized in event store; command start/finish may be persisted when needed for exact TTA/proof reconstruction.

---

# 9. State transition logging is mandatory

No state change without an event.

```text
PREFLIGHT -> READY
READY -> ROUTED
ROUTED -> EXECUTING
EXECUTING -> PROVING
PROVING -> ACCEPTING
ACCEPTING -> CHECKPOINTED
```

Exceptional:

```text
* -> REPLAN
* -> BLOCKED
* -> ABORTED
```

Required event fields:

```text
state_before
state_after
transition_reason
causation_event_id
actor
```

Guard:

```text
if state mutation succeeds but audit append fails:
    fail closed for consequential orchestration transition
```

A control transition that cannot be durably recorded must not silently proceed.

---

# 10. Authority and write-lease logging

The previous incident shows write ownership is not metadata; it is a safety boundary.

Canonical write lease:

```text
lease_id
run_id
wave_id
delegation_id
owner
mode
base_head
worktree_id
worktree_fp
allowed_paths
acquired_at
released_at
release_reason
```

Every write operation must resolve an active lease.

Events:

```text
write_lease.acquired
mutation.applied
write_lease.released
```

must be queryable as one lineage.

Hard invariant:

```text
WRITE_WITHOUT_ACTIVE_LEASE = 0
```

If delegated lane fails:

```text
write_lease.released(reason=failure)
state.transition(EXECUTING -> REPLAN)
```

Only after new `route.selected` + `write_lease.acquired` may another owner mutate feature scope.

---

# 11. Coordination wave contract

Every wave must start with a machine-readable manifest.

```json
{
  "wave_id": "wave_003",
  "objective": "Implement backend financial boundary",
  "base_head": "...",
  "worktree_fp": "...",
  "contract_fp": "...",
  "execution_mode": "deep_single_lane",
  "risk": "critical",
  "integration_width": "high",
  "seriality": "high",
  "oracle_strength": "strong",
  "packets": ["packet_A"],
  "write_owners": ["CODEX:lane-1"],
  "required_proof_nodes": ["backend-focused", "auth", "postgres", "openapi"],
  "stop_conditions": [
    "finance_semantics_ambiguous",
    "contract_drift",
    "base_drift",
    "out_of_scope_write"
  ]
}
```

This manifest is hashed and the hash is placed on all wave events.

---

# 12. Pre-wave audit gate

Before dispatch, persist one `wave.started` + preflight snapshot.

Required checks:

```text
[ ] finish line exists
[ ] protected invariants recorded
[ ] base HEAD known
[ ] worktree fingerprint known
[ ] contract fingerprint known if relevant
[ ] execution mode classified
[ ] route requested/resolved recorded
[ ] oracle preflight green/available
[ ] coordination dependencies READY for selected mode
[ ] no stale write lease
[ ] packet scope/proof/stop defined
[ ] expected budget/deadline recorded
```

If any required condition fails:

```text
wave is not dispatched
```

Failure is still logged.

---

# 13. In-wave logging

Do not log every token.

Log decision-relevant lifecycle.

Minimum:

```text
route selection
readiness/liveness change
delegation create/close
write lease acquire/release
packet dispatch/complete/block
model start/end/interruption
mutation candidate/apply/reject
proof start/pass/fail/cache-hit
failure classification
REPLAN decision
contract invalidation
```

For tool commands record:

```text
tool_call_id
tool_name
command_class
args_hash
result_hash
started_at
finished_at
duration
exit_status
output_bytes
truncated
```

Raw output is an optional local artifact, not a remote telemetry attribute.

---

# 14. Post-wave log and generated report

Every closed wave generates a deterministic Markdown summary from ledger facts.

Suggested file:

```text
docs/orchestration-runs/<date>/<story>/<run-id>/wave-003.md
```

Template:

```markdown
# Wave 003 — BACKEND_FINANCIAL_BOUNDARY

## Provenance
- run
- story/task
- base
- worktree
- contract fingerprint
- event bundle hash

## Planned route
- mode
- requested route/model/effort
- packet(s)
- owner(s)
- proof plan

## Actual route
- resolved route/model/effort
- fallbacks/replans

## Timeline
| Time | State/Event | Actor | Result | Duration |

## Authority
| Lease | Owner | Scope | Acquired | Released | Reason |

## Packet outcomes
| Packet | Candidate | Mutation | Result | Failure class |

## Proof DAG
| Node | Fingerprint | Status | Cache hit | Duration |

## Metrics
- time to dispatch
- time to first write
- time to first green
- time to accepted
- model wall
- tool calls
- credits
- proof cache hits
- broad gate count

## Deviations
- plan vs actual
- unexpected route changes
- blocked/failed readiness
- base/contract drift

## Accepted facts
Facts only from verified environment/proof.

## Optimization note
Generated candidate observations; not automatic policy changes.
```

---

# 15. End-of-run story report

A story/run report aggregates all waves.

```text
run-summary.md
```

Required sections:

1. Finish line and protected invariants.
2. Wave graph.
3. Planned vs actual topology.
4. Route/model/effort use.
5. State-transition anomalies.
6. Authority/lease anomalies.
7. Failure and REPLAN taxonomy.
8. Proof DAG + cache reuse.
9. Time-to-accepted decomposition.
10. Credits/cost by accepted packet.
11. Rework and Sol repair burden.
12. Checkpoints.
13. Lessons.
14. Candidate policy changes.
15. Confidence/sample-size warning.

This is the main artifact committed for future optimization.

---

# 16. Route ledger becomes a materialized view

Do not manually maintain a second source of truth.

Derive route ledger rows from canonical events.

Suggested materialized fields:

```text
RUN_ID
WAVE_ID
TASK_ID
STORY_ID
TASK_CLASS
BEHAVIOR_PACKET
PACKET_FP
BASE_HEAD
WORKTREE_FP
CONTRACT_FP
EXECUTION_MODE
ROUTE_REQUESTED
ROUTE_RESOLVED
MODEL
EFFORT
ORACLE_STRENGTH
INTEGRATION_WIDTH
SERIALITY
TOOL_DENSITY
RISK_CLASS
PACKET_CONTEXT_BYTES
INPUT_TOKENS
CACHED_INPUT_TOKENS
OUTPUT_TOKENS
REASONING_TOKENS
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

---

# 17. Timing model must become causal

Current performance gap estimate is useful but insufficient.

Each wave needs timestamps for:

```text
T0 run/wave start
T1 route decision
T2 first dispatch
T3 model accepted request
T4 first useful evidence
T5 first write/candidate
T6 first focused green
T7 boundary green
T8 broad green
T9 Sol acceptance
T10 checkpoint
```

Derived metrics:

```text
ROUTING_LATENCY         = T2-T0
MODEL_STARTUP_LATENCY   = T3-T2
TIME_TO_FIRST_WRITE     = T5-T0
TIME_TO_FIRST_GREEN     = T6-T0
PROOF_TAIL              = T8-T6
ACCEPTANCE_TAIL         = T9-T8
TIME_TO_ACCEPTED        = T9-T0
CHECKPOINT_TAIL         = T10-T9
```

For parallel wave, also calculate critical path from event DAG, not sum of lane durations.

---

# 18. Proof ledger

Proof must be a first-class durable object.

Schema:

```text
proof_id
run_id
wave_id
stage_id
stage_version
fingerprint
command_hash
declared_input_hash
toolchain_hash
upstream_proof_fps
started_at
finished_at
status
exit_code
duration_ms
output_hash
artifact_ref
cache_hit
invalidated_at
invalidation_reason
```

## 18.1 Proof reuse rule

```text
reuse iff:
    stage_id matches
    stage_version matches
    fingerprint matches
    required upstream fingerprints match
    status == PASS
```

No timestamp-only reuse.

## 18.2 Wrapper timeout

```text
wrapper timeout
-> retain every completed proof node
-> resume first missing/invalid node
```

Never restart from stage 1 automatically.

---

# 19. OTel mapping

Use OTel as projection from canonical events.

Suggested root span:

```text
invoke_workflow coding_tools_orchestration
```

Child spans:

```text
plan
invoke_agent <route>
execute_tool <tool>
proof <stage>
replan
```

Use standard GenAI attrs where applicable:

```text
gen_ai.operation.name
gen_ai.provider.name
gen_ai.request.model
gen_ai.agent.name
gen_ai.conversation.id
```

Custom low-cardinality attrs:

```text
orchestration.mode
orchestration.state
orchestration.route
orchestration.failure_class
orchestration.wave.number
orchestration.risk
orchestration.oracle_strength
orchestration.integration_width
orchestration.seriality
orchestration.cache_hit
```

High-cardinality IDs may be stored on spans/logs where backend supports them but should not become metric labels.

Important:

```text
delegation_id is retained in canonical ledger even if OTel schema evolves.
```

---

# 20. Privacy and security policy

## 20.1 Never log private chain-of-thought

Persist:

- route decision result;
- reason code;
- evidence IDs;
- failure class;
- accepted facts.

Do not persist hidden reasoning narrative.

## 20.2 Remote telemetry

Never export by default:

- raw prompt;
- source contents;
- tool stdout/stderr;
- secrets/env;
- auth token;
- absolute local paths;
- arbitrary command arguments.

Use:

- normalized code;
- relative/sanitized identifiers;
- hashes;
- byte counts;
- low-cardinality categories.

## 20.3 Local ledger

Local ledger may retain more operational detail but still passes through existing secret-value/env scrubbing.

Detailed artifacts should have retention limits.

---

# 21. Retention tiers

Recommended:

```text
TIER A — canonical compact events
retain long-term locally

TIER B — raw command/model artifacts
short retention, configurable

TIER C — generated sanitized Markdown
commit when useful

TIER D — OTel remote observability
backend policy/sampling dependent
```

Example defaults:

```text
compact event DB:        180 days or size cap
raw artifacts:           14–30 days
wave reports:            durable
research aggregates:     durable
```

Do not hard-code retention until repository/user policy is settled.

---

# 22. Rollout W0 — Audit substrate first

## Goal

Create reliable data before changing adaptive policy.

## Changes

New modules:

```text
orchestration_ledger.py
orchestration_events.py
orchestration_report.py
```

Integrations:

```text
server.py
codex_bridge.py
TaskStateStore projection
PerformanceTrace projection
```

## Behavior

Shadow only:

- existing routing result unchanged;
- append run/wave/state/route/model/proof events;
- generate report;
- compare ledger totals with existing task/performance state.

## W0 acceptance

```text
EVENT_LOSS_IN_CONTROLLED_TEST = 0
EVENT_SEQUENCE_DUPLICATE = 0
RUN/WAVE RECONSTRUCTION = deterministic
EXISTING ROUTING BEHAVIOR = unchanged
SECRET LEAK FIXTURE = 0
LEDGER_WRITE_FAILURE = surfaced
REPORT = reproducible from DB
```

## W0 test cases

1. normal MCP-only task;
2. Mini candidate task;
3. deadline interruption;
4. capacity failure;
5. MCP process restart/resume;
6. task clear/archive;
7. concurrent read during append;
8. secret-like payload scrubbing.

---

# 23. Rollout W1 — Hard EOCL authority/state enforcement

## Goal

Eliminate silent topology drift.

## Implement

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

State is projected from ledger or transactionally updated with ledger append.

## Hard guards

```text
NO ROUTE CHANGE WITHOUT TRANSITION
NO WRITE OWNER CHANGE WITHOUT TRANSFER
NO FEATURE WRITE WHILE STATE=REPLAN
NO DESKTOP DISPATCH WHILE READY=false
NO MUTATION ON BASE/WORKTREE FP MISMATCH
```

## W1 acceptance

```text
SILENT_MODE_DRIFT = 0
WRITE_WITHOUT_ACTIVE_LEASE = 0
DEEP_FAILURE_WITHOUT_REPLAN = 0
REPLAN_WITHOUT_REASON_CODE = 0
UNLOGGED_STATE_TRANSITION = 0
```

## Operational policy

After W1 passes, high-risk finance/auth/privacy stories may use EOCL mode again.

---

# 24. Rollout W2 — Proof DAG and resumable verification

## Goal

Stop losing proof because wrapper tail timed out.

## Implement

- proof stage registry;
- proof fingerprint function;
- proof store/index;
- cache-hit event;
- missing-node executor;
- broad-gate once-per-integrated-fingerprint rule.

## W2 acceptance

```text
REUSED_PROOF_WITH_MISMATCHED_FP = 0
COMPLETED_PROOF_ERASED_BY_WRAPPER_TIMEOUT = 0
BROAD_GATE_RUNS_PER_FINAL_FP <= 1 unless explicit invalidation
PROOF_LINEAGE_RECONSTRUCTABLE = true
```

## Benchmark

Use known long wrappers such as PFM/BFF-style staged proof fixtures to measure:

- wall time saved;
- duplicate command count;
- proof cache hit rate;
- failure localization latency.

---

# 25. Rollout W3 — Behavior packets and coordination waves

## Goal

Make delegation unit coherent and parallelism safe.

## Implement

Packet schema:

```text
packet_id
behavior
objective
scope
allowed_paths
settled_invariants
contract_fp
base_head
worktree_fp
proof_plan
stop_conditions
```

Coordination mode:

```text
COORDINATED_MULTI_WORKTREE only if:
  independent_workstreams >= 2
  contract_frozen
  writes_disjoint
  supervisor_ready
  integration_capacity_available
```

## W3 logging requirement

Every wave must include:

- `wave.started` manifest;
- readiness snapshot;
- delegation graph;
- lease graph;
- packet outcomes;
- proof graph;
- wave summary MD.

## W3 acceptance

```text
PARALLEL_SHARED_CHECKOUT_WRITERS = 0
PACKET_WITHOUT_PROOF_PLAN = 0
PACKET_ON_STALE_CONTRACT = 0
WAVE_WITHOUT_SUMMARY = 0
```

---

# 26. Rollout W4 — Adaptive route optimization

Only after W0–W3 create reliable labels.

## Start with simple historical retrieval

Features:

```text
TASK_CLASS
RISK
ORACLE_STRENGTH
INTEGRATION_WIDTH
SERIALITY
TOOL_DENSITY
PACKET_QUALITY
CONTEXT_BYTES
CONTRACT_STABILITY
WRITE_OVERLAP
CACHE_STATE
CAPACITY_STATE
```

Query recent similar accepted waves.

Do not train a learned router first.

## Promotion gate

A route is promoted per class only if representative samples show:

1. no worse correctness/critical-defect floor;
2. first-pass acceptance high enough;
3. lower or materially better TTA distribution;
4. lower expected accepted-result cost;
5. no increase in Sol repair/integration burden;
6. acceptable capacity behavior;
7. stable after runtime/model version changes.

No promotion from 3–4 successes.

---

# 27. Rollout W5 — Continuous evaluation

Periodically generate:

```text
docs/research/orchestration-evaluation-<date>.md
```

Contents:

- task-class counts;
- route distribution;
- acceptance by route/class;
- capacity/deadline rates;
- median/p90 TTA;
- proof cache savings;
- controller drift attempts blocked;
- replan reasons;
- Sol repair turns;
- cost/accepted result;
- single-lane vs parallel wave comparison;
- model/version changes.

Policy change must reference evidence window/run IDs.

---

# 28. Exact code change map

## `task_state.py`

Keep as projection/UI state.

Change:

- add current `run_id`, `wave_id`, orchestration state summary;
- no longer rely on rolling events for forensic history;
- projection rebuilt/recovered from canonical ledger when needed.

## `performance_trace.py`

Either:

1. derive its aggregates from canonical event ledger; or
2. keep lightweight store but attach run/wave/span IDs.

Recommended long-term: materialized view from ledger.

## `telemetry.py`

Do not turn product telemetry into audit log.

Add only safe aggregate orchestration counters if useful.

## `server.py`

Main integration points:

- run/wave start;
- mode/route decision;
- state transition;
- readiness gate;
- write lease acquisition/validation;
- tool/mutation/proof hooks;
- REPLAN/failure normalization;
- report generation trigger.

## `codex_bridge.py`

Emit:

```text
model requested/resolved
effort requested/resolved
profile
thread/session id (sanitized/local)
start/end/deadline/capacity
token usage/cache usage
candidate/diff hash
```

## build/proof layer

Add:

- proof stage ID/version;
- declared input fingerprint;
- proof event emission;
- result cache.

---

# 29. Database schema proposal

Minimal SQLite tables:

```sql
runs(
  run_id TEXT PRIMARY KEY,
  task_id TEXT,
  story_id TEXT,
  repo_id TEXT,
  branch TEXT,
  base_head TEXT,
  started_at TEXT,
  ended_at TEXT,
  outcome TEXT
);

waves(
  wave_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  wave_no INTEGER NOT NULL,
  manifest_hash TEXT NOT NULL,
  execution_mode TEXT,
  contract_fp TEXT,
  worktree_fp TEXT,
  started_at TEXT,
  ended_at TEXT,
  outcome TEXT
);

events(
  sequence INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id TEXT UNIQUE NOT NULL,
  run_id TEXT NOT NULL,
  wave_id TEXT,
  delegation_id TEXT,
  parent_delegation_id TEXT,
  causation_event_id TEXT,
  trace_id TEXT,
  span_id TEXT,
  event_type TEXT NOT NULL,
  recorded_at TEXT NOT NULL,
  state_before TEXT,
  state_after TEXT,
  actor_plane TEXT,
  actor_role TEXT,
  status TEXT,
  failure_class TEXT,
  duration_ms INTEGER,
  payload_json TEXT,
  payload_hash TEXT
);

proofs(
  proof_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  wave_id TEXT,
  stage_id TEXT NOT NULL,
  stage_version TEXT NOT NULL,
  fingerprint TEXT NOT NULL,
  status TEXT NOT NULL,
  duration_ms INTEGER,
  cache_hit INTEGER NOT NULL,
  output_hash TEXT,
  artifact_ref TEXT,
  UNIQUE(stage_id, stage_version, fingerprint)
);
```

Indexes:

```text
events(run_id, sequence)
events(wave_id, sequence)
events(delegation_id, sequence)
events(event_type, recorded_at)
proofs(stage_id, fingerprint)
```

Do not denormalize every route metric into write-time tables initially. Build views after event semantics stabilize.

---

# 30. Crash/restart semantics

On MCP restart:

1. open ledger;
2. inspect latest run/wave state;
3. identify leases without terminal release;
4. verify owning process/thread/worktree liveness;
5. mark stale lease as `recovery_required`, never silently reclaim;
6. reconstruct current TaskState projection;
7. require explicit REPLAN or resume path;
8. continue sequence.

Log:

```text
runtime.recovered
lease.stale_detected
state.recovered
```

No history inference from timestamps alone.

---

# 31. Tamper/error detection

For high-value local audit, optional hash chain:

```text
event_hash = SHA256(canonical_event_without_hash + prev_event_hash)
```

Benefits:

- detect accidental edit/truncation;
- bind generated report to event bundle.

Not required for W0 if it adds too much code; schema should reserve fields:

```text
prev_event_hash
event_hash
```

---

# 32. What to compare after 20–30 real waves

## 32.1 Packet class

```text
localized deterministic
bounded candidate
harder bounded leaf
deep single-lane
true parallel multi-worktree
critical finance/auth/privacy
```

## 32.2 Metrics

```text
first-pass accepted
TTA median/p90
model credits / accepted behavior
Sol repair turns
proof tail
proof cache hit rate
failure rate by class
replan count
patch ambiguity rate
controller drift blocked count
readiness failure rate
parallel speedup vs coordination overhead
```

## 32.3 Questions answerable for the first time

- Mini vs Luna: class nào thật sự có economic difference?
- Sol xhigh: class nào giảm rework đủ để bù credits?
- Desktop: khi nào persistent context giảm TTA?
- parallel BE/FE: speedup thật hay merge/review tax?
- proof cache: tiết kiệm bao nhiêu wall time?
- packet size/context bytes nào bắt đầu tăng BLOCKED/PROMPT_TOO_LARGE?
- supervisor readiness instability có đáng giữ persistent coordination không?

---

# 33. Wave-level optimization rules

After every wave, generator may flag observations but must not automatically rewrite policy.

Examples:

```text
FLAG: repeated PROMPT_TOO_LARGE for context > X bytes
FLAG: Mini blocked > threshold for task class
FLAG: proof stage cache hit saves high wall time
FLAG: Desktop readiness failure repeated
FLAG: p90 TTA regression after runtime update
FLAG: high Sol repair turns after lower-tier route
```

A policy change requires:

```text
multiple representative waves
+ evidence review
+ explicit decision record
```

---

# 34. Recommended operating procedure for every future coordination wave

## Before wave

```text
1. Resolve run/story objective.
2. Read current state capsule.
3. Verify base/worktree/contract fingerprints.
4. Validate cheapest authoritative oracle.
5. Classify risk/width/seriality/tool density.
6. Select execution mode.
7. Check mode-specific readiness.
8. Build coherent behavior packet(s).
9. Create delegation/write lease plan.
10. Persist wave manifest.
11. Only then dispatch.
```

## During wave

```text
1. Keep one write owner per mutable surface.
2. Emit model/tool/mutation/proof lifecycle events.
3. On typed failure, release authority before REPLAN.
4. Do not unchanged-retry.
5. Do not update state capsule from executor narrative alone.
6. Update accepted facts only from environment/proof.
7. Invalidate dependent packet if contract/base changes.
```

## After wave

```text
1. Complete required proof nodes.
2. Sol accepts/rejects.
3. Close leases/delegations.
4. Close wave.
5. Generate wave report.
6. Create technical checkpoint if stable boundary accepted.
7. Keep governance status independent.
8. Feed materialized metrics into historical route dataset.
```

---

# 35. Example: future finance feature

Suppose next feature has backend finance semantics + UI.

## Wave 0 — semantic/control

```text
ChatWeb Sol
-> freeze finance meaning/public contract
-> no implementation writer yet
```

Log:

```text
wave.started
mode.selected(control_only)
contract.frozen
wave.accepted
```

## Wave 1 — backend deep lane

```text
mode = DEEP_SINGLE_LANE
route = Codex Sol xhigh
worktree = isolated backend
```

Precondition:

```text
Desktop/App Server READY
write lease active
```

On `PROMPT_TOO_LARGE`:

```text
model.dispatch.interrupted/failed
failure.classified(PROMPT_TOO_LARGE)
write_lease.released
state EXECUTING -> REPLAN
packet rebuilt by behavior boundary
```

No controller micro-patching until explicit ownership transfer.

## Wave 2 — frontend

Only after backend contract fingerprint frozen.

May be:

```text
Mini/Luna candidate
or
Sol xhigh deep lane
```

according to actual complexity.

## Wave 3 — integration

Execute only missing proof nodes.

Broad gate once on final integration fingerprint.

Generate run summary.

---

# 36. Acceptance criteria for the logging system itself

Hard correctness:

```text
UNLOGGED_CONTROL_TRANSITION = 0
UNLOGGED_WRITE = 0
EVENT_ORDER_AMBIGUITY_WITHIN_RUN = 0
DELEGATION_WITHOUT_ID = 0
WRITE_LEASE_WITHOUT_DELEGATION = 0
REUSED_PROOF_WITH_WRONG_FP = 0
WAVE_WITHOUT_TERMINAL_EVENT = 0 after recovery handling
REPORT_FACT_NOT_DERIVABLE_FROM_LEDGER = 0
```

Privacy:

```text
SECRET_FIXTURE_LEAK = 0
RAW_CHAIN_OF_THOUGHT_LOGGED = 0
REMOTE_RAW_SOURCE_LOGGED = 0
REMOTE_RAW_PROMPT_LOGGED = 0 by default
```

Performance:

Set baseline first.

Target principle:

```text
ledger append overhead must be small relative to MCP/model/tool latency
```

Do not invent a percentage before measurement.

---

# 37. What not to do

Do not:

- use PostHog product telemetry as audit database;
- use a rolling 100-event task list as forensic history;
- commit raw prompts/tool outputs to Git;
- log chain-of-thought;
- use timestamps alone to infer delegation;
- assume trace parentage equals write authority;
- emit high-cardinality IDs as metric labels;
- build learned router before clean labels exist;
- optimize model prices before proof/rework/latency are measured;
- create one Markdown manually per tool call;
- fan out workers merely to generate more telemetry;
- make logging failure silently disappear on control transitions;
- allow wave summary to become a second manually edited source of truth.

---

# 38. Final recommended sequence

```text
FIRST
  build OrchestrationLedger + wave identity + event schema

THEN
  instrument existing route/state/model/proof flows in shadow mode

THEN
  hard-enforce readiness/state/write ownership

THEN
  proof DAG + fingerprints + resumable verification

THEN
  behavior-packet/worktree coordination

THEN
  class-specific routing optimization from measured history
```

This sequence is optimal because it simultaneously satisfies:

1. **correctness:** hard authority/state gates arrive before next high-risk coordinated story;
2. **learnability:** each implementation wave produces data about itself;
3. **economics:** no repeated blind benchmark/reconstruction;
4. **forensics:** future incident can be reconstructed from durable facts;
5. **maintainability:** one canonical event source drives state, metrics, OTel and documentation;
6. **privacy:** detailed local audit and remote observability remain separate;
7. **routing quality:** future model/topology decisions use accepted-result evidence, not intuition.

---

# 39. Implementation decision

## Production model policy

**UNCHANGED for now.**

## Production smart tool surface

**KEEP 8 tools.**

## Next code change priority

```text
P0: Orchestration Audit Ledger + wave/run/delegation identity
P1: EOCL state/write authority enforcement
P2: proof DAG/fingerprint/cache
P3: coordination/worktree wave machinery
P4: historical adaptive optimization
```

## First mandatory artifact after implementation starts

Every engineering wave implementing P0–P4 must itself produce:

```text
wave manifest
+ canonical event records
+ proof records
+ generated wave summary
+ checkpoint/result reference
```

That creates a self-observing optimization loop: the system used to improve orchestration is itself evaluated by the same orchestration evidence model.

---

# 40. References

## Local decision records

- `docs/research/EXECUTOR_ROUTING_BENCHMARK_2026-08-12.md`
- `docs/research/MODEL_ORCHESTRATION_RESEARCH_PHASE2_2026-08-12.md`
- `docs/research/ORCHESTRATION_METHODOLOGY_EXPERIMENTS_AND_PRODUCTION_DECISION_2026-08-12.md`
- `docs/research/PFM_ORCHESTRATION_RUNTIME_POSTMORTEM_AND_ENFORCED_CONTROL_LOOP_RESEARCH_2026-08-13.md`

## Research

1. Mishra, A.; Sharad, K. **Observability for Delegated Execution in Agentic AI Systems.** arXiv:2606.09692, 2026.  
   https://arxiv.org/abs/2606.09692

2. Chen, M. et al. **Seeing the Whole Elephant: A Benchmark for Failure Attribution in LLM-based Multi-Agent Systems.** ACL 2026. DOI `10.18653/v1/2026.acl-long.912`.  
   https://aclanthology.org/2026.acl-long.912/

3. AlSayyad, A.; Huang, K. Y.; Pal, R. **AgentTrace: A Structured Logging Framework for Agent System Observability.** arXiv:2602.10133, 2026.  
   https://arxiv.org/abs/2602.10133

4. Wang, Z. et al. **Turning Interaction History into Execution State: A Runtime Layer for Long-Horizon Coding Agents.** arXiv:2608.00808, 2026.  
   https://arxiv.org/abs/2608.00808

5. OpenTelemetry. **GenAI Semantic Conventions.**  
   https://github.com/open-telemetry/semantic-conventions-genai

6. OpenTelemetry. **Tracing SDK / Sampling.**  
   https://opentelemetry.io/docs/specs/otel/trace/sdk/

7. OpenTelemetry. **Logs Specification / Data Model.**  
   https://opentelemetry.io/docs/specs/otel/logs/

8. W3C. **Trace Context Recommendation.**  
   https://www.w3.org/TR/trace-context/

---

# 41. One-line decision

> **Do not optimize the next coordination wave until that wave can prove who owned it, what state it was in, what evidence remained valid, what changed, what failed, and how the accepted result was reached.**
