# Trạng thái triển khai Ubuntu Control Plane

> Bản tóm tắt kế hoạch + hiện trạng theo semantics một account nhiều client:
> [SHARED_ACCOUNT_WORKSPACE_STATUS.md](SHARED_ACCOUNT_WORKSPACE_STATUS.md).
> Windows exact gate: [WINDOWS_EXACT_VALIDATION_RUNBOOK.md](WINDOWS_EXACT_VALIDATION_RUNBOOK.md).
> Các checkpoint phía dưới là chronology/evidence, không tự nâng mức proof.

> Bản cập nhật điều hành mới nhất về semantics một tài khoản ChatGPT dùng
> nhiều client và `binding_id` nằm ở
> [TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md](TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md),
> checkpoint mới nhất **22-09-2026, 06:34 +07, Windows `DESKTOP-63643J4` Wave 47**.
> Các số liệu bên dưới vẫn giữ nguyên bằng chứng theo từng checkpoint, không tự
> nâng thành package/live proof.

## Checkpoint Wave 48 — no-receipt historical dispatch disposition added — 22-09-2026

Source schema hiện là **25**. Đã bổ sung một bảng disposition riêng và hai
route operator cho đúng legacy case còn sót: `workspace_context` đã hết hạn,
`dispatch_unconfirmed`, đúng một attempt, không có receipt, và node stale/
unavailable hoặc thiếu runtime/policy observation hợp lệ. Operation yêu cầu
literal declaration `HISTORICAL_READ_ONLY_UNOBSERVED_DISPATCH` cùng rationale
bounded; ghi digest gắn với action/attempt/node observation và audit event.

Disposition này **không** tạo receipt, không đổi `actions.delivery_state`, không
retry/cancel/replay và không mở admission. Health/backup inspection tách riêng
`historical_unobserved_dispatch_count` và trừ disposition này khỏi
`unquarantined_unresolved_action_count`, nhưng action vẫn là evidence chưa quan
sát, không phải completed hay natural outcome. Store + HTTP/UI focused suite
đã PASS; chưa có operator invocation trên Ubuntu, chưa có deployment/restart,
strict Windows discovery hoặc natural-work outcome.

## Checkpoint Wave 47 — exact checkout đã đồng bộ sau enrollment — 22-09-2026, 06:34 +07

Linux, GitHub và Windows `E:\DEV\Codex-web` hiện cùng ở
`main @ 99fbdd95b5bceb901c80e8d4b63582d0266bb456`. Windows được fast-forward
bằng bundle tạm qua SSH; không reset/rebase, không restart runtime, không đổi
remote; bundle đã xoá. Chỉ ledger/performance projection `.coding-tools` dirty
do runtime evidence. Commit chỉ là docs/delivery receipt, không đổi package
runtime.

Các gate central của Wave 46 giữ nguyên: enrollment chờ operator approve, epoch
đã `FAILED/ACTIVATION_REQUEST_EXPIRED`, admission đóng, route/workspace policy
chưa có; Ubuntu vẫn recovery và service chưa nạp exact package.

## Checkpoint Wave 46 — enrollment Windows đã gửi, Control Plane vẫn recovery — 22-09-2026, 06:27 +07

Windows exact checkout và Linux/GitHub cùng ở `main @
eab25528ffb070e2de6732574ca2599d89b8d08b`; source Windows chỉ có projection
`.coding-tools` runtime dirty. Packaged Recovery Host/MCP đang sống, nhưng epoch
central handoff đã `FAILED/ACTIVATION_REQUEST_EXPIRED`; admission đóng,
`central_connected=false`, `authority_ready=false`,
`central_status_reason=LOCAL_EXECUTOR_NOT_READY`, `fully_ready=false` và
connector `CHANGED_NEEDS_DISCOVERY`.

Hồ sơ node chưa tồn tại trước wave này, nên đã gửi một enrollment request qua
`https://svhome.tail0e4032.ts.net`; receipt là `pending_operator_approval`
(`enroll_31e46b3ad4714738b27707c7b7b8e6a8`). Không hiển thị credential và chưa
cài policy/workspace registry. Ubuntu `/healthz` vẫn `ok=true`, schema 19,
admission `recovery`, `enrollment_requests=5`, `oauth_principals=0`, còn 1
unquarantined unresolved action; service đang nạp package cũ
`sha256:3a151842840530206acf90cdeb0731476af555a46601a357d750ce2105a5b773`
(`0843ece334e07dd29f03cbd4c67fa97fc885ea1c`), chưa phải exact local package.

Blocker là operator Ubuntu approval và quyền deploy/verify package exact; sau đó
mới reconcile node credential/heartbeat, đăng ký workspace, cài policy read-only,
retry full-clean epoch mới và xét binding/task. Chưa `LIVE_ACCEPTED`.

## Checkpoint Wave 44 — receipt HEAD đã đồng bộ; Control Plane chưa deploy — 21-09-2026, 21:42 +07

Linux/GitHub và Windows exact checkout đều ở `main @
dcb3fc492b22d1b04547f3eae1c595b4ee6e4ce0`; Windows worktree sạch. Đây là
delivery receipt `.coding-tools` sau artifact build `bb4522c`, không thay đổi package runtime.
Windows vẫn `MISSING/RECOVERY_DESCRIPTOR_STALE`; Ubuntu chưa có quyền SSH quản
trị để deploy release exact, nên không mở admission hoặc tạo binding/task.
Mức bằng chứng giữ nguyên `SOURCE_PRESENT + FOCUSED_TEST_PROOF + PACKAGED_PROOF`,
chưa `LIVE_ACCEPTED`. Next action là owner closure/activation Windows trước,
sau đó mới verify/deploy Control Plane khi có SSH authority hợp lệ.

## Checkpoint Wave 45 — Windows refresh thiếu local Runtime API Key — 21-09-2026, 22:06 +07

Refresh tương tác đã bootstrap được Recovery Host nhưng failed-closed ở runtime
preflight vì profile local chưa có Runtime API Key; epoch refresh kết thúc
`FAILED/ACTIVATION_EPOCH_FAILED`. Không có binding/task/admission hoặc Ubuntu
deploy mutation; task/PID/script/log tạm đã được dọn. Cần owner chọn local-key
qua UI hoặc central pairing/config hợp lệ trước khi tiếp tục Windows activation;
Control Plane Ubuntu vẫn chưa deploy do thiếu SSH authority.

## Trạng thái điều hành mới nhất — Windows `DESKTOP-63643J4` — 21-09-2026, 21:42 +07

Exact checkout `E:\DEV\Codex-web` đã đồng bộ với Linux và GitHub; checkout
HEAD là `dcb3fc492b22d1b04547f3eae1c595b4ee6e4ce0` và worktree Windows sạch.
Runbook phải đọc lại `git rev-parse HEAD` ngay trước activation. `npm ci`
và `npm run dist` đạt Node/Electron **922/922 PASS**, MCP **1160/1160 PASS**;
packaged và installed smoke đều pass trên package lineage `bb4522c`. Installer
`1.0.7` có SHA-256
`61fb7fa5785c3861fcd4c8371f54172894472c9a0b7d48854c5cb05126d7c14e`.

Installed smoke đã uninstall và cleanup nên runtime hiện `DEV_UI STATUS
state=MISSING`, `host=unavailable`, `error_code=ENOENT`; full-clean preflight
cũng trả `ENOENT`. Mức proof là exact candidate `PACKAGED_PROOF`, chưa
`LIVE_ACCEPTED`; chưa có credential/context/admission/binding/task/deploy
mutation. Gate tiếp theo là owner acceptance exact source + supported full-clean
activation, rồi mới enrollment/workspace/binding/task và T01–T16.

## Checkpoint Wave 39 — exact Windows build/installed proof, live gate còn mở — 21-09-2026, 19:02 +07

SSH/Tailscale tới `100.72.186.41` vẫn reachable. Wave này chỉ cập nhật
exact-source/build evidence và tài liệu; không mở Ubuntu admission, không
dispatch action, không đổi OAuth/credential, không restart/deploy production.

## Checkpoint Wave 40 — installed candidate có mặt, chưa có interactive runtime — 21-09-2026, 19:31 +07

NSIS `1.0.7` đã cài per-user đúng artifact; executable installed hash khớp
unpacked build. SSH launch không tạo Electron/Recovery Host process, không có
Supervisor Task và không có `recovery-host.json`; `dev-ui` vẫn `MISSING/ENOENT`.
Đây là installed artifact proof, chưa `LIVE_ACCEPTED`. Owner cần mở app từ
desktop interactive và tạo closure/activation chính thức trước khi pairing,
workspace binding hoặc task.

## Checkpoint Wave 41 — activation incomplete và Ubuntu release chưa nạp HEAD hiện tại — 21-09-2026, 20:05 +07

Read-only SSH recheck quan sát được packaged UI/Recovery Host/MCP với identity
đúng installation, nhưng strict snapshot vẫn `workspace=""`,
`mcpRunning=false`, `centralConnected=false`, `authorityReady=false`,
`componentsReady=false`, `fullyReady=false`, `updateIncomplete=true`, closure
trống và connector `UNAVAILABLE`.

Một activation owner attempt đã chuyển durable epoch sang
`STOPPING`/`admission=CLOSED` rồi mất replacement process; descriptor stale và
không có Supervisor task. Đây là **activation incomplete**, không phải live
acceptance. Task tạm cũ trỏ tới file đã mất đã được gỡ; profile/credential/
workspace không bị xoá và epoch không bị sửa bằng tay.

Ubuntu `/healthz` vẫn `ok=true` nhưng đang nạp release
`0843ece334e07dd29f03cbd4c67fa97fc885ea1c`, package fingerprint không khớp
source HEAD hiện tại, admission `recovery`, `oauth_principals=0`; SSH quản trị
Ubuntu bị từ chối. Vì vậy chưa thể deploy release mới, mở admission hoặc tạo
binding/task. Mức proof vẫn `SOURCE_PRESENT + FOCUSED_TEST_PROOF + candidate
PACKAGED_PROOF`.

## Checkpoint Wave 36 — BLOCKED chờ external owner activation — 21-09-2026, 12:41 +07

Authoritative recheck vẫn `DEV_UI STATUS state=MISSING` với
`RECOVERY_DESCRIPTOR_STALE`; Supervisor Task `Running` nhưng status
`spawn_failed`, `SPAWN_FAILED`, executable missing. Cùng blocker đã lặp qua
Waves 33–36 sau khi source suite đạt **133/133**.

Đã hết safe read-only progress trên target. Đánh dấu **BLOCKED** chờ owner
thực hiện acceptance ceremony + supported full-clean activation trên exact
artifact/source, rồi Supervisor install nếu cần. Ubuntu không mở admission,
không dispatch và không sửa ledger/epoch.

## Checkpoint Wave 35 — focused lifecycle regression — 21-09-2026, 12:39 +07

`node --test tests/dev-ui-lifecycle.test.js tests/full-clean-activation.test.js
tests/recovery-supervisor.test.js` đạt **133 pass, 0 fail, 1 skip**. Các guard
exact closure, descriptor stale, full-clean epoch và Supervisor eligibility đều
được kiểm; không có live mutation trong test.

Windows target vẫn `RECOVERY_DESCRIPTOR_STALE`/`SPAWN_FAILED`, nên source proof
này không nâng thành `LIVE_ACCEPTED`. Ubuntu admission không đổi.

## Checkpoint Wave 34 — lifecycle preflight và Supervisor status — 21-09-2026, 12:36 +07

`dev:status` từ checkout Windows và candidate đều trả exit 0 nhưng báo
`state=MISSING`, `host=unavailable`, `error_code=RECOVERY_DESCRIPTOR_STALE`.
`full-clean-activation --preflight` trả exit 1 với `RECOVERY_DESCRIPTOR_STALE`;
Supervisor status cho Task `Running` nhưng `state=spawn_failed`,
`last_error_code=SPAWN_FAILED` vì executable bị thiếu.

Đây là lifecycle proof chính thức của blocker; không retry heartbeat để suy ra
readiness, không restart/install/sửa epoch, không mở admission và không dispatch.
Mức proof vẫn `SOURCE_PRESENT + FOCUSED_TEST_PROOF + candidate PACKAGED_PROOF`.
Next action là exact acceptance/full-clean activation rồi Supervisor install hỗ
trợ, sau đó strict readiness và OAuth binding/task.

## Checkpoint Wave 33 — kiểm tra read-only target và phân loại blocker — 21-09-2026, 12:29 +07

`DESKTOP-63643J4` (`100.72.186.41`) reachable qua Tailscale/SSH. Windows
checkout đang ở HEAD `3779096a9156bf2827e3164d09bcc1ef647a2c01` với 23 thay
đổi; candidate packaged `1.0.7` không có `.git`. Accepted-code closure trong
profile vẫn là checkpoint `8d10f27638e2498cba80edf0bcbe77ce`/accepted HEAD
`cffd2acee24a4f38f4a83ddfea4c40f766de7a63`, `activation_eligible=true` nhưng
`affected_components=[]`, `components_current=false`, `lifecycle_clean=false`.

Durable epoch hiển thị `READY/OPEN`, song không có current-process proof: owner
PID Recovery Host đã chết, runtime PID/revision stale, Supervisor hiện
`spawn_failed` (`SPAWN_FAILED`). Heartbeat chẩn đoán trả
`blocked/runtime_unavailable`, `runtime_state=MISSING`, `fully_ready=unknown`,
`policy_state=expired_or_disabled`; nó chỉ ghi route evidence/last-seen. Đây là
**exact-source/closure mismatch + stale Supervisor**, không phải lỗi network.
Không restart/install, không sửa ledger/epoch, không mở admission và không gọi
model.

Mức proof giữ nguyên `SOURCE_PRESENT + FOCUSED_TEST_PROOF + candidate
PACKAGED_PROOF`; chưa `LIVE_ACCEPTED`. Next action là owner acceptance ceremony
trên exact artifact/source rồi full-clean activation hỗ trợ; sau đó mới kiểm
strict readiness và OAuth binding/task live.

## Checkpoint Wave 32 — Tailscale live connection, Recovery IPC và fail-closed start — 21-09-2026, 12:10 +07

SSH/Tailscale tới `DESKTOP-63643J4` (`100.72.186.41`) thành công. Installed
supervisor manifest còn trỏ tới executable đã bị installed-smoke dọn; candidate
unpacked `1.0.7` vẫn có executable/installer nên được dùng cho phép thử tạm.

Candidate Recovery Host khởi chạy trên data root hiện hành; `recovery.ping`
`ok=true/ready=true`, owner process/instance identity khớp và Supervisor từng
báo `healthy`. `runtime.identity_observation` vẫn `mcp_ready=false`,
`identity_current=false`. Runtime snapshot giữ
`central_connected=false`, `authority_ready=false`,
`central_status_reason=LOCAL_EXECUTOR_NOT_READY`, `fully_ready=false`,
`update_incomplete=true`, `recovery_blocked=true`. `runtime.start` bị từ chối
HTTP 409 `UPDATE_INCOMPLETE`: không được thay Coding MCP trong epoch cũ; cần
full-clean activation epoch mới từ owner.

`runtime-heartbeat` exit 0 ở mức `degraded/packaged_runtime_unready`, không
dequeue action/receipt. Candidate process đã được dừng theo đúng owner PID sau
receipt; hiện `Coding Tools MCP` count là 0, descriptor stale. Supervisor ghi
`OWNER_DEAD` ngay sau cleanup và retry tiếp theo là `SPAWN_FAILED` vì executable
trong manifest vẫn thiếu. Không mở admission Ubuntu, không đổi OAuth/binding/task, không gọi
model, không deploy/restart production.

Mức proof không đổi: **source/focused + candidate PACKAGED_PROOF**, chưa
`LIVE_ACCEPTED`. Next action là owner-authorized full-clean activation trên exact
artifact/source, rồi strict MCP/Tunnel/UI identity/heartbeat.

## Checkpoint Wave 26 — Tailscale test connection và runtime gate — 21-09-2026, 11:27 +07

SSH/Tailscale tới `DESKTOP-63643J4` xác nhận đúng candidate. Focused rerun trên
target đạt lifecycle **18/18**, same-account OAuth **3/3**, two-client exec
**1/1**, document-write **1/1** và standing patch **1/1**; patch fixture có
warning teardown `WinError 10038` nhưng pass. Node credential heartbeat
`degraded` trả `exit 0` và local registry có một workspace opaque với
generation/capability `{read,write,exec}`.

Runtime probe hiện tại không thấy Electron/Node process; `runtime-heartbeat`
trả `blocked/runtime_unavailable`, `runtime_identity=unreported`,
`runtime_state=MISSING`. Connected-agent bounded một vòng kết thúc bình thường
với `MAX_ITERATIONS_REACHED`, không dequeue action và không gửi receipt.
Ubuntu admission vẫn `recovery`; wave này không tạo OAuth principal/binding/task,
không thay policy central và không deploy/restart.

Kết luận giữ nguyên: candidate có **PACKAGED_PROOF**, chưa có `LIVE_ACCEPTED`.
Gate tiếp theo là exact Electron/Recovery packaged startup + strict identity,
Sau đó owner-authorized binding/task/toolchain/fault/soak.

## Checkpoint Wave 27 — packaged recovery smoke cô lập — 21-09-2026, 11:38 +07

Official packaged smoke trên candidate trả **exit 0**: 17 resources, đủ 8
smart-v3 tools, Recovery Host/MCP và device identity healthy, Supervisor
healthy, live-owner/hash-mismatch fail-closed pass, production descriptor stable
và Scheduled Task không bị mutate. User-data dùng TEMP riêng và đã cleanup;
không còn candidate process sau khi kết thúc.

Đây chỉ là package/isolation proof. Ubuntu vẫn `recovery`, runtime production
chưa chạy và chưa có OAuth live binding/task; không mở dispatch hoặc nâng nhãn
`LIVE_ACCEPTED`.

## Checkpoint Wave 28 — central health và source capability recheck — 21-09-2026, 11:41 +07

GET `/healthz` read-only trả `ok=true`, SQLite `ok`, schema **19**, admission
`recovery`, actual/expected package SHA khớp, `oauth_principals=0`,
`node_workspaces=3`, unresolved actions **11**. Targeted source `unittest`
đạt **7/7 PASS**: account/binding/writer **4/4** và local exec/document/patch
**3/3**. Local `pytest` không chạy vì interpreter thiếu module; đây là
environment limitation, không phải regression. Chưa mở central dispatch.

## Checkpoint Wave 29 — full Control Plane source discovery — 21-09-2026, 11:44 +07

`unittest discover` toàn bộ `control-plane/tests` đạt **298/298 PASS trong
96,772s**. Receipt fixture lifecycle/unknown-state là expected negative/recovery
coverage; không có failure, không gửi action live và không thay admission. Mức
này chỉ là source regression proof; Windows runtime/owner gates vẫn mở.

## Checkpoint Wave 30 — installed NSIS smoke và isolation — 21-09-2026, 11:49 +07

Installed smoke trên candidate trả **exit 0**: NSIS `1.0.7` install/register,
packaged Recovery smoke, uninstall và registration cleanup đều pass. Production
Recovery descriptor và Scheduled Task definition không đổi. Đây là installed
candidate proof; chưa mở runtime production, OAuth live binding/task hoặc
dispatch.

## Checkpoint Wave 31 — post-smoke read-only state — 21-09-2026, 11:51 +07

Target sau installed smoke có **0** process candidate. Recovery descriptor còn
metadata owner/instance nhưng không có owner process sống; đây là stale state,
không phải runtime liveness. Ubuntu `/healthz` vẫn `ok`, schema 19,
`admission=recovery`, `oauth_principals=0`, `node_workspaces=3`, unresolved 11.
Không có live action hoặc admission/restart change.

## Checkpoint Wave 25 — node workspace registration và policy local — 21-09-2026

Credential node đã heartbeat `degraded` thành công tới Ubuntu (`exit 0`).
Workspace candidate đăng ký thành công với capability `read/write/exec`; local
standing policies cho file-read, approved-patch và exec đều inspect được ở
trạng thái `enabled`/`authority_mode=standing`. ACL thực tế chỉ có user hiện
tại, SYSTEM và Administrators.

`runtime-heartbeat` không thể báo ready (`runtime_status_unavailable`), còn một
vòng `run-connected-agent` kết thúc `MAX_ITERATIONS_REACHED` sau trạng thái
`degraded/CONTROL_PLANE_BRIDGE_FAILED`; không lane nào dequeue. Health Ubuntu
read-only sau đăng ký ghi nhận `node_workspaces=3`, `oauth_principals=0`,
`admission_mode=recovery`, unresolved **11**, SQLite/package SHA khớp.

Đây là node registration + local policy proof, **không phải OAuth binding/live
task proof**. Không mở admission, không tạo principal/binding/task/action,
không file effect, reboot/restart, deploy, commit hoặc push. Gate tiếp theo là
khởi chạy đúng Electron/Recovery packaged runtime và chứng minh strict identity;
sau đó mới có thể nghiệm thu OAuth two-client/binding.

## Checkpoint Wave 24 — candidate reachable nhưng runtime live chưa bind — 21-09-2026, 10:59 +07

Tailscale/SSH tới `DESKTOP-63643J4` (`100.72.186.41`) xác thực thành công.
Focused Windows candidate recheck đạt secret/rotation/workspace **18/18**,
same-account OAuth **3/3**, two-client exec **1/1**, document-write **1/1** và
standing patch **1/1**. Đây là fixture/candidate proof, không phải UI/account
live proof.

Read-only probe cho thấy Electron/Recovery không chạy; workspace registry chưa
có (`list-workspaces` rỗng); Supervisor `spawn_failed` và agent
`integrity_unproven`. `inspect-read-only-policy` packaged trên dev data root bị
fail-closed với `CONTROL_PLANE_POLICY_PACKAGED_DATA_ROOT_FORBIDDEN`. Vì vậy
reachability đã đóng, nhưng runtime bind/reconnect chưa được chứng minh.

Giữ trạng thái **`SOURCE_PRESENT + FOCUSED_TEST_PROOF + candidate
PACKAGED_PROOF`**, chưa `LIVE_ACCEPTED`. Wave này không chạm Ubuntu admission,
credential thật, reboot/restart, deploy, commit hoặc push. Gate tiếp theo cần
test account/data root được owner ủy quyền: pair/enroll → register workspace →
heartbeat/connected-agent → reboot/reconnect/rotation/revoke → hai client thật.

## Checkpoint Wave 23 — packaged/installed smoke recheck — 21-09-2026, 10:48 +07

Packaged smoke trên candidate pass với **17 resources**, smart-v3 **8 tools**,
Recovery/MCP/Supervisor healthy và fail-closed owner/hash; installed smoke
installer `1.0.7` install/register/uninstall pass, giữ nguyên production
descriptor và Scheduled Task. Đây là package/isolation proof, không phải
reboot/reconnect, live account hoặc owner acceptance.

## Checkpoint Wave 22 — structured exec/journal parity trên Windows candidate — 21-09-2026, 10:45 +07

Candidate Windows đạt **1/1 PASS trong 6,38s** cho workflow argv
`git/build/test/deploy` trên một local lane và **1/1 PASS trong 4,30s** cho
HTTP→node journal→Recovery terminal receipt. Đây là fixture route/receipt proof,
không phải workspace production hoặc deploy thật. Ubuntu vẫn ở `recovery`,
OAuth principals `0`; không mở admission hay tạo action live.

## Checkpoint Wave 21 — Windows target reachable, Ubuntu health read-only — 21-09-2026, 10:31 +07

SSH trực tiếp tới `DESKTOP-63643J4` (`100.72.186.41`) đã thành công. Candidate
`E:\DEV\Codex-web-candidate-502ffb8` là bản cô lập version `1.0.7`, có
`dist\win-unpacked` và installer NSIS, không có `.git`. Focused recheck trên
candidate đạt **18/18** secret/rotation/workspace, **3/3** same-account OAuth,
**1/1** two-client exec, **1/1** document-write và **1/1** standing patch.
Receipt Windows candidate trước đó cũng đạt full MCP **1.160/1.160 PASS** và
Node/Electron **922/922 PASS**; bốn OAuth config assertion POSIX-mode trên NTFS
được giữ là fixture portability, không phải lý do thay đổi policy bảo mật.

Health Ubuntu chỉ đọc hiện tại: `ok=true`, schema **19**, SQLite `ok`,
`admission_mode=recovery`, counts **3/4/4/24/18/18/13** (nodes/enrollments/
bindings/contexts/requests/actions/receipts), OAuth principals **0**, unresolved
actions **11** (10 quarantined, 1 unquarantined), auth mode
`legacy_context_grant`, package SHA đúng expected. Vì `oauth_principals=0` và
admission chưa mở, đây là health/inventory evidence chứ chưa phải central live
account acceptance.

Wave 21 đã gỡ blocker reachability, không gỡ các gate sản phẩm còn lại. Giữ
nhãn **`SOURCE_PRESENT + FOCUSED_TEST_PROOF + candidate PACKAGED_PROOF`**;
chưa gọi là `LIVE_ACCEPTED`. Next action là installed rotation/revoke + reboot/
reconnect, hai ChatGPT client thật cùng `principal_id`, toolchain thật, T01–T16,
restore/soak và owner acceptance; không tự reconcile action hay restart Ubuntu.

## Snapshot repository hiện tại — 21-09-2026

Branch `codex/control-plane-quarantine`, HEAD
`502ffb8cf8b541ee74af30194aff2dce08c3b649`; worktree dirty có chủ ý vì các
thay đổi source/test/docs/evidence. Lượt này không reset/clean, commit, push,
deploy hoặc restart service. Mức bằng chứng hiện là
**`SOURCE_PRESENT + FOCUSED_TEST_PROOF` + candidate `PACKAGED_PROOF`**.

Số liệu authoritative: Control Plane **295/295 PASS**; `npm run test:all` với
bundled workspace Python 3.12.14/pytest 8.4.2 đạt Node/Electron **858 PASS, 16
SKIP, 0 FAIL / 874** và MCP **1.153 PASS, 7 SKIP, 0 FAIL / 1.160**; Linux
resource preflight **427 resources + 9 adapters**; packaged/installed focused
**5/5 PASS**. Windows candidate package/installer, installed smoke và DPAPI/ACL
đã có proof; startup/reconnect/revoke/rotation trên installed, two-client live
acceptance, T01–T16 và soak 24 giờ vẫn là gate mở.

Wave 17 là receipt lịch sử có một dependency-only failure; Wave 18 đã chạy lại
bằng interpreter có dev extra đúng chuẩn và không còn failure. Không sửa policy
runtime để làm xanh giả;
Control Plane unittest **295/295 PASS** và Node/Electron `npm test` **858 PASS,
16 SKIP, 0 FAIL / 874 trong 43.317s** là receipt chạy trực tiếp trên worktree;
source-root/secret checks đều PASS.

Wave 14 focused recheck bổ sung **71/71 PASS** cho account/task/HTTP → node và
**146/146 PASS** cho store/node authority/credential/workspace; Node/Electron
bridge/enrollment/recovery đạt **34 PASS, 1 SKIP, 0 FAIL**. Đây vẫn là
source/focused proof; Windows exact/live gates chưa được đóng.

Wave 15 full regression đạt Node/Electron **874 tests: 858 PASS, 16 SKIP, 0
FAIL trong 43,45s** và Control Plane **295/295 PASS trong 96,37s**; source-root
và repository-secret checks PASS. Đây vẫn là source/local proof trên Linux.

## Checkpoint Wave 20 — target Windows và evidence guard — 21-09-2026, 08:18 +07

- Read-only SSH tới alias `daochienthang` timeout sau 5 giây; không có copy,
  cài đặt, test hay restart ngoài được thực hiện.
- Không có Windows `win-unpacked`/installer trong workspace Linux hiện tại.
- `npm run check:coding-tools-history`: **PASS (4.873 files)**; repository
  secret check: **PASS**.

Đây là external-state blocker cho packaged/live gate, không phải source failure.
Wave 18 vẫn là source/local baseline; Wave 19 vẫn phân loại `windows_only`.

## Checkpoint Wave 19 — phân loại Recovery/packaged gate Windows — 21-09-2026, 08:14 +07

- `npm run test:recovery:e2e`: **3 SKIP, 0 FAIL** vì toàn bộ test yêu cầu
  `process.platform === "win32"`.
- `npm run test:recovery:packaged`: `dist:dir` tạo Linux unpacked candidate;
  packaged smoke trả `{ok:true, skipped:true, reason:"windows_only"}`.

Đây là platform/environment gate chứ không phải source failure. Không nâng
`PACKAGED_PROOF` hoặc `LIVE_ACCEPTED`; cần Windows exact runner để kiểm
RunAsNode/Recovery/installer, DPAPI/ACL/startup/reconnect/rotation và sau đó
two-client/T01–T16.

## Checkpoint Wave 18 — full local gate xanh — 21-09-2026, 08:06 +07

`npm run test:all` đã hoàn tất trên source tree với runtime dependency chuẩn:

- Electron/Desktop: **874 tests, 858 PASS, 16 SKIP, 0 FAIL**; source-root và
  repository-secret checks PASS.
- Coding Tools MCP: **1.160 collected, 1.153 PASS, 7 SKIP, 0 FAIL** trong
  **159,98s**.
- Warning còn lại chỉ là resource/cleanup warning; không có failure.

Wave này xác nhận các phần Control Plane có thể tiếp tục được tận dụng cho mục
tiêu account chung: OAuth principal/inventory, binding/task pin, enrollment và
credential dài hạn theo node, writer/generation fence, queue/receipt,
Recovery/RuntimeOrchestrator, standing bridges và journal idempotency. Không
được suy ra Windows packaged/live, quyền Administrator, hai client ChatGPT thật
hoặc model gateway đã triển khai.

**Next action:** tạo Windows exact candidate và đóng DPAPI/ACL/startup/reconnect/
rotation; sau đó chạy two-client cùng `principal_id` → chọn `binding_id` →
đọc/sửa/exec/Git/build/test/deploy trên node đúng → T01–T16, backup/restore,
soak 24 giờ và owner acceptance.

## Checkpoint Wave 17 — full MCP source-first rerun — 21-09-2026

Full MCP với source repository đứng trước dependency runtime, proxy variables
unset và `PYTHONWARNINGS=error::ResourceWarning` đạt **1.160 collected: 1.152
PASS, 1 FAIL, 7 SKIP, 37 warnings trong 161.53s**. SDK HTTP/operator timestamp
**19/19 PASS**; multi-workspace HTTP và authorized workspace **2/2 PASS**.

Failure duy nhất là continuous-check bookkeeping gọi `python -m pytest` trong
child system Python không có pytest; cùng logic đạt pass khi child có dev
dependency và `ShellEnvPolicy(inherit="all")`. Đây là dependency/harness gap;
không nới policy `PYTHONPATH` hoặc coi full MCP là xanh giả. Windows exact/live,
two-client ChatGPT, toolchain thật, T01–T16 và soak vẫn mở.

## Checkpoint Wave 16 — full MCP recheck và phân loại blocker (lịch sử) — 21-09-2026

Lần chạy full MCP của Wave 16 thu được **1.160 collected: 1.145 PASS, 8 FAIL,
7 SKIP, 35 warnings trong 160.43s**; không ghi đây là full pass. Một official
SDK smoke báo `httpx.InvalidURL` và cần retry khi bỏ proxy; các matrix/
greenfield/build/continuous-check/workspace-session gọi child `python` trong khi
host chỉ có `python3`; operator-report cần xác minh lại `24:00:00Z` trên đúng
interpreter. Đây là phân loại harness/environment hoặc chưa tái hiện source bug,
không phải bằng chứng local authority đã hỏng.

Receipt trực tiếp vẫn xanh là Control Plane **295/295 PASS** và Node/Electron
**858 PASS, 16 SKIP, 0 FAIL / 874**. Chưa có Windows exact package/live,
DPAPI/ACL, reboot/reconnect, two-client ChatGPT thật, toolchain thật, T01–T16,
backup/restore, soak 24 giờ hoặc owner acceptance; mức proof không đổi:
`SOURCE_PRESENT + FOCUSED_TEST_PROOF` + integrated local test proof.

## Checkpoint Wave 10 — refresh Linux packaged candidate — 21-09-2026

Candidate `dist/linux-unpacked` được tạo lại bằng `npm run dist:dir` (**PASS**).
Hai nhóm packaged/installed recovery smoke đạt **3/3 PASS**; packaged smoke
trả `windows_only` đúng contract trên Linux. Verifier trực tiếp đạt
**427 resource files exact-source**, **9 control-plane adapters exact-source**
và **463 entries sanitized**.
HTTP boundary recheck cho hai client cùng `principal_id` chọn nhiều binding và
handoff writer lease đạt **2/2 PASS trong 3.053s**.
HTTP → node → Recovery cho document-write và structured exec đạt **23/23 PASS
trong 29.601s** với `PYTHONWARNINGS=error::ResourceWarning`.
Standing-profile configuration, shared-task observation và cross-client
writer/exec guard đạt **3/3 PASS trong 3.046s**.
Standing patch không cần per-patch approval và document-create không đưa
content vào action payload đạt **2/2 PASS trong 0.083s**.

Receipt này chỉ chứng minh resource/package wiring trên Linux. Windows
RunAsNode fuse, Recovery Host, DPAPI/ACL, reboot/reconnect và live two-client
vẫn là gate mở; không nâng nhãn proof.

## Checkpoint Wave 11 — documentation contract alignment — 21-09-2026

`control-plane/README.md` đã đánh dấu `install-read-only-policy-*` là legacy
compatibility-only và mô tả trusted flow hiện hành: OAuth account → opaque
`binding_id` → standing node-local read/write/structured exec → task pin/
reconnect. Wave này chỉ sửa tài liệu, không đổi live service hoặc quyền node.

## Checkpoint Wave 12 — T01–T16 source/live matrix — 21-09-2026

Ma trận T01–T16 và trạng thái từng gate được ghi tại
[SHARED_ACCOUNT_WORKSPACE_STATUS.md](SHARED_ACCOUNT_WORKSPACE_STATUS.md). Các
receipt fixture/source chỉ giữ mức focused; Windows exact, two-client live,
DPAPI/ACL, backup/restore và soak chưa được nâng nhãn.

## Checkpoint Wave 9 — Recovery Supervisor không còn khóa vào read-only TTL — 21-09-2026

Audit code/runtime contract đã tìm thấy lỗi nối giữa worker và Supervisor:
Supervisor đã spawn `run-connected-agent`, nhưng preflight vẫn chỉ đọc
`control-plane-read-only-policy.json` và bắt `expires_at_ms`. Điều đó mâu thuẫn
với connected-agent heartbeat độc lập và làm standing write/exec có thể mất
startup sau khi pilot policy hết hạn; config đã DPAPI hóa cũng không còn
`node_secret` plaintext để Supervisor đọc.

Đã sửa preflight để xét đúng ba lane standing v2: file-read,
approved-patch/document-write và structured exec. Supervisor chỉ spawn khi có ít
nhất một lane enabled, đúng origin/device/endpoint, exact workspace generation
còn current và resource hash hợp lệ. Thiếu/sai policy, registry hoặc identity
đều fail-closed; read-only pilot hết hạn/disabled không còn chặn connected
agent. `node_secret_dpapi` chỉ được nhận diện theo marker, không giải mã hoặc
đưa secret vào log/argv. Node agent vẫn revalidate policy và workspace ngay
trước heartbeat/dequeue/effect.

Proof trực tiếp: PowerShell helper class **1/1 PASS**, `test_store` **83/83 PASS`,
Supervisor Node test **1 PASS, 1 SKIP**, `git diff --check` PASS. Đây chưa phải
Windows packaged/live proof; chưa chạy reboot/logon, DPAPI/ACL, two-client thật,
T01–T16 hoặc soak. Next action là đóng gói artifact Windows mới và chạy P1–P6,
không bật Ubuntu live hay model gateway trong wave này.

## Checkpoint Wave 7 — shared-account HTTP→node capability recheck — 21-09-2026

Focused group gồm OAuth/account, task pin/writer handoff, exec Recovery và
document-write HTTP→node: **57/57 PASS trong 45.280s**. Full Control Plane
unittest: **294/294 PASS trong 94.877s** bằng Python 3.14.4 với
`PYTHONWARNINGS=error::ResourceWarning`; không còn SQLite `ResourceWarning`.

Đã chứng minh local/source path cho shared `principal_id` → nhiều `binding_id`,
standing patch/document/exec trên node local, writer fence, crash/lost-ACK,
terminal receipt replay và `unknown/reconcile_required` không redeliver effect.
Windows package/DPAPI/ACL/reboot/reconnect/live two-client/T01–T16 vẫn chưa có
receipt và chưa được nâng mức bằng chứng.

## Checkpoint Wave 8 — standing local authority configuration proof — 21-09-2026

OAuth configuration focused **6/6 PASS**: standing write/exec chỉ bật với
file-read, write scope riêng và flag hợp lệ; các tổ hợp thiếu scope, exec đơn
độc hoặc giá trị sai đều fail-closed. Full Control Plane sau thay đổi đạt
**295/295 PASS trong 95.319s** bằng Python 3.14.4 với
`PYTHONWARNINGS=error::ResourceWarning`.

Đây là proof cấu hình/source; không phải live activation. Ubuntu live chưa được
mở flag, Windows DPAPI/ACL/package/startup/reconnect và two-client acceptance
vẫn là gate tiếp theo.

## Checkpoint Wave 4 — node revoke và public task admission — 21-09-2026

OAuth inventory/HTTP focused đã chứng minh node bị revoke vẫn hiển thị như
target lịch sử nhưng không dispatchable: `node_state=revoked`,
`dispatch_state=node_revoked`, `dispatch_blockers=["node_revoked"]`. Public
`task_open` trên binding đó trả `CONFLICT`, không tạo task và không failover;
projection vẫn credential-free.

Receipt: OAuth HTTP **28/28 PASS trong 14.266s**; toàn bộ Control Plane
unittest **292/292 PASS trong 92.197s** với `ResourceWarning` được nâng thành
lỗi (không còn warning SQLite). Đây là source proof mới nhất; không
thay thế Windows exact package/DPAPI/ACL/startup hoặc live acceptance.

## Checkpoint Wave 5 — principal revoke và retired generation — 21-09-2026

OAuth ingress hiện có focused proof rằng revoke `principal_id` trả `403
FORBIDDEN`, không tạo pending link và không làm lộ target. Retire generation
giữ binding lịch sử với `workspace_state=retired`; `task_open` bị chặn bằng
`CONFLICT`, không retarget/failover.

Receipt mới: OAuth HTTP **30/30 PASS trong 15.812s**; toàn bộ Control Plane
unittest **294/294 PASS trong 96.371s** với `ResourceWarning` là lỗi. Đây vẫn
là source/local proof, chưa phải Windows package/live acceptance.

## Checkpoint Wave 6 — Node/Electron regression recheck — 21-09-2026

`npm test` đã PASS **858/874** (16 skip có chủ đích) trong **43.317s**; source
root và repository-secret checks đều PASS. Đây vẫn là source/local proof, không
thay thế Windows package/fuse/Recovery/DPAPI/ACL hoặc live acceptance.

## Trạng thái điều hành chốt — một account, nhiều client, 21-09-2026

Một OAuth account được ánh xạ thành cùng `principal_id` trên tất cả client/máy
đăng nhập account đó; client chọn `binding_id` của máy/workspace cần làm việc.
Ví dụ máy A bind W1 thành B1 thì máy B/C cùng account chọn B1 và lệnh chạy ở
A/W1. Task pin bất biến
`{device_id, endpoint_id, workspace_id, workspace_generation}`. Ubuntu chỉ xác
thực, định tuyến, xếp hàng và lưu receipt; node đã bind giữ file, Git, process,
build/test/deploy và quyền OS local. Enrollment/credential tồn tại lâu dài sau
khi được duyệt; không sao chép token/context và không xin duyệt từng lệnh trong
standing local scope. `binding_id` không phải bearer token và không có
`active_workspace` toàn account.

### Reuse map và khoảng trống thực tế

| Có thể dùng ngay | Chưa được coi là đã hoàn tất |
| --- | --- |
| `mcp_oauth.py`, `http_api.py`, `mcp_facade.py`, `store.py` cho principal/account inventory, binding, task, writer lease, generation, queue/receipt | Hai OAuth client khác token cùng principal đã route chung bound node trong Windows E2E; UI ChatGPT live vẫn chưa nghiệm thu |
| Enrollment/device identity/credential, SecretStore/DPAPI source path, heartbeat, reconnect, rotation, workspace capability registry | DPAPI/`safeStorage`/ACL/reboot/startup/revoke/rotation trên package thật |
| File-read, approved-patch, document-write, structured-exec bridges; Recovery Host/IPC; RuntimeOrchestrator; Coding Tools MCP | Git/build/test/deploy thật và duplicate-effect/reconcile trên packaged Windows |
| Resource verifier, packaged/installed helper smoke, `.coding-tools` ledger/evidence; Windows `dist:dir`/NSIS/installed smoke đã pass | DPAPI/ACL/reboot/reconnect/rotation live, T01–T16, backup/restore, soak ≥24h, owner acceptance |

Mức bằng chứng hiện tại là **`SOURCE_PRESENT + FOCUSED_TEST_PROOF` + Windows
candidate `PACKAGED_PROOF`**. Bước kế tiếp theo đúng thứ tự: (1) DPAPI/ACL,
reboot/startup/reconnect/rotation trên package thật, (2) hai ChatGPT client live
và binding acceptance, (3) full local toolchain + fault matrix/soak, (4) owner
acceptance rồi mới xem xét release/deploy. Không thêm executor Ubuntu thứ hai;
provider/model gateway chỉ là nhánh tùy chọn.

## Checkpoint Wave 3 — lifecycle-aware account inventory — 21-09-2026

Store đã sửa `list_account_targets()` để dùng inventory giữ lịch sử: target của
cùng account vẫn xuất hiện khi binding bị revoke, node bị revoke, workspace
generation đã retire hoặc registration bị thiếu. Projection chỉ có ID, display
name, capability và timestamp; không có absolute path/secret/OAuth subject.
`dispatch_state`/`dispatch_blockers` cho biết vì sao target không dispatchable;
`task_open` và các action path vẫn chặn target không còn current.

Focused proof: `control-plane/tests/test_mcp_oauth.py` **27/27 PASS** và
`control-plane/tests/test_store.py` **83/83 PASS**, OAuth/task focused group
**39/39 PASS trong 13.03s**; toàn bộ Control Plane unittest **291/291 PASS
trong 90.154s**. Chưa có thay đổi live; gate
Windows/package/two-client thật vẫn mở.

Linux package preflight sau source wave: `npm run dist:dir` PASS; resource
verifier **427 files + 9 control-plane adapter files**; packaged/installed
recovery/release focused tests **5/5 PASS**. Linux preflight không chứng minh
Windows RunAsNode fuse, Recovery Host, DPAPI/ACL hay reboot/startup.

## Checkpoint integrated source gate xanh trước Wave 16 — 21-09-2026

`npm run test:all` đã chạy bằng Python runtime product **3.12.14** + pytest
**8.4.2** và hoàn tất:

- Node/Electron: **874 tests: 858 PASS, 16 SKIP, 0 FAIL**;
- MCP Python: **1.160 collected: 1.153 PASS, 7 SKIP, 0 FAIL / 159.31s**;
- source-root, repository-secret và focused hash/timestamp/restart/
  continuous-check regression: PASS.

Wave này cập nhật exact structured-`argv` hash, canonical timestamp parser,
platform-aware restart/reconcile expectation và chỉ dùng `trusted` cho
ContextBudget output fixture; không nới safe policy. Evidence vẫn là
**`SOURCE_PRESENT + FOCUSED_TEST_PROOF` + integrated local test proof**.
Windows exact package/fuse/DPAPI/ACL, reboot/reconnect/revoke/rotation, two
ChatGPT clients, T01–T16 và soak 24h còn mở.

**Next action:** Windows exact package/Recovery smoke → credential/startup gates
→ same-account two-client acceptance → fault matrix/soak/owner acceptance.

## Checkpoint direct MCP Python initial attempt (superseded) — 21-09-2026

Python **3.14.4** + pytest **8.4.2** với dev dependencies đầy đủ trong runtime
tạm đã collect **1.160 test: 1.149 PASS, 4 FAIL, 7 SKIP**. Đây là direct suite
proof; không phải package Windows và không thay thế `npm run test:mcp` trên host,
vì `/usr/bin/python3` hiện vẫn thiếu pytest.

Bốn blocker cần xử lý trước khi gọi lane xanh:

1. exact tool-contract hash test còn mong `d694…`, trong khi structured `argv`
   hiện tại sinh `bc44…`;
2. live restart/reconcile chưa terminalize được managed job sau khi command
   handle mất, phải giữ process identity/owner fence và không kill PID mù;
3. canonical timestamp parser chấp nhận `24:00:00Z` trên Python 3.14;
4. continuous-check fixture chạy `python -m pytest` nhưng child không thấy
   pytest do runtime không truyền `PYTHONPATH` tạm (environment/harness gap).

Node/source lane vẫn **874 tests: 858 PASS, 16 SKIP, 0 FAIL**; Control Plane
unittest riêng vẫn **289/289 PASS**. Trạng thái evidence giữ nguyên
**`SOURCE_PRESENT + FOCUSED_TEST_PROOF`**.

**Next action:** sửa/retest 4 blocker, cài dev extra vào interpreter thật rồi
chạy lại `npm run test:all`; sau đó mới mở Windows exact package/fuse/DPAPI/ACL,
reboot/reconnect/revoke/rotation và T01–T16.

## Checkpoint npm host dependency — 21-09-2026 (previous run)

`npm run test:all` đạt Node/source lane **874 tests: 858 PASS, 16 SKIP, 0 FAIL**;
source-root và repository-secret checks đều PASS. Lệnh kết thúc ở `test:mcp`
vì `/usr/bin/python3` thiếu `pytest`. Host không có `pip`/`ensurepip`, nên
`python3 -m pip install -e 'resources/coding-tools-mcp[dev]'` chưa thể chạy.
Đây là blocker dependency của môi trường; chưa được tính là MCP pytest pass và
chưa thay đổi mức bằng chứng `SOURCE_PRESENT + FOCUSED_TEST_PROOF`.

## Chốt semantics account/workspace — 21-09-2026

Một account ChatGPT/OAuth dùng chung tạo một `principal_id`. Máy A bind workspace
và nhận `binding_id`; mọi client cùng account có thể chọn ID đó để gửi việc tới
đúng A, trong khi file, Git, process, build/test/deploy và quyền OS vẫn nằm ở
runtime local của A. `binding_id` chỉ là selector, không phải token/context.
Mỗi task khóa `{device_id, endpoint_id, workspace_id, workspace_generation}`;
writer lease/idempotency/generation fence ngăn client thứ hai retarget hoặc ghi
đè task đang chạy. Không tạo `active_workspace` toàn tài khoản và không copy
cookie, OAuth token, node secret, context hay absolute path giữa máy.

Đã có thể tái sử dụng account inventory/binding/task store, enrollment và
credential lâu dài theo device, heartbeat/reconnect/rotation source path,
standing local policy, journal/receipt, Recovery IPC/Host, RuntimeOrchestrator,
Coding Tools MCP, connected-agent và package verifier. Bằng chứng hiện tại là
`SOURCE_PRESENT + FOCUSED_TEST_PROOF`: same-account **3/3**, document E2E **3/3**,
exec parity **12/12**, Control Plane **289/289**, integrated MCP Python **1.153 PASS /
0 FAIL / 7 SKIP trên 1.160**, Node/Electron **858 PASS / 16 SKIP / 0 FAIL trên
874**. Exact Windows package/fuse/DPAPI/ACL/live toolchain, hai
ChatGPT client thật, fault matrix T01–T16 và soak 24 giờ vẫn chưa đóng; không
được gọi là `PACKAGED_PROOF` hay `LIVE_ACCEPTED`.

## Checkpoint test-runner và regression — 21-09-2026, 04:38 +07

Đã sửa đường `npm run test:mcp` để dùng `scripts/run-python.js --module pytest`,
chọn đúng interpreter theo host; `pytest>=8,<9` đã được khai báo trong dev
extra. Regression sau sửa: Python Control Plane **289/289 PASS trong 92.465s**;
Node/Electron **874 tests: 858 PASS / 16 SKIP / 0 FAIL trong 43.485s**;
release-runner **2/2 PASS**; source-root, secret check, `node --check` và
`git diff --check` PASS. Host hiện chưa cài module `pytest`, nên
`npm run test:mcp` dừng ở `No module named pytest`; đây là dependency gap của
môi trường, chưa phải MCP pytest proof. Cài dev extras rồi chạy `npm run test:all`
là bước kế tiếp trước Windows package gate.

## Checkpoint Python 3.14 runtime hardening — 21-09-2026, 04:44 +07

Đã sửa semantic fingerprint để hỗ trợ hằng `slice` và sửa Landlock standalone
helper để resolve package imports trước khi chạy command. Bằng chứng focused:
`test_wave_a_runtime` **12/12**, `test_landlock_exec` **3/3**, continuation
identity/structured argv **2/2**, continuation patch/proof-replan **2/2** và
`py_compile` đều PASS. Đây là source/local proof; Windows package/live và
`npm run test:mcp` đầy đủ vẫn mở vì host chưa cài `pytest`.

Bổ sung proof local: `test_controller_continuity` + `test_controller_reattach`
**21/21 PASS**; `test_run_continuation` **50/50 PASS**. Đây là source/local
proof, không thay thế pytest suite hoặc Windows live acceptance.

Sandbox pytest **9.0.2** chỉ collection được **1158 items / 1 error** vì thiếu
`mcp`, lại không khớp constraint `<9`; không tính là pytest proof. Cần cài dev
extra đầy đủ trên host/pipeline rồi chạy lại `npm run test:all`.

## Checkpoint package/resource preflight — 21-09-2026, 04:46 +07

`npm run dist:dir` tạo `dist/linux-unpacked` và verifier đạt; packaged/installed
helper tests **3/3 PASS**; smoke runtime trả `windows_only` đúng contract. Đây
là Linux preflight, chưa phải Windows fuse/Recovery/DPAPI/ACL hoặc
`PACKAGED_PROOF`.

## Checkpoint Wave 42 — Windows exact rebuild/install passed; Ubuntu deploy blocked — 21-09-2026, 21:25 +07

Windows `main@bb4522c` đã chạy trọn build gate: Node/Electron **922/922 PASS**,
MCP **1160/1160 PASS trong 2764,26s**, resource verification PASS. Installer
`1.0.7` SHA-256 `61fb7fa5785c3861fcd4c8371f54172894472c9a0b7d48854c5cb05126d7c14e`;
executable installed khớp unpacked `a57ced0d185472d5c5e234a1177bf13ca35f14d2661300fc80e92c6daa7ecbd2`.
Packaged recovery smoke PASS (17 resources, 8 tools, Recovery/MCP/Supervisor
isolation). Windows worktree sạch sau khi hoàn tác icon build-only.

Đây vẫn là `PACKAGED_PROOF`, chưa `LIVE_ACCEPTED`: activation epoch production
đang `STOPPING/CLOSED`, không có workspace/connector/authority live. Ubuntu
release exact HEAD đã build/verify cục bộ với schema 24 và fingerprint
`sha256:52889093c453e4b5fbbf82ddb593fb150ebe73e8d32a307d04cae81b59af3bc6`,
nhưng SSH quản trị bị từ chối nên service chưa nạp artifact mới; admission vẫn
`recovery`, chưa mở binding/task.

## Checkpoint W2 focused execution parity — 21-09-2026, 04:08 +07

Đường `exec_command` structured argv hiện đã có focused parity proof cho bốn
nhóm thao tác Git/build/test/deploy: cùng task/writer lease/binding, poll qua
node, Recovery bridge thật và terminal receipt cho từng action. Test mới
`test_oauth_exec_workflow_parity_uses_one_local_lane` nâng HTTP→node→Recovery
exec suite lên **12/12 PASS trong 22.262s**.

Các argv được fixture ghi nhận là `git --version`, `npm run build`, `npm test`
và `npm run deploy`. Allowlist vẫn nằm ở policy local; Ubuntu chỉ chuyển
structured argv và target bất biến. Vì peer MCP là deterministic fixture, mức
bằng chứng chỉ là **`FOCUSED_TEST_PROOF`**. Chưa có Windows packaged/live
toolchain, deploy thật, reboot/reconnect/revoke/rotation live hoặc hai client
ChatGPT thật cùng `principal_id`.

Bước kế tiếp là W2 packaged command proof trên Windows (Git/build/test/deploy
thật), sau đó W3 same-account two-client acceptance; không tạo executor Ubuntu
thứ hai và không gọi provider model.

## Checkpoint packaged preflight — 21-09-2026

Preflight trên Linux đã tạo `dist/linux-unpacked` và verifier xác nhận resource
allowlist/byte identity cùng các bridge document/exec/approved-patch/file-read.
Hai test helper packaged/installed đạt **3/3 PASS**; nhóm Node build/package
verification liên quan đạt **12/12 PASS**; smoke runtime chính trả
`windows_only` nên được phân loại là skip có chủ đích. Lệnh Windows mặc định
dừng ở `build.electronDist` vì nó trỏ tới Linux Electron; một override CLI tạm
thời đã tạo PE `dist/win-unpacked/Coding Tools MCP.exe` và verifier độc lập đạt
**285 resource files + 9 adapter files**, nhưng `afterPack` fail-closed khi
`assertRunAsNode` cố chạy `.exe` trên Linux. Cần exact Windows build/smoke để
xác minh fuse/runtime và mới ghi `PACKAGED_PROOF`.

## Checkpoint same-account multi-binding focused proof — 21-09-2026

Test mới `test_same_account_selects_multiple_bindings_without_retargeting_existing_task`
đã chứng minh qua HTTP facade rằng hai token cùng `principal_id` nhìn thấy hai
`binding_id`; task A trên binding A và task B trên binding B không lẫn đích, còn
client B observe task A vẫn nhận target A. Cùng hai regression account/task
khác đạt **3/3 PASS trong 3.102s**. Đây chỉ là focused source proof; ChatGPT
client thật, Windows package và Job live handoff vẫn chưa nghiệm thu.

## Checkpoint sau W1 E2E + full regression — 21-09-2026, 03:55 +07

Working tree vẫn ở `codex/control-plane-quarantine@502ffb8cf8b541ee74af30194aff2dce08c3b649`;
đã xử lý relay/crash setup, thêm lost-ACK proof và chạy lại regression. Không
tạo Job live, không thay đổi live state, không commit/push/deploy/restart và
không gọi provider trả phí.

### Account chung và workspace target

Một account ChatGPT/OAuth xác minh thành `principal_id` duy nhất trong control
plane. Các máy/client cùng account có thể chọn cùng `binding_id`; ID này trỏ
đến đúng device/endpoint/workspace đã bind. Mỗi task vẫn pin immutable tới
`{device_id, endpoint_id, workspace_id, workspace_generation}`. Vì vậy client B
có thể gửi việc tới workspace của máy A nếu chọn cùng binding, nhưng không thể
retarget task A đang chạy. Ubuntu làm auth/router/queue/receipt; node A giữ
credential, file, Git, process và quyền OS local.

### Source và proof hiện tại

- Đã có W1 source path: `recovery_document_write_bridge.cjs`,
  `RecoveryHost` handler `runtime.control_plane_document_write`, node
  `document_write` poll/loop/CLI, journal/lock và lane thứ năm trong
  `run-connected-agent`; packaged resource allowlist/smoke cũng đã cập nhật.
- Central document admission, task/writer/generation/idempotency và digest-only
  receipt validator đã có từ batch trước.
- CJS bridge đã nâng `MAX_REQUEST_BYTES` lên `512 KiB`, trong khi document
  content cap là `256 KiB`; boundary dưới/trên cap có proof.
- HTTP→node→Recovery→Coding Tools MCP document E2E **3/3 PASS**: create/convert
  file thật, crash sau effect thành `unknown/reconcile_required`, và mất ACK
  replay receipt không redelivery. Bridge/adapter focused **10/10 PASS**;
  Python document node-agent + E2E focused **8/8 PASS**.
- Full Python control-plane: **289/289 PASS trong 91.287s**. Full Node/Electron:
  **873 tests; 857 PASS / 16 SKIP / 0 FAIL trong 43.611s**; source-root và
  repository-secret checks PASS. `py_compile`, `node --check`, `git diff --check`
  PASS.

Mức hiện tại vẫn là **`SOURCE_PRESENT + FOCUSED_TEST_PROOF`**. Chưa được ghi là
`PACKAGED_PROOF`/`LIVE_ACCEPTED`; chưa có Windows package/DPAPI/ACL/reboot/
revoke/rotation, full Git/build/test/deploy acceptance hoặc hai client ChatGPT
thật cùng `principal_id`.

### Tận dụng và việc kế tiếp

Đã tận dụng OAuth/account inventory, `ControlPlaneStore` bindings/task/writer
leases/generation, enrollment và credential riêng theo device, heartbeat/
reconnect/rotation, workspace registry/capability `{read,write,exec}`, standing
policy v2, journal/receipt, `RecoveryIpcServer`, `RecoveryHost`,
`RuntimeOrchestrator`, Coding Tools MCP và connected-agent worker. Không dựng
lại credential, queue, executor Ubuntu, hay cơ chế copy context/token.

Thứ tự tiếp theo: (1) W2 parity cho Git/build/test/deploy trên structured local
runtime; (2) Windows packaged/live DPAPI/ACL/startup/reconnect/revoke/rotation;
(3) same-account two-client acceptance với binding/task/writer handoff;
(4) release/soak/evidence và owner acceptance; (5) chỉ khi thật sự cần mới
thêm provider gateway cho server-side inference.

## Checkpoint baseline trước khi nối W1 — 21-09-2026, 03:18 +07

Working tree được xác minh ở branch `codex/control-plane-quarantine`, HEAD
`502ffb8cf8b541ee74af30194aff2dce08c3b649`; không tạo Job, không thay đổi live
state, không commit/push/deploy/restart và không gọi provider trả phí.

- **Python:** `279/279 PASS` trong `84.520s`.
- **Node/Electron:** `868 tests; 852 PASS / 16 SKIP / 0 FAIL` trong `43.845s`;
  source-root và repository-secret checks PASS.
- **Syntax/integrity:** `py_compile`, `node --check` các bridge/runtime liên
  quan và `git diff --check` PASS.
- **Central document create:** focused `1/1 PASS`; đây mới là durable
  admission/queue/idempotency proof, không phải file-effect proof.
- **Document bridge/runtime guards:** focused `14/14 PASS`; chưa có
  Recovery-process create/convert test.

### Reuse map và gap còn lại

Account ChatGPT dùng chung được biểu diễn bằng cùng OAuth `principal_id`; mỗi
client chọn `binding_id`, còn task bị khóa vào exact device/endpoint/workspace/
generation. Ubuntu chỉ xác thực, xếp hàng và lưu receipt. Node giữ credential,
file, Git, process, build/test/deploy và quyền OS local. Đã tận dụng OAuth/account
inventory, `ControlPlaneStore`, enrollment/rotation, heartbeat/reconnect,
workspace registry, standing policy v2, journal/receipt, Recovery IPC/Host,
RuntimeOrchestrator, Coding Tools MCP và connected-agent worker; không có
credential/context copy hay active workspace toàn tài khoản.

W1 document-write mới có central schema/admission, Electron bridge,
RuntimeOrchestrator và node helper/journal source. Chưa có CJS descriptor-hiding
bridge, RecoveryHost handler, node poller/CLI/lane connected-agent và
Recovery-process file-effect/fault proof. Do đó chưa quảng bá `doc_create` hoặc
`doc_convert` là quyền ghi live; Windows packaged/DPAPI/ACL/reboot/revoke/
rotation và hai ChatGPT client thật vẫn là gate sau.

## Checkpoint validation mới nhất — 21-09-2026, 03:05 +07

Đã chạy lại test trên working tree hiện tại; không tạo Job, không đổi live
state, không commit/push/deploy/restart và không gọi provider trả phí. Git vẫn ở
`codex/control-plane-quarantine@502ffb8cf8b541ee74af30194aff2dce08c3b649`,
worktree dirty có chủ ý.

- Python control-plane: **279/279 PASS** trong **83.534s** với
  `PYTHONPATH=control-plane python3 -m unittest discover -s control-plane/tests -v`.
- Node/Electron: **868 tests; 852 PASS / 16 SKIP / 0 FAIL** qua `npm test`;
  source-root và repository-secret checks PASS.
- `node --check`, `py_compile`, `git diff --check`: PASS.
- Document central create: **1/1 PASS**; đây là admission/queue/idempotency
  proof, không phải node file-effect proof.

## Tóm tắt account chung và phần đã tận dụng

Một OAuth-verified `principal_id` có thể được nhiều ChatGPT client dùng chung;
mỗi task chọn `binding_id` và bị pin tới
`{device_id, endpoint_id, workspace_id, workspace_generation}`. Ubuntu giữ
auth/queue/receipt, còn máy đã bind giữ workspace, credential, Git, process và
quyền OS local. Đã tận dụng OAuth/account inventory, `ControlPlaneStore`
bindings/task/writer leases, node enrollment/credential/heartbeat/rotation,
standing local policy, node journal, Recovery IPC/Host, RuntimeOrchestrator và
Coding Tools MCP. Vì vậy chưa cần dựng lại credential theo máy, queue task,
hay một executor trung tâm mới.

W1 document-write hiện mới ở mức central schema/admission + Electron bridge
source. Còn thiếu node `document_write` poller, CJS Recovery bridge, handler
RecoveryHost và Recovery-process create/convert proof; không được gọi đây là
full write capability. Hai client ChatGPT thật, Windows packaged/live,
DPAPI/ACL/reboot/revoke/rotation live và provider gateway (nếu cần) cũng chưa
đóng gate. Kế hoạch chi tiết và điều kiện nghiệm thu nằm ở
[TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md](TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md).

## Recheck tài liệu mới nhất — 21-09-2026, 02:50 +07

Lượt này chỉ cập nhật tài liệu và đối chiếu source/status; không chạy lại test,
không tạo Job, không thay đổi live state, không commit/push/deploy/restart và
không gọi provider trả phí. Các số liệu bên dưới là checkpoint validation gần
nhất lúc 02:40 +07 trên cùng working tree.

Mô hình vận hành đã chốt là **một tài khoản ChatGPT/OAuth `principal_id` dùng
nhiều controller, chọn `binding_id` để định tuyến tới máy có workspace**.
Ubuntu giữ auth/queue/receipt; node Windows giữ file, Git, process, build/test/
deploy và quyền OS local. `binding_id` không phải token; task luôn pin tới
`{device_id, endpoint_id, workspace_id, workspace_generation}` và không có
`active_workspace` toàn tài khoản.

Sau khi bổ sung central document-write schema, lỗi DDL dấu phẩy thừa đã được
sửa. Validation hiện hành trên working tree:

- Python control-plane discovery: **279/279 PASS trong 82.053s**; focused central
  document-create test **1/1 PASS** (task-session file **12/12 PASS**).
- OAuth/task/exec/HTTP focused group: **85/85 PASS**.
- Node/Electron `npm test`: **852 PASS / 16 SKIP / 0 FAIL** trên 868 test; source
  root và repository-secret checks PASS.

Điểm cần nói rõ: `document_workflow` read đã có standing-policy proof;
`doc_create`/`doc_convert` mới có central schema/admission và relay validator
ở mức source. Node document-write lane, Recovery process bridge, Windows
packaged/live và hai ChatGPT client thật **chưa nghiệm thu**, nên không bật hoặc
gọi đây là full write capability. Bảng tái sử dụng, wave W0–W6 và T01–T16 nằm
trong [kế hoạch hiện hành](TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md).

**Next implementation batch (W1):** thêm poller lane `document_write`, bridge
`RecoveryIpc/RecoveryHost/RuntimeOrchestrator` riêng cho document create/convert,
gọi `document_workflow` trên exact workspace local và ghi receipt
`prepared/completed/rejected/unknown` với task/writer/generation correlation.
Phải có stale-path/generation/allowlist/overwrite rejection và crash/lost-ACK
proof trước khi mở capability write trên node.

> **Hướng dẫn hiện hành — 21-09-2026:** xem
> [kế hoạch, hiện trạng và bảng tái sử dụng theo tài khoản/workspace](TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md).
> Các snapshot/receipt trong tài liệu này giữ nguyên ngày quan sát; những mô tả
> schema 8, admission hay gate pilot dưới đây không phải xác minh live hiện tại.
> Receipt mới hơn và giới hạn bằng chứng được phân loại trong kế hoạch mới.

**Cập nhật kiểm tra lại:** 21-09-2026, 02:24 +07 cho working-tree G4-F → G4-K,
SecretStore, node-agent credential protection, schema-22 rotation, Electron
owner-mediated rotation, account presence inventory và connected-agent worker;
wave G4-K/SecretStore lúc 22:21–01:40 +07 bổ sung Recovery restart/crash fixture,
lưu secret crash-safe ở mức source, bảo vệ node credential bằng DPAPI envelope,
rotation prepare/activate/ack ở mức source, hoàn tất Node/Python regression và
cập nhật tài liệu và standing patch qua Recovery process thật. Lượt 02:24 chỉ
chốt rõ semantics một account ChatGPT → nhiều client → `binding_id` chung;
không thay đổi source/live state. Các snapshot
deployment bên dưới giữ mốc 15-09-2026, khoảng 08:58–20:26 +07:00
(Asia/Ho_Chi_Minh).

**Trạng thái:** Pilot có kiểm soát — chưa đủ bằng chứng để gọi là production hoặc autonomous execution.

Tài liệu này phân biệt kiểm tra hiện hành với snapshot triển khai trước. Các tài liệu trong `docs/research/` là chronology/evidence tại thời điểm viết và không bị sửa để làm chúng trông như trạng thái hiện tại. Kế hoạch chi tiết và ma trận nghiệm thu hiện hành ở [TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md](TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md); các receipt cũ bên dưới chỉ giữ giá trị lịch sử.

## Checkpoint working tree hiện hành — G4-F → G4-K Recovery exec/stop/reconcile/crash-restart + presence/connected agent, 21-09-2026

Đây là bằng chứng source/focused trên working tree, **không phải** activation
của Ubuntu release bên dưới và không phải packaged/live Windows acceptance.

- Central OAuth HTTP, node heartbeat/poll, local standing exec policy, journal
  và receipt store chạy thật trong fixture. Node agent gọi một Node process
  fixture riêng có `RecoveryIpcServer`, `RecoveryHost` và
  `RuntimeOrchestrator.controlPlaneExec()` thật; peer Coding Tools MCP chỉ là
  HTTP fixture deterministic cho health/bind/exec/control.
- `exec_run` trả một handle `running`; poll sau đọc lại handle và gọi
  `exec_poll` mà không spawn lại. Stop giữ `pending` cho tới khi
  `command_control(kill)` trả terminal evidence, sau đó mới ghi `stopped`
  receipt và acknowledge stop.
- Sửa lỗi trung tâm: `store.py` đưa `stopped` vào
  `TERMINAL_RECEIPT_STATES`; trước đó receipt hợp lệ bị HTTP 400 và action giữ
  `accepted`. Teardown đóng process stderr pipe để không để warning tài nguyên.
- G4-G phát hiện một ranh giới journal trong đó `request/result` của Job
  `running` chỉ được ghi sau khi receipt gửi đi. Node agent nay persist atomic
  projection đầy đủ trước network boundary; fault fixture làm central commit
  `accepted` rồi bỏ ACK và chứng minh poll sau replay receipt, gọi `exec_poll`
  đúng handle, không gọi lại `exec_run`.
- G4-H đóng socket MCP ngay sau `exec_run`; node ghi một receipt
  `unknown/reconcile_required`, lần poll sau không re-dispatch và không gọi
  `exec_poll` trên effect không rõ kết quả.
- G4-I làm mất ACK sau khi central đã ghi terminal `completed`; node giữ payload
  terminal trong journal, poll sau replay đúng receipt và không relay lại Job.
- Validation: HTTP→Recovery process E2E exec/stop/lost-ACK/disconnect/
  terminal-ACK/crash-restart/running-restart/terminal-crash/terminal-ACK-restart/
  stop-pending-restart/writer-job-handoff **11/11 PASS**;
  `test_store` **85/85** ở lane fault; `test_mcp_exec` **8/8**;
  `test_exec_node_agent` **21/21**; node-secret protection **8/8**; node
  credential rotation **5/5** và HTTP **1/1**; mốc trước Recovery-process
  standing patch, full control-plane discovery **275/275 PASS**; `test_store`
  **83/83 PASS**;
  OAuth module **24/24 PASS** với
  `unknown → online → offline`; `py_compile`,
  `node --check`, `git diff --check`
  PASS. SecretStore focused **5/5 PASS**. Full Node đã hoàn tất với **868
  tests: 852 PASS / 16 SKIP / 0 FAIL**. Recovery Supervisor source test
  **1 PASS / 1 SKIP / 0 FAIL**.
  Đây chỉ là `FOCUSED_TEST_PROOF`; chưa chứng minh terminal Recovery crash/
  restart, duplicate-effect/reconcile đầy đủ, Windows package/live, hai ChatGPT
  client thật, read/write/Git/build/test/deploy end-to-end hay soak.

## Checkpoint mới nhất — standing patch qua Recovery process thật, 21-09-2026, 02:00 +07

Standing approved-patch hiện đã đi qua process fixture có thật
`RecoveryIpcServer` → `RecoveryHost` → `RuntimeOrchestrator` → Coding Tools
MCP, thay vì chỉ gọi bridge giả lập:

- Crash sau local MCP đã ghi file nhưng trước khi bridge nhận kết quả: **1/1
  PASS**; node gửi một receipt `unknown`, central giữ
  `reconcile_required`, restart process không redeliver `apply_patch`.
- Central commit `completed` rồi mất ACK: **1/1 PASS**; approved-patch journal
  replay đúng terminal receipt, store idempotent và observation chỉ có một
  `apply_patch`.
- Standing bridge request nay bắt buộc có `authority_mode=standing`; adapter
  Recovery chuyển đủ `task_id`, `writer_lease_generation`, `run_id`, `wave_id`
  và postimage metadata trước lớp allowlist. Đây là sửa lỗi contract lộ ra chỉ
  khi chạy process thật, không mở rộng quyền OS.

Validation của wave: approved-patch HTTP→node class **5/5 PASS trong 11.771s**;
full Python control-plane discovery **278/278 PASS trong 82.054s**; Node
approved-patch/Recovery bridge **12/12 PASS**; `node --check` và
`py_compile` PASS. Mức bằng chứng vẫn là source/focused trên working tree,
chưa phải Windows packaged/live hoặc Ubuntu live activation.

### Standing artifact/document-read parity — 21-09-2026, 02:18 +07

Artifact `document_workflow` read hiện dùng cùng file-read policy standing
schema v2 (`authority_mode=standing`, `expires_at_ms=null`) thay vì quay lại
TTL context. Node vẫn kiểm đúng workspace generation, root-relative allowlist,
UTF-8/size cap và receipt digest; test không mở quyền ghi và không tự gọi
Recovery/MCP ngoài scope đọc.

Focused proof: `test_standing_artifact_read_uses_the_same_local_policy_without_ttl`
**1/1 PASS**; toàn bộ `test_file_read_node_agent.py` **10/10 PASS**. Đây là
source/local proof cho parity của document read. Document create/convert,
Recovery-process document bridge, Windows packaged/live và hai client ChatGPT
thật vẫn chưa được nghiệm thu.

### Standing-write source checkpoint — 21-09-2026, 00:52 +07

Local policy v2 vẫn có `authority_mode=standing` cho file-read/approved-patch/
exec và connected-agent không phụ thuộc TTL read-only để heartbeat. Central
`agent_workflow.apply_patch` nay có profile
`control-plane-oauth-standing-write-v1`, schema-23 `mcp_standing_patch_intents`
và không yêu cầu `permission_request_id` trong scope đã bật. Admission vẫn bắt
principal OAuth + distinct write scope + `binding_id`/task + writer
lease/generation + exact path/digest/envelope/contract; node tiếp tục kiểm
local policy/OS trước effect. `request_permissions` chỉ còn cho legacy hoặc
escalation ngoài scope.

Focused test `test_standing_write_queues_without_per_patch_permission_and_replays`
và HTTP→node `test_oauth_standing_write_to_node_patch_to_verified_status` là
**2/2 PASS**; full Python discovery **275/275 PASS**. E2E này đã chứng minh
tools/list standing capability, writer claim, không có `permission_request_id`,
node poller admission bằng local standing policy, file write trong fixture,
completed receipt và MCP status projection; facade projection được sửa để
chấp nhận action `authority_mode=standing` mà vẫn reject field/mode sai. Đây
mới là `SOURCE_PRESENT + FOCUSED_TEST_PROOF`: chưa có standing fault/
duplicate-effect/reconcile đầy đủ, Windows packaged/live acceptance, hai
ChatGPT client thật hoặc full read/write/Git/build/test/deploy E2E.

### Standing HTTP→node completed receipt — 21-09-2026, 01:08 +07

Fixture E2E mới đã chạy đúng chuỗi:

```text
OAuth bearer + linked principal
  → tools/list standing contract
  → task_control.writer_claim
  → agent_workflow.apply_patch (không permission_request_id)
  → node `/poll` + policy v2 standing
  → local bridge fixture ghi file
  → completed receipt
  → MCP patch_status relay digest-only result
```

`_completed_approved_patch_relay()` trước đó chỉ chấp nhận exact action fields
của owner-review; standing action có thêm `authority_mode=standing`, vì vậy
receipt đã completed nhưng status bị trả `pending_or_unverified`. Source đã
được sửa để standing bắt buộc đúng `authority_mode=standing` và compatibility
`permission_request_id=standing`, còn owner-review vẫn không được mang field
standing. E2E `test_oauth_standing_write_to_node_patch_to_verified_status`
**1/1 PASS**; approved-patch HTTP E2E + task facade **14/14 PASS**.

**Git/run state:** branch `codex/control-plane-quarantine`, HEAD
`502ffb8cf8b541ee74af30194aff2dce08c3b649`, worktree dirty; lượt này không
commit, push, deploy, restart service hoặc gọi provider trả phí. Bước kế tiếp là
Windows packaged/live DPAPI/ACL migration and rotation/retry proof, sau đó G4-K
duplicate-effect/reconcile còn lại và packaged/live gates.

### Latest standing HTTP→node verification — 21-09-2026, 01:19 +07

The affected approved-patch HTTP class was rerun after the stale-generation
fixture was added: **3/3 PASS**. It covers the owner-review regression, the
standing path without `permission_request_id` through node poll/local policy to
completed receipt and `patch_status`, rejection of a stale local workspace
generation before the mutation bridge, and an explicit `unknown`/
`reconcile_required` observation that cannot be retried. The full Python
control-plane discovery then passed **275/275 in 73.574s**. A SQLite
`ResourceWarning` remains, but there was no test failure.

This is still source/focused evidence on the dirty working tree. It does not
close standing stale-preimage/path or lost-ACK/duplicate-effect proof, Windows
packaged/live DPAPI/ACL/startup/reconnect/rotation, two real ChatGPT clients,
full read/write/Git/build/test/deploy, or the 24-hour soak.

### Standing fault proof continuation — 21-09-2026, 01:32 +07

The same HTTP→node standing fixture now proves two additional boundaries:

- A local `CONTROL_PLANE_APPROVED_PATCH_PREIMAGE_MISMATCH` becomes one settled
  `rejected` receipt and leaves the fixture file unchanged.
- If the central service commits `completed` but the node loses the response,
  the journal retries the same receipt; the store replays it idempotently and
  the bridge is not invoked again. Only one terminal receipt remains.

The affected HTTP class is **3/3 PASS**; node/store/task regression is
**105/105 PASS**; full Python discovery is **275/275 PASS in 74.546s**. The
remaining `ResourceWarning` messages are SQLite cleanup hygiene, not failures.
This is still source/focused proof, not exact Windows/Recovery packaged proof.

### Standing path-deny + full regression — 21-09-2026, 01:37 +07

The standing fixture now also sends a valid exact-file envelope for a relative
path outside the local allowlist. Node admission settles it as `rejected`
before the mutation bridge and does not create the target file. The affected
HTTP class is **3/3 PASS**; node/store/task regression is **105/105 PASS**; full
Python discovery is **275/275 PASS in 74.631s**. `git diff --check` and updated
document whitespace checks pass. Terminal-unknown/duplicate-effect proof on the
remaining Recovery boundaries and all Windows/live/multi-client gates remain
open.

### Standing terminal-unknown — 21-09-2026, 01:40 +07

The standing path now also handles a post-prepared bridge timeout as one
`unknown` receipt and central `reconcile_required` lifecycle. `patch_status`
reports the uncertainty without patch bytes, and a following poll does not
invoke the mutation bridge again. Full Python discovery is **275/275 PASS in
73.941s**; the remaining warnings are SQLite cleanup hygiene. This is still a
mocked HTTP fixture, not Recovery-process/package/live proof.

### G4-J — process crash sau `exec_run` không redeliver

Node agent ghi `prepared` trước khi gọi Recovery bridge. Nếu bridge trả lỗi sau
boundary này, entry không còn được phân loại là pre-effect `rejected`; node giữ
payload unknown với `code=CONTROL_PLANE_EXEC_EFFECT_UNKNOWN` và
`diagnostic_code`, gửi một receipt `unknown` rồi dừng retry effect. Process
fixture có thể tự thoát sau khi MCP đã ghi nhận `exec_run`; restart cùng data root
giữ observation và descriptor mới.

Focused proof: `test_exec_node_agent` **21/21**, E2E HTTP→Recovery **10/10**, full
Python discovery **254/254**. Đây là proof của process-crash/running-resume/
terminal-loss boundaries; central terminal ACK loss, stop-pending, Windows Job
handoff, packaged/live và two-client acceptance vẫn chưa đạt.

### G4-K partial — running handle resume và terminal result loss

Focused fixture hiện chứng minh hai boundary bổ sung:

- Sau receipt `accepted` cho Job `running`, Recovery process bị kill và khởi
  động lại. Node đọc local handle từ journal, gọi `exec_poll` qua process mới,
  settle terminal receipt và không gọi `exec_run` lần hai.
- Khi MCP đã trả terminal result nhưng Recovery chết trước bridge ACK, node giữ
  `unknown/reconcile_required`; restart không tự biến nó thành `completed` và
  không dequeue lại action.

Đây là **partial G4-K**; chưa có duplicate-effect/reconcile đầy đủ hoặc
writer lease/handoff trên Windows Job thật.

### G4-K continuation — terminal ACK và stop-pending qua Recovery restart, 20-09-2026, 22:34 +07

Hai boundary mới đã được kiểm chứng trên cùng process fixture Recovery/Electron:

- Central đã commit terminal `completed` nhưng node mất ACK; Recovery process bị
  kill ngay sau commit. Journal giữ terminal receipt chưa gửi, process mới chỉ
  replay receipt và không relay lại `exec_run`/`exec_poll`.
- Local MCP đã nhận `exec_stop` nhưng Recovery chết trước bridge response. Stop
  vẫn `pending`, không acknowledge sớm; process mới poll cùng handle, nhận
  observation stop đã có hiệu lực, ghi `stopped` rồi mới acknowledge.

Focused proof: E2E HTTP→Recovery **11/11 PASS**; node-agent + MCP fault/store/
exec lane **34/34 PASS**; `node --check`, `py_compile` và `git diff --check`
PASS. Đây vẫn là source/focused proof với MCP peer deterministic, chưa phải
Windows Job Object, packaged/live hay hai ChatGPT client thật. G4-K còn mở ở
writer lease unresolved/handoff và duplicate-effect/reconcile trên Job thật.

### G4-K writer lease trên Job local — 20-09-2026, 22:43 +07

E2E đã nối writer lease trung tâm với Job local qua node journal và Recovery
process. Task B cùng binding bị `CONFLICT` khi task A còn `running`; release
sớm của A cũng bị chặn. Sau terminal receipt, A release được lease và B claim
được generation mới. Observation giữ đúng một `exec_run` và một `exec_poll`.

Focused proof: HTTP→Recovery **11/11 PASS**, full Python discovery **255/255
PASS**. Đây chưa phải Windows Job Object packaged/live, hai ChatGPT client thật
hoặc deployment/soak proof.

### SecretStore checkpoint — 20-09-2026, 22:52 +07

Electron `SecretStore` hiện ghi envelope `schema_version=1` bằng temporary file
độc quyền + `fsync`, đặt mode owner-only, giữ `.bak` và thử backup khi primary
hỏng. Payload legacy được đọc một lần và migrate ở mutation kế tiếp. Nếu cả hai
bản hỏng hoặc encryption unavailable, `set/remove` fail-closed thay vì ghi đè
credential. Test [`tests/secret-store.test.js`](../tests/secret-store.test.js)
**5/5 PASS**; full Node **867 tests: 851 PASS / 16 SKIP / 0 FAIL**.

Đây chỉ là source/focused proof trên Linux với fake encryption. Chưa có bằng
chứng Electron `safeStorage`/Windows DPAPI live, ACL thật, migration node secret
khỏi `control-plane-node.json`, hay rotation chịu crash/mất ACK. Vì vậy tình
trạng thái vẫn là pilot có kiểm soát; SecretStore chưa đóng gate credential/G2.

### Node-agent credential protection checkpoint — 20-09-2026, 23:06 +07

`control_plane/node_agent.py` hiện có Windows-specific protected credential
path độc lập với renderer/Electron UI:

- `_write_config()` loại `node_secret` khỏi JSON Windows và lưu
  `node_secret_dpapi`; `_config()` giải mã chỉ trong memory, từ chối plaintext
  và protected value cùng tồn tại, và không fallback plaintext khi protection
  unavailable.
- Config legacy có raw `node_secret` được migrate ở lần đọc authenticated đầu
  tiên bằng temporary file độc quyền, `flush` + `fsync` và `os.replace`. Nếu
  migration lỗi, file cũ vẫn giữ nguyên; không tạo plaintext backup.
- [`test_node_secret_protection.py`](../control-plane/tests/test_node_secret_protection.py)
  **6/6 PASS**: Windows protected write, in-memory unwrap/reprotect, ambiguity
  refusal, fail-closed unavailable protection, legacy migration và non-Windows
  fixture compatibility. Full Python discovery sau patch **261/261 PASS**.

Đây là **SOURCE_PRESENT + FOCUSED_TEST_PROOF** dùng mocked Windows API, không
phải DPAPI live/ACL/packaged proof. `SecretStore` Electron **5/5 PASS** vẫn là
fake-encryption/Linux proof riêng; chưa có rotation hai pha chịu crash/mất ACK,
restart/reconnect trên exact package, Windows Job live hoặc hai ChatGPT client
thật. Không commit/push/deploy/restart/provider trong checkpoint này.

### Schema-22 node-mediated credential rotation checkpoint — 20-09-2026, 23:29 +07

The previous operator-facing one-shot rotation is now fail-closed. The source
contract is a durable node-mediated sequence:

```text
candidate persisted locally → prepare(hash only) → activate(dual auth)
→ candidate promoted locally → ack(new credential) → old hash retired
```

- `node_credential_rotations` stores `rotation_id`, hash digests, generation,
  state and timestamps; it never stores the raw candidate secret. Repeating
  `prepare`, `activate` or `ack` for the same ID replays the durable row, while
  another active rotation is rejected.
- During `activated`, both old and new node credentials authenticate. Only
  `ack` with the new credential changes `nodes.credential_hash` and
  `credential_generation`; a lost response can therefore be retried safely.
- Node-agent pending candidates are protected through the same Windows DPAPI
  envelope source path and are removed after completion. CLI state resumes from
  `candidate_persisted`, `prepared`, `activated` or `promoted` without printing
  either credential.
- Focused proof: node-secret protection **8/8**, rotation store/agent **5/5**,
  HTTP route **1/1**; full Python discovery **269/269 PASS** in **75.868s**.

This is still **SOURCE_PRESENT + FOCUSED_TEST_PROOF** with mocked Windows API,
local SQLite and HTTP fixtures. It is not Windows packaged/live DPAPI, ACL,
operator-UI, real-machine rotation, or exact-package crash/soak proof.

### Electron owner-mediated credential rotation checkpoint — 20-09-2026, 23:43 +07

The Electron owner boundary now invokes the durable node-mediated rotation
protocol without exposing the candidate secret to the renderer or IPC. The
enrollment service calls only the packaged `node_agent.py rotate-credential`
command and parses a redacted state/generation receipt. Main IPC requires the
`central_executor` role and explicit `confirmRotation=true`; preload exposes
only the confirmed action, and the renderer shows state/generation after an
approved enrollment and can retry the durable phase.

Focused enrollment/manager/rotation proof is **25/25 PASS**. The full Node
suite is **868 tests: 852 PASS / 16 SKIP / 0 FAIL**; `node --check` and
`git diff --check` pass. This is still source/focused proof: Windows packaged
`safeStorage`/DPAPI, ACL, exact-build crash/lost-ACK rotation, and real
ChatGPT multi-client acceptance remain open.

### Account inventory presence checkpoint — 21-09-2026, 00:04 +07

`list_account_targets` now returns path-free `presence_state` and
`heartbeat_age_ms` for each active binding. A missing/invalid heartbeat is
`unknown`; a heartbeat no older than the 60-second threshold is `online`; a
stale heartbeat is `offline`. This observation is independent of task/context
authority and does not create a policy, action, failover or new credential.

The focused regression for `unknown → online → offline` is **1/1 PASS**; the
OAuth module is **24/24 PASS** and full Python discovery is **270/270 PASS** in
about **70.766s**. This uses a fake clock and SQLite fixture, so packaged
Windows heartbeat/reconnect, revoked-vs-offline reconciliation and two real
ChatGPT clients remain open.

### Connected-agent worker checkpoint — 21-09-2026, 00:22 +07

The packaged Supervisor command is now `run-connected-agent`. It publishes a
heartbeat before every iteration without requiring the expiring compact
read-only policy, then gates `file-read`, artifact, approved-patch and exec
polling on the corresponding standing local policy and current workspace
generation. Missing/disabled authority is a skipped lane, not a dequeue or
permission grant. Transport/runtime/auth failures use bounded reconnect
backoff, and a dedicated lock prevents duplicate connected agents; the legacy
`run-read-only-agent` remains a diagnostic compatibility command.

Focused connected-agent tests are **3/3 PASS**; full Python discovery is
**273/273 PASS** in **71.758s**. This is still source/focused proof, not exact
Windows packaged startup/reconnect, live heartbeat, revoked-vs-offline
reconciliation, two ChatGPT clients, or full read/write/Git/build/test/deploy
E2E.

**Next action:** run the exact Windows packaged candidate through DPAPI/ACL,
restart/reconnect and rotation crash/lost-ACK tests, then continue the remaining
G4 duplicate-effect/reconcile and write-path parity gates.

## Checkpoint hiện hành sau delivery local/GitHub

### Checkpoint immutable release + private HTTPS UI — 16-09-2026, 15:14–15:25 +07:00

Đây là deployment thật của central service và private operator UI; nó **không**
phải canary Windows, quyền execution hay production/autonomous acceptance.

- Ubuntu `svhome` / Tailnet `100.116.112.22` chạy chính service user hiện có.
  Candidate được extract vào release directory versioned, verifier artifact PASS
  với `25` file, schema `8`, revision
  `2e64e9485f37cf6f94e8144797ea800a6e050545` và package fingerprint
  `sha256:4bef62162e8a5ccc6de136dbabd2079d5c605a8bbf130aabf48de67655880040`.
  `current` trỏ release bất biến; main, backup và healthcheck unit đều nạp
  launcher/script từ release, không nạp Python/shell từ checkout.
- Trước switch, admission được operator đóng về `recovery` và snapshot legacy
  đã hoàn tất `Result=success`; inventory vẫn có 1 node/1 enrollment request
  và 0 binding/context/work request/action/receipt/intent. Không contact node,
  tạo binding hay dispatch công việc trong maintenance.
- Tailscale Serve được owner bật và proxy **tailnet-only** HTTPS
  `https://svhome.tail0e4032.ts.net/` tới upstream exact
  `http://100.116.112.22:8765`; không bật Funnel/public Internet. Lần start đầu
  fail-closed vì `EnvironmentFile` schema-7 ghi đè giá trị drop-in, tạo 502 ngắn
  hạn. Service được dừng, nguyên nhân được xác minh, chỉ các biến không bí mật
  (revision/fingerprint/backup/health/UI origin) được cập nhật rồi start lại;
  không che failure và không mở admission để lấy health xanh.
- Proof sau activation qua HTTPS: service `active/running`, SQLite integrity
  `ok`, schema `8`, actual/protected fingerprint khớp exact và admission vẫn
  `recovery`; GET-only deployment verifier với gate `recovery` PASS. Manual
  invocation của backup script release PASS. Timer backup/healthcheck vẫn
  enabled; healthcheck production cố ý yêu cầu admission `open`, nên nó không
  được dùng làm PASS trong khi maintenance recovery còn giữ.
- Browser-path proof thực qua HTTPS PASS: root UI, login session, overview và
  logout; cookie có `Secure`, `HttpOnly`, `SameSite=Strict`, CSRF được yêu cầu
  cho thao tác browser. Overview chỉ hiện central read model (1 node/1
  enrollment, 0 binding/context/work/action); session test đã logout. Không có
  token, DB path, receipt hoặc payload nhạy cảm trong checkpoint này.

**Gate còn lại:** release/UI central đã live nhưng RC-A chưa đạt. Windows
candidate vẫn unsigned/chưa cài production, không có strict-ready discovery,
binding/context/policy hoặc read-only end-to-end canary. Admission phải giữ
`recovery` cho đến khi owner cho phép pilot scope và kiểm tra node Windows mới.
Off-host encrypted backup/key-management, restore reconciliation và 24-hour
soak của exact deployed build cũng chưa đạt.

### Controlled production crash-restart and rebased soak — 15-09-2026, 20:24–20:26 +07:00

Đây là một crash-recovery proof của central service, không phải node effect,
remote reconnect hoặc quyền execution.

- Preflight xác nhận `Restart=on-failure` với delay 5 giây, no systemd jobs,
  node degraded và zero binding/context/work request/action/receipt/intent.
  Chỉ sau đó mới gửi `SIGKILL` tới **MainPID duy nhất** của
  `codex-control-plane.service`; không có admission change hoặc manual restart.
- Systemd ghi process exit `status=9/KILL`, scheduling restart và khởi động PID
  mới sau 5 giây; `NRestarts` tăng từ `0` lên `1`, listener Tailnet trở lại.
  Health của service instance mới PASS exact package fingerprint, schema `7`,
  SQLite `ok`, admission `open` và tất cả core action counts vẫn `0`.
- Healthcheck scheduled tiếp theo lúc 20:26 +07 PASS trên instance mới và
  snapshot automatic vẫn fresh. Không contact node, tạo policy/binding/action,
  chuyển backup hoặc restart component khác.

**Soak rebase:** window 20:02 bị gián đoạn có chủ đích bởi crash proof này, nên
không được gọi uninterrupted. Observation 24 giờ mới bắt đầu từ healthcheck
PASS 20:26 +07; criteria giữ nguyên: service instance/restart history, timer
cadence, fresh backup và health verifier phải được đối chiếu tại cuối window.

### Checkpoint isolated tmpfs full-filesystem fault drill — 15-09-2026, 20:18–20:22 +07:00

Checkpoint này hoàn tất proof T14 cho một filesystem `ENOSPC` **cô lập**. Nó
không làm đầy filesystem production, không chạy node, không tạo quyền execution
và không thay thế P3/soak còn lại.

- Probe đầu tiên dùng SQLite `max_page_count` bị loại: giới hạn đó chỉ áp vào
  connection filler, nên service connection vẫn tạo một intent/action synthetic.
  Artifact của probe được giữ, durable-quarantine với admission `recovery`,
  integrity `ok`; nó không được tính là proof T14 hoặc action production.
- Drill được chấp nhận chạy trực tiếp trong user+mount namespace rprivate với
  tmpfs `/tmp` 1 MiB; service fixture, database, filler và token scope đều chỉ
  tồn tại trong namespace. Filler chỉ tiếp tục khi nhận `ENOSPC`, sau đó fixed
  operator-authenticated `workspace_context(request_read_only)` nhận đúng HTTP
  `503` / `DURABLE_STORAGE_UNAVAILABLE` qua đường HTTP/SQLite thật.
- Filler được giải phóng bên trong private tmpfs để kiểm tra hậu quả: fixture
  giữ SQLite integrity `ok`, admission `open` và zero
  `work_requests`/`actions`/`mcp_read_only_intents`. Vì vậy failed intake không
  để partial durable state. Private mount tự unmount; host `/tmp` không có
  artifact drill và port loopback không còn listener.
- Verifier production sau drill tiếp tục PASS exact package/schema/integrity/
  admission, cùng PID và `NRestarts=0`. Không restart production, không contact
  node, không tạo binding/policy hay gửi snapshot qua mạng.

**T14 đạt trong phạm vi cô lập:** SQLite-busy và tmpfs-ENOSPC đều fail closed
qua HTTP, không false-ack durable intake. **P3 còn lại:** off-host/encrypted
backup, production restore/reconciliation, node reconnect/fault proof và soak.

### Baseline operational soak bị thay thế — 15-09-2026, 20:02 +07:00

Đây là mốc observation đầu tiên, không phải claim soak đã hoàn tất. Window này
đã bị gián đoạn có chủ đích bởi crash proof 20:24; checkpoint mới hơn định nghĩa
baseline uninterrupted thay thế.

- User service production đã active từ 19:01:53 +07, giữ cùng process instance,
  PID và `NRestarts=0` qua deployment, restore drill và SQLite-busy drill.
  Verifier production tại baseline tiếp tục PASS exact package fingerprint,
  schema `7`, SQLite `ok` và admission `open`.
- Hourly timer đã tự kích hoạt backup lúc 20:01:59 +07. Job kết thúc success
  lúc 20:02, tạo snapshot/inspection receipt owner-only mới; snapshot hash
  giữ `5fe01654…ad4ee0d` vì durable state không đổi, với schema `7`, integrity
  `ok` và zero unresolved action. Đây là scheduled run, không phải manual
  invocation, restart service hoặc node contact.
- Persistent journal còn giữ các healthcheck scheduled PASS lúc 19:38 và
  19:54 +07. Healthcheck scheduled tiếp theo lúc 20:10 +07 cũng PASS sau
  automatic snapshot mới, xác nhận cycle backup → freshness check → exact
  deployment verifier không restart service hoặc contact node. Backup directory
  mode `0700`, artifact/receipt mode `0600`; timer backup tiếp theo được
  systemd lên lịch sau một giờ.

**Acceptance đang chạy:** sau tối thiểu 24 giờ từ baseline, đối chiếu journal
và receipts với service instance/restart count, timer cadence, fresh verified
backup và health verifier. Bất kỳ restart, missing timer run, stale backup,
recovery admission hoặc package mismatch nào sẽ dừng claim soak và được
phân loại trước khi tiếp tục.

### Checkpoint isolated SQLite-busy fault drill — 15-09-2026, 19:45–19:53 +07:00

Checkpoint này là evidence T14/P3 giới hạn cho contention SQLite thật trên
fixture cô lập; nó không phải full-disk test, production fault, node effect hay
quyền mở execution.

- Fixture database owner-only riêng có một node/binding/context synthetic, ba
  event bootstrap và zero `work_requests`, `actions`, `mcp_read_only_intents`.
  Nó không dùng DB, token hay node policy production. Service fixture chỉ bind
  loopback và pin exact package fingerprint.
- Một transient lock-holder riêng đã lấy SQLite `BEGIN EXCLUSIVE`. Trong khi
  lock còn giữ, request operator-authenticated `/mcp` hợp lệ cho fixed
  `workspace_context(request_read_only)` nhận đúng HTTP `503`, error code
  `DURABLE_STORAGE_UNAVAILABLE` với response content-free. Đây là failure ở
  đường HTTP/SQLite thật, không phải mock.
- Sau release lock, verifier của service fixture PASS: schema `7`, SQLite `ok`,
  admission `open`, instance hợp lệ và fingerprint actual/expected khớp.
  Readback fixture giữ event count `3` và vẫn zero work request/action/read-only
  intent; vì vậy failed intake không có durable partial state để dispatch.
- Lock-holder và service fixture đều đã stop (`inactive/dead`, PID `0`); port
  loopback drill không còn listener. Production không restart và vẫn verifier
  PASS, active cùng PID, `NRestarts=0`. Clock host có NTP synchronization và
  monotonic-clock check bình thường; không ghi thời lượng fault từ timestamp
  wall-clock định dạng sai.

**P3 còn lại:** T14 full-filesystem proof được ghi riêng ở checkpoint mới hơn;
chưa có off-host/encrypted backup, production restore/reconciliation, node
reconnect/fault proof hoặc soak. Hiện
`/home` và state storage cùng một ext4 local; không quan sát được backup client
hay cấu hình remote đã sẵn sàng, nên không tự chọn đích/off-host key scheme.
Tailnet hiện có một Windows peer online và CLI hỗ trợ Taildrop, nhưng đây chỉ là
transport: chưa có evidence receiver retention/ACL, at-rest encryption hoặc
recovery key. Không snapshot nào được chuyển qua đường này.
Fault drill này chứng minh fail-closed durable intake dưới SQLite contention,
không đóng toàn bộ P3.

### Checkpoint isolated restore drill — 15-09-2026, 19:32–19:37 +07:00

Checkpoint này bổ sung bằng chứng P3 hẹp cho một **isolated drill**; nó không
phải production restore, quyền reopen admission, proof node effect hay
nghiệm thu 24/7.

- Snapshot automatic schema-7 được immutable-inspect trước khi dùng: integrity
  `ok`, SHA-256 `5fe01654…ad4ee0d`, admission nguồn `open`, không có delivery
  state hoặc unresolved action. Từ đó tạo một SQLite candidate mới, không đè
  production, với durable admission `recovery`, integrity `ok`, schema `7` và
  zero unresolved action. Artifact drill và thư mục chứa nó là owner-only
  (lần lượt mode `0600`/`0700`).
- Một transient user service riêng khởi động candidate trên đúng loopback
  `127.0.0.1:18765`, với token ngẫu nhiên chỉ cho scope drill, package
  fingerprint được pin. GET-only verifier PASS: schema `7`, SQLite `ok`,
  admission `recovery`, fingerprint actual/expected cùng
  `sha256:3f247e44c1b25658eb3bad2af313d13c7ec73ac250569e93a77463ba8aef64a9`.
  Health chỉ quan sát node/enrollment đã có và các nhóm
  binding/context/request/action/receipt/intent đều `0`; không gọi node,
  không tạo binding/policy/action và không dùng credential production.
- Candidate được inspect lại sau khi service dừng: schema/integrity/admission
  và delivery counts vẫn đúng (`recovery`, zero unresolved). Byte hash của
  candidate sau lifecycle khác receipt lúc tạo candidate, nên không được suy
  là byte-identical restore artifact. Khác biệt byte này được ghi nhận thay vì
  che giấu; bằng chứng drill được giới hạn ở semantic state và source snapshot
  hash.
- Unit drill đã được stop có chủ đích (`inactive/dead`, PID `0`), port `18765`
  không còn listener. Production không restart: `codex-control-plane.service`
  vẫn active cùng PID, `NRestarts=0`; verifier production sau drill vẫn PASS
  với admission `open`, schema `7`, integrity `ok` và exact fingerprint.

**P3 còn lại:** chưa có storage encryption hay bản sao off-host; fault drill
SQLite-busy được ghi riêng ở checkpoint mới hơn, nhưng full-disk test cô lập,
production restore/reconciliation, node reconnect/fault proof hoặc soak vẫn
chưa có. Do đó isolated restore drill không đánh dấu P3 hoàn tất.

### Checkpoint triển khai Ubuntu trực tiếp — 15-09-2026, 19:01–19:10 +07:00

Checkpoint này thay thế riêng các quan sát cũ nói rằng endpoint Ubuntu không
thể chứng minh package/schema hiện hành. Nó không thay thế các gate Windows,
client hoặc outcome bên dưới.

- **Source/delivery:** `main` đã delivery/push ở
  `000938f401b6d6605b0b94474cbc87b5171c2909`; patch
  `3f1bd8a` sửa contract identity của bridge: result action hiện dùng
  `process_instance_id` / `server_instance_id` thống nhất từ Runtime
  Orchestrator qua Recovery Host tới node wrapper. Focused bridge `5/5` và
  Recovery Host `37/37` PASS trước delivery. GitHub nhận ledger evidence theo
  retention invariant và cảnh báo size khoảng 93 MB; không chuyển LFS hoặc bỏ
  evidence khỏi Git.
- **Ubuntu service:** user unit `codex-control-plane.service` enabled, với
  `Linger=yes`, đang chạy sau restart có kiểm soát lúc 19:01 +07, bind riêng
  `100.116.112.22:8765` trong Tailnet, `Restart=on-failure`,
  `NoNewPrivileges=yes`, `PrivateTmp=yes`. Environment owner-only đã pin
  declared source revision và exact expected package fingerprint. GET-only
  deployment verifier PASS: SQLite integrity `ok`, schema `7`, durable
  admission `open`, process instance hợp lệ, fingerprint actual/expected cùng
  `sha256:3f247e44c1b25658eb3bad2af313d13c7ec73ac250569e93a77463ba8aef64a9`.
  Một curl ngay sau restart đã thấy socket chưa bind; verifier ngay sau đó và
  readback socket/health PASS, nên được phân loại startup transient đã giải
  quyết, không phải success giả.
- **Backup/retention:** đã tạo snapshot pre-migration schema-0, verified và
  immutable-inspected (SHA-256 `dae6fec1…d25e885`), trước migration. Profile
  automatic backup giờ chạy hourly với `Persistent=true`, jitter tối đa 5 phút,
  ngưỡng 5 GiB, owner-only storage và retention 30 ngày chỉ cho snapshot do
  job tạo. First live backup schema-7 đã PASS integrity/inspection, artifact
  hash `5fe01654…ad4ee0d`, admission `open`, unresolved actions `0`. Timer
  `codex-control-plane-backup.timer` enabled; service không restart và không
  contact node. Đây là backup local có ACL, **không** phải encrypted/off-host
  backup; isolated restore drill được ghi riêng ở checkpoint mới hơn. Root
  filesystem quan sát là ext4 trực tiếp; at-rest encryption không được suy ra.
  Companion healthcheck 15 phút cũng enabled; first check PASS exact
  package/schema/instance/admission và tuổi backup 759 giây. Lần scheduled
  sau drill lúc 19:38 cũng PASS. Nó chỉ ghi receipt content-free; recovery,
  backup stale hoặc package gate sai sẽ fail journal thay vì tự restart/reopen.
- **Deployment hygiene:** timer `codex-autopull.timer` đã disable. Nó từng
  `git pull` mỗi phút, va Git index trong delivery và có thể làm checkout mới
  nhưng service chưa reload. Không còn automatic source drift; future update
  phải đi qua snapshot → delivery → fingerprint pin → controlled restart.
- **Node/canary boundary:** Tailnet thấy node Windows `DaoChienThang` online
  (direct), nhưng central record hiện stale/degraded hơn 16 giờ, mcp server
  identity absent và chưa có binding/context/request/action/receipt. WinRM
  có mở nhưng yêu cầu Negotiate; Ubuntu không có credential/Kerberos session
  hay SSH listener hợp lệ. Không đoán password, không tạo binding từ identity
  cũ, không provision policy, không gọi bridge/canary hoặc mutation.

**Gate còn lại:** cần một kênh quản trị Windows được xác thực để lấy strict
current-process discovery/identity, chạy runtime-heartbeat, rồi tạo binding và
policy v2 có expiry trên exact target trước một `poll-read-only-once` canary.
Sau P1d mới xét mutation P2. P3 vẫn cần encryption/off-host backup arrangement,
full-disk drill, reconnect/fault proof và soak; P4/C/W/U/O
không tự được mở.

Checkpoint này là trạng thái vận hành mới nhất và **ghi đè các mô tả “uncommitted”, MCP revision mismatch hoặc P0 degraded trong phần chronology bên dưới**. Các đoạn cũ vẫn được giữ nguyên để bảo toàn bằng chứng thời điểm quan sát.

- **Git/source delivery:** payload control-plane/Electron/MCP/recovery/test và delivery snapshot được commit qua `745d839`, `cb788b9`, `50993da` rồi fetch lại từ `origin/main` với divergence `0 0`. Đây chứng minh payload bytes đã được delivery lên GitHub, không chứng minh Ubuntu đã pull/load chúng; checkpoint này có thể thuộc một follow-up documentation delivery riêng.
- **Windows Desktop technical activation:** sau authenticated `runtime.stop`, snapshot-consistent delivery và explicit full-clean refresh, `npm run dev:status` quan sát `state=CURRENT`, development installation current, UI running/disk revision khớp, MCP running/disk revision khớp, `components_ready=true`, `fully_ready=true`, `runtime_update_incomplete=false`, telemetry fresh. Đây là proof kỹ thuật local hiện hành, không phải proof remote effect hay release acceptance.
- **Connector boundary:** connector đang `CURRENT_COMPATIBLE_ACKNOWLEDGED` với contract SHA hiện hành khớp và không yêu cầu refresh/ACK thêm, nhưng `connector_rediscovered=false`. Chưa quan sát exact ChatWeb client thực hiện `server/discover`/`tools/list` trên MCP mới; không gọi đó là client E2E canary.
- **Ubuntu remote boundary:** chưa có deploy/restart/systemd/DB mutation trong checkpoint này. Lần thử SSH non-interactive vào target đã biết `svhome@100.116.112.22` bị từ chối `Permission denied (publickey,password)`, nên không có quyền hợp lệ để kiểm tra owner/checkout/unit hoặc đưa revision `50993da` lên Ubuntu. Preflight chỉ đọc tiếp theo cho thấy SSH agent không chạy, không có default identity trong `.ssh`, và một PEM còn lại không có binding đã chứng minh với target; không thử key/account suy đoán. Một verifier GET-only mới, dùng fingerprint `sha256:b8881db477fafa29ac79f0ef44a7b1bb040a151f04b118516c875c31fed7565f` của selected package hiện tại và expected admission `open`, tiếp tục trả `CONTROL_PLANE_DEPLOYMENT_HEALTH_INCOMPLETE` (exit 2). Vì vậy endpoint chưa cung cấp receipt exact deployed-package; không được suy từ health cũ thành remote state hiện tại.
- **Runtime evidence:** sau khi local runtime chạy lại, `.coding-tools/**` tiếp tục tạo evidence live. Chúng được giữ nguyên cho delivery transaction sau; không có source/document unstaged ngoài runtime evidence và các artifact tạm đã tồn tại trong `tmp/`.
- **Nghiệm thu còn thiếu:** Ubuntu exact-deployment receipt, authenticated service/backup/reboot/restore evidence, strict client rediscovery, central read-only canary rồi mutation canary theo policy, và natural workload có outcome độc lập. Không có mục nào trong số này được suy ra từ local tests, Git push hoặc `fully_ready=true`.

## Kiểm tra hiện hành từ E:/DEV/Codex-web

Baseline: `main`, HEAD `a0f3a6f5b9530e86e31a88a23b9b144482b3f8c6`, worktree sạch lúc bắt đầu assessment.

Delta lúc 09:17 +07:00 và lần status kế tiếp: một công việc đồng thời đang sửa `recoveryBootstrap.js`, `dev-ui-lifecycle.js`, `dev-ui-lifecycle.test.js`, `recovery-bootstrap.test.js` để thêm idle packaged→development handoff. Đây mới là source candidate chưa được assessment này kiểm thử/nghiệm thu/activate; không được coi là runtime đã phục hồi. Xem E10 trong kế hoạch mới và phối hợp với owner trước khi sửa trùng vùng. Backend control-plane được test không thay đổi.

**Delta P1a.1/P1a.2/P1a.3/P1a.4/P1a.5 + CI, `2026-09-15T10:47+07:00`:** source local `control-plane/**` đã được harden/test lại, thêm owner-scoped observation inventory, subprocess crash-boundary regressions ở cả hai phía `COMMIT`, intake revalidation để revoke node chặn context/request mới, strict-readiness projection, truthful identity-missing heartbeat và health provenance metadata; focused suite đã được gắn vào CI Linux+Windows, nhưng còn uncommitted. Đây không làm thay đổi endpoint Ubuntu đã kiểm lại lúc 10:25, hay quyền mở central execution.

**Delta P1b.0 identity observer, `2026-09-15T11:01+07:00`:** source local thêm duy nhất action Recovery IPC read-only `runtime.identity_observation`; node agent chỉ đọc nó sau strict aggregate readiness và chỉ tiếp nhận MCP process/server/epoch/current contract SHA đã sanitize. Schema v5 giữ server identity riêng, dispatch không admit thiếu một trong các identity. CJS observer 3/3, Recovery Host 36/36 và năm Python behavior proofs PASS; không có live call vì P0 hiện vẫn degraded. Đây không tạo actor/bridge/facade/grant/receipt hay quyền mở central execution.

**Delta P1c.0 status-only MCP facade, `2026-09-15T11:17+07:00`:** source local thêm `POST /mcp` operator-authenticated, stateless JSON-RPC cho MCP `2025-11-25`: exact tám public tool names, `initialize`/`tools/list`/`tools/call`, profile/hash và envelope `context_id`. Chỉ `workspace_context` đọc central owner-scoped context/node status và ghi rõ `workspace_accessed=false`; bảy tool khác trả `LOCAL_ADMISSION_BRIDGE_REQUIRED`. Nó không forward token/body, không gọi node, seal/poll action hay execute. Full HTTP API suite 7/7 PASS trong 7.357s. Đây không tạo client discovery proof, local schema/capability, bridge/relay, local workspace access, binding, receipt hay canary authority.

**P0/E29 audit cuối, `2026-09-15T11:20–11:23+07:00`:** Recovery IPC không có supported action cho node gọi local MCP; chỉ có identity observation đọc. Callers MCP Electron hiện hữu có token/client identity riêng của panel, watchdog hoặc control-center; không được tái dùng chúng làm central actor. Probe runtime tiếp theo vẫn `CURRENT` ở development installation, nhưng MCP running revision `72f8…` trong khi disk revision đã đổi tiếp thành `1fc…`; `mcp_update_pending=true`, `fully_ready=false`, connector compatible—not strict. Không restart/refresh hay gọi live observer/canary.

**Delta P1b.1 narrow local read-only bridge, `2026-09-15T11:46+07:00`:** source local thêm actor riêng `electron-control-plane-bridge`, policy local không credential/default-off/hết hạn, action Recovery IPC read-only và CJS wrapper che descriptor token. Chỉ `poll-read-only-once` explicit có thể chuyển một sealed action exact thành `workspace_context({detail:"compact",max_entries:1})`; ordinary `poll` is now a no-op and cannot dequeue central work. Host đòi exact device/owner/endpoint/workspace/generation/action/attempt/expiry, strict current-process connector và MCP identity; Runtime Orchestrator tự giữ local token/attestation. Node journal ghi `prepared` trước subprocess, lưu safe handle/digest trước receipt và map interruption thành `unknown`, không re-call. Policy không được tự tạo. Policy unit 3/3, Orchestrator 2/2, wrapper 3/3, Recovery Host 37/37 và Python Node-journal 2/2 PASS. Không tạo policy/action/binding thật, không gọi live bridge, không restart/deploy.

**P0/E31 final read-only recheck, `2026-09-15T11:52:29+07:00`:** Development installation vẫn `CURRENT`, Electron revision khớp và telemetry fresh; MCP running `72f8…` vẫn khác disk `1fc…`, `mcp_update_pending=true`, `components_ready=false`, `fully_ready=false`, `runtime_update_incomplete=true` và connector vẫn `CURRENT_COMPATIBLE_ACKNOWLEDGED`/compatible bootstrap. Ubuntu `/healthz` tiếp tục trả service/SQLite `ok`, node=1, nhưng bindings/contexts/work_requests/actions/receipts đều 0. Không SSH, restart, policy provision, live bridge, binding hay write được thực hiện.

**Delta P1c.1 redacted lifecycle status, `2026-09-15T11:57+07:00`:** `workspace_context` in the local status façade accepts an optional existing `action_id` only under the same context/owner. It returns action/attempt/receipt IDs, lifecycle state and digests, while excluding action arguments, admission reference, receipt payload, local handle and workspace path; wrong context is rejected. It never seals/polls/relays/calls a node. HTTP API suite 7/7 PASS in 8.991s. This is central observation only, not client-to-node proof.

**Final local integration proof, `2026-09-15T11:59+07:00`:** `py_compile` for Node agent/facade/HTTP API and the complete `control-plane/tests` suite passed **35/35 in 41.348s**, including P1b.1 completed/unknown-journal paths and P1c.1 redaction/wrong-context. This is local source evidence only; it is not a GitHub Actions, Ubuntu deployment, policy-provision, strict-runtime, live bridge or canary result.

**Delta P1c.2 fixed central read-only intent + safe legacy poll, `2026-09-15T12:14–12:18+07:00`:** schema v6 now records `mcp_read_only_intents` by owner, idempotency key and immutable digest. The operator-authenticated façade accepts only `workspace_context(operation=request_read_only)` with exact context, expiry and idempotency key, atomically creating one fixed `workspace_context({detail:"compact",max_entries:1})` request/action. Exact replay returns the same identifiers; changed expiry/payload conflicts and central recovery mode refuses new intake. The response remains `workspace_accessed=false` and `queued_for_local_admission`; it does not call, poll or authorize a node. Audit found that the legacy non-executing `poll` could still allocate `dispatch_unconfirmed` without a receipt, so it is now local-only `POLL_EXECUTION_DISABLED` and never calls central dequeue. Full `control-plane/tests` is **37/37 PASS in 44.681s**; current bridge CJS tests are 8/8 PASS and Recovery Host is 37/37 PASS in 13.332s. This is not deployment, policy, strict runtime, node poll, local workspace access or canary proof.

**Delta P1c.3 canonical provenance + truthful lifecycle, `2026-09-15T12:31–12:38+07:00`:** façade contract profile/schema v3 now supplies `central_lifecycle_state` only where durable action/attempt/receipt records define it. It never calls a send record a local effect or business outcome. A generic `seal_action` can no longer mint the one fixed read-only bridge shape; central delivery joins its canonical intent digest and the node verifies both digest and `mcp_facade:<digest>` admission reference before any local bridge attempt. Missing/mismatched provenance is terminally rejected pre-effect, not marked unknown. Full `control-plane/tests` is **40/40 PASS in 44.579s**. This remains source proof only: it is not a policy install, strict runtime, real node call, Ubuntu deployment, local workspace access or canary.

**Current P0/Ubuntu read-only recheck, `2026-09-15T12:38+07:00`:** Electron development UI is `CURRENT` and its running/disk revision now both read `c5a057…`; UI `update_pending=false` and telemetry is fresh. This does not open P0: MCP running `72f8c7…` differs from disk `cb7ff6…`, `mcp_update_pending=true`, `components_ready=false`, `fully_ready=false`, `runtime_update_incomplete=true`, and connector remains compatible bootstrap without rediscovery. Ubuntu `/healthz` remains service/SQLite `ok`, node=1 and binding/context/request/action/receipt=0, still without schema/admission/declared-source fields. No restart, SSH, deployment, policy, binding or action was performed.

**Delta P1b.1 typed receipt-transport recovery, `2026-09-15T12:44+07:00`:** Node transport now turns `URLError`/OS/timeout failures into the safe typed code `CONTROL_PLANE_TRANSPORT_UNAVAILABLE`. A local regression persists a completed receipt, injects the failed send, then proves the next invocation sends the exact durable receipt before any new poll while never calling the local bridge again. Complete local `control-plane/tests` suite is **42/42 PASS in 49.983s**. This covers only a simulated local transport boundary; it is not proof of a live central ACK loss, process crash, Ubuntu restore, installed policy, strict runtime or canary.

**Delta P1a/P3 explicit verified snapshot, `2026-09-15T12:55+07:00`:** new local command `python -m control_plane.maintenance snapshot` requires an existing SQLite source and opens it `mode=ro`, so it can create a verified, non-overwriting snapshot before a source initialization/migration without creating or upgrading the source. It emits only content-free metadata and typed `NOT_FOUND`/`CONFLICT` errors. A legacy-schema fixture confirms no source table/version change; CLI boundary tests pass; complete `control-plane/tests` is **44/44 PASS in 53.064s**. This is a source primitive only—not retention/ACL setup, Ubuntu deployment, restore, admission change, reconciliation, process crash or live drill proof.

**Delta P1a health-instance provenance, `2026-09-15T13:00+07:00`:** every local `ControlPlaneHttpServer` now generates one process-lifetime, content-free `service_instance_id=cp_<uuid>` and includes it in `/healthz` beside schema/admission/declared-source metadata. The regression proves format and stable identity across two health reads from the same process; complete `control-plane/tests` is **44/44 PASS in 49.871s**. The value correlates health samples only: it is not loaded-byte, configuration, service-owner, deployed-Ubuntu or restart proof. The currently observed Ubuntu endpoint does not yet expose it.

**Delta P1a/P3 snapshot artifact fingerprint, `2026-09-15T13:05+07:00`:** the verified snapshot receipt now reports the SHA-256 of the fully verified staged snapshot bytes before atomic rename. Store and CLI regressions recompute and match the digest; complete `control-plane/tests` is **44/44 PASS in 50.068s**. The digest binds an artifact without exposing its content, but it is not source-byte provenance, retention policy, a restore/reconciliation acceptance or deployed-Ubuntu proof.

**Current P0/Ubuntu recheck, `2026-09-15T13:06+07:00`:** development UI remains `CURRENT`, current-installation and Electron running/disk revision aligned, telemetry fresh. P0 remains closed because MCP running `72f8c7…` still differs from disk `cb7ff6…`, `mcp_update_pending=true`, `components_ready=false`, `fully_ready=false`, `runtime_update_incomplete=true`, and connector remains `CURRENT_COMPATIBLE_ACKNOWLEDGED` without rediscovery. Ubuntu `/healthz` still reports only service/SQLite `ok`, node=1 and binding/context/request/action/receipt=0, with no schema/admission/declared-source/service-instance evidence. No SSH, deployment, restart, policy, binding, action or canary was performed.

**Delta P1a/P3 immutable snapshot inspection, `2026-09-15T13:12+07:00`:** `python -m control_plane.maintenance inspect-snapshot` now opens only a completed snapshot as `mode=ro&immutable=1`, optionally binds it to the prior snapshot SHA-256, rejects WAL/SHM sidecars, and returns integrity/schema/admission plus delivery-state and unresolved-action counts for an operator's restore plan. Tests cover unknown/reconcile evidence, exact/malformed/mismatched digest and sidecar refusal; full `control-plane/tests` is **46/46 PASS in 52.278s**. This is read-only preflight only—not restore, admission change, node-effect reconciliation, source/deployment proof, retention/ACL configuration or a live drill.

**Delta P1b.1 actual node-agent subprocess crash, `2026-09-15T13:17+07:00`:** a real child process exits immediately after its durable `prepared` journal write and before bridge outcome/receipt. The subsequent invocation turns exactly that entry into `unknown`, submits the receipt before any poll and proves that no bridge reexecution occurs. Complete `control-plane/tests` is **47/47 PASS in 52.655s**. This is a local node-agent process fixture before any real Recovery IPC/MCP effect; it is not a bridge/effect crash, central ACK loss, network partition, Ubuntu process crash or restore drill.

**Delta P1a package-source fingerprint, `2026-09-15T13:28+07:00`:** every local HTTP server now computes one deterministic, content-free `package_source_sha256` at startup from the immediate `control_plane/*.py` package files, domain-separating file names and byte hashes. Health repeats that value for the process; focused fingerprint/health tests and `py_compile` PASS, and the complete `control-plane/tests` suite is **48/48 PASS in 51.275s**. This helps an operator compare a deployed process with a selected package artifact, but is not a signed artifact, loaded-extension, service-owner/configuration, Ubuntu deployment or canary attestation.

**Delta P1a expected package-fingerprint gate, `2026-09-15T13:34+07:00`:** an optional protected `CONTROL_PLANE_EXPECTED_PACKAGE_SOURCE_SHA256` now accepts only lowercase `sha256:<64-hex>` and is compared before the HTTP listener binds. A mismatch or malformed value refuses server start; health returns the expected value only after equality. README and the systemd example describe the setting. Focused validation + `py_compile` PASS; complete `control-plane/tests` is **49/49 PASS in 100.655s**. This turns an operator-selected expected fingerprint into a fail-closed package comparison, not a signed artifact, service-owner/configuration, deployment, effect or canary proof.

**Delta P1a offline package-fingerprint receipt, `2026-09-15T13:40+07:00`:** `python -m control_plane.maintenance package-fingerprint` now prints the exact content-free package fingerprint for a selected local checkout/package without instantiating the store, opening SQLite, reading runtime configuration, binding an HTTP listener or contacting a node. Its receipt is the safe input for E45 only when run from the exact selected deployment package. Focused validation + `py_compile` PASS; full `control-plane/tests` is **50/50 PASS in 99.124s**. It remains local preparation: not a remote artifact/service/unit attestation, deployment, policy, effect or canary proof.

**Current P0 recheck, `2026-09-15T13:43+07:00`:** development UI remains `CURRENT`, Electron running/disk revision aligned and runtime telemetry fresh. P0 remains closed: MCP running `72f8c7…` differs from disk `cb7ff6…`, `mcp_update_pending=true`, `components_ready=false`, `fully_ready=false`, `runtime_update_incomplete=true`, and the connector is still compatible bootstrap without rediscovery. No observer, bridge, policy, binding, action, restart, deployment or mutation was performed.

**Delta P3 recovery runbook, `2026-09-15T13:47+07:00`:** new [Control Plane Recovery and Restore Runbook](CONTROL_PLANE_RECOVERY_RUNBOOK.md) gives the operator an authority-bounded path from preflight through isolated drill, production restore/reconciliation, retention/ACL evidence, T13/T14 criteria, abort and redacted reporting. It binds E38/E40/E42/E44–E46 without treating any primitive as a restore result. This is documentation only: no retention setup, snapshot, systemd operation, restore, reconciliation, node observation, T13/T14 drill, P0 closure or canary occurred.

**Delta P3/T14 durable-write failure, `2026-09-15T13:53+07:00`:** a SQLite wrapper now injects failure exactly at the fixed central read-only intent's `COMMIT` after writes, performs an actual rollback, and proves no intent/action/event survives or can dispatch. The HTTP surface now maps `sqlite3.Error` to content-free `503 DURABLE_STORAGE_UNAVAILABLE`, never a false successful response. Focused proofs + `py_compile` PASS; full `control-plane/tests` is **52/52 PASS in 56.241s**. This is a deterministic source fixture, not an Ubuntu full-disk/DB-busy fault, real fixed-intent HTTP commit failure, retention/ACL proof, node effect, restore drill or canary.

**Delta P3/T13 recovery-locked restore candidate, `2026-09-15T14:01+07:00`:** `python -m control_plane.maintenance prepare-recovery-restore` now inspects a completed, exact-hash, schema-v6 snapshot and creates only a new, non-overwriting SQLite candidate. The candidate persists `admission_mode=recovery` and a content-free source-artifact event, so an older `open` snapshot cannot silently make its queued work pollable when prepared for a separately authorized drill. The regression proves source/candidate hash binding, destination non-overwrite and zero action delivery from the candidate; focused 3/3 + `py_compile` PASS and complete `control-plane/tests` is **53/53 PASS in 66.296s**. It does not replace a live DB, change a running service/admission, contact or reconcile a node, configure retention/ACL, perform a drill, or prove a restore/canary.

**Current P0 recheck, `2026-09-15T14:01+07:00`:** development UI remains `CURRENT`; Electron running/disk revision is `c5a057…` on both sides and the runtime snapshot is fresh. P0 stays closed: MCP running `72f8c7…` differs from disk `cb7ff6…`, `mcp_update_pending=true`, `components_ready=false`, `fully_ready=false`, `runtime_update_incomplete=true`, and connector remains `CURRENT_COMPATIBLE_ACKNOWLEDGED` with `compatible_activation_bootstrap`, without rediscovery. No observer, bridge, policy, binding, action, restart, deployment or mutation was performed.

**Delta P1b.1 timeout/no-retry regression, `2026-09-15T14:10+07:00`:** after the durable `prepared` journal marker, a simulated `subprocess.TimeoutExpired` now has an explicit node-lane regression: it persists and submits exactly one content-free `unknown` receipt. A fixture that redelivers the same sealed action proves the existing journal entry prevents a second bridge subprocess invocation. Focused proof + `py_compile` PASS; complete `control-plane/tests` is **54/54 PASS in 66.802s**. This is a local Python timeout fixture—not an actual Recovery IPC/MCP crash, central ACK/network failure, node effect, installed policy, Ubuntu deployment, canary or outcome proof.

**Delta P3/T14 fixed-intent HTTP commit-failure regression, `2026-09-15T14:15+07:00`:** a loopback `POST /mcp` drives the authenticated fixed `workspace_context(request_read_only)` façade through a real SQLite wrapper that rolls back at `COMMIT`. The HTTP response is exactly content-free `503 DURABLE_STORAGE_UNAVAILABLE`; the test verifies no `mcp_read_only_intent`, work request, action or event remains. Focused proof + `py_compile` PASS; complete `control-plane/tests` is **55/55 PASS in 69.755s**. This remains a local HTTP/SQLite fixture—not a physical disk/DB-busy fault, Ubuntu service proof, node call/effect, network/ACK boundary, retention/ACL proof, restore drill or canary.

**Delta P1/T01 same-workspace target isolation, `2026-09-15T14:21+07:00`:** two ready Store nodes can now be exercised with the same logical workspace ID and generation but distinct bindings, contexts, requests and actions. Each device poll receives exactly its own action, and the delivery record retains its distinct device/binding/context scope. Focused proof + `py_compile` PASS; complete `control-plane/tests` is **56/56 PASS in 69.372s**. This is Store isolation only—not a real shared Windows path, client selection/discovery, local admission, bridge call, receipt, wrong-path canary or remote effect proof.

**Current P0/Ubuntu recheck, `2026-09-15T14:23+07:00`:** Windows development UI remains `CURRENT`, Electron running/disk revision remains `c5a057…`, and runtime telemetry is fresh. P0 is still closed: MCP running `72f8c7…` differs from disk `cb7ff6…`, `mcp_update_pending=true`, `components_ready=false`, `fully_ready=false`, `runtime_update_incomplete=true`, and connector remains compatible bootstrap without rediscovery. Unauthenticated Ubuntu `GET /healthz` returned HTTP 200, service/SQLite `ok`, nodes=1, enrollment_requests=1 and bindings/contexts/work_requests/actions/receipts=0—but still no schema, admission, service-instance or package-source fingerprint. No SSH, systemd operation, deployment, restart, policy, binding, action or canary occurred.

**Delta P0 exact-deployment health verifier, `2026-09-15T14:30–14:41+07:00`:** new `control_plane.deployment_verifier` accepts only an explicit credential-free absolute HTTP(S) `/healthz` URL and makes exactly one GET; redirects are refused rather than followed. It requires current schema v6, expected durable admission, service/SQLite `ok`, a valid process instance ID, and both the running and startup-gated package fingerprints to exactly equal an operator-supplied selected-package fingerprint. Missing/null fields return typed `CONTROL_PLANE_DEPLOYMENT_HEALTH_INCOMPLETE`; contradicting values return `..._MISMATCH`; redirects/unavailable health return `..._UNAVAILABLE`; no endpoint, body, exception text or credentials are printed. `py_compile` plus the affected HTTP/fingerprint and verifier surface are **16/16 PASS (21.969s)**, including a redirect refusal regression. The full discovery run was unobserved/incomplete after tool interruption, so the previous E54 56/56 is retained only as the prior full-suite result. Both read-only Ubuntu verifications (the final one uses the redirect-refusing source) against the current selected local package and expected `open` returned `...HEALTH_INCOMPLETE` (exit 2), so no exact deployed-package receipt exists. This does not inspect/change remote service ownership, checkout, configuration, TLS, admission authorization, process state or node execution.

**Delta P1/T15 façade-contract pin, `2026-09-15T15:04+07:00`:** source local now requires `request_read_only` to carry the exact `{schema_version,profile,sha256}` metadata advertised by `initialize`/`tools/list`. Schema v7 persists that immutable triple with the central intent and emits it only with the sealed node action; node agent rejects absent/invalid legacy fields before the bridge. Local policy schema v2 pins the identical triple (v1 is rejected, not upgraded), Runtime Orchestrator includes it in its local handle/receipt, Recovery Host rejects an in-flight result whose triple changes, and the descriptor-hiding CJS wrapper/Python allowlists preserve it without exposing MCP data or credentials. A façade mismatch yields `CONTRACT_MISMATCH` before durable intake; policy/result mismatches are pre-effect typed failures. A v6 migration regression proves the added pin defaults are deliberately empty/fail-closed rather than inferred. Current-source proof: `py_compile` PASS; `tests.test_store` **45/45 PASS (156.297s)**; HTTP API + deployment-verifier **16/16 PASS (19.260s)**; CJS bridge/orchestrator/policy tests **8/8 PASS**; focused Recovery Host contract-drift test PASS. No policy was installed, no action/binding was created, and no Recovery IPC/MCP/Ubuntu request, restart, deployment or canary occurred. This closes only the local T15 source handshake, not a deployed or live capability-drift proof.

**Current P0/Ubuntu read-only recheck, `2026-09-15T15:15+07:00`:** development UI remains `CURRENT`, the Electron UI running/disk revision is still `c5a057…`, and runtime telemetry is fresh. P0 remains closed: MCP running `72f8c7…` still differs from disk `cb7ff6…`, `mcp_update_pending=true`, `components_ready=false`, `fully_ready=false`, `runtime_update_incomplete=true`, and the connector remains `CURRENT_COMPATIBLE_ACKNOWLEDGED` / `compatible_activation_bootstrap` without rediscovery. An offline current-package fingerprint followed by one credential-free Ubuntu `/healthz` verifier GET again returned only `CONTROL_PLANE_DEPLOYMENT_HEALTH_INCOMPLETE` (exit 2). It neither identifies nor changes the remote checkout/service nor opens an admission/canary authority. No restart, refresh, SSH, deployment, policy, binding, action or canary occurred.

**Delta P1c discovery-surface regression, `2026-09-15T15:19+07:00`:** `server/discover` is now explicitly covered as the compact MCP client entrypoint: the authenticated response preserves the same protocol version, server identity and façade contract metadata as `initialize`, and yields exactly the same eight public tools with closed input schemas as `tools/list`. Current HTTP API + deployment-verifier proof is **16/16 PASS (17.428s)**. This validates central discovery presentation only; it is not client negotiation, local capability acceptance, relay, workspace access, policy provisioning, canary or deployment evidence.

| Lớp | Kết quả kiểm tra mới | Giới hạn |
| --- | --- | --- |
| Source baseline | Baseline `control-plane/**`, systemd template và tài liệu trước delta P1a được track ở commit local `a0f3a6f`; delta P1a/CI hiện là local worktree | Không chứng minh remote Git/deployed bytes đang giống local |
| P1a.1/P1a.2/P1a.3/P1a.4/P1a.5 + P1b.0/P1b.1 + P1c.0/P1c.1/P1c.2/P1c.3 + T15 source local | Versioned schema v2→v7, atomic migration rollback, explicit verified Backup API snapshot, no-init/no-migrate local snapshot CLI and immutable no-restore inspection, durable recovery admission lock/reopen, freshness/identity/binding/context/request/expiry gate, exact attempt + receipt replay/reconcile, credential-free owner-scoped node/context/request/action lineage observation, stricter readiness, credential rotation/revoke/cancel never-sent boundary; revoke node blocks fresh context/request admission; health has schema/admission/declared-source, process-lifetime instance and package-source fingerprint projection, optionally fail-closed against an operator-selected expected fingerprint before listen; an offline CLI derives the fingerprint from the selected source package without opening the DB; a separate GET-only verifier requires actual and startup-gated fingerprints plus schema/admission/health fields before issuing a content-free comparison receipt; the P3 runbook defines an isolated drill/restore/reconcile/reopen procedure; P1b.0 descriptor-bound read-only recovery observation keeps MCP process/server identity separate; P1b.1 adds a policy-gated, exact fixed local read lane with a no-retry prepared journal, typed receipt-transport replay and timeout→unknown duplicate no-retry regression; P1c.0 declares the exact eight public tool names, P1c.1 adds redacted central action lifecycle status, P1c.2 adds atomic fixed central read-only intent/action, P1c.3 reserves the bridge shape to canonical intent provenance plus truthful central lifecycle projection, and T15 pins the advertised façade contract through central intent, node action, policy and safe receipt | Uncommitted/un-deployed; verifier reads one health response only and is not a signature/service-owner/configuration/checkout/TLS/write-admission attestation; runbook/snapshot/inspection CLIs are not retention/ACL/restore or a drill; instance ID is not byte/service-owner attestation; lock is not a restore drill or node fence; declared source is not byte attestation; P1b.1 policy is not provisioned and P1c.3/T15 only queue and guard central intent; none proves local workspace access, remote effect, scheduler or live canary |
| Focused proof / CI config local | Baseline assessment 8/8 PASS; P1a latest complete suite was 30/30 PASS, 27.620s, warnings-as-errors + `py_compile`; E25 changed-boundary proof: CJS observer 3/3, Recovery Host 36/36 (10.526s), Python migration/server-identity/projection/observer-parser/HTTP proofs 5/5 PASS. E30: policy 3/3, Orchestrator 2/2, CJS wrapper 3/3, Recovery Host 37/37, Node journal 2/2. E54 is the prior complete Python suite 56/56 (69.372s), including fixed intent/replay/recovery, no-dequeue ordinary poll, provenance reservation, pre-effect rejection, façade lifecycle/redaction, typed receipt-transport replay, timeout→unknown duplicate no-retry, same-workspace two-node target isolation, no-init snapshot CLI, health instance/package fingerprint, expected-fingerprint startup refusal and offline source-only fingerprint receipt, snapshot artifact digest, immutable snapshot inspection, child-process crash recovery, durable commit-failure rollback/typed HTTP error, fixed-intent HTTP 503 rollback, and a non-overwriting recovery-locked restore candidate. E56 affected HTTP/fingerprint + deployment-verifier surface is **16/16 PASS (21.969s)** plus `py_compile`, including redirect refusal; full discovery after E56 is unobserved/incomplete, not a PASS claim. Final tracked `git diff --check` and focused untracked-file whitespace checks PASS. CI Linux+Windows now run Python suite plus CJS observer | GitHub/Ubuntu exact-delivery run not observed; no real Recovery IPC/MCP effect crash, network partition, full-disk/DB-busy fault or restore proof |
| Ubuntu endpoint | GET health lúc `2026-09-15T14:23+07:00`: HTTP 200, service/SQLite `ok`, nodes=1, enrollment_requests=1, bindings/contexts/work_requests/actions/receipts=0. Lúc 14:31, GET-only exact-deployment verifier với selected local fingerprint/`open` trả `CONTROL_PLANE_DEPLOYMENT_HEALTH_INCOMPLETE` (exit 2); response vẫn thiếu P1a.4 `admission_mode`, schema, declared source, service instance, package-source fingerprint hoặc P1c intent count | Không SSH/systemd recheck; verifier không thể accept exact deployed package từ health cũ và không cung cấp remote source/instance binding, DB write-admission proof hay cause of absence |
| Central execution evidence | Health báo bindings=0, contexts=0, work_requests=0, actions=0, receipts=0 | Chưa có central read-only hoặc mutation canary |
| Windows từ checkout này — current P0 | `node scripts/dev-ui-lifecycle.js status` lúc 14:23: `state=CURRENT`, `installation=current`, dev Electron running/disk revision đều `c5a057…`, UI `update_pending=false`, telemetry fresh; nhưng MCP running `72f8…` khác disk `cb7…`, `mcp_update_pending=true`, `components_ready=false`, `fully_ready=false`, `runtime_update_incomplete=true`, connector `CURRENT_COMPATIBLE_ACKNOWLEDGED`, `connector_rediscovered=false` | Electron UI alignment is current but MCP/runtime admission still is not; no strict discovery/local admission, live identity observation hay safe canary authority |
| Earlier mismatch evidence | Đọc field an toàn lúc 09:13 +07:00: descriptor có `runtime_mode=packaged`, trong khi dev status thời điểm đó yêu cầu `development` | Không phải proof packaged runtime hỏng; không suy current `installation=current` là concurrent handoff accepted |
| Adapter/facade | Source thêm REST owner observation, descriptor-bound identity observer, P1b.1 policy-gated local `workspace_context` lane và P1c.0–P1c.3 central status/lifecycle plus one provenance-bound durable intent. Ordinary node `poll` is local-only `POLL_EXECUTION_DISABLED` and cannot dequeue; P1b.1 command is named separately | P1b.1 is source-only without installed policy/strict runtime/live result; P1c.3 does not call or relay to a node; no panel/watchdog/ChatWeb identity or raw stdio is reused |

Census canonical local ledger qua snapshot read-only: SQLite integrity `ok`, FK errors=0; 9 ordinary active run records (8 stale candidates, 1 awaiting acceptance), 6 P5 anchors; 1 stale managed-job residue; unexplained active runs=0, projection drift=false; `mutated_canonical_ledger=false`. Đây không phải chín process đang chạy, không cho phép tự accept/cleanup. Chi tiết timestamp/hash/projections nằm trong kế hoạch mới.

**Kết luận hiện hành:** backend có foundation, P1a.1–P1a.5, P1b.0/P1b.1, P1c.0–P1c.3 và T15 local source/proof cùng CI coverage config; E38 makes an existing-source verified snapshot operationally reproducible without initiating/migrating the DB, E39 makes same-process health samples correlatable, E40 binds the snapshot artifact to an exact digest, E42 supplies immutable reconciliation preflight, E43 proves pre-bridge node-agent process-crash recovery, E44 adds a package-source fingerprint to compare a running server with a selected artifact, E45 can make that comparison fail closed before the server listens, E46 produces the expected fingerprint offline from a selected package, E48 supplies the P3 operator runbook, E49 proves rollback/no-false-success under a deterministic central commit failure, E50 prepares a separate recovery-locked candidate so a prior `open` snapshot cannot silently re-open delivery, E52 proves a timeout cannot cause local duplicate reexecution, E53 proves the fixed HTTP intent returns no false success or partial durable record, E54 proves two bindings using the same logical workspace do not cross-device poll, E56 turns exact artifact/schema/admission health comparison into a reusable fail-closed receipt, and E58 makes contract drift fail closed through the central intent, local policy and safe receipt. E59 reconfirms the exact current Windows P0 and Ubuntu deployed-package gates remain closed. P1b.1 has source actor/policy/journal and E37/E43/E52 prove local recovery cannot reexecute that read-only lane; legacy `poll` no longer dequeues, nhưng policy chưa provisioned và không có live call. P1c.3/T15 chỉ create and guard a canonical central intent; chúng không relay. P1 end-to-end chưa đạt, remote mutation tiếp tục đóng. Cần delivery/review theo quyền phù hợp, owner lifecycle xử lý MCP P0, provision/review policy v2 trên target, chọn client/target và thực hiện one explicit read-only canary sau các gate.

## Snapshot triển khai trước trong ngày 15-09-2026 — không phải toàn bộ đã kiểm tra lại

Các quan sát dưới đây được giữ làm lịch sử của pilot trước; các trường khác với bảng kiểm tra mới không được dùng như trạng thái hiện tại của checkout này.

| Lớp | Trạng thái | Bằng chứng mạnh nhất |
| --- | --- | --- |
| Ubuntu control plane | Đang chạy | User service `codex-control-plane.service` active/enabled tại `/home/svhome/DEV/Codex-web`; SQLite `integrity_check=ok`. |
| Khả dụng qua đăng xuất Ubuntu | Đã cấu hình | `loginctl show-user svhome -p Linger` trả `Linger=yes`; đây chưa thay thế bài reboot acceptance. |
| Ingress mạng | Chỉ Tailnet/private | Dịch vụ bind IP Tailnet của Ubuntu trên cổng 8765; truy cập từ PC Windows tới `/healthz` đã thành công. Không công bố Internet. |
| Server identity/operator auth | Đã triển khai | Operator token chỉ ở file mode 600 ngoài repository. Endpoint operator dùng Bearer; endpoint node dùng node secret hash-verified. Không ghi payload hoặc Authorization vào log HTTP. |
| Node enrollment | Đã kiểm chứng | PC Windows tạo secret cục bộ, gửi hash để chờ duyệt; Ubuntu duyệt request; heartbeat node sau đó được xác thực với readiness `unknown`. Secret không đi qua operator response hay Git. |
| Runtime Windows | Degraded, không ready | One-shot adapter đã publish trạng thái hiện hành: Electron/MCP/tunnel và revision khớp, nhưng activation epoch vẫn `VERIFYING`, admission đóng vì chưa có current-process connector discovery. |
| Remote execution | Chưa mở, theo chủ đích | Chưa tạo workspace binding/context/work request/action. Server không gọi shell, không thay local MCP writer và không tự failover sang server. |

## Thành phần source mới

`control-plane/` là control plane Python chuẩn thư viện, SQLite-backed:

- Registry node, enrollment hai bước, binding/context/request/action/receipt/event bền vững.
- Chỉ cho phép đúng tám tool public của `smart-v3`.
- Action gắn target/binding/context/workspace generation/tool/arguments/idempotency/admission/expiry bằng digest bất biến.
- P1a.1 local chỉ handoff queued action khi revalidation pass, ghi `dispatch_unconfirmed` + exact attempt trước response, và không redeliver state đó. P1a.2 thêm revoke/cancel/rotation nhưng chỉ settle queued never-sent action. P1a.3 thêm atomic migration, verified Backup API snapshot, no-init/no-migrate snapshot CLI và two-thread central race regression. P1a.4 thêm durable recovery admission lock/reopen. P1a.5 thêm credential-free, owner-scoped inventory/lineage observation; subprocess proof cho thấy central exit trước commit rollback hoàn toàn, còn exit sau commit giữ exact attempt để reconcile; admission transaction cũng chặn context/request mới dưới node revoked. P1b.0 thêm read-only, descriptor-bound observation of exact MCP process/server/epoch/contract SHA; node chỉ publish nó sau strict aggregate status và schema v5 dispatch kiểm tra cả hai ID. P1b.1 thêm actor riêng, policy default-off/hết hạn, exact read-only action/journal, typed unknown reconciliation và typed receipt-transport replay không re-call bridge, nhưng not a live policy/effect proof. Health có schema/admission/deployment metadata nhưng không byte attestation. Không phần nào mở mutation/fence hoặc thay node-side effect reconciliation cho broader actions.
- `node_agent.py` enrol/heartbeat/runtime-heartbeat và ordinary `poll` không thực thi **hoặc dequeue** action. Chỉ `poll-read-only-once` explicit có P1b.1 source lane; nó còn cần strict runtime + local policy + central action thật.

Template systemd tại `deploy/codex-control-plane.service.example`; config thật và SQLite runtime nằm ngoài Git dưới home của tài khoản Ubuntu.

## Proof ghi nhận trong snapshot triển khai trước

- Local: 8 test pass, bao gồm negative operator authorization, two-step enrollment và runtime-heartbeat fail-closed. Khi chạy từ repo root phải đặt `PYTHONPATH=control-plane` như README; command đầy đủ được kiểm lại ở bảng hiện hành.
- Ubuntu: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=control-plane python3 -W error -B -m unittest discover -s control-plane/tests -v` — 8/8 tests pass; health endpoint trả SQLite `ok`.
- Local: `git diff --check` pass.
- Windows: `npm run dev:refresh` khởi động MCP và tunnel với revision hiện tại; `npm run dev:status` xác nhận runtime telemetry hiện diện nhưng `fully_ready=false`.

## Chặn connector trong snapshot trước — không thay thế current contract

Control plane không được phép coi node ready chỉ vì tiến trình đang chạy. Execution Hub từ chối mở admission vì connector contract chỉ ở `UNCHANGED_ACKNOWLEDGED`, thiếu receipt `tools/list` gắn với process/activation epoch hiện tại. Lệnh acknowledgement chính thức trả `CONNECTOR_CONTRACT_NOT_REDISCOVERED`.

Trình tự được đề xuất trong snapshot trước (đã được bổ sung/supersede bởi P0–P1 trong kế hoạch mới):

1. Kết nối/reconnect ChatGPT/Coding Tools MCP với Execution Hub Windows mới khởi động để có một `tools/list` current-process discovery.
2. Chạy lại full-clean/refresh theo lifecycle hiện hữu và xác nhận `fully_ready=true`, admission mở, connector freshness là current-process discovery.
3. Lấy workspace identity và generation từ runtime live, rồi mới tạo binding ở Ubuntu. Không tính SHA suy đoán hay trạng thái cache làm binding proof.
4. Chỉ sau đó chạy một action read-only `workspace_context`; đối chiếu receipt với đúng action và device. Mutation vẫn phải giữ authority, permission và acceptance cục bộ.

Đính chính phạm vi hiện hành: local contract còn có đường attested compatible no-workspace bootstrap khi đủ điều kiện exact/compatible SHA; `CURRENT_COMPATIBLE_ACKNOWLEDGED` không phải strict rediscovery. Không yêu cầu hoặc giả lập `tools/list` một cách máy móc, không gọi refresh để thay receipt. Trước mọi recovery cần giải quyết installation mismatch; trước central canary cần implement/test facade và actor/admission adapter. Xem [CURRENT_STATE](CURRENT_STATE.md) và kế hoạch mới, P0–P1.

## Quyết định kiến trúc đã chốt

- Ubuntu là durable registry/queue/audit plane; Windows Execution Hub + Coding Tools MCP vẫn là execution writer và proof authority.
- Không thay tunnel hiện hữu chỉ bằng việc đổi địa chỉ server. Central link là capability phụ, không phải bypass readiness/connector/permission.
- Không auto-route model. `execution_route=auto` vẫn fail-closed deterministic.
- Không khởi động service Windows “khi chưa đăng nhập” trong pilot này. Electron, user secrets và interactive connector hiện session-bound. Nếu yêu cầu availability sau logoff/reboot Windows, phải có một workstream riêng: identity/secret store phi tương tác, Windows Service hoặc scheduled task được thiết kế lại, user-consent/TLS/rollback và reboot proof. Không được dùng auto-login như biện pháp mặc định.

## Rủi ro và việc còn lại

- Ingress hiện được bảo vệ bởi Tailnet + auth, chưa có TLS/mTLS layer ứng dụng hoặc public reverse proxy. Giữ private cho đến khi có mô hình chứng chỉ/rotation/revocation và test negative tương ứng.
- Có one-shot Windows runtime-heartbeat adapter đọc `dev-ui-lifecycle.js status`; P1a.1 sửa predicate để `MISSING` thắng cờ ready mâu thuẫn. P1b.0 source có descriptor-bound process/server/epoch/contract provenance chỉ sau strict aggregate status; P1b.1 source giờ có one fixed local read lane with a separate actor/policy/journal, and legacy `poll` cannot consume central work, but P0 hiện không strict, policy is absent by default và chưa có live observer/bridge result. P1c.2 chỉ creates a fixed central queue record, không phải scheduler/background service hoặc façade relay. Heartbeat sau logon và runtime headless là hai capability khác nhau.
- Snapshot pilot trước ghi nhận `startWithWindows=false`, `autoStartServices=false`; lượt này không đọc lại các config values đó. Nếu bật `startWithWindows`, đường supervisor hiện hữu là **sau khi người dùng đăng nhập Windows**, không phải proof service chạy trước login.
- Chưa có proof reboot Ubuntu, offline/reconnect, external process/network crash trên local bridge, retention/ACL, restore drill, wrong-device binding qua bridge hoặc natural multi-step Goal. P1a.5 có subprocess exit sau central dispatch commit; P1b.1 has E43 node-agent pre-bridge crash plus prepared→unknown proof, E52 timeout no-retry proof and E37 simulated receipt transport replay; E38/E40 have snapshot/digest, E39 has health correlation, E42 has restore preflight, E44–E46 have package comparison/optional startup refusal/offline expected-value generation, E48 has an operator procedure, E49/E53 have local commit-failure rollback, E50 has a recovery-locked candidate, and E54 has central same-workspace target isolation, nhưng chưa chứng minh Recovery IPC/MCP effect crash, network, deployed process ownership, full-disk/DB-busy, retention/ACL or restore trên runtime thật.
- Snapshot pilot trước ghi nhận working tree Ubuntu có thay đổi của người dùng; lượt assessment này không SSH/pull/reset/commit và không xác minh lại dirty state đó. Baseline control-plane/deploy nằm ở commit local `a0f3a6f`, nhưng P1a.1–P1a.5, P1b.0/P1b.1, P1c.0/P1c.1/P1c.2/P1c.3 và CI hiện còn uncommitted; trạng thái push/loaded build Ubuntu chưa được kiểm chứng.

## Next action chính xác

Review/commit P1a.5 + P1b.0/P1b.1 + P1c.0/P1c.1/P1c.2/P1c.3 + E38–E56 qua delivery guard chỉ khi người dùng giao commit; P0 hiện yêu cầu owner lifecycle giải quyết `mcp_update_pending`/`runtime_update_incomplete`, running/disk revision drift và lấy strict runtime discovery trên đúng development installation, không suy `CURRENT_COMPATIBLE_ACKNOWLEDGED` là admission. Ubuntu first needs an authorized deployment/service-owner packet and a new exact package with `CONTROL_PLANE_EXPECTED_PACKAGE_SOURCE_SHA256`; only then may the GET-only verifier be rerun and its pass be combined with separate systemd/checkout evidence. Chỉ khi P0 Windows strict mới chạy observer read-only để record exact live identity, nhưng vẫn phải provision/review local policy for P1b.1 và xác nhận target/client canary trước binding. P1c.2 is a fixed durable intake only; after capability/target proof, the first execution remains one explicit `poll-read-only-once` canary, not a scheduler; legacy `poll` cannot consume that action. E37/E43/E49/E52/E53/E54 limit receipt loss, node-agent pre-bridge crash, timeout retry and central durable-write/target-isolation behavior; E38/E40 supply snapshot primitive and digest; E39 supplies health correlation; E42 supplies restore preflight; E44/E45/E46/E56 supply package-artifact comparison, optional fail-closed startup, offline expected-value generation and exact read-only health receipt; E48 supplies the restore/reconciliation procedure and E50 supplies a recovery-locked candidate, but neither is an external restore. E57 confirms the deployed endpoint cannot yet produce the required package/admission provenance. Wave source/operations còn lại vẫn là real Recovery IPC/MCP/network crash + full-disk/DB-busy and restore drill/retention; CI focused coverage source đã có nhưng chưa được GitHub Actions chạy. Nếu client không expose connector hợp lệ thì `WAITING_FOR_SUPPORTED_CONNECTOR`, không raw-protocol bypass. Chưa bật scheduler/execution poll chung, chưa remote mutation, chưa restart/deploy. Chi tiết thứ tự và exit gates: [kế hoạch hoàn thiện](UBUNTU_24X7_COMPLETION_PLAN.md).

## Windows Tailscale candidate evidence — 2026-09-21

`DESKTOP-63643J4` (`100.72.186.41`) accepted SSH testing in the isolated
candidate `E:\DEV\Codex-web-candidate-502ffb8`. Shared-account routing is now
focused-proven on Windows: three OAuth binding tests and one two-client
exec-to-same-bound-node E2E pass. The broader HTTP→node E2E group is 22/22
pass and Recovery process E2E is 3/3 pass. This is source/unpacked evidence;
it does not promote the Ubuntu service, a Windows package, or a live runtime.

The initial full Windows MCP run was 1,158 pass with two platform-fixture
failures; after the fixture portability fixes, the candidate rerun is
**1.160/1.160 PASS in 31m45s**. OAuth configuration still has four
NTFS/POSIX-mode fixture assertions; keep those separate and do not turn them
into a false green by weakening credential or execution policy.

The same candidate then passed `dist:dir`, packaged recovery smoke, direct NSIS
installer build `1.0.7`, and installed install/smoke/uninstall. Packaged smoke
verified the smart-v3 contract, 17 required resources, Recovery Host/MCP
readiness, device identity, and fail-closed owner/hash checks; installed smoke
verified registry cleanup and unchanged production supervisor/descriptor. This
is candidate package proof only, not a live Windows or Ubuntu deployment proof.

A subsequent Windows probe found inherited broad ACLs on node config/policy
files. `node_agent.py` now hardens all atomic local JSON writes before rename
with current-user/SYSTEM/Administrators SID allowlisting and fails closed on
ACL command failure. Real source and packaged Python probes show DPAPI envelope
round-trip, no plaintext, and the exact three-principal ACL. Node secret,
rotation and workspace focused tests are **18/18 PASS** on Windows; HTTP→node
E2E after the fix is **22/22 PASS** (one known socket-teardown warning).
