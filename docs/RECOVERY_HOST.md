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

Trong `full_clean_activation`, Recovery Host cũng là owner của bước connector ACK
sau handoff. ACK chỉ được ghi khi tất cả component/projection gate khác đã pass và
một health observation duy nhất chứng minh discovery thuộc đúng
`activation_epoch_id`, `process_instance_id`, `server_instance_id` và tool-contract
SHA hiện tại. Vì vậy deferred restart từ `task_control` không phụ thuộc vào một
CLI worker còn sống để hoàn tất ACK, nhưng vẫn không thể dùng persisted SHA,
`tools/call` hoặc receipt của process cũ để mở admission.

Watchdog vẫn dùng `soft_recovery` theo component: Tunnel failure chỉ thay Tunnel;
MCP exit hoặc semantic hang sau ngưỡng defer chỉ thay exact owned MCP process và
giữ nguyên Tunnel PID. MCP replacement mang expected code revision qua spawn và
được dừng fail-closed nếu disk revision đổi trước postflight, thay vì âm thầm tải
source mới dưới activation epoch cũ.

Semantic watchdog không dùng `workspace_context` như một liveness probe. Trước
canary, nó lấy HTTP control-health trong cửa sổ tối đa 5 giây; nếu health tạm thời
không sẵn sàng, hoặc receipt báo snapshot/command đang bận, tick đó được skip và
failure streak được reset. Chỉ ba semantic canary failures liên tiếp, trong lúc
HTTP health xanh và runtime idle, mới đủ điều kiện soft-restart riêng Coding MCP.
Primary lifecycle watchdog vẫn là authority cho process/Tunnel liveness; vì vậy
tool call dài không bị biến thành semantic failure rồi tự cắt MCP đang phục vụ.

Electron UI heartbeat chỉ đọc projection supervision hoàn tất gần nhất qua
`runtime.lightweight_snapshot`; nó không chạy thêm MCP health, Tunnel CLI, Git,
`netstat` hoặc OS-identity probe song song với watchdog. Projection mang
`snapshotSource`, `snapshotObservedAtUnixMs`, `snapshotAgeMs`, `snapshotBusy`,
`telemetryAvailable` và `signalStale`; UI publisher giữ single-flight nên một
heartbeat chậm không tạo lượt poll chồng lên nhau. Khi chưa có projection hoặc
projection cũ hơn 30 giây, MCP/Coding Tunnel/Recovery Tunnel được trình bày là
`UNKNOWN/WARN` (vàng), không bị suy diễn thành `false`/đỏ. Màu đỏ chỉ dành cho
process/component đã xác nhận dừng/lỗi hoặc Recovery state deterministic
`blocked_*`; receipt cũ chỉ được giữ làm context và không được dùng để tuyên bố
fresh green hay mở activation admission.

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
- Development operators use `npm start` (full-system refresh), `npm run dev`,
  `npm run dev:stop`, and `npm run dev:replace`. These commands bind every
  mutating signal to the exact
  `development` installation identity from the authenticated Recovery Host
  descriptor. They never scan by process name or accept an arbitrary PID.
- `npm start` requests the explicit `full_clean_refresh` transaction. Recovery
  Host closes admission, captures the canonical ledger census, stops the exact
  owned child set, hands off to a new Recovery Host and starts fresh MCP,
  Tunnel, Recovery-plane and UI processes under one activation epoch. Durable
  ledger/history/configuration/identity files are retained. A missing census,
  foreign process or incomplete postflight remains `UPDATE_INCOMPLETE`; no
  process-name kill or false `fullyReady` result is allowed.
- The CLI process-refresh poll remains bounded at five minutes, while the
  durable refresh bootstrap/activation transaction is bounded at ten minutes.
  The second five-minute phase gives the real external ChatGPT connector time
  to contact the newly verified MCP after a cold replacement/canonical census;
  it is not a late-commit bypass. Every store mutation, READY commit and
  admission-open boundary still rejects the epoch at or after the exact expiry.
  A cold Recovery Host bootstrap may take up to 90 seconds (120 seconds
  maximum). These bounds do not extend component-scoped activation requests.
- After exact process replacement, `npm start` may report the truthful pending
  receipt `activation=VERIFYING admission=closed fully_ready=false
  connector=pending` while the external connector has not contacted the new MCP
  process yet. Recovery Host keeps the epoch closed and automatically re-enters
  final census after either an exact current-process `tools/list` /
  `server/discover` receipt or the activation-only compatibility bootstrap
  described below. While only that gate is pending, the supervisor refreshes
  its exact component projection with bounded live MCP/PID observations;
  lightweight UI status only consumes that completed projection and never starts
  a second heavy OS-identity/Tunnel census. The first
  cached-client `workspace_context` call can therefore return a retryable
  bootstrap envelope; after the watchdog commits the ACK and opens admission,
  the retry performs the real workspace read.
- A watchdog census may reuse the exact durable projection-rebuild receipt only
  while the epoch remains `VERIFYING`, admission remains `CLOSED`, the connector
  is the sole incomplete gate, and all recorded process, workspace, device,
  revision, UI, Recovery Plane, epoch and immutable-ledger gates still pass.
  Both the watchdog census and the final READY-commit census still re-read MCP,
  Tunnel, Recovery Plane, Electron UI, connector and activation identities. The
  reuse therefore removes duplicate multi-minute ledger reconstruction without
  treating a stale component observation as current readiness.
- Khi watchdog thu được census `pass=true`, census đó được persist ở
  `VERIFYING/CLOSED` trước khi `finalize()` chạy census độc lập. Nếu exact
  projection receipt hết TTL năm phút ngay tại ranh giới này, coordinator chỉ
  fresh-rebuild cặp preflight/health khi hai lỗi duy nhất là
  `PREFLIGHT_RECEIPT_STALE` và `HEALTH_RECEIPT_STALE`. Sai workspace, ledger,
  process/server identity, activation epoch hoặc receipt integrity vẫn fail-closed
  và không được phép đi qua fallback.
- The Electron UI launcher is intentionally the one visible child: Recovery
  Host, MCP, Tunnel and recovery-plane processes remain hidden, while the UI is
  started without the Windows `SW_HIDE` flag. The UI subscribes to
  `ready-to-show`, retries the bounded `show/focus` reveal if Windows reports
  it is still hidden, and registers its revision only after the window is
  actually visible. A live Electron PID without a visible window is therefore
  not a valid UI receipt and keeps the activation `UPDATE_INCOMPLETE`.
- If a Recovery Host starts while a resumable activation epoch has already
  expired, it terminalizes that epoch as `FAILED` with admission closed but
  keeps authenticated control-plane IPC available. This is a recoverable
  startup state: the next explicit `npm start` creates a new full-clean epoch;
  the host does not auto-start child runtimes or report a late successful
  bootstrap for the expired operation.
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
Mọi operator `restart`, accepted code/revision activation và controlled update
đều đi qua `full_clean_activation`: đóng admission, checkpoint durable state,
dừng Electron UI, Coding Tunnel, Coding MCP và Recovery MCP/Tunnel, handoff
Recovery Host sang process mới, rồi khởi động lại toàn bộ bằng cùng một
`activation_epoch_id`. Epoch chỉ được mở khi final census xác minh exact
workspace/device/revision/process identities, tunnel thật, UI, Recovery Plane
và connector receipt mới; nếu thiếu bất kỳ gate nào, trạng thái là
`UPDATE_INCOMPLETE` và admission vẫn đóng. Disk revision được kiểm tra lại ngay
trước stop và trong spawn path; activation failure sau khi dựng fence sẽ giữ
durable epoch ở `FAILED`/closed, đồng thời process thay thế chưa verify được sẽ
bị dừng fail-closed. Watchdog/auto-recovery vẫn dùng `soft_recovery` cho lỗi cục
bộ, nhưng revision-continuity guard chặn soft path nếu source trên disk đã đổi.

Nếu MCP đã dừng trước khi operator retry, Recovery Host không nhận một
`ledgerSnapshot` do caller tự cung cấp. Host chạy helper
`activation_ledger_census.py` độc lập với MCP; helper tạo một SQLite
Backup-API copy immutable/query-only, kiểm tra integrity/FK, active
background/managed/lane resources, unresolved acceptance, projection drift,
và runtime-state PID residue. Census được chụp lại lần hai ngay trước khi
epoch mới được tạo, đồng thời helper giữ application ledger gate ở chế độ
exclusive cho tới khi durable epoch-store create hoàn tất; khác `sha256`, `logical_sha256`, fingerprint, workspace
hoặc ledger path sẽ bị từ chối `ORCHESTRATION_STATE_UNCERTAIN` trước khi dừng
bất kỳ process nào. Nếu census không chứng minh quiescence thì epoch FAILED cũ
vẫn giữ nguyên và operator phải xử lý đúng lifecycle/acceptance authority;
không có đường tắt bằng cách xóa hoặc sửa ledger.

Electron UI tự relaunch bằng launcher argv cố định sau khi host trả lệnh qua UI
registration; registration revision mới complete action. Full-clean Recovery
Host update dừng Coding MCP/Tunnel và Recovery Plane trước khi host cũ nhả
IPC/gateway/owner lock; host mới được spawn bằng argv nội bộ cố định, acquire
ownership, load lại durable state và verify cùng epoch rồi mới complete action.
Nếu host mới không healthy trong thời hạn, host cũ reacquire ownership và ghi
failure thay vì để control plane mất chủ.

Workflow là: sửa source, chạy test, xem `update_pending`, gọi explicit preflight
và `activate_update`; request sẽ tạo full-clean epoch và trả operation status
`accepted/HANDOFF` cho tới khi Recovery Host replacement hoàn tất. Chỉ receipt
`READY` có `fully_ready=true`, `admission_open=true`, cùng
`running_revision == disk_revision` và connector ACK mới là activation hoàn tất.
Không có watcher tự restart; soft restart chỉ thuộc watchdog khi xử lý lỗi cục
bộ và không được nạp revision mới dưới epoch cũ.

`task_control(action="restart_runtime")` dùng cùng transaction này qua deferred
post-tool-call handoff. MCP kiểm tra idle, dựng activation fence và ghi một ticket
ngắn hạn bound exact workspace/process/server; `ticket_id` đồng thời là
`operation_id`. Signed census không được trừ active tool call đang khởi tạo restart:
trong khi count còn khác `0`, nó phải trả `RUNTIME_BUSY`, giữ nguyên journal/fence
và retry cùng operation. Chỉ sau khi tool response đã rời MCP boundary, Recovery Host xác minh lại exact
MCP instance, lấy source checkpoint duy nhất từ
`hostStatus.auto_activation.closure_input`, rồi gọi `FullCleanActivation.restart`.
Khi host claim ticket, nó rename sang journal `.processing` và chỉ xóa journal sau
khi durable epoch đã bind đúng operation hoặc fence được xác nhận hủy. Crash giữa
claim và epoch creation vì thế được resume ở lần supervise sau; lỗi
`RUNTIME_BUSY` giữ journal/fence để retry cùng operation, còn trạng thái đọc không
chắc chắn luôn giữ fail-closed.
Ticket không được mang hoặc suy diễn source authority. Authenticated GET preflight
phải forward đúng signed operation ID để nhận lại chính fence đã dựng; operation
khác vẫn bị `RUNTIME_BUSY`. Thiếu/stale/non-activatable checkpoint, identity lệch
hoặc ticket hết hạn đều fail closed trước process mutation. Public
`runtime.restart` cũng resolve checkpoint phía Recovery Host; nếu caller có gửi
checkpoint thì nó phải exact-match closure hiện hành.

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
fully ready và connector contract current. Exact `tools/list` SHA vẫn là audit
identity; persisted SHA một mình không phải process-freshness proof. Sau process
replacement hoặc full-clean epoch, connector freshness phải đi qua một trong hai
đường exact:

1. Target process nhận `tools/list` hoặc `server/discover`, tạo receipt bind đúng
   current contract SHA, process instance và server instance; trạng thái đổi từ
   `CHANGED_NEEDS_DISCOVERY` sang `CHANGED_DISCOVERED_NEEDS_ACK`, rồi Recovery
   Host ACK exact current SHA thành `CURRENT_ACKNOWLEDGED`.
2. Khi admission của activation đang đóng và current contract khai báo exact
   predecessor tương thích (hoặc SHA đã acknowledge chính là current SHA), cached
   ChatWeb connector được phép gọi duy nhất `workspace_context` qua no-workspace
   bootstrap. Đường này không resolve path, không đọc workspace/ledger, không chạy
   tool implementation và trả `completed=false`, `retryable=true`,
   `workspace_accessed=false`. Receipt được lưu riêng, bind `client_type=chatweb`,
   current contract/process/server/activation epoch/timestamp. Receipt exact đầu
   tiên của cùng boundary này là immutable; các retry tiếp theo, kể cả qua client
   identity mới, không được đổi timestamp sau khi Recovery Host đã ghi ACK. Recovery Host chỉ
   ACK khi mọi field exact và predecessor/boundary hợp lệ; trạng thái cuối là
   `CURRENT_COMPATIBLE_ACKNOWLEDGED`.

Compatibility bootstrap không ghi `connectorRediscovered=true`, không tạo
rediscovery timestamp và không được ghi thành ordinary successful tool contact.
Một `tools/call` bình thường sau khi admission mở vẫn không thay thế discovery.
Post-ACK của cả hai đường yêu cầu `acknowledged_sha256 == tool_contract_sha256`,
`connectorRefreshRequired == false`, không còn acknowledgement pending, và final
census phải bind lại đúng process/server/epoch trước khi mở admission. Trạng thái
legacy `COMPATIBLE_ACKNOWLEDGED` vẫn bị từ chối. `LIVE_CLOSED` chỉ là local runtime
closure; projection luôn ghi `release_state=NOT_RELEASED` và
`production_state=NOT_CLAIMED`.

Với MCP 2026 stateless, `task_context_id` vẫn là application-state handle ưu tiên.
Nếu connector wrapper không echo handle này, chỉ `task_control` với exact `run_id`
được phép khôi phục context đã persist cho một tập continuation hẹp: các thao tác
read-only inspection và `ack/accept/reject` có selector đầy đủ. Recovery chỉ hợp
lệ khi exact RUN map duy nhất tới một context trong đúng authorized workspace và
không có active controller thuộc logical/execution principal khác. Không có exact
RUN, mapping mơ hồ hoặc có foreign active controller thì hệ thống không merge
context hay transfer authority; request tiếp tục dùng context stateless mới và
các authority guard phía sau vẫn fail-closed.

C4/measurement không được nhập vào connector activation gate. Connector closure
có thể đóng trước trong khi C4 vẫn `HOLD_NATURAL_EVIDENCE`; không tạo synthetic
PRL/C4 event chỉ để hoàn tất activation.

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
