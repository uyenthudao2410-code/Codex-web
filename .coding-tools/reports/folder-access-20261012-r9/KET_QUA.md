# Kết quả sửa máy DESKTOP-63643J4 — 12/10/2026

## Đã chạy thành công

Thư mục đang kết nối là **E:\DEV\Autocad**. Bản local **r9d** đang READY/OPEN; shortcut Desktop và Start Menu đều mở bản này.

| Kiểm tra qua Ubuntu MCP | Kết quả |
| --- | --- |
| Tạo file, đọc lại | PASS |
| Sửa file bằng PATCH, đọc lại | PASS |
| Node | Exit 0 — v24.19.0 |
| Thư mục chạy lệnh | C:\CodexWorkspace\share-0, ánh xạ đúng Autocad |
| Node đọc và tính SHA-256 file vừa sửa | Khớp |
| .NET | Exit 0 — 10.0.102 |

File kiểm thử: `E:\DEV\Autocad\mcp-access-smoke-20261012-r9d.txt`, 63 byte, SHA-256 `3a42ea5c3e68101db07001a265b9fb4fcbbc0021ed965139dcf10ea99ba73023`.

Luồng sử dụng: **Thêm thư mục → chọn thư mục dự án → xác nhận một lần**. Mặc định có quyền đọc, sửa và chạy lệnh. Việc thêm hoặc kiểm tra quyền thư mục không mở Windows Sandbox; lệnh thật sử dụng môi trường Sandbox. Connector trung tâm hiện chọn một workspace mỗi lần; chọn thư mục khác sẽ chuyển binding theo đúng thư mục đó.

## Trạng thái cuối

- Máy chủ `svhome` đã triển khai bản sửa và restart theo xác nhận trước đó. MCP online, tunnel HTTP 200, kiểm tra SQLite đạt, cơ chế gia hạn theo workspace đang chọn hoạt động.
- Các task kiểm thử trung tâm đã đóng, writer đã giải phóng; generation Autocad không còn action chưa kết thúc. Các Job chạy lệnh đã hoàn tất.
- Không sửa mã chức năng AutoCAD. Hai file kiểm thử r9c/r9d và `.coding-tools` được giữ làm bằng chứng.
- Repo Codex-web vẫn ở `main`, HEAD `7999c4151cb501db86f2e4d0a2275d33fc248324`, khớp `main` hiện tại trên GitHub qua `git ls-remote`. Các thay đổi local được giữ nguyên. Không commit, push hay phát hành installer.
- Package kiểm tra 91 file ứng dụng / 298 resources / 9 adapters và smoke bản đóng gói đạt. Các test tập trung cho luồng chọn thư mục, đường dẫn file và chạy lệnh đạt; `git diff --check`, kiểm tra dữ liệu nhạy cảm và chính sách giữ lịch sử `.coding-tools` đều PASS.

Giới hạn còn lại: đây là candidate local. Phiên nghiệm thu nội bộ của PATCH còn `ACCEPTING` vì chưa có bằng chứng kiểm thử cùng wave; không được coi là đã ACCEPTED. Audit qua gateway hiện có lúc 16:43 xác nhận trạng thái này, không sửa lease hay ledger; helper đã thoát. `ACCEPTING` riêng nó không chặn chuyển thư mục, khác với lệnh/workflow đang chạy. Các thao tác đọc/ghi/sửa/chạy đã hoàn tất. Hai action UNKNOWN lịch sử của generation cũ vẫn được giữ nguyên và cách ly.

## Bằng chứng

- [Biên nhận tổng hợp](completion-r9d.json)
- [Kiểm tra Git và chính sách lưu bằng chứng](final-validation-r9d.json)
- [File qua MCP](canary/autocad-folder-access-receipt-r9d-379870e54349464ca9bf8c1d03dd92e0.ndjson)
- [Node và .NET qua MCP](canary/autocad-exec-remaining-receipt-r9d-912d867d0dff4ce98aa3b3220a096319.ndjson)
- [Máy chủ cuối](final-server-surface-r9d-1791797626010.json)
- [Runtime cuối](r9d-transition/final-machine-observation-activation-mv514if9-7a4fabe0ce77708f8be03ff43a6518db-1791797633598.json)
- [Shortcut](r9d-transition/coding-tools-shortcuts-after-r9d.json)
- [Audit phiên nghiệm thu còn chờ](r9d-transition/existing-gateway-canary-audit-1791798210962.json)
