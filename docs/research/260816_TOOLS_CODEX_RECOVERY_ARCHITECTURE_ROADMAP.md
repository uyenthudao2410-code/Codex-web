# Tools-Codex Recovery Architecture & Implementation Roadmap

**Project:** Tools-Codex-web / `web-mcp-assistant`  
**Workspace được audit:** `E:/Github/Tools-Codex-web`  
**Baseline quan sát gần nhất:** branch `main`, HEAD `64ac538ae374965bf8d51428f4b4508363b79f2f`, worktree đang dirty  
**Ngày lập tài liệu:** 2026-08-16  
**Trạng thái đề xuất:** **GO có điều kiện**  
**Mục tiêu:** Loại bỏ Electron khỏi failure domain của hạ tầng điều khiển, để hệ thống vẫn có thể được chẩn đoán và khôi phục khi Electron UI/main process bị lỗi hoặc bị đóng.

---

## 1. Executive Summary

Vấn đề chính của kiến trúc hiện tại không phải là "Electron chết thì chắc chắn mọi process con chết theo". Coding MCP và OpenAI Tunnel đang được spawn thành process riêng và có thể vẫn tiếp tục tồn tại sau khi Electron main process mất. Vấn đề thực tế là **quyền sở hữu control plane, supervisor, local gateway, secret access và lifecycle management đang nằm trong Electron main process**.

Khi Electron main process chết:

- UI mất;
- watchdog `RuntimeOrchestrator.supervise()` mất;
- khả năng tự khôi phục Coding MCP/Tunnel mất;
- `HubProxyGateway` mất;
- restart ticket do Coding MCP tạo ra không còn supervisor tiêu thụ;
- không còn một control plane độc lập để ChatGPT yêu cầu mở lại Electron.

Do đó, giải pháp đúng là **tách Recovery Host ra khỏi Electron**. Recovery Host chạy headless trong **user session**, tự khởi động khi người dùng đăng nhập Windows, sở hữu lifecycle của Coding MCP, Coding Tunnel, Recovery MCP, Recovery Tunnel và local gateway. Electron trở thành UI/client có thể crash/restart mà không làm mất hạ tầng điều khiển.

Sau khi xem xét phản biện kiến trúc độc lập, Recovery Plane không nên dùng chung process/tunnel với Coding Plane. Nếu Coding MCP hoặc Coding Tunnel chính là failure domain đang hỏng, recovery tools nằm trong cùng failure domain sẽ biến mất. Vì vậy kiến trúc mục tiêu nên có:

```text
ChatGPT Web
   |
   +--> Recovery Tunnel --> Recovery MCP --> Recovery Host
   |
   +--> Coding Tunnel ----> Coding MCP ----> Coding runtime

Recovery Host
   |
   +--> supervise Electron UI
   +--> supervise Coding MCP
   +--> supervise Coding Tunnel
   +--> supervise Recovery Tunnel
   +--> own local gateway
   +--> own runtime health / process state
   +--> expose bounded recovery actions only
```

Tuy nhiên, Recovery Architecture **không phải thuốc chữa tất cả**. Có ba bài toán độc lập cần được quản lý riêng:

1. **Continuity / ledger semantics:** timeout, lease hết hạn, reconnect, `ACCEPTING`, duplicate execution.
2. **Runtime recovery:** Electron, MCP, Tunnel, Gateway chết hoặc treo.
3. **Performance / memory:** ledger allocation, session persistence, payload volume, RAM.

Recovery Host giải quyết trực tiếp bài toán số 2. Nó chỉ được phép restart Coding runtime sau khi bài toán số 1 có invariant đủ mạnh để chứng minh restart/reconnect không replay công việc hoặc làm sai orchestration state.

---

## 2. Vấn đề cần giải quyết

### 2.1 Triệu chứng người dùng

Use case thực tế:

```text
Người dùng đang điều khiển Tools-Codex qua ChatGPT
        |
        v
Electron lỗi / main process crash / app bị tắt
        |
        v
UI mất kết nối
        |
        v
Không còn đường trong app để restart Electron hoặc runtime
        |
        v
Người dùng ở xa không thể tiếp tục công việc
```

Điều người dùng cần không phải một remote desktop đầy đủ. Nhu cầu tối thiểu là:

- kiểm tra máy/runtime còn online không;
- kiểm tra Electron đang chạy hay không;
- mở hoặc restart Electron;
- xem log Electron gần nhất;
- kiểm tra Coding MCP/Tunnel;
- restart Coding runtime khi an toàn;
- đảm bảo mọi thao tác recovery có idempotency, audit và không replay công việc đang chạy.

### 2.2 Single point of failure hiện tại

Hiện tại `electron/main.js` vừa là UI process vừa bootstrap và sở hữu backend runtime:

```text
Electron main
├── BrowserWindow / ChatGPT UI
├── RuntimeOrchestrator
├── HealthService
├── HubProxyGateway
├── Coding MCP lifecycle
├── OpenAI Tunnel lifecycle
└── watchdog khoảng 5 giây/lần
```

`app.whenReady()` tạo `RuntimeOrchestrator`, `HubProxyGateway`, `HealthService`, sau đó chạy `orchestrator.supervise()` theo interval. Vì vậy supervisor logic dù đã khá tốt vẫn nằm trong Electron lifecycle.

### 2.3 Coding MCP và Tunnel không nhất thiết chết cùng Electron

`NativeService` và `TunnelService` spawn process riêng, `windowsHide: true`, có `unref()`, và hiện không dùng `detached: true`. Vì vậy không nên mô hình hóa hệ thống theo giả định:

```text
Electron chết => MCP chết => Tunnel chết
```

Mô hình đúng hơn là:

```text
Electron chết
   |
   +--> MCP có thể còn sống
   +--> Tunnel có thể còn sống
   +--> nhưng supervisor chắc chắn mất
   +--> local gateway chắc chắn mất
   +--> lifecycle ownership mất
   +--> recovery request consumer mất
```

### 2.4 Continuity failure là bài toán riêng

`Message delivery timed out`, stale lease và reconnect không phải lỗi mà Recovery Host tự động chữa được.

Một failure pattern nguy hiểm là:

```text
tool/run hoàn thành hoặc đã tới ACCEPTING
        |
        v
response stream về client timeout
        |
        v
compact task state không phản ánh canonical ledger
        |
        v
controller lease hết TTL nhưng row vẫn trông active
        |
        v
client reconnect không biết phải resume / accept / reject
        |
        v
retry có nguy cơ tạo work trùng
```

Do đó, **restart capability chỉ an toàn khi canonical ledger semantics đủ mạnh**.

---

## 3. Những gì code hiện tại đã có và có thể tái sử dụng

### 3.1 `RuntimeOrchestrator`

File chính:

- `electron/services/runtimeOrchestrator.js`

Đã có các primitive quan trọng:

- `start()`
- `stop()`
- `restart()`
- `lightweightSnapshot()`
- `supervise()`
- `recoverTunnelOnly()`
- `pendingSupervisorRestartRequest()`
- `serviceSupervisorRestartRequest()`

Supervisor hiện phân biệt các failure class:

```text
tunnel_unavailable
mcp_health_unavailable
mcp_process_exited
```

Nó không restart toàn bộ một cách mù quáng. Nếu MCP khỏe nhưng Tunnel chết, nó chỉ recover Tunnel. Nếu MCP process còn sống nhưng health check tạm thời lỗi, nó defer recovery để tránh cắt tool call đang chạy. Sau nhiều lần deferral mới escalation thành full restart.

Backoff đã có giới hạn tăng dần, tối đa khoảng 60 giây.

**Kết luận:** Không nên viết supervisor mới từ đầu. Nên extract và đổi ownership.

### 3.2 `NativeService`

File:

- `electron/services/nativeService.js`

Đã có:

- process fingerprint theo workspace/port/permission;
- PID state;
- reuse process nếu fingerprint khớp;
- start Python MCP với bearer auth;
- kill toàn process tree bằng `taskkill /T /F` khi cần;
- supervisor request file được truyền qua environment.

### 3.3 `TunnelService`

File:

- `electron/services/tunnelService.js`

Đã có:

- bundled `tunnel-client.exe`;
- outbound tunnel;
- Runtime API Key đi qua environment;
- MCP bearer truyền qua environment header;
- health port cục bộ;
- PID state;
- start/stop/status.

Điều này có nghĩa là bài toán "máy local giữ một đường outbound để ChatGPT có thể gọi vào" đã có nền tảng. Không cần tự xây public HTTP reverse proxy mới chỉ để giải quyết Electron recovery.

### 3.4 `HealthService`

File:

- `electron/services/healthService.js`

Đã có ownership check và repair logic cho:

- workspace;
- runtime;
- tunnel client;
- secrets;
- ports;
- MCP;
- Tunnel.

### 3.5 `HubProxyGateway`

File:

- `electron/services/hubProxyGateway.js`

Đã có:

- loopback-only HTTP server;
- per-process random bearer token;
- allowlisted proxy identities;
- request/response size limits;
- timing-safe token compare;
- bounded telemetry;
- local descriptor file;
- upstream forwarding vào Coding MCP.

Điểm yếu hiện tại là gateway **thuộc Electron process**. Descriptor còn ghi `electron_pid`, thể hiện ownership đang gắn với Electron.

### 3.6 Coding MCP restart ticket

Các file liên quan:

- `resources/coding-tools-mcp/coding_tools_mcp/coordination.py`
- `resources/coding-tools-mcp/coding_tools_mcp/tool_schema.py`

Coding MCP đã có `restart_runtime` và `_enqueue_runtime_restart()` với các protection quan trọng:

- yêu cầu `confirm_restart=true`;
- từ chối khi còn active commands/background operations;
- ticket có TTL;
- bind đúng workspace;
- atomic write;
- duplicate pending ticket được nhận biết;
- response được phép flush trước khi supervisor restart runtime.

Điểm cần thay đổi là khái niệm `supervisor = electron`. Sau kiến trúc mới, supervisor phải là Recovery Host.

### 3.7 Regression/fault tests hiện có

Focused supervisor/proxy/lifecycle suite đã được chạy trong audit và cho kết quả:

```text
23 passed
0 failed
```

Các behavior đã được test gồm:

- Tunnel chết nhưng MCP khỏe => chỉ recover Tunnel;
- live MCP không bị kill bởi transient health failure;
- hung MCP được defer trước khi escalation;
- exited MCP dẫn tới full restart;
- restart ticket fresh được consume một lần;
- stale/wrong-workspace ticket bị loại;
- process tree stop path có `/T /F`;
- local gateway giữ bearer thật bên trong backend.

Worktree hiện tại cũng đang có WIP continuity fixes cho:

- persist lease expiry;
- rebuild compact projection từ SQLite ledger;
- giữ `ACCEPTING` resumable;
- hiển thị `Awaiting acceptance`.

Focused continuity checks đã xác nhận các oracle chính liên quan lease expiry và reconnect acceptance đang pass.

---

## 4. Phân loại failure domain

### 4.1 Continuity / Orchestration failure domain

Ví dụ:

- response timeout;
- controller mất kết nối;
- lease TTL hết;
- compact state stale;
- canonical state là `ACCEPTING` nhưng UI báo `Waiting for model`;
- retry tạo duplicate work;
- proof đã hoàn thành nhưng acceptance chưa được ghi nhận.

**Owner:** Coding MCP + orchestration ledger semantics.  
**Recovery Host:** không được tự sửa semantics; chỉ được dựa trên canonical state để quyết định restart có an toàn hay không.

### 4.2 Runtime failure domain

Ví dụ:

- Electron main crash;
- Coding MCP exited;
- Coding MCP hung;
- Coding Tunnel disconnected;
- Recovery Tunnel disconnected;
- local gateway died;
- stale PID/process ownership.

**Owner:** Recovery Host.

### 4.3 Performance / resource failure domain

Ví dụ:

- RAM tăng;
- large session persistence snapshot;
- excessive response bytes;
- ledger size;
- log volume.

**Owner:** runtime/persistence optimization.  
**Recovery Host:** có thể quan sát và report, nhưng không được xem restart là fix mặc định cho memory architecture.

---

## 5. Mục tiêu kiến trúc

### 5.1 Mục tiêu bắt buộc

1. Electron là disposable UI.
2. Electron chết không làm mất supervisor.
3. Electron chết không làm mất Coding MCP/Tunnel chỉ vì lifecycle owner chết.
4. Coding MCP chết vẫn còn Recovery MCP để chẩn đoán và restart.
5. Coding Tunnel chết vẫn còn Recovery Tunnel.
6. Recovery actions là typed capability, không phải arbitrary shell.
7. Restart Coding runtime phải dựa trên canonical ledger state.
8. Duplicate recovery request phải idempotent.
9. Recovery logs phải bounded và redacted.
10. Mọi destructive/high-impact recovery action phải fail closed khi state không đủ chắc chắn.

### 5.2 Non-goals của V1

Không cố giải quyết trong V1:

- remote desktop GUI hoàn chỉnh;
- pre-login Windows control;
- Wake-on-LAN / máy mất điện;
- tự động sửa mọi coding bug qua recovery plane;
- arbitrary PowerShell/command execution từ Recovery MCP;
- thay thế Coding MCP;
- thay thế orchestration ledger;
- chữa RAM bằng restart định kỳ;
- xây bot Telegram/OpenClaw/VPS riêng chỉ để cứu Electron.

---

## 6. Nguyên tắc thiết kế

### Principle A — Recovery plane phải độc lập failure domain

Không đặt recovery tools trong cùng Coding MCP process/tunnel nếu mục tiêu là cứu Coding MCP/tunnel.

Sai:

```text
ChatGPT --> Coding Tunnel --> Coding MCP --> restart Coding MCP
```

Nếu Coding Tunnel/MCP chết, lệnh restart không tồn tại.

Đúng:

```text
ChatGPT --> Recovery Tunnel --> Recovery MCP --> Recovery Host
                       |
                       +--> restart/check Coding MCP
```

### Principle B — Canonical ledger là source of truth

Không dựa vào UI text hoặc compact state cũ để quyết định restart.

```text
SQLite orchestration ledger / authoritative runtime state
        |
        v
preflight restart decision
```

### Principle C — Recovery tool schema tối thiểu

Model chỉ được chọn hành động từ allowlist. Không được cung cấp executable/path/PID/environment tùy ý.

### Principle D — Idempotency ở mọi write action

Mỗi write action phải có operation/restart identity bền vững. Reconnect/retry không được gây double restart hoặc duplicate work.

### Principle E — User-session first

V1 chạy cùng Windows user session để:

- giữ compatibility với secret store hiện tại;
- có interactive desktop để mở Electron;
- tránh Session 0 complexity;
- giảm phạm vi installer/service migration.

Windows SCM + per-user helper chỉ là Phase sau nếu có yêu cầu pre-login.

### Principle F — Recovery phải tự heal cục bộ

Không thể dùng ChatGPT gọi chính một recovery tunnel đang chết để sửa tunnel đó. Recovery Host phải tự supervise Recovery Tunnel local.

---

## 7. Kiến trúc mục tiêu

```text
                         +----------------------+
                         |     ChatGPT Web      |
                         +----------+-----------+
                                    |
                   +----------------+----------------+
                   |                                 |
                   v                                 v
        +----------------------+          +----------------------+
        |   Recovery Tunnel    |          |    Coding Tunnel     |
        +----------+-----------+          +----------+-----------+
                   |                                 |
                   v                                 v
        +----------------------+          +----------------------+
        |     Recovery MCP     |          |      Coding MCP      |
        |   fixed tool schema  |          | coding/orchestration |
        +----------+-----------+          +----------+-----------+
                   |                                 |
                   +---------------+-----------------+
                                   |
                                   v
                      +---------------------------+
                      |       Recovery Host       |
                      |     user-session/headless |
                      +-------------+-------------+
                                    |
             +----------------------+-----------------------+
             |                      |                       |
             v                      v                       v
      +-------------+       +---------------+       +---------------+
      | Electron UI |       | Local Gateway |       | Runtime State |
      | disposable  |       | Codex/OpenCode|       | logs/health   |
      +-------------+       +---------------+       +---------------+
```

### 7.1 Optional break-glass channel

Không phải core architecture, nhưng có thể giữ một đường cứu hộ thứ ba nếu cần điều khiển bằng điện thoại khi ChatGPT custom MCP không khả dụng:

```text
Phone
  |
Tailscale
  |
Windows OpenSSH
  |
fixed recovery CLI
```

Break-glass CLI nên gọi cùng typed recovery API nội bộ, không bypass bằng một shell không kiểm soát trừ khi operator chủ động dùng SSH admin.

---

## 8. Trách nhiệm từng component

### 8.1 Recovery Host

Recovery Host là control-plane owner mới.

Trách nhiệm:

- load runtime settings;
- access secrets trong đúng user context;
- start/supervise Coding MCP;
- start/supervise Coding Tunnel;
- start/supervise Recovery MCP;
- start/supervise Recovery Tunnel;
- own local gateway;
- monitor Electron process;
- start/restart Electron;
- serve local authenticated IPC;
- reconcile process state;
- record bounded recovery audit.

Recovery Host **không**:

- thực hiện arbitrary coding command;
- tự quyết định sửa source;
- thay đổi orchestration state theo suy đoán;
- auto-force restart một busy Coding runtime.

### 8.2 Recovery MCP

Recovery MCP phải có dependency graph nhỏ, không import Coding MCP runtime để tránh cùng failure domain.

Tool surface đề xuất:

| Tool | Loại | Mục đích |
|---|---|---|
| `system_status` | read | tổng quan host, Electron, Coding plane, Recovery plane |
| `electron_status` | read | PID/health/start time/last exit |
| `electron_start` | write | mở Electron khi đang stopped |
| `electron_restart` | write | restart Electron có idempotency |
| `electron_logs` | read | đọc tail bounded/redacted |
| `coding_tools_status` | read | trạng thái Coding MCP/Tunnel/ledger safety |
| `coding_tools_restart` | write | controlled restart sau canonical preflight |
| `tunnel_status` | read | trạng thái hai tunnel |

Không expose:

- `run_command`;
- `powershell`;
- `kill_pid`;
- `start_process(path)`;
- `read_file(path)`;
- `set_env`;
- arbitrary log path;
- arbitrary executable/argv.

### 8.3 Coding MCP

Tiếp tục là execution/orchestration plane cho coding.

Nó không nên là recovery owner của chính nó.

Thay đổi cần thiết:

- restart request hướng tới Recovery Host thay vì Electron supervisor;
- expose canonical preflight state đủ để Recovery Host quyết định restart;
- preserve idempotency/restart ticket semantics;
- reconnect/acceptance invariants phải được hoàn tất trước khi remote write recovery mở ra.

### 8.4 Electron UI

Sau refactor Electron chỉ còn:

- BrowserWindow;
- ChatGPT view;
- renderer;
- local IPC client;
- UI display/control.

Không còn:

- ownership Coding MCP;
- ownership Coding Tunnel;
- ownership local gateway;
- watchdog chính;
- secret lifecycle owner duy nhất.

### 8.5 Local Gateway

Chuyển từ Electron process sang Recovery Host.

Descriptor nên đổi từ dạng ownership Electron:

```json
{
  "electron_pid": 12345
}
```

sang dạng generic:

```json
{
  "version": 2,
  "owner_type": "recovery-host",
  "owner_pid": 12345,
  "created_at": "..."
}
```

Mục tiêu: Codex Desktop/OpenCode không mất gateway chỉ vì Electron UI crash.

---

## 9. Secret và path architecture

### 9.1 Vấn đề hiện tại

`electron/paths.js` phụ thuộc trực tiếp Electron API:

- `app.getPath('userData')`;
- `app.isPackaged`;
- `app.getAppPath()`.

Trong khi backend services cần các path:

- settings;
- secrets;
- runtime state;
- supervisor request;
- gateway descriptor;
- logs;
- tunnel executable;
- Python/runtime resources.

`SecretStore` lại dùng Electron `safeStorage`.

### 9.2 Refactor đề xuất

Tách path resolver khỏi Electron:

```text
RuntimePaths
├── dataRoot
├── resourcesRoot
├── settingsFile
├── secretsFile
├── stateFile
├── supervisorRequestFile
├── logs
└── binaries
```

Inject `RuntimePaths` vào backend services.

V1 có thể vẫn dùng một user-session host để giữ compatibility với secret context hiện tại. Chưa cần chuyển ngay sang LocalSystem credential model.

### 9.3 Quy tắc secret

- Không ghi secret vào log.
- Không truyền secret qua command line nếu có thể dùng environment/file ACL.
- Recovery MCP không trả secret status ngoài boolean/metadata tối thiểu.
- Descriptor local không chứa MCP bearer thật.
- Nếu sau này chuyển SCM service, secret migration phải là một project riêng có rollback.

---

## 10. Local IPC giữa Electron và Recovery Host

Electron cần một đường local để:

- query runtime state;
- request normal start/stop/restart;
- subscribe heartbeat/status;
- request logs;
- nhận startup/reconnect state.

Đề xuất ưu tiên:

1. loopback HTTP với ephemeral/local token đã có pattern tương tự `HubProxyGateway`; hoặc
2. Windows named pipe với ACL theo user SID.

V1 nên chọn giải pháp có ít code mới nhất. Nếu reuse loopback HTTP:

- bind `127.0.0.1` only;
- token random đủ mạnh;
- descriptor file permission hạn chế;
- allowlist route;
- request size limit;
- no arbitrary proxy;
- process ownership verified.

Không expose Recovery Host trực tiếp ra LAN.

---

## 11. Restart protocol

### 11.1 `electron_start`

Preconditions:

- Recovery Host healthy;
- interactive user session tồn tại;
- không có Electron instance hợp lệ đang chạy;
- executable path lấy từ trusted configuration, không từ model.

Flow:

```text
request
  |
  v
idempotency check
  |
  v
verify Electron absent
  |
  v
spawn trusted Electron executable
  |
  v
wait for local heartbeat / window-ready marker
  |
  v
return ready/failed + bounded evidence
```

### 11.2 `electron_restart`

Flow:

```text
request
  |
  v
idempotency check
  |
  v
mark restart intent
  |
  v
graceful shutdown nếu có thể
  |
  v
bounded wait
  |
  +--> still alive -> controlled kill trusted process tree
  |
  v
start Electron
  |
  v
health/heartbeat verify
```

Không được dùng PID do model cung cấp.

### 11.3 `coding_tools_restart`

Đây là action rủi ro cao hơn.

Bắt buộc:

```text
request
  |
  v
idempotency check
  |
  v
read canonical orchestration state
  |
  +--> active execution/background op -> REFUSE
  |
  +--> uncertain/stale state -> REFUSE
  |
  +--> ACCEPTING -> preserve resumable acceptance
  |
  +--> idle/safe -> continue
  |
  v
record restart ticket
  |
  v
stop Coding Tunnel nếu cần
  |
  v
restart Coding MCP
  |
  v
wait health
  |
  v
restart/rebind Coding Tunnel
  |
  v
reconcile canonical ledger projection
  |
  v
verify process/server instance changed
  |
  v
return bounded result
```

### 11.4 Force restart

Không nên thiết kế V1 chỉ bằng:

```json
{ "force": true }
```

vì model có thể tự quyết định thêm boolean.

Nếu thật sự cần force semantics, nên là capability/action riêng, ví dụ:

```text
coding_tools_force_restart
```

với confirmation contract mạnh hơn và operator-visible reason.

---

## 12. Continuity invariants — Phase 0 gate

Các invariant phải được xem là điều kiện trước khi remote restart Coding runtime được bật:

### Invariant 1 — Lease expiry được persist

```text
expires_at <= now
=> durable status != active
```

Không chỉ derive `expired` trong memory.

### Invariant 2 — `ACCEPTING` là resumable

```text
canonical latest state == ACCEPTING
=> reconnect returns ACCEPTING
=> current_step = Awaiting acceptance
=> không replay execution/proof
```

### Invariant 3 — Proof không bị mất vì transport timeout

Timeout response không được làm hệ thống coi work là chưa chạy nếu durable proof đã tồn tại.

### Invariant 4 — Retry không tạo duplicate work

Idempotency/fencing phải ngăn duplicate mutation sau reconnect.

### Invariant 5 — Compact projection có thể rebuild từ durable ledger

Không dùng task-state JSON stale làm source of truth khi ledger đã có canonical evidence mới hơn.

### Invariant 6 — Restart không tự động accept/reject

Recovery Host chỉ preserve/reconcile state. Final acceptance vẫn thuộc đúng controller/acceptance owner.

---

## 13. Lộ trình triển khai chi tiết

# Phase 0 — Hoàn thiện Continuity / Ledger Hardening

### Mục tiêu

Làm cho restart/reconnect an toàn về orchestration semantics trước khi mở remote write recovery cho Coding runtime.

### Phạm vi

Các WIP hiện tại liên quan:

- `resources/coding-tools-mcp/coding_tools_mcp/orchestration_ledger.py`
- `resources/coding-tools-mcp/coding_tools_mcp/server.py`
- `resources/coding-tools-mcp/coding_tools_mcp/mcp_http_handler.py`
- `resources/coding-tools-mcp/coding_tools_mcp/coordination.py`
- `resources/coding-tools-mcp/tests/test_coordination_state.py`
- `resources/coding-tools-mcp/tests/test_orchestration_workflow.py`
- projection/UI trạng thái liên quan.

### Công việc

1. Review diff WIP hiện có.
2. Xác nhận `expire_controller_leases()` persist DB status.
3. Xác nhận reconnect rebuild canonical projection.
4. Xác nhận `ACCEPTING` không bị stale reconciliation abort.
5. Xác nhận lease reacquire tăng fencing token đúng.
6. Xác nhận timeout/reconnect không replay tool work.
7. Xác nhận compact state đổi từ `Waiting for model` sang `Awaiting acceptance` khi phù hợp.
8. Chạy focused tests.
9. Chạy affected MCP tests.
10. Chỉ deploy/restart sau khi review/accept WIP hiện tại.

### Acceptance criteria

- expired lease durable không còn `active`;
- reconnect ở `ACCEPTING` quay lại `ACCEPTING`;
- không duplicate tool work;
- proof identity được giữ khi fingerprint không đổi;
- stale reconciliation không phá acceptance-ready run;
- focused tests pass;
- diff được review và accepted.

### Lưu ý Git/orchestration

File `.coding-tools/orchestration/ledger.sqlite3` là artifact orchestration quan trọng của project và không được vô tình loại khỏi commit/push khi thực hiện các commit có chủ đích liên quan project state.

---

# Phase 1 — Extract Headless Recovery Host

**Implementation status (2026-08-16):** local ownership transfer is implemented
for the user-session host and Electron UI client. A deterministic real-Electron
process lane now covers client termination/reattach while the Recovery Host,
gateway, watchdog and Coding MCP/Tunnel process stand-ins retain identity.
Production Coding MCP/Tunnel fault injection and packaged Windows/login
acceptance remain pending; independent Recovery MCP/Tunnel is intentionally not
part of this phase.

### Mục tiêu

Tạo process headless độc lập Electron nhưng vẫn chạy trong cùng user session.

### Thiết kế

Ban đầu chưa cần expose Recovery MCP ra model. Chỉ cần chứng minh lifecycle đã tách.

### Công việc

1. Tạo entrypoint Recovery Host.
2. Extract/inject runtime paths.
3. Cho Recovery Host tạo `RuntimeOrchestrator`.
4. Chuyển Coding MCP lifecycle sang Recovery Host.
5. Chuyển Coding Tunnel lifecycle sang Recovery Host.
6. Chuyển watchdog `supervise()` sang Recovery Host.
7. Chuyển `HubProxyGateway` sang Recovery Host.
8. Giữ Electron UI chạy như client.
9. Thiết kế ownership lock/single-instance cho Recovery Host.
10. Cấu hình auto-start trong user session.

### File dự kiến

New:

- `electron/recoveryHost.js` hoặc package/module tương đương;
- `electron/services/runtimePaths.js`;
- `electron/services/recoveryIpcServer.js`;
- `electron/services/electronUiSupervisor.js`.

Refactor:

- `electron/main.js`;
- `electron/paths.js`;
- `electron/services/runtimeOrchestrator.js`;
- `electron/services/hubProxyGateway.js`;
- `electron/services/settingsStore.js`;
- `electron/services/secretStore.js` nếu cần dependency injection.

### Acceptance criteria

- kill Electron main nhưng Recovery Host vẫn chạy;
- Coding MCP vẫn healthy;
- Coding Tunnel vẫn healthy;
- local gateway vẫn reachable;
- Recovery Host watchdog vẫn chạy;
- Electron có thể được mở lại local;
- không có hai Recovery Host cùng sở hữu runtime.

---

# Phase 2 — Electron trở thành UI Client thuần

**Implementation status (2026-08-16):** lifecycle, health, log, and runtime
mutation calls now use authenticated Recovery Host IPC. Direct panel reads of
the Coding MCP data plane remain unchanged for protocol compatibility.

### Mục tiêu

Loại hoàn toàn backend lifecycle ownership khỏi Electron.

### Công việc

1. Electron không gọi trực tiếp `RuntimeOrchestrator.start/stop/restart`.
2. Electron gửi local authenticated request tới Recovery Host.
3. UI subscribe runtime heartbeat/status.
4. Runtime logs được đọc qua bounded API.
5. Manager/control center hiển thị Recovery Host status.
6. Electron shutdown không stop Coding MCP/Tunnels trừ khi operator explicit chọn stop services.
7. `keepRunningOnClose` được định nghĩa lại cho UI vs infrastructure.

### Acceptance criteria

- close UI không dừng infrastructure;
- crash Electron không đổi PID Coding MCP/Tunnels;
- reopen Electron attach lại runtime hiện hữu;
- không regenerate secrets/tokens vô tình khi Electron reopen;
- UI không trở thành source of truth của runtime state.

---

# Phase 2.5 — Development Code Activation / Revision Awareness

**Implementation status (2026-08-16):** Wave 2.5A observation và Wave 2.5B
controlled activation đã được triển khai trong source/worktree. Chưa activate
process đang sống, package, deploy hoặc production-acceptance.

### Mục tiêu

Phân biệt code process đã load với source hiện có trên disk mà không dùng hot
reload hoặc restart theo file watcher.

`package.json` có dependency `electron-updater`, nhưng source hiện không import
`autoUpdater` hoặc gọi check/download/install. Do đó app đang chạy không có
self-update path chỉ vì dependency này tồn tại; development source, packaged app,
Python MCP, tunnel binary và Rust binary đều cần activation/rebuild riêng theo
component.

### Nuance của implementation hiện tại

`NativeService` có fingerprint workspace/config và nhánh reuse process cùng
fingerprint. Tuy nhiên `RuntimeOrchestrator.start()` hiện dừng runtime cũ trước
khi gọi `NativeService.start()`, nên nhánh reuse không phải đường chính của một
manual start. Vấn đề stale code vẫn có thật ở health/watchdog path: MCP healthy
tiếp tục được giữ nguyên dù source Python trên disk đã đổi; Recovery Host healthy
cũng được `ensureRecoveryHost()` reuse sau khi source JavaScript đổi.

### Thiết kế observation-first

Mỗi component dùng content hash từ manifest source cố định:

- `recovery_host`: entrypoint và các lifecycle/IPC/path/service dependencies;
- `coding_mcp`: `pyproject.toml` và package `coding_tools_mcp/**/*.py`;
- `electron_ui`: Electron UI entry/preload/controller và renderer JS/CSS/HTML.

Không dùng Git HEAD làm revision duy nhất vì HEAD không đổi khi source dirty hoặc
untracked. Không hash toàn repository và không đưa `.coding-tools` runtime
evidence vào revision. Tracker giới hạn file/bytes và cache 30 giây, nên watchdog
5 giây không hash lại source ở mỗi tick.

Schema quan sát:

```json
{
  "running_revision": "...",
  "disk_revision": "...",
  "update_pending": true,
  "state": "update_pending"
}
```

Recovery Host chụp `running_revision` khi process boot. Coding MCP revision được
persist vào `runtime-state.json` và truyền qua environment khi process spawn.
Runtime legacy đang sống nhưng chưa có revision được báo `unknown`, không suy
đoán rằng code đang current.

### Controlled activation đã triển khai

Wave này không thêm watcher hoặc auto restart. `activate_update()` hiện có:

1. typed request riêng cho `coding_mcp`, `electron_ui`, `recovery_host`, TTL tối
   đa 60 giây và không nhận path/executable/shell/remote kill PID;
2. bounded atomic `recovery-actions.json` cho replay/idempotency/result;
3. authenticated Coding MCP activation preflight + admission fence, xét active
   tool/command/background/managed process/agent lane và canonical ledger;
4. explicit preservation cho durable `ACCEPTING`; các active state khác fail
   closed bằng `RUNTIME_BUSY`, integrity/identity không chắc chắn bằng
   `ORCHESTRATION_STATE_UNCERTAIN`;
5. Coding MCP restart riêng và giữ tunnel; health/workspace/instance/revision
   được verify sau restart;
6. Electron UI running-revision registration và fixed-argv self-relaunch;
7. Recovery Host replacement bằng fixed-argv/owner-lock handoff, giữ MCP/Tunnel
   và bounded rollback về host cũ nếu replacement không healthy;
8. không có action restart-all.

### Acceptance criteria của foundation

- sửa source allowlisted làm `disk_revision` đổi;
- `running_revision` giữ nguyên cho tới process replacement;
- `update_pending=true` không tự restart component;
- file ngoài manifest không làm revision đổi;
- legacy/uncertain running revision fail truthful thành `unknown`;
- hashing bounded, component-scoped và không chạy mỗi watchdog tick.

### Acceptance criteria của controlled activation

- duplicate cùng operation/payload replay durable result; payload khác fail
  `IDEMPOTENCY_CONFLICT`; request hết TTL không mutate process;
- preflight atomically fence tool admission và refuse active/uncertain state;
- Coding MCP activation không đổi tunnel instance và chỉ complete sau expected
  revision health check cùng process/server identity mới; revision đổi trước
  stop/spawn hoặc replacement không verify được sẽ fail closed;
- Electron UI activation complete sau registration của UI instance/revision mới;
- Recovery Host handoff giữ Coding MCP/Tunnel; replacement failure làm host cũ
  reacquire ownership trong bounded timeout;
- không action nào nhận arbitrary executable/path/shell hoặc restart tất cả.

---

# Phase 3 — Independent Recovery MCP + Recovery Tunnel

### Mục tiêu

Tạo remote recovery plane tách failure domain khỏi Coding plane.

### Công việc

1. Tạo Recovery MCP process nhỏ.
2. Tool schema fixed, typed.
3. Recovery Host supervise Recovery MCP.
4. Khởi động Recovery Tunnel riêng.
5. Recovery Tunnel forward chỉ tới Recovery MCP.
6. Coding Tunnel tiếp tục forward Coding MCP riêng.
7. Recovery Tunnel có local self-healing.
8. Tạo independent health state cho hai tunnel.

### Bắt buộc độc lập

Recovery MCP không được:

- import Coding MCP runtime như library;
- phụ thuộc Coding MCP port đang healthy để boot;
- dùng Coding Tunnel để expose itself;
- chết khi Coding MCP restart.

### Acceptance criteria

- kill Coding MCP => Recovery MCP vẫn callable;
- kill Coding Tunnel => Recovery MCP vẫn callable;
- restart Coding MCP qua Recovery plane thành công khi idle;
- Recovery Tunnel restart không làm Coding MCP restart;
- Coding Tunnel restart không làm Recovery MCP restart.

---

# Phase 4 — Recovery Safety Protocol

### Mục tiêu

Đưa Recovery Plane từ prototype thành trusted control plane.

### Công việc

1. Idempotency key cho mọi write action.
2. Stable action result store hoặc bounded operation state.
3. Canonical ledger preflight trước `coding_tools_restart`.
4. Typed refusal codes:
   - `RUNTIME_BUSY`
   - `ORCHESTRATION_STATE_UNCERTAIN`
   - `ACCEPTANCE_PENDING`
   - `RECOVERY_HOST_NOT_READY`
   - `ELECTRON_ALREADY_RUNNING`
   - `RESTART_ALREADY_PENDING`
5. Request TTL.
6. Bounded log tail.
7. Secret redaction.
8. Audit metadata:
   - action;
   - target component;
   - request identity;
   - result;
   - duration;
   - old/new process instance IDs.
9. Không log arbitrary command vì Recovery Plane không có arbitrary command.
10. Rate limiting/cooldown để tránh crash loop.

### Circuit breaker

Ví dụ:

```text
Electron restart fail 3 lần / 5 phút
=> stop auto restart
=> mark recovery_blocked
=> require operator action
```

Tương tự cho Coding MCP/Tunnels.

### Acceptance criteria

- duplicate idempotency key không thực hiện action lần hai;
- busy Coding runtime bị từ chối;
- uncertain canonical state bị từ chối;
- logs không chứa bearer/runtime API key;
- repeated crash kích hoạt circuit breaker;
- audit đủ để biết action nào đã xảy ra mà không cần log sensitive payload.

---

# Phase 5 — Fault Injection & Acceptance

### Mục tiêu

Chứng minh recovery bằng deterministic faults thay vì chỉ code review.

### Test matrix

| Fault | Kỳ vọng |
|---|---|
| Kill Electron renderer | UI recover/reopen, backend không đổi |
| Kill Electron main | Recovery Host/Coding MCP/Tunnels sống |
| Close Electron bình thường | infrastructure tiếp tục nếu policy keep-running |
| Kill Coding MCP khi idle | Recovery detects và restart theo policy |
| Kill Coding MCP giữa active operation | không auto-kill/replay; state xử lý theo policy |
| Coding MCP hung health | defer trước escalation |
| Kill Coding Tunnel | Recovery plane vẫn callable, Coding Tunnel auto-heal |
| Kill Recovery Tunnel | local Recovery Host tự heal |
| Kill Recovery MCP | Recovery Host restart Recovery MCP |
| Kill Recovery Host | startup/supervision policy khôi phục host |
| Reconnect tại `ACCEPTING` | resume acceptance, không replay execution |
| Expire controller lease | durable status thành expired |
| Duplicate `electron_restart` | một restart thực tế |
| Duplicate `coding_tools_restart` | một restart thực tế |
| Restart request sai workspace | refuse |
| Restart request stale/expired | refuse |
| Log tail rất lớn | bounded response |
| Secret-like metadata | redacted |
| User logoff/login | V1 behavior được xác định rõ và test |
| Windows reboot/login | Recovery Host auto-start và restore services |

### Acceptance strategy

Mỗi wave chỉ accepted khi:

1. diff nhỏ và ownership rõ;
2. focused oracle pass;
3. adjacent high-risk fault được test;
4. không phá continuity invariants;
5. không tăng failure coupling mới.

---

# Phase 6 — Productization / Windows SCM nếu thật sự cần

### Điều kiện mở phase

Chỉ triển khai nếu requirement trở thành:

> Máy phải recover/control được ngay sau boot, trước khi user đăng nhập Windows.

### Kiến trúc khi đó

```text
Windows SCM Service
      |
      +--> headless infrastructure processes
      |
      +--> secured IPC
              |
              v
      Per-user Launcher
              |
              v
          Electron UI
```

### Công việc bổ sung

- Windows service installer;
- service account model;
- secret migration;
- named pipe ACL/user SID;
- session discovery;
- per-user launcher startup;
- upgrade/rollback;
- service recovery policy;
- uninstall cleanup;
- compatibility migration từ user-session-only version.

### Không làm sớm

Không nên dùng LocalSystem Service V1 để trực tiếp spawn Electron UI. Nó kéo theo Session 0, user token, interactive desktop và secret-context complexity vượt quá giá trị hiện tại.

---

## 14. Security Model

### 14.1 Threat assumptions

Recovery Plane có quyền restart application/runtime nên phải coi là privileged control interface.

Rủi ro chính:

- prompt/model gọi nhầm destructive action;
- replay request;
- local process giả mạo client;
- descriptor/token leak;
- crash loop;
- restart giữa mutation;
- log leak secret;
- compromised Coding MCP cố điều khiển Recovery Host ngoài capability cho phép.

### 14.2 Controls

#### Fixed capabilities

Không arbitrary shell.

#### Trusted paths

Executable path do Recovery Host config quản lý, không do model gửi.

#### Idempotency

Write action có durable request identity.

#### TTL

Stale request không được thực thi.

#### Canonical preflight

Coding restart phải check orchestration truth.

#### Local IPC auth

Loopback token hoặc named-pipe ACL.

#### Bound outputs

Status/log response có size/line/time limits.

#### Redaction

Keys chứa `token`, `secret`, `authorization`, `key` hoặc credential patterns phải bị redact.

#### Audit

Ghi action metadata, không ghi secret/raw arbitrary command.

---

## 15. State Machine đề xuất cho Recovery Host

### Component state

```text
STOPPED
STARTING
HEALTHY
DEGRADED
RECOVERING
BLOCKED
STOPPING
```

### Recovery rules

```text
HEALTHY
  |
  +-- health failure N lần --> DEGRADED
                              |
                              +-- safe recovery --> RECOVERING
                              |                    |
                              |                    +--> HEALTHY
                              |                    +--> BLOCKED
                              |
                              +-- unsafe/busy --> DEGRADED + defer
```

### Không overload state

Không dùng cùng một boolean `running` để đại diện:

- process alive;
- port listening;
- protocol healthy;
- tunnel connected;
- orchestration safe.

Status phải tách các dimension này.

---

## 16. Status schema đề xuất

Ví dụ `system_status`:

```json
{
  "host": {
    "state": "healthy",
    "pid": 1234,
    "started_at": "2026-08-16T07:00:00+07:00"
  },
  "electron": {
    "state": "stopped",
    "pid": null,
    "last_exit_code": 1
  },
  "coding": {
    "mcp_process": "healthy",
    "mcp_protocol": "healthy",
    "tunnel": "healthy",
    "orchestration_restart_safe": true
  },
  "recovery": {
    "mcp": "healthy",
    "tunnel": "healthy"
  }
}
```

Không trả:

- raw token;
- raw environment;
- command line chứa secret;
- private file paths không cần thiết;
- full log không bounded.

---

## 17. Rollout Strategy

### 17.1 Không big-bang refactor

Triển khai theo ownership transfer từng bước.

### 17.2 Feature flag / dual observation

Trong giai đoạn đầu có thể để Recovery Host chỉ observe trạng thái trong khi Electron vẫn owner, sau đó chuyển ownership một component một lần.

Ví dụ thứ tự:

```text
1. Recovery Host process exists
2. Recovery Host observes only
3. Move watchdog ownership
4. Move local gateway ownership
5. Move Coding MCP ownership
6. Move Coding Tunnel ownership
7. Electron becomes client only
8. Add independent Recovery MCP/Tunnel
```

Tránh để hai supervisor cùng restart cùng một process.

### 17.3 Rollback

Mỗi phase phải có rollback:

- config switch về Electron-owned lifecycle;
- Recovery Host stop không xóa user data;
- không migrate secret format trong cùng phase extraction;
- không đổi quá nhiều persisted schema một lần;
- descriptor versioning backward-compatible trong migration window.

---

## 18. Operational Runbook sau khi hoàn thành

### Case A — Electron chết

Người dùng yêu cầu:

```text
Kiểm tra Electron máy DEV.
```

Recovery:

```text
system_status / electron_status
=> Electron stopped
=> Coding plane healthy
=> Recovery plane healthy
```

Sau đó:

```text
electron_start
```

### Case B — Electron crash loop

Recovery Host thử bounded retry, sau threshold:

```text
state = BLOCKED
reason = ELECTRON_CRASH_LOOP
```

Operator đọc `electron_logs`, sau đó dùng Coding plane để sửa code nếu Coding plane vẫn healthy.

### Case C — Coding Tunnel chết

Recovery Host tự restart Coding Tunnel. Recovery Tunnel không bị ảnh hưởng.

### Case D — Coding MCP chết khi idle

Recovery plane kiểm tra ledger safe, restart MCP, rebind Coding Tunnel, verify new instance ID.

### Case E — Coding MCP chết khi orchestration đang chạy

Không giả định work có thể replay. Reconnect vào canonical ledger, xác định state và proof trước khi hành động tiếp.

### Case F — Recovery Tunnel chết

Recovery Host tự heal cục bộ. Không chờ ChatGPT ra lệnh sửa chính đường Recovery Tunnel.

---

## 19. Fault-domain matrix cuối

| Sự cố | Coding Plane | Recovery Plane | Khả năng cứu |
|---|---|---|---|
| Renderer crash | sống | sống | Có |
| Electron main crash | sống | sống | Có |
| Electron UI closed | sống | sống | Có |
| Coding MCP crash | chết/degraded | sống | Có |
| Coding Tunnel crash | unavailable remote coding | sống | Có |
| Recovery MCP crash | coding có thể sống | host local còn | Host tự recover |
| Recovery Tunnel crash | coding có thể sống | remote recovery tạm mất | Host tự recover |
| Recovery Host crash | child process có thể còn | control plane mất | startup supervisor phải recover |
| ChatGPT/OpenAI connectivity mất | local sống | remote MCP mất | optional SSH break-glass |
| User logout | V1 dừng theo user session | V1 dừng | Phase 6 nếu cần |
| Machine mất mạng | remote unavailable | remote unavailable | Không giải bằng app |
| Machine mất điện | off | off | Cần WoL/OOB nếu có requirement |

---

## 20. Metrics để đánh giá thành công

### Reliability

- Electron crash recovery success rate.
- Coding Tunnel auto-recovery success rate.
- Coding MCP safe-restart success rate.
- Recovery Tunnel uptime sau user login.
- số lần circuit breaker kích hoạt.

### Continuity

- reconnect tại `ACCEPTING` không replay work;
- duplicate tool execution count = 0;
- stale active lease after TTL = 0 theo canonical DB semantics;
- accepted proof reuse chỉ trên exact fingerprint match.

### Security

- secret exposure in logs = 0;
- arbitrary command surface in Recovery MCP = 0;
- unauthorized local IPC acceptance = 0;
- duplicate recovery mutation do retry = 0.

### Operability

- số bước operator cần để mở lại Electron;
- thời gian từ detection đến healthy state;
- tỷ lệ recovery tự động vs cần manual intervention.

---

## 21. Risks và mitigation

### Risk 1 — Hai supervisor cùng ownership

**Mitigation:** single owner lock + phased migration + explicit ownership state.

### Risk 2 — Recovery Host dùng secret context khác

**Mitigation:** V1 user-session only; không đổi sang LocalSystem sớm.

### Risk 3 — Recovery plane phụ thuộc Coding plane

**Mitigation:** process/tunnel riêng, dependency graph nhỏ.

### Risk 4 — Restart làm mất active orchestration

**Mitigation:** Phase 0 canonical ledger gate + restart preflight + refuse uncertain state.

### Risk 5 — Crash loop gây CPU/process churn

**Mitigation:** exponential backoff + circuit breaker.

### Risk 6 — Local IPC bị lạm dụng

**Mitigation:** loopback-only + strong token hoặc named pipe ACL + fixed routes.

### Risk 7 — Worktree hiện tại đang dirty

**Mitigation:** không thực hiện broad refactor trước khi WIP continuity hiện tại được review/accepted; mỗi phase giữ scope nhỏ và không overwrite unrelated changes.

### Risk 8 — External ChatGPT/MCP platform constraint thay đổi

**Mitigation:** Recovery Host architecture không phụ thuộc UI mobile. Trước release cần re-verify khả năng custom MCP/write actions trên các ChatGPT plan/surface đang dùng. Nếu mobile vẫn là blocker, giữ optional SSH/Tailscale break-glass.

---

## 22. Những quyết định kiến trúc đã loại bỏ

### 22.1 Không dùng OpenClaw làm core recovery

Không cần một conversational gateway lớn chỉ để giải quyết một lifecycle failure trong desktop app.

### 22.2 Không tự xây public recovery API mới

Project đã có tunnel architecture. Public inbound API làm tăng auth/firewall/credential attack surface.

### 22.3 Không dùng một Coding MCP/Tunnel duy nhất cho cả coding và recovery

Vi phạm failure-domain isolation.

### 22.4 Không bắt đầu bằng Windows LocalSystem Service

Tăng complexity liên quan secret context, interactive desktop và installer quá sớm.

### 22.5 Không dùng restart định kỳ để chữa continuity/RAM

Restart là recovery operation, không phải substitute cho đúng ledger semantics hoặc memory architecture.

---

## 23. Definition of Done tổng thể

Dự án chỉ coi Recovery Architecture hoàn thành khi:

- Electron có thể bị kill và mở lại mà Coding plane không mất;
- Coding MCP có thể bị kill khi idle và được Recovery plane restart;
- Coding Tunnel có thể bị kill mà Recovery plane vẫn callable;
- Recovery Tunnel có thể bị kill và Recovery Host tự heal;
- reconnect tại `ACCEPTING` không replay work;
- expired controller lease được persist đúng;
- duplicate restart request không gây duplicate action;
- Recovery MCP không có arbitrary command surface;
- logs bounded/redacted;
- secret không xuất hiện trong recovery responses/logs;
- user login/reboot startup behavior có test;
- rollback path tồn tại;
- worktree/project state không bị mất trong migration;
- final fault-injection matrix pass.

---

## 24. Gợi ý chia implementation thành các wave nhỏ

### Wave 0A — Review continuity WIP

```text
OBJECTIVE: prove canonical lease/reconnect semantics
SCOPE: orchestration ledger + projection tests
PROOF: focused continuity tests
STOP: any ambiguous replay/acceptance behavior
```

### Wave 0B — Accept/deploy continuity fixes

Chỉ sau review đầy đủ diff/proof.

### Wave 1A — RuntimePaths extraction

Không đổi behavior, chỉ cắt dependency Electron API khỏi backend path ownership.

### Wave 1B — Recovery Host bootstrap

Headless process + single instance + watchdog, chưa remote.

### Wave 1C — Move local gateway

Gateway ownership sang Recovery Host, giữ protocol compatibility.

### Wave 2A — Move Coding MCP lifecycle

Electron trở thành client của lifecycle owner mới.

### Wave 2B — Move Coding Tunnel lifecycle

Test Electron kill không ảnh hưởng tunnel.

### Wave 2.5A — Revision awareness

Component-scoped bounded hash, persisted Coding MCP running revision và
read-only `update_pending`; tuyệt đối không restart theo file watcher.

### Wave 2.5B — Controlled activation

Đã triển khai idempotency + canonical preflight và action/handoff riêng cho
Coding MCP, Electron UI, Recovery Host; không có restart-all. Packaged/login và
production fault-matrix acceptance vẫn pending.

### Wave 3A — Recovery MCP read-only

Chỉ `system_status`, `electron_status`, `coding_tools_status`, `tunnel_status`.

### Wave 3B — Electron write actions

Thêm `electron_start/restart` với idempotency.

### Wave 3C — Coding restart action

Chỉ sau continuity gate, có canonical preflight.

### Wave 4 — Fault injection

Không thêm feature; chỉ fix những failure được fault tests chứng minh.

### Wave 5 — Startup/installer hardening

User-session auto-start trước. SCM chỉ khi có requirement rõ.

---

## 25. Tài liệu/code cần xem khi triển khai

### Internal code

- `electron/main.js`
- `electron/paths.js`
- `electron/services/runtimeOrchestrator.js`
- `electron/services/nativeService.js`
- `electron/services/tunnelService.js`
- `electron/services/healthService.js`
- `electron/services/hubProxyGateway.js`
- `electron/services/secretStore.js`
- `electron/services/settingsStore.js`
- `resources/coding-tools-mcp/coding_tools_mcp/coordination.py`
- `resources/coding-tools-mcp/coding_tools_mcp/orchestration_ledger.py`
- `resources/coding-tools-mcp/coding_tools_mcp/server.py`
- `resources/coding-tools-mcp/coding_tools_mcp/mcp_http_handler.py`
- `resources/coding-tools-mcp/coding_tools_mcp/tool_schema.py`
- `tests/runtime-lifecycle.test.js`
- `tests/live-supervisor-e2e.test.js`
- `tests/hub-proxy-gateway.test.js`
- `resources/coding-tools-mcp/tests/test_coordination_state.py`
- `resources/coding-tools-mcp/tests/test_orchestration_workflow.py`

### External constraints cần re-verify trước release

- OpenAI Secure MCP Tunnel behavior/capabilities;
- ChatGPT custom/full MCP availability trên web/mobile và theo plan;
- Windows interactive service/session behavior nếu triển khai SCM;
- Electron `safeStorage` behavior trên Windows nếu đổi process/user context.

Không nên đóng cứng các product-plan/mobile constraints vào kiến trúc lõi vì chúng có thể thay đổi. Kiến trúc Recovery Host phải vẫn đúng dù bề mặt ChatGPT thay đổi.

---

## 26. Kết luận quyết định

**Khuyến nghị cuối cùng: GO theo lộ trình continuity-first và failure-domain isolation.**

Kiến trúc mục tiêu:

```text
Continuity-safe canonical ledger
        +
User-session Recovery Host
        +
Independent Recovery MCP/Tunnel
        +
Independent Coding MCP/Tunnel
        +
Electron = UI only
        +
Optional Tailscale/SSH break-glass
```

Không cần viết lại supervisor từ số 0. Code hiện tại đã có phần lớn lifecycle primitives và fault-tested behavior cần thiết. Công việc giá trị cao nhất là **chuyển ownership ra khỏi Electron**, **tách Recovery Plane khỏi Coding Plane**, và **đặt canonical continuity invariants làm safety gate trước remote Coding restart**.

Lộ trình nên triển khai tuần tự, mỗi phase có oracle và rollback riêng. Không nên kết hợp continuity refactor, secret migration, Windows SCM và Recovery MCP vào một big-bang change.

---

## 27. Trạng thái tại thời điểm lập tài liệu

- Workspace audit: `E:/Github/Tools-Codex-web`.
- Branch: `main`.
- HEAD quan sát: `64ac538ae374965bf8d51428f4b4508363b79f2f`.
- Worktree đang có nhiều WIP/uncommitted changes ở orchestration/ledger/runtime liên quan.
- Focused Electron supervisor/proxy/lifecycle suite đã pass trong audit.
- Focused continuity oracle về persisted lease expiry và reconnect `ACCEPTING` đã pass khi chạy đúng package working directory.
- Wave 1A/1B/1C implementation đã được thêm vào worktree: RuntimePaths,
  Recovery Host bootstrap/lock/IPC, watchdog ownership và local gateway owner.
- Real-process lane `npm run test:recovery:e2e` dùng Electron runtime thật và
  state cô lập đã cover client kill/reattach, host/watchdog/gateway continuity và
  PID continuity của Coding MCP/Tunnel stand-in. Đây chưa phải production binary
  hoặc packaged/login acceptance.
- Phase 2.5 đã thêm component-scoped revision hashes, UI registration, durable
  idempotent activation actions, canonical MCP activation fence, component-only
  restart/handoff và post-activation revision verification. Không có watcher,
  automatic activation hoặc restart-all; process sống chưa tự load source này
  cho tới explicit controlled activation sau validation.
- Electron UI hiện là lifecycle client; independent Recovery MCP/Tunnel,
  idempotent remote write protocol và production fault matrix chưa hoàn tất.
- Git config hiện có `status.showUntrackedFiles=no`; vì vậy các file Recovery mới
  phải được kiểm tra bằng `git status --short --untracked-files=all` và đưa rõ vào
  staging/commit khi wave được accept. Không dùng status mặc định làm bằng chứng
  rằng worktree không có untracked implementation.
- Chưa commit, push, deploy hoặc restart hệ thống chỉ vì tài liệu này.

Tài liệu này nên được dùng làm **architecture contract + execution roadmap** cho các implementation wave tiếp theo.
