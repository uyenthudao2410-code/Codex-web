# Kết quả sửa hiển thị target — 12/10/2026

## Kết quả

Đã cài và khởi động bản local `machine-folder-access-1012-r9e` trên
`DESKTOP-63643J4`. Runtime READY/OPEN, MCP hoạt động; target được cấp vẫn là
`E:\DEV\Autocad`. Sidebar, Thiết bị, bảng thực thi, thư mục được chọn và thông
tin thư mục cùng render đường dẫn Autocad trên dữ liệu live.

Lỗi gốc: sidebar và Thiết bị lấy workspace mặc định của runtime
(`E:\DEV\Codex-web`), trong khi bảng thực thi lấy binding đang hoạt động.
`renderWorkspaceTarget` nay dùng một target trung tâm đã xác minh cho các nhãn
liên quan, đồng bộ cả lần render đầy đủ lẫn các cập nhật bất đồng bộ. Khi nguồn
heartbeat/quyền cũ, mất quyền hoặc sai generation, nhãn target bị xóa. Git trong
Thiết bị được ghi rõ là **Git ứng dụng**.

## Bằng chứng

- 96 kiểm tra tập trung đạt; syntax JavaScript và kiểm tra whitespace đạt.
- Package được xác minh đúng 91 tệp app, 298 resources và 9 adapter; smoke test
  package cô lập đạt. Native/executor/adapter khớp r9d đã kiểm read/write/PATCH
  và command thật. Build cũng tái tạo ba icon theo lệnh build hiện có.
- [Renderer trên dữ liệu live](live-renderer-verification-1791800160320.json):
  năm nhãn đều `E:\DEV\Autocad`, quyền read/write/exec bật, target fresh/ready/
  dispatchable, heartbeat cũ xóa nhãn, epoch giữ nguyên. Chạy đúng các hàm render
  của package trong DOM bộ nhớ; chưa phải ảnh trực tiếp cửa sổ Windows.
- [Quan sát runtime cuối](r9e-transition/final-machine-observation-activation-mv53i8gp-f06eeb5b46a11d2cf7ebdc9445606937-1791800187814.json):
  READY/OPEN, fullyReady/MCP/native true, UI và Host revision current, descriptor
  ổn định, không có tool/command/background/managed process đang hoạt động.
- [Quan sát Ubuntu cuối](final-server-observation-1791800243955.json): target
  Autocad ready/online/dispatchable, read/write/exec true, 0 task chưa đóng,
  0 writer chưa giải phóng, 0 action chưa giải quyết ở generation hiện tại;
  SQLite integrity ok. Binding/pilot/generation cũ của target giữ nguyên.
- Hai shortcut Desktop/Start Menu đã đổi sang đúng r9e; thuộc tính khác được
  đối chiếu và giữ nguyên, bản gốc đã sao lưu trong thư mục transition.

## Trạng thái và giới hạn

- Git: `main @ 7999c4151cb501db86f2e4d0a2275d33fc248324`, vẫn dirty; các sửa đổi
  và evidence trước đó được giữ. Không commit, push, tag hay release.
- Có thao tác local: ordinary stop một lần, retire đúng UI/Host r9d, cài
  supervisor r9e, mở UI, full refresh và cập nhật shortcut. Wave này không
  deploy/restart hay sửa cấu hình server Ubuntu.
- Công cụ evidence đọc nhầm full snapshot sau stop và báo
  `ORDINARY_STOP_NOT_CONFIRMED`; lỗi và producer gốc giữ nguyên. Xác nhận bổ
  sung đọc trạng thái stopped/census thật, hash-bind producer và failure, không
  gọi lại stop. Xem [trình tự triển khai](r9e-transition/README-transition.md).
- Một lệnh complete báo `RUNTIME_BUSY` khi worker activation đang chạy; worker
  tự hoàn tất READY/OPEN sau hai giây. Không còn blocker triển khai local.
- Các run lịch sử chờ acceptance, canary Autocad `ACCEPTING` và hai action
  UNKNOWN bị cách ly vẫn là lịch sử chưa hoàn tất; không sửa ledger để đóng
  giả. Chúng không có command/background sống trong census hiện tại.
- Đây là bản candidate được kích hoạt trên máy này; chưa là installer/release
  công bố. Giữ thư mục r9e vì shortcut và supervisor đang dùng nó.

## Tệp thay đổi trong wave

`renderer/app.js`, `renderer/index.html`, hai test folder/manager,
`docs/CURRENT_STATE.md`, ba icon do build và evidence dưới thư mục báo cáo này.
Không sửa mã chức năng Autocad. Việc chạy command thật không được lặp lại chỉ
để kiểm nhãn; proof r9d được giữ vì backend/executor không đổi.

Bước tiếp theo: dùng **Coding Tools MCP** từ shortcut đã cập nhật và làm việc
với target Autocad hiện tại. Không còn bước cấp quyền hay chuyển pilot cần làm
trong wave này.
