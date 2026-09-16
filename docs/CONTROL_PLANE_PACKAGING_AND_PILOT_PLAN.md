# Kế hoạch đóng gói, UI kiểm soát và chạy thử Ubuntu → Windows

Ngày lập: **16-09-2026**. Source baseline: `main@b57ab92325560070e290a90dd5788f61313afb2d`.

**Trạng thái triển khai (16-09-2026):** W1 đã có source + focused proof: idle
handoff chặn UI pending và revalidate ở boundary; deadline IPC là một ngân sách
chung; identity CJS→Python giữ `observation_kind`. W2 đã có source + focused
proof cho adapter packaged: Python/Electron bundled launcher, installed-path
identity/status/read-only bridge và package manifest/verifier. W3 có source +
focused HTTP proof cho UI same-origin: session in-memory, redacted overview,
CSRF/Origin, approval enrollment identity-only, admission control, action/receipt
lifecycle không payload, policy observation redacted và fixed browser read-only
canary; chưa có browser/HTTPS proof thật. W4 có source policy provisioning
packaged, nhưng chưa có Electron onboarding, actual enrollment hay canary. Sau
transfer Git bundle có kiểm tra hash, Windows candidate `main@e0b5bbd…` đã chạy
focused package verifier `8/8`, Electron Builder NSIS thành công và packaged
Recovery smoke thành công. Installer có SHA-256 được ghi bên dưới nhưng trạng
thái Authenticode là `NotSigned`, nên không được cài lên office node. Ubuntu
artifact versioned source đã build có manifest/hash, nhưng service vẫn chạy
revision/schema cũ; SSH deploy bị từ chối public-key, vì thế chưa restart
Ubuntu/Windows, chưa mở ingress, chưa gửi dữ liệu ra ngoài hay publish release.
W4–W8 và RC-A/RC-B vẫn chưa đạt; W3 chỉ được đóng sau evidence
HTTPS/browser thật và telemetry/local-observation contract. Phải xác nhận lại
target, quyền thao tác và trạng thái đang chạy trước effect thật.

**Cập nhật validation (16-09-2026, source worktree hiện tại):** focused Python
cho HTTP UI đạt `20/20`, store/node-agent + cross-language policy digest đạt
`56/56`; deployment-health verifier đạt `4/4`; focused Node cho recovery/adapter/bridge đạt `80/80`; verifier bundle
đạt `8/8`. `npm run test:recovery:packaged` đã tạo `dist/linux-unpacked` và
exact-resource verifier xác nhận đúng năm adapter resource; smoke chủ động
`skip` vì chỉ có ý nghĩa trên Windows. `npm test` trên Ubuntu không phải release gate xanh:
`691 pass / 23 fail / 53 cancelled / 15 skipped`. Một phần lỗi là môi trường
Ubuntu không có executable/hành vi Windows (`python`, `where.exe`, `netstat.exe`,
đường dẫn Windows); phần còn lại gồm assertion supervisor/MCP/workspace. Chúng
phải được tái lập và phân loại trên Windows candidate sạch trước W5; không đổi
oracle để làm xanh trên Ubuntu.

**Windows candidate proof (16-09-2026):** `npm run dist` tại
`main@1f585b9…` đã chạy hết test lane (Python `1158/1158` pass trong 29 phút
03 giây) rồi phát hiện verifier after-pack tự mâu thuẫn: adapter
`resources/control-plane` bị so với source root `resources`. Sửa `0e07395…`
giữ hai phép kiểm byte-exact riêng: tree `resources` và đúng năm tệp adapter.
Trên `main@e0b5bbd…`, focused verifier đạt `8/8`; `electron-builder --win nsis`
thành công; `node scripts/packaged-recovery-smoke.js` đạt `ok:true` với 13
resource bắt buộc, isolated user-data, Recovery host/MCP healthy và Supervisor
fail-closed. `node scripts/installed-recovery-smoke.js` sau đó cài đúng
installer vào scratch path, xác nhận registration tạm, chạy cùng packaged
smoke, gỡ file/registration với exit `0`, và chứng minh production Recovery
descriptor/Scheduled Task không đổi. Artifact là
`coding-tools-mcp-setup-1.0.0.exe`, `121767504` bytes, SHA-256
`ab376d7b9f1517cc0077d1d7213b874236a4fb5a85148c089d7cec74f750cb54`.
`Get-AuthenticodeSignature` trả `NotSigned`; đây là candidate đã build và có
isolated-install smoke, không phải office upgrade, published hay signed release
proof.

**Fingerprint ứng viên Ubuntu (worktree dirty, chưa triển khai):**
`sha256:4bef62162e8a5ccc6de136dbabd2079d5c605a8bbf130aabf48de67655880040`
từ `python3 -m control_plane.maintenance package-fingerprint`. Nó chỉ là mốc
byte của các module control-plane cho lần đóng gói/deploy kế tiếp; không được
đặt vào service environment hay dùng để suy ra runtime live đã cập nhật.

**Baseline Windows qua SSH (16-09-2026):** xác minh `Admin@DESKTOP-63643J4`
qua Tailnet, Node `24.19.0`, npm `11.14.1`, Python `3.11.7`; checkout sạch
`E:\\DEV\\Codex-web` là `main@b57ab92…`. Node suite của baseline có đúng một
lỗi `recovery-plane.test.js`: child Recovery MCP không mở một port ephemeral
trong lần chạy full song song. Port rảnh sau test và cùng test chạy riêng đạt
`1/1` trong 1.8s, nên đây là flake/parallelism candidate, chưa được phép gọi
full suite xanh. Candidate W1–W4 đã được chuyển qua Git bundle có SHA-256 khớp
và fast-forward đến `main@e0b5bbd…`; không thay credential/remote GitHub. Khi
giới hạn Node test concurrency là `4`, toàn bộ Node suite, `source root clean`
và secret check của baseline đã pass; script `npm test` của source hiện tại dùng
cùng giới hạn để giữ gate lặp lại được. Package proof của candidate được ghi ở
phần validation trên; chỉ focused verifier được chạy lại sau fix vì Python
test lane không đổi kể từ lượt `1158/1158` pass.

**Recheck live chỉ-đọc (16-09-2026):** `codex-control-plane.service` trên
Ubuntu đang `active`, có health SQLite `ok`, nhưng service đang chạy revision
`000938f…`, khác source `e0b5bbd…` và khác source worktree hiện có. Central
hiện có 1 node/enrollment request nhưng 0 binding, context, work request,
action, receipt và read-only intent; Tailscale chưa có Serve/Funnel config.
Như vậy UI/package source mới **chưa** được triển khai hoặc chạy live. Không
restart service, không đổi ingress và không thao tác Windows trong recheck này.

Kế hoạch này cụ thể hóa phần đóng gói/UI/pilot của
[kế hoạch hoàn thiện](UBUNTU_24X7_COMPLETION_PLAN.md), dùng
[trạng thái triển khai](CONTROL_PLANE_IMPLEMENTATION_STATUS.md),
[release checklist](RELEASE_CHECKLIST.md) và
[runbook khôi phục](CONTROL_PLANE_RECOVERY_RUNBOOK.md). Không sửa lịch sử trong
`docs/research/`; không dùng các checkpoint cũ như trạng thái live hiện tại.

## 1. Kết quả phải bàn giao

Người vận hành mở một trang Web riêng tư trên Ubuntu và trả lời được:

1. Ubuntu còn hoạt động không; backup, DB và admission có an toàn không?
2. Máy Windows nào online, máy nào thực sự sẵn sàng nhận việc, vì sao bị chặn?
3. Đang chạy việc gì, trên đúng workspace nào, tiến độ nào đã được node xác nhận?
4. Làm thế nào ngừng cấp việc mới, hủy việc chưa gửi, dừng đúng job đang chạy?
5. Máy đang chạy build nào, bản cài đặt nào, bản mới đã được nạp chưa?
6. Khi lỗi/mất mạng, việc nào đã xong, việc nào chưa rõ kết quả, cách đối soát?

Chia giao hàng thành hai mốc hữu hạn, không gọi mốc đầu là hoàn tất cả hệ thống:

| Mốc | Phải có | Chưa được tuyên bố |
| --- | --- | --- |
| **RC-A — packaged read-only pilot** | Ubuntu Web UI dùng dữ liệu thật; Windows cài từ NSIS có node adapter; enrollment/policy/binding đúng; một canary chỉ đọc đi trọn đường; UI đóng admission/hủy việc chưa gửi được | Điều khiển/sửa code từ xa tổng quát; dừng mọi job; mutation; production 24/7 |
| **RC-B — controlled execution pilot** | RC-A + một workflow ghi được cho phép, kết quả kiểm tra độc lập, stop/fence/replay/reconnect/rollback; backup ngoài máy có mã hóa, restore có đối soát, observation 24 giờ sau triển khai cuối | WOL; Windows chưa login vẫn chạy; AI tự làm vô hạn; HA; thay primary tunnel; public release nếu chưa được giao |

UI giám sát là hạng mục bắt buộc **trước khi chạy thử thật**, không để cuối dự án.

## 2. Baseline và các khoảng trống đã xác định

### Fresh read-only recheck — 16-09-2026 (sau source W4, trước deploy)

- Ubuntu user service `codex-control-plane.service` đang `active/running`, PID
  `233866`, bind `100.116.112.22:8765`, `NRestarts=1`; backup và healthcheck
  timers đều active. Đây là state process hiện tại, không phải new deployment
  proof.
- `/healthz` trả SQLite `ok`, schema `7`, admission `open`, 1 node và 1
  enrollment request, nhưng binding/context/work request/action/receipt đều
  `0`. Không có product canary hoặc local execution được suy ra từ các count.
- Runtime đang nạp declared revision `000938f401b6d6605b0b94474cbc87b5171c2909`
  và package fingerprint `sha256:3f247e44c1b25658eb3bad2af313d13c7ec73ac250569e93a77463ba8aef64a9`;
  nó không phải checkout/source W1–W4 đang sửa trong lượt này. Không restart để
  nạp working tree dirty.
- MagicDNS của host là `svhome.tail0e4032.ts.net`; `tailscale serve status` và
  `tailscale funnel status` đều “No serve config”. Service không listen
  `127.0.0.1:8765`, vì vậy HTTPS Tailnet phải được thiết kế với upstream exact
  `100.116.112.22:8765` (hoặc thay bind qua controlled deployment), không giả
  định proxy localhost hoạt động.

Live snapshot gần nhất thuộc lượt đánh giá **16-09-2026 10:54–10:57 +07**,
không phải một probe mới của lượt lập kế hoạch này:

**Recheck chỉ-đọc sau source schema 8 (16-09-2026):** Windows office node
`DESKTOP-63643J4` vẫn sạch ở `main@b57ab923…`, có 3 process `Coding Tools MCP`
đang chạy và chưa nhận source candidate. Ubuntu
`codex-control-plane.service` vẫn `active` (PID `233866`, `NRestarts=1`) nhưng
`/healthz` trả schema `7`, fingerprint
`sha256:3f247e44c1b25658eb3bad2af313d13c7ec73ac250569e93a77463ba8aef64a9`
và revision `000938f…`; DB vẫn có 1 node/1 enrollment và 0 binding/context/
work/action/receipt. Đây là proof runtime cũ, không phải deploy mới; probe không
copy code, restart, đổi admission hay mở ingress.

| Thành phần | Bằng chứng gần nhất | Hệ quả cho kế hoạch |
| --- | --- | --- |
| Ubuntu | `svhome`, `100.116.112.22`; service active, schema 7, SQLite tốt, package fingerprint khớp; backup/healthcheck thành công | Giữ service/DB hiện có; không xây backend cạnh tranh |
| Git | Ubuntu, GitHub `main`, Windows checkout cùng `b57ab92` | Đồng bộ code đã đạt, không có nghĩa runtime đã cập nhật |
| Windows pilot | `DESKTOP-63643J4`, `100.72.186.41`, user `Admin`; checkout `E:\DEV\Codex-web` | Đây là target đầu tiên; không tự đưa máy DaoChienThang vào rollout |
| Runtime Windows | Recovery Host chạy từ `E:\WebMcpAcceptanceHost-1.0.0`; MCP/native/tunnel false, `fully_ready=false`, connector unavailable | Cần deployment/activation có kiểm soát và identity/readiness mới |
| Hai process phụ | GPU và utility là con của Recovery Host | Không còn dùng nhận định sai “2 UI người dùng đang mở” làm blocker |
| Central execution | Binding/context/work request/action/receipt đều 0; chưa có bridge policy trên Windows | Chưa có canary end-to-end nào được nghiệm thu |
| Installer đang giữ | 1.0.0, 121,750,019 bytes; SHA-256 `6a1c762c6f810ba3a5738f5e274465453ffa4a122d27ef7921045391e719d576` | Artifact tham chiếu của `b57ab92`, **không dùng làm candidate cuối** sau các sửa tiếp theo |
| Proof cũ | Node 828/828 pass; MCP 1.156 pass/2 fail, hai case pass khi kiểm tra riêng sau sửa test/giảm tải; packaged smoke pass | Giữ cả lỗi ban đầu và kết quả retry; không đổi thành claim full suite mới đã pass |

Các blocker source phải được đóng:

- **B1 — idle handoff sai khi UI đang khởi động:** `superviseElectronUi()` có
  thể spawn UI rồi trả `alive=false` từ quan sát trước spawn; cached IPC và
  handoff hiện không chặn pending registration. Lượt audit đã tái hiện trong
  bộ nhớ, không spawn process thật.
- **B2 — thời hạn retry chưa bao trùm I/O:** hai lần gọi status/snapshot vẫn có
  timeout riêng đầy đủ; tổng chờ có thể vượt deadline caller.
- **B3 — hợp đồng identity CJS → Python thiếu trường:**
  `normalizedObservation()` kiểm tra nhưng không trả `observation_kind`;
  `observed_runtime_identity()` bắt buộc nó bằng `mcp_identity_read_only`.
- **B4 — adapter chỉ hỗ trợ development:** hai CJS wrapper yêu cầu
  `runtime_mode=development`; node agent gọi `scripts/dev-ui-lifecycle.js`.
  Chưa có đường tương đương cho installed runtime.
- **B5 — gói NSIS thiếu node adapter:** manifest package hiện đóng gói
  `electron/`, `renderer/`, `resources/`, không gồm node agent trong
  `control-plane/`. Không thể coi installer hiện tại là node cài đặt hoàn chỉnh.
- **B6 — UI central và telemetry việc đang chạy chưa có:** Electron Control
  Center là local-only; HTTP central mới có JSON API. Heartbeat identity/readiness
  không chứng minh active job, write lease hoặc tiến độ RUN/WAVE.
- **B7 — execution/result relay còn hẹp:** façade chỉ có central status và
  một fixed read-only intent; bảy tool khác bị chặn. Receipt/digest không tự
  là kết quả nghiệp vụ để người dùng đọc và nghiệm thu.

Nguồn cần sửa/đối chiếu: [Recovery bootstrap](../electron/services/recoveryBootstrap.js),
[Recovery Host](../electron/services/recoveryHost.js),
[identity observer](../control-plane/control_plane/recovery_identity_observer.cjs),
[read-only wrapper](../control-plane/control_plane/recovery_read_only_bridge.cjs),
[node agent](../control-plane/control_plane/node_agent.py),
[façade](../control-plane/control_plane/mcp_facade.py),
[package](../package.json), [UI local](../renderer/index.html).

## 3. Kiến trúc được chọn cho pilot

### 3.1 Vai trò và ranh giới

| Nơi chạy | Giữ trách nhiệm | Không làm |
| --- | --- | --- |
| Ubuntu | Web UI operator + HTTP/MCP façade + registry/queue/action journal/receipt + backup | Không sửa trực tiếp file Windows qua SSH/SMB; không nhận quyền local chỉ vì node online |
| Windows installed Recovery Host | Quản lý lifecycle local, exact installation identity, policy/grant và node helper | Không tạo writer mới ngoài Coding MCP; không nhận executable/shell/PID tùy ý từ Web UI |
| Coding Tools MCP Windows | Workspace, Job/RUN/WAVE, controller/write fence, effect/proof canonical | Không giao canonical ledger cho Ubuntu quyết định thay |
| Electron Control Center Windows | Setup/enrollment local, sửa cấu hình, local diagnostics và lifecycle được cho phép | Không đổi nhãn local-only thành fleet management |
| GitHub | Source và bằng chứng delivery được phép đưa lên repo | Không phải hàng đợi công việc hay nơi giữ credential/profile Windows |

Luồng nghiệm thu: **UI/client → Ubuntu → node helper → Recovery Host/local
MCP → journal/receipt → Ubuntu → UI/client**. SSH chỉ phục vụ quản trị triển
khai/chẩn đoán. Chạy thành công một lệnh SSH không được tính là product canary.

### 3.2 Một đường vận hành chính

- Chọn **Windows packaged runtime** làm đích RC-A/RC-B. `E:\DEV\Codex-web`
  vẫn là source/workspace, không được dùng làm installation identity của app.
- Development runtime chỉ dùng kiểm thử riêng; không cho packaged/development
  cùng làm chủ một data profile/workspace. Có thể giữ development adapter cho
  kỹ thuật, nhưng mode/identity phải chọn tường minh, không auto-fallback.
- Node helper dùng Python đã bundle và adapter được chạy bởi Electron đã cài;
  không đòi máy đích có Git, Node toàn cục hoặc checkout để agent hoạt động.
- Recovery Host giám sát một helper theo fixed launch manifest; helper chỉ chở
  observation/action/receipt. Runtime local vẫn là nơi admit/execute duy nhất.
  Helper mặc định không nhận việc khi chưa có local policy hợp lệ.
- Windows pilot yêu cầu đúng user đã đăng nhập. Supervisor hiện là user-session
  `Interactive`/logon, không được hứa cold boot/no-login. Ubuntu user service
  có linger là ranh giới khác.

### 3.3 Web UI nhỏ, riêng tư

- Cùng origin với backend; HTML/CSS/JavaScript gọn, tái dùng phong cách và
  quy tắc trạng thái của Electron. Chưa thêm frontend framework, DB hoặc BFF
  service mới chỉ để dựng dashboard.
- Serve qua **HTTPS trong Tailnet**, không mở Internet/Funnel/router. Tên URL
  chính thức chỉ chốt sau khi kiểm tra DNS/certificate trên Ubuntu; hiện
  `http://100.116.112.22:8765` là backend, không phải Web UI HTTPS đã triển khai.
- Browser session giới hạn thời gian, cookie `HttpOnly`, `Secure`,
  `SameSite=Strict`, logout/invalidate; dùng cùng operator ownership hiện có.
  Các route ghi cần CSRF/Origin check, rate limit và revalidation server-side.
  Session trong bộ nhớ phù hợp single-owner; service restart yêu cầu login lại.
- Không lưu operator token trong URL/localStorage/bundle/report; không gửi
  operator token xuống node. Node credential và secret local tách riêng.
- Static assets chỉ được serve theo allowlist, có CSP, chống path traversal;
  read model/API `no-store`; text từ node/log render dưới dạng text, không HTML.

## 4. UI kiểm soát: sáu màn hình phải có

### 4.1 Tổng quan hệ thống

Hiển thị riêng Ubuntu service/DB/admission, backup age, disk-space warning,
Windows transport, MCP readiness, contract freshness và loaded revision.
Mỗi card có giờ quan sát, tuổi dữ liệu, nguồn bằng chứng và lý do lỗi.

Không có một đèn xanh chung che mất “Ubuntu up nhưng Windows chưa chạy”.
Đối chiếu `source → packaged → installed → running → pilot accepted` bằng
các badge khác nhau. Mở console vẫn xem được central khi Windows offline.

### 4.2 Thiết bị và workspace

Danh sách node và trang chi tiết: tên hiển thị, stable device/endpoint IDs,
runtime instance/epoch, contract SHA, heartbeat, package/build, binding/context,
workspace generation, policy trạng thái/expiry. IP chỉ là địa chỉ vận chuyển.

Wizard chọn đúng máy → xác minh local workspace được phép → tạo binding/context
có expiry. Root/workspace selection được đối chiếu tại Windows, không nhập path
bất kỳ từ browser rồi coi là đã có quyền. Chuyển node tạo context mới, không
đổi target của action đang tồn tại.

### 4.3 Công việc và timeline

Hiển thị `WorkRequest → action → attempt → local Job/RUN/WAVE → receipt → proof`
với correlation IDs. Tách rõ đã lưu, chờ node, đã có thể gửi, node chấp nhận,
đang chạy có telemetry, hoàn tất kỹ thuật, cần nghiệm thu và chưa rõ effect.

“Đang chạy gì” phải đến từ **projection local có schema và timestamp**, gồm
job/run/wave ID, trạng thái, số command hoạt động, busy/write-fence, mốc tiến độ,
exit code và bằng chứng kết quả được phép. Không suy từ `accepted`, queue count,
PID còn sống hay heartbeat. Thiếu dữ liệu ghi “chưa có quan sát local”.

Result preview có allowlist, giới hạn bytes, owner/target/expiry; log theo cursor
và redaction. RC-A giữ receipt/digest nếu chưa có data-relay được cấp quyền;
phải nói rõ giới hạn đó. RC-B cần kết quả đủ để người dùng nghiệm thu workflow.

### 4.4 Chạy thử có hướng dẫn

Checklist trước gửi: đúng node/workspace, build current, strict discovery,
policy hợp lệ, không busy, scope/expiry/capability đúng. Cho xem request summary,
target và phạm vi trước xác nhận. RC-A chỉ cho một fixed read-only canary.

Submit chống double-click bằng idempotency key; timeout mạng giữ exact request
để truy vấn lại, không sinh key mới nhằm chạy lại. HTTP ACK chỉ hiển thị “đã lưu”.
Sau khi nhận receipt, UI cho xem actual target/instance và oracle kiểm chứng.

### 4.5 An toàn và đối soát

| Nút | Ngữ nghĩa thật | Gate |
| --- | --- | --- |
| Đóng admission / bảo trì | Dùng durable `recovery`; chặn intake/dispatch mới, vẫn nhận late receipts hợp lệ | Có từ RC-A; không ghi “đã dừng mọi job” |
| Mở lại admission | Owner xác nhận sau fresh readiness và rà soát inflight/unknown | Không tự mở vì reconnect hoặc health xanh |
| Hủy yêu cầu chưa gửi | Settle chỉ action chưa từng gửi | Action đã gửi phải ghi “đã yêu cầu hủy/chưa xác nhận dừng” nếu có supported stop path |
| Thu hồi node/binding/context | Chặn quyền mới theo backend, giữ evidence lịch sử | Không giả định effect cũ chưa xảy ra; credential revoke có thể cần đường đối soát riêng |
| Dừng job đang chạy | Request qua local authority, bind exact Job/RUN/instance; chờ terminal receipt | Chỉ bật trong RC-B sau bridge và stop/fence proof; không kill PID từ browser |
| Restart/update runtime | Lifecycle operation có preview target/build, active-work preflight, controlled full-clean và postflight | Chưa có remote contract thì disabled, thao tác local Electron theo runbook |
| Đối soát kết quả chưa rõ | Đọc exact local journal/effect proof, ghi quyết định qua authority được hỗ trợ | Không có nút “retry unknown” hoặc sửa thẳng database |

Nút disabled phải giải thích lý do và next action. Không bê nút “clear logs”,
“clear task state” hoặc “clear performance” từ Electron lên central audit UI.

### 4.6 Phiên bản, kiểm thử và vận hành

Hiển thị source commit, manifest/hash artifact, app mode, installed/running
identity, package signature status thực tế, kết quả test/smoke/canary, backup
timestamp/hash, restore/reconcile receipt và soak window/incidents.

Cho export **báo cáo đã lọc secret**, không tải profile/DB/credential/raw payload.
Một test pass, installer build thành công và outcome người dùng là ba trạng thái
khác nhau. Fault drill phải có nhãn isolated/production và scope.

### 4.7 Chất lượng UI tối thiểu

- Layout desktop và mobile; tiếng Việt; keyboard focus, trạng thái bằng chữ và
  màu, không dùng màu làm tín hiệu duy nhất.
- Poll overview single-flight khoảng 5 giây khi tab hiển thị; background giảm
  tần suất/backoff. Đây là ngưỡng thiết kế để đo, không phải latency đã chứng minh.
- Dùng stale thresholds từ contract hiện hành (node heartbeat hiện 60 giây;
  runtime projection có ngưỡng riêng), không tự biến timestamp thiếu thành mới.
- Không đồng bộ chạy `systemctl`, SSH hoặc process census nặng theo từng poll UI.
  Central đọc receipt và observation đã thu; local supervisor sở hữu probe.
- Target/generation/epoch đổi hoặc status hết hạn thì vô hiệu hóa thao tác;
  backend phải kiểm tra lại ngay lúc nhận thao tác, không tin cờ ready của browser.

## 5. Các gói công việc và thứ tự thực hiện

| Gói | Công việc | Phụ thuộc | Gate kết thúc |
| --- | --- | --- | --- |
| W0 | Khóa baseline, target, scope, backup/rollback inventory; sửa drift tài liệu build | Không | Có preflight và danh sách quyền, không còn giả định “hai UI”/installer tự có agent |
| W1 | Sửa B1/B2/B3 và regression tests | W0 | Handoff fail-closed, deadline thật, CJS→Python identity không mất trường |
| W2 | Packaged node adapter/helper, lifecycle và observation DTO | W1 | Chạy được từ installed tree, không phụ thuộc checkout/global Node, single owner |
| W3 | Web UI, auth, read models và các central safety controls | Chốt DTO của W2 | UI dùng backend thật; offline/stale/unknown/CSRF/secret tests đạt |
| W4 | Enrollment/policy wizard, bounded read-only loop và result/receipt flow | W2 + W3 | Integration fixture trọn đường và negative target/authority cases đạt |
| W5 | Freeze nguồn, đóng hai gói, smoke và cài/activate office node | W1–W4 | Exact bytes/package/installed/running receipt, strict runtime readiness |
| W6 | Chạy thử read-only bằng UI/client | W5 | **RC-A đạt**, không có action unknown bị che hoặc execution qua SSH |
| W7 | Một mutation workflow, stop/cancel/fence, bounded result relay | RC-A | **Execution gate đạt**, effect đúng một lần trong các fault case đã test |
| W8 | Offline/reconnect/restore/backup ngoài máy/rollback và soak | RC-A; effect recovery sau W7 | **RC-B đạt** với operator acceptance và evidence packet |

W2 và W3 có thể làm song song sau contract freeze; một owner cho mỗi file/schema.
Không chờ UI trang trí xong mới viết test lõi; không mở mutation trước RC-A.

### W0 — Chuẩn bị và kế hoạch rollback

1. Recheck Git root/HEAD/dirty của Ubuntu và Windows; giữ nguyên work khác và
   toàn bộ evidence `.coding-tools` theo repo policy.
2. Xác minh app root/profile/user/process tree/descriptor/Supervisor manifest,
   installer registry và active Job/RUN/write authority. Không suy từ tên `.exe`.
3. Kết quả query registry trước từng lỗi parse path: phải query lại an toàn;
   không khẳng định “không có đăng ký uninstall” từ query đó.
4. Lưu installer cũ + hash, task/manifest/config metadata và verified snapshot
   vào vị trí rollback riêng, **ngoài `dist`**, trước build vì `clean-dist` xóa
   output cũ. Secret/profile backup riêng, ACL và encryption; không đưa lên Git.
5. Chọn một workspace canary không nhạy cảm trên office node; mutation dùng
   file fixture mới có tên exact, không sửa dữ liệu làm việc để thử lần đầu.
6. Sửa maintained docs cho đúng `npm run dist` hiện chạy `test:all` = Node + MCP;
   `dist:dir` không chạy toàn bộ tests. Giữ history của proof cũ.

### W1 — Sửa lỗi an toàn và hợp đồng

- Pending launch, waiting registration, initial grace, unknown, stale, busy
  không được admit idle handoff. Không đổi `alive === false` thành `!== true`.
  Phải invalidate observation cũ khi lifecycle/registration đổi và xác minh
  quiescence tại ranh giới handoff, không chỉ dùng hai snapshot lệch thời điểm.
- Một monotonic deadline chung cho status, snapshot và sleep. Trước mỗi lần
  gọi lấy remaining budget; hết budget thì fail closed, không thêm timeout tối
  thiểu vượt ngân sách. Các retry chỉ dành cho trạng thái quan sát an toàn.
- Bổ sung đúng trường identity đã được xác minh vào output wrapper; test serialize
  output CJS thật → parser Python thật. Missing/wrong kind/epoch/server identity
  vẫn không ready; không bù từ UI PID hoặc fixture đi vòng adapter.
- Tối thiểu test: UI vừa spawn; registered UI live; PID tái sử dụng; không có
  registration; suppression; snapshot busy kéo dài; slow first/second IPC;
  timeout không gây mutation; exact good identity và malformed identity.

### W2 — Runtime cài đặt và agent quan sát

- Tách `installation_root`, `workspace_root`, `data_root`; dùng runtimePaths và
  installed identity/manifest để resolve, không giả packaged là development.
- Cập nhật wrapper/status observer cho exact mode; packaged entrypoint chỉ cho
  phép status/identity/fixed bridge qua Recovery IPC. Không expose eval, token,
  arbitrary module path, command hoặc file read từ helper.
- Thêm selected node files vào package input và verifier theo **một manifest
  nguồn**, không duy trì hai bản sao code thủ công. Có bundled Python + cách
  chạy adapter qua installed Electron; thử khi checkout không truy cập được.
- Recovery Host sở hữu start/stop/reap helper; một instance; mất parent thì
  không để agent tự trở thành authority. Supervisor vẫn phục hồi Host theo
  fixed manifest. Network error dùng bounded backoff; không spin/poll vô hạn.
- Mặc định heartbeat/observation; execution loop tắt. Sau policy riêng mới
  bật read-only lane. Receipt replay từ journal luôn trước new dispatch; không
  thực thi lại một action chỉ vì subprocess/network timeout.
- Thêm projection versioned/redacted cho policy status, capability, busy,
  active local job/run/wave và progress; giới hạn bytes/count, timestamp và
  observation sequence. Không copy canonical ledger hoặc raw prompt/log.
- Windows ACL cần được xác minh thực tế cho config/journal/secret; `chmod 600`
  trên Python Windows không được coi là ACL proof.

### W3 — Backend read model và UI

**Đã có trong source (chưa phải UI live):** `GET /` và hai asset allowlist chỉ
được enable khi `CONTROL_PLANE_WEB_ORIGIN` là một HTTPS origin cụ thể. Login
đổi operator token thành cookie `HttpOnly; Secure; SameSite=Strict` 30 phút
trong bộ nhớ; service restart/logout invalidates session. `GET /v1/ui/overview`
trả read model central có redaction, không trả objective/criteria/scope hay raw
action/receipt data. Browser có thể duyệt đúng một enrollment request đang chờ
(chỉ tạo identity, không tạo policy/binding/context/execution), đóng admission
về `recovery`, và W4 bổ sung route riêng chỉ queue fixed `workspace_context`
canary cho context live. Các write chỉ accept exact Origin + session-bound CSRF;
canary có expiry server-owned tối đa 10 phút và one idempotency
key/session/context. Reopen vẫn theo Bearer/runbook sau independent review;
không có generic tool/path/target hay credential browser route. Bearer automation
hiện hữu không bị đổi. Node inventory còn có policy state/expiry/reason đã
lọc từ heartbeat local; nó là telemetry của node, không phải quyền browser hay
bằng chứng policy đã được central xác minh. Policy digest, file policy, local
path và credential không đi vào overview. Focused
`test_http_api.py` chứng minh routes/assets, cookie flags, wrong/missing Origin,
rate limit, redaction, logout/invalidation, CSRF rejection/acceptance và replay
fixed canary. Fixture HTTP/SQLite còn chứng minh browser queue → central poll →
strict node bridge mock → receipt → redacted overview; nó không thay thế bridge
hay Windows thật. Đây không chứng minh certificate, reverse proxy, browser thật,
node telemetry hoặc Windows readiness.

UI còn hiển thị lifecycle projection giới hạn theo owner cho action: tool/target
identifier, delivery state, receipt state/time mới nhất và receipt count. Nó
loại bỏ arguments, admission reference, local handle, receipt payload/digest và
secret. Vì vậy `dispatch_unconfirmed`/`reconcile_required` vẫn hiện rõ là chưa
biết hoặc cần đối soát, không được diễn giải thành effect hoàn tất.

**Còn để đạt gate W3:** phải chốt private HTTPS URL/proxy, run test browser thật
qua URL đó (login/logout/refresh/expiry/CSRF và XSS fixture) và bổ sung các DTO
local telemetry versioned/redacted còn lại (busy/Job/RUN/WAVE/progress) trước
khi UI được nói “đang chạy việc gì”.
UI hiện hiển thị heartbeat/readiness đúng là node-reported, không biến nó thành
active Job/RUN/WAVE hay quyền mutation. Không bật cancel/stop/binding wizard
trước W4/W7 tương ứng.

- Dùng các GET inventory/admission/request/action hiện hữu; thêm operator
  read model có version cho overview/ops/local observations, phân trang và
  redaction. **Route mới phải được thiết kế/test**, không coi đã tồn tại.
- Node gửi telemetry theo authenticated node route, không được đổi owner hoặc
  target bằng payload. Sau snapshot restore/service restart, UI không trộn
  quan sát cũ với instance mới thành ready.
- Local telemetry chỉ phục vụ hiển thị; mutation authority không được lấy từ
  UI cache. UI mới không thêm tool thứ chín vào public MCP surface.
- Reuse stylesheet/design/tri-state patterns, không expose Electron preload
  qua mạng. HTTP API giữ cùng canonical Store; không thêm DB status riêng.
- Test browser thật: login/logout/session expiry/CSRF, wrong origin, XSS log
  fixture, không lộ token, offline, refresh trang, stale/busy, duplicate submit,
  timeline và nút bị khóa có lý do. Có screenshot/video evidence dùng dữ liệu
  fixture hoặc đã sanitize; không chụp credential màn hình.

### W4 — Onboarding và read-only dispatch

**Đã có trong source (chưa phải enrollment/pilot live):** packaged
`node-agent.cmd` nay nhận đúng fixed runtime arguments cho enrollment,
heartbeat và safe poll; trước đây các subcommand này reject tail arguments của
launcher. Lệnh local `install-read-only-policy` tạo đúng policy v2 ở packaged
data root, require confirmation, bind origin/device/endpoint/owner/workspace/
generation/facade pin, giới hạn expiry 24 giờ và không nhận data-root khác.
`inspect-read-only-policy` chỉ trả projection không credential; `disable...`
ghi `enabled=false` thay vì xóa evidence. Cross-language test chứng minh policy
Python được Recovery Host CJS normalize/digest đúng; negative tests chặn missing
confirmation và packaged path redirect. Lệnh này không contact Ubuntu, không
start scheduler, không invoke bridge/dequeue hay enable mutation; Windows ACL
vẫn `unverified` cho tới install gate.

`runtime-heartbeat` hiện kèm policy observation compact (`enabled`,
`expired_or_disabled` hoặc `unavailable` với reason code); SQLite schema 8 chỉ
lưu state/expiry/digest/reason, và overview browser chỉ nhận state/expiry/reason.
Heartbeat cũ không xóa observation policy trước đó. Đây là observability, không
là policy grant hay admission authority.

Source hiện có thêm `run-read-only-loop`: chỉ operator local gọi rõ ràng, min
15 giây, tối đa 24 giờ; trước khi loop nó kiểm tra policy enabled/chưa expiry
và exact central origin/device/endpoint. Nếu gate local sai, không heartbeat
hay dequeue. Mỗi iteration mới heartbeat strict rồi mới gọi lane read-only;
không tạo Scheduled Task, không chạy lúc logout và không biến `poll` cũ thành
execution ngầm. Focused store tests chứng minh thứ tự heartbeat→poll, bounded
sleep, packaged launcher tail và policy-missing refusal không allocation.

**Còn để đạt gate W4:** Electron onboarding UI, actual enrollment/binding/
context và local telemetry/receipt projection chưa có. Browser request hiện
chỉ là fixed canary, chưa phải wizard hay remote execution; chưa có policy được
cài trên office node. Các bước này cần exact canary workspace/generation,
façade contract, expiry, maintenance window và quyền thao tác Windows trước
effect thật.

- Local node tự tạo secret, gửi hash enrollment; owner duyệt đúng device và
  endpoint. Không chuyển operator bearer xuống Windows.
- Electron bổ sung trang “Kết nối Ubuntu”: URL private, fingerprint/target,
  pending approval, heartbeat, policy scope/expiry và bật/tắt nhận việc.
- Provision policy v2 bằng đường local được bảo vệ, bind central origin,
  owner/device/endpoint/workspace/generation và façade contract pin. Web UI
  chỉ đề nghị scope; không tự mint local authority.
- Chỉ tạo binding/context sau strict current-process discovery/identity. Client
  pilot mặc định là Web UI riêng tư; proof ChatGPT/Codex connector central là
  gate riêng nếu người dùng muốn dùng từ cloud. Local strict receipt vẫn cần
  một client được runtime hỗ trợ; không forge receipt từ raw request tùy ý.
- Thêm loop read-only dưới lifecycle W2, có switch enable rõ ràng, expiry và
  ngắt nhận việc mới khi manual stop/admission đóng. Không đổi legacy `poll`
  từ no-op thành execution ngầm.
- Façade và UI cùng đi qua fixed intent handler canonical; không tạo generic
  action để bypass provenance. Contract thay đổi thì pin/schema/fingerprint và
  policy/client cần được cập nhật đồng bộ, không giả tương thích.

### W5 — Đóng gói hai artifact và triển khai có kiểm soát

**Source/package proof hiện có (chưa deploy):** `npm run dist:control-plane`
tại `main@e12d131…` tạo versioned release directory và archive Ubuntu,
schema `8`, package fingerprint
`sha256:4bef62162e8a5ccc6de136dbabd2079d5c605a8bbf130aabf48de67655880040`,
archive SHA-256 `2090e173cbd73ab054a3a0eb459cf9bbffb6950a9d3ebd0f93bfcf1192430522`.
Artifact chỉ gồm allowlist backend/UI embedded, deployment templates/launchers,
environment example, migration/backup/rollback guide và manifest file/component
hashes. Nó không có DB, `.coding-tools`, token, node credential, session hoặc
environment thật; templates chạy qua symlink `current` tới release immutable,
không qua Git checkout. Focused artifact integration giải nén archive, chạy
launcher với state/DB tạm ở ngoài release, nhận `/healthz` đúng
schema/fingerprint/revision rồi dừng process. Đây là package preparation proof,
không phải health của Ubuntu, systemd ownership, activation, rollback,
HTTPS/browser, node, canary hay production proof.

**Gói Ubuntu:** backend + Web UI assets + systemd/unit/timer templates +
manifest phiên bản/hash + migration/backup/rollback hướng dẫn. DB/secrets ở
state directory, không nằm trong artifact. Giữ deployment pin và health
verifier; dùng versioned release directory khi đóng gói để source edit không
âm thầm đổi bytes của service đang chạy.

**Gói Windows:** NSIS 1.0.x/phiên bản được chốt, Electron/Recovery/MCP + bundled
dependencies + node adapter, local onboarding và Supervisor integration. Không
tự bump product version ở lượt lập kế hoạch. Thư mục cài đặt exact được chốt
sau W0; không ghi đè thư mục acceptance cũ bằng phép copy tùy tiện.

Manifest delivery phải chứa source commit/tree, product/runtime mode, component
digests, DB schema, local và façade contracts, asset/helper hashes, build OS/
toolchain versions, installer size/SHA-256 và references tới proof tương ứng.
`package_source_sha256` hiện bao gồm `control_plane/*.py`, nên source của UI
embedded `web_ui.py` được bind cùng package source; vẫn **không** dùng nó để
chứng minh CJS helpers, packaged resource layout, artifact signature hoặc
actual proxy bytes. Manifest phải cover các boundary đó riêng.
Log “signing with signtool” không chứng minh có certificate hợp lệ; kiểm tra và
ghi actual signature status. Không hứa artifact signed khi chỉ có SHA-256.

Thứ tự build/deploy:

1. Review source/contract/secrets; kiểm tra active jobs; freeze exact candidate
   và chạy relevant tests. Không chạy lại full suite ở mỗi edit; release proof
   gắn bytes chính xác, test thay đổi mới thì chạy focused phù hợp.
2. Nếu được giao commit/push: chạy `stage:coding-tools-delivery` rồi
   `check:coding-tools-delivery` trước mỗi delivery; giữ invariant evidence.
   Build từ checkout sạch/isolated worktree **ngoài `.coding-tools`**.
3. Đóng gói Windows bằng entrypoint hiện hành. Thêm regression filter
   `__pycache__`/`.pytest_cache`/bytecode để source chứa cache vẫn không lọt vào
   artifact; không dựa lâu dài vào xóa cache bằng tay hoặc tắt sanitation.
4. Chạy Recovery real-process E2E vì thay lifecycle; packaged smoke có thêm
   installed adapter/helper coverage. Lưu log/exit/status và artifact hashes.
5. Chạy install/uninstall smoke ở environment **không có cùng sản phẩm đăng ký
   trong user đó**. Harness hiện tại không phải upgrade test. Office upgrade,
   Scheduled Task/logon và production profile preservation cần proof riêng.
6. Đóng admission, drain/reconcile inflight, snapshot và kiểm tra rollback
   compatibility. Update Ubuntu artifact/unit pin có kiểm soát; verify schema,
   fingerprint, UI manifest và instance; giữ admission recovery cho tới gate.
7. Cài Windows candidate qua supported installation procedure. Retirement của
   owner cũ phải có exact identity/quiescence; nếu chưa có packaged upgrade
   lifecycle hợp lệ thì hoàn thiện path đó, không dùng global taskkill hoặc
   installer ép đóng serving process để né guard.
8. Reinstall/refresh Supervisor bằng supported path khi executable/manifest đổi;
   verify heartbeat của Supervisor mới, không chỉ Task Scheduler báo Running.
9. Lấy actual loaded revisions, fresh host/UI/MCP identities và epoch, workspace
   generation, tunnel/recovery health và strict discovery/ACK; chỉ explicit
   reopen sau kiểm chứng. `dev:status installation=mismatch` không phải oracle
   cho packaged node; dùng observer mode đúng đã hoàn thiện trong W2.

Artifact ở `b57ab92` không còn đủ proof cho candidate có W1–W4. Git bundle qua
SSH chỉ là phương tiện chuyển source khi GitHub auth không khả dụng; phải verify
HEAD/hash, không đưa credential vào URL hoặc tự cấu hình GCM bằng secret trong chat.

### W6 — Kịch bản nghiệm thu RC-A

1. Mở UI, login, thấy đúng Ubuntu và office node cùng tuổi telemetry/build/policy.
2. Hoàn thành strict-ready preflight; tạo một binding/context có expiry cho root
   pilot đã được phép, không tự gắn vào workspace sản xuất khác.
3. Từ UI gửi một read-only intent. Theo dõi same request/action/attempt qua
   node journal và Recovery/MCP receipt; không SSH thay cho execution lane.
4. Xác minh local workspace thật đã được truy cập, identity/contract/policy
   đúng, output digest/preview match oracle không nhạy cảm.
5. Double-click/reload/resend cùng key phải giữ ID và không phát sinh invocation
   thứ hai. Thử sai node/owner/context/generation, policy expired, contract drift,
   runtime stale/busy; tất cả từ chối trước effect.
6. Windows offline: central/UI còn dùng được, request hiển thị chờ; reconnect
   revalidate trước dispatch. Expired request không chạy khi máy quay lại.
7. Đóng admission/hủy never-sent từ UI; đối chiếu central state và node proof,
   không hiển thị job đã dừng nếu chưa có terminal local receipt.

**Pass:** proof chain đủ, đúng target, một invocation, UI trung thực và không có
unknown chưa giải thích. Nếu chưa có strict client receipt: báo đúng blocker,
không bỏ guard để lấy màu xanh.

### W7 — Một workflow ghi có kiểm soát và dừng job

Đây là implementation mới, không phải bật bảy tool đang chặn:

- Chọn một workflow sửa file fixture trong root pilot, theo API local hiện hữu
  phù hợp; không generic shell gateway. Local controller cấp exact grant/write
  fence, RUN/WAVE/context và idempotency/effect journal trước invocation.
- UI preview file/scope/preimage hash và canary identifier; user/owner xác nhận
  phạm vi. Node recheck target, policy, expiry, generation, preimage và fence.
- Sau effect: independent diff/hash oracle và local proof; central chỉ project
  receipt, không tự accept outcome thay controller/người dùng.
- Result relay/versioned capabilities chỉ mở cho workflow được kiểm chứng;
  handles namespaced theo node/context, expiry/owner, bytes limit và redaction.
- Stop job dùng supported `command_control`/task lifecycle theo exact handle;
  job không hỗ trợ stop thì UI nói rõ, không tự suy từ pause request. Có test
  child-process quiescence và không phát sinh late write sau stop được xác nhận.
- Lost ACK sau effect: replay receipt hoặc reconcile journal, không gọi mutation
  lần hai. Có test crash trước/sau local dispatch/effect, cancel/revoke/expiry
  race, direct+central concurrent writer, stale grant và changed generation.
- Mutation canary rollback chỉ revert exact fixture nếu hash vẫn khớp output
  của canary; có concurrent change thì dừng, không force restore file.

### W8 — Fault, phục hồi và vận hành

- Chạy fixtures cô lập trước; fault thật chỉ trên target/window được giao quyền.
  Không làm đầy disk production hoặc reboot máy office khi chưa có cửa sổ bảo trì.
- Test offline/reconnect, helper/Recovery Host restart, central crash, receipt
  delivery loss; thể hiện unknown thật và đối soát, không quảng cáo exactly-once
  tuyệt đối ngoài các boundary đã chứng minh.
- Backup local hourly/retention hiện có là nền. Chốt destination off-host và
  chủ sở hữu recovery key trước encrypted transfer; key không nằm cùng artifact,
  không mặc định upload vào tài khoản/cloud chưa được chọn.
- Restore candidate ở admission recovery, đối chiếu các effect xảy ra sau mốc
  snapshot với node journal, schema/credential compatibility và live grants;
  không copy/merge ledger, không tự reopen vì integrity tốt.
- Rollback app: đóng admission → fence central actor tại node → reconcile/drain
  → activate previous compatible binary → fresh identities/contract → explicit
  reopen. Database rollback là quyết định riêng, không chạy kèm app rollback
  một cách mặc định.
- Sau fault/rollout cuối, bắt đầu **24 giờ soak mới** của exact deployed build.
  Theo dõi instance/restart, timer cadence, backup freshness, heartbeat, queue,
  unknown/effect count và read-only canary theo nhịp đã duyệt. Fault windows tách
  khỏi uninterrupted soak; source/service thay đổi thì nêu rõ rebase.
- Windows logout: báo offline/chưa sẵn sàng, không giả định vẫn execute. Logon/
  reboot đúng user rồi verify Supervisor+agent+runtime. No-login là nhánh sau,
  không dùng để kéo dài nghiệm thu RC-B vô hạn.

## 6. Ma trận proof tối thiểu

| Boundary | Proof cần thu | Gate |
| --- | --- | --- |
| Safety/source | UI launch race; deadline; serialized CJS→Python identity; wrong-install rejection | W1/W2 |
| Local worker | Installed tree không checkout; single helper; parent stop; manual stop; durable receipt recovery | W2 |
| Central/browser | Auth/CSRF/owner/target/redaction; stale/unknown; duplicate submit; no false completion | W3/W4 |
| Artifact | Byte-exact resources/adapter/assets; cache exclusion; NSIS/hash/signature status; sanitized manifests | W5 |
| Install/lifecycle | Isolated install; office upgrade riêng; profile/ledger preserved; fresh runtime + strict ACK; Supervisor heartbeat | W5 |
| Product read-only | UI request → correct Windows effect → receipt; wrong target negative; offline/expiry | RC-A |
| Mutation/stop | One scoped effect + independent oracle; same-key replay; lost ACK; stop/revoke races; one writer | W7 |
| Recovery | Central/node restart; restored snapshot older than effect; rollback compatibility; unknown remains visible | W8 |
| Operations | Encrypted off-host recovery; measured restore; uninterrupted 24h exact-build receipts; operator review | RC-B |

Các entrypoint kiểm thử hiện có để chọn theo thay đổi, **không phải lệnh đã chạy
trong lượt lập kế hoạch**:

```text
node --test tests/recovery-bootstrap.test.js tests/recovery-host.test.js tests/dev-ui-lifecycle.test.js
node --test control-plane/tests/recovery_identity_observer.test.cjs control-plane/tests/recovery_read_only_bridge.test.cjs
node --test tests/control-plane-read-only-bridge.test.js tests/control-plane-bridge-runtime.test.js
node --test tests/control-center-truthfulness.test.js tests/control-center-signal-failsafe.test.js tests/build-verification.test.js
python -m unittest discover -s control-plane/tests -v    (PYTHONPATH=<repo>/control-plane)
npm run test:recovery:e2e
npm run dist
node scripts/packaged-recovery-smoke.js
node scripts/installed-recovery-smoke.js                (chỉ trên environment đủ điều kiện)
```

Cross-language/browser/packaged-agent/upgrade/reconnect tests còn thiếu phải
được bổ sung; không coi những lệnh trên đã bao phủ chúng. Full suite từng mất
47 phút trên office node: chỉ chạy ở release boundary, kiểm soát tải, ghi riêng
performance budget failure và functional failure; không nới oracle để xanh.

## 7. Quyết định và quyền cần chốt tại thời điểm triển khai

Không cản trở việc viết code/test fixture và lập kế hoạch; phải chốt trước effect thật:

1. Exact install destination/maintenance window trên office Windows; giữ app
   packaged là runtime chính, không chạy development cùng profile.
2. Pilot workspace và dữ liệu được relay; file mutation canary cụ thể, quyền
   đọc/ghi và người nghiệm thu. Không coi mọi file trên Windows đều được cấp quyền.
3. URL HTTPS Tailnet/certificate và client pilot. Web UI private là mặc định;
   cloud connector cần network/access acceptance riêng.
4. Quyền deploy/restart Ubuntu/Windows, install Supervisor, drain jobs và
   reboot/logon drill. Không suy quyền publish/tag/release công khai từ “đóng gói”.
5. Nơi giữ backup off-host đã mã hóa, recovery key và cách thử restore không
   ảnh hưởng dữ liệu đang dùng.

## 8. Định nghĩa hoàn tất và bàn giao

RC-A chỉ đóng khi UI thật, packaged node thật và read-only product canary đều
đạt; không chỉ ảnh mockup/build/test pass. RC-B chỉ đóng thêm sau mutation/stop/
recovery/operations có receipt và người vận hành xác nhận dùng được.

Mỗi gói kết thúc phải báo: đã sửa/đã chứng minh gì; Git và exact build/runtime;
job/lease/action state; blocker; việc còn lại; next action. Bàn giao cuối gồm
URL UI đã verify, installer và manifest, runbook cài/khôi phục, báo cáo proof
đã lọc secret, danh sách giới hạn còn lại và trạng thái push/deploy/release.

Không tính phần trăm từ số file/test. Không gọi “hoàn tất” khi chỉ đóng gói,
SSH thành công, Git đồng bộ, queue rỗng hoặc có một component health xanh.

**Thứ tự bắt đầu:** W0 → W1; sau đó W2/W3 theo contract thống nhất. Chỉ sau
W4 mới freeze candidate và đi W5/W6. Chưa chốt thời hạn ngày công trước W1/W2;
24 giờ soak là tối thiểu thời gian observation, không phải tổng estimate dự án.

**Trạng thái lượt thực hiện:** source W1–W4 phần nền đã được sửa và có focused
proof như nêu đầu tài liệu; chưa commit/push/deploy/restart/release. Lượt này đã
chạy package build Linux, focused tests và `npm test`; không chạy canary hay
effect từ xa. `electron/app-icon.ico` và `electron/app-icon.png` bị `icon:build`
viết lại khi build, cần review riêng trước delivery; không tự khôi phục/ghi đè
thay đổi. `.coding-tools/delivery-snapshot.json` staged và canonical ledger live
modified được giữ như evidence theo policy; research chronology không bị sửa.
