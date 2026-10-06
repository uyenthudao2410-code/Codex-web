# Kế hoạch hoàn thiện và hiện trạng — một tài khoản ChatGPT, nhiều máy, workspace dùng chung

## Phân biệt hai loại workspace

Trong app Coding Tools, workspace được chọn/đăng ký là **thư mục dự án local trên
Windows** (ví dụ `E:\DEV\Codex-web`), gắn với `workspace_id` và generation của
node. Đây là thư mục duy nhất được cấp quyền ghi trong Windows Sandbox.

Kết nối/plugin ChatGPT là một lớp riêng với workspace Windows. Không cần nhập
Organization ID hoặc ChatGPT Workspace ID vào `workspace_context` để chọn
project local. Ở các lần kiểm tra 26–27/09/2026, kết nối ChatGPT Plus cá nhân
hiện có đã trả `inventory` và `task_list`; đây là bằng chứng cho đúng kết nối và
hai operation đó. [OpenAI Developer Mode docs](https://developers.openai.com/api/docs/guides/developer-mode)
hiện liệt kê Plus cá nhân là đủ
điều kiện dùng MCP đầy đủ trên web; khả năng cụ thể vẫn phụ thuộc Developer Mode,
app đã thêm vào cuộc trò chuyện, rollout và cấu hình phía Control Plane. Không
cần Business workspace chỉ để dùng Plus cá nhân. Organization ID trên OpenAI
Platform là phạm vi quản trị riêng, không phải `workspace_id` hoặc `binding_id`
của Coding Tools.

## Đính chính luồng cá nhân — 26-09-2026

Nếu `Ubuntu Control Plane` đã gọi được `workspace_context(inventory)` trong
ChatGPT cá nhân, giữ nguyên kết nối đó. Không yêu cầu người dùng tìm Organization
ID / ChatGPT Workspace ID để tiếp tục kiểm tra task hoặc đọc file. Những ID này
không thuộc payload `workspace_context`; yêu cầu scope của công cụ quản trị
tunnel không được suy rộng thành điều kiện sử dụng Control Plane.

Luồng `private_tunnel_service` dùng một service principal do chủ hệ thống cấp,
không nhận diện từng người ChatGPT. Chế độ này không yêu cầu OAuth từng người,
nhưng cũng không bỏ grant, binding, policy, sandbox hay receipt. Nếu triển khai
dùng OAuth thì giữ OAuth; không đổi authentication chỉ vì gói ChatGPT là Plus.
Xem [hướng dẫn cá nhân](../control-plane/README.md#personal-chatgpt-plus--pro-reuse-the-existing-connection)
và [trạng thái hiện hành](CURRENT_STATE.md) trước khi sử dụng các snapshot cũ
bên dưới. Các checkpoint 23–24/09 giữ nguyên theo thời điểm quan sát; chúng
không chứng minh tình trạng tài khoản hoặc runtime ngày 26/09.

## Checkpoint mới hơn — 24-09-2026, 13:31 +07

Source `main @ 50cd0e86`, worktree dirty. Workspace của Coding Tools là thư mục
Windows đã chọn trong app; ChatGPT Business workspace là tổ chức chứa thành viên
và connector, không phải đường dẫn file.

Candidate `r8` unpacked build/afterPack pass và runtime canary **PASS** trên
`E:\DEV\Codex-web`: Windows Sandbox guest realpath/cwd/temp, nested Node child,
`npm prefix` trỏ đúng thư mục probe và synthetic `npm test` marker đều đúng;
lease được nhả/reacquire, MXC deprovision trả thành công, cache placeholder không
phát sinh. Python adapter **18/18** (+2 subtests), NPM resolver **2/2** (+2
subtests), build verifier **12/12**, Node exec sandbox **4/4**. PowerShell argv
round-trip hỗ trợ space/quote/trailing slash/empty argument. Binary MXC vẫn
**unsigned/experimental/dev-only**; đây chưa phải installer hay release.

Packaged Recovery Host smoke của r8 cũng **PASS**: user-data cô lập, descriptor
bản cài giữ nguyên, Recovery Host/MCP ready, supervisor healthy và fail-closed
trong owner/hash mismatch; không sửa scheduled task.

Hai commit local hiện có: `a4becdb7` (source/candidate) và `3ca26a74` (runbook).
Sau commit, worktree chỉ còn live drift của canonical ledger; delivery receipt,
`--verify-index`, repository secrets và coding-tools history guard đều PASS.

Ghi nhận lỗi canary r7: npm không khóa prefix nên đã chọn nhầm package root và
bắt đầu script `npm test` của repo; timeout sau 30 giây đã dừng nó trong Windows
Sandbox. HEAD và danh sách đường dẫn Git không đổi sau lần thử, nhưng `.coding-tools`
đã dirty trước đó nên không có baseline để khẳng định nội dung SQLite không drift.
r8 precheck `npm prefix` xác nhận package probe trước khi cho chạy script, tránh
lặp lại workload repo ngoài ý muốn.

Các candidate chẩn đoán r4–r7 và bốn cache files do lần thử lỗi tạo đã được chuyển
nguyên vẹn, hash-verified, vào `E:\Caches\Temp\codex-mxc-quarantine-20260924`;
candidate r1–r3 không đổi. Source/r8 resources không có `%SystemDrive%` placeholder.
Probe không để lại thư mục `.mxc-wsb-*` trong workspace; VMMEM đã tự thoát sau
deprovision, không reboot, kill hay force-reclaim.

## Mô hình OpenAI Tunnel và shared service

Theo [Secure MCP Tunnel docs](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels), tunnel là transport riêng tư: cần `tunnel_id`, Platform runtime API key cho `tunnel-client`, và liên kết đúng cả Platform organization lẫn ChatGPT workspace. Tunnel không đại diện danh tính từng thành viên; quyền Tunnels và quyền developer mode/workspace là hai lớp riêng.

ChatGPT MCP OAuth là user authorization-code + PKCE. OpenAI nêu rõ ChatGPT không hỗ trợ client-credentials/service-account grants hoặc customer API keys cho OAuth MCP, còn tool `noauth` là anonymous; với write tools, [auth guidance](https://developers.openai.com/plugins/build/auth) khuyến nghị xác thực user. Repo có một lựa chọn riêng `private_tunnel_service`: một shared service principal/grant được tunnel-client đưa vào request cục bộ; nó không tạo user identity riêng cho từng thành viên. Đây là lựa chọn khớp với quyết định của chủ workspace (hai thành viên dùng chung service identity trong scope folder đã bind), nhưng cần giữ service grant hẹp và binding Windows exact.

Ubuntu peer `svhome` online trên Tailscale và host-key khớp entry trusted theo IP
hiện tại, nhưng Tailscale SSH tiếp tục từ chối user `admin` theo policy. Local
Tunnel MCP trên Windows liệt kê `aliases=[]`; admin profile `default` chỉ tham chiếu
key từ environment nhưng value không hiện trong environment này. Đây **không** chứng
minh Ubuntu tunnel offline. Không đổi ACL hay thử user khác. ChatGPT connector UI
chưa được kiểm tra vì Computer Use trả `Codex auth token is unavailable`. Server
snapshot gần nhất (23-09) còn schema 28, admission `recovery`, auth
`legacy_context_grant`, chưa service grant/binding Windows write/exec; chưa có
ChatGPT Business→Ubuntu→Windows canary. Chưa đọc/ghi/deploy/restart Ubuntu, chưa
bật policy hoặc push.

## Checkpoint Windows Sandbox state-aware candidate — 24-09-2026

Source hiện `main @ 50cd0e86`, worktree dirty; bảo toàn mọi `.coding-tools/**`
evidence. Windows ProcessContainer trên máy này vẫn fail `realpath EPERM`, nên
đường exec đã ghép sang state-aware Windows Sandbox khi feature và bộ binary
candidate cùng sẵn sàng. Một Runtime giữ tối đa một VM ấm; command single-flight,
chỉ map workspace đã chọn RW và toolchains RO, network bị chặn trong guest.
Cancellation, cleanup không chắc chắn, workspace đổi và Runtime đóng đều dừng
VM; nếu teardown không xác nhận, lần chạy sau giữ fail-closed.

MXC source được ghim tại
`cbe1774364ea2ec846f56ab744e43a416f751420`, schema `0.10.0-alpha`;
local patch `85a0991dd4473b31574ad6c71d2c489389e6719a3e6ef9116f5f9156a7b7c8df`
đổi guest share destinations sang `C:\CodexWorkspace\share-0` (ghi) và
`C:\CodexToolchains\share-N` (chỉ đọc); thư mục E: trên host không còn bị dùng
làm guest drive E:. Ba binary là **unsigned, experimental, dev-only**. Windows
feature `Containers-DisposableClientVM` đã bật và reboot xác nhận.

**Bằng chứng hiện có:** upstream Windows Sandbox/CLI tests **281/281**; adapter
state-aware **11/11**; session/build **89/89**; Wave-A **13/13**; Node policy,
packaging, Control Plane **30/30**. Manual Windows Sandbox guest E:-host→C:-guest
share smoke ghi marker và teardown thành công; MXC one-shot no-share chạy được.
Unpacked `r3` đã qua exact resources **295 files**, adapter **9 files**,
sanitation, legacy binary Authenticode và `RunAsNode`.

Runtime acceptance còn thiếu: patched state-aware VM đã handshake `Ready`, nhưng
nested PowerShell/Node canary thoát code 1. Sau đó state-aware start-only trả
`backend_error`; hai `vmmemWindowsSandbox` processes còn sau khi daemon và
RemoteSession đã rời. Không kill process SYSTEM hoặc dùng `--force-reclaim`.
Exec standing policy chưa cài; chưa xác nhận binding/admission mới trên Ubuntu;
chưa có ChatGPT→Ubuntu→Windows end-to-end canary. Không đổi ACL, không deploy/
restart Ubuntu, không commit/push. Candidate `r1`, failed `r1` và các installer
trước đây vẫn được giữ nguyên.

Đây là source/focused-test evidence, chưa phải packaged/installed/released,
Ubuntu deployment, hay natural ChatGPT E2E proof.

## Last observed Ubuntu deployment checkpoint — 23-09-2026, 22:19 +07

Code commit 2119d980 adds a Windows fail-closed gate: Control Plane
structured exec_command now returns SANDBOX_UNAVAILABLE before process spawn
on Windows until a filesystem sandbox is available. Tests prove no process is
spawned; this keeps the selected-workspace boundary honest while sandbox work
remains. resources/coding-tools-mcp full suite: 1163 passed, 5 skipped, 258
subtests; root npm test: 1044/1044. The separate module-size checker still
reports five over-budget modules that this change did not touch.

Installer candidate from this source is at
dist/windows-installer-2119d980-noresedit/coding-tools-mcp-setup-1.0.7.exe
(SHA-256 1362ECFFC5C65CCBBBE1E72C37DA40B90801DCF11783EB7F1B50D038E3D9D2F5).
Packaged smoke passes. Electron Builder's normal Windows resource editor hits
EBUSY when editing the 225 MB executable; the tested candidate disables
resource editing/signing, so it is a validation artifact, not the final
installer. The installed app remains unchanged, and activation preflight still
reports RECOVERY_HOST_INSTALLATION_MISMATCH for the development checkout.

Release `97f26a13b0def2795421c454bc32e1f301aa0704` đã được chép qua SSH
`svhome`, đối chiếu SHA-256 archive và verifier trên Ubuntu, sau đó cài vào
versioned releases và kích hoạt bằng symlink `current` cùng systemd user unit.
Trước migration đã tạo snapshot SQLite bằng Backup API, SHA-256
`08c92f75f202049e98382f784187056c7ba37e110873c7a4d80da9feab54c3e2`,
schema 25, integrity `ok`, admission `recovery`; file snapshot owner-only 0600.
Một bản sao tạm đã migrate thử schema 25→28 giữ nguyên 18 action rồi tự dọn.

Sau restart, `/healthz` và release verifier xác nhận Ubuntu live schema 28,
SQLite integrity `ok`, package SHA
`sha256:a2f23a7666abaac083b49f851400b792b868f87e2fe5bd9bbc477c320048abf4`,
service instance `cp_2c46fcb41a7849c3aee196e60ad43fbd`; 18 action/13
receipt không đổi. Tunnel unit vẫn active, local `/healthz` và `/readyz` của
tunnel trả `live`/`ready`. Chạy `tunnel-client doctor` song song với daemon
đang sống báo health listener 8768 đã được chiếm, nên không dùng kết quả doctor
đó làm chứng cứ tunnel hỏng hay làm thay thế cho real ChatGPT MCP call. Quan
trọng: auth vẫn
`legacy_context_grant`, admission vẫn `recovery`; chưa cấp service principal/
grant, chưa đổi header Tunnel, chưa mở pilot, chưa thay Windows bản cài. Có 11
action không có kết quả cuối trên hai node lịch sử (10 `reconcile_required`,
1 `dispatch_unconfirmed`); tất cả đã có disposition cách ly, nhưng không được
gọi là effect đã được xác minh hoặc tự ý mở global admission.

Tiếp theo là nghiệm thu bản Windows candidate trên đúng installed/runtime,
thay generation read-only sang quyền file cần thiết, tạo binding mới, cài và
quan sát policy local. Sau đó mới cấu hình shared service grant và pilot đúng
binding; quyền exec vẫn đóng vì chưa có cách ly tiến trình theo workspace.

Windows NSIS candidate `dist/windows-installer-97f26a13/coding-tools-mcp-setup-1.0.7.exe`
đã build, SHA-256
`DFF23CE4FFE743FD49159893719C244FD6156F659C85E07615A56C2CAD70F19D`;
unpacked cùng build vượt qua packaged recovery smoke. `npm test` đạt 1044/1044,
source-root và repository secret check PASS. Candidate **chưa cài đè** app
đang chạy: per-user installation hiện có, Recovery Supervisor `healthy` với
agent `running_heartbeat_only`, còn preflight activation của checkout trả
`RECOVERY_HOST_INSTALLATION_MISMATCH`. Quy trình chính thức đòi đúng owner
installation và acceptance closure theo HEAD; không tắt process theo tên hoặc
cài đè để vượt gate. Installed smoke cũng chỉ hợp lệ trên máy không có bản
cài per-user, nên chưa chạy trên máy này.

Sau Ubuntu upgrade, node-agent **của bản cài Windows hiện hành** gọi lại
`reconcile-authority-status` thành công: node `4c4b7a5b-…` có một binding
active cho workspace `Codex-web` generation `generation_a91d…`, presence
`online`, nhưng capabilities vẫn `read=true, write=false, exec=false`, node
readiness `degraded`, policy `expired_or_disabled`. Vì vậy đường node→Ubuntu
còn sống, song không có quyền file-write/exec live. Sau quan sát này Tailscale
SSH đòi xác thực lại cho một truy vấn read-only tiếp theo; không thử vượt qua
login, không có thay đổi server sau thời điểm đó.

## Checkpoint mới — 23-09-2026, 20:46 +07 (local package candidate, chưa triển khai)

Windows checkout `E:\DEV\Codex-web` đang phát triển candidate chung cho hai
thành viên ChatGPT Business. Ubuntu live đọc qua `/healthz` vẫn là schema 25,
`legacy_context_grant`, admission `recovery`, declared revision `749ab5c9`.
Đó là bằng chứng server cũ còn chạy, không phải candidate source đã lên server.
Windows hiện có process `Coding Tools MCP.exe` từ
`C:\Users\Admin\AppData\Local\Programs\Coding Tools MCP`; `npm run
dev:status` của source báo `DEV_UI_INSTALLATION_MISMATCH`, không phải bằng chứng
process bản cài đã nạp source mới. Bản cài vẫn cần build/activation mới để
nhận UI cài standing file policy. Chưa có canary ChatGPT → Ubuntu → Windows
đọc/vá file.

Commit cục bộ `97f26a13` tách một service principal chung khỏi OAuth cá nhân, cấp
grant có scope `inventory`, `read`, `patch` bất biến, và chỉ nhận tác vụ cho
binding/generation được owner chọn trong một quyết định `scoped_pilot` tối đa
24 giờ. Action cũ không gắn quyết định không được poll trong pilot. App Windows
cho chọn workspace đã đăng ký, lấy hợp đồng MCP từ node-authenticated Ubuntu,
cài policy đọc/vá file exact generation và báo đúng trạng thái sau reload.
Ubuntu release candidate `codex-control-plane-97f26a13…` đã build và verify
local với schema 28, package SHA
`sha256:a2f23a7666abaac083b49f851400b792b868f87e2fe5bd9bbc477c320048abf4`.
Windows unpacked candidate ở `dist/windows-candidate-97f26a13/win-unpacked`
đã qua packaged recovery smoke (resource exact, user-data isolation, Recovery
Host/MCP và supervisor); chưa cài đè bản đang chạy. Ubuntu qua SSH `svhome`
được xác nhận service+tunnel đang active, release live `749ab5c9` verifier
PASS với schema 25. Đây là local `PACKAGED_PROOF`, không phải Ubuntu deploy,
Windows installed proof hay ChatGPT E2E.

Chưa cài policy chạy lệnh: `cwd`/argv-prefix không cách ly filesystem trên
Windows, nên không được nói đã hoàn thiện yêu cầu exec tự động. Không mở
admission, không cấp service grant live, không sửa policy live trong checkpoint
này. Source proof, packaged proof, live proof và natural-work proof vẫn là bốn gate
riêng.

Điều kiện tiếp theo: hoàn tất kiểm tra tích hợp và giao source; đối soát lịch
sử action cũ, thử bản Ubuntu/Windows candidate trên môi trường cô lập, cấp
service grant mới `[inventory, read, patch]` qua operator runbook, thay đúng
generation/binding, sau đó canary đọc và vá file. Chỉ bật exec khi có rào OS
thật hoặc phạm vi lệnh cố định được chấp nhận rõ là chạy dưới quyền Windows
user, không phải sandbox workspace.

**Ngày cập nhật:** 22-09-2026, 06:34 +07
**Branch:** `main`
**HEAD đã kiểm tra:** `99fbdd95b5bceb901c80e8d4b63582d0266bb456`
**Mức bằng chứng hiện tại:** `SOURCE_PRESENT + FOCUSED_TEST_PROOF` + exact
Windows build/installed candidate `PACKAGED_PROOF`; chưa phải `LIVE_ACCEPTED`

Đây là bản đọc nhanh dành cho việc điều hành. [Kế hoạch chi tiết theo chronology](TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md), [runbook Windows exact](WINDOWS_EXACT_VALIDATION_RUNBOOK.md), [trạng thái Control Plane](CONTROL_PLANE_IMPLEMENTATION_STATUS.md) và [current state](CURRENT_STATE.md) vẫn giữ toàn bộ receipt lịch sử; tài liệu này chỉ gom lại contract hiện hành, phần đã tận dụng và việc còn phải đóng.

## Checkpoint Wave 47 — ba checkout đã cùng `main@99fbdd9` — 22-09-2026, 06:34 +07

Windows `E:\DEV\Codex-web` đã fast-forward an toàn lên cùng commit với Linux và
GitHub bằng bundle tạm qua SSH; không reset/rebase, không đổi remote, không
restart runtime. Chỉ hai projection `.coding-tools` runtime còn dirty trên
Windows; source/package files sạch và bundle tạm đã xoá. Delta là docs/evidence,
không thay installer hay code runtime.

Wave 46 vẫn là trạng thái vận hành: enrollment `pending_operator_approval`,
epoch `ACTIVATION_REQUEST_EXPIRED`, admission đóng, chưa route evidence,
workspace registry/policy hoặc `LIVE_ACCEPTED`.

## Checkpoint Wave 46 — central handoff sống, enrollment Ubuntu chờ duyệt — 22-09-2026, 06:27 +07

Windows exact `main @ eab25528ffb070e2de6732574ca2599d89b8d08b` đang chạy
packaged Recovery Host/MCP đúng installation và workspace `E:\DEV\Codex-web`.
Epoch handoff đã hết hạn (`ACTIVATION_REQUEST_EXPIRED`), admission đóng,
`central_connected=false`, `authority_ready=false`,
`central_status_reason=LOCAL_EXECUTOR_NOT_READY`, `fully_ready=false`; chưa có
binding/task live.

Đã gửi đúng một enrollment request tới `https://svhome.tail0e4032.ts.net`;
receipt `pending_operator_approval` với enrollment
`enroll_31e46b3ad4714738b27707c7b7b8e6a8`. Node config đã được tạo cục bộ nhưng
route evidence, workspace registry và policy chưa có; không đọc/hiển thị node
credential. Ubuntu health vẫn HTTP 200/schema 19 nhưng admission `recovery`,
`oauth_principals=0`, package đang chạy revision cũ `0843ece334e07dd29f03cbd4c67fa97fc885ea1c`.

Next action là operator Ubuntu approve enrollment và cấp quyền deploy exact
Control Plane package; sau đó reconcile credential/heartbeat, đăng ký workspace,
cài policy và retry full-clean bằng epoch mới. Mức proof vẫn
`SOURCE_PRESENT + FOCUSED_TEST_PROOF + PACKAGED_PROOF`, chưa `LIVE_ACCEPTED`.

## Checkpoint Wave 44 — receipt HEAD đã đồng bộ sang Windows; live gate giữ nguyên — 21-09-2026, 21:42 +07

`dcb3fc492b22d1b04547f3eae1c595b4ee6e4ce0` chỉ là delivery receipt
`.coding-tools`, không đổi package-relevant source. Linux/GitHub và Windows
`E:\DEV\Codex-web` cùng ở HEAD này, worktree Windows sạch; installer hash vẫn
`61fb7fa5785c3861fcd4c8371f54172894472c9a0b7d48854c5cb05126d7c14e`.
Runtime vẫn `MISSING/RECOVERY_DESCRIPTOR_STALE`, chưa `LIVE_ACCEPTED`; owner
closure/activation là gate kế tiếp.

## Checkpoint Wave 45 — refresh Windows dừng đúng vì thiếu Runtime API Key — 21-09-2026, 22:06 +07

Refresh được chạy trong phiên `Admin` tương tác và đã bootstrap Recovery Host,
nhưng runtime local không có `Runtime API Key`, nên epoch refresh kết thúc
`FAILED` với `ACTIVATION_EPOCH_FAILED`. Không còn process/task/script/log tạm;
profile, credential và workspace được giữ nguyên. Runtime trở lại
`MISSING/ENOENT`, chưa `LIVE_ACCEPTED`.

Gate tiếp theo là owner nhập key trong UI Windows (không gửi key vào chat) nếu
dùng local executor, hoặc hoàn tất pairing/config central executor nếu không
muốn giữ key trên Windows; sau đó mới refresh/preflight lại.

## Checkpoint Wave 43 — exact source đã đồng bộ sang Windows; activation vẫn chờ owner — 21-09-2026, 21:35 +07

Linux/GitHub và Windows `E:\DEV\Codex-web` đều ở `main @
fa055951d912997d75c9de5d7d18ee42f72b3094`; worktree Windows sạch. Delta từ
`bb4522c` chỉ là tài liệu/evidence, nên artifact `1.0.7` hiện hành vẫn giữ
SHA-256 `61fb7fa5785c3861fcd4c8371f54172894472c9a0b7d48854c5cb05126d7c14e`.

Windows read-only check vẫn là `MISSING/RECOVERY_DESCRIPTOR_STALE`, còn
`full-clean-activation --preflight` fail-closed vì Recovery Host descriptor
owner không sống. Chưa có closure exact source, workspace/connector/authority,
binding/task hoặc Ubuntu deploy; mức proof chưa vượt `PACKAGED_PROOF`. Owner
cần mở UI từ desktop interactive và tạo closure năm trường cho đúng HEAD trước
khi activation.

## Checkpoint Wave 41 — activation incomplete; Ubuntu release chưa đồng bộ — 21-09-2026, 20:05 +07

Linux, GitHub và Windows đều ở `main @ 7f26754657c5a1e933dea000fb75a0624e72f152`,
Windows worktree sạch. Packaged UI/Recovery Host đã được quan sát sống đúng
installation, nhưng strict snapshot vẫn chưa có workspace, MCP execution,
central authority hoặc connector ACK; closure exact source vẫn trống.

Một activation owner attempt đã dừng ở `STOPPING` với admission đóng và không
có replacement process, nên chưa được nâng thành `LIVE_ACCEPTED`. Task tạm cũ
trỏ tới file đã mất đã được gỡ; không xoá profile, credential hay workspace.
Ubuntu `/healthz` hiện vẫn nạp release cũ, admission `recovery`, chưa có OAuth
principal và SSH quản trị bị từ chối. Cần closure exact source + quyền deploy
Ubuntu trước khi mở admission, binding hoặc task.

## Checkpoint Wave 42 — exact Windows rebuild/install proof — 21-09-2026, 21:25 +07

Windows exact `bb4522c` đã chạy `npm run dist`: Node/Electron **922/922 PASS**,
MCP **1160/1160 PASS**; installer `1.0.7` mới SHA-256
`61fb7fa5785c3861fcd4c8371f54172894472c9a0b7d48854c5cb05126d7c14e`. Installed
executable khớp unpacked artifact (`a57ced0d…a7ecbd2`). Packaged recovery smoke
PASS (17 resources, 8 tools, Recovery/MCP/Supervisor isolation); source/worktree
Windows sạch sau khi trả icon build về HEAD.

Đây là packaged/installed proof, chưa `LIVE_ACCEPTED`: activation cũ vẫn
`STOPPING/CLOSED`, app hiện không chạy, chưa workspace/connector/central
authority/binding/task. Control Plane release cùng HEAD đã build/verify cục bộ
nhưng Ubuntu chưa deploy vì SSH bị từ chối; admission vẫn `recovery`.

## Checkpoint Wave 39 — exact main Windows build và installed smoke — 21-09-2026, 19:02 +07

Linux, GitHub `origin/main` và checkout Windows `E:\DEV\Codex-web` đã được
đối chiếu cùng HEAD `abc1a639a2bfd48a7f8c7c212bc26bb7724c9fc0`; Windows chỉ
còn branch `main` và worktree sạch. Trên checkout exact đã chạy `npm ci` và
`npm run dist`: Node/Electron **922/922 PASS**, MCP Python **1160/1160 PASS**,
resource/source/secret gates PASS. Installer `1.0.7` có SHA-256
`dcf1f5535eacb3e5c66d3a246503bec5dbcf949833b6e476b83576574a68351b`.

`packaged-recovery-smoke.js` và `installed-recovery-smoke.js` đều trả `ok=true`;
installer/register/uninstall, Recovery Host, MCP, Supervisor và cleanup đều
pass. Installed smoke đã dọn profile/process sau khi chạy. Vì vậy đây là
`PACKAGED_PROOF` mạnh hơn, không phải runtime live: `dev-ui status` hiện
`state=MISSING`, `host=unavailable`, `error_code=ENOENT`, và full-clean
preflight thiếu `recovery-host.json`. Không tạo credential/context, không mở
admission, không tạo binding/task hay deploy. Next action vẫn là owner
acceptance exact source + full-clean activation, sau đó mới enrollment,
workspace/binding/task và T01–T16/soak.

## Checkpoint Wave 40 — cài artifact ổn định, GUI chưa khởi động qua SSH — 21-09-2026, 19:31 +07

Sau installed smoke, installer exact `1.0.7` đã được cài per-user vào
`C:\Users\Admin\AppData\Local\Programs\Coding Tools MCP`; registry uninstall
ghi đúng `Coding Tools MCP 1.0.7`. Hash executable installed
`a57ced0d185472d5c5e234a1177bf13ca35f14d2661300fc80e92c6daa7ecbd2` trùng
hash executable unpacked từ cùng artifact. Không có Supervisor Scheduled Task.

Khởi chạy từ SSH thường và SSH có TTY đều không tạo GUI process; profile
`%APPDATA%\web-mcp-assistant` và `recovery-host.json` vẫn chưa có. Vì vậy
`dev-ui status` còn `MISSING/ENOENT` và full-clean preflight còn `ENOENT`.
Đây là installed artifact proof, chưa live acceptance; bước tiếp theo phải
được chạy từ phiên desktop `Admin` tương tác để tạo closure/activation chính
thức, không tự forge context hoặc epoch.

## Trạng thái mới nhất — Windows `DESKTOP-63643J4`

Tailscale/SSH đã kết nối tới `100.72.186.41`; Wave 33 vừa đối chiếu read-only
đúng candidate packaged trên data root thật rồi dọn tiến trình test. Wave 26
recheck node và Wave 27 đã recheck packaged candidate;
candidate riêng đã chứng minh
shared-account routing, HTTP→node E2E, Recovery process và packaged/installed
smoke. Runtime live hiện chưa có process; local workspace registry đã có nhưng
chưa có OAuth binding/task; vì chưa có
reboot/reconnect/DPAPI-ACL/owner acceptance nên chỉ mở
`PACKAGED_PROOF` cho candidate, chưa mở `LIVE_ACCEPTED`.

## Checkpoint Wave 37 — SSH handoff đã xong, strict runtime còn đóng — 21-09-2026, 13:36 +07

Đã xử lý trực tiếp trên `DESKTOP-63643J4` qua SSH. Recovery Host development
cũ được xác thực bằng descriptor/IPC, gọi `runtime.stop` rồi terminate đúng
process identity; không dùng `taskkill` theo tên. Supervisor packaged sau đó
đã dựng được Recovery Host candidate mới: `state=healthy`, connected agent
`running`, host `runtime_mode=packaged`, `recovery.ping ready=true`.

Đây mới là liveness/handoff proof, chưa phải execution proof. Snapshot strict
hiện tại là `central_connected=true` nhưng `authority_ready=false`,
`central_status_reason=LOCAL_EXECUTOR_NOT_READY`, `fully_ready=false` và
`update_incomplete=true`. Durable activation epoch đang `FAILED` với mã
`RECOVERY_REPLACEMENT_TARGET_CHANGED`; vì vậy MCP local/Tunnel không được tự
khởi động lại trong epoch cũ và không được mở action.

Registry local hiện có một entry opaque với capability `{read,write,exec}`,
nhưng canonical root vẫn là `E:\DEV\Codex-web-candidate-502ffb8`; mục tiêu
nghiệm thu được yêu cầu là `E:\DEV\Codex-web`. Luồng `replace-workspace` chính
thức sẽ giữ `workspace_id`, retire generation cũ, tạo generation mới, tắt các
policy local khớp generation cũ và khiến binding/task cũ trên account dùng
chung bị fence. Vì thao tác đó có thể ảnh hưởng máy/client khác cùng tài khoản,
chưa chạy mutation khi chưa có xác nhận owner về việc đổi generation.

Không có action nào được dequeue/execute, không gọi model, không deploy và
không sửa epoch/credential bằng tay. Next action: owner xác nhận **replace
generation hiện tại sang `E:\DEV\Codex-web`** (hoặc chọn đăng ký workspace mới),
sau đó cung cấp closure exact source để chạy full-clean activation; chỉ khi
strict runtime đạt mới kiểm binding/task và T01–T16.

## Checkpoint Wave 38 — replace path bị từ chối đúng, state không đổi — 21-09-2026

Sau khi owner xác nhận đổi generation, đã gọi candidate `node-agent.cmd
replace-workspace` với root `E:\DEV\Codex-web`. CLI trả mã
`CONTROL_PLANE_WORKSPACE_REPLACEMENT_NOT_FOUND` trước khi tạo journal hoặc gọi
retire/register, vì implementation hiện tại chỉ tìm entry có **cùng canonical
path** rồi mới đổi label/capability. Đây là giới hạn contract hiện hành,
không phải lỗi SSH hay lỗi credential.

Kiểm tra sau lỗi: registry vẫn trỏ `E:\DEV\Codex-web-candidate-502ffb8`,
generation cũ và ba standing policy vẫn `enabled=true`; Supervisor vẫn
`healthy`, agent `running`, không có replacement journal. Không chạy fallback
`retire-workspace` + `register-workspace` vì fallback tạo `workspace_id` mới,
không đáp ứng yêu cầu giữ ID/generation dùng chung. Cần quyết định riêng:
đăng ký workspace mới, hoặc mở một thay đổi product/artifact để hỗ trợ migrate
canonical path với old workspace identity explicit.

## Checkpoint Wave 36 — BLOCKED chờ owner activation trên Windows — 21-09-2026, 12:41 +07

Recheck authoritative cuối: `dev:status` vẫn trả
`state=MISSING/host=unavailable/error_code=RECOVERY_DESCRIPTOR_STALE`; Supervisor
Task vẫn `Running` nhưng `state=spawn_failed`,
`last_error_code=SPAWN_FAILED`, `last_error_message=Recovery Supervisor
executable missing`, với 378 lần retry. Các Wave 33–36 đều xác nhận cùng một
blocker; source focused suite đã pass nên không còn bước read-only nào có thể
đưa runtime live lên.

**BLOCKED — cần external owner action:** trên `DESKTOP-63643J4`, owner phải
chạy acceptance ceremony cho exact source/artifact, full-clean activation được
hỗ trợ, rồi cài lại Supervisor từ đúng checkout nếu manifest vẫn thiếu. Sau khi
strict flags đạt, tôi sẽ tiếp tục binding/task, workspace toolchain và T01–T16.
Không sửa epoch/closure bằng tay và không retry mù.

## Checkpoint Wave 35 — source lifecycle regression xanh, Windows gate vẫn mở — 21-09-2026, 12:39 +07

Focused regression trên source hiện tại:
`node --test tests/dev-ui-lifecycle.test.js tests/full-clean-activation.test.js
tests/recovery-supervisor.test.js` đạt **133 pass, 0 fail, 1 skip** (skip là
nhánh runtime Supervisor chỉ chạy trên Windows). Nhóm test xác nhận status
read-only, exact closure binding, fail-closed preflight, full-clean epoch,
Supervisor eligibility và không fallback stop-start.

Đây là source proof mới, không làm thay đổi Windows external state. Target vẫn
giữ `RECOVERY_DESCRIPTOR_STALE`/`SPAWN_FAILED`; chưa có strict runtime live.
Mức proof nâng độ tin cậy source nhưng vẫn là
`SOURCE_PRESENT + FOCUSED_TEST_PROOF + candidate PACKAGED_PROOF`, chưa
`LIVE_ACCEPTED`.

## Checkpoint Wave 34 — preflight xác nhận descriptor stale và Supervisor thiếu executable — 21-09-2026, 12:36 +07

Owner activation chưa xảy ra. `node scripts/dev-ui-lifecycle.js status` chạy từ
cả checkout Windows và candidate đều trả exit 0 theo semantics read-only nhưng
`state=MISSING`, `host=unavailable`, `error_code=RECOVERY_DESCRIPTOR_STALE`.
`node scripts/full-clean-activation.js --preflight` từ checkout trả exit 1 với
`RECOVERY_DESCRIPTOR_STALE` (Recovery Host owner không còn sống).

Supervisor status vẫn cho `installed=true`, Scheduled Task `Running`, nhưng
`state=spawn_failed`, `last_error_code=SPAWN_FAILED`, thông báo executable của
Recovery Supervisor bị thiếu. Đây là bằng chứng trực tiếp rằng việc retry
heartbeat không thể làm runtime sống lại; cần cài lại Supervisor bằng installer
được hỗ trợ từ đúng source/artifact sau khi closure hợp lệ. Không restart,
install, sửa epoch, dispatch hay gọi model trong wave này.

Blocker vẫn là **exact-source/accepted-closure mismatch + stale Supervisor**;
proof giữ `SOURCE_PRESENT + FOCUSED_TEST_PROOF + candidate PACKAGED_PROOF`.
Next action không đổi: owner thực hiện acceptance ceremony/full-clean
activation trên exact source, sau đó khôi phục Supervisor và mới chạy strict
runtime/binding/task/toolchain.

## Checkpoint Wave 33 — xác nhận máy mở để test, nhưng closure/runtime vẫn stale — 21-09-2026, 12:29 +07

Kết nối Tailscale/SSH tới `DESKTOP-63643J4` (`100.72.186.41`) tiếp tục thành
công với user `Admin`. Đây là đợt đối chiếu và heartbeat chẩn đoán bounded;
không cài lại, không restart, không sửa epoch/acceptance, không dequeue/execute
action, không gọi model và không deploy. Heartbeat chỉ ghi route evidence
credential-free/last-seen theo thiết kế.

Đối chiếu tại máy đích cho thấy checkout thật `E:\DEV\Codex-web` đang ở HEAD
`3779096a9156bf2827e3164d09bcc1ef647a2c01` và còn 23 thay đổi; candidate
`E:\DEV\Codex-web-candidate-502ffb8` là version `1.0.7`, có package nhưng
không có `.git`. Closure durable trên profile vẫn giữ checkpoint
`8d10f27638e2498cba80edf0bcbe77ce`/accepted HEAD
`cffd2acee24a4f38f4a83ddfea4c40f766de7a63`, `activation_eligible=true` nhưng
`affected_components=[]`, `components_current=false` và `lifecycle_clean=false`.
Các giá trị này không bind được candidate với HEAD hiện tại.

Durable epoch còn ghi `READY/OPEN`, nhưng đó chỉ là record cũ: `runtime-state`
chỉ còn PID/revision stale, owner PID của `recovery-host.json` không còn sống;
Supervisor Task vẫn tồn tại nhưng status là `spawn_failed` với lỗi
`SPAWN_FAILED`. Vì không có current-process census/identity nên không được suy
ra `fully_ready` hay `LIVE_ACCEPTED` từ epoch record đó.

**Phân loại:** blocker vận hành do exact-source/accepted-closure mismatch và
installed Supervisor manifest stale; không phải lỗi Tailscale. **Bằng chứng
giữ nguyên:** `SOURCE_PRESENT + FOCUSED_TEST_PROOF + candidate PACKAGED_PROOF`.
Next action là owner dùng artifact/source exact để chạy acceptance ceremony và
full-clean activation được hỗ trợ (sau đó cài lại Supervisor từ đúng checkout
nếu cần), rồi mới kiểm strict MCP/Tunnel/UI readiness và binding/task live.

## Checkpoint Wave 32 — Tailscale live test, Recovery Host identity và fail-closed runtime — 21-09-2026, 12:10 +07

SSH qua Tailscale xác nhận đúng `DESKTOP-63643J4\Admin` (`100.72.186.41`).
Installed supervisor còn manifest trỏ tới executable đã bị dọn bởi
installed-smoke; đây là stale installed state, không phải lỗi mạng. Candidate
unpacked `1.0.7` có executable và installer đầy đủ.

Theo đúng cửa sổ test, candidate Recovery Host được mở tạm trên data root người
dùng. `recovery.ping` trả `ok=true`, `ready=true`, PID/instance identity khớp;
Supervisor chuyển `healthy`. Tuy nhiên strict runtime observation vẫn là
`mcp_ready=false`, `identity_current=false`; snapshot ghi
`central_connected=false`, `authority_ready=false`,
`central_status_reason=LOCAL_EXECUTOR_NOT_READY`, `fully_ready=false`,
`update_incomplete=true`, `recovery_blocked=true`. Gọi `runtime.start` bị từ
chối HTTP 409 `UPDATE_INCOMPLETE`: epoch cũ không cho thay Coding MCP tại chỗ,
phải có full-clean activation epoch mới do owner chấp thuận.

Node `runtime-heartbeat` chạy exit 0 nhưng chỉ báo
`readiness=degraded`, `reason=packaged_runtime_unready`,
`runtime_state=unknown`, `fully_ready=unknown`, `policy_state=expired_or_disabled`;
route evidence mới là `fresh`. Không dequeue action, không gửi receipt và không
gọi model. Sau khi lấy receipt, tiến trình candidate được dừng theo đúng PID;
hiện còn **0** `Coding Tools MCP` process, descriptor chỉ còn stale metadata;
Supervisor ghi `OWNER_DEAD` ngay sau cleanup và lần retry tiếp theo trở lại
`SPAWN_FAILED` vì executable trong manifest vẫn thiếu.

Kết luận: kết nối Tailscale và Recovery IPC đã được chứng minh, nhưng chưa có
runtime execution live. Mức bằng chứng vẫn
`SOURCE_PRESENT + FOCUSED_TEST_PROOF + candidate PACKAGED_PROOF`, chưa
`LIVE_ACCEPTED`. Next action chính xác là owner chạy full-clean activation trên
đúng artifact/source, để MCP/Tunnel/UI đạt strict identity/heartbeat; sau đó mới
kiểm OAuth `principal_id`/`binding_id`/task pin, toolchain thật và T01–T16.

## Checkpoint Wave 26 — Tailscale recheck và connected-agent fail-closed — 21-09-2026, 11:27 +07

Tailscale ping tới `DESKTOP-63643J4` (`100.72.186.41`) trả lời qua DERP HKG
(khoảng 70 ms); SSH xác nhận `DESKTOP-63643J4\Admin` và candidate
`E:\DEV\Codex-web-candidate-502ffb8`. Candidate focused receipts chạy lại
trên đúng máy đích: lifecycle secret/rotation/workspace **18/18 PASS**;
same-account OAuth/binding **3/3 PASS** (28 deselected); hai client route exec
**1/1 PASS** (12 deselected); document-write **1/1 PASS** (2 deselected);
standing patch **1/1 PASS** (4 deselected). Patch lane có cảnh báo teardown
fixture Windows `WinError 10038`, nhưng test pass và không có effect production.

Credential node gửi `heartbeat --readiness degraded` thành công (`exit 0`, có
`last_seen_at_ms`). Registry local đọc được đúng một workspace opaque
`workspace_a84ba281f3ef4365b949b1b35376dfba`, generation
`generation_63c426bce483466e9ced0087a9d75377`, capabilities `{read,write,exec}`.
Không có process `electron`/`node`. `runtime-heartbeat` trả trạng thái
`blocked/runtime_unavailable` với runtime identity `unreported`, state `MISSING`
và policy `expired_or_disabled`; một `run-connected-agent --max-iterations 1`
đã dừng `MAX_ITERATIONS_REACHED` sau một vòng, mọi lane không bắt đầu poll,
`received_action_ids=[]`, `submitted_receipts=0`.

Đây là bằng chứng **reachable + credential/registry + focused candidate**,
không phải OAuth `principal_id`/`binding_id` live, runtime execution hay
ChatGPT UI two-client proof. Không mở admission, không tạo task/action live,
không ghi workspace, reboot/restart/deploy, commit hoặc push. Gate tiếp theo
vẫn là owner mở Electron/Recovery packaged runtime đúng data root, rồi mới
kiểm strict identity/heartbeat, OAuth binding/task pin, toolchain thật và
T01–T16.

## Checkpoint Wave 27 — packaged recovery smoke cô lập — 21-09-2026, 11:38 +07

Official `scripts/packaged-recovery-smoke.js` chạy trên candidate Windows và
trả **exit 0**. Receipt xác nhận executable/app.asar, **17 required resources**,
đủ **8 smart-v3 public tools**, Recovery Host ready, device identity có mặt,
mode `independent_mcp_tunnel_v1`, Recovery MCP sống, Supervisor healthy,
`live_owner_fail_closed` và `hash_mismatch_fail_closed` đều pass; production
Recovery descriptor ổn định và `scheduled_task_mutation=false`.

Smoke dùng user-data TEMP cô lập và cleanup hoàn tất; sau cleanup không còn
process `Coding Tools MCP`/Electron/Node. Đây là **candidate PACKAGED_PROOF**,
không phải runtime production, OAuth binding/task live hay owner acceptance.
Không mở admission, không dispatch action, không deploy/restart production.

## Checkpoint Wave 28 — central health và source capability recheck — 21-09-2026, 11:41 +07

Ubuntu `/healthz` read-only sau heartbeat mới vẫn trả `ok=true`, SQLite
integrity `ok`, schema **19**, `admission_mode=recovery`, package SHA thực tế
khớp expected, `oauth_principals=0`, `node_workspaces=3` và unresolved actions
**11** (10 quarantined, 1 chưa quarantine). Không mở admission hoặc reconcile.

Source recheck bằng stdlib `unittest` đạt **7/7 PASS**: 4 test account/binding/
writer handoff và 3 test local structured exec/document-write/standing patch.
Lần gọi `pytest` local trước đó bị phân loại là thiếu module môi trường
(`No module named pytest`), không phải source/test failure; candidate Windows
pytest focused trước đó vẫn đã pass. Runtime live và ChatGPT UI acceptance vẫn
chưa có.

## Checkpoint Wave 29 — full Control Plane source discovery — 21-09-2026, 11:44 +07

`PYTHONPATH=control-plane:control-plane/tests python3 -m unittest discover`
chạy toàn bộ `control-plane/tests` và đạt **298/298 PASS trong 96,772s**.
Receipt stdout có các fixture lifecycle/unknown-state đúng thiết kế; không có
failure và không tạo live action. Đây là source regression proof, không thay thế
Windows installed/runtime, OAuth UI hoặc owner acceptance.

## Checkpoint Wave 30 — installed NSIS smoke và isolation — 21-09-2026, 11:49 +07

Candidate Windows chạy `scripts/installed-recovery-smoke.js` với **exit 0**:
installer `1.0.7` install/register pass; packaged smoke lồng bên trong pass với
17 resources, 8 smart-v3 tools, Recovery/MCP/device identity/Supervisor; sau đó
uninstall pass, executable và user-install registration được dọn sạch.
Production Recovery descriptor và Scheduled Task definition giữ nguyên.

Đây là **installed candidate proof**, chưa phải reboot/logon/reconnect, live
OAuth binding/task, workspace toolchain thật, T01–T16 hoặc owner acceptance.

## Checkpoint Wave 31 — post-smoke read-only state — 21-09-2026, 11:51 +07

Post-check trên target không còn process `Coding Tools MCP`/Electron/Node.
File Recovery descriptor vẫn còn metadata owner/instance, nhưng không có owner
process sống; nó chỉ là stale/observation-only và không được coi là
runtime liveness. Ubuntu health không đổi: SQLite `ok`, schema 19,
`admission_mode=recovery`, `oauth_principals=0`, `node_workspaces=3`, unresolved
11. Không có action live, restart production hay thay admission.

## Checkpoint Wave 25 — node registration và local standing capability — 21-09-2026

Node credential đã heartbeat thành công ở trạng thái `degraded`. Candidate
workspace đã được central đăng ký với opaque `workspace_id` và generation,
capability `{read,write,exec}`; local registry có đúng một entry và API không
trả canonical path. Đây chưa phải OAuth `binding_id`/task pin vì Ubuntu vẫn
`recovery`, `oauth_principals=0`.

Standing policy local đã cài cho candidate: file-read (3 path), approved-patch
(1 path) và structured exec (6 argv prefix cho Git/npm/Python test), không TTL.
ACL probe thực tế chỉ còn current user + SYSTEM + Administrators. Một vòng
`run-connected-agent` bắt đầu và dừng bình thường sau một iteration nhưng
fail-closed `CONTROL_PLANE_BRIDGE_FAILED`; không dequeue hoặc tạo receipt action.

Ubuntu health sau đăng ký giữ SQLite/package SHA `ok`, `node_workspaces=3`,
unresolved actions **11**. Wave này chỉ thay đổi registry/heartbeat/policy test
trên target; không ghi workspace, không mở admission, không tạo OAuth
principal/binding/task, không reboot/restart/deploy.

## Checkpoint Wave 24 — kiểm thử lại kết nối Tailscale và candidate — 21-09-2026, 10:59 +07

SSH/Tailscale tới `DESKTOP-63643J4` (`100.72.186.41`, `Admin`) vẫn reachable.
Candidate cô lập `1.0.7` chạy focused lanes không dùng credential thật:
secret/rotation/workspace **18/18 PASS (4,37s)**; same-account OAuth **3 PASS,
28 deselected (10,32s)**; two-client exec **1/1 PASS (9,61s)**; document-write
**1/1 PASS (4,91s)**; standing patch **1/1 PASS (10,43s)**.

Read-only runtime probe cho thấy hiện không có Electron/Recovery process;
`control-plane-workspaces.json` chưa tồn tại và `list-workspaces` trả danh sách
rỗng. Supervisor là `spawn_failed`, connected agent là `integrity_unproven`.
Packaged policy inspection trên data root dev bị chặn đúng mã
`CONTROL_PLANE_POLICY_PACKAGED_DATA_ROOT_FORBIDDEN`, nên không được coi data
root dev đó là installed packaged binding.

Wave này chỉ chứng minh **reachable + candidate focused proof**. Không mở
Ubuntu admission, không tạo principal/binding/action live, không reboot/restart,
rotate/revoke credential thật, deploy, commit hoặc push. `LIVE_ACCEPTED` vẫn
chưa đạt; cần test account/data root được owner cho phép để pair/enroll,
register workspace, heartbeat/connected-agent, rồi mới kiểm reboot/reconnect và
hai client ChatGPT thật.

## Checkpoint Wave 23 — packaged/installed smoke recheck — 21-09-2026, 10:48 +07

- Packaged smoke: **PASS**, 17 resources, smart-v3 đủ 8 tool, Recovery/MCP/
  Supervisor healthy, owner/hash fail-closed pass, không mutate Scheduled Task.
- Installed smoke: installer `1.0.7` install/register → smoke → uninstall pass;
  production descriptor và Scheduled Task definition stable, cleanup pass.

Đây là candidate package/isolation proof, không phải reboot/reconnect hoặc
owner/live account proof. Các gate T01/T03/T09/T15 và hai client ChatGPT thật
vẫn cần chạy trên workspace/credential được phép.

## Checkpoint Wave 22 — structured exec parity trên Windows candidate — 21-09-2026, 10:45 +07

- Workflow parity `git --version` → `npm run build` → `npm test` →
  `npm run deploy` trên một local structured lane: **1/1 PASS trong 6,38s**.
- HTTP→node journal và terminal receipt: **1/1 PASS trong 4,30s**.

Hai ca này chạy fixture deterministic trên candidate, chứng minh route/task/
writer/receipt và không tạo deployment thật. Vì Ubuntu vẫn `recovery` và
`oauth_principals=0`, chưa thể nghiệm thu workspace production hoặc hai client
ChatGPT thật. Wave 22 chỉ nâng candidate proof cho T06/T09; các gate
rotation/reboot/reconnect, toolchain thật, T01–T16, restore/soak và owner
acceptance vẫn mở.

## Checkpoint Wave 21 — Windows candidate đang reachable — 21-09-2026, 10:31 +07

- SSH trực tiếp xác nhận `DESKTOP-63643J4`/`Admin`; candidate
  `E:\DEV\Codex-web-candidate-502ffb8` version `1.0.7` có unpacked package và
  NSIS installer, nhưng không có `.git` và không ghi đè checkout chính.
- Focused recheck trên candidate không dùng credential thật: node
  secret/rotation/workspace **18/18 PASS**, same-account OAuth/binding **3/3
  PASS**, two-client exec route **1/1 PASS**, document-write **1/1 PASS**,
  standing patch **1/1 PASS**.
- Ubuntu health read-only: `ok=true`, schema 19, SQLite `ok`, admission
  `recovery`; counts `3 nodes / 4 enrollments / 4 bindings / 24 contexts /
  18 requests / 18 actions / 13 receipts`; `oauth_principals=0`, unresolved
  **11** (10 quarantined, 1 unquarantined), auth mode
  `legacy_context_grant`, package SHA khớp expected.
- Receipt Windows candidate đã có trước đó: full MCP **1.160/1.160 PASS**
  (31m45s) và Node/Electron **922/922 PASS**. Bốn OAuth config assertion còn
  lại chỉ kiểm mode POSIX `0400/0600` trên NTFS; không nới ACL/secret policy để
  biến fixture này thành pass giả.

Wave này xác nhận máy test đã mở lại; Wave 20 “target chưa reachable” chỉ còn
là chronology. Chưa nâng `LIVE_ACCEPTED`: chưa chạy rotation/revoke + reboot/
logon/reconnect trên installed candidate, hai ChatGPT client thật qua UI,
toolchain Git/build/test/deploy trên workspace thật, T01–T16, restore, soak hoặc
owner acceptance. Không tự sửa unresolved action và không mở admission Ubuntu.

**Next action:** chạy các gate Windows còn thiếu theo
[WINDOWS_EXACT_VALIDATION_RUNBOOK.md](WINDOWS_EXACT_VALIDATION_RUNBOOK.md), sau
đó nghiệm thu hai client cùng `principal_id` chọn cùng `binding_id`; chỉ owner
mới nâng `LIVE_ACCEPTED`.

## Checkpoint Wave 20 — target Windows và evidence guard — 21-09-2026, 08:18 +07

- Read-only SSH tới target alias `daochienthang` timeout sau 5 giây; không copy
  source, cài đặt, chạy test hay thay đổi hệ thống ngoài.
- Không có `dist/win-unpacked` hoặc installer Windows trong workspace Linux.
- `npm run check:coding-tools-history`: **PASS (4.873 files)**; repository
  secret check: **PASS**.

Blocker hiện tại là **Windows runner/target chưa reachable**. Wave 18 vẫn là
full source/local regression baseline; Wave 19 vẫn là `windows_only` platform
classification. Chưa nâng `PACKAGED_PROOF`/`LIVE_ACCEPTED`.

Runbook bàn giao đã được thêm tại
[WINDOWS_EXACT_VALIDATION_RUNBOOK.md](WINDOWS_EXACT_VALIDATION_RUNBOOK.md), bao
gồm lệnh exact, enrollment một lần, hai client cùng principal, execution parity,
fault matrix và điều kiện thoát.

**Next action:** khi có target Windows được phép truy cập, chạy Recovery/
packaged/installed smoke, DPAPI/ACL/reboot/reconnect/rotation và T01–T16;
không đoán credential hoặc deploy/restart trong lúc target chưa sẵn sàng.

## Checkpoint Wave 19 — phân loại Recovery/packaged gate Windows — 21-09-2026, 08:14 +07

Đã kiểm tra hai lane cần Windows exact:

- `npm run test:recovery:e2e`: **3 SKIP, 0 FAIL**; cả ba test đều skip có chủ
  đích ngoài `win32`.
- `npm run test:recovery:packaged`: `dist:dir` dựng Linux candidate thành công;
  packaged smoke trả `{ok:true, skipped:true, reason:"windows_only"}`.

Đây là **environment/platform gate**, không phải source pass và cũng không phải
failure. Không nâng nhãn `PACKAGED_PROOF`/`LIVE_ACCEPTED`; `dist/linux-unpacked`
chỉ là preflight artifact ignored. Cần Windows runner để kiểm RunAsNode,
Recovery Host, installer, DPAPI/ACL, startup/reconnect và rotation.

**Next action:** dùng candidate cùng HEAD trên Windows, chạy lại hai lane trên,
installed smoke và T01–T16; sau đó nghiệm thu hai client cùng `principal_id`
chọn đúng `binding_id`, toolchain thật, backup/restore và soak 24 giờ.

## Checkpoint Wave 18 — full local gate bằng runtime dependency chuẩn — 21-09-2026, 08:06 +07

Đã chạy lại `npm run test:all` trên đúng working tree với bundled workspace
runtime Python **3.12.14** và `pytest 8.4.2`, source-first `PYTHONPATH`, proxy
variables unset và cảnh báo tài nguyên được theo dõi nghiêm ngặt:

- Node/Electron `npm test`: **874 tests, 858 PASS, 16 SKIP, 0 FAIL**; source-root
  clean và repository-secret check PASS.
- MCP: **1.160 collected, 1.153 PASS, 7 SKIP, 0 FAIL** trong **159,98s**.
- Các warning còn lại là `ResourceWarning`/cleanup warning trong một số test;
  không có test failure và không có dấu hiệu regression authority.
- Control Plane receipt gần nhất vẫn **295/295 PASS**; đây là lane riêng đã
  chạy bằng Python 3.14.4, không gộp nhầm vào số MCP.

Wave 18 đã đóng failure dependency-only của Wave 17 bằng cách dùng đúng
interpreter có dev extra; không sửa policy runtime để làm xanh giả. Mức bằng
chứng được nâng thành **full source/local regression xanh**, nhưng vẫn chỉ là
source/focused/integrated local proof. Chưa được suy ra Windows packaged/live,
DPAPI/ACL, reboot/reconnect, hai ChatGPT client thật, Git/build/test/deploy trên
node thật, T01–T16, backup/restore hay soak 24 giờ.

**Tận dụng được ngay từ code hiện tại:**

- `principal_id`/OAuth inventory, `binding_id`, task pin, writer lease và
  generation fence để nhiều client cùng account chọn đúng máy/workspace.
- Enrollment, credential riêng theo node, SecretStore/DPAPI path, heartbeat,
  rotation/revoke và reconnect; không cần xây lại hoặc chép token/context mỗi
  phiên.
- File-read, approved-patch, document-write và structured-exec bridge qua
  Recovery Host/RuntimeOrchestrator; node giữ file/process/Git/build/test/deploy
  theo quyền OS local.
- Journal/idempotency, lost-ACK replay, `unknown/reconcile_required`, stop/
  observe/handoff, Supervisor standing-policy và `.coding-tools` evidence.

**Next action chính xác:** đóng gói Windows candidate từ cùng HEAD → exact
RunAsNode/Recovery/installer/DPAPI/ACL/reboot/reconnect/rotation → hai client
cùng `principal_id` chọn một `binding_id` và kiểm tra target/generation → chạy
đọc/sửa/exec/Git/build/test/deploy thật → T01–T16, backup/restore, soak 24 giờ
và owner acceptance. Chưa commit, push, deploy, restart service, bật quyền
live hay gọi provider trả phí.

## Checkpoint Wave 17 — full MCP source-first rerun — 21-09-2026

Full MCP rerun với source repository đứng trước runtime dependency, proxy
variables đã unset và `PYTHONWARNINGS=error::ResourceWarning` đạt:

- **1.160 collected: 1.152 PASS, 1 FAIL, 7 SKIP, 37 warnings trong 161,53s**.
- SDK HTTP + operator timestamp: **19/19 PASS**.
- Multi-workspace HTTP + authorized workspace session: **2/2 PASS** với
  executable `python` thật.
- Continuous-check bookkeeping pass khi child có dev `pytest` qua
  `ShellEnvPolicy(inherit="all")`; test mặc định còn fail vì `/usr/bin/python3.14`
  trên host không có pytest và runtime core cố ý không truyền `PYTHONPATH`.

Vì vậy failure còn lại là **dependency/harness-only**, chưa phải source
authority bug; full MCP chưa được gọi là xanh cho tới khi chạy trên interpreter
dev chuẩn. Wave 17 chỉ cập nhật bằng chứng và next action, không thay đổi quyền
live.

**Next action:** chạy `npm run test:all` trên host/pipeline có dev extra chuẩn,
ghi receipt không dùng runtime tạm, rồi mới chuyển Windows exact candidate sang
enrollment/DPAPI/reconnect và two-client acceptance.

## Checkpoint Wave 16 — trạng thái hiện hành sau full MCP recheck — 21-09-2026

Contract không đổi: một account ChatGPT/OAuth ánh xạ về một `principal_id` dùng
chung; client chọn `binding_id`; task pin `{device_id, endpoint_id, workspace_id,
workspace_generation}`; Ubuntu chỉ auth/route/queue/receipt; node đã bind giữ
file, process, Git, build/test/deploy và quyền OS local. Nếu account chỉ có một
binding usable, UI có thể tự chọn ID đó cho chat mới, nhưng server vẫn phải nhận
`binding_id` rõ ràng và không tạo `active_workspace` toàn account.

Trạng thái test hiện hành:

- Node/Electron: **874 tests, 858 PASS, 16 SKIP, 0 FAIL**; source-root và
  repository-secret checks PASS.
- Control Plane: **295/295 PASS**.
- MCP full-suite Wave 16 (lịch sử): **1.160 collected, 1.145 PASS, 8 FAIL,
  7 SKIP, 35 warnings**. Receipt hiện hành là Wave 17: **1.152 PASS, 1 FAIL,
  7 SKIP**; vẫn chưa đạt full gate.
- Linux package preflight: **427 resources + 9 adapters**, helper smoke vẫn
  chỉ là Linux evidence.

Tám failure MCP hiện được phân loại để xử lý theo thứ tự: một official SDK
smoke do `httpx.InvalidURL`/proxy runtime; các matrix/greenfield/build/
continuous-check/workspace-session do child `python` không có trên host; và
operator-report cần xác minh lại canonical timestamp `24:00:00Z` trên đúng
interpreter. Chưa dùng lần chạy này để kết luận source authority sai hoặc để
nâng mức proof.

**Next action:** shim `python → /usr/bin/python3.14` chỉ trong môi trường test,
unset proxy cho SDK smoke, rerun tám failure rồi chạy lại MCP full suite; sau
đó mới chuyển Windows exact candidate → DPAPI/ACL/reconnect → two-client cùng
`principal_id` → toolchain thật → T01–T16/soak/owner acceptance. Wave này chỉ
cập nhật tài liệu, không commit/push/deploy/restart service hay bật quyền live.

## Checkpoint Wave 13 — xác nhận account ChatGPT dùng chung và kế hoạch cập nhật — 21-09-2026

Yêu cầu vận hành đã được chốt lại theo đúng mô hình **một tài khoản ChatGPT/OAuth,
nhiều client/máy điều khiển, workspace được chọn bằng ID**:

```text
ChatGPT account/OAuth
    -> một principal_id dùng chung
    -> client chọn binding_id cho từng task
    -> task pin device/endpoint/workspace/generation
    -> Ubuntu auth + inventory + route + queue + receipt
    -> node đã bind thực thi tại workspace local bằng quyền OS của node
```

Ví dụ bắt buộc: máy A bind workspace `W1` thành `B1`; máy B/C đăng nhập cùng
account và chọn `B1`; lệnh của B/C chạy tại A/W1, không chạy tại B/C và không
copy workspace. Nếu account có `B2`/`B3`, client phải chọn ID tương ứng cho task
đó. `binding_id` chỉ là selector opaque, không phải token, context, credential,
quyền Administrator hay một `active_workspace` dùng chung cho mọi chat.

| Thành phần | Trách nhiệm đã chốt | Không được suy diễn thành |
| --- | --- | --- |
| Account / `principal_id` | Xác định các client thuộc cùng tài khoản và quyền xem target | Quyền tự chạy trên mọi máy hoặc bỏ qua writer/generation fence |
| `binding_id` | Chọn một device + endpoint + workspace + generation cụ thể | Bearer token, đường dẫn file, context ngắn hạn hoặc quyền OS |
| Task | Đóng băng target khi mở và giữ receipt/attempt theo target đó | Tự retarget/failover khi client đổi lựa chọn hoặc node khác online |
| Ubuntu | Auth, inventory, route, queue, quan sát và receipt | Nơi giữ file/workspace hoặc nơi thực thi thay node |
| Node đã bind | Giữ file, process, Git, build/test/deploy và kiểm tra policy/ACL local | Tài khoản Windows được nâng thành Administrator |

**Tình hình tại checkpoint:** source, focused tests và candidate Windows đã
chứng minh phần lớn đường đi account → binding → task → node; package/installed
smoke và DPAPI/ACL probe đã pass. Mức hiện tại là candidate `PACKAGED_PROOF`,
chưa phải `LIVE_ACCEPTED`: reboot/reconnect/rotation live, hai ChatGPT client
thật, toolchain Git/build/test/deploy, T01–T16, backup/restore, soak 24 giờ và
owner acceptance vẫn là gate mở.

**Phần tận dụng:** OAuth/account inventory và `ControlPlaneStore`; enrollment,
credential/rotation/heartbeat; SecretStore và Recovery Host/IPC; standing
file-read, approved-patch, document-write, structured-exec bridges; journal,
idempotency, writer lease, generation fence, queue/receipt; Coding Tools MCP;
connected-agent/Supervisor; resource verifier, packaged smoke và `.coding-tools`
evidence. Không xây lại credential theo máy, executor Ubuntu thứ hai, cơ chế
copy token/context hoặc duyệt từng lệnh trong standing local scope.

**Next action chính xác:** build Windows candidate từ HEAD hiện tại → chạy
RunAsNode/Recovery/installed smoke và kiểm byte identity → enrollment/bind `W1/B1`
với DPAPI/ACL, reboot/reconnect và rotation/revoke → hai client cùng
`principal_id` chọn `B1` và observe/stop/handoff → read/write và structured
Git/build/test/deploy thật → T01–T16, backup/restore và soak 24 giờ → owner
acceptance. Chỉ sau các receipt đó mới nâng nhãn bằng chứng hoặc xem xét
release/deploy. Wave này chỉ cập nhật tài liệu, không đổi live quyền, không
commit/push/deploy/restart service và không gọi provider trả phí.

## Checkpoint Wave 15 — full regression gate trên source hiện tại — 21-09-2026

Sau Wave 14, đã chạy full regression trên đúng worktree và HEAD hiện tại:

- `npm test`: **874 tests, 858 PASS, 16 SKIP, 0 FAIL** trong **43,45s**;
  source-root clean và repository-secret check đều PASS.
- Full Control Plane Python suite bằng Python 3.14.4 và dependency runtime tạm:
  **295/295 PASS trong 96,37s**, với `PYTHONWARNINGS=error::ResourceWarning`.

Không có failure mới. Các skip là ca Windows/runtime có điều kiện, không phải
pass giả. Wave 15 xác nhận source/test baseline hiện tại không regress sau khi
đồng bộ shared-account UI/docs; mức proof vẫn là
`SOURCE_PRESENT + FOCUSED_TEST_PROOF` + integrated local test proof.

**Không được suy diễn:** full Linux/source regression không đóng Windows exact
package, RunAsNode/Recovery Host thật, DPAPI/ACL, reboot/reconnect, hai client
ChatGPT live, Git/build/test/deploy trên workspace thật, T01–T16 hoặc soak 24h.
Next action vẫn là chuyển candidate này sang Windows và chạy P1–P5.

## Checkpoint Wave 14 — recheck focused account → node và local authority — 21-09-2026

Đã chạy lại trên đúng worktree hiện tại bằng Python 3.14.4 với dependency
runtime tạm đã có sẵn; lần gọi đầu thiếu `control-plane` trong `PYTHONPATH` và
được phân loại là **harness invocation error**, không phải lỗi source. Lần retry
đúng môi trường đạt:

- OAuth/account, task session, writer/exec và HTTP → node document/exec/patch:
  **71/71 PASS trong 58,32s**.
- Store, file-read, approved-patch, document-write, structured-exec, credential
  rotation/protection và workspace replacement: **146/146 PASS trong 9,53s**,
  với `PYTHONWARNINGS=error::ResourceWarning`.
- Node/Electron document/exec bridge, enrollment, SecretStore, packaged smoke và
  Supervisor preflight: **34 PASS, 1 SKIP, 0 FAIL trong 3,75s**; skip là runtime
  Supervisor thật chỉ chạy trên Windows.
- Đồng bộ mô tả UI Device Control với boundary mới (panel chỉ điều khiển device
  hiện tại, còn `binding_id` đi qua Control Plane) và cập nhật docstring facade;
  `py_compile` cùng Control Center focused **14/14 PASS**.

Wave 14 củng cố bằng chứng focused cho shared `principal_id` → `binding_id` →
task pin → node-local read/write/exec, credential lifecycle và không duplicate
effect. Nó không chứng minh Windows exact package, DPAPI/ACL thật, reboot/
reconnect live, hai ChatGPT client thật hay owner acceptance; mức proof vẫn là
`SOURCE_PRESENT + FOCUSED_TEST_PROOF` + integrated local test proof.

**Next action không đổi:** chuyển receipt này vào candidate Windows exact, chạy
P1 enrollment/DPAPI/reconnect → P2 two-client same-account → P3 toolchain thật →
P4 fault matrix/T01–T16 → P5 backup/restore/soak/owner acceptance.

## Checkpoint Wave 10 — refresh Linux packaged candidate — 21-09-2026

Đã tạo lại candidate unpacked từ worktree hiện tại bằng `npm run dist:dir`.
Receipt mới:

- electron-builder Linux `dist/linux-unpacked`: **PASS**.
- `node --test tests/packaged-recovery-smoke.test.js tests/installed-recovery-smoke.test.js`: **3/3 PASS**.
- `node scripts/packaged-recovery-smoke.js`: `{"ok":true,"skipped":true,"reason":"windows_only"}` đúng contract.
- Verifier trực tiếp trên candidate: **427 resource files exact-source**, **9
  control-plane adapters exact-source**, **463 entries sanitized**.
- HTTP boundary cho hai client cùng `principal_id` (chọn nhiều binding và
  handoff writer lease): **2/2 PASS trong 3.053s**.
- HTTP → node → Recovery cho document-write và structured exec: **23/23 PASS
  trong 29.601s**, chạy với `PYTHONWARNINGS=error::ResourceWarning`.
- Standing-profile configuration, shared-task observation và cross-client
  writer/exec guard: **3/3 PASS trong 3.046s**.
- Standing patch không cần per-patch approval và document-create không đưa
  content vào action payload: **2/2 PASS trong 0.083s**.

Đây là bằng chứng byte/resource và helper preflight trên Linux. Nó không chứng
minh Windows RunAsNode fuse, Recovery Host process thật, DPAPI/ACL, reboot,
reconnect, hai client live hoặc owner acceptance; mức proof không đổi.

## Checkpoint Wave 11 — documentation contract alignment — 21-09-2026

Đã rà `control-plane/README.md` theo contract account dùng chung. Phần
`install-read-only-policy-*` nay được đánh dấu rõ là **legacy pilot/
compatibility-only**; README mô tả trusted flow hiện hành: OAuth account →
opaque `binding_id` → standing node-local `file-read`, write/document và
structured exec → task pin/reconnect. Không thay đổi live service hoặc quyền
Windows; đây là đồng bộ tài liệu với source/test hiện có.

## Checkpoint Wave 12 — T01–T16 source/live matrix — 21-09-2026

Bảng dưới đây tách rõ proof đã có ở source/focused khỏi acceptance còn thiếu
trên Windows exact artifact. `FOCUSED` không được hiểu là `LIVE_ACCEPTED`.

| ID | Phạm vi kiểm thử | Trạng thái hiện tại | Receipt hoặc thiếu sót chính |
| --- | --- | --- | --- |
| T01 | Enrollment một lần, credential riêng, reboot/reconnect, revoke | `FOCUSED_TEST_PROOF + WINDOWS_CANDIDATE` | Windows secret/rotation/workspace **18/18 PASS**, DPAPI/ACL probe pass; reboot/reconnect/revoke live còn mở |
| T02 | Hai binding khác device không lẫn action/receipt | `FOCUSED_TEST_PROOF` | Multi-binding/task isolation source tests; chưa có hai node Windows thật |
| T03 | Cùng principal chọn từng `binding_id`, không retarget task | `FOCUSED_TEST_PROOF` | HTTP same-account **3/3 PASS**; chưa có hai ChatGPT client thật |
| T04 | Observe/writer lease/handoff giữa hai client cùng principal | `FOCUSED_TEST_PROOF` | Profile/shared-task/cross-client guard **3/3 PASS**; live handoff còn mở |
| T05 | Offline/stale heartbeat chỉ đổi presence, không cấp quyền/failover | `FOCUSED_TEST_PROOF` | Inventory/store presence tests; chưa có network/offline Windows receipt |
| T06 | Patch/document/exec receipt và mất ACK không chạy effect lần hai | `FOCUSED_TEST_PROOF + WINDOWS_CANDIDATE` | HTTP → node → Recovery **23/23 PASS**; Windows journal/terminal **1/1 PASS**, package crash/lost-ACK live còn mở |
| T07 | Crash sau prepared/MCP disconnect → `unknown/reconcile_required` | `FOCUSED_TEST_PROOF` | Recovery process fixtures xanh; chưa có crash/restart trên Windows installed package |
| T08 | Stale generation/path/preimage/allowlist/capability reject trước effect | `FOCUSED_TEST_PROOF` | Node/bridge/generation negative tests xanh; chưa có OS ACL/live path proof |
| T09 | Read/write/Git/build/test/deploy đúng node và quyền OS local | `FOCUSED_TEST_PROOF + WINDOWS_CANDIDATE` | Structured parity **12/12 PASS**; Windows candidate workflow route **1/1 PASS**; chưa chạy toolchain/deploy thật trên workspace bound |
| T10 | Credential rotation, ACK/mất ACK, key cũ invalid | `FOCUSED_TEST_PROOF + WINDOWS_CANDIDATE` | Rotation **5/5 PASS**, protection/migration **8/8 PASS**, Windows group **18/18 PASS**; installed rotation/ACK live còn mở |
| T11 | Recovery process crash/restart giữ journal/handle/terminal state | `FOCUSED_TEST_PROOF + WINDOWS_CANDIDATE` | Recovery process **3/3 PASS** và packaged/installed smoke; chưa có installed Supervisor restart live |
| T12 | Document create/convert qua bridge process thật | `FOCUSED_TEST_PROOF + WINDOWS_CANDIDATE` | Document node/HTTP E2E **23/23 PASS**, Windows document-write **1/1 PASS**; exact workspace effect còn mở |
| T13 | Windows DPAPI/`safeStorage`/ACL thật | `PACKAGED_PROOF` | Source + packaged Python DPAPI/ACL probe pass; live reboot/rotation/revoke và owner acceptance còn mở |
| T14 | Model gateway tách MCP relay (chỉ nếu bật) | `NOT_APPLICABLE_YET` | Chưa yêu cầu server-side inference; không dùng MCP relay để giả gateway |
| T15 | Soak 24h, queue/reconcile, backup/restore, no duplicate effect | `NOT_PROVEN` | Có isolated/source primitives; chưa có final-build 24h + restore live |
| T16 | Owner revoke/rebind/revoke, mọi client thấy trạng thái rõ | `FOCUSED_TEST_PROOF` | Revoke/retire inventory và admission fail-closed đã có; owner/live two-client acceptance còn mở |

**Điều kiện nâng nhãn:** chỉ khi T01–T13, T15–T16 chạy trên đúng Windows
candidate, có receipt redacted và owner acceptance mới được ghi
`PACKAGED_PROOF`/`LIVE_ACCEPTED`. T14 chỉ mở thành gate riêng nếu quyết định
thêm provider/model gateway.

## 1. Kết luận sản phẩm đã chốt

Luồng đúng là:

```text
Một tài khoản ChatGPT/OAuth
    -> một principal_id dùng chung cho mọi client của tài khoản
    -> client chọn binding_id của workspace cần làm việc
    -> task pin {device_id, endpoint_id, workspace_id, workspace_generation}
    -> Ubuntu xác thực, resolve target, queue/dispatch và trả receipt
    -> node đã bind thực thi tại file/process/toolchain local bằng quyền OS local
```

Ví dụ bắt buộc phải giữ đúng:

```text
Máy A bind workspace W1 -> binding B1
Máy B/C đăng nhập cùng tài khoản ChatGPT -> thấy B1 -> chọn B1
Lệnh của B/C chạy tại máy A, trên W1; không chạy tại B/C và không copy W1
```

Nếu cùng tài khoản có thêm `B2`, `B3`, client chọn ID tương ứng cho từng task.
Không tạo một `active_workspace` chung rồi tự đổi đích cho mọi chat.

Các bất biến:

- `binding_id` là selector opaque, không phải bearer token, context, cookie,
  credential hay quyền Administrator.
- Binding thuộc về một node/workspace cụ thể. Task đã mở giữ nguyên target;
  client đổi lựa chọn mặc định, node khác online hoặc failover không được
  retarget task đang chạy.
- Cùng `principal_id` không bỏ qua idempotency, writer lease, generation fence,
  local policy và terminal receipt. Client khác chỉ observe/stop/handoff trong
  scope được cấp.
- Enrollment và credential là lâu dài theo node. Sau khi được duyệt, node tự
  reconnect sau reboot; không chép token/context và không xin duyệt từng lệnh
  trong standing local scope.
- “Toàn quyền local” chỉ có nghĩa là dùng quyền user/ACL và policy của chính
  máy đã bind; Ubuntu không nâng tài khoản thành Windows Administrator.
- Ubuntu giữ auth, inventory, route, queue, receipt và API dịch vụ. File,
  process, Git, build/test/deploy và quyền OS nằm ở node. Ubuntu không giữ bản
  sao workspace thay node.

## 2. Hiện trạng đã chứng minh

| Boundary | Đã có trong source/local proof | Receipt gần nhất | Chưa được tuyên bố |
| --- | --- | --- | --- |
| Account → principal → nhiều binding | OAuth account inventory, opaque binding, task pin, lifecycle state, writer/generation fence | HTTP same-account **3/3 PASS**; Windows two-client exec **1/1 PASS**; Control Plane **295/295 PASS** | Hai ChatGPT client thật qua UI cùng `principal_id` trên target owner |
| Enrollment lâu dài | Device identity, request/approval, credential generation, heartbeat/reconnect, rotation/revoke source path, workspace registry | Windows secret/rotation/workspace **18/18 PASS**; DPAPI/ACL probe pass | Reboot/logon/reconnect và rotation/revoke trên installed artifact |
| Local file/read-write | Standing file-read, approved-patch, document create/convert qua node → Recovery → RuntimeOrchestrator → Coding Tools MCP | HTTP→node **22/22 PASS**; document-write/patch focused pass | File effect trên workspace thật và quyền OS thật |
| Local exec parity | Structured `argv` lane dùng cho Git/build/test/deploy; poll/stop/output cursor/terminal receipt | HTTP → node → Recovery exec **12/12 PASS**; two-client route **1/1 PASS** | Chạy Git/build/test/deploy thật trên workspace Windows |
| Recovery/continuity | Journal `prepared/completed/rejected/unknown`, lost-ACK replay, stop/reconcile, writer lease, connected-agent và Supervisor preflight standing policy | Recovery process **3/3 PASS**; packaged/installed smoke pass | Reboot/crash/lost-ACK/rotation live và restore/soak |
| Package/resources | Windows `dist:dir`, resource verifier, Recovery smoke và NSIS/installed helper | Candidate `PACKAGED_PROOF`; installer `1.0.7`, install/uninstall pass; DPAPI/ACL pass | Exact Git byte lineage, reboot/startup live và owner acceptance |
| Regression | Node/Electron, Control Plane Python và MCP integrated/candidate | Candidate Node/Electron **922/922 PASS**, MCP **1.160/1.160 PASS**; Linux Control Plane **295/295 PASS** | Candidate không có `.git`; bốn OAuth NTFS/POSIX fixture assertion và live gates |
| Model boundary | Ubuntu auth/router/queue/receipt và MCP tool relay được tách khỏi model | Source contract + focused tool/function boundary | Provider/model gateway chỉ mở khi sản phẩm thật sự cần Ubuntu chủ động gọi model |

### Cách đọc các con số

- Receipt MCP integrated gần nhất là Wave 18, chạy bằng bundled workspace
  Python **3.12.14** với `pytest 8.4.2`; Wave 17 chỉ là lịch sử của dependency
  harness gap và không còn là current truth.
- `npm test` và Control Plane unittest đã chạy trực tiếp trên worktree này.
- Linux package hoặc PE preflight không thay thế Windows exact package/live proof.
- Candidate đã có `PACKAGED_PROOF`; chưa có `LIVE_ACCEPTED` hoặc owner acceptance.

## 3. Những gì đang tận dụng, không xây lại

| Nhu cầu | Thành phần hiện có | Cách dùng trong contract mới |
| --- | --- | --- |
| Account/OAuth | `control-plane/control_plane/mcp_oauth.py`, `http_api.py`, `mcp_facade.py`, `store.py` | Giữ một `principal_id` cho các client cùng account; inventory trả từng binding, không tạo active workspace toàn account |
| Bind/enrollment | `control-plane/control_plane/node_agent.py`, enrollment API, device identity, heartbeat/presence | Duyệt một lần; credential sống theo node; reconnect độc lập context/pilot TTL |
| Secret/lifecycle | `electron/services/secretStore.js`, `controlPlaneEnrollment.js`, `runtimeOrchestrator.js`, `recoveryHost.js`, `recoveryIpc.js` | Bảo vệ secret bằng OS owner store/DPAPI path; route evidence không trở thành action grant |
| Target/task ownership | `ControlPlaneStore` task sessions, idempotency, writer lease, generation fence, queue/receipt | Mọi action nhận `binding_id` rồi pin target; client khác không ghi đè mù |
| Local capability | `controlPlaneFileReadBridge.js`, `controlPlaneApprovedPatchBridge.js`, `controlPlaneDocumentWriteBridge.js`, `controlPlaneExecBridge.js` và node lanes tương ứng | Một local lane cho read/write/exec; local policy và OS quyết định quyền |
| Effect safety | Recovery journal, `RecoveryIpcServer`, Recovery Host, `RuntimeOrchestrator`, `run-connected-agent` | Không gọi lại effect sau lost ACK; giữ `unknown/reconcile_required` khi chưa biết kết quả |
| Tool execution | `resources/coding-tools-mcp/coding_tools_mcp/{tool_schema.py,exec_tools.py,landlock_exec.py}` | Structured argv/process lifecycle; MCP chỉ thực thi tool trên node, không giả làm model |
| Package/evidence | `scripts/verify-packaged-resources.js`, `scripts/packaged-recovery-smoke.js`, `scripts/installed-recovery-smoke.js`, `.coding-tools/**` | Dùng verifier/smoke/ledger để chứng minh đúng bytes và giữ lại evidence theo retention invariant |

Không cần xây lại credential theo máy, queue/task ledger, executor Ubuntu thứ
hai, cơ chế chép context/token giữa client hoặc duyệt từng lệnh ở Ubuntu trong
standing local scope. Không chuyển quyền điều hành local lên server chỉ để làm
đơn giản hóa.

## 4. Kế hoạch hoàn thiện theo gate

### P0 — Đóng băng contract và candidate

1. Chốt fixture `W1/B1` và nếu cần `W2/B2`; mỗi binding có device, endpoint,
   workspace và generation riêng.
2. Chốt schema/contract hash, standing local policy `{read, write, exec}` và
   exact Windows artifact sẽ kiểm thử.
3. Kiểm tra inventory/task/receipt không lộ `canonical_path`, `node_secret`,
   token hoặc context; binding chỉ là ID opaque.

**Exit:** candidate có revision/manifest; task projection giữ target bất biến;
không còn checkpoint cũ bị dùng làm current truth.

### P1 — Enrollment, credential và reconnect

1. Máy A gửi enrollment; Ubuntu duyệt; node nhận credential riêng và lưu bằng
   DPAPI/`safeStorage` + ACL đúng user/service owner.
2. Bind W1 thành B1; ghi workspace registry với generation và capability local.
3. Reboot/logon node; xác nhận tự reconnect/heartbeat, không chép token/context.
4. Chạy staged rotation, mất ACK, revoke credential, retire generation và
   replacement binding; admission phải fail-closed đúng blocker.

**Receipt bắt buộc:** enrollment approval, credential generation, DPAPI/ACL,
startup/reconnect, rotation/revoke/retire trên exact Windows artifact.

### P2 — Shared-account routing và task pin

1. Dùng hai ChatGPT client/access token cùng OAuth `principal_id`.
2. Cả hai đọc inventory và thấy B1; client thứ hai mở task chọn B1.
3. Mở thêm task trên B2 nếu có; kiểm tra mỗi task giữ đúng target.
4. Observe/stop/handoff từ client còn lại theo scope; chứng minh không retarget,
   không tự failover sang node khác và không lộ path/secret.

**Exit:** receipt chứng minh B/C gửi lệnh tại A/W1 khi chọn B1; principal chung
không biến thành quyền quản trị OS.

### P3 — Local read/write/exec đầy đủ

1. Chạy file read và document/approved-patch write bằng standing policy.
2. Chạy structured `argv` cho `git`, build, test và deploy qua cùng task/writer
   lane; shell text chỉ là escape hatch có kiểm soát.
3. Kiểm output cursor, poll, stop, child-process policy, deny path và terminal
   receipt.
4. Chạy trên workspace thật của node, không dùng deterministic fixture để tuyên
   bố package/live.

**Exit:** Git/build/test/deploy thật chạy đúng tại A/W1, policy local deny đúng,
không có per-command approval ở Ubuntu.

### P4 — Recovery và fault matrix

1. Kiểm crash trước effect, sau effect, mất ACK, process restart, network
   disconnect, duplicate delivery và stop-pending.
2. Journal phải phân biệt `prepared`, `completed`, `rejected`, `unknown` và
   `reconcile_required`; không redeliver effect không an toàn.
3. Kiểm Supervisor reconnect sau pilot read-only TTL hết hạn; standing lane còn
   hợp lệ thì node vẫn chạy, policy/identity sai thì fail-closed.

**Exit:** T01–T16 theo matrix dự án đạt; mỗi ca có receipt gắn task/attempt/node
và không dùng PID để đoán kết quả terminal.

### P5 — Đóng gói, live acceptance và vận hành

1. Build đúng Windows exact artifact; chạy fuse/RunAsNode, Recovery Host,
   installed smoke và resource byte-identity.
2. Reboot/reconnect, revoke/rotation, shared-account two-client, local
   read/write/exec và T01–T16 trên artifact cài thật.
3. Chạy backup/restore, offline/reconnect và soak tối thiểu 24 giờ.
4. Owner xem receipt và ký acceptance; sau đó mới nâng nhãn sang
   `PACKAGED_PROOF`, rồi `LIVE_ACCEPTED` nếu toàn bộ gate đạt.

**Exit:** có Windows/live receipt, owner acceptance, trạng thái job quiescent và
không còn blocker chưa phân loại.

### P6 — Model/provider gateway (chỉ khi cần)

Chỉ mở gate này nếu yêu cầu sản phẩm là Ubuntu chủ động gửi request suy luận
đến provider/model. Gateway phải tách khỏi MCP/tool relay, có secret/provider
policy, rate/cost/timeout, receipt và test riêng. MCP/Tunnel hiện chỉ chuyển lời
gọi tool; nó không tự trở thành API model và không được dùng gateway để chuyển
quyền điều hành local sang Ubuntu.

## 5. Việc còn thiếu và thứ tự hành động tiếp theo

### Blocker thật

- Candidate Windows đã có `PACKAGED_PROOF`, NSIS/installed smoke và DPAPI/ACL
  hardening receipt; vẫn chưa kiểm reboot/logon, reconnect và rotation/revoke
  trên installed artifact với test account được phép.
- Chưa có hai ChatGPT client thật cùng `principal_id` chọn cùng B1.
- Chưa chạy Git/build/test/deploy thật trên workspace bound.
- Chưa chạy T01–T16, crash/lost-ACK/restart live, backup/restore và soak 24 giờ.
- Chưa có owner acceptance; Ubuntu live activation/model gateway chưa được mở.

### Next action theo đúng thứ tự

1. Trên installed candidate đã tạo: enrollment/rotation/revoke → reboot/logon
   → reconnect; lưu receipt không chứa secret/path và giữ fail-closed khi ACK
   mất hoặc generation bị retire.
2. Dùng hai client cùng account: inventory, chọn B1, mở/observe/stop/handoff,
   rồi kiểm task pin không retarget; thêm B2 nếu cần.
3. Chạy local read/write và structured Git/build/test/deploy thật; kiểm quyền OS,
   output/stop/unknown và deny policy.
4. Chạy T01–T16, backup/restore, offline/reconnect và soak 24 giờ.
5. Owner review/acceptance; chỉ khi đạt mới cập nhật nhãn proof, chuẩn bị release
   hoặc deploy theo một yêu cầu riêng.

## 6. Quy tắc bằng chứng và trạng thái Git

- Hiện tại công bố `SOURCE_PRESENT + FOCUSED_TEST_PROOF` + Windows candidate
  `PACKAGED_PROOF`; chưa gọi là `LIVE_ACCEPTED`.
- Worktree dirty là có chủ ý, chứa source/test/docs/evidence của các wave; không
  reset, clean, restore hoặc ghi đè thay đổi không liên quan.
- Chưa commit, push, deploy, restart service hoặc gọi provider trả phí trong
  lượt cập nhật tài liệu này.
- Trước commit/push bắt buộc chạy `npm run stage:coding-tools-delivery` rồi
  `npm run check:coding-tools-delivery`; giữ toàn bộ `.coding-tools/**` theo
  retention invariant và không xuất secret.
- Mỗi wave sau này phải bổ sung checkpoint gồm: thay đổi, receipt mạnh nhất,
  blocker/phân loại lỗi, việc còn lại và exact next action.

## 7. Lịch sử thay đổi tài liệu

- **21-09-2026 — Wave 24:** xác thực lại Tailscale/SSH tới
  `DESKTOP-63643J4`; focused candidate đạt **18/18 + 3/3 + 1/1 + 1/1 + 1/1**.
  Read-only probe cho thấy workspace registry chưa có, Electron/Recovery không
  chạy, Supervisor `spawn_failed` và connected agent `integrity_unproven`; ghi
  rõ reachable-for-test chưa phải live binding, không mở quyền hay admission.
- **21-09-2026 — Wave 23:** packaged/installed smoke recheck trên candidate
  Windows pass, installer `1.0.7` cleanup pass, production descriptor và
  Scheduled Task stable; củng cố `PACKAGED_PROOF`, chưa nâng live acceptance.
- **21-09-2026 — Wave 22:** Windows candidate structured workflow
  `git/build/test/deploy` **1/1 PASS** và HTTP→node journal/terminal receipt
  **1/1 PASS**; ghi rõ đây là fixture route proof, chưa phải toolchain/deploy
  thật hoặc `LIVE_ACCEPTED`.
- **21-09-2026 — Wave 21:** Tailscale/SSH tới `DESKTOP-63643J4` reachable;
  focused candidate recheck đạt **18/18 + 3/3 + 1/1 + 1/1 + 1/1** cho
  secret/rotation/workspace, same-account OAuth, two-client exec,
  document-write và standing patch. Ghi lại Ubuntu health schema 19, admission
  recovery, OAuth principals 0 và unresolved 11; đóng blocker reachability nhưng
  không nâng `LIVE_ACCEPTED`.
- **21-09-2026 — Wave 15:** full Node/Electron regression **858 PASS, 16 SKIP,
  0 FAIL / 874** và full Control Plane **295/295 PASS**; source-root/secret
  checks xanh, không nâng Windows/live proof.
- **21-09-2026 — Wave 16:** ghi nhận MCP full-suite recheck **1.145 PASS,
  8 FAIL, 7 SKIP** và phân loại proxy/child-`python`/timestamp để không dùng
  receipt xanh cũ làm current truth; bổ sung semantics UI auto-select nhưng
  server vẫn pin `binding_id`. Chỉ cập nhật tài liệu, không nâng proof.
- **21-09-2026 — Wave 17:** source-first/proxy-free MCP rerun đạt **1.152 PASS,
  1 FAIL, 7 SKIP**; SDK/operator/workspace focused retries xanh, còn một
  continuous-check test thiếu pytest trong child system Python. Không sửa policy
  để làm xanh giả; giữ blocker là dependency/harness và chưa nâng proof.
- **21-09-2026 — Wave 14:** re-run focused account/task/HTTP→node, node
  authority/credential và Node/Electron bridge/recovery groups; phân loại lỗi
  `PYTHONPATH` ban đầu là harness error và ghi receipt retry xanh. Không nâng
  Windows/live proof.
- **21-09-2026 — Wave 13:** ghi rõ account ChatGPT dùng chung một
  `principal_id`, client chọn `binding_id` theo task và lệnh chạy tại node đã
  bind; bổ sung ma trận trách nhiệm, reuse map và exact next action. Chỉ cập
  nhật tài liệu, không nâng proof package/live.
- **21-09-2026 — Wave 12:** thêm ma trận T01–T16 tách `FOCUSED_TEST_PROOF`,
  `NOT_PROVEN` và `NOT_APPLICABLE_YET`; không nâng gate Windows/live.
- **21-09-2026 — Wave 11:** đồng bộ `control-plane/README.md` để read-only/
  context chỉ còn compatibility-only và trusted standing account flow là
  current contract.
- **21-09-2026 — Wave 10:** refresh Linux unpacked candidate, resource
  sanitation/exact-source verification, packaged/installed smoke và recheck
  HTTP two-client/document-write/structured-exec; không nâng mức Windows/live.
- **21-09-2026 — Wave 9:** Supervisor preflight chuyển từ read-only pilot TTL
  sang standing file-read/approved-patch/exec; chấp nhận marker DPAPI an toàn;
  giữ fail-closed theo identity/workspace/resource.
- **21-09-2026 — Bản cập nhật này:** gom semantics một account nhiều client,
  reuse map, hiện trạng bằng chứng và plan P0–P6 vào một file điều hành duy nhất;
  không thay đổi quyền live hay triển khai.

### Checkpoint kết nối test Windows `DESKTOP-63643J4` — 21-09-2026

Kết nối Tailscale/SSH tới `100.72.186.41` đã xác thực. Candidate cô lập tại
`E:\DEV\Codex-web-candidate-502ffb8`, không ghi đè checkout chính của máy
Windows. Shared-account contract đã được test trên chính máy này: các client
khác token nhưng cùng `issuer/subject` dùng cùng `principal_id`, chọn
`binding_id`, mở task/claim writer và route `exec` tới cùng node/workspace;
client còn lại đọc được cùng status/output/receipt. Kết quả focused:
**3 OAuth binding tests PASS + 1 two-client exec E2E PASS**.

HTTP→node parity cho file-read, document-write, approved-patch và exec là
**22/22 PASS**; Recovery process là **3/3 PASS**. Đây là proof unpacked/source
trên Windows, không phải proof cài đặt/reboot/live. Full MCP có 2 lỗi fixture
OS-specific (Landlock message và `echo` shell builtin); OAuth config có 4 lỗi
do assertion POSIX file mode trên NTFS. Không dùng các lỗi đó để hạ thấp
quyền/runtime; cần sửa hoặc đánh dấu portability harness riêng.

Packaged gate trên candidate cũng đã pass: `dist:dir`, packaged recovery smoke
và NSIS `1.0.7` build. Installed smoke cài/gỡ trong thư mục tạm, giữ nguyên
production Recovery descriptor và Scheduled Task. Đây là packaged evidence,
chưa phải reboot/live/owner acceptance.

Sau đó đã harden ACL thật cho node config và local policy/journal JSON trên
Windows. Probe DPAPI + `icacls` trong source và packaged Python đều chỉ còn
current user + SYSTEM + Administrators; HTTP→node E2E sau thay đổi vẫn **22/22
PASS**. Vì vậy credential boundary hiện có packaged proof mạnh hơn, nhưng
rotation/revoke/reconnect live vẫn còn mở.
