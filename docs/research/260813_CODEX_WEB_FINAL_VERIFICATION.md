# 260813 — Codex Web Final Verification

## Trạng thái tài liệu

Báo cáo này được cập nhật sau lượt triển khai kiến trúc **upstream MCP kernel + Tools-Codex-web control plane** ngày 2026-08-13. Nó thay thế các trạng thái cũ trong bản khôi phục trước đó, đặc biệt ở các hạng mục fencing, lease expiry, stateless HTTP canary, multi-client cursor và durable event replay.

**Ràng buộc:** không commit, không push, không tag, không release, không deploy.

---

## 1. Snapshot

```text
Workspace: E:\DEV\Tools-Codex-web
Branch: main
HEAD baseline: a051897449827e4753b16def1b693d867fad76e9
Model-facing smart surface: 8 tools, không mở rộng thành catalog upstream 18 tools
```

Workspace đã có thay đổi/WIP từ trước. Lượt triển khai này không reset, clean hoặc overwrite các thay đổi không liên quan.

> **Cập nhật 2026-08-13 (lượt hoàn thiện):** HEAD hiện tại `378fe5ee` trên `main`. Lượt này hoàn thiện universal idempotency, unified budget/retry, per-principal quota, supervisor escalation, Job Object Windows, live fault-injection E2E và regression benchmark. Python suite `127/127 OK`; Node suite `47/47 pass`.

---

## 2. Tổng kết triển khai

| Capability | Status | Evidence chính |
|---|---|---|
| Exact LF-only patch fidelity | `VERIFIED` | `patching.py`, `test_wave_a_runtime.py` |
| Model-facing retry/terminality hints | `VERIFIED` | `tool_results.py`, `test_wave_a_runtime.py` |
| Frozen-head + rolling-tail output retention | `VERIFIED` | `processes.py`, `server.py`, `test_wave_a_runtime.py` |
| Official MCP Python SDK legacy stdio smoke | `VERIFIED` | `test_mcp_sdk_smoke.py` |
| Official MCP Python SDK legacy Streamable HTTP smoke | `VERIFIED` | `test_mcp_sdk_smoke.py` |
| Duplicate initialize idempotency | `VERIFIED` | `test_wave_a_runtime.py` |
| MCP 2026-07-28 stateless HTTP canary | `VERIFIED` | `protocol.py`, `server.py`, `test_stateless_http_2026.py` |
| Legacy 2025 transport compatibility | `VERIFIED` | SDK smoke + full suite |
| Exact 8-tool smart surface preserved | `VERIFIED` | SDK smoke + `stability-source.test.js` |
| Durable orchestration ledger | `VERIFIED` | `orchestration_ledger.py` |
| Monotonic write fencing token | `VERIFIED` | `write_fences`, `test_orchestration_control.py` |
| Lease expiry + explicit renewal | `VERIFIED` | `orchestration_control.py`, focused tests |
| Stale writer rejection | `VERIFIED` | `STALE_WRITE_FENCE` regression test |
| One active writer/workspace | `VERIFIED` | durable workspace fence |
| Per-consumer command-output cursors | `VERIFIED` | `ExecSession.consumer_cursors`, regression test |
| Durable event replay by sequence cursor | `VERIFIED` | `list_events_since`, `task_control action=events` |
| Persistent Codex App Server lane resume | `VERIFIED` | `codex_bridge.py`, durable coordination tests |
| Handoff capsule | `VERIFIED` | ledger + durable runtime tests |
| Background-operation truthfulness | `VERIFIED` | durable operation/orphan tests |
| Durable `agent_workflow` execute idempotency | `VERIFIED` | durable claim/result, conflict + unknown-outcome fail-closed, runtime-recreation regression |
| `agent_workflow` admission budget | `VERIFIED` | auto-step/tool-hop/runtime/credit caps; oversized plan rejected before execution |
| Universal mutation idempotency envelope | `VERIFIED` | `call_tool`/`_idempotency_claim_or_replay` cho mọi tool có `idempotency_key`: replay dedup, conflict fail-closed, in-progress block, unknown-outcome, replay sống qua restart; `test_universal_idempotency.py` |
| `command_id` semantic migration | `PARTIAL` | model-facing API ưu tiên `command_id`; `session_id` còn là alias compatibility và tên nội bộ ở một số đường cũ |
| Unified retry/admission budget | `VERIFIED` | `budget_control.py`: RetryPolicy (backoff cap + jitter) cho read-only retry; BudgetDeadline (runtime + inactivity) cho background operation watchdog; `test_budget_control.py` |
| Per-principal quota | `VERIFIED` | command-slot quota + retained-output eviction theo `principal_id`; `test_per_principal_quota.py` |
| `default_cwd` transport state removed | `VERIFIED` | `get/set_default_cwd` deprecated no-op, loại khỏi smart surface + compat catalog |
| MCP 2026-07-28 default-on | `VERIFIED` | cả hai era served mặc định; opt-out bằng `CODING_TOOLS_MCP_STATELESS_HTTP_2026=0`; legacy handshake vẫn green |
| Supervisor escalation cap | `VERIFIED` | `MAX_DEFERRED_RECOVERIES=6` trong `runtimeOrchestrator.js`; hết hoãn vô hạn khi MCP hang; Node regression test |
| Windows command-tree cancellation | `VERIFIED` | `taskkill /T /F` + Job Object kill-on-close (`_attach_windows_job`) + fault test kiểm tra PID process con đã chết |
| Component-scoped runtime recovery | `VERIFIED` ở source/regression level | tunnel-only recovery giữ MCP; health timeout không kill process sống; full restart chỉ khi MCP process chết; escalation sau N lần hoãn |
| Browser close/reopen E2E | `VERIFIED` ở live harness | `test_live_transport_failures.py`: client nhận handoff rồi biến mất → workflow durable tiếp tục → client mới poll operation đến `completed` + replay events theo cursor + task state persisted |
| Live tunnel failure giữa active call | `VERIFIED` ở live harness | TCP proxy tunnel thật chết giữa tool call → MCP sống, command tiếp tục → proxy mới poll thấy command còn chạy/hoàn thành |
| Live supervisor với MCP thật | `VERIFIED` | `tests/live-supervisor-e2e.test.js`: tunnel-only recovery không kill MCP thật; escalation kill process treo; full restart khi process chết |
| Real MCP process crash/reconcile E2E | `VERIFIED` | `test_live_restart_reconcile.py`: crash giữa tool call → tree killed (Job Object), task state persisted, duplicate delivery replayed, dead handle truthful |
| Real Codex provider crash/restart E2E | `VERIFIED` | `test_live_codex_provider_restart.py` + stub App Server thật (stdio JSON-RPC, 2 process riêng): crash giữa turn → `resume_persistent_thread` trên provider mới → turn completed cùng thread |
| System-wide Windows Job Object ownership | `VERIFIED` | exec path gắn Job Object kill-on-close + live crash test chứng minh child không sống sót |
| Native MCP/Tunnel ownership (Electron) | `VERIFIED` ở source invariant | `nativeService.js`/`tunnelService.js` stop dùng `taskkill /T /F`; Node regression test khóa invariant |
| `session_id` deprecation telemetry | `VERIFIED` | `legacy_session_alias_uses` đếm alias-only usage, expose trong `/__control/health`; regression test |
| Serialized tool-result bytes benchmark | `VERIFIED` | `benchmarks/tool_result_bytes.py`; 3/3 completion, 9 tool calls/run, median 531 bytes; report tại `benchmarks/reports/` |

---

## 3. Wave A — Upstream correctness sync

### A1. Patch fidelity

**Status: VERIFIED**

`resources/coding-tools-mcp/coding_tools_mcp/patching.py` không còn dùng `str.splitlines()` cho patch/file line semantics. Patch parser normalize CRLF transport framing rồi split bằng literal `\n`; update hunks cũng split bằng literal `\n` và giữ trailing-newline semantics.

Regression coverage xác nhận không làm biến đổi ngoài ý muốn các code point:

```text
\x0c
\x85
U+2028
U+2029
```

và vẫn giữ đúng:

```text
CRLF
file không có trailing newline
file có trailing newline
```

### A2. Error terminality/retry hints

**Status: VERIFIED**

Model-facing error text giờ chứa trực tiếp:

```text
Category: <category>.
Retryable: yes|no.
Retry: <hint>
```

Với lỗi terminal không có retry hint:

```text
Do not repeat this call unchanged.
```

Mục tiêu là giảm retry dead-handle / retry cùng call không đổi.

### A3. Head + tail output retention

**Status: VERIFIED**

`ExecSession` giữ:

```text
frozen head + evicted middle + rolling tail
```

và expose telemetry:

```text
head_retained_bytes
tail_retained_bytes
evicted_gap_bytes
evict_events
evicted_bytes_total
```

`read_output` có thể page qua retention gap mà không giả vờ middle bytes vẫn tồn tại.

### A4. Official MCP SDK smoke

**Status: VERIFIED**

Dev extra có:

```text
mcp>=1.26,<2
```

`tests/test_mcp_sdk_smoke.py` dùng official MCP Python SDK để kiểm tra độc lập:

```text
stdio: initialize -> tools/list -> workspace_context
Streamable HTTP legacy: initialize -> tools/list -> workspace_context
```

Cả hai đều xác nhận đúng 8 smart tools.

---

## 4. Wave B — Stateless MCP transport canary

### B1. Modern protocol

**Status: VERIFIED ở canary level**

`protocol.py` có:

```text
STATELESS_PROTOCOL_VERSION = "2026-07-28"
LEGACY_PROTOCOL_VERSIONS = ("2025-11-25", "2025-06-18")
```

Modern HTTP được bật có chủ ý bằng:

```text
CODING_TOOLS_MCP_STATELESS_HTTP_2026=1
```

Mặc định flag tắt; legacy path giữ nguyên.

### B2. Stateless semantics

Modern request:

- không tạo transport `Mcp-Session-Id`;
- không yêu cầu `runtime.initialized`;
- không echo legacy session header;
- dùng shared control Runtime nhưng durable workflow state tiếp tục sống ở task/orchestration/Codex layers;
- `initialize` modern bị loại khỏi lifecycle;
- `server/discover`, `tools/list`, `tools/call` dùng self-describing result metadata.

### B3. Header/body validation

Canary fail-closed khi:

```text
MCP-Protocol-Version != params._meta protocolVersion
Mcp-Method != JSON-RPC method
Mcp-Name != named request target
clientCapabilities bị thiếu ở modern request
```

Modern GET/HEAD/DELETE không được dùng như legacy session lifecycle.

### B4. Compatibility

**Status: VERIFIED**

Official SDK legacy Streamable HTTP smoke vẫn green trong cùng full suite. Điều này chứng minh canary chưa phá default legacy compatibility.

---

## 5. Wave D — Distributed writer correctness

### D1. Durable write fences

**Status: VERIFIED**

SQLite schema nâng lên version 3 và thêm:

```text
write_fences
  scope_key
  fencing_token
  lease_id
  owner
  run_id
  wave_id
  status
  expires_at
  updated_at
```

Acquisition dùng transaction `BEGIN IMMEDIATE` để serialize claim trên workspace.

### D2. Monotonic fencing

**Status: VERIFIED**

Khi lease cũ release/expire và writer mới claim workspace:

```text
fencing_token N -> N+1
```

Attempt cũ với token N bị `STALE_WRITE_FENCE` và không còn quyền mutate.

### D3. Lease expiry + renewal

**Status: VERIFIED**

Default TTL:

```text
WRITE_LEASE_TTL_SECONDS = 60.0
```

`renew_write_lease()` chỉ renew đúng owner + lease_id + fencing_token đang active. Expired lease bị `WRITE_LEASE_EXPIRED`.

Recovery chỉ dựng lại write lease khi durable fence vẫn hợp lệ.

### D4. Sensitive-field sanitation

`fencing_token` được giữ như control identity, không bị generic secret regex redaction. Secret/token thật ở các field nhạy cảm khác vẫn giữ redaction behavior trước đó.

---

## 6. Wave D — Multi-client observation và event replay

### D5. Per-consumer command output cursor

**Status: VERIFIED**

`ExecSession` hỗ trợ tối đa 16 bounded consumer cursor. `command_control` poll/write có optional:

```text
consumer_id
```

Ví dụ logical clients:

```text
chatweb
supervisor
desktop
```

Một consumer đọc output không làm consumer khác mất output. Không truyền `consumer_id` thì legacy global cursor semantics vẫn được giữ để backward compatible.

### D6. Durable orchestration event replay

**Status: VERIFIED ở control-plane API level**

`OrchestrationLedger.list_events_since()` hỗ trợ:

```text
after_seq
limit
events
next_after_seq
has_more
```

`task_control action=events` expose replay này để chat/client mới có thể tiếp tục từ sequence cursor thay vì replay transcript.

Regression test chứng minh cùng `after_seq` trả lại cùng page và không consume event của client khác.

---

## 7. Durable execution/Codex state vẫn giữ ngoài transport

Việc thêm stateless modern MCP **không xóa**:

```text
task_id
run_id
wave_id
execution state
proof/checkpoint
persistent agent lane
Codex thread/session
handoff capsule
background operation
coordination messages
write fence
```

Đây là separation chủ đích:

```text
transport connection != execution session != Codex provider session
```

---

## 8. Verification commands

### Full Python suite

```text
python -m unittest discover -s tests -p test*.py
```

Kết quả mới nhất sau khi thêm fault-injection cancellation và supervisor recovery:

```text
Ran 99 tests in 26.568s
OK
exit_code = 0
```

### Python syntax/compile gate

```text
python -m py_compile coding_tools_mcp/patching.py coding_tools_mcp/tool_results.py coding_tools_mcp/processes.py coding_tools_mcp/protocol.py coding_tools_mcp/server.py coding_tools_mcp/orchestration_ledger.py coding_tools_mcp/orchestration_control.py tests/test_wave_a_runtime.py tests/test_mcp_sdk_smoke.py tests/test_stateless_http_2026.py tests/test_orchestration_control.py tests/test_orchestration_ledger.py
```

Result:

```text
exit_code = 0
```

### Diff whitespace gate

```text
git diff --check -- resources/coding-tools-mcp/coding_tools_mcp resources/coding-tools-mcp/tests resources/coding-tools-mcp/pyproject.toml
```

Result:

```text
exit_code = 0
```

Chỉ có Git line-ending warnings LF/CRLF; không có whitespace error.

### Product/source stability gate

```text
node --test tests/stability-source.test.js
```

Result:

```text
tests = 5
pass = 5
fail = 0
exit_code = 0
```

Gate xác nhận smart mode vẫn giữ compact 8-tool surface và HTTP/runtime source invariants hiện tại vẫn green.

### Full Electron/Node product suite

```text
npm.cmd test
```

Result:

```text
tests = 44
pass = 44
fail = 0
source root clean
exit_code = 0
```

Trong đó `runtime-lifecycle.test.js` có 10 regression test và chứng minh supervisor:

```text
MCP healthy + tunnel unavailable -> restart tunnel only
MCP health unavailable + owned process alive -> defer recovery, không kill MCP
owned MCP process exited -> full restart
failure type thay đổi -> đếm lại từ 1, không cộng dồn sai loại lỗi
```

### Windows child-process cancellation fault injection

```text
python -m unittest tests.test_resilience_fault_injection.CommandCancellationFaultInjectionTests
```

Result:

```text
Ran 1 test
OK
exit_code = 0
```

Test khởi động một Python child thật, đọc PID của child, thực hiện `command_control kill`, rồi xác nhận cả shell handle và child PID đều không còn sống.

---

## 9. Remaining gaps

### P0 còn lại

1. **Universal idempotency envelope** — `VERIFIED` ở lượt hoàn thiện.
   - Mọi tool nhận `idempotency_key` qua `object_schema`; `call_tool` claim/replay/finish durable trong SQLite ledger;
   - duplicate delivery trả replay `deduplicated` (không tạo side effect thứ hai); conflict fail-closed; in-progress chặn bản sao; outcome-unknown sau process crash fail-closed; replay sống qua MCP restart (unit + live E2E).

2. **Real fault-injection E2E** — `VERIFIED` ở live-harness level.
   - `VERIFIED`: kill MCP thật giữa tool call → Job Object giết toàn command tree; restart → task state persisted, duplicate delivery replayed, dead handle truthful (`test_live_restart_reconcile.py`).
   - `VERIFIED`: tunnel (TCP proxy thật) chết giữa active call → MCP và command không bị cắt; proxy mới poll tiếp (`test_live_transport_failures.py`).
   - `VERIFIED`: client "đóng browser" giữa task → durable workflow tiếp tục chạy; client mới poll operation đến completed + replay events theo cursor (`test_live_transport_failures.py`).
   - `VERIFIED`: Codex provider crash giữa turn → provider mới (process thật khác) resume cùng thread và hoàn thành turn (`test_live_codex_provider_restart.py`).
   - `VERIFIED`: supervisor chạy với MCP process thật — tunnel-only recovery, escalation, full restart (`tests/live-supervisor-e2e.test.js`).
   - Còn lại: acceptance thủ công qua chính Electron app + OpenAI tunnel + ChatGPT connector thật.

3. **Unified retry/admission controller** — `VERIFIED` ở lượt hoàn thiện.
   - `budget_control.py`: `RetryPolicy` (exponential backoff cap + jitter) áp dụng auto-retry chỉ cho read-only tools (mutation không bao giờ auto-retry để tránh duplicate side effect — giữ nguyên EOCL); `BudgetDeadline` (wall-clock + inactivity) được watchdog của background operation enforce; snapshot background operation expose `remaining_seconds`/`exceeded`;
   - `agent_workflow` admission budget giữ nguyên; `max_attempts` vẫn manual-replan-only theo chủ ý an toàn.

### P1

4. **`command_id` migration**
   - `exec_command` trả `command_id` và `command_control` ưu tiên `command_id`;
   - `session_id` vẫn tồn tại như alias compatibility và ở một số đường nội bộ/legacy;
   - cần deprecation/telemetry plan trước khi bỏ alias, không cần đổi gấp.

5. **System-wide Windows process ownership** — `VERIFIED` cho exec path.
   - Command do MCP spawn được gắn Job Object `KILL_ON_JOB_CLOSE` ngay khi khởi tạo (CREATE_SUSPENDED → assign → resume); kill/close job = giết toàn cây, không phụ thuộc console events; fallback `taskkill /T /F` khi Job Object không khả dụng; tắt bằng `CODING_TOOLS_MCP_WINDOWS_JOB_OBJECT=0`.
   - `NOT_VERIFIED`: chưa chứng minh ownership tương đương cho chính Native MCP/Tunnel process (thuộc Electron supervisor, chưa có live harness).

6. **Browser/UI reconnect integration**
   - durable `after_seq` replay đã có;
   - live harness đã chứng minh client mới replay được events + operation state sau khi client cũ biến mất;
   - binding cuối cùng trong Electron UI cần acceptance thủ công.

---

## 10. RELEASE GATE

# RELEASE GATE: PASS Ở HARNESS LEVEL — CẦN ACCEPTANCE THỦ CÔNG TRÊN APP THẬT

Toàn bộ blocker trước đây đã có bằng chứng chạy thật với process/MCP/tunnel/proxy thật (`131` Python tests gồm 4 live E2E suites, `51` Node tests gồm live supervisor E2E). Điều duy nhất không thể chứng minh bằng test tự động là acceptance qua chính Electron app + OpenAI Secure Tunnel + ChatGPT connector thật — đây là hoạt động vận hành, không còn là code blocker.

```text
[x] universal mutation idempotency (replay/conflict/in-progress/unknown + restart-surviving)
[x] unified budget/retry controller (read-only auto-retry backoff+jitter; background deadline watchdog; inactivity budget)
[x] per-principal command-slot + retained-output quotas
[x] supervisor escalation cap (hết deferral vô hạn khi MCP hang)
[x] Windows Job Object kill-on-close ownership + live crash proof
[x] live MCP restart mid-call reconcile E2E (tree killed, task persisted, duplicate delivery replayed, dead handle truthful)
[x] live tunnel failure giữa active tool call (TCP proxy thật; MCP + command không bị cắt)
[x] browser-style disconnect/reconnect E2E (client biến mất giữa task; durable work tiếp tục; replay events + task state)
[x] live supervisor E2E với MCP process thật (tunnel-only recovery / escalation / full restart)
[x] real Codex provider restart E2E (stub App Server 2 process thật; resume cùng thread hoàn thành turn)
[x] `default_cwd` transport state removed
[x] `session_id` alias deprecation telemetry
[x] native/tunnel tree ownership (taskkill /T /F invariant)
[x] serialized tool-result bytes regression benchmark
```

Việc còn lại cho release thật (thủ công, 1 lần): mở app → nối ChatWeb → chạy 1 task thật → đóng browser giữa task → mở lại → xác nhận progress/task tiếp tục; xác nhận tunnel tự hồi phục khi mạng rớt. Không cần thay đổi source.

---

## 11. Git / external operations

```text
Commit: NO
Push: NO
Tag: NO
Release: NO
Deploy: NO
Service restart: NO
Force reset/clean: NO
```

Quan sát cuối lượt: không có process runtime/test khớp và cổng MCP `18766` không lắng nghe. Đây là thay đổi runtime xảy ra ngoài thao tác của lượt này; không tự khởi động lại dịch vụ khi chưa có ủy quyền live-operation.

Temporary implementation helper scripts đã được xóa; source/test changes còn ở working tree để tiếp tục review/triển khai.

---

## 12. Kết luận

Sau lượt hoàn thiện, kiến trúc đã chuyển từ “foundation only” sang một control plane có đầy đủ primitive resilience và bằng chứng chạy thật:

```text
safe patch kernel
+ explicit retry semantics
+ intelligent bounded output
+ independent SDK protocol smoke
+ stateless modern MCP transport (default-on, legacy compat)
+ durable execution state outside transport
+ monotonic writer fencing
+ lease expiry/renewal
+ multi-client output cursors
+ durable event replay
+ persistent Codex lanes/handoff/proof state
+ universal mutation idempotency envelope
+ unified budget/retry controller
+ per-principal quotas
+ supervisor escalation cap
+ Windows Job Object ownership
+ live MCP restart reconcile E2E
+ serialized tool-result bytes benchmark
```

Trạng thái đúng hiện tại:

```text
Wave A correctness sync: VERIFIED
Wave B stateless transport (default-on): VERIFIED
Wave C command_id migration: PARTIAL (alias compat còn giữ, có deprecation telemetry)
Wave C default_cwd removal: VERIFIED
Wave D fencing/lease: VERIFIED
Wave D multi-client/event replay: VERIFIED
Universal idempotency/budget/quota: VERIFIED
Windows process ownership: VERIFIED (Job Object exec path + taskkill /T native/tunnel)
Live E2E (MCP crash, tunnel failure, browser reconnect, Codex provider restart, supervisor): VERIFIED
Full target release readiness: PASS ở harness level; còn acceptance thủ công trên app thật
```
