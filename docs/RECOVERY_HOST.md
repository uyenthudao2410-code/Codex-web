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

## Phase 3A independent Recovery Supervisor

`resources/recovery-supervisor/recovery-supervisor.ps1` là watchdog cùng Windows
user nhưng nằm ngoài process Recovery Host. `recovery:supervisor:install` copy
script + fixed manifest sang `%LOCALAPPDATA%\\WebMcpRecoverySupervisor` và đăng ký
Scheduled Task `WebMCP Recovery Supervisor` ở logon. Supervisor xác minh bounded
descriptor, exact owner PID và authenticated `recovery.ping` trên `127.0.0.1`.

Nếu descriptor hoặc lock owner còn sống nhưng IPC không trả lời, supervisor
fail-closed ở `blocked_live_owner` và không kill process. Chỉ khi cả hai owner đều
đã chết qua 4 mẫu liên tiếp, nó mới spawn argv cố định `--recovery-host`. Manifest
khóa app root, executable và SHA-256 executable; binary đổi thì yêu cầu reinstall.
Sau spawn có cooldown 20 giây; tối đa 4 lần trong 10 phút rồi suppress 5 phút.
Status secret-free nằm ở `%APPDATA%\\web-mcp-assistant\\recovery-supervisor-status.json`.

```text
npm run recovery:supervisor:install
npm run recovery:supervisor:status
npm run recovery:supervisor:uninstall
```

Supervisor không sở hữu Coding MCP/Tunnel. Nó chỉ chịu trách nhiệm bounded
resurrection của Recovery Host. **Phase 3B independent Recovery MCP/Tunnel đã có
implementation trong current worktree** và được Recovery Host supervise; Recovery
Tunnel phải có tunnel ID riêng, không reuse Coding Tunnel để tránh cùng failure
domain.

## Phase 3B independent Recovery MCP/Tunnel

Recovery Host supervise một break-glass data plane riêng: Python
`resources/recovery-mcp/recovery_mcp.py` trên `127.0.0.1:18767` và, khi được cấu
hình, Recovery Tunnel health trên `127.0.0.1:18083`. Hai process dùng state/log/PID
riêng và spawn `detached`, nên Recovery Host handoff/crash không kéo chúng chết.
Host mới adopt process đúng fingerprint hoặc replace đúng PID nếu code/settings đổi.

Recovery MCP không import Coding MCP và chỉ export `recovery_status` cùng
`repair_primary_runtime`. Repair bắt buộc `confirm=true` và chỉ forward fixed
authenticated RPC `health.repair` tới Recovery Host; không nhận shell, path, PID
hay RPC action tùy ý.

`recoveryTunnelId` mặc định rỗng. Khi chưa có tunnel resource thứ hai, local Recovery
MCP vẫn chạy nhưng Recovery Tunnel báo `not_configured`. `recoveryTunnelId` bị từ
chối nếu trùng `tunnelId`; hệ thống không reuse Coding Tunnel để giả lập independent
recovery. Khi có tunnel ID riêng, Recovery Tunnel dùng channel `recovery`, port và PID
riêng. Runtime API key có thể dùng chung credential, nhưng process/tunnel failure
domain vẫn tách biệt.

Operational status exposes `recovery_plane_mode=independent_mcp_tunnel_v1`; persisted
`recovery-plane-state.json` uses schema `version: 1`. These markers make it explicit
that Recovery MCP/Tunnel identity must not be folded back into primary runtime state.

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

Sau final acceptance, Recovery Host có accepted-code auto activation. Host không
watch source file: nó chỉ xét task current/history đã `CHECKPOINTED`, yêu cầu
checkpoint `accepted` trong canonical SQLite ledger, khớp exact final worktree
fingerprint, rồi chạy thêm `git status --untracked-files=all` để chặn concurrent
dirty source trong target component. Với checkpoint legacy được tạo khi Git ẩn
untracked, target source vẫn còn untracked sẽ bị từ chối vì bytes chưa được
fingerprint chứng minh; staged/tracked source không có giới hạn này. Khi các gate
đều đúng, Host gọi lại chính Safe Code Activation theo thứ tự
`recovery_host -> coding_mcp -> electron_ui`; busy/uncertain chỉ deferred, không
restart. Queue nằm trong user-data nên Recovery Host mới tiếp tục được sau
handoff và không cần ChatGPT gọi loopback IPC để kích hoạt mỗi lần.

Lần chuyển đầu tiên từ Recovery Host/Coding MCP legacy chưa expose activation
RPC là một mixed-version bootstrap boundary. Process legacy không thể tự chứng
minh canonical preflight bằng protocol mới, nên không được tự fallback sang
kill/restart. Operator chỉ bootstrap trong maintenance window đã xác nhận
canonical runtime idle; sau khi host và MCP mới đã load, mọi activation tiếp
theo phải đi qua protocol controlled ở trên.

## Current scope and rollback

Current worktree đã chuyển ownership local/UI client sang Recovery Host và đã có
independent Recovery MCP/Tunnel source implementation cùng focused
lock/IPC/lifecycle coverage. Lane `npm run test:recovery:e2e` chạy Electron main
process thật trong data root tạm, kill client thứ nhất rồi xác nhận client thứ hai
attach lại cùng Recovery Host, process identity của Coding MCP/Tunnel stand-in và
gateway.

Các boundary còn cần chứng minh theo từng thay đổi là packaged Windows/login
acceptance, production fault matrix, cấu hình tunnel thứ hai khi môi trường yêu
cầu remote recovery, và live controlled activation của exact source revision.
Remote recovery exposure rộng hơn break-glass surface hiện tại vẫn là future
scope nếu có nhu cầu. Source implementation chưa có nghĩa là process đang sống đã
load code mới; activation thực tế vẫn phải được chứng minh sau gate kiểm thử.

Rollback không cần migrate persisted state: tắt login item Recovery Host, dừng
process host thuộc instance hiện tại, rồi chạy bản build trước đó. Không xóa
`runtime-state.json`, settings, secrets hoặc orchestration ledger trong rollback.
