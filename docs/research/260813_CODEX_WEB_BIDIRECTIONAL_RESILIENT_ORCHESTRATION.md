# 260813 — Codex Web Bidirectional Resilient Orchestration

## Trạng thái tài liệu

Tài liệu này được **khôi phục ngày 2026-08-13** vì file nguồn được nhắc tới trước đó không còn hiện diện trong workspace. Nội dung được tái dựng từ trạng thái code hiện tại, các test đang có, `docs/research/260813_CODEX_WEB_ORCHESTRATION_BLUEPRINT.md` và báo cáo tổng hợp của phiên làm việc trước. Đây là bản nguồn có thể dùng tiếp cho triển khai, nhưng không được coi là bản sao bit-for-bit của file đã mất.

**Ràng buộc của lượt khôi phục:** không commit, không push, không tag, không release, không deploy.

---

## 1. Kết luận kiến trúc

Không để ChatWeb hoặc Codex Desktop trở thành nơi duy nhất giữ trạng thái công việc. Hệ thống cần tách ba lớp phiên:

1. **Chat session** — vòng đời của hội thoại ChatWeb; có thể đóng, reload, hết context hoặc chuyển chat.
2. **Execution session** — phiên điều phối bền vững của Tools-Codex-web; đây mới là nguồn sự thật về task, wave, proof, checkpoint và trạng thái điều phối.
3. **Codex provider session** — thread/session của Codex App Server/CLI/provider; có thể tạo mới, fork, resume hoặc thay thế mà không làm mất identity của execution session.

Mô hình mục tiêu:

```text
ChatWeb
  ├─ submit intent / answer / cancel / reprioritize
  └─ receive progress / checkpoint / needs-input / result
                 │
                 ▼
Tools-Codex-web durable control plane
  ├─ task state projection
  ├─ append-only event/proof ledger
  ├─ coordination inbox/outbox
  ├─ durable agent-lane registry
  ├─ handoff capsules
  ├─ write authority / lease
  ├─ supervisor / restart reconciliation
  ├─ proof cache and acceptance gate
  └─ cost / deadline / capacity controls
                 │
                 ▼
Codex provider adapter
  ├─ bridge-owned persistent App Server thread
  ├─ ephemeral read-only review/fork
  └─ explicit unsupported state for live Desktop attachment
```

MCP là tool/capability boundary. MCP transport session không được dùng thay cho durable workflow state.

---

## 2. Những phần đã hiện diện trong code

### 2.1 Durable orchestration ledger — IMPLEMENTED

Nguồn chính:

```text
resources/coding-tools-mcp/coding_tools_mcp/orchestration_ledger.py
```

`OrchestrationLedger` dùng SQLite, cố gắng bật WAL và lưu các bảng:

- `runs`
- `waves`
- `delegations`
- `events`
- `proofs`
- `checkpoints`
- `agent_lanes`
- `coordination_messages`
- `handoff_capsules`
- `background_operations`

Event được append-only theo từng run và hash-chain qua `prev_hash` / `event_hash`. Payload nhạy cảm được sanitize; prompt, patch, stdout/stderr và content lớn không được lưu thô mà thay bằng hash/kích thước.

Ý nghĩa: trạng thái điều phối không phụ thuộc transcript ChatWeb và có thể tái dựng sau process restart.

### 2.2 Task state projection — IMPLEMENTED

Nguồn:

```text
resources/coding-tools-mcp/coding_tools_mcp/task_state.py
```

`TaskStateStore` lưu projection gọn tại `.coding-tools/task-state.json`, có archive/history và atomic replace. Projection chứa:

- task id/objective;
- orchestration projection;
- steps/current step;
- command/test/build result;
- modified files;
- failure/next step;
- event history gọn.

SQLite ledger là history authority; JSON task-state là projection phục vụ client/operator.

### 2.3 Orchestration state machine và write authority — IMPLEMENTED, fencing còn PARTIAL

Nguồn:

```text
resources/coding-tools-mcp/coding_tools_mcp/orchestration_control.py
```

State machine hiện tại:

```text
PREFLIGHT
  -> READY
  -> ROUTED
  -> EXECUTING
  -> PROVING
  -> ACCEPTING
  -> CHECKPOINTED

failure path:
  -> REPLAN / BLOCKED / ABORTED
```

`OrchestrationControl` có:

- route selection;
- delegation identity;
- write lease;
- owner check;
- allowed-path scope;
- base HEAD/worktree fingerprint check;
- revoke lease trước proof/replan;
- recover state và active lease từ ledger.

Điểm chưa hoàn tất so với kiến trúc mục tiêu: write lease hiện **chưa có fencing token tăng đơn điệu và lease expiry/heartbeat**. Vì vậy single-writer trong một control flow đã có, nhưng stale-writer fencing sau phân phối/restart chưa đạt thiết kế cuối.

### 2.4 Durable Codex agent lane registry — IMPLEMENTED

`agent_lanes` lưu:

- `lane_id`;
- `semantic_key`;
- role/provider;
- thread/session id;
- lifecycle;
- profile/model/effort;
- base HEAD/worktree/contract fingerprint;
- last turn id;
- metadata.

Unique partial index ngăn hai live lane cùng chiếm một semantic workstream trong cùng run.

Khi runtime khởi động lại, lane thuộc process cũ đang `active` được chuyển về `waiting` với recovery reason thay vì bị coi là đã mất.

### 2.5 Bidirectional coordination storage — IMPLEMENTED ở durable-message layer

`coordination_messages` hỗ trợ:

```text
direction
kind
status
run_id / wave_id / lane_id
base_head / worktree_fp
payload
acknowledged_at
```

`append_coordination_message()` dùng `INSERT OR IGNORE`, message có thể persist qua store recreation và có explicit acknowledge.

Các direction dự kiến:

```text
chatweb_to_codex
codex_to_chatweb
```

Đây là nền tảng inbox/outbox hai chiều. Tuy nhiên envelope hoàn chỉnh với `correlationId`, `causationId`, `idempotencyKey`, protocol-level sequence và public reconnect API vẫn chưa được đóng gói thành một giao thức client-facing duy nhất.

### 2.6 Handoff capsule — IMPLEMENTED

Capsule được lưu durable, có:

- `conversation_epoch`;
- `version`;
- bounded payload;
- SHA-256;
- latest-capsule lookup.

Giới hạn hiện tại:

```text
HANDOFF_CAPSULE_MAX_BYTES = 8192
```

Raw transcript, source content, patch và stdout/stderr không được nhồi vào capsule. Đây là nền móng để chat mới bind lại execution session mà không phải copy toàn transcript.

### 2.7 Background operations — IMPLEMENTED, restart resume còn PARTIAL

Long `agent_workflow` có process-scoped background operation và durable record trong ledger.

Record lưu:

```text
operation_id
server_instance_id
tool
task_id
run_id
wave_id
status
timestamps
summary
```

Khi runtime mới thấy operation `running` của server instance cũ, nó đánh dấu `orphaned` với `mcp_runtime_restarted` thay vì giả vờ vẫn chạy.

Đây là semantics trung thực. Bước tiếp theo của kiến trúc cuối là reconcile/resume có policy cho từng loại side effect, không blind-retry.

---

## 3. Codex App Server bridge

Nguồn:

```text
resources/coding-tools-mcp/coding_tools_mcp/codex_bridge.py
```

Bridge hiện là **independent App Server sidecar**, không điều khiển live Desktop turn.

Các nguyên tắc đã được code hóa:

- chia sẻ Codex home/auth/history;
- workspace-scoped;
- `approvalPolicy=never`;
- read-only sandbox;
- network disabled;
- persisted Desktop threads chỉ để inspect/fork;
- arbitrary Desktop thread không được bridge chiếm quyền;
- persistent bridge-owned thread có thể resume ở bridge instance mới khi registry cung cấp thread/session identity hợp lệ.

Các action hỗ trợ:

```text
status
models
threads
run
continue
observe
interrupt
close
```

Provider lane có thể `ephemeral` hoặc `persistent`.

### Provider truthfulness

Bridge status nói rõ:

```text
bridge_mode = independent_app_server_sidecar
live_desktop_turn_attached = false
```

Vì vậy UI/control plane không được hiển thị “Desktop attached” khi thực tế chỉ là sidecar/headless persistent thread.

### Capacity/cost controls đã có

Bridge có:

- model/effort profile routing;
- max prompt 20,000 chars;
- bounded output schema;
- deadline tối đa 30s cho turn được chờ inline;
- interrupt khi deadline hit;
- per-model capacity cooldown;
- token usage và estimated credit accounting;
- bounded recent-run telemetry.

Đây là backpressure/cost foundation; chưa phải admission controller đầy đủ theo `max_tokens`, `max_cost`, `max_attempts`, `max_auto_steps`.

---

## 4. Proof, checkpoint và final authority

Nguồn:

```text
resources/coding-tools-mcp/coding_tools_mcp/proof_ledger.py
resources/coding-tools-mcp/coding_tools_mcp/orchestration_report.py
```

`ProofLedger` tạo content-addressed fingerprint từ:

- stage id/version;
- base HEAD;
- worktree fingerprint;
- contract fingerprint;
- selected input paths;
- config;
- upstream proof ids.

Một proof pass có thể được cache/reuse nếu fingerprint không đổi. Proof record lưu command hash, duration, exit code, cache state và metadata result.

Acceptance flow buộc đi qua:

```text
EXECUTING -> PROVING -> ACCEPTING -> CHECKPOINTED
```

Control plane không nên tuyên bố hoàn tất chỉ vì worker/model nói “done”.

---

## 5. Context rotation và giới hạn ChatWeb

Operational baseline giữ từ blueprint:

| Mức context ước tính | Hành động |
|---|---|
| 60–65% | Delta-only; không đưa lại file/log đã biết |
| 75% | Tạo checkpoint + handoff capsule |
| 85% | Không nhận thêm task dài; chuẩn bị chat mới |
| 90%+ | Chỉ checkpoint/critical action |

Luôn giữ headroom 15–20% cho tool output/metadata.

Nguồn sự thật phải ở ngoài transcript:

```text
.coding-tools/
  task-state.json
  task-history.json
  orchestration/ledger.sqlite3
  orchestration/reports/
```

Không làm “summary of summary” vô hạn. Capsule phải có thể rebuild từ ledger + source + diff + proof.

---

## 6. Retry, recovery, supervisor

### Đã có

- failure classification;
- REPLAN wave thay vì tiếp tục mù;
- capacity cooldown;
- bounded deadline;
- background operation persistence;
- orphan detection sau runtime restart;
- agent-lane recovery về `waiting`;
- Windows Codex sidecar process-tree termination bằng `taskkill /T /F` fallback;
- proof cache;
- explicit final acceptance.

### Còn thiếu hoặc partial

- monotonic fencing token;
- lease expiry + heartbeat;
- automatic startup reconciliation theo side-effect class;
- exponential backoff + full jitter cho retry policy tổng quát;
- DLQ/replay policy hoàn chỉnh;
- `max_auto_steps` / `max_tool_hops` / `max_attempts` / `max_cost` admission gate thống nhất;
- client-facing `last_event_id`/sequence reconnect stream hoàn chỉnh;
- WebSocket/SSE event replay contract;
- per-consumer cursor cho multi-client observation;
- Windows Job Object cho mọi subprocess, không chỉ Codex sidecar kill-tree fallback.

---

## 7. Phân vai model để giảm token

### SOL/controller

Nên giữ cho:

- DAG/dependency;
- kiến trúc;
- conflict;
- consequential review;
- final acceptance/recovery decision.

Không dùng SOL cho:

- heartbeat;
- polling;
- log tail;
- git status;
- retry scheduler;
- process/port detection;
- hash/proof indexing;
- state projection.

### Worker lanes

Mỗi lane nhận bounded packet:

```text
scope
allowed_paths
acceptance_criteria
dependencies
budget
required_tests
output_contract
```

Output nên chuẩn hóa:

```text
status
summary
changed_files/tests hoặc findings
missing_proof
blocker/question
next_action
confidence
```

---

## 8. Concurrency baseline

Khuyến nghị tiếp tục giữ:

```text
SOL/controller concurrent:         1
Writer / workspace:                1
Read-only analyzer / workspace:    2
Independent reviewer:              1 khi có giá trị
```

Code write song song chỉ khi có isolated worktree/branch và ownership rõ. Không cho nhiều writer trực tiếp lên một working tree.

---

## 9. Acceptance gates của kiến trúc cuối

Một bản rollout chỉ được coi là hoàn tất khi có evidence cho toàn bộ:

1. Browser đóng/mở lại không mất task.
2. Runtime restart không mất journal/command identity.
3. Codex provider restart có thể reconcile/resume đúng lane.
4. Duplicate delivery không tạo duplicate side effect.
5. Stale attempt bị fencing từ chối.
6. Hai writer không thể sửa cùng workspace.
7. Chat mới bind từ checkpoint/capsule, không copy transcript cũ.
8. Desktop attachment unsupported được hiển thị trung thực.
9. Cancel không để orphan process.
10. Retry không vô hạn.
11. Status/heartbeat không gọi LLM.
12. Secret không xuất hiện trong ledger/handoff.
13. Mỗi `VERIFIED` có source/test/command/exit code.

---

## 10. Source map hiện tại

```text
Architecture/control:
  resources/coding-tools-mcp/coding_tools_mcp/orchestration_control.py

Durable ledger/session/coordination/handoff:
  resources/coding-tools-mcp/coding_tools_mcp/orchestration_ledger.py

Task projection:
  resources/coding-tools-mcp/coding_tools_mcp/task_state.py

Proof cache/evidence:
  resources/coding-tools-mcp/coding_tools_mcp/proof_ledger.py

Codex provider adapter:
  resources/coding-tools-mcp/coding_tools_mcp/codex_bridge.py

High-level MCP workflow:
  resources/coding-tools-mcp/coding_tools_mcp/server.py

Focused tests:
  resources/coding-tools-mcp/tests/test_coordination_state.py
  resources/coding-tools-mcp/tests/test_orchestration_control.py
  resources/coding-tools-mcp/tests/test_codex_bridge.py
  resources/coding-tools-mcp/tests/test_durable_coordination_runtime.py
  resources/coding-tools-mcp/tests/test_orchestration_workflow.py
  resources/coding-tools-mcp/tests/test_orchestration_ledger.py
  resources/coding-tools-mcp/tests/test_proof_ledger.py
  resources/coding-tools-mcp/tests/test_orchestration_report.py
```

---

## 11. Kết luận

Kiến trúc hiện tại đã đi xa hơn một prompt-based orchestrator: đã có durable ledger, task projection, state authority, proof ledger, lane registry, handoff capsule, coordination messages, background-operation record và persistent Codex App Server lane.

Tuy nhiên hệ thống **chưa đạt toàn bộ “resilient bidirectional control plane” mục tiêu** vì fencing/lease expiry, full reconnect stream, generalized retry/admission control và full fault-injection E2E còn thiếu. Các phần đó phải được giữ là `PARTIAL/NOT_IMPLEMENTED`, không nâng thành `VERIFIED` chỉ dựa trên thiết kế.

Tài liệu verification đi kèm:

```text
docs/research/260813_CODEX_WEB_FINAL_VERIFICATION.md
```
