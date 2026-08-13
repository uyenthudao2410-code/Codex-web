# 260813 — Kiến trúc phối hợp Chatweb ↔ Codex bền vững, đa chiều và tiết kiệm

## 1. Quyết định kiến trúc

Không để Chatweb hoặc Codex Desktop trở thành nơi lưu trạng thái công việc duy nhất. Hai phía chỉ là **client/worker** của một lớp điều phối bền vững trong Tools-Codex-web.

Tách ba loại phiên:

1. **Chat session**: hội thoại Chatweb, có thể hết ngữ cảnh hoặc bị đóng.
2. **Execution session**: phiên điều phối chuẩn của Tools-Codex-web, bền vững và là nguồn sự thật.
3. **Provider session**: thread/session cụ thể của Codex Desktop, Codex CLI hoặc provider khác; có thể tạo mới, nối lại hoặc thay thế.

Một job vẫn tiếp tục khi chat bị đóng và vẫn giữ nguyên danh tính khi Codex provider phải đổi session.

## 2. Kiến trúc mục tiêu

```text
Chatweb client
  ├─ submit / cancel / reprioritize / answer
  └─ ack / progress / checkpoint / needs-input / result
                 │
                 ▼
Tools-Codex-web durable control plane
  ├─ API + WebSocket/SSE
  ├─ task state machine
  ├─ session registry
  ├─ inbox/outbox + event journal
  ├─ lease + fencing
  ├─ supervisor + recovery
  ├─ context compiler + handoff store
  ├─ budgets + admission control
  └─ observability + doctor
                 │
                 ▼
Codex provider adapters
  ├─ supported Desktop attachment, khi capability có thật
  ├─ Codex CLI/headless resumable session
  └─ one-shot stateless mode cho tác vụ nhỏ
```

MCP là ranh giới gọi công cụ/capability. MCP không thay thế durable workflow, idempotency, retry, session registry hoặc recovery.

## 3. Giao thức hai chiều

Mọi message dùng envelope có version:

```json
{
  "protocolVersion": 1,
  "eventId": "evt_...",
  "eventType": "task.progress",
  "jobId": "job_...",
  "taskId": "task_...",
  "attemptId": "attempt_...",
  "sessionId": "exec_...",
  "correlationId": "corr_...",
  "causationId": "evt_parent",
  "idempotencyKey": "stable-operation-key",
  "sequence": 42,
  "occurredAt": "ISO-8601",
  "payload": {}
}
```

Nhóm event tối thiểu:

- `hello`, `capabilities`, `heartbeat`, `state.sync`
- `task.offer`, `task.ack`, `task.started`, `task.progress`
- `task.checkpoint`, `task.needs_input`, `task.result`, `task.failed`
- `task.cancel`, `task.cancelled`
- `artifact.published`, `cost.warning`, `conflict.detected`

ACK chỉ được phát sau khi event/command đã được ghi bền vững. Delivery có thể lặp; consumer bắt buộc idempotent.

## 4. State machine

```text
QUEUED
  -> LEASED
  -> DISPATCHED
  -> ACKED
  -> RUNNING
       -> WAITING_INPUT
       -> CHECKPOINTED
       -> SUCCEEDED
       -> FAILED_RETRYABLE
       -> FAILED_TERMINAL
       -> CANCELLED
       -> DEAD_LETTER
```

Mỗi task chỉ có một writer hợp lệ. Lease có thời hạn và **fencing token tăng đơn điệu**; attempt cũ không được ghi kết quả sau khi lease đã được cấp lại.

## 5. Chính sách session Codex

### Khi sessionless được chấp nhận

Chỉ dùng cho tác vụ:

- đọc hoặc kiểm tra đơn giản;
- không sửa code;
- không cần trao đổi lại;
- chạy ngắn và có kết quả quyết định;
- retry không gây side effect.

### Khi bắt buộc create-or-resume session

- sửa code hoặc nhiều bước;
- cần hỏi đáp/ra quyết định;
- cần checkpoint/resume;
- chạy lâu;
- có nhiều worker/reviewer;
- cần Desktop tiếp tục đúng ngữ cảnh.

Không chạm private database hoặc file nội bộ không được hỗ trợ của Codex Desktop. Adapter phải kiểm tra capability:

- `desktop_attachment=true`: có thể bind session chính thức;
- `headless_resumable=true`: chạy bằng CLI/headless và lưu provider thread ID;
- không có hai capability trên: chỉ one-shot, UI phải hiển thị rõ `stateless`.

Session registry tối thiểu lưu provider, workspace identity, worktree, external thread/session ID, execution mode, model/role, capabilities, status, timestamps, context estimate, parent session và checkpoint hash.

## 6. Vượt giới hạn ngữ cảnh Chatweb

Không đợi gần 1 triệu token. Áp dụng ngưỡng:

- **60–65%**: chỉ gửi delta, giảm log và kết quả lặp.
- **75%**: tạo checkpoint/handoff capsule.
- **85%**: không nhận thêm task dài; bind chat mới vào execution session hiện hữu.
- Luôn dành 15–20% headroom cho tool output và sự sai lệch tokenizer.

Nguồn sự thật nằm ngoài transcript:

```text
state/
  project-state.json
  active-tasks.json
  session-registry.json hoặc DB
  event-journal
  decisions.md
  artifact-index.json
  evidence.ndjson
  checkpoints/
```

Handoff capsule phải deterministic, có version/hash và chứa:

- mục tiêu, acceptance criteria, constraints;
- trạng thái task và owner/lease;
- quyết định, giả định và vấn đề chưa giải quyết;
- file đã đổi, diff/artifact references;
- lệnh/test và exit code;
- budget đã dùng/còn lại;
- next actions;
- evidence pointers.

Không liên tục tóm tắt bản tóm tắt. Định kỳ rebuild capsule từ event journal, source files và test evidence.

## 7. Loại bỏ nguyên nhân Chatweb tự chạy hay fail

| Hiện tượng | Nguyên nhân kiến trúc | Xử lý |
|---|---|---|
| Đóng/reload tab làm mất run | UI sở hữu vòng đời process | Supervisor chạy ngoài UI, UI reconnect bằng `last_event_id` |
| Retry tạo run trùng | Không có idempotency/inbox | Idempotency key + durable inbox/outbox |
| Hai agent sửa cùng workspace | Không có lease/fencing | Một writer/workspace, worktree độc lập, fencing token |
| Run treo nhưng vẫn auto-poll | Không có heartbeat/inactivity timeout | Heartbeat, watchdog, circuit breaker |
| Token tăng mạnh | Đưa toàn log/file vào chat | Spool log ra file; chỉ gửi tail, diff và artifact refs |
| Retry làm tăng chi phí | Retry mọi lỗi | Phân loại transient/terminal, backoff + jitter, max attempts |
| Khởi động lại mất trạng thái | State ở memory | Event journal, snapshot, startup reconciliation |
| Không rõ Desktop có thật sự nối | Không capability negotiation | Handshake và mode badge rõ ràng |
| Tiến độ giả/khó kiểm chứng | Agent tự kể lại | Evidence bằng file, command, exit code và hash |

## 8. Supervisor và recovery

- Per-workspace writer concurrency mặc định: `1`.
- Read-only analyzers: giới hạn nhỏ, chỉ song song khi độc lập.
- Timeout tách `inactivity_timeout` và `max_runtime`.
- Retry chỉ cho lỗi transient; dùng exponential backoff + full jitter.
- Circuit breaker theo provider/workspace.
- Startup reconciliation kiểm tra expired lease, orphan process và attempt có side effect mơ hồ.
- DLQ cho task hết retry; replay phải bắt đầu từ checkpoint, không chạy mù từ đầu.
- Trên Windows phải dọn cả process tree/job object, không chỉ PID cha.
- Output được spool; status/heartbeat không gọi LLM.

## 9. Phân vai model và kiểm soát chi phí

### SOL/controller

Chỉ dùng cho:

- chia DAG và phát hiện dependency;
- quyết định kiến trúc;
- xử lý xung đột;
- phê duyệt thay đổi rủi ro cao;
- review cuối.

Không dùng SOL để polling, đọc lại repo, lặp kế hoạch hoặc tóm tắt log.

### Worker

Mỗi task có phạm vi file, acceptance criteria, budget và output contract:

```text
status
changed_files
tests_and_exit_codes
evidence
blockers_or_next_action
```

### Nguyên tắc tiết kiệm

- prompt prefix ổn định để tận dụng cache;
- gửi delta và artifact references;
- không đưa toàn bộ transcript cho worker;
- deterministic scripts xử lý git status, test discovery, log parsing;
- admission control theo token, thời gian, attempts và concurrency;
- dừng khi không có progress event thực, không tạo chuỗi “continue” vô hạn.

## 10. Mặc định vận hành đề xuất

Các giá trị sau là baseline để benchmark rồi điều chỉnh:

- writer/workspace: `1`;
- read-only workers/workspace: `2`;
- coordinator calls đồng thời: `1`;
- heartbeat: `15 s`;
- lease: `60 s`;
- inactivity timeout: `5 min`;
- retries transient: tối đa `3`;
- checkpoint: khi đổi phase, trước side effect, và theo chu kỳ;
- context capsule: mục tiêu dưới `10k–20k` token;
- raw tool output trong chat: giới hạn theo dòng/kích thước, phần còn lại lưu artifact.

## 11. Rollout

1. **Shadow mode**: ghi event và đo, chưa thay luồng cũ.
2. **Canary một workspace**: durable queue/session/recovery.
3. **Bật bidirectional mode mặc định**.
4. **Tắt legacy auto-run/polling** sau khi fault tests pass.
5. Chỉ chuyển SQLite local sang PostgreSQL khi thực sự có nhiều máy/worker phân tán.

SQLite WAL phù hợp triển khai local một máy; PostgreSQL là lựa chọn khi cần coordinator đa máy. Redis không nên là nguồn sự thật duy nhất cho workflow.

## 12. Acceptance gates

- Browser đóng/mở lại không mất task.
- Worker chết rồi restart vẫn reconcile và resume.
- Duplicate delivery không tạo duplicate side effect.
- Stale attempt bị fencing từ chối.
- New chat bind đúng execution session từ checkpoint.
- Desktop attachment không được giả lập; unsupported phải hiển thị rõ.
- Cancellation không để orphan process.
- Không có unbounded loop/concurrency.
- Không log secret hoặc prompt nguyên khối.
- Mỗi capability `VERIFIED` có source file, test, command và exit code.
- Commit/push/deploy vẫn là gate riêng, không tự động.

## 13. Báo cáo triển khai trong workspace

Source of truth sau các work package:

```text
E:\DEV\Tools-Codex-web\docs\research\260813_CODEX_WEB_BIDIRECTIONAL_RESILIENT_ORCHESTRATION.md
E:\DEV\Tools-Codex-web\docs\research\260813_CODEX_WEB_FINAL_VERIFICATION.md
```

Kiểm tra nhanh:

```powershell
Set-Location E:\DEV\Tools-Codex-web
git status --short
Select-String `
  -Path .\docs\research\260813_CODEX_WEB_FINAL_VERIFICATION.md `
  -Pattern 'RELEASE GATE|PASS|BLOCKED|VERIFIED|PARTIAL|NOT_IMPLEMENTED'
```

Không coi tài liệu là bằng chứng thay cho test; dòng `RELEASE GATE` và các command/exit code mới là điều kiện phát hành.
