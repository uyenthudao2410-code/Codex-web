# 260814 — Phân tích, phương pháp luận và kế hoạch tổng thể Execution Hub cho ChatWeb ⇄ Codex Desktop

**Ngày:** 2026-08-14  
**Workspace đánh giá:** `E:\DEV\Tools-Codex-web`  
**Mục đích:** tài liệu thiết kế/đánh giá và source-of-truth cho rollout Execution Hub.  
**Trạng thái:** **SOURCE IMPLEMENTED / FOCUSED PROOFS PASS / LIVE ACTIVATION PENDING**. Thiết kế đã được duyệt và triển khai source ngày 2026-08-14; còn full Electron restart + real two-client live canary trước khi gọi FULL LIVE PASS.  
**Phạm vi:** hợp nhất ChatWeb, Codex Desktop, Coding Tools MCP và Electron thành một hệ điều phối bền vững có giao diện Hub trực quan, giải quyết long-running work, giới hạn context, ownership, routing/cost, handoff và quan sát vận hành.

> Báo cáo triển khai chi tiết, accepted work packages, focused proofs và live activation checklist: `docs/research/260814_EXECUTION_HUB_IMPLEMENTATION_STATUS.md`.

---

## 0. Executive summary

Mục tiêu không phải làm cho ChatWeb “sống lâu như Codex Desktop”, cũng không phải cố đưa toàn bộ lịch sử dự án vào một context window rất lớn. Mục tiêu đúng là:

> **Conversation có thể ngắn và thay thế được; execution phải bền vững, có một nguồn sự thật, có thể quan sát và chuyển frontend mà không mất task.**

Kiến trúc mục tiêu được chốt ở mức định hướng như sau:

```text
                         NGƯỜI DÙNG / OPERATOR
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
             CHATWEB CLIENT              CODEX DESKTOP CLIENT
        conversation / research /        deep coding / long-lived
        semantic control / accept        worker UI / investigation
                    │                           │
                    │ MCP/Tunnel                │ local stdio adapter
                    └─────────────┬─────────────┘
                                  ▼
                    ┌───────────────────────────┐
                    │ EXECUTION CONTROL HUB     │
                    │ ONE RUNTIME AUTHORITY     │
                    │                           │
                    │ task / run / wave         │
                    │ controller ownership      │
                    │ routing                   │
                    │ event journal             │
                    │ proof ledger              │
                    │ idempotency               │
                    │ write fence               │
                    │ client registry/cursors   │
                    │ handoff/resume             │
                    │ cost/health/telemetry      │
                    └─────────────┬─────────────┘
                                  │
                     adaptive workers/providers
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
              deterministic      Mini/Luna   Codex Sol lane
                    └─────────────┬─────────────┘
                                  ▼
                         SINGLE WRITE GATE
                                  ▼
                         REPOSITORY/WORKSPACE
```

### Kết luận quan trọng nhất

1. **Ý tưởng “1 ledger — 2 mặt trận” đúng**, nhưng production topology không nên là hai full MCP Runtime độc lập cùng mở `.coding-tools`.
2. Nên có **một Coding Tools Runtime duy nhất do Electron supervisor sở hữu**, ChatWeb và Codex Desktop chỉ là hai client/adapters.
3. Dự án **không bắt đầu từ số 0**: durable ledger, task projection, EOCL, proof, idempotency, write-fence primitive, handoff capsule, model lanes, restart supervisor và Control Panel đều đã tồn tại.
4. Phần còn thiếu chủ yếu là **multi-client authority + client registry/cursor + Desktop same-runtime adapter + Hub UI thống nhất + fault/E2E proof**.
5. Giới hạn context ChatWeb được giải bằng **externalized execution state + bounded resume packet + proactive context rotation**, không bằng context vô hạn.
6. P2 routing và auto-handoff phải tiếp tục **evidence-gated**; không tune chỉ vì implementation đã sẵn sàng.

---

# 1. Bài toán cần giải quyết

## 1.1 Bài toán ChatWeb

ChatWeb có các đặc điểm khiến nó không thể là execution authority duy nhất:

- browser/chat session có thể đổi hoặc kết thúc;
- một model turn không nên giữ sống trong hàng giờ chỉ để chờ build/test/worker;
- context window hữu hạn;
- lịch sử chat tăng dần gây context tax và giảm khả năng tập trung vào working set;
- connector/tool schema có lifecycle riêng của host;
- host có thể không hỗ trợ một số capability như interactive permission elicitation.

Nếu execution state chỉ nằm trong transcript thì xảy ra chuỗi lỗi:

```text
chat dài
  → context pressure
  → phải tóm tắt
  → summary của summary
  → mất detail/proof
  → chat mới reconstruct bằng trí nhớ
  → duplicate work hoặc sai state
```

## 1.2 Bài toán Codex Desktop

Codex Desktop phù hợp hơn với deep coding và persistent thread, nhưng nếu coi Desktop là nơi làm mọi task thì:

- routine leaf work vẫn có thể dùng tier đắt;
- model thread không nên được coi là database của project;
- thread persistence không thay thế proof, idempotency hoặc writer ownership;
- arbitrary live Desktop thread hiện không phải surface mà Coding Tools MCP có thể chiếm quyền một cách trung thực;
- nếu Desktop spawn một full MCP runtime khác, ownership có nguy cơ bị phân tán.

## 1.3 Bài toán phối hợp hai bên

Mục tiêu người dùng thực tế là đồng thời đạt:

### A. Continuity

Đổi ChatWeb ⇄ Codex Desktop mà không phải paste lại transcript, diff, task description hoặc kể “đang làm tới đâu”.

### B. Long-running execution

Task có thể chạy lâu hơn lifetime của một ChatWeb turn/session.

### C. Adaptive compute

Task nhỏ có strong oracle được route xuống deterministic/Mini/Luna; Sol chỉ giữ phần integration width cao, deep work hoặc final acceptance.

### D. Singular authority

Hai frontend không được trở thành hai writer/controller độc lập cùng sửa một workspace.

### E. Operator visibility

Người dùng phải nhìn một màn hình Hub và biết ngay:

- client nào online;
- ai đang controller;
- worker/model nào đang chạy;
- run/wave ở trạng thái nào;
- proof PASS/FAIL;
- ai giữ quyền write;
- context/handoff có an toàn không;
- có thể đóng/đổi ChatWeb hay chưa.

---

# 2. Phương pháp luận đánh giá

Tài liệu này dùng ba lớp evidence riêng biệt, không trộn lẫn.

## 2.1 Lớp A — Evidence từ source/runtime của dự án

Đây là bằng chứng mạnh nhất cho câu hỏi “dự án hiện đã làm được gì”.

Nguồn nội bộ chính:

- `docs/research/260813_CODEX_WEB_BIDIRECTIONAL_RESILIENT_ORCHESTRATION.md`
- `docs/research/260813_CODEX_WEB_ORCHESTRATION_BLUEPRINT.md`
- `docs/research/2026-08-14_POST_P1_FOLLOWUP_TRACKER.md`
- `docs/research/2026-08-14_REAL_CODEX_BENCHMARK_AND_TOKEN_USAGE.md`
- `docs/research/2026-08-14_SYSTEM_CAPABILITY_DEEP_TEST_SUITE.md`
- `docs/research/2026-08-14_CODEX_DESKTOP_CHATWEB_INTEGRATION_PLAN.md`
- `renderer/panel.html`
- `resources/coding-tools-mcp/coding_tools_mcp/orchestration_ledger.py`

Evidence được chia:

1. **Live runtime/durable measurement** — mạnh nhất cho activation hiện tại.
2. **Focused deterministic proof** — chứng minh semantics trong scope test.
3. **Real-model microbenchmark** — model/credits/cache/TTA thật nhưng sample nhỏ.
4. **Scenario simulation** — chỉ dùng regression/economics guard.
5. **Blocked candidate sample** — không được tính vào accepted routing cohort.

## 2.2 Lớp B — Nghiên cứu/primary source bên ngoài

Dùng để kiểm tra xem kiến trúc có phù hợp với thực tiễn production/research không.

Các nhóm tham khảo:

- OpenAI Codex App Server và long-lived runtime;
- long-context utilization;
- multi-agent centralized orchestration;
- cost-aware model routing;
- safety/calibration của cheap-model routing;
- tool-surface reduction;
- distributed ownership/locking;
- real-task agent evaluation và reliability metrics.

## 2.3 Lớp C — Suy luận thiết kế

Một thiết kế chỉ được đề xuất khi:

- giải một gap đã quan sát;
- tái sử dụng primitive hiện có khi có thể;
- không đưa complexity vào hot path nếu có thể giữ ở control plane;
- fail closed ở ownership/permission/destructive boundary;
- có test/fault-injection acceptance rule cụ thể.

Các claim trong lớp C phải được đánh dấu là **proposal**, không nâng thành “đã verified”.

---

# 3. Nghiên cứu và thực tiễn liên quan

## 3.1 OpenAI Codex App Server: UI không phải source of truth

OpenAI mô tả Codex App Server là một **long-lived process** quản lý thread lifecycle/persistence và streaming events. Thread có thể create, resume, fork, archive; history được persist để client reconnect và render lại timeline.

Đặc biệt với Codex Web, OpenAI nêu rõ web/browser session là ephemeral; tab có thể đóng, mạng có thể rớt, nên browser không thể là source of truth cho long-running task. State/progress phải giữ server-side để session mới reconnect và catch up.

**Áp dụng cho Tools-Codex-web:**

```text
ChatWeb session       ≠ execution session
Codex Desktop thread  ≠ execution session
```

Execution session phải thuộc Hub.

Điều này ủng hộ trực tiếp mô hình:

```text
many clients
    ↓
one durable runtime/control plane
```

Thay vì để transcript/UI sở hữu vòng đời công việc.

## 3.2 Long context: capacity không đồng nghĩa retrieval reliability

Nghiên cứu *Lost in the Middle* cho thấy model long-context có thể giảm hiệu năng khi thông tin cần thiết nằm ở vị trí bất lợi trong context; long window không đồng nghĩa model khai thác mọi token đồng đều.

Do đó “1M token” không nên được xem như project RAM.

Mô hình đúng là hierarchical memory/working set:

```text
L0  model context       — bounded working set hiện tại
L1  resume/handoff      — bounded checkpoint/capsule
L2  execution ledger    — durable run/events/proofs
L3  repository          — source/tests/history/artifacts
```

Model chỉ nhận dữ liệu cần thiết cho quyết định hiện tại.

## 3.3 Multi-agent: centralized orchestration tốt hơn cho workflow tuần tự

Google Research đánh giá 180 agent configurations trên nhiều kiến trúc. Kết quả công bố cho thấy multi-agent có thể giúp task parallelizable nhưng gây penalty lớn trên sequential planning; centralized hub-and-spoke giúp kiểm soát error amplification tốt hơn independent agents.

**Áp dụng:**

Không dùng mô hình:

```text
ChatWeb autonomous controller
+
Desktop autonomous controller
+
shared SQLite
```

Mà dùng:

```text
ONE controller authority at a time
+
worker lanes bounded by Hub
```

Hai “mặt trận” là hai frontend, không phải hai sovereign controller.

## 3.4 MTRouter: routing theo task/history, không dùng model đắt cho mọi lượt

MTRouter (ACL 2026) nghiên cứu cost-aware routing trên multi-turn long-horizon tasks và báo cáo trade-off cost/performance tốt hơn khi routing theo history/task/model utility. Một quan sát quan trọng là router hiệu quả không nhất thiết chuyển model liên tục; transient failures không nên tạo cascade vô hạn.

**Áp dụng:**

- deterministic trước;
- Mini/Luna cho bounded leaf khi oracle đủ mạnh;
- Sol cho integration width cao, deep work, conflict, acceptance;
- tránh Mini→Luna→Sol ladder mặc định trên mọi request;
- đánh giá bằng `credits / accepted task`, không chỉ giá một worker call.

## 3.5 Conformal routing: không promote cheap route từ sample nhỏ

Nghiên cứu *Conformal LLM Routing with Distribution-Free Safety Guarantees* nhấn mạnh routing cheap model cần safety calibration, không chỉ tối ưu mean cost/accuracy.

**Áp dụng:**

P2 hiện giữ threshold chưa đổi vì accepted Mini/Luna representative samples chưa đủ là quyết định đúng. Blocked calls không được biến thành accepted evidence.

## 3.6 ToolScope: tool surface nhỏ giảm ambiguity/context tax

ToolScope (ACL 2026) nghiên cứu redundancy/overlap trong toolset và context-aware filtering/merging.

**Áp dụng:**

Giữ `smart-v3` 8 public tools là hướng đúng. Multi-client integration không nên thêm một loạt top-level tools chỉ để phục vụ UI. Hub nên mở rộng internal projection/control endpoint và tận dụng `task_control`/`agent_workflow` hiện có.

## 3.7 SQLite WAL không giải quyết orchestration ownership

SQLite WAL cho phép readers và writer hoạt động đồng thời, nhưng tài liệu SQLite vẫn chỉ ra WAL chuẩn chỉ có một writer tại một thời điểm.

Điều này bảo vệ database transaction, **không tự quyết định semantic authority**:

```text
DB biết ai COMMIT trước
≠
Hub biết ai được phép sửa workspace
```

Hai process có thể tuần tự ghi ledger hoàn toàn hợp lệ nhưng cùng tin rằng mình là controller/writer của cùng task.

Vì vậy “hai full MCP process cùng mở SQLite WAL” chỉ phù hợp prototype/shadow experiment, không nên là topology production mặc định.

## 3.8 Chubby và distributed lock thinking

Google Chubby là ví dụ kinh điển về coarse-grained distributed lock/reliable coordination. Bài học áp dụng không phải xây lại Chubby, mà là:

> Khi có nhiều actor có thể thay đổi cùng state, ownership/lease/fencing phải là khái niệm riêng, không được suy ra từ shared storage.

Dự án hiện đã có write-fence primitive với fencing token, lease, TTL/renew/assert/release — đây là nền móng tốt. Nhưng controller ownership giữa ChatWeb/Desktop cần được mô hình hóa riêng.

## 3.9 SWE-bench và τ-bench: đánh giá bằng task thật và reliability nhiều lần

SWE-bench dùng real GitHub issues + test oracle thay vì synthetic Q&A. τ-bench nhấn mạnh reliability qua nhiều lần thử (`pass^k`), không coi một lần thành công là đủ.

**Áp dụng:**

- rollout Hub phải dùng real task canaries;
- long-running/handoff/reconnect phải chạy lặp nhiều lần;
- acceptance cuối dựa vào repository/proof/state, không dựa vào model tự báo “done”.

---

# 4. Điều chỉnh các giả định trong kế hoạch cũ

File `2026-08-14_CODEX_DESKTOP_CHATWEB_INTEGRATION_PLAN.md` là một prototype direction tốt nhưng có hai giả định cần sửa trước production rollout.

## 4.1 Workspace path cũ đã stale

Tài liệu cũ ghi nhiều vị trí:

```text
E:\Github\Tools-Codex-web
```

Authoritative workspace hiện tại là:

```text
E:\DEV\Tools-Codex-web
```

Nếu Desktop config vẫn dùng `PYTHONPATH=E:\Github\...` trong khi cwd/ledger dùng `E:\DEV\...`, có thể tạo tình trạng nguy hiểm:

```text
same ledger
but different runtime source/version
```

**Gate đầu tiên của rollout phải audit và sửa config này.**

## 4.2 Hai full MCP Runtime cùng share ledger không phải final topology

Prototype cũ:

```text
ChatWeb → Runtime A ─┐
                    ├→ shared .coding-tools
Desktop → Runtime B ─┘
```

Production target:

```text
ChatWeb ─────────────┐
                     ▼
                ONE RUNTIME
                     ▲
Desktop stdio proxy ─┘
```

Lợi ích:

- một in-memory runtime truth;
- một background-operation registry;
- một router;
- một write-fence manager;
- một idempotency authority;
- một service owner/restart path;
- không cần distributed coordination giữa hai local MCP authorities trong common case.

---

# 5. Trạng thái dự án hiện tại

## 5.1 Backend Hub primitives đã có

Theo source/tracker hiện tại:

| Primitive | Trạng thái |
|---|---|
| Durable run/wave ledger | PASS/IMPLEMENTED |
| Append-only events + hash chain | IMPLEMENTED |
| Task projection | IMPLEMENTED |
| Proof ledger + proof cache | LIVE PASS |
| Idempotency replay/conflict | LIVE PASS |
| Handoff capsule ≤8 KiB | PASS |
| Agent lane registry | IMPLEMENTED |
| Coordination messages | IMPLEMENTED |
| Background operations | IMPLEMENTED, recovery semantics bounded |
| EOCL state machine | LIVE |
| Electron-supervised restart | FULL LIVE PASS |
| Contract fingerprint/stale connector detection | FULL LIVE PASS |
| Permission unsupported fail-closed status | FULL LIVE PASS |
| Candidate deep-symbol packet localization | FULL LIVE PASS |
| Task/EOCL stop terminalization | FULL LIVE PASS |
| Write fence table/token/TTL primitives | IMPLEMENTED |
| Accepted cohort telemetry | 31/31 complete dimensions |
| Accepted representative non-deterministic cohorts | PENDING |
| Auto-handoff evidence | PENDING |

## 5.2 Hub UI đã có thật

Dự án hiện có hai surface:

### A. Electron “Trung tâm Quản lý”

Quản lý:

- workspace;
- MCP runtime;
- tunnel;
- health/repair;
- restart;
- permission/config;
- task/build/logs;
- connector stale detection.

### B. Orchestration Control Panel cạnh ChatGPT

Nguồn:

```text
renderer/panel.html
renderer/panel.js
electron/panelPreload.js
electron/main.js
```

Endpoint:

```text
GET /__control/orchestration
```

Panel hiện hiển thị:

- task objective/status/progress/current command;
- run/wave/execution mode/base HEAD;
- event timeline;
- proofs;
- delegations;
- MCP/Tunnel status;
- pause/resume/stop;
- record handoff capsule;
- refresh theo chu kỳ.

**Kết luận:** Hub UI không phải greenfield. Cần nâng cấp panel hiện tại thành **Multi-Client Execution Control Center**.

## 5.3 Những gì UI/Hub chưa có

| Gap | Trạng thái |
|---|---|
| ChatWeb client identity/card | NOT IMPLEMENTED |
| Codex Desktop client identity/card | NOT IMPLEMENTED |
| Online/last-seen per client | NOT IMPLEMENTED |
| Controller owner | NOT IMPLEMENTED |
| Controller lease/TTL | NOT IMPLEMENTED |
| Durable per-client event cursor | PARTIAL primitives |
| Desktop → same Runtime stdio adapter | NOT IMPLEMENTED |
| Visual handoff/ack state | NOT IMPLEMENTED |
| Context-pressure state | NOT IMPLEMENTED |
| `SAFE TO ROTATE CHATWEB` verdict | NOT IMPLEMENTED |
| End-to-end two-client fault suite | NOT IMPLEMENTED |

---

# 6. Kiến trúc mục tiêu chi tiết

## 6.1 Roles phải tách rõ

Không dùng từ “agent” cho mọi thứ. Hub nên phân biệt:

```text
CLIENT      = UI/front-end kết nối vào Hub
CONTROLLER  = actor có quyền semantic decision cho run
WORKER      = lane thực hiện bounded work
WRITER      = authority thực hiện mutation lên authoritative checkout
ACCEPTOR    = authority final go/no-go
SUPERVISOR  = owner của runtime/service lifecycle
```

Baseline mục tiêu:

```text
ChatWeb        = client + semantic controller + final acceptor
Codex Desktop  = client + deep-code worker UI
Coding Runtime = writer + execution/proof authority
Electron       = supervisor + operator UI
Mini/Luna/Sol  = adaptive worker lanes
```

Sau này có thể handoff controller, nhưng không để hai controller active đồng thời cho cùng run.

## 6.2 Single Runtime Authority

Electron sở hữu một Coding Tools Runtime duy nhất.

### ChatWeb path

```text
ChatWeb
  → OpenAI MCP/Tunnel
  → Coding Tools Runtime
```

### Desktop path

Không spawn full `python -m coding_tools_mcp` authority thứ hai.

Dùng:

```text
Codex Desktop
  → stdio MCP shim/proxy
  → localhost authenticated control/MCP endpoint
  → SAME Coding Tools Runtime
```

Shim phải tối giản:

- translate stdio MCP framing;
- attach `client_id=desktop_*`;
- không có ledger riêng;
- không giữ execution authority;
- reconnect được;
- không tự restart runtime;
- version handshake với Hub.

## 6.3 Client Registry

Đề xuất bảng/state mới hoặc projection tương đương:

```text
client_id
client_type      chatweb | codex_desktop | electron | other
session_instance
role             controller | worker | observer
connected_at
last_seen_at
last_event_seq
capabilities
runtime_instance_id
contract_sha
status           online | stale | offline
metadata_safe
```

Không lưu secret/token/raw conversation id nếu không cần; identity có thể hash/domain-separate khi cần persistence.

## 6.4 Controller Lease

Controller lease khác write fence.

### Write fence

Bảo vệ **mutation**.

### Controller lease

Bảo vệ **semantic authority**:

- ai được reprioritize;
- ai được decide replan;
- ai được final accept/reject;
- ai được handoff controller.

Đề xuất:

```text
controller_scope = run_id
owner_client_id
lease_id
fencing_token
expires_at
last_heartbeat
status
```

Rules:

1. Một run có tối đa một active controller lease.
2. Lease token tăng đơn điệu khi ownership đổi.
3. Message/action từ controller cũ bị reject sau handoff.
4. `pause` không mặc nhiên chuyển controller.
5. Expiry không auto-grant Desktop nếu policy chưa cho phép; run có thể vào `WAITING_CONTROLLER`.
6. Final acceptance mặc định vẫn cần ChatWeb/Sol cho đến khi policy mới được evidence-proven.

## 6.5 Per-client durable cursor

Mỗi client phải catch up độc lập.

Ví dụ:

```text
ledger seq = 5000
chatweb cursor = 3200
desktop cursor = 4800
electron cursor = 5000
```

ChatWeb reconnect:

```text
events(after_seq=3200)
```

không replay 1..5000.

Cần tránh một client “consume” event làm client khác mất dữ liệu.

Command output đã có ý tưởng `consumer_id`; orchestration event stream cần cùng tinh thần.

## 6.6 Resume Packet / Context Compiler

Hub không chuyển toàn transcript.

Resume packet nên deterministic và mục tiêu nhỏ:

```text
GOAL
CURRENT RUN/WAVE
CONTROLLER/WRITER
BASE HEAD / WORKTREE IDENTITY
SETTLED DECISIONS
COMPLETED MILESTONES
LATEST PROOFS
CHANGED PATHS
OPEN RISKS/BLOCKERS
PENDING MESSAGES
NEXT ACTION
CURSOR
CAPSULE REF/HASH
```

Không chứa:

- raw transcript dài;
- full source files;
- full command logs;
- hidden reasoning;
- repeated summaries.

Nếu cần chi tiết, client truy xuất từ repository/ledger/proof bằng exact reference.

## 6.7 Proactive context rotation

Operational policy giữ tinh thần blueprint:

| Context pressure ước tính | Hành động |
|---|---|
| ~60–65% | delta-only, không replay output cũ |
| ~75% | checkpoint + capsule freshness check |
| ~85% | không nhận thêm long work vào chat hiện tại; chuẩn bị new chat |
| ~90%+ | chỉ critical/checkpoint/handoff |

Đây là policy nội bộ, không phải claim về giới hạn chính thức của ChatGPT.

Hub UI không nhất thiết phải biết token exact nếu host không expose. Có thể dùng trạng thái:

```text
NORMAL
ELEVATED
ROTATE_RECOMMENDED
ROTATE_REQUIRED
UNKNOWN
```

và luôn hiển thị nguồn/độ tin cậy của estimate.

## 6.8 Long-running work

Một ChatWeb call không được giữ sống hàng giờ.

Pattern:

```text
ChatWeb starts intent
  → Hub creates run + operation/lane
  → returns durable identity
  → worker continues outside ChatWeb turn
  → events/proofs accumulate
  → if semantic input needed: WAITING_INPUT
  → if final review needed: ACCEPTING/WAITING_CONTROLLER
```

ChatWeb có thể biến mất ở giữa.

Hub không được tự final-accept nếu policy yêu cầu human/ChatWeb semantic authority.

---

# 7. Thiết kế Execution Control Center

## 7.1 Mục tiêu UX

Nhìn một màn hình phải trả lời ngay tám câu:

1. ChatWeb có online không?
2. Codex Desktop có online không?
3. Ai là controller?
4. Worker/model nào đang chạy?
5. Run/wave đang ở phase nào?
6. Ai đang giữ write authority?
7. Proof hiện ra sao?
8. Có thể đóng/đổi ChatWeb an toàn hay chưa?

## 7.2 Overview đề xuất

```text
┌──────────────────────────────────────────────────────────────┐
│ EXECUTION CONTROL CENTER                         HEALTHY ●   │
├──────────────────────────────────────────────────────────────┤
│ CLIENTS                                                      │
│ ChatWeb       ● ONLINE   CONTROLLER   cursor #1287           │
│ Codex Desktop ● ONLINE   WORKER       cursor #1283           │
│ Electron      ● ONLINE   SUPERVISOR                           │
│ Controller lease: chatweb_01, TTL 58 s                       │
├──────────────────────────────────────────────────────────────┤
│ CURRENT EXECUTION                                            │
│ Task: Feature X                                              │
│ Run R123 · Wave 4 · PROVING                                  │
│ Route: Luna · Worker lane: codex_01                          │
│ Progress: ███████████████░░░ 76%                             │
├──────────────────────────────────────────────────────────────┤
│ PROOF                                                        │
│ unit tests      PASS                                         │
│ build           PASS                                         │
│ integration     RUNNING                                      │
├──────────────────────────────────────────────────────────────┤
│ AUTHORITY                                                    │
│ semantic controller  ChatWeb                                 │
│ writer               Coding Tools Runtime                    │
│ write fence           token #42 / valid                      │
│ final acceptor        ChatWeb Sol                            │
├──────────────────────────────────────────────────────────────┤
│ CONTINUITY                                                   │
│ capsule               CURRENT                                │
│ pending messages      2                                      │
│ context pressure      ELEVATED                               │
│ SAFE TO ROTATE CHATWEB: YES                                  │
└──────────────────────────────────────────────────────────────┘
```

## 7.3 Các tab/section đề xuất

### Overview

Operator summary + continuity verdict.

### Clients

- client identity;
- connection status;
- role;
- last seen;
- cursor lag;
- runtime/contract compatibility;
- capability badges.

### Execution

- task/run/wave;
- EOCL timeline;
- current operation;
- current command;
- worker lanes;
- controller ownership.

### Workers & Routing

- requested/resolved route;
- model/profile/effort nếu runtime có bằng chứng;
- cache/credits/TTA;
- blocked/cooldown state;
- reason route selected.

### Proof & Safety

- tests/build/proofs;
- proof cache status;
- idempotency status;
- write lease/fence;
- workspace/head drift;
- permission mode;
- orphan/stale counters.

### Continuity

- capsule freshness;
- client cursors;
- pending messages;
- last checkpoint;
- context pressure;
- safe-to-rotate verdict;
- handoff state and acknowledgements.

### Runtime

- process/server instance;
- MCP/Tunnel health;
- contract hash;
- restart control;
- supervisor state;
- diagnostics.

## 7.4 `SAFE TO ROTATE CHATWEB`

Đây nên là derived verdict, không phải nút đoán.

### YES khi tối thiểu

- durable run state exists;
- latest important decisions đã nằm ledger/capsule;
- no uncommitted semantic input chỉ tồn tại trong chat;
- active worker/operation có durable identity hoặc run đang ở safe wait state;
- proof/current base refs đã persist;
- no ownership conflict;
- event cursor/capsule không stale theo policy.

### NO khi

- chưa persist task/run;
- controller đang giữ quyết định chưa checkpoint;
- background side effect outcome unknown;
- capsule missing/stale trong khi cần rotation;
- handoff pending nhưng chưa ack;
- write/contract drift chưa resolve.

UI phải hiển thị `reason_codes`, không chỉ YES/NO.

---

# 8. Routing và economics sau khi có Hub

## 8.1 Desktop là frontend, không phải model tier

Quy tắc cần được code/UX củng cố:

```text
Task mở từ Codex Desktop
≠
Task bắt buộc chạy Sol
```

Desktop client có thể submit vào `agent_workflow`; Hub route xuống deterministic/Mini/Luna nếu task phù hợp.

## 8.2 Benchmark nội bộ hiện tại

Real-model microbenchmark cùng bounded packet:

| Lane | Credits đo thật | Ghi chú |
|---|---:|---|
| Mini low | ~0.0507 | oracle 3/3 |
| Mini continuation | ~0.0221 | cache ~96.6% |
| Luna high | ~0.2276 | oracle 3/3 |
| Sol xhigh | ~1.2482 | oracle 3/3 |

Trên packet cụ thể đó, Sol xhigh khoảng 24.6× Mini.

**Không được suy ra** toàn bộ Desktop task sẽ rẻ 24.6×, vì economics end-to-end là:

```text
controller cost
+ worker cost
+ packet/retrieval cost
+ proof
+ repair/retry
+ cache effects
```

KPI chính:

- credits / accepted task;
- TTA / accepted task;
- first-pass accepted rate;
- repairs / accepted;
- critical defect rate;
- duplicate-work rate;
- route-switch count;
- cache ratio.

## 8.3 P2 vẫn evidence-gated

Latest internal tracker có accepted cohort dimensions 31/31 nhưng accepted cohorts vẫn deterministic. Hai Mini observations là blocked pre-fix attempts.

Do đó rollout Hub **không đồng nghĩa** thay routing thresholds.

Hub chỉ giúp thu data đúng hơn.

---

# 9. Handoff strategy

## 9.1 Không copy transcript

Không:

```text
ChatWeb transcript → giant summary → Desktop
```

Dùng:

```text
execution state
+ checkpoint
+ capsule
+ proof refs
+ delta events
```

## 9.2 Same-thread vs fresh-thread

Internal A/B seed hiện có:

- same-thread continuation có cache cao hơn và incremental cost thấp hơn fresh resume trong sample hiện tại;
- capsule fresh resume vẫn PASS về state continuity.

Policy hợp lý hiện tại:

```text
healthy provider thread → continue same thread
rollover/recovery       → capsule/resume
controller auto-handoff → OFF cho đến khi đủ evidence
```

## 9.3 Handoff controller protocol đề xuất

```text
1. current controller requests handoff
2. Hub checkpoint/capsule
3. target client receives offer
4. target validates run/base/contract/cursor
5. target ACKs
6. Hub increments controller fencing token
7. old controller loses mutation/semantic authority
8. target becomes controller
9. all clients receive controller_changed event
```

Không đổi owner trước target ACK nếu không có explicit forced-recovery policy.

---

# 10. Security và authority invariants

Các invariant phải được test, không chỉ ghi docs.

1. **One semantic controller per run.**
2. **One authoritative writer per workspace scope.**
3. Worker model không được tự mutation authoritative checkout nếu lane policy chỉ cho candidate/review.
4. Stale fencing token bị reject.
5. Expired lease không được dùng để commit.
6. Duplicate delivery không tạo side effect thứ hai.
7. `ELICITATION_UNSUPPORTED` không thành permission grant.
8. Desktop adapter không được tự bypass server policy vì là local.
9. Client identity/cursor không chứa raw secrets.
10. Handoff capsule không chứa raw transcript, patch, stdout/stderr hoặc private chain-of-thought.
11. Restart lifecycle vẫn thuộc Electron supervisor.
12. Public MCP contract không bị phình chỉ vì dashboard cần thêm data.
13. Không giả vờ attach vào live arbitrary Codex Desktop thread khi capability không có.

---

# 11. Kế hoạch triển khai theo phase

## Phase 0 — Freeze architecture contract

**Mục tiêu:** duyệt quyết định trước khi code.

Quyết định cần chốt:

- single-runtime authority = YES;
- ChatWeb default semantic controller/final acceptor = YES ở giai đoạn đầu;
- Desktop = client/worker, không controller mặc định;
- no transcript sync;
- no second full Runtime in production topology;
- existing smart-v3 8-tool public surface được giữ nếu có thể;
- Hub UI nâng từ panel hiện tại, không xây frontend mới độc lập.

**Output:** architecture decision + interface contracts.

## Phase 1 — Audit Desktop config và prototype connectivity

### Việc làm

1. Kiểm tra actual Codex config.
2. Loại bỏ stale `E:\Github` nếu còn.
3. Xác minh Codex Desktop hiện spawn MCP thế nào.
4. Prototype stdio proxy → existing Runtime endpoint.
5. Handshake xác nhận:
   - runtime instance;
   - tool contract hash;
   - workspace identity;
   - client type/id.

### Acceptance

- Desktop nhìn cùng runtime instance với ChatWeb;
- không tạo ledger/runtime authority thứ hai;
- 8-tool contract tương thích;
- reconnect proxy không mất task.

## Phase 2 — Client Registry + per-client cursor

### Backend

Thêm projection/store tối thiểu cho:

- ChatWeb;
- Codex Desktop;
- Electron supervisor.

### API/control endpoint

Mở rộng internal `__control/orchestration` hoặc versioned endpoint mới với:

```text
clients[]
client_id/type/role/status
last_seen
cursor/current_seq/lag
contract/runtime compatibility
```

### Cursor semantics

- independent per client;
- durable nếu cần cross-process/restart continuity;
- bounded retention;
- explicit resync khi cursor quá cũ.

### Acceptance

- hai client poll khác tốc độ không consume event của nhau;
- reconnect catch up đúng delta;
- missing/old cursor có deterministic recovery.

## Phase 3 — Controller Lease

### Backend

Controller lease + fencing token theo run.

### Initial policy

```text
ChatWeb connected + healthy → controller
Desktop → worker/observer
ChatWeb absent → run tiếp tục worker-safe work
semantic/final decision → WAITING_CONTROLLER
```

Chưa auto-transfer controller cho Desktop ở phase này.

### Acceptance

- simultaneous claim → một winner;
- old token action rejected;
- expiry → waiting state, không split brain;
- handoff with ACK changes token exactly once;
- reconnect old ChatWeb không tự reclaim nếu token đã đổi.

## Phase 4 — Resume packet/context compiler

### Xây deterministic projection

Input:

- task/run/wave;
- latest accepted checkpoint;
- event delta;
- proof refs;
- changed paths;
- messages;
- capsule;
- current authority state.

Output bounded.

### Acceptance

- new chat resumes without transcript;
- packet hash/version stable;
- same state → same projection modulo allowed timestamps;
- oversized history không làm output vượt budget;
- references đủ để drill down khi cần.

## Phase 5 — Execution Control Center UI

Nâng `renderer/panel.*` thay vì xây app mới.

### UI milestone 1

- Clients;
- Controller;
- Current execution;
- Proof;
- Write authority;
- Continuity verdict.

### UI milestone 2

- worker/routing economics;
- cursor lag;
- handoff visual state;
- context-pressure state;
- alert/reason codes.

### Acceptance

Operator không cần đọc ledger/CLI để xác định:

- owner;
- phase;
- client health;
- proof;
- safe-to-rotate.

## Phase 6 — Controlled handoff ChatWeb ⇄ Desktop

Ban đầu **manual explicit handoff**.

Flow theo ACK/fencing ở §9.3.

Không auto-trigger theo context pressure ngay.

### Acceptance

- no state loss;
- no duplicate work;
- old controller rejected;
- target receives correct delta;
- rollback/abort handoff leaves known owner.

## Phase 7 — Long-running/background reconciliation

Phân loại operations:

```text
read-only resumable
idempotent replay-safe
indeterminate side effect
non-resumable process-local
```

Không blind retry.

### Acceptance

- runtime restart không giả vờ background op còn chạy;
- replay-safe op dedups;
- unknown side effect yêu cầu reconciliation;
- orphan process không tồn tại sau cancel/restart policy.

## Phase 8 — Fault injection / E2E two-client suite

Các scenario bắt buộc:

1. đóng ChatWeb giữa worker run;
2. ChatWeb reconnect fresh chat;
3. Desktop disconnect/reconnect;
4. Runtime restart giữa event stream;
5. duplicate command delivery;
6. stale controller token;
7. stale writer token;
8. handoff ACK lost;
9. target client dies after ACK before action;
10. tunnel drops response;
11. command result larger than chat budget;
12. capsule stale vs repository drift;
13. provider thread unavailable/capacity cooldown;
14. two simultaneous client control requests;
15. final acceptance after long absence.

### Reliability requirement

Không chỉ pass một lần. Chạy repeated trials theo tinh thần pass^k, tối thiểu đủ để phát hiện flakiness của reconnect/handoff paths.

## Phase 9 — Evidence-driven automation

Chỉ sau E2E và real-task data:

- cân nhắc auto-handoff;
- cân nhắc controller auto-transfer;
- cân nhắc routing threshold update.

Không gộp ba quyết định này thành một flag.

---

# 12. Acceptance matrix cuối

Một release được gọi là **Multi-Client Hub READY** khi có proof cho toàn bộ:

| Gate | Tiêu chí |
|---|---|
| Single runtime | ChatWeb và Desktop report cùng runtime authority |
| Client identity | client online/offline/last-seen chính xác |
| Event continuity | mỗi client catch up bằng cursor độc lập |
| Controller singularity | không có hai controller valid cùng run |
| Writer singularity | stale/second writer bị fencing |
| Browser loss | đóng ChatWeb không mất execution |
| Fresh chat | new ChatWeb session resume cùng run không copy transcript |
| Desktop loss | worker/client disconnect không corrupt run |
| Restart | runtime restart reconcile state đúng |
| Idempotency | duplicate delivery không duplicate side effect |
| Handoff | controller chuyển đúng một lần, ACK + token proof |
| Proof authority | worker “done” không bypass PROVING/ACCEPTING |
| Permission | unsupported elicitation vẫn fail closed |
| Context bounded | resume packet/capsule nằm trong budget |
| UI truthfulness | Hub không hiển thị Desktop attached nếu chỉ có sidecar |
| Cost telemetry | credits/TTA/cache có source và không overclaim |
| Safety to rotate | verdict có reason code và test cases |
| Cancellation | không orphan process/job trong supported scope |
| Secret hygiene | không secret/raw transcript trong ledger/capsule/client registry |

---

# 13. Metrics cần đưa lên Hub

## 13.1 Reliability

- active runs;
- blocked/waiting-controller runs;
- stale/orphan counts;
- handoff success rate;
- reconnect success rate;
- duplicate suppression count;
- stale-token rejection count;
- proof failure/repair rate.

## 13.2 Performance

- TTA p50/p90;
- local execution time;
- provider wait proxy;
- queue/wait time;
- event cursor lag.

## 13.3 Economics

- credits today;
- credits / accepted task;
- credits by route;
- cache ratio;
- proof cache saved time;
- wasted candidate/repair credits;
- model switches per accepted run.

## 13.4 Continuity

- capsule age/hash/currentness;
- last checkpoint age;
- current controller;
- controller TTL;
- pending message count;
- client cursor lag;
- context pressure;
- `SAFE TO ROTATE CHATWEB`.

---

# 14. Những việc không nên làm

1. Không xây second orchestration framework cạnh EOCL.
2. Không tạo thêm một “memory AI” trước khi tận dụng ledger/source/proof.
3. Không sync full ChatWeb transcript sang Desktop.
4. Không coi Codex Desktop thread là project database.
5. Không dùng SQLite lock làm semantic ownership.
6. Không thêm hàng chục public MCP tools cho dashboard.
7. Không auto-handoff chỉ vì context estimate cao.
8. Không mass-parallelize workers cho workflow tuần tự.
9. Không tune routing từ synthetic task hoặc blocked call.
10. Không để MCP tự `taskkill` chính nó; Electron tiếp tục giữ restart authority.
11. Không claim arbitrary live Desktop attachment nếu API không chứng minh.
12. Không mass-clean historical ledger rows chỉ để dashboard đẹp.

---

# 15. Rủi ro và biện pháp giảm thiểu

## R1 — Desktop adapter trở thành second authority trá hình

**Mitigation:** adapter stateless/thin, không có ledger, không có router, không có direct workspace mutation.

## R2 — Controller lease gây complexity quá mức

**Mitigation:** scope chỉ theo `run_id`, một owner, TTL, fencing token, explicit handoff. Không xây distributed consensus tổng quát.

## R3 — Cursor persistence phình ledger

**Mitigation:** lưu projection nhỏ per client/run, bounded retention; event journal vẫn authority.

## R4 — Hub UI trở thành source of truth

**Mitigation:** UI chỉ render runtime projection. Refresh/restart UI không thay business state.

## R5 — Context pressure không đo được chính xác

**Mitigation:** hiển thị estimate/unknown; continuity verdict dựa chủ yếu vào durable state/capsule/ownership, không phụ thuộc một token counter duy nhất.

## R6 — Auto-handoff tạo duplicate work

**Mitigation:** manual handoff trước; token fencing + ACK; auto chỉ sau real A/B evidence.

## R7 — Routing tiết kiệm worker nhưng tăng controller overhead

**Mitigation:** đo total credits/accepted task và TTA, không chỉ candidate price.

## R8 — Host limitations ChatGPT/Codex thay đổi

**Mitigation:** capability negotiation + contract fingerprint + truthful unsupported states; core runtime không phụ thuộc UI-specific feature.

---

# 16. Thứ tự ưu tiên đề xuất

## P0 — Kiến trúc và connectivity

1. Duyệt single-runtime topology.
2. Audit/sửa Codex Desktop stale config.
3. Prototype Desktop stdio proxy → same Runtime.

## P1 — Multi-client correctness

4. Client registry.
5. Per-client cursor.
6. Controller lease/fencing.
7. Internal orchestration snapshot v2.

## P1.5 — Operator UX

8. Upgrade Control Panel → Execution Control Center.
9. Continuity verdict + reason codes.
10. Manual controlled handoff UI.

## P2 — Resilience proof

11. Resume packet compiler.
12. Two-client fault suite.
13. Restart/reconnect/idempotency/handoff repeated canaries.

## P3 — Economics/automation

14. Real accepted Mini/Luna/Sol cohorts.
15. Routing calibration.
16. Real handoff A/B.
17. Chỉ khi đủ evidence mới cân nhắc auto-handoff/controller automation.

---

# 17. Dự kiến ảnh hưởng hiệu năng

Nếu triển khai đúng control-plane boundary, normal tool hot path không nên chịu chi phí đáng kể.

### Chỉ chạy khi control/observation

- client heartbeat/last seen;
- cursor bookkeeping;
- controller lease renew;
- Hub snapshot;
- context/handoff status.

### Không nên chèn vào mọi tool call

- full client registry scan;
- full event replay;
- contract recomputation;
- UI aggregation nặng;
- model call để “summarize status”.

Tối ưu:

- contract hash tính startup;
- snapshot projection bounded;
- cursor indexed by run/client;
- heartbeat không gọi LLM;
- telemetry aggregation async/bounded;
- UI poll 2s hoặc event stream về sau.

---

# 18. Định hướng sản phẩm

Không định vị Tools-Codex-web là một ChatGPT wrapper hoặc một IDE cạnh tranh Codex Desktop.

Định vị đề xuất:

> **Tools-Codex-web = Local AI Execution Control Plane / Execution Hub cho nhiều AI coding frontends.**

Electron là **Control Center**, không phải nơi model phải chat.

ChatWeb và Codex Desktop là hai UX chuyên biệt:

```text
ChatWeb
  semantic/research/user-facing

Codex Desktop
  deep coding/inspection/worker-facing

Execution Hub
  durable truth/authority/proof/routing
```

Điểm khác biệt của sản phẩm không phải “có thêm nhiều model”, mà là:

- execution continuity;
- adaptive compute;
- strong proof;
- singular ownership;
- cross-client handoff;
- transparent operator control.

---

# 19. Quyết định cần duyệt trước khi triển khai

Đề nghị người duyệt chốt từng dòng:

- [ ] Đồng ý **single-runtime authority** là topology production.
- [ ] Đồng ý Codex Desktop dùng **thin stdio proxy/adapter**, không full Runtime thứ hai.
- [ ] Đồng ý ChatWeb tiếp tục là **default semantic controller/final acceptor** ở rollout đầu.
- [ ] Đồng ý xây **controller lease** riêng, không tái sử dụng write lease một cách nhập nhằng.
- [ ] Đồng ý nâng panel hiện tại thành **Execution Control Center** thay vì tạo app UI mới.
- [ ] Đồng ý **không sync transcript**, chỉ dùng bounded resume packet/capsule/references.
- [ ] Đồng ý manual handoff trước, auto-handoff sau evidence.
- [ ] Đồng ý routing threshold không đổi cho đến khi có accepted cohorts đại diện.
- [ ] Đồng ý `SAFE TO ROTATE CHATWEB` phải là derived verdict có reason codes.
- [ ] Đồng ý fault-injection E2E là release gate bắt buộc.

Nếu các quyết định trên được duyệt, implementation có thể chia thành các work package nhỏ, mỗi package có EOCL run/wave, focused proof và acceptance riêng; không cần một refactor khổng lồ.

---

# 20. Nguồn tham khảo

## 20.1 Nguồn nội bộ — authoritative cho trạng thái dự án

1. `docs/research/2026-08-14_CODEX_DESKTOP_CHATWEB_INTEGRATION_PLAN.md`
2. `docs/research/260813_CODEX_WEB_BIDIRECTIONAL_RESILIENT_ORCHESTRATION.md`
3. `docs/research/260813_CODEX_WEB_ORCHESTRATION_BLUEPRINT.md`
4. `docs/research/2026-08-14_POST_P1_FOLLOWUP_TRACKER.md`
5. `docs/research/2026-08-14_REAL_CODEX_BENCHMARK_AND_TOKEN_USAGE.md`
6. `docs/research/2026-08-14_SYSTEM_CAPABILITY_DEEP_TEST_SUITE.md`
7. `README.md`
8. `renderer/panel.html`
9. `resources/coding-tools-mcp/coding_tools_mcp/orchestration_ledger.py`

## 20.2 Nghiên cứu/primary source bên ngoài

### [R1] OpenAI — Unlocking the Codex harness: how we built the App Server, 2026

https://openai.com/index/unlocking-the-codex-harness/

Bài học sử dụng: App Server là long-lived process; thread history persisted; web UI ephemeral; server-side state cho phép reconnect/catch-up; protocol bidirectional phục vụ rich clients.

### [R2] Liu et al. — Lost in the Middle: How Language Models Use Long Contexts, 2023

https://arxiv.org/abs/2307.03172

Bài học sử dụng: long context capacity không đồng nghĩa robust retrieval/use ở mọi vị trí; cần bounded working set/retrieval thay vì nhồi toàn history.

### [R3] Kim et al./Google Research — Towards a science of scaling agent systems, 2026

https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/

Bài học sử dụng: multi-agent có lợi khi parallelizable; sequential workflows chịu coordination penalty; centralized orchestrator kiểm soát error amplification tốt hơn independent agents.

### [R4] Zhang et al. — MTRouter: Cost-Aware Multi-Turn LLM Routing with History–Model Joint Embeddings, ACL 2026

https://aclanthology.org/2026.acl-long.2045/

DOI: `10.18653/v1/2026.acl-long.2045`

Bài học sử dụng: cost-aware routing trên long-horizon multi-turn; tránh model đắt cho mọi lượt và tránh model switching/cascade không cần thiết.

### [R5] Uddin & Bauer — Conformal LLM Routing with Distribution-Free Safety Guarantees, ACL 2026

https://aclanthology.org/2026.acl-srw.70/

DOI: `10.18653/v1/2026.acl-srw.70`

Bài học sử dụng: cheap-model routing cần calibration/safety bound; không promote từ sample nhỏ.

### [R6] ToolScope — Enhancing LLM Agent Tool Use through Tool Merging and Context-Aware Filtering, ACL 2026

https://aclanthology.org/2026.acl-long.1573/

DOI: `10.18653/v1/2026.acl-long.1573`

Bài học sử dụng: giảm redundancy/tool ambiguity và context tax; củng cố hướng giữ public tool surface nhỏ.

### [R7] SQLite — Write-Ahead Logging

https://sqlite.org/wal.html

Bài học sử dụng: WAL tăng reader/writer concurrency nhưng WAL chuẩn vẫn chỉ một writer tại một thời điểm; DB concurrency không thay thế semantic ownership/fencing.

### [R8] Burrows — The Chubby lock service for loosely-coupled distributed systems, OSDI 2006

https://research.google/pubs/the-chubby-lock-service-for-loosely-coupled-distributed-systems/

Bài học sử dụng: distributed ownership/lease là khái niệm riêng; shared storage không đủ để biểu diễn authority.

### [R9] Yao et al. — τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains, 2024

https://arxiv.org/abs/2406.12045

Bài học sử dụng: reliability cần đo nhiều trial (`pass^k`), không chỉ một lần success.

### [R10] Jimenez et al. — SWE-bench: Can Language Models Resolve Real-World GitHub Issues?, ICLR 2024

https://arxiv.org/abs/2310.06770

Bài học sử dụng: đánh giá coding agent bằng real software tasks + independent oracle/tests.

---

# 21. Kết luận cuối

Mục tiêu “ChatWeb + Codex Desktop thông nhau, không mất task khi ChatWeb hết context hoặc biến mất, route model tiết kiệm hơn, có một giao diện trung tâm để kiểm soát toàn bộ” **có khả năng đạt được với codebase hiện tại**.

Điểm then chốt là không cố kéo dài lifetime/context của ChatWeb, mà chuyển execution truth ra Hub:

```text
conversation is replaceable
execution is durable
frontend is replaceable
worker/model is replaceable
proof is authoritative
controller is singular
writer is singular
```

Dự án hiện đã có phần lớn primitives khó: ledger, EOCL, proof, idempotency, handoff, lanes, write-fence, restart supervisor và orchestration panel. Vì vậy bước tiếp theo không phải xây một hệ mới mà là **hợp nhất chúng thành một single-runtime multi-client control plane có ownership/cursor rõ ràng và nâng Control Panel thành Execution Control Center**.

Nếu tài liệu này được duyệt, nên triển khai theo Phase 0→8 với focused proof từng package. P2 routing và auto-handoff chỉ được tự động hóa sau khi có real accepted evidence; đó là evidence gate có chủ đích, không phải blocker của Hub architecture.
