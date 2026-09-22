# Phương án đơn giản hóa thiết lập và Cài đặt

Ngày: 22-09-2026. Source bắt đầu: `main@50ae5c40b0490ebfaf11a8269e982d8475a76ff0`.
Trạng thái: **P1/P2, projection liên kết tài khoản và preset UI đã triển khai vào source; policy adapter/lifecycle P3, đóng gói P4 và runtime live vẫn mở**.
Phạm vi: Windows Execution Hub kết nối Ubuntu Control Plane; giữ tương thích
với cấu hình kết nối trực tiếp đang có. Không phải chứng nhận runtime live.

## 1. Quyết định thiết kế

Thay trải nghiệm “tự cấu hình từng bộ phận kỹ thuật” bằng:

1. Một nơi vào **Cài đặt**, nhìn thấy ngay, không phải tìm trong System.
2. Một luồng **Thiết lập máy này** có thể đóng rồi tiếp tục đúng bước.
3. Mỗi màn hình nói rõ **đang thiếu gì, ai xử lý, bấm gì tiếp theo**.
4. Máy chủ, thư mục và tài khoản là những khái niệm chính. MCP, epoch,
   binding, generation, policy, fingerprint và PID nằm trong chi tiết kỹ thuật.
5. App làm các bước máy móc sau khi người dùng đồng ý; không tự cấp quyền,
   giả thành công, tự duyệt máy hoặc khởi động lại khi người dùng chỉ kiểm tra.

Mục tiêu của đợt này không phải thay toàn bộ dashboard, Tasks/Proof, chat,
model routing hoặc token analytics. Các chức năng đó không thuộc Cài đặt.

## 2. Vấn đề hiện tại đã đối chiếu source

| Vấn đề | Bằng chứng | Thay đổi cần làm |
|---|---|---|
| Thiết lập phân tán | `renderer/index.html:42`, `:251`, `:263`, `:313`, `:415`: 6 mục chính, 5 trang con System; kết nối/thư mục/hướng dẫn/preferences ở các nơi khác nhau | Một điểm vào và một hành trình cấu hình |
| Ubuntu bị phủ lên form direct cũ | `renderer/app.js:236`, `renderer/index.html:263`: central ẩn một số field nhưng còn bố cục triển khai/proxy/Python và nhiều thuật ngữ | Luồng central riêng trong cùng app; không nhân đôi dữ liệu cấu hình |
| Chẩn đoán sai theo vai trò | `electron/services/healthService.js:29`: vẫn yêu cầu key, Tunnel ID/client/running cho mọi role; `repair():50` có thể đổi port/tạo token trước khi báo thiếu cấu hình | Chẩn đoán theo vai trò; tách kiểm tra khỏi thay đổi |
| Lưu preference không độc lập | `renderer/app.js:1091`, `:1773`: global collect/save thu field mọi trang; startup/report interval thiếu handler lưu riêng | Mỗi preference chỉ gửi field đã thay đổi; báo lỗi và trạng thái lưu cạnh field |
| Tên nút không phản ánh tác động | `renderer/app.js:915`, `:1669`: “Kiểm tra Executor” có thể đi vào start/restart | Nút “Kiểm tra” không thay runtime; thao tác thay process có tên và xác nhận riêng |
| Nguyên nhân bị che | `renderer/index.html:100` có source/closure card nhưng `renderer/control-center.css:108` ẩn `.legacy-overview` | Banner chính luôn hiển thị blocker bằng tiếng Việt; không cần mở card hash/epoch |
| Dễ chọn nhầm thư mục | `renderer/app.js:323`: path candidate chủ yếu nằm tooltip; registry và workspace chính là hai đối tượng khác nhau | Hiện tên máy, tên thư mục và đường dẫn local trước khi đồng ý; không tự đổi target task |
| Chờ duyệt không có hành trình tiếp tục rõ | URL không được restore trong `applyFormValues`; reconcile ở initialize/request/rotation | Nạp cấu hình đã lưu, theo dõi request cũ, không bắt nhập lại hoặc tạo request mới |
| Nhiều nơi định nghĩa “ready” | `renderer/app.js:124`, `:427`, `:726` có các phép đánh giá khác nhau | Dùng chung một lớp diễn giải từ sự thật runtime, có kiểm tra freshness |

Các nhận định này là audit source; chưa phải kết quả test tương tác Windows.

### Hai điểm cần sửa trong cách hướng dẫn vận hành

- **Chuyển sang Ubuntu không phải nghiệm thu code.**
  `electron/main.js:1327` sử dụng `full_clean_execution_role_handoff`, không
  bắt nhập accepted-code checkpoint. Full-clean cho bản code thay đổi vẫn
  giữ gate acceptance riêng. Không đưa JSON checkpoint thành bước onboarding.
- **Development khác packaged.** `npm run dev:status` xây identity development;
  mismatch với bản installed không tự chứng minh process đã chết hay package
  hỏng. Chẩn đoán app phải dựa đúng installation, identity và process receipt,
  không yêu cầu mở development app để “sửa” bản installed.

## 3. Cấu trúc Cài đặt mới

Một mục **Cài đặt** cố định, với bốn nhóm. Nhóm cuối mặc định thu gọn.
Các route cũ dẫn về nội dung tương ứng; không giữ hai form cùng ghi một field.

| Nhóm | Người dùng nhìn thấy | Không nằm trên màn hình thường |
|---|---|---|
| Kết nối | Máy này; máy chủ đang dùng; quyền kết nối máy; trạng thái liên kết tài khoản; Tiếp tục thiết lập | Tunnel/key của direct mode; context; node secret; revision chi tiết |
| Thư mục & quyền | Tên/path local; mức quyền được chọn và quyền đã áp dụng; Thêm thư mục; Sửa quyền | ID/generation, policy JSON, legacy assignment, đường dẫn internals |
| Ứng dụng | Giao diện; mở sau khi đăng nhập Windows; tự chuẩn bị khi mở app; đóng cửa sổ thì chạy nền hay dừng | Tool mode cố định; cấu hình báo tiến độ; token maintenance |
| Hỗ trợ & nâng cao | Kiểm tra kết nối; xem vấn đề; báo cáo đã che dữ liệu nhạy cảm; phiên bản; các mục nâng cao mở khi cần | Không trải toàn bộ cổng/proxy/credential/source receipts cùng lúc |

Mục nâng cao chứa Network/Proxy, cổng, dữ liệu đăng nhập, thay credential,
direct legacy, chẩn đoán runtime/source, và liên kết tới công cụ kiểm thử/build.
Mỗi nhóm chỉ mở rộng một cấp, không thêm System → Settings → Advanced → ...

Các nút chạy/dừng công việc thuộc màn công việc hoặc tổng quan, không biến
Cài đặt thành bảng điều khiển tác vụ. Chỉ dẫn xử lý lỗi có thể dẫn tới thao tác
runtime đúng scope khi thực sự cần.

## 4. Màn hình người dùng mở hàng ngày

Đầu Cài đặt là một tóm tắt ngắn:

> **Cần hoàn tất kết nối máy này**
>
> Máy chủ Ubuntu chưa cho phép máy Windows này kết nối.
> Cấu hình đã được lưu; không cần nhập lại.
>
> **Mở trang quản trị Ubuntu** · Kiểm tra lại

Chỉ một nút chính ứng với vấn đề hiện tại. Dưới nó là tiến độ thiết lập và các
nhóm Cài đặt. Không có ba nút Start/Restart/Deploy cạnh nhau.

Khi đủ điều kiện, thông báo là “Sẵn sàng nhận việc — trong quyền đã cho phép”.
“Đã kiểm tra từ ChatGPT lúc …” là bằng chứng riêng. Không gọi việc lưu cấu hình,
HTTP 200 hoặc process đang sống là đã kiểm thử toàn tuyến.

## 5. Luồng thiết lập bốn bước

Ba thông tin chính cần người dùng quyết định: máy chủ nào (nếu chưa có), thư
mục nào, và cho phép làm gì. Đăng nhập/duyệt máy vẫn là thao tác có ý nghĩa
quyền hạn; không giả vờ toàn bộ quy trình chỉ có ba click.

### Bước 1 — Kết nối máy chủ

- Profile hiện tại đã là central: đọc lại máy chủ/request đã lưu. Không hỏi
  chuyển vai trò hoặc nhập key Windows lần nữa.
- Cài mới: đề xuất “Dùng máy chủ Ubuntu”; chỉ đi vào direct khi người dùng
  chọn rõ. Không hard-code server cá nhân của chủ repo cho mọi người dùng.
- Nhập HTTPS origin một lần nếu chưa được cấu hình. Hiện tên máy chủ và kiểm
  tra đúng origin, kết nối, phiên bản tương thích trước thao tác tạo kết nối.
- Nếu có request pending: hiển thị “Chờ quản trị viên duyệt máy”, tên máy và
  địa chỉ máy chủ. “Mở trang quản trị Ubuntu” chỉ mở trang private; không nhúng
  operator credential vào Windows, URL, chat hoặc log.
- Chủ máy và quản trị viên có thể cùng là một người, nhưng UI vẫn nói rõ đang
  thực hiện ở đâu. Không có quyền quản trị thì hiển thị hướng dẫn bàn giao ngắn.
- Tải lại trạng thái từ request đang có; không gửi enrollment mới khi double
  click/reopen/timeout. Node bị thu hồi không tự tái đăng ký.
- Máy chủ chưa hỗ trợ chức năng yêu cầu: báo “Máy chủ cần cập nhật”; không
  hướng dẫn cài lại Windows hoặc tự bật legacy để vượt gate.

Migration từ direct cũ là thao tác có xác nhận: hiển thị runtime/công việc bị
ảnh hưởng, kiểm tra active work, giữ config và secrets cũ. Không đổi
`executionRole` bằng settings autosave.

### Bước 2 — Chọn thư mục và quyền

Một lần chọn thư mục bằng dialog. Hiện rõ:

> Máy: DESKTOP-63643J4
>
> Thư mục: E:\DEV\Codex-web

Hai lựa chọn thường dùng:

- **Chỉ xem** (mặc định): chỉ đọc trong phạm vi cho phép; không sửa file/chạy lệnh.
- **Làm việc với mã nguồn**: đọc, sửa và chạy công cụ trong phạm vi đã cấu hình.
  Phải chọn rõ và xem xác nhận phạm vi trước khi áp dụng.

“Tùy chỉnh” chỉ hiện các quyền rời và giới hạn cụ thể khi người dùng mở phần
nâng cao. Không dùng
“Tin cậy” để người dùng phải đoán là quyền gì. Không đổi `permissionMode=safe`
thành trusted vì họ chọn read/write/exec.

Trong UI central, ba lựa chọn này là preset tiếng Việt. Preset chỉ tạo ra
inventory capability local; nó không tự tạo binding, context hay policy. ID
workspace/generation không hiển thị trong luồng thường và chỉ còn là selector
nội bộ của thao tác nâng cao.

Nút chính: **Thêm thư mục này**. Ứng dụng có thể dẫn đăng ký → chuẩn
bị quyền → chọn liên kết trong cùng luồng, nhưng giữ từng receipt/thẩm quyền
riêng. Đăng ký thành công không có nghĩa đã được phép chạy.

Quan trọng khi triển khai preset:

- Source hiện tại có policy danh sách file và argv-prefix. Checkbox `exec`
  chưa tự tạo allowlist; checkbox `write` chưa cho phép ghi toàn root.
- Cần adapter local có kiểm tra để biến lựa chọn người dùng thành phạm vi
  policy cụ thể. Owner/contract/ID lấy từ nguồn đã xác thực; renderer không
  tự đặt giá trị. Đây là phần backend phải làm, không chỉ đổi chữ trong UI.
- Không gắn nhãn “toàn thư mục” nếu contract hiện tại chỉ cho một tập file.
  Nếu nhu cầu toàn root cần mở rộng policy, đó là thay đổi contract riêng có
  test path traversal/reparse/symlink, secrets và generation; không dùng `*`
  hoặc argv-prefix quá rộng để giả hoàn thiện preset.
- Build/test có thể chạy script của repository: phần xác nhận phải nói rõ,
  không gọi mọi script là an toàn. Không thêm quyền push/deploy/xoá dữ liệu
  chỉ do chọn preset, không giả rằng argv `git`/`npm` đã đủ giới hạn quyền.
- Nếu mới áp dụng được read nhưng người dùng chọn write/exec, hiển thị từng
  quyền “đã áp dụng/chưa áp dụng”; không báo hoàn tất cả gói.

Ứng dụng tự quản lý các định danh nội bộ. Cụ thể source node-agent tạo và lưu
workspace ID/generation trước khi đăng ký Ubuntu để retry cùng identity;
người dùng không phải xin rồi chép các ID này.

Sửa quyền của thư mục đã dùng mở một bản tóm tắt tác động và xác nhận. Chỉ khi
backend chứng minh job đã dừng mới nói “đã dừng”; generation bị fence không
chứng minh process đang chạy đã chết. Không autosave quyền hoặc tự retarget
task. Đổi path không giả làm replace capability: giữ ID cần path-migration được
triển khai; nếu chưa có phải hướng dẫn tạo thư mục mới và giữ record cũ.

### Bước 3 — Liên kết tài khoản

- Mở đúng luồng liên kết tài khoản qua máy chủ/connector được cấu hình.
- Không đánh đồng “ChatGPT đang đăng nhập trong cửa sổ web” với OAuth principal
  đã được Control Plane chấp nhận.
- Người dùng chọn đích bằng **tên máy + tên thư mục**; ID vẫn dùng ở backend.
  Link/binding mới chỉ tạo bằng quyền hợp lệ và sau lựa chọn này, không do
  node tự nhận quyền account.
- Thiếu OAuth backend/configuration: nêu “Quản trị viên cần cấu hình liên kết
  tài khoản”; không hiển thị một nút đăng nhập giả hoặc đưa context legacy vào
  luồng thường ngày.
- Phiên hết hiệu lực/revoked/phân quyền chưa đủ có thông báo riêng khi có bằng
  chứng. Chỉ HTTP `FORBIDDEN` chưa đủ kết luận context đã hết hạn.
- Một tài khoản dùng nhiều client được cùng chọn đích đã cấp; mỗi task pin
  target/generation riêng, không có “thư mục đang hoạt động” toàn tài khoản.

### Bước 4 — Kiểm tra và hoàn tất

- Tự quan sát các bằng chứng hiện có; hiển thị từng kết quả theo vai trò.
- “Kiểm tra kết nối” chỉ quan sát, không cài policy/start/restart/deploy hoặc
  lấy action khỏi queue. Reconcile cache/enrollment có thể ghi state cục bộ:
  ghi đúng là bước đồng bộ, không gọi mọi hành động đồng bộ là read-only.
- Nếu cần thay process: nút **Chuẩn bị máy này** có tóm tắt tác động và gọi
  operation hỗ trợ. Tiến độ lấy từ operation, không chạy animation % giả.
- Chờ người dùng duyệt/login không tiêu thụ thời hạn thay process. Hiện source
  chỉ cho enrollment sau khi chọn central role; không thể chỉ đảo thứ tự UI.
  Cần phân tách chuẩn bị onboarding đóng quyền với epoch thay process, hoặc
  dùng handoff retry hiện có sau khi prerequisite đạt. Giữ nguyên deadline
  bảo vệ execution; không tăng TTL vô hạn hoặc tạo epoch mới mỗi vòng polling.
- Reload theo dõi lại operation đang có. Failed/expired chỉ retry có chủ đích
  sau kiểm tra điều kiện; không ghi lại epoch FAILED thành READY.
- Runtime central dùng local readiness + route + authority; không yêu cầu
  Tunnel/connector ACK của Windows direct. Account/binding/admission và phép
  thử từ ChatGPT là những bằng chứng bổ sung, không thay thế nhau.
- Phép thử end-to-end là yêu cầu đọc hẹp do người dùng đồng ý qua ChatGPT;
  chỉ có receipt thật đúng máy/thư mục mới báo đã thử thành công. Không chạy
  build/ghi file hoặc model provider chỉ để tô xanh setup.

Setup sẵn sàng khác với nghiệm thu bản phát hành: T01–T16, reboot/restore,
soak 24h và owner acceptance là gate của đội vận hành. Không bắt người dùng
thông thường chờ 24h để được dùng một bản đã đủ quyền, và không tự nâng
`LIVE_ACCEPTED` bằng wizard.

## 6. Trạng thái và thông báo lỗi

Không thêm workflow engine/DB readiness mới. Một lớp diễn giải thuần từ
snapshot, enrollment, registry/policy, account/binding và operation receipts
có timestamp. Form draft chỉ lưu lựa chọn UI; không có `ready=true` bền vững
riêng của wizard. `firstRunCompleted`/checkbox hướng dẫn không chứng minh quyền.

Mỗi kết quả gồm: trạng thái ngắn, lời giải thích, người xử lý, hành động chính,
thời gian quan sát, chi tiết kỹ thuật. Các lỗi song song vẫn xem được ở chi
tiết; banner ưu tiên blocker của bước đang làm, không tạo một thứ tự chặn giả
cho những bước độc lập.

| Tình huống | Lời nói với người dùng | Hành động đúng |
|---|---|---|
| Pending approval | Máy này đang chờ Ubuntu duyệt | Mở trang quản trị; theo dõi request cũ |
| Server cũ/recovery | Máy chủ đang cần bảo trì | Xem việc cần làm trên Ubuntu; không restart Windows |
| Chưa có folder | Chưa chọn thư mục để làm việc | Chọn thư mục |
| Policy thiếu/không khớp | Quyền đã chọn chưa được áp dụng | Xem phạm vi và áp dụng theo workflow local |
| Account chưa liên kết | Tài khoản chưa được phép dùng thư mục này | Liên kết/chọn target theo evidence |
| Epoch hết hạn | Lần chuẩn bị trước chưa hoàn tất; cấu hình còn nguyên | Kiểm tra và tiếp tục bằng operation mới khi hợp lệ |
| Installation mismatch | Công cụ đang kiểm tra một bản cài khác | Xem bản cài đúng; xác minh owner, không kill theo tên |
| Source closure thiếu | Bản cập nhật chưa được xác nhận | Workflow nghiệm thu/cập nhật của quản trị viên |
| Active work | Có công việc đang chạy nên chưa áp dụng thay đổi | Xem công việc; không tự stop |
| Snapshot stale/unknown | Chưa kiểm tra lại được | Hiện thời điểm gần nhất và Kiểm tra lại |
| FORBIDDEN chưa rõ nguyên nhân | Phiên này chưa được cấp quyền | Chẩn đoán scope/account; không đoán hết hạn rồi tự cấp context |

Nút **Kiểm tra lại** không trở thành **Sửa tất cả**. Sửa chữa hiển thị đúng một
thao tác phù hợp, ảnh hưởng và điều kiện dừng. Mã lỗi không bị bỏ: chuyển vào
“Chi tiết kỹ thuật / Sao chép báo cáo”. Báo cáo phải theo allowlist, loại secret,
cookie/Authorization/DPAPI payload và nội dung file; path local mặc định che,
có preview trước khi chia sẻ. Không tự gửi báo cáo ra mạng.

## 7. Cách lưu cấu hình và hành vi ứng dụng

- Theme và preference đơn giản: lưu ngay từng field; hiện “Đang lưu/Đã lưu/
  Chưa lưu được”; failure khôi phục hoặc giữ draft rõ ràng, không im lặng.
- Mạng/cổng: chỉnh trong form nhỏ có **Lưu thay đổi**. Nếu cần restart, ghi
  “Đã lưu — chưa áp dụng”, cho chọn thời điểm. Không dùng save toàn bộ DOM.
- Quyền, đổi server, thu hồi, rotation, xoá phiên đăng nhập: confirmation riêng
  và snapshot trước thao tác; không gom vào autosave preference.
- `startWithWindows`, `autoStartServices`, `keepRunningOnClose` vẫn là ba hành
  vi khác nhau. Nhãn lần lượt là “Mở sau khi đăng nhập Windows”, “Tự chuẩn bị
  kết nối khi mở ứng dụng”, “Tiếp tục chạy khi đóng cửa sổ”. Không quảng cáo
  chạy khi logout/Session 0. Giữ giá trị cũ; cài mới không bật tự chạy nếu chưa
  có consent. Startup source development vẫn bị giới hạn theo contract.
- Theme theo hệ thống là đề xuất tiện ích, không giả đang có: config hiện chỉ
  light/dark. Có thể làm sau, không chặn bản đơn giản đầu tiên.
- Report interval vào nâng cao; tool mode smart-v3 cố định chỉ cần ghi ở About.
- Reconcile UI dùng một chủ sở hữu refresh và cache; không thêm nhiều timer
  tạo subprocess/SSH/heartbeat cho từng thẻ. Resume khi mở lại; backoff offline;
  stale không giữ màu xanh. Lưu receipt thành công dù refresh kế tiếp lỗi.

## 8. Phần triển khai lại và phần tái sử dụng

| Công việc | Cách triển khai nhỏ nhất | Tình trạng |
|---|---|---|
| Thông báo/next action nhất quán | Presenter thuần dùng snapshot hiện có, test matrix | Đã có setup presenter 4 bước và test source |
| Health central đúng role | Sửa `healthService.js`, tái dùng readiness/ownership thay kiểm Tunnel direct | Đã triển khai + test central/direct |
| Form độc lập | Sửa renderer event handlers; allowlist settings/main + atomic SettingsStore | Preference đơn giản đã lưu từng field; form quyền/mạng vẫn cần xác nhận riêng |
| Kết nối/đăng ký/retry | Tái dùng `controlPlaneEnrollment`, node-agent, Manager IPC và journal | Có nền tảng |
| Resume wizard + server URL | Diễn giải state sau reload; receipt server_origin được kiểm tra trước hiển thị | Setup 4 bước + origin Ubuntu được lưu/khôi phục; receipt binding vẫn phụ thuộc Ubuntu |
| Policy preset không cần CLI | Adapter Manager-only cho policy đang có, metadata đã xác thực, scope preview | Khoảng trống backend cần đóng |
| Account/binding status trong app | Tái dùng inventory/auth server; chỉ bổ sung projection/API tối thiểu còn thiếu | Đã có node-authenticated `authority-status` path-free, parser/IPC/UI và focused tests; chưa xác minh server deployed |
| Tách onboarding wait khỏi activation TTL | Tái dùng coordinator/handoff, chỉnh ranh giới chuẩn bị nếu cần | Thay đổi lifecycle có rủi ro, không phải CSS |
| Chẩn đoán đúng packaged installation | Reuse runtime paths/IPC và Supervisor của bản cài | Có nền tảng; không dùng dev CLI thay thế |
| Báo cáo hỗ trợ | Projection allowlist + preview/copy/export có chủ đích | Cần viết |

Không đổi public smart-v3 tools, thêm controller/server executor, hoặc rewrite
Electron sang React/WinUI trong đợt này. Không thêm một config JSON song song.
Không ẩn DOM rác chỉ để giữ test khóa theo layout cũ.

## 9. Các đợt triển khai và điều kiện xong

### P0 — Chốt thiết kế (đã hoàn thành)

- Audit, phương án này và bản phác tương tác với trạng thái giả lập.
- Chốt nhóm màn hình, wording, các quyền và state fixtures.
- Bản phác không gọi server, không phản ánh live status, không tạo credential.

### P1 — Sửa điều gây hiểu sai trước (đã triển khai nền tảng)

- Health theo role; tên nút đúng side effect; trạng thái đồng nhất; save từng
  preference; hiện blocker hiện hành thay vì chỉ Degraded.
- Test nhỏ: settings, health-service, handoff-ui, presenter truthfulness.
- Đã làm: central health không đòi key/Tunnel/Tunnel client Windows; route Ubuntu fail-closed; nút central mở Kết nối thay vì gọi start/restart; URL origin không bí mật được lưu để khôi phục; theme/startup/background/report interval gửi từng field với trạng thái lưu.
- Exit còn lại: test tương tác renderer đầy đủ, packaged Windows và kiểm tra cài đặt nâng cấp.

### P2 — Một Cài đặt và wizard có thể tiếp tục (đã triển khai UI nền tảng)

- Gộp routes/form; tiếng Việt thống nhất; thư mục/path rõ; nâng cao thu gọn.
- Continue đúng request/operation; không mất input khi chuyển nhóm, không
  duplicate effect; pending là trạng thái chờ bình thường, không spinner vô hạn.
- Đã làm: một mục Cài đặt cố định, nhóm Kết nối/Thư mục & quyền/Ứng dụng/Hỗ trợ, setup 4 bước có thể tiếp tục và CTA theo blocker; pending không biến thành success; workspace central dùng preset “Chỉ xem / Làm việc với mã nguồn / Tùy chỉnh” và giấu ID opaque khỏi inventory thường.
- Bước 3 trên UI dùng nhãn **Liên kết & quyền** cho central và **Kiểm tra kết nối** cho direct legacy. `authorityReady` chỉ là bằng chứng policy local/route hiện tại; không được diễn giải thành OAuth principal hoặc account binding đã liên kết.
- Đã nối projection `POST /v1/nodes/{device_id}/authority-status` qua node-agent/IPC. Card chỉ hiển thị “Chưa có liên kết tài khoản”, “Đã có target được cấp”, “Binding bị thu hồi”, “Workspace chưa được đăng ký” hoặc trạng thái chờ/chặn; không hiển thị ID/path/credential. Projection là bằng chứng riêng, chưa thay thế phép thử ChatGPT.
- Exit còn lại: policy preset/lifecycle và xác minh server deployed; không báo completed khi backend chưa có bằng chứng.

### Preview giao diện (chỉ để xem bố cục)

Preview tĩnh phải bật rõ ràng bằng query `preview=1`; đây là dữ liệu mẫu, không phải
runtime proof. Ví dụ chạy từ thư mục repo:

```text
python -m http.server 8123 --bind 127.0.0.1
http://127.0.0.1:8123/renderer/index.html?preview=1&theme=light#system
```

Mở `index.html` không có `preview=1` sẽ cố ý hiển thị **IPC/preload chưa kết nối**
với trạng thái `MCP OFF`, `Chưa chọn thư mục`; cơ chế này bảo vệ bản Electron thật
khỏi việc tự tạo preview khỏe khi preload bị mất.

### P3 — Bỏ các thao tác CLI trong cấu hình bình thường (đang triển khai)

- Nối policy preset và chuẩn bị runtime qua các
  service hỗ trợ; review phạm vi quyền, target pin và retry safety.
- Account/binding projection node-safe đã hoàn thành ở source: chỉ đọc, xác thực
  bằng node credential, strict schema, không trả path/owner/OAuth ID; cần chạy
  tiếp với server Ubuntu packaged để xác minh hợp đồng triển khai.
- Tách chờ duyệt/login khỏi execution TTL; giữ code acceptance riêng.
- Test mới cho policy adapters, identity/source mismatch, active tasks, permission
  replacement, response loss và không tự retry effect unknown.
- Exit: một Windows user và một operator Ubuntu hoàn thành setup mà không
  copy ID/token/JSON hoặc chạy shell. Server deploy/OAuth vẫn là điều kiện
  quản trị thật, không thể được khắc phục chỉ bằng đổi giao diện Windows.

### P4 — Đóng gói, kiểm chứng và đồng bộ

- Freeze source rồi build Windows/verify resources/smoke trên exact commit.
  Test cài mới và nâng cấp profile thật có phê duyệt; backup được bảo vệ trước
  migration. Không sửa riêng HTML hoặc app.asar trên máy Windows.
- Bản Windows, Ubuntu package (nếu backend đổi), source GitHub phải có revision/
  hash compatibility receipt. Chỉ docs/CSS đổi không tự buộc deploy Ubuntu;
  server contract đổi thì deploy server tương thích trước bằng runbook có backup.
- Windows checkout `E:\DEV\Codex-web` nhận cùng source bằng fast-forward sau
  khi đã xử lý evidence/concurrent changes đúng quy trình. Không reset/clean để
  bỏ ledger; không tạo worktree/branch tồn đọng ngoài nhu cầu được chấp thuận.
- Trước mỗi commit/push: stage/check `.coding-tools` theo AGENTS.md; chỉ hai
  SQLite sidecars được ngoại lệ; phát hiện secret phải dừng delivery.
- Candidate pass mới cài có kiểm soát. Giữ data root, credentials, registry,
  accepted-code evidence và policy. Rollback không tự đưa quyền/generation cũ
  đã thu hồi trở lại; DB restore là thao tác khác với rollback app.

Không chốt số ngày chắc chắn khi P3 còn gap authorization/lifecycle. Có thể giao
P1/P2 trước như bản dễ hiểu hơn, nhưng chỉ gọi “thiết lập không cần CLI hoàn
chỉnh” khi P3/P4 có bằng chứng. Deploy, push và service change cần authority
theo cửa sổ triển khai, không được suy ra từ việc duyệt bản thiết kế.

## 10. Ma trận nghiệm thu tối thiểu

Các mục sau là **mục tiêu kiểm thử tương lai**, chưa PASS bởi bản kế hoạch.

1. Cài mới central: không key/Tunnel/context/JSON/CLI trên Windows.
2. Profile hiện tại đang pending: giữ URL/request và tiếp tục đúng bước.
3. Chờ duyệt một giờ rồi đóng/mở: không tạo request/epoch lặp; TTL bảo vệ
   execution không bị nới vô hạn.
4. Double click/retry/lost ACK: không duplicate registration/rotation/process.
5. Đăng ký đã thành công nhưng refresh lỗi: vẫn giữ kết quả đã commit.
6. Preference thay đổi: chỉ field đó lưu; Save/Applied có nghĩa nhất quán.
7. Central local process đang sống nhưng route/policy/admission thiếu: không
   báo sẵn sàng nhận việc; readonly user không bị yêu cầu write/exec để ready.
8. Revoked/expired/mismatch/unknown: không đổi thành offline hay tự sửa quyền.
9. Task đang chạy: thay quyền/path có impact rõ, không retarget/stop không phép.
10. “Kiểm tra” không thay process, port, credential, policy hoặc dispatch action.
11. Preset quyền hiển thị đúng phạm vi thực; không cấp wildcard toàn root/argv
    tùy ý. Policy chưa đủ thì không báo hoàn tất.
12. Nâng cấp giữ AppData/DPAPI/workspaces/evidence, không đòi cài lại từ đầu.
13. Readiness/canary đúng installed artifact; hai client thật cùng tài khoản
    nhìn thấy đúng target, không lộ path local hoặc credential tới server.
14. App chạy sau login/reconnect theo preference; không hứa chạy khi logout.
15. Dùng được bằng bàn phím và screen reader, focus thấy rõ; lỗi có chữ không
    chỉ màu; zoom 200%, cửa sổ Windows nhỏ và light/dark không che CTA.
16. Thử với khoảng 5 người chưa biết MCP: ít nhất 4 người chọn được next action
    đúng mà không cần người hướng dẫn chỉ tab/lệnh. Mục tiêu thao tác chủ động
    dưới 5 phút với server sẵn sàng, không tính thời gian chờ duyệt/tải/cài.

Tận dụng các suite `settings`, `health-service`, `control-plane-enrollment`,
`central-executor-handoff-ui`, `control-center-manager`, `control-center-truthfulness`,
`control-center-signal-failsafe`. Thêm DOM interaction tests cho hành vi mới;
không chỉ regex chốt ID/chuỗi UI. Chỉ chạy lifecycle/full-clean suite khi đổi
boundary đó; full release gates tại P4, không chạy full stack cho docs-only.

## 11. Cơ sở tham khảo và điểm cố ý khác

- [Microsoft: Guidelines for app settings](https://learn.microsoft.com/en-us/windows/apps/design/app-settings/guidelines-for-app-settings): dùng một điểm vào, mặc định hợp lý, nhóm lựa chọn liên quan, và giữ tác vụ thường ngày ngoài Settings. Áp dụng nguyên tắc bố trí, không chuyển công nghệ app sang WinUI.
- [W3C WAI: Multi-page forms](https://www.w3.org/WAI/tutorials/forms/multi-page/): chia biểu mẫu dài theo bước logic, có tiến độ và tiếp tục dữ liệu đã nhập. Onboarding chờ con người được tách khỏi timeout bảo vệ thay process.

Preference vô hại có thể lưu tức thời; quyền/identity/restart vẫn cần xác nhận
riêng vì có tác động vượt một tùy chọn giao diện. Các trường direct không liên
quan central nằm trong luồng nâng cao tương ứng, không thành hàng loạt control
disabled trên trang cơ bản. Đây là lựa chọn theo ranh giới của sản phẩm này.

## 12. Checkpoint bàn giao

- Hoàn thành: audit source, phương án, bản phác UI cô lập, P1 nền tảng, P2 UI nền tảng, preset quyền dễ hiểu và projection account/binding node-safe; `npm test` pass 867, skip 16 mục Windows-only, kiểm tra secret pass.
- Chưa làm: policy adapter/lifecycle P3 và test tương tác renderer thực tế, P4 đóng gói và test runtime Windows mới, deploy/approve/OAuth, nghiệm thu LIVE. Projection account/binding mới có bằng chứng source/focused test, chưa xác minh server deployed. Preset UI đã có nhưng vẫn chỉ là inventory capability; không được gọi là policy authority.
- Git đầu lượt: `main@50ae5c4`, có ledger runtime dirty từ trước; không thay
  ledger bằng tay, không tạo commit/branch hoặc push trong bước thiết kế.
- Bằng chứng mới: `npm test` **867 pass, 16 skip Windows-only, 0 fail**; focused Settings/authority/health **10 pass**; Control Plane store/HTTP **43 pass**; preview `index.html?preview=1#system` đã mở được và không có lỗi tải resource.
- Bước tiếp theo: hoàn thiện policy adapter + lifecycle, chạy packaged Windows/Ubuntu contract test, rồi mới build/đồng bộ artifact exact theo P4.
