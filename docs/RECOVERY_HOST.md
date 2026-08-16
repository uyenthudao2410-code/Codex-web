# Recovery Host

Recovery Host là control-plane headless chạy trong cùng Windows user session với
ứng dụng. Electron UI chỉ giữ cửa sổ, cấu hình và IPC client; lifecycle của
Coding Tools MCP, OpenAI Tunnel, local Execution Hub gateway và watchdog thuộc
Recovery Host.

## Runtime topology

```text
Electron UI --authenticated loopback IPC--> Recovery Host
                                               |
                                               +--> RuntimeOrchestrator
                                               +--> Coding MCP/Tunnel
                                               +--> Execution Hub gateway
                                               +--> bounded watchdog
```

Recovery Host không mở LAN endpoint. IPC bind `127.0.0.1` trên cổng ephemeral,
được xác thực bằng token ngẫu nhiên trong descriptor có ACL best-effort. Các
route IPC dùng action allowlist và bounded JSON request/response; không có
arbitrary shell, executable, PID hoặc environment input. Per-action typed schema
được enforce cho preflight, activation, operation status và UI registration.

## Startup

- Mở ứng dụng bình thường: UI kiểm tra descriptor rồi khởi động một Recovery
  Host nếu chưa có host healthy.
- `startWithWindows`: Windows login item được cấu hình với `--recovery-host`,
  nên host có thể khởi động trước UI và giữ runtime resident.
- Chạy trực tiếp trong bản development: `electron . --recovery-host`.

Descriptor runtime nằm tại `%APPDATA%\web-mcp-assistant\recovery-host.json`.
Execution Hub descriptor vẫn nằm tại
`%APPDATA%\web-mcp-assistant\execution-hub-proxy.json`, nhưng ownership được
ghi là `recovery-host` thay vì `electron`.

## Safety boundaries

- Single-owner lock ngăn hai Recovery Host cùng quản lý runtime.
- Controlled activation fail-closed khi Coding MCP còn tool call, command,
  background operation, managed process, active agent lane hoặc orchestration
  khác `ACCEPTING`. `ACCEPTING` chỉ được giữ qua restart khi request xác nhận rõ.
- Secret file vẫn dùng Electron `safeStorage` trong cùng user context. Không
  đổi credential model hoặc chuyển sang LocalSystem/Windows SCM ở wave này.
- Log và IPC response có giới hạn kích thước; token/bearer không được trả về
  trong status/log projection.

## Development code activation

Source file thay đổi không tự cập nhật process đang chạy. Recovery Host hiện
expose revision awareness theo component:

```json
{
  "running_revision": "sha256...",
  "disk_revision": "sha256...",
  "update_pending": false,
  "state": "current"
}
```

`electron-updater` hiện chỉ có trong dependency manifest; source không import
`autoUpdater`, không gọi check/download/install update và không có hot reload.
Vì vậy dependency đó không phải bằng chứng rằng development source hoặc bản app
đang chạy sẽ tự nhận code mới.

`recoveryHost.code_revision` phản ánh code Recovery Host đã load so với source
trên disk. `status.codeRevision.codingMcp` làm tương tự cho Coding MCP; revision
được ghi vào runtime state lúc MCP spawn. MCP cũ được tạo trước capability này
có trạng thái `unknown` cho tới lần controlled restart kế tiếp.

Electron UI đăng ký instance/PID/revision sau khi attach host và lặp lại cùng
heartbeat. PID chỉ dùng để xác minh registration còn sống, không bao giờ được
dùng làm remote kill target. `recoveryHost.electron_ui_revision` vì thế phản ánh
đúng UI revision đang chạy hoặc `unknown` khi chưa có registration.

Hash dùng manifest component cố định, giới hạn tối đa file/bytes và cache 30
giây. Nó không gọi Git, không đưa `.coding-tools` hoặc toàn repository vào
fingerprint, và không kích hoạt restart từ file watcher.

Activation RPC gồm `code.activation_preflight`, `code.activate_update`,
`code.activation_status` và `client.register_ui_revision`. Request chỉ nhận
component allowlist, operation ID, timestamps TTL tối đa 60 giây, expected disk
revision và cờ bảo toàn `ACCEPTING`; không nhận path, executable, argv, shell hoặc
PID để điều khiển process. Kết quả được lưu bounded/atomic tại
`recovery-actions.json`; replay cùng operation trả kết quả cũ, payload khác bị
từ chối `IDEMPOTENCY_CONFLICT`. Terminal result vẫn replay được sau khi request
TTL hết; request mới hoặc request hết hạn trong preflight không được mutate
process.

Coding MCP expose authenticated `__control/activation`. Prepare preflight kiểm
tra canonical ledger/integrity cùng active tool/command/background/managed
process/agent lane, rồi atomically dựng activation fence để chặn tool call mới.
Recovery Host restart riêng Coding MCP, giữ tunnel, và chỉ complete khi health
trả đúng workspace, process/server identity mới và expected code revision. Disk
revision được kiểm tra lại ngay trước stop và ngay trong spawn path; activation
failure sau khi dựng fence sẽ hủy fence, đồng thời process thay thế chưa verify
được sẽ bị dừng fail-closed.

Electron UI tự relaunch bằng launcher argv cố định sau khi host trả lệnh qua UI
registration; registration revision mới complete action. Recovery Host update
spawn host mới bằng argv nội bộ cố định, host cũ nhả IPC/gateway/owner lock nhưng
giữ Coding MCP/Tunnel, host mới acquire + verify revision rồi complete action.
Nếu host mới không healthy trong thời hạn, host cũ reacquire ownership và ghi
failure thay vì để control plane mất chủ.

Workflow là: sửa source, chạy test, xem `update_pending`, gọi explicit preflight
và `activate_update` đúng component, rồi đọc operation status cùng
`running_revision == disk_revision`. Không có watcher hoặc `restart-all`.

Lần chuyển đầu tiên từ Recovery Host/Coding MCP legacy chưa expose activation
RPC là một mixed-version bootstrap boundary. Process legacy không thể tự chứng
minh canonical preflight bằng protocol mới, nên không được tự fallback sang
kill/restart. Operator chỉ bootstrap trong maintenance window đã xác nhận
canonical runtime idle; sau khi host và MCP mới đã load, mọi activation tiếp
theo phải đi qua protocol controlled ở trên.

## Current scope and rollback

Wave hiện tại đã chuyển ownership local và UI client, đồng thời có focused
lock/IPC/lifecycle tests. Lane `npm run test:recovery:e2e` chạy Electron main
process thật trong data root tạm, kill client thứ nhất rồi xác nhận client thứ hai
attach lại cùng Recovery Host, process identity của Coding MCP/Tunnel stand-in và
gateway. Lane này chứng minh process boundary một cách deterministic; packaged
Windows/login acceptance và fault matrix với Coding MCP/Tunnel production vẫn
pending. Independent Recovery MCP/Tunnel, remote recovery exposure và production
fault matrix vẫn là các wave tiếp theo. Source implementation chưa có nghĩa là
process đang sống đã load code mới; activation thực tế vẫn phải được gọi rõ sau
khi gate kiểm thử pass.

Rollback không cần migrate persisted state: tắt login item Recovery Host, dừng
process host thuộc instance hiện tại, rồi chạy bản build trước đó. Không xóa
`runtime-state.json`, settings, secrets hoặc orchestration ledger trong rollback.
