# Kế hoạch hoàn thiện luồng thực thi code

Ngày: **11-10-2026**. Repository quan sát: dirty `main @ 2c554f59cb7b8ffc86ce5e0e28076c792777642f`.
## Cập nhật — initial proof đã chuẩn bị, chưa triển khai

Quyền thử r10 đã hết **20:48:18.491 +07**. Source mới đã gắn một lệnh test argv
bất biến vào bản vá, kiểm tra quyền Đọc/Sửa/Chạy đúng thư mục trước ghi và ngay
trước chạy, lưu proof đúng RUN/WAVE và giữ effect khi test fail/timeout. Gọi lại
chỉ quan sát kết quả cũ. Các hash của request không dùng tính năng mới giữ nguyên.

Candidate Windows `initial-proof-1011-r11` đã build, parity 12 file và smoke
packaged trong hồ sơ riêng đạt. Gói Ubuntu `9cae1044…` đã kiểm chứng cục bộ;
schema29 giữ lịch sử cũ. Test tập trung JS/Recovery/native/server đạt; lượt native
đầy đủ theo yêu cầu tách module ghi nhận **1218 PASS / 5 FAIL / 5 SKIP**. Một lỗi
là expected contract cũ, đã sửa assertion exact hash/schema và retry đạt 1/1;
ba check continuation bị trạng thái Sandbox đang dùng chung từ chối trước
thực thi. Một fixture chờ `exited` ngay sau bounded yield đã đổi sang poll cùng
handle; retry thật đạt 1/1, không dùng VM. Diagnostic mock ở boundary đạt 4/4,
không thay ba test live còn bị chặn. Hai lỗi ban đầu đã có retry đạt; ba gate
continuation live vẫn chưa nghiệm thu. Chưa thấy regression source trong năm
phân loại này và chưa tuyên bố full suite xanh; package không thay proof môi trường.
Các gói mới chưa kích hoạt/deploy và chưa gia hạn quyền.

Artifact recovery riêng `81303f7c…` đạt 7/7 kiểm tra offline: chỉ mở schema29 đã
persist recovery, giữ toàn bộ hàng/cột verification mới và chặn intake, dispatch,
grant cùng acceptance mới. Đây là đường recovery đóng đã chuẩn bị cục bộ,
không phải rollback về schema28 hay bản đã deploy; proof không dùng network,
runtime hoặc dịch vụ thật. [Receipt recovery](../.coding-tools/reports/unified-setup-20261011/executor-repair/initial-proof-server/rollback-preparation/proof-receipt.json).

Contract native mới vẫn có tám tool `smart-v3`, schema1, SHA
`0e4733844a471814a3a6240fa9c0423b56195ab80f6e5283b5c978e28edaaed4`.
Test đã ghim exact hash, tính lại từ public `tools/list` và kiểm tra schema plan
bốn trường cùng expiry riêng. Không dùng hash native này thay contract Ubuntu.

Controller của phiên hiện tại chưa có transport native ChatWeb đã xác thực để
gọi `task_control accept`. Cần chốt phiên/controller thật trước live canary mới;
receipt patch + test thành công vẫn phải ghi acceptance pending nếu chưa có
checkpoint đó. Không đổi actor Electron để giả controller ChatWeb.

Bước kế tiếp: nghiệm thu ba test live khi Sandbox trên host sẵn sàng, triển khai đúng hai artifact sau xác nhận theo
AGENTS §5, chạy một NEW patch có test kiểm tra chính hành vi đã sửa, quan sát
source-bound proof rồi nghiệm thu bằng controller ChatWeb thật. Giữ RUN/WAVE
cũ và dữ liệu lịch sử. Agent cài bền vững, cleanup/timeout và installer ký vẫn là
các phần cần nghiệm thu riêng.

Xem [packet nghiệm thu bản vá mới](../.coding-tools/reports/unified-setup-20261011/executor-repair/candidate-r11/NEW-PATCH-ACCEPTANCE.md)
và [gói server/migration](../.coding-tools/reports/unified-setup-20261011/executor-repair/initial-proof-server/README.md).

Trạng thái ghi nhận **20:38:26 +07**: **r10 packaged đang chạy và READY trên
DaoChienThang; hai lần gọi MCP trên epoch đã recovery đều đạt 4 PASS/0 FAIL/exit 0
với Job/receipt/output đúng nguồn. Store-only Ubuntu đã triển khai theo xác nhận.
Quyền đúng folder giữ hạn 20:48:18.491, không gia hạn khi recovery. Các checkpoint
r7/r9 và giai đoạn chuẩn bị r10 bên dưới là bằng chứng lịch sử.**

## Checkpoint hiện tại — r10 controlled acceptance

- Runtime recovered epoch READY/open, Host/UI/native/agent cùng sống và các cờ
  local/central/authority/fully-ready đều true; MCP inventory online/ready/enabled.
- Initial và warm submission là hai action độc lập, mỗi lần một attempt,
  test 4/4, Job thực terminal và task/context/writer đã đóng; không replay.
  Mode `cold` của initial chưa chứng minh cold startup sạch vì bản ghi daemon
  cũ còn tồn tại. Warm host hint chưa chứng minh owner/reuse/VM cleanup.
- Census query-only có SQLite `ok`, command/Job/lane hoạt động = 0; phân loại
  `RUNTIME_BUSY` chỉ do runtime đang sống. RUN/WAVE acceptance cũ và hashes giữ
  nguyên. Job exec độc lập có RUN/WAVE rỗng; chưa có source-bound proof của patch
  hoặc controller acceptance. Timeout chưa thử.
- Runtime trước biến mất đột ngột khoảng 20:17, chưa biết nguyên nhân. Quan sát
  parent Job membership không đủ kết luận nguyên nhân; supported recovery đã
  khôi phục đúng package. Agent thử còn bounded; durable lifecycle/delegation,
  cleanup/timeout và signed installer vẫn là gate.
- Bước tiếp theo: thêm initial verification bằng argv được duyệt vào NEW approved
  patch, giữ receipt phân biệt patch effect với proof failure/dedup, ghi native
  ProofLedger đúng RUN/WAVE rồi dùng controller ChatWeb thật gọi `task_control accept`.
  Không replay patch cũ hoặc coi exit 0 của exec riêng là acceptance.

Xem [bằng chứng r10](../.coding-tools/reports/unified-setup-20261011/executor-repair/candidate-r10/mcp-acceptance/R10-CONTROLLED-ACCEPTANCE.md)
và [plan initial proof](../.coding-tools/reports/unified-setup-20261011/executor-repair/acceptance-gap/INITIAL-PROOF-IMPLEMENTATION-PLAN.md).
Git vẫn dirty `main @ 2c554f59`; runtime packaged vẫn r10 trong lúc sửa source.
Parity 11 file của r10 là snapshot trước adapter mới; các sửa đổi initial proof
cần validation riêng và candidate/parity/rollout mới trước khi gọi là packaged/live.
Store deploy/restart Ubuntu đã xảy ra; không commit/push/release hoặc reboot Windows.

Tài liệu này chốt thứ tự xử lý cho yêu cầu thiết lập gọn và giải quyết vấn đề
code từ đầu đến cuối. Nó dùng [CURRENT_STATE](CURRENT_STATE.md) làm nguồn hiện
trạng và giữ hướng hội tụ của [ROADMAP](ROADMAP.md). Các kế hoạch/checkpoint
tháng 9 giữ nguyên giá trị lịch sử; các số đo cũ không trở thành trạng thái live
hôm nay. Không cần xây thêm một hệ điều phối, registry hay cơ sở dữ liệu mới
để hoàn thành chương trình này.

## 1. Kết quả người dùng cần nhận

**Cài một ứng dụng, chọn máy/thư mục và quyền, đưa vấn đề cần sửa; hệ thống tìm
nguyên nhân, sửa đúng phạm vi, chạy kiểm thử và trả kết quả được kiểm chứng.**

Luồng sử dụng hằng ngày:

1. Mở ứng dụng hoặc connector đã kết nối; lựa chọn máy/thư mục được giữ.
2. Nhập vấn đề và điều kiện thành công.
3. Theo dõi tiến độ, diff, lệnh/test và kết quả trên cùng giao diện.
4. Nếu bị chặn, ứng dụng chỉ rõ nguyên nhân và một hành động tiếp theo.

ID binding/context, JSON policy, token và lệnh SSH không nằm trong luồng bình
thường. Owner vẫn xác nhận lần đầu khi cấp máy/phạm vi và khi mở rộng quyền.
Người dùng không phải gia hạn quyền thử nghiệm mỗi giờ để dùng sản phẩm hằng ngày.
Điều cuối là **mục tiêu cần triển khai/nghiệm thu**, chưa là khả năng đã đạt.

## 2. Hiện trạng và điều chỉnh kế hoạch được gửi

### Checkpoint 18:49 +07 — r9 chạy, r10 đã đóng gói

- r9 đã kích hoạt theo quyền owner. Cold MCP canary có 4 PASS/0 FAIL/exit 0,
  một attempt với Job/receipt đúng nguồn. Warm attempt native exit 0 nhưng relay
  từ chối command ID bắt đầu bằng `-`; đã đối soát failed/settled, giữ journal
  UNKNOWN và không replay. Không có TAP đầy đủ để gọi warm là 4 PASS.
- Census trực tiếp xác nhận READY, không còn command/lane/task thử/writer mở;
  13 quarantine families và RUN/WAVE chờ acceptance cũ giữ nguyên. Ubuntu chưa
  đổi snapshot/service. Quyền thử đúng folder kết thúc lúc 19:19:16.518.
- r10 sửa URL-safe ID, bỏ compact assignment bắt buộc khỏi setup standing và
  thêm cleanup có xác nhận cho đường full-clean. Build, 11-file parity và
  isolated packaged smoke đạt; 55 adapter + 57 setup/policy + 72 native +
  75 full-clean cases và 3 process cases là các receipt riêng, có phần coverage
  giao nhau. r10 chưa được kích hoạt, chưa có live teardown proof.
- Store chỉ sửa lookup assignment để loại internal action contexts khi đủ
  owner/binding/request/action/context correlation. 7 cases đạt; gói Store-only
  snapshot `395c7868…` đã chuẩn bị, chưa deploy. Đây không phải việc cấp quyền
  bằng context của action hoặc sửa trực tiếp row lịch sử.
- Điều kiện chuyển r9 → r10: chứng minh môi trường warm cũ đã dọn qua đường
  được hỗ trợ trước khi stop exact runtime. API cũ thiếu cleanup marker;
  không lấy trạng thái Job exited hay `process_tree_cleaned` làm proof VM.
  Ordinary stop ngoài full-clean vẫn là gate cần hoàn thiện riêng.

Kiểm tra chỉ đọc lúc **19:16:26 và 19:16:58 +07** xác nhận host không còn
tiến trình Sandbox và không có bản ghi daemon (không mở nội dung bản ghi).
Census giữ nguyên command/job/lane đang chạy = 0, pending acceptance và lịch
sử quarantine. Freeze/preflight r10 lúc **19:17:17–19:17:38** cũng đạt, với
hai quan sát VM/backend bằng 0. Không chạy canary timeout mới; chưa xác định
nguyên nhân môi trường cũ biến mất và không gọi đây là cleanup API confirmation.
Helper chuyển bản bắt buộc kiểm tra lại VM/backend ngay trước mỗi thao tác.

Lúc **19:20:40**, server giữ nguyên source/service và trạng thái quiescent.
Quyền thử r9 đã hết lúc 19:19:16.518; yêu cầu duyệt gộp r10/Store/cửa sổ 60 phút
mới đang chờ trả lời. Không chạy thêm test hoặc tự gia hạn quyền sau thời hạn.

### Checkpoint rollout 19:38 +07

Owner đã duyệt r10/Store/cửa sổ 60 phút mới. Ubuntu phục vụ Store `395c7868…`,
service mới `cp_6766892f5ada47d1862a0d24334f1116`; backup SQLite và đối chiếu
toàn bộ lịch sử đạt, không restore DB. Intake ở recovery. Windows chưa đổi:
agent thử r9 đã kết thúc, quyền cũ hết hạn khiến projection admission/readiness
đóng dù durable epoch giữ READY/OPEN. Preflight đã chặn trước thao tác Windows.
Đang nối fresh local identity/quiescence proof với gia hạn owner đúng scope,
sau đó chuyển r10; chỉ mở intake khi có r10 heartbeat/policy sẵn sàng thật.

Đợt tiếp theo là rollout packet đã đóng băng sau xác nhận thao tác dịch vụ,
nghiệm thu cold/warm/timeout và setup standing trên runtime mới; sau đó đóng
adapter proof/acceptance và delegation dùng thường ngày. Không tự gia hạn pilot
hoặc đánh dấu semantic acceptance chỉ vì test exit 0. Xem
[CURRENT_STATE.md](CURRENT_STATE.md) và [packet r10](../.coding-tools/reports/unified-setup-20261011/executor-repair/candidate-r10/).

| Nội dung | Bằng chứng hiện có | Cách xử lý |
| --- | --- | --- |
| `inventory` trả `targets: []` | Private service chỉ thấy binding được pilot hiện hành ủy quyền; response hiện chưa trả lý do target bị lọc | Quan sát đúng principal, delegation và hạn quyền; thêm reason có cấu trúc cùng next action. Không đăng ký lại theo suy đoán. |
| `INVALID_ARGUMENT` của `read_file` | Pin facade bị dùng nhầm thành tên tool/hash node; revision Ubuntu đã sửa feedback và đã có bounded read proof | Dùng discovery và test contract hiện có; chỉ sửa sai khác còn tái hiện được. |
| Chạy lệnh/test | r9 cold canary đạt 4 PASS/exit 0; warm native exit 0 nhưng relay từ chối URL-safe ID. r10 sửa contract và cleanup, package/smoke đạt | Nghiệm thu cold/warm/timeout trên r10, giữ lịch sử r7/r9 và exact Job/receipt; không replay lần UNKNOWN. |
| Giao diện phân tán | r7 đã gộp một cửa sổ/trang setup, candidate/smoke/106 Node + 8 Console cases đạt; kích hoạt live đạt READY lúc 17:24 | Tái sử dụng giao diện đã chạy. Renderer continuation và connector ChatGPT thật còn gate nghiệm thu riêng. |
| Patch thành công nhưng acceptance chờ | Bridge cố ý giữ `local_semantic_acceptance=pending`; verdict Ubuntu không gọi coordinator local | Hoàn thiện adapter proof/acceptance cùng đợt P0 về setup và delegation. |
| Thiết lập và gia hạn quá nhiều lần | r10 source/candidate đã bỏ compact assignment bắt buộc khỏi standing setup; private service vẫn dùng pilot | Nghiệm thu continuation trên runtime mới; triển khai delegation exact-target dùng thường ngày. Không tự gia hạn pilot. |
| Lỗi authority báo sai bước tiếp theo | `_tool_failure` hiện ánh xạ mọi `CONFLICT` sang quan sát action dù execution chưa bắt đầu | Dùng reason có cấu trúc từ Store để phân biệt đối soát action với xử lý authority/admission; không suy diễn từ chuỗi message. |
| Có bộ cài sản phẩm hoàn chỉnh | r7 là unpacked development candidate; gate đóng gói chặn binary Sandbox thử nghiệm unsigned ở đường release thông thường | Đóng gate release/install trước khi tuyên bố “cài là dùng”. |

Rollout mới có [receipt thực tế](../.coding-tools/reports/unified-setup-20261011/rollout-r7/):
Ubuntu phục vụ đúng frozen Console delta; r7 READY, hai phép đọc hoàn tất,
quyền exact-folder từ 17:20:33.341 đến 18:20:33.341 +07. Test mới thất bại trước
process, không có exit 0/output test. Các proof r5 trước đó vẫn là lịch sử.
Quyền thử trước đã hết hạn không tự chứng minh code bị lỗi.

## 3. Chốt kiến trúc và phạm vi

- Ubuntu giữ endpoint MCP chung, xác thực, phạm vi tài khoản, binding và relay.
- Với workspace đang ở Windows, Windows giữ source và thực thi bằng agent/runtime
  hiện có. Một runtime làm chủ ledger và ghi workspace.
- Electron là giao diện quản lý cùng luồng công việc; Recovery Host quản lý vòng
  đời runtime; controller hợp lệ giữ quyền nghiệm thu.
- Giữ backend Sandbox đang có; ứng dụng kiểm tra và hướng dẫn prerequisite trong
  lần cài đầu. Agent không tự hạ sandbox khi môi trường chưa sẵn sàng.
- Mỗi node hiện có một policy file/exec hoạt động. UI phải nói rõ folder đang
  được áp dụng; chọn folder khác là một chuyển scope được kiểm tra, không phải
  quyền đồng thời cho mọi folder đã đăng ký.

**Server đã tồn tại không thay thế executor ở nơi đang giữ mã nguồn.** Nếu chọn
chạy hoàn toàn trên Ubuntu thì repository, dependency và công việc phải chuyển
sang workspace Ubuntu. Đây là quyết định placement riêng với đánh giá khả năng
chạy dự án; không đưa chuyển toàn bộ source hoặc thêm backend vào đợt hiện tại.

Giữ contract facade và contract node độc lập khi chúng mô tả các tầng khác nhau.
Một nguồn định nghĩa được kiểm soát cho **mỗi contract**, kèm test adapter giữa
các tầng, hữu ích hơn ép mọi tầng dùng một hash/schema chung. Public smart-v3
vẫn có tám tool; thay đổi operation/adapter cần plan discovery tương ứng.

### Quyền hiện có và khoảng trống dùng thường ngày

| Lớp | Contract hiện có | Ý nghĩa cho kế hoạch |
| --- | --- | --- |
| Standing file/exec local | Policy gắn đúng workspace/generation không tự hết hạn; node ưu tiên standing observation khi policy có mặt | Dùng lại installer và observation hiện có; horizon của heartbeat là freshness, không phải quyền server vô hạn. |
| Compact metadata assignment | `read-only-policy-assignment` resolve đúng một context còn hạn; không có context thì thiếu assignment, nhiều context thì conflict | Đây là đường compact cũ. r7 gọi nó vô điều kiện trước policy standing, nên setup vẫn cần context dù standing authority đã có. |
| Standing authority | `/v1/nodes/{device_id}/policy-authority` đã trả owner, contract và metadata binding cho đúng endpoint/workspace/generation | Thay đổi hẹp ở continuation để dùng đường này cho setup standing; endpoint không tự cài policy hay cấp quyền action. |
| Private tunnel service | `_admission_decision` vẫn cần scoped pilot exact-target kể cả admission `open`; dispatch ghim decision live ban đầu | Chưa có delegation exact-target bền vững dùng thường ngày. Grant còn hạn hoặc mở `open` không giải quyết khoảng trống này. |
| Account OAuth | Đã có authority theo account và có thể dùng `open` không cần pilot private service | Đây là lựa chọn đã có khi account authentication phù hợp; không bắt buộc chuyển connector cá nhân sang OAuth. |
| Thời hạn | Pilot tối đa 24 giờ; service grant tối đa 30 ngày; Console context có lựa chọn đến 24 giờ | 60 phút là cửa sổ operator đã chọn cho phép thử này, không phải hard limit toàn sản phẩm. Tăng TTL không tạo delegation dùng thường ngày. |

Các nguồn trực tiếp: [node policy API](../control-plane/control_plane/http_api.py),
[node observation](../control-plane/control_plane/node_agent.py),
[admission/dispatch và TTL](../control-plane/control_plane/store.py),
[continuation r7](../renderer/app.js). Hai đường compact và standing phải được
phân biệt trong projection, UI và test; không xóa đường compact còn được dùng
chỉ để làm setup đứng thành công.

## 4. Thứ tự triển khai và điểm dừng

### Đợt 0 — Chốt baseline và một đường nghiệm thu

**Đầu ra:** bảng đúng source/build/runtime/principal/workspace, test oracle và
quyền của controller. Tái sử dụng receipt r9 và candidate r10 còn khớp source;
proof r7 chỉ là lịch sử của lần khởi tạo thất bại.

- Thực hiện đợt live đã được duyệt theo §7: trước thay đổi quan sát inventory,
  enrollment, binding, node, policy, admission và contract trong cùng phiên;
  phân biệt hết quyền, offline và lỗi code. Bảo toàn rollback và inflight work.
- Đóng lỗi khởi tạo executor vừa tái hiện: probe Sandbox đạt nhưng exec Job
  `spawn_failed` trước process. Ghi phase/backend/error gốc có giới hạn; xác
  minh cold start, sau probe và sau relaunch bằng cùng lệnh nhỏ. Test fixture
  phải phát hiện đúng lỗi này. Chỉ tiếp tục khi Job/receipt terminal có output
  và exit thực tế; không tăng timeout hoặc bỏ sandbox theo suy đoán.
- Lỗi gốc hiện chỉ được giữ thành `SANDBOX_STATE_PHASE_FAILED`; bridge báo
  `CONTROL_PLANE_EXEC_MCP_REJECTED`, nên chưa biết chi tiết backend thất bại.
  Giữ phase/diagnostic đã lọc và lookup exact terminal Job để tự chuyển receipt
  thất bại qua đường được hỗ trợ. Journal UNKNOWN gốc phải được bảo toàn.
- Đối chiếu RUN/WAVE chờ acceptance với owner, exact source/proof và lease. Chỉ
  controller có authority mới quyết định accept/reject; không sửa ledger hoặc
  tạo receipt để dọn trạng thái.
- Chọn một fixture hiện có được phép sửa và một lỗi thật trong repository này.
  Với lỗi thật, chốt reproduction, test thất bại và điều kiện thành công trước.
- Giữ một packet source/contract/release cần giao. Không build/rollout lại cho
  từng chỉnh sửa nhỏ khi các thay đổi còn cùng đợt.

**Qua gate:** biết chính xác thao tác nào chạy ở đâu, ai nghiệm thu, test nào
quyết định thành công. Nếu chỉ thiếu quyền/hết hạn thì ghi blocker vận hành và
tiếp tục phần source có thể làm; không viết thêm policy để né blocker.

### Đợt 1 — P0: Khép kín sửa → test → nghiệm thu

**Khoảng trống đã xác định:**

- `electron/services/controlPlaneApprovedPatchBridge.js` trả patch effect và
  local RUN/WAVE nhưng cố ý để semantic acceptance chờ.
- `RuntimeOrchestrator.controlPlaneExec` tạo context riêng cho exec action,
  không nhận caller tự chọn RUN/WAVE và gọi `exec_command`. Exit 0 của lệnh đó
  chưa trở thành proof của wave patch.
- `Store.record_mcp_patch_acceptance` lưu verdict phía Ubuntu; nó chưa gọi
  coordinator local. `coordination.py` đã có gate proof/controller/accepted files.

**Việc cần làm:** dùng verification của workflow hiện có cho patch mới và nối
quyết định acceptance tới controller hợp lệ, dùng action/task hiện có để lookup
local RUN/WAVE phía server/agent.

1. Bảo toàn liên kết task → patch action → local RUN/WAVE → file/postimage hash.
2. Với **wave mới**, adapter truyền verification/test được cấp quyền ngay trong
   initial `agent_workflow`; đường này đã tạo ProofLedger trước ACCEPTING. Giữ
   test theo argv/checks và phạm vi policy hiện có; không thêm endpoint prove
   khi initial workflow đã đáp ứng. Lệnh exec riêng chưa là proof của patch wave.
3. Controller có authority gọi đường `task_control` accept/reject hiện có.
   Agent/bridge/Supervisor chỉ chuyển tiếp và quan sát; không tự nghiệm thu.
4. Trả trạng thái effect, proof, local acceptance và kết quả vấn đề riêng biệt.
   Lặp lại cùng request/verdict không gây áp patch hoặc chạy test thêm lần nữa.
5. Nếu contract facade phải đổi, đóng gói schema/hash/discovery và test payload
   cùng packet. Caller không được tiêm RUN/WAVE tùy ý để chiếm quyền.

`task_control accept` tự tính digest từ passed proofs đúng RUN/WAVE và kiểm
HEAD/contract/path bytes/coverage; caller không tự cung cấp digest để bỏ gate.
Owner/service của Control Plane hiện chưa có handoff thành native controller.
`handoff=record` chỉ lưu capsule, không cấp quyền acceptance. Giữ controller
ChatWeb attested tại bước accept; không cho Electron tự nhận vai trò này.
Wave cũ đang ACCEPTING thiếu proof phải có đường phục hồi được controller
cho phép riêng; không replay patch/test hoặc sửa ledger để làm nó được nghiệm thu.

**Các module dự kiến:** bridge patch/exec và `runtimeOrchestrator.js`; facade,
node agent/recovery bridge; `workflow_tools.py`/`coordination.py` chỉ ở phần adapter
cần thiết. Không thay toàn bộ state machine hoặc parser đã có.

**Qua gate:** đọc preimage → patch → đọc postimage → test → proof đúng source/wave
→ controller accept; một task kết thúc, writer được nhả, không sinh thêm RUN chờ
acceptance. Test fail/stale hash/wrong controller thì chưa nghiệm thu.

### Đợt 2 — P0: Setup standing và delegation đúng target

Sau khi chốt identity/proof contract, hai phần này có thể làm song song với
adapter nghiệm thu; không phải điều kiện để kéo dài đợt sửa code. Chúng giải
quyết việc người dùng phải tạo context/gia hạn pilot để bắt đầu làm việc;
chúng là thay đổi sản phẩm tiếp theo, không nằm trong Console/UI
delta đã được duyệt rollout.

**A. Bỏ phụ thuộc compact context trong setup standing**

- Dùng `inspect-policy-authority` và installer standing đã có để resolve đúng
  node/owner, endpoint, workspace/generation và capability; principal/delegation
  server vẫn được kiểm riêng tại admission. r7 hiện gọi
  `installControlPlaneReadOnlyPolicyAssignment` vô điều kiện ở đầu continuation;
  thay điều kiện này bằng contract standing được xác minh, không bỏ mọi gate.
- Giữ compact assignment cho đường read-only có hạn còn cần nó. Không biến
  context action thành quyền duy trì, tự tạo context hoặc gia hạn context/pilot.
- Dùng standing policy observation để xác minh route/readiness sau cài; vẫn
  kiểm heartbeat fresh, Sandbox, receipt hash và scope ở effect boundary.
- Owner cấp/thu hồi scope trên màn hình hiện có; local consent vẫn gắn exact
  máy/folder/capability. Đổi quyền tạo generation mới, fence generation cũ.

**B. Delegation exact-target dùng thường ngày cho private service**

- Bổ sung một đường owner-approved delegation bền vững cho đúng service
  principal, binding, endpoint, workspace generation và capability, có revoke
  và thời hạn/lifecycle rõ ràng. Dùng Store và authority/admission hiện có;
  không thêm registry hoặc biến grant service thành quyền toàn bộ owner.
- Inventory, task intake và dispatch phải cùng kiểm delegation này. Task/action
  ghim authority record đã chấp nhận; revoke, expiry hoặc generation/endpoint
  đổi chặn bước chưa gửi. Đã gửi thì tiếp tục observe/reconcile đúng action/Job.
- Pilot có hạn vẫn giữ cho phép thử; không mở admission `open` để bỏ kiểm scope,
  không auto-renew decision. Account OAuth là đường hiện có cần đánh giá/reuse
  khi đúng nhu cầu, không là một nền tảng mới phải xây.
- Dùng transaction/idempotency cho thao tác owner khi hai tab có thể tạo binding
  hoặc authority trùng. Cùng request trả lại kết quả cũ; conflict scope trả lý
  do rõ và hướng đối soát, không tự chọn cửa sổ quyền mới nhất.

**Qua gate:** relaunch app giữ đúng scope, standing setup không đòi compact
context, private service chỉ thấy/chạy target được delegation dùng thường ngày
cho phép. Hết pilot thử nghiệm không âm thầm mở rộng quyền; revoke, sai principal,
endpoint hoặc generation vẫn chặn. Local standing policy một mình không cấp
authority server.

### Đợt 3 — P1: Một bảng chẩn đoán tại chỗ

- Tái sử dụng inventory/status, journal, policy, epoch và Job observation.
- `inventory` trả reason có cấu trúc khi không có target do chưa delegation,
  hết hạn/thu hồi hoặc scope không current; metadata chẩn đoán không lộ target
  ngoài phạm vi principal. Đối chiếu endpoint tuple trong target projection với
  admission để target stale không hiện dispatchable rồi bị từ chối khi chạy.
- Store trả named reason cho authority/admission conflict. Facade ánh xạ reason
  thành next action; `CONFLICT` với `execution=not_started` không luôn yêu cầu
  `observe_existing_action`. Chỉ đưa bước đó khi đã có action cần đối soát.
- Reuse schema `oneOf`, structured validation errors và `tool_contract` trong
  inventory đã sửa. Không mở đợt schema rewrite chỉ vì pin client cũ bị sai.
- Với mỗi blocker trả `code`, tầng lỗi, `retryable`, hành động tiếp theo và các
  ID liên kết sẵn có; không tạo một telemetry database hoặc “diagnostics service”.
- UI hiển thị một lỗi chính cùng phần quyền đã đạt: hết quyền, offline, sai
  contract, thiếu feature/reboot, dependency thiếu, test fail, effect UNKNOWN,
  acceptance pending phải có cách xử lý khác nhau.
- Quan sát/chẩn đoán chỉ đọc; action sửa lỗi phải ghi rõ scope/ảnh hưởng. Không
  tự restart hay đổi quyền để biến một status thành xanh.

**Qua gate:** mọi blocker trong ma trận §5 có lý do và một bước tiếp theo đúng;
không re-enroll vì inventory trống hoặc observe action chưa từng được tạo.

### Đợt 4 — P1: Phục hồi và bộ cài thực thi

**Phục hồi:** dùng journal prepared/running/terminal, ACK replay, exact Job/process
identity, poll/stop và activation/recovery hiện có.

- Thêm đường reconcile/observe chính thức cho UNKNOWN và startup failure để
  không phải chạy script cứu hộ riêng ngoài luồng sản phẩm.
- Giữ phase/backend/error code đủ chẩn đoán, bỏ credential và dữ liệu nhạy cảm.
- Mất ACK hoặc reconnect tra action/Job cũ; không spawn lại vì client timeout.
  Nếu chưa biết effect thì chặn retry và yêu cầu kiểm chứng/reconcile.

**Cài đặt:** r7 unpacked không phải installer release. Chốt nguồn binary Sandbox
được hỗ trợ và gate signing/provenance của release; không bỏ verification để
đóng gói thử nghiệm thành bản sản phẩm.

- Một preflight trong app/bộ cài kiểm Windows feature, pending reboot, runtime
  đóng gói, toolchain và dependency của thư mục. Dùng kết quả probe hiện có.
- Khi cần bật feature, hướng dẫn/thao tác UAC theo yêu cầu owner; chỉ reboot khi
  owner chọn. Không bắt người dùng tự tìm script/token hoặc lệnh cấu hình.
- Kiểm source ở ổ E, đường dẫn có khoảng trắng, project root và dependency đã
  cài. Sandbox hiện không có mạng: việc tải dependency là bước thiết lập được
  chỉ định, test dùng dependency có sẵn; không hứa chạy `npm install` tải mạng
  trong sandbox không có mạng.
- Gói bất biến có manifest, source/resource hashes, update và rollback theo
  release. UI bật lên đúng installation, không cạnh tranh Recovery Host cũ.
- Đưa connected agent/heartbeat vào lifecycle được installation quản lý,
  có quan sát/restart/relaunch đúng identity. Poller thử nghiệm đang được chạy
  bằng helper có giới hạn 200 lượt × 15 giây; đó chưa là kết nối thường trực
  cho sản phẩm. Dùng supervision hiện có, không tạo thêm dịch vụ điều phối.

**Qua gate:** fresh install + upgrade + relaunch/login/reboot theo kiểm thử được
duyệt; cùng workspace/permission, một runtime, chạy test và thu hồi resources
đúng; rollback không đảo dữ liệu workspace hoặc phục hồi DB âm thầm.

### Đợt 5 — Nghiệm thu việc sửa code thật và chuyển sang sản phẩm

Một phép nghiệm thu từ connector ChatGPT thật trên target đã cấp quyền:

`discovery → đọc → tái hiện lỗi → sửa → đọc xác minh → test → proof/accept → báo kết quả`

- Khớp binding, workspace generation, contract, postimage và RUN/WAVE.
- Có exit code/output/Job terminal và controller acceptance đúng wave.
- Chứng minh lỗi ban đầu hết; kết quả người dùng được xác nhận riêng theo
  Problem Revision hiện có. Khi cùng vấn đề còn lỗi, reopen đúng revision.
- Task/writer/job hoạt động của phép thử kết thúc đúng; evidence lịch sử UNKNOWN
  được giữ, không biến toàn bộ lịch sử thành zero pending giả.

**Qua gate:** một lỗi thật được giải quyết end-to-end và kiểm chứng độc lập.
Sau đó thu thập 5–10 vấn đề thật, đo thời gian giải quyết, số vòng sửa lại và
công sức thao tác. Thiếu dữ liệu là chưa biết; số test không thay kết quả sản phẩm.

## 5. Ma trận nghiệm thu tối thiểu

Các dòng sau là **mục tiêu**, chưa là kết quả đã đạt. Dùng số case phân biệt lỗi,
không chạy hàng chục lần cùng một happy path để thay fault coverage.

| Case | Kết quả bắt buộc |
| --- | --- |
| Workspace hợp lệ / sai principal / hết scope / node offline | Target hoặc blocker có lý do đúng; không chọn target khác để thử tiếp. |
| Standing setup / compact assignment thiếu hoặc mơ hồ | Standing đi qua authority đã có; compact vẫn giữ gate đúng; không tự tạo/gia hạn context. |
| Private service hết pilot / delegation standing / account OAuth | Mỗi principal dùng đúng authority; `open` không bypass pilot; delegation chỉ cấp exact-target và revoke được. |
| Inventory trống / endpoint stale / authority conflict trước intake | Named reason và next action đúng, không lộ target ngoài scope và không yêu cầu quan sát action chưa có. |
| Payload đúng, field sai, pin facade/node bị nhầm, client schema cũ | Payload đúng hoạt động; trường sai/contract mismatch có chỉ dẫn; không có side effect. |
| Read → patch → readback → test → accept | Exact pre/postimage, proof đúng wave, accepted checkpoint đúng controller; task/writer đóng. |
| Sai preimage, source đổi trong lúc test, test fail | Không áp nhầm/không dùng proof cũ/không accept. |
| Lặp request trước và sau effect/terminal | Kết quả cũ hoặc quan sát Job cũ; mutation và spawn không bị nhân đôi. |
| Mất ACK/restart sau prepare, sau accept delivery, sau terminal | Cùng action/Job/attempt; effect không rõ vẫn UNKNOWN và không retry mù. |
| Cancel/stop khi test/probe đang chạy | Dừng bước chưa gửi; quan sát thao tác đã gửi; không đổi sang target khác. |
| Thu hồi node/binding/scope hoặc đổi generation giữa workflow | Các bước sau bị fence; không có ghi ngoài policy. |
| Sandbox chưa bật / pending reboot / dependency thiếu / cold start | Chẩn đoán đúng; quyền đọc/sửa hiện riêng; timeout/cold start không tạo job mới. |
| Hai Console tab cùng cấp folder | Một kết quả scope nhất quán hoặc conflict rõ; không tạo grant/context mơ hồ rồi báo thành công. |
| Fresh install / upgrade / reboot / rollback | Một installation/runtime hoạt động, giữ identity và source; trạng thái không lấy từ receipt cũ. |
| Đóng/mở giao diện và một lỗi thật | Không phải nhập lại ID/token; vấn đề được giải quyết hoặc reopen có lý do. |

Thứ tự proof: test nhỏ cho thay đổi → test qua adapter/HTTP bằng fixture → một
phép Windows Sandbox thật → connector ChatGPT thật. Các lần lặp bổ sung chỉ để
kiểm một rủi ro cụ thể như cold/warm, restart hoặc phát hiện flake.

## 6. Điều kiện dừng sửa hạ tầng

Đợt ổn định hoàn tất khi đường end-to-end đã đạt, fault cases của đường chính
đạt, bộ cài được nghiệm thu và một lỗi thật được giải quyết với outcome evidence.
Từ đó, đưa lỗi UX nhỏ vào backlog; chỉ mở lại hạ tầng khi có tái hiện cụ thể về
sai target, mất/trùng effect, truy cập sai quyền, không chạy được test, hoặc
không có proof/acceptance hợp lệ.

Trong đợt này hoãn: backend execution mới, chuyển toàn bộ repository sang Ubuntu,
document/image E2E, thêm routing/model, registry chung mới, telemetry service mới,
và viết lại orchestration. Phân tích/reproduction/diff UI cho vấn đề thật có thể
làm song song; quyền thực thi và nghiệm thu vẫn theo gate đã chốt.

## 7. Delivery, quyền và next action

- Source/test/docs ở repository có thể chuẩn bị tiếp theo phạm vi đã giao.
- Người dùng đã duyệt kích hoạt candidate r7 cho profile Windows
  `web-mcp-assistant` trên DaoChienThang, rollout frozen `web_ui.py` delta lên
  `svhome@100.116.112.22`, restart user service `codex-control-plane.service`
  và cấp mới 60 phút đúng folder `E:/Github/Tools-Codex-web`. Không hỏi lại các
  thao tác này; reverify identity, inflight work và artifact trước thực hiện.
- Approval trên chỉ bao phủ đợt đã chuẩn bị cụ thể. Các thay đổi standing setup,
  delegation và proof/acceptance trong kế hoạch còn cần implementation, source
  proof và packet được review trước rollout tương ứng. Authorization hiện có
  không phải receipt triển khai, quyền tự gia hạn hoặc mở rộng target.
- Không sửa evidence/ledger thủ công, không lẫn unrelated source vào packet.
  Nếu giao Git, chạy retention staging/guard `.coding-tools` theo AGENTS.md trước
  commit/push; giữ cả các receipt thất bại và rollback.
- Mỗi đợt kết thúc bằng checkpoint: phần đạt, proof/source/runtime, blocker,
  phần còn lại và bước kế tiếp. Source, candidate, live activation và kết quả
  vấn đề luôn được báo riêng.

**Bước tiếp theo:** sửa đường khởi tạo Sandbox và giữ diagnostic gốc trên source,
chốt oracle cho cold start/sau probe/relaunch và lỗi terminal lên server. Rollout
r7/Console/60 phút đã có receipt; test thất bại đã đối soát và task/writer đóng,
không chạy lại cùng request. Sau khi execution gate đạt, thực hiện adapter
patch/proof/acceptance ở đợt 1; standing setup/delegation và chẩn đoán làm song
song trong phạm vi đã chốt. Nghiệm thu từ ChatGPT thật và bộ cài còn là gate mở.
