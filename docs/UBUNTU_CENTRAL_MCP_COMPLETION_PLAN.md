# Kế hoạch hoàn thiện: Ubuntu giữ Tunnel chính và MCP gốc, các máy là client/node

Ngày lập: **16-09-2026**. Source kiểm tra: `main@61cd80eb35dc0bbf5bd48d7f52d665b801190d7b`.
Trạng thái: **kế hoạch triển khai; các gate mới bên dưới chưa đạt**.

## 1. Đích người dùng đã làm rõ — không đổi thành pilot Windows độc lập

**Ubuntu là server trung tâm, giữ OpenAI Tunnel chính, MCP gốc/dùng chung,
điều phối và phiên làm việc. Windows/các máy khác cài client + agent, kết nối
đến Ubuntu và thực thi trên file của chính máy được chọn.** Người dùng không
phải cấu hình OpenAI Runtime Key/Tunnel trên từng máy con.

Đã đọc toàn bộ [kế hoạch gốc ngày 15/09](research/260915_UBUNTU_24X7_CONTROL_PLANE_PLAN.md),
987 dòng. Các phần cần thực hiện cùng nhau là §4 (một ingress/MCP chung),
§5–9 (authority/target/dispatch), §10 (lifecycle), §11.3 (controller khi server
nhận yêu cầu ngôn ngữ tự nhiên), P4 (cutover) và §15–17 (test/operations).

Điều chỉnh so với cách triển khai trước:

- Giữ Tunnel Windows trong bản nghiên cứu là **bước chuyển tiếp**, không phải
  trạng thái hoàn thành. P4 nay là việc bắt buộc, không để sau một mốc “đã xong”.
- MCP trung tâm không được dừng ở danh sách tám tên tool và queue chỉ-đọc.
  Nó phải thực sự chọn đúng máy/workspace, gọi tool và trả kết quả/Job handle.
- UI Windows là client của server và giao diện cấp quyền local; không bắt
  người dùng vận hành thêm một sản phẩm OpenAI-facing độc lập trên mỗi PC.
- Giữ lại code thực thi local hiện có bên trong agent khi hữu ích. Một process
  MCP loopback/stdio nội bộ là chi tiết triển khai, **không phải MCP gốc thứ hai**,
  không có connector OpenAI/Tunnel/model key riêng.
- “Bộ não” gồm model suy luận và phần mềm điều phối. Ubuntu giữ phần mềm,
  session và quyền điều phối; model vẫn được gọi qua dịch vụ được chủ sở hữu
  cho phép. MCP/Tunnel tự thân không phải model và không tự tiếp tục một chat.
- Đây là xây ứng dụng client/server của repo theo trải nghiệm người dùng mong
  muốn; không hứa có thể đổi backend của ứng dụng Codex Desktop chính thức bằng
  một URL, cũng không tự host lại dịch vụ/model OpenAI.

Phạm vi hoàn thành chính gồm: server trung tâm + một luồng tác vụ AI có giới
hạn + Windows agent + UI kiểm soát + đọc/ghi/chạy/dừng + offline/reconnect +
package/rollback/24h soak. Không giảm đích thành SSH chạy được hoặc dashboard
đăng nhập được. WOL, cold boot chưa đăng nhập, HA và tự chuyển workspace sang
Ubuntu là nhánh riêng, không được quảng cáo đã hỗ trợ.

## 2. Baseline đã có và khoảng trống

Đây là số liệu có thời điểm, không phải lời hứa máy luôn giữ trạng thái đó.

| Boundary | Bằng chứng | Kết luận dùng cho kế hoạch |
| --- | --- | --- |
| Source Ubuntu | `61cd80e`, đồng bộ tracking `origin/main`; `.coding-tools` snapshot/ledger có drift runtime | Giữ nguyên evidence; không reset/clean |
| Ubuntu live, recheck 16:20 +07 | `svhome`, `100.116.112.22`, x86_64; service active; schema 8; SQLite `ok`; admission `recovery`; không systemd job đang chạy | Nền central đã triển khai, chưa mở dispatch |
| Release central | `2e64e9485f37cf6f94e8144797ea800a6e050545`, fingerprint `sha256:4bef62162e8a5ccc6de136dbabd2079d5c605a8bbf130aabf48de67655880040` | Runtime khác HEAD docs là bình thường khi bytes đúng manifest |
| UI private | `https://svhome.tail0e4032.ts.net`, Tailscale Serve | Đây là UI/node network, **không phải OpenAI Tunnel chính** |
| Registry, audit 16:11 +07 | Chỉ có `DaoChienThang`, observation cũ từ 15-09 02:55 +07; 0 binding/context/action | Chưa enroll máy văn phòng vào server; không dùng lại identity máy khác |
| Máy văn phòng, audit 16:06–16:11 +07 | `DESKTOP-63643J4`, `100.72.186.41`, profile Admin; app installed; Supervisor healthy và heartbeat fresh | Cài đặt thành công, không chứng minh central E2E |
| Cấu hình Windows | `health.inspect`: runtime-key/tunnel-id/workspace/Python/ports đều hợp lệ; autoStart=false | Không yêu cầu nhập lại key chỉ vì input trống; chưa chứng minh key dùng được ở mọi scope |
| Windows runtime chính | MCP/Tunnel OFF; `recoveryBlocked=true`; log `UPDATE_INCOMPLETE`: không được thay MCP tại chỗ dưới epoch READY đã kết thúc | Cần migration/activation mới được kiểm chứng, không sửa record READY bằng tay |
| Recovery Windows | Recovery Host/MCP/Tunnel healthy trong audit; epoch record READY nhưng runtime chưa ready | Liveness/recovery khác execution readiness; UI hiện gom lý do chưa chính xác |
| Installer cũ | `1.0.0`, SHA-256 `ab376d7b9f1517cc0077d1d7213b874236a4fb5a85148c089d7cec74f750cb54`; unsigned đã được user cho phép cài | Không coi đây là package cho kiến trúc central mới |
| Source Windows | Checkout `9f6b2b3`, sạch trong audit 16:11 +07 | HEAD checkout không chứng minh bytes ứng dụng đã nạp |
| Healthcheck Ubuntu | Timer tồn tại nhưng service check failed: script yêu cầu admission `open`, live là `recovery` | Sửa phân loại maintenance/readiness, không mở admission để che lỗi |
| Root MCP/AI trên Ubuntu | Source worktree đã có grant-scoped root MCP, listener `/mcp` loopback riêng và một relay metadata read-only hẹp cho `workspace_context`; chưa có `tunnel-client`/profile/ID Linux, unit Tunnel hoặc proof client OpenAI thật; bảy tool ngoài lát cắt này vẫn chưa có relay thực | G1 ingress và G4 source đã tiến triển, nhưng G1/G4 live, controller và đủ tám tool vẫn chưa đạt |

Source anchors đã kiểm tra: [MCP facade](../control-plane/control_plane/mcp_facade.py),
[node agent](../control-plane/control_plane/node_agent.py),
[runtime readiness/start](../electron/services/runtimeOrchestrator.js),
[activation](../electron/services/fullCleanActivation.js),
[bridge admission](../electron/services/recoveryHost.js),
[healthcheck](../deploy/control-plane-healthcheck.sh),
[UI](../renderer/app.js). UI chủ động xóa ô key sau lưu và dùng boolean secret
presence để hiển thị dòng xanh; ô trống không chứng minh thiếu key.

Các chứng cứ Git/source/test trong `.coding-tools` không thay thế DB central,
node journal hoặc process live. Trước mỗi rollout phải đo lại đúng các đích;
chưa có census mới chứng minh mọi local Job Windows đã quiescent.

### Checkpoint live G1-L — recheck chỉ-đọc Ubuntu, chưa triển khai central (16-09-2026)

Đo lại trực tiếp trên `svhome` không thay đổi service cho thấy
`codex-control-plane.service` đang `enabled` và `active`, nhưng đang nạp
release đã cài có `schema_version=8` (source hiện tại là 9), admission
`recovery`, 1 node và 2 enrollment request, cùng **0** binding/context/work-request/
action/receipt. Không có listener TCP 8766, unit
`codex-control-plane-mcp-tunnel.service` là `not-found`, và không có
`tunnel-client` trên `PATH`. `tailscale serve` chỉ proxy Tailnet root tới
`100.116.112.22:8765`; `/mcp` ở listener đó trả 404.

Vì vậy Tailscale UI hiện có không phải OpenAI Tunnel/root MCP, và server chưa
thể nhận MCP client/controller. Không đọc env secret, không restart, không
migrate DB, không mở admission và không thay đổi Windows trong lần đo này.
Điều kiện triển khai tiếp theo là một candidate release sạch/được verify, rồi
provision profile Tunnel Linux qua kênh local an toàn trước khi cài unit mới.

### Checkpoint triển khai G1-A — source/test, chưa rollout (16-09-2026)

Đã thay lớp source của root MCP từ việc dùng trực tiếp operator Bearer sang
**MCP access grant** bền vững, chỉ có một `context_id`, `principal_id`, hạn
dùng và khả năng thu hồi. Token thô chỉ trả một lần khi operator tạo grant;
SQLite chỉ giữ digest domain-separated. `/mcp` từ chối operator token, grant
hết hạn/thu hồi/context đóng/binding-node thu hồi và context khác. Intent
read-only mới ghi principal vào lineage. Tại checkpoint G1-A contract source là
`schema_version=4`, profile `control-plane-scoped-read-only-queue-v3`; G4-A
bên dưới đã bump nó lên schema 5 cho relay metadata. SQLite source migration
là `user_version=9`.

Đây là bằng chứng **source + test**. Phần grant ban đầu pass 85 tests; sau
checkpoint G1-B bên dưới, full suite pass 87 tests. Chưa migrate DB Ubuntu,
chưa restart service, chưa cấp grant thật, chưa có Linux Tunnel và chưa có node
Windows central E2E. Vì vậy G1, G4 và các gate sau vẫn mở.

### Checkpoint triển khai G1-B — ingress Tunnel Ubuntu tách route, chưa rollout (16-09-2026)

`serve_from_environment()` hiện tạo hai listener dùng chung Store: listener
Tailnet/UI/API chính tắt hoàn toàn `/mcp`; listener thứ hai bắt buộc bind literal
`127.0.0.1`, mặc định port `8766`, chỉ nhận `POST /mcp`. Tất cả GET, UI,
enrollment, node, operator và admin route bị `404` tại listener Tunnel. Release
có thêm launcher và mẫu user-systemd riêng cho Tunnel; launcher chỉ chạy profile
đã khởi tạo, không nhận, in hoặc lưu Runtime API key. Profile phải được tạo với
URL chính xác `http://127.0.0.1:8766/mcp` rồi `doctor` trước khi service chạy.

Proof source: route-isolation, environment validation và archive-extraction
test đều pass; full `PYTHONPATH=control-plane python3 -m unittest discover -s
control-plane/tests -v` pass **87 tests**. Test archive khởi động cả hai
listener thực và chứng minh grant chỉ được nhận ở loopback `/mcp`.

Recheck Ubuntu chỉ-đọc sau thay đổi source: `codex-control-plane.service` vẫn
`active` và `enabled`, nhưng config không có các field MCP bind/port hay
Tunnel client/profile/ID; `tunnel-client` không có trên `PATH`; unit
`codex-control-plane-mcp-tunnel.service` chưa được cài. Không đọc secret,
không đổi service, không restart hay deploy trong recheck. Đây là blocker G1
live chính xác: cần cài binary chính thức, tạo profile an toàn, chạy `doctor`,
build/verify release rồi mới cài hai unit theo trình tự rollback được. Nó không
phải lý do để quay lại yêu cầu Tunnel/Runtime key trên Windows.

### Checkpoint triển khai G2-A — role node bền vững, chưa đổi lifecycle (16-09-2026)

Electron settings source nay có `executionRole`: `direct_legacy` hoặc
`central_executor`, schema config v7. Giá trị cũ/không hợp lệ luôn trở về
`direct_legacy`; role này hoàn toàn tách khỏi `runtime_mode`
`development/packaged` và không tự tạo/xóa/đổi Tunnel ID. Nó mới là contract
cho handoff có kiểm soát, **chưa** làm Windows executor khởi động không cần
Tunnel/key và chưa tự đổi profile đang cài.

Focused settings checks pass 11/11. Full `tests/settings.test.js` trên Ubuntu
còn một failure nền của test MRU dùng literal `C:\\workspace-*` trong khi
`path.isAbsolute` của Linux trả false; chạy đúng `config.js` ở `HEAD` trước
thay đổi cũng cho count 0. Không sửa chệch test/path semantics trong wave này.
G2 còn cần đưa role vào activation epoch, runtime/recovery readiness và
Supervisor theo đúng migration có fence/census của kế hoạch.

### Checkpoint triển khai G2-B — local executor source/test, chưa handoff (16-09-2026)

`RuntimeOrchestrator` nay có nhánh `central_executor` có kiểm soát. Node ở
nhánh này khởi động và kiểm tra **MCP loopback local** nhưng không đọc
`runtimeApiKey`, không đòi `tunnelId`/`recoveryTunnelId`, không kiểm tra hay
spawn `tunnel-client`, không resolve proxy cho OpenAI, và không làm giả
`tunnelRunning`/connector ACK. Nếu một direct Tunnel cũ do chính node quản lý
còn chạy, lifecycle chỉ gọi owned stop trước bootstrap; không tìm/diệt process
không rõ nguồn gốc.

Snapshot tách rõ `localReady`, `directReady`, `centralConnected`,
`authorityReady` và `centralStatusReason`. Local MCP healthy hiện cho
`componentsReady=true`, nhưng vẫn `fullyReady=false` với
`CENTRAL_ROUTE_NOT_CONFIGURED` đến khi G3/G4 có pairing + authenticated route
proof + per-action authority thật. Watchdog central không bao giờ chọn
Tunnel-only recovery; local process recovery cũng không nạp key/Tunnel node.
`executionRole` chưa được mở cho generic Settings Save: chuyển role phải qua
full-clean handoff/fence riêng, không phải click một toggle.

Proof mới: focused bootstrap/readiness/watchdog tests pass 6/6; focused config
tests pass 3/3; syntax checks và `git diff --check` pass. Full
`tests/runtime-lifecycle.test.js` chạy 84/87; ba failure có sẵn theo platform
Linux: hai fixture dùng `C:\\...` với `path.isAbsolute` Linux, một fixture gọi
`netstat.exe`. Những test đó không nằm trên nhánh central mới; không sửa chệch
Windows-path/process semantics ở wave này. Chưa chuyển config máy văn phòng,
chưa restart/cài app, chưa pair node, chưa build artifact hay đụng Ubuntu
service.

### Checkpoint triển khai G2-C — central-route proof source/test, chưa handoff (16-09-2026)

Điểm thiếu đã được bịt ở mức source: `central_executor` không còn có thể chỉ
đứng mãi ở dòng chung `CENTRAL_ROUTE_NOT_CONFIGURED`. Node agent chỉ sau khi
nhận **echo đầy đủ của heartbeat đã xác thực** từ Ubuntu mới ghi một
`control-plane-route-evidence.json` không có credential vào data root Electron.
Evidence buộc exact device ID, endpoint, origin, credential generation, server
timestamp, local timestamp, readiness và state policy; Electron từ chối record
missing/malformed/future/stale quá 60 giây/copy sang device khác. Nó chỉ có
nghĩa “node vừa nối xác thực tới Ubuntu”, không phải action grant.

Runtime central tách ba trạng thái thật: `localReady`, `centralConnected` và
`authorityReady` (policy local read-only còn hạn). Chỉ khi cả ba cùng đúng mới
`fullyReady=true`; không giả `tunnelRunning` hay connector ACK. Recovery Host
và packaged observer cũng nhận central route + policy làm gate thay cho local
OpenAI Tunnel trong mode central; per-action vẫn qua local bridge policy,
identity và envelope. Tests focused đã cover evidence fresh, stale, copy sai
device, thiếu policy, echo response thiếu và central readiness không Tunnel.

Đây vẫn là **source/test**. Nó chưa làm full-clean activation central chạy
được trên package cũ, chưa pair `DESKTOP-63643J4`, chưa cài policy, không có
central action/read thật và chưa dừng Tunnel Windows live. Lifecycle full-clean
còn phải tách recovery/Tunnel-local census sang central route census trước
cutover candidate; không biến route status file thành cách bypass gate đó.

### Cập nhật validation G2-C và thiết kế bắt buộc G2-D (16-09-2026)

Sau checkpoint trên, toàn bộ `tests/runtime-lifecycle.test.js` đã pass **87/87**
và `tests/settings.test.js` pass **14/14** trên Ubuntu. Hai fixture Windows
trước đó phơi lộ lỗi thật của comparator: path từ health/activation payload
được parse theo Linux khi test/control host là Linux. Comparator nay nhận diện
drive/UNC Windows và dùng `path.win32`, vì vậy path khác workspace không còn có
thể trở thành health success giả. Một seam PID listener chỉ có ở constructor
cho fixture soft-recovery; production vẫn dùng probe listener Windows mặc định.

G2-D không được chỉ đổi một điều kiện `tunnelRunning`. Handoff direct ↔ central
phải là một activation epoch mới chứa `execution_role` và `component_profile`
immutable. Tiếp tục replacement phải:

1. đọc role/profile từ epoch, không suy luận từ key/Tunnel còn sót trong
   Settings; terminal direct READY không thể là proof central;
2. close/fence, quiesce **owned** MCP/Tunnel/recovery child cũ, capture identity
   evidence và chỉ sau đó persist role mới; không kill PID/port không rõ owner;
3. trong central profile chỉ launch local MCP + recovery local cần thiết với
   credential loopback; scrub Tunnel ID/API-key khỏi input Recovery Plane và
   không spawn primary hay recovery OpenAI Tunnel;
4. final census central phải vẫn kiểm exact MCP/recovery-process/epoch/revision/
   workspace/device/UI-or-supervisor liveness và projection receipt, nhưng thay
   Tunnel identity + connector ACK bằng route evidence fresh đúng device,
   server origin/endpoint/generation và policy local còn hạn;
5. commit READY chỉ khi census theo component profile pass; revalidate cùng
   profile trước admission. Rollback central → direct phải tạo epoch mới và
   khởi tạo trực tiếp lại theo direct contract, không reuse evidence central.

Các negative tests G2-D phải cover stale/copy route evidence, stale direct
Tunnel record, recovery Tunnel config còn sót, epoch role mismatch, missing
local policy và revision drift sau spawn. Chỉ sau candidate package và các test
này pass mới được chạm vào profile đang cài ở `DESKTOP-63643J4`.

### Checkpoint triển khai G2-D — handoff role/profile source/test, chưa rollout (16-09-2026)

`fullCleanActivation` nay đóng vai trò direct/central cùng `component_profile`
vào epoch bất biến. Đổi role ngoài `full_clean_execution_role_handoff` bị từ
chối; replay có role khác epoch cũng bị từ chối. Khi replacement đã fence và
dừng các child do nó sở hữu, role mới mới được lưu từ epoch bền vững. Điều này
không cho Settings/UI đổi một cờ để vô tình hồi sinh ingress direct cũ.

Ở `central_executor`, startup Recovery Plane chỉ nhận MCP local và credential
loopback: primary/recovery Tunnel ID bị rút khỏi input, `runtimeApiKey` không
được đọc, không query/spawn Tunnel và final census thay Tunnel/connector ACK
bằng `central_connected + authority_ready + central_route_verified`. READY
central còn bắt buộc exact MCP/recovery/epoch/workspace/device/revision/process
identity/UI proof; route lên nhưng một proof còn thiếu cũng bị đóng admission.

Đã sửa một lỗi fail-closed sẵn có của census: timeout bị `unref` có thể làm
Promise cleanup bị bỏ dở nếu child không chịu thoát. Deadline nay giữ tiến trình
sống đến khi có `confirmed` hoặc `CLEANUP_UNCERTAIN`, không còn test treo/hủy
dây chuyền. Validation: `tests/full-clean-activation.test.js` **58/58**,
`tests/activation-epoch.test.js` **21/21**, syntax của hai service và
`git diff --check` pass. Đây chỉ là source/test; còn thiếu candidate package,
role-handoff UI có kiểm soát, pairing/policy thật, cutover office node và
rollback/soak. Không thay Settings hay Tunnel trên máy đang dùng.

### Checkpoint triển khai G2-E — role-handoff UI có kiểm soát, chờ package Windows (16-09-2026)

Khoảng trống UI ở G2-D đã được đóng trong source. Khi Windows còn
`direct_legacy`, Connections hiện một nút duy nhất **Chuyển sang executor
Ubuntu**. IPC không nhận role, key, Tunnel, workspace hoặc tham số từ renderer;
nó chỉ nhận từ Manager, lấy checkpoint Recovery Host mới qua
`fullCleanRestartOptions()`, rồi yêu cầu đúng
`executionRole=central_executor` với mode
`full_clean_execution_role_handoff`. `FullCleanActivation` vẫn là nơi duy nhất
persist role sau fence/census; Settings/UI không thể tự set cờ role.

Nút biến mất sau khi role central được xác nhận. Cấu hình direct cũ không bị
hiển thị hoặc gửi tới Ubuntu và không còn được Runtime đọc; nó chỉ còn là dữ
liệu rollback có kiểm soát. Bước kế tiếp bắt buộc vẫn là pairing, binding,
context và policy từ Ubuntu; handoff không tự cấp route evidence, action grant
hay quyền ghi/thực thi.

Proof source: syntax Electron/renderer, `tests/control-center-manager.test.js`,
`tests/recovery-plane.test.js`, `tests/dev-ui-lifecycle.test.js`,
`tests/full-clean-activation.test.js`, `tests/activation-epoch.test.js`,
`tests/runtime-lifecycle.test.js`, `tests/settings.test.js` và các test
control-plane focused đã pass trên Ubuntu. Chưa coi là rollout: còn phải commit,
đóng gói/cài candidate Windows, thực thi nút handoff trên `DESKTOP-63643J4`,
rồi đo pairing/policy/route proof live trước khi mở bất kỳ admission nào.

### Checkpoint triển khai G3-A — read-only agent bền vững source/test, chưa onboarding (16-09-2026)

Node adapter có thêm `run-read-only-agent`: process cùng user chạy dài hạn
nhưng vẫn chỉ gọi allowlist `workspace_context`. Mỗi vòng revalidate policy
local trước heartbeat/poll; policy thiếu, tắt, hết hạn, malformed hoặc sai node
thì dừng ngay trước dequeue. Runtime/network lỗi dùng exponential backoff bị
chặn trần; không lặp effect đã có khả năng chạy. Lock atomically-created cạnh
config ngăn hai agent cùng profile chạy song song; chỉ reclaim lock khi PID ghi
trong lock được xác nhận đã chết, còn lock malformed/không chắc chắn giữ
fail-closed.

Recovery Supervisor packaged source đã quản lý entrypoint này mà không thêm
Scheduled Task: manifest candidate ghi hash của bundled Python và agent; chỉ
khi hash đúng, node config đã pair và policy v2 enabled/chưa expiry/match
server-device-endpoint thì Supervisor mới spawn agent trong **cùng interactive
user**. Trạng thái `manifest_legacy`, `waiting_for_pairing`, policy mismatch,
integrity failure, PID hay spawn failure được ghi riêng vào status; supervisor
cũ thiếu manifest field không đoán path và không spawn agent.

Proof focused: loop/read-only agent có test revalidation, disable/expiry stop,
transient backoff, live-lock refusal và stale-lock reclaim; tất cả pass. Lệnh
này không tạo Scheduled Task mới, không chạy Session 0/SYSTEM, không dùng key/
Tunnel OpenAI và không thêm mutation. Vì vậy G3 live vẫn chờ pairing thực,
policy local được operator duyệt, **candidate installer/Supervisor** có kiểm
tra upgrade và heartbeat/reconnect trên office node; không gọi source/test là
onboarding hoàn tất.

### Checkpoint triển khai G3-B — UI pairing packaged source/test, chưa gửi từ Windows (16-09-2026)

Command Center cho `central_executor` nay có đúng một ô HTTPS origin Ubuntu và
nút gửi enrollment. IPC chỉ nhận từ cửa sổ Command Center, từ role central đã
được full-clean handoff; không có API đổi role, cấp binding/context/policy hay
đưa Runtime API Key, Tunnel ID/OpenAI credential sang node. Launcher chỉ chạy
Python/node-agent đã bundled trong candidate packaged, môi trường con bị
allowlist; source/development mode, URL có path/credential hoặc HTTP đều bị
từ chối trước khi ghi config.

Node agent ghi config v1 vào đúng Electron `dataRoot` trước request để retry
với cùng credential hash là idempotent. Đổi Ubuntu/device/endpoint cần cờ CLI
explicit, tạo credential mới và không kế thừa target cũ. Supervisor chỉ thấy
config này như tín hiệu `waiting_for_pairing`; nó vẫn không spawn loop cho tới
khi Ubuntu đã duyệt và local policy v2 khớp server/device/endpoint, còn
binding/context/action là các record tách biệt.

Proof focused: syntax Electron; `tests/control-plane-enrollment.test.js`,
`tests/control-center-manager.test.js`, `tests/recovery-supervisor.test.js`,
`tests/recovery-host.test.js`, `tests/dev-ui-lifecycle.test.js`; và hai
negative Python enrollment tests đều pass. Lần test đầu tiên trước khi sửa
va chạm tên helper đã tạo thêm một enrollment pending trên Ubuntu; record đó
không có approval, binding, context, policy hay action và không được tính là
onboarding. Không tự xóa lịch sử DB. Chưa có candidate package, chưa cài/chạy
nút pairing trên `DESKTOP-63643J4`, chưa duyệt enrollment thật và chưa có
route evidence live.

### Checkpoint triển khai G3-C — browser binding/context có giới hạn source/test, chưa rollout (16-09-2026)

Private operator console Ubuntu không còn dừng ở duyệt identity. Sau khi một
node đã được enrollment, operator có thể chọn node, nhập **opaque** workspace
ID/generation đã đối soát độc lập và tạo binding; không có ô path Windows,
content hoặc secret. Context được cấp riêng từ server clock, chỉ 5 phút–24 giờ;
browser không gửi expiry tuyệt đối. Close context và revoke binding là thao tác
explicit có confirm và chỉ từ chối action chưa gửi — không báo sai rằng một
effect đã gửi đã bị dừng.

Các route browser mới bắt buộc private session, HTTPS same-origin và CSRF;
payload có shape/type strict. Chúng không cài policy local, không mở admission,
không làm node chạy và không cấp model/Tunnel credential. `unittest discover`
control-plane hiện pass **96 tests**, gồm test cross-origin bị 403, invalid
duration bị từ chối, lifecycle create/close/revoke và không lộ credential.
Đây vẫn chỉ là source/test: policy phải được cấp trên Windows sau candidate
install, còn UI/live direct walkthrough và route proof chưa có.

### Checkpoint triển khai G3-D — cài policy read-only theo context source/test, chưa rollout (16-09-2026)

Sau khi operator tạo context trong Ubuntu Console, Command Center của node
central có thể nhận đúng mã `ctx_…` đó và thực hiện một lần **cài local có
xác nhận**. Electron chỉ chạy node-agent đã bundled từ candidate packaged;
agent dùng credential node giữ tại máy để gọi endpoint Ubuntu đã xác thực.
Ubuntu chỉ trả template khi context còn live và đúng cùng `device_id` +
`endpoint_id`. Template chứa scope opaque, expiry theo clock server và contract
facade; không chứa operator bearer, node secret, OpenAI Runtime Key, Tunnel ID,
đường dẫn Windows hay content workspace.

Renderer không nhận secret, chỉ thấy receipt allowlist (expiry, digest,
`runtime_mode=packaged`, ACL state). Thay policy hiện có cần checkbox explicit;
agent không overwrite mặc định. Context đóng/hết hạn hoặc context của node khác
đều bị server từ chối trước khi policy được ghi. Cài policy chỉ mở lane
**read-only** hiện có: nó không tạo action, không cấp ghi/exec, không mở
admission, không chạy model và không biến node thành Tunnel/MCP gốc.

Proof: kiểm thử HTTP chặn node khác/context đã đóng; node-agent chỉ ghi policy
từ response có shape/target đúng; Electron service/IPC/UI syntax và hai suite
`control-plane-enrollment` + `control-center-manager` đều pass. Toàn bộ
`PYTHONPATH=control-plane python3 -m unittest discover -s control-plane/tests`
pass **98 tests**.
Đây vẫn chỉ là source/test trên Ubuntu: package clean, upgrade office,
pair/approve/bind/context/policy live, read-only canary và proof route thực vẫn
chưa đạt. Không dùng checkpoint này để nói Windows đã kết nối hoặc được phép
thực thi.

### Checkpoint live G3-L — office SSH inventory chỉ-đọc, chưa onboarding (16-09-2026)

Từ Ubuntu, SSH batch-key tới đúng Tailscale node `100.72.186.41` đã xác nhận
host `DESKTOP-63643J4`, user `admin` và service `sshd` đang `Running`. Truy vấn
chỉ đọc xác nhận `Coding Tools MCP 1.0.0` đang được đăng ký, data root Electron
tồn tại và `WebMCP Recovery Supervisor` đang `Running`. Đây là bằng chứng kênh
quản trị/rollback có thể dùng, không phải proof central execution.

Trong data root hiện không có `control-plane-node.json`, read-only policy hoặc
route evidence. Supervisor status tự báo `healthy`, zero consecutive failures
và không error; LastTaskResult cũ `0x800710E0` không phải trạng thái process
hiện tại. Manifest packaged schema 1 vẫn thiếu hash Python/node-agent control
plane, do đó agent state trống và không có agent PID — đúng là legacy profile,
không phải pairing failure. Registry installer cũng không có `InstallLocation`;
không suy diễn path executable hay coi đó là hỏng installer. Kết luận đúng là
máy office chưa pair/cấp policy/handoff central và vẫn phải đi qua upgrade
candidate + full-clean activation. Kết nối SSH cảnh báo thuật toán KEX hiện
không post-quantum; đây là hardening riêng cần đánh giá sau, không tự sửa `sshd`
trong cutover.

### Checkpoint live G9-L — office preservation inventory chỉ-đọc (16-09-2026)

Preflight qua SSH chỉ liệt kê presence/byte-size, không đọc nội dung profile,
secret, workspace hay ledger. Profile hiện có các artifact phải giữ khi upgrade:
`device.json` (155 B), `settings.json` (1,246 B), `secrets.bin` (334 B),
`runtime-state.json` (2,564 B), `activation-epoch.json` (540,316 B),
`recovery-host.json` (676 B) và `recovery-supervisor-status.json` (877 B).
`task-state.json` không có. Ba artifact central expected (node config, policy,
route evidence) đều chưa có — phù hợp chưa onboarding, không phải file cần tự
tạo trước upgrade.

Đây là inventory để tạo backup/reconcile sau này, không thay verified snapshot
hay proof content. Upgrade candidate phải preserve những file trên và workspace
ledger riêng, rồi đối chiếu existence/identity/permission trước khi full-clean
activation; không uninstall bản office hoặc xóa `secrets.bin` để làm installer
smoke xanh.

### Checkpoint triển khai G4-A — relay metadata workspace source/test, chưa canary (16-09-2026)

`workspace_context` nay có thể trả kết quả của **một action đã hoàn tất**,
nhưng chỉ qua receipt thuộc đúng owner/context/action và đúng facade contract
hiện tại (`schema_version=5`, profile
`control-plane-scoped-read-only-relay-v4`). Đây không phải tunnel, file relay
hay endpoint MCP tổng quát: client chỉ có thể queue fixed request
`{detail:"compact",max_entries:1}`, rồi hỏi lại đúng `action_id`.

Kết quả được allowlist và kiểm tra lại ở Runtime Orchestrator, Recovery Host,
subprocess CJS, Python node agent và MCP facade. Payload chỉ gồm project
type/name/version, tối đa một entry gốc (tên, loại, kích thước, hidden/ignored)
và Git compact (is-repo, branch, số thay đổi, truncated). Nó loại tuyệt đối
absolute Windows path, file content, task text, symlink target, local handle,
token và field lạ. Digest canonical của summary được xác minh độc lập trên các
biên JavaScript/CJS/Python, bao gồm object bên trong array, nên Unicode/field
order không thể làm receipt hợp lệ bị từ chối hoặc receipt khác bị thay thế.

Proof focused đã pass: 46 Node tests ở Runtime bridge/Recovery Host/CJS bridge
và 1 test HTTP MCP façade end-to-end với receipt có raw workspace giả; output
chỉ còn summary allowlist. Đây là **source/test**: chưa build artifact, chưa
cài policy Windows, chưa pair node, chưa gọi MCP qua Tunnel Ubuntu, chưa đọc
workspace thật. G4 canary và toàn bộ G5–G9 vẫn mở.

### Checkpoint triển khai G7-A — UI executor central source/test, chưa cài Windows (16-09-2026)

Electron renderer nay đọc `executionRole=central_executor` thay vì suy diễn từ
ô key/Tunnel. Ở role này UI ẩn và disable mọi input/button OpenAI Tunnel,
Runtime API Key và Recovery Tunnel của Windows; hướng dẫn connector local cũng
được thay bằng hướng dẫn pairing Ubuntu. Giá trị direct legacy cũ được giữ
nguyên khi người dùng lưu workspace/settings trong central mode, để chỉ
full-clean handoff có kiểm soát mới quyết định retire/rollback chúng.

Status UI hiện phân biệt local MCP, `centralConnected`, `authorityReady` và
`centralStatusReason`: "MCP local đang chạy" không còn tự đổi thành Tunnel
xanh. Các vị trí hero/sidebar/device/source summary hiển thị rõ Tunnel là do
Ubuntu quản lý, hoặc đang chờ pairing/policy, thay vì bắt người dùng nhập key
Windows. Closure view central cũng kiểm tra central route proof thay cho
`tunnelRunning` local.

Proof source: `tests/control-center-manager.test.js`, central-route evidence,
runtime lifecycle, full-clean activation và settings tests đều pass; syntax
renderer và `git diff --check` pass. Đây chưa phải Windows rendering/live
pairing proof, chưa thêm UI chọn server/pairing code và không tự thay đổi role
máy đang cài. G7 complete vẫn phụ thuộc G3/G6 và walkthrough browser thật.

### Checkpoint G9a — strict package gate và recheck live, chưa rollout (16-09-2026)

Đã gọi builder chuẩn `npm run dist:control-plane`. Builder dừng với
`CONTROL_PLANE_RELEASE_BUILD_FAILED` vì checkout có tracked/untracked release
drift ngoài `.coding-tools`; đó là guard bắt buộc, nên không có archive
candidate nào được tạo từ trạng thái nửa sạch và không dùng artifact cũ trong
`dist/` làm bằng chứng cho source hiện tại. Không tự `git clean`, reset, lách
`require-clean-source`, stage/commit hay thay đổi remote để vượt gate này.

Recheck chỉ-đọc sau đó xác nhận Ubuntu vẫn có đúng một listener
`100.116.112.22:8765`; `codex-control-plane.service` enabled/active ở schema
8, admission `recovery`, SQLite `ok`, 1 node, 2 enrollment request và 0
binding/context/work/action/receipt. URL Tailnet HTTPS phục vụ `/healthz`,
nhưng unit MCP Tunnel riêng là `not-found`/inactive, không có listener 8766 và
không có `tunnel-client` Linux. Vì vậy đây chưa phải root MCP/OpenAI Tunnel
live, và không tiến hành rollout Windows hay restart service.

Điều kiện chính xác để đi tiếp G9a là tạo một snapshot source có ownership rõ
ràng (review + commit delivery theo policy `.coding-tools`, hoặc worktree sạch
được người vận hành chọn), chạy lại build/verify archive, rồi provision profile
Tunnel Linux qua file owner-only. Sau đó mới có thể cài unit mới, approve
enrollment office, cấp policy/binding/context tối thiểu và chạy canary. Không
có bước nào được phép đổi admission `recovery` thành `open` chỉ để UI hết lỗi.

### Checkpoint G8-A — healthcheck phân biệt maintenance source/test, chưa rollout (16-09-2026)

Recheck live cho thấy timer `codex-control-plane-healthcheck` fail vì release
cũ ép `--expected-admission open`, trong khi SQLite đang cố ý ở `recovery`.
Đó không phải bằng chứng service hỏng và không được xử lý bằng cách tự mở
admission. Candidate source nay đòi biến explicit
`CONTROL_PLANE_HEALTH_EXPECTED_ADMISSION` có đúng `recovery` hoặc `open`.
Nó chỉ truyền expectation vào deployment verifier; không có route, mutation
SQLite, restart hay thay đổi admission nào trong script. Template chọn
`recovery` cho migration/canary; operator chỉ đổi sang `open` sau readiness
review độc lập.

Proof: archive/extracted-release test chạy healthcheck thành công cả khi
server `open` và khi operator đưa nó về `recovery`, đồng thời backup/fingerprint
vẫn được kiểm. Service Ubuntu hiện nạp release cũ nên vẫn fail theo contract
cũ cho tới G9a; không sửa file immutable đang chạy. Health PASS ở `recovery`
chỉ chứng minh maintenance đúng kế hoạch, không cấp execution readiness.

## 3. Kiến trúc đích và ranh giới trách nhiệm

### 3.1 Luồng sử dụng

1. Người dùng mở client/web, đăng nhập server Ubuntu, chọn **máy + workspace**.
2. Ubuntu giữ session và WorkRequest; controller trung tâm xử lý yêu cầu qua
   model được phép, gọi cùng MCP gốc mà client bên ngoài sử dụng.
3. Root MCP resolve context/authority rồi ghi action bền vững; node chủ động
   nhận việc qua HTTPS private, thực thi ở đúng máy, trả receipt/kết quả.
4. UI nhận tiến độ và kết quả từ server; đóng cửa sổ không tạo một controller
   khác. Tác vụ chỉ tiếp tục trong quyền/ngân sách đã giao, không vô hạn.
5. Client ChatGPT/Codex được hỗ trợ có thể gọi cùng root MCP qua **Tunnel trên
   Ubuntu**. Một task chỉ có một controller có quyền; không cho client ngoài
   và controller server cùng nhận quyền ghi một RUN.

| Thành phần | Ubuntu | Máy Windows/Linux/macOS tham gia |
| --- | --- | --- |
| Tunnel chính OpenAI | Một endpoint trung tâm và Linux tunnel-client được quản lý | Không bắt buộc, không tự spawn trong central mode |
| MCP gốc | Discovery/schema, target/context, dispatch, result/handle relay | Executor nội bộ, không cần endpoint OpenAI riêng |
| Suy luận/phiên hội thoại | Controller gọi provider, session/turn/approval/budget | UI gửi yêu cầu, xem tiến độ; không giữ provider secret của server |
| File/toolchain/process | Chỉ state/artifact được phép; không tự coi file Windows là file Ubuntu | File thật, toolchain, local Job, policy, effect journal |
| Quyền | Owner/session/intent và delegation có scope | Kiểm tra lại root, process/epoch, grant/fence trước effect |
| UI | Fleet, tasks, approvals, diagnostics, backup/ingress | Pairing, chọn root, local permission, pause/disconnect, mở UI server |

### 3.2 Chọn giải pháp tối thiểu

- Phát triển tiếp **một Python central backend + SQLite** đang có; không thêm
  server Rust cạnh tranh hoặc một cơ chế ghi trực tiếp qua SMB/SSH.
- Nâng façade hiện có thành **root MCP đầy đủ**. “Facade” là cách tổ chức code,
  không được dùng để biện hộ cho tám tool chỉ có tên nhưng không thực thi.
- Node transport v1: HTTPS authenticated polling có backoff trên Tailnet, tái
  dùng action/receipt hiện có. Chỉ thêm long-poll khi cần; không xây đồng thời
  WSS/gRPC/SSH dispatcher. Receipt/status/cancel không bị bỏ đói bởi Job dài.
- Giữ thư viện execution MCP/Recovery và ledger local; thay ownership/lifecycle
  cần thiết để agent central tự vận hành mà không cần OpenAI credentials.
- Native Linux package trên Ubuntu; không copy `.exe` hay launcher `cmd.exe`
  Windows để làm server. Agent mỗi OS dùng runtime/toolchain đúng OS.
- Các protocol/core states trung lập OS. Nghiệm thu Windows thật trước, sau đó
  thêm node thật thứ hai; Linux/macOS chỉ được ghi supported khi có package,
  lifecycle và file/job tests trên OS đó. Không đổi thành lời hứa tất cả OS.

### 3.3 Hai đường mạng, không nhầm ba loại credential

- OpenAI/client → Tunnel trung tâm → MCP gốc Ubuntu.
- Node/client desktop → HTTPS Tailnet Ubuntu → node dispatch/results.
- Credential vận hành Tunnel nằm **Ubuntu**, credential model/API nằm Ubuntu
  khi dùng controller server, credential pairing/node nằm trên từng node.
  Chúng có audience khác nhau; không dùng operator token UI cho node, không
  passthrough cloud key sang Windows, không copy secret-store/cookies giữa máy.
- Root MCP external phải có auth/scoping riêng cho client/controller. Không
  đưa mọi RPC từ Tunnel vào `owner_default` bằng một token operator vô hạn.
- Tailscale Serve không làm cloud client tự truy cập được private IP; không
  bật Funnel/public ingress để né phần tích hợp Tunnel.

OpenAI mô tả Tunnel là kết nối outbound từ host tới MCP private, có mẫu vận
hành VM/systemd; Responses API có thể gọi MCP bằng `tunnel_id`. Điều này hỗ trợ
hướng đặt ingress tại Ubuntu, **chưa chứng minh binary/profile/tài khoản của
máy này hoạt động**. G1 phải xác minh thực tế.
[Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels).

### 3.4 Controller AI cho client mỏng

Đề xuất mặc định cho kế hoạch: **một adapter Responses API ở Ubuntu**, chỉ
được gọi root MCP đã giới hạn task, không có shell/file tool tự chạy trên
filesystem server. Không xây thêm provider framework. Chọn model, thông tin
đăng nhập và ngân sách trước live call; Tunnel runtime key không được coi là
quyền gọi model. Dùng mock/fixture cho implementation trước gate chi phí.

API có công cụ lọc tool và luồng approval; approval transport vẫn không thay
cho local grant/fence của dự án. Adapter phải lưu liên kết provider response/
tool call với exact action và thực thi chính sách scope ở server, không chỉ
dựa vào model tuân theo prompt.
[MCP and Connectors](https://developers.openai.com/api/docs/guides/tools-connectors-mcp).

Đây là **lựa chọn kỹ thuật đề xuất**, không phải mặc định tiêu tiền. Nếu owner
chọn Codex App Server thay API adapter, chốt thay thế trước G6, chỉ làm một
đường. App Server là adapter cho thread/turn/event/approval; không tự có fleet
executor, không expose listener thô ra Internet, và phải chứng minh built-in
local tools không thao tác nhầm Ubuntu khi target là Windows.
[Codex App Server](https://learn.chatgpt.com/docs/app-server).

## 4. Những bất biến không được bỏ để làm trạng thái xanh

1. Một root MCP phía client; một writer hợp lệ trên mỗi workspace ở node.
2. Global context bất biến: owner/controller + node/endpoint + workspace ID/
   generation + contract. Không dùng biến active_device chung toàn server.
3. Enrollment không tự cấp quyền file, heartbeat không tự cấp quyền chạy.
4. Giữ local canonical RUN/WAVE/Job/proof/effect và controller generation;
   server điều phối bằng delegation, không copy/merge ledger node.
5. Action/attempt được commit trước send; key/digest/target không đổi sau
   timeout. Mất ACK → reconcile cùng action, không tạo lệnh mới để thử lại.
6. Đóng intake, cancel never-sent, stop Job, revoke authority và rollback file
   là năm hành động khác nhau. UI chỉ báo stopped sau receipt đúng handle.
7. Manual stop local thắng queue/auto-restart; mất mạng không chứng minh Job
   đã dừng. Không mở direct writer cho đến khi scope central đã quiescent.
8. Auth/secret/code phải giới hạn audience/data scope. Preview/log từ node là
   dữ liệu không tin cậy, không được mở rộng grant hay sửa system instruction.
9. Source, tests, package, deployed bytes, live E2E và user outcome là các lớp
   chứng minh riêng. Không lấy process/PID/timer Running làm bằng chứng hoàn tất.

## 5. Các gói công việc và thứ tự bắt buộc

Luồng phụ thuộc: **G0 → G1/G2/G3 → G4 → G5 → G6/G7 → G9a
(package + triển khai candidate) → G8 (fault/restore + soak build cuối)
→ G9b (bàn giao)**.
G1, G2, G3 có thể phát triển song song trên fixture sau khi G0 chốt contract;
không rollout live song song mù. G7 UI được phát triển dần từ G3, không để tới
cuối mới kiểm tra trải nghiệm. G4–G7 dùng candidate fixtures/package riêng để
nghiệm thu từng boundary; mọi thay đổi bytes/deploy sau đó làm mất hiệu lực
soak cũ. Mỗi gói kết thúc bằng report kết quả, Git/build, proof mạnh nhất,
blocker và bước tiếp theo.

### G0 — Chốt contract đích, baseline và kế hoạch chuyển đổi

**Làm:**

- Freeze exact central/Windows candidate, lưu manifest, settings references,
  identity, admission, actions, owned processes và supported Job/ledger census.
- Chọn workspace pilot trên máy văn phòng bằng local UI. `E:\DEV\Codex-web`
  là workspace đang quan sát, **không tự là quyền sửa toàn repo**; dùng fixture
  mới ngoài `.coding-tools` cho mutation/fault trước task thật.
- Ghi vai trò server Ubuntu và một setting vai trò node: `central_executor`
  hoặc `direct_legacy`. Profile cũ thiếu setting giữ legacy, không đoán vai trò
  từ key có/không. Đây không phải `runtime_mode` đang mang nghĩa
  `development/packaged`. Chưa tự đổi mode máy đang chạy.
- Chốt v1 auth, capabilities, target context, receipt schema và quyền data
  relay. Bump contract khi cần; không giả schema root byte-identical local.
- Chốt exact Linux tunnel-client version/source checksum, owner/tunnel endpoint,
  client nghiệm thu, model auth/budget và root pilot trước các bước live liên quan.
- Kiểm tra các lịch/automation cũ không tiếp tục repair theo mục tiêu Windows
  direct trong thời gian cutover; thay prompt/scope chỉ qua công cụ được hỗ trợ.

**PASS:** không còn ambiguity Ubuntu/Windows cùng làm “MCP gốc”; có target,
baseline, scope và rollback packet. Thiếu credential không chặn viết code/test
fixture, nhưng chặn đúng bước live cần credential đó.

### G1 — Tunnel chính và MCP gốc hoạt động thật trên Ubuntu

**Code/deploy:** `control-plane/control_plane/{http_api,mcp_facade,store}.py`,
`deploy/`, `scripts/build-control-plane-release.py`,
`deploy/control-plane-verify-release.py`; helper/service mới chỉ khi cần.

1. Bổ sung Linux tunnel-client vào manifest/dependency receipt theo version đã
   chọn, kiểm tra executable/architecture/checksum/license; không dùng `.exe`.
2. Managed service cho **Tunnel Ubuntu**, secret file owner-only, startup order,
   backoff và stop đúng service. Root MCP chỉ expose routes cần cho RPC; UI,
   enrollment admin và secret endpoints không vô tình đi qua Tunnel. Dùng
   dedicated loopback MCP listener hoặc path allowlist được test; cấu hình
   URL kết thúc `/mcp` đơn thuần không chứng minh route isolation.
3. Root MCP hỗ trợ initialize/discovery/current contract, inventory khi mọi
   node offline, auth riêng client/controller và bounded request lifecycle.
   Chứng minh provider/client → Tunnel Linux → root truyền auth bằng cơ chế
   được hỗ trợ: dedicated audience, task/controller scope, TTL và revoke.
   Strip/reject caller-supplied identity headers; không tin header tự khai
   owner. Test missing/wrong/expired credential, wrong task/context qua ingress
   thật trước khi mở write/AI. Nếu chỉ chứng minh được static token
   `owner_default` thì gate chưa đạt, không tự hạ tiêu chuẩn xác thực.
4. Hoàn thiện async response mapping: request lâu trả handle rõ `queued`/
   `running`, client observe/cancel exact handle; không giữ một HTTP request vô
   hạn và không nói “completed” khi mới persist queue.
5. Stage ingress bằng tunnel Ubuntu riêng nếu owner chấp thuận; nếu tái dùng
   ID cũ phải dừng/fence old tunnel owner rồi mới chuyển. Không cho hai máy
   poll cùng Tunnel ID trong lúc thử vận may routing.
6. Test từ client thật qua OpenAI endpoint tới root MCP Ubuntu; đọc manifest/
   inventory và quan sát được khi Windows tắt. Tailscale curl không thay test này.

**PASS:** Tunnel Linux → root MCP có auth/discovery thật và một endpoint trung
tâm; chưa cần cho Windows chạy effect. Không đóng G1 bằng `/healthz` đơn thuần.

### G2 — Biến Windows stack thành local executor thuộc server

**Code:** `electron/services/` gồm `config.js`, `settingsStore.js`,
`runtimeOrchestrator.js`, `fullCleanActivation.js`, `activationEpoch.js`,
`recoveryHost.js`, `recoveryPlaneService.js`, `connectorAttestation.js`,
`nativeService.js`, `runtimePaths.js`; node observer/adapter, các admission
modules Python liên quan và packaged Supervisor. Không thêm runtime writer
thứ hai. `central` bên dưới là cách viết gọn của `central_executor`.

1. Tách local execution lifecycle khỏi OpenAI ingress. Ở `central` mode:
   không đòi primary/recovery Tunnel ID, Runtime API Key hoặc ChatGPT discovery
   để khởi động MCP local; không spawn tunnel-client trên node.
2. Thay bằng chứng readiness bằng **central-route proof thật**, phân lớp:
   local bootstrap/activation kiểm tra owned process/server/epoch/revision/
   contract; node online thêm enrollment + authenticated server/channel và
   nonce-bound handshake. Chỉ admission của **một action cụ thể** mới đòi
   context/root/grant/fence/expiry/generation tương ứng. Dùng cùng định nghĩa
   ở observer/heartbeat/pre-poll/action/final activation, nhưng không ép task
   grant vào bootstrap. Endpoint/contract hash đơn thuần không chứng minh
   freshness; không tự cấp quyền để thoát vòng pairing/context/approval.
3. Local MCP/executor vẫn có kiểm tra process ownership/revision; credential
   loopback riêng. Không set giả `tunnelRunning=true`, không tạo ChatGPT ACK
   giả và không bỏ guard trong Python chỉ để frontend hết đỏ.
4. Tách `local_ready`, `central_connected`, `authority_ready`, `direct_ready`.
   Node offline vẫn có thể nhận stop local/thu thập receipt; không bị hồi sinh
   trái manual-stop. Authority renew không chạy lại unknown effect.
5. Recovery Host/Supervisor local không phụ thuộc OpenAI Recovery Tunnel.
   Local health/repair/credential store giữ hoạt động; UI là client, không là
   thành phần bắt buộc của executor readiness sau khi onboarding hoàn tất.
6. Sửa lỗi hiện hữu bằng supported fresh full-clean activation/mode handoff:
   census → close/fence → quiesce exact children → snapshot → epoch mới →
   identities mới → local discovery thật → READY_COMMITTED khi vẫn đóng →
   revalidate/commit exact digest → authenticated central handshake/route
   proof mới. Epoch/receipt phải ghi role và component set; direct READY cũ
   không được dùng làm central proof. Không xóa `activation-epoch.json`, lock,
   secrets hoặc ledger, không ép sửa READY thành trạng thái khác.
7. Chọn `central` trong setup mới; giữ `direct` hiện hữu không bị tự chuyển.
   Đi/đến `direct` phải cùng thủ tục handoff, không bật hai writer song song.

**PASS:** fixture/candidate không có cả hai OpenAI Tunnel ID và không có
Runtime API Key Windows vẫn chạy local executor, kết nối central và đọc được
fixture; stop/restart/revision drift/wrong actor tiếp tục bị kiểm soát.
Sửa lỗi legacy direct có thể cần để rollback, nhưng không được biến nó thành
điều kiện buộc user dùng Tunnel Windows mãi.

### G3 — Pairing đúng máy và node chạy có giám sát

**Code:** `node_agent.py`, launcher packaged, `store.py`, `http_api.py`,
`web_ui.py`, client Electron và Supervisor resource.

1. Windows setup chỉ yêu cầu URL Ubuntu + đăng nhập/pairing + root được phép.
   Pairing code hữu hạn/một lần, approval server hiển thị đúng machine/device;
   credential node sinh local, lưu an toàn, không đưa operator token cho node.
2. Enroll **DESKTOP-63643J4** riêng; không đổi tên bản ghi DaoChienThang thành
   máy văn phòng. Bản ghi cũ giữ lịch sử và được đánh dấu stale, không auto-adopt.
3. Chốt local workspace identity rồi tạo binding/context bằng supported API.
   Có expiry, owner, generation và quyền rõ read/write/exec; path chỉ có nghĩa
   dưới node đã xác thực. Re-enrollment không kế thừa quyền máy cũ.
4. Một supervised node loop thật: heartbeat, poll, receipt replay, backoff,
   graceful shutdown, bounded output và single-instance. Mở rộng loop có giới
   hạn hiện tại, không gọi script vài lần rồi gọi là agent 24/7.
5. Windows chạy theo profile user đã đăng nhập, local stop/disable có hiệu lực;
   AtLogOn reinstall/upgrade có hash/manifest, không lạm dụng Session 0/SYSTEM.
   Không tạo task tạm mới mỗi lần cần chạy GUI.
6. Heartbeat mỗi 15s/stale sau 60s là **đề xuất cấu hình v1 để test**, không
   proof uptime. Tách node online khỏi local_ready và permission readiness.

**PASS:** office node xuất hiện đúng identity trên Ubuntu, timestamp cập nhật,
policy state trung thực; tắt agent hiển thị offline/stale và reconnect không
tạo identity/Job trùng. Onboarding hoàn tất không cần terminal hoặc key OpenAI.

### G4 — Root MCP đọc được workspace từ client thật

**Code:** `mcp_facade.py`, `http_api.py`, `store.py`, bridge CJS/Recovery và
local context/identity trong `resources/coding-tools-mcp/coding_tools_mcp/`.

1. `workspace_context` discovery/select cấp global context bất biến và map
   node-local context hợp lệ. Auth, schema/hash, annotations cập nhật đồng bộ.
2. Implement root read relay cho inventory/context và đọc fixture được phép;
   caller không tùy chọn arbitrary node endpoint, header hoặc path server.
3. Receipt ràng buộc owner/context/action/attempt/node/process/epoch/contract;
   timestamp fresh; output digest/preview do đúng node báo.
4. Test hai node cùng tên/cùng path, context user khác, expired grant, stale
   epoch và contract drift đều từ chối trước truy cập; không fallback Ubuntu.
5. Gọi qua **Tunnel trung tâm**, không dùng SSH thay tool invocation. Read
   cùng marker/hash ở Windows; Ubuntu không có bản file để trả nhầm.

**PASS:** vòng client/model → Tunnel Ubuntu → root MCP → office agent → file
Windows → receipt → client hoàn tất khi không có OpenAI Tunnel trên Windows.
Đây là lát cắt đầu tiên; chưa được báo toàn dự án xong.

### G5 — Đủ công cụ thực thi, quyền ghi, Job và dừng việc

**Đích:** tám tên `smart-v3` ở root có schema/capability thật; không giữ bảy
stub lỗi rồi quảng cáo đủ tám tool. Mapping giữ namespace node/context cho
local handles. Mỗi operation khai báo là supported phải có success/negative
tests; không chuyển mọi thứ thành generic shell endpoint.

| Tool root | Việc tối thiểu phải chạy từ server | Bảo vệ/kiểm chứng |
| --- | --- | --- |
| `workspace_context` | Chọn/đọc đúng workspace/context | Không global active workspace; stale generation bị chặn |
| `agent_workflow` | Đọc, đề xuất patch, apply/verify theo contract local | Preimage hash, scope root, review diff, outcome độc lập |
| `task_control` | Tạo/observe/pause/resume/handoff đúng RUN/WAVE; restart action có lifecycle | Không nhận queue record làm local RUN; không tự accept |
| `exec_command` | Chạy process/argv/cwd trong root được cấp | Job durable, account đúng, network/permission policy |
| `command_control` | Đọc output theo cursor, stdin nếu hợp lệ, stop exact Job | Reconcile/stop token, child quiescence, không late write |
| `request_permissions` | Xin/duyệt scope cụ thể qua client/server/local adapter | Challenge expiry/replay, CSRF, owner/root/operation binding |
| `document_workflow` | Tạo/đọc artifact được phép tại node và trả handle | Bytes/type/size/owner checks, không path tải file tùy ý |
| `view_image` | Relay ảnh/artifact từ đúng node | MIME/size/expiry/owner; không mở path Windows trên Ubuntu |

Thứ tự: read/proposal → patch một fixture → process hữu hạn → observe/stop
process dài → permissions/artifacts đầy đủ. Giữ existing local Job semantics,
không tạo job scheduler thứ hai. Action journal trước send, local effect
journal trước invocation, idempotency map tới đúng controller và context.

**PASS:** sửa một fixture có diff/proof độc lập; một process thật chạy rồi
stop được; lỗi sau effect/mất ACK chỉ replay receipt, không mutation lại;
wrong target, stale preimage, permission denied và unsupported đều trung thực.

### G6 — Server giữ phiên và điều phối AI cho các client mỏng

1. Thêm một adapter controller vào backend theo §3.4; session/turn và provider
   response IDs liên kết WorkRequest/local RUN. Không tạo canonical Goal/ledger
   cạnh tranh và không auto-handoff một RUN đang thuộc controller khác.
2. User gửi yêu cầu tự nhiên từ app Windows/web; server chọn context đã được
   user xác nhận, gọi model và dispatch qua **cùng root MCP/action path G4–G5**.
   Không đường shell bí mật ngoài journal để làm demo.
   Root MCP credential phải được bind server-side với principal/task/context/
   expiry, không tin model truyền owner/scope trong args. Tool call ID được
   map một lần tới action; `request_permissions` không tự duyệt và
   `agent_workflow` không được gọi lồng suy luận vô hạn.
3. Một controller lease/generation cho mỗi RUN; cloud client trực tiếp và server
   controller muốn tiếp quản phải supported handoff. Không fork cùng yêu cầu
   thành hai RUN ghi cùng workspace để né tranh chấp.
4. Thiết lập ngân sách/expiry/max steps/no-progress; không tự tăng. Stop từ UI
   dừng turn mới, fence dispatch mới và điều khiển exact active Job nếu được
   phép; trạng thái chờ Job terminal phải được hiển thị.
5. Browser đóng có thể để tác vụ tiếp tục hữu hạn ở server; mất node thì chờ,
   không model polling liên tục. Reconnect tải lại session/Job cũ; server restart
   reconcile provider/tool/action trước khi tiếp tục, không resend blind.
6. Usage nếu có phải provider-reported; missing không là zero. Tắt model route
   không ảnh hưởng khả năng xem log/stop/revoke. Không đổi `execution_route=auto`
   sang route/model đắt tiền chỉ vì server có credential.
7. Data gửi model có phạm vi được chấp thuận; secrets excluded. Output của
   model không tự là permission, effect proof hoặc acceptance cuối.

**PASS:** từ Windows client không giữ API key, gửi một yêu cầu sửa fixture;
server tạo kế hoạch, xin quyền cần thiết, sửa/test đúng Windows và trả diff.
Đóng/mở client thấy cùng task; hết ngân sách/revoke dừng đúng. Đây là gate bắt
buộc cho trải nghiệm “client dùng đầu não server”, không thay bằng curl demo.

### G7 — UI để người dùng tự vận hành, không cần vòng sửa bằng SSH

**Server UI** phải có:

- Server: root MCP/Tunnel/OpenAI auth/DB/backup/build, maintenance và tuổi đo.
- Devices: machine/device ID, OS, online/local_ready/permissions, workspace,
  bản installed/loaded; node stale khác node sai identity.
- Tasks: đúng máy/root/controller, saved/queued/dispatched/running/unknown/
  failed/completed/awaiting-review; progress từ receipt, không % suy đoán.
- Approval: exact target/files/command/scope/expiry, ai duyệt và việc gì đang
  chờ; không expose loopback consent endpoint qua proxy như thao tác local.
- Controls: pause intake, cancel never-sent, stop Job, revoke node và retry
  chỉ khi an toàn. Mỗi nút mô tả đúng effect và trạng thái xác nhận.
- Result: diff, test exit/output bounded, artifact, independent review và
  lỗi có reason/actionable next step; không chỉ thông báo UPDATE_INCOMPLETE.

**Client/node UI** phải có: URL server/pairing, root được chia sẻ, task đang
chạy trên máy này, local pause/revoke, installed/loaded version. Central mode
ẩn các trường Runtime API Key/Tunnel ID của Windows và hiển thị “Được quản lý
bởi Ubuntu”; direct/recovery cloud route nếu giữ chỉ nằm trong quản trị nâng
cao, không là lỗi bắt người dùng tự xử lý.

Sửa cụ thể renderer đang gán mọi `updateIncomplete` thành “Đang hoàn tất
activation epoch”: epoch blocked, stopped, offline, credential missing và
contract mismatch phải có nhãn riêng. UI không gợi nhập key khi presence=true.

**PASS:** walkthrough trên Windows thật + browser Ubuntu bằng click: pair →
select root → send task → approval → xem kết quả → stop → reconnect. Secret
không ở DOM/log/export; keyboard và layout cửa sổ nhỏ dùng được. Test HTTP
login/logout trước đây không thay proof browser rendering/hành trình người dùng.

### G8 — Offline, rollback và vận hành 24/7

- Intent khi node offline giữ scope/TTL, không đóng dấu đang chạy; trước
  dispatch revalidate. Intent expired/canceled không chạy khi node quay lại.
- Fault fixtures cover crash tại durable boundaries, response loss, node
  restart, central restart, contract update, revoke/cancel race và DB đầy/busy.
  Không chèn fault vào máy đang làm việc nếu chưa có cửa sổ riêng.
- Tách liveness/process, DB integrity, durability, expected maintenance mode,
  cloud ingress, node readiness và action outcome. Healthcheck bảo trì PASS
  có nghĩa “bảo trì đúng kế hoạch”, không “được phép thực thi”. Mode drift vẫn
  phải cảnh báo; không derive expected mode bằng cách luôn tin live response.
- Snapshot nhất quán, retention/ACL/disk-alert; off-host encrypted backup có
  destination và recovery-key owner được chọn trước. Không tự upload vào cloud
  hoặc PC khác chưa được chỉ định. Restore cô lập rồi reconcile trước reopen.
- Rollback: close intake → node fence → reconcile → stop/quiesce exact jobs →
  compatible binary/contract → mới handoff. DB rollback không đi kèm binary
  rollback mặc định; không xóa changes, ledger hoặc secret store.
- Sau fault/rollout cuối mới bắt đầu **24 giờ soak liên tục** của exact build:
  theo dõi process instances, restart history, node heartbeat, backup freshness,
  queue/unknown/duplicate effect. Fault drill tách window; nếu restart/redeploy
  thì ghi rebase, không cộng đủ 24h từ nhiều build.

**PASS:** action lineage không mất/không lặp effect trong ma trận thử; stop và
manual-stop có hiệu lực; restore có proof; 24h đúng build và còn biết rõ single
server là điểm lỗi đơn. Không gọi đây HA/SLA tuyệt đối.

### G9 — Đóng gói, triển khai, bỏ phụ thuộc Windows Tunnel và bàn giao

**G9a:** bước 1–6 tạo/cài candidate và cutover trước G8. Sau mọi fault/rollback
test, chọn exact final build rồi mới chạy soak G8. **G9b:** bước 7–8 và checklist
cuối sau G8; nếu G9b thay source/runtime bytes thì quay lại validation và soak
của build mới, không dùng receipts build trước.

1. Build Ubuntu release chứa root MCP/controller/UI + unit templates + manifest
   và Tunnel binary/dependency identity; DB/secrets ngoài archive. Verify bytes
   tại đích trước activation; immutable current symlink không trỏ checkout.
2. Build NSIS node/client mới; manifest bao gồm agent, execution resources,
   supported modes/contracts, build source/version/hash. Linux node package
   riêng khi đưa Linux vào phạm vi; không chỉ đổi tên binary Windows.
3. Chạy fresh-install fixture và **upgrade đúng bản 1.0.0 đang cài** có config/
   identity/ledger/dirty workspace/Scheduled Task preservation. Harness
   installed-smoke cũ không phải upgrade test và không được chạy uninstall
   trên profile Admin hiện có sản phẩm đã cài.
4. Migrate office một node: close/fence → verify backup/quiescence → upgrade →
   refresh packaged Supervisor đúng executable → central-route activation →
   receipt mới. Không dùng `npm dev:status` để đánh giá app packaged.
5. Nghiệm thu có Windows primary **và recovery** OpenAI Tunnel ngừng chạy,
   credentials không được central mode sử dụng. Giữ vật liệu rollback an toàn;
   không tự xóa/rotate credentials của user.
6. Thêm node thứ hai bằng cùng onboarding; không thay Tunnel/server code để
   thêm mỗi PC. Nếu chưa có node thật thứ hai, wrong-target fixture có thể pass
   nhưng claim multi-device live vẫn chưa đóng.
7. Source/evidence delivery trước mọi commit/push theo AGENTS; xác minh remote
   HEAD và tải/kiểm checksum artifacts sau delivery. Không tag/public release
   hoặc force push nếu chưa được giao đích đó.
8. Hướng dẫn cuối phải đủ: cài client, pair/root, gửi việc, duyệt, dừng, đọc lỗi,
   backup/restore và rollback. User không cần nhập PowerShell nhiều lần để vận
   hành bình thường. Lập bảng phần supported/unsupported có bằng chứng.

**PASS cuối:** hoàn thành toàn bộ checklist §8; không dùng “installer pass”
để bỏ qua AI/controller, root MCP relay hoặc central-only E2E.

## 6. Ma trận nghiệm thu bắt buộc

Tất cả ca dưới đây là **PLANNED cho kiến trúc mới**, không mượn PASS cũ.

| ID | Thử nghiệm | Bằng chứng đạt |
| --- | --- | --- |
| A01 | Tất cả node offline | Root MCP/Tunnel/UI Ubuntu vẫn trả inventory có timestamp |
| A02 | Cloud client thật gọi root qua Tunnel Ubuntu | Discovery đúng schema/hash; authenticated RPC tới đúng root |
| A03 | Windows không có runtime key/primary/recovery tunnel | Executor central hoạt động; không spawn cloud tunnel |
| A04 | Pair office mới, có DaoChienThang cũ | Hai identity riêng; không nhận nhầm quyền máy cũ |
| A05 | Read file chỉ có trên Windows | Bytes/digest đúng node; server không đọc file local giả thay |
| A06 | Hai máy có cùng path + context user khác | Cross-device/cross-owner từ chối trước effect |
| A07 | Contract/process/epoch/generation drift | Invalidate freshness; không dùng cached READY để dispatch |
| A08 | Một patch có expected preimage | Diff/test đúng root; concurrent edit bị từ chối, không overwrite |
| A09 | Cùng action/key replay; key đổi args/target | Một effect hoặc conflict; không tạo RUN/Job mới |
| A10 | Crash/mất ACK tại từng commit/send/effect boundary | Cùng action được reconcile; unknown giữ unknown |
| A11 | Long Job + stop + child process | Exact handle terminal/quiescent; không late write sau stop xác nhận |
| A12 | Revoke/expiry/cancel đua với dispatch | Không effect ngoài grant; late receipt được giữ, không cấp lại quyền |
| A13 | Direct/central và hai controller cùng ghi | Chỉ một writer; handoff cần quiescence |
| A14 | Offline queue/reconnect/server restart | Giữ intent/context/task đúng ID; expired/canceled không chạy |
| A15 | Manual stop/logout/close UI | Tôn trọng stop; hỗ trợ keep-running có proof, không tự suy no-login |
| A16 | Terminal READY cũ → central-mode activation mới | Không sửa/xóa history; identities/proof mới khớp, recovery không loop |
| A17 | Root đủ tám tool/capability | Các operation được hỗ trợ thật; no generic-shell bypass/no stub overclaim |
| A18 | Artifact/document/image | Owner/node/handle/MIME/size/expiry đúng, không arbitrary server path |
| A19 | Thin client gửi yêu cầu AI, đóng/mở UI | Same task/turn; effect qua root MCP; provider secret chỉ server |
| A20 | Budget/no-progress/revoke/mất controller | Dừng đúng boundary; không tự tăng ngân sách hoặc đổi owner |
| A21 | UI/operator login và quyền | CSRF/session expiry/replay/wrong owner bị chặn; không rò secret |
| A22 | Maintenance và hỏng thật | Recovery được phân loại đúng; disk/DB/tunnel lỗi thật không bị giấu |
| A23 | Backup encrypted/off-host + restore | Decrypt/restore được bằng recovery key đúng; reconcile trước reopen |
| A24 | Upgrade/rollback package | Settings/identity/ledger/jobs/files giữ đúng, old actor bị fence |
| A25 | Node/OS thứ hai | Package/lifecycle/file/job proof trên máy thật; support matrix trung thực |
| A26 | 24 giờ sau rollout/fault cuối | Exact build, timers/heartbeats/receipts; không unknown chưa giải thích |
| A27 | Task tự nhiên do người dùng chọn | Kết quả hữu ích được kiểm độc lập; model nói xong không đủ |

Đối chiếu toàn bộ ma trận gốc: T01–T04 → A06/A07; T05–T09 → A09/A10/A14;
T10–T12 → A07/A11/A12/A13; T13–T14 → A22/A23; T15–T17 → A03/A07/A15/A16;
T20–T22 → A18/A20/A27; T24 → A13/A24. T18 (no-login), T19 (WOL), T23 (Ubuntu
execution workspace) giữ là nhánh tách riêng, chưa được user giao chi tiết
trong đích hiện tại; không báo đạt hoặc dùng chúng để tự chuyển nơi thực thi.

Mỗi ca lưu exact source/build/contract, UTC window, target/action/context
references đã sanitize, oracle expected/actual, PASS/FAIL/INCONCLUSIVE, final
job/authority state. Receipt có nội dung nhạy cảm giữ tại nơi có ACL; Git giữ
evidence đã redaction, tuân thủ retention `.coding-tools` và dừng nếu có secret.

## 7. Validation, deliverables và cách tránh triển khai vòng quanh

### Các lane có sẵn để mở rộng

- Python central: `control-plane/tests/test_store.py`, `test_http_api.py`,
  `test_deployment_verifier.py`, `test_release_artifact.py`.
- Adapter: `control-plane/tests/recovery_runtime_adapter.test.cjs`,
  `recovery_identity_observer.test.cjs`, `recovery_read_only_bridge.test.cjs`.
- Lifecycle: `tests/runtime-lifecycle.test.js`, `activation-epoch.test.js`,
  `full-clean-activation.test.js`, `recovery-host.test.js`,
  `recovery-bootstrap.test.js`, `recovery-supervisor.test.js`.
- Authority/bridge: `tests/control-plane-bridge-runtime.test.js`,
  `control-plane-read-only-bridge.test.js`; Python local
  `test_workspace_session_isolation.py`, `test_controller_continuity.py`,
  `test_activation_epoch.py`, `test_run_continuation.py`, `test_goal_pursuit.py`.
- Test mới chỉ thêm cho boundary chưa có: root relay/context/handles,
  central-mode activation, controller/budget, node managed lifecycle,
  UI workflow, upgrade preservation và Tunnel Linux integration.

Trong implementation dùng smallest affected test/name. Tại release, thay đổi
này cắt qua lifecycle/transport/authority nên cần Windows `npm run dist`,
`npm run test:recovery:e2e`, packaged smoke, isolated install **và** upgrade
test riêng. Ubuntu `npm run dist:control-plane` + extracted verifier/launch/
health/backup proof. Không chạy full suites cho riêng tài liệu này.

Trước mọi commit/push khi được giao delivery:

```text
npm run stage:coding-tools-delivery
npm run check:coding-tools-delivery
```

Chốt release bằng exact bytes, không rebuild ngầm sau test; bytes thay đổi thì
invalidated proof đúng boundary. Preserve mọi `.coding-tools` trừ hai sidecar
được phép; không dùng Git commit liên tục để đuổi theo telemetry.

**Artifacts phải bàn giao:** source + contract/migration tests; Ubuntu archive
và tunnel dependency manifest; Windows node/client installer + hash/signature
state; node2 package receipt; central/node API capability table; pairing/operate/
recovery runbook; A01–A27 evidence index; known limits; Git/local/remote/build
identity rõ ràng. Public release/signing certificate là quyết định riêng.

## 8. Definition of Done — không đổi nghĩa của “xong”

- [ ] Tunnel chính và MCP gốc thực sự chạy trên Ubuntu, client thật dùng được.
- [ ] Windows chỉ cần server URL/pairing/root; không cần key/Tunnel OpenAI riêng.
- [ ] Local executor central không lệ thuộc cả primary lẫn recovery cloud tunnel.
- [ ] Có server-owned AI session cho client mỏng, model auth/budget hợp lệ.
- [ ] Đọc, sửa, verify, chạy process và dừng đúng Job qua root MCP hoạt động thật.
- [ ] UI cho thấy đúng máy/workspace/task, trạng thái chờ/lỗi và quyền đang cấp.
- [ ] Tám tool root có capability/operation parity đã kiểm, không che stub bằng tên.
- [ ] Offline/reconnect/duplicate/unknown effect/expiry/rollback được nghiệm thu.
- [ ] Office + node thứ hai không nhầm đích; không overclaim OS chưa thử.
- [ ] Nâng cấp/bảo toàn dữ liệu, backup/restore và 24h soak đúng build có proof.
- [ ] Một tác vụ thực tế được người dùng xem kết quả và xác nhận đạt yêu cầu.
- [ ] Hướng dẫn vận hành đủ, các phần chưa hỗ trợ ghi rõ; source/evidence/artifact
      được đồng bộ đúng destination khi được giao delivery.

### 8.1 Completion audit hiện tại (16-09-2026)

| Tiêu chí | Bằng chứng mạnh nhất hiện có | Kết luận / gate kế tiếp |
| --- | --- | --- |
| Root Tunnel/MCP Ubuntu | `codex-control-plane.service` active: root MCP chỉ bind loopback `127.0.0.1:8766` (anonymous POST `403`), Tailnet Console `:8765/mcp` trả `404`; `tunnel-client v0.0.14` Linux đã verify checksum và cài private, nhưng profile/Tunnel ID chưa có | **Chưa đạt primary Tunnel**; cần Tunnel OpenAI mới/được chuyển chính thức, runtime credential local, profile HTTP tới `127.0.0.1:8766/mcp`, `doctor`, rồi client thật |
| Windows không cần key/Tunnel | Candidate `9cc2d96` đã build/cài trên `DESKTOP-63643J4`; focused Windows Electron/recovery suite 113/113 pass, `app.asar` installed khớp candidate, Supervisor packaged healthy | **Chưa central live**; phải chạy nút full-clean handoff, sau đó pair/bind/context/policy Ubuntu thật |
| Executor central không cloud Tunnel | Runtime/lifecycle/supervisor source + packaged agent đã có; Supervisor office báo `waiting_for_pairing`, không spawn agent | **Chưa đạt**; role Windows vẫn chưa handoff nên chưa có bằng chứng central startup không Tunnel trên office |
| Server-owned AI/controller | Chỉ có plan/contract; chưa có provider/model/budget/lease adapter | **Chưa bắt đầu**; cần quyết định provider, consent dữ liệu và budget |
| Read/write/process/stop | Một relay `workspace_context` read-only có source proof | **Chưa đạt**; bảy tool và Job lifecycle thực chưa có |
| UI vận hành | Ubuntu private Console active; Windows Command Center candidate đã cài và có nút handoff được manager-IPC fence | **Một phần packaged**, chưa click handoff/pair/E2E đúng UI interactive |
| Eight-tool parity | Tám tên công khai, chỉ một lane relay read-only | **Chưa đạt**; không xem discovery là capability parity |
| Fault/offline/rollback | Một số source fixtures, SQLite backup/health source proof | **Chưa nghiệm thu** trên package/node thật |
| Multi-node đúng đích | Registry live chỉ có node cũ + enrollment pending; office chưa onboarding thật | **Chưa đạt** |
| Upgrade/backup/soak | Ubuntu verified release/SQLite snapshot trước deployment; Windows upgrade cài cùng user và Supervisor được reinstall, heartbeat healthy | **Chưa đạt**; không có rollback exercise hay 24h soak |
| Tác vụ người dùng thật | Không có action/receipt live | **Chưa đạt** |
| Delivery/runbook | `main@9cc2d96` đã push GitHub; delivery/secret guard pass trước push; candidate installer SHA-256 và unsigned state đã xác minh | **Một phần delivery**; chưa có tagged/public release, tunnel/agent E2E hay walkthrough vận hành |

G4 chỉ là mốc đọc thử; G5 chỉ là technical execution; **không đóng mục tiêu
tổng thể trước G6–G9 và checklist này**. Nếu external credential/hardware chưa
sẵn sàng, ghi rõ gate chưa đạt thay vì đổi mục tiêu thành phần dễ làm hơn.

### 8.2 Receipt rollout hiện tại — chưa phải nghiệm thu kiến trúc (16-09-2026)

Wave này đã push `main@9cc2d96025a40bc2f2b49f52626ed8170281d169`, xây và cài
candidate Windows từ source archive đã verify. Installer SHA-256 là
`f32bbdc23455b41860f31dd317506694318c0289f52842b2ae7d8b8042ce7a9c` và vẫn
`NotSigned`, đúng như installer 1.0.0 trước đó; `node-agent.cmd` bundled và
`app.asar` đã cài khớp bytes candidate. Không đọc/đổi Runtime API Key hoặc
Tunnel ID Windows.

Supervisor trên office đã được reinstall đúng executable candidate vì manifest
cũ chủ động từ chối executable identity đổi. Sau replacement, scheduled task
`WebMCP Recovery Supervisor` `Running`/`healthy`, còn control-plane agent ở
`waiting_for_pairing`; đó là trạng thái mong đợi trước handoff, không phải route
Ubuntu đã sẵn sàng.

Ubuntu có OpenAI `tunnel-client v0.0.14` lấy từ release chính thức, archive
SHA-256 `15bd17e805cad39d412199115bb9e10a978dd35258a114cdf25dd2ae6681c7d3`.
Binary mới chỉ được cài private; không có profile, Runtime credential, systemd
Tunnel unit hay OpenAI-hosted Tunnel đang chạy. Không mở admission `recovery`.

## 9. Việc cần từ người dùng — đúng lúc, không xin lại điều đã chốt

### Sửa lỗi handoff được người dùng tái hiện — 16-09-2026

Baseline sửa lỗi `main@8b7a82d`: ảnh Windows và RPC read-only xác nhận
`direct_legacy`, MCP/Tunnel chính OFF, Supervisor healthy. Closure có
`ACTIVATABLE` nhưng `affected_components=[]`: nó không phải checkpoint kích
hoạt code. Nút mới ở `9cc2d96` đã nối nhầm tới accepted-code restart; test tĩnh
UI trước đó chỉ chứng minh wiring, chưa chứng minh thao tác thật.

Source repair tách riêng migration do operator yêu cầu, vẫn giữ hai census
ledger, exclusive gate, fence/owned stop, epoch/profile bất biến và kiểm chứng
trước admission. Code activation thường vẫn đòi đúng checkpoint; trộn tham số
code/soft restart/acceptance override vào migration bị từ chối. UI không đưa
receipt HANDOFF vào renderer snapshot hay báo đã kết nối, và có retry cho
epoch thất bại/hết hạn sau khi pairing.

Đã sửa thêm ba lỗi trong cùng đường đi: final census central phụ thuộc ngược
vào READY của chính nó; proof thiếu `all_components_same_epoch`; adoption/
supervision Recovery vẫn áp hợp đồng Tunnel trực tiếp cho central. Test mới
đi qua census thật → READY_COMMITTED → revalidate → READY, đồng thời giữ CLOSED
khi route thiếu/cũ/sai device, policy hết hạn hoặc Tunnel local còn chạy.

Rollout exact candidate và kết quả live sẽ được ghi riêng sau kiểm thử Windows;
không dùng source tests làm bằng chứng đã pair hay đã có Tunnel Ubuntu.

Checkpoint live sau sửa lỗi (16-09-2026, khoảng 22:05 +07): candidate
`d9b71c3` đã push/build/cài trên office; installer SHA-256
`5ad53eb4c343000c487da678242056dae70aa8643bde2460f3b4dd4b113d0b83`, unsigned.
Kho secret mã hóa được kiểm digest trước/sau và giữ nguyên, snapshot các file
cấu hình/identity/epoch trước upgrade nằm trong profile riêng ngoài repository.
Không sửa checkout `E:\DEV\Codex-web` hoặc xóa ledger.

Kiểm chứng Windows: 864/865 Node tests pass ở lần chạy đồng thời; một fixture
expiry dùng thời gian thật hết hạn ngay khi dựng dữ liệu, retry riêng pass 1/1.
Recovery real-process 3/3 và packaged smoke pass; smoke không đổi production
descriptor/Scheduled Task. Test mới của nút handoff chạy handler thật với closure
absent/non-code và kiểm không báo thành công khi mới nhận HANDOFF.

Handoff live qua Recovery IPC đã tạo epoch mới, persist `central_executor`,
spawn local MCP và không spawn primary Tunnel. Đã enroll đúng device office
`ac251d4f-304a-4f06-885c-a9aea1f2a13a`, duyệt identity, tạo binding
`office_codex_web` cho workspace hiện tại và context/policy metadata read-only
24 giờ (không cấp ghi/exec). Sau heartbeat thật, Windows đạt
`READY/OPEN`, `fullyReady/localReady/centralConnected/authorityReady=true`,
central census pass. Ubuntu global admission vẫn `recovery`.

Kiểm tra bền vững phát hiện lỗi tiếp theo: Supervisor PowerShell dùng `$host`
(trùng biến hệ thống `$Host` read-only) khi đọc origin của policy, nên báo
`cycle_error` sau pairing. Đã tái hiện qua chính helper cài trên Windows với
`VariableNotWritable`; kết nối một-shot ở trên chưa phải heartbeat bền vững.
Hotfix và postflight dài hơn TTL heartbeat phải đóng điểm này trước handoff cuối.
`npm audit --omit=dev` còn advisory high cho `js-yaml` có sẵn; không trộn upgrade
dependency ngoài phạm vi vào bản sửa migration này.

Đã chốt: Ubuntu `svhome` là server; Tunnel/MCP gốc ở server; Windows office
là node đầu; có UI; không bắt node tự cấu hình OpenAI; installer unsigned cũ
đã được cho phép cài. Không hỏi lại các quyết định này.

Trước live phase cần:

1. **G1:** cấp credential/runtime Tunnel cho Ubuntu bằng kênh local an toàn;
   chọn endpoint trung tâm mới hoặc explicit chuyển ID cũ. Không gửi key vào chat.
2. **G3/G5:** chọn root pilot và phạm vi read/write/exec; quyền data gửi model.
3. **G6:** chốt provider/account/model và giới hạn chi phí/thời gian cho server
   controller. API proposal không tự có quyền dùng tiền/tài khoản của user.
4. **G8:** chọn nơi backup off-host + người giữ recovery key.
5. **G9:** lịch upgrade/logon/fault trên office, node thật thứ hai và policy ký
   candidate mới; xác nhận unsigned cũ không phải chấp nhận mọi binary tương lai.

Không cần tất cả câu trả lời mới viết code fixture; chỉ dừng tại effect cần
đúng quyền đó. Công việc bắt đầu tiếp theo là G0 contract/baseline và test đỏ
cho central mode không có Windows Tunnel, **không phải nhập lại Windows key**.

## 10. Quan hệ với tài liệu cũ và checkpoint lượt lập kế hoạch

- Giữ nguyên bản nghiên cứu 15/09 làm chronology; kế hoạch này cụ thể hóa
  yêu cầu làm rõ ngày 16/09, đưa P4 và controller server vào đích cần bàn giao.
- [Completion plan cũ](UBUNTU_24X7_COMPLETION_PLAN.md) và
  [packaging/pilot plan cũ](CONTROL_PLANE_PACKAGING_AND_PILOT_PLAN.md) vẫn có
  giá trị chứng cứ/test, nhưng RC-A/RC-B loại trừ primary cutover không còn là
  Definition of Done cho yêu cầu hiện tại.
- [Implementation status](CONTROL_PLANE_IMPLEMENTATION_STATUS.md) là lịch sử
  deployment; đoạn “Windows chưa cài” tại checkpoint 15:25 đã bị sự kiện cài
  sau đó thay thế. Audit §2 ở đây là baseline kế hoạch, không sửa lịch sử cũ.
- Lượt này: đọc đầy đủ tài liệu gốc, audit code và tài liệu OpenAI, viết kế
  hoạch. Không đổi secret, admission, process, Scheduled Task hoặc tunnel;
  không chạy model, install/restart, broad test, commit/push/tag/release.
  Ubuntu vẫn recovery; final new-build acceptance chưa có. Goal không complete.
