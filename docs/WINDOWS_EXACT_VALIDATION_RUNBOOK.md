# Windows exact validation runbook

Runbook này dành cho owner hoặc Windows runner đã được ủy quyền để đóng gate
`PACKAGED_PROOF`/`LIVE_ACCEPTED` của Execution Hub + Coding Tools MCP. Nó không
tự cấp credential, không tự deploy và không thay thế owner acceptance.

### Cửa sổ test hiện tại — 21-09-2026, 21:42 +07

Wave 43 đã đưa commit tài liệu/evidence `fa055951d912997d75c9de5d7d18ee42f72b3094`
vào exact checkout Windows `E:\DEV\Codex-web`; worktree sạch. Vì commit này
không đổi package-relevant source, artifact `1.0.7` từ build `bb4522c` vẫn là
candidate hiện hành với SHA-256
`61fb7fa5785c3861fcd4c8371f54172894472c9a0b7d48854c5cb05126d7c14e`.
Read-only recheck: `dev:status` là `MISSING/RECOVERY_DESCRIPTOR_STALE`,
`full-clean-activation --preflight` cũng trả `RECOVERY_DESCRIPTOR_STALE`.
Không chạy `--execute`, không forge closure/epoch. Owner vẫn phải mở app từ
desktop interactive và tạo closure năm trường cho đúng HEAD trước activation.

Wave 44 đồng bộ tiếp delivery receipt `dcb3fc492b22d1b04547f3eae1c595b4ee6e4ce0`;
đây là evidence-only delta, không cần rebuild package. Exact checkout hiện tại
đã được kiểm tra lại ở HEAD này, worktree sạch.

Wave 45 đã thử refresh từ phiên `Admin` tương tác. Recovery Host bootstrap và
refresh epoch bắt đầu được, nhưng runtime dừng với `ACTIVATION_EPOCH_FAILED`
do chưa có Runtime API Key trong profile local. Task/PID/script/log tạm đã dọn;
không chạy `--execute` của full-clean activation và không forge closure. Owner
cần lưu key cục bộ qua UI nếu chọn local executor, hoặc hoàn tất central pairing
trước khi thử refresh/preflight lại.

Exact checkout hiện tại là `E:\DEV\Codex-web` ở `dcb3fc492b22d1b04547f3eae1c595b4ee6e4ce0`;
runtime package lineage đã build là `bb4522cdc5f011942cce89f98c415df930f3f359`.
Windows worktree sạch, không còn
candidate path/branch rác; đọc lại `git rev-parse HEAD` ngay trước activation.
`npm ci` và `npm run dist` đã chạy trên checkout
exact: Node/Electron **922/922 PASS**, MCP **1160/1160 PASS**, source-root/secret
gates PASS. Installer `1.0.7` SHA-256 là
`61fb7fa5785c3861fcd4c8371f54172894472c9a0b7d48854c5cb05126d7c14e`.

Packaged và installed smoke đều pass; installed smoke đã uninstall và cleanup
profile/process. Vì vậy bằng chứng hiện tại là exact candidate
`PACKAGED_PROOF`, chưa `LIVE_ACCEPTED`: `dev-ui status` hiện
`MISSING/ENOENT` và full-clean preflight cũng trả `ENOENT`. Không tự
forge acceptance, credential/context, admission, binding/task hoặc deploy.

Wave 40 đã cài installer exact `1.0.7` per-user tại
`C:\Users\Admin\AppData\Local\Programs\Coding Tools MCP`; registry và
executable installed hash khớp unpacked artifact. Launch qua SSH (có và không
có TTY) không tạo GUI/Recovery Host process, không tạo Supervisor Task và
không tạo `recovery-host.json`. Vì vậy bước tiếp theo phải chạy từ desktop
interactive của `Admin`; SSH chỉ dùng để kiểm tra, không được xem là GUI
acceptance.

Wave 41 recheck cho thấy UI packaged/Recovery Host/MCP đã từng chạy đúng
installation và owner identity khớp, nhưng strict snapshot vẫn chưa có
workspace, MCP execution, central authority hoặc connector ACK. Một activation
owner attempt đã dừng ở `STOPPING` với admission đóng, không có replacement
process; descriptor stale và Supervisor task không tồn tại. Không được gọi đây
là activation thành công hoặc `LIVE_ACCEPTED`.

Task cũ `CodingTools-StageA-Deferred-Worker` (09-03) trỏ tới file tạm đã mất
đã được gỡ đúng mục tiêu. Không xoá `%APPDATA%\\web-mcp-assistant`, credential,
workspace hay activation evidence. Khi owner mở lại UI, phải đọc `HEAD` hiện
tại và tạo closure năm trường mới trước `--preflight`/`--execute`.

### Wave 42 — exact rebuild/install proof — 21-09-2026, 21:25 +07

Từ `main@bb4522cdc5f011942cce89f98c415df930f3f359`, `npm run dist` đã pass
Node/Electron **922/922** và MCP **1160/1160**; `verify-packaged-resources`
pass. Installer `1.0.7` SHA-256:
`61fb7fa5785c3861fcd4c8371f54172894472c9a0b7d48854c5cb05126d7c14e`.
Executable installed khớp unpacked artifact:
`a57ced0d185472d5c5e234a1177bf13ca35f14d2661300fc80e92c6daa7ecbd2`.
`packaged-recovery-smoke.js` trả `ok=true` với 17 resources, 8 tools,
Recovery/MCP/Supervisor healthy và production descriptor/task stable.

Artifact mới chỉ chứng minh packaged/installed boundary. App production vẫn
chưa mở lại sau epoch `STOPPING/CLOSED`; do đó chưa chạy `--preflight` hoặc
`--execute`, chưa tạo workspace/binding/task và chưa nâng `LIVE_ACCEPTED`.

`DESKTOP-63643J4` (`100.72.186.41`) hiện reachable qua Tailscale/SSH. Exact
checkout `E:\DEV\Codex-web` là nguồn Git dùng cho build/receipt; không dùng
candidate directory đã retire. Focused recheck lịch sử vẫn giữ: **18/18**
secret/rotation/workspace, **3/3** same-account OAuth, **1/1** two-client exec,
**1/1** document-write, **1/1** standing patch.
Focused structured workflow parity cũng đạt **1/1** `git/build/test/deploy` và
**1/1** journal/terminal receipt; đây là fixture deterministic, không phải
toolchain/deploy thật. Các lane này không dùng credential thật và chưa thay cho
owner acceptance.

Packaged/installed smoke recheck hiện hành cũng pass: 17 resources, 8 smart-v3
tools, Recovery/MCP/Supervisor healthy, fail-closed owner/hash, install/register/
uninstall cleanup và production descriptor/Scheduled Task stable. Đây vẫn là
candidate package proof; các bước reboot/reconnect/live account bên dưới chưa
được tự động coi là đạt.

Ubuntu `/healthz` hiện chỉ đọc là `ok=true`, schema 19, SQLite `ok`,
`admission_mode=recovery`, OAuth principals 0 và còn 1 unresolved action chưa
quarantine; không mở admission hoặc tự reconcile từ runbook này. Vì target đã
reachable, không còn dừng ở `WAITING_FOR_WINDOWS_RUNNER`; các bước bên dưới là
gate còn thiếu để nâng từ candidate `PACKAGED_PROOF` lên `LIVE_ACCEPTED`.

Wave 26 xác thực lại các lane trên cùng candidate với kết quả **18/18**, **3/3**,
**1/1**, **1/1**, **1/1**. Node credential heartbeat `degraded` pass; registry
đã có một workspace opaque với capability `{read,write,exec}`. Tuy nhiên
Electron/Node process không chạy, `runtime-heartbeat` trả
`blocked/runtime_unavailable` với runtime state `MISSING`; connected-agent một
iteration dừng `MAX_ITERATIONS_REACHED` và không nhận action/gửi receipt.
Vì vậy target đã mở để test và credential/registry đã được quan sát, nhưng chưa
phải installed live runtime đã bind; vẫn cần owner-authorized exact startup,
strict identity, binding/task, toolchain thật và fault gates.

Official packaged smoke vừa pass trên candidate với exit 0: 17 resources, 8
smart-v3 tools, Recovery Host/MCP/device identity, Supervisor healthy và
fail-closed owner/hash paths; production descriptor stable, Scheduled Task không
mutate, TEMP user-data cleanup pass. Đây vẫn là `PACKAGED_PROOF`; không thay thế
installed startup/reconnect, OAuth two-client, toolchain thật hoặc owner gate.

Source-side account/binding/writer recheck đạt **4/4**, local exec/document/
standing-patch recheck đạt **3/3** bằng `unittest`; local pytest command thiếu
module `pytest` nên không được tính là test failure. Đây chỉ là source proof bổ
sung, không thay thế exact installed/live gates.

Control Plane source discovery vừa đạt **298/298 PASS trong 96,772s** bằng
`unittest`; đây chỉ là regression evidence trên Ubuntu/worktree, không thay
thế Windows installed/runtime, two-client ChatGPT hoặc owner acceptance.

Installed NSIS smoke vừa pass **exit 0** trên candidate `1.0.7`: install/register,
packaged smoke, uninstall và registration cleanup; production descriptor cùng
Scheduled Task definition stable. Đây vẫn là candidate installed proof, chưa
thay thế reboot/logon/reconnect hoặc live account/toolchain gates.

Post-check sau smoke: candidate process count **0**; descriptor hiện diện nhưng
owner process không sống, nên phải ghi là stale/observation-only. Descriptor tồn
tại không thay cho strict runtime heartbeat hoặc installed liveness.

### Wave 37 — SSH handoff packaged pass, chưa mở strict execution — 21-09-2026, 13:36 +07

Handoff trên `DESKTOP-63643J4` đã được thực hiện bằng đường chính thức: ping
descriptor/IPC, `runtime.stop`, kiểm process creation identity và terminate đúng
PID cũ. Supervisor packaged sau đó báo `healthy`, connected agent `running`,
Recovery Host mới ở `runtime_mode=packaged`, `recovery.ping ready=true`.

Probe strict sau handoff trả `central_connected=true` nhưng
`authority_ready=false`, `central_status_reason=LOCAL_EXECUTOR_NOT_READY`,
`fully_ready=false`, `update_incomplete=true`; epoch đang `FAILED` với
`RECOVERY_REPLACEMENT_TARGET_CHANGED`. Đây là lý do không được gọi
`runtime.start`/full-clean retry mù, không dequeue action và không gọi model.

Local registry có capability `{read,write,exec}` nhưng root là
`E:\DEV\Codex-web-candidate-502ffb8`; root cần nghiệm thu là
`E:\DEV\Codex-web`. Lệnh chính thức cần dùng khi owner xác nhận là:

```powershell
& '<candidate>\resources\resources\control-plane\node-agent.cmd' replace-workspace `
  --config "$env:APPDATA\web-mcp-assistant\control-plane-node.json" `
  --workspace-registry "$env:APPDATA\web-mcp-assistant\control-plane-workspaces.json" `
  --workspace-path 'E:\DEV\Codex-web' `
  --display-name 'Codex-web' `
  --capability-read --capability-write --capability-exec `
  --confirm-replace
```

Lệnh này **không chạy tự động** vì nó retire generation cũ, tắt policy local
khớp generation và fence binding/task trên account dùng chung. Owner phải xác
nhận ảnh hưởng tới client khác trước; sau receipt replacement mới cài lại
standing policy theo generation mới và tiếp tục full-clean activation exact
source.

### Wave 38 — kết quả lệnh replacement đã xác nhận — 21-09-2026

Lệnh trên đã được chạy sau owner confirmation nhưng trả:
`CONTROL_PLANE_WORKSPACE_REPLACEMENT_NOT_FOUND`. Nguyên nhân là CLI hiện tại
chỉ tìm old entry bằng chính canonical path mới; nó không phải thao tác migrate
path. Kiểm tra sau lỗi chứng minh registry/policy/Supervisor không đổi và không
có journal dở dang.

Không tự dùng `retire-workspace` + `register-workspace`: luồng đó tạo opaque
`workspace_id` mới, làm sai mục tiêu giữ identity dùng chung. Nếu cần giữ ID,
cần bổ sung product/artifact path-migration explicit rồi build/cài candidate
mới; nếu chấp nhận ID mới, owner phải xác nhận riêng để chạy retire/register.

### Wave 36 — BLOCKED chờ owner activation — 21-09-2026, 12:41 +07

Authoritative `dev:status` vẫn `state=MISSING`, `host=unavailable`,
`RECOVERY_DESCRIPTOR_STALE`; Supervisor Task `Running` nhưng
`spawn_failed/SPAWN_FAILED` vì executable bị thiếu. Blocker này đã lặp qua
Waves 33–36 và source suite đã pass, nên không còn phép thử read-only nào có
thể chứng minh runtime live.

Owner action bắt buộc: acceptance ceremony trên exact source/artifact →
supported full-clean activation → Supervisor install đúng checkout nếu cần.
Không sửa activation record/closure bằng tay.

## Hướng dẫn chi tiết cho owner: từ `DESCRIPTOR_STALE` tới `LIVE_ACCEPTED`

Phần này là trình tự thao tác cho cửa sổ test của
`DESKTOP-63643J4`. Owner phải chạy trên máy Windows đã đăng nhập đúng user
đã giữ data root; các lệnh có nhãn **MUTATION** có thể cài Scheduled Task,
tạo activation epoch hoặc thay process. Lệnh **READ-ONLY** chỉ quan sát và
không làm cho runtime sống lại. Không dán token, DPAPI payload,
`Authorization` header, secret hoặc nội dung workspace vào receipt/chat.

### Bước 1 — chốt exact checkout trước khi đụng runtime (READ-ONLY)

Chạy từ checkout mà owner thực sự muốn nghiệm thu, không chạy lẫn candidate
không có `.git` với checkout Git:

```powershell
Set-Location E:\DEV\Codex-web
git rev-parse --show-toplevel
$head = (git rev-parse HEAD).Trim()
$version = (node -p "require('./package.json').version").Trim()
"HEAD=$head"
"VERSION=$version"
git status --short
npm run dev:status
```

Ghi lại `HEAD`, version và trạng thái dirty trong receipt nội bộ. Checkout thật
đã sạch và runtime component exact code lineage là
`abc1a639a2bfd48a7f8c7c212bc26bb7724c9fc0`; candidate
`E:\DEV\Codex-web-candidate-502ffb8` đã retire. Vì vậy:

- dùng candidate chỉ để nói `PACKAGED_PROOF`/installed smoke;
- muốn activation code phải dùng đúng checkout/artifact mà owner vừa review và
  tạo closure mới cho nó;
- nếu cần đổi HEAD hoặc dọn dirty worktree, owner phải thực hiện bằng quy
  trình Git riêng đã được chấp thuận; không `reset --hard`, không copy closure
  hoặc epoch từ máy khác.

### Bước 2 — đối chiếu artifact/package với source (READ-ONLY)

Nếu nghiệm thu package, lấy version và hash installer/unpacked artifact ngay
trên cùng source window. Ví dụ:

```powershell
Set-Location E:\DEV\Codex-web
Get-ChildItem -LiteralPath .\dist -File -Filter '*.exe' |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 3 FullName,Length,LastWriteTime

$installer = Get-ChildItem -LiteralPath .\dist -File -Filter '*.exe' |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1
if ($null -ne $installer) {
  Get-FileHash -LiteralPath $installer.FullName -Algorithm SHA256
}
node scripts/verify-packaged-resources.js
```

Hash/version phải được ghi cùng exact source/checkpoint. Hash của candidate
không có `.git` không được dùng làm `accepted_head` hay Git/release proof.

### Bước 3 — tạo acceptance closure bằng luồng chính thức (MUTATION của hồ sơ)

Trong Electron/ChatGPT Control Center, owner mở đúng EOCL run/wave đang ở
`ACCEPTING`, đọc các receipt rồi accept/checkpoint **đúng source**. Trình tự
EOCL là `PREFLIGHT → READY → ROUTED → EXECUTING → PROVING → ACCEPTING →
CHECKPOINTED`; test xanh chỉ là proof, không tự là acceptance.

Closure phải có đủ các điều kiện sau:

```text
source_accepted=true
accepted_receipts_complete=true
activation_eligible=true
eligibility_code=ACTIVATABLE
affected_components_valid=true
accepted_head == git rev-parse HEAD
lifecycle_clean=true
```

Khi code activation là cần thiết, `affected_components` phải liệt kê đúng
component có byte thay đổi (`recovery_host`, `coding_mcp`, `electron_ui` theo
thứ tự canonical) và mỗi component phải có accepted receipt + postflight
receipt. `affected_components=[]` chỉ phù hợp khi không có code activation;
Windows profile hiện chưa có Recovery Host/closure sau installed-smoke
cleanup, nên **chưa đủ** và không được tự tạo payload thay owner.

Payload checkpoint mà CLI nhận chỉ gồm đúng năm trường sau, lấy từ closure
chính thức; không tự đặt ID/fingerprint:

```powershell
$env:FULL_CLEAN_SOURCE_CHECKPOINT_JSON = @'
{"checkpoint_id":"<closure.source_checkpoint_id>","run_id":"<closure.run_id>","wave_id":"<closure.wave_id>","proof_fingerprint":"<closure.proof_fingerprint>","git_head":"<closure.accepted_head>"}
'@
```

Không sửa tay `accepted-code-activation.json`, `activation-epoch.json`, forge
checkpoint, copy acceptance hoặc receipt từ một HEAD khác. Nếu Control Center
không tạo được closure đủ điều kiện, dừng ở `PACKAGED_PROOF` và ghi mã từ chối.

### Bước 4 — preflight rồi mới full-clean activation

1. Kiểm tra preflight (READ-ONLY):

   ```powershell
   node scripts/full-clean-activation.js --preflight
   ```

   Với owner closure hợp lệ và Recovery Host sống, preflight phải trả
   `safe=true`/component đúng. `RECOVERY_DESCRIPTOR_STALE`,
   `ACTIVATION_SOURCE_CHECKPOINT_NOT_ELIGIBLE` hoặc
   `RECOVERY_BOOTSTRAP_REQUIRED` là từ chối có chủ ý; không retry mù.

2. Chỉ sau khi owner đã chấp thuận cửa sổ thay process và preflight hợp lệ,
   chạy activation (MUTATION):

   ```powershell
   node scripts/full-clean-activation.js --execute
   ```

   Lệnh này tạo deferred operation và có thể thay Recovery Host/MCP/Tunnel/UI
   trong một activation epoch; không chạy khi có task đang cần giữ lease. Lưu
   `operation_id` và xem kết quả bằng lệnh READ-ONLY:

   ```powershell
   $env:FULL_CLEAN_ACTIVATION_OPERATION_ID = '<operation_id trả về>'
   node scripts/full-clean-activation.js --status
   ```

   Chỉ coi activation thành công khi operation và postflight cùng chứng minh
   epoch mới `READY`, admission mở, `fully_ready=true`, component revision đang
   chạy bằng disk revision và connector đã được acknowledge. `npm run dev:refresh`
   là process refresh được hỗ trợ cho development; nó **không** tạo source
   acceptance và không thay cho `FULL_CLEAN_SOURCE_CHECKPOINT_JSON`.

### Bước 5 — khôi phục Supervisor nếu manifest còn trỏ executable cũ

Sau khi source/closure đã đúng, đọc trạng thái trước (READ-ONLY):

```powershell
npm run recovery:supervisor:status
```

Nếu status còn `SPAWN_FAILED`/`Recovery Supervisor executable missing`, owner
chạy từ đúng checkout (MUTATION — cài/cập nhật Scheduled Task và manifest):

```powershell
npm run recovery:supervisor:install
npm run recovery:supervisor:status
```

Kỳ vọng tối thiểu là `installed=true`, Task `Running`, `status.state=healthy`,
không còn `SPAWN_FAILED`/`OWNER_DEAD`, và manifest trỏ tới executable có hash
đúng exact checkout. Không cài Supervisor từ candidate khác source rồi gọi đó
là live proof.

### Bước 6 — strict runtime proof sau activation (READ-ONLY)

Chạy lại hai quan sát độc lập:

```powershell
npm run dev:status
npm run recovery:supervisor:status
```

Không nâng trạng thái nếu có bất kỳ dấu hiệu nào sau đây: `state=MISSING`,
`host=unavailable`, `RECOVERY_DESCRIPTOR_STALE`, `installation=current` sai,
`components_ready=false`, `fully_ready=false`, `runtime_update_incomplete=true`,
MCP `running_revision` khác `disk_revision`, hoặc connector chưa
`CURRENT_ACKNOWLEDGED`/được acknowledge theo contract.

Sau đó chạy heartbeat có chỉ rõ data root (READ-ONLY, không dequeue/execute):

```powershell
$env:PYTHONPATH = "$PWD\control-plane"
python -m control_plane.node_agent runtime-heartbeat `
  --config "$env:APPDATA\web-mcp-assistant\control-plane-node.json" `
  --project-root "$PWD" `
  --data-root "$env:APPDATA\web-mcp-assistant"
```

Kỳ vọng: `readiness=ready`, `runtime_identity=reported`, `fully_ready=true`,
`route_evidence=fresh`. Heartbeat chỉ là một receipt chẩn đoán; nó không thay
cho installed/live process census, owner acceptance hoặc task effect proof.

### Bước 7 — enrollment, workspace và binding lâu dài

Chỉ bắt đầu khi strict runtime đã đạt. Trong Command Center:

1. Chọn **Gửi yêu cầu pairing** trên node; Ubuntu owner approve một lần. Node
   lưu credential riêng trong SecretStore/DPAPI và reconnect sau restart; không
   chép token/context vào mỗi chat.
2. Chọn root local và capability `{read,write,exec}` theo quyền owner. Path
   chỉ lưu ở node; Ubuntu nhận opaque `workspace_id`, generation, label và
   capability. `write`/`exec` là trần local, không biến user Windows thành
   Administrator.
3. Kiểm tra registry (READ-ONLY) bằng launcher packaged được cài đúng:

   ```powershell
   & '<installed>\resources\resources\control-plane\node-agent.cmd' list-workspaces `
     --config "$env:APPDATA\web-mcp-assistant\control-plane-node.json" `
     --workspace-registry "$env:APPDATA\web-mcp-assistant\control-plane-workspaces.json"
   ```

4. Từ account inventory, Ubuntu tạo một `binding_id` opaque cho workspace
   generation đó. `binding_id` không phải token, context, path hay quyền OS;
   revoke/replace generation phải làm binding/task cũ fail-closed.

### Bước 8 — chứng minh nhiều client cùng một tài khoản

Mở ChatGPT client A và B bằng cùng OAuth account. Cả hai phải nhận cùng
`principal_id` (receipt chỉ cần redacted ID) và nhìn thấy `binding_id` của máy
đã bind. A mở task; task phải pin bất biến:

```text
{binding_id, device_id, endpoint_id, workspace_id, workspace_generation}
```

B chỉ observe/continue hoặc mở task khác cùng target theo writer lease; không
retarget task A, không tạo `active_workspace` toàn account. Dấu hiệu đạt là
lệnh từ cả A/B được route tới `DESKTOP-63643J4`/workspace đã bind, không chạy
tại Ubuntu hay máy đang mở chat, và sau reboot node reconnect bằng credential
cũ.

### Bước 9 — parity, fault và tiêu chí kết thúc

Trên binding đã pin, chạy theo thứ tự: `workspace_context` → patch/write →
structured `exec_command`/stop → Git → build/test → deploy fixture có kiểm
soát. Mỗi action phải có task/attempt/generation và terminal receipt; timeout
hoặc mất ACK là `unknown/reconcile_required`, không được đổi thành completed
và retry effect mù.

Sau đó chạy T01–T16, fault/restore và soak tối thiểu 24 giờ như ma trận ở
`SHARED_ACCOUNT_WORKSPACE_STATUS.md`. Chỉ owner mới được đóng EOCL ở
`CHECKPOINTED` và nâng proof thành `LIVE_ACCEPTED`. Nếu còn stale descriptor,
Supervisor error, thiếu reboot/reconnect/rotation, chưa có hai ChatGPT client
thật hoặc chưa có toolchain receipt, báo blocker tương ứng và giữ
`PACKAGED_PROOF`.

### Wave 35 — source lifecycle regression và Windows gate — 21-09-2026, 12:39 +07

Source focused command:
`node --test tests/dev-ui-lifecycle.test.js tests/full-clean-activation.test.js
tests/recovery-supervisor.test.js` → **133 pass, 0 fail, 1 skip** (Windows-only).
Đây là regression proof cho lifecycle/activation guards, không thay thế
installed Windows runtime, owner acceptance hoặc binding/task live.

Target vẫn `RECOVERY_DESCRIPTOR_STALE`; Supervisor vẫn `SPAWN_FAILED`. Không
thực hiện install/restart/dispatch trong wave này.

### Wave 34 — lifecycle preflight và Supervisor status — 21-09-2026, 12:36 +07

`node scripts/dev-ui-lifecycle.js status` chạy từ checkout Windows và candidate
đều trả exit 0 nhưng `state=MISSING`, `host=unavailable`,
`error_code=RECOVERY_DESCRIPTOR_STALE`. `node scripts/full-clean-activation.js
--preflight` trả exit 1 với `RECOVERY_DESCRIPTOR_STALE` vì Recovery Host owner
không còn sống.

Supervisor status xác nhận Task `Running` nhưng `state=spawn_failed`,
`last_error_code=SPAWN_FAILED`, executable bị thiếu. Không retry heartbeat để
che lỗi, không install/restart/sửa activation record trong wave này. Cần owner
acceptance trên exact source/artifact, supported full-clean activation, rồi
Supervisor install và strict flags trước khi chạy binding/task/toolchain thật.

### Wave 33 — read-only đối chiếu target trước activation — 21-09-2026, 12:29 +07

SSH/Tailscale vẫn reachable. Checkout `E:\DEV\Codex-web` trên Windows là HEAD
`3779096a9156bf2827e3164d09bcc1ef647a2c01` với 23 thay đổi; candidate
`E:\DEV\Codex-web-candidate-502ffb8` là `1.0.7` nhưng không có `.git`. Profile
accepted closure đang giữ checkpoint `8d10f27638e2498cba80edf0bcbe77ce` và
accepted HEAD `cffd2acee24a4f38f4a83ddfea4c40f766de7a63`; các cờ còn lại là
`activation_eligible=true`, `affected_components=[]`,
`components_current=false`, `lifecycle_clean=false`.

Bounded `runtime-heartbeat` trả `readiness=blocked`,
`reason=runtime_unavailable`, `runtime_state=MISSING`, `fully_ready=unknown`,
`policy_state=expired_or_disabled`; heartbeat chỉ làm mới route evidence.
Epoch durable hiển thị `READY/OPEN`, nhưng Recovery Host owner PID đã chết,
runtime PID/revision stale và Supervisor Task đang `spawn_failed` với
`SPAWN_FAILED`. Đây là blocker **exact-source/accepted-closure mismatch + stale
Supervisor**, không phải lỗi Tailscale. Wave này không install/restart, không sửa
activation record, không tạo binding/task hoặc dispatch.

Gate tiếp theo là owner chạy acceptance ceremony và supported full-clean
activation trên exact artifact/source; nếu cần thì cài lại Supervisor từ đúng
checkout. Chỉ khi current-process strict proof đạt
`mcp_ready=true`, `identity_current=true`, `central_connected=true`,
`authority_ready=true`, `fully_ready=true` mới tiếp tục live account,
workspace toolchain, T01–T16 và soak.

## Wave 32 — Tailscale live test và điều kiện mở runtime

SSH/Tailscale tới `DESKTOP-63643J4` (`100.72.186.41`) đã được kiểm tra lại.
Installed supervisor manifest trỏ tới executable đã bị uninstall; candidate
unpacked `1.0.7` vẫn có executable nên được mở tạm trên data root hiện hành.
`recovery.ping` trả `ok=true/ready=true`, descriptor/process identity khớp.

Strict observation vẫn trả `mcp_ready=false`, `identity_current=false`; runtime
giữ `central_connected=false`, `authority_ready=false`,
`central_status_reason=LOCAL_EXECUTOR_NOT_READY`, `fully_ready=false`,
`update_incomplete=true`, `recovery_blocked=true`. RPC `runtime.start` bị từ
chối HTTP 409 `UPDATE_INCOMPLETE`; không được thay Coding MCP trong epoch cũ,
phải có full-clean activation epoch mới do owner chấp thuận.

`runtime-heartbeat` exit 0 nhưng chỉ `degraded/packaged_runtime_unready`,
`runtime_state=unknown`, `fully_ready=unknown`, `policy_state=expired_or_disabled`;
route evidence `fresh`. Không có dequeue action, receipt hay model dispatch.
Candidate process đã được dừng sau kiểm tra; hiện descriptor chỉ là stale
metadata; Supervisor ghi `OWNER_DEAD` rồi retry thành `SPAWN_FAILED` vì
executable trong manifest thiếu. Gate tiếp theo không phải thử lại heartbeat,
mà là owner thực hiện full-clean activation trên exact artifact/source rồi mới
kiểm strict MCP/Tunnel/UI identity và binding/task.

## 0. Điều kiện đầu vào

- Checkout phải trỏ tới đúng HEAD/candidate đã được ghi trong
  [`TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md`](TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md).
- Ghi trước `git rev-parse HEAD`, `git status --short` và package version. Nếu
  cần `exact source`, worktree phải sạch; không dùng artifact cũ hơn source.
- Windows x64, Node/npm, PowerShell và quyền user phù hợp; không chạy bằng
  Administrator để che lỗi ACL/local authority.
- Xác định rõ data root test và production; mọi smoke phải dùng temp/user-data
  cô lập. Không in token, DPAPI payload, Authorization header hoặc absolute
  workspace path vào receipt công khai.

Nếu thiếu runner, target unreachable hoặc chưa có cửa sổ owner, dừng ở
`WAITING_FOR_WINDOWS_RUNNER`; không đoán SSH key, password hay target khác.

## 1. Source/package gate

Chạy từ root candidate:

```powershell
npm test
npm run test:mcp
npm run test:all
npm run test:recovery:e2e
npm run dist
```

Sau khi NSIS candidate được tạo:

```powershell
npm run test:recovery:packaged
node scripts/installed-recovery-smoke.js
```

Receipt tối thiểu phải ghi:

- Node/Electron, MCP và Control Plane counts; không coi `SKIP` là `PASS`.
- `dist/win-unpacked`/installer hash gắn với exact source/candidate.
- Packaged Recovery Host identity, independent Recovery MCP, Supervisor healthy
  path và fail-closed live-owner/hash-mismatch paths.
- Installed smoke uninstall hoàn tất; production Recovery descriptor và
  Scheduled Task definition không đổi.

Nếu một lane trả `windows_only`, đó là **chưa chạy gate**, không phải proof.

## 2. Enrollment một lần và credential dài hạn

Trên node A:

1. Gửi enrollment request qua HTTPS tới Ubuntu; đối chiếu fingerprint/approval
   theo luồng UI/operator hiện hành.
2. Kiểm `device_id` bền vững, credential generation và SecretStore/DPAPI ACL;
   không đọc raw secret từ renderer, argv hoặc log.
3. Đăng ký workspace `W1` với capability đã owner chọn. Ubuntu chỉ nhận
   `workspace_id`, generation, display name và capability; path giữ ở node.
4. Xác nhận inventory tạo `binding_id=B1` opaque. `B1` không được dùng như
   bearer token, context ID, path hoặc quyền Administrator.
5. Restart/reboot node rồi kiểm heartbeat/reconnect vẫn dùng credential cũ.
6. Chạy rotation prepare → activate → promote → ack; mô phỏng mất ACK/crash và
   xác nhận retry không tạo credential/effect thứ hai. Sau revoke, task mới phải
   bị chặn, không failover sang máy khác.

## 3. Hai client cùng một tài khoản

Với client ChatGPT A và B đăng nhập cùng account/OAuth (`principal_id` giống
nhau):

1. Cả hai inventory đều nhìn thấy `B1` nhưng không thấy secret/path.
2. A mở task với `binding_id=B1`; task pin
   `{device_id, endpoint_id, workspace_id, workspace_generation}`.
3. B observe/continue theo scope; không được mở cùng idempotency key với target
   khác, retarget task đang chạy hoặc tự tạo `active_workspace` toàn account.
4. Writer lease chỉ cho một writer; handoff chỉ sau terminal receipt hoặc
   reconcile rõ. Client đổi binding mặc định không đổi target task đã mở.

Expected effect: lệnh của A/B chạy tại node A/W1, không chạy tại máy đang mở
chat và không copy workspace lên Ubuntu.

## 4. Local execution parity

Trên `B1`, chạy lần lượt với receipt gắn `principal_id`, `binding_id`, task,
attempt, node và generation:

- `workspace_context`: inventory/read đúng file marker;
- `agent_workflow`: patch nhiều file, stale preimage/path/generation bị từ chối;
- `document_workflow`: create/convert đúng policy và output digest;
- `exec_command` + `command_control`: structured `argv`, cwd tương đối,
  output cursor, stop/quiescence, retry/lost-ACK/unknown;
- Git status/diff/commit trong fixture;
- build và test của fixture;
- deploy giả lập/được owner chỉ định trong workspace, không nâng quyền OS.

Ubuntu chỉ queue/auth/route/receipt. Node local policy, ACL và Runtime/Recovery
Host mới quyết định effect. Không thêm per-command Ubuntu approval trong
standing local scope; không biến MCP/Tunnel thành model API.

## 5. Fault, restore và soak

Chạy T01–T16 theo ma trận trong
[`SHARED_ACCOUNT_WORKSPACE_STATUS.md`](SHARED_ACCOUNT_WORKSPACE_STATUS.md), tối
thiểu các fault sau:

- node offline/reconnect và Ubuntu restart;
- Recovery/MCP crash trước effect, sau effect, sau terminal receipt và mất ACK;
- stale preimage/path/policy/generation;
- writer lease unresolved, stop pending, duplicate retry;
- credential rotation/revoke và workspace replacement;
- backup/restore candidate không tự mở lại action cũ;
- soak liên tục tối thiểu 24 giờ với ledger/receipt không mất hoặc duplicate.

Mỗi ca phải có terminal receipt hoặc `unknown/reconcile_required` trung thực;
không biến timeout thành completed/rejected và không retry mù.

## 6. Exit criteria và báo cáo

Chỉ ghi `PACKAGED_PROOF` khi exact Windows artifact/package/installed smoke và
fault receipts đạt. Chỉ ghi `LIVE_ACCEPTED` khi owner xác nhận hai client cùng
account, target đúng node/workspace, toolchain thật, T01–T16, backup/restore và
soak 24 giờ.

Báo cáo cuối phải nêu: HEAD/source hash, package hash, test counts, skipped
cases, target/binding/task identities đã redacted, receipt paths, mọi blocker,
và xác nhận có/không commit, push, deploy, restart hoặc provider dispatch.
