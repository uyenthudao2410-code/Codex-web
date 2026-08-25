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
                                               +--> Electron UI recovery watchdog
                                               +--> bounded watchdog
```

Recovery Host không mở LAN endpoint. IPC bind `127.0.0.1` trên cổng ephemeral,
được xác thực bằng token ngẫu nhiên trong descriptor có ACL best-effort. Các
route IPC dùng action allowlist và bounded JSON request/response; không có
arbitrary shell, executable, PID hoặc environment input. Per-action typed schema
được enforce cho preflight, activation, operation status và UI registration.

> **Compatibility note for Coding Tools MCP 1.0:** the desktop display and package
> names were renamed from the historical upstream identity, but the existing
> `%APPDATA%\web-mcp-assistant` data root is intentionally retained. This keeps
> encrypted credentials, descriptors, Recovery Host state, and existing desktop
> connections available during the in-place upgrade.

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

Recovery Host mới là owner của recovery boundary cho Electron UI. Sau khi một UI
đã đăng ký instance/PID hợp lệ, watchdog 5 giây có thể mở lại UI bằng launcher argv
cố định nếu process đó biến mất ngoài ý muốn. Watchdog không tự mở UI khi host chỉ
chạy headless và chưa từng nhận registration trong host instance hiện tại. Mỗi lần
launch có registration grace/cooldown, giới hạn số lần trong cửa sổ thời gian và
circuit break để tránh crash loop.

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
- Nếu UI đã đăng ký rồi bị crash/kill ngoài ý muốn, Recovery Host giữ Coding và
  Recovery planes nguyên trạng rồi spawn lại duy nhất Electron UI bằng executable
  và argv nội bộ cố định.
- Thao tác operator quit gửi authenticated `client.suppress_ui_recovery` cho đúng
  UI instance trước khi thoát. Suppression được lưu trong user-data và sống qua
  Recovery Host replacement; registration UI hợp lệ kế tiếp sẽ xóa suppression.
- Development operators use `npm run dev`, `npm run dev:stop`, and
  `npm run dev:replace`. These commands bind every mutating signal to the exact
  `development` installation identity from the authenticated Recovery Host
  descriptor. They never scan by process name or accept an arbitrary PID.
- `dev:stop` persists watchdog suppression before dispatching an Electron
  single-instance stop signal containing the exact registered UI instance ID.
  The primary UI accepts that signal only when it matches its in-memory identity,
  then follows the ordinary graceful `quitUi` path. Coding MCP, Recovery Host,
  and Tunnel remain resident. The command refuses to claim `STOPPED` when the
  Recovery Host is initially unavailable. After signaling, success requires the
  exact current host to report the UI `MISSING` or the previously bound PID to be
  proven dead; transient host loss alone is not a successful postflight.
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

`recoveryHost.electron_ui_recovery` phản ánh watchdog riêng cho UI (`healthy`,
`waiting_for_registration`, `cooldown`, `suppressed`, `circuit_suppressed`, ...),
cùng bounded `pid`, `instance_id`, `started_at_unix_ms`, và `runtime_mode` để
local DEV lifecycle postflight có thể bind đúng process. Không có descriptor token
hoặc credential nào trong projection này. Trạng thái UI không được nhập vào Coding MCP/Tunnel. Controlled electron code activation
có ưu tiên hơn crash recovery; khi activation đang `accepted`, watchdog không spawn
UI thứ hai và chờ luồng activation/re-registration hoàn tất.

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

### Activation Closure Contract

Chuỗi authority bắt buộc là `ACCEPTED/CHECKPOINTED -> ACTIVATABLE -> component
postflight -> LIVE_CLOSED`. Mỗi request phải mang đúng năm field của accepted
checkpoint: `checkpoint_id`, `run_id`, `wave_id`, `proof_fingerprint` và
`git_head`. Giá trị được so exact; runtime không trim/lowercase hoặc tái dựng ID
không canonical để biến input thành authority. Cả source-checkpoint response,
prepare response và post-cancel verification phải bind đúng operation/checkpoint.

Component receipt dùng schema v2. Ngoài revision/health/instance/timestamp,
receipt chỉ hợp lệ sau khi fence đã được cancel/release và một verifier mới đọc
canonical lifecycle snapshot qua SQLite Backup API, immutable + query-only,
`integrity_check=["ok"]`, không có foreign-key row, và có physical/logical SHA-256
hợp lệ. Toàn bộ blocking count, unexplained active RUN và unbound live residue
phải bằng 0; cờ `clean=true` riêng lẻ không đủ. Quy tắc này cũng áp dụng khi
checkpoint không có component cần restart.

Closure cuối còn yêu cầu component running/disk revision khớp, Runtime + Tunnel
fully ready và connector contract current. `UNCHANGED_ACKNOWLEDGED` không cần tạo
rediscovery giả khi current SHA đúng bằng acknowledged SHA và refresh flag là
false. Khi SHA thay đổi thật, target process phải thực hiện `tools/list` hoặc
`server/discover`, sau đó mới được acknowledgement qua Recovery Host; một
`tools/call` thông thường không thay thế discovery. `LIVE_CLOSED` chỉ là local
runtime closure; projection luôn ghi `release_state=NOT_RELEASED` và
`production_state=NOT_CLAIMED`.

For the ordinary development UI path, `npm run dev` automates only that supported
Electron component flow: `CURRENT` is focused, `STALE` goes through
`code.activation_preflight` plus `code.activate_update`, and `MISSING` is launched.
The `STALE` path must bind the exact `source_checkpoint` identity from
`hostStatus.auto_activation.closure_input`; it refuses when source acceptance,
accepted-receipt completeness, activation eligibility, affected-component
validity, or `electron_ui` ownership is absent. Prepare does not infer authority
from component postflight receipts.
It then re-reads Recovery Host status and reports PID, instance, runtime mode,
running revision, and disk revision. `npm run dev:replace` deliberately activates
a stale handler first, suppresses recovery, gracefully stops that exact instance,
launches once, and requires a new instance with matching revisions. A different
checkout/installation is a typed refusal, not an implicit takeover.

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

Exact worktree identity ép Git trả toàn bộ untracked paths, loại `.coding-tools`
không phân biệt casing trên Windows, không đưa bytes của symlink/reparse target
ngoài workspace vào digest, và fail closed nếu bounded status bị truncate. Python
acceptance và Electron verifier phải tạo cùng fingerprint trên cùng snapshot;
không được reuse proof khi hai phía lệch hoặc source tiếp tục đổi.

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

Lane `npm run test:recovery:packaged` build `dist/win-unpacked` từ đúng source
hiện tại rồi chạy executable đóng gói bằng argv `--recovery-host` trong Electron
user-data root tạm. Lane này kiểm tra resource đóng gói, device identity,
`independent_mcp_tunnel_v1`, Recovery MCP thật trên cổng tạm, packaged Recovery
Supervisor healthy ping, live-owner fail-closed và executable-hash fail-closed.
Nó không cài Scheduled Task, không sửa production AppData và xác nhận descriptor
Recovery production giữ nguyên trước/sau cleanup.

Các boundary còn cần chứng minh theo từng release/thay đổi là installed Windows
logon/session behavior khi release yêu cầu, các production-only fault scenario
không an toàn để giả lập trong isolation, cấu hình tunnel thứ hai khi môi trường
yêu cầu remote recovery, và live controlled activation khi component đang chạy
cần nạp source revision mới.
Remote recovery exposure rộng hơn break-glass surface hiện tại vẫn là future
scope nếu có nhu cầu. Source implementation chưa có nghĩa là process đang sống đã
load code mới; activation thực tế vẫn phải được chứng minh sau gate kiểm thử.

Rollback không cần migrate persisted state: tắt login item Recovery Host, dừng
process host thuộc instance hiện tại, rồi chạy bản build trước đó. Không xóa
`runtime-state.json`, settings, secrets hoặc orchestration ledger trong rollback.
