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
| Universal mutation idempotency envelope | `PARTIAL` | đã có cho `agent_workflow` execute, chưa áp dụng cho mọi mutation |
| `command_id` semantic migration | `PARTIAL` | model-facing API ưu tiên `command_id`; `session_id` còn là alias compatibility và tên nội bộ ở một số đường cũ |
| Unified retry/admission budget | `PARTIAL` | admission đã có cho `agent_workflow`; chưa có controller retry/backoff thống nhất toàn hệ thống |
| Windows command-tree cancellation | `VERIFIED` | `taskkill /T /F` + fault test kiểm tra PID process con đã chết |
| Component-scoped runtime recovery | `VERIFIED` ở source/regression level | tunnel-only recovery giữ MCP; health timeout không kill process sống; full restart chỉ khi MCP process chết |
| Browser close/reopen E2E | `NOT_VERIFIED` | cần fault-injection harness |
| Real MCP process crash/reconcile E2E | `NOT_VERIFIED` | unit/storage primitives đã có |
| Real Codex provider crash/restart E2E | `PARTIAL` | simulated persistent resume đã green |
| System-wide Windows Job Object ownership | `PARTIAL` | command/native/tunnel có tree kill; chưa chứng minh mọi execution path bằng Job Object/equivalent |

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

1. **Universal idempotency envelope**
   - `agent_workflow phase=execute|run` đã có stable idempotency key, durable result và unknown-outcome fail-closed;
   - vẫn cần mở rộng contract này sang các mutation/tool còn lại;
   - duplicate delivery phải không tạo duplicate side effect.

2. **Real fault-injection E2E**
   - đóng/mở ChatWeb giữa task;
   - restart tunnel giữa active MCP call và chứng minh MCP process/tool call không bị cắt;
   - kill/restart MCP process giữa run và reconcile durable operation;
   - kill/restart Codex App Server thật;
   - duplicate delivery;
   - stale lease race;
   - orchestration cancellation/orphan race.

   Source-level supervisor recovery và command child-tree cancellation đã green; chúng chưa thay thế browser/tunnel live acceptance.

3. **Unified retry/admission controller**
   - `agent_workflow` đã enforce `max_auto_steps`, `max_tool_hops`, `max_runtime_seconds` và credit cap trước execution;
   - `max_attempts` hiện là manual-replan-only, chưa phải automatic retry controller;
   - exponential backoff + jitter;
   - inactivity budget;
   - token/cost ceilings.

### P1

4. **`command_id` migration**
   - `exec_command` trả `command_id` và `command_control` ưu tiên `command_id`;
   - `session_id` vẫn tồn tại như alias compatibility và ở một số đường nội bộ/legacy;
   - cần deprecation/telemetry plan trước khi bỏ alias, không cần đổi gấp để sửa lỗi progress hiện tại.

5. **System-wide Windows process ownership**
   - command cancellation, Native MCP và Tunnel hiện có tree kill bằng `taskkill /T /F`;
   - cần chứng minh/chuẩn hóa toàn bộ execution path bằng Job Object hoặc equivalent reconciliation.

6. **Browser/UI reconnect integration**
   - durable `after_seq` replay đã có;
   - UI/client binding vào event replay + handoff capsule cần E2E.

---

## 10. RELEASE GATE

# RELEASE GATE: BLOCKED

Không nâng full target architecture thành release-ready chỉ vì 99 Python tests và 44 Electron/Node tests đang green.

Các blocker quyết định còn lại:

```text
[ ] universal mutation idempotency
[ ] unified automatic retry/backoff/inactivity budgets
[ ] browser close/reopen fault injection
[ ] live tunnel restart giữ active MCP tool call
[ ] real MCP runtime restart reconciliation E2E
[ ] real Codex provider restart E2E
[ ] orchestration cancellation/orphan race proof
[ ] system-wide Windows process ownership proof
```

Các blocker cũ sau đây đã được giải quyết ở source + regression-test level:

```text
[x] exact-line patch fidelity
[x] explicit retry terminality
[x] head + tail output retention
[x] official MCP SDK legacy smoke
[x] duplicate initialize
[x] stateless 2026 HTTP canary
[x] monotonic fencing token
[x] lease expiry + renewal
[x] stale-writer rejection
[x] per-consumer command output cursor
[x] durable event replay sequence
[x] durable `agent_workflow` execute idempotency + unknown-outcome fail-closed
[x] `agent_workflow` admission budget
[x] Windows command child-tree cancellation fault test
[x] component-scoped supervisor recovery regression
```

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

Sau lượt này, kiến trúc đã chuyển từ “foundation only” sang một control plane có nhiều primitive resilience thật sự:

```text
safe patch kernel
+ explicit retry semantics
+ intelligent bounded output
+ independent SDK protocol smoke
+ opt-in stateless modern MCP transport
+ durable execution state outside transport
+ monotonic writer fencing
+ lease expiry/renewal
+ multi-client output cursors
+ durable event replay
+ persistent Codex lanes/handoff/proof state
```

Trạng thái đúng hiện tại:

```text
Wave A correctness sync: VERIFIED
Wave B stateless transport canary: VERIFIED
Wave D fencing/lease: VERIFIED
Wave D multi-client/event replay: VERIFIED
Agent workflow idempotency/admission: VERIFIED trong phạm vi agent_workflow
Windows command-tree cancellation: VERIFIED bằng child PID fault test
Runtime supervisor component isolation: VERIFIED ở source/regression level
Wave C command_id migration: PARTIAL, model-facing preferred name đã có
Universal mutation idempotency/automatic retry/live browser-tunnel E2E: PARTIAL/NOT_VERIFIED
Full target release readiness: BLOCKED
```
