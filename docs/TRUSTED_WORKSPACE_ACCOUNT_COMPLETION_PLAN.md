# Kế hoạch hiện hành: máy tin cậy lâu dài, workspace dùng chung qua tài khoản ChatGPT

> Bản tóm tắt điều hành cô đọng, có reuse map và next action:
> [SHARED_ACCOUNT_WORKSPACE_STATUS.md](SHARED_ACCOUNT_WORKSPACE_STATUS.md).
> Quy trình đóng gate Windows exact nằm ở
> [WINDOWS_EXACT_VALIDATION_RUNBOOK.md](WINDOWS_EXACT_VALIDATION_RUNBOOK.md).
> Tài liệu này tiếp tục giữ chronology, receipt và các gate chi tiết.

## Trạng thái điều hành mới nhất — `DESKTOP-63643J4` — 21-09-2026, 21:42 +07

Wave 44 đã đồng bộ commit delivery receipt `dcb3fc492b22d1b04547f3eae1c595b4ee6e4ce0`
giữa Linux/GitHub và Windows. Đây là `.coding-tools` evidence-only delta, không
đổi package-relevant source; Windows worktree sạch, installer hash vẫn
`61fb7fa5785c3861fcd4c8371f54172894472c9a0b7d48854c5cb05126d7c14e`.
Runtime vẫn `MISSING/RECOVERY_DESCRIPTOR_STALE`, nên chưa có `LIVE_ACCEPTED`.

Wave 45 đã thử `dev-ui-lifecycle.js refresh` từ phiên `Admin` tương tác. Host
bootstrap thành công và tạo refresh epoch, nhưng runtime dừng trước postflight
vì thiếu Runtime API Key trong profile local; epoch kết thúc `FAILED` với
`ACTIVATION_EPOCH_FAILED`. Đã dọn task/PID/script/log tạm, không xoá profile,
credential hoặc workspace. Owner cần chọn local-key qua UI hoặc central pairing
đúng contract trước khi thử refresh/preflight lại.

Wave 43 đã đồng bộ exact source giữa Linux/GitHub và Windows `E:\DEV\Codex-web`
ở `main @ fa055951d912997d75c9de5d7d18ee42f72b3094`; Windows worktree sạch.
Delta này chỉ là tài liệu/evidence sau build `bb4522c`, không làm thay đổi package
runtime; installer `1.0.7` vẫn có SHA-256
`61fb7fa5785c3861fcd4c8371f54172894472c9a0b7d48854c5cb05126d7c14e`.

Read-only status vẫn `MISSING/RECOVERY_DESCRIPTOR_STALE` và preflight vẫn
fail-closed vì Recovery Host owner không sống. Mức proof là
`SOURCE_PRESENT + FOCUSED_TEST_PROOF + PACKAGED_PROOF`, chưa `LIVE_ACCEPTED`.
Không tự tạo closure/epoch hoặc mở admission; gate kế tiếp là owner desktop
interactive tạo closure đủ năm trường cho đúng HEAD, rồi preflight/activation.

Wave 41 đã đối chiếu Linux, GitHub `origin/main` và checkout exact Windows
`E:\DEV\Codex-web` ở `main @
7f26754657c5a1e933dea000fb75a0624e72f152`. `npm ci` và `npm run dist` đạt
Node/Electron **922/922 PASS** và MCP **1160/1160 PASS**; packaged/installed
smoke đều pass, installer `1.0.7` có SHA-256
`dcf1f5535eacb3e5c66d3a246503bec5dbcf949833b6e476b83576574a68351b`.
Installed smoke đã cleanup nên runtime hiện không chạy (`dev-ui
state=MISSING`, full-clean preflight `ENOENT` thiếu `recovery-host.json`).
Mức bằng chứng là exact candidate `PACKAGED_PROOF`, chưa `LIVE_ACCEPTED`.
Không có credential/context/admission/binding/task/deploy mutation trong wave
này. Gate còn lại là owner acceptance exact source + supported full-clean
activation, sau đó mới enrollment/workspace generation/binding/task, T01–T16,
restore và soak.

## Checkpoint Wave 41 — activation incomplete và Ubuntu package drift — 21-09-2026, 20:05 +07

Runtime packaged trên Windows đã được quan sát với Recovery Host/MCP/UI owner
identity hợp lệ, nhưng strict snapshot vẫn là `workspace=""`,
`mcpRunning=false`, `centralConnected=false`, `authorityReady=false`,
`componentsReady=false`, `fullyReady=false`, `updateIncomplete=true`, closure
trống và connector `UNAVAILABLE`.

Một activation owner attempt đã tạo epoch nhưng dừng ở
`STOPPING`/`admission=CLOSED`; không có replacement process và descriptor trở
thành stale. Đây là failure/incomplete state, không được tự sửa epoch hoặc
forge checkpoint. Task `CodingTools-StageA-Deferred-Worker` cũ trỏ tới file tạm
đã mất đã được gỡ; profile và credential giữ nguyên.

Control Plane Ubuntu vẫn chạy release cũ, package fingerprint không khớp source
HEAD `7f267546`, admission `recovery`, `oauth_principals=0`; SSH quản trị bị từ
chối nên chưa thể deploy release mới. Next action vẫn là owner closure exact
source → preflight/activation Windows → strict heartbeat/workspace binding;
đồng thời cần quyền SSH hợp lệ để verify/deploy Ubuntu release cùng HEAD.

## Checkpoint Wave 42 — exact Windows package rebuilt and installed — 21-09-2026, 21:25 +07

Exact checkout `bb4522c` trên Windows đã hoàn tất `npm run dist`: Node/Electron
**922/922 PASS**, MCP **1160/1160 PASS trong 2764,26s**, resource verification
PASS. Installer `1.0.7` SHA-256 là
`61fb7fa5785c3861fcd4c8371f54172894472c9a0b7d48854c5cb05126d7c14e`; executable
installed/unpacked khớp SHA-256 `a57ced0d185472d5c5e234a1177bf13ca35f14d2661300fc80e92c6daa7ecbd2`.
Packaged recovery smoke PASS với 17 resources/8 tools và production isolation.

Không có source runtime mutation; icon build tạm đã được trả về HEAD. Runtime
production chưa mở lại sau activation `STOPPING/CLOSED`, nên chưa tạo closure,
workspace, connector ACK, binding/task hay admission. Ubuntu release exact đã
verify cục bộ nhưng chưa deploy vì SSH bị từ chối.

## Checkpoint Wave 40 — installed artifact hiện diện, GUI SSH không khởi động — 21-09-2026, 19:31 +07

Installer exact `1.0.7` đã cài per-user tại
`C:\Users\Admin\AppData\Local\Programs\Coding Tools MCP`; registry và
executable installed khớp unpacked artifact. Không có process Electron,
Recovery Host hoặc Supervisor Task sau khi thử launch qua SSH (kể cả TTY),
`recovery-host.json` chưa tồn tại và preflight trả `ENOENT`. Không có
credential/context/admission/binding/task mutation. Gate tiếp theo là owner mở
ứng dụng từ desktop interactive, tạo acceptance closure exact source, rồi mới
full-clean activation và strict heartbeat.

Tailscale/SSH tới `100.72.186.41` đã mở; Wave 26 xác thực node và Wave 27
đã xác thực packaged candidate.
Candidate cô lập trên máy Windows đã
đạt shared-account OAuth/binding và two-client exec E2E, HTTP→node **22/22**,
Recovery process **3/3**, packaged/installed smoke và NSIS installer. Mức hiện
tại là **`SOURCE_PRESENT + FOCUSED_TEST_PROOF + candidate PACKAGED_PROOF`**;
chưa phải `LIVE_ACCEPTED`; Wave 32 đã mở Recovery Host candidate tạm thời để
kiểm IPC rồi dọn sạch, nên runtime live hiện lại chưa có process; registry mới
chỉ là local/node registration chứ chưa có OAuth binding/task.
Full MCP candidate receipt đã là **1.160/1.160
PASS** và Node/Electron **922/922 PASS**; bốn assertion OAuth config còn lại
chỉ là fixture NTFS/POSIX-mode `0400/0600`, không được nới security policy để
làm xanh giả.

## Checkpoint Wave 37 — SSH handoff packaged pass, activation/workspace còn chờ — 21-09-2026, 13:36 +07

Qua SSH trên `DESKTOP-63643J4`, đã hoàn tất handoff được bảo vệ: xác thực
Recovery Host development cũ bằng IPC, gọi `runtime.stop`, kiểm creation
identity rồi terminate đúng cây process. Supervisor packaged dựng host mới và
agent candidate vẫn `running`; `recovery.ping` trả `ready=true`. Không kill
theo tên, không đụng credential.

Strict runtime chưa mở: `central_connected=true`, nhưng
`authority_ready=false`, `central_status_reason=LOCAL_EXECUTOR_NOT_READY`,
`fully_ready=false`, `update_incomplete=true`. Epoch durable đang `FAILED` với
`RECOVERY_REPLACEMENT_TARGET_CHANGED`, nên không gọi `runtime.start`, không
dequeue/execute action và không gọi model.

Workspace registry local đang trỏ tới candidate root
`E:\DEV\Codex-web-candidate-502ffb8` với capability `{read,write,exec}`; mục
tiêu thực là `E:\DEV\Codex-web`. Không tự chạy `replace-workspace`: luồng này
giữ opaque `workspace_id` nhưng retire generation cũ, tắt policy local và
fence binding/task của mọi client dùng chung tài khoản. Cần owner xác nhận đổi
generation (hoặc chọn đăng ký workspace mới) trước khi tạo mutation trung tâm.

Mức proof hiện tại vẫn `SOURCE_PRESENT + FOCUSED_TEST_PROOF + candidate
PACKAGED_PROOF`, chưa `LIVE_ACCEPTED`. Next action theo thứ tự: (1) owner
chốt workspace root/generation; (2) tạo closure exact source hợp lệ; (3)
full-clean activation và Supervisor exact artifact; (4) strict heartbeat,
binding/task, rồi mới T01–T16/soak.

## Checkpoint Wave 38 — CLI hiện chưa hỗ trợ migrate canonical path — 21-09-2026

Đã thực hiện lệnh `replace-workspace` được owner xác nhận với
`E:\DEV\Codex-web`; kết quả fail-closed là
`CONTROL_PLANE_WORKSPACE_REPLACEMENT_NOT_FOUND`. Implementation hiện tại chỉ
cho replacement khi `--workspace-path` đã tồn tại trong local registry (đổi
label/capability); nó không tự suy ra old entry khi path thay đổi. Lệnh dừng
trước network mutation: không retire generation, không register generation mới,
không tạo journal và không thay local policy.

Fallback `retire-workspace` rồi `register-workspace` sẽ đổi cả `workspace_id`,
do đó không được tự chạy khi mục tiêu là giữ shared-account identity. Còn hai
lựa chọn đúng: (a) owner chọn một workspace mới/ID mới; hoặc (b) cập nhật
product + packaged artifact để có path migration explicit (old workspace ID /
generation), rồi chạy lại full replacement. Strict runtime vẫn đang đóng ở
`LOCAL_EXECUTOR_NOT_READY`; không được coi lỗi CLI này là bằng chứng execution.

## Checkpoint Wave 36 — BLOCKED: chờ owner activation — 21-09-2026, 12:41 +07

Recheck chính thức vẫn `dev:status=MISSING/RECOVERY_DESCRIPTOR_STALE` và
Supervisor `Running` nhưng `spawn_failed/SPAWN_FAILED` vì executable thiếu.
Blocker này lặp lại qua Waves 33–36; source proof **133 pass, 0 fail, 1 skip**
đã đủ cho phần lifecycle, nhưng không thể thay thế external owner acceptance.

Đánh dấu điều hành **BLOCKED** cho tới khi owner trên Windows chạy acceptance
ceremony + supported full-clean activation trên exact source/artifact, rồi
Supervisor install nếu cần. Không forge closure, không sửa epoch bằng tay.

## Checkpoint Wave 35 — source lifecycle proof 133/133, live gate chưa mở — 21-09-2026, 12:39 +07

Source lifecycle/full-clean/Supervisor focused suite đạt **133 pass, 0 fail,
1 skip**; skip là runtime Supervisor Windows-only. Bằng chứng xác nhận các
guard đang từ chối đúng khi descriptor stale/closure không đủ, không tự cấp
quyền từ epoch durable và không biến source test thành live acceptance.

Windows target vẫn `RECOVERY_DESCRIPTOR_STALE` và `SPAWN_FAILED`; chưa có
process/runtime live, binding/task live hay owner acceptance. Mức hiện tại vẫn
`SOURCE_PRESENT + FOCUSED_TEST_PROOF + candidate PACKAGED_PROOF`.

## Checkpoint Wave 34 — lifecycle/preflight chính thức vẫn fail-closed — 21-09-2026, 12:36 +07

Read-only `dev:status` trên checkout Windows và candidate đều trả
`state=MISSING`, `host=unavailable`, `error_code=RECOVERY_DESCRIPTOR_STALE`.
`full-clean-activation --preflight` cũng từ chối với cùng mã vì Recovery Host
owner không còn sống. Supervisor Task vẫn `Running` nhưng status là
`spawn_failed`/`SPAWN_FAILED` vì executable bị thiếu.

Đây là bằng chứng lifecycle chính thức, không chỉ là suy luận từ file state.
Không được retry mù, sửa epoch hoặc chép acceptance; phải khôi phục exact
source/closure trước, rồi dùng installer Supervisor được hỗ trợ và kiểm strict
identity. Mức proof chưa đổi và chưa có binding/task live.

## Checkpoint Wave 33 — Windows target reachable, chưa có runtime live — 21-09-2026, 12:29 +07

Đợt kiểm tra chỉ-đọc xác nhận `DESKTOP-63643J4` (`100.72.186.41`) vẫn mở để
test. Checkout Windows `E:\DEV\Codex-web` là HEAD
`3779096a9156bf2827e3164d09bcc1ef647a2c01` với 23 thay đổi; candidate `1.0.7`
ở `E:\DEV\Codex-web-candidate-502ffb8` không có `.git`. Profile runtime giữ
closure cũ (`source_checkpoint_id=8d10f27638e2498cba80edf0bcbe77ce`, accepted
HEAD `cffd2acee24a4f38f4a83ddfea4c40f766de7a63`), dù đánh dấu
`activation_eligible=true` thì `affected_components=[]`,
`components_current=false`, `lifecycle_clean=false`.

Epoch durable báo `READY/OPEN` nhưng không có process hiện tại chứng minh epoch
đó: Recovery Host owner PID đã chết, runtime PID/revision là stale và
Supervisor đang `spawn_failed`/`SPAWN_FAILED`. Vì vậy không nâng mức proof,
không tạo binding/task live và không chạy canary workspace. Blocker là
exact-source/accepted-closure mismatch cùng Supervisor manifest stale; mạng
Tailscale không phải blocker.

**Bằng chứng hiện tại vẫn:** `SOURCE_PRESENT + FOCUSED_TEST_PROOF + candidate
PACKAGED_PROOF`, chưa `LIVE_ACCEPTED`. Bước kế tiếp duy nhất là owner chạy
acceptance ceremony + full-clean activation trên exact source/artifact được
chấp thuận, khôi phục Supervisor qua installer hỗ trợ nếu cần, rồi xác nhận
strict `mcp_ready`, identity, central connection, authority và `fully_ready`.

## Checkpoint Wave 32 — Tailscale live test và runtime gate — 21-09-2026, 12:10 +07

Tailscale/SSH tới `DESKTOP-63643J4` (`100.72.186.41`) xác nhận đúng user
`Admin`. Manifest supervisor installed vẫn trỏ tới executable đã bị uninstall;
candidate unpacked `1.0.7` còn đủ `Coding Tools MCP.exe` và installer.

Recovery Host candidate được mở tạm trên data root hiện hành và trả
`recovery.ping ok=true/ready=true`; descriptor owner/instance và packaged
installation identity được kiểm bằng process sống. Strict identity observation
cho thấy `mcp_ready=false`, `identity_current=false`; runtime snapshot giữ
`central_connected=false`, `authority_ready=false`,
`central_status_reason=LOCAL_EXECUTOR_NOT_READY`, `fully_ready=false`,
`update_incomplete=true`, `recovery_blocked=true`. RPC `runtime.start` trả
HTTP 409 `UPDATE_INCOMPLETE`, vì epoch cũ không cho thay Coding MCP tại chỗ; cần
full-clean activation epoch mới có owner authority.

`runtime-heartbeat` exit 0 nhưng chỉ `degraded/packaged_runtime_unready`,
`runtime_state=unknown`, `fully_ready=unknown`, `policy_state=expired_or_disabled`;
route evidence `fresh`. Không poll/dequeue action, không receipt, không gọi
model. Candidate process đã được dừng sau test; hiện còn 0 process và descriptor
chỉ là stale metadata; Supervisor ghi `OWNER_DEAD` ngay sau cleanup rồi trở lại
`SPAWN_FAILED` ở lần retry vì executable trong manifest vẫn thiếu.

Wave này chỉ đóng **Tailscale reachability + Recovery IPC proof**, không đóng
runtime execution, OAuth binding/task, toolchain thật hay `LIVE_ACCEPTED`.

## Checkpoint Wave 26 — Tailscale candidate recheck và connected-agent — 21-09-2026, 11:27 +07

Tailscale tới `DESKTOP-63643J4` (`100.72.186.41`) trả lời qua DERP HKG;
SSH xác nhận đúng user `DESKTOP-63643J4\Admin` và candidate
`E:\DEV\Codex-web-candidate-502ffb8`. Focused receipt mới trên target:
secret/rotation/workspace **18/18 PASS**; cùng account OAuth/binding
**3/3 PASS** (28 deselected); two-client exec **1/1 PASS** (12 deselected);
document-write **1/1 PASS** (2 deselected); standing patch **1/1 PASS**
(4 deselected). Standing-patch fixture có cảnh báo teardown `WinError 10038`
nhưng không có test failure hay production effect.

Credential node gửi `heartbeat --readiness degraded` thành công (`exit 0`,
`last_seen_at_ms` có giá trị). Local registry có đúng một workspace opaque
`workspace_a84ba281f3ef4365b949b1b35376dfba`, generation
`generation_63c426bce483466e9ced0087a9d75377`, capability `{read,write,exec}`.
Probe hiện hành không thấy process Electron/Node; `runtime-heartbeat` báo
`blocked`, reason `runtime_unavailable`, identity `unreported`, state `MISSING`.
`run-connected-agent` với một iteration kết thúc `MAX_ITERATIONS_REACHED`; năm
lane đều không bắt đầu vì runtime unavailable, không nhận action và không gửi
receipt.

Wave này chỉ củng cố **reachable + credential/registry + candidate focused
proof**. Nó không tạo OAuth `principal_id`/`binding_id`/task live, không mở
admission Ubuntu, không ghi workspace, reboot/restart/deploy, commit hoặc push.
Giữ mức **`SOURCE_PRESENT + FOCUSED_TEST_PROOF + candidate PACKAGED_PROOF`**;
next action là owner chạy đúng Electron/Recovery packaged runtime, strict
identity/heartbeat, rồi mới kiểm binding/task pin, Git/build/test/deploy thật,
T01–T16, restore/soak và owner acceptance.

## Checkpoint Wave 27 — packaged recovery smoke cô lập — 21-09-2026, 11:38 +07

Candidate `E:\DEV\Codex-web-candidate-502ffb8` chạy official
`scripts/packaged-recovery-smoke.js` với **exit 0**. Receipt mới xác nhận
17 resources, app.asar/executable, smart-v3 đúng 8 public tools, Recovery Host
ready, device identity, `independent_mcp_tunnel_v1`, Recovery MCP alive,
Supervisor healthy và hai đường fail-closed live-owner/hash-mismatch; production
descriptor vẫn ổn định, không mutate Scheduled Task. User-data được cô lập trong
TEMP và đã cleanup, không còn process candidate sau smoke.

Wave này nâng độ chắc của **candidate PACKAGED_PROOF** nhưng không biến thành
`LIVE_ACCEPTED`: chưa chứng minh startup installed, strict heartbeat trên
runtime owner thật, OAuth `principal_id`/`binding_id`/task, toolchain thật,
T01–T16, restore/soak hoặc owner acceptance.

## Checkpoint Wave 28 — central health và source capability recheck — 21-09-2026, 11:41 +07

Read-only `/healthz` Ubuntu sau heartbeat vẫn giữ SQLite `ok`, schema **19**,
`admission_mode=recovery`, package SHA actual/expected khớp,
`oauth_principals=0`, `node_workspaces=3`, unresolved **11** (10 quarantined,
1 unquarantined). Không có admission change hoặc action reconciliation.

Targeted source recheck bằng `unittest` đạt **7/7 PASS**: account/binding/writer
handoff **4/4**, local exec/document-write/standing patch **3/3**. System Python
không cài `pytest` nên lệnh pytest local được phân loại environment gap; không
đổi code để làm xanh giả. Candidate Windows pytest receipts vẫn giữ nguyên.

Wave này củng cố source/central evidence, không tạo OAuth live binding/task và
không nâng mức khỏi `SOURCE_PRESENT + FOCUSED_TEST_PROOF + candidate
PACKAGED_PROOF`.

## Checkpoint Wave 29 — full Control Plane source discovery — 21-09-2026, 11:44 +07

Toàn bộ `control-plane/tests` chạy bằng stdlib `unittest discover` đạt
**298/298 PASS trong 96,772s**. Các fixture receipt lifecycle/unknown-state
đúng expected; không có source regression và không tạo action live. Đây là
source proof bổ sung, chưa chứng minh installed runtime, OAuth UI two-client,
toolchain thật, fault/restore/soak hoặc owner acceptance.

## Checkpoint Wave 30 — installed NSIS smoke và isolation — 21-09-2026, 11:49 +07

Candidate Windows chạy `scripts/installed-recovery-smoke.js` với **exit 0**.
Installer `1.0.7` install/register pass; packaged smoke bên trong pass với 17
resources, smart-v3 8 tools, Recovery/MCP/device identity/Supervisor healthy;
uninstall pass và executable/user-install registration được dọn sạch. Production
Recovery descriptor và Scheduled Task definition stable.

Đây là installed candidate proof, chưa phải reboot/logon/reconnect, OAuth live
binding/task, workspace toolchain thật, T01–T16, restore/soak hoặc owner
acceptance.

## Checkpoint Wave 31 — post-smoke read-only state — 21-09-2026, 11:51 +07

Sau installed smoke, target không còn process `Coding Tools MCP`/Electron/Node.
Descriptor production còn metadata nhưng owner process không sống, nên được phân
loại stale/observation-only; descriptor tồn tại không chứng minh runtime ready.
Ubuntu `/healthz` vẫn SQLite `ok`, schema 19, `admission_mode=recovery`,
`oauth_principals=0`, `node_workspaces=3`, unresolved **11**. Không có live
action, admission change hoặc production restart.

## Checkpoint Wave 25 — heartbeat, node workspace registration và standing policy — 21-09-2026

Từ candidate đã gửi `heartbeat --readiness degraded` bằng credential node đã
enroll; Ubuntu trả `exit 0` và `last_seen_at_ms`, chứng minh credential dài hạn
vẫn xác thực được. `runtime-heartbeat` và một vòng `run-connected-agent` đều
fail-closed vì Electron/Recovery chưa chạy (`runtime_status_unavailable` /
`CONTROL_PLANE_BRIDGE_FAILED`); không có lane nào poll hoặc dequeue action.

Candidate workspace test đã đăng ký qua `/workspace-registrations` với:

- `workspace_id=workspace_a84ba281f3ef4365b949b1b35376dfba`;
- `workspace_generation=generation_63c426bce483466e9ced0087a9d75377`;
- capability local `{read:true,write:true,exec:true}`.

Đây là **node workspace registration**, chưa phải OAuth `binding_id`: Ubuntu
vẫn `admission_mode=recovery`, `oauth_principals=0`, chưa có task/action mới.
Local standing policies đã cài trên candidate data root (file-read 3 path,
approved-patch 1 path, exec 6 argv prefix; không hết hạn). `icacls` xác nhận
mọi file config/registry/policy chỉ còn current user, SYSTEM và
Administrators; không có broad `Users`/`Authenticated Users` grant.

Ubuntu health read-only sau đăng ký: `node_workspaces=3`, SQLite `ok`, package
SHA khớp expected, unresolved actions vẫn **11** (10 quarantined, 1 chưa
quarantine). Wave này có thay đổi có kiểm soát ở node workspace registry,
heartbeat và local test policy; không tạo OAuth principal/binding/task, không
ghi file workspace, không reboot/restart/deploy/commit/push.

Mức bằng chứng giữ **`SOURCE_PRESENT + FOCUSED_TEST_PROOF + candidate
PACKAGED_PROOF`**, chưa `LIVE_ACCEPTED`. Next action: owner phải mở runtime
Electron/Recovery đúng data root packaged, kiểm runtime identity/heartbeat rồi
mới thử connected-agent; sau đó mới tạo OAuth principal/binding và kiểm hai
client thật.

## Checkpoint Wave 24 — kiểm thử lại kết nối Tailscale và candidate — 21-09-2026, 10:59 +07

Kết nối Tailscale/SSH tới `DESKTOP-63643J4` (`100.72.186.41`, user `Admin`)
đã được xác thực lại. Tôi chỉ chạy candidate cô lập version `1.0.7`, không
dùng credential thật và không chạm checkout/production data root trên máy đích.

| Lane | Receipt mới nhất | Cách đọc |
| --- | --- | --- |
| Secret/rotation/workspace | **18/18 PASS** trong 4,37s | Node lifecycle fixture trên Windows candidate |
| Same-account OAuth/binding | **3 PASS**, 28 deselected trong 10,32s | Hai client fixture cùng `principal_id`, task vẫn pin `binding_id` |
| Two-client exec route | **1/1 PASS** trong 9,61s | Route/receipt proof, chưa phải ChatGPT UI live |
| Document write | **1/1 PASS** trong 4,91s | HTTP → node → Recovery fixture |
| Standing patch | **1/1 PASS** trong 10,43s | Local standing policy/receipt fixture |

Probe read-only trên data root hiện hành cho thấy `control-plane-node.json` có
credential metadata nhưng `control-plane-workspaces.json` chưa tồn tại;
`list-workspaces` trả `{"workspaces":[]}`. Không có Electron/Recovery process
đang chạy; Supervisor hiện `spawn_failed`, connected agent
`integrity_unproven`. Gọi `inspect-read-only-policy` bằng `runtime-mode=packaged`
trên data root dev bị từ chối có mã
`CONTROL_PLANE_POLICY_PACKAGED_DATA_ROOT_FORBIDDEN`. Đây là bằng chứng máy
reachable để test, không phải bằng chứng runtime live đã bind workspace.

Wave 24 củng cố **`SOURCE_PRESENT + FOCUSED_TEST_PROOF + candidate
PACKAGED_PROOF`**, không nâng `LIVE_ACCEPTED`. Không mở admission Ubuntu, không
tạo OAuth principal/binding/action live, không rotate/revoke credential thật,
không reboot/restart/deploy/commit/push. Next action chính xác là owner cung cấp
cửa sổ test account/data root được phép để pair/enroll → register workspace →
kiểm `binding_id`/heartbeat → chạy `run-connected-agent`, rồi mới kiểm reboot/
reconnect/rotation/revoke và hai client thật.

## Checkpoint Wave 23 — packaged và installed smoke recheck — 21-09-2026, 10:48 +07

Trên candidate Windows hiện hành, không chạm production descriptor hoặc
Scheduled Task:

- Packaged smoke trả `ok=true`: executable/app.asar hợp lệ, **17 required
  resources**, smart-v3 đủ **8 public tools**, Recovery Host/MCP healthy,
  `independent_mcp_tunnel_v1`, device identity có mặt, Supervisor healthy và
  hai đường `live_owner_fail_closed`/`hash_mismatch_fail_closed` pass;
  `scheduled_task_mutation=false`.
- Installed smoke với installer **1.0.7**: install/register pass, chạy lại
  packaged smoke pass, uninstall thành công, file/registration được dọn sạch;
  production Recovery descriptor và Scheduled Task definition giữ nguyên.

Wave 23 củng cố **candidate `PACKAGED_PROOF`** và isolation, không chứng minh
reboot/logon, credential reconnect/rotation/revoke, task live hoặc owner
acceptance. Next action vẫn là test account được phép cho installed
rotation/reconnect, rồi hai client thật và workspace/toolchain thật.

## Checkpoint Wave 22 — structured toolchain parity trên Windows candidate — 21-09-2026, 10:45 +07

Trên cùng candidate cô lập, với `PYTHONPATH` chỉ ở process test và không dùng
credential thật, đã chạy thêm hai ca focused:

- `test_oauth_exec_workflow_parity_uses_one_local_lane`: **1/1 PASS trong
  6,38s**; các argv `git --version`, `npm run build`, `npm test`,
  `npm run deploy` đi qua cùng local structured lane, cùng task/writer/receipt.
- `test_oauth_exec_runs_through_http_node_journal_and_terminal_status`:
  **1/1 PASS trong 4,30s**; HTTP → node journal → Recovery → terminal receipt
  được xác nhận trên candidate Windows.

Đây là proof route/authority/receipt của fixture deterministic, không phải bằng
chứng đã build/test/deploy workspace thật hoặc đã deploy production. Ubuntu
health vẫn `admission_mode=recovery`, `oauth_principals=0`; không tạo account,
binding hay action live.

Wave 22 nâng bằng chứng candidate cho T06/T09, không nâng `LIVE_ACCEPTED`.
Next action vẫn là installed rotation/revoke + reboot/logon/reconnect bằng test
account được phép, sau đó hai client ChatGPT thật cùng `principal_id`, toolchain
workspace thật, T01–T16, restore/soak và owner acceptance.

## Checkpoint Wave 21 — kết nối Windows mở lại và focused recheck — 21-09-2026, 10:31 +07

Đã xác minh trực tiếp qua Tailscale/SSH, không đoán alias hay target khác:

- `DESKTOP-63643J4` (`100.72.186.41`) trả lời dưới `DESKTOP-63643J4\Admin`;
  Windows 11 Pro Insider Preview, PowerShell 5.1.
- Candidate cô lập `E:\DEV\Codex-web-candidate-502ffb8` tồn tại, version
  `1.0.7`, có `node_modules`, `dist\win-unpacked` và
  `coding-tools-mcp-setup-1.0.7.exe`; candidate không có `.git`, nên không được
  gọi là checkout phát hành và không đụng checkout chính trên máy đích.
- Chạy lại bằng `PYTHONPATH` process-local, không dùng credential thật:
  **18/18 PASS** cho node secret/rotation/workspace (**4,20s**), **3/3 PASS**
  cho ba test same-account OAuth/binding (**8,84s**), **1/1 PASS** cho
  two-client exec route/receipt (**3,59s**), **1/1 PASS** document-write qua
  Recovery (**4,58s**) và **1/1 PASS** standing approved-patch (**9,15s**).
- Receipt candidate trước đó vẫn giữ nguyên: full MCP **1.160/1.160 PASS**
  trong **1.905,35s (31m45s)** và Node/Electron **922/922 PASS**. Đây là
  candidate proof; bốn OAuth config assertion NTFS/POSIX-mode không nằm trong
  đường shared-account execution và không phải lý do để hạ local ACL/secret
  policy.
- Ubuntu `/healthz` read-only hiện trả `ok=true`, schema **19**, SQLite `ok`,
  `admission_mode=recovery`, counts `nodes=3`, `enrollment_requests=4`,
  `bindings=4`, `contexts=24`, `work_requests=18`, `actions=18`,
  `receipts=13`, `oauth_principals=0`; unresolved actions **11** (10 đã
  quarantine, 1 còn unquarantined). `mcp_authentication_mode` vẫn là
  `legacy_context_grant`; package source SHA khớp expected SHA.

Wave 21 đóng blocker **target chưa reachable** của Wave 20, nhưng không tự mở
quyền live. Mức chứng cứ hiện tại là
**`SOURCE_PRESENT + FOCUSED_TEST_PROOF + WINDOWS_UNPACKED_CANDIDATE + candidate
PACKAGED_PROOF`**; chưa phải `LIVE_ACCEPTED`. Các focused test trên là fixture
local của candidate, không thay cho hai ứng dụng ChatGPT thật cùng OAuth
`principal_id` qua UI, reboot/logon/reconnect/rotation/revoke trên installed
artifact hay toolchain workspace thật.

**Next action chính xác:** dùng cửa sổ Windows đang mở để chạy rotation/revoke
và reboot/logon/reconnect trên installed candidate với test account được phép;
đối chiếu inventory/`binding_id` rồi chạy hai client thật cùng
`principal_id`, observe/stop/handoff, Git/build/test/deploy giả lập có kiểm soát,
T01–T16, backup/restore và soak 24 giờ. Chỉ sau owner acceptance mới nâng
`LIVE_ACCEPTED`; không tự xử lý unresolved action Ubuntu, không mở admission,
không deploy/restart service hoặc gọi provider trả phí.

## Checkpoint Wave 20 — kiểm tra target Windows và bảo toàn evidence — 21-09-2026, 08:18 +07

Đã thực hiện các kiểm tra read-only để mở gate Windows mà không tự ý ghi hoặc
restart hệ thống ngoài:

- SSH alias Windows đã biết `daochienthang` không kết nối được trong timeout 5s;
  không có test, copy source, cài đặt hay mutation nào được thực hiện trên máy
  đó.
- Workspace Linux không có `dist/win-unpacked` hoặc installer Windows hiện
  hành; artifact `dist/linux-unpacked` chỉ là preflight platform khác.
- `npm run check:coding-tools-history`: **PASS (4.873 files)**; repository
  secret check: **PASS**. `.coding-tools` evidence vẫn hợp lệ và không bị mở
  rộng ignore.

Wave 20 củng cố rằng blocker hiện tại là **external-state/Windows runner
availability**, không phải failure source/local. Wave 18 vẫn là source/local
regression baseline và Wave 19 là platform classification; chưa nâng
`PACKAGED_PROOF`/`LIVE_ACCEPTED`.

Đã thêm [runbook Windows exact](WINDOWS_EXACT_VALIDATION_RUNBOOK.md) với điều
kiện đầu vào, lệnh smoke/package/installed, enrollment một lần, hai client cùng
`principal_id`, execution parity, fault matrix và exit criteria. Runbook không
thực hiện mutation; nó là gói bàn giao để chạy ngay khi target reachable.

**Next action chính xác:** khi có Windows runner/target reachable và được phép
thực hiện, chạy candidate cùng HEAD qua Recovery/packaged/installed smoke,
DPAPI/ACL/reboot/reconnect/rotation rồi T01–T16/two-client/toolchain/soak.
Trong lúc chưa có target, tiếp tục chỉ làm source/focused/evidence checks; không
đoán credential, không retry vô hạn, không deploy/restart.

## Checkpoint Wave 19 — Recovery/packaged gate phân loại theo nền tảng — 21-09-2026, 08:14 +07

Đã chạy hai lane phụ thuộc Windows trên source hiện tại để xác định blocker
thật, không dùng skip làm pass:

| Lane | Receipt | Phân loại |
| --- | --- | --- |
| `npm run test:recovery:e2e` | **3 tests, 0 PASS, 3 SKIP, 0 FAIL** trong **285ms** | Cả ba ca được đánh dấu `win32`; không phải source failure |
| `npm run test:recovery:packaged` | `dist:dir` dựng Linux unpacked candidate; `packaged-recovery-smoke.js` trả `{ok:true, skipped:true, reason:"windows_only"}` | Linux packaging/resource preflight; chưa phải Windows packaged proof |

Wave 19 không thay đổi source hoặc quyền live. Artifact `dist/linux-unpacked`
chỉ là output ignored của preflight; không được xem là installer Windows,
RunAsNode, Recovery Host, DPAPI/ACL hay startup/reconnect evidence.

**Ý nghĩa:** blocker còn lại là cần một Windows exact runner/máy test, không phải
failure của source hiện tại. Giữ receipt Wave 18 làm full source/local regression
gate và chuyển candidate sang Windows để đóng T01/T02/T08/T10/T13/T15/T16,
two-client acceptance, fault matrix, backup/restore và soak.

**Next action chính xác:** trên Windows candidate cùng HEAD chạy
`npm run test:recovery:e2e`, `npm run test:recovery:packaged`, installed smoke,
DPAPI/ACL/reboot/reconnect/rotation; sau đó mới nghiệm thu hai client cùng
`principal_id` chọn đúng `binding_id`. Không commit, push, deploy, restart
service hoặc gọi provider trong Wave 19.

## Checkpoint Wave 18 — full local gate xanh bằng runtime dependency chuẩn — 21-09-2026, 08:06 +07

Đã hoàn tất `npm run test:all` trên đúng working tree bằng bundled workspace
runtime Python **3.12.14** với `pytest 8.4.2`, source-first `PYTHONPATH`, proxy
variables unset và không thay đổi policy production:

| Lane | Receipt | Cách đọc |
| --- | --- | --- |
| Electron/Desktop | `npm test`: **874 tests, 858 PASS, 16 SKIP, 0 FAIL**; source-root và repository-secret checks PASS | Node/source regression xanh; skip là ca Windows/runtime có điều kiện |
| Coding Tools MCP | **1.160 collected, 1.153 PASS, 7 SKIP, 0 FAIL** trong **159,98s** | Full MCP xanh trên interpreter có dev extra đúng chuẩn |
| Control Plane | **295/295 PASS** ở receipt lane riêng bằng Python 3.14.4 | Account/binding/task/node authority không regress |

Một số `ResourceWarning`/cleanup warning vẫn xuất hiện trong summary của MCP,
nhưng không có test failure. Failure dependency-only của Wave 17 đã được xử lý
bằng cách dùng đúng interpreter có `pytest`; không thêm `PYTHONPATH` hoặc nới
runtime policy để làm xanh giả.

### Ý nghĩa đối với sản phẩm

Wave 18 xác nhận source hiện tại có một regression gate cục bộ xanh cho contract:

```text
ChatGPT/OAuth account
  -> principal_id dùng chung
  -> client chọn binding_id
  -> task pin device/endpoint/workspace/generation
  -> Ubuntu auth/inventory/route/queue/receipt
  -> node đã bind thực thi file/process/Git/build/test/deploy local
```

Có thể tận dụng ngay các mảnh đã có: OAuth/account inventory và
`ControlPlaneStore`; enrollment/credential/rotation/heartbeat; SecretStore và
Recovery Host/IPC; standing file-read, approved-patch, document-write và
structured-exec bridges; journal/idempotency/writer lease/generation fence;
Coding Tools MCP; connected-agent/Supervisor; resource/package verifier và
`.coding-tools` evidence. Không xây lại credential theo máy, executor Ubuntu
thứ hai, cơ chế copy token/context hoặc vòng duyệt từng lệnh trong standing
local scope.

### Ranh giới bằng chứng vẫn giữ nguyên

Receipt này chỉ nâng mức thành **full source/local regression xanh**. Nó chưa
phải `PACKAGED_PROOF` hoặc `LIVE_ACCEPTED`: chưa có Windows exact
RunAsNode/Recovery/installer, DPAPI/ACL, reboot/reconnect/rotation crash, hai
ChatGPT client thật cùng `principal_id`, Git/build/test/deploy thật trên node
đúng, T01–T16, backup/restore, soak 24 giờ hay owner acceptance.

**Next action chính xác:** tạo Windows candidate từ cùng HEAD → chạy exact
packaged/installed smoke và credential/startup/reconnect gates → nghiệm thu hai
client chọn cùng `binding_id`/target fence → chạy parity read/write/exec/Git/
build/test/deploy → T01–T16, fault matrix, backup/restore, soak và owner
acceptance. Chưa commit, push, deploy, restart service, bật quyền live hoặc
gọi provider trả phí trong wave này.

## Checkpoint Wave 17 — full MCP source-first rerun và cô lập dependency gap — 21-09-2026

Đã chạy lại toàn bộ `resources/coding-tools-mcp/tests` với source repository
đứng trước runtime dependency tạm trong `PYTHONPATH`, bỏ toàn bộ proxy variables,
và `PYTHONWARNINGS=error::ResourceWarning`:

```text
1.160 collected: 1.152 passed, 1 failed, 7 skipped, 37 warnings
161.53s
```

Các kiểm chứng tách riêng sau full run:

- Official MCP SDK HTTP smoke + operator-report canonical timestamp:
  **19/19 PASS** khi source-first và proxy-free.
- Multi-workspace HTTP matrix + authorized workspace session: **2/2 PASS** khi
  child `python` là executable thật `/usr/bin/python3.14`.
- Continuous-check bookkeeping: bản test mặc định còn fail vì child system
  Python không có `pytest`; cùng logic chạy với `ShellEnvPolicy(inherit="all")`
  và dependency-aware `PYTHONPATH` đạt **passed, exit 0**, `current_command=null`
  và `command_finished`.

Failure duy nhất còn lại là:

```text
ToolModeTests.test_continuous_check_terminalizes_internal_command_bookkeeping
```

Nó gọi `python -m pytest --version`; runtime production cố ý chỉ truyền core
environment và không đưa `PYTHONPATH` vào child, trong khi host `/usr/bin/python3.14`
không cài pytest. Đây là **environment/dependency harness gap**, không phải lỗi
account, binding, local authority hay bookkeeping logic. Không nới policy
`PYTHONPATH` trong source để làm xanh giả; receipt full MCP vẫn là **chưa xanh**
cho tới khi test host/pipeline dùng interpreter có dev extra đúng chuẩn.

Wave 17 nâng bằng chứng local từ 8 failure xuống 1 dependency-only failure,
nhưng chưa nâng `PACKAGED_PROOF`/`LIVE_ACCEPTED`. Exact next action là chạy
`npm run test:all` trên host/pipeline có Python dev extra chuẩn (không runtime
tạm), sau đó chuyển candidate Windows vào P1–P6. Wave này không commit, push,
deploy, restart service, bật quyền live hoặc gọi provider trả phí.

## Checkpoint Wave 16 — cập nhật theo semantics account dùng chung và rà full MCP — 21-09-2026

### Contract sản phẩm phải giữ nguyên

Yêu cầu hiện hành là **một tài khoản ChatGPT/OAuth dùng chung cho nhiều máy
điều khiển**. Mỗi lần bind workspace vào một node tạo một `binding_id` opaque;
mọi client đăng nhập cùng account dùng cùng `principal_id`, đọc inventory và
chọn binding đó. Ví dụ: máy A bind `W1` thành `B1`; máy B/C chọn `B1` thì việc
chạy tại A/W1, không chạy tại B/C và không copy workspace.

```text
ChatGPT account/OAuth
    -> principal_id dùng chung trên mọi client
    -> client chọn binding_id (UI có thể tự chọn nếu chỉ có một binding usable)
    -> server vẫn nhận binding_id rõ ràng và task pin target bất biến
    -> Ubuntu auth/inventory/route/queue/receipt
    -> node đã bind giữ file/process/Git/build/test/deploy và quyền OS local
```

`binding_id` là selector, không phải token, context, credential, raw path hay
quyền Administrator. UI có thể ghi nhớ binding được chọn cho chat mới, nhưng
không tạo một `active_workspace` toàn tài khoản; task đã mở không retarget hoặc
failover khi client đổi lựa chọn, node đổi presence hay binding khác online.
Enrollment/credential sống lâu dài theo node; reboot/reconnect không cần chép
token/context và standing local scope không yêu cầu Ubuntu duyệt lại từng lệnh.

### Tình hình bằng chứng mới nhất

| Lane | Receipt mới nhất | Cách đọc |
| --- | --- | --- |
| Node/Electron | **874 tests: 858 PASS, 16 SKIP, 0 FAIL**; source-root và repository-secret checks PASS | Source/local regression xanh; skip là ca Windows/runtime có điều kiện |
| Ubuntu Control Plane | **295/295 PASS** bằng Python 3.14.4 | Account, binding, task, writer, recovery, credential và node lanes không regress |
| MCP full suite ở Wave 18 (hiện hành) | **1.160 collected: 1.153 PASS, 7 SKIP, 0 FAIL, 159,98s** | Chỉ còn resource/cleanup warnings; đây là source/local proof, chưa thay Windows package/live |
| Linux package/preflight | `dist:dir` PASS; **427 resources + 9 adapters**; packaged/installed helper focused PASS | Chỉ chứng minh resource/adapter và helper trên Linux, không thay Windows package/live |

Wave 17 với **1.152 PASS, 1 FAIL, 7 SKIP** là receipt lịch sử của dependency/
harness gap (child system Python thiếu `pytest`); Wave 18 đã chạy lại bằng
bundled Python **3.12.14** có `pytest 8.4.2` và đạt **0 FAIL**. Vì vậy không
được dùng số Wave 17 để mô tả current truth. Warning resource/cleanup còn lại
không làm test fail, nhưng cũng không nâng bằng chứng thành Windows
`PACKAGED_PROOF` hoặc `LIVE_ACCEPTED`.

### Phần đã tận dụng được, không xây lại

- **Account/binding:** `mcp_oauth.py`, `http_api.py`, `mcp_facade.py` và
  `ControlPlaneStore` đã có principal mapping, inventory nhiều binding,
  lifecycle state, task pin, writer lease và generation fence.
- **Enrollment/credential:** `node_agent.py`, enrollment API,
  `controlPlaneEnrollment.js`, SecretStore, heartbeat, rotation/revoke và
  workspace registry đã tạo sẵn đường duyệt một lần theo node.
- **Local execution:** các bridge file-read, approved-patch, document-write và
  structured-exec nối qua Recovery Host/IPC, RuntimeOrchestrator và Coding
  Tools MCP; structured `argv` là đường dùng cho Git/build/test/deploy.
- **Safety/continuity:** journal `prepared/completed/rejected/unknown`,
  idempotency, lost-ACK replay, `unknown/reconcile_required`, stop/observe/
  handoff và Supervisor standing-policy preflight đã có source/focused proof.
- **Evidence/package:** resource verifier, packaged/installed smoke và toàn bộ
  `.coding-tools/**` là bằng chứng phải giữ lại; không tạo executor Ubuntu,
  credential scheme, context-copy flow hoặc per-command approval mới.

### Exact next action sau Wave 16 (lịch sử; đã được supersede bởi Wave 18–20)

1. Tạo shim `python` tạm trỏ tới `/usr/bin/python3.14`, chạy lại đúng các test
   `python: not found`; unset proxy variables rồi chạy lại official SDK smoke.
2. Nếu operator-report vẫn tái hiện `24:00:00Z`, chạy focused test và sửa parser
   tối thiểu, sau đó chạy lại toàn bộ MCP suite để có receipt sạch.
3. Khi các local gates xanh, build **Windows exact candidate** và chạy P1
   enrollment/DPAPI/ACL/reboot/reconnect/rotation/revoke.
4. Dùng hai client ChatGPT thật cùng `principal_id`, chọn `B1`, kiểm observe/
   stop/handoff và target receipt; tiếp theo chạy read/write/Git/build/test/
   deploy thật, T01–T16, backup/restore và soak 24 giờ.
5. Chỉ sau owner acceptance và receipt Windows/live mới nâng nhãn hoặc xem xét
   release/deploy; model/provider gateway vẫn là gate tùy chọn riêng.

Wave 16 chỉ cập nhật kế hoạch và phân loại bằng chứng; không commit, push,
deploy, restart service, bật quyền live hay gọi provider trả phí.

Các tiêu đề “mới nhất” ở các checkpoint phía dưới là lịch sử tại thời điểm
chúng được ghi. Khi đối chiếu hiện trạng, luôn ưu tiên Wave 19 và các snapshot
đầu tài liệu; Wave 18 giữ receipt **MCP 1.153 PASS / 7 SKIP / 0 FAIL** làm
full-suite source/local baseline trên runtime dependency chuẩn. Các số liệu cũ hơn chỉ
là chronology, không thay thế receipt này.

## Checkpoint Wave 15 — full regression gate trên source hiện tại — 21-09-2026

Full regression sau các chỉnh sửa Wave 14 đạt:

| Nhóm | Receipt | Phân loại |
| --- | --- | --- |
| Node/Electron `npm test` + source-root + repository-secret | **874 tests: 858 PASS, 16 SKIP, 0 FAIL, 43,45s** | Source/local regression xanh; 16 skip là ca Windows/runtime có điều kiện |
| Toàn bộ `control-plane/tests` | **295/295 PASS, 96,37s** | Account, binding, task, writer, recovery, credential và node lanes không regress |

Wave 15 chỉ cung cấp source/focused/integrated local proof. Không nâng nhãn
`PACKAGED_PROOF`/`LIVE_ACCEPTED`; Windows exact package/live, DPAPI/ACL,
reboot/reconnect, two-client ChatGPT thật, toolchain thật, T01–T16 và soak 24h
vẫn mở.

**Exact next action:** giữ source này làm candidate, build trên Windows, chạy
P1 enrollment/reconnect → P2 shared-account two-client → P3 read/write/exec
toolchain → P4 fault matrix → P5 backup/restore/soak/owner acceptance.

## Checkpoint Wave 14 — focused validation mới nhất — 21-09-2026

Đã re-run các nhóm test sát mục tiêu account dùng chung và node-local authority
trên worktree hiện tại. Lần gọi Python đầu thiếu `control-plane` trong
`PYTHONPATH`; sau khi sửa invocation, kết quả là:

| Nhóm | Receipt | Ý nghĩa |
| --- | --- | --- |
| OAuth/account, task session, writer/exec, HTTP → node document/exec/patch | **71/71 PASS, 58,32s** | Cùng `principal_id` chọn `binding_id`, task pin và relay local không retarget |
| Store/node file-read, patch, document, exec, credential, secret, workspace replacement | **146/146 PASS, 9,53s** | Lifecycle, generation fence, standing local lanes và fail-closed path |
| Node/Electron bridge, enrollment, SecretStore, packaged smoke, Supervisor helper | **34 PASS, 1 SKIP, 0 FAIL, 3,75s** | Adapter/resource/recovery wiring; skip là runtime Supervisor thật ngoài Windows |
| UI boundary/docstring alignment | **py_compile PASS; Control Center 14/14 PASS** | Loại bỏ mô tả M2 stale; panel vẫn local-only, shared binding đi qua Control Plane |

Các receipt này là **source/focused/integrated local proof**. Không nâng thành
`PACKAGED_PROOF`/`LIVE_ACCEPTED`, vì host hiện tại không thể chứng minh Windows
RunAsNode/Recovery Host/DPAPI/ACL, reboot/logon/reconnect, hai ChatGPT client
thật, Git/build/test/deploy thật hoặc soak 24 giờ.

**Next action:** dùng đúng source này để build candidate Windows, sau đó chạy
P1 → P2 → P3 → P4/P5 theo Wave 13; không dùng Linux test để thay thế gate
Windows/live và không bật provider/model gateway khi chưa có yêu cầu riêng.

## Checkpoint Wave 13 — xác nhận semantics account chung và thứ tự hoàn thiện — 21-09-2026

Đây là checkpoint contract nền để triển khai theo yêu cầu “tất cả máy dùng cùng một
tài khoản ChatGPT nhưng lệnh chạy tại workspace đã bind”. Mô hình chuẩn là:

```text
Một ChatGPT/OAuth account
    -> một principal_id dùng chung trên mọi client của account
    -> client chọn binding_id của workspace cần làm việc
    -> task pin {device_id, endpoint_id, workspace_id, workspace_generation}
    -> Ubuntu xác thực, resolve target, queue/dispatch và trả receipt
    -> node đã bind thực thi local bằng quyền OS/policy của chính node
```

### Quy tắc không được lệch

- Máy A bind `W1` thành `B1`; máy B/C cùng account chỉ cần chọn `B1` thì lệnh
  chạy tại A/W1. Không chạy tại máy gửi lệnh và không copy workspace.
- `binding_id` là selector opaque. Nó không chứa path, token, context, secret và
  không tự cấp quyền Administrator.
- Task pin target lúc mở. Đổi binding mặc định, node online/offline hoặc client
  khác không được retarget/failover task đang chạy.
- Cùng `principal_id` chỉ chia sẻ danh tính account và quyền quan sát/điều khiển
  theo scope; vẫn giữ idempotency, writer lease, generation fence, local policy
  và terminal receipt.
- Enrollment/credential sống lâu dài theo node. Reboot/reconnect không cần chép
  token/context và Ubuntu không xin duyệt lại từng lệnh trong standing local
  scope.
- Ubuntu làm auth/inventory/routing/queue/receipt; node giữ file, process, Git,
  build/test/deploy và quyền OS local. MCP/Tunnel chỉ relay tool, không mặc định
  là API suy luận model.

### Những gì đã tận dụng và không xây lại

| Nhu cầu | Thành phần tái sử dụng | Vai trò trong kế hoạch |
| --- | --- | --- |
| Account và target inventory | `mcp_oauth.py`, `http_api.py`, `mcp_facade.py`, `store.py` | Ánh xạ account vào `principal_id`, trả nhiều `binding_id` opaque và giữ lifecycle state |
| Enrollment lâu dài | `node_agent.py`, `controlPlaneEnrollment.js`, heartbeat, rotation/revoke | Duyệt một lần, credential riêng theo node, tự reconnect và fail-closed khi stale/revoked |
| Secret/lifecycle | `secretStore.js`, `runtimeOrchestrator.js`, `recoveryHost.js`, `recoveryIpc.js` | Bảo vệ credential, journal/reconcile và giao tiếp với runtime local |
| Task/authority | `ControlPlaneStore` | Pin target, idempotency, writer lease, generation fence, queue và receipt |
| Local capabilities | file-read, approved-patch, document-write, structured-exec bridges | Dùng chung đường node-local cho read/write/exec; OS/ACL của node quyết định quyền |
| Tool/runtime | Recovery Host, connected-agent/Supervisor, Coding Tools MCP | Giữ process lifecycle, output/stop/reconcile và structured `argv` cho Git/build/test/deploy |
| Evidence/package | resource verifier, packaged/installed smoke, `.coding-tools/**` | Kiểm byte/resource và bảo toàn ledger/receipt; không dùng fixture để tuyên bố live |

Không tạo credential scheme thứ hai, executor Ubuntu thứ hai, cơ chế chép
context/token giữa client hoặc per-command approval mới. Model/provider gateway
chỉ là gate P6 nếu sản phẩm thật sự yêu cầu Ubuntu chủ động gửi request suy luận;
MCP relay hiện tại không tự đáp ứng vai trò đó.

### Trạng thái và thứ tự gate tại thời điểm này

- **Đã chứng minh ở source/focused/integrated local:** account → binding → task
  pin; enrollment/rotation/revoke source path; standing read/write/document/
  structured exec; writer/recovery/receipt; Linux resource/package preflight.
- **Chưa được tuyên bố:** Windows exact package/fuse/Recovery Host, DPAPI/
  `safeStorage`/ACL thật, reboot/startup/reconnect live, hai ChatGPT client thật,
  Git/build/test/deploy trên workspace bound, T01–T16, backup/restore, soak 24 giờ
  và owner acceptance.
- **Mức proof hợp lệ:** Wave 18 hiện đã có full source/local regression xanh;
  vẫn chưa phải `PACKAGED_PROOF` hay `LIVE_ACCEPTED`. Chỉ sau khi chạy đúng
  Windows candidate và có owner acceptance mới nâng hai nhãn đó.

### Exact next action

1. Build Windows candidate từ HEAD hiện tại; chạy RunAsNode fuse, Recovery Host,
   installed smoke và verifier byte/resource.
2. Trên candidate, enrollment → approve → bind `W1/B1`; kiểm DPAPI/ACL,
   reboot/logon, reconnect, rotation/revoke và workspace replacement.
3. Dùng hai client cùng `principal_id`: inventory, chọn `B1`, mở task,
   observe/stop/handoff; xác nhận task không retarget và receipt gắn đúng node.
4. Chạy read/write/document và structured `argv` cho Git/build/test/deploy thật;
   kiểm quyền OS, deny path, output/stop và `unknown/reconcile_required`.
5. Chạy T01–T16, fault matrix, backup/restore và soak tối thiểu 24 giờ; sau đó
   owner review/acceptance.

Wave 13 chỉ sửa tài liệu điều hành; không bật Ubuntu live, không đổi quyền
Windows, không commit/push/deploy/restart service và không gọi model/provider trả
phí.

## Checkpoint điều hành trước Wave 16 — kế hoạch chốt theo account dùng chung — 21-09-2026

Phần này là bản tóm tắt điều hành phải được dùng làm chuẩn khi triển khai tiếp.
Các checkpoint phía dưới giữ nguyên để bảo toàn lịch sử và bằng chứng theo thời
điểm; nếu một checkpoint cũ nói “chưa có” nhưng phần này nói “đã có source/test”,
thì hiểu là phần cũ đã được **superseded**, không phải đã được nghiệm thu live.

### Snapshot repository và bằng chứng — 21-09-2026

- Repository đang ở branch `codex/control-plane-quarantine`, HEAD
  `502ffb8cf8b541ee74af30194aff2dce08c3b649`; worktree dirty có chủ ý vì các
  wave source/test/docs/evidence hiện hành. Không reset, clean hoặc ghi đè phần
  việc đang có.
- Đã có source và local proof cho account inventory, binding/task pin,
  enrollment/credential, read/write/structured-exec, Recovery và receipt. Các
  binding bị revoke hoặc generation bị retire vẫn hiện trong inventory với
  blocker, nhưng admission vẫn fail-closed.
- Regression hiện hành: Control Plane **295/295 PASS**; MCP **1.160 collected,
  1.153 PASS, 7 SKIP, 0 FAIL**; Node/Electron **858 PASS, 16 SKIP, 0 FAIL /
  874**; Linux package preflight **427 resources + 9 adapters** và helper /
  release focused **5/5 PASS**.
- Wave 18 đã chạy `npm run test:all` bằng bundled Python 3.12.14/pytest 8.4.2;
  dependency-only failure của Wave 17 không còn. Receipt này vẫn là source/local
  proof, chưa phải Windows package/live.
- Chưa commit, push, deploy, restart service hoặc gọi provider trả phí trong
  lượt này. Chưa có Windows exact artifact/live receipt, nên mức công bố vẫn
  là **full source/local regression xanh** ở Wave 18, nhưng chưa phải
  `PACKAGED_PROOF`/`LIVE_ACCEPTED`.

Snapshot này là điểm xuất phát cho gate Windows tiếp theo; các con số cũ hơn ở
phía dưới chỉ là lịch sử và không được dùng để hạ hoặc nâng mức bằng chứng hiện
thời.

## Checkpoint Wave 10 — refresh Linux packaged candidate — 21-09-2026

Đã tạo lại `dist/linux-unpacked` bằng `npm run dist:dir` (**PASS**). Packaged /
installed recovery smoke đạt **3/3 PASS**; `packaged-recovery-smoke.js` trả
`windows_only` đúng contract khi chạy ngoài Windows. Verifier trực tiếp trên
candidate đạt **427 resource files exact-source**, **9 control-plane adapters**
và **463 entries sanitized**.
HTTP boundary recheck cho hai client cùng `principal_id` chọn nhiều binding và
handoff writer lease đạt **2/2 PASS trong 3.053s**.
HTTP → node → Recovery cho document-write và structured exec đạt **23/23 PASS
trong 29.601s** với `PYTHONWARNINGS=error::ResourceWarning`.
Standing-profile configuration, shared-task observation và cross-client
writer/exec guard đạt **3/3 PASS trong 3.046s**.
Standing patch không cần per-patch approval và document-create không đưa
content vào action payload đạt **2/2 PASS trong 0.083s**.

Đây chỉ là Linux resource/package preflight, không phải Windows RunAsNode fuse,
Recovery Host, DPAPI/ACL, reboot/reconnect hay live acceptance. Mức công bố vẫn
là `SOURCE_PRESENT + FOCUSED_TEST_PROOF` + integrated local test proof.

## Checkpoint Wave 11 — documentation contract alignment — 21-09-2026

`control-plane/README.md` đã được đồng bộ: `install-read-only-policy-*` là
legacy compatibility-only; trusted flow dùng OAuth account, opaque
`binding_id`, standing node-local read/write/structured exec, task pin và
reconnect. Không thay đổi live service, credential hoặc quyền Windows trong
wave này.

## Checkpoint Wave 12 — T01–T16 source/live matrix — 21-09-2026

Bản điều hành [SHARED_ACCOUNT_WORKSPACE_STATUS.md](SHARED_ACCOUNT_WORKSPACE_STATUS.md)
đã có bảng T01–T16 tách proof focused khỏi Windows/live acceptance. Không dùng
fixture để nâng nhãn; T13/T15 và các gate package/two-client/soak vẫn mở.

## Checkpoint Wave 9 — sửa preflight Supervisor cho standing authority — 21-09-2026

Audit sau Wave 8 phát hiện một lệch quan trọng giữa source và thiết kế đã chốt:
`run-connected-agent` đã heartbeat độc lập với pilot read-only, nhưng
Recovery Supervisor vẫn bắt buộc `control-plane-read-only-policy.json` còn hạn.
Sau khi policy pilot hết hạn, hoặc sau khi credential đã được chuyển sang
DPAPI, node standing write/exec có thể bị Supervisor không khởi động lại dù
workspace và credential vẫn hợp lệ.

Đã sửa `resources/recovery-supervisor/recovery-supervisor.ps1` để:

- preflight các policy standing v2 thực tế: file-read, approved-patch và exec;
- không dùng `expires_at_ms` của read-only pilot làm điều kiện sống còn;
- chấp nhận cấu hình credential plaintext legacy hoặc marker DPAPI
  `node_secret_dpapi` mà không giải mã/in secret trong Supervisor;
- chỉ cho connected agent chạy khi có ít nhất một standing lane enabled, đúng
  server/device/endpoint và workspace generation còn đăng ký hiện hành;
- trả trạng thái fail-closed riêng khi standing policy thiếu/sai, workspace
  registry thiếu/cũ hoặc identity không khớp. Mỗi lane vẫn bị node agent kiểm tra
  lại ngay trước dequeue/effect.

Focused proof sau sửa:

- PowerShell helper của Supervisor bao phủ lane file-read, approved-patch,
  exec-only, read-only policy hết hạn/disabled, standing policy hết hạn, DPAPI
  marker và workspace registry: **1/1 test class PASS** trên host có PowerShell;
- `node --test tests/recovery-supervisor.test.js`: **1 PASS, 1 SKIP** (nhóm
  runtime thật được skip có chủ đích ngoài Windows);
- connected-agent/heartbeat và toàn bộ `test_store`: **83/83 PASS**;
- `git diff --check`: PASS.

Đây là source/focused proof, chưa phải Windows exact packaged startup, reboot,
DPAPI/ACL, live reconnect hay two-client acceptance. Không commit, push,
deploy, restart service hoặc gọi provider trả phí trong wave này.

### Trạng thái và phần tận dụng sau Wave 9

| Phần | Đang tận dụng | Không được hiểu nhầm là đã xong |
| --- | --- | --- |
| Account/workspace | `principal_id` dùng chung; `binding_id` chọn target; task pin device/endpoint/workspace/generation | Hai ChatGPT client thật cùng account trên Windows exact artifact |
| Enrollment | Device identity, credential generation, reconnect/heartbeat, rotation/revoke và DPAPI source path | DPAPI/ACL, reboot/logon và rotation receipt trên package Windows thật |
| Local execution | Standing file-read, approved-patch, document-write và structured exec qua node → Recovery → Coding Tools MCP | Git/build/test/deploy thật và policy/child-process fault trên package |
| Recovery | Journal, idempotency, writer lease, unknown/reconcile, connected-agent lock và Supervisor preflight mới | Crash/lost-ACK/restart/failover live trên Windows |
| Ubuntu | Auth, inventory, routing, queue và receipt; không giữ file và không cấp quyền từng lệnh | Ubuntu live activation/model gateway; gateway chỉ mở nếu có yêu cầu server-side inference |

**Next action chính xác:** đóng gói Windows candidate chứa Supervisor/node-agent
mới → chạy fuse/Recovery smoke → bind một workspace W1 thành B1 và approve
credential → reboot/reconnect → kiểm tra hai client cùng `principal_id` chọn
B1 → chạy read/write/Git/build/test/deploy và T01–T16 → soak 24 giờ → owner
acceptance. Chỉ sau receipt live và owner sign-off mới nâng mức bằng chứng.

## Checkpoint Wave 7 — shared-account HTTP→node capability recheck — 21-09-2026

Đã chạy lại trực tiếp trên đúng worktree hiện tại, không dùng receipt lịch sử:

- Nhóm OAuth/account, task pin và writer handoff, exec qua Recovery, document
  write qua Recovery: **57/57 PASS trong 45.280s**.
- Toàn bộ Control Plane unittest: **294/294 PASS trong 94.877s** bằng Python
  **3.14.4** với `PYTHONWARNINGS=error::ResourceWarning`; không còn
  `ResourceWarning` SQLite.

Wave này chứng minh ở mức source/focused rằng cùng một `principal_id` có thể
chọn nhiều `binding_id` mà không retarget task đang mở; standing patch,
document create/convert và structured exec đi qua HTTP → node journal →
Recovery/local runtime; crash, lost ACK và terminal receipt được replay hoặc
chuyển `unknown/reconcile_required` mà không redeliver effect. Đây chưa phải
Windows packaged/live proof và không chứng minh hai ChatGPT client thật.

Mức công bố vẫn là **`SOURCE_PRESENT + FOCUSED_TEST_PROOF` + integrated local
test proof**. Bước kế tiếp là chạy exact Windows package/Recovery/DPAPI/ACL,
reboot/reconnect/rotation, rồi nghiệm thu hai client cùng account và T01–T16.

## Checkpoint Wave 8 — standing local authority configuration proof — 21-09-2026

Đã bổ sung test cấu hình OAuth cho đúng profile sản phẩm không duyệt từng lệnh:
`CONTROL_PLANE_MCP_OAUTH_STANDING_WRITE_ENABLED=true` và
`CONTROL_PLANE_MCP_OAUTH_EXEC_ENABLED=true` chỉ hợp lệ khi có file-read, một
write scope riêng và OAuth introspection đầy đủ. Bật exec đơn độc, thiếu write
scope, dùng scope trùng hoặc dùng giá trị không chuẩn đều bị fail-closed.

Focused configuration class: **6/6 PASS**. Full Control Plane sau thay đổi:
**295/295 PASS trong 95.319s** bằng Python 3.14.4 với
`PYTHONWARNINGS=error::ResourceWarning`.

Mẫu rollout đã đồng bộ trong `deploy/control-plane.env.example` và
`control-plane/README.md`: các biến standing write/exec chỉ xuất hiện dạng
comment/sample, không làm thay đổi Ubuntu live mặc định.

Đây chỉ là source/focused configuration proof; không tự bật flag trên Ubuntu
live, không thay đổi quyền Windows và không thay thế DPAPI/ACL, packaged/live
reconnect hoặc two-client acceptance. Chỉ sau khi owner cấu hình scope và local
policy trên exact artifact mới chạy gate Windows/P1–P6.

## Checkpoint Wave 4 — node lifecycle inventory và public task admission — 21-09-2026

Đã bổ sung proof HTTP cho đúng trường hợp account dùng chung nhìn thấy một node
đã bị revoke mà không được phép mở task mới trên target đó. Inventory vẫn giữ
`binding_id` opaque để client biết target tồn tại, nhưng trả:
`binding_state=active`, `node_state=revoked`, `workspace_state=active`,
`dispatch_state=node_revoked` và `dispatch_blockers=["node_revoked"]`.

`workspace_context(operation=task_open)` qua OAuth ingress trên cùng binding bị
từ chối với lỗi `CONFLICT` (không tạo task và không failover sang máy khác).
Projection không chứa `canonical_path` hoặc `node_secret`.

Validation:

- OAuth HTTP focused: **28/28 PASS trong 14.266s**;
- toàn bộ Control Plane unittest bằng Python 3.14.4: **292/292 PASS trong
  92.197s**;
- test harness đã đóng rõ các SQLite connection; full run với
  `PYTHONWARNINGS=error::ResourceWarning` vẫn **292/292 PASS**, không còn
  warning rò rỉ tài nguyên.

Đây vẫn là source/focused proof. Bước tiếp theo không đổi: exact Windows
package/Recovery/DPAPI gate, rồi two-client live acceptance. Các checkpoint cũ
ghi 291/291 là receipt trước khi thêm ca này.

## Checkpoint Wave 5 — principal revoke và retired generation qua OAuth HTTP — 21-09-2026

Đã bổ sung hai boundary proof cho account dùng chung:

- Sau khi revoke `principal_id`, OAuth ingress trả **403 `FORBIDDEN`**, không
  tạo link pending mới và không làm lộ `binding_id`, path hoặc node secret.
- Sau khi retire workspace generation, inventory vẫn giữ binding lịch sử với
  `binding_state=revoked`, `workspace_state=retired` và blocker
  `["binding_revoked", "workspace_retired"]`; `task_open` trả **`CONFLICT`**,
  không retarget sang generation thay thế và không failover.

Validation sau wave:

- OAuth HTTP focused: **30/30 PASS trong 15.812s**;
- toàn bộ Control Plane unittest: **294/294 PASS trong 96.371s** bằng Python
  3.14.4 với `PYTHONWARNINGS=error::ResourceWarning`;
- `py_compile` và `git diff --check`: PASS.

Đây vẫn là source/focused proof. Windows exact package, hai ChatGPT client
thật và owner acceptance chưa được chứng minh.

## Checkpoint Wave 6 — Node/Electron regression recheck — 21-09-2026

`npm test` đã chạy trên đúng worktree hiện tại và đạt **858 PASS, 16 SKIP,
0 FAIL / 874** trong **43.317s**. Hai hậu kiểm đi kèm cũng PASS:
`check-source-root-clean` và `check-sensitive-tracked`.

Đây là source/local regression receipt; các test Windows được skip có chủ đích
vẫn không chứng minh fuse, Recovery Host, DPAPI/ACL hoặc installed package.
MCP Python integrated vẫn là receipt product runtime trước đó vì host hiện tại
chưa có `pytest`.

### 1. Contract sản phẩm không được làm lệch

```text
Một tài khoản ChatGPT/OAuth
  -> một verified principal_id dùng chung cho mọi client
  -> client chọn binding_id của workspace cần làm việc
  -> Ubuntu xác thực, resolve target, queue/dispatch và trả receipt
  -> node đã bind thực thi trên workspace local bằng quyền OS/policy của node
```

Diễn giải đúng theo yêu cầu mới: máy A bind workspace `W1` và nhận `B1`; mọi
máy/client đang đăng nhập **cùng account ChatGPT/OAuth** có thể chọn `B1`, nên
lệnh từ máy B/C vẫn chạy tại A/W1. Nếu account có thêm `B2`, `B3`, client chọn
ID tương ứng cho từng task. ChatGPT client là controller; binding mới là target
thực thi. Không tạo một `active_workspace` chung để tự đổi đích cho tất cả task.

- Một lần bind workspace vào máy tạo `binding_id` opaque. ID này là selector,
  không phải bearer token, context, cookie hay quyền Administrator.
- Máy A bind `W1` thành `B1`; ChatGPT client B/C dùng cùng `principal_id` có thể
  chọn `B1` để lệnh chạy tại A/W1. Client đang mở chat chỉ là controller, không
  trở thành execution host và không nhận bản sao workspace.
- Mỗi task đóng băng target ngay khi mở:
  `{binding_id, device_id, endpoint_id, workspace_id, workspace_generation}`.
  Session/client đổi lựa chọn mặc định không được retarget task đang chạy.
- Cùng account không bỏ qua `idempotency`, writer lease, generation fence,
  local policy hoặc terminal receipt. Client khác có thể observe/stop/handoff
  theo scope đã cấp nhưng không được ghi đè mù.
- Enrollment và credential thuộc về node; sau khi được duyệt, node reconnect
  sau reboot mà không phải chép token/context hay xin duyệt từng lệnh trong
  standing local scope. Ubuntu không tự nâng quyền OS của node.
- Ubuntu không giữ file/workspace thay node và không biến MCP/Tunnel thành API
  suy luận. Chỉ mở provider/model gateway nếu có yêu cầu rõ ràng rằng Ubuntu
  phải chủ động gọi model; khi đó gateway là một project/gate riêng.

### 2. Hiện trạng đã được chứng minh và giới hạn công bố

| Boundary | Đã có và tận dụng được | Bằng chứng gần nhất | Còn thiếu để nâng mức |
| --- | --- | --- | --- |
| Account → `principal_id` → nhiều `binding_id` | OAuth account inventory, lifecycle state, opaque binding, task pin, writer/generation fence | HTTP same-account **3/3 PASS**; Windows two-client exec **1/1 PASS**; Control Plane **295/295 PASS** | Hai ChatGPT client thật qua UI cùng principal trên target owner |
| Enrollment/credential lâu dài | Device identity, enrollment request/approval, credential generation, heartbeat, reconnect, revoke/rotation source path | Windows secret/rotation/workspace **18/18 PASS**; DPAPI/ACL probe pass; source lifecycle suites xanh | Reboot/startup/reconnect và rotation/revoke trên installed artifact |
| Local read/write | Standing file-read, approved-patch và document create/convert qua node → Recovery → RuntimeOrchestrator → Coding Tools MCP | HTTP→node **22/22 PASS**; document-write/patch focused pass | File-effect trên workspace thật, quyền OS thật và fault proof live |
| Local exec parity | Structured `argv` lane dùng chung cho Git/build/test/deploy; poll, stop, output cursor, terminal receipt | HTTP → node → Recovery exec **12/12 PASS**; two-client route **1/1 PASS** | Toolchain Windows thật, deploy thật, policy deny/child-process proof trên package |
| Continuity/recovery | Journal `prepared/completed/rejected/unknown`, lost-ACK replay, stop/reconcile, connected-agent | Recovery process **3/3 PASS**; packaged/installed smoke pass | Reboot/crash/lost-ACK trên installed Windows và hai-client handoff live |
| Package/resource | Windows `dist:dir`, resource verifier, packaged/installed helper smoke; PE resource inspection | Candidate `PACKAGED_PROOF`; installer `1.0.7`, install/uninstall và ACL/DPAPI pass | Exact Git byte lineage, startup/reconnect live và owner acceptance |
| Regression | Node/Electron, Control Plane Python và MCP integrated/candidate | Candidate Node/Electron **922/922 PASS**, MCP **1.160/1.160 PASS**; Control Plane **295/295 PASS** | Candidate không có `.git`; bốn OAuth NTFS/POSIX fixture assertion, T01–T16, soak |
| Model boundary | Ubuntu auth/router/queue/receipt và MCP tool relay | Source contract + focused tests | Provider gateway chỉ khi sản phẩm yêu cầu server-side inference |

Mức công bố chính xác hiện tại là **`SOURCE_PRESENT + FOCUSED_TEST_PROOF` +
Windows candidate `PACKAGED_PROOF`**. Chưa được ghi `LIVE_ACCEPTED`. Không dùng
Linux preflight, fixture deterministic hoặc receipt lịch sử để thay cho
installed reboot/reconnect, hai client UI thật, toolchain, T01–T16, restore,
soak và owner acceptance.

### 3. Những gì phải tận dụng, không xây lại

| Mục tiêu | Thành phần hiện có | Cách ghép vào contract mới |
| --- | --- | --- |
| OAuth/account và inventory | `control-plane/control_plane/mcp_oauth.py`, `http_api.py`, `mcp_facade.py`, `store.py` | Giữ một `principal_id` cho các client cùng account; inventory trả từng binding; không tạo `active_workspace` toàn account |
| Bind/enrollment lâu dài | `node_agent.py`, enrollment API, device identity, heartbeat/presence, rotation và `electron/services/controlPlaneEnrollment.js` | Duyệt một lần; credential nằm ở node; reconnect độc lập context/pilot TTL |
| Secret và lifecycle node | `electron/services/secretStore.js`, `runtimeOrchestrator.js`, `recoveryHost.js`, `recoveryIpc.js` | Bảo vệ secret bằng owner/OS store; central route chỉ là evidence kết nối, không phải action grant |
| Target/task/ownership | `ControlPlaneStore` task sessions, idempotency, writer lease, generation fence, queue/receipt | Mọi action nhận binding rồi pin target; client khác chỉ observe/điều khiển theo scope |
| Local capability | `node_agent.py`, `electron/services/controlPlaneFileReadBridge.js`, `controlPlaneApprovedPatchBridge.js`, `controlPlaneDocumentWriteBridge.js`, `controlPlaneExecBridge.js` | Một local lane cho read/write/exec; local policy và OS là nguồn quyết định quyền |
| Recovery/effect safety | Journal, `RecoveryIpcServer`, Recovery Host, `RuntimeOrchestrator`, `run-connected-agent` | Không redeliver sau lost ACK; trạng thái `unknown/reconcile_required` là thật, không đoán từ PID |
| MCP/tool execution | `resources/coding-tools-mcp/coding_tools_mcp/{tool_schema.py,exec_tools.py,landlock_exec.py}` | Structured argv/process lifecycle; MCP chỉ thực thi tool trên node, không thay model/provider |
| Package/evidence | `scripts/verify-packaged-resources.js`, `scripts/packaged-recovery-smoke.js`, `scripts/installed-recovery-smoke.js`, `.coding-tools/**` | Dùng verifier/smoke/ledger để chứng minh đúng bytes; giữ mọi evidence theo retention invariant |

Không cần dựng lại credential theo máy, queue/task ledger, executor Ubuntu thứ
hai, cơ chế chép context/token, hay per-command approval ở Ubuntu trong standing
local scope. Không chuyển quyền điều hành local lên server để “đơn giản hóa”.

### 4. Kế hoạch hoàn thiện chi tiết theo gate

| Gate | Việc phải làm | Điều kiện đạt / receipt bắt buộc |
| --- | --- | --- |
| **P0 — contract/candidate freeze** | Chốt fixture `B1/B2`, exact Windows artifact, startup scope và policy `{read,write,exec}`; khóa schema/contract hash; rà các checkpoint superseded | Inventory/task/receipt cùng giữ target bất biến; không lộ secret/path/context; candidate có revision và byte manifest |
| **P1 — identity/enrollment** | Trên Windows exact candidate: bind một lần, approve, lưu credential, reboot/reconnect; test revoke, retire, replacement và staged rotation/mất ACK | DPAPI/`safeStorage` + ACL pass; node tự reconnect; revoked/retired/offline/unknown phân biệt; không cần chép token/context |
| **P2 — account/task routing** | Hai client thật cùng OAuth account: inventory thấy các binding; mở task ở `B1`/`B2`; client B observe/claim/release theo scope | Task trả đúng `{device, endpoint, workspace, generation}`; không retarget task đã mở; writer lease/generation conflict bị chặn rõ |
| **P3 — local capability parity** | Trên cùng node chạy read/write/document/exec; kiểm Git, build, test, deploy, output cursor, stop child tree và policy deny | File effect/receipt nằm ở node; Ubuntu chỉ queue/dispatch/status; mỗi action có terminal receipt hoặc `unknown/reconcile_required` |
| **P4 — fault and handoff** | Crash trước/sau effect, lost ACK, Recovery restart, node reconnect, Ubuntu restart; chạy observe/stop/handoff giữa client A/B | Không duplicate effect, không spawn lại mù, không kill PID không chứng minh owner, không đổi target task đang chạy |
| **P5 — package/operations** | Build PE/installer trên Windows; fuse/RunAsNode, Recovery Host, startup sau logon (và ghi rõ pre-login nếu chưa hỗ trợ), ACL, backup/restore | Exact packaged smoke và installed smoke pass; bytes/resource/epoch/revision/identity khớp; rollback có đường kiểm chứng |
| **P6 — acceptance/soak** | Chạy T01–T16, fault matrix cuối, owner acceptance, soak ≥24 giờ; cập nhật `.coding-tools` evidence và delivery snapshot | Chỉ khi owner ký và receipt live khớp mới nâng `PACKAGED_PROOF` → `LIVE_ACCEPTED`; sau đó mới cân nhắc deploy |
| **P7 — optional model gateway** | Chỉ nếu yêu cầu Ubuntu chủ động suy luận: thêm provider auth/budget/timeout/receipt và test tool-call/model boundary | Gateway là gate riêng; không làm thay đổi local authority, binding/task fence hay biến MCP thành model API |

### 5. Trình tự thực hiện ngay sau tài liệu này

1. Trên Windows host/pipeline có toolchain thật, build candidate exact và chạy
   fuse/Recovery/package smoke; lưu revision, artifact hash và resource receipt.
2. Trên đúng artifact đó chạy DPAPI/`safeStorage`, ACL, reboot/startup,
   reconnect, revoke/retire, rotation và workspace replacement.
3. Dùng hai ChatGPT client thật cùng `principal_id`: inventory, chọn `B1/B2`,
   mở task, observe/stop/handoff; lưu target/lease/receipt đã redacted.
4. Chạy Git/build/test/deploy thật cùng structured argv, sau đó T01–T16,
   backup/restore và soak 24 giờ.
5. Owner review evidence, ghi acceptance hoặc blocker; chỉ sau acceptance mới
   thực hiện release/deploy theo target được chỉ định.

Trong Wave 8 đã thêm đúng một test cấu hình OAuth và cập nhật tài liệu; không
bật flag live, commit, push, deploy, restart service, thay đổi quyền live hoặc
gọi provider trả phí.

## Checkpoint Wave 3 — inventory giữ trạng thái revoke/retire, 21-09-2026

Đã đóng một khoảng trống trong contract account dùng chung: trước đây
`list_account_targets()` chỉ trả binding có node/workspace generation hiện tại,
nên một client không thể phân biệt “đã revoke”, “generation đã retire” và “chưa
từng thấy registration”. Store nay dùng inventory credential-free với `LEFT JOIN`
để giữ lại binding lịch sử của đúng owner/account nhưng không làm chúng
dispatchable.

Mỗi target trả thêm các trường trạng thái không chứa path/secret:

- `binding_state`: `active` hoặc `revoked`;
- `node_state`: `active` hoặc `revoked`;
- `workspace_state`: `active`, `retired` hoặc `missing`;
- `dispatch_state`: `dispatchable` hoặc blocker chính;
- `dispatch_blockers`: toàn bộ blocker (`binding_revoked`, `node_revoked`,
  `workspace_retired`, `workspace_missing` nếu có);
- timestamp revoke/registration/retire tương ứng.

`task_open`, action admission và generation fence vẫn yêu cầu binding/node/
workspace hiện tại; thay đổi này chỉ làm trạng thái hiển thị đúng và ngăn
client tự suy diễn failover. Không có absolute path, node secret, OAuth subject
hay context trong projection.

Focused validation sau thay đổi:

- `control-plane/tests/test_mcp_oauth.py`: **27/27 PASS**;
- `control-plane/tests/test_store.py`: **83/83 PASS**;
- OAuth/task focused group (`test_mcp_oauth.py` + `test_mcp_task_sessions.py`):
  **39/39 PASS trong 13.03s**;
- toàn bộ Control Plane unittest: **291/291 PASS trong 90.154s**;
- ca mới chứng minh retired generation trả `workspace_retired` và binding bị
  revoke trả `binding_revoked`, nhưng cả hai vẫn hiện rõ trong inventory;
- các ca account khác owner vẫn không nhìn thấy target/path của owner khác.

Package preflight sau cùng source wave cũng đạt trên Linux:

- `npm run dist:dir`: PASS;
- verifier exact source/package: **427 resource files + 9 control-plane adapter
  files**;
- packaged/installed recovery and release focused tests: **5/5 PASS**.

Đây chưa phải Windows package proof: môi trường hiện tại là Ubuntu, không có
Windows Electron/PE fuse execution, Recovery Host thật, DPAPI/ACL hoặc reboot.

Mức bằng chứng vẫn là **`SOURCE_PRESENT + FOCUSED_TEST_PROOF`**; chưa nâng
Windows/package/live. Bước tiếp theo: dùng đúng field trạng thái này trong
two-client acceptance, rồi chạy exact Windows package/reconnect/revoke và
workspace replacement. Lượt này không commit, push, deploy, restart service hay
gọi provider trả phí.

## Checkpoint Wave 2 — integrated source gate xanh — 21-09-2026

Đã hoàn thiện và xác minh bốn blocker của wave trước:

- cập nhật exact test receipt theo tool contract structured-`argv` hiện tại
  `bc44c044…a1fa769b0`;
- siết canonical event-time parser để reject `24:00:00Z`;
- giữ restart/reconcile fail-closed trên POSIX khi process còn sống nhưng owner
  handle của MCP đã mất; Windows Job Object mới được terminalize khi có proof
  tree đã chết. Test không còn yêu cầu nhận bừa PID POSIX;
- đổi riêng `ContextBudgetTests` sang `permission_mode="trusted"` vì chúng
  kiểm tra inline child output/exit-code; production `safe` policy vẫn từ chối
  inline script như thiết kế.

Validation integrated bằng Python runtime product **3.12.14**, pytest
**8.4.2**, `npm run test:all`:

- Node/Electron: **874 tests; 858 PASS, 16 SKIP, 0 FAIL**;
- MCP Python: **1.160 collected; 1.153 PASS, 7 SKIP, 0 FAIL** trong **159.31s**;
- source-root check: PASS; repository-secret check: PASS;
- direct focused regression của hash/timestamp/restart/continuous-check:
  **4/4 PASS**; `git diff --check` và Markdown whitespace check: PASS.

Đây là **`SOURCE_PRESENT + FOCUSED_TEST_PROOF` và integrated local test proof**.
Nó chưa chứng minh artifact Windows, DPAPI/ACL, Recovery fuse, reboot/startup,
hai ChatGPT client thật hoặc owner acceptance. Git vẫn ở branch
`codex/control-plane-quarantine`/HEAD `502ffb8c…`, worktree dirty có chủ ý; wave
này không commit, push, deploy, restart service hay gọi provider trả phí.

### Bước kế tiếp sau integrated gate

1. Chạy exact Windows package/fuse/Recovery smoke trên Windows host/pipeline;
2. kiểm DPAPI/`safeStorage`/ACL, reboot, reconnect, revoke, rotation và
   workspace replacement trên artifact exact;
3. nghiệm thu hai ChatGPT client cùng `principal_id`: inventory, chọn cùng
   `binding_id`, observe/stop/handoff và writer/generation fence;
4. chạy T01–T16, backup/restore, soak 24 giờ, owner acceptance; chỉ khi đó
   mới xem xét nâng `PACKAGED_PROOF` → `LIVE_ACCEPTED`.

## Checkpoint Python 3.14 direct suite — initial blocker classification (superseded) — 21-09-2026

Đã chạy lane Python MCP trực tiếp bằng **Python 3.14.4**, **pytest 8.4.2** và
đầy đủ dev dependencies cài vào runtime tạm; `NO_PROXY` chỉ giữ các địa chỉ
loopback IPv4 và thêm shim `python` để các fixture legacy không phụ thuộc tên
lệnh của host. Đây là một phép kiểm chứng direct của suite, không phải bằng
chứng package Windows hay live acceptance.

Git vẫn ở branch `codex/control-plane-quarantine`, HEAD
`502ffb8cf8b541ee74af30194aff2dce08c3b649`; worktree dirty có chủ ý vì các wave
source/test trước đó. Lượt kiểm tra này chỉ đọc/chạy test và cập nhật tài liệu;
không commit, push, deploy, restart service, tạo Job live hoặc gọi provider trả
phí.

- Collection: **1.160 test**.
- Kết quả: **1.149 PASS, 4 FAIL, 7 SKIP** trong khoảng **161s**.
- Các lỗi còn lại:
  1. `test_efficiency_runtime...` vẫn giữ exact hash cũ
     `d69436…f67810`, trong khi contract hiện tại có structured `argv` và sinh
     `bc44c044…a1fa769b0`. Đây là contract/test receipt cần chốt migration,
     không được tự coi là pass.
  2. `test_live_restart_reconcile...` sau khi MCP process chết chưa chuyển được
     managed command thành terminal receipt an toàn; command handle mất và job
     còn orphaned/non-terminal. Cần sửa reconcile theo process identity/owner
     fence, tuyệt đối không kill PID không còn chứng minh thuộc runtime.
  3. `test_operator_report_isolation...` parser Python 3.14 còn nhận
     `24:00:00Z`; cần siết canonical timestamp để reject giờ ngoài `00..23`.
  4. `test_continuous_check_terminalizes...` dùng `python -m pytest --version`,
     nhưng runtime cố ý không truyền `PYTHONPATH` tạm vào child nên child không
     thấy pytest. Đây là dependency/harness gap; host product phải cài dev
     extra vào interpreter thật trước khi dùng làm release proof.

Lần chạy đầu không có shim báo nhiều lỗi `python: not found`; sau khi sửa môi
trường còn bốn lỗi nêu trên. Vì vậy `npm run test:all` vẫn chỉ có Node/source
lane xanh (**874 tests; 858 PASS, 16 SKIP, 0 FAIL**) còn `npm run test:mcp` trên
host `/usr/bin/python3` vẫn dừng vì thiếu pytest. Control Plane unittest riêng
vẫn giữ bằng chứng **289/289 PASS**. Mức sản phẩm không đổi:
**`SOURCE_PRESENT + FOCUSED_TEST_PROOF`**, chưa được nâng lên
`PACKAGED_PROOF` hay `LIVE_ACCEPTED`.

### Việc phải làm ngay sau checkpoint

1. Chốt migration exact hash: cập nhật test/compatibility receipt cho contract
   `bc44…` nếu structured argv là contract hiện hành; giữ hash `d694…` chỉ như
   predecessor lịch sử.
2. Sửa và thêm focused proof cho restart/reconcile: terminalize đúng job có
   identity hợp lệ, bảo toàn `unknown/reconcile_required`, không suy đoán từ PID.
3. Siết parser timestamp và chạy lại nhóm operator-report.
4. Cài dev extra vào interpreter thật của test host hoặc pipeline, rồi chạy
   lại `npm run test:all`; chỉ sau đó mới chuyển sang Windows exact package,
   DPAPI/ACL, reboot/reconnect/revoke/rotation và T01–T16.

## Checkpoint npm host dependency — Node gate xanh, MCP pytest bị chặn bởi host — 21-09-2026 (previous run)

Đã chạy đúng lệnh tổng hợp `npm run test:all` trên working tree hiện tại. Kết
quả phải đọc tách theo từng lane:

- `npm test`: **874 tests; 858 PASS, 16 SKIP, 0 FAIL** trong khoảng **43.7s**.
- `check-source-root-clean.js`: PASS.
- `check-sensitive-tracked.js`: PASS.
- `npm run test:mcp`: **chưa chạy được** vì `/usr/bin/python3` báo
  `No module named pytest`; đây là dependency blocker, không phải test failure
  của MCP.
- Lệnh chuẩn `python3 -m pip install -e 'resources/coding-tools-mcp[dev]'` cũng
  chưa thể thực hiện trên host: Python không có `pip` và `python3 -m ensurepip`
  trả `No module named ensurepip`.

Vì vậy checkpoint này nâng bằng chứng Node/source checks trên đúng working tree,
nhưng không nâng Python MCP lên full pass và không thay đổi mức sản phẩm
`SOURCE_PRESENT + FOCUSED_TEST_PROOF`. Bước tiếp theo là chuyển sang test
host/pipeline có Python package tooling, cài đúng dev extra (`mcp>=1.26,<2`,
`pytest>=8,<9` cùng các dependency trong `pyproject.toml`), rồi chạy lại
`npm run test:all`. Không dùng pytest 9 hoặc collection thiếu `mcp` làm bằng
chứng thay thế.

## Checkpoint contract account chung — một tài khoản, nhiều máy điều khiển, workspace chọn bằng ID

Ngày cập nhật: **21-09-2026**, theo xác nhận mới nhất của chủ hệ thống.

### Kết luận sản phẩm đã chốt

Một workspace chỉ cần bind vào máy thực thi một lần. Lần bind đó tạo một
`binding_id` opaque. Mọi máy đang đăng nhập **cùng một tài khoản ChatGPT/OAuth**
đã được xác minh đều có thể nhìn thấy binding được chia sẻ và gửi việc tới ID
đó:

```text
ChatGPT client A/B/C (cùng principal_id)
  → chọn binding_id của workspace
  → Ubuntu xác thực, resolve và queue theo binding
  → node đã bind nhận task
  → runtime local trên node đọc/ghi/chạy Git/build/test/deploy
```

Ví dụ: máy A bind `W1` và nhận `B1`; người dùng mở ChatGPT trên máy B hoặc C,
chọn `B1`, thì lệnh chạy tại **A/W1**, không chạy trên B/C và không sao chép
workspace lên Ubuntu. Nếu máy D bind `W2` thành `B2`, cùng account thấy cả `B1`
và `B2`, nhưng mỗi task phải chọn đúng ID. Phiên có thể ghi nhớ một ID mặc
định; đó chỉ là state của client, không phải `active_workspace` toàn tài khoản
và không được retarget task đang chạy.

`binding_id` không phải bearer token. Task sau khi mở giữ immutable target:

```json
{
  "device_id": "…",
  "endpoint_id": "…",
  "workspace_id": "…",
  "workspace_generation": 7
}
```

Vì vậy cùng account không đồng nghĩa ghi đè tự do: writer lease, idempotency,
generation fence, local policy và terminal receipt vẫn áp dụng. Client khác có
thể observe/stop/handoff theo scope, nhưng không được đổi đích task đã mở.
Node secret, cookie/OAuth token, context và absolute path không được copy giữa
các máy. Máy chỉ điều khiển ChatGPT không cần enroll executor nếu nó không giữ
workspace.

### Tình hình hiện tại, đọc theo mức bằng chứng

| Hạng mục | Đã có/tận dụng | Bằng chứng gần nhất | Trạng thái thực tế |
| --- | --- | --- | --- |
| Account → binding → task target | `principal_id`, inventory, opaque `binding_id`, immutable target, writer lease/generation | Same-account HTTP focused **3/3 PASS**; Python Control Plane **295/295 PASS** | `SOURCE_PRESENT + FOCUSED_TEST_PROOF`; chưa có hai ChatGPT client live |
| Local write/document | `doc_create`/`doc_convert` qua node → Recovery → RuntimeOrchestrator → Coding Tools MCP | Document E2E **3/3 PASS**, bridge/adapter **10/10 PASS** | Fixture/source proof; Windows file-effect live còn mở |
| Local exec parity | Một structured-argv lane cho Git/build/test/deploy, cùng task/binding/writer/receipt | HTTP→node→Recovery **12/12 PASS** | Deterministic fixture; chưa phải toolchain Windows thật |
| Runtime continuity | Journal `prepared/completed/rejected/unknown`, stop/reconcile, continuation/reattach | Wave A **12/12**, Landlock **3/3**, continuity **21/21**, run continuation **50/50** | Source/local proof |
| Package/resource | Linux `dist:dir`, resource verifier, packaged/installed helper smoke | **3/3 PASS**; Windows PE verifier **285 + 9 files** | Linux preflight; chưa có RunAsNode/Recovery Windows |
| Regression/tooling | Node/Electron **874 tests: 858 PASS, 16 SKIP, 0 FAIL**; Control Plane **295/295 PASS**; MCP **1.153 PASS, 7 SKIP, 0 FAIL / 1.160**; release runner **2/2 PASS** | `node --check`, `py_compile`, `git diff --check` PASS | Full source/local gate xanh; Windows/package/live gates còn mở |

Mức được phép công bố hiện tại là **full source/local regression xanh** (nền
`SOURCE_PRESENT + FOCUSED_TEST_PROOF`).
Chưa được ghi `PACKAGED_PROOF` hoặc `LIVE_ACCEPTED` vì còn thiếu exact Windows
artifact, DPAPI/`safeStorage`/ACL, reboot/startup, reconnect, revoke/rotation,
Git/build/test/deploy thật và nghiệm thu hai client dùng chung `principal_id`.

### Những gì tận dụng ngay, không xây lại

| Nhu cầu | Khối hiện có cần giữ | Cách dùng trong thiết kế mới |
| --- | --- | --- |
| Danh tính tài khoản và binding | `mcp_oauth.py`, `http_api.py`, `mcp_facade.py`, `ControlPlaneStore` | Ánh xạ OAuth về cùng `principal_id`; inventory trả các `binding_id`; không tạo `active_workspace` toàn cục |
| Đăng ký máy lâu dài | Enrollment, device identity, credential riêng, heartbeat/presence, reconnect, rotation source path | Duyệt một lần; credential nằm ở node; reconnect không xin lại context/token |
| Chọn và khóa đích | Task-open/idempotency, writer lease, generation fence, queue/receipt | Mỗi task pin `{device, endpoint, workspace, generation}`; client khác không retarget |
| Thực thi local | Standing policy v2, `node_agent.py`, `RecoveryIpcServer`, `RecoveryHost`, `RuntimeOrchestrator`, Coding Tools MCP | Giữ quyền file/Git/process/build/test/deploy tại OS local của node |
| Fault/recovery | Journal, `unknown/reconcile_required`, stop/restart/reattach, connected-agent worker | Không spawn lại sau mất ACK; replay receipt; không giả terminal state |
| Package/evidence | Resource verifier, release runner, smoke scripts, `.coding-tools` ledger/evidence | Dùng để chứng minh exact artifact; không dùng Linux preflight thay Windows proof |

Không cần tạo lại credential theo máy, queue/task ledger, executor Ubuntu thứ
hai, hệ thống copy context/token, hay server AI controller cho đường MCP chính.
Provider/model gateway chỉ là nhánh tùy chọn nếu sản phẩm thật sự yêu cầu
Ubuntu chủ động gọi model; MCP/Tunnel không tự là API suy luận.

### Kế hoạch hoàn thiện theo gate

1. **G0 — khóa contract và candidate:** giữ semantics account/binding ở trên;
   chốt workspace fixture, device/endpoint, startup scope và exact artifact;
   không thêm approval từng context/lệnh trong standing local scope.
2. **G1/G2 — identity và enrollment:** chạy inventory trên hai client cùng
   `principal_id`; kiểm binding/revoke/retire; trên Windows exact candidate kiểm
   DPAPI/`safeStorage`, ACL, reboot, reconnect, credential rotation và mất ACK.
3. **G3 — full local capability:** chạy read/write/exec cùng một local lane;
   kiểm file/document, Git, build, test, deploy, output cursor, child-process
   stop và policy deny. Ubuntu chỉ dispatch/receipt; không nhận shell quyền OS.
4. **G4 — multi-client/continuity:** client A mở task tại `B1`, client B
   observe/stop/handoff; chạy crash, restart, lost-ACK, unknown/reconcile,
   writer lease và generation fence; chứng minh không duplicate effect/retarget.
5. **G5 — vận hành lâu dài:** kiểm presence `unknown/online/offline`, một agent
   sau reconnect, UI đóng/mở, Ubuntu restart, node reboot và revoke; ghi riêng
   verdict sau user-logon hay pre-login.
6. **G6 — release/acceptance:** chạy T01–T16 trên đúng packaged bytes, backup/
   restore, fault matrix cuối và soak liên tục tối thiểu 24 giờ; owner ký nhận
   rồi mới nâng `PACKAGED_PROOF` → `LIVE_ACCEPTED` và mới xem xét deploy.

### Bước kế tiếp chính xác

Sau khi xử lý 4 blocker direct suite, trên test host/pipeline cài dependency
đầy đủ vào interpreter thật rồi chạy:

```bash
python3 -m pip install -e 'resources/coding-tools-mcp[dev]'
npm run test:all
```

Sau đó chuyển sang host Windows exact để chạy package/fuse/Recovery smoke và
T01–T16. Cho tới khi có các receipt đó, chỉ cập nhật source/focused proof; lượt
này không commit, push, deploy, restart service hoặc gọi provider trả phí.

## Bản cập nhật điều hành theo xác nhận tài khoản dùng chung — 21-09-2026, 04:30 +07

Đây là phần tóm tắt phải đọc trước các checkpoint lịch sử bên dưới. Contract
đích đã chốt là:

```text
Một tài khoản ChatGPT/OAuth
  → một verified principal_id dùng chung trên mọi client
  → client chọn binding_id của workspace cần làm việc
  → Ubuntu xác thực, resolve target, queue/dispatch và trả receipt
  → đúng node đã bind thực thi trên workspace local bằng quyền OS/policy của máy
```

`binding_id` là selector của lần bind workspace vào một máy, không phải token,
context hay `active_workspace` toàn tài khoản. Vì vậy:

- Máy A bind workspace `W1` và nhận `B1`; mọi máy khác đăng nhập cùng account
  có thể chọn `B1` để ra lệnh tới **máy A/W1**. Máy đang mở ChatGPT chỉ là
  controller, không tự trở thành host thực thi và không nhận bản sao file.
- Nếu account có `B1`, `B2`, … thì inventory phải trả từng binding; client
  chọn ID theo task. Target của task đã mở là bất biến
  `{device_id, endpoint_id, workspace_id, workspace_generation}`. Không có
  thao tác đổi workspace toàn cục làm retarget task đang chạy.
- Cùng account không đồng nghĩa được ghi đè đồng thời: writer lease,
  idempotency, generation fence và receipt/reconcile vẫn áp dụng. Node secret,
  cookie/token ChatGPT, absolute path và context không được copy giữa client.
- Khi binding offline, revoked hoặc retired, control plane phải trả đúng trạng
  thái; không tự chuyển việc sang Ubuntu hay một máy khác.

### Hiện trạng có bằng chứng gần nhất

| Phần | Đã chứng minh | Mức bằng chứng hiện tại |
| --- | --- | --- |
| Account → nhiều binding | Hai token cùng `principal_id` thấy nhiều `binding_id`; task A/B giữ đúng target; observe không retarget | Focused HTTP **3/3 PASS** |
| Document write | `doc_create`/`doc_convert` đi HTTP → node → Recovery → RuntimeOrchestrator → Coding Tools MCP; crash/lost-ACK không tạo effect lần hai | Document E2E **3/3 PASS**, bridge/adapter **10/10 PASS** |
| Exec parity | Git/build/test/deploy dùng một structured-argv local lane, chung task/writer/binding và terminal receipt; Windows candidate đã chạy read/write/exec parity | HTTP→node→Recovery **12/12 PASS**; Windows E2E group **22/22 PASS** |
| Regression | Control Plane Python **289/289 PASS / 92.465s**; Node/Electron **858 PASS, 16 SKIP, 0 FAIL / 874 tests** | Source + focused/full test proof |
| Package | Linux preflight đạt; Windows candidate `dist:dir`, NSIS installer, packaged và installed Recovery smoke đều pass | Candidate `PACKAGED_PROOF`; chưa live/reboot/DPAPI/ACL |

Kết luận được phép ghi hôm nay là **`SOURCE_PRESENT + FOCUSED_TEST_PROOF` +
Windows candidate `PACKAGED_PROOF`**. Chưa được ghi `LIVE_ACCEPTED`: chưa chạy
DPAPI/ACL/safeStorage, reboot/startup, reconnect, revoke/rotation, Git/build/
test/deploy live hay hai ChatGPT client thật qua UI cùng `principal_id`.

### Tận dụng trực tiếp, không xây lại

- `mcp_oauth.py`, `http_api.py`, `mcp_facade.py` và `ControlPlaneStore` cho
  OAuth principal, account inventory, opaque binding, task idempotency, writer
  lease, generation fence, queue và receipt.
- Enrollment/credential riêng theo device, device identity, heartbeat/presence,
  reconnect, rotation source path, SecretStore/DPAPI path và workspace registry
  `{read, write, exec}`.
- Standing local policy v2, `node_agent.py`, journal `prepared/completed/
  rejected/unknown`, `RecoveryIpcServer`, `RecoveryHost`,
  `RuntimeOrchestrator`, Coding Tools MCP và `run-connected-agent`.
- Các bridge/fixture/proof đã có cho file-read, approved-patch, document-write,
  structured exec, stop/restart/reconcile và packaged resource verification.

Không cần tạo credential theo máy lần nữa, executor Ubuntu thứ hai, cơ chế copy
context/token giữa client, hay model gateway cho đường MCP chính. Gateway
provider chỉ mở thành nhánh riêng nếu yêu cầu sản phẩm chuyển sang “Ubuntu chủ
động gọi model để suy luận”.

### Thứ tự hoàn thiện bắt buộc

1. Trên host/pipeline Windows, build đúng artifact và chạy fuse/Recovery smoke;
   sau đó chạy Git/build/test/deploy thật bằng local policy của node.
2. Kiểm tra DPAPI/safeStorage/ACL, startup sau reboot, reconnect, revoke,
   rotation và workspace replacement trên candidate exact.
3. Dùng hai ChatGPT client thật cùng `principal_id`: inventory, chọn cùng/mỗi
   `binding_id`, mở task, observe/stop/handoff và chứng minh không retarget,
   không lộ secret/path.
4. Chạy fault matrix T01–T16, backup/restore và soak tối thiểu 24 giờ; ghi
   owner acceptance trước khi nâng mức thành `LIVE_ACCEPTED`.
5. Chỉ sau các gate trên mới quyết định release/deploy; lượt này không commit,
   push, deploy, restart service hoặc gọi provider trả phí.

## Checkpoint test-runner và regression hiện hành — 21-09-2026, 04:38 +07

Đã đóng một lỗi tooling có thể làm sai kết luận release trên Ubuntu: `npm run
test:mcp` trước đây gọi thẳng `python`, nên dừng với `python: not found` dù host
có `python3`. Runner dùng chung [scripts/run-python.js](../scripts/run-python.js)
nay hỗ trợ `--module`, tự chọn `python3` trên Unix và `python`/`py` trên
Windows; `package.json` gọi `pytest` qua runner đó. `pytest>=8,<9` cũng đã được
khai báo trong dev extra của `resources/coding-tools-mcp/pyproject.toml` và
hướng dẫn cài đặt đã ghi trong [TESTING.md](TESTING.md).

Bằng chứng sau thay đổi:

- Python Control Plane: **289/289 PASS trong 92.465s**.
- Node/Electron: **874 tests; 858 PASS / 16 SKIP / 0 FAIL trong 43.485s**;
  source-root và repository-secret checks PASS.
- Release-runner focused test: **2/2 PASS**; `node --check` và
  `git diff --check` PASS.
- `npm run test:mcp` đã chọn đúng `/usr/bin/python3` nhưng host hiện chưa cài
  module `pytest`, nên kết thúc trung thực bằng `No module named pytest`. Đây là
  **environment dependency gap**, không phải test pass và không được gộp vào
  bằng chứng Python 289/289.

Wave này chưa thay đổi quyền live, không tạo Job, không build/release/deploy,
không restart service và không gọi provider. Bước kế tiếp chính xác là cài dev
extras trên test host/Windows pipeline rồi chạy `npm run test:all`; sau đó mới
tiếp tục exact Windows package/fuse/DPAPI và hai-client acceptance.

## Checkpoint Python 3.14 runtime hardening — 21-09-2026, 04:44 +07

Đợt fallback `unittest` đã làm lộ hai lỗi runtime source thật, không liên quan
đến quyền account nhưng ảnh hưởng local execution:

- `runtime_behavior_identity.py` nay chuẩn hóa `slice(start, stop, step)` trong
  semantic code fingerprint. Trước đó Python 3.14 đưa hằng `slice` vào
  `co_consts`, làm continuity/reattach ném `TypeError` và false-fail.
- `landlock_exec.py` nay tự thêm package parent khi được gọi đúng vai trò
  standalone child. Trước đó helper chết trước argument validation vì relative
  import, khiến structured argv local lane trả exit 1 dù command hợp lệ.

Focused proof sau sửa:

- `test_wave_a_runtime`: **12/12 PASS trong 0.480s**.
- `test_landlock_exec`: **3/3 PASS**; có test process thật xác nhận standalone
  import/argument boundary.
- Continuation identity + internal structured argv: **2/2 PASS**.
- Continuation patch/proof-replan: **2/2 PASS**.
- `py_compile` cho hai module: PASS.

Đây là source/focused proof cho local runtime, không nâng mức thành Windows
packaged/live. `npm run test:mcp` vẫn cần cài dev extra `pytest` trước khi chạy
đầy đủ; `unittest` toàn suite không được dùng làm thay thế vì có test pytest và
external bridge/provider fixtures.

Bổ sung proof local sau khi sửa: `test_controller_continuity` +
`test_controller_reattach` **21/21 PASS**; `test_run_continuation` **50/50
PASS**. Điều này đóng false-fail Python 3.14 ở continuity/reattach trong scope
source/local; không thay thế pytest suite hoặc Windows/client live acceptance.

Dependency audit bổ sung: sandbox apt tạm có pytest **9.0.2** nhưng collection
dừng ở **1158 items / 1 error** vì thiếu package `mcp`; version này cũng không
khớp constraint `pytest>=8,<9`. Đây chỉ là chẩn đoán môi trường, không phải
pytest proof và không thay đổi repository. Host/pipeline đúng cần cài dev extra
đầy đủ từ `resources/coding-tools-mcp[dev]` rồi chạy lại `npm run test:all`.

## Checkpoint package/resource preflight sau runtime hardening — 21-09-2026, 04:46 +07

Đã đóng gói lại resource trên Linux sau hai sửa đổi Python runtime:

- `npm run dist:dir`: **PASS**, tạo `dist/linux-unpacked` và chạy
  `verify-packaged-resources.js` thành công.
- Packaged/installed helper tests: **3/3 PASS**.
- `node scripts/packaged-recovery-smoke.js`: trả
  `{"ok":true,"skipped":true,"reason":"windows_only"}` đúng contract.

Đây chỉ là resource/package preflight trên Linux. Fuse RunAsNode, Recovery Host
process, DPAPI/safeStorage/ACL và Git/build/test/deploy thật vẫn phải chạy trên
Windows exact artifact; không nâng mức bằng chứng thành `PACKAGED_PROOF`.

## Checkpoint W2 focused execution parity — 21-09-2026, 04:08 +07

Đã đóng một phần W2 ở mức source/focused proof mà không tạo executor mới:
`exec_command` structured `argv` chạy qua cùng chuỗi Recovery process →
`RuntimeOrchestrator` → Coding Tools MCP cho bốn nhóm thao tác `git`, build,
test và deploy. Bài kiểm tra dùng cùng một task, cùng writer lease và cùng
`binding_id`; mỗi action nhận terminal receipt riêng và không redelivery.

- Test mới: `test_oauth_exec_workflow_parity_uses_one_local_lane`.
- HTTP→node→Recovery exec suite: **12/12 PASS trong 22.262s** (11 ca fault/
  restart/stop trước đó và ca parity mới).
- Fixture ghi nhận chính xác các argv `git --version`, `npm run build`,
  `npm test`, `npm run deploy`; allowlist vẫn do policy local của node quyết
  định, Ubuntu không nhận shell string, environment map hay quyền deploy riêng.
- Đây là **`FOCUSED_TEST_PROOF` cho routing/receipt parity**, không phải bằng
  chứng npm/Git/deploy thật trên Windows. Deterministic MCP peer chỉ mô phỏng
  kết quả terminal; chưa được dùng để tuyên bố `PACKAGED_PROOF` hoặc
  `LIVE_ACCEPTED`.

W2 còn mở ở exact packaged/live toolchain: chạy Git/build/test/deploy thật dưới
  local policy của Windows, kiểm process/output/stop/unknown trên artifact đã
  đóng gói, rồi mới ghép với acceptance hai ChatGPT client cùng
  `principal_id`. Không thêm model gateway hay Ubuntu executor cho wave này.

## Checkpoint packaged preflight — 21-09-2026

Đã chạy preflight đóng gói trên môi trường Linux hiện tại để kiểm tra resource
allowlist và artifact wiring, nhưng không nâng mức bằng chứng thành Windows
packaged/live:

- `npm run dist:dir` tạo `dist/linux-unpacked` thành công; `verify-packaged-resources.js`
  xác nhận resource byte-identical và các bridge `document`, `exec`,
  `approved-patch`, `file-read` có mặt trong control-plane adapter.
- `node --test tests/packaged-recovery-smoke.test.js tests/installed-recovery-smoke.test.js`:
  **3/3 PASS**. Nhóm Node build/package verification liên quan đạt **12/12
  PASS**; `node scripts/packaged-recovery-smoke.js` trả
  `{"ok":true,"skipped":true,"reason":"windows_only"}` đúng contract.
- Lệnh mặc định `npx electron-builder --win --dir` dừng trước artifact vì
  `build.electronDist=node_modules/electron/dist` trỏ tới Linux distribution.
  Lệnh thử có override CLI `--config.electronDist=` đã tải Windows Electron và
  tạo PE `dist/win-unpacked/Coding Tools MCP.exe`; verifier độc lập xác nhận
  **285 resource files** và **9 control-plane adapter files** byte-identical.
  Hook `afterPack` vẫn fail-closed ở `assertRunAsNode` vì host Linux không thể
  thực thi `.exe`; do đó fuse/runtime chưa được chứng minh. Đây là
  cross-host/package preflight, không phải Windows packaged/live proof; không
  sửa cấu hình repo chỉ để bỏ qua fuse gate.

Kết luận: resource/package preflight đạt, còn `PACKAGED_PROOF` và
`LIVE_ACCEPTED` vẫn mở. Bước tiếp theo bắt buộc là chạy exact Windows build và
`test:recovery:packaged`/installed smoke trên host Windows hoặc artifact Windows
được build bởi pipeline có đúng Electron distribution; sau đó mới chạy Git/
build/test/deploy thật và T01–T16.

## Checkpoint same-account multi-binding focused proof — 21-09-2026

Đã bổ sung và chạy contract test HTTP cho đúng semantics account dùng chung:
`test_same_account_selects_multiple_bindings_without_retargeting_existing_task`.
Kết hợp với hai test account/task đã có, focused group **3/3 PASS trong 3.102s**:

- hai access token khác nhau cùng OAuth `principal_id` thấy inventory gồm hai
  `binding_id` của hai node/workspace;
- client A mở task trên binding A, client B mở task khác trên binding B;
- client B observe task A nhưng projection vẫn giữ `binding_id/device_id` của A,
  không retarget và không lộ `node_secret`/`canonical_path`.

Đây là `FOCUSED_TEST_PROOF` ở HTTP/facade/store boundary, chưa phải hai ChatGPT
client thật, Windows package, writer handoff trên Job live hay runtime effect.

## Checkpoint sau W1 E2E + full regression — 21-09-2026, 03:55 +07

Đây là checkpoint hiện hành thay cho các mô tả W1 cũ ở bên dưới. Đã sửa hai
blocker relay/crash setup, bổ sung ca mất ACK và chạy lại focused/full tests.
Không tạo Job live, không đổi quyền live, không commit/push/deploy/restart và
không gọi provider trả phí. Git vẫn ở
`codex/control-plane-quarantine@502ffb8cf8b541ee74af30194aff2dce08c3b649`;
worktree dirty do batch thay đổi đang được giữ lại.

### Mô hình account/workspace đã chốt

```text
ChatGPT/OAuth account
  → verified principal_id (dùng chung cho mọi client của account)
  → client chọn binding_id của workspace/host
  → task pin bất biến {device_id, endpoint_id, workspace_id, workspace_generation}
  → Ubuntu auth/router/queue/receipt
  → đúng node đã bind thực thi bằng file/tool/process/quyền OS local
```

`binding_id` là ID opaque của một lần bind workspace vào máy, không phải token
và không phải `active_workspace` toàn tài khoản. Hai hoặc nhiều máy mở cùng
một tài khoản có thể nhìn thấy cùng inventory và chọn cùng `binding_id`; khi đó
các lệnh đi về **cùng máy chứa workspace đó**. Writer lease, idempotency và
task pin quyết định việc ghi/tiếp quản; client B không thể đổi đích task A đang
chạy. Client chỉ mở ChatGPT không cần enroll node nếu nó không chứa workspace.

Ubuntu giữ xác thực, định tuyến, hàng đợi, trạng thái và receipt. Node đã bind
giữ credential riêng, file, Git, process, build/test/deploy và quyền OS local.
“Toàn quyền” chỉ trong phạm vi user/ACL và policy local của máy; không biến tài
khoản thành Windows Administrator.

### Tình hình hiện tại, bằng chứng và giới hạn kết luận

| Hạng mục | Hiện đã có trong source | Bằng chứng gần nhất | Còn phải đóng |
| --- | --- | --- | --- |
| Identity/account | OAuth `principal_id`, account inventory, owner mapping | Full Python **289/289 PASS**; HTTP tests có ca hai client cùng principal | Hai client ChatGPT thật trên Windows |
| Binding/target | `binding_id`, immutable task target, writer lease, generation fence | Store/OAuth/task focused proof | Reconnect/revoke/retire trên package thật |
| Node tin cậy | Enrollment hai bước, credential riêng, heartbeat/reconnect, rotation source, workspace registry `{read,write,exec}` | Enrollment/secret/rotation source tests | DPAPI, ACL, reboot và rotation trên Windows package |
| Runtime local | Standing policy v2, file-read, approved-patch, exec, journal và Recovery IPC/Host/Orchestrator | Approved-patch/exec đã có Recovery-process fixture | Full Git/build/test/deploy acceptance trên package |
| Document write W1 | Central intent/schema; Electron bridge; CJS descriptor-hiding bridge; RecoveryHost handler; node `document_write` poll/loop/CLI/lane; packaged allowlist/smoke wiring | HTTP→node→Recovery→MCP E2E **3/3 PASS**; bridge **10/10 PASS**; full Python/Node xanh | Windows package/live file-effect và quyền OS thật |
| Model boundary | Ubuntu auth/router/queue/receipt và MCP tool relay | Function/tool boundary đã được phân biệt | Chỉ thêm provider gateway nếu Ubuntu phải chủ động gọi model |

Validation hiện hành: Python **289/289 PASS trong 91.287s**; Node/Electron
**873 tests; 857 PASS / 16 SKIP / 0 FAIL trong 43.611s**, kèm source-root và
repository-secret checks PASS. Focused document node-agent + HTTP E2E là
**8/8 PASS** (trong đó E2E document **3/3 PASS**); bridge/adapter là
**10/10 PASS**. `py_compile`, `node --check` và `git diff --check` PASS.
ResourceWarning về một số connection SQLite trong suite là cảnh báo không làm
test fail, chưa phải bằng chứng package/live. Mức đúng vẫn là
**`SOURCE_PRESENT + FOCUSED_TEST_PROOF`**, chưa phải `PACKAGED_PROOF` hoặc
`LIVE_ACCEPTED`.

### W1 đã nối đến đâu và việc kế tiếp theo đúng thứ tự

Đã nối và chứng minh bằng fixture process thật đủ source path cho lane document
create/convert:

1. `recovery_document_write_bridge.cjs` đọc request bounded, dùng descriptor
   Recovery hiện hành và chỉ trả receipt digest-only; descriptor, MCP token và
   absolute path không đi về Ubuntu.
2. `RecoveryHost` nhận `runtime.control_plane_document_write`, kiểm device,
   local writable policy, workspace registry, runtime identity và facade
   contract trước khi gọi `RuntimeOrchestrator`.
3. `node_agent.py` có strict action admission, `prepared/completed/rejected/
   unknown` journal, lock riêng, `poll-document-write-once`,
   `run-document-write-loop` và lane thứ năm của `run-connected-agent`.
4. Package resource allowlist và packaged smoke đã biết bridge mới.
5. CJS request cap đã tăng lên `512 KiB`, đủ chứa content cap `256 KiB` cộng
   envelope; boundary dưới/trên cap có test.
6. Receipt relay đã kiểm tra `attempt_id` với delivery attempts đã dispatch;
   status chỉ trả projection digest-only, không trả content/absolute path/token.

Proof E2E hiện tại:

- `doc_create` ghi file `.md` thật và `doc_convert` ghi `.docx` thật qua chuỗi
  HTTP facade → node poll → CJS bridge → Recovery IPC/Host →
  RuntimeOrchestrator → local Coding Tools MCP fixture.
- Crash sau local effect tạo `unknown/reconcile_required`; poll sau không gọi
  lại `document_workflow`.
- Central `completed` nhưng mất ACK được replay từ journal; không tạo effect
  lần hai và status vẫn relay được receipt.

Các việc chưa được coi là hoàn tất:

1. Đóng W2 execution parity: map Git/build/test/deploy vào các lane structured
   hiện có, giữ task/writer/receipt semantics và quyền OS tại node.
2. Chạy package Windows thật: DPAPI/safeStorage, ACL, startup/reboot,
   reconnect, revoke/rotation và workspace replacement; Linux fixture không
   được dùng để thay thế gate này.
3. Chạy same-account acceptance với hai ChatGPT client/access token thật:
   cùng `principal_id`, cùng `binding_id`, observe/handoff writer lease và
   chứng minh task đang chạy không bị retarget.
4. Kiểm tra release/package/evidence và soak; chỉ ghi `PACKAGED_PROOF` khi
   artifact Windows đã chạy, và chỉ ghi `LIVE_ACCEPTED` sau owner acceptance.
5. Chỉ bổ sung provider/model gateway nếu yêu cầu thực tế là Ubuntu chủ động
   gửi request suy luận; MCP/Tunnel hiện chỉ relay tool call.

### Tận dụng gì, không xây lại gì

- **Identity:** OAuth introspection/link, `principal_id`, owner mapping và
  account inventory trong `mcp_oauth.py`, `http_api.py`, `ControlPlaneStore`.
- **Target:** `bindings`, opaque `binding_id`, `node_workspaces`, workspace
  generation, retire/rebind và heartbeat presence; central không relay path.
- **Authority:** `mcp_task_sessions`, idempotency, immutable target,
  `mcp_task_writer_leases`, action claim, terminal receipt và
  `unknown/reconcile_required`.
- **Trusted node:** enrollment hai bước, credential riêng theo device,
  reconnect/heartbeat/rotation, SecretStore/DPAPI source path và workspace
  registry/capability local.
- **Local execution:** standing policy v2, allowlist/generation/OS checks,
  journal chống duplicate-effect, `RecoveryIpcServer`, `RecoveryHost`,
  `RuntimeOrchestrator`, Coding Tools MCP và `run-connected-agent`.
- **Product boundary:** `document_workflow` chỉ là local tool được node gọi;
  MCP/tunnel không tự biến thành model API. Chỉ thêm gateway provider khi
  Ubuntu thật sự phải chủ động gửi request suy luận.

### Checkpoint vận hành

W1 source/fixture đã đạt, nhưng chưa mở capability write live trên package và
chưa có Windows/ChatGPT-client acceptance. Không có provider call, deploy,
restart service, commit hoặc push. Bước chính xác tiếp theo là W2 parity →
Windows packaged/live gates → same-account acceptance → owner/release gate;
mọi checkpoint phải giữ phân loại `SOURCE_PRESENT + FOCUSED_TEST_PROOF` cho tới
khi có receipt/package/live evidence tương ứng.

## Checkpoint baseline trước khi nối W1 — 21-09-2026, 03:18 +07

Đã xác minh lại trên cùng working tree, không tạo Job, không đổi quyền live,
không commit/push/deploy/restart và không gọi provider trả phí. Git vẫn ở
`codex/control-plane-quarantine@502ffb8cf8b541ee74af30194aff2dce08c3b649`,
worktree dirty do batch thay đổi đang được giữ lại.

| Hạng mục | Bằng chứng mới nhất | Kết luận được phép ghi |
| --- | --- | --- |
| Python control-plane | `PYTHONPATH=control-plane python3 -m unittest discover -s control-plane/tests -v`: **279/279 PASS**, **84.520s** | Central OAuth/account/binding/task/writer/queue/receipt và các lane hiện có không hồi quy |
| Node/Electron | `npm test`: **868 tests; 852 PASS / 16 SKIP / 0 FAIL**, **43.845s**; source-root + repository-secret checks PASS | Regression source hiện xanh trên Linux; các ca Windows vẫn chưa được đóng |
| Syntax/integrity | `py_compile`, `node --check` cho các file bridge/runtime, `git diff --check`: PASS | Không có lỗi cú pháp/whitespace trong batch kiểm tra này |
| Document central admission | focused `test_standing_document_create_is_durable_and_does_not_put_content_in_action_payload`: **1/1 PASS** | Ubuntu đã nhận intent có task/writer/generation/idempotency; **chưa chứng minh file-effect trên node** |
| Document bridge guards | focused Node bridge/runtime regression: **14/14 PASS** | Admission/receipt validator source có proof; chưa phải Recovery-process create/convert |

### Tình hình hiện tại và phần đã tận dụng

Mô hình đã chốt không đổi:

```text
một ChatGPT account/OAuth principal_id
  → chọn binding_id
  → task pin {device_id, endpoint_id, workspace_id, workspace_generation}
  → Ubuntu auth/queue/receipt
  → node đã bind giữ credential/file/Git/process và quyền OS local
```

Đã tái sử dụng trực tiếp: OAuth principal/account inventory; `ControlPlaneStore`
với binding, task idempotency, writer lease và immutable generation; enrollment
hai bước và credential riêng theo device; heartbeat/presence/reconnect/rotation;
standing policy v2 và workspace registry; journal/receipt `unknown /
reconcile_required`; `RecoveryIpcServer`, `RecoveryHost`,
`RuntimeOrchestrator`, Coding Tools MCP và `run-connected-agent`. Không cần dựng
lại credential theo máy, queue trung tâm, executor Ubuntu thứ hai, hay cơ chế
copy token/context giữa các client cùng account.

### W1 đang ở đâu

Source đã có central `mcp_document_write_intents`, action lane/schema,
`controlPlaneDocumentWriteBridge.js`, `RuntimeOrchestrator.controlPlaneDocumentWrite()`
và `RecoveryIpcClient.controlPlaneDocumentWrite()`. `node_agent.py` hiện đã có
admission strict, digest-only result validator và journal `prepared/completed/
rejected/unknown`; các helper này đã qua `py_compile` nhưng chưa có poller chạy
thật. Còn thiếu đúng các mắt xích sau:

1. `recovery_document_write_bridge.cjs` để ẩn Recovery descriptor/MCP token.
2. Handler `runtime.control_plane_document_write` trong `RecoveryHost` và import
   policy/admission/normalizer tương ứng.
3. Node `poll_document_write_once`, lock/loop/CLI mapping và lane thứ năm trong
   `run-connected-agent`.
4. Recovery-process fixture create/convert, stale generation/path/overwrite/
   capability rejection, crash/lost-ACK/replay tests; sau đó mới xem xét mở
   capability write trên package Windows.

Vì vậy mức đúng hiện tại vẫn là **`SOURCE_PRESENT + FOCUSED_TEST_PROOF`**, chưa
phải `PACKAGED_PROOF` hay `LIVE_ACCEPTED`.

## Checkpoint xác minh mới nhất — 21-09-2026, 03:05 +07

Đây là checkpoint kiểm chứng lại source và test trên cùng working tree; không
đổi quyền live, không tạo Job, không commit/push/deploy/restart và không gọi
provider trả phí. Git vẫn ở branch `codex/control-plane-quarantine`, HEAD
`502ffb8cf8b541ee74af30194aff2dce08c3b649`; worktree vẫn dirty vì chứa batch
thay đổi đang được giữ lại.

| Hạng mục | Kết quả hiện đã kiểm chứng | Ý nghĩa sản phẩm |
| --- | --- | --- |
| Python control-plane | `PYTHONPATH=control-plane python3 -m unittest discover -s control-plane/tests -v`: **279/279 PASS**, 83.534s | OAuth, binding/account inventory, task/writer fence, queue/receipt, enrollment, read/patch/exec fixture không hồi quy |
| Node/Electron | `npm test`: **868 tests; 852 PASS / 16 SKIP / 0 FAIL**; source-root và repository-secret check PASS | Các bridge/runtime/Recovery regression hiện không có lỗi trên môi trường Linux này |
| Syntax/diff | `node --check`, `py_compile`, `git diff --check`: PASS | Chưa phát hiện lỗi cú pháp hoặc whitespace trong batch hiện tại |
| Document central lane | `test_standing_document_create_is_durable_and_does_not_put_content_in_action_payload`: **1/1 PASS** (nằm trong 279) | Ubuntu đã nhận/admit và xếp hàng intent; **chưa chứng minh file được ghi trên node** |

### Kết luận vận hành tại checkpoint này

Semantics đã chốt là:

```text
một tài khoản ChatGPT/OAuth principal_id
  → chọn binding_id của workspace/host
  → task pin {device_id, endpoint_id, workspace_id, workspace_generation}
  → Ubuntu xác thực, queue và lưu receipt
  → node đã bind giữ credential/file/Git/process và thực thi bằng quyền OS local
```

Các máy cùng đăng nhập một tài khoản có thể nhìn thấy và chọn cùng
`binding_id`; máy chỉ mở ChatGPT là **controller**, không tự trở thành execution
host. Không có `active_workspace` toàn tài khoản, không copy token/context/node
secret giữa máy, và task đang chạy không bị đổi đích chỉ vì client khác chọn
một binding khác. `online/offline/unknown` chỉ là presence, không phải cấp
quyền.

### Đã tận dụng trong code hiện có

- **Identity/account:** OAuth introspection/link, `principal_id`, owner mapping
  và account inventory trong `mcp_oauth.py`, `http_api.py`, `ControlPlaneStore`.
- **Workspace target:** opaque `binding_id`, `node_workspaces`, generation,
  retire/rebind và heartbeat presence; central không lưu/relay absolute path.
- **Task/authority:** `mcp_task_sessions`, idempotency, immutable target,
  `mcp_task_writer_leases`, action claim, terminal receipt và
  `unknown/reconcile_required`.
- **Node tin cậy:** enrollment hai bước, credential riêng theo device,
  reconnect/heartbeat, rotation source path, workspace registry và capability
  local `{read, write, exec}`.
- **Runtime local:** standing policy v2, allowlist/generation/OS check,
  journal chống duplicate-effect, `RecoveryIpcServer`, `RecoveryHost`,
  `RuntimeOrchestrator`, Coding Tools MCP và `run-connected-agent`.
- **Đã có proof mạnh hơn:** approved-patch và exec đã đi qua Recovery process
  fixture với lost-ACK/crash/restart/writer-lease cases; document read đã dùng
  standing file-read policy.
- **Document write đang nối tiếp:** central `mcp_document_write_intents` và
  `controlPlaneDocumentWriteBridge.js` đã có admission/receipt shape; lane node
  và CJS Recovery bridge chưa hoàn tất nên chưa quảng bá capability live.

### Việc còn thiếu, theo thứ tự không được bỏ qua

1. **W1 — đóng document write end-to-end:** thêm node lane
   `document_write`, CJS bridge ẩn descriptor/token, handler RecoveryHost và
   fixture create/convert thật; mọi rejection phải xảy ra trước local effect.
2. **W1 fault proof:** journal `prepared/completed/rejected/unknown`, crash/lost
   ACK/restart/replay; `unknown` phải yêu cầu reconcile và không gọi
   `document_workflow` lần hai.
3. **W2 — execution parity:** giữ cùng task/writer/receipt semantics cho
   document, patch và exec; sau đó map Git/build/test/deploy vào runtime local,
   không chuyển quyền OS sang Ubuntu.
4. **W3 — same-account acceptance:** hai access token/client cùng
   `principal_id` chọn một binding, client B observe/handoff, không retarget task
   A đang chạy.
5. **W4 — Windows packaged/live:** chạy Electron/Recovery package thật, kiểm
   DPAPI/safeStorage, ACL, startup/reboot, reconnect, revoke và rotation; Linux
   fixture không đóng gate này.
6. **W5/W6 — model boundary và release:** chỉ thêm provider gateway nếu Ubuntu
   phải chủ động gọi model; sau đó soak 24h, backup/restore, staged evidence và
   owner acceptance. Không nhầm MCP tool relay với model API.

Cho tới khi W1–W4 có receipt/file-effect trên Windows thật, trạng thái đúng là
`SOURCE_PRESENT + FOCUSED_TEST_PROOF`, chưa phải `PACKAGED_PROOF` hoặc
`LIVE_ACCEPTED`.

## Recheck tài liệu theo xác nhận account dùng chung — 21-09-2026, 02:50 +07

Lượt này chỉ cập nhật kế hoạch và đối chiếu source/status trong working tree;
không thay đổi quyền live, không tạo Job, không commit/push/deploy/restart và
không gọi provider trả phí. Bằng chứng test gần nhất vẫn là checkpoint
**02:40 +07** được ghi ngay dưới đây.

Quy tắc sản phẩm đã chốt: một tài khoản ChatGPT/OAuth được ánh xạ về cùng
`principal_id`; mỗi workspace bind tạo một `binding_id`; mọi máy chỉ mở
ChatGPT nhưng đăng nhập cùng principal có thể chọn `binding_id` đó. Chỉ máy
chứa workspace mới là execution host và giữ node credential, file, Git,
process, build/test/deploy cùng quyền OS local. Nếu có nhiều binding, chọn ID
theo từng task; nếu chỉ có một binding, client có thể dùng nó làm mặc định của
phiên. Mặc định phiên không phải `active_workspace` toàn tài khoản và không
được đổi đích của task đang chạy.

Trạng thái hiện tại vẫn là **SOURCE_PRESENT + FOCUSED_TEST_PROOF**, chưa phải
`PACKAGED_PROOF` hay `LIVE_ACCEPTED`: central document-write đã có schema và
admission, nhưng node document-write/Recovery bridge/file-effect, Windows
packaged/live và hai ChatGPT client thật còn mở.

## Bảng điều hành bằng chứng gần nhất — 21-09-2026, 02:40 +07

### Kết luận ngắn

Mô hình đúng của sản phẩm là:

```text
một tài khoản ChatGPT
  → OAuth principal_id đã xác minh
  → chọn binding_id của workspace/host
  → task pin bất biến tới device/endpoint/workspace/generation
  → Ubuntu xác thực, xếp hàng, chuyển receipt
  → máy Windows đã bind thực thi bằng file/tool/process/quyền OS local
```

Máy đang mở ChatGPT chỉ là **controller**. Máy có workspace mới là
**execution host**; nó giữ credential riêng, file, Git, process, build/test và
triển khai. Không dùng `active_workspace` toàn tài khoản, không dùng tên máy,
raw path hoặc bare `workspace_id` để định tuyến, và không chép context/token/
node-secret giữa các máy.

### Tình hình đã chứng minh trong repository

| Mức | Hiện trạng | Bằng chứng gần nhất | Không được suy ra |
| --- | --- | --- | --- |
| Identity/account | Có OAuth principal/link/owner inventory; nhiều access token của cùng principal giữ cùng target | OAuth focused và HTTP class có ca hai client cùng principal | Chưa có hai ChatGPT client thật chạy trên Windows |
| Workspace target | `binding_id` pin `{device_id, endpoint_id, workspace_id, workspace_generation}`; generation thay thế/retire có fence | store/OAuth/task tests, account inventory presence | Chưa có packaged/live reconnect và revoke trên máy thật |
| Task/writer | task idempotency, immutable target, writer lease/generation; lease giữ tới terminal receipt | `test_mcp_task_sessions`, OAuth handoff/exec tests | Chưa đóng Job handoff trên Windows thật |
| Node enrollment | credential riêng theo node, heartbeat/poll, reconnect worker, rotation/DPAPI source path | enrollment/rotation/secret focused tests | Chưa chứng minh DPAPI/ACL/safeStorage live |
| Local execution | standing file-read, approved-patch và exec policy; Recovery IPC/Host + RuntimeOrchestrator + Coding Tools MCP | approved-patch HTTP→Recovery **5/5**, exec/stop Recovery **11/11** | Chưa là package Windows/live; chưa có full Git/build/test/deploy acceptance |
| Document read | `document_workflow` read dùng standing file-read policy, allowlist, generation, receipt | standing artifact-read **1/1**, file-read node **10/10** | Đây không phải document write |
| Document create/convert | Central schema/admission draft đã có (schema 24, idempotency, task/writer pin, digest-only relay validator); feature flag chưa được bật live | central focused **1/1**, full Python **279/279**, central code compile | **Chưa có node document-write poller, Recovery bridge hay file-effect proof**; không được gọi là đã dùng được |

### Đã tận dụng gì, không xây lại gì

1. **Identity và account:** tái dùng OAuth introspection/link request,
   `principal_id`, owner mapping và inventory path-free trong `mcp_oauth.py`,
   `http_api.py` và `ControlPlaneStore`.
2. **Đích workspace:** tái dùng `bindings`, `node_workspaces`, opaque
   `binding_id`, workspace generation và trạng thái presence từ heartbeat.
3. **Dòng công việc:** tái dùng `mcp_task_sessions`, idempotency, immutable
   target, `mcp_task_writer_leases`, action links và terminal receipt.
4. **Máy tin cậy:** tái dùng enrollment hai bước, node credential riêng,
   reconnect/heartbeat/poller và rotation; credential không đi qua MCP client.
5. **Runtime local:** tái dùng local policy v2, workspace registry/allowlist,
   journal chống duplicate-effect, `RecoveryIpcServer`, `RecoveryHost`,
   `RuntimeOrchestrator` và Coding Tools MCP.
6. **Quan sát:** tái dùng action status, receipt digest-only, `unknown /
   reconcile_required`, inventory `online/offline/unknown`; không biến status
   thành quyền mới.
7. **Model:** không giả định MCP/tunnel là API suy luận. Nếu Ubuntu phải chủ
   động gọi provider, bổ sung gateway riêng; nếu ChatGPT vẫn là controller thì
   chỉ cần tool relay hiện có.

### Kế hoạch hoàn thiện theo wave

| Wave | Việc phải làm | Điều kiện đạt |
| --- | --- | --- |
| W0 — contract freeze | Chốt `principal_id → binding_id → task pin`; không có account-wide active target; ghi rõ capability local `{read, write, exec}` và trạng thái `unknown/offline/revoked/retired` | `tools/list`, inventory và task status cùng một contract; không lộ path/secret |
| W1 — document write | Thêm lane `document_write` riêng trong node-agent; kiểm source/target, extension, allowlist, generation, overwrite, content cap; gọi Coding Tools MCP `document_workflow`; thêm `RecoveryIpc/Host/RuntimeOrchestrator` bridge; journal prepared/completed/unknown và replay | create/convert thật trong fixture, lost-ACK/crash không chạy effect lần hai; central status relay đúng digest |
| W2 — execution parity | Giữ `exec_run/poll/stop`, approved-patch, document write dưới cùng task/writer/receipt semantics; map Git/build/test/deploy vào local runtime, không chuyển quyền OS sang Ubuntu | mỗi lane có rejection trước effect, terminal receipt, unknown không auto-retry; local capability là nguồn quyết định |
| W3 — same-account acceptance | Hai client/token khác nhau nhưng cùng `principal_id`: inventory cùng thấy binding; client A mở task, B observe; writer handoff có kiểm soát; task đang chạy không đổi target | T01/T04/T06/T16 trên exact package; không có context/token copy |
| W4 — Windows package | Chạy packaged Electron/Recovery process thật; DPAPI/safeStorage, ACL, startup sau reboot, reconnect, offline/revoke, credential rotation | evidence `PACKAGED_LIVE`, không dùng Linux/fake encryption để đóng gate |
| W5 — Ubuntu/provider boundary | Nếu cần máy chủ tự suy luận, triển khai provider gateway với auth/budget/timeout/receipt; nếu không, giữ Ubuntu ở auth/router/queue | test tool-call không bị nhầm thành model API; provider call chỉ khi có ủy quyền |
| W6 — soak/release | T01–T16, fault matrix, 24h soak, backup/restore, staged delivery snapshot; chỉ sau đó mới activation/release | owner acceptance, live receipt, packaged artifact và `.coding-tools` evidence khớp |

### Gói triển khai kế tiếp — W1 document write

Đây là batch tiếp theo, dùng lại toàn bộ identity/binding/task/runtime hiện có;
không tạo policy universe hoặc executor thứ hai:

| Bước | Việc cụ thể | Điều kiện kiểm chứng |
| --- | --- | --- |
| W1-A — node lane | Thêm `poll_actions(..., lane="document_write")`; parse strict các trường `mcp_document_write_*`; kiểm `operation`, source/target, extension, title/content cap, overwrite, allowlist, workspace generation, task và writer lease trước effect | action sai bị `rejected` trước local write; đúng action mới được `prepared` |
| W1-B — Recovery bridge | Tạo `electron/services/controlPlaneDocumentWriteBridge.js` và `control-plane/control_plane/recovery_document_write_bridge.cjs`; nối `RecoveryIpc`, `RecoveryHost`, `RuntimeOrchestrator.controlPlaneDocumentWrite()` | bridge fail-closed, không lộ descriptor/MCP token/absolute path về Ubuntu |
| W1-C — local MCP | Bootstrap exact workspace bằng `workspace_context`; gọi `document_workflow` với `action=create` hoặc `action=convert`; local runtime chịu filesystem/OS permission | create/convert ghi đúng host; overwrite, path, generation và capability bị chặn đúng lý do |
| W1-D — receipt/journal | Ghi `prepared/completed/rejected/unknown`; giữ `action_id`, `attempt_id`, `task_id`, `writer_lease_generation`; relay digest-only theo `_completed_document_write_relay()` | crash/lost-ACK chỉ replay receipt hoặc `reconcile_required`, không chạy effect lần hai |
| W1-E — focused/E2E | Bổ sung node poller, Recovery-process create/convert, stale generation/path/allowlist/overwrite, HTTP→node status và crash/lost-ACK tests | document create/convert fixture đạt full pass; sau đó mới mở W2 parity |

Receipt thành công phải mang tối thiểu `operation_kind=control_plane_document_write`,
`local_handle`, `action_id`, `attempt_id`, `task_id`,
`writer_lease_generation`, `operation`, `target/source`, `{size, sha256, format}`
và actor/runtime/contract metadata. Raw document content, absolute path,
Recovery descriptor và credential không được relay về Ubuntu.

### Ma trận nghiệm thu tối thiểu

- **T01:** một node đăng ký/duyệt một lần, reboot/reconnect vẫn dùng credential
  riêng; thu hồi thì dừng dispatch.
- **T02:** hai binding cùng tên workspace nhưng khác `device_id` không lẫn
  action/receipt.
- **T03:** cùng principal chọn từng `binding_id`; không có retarget task đang
  chạy.
- **T04:** hai client cùng principal quan sát cùng task; writer lease chặn
  ghi cạnh tranh và handoff sau terminal.
- **T05:** node offline/stale heartbeat chỉ đổi presence, không cấp quyền và
  không failover âm thầm.
- **T06:** patch/document/exec thành công có receipt digest; mất ACK chỉ
  replay receipt, không chạy effect lần hai.
- **T07:** crash sau prepared hoặc MCP disconnect → `unknown/reconcile_required`;
  restart không redeliver.
- **T08:** stale generation/path/preimage/allowlist/capability bị reject trước
  local effect.
- **T09:** read/write/Git/build/test/deploy chỉ chạy ở workspace node với quyền
  OS local; Ubuntu không thành Administrator.
- **T10:** credential rotation prepare/activate/ack và retry không làm lộ secret.
- **T11:** Recovery process crash/restart giữ journal/Job handle và terminal
  state.
- **T12:** document create/convert chỉ sau khi W1 có bridge process thật.
- **T13:** Windows DPAPI/safeStorage/ACL live, không dùng fake/mocked proof.
- **T14:** model gateway (nếu bật) tách khỏi MCP tool relay, có budget/timeout.
- **T15:** 24h soak, queue/reconcile/backup restore và no-duplicate-effect.
- **T16:** owner thu hồi/rebind/revoke; mọi client nhận trạng thái rõ ràng.

### Quy tắc báo cáo trạng thái

Chỉ dùng `SOURCE_PRESENT`, `FOCUSED_TEST_PROOF`, `PACKAGED_PROOF` hoặc
`LIVE_ACCEPTED` đúng với bằng chứng thực tế. Một test fixture không đóng gate
Windows/live; central queue không có nghĩa file đã ghi; `online` không có nghĩa
được cấp thêm quyền. Tài liệu này là kế hoạch và bảng bằng chứng, không phải
thông báo đã bật full quyền.

> **Override hiện hành — 21-09-2026, 02:40 +07:** nếu các dòng tổng hợp
> checkpoint cũ bên dưới còn ghi 01:08/2/2, 3/3 hoặc 275/275, hãy dùng
> checkpoint mới nhất ở đây: HTTP→node approved-patch **5/5 PASS trong
> 11.771s**, full Python **279/279 PASS trong 82.053s**, central document-create
> focused **1/1 PASS**, Node
> approved-patch/Recovery bridge **12/12 PASS**. Hai ca mới chạy qua
> **Recovery process thật 2/2 PASS**: crash sau local `apply_patch` là
> `unknown/reconcile_required` và restart không redeliver; central đã commit
> `completed` nhưng mất ACK thì journal replay receipt mà không chạy patch lần
> hai. Artifact `document_workflow` read cũng đã có standing-policy focused
> proof **1/1** (file-read node suite **10/10**). Đây vẫn là source/focused
> fixture proof, không phải Windows/live hoặc two-client proof.

> **Ngày cập nhật:** 21-09-2026, 02:40 +07 (Asia/Bangkok).
> **Baseline khảo sát:** `codex/control-plane-quarantine@502ffb8cf8b541ee74af30194aff2dce08c3b649` **cộng các thay đổi chưa commit có sẵn**; wave này nối standing-write qua HTTP OAuth → node poller → local policy → receipt, bổ sung oracle stale-generation/unknown, standing Recovery-process proof và focused standing artifact-read proof, không thay đổi hệ thống live.
> **Làm rõ account dùng chung:** một lần bind workspace tạo ra `binding_id`; mọi ChatGPT client đăng nhập cùng `principal_id` đã được OAuth xác minh có thể chọn ID đó. Client đang mở ChatGPT chỉ là controller, không phải execution host và không cần enroll nếu không chứa workspace. Task pin `{binding_id, device_id, endpoint_id, workspace_id, workspace_generation}` bất biến; không có `active_workspace` toàn tài khoản và không copy context/token/node secret giữa các máy.
> **Supersede mới nhất — 02:18 +07:** standing approved-patch đã chạy qua Recovery process fixture thật **2/2 PASS** (crash→`unknown/reconcile_required` không redeliver; completed receipt mất ACK được replay không chạy patch lần hai). HTTP→node class hiện **5/5 PASS**, full Python discovery **278/278 PASS trong 82.054s** sau khi thêm standing artifact-read proof, Node bridge/Recovery **12/12 PASS**. Đây vẫn là source/focused proof; Windows packaged/live và hai ChatGPT client thật còn mở.
> **Checkpoint mới nhất:** 21-09-2026, connected-agent worker sau presence inventory và các wave G4-K, G4-J, SecretStore, node-credential DPAPI, schema-22 rotation, Electron owner rotation **và standing-write HTTP→node path** (focused/full local proof cập nhật khoảng 01:08 +07; G4-K, G5 và G2 vẫn chưa đóng live). Schema **22 → 23** bổ sung durable `mcp_standing_patch_intents`; correlation `task_id` + `writer_lease_generation` vẫn được nối xuyên action/intent → node bridge → receipt; đường `exec_run`/`exec_poll`/`exec_stop` đã đi qua policy local → Recovery IPC/Host → `RuntimeOrchestrator` → Coding Tools MCP. `list_account_targets` nay trả thêm `presence_state` (`unknown`/`online`/`offline`) và `heartbeat_age_ms` từ `last_seen_at_ms` với ngưỡng 60 giây; đây là quan sát kết nối độc lập task/context, không cấp quyền mới và không lộ path/secret. Node-agent có `run-connected-agent`: heartbeat/reconnect không phụ thuộc read-only policy; mỗi lane file-read/artifact/approved-patch/exec chỉ poll sau khi standing local policy, capability và workspace generation hiện hành được xác nhận. Supervisor packaged đã gọi command mới; lock/backoff giữ một connected agent và không mở rộng authority. Policy exec, file-read và approved-patch đều có source schema v2 với `authority_mode=standing`, `expires_at_ms=null`; central `agent_workflow.apply_patch` nay có profile standing source, không bắt `permission_request_id`, nhưng vẫn bắt OAuth write scope, binding/task, writer lease, digest, contract và local policy; standing receipt projection đã được sửa để xác minh action arguments có `authority_mode=standing`; policy v1 vẫn được đọc như `expiring_legacy`; action TTL trung tâm vẫn giữ để chống queue replay. Electron enrollment/UI nhận capability workspace `read/write/exec` do chủ máy chọn (mặc định read-only an toàn), `replace-workspace` có confirmation + retire/register theo generation với journal retry-safe, Recovery bridge có fail-closed/typed-failure oracles, OAuth ingress hiện chứng minh task lineage, writer handoff, claim-before-dispatch và giữ lease đến terminal receipt giữa hai token cùng principal dùng chung binding. G4-E bổ sung E2E HTTP OAuth → node heartbeat/poll → local exec journal → accepted/terminal receipt → MCP status/output; G4-F thay bridge hẹp bằng fixture process Recovery/Electron thật cho `exec_run`/`exec_poll`/`exec_stop`, sửa store để `stopped` là terminal receipt và chứng minh stop ACK chỉ sau quiescence; G4-G phát hiện/sửa journal chưa persist đủ `request/result` trước receipt ACK, rồi chứng minh mất ACK sau central accepted không gây spawn lại; G4-H mô phỏng MCP disconnect sau `exec_run`, ghi `unknown/reconcile_required` và chặn mọi retry effect; G4-I mô phỏng terminal receipt ACK loss và replay terminal payload không relay lại Job; G4-J mô phỏng Recovery process crash ngay sau khi MCP nhận `exec_run`, phân loại `unknown/reconcile_required`, restart process thật và chứng minh không redeliver; G4-K mô phỏng Job `running` qua Recovery restart và terminal result mất trước bridge ACK, đều không tạo `exec_run` thứ hai. Electron SecretStore có focused **5/5 PASS** cho envelope/migration/backup/fail-closed với fake encryption; node-agent có DPAPI envelope source path, legacy plaintext/pending migration và fail-closed fallback với focused **8/8 PASS**; rotation protocol store/agent có **5/5 PASS**, HTTP boundary **1/1 PASS** và Electron enrollment/manager rotation boundary **25/25 PASS**. Chưa có Windows `safeStorage`/DPAPI live, ACL packaged proof, rotation trên máy thật hoặc ChatGPT live.
> **Validation checkpoint:** standing facade/task test + standing HTTP→node patch-to-status E2E **2/2 PASS**; bộ focused Python liên quan store/OAuth/approved-patch/node-agent/task-session **132/132 PASS**; checkpoint mới nhất full control-plane discovery **278/278 PASS** trong **82.054s**, HTTP→node approved-patch **5/5 PASS**, Node approved-patch/Recovery bridge **12/12 PASS**, standing artifact-read **1/1 PASS**, và Node full suite **868 tests: 852 PASS / 16 SKIP / 0 FAIL**; các lane trước đó gồm Node bridge/CJS/runtime **13/13 PASS**, approved-patch regression **9/9 PASS**, Python exec fault-focused **21/21 PASS**, file-read + approved-patch focused **20/20 PASS**, enrollment/manager/rotation **25/25 PASS**, workspace replacement **3/3 PASS**, node-secret protection **8/8 PASS**, node-credential rotation **5/5 PASS**, rotation HTTP **1/1 PASS**, connected-agent lane tests **3/3 PASS**, G4-B writer handoff HTTP **1/1 PASS**, G4-C exec guard HTTP **1/1 PASS**, G4-D terminal handoff **1/1 PASS**, G4-E HTTP→node exec E2E **1/1 PASS**, G4-F/G4-G/G4-H/G4-I/G4-J/G4-K HTTP→Recovery process exec/stop/lost-ACK/disconnect/terminal-ACK/crash-restart/running-restart/terminal-crash/terminal-ACK-restart/stop-pending-restart/writer-job-handoff E2E **11/11 PASS**, `test_exec_node_agent` **21/21 PASS**, `test_mcp_faults` + `test_store` **85/85 PASS**, rerun `test_mcp_exec` **8/8 PASS**, OAuth class **24/24 PASS** (có test `unknown → online → offline`), Electron SecretStore **5/5 PASS**. `py_compile`, `node --check` và `git diff --check` đã chạy lại và PASS; full discovery có `ResourceWarning` về một số SQLite connection chưa đóng nhưng không có test failure. SecretStore/DPAPI proof dùng fake encryption/temp directory hoặc mocked Windows API; chưa chứng minh Windows `safeStorage`/DPAPI live. Đây vẫn là source/focused/full test proof trên working tree, không phải live/package proof.
> **Checkpoint xác nhận lại, 21-09-2026, 01:19 +07:** HTTP approved-patch E2E class **3/3 PASS** (owner-review, standing completed/status, stale local generation bị reject trước bridge và unknown/reconcile không retry); full Python discovery **275/275 PASS** trong **73.574s**. Một `ResourceWarning` SQLite connection chưa đóng vẫn xuất hiện nhưng không làm test fail. Đây là source/focused proof trên working tree; chưa có Windows packaged/live hoặc ChatGPT hai-client thật.
> **Rà soát bằng chứng:** targeted `test_wave_a_runtime.py` vẫn **11/12 PASS**; ca còn lại là lỗi môi trường/harness Linux của standalone Landlock helper (`ImportError` relative import), không phải proof của bridge relay. Chưa có validation Ubuntu live, Windows packaged/live hay ChatGPT thật.
> **Trạng thái:** G0 hoàn tất; G1/G2/G3/G4 đã có source + focused/full test proof trên working tree; standing central `agent_workflow.apply_patch` nay có source + HTTP→node completed-receipt proof; G3-G/G3-H, G4-A, G4-B, G4-C, G4-D, G4-E, G4-F, G4-G, G4-H, G4-I, G4-J và một phần G4-K đã có source/focused proof cho thay capability, fail-closed Recovery boundary, account lineage, writer serialization, chặn exec trước dispatch, giữ lease đến terminal receipt, relay exec qua HTTP/node journal, stop terminal qua Recovery process thật, replay accepted/terminal receipt sau mất ACK, reconcile khi MCP disconnect, crash/restart không redeliver và running Job resume qua process mới. Account inventory và `run-connected-agent` đã có source/focused proof cho heartbeat độc lập policy, reconnect backoff và lane gating; heartbeat/reconnect trên node live vẫn chưa nghiệm thu. Electron SecretStore có source/focused proof cho envelope versioning, migration legacy, backup fallback và fail-closed corruption/unavailable encryption; node-agent có DPAPI active/pending envelope, legacy migration và fail-closed fallback **8/8**; schema-22 node-mediated rotation có source/focused proof cho prepare/activate/ack, dual-auth và retry. Chưa có Windows live/packaged proof, rotation trên máy thật hoặc crash/mất ACK trên exact package. **G3/G4 vẫn chưa hoàn tất sản phẩm**: standing fault/duplicate-effect/reconcile, terminal-crash/duplicate-effect/reconcile đầy đủ trên mọi boundary, writer handoff live trên Job thật, các write paths còn lại, packaged/live proof và read/write/Git/build/test/deploy end-to-end còn mở; G5/G6 packaged/live/soak còn backlog. Tài liệu này là kế hoạch triển khai/đánh giá, không phải xác nhận đã bật full quyền.
> **Giới hạn bằng chứng:** đã đối chiếu code, diff, test-source và receipt trong repo; không kiểm tra máy live, không đọc DB vận hành/ledger để đếm Job, không thay đổi dịch vụ, không commit/push/deploy/restart hoặc gọi provider trả phí.

> **Bổ sung supersede checkpoint 01:08 — 21-09-2026, 01:19 +07:** lớp HTTP→node approved-patch hiện **3/3 PASS**. Ca mới chứng minh policy/workspace-generation stale bị reject trước mutation bridge, file không bị ghi lần hai; ca unknown/reconcile chứng minh status trung thực và không retry effect. Full Python discovery chạy lại **275/275 PASS trong 73.574s**. Các fault standing còn thiếu (stale preimage/path, lost ACK sau completed, duplicate-effect/reconcile) và mọi gate Windows/live vẫn mở.

### Checkpoint mới nhất — standing patch qua Recovery process thật, 21-09-2026, 02:00 +07

Wave này đã chuyển standing approved-patch từ HTTP→node bridge fixture sang
đường process thật hiện có của Desktop:

```text
OAuth cùng principal
  → binding_id/task + writer lease
  → node poll + standing local policy
  → recovery_approved_patch_bridge.cjs
  → RecoveryIpcServer → RecoveryHost
  → RuntimeOrchestrator.controlPlaneApprovedPatch
  → Coding Tools MCP agent_workflow.apply_patch
  → local file + receipt
```

| Hạng mục | Đã tận dụng/thay đổi | Bằng chứng mới | Chưa được suy ra |
| --- | --- | --- | --- |
| Recovery boundary | Dùng lại `RecoveryIpcServer`, `RecoveryHost`, `RuntimeOrchestrator` và `controlPlaneApprovedPatchBridge`; fixture MCP chỉ là peer deterministic | Standing crash-after-effect **1/1 PASS**; file đã đổi nhưng receipt là `unknown/reconcile_required`, restart không gọi `apply_patch` lần hai | Chưa phải Electron packaged/Windows process thật |
| Receipt/replay | Dùng lại approved-patch journal, idempotent `store.record_receipt` và terminal receipt projection | Standing lost-ACK qua process **1/1 PASS**; central `completed`, poll sau replay đúng receipt, chỉ một local patch effect | Chưa chứng minh crash/ACK trên package Windows và mọi Recovery boundary |
| Contract adapter | Standing request giữ `authority_mode`; adapter chuyển đủ `task_id`, `writer_lease_generation`, `run_id`, `wave_id` và postimage metadata để verifier không mất correlation | HTTP→node class **5/5 PASS** (3 ca cũ + 2 process thật); Node approved-patch/Recovery bridge **12/12 PASS** | Chưa đóng parity exec/artifact/document và write paths khác |

**Tận dụng được ngay:** không cần xây lại identity/account, `binding_id`,
workspace registry/generation, writer lease, OAuth ingress, node poller,
approved-patch journal/receipt, Recovery IPC/Host, RuntimeOrchestrator hay
Coding Tools MCP. ChatGPT vẫn là controller; Ubuntu vẫn xác thực/định tuyến;
Windows runtime vẫn giữ file, Git, process và quyền OS local. Các thay đổi mới
chỉ nối đúng correlation và làm rõ standing-mode contract ở ranh giới adapter.

**Mức bằng chứng:** `SOURCE_PRESENT + FOCUSED_TEST_PROOF` trên working tree.
Đã chạy Python approved-patch HTTP→node **5/5 PASS trong 11.771s**, full
control-plane discovery **278/278 PASS trong 82.054s**, Node
approved-patch/Recovery bridge **12/12 PASS**, `node --check` và `py_compile`
PASS. Chưa bật flag Ubuntu live, chưa deploy/restart, chưa gọi provider trả
phí, chưa nghiệm thu Windows DPAPI/ACL/packaged/startup/reconnect/rotation,
hai ChatGPT client thật hoặc T01–T16/soak 24 giờ.

**Next action chính xác:** chạy cùng hai ca trên Windows packaged candidate với
DPAPI/ACL và Recovery process thật; sau đó bổ sung standing parity cho exec,
artifact/document/write paths, nghiệm thu hai client cùng `principal_id` chọn
`binding_id`, rồi chạy T01–T16 và soak tối thiểu 24 giờ.

### Checkpoint clarification — một tài khoản ChatGPT, nhiều máy điều khiển, 21-09-2026, 02:24 +07

Xác nhận mới nhất được chốt thành contract vận hành như sau: **ID sinh ra khi
bind workspace là selector của đích; mọi máy đang đăng nhập cùng một tài khoản
ChatGPT đã được OAuth xác minh đều có thể ra lệnh tới selector đó.** Máy đang
mở ChatGPT chỉ là controller. Máy nào thực sự chứa workspace mới là execution
host và máy đó giữ credential/enrollment riêng của nó.

| Khái niệm | Quy tắc phải giữ | Ý nghĩa thực tế |
| --- | --- | --- |
| Tài khoản ChatGPT | OAuth ánh xạ các client về cùng `principal_id`; client không cần enroll nếu chỉ điều khiển | Máy A, B, C dùng cùng account có thể thấy inventory được chia sẻ và gửi task |
| `binding_id` | ID opaque của `{principal/owner, device_id, endpoint_id, workspace_id, workspace_generation}`; không phải token | Chọn đúng workspace/host; không định tuyến bằng tên máy, raw path hay bare `workspace_id` |
| Task | Pin bất biến `{binding_id, device_id, endpoint_id, workspace_id, workspace_generation}` từ lúc mở | Client đổi máy hoặc session default không làm task đang chạy đổi đích |
| Quyền ghi/chạy | Standing local policy và writer lease ở node; cùng account không bỏ qua fence | Hai client có thể observe; chỉ một writer hợp lệ ghi tại một thời điểm, conflict phải rõ |
| Credential | Node secret/DPAPI/safeStorage chỉ ở máy đã bind; không copy cookie, token, context hay node secret | Đăng ký dùng lâu dài sau reboot/reconnect; không chép token mỗi phiên |
| Offline/retire | `offline`, `revoked`, `retired` và `unknown` là trạng thái khác nhau; không failover âm thầm | Ubuntu báo đúng trạng thái; không chuyển file sang Ubuntu hoặc máy khác nếu chưa chọn binding mới |

Nếu account chỉ có một binding đang hoạt động, client có thể dùng binding đó
làm mặc định của phiên. Nếu có nhiều binding, client phải chọn ID cho từng
task; “mặc định” chỉ là state của client/session, không phải
`active_workspace` toàn tài khoản. Đây là mô hình **một account → nhiều client →
một hoặc nhiều workspace binding**, không phải mô hình mỗi client tự có một
workspace tách rời.

Mức bằng chứng của clarification này hiện là **contract + source/focused
fixture**, chưa phải nghiệm thu hai ChatGPT client thật. Gate tương ứng vẫn là
T01/T04/T06/T16 trên exact Windows package, sau khi đóng DPAPI/ACL, startup,
reconnect, writer/Job và parity read/write/exec.

## 0. Bảng điều hành cập nhật — 21-09-2026, 00:04 +07

### 0.0 Checkpoint mới — standing write HTTP→node path, 21-09-2026, 01:08 +07

Wave này đã chuyển gap quan trọng nhất của contract từ **“chưa có đường
HTTP→node”** sang **“đã có đường source + focused receipt proof, chưa live/package”**:

| Thành phần | Đã tận dụng/thay đổi | Ý nghĩa vận hành | Chưa được suy ra |
| --- | --- | --- | --- |
| OAuth/account | `mcp_oauth.py` giữ principal đã link và thêm cờ `CONTROL_PLANE_MCP_OAUTH_STANDING_WRITE_ENABLED` | Cùng tài khoản ChatGPT dùng chung principal; phải có write scope riêng | Không cho phép account khác, scope thiếu hoặc principal bị revoke |
| Contract MCP | `control-plane-oauth-standing-write-v1`, schema 19; `agent_workflow` công bố `capability_state=standing_write` | Client không phải xin `permission_request_id` cho patch trong standing scope | Không phải quyền shell/arbitrary path và không thay local OS policy |
| Central admission | `mcp_standing_patch_intents` (schema 23), exact path/preimage/patch digest/envelope, binding/task pin, writer lease/generation và idempotency | Retry cùng key/payload replay cùng action; task khác cùng binding bị conflict | Queue thành công chưa phải file đã ghi; action TTL vẫn chống replay |
| Node/local | Reuse approved-patch bridge, schema policy v2 `authority_mode=standing`, workspace registry/generation và Recovery/runtime | Node là nơi kiểm preimage, allowlist, local capability/OS và thực thi | Chưa chứng minh Windows package/live hoặc file write thật sau HTTP |

**Focused proof mới:** facade test +
`test_oauth_standing_write_to_node_patch_to_verified_status` **2/2 PASS**
(tools/list, không có `permission_request_id`, writer claim, node poll, local
standing policy, completed receipt và status projection). Full Python discovery
sau test là **275/275 PASS** trong **74.130s**; một số `ResourceWarning` SQLite
vẫn là hygiene backlog. Đây là `SOURCE_PRESENT + FOCUSED_TEST_PROOF` trên
working tree, không phải Windows packaged/live hay ChatGPT client thật.

**Cách hiểu đúng với nhiều máy cùng một tài khoản:** `binding_id` là selector
để chọn host/workspace; nó không phải token. Mỗi task vẫn giữ bất biến
`{binding_id, device_id, endpoint_id, workspace_id, workspace_generation}`.
Hai client cùng principal có thể observe cùng inventory/task, nhưng writer
lease chỉ cho một task ghi tại một binding; client thứ hai không được tự ghi
đè. Nếu H1 offline, Ubuntu báo `offline/unknown`, không tự chuyển file sang
Ubuntu hay failover sang H2.

**Next action chính xác:** (1) thêm standing fault path để chứng minh receipt
unknown, preimage/path/generation/policy mismatch và lost-ACK không tạo effect
thứ hai; (2) bổ sung standing
parity cho exec/artifact/document/write paths được công bố; (3) chạy exact
Windows packaged DPAPI/ACL/startup/reconnect/rotation; (4) nghiệm thu hai
ChatGPT client cùng principal với hai binding và target/generation fence; (5)
chạy T01–T16 rồi soak tối thiểu 24 giờ. Chưa mở cờ này trên Ubuntu live trong
lượt tài liệu.

### Kết luận vận hành hiện tại

**Đích sản phẩm đã chốt:** một tài khoản ChatGPT dùng chung có thể điều khiển
nhiều máy đã đăng ký. Mỗi lần bind workspace tạo một `binding_id`; client chỉ
cần xác thực cùng `principal_id`, chọn ID, rồi Ubuntu định tuyến tới đúng
`device_id/endpoint_id/workspace_id/workspace_generation`. File, Git, process,
build và test vẫn chạy trên máy giữ workspace, theo quyền OS/local policy của
máy đó. Client đang mở ChatGPT không tự trở thành execution host.

**Tình hình code hiện tại:** dự án đã có phần lớn nền tảng cần thiết và không
cần xây lại identity, runtime executor hay một AI controller trung tâm mới.
Các mảnh có thể dùng ngay là OAuth/account inventory, registry và binding,
enrollment/credential theo node, task ID/idempotency, writer lease/generation,
queue/receipt, Coding Tools MCP, Recovery/RuntimeOrchestrator, Job/RUN/WAVE
ledger, package/backup verifier và các fixture fault/recovery hiện có.

**Bằng chứng mạnh nhất:** working tree hiện đã có `SOURCE_PRESENT` +
`FOCUSED_TEST_PROOF`; full Python control-plane **275/275 PASS**, OAuth class
**24/24 PASS** với presence `unknown → online → offline`, full Node
**868 tests: 852 PASS / 16 SKIP / 0 FAIL**, HTTP→Recovery process **11/11
PASS**, node-secret protection **8/8 PASS**, credential rotation **5/5 PASS**
và rotation HTTP **1/1 PASS**. Đây là bằng chứng source/fixture local, không
phải xác nhận package/live.

### Gate còn mở trước khi gọi là hoàn tất

1. Chạy exact Windows packaged/installed build với DPAPI/`safeStorage` thật,
   ACL, legacy migration, restart/reconnect và rotation crash/mất ACK.
2. Đóng duplicate-effect/reconcile còn lại trên Recovery/MCP/Job thật; giữ
   writer lease tới terminal receipt và kiểm tra stop/handoff khi effect chưa rõ.
3. Đã có standing patch admission và HTTP→node→Recovery-process proof ở source;
   bước tiếp theo là nối parity cho các write/exec/artifact path còn lại, rồi chạy
   đọc/sửa nhiều file, Git, build/test và deploy trong workspace fixture. Không
   biến local permission thành quyền Administrator.
4. Dùng hai ChatGPT client thật cùng principal trên exact connection để kiểm
   `binding_id`, đổi client quan sát/tiếp tục, target/generation fence và
   reconnect sau Ubuntu/node/UI restart.
5. Chốt startup scope (sau user logon hoặc pre-login), chạy T01–T16 trên đúng
   candidate cuối, rồi soak liên tục ít nhất 24 giờ. Chưa được gọi là
   production/full authority trước các gate này.

### Trạng thái Git và phạm vi lượt cập nhật

Branch vẫn là `codex/control-plane-quarantine`, HEAD
`502ffb8cf8b541ee74af30194aff2dce08c3b649`; worktree có dirty source/test,
docs và `.coding-tools` evidence từ các wave trước. Lượt này chỉ cập nhật tài
liệu; không commit, push, deploy, restart service, đổi credential hay gọi
provider trả phí. Các receipt lịch sử vẫn giữ nguyên ngày và không được dùng
thay cho live proof.

## 1. Kết luận ngắn: dự án đang ở đâu, tận dụng được gì?

**Không bắt đầu lại từ đầu.** Dự án đã có backend Ubuntu, đăng ký máy/credential,
registry workspace, binding theo tài khoản, task ID bền vững, queue/receipt,
runtime local và Recovery Supervisor. Receipt lịch sử đã ghi nhận Ubuntu triển
khai schema 19 và chuyển action tới đúng node Windows.

**Chưa đủ để tuyên bố đã đạt trải nghiệm đích.** `exec_run`, `exec_poll`,
`exec_stop` và resume journal hiện đã có relay source/focused proof qua runtime
local; tuy nhiên policy thường trực, fault/reconcile trên process thật, đổi khóa
chịu mất ACK và nhiều chat cùng điều khiển chưa được đóng live. Chưa có receipt
dùng ChatGPT thật từ hai máy, cùng tài khoản, sửa/build/test xuyên suốt trên
cùng workspace từ xa mà không phải duyệt context/lệnh ở Ubuntu.

Đợt kiểm tra source gần nhất đã xác nhận các mảnh G1/G2/G4 không còn chỉ là kế
hoạch: task-open idempotency, enrollment status/reconcile, schema-21 writer
lease/generation và OAuth `task_control` đã có implementation; fixture và node
admission contract đã được cập nhật để kiểm chứng correlation mới. Đây vẫn là
**source/focused proof**, không phải bằng chứng node
Windows, Ubuntu release, ChatGPT thật hay quyền write/exec đã được bật.

Phần việc chính là **nối và hoàn thiện các thành phần hiện có**, tách đăng ký,
quyền local và vòng đời task; không xây một runtime, hệ thống identity hoặc
controller AI trung tâm khác.

### 1.1 Phạm vi thay thế tài liệu cũ

Tài liệu này là kế hoạch thực hiện hiện hành cho yêu cầu người dùng làm rõ ngày
20-09. Nó thay thế chỉ dẫn đích/phụ thuộc/nghiệm thu mâu thuẫn trong
[kế hoạch Ubuntu central trước đây](UBUNTU_CENTRAL_MCP_COMPLETION_PLAN.md):

- Read-only/context có hạn không còn là giới hạn sản phẩm cuối.
- Ubuntu không thêm bước người duyệt từng patch/lệnh trong quyền local đã cấu hình.
- ChatGPT trên các máy của cùng tài khoản là đường điều khiển chính; không bắt
  xây server AI controller hoặc local inference loop để hoàn thành đường này.
- Gateway gọi model/provider chỉ là nhánh riêng nếu chủ hệ thống yêu cầu ứng
  dụng riêng gọi suy luận qua Ubuntu.

Các receipt có ngày, nghiên cứu và kết quả đo trước đây giữ nguyên giá trị lịch
sử, không bị viết lại thành bằng chứng cho yêu cầu mới. Thứ tự phân xử sự thật
kỹ thuật vẫn theo [CURRENT_STATE](CURRENT_STATE.md) và [AGENTS](../AGENTS.md).
Kế hoạch không tự cấp quyền sửa hệ thống live, gọi provider, push hay release.

### 1.2 Xác nhận mới nhất: một tài khoản, nhiều client, một đích được chọn

Quy tắc cần triển khai và nghiệm thu là:

```text
ChatGPT client A/B/C (cùng principal tài khoản)
        │ OAuth/user identity đã xác minh
        ▼
Ubuntu MCP: inventory → chọn binding_id → kiểm generation/target
        │ dispatch qua endpoint của node đã đăng ký
        ▼
Máy host H1: runtime local → workspace W1 → file/Git/process/build/test
```

- Máy **H1** đăng ký và bind workspace **W1** một lần. `binding_id=B1` là
  selector công khai để ChatGPT trên A, B hoặc C chọn đúng H1/W1; nó không phải
  bearer credential và không chứa raw path/secret.
- A, B và C có thể là các máy chỉ mở ChatGPT, không cần enroll executor. Khi
  cùng principal chọn `B1`, mọi lệnh hợp lệ đều được thực thi ở H1/W1, không
  chạy nhầm trên máy đang mở ChatGPT và không chuyển file sang Ubuntu.
- Nếu H2 đăng ký workspace W2, cùng tài khoản thấy thêm `B2` và chọn đích theo
  từng task. Không có biến `active_workspace` toàn tài khoản làm đổi đích của
  task đang chạy; task đã mở giữ target bất biến.
- Biết `B1` không đủ truy cập: account khác, node key, generation cũ, workspace
  đã retire hoặc local policy đã tắt đều phải bị chặn đúng lý do.
- “Chung tài khoản ChatGPT” chỉ là cùng principal sau OAuth/IdP verification.
  Không copy cookie, user token, node secret hoặc context giữa các máy; refresh
  OAuth là việc của phiên điều khiển, không phải đăng ký lại executor.

Đây là bổ sung vào contract, không phải bằng chứng rằng luồng hai client đã chạy
thành công. Bằng chứng live vẫn phải là T01/T04/T06/T16 trên exact build và
workspace fixture được chỉ định.

### 1.2a Quy tắc chia sẻ account và `binding_id` (chốt theo xác nhận mới nhất)

Diễn giải vận hành ngắn gọn là: **bind một workspace tạo ra một ID; mọi máy
đang đăng nhập cùng một tài khoản ChatGPT đã liên kết đều có thể dùng tài khoản
đó để ra lệnh tới ID này**. Máy mở ChatGPT chỉ là controller, không phải host
thực thi. Nếu tài khoản chỉ có một binding đang hoạt động, client có thể dùng
binding đó làm target mặc định của phiên; nếu có nhiều binding, client phải chọn
`binding_id` cho từng task. “Mặc định” là state của client/phiên, không phải một
biến global làm đổi đích của task đã mở.

Mỗi request trung tâm phải đi theo chuỗi sau:

```text
OAuth token của client
  → verified principal_id (cùng account trên mọi máy)
  → binding_id (opaque selector)
  → {device_id, endpoint_id, workspace_id, workspace_generation}
  → node credential + local capability/policy
  → file/Git/process/build/test tại đúng host
```

- Cùng `principal_id` được phép thấy và dùng những binding đã chia sẻ cho
  account đó; không suy ra quyền từ email, tên máy, raw path hay lời nói trong
  prompt. MCP server phải kiểm tra token theo issuer, audience, expiry và scope
  trước mỗi tool call theo [tài liệu xác thực MCP chính thức của OpenAI](https://developers.openai.com/plugins/build/auth).
- `binding_id` chỉ là selector, không phải bearer credential. Node secret,
  cookie ChatGPT, OAuth access/refresh token và local path không được sao chép
  giữa các máy.
- Nhiều client cùng account có thể cùng observe một task; việc ghi/sửa/tiếp
  quản vẫn qua writer lease, task target bất biến và generation fence. Cùng
  account không có nghĩa là hai controller instance được phép ghi đè nhau.
- Nếu H1/W1 bị retire hoặc thay generation, mọi client cùng account phải thấy
  binding cũ là fenced/revoked và chọn binding generation mới; không tự failover
  sang Ubuntu hay máy khác.

### 1.3 Những gì có thể tận dụng ngay theo đường đi của một công việc

| Bước | Khối hiện có cần giữ | Cách dùng trong contract mới | Không được suy ra |
| --- | --- | --- | --- |
| 1. ChatGPT client | OAuth/introspection và linked principal trong `mcp_oauth.py` | Xác thực cùng account trên A/B/C; client chỉ là controller | Máy mở ChatGPT không tự trở thành host thực thi |
| 2. Chọn đích | `list_account_targets`, registry workspace và `binding_id` trong `store.py` | Inventory trả selector opaque; task pin đúng `{device, endpoint, workspace, generation}` | Biết raw path/workspace ID không đủ quyền |
| 3. Mở task | `create_mcp_task_session`, `mcp_task_open_idempotency` và schema-21 `mcp_task_writer_leases` | Retry cùng key trả cùng `task_id`; task pin target; writer claim/renew/release có generation | Source lease chưa phải runtime Job continuity hay live multi-client proof |
| 4. Node tin cậy | Device identity, enrollment hash/generation, `node_enrollment_status`, `reconcile-enrollment`, node-agent DPAPI envelope + legacy migration, schema-22 node-mediated rotation | Duyệt một lần, reconnect/reload giữ credential và trạng thái; Windows source path không ghi plaintext sau migration; prepare/activate/ack retry-safe ở source | Chưa có Windows packaged/live DPAPI/ACL proof hoặc rotation trên exact máy thật |
| 5. Thực thi tại host | Coding Tools MCP, `runtimeOrchestrator`, Job/RUN/WAVE ledger, resource/writer fences | Central adapter phải gọi đúng runtime hiện hữu cho file/Git/build/test/process | Không dùng `_run_bounded_exec` direct-Popen candidate làm đường sản phẩm cuối |
| 6. Vận hành/recovery | Recovery Host, Supervisor, lock/backoff, receipt/unknown/reconcile, backup/package verifier | Giữ lineage, stop/reconnect/fault evidence và rollback có kiểm soát | Source presence, PID Running hoặc smoke local chưa là live package/soak |

Vì vậy backlog là **kết nối và tách boundary**, không phải viết lại identity,
registry, task ledger hay local runtime. Mỗi bước chỉ được nâng mức bằng chứng
khi có test/receipt đúng loại; source có sẵn không tự biến thành activation.

### 1.3a Standing write đã có central source path; các gate còn lại

Hai lớp quyền vẫn phải tách rõ:

- `node_agent.py` hiểu policy local schema v2 `authority_mode=standing` cho
  `file-read`, `approved-patch` và `exec`; policy này quyết định node có được
  nhận lane hay không.
- `agent_workflow.apply_patch` nay có contract standing riêng. Trong scope đã
  bật, request không cần `permission_request_id` hay owner-review record; central
  vẫn bắt OAuth write scope riêng, `binding_id`, `task_id`, writer
  lease/generation, path tương đối, preimage/patch digest, envelope và facade
  contract. `request_permissions` được giữ cho out-of-scope escalation/legacy,
  không phải bước duyệt lại từng patch trong standing scope.

Implementation hiện có ở mức source: `mcp_standing_patch_intents` (schema 23),
idempotency theo principal/key, task/action linkage, immutable target, action
TTL chống queue replay và redacted lifecycle projection. Test facade chứng minh
tools/list, queue không có `permission_request_id`, replay cùng action và conflict
khi task khác đang giữ writer lease (**1/1 PASS**). HTTP→node fixture hiện đã
chứng minh completed receipt/status, stale local generation bị chặn trước bridge
và unknown/reconcile không retry; lớp mới nhất là **5/5 PASS**, trong đó có hai
ca Recovery-process thật. Mốc **3/3** chỉ là checkpoint cũ.

Central `document_workflow` `doc_create`/`doc_convert` hiện đã có schema 24,
idempotency, task/writer pin và digest-only relay validator ở mức source; đây
chưa phải local file effect. W1 ở trên là phần còn thiếu để biến source path đó
thành capability dùng được tại workspace node.

Chưa gọi là hoàn tất sản phẩm vì cần nối và chứng minh tiếp: path-deny và
terminal-unknown trên standing bridge, duplicate-effect/reconcile xuyên các
boundary còn lại; parity của exec/artifact/document và các write path khác;
Windows packaged/live; hai ChatGPT client thật và soak. Nói cách khác, gap đã
đổi từ “thiếu central implementation” thành “chưa có fault-complete/live
acceptance”.

### 1.4 Tóm tắt để vận hành và quyết định đầu tư

| Có thể tận dụng ngay | Chưa được gọi là hoàn tất | Không nên xây lại lúc này |
| --- | --- | --- |
| OAuth/linked principal, inventory và `binding_id`; enrollment/device identity; task ID/idempotency; writer lease/generation; queue/receipt; standing patch source path; Coding Tools MCP + Recovery/RuntimeOrchestrator; test/ledger/backup/package verifier hiện có | Hai ChatGPT client thật cùng principal; standing fault/reconcile đầy đủ; parity đủ read/write/exec/artifact; Windows packaged/live; file write/Git/build/test/deploy E2E; Recovery crash/duplicate-effect/reconcile đầy đủ; secret-store/rotation chịu mất ACK; soak ≥24 giờ | Hệ thống đăng nhập mới, runtime executor mới, server AI controller cho đường MCP chính, copy context/token mỗi phiên, hoặc failover tự động sang Ubuntu/máy khác |

Thứ tự thực hiện sau checkpoint này là: (1) hoàn tất G4-K cho terminal ACK,
stop-pending và duplicate-effect/reconcile còn lại, kiểm tra writer fence; (2)
nối writer lease vào Job Windows thật, rồi chạy hai-client live; (3) hoàn thiện
secret-store và rotation; (4) chạy write-path/runtime parity; (5) packaged
activation, T01–T16, fault cuối và soak. Nếu chưa có máy/workspace/cửa sổ live
được chỉ định, chỉ làm source/focused proof và không tự deploy.

## 2. Contract sản phẩm đã chốt

**Quyền điều khiển đi theo tài khoản; đích thực thi đi theo ID workspace; file
và process ở đúng máy chứa workspace.**

Ví dụ minh họa: máy A đăng ký workspace `WS-A`. Người dùng mở ChatGPT trên B
hoặc C, sử dụng cùng tài khoản/kết nối dịch vụ đã liên kết, chọn `WS-A` và giao
việc. Ubuntu chuyển yêu cầu về A. Không sao chép workspace sang B/C, không yêu
cầu B/C giữ credential của A, không tự chạy trên Ubuntu khi A offline.

| Vai trò | Trách nhiệm | Không được suy ra |
| --- | --- | --- |
| ChatGPT trên máy điều khiển | Suy luận, gọi tool, đọc kết quả và tiếp tục công việc | Thiết bị đang mở ChatGPT không tự là máy đích |
| Ubuntu | Xác thực tài khoản, registry máy/workspace, resolve đích, dispatch, trạng thái/receipt | Không sở hữu file Windows; không có quyền shell local chỉ vì đã duyệt máy |
| Runtime trên máy đích | Quyền local, file/Git/toolchain, thực thi và quản lý Job/RUN/WAVE | Không vượt quyền OS, tự nâng Administrator hoặc tự chuyển `dangerous` |
| Máy chỉ mở ChatGPT | Giao diện điều khiển bằng tài khoản hợp lệ | Không cần enrollment executor nếu không cung cấp workspace |

Hai luồng cấp quyền độc lập:

1. **Đăng ký máy thực thi:** máy tự sinh credential, Ubuntu duyệt một lần;
   đăng ký tồn tại đến khi thu hồi hoặc thay khóa, không phụ thuộc context.
2. **Liên kết tài khoản điều khiển:** cùng principal đã xác thực có quyền với
   các workspace được chia sẻ cho owner, bất kể máy nào đang mở ChatGPT.

Theo [OpenAI Authentication](https://developers.openai.com/plugins/build/auth),
ChatGPT gắn access token của kết nối OAuth vào yêu cầu MCP và server phải xác
minh issuer, audience, expiry và scope. Vì vậy backend ánh xạ danh tính dịch vụ
đã xác thực; không tin email, `owner_id`, tên máy hay lời khai trong prompt.
“Cùng ChatGPT login” phải được nghiệm thu bằng kết nối thật trên các client,
không được suy thành cùng principal hoặc khả năng đồng bộ connector đã có.

Token có thể cần refresh/đăng nhập lại theo hệ thống xác thực; điều đó không
đồng nghĩa duyệt lại node/workspace hay cấp quyền từng lệnh. Không copy cookie,
operator token hoặc node secret giữa các client. Dự án không cam kết bỏ các
xác nhận do ChatGPT hoặc hệ điều hành tự yêu cầu.

## 3. Hiện trạng và mức bằng chứng

### 3.1 Source hiện tại có gì?

Các hàng dưới đây là **SOURCE_PRESENT / test-source có sẵn**, không phải kết
quả test vừa chạy hoặc bằng chứng các bytes này đang được máy live nạp.
Các symbol được nêu để tra cứu ổn định khi số dòng thay đổi.

| Thành phần | Đã có / tận dụng | Khoảng trống cần hoàn thiện | Nguồn |
| --- | --- | --- | --- |
| Identity cài đặt | Device ID bền vững, không tạo lại mỗi lần mở app | Giữ nguyên qua upgrade/reconnect; không tự tái tạo khi config hỏng | [deviceIdentity.js](../electron/services/deviceIdentity.js), `runtimeDeviceIdentity` |
| Enrollment máy | Secret sinh tại node, lưu trước HTTP; Ubuntu nhận hash và duyệt | UI/reconcile pending → approved bền vững; chống duyệt nhầm thiết bị | [node_agent.py](../control-plane/control_plane/node_agent.py), `request_enrollment`; [store.py](../control-plane/control_plane/store.py), `approve_enrollment` |
| Credential lâu dài | `authenticate_node` kiểm hash/revoked, không có TTL context; Electron `SecretStore` có envelope versioning, legacy migration, temporary+fsync write, `.bak` fallback; node-agent `_write_config` có Windows DPAPI active/pending envelope, legacy migration và fail-closed plaintext fallback. Duyệt một lần, reload/reconnect giữ credential; source path có node-secret protection **8/8**, rotation **5/5**, HTTP **1/1**, Electron SecretStore **5/5** và owner UI/IPC **25/25** | Chưa có Windows packaged/live DPAPI/`safeStorage`/ACL proof, migration trên máy thật hoặc rotation exact-package crash/lost-ACK evidence | [store.py](../control-plane/control_plane/store.py); [node_agent.py](../control-plane/control_plane/node_agent.py), `_config`/`_write_config`/`rotate_node_credential`; [secretStore.js](../electron/services/secretStore.js); [controlPlaneEnrollment.js](../electron/services/controlPlaneEnrollment.js); [tests/secret-store.test.js](../tests/secret-store.test.js); [test_node_secret_protection.py](../control-plane/tests/test_node_secret_protection.py); [test_node_credential_rotation.py](../control-plane/tests/test_node_credential_rotation.py) |
| Thu hồi/rotation | Server có revoke; schema-22 `node_credential_rotations` giữ hash/generation/state; node-agent CLI `rotate-credential` có prepare → activate → promote → ack; Electron owner có confirmation → IPC → parser state/generation | Node tự sinh candidate, giữ credential cũ tới activate, chấp nhận dual-auth tới ack, retry sau mất ACK/crash; legacy one-shot route fail-closed; UI không nhận raw secret | Chưa có Windows packaged/live rotation, DPAPI/ACL/reconnect và fault proof trên máy thật | [store.py](../control-plane/control_plane/store.py), `prepare_node_credential_rotation`, `activate_node_credential_rotation`, `acknowledge_node_credential_rotation`; [node_agent.py](../control-plane/control_plane/node_agent.py), `rotate_node_credential`; [controlPlaneEnrollment.js](../electron/services/controlPlaneEnrollment.js) |
| Registry workspace | Path canonical giữ local; gửi opaque ID/generation/capabilities; có retirement và `replace-workspace` theo generation | Standing local permission bền vững và binding thuận tiện, không thủ tục context hằng ngày | [node_agent.py](../control-plane/control_plane/node_agent.py), `register_workspace`, `retire_workspace`, `replace_workspace` |
| Binding đích | `binding_id` ánh xạ owner/device/endpoint/workspace/generation | Dùng nhất quán làm public selector; không định tuyến bằng raw workspace ID/tên/path | [store.py](../control-plane/control_plane/store.py), `create_binding` |
| Account/OAuth | Introspection, linked principal, owner-scoped inventory độc lập context; `list_account_targets` có presence `unknown/online/offline` + tuổi heartbeat, không lộ path | Chưa có live proof nhiều máy ChatGPT cùng principal điều khiển đầy đủ hoặc heartbeat live | [mcp_oauth.py](../control-plane/control_plane/mcp_oauth.py); [store.py](../control-plane/control_plane/store.py), `list_account_targets` |
| Task session | Task ID durable, pin target; open/list/close; keyed idempotency replay; schema-21 writer lease/generation; generation được lưu ở action/approved-patch/exec intent; redacted observe/claim/release | Generation đã đi vào exec bridge/receipt và fixture Recovery process; chưa chứng minh continuity đến Windows Job live; observe/stop/attach/handoff live giữa hai controller chưa đủ | [store.py](../control-plane/control_plane/store.py), `create_mcp_task_session`, `mcp_task_writer_leases`; [test_mcp_task_sessions.py](../control-plane/tests/test_mcp_task_sessions.py) |
| Root MCP | Đúng tám tên smart-v3; candidate read/patch/exec/stop/artifact | Đủ tên không phải đủ operation; có scope giới hạn/unavailable và feature gates | [mcp_facade.py](../control-plane/control_plane/mcp_facade.py), `tool_contract` |
| Dispatch/receipt | Durable action/attempt, receipt replay, unknown/reconcile; G3-C giữ `command_id`/`job_id`/RUN/WAVE correlation xuyên `run → poll/stop → terminal`; G4-F đã settle `stopped` receipt sau Recovery process thật; G4-G persist running projection trước receipt ACK và replay accepted receipt sau ACK loss; G4-H ghi `unknown/reconcile_required` khi MCP disconnect; G4-I replay terminal receipt sau ACK loss không relay Job | ACK loss ở các boundary khác, duplicate-effect/reconcile đầy đủ và central observe/handoff live chưa đủ | [store.py](../control-plane/control_plane/store.py); journals trong [node_agent.py](../control-plane/control_plane/node_agent.py) |
| Runtime local | File/workflow/exec/Git/document, Job, process control, idempotency, writer fences; G3-A…G gọi `workspace_context` + `exec_command` + `command_control(poll/kill)` qua local MCP; G4-F chứng minh `exec_run`/`poll`/`stop` đi qua Recovery IPC/Host → `RuntimeOrchestrator` → MCP fixture thật | Read/write/exec đầy đủ vẫn chưa được đóng end-to-end; **exec, file-read và approved-patch policy v2 đã standing ở source**, compact read-only/context pilot còn TTL; Windows packaged/live process proof chưa có | [Coding Tools MCP](../resources/coding-tools-mcp/AGENTS.md); [runtimeOrchestrator.js](../electron/services/runtimeOrchestrator.js) |
| Recovery bridge | Actor/identity/contract checks; `runtime.control_plane_exec` đã có RPC allowlist, Recovery handler và descriptor-hiding CJS bridge | Chưa có packaged/live proof; cần giữ fail-closed khi runtime identity/contract/workspace/generation mismatch | [recoveryHost.js](../electron/services/recoveryHost.js); [recoveryIpc.js](../electron/services/recoveryIpc.js); [recovery_exec_bridge.cjs](../control-plane/control_plane/recovery_exec_bridge.cjs) |
| Exec candidate | Structured `argv`, local policy v2 standing, journal `prepared`/`running`, receipt `command_id`/`job_id`; node poller đã gọi Recovery bridge cho `run`, `poll`, `stop`; direct-Popen chỉ còn source compatibility/focused-test helper; G4-F có process fixture thật và terminal `stopped` receipt; G4-G có lost-ACK accepted-receipt replay không respawn; G4-H có MCP disconnect → unknown/reconcile không retry; G4-I có terminal receipt replay không relay | Fault proof duplicate-effect/reconcile sau các Recovery boundary khác, stop quiescence sau timeout/network loss trên exact packaged process, rotation/reconcile | [node_agent.py](../control-plane/control_plane/node_agent.py); [test_exec_node_agent.py](../control-plane/tests/test_exec_node_agent.py); [test_mcp_exec_http_node_e2e.py](../control-plane/tests/test_mcp_exec_http_node_e2e.py) |
| Structured argv runtime | Public `argv` bounded chỉ cho bridge đã attestation; `exec_tools.py` vẫn giữ resource governance và `shell=False`; bridge/runtime focused **11/11 PASS** | Chưa chứng minh packaged/live qua Recovery → MCP trên máy thật; không lách `_continuation_internal`, không join argv thành shell string | [exec_tools.py](../resources/coding-tools-mcp/coding_tools_mcp/exec_tools.py), [tool_schema.py](../resources/coding-tools-mcp/coding_tools_mcp/tool_schema.py), [tests/control-plane-exec-runtime.test.js](../tests/control-plane-exec-runtime.test.js) |
| Agent/Supervisor | Có lock/backoff, integrity manifest, khởi chạy same-user `run-connected-agent`; heartbeat độc lập read-only policy; account inventory đã phân loại presence theo heartbeat; lane gating cho file-read/artifact/approved-patch/exec | Reconnect/heartbeat trên node live, revoked/offline reconciliation và startup scope vẫn chưa nghiệm thu; local policy/OS authority chưa phải packaged/live proof | [recovery-supervisor.ps1](../resources/recovery-supervisor/recovery-supervisor.ps1); [node_agent.py](../control-plane/control_plane/node_agent.py), `run_connected_agent`; [store.py](../control-plane/control_plane/store.py), `list_account_targets` |
| Startup Windows | Scheduled Task AtLogOn, Interactive, Limited | Không chứng minh chạy trước login sau cold boot; cần quyết định scope riêng | [recovery-supervisor.ps1](../resources/recovery-supervisor/recovery-supervisor.ps1), `Install-Supervisor` |
| Backup/release/recovery | SQLite backup/inspect/restore-candidate, package verifier, admission recovery, healthcheck | Tái dùng khi migration; proof package/live/soak vẫn riêng | [Recovery runbook](CONTROL_PLANE_RECOVERY_RUNBOOK.md); [maintenance.py](../control-plane/control_plane/maintenance.py); [deployment_verifier.py](../control-plane/control_plane/deployment_verifier.py) |

Permission local hiện hành thuộc Python Coding Tools với các mode
`safe/trusted/dangerous`; không áp máy móc `WEBCODEX_AUTHORITY_MODE=trusted_agent`
của subsystem Rust. Duyệt máy không tự chọn `dangerous`; giữ chính sách secret,
filesystem, process và quyền OS đang có.

### 3.2 Các sửa đổi chưa commit phải bảo toàn

Trước lượt tài liệu, worktree đã có sửa đổi ở control-plane, Electron/renderer,
tests và packaged/installed smoke, cùng `.coding-tools/orchestration/ledger.sqlite3`;
có hai test smoke mới và `var/` chưa track. Không reset, ghi đè hoặc đưa chúng
vào một commit tài liệu ngoài ý người dùng.

Phần có thể tận dụng ngay là UI bỏ nhập `ctx_…`, lookup assignment theo workspace
và generation, cùng các primitive G1/G2/G4 vừa được kiểm chứng sau wave schema
21:
`binding_id`/task target bất biến, bảng replay `mcp_task_open_idempotency`,
enrollment ID/status, reconcile sau reload/mất mạng, schema-21 writer lease và
route node-authenticated không lộ secret. Wave mới đã đặt generation vào action
digest, approved-patch/exec bridge request và receipt; fixture cũ đã được migrate
để giữ fail-closed khi correlation thiếu.
Wave G3-A/G3-B/G3-C/G3-D/G3-E/G3-F/G3-G/G3-H còn có thể tận dụng trực tiếp: policy exec local tách
khỏi compact read-only/context pilot; policy v2 của exec, file-read và
approved-patch dùng `authority_mode=standing` và `expires_at_ms=null`; registry workspace local giữ canonical path; Recovery IPC
che descriptor/credential; `RuntimeOrchestrator` gọi `workspace_context` rồi
`exec_command` bằng structured `argv`, gọi `command_control` cho poll/stop; node
journal giữ `prepared`/`running` cùng receipt Job/RUN/WAVE.
Các guard target/device/endpoint/workspace/generation/contract/attestation vẫn
được kiểm tra trước effect. G3-G đã bổ sung luồng thay capability tường minh cho
root đã đăng ký: giữ `workspace_id`, tạo generation mới, retire generation cũ ở
Ubuntu trước, vô hiệu policy local cũ rồi register generation mới; journal local
chỉ chứa phase/ID, không chứa secret. Retry sau mất ACK hoặc crash tiếp tục đúng
phase và không retire/register trùng. UI cảnh báo binding/task generation cũ bị
fence và phải bind lại. Đây là migration proof ở node/Electron fixture, chưa phải
live Ubuntu/Windows proof.
Tuy nhiên `assigned_read_only_policy_context` và policy exec legacy v1 vẫn là
đường tương thích có hạn; **ẩn context khỏi UI, relay `exec_run`/`poll`/`stop` và
thay capability có journal không phải tự động là proof trusted workspace lâu
dài**. Exec, file-read, approved-patch và replacement hiện có source/focused
proof; G3-H mới thêm oracle fail-closed cho installation mismatch và typed IPC
failure, còn G4-F đã gọi Recovery process fixture thật cho exec/stop nhưng chưa
chạy exact packaged/live process. Các write path khác, rotation, protected
secret store, fault/reconcile sau lost ACK trên process thật và live multi-client
proof vẫn là backlog. Các sửa đổi
file/exec handling, smoke và test đi kèm vẫn là candidate cần review/proof của
đúng bytes.

Không gắn kết quả pytest lịch sử cho working tree này chỉ vì cùng nhánh hoặc
có cùng số phiên bản. HEAD cũng chưa chứa các sửa đổi kể trên.

### 3.3 Những gì đã từng được ghi nhận vận hành

Nguồn: các mục “Receipt” ngày 19–20/09 trong
[kế hoạch central cũ](UBUNTU_CENTRAL_MCP_COMPLETION_PLAN.md).
Đây là **receipt lịch sử trong repo, chưa xác minh live lại ở lượt này**.

| Mốc | Đã ghi nhận | Không được suy ra |
| --- | --- | --- |
| 19-09, release/migration | Artifact schema 19 verify; migration 10 → 19 được thử trên bản sao | Không tự là live migration hay node execution |
| 19-09, Ubuntu rollout `528035f` | Service active, schema 19, integrity/fingerprint khớp, giữ dữ liệu; lỗi env-file đè revision/hash đã được sửa trong receipt | Không chứng minh runtime Windows hay tài khoản ChatGPT end-to-end |
| 19-09, Tunnel | Active/đăng ký được, nhưng readyz 503 do pilot grant/context hết hạn và MCP Forbidden | Không gọi Tunnel fully ready; strict discovery/OAuth vẫn cần bằng chứng |
| 19-09, DaoChienThang canary | Verify release, heartbeat, đăng ký workspace và dispatch đúng node | `runtime_lifecycle_missing` chặn lane; chưa có read/patch/exec effect proof |
| 19-09, app Windows | Unpacked app chạy, Recovery Host/UI kết nối, identity đúng | Builder/sign lỗi; strict_ready false; chưa phải NSIS release hoàn tất |
| 20-09, Windows proof | Receipt ghi pytest `1153 passed, 5 skipped`, exit 0 | Không phải test vừa chạy, không bảo đảm package/activation hoặc dirty source hôm nay |
| 20-09, receipt cuối | Owner acceptance; closure `bc1e3e84` ACTIVATABLE; PATH/Git ownership/census được xử lý | Activation intent còn `awaiting/pending`; bước kế tiếp ghi là restart UI rồi execution canary, chưa có receipt hoàn tất |

Không dùng snapshot schema 8/admission recovery trong
[status ngày 15–16/09](CONTROL_PLANE_IMPLEMENTATION_STATUS.md) làm trạng thái
ngày 20/09. Cũng không lấy các receipt của một lane nói heartbeat độc lập task
để phủ nhận việc supervisor/default agent trong source vẫn policy-gated.

Lượt này không đọc canonical ledger, task-state, performance hay DB central để
đếm Job live; **trạng thái Job/process hiện tại trên các máy là chưa khảo sát**.
Trước rollout, đọc bằng phương pháp an toàn các nguồn liên quan: ledger local
là causal authority của RUN/WAVE/Job, DB central/journal cho delivery, process
receipt cho activation. Không copy/merge chúng thành ledger thứ hai, không sửa
evidence để làm báo cáo sạch.

### 3.4 Bảng trạng thái hiện tại theo mức bằng chứng

Bảng này là cách đọc ngắn gọn nhất về “đã làm đến đâu”. `SOURCE_PRESENT` chỉ
cho biết code/interface tồn tại; `TEST_SOURCE` chỉ cho biết test đã có trong
repo; `HISTORICAL_RECEIPT` là kết quả cũ được ghi lại; `LIVE_UNVERIFIED` chưa
được kiểm tra lại ở lượt cập nhật này.

| Hạng mục | Mức hiện tại | Có thể tận dụng ngay | Việc còn thiếu để gọi là đạt |
| --- | --- | --- | --- |
| Contract account → binding → host | `DOCUMENTED` | §1.2, `binding_id`, task immutable target | T01/T03/T04/T16 với hai client thật |
| Ubuntu central registry/auth | `SOURCE_PRESENT` + receipt lịch sử | OAuth verification, node registry, workspace/binding, dispatch/receipt | Recheck live exact release, route/generation và failure cases |
| Enrollment/credential theo node | `IMPLEMENTED_SOURCE` + `FOCUSED_TEST` (Electron SecretStore **5/5**, node-agent DPAPI/migration **8/8**, rotation **5/5**, HTTP **1/1**, Electron owner boundary **25/25**; mocked/local only) | Device identity, enrollment approval, hash/generation, revoke, durable `enrollment_id`/state, node-authenticated reconcile, protected source persistence, legacy migration, staged rotation và dual-auth, owner-confirmed IPC/UI | Windows packaged/live `safeStorage`/DPAPI + ACL proof, migration trên máy thật, rotation exact-package crash/mất ACK và live restart/rotation evidence |
| Account inventory/task session | `IMPLEMENTED_SOURCE` + `FOCUSED_TEST` (presence **1/1**, OAuth class **24/24**) | `list_account_targets` với selector + `presence_state`, task open/list/close, owner scope, keyed task replay table, redacted `task_control` observe/claim/release | Live cross-client observe/stop, attach/handoff trên ChatGPT thật, heartbeat/reconnect live và runtime Job proof |
| Runtime local | `IMPLEMENTED_SOURCE` + `FOCUSED_TEST` (exec/file-read/standing artifact-read/approved-patch bridge; G4-F/G4-J/G4-K Recovery process fixtures; live chưa xác minh) | Coding Tools MCP, Job/RUN/WAVE ledger, process/file/Git/build/test, Recovery Host; standing document read dùng allowlist/generation/receipt với `test_file_read_node_agent` **10/10** | Central adapter đầy đủ read/write/exec/document create; không dùng direct-Popen candidate; packaged/live proof |
| Local permission | `PARTIAL` (capability picker + replacement migration Electron/node; exec/file-read/approved-patch standing v2 ở source; artifact đọc dùng standing file-read policy; central standing patch source schema 23; compact read-only/context pilot còn TTL) | Mode `safe/trusted/dangerous`, resource/secret/process governance, chủ máy chọn hoặc thay `read/write/exec` một lần theo root; HTTP→node standing completed/status, stale-preimage/path-deny/terminal-unknown, lost-ACK replay và generation fence đã có fixture **5/5**; standing artifact read **1/1**; SecretStore local fail-closed đã có focused proof | Standing duplicate-effect/reconcile trên các boundary còn lại, nối standing scope vào exec/artifact/document-create/write paths còn lại, local escalation rõ ràng, protected Windows secret store/DPAPI, rotation và live proof |
| Presence/reconnect | `IMPLEMENTED_SOURCE` + `FOCUSED_TEST` / `LIVE_UNVERIFIED` (inventory **1/1**, connected-agent **3/3**, trạng thái `unknown → online → offline`) | `presence_state`, `heartbeat_age_ms`, `run-connected-agent`, Supervisor, lock/backoff và route evidence; presence không cấp task authority | Heartbeat/reconnect trên node packaged/live, revoked/offline reconciliation và startup scope; agent không phụ thuộc TTL read-only context |
| Multi-client same-account | `IMPLEMENTED_SOURCE` + `FOCUSED_TEST` / `LIVE_UNVERIFIED` (OAuth class **24/24**, HTTP→Recovery process **11/11**, gồm lineage, handoff/exec guard, terminal fence, crash/restart và writer-job fence) | Binding/account scope, `mcp_task_writer_leases`, per-task generation, release/expiry handoff, claim-before-dispatch, terminal receipt fence, `task_control` | Hai ChatGPT client thật cùng principal trên exact connection; duplicate effect, stop/handoff live |
| Windows package/startup | `HISTORICAL_RECEIPT` / `LIVE_UNVERIFIED` | Unpacked app, smoke scripts, scheduled AtLogOn path; replacement UI source proof | Exact packaged/installed build, activation/re-discovery, startup scope đã chọn |
| End-to-end/soak | `NOT_PROVEN` | Ma trận T01–T16 và receipt lịch sử làm checklist | T16 trên final build, fault cuối rồi soak liên tục ≥24 giờ |

Vì vậy trạng thái hiện tại nên báo là **“nền tảng và nhiều mảnh ghép đã có,
contract mới đã được chốt ở tài liệu, G1/G2 đã có source/focused proof, nhưng
chưa hoàn thiện trusted workspace đa-client end-to-end”**. Không báo “đã
production”, “đã full quyền” hoặc “đã chạy được trên mọi máy” dựa trên bảng này.

**Focused/full validation của working tree hiện tại (21-09, sau presence inventory và các wave G4-K, SecretStore, rotation):**

**Checkpoint hiện hành cần dùng để đọc trạng thái:** approved-patch
HTTP→node **5/5 PASS trong 11.771s**, bao gồm hai ca đi qua Recovery process
fixture thật (crash sau effect thành `unknown/reconcile_required`, và central
completed mất ACK được replay mà không tạo patch lần hai); full Python control
plane discovery **278/278 PASS trong 82.054s**; Node approved-patch/Recovery
bridge **12/12 PASS**; `node --check`, `py_compile` và `git diff --check`
**PASS**. Full discovery vẫn có `ResourceWarning` về một số SQLite connection
chưa đóng nhưng không có test failure. Đây là `SOURCE_PRESENT +
FOCUSED_TEST_PROOF` trên working tree, chưa phải Windows packaged/live,
Ubuntu live activation hay nghiệm thu hai ChatGPT client thật.

**Parity checkpoint mới — standing artifact/document read, 21-09-2026,
02:18 +07:** `poll_artifact_once` đã được kiểm chứng với policy file-read
schema v2 `authority_mode=standing`, `expires_at_ms=null`, đúng workspace
generation và allowlist. Fixture nhận `document_workflow` artifact action,
đọc UTF-8 tại node và gửi một completed receipt có content digest; không có
context TTL hoặc per-read approval nào được dùng. Focused test mới
`test_standing_artifact_read_uses_the_same_local_policy_without_ttl` **1/1
PASS**; toàn bộ `test_file_read_node_agent.py` **10/10 PASS**. Đây là proof
node/source local, chưa phải Recovery-process document bridge, document create,
Windows packaged/live hay hai ChatGPT client thật.

- Mốc trước standing Recovery process: sau presence inventory patch,
  `PYTHONPATH=control-plane python3 -m unittest discover -s control-plane/tests
  -p 'test_*.py' -q` chạy **274/274 PASS** trong khoảng **71.653s**; riêng
  `test_mcp_oauth.py` **24/24 PASS**, bao gồm `unknown → online → offline`.
  Mốc này đã được supersede bởi checkpoint **278/278** ở trên; warning SQLite
  vẫn là hygiene backlog, không phải bằng chứng live/package.

- Mốc xanh ngay trước wave schema 21 là full control-plane **223/223 PASS** và
  Node **24/24 PASS**; mốc này đã được supersede vì source contract đã thêm
  correlation bắt buộc.
- Validation control-plane trước G4-F: `PYTHONPATH=control-plane python3 -m
  unittest discover -s control-plane/tests -p 'test_*.py' -q` chạy **244/244
  PASS**. Sau G4-F/G4-G, các lane bị ảnh hưởng trực tiếp được chạy lại:
  `test_store` **80/80 PASS**, `test_mcp_exec` **8/8 PASS**,
  `test_mcp_faults` + `test_store` **85/85 PASS**, `test_exec_node_agent`
  **20/20 PASS** và HTTP→node/Recovery exec-stop-lost-ACK-disconnect E2E
  **5/5 PASS**. Các mốc này là chronology của các wave trước; dùng
  checkpoint **278/278 + 5/5 + 12/12 + standing artifact-read 1/1** ở trên làm oracle hiện hành.
  File-read/approved-patch/exec node-agent, workspace
  replacement, shared-account OAuth two-client, writer handoff/exec guard qua
  HTTP và HTTP→node file-read/approved-patch e2e đều xanh. G4-F/G4-G/G4-H/G4-I không được
  suy ra thành packaged/live Windows proof.
- Node full:
  `node --test --test-concurrency=4 tests/*.test.js` chạy **868 tests: 852
  PASS, 16 SKIP, 0 FAIL**. Trong đó bridge/runtime, enrollment/manager,
  Electron credential-rotation boundary, replacement UI contract và SecretStore
  lanes đều PASS. Mốc 867/851 ở các đoạn chronology phía dưới là kết quả trước
  khi thêm Electron rotation boundary, không phải kết quả mới nhất.
- SecretStore focused:
  `node --check electron/services/secretStore.js` và
  `node --test tests/secret-store.test.js` **5/5 PASS**. Test chứng minh
  envelope schema, legacy migration, backup fallback, fail-closed khi hai bản
  hỏng hoặc encryption unavailable, mode `0600` trên POSIX và dọn temp file;
  fake encryption không thay cho Windows `safeStorage`/DPAPI.
- Node-agent credential focused:
  `PYTHONPATH=control-plane python3 -m unittest -v
  control-plane.tests.test_node_secret_protection` **6/6 PASS**. Test chứng minh
  Windows config source chỉ ghi `node_secret_dpapi`, giải mã chỉ trong memory,
  từ chối plaintext + protected đồng thời, không fallback plaintext khi DPAPI
  unavailable, migrate config legacy ở lần đọc đầu tiên và vẫn đọc fixture legacy
  trên non-Windows. Windows API được mock; đây chưa phải DPAPI live, ACL thật,
  packaged migration hay rotation crash/mất ACK.
- Node-mediated credential rotation focused:
  [`test_node_credential_rotation.py`](../control-plane/tests/test_node_credential_rotation.py)
  **5/5 PASS** và HTTP rotation boundary trong `test_http_api.py` **1/1 PASS**.
  Proof bao phủ schema-22 prepare idempotency, dual-auth sau activate, old-key
  retirement chỉ sau ack, conflict rotation thứ hai, node resume từ promoted
  config và fail-closed legacy one-shot route. Đây vẫn là local source/fixture
  proof; Electron owner UI/IPC source boundary đã có focused **25/25 PASS**,
  nhưng chưa phải Windows packaged/live hoặc operator UI chạy trên máy thật.
- Node focused (mốc trước full suite):
  `node --test tests/control-plane-approved-patch-bridge.test.js
  tests/control-plane-approved-patch-runtime.test.js
  tests/control-plane-enrollment.test.js tests/control-center-manager.test.js`
  đã được re-run sau fixture migration và **25/25 PASS**; test node-agent
  replacement riêng **3/3 PASS**; full suite là oracle hiện hành.
- `py_compile` cho `store.py`, `node_agent.py`, `http_api.py`, `mcp_facade.py`
  và `git diff --check`: **PASS**; fixture process `stderr` đã được đóng trong
  teardown nên lane G4-F không còn `ResourceWarning` của pipe.
- Validation riêng sau G3-H: Node bridge/CJS/runtime **13/13 PASS**; approved-patch
  bridge/runtime regression **9/9 PASS**; Python file-read + approved-patch
  focused **20/20 PASS**; Python exec fault-focused **20/20 PASS**; Python
  `test_mcp_exec` + `test_mcp_oauth` + `test_http_api` lần lượt
  **8/8 + 23/23 + 41/41 = 72/72 PASS**. Riêng G4-B writer handoff, G4-C
  exec guard qua OAuth HTTP ingress và G4-D terminal fence lần lượt
  **1/1 + 1/1 + 1/1 PASS**. `node --check` cho các module Electron
  liên quan, `py_compile` và `git diff --check` cũng **PASS**.
- `npm run test:mcp` vẫn chưa chạy được trong shell này vì entrypoint dùng
  `python` và môi trường không có `pytest`; control-plane discovery bằng
  `python3` đã chạy đủ **244/244**. Lượt full discovery có một số
  `ResourceWarning` về connection SQLite chưa đóng nhưng exit code **0** và
  không có test failure; đây là hygiene warning cần xử lý riêng, không được
  nâng mức live evidence.

Các con số hiện tại chứng minh source/test local đã xanh sau migration,
`exec_run → poll/stop → terminal` bridge có focused proof, trong đó stop đã đi
qua Recovery IPC/Host và process fixture thật; exec, file-read và approved-patch
policy v2 standing có regression proof; G4-G còn chứng minh accepted receipt
ACK loss được replay từ journal mà không respawn, G4-H biến MCP disconnect
thành `unknown/reconcile_required` mà không retry effect, và G4-I replay
terminal receipt mà không relay Job. Chúng
không nâng các hàng `LIVE_UNVERIFIED`,
`HISTORICAL_RECEIPT` hoặc `NOT_PROVEN` thành PASS; đặc biệt chưa có ChatGPT thật
trên hai máy, Ubuntu live schema 21, Windows packaged exact build, controller
crash/mất ACK trên runtime thật, các write path còn lại, rotation crash,
deployment hay soak 24 giờ. G4-E đã đóng **source/focused** đường HTTP
`exec_run` → node `poll_exec_once` → local journal → terminal receipt → MCP
status/output; G4-F nối tiếp đường này bằng Recovery/RuntimeOrchestrator
process fixture thật cho run/poll/stop, G4-G thêm ACK-loss replay, G4-H thêm
MCP disconnect → unknown/reconcile và G4-I thêm terminal ACK replay.
**Packaged/live Windows,
duplicate-effect/reconcile đầy đủ vẫn còn mở**.

## 4. Quyết định KEEP / MODIFY / ADD / DEFER

| Xử lý | Thành phần / quyết định |
| --- | --- |
| KEEP | Python central + SQLite; credential riêng theo node; linked account; workspace registry/binding; action/attempt/receipt; runtime MCP/Recovery/Job/ledger hiện có; backup và package verifier |
| MODIFY | Onboarding bền vững; status độc lập quyền; policy local dài hạn; task-open idempotency; binding lifecycle; adapter đầy đủ; writer ownership qua nhiều chat; rotation; UI và startup |
| ADD tối thiểu | Node self-status/reconcile an toàn; chuyển khóa có phục hồi; contract structured process hợp lệ; các oracle multi-client/fault/reconnect còn thiếu |
| BỎ KHỎI ĐƯỜNG CHÍNH | Copy token/context mỗi phiên; Ubuntu human approval từng action trong policy local; yêu cầu có server AI controller mới được coi là hoàn thành |
| DEFER | Model gateway/app AI riêng; nhiều provider; IAM đa-tenant; HA; tự failover workspace sang máy khác; hỗ trợ OS chưa có package/proof |

Không xóa evidence/receipt hay vô hiệu guard cũ bằng đổi nhãn. Candidate pilot
chỉ được chuyển sau migration rõ ràng; không kéo TTL thành cực lớn rồi gọi đó
là tách identity khỏi authority.

## 5. Contract đích: ID, quyền và trạng thái

### 5.1 ID workspace và task

- Public selector tái dùng **`binding_id`**; UI có thể ghi “ID workspace”. Không
  tạo thêm ID ngang hàng hoặc coi bare `workspace_id` là duy nhất toàn fleet.
- Binding resolve exact `{owner, device, endpoint, workspace, generation}`;
  node mới biết absolute path. ID không phải bearer credential.
- Binding còn hiệu lực không hết chỉ vì context/task hết hạn. Bind cùng tuple
  bằng retry phải trả cùng binding hoặc xử lý trùng rõ ràng, không tạo danh
  sách đích trùng gây chọn nhầm. Thay root/generation phải vô hiệu đích cũ.
- `task_open` cần key idempotent; task giữ nguyên đích trong suốt đời nó.
- Cùng principal từ máy khác có thể list/observe/stop task trong scope; tiếp
  quản writer dùng attach/handoff có fence, không mặc định cùng account là
  cùng controller instance.
- Không có global `active_workspace` của toàn account/server. Chat mới có thể
  chọn workspace khác mà không đổi task đang chạy.

### 5.2 Quyền thường trực và phiên tạm thời

- Enrollment cấp quyền dùng dịch vụ cho node, không tự cấp file/exec local.
- Chủ máy cấu hình phạm vi workspace và quyền local một lần; giữ tới khi chủ
  máy đổi/thu hồi, trừ khi họ chủ động chọn thời hạn.
- Trong quyền đó, lệnh hợp lệ tự thực thi sau kiểm tra máy/root/schema/OS; không
  tạo yêu cầu người Ubuntu duyệt context, patch hay từng command.
- Ngoài quyền đó, local runtime từ chối hoặc dùng local escalation đã cấu hình;
  Ubuntu không được tự nâng quyền để “sửa kết nối”.
- Context/lease/deadline là cơ chế nội bộ có thể tái lập tự động dưới authority
  hiện hành; task đã đóng/revoked không được âm thầm sống lại. Task mới không
  yêu cầu pairing lại; task còn hợp lệ tiếp tục theo contract local.
- Push/publish/release/deploy vẫn cần yêu cầu công việc xác định hành động và
  đích; đây là phạm vi người dùng giao, không phải một hàng đợi duyệt Ubuntu mới.

### 5.3 Những trạng thái không được nhập làm một

| Trạng thái | Ý nghĩa |
| --- | --- |
| Registration | Pending / approved / revoked / cần phục hồi credential |
| Connectivity | Online/offline với timestamp và độ tươi |
| Runtime readiness | Ready/degraded/blocked/update pending với identity thật |
| Local permission | Enabled/paused/denied theo scope local |
| Task/Job | Queued/running/terminal/unknown; pending stop khác stopped |

Node chưa có task/workspace vẫn có thể báo kết nối. Offline không là revoked.
Thu hồi tài khoản, thu hồi node, gỡ workspace, ngừng intake và stop process là
những thao tác khác nhau. Offline không chứng minh Job đã dừng; không rollback
file hoặc kill mọi process local chỉ vì revoke dịch vụ.

## 6. Gói công việc và thứ tự thực hiện

Trạng thái hiện tại: **G0 hoàn tất; G1/G2/G3/G4 có source và focused/full test
proof, trong đó W1 document E2E và W2 exec parity đã qua fixture; chưa nghiệm
thu live; G5/G6 chưa hoàn tất theo contract mới.** Code/test có sẵn được tái sử
dụng theo §3, không đánh dấu cả gói là xong chỉ vì một vài symbol hoặc test
fixture đã tồn tại.

### 6.0 Tiến độ và thứ tự ưu tiên ngay sau lượt tài liệu

| Ưu tiên | Gói | Trạng thái hiện tại | Bước kế tiếp có thể giao |
| --- | --- | --- | --- |
| 0 | G0 | **Hoàn tất tài liệu** | Giữ file này làm entry point; không sửa receipt lịch sử |
| 1 | G1 | **Idempotency + multi-binding source/focused tests đã PASS; live chưa xác minh** — HTTP multi-binding group **3/3**, full Python **289/289** | Inventory/binding và cùng principal trên hai client thật; giữ task target bất biến |
| 1 | G2 | **Đã triển khai source + focused tests; live chưa xác minh** — Electron SecretStore **5/5 PASS**, node-agent DPAPI/migration **8/8 PASS**, rotation **5/5**, HTTP **1/1**, Electron owner UI/IPC **25/25** ở source với fake/mocked protection | Chạy Windows packaged/live DPAPI/`safeStorage` + ACL/migration trên máy thật; sau đó fault-test rotation generation/retry trên exact package và kiểm tra restart/approved/revoked/reconnect |
| 2 | G3 | **Standing patch, document-write và exec parity đã có source + focused/Recovery-process proof; live chưa xác minh** — document HTTP→node→Recovery **3/3**, exec parity cùng local lane **12/12**, standing patch class **5/5**; crash/lost-ACK có `unknown/reconcile_required` hoặc receipt replay | Chạy Git/build/test/deploy thật trên Windows package; đóng duplicate-effect/reconcile ở các boundary còn lại; hoàn thiện parity artifact/read/write và giữ presence/reconcile độc lập khỏi pilot read-only |
| 2 | G4 | **G4-J + G4-K source/focused process proof; live chưa xác minh** — crash/restart trước bridge ACK, running Job resume, terminal ACK replay, stop-pending restart và writer fence trên local Job đã có **11/11 E2E** | Hoàn tất duplicate-effect/reconcile trên Job thật và xác minh writer lease trên Windows Job packaged/live; sau đó test hai ChatGPT client thật, stop và handoff |
| 3 | G5 | **`run-connected-agent` source + focused proof; live chưa xác minh** | Đưa command mới vào exact Windows package, kiểm heartbeat/reconnect độc lập policy, revoked/offline reconciliation và chọn/chứng minh startup sau logon hoặc pre-login |
| 4 | G6 | **Chưa rollout nghiệm thu** | Exact package → activation/re-discovery → T01–T16 → fault cuối → soak ≥24h; chỉ deploy khi có target/window rõ |

Không nên bắt đầu bằng việc bật cờ `exec`, kéo dài TTL context, tạo server AI
mới hoặc tái-enroll toàn bộ máy. Những việc đó không giải quyết nút thắt
account→binding→host và có thể làm mất khả năng phân biệt source proof với live
proof.

### G0 — Contract và baseline hiện hành

- Đặt tài liệu này làm entry point, cập nhật pointer trong CURRENT_STATE và
  kế hoạch/status cũ; giữ receipt lịch sử nguyên văn.
- Chốt ChatGPT là semantic controller, node runtime là execution authority;
  gateway/provider riêng không nằm trên critical path.
- Ghi source baseline + dirty scope, receipt lịch sử và phần chưa khảo sát live.

**Đầu ra:** kế hoạch này, ma trận tái sử dụng, acceptance T01–T16.
**PASS:** không còn chỉ dẫn hiện hành bắt đi qua server AI/per-action pilot
để nghiệm thu yêu cầu dùng chung account.

### G1 — Account, workspace inventory và task selection

**Tái dùng:** `mcp_oauth.py`, `http_api.py`, `store.py`, `mcp_facade.py`, tests
OAuth/task sessions. Không xây thêm hệ thống đăng nhập hay role framework.

1. Xác minh liên kết account hiện có, ánh xạ ổn định principal → owner, scope
   cần thiết cho các operation; không fallback từ OAuth sang shared pilot bearer.
2. Inventory trả binding ổn định và tên máy/workspace/capability/status rõ ràng.
3. Bind một lần từ registry local; retry không sinh đích trùng; quyền chia sẻ
   không tự biến mất khi hết task/context.
4. Task-open idempotent, immutable target; list/observe/stop từ client khác cùng
   principal; không yêu cầu máy chỉ mở ChatGPT enroll executor.
5. Kiểm tra sớm discovery/account inventory trên hai client thật khi được phép;
   nếu nền tảng chưa cho kết nối, ghi gate cụ thể, không thay bằng HTTP 200.

**PASS:** T01–T05 ở contract tests; live hai-client là gate riêng ghi exact
connection/build. Không bắt thử write live trước khi G3/G4 sẵn sàng.

### G2 — Enrollment bền vững, bảo vệ và đổi khóa

**Tái dùng:** node enrollment/store, `controlPlaneEnrollment.js`, device identity,
secret store và UI hiện có.

1. Lưu enrollment ID và quan sát trạng thái có timestamp; reload UI không mắc
   kẹt “pending” hoặc gửi enrollment mới khi đã approved.
2. Node tự reconcile trạng thái bằng credential; không public enumeration;
   cùng target retry dùng lại identity/secret, đổi origin/target cần thao tác rõ.
3. Approval có fingerprint/mã đối chiếu; reject/recover rõ, không tin hostname.
4. Bảo vệ secret bằng storage cùng user/ACL thực; node-agent Windows dùng
   DPAPI envelope và tự migrate config plaintext legacy ở lần đọc đầu tiên;
   Electron SecretStore dùng envelope/backup/fail-closed. Migration không được
   lộ secret trong renderer, argv, log hoặc Git. Kiểm tra quyền đọc khi chọn
   startup.
5. Rotation dùng hai pha node-mediated: node sinh candidate và persist protected
   trước `prepare`; central commit `activate` giữ old+new auth; node promote local
   rồi `ack` mới commit generation và retire old hash. Retry/reconcile phải phục
   hồi sau crash/mất ACK; phân biệt routine rotation với emergency revoke/lost-key
   recovery. Không giữ key cũ hợp lệ sau `ack` hay tự kích hoạt lại node revoked.

**PASS:** T02, T08, T10, T15; một lần approval qua restart/mất mạng; không copy
token; key A không sử dụng thay node B.

### G3 — Standing local policy và một đường thực thi đầy đủ

**Tái dùng:** runtime Coding Tools, Recovery Host/attestation, bridge/transport
hiện có, file/process/resource governance và permission local.

1. Tách quyền local bền vững khỏi context pilot. Chủ máy cấu hình/chuyển đổi
   một lần; không âm thầm nâng các root read-only đang có thành write/exec.
   Khi label/capability của một root đã đăng ký thay đổi, bắt buộc đi qua luồng
   thay thế tường minh: giữ `workspace_id`, tạo `workspace_generation` mới,
   retire generation cũ tại Ubuntu trước, vô hiệu policy local cũ rồi mới
   register generation mới. Không ghi đè registry/server record tại chỗ.
2. Admitted adapter chuyển đúng tool vào runtime hiện hữu; node poller không
   trở thành execution engine thứ hai. Recovery IPC vẫn là lifecycle có allowlist.
3. Dùng cùng checks target/root/preimage/actor/runtime identity/contract trước
   effect, cùng Job/idempotency/resource ownership, cùng đường trả lỗi.
4. Hoàn thiện structured argv/ProcessSpec qua contract được kiểm tra trong
   `exec_command` hoặc adapter; không dùng cờ private để né admission. Shell
   giữ là escape hatch được quyền local cho phép.
5. Thay nhánh direct-Popen của đường sản phẩm bằng runtime process lifecycle;
   không bật candidate exec rồi coi stop tree/receipt identity đã hoàn tất.
6. Mọi operation quảng cáo supported phải trả nội dung/output/diff/artifact
   hữu ích có giới hạn/redaction, không chỉ metadata và không bí mật credentials.

**G3-G — migration/replacement capability (đã có source + focused proof, chưa live):**

1. Thêm command/service `replace-workspace` và nút UI riêng; yêu cầu chủ máy
   xác nhận old generation, label mới và `{read, write, exec}` mới. `read` luôn
   bắt buộc; không dùng lại nút register như một overwrite ngầm.
2. Ghi phase marker local (`planned` → `retire_sent` → `retired` →
   `register_sent` → `completed`) cùng old/new generation và idempotency key;
   marker không chứa secret. Retry sau timeout/crash tiếp tục đúng phase, không
   tạo workspace/binding trùng.
3. Gọi retire đúng `{device_id, workspace_id, old_generation}` và chỉ sau
   receipt idempotent thành công mới vô hiệu policy file-read/patch/exec gắn với
   generation cũ. Nếu retire đã commit nhưng ACK mất, replay đúng request để
   lấy receipt; không tự register generation mới trước khi xác định phase.
4. Register generation mới với cùng `workspace_id` và capability đã xác nhận;
   central store tự fence binding/task cũ. Node chỉ thay entry local sau khi
   receipt mới hợp lệ; mất ACK sau register phải replay cùng generation.
5. UI phải hiển thị cảnh báo binding/task cũ đã bị fence/revoke và yêu cầu bind
   lại generation mới. Không gọi đây là “đổi quyền tức thời” nếu task cũ còn
   queued/unknown; phải reconcile trước.
6. Bổ sung test node-agent, Electron service/UI và store/HTTP cho: đổi label,
   read→write/exec, retire mất ACK, register mất ACK, crash giữa hai phase,
   old binding/task fence và không lộ path/secret. Các test fixture hiện đã xanh
   (`workspace_replacement` **3/3**, enrollment/manager **24/24**, full Node
   **862**); mức này mới là migration proof ở source, chưa chuyển thành live
   capability activation.

| Tool smart-v3 | Phạm vi cần đóng qua central | Oracle tối thiểu |
| --- | --- | --- |
| `workspace_context` | Inventory, chọn đích, context/read theo quyền local | Đọc đúng marker; sai account/root/generation bị chặn |
| `agent_workflow` | Tạo/sửa nhiều file, patch, verify theo runtime contract | Guarded diff; stale preimage không ghi đè |
| `task_control` | Theo dõi/quản lý RUN/WAVE và handoff; restart có lifecycle riêng | Không tạo writer thứ hai; restart không bypass activation |
| `exec_command` | Process/argv/cwd, Git, build/test và deploy được giao | Cùng runtime governance; account OS không bị nâng quyền |
| `command_control` | Output cursor, stdin khi supported, timeout/stop | Exact Job; child-tree quiescence; large output không treo |
| `request_permissions` | Đánh giá policy/local escalation khi cần | Trong standing policy không thêm Ubuntu human approval |
| `document_workflow` | Các operation tài liệu/artifact được runtime công bố | Nội dung/type/size/owner đúng; không tùy ý đọc file server |
| `view_image` | Ảnh/artifact đúng node/task | Handle/owner/MIME/size đúng; không giải path Windows trên Ubuntu |

`restart_runtime` vẫn là action của `task_control`, không thêm tool thứ chín.
Các operation chưa hỗ trợ phải báo đúng; không lấy số tám làm bằng chứng parity.

**Checkpoint triển khai G3-C/G3-D/G3-E hiện tại:** `exec_run` vẫn đi qua một relay duy nhất
vào runtime hiện hữu; thêm `exec_poll` và `exec_stop` dùng cùng `command_id`,
`job_id`, `local_handle`, `consumer_id`, `run_id` và `wave_id`. `RuntimeOrchestrator`
bind workspace rồi gọi `command_control(action=poll|kill)`; node agent đọc
journal `running` trước khi nhận action mới, không spawn lại, terminalize kết quả
đã có bằng chứng và chỉ acknowledge stop sau terminal evidence. `exec_stop` được
phép reconcile sau khi action TTL hết hạn nhưng vẫn default-deny nếu policy bị
disabled/target/contract/generation lệch. `runtime.control_plane_exec` vẫn
allowlist trong Recovery IPC; CJS bridge không lộ descriptor/credential. Policy
exec v2 có `authority_mode=standing` và `expires_at_ms=null`; chỉ action expiry
trung tâm còn giới hạn queue replay.

**Chưa được tính là hoàn tất:** standing `agent_workflow.apply_patch` đã có
HTTP→node completed-receipt fixture, nhưng chưa có preimage/path/generation/
policy mismatch và fault proof trên Recovery IPC/MCP process thật. Exec,
file-read, artifact và các write path khác chưa có parity end-to-end;
packaged activation, Windows live, read/write/exec/Git/build/deploy đầy đủ và
ChatGPT two-client receipt cũng chưa có. Vì vậy G3-E/G3-G/G3-H vẫn ở mức
**source + focused/full test proof**, còn G3 product gate mở cho
fault/reconcile, packaged/live proof và quyền local end-to-end.

**PASS:** T07, T12–T13, T15 trên fixture; không mất meaningful safety checks,
không có hàng đợi approval Ubuntu cho từng command trong scope đã cấu hình.

### G4 — Job continuity và nhiều chat/máy cùng account

**Tái dùng:** central action/attempt/receipt, local RUN/WAVE/Job ledger,
idempotency/resource fence. Không thêm scheduler hoặc lock manager cạnh tranh.

1. Mapping bền task/action/tool-call/idempotency → exact local run/wave/job;
   delivery attempt mới không tự là permission chạy effect lần nữa.
2. Cùng key/cùng payload replay cùng kết quả; khác target/payload conflict.
3. Mất ACK sau spawn hoặc patch: đọc journal/Job trước, replay receipt; thiếu
   chứng cứ thì unknown/reconcile, không tự tạo lệnh khác để thử lại.
4. Hai chat cùng principal vẫn là hai controller instance; nối vào write-fence
   local. Hai task ghi cùng workspace được tuần tự hóa hoặc conflict rõ.
5. Client khác observe/stop được theo scope; attach/handoff đổi generation và
   fence actor cũ. Không giả thread/chat ID do model khai là chứng cứ ownership.
6. Stop báo pending cho tới receipt terminal đủ chứng cứ; cancel chưa gửi,
   revoke authority và stop cây process là các đường riêng. Không mất output
   cursor khi reconnect và không để Job dài chặn status/cancel.

**PASS:** T04–T06, T11–T13; thử crash trước/sau các ranh giới durable mà không
gây duplicate effect hoặc false terminal state.

**Đã triển khai ở source trong các wave này:** bảng `mcp_task_writer_leases`
(schema 21) giữ `task_id`, binding, generation, thời điểm renew/expiry và
release reason; lease duy nhất trên mỗi binding được claim/renew trong cùng
transaction với admitted patch/exec. `writer_lease_generation` hiện được lưu
ở `actions`, `mcp_approved_patch_intents` và `mcp_exec_intents`, đi vào action
digest, được kiểm lại ở `poll_actions`, rồi truyền qua approved-patch/exec
bridge và receipt cùng `run_id`/`wave_id`. Lease hết hạn hoặc release sẽ fence
queued action trước node dispatch; lease unresolved `dispatch_unconfirmed`,
`accepted` hoặc `reconcile_required` không được takeover. OAuth `task_control`
hiện có `task_observe`, `writer_claim`, `writer_release`; view observe chỉ trả
task/action lifecycle đã rút gọn, không trả `arguments_json`, patch envelope,
file bytes hay node secret.

Checkpoint G4-A bổ sung HTTP ingress fixture với hai access token khác nhau cùng
OAuth principal: inventory trả cùng `binding_id`, task-open replay trả cùng
`task_id`, và client thứ hai observe đúng task (shared-account test **1/1 PASS**).

Đoạn trên là ghi chú của **checkpoint G4 trước migration schema 21**; nó được
supersede bởi checkpoint fixture migration + full regression green ở cuối tài
liệu. Hiện fixture/source local đã xanh theo các con số ở §3.4, nhưng các giới
hạn sản phẩm vẫn còn nguyên: lease chưa được nối vào Windows Job live, chưa có
crash/mất ACK qua package exact, và stop hiện vẫn là lifecycle của
`command_control`, không được giả thành writer handoff thành công. Vì vậy local
focused/full proof vẫn chưa phải multi-client ChatGPT, packaged/live hay soak
proof.

**G4-J — Recovery process crash/reconcile (đã có source + focused proof, chưa live):**

1. Bổ sung process fixture tự thoát sau khi MCP đã nhận `exec_run` và giữ
   marker/journal observable nhưng không chứa secret. Mốc terminal crash vẫn
   là phần mở rộng G4-K.
2. Kiểm tra mọi nhánh lỗi bridge: nếu đã có durable `prepared` hoặc handle thì
   không được trả `rejected` như lỗi trước
   effect; phải trả `unknown/reconcile_required` và giữ đúng `command_id`,
   `job_id`, `run_id`, `wave_id`.
3. Khởi động lại node/recovery fixture, đọc journal trước khi nhận action mới,
   chứng minh không gọi `exec_run` lần hai. Chỉ `exec_poll`/reconcile khi
   effect boundary đã rõ; nếu không rõ thì giữ unknown để operator xử lý.
4. Đã lặp lại process restart với cùng installation/data root; test chứng minh
   central giữ `reconcile_required`, process mới không nhận lại action và tổng
   `exec_run` chỉ xuất hiện một lần. Không dùng fixture pass để tuyên bố package/live.

**Bằng chứng:** `test_exec_node_agent` **21/21 PASS**, HTTP→Recovery process
E2E **6/6 PASS**, full control-plane discovery **250/250 PASS**; `node --check`,
`py_compile` và `git diff --check` PASS. Đây là focused proof cho crash sau
`exec_run`, không phải Recovery crash terminal, Windows Job hay packaged/live.

**G4-K — terminal crash/restart và writer/Job handoff (đang thực hiện, chưa đóng):**

- Đã có focused proof cho Job `running` qua Recovery restart: node đọc handle
  journal, process mới gọi `exec_poll`, terminal receipt được settle và không
  gọi `exec_run` lần hai.
- Đã có focused proof cho local terminal result mất trước bridge ACK: node giữ
  `unknown/reconcile_required`, restart không tự suy diễn completed và không
  redeliver.
- Còn mô phỏng crash sau central terminal receipt trước ACK, crash khi stop đang
  pending và writer lease unresolved; cần chứng minh terminal payload replay,
  không tạo attempt mới, không takeover qua `unknown/reconcile`, sau đó mới
  chuyển oracle sang Job Windows thật và hai ChatGPT client live.

### G5 — Presence, startup và UI vận hành lâu dài

**Tái dùng:** Recovery Supervisor, lock/backoff, route evidence, enrollment UI,
Command Center. Không cài thêm scheduler song song.

1. Agent connection/status sống từ registration và package hợp lệ, không cần
   policy read-only còn hạn; task admission là bước độc lập sau đó.
2. Phân loại transport outage khác auth revoked/invalid; config/secret hỏng
   cần recovery, không tự sinh identity mới để né lỗi.
3. UI thể hiện riêng năm trạng thái ở §5.3 và đích bất biến của từng task.
4. Đóng UI không mất đăng ký; local pause/manual stop không bị auto-restart
   bật lại trái ý. Network recover giữ một agent, cùng Job/receipt lineage.
5. Revoke account/node/workspace có xác nhận đúng target và audit; không ngầm
   xóa file, rollback hoặc báo offline Job đã dừng.

**Hai mức startup phải quyết định trước implementation lifecycle:**

- **Sau reboot + user logon:** tái dùng AtLogOn/Interactive/Limited hiện có;
  không cần mở UI, nhập token hoặc cài lại policy mỗi phiên.
- **Sau reboot chưa login:** chưa có proof trong baseline. Nếu người dùng yêu
  cầu mức này thì là acceptance bắt buộc thêm, không được đánh tráo bằng mức
  trên. Cần chọn account/service headless, storage secret, toolchain/GUI/mapped
  drive dependencies; không tự chọn SYSTEM/Administrator hay lưu password thô.

**PASS:** T08–T11, T15; verdict startup ghi rõ mức đã được chọn/kiểm chứng.

### G6 — Migration, package, rollout và nghiệm thu người dùng

1. Review dirty changes có sẵn; xác định exact candidate, không lẫn code/docs
   với artifact/deployed bytes. Giữ nguyên identity, registry và evidence.
2. Lập capability/schema compatibility giữa central/agent/runtime; phiên bản
   cũ không được tự hiểu policy mới là full quyền. Mismatch chặn effect, báo lý do.
3. Backup verified trước migration; đóng intake theo runbook khi cần; kiểm tra
   pending/unknown actions, runtime Job và writer trước cutover. Không retry mù.
4. Chủ máy chuyển policy lâu dài một lần. Không tái enroll tất cả máy hoặc tạo
   owner/binding mới chỉ để né migration; không hồi sinh context đã thu hồi.
5. Build/verify exact central artifact và Windows candidate; smoke packaged,
   installed, activation/re-discovery, rồi hai-client E2E trên workspace fixture.
6. Chạy soak ít nhất 24 giờ liên tục trên exact final build sau fault/rollout
   cuối, kèm quan sát qua mốc TTL pilot cũ; không cộng dồn các window/build.
   Thay runtime bytes, redeploy hoặc restart làm mở window mới. Ghi outage/
   failure/unknown thật và xử lý rõ trước PASS; không lấy unit fake-clock thay
   soak thực hoặc lấy thời gian gián đoạn làm liên tục.
7. Rollback giữ schema/receipt có thể đối chiếu; nếu binary cũ không hiểu state
   mới, giữ admission recovery và dùng restore/reconcile được duyệt, không
   trỏ lại DB cũ rồi mất lịch sử hoặc cấp lại credential revoked.

**PASS:** T01–T16 theo phạm vi đã chốt, đúng packaged bytes, user xác nhận workflow.
Source/test pass không thay live acceptance; không gọi production-ready trước
gate này. Mọi rollout/restart/deploy phải có yêu cầu và target được cấp riêng.

### 6.1 Phụ thuộc và phân công

Thứ tự chính: **G0 → G1/G2 → G3 → G4/G5 → G6**. G1/G2 có thể phát triển song
song; contract G3/G4 và status/startup G5 có thể chuẩn bị sớm, nhưng không bật
live execution trước khi admission, writer và stop/reconcile được chứng minh.

| Nhóm thực hiện | Phần sở hữu |
| --- | --- |
| Central | Account/binding/task, dispatch/receipt, compatibility và central UI |
| Desktop/runtime | Enrollment/secret, standing permission, bridge, Job/process, supervisor/UI |
| Kiểm chứng | Contract/fault tests, exact artifact và multi-client Windows acceptance |
| Chủ hệ thống | Chọn mức startup, xác nhận quyền local, account/IdP, máy/workspace và cửa sổ rollout/deploy |

Không yêu cầu người dùng quyết định lại mục tiêu đã chốt; chỉ hỏi khi cần một
lựa chọn vận hành cụ thể. Chưa có ước lượng ngày hoàn thành đáng tin cho các
gate live; sau G1/G2 mới ước lượng từ khối lượng và khả năng truy cập máy thật,
không biến số dòng hoặc số test hiện có thành phần trăm hoàn thành.

## 7. Ma trận nghiệm thu

Mỗi case ghi candidate/build/contract, target, expected/actual, evidence và
trạng thái Job cuối. Mặc định **chưa nghiệm thu contract mới**; test-source hoặc
receipt cũ chỉ là đầu vào tái sử dụng, không tự đánh dấu PASS.

| ID | Case | Điều kiện PASS |
| --- | --- | --- |
| T01 | ChatGPT trên hai máy, cùng tài khoản đã liên kết | Cùng `principal_id` thấy cùng `binding_id`/workspace; nếu chỉ có một binding thì dùng được làm target mặc định; máy chỉ điều khiển không enroll; lệnh đi đúng host |
| T02 | Sai tài khoản/loại credential | Node key không làm user MCP token; user token không giả node; account lạ/revoked không truy cập bằng biết ID |
| T03 | Host trùng tên/path/raw workspace ID; retry bind | Binding resolve đúng tuple và marker; retry không tạo đích trùng; không failover Ubuntu |
| T04 | Client đổi lựa chọn, root retire/rebind | Task giữ đích; account khác không dùng task; generation mới không nhận task cũ; mọi client cùng account thấy trạng thái fenced và phải bind lại |
| T05 | Task-open timeout/mất ACK | Cùng key/scope trả cùng task; khác scope conflict; không thêm RUN/Job |
| T06 | Hai chat ghi đồng thời, tiếp quản từ máy khác | Một writer hoặc serialization/conflict rõ; actor cũ bị fence; observe/stop không chiếm writer |
| T07 | Read/write/exec trong và ngoài standing policy | Trong scope không thêm Ubuntu approval; ngoài scope bị chặn/local escalation; không vượt OS/root/preimage |
| T08 | Quá 24h/context expiry/task close/OAuth refresh | Enrollment và permission thường trực không mất; không copy token/context; closed/revoked task không tự sống lại |
| T09 | Mất mạng, Ubuntu restart, đóng UI, node reboot | Giữ identity, một agent, cùng lineage; auto reconnect; ghi riêng logon và pre-login verdict |
| T10 | Rotation crash/mất ACK | Cùng device, generation tăng đúng; key cũ invalid sau chuyển đổi; recovery không lộ secret/đăng ký trùng |
| T11 | Revoke account/node, disable root, stop khi offline | Chặn đúng scope; pending/unknown trung thực; late receipt đối chiếu được; không giả stopped |
| T12 | Runtime parity | Đọc, sửa nhiều file, Git, build/test, document/image/artifact đúng máy; operation advertised có success/negative proof |
| T13 | Exec fault/large output/child process | Không deadlock; output cursor ổn định; exact Job/tree-stop; crash/mất ACK không tạo effect lần hai |
| T14 | Upgrade/rollback/restore | Giữ device/permission/ledger/dirty files; không hồi sinh quyền revoked; incompatibility đóng admission rõ |
| T15 | Secret/config/root/permission lỗi | Secret không vào UI/log/argv/artifact; config hỏng không tự enroll; local disable không bị bật lại |
| T16 | E2E thật + soak + deployment có scope | Hai client ChatGPT sửa/test trên host đích, đổi client quan sát/tiếp tục đúng task; soak ≥24h liên tục trên final build sau fault cuối; deploy fixture chỉ khi đích được giao |

Windows là acceptance target đầu tiên. Chỉ ghi Linux/macOS hoặc bề mặt ChatGPT
khác supported sau khi có package/client/lifecycle proof tương ứng. Không lấy
kết quả HTTP fixture hoặc một client duy nhất làm bằng chứng “tất cả máy”.

## 8. Validation và các file cần tận dụng

Không chạy full Cargo/npm/Python suite cho thay đổi tài liệu này. Khi triển khai,
bắt đầu bằng lane nhỏ nhất phát hiện hành vi đổi; xem [TESTING](TESTING.md).

| Boundary | File/test nền để mở rộng |
| --- | --- |
| Account/binding/task/rotation | [test_store.py](../control-plane/tests/test_store.py), [test_http_api.py](../control-plane/tests/test_http_api.py), [test_mcp_oauth.py](../control-plane/tests/test_mcp_oauth.py), [test_mcp_task_sessions.py](../control-plane/tests/test_mcp_task_sessions.py) |
| Onboarding/UI/presence | [control-plane-enrollment.test.js](../tests/control-plane-enrollment.test.js), [control-center-manager.test.js](../tests/control-center-manager.test.js), [recovery-supervisor.test.js](../tests/recovery-supervisor.test.js), [control-plane-route-evidence.test.js](../tests/control-plane-route-evidence.test.js) |
| Bridge và quyền | [control-plane-bridge-runtime.test.js](../tests/control-plane-bridge-runtime.test.js), [control-plane-approved-patch-runtime.test.js](../tests/control-plane-approved-patch-runtime.test.js), [control-plane-file-read-runtime.test.js](../tests/control-plane-file-read-runtime.test.js) |
| Node journal/exec | [test_exec_node_agent.py](../control-plane/tests/test_exec_node_agent.py), [test_approved_patch_node_agent.py](../control-plane/tests/test_approved_patch_node_agent.py), [test_mcp_exec.py](../control-plane/tests/test_mcp_exec.py), [test_mcp_faults.py](../control-plane/tests/test_mcp_faults.py) |
| Runtime continuity/fencing/process | [test_universal_idempotency.py](../resources/coding-tools-mcp/tests/test_universal_idempotency.py), [test_execution_resources.py](../resources/coding-tools-mcp/tests/test_execution_resources.py), [test_windows_job_object.py](../resources/coding-tools-mcp/tests/test_windows_job_object.py), [test_workspace_session_isolation.py](../resources/coding-tools-mcp/tests/test_workspace_session_isolation.py) |
| Package/migration | [test_release_artifact.py](../control-plane/tests/test_release_artifact.py), [packaged-recovery-smoke.js](../scripts/packaged-recovery-smoke.js), [installed-recovery-smoke.js](../scripts/installed-recovery-smoke.js), [RELEASE_CHECKLIST](RELEASE_CHECKLIST.md), [Recovery runbook](CONTROL_PLANE_RECOVERY_RUNBOOK.md) |

Các tests chưa có phải bổ sung vào boundary đang sở hữu hành vi, không tạo suite
hoặc framework chung mới. Thay đổi ownership/process cần proof Recovery process;
Windows Job Object/startup cần Windows thật; release/live cần exact package.
Không rerun proof không liên quan hoặc đổi tests để che guard chưa được đáp ứng.

## 9. Những quyết định còn cần đúng thời điểm

1. **Trước G5:** reboot cần tự hoạt động sau login hay bắt buộc trước login?
   Mức pre-login không được tự loại khỏi yêu cầu hoặc tự coi đã hỗ trợ.
2. **Trước live G1/G6:** xác định connection/IdP đã liên kết, hai máy mở ChatGPT,
   máy thực thi và workspace fixture. Không yêu cầu dán token vào chat.
3. **Trước policy migration:** xác nhận scope local lâu dài và các root được
   chia sẻ; chỉ cấu hình một lần, không quay lại cấp context mỗi ngày.
4. **Trước deploy/live operations:** chỉ định đích, cửa sổ và rollback authority.
5. **Chỉ khi cần app AI riêng:** mới chọn provider/model/ngân sách và xây gateway;
   không lấy nhánh tùy chọn này làm blocker của MCP dùng chung.

## 10. Definition of Done và checkpoint tài liệu

Đường chính hoàn thành khi người dùng có thể:

1. Đăng ký và được duyệt máy đích một lần; bind workspace và cấu hình quyền local.
2. Mở ChatGPT trên ít nhất hai máy cùng tài khoản/kết nối đã xác thực, thấy cùng
   ID workspace và giao việc đúng máy đích, không enroll máy chỉ điều khiển.
3. Đọc/sửa/Git/build/test và chạy/dừng Job trong quyền đã giao; không duyệt
   context hay từng lệnh ở Ubuntu, không vượt quyền OS.
4. Đổi client, reconnect/reboot theo scope đã chọn, vượt TTL pilot và upgrade
   mà không mất đăng ký/task lineage hoặc lặp effect.
5. Thu hồi/đổi khóa/gỡ workspace có hiệu lực đúng phạm vi, trạng thái trung thực;
   đủ fault/packaged/soak proof trên candidate được xác định.

Không dùng một patch đơn file, tám tên tool, PID Running, source acceptance
hoặc HTTP 200 làm thay thế cho các điều kiện trên. ChatGPT đóng không chứng
minh vòng suy luận tiếp tục nền; Job đã giao chỉ tiếp tục theo lifecycle local.

**Checkpoint cập nhật kế hoạch và validation, 20-09-2026, 16:04 +07 (lịch sử; đã
được re-run ở 16:34–16:35):** cập
nhật entry point này để phản ánh đúng mô hình account chung → `binding_id` →
host/workspace và tình trạng G1/G2 đã có source/focused proof. Chỉ sửa tài liệu
trong wave này; giữ nguyên mọi dirty source/evidence có trước. Không tạo
execution Job, không kiểm tra trạng thái Job live, không commit/push,
release/deploy/restart hoặc gọi provider trả phí.

Validation tài liệu: `git diff --check` PASS; đã kiểm tra đủ G0–G6 và T01–T16,
không có conflict marker/trailing whitespace. Các test focused được chạy riêng
ở checkpoint dưới; đây không phải live acceptance.

### Checkpoint implementation G2 — durable enrollment/status (20-09-2026)

- **Đã thay đổi:** `store.py` làm retry enrollment theo cùng credential trở nên
  replay-safe sau approval; thêm `node_enrollment_status` cho pending/approved/
  revoked mà không trả secret, owner, path hay OAuth identity; `http_api.py`
  thêm route node-authenticated `/v1/nodes/{device_id}/enrollment-status`.
- **Đã thay đổi:** `node_agent.py` ghi `enrollment_id`, `enrollment_state`,
  `enrollment_observed_at_ms`, generation và lỗi gần nhất vào config trước/sau
  network boundary; thêm `reconcile-enrollment`, giữ trạng thái cũ với
  `fresh=false` khi Ubuntu tạm mất mạng, không tự tạo enrollment mới.
- **Đã thay đổi:** Electron service/main/preload/renderer đọc lại status sau
  reload và hiển thị riêng pending/approved/revoked/stale; renderer không nhận
  node secret. Các output parser giữ bounded/strict schema.
- **Bằng chứng mạnh nhất:** các lane focused hiện tại gồm store 80/80, HTTP
  41/41 và Node enrollment/manager 21/21 PASS; test riêng cho enrollment/status
  và các route liên quan nằm trong các lane này. Đây là source/focused test
  proof, chưa phải Windows packaged/live proof; protected Windows secret store
  và rotation chưa đóng.
- **Git/run state:** branch `codex/control-plane-quarantine`, HEAD vẫn
  `502ffb8cf8b541ee74af30194aff2dce08c3b649`; worktree dirty từ trước cộng
  thay đổi G2 chưa commit; không commit/push/deploy/restart/provider.
- **Blocker còn lại:** chưa có live node/Ubuntu và exact packaged build trong
  lượt này, nên chưa đánh dấu T08/T10/T15/T16 PASS. Idempotency đã có source và
  focused proof; next action chính xác là controller writer lease/generation,
  observe/stop/handoff giữa hai controller cùng account, rồi mới nối runtime
  write/exec.

### Checkpoint implementation G1 — keyed task-open (20-09-2026)

- **Đã thay đổi:** thêm bảng durable `mcp_task_open_idempotency`; `task_open`
  public của OAuth MCP bắt buộc `idempotency_key`. Cùng principal + key +
  target/label trả cùng `task_id`; đổi target/label trả `ConflictError`. Task
  vẫn lưu binding/device/endpoint/workspace/generation bất biến.
- **Đã thay đổi:** private Console caller cũ vẫn được tương thích bằng key
  legacy sinh nội bộ; đường MCP đa-client không dùng đường fallback này. Replay
  được xử lý trước admission/binding revalidation để không tạo task mới khi
  client retry sau fault hoặc khi target đã đóng.
- **Bằng chứng mạnh nhất:** `test_mcp_task_sessions` 8/8, `test_mcp_oauth`
  19/19, HTTP API 41/41 và store 80/80 PASS bằng `unittest`; `py_compile` và
  `git diff --check` cũng PASS. Chưa có live two-client/lease proof nên T04–T06
  và T16 chưa PASS.
- **Git/run state:** cùng branch/HEAD như checkpoint G2; worktree vẫn dirty,
  chưa commit/push/deploy/restart. Thay đổi G1/G2 đang nằm cùng working tree để
  review guarded trước khi staging.
- **Next action:** bổ sung controller writer lease/generation và observe/stop
  scope cho hai chat cùng principal; sau đó mới relay runtime write/exec.

### Checkpoint validation focused — 20-09-2026, 16:02–16:04 +07 (lịch sử)

- `control-plane/tests`: store **80/80**, HTTP API **41/41**, OAuth **19/19**,
  task sessions **8/8**, exec node **12/12**, file-read node **7/7** PASS qua
  `unittest` với Python runtime của workspace.
- `tests/`: enrollment + Control Center **21/21** và packaged/installed
  recovery smoke **3/3** PASS qua Node test runner.
- `py_compile` các module control-plane đã sửa và `git diff --check` PASS.
- `npm run test:mcp`/pytest không dùng được trong shell này vì lệnh `python`
  không có và bundled Python không cài `pytest`; đã chuyển sang `unittest`,
  không bỏ qua lỗi test nào.
- Kết luận wave: **focused source proof PASS; live/package/soak proof vẫn
  thiếu**. Không có failure sản phẩm mới được quan sát trong các lane đã chạy.

### Checkpoint implementation G4 — writer lease và task control, 20-09-2026,
16:25 +07

- **Đã thay đổi:** `store.py` nâng schema source lên 20, thêm durable
  `mcp_task_writer_leases` với unique active lease theo `binding_id`,
  `lease_generation`, renew/expiry/release audit; claim/renew/release đều nằm
  trong transaction. Approved patch và bounded exec có `task_id` giờ phải claim
  lease trước khi seal action; read/permission-request không lấy writer lease.
- **Đã thay đổi:** `observe_mcp_task` trả task state, lease hiện hành và action
  lifecycle đã redacted; `close_mcp_task_session`/owner close giải phóng lease.
  `mcp_facade.py` mở `task_control` cho OAuth file-read contract với ba operation
  `task_observe`, `writer_claim`, `writer_release`; không trả payload file,
  patch envelope, argv hay credential.
- **Bằng chứng mạnh nhất:** `test_mcp_task_sessions` **10/10** (gồm claim,
  renew replay, conflict giữa hai task, release, expiry handoff và facade
  task_control); `test_mcp_exec` **6/6**; `test_mcp_permission_requests`
  **10/10**; `test_mcp_oauth` **19/19**; `test_http_api` **41/41**; `test_store`
  **80/80**; `py_compile` PASS. Các test cũ không bị regression.
- Số OAuth **19/19** ở checkpoint 16:25 là trước khi test HTTP
  `task_control` được thêm; re-run 16:34–16:35 bên dưới đã xác nhận **20/20**
  và full discovery **223/223**.
- **Giới hạn:** chưa có ChatGPT thật trên hai máy cùng principal, chưa có
  exact Windows package/Ubuntu live source-20 rollout, chưa có controller crash
  sau claim, mất ACK sau spawn, observe/stop trên Job live hoặc soak. Không đánh
  dấu T04–T06/T11–T13/T16 PASS.
- **Git/run state:** branch `codex/control-plane-quarantine`, HEAD
  `502ffb8cf8b541ee74af30194aff2dce08c3b649`; worktree dirty, source/docs chưa
  commit; không stage/commit/push/deploy/restart/provider.
- **Next action chính xác:** nối lease generation vào bridge → exact Coding Tools
  Job/RUN/WAVE identity; thêm fault tests claim-before/after dispatch và
  cross-client stop/observe; sau đó mới tách presence khỏi TTL read-only và
  chạy packaged/live acceptance.

### Checkpoint validation re-run — 20-09-2026, 16:34–16:35 +07

- Full control-plane discovery trên working tree hiện tại đã chạy **223/223
  PASS** bằng `python3 -m unittest discover -s tests -p 'test_*.py' -q` trong
  46,588 giây. Kết quả mới bao gồm test HTTP `task_control` nên OAuth là
  **20/20** và task sessions là **10/10**; các lane liên quan khác là HTTP
  **41/41**, store **80/80**, exec **6/6**, permission **10/10**, release
  artifact **3/3**.
- Node focused lane `node --test` cho enrollment/Control Center và
  packaged/installed recovery smoke đạt **24/24 PASS** (21 + 3). `py_compile`
  bốn module control-plane và `git diff --check` cũng **PASS**.
- Đây là revalidation của source/fixture/local smoke. Nó không chứng minh
  Ubuntu live đã nạp schema 20, exact Windows package đã activate, hai ChatGPT
  client cùng principal đã chạy, hay writer lease đã nối vào Job/RUN/WAVE thật.
- **Git/run state:** branch `codex/control-plane-quarantine`, HEAD
  `502ffb8cf8b541ee74af30194aff2dce08c3b649`; worktree vẫn dirty, gồm cả
  `.coding-tools/orchestration/ledger.sqlite3`; chưa stage/commit/push,
  deploy/restart hoặc gọi provider trả phí.
- **Bước tiếp theo:** giữ lease generation xuyên suốt bridge → exact Coding
  Tools Job/RUN/WAVE; thêm fault test claim-before/after dispatch, controller
  crash/mất ACK và cross-client observe/stop/attach/handoff trên fixture, rồi
  mới mở G3 standing read/write/exec và nghiệm thu packaged/live.

### Checkpoint schema-21 writer-fence migration — 20-09-2026, 17:01–17:02 +07

- **Đã thay đổi:** control-plane `SCHEMA_VERSION` nâng từ `20` lên `21`;
  migration thêm `writer_lease_generation` vào `actions`,
  `mcp_approved_patch_intents` và `mcp_exec_intents`. Approved patch/exec
  capture generation khi seal; generation đi vào action digest và được
  `poll_actions` kiểm lại theo lease hiện hành, task và binding trước dispatch.
- **Đã thay đổi:** release/takeover bị fence nếu còn action
  `dispatch_unconfirmed`, `accepted` hoặc `reconcile_required`; node agent
  yêu cầu `mcp_task_id` + generation trước bridge. Approved-patch bridge và
  runtime context/idempotency giữ task/generation; receipt redacted yêu cầu
  thêm `task_id`, generation, `run_id`, `wave_id`; `agent_workflow` nhận
  `contract_fingerprint` authority metadata.
- **Validation tại thời điểm checkpoint:** ban đầu full discovery còn **224
  test: 217 PASS, 4 failure, 3 error** và Node focused **30 test: 23 PASS,
  7 failure** do migration fixture/contract. Các lỗi đó đã được đóng ở
  checkpoint kế tiếp bên dưới; không phải live node failure.
- **Git/run state:** branch `codex/control-plane-quarantine`, HEAD vẫn
  `502ffb8cf8b541ee74af30194aff2dce08c3b649`; worktree dirty với source/test/
  docs/evidence có sẵn, chưa commit/push/deploy/restart hoặc gọi provider trả
  phí. Không reset/clean các dirty files.
- **Blocker phân loại tại thời điểm đó:** không có bằng chứng lỗi Ubuntu live hay
  Windows runtime; cần migrate fixture/test cho contract schema 21.
- **Next action đã thực hiện:** bổ sung `endpoint_id`, `mcp_task_id` và
  `writer_lease_generation` vào fixture/action/result, mở rộng expected-fields
  node admission và cập nhật contract-fingerprint assertion; sau đó chạy lại
  discovery + Node focused/full. Không mở direct-Popen, không deploy live.

### Checkpoint fixture migration + full regression green — 20-09-2026, sau 17:xx +07

- **Đã thay đổi:** các fixture/action của `test_mcp_exec.py`, approved-patch
  node/e2e, exec node và Electron bridge/runtime đã mang task ID, endpoint,
  writer generation, RUN/WAVE receipt correlation và authority fingerprint.
  Node approved-patch policy admission cũng đã thêm task/generation vào
  expected schema và kiểm tra fail-closed trước local bridge; đây là source fix,
  không chỉ sửa assertion.
- **Validation mạnh nhất:** Python control-plane discovery **224/224 PASS**;
  Node full `node --test --test-concurrency=4 tests/*.test.js` **848 tests,
  832 PASS, 16 SKIP, 0 FAIL**; patch/exec HTTP-node e2e, approved-patch
  bridge/runtime focused và `py_compile` đều PASS; `git diff --check` PASS.
- **Bằng chứng vẫn giới hạn:** đây là source/fixture/local test proof trên
  working tree. Chưa chứng minh Ubuntu live đã nạp schema 21, ChatGPT thật trên
  hai máy cùng principal, exact Windows packaged activation, crash/mất ACK live,
  standing write/exec hoặc soak.
- **Git/run state:** branch `codex/control-plane-quarantine`, HEAD vẫn
  `502ffb8cf8b541ee74af30194aff2dce08c3b649`; worktree dirty, chưa commit/push/
  deploy/restart/provider.
- **Next action:** nối lease generation vào exact Coding Tools Job/RUN/WAVE
  lifecycle và triển khai admitted runtime relay cho read/write/exec theo
  standing local policy; sau đó mới chạy packaged/two-client/fault/soak gates.

### Checkpoint G3-prep — structured argv và skeleton exec bridge, 20-09-2026, 17:33 +07

Wave này chỉ đặt đúng boundary để chuyển exec vào Coding Tools MCP; **chưa
được gọi là relay đã hoạt động** và không mở thêm quyền live.

- **Đã thay đổi ở MCP runtime:** `tool_schema.py` công bố trường `argv` bounded
  (tối đa 32 phần tử, mỗi phần tử tối đa 2048 byte) riêng cho local control-plane
  bridge. `exec_tools.py` chỉ nhận trường này khi request context có đủ
  `client_id=electron-control-plane-exec-bridge`, `client_type=electron` và
  `attestation_verified=true`; caller thường gửi `argv` bị từ chối. `cmd` phải
  trùng executable đầu tiên; NUL/newline/metacharacter và giới hạn vượt mức bị
  chặn; process vẫn đi qua resource governance hiện hữu và `shell=False`.
- **Đã thêm adapter source:** [controlPlaneExecBridge.js](../electron/services/controlPlaneExecBridge.js)
  có loader/validator cho policy cục bộ, resolve registry workspace theo
  `{workspace_id, workspace_generation}`, allowlist argv, kiểm tra
  device/endpoint/owner/task/writer lease và contract fingerprint, digest bounded
  cùng normalizer receipt có `command_id`, `job_id`, `run_id`, `wave_id` và
  runtime identity. Adapter không tự spawn process và không nhận absolute path
  hay credential từ Ubuntu.
- **Đã thêm test:** admission không có bridge identity bị từ chối; identity có
  attestation chạy `echo` qua structured argv. Test chuyên biệt **1/1 PASS**.
  `node --check electron/services/controlPlaneExecBridge.js`, module admission
  smoke (`normalisePolicy` → `admitExecBridgeRequest`) và `git diff --check`
  **PASS**. Đây là source/module proof, chưa phải Recovery/MCP live proof.
- **Giới hạn validation:** targeted `test_wave_a_runtime.py` đạt **11/12 PASS**.
  Ca còn lại là `test_exec_returns_command_id_and_canonical_command_output_refs`
  trên Linux fixture mặc định: helper `landlock_exec.py` được gọi như script nên
  lỗi `ImportError: attempted relative import with no known parent package`;
  đây là lỗi harness/runtime sandbox có trước wave, không được ghi thành bằng
  chứng bridge relay. Full control-plane `224/224` và Node `832/16 SKIP/0 FAIL`
  vẫn là mốc của wave fixture trước đó, chưa được chạy lại chỉ vì thay đổi này.
- **Chưa làm trong wave:** chưa thêm `controlPlaneExecPolicyFile()`;
  chưa có `control-plane/recovery_exec_bridge.cjs`, RPC
  `runtime.control_plane_exec`, handler/admission trong Recovery Host hay method
  `RuntimeOrchestrator.controlPlaneExec()`; `node_agent._poll_exec_once()` vẫn
  gọi `_run_bounded_exec` direct-Popen. Vì vậy direct-Popen **vẫn là đường hiện
  tại**, chưa thể tuyên bố process đã được quản lý bởi Job/RUN/WAVE qua MCP.
- **Git/run state:** branch `codex/control-plane-quarantine`, HEAD
  `502ffb8cf8b541ee74af30194aff2dce08c3b649`; worktree vẫn dirty, có source,
  test, docs, `.coding-tools/orchestration/ledger.sqlite3` và `var/` chưa track;
  không stage/commit/push/deploy/restart hoặc gọi provider trả phí.
- **Next action chính xác:** tích hợp policy path → Recovery IPC → Recovery Host
  → RuntimeOrchestrator; bind `workspace_context`, gọi `exec_command` với argv
  + attestation + `task_context_id`/idempotency metadata; sau đó đổi node poller
  sang bridge, giữ journal `prepared` và trả `unknown` sau boundary nếu mất ACK.
  Trước khi gọi G3 hoàn tất phải có `command_control` polling/stop cho Job dài,
  receipt Job/RUN/WAVE và test mismatch device/endpoint/workspace/generation.

### Checkpoint G3-A — relay `exec_run` qua runtime hiện hữu, 20-09-2026, 18:10 +07

Wave này đã thực hiện phần relay đầu tiên nhưng **chưa đóng toàn bộ G3**.
Không có quyền live nào được tự bật; policy vẫn phải được operator cài và
kiểm tra tại node.

- **Đã nối:** `RuntimePaths.controlPlaneExecPolicyFile()`; Recovery IPC allowlist
  `runtime.control_plane_exec`; Recovery Host loader/admission kiểm policy,
  device, workspace registry, endpoint, task, writer generation, argv allowlist,
  contract và runtime identity; `recovery_exec_bridge.cjs` che descriptor/token
  khỏi Python node agent.
- **Đã nối:** `RuntimeOrchestrator.controlPlaneExec()` chỉ gửi lời gọi nội bộ
  tới Coding Tools MCP. Nó bind `workspace_context`, gọi `exec_command` với
  structured `argv`, `task_context_id`, idempotency key và connector attestation;
  local MCP giữ process/Job/RUN/WAVE. Receipt được allowlist và digest gồm
  `command_id`, `job_id`, `run_id`, `wave_id`, runtime identity và output refs.
- **Đã nối:** `_poll_exec_once()` chuyển đường spawn sản phẩm chính sang Recovery /
  Electron bridge; journal ghi `prepared` trước effect, lưu `running` cùng
  handle khi MCP trả job dài, terminalize `completed`/`failed`/`stopped`, và
  chuyển `unknown` khi boundary/identity/ACK không đủ. `_run_bounded_exec` còn
  trong source chỉ để compatibility/focused tests, không phải đường relay mới.
- **Validation exact bytes:** Node bridge/CJS/runtime **7/7 PASS**; approved-patch
  bridge/runtime **9/9 PASS**; Python node-agent exec **12/12 PASS**; Python
  `test_mcp_exec` **7/7**, `test_mcp_oauth` **20/20**, `test_http_api` **41/41**
  (tổng **68/68 PASS**); `py_compile`, `node --check`, `git diff --check`
  **PASS**. Đây là focused/source proof trên working tree, không phải Windows
  packaged/live proof.
- **Còn thiếu và không được suy ra:** admission hiện chỉ nhận `exec_run`;
  `exec_poll` chưa gọi `command_control` để đọc lại Job đang `running`;
  `exec_stop` chưa lấy stop request, kill cây process và acknowledge terminal;
  chưa có resume journal trước mỗi poll để không spawn lại sau reboot/crash;
  mất ACK/identity phải tiếp tục `unknown/reconcile`. Policy exec hiện có
  `expires_at_ms`, nên chưa phải standing permission độc lập context. Chưa có
  test live multi-client, packaged activation, fault sau spawn, rotation hay
  soak.
- **Git/run state:** branch `codex/control-plane-quarantine`, HEAD vẫn
  `502ffb8cf8b541ee74af30194aff2dce08c3b649`; worktree dirty gồm source/test/
  docs, `.coding-tools/orchestration/ledger.sqlite3` và `var/` chưa track.
  Không commit, push, deploy, restart hoặc gọi provider trả phí.
- **Next action chính xác:** mở rộng contract/admission cho `exec_poll` và
  `exec_stop` với `command_id`, `consumer_id`, `yield_time_ms`, `signal`,
  `wait_ms`; thêm `_resume_running_exec_entries()` và stop acknowledgment;
  sau đó chạy fault tests mismatch device/endpoint/workspace/generation,
  running → poll → terminal, stop/pending/quiescence và crash/mất ACK trước
  khi nâng G3 lên PASS.

**Bước tiếp theo chính xác:** hoàn thiện `exec_poll`/`exec_stop`/resume và
fault/reconcile trên exact Job/RUN/WAVE của G3-A; bổ sung mismatch,
running→terminal, stop/quiescence và crash/mất ACK tests. Sau đó nối writer
handoff/observe của G4 với hai ChatGPT client thật, chuyển policy local khỏi
TTL context, rồi mới chạy packaged/live T01–T16 và soak. Không bật lại
direct-Popen làm đường sản phẩm và không kéo dài policy pilot để giả lập quyền
thường trực.

### Checkpoint G3-B — Job lifecycle `poll/stop/resume`, 20-09-2026, 18:33 +07

Wave này đã hoàn thành phần lifecycle source/focused proof bị bỏ ngỏ ở G3-A;
chưa bật quyền trên máy thật và **chưa đóng G3 product gate**.

- **Runtime bridge:** `controlPlaneExecBridge.js` và
  `RuntimeOrchestrator.controlPlaneExec()` nhận đủ `exec_run`, `exec_poll`,
  `exec_stop`. `exec_run` gọi `exec_command`; hai operation còn lại chỉ gọi
  `command_control` với cùng `command_id`/`job_id`/`local_handle` và không mang
  argv mới. Kết quả chuẩn hóa `running`, `exited`, `terminated`, `timeout`,
  `stopped`, `reconciled_terminal` và giữ `run_id`/`wave_id`.
- **Node continuity:** `node_agent.py` có `_resume_running_exec_entries()`,
  `_poll_exec_stop_requests()` và `_control_bridge_observation()`. Journal đọc
  Job `running` trước khi dequeue action mới; chỉ ghi terminal receipt và gọi
  stop-ack sau terminal evidence. Stop/poll được kiểm tra lại target, policy
  digest, contract, workspace và handle; policy disabled vẫn default-deny.
- **Regression/focused proof:** runtime/bridge **9/9 PASS**; Python
  `test_exec_node_agent` **14/14 PASS**, gồm `running → poll → terminal`,
  `poll → running → stop → stopped → acknowledge`, và no-respawn sau journal;
  Python control-plane **226/226 PASS**; Node **855 tests, 839 PASS / 16 SKIP /
  0 FAIL**. Không có test nào tự cấp local policy hoặc gọi provider trả phí.
- **Sửa lỗi trong wave:** đồng bộ exact envelope fields trong fixtures và bổ
  sung `operation=exec_run` ở request tạo từ action; đây là lỗi contract/test
  đã phát hiện, không phải nới lỏng admission.
- **Còn thiếu:** policy thường trực không phụ thuộc TTL/context; fault trên
  Recovery IPC/MCP process, network/full-disk/DB-busy và rotation mất ACK; test
  Windows packaged/live, hai client ChatGPT thật, write/build/test/deploy và
  soak 24 giờ. `_run_bounded_exec` vẫn chỉ compatibility/focused helper.
- **Git/run state:** branch `codex/control-plane-quarantine`, HEAD
  `502ffb8cf8b541ee74af30194aff2dce08c3b649`; worktree vẫn dirty, có
  `.coding-tools/orchestration/ledger.sqlite3` modified và `var/` untracked.
  Chưa commit, push, deploy, restart hoặc gọi provider trả phí.
- **Next action chính xác:** tách policy exec standing khỏi read-only TTL theo
  một migration có version/reconcile; sau đó chạy fault/package/live gate T01,
  T04, T06, T07, T12–T16 trên exact build. Nếu live gate chưa được cấp target
  và thời gian, giữ trạng thái `SOURCE/FOCUSED_PROOF`, không đánh dấu PASS.

### Checkpoint G3-C — standing exec policy, 20-09-2026, 18:48–18:50 +07

Wave này đã tách TTL của **local exec authority** khỏi context/pilot read-only ở
source; không tự bật quyền trên máy thật và không thay đổi các policy file-read /
approved-patch còn đang được dùng cho compatibility.

- **Đã thay đổi:** `control-plane/node_agent.py` cài policy exec
  `schema_version=2`, `authority_mode=standing`, `expires_at_ms=null`. CLI
  `install-exec-policy` không còn nhận expiry như một quyền hợp lệ; nếu caller
  vẫn truyền `--expires-at-ms` thì trả lỗi migration có kiểu rõ ràng. `inspect-
  exec-policy` trả `authority_mode`; `disable-exec-policy` vẫn là nút thu hồi
  local rõ ràng.
- **Tương thích có giới hạn:** policy exec schema 1 được đọc như
  `expiring_legacy` để migration/revoke an toàn và vẫn hết hạn đúng hạn. Không
  kéo dài policy v1 hoặc ẩn expiry để giả lập standing authority.
- **Boundary giữ nguyên:** `exec_run` vẫn bắt `action.expires_at_ms` để chống
  replay trong queue; `exec_poll`/`exec_stop` chỉ phục hồi Job đã ghi journal,
  không tạo process mới sau TTL. Mọi request vẫn kiểm tra enabled, owner,
  device, endpoint, workspace/generation, server origin, facade contract,
  allowlist `argv`, giới hạn timeout/output và handle/Job exact.
- **Validation mạnh nhất:** Node bridge/CJS/runtime **11/11 PASS**; approved-
  patch bridge/runtime **9/9 PASS**; Python exec node-agent **14/14 PASS**;
  Python MCP exec + OAuth + HTTP API **68/68 PASS**; full control-plane
  discovery **226/226 PASS**; Node full **857 tests: 841 PASS / 16 SKIP /
  0 FAIL**; `py_compile`, `node --check`, `git diff --check` **PASS**.
  Targeted `test_wave_a_runtime.py` vẫn **11/12 PASS**, với một lỗi import
  standalone Landlock helper của Linux harness; lỗi này không được tính là
  bridge relay proof.
- **Git/run state:** branch `codex/control-plane-quarantine`, HEAD
  `502ffb8cf8b541ee74af30194aff2dce08c3b649`; worktree vẫn dirty với các source,
  test, docs, `.coding-tools/orchestration/ledger.sqlite3` và `var/` untracked.
  Wave tài liệu không commit, push, deploy, restart service hoặc gọi provider
  trả phí.
- **Blocker còn lại:** chưa có Ubuntu live schema 21/exec policy v2, Windows
  packaged/live process proof, ChatGPT thật trên hai client cùng principal,
  fault/mất ACK/reboot/DB-busy, protected secret store/rotation crash, standing
  write/file/patch end-to-end hoặc soak 24 giờ. Vì vậy G3-C chỉ là
  `SOURCE/FOCUSED/FULL_TEST_PROOF`, chưa phải `LIVE_PASS`.
- **Next action chính xác:** chạy fault/reconcile trên Recovery IPC/MCP thật
  (mismatch target/generation, mất ACK sau spawn/kill, restart khi Job running),
  sau đó nối standing scope của file/write/patch và presence. Chỉ khi exact
  Windows package + Ubuntu service + hai ChatGPT client được cấp target/window
  mới chạy T01–T16, rotation/revoke và soak ≥24 giờ.

### Checkpoint G3-D — standing file-read/approved-patch policy, 20-09-2026

Wave này hoàn tất phần source/fixture còn bị mô tả sai là TTL-only: local
file-read và approved-patch policy giờ có authority standing v2 độc lập với
compact read-only/context pilot. Wave không tự bật quyền trên máy thật, không
đổi allowlist/path/capability thành unrestricted và không thay thế action TTL
trung tâm chống replay.

- **Đã thay đổi:** `control-plane/node_agent.py` chấp nhận schema v2 cho
  file-read và approved-patch với `authority_mode=standing` và
  `expires_at_ms=null`. CLI cài policy không truyền `--expires-at-ms` sẽ cài
  standing policy; truyền expiry vẫn là compatibility path legacy v1 và không
  được dùng để giả lập quyền standing. `inspect` phân biệt `standing` với
  `expiring_legacy`; `disable` là nút thu hồi local rõ ràng.
- **Đã thay đổi:**
  `controlPlaneFileReadBridge.js` và `controlPlaneApprovedPatchBridge.js` đọc,
  chuẩn hóa và admission cả v2 standing lẫn v1 legacy. Standing policy không
  bị từ chối chỉ vì policy expiry đã qua, nhưng mỗi action/request vẫn phải có
  TTL riêng; target, device, endpoint, workspace/generation, facade contract,
  enabled, allowlist và giới hạn dữ liệu vẫn được kiểm lại trước effect.
- **Ranh giới không đổi:** compact `read_only`/context policy vẫn là pilot có
  expiry và không được dùng làm thủ tục cấp quyền hàng ngày của trusted
  workspace. Standing file-read/approved-patch cũng chưa chứng minh quyền write
  khác, quyền OS, secret store, package/live process hay deployment.
- **Validation mạnh nhất:** Python control-plane discovery **232/232 PASS**;
  Python file-read + approved-patch focused **20/20 PASS**; Python exec-focused
  **16/16 PASS**; Node bridge/CJS/runtime **11/11 PASS**; approved-patch
  bridge/runtime **9/9 PASS**; full Node **859 tests: 843 PASS / 16 SKIP / 0
  FAIL**; `py_compile`, `node --check` và `git diff --check` **PASS**.
- **Ý nghĩa bằng chứng:** đây là `SOURCE/FOCUSED/FULL_TEST_PROOF` trên
  working tree. Không nâng thành Ubuntu live schema 21, Windows packaged/live,
  ChatGPT thật trên hai client, Recovery fault/reconcile, rotation crash hoặc
  soak 24 giờ.
- **Git/run state:** branch `codex/control-plane-quarantine`, HEAD
  `502ffb8cf8b541ee74af30194aff2dce08c3b649`; worktree vẫn dirty với source,
  test, docs, `.coding-tools/orchestration/ledger.sqlite3` và `var/` untracked.
  Chưa commit, push, deploy, restart service hoặc gọi provider trả phí.
- **Next action chính xác:** chạy fault/reconcile trên Recovery IPC/MCP thật;
  nối standing scope vào các write path còn lại và presence; sau đó mới chạy
  exact Ubuntu/Windows package, hai ChatGPT client cùng principal, T01–T16,
  rotation/revoke và soak ≥24 giờ.

### Checkpoint G3-E — fault/reconcile journal proof, 20-09-2026

Wave này bổ sung oracle cho các boundary mà G3-D vẫn chưa chứng minh: bridge
timeout sau khi đã ghi `prepared`, mất kết nối khi Job đang `running`, stop
request chưa thể kill/ACK, và mất ACK khi gửi terminal receipt. Không thay đổi
quyền live, không gọi process thật qua Recovery IPC trong test, và không biến
timeout thành retry effect.

- **Đã kiểm chứng:** sau timeout ở boundary `prepared`, node ghi `unknown` và
  không gọi direct-Popen hoặc spawn lần hai; lần poll sau chỉ quan sát journal
  đã terminal.
- **Đã kiểm chứng:** khi poll Job `running` gặp timeout, journal giữ `running`
  cùng `last_control_error`; lần sau mới dùng đúng `local_handle` để lấy terminal
  evidence, không tạo Job mới.
- **Đã kiểm chứng:** stop timeout giữ trạng thái pending/running và không gọi
  endpoint acknowledge; chỉ sau kết quả `stopped` mới gửi stop ACK.
- **Đã kiểm chứng:** nếu terminal receipt đã ghi bền vững nhưng ACK mạng mất,
  lần chạy sau gửi lại đúng payload từ journal, không relay lại Job.
- **Validation:** `test_exec_node_agent` **20/20 PASS**; full control-plane
  discovery **236/236 PASS**; `py_compile` và `git diff --check` **PASS**.
  Đây là source/focused fault proof; chưa phải Recovery IPC/MCP process thật,
  Windows packaged/live hay network/DB-busy/full-disk proof.
- **Git/run state:** branch `codex/control-plane-quarantine`, HEAD
  `502ffb8cf8b541ee74af30194aff2dce08c3b649`; worktree vẫn dirty với source,
  test, docs, `.coding-tools/orchestration/ledger.sqlite3` và `var/` untracked.
  Chưa commit, push, deploy, restart service hoặc gọi provider trả phí.
- **Next action chính xác:** dựng fault harness qua Recovery IPC/MCP thật (mismatch
  target/generation, mất ACK sau spawn/kill, restart khi Job running), rồi đóng
  protected secret store/rotation crash trước packaged/two-client/T01–T16.

### Checkpoint G3-F — capability workspace không còn hardcode read-only, 20-09-2026

Wave này sửa đúng nút thắt giữa contract trusted workspace và onboarding Electron:
node-agent/server đã nhận `read/write/exec` từ các wave trước, nhưng UI và IPC
Electron vẫn luôn đăng ký `{read:true, write:false, exec:false}`. Sau wave này,
chủ máy chọn capability một lần cho từng root trước khi bind; mặc định vẫn là
read-only an toàn và capability `read` luôn bắt buộc.

- **Đã thay đổi:** `controlPlaneEnrollment.normalizeWorkspaceCapabilities()` kiểm
  schema exact gồm đúng ba khóa và boolean; `registerWorkspace()` truyền
  `--capability-write`/`--capability-exec` khi được chọn; receipt/list/retire vẫn
  parse và hiển thị capability thật. `electron/main.js` chuyển nguyên request
  capability từ IPC vào service, không đưa raw path hay secret lên Ubuntu.
- **Đã thay đổi:** `renderer/index.html` có picker Đọc/Ghi/Chạy; `renderer/app.js`
  giữ state capability riêng, truyền capability khi đăng ký và hiển thị inventory
  `read/write/exec` thay vì gắn nhãn mọi root là Read-only. Đăng ký vẫn chỉ là
  inventory opaque; không tự đổi workspace chính, tạo binding, cấp context hay
  vượt quyền Windows/OS. Policy local standing và writer/target/generation fence
  vẫn là boundary bắt buộc ở bước thực thi.
- **Test/proof:** `tests/control-plane-enrollment.test.js` thêm full capability,
  CLI flag propagation, default và malformed/extra/non-boolean/read=false cases;
  `tests/control-center-manager.test.js` cập nhật contract UI. Focused Node
  `control-plane-enrollment + control-center-manager` **23/23 PASS**;
  `node --check` cho `controlPlaneEnrollment.js`, `main.js`, `app.js` và
  `git diff --check` **PASS**.
- **Mức bằng chứng:** `SOURCE_PRESENT + FOCUSED_TEST_PROOF`. Chưa chứng minh
  packaged Windows UI, Ubuntu schema 21 live, capability migration trên máy đã
  đăng ký, ChatGPT hai client cùng principal, hay write/Git/build/test/deploy
  end-to-end. Capability write/exec được quảng cáo là local ceiling, không phải
  server tự cấp quyền và không biến tài khoản Windows thành Administrator.
- **Git/run state:** vẫn branch `codex/control-plane-quarantine`, HEAD
  `502ffb8cf8b541ee74af30194aff2dce08c3b649`; worktree dirty do các thay đổi đã
  có, `.coding-tools/orchestration/ledger.sqlite3` modified và `var/` untracked.
  Wave này không commit, push, deploy, restart service hay gọi provider trả phí.
- **Next action chính xác:** làm migration/replace UX cho root đã đăng ký khác
  capability (không âm thầm ghi đè generation), nối standing capability vào các
  write path còn lại, rồi chạy exact package/live gates T01/T04/T06/T07/T12–T16.

### Checkpoint G3-G — thay capability workspace có xác nhận và retry journal, 20-09-2026

Wave này đã đóng khoảng trống mà G3-F còn để lại: capability picker không còn
chỉ đăng ký lần đầu mà có một đường thay thế rõ ràng cho workspace đã tồn tại.
Thay đổi giữ nguyên `workspace_id` và canonical path cục bộ, nhưng luôn tạo
`workspace_generation` mới; generation cũ được retire ở Ubuntu trước khi local
registry chuyển sang entry mới.

- **Đã thay đổi ở node-agent:** thêm CLI/service `replace-workspace` với
  `--confirm-replace`; tạo generation mới; gửi retire đúng
  `{device_id, workspace_id, old_generation}` rồi mới register generation mới;
  vô hiệu policy read/file-read/approved-patch/exec cũ sau receipt retire hợp lệ;
  chỉ commit registry local sau receipt register mới hợp lệ. `retire-workspace`
  cũng vô hiệu exec policy cũ.
- **Đã thay đổi về phục hồi:** journal cạnh config chỉ lưu phase và ID không
  chứa secret (`planned` → `retire_sent` → `retired` → `register_sent`);
  retry sau mất ACK hoặc crash tiếp tục phase hiện tại, không retire/register
  trùng. Response register phải khớp đúng device/workspace/generation và không
  được ghi đè bởi entry local cũ trong race.
- **Đã thay đổi ở Electron/UI:** thêm parser receipt, service
  `replaceWorkspace()`, IPC/preload `control-plane:replace-workspace`, nút
  “Thay capability” và xác nhận old → new. UI cảnh báo binding/task generation
  cũ bị fence và phải bind lại ID mới. Capability mới chỉ là local ceiling; không
  biến tài khoản Windows thành Administrator.
- **Test/proof:** `control-plane/tests/test_workspace_replacement.py`
  **3/3 PASS** (thành công, mất ACK khi register và yêu cầu confirmation);
  enrollment/manager **24/24 PASS**; full control-plane **239/239 PASS**;
  full Node **862 tests: 846 PASS / 16 SKIP / 0 FAIL**; `node --check` và
  `git diff --check` PASS. Đây là `SOURCE_PRESENT + FOCUSED/FULL_TEST_PROOF`,
  chưa phải evidence Ubuntu live, Windows packaged/live hay hai client ChatGPT.
- **Git/run state:** branch `codex/control-plane-quarantine`, HEAD vẫn
  `502ffb8cf8b541ee74af30194aff2dce08c3b649`; worktree dirty gồm source, tests,
  docs, `.coding-tools/orchestration/ledger.sqlite3` và `var/` untracked. Wave
  này không commit, push, deploy, restart service hay gọi provider trả phí.
- **Next action chính xác:** chạy fault harness qua Recovery IPC/MCP process thật;
  nối standing capability vào write paths còn lại; hoàn tất protected Windows
  secret store và rotation crash; sau đó mới chạy exact package/Ubuntu schema 21,
  hai ChatGPT client cùng principal, T01/T04/T06/T07/T12–T16 và soak ≥24 giờ.

### Checkpoint G3-H — Recovery bridge fail-closed fault oracles, 20-09-2026

Wave này bổ sung hai oracle còn thiếu ở boundary descriptor-hiding CJS bridge:
bridge phải dừng trước IPC nếu installation identity không khớp, và phải truyền
ra lỗi IPC có mã kiểu mà không làm lộ descriptor/token. Đây là bằng chứng
fail-closed ở source/test; nó không thay thế fault trên Recovery Host/MCP process
thật, network thật hoặc packaged Windows.

- **Đã thay đổi:** `control-plane/tests/recovery_exec_bridge.test.cjs` kiểm tra
  mismatch identity không tạo IPC call và kiểm tra `RECOVERY_IPC_TIMEOUT` được
  giữ nguyên như typed failure.
- **Validation:** nhóm bridge/CJS/runtime (`control-plane/tests/recovery_exec_bridge.test.cjs`,
  `tests/control-plane-exec-bridge.test.js`, `tests/control-plane-exec-runtime.test.js`)
  chạy **13/13 PASS**; full Node vẫn **862 tests: 846 PASS / 16 SKIP / 0 FAIL**;
  `node --check` và `git diff --check` PASS.
- **Mức bằng chứng:** `FOCUSED_TEST_PROOF` cho installation mismatch, descriptor
  hiding và typed IPC failure. Chưa nâng T07/T13/T16 hoặc G3 product gate; chưa
  có process-fault receipt, protected secret-store/rotation, packaged/live,
  hai client ChatGPT hay E2E read/write/Git/build/test/deploy.
- **Kiểm tra runtime chỉ-đọc:** `npm run dev:status` trong shell hiện tại trả
  `DEV_UI_APPDATA_UNAVAILABLE` vì môi trường Linux không có `APPDATA`; đây là
  giới hạn môi trường quan sát, không phải live Windows failure và không nâng
  hoặc hạ mức bằng chứng của G3.
- **Next action chính xác:** chạy fault/reconcile qua Recovery IPC/MCP process
  thật trên exact package; nếu chưa có target Windows/live thì tiếp tục đóng
  protected secret-store/rotation fixture và standing write-path proof, rồi cập
  nhật receipt mới mà không gộp source proof thành live proof.

### Checkpoint G4-A — hai client OAuth cùng principal dùng chung binding/task, 20-09-2026

Wave này bổ sung oracle sát với contract account chung: hai access token khác
nhau được verifier ánh xạ vào cùng một OAuth principal. Cả hai client đều thấy
cùng inventory `binding_id`; client A mở task, client B replay cùng idempotency
key nhận đúng `task_id` và observe task qua `task_control`. Projection quan sát
không chứa `node_secret` hoặc `arguments_json`.

- **Đã thay đổi:** `_StaticVerifier` trong `control-plane/tests/test_mcp_oauth.py`
  hỗ trợ mapping token → identity để mô phỏng hai client mà không copy cookie,
  node credential hay context. Test chạy qua OAuth MCP HTTP ingress có
  `file_read_enabled`, đúng feature gate của task sessions.
- **Validation:** test `test_two_clients_same_oauth_principal_share_binding_and_observe_one_task`
  **1/1 PASS**; full control-plane discovery **240/240 PASS**; các lane Node
  trước đó giữ **862 tests: 846 PASS / 16 SKIP / 0 FAIL**.
- **Mức bằng chứng:** `FOCUSED_TEST_PROOF` cho account→binding→task lineage và
  redacted observe giữa hai token cùng principal. Chưa phải hai ChatGPT client
  thật, OAuth/IdP live, writer handoff trên Job thật, Windows packaged hay
  read/write/Git/build/test/deploy E2E.
- **Next action chính xác:** chạy cùng scenario trên hai client ChatGPT thật
  sau khi có exact Ubuntu/Windows target; tiếp tục kiểm writer lease takeover,
  stop/handoff và duplicate-effect khi một client mất ACK.

### Checkpoint G4-B — writer handoff giữa hai client qua OAuth HTTP, 20-09-2026

Wave này đã thực hiện phần source/focused tiếp theo của G4-A trên đúng ingress
HTTP, không chỉ gọi store hoặc facade trực tiếp. Hai access token khác nhau vẫn
được verifier ánh xạ vào cùng OAuth principal và cùng `binding_id`:

1. client A mở task A và `writer_claim` thành công;
2. client B mở task B trên cùng binding nhưng `writer_claim` nhận `CONFLICT`
   vì lease của task A còn giữ;
3. client A `writer_release` với lý do handoff;
4. client B `writer_claim` thành công, nhận lease mới của task B;
5. receipt trả về không chứa `node_secret` hay `arguments_json`.

**Đã thay đổi:** thêm test
`test_two_clients_same_oauth_principal_handoff_writer_lease_over_http` trong
`control-plane/tests/test_mcp_oauth.py`. Test đi qua `ControlPlaneHttpServer`
và OAuth MCP ingress thật của fixture. `lease_generation` là monotonic theo
từng `task_id`; `task_id` đồng thời được seal vào action/intent nên task mới có
thể bắt đầu ở generation 1 mà không thừa hưởng authority của task cũ.

**Validation:** test G4-B **1/1 PASS**; toàn bộ OAuth class **22/22 PASS**;
full control-plane discovery **241/241 PASS**; `git diff --check` PASS.
Các cảnh báo `ResourceWarning` về connection SQLite chưa đóng trong full
discovery được ghi nhận là hygiene warning với exit code 0, không phải test
failure hay live proof.

**Mức bằng chứng:** `FOCUSED_TEST_PROOF` cho account → binding → task →
writer serialization/handoff qua HTTP. Chưa phải hai ChatGPT client thật,
OAuth/IdP live, writer takeover trên Job thật, stop/reconcile sau mất ACK,
Windows packaged/live hay E2E read/write/Git/build/test/deploy.

**Next action chính xác:** nối writer lease vào một Job local thật để kiểm
claim-before-dispatch, stop/terminal receipt, mất ACK và duplicate-effect;
sau đó chạy fault/reconcile qua Recovery IPC/MCP process thật. Khi có target
Windows/Ubuntu và cửa sổ vận hành được cấp, chạy T01/T04/T06/T07/T12–T16 trên
exact package rồi mở soak ≥24 giờ.

### Checkpoint G4-C — lease chặn exec trước dispatch qua OAuth HTTP, 20-09-2026

Wave này đã kiểm tra writer lease ở mutation path thay vì chỉ kiểm tra
`task_control`. Với cùng principal và cùng `binding_id`, client A claim task A;
client B mở task B rồi gọi `exec_run`. Central trả `CONFLICT` ngay tại bước
claim-before-dispatch, trước khi tạo `context`, `work_request` hoặc `action`.
Sau khi A release, client B lặp lại cùng idempotency key và action được queue
đúng task B với `writer_lease_generation` được lưu trong exec intent.

**Đã thay đổi:** thêm test
`test_writer_lease_blocks_cross_client_exec_before_dispatch_over_http` trong
`control-plane/tests/test_mcp_oauth.py`; fixture bật đầy đủ OAuth exec contract
và workspace capability `exec=true`. Test dùng `ControlPlaneHttpServer` thật,
kiểm tra count durable không tăng ở lần bị chặn, rồi kiểm tra action queued và
intent `{task_id, writer_lease_generation}` sau handoff.

**Validation:** G4-C **1/1 PASS**; toàn bộ OAuth class **23/23 PASS**; full
control-plane discovery **242/242 PASS**; Python exec + OAuth + HTTP API
**7/7 + 23/23 + 41/41 = 71/71 PASS**; `py_compile` và `git diff --check`
PASS. Full discovery vẫn có `ResourceWarning` về SQLite connection chưa đóng,
exit code 0 và không có failure; đây là hygiene backlog riêng.

**Mức bằng chứng:** `FOCUSED_TEST_PROOF` cho claim-before-dispatch và không
tạo durable effect khi lease bị giữ. Chưa chứng minh process local đã spawn,
Job/RUN/WAVE terminal receipt, stop quiescence, mất ACK/duplicate-effect trên
Recovery process thật, packaged/live Windows hay ChatGPT thật.

**Next action chính xác:** đưa cùng `task_id` + generation qua một Job local
thật, kiểm tra action A chạy/stop/terminal rồi mới cho B claim; thêm fault
oracle mất ACK trước/sau spawn và reconcile để chứng minh không lặp effect.

### Checkpoint G4-D — terminal receipt fence trước writer handoff, 20-09-2026

Wave này kiểm tra boundary sau dispatch ở central store. Task A queue một
`exec_run`, node heartbeat đạt trạng thái dispatchable và `poll_actions` tạo
`dispatch_unconfirmed`. Khi chưa có kết quả cuối, `writer_release` của task A
bị từ chối vì còn `unresolved dispatched action`; task B chưa thể nhận quyền.
Sau `record_receipt(..., receipt_state="completed")`, action chuyển sang
`settled`, task A release thành công và task B mới claim được writer lease.

**Đã thay đổi:** thêm test
`test_dispatched_exec_keeps_writer_lease_until_terminal_receipt` trong
`control-plane/tests/test_mcp_exec.py`. Test kiểm tra cả attempt/receipt
lineage, không chỉ trạng thái lease trong memory. Nó chứng minh central không
cho phép handoff mù sau khi đã có khả năng tạo effect.

**Validation:** G4-D **1/1 PASS**; MCP exec class **8/8 PASS**; full
control-plane discovery **243/243 PASS**; tổng Python exec + OAuth + HTTP API
**8/8 + 23/23 + 41/41 = 72/72 PASS**; `py_compile` và `git diff --check`
PASS. Full discovery vẫn phát `ResourceWarning` về connection SQLite chưa
đóng (exit code 0, không test failure); giữ đây là hygiene backlog riêng.

**Mức bằng chứng:** `FOCUSED_TEST_PROOF` cho durable dispatch → terminal
receipt → writer handoff. Chưa phải local Windows Job/RUN/WAVE thật, Recovery
IPC process fault, stop quiescence, lost-ACK/duplicate-effect, packaged/live
activation hay hai ChatGPT client thật.

**Next action chính xác:** ghép central attempt/receipt này với exact local
Recovery/RuntimeOrchestrator Job handle; chạy stop trước/sau terminal, mất ACK
trước/sau spawn và reconcile receipt, rồi mới đánh giá writer takeover live.

### Checkpoint G4-E — HTTP→node exec journal và terminal MCP status, 20-09-2026

Wave này đóng gate source/focused gần nhất trên đúng đường người dùng sẽ đi:

1. OAuth MCP mở task và claim writer lease qua `ControlPlaneHttpServer` thật;
2. `exec_run` queue đúng `binding_id`, `task_id` và generation;
3. node heartbeat thật làm central coi node dispatchable;
4. `poll_exec_once` lấy action qua node-authenticated HTTP, đọc standing exec
   policy, ghi journal `prepared`, gọi bridge hẹp và gửi receipt `accepted`;
5. lần poll sau đọc đúng local handle từ journal, gọi `exec_poll` (không spawn
   lại), ghi receipt terminal và để MCP trả `exec_status`/`exec_output` đã verify.

Đã sửa một lỗi thực tế ở boundary này: kết quả terminal từ `exec_poll` trước
đó không có `output_bytes`, khiến `_completed_exec_relay` bỏ qua receipt hợp lệ
và báo `local_admission_pending_or_running` dù action đã settled. Node agent giờ
tính lại byte count sau khi validate mọi control result; test E2E giữ regression
cho cả receipt accepted, terminal receipt, command/job/run/wave correlation,
journal replay và không lộ node secret, policy digest hoặc local path.

**Đã thay đổi:** thêm
`control-plane/tests/test_mcp_exec_http_node_e2e.py` và sửa
`_control_bridge_observation` trong `control-plane/control_plane/node_agent.py`.
Bridge Recovery/Electron được mock hẹp có chủ đích; central queue, OAuth
facade, heartbeat/poll HTTP, local policy admission, journal, receipt store và
MCP status/output đều chạy thật trong fixture.

**Validation:** E2E G4-E **1/1 PASS**; regression lane liên quan **96/96 PASS**;
full control-plane discovery **244/244 PASS**; `py_compile` và
`git diff --check` PASS. Một số `ResourceWarning` SQLite vẫn xuất hiện trong
full discovery nhưng exit code 0 và không có test failure.

**Mức bằng chứng:** `FOCUSED_TEST_PROOF` cho central→node exec relay và
terminal status; chưa phải Recovery IPC/MCP process thật, Windows Job thật,
packaged/live activation, hai ChatGPT client thật hay deployment/soak.

**Next action chính xác:** thay bridge mock bằng fixture Recovery/Electron
process thật trên exact package, rồi chạy stop trước/sau terminal, lost-ACK
trước/sau spawn, duplicate-effect/reconcile và writer handoff trên Job/RUN/WAVE.

### Checkpoint G4-F — Recovery process thật cho exec/stop và terminal stopped receipt, 20-09-2026

Wave này đã thay phần bridge mock hẹp của G4-E bằng một Node process fixture
riêng sở hữu `RecoveryIpcServer` thật, `RecoveryHost.prototype.controlPlaneExec`
thật và `RuntimeOrchestrator.controlPlaneExec()` thật. Fixture dùng Coding Tools
MCP HTTP peer deterministic chỉ cho health, bind, `exec_command` và
`command_control`; nó ghi lại sequence mà không đưa descriptor/token/path ra
Python test.

- `exec_run` tạo đúng một local command và trả `running` kèm `local_handle`;
  poll lần sau đọc journal `running`, gọi `exec_poll` qua Recovery IPC và không
  spawn lại command.
- `exec_stop` trước hết vẫn là `pending`; sau khi Recovery gọi
  `command_control(kill)` và trả status terminal, node ghi receipt `stopped`
  rồi mới gửi stop ACK. Sequence fixture được kiểm tra là
  `bind → exec_run → bind → poll → bind → kill`, recovery calls là
  `exec_run → exec_poll → exec_stop`.
- Sửa product boundary trong `store.py`: thêm `stopped` vào
  `TERMINAL_RECEIPT_STATES`, để receipt stop được settle action thay vì bị HTTP
  400. Đây là lỗi thật được phát hiện bởi process fixture, không phải nới lỏng
  test.
- Teardown fixture đóng `stderr` pipe; E2E không còn warning pipe chưa đóng.

**Đã thay đổi:**
`tests/recovery-exec-process-fixture.cjs`,
`control-plane/tests/test_mcp_exec_http_node_e2e.py`,
`control-plane/control_plane/store.py`.

**Validation:** G4-F HTTP→Recovery process exec/stop **2/2 PASS**;
`test_mcp_exec` **8/8 PASS**; `test_store` **80/80 PASS**; `node --check`
fixture/bridge, `py_compile` và `git diff --check` PASS. Đây là
`FOCUSED_TEST_PROOF` cho Recovery process boundary và terminal stop receipt;
chưa phải Windows packaged/live, ChatGPT thật trên hai client, lost-ACK sau
spawn, duplicate-effect/reconcile hoặc soak.

**Next action chính xác:** thêm fault injection tại các điểm sau `exec_run`,
trước/sau receipt ACK và khi Recovery/MCP process mất kết nối; chứng minh
unknown/reconcile không chạy lại effect, sau đó mới chạy writer handoff trên
Job thật và packaged Windows.

### Checkpoint G4-G — persist running projection trước receipt ACK, 20-09-2026

Wave fault đầu tiên đã tìm thấy một lỗi có thể làm mất khả năng tiếp tục Job:
nhánh `exec_run` ghi receipt `accepted` vào journal trước, nhưng chỉ bổ sung
`request`, `policy_sha256` và `result` sau đó. Nếu central đã commit receipt mà
phản hồi/ACK mất, process node restart/poll sau sẽ thấy entry `running` thiếu
đầu vào để gọi `exec_poll`, rồi có nguy cơ chuyển effect đang chạy thành
`unknown`.

- `node_agent.py` giờ ghi atomic **đầy đủ running projection** — request, policy
  digest, result/local handle và receipt — trước khi gửi receipt qua network.
- Fault E2E làm central commit `accepted` nhưng cố ý bỏ ACK ở phía node. Poll
  tiếp theo replay đúng receipt (central trả replay), đọc cùng local handle và
  gọi `exec_poll`; sequence local vẫn chỉ là
  `bind → exec_run → bind → poll`, không có `exec_run` thứ hai.
- Central action kết thúc `settled` với đúng hai receipt `accepted`,
  `completed`; test cũng kiểm tra recovery calls chỉ gồm `exec_run`,
  `exec_poll`.

**Đã thay đổi:**
`control-plane/control_plane/node_agent.py` và
`control-plane/tests/test_mcp_exec_http_node_e2e.py` (thêm helper queue task và
fault test `test_oauth_exec_replays_lost_accepted_receipt_without_respawn`).

**Validation:** fault E2E mới **1/1 PASS**; toàn bộ HTTP→Recovery exec/stop/lost-
ACK E2E **3/3 PASS**; `test_exec_node_agent` **20/20 PASS**; `test_mcp_faults` +
`test_store` **85/85 PASS**; `test_mcp_exec` **8/8 PASS**. Đây là
`FOCUSED_TEST_PROOF` cho ACK loss sau central accepted; chưa chứng minh mất ACK
ở mọi boundary, Recovery disconnect/duplicate-effect/reconcile đầy đủ,
packaged/live Windows hay ChatGPT hai client thật.

**Next action chính xác:** bổ sung fault khi Recovery/MCP mất kết nối sau
`exec_run` nhưng trước kết quả, và khi terminal receipt ACK mất; mỗi case phải
phân biệt `running`, `unknown/reconcile` và terminal, không re-execute effect.

### Checkpoint G4-H — MCP disconnect sau exec_run → unknown/reconcile, 20-09-2026

Wave này đưa fault vào đúng process fixture Recovery/MCP. MCP peer nhận request
`exec_command`, ghi observation `exec_run`, rồi đóng socket trước khi trả kết
quả. Node không được suy diễn đây là success hoặc stopped.

- Node ghi một receipt `unknown` với `reconciliation_required=true`; central
  chuyển action sang `reconcile_required`.
- Lần poll sau chỉ đọc/replay journal đã terminal-unknown, không gọi lại
  `exec_run`, không gọi `exec_poll` và không tạo attempt mới. Sequence được
  kiểm tra là `bind → exec_run`, Recovery call chỉ có `exec_run`.
- Đây là trạng thái an toàn và trung thực: effect local có thể đã bắt đầu nhưng
  kết quả không biết; operator/reconcile phải xử lý trước retry. Không coi
  `unknown` là lỗi permission hay terminal failure.

**Đã thay đổi:**
`tests/recovery-exec-process-fixture.cjs` hỗ trợ `drop_after_exec_run`, và
`control-plane/tests/test_mcp_exec_http_node_e2e.py` thêm test
`test_oauth_exec_mcp_disconnect_becomes_unknown_without_retry`.

**Validation:** HTTP→Recovery exec/stop/lost-ACK/disconnect E2E **4/4 PASS**;
fixture/bridge `node --check`, `py_compile` và `git diff --check` PASS. Đây là
`FOCUSED_TEST_PROOF` cho một MCP disconnect sau dispatch; chưa bao phủ mất ACK
terminal, Recovery IPC crash, duplicate-effect ở mọi boundary, packaged/live
Windows, hai ChatGPT client thật hoặc soak.

**Next action chính xác:** thêm terminal receipt ACK-loss và Recovery IPC process
crash/restart fixtures; giữ nguyên nguyên tắc unknown không được tự redeliver,
sau đó nối writer handoff vào Job/RUN/WAVE thật.

### Checkpoint G4-I — terminal receipt ACK-loss replay không relay lại Job, 20-09-2026

Wave này kiểm tra nửa còn lại của receipt durability trên cùng Recovery process
fixture. Job đã chạy qua `exec_run`, poll sau nhận terminal result và central đã
settle `completed`; test cố ý bỏ phản hồi sau khi central ghi terminal receipt.

- Node journal giữ `state=completed` và `receipt_submitted=false` cùng payload
  terminal bất biến.
- Poll tiếp theo gửi lại đúng payload; central trả replay, không gọi lại
  `exec_run` hoặc `exec_poll`, không tạo attempt/Job mới. Sequence vẫn là
  `bind → exec_run → bind → poll`.
- Phân biệt rõ với G4-H: G4-H là effect không biết kết quả nên phải
  `unknown/reconcile`; G4-I đã có terminal evidence nên chỉ cần replay ACK.

**Đã thay đổi:**
`control-plane/tests/test_mcp_exec_http_node_e2e.py` thêm test
`test_oauth_exec_replays_lost_terminal_receipt_ack_without_relay`.

**Validation:** HTTP→Recovery exec/stop/lost-ACK/disconnect/terminal-ACK E2E
**5/5 PASS**; `test_exec_node_agent` **20/20 PASS**; `py_compile`, `node --check`
và `git diff --check` PASS. Đây là `FOCUSED_TEST_PROOF` cho terminal receipt
ACK-loss trên fixture process; chưa phải Recovery IPC crash/restart, Windows
packaged/live, hai ChatGPT client thật, duplicate-effect ở mọi boundary hoặc
soak.

**Next action chính xác:** dựng Recovery IPC process crash/restart trong lúc Job
đang `running` và terminal, rồi kiểm tra writer lease/handoff không vượt qua
`unknown/reconcile` hoặc unresolved dispatch.

### Checkpoint cập nhật kế hoạch theo clarification account chung — 20-09-2026, 21:59 +07

Đây là wave **tài liệu/status**, không phải wave bật quyền hoặc triển khai live.
Kế hoạch đã chốt rõ một bind workspace tạo ra một `binding_id`; mọi ChatGPT
client dùng cùng `principal_id` đã xác minh có thể thấy/chọn binding đó. Máy mở
ChatGPT chỉ gửi yêu cầu và nhận kết quả; node đã enroll mới là nơi giữ file,
toolchain, Git, process và quyền OS. Nếu có nhiều binding, client chọn ID theo
từng task; nếu chỉ có một binding, nó chỉ là mặc định của client/phiên. Không có
global switch đổi đích của task đang chạy.

Tài liệu cũng phân loại lại điều có thể tận dụng và điều chưa được chứng minh:
OAuth/account inventory, enrollment/credential, registry/binding, task
idempotency, writer lease/generation, queue/receipt, local MCP/Recovery
runtime, test fixtures và package/backup verifier được giữ làm nền; không xây
lại identity/runtime/controller AI. Ngược lại, hai ChatGPT client thật,
Windows packaged/live, write-path parity, secret-store/rotation, Recovery
crash/reconcile đầy đủ và soak vẫn là gate mở.

**Git/run state:** branch `codex/control-plane-quarantine`, HEAD
`502ffb8cf8b541ee74af30194aff2dce08c3b649`, worktree dirty (gồm thay đổi source,
test, docs và evidence có từ trước cộng wave tài liệu này). Không commit, push,
deploy, restart service, gọi model/provider trả phí hoặc thay đổi credential.
Mức bằng chứng mạnh nhất vẫn là `SOURCE_PRESENT` + `FOCUSED_TEST_PROOF`; các số
liệu hiện hành giữ nguyên: control-plane **244/244 PASS** ở mốc discovery, Node
**862 tests: 846 PASS / 16 SKIP / 0 FAIL**, Recovery exec/stop/lost-ACK/
disconnect/terminal-ACK **5/5 PASS**. Các con số này không được nâng thành
live/package acceptance.

**Bước tiếp theo chính xác tại thời điểm checkpoint này:** thực hiện G4-J trong
kế hoạch — Recovery process crash sau `prepared`/spawn, phân loại
`unknown/reconcile` đúng boundary, chứng minh không có `exec_run` lần hai. Bước
này đã được thực hiện ở checkpoint G4-J bên dưới; next action hiện hành là G4-K
terminal crash/restart và writer/Job handoff trước khi chạy T01/T04/T06/T07/T12–T16
trên exact package.

### Checkpoint G4-J implementation — Recovery crash sau `exec_run`, 20-09-2026, 22:11 +07

Wave này đã thực hiện bước kế tiếp thay vì chỉ ghi kế hoạch:

- Node agent không còn dùng phân loại pre-effect để biến lỗi bridge sau marker
  `prepared` thành `rejected`. Mọi lỗi trả về sau boundary
  durable này (`CONTROL_PLANE_EXEC_UNAVAILABLE`, timeout, process disconnect,
  result lỗi) đều giữ entry, tạo payload `CONTROL_PLANE_EXEC_EFFECT_UNKNOWN` với
  `diagnostic_code`, gửi một receipt `unknown` và yêu cầu reconcile. Các lỗi
  validation trước marker vẫn bị reject bình thường.
- Process fixture Recovery/Electron thật hỗ trợ tự thoát ngay sau khi MCP đã
  ghi nhận `exec_run`; observation được giữ qua restart. E2E khởi động lại
  đúng data root/descriptor, poll lại cùng node và chứng minh action đã ở
  `reconcile_required`, process mới không gọi `exec_run`, không tạo attempt mới.
- Unit regression riêng cho `CONTROL_PLANE_EXEC_UNAVAILABLE` bảo vệ lỗi cũ đã
  bị phát hiện; test timeout sau prepare cũng được cập nhật để kiểm tra
  `code=CONTROL_PLANE_EXEC_EFFECT_UNKNOWN` và chẩn đoán gốc riêng.

**Validation:** full control-plane discovery **250/250 PASS**; node-agent
**21/21 PASS**; HTTP→Recovery exec/stop/lost-ACK/disconnect/terminal-ACK/
crash-restart **6/6 PASS**; `test_mcp_faults` **5/5**, `test_mcp_exec` **8/8**,
`test_store` **80/80** PASS; `py_compile`, `node --check` và `git diff --check`
PASS. Full discovery có `ResourceWarning` connection SQLite đã biết nhưng exit
0 và không có test failure; đây là hygiene backlog, không nâng mức bằng chứng.

**Mức bằng chứng:** `SOURCE_PRESENT + FOCUSED_TEST_PROOF`, chưa phải live.
G4-K còn lại: terminal crash/restart trước/sau receipt ACK, stop-pending và
writer lease unresolved; sau đó mới nghiệm thu Job Windows, hai ChatGPT client
thật, packaged/live và soak.

### Checkpoint G4-K partial — Recovery restart khi Job running/terminal, 20-09-2026, 22:21 +07

Wave này mở rộng G4-K nhưng chưa tuyên bố đóng toàn bộ boundary:

- Khi node đã nhận receipt `accepted` với Job `running`, Recovery process bị kill
  thật rồi khởi động lại cùng data root. Node đọc handle từ journal, process mới
  nhận đúng `exec_poll`, trả terminal result và central settle `completed`; quan
  sát MCP giữ đúng `bind → exec_run → bind → poll`, không có `exec_run` thứ hai.
- Khi local MCP đã trả terminal result nhưng Recovery process chết trước bridge
  ACK, node không đoán terminal state. Nó ghi một receipt `unknown`, central giữ
  `reconcile_required`; process restart không dequeue lại action và không relay
  thêm Job.
- Fixture giữ observation qua restart và ghi hai process launches, giúp phân biệt
  process continuity với một poll mock trong cùng process. Đây vẫn là fixture
  deterministic cho MCP peer, chưa phải Windows Job Object hay packaged Recovery.

**Validation:** HTTP→Recovery process E2E **8/8 PASS** (gồm G4-J crash sau
`exec_run`, G4-K running restart và terminal result loss); full control-plane
discovery **252/252 PASS**; node-agent **21/21 PASS**; `test_mcp_faults` **5/5**,
`test_mcp_exec` **8/8**, `test_store` **80/80**; `py_compile`, `node --check`,
`git diff --check` PASS. Full discovery có `ResourceWarning` SQLite connection
đã biết, exit 0 và không có failure.

**Còn mở để đóng G4-K:** mất ACK sau central terminal receipt, stop-pending qua
Recovery restart, writer lease unresolved/hand-off trên Job thật; sau đó mới
chạy packaged/live và hai client ChatGPT cùng account.

### Checkpoint G4-K continuation — terminal ACK và stop-pending qua Recovery restart, 20-09-2026, 22:34 +07

Wave này đã đóng thêm hai boundary trên cùng fixture process Recovery/Electron
thật, không dùng mock thay cho Recovery IPC:

- Khi `exec_poll` trả terminal result, central commit `completed` nhưng node mất
  ACK, test giết Recovery process ngay sau central commit. Node giữ terminal
  receipt trong journal với `receipt_submitted=false`; process mới chỉ replay
  receipt, không gọi lại `exec_run` hoặc `exec_poll`.
- Khi local MCP đã nhận `exec_stop` nhưng Recovery chết trước bridge response,
  node giữ Job `running`, stop request vẫn `pending` và chưa acknowledge. Sau
  restart, node poll đúng handle; observation persisted của fixture cho thấy
  stop đã có hiệu lực, node ghi `stopped` rồi mới acknowledge stop. Không có
  `exec_run` thứ hai.

Validation của wave: HTTP→Recovery process E2E **10/10 PASS** (8 boundary cũ
và 2 boundary mới), cùng `test_exec_node_agent` + `test_mcp_faults` +
`test_mcp_exec` **34/34 PASS**, full control-plane discovery **254/254 PASS**,
`node --check`, `py_compile` và
`git diff --check` **PASS**. Đây vẫn là `SOURCE_PRESENT + FOCUSED_TEST_PROOF`;
fixture MCP là peer deterministic và chưa phải Windows Job Object, packaged
Recovery hay hai ChatGPT client thật.

**Còn lại của G4-K:** writer lease unresolved/handoff gắn với Job thật và
duplicate-effect/reconcile trên các boundary ngoài fixture này. Sau đó mới
được nâng sang packaged/live, secret-store rotation, write-path parity, T01–T16
và soak liên tục ≥24 giờ.

### Checkpoint G4-K writer lease trên Job local — 20-09-2026, 22:43 +07

E2E hiện đã gắn writer lease trung tâm với một Job local thật qua toàn bộ đường
HTTP → node journal → Recovery process → MCP. Task B cùng binding không thể
claim lease hoặc release thay task A khi Job A còn `running`; release sớm bị
`CONFLICT`. Sau receipt terminal `completed`, task A release được lease và task
B claim generation mới; observation vẫn chỉ có một `exec_run` và một
`exec_poll`.

Validation: HTTP→Recovery E2E **11/11 PASS**, full control-plane discovery
**255/255 PASS**. Đây là proof writer fence + local Job trong fixture, chưa phải
hai ChatGPT client thật, Windows Job Object packaged/live, duplicate-effect
reconcile trên mọi process boundary hoặc deployment.

**Bước G4 kế tiếp:** mở rộng duplicate-effect/reconcile với handoff/stop khi
writer lease unresolved trên Job thật, sau đó mới chuyển sang secret-store/
rotation và packaged/live acceptance.

### Checkpoint SecretStore — 20-09-2026, 22:52 +07

Đã hoàn thiện và kiểm chứng focused phần lưu secret cục bộ trong
[`electron/services/secretStore.js`](../electron/services/secretStore.js):

- Envelope mới có `schema_version=1` và `entries`; payload legacy không có
  schema vẫn đọc được và sẽ được migrate ở mutation kế tiếp.
- Ghi file dùng temporary file độc quyền, `fsync`, mode owner-only `0600`,
  backup `.bak`, cleanup temp và nhánh rename riêng cho Windows.
- Đọc primary hỏng sẽ thử backup cuối cùng còn hợp lệ. Nếu cả primary và
  backup đều không đọc được, `set/remove` dừng fail-closed thay vì ghi đè
  credential hiện có; encryption unavailable cũng dừng mutation.
- Test mới
  [`tests/secret-store.test.js`](../tests/secret-store.test.js) chạy **5/5
  PASS** với fake encryption và thư mục tạm, bao phủ envelope/get-status,
  legacy migration, backup fallback, corrupt-store refusal, unavailable
  encryption, mode/cleanup.

Giới hạn bằng chứng phải giữ nguyên: đây là source/focused proof trên Linux;
chưa chứng minh Electron `safeStorage`/Windows DPAPI live, ACL thật, migration
credential node hiện nằm trong `control-plane-node.json`, hoặc rotation mới
chịu crash/mất ACK. Vì vậy SecretStore không đóng G2 và không nâng mức
`IMPLEMENTED_SOURCE + FOCUSED_TEST` thành packaged/live acceptance.

**SecretStore delivery checkpoint tại 22:52 (đã được supersede bởi checkpoint
node-agent bên dưới):** `node --check` SecretStore, focused SecretStore **5/5**,
full Node **867 tests: 851 PASS / 16 SKIP / 0 FAIL**, `git diff --check` PASS.
Full control-plane tại thời điểm đó là **255/255 PASS** và E2E G4-K **11/11
PASS**; các con số này giữ nguyên làm chronology, còn oracle hiện hành sau patch
node-agent là **261/261**. Chưa commit, push, deploy, restart service hay gọi
provider trả phí.

### Checkpoint node-agent credential protection — 20-09-2026, 23:06 +07

Đã nối phần bảo vệ credential riêng của node-agent vào config Windows ở mức
source:

- Windows `_write_config()` bỏ raw `node_secret`, lưu `node_secret_dpapi` với
  prefix/version marker; `_config()` chỉ giải mã credential vào memory và từ
  chối config chứa đồng thời plaintext + protected value.
- Config Windows legacy còn `node_secret` được migrate ở lần đọc authenticated
  đầu tiên bằng đường ghi atomic; nếu DPAPI unavailable hoặc migration fail thì
  không ghi plaintext fallback và không tạo backup plaintext. Non-Windows source
  fixtures vẫn đọc legacy shape để không làm giả bằng chứng Windows.
- Ghi temporary dùng file độc quyền, `flush` + `fsync`, rồi `os.replace`; không
  dựa vào một lần `os.write()` có thể ghi thiếu payload.
- [`test_node_secret_protection.py`](../control-plane/tests/test_node_secret_protection.py)
  **6/6 PASS**; full Python control-plane discovery sau patch **261/261 PASS**;
  `py_compile` và `git diff --check` **PASS**.

Mức bằng chứng chính xác là **SOURCE_PRESENT + FOCUSED_TEST_PROOF** với
`os.name`/DPAPI helpers được mock; chưa phải Windows DPAPI live, Electron
`safeStorage` live, ACL packaged proof, migration trên máy thật hoặc rotation
chịu crash/mất ACK. Vì vậy G2 chỉ được nâng từ “SecretStore source proof” lên
“node-agent protected persistence source proof”, chưa đóng gate credential.

**Bước tiếp theo chính xác:** chạy trên exact Windows packaged build với một
config legacy fixture được kiểm soát; xác nhận DPAPI decrypt/restart, ACL
owner-only, approved/revoked/reconnect và migration không lộ secret. Sau đó
thiết kế rotation hai pha (`new generation → node persist → authenticated ACK →
revoke old`) với crash/mất ACK/retry, rồi mới tiếp tục duplicate-effect/reconcile
cuối G4 và hai ChatGPT client thật. Không commit/push/deploy/restart/provider
trong checkpoint này.

### Checkpoint schema-22 node-mediated credential rotation — 20-09-2026, 23:29 +07

Đã thay đường đổi khóa một bước bằng protocol có state durable:

```text
node sinh candidate + persist protected pending
  → central prepare (chỉ hash, chưa đổi auth)
  → central activate (old + new cùng hợp lệ)
  → node promote candidate local
  → central ack (đổi hash/generation, retire old)
```

- SQLite schema **21 → 22** thêm `node_credential_rotations`; central chỉ giữ
  hash, generation và state `prepared/activated/completed/aborted`, không giữ raw
  secret. `prepare` retry cùng `rotation_id` trả cùng row; rotation thứ hai bị
  chặn cho tới khi rotation trước hoàn tất.
- Node-agent thêm `node_secret_pending` được DPAPI-protect trên Windows, state
  `candidate_persisted/prepared/activated/promoted/completed`, và CLI
  `rotate-credential`. Crash/mất ACK trước hoặc sau promote có thể chạy lại
  đúng phase; pending protected copy bị xóa sau completed.
- Trong cửa sổ `activated`, old và new credential đều xác thực được; chỉ ack
  bằng new credential mới cập nhật `nodes.credential_hash` và
  `credential_generation`. Legacy operator route `/rotate-credential` fail-closed
  để không còn one-shot switch làm mất node trước khi node lưu key mới.
- Focused proof: node-secret protection **8/8 PASS**, rotation store/agent
  **5/5 PASS**, HTTP rotation **1/1 PASS**; full Python discovery **269/269
  PASS** trong **75.868s**; `py_compile` và `git diff --check` PASS.

Mức bằng chứng là **SOURCE_PRESENT + FOCUSED_TEST_PROOF**. DPAPI helpers vẫn
được mock, HTTP peer và SQLite là fixture local; chưa có Windows packaged/live,
ACL thật, operator UI, rotation trên máy thật hoặc fault/soak exact package.

**Bước tiếp theo chính xác:** đưa CLI/rotation protocol vào packaged Windows
launcher và kiểm tra migration/restart/reconnect trên máy thật; sau đó mô phỏng
crash/mất ACK ở từng phase với DPAPI thật, rồi mới đóng G2 và chuyển sang
duplicate-effect/reconcile cuối G4, write-path parity và T01–T16.

Trước bất kỳ commit/push nào của bước triển khai, tuân thủ retention invariant:
chạy `npm run stage:coding-tools-delivery` rồi
`npm run check:coding-tools-delivery`, giữ toàn bộ `.coding-tools` trừ đúng hai
SQLite sidecar được cho phép. Không staging/commit tự động trong lượt tài liệu.

### Checkpoint cập nhật kế hoạch điều hành — 20-09-2026, 23:35 +07

Đã bổ sung bảng điều hành ở đầu tài liệu để trả lời trực tiếp ba câu hỏi:
**đích sản phẩm là gì**, **hiện đã có bằng chứng nào**, và **có thể tận dụng
khối nào thay vì xây lại**. Bảng cũng tách gate còn mở thành năm nhóm: Windows
packaged/live credential, duplicate-effect/reconcile trên Job thật, write-path
parity, hai ChatGPT client thật và T01–T16/soak. Mục multi-client trong bảng
trạng thái đã được chỉnh để phản ánh các lane mới nhất (OAuth **23/23** và
HTTP→Recovery process **11/11**), không còn dùng số focused cũ làm headline.

**Checkpoint kết thúc wave:** chỉ có Markdown được cập nhật; branch/HEAD,
worktree dirty, `.coding-tools` evidence và mọi source/test chưa commit được
giữ nguyên. Validation tài liệu tiếp theo là `git diff --check` và rà trailing
whitespace; không có commit, push, deploy, restart, credential change hoặc
provider call trong wave này. **Bước kế tiếp chính xác:** lấy quyền truy cập
Windows packaged/live đã được chỉ định, chạy G2 DPAPI/ACL/rotation trước rồi
đóng G4 Job/reconcile; nếu chưa có target live thì chỉ tiếp tục source/focused
proof và không tuyên bố hoàn tất.

### Checkpoint implementation — Electron owner-mediated credential rotation, 20-09-2026, 23:43 +07

Đã nối schema-22/node-agent rotation vào boundary Electron mà không đổi mô hình
quyền:

- ControlPlaneEnrollmentService.rotateCredential() chỉ chạy packaged agent
  với rotate-credential; parser kiểm tra device, rotation ID, state,
  generation, freshness và error code. Raw credential không đi qua renderer,
  IPC payload, argv hoặc environment.
- Main process thêm IPC control-plane:rotate-credential, bắt buộc
  central_executor và confirmRotation=true; preload chỉ expose request
  đã xác nhận. Renderer chỉ hiển thị generation/state và cho owner bấm xác
  nhận sau khi enrollment ở trạng thái approved.
- Preview/API contract và manager regression bảo vệ hidden/unapproved state,
  retry state, malformed receipt, role/confirmation gate và không lộ secret.

**Validation:** combined Electron enrollment/manager/rotation lane **25/25
PASS**; full Node node --test --test-concurrency=4 tests/*.test.js
**868 tests: 852 PASS / 16 SKIP / 0 FAIL**; node --check cho
controlPlaneEnrollment.js, main.js, preload.js, renderer/app.js và
git diff --check **PASS**.

**Mức bằng chứng:** SOURCE_PRESENT + FOCUSED_TEST_PROOF. Đây chưa phải
Windows packaged/live safeStorage/DPAPI, ACL, exact build, rotation crash/
lost-ACK trên máy thật, hay ChatGPT multi-client proof. **Next action:** chạy
đúng candidate Windows packaged để xác nhận owner flow này với DPAPI thật, sau
đó tiếp tục G4 duplicate-effect/reconcile và write-path parity.

### Checkpoint presence inventory theo account — 21-09-2026, 00:04 +07

`ControlPlaneStore.list_account_targets()` nay tính presence cho từng
`binding_id` từ `nodes.last_seen_at_ms`, với ngưỡng mặc định 60 giây:

- chưa có heartbeat hợp lệ → `presence_state=unknown`, `heartbeat_age_ms=null`;
- heartbeat còn mới → `presence_state=online`;
- heartbeat quá ngưỡng → `presence_state=offline`.

Projection này chỉ giúp các ChatGPT client cùng `principal_id` biết binding nào
đang có node kết nối. Nó không tạo task/context/policy/action, không đổi
`binding_id`, không cấp lại quyền, không failover sang máy khác và không trả về
path/credential. Vì vậy presence được tách khỏi quyền thực thi và khỏi TTL của
compact read-only/context pilot.

Focused proof: `test_account_target_inventory_distinguishes_unknown_online_and_stale_presence`
**1/1 PASS**; toàn bộ `test_mcp_oauth.py` **24/24 PASS**; full Python discovery
**270/270 PASS** (khoảng **70.766s**). Đây vẫn là source/focused proof với fake
clock và SQLite fixture, chưa phải heartbeat/reconnect trên Windows packaged
hoặc hai ChatGPT client thật.

**Bước tiếp theo chính xác:** đưa heartbeat/presence projection vào exact
Windows packaged candidate, kiểm tra reconnect sau node/UI/Ubuntu restart,
phân biệt offline với revoked và chạy lại T01/T04/T06/T16 trước khi gọi
multi-client trusted workspace là live.

### Checkpoint G5 — connected-agent worker độc lập read-only context, 21-09-2026, 00:22 +07

Đã nối Supervisor packaged sang command `run-connected-agent`. Khác với
`run-read-only-agent` legacy, worker mới:

1. gửi `runtime-heartbeat` trước mỗi vòng, kể cả khi không có compact
   read-only policy;
2. dùng lock riêng và backoff hữu hạn để reconnect, không tạo agent trùng;
3. kiểm tra standing local policy + workspace registry/generation trước từng
   lane; thiếu hoặc tắt policy thì chỉ ghi `disabled`, không dequeue action;
4. poll riêng các lane `file-read`, `artifact`, `approved-patch` và `exec`,
   giữ nguyên journal/receipt/bridge hiện hữu và không tự nâng capability.

Ba regression mới trong `test_store.py` chứng minh heartbeat không phụ thuộc
read-only policy, tất cả lane được gọi khi owner bật policy, và retry transport
theo backoff **3/3 PASS**. Full Python discovery sau wave này là **273/273
PASS** trong **71.758s**; `py_compile` và parser `run-connected-agent` PASS;
Recovery Supervisor Node test **1 PASS / 1 SKIP / 0 FAIL**.

Đây vẫn là **SOURCE_PRESENT + FOCUSED_TEST_PROOF**. Chưa có Windows packaged
candidate, DPAPI/ACL live, startup sau reboot, heartbeat/reconnect thật,
revoked-vs-offline reconciliation, hai ChatGPT client thật hoặc E2E
read/write/Git/build/test/deploy. **Bước tiếp theo:** đóng gói command mới,
chạy exact Windows smoke/restart rồi mới nâng G5/G6 lên live proof.

### Checkpoint standing-write source path — 21-09-2026, 00:52 +07

Đã hoàn tất trong wave này:

- Bổ sung standing-write central admission ở `store.py` với schema 23 và bảng
  `mcp_standing_patch_intents`; action vẫn pin account/binding/task/generation,
  writer lease, exact digest/envelope và idempotency.
- Bổ sung OAuth/facade contract `control-plane-oauth-standing-write-v1`, env
  `CONTROL_PLANE_MCP_OAUTH_STANDING_WRITE_ENABLED` và schema `agent_workflow`
  không yêu cầu `permission_request_id` trong standing scope.
- Thêm regression `test_standing_write_queues_without_per_patch_permission_and_replays`;
  focused group **131/131 PASS**, full Python discovery **274/274 PASS**;
  `py_compile`, trailing-whitespace và `git diff --check` PASS.
- Cập nhật README, CURRENT_STATE, CONTROL_PLANE_IMPLEMENTATION_STATUS và file
  kế hoạch này để phản ánh đúng account chung, `binding_id` là selector và
  phân biệt source/focused với live/package.

Trạng thái Git/run hiện tại: branch `codex/control-plane-quarantine`, HEAD
`502ffb8cf8b541ee74af30194aff2dce08c3b649`, worktree vẫn dirty với nhiều source,
test, docs và `.coding-tools` evidence từ các wave trước; không commit, push,
deploy, restart service, đổi credential hay gọi provider trả phí. Không bật
standing flag trên Ubuntu live trong wave này.

Blocker/remaining: chưa có HTTP→node standing receipt/fault proof, Windows
packaged DPAPI/ACL/startup/reconnect/rotation, parity exec/artifact/write paths,
hai ChatGPT client thật cùng principal, T01–T16 và soak ≥24 giờ.

Next action chính xác: chạy standing path trên fixture HTTP OAuth → node poller →
local policy → receipt (completed, stale preimage, generation mismatch,
lost-ACK/unknown), sau đó mới xin cửa sổ Windows packaged/live và nghiệm thu
hai-client/soak. Không dùng test fixture này để tuyên bố production/full
authority.

### Checkpoint standing-write HTTP→node receipt — 21-09-2026, 01:08 +07

Đã hoàn tất trong wave này:

- Thêm E2E `test_oauth_standing_write_to_node_patch_to_verified_status`: OAuth
  HTTP `tools/list` nhận capability `standing_write`; `task_control.writer_claim`
  giữ writer lease; `agent_workflow.apply_patch` không truyền
  `permission_request_id`; node poller đọc action qua `/v1/nodes/{device}/poll`,
  kiểm policy v2 standing, gọi bridge fixture và gửi receipt `completed`.
- Sửa `_completed_approved_patch_relay()` để phân biệt action owner-review và
  standing. Standing phải có đúng `authority_mode=standing` và
  `permission_request_id=standing`; field thừa hoặc mode sai vẫn bị loại.
- MCP `patch_status` nay relay được file digest/size đã verify cho standing
  receipt mà không lộ envelope, absolute path, policy digest hay local handle.

Bằng chứng: standing facade + HTTP→node E2E **2/2 PASS**; focused group
**132/132 PASS**; full Python discovery **275/275 PASS** trong **74.130s**.
Full Node vẫn **868 tests: 852 PASS / 16 SKIP / 0 FAIL** từ checkpoint trước.
Full discovery có một số `ResourceWarning` SQLite connection chưa đóng nhưng
không có test failure.

Trạng thái hiện tại: đây là source/focused fixture proof trên Linux, chưa phải
Windows packaged/live, chưa phải ChatGPT hai-client thật và chưa chứng minh
lost-ACK/unknown/duplicate-effect cho standing patch. Không commit, push,
deploy, restart service, bật flag live hoặc gọi provider trong wave này.

Next action chính xác: thêm standing fault cases (stale preimage/path,
generation/policy mismatch, lost ACK và retry không tạo effect thứ hai), sau đó
chạy exact Windows package và nghiệm thu hai client cùng principal.

### Checkpoint xác nhận lại standing fault boundary — 21-09-2026, 01:19 +07

Đã chạy lại lớp tích hợp hiện hành sau khi bổ sung ca generation stale và
unknown/reconcile:

- `test_mcp_approved_patch_http_node_e2e` **3/3 PASS**: owner-review path;
  standing `apply_patch` qua HTTP → node poller → local policy → completed
  receipt/status; policy/workspace-generation stale bị reject trước mutation
  bridge và không ghi file lần hai; effect `unknown` được chiếu là
  `reconcile_required` và không dequeue/retry lại.
- Full Python control-plane discovery **275/275 PASS trong 73.574s**. Có một
  `ResourceWarning` về SQLite connection chưa đóng; đây là hygiene warning,
  không phải test failure.

Mức bằng chứng vẫn là `SOURCE_PRESENT + FOCUSED_TEST_PROOF` trên working tree.
Ca standing stale preimage/path, lost ACK sau completed receipt và proof
duplicate-effect/reconcile xuyên mọi boundary vẫn chưa đóng; Windows
packaged/live DPAPI/ACL/startup/reconnect/rotation, hai ChatGPT client thật,
T01–T16 và soak ≥24 giờ vẫn là backlog. Không commit, push, deploy, restart
service, bật flag live hoặc gọi provider trả phí trong checkpoint này.

**Next action chính xác:** bổ sung fault cases còn thiếu cho standing patch,
chạy lại `git diff --check`, sau đó xin cửa sổ exact Windows package/live và
nghiệm thu account chung → `binding_id` → đúng host/workspace trước T01–T16.

### Checkpoint standing fault proof — 21-09-2026, 01:32 +07

Wave này đã chuyển thêm hai gap của standing patch từ “chưa có proof” sang
`SOURCE_PRESENT + FOCUSED_TEST_PROOF` trong
`test_oauth_standing_write_to_node_patch_to_verified_status`:

- **Stale preimage:** node/bridge trả `CONTROL_PLANE_APPROVED_PATCH_PREIMAGE_MISMATCH`, action settled là `rejected`, file không bị ghi.
- **Mất ACK sau completed:** central đã lưu receipt `completed` trước khi test làm mất response; journal retry gửi lại cùng digest, store replay idempotent, bridge chỉ chạy một lần và action chỉ giữ một terminal receipt.
- **Regression:** HTTP approved-patch class **3/3 PASS**; node/store/task focused group **105/105 PASS**; full Python discovery **275/275 PASS trong 74.546s**. Có `ResourceWarning` SQLite trong một số test nhưng không có failure.

Đã đóng proof local cho stale-generation, stale-preimage và lost-ACK replay;
chưa đóng duplicate-effect/reconcile trên mọi Recovery/package boundary, path
deny standing qua exact Windows bridge, Windows packaged/live DPAPI/ACL/
startup/reconnect/rotation, hai ChatGPT client thật, parity read/write/exec/
Git/build/test/deploy, T01–T16 và soak ≥24 giờ.

**Next action chính xác:** thêm/kiểm chứng standing path-denied và terminal
unknown trên Recovery process thật, sau đó chạy exact Windows package/live.
Không commit, push, deploy, restart service, bật flag live hoặc gọi provider
trả phí trong checkpoint này.

### Checkpoint standing path-deny + full regression — 21-09-2026, 01:37 +07

Đã hoàn tất thêm một oracle local cho standing write: envelope hợp lệ nhưng
relative path không nằm trong allowlist bị settle `rejected` trước mutation
bridge; file đích không tồn tại và không bị tạo. Ca này chạy cùng E2E standing
HTTP→node với stale-preimage, stale-generation và lost-ACK replay.

- HTTP approved-patch class: **3/3 PASS**.
- Node/store/task focused group: **105/105 PASS**.
- Full Python control-plane: **275/275 PASS trong 74.631s**; có một
  `ResourceWarning` SQLite connection chưa đóng, không có test failure.
- `git diff --check` và trailing-whitespace check: **PASS**.

Standing path-deny/preimage/generation và lost-ACK replay hiện có source/focused
proof. Chưa có terminal-unknown/duplicate-effect proof trên mọi Recovery process
boundary, Windows packaged/live, hai ChatGPT client thật, parity đầy đủ
read/write/exec/Git/build/test/deploy, T01–T16 hoặc soak 24 giờ.

**Next action chính xác:** bổ sung terminal-unknown cho standing trên Recovery
process fixture thật, sau đó chuyển sang exact Windows packaged/live gate.

### Checkpoint standing terminal-unknown — 21-09-2026, 01:40 +07

Đã bổ sung ca standing bridge trả lỗi sau prepared boundary. HTTP→node ghi
`unknown`, central chuyển `reconcile_required`, `patch_status` trả
`local_patch_effect_unknown_reconcile_required`, và poll sau không gọi bridge
lại. Đây là source/focused HTTP fixture, chưa phải Recovery process thật.

- HTTP approved-patch class: **3/3 PASS**.
- Full Python control-plane: **275/275 PASS trong 73.941s**; có một số
  `ResourceWarning` SQLite cleanup, không có test failure.
- `git diff --check` và trailing-whitespace checks: **PASS**.

Standing path-deny, stale-preimage, stale-generation, terminal-unknown/no-retry
và lost-ACK receipt replay hiện đã có fixture proof. Còn mở: duplicate-effect
trên mọi Recovery/package boundary, exact Windows packaged/live DPAPI/ACL/
startup/reconnect/rotation, hai ChatGPT client thật, parity đầy đủ
read/write/exec/Git/build/test/deploy, T01–T16 và soak ≥24 giờ.

**Next action chính xác:** đưa terminal-unknown/replay oracle này qua Recovery
process fixture thật, rồi chuyển sang Windows packaged/live gate.

### Checkpoint Windows Tailscale candidate — 21-09-2026, DESKTOP-63643J4

Đã mở và giữ kết nối SSH qua Tailscale tới máy Windows `DESKTOP-63643J4`
(`100.72.186.41`, user `Admin`). Không dùng checkout đang có của máy đích;
source working tree được đặt riêng tại `E:\DEV\Codex-web-candidate-502ffb8`
và cài dependency riêng bằng `npm ci --no-audit --no-fund` (**thành công,
288 packages**). Candidate không kèm `.git`, vì vậy không được coi là một
checkout Git phát hành.

Proof chạy thật trên Windows candidate:

- Node/Electron: **922/922 PASS**; `npm test` chỉ dừng ở guard cuối vì
  candidate không có `.git` (`check-source-root-clean` và
  `check-sensitive-tracked` báo không ở trong Git worktree), không phải test
  fail.
- Shared-account OAuth/binding: **3 PASS, 28 deselected**.
- Hai OAuth client khác token nhưng cùng `issuer/subject`, cùng
  `principal_id`, task pin cùng `binding_id` và receipt của bound node:
  **1 PASS, 12 deselected**.
- HTTP→node E2E read/write/approved-patch/document-write/exec/file-read:
  **22 PASS**, 3 cảnh báo teardown `WinError 10038` trong fixture crash/lost
  ACK; không có assertion failure.
- Recovery process E2E: **3/3 PASS trong 24.871s** (kill/reattach Electron,
  thay Coding MCP giữ Tunnel/gateway, handoff Recovery Host).

Full Python MCP trên Windows ở lần chạy đầu: **1.158 PASS, 2 FAIL, 0 SKIP
trong 37m12s**. Hai failure được phân loại là portability của test/fixture,
chưa phải lỗi shared-account/control-plane: `test_landlock_exec.py` mong chuỗi
lỗi Linux khác với message `only supported on Linux`; `test_wave_a_runtime.py`
dùng shell builtin `echo` với `shell=False` nên Windows trả `WinError 2`.
Receipt này đã được supersede sau khi sửa fixture: lần chạy candidate tiếp theo
đạt **1.160/1.160 PASS trong 1.905,35s (31m45s)**.
Focused OAuth config có **40 PASS, 4 FAIL** vì test vẫn yêu cầu POSIX mode
`0400/0600` trên file credential tạm Windows; riêng shared-account và E2E
luồng target đều PASS. Chưa sửa các fixture này trong checkpoint.

Mức proof của checkpoint ban đầu chỉ tới `SOURCE_PRESENT +
FOCUSED_TEST_PROOF + WINDOWS_UNPACKED_CANDIDATE`; các checkpoint packaged,
DPAPI/ACL và Wave 21 đã nâng candidate lên `PACKAGED_PROOF`, nhưng chưa
`LIVE_ACCEPTED`. Bốn OAuth config assertion POSIX-mode `0400/0600` vẫn là
fixture NTFS riêng. Reboot/DPAPI-ACL reconnect/rotation/revoke trên installed,
Git-build-test-deploy thật, T01–T16, restore hoặc soak 24 giờ vẫn chưa hoàn tất.

**Next action lịch sử:** chạy `dist:dir` và packaged/installed Recovery smoke
trên candidate; việc này đã pass ở checkpoint kế tiếp. Gate hiện hành nằm ở
rotation/revoke, reboot/reconnect, hai client UI thật và owner acceptance.

### Checkpoint Windows packaged/installed proof — 21-09-2026

Trên cùng candidate Windows, `npm run dist:dir` đã tạo `dist\\win-unpacked`
thành công (Electron 43.2.0 x64, native resources và app executable). Smoke
packaged trả `ok=true`, `required_resources=17`, smart-v3 tool contract đúng
8 tool, `host_ready=true`, `device_identity_present=true`, `mcp_alive=true`,
supervisor `healthy=true`, `live_owner_fail_closed=true`,
`hash_mismatch_fail_closed=true`, và không mutate Scheduled Task.

NSIS build trực tiếp bằng `npx electron-builder --win nsis` cũng thành công,
tạo `coding-tools-mcp-setup-1.0.7.exe`. Installed Recovery smoke đã cài vào
thư mục tạm, thấy registry `registered=true`, chạy lại packaged smoke, rồi
uninstall sạch (`installed_files_removed=true`, `registration_removed=true`);
production Recovery descriptor và Scheduled Task fingerprint giữ nguyên.

Đây là `PACKAGED_PROOF + INSTALLED_RECOVERY_SMOKE` trên candidate, không phải
`LIVE_ACCEPTED`: chưa reboot/logon/reconnect, DPAPI/ACL rotation/revoke,
workspace Git/build/test/deploy thật, hai ChatGPT client thật qua UI, T01–T16,
restore/soak hoặc owner acceptance.

### Checkpoint Windows DPAPI/ACL hardening — 21-09-2026

Probe trên candidate phát hiện ACL mặc định trước đây cho
`Authenticated Users:(M)` và `Users:(RX)` trên file node config. Đây là gap
security thật, không phải fixture. Đã sửa `node_agent.py`: mọi config/policy/
journal JSON atomic write trên Windows harden temporary file trước rename bằng
SID allowlist (current user, `S-1-5-18` SYSTEM, `S-1-5-32-544` Administrators)
và fail-closed nếu `whoami.exe`/`icacls.exe` lỗi; không còn dựa vào `chmod`.

Receipt sau sửa trên máy `DESKTOP-63643J4`:

- local unittest node secret/rotation/workspace: **18/18 PASS**;
- Windows candidate focused cùng nhóm: **18/18 PASS trong 4.35s**;
- real DPAPI config + policy probe: protected envelope, không plaintext,
  round-trip pass; `icacls` chỉ còn 3 principal allowlist;
- packaged `native-python` probe: cùng DPAPI/ACL result pass;
- HTTP→node E2E sau hardening: **22/22 PASS**, một warning teardown
  `WinError 10038` trong fixture crash.
- Rebuild `dist:dir`, packaged smoke, NSIS build và installed smoke đều pass
  lại sau source change.

Đây nâng chất lượng `PACKAGED_PROOF` cho credential/local-state boundary;
chưa phải `LIVE_ACCEPTED`: vẫn thiếu reboot/logon/reconnect/rotation ACK thật,
hai ChatGPT client qua UI, Git/build/test/deploy trên workspace thật, T01–T16,
restore và soak 24 giờ.

**Next action chính xác:** chạy rotation/revoke và reconnect trên installed
candidate với một test account được phép, sau đó kiểm tra workspace toolchain
thật trước khi mở T01–T16.
