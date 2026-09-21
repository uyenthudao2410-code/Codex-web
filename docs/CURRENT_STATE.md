# Current Project State — Tools-Codex-web

> Bản tóm tắt điều hành cô đọng: [SHARED_ACCOUNT_WORKSPACE_STATUS.md](SHARED_ACCOUNT_WORKSPACE_STATUS.md).
> Runbook Windows exact: [WINDOWS_EXACT_VALIDATION_RUNBOOK.md](WINDOWS_EXACT_VALIDATION_RUNBOOK.md).
> Tài liệu này giữ chronology chi tiết của current state; khi cần quyết định
> triển khai, đọc bản tóm tắt trước rồi đối chiếu receipt ở đây.

> Đọc [kế hoạch điều hành hiện hành](TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md)
> trước: checkpoint mới nhất **21-09-2026, 21:42 +07** đã đối chiếu Linux,
> GitHub và Windows `DESKTOP-63643J4` ở cùng `main @
> dcb3fc492b22d1b04547f3eae1c595b4ee6e4ce0`. Exact Windows build đạt Node/Electron
> `922/922`, MCP `1160/1160`, packaged/installed smoke pass và cleanup pass.
> Runtime sau cleanup hiện không có Recovery Host (`state=MISSING`,
> `RECOVERY_DESCRIPTOR_STALE`),
> nên chưa chứng minh live workspace binding hay `LIVE_ACCEPTED`.

## Checkpoint Wave 44 — delivery receipt HEAD đã đồng bộ; package/runtime không đổi — 21-09-2026, 21:42 +07

Commit `dcb3fc492b22d1b04547f3eae1c595b4ee6e4ce0` chỉ cập nhật delivery receipt
`.coding-tools`; package-relevant source và installer không đổi. Linux/GitHub và
Windows `E:\DEV\Codex-web` đều đã ở HEAD này, worktree Windows sạch. Installer
candidate vẫn giữ SHA-256 `61fb7fa5785c3861fcd4c8371f54172894472c9a0b7d48854c5cb05126d7c14e`.

Runtime Windows vẫn `MISSING/RECOVERY_DESCRIPTOR_STALE`; preflight fail-closed
vì Recovery Host owner không sống. Mức proof không đổi và chưa được tạo
closure/epoch/binding/task.

## Checkpoint Wave 43 — GitHub/Windows exact source đồng bộ; live gate vẫn đóng — 21-09-2026, 21:35 +07

Linux `main`, GitHub `origin/main` và Windows `E:\DEV\Codex-web` đã cùng ở
`fa055951d912997d75c9de5d7d18ee42f72b3094`; worktree Windows sạch. Commit này
chỉ bổ sung tài liệu/evidence sau build `bb4522c`, nên installer `1.0.7` và
packaged proof hiện hành vẫn giữ hash
`61fb7fa5785c3861fcd4c8371f54172894472c9a0b7d48854c5cb05126d7c14e` và không
cần rebuild package cho riêng delta tài liệu.

Read-only Windows recheck trả `DEV_UI STATUS state=MISSING` với
`error_code=RECOVERY_DESCRIPTOR_STALE`; `full-clean-activation --preflight`
trả `RECOVERY_DESCRIPTOR_STALE` (Recovery Host owner không sống). Vì vậy mức
bằng chứng vẫn là `SOURCE_PRESENT + FOCUSED_TEST_PROOF + PACKAGED_PROOF`, chưa
`LIVE_ACCEPTED`. Không forge closure/epoch, không mở admission, binding/task
hay deploy; bước kế tiếp vẫn là owner desktop interactive tạo closure đủ năm
trường cho đúng HEAD rồi mới preflight/activation.

## Checkpoint Wave 41 — activation owner attempt stopped; central package drift — 21-09-2026, 20:05 +07

Đối chiếu mới nhất cho thấy Linux, GitHub và checkout Windows
`E:\DEV\Codex-web` đều ở `main @ 7f26754657c5a1e933dea000fb75a0624e72f152`;
Windows worktree sạch. Installer `1.0.7` hiện diện và UI packaged đã từng
chạy đúng installation; Recovery Host/MCP/UI process được quan sát với owner
identity khớp. Strict snapshot vẫn có `workspace=""`, `mcpRunning=false`,
`centralConnected=false`, `authorityReady=false`, `componentsReady=false`,
`fullyReady=false`, `updateIncomplete=true`, closure trống và connector
`UNAVAILABLE`.

Trong lúc kiểm tra, một activation epoch owner chuyển sang
`STOPPING`/`admission=CLOSED` nhưng không tạo replacement process; descriptor
hiện stale và không có Supervisor task. Đây là **activation incomplete**, không
phải `LIVE_ACCEPTED`; không sửa epoch hay forge closure. Scheduled Task cũ
`CodingTools-StageA-Deferred-Worker` trỏ tới file tạm đã mất được gỡ đúng mục
tiêu; profile `%APPDATA%\\web-mcp-assistant`, credential và workspace không bị
xoá.

Ubuntu `/healthz` vẫn `ok=true`, nhưng service đang nạp release cũ
`0843ece334e07dd29f03cbd4c67fa97fc885ea1c` với package fingerprint khác source
HEAD hiện tại; admission vẫn `recovery`, `oauth_principals=0` và còn một action
unquarantined. SSH quản trị Ubuntu bị từ chối, nên chưa thể đưa release
`7f267546` lên service. Mức bằng chứng giữ nguyên
`SOURCE_PRESENT + FOCUSED_TEST_PROOF + candidate PACKAGED_PROOF`.

Next action: owner mở app từ desktop interactive, tạo closure exact source đủ
năm trường cho đúng HEAD hiện tại; sau đó preflight/activation và strict
heartbeat. Cần quyền SSH hợp lệ để build/verify/deploy Control Plane release
đúng HEAD; không mở admission hoặc tạo binding/task trước hai gate này.

## Checkpoint Wave 42 — exact Windows rebuild/install passed; live gate remains closed — 21-09-2026, 21:25 +07

Từ checkout Windows exact `main@bb4522cdc5f011942cce89f98c415df930f3f359`,
`npm run dist` đã chạy trọn gate Node/Electron **922/922 PASS** và MCP
**1160/1160 PASS trong 2764,26s**. `verify-packaged-resources` PASS. NSIS
installer `1.0.7` mới có SHA-256
`61fb7fa5785c3861fcd4c8371f54172894472c9a0b7d48854c5cb05126d7c14e`; sau khi
cài, executable installed khớp unpacked artifact ở
`a57ced0d185472d5c5e234a1177bf13ca35f14d2661300fc80e92c6daa7ecbd2`.

Packaged recovery smoke PASS với 17 resources, 8 smart-v3 tools, Recovery/MCP
device identity, Supervisor health và live-owner/hash-mismatch fail-closed;
production descriptor/task không bị mutate. Build đã tạo lại icon tạm trên
Windows nhưng hai file source icon đã được trả về đúng HEAD; Windows worktree
vẫn sạch. Đây là **exact packaged/installed proof**, không phải live acceptance:
app không được tự mở, activation epoch cũ vẫn `STOPPING/CLOSED`, chưa có
workspace/connector/central authority và chưa có binding/task.

Control Plane release exact HEAD đã build/verify cục bộ (schema 24, package
fingerprint `sha256:52889093c453e4b5fbbf82ddb593fb150ebe73e8d32a307d04cae81b59af3bc6`,
archive SHA-256 `b97e511007298dcf2df0a5e58cbbcf41d17bab5a5e8f4920db32fcd1a479d876`)
nhưng chưa deploy do SSH Ubuntu bị từ chối. Live Ubuntu vẫn release cũ,
admission `recovery`; không mở admission hoặc tạo binding/task.

## Checkpoint Wave 39 — exact source/build đã đồng bộ, live activation còn mở — 21-09-2026, 19:02 +07

Checkout Windows `E:\DEV\Codex-web` sạch ở đúng `abc1a63`; `npm ci`, NSIS
build, packaged smoke và installed smoke đều pass. Artifact local là
`dist\coding-tools-mcp-setup-1.0.7.exe`, SHA-256
`dcf1f5535eacb3e5c66d3a246503bec5dbcf949833b6e476b83576574a68351b`.

Đây là bằng chứng candidate `PACKAGED_PROOF`, không phải `LIVE_ACCEPTED`:
installed smoke đã uninstall để không giữ profile giả; `dev-ui status` trả
`MISSING/ENOENT` và full-clean preflight không có `recovery-host.json`. Không
được forge checkpoint hoặc suy ra readiness từ artifact. Gate tiếp theo là
owner acceptance exact source, full-clean activation được hỗ trợ, rồi strict
heartbeat/enrollment/workspace binding/task và T01–T16.

## Checkpoint Wave 40 — installed artifact đã có, chưa có GUI/runtime live — 21-09-2026, 19:31 +07

NSIS exact `1.0.7` hiện đã cài per-user tại
`C:\Users\Admin\AppData\Local\Programs\Coding Tools MCP`; registry và hash
executable installed khớp unpacked artifact. SSH launch (có và không có TTY)
không tạo process Electron/Recovery Host, không tạo
`%APPDATA%\web-mcp-assistant\recovery-host.json`, và không tạo Supervisor
Task. `dev-ui` vẫn `MISSING/ENOENT`; đây là installed proof chứ chưa phải
`LIVE_ACCEPTED`. Cần owner mở executable từ desktop `Admin`, tạo closure chính
thức và chạy preflight/activation theo runbook.

## Checkpoint Wave 36 — BLOCKED chờ Windows owner activation — 21-09-2026, 12:41 +07

Recheck `dev:status` vẫn `MISSING/RECOVERY_DESCRIPTOR_STALE`; Supervisor vẫn
`spawn_failed/SPAWN_FAILED` vì executable thiếu. Blocker exact-source/closure +
Supervisor đã lặp qua Waves 33–36; source lifecycle suite đã **133 pass, 0
fail, 1 skip**, nhưng chưa có current-process proof.

Trạng thái điều hành: **BLOCKED** chờ owner chạy acceptance ceremony và
supported full-clean activation trên exact Windows artifact/source, sau đó
Supervisor install nếu cần. Không forge closure, không sửa epoch thủ công.

## Checkpoint Wave 35 — source lifecycle regression pass, live runtime chưa có — 21-09-2026, 12:39 +07

Focused Node suite cho `dev-ui-lifecycle`, `full-clean-activation` và
`recovery-supervisor` đạt **133 pass, 0 fail, 1 skip** (Windows-only). Đây là
source proof rằng các đường status/preflight/activation tiếp tục fail-closed
đúng thiết kế.

Target Windows vẫn `RECOVERY_DESCRIPTOR_STALE`, Supervisor `SPAWN_FAILED`,
không có current-process strict proof. Mức proof chưa vượt candidate
`PACKAGED_PROOF`, chưa `LIVE_ACCEPTED`.

## Checkpoint Wave 34 — lifecycle CLI xác nhận runtime không thể tự hồi phục — 21-09-2026, 12:36 +07

`dev:status` trên checkout Windows và candidate đều trả
`state=MISSING`, `host=unavailable`, `error_code=RECOVERY_DESCRIPTOR_STALE`.
`full-clean-activation --preflight` trả exit 1 với cùng mã vì Recovery Host
owner đã chết. Supervisor Task còn `Running` nhưng status
`spawn_failed`/`SPAWN_FAILED`, executable bị thiếu.

Đây là bằng chứng CLI chính thức, nên không retry heartbeat, không sửa epoch,
không restart/install và không mở dispatch. Blocker vẫn là
exact-source/accepted-closure mismatch + stale Supervisor; proof chưa vượt
candidate `PACKAGED_PROOF` và chưa `LIVE_ACCEPTED`.

Next action: owner acceptance + supported full-clean activation trên exact
artifact/source, sau đó Supervisor install và strict runtime validation.

## Checkpoint Wave 33 — xác nhận kết nối test và stale activation — 21-09-2026, 12:29 +07

Tailscale/SSH tới `DESKTOP-63643J4` (`100.72.186.41`) thành công trong đợt
đọc-only. Checkout Windows là HEAD `3779096a9156bf2827e3164d09bcc1ef647a2c01`
với 23 thay đổi; candidate `1.0.7` không có `.git`. Accepted closure vẫn giữ
checkpoint `8d10f27638e2498cba80edf0bcbe77ce` và accepted HEAD
`cffd2acee24a4f38f4a83ddfea4c40f766de7a63`; dù `activation_eligible=true`,
`affected_components=[]`, `components_current=false`, `lifecycle_clean=false`.

Heartbeat chẩn đoán bounded trả `blocked/runtime_unavailable`,
`runtime_state=MISSING`, `fully_ready=unknown`,
`policy_state=expired_or_disabled`; nó chỉ làm mới route evidence/last-seen.
Epoch record `READY/OPEN` là dữ liệu durable cũ, không phải liveness: owner PID
Recovery Host không còn sống, runtime PID/revision stale và Supervisor báo
`spawn_failed`/`SPAWN_FAILED`. Không có mutation workspace/job/activation,
restart, install, dispatch hay model call trong wave này. Phân loại blocker là exact-source/closure mismatch
và Supervisor manifest stale; proof vẫn là candidate `PACKAGED_PROOF`, chưa
`LIVE_ACCEPTED`.

Next action: owner thực hiện acceptance ceremony + full-clean activation trên
exact artifact/source, khôi phục Supervisor theo installer hỗ trợ nếu cần, rồi
mới chạy strict runtime, binding/task và toolchain thật.

## Checkpoint Wave 32 — Tailscale live test và Recovery Host fail-closed — 21-09-2026, 12:10 +07

SSH/Tailscale tới `DESKTOP-63643J4` (`100.72.186.41`) thành công. Candidate
unpacked `1.0.7` được mở tạm trên data root thật; `recovery.ping` trả
`ok=true/ready=true` và process identity khớp. Strict runtime vẫn chưa sẵn
sàng: `mcp_ready=false`, `identity_current=false`,
`central_status_reason=LOCAL_EXECUTOR_NOT_READY`, `fully_ready=false`,
`update_incomplete=true`. `runtime.start` bị chặn đúng mã
`UPDATE_INCOMPLETE` vì cần full-clean activation epoch mới.

`runtime-heartbeat` exit 0 nhưng chỉ `degraded/packaged_runtime_unready`, không
poll/dequeue/receipt/model. Tiến trình candidate đã được dừng sau test; hiện
không còn `Coding Tools MCP` process, descriptor là stale metadata; Supervisor
ghi `OWNER_DEAD` rồi retry thành `SPAWN_FAILED` vì executable trong manifest
thiếu. Đây là proof kết nối/Recovery IPC, không phải live execution hay
`LIVE_ACCEPTED`.

## Checkpoint Wave 26 — kiểm tra Tailscale, heartbeat và runtime hiện hành — 21-09-2026, 11:27 +07

Tailscale/SSH tới `DESKTOP-63643J4` (`100.72.186.41`) thành công; đường ping
đi qua DERP HKG. Candidate chạy lại focused lifecycle **18/18**, same-account
OAuth **3/3**, two-client exec **1/1**, document-write **1/1** và standing patch
**1/1**. Cảnh báo teardown `WinError 10038` chỉ ở fixture HTTP, không làm fail
test và không chạm production.

Heartbeat bằng credential node trả `exit 0` với `last_seen_at_ms`; registry có
đúng một workspace opaque/generation và capability `{read,write,exec}`. Không
có process Electron/Node. `runtime-heartbeat` là `blocked` vì
`runtime_unavailable`/`MISSING`; connected-agent một iteration dừng
`MAX_ITERATIONS_REACHED`, không action/receipt nào được poll/gửi.

Đây là **candidate + connected reachability proof**, không phải OAuth live
binding/task, local file effect, ChatGPT UI two-client hay owner acceptance.
Không mở admission, reboot/restart/deploy, commit hoặc push trong wave này.

## Checkpoint Wave 27 — official packaged recovery smoke — 21-09-2026, 11:38 +07

Candidate Windows chạy `scripts/packaged-recovery-smoke.js` và trả **exit 0**.
Kết quả: executable/app.asar và **17 resources** hợp lệ, smart-v3 đủ 8 tool,
Recovery Host/MCP ready, device identity present, Supervisor healthy,
live-owner/hash-mismatch fail-closed pass, production descriptor stable và
Scheduled Task không bị thay đổi. User-data là TEMP cô lập, cleanup pass; không
còn process candidate sau smoke.

Đây là package proof tăng cường, không phải live production runtime, OAuth
binding/task hoặc owner acceptance; không có dispatch/deploy/restart trong wave.

## Checkpoint Wave 28 — central health và source capability recheck — 21-09-2026, 11:41 +07

Ubuntu `/healthz` read-only vẫn `ok=true`, SQLite `ok`, schema 19,
`admission=recovery`, package SHA actual/expected khớp, `oauth_principals=0`,
`node_workspaces=3`, unresolved **11**. Source targeted `unittest` chạy **7/7
PASS** (account/binding/writer 4/4; exec/document/standing patch 3/3).
Lệnh pytest local bị thiếu module `pytest` và được ghi nhận là environment gap;
candidate Windows focused pytest vẫn pass. Không có live dispatch hay owner
acceptance mới.

## Checkpoint Wave 29 — full Control Plane source discovery — 21-09-2026, 11:44 +07

Toàn bộ `control-plane/tests` đạt **298/298 PASS trong 96,772s** bằng stdlib
`unittest discover`. Không có source regression; stdout fixture chỉ bao gồm
lifecycle/unknown-state receipts expected và không tạo live action. Chưa có
thay đổi admission, deploy, restart hoặc owner acceptance.

## Checkpoint Wave 30 — installed NSIS smoke và isolation — 21-09-2026, 11:49 +07

Candidate Windows installed smoke trả **exit 0**: installer `1.0.7` install/
register, packaged Recovery smoke, uninstall và registration cleanup pass;
production descriptor/Scheduled Task definition stable. Đây là installed
candidate proof, chưa phải installed reboot/reconnect, live OAuth binding/task,
toolchain thật hoặc owner acceptance.

## Checkpoint Wave 31 — post-smoke read-only state — 21-09-2026, 11:51 +07

Post-check target có **0** process candidate. Descriptor production còn metadata
nhưng không có owner process sống, nên chỉ là stale/observation-only; không dùng
sự tồn tại của descriptor để suy ra runtime ready. Ubuntu health vẫn SQLite
`ok`, schema 19, `admission=recovery`, `oauth_principals=0`, `node_workspaces=3`,
unresolved 11. Không có live action hoặc production restart.

## Checkpoint Wave 24 — Tailscale candidate recheck và trạng thái runtime — 21-09-2026, 10:59 +07

SSH tới `DESKTOP-63643J4` (`100.72.186.41`) xác thực lại. Trên candidate
Windows `1.0.7`, focused lanes mới nhất đạt: secret/rotation/workspace
**18/18**, same-account OAuth **3/3**, two-client exec **1/1**,
document-write **1/1**, standing patch **1/1**. Không dùng credential thật.

Read-only probe phát hiện không có Electron/Recovery process; workspace registry
chưa tồn tại và `list-workspaces` trả rỗng; Supervisor `spawn_failed`, agent
`integrity_unproven`. Packaged policy inspection trên data root dev bị từ chối
đúng mã `CONTROL_PLANE_POLICY_PACKAGED_DATA_ROOT_FORBIDDEN`. Do đó máy đã
reachable để test nhưng chưa chứng minh installed runtime live đã bind workspace.

Mức bằng chứng giữ nguyên candidate `PACKAGED_PROOF`, chưa `LIVE_ACCEPTED`.
Không có Ubuntu mutation, live credential change, reboot/restart, deploy,
commit hoặc push. Bước tiếp theo phải có test account/data root được owner cho
phép để pair/enroll, register workspace và chạy connected-agent trước khi kiểm
reboot/reconnect/rotation/revoke và hai client ChatGPT thật.

## Checkpoint Wave 23 — packaged/installed smoke recheck — 21-09-2026, 10:48 +07

Candidate Windows packaged smoke pass: executable/app.asar, **17 resources**,
smart-v3 **8 tools**, Recovery/MCP/Supervisor healthy, owner/hash fail-closed
pass và không mutate Scheduled Task. Installed smoke installer `1.0.7`
install/register/smoke/uninstall pass, production descriptor/Scheduled Task
stable. Đây vẫn là candidate package proof; chưa có reboot/reconnect/live task.

## Checkpoint Wave 22 — structured toolchain parity candidate — 21-09-2026, 10:45 +07

Windows candidate chạy focused workflow parity **1/1 PASS trong 6,38s** cho
`git --version`, `npm run build`, `npm test`, `npm run deploy` trên cùng local
structured lane; HTTP→node journal/terminal receipt **1/1 PASS trong 4,30s**.
Đây là fixture deterministic, không phải build/test/deploy workspace thật.
Ubuntu vẫn `recovery`, OAuth principals `0`; không có live action hay deployment.

## Checkpoint Wave 21 — Windows target reachable và candidate recheck — 21-09-2026, 10:31 +07

Tailscale/SSH trực tiếp tới `DESKTOP-63643J4` (`100.72.186.41`) đã thành công.
Candidate cô lập `E:\DEV\Codex-web-candidate-502ffb8` version `1.0.7` có
`node_modules`, `dist\win-unpacked` và NSIS installer; không có `.git`, nên
không phải checkout phát hành và không chạm checkout chính.

Focused recheck không dùng credential thật đạt: secret/rotation/workspace
**18/18**, same-account OAuth/binding **3/3**, two-client exec **1/1**,
document-write **1/1**, standing patch **1/1**. Ubuntu `/healthz` read-only
trả `ok=true`, schema 19, SQLite `ok`, `admission=recovery`, counts
`3 nodes / 4 enrollments / 4 bindings / 24 contexts / 18 requests / 18 actions /
13 receipts`, OAuth principals `0`, unresolved `11` (10 quarantined, 1
unquarantined), package SHA khớp expected.
Windows candidate receipt trước đó đã đạt full MCP **1.160/1.160 PASS** trong
31m45s và Node/Electron **922/922 PASS**; bốn OAuth config mode POSIX còn fail
trên NTFS là fixture portability, không được nới ACL/secret policy.

Wave 21 thay thế kết luận “Windows target chưa reachable” của Wave 20, nhưng
không nâng `LIVE_ACCEPTED`: còn installed rotation/revoke, reboot/logon/
reconnect, hai client ChatGPT thật qua UI, Git/build/test/deploy workspace thật,
T01–T16, backup/restore, soak 24 giờ và owner acceptance. Không reconcile
unresolved action, mở admission, restart Ubuntu, deploy hoặc gọi provider trong
wave này.

## Snapshot repository hiện tại — 21-09-2026

Branch `codex/control-plane-quarantine`, HEAD
`502ffb8cf8b541ee74af30194aff2dce08c3b649`; worktree dirty có chủ ý với các
thay đổi source/test/docs/evidence của các wave hiện hành. Không có reset/clean,
commit, push, deploy hay restart service trong lượt cập nhật này.

Bằng chứng Linux/source lịch sử cần dùng khi đối chiếu: `npm run test:all` đã xanh với
Node/Electron **874 tests: 858 PASS, 16 SKIP, 0 FAIL** và MCP **1.160
collected: 1.153 PASS, 7 SKIP, 0 FAIL** trên bundled workspace Python 3.12.14 /
pytest 8.4.2; Control Plane lane riêng **295/295 PASS**. Linux resource
preflight vẫn là **427 resources + 9 adapters** và packaged/installed focused
**5/5 PASS**. Windows candidate đã có package/installer, installed smoke và
DPAPI/ACL proof; vẫn chưa chứng minh installed reboot/startup/reconnect/revoke/
rotation, hai ChatGPT client live, T01–T16, soak 24 giờ và owner acceptance.
Bằng chứng Windows mới nhất nằm ở Wave 21 và mục 13 bên dưới.

Wave 17 là receipt lịch sử với một dependency-only failure; Wave 18 đã rerun
trên interpreter có dev extra đúng chuẩn và không còn failure. Không sửa
runtime policy hoặc thêm `PYTHONPATH` vào production để làm xanh giả.
Receipt chạy trực tiếp trên worktree hiện tại là Control Plane unittest
**295/295 PASS** và Node/Electron `npm test` **858 PASS, 16 SKIP, 0 FAIL / 874
trong 43.317s**; source-root/secret checks đều PASS.

Wave 14 focused recheck sau đó đạt thêm **71/71 PASS** cho account/task/HTTP →
node, **146/146 PASS** cho store/node authority/credential/workspace và Node/
Electron **34 PASS, 1 SKIP, 0 FAIL** cho bridge/enrollment/recovery. Đây vẫn là
source/focused proof; không thay thế Windows exact/live gates.

Wave 15 full regression trước đó đạt Node/Electron **874 tests: 858 PASS, 16 SKIP,
0 FAIL trong 43,45s** và Control Plane **295/295 PASS trong 96,37s**; source-root
và repository-secret checks PASS. Đây vẫn là source/local proof trên Linux.

Kế hoạch chi tiết, reuse map và điều kiện nâng gate nằm ở
[TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md](TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md).

## Checkpoint Wave 20 — target Windows và evidence guard — 21-09-2026, 08:18 +07

Read-only SSH tới alias Windows đã biết `daochienthang` timeout sau 5 giây;
không có thao tác ghi/cài đặt/restart nào được thực hiện. Workspace Linux cũng
không có artifact `win-unpacked` hoặc installer Windows hiện hành.

`npm run check:coding-tools-history` đạt **PASS (4.873 files)** và repository
secret check đạt **PASS**. `.coding-tools` evidence vẫn được giữ nguyên; blocker
còn lại là Windows runner/target chưa reachable, không phải source failure.
Runbook exact để owner chạy khi target sẵn sàng nằm ở
[WINDOWS_EXACT_VALIDATION_RUNBOOK.md](WINDOWS_EXACT_VALIDATION_RUNBOOK.md).

## Checkpoint Wave 19 — Recovery/packaged gate phân loại theo nền tảng — 21-09-2026, 08:14 +07

- `npm run test:recovery:e2e`: **3 SKIP, 0 FAIL**; các test đều yêu cầu
  Windows `win32`.
- `npm run test:recovery:packaged`: Linux `dist:dir` dựng candidate thành
  công, nhưng smoke trả `{ok:true, skipped:true, reason:"windows_only"}`.

Đây là blocker môi trường Windows, không phải lỗi source. Linux unpacked
candidate không đóng `PACKAGED_PROOF`; cần chạy đúng lane trên Windows để xác
minh RunAsNode/Recovery/installer, DPAPI/ACL, startup/reconnect/rotation.

## Checkpoint Wave 18 — full local gate xanh — 21-09-2026, 08:06 +07

Receipt cuối cùng:

- `npm test`: **874 tests, 858 PASS, 16 SKIP, 0 FAIL**; source-root clean và
  repository-secret check PASS.
- `npm run test:mcp`: **1.160 collected, 1.153 PASS, 7 SKIP, 0 FAIL** trong
  **159,98s**; SDK/operator focused và workspace authorization đều nằm trong
  discovery xanh.
- Warnings còn lại là resource/cleanup warnings đã biết, không có failure.

Điều này xác nhận có thể tiếp tục tận dụng toàn bộ đường source hiện có:
`principal_id`/OAuth inventory, `binding_id` + task pin, enrollment và
credential riêng theo node, SecretStore/DPAPI, heartbeat/reconnect/rotation,
writer lease/generation fence, file-read/patch/document/structured-exec bridge,
Recovery Host/RuntimeOrchestrator, journal/idempotency/unknown-reconcile,
Coding Tools MCP, Supervisor và `.coding-tools` evidence. Không cần xây lại
credential theo máy, context-copy flow hay executor thứ hai trên Ubuntu.

Mức proof hiện tại là **full source/local regression xanh**, chưa phải
`PACKAGED_PROOF`/`LIVE_ACCEPTED`. Gate kế tiếp là Windows exact package và
two-client cùng principal; sau đó mới chạy toolchain thật, T01–T16, backup/
restore, soak 24 giờ và owner acceptance.

## Checkpoint Wave 17 — full MCP source-first rerun — 21-09-2026

Full MCP chạy với source repository đứng trước dependency runtime, proxy
variables unset và `PYTHONWARNINGS=error::ResourceWarning` đạt **1.160
collected: 1.152 PASS, 1 FAIL, 7 SKIP, 37 warnings trong 161.53s**.

SDK HTTP/operator timestamp **19/19 PASS** và multi-workspace/authorized
workspace **2/2 PASS** sau khi dùng đúng source và executable `python`. Failure
duy nhất là `ToolModeTests.test_continuous_check_terminalizes_internal_command_bookkeeping`:
child system Python không có pytest, trong khi runtime core cố ý không truyền
`PYTHONPATH`. Cùng logic chạy pass với `ShellEnvPolicy(inherit="all")` và
dependency-aware child, nên đây là **environment/dependency harness gap**, không
phải source authority bug.

Không sửa policy để làm xanh giả. Receipt trực tiếp vẫn là Control Plane
**295/295 PASS** và Node/Electron **858 PASS, 16 SKIP, 0 FAIL / 874**; Windows
exact/live, two-client, toolchain thật, T01–T16 và soak vẫn mở.

## Checkpoint Wave 16 — full MCP recheck và phân loại blocker (lịch sử) — 21-09-2026

Lần chạy full MCP của Wave 16 thu được **1.160 collected: 1.145 PASS, 8 FAIL,
7 SKIP, 35 warnings trong 160.43s**. Không ghi đây là full pass. Một official
SDK smoke báo `httpx.InvalidURL` (cần bỏ proxy khi retry); các matrix/
greenfield/build/continuous-check/workspace-session gọi child `python` trong khi
host chỉ có `python3` (cần shim tạm); operator-report cần xác minh lại
`24:00:00Z` trên đúng interpreter. Đây là phân loại harness/environment hoặc
chưa tái hiện source bug, không phải bằng chứng local authority đã hỏng.

Receipt trực tiếp vẫn xanh là Node/Electron **858 PASS, 16 SKIP, 0 FAIL / 874**
và Control Plane **295/295 PASS**. Vì Windows exact package/live, DPAPI/ACL,
reboot/reconnect, hai ChatGPT client thật, toolchain thật, T01–T16, backup/
restore, soak 24 giờ và owner acceptance còn mở, mức bằng chứng không đổi:
`SOURCE_PRESENT + FOCUSED_TEST_PROOF` + integrated local test proof.

## Checkpoint Wave 10 — refresh Linux packaged candidate — 21-09-2026

`npm run dist:dir` đã tạo lại `dist/linux-unpacked` thành công. Hai nhóm
packaged/installed recovery smoke đạt **3/3 PASS**; script packaged smoke trả
`windows_only` theo đúng thiết kế khi chạy trên Linux. Verifier trực tiếp xác
nhận **427 resource files exact-source**, **9 control-plane adapters** và
**463 entries sanitized**.
Focused HTTP recheck cho hai client cùng `principal_id` chọn nhiều binding và
handoff writer lease đạt **2/2 PASS trong 3.053s**.
HTTP → node → Recovery cho document-write và structured exec đạt **23/23 PASS
trong 29.601s** với `PYTHONWARNINGS=error::ResourceWarning`.
Standing-profile configuration, shared-task observation và cross-client
writer/exec guard đạt **3/3 PASS trong 3.046s**.
Standing patch không cần per-patch approval và document-create không đưa
content vào action payload đạt **2/2 PASS trong 0.083s**.

Đây chỉ là Linux resource/package preflight. RunAsNode fuse, Recovery Host,
DPAPI/ACL, reboot/reconnect, two-client live và owner acceptance vẫn chưa có
receipt; không nâng mức thành `PACKAGED_PROOF` hoặc `LIVE_ACCEPTED`.

## Checkpoint Wave 11 — documentation contract alignment — 21-09-2026

`control-plane/README.md` đã được đồng bộ với trusted-workspace contract:
read-only/context commands được đánh dấu legacy compatibility-only; flow chính
là OAuth account → opaque `binding_id` → standing local read/write/structured
exec → task pin và reconnect. Không có live service, quyền Windows hay credential
nào thay đổi trong wave tài liệu này.

## Checkpoint Wave 12 — T01–T16 source/live matrix — 21-09-2026

Ma trận T01–T16 đã được đưa vào [bản điều hành account/workspace](SHARED_ACCOUNT_WORKSPACE_STATUS.md), tách rõ `FOCUSED_TEST_PROOF`, `NOT_PROVEN` và `NOT_APPLICABLE_YET`. Không có T01–T16 nào được nâng thành live chỉ từ fixture; Windows exact, two-client, DPAPI/ACL và soak vẫn mở.

## Checkpoint Wave 9 — standing-policy Supervisor preflight — 21-09-2026

Đã audit và sửa một khoảng trống startup: Supervisor trước đây vẫn phụ thuộc
policy read-only pilot có TTL, trong khi packaged node đã chạy
`run-connected-agent` và các lane sản phẩm dùng policy standing riêng. Sau khi
read-only TTL hết hạn hoặc config credential đã chuyển sang DPAPI, connected
agent có thể không được spawn dù binding vẫn hợp lệ.

Supervisor nay preflight các policy standing v2 (`file-read`, `approved-patch`,
`exec`), cần ít nhất một lane enabled có identity server/device/endpoint đúng
và workspace generation còn current. Không có lane hợp lệ, registry stale/missing,
identity sai hoặc resource hash sai đều dừng fail-closed. Marker
`node_secret_dpapi` được chấp nhận mà Supervisor không giải mã hay in secret;
node agent vẫn là nơi kiểm tra credential và từng lane lần cuối.

Receipt wave: PowerShell helper class **1/1 PASS**, `test_store` **83/83 PASS**,
`node --test tests/recovery-supervisor.test.js` **1 PASS, 1 SKIP**, và
`git diff --check` PASS. Đây mới là source/focused proof; chưa có Windows exact
package/reboot/DPAPI/ACL/live reconnect, two-client acceptance hoặc soak.

Không commit, push, deploy hay restart service trong wave này. Việc tiếp theo là
đóng gói exact Windows candidate rồi chạy startup/reconnect và shared-account
acceptance theo kế hoạch P1–P6.

## Checkpoint Wave 7 — shared-account HTTP→node capability recheck — 21-09-2026

Đã chạy trực tiếp trên worktree hiện tại: nhóm OAuth/account, task pin/writer
handoff, exec Recovery và document-write HTTP→node đạt **57/57 PASS trong
45.280s**. Toàn bộ Control Plane đạt **294/294 PASS trong 94.877s** bằng Python
3.14.4 với `PYTHONWARNINGS=error::ResourceWarning`; không còn SQLite
`ResourceWarning`.

Đây là source/focused proof cho cùng `principal_id` chọn nhiều `binding_id`,
standing write/document/exec đi qua node local, và crash/lost-ACK không tạo
effect lần hai. Chưa có Windows packaged/live receipt, hai ChatGPT client thật,
Git/build/test/deploy trên artifact thật, T01–T16 hoặc soak 24 giờ.

## Checkpoint Wave 8 — standing local authority configuration proof — 21-09-2026

Đã thêm test cấu hình OAuth chứng minh profile standing write/exec chỉ bật khi
có file-read, write scope riêng và flag hợp lệ; thiếu scope, bật exec đơn độc
hoặc dùng giá trị không chuẩn đều bị từ chối. Focused configuration đạt **6/6
PASS**; full Control Plane đạt **295/295 PASS trong 95.319s** bằng Python
3.14.4 với `PYTHONWARNINGS=error::ResourceWarning`.

Flag này chưa được bật live và không phải bằng chứng DPAPI/ACL, package Windows,
reboot/reconnect hay hai ChatGPT client thật.

## Checkpoint Wave 4 — node revoke và public task admission — 21-09-2026

Đã thêm HTTP proof cho node bị revoke: inventory của cùng OAuth account vẫn giữ
`binding_id` nhưng báo `node_state=revoked`, `dispatch_state=node_revoked` và
`dispatch_blockers=["node_revoked"]`; `task_open` bị trả `CONFLICT`, không tạo
task mới và không failover. Response không lộ path hoặc node secret.

OAuth focused **28/28 PASS trong 14.266s**; toàn bộ Control Plane unittest
**292/292 PASS trong 92.197s** bằng Python 3.14.4 với
`PYTHONWARNINGS=error::ResourceWarning` (không còn warning SQLite). Đây là source/local proof;
Windows package/live và hai ChatGPT client thật vẫn chưa được nghiệm thu.

## Checkpoint Wave 5 — principal revoke và retired generation — 21-09-2026

OAuth HTTP proof mới xác nhận revoke `principal_id` trả `403 FORBIDDEN`, không
tạo link pending và không lộ target/path/secret. Retire workspace generation
giữ binding lịch sử trong inventory với `workspace_state=retired`, còn public
`task_open` trả `CONFLICT`, không retarget sang generation mới.

OAuth focused **30/30 PASS trong 15.812s**; toàn bộ Control Plane **294/294 PASS
trong 96.371s** với `PYTHONWARNINGS=error::ResourceWarning`. Đây vẫn là source
proof; Windows package/live và two-client acceptance còn mở.

## Checkpoint Wave 6 — Node/Electron regression recheck — 21-09-2026

`npm test` trên worktree hiện tại đạt **858 PASS, 16 SKIP, 0 FAIL / 874 trong
43.317s**; `check-source-root-clean` và `check-sensitive-tracked` đều PASS.
Các skip Windows vẫn là giới hạn môi trường, không phải `PACKAGED_PROOF`.

## Bản điều hành đã chốt — shared account, trusted workspace, 21-09-2026

Contract hiện hành là **một account ChatGPT/OAuth → một `principal_id` dùng chung
trên tất cả client/máy đăng nhập account đó → client chọn `binding_id` → task pin
device/endpoint/workspace/generation → Ubuntu auth/router/queue/receipt → node
local thực thi**. Ví dụ: máy A bind workspace W1 thành B1; máy B/C dùng cùng
account chỉ cần chọn B1 thì lệnh chạy tại A/W1. `binding_id` chỉ là selector,
không phải token hay context; task đã mở không được retarget. File, Git, process,
build/test/deploy và quyền OS nằm trên máy đã bind. Ubuntu không xin duyệt từng
context/lệnh trong standing local scope và không tự nâng quyền OS.

Đã tận dụng được: OAuth/account inventory và `ControlPlaneStore`; enrollment,
credential riêng, heartbeat/reconnect/rotation; standing local policy; node
journal/receipt; Recovery IPC/Host; RuntimeOrchestrator; các bridge file-read,
approved-patch, document-write, structured-exec; Coding Tools MCP; connected
agent; package/resource verifier và `.coding-tools` evidence.

Hiện trạng được phép công bố: **`SOURCE_PRESENT + FOCUSED_TEST_PROOF` +
integrated local test proof**. Không được gọi là `PACKAGED_PROOF`/`LIVE_ACCEPTED`:
Windows exact package/fuse/DPAPI/ACL, reboot/startup/reconnect/revoke/rotation,
Git/build/test/deploy thật, hai ChatGPT client live, T01–T16 và soak 24 giờ còn
chưa đóng. Kế hoạch gate và reuse map chuẩn nằm ở
[TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md](TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md).

## Checkpoint Wave 3 — account inventory giữ lifecycle state — 21-09-2026

`list_account_targets()` nay không làm mất binding khi generation bị retire hoặc
binding/node bị revoke. Inventory của đúng OAuth account giữ target opaque và
trả `binding_state`, `node_state`, `workspace_state`, `dispatch_state` cùng
`dispatch_blockers`; task/action admission vẫn fail-closed và không tự chuyển
sang máy khác. Không thêm path, secret, subject hay context vào projection.

Validation focused: `test_mcp_oauth.py` **27/27 PASS**, `test_store.py`
**83/83 PASS**, OAuth/task focused group **39/39 PASS trong 13.03s**; toàn bộ
Control Plane unittest **291/291 PASS trong 90.154s**.
Đây là source/focused proof; Windows exact package, DPAPI/ACL,
reboot/reconnect/revoke live và two-client ChatGPT thật vẫn chưa nghiệm thu.

Linux package preflight sau wave: `npm run dist:dir` PASS; exact resource
verifier **427 resources + 9 control-plane adapters**; packaged/installed
recovery/release focused tests **5/5 PASS**. Đây chưa phải Windows fuse,
Recovery Host, DPAPI/ACL hay installed-package proof.

## Checkpoint integrated source gate xanh trước Wave 16 — 21-09-2026

Đã xử lý bốn blocker của wave trước và chạy `npm run test:all` bằng Python
runtime product **3.12.14** + pytest **8.4.2**:

- Node/Electron: **874 tests; 858 PASS, 16 SKIP, 0 FAIL**;
- MCP Python: **1.160 collected; 1.153 PASS, 7 SKIP, 0 FAIL** trong **159.31s**;
- source-root và repository-secret checks: PASS;
- focused hash/timestamp/restart/continuous-check regression: **4/4 PASS**.

Các thay đổi giữ đúng ranh giới: hash test theo structured-`argv`, timestamp
reject `24:00:00Z`, restart POSIX fail-closed khi process còn sống mà owner
handle mất, Windows chỉ terminalize khi Job Object chứng minh tree đã chết,
ContextBudget fixture dùng `trusted` thay vì nới `safe` policy.

Mức hiện tại là **`SOURCE_PRESENT + FOCUSED_TEST_PROOF` + integrated local test
proof**; chưa có Windows package/fuse/DPAPI/ACL, reboot/reconnect/revoke/rotation,
hai ChatGPT client thật, T01–T16 hay owner acceptance.

**Next action:** exact Windows package/Recovery smoke → credential/startup gates
→ two-client same-account acceptance → T01–T16/soak 24h.

## Checkpoint direct Python MCP initial attempt (superseded) — 21-09-2026

Đã chạy trực tiếp suite MCP bằng Python **3.14.4** + pytest **8.4.2** và đầy đủ
dev dependencies trong runtime tạm; shim `python` chỉ phục vụ fixture legacy.
Kết quả: **1.160 collected; 1.149 PASS, 4 FAIL, 7 SKIP**. Bốn lỗi còn lại là:

- exact tool-contract hash trong test chưa cập nhật từ `d694…` sang contract
  structured-argv hiện tại `bc44…`;
- restart/reconcile làm mất command handle và chưa terminalize managed job bằng
  process identity/owner fence an toàn;
- parser report nhận nhầm `24:00:00Z` trên Python 3.14;
- fixture continuous-check không thấy pytest vì runtime không truyền
  `PYTHONPATH` tạm vào child (dependency/harness gap, không phải quyền local).

Đây là direct source test với dependency tạm, chưa phải `npm run test:mcp` trên
host (host `/usr/bin/python3` vẫn thiếu pytest), chưa phải package/live proof.
Do đó không ghi “full Python pass”; Node lane vẫn **874 tests: 858 PASS, 16 SKIP,
0 FAIL**, Control Plane unittest riêng **289/289 PASS**. Mức hiện tại vẫn là
`SOURCE_PRESENT + FOCUSED_TEST_PROOF`.

**Next action:** xử lý 4 blocker trên, chạy lại `npm run test:all` với interpreter
thật có dev extra, rồi chuyển sang Windows exact package/fuse/DPAPI/ACL,
reboot/reconnect/revoke/rotation và T01–T16.

## Checkpoint npm host dependency — 21-09-2026 (previous run)

`npm run test:all` đã hoàn tất lane Node/source: **874 tests; 858 PASS, 16 SKIP,
0 FAIL**, source-root và repository-secret checks PASS. Lane MCP dừng trung thực
ở `/usr/bin/python3: No module named pytest`. Host cũng không có `pip` hoặc
`ensurepip`, nên chưa thể cài `resources/coding-tools-mcp[dev]` tại đây. Không
ghi checkpoint này là full test pass; cần test host/pipeline có Python package
tooling rồi chạy lại toàn bộ lệnh.

## Tóm tắt điều hành theo xác nhận account dùng chung — 21-09-2026

Một workspace bind vào máy A tạo `binding_id=B1`. Mọi máy mở cùng tài khoản
ChatGPT/OAuth có thể chọn `B1` để điều khiển **A/W1**; máy đang mở ChatGPT chỉ
là controller, không phải execution host. Nếu có `B2`, client chọn ID theo từng
task. Task đã mở giữ `{device_id, endpoint_id, workspace_id,
workspace_generation}`; không có `active_workspace` toàn account, không copy
context/token/node-secret và không tự failover sang Ubuntu khi node offline.

Đã tận dụng OAuth/account inventory, `ControlPlaneStore` binding/task/writer
lease/generation, enrollment/credential riêng, heartbeat/reconnect/rotation,
standing local policy, node journal, Recovery IPC/Host, RuntimeOrchestrator,
Coding Tools MCP, connected-agent và resource/package verifier. Hiện có focused
proof cho same-account **3/3**, document E2E **3/3**, exec parity **12/12**,
Control Plane **289/289**, integrated MCP Python **1.153 PASS / 0 FAIL / 7 SKIP
trên 1.160**, Node/Electron **858 PASS / 16 SKIP / 0 FAIL trên 874**.
Đây vẫn là source/focused proof: Windows exact package, DPAPI/ACL, reboot,
reconnect/revoke/rotation, Git/build/test/deploy thật và hai ChatGPT client live
còn mở. Bước kế tiếp là chạy exact Windows package/fuse/Recovery smoke, rồi
DPAPI/ACL/startup/reconnect/revoke/rotation, two-client acceptance, T01–T16 và
soak 24 giờ.

## Checkpoint test-runner và regression — 21-09-2026, 04:38 +07

`npm run test:mcp` đã được đưa qua `scripts/run-python.js --module pytest` để
không phụ thuộc tên lệnh `python` trên Ubuntu; dev extra đã khai báo
`pytest>=8,<9`. Regression sau sửa: Python Control Plane **289/289 PASS**;
Node/Electron **874 tests: 858 PASS / 16 SKIP / 0 FAIL**; release-runner
**2/2 PASS**; source-root/secret/syntax/diff checks PASS. Python host hiện chưa
có `pytest`, nên `npm run test:mcp` vẫn chưa chạy được và không được tính là
PASS. Next action: cài dev extras, chạy `npm run test:all`, rồi exact Windows
package/fuse/DPAPI/live acceptance.

## Checkpoint Python 3.14 runtime hardening — 21-09-2026, 04:44 +07

Đã sửa hai lỗi source: fingerprint hỗ trợ `slice` trong `co_consts`; Landlock
standalone child resolve được package imports. Focused proof: Wave A **12/12**,
Landlock **3/3**, continuation identity/argv **2/2**, patch/proof-replan **2/2**,
`py_compile` PASS. Đây chưa phải package/live proof; full MCP pytest vẫn chờ
dev extra `pytest` trên host.

Continuity/reattach bổ sung **21/21 PASS** và `test_run_continuation` **50/50
PASS** sau sửa; đây vẫn là source/local proof, chưa phải pytest đầy đủ hay
Windows live proof.

Sandbox pytest **9.0.2** collection dừng ở **1158 items / 1 error** do thiếu
`mcp` và không khớp constraint `<9`; không tính là pass. Dev extra đầy đủ vẫn
cần trên host/pipeline trước `npm run test:all`.

## Checkpoint package/resource preflight — 21-09-2026, 04:46 +07

Sau runtime hardening, `npm run dist:dir` PASS; packaged/installed helper tests
**3/3 PASS**; packaged smoke trả `windows_only` đúng chủ đích. Đây vẫn là Linux
preflight, không phải Windows fuse/runtime/DPAPI/ACL hoặc `PACKAGED_PROOF`.

## Checkpoint W2 focused execution parity — 21-09-2026, 04:08 +07

Đã thêm focused proof rằng một task dùng cùng structured local lane cho Git,
build, test và deploy: `git --version`, `npm run build`, `npm test`,
`npm run deploy`. Bốn action dùng chung binding/writer lease, đi qua
Recovery→RuntimeOrchestrator→Coding Tools MCP và có terminal receipt riêng.

`test_oauth_exec_workflow_parity_uses_one_local_lane` cùng exec HTTP→node suite
đạt **12/12 PASS trong 22.262s**. Đây là `FOCUSED_TEST_PROOF` trên deterministic
fixture; chưa phải Windows package/live hoặc deploy thật. Local allowlist vẫn là
nguồn cấp quyền, Ubuntu không trở thành executor và không có shell/context/token
copy giữa máy.

Remaining: Windows packaged command proof, two-client same-account acceptance,
credential/reconnect/revoke live gates, rồi soak/release.

## Checkpoint packaged preflight — 21-09-2026

Linux packaging preflight đã đạt: `npm run dist:dir` tạo `dist/linux-unpacked`,
resource verifier xác nhận adapter/bridge hiện hành, packaged/installed helper
tests đạt **3/3 PASS**, còn nhóm Node build/package verification liên quan đạt
**12/12 PASS**. Runtime smoke chính thức trả
`{"ok":true,"skipped":true,"reason":"windows_only"}`. Lệnh Windows mặc định
không dùng được vì `build.electronDist=node_modules/electron/dist` là Linux;
override CLI tạm thời đã tạo PE `dist/win-unpacked/Coding Tools MCP.exe`, với
verifier độc lập **285 resource files + 9 adapter files**. `afterPack` vẫn fail
đúng chủ đích khi cần chạy `.exe` để xác minh RunAsNode fuse trên Linux; chưa có
fuse/runtime proof. Trạng thái vẫn là `SOURCE_PRESENT + FOCUSED_TEST_PROOF`,
chưa phải packaged/live. Next action: chạy exact build và recovery smoke trên
host Windows/pipeline Windows.

## Checkpoint same-account multi-binding focused proof — 21-09-2026

Focused HTTP group **3/3 PASS trong 3.102s** (gồm test mới
`test_same_account_selects_multiple_bindings_without_retargeting_existing_task`).
Hai token cùng `principal_id` thấy hai `binding_id`; task A/B giữ đúng target
riêng, và client B observe task A không thể retarget sang binding B. Projection
không chứa secret/path. Đây chưa phải nghiệm thu ChatGPT thật, Windows live hay
writer handoff trên Job packaged.

## Checkpoint sau W1 E2E + full regression — 21-09-2026, 03:55 +07

Đây là trạng thái hiện hành sau khi xử lý hai blocker W1, thêm lost-ACK proof
và chạy lại focused/full regression. Không tạo Job live, không đổi live state,
không commit/push/deploy/restart và không gọi provider trả phí.
Repository vẫn ở `codex/control-plane-quarantine@502ffb8cf8b541ee74af30194aff2dce08c3b649`;
worktree dirty có chủ ý.

Mô hình đã chốt: mọi client ChatGPT đăng nhập cùng account dùng chung OAuth
`principal_id`; mỗi task chọn `binding_id` của workspace/host và bị pin vào
`{device_id, endpoint_id, workspace_id, workspace_generation}`. Nếu nhiều máy
cùng account chọn cùng `binding_id`, tất cả lệnh đi tới cùng node đã bind; máy
chỉ mở ChatGPT là controller, không phải execution host. Không có
`active_workspace` toàn tài khoản và không copy token/context/node-secret.

| Khu vực | Đã tận dụng/đã có | Chưa đủ để gọi hoàn tất |
| --- | --- | --- |
| Account và định tuyến | OAuth principal/account inventory, `ControlPlaneStore`, binding/task/writer/generation | Hai client thật cùng principal trên Windows |
| Máy tin cậy | Enrollment một lần, credential riêng, heartbeat/reconnect/rotation, workspace registry và capability local | DPAPI/ACL/reboot/revoke/rotation trên package thật |
| Thực thi local | File-read standing, approved-patch, exec, Recovery IPC/Host, RuntimeOrchestrator, Coding Tools MCP | Full Git/build/test/deploy acceptance trên Windows package |
| Document create/convert | Central schema/admission; Electron bridge; CJS bridge; RecoveryHost; node poller/loop/CLI/lane; package allowlist | HTTP→Recovery E2E **3/3 PASS**, bridge **10/10 PASS**; Windows package/live còn mở |
| Ubuntu/model | Auth/router/queue/receipt; tool relay | Provider gateway chỉ khi server phải chủ động gọi model |

Validation hiện hành: Python **289/289 PASS trong 91.287s**; npm **873 tests:
857 PASS / 16 SKIP / 0 FAIL trong 43.611s**, kèm source-root và
repository-secret checks PASS. Focused Python document node-agent + HTTP E2E
**8/8 PASS**, document bridge/adapter **10/10 PASS**; `py_compile`,
`node --check`, `git diff --check` PASS. CJS request cap hiện là `512 KiB`, đủ
cho content cap `256 KiB` cộng envelope. Mức bằng chứng vẫn là
**`SOURCE_PRESENT + FOCUSED_TEST_PROOF`**, chưa phải packaged/live.

W1 đã chứng minh create/convert file-effect qua Recovery process fixture thật;
crash sau effect chuyển `unknown/reconcile_required`, còn central completed mất
ACK được replay mà không redelivery. Điều này chưa thay thế Windows packaged/
live evidence.

Kế hoạch wave, ma trận nghiệm thu và reuse map đầy đủ nằm ở
[TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md](TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md).

## Checkpoint baseline trước khi nối W1 — 21-09-2026, 03:18 +07

Repository đang ở `codex/control-plane-quarantine@502ffb8cf8b541ee74af30194aff2dce08c3b649`,
worktree dirty có chủ ý. Lượt xác minh không tạo Job, không đổi live state,
không commit/push/deploy/restart và không gọi provider trả phí.

| Phần | Đã có và có thể tận dụng | Còn thiếu để gọi là hoàn tất |
| --- | --- | --- |
| Account/workspace | OAuth `principal_id`, inventory, opaque `binding_id`, task pin exact device/endpoint/workspace/generation | Hai client ChatGPT thật trên Windows |
| Trusted node | Enrollment một lần, credential riêng, heartbeat/reconnect, rotation source path, workspace registry/capability | DPAPI/ACL/reboot/revoke/rotation trên package Windows thật |
| Local execution | Standing file-read, approved-patch, exec; local policy, journal, Recovery IPC/Host, RuntimeOrchestrator, Coding Tools MCP | Full Git/build/test/deploy acceptance trên node package |
| Document write | Central intent/schema, Electron bridge, RuntimeOrchestrator, node admission/journal helper | CJS bridge, RecoveryHost handler, node poller/CLI, Recovery-process file effect + fault proof |
| Ubuntu/model boundary | Auth/router/queue/receipt; MCP tool relay | Provider gateway chỉ khi Ubuntu phải chủ động gọi model |

Validation hiện hành: Python **279/279 PASS trong 84.520s**; npm **868 tests,
852 PASS / 16 SKIP / 0 FAIL trong 43.845s**; source-root, repository-secret,
`py_compile`, `node --check` và `git diff --check` đều đạt. Mức bằng chứng là
**`SOURCE_PRESENT + FOCUSED_TEST_PROOF`**. Central document create focused
**1/1 PASS** và bridge/runtime focused **14/14 PASS** chỉ chứng minh admission/
validator source; chưa chứng minh file được ghi qua Recovery process trên
Windows packaged/live.

Kế hoạch wave W0–W6, bảng “tận dụng gì”, W1 packet và ma trận T01–T16 nằm ở
[`TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md`](TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md).

## Xác minh mới nhất — 21-09-2026, 03:05 +07

Đợt này chạy lại kiểm tra trên working tree hiện tại, không tạo Job, không
thay đổi live state, không commit/push/deploy/restart và không gọi provider trả
phí. Branch/HEAD vẫn là `codex/control-plane-quarantine` /
`502ffb8cf8b541ee74af30194aff2dce08c3b649`; worktree dirty có chủ ý.

- `PYTHONPATH=control-plane python3 -m unittest discover -s control-plane/tests -v`:
  **279/279 PASS** trong **83.534s**.
- `npm test`: **868 tests; 852 PASS / 16 SKIP / 0 FAIL**; source-root và
  repository-secret checks PASS.
- `node --check`, `py_compile`, `git diff --check`: PASS.
- Central document create test **1/1 PASS**: intent có task/writer/generation,
  idempotency và digest-only contract, nhưng chưa phải file-effect trên node.

### Trạng thái sản phẩm cần dùng làm chuẩn

Một tài khoản ChatGPT/OAuth được xác minh thành `principal_id`; các client
cùng principal chọn `binding_id` để gửi việc tới đúng máy chứa workspace. Task
pin bất biến tới device/endpoint/workspace/generation. Ubuntu chỉ giữ auth,
queue và receipt; node giữ file, Git, process, build/test/deploy và quyền OS
local. Client mở ChatGPT không cần enroll nếu không chứa workspace. Không có
`active_workspace` toàn tài khoản và không copy context/token/node-secret.

### Đã có / còn mở

| Phần | Hiện trạng |
| --- | --- |
| OAuth, account inventory, binding, task idempotency, writer lease/generation | Có source và focused/full Python proof |
| Enrollment, credential riêng, heartbeat/reconnect, rotation source path | Có source/test; DPAPI/ACL Windows live còn mở |
| Standing file-read, approved-patch, exec | Có local policy/journal/receipt; patch và exec đã có Recovery-process fixture proof |
| `document_workflow` read | Có standing-policy proof |
| `doc_create`/`doc_convert` | Central schema/admission và Electron bridge source đã có; node lane/Recovery CJS/file-effect chưa có |
| Hai ChatGPT client thật, packaged Windows, reboot/revoke/rotation thật | Chưa nghiệm thu |
| Ubuntu gọi model/provider chủ động | Chưa triển khai; chỉ cần nếu product thật sự yêu cầu server-side inference |

Chi tiết wave, điều kiện pass/fail, ma trận T01–T16 và danh sách “tận dụng gì”
nằm trong [TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md](TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md).

## Recheck tài liệu 2026-09-21 02:50 +07

Lượt 02:50 chỉ recheck source/documentation và cập nhật kế hoạch theo semantics
account dùng chung; không chạy lại test, không tạo Job và không thay đổi live
state. Các số liệu validation dưới đây là bằng chứng gần nhất của checkpoint
02:40 +07 trên cùng working tree.

- Repository vẫn ở branch `codex/control-plane-quarantine`, HEAD
  `502ffb8cf8b541ee74af30194aff2dce08c3b649`, worktree dirty theo chủ ý; lượt
  này không commit, push, deploy, restart hay gọi provider trả phí.
- Sau khi thêm central document-write schema, đã sửa DDL migration và chạy lại:
  full Python control-plane **279/279 PASS trong 82.053s**; nhóm OAuth/task/
  exec/HTTP **85/85 PASS**; `npm test` **852 PASS / 16 SKIP / 0 FAIL** trên
  868 Node tests, kèm source-root và repository-secret checks PASS.
- `document_workflow` read đã có standing policy proof. `doc_create`/
  `doc_convert` hiện mới dừng ở central schema/admission sau feature flag:
  **chưa có node document-write poller, Recovery process bridge hoặc file-effect
  proof**, vì vậy chưa được xem là capability live.
- Mô hình dùng chung đã chốt: cùng OAuth-verified `principal_id` có thể chọn
  cùng `binding_id`; task pin exact device/endpoint/workspace/generation; node
  giữ credential và quyền OS local. Chi tiết wave/gate ở
  [`TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md`](TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md).

> **Status date:** 2026-09-21 02:50 +07 (documentation/source recheck; live receipts retain their own dates)
> **Desktop package:** `coding-tools-mcp 1.0.3`
> **Purpose:** canonical operational snapshot for the current repository. This is not a release note and does not imply that every source change has been activated, packaged, or released.
> **Git review:** 2026-09-21 02:50 +07, branch `codex/control-plane-quarantine`, HEAD `502ffb8cf8b541ee74af30194aff2dce08c3b649`; worktree remains intentionally dirty; the 22:21–02:18 +07 validation wave made no commit, push, deploy or restart. The 02:50 update records the shared-account/binding selector contract and the W1 document-write implementation packet only.

### Shared-account trusted workspace target — 2026-09-21

The current owner clarification and implementation plan are recorded in
[`TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md`](TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md).
One linked account may command a bound workspace from ChatGPT on different
computers. The issuing client is not the execution target and does not need
node enrollment unless it also hosts a workspace. ChatGPT owns the semantic
tool loop; Ubuntu authenticates and routes to the exact binding; the existing
local runtime retains filesystem, Job and execution authority. A separate
model gateway or server AI controller is not required for this primary path.
When that account has one active binding, clients may use its `binding_id` as
the session default; with multiple bindings, each task selects an ID. The
default is client/session state, never a global switch that retargets a running
task. All clients still resolve through the same verified principal and the
same account-scoped binding inventory.

The account inventory now also exposes a path-free connection observation for
each binding: `presence_state=unknown` before a valid heartbeat, `online` while
`last_seen_at_ms` is within the 60-second threshold, and `offline` after it is
stale, together with `heartbeat_age_ms`. This is visibility only; it does not
create a task/context/policy, change the selected target, grant execution, or
replace live reconnect/revocation proof.

### W1 implementation boundary — document create/convert

The central facade and schema are present, but they do not yet mean that a file
was written on the bound machine. The next implementation packet must add a
dedicated node `document_write` lane, a Recovery process bridge, strict source/
target/generation/allowlist/overwrite validation, local `document_workflow`
create/convert calls, and prepared/completed/rejected/unknown journal receipts.
The exact acceptance gate is a Recovery-process fixture plus HTTP→node status
proof where crash or lost ACK never invokes the document effect twice. Until
that gate passes, `doc_create` and `doc_convert` remain source-only central
capabilities and are not advertised as live write access.

### Shared-account clarification checkpoint — 2026-09-21 02:24 +07

The binding ID is the workspace/host selector. Every ChatGPT client signed into
the same OAuth-verified account (`principal_id`) may choose that ID and issue
work to the bound host. The client computer is not the executor unless it also
owns an enrolled workspace. A task remains pinned to
`{binding_id, device_id, endpoint_id, workspace_id, workspace_generation}`;
there is no account-wide `active_workspace` that retargets a running task.

The node credential remains device-specific and standing local policy remains
the execution gate. Same-account clients may observe or request work, but
writer lease/generation fencing serializes writes and prevents one controller
from silently overwriting another. If the selected binding is offline, revoked
or retired, the service reports that state; it does not silently move files to
Ubuntu or another machine. This is the product contract now recorded in
[`TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md`](TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md),
not a claim that two real ChatGPT clients have already passed live acceptance.

The packaged Supervisor source path now uses `run-connected-agent`. It emits a
heartbeat before polling and gates each file-read, artifact, approved-patch and
exec lane on the corresponding standing local policy and current workspace
generation. A missing policy is a disabled lane, not a reason to dequeue or
grant authority.

The central MCP facade now has a separate standing-write source path for
`agent_workflow.apply_patch`. In that profile the request omits
`permission_request_id` and is admitted only with the verified principal,
distinct OAuth write scope, `binding_id`/task target, current writer
lease/generation, exact path/preimage/patch digest, envelope and facade
contract. `mcp_standing_patch_intents` is durable and idempotent; the local node
still decides whether the standing workspace policy/OS checks admit the effect.
The latest HTTP→node approved-patch integration class is **5/5 PASS in
11.771s**, including the two Recovery-process cases; full Python discovery is
**278/278 PASS in 82.054s** and the Node approved-patch/Recovery bridge lane is
**12/12 PASS**. The earlier **3/3** class remains a superseded fixture
checkpoint. This is still source/fixture proof only: Windows packaged/live
policy and two real ChatGPT clients remain open, so the repository must not
claim approval-free patch/write is live or fully accepted.

### Latest source validation checkpoint — 2026-09-21 02:00 +07

Standing approved-patch đã chạy qua process fixture Recovery/Electron thật,
không còn chỉ mock bridge: `RecoveryIpcServer` → `RecoveryHost` →
`RuntimeOrchestrator.controlPlaneApprovedPatch` → Coding Tools MCP
`agent_workflow.apply_patch`.

- Crash sau khi local MCP đã ghi file nhưng trước khi bridge nhận kết quả: **1/1
  PASS**; node ghi `unknown`, central là `reconcile_required`, process restart
  không redeliver `apply_patch`.
- Central đã commit `completed` nhưng node mất ACK: **1/1 PASS**; poll sau
  replay cùng receipt, store idempotent và MCP chỉ nhận một `apply_patch`.
- Để đường thật chạy đúng, standing request giữ `authority_mode`; Recovery
  adapter chuyển đủ task/writer/run/wave correlation và postimage metadata.

Lớp HTTP→node approved-patch hiện **5/5 PASS** (3 fixture cũ + 2 process thật),
full Python control-plane discovery **278/278 PASS trong 82.054s**, Node
approved-patch/Recovery bridge **12/12 PASS**. Đây vẫn là
`SOURCE_PRESENT + FOCUSED_TEST_PROOF` trên Linux working tree; chưa phải
Windows packaged/live, hai ChatGPT client thật, full read/write/Git/build/test/
deploy hay soak.

Parity read mới nhất: `document_workflow` artifact read dùng file-read policy
standing (`authority_mode=standing`, `expires_at_ms=null`) với generation và
allowlist hiện hành. Focused test mới **1/1 PASS**, toàn bộ
`test_file_read_node_agent.py` **10/10 PASS**. Đây chỉ chứng minh node/source
document read; document create/convert và Recovery-process document bridge vẫn
đang mở.

### Previous source validation checkpoint — 2026-09-21 01:19 +07

The focused HTTP→node class was rerun after the stale-generation case was
added. It passed **3/3**; the stale local workspace policy was rejected before
the mutation bridge and the fixture file was not written a second time. The
unknown-effect case remains explicitly `reconcile_required` and is not retried.
The full Python control-plane discovery then passed **275/275** in **73.574s**;
one SQLite `ResourceWarning` remains as hygiene backlog without a test failure.
This does not change the live/package verdict: Windows DPAPI/ACL/startup/
reconnect/rotation, standing fault completeness, two real ChatGPT clients,
full read/write/Git/build/test/deploy, and the 24-hour soak remain open.

### Standing fault proof checkpoint — 2026-09-21 01:32 +07

The standing HTTP→node fixture now also covers a stale local preimage and a
completed-receipt ACK loss. A stale preimage settles as `rejected` before a
write; when the central receipt is committed but the response is lost, the
node journal retries the same receipt digest, the store returns an idempotent
replay, and the mutation bridge is not called a second time. The affected
HTTP class remains **3/3 PASS**; the node/store/task focused group is **105/105
PASS** and full Python discovery is **275/275 PASS in 74.546s**. SQLite
`ResourceWarning` messages remain hygiene warnings only.

This strengthens source/focused evidence but is not Windows packaged/live or
Recovery-process proof. Standing path-deny/terminal-unknown across the exact
Recovery boundary, Windows DPAPI/ACL/startup/reconnect/rotation, two real
ChatGPT clients, full read/write/Git/build/test/deploy and 24-hour soak remain
open.

### Standing path-deny and regression checkpoint — 2026-09-21 01:37 +07

The same standing HTTP→node fixture now rejects a valid exact-file envelope
whose relative path is outside the installed local allowlist; no bridge call or
new file occurs. The class remains **3/3 PASS**, the node/store/task group is
**105/105 PASS**, and full Python discovery is **275/275 PASS in 74.631s**.
`git diff --check` and updated-document whitespace checks pass. The remaining
unknown/duplicate-effect Recovery boundary and all Windows/live/multi-client/
read-write-exec/Git/build/test/deploy/soak gates remain open.

### Standing terminal-unknown checkpoint — 2026-09-21 01:40 +07

The standing HTTP→node fixture now turns a post-prepared bridge failure into
`unknown/reconcile_required`; `patch_status` exposes the uncertainty and a
later poll does not invoke the bridge again. Full Python discovery after this
case is **275/275 PASS in 73.941s**. This remains a mocked HTTP fixture, not a
Recovery process/package proof; duplicate-effect across every Recovery boundary,
Windows/live, two-client account control and final soak remain open.

### Standing-write source checkpoint — 2026-09-21 00:52 +07

The working tree now contains the central standing path required by the shared
account contract: facade profile `control-plane-oauth-standing-write-v1`,
schema-23 table `mcp_standing_patch_intents`, a distinct OAuth write scope,
immutable `{binding_id, task_id, workspace_generation}` lineage, writer-lease
generation, exact preimage/patch digest and idempotency replay. The node still
owns the effect: its standing local policy, path allowlist, preimage and OS
permissions must admit the action before any file write.

Focused proof `test_standing_write_queues_without_per_patch_permission_and_replays`
plus HTTP→node `test_oauth_standing_write_to_node_patch_to_verified_status` is
**2/2 PASS** and includes the `tools/list` capability marker, absence of
`permission_request_id`, same-action replay, writer conflict, local standing
policy admission and verified completed receipt. Full Python control-plane
discovery is **275/275 PASS**. No Windows packaged/live run or two-client
ChatGPT acceptance has been performed yet.

The new target is durable node enrollment and standing local permissions,
without manual context/token copying or Ubuntu per-command human approval
inside the configured local scope. It does not relax account authentication,
target/generation checks, local writer fences, OS permissions or explicit
deployment scope. Earlier planning requirements for short-lived read-only
pilot authority or mandatory server-owned inference are superseded as target
guidance, not erased as historical evidence.

Source review at `502ffb8cf8b541ee74af30194aff2dce08c3b649` plus the pre-existing
dirty worktree confirms reusable enrollment/credentials, account inventory,
bindings, pinned task sessions, queue/receipts, local runtime and Supervisor.
The current source also contains durable enrollment status/reconcile, keyed
`task_open` idempotency, schema-21 task writer leases/generation fences and
OAuth `task_control` for redacted observe/claim/release. The schema-21 wave now
propagates task/generation through action, approved-patch/exec bridge and
receipt; fixture migration and node admission expected-fields are now covered
by green local tests. G3-A/G3-B/G3-C/G3-D/G3-E/G3-F/G3-G/G3-H and G4-A/G4-B/G4-C/G4-D now wire `exec_run`,
`exec_poll` and `exec_stop` through the local policy, Recovery IPC/Host, descriptor-hiding
bridge, `RuntimeOrchestrator` and Coding Tools MCP, so the local MCP owns the
managed Job/RUN/WAVE/process lifecycle and returns a correlated receipt. The
G4-E HTTP→node fixture now exercises OAuth task/writer claim, node heartbeat,
central dispatch, standing policy admission, local exec journal, accepted then
terminal receipts, and verified MCP status/output without spawning a second
command on resume. G4-F now runs the Recovery IPC/Host and
`RuntimeOrchestrator.controlPlaneExec()` inside a separate Node process fixture:
`exec_run → exec_poll → exec_stop` reaches the deterministic MCP peer, and stop
ACK is emitted only after terminal evidence. The terminal control-result path was
fixed to preserve `output_bytes`, and `store.py` now treats `stopped` as a
terminal receipt so the settled action is not rejected with HTTP 400.
G4-G then found and fixed a journal boundary: the complete `running` projection
(`request`, policy digest, result and handle) is now persisted before the
central receipt request. A fault fixture that commits `accepted` but drops the
node's ACK replays that exact receipt on the next poll and reaches terminal
status without a second `exec_run`.
G4-H adds the complementary MCP disconnect case: a socket close immediately
after `exec_run` produces one `unknown/reconcile_required` receipt and no retry
effect on the next poll.
G4-I covers the terminal side: after central commits `completed` but the node
loses the receipt ACK, the next poll replays the terminal payload without
relaying `exec_run` or `exec_poll`.
G4-J now covers the Recovery-process side: the fixture exits after the MCP has
recorded `exec_run`, every post-`prepared` bridge error becomes one
`unknown/reconcile_required` receipt, and a restarted process/data root does not
receive a second `exec_run`.
G4-K partial now covers a running Job resumed through a newly started Recovery
process (`exec_poll` settles the same handle), a terminal local result lost
before bridge ACK (`unknown/reconcile_required`, no redelivery), a central
terminal receipt ACK loss across Recovery restart, a stop accepted by local MCP
but left pending until the restarted process polls the same handle, and writer
lease handoff held until a real local Job reaches terminal receipt.
exec, file-read and approved-patch policy sources are now schema 2 with
`authority_mode=standing` and `expires_at_ms=null`; action TTL remains only to
prevent queue replay, while policy v1 remains accepted as `expiring_legacy` and
the compact read-only/context pilot remains expiring. Schema-23 central
standing patch intents now keep the same binding/task/writer fence and do not
create a per-patch owner-review record. Node resume reads a
persisted `running` handle before accepting a new action and stop is
acknowledged only after terminal evidence. The G3-G replacement flow keeps
`workspace_id`, retires the old generation at Ubuntu, disables old local
policies, registers a new generation only after a valid receipt, and uses a
secret-free phase journal to resume after lost ACK/crash. Schema-22 now adds
node-mediated credential rotation with durable prepare/activate/ack state and
dual-auth handoff; account inventory presence is now source/focused proof, while
Windows live/packaged rotation, live heartbeat/reconnect, standing fault/
duplicate-effect proof, remaining write-path parity and live multi-chat writer
continuity remain completion work. The
local `SecretStore` now has a versioned envelope, legacy migration,
temporary+fsync writes, owner-only mode, backup fallback and fail-closed
corruption/unavailable-encryption handling. Its focused test is **5/5 PASS**;
this is fake-encryption/Linux source proof only. The node-agent now has a
Windows DPAPI active/pending envelope source path, in-memory unwrapping, legacy
plaintext migration and fail-closed protection fallback; its focused test is
**8/8 PASS**. Rotation store/agent is **5/5 PASS** with HTTP boundary **1/1**.
Those Windows API calls are mocked in source tests, so Windows `safeStorage`/
DPAPI live integration, ACLs, packaged migration and exact-package rotation
crash/lost-ACK proof are still open.
`_run_bounded_exec` is retained only for compatibility/focused tests; the new
poller path uses the Recovery/Electron bridge, but no packaged/live proof exists
yet. The Electron enrollment boundary now exposes a local capability picker:
`read` is mandatory, while the owner may select `write` and `exec`; the selected
shape is validated and passed to the packaged node-agent. This removes the
previous UI hardcode that made every registered root read-only, but it does not
itself install standing policies, create a binding, or prove remote execution.
The remaining assignment/policy compatibility UI and live expiring-context
requirements are still not the final trusted-workspace contract.

The latest recorded 19–20 September receipts report Ubuntu revision `528035f`
at schema 19 and real node dispatch, but not completed Windows execution:
the final activation receipt remains `awaiting/pending`. Historical Windows
pytest proof and an unpacked app launch do not establish a successful NSIS
release, current strict readiness or live multi-client acceptance. Focused
source tests were rerun through 21-09-2026: the pre-schema-21 run was **223/223
PASS** with Node **24/24 PASS**; the previous full checkpoint was **275/275
PASS** in Python control-plane discovery and **868 Node tests: 852 PASS, 16
SKIP, 0 FAIL**. The latest standing-Recovery checkpoint supersedes that Python
checkpoint with **278/278 PASS in 82.054s** and the approved-patch/Recovery
bridge lane with **12/12 PASS**; the Node full-suite count remains **868: 852
PASS, 16 SKIP, 0 FAIL**. The earlier Python discovery completed at about
01:08 +07 in roughly 74.130s; the Node command completed at about 23:43 +07, after
adding the Electron owner-rotation suite.
Workspace replacement is **3/3 PASS**, enrollment/manager/rotation is **25/25
PASS**, and OAuth account lineage, writer handoff, exec guard and presence are
covered (**4/4 focused lanes**, full OAuth class **24/24 PASS**; the presence
test is `unknown → online → offline`); connected-agent worker tests are **3/3
PASS**; terminal writer fencing is **1/1 focused PASS** (MCP exec class **8/8
PASS**). G4-F→G4-K HTTP→Recovery process
exec/stop/lost-ACK/disconnect/terminal-ACK/crash-restart/running-restart/
terminal-crash/terminal-ACK-restart/stop-pending-restart/writer-job-handoff E2E is **11/11 PASS**;
the directly affected `test_store` and
`test_mcp_exec` reruns are **80/80** and **8/8 PASS**. G4-G lost-ACK replay
E2E adds **1/1 PASS**; `test_exec_node_agent` is **21/21 PASS** and the
combined `test_mcp_faults` + `test_store` lane is **85/85 PASS**. G4-H
MCP-disconnect reconcile is **1/1 PASS** and G4-I terminal-ACK replay is
**1/1 PASS**.
The subsequent G3-prep checks are `node --check` **PASS**, dedicated structured-
argv admission **1/1 PASS**, direct bridge admission smoke **PASS**, and `git
diff --check` **PASS**. The G3-C/G3-D/G3-E/G3-F/G3-G/G3-H focused checks then passed:
bridge/CJS/runtime **13/13**, approved-patch bridge/runtime **9/9**, Python
file-read + approved-patch **20/20**, Python exec fault-focused **21/21**, and Python
MCP exec + OAuth + HTTP API **72/72**, including G4-B writer handoff, G4-C
exec guard and G4-D terminal fence **1/1 each**; G4-E HTTP→node exec E2E is
**1/1 PASS**; G4-F adds the real Recovery process fixture for run/poll/stop,
G4-G covers accepted-receipt ACK loss, G4-H covers MCP disconnect reconcile and
G4-I covers terminal receipt ACK replay, G4-J covers process crash/restart
without redelivery and G4-K covers running-handle resume/terminal-result loss.
enrollment/manager/rotation **25/25**; `py_compile` and related `node --check`
checks also pass. Targeted `test_wave_a_runtime.py` remains
**11/12 PASS**, with the remaining Linux standalone Landlock-helper import
failure classified as a pre-existing harness/runtime issue. These are still not
live service/job or ChatGPT two-client proof: remaining write-path integration,
terminal Recovery crash/duplicate-effect/reconcile beyond the covered process
crash,
packaged activation and soak remain open. The HTTP→node proof plus
G4-F/G4-G/G4-H/G4-I/G4-J/G4-K process/fault fixtures are
source/focused; neither is packaged/live Windows Job proof. See the new plan for dated evidence,
reuse/gap tables and G0–G6/T01–T16.
Automatic startup after user logon and pre-login boot operation are separate
acceptance claims; the existing Interactive/Limited Supervisor proves neither
new live claim by source presence alone.

### G4-K partial implementation/status checkpoint — 20-09-2026, 22:21 +07

The current plan now treats `binding_id` as the shared-account workspace
selector: one bound host/workspace can be commanded by multiple ChatGPT clients
that resolve to the same verified principal. The client device is not silently
enrolled as an executor, and a task keeps its resolved device/workspace/generation
even when another client takes over observation or writing. This is a contract
clarification and status update, not live two-client proof.

G4-J is source/focused proof and G4-K is partial source/focused proof: simulate Recovery process crash after a
durable `prepared`/spawn boundary, classify the outcome as
`unknown/reconcile_required` when effect is uncertain, and prove that resume
does not call `exec_run` twice. Running-handle resume and terminal-result-loss
cases now also pass. The continuation wave additionally proves central terminal
receipt ACK loss across Recovery restart and stop-pending across a Recovery
crash/restart. Validation is full Python **255/255 PASS**, node-agent
**21/21 PASS**, Recovery HTTP process E2E **11/11 PASS**, and the combined
node-agent/MCP fault/store/exec lane **34/34 PASS**. The remaining G4-K gate is
writer/Job handoff plus duplicate-effect/reconcile on a real Job. Until that and
the later package/live gates are closed, the project remains
**focused-test proof, not production/full-authority acceptance**. Reusable foundations are listed in
[`TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md`](TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md);
no new identity system, AI controller, or per-session context copy is needed.

### G4-K continuation implementation/status checkpoint — 20-09-2026, 22:34 +07

The Recovery process fixture now persists a locally accepted stop observation.
If the process dies before the bridge response, the node leaves the stop
request pending; after restart it polls the same handle, records `stopped`, and
only then acknowledges the stop. A second test kills Recovery after central
commits a terminal receipt but before the node receives the ACK; the restarted
node replays the journaled receipt without another `exec_run`/`exec_poll`.
This is focused process-fixture evidence, not Windows Job Object or packaged
runtime evidence.

### G4-K writer-lease/local-Job checkpoint — 20-09-2026, 22:43 +07

The E2E path now keeps task A's binding writer lease while its local Recovery
Job is running. A competing task B receives `CONFLICT` for claim/release; only
after the terminal receipt can A release and B claim. The fixture observed one
`exec_run` and one `exec_poll`. This proves the central fence is connected to a
local Job lifecycle, but not yet to a packaged Windows Job or two real ChatGPT
clients.

### SecretStore checkpoint — 20-09-2026, 22:52 +07

`electron/services/secretStore.js` now persists a schema-versioned envelope with
an atomic temporary-file write, `fsync`, owner-only mode and `.bak` recovery.
Legacy unversioned payloads remain readable and migrate on the next mutation;
primary corruption can recover from a valid backup, while a store with no valid
copy or unavailable encryption refuses `set/remove` instead of overwriting
credential evidence. `tests/secret-store.test.js` covers these cases and is
**5/5 PASS**; the full Node command at this 22:52 checkpoint was **867 tests:
851 PASS, 16 SKIP, 0 FAIL**. The current 23:43 full-suite result is recorded
in the headline above and in the Electron owner-mediated rotation checkpoint.

This is Linux source/focused proof using fake encryption. It does not prove
Electron `safeStorage`/Windows DPAPI, ACLs, migration of the node credential
currently held in `control-plane-node.json`, or crash-safe credential rotation.
Those remain G2 gates. No live service, Windows package, ChatGPT client, commit,
push, deployment, restart or paid model call occurred.

### Node-agent credential protection checkpoint — 20-09-2026, 23:06 +07

The node-agent source now protects the Windows config credential independently
of Electron: `_write_config()` stores a `node_secret_dpapi` envelope and never
writes raw `node_secret` on the Windows branch; `_config()` unwraps it only in
memory and rejects ambiguous plaintext+protected files. A legacy Windows config
is migrated at the first authenticated read through an atomic replacement. If
the protection API is unavailable or the replacement fails, the old file is not
replaced by a plaintext fallback and no plaintext backup is created. Temporary
payloads are written with `flush` + `fsync` before `os.replace`.

Focused proof [`test_node_secret_protection.py`](../control-plane/tests/test_node_secret_protection.py)
is **6/6 PASS**; full Python control-plane discovery is **261/261 PASS** after
the patch, with `py_compile` and `git diff --check` also PASS. The Windows API
is mocked, so this is **SOURCE_PRESENT + FOCUSED_TEST_PROOF**, not live DPAPI,
ACL, packaged migration, restart/reconnect, or crash-safe rotation evidence.
The next gate is exact Windows packaged validation, followed by two-phase
credential rotation/retry under crash and lost ACK before claiming G2 complete.

### Schema-22 node-mediated credential rotation checkpoint — 20-09-2026, 23:29 +07

The unsafe one-shot operator rotation path is now fail-closed. The supported
source path is node-mediated:

```text
persist protected candidate → central prepare → central activate
→ promote candidate locally → central ack → retire old hash
```

SQLite schema 22 adds `node_credential_rotations`, which stores only hashes,
generation and state. `prepare` is idempotent; `activate` keeps old and new
credentials valid until acknowledgement; `ack` atomically promotes the new
hash/generation and makes the old credential invalid. A second active rotation
is rejected.

The node-agent persists a pending candidate in its protected Windows envelope,
tracks `candidate_persisted/prepared/activated/promoted/completed`, and resumes
after lost responses or process restart. Focused proof is rotation store/agent
**5/5 PASS**, HTTP **1/1 PASS**, node-secret protection **8/8 PASS**, and full
Python control-plane **269/269 PASS** in **75.868s**. This remains mocked/local
source proof: no Windows DPAPI/ACL packaged run, operator UI, real-machine
rotation, or exact-package fault/soak evidence yet.

### Electron owner-mediated rotation checkpoint — 20-09-2026, 23:43 +07

The packaged Electron boundary now exposes an owner-confirmed credential
rotation action. `ControlPlaneEnrollmentService.rotateCredential()` invokes
only the packaged node-agent `rotate-credential` command and strictly parses a
redacted state/generation receipt. Main IPC requires the central-executor role
and `confirmRotation=true`; preload exposes no secret; the renderer shows only
state/generation and never receives the raw candidate. The UI keeps the action
hidden until enrollment is `approved` and supports retry of the durable node
phase.

Focused enrollment/manager/rotation proof is **25/25 PASS**. Full Node is
**868 tests: 852 PASS / 16 SKIP / 0 FAIL**; syntax checks and `git diff --check`
pass. This is still source/focused proof: Windows packaged/live DPAPI,
`safeStorage`, ACL, exact-build crash/lost-ACK rotation and real ChatGPT
multi-client acceptance remain open.

### Account inventory presence checkpoint — 2026-09-21, 00:04 +07

`ControlPlaneStore.list_account_targets()` now returns `presence_state` and
`heartbeat_age_ms` for each active binding without exposing a local path or
credential. The projection is `unknown` when no valid heartbeat exists,
`online` while `last_seen_at_ms` is within the 60-second threshold, and
`offline` once that heartbeat is stale. It is deliberately independent of
task/context/policy creation and does not grant authority or retarget a task.

The focused regression
`test_account_target_inventory_distinguishes_unknown_online_and_stale_presence`
passes **1/1**; the OAuth module is **24/24 PASS** and the full Python discovery
is **270/270 PASS** (about **70.766s**). This is fake-clock/SQLite source proof;
Windows packaged heartbeat, reconnect after restart, revoked-vs-offline
reconciliation and two real ChatGPT clients remain unverified.

### Connected-agent worker checkpoint — 2026-09-21, 00:22 +07

The packaged Supervisor now starts `run-connected-agent`. It sends a runtime
heartbeat before each iteration regardless of compact read-only policy state,
then checks the current local workspace registry/generation and standing policy
before polling `file-read`, `artifact`, `approved-patch` or `exec`. Missing or
disabled policy is a typed disabled lane; it never grants authority or dequeues
that lane. Transport/runtime/auth failures use bounded backoff, and a dedicated
same-profile lock prevents duplicate connected agents. The legacy
`run-read-only-agent` remains available only for explicit pilot diagnostics.

The new worker regressions are **3/3 PASS**; full Python discovery is **273/273
PASS** in **71.758s**. This remains source/focused proof: exact Windows package,
startup/reconnect after reboot, real heartbeat, revoked-vs-offline handling,
two ChatGPT clients and full read/write/Git/build/test/deploy E2E are still open.

### Prior source checkpoint — workspace capability registration — 2026-09-20

The Electron-to-node enrollment boundary now carries the owner-selected local
capability shape `{read, write, exec}`. `read` is always required; `write` and
`exec` default to false and are enabled only by explicit local UI selection.
The service rejects missing/extra keys, non-boolean values and `read=false`,
then passes the corresponding node-agent flags. Registration remains opaque:
the path stays local, Ubuntu receives only ID/generation/display/capability,
and no binding/context/task authority is created by this step. Inventory rows
show the actual capability set.

Proof for this checkpoint is focused source proof only: Node enrollment + manager
tests **23/23 PASS**, the three changed JavaScript modules pass `node --check`,
and `git diff --check` passes. It does not prove that an already registered
workspace can be upgraded in place, nor that packaged/live Windows, Ubuntu
schema 21, two ChatGPT clients, or write/Git/build/test/deploy E2E are active.
That checkpoint was superseded by the G3-G replacement/migration source proof
below; the live gates remain open.

### Latest source checkpoint — workspace capability replacement/migration — 2026-09-20

The registered-root capability change now has an explicit replacement flow. The
node keeps the same `workspace_id` and local canonical path, retires the old
`workspace_generation` at Ubuntu, disables old file-read/approved-patch/exec
policies, and registers a new generation only after a valid receipt. The local
registry is committed last, so a failed retire or register cannot silently
overwrite the old entry.

The node-agent `replace-workspace` command requires explicit confirmation and
stores only a secret-free phase journal (`planned`, `retire_sent`, `retired`,
`register_sent`). Lost registration ACK or a crash resumes the register phase
without a second retire; stale generation/task/binding references are fenced
and the UI tells the operator to bind the new ID. Electron now exposes the
service, IPC and preload route plus a “Thay capability” action. The new
capability remains a local ceiling and never grants Windows Administrator.

Proof for this checkpoint is source/focused/full-test evidence: replacement
tests **3/3 PASS**, enrollment/manager **24/24 PASS**, Python control-plane
**240/240 PASS**, Node **862 tests (846 PASS / 16 SKIP / 0 FAIL)**, `node --check`
and `git diff --check` PASS. No Ubuntu schema-21 live receipt, packaged Windows
activation, two-client ChatGPT receipt, Recovery IPC process-fault proof,
protected secret-store/rotation proof, or read/write/Git/build/test/deploy E2E
has been obtained in this checkpoint.

### Latest focused fault checkpoint — Recovery bridge boundary — 2026-09-20

The descriptor-hiding CJS bridge now has focused failure oracles for two
fail-closed cases: a Recovery installation identity mismatch stops before any
IPC call, and a typed Recovery IPC failure is propagated without returning the
descriptor/token. This is source/focused evidence only; it is not a Recovery
Host process, packaged Windows, or network-fault receipt.

The combined bridge/CJS/runtime lane is **13/13 PASS**. The full Node suite is
**862 tests (846 PASS / 16 SKIP / 0 FAIL)**. The next gate remains a real
Recovery IPC/MCP fault/reconcile run on the exact package, followed by protected
secret-store/rotation and the two-client account→binding→host E2E.

A read-only `npm run dev:status` attempt in this Linux shell returned
`DEV_UI_APPDATA_UNAVAILABLE` because `APPDATA` is unavailable. This is an
observation-environment limitation, not a Windows runtime verdict; no live
activation or service mutation was attempted.

### Prior account-sharing source checkpoint (G4-A) — two clients, one principal — 2026-09-20

The OAuth HTTP fixture now maps two distinct access tokens to the same verified
principal. Both clients see the same account-scoped `binding_id`; client A opens
a task, client B replays the same idempotency key and receives the same
`task_id`, then observes the pinned binding through `task_control`. The
observation is redacted and contains neither node credentials nor action
argument JSON.

This focused test is **1/1 PASS** and the full Python control-plane discovery is
**240/240 PASS**. It proves the source-level account→binding→task contract only;
it does not prove two real ChatGPT sessions, live IdP/OAuth, writer takeover on
a real Job, or Windows packaged execution. The next gate is the same scenario
with two real clients plus writer-lease/stop/handoff and duplicate-effect tests.

### Latest writer-handoff source checkpoint — two clients, one binding — 2026-09-20

The OAuth HTTP fixture now proves the next G4 boundary with two distinct bearer
tokens mapped to the same verified principal and one `binding_id`. Client A
opens task A and claims the workspace writer lease. Client B opens task B on the
same binding; its claim returns a MCP `CONFLICT` while A still holds the lease.
After A releases with an explicit handoff reason, B claims successfully. The
returned projection contains neither `node_secret` nor `arguments_json`.

This is test `test_two_clients_same_oauth_principal_handoff_writer_lease_over_http`
and it passed **1/1** through the real `ControlPlaneHttpServer` OAuth MCP
ingress. Full OAuth tests are **22/22 PASS** and full control-plane discovery is
**241/241 PASS**. Lease generations are monotonic per task; `task_id` is also
sealed into action/intent, so task B starting at generation 1 does not inherit
task A's authority.

Evidence level remains `FOCUSED_TEST_PROOF`, not live acceptance. There is still
no receipt from two real ChatGPT sessions, an actual local Job handoff, stop or
duplicate-effect recovery after lost ACK, packaged Windows activation, or
read/write/Git/build/test/deploy E2E. The next implementation gate is to bind
this lease path to a real Job/RUN/WAVE lifecycle and run claim-before-dispatch,
terminal stop, fault/reconcile and duplicate-effect tests before live rollout.

### Latest exec-guard source checkpoint — claim-before-dispatch — 2026-09-20

The next mutation boundary is now covered through the OAuth HTTP ingress. With
client A holding the writer lease on task A, client B's `exec_run` for task B on
the same binding returns `CONFLICT` before any `context`, `work_request`, or
`action` is created. After A releases, B repeats the same idempotency key and
the action is queued for task B; the exec intent stores the task and lease
generation. The fixture uses `exec=true` capability and the full OAuth exec
contract, but does not spawn a process.

Test `test_writer_lease_blocks_cross_client_exec_before_dispatch_over_http`
passed **1/1**. Full OAuth tests are **23/23 PASS** and full control-plane
discovery is **242/242 PASS**. This is `FOCUSED_TEST_PROOF` for central
claim-before-dispatch and no-durable-effect-on-conflict, not proof of a local
Job, terminal receipt, stop quiescence, lost-ACK recovery, packaged Windows, or
two real ChatGPT sessions. The next gate is an exact Job/RUN/WAVE lifecycle
test with stop, reconcile and duplicate-effect fault boundaries.

### Latest terminal-fence source checkpoint — dispatch to handoff — 2026-09-20

The central queue now has a focused proof that a dispatched exec cannot be
handed to another task while its outcome is unresolved. Task A is polled into
`dispatch_unconfirmed`; releasing its writer lease returns `CONFLICT`. Only a
terminal `completed` receipt settles the action, after which A can release and
task B can claim the same binding. This checks durable attempt/receipt state,
not merely an in-memory lease.

Test `test_dispatched_exec_keeps_writer_lease_until_terminal_receipt` passed
**1/1**; the MCP exec class is **8/8 PASS** and full control-plane discovery is
**243/243 PASS**. Evidence is still `FOCUSED_TEST_PROOF`: no exact Windows Job,
Recovery process fault, stop-quiescence, lost-ACK/duplicate-effect, packaged
activation or real ChatGPT two-client receipt exists yet. The next gate is to
bind this central attempt/receipt fence to the local Recovery/RuntimeOrchestrator
Job handle and exercise terminal stop plus fault reconciliation.

### Latest HTTP→node exec source checkpoint (G4-E) — 2026-09-20

The new fixture closes the next source-level integration boundary. A linked
OAuth client opens a task and claims its writer lease through the real MCP HTTP
ingress; a node heartbeat makes the target dispatchable; `exec_run` is polled
through the node-authenticated HTTP route; the node validates its standing
policy, writes a durable journal entry and submits an accepted receipt. A
second `poll_exec_once` resumes the persisted command handle with `exec_poll`
and submits the terminal receipt without a second spawn. MCP `exec_status` and
`exec_output` then relay only the verified terminal payload.

The fixture deliberately mocks only `recovery_exec_bridge` with a narrow
result. Central OAuth/queue/attempt/receipt storage, node policy admission,
journal, HTTP routes and MCP projections are real. It found and fixed a real
bug where terminal control receipts omitted `output_bytes`; the central relay
verifier therefore discarded an otherwise valid settled receipt.

`test_mcp_exec_http_node_e2e.py` passed **1/1**, the related regression lane
passed **96/96**, and full Python control-plane discovery is now **244/244
PASS**. This remains `FOCUSED_TEST_PROOF`: no packaged Recovery process,
Windows Job, lost-ACK/duplicate-effect fault drill, two real ChatGPT sessions,
or live deployment is proven. Next gate: replace the bridge mock with an exact
Recovery/Electron process fixture and exercise stop, lost-ACK, reconcile and
writer handoff across Job/RUN/WAVE.

### Ubuntu central-executor migration repair — 2026-09-16

The owner-authorized Ubuntu-primary architecture is tracked in
[`UBUNTU_CENTRAL_MCP_COMPLETION_PLAN.md`](UBUNTU_CENTRAL_MCP_COMPLETION_PLAN.md).
The installed Windows candidate exposed a real onboarding defect: its role-change
button required an accepted **code** checkpoint, although the live checkpoint had
no affected code components. Operator role migration now has its own exact
`full_clean_execution_role_handoff` path. It still requires canonical ledger
quiescence, process ownership, fencing, a new durable epoch and profile-specific
verification; it does not fabricate source acceptance or bypass code activation.
Pairing/policy can proceed after the role is persisted while admission remains
closed; FAILED/expired onboarding has an explicit retry. Pending handoff is not
reported as successful central connectivity.

Central final verification reads fresh independent route/policy evidence instead
of requiring its own READY bit. Persisted central READY adoption uses its exact
central census, never a Windows Tunnel connector receipt. Ordinary central
Recovery supervision also strips legacy Tunnel inputs and never reads the Windows
Runtime API key. These are focused source/test claims until the deployment receipt
in the completion plan records the exact candidate and observed live result.

### Ubuntu root MCP Tunnel provisioning — 2026-09-17

The root facade negotiates `2025-11-25` and `2025-06-18` instead of rejecting a
compatible client's offered protocol. Authenticated MCP notifications return
HTTP 202 without a body; missing/null request IDs cannot dispatch tool work.
The eight-tool schema, context-scoped grant and admission boundaries are unchanged.

The Tunnel unit loads a dedicated nonsecret `mcp-tunnel.env`, never the operator
environment. Its launcher pins the selected Tunnel ID and main loopback MCP URL,
and passes an owner-private file reference for the scoped MCP Authorization
header. The OpenAI Runtime key is a separate file reference in the protected
profile. A shared Tunnel grant represents one pilot principal/context, not
per-user identity; it stops authenticating when that context/grant expires or
is revoked. Configuration/doctor success is not a cloud-client execution proof.
See the completion plan for the exact deployment receipt and remaining gates.

The first user-confirmed ChatGPT connector creation reached root
`server/discover`, but the facade replied with the legacy initialize/list
shape. Modern MCP discovery requires supported versions, complete-result/cache
fields, and namespaced server information. A scoped dual-era adapter now serves
MCP `2026-07-28` requests independently while preserving legacy initialize
clients, exact grants, tool schemas and recovery admission. A successful HTTP
200 or Tunnel poll is not connector creation proof; record the actual ChatGPT
application/discovery outcome separately.

## 0. Current convergence guidance — 2026-09-04

The current engineering strategy is **convergence, not architecture expansion**. Do not build more system merely because a historical plan contains another layer or because an evidence gate is still open. Existing implementation should be closed by exact provenance, a real end-to-end Problem continuity observation, natural evidence, and accepted-result economics before another framework or control plane is authorized.

Use the following evidence ladder. Each row is a distinct claim and a stronger row must never be inferred from a weaker one:

| Evidence state | What it proves |
|---|---|
| `SOURCE_PRESENT` | Exact bytes exist in the current checkout. This is not proof, acceptance, or runtime evidence. |
| `FOCUSED_PROOF` | A bounded oracle passed for those exact bytes. This is still not final acceptance or live activation. |
| `EOCL_ACCEPTED` | The semantic controller accepted exact receipts at a stable checkpoint. This is not proof that a process loaded them. |
| `LIVE_COMPATIBLE` | A current development process/revision is live under the compatible activation path, for example `CURRENT_COMPATIBLE_ACKNOWLEDGED`. This is process-bound local evidence and is **not** strict connector rediscovery. |
| `STRICT_REDISCOVERED` | An official current-process discovery receipt (`tools/list` or `server/discover`) exists and is acknowledged under the strict path. Compatible bootstrap/current access must never be relabeled as this state. |
| `PACKAGED_RELEASED` | Required package/installer/release evidence has passed. Local source, EOCL, or live-development evidence does not imply this state, deployment, production, or SLO proof. |
| `NATURAL_PROBLEM_OUTCOME` | A real natural Problem Revision preserves exact RUN/WAVE continuity and ends in independent outcome confirmation or a truthful same-revision reopen. Accepted execution alone is not this outcome. |
| `ECONOMICS_POLICY` | Representative natural evidence has enough measured accepted-result economics to justify a policy decision. Missing usage, money, outcome, or coverage stays unknown rather than zero. |

The convergence sequence is intentionally finite:

1. converge the implementation and exact provenance already present; do not add another system layer;
2. prove continuity on **one real natural Problem** from Problem Revision through exact RUN/WAVE/checkpoint to independent outcome or truthful reopen;
3. gather **5-10 natural Problems** with the same provenance discipline instead of synthetic filler;
4. measure accepted-result economics, coverage, rework, TTAR/TTPR and operator burden without converting missing evidence to zero;
5. only then decide whether EGRI/P5 should advance, remain gated, or be simplified;
6. classify the surviving surface explicitly as **KEEP / MODIFY / REMOVE**.

`KEEP` means retain a mechanism with unique authority/value and current evidence. `MODIFY` means correct a demonstrated defect or evidence gap using the smallest existing surface. `REMOVE` means delete or collapse redundant policy/framework surface only after its authority/evidence role is demonstrably unnecessary; never erase durable evidence or rewrite dated research chronology to make the present look cleaner.

This section is the current sequencing and provenance authority for this maintained document. Older dated runtime paragraphs below remain immutable observation snapshots. If a historical block says `current`, `update_pending`, `connector blocked`, `source-only`, or names a process/epoch, read that language in the timestamped observation window unless a fresh supported runtime receipt re-establishes it. A present-day `CURRENT`/`fully_ready` local observation is still only local runtime evidence; compatible current access is not strict rediscovery, and neither is a package/release/production claim.

### Current 1.0 engineering/release-candidate receipt — 2026-09-06

The local Windows 1.0 engineering candidate is closed through source, full
Python proof, an exact-current NSIS build, packaged and installed Recovery
smoke, and a sufficient fresh UI performance window. This is a local
release-candidate claim only: no tag, GitHub release, publication, deployment,
production claim, independent new-machine run, or upgrade from a historically
published installer is implied.

- `npm run test:mcp` completed with `936 passed, 5 skipped` in `371.66s`
  (exit `0`). The earlier 300-second timeout was a proof-window limitation, not
  a retained Python failure.
- The current-source Node release lane completed with `714` tests passed plus
  source-root and tracked-secret guards passed. One Windows temporary-tree
  cleanup produced `EPERM`; its exact focused retry passed `4/4`. The final
  `npx electron-builder --win nsis` node then completed with exit `0` and
  produced `dist/coding-tools-mcp-setup-1.0.0.exe`. The exact installer used
  for the final local smoke was `121,636,941` bytes with SHA-256
  `20f740bac29522d634bbfc4708040538f0cab8528d907e03ac46b7dd47f8af0c`;
  its blockmap SHA-256 was
  `d0d8a0348eace3969715e11da79a856c8e576c8c7b881e314dc88fa375ba104b`.
- The final packaged smoke proved byte-exact allowed resources, only `en-US`
  and `vi` locales, `smart-v3` with exactly eight public tools, Recovery Host
  and independent Recovery MCP readiness, supervisor health, live-owner and
  executable-hash fail-closed behavior, no Scheduled Task mutation, and an
  unchanged production Recovery descriptor.
- `node scripts/installed-recovery-smoke.js` then installed the exact NSIS
  candidate silently into an isolated temporary path, verified its registered
  installation and the same packaged Recovery/contract surface, uninstalled it
  with exit `0`, removed installed files and registration, and proved that the
  production Recovery descriptor and existing Recovery Supervisor Scheduled
  Task definition did not change. This is same-machine isolated-install proof,
  not an independent new-machine receipt.
- The release-harness source was accepted by Coding-VP at checkpoint
  `e5673e0ded354257a7c3309dfc1691b0` and corrected after lifecycle postflight at
  checkpoint `84b65096ab0c4a4e98bcf07362f94540`. The correction removed an unnecessary
  `package.json` alias that made the Electron revision appear stale without an
  activatable component; the direct installed-smoke command remains the
  supported test entry point. Current `npm run dev:status` again reports equal
  Electron running/disk revisions, `CURRENT`, `fully_ready=true`, and
  `CURRENT_COMPATIBLE_ACKNOWLEDGED`. Compatible bootstrap remains distinct from
  strict connector rediscovery.
- A fresh Electron UI instance collected 20 renderer, 40 main-process, and 445
  event-loop samples. Readiness is `pass`: event-loop p95 `15.5ms`, normal IPC
  p95 `85.1ms`, snapshot-apply p95 `0.1ms`, and dashboard-refresh p95 `110.6ms`.
  The older long-lived window's insufficient/stale sample set is superseded for
  this local candidate, not rewritten.
- A query-only canonical lifecycle census reports zero managed jobs, zero
  unexplained active RUNs, zero awaiting-acceptance RUNs, and no projection
  drift. Thirty-three inactive RUNs remain below the 86,400-second stale
  threshold and are therefore not eligible for forced reconciliation. Six P5
  experiment anchors remain retained historical evidence.
- The two `260905_*` research/checkpoint documents referenced below were
  restored byte-for-byte from their verified retained Git object. They remain
  dated chronology and do not override this maintained current receipt.

Natural Problem continuity/outcome, representative accepted-result economics,
automatic non-deterministic routing promotion, strict connector rediscovery,
an independent new-machine run, and publication/deployment remain separate
evidence gates. They are not blockers to this bounded local engineering
release-candidate closure and must not be reported as completed without their
own real evidence.

### Baseline correction source checkpoint — 2026-09-05

The implementation follow-up to the [05 September finish-line assessment](research/260905_COMPREHENSIVE_PROJECT_ASSESSMENT_AND_FINISH_LINE.md)
is tracked in the [source/test checkpoint](research/260905_FINISH_LINE_IMPLEMENTATION_CHECKPOINT.md).
The user-approved closure decision on 06 September is recorded in checkpoint
section 20: finish M1 engineering convergence separately from empirical M2/M3,
upstream accounting and destination-specific delivery. Freeze source/features
and these progress documents during the proof → acceptance → controlled activation
batch. Compare accepted bytes once, close only demonstrated gaps in a combined
integration scope, classify/reconcile eligible control debt through supported
authority, and obtain exact live-current proof. Sections 21–22 supersede the early
20.5–20.6 observations: the product 1.0.0 normalization is present in the existing
version RUN. Node, Python and Rust commands are terminal exit 0, but consolidated
exact-byte acceptance is still open. Python's retained task projection records
930 passed, 5 skipped and 218 subtests; skips are not passes. The audited build
verification has build_result=null and an existing older artifact inventory, so
a fresh package build is not proven. Of 40 accepted receipt paths rehashed, 38
still match and two have the requested version/policy drift. Section 22 records
successful public exact-run context recovery: task_control get with the exact
RUN and no supplied context returned its persisted owner handle, bound to the
correct task/RUN/WAVE. Continue with that returned handle; no manual handoff or
new RUN is required. Do not create a parallel writer or repeat completed broad
commands to work around a missing canonical proof record.
The latest advice retains mandatory .coding-tools evidence in Git; migration or
untracking is not part of M1. Keep product-source cleanliness separate from
allowed evidence mutations. This does not waive acceptance
guards or authorize rerouting a denied oracle. Do not
hold M1 open merely for natural-cohort counts, upstream billing or rendered 900px
proof, and do not report any of those deferred claims as completed.
That checkpoint's sections 9 and 12 record exact two-file dashboard and parser
EOCL acceptance, respectively. Section 12 corrects the earlier unverified client
block diagnosis and records successful current-context reads and revalidation
after documentation-only worktree drift. Section 13 records exact-file acceptance
of the Recovery Host and release runbooks, including the corrected strict versus
attested compatibility ACK guidance. That document acceptance is not runtime
proof; the independent Python metadata proof attempt stopped at the server's
inline-script permission gate without a grant or accepted proof.
Section 14 adds exact producer-measurement and three-file command-core acceptance.
Section 15 separately closes exact two-file `live_control.py`/endpoint acceptance
and its report ACK, backed by four focused temporary HTTP tests and four subtests.
This current successful request does not erase the unverified historical refusal
or clear the separate metadata permission gate. The latest recorded development
check after the producer change reports Coding MCP `update_pending`; source and
HTTP-harness acceptance are not loaded-revision or live-user journal proof.
Section 16 closes the initial donut placeholder correction and its focused Node
proof/ACK without reaccepting the dashboard core. The six hard-coded model rings
are absent before the first snapshot. This does not accept the entire Electron
integration. Section 17 closes the three-file responsive correction and static
regressions: narrow KPI cards use the existing breakpoint, inner metadata no longer
inherits outer-card sizing, and narrow split panels/tool rows remain reachable.
Section 18 closes exact 16-file font/distributor-identity and renderer-revision
adoption, focused proof and final report ACK. Historical distributor byte checks
remain dated evidence, not a fresh font fetch or legal/rendering/installer proof.
No rendered 900px/CSS-engine proof has been obtained; the browser URL-policy denial
remains respected. Section 19 closes the exact main/preload window/bridge packet
with focused source/VM proof and report ACK, without a live-window claim. Metadata
official proof, consolidated provenance/control hygiene and accepted-to-loaded
still have independent gates. Direct version-literal alignment review is not
installed-distribution or executed runtime parity proof.
Section 19.4 verifies that public `task_control audit` with `run_id` and without
`wave_id`/`after_seq` exposes canonical checkpoint `metadata.accepted_files`;
the wave-filtered projection omits those aggregate fields. Audit regenerates the
target RUN reports, so it is not strictly read-only. This supported receipt source
enables baseline comparison; one audited RUN is not whole-baseline/G1 closure.
No-write adoption still requires exact passed proof; source review or verification
`none` is not an exemption for the unresolved metadata acceptance.
The latest recorded development check (2026-09-05T16:26:27.742Z) reports Electron
`STALE` and MCP `update_pending` with fresh telemetry; no activation occurred in
these waves. All further progress belongs in the existing checkpoint, not a new
progress or handoff report; sections 18.4 and 19.3–19.4 distinguish the remaining gates.
An explicit null/undefined performance pulse now clears the previous dashboard
trace and reports unavailable data; an omitted field preserves the existing
trace and a measured zero remains observed. The Codex-web product version is
`1.0.0` across the Electron package and Python MCP package/runtime metadata.
Protocol, schema, tool-contract, and data-format versions remain independent
compatibility identities.
The release checklist now uses `npm start`/`npm run dev` for start/focus and
`npm run dev:refresh` for full refresh, with explicit Python proof when a release
candidate changes MCP behavior.

For EOCL-scoped commands, `task_control(get)`, `task_state_get`, and live control
now derive command presentation from an exact checkout-local managed Job with
matching command/RUN/WAVE identity. A verified terminal Job clears the presented
active command and supplies `current_command_observation`; missing or conflicting
identity stays unknown without disclosing another Job's result. This does not
write task-state, append completion events, or synthesize proof/results. Raw
persisted projection and `CHECKPOINTED` authority remain intact; ordinary
commands without EOCL ownership keep their existing behavior. Focused source
proof is recorded in the linked checkpoint; no loaded-runtime claim is made.

The command path scanner now separates the filesystem prefix from a pytest node
selector for explicit `python`/`python3 -m pytest` invocations when the candidate
is the first node argument, optionally preceded by `-q`/`-v`/`-s`/`-x` flags.
Interpreter operands, ambiguous/plugin option operands, response files and
redirection targets keep their original path syntax and authority checks.
This is a bounded selector correction, not a full pytest CLI parser or endpoint
proof. The release checklist also distinguishes process-bound compatible
connector freshness from strict rediscovery; retained contract ACK alone is not
new-epoch readiness, and stale/missing telemetry remains unknown.

These local changes do not extend an earlier EOCL acceptance receipt or prove
that the running development processes loaded the new bytes. Consolidated
baseline acceptance, accepted-to-loaded activation, natural Problem continuity
and outcomes, controller accounting, and package/release evidence retain their
own gates. See the linked checkpoint for exact scope, proof and remaining work;
historical runtime observations below remain bound to their recorded timestamps.

## 1. Source of truth and document precedence

When repository documents disagree, use this order:

1. **Current implementation + focused tests + live runtime contract** for the exact checkout being operated.
2. **This file (`docs/CURRENT_STATE.md`)** for the current product boundary and operating policy.
3. `README.md`, `docs/ARCHITECTURE.md`, `docs/RECOVERY_HOST.md`, `docs/TESTING.md`, `docs/ROADMAP.md`, `docs/RELEASE_CHECKLIST.md`, and `SECURITY.md` for maintained product guidance.
4. `docs/MODEL_EXECUTION.md` and `docs/agent/*` for the WebCodex core/subsystem they explicitly describe.
5. Dated files under `docs/research/*` as historical evidence, plans, benchmarks, and decision snapshots. They do **not** override later source or this current-state document.

A source implementation can be newer than the process currently running. For Electron, Recovery Host, Coding Tools MCP, and other supervised components, distinguish **source present**, **focused proof passed**, **EOCL accepted**, **controlled activation completed**, and **packaged/released**.

Development startup has two explicit contracts. `npm start` and `npm run dev` use the same stable start/focus lifecycle: they inspect the authenticated Recovery Host receipt for this exact development installation, classify Electron UI as `CURRENT`, `STALE`, or `MISSING`, focus a current UI, use component activation for a stale UI, or launch a missing UI. Success requires `running_revision == disk_revision` with PID/instance/mode metadata and a ready runtime postflight. Stale code activation remains authorized only from an eligible accepted closure checkpoint. `npm run dev:refresh` is the separate operator full-system refresh: it authenticates the current Recovery Host, creates a durable `full_clean_refresh` activation epoch, replaces Recovery Host, Coding MCP/Tunnel, configured Recovery MCP/Tunnel and Electron UI, then verifies fresh process identities, matching revisions and epoch binding. When the shared profile is owned by a packaged Recovery Host, `npm start` and `npm run dev:refresh` may perform this handoff only after authenticated exact PID/instance/start-token proof shows that host has no live UI, MCP, native runtime or Tunnel, has fresh non-busy telemetry, is not recovering, has a terminal activation epoch, and is bound to the selected development workspace. A live, stale, ambiguous, wrong-workspace, or different-development-checkout owner remains fail-closed. It never deletes durable truth; it fails closed if ownership, canonical ledger state or postflight cannot be proven. `npm run dev:stop` suppresses UI watchdog recovery and asks the exact registered single instance to quit while preserving Recovery Host, MCP, and Tunnel. It refuses an initially unavailable Recovery Host and reports success only after that exact host reports the UI `MISSING` or the previously bound PID is proven dead; transient host loss is not stop proof. `npm run dev:replace` applies the same exact-instance stop postflight, then relaunches and verifies a different UI instance. Connector discovery/ACK remains a separate gate; a refresh does not invent a connector receipt or open admission early.

The Command Center exposes loaded-source status for the three revisioned components—Electron UI, Recovery Host, and Coding MCP—and reports Tunnel health separately as `READY` or `STOPPED`. `CURRENT` is process/revision evidence only and never derives from Tunnel availability; it is not EOCL acceptance, release, deployment, production, or SLO proof. A source-update notice remains visible whenever a running component revision differs from disk.

The five-second Electron heartbeat is a read-only consumer of the latest completed Recovery Host supervision projection; it does not launch a second MCP/Tunnel/Git/OS-identity census. Recovery Host publishes the projection source, observation timestamp, age, busy flag, and freshness state, while Electron keeps heartbeat publication single-flight. Missing or older-than-30-second telemetry is `UNKNOWN/WARN` and appears yellow while retaining the last receipt for context; it is not evidence that MCP, Coding Tunnel, or Recovery Tunnel has stopped. Red is reserved for a confirmed stopped/error state or a deterministic `blocked_*` Recovery condition. This presentation rule does not weaken lifecycle recovery thresholds, process-identity checks, activation gates, or aggregate `fullyReady` semantics.

### Accepted-to-live activation closure

The supported development closure is `ACCEPTED/CHECKPOINTED -> ACTIVATABLE -> controlled component activation -> schema-v2 component postflight -> LIVE_CLOSED`. Each activation is authorized by one exact, non-normalized five-field `source_checkpoint`: `checkpoint_id`, `run_id`, `wave_id`, `proof_fingerprint`, and `git_head`. The Coding MCP preflight must return `ok=true`, `code=ACTIVATABLE`, and the same five values; partial, trimmed, case-folded, or otherwise reconstructed identities are not authority.

A schema-v2 postflight is accepted only when its operation, component, checkpoint lineage, expected/running/disk revision, instance transition, timestamps, health result, and fresh post-cancel lifecycle decision all verify. That final lifecycle decision must come from a new immutable, query-only SQLite Backup-API snapshot with `integrity_check=["ok"]`, zero foreign-key rows, valid physical/logical SHA-256 values, the exact operation/checkpoint, no fence, and zero blocking lifecycle counts, unexplained active RUNs, or unbound live residues. A contradictory `clean=true` flag cannot override those facts; the same lifecycle rule applies when an accepted checkpoint affects zero runtime components.

`LIVE_CLOSED` means only that this exact accepted local source is loaded and locally ready under the verified lifecycle and connector contract. Its projection deliberately remains `release_state=NOT_RELEASED` and `production_state=NOT_CLAIMED`. Connector continuity is separate: persisted SHA equality alone is not process-freshness proof for a new full-clean epoch. A breaking contract, meaning the acknowledged SHA is not the exact current SHA and is not a declared compatible predecessor under the same schema/profile boundary, still requires an attested current-process `tools/list` or `server/discover` receipt plus official Recovery Host acknowledgement. For an exact current SHA or declared compatible predecessor, an admission-closed no-workspace bootstrap may instead close the connector gate only after an attested ChatWeb `workspace_context` call is bound to the exact activation epoch, MCP process instance, server instance and contract SHA, reports `workspace_accessed=false`, and the Recovery Host guarded ACK persists that exact receipt. Raw HTTP, implicit or explicit identity headers without managed-tunnel attestation, catalog metadata, arbitrary `tools/call`, or textual receipts cannot satisfy either path. The compatible acknowledged state is `CURRENT_COMPATIBLE_ACKNOWLEDGED`; it remains truthful with `connectorRediscovered=false`, carries its own compatibility acknowledgement timestamp, and may reach `READY` / admission `OPEN` without inventing a discovery receipt.

### Superseding P0.6 accepted baseline and live receipt — 2026-09-01

The current accepted source baseline is `main @ 30b7d1b971b65034d3e4c95568c970fcc0e9380c`, and the observed
`origin/main` ref matches that commit. The P0.6 source packet contains exactly
27 source/documentation files with packet SHA-256
`b64a9704a73ea78fd3f330f12712b03090f8082765b3befd4b52eaa849d8d739`.
Its immutable candidate and acceptance receipts are
`.coding-tools/orchestration/baselines/p0.6-20260831T141719Z-b64a9704.candidate.json`
and `.coding-tools/orchestration/baselines/p0.6-20260831T141719Z-b64a9704.acceptance.json`.
ChatWeb accepted the exact-file wave at checkpoint
`e3b6c1a07b3f4524af8d0bef967fc7d5`; the canonical proof fingerprint is
`702139edffa332d62604af2b57e63c9ca65828207f92c589608f2c83df546fba`,
and completion report
`7a4ec1350c3a3ba58fb61926088e8f12f965a02de248a950b88de6d48483114c`
is acknowledged. This supersedes earlier paragraphs that describe P0.6,
full-component acceptance, or the scoped delivery commit as still open; those
paragraphs remain historical receipts for the observations made at their own
timestamps.

The accepted-baseline process receipt immediately after delivery reported
Electron UI and Coding MCP `CURRENT`, `components_ready=true`,
`fully_ready=true`, `runtime_update_incomplete=false`, and `error_code=none`.
Connector continuity at that accepted identity is
`CURRENT_COMPATIBLE_ACKNOWLEDGED` through the managed-attested
`compatible_activation_bootstrap` path, with
`connector_refresh_required=false`, `connector_ack_pending=false`, and
`connector_rediscovered=false`; no strict discovery is inferred. Windows
Recovery Supervisor reports `Running` / `healthy` with zero consecutive
failures. A fresh immutable Backup-API lifecycle census reports schema 12,
SQLite integrity `ok`, zero foreign-key rows, zero ordinary active RUNs, no
managed jobs, no projection drift, no unexplained active RUNs, no unbound live
resources, and no stale background-operation residue. Six terminal P5 epoch
anchors remain retained as evidence and do not constitute active work.

P0 Operational Convergence and the P0.6 immutable local baseline are therefore
closed for this accepted source/runtime identity. This does not promote the
separate product-evidence or delivery gates: independent natural Golden HR
outcomes, prospective causal evidence, P4 predictive validity, P5-A0 natural
instrumentation health, Windows installer/release acceptance, deployment,
production, and SLO claims remain open until their own authority and evidence
requirements are satisfied.

### Post-baseline P2 source slice — 2026-09-01

The current post-P0.6 worktree adds a source-only derived Resolution Capsule to
the existing `task_control(handoff)` path; it does not add a ninth public tool or
a second authority/database plane. The projector binds the exact RUN to its
primary Problem Revision, emits the typed contract and criteria fingerprints,
bounded latest-event identity, same-revision reopen and independent-outcome
receipt observations, and a content-free Problem Frame shadow/advisory. It
explicitly states that transcript, raw source and private reasoning are absent
and that the capsule grants neither mutation nor acceptance authority. The
outer handoff remains capped at 8 KiB: a contract of at most 4 KiB is embedded;
a larger valid contract is represented by its exact identity plus
`exact_revision_refresh_required=true`, so callers must fetch the exact revision
instead of receiving silently truncated content.

Focused source proof for this slice is `17 passed, 3 subtests passed` in
`tests/test_problem_lineage.py`, `18 passed` across the durable coordination and
coordination-state consumers, plus the module-size and scoped diff-hygiene
guards. This is not yet an accepted or loaded-runtime claim. A fresh
`npm run dev:status` after the runtime-affecting source edit reports Electron UI
`CURRENT`, but Coding MCP `mcp_revision_state=update_pending`,
`components_ready=false`, `fully_ready=false`, and
`runtime_update_incomplete=true`; the exact running and disk revisions differ.
Recovery Supervisor independently remains `Running` / `healthy` with zero
consecutive failures. Controlled activation and a new exact acceptance receipt
are separate next gates; natural Golden HR outcome evidence remains uncreated.

### Historical operational recency override — 2026-08-27

The maintained execution tracker at [`research/260823_CODING_WEB_GATE0_PRL_IMPLEMENTATION_AND_VALIDATION_TRACKER.md`](research/260823_CODING_WEB_GATE0_PRL_IMPLEMENTATION_AND_VALIDATION_TRACKER.md) was the operational receipt for the volatile lifecycle, connector, PRL, and packaged-harness claims in that observation window. The superseding P0.6 section above is the current maintained receipt; this historical section must not override it.

- The checked-out Git identity observed on 2026-08-29 is `main @ c0aa335c7c12746a1f4ff42e84234f8c54914658`, matching `origin/main`. The current full-clean activation-closure, PRL v11, managed-tunnel attestation, exact discovery-receipt and lightweight-UI waves remain newer uncommitted source until an exact accepted checkpoint says otherwise; therefore the P5 source baseline is not clean even though HEAD matches upstream. PRL fails public caller-derived authority closed, records immutable non-code dispositions and checkpoint-bound reconciliation, reports revision-scoped clocks/intervals, and emits C4 receipt schema `2` with Backup-API snapshot identity plus independently rebuilt proof/checkpoint/bridge coverage. Neither a matched source revision nor a fresh runtime receipt is a package, installer, release, deployment, production, or SLO claim.
- Earlier P0/P4 connector acknowledgements and tool calls are `VERIFIED_SNAPSHOT`, not current-process authority. The current connector claim must be read from a fresh Recovery Host closure receipt under the unchanged-versus-changed SHA rules above; no persisted hash, generic tool call, or historical rediscovery timestamp may substitute for it.
- P5 anchors remain terminal and the earlier A0 source-drift epoch retains its truthful zero funnel. Volatile ordinary-RUN, managed-job, and residue counts are not frozen in this maintained source document: recapture them from one immutable `report_lifecycle_census.py` snapshot before activation or stale-run reconciliation, and use only the official exact-ID path for a genuinely eligible stale RUN.
- PRL-D and A2 remain `HOLD_NATURAL_EVIDENCE`; missing natural observations, TTPR, stage coverage, and measured money remain unknown rather than zero.
- The isolated P0.3 packaged Recovery lane is source/package-local evidence, not an exact-frozen release candidate, installed-session, reboot/logon, connector, or production claim.

### PRL v12 typed outcome-receipt source checkpoint — 2026-08-31

The current uncommitted worktree advances PRL storage from schema v11 to v12
and new problem events from schema 2 to schema 3 without changing the public
eight-tool `smart-v3` contract. `problem.confirm` remains a semantic input: the
runtime, not the public caller, claims the exact one-shot ChatWeb host turn and
derives `CHATWEB_EXPLICIT_USER_OUTCOME_V1` from the event ID, Problem Revision,
turn ID and trace ID. The resulting receipt is written under
`RUNTIME_OUTCOME_RECEIPT`, participates in the event hash chain, and is counted
by the read-only economics reporter only when the digest and provenance binding
recompute exactly. Direct caller receipt fields, missing host identity, a
mismatched digest, or tampered event bytes fail closed.

The guarded v11-to-v12 path preserves historical schema-2 event hashes and
leaves their receipt fields empty; it never backfills independent outcome
evidence. The current focused/affected packet passes `39` tests plus `7`
subtests, module-size validation and Python compilation, and the disk contract
remains the exact eight-tool SHA
`c244ed297f707f9df48c1e5d6c7e204693f281a755c2e6344bde78e94abb8251`.
The source packet was subsequently migrated under the guarded v11-to-v12 path
and loaded by the current development process. The following current receipt
supersedes the source-only qualification above for the live local epoch; it
does not rewrite the historical checkpoint.

### Current PRL v12 runtime and connector receipt — 2026-08-31T04:46Z

The full-clean development epoch
`activation-mtgqx4ha-2d70125bdcf3f1654d0c2de29361823a` is `READY` with admission
`OPEN`. Recovery Host, Coding MCP and Tunnel are running; Coding MCP
`running_revision == disk_revision ==
e5d120eb38e89f195dd504d77e64f5081dd5737710dd088cfe71e6b0a2b3c897`; the
Electron UI is also current. Coding-VP Live produced one managed-attested,
no-workspace `workspace_context` compatibility bootstrap at
`2026-08-31T04:45:19.154620+00:00`, bound to the current epoch/process/server
and contract SHA. The guarded Recovery Host acknowledgement is
`CURRENT_COMPATIBLE_ACKNOWLEDGED` with
`connector_freshness_mode=compatible_activation_bootstrap`,
`connector_refresh_required=false`, `connector_ack_pending=false`, and
`fully_ready=true`. This is intentionally not claimed as strict
`tools/list`/`server/discover`: `connector_rediscovered=false` remains truthful.

The PRL v12 canary was read-only and returned
`C4_SOURCE_READY_AWAITING_NATURAL_CANARY`; SQLite integrity and foreign-key
checks passed, while no natural cohort was inferred. The PRL-D economics
reporter returned schema version `5` against canonical PRL schema `12`, with
zero problem revisions and `null`/unavailable outcome, TTPR and efficacy
denominators. Missing natural evidence remains `unknown`/`null`; no synthetic
problem, outcome receipt or policy promotion was created.

This receipt closes current local runtime activation only. Full-component
source acceptance for the entire dirty Coding MCP component, an immutable
accepted Git baseline (P0.6), natural HR outcome evidence, commit, package,
release, deployment and production claims remain separate open gates.

### Current local activation and UI performance receipt — 2026-08-29T20:15:03Z

The exact current development process has now closed the local connector and UI
performance gates for the uncommitted source on disk. Query-only lifecycle
census observed `active_agent_lanes=0`, no managed jobs, unexplained active
runs, unbound resources, stale background residue or projection drift, and did
not mutate the canonical ledger. Three ordinary `active` rows remain classified
`THRESHOLD_SENSITIVE_STALE_CANDIDATE`; each has zero live ownership and remains
untouched until the supported stale threshold/authority permits reconciliation.

Full-clean epoch
`activation-mtetdl86-68c08c2f914e8049a4ebb4bf69833539` is `READY` with
admission `OPEN`. Coding MCP process/server identities are
`9RkQbeqAUay5_LRD` / `4OtFTiY9AnN5C8Po`, and its running revision equals disk
revision `68f0a59095855c4250f85bc72a7784ffafca99b424e73158a95948d1112ceff6`.
The real Coding-VP Live connection produced current-process discovery at
`2026-08-29T20:10:30.820587Z`; Recovery Host guarded acknowledgement reports
`CURRENT_ACKNOWLEDGED`, `connector_rediscovered=true`,
`connector_refresh_required=false`, `connector_ack_pending=false`, and exact
current/acknowledged contract SHA
`c244ed297f707f9df48c1e5d6c7e204693f281a755c2e6344bde78e94abb8251`.

On Electron UI instance `2709389fe3f50d3202ae67a25b3b7218`, the retained
25-renderer/50-main/558-event-loop sample window passes all current budgets:
event-loop p95 `15.6 ms`, normal IPC p95 `44.2 ms`, snapshot-apply p95 `0 ms`,
and dashboard-refresh p95 `66.2 ms`. Direct Recovery IPC also passes with 20
samples and p95 `3.07 ms`.

This is exact local runtime/connector/UI evidence for the present dirty
worktree, not an immutable accepted source baseline. P0.6 remains open until an
accepted/checkpointed Git identity exists under explicit scoped commit
authority and the remaining threshold-sensitive lifecycle rows can be handled
through supported authority. P5 remains gated on natural eligible workload and
an explicit frozen manifest/operator action. No commit, push, package, release,
deployment, or production operation is implied by this receipt.

### Operational follow-up — 2026-08-29T23:39:08Z

A new authenticated Recovery Host snapshot for the same checkout confirms that
the local control plane has not regressed: the epoch above remains `READY` with
admission `OPEN`; MCP, Tunnel and aggregate readiness are true; failures are
zero; connector state remains `CURRENT_ACKNOWLEDGED`; the strict discovery
receipt is still bound to the current process at
`2026-08-29T20:10:30.820587Z`; and both Coding MCP and Electron UI still report
`running_revision == disk_revision` with `update_pending=false`. The installed
development Recovery Supervisor is also `Running` / `healthy` with zero
consecutive failures. Consequently, an error observed through an older
ChatGPT connector or tunnel ID is not evidence that this active Electron
runtime is offline.

The ChatGPT Business workspace now shows the developer-mode app
`Coding-VP Live` as connected and exposes the expected eight-tool schema.
However, neither the app-details **Refresh** action nor a new normal ChatWeb
conversation advanced `connector_rediscovered_at`; the conversation reported
that protocol-level `tools/list` and `server/discover` are not exposed as model
callable operations, and no business tool fallback was used. The schema view,
the textual response, and the unchanged timestamp are therefore **not** a new
discovery receipt. They do not invalidate the accepted receipt for the current
process, but they leave rediscovery of a future replacement process unproven.
Do not stop this healthy epoch or run another full-clean merely to probe that
external client limitation.

The immutable/query-only census captured at
`2026-08-29T23:39:08.645Z` again reports `integrity_check=ok`, zero foreign-key
rows, `mutated_canonical_ledger=false`, no managed jobs, no unexplained active
RUN, no unbound live resource, no stale background residue and no projection
drift. The three ordinary active rows still have zero controller lease, write
fence, live agent lane, managed job and background operation, but remain
`below_current_stale_threshold`. Their earliest eligible times are
`2026-08-30 09:34:34`, `09:36:13` and `09:50:58` Asia/Saigon. No reconciliation,
runtime stop, activation, connector ACK, accepted-baseline creation, P5 action,
commit, push, package, release or deployment was performed in this follow-up.
The active completion monitor must recapture fresh hashes and exact-ID
preflight after those thresholds; it must also prove a managed-attested
discovery route before replacing the current process.

### Causal correction and live recapture — 2026-08-29T23:43:51Z

The discovery prerequisite above means a demonstrably connected official
route, not an impossible receipt for a process that does not yet exist.  The
same `Coding-VP Live` route already produced the managed-attested receipt for
the current replacement process at `2026-08-29T20:10:30.820587Z`.  A later
same-process app refresh that did not advance the timestamp does not invalidate
that receipt; it only fails to prove another protocol discovery occurred.  A
future replacement must therefore create its own receipt *after* the process
exists and before guarded acknowledgement.  If it does not, the new epoch must
remain fail-closed with admission closed; neither model text nor another
full-clean loop is a substitute.

Fresh local checks also disprove the attached claim that the active Coding
Tunnel is currently offline.  `npm run dev:status` reports `CURRENT`,
`host=available`, matching Electron running/disk revisions,
`CURRENT_ACKNOWLEDGED`, current-process discovery, no connector refresh/ACK
pending state, and no error.  The independent Recovery Supervisor briefly
reported `blocked_live_owner / LIVE_OWNER_UNRESPONSIVE` for one 1.5-second ping
while concurrent status/census reads were running, correctly refused to kill a
live owner, and returned on its next poll to `Running / healthy` with zero
consecutive failures and no restart attempt.  This is a transient uncertain
observation, not proof of a stopped tunnel or authority to replace the owner.

The immutable/query-only census at `2026-08-29T23:43:04.726Z` retained SQLite
integrity, zero foreign-key rows, no managed jobs, unexplained active RUNs,
unbound resources, stale background residues or projection drift.  Its
physical/logical SHA-256 values are respectively
`b556ead11a7ddb5fb303a47c98e9bb74ebb575202da8b65dc2e4c87a58d07107` and
`ed2cb592030ddefbcf5459475dcd9f4a67757e6654a8fd27c2e594c3ba426b5c`.
All three ordinary rows still had zero controller leases, write fences, live
agent lanes, managed jobs and running background operations, but their ages
were only `75123`–`76108` seconds against the supported `86400`-second
threshold.  These hashes are observation-only and must be recaptured after the
last threshold at `2026-08-30 09:50:58` Asia/Saigon; they are not authority for
later reconciliation.

### Recovery Supervisor false-owner remediation — 2026-08-30T00:04:36Z

The one-poll `blocked_live_owner / LIVE_OWNER_UNRESPONSIVE` transition above is
now reproducible and has a bounded source cause.  Both `recovery.ping` and
`recovery.status` previously built `hostStatus()` synchronously on the Recovery
Host IPC event loop.  That path performs Windows process-identity observation,
forced component-revision work and durable activation-state reads.  A normal
`npm run dev:status` can therefore overlap the independent Supervisor's
1.5-second liveness deadline and make an exact live owner temporarily
unresponsive.  The Supervisor response remains correct and fail-closed: the
live owner is not killed or adopted, the failure streak is one, no restart is
attempted, and the following poll returns to `healthy`.

The dirty source now separates liveness, cached presentation and mutation
authority.  `recovery.ping` is an in-memory exact host identity receipt;
`recovery.status` copies the most recent completed supervision projection and
adds bounded age/staleness metadata.  Activation and mutation paths retain
their fresh exact-identity, revision, epoch and ledger preflights.  A real
process harness race exposed by the faster ping was also corrected: the harness
must wait for a projection carrying the expected positive MCP/Tunnel PIDs and
must never probe or signal PID `0` during cleanup.

Current focused proof is `71/71 PASS` for Recovery Host and lifecycle status,
and `152/152 PASS` for the affected Supervisor, full-clean, runtime-lifecycle
and real-process boundary.  The real-process subset is `3/3 PASS` and
`git diff --check` passes.  A live recapture at `2026-08-30T00:04:10Z` still
reports `CURRENT`, `CURRENT_ACKNOWLEDGED`, current-process rediscovery, exact
connector SHA equality, no refresh/ACK pending state and no error.  The next
Supervisor poll reproduced the old one-failure state and the poll at
`2026-08-30T00:04:36Z` returned to `healthy` with the same host identity and no
restart attempt.  This proves the source cause against the still-running old
process; it does not claim that the new source is active.  Loading the fix
remains part of the single supported post-threshold full-clean sequence.

The same dirty source fingerprint now also has broad repository proof.  The
Node repository suite originally reported `547/547 PASS`, followed by the source-root
policy guard and repository secret check passing.  The complete Coding Tools
MCP suite reports `741 PASS` with `4` environment-conditional skips out of
`745` collected tests.  These broader results strengthen source acceptance but
do not create a checkpointed Git identity, mutate lifecycle state, activate the
new Recovery Host source, or promote P0.6/P5 by themselves.

### Development Supervisor suppression correction — 2026-08-30T00:38:27Z

A later live recapture found a second, independent resilience cause. The
previous Recovery Host was last observed healthy at `2026-08-30T00:09:31Z`,
but `%LOCALAPPDATA%\WebMcpRecoverySupervisor\stop.request` was written at
`2026-08-30T00:09:37.473Z`. Every subsequent Scheduled Task invocation
therefore exited in `stopping`; by `2026-08-30T00:38:25Z`, `npm run dev:status`
correctly reported `MISSING / RECOVERY_DESCRIPTOR_STALE`. The task remained
installed and its manifest still identified this exact checkout, so this was
not a `blocked_live_owner`, connector-cache result, or foreign-checkout
takeover.

The source cause was `ensureRecoveryHost()` suppressing any installed
development Supervisor *before* it checked whether the UI could simply attach
to the already healthy exact-checkout Recovery Host. That ordinary attachment
created the stop sentinel even though no host mutation or handoff followed;
when the Host later disappeared, the deliberately suppressed Supervisor could
not resurrect it. The dirty source now defers the decision until immediately
before an actual stale-host retirement or missing-host spawn and preserves an
installed Supervisor whose app-root/executable identity already matches the
current checkout. An exact healthy attachment never reaches suppression.
Focused launcher coverage is `15/15 PASS`, and the scoped diff check passes. The
current stopped runtime has not loaded this correction, and no restart or
Supervisor reinstall was performed during the diagnosis. The full Node
repository suite for this corrected source reports `550/550 PASS`, and the
source-root policy guard plus repository secret check also pass.

The same census also explains the fourth ordinary active RUN
`037b642a187e4f098dc66e6dd1c9b3c1`. It was not created by a status poll or
background cleanup. A distinct ChatWeb task context explicitly invoked the
destructive/project-write `agent_workflow(phase="prepare")` at
`2026-08-29T23:52:54Z`, which intentionally created a durable `PREFLIGHT` RUN,
then ended after read-only commands without using exact-context
`task_control(action="stop")`. That caller action contradicted its own stated
"do not create RUN/WAVE" constraint. The RUN has zero controller lease, write
fence, live lane, managed job and background operation, but the current
controller is not authorized to forge the old task context or reconcile below
the supported 24-hour threshold. Its earliest stale-reconciliation time is
approximately `2026-08-31 06:53:20` Asia/Saigon. This is a caller lifecycle
contract violation, not evidence that a read-only status or census path
spontaneously creates RUN rows.

### Long-lived managed-Tunnel discovery correction — 2026-08-30

The unchanged rediscovery timestamp after the later real `Coding-VP Live`
refresh was not merely a model-binding limitation. Sanitized Tunnel chronology
shows that the official control plane forwarded `openai-mcp-discover` at about
`2026-08-30 03:10:30` and again at `06:27:17` Asia/Saigon for the same exact
activation epoch, MCP process/server identities and contract SHA. The first
request created the strict receipt at `2026-08-29T20:10:30.820587Z`; the second
request reached MCP but did not advance it.

The repository-side cause was a mismatch between producer and verifier
semantics. `tunnel-client` supports one static `--mcp.extra-headers` value for a
managed Tunnel lifecycle, while the MCP verifier expired that same HMAC after
15 minutes. Legitimate discovery on a long-lived exact process was therefore
served but downgraded from `attested_transport` with `timestamp_expired`, so it
could not update the authoritative receipt. The source now models the primitive
truthfully as a lifecycle-bound capability: it retains HMAC-SHA256, exact
client/epoch/process/server/contract binding, future-timestamp rejection,
tamper rejection and secret rotation on MCP replacement, but does not expire an
otherwise exact live-lifecycle capability solely by wall-clock age. Direct
regressions prove that an exact 24-hour-old capability remains valid, while
cross-epoch/process/server/SHA replay, secret rotation, tamper and future
timestamps remain rejected.

The Tunnel launch contract is also covered directly: the attestation reference
appears only under `--mcp.extra-headers`; local
`--mcp.discovery-extra-headers` probes receive no attestation and cannot
manufacture a ChatWeb receipt. Recovery Host now ignores even an exact
compatibility `workspace_context` bootstrap when deciding whether to wake the
strict final-census/finalize path. Bootstrap leaves the epoch
`VERIFYING` / admission `CLOSED`; only an exact managed-attested current-tuple
`tools/list` or `server/discover` receipt can lead to strict ACK and
`READY` / `OPEN`.

Focused source proof for this correction is `42 passed, 4 subtests passed` in
the Python connector/protocol/HTTP/activation suite and `213 passed` in the
affected Node Tunnel/lifecycle/full-clean/Recovery Host/development-status
suite. Module-size budgets and `git diff --check` pass. These results prove the
dirty source behavior only. A read-only `npm run dev:status` at the end of the
wave reports `state=MISSING`, `host=unavailable`,
`error_code=RECOVERY_DESCRIPTOR_STALE`; no live process has loaded this fix.
The status line now labels its legacy revision fields
`revision_scope=electron_ui` and separately reports Coding MCP revision,
aggregate readiness and snapshot freshness, preventing a UI `CURRENT` result
from being misread as whole-stack currency. No restart, activation, connector
ACK, commit, push, package, release or deployment was performed by this source
correction.

### Strict discovery authority hardening and live recapture — 2026-08-30T07:22:22Z

The current dirty source now closes the remaining authority gaps around MCP
replacement and connector projection. Every epoch-bound Native/Python launch
normalizes to admission `closed`; explicit `open` or unknown gates are rejected.
Durable epoch authority that is missing or unreadable fails closed before
process mutation, and `READY_COMMITTED`, `READY`, or `FAILED` epochs cannot be
reused for another MCP spawn. A direct eligible MCP replacement rotates the
attestation secret and replaces the dependent Coding Tunnel with an attestation
bound to the new MCP epoch/process/server/contract tuple; failure to rebind the
Tunnel rolls the new MCP back. Live connector projections compare discovery,
contact, and bootstrap receipts to the exact health tuple, so a receipt from a
retired process cannot be presented as current. Detached hash/synchronization
helpers no longer persist an acknowledgement; the mutating path requires the
complete current health receipt.

The final core affected Node packet is `239/239 PASS`, and the broader lifecycle
packet is `340/340 PASS`. The focused Python activation packet is `9/9 PASS`
with `2` passing subtests; JavaScript syntax, Python compilation, and
`git diff --check` also pass. This is source proof for the dirty worktree, not
loaded-runtime or delivery proof.

A read-only `npm run dev:status` recapture reports `state=CURRENT` and
`host=available` for Electron UI, with its running/disk revisions equal and
`update_pending=false`. Coding MCP is still the older loaded source:
`mcp_revision_state=update_pending`, running revision
`23b6aa33d59083a9706289a4d4cdbf261b84cebe1a59d758d903079e0e3101af`, disk
revision `84f0f941c46386812746d0b6f3bcace449475b5106551c980e0be476d68da800`.
Therefore `components_ready=false`, `fully_ready=false`, and
`runtime_update_incomplete=true`. Connector state is
`UNCHANGED_COMPATIBLE_NEEDS_ACK` with `connector_rediscovered=false`, no
rediscovery timestamp, `connector_ack_pending=true`, and
`connector_refresh_required=false`. The last field does not cancel the pending
strict gate. This recapture supersedes older live-looking receipts above only
for current process state; it does not rewrite their historical chronology.
No restart, activation, connector ACK, commit, push, package, release, or
deployment was performed in this hardening wave.

### Source validation update — 2026-08-27

Before the automatic endpoint-identity packet below, the then-current uncommitted source fingerprint had a green Node repository suite (`482/482`) and a green complete Coding Tools MCP result (`698` tests, `4` environment-conditional skips, `106` subtests), including the focused full-clean/activation, acceptance, orchestration, PRL, and projection packet (`120` tests, `1` skip, `43` subtests). The newer endpoint packet has focused source proof for installation separation, workspace-generation invalidation, stateless discovery metadata, unchanged tool-contract SHA, and Python compilation. These remain source-level results only; they do not establish current-process connector discovery/ACK, controlled activation, package, release, deployment, or production readiness. Live process-refresh evidence remains a separate receipt.

At `2026-08-27T16:37:26Z`, a controlled `npm start` process refresh from this
checkout exited successfully after replacing Recovery Host, Coding MCP, Coding
Tunnel, Recovery MCP, Recovery Tunnel, and Electron UI. The replacement Coding
MCP (`pid=20916`, component revision
`c6f1c2f2bb0c92ff46a5e3002cb58b9c358af9d4b27f7d3fd4b057661e29bd92`)
and Coding Tunnel (`pid=21484`) were both ready; the former stopped-runtime
`ORCHESTRATION_STATE_UNCERTAIN` refusal did not recur. The durable activation
epoch `activation-mtbqsh83-094c596a51df8d2f827d01936dbda21a` remains
truthfully `VERIFYING` with admission closed because the real external client
has not yet produced current-process discovery for tool-contract SHA
`57ed56a4f008287d9d9fdef035fa248f91cce4d58e935280b28963e4126a8053`;
the retained acknowledgement names older SHA
`3e37f9fed85bd80f46ee79a820291f617584b6b6ba65b43c16f163adf37993fd`.
This is live component/process proof, not connector ACK, `LIVE_CLOSED`, package,
release, deployment, or production proof.

### Live reconciliation — 2026-08-26

The Recovery Host receipt captured at `2026-08-26T02:06:12Z` for `E:\DEV\Codex-web` remains historical live evidence for that loaded process. It reported the then-existing component-local `fullyReady=true`, Coding MCP `running_revision == disk_revision == cbcab4d0e5382431d1193724c7e13c128de319bceea7baae2e617a05decc3db5`, and the exact eight-tool `smart-v3` contract SHA `fb159d403ef490caeb29b1b54111c2b0353a7544bb2ecad564cfec3b2f878585`. It simultaneously reported `connectorRediscovered=false`, `connectorRediscoveredAt=null`, `connectorRefreshRequired=true`, with acknowledged SHA `34cbb4c3ce3668f86ef6340dcb210d07425814c40ba734180ee1c026c96d409c`. Under the maintained aggregate readiness contract below, that tuple is `UPDATE_INCOMPLETE` and must project `fullyReady=false`; the historical green field is not current activation authority. Focused transport/stateless/fault validation was green (`22/22`), the SDK contract/exception boundary was green (`8/8`), and an HTTP-level `tools/call` regression confirmed raw `ExceptionGroup` text could not escape the JSON-RPC boundary (`6/6`). A model-text inventory or ordinary `tools/call` cannot replace real current-process `tools/list`/`server/discover`, official acknowledgement, or C4 natural evidence.

## 2. Current product boundary

The product currently operated from this repository is the **Windows Electron Execution Hub + Coding Tools MCP** stack. The repository still contains substantial WebCodex Rust/server/runner functionality inherited from and developed beyond the upstream project; that code is a foundation/subsystem, not the only description of the desktop product.

```text
ChatWeb / ChatGPT
      |
      | MCP over primary tunnel
      v
Recovery Host / Execution Hub authority
      |
      +--> ONE Coding Tools MCP Runtime -----> workspace / Git / commands / proof
      |            ^
      |            |
      |       Codex Desktop thin stdio proxy
      |
      +--> Electron Execution Control Center
      |
      +--> independent Recovery MCP + Recovery Tunnel

Secondary reasoning/provider lanes:
  Codex App Server / OpenCode -> bounded candidate, review, or read-only provider work
  Coding Tools MCP / EOCL      -> mutation, proof, durable ledger, acceptance boundary
```

There must not be two peer Coding Tools runtimes independently mutating the same workspace/ledger. ChatWeb and Codex Desktop share the Execution Hub truth; they do not synchronize transcripts.

## 3. Current `smart-v3` MCP contract

The current `smart` profile intentionally exposes exactly these eight public tools:

- `workspace_context`
- `agent_workflow`
- `task_control`
- `document_workflow`
- `exec_command`
- `command_control`
- `request_permissions`
- `view_image`

### Automatic installed-endpoint identity (source contract)

Every Electron installation already creates a durable random `device_id` and
passes it, the current Recovery Host instance, and the OS display name to Coding
MCP. Coding MCP now derives a non-secret `endpoint_id` and collision-resistant
`route_key` automatically from that installation identity, while each canonical
root retains its separate content-free `workspace_id` and
`workspace_generation`. A standalone MCP process that has no Electron-provided
device identity falls back to a workspace-scoped endpoint identity rather than
collecting an implicit hardware fingerprint.

Legacy initialize, authenticated stateless responses, `server/discover`, and
`workspace_context` expose the same endpoint projection. The public unauthenticated
server card remains generic and never exposes device/workspace identity. The dynamic server title
includes the detected device display name and current workspace; routing
instructions tell the client to reuse the endpoint already pinned to the task
instead of probing peer Coding Tools connectors just to compare identities.
Process/server/activation fields remain freshness invalidators, and mutation must
never silently fail over to another endpoint. Dynamic endpoint metadata is kept
outside the eight-tool schema, so installing the same build on another machine
does not create a machine-specific `tools/list` SHA or unnecessary contract ACK.

This removes any requirement to configure labels such as Home/Office manually.
A first installation still requires the operator to select/authorize a workspace
and supply its separately created Tunnel ID and runtime credential; those are
authorization inputs that cannot be inferred safely from hostname or local disk.

### BOOT_HOST_TRANSITION_RECONNECTION_LOOP — working-tree source fixed / current-device live pass

The remaining implementation packets, acceptance matrix, and closure boundaries
are defined in [the detailed closure plan](BOOT_HOST_TRANSITION_CLOSURE_PLAN.md).
That plan is not a claim that the whole product problem has been closed.

This product problem tracks repeated manual repair, refresh, login, or connector
recovery after a same-device cold start or after returning on a device that
skipped one or more compatible releases. Account session, endpoint/workspace
identity, and connector-contract acknowledgement remain three separate layers:
the Electron ChatGPT view uses the durable `persist:chatgpt-session` partition;
each installation keeps its own device-bound endpoint identity; and connector
freshness stays bound to the exact current process, server, activation epoch,
workspace generation, and public contract SHA. A new device may still require
one real account login and separately provisioned local credentials. Credentials
or mutation authority must never be copied or silently failed over between
devices.

The Problem is closed only when all of the following are demonstrated:

- a same-device cold boot reuses a non-revoked ChatGPT session and the saved
  workspace/device identity without source repair or repeated refresh;
- Recovery Host, Coding MCP, and the device's own Tunnel start or recover into
  the exact configured workspace, with admission opened only after the guarded
  connector path completes;
- a client that skipped one or more reviewed additive releases can bootstrap
  through the reviewed compatibility closure, while a breaking or unknown
  contract still requires real discovery;
- a new device asks for account login and local credential/workspace setup only
  when they are genuinely absent or revoked, never by copying another device's
  token or authority;
- Coding-VP Live and a separately tunnelled Coding MCP remain distinct routes,
  and no write-capable task silently fails over between them; and
- focused cold-start/skipped-version/two-device tests plus an installed Windows
  logon smoke pass for the exact release candidate.

The `ae04947` public contract changed from `d52c889...` to `d69436c...` by adding
only optional `candidate_cursor` and `candidate_limit` fields to
`task_control.goal_event` plus a descriptive pagination update. The committed
source omitted the reviewed compatibility edge and retained the stale exact-SHA
test, so an already acknowledged client correctly fell into
`CHANGED_NEEDS_DISCOVERY`. The current working tree now records the reviewed direct
`d69436c... -> d52c889...` edge and publishes the deterministic transitive
closure of the existing reviewed additive-edge graph. This lets a device skip
multiple compatible releases without manual per-release discovery. Unknown or
malformed hashes and any reachable graph cycle return no compatibility; an
undeclared or schema/profile-changing contract still requires real current-
process `tools/list` or `server/discover`.

Compatibility metadata alone never opens admission. The narrow bootstrap still
requires an attested ChatWeb `workspace_context` contact with no workspace read,
matching current contract/process/server/epoch identity, and the final activation
census independently requires the exact device and workspace binding. Focused
Python tests cover exact SHA, multi-hop order, unknown hashes, malformed edges,
and cycles. Electron tests cover skipped-version acknowledgement plus negative
process/server/epoch/client/workspace-access cases, while the existing connector
binding and full-clean suites retain their independent fail-closed gates.

The controlled development refresh captured on 2026-09-14 completed epoch
`activation-mu0nwtkj-5b558ae4a52562fb6c739de983b52912` as `READY`, with
MCP and Tunnel ready, admission open, `fully_ready=true`, and
`CURRENT_COMPATIBLE_ACKNOWLEDGED`; both current and acknowledged contract SHA are
`d69436cabfbb6dca7b365df507f4b507857d9b29c11a44883fab77de54f67810`.
This is a current-device development live pass, not an installed Windows logon,
two-device, package, release, deployment, or production claim. Those boundary
smokes remain required before closing the whole cross-machine product problem.

### Authorized-root workspace projection (source contract)

When the Runtime has more than one authorized root, `workspace_context(path)`
canonicalizes the requested root and reports that root's `workspace_id`, project
metadata, Git summary, and task projection. The task projection is loaded from
the selected root and current MCP execution context; it never falls back to the
primary Runtime task or to another project. A context that has been bound by a
workspace read cannot be rebound to a different root (`TASK_CONTEXT_WORKSPACE_MISMATCH`).
Mutating public calls without an explicit path/workdir or an already-bound task
context fail closed with `WORKSPACE_TARGET_REQUIRED` when multiple roots are
authorized. This is source and focused-test proof only; it does not by itself
prove controlled live activation, packaging, release, or production readiness.
The binding is persisted as server-derived state in
`.coding-tools/orchestration/task-context-workspaces.json`; after Runtime
restart the canonical root, current authorization set, and content-free
`workspace_id` are revalidated before reuse. Missing, malformed, legacy, or
unauthorized mappings fail closed as `UNKNOWN_LEGACY_WORKSPACE`,
`WORKSPACE_NOT_AUTHORIZED`, or `WORKSPACE_SCOPE_INCONSISTENT`.
Handoff capsules include the bound workspace identity, authority transition,
source/diff fingerprints, lease/delegation IDs, bounded dirty paths, proof IDs,
and unresolved-risk projection; they do not replace the canonical ledger or
carry transcript/raw command output.
The repository also has a public stateless-HTTP matrix that binds two temporary
workspace roots, creates separate task/run projections, rejects cross-workspace
`task_control`, then recreates the Runtime and verifies the authorized context
and task projection are restored.

`restart_runtime` is an action of `task_control`, not a ninth public tool. The runtime publishes a deterministic contract fingerprint and tool count so Electron can detect a stale ChatGPT connector schema.
The action is a deferred post-tool-call full-clean request: MCP returns a short-lived
ticket after fencing the exact operation, and Recovery Host later consumes the
same ticket ID as the full-clean operation ID. Recovery Host revalidates the
ticket's workspace/process/server identity and resolves source authority only
from the current accepted closure; it never treats the ticket itself as a
checkpoint. The signed Recovery Host census may reuse that exact fence identity,
but it does not discount the initiating active tool call. It returns
`RUNTIME_BUSY` and keeps the `.processing` journal until the MCP active-call count
is actually zero, then retries the same operation. This proves the caller has
left its tool boundary before process mutation while preserving fail-closed
checkpoint authority.

Runtime activation has two explicit modes. `soft_recovery` remains component-scoped
for automatic local fault recovery (for example, a dead Tunnel or a crashed MCP)
and is revision-continuity guarded. When the durable epoch is eligible for an
in-place replacement, repeated semantic MCP failures replace the exact owned
MCP process and restart only its dependent Coding Tunnel process so
the managed attestation is rebound to the new MCP process/server tuple; Tunnel
configuration and the Recovery Host/UI/Recovery Plane stay in place. The MCP
replacement is stopped again if disk revision drifts across its spawn boundary.
This path is legal only while durable epoch authority is readable and
nonterminal. `READY_COMMITTED`, `READY`, and `FAILED` epochs cannot be reused for
another MCP spawn, even with a closed gate; a new full-clean epoch is required,
and missing/unreadable epoch authority fails closed before Native or Tunnel
mutation. Operator `restart`, accepted code/revision
activation, and controlled updates use `full_clean_activation`: a durable
`activation_epoch_id` is created, admission closes, durable state is checkpointed,
Electron UI/Coding Tunnel/Coding MCP and configured Recovery MCP/Tunnel are stopped,
and a replacement Recovery Host starts fresh processes with the same epoch. The
epoch remains `UPDATE_INCOMPLETE` until a final current-process census verifies
workspace, persistent device identity plus fresh lifecycle instance identity,
disk/runtime revisions, process/server/supervisor identities, real tunnel health,
UI and Recovery Plane identities, and a fresh connector discovery/ACK. For the
deferred `task_control` route, Recovery Host performs that ACK itself only after
the exact post-preflight health receipt binds `tools/list`/`server/discover` to
the current epoch, process ID, server ID and contract SHA; persisted hashes,
compatibility-only contact and ordinary `tools/call` are insufficient. Only a
verified `READY` epoch with `admission_open=true` may report `fullyReady=true`.
The ledger, task history, acceptance state, settings, secrets handles,
authorized roots, and device identity are never deleted by this transaction.

The development `npm run dev:refresh` command treats exact process refresh completion and
connector acceptance as separate observable boundaries. It exits successfully
after the new Recovery Host, Coding MCP/Tunnel, Recovery MCP/Tunnel and Electron
UI have passed their exact identity/epoch/revision/health/projection census. If
real-client discovery has not happened yet, the durable epoch remains
`VERIFYING`, admission remains closed, and the CLI reports
`fully_ready=false connector=pending`; it does not wait until TTL and misreport
the completed process refresh as a startup failure. While only this external
connector gate remains, Recovery Host serves a bounded cached read-only runtime
snapshot and polls the MCP discovery receipt without repeating OS-identity and
Tunnel census probes every five seconds. Exact current-process discovery is the
event that re-enters the authoritative final census/ACK/READY transaction. The
watchdog persists that exact passing census while admission is still closed
before `finalize()` performs its independent census. If the otherwise valid
cached projection receipt crosses its five-minute TTL at this boundary, the
coordinator rebuilds the projection and captures a new health receipt; workspace,
ledger, process, server, epoch or receipt-integrity mismatch still fails closed.

When a failed activation left Coding MCP stopped, an explicit retry is admitted
only after Recovery Host obtains an independent immutable/query-only
Backup-API ledger census, validates quiescence and unresolved-acceptance gates,
and confirms the same census fingerprint on a second read immediately before
epoch creation while holding the application ledger gate exclusively through
the durable epoch-store create. A ledger hash, workspace, source-checkpoint, or runtime-state
identity change fails closed before any process stop; the durable ledger and
the failed epoch remain untouched.

Because background workflows are process-scoped, a stopped-runtime census does
not treat an old `running` row as live forever. Rows with a parseable activity
timestamp older than the census grace window are retained as stale residue and
the replacement runtime marks them orphaned during startup. Managed-process
rows are likewise restart-reconcilable only when an exact OS identity probe
proves that the original PID is gone or has been recycled. Recent or malformed
background evidence, a live matching process, an unverifiable process identity,
leases, fences, live lanes, projection drift, and integrity failures still
block activation.

Contextual task files are current views, not a complete index of historical
RUNs. An `AWAITING_ACCEPTANCE` RUN with a valid canonical wave/state, no live
ownership and activity older than the census grace window may have no remaining
context binding without causing `PROJECTION_DRIFT`. The read-only census reports
this as `unprojected_historical_acceptance_count`; the RUN remains active and
awaiting acceptance. The separate acceptance gate still blocks accepted-code
activation unless the existing explicit process-refresh policy preserves pending
acceptance. Fresh missing bindings, present-but-conflicting projections and live
ownership remain fail-closed. Stopped-runtime refusals include the bounded census
`reason` in the CLI error instead of discarding it at the bootstrap boundary.

Low-level/legacy tools may still exist in compatibility or non-smart modes, but new agent workflows should prefer the compact smart surface.

## 4. Authority, EOCL, routing, and handoff

`agent_workflow` is the primary end-to-end coding path. Mutation/proof workflows are governed by the EOCL state machine and durable orchestration ledger. A successful command or green test does not by itself equal final acceptance; an `ACCEPTING` wave still requires the authorized semantic controller to accept or reject it.

Bounded RUN continuation has two explicit consent adapters over the same exact descriptor contract. The embedded Electron ChatGPT view can stage its existing one-shot DOM-observed command receipt. An attested external ChatWeb controller that cannot produce that Electron event instead receives a short-lived loopback approval URL: its fragment token is process-local and absent from HTTP request targets/logs, the page renders the exact RUN/WAVE/workspace/epoch/fingerprint/scope/check/budget terms, and an explicit local button press grants and starts only that continuation. The endpoint rejects forwarded/tunnel-shaped traffic, controller transfer, runtime or WAVE drift, expiry, and replay. Neither a generic visible turn nor a copied descriptor grants background authority, and final acceptance remains controller-owned.

For a selected read-only review, `agent_workflow(phase="prepare")` also accepts an optional `committed_review` object. It requires exact local 40-hex base/head commits, computes an explicit local merge-base range, disables external diff/textconv and system/global attributes, bounds and redacts returned evidence, and signs any continuation to the immutable range. It adds no ninth MCP tool, cannot run in a mutation/resume phase, does not fetch history, and does not itself establish execution or acceptance evidence.

For ordinary context collection, `agent_workflow` phase `prepare`/`run` exposes the existing bounded context controls and forwards them unchanged to `prepare_coding_context`. The public `smart-v3` surface remains exactly eight tools; this does not create a second index or authority.

The split `prepare -> execute` path is explicitly lineage-bound. `prepare` returns `prepared_binding.run_id` and `prepared_binding.wave_id`; callers should pass both values to `execute`. The runtime requires the pair to match the caller-scoped current `PREFLIGHT`/`READY` prepare lineage and fails closed before creating a new RUN or write lease when a refined execute objective omits or mismatches that binding. The prepare RUN objective remains the immutable authority; an execute objective is only a narrower implementation plan.

Current authority rules:

- ChatWeb/Sol remains the normal semantic controller and final-acceptance authority for coordinated work.
- Electron/Recovery Host owns service lifecycle and secrets.
- Coding Tools MCP owns deterministic workspace mutation, verification, durable task/run/proof state, and write fencing.
- Codex Desktop is a second client of the same Runtime through the thin proxy; controller transfer is explicit and does not automatically grant a repository write lease.
- Codex App Server and OpenCode are secondary lanes, not an independent authoritative writer of the primary checkout.

### Routing policy currently in force

Supported explicit routes include `deterministic`, `mini`, `luna`, `terra`, `sol_xhigh`, `sol_max`, and `sol_ultra`. However, **`execution_route=auto` is currently fail-closed to `deterministic`** while representative accepted paired evidence is insufficient. The runtime reason is the ROI/evidence gate, not an inability to invoke the other routes.

Consequences:

- do not describe Mini/Luna/Terra/Sol as automatically selected in production today;
- non-deterministic lanes are explicit/evaluation lanes until the accepted representative cohort gate changes;
- `sol_max` and `sol_ultra` still require explicit high-cost acknowledgement;
- provider traffic/capacity telemetry does not itself authorize automatic routing;
- OpenCode automatic routing remains off/evidence-gated;
- automatic global server-first compute placement remains off until representative P3 evidence supports promotion.

Auto-handoff is also kept off until enough representative real-task A/B evidence shows a stable benefit without state loss or duplicate work. Durable handoff capsules remain available for rollover/recovery.

## 5. Runtime evidence and measurement

For repository-local evaluation and postmortems, the durable orchestration ledger is the canonical causal source:

```text
.coding-tools/orchestration/ledger.sqlite3
```

Supporting projections include `.coding-tools/performance.json`, `.coding-tools/task-history.json`, and `.coding-tools/task-state.json`. These are runtime evidence, not source-code inputs, and must not be folded into source/worktree fingerprints.

Current measurement policy:

- distinguish provider-reported/measured tokens, cost, and timing from estimates;
- never present internal estimated credits as provider billing;
- keep representative, benchmark, and synthetic evidence separate;
- do not promote routing or placement from small or synthetic samples;
- host-visible latency claims require an explicit host observation bound to the exact EOCL run/wave, not timestamp proximity.

### Accepted-Result Economics measurement layer

The current source adds a read-only Accepted-Result Economics layer on top of the existing canonical ledger and performance projection. Its operating North Star is:

> **Minimize Accepted-Result Economic Loss under fixed quality, security, authority and correctness floors.**

The decision order is deliberately lexicographic rather than a single blended score:

```text
quality floor
  -> first-pass outcome
  -> restricted TTAR p90
  -> accepted-result resource cost
  -> human/operator burden
  -> simplicity
```

`npm run report:accepted-result-economics` is read-only. It reports accepted deterministic representative runs, bounded retained per-run resource telemetry, first-pass versus repaired resource distributions, top-tail workflow forensics, proof-cache economics, monetary/token coverage, and an exact-HEAD DRE window for `source_base_drift` and `acceptance_correction`.

Evidence semantics are fail-closed:

- missing money/tokens/resource observations remain **unknown**, never zero;
- monetary CAR remains unavailable until accepted-result monetary-cost coverage is complete;
- `estimated_wait_ms` is the capped gap between consecutive MCP tool calls and may include controller/model/network/operator time; it is **not** proven avoidable loss and is **not** provider billing;
- bounded `performance.run_metrics` retention means an observed resource subset is descriptive and its coverage must be reported rather than silently extrapolated to every accepted run;
- historical DRE counts identify mechanisms, but only natural accepted work on an exact clean current source revision may justify another current hardening wave;
- a low proof-cache hit rate is measurement evidence, not by itself a reason to build a new cache architecture.

P5 source now carries the same economics boundary. Promotion requires accepted-result resource economics and resource-overhead noninferiority; monetary-cost noninferiority is required when complete monetary coverage exists. No missing cost is converted to zero and no partial resource vector is relabeled as monetary CAR. P5 remains explicit, gated, arm-neutral before assignment, and non-automatic.

The current host-observation path uses content-free identities (`turn_id`, `trace_id`, `span_id`) and explicit run binding; prompt/response text is not copied into the correlation record.

## 6. P0-P3 closure and evidence boundary

The P0-P3 program is no longer one undifferentiated implementation gate. Engineering closure, live activation, and representative efficacy are tracked separately so an evidence program cannot silently reopen accepted architecture and a source fix cannot be mistaken for a running-process acceptance.

| Phase | Engineering/source | Live / evidence boundary | Current interpretation |
|---|---|---|---|
| P0 — runtime truth/error boundary | **CLOSED (source)** | **Historical live receipt; current connector discovery blocked** | ExceptionGroup normalization and self-recovery hardening are implemented. The 2026-08-18 connector acceptance is retained as `VERIFIED_SNAPSHOT`; the current process still requires its own real-client `tools/list` or `server/discover` receipt before connector acceptance can be current. |
| P1 — measurement integrity | **CLOSED** | **ECONOMICS DEFERRED** | Controlled plumbing is sufficient for experiments. Missing controller/provider usage or money remains unknown, never zero; it does not authorize automatic routing. |
| P2 — rework diagnosis | **CLOSED** | **CAUSAL EFFICACY DEFERRED** | The diagnostic phase identified rework as a material cost. Generic `CHECK_FAILED` and `BUILD_VERIFICATION_FAILED` observations now receive prospective, content-free stage/family detail; historic rows without that detail remain unclassified rather than being backfilled into a causal repair cause. Incomplete historical causal/oracle coverage is a measurement limitation for later experiments, not a reason to expand P2 architecture indefinitely. |
| P3 — compute-placement control | **CLOSED / ACCEPTED** | **REPRESENTATIVE EFFICACY DEFERRED** | Explicit placement control is implemented; the representative 10–20-pair pilot remains separate and global server-first stays off. |

The P0 **live activation acceptance** below was satisfied on 2026-08-18. The program may move to a new engineering roadmap item while P1/P2/P3 evidence programs continue in parallel without reopening their closed implementation waves.

### P4 — Solution Economics Shadow — SOURCE/GATE ACCEPTED / EVIDENCE COLLECTING

P4 engineering is now split into three explicit boundaries: source contract, live collection health, and empirical predictive readiness. Current source provides the shadow evidence path for `feature` and `bugfix` runs:

- one task-level recommendation is recorded before the first `write_lease_acquired` event;
- recommendation evidence is structured and content-free: candidate scope, estimated touched surface, root-cause confidence, oracle strength, expected repair risk, and smallest causal solution scope;
- the recommendation is joined after execution to durable accepted-result evidence including first-pass acceptance, repair/replan count, TTAR, accepted file receipts, proof duration, explicit local/wait observation spans, and explicit manual-fix outcome when available;
- lines/symbols touched, cost, wait, or intervention remain unknown when they were not actually observed; absent telemetry is never converted to zero;
- representative rows alone are eligible for predictive promotion; benchmark, synthetic, and unlabeled rows remain descriptive evidence only;
- predictive validation requires representative terminal outcome variation plus positive leave-one-out Brier gain and Bonferroni-adjusted Wilson interval separation; the result remains association evidence, not a causal treatment claim;
- LOC/touched surface remains an explanatory variable, not the optimization target.

P4 does **not** add another public MCP tool and does not change routing, model choice, compute placement, write authority, proof policy, acceptance authority, or production mutation behavior. `solution_shadow` is an action inside `task_control` on the existing eight-tool `smart-v3` surface.

The development supervisor has also been hardened so development Coding MCP launches are pinned to the current Electron checkout (`appRoot/resources/coding-tools-mcp`), with that module root first in `PYTHONPATH`, used as `cwd`, persisted as launch provenance, and mismatches refused rather than silently reusing a foreign/stale runtime.

The population/readiness window is fail-closed against unrelated run churn. `solution_shadow_population_report` now selects the latest enrolled shadow runs directly (`population_scope=latest_shadow_runs_v2`) instead of selecting the latest generic runs and filtering afterward. This prevents diagnose/telemetry workload from evicting genuine P4 evidence from the analysis window.

Repository operators can evaluate the canonical committed ledger with:

```text
python resources/coding-tools-mcp/scripts/report_p4_readiness.py --workspace .
python resources/coding-tools-mcp/scripts/report_p4_readiness.py --workspace . --require-ready
python resources/coding-tools-mcp/scripts/report_p4_readiness.py --workspace . --require-p5-experiment-active
npm run check:p5-readiness
```

The manual-only GitHub workflow `.github/workflows/p4-readiness.yml` exposes the P4 gate without enabling ordinary push/PR Actions consumption. `--require-ready` succeeds only when `p4_gate.can_answer_which_signals_predict_repair=true`; missing or insufficient evidence cannot be converted into a green P4 closure claim. `--require-p5-experiment-active` is an observation assertion for an already explicit P5 epoch, not an activation command. `npm run check:p5-readiness` and the deprecated `--require-p5-ready` retain the legacy P4-predictive treatment readiness meaning and must not be used to claim P5-A0 integrity readiness.

**The 2026-08-19 live collection receipt is historical (`VERIFIED_SNAPSHOT`), not a current P4 outcome.** At that snapshot the ChatWeb/Coding-VP plane exposed `task_control.solution_shadow`, exactly 8 `smart-v3` public tools, contract SHA `bd5c09aeffe02bb60d0f548ed02912e8a21e78b91404186e6896f6d6cbdedd70`, and no reported stale/orphan residue. A later process had a genuine rediscovery and official acknowledgement, but the newest target-process snapshot requires fresh real-client discovery again; neither receipt proves a current `solution_shadow` call or P4 outcome. Source support and later natural evidence remain separate gates.

The P4 empirical gate remains **COLLECTING unless the canonical ledger reporter says `EMPIRICALLY_COMPLETE`**. The 2026-08-19 snapshot (9 representative terminal shadow tasks, 0 representative causal-solution repairs, and `validated_signals=[]`) remains historical evidence that predictive validity was not established; it must not be reused as an activation proof for later source. P4-C therefore remains strict/shadow-only and P4-E remains coverage-first/advisory-only.

**Current P4 readiness (`VERIFIED_CURRENT`, descriptive) remains `COLLECTING`.** The immutable canonical-ledger report captured at `2026-08-29T14:19:17.492306Z` contains `99` representative terminal shadows: causal-solution repair `n=1`, nonrepair `n=72`, and repair-unknown `n=26`; raw post-replan patched observations were `n=26`. `validated_signals=[]`, `p4_empirically_complete=false`, and predictive-policy activation remains false. The source implementation exists, but the upstream-matched P5 baseline is not ready because code-bearing source is dirty. These imbalanced labels do not establish a prediction effect or causal intervention result. The current connector now has the attested current-process discovery receipt recorded above, but that connector pass is not a P4 outcome and does not authorize automatic policy, P5 treatment, or routing.

P5 has a separately gated **source implementation**: manifest v2, secret-handle seed commitment, pre-assignment arm-neutral eligibility/enrollment, restart-safe block randomization, immutable all-assigned ITT outcome rows, analyzer/source-identity checks, and pause/close/hard-stop controls are exposed as `task_control(action="p5")` inside the unchanged eight-tool `smart-v3` surface. A write-capable `agent_workflow` can carry `p5_assignment_id` only for the immutable `feature`/`bugfix` task class; after the ordinary workspace fence is acquired and before any mkdir/patch call, the runtime records an immutable P5 pre-write binding to the exact run, wave, and lease. Caller-supplied first-write time is rejected. The feasibility analyzer projects the complete durable funnel (`assessed → eligible → enrolled → assigned → protocol started → pre-write binding/first-write record → terminal → immediate quality → delayed follow-up/interference`) by assigned arm and workflow stratum. It verifies completed 2/2 block shape and exact table joins instead of pretending that a low-power canary SRM p-value proves randomization; completed-block mismatch, orphaned rows, arm crossover, or a write-binding/first-write mismatch hard-stops a live epoch. Incomplete live blocks are reported as pending, not claimed as imbalance. It does not loosen P4-C or require P4 predictive readiness before a P5-A0 instrumentation epoch. An operator must still explicitly open a frozen, source/runtime-matching manifest, with a clean upstream-matched control-plane source when the manifest requires it and with no active workspace write fence. `p5_automatic_start=false`, `automatic_policy_activation=false`, and automatic production promotion remain invariants. No source proof substitutes for a live P5-A0 A/A epoch, a P5-A treatment canary, an efficacy conclusion, or promotion.

For a development Electron runtime, the trusted parent process may receive `CODING_TOOLS_P5_A0_SEED` only from an external secret-delivery channel during a fail-closed controlled restart. The helper immediately writes that one-time value to Electron `safeStorage` under the `p5A0Seed` SecretStore entry; every normal start, primary-MCP recovery, controlled restart, and code activation reads that encrypted entry and maps it to the opaque `secret://experiment/p5/a` broker handle. Native launch deliberately omits the raw environment name from the child MCP environment and refuses to fall back to it when no SecretStore seed is present, so an incidental restart cannot change experiment identity. Do not place the raw value in the repository, tracked `.coding-tools` evidence, manifest, chat, or ordinary application settings; restart-safe live provisioning remains an operator/runtime operation, not source evidence. The MCP-only controlled-restart helper is fail-closed: it requires exact non-empty `--expect-app-root`, `--expect-workspace`, and `--expect-user-data` identities; binds its RuntimePaths to that verified development product root; then verifies the persisted `nativeDeviceId` and `nativeDeviceInstanceId`, before reading the secret store or terminating a runtime PID.

P5 source identity is the latest code-bearing commit of `HEAD` and upstream, excluding `.coding-tools/**`; evidence-only commits and live runtime projections remain mandatory Git history but do not create a false source-drift event. Any actual source-code commit still requires a new frozen P5 epoch before enrollment or assignment.

The P5-A0 operator path is intentionally narrow. The runtime can prepare a production A0 manifest only from the current code-bearing source/upstream identity, loaded eight-tool runtime contract, a material content-free environment fingerprint, the deterministic analyzer identity, and the SHA-256 commitment of `secret://experiment/p5/a`. `prepare_a0` is read-only and never opens an epoch. `open` rechecks source, runtime, analyzer, environment and writer quiescence, so a prepared manifest cannot be reused across environment drift. The production A0 horizon is four hours. Electron exposes only `status / prepare / open / analyze / pause / resume / close / hard-stop`; it keeps the prepared manifest in the trusted main process, never accepts raw seed material from the renderer, and exposes no P5-A treatment activation control. This remains shadow A/A instrumentation: both assigned labels receive the current control protocol and no automatic routing or promotion is enabled.

### P0 historical live activation incident — source CLOSED / prior receipt accepted

During an earlier 2026-08-18 closure check, every ChatWeb Coding MCP action attempted through that connected tool surface (`workspace_context`, `task_control restart_runtime`, and `agent_workflow`) returned a raw `ExceptionGroup: unhandled errors in a TaskGroup` before a normal typed tool result could be observed. The incident and the later acceptance are historical evidence for that source/runtime instance; neither establishes the identity or connector state of the current process.

Two source-side gaps are now addressed:

1. The MCP protocol boundary normalizes an `ExceptionGroup` into typed `ASYNC_TASK_GROUP_FAILED` JSON-RPC evidence instead of stringifying the raw group.
2. Recovery Host now has a throttled **semantic tool-plane watchdog**. It first performs a bounded five-second HTTP health preflight, then performs a read-only local `workspace_context` canary only when that health receipt is ready and reports no active command or snapshot contention. A transiently unavailable HTTP health response, or an MCP that is already serving work, skips the semantic canary and clears its semantic-failure streak instead of converting liveness uncertainty into a restart. Three consecutive eligible semantic failures are required before component-scoped MCP replacement. Recovery still delegates only through the existing `RuntimeOrchestrator.restart({ automatic: true })` lifecycle authority, and the watchdog is suppressed while the lifecycle controller is busy, recovering, handing off, or manually stopped. The canary does not create a second writer or recovery authority.

Focused source regression proves the semantic canary accepts a real `workspace_context` response, rejects an HTTP-200 raw TaskGroup JSON-RPC failure, skips while HTTP health is temporarily unavailable or the runtime is busy, restarts only after the three-failure threshold, and does not restart while the lifecycle controller is busy.

**Historical live acceptance (`VERIFIED_SNAPSHOT`).** On 2026-08-18 the then-connected instance demonstrated the accepted behavior on the real tool path:

- delivered/source HEAD `0cf1eec7366f09d52235ca235d92ccd8b3ea4e18` contains `beb2dc51` (protocol normalization) and `c7841920` (boundary regression) in its ancestry;
- the primary Coding MCP process observed as PID `18444` was created at `2026-08-18 15:28:53 +07:00`, after both P0 source commits, and runs `E:\DEV\Codex-web\resources\native-python\pythonw.exe -m coding_tools_mcp --workspace E:\DEV\Codex-web`;
- `workspace_context(detail=full)` succeeds through the real connector and reports the current source identity plus live `process_instance_id` / `server_instance_id`;
- `agent_workflow` prepare succeeds through the same live tool plane;
- `task_control` audit succeeds with hash-chain integrity PASS and quiescent execution resources;
- the live `smart-v3` contract reports exactly 8 public tools;
- focused ExceptionGroup boundary regression passes `4/4` from the Coding MCP component root;
- no raw `ExceptionGroup` escaped any of the live acceptance calls;
- the live runtime reported zero stale orchestration runs, unresolved stale runs, orphaned background operations, and orphaned idempotency records.

No Runtime restart was performed for this acceptance. A restart was unnecessary because the observed primary Coding MCP process itself started after the accepted P0 fix commits and then passed the live checklist. Future runtime-affecting changes still require their own source-versus-live activation proof; this acceptance does not collapse that distinction.

### P3 Engineering / Control Plane — CLOSED / ACCEPTED

The explicit validation compute-placement implementation is accepted at source commit `2c990332` (`feat: control validation compute placement`). P3 engineering is no longer a semantic roadmap blocker.

Accepted behavior:

- `compute_placement_policy = local_only | server_preferred` is available only for eligible long structured `cargo_check` / `cargo_test` validation.
- Explicit placement requires an Agent-backed project, no sandbox, structured asynchronous validation support, and a clean exact-source Runner checkout.
- Invalid explicit contexts fail closed before enqueue/process execution.
- `local_only` keeps execution on the source Runner and never selects server compute.
- `server_preferred` uses exact-source target selection and revalidation; if no valid target remains, execution safely falls back to the source Runner.
- Placement evidence records requested policy, actual placement, fallback, source Runner and executor Runner and is preserved through Job metadata, handoff/terminal result, `job_status`, and `job_log` projection.
- Omitting the selector preserves the established production behavior, including the pre-existing dirty-snapshot auto-offload path.
- Focused R3B2 integration regression covered server dispatch, local-only source execution, safe fallback, invalid-context pre-enqueue rejection, evidence projection, and selector-absent regression behavior before acceptance.

The preregistered analyzer remains frozen under the identity recorded in `docs/research/260818_P3_SERVER_FIRST_PAIRED_EXPERIMENT_MANIFEST.md`. Existing pilot outcomes must not be reinterpreted under an edited analyzer without a new manifest/version.

### P3 Representative Efficacy Pilot — DEFERRED

The frozen experiment `p3-server-first-pilot-v1` targets **10–20 genuinely eligible representative paired tasks**. Its purpose is instrumentation/variance/failure-mix/break-even/power planning before any confirmatory promotion claim.

This evidence program is intentionally separate from the engineering completion gate:

- it does not block moving to another engineering roadmap item after P0 live activation acceptance;
- it does not authorize claiming server-first is faster, cheaper, or better;
- it does not auto-promote global server-first;
- automatic activation remains `false`;
- missing controller/provider monetary cost is unknown, never zero;
- a confirmatory cohort is still required before broad promotion.

## 7. Recovery architecture

Persisted MCP/Tunnel PIDs are not live ownership proof across reboot or profile
migration. Stopped-runtime activation census and primary/Recovery service
lifecycle compare each PID with its OS process-start token. A verified different
token means the stored process has exited; census remains read-only and service
cleanup clears only the unchanged stale receipt, without adopting or terminating
the unrelated replacement PID. Missing tokens, malformed observations and
unavailable identity probes still fail closed. Device-ownership checks and legacy
Recovery migration apply only after the exact stored process is proven live.
The canonical ledger and durable history are never cleared to recover a PID.

Independent recovery is no longer only a roadmap concept. The current source contains:

- a headless Recovery Host that owns primary Runtime/Tunnel/Execution-Hub lifecycle;
- a Windows user-session Recovery Supervisor that resurrects the Recovery Host under bounded, fail-closed rules;
- a separate Recovery MCP process and, when configured, a separate Recovery Tunnel;
- a semantic Coding MCP tool-plane watchdog that can distinguish control-health success from failed `tools/call` behavior and delegates restart to the existing orchestrator;
- `recovery_plane_mode=independent_mcp_tunnel_v1` state;
- bounded `recovery_status` / confirmed `repair_primary_runtime` behavior rather than arbitrary remote shell/process control;
- controlled component activation and accepted-code activation gates.

The Recovery Tunnel must use a distinct tunnel identity from the primary Coding Tunnel. If a second tunnel resource is not configured, the independent local Recovery MCP may still exist while remote Recovery Tunnel status remains `not_configured`.

Development-startup note: the current checkout intentionally writes a bounded
`%LOCALAPPDATA%\\WebMcpRecoverySupervisor\\stop.request` sentinel only before an
actual development Recovery Host retirement/handoff or missing-host spawn when
the installed development Supervisor is not proven to match the current
app-root/executable identity, so another checkout cannot resurrect the wrong runtime.
Attaching an Electron UI to the already healthy exact-checkout Host must not
write this sentinel. The sentinel is operational suppression, not a health
result and not evidence of `blocked_live_owner`. After a development handoff,
re-enable supervision only through the supported
`npm run recovery:supervisor:install` installer for the exact current checkout;
it refreshes the installed script/manifest identity and removes the sentinel.
Packaged supervision has a separate installed identity and is not affected by
this development-only guard.

Implementation in source is not the same as a packaged/live proof. Recovery changes still require the relevant process-boundary, activation, packaged-Windows/login, and fault-matrix acceptance appropriate to the change.

The current checkout also has a repeatable isolated packaged-Windows Recovery lane: `npm run test:recovery:packaged`. It builds `dist/win-unpacked`, launches the packaged `--recovery-host` under a temporary Electron user-data root, proves device identity plus independent Recovery MCP, exercises the packaged Recovery Supervisor in healthy and fail-closed fault cases, cleans only isolated PIDs, and verifies that the production Recovery descriptor identity is unchanged. This is packaged runtime evidence, not publication of an installer and not a substitute for an actual installed-logon/session smoke when that boundary is required for release.

## 8. Semantic localization and LSP resource policy

Coding Tools MCP uses semantic-first localization when the native WebCodex LSP provider is available and falls back to bounded text search per query when semantic localization is unavailable, denied by resource admission, or cannot handle a query.

The current worktree also contains LSP process telemetry/resource-governance work: process instance identity, PID/start identity, current and peak working set, pending-request state, memory-pressure classification, restart/drain counters, bounded idle reaping, and soft/hard pressure behavior. Pressure policy is internal and testable; it must not be documented as one universal production memory number derived from a historical sample.

The P2/P3 LSP/resource hardening was technically closed on 2026-08-16. Its 10-cycle real Connector/Runner/rust-analyzer acceptance window recorded distinct process identities for every cold restart, final `STOPPED`, zero active HEAVY claim/write fence/stale run/orphan/overlap, and p95 peak LSP working set below 30 MiB on that Windows host. This host-scoped sample supports keeping the existing 2 GiB/3 GiB soft/hard defaults; it is evidence for that acceptance window, not a universal memory guarantee.

## 9. Validation, security, and release boundary

For ordinary changes, validate only the behavior changed. The current top-level entry points are:

```text
npm test
npm run test:mcp
npm run test:all
npm run test:recovery:e2e
npm run test:recovery:packaged
npm run canary:opencode-flash:preflight
npm run dist
npm run dist:dir
```

The paid/real provider canary `npm run canary:opencode-flash` may create external provider cost and must run only with explicit authorization for that cost. Its `:preflight` variant performs readiness validation without provider dispatch.

Runtime-affecting source changes need a separate activation/instance check after source tests. A release claim needs source proof, required live/process proof, exact accepted fingerprint, packaging checks, and rollback guidance appropriate to the component.

Account credential snapshots under `docs/ac/` are local-only data and must never be tracked. They have been removed from the current `main` tree and `/docs/ac/` is ignored. Credentials that were previously committed must be treated as exposed and rotated/revoked. Purging them from existing Git history is a separate destructive history-rewrite action and is not implied by ordinary cleanup commits.

## 10. Known evidence gates that remain intentional

The following are deliberate evidence/authority gates, not documentation bugs:

- P0 source activation and multi-workspace control plane: source implementation and earlier live receipts are retained, but no static documentation line is a current-process `LIVE_PASS`. The current local verdict is authoritative only when a fresh Recovery Host projection for the exact accepted checkpoint reports `closure_state=LIVE_CLOSED`; even that verdict is local runtime/control-plane evidence, not a package, release, deployment, or production claim;
- automatic non-deterministic routing: **OFF / deterministic fail-closed** pending representative accepted paired evidence;
- automatic global server-first: **OFF** pending representative compute-placement evidence;
- P3 representative efficacy: **DEFERRED**, separate from the closed engineering gate;
- P4 source/gate engineering: **ACCEPTED**; development launch authority is pinned to the current checkout and `solution_shadow` schema publication has been observed;
- P4 live tool-call health: the 2026-08-19 `solution_shadow` call remains **VERIFIED_SNAPSHOT**. The current target process requires a fresh discovery receipt before its connector status can be promoted, and P4 collection remains unobserved until a natural task actually records a P4 outcome;
- P4 predictive validity: **COLLECTING unless `report_p4_readiness.py` reports `EMPIRICALLY_COMPLETE`**; benchmark, synthetic, and unlabeled shadow rows are not promotion evidence;
- P5 experiment integrity source: **IMPLEMENTED / FAIL-CLOSED.** A prior explicit P5-A0 epoch was closed transparently with zero enrollment, assignment, write binding, or outcome when the Wave 3 funnel gap above was discovered; it is evidence of operator/seed/manifest control only, never A/A health, treatment feasibility, or efficacy. `task_control(action="p5")` validates a frozen manifest, source/runtime identity, secret-backed seed commitment, assignment/enrollment order, and the absence of an active workspace writer before opening a rebaselined epoch. P5-A0 may be explicitly opened for instrumentation before P4 predictive completion; P5-A treatment remains separately gated by its own registered manifest, natural eligible task/oracle funnel, and explicit operator authority. Neither starts automatically, and neither is a production-promotion signal;
- auto-handoff: **OFF** pending more real A/B evidence;
- paid Flash terminal reproduction: **requires explicit external-cost authorization**;
- provider/model write authority over the primary checkout: **not granted by telemetry or routing alone**;
- ChatGPT context-pressure percentage: **unknown unless the host exposes a real source**; do not fabricate one.

## 11. Historical WebCodex material

WebCodex core documents, Rust crates, server/runner deployment material, and dated research remain useful and should not be deleted merely because the desktop product has moved further. Their scope must be explicit. When a historical plan says something is future work but current source now implements it, preserve the historical record and update this current-state document or the maintained product guide instead of rewriting chronology.

## 12. Current exact-file EOCL acceptance and live recheck — 2026-08-31

The bounded EOCL wave `f8bb0fcf65a94e929b600b67e0413e6a` /
`52e3d5abc9c247ea945a9e7089ba5254` reached `CHECKPOINTED` and received final
ChatWeb operator acceptance at checkpoint
`95468d1606764d768151ea1b047381e3`. The checkpoint is bound to base HEAD
`a357e1bb45a68cfaf25b8a2aa99a133ab256102c`, worktree fingerprint
`2878151e13221a8c6c9f6f8506b25c30b29d083e9b1f5435883452e508f77413`, and
canonical checkpoint proof fingerprint
`a77efcee64e4503ce7ff2519b6c5c2811ef7d4ede07945b4bb6caae9897b9dc5`.

The exact accepted-file receipt is complete (`schema_version=2`, `count=3`)
and contains only these component-owned existing files:

| Path | SHA-256 | Size (bytes) |
|---|---|---:|
| `electron/services/recoveryActionStore.js` | `18c6a2b99ed2535324f0547030c2b65c4c573d98d6d6ff1846a0002812d4bdbf` | 75717 |
| `electron/services/recoveryHost.js` | `8ed02caf81f451c9c78c9e4cffeb8a916c8c472985b778f4e674435a9a9072d0` | 130667 |
| `resources/coding-tools-mcp/coding_tools_mcp/tool_schema.py` | `fd21ea595592388abb62dca6b4cb89db8dd8b52b7d25498c2c19bbb9cca53ecd` | 68738 |

Five focused deterministic proof stages passed, with no source edit in this
wave; the wave adopted exact bytes already present in the authorized worktree.
The earlier checkpoint `9411d3aec777422c89b25ef4837da86f` remains immutable and
is not widened retroactively. This therefore closes exact-file EOCL acceptance
for the three listed files only. It is not a single accepted packet for every
code-bearing file currently dirty in the Coding MCP component.

A fresh read-only runtime recheck at `2026-08-31T05:19:22.575Z` reports
Electron UI and Coding MCP `CURRENT`, `running_revision == disk_revision`,
`components_ready=true`, `fully_ready=true`, `runtime_update_incomplete=false`,
and `error_code=none`. The connector is
`CURRENT_COMPATIBLE_ACKNOWLEDGED` through the managed-attested
`compatible_activation_bootstrap` path, with
`connector_rediscovered=false`, `connector_refresh_required=false`, and
`connector_ack_pending=false`; no strict `tools/list` or `server/discover`
receipt is claimed.

The immutable query-only lifecycle census at `2026-08-31T05:19:30.478Z`
reported SQLite schema `12`, `integrity_check=["ok"]`, zero foreign-key rows,
`projection_drift=false`, `mutated_canonical_ledger=false`, zero managed jobs,
zero unexplained active runs and zero unbound live resources. It also observed
nine ordinary active RUN rows: seven `THRESHOLD_SENSITIVE_STALE_CANDIDATE`, one
`GRACE_PERIOD_INACTIVE`, and one `AWAITING_ACCEPTANCE` (`275a340f190e43ffb7feeb47a0698109`).
They have no live ownership, but the stale candidates are below the current
86400-second threshold and the awaiting-acceptance row lacks a safe exact
acceptance packet. None may be force-reconciled or accepted blindly.

Accordingly, current local runtime readiness and the three-file EOCL checkpoint
are closed, while the full-component accepted baseline/P0.6, natural Golden HR
outcomes, prospective efficacy, commit, package/release, deployment and
production gates remain open. No restart, commit, push, package, release,
deployment or production operation occurred in this recheck.

## 13. Windows Tailscale candidate recheck — 2026-09-21

SSH through Tailscale to `DESKTOP-63643J4` (`100.72.186.41`) was verified.
Testing used the isolated candidate `E:\DEV\Codex-web-candidate-502ffb8` and
did not modify the existing Windows checkout. Node/Electron tests reported
922/922 pass; Recovery process E2E reported 3/3 pass; HTTP→node read/write/
approved-patch/document-write/exec/file-read reported 22/22 pass. Shared
account tests reported 3 OAuth binding tests plus one two-client exec routing
test pass, proving the same `issuer/subject` resolves to one `principal_id`
while each task remains pinned to its selected `binding_id`.

The candidate intentionally has no `.git`, so the final `npm test` repository
guards could not run and no Git cleanliness/release claim is made. The initial
full Python MCP receipt was 1,158 pass with two OS-specific fixture failures
(Landlock error text and a `shell=False` `echo` builtin); after the fixture
portability fixes, the candidate rerun is **1.160/1.160 PASS in 31m45s**.
Four OAuth configuration assertions still assume POSIX credential file modes
on NTFS and remain a separate fixture issue. These results are Windows
candidate evidence; reboot/reconnect/rotation, live deployment and owner
acceptance remain open.

The subsequent Windows packaged gate passed on the same candidate: `dist:dir`,
packaged recovery smoke, NSIS installer build `1.0.7`, and installed
install/smoke/uninstall. The installed smoke preserved the production Recovery
descriptor and Scheduled Task definition. This promotes only candidate
`PACKAGED_PROOF`; it does not prove reboot, DPAPI/ACL rotation, live service,
workspace Git/build/test/deploy, or owner acceptance.

The follow-up Windows security probe found and fixed inherited broad ACLs on
node config/policy JSON. Atomic writes now apply a SID allowlist before rename
and fail closed on ACL tooling errors. Source and packaged DPAPI probes both
round-trip without plaintext and show only current user, SYSTEM and
Administrators; the Windows HTTP→node group remains 22/22 pass afterward.
Wave 21 then reconnected to the same target and reran **18/18**
secret/rotation/workspace, **3/3** same-account OAuth, **1/1** two-client exec,
**1/1** document-write and **1/1** standing patch. Ubuntu health remained
read-only (`ok=true`, schema 19, `recovery`, OAuth principals 0, unresolved 11),
so these receipts still do not constitute live owner acceptance.
