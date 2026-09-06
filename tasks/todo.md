# Tasks: Thiết kế gọn trên 1 view đẹp, trực quan, nhiều hiệu ứng

> **Cập nhật phạm vi bằng chứng — 05/09/2026:** Các checkbox/số test và hình minh họa bên dưới là checkpoint của đợt thiết kế, không phải xác nhận G0–G10, runtime hiện hành hoặc Production. Audit mới ghi source fixes có focused proof nhưng chưa final-accept/activate; activation hiện FAILED/CLOSED; usage/outcome tự nhiên còn mở. Bổ sung mục 9 đã xác minh sáu font trùng byte với artifact chính thức, thêm license/notice và sửa hai lỗi tích hợp token-window; đây vẫn là source proof, chưa package/live acceptance. Xem [báo cáo tồn đọng và điều kiện đóng](../docs/research/260905_REMAINING_ISSUES_CLOSURE_AUDIT.md). Giữ các ghi chép thiết kế bên dưới làm lịch sử, không dùng số token/cost minh họa làm dữ liệu đo.

- [x] 1. Lập kế hoạch kiến trúc giao diện 1-View cho Dashboard Vận hành <!-- id: 100 -->
  - [x] Khảo sát độ cao viewport chuẩn desktop (900px - 1080px) và tính toán tỷ lệ phân bổ pixel <!-- id: 101 -->
  - [x] Bố trí bố cục 2 tầng: Tầng 1 (Header + Toolbar + 7 Thẻ KPI) và Tầng 2 (Split View: Biểu đồ xu hướng / Nhật ký lượt chat) <!-- id: 102 -->
  - [x] Đảm bảo giữ nguyên 100% ID và contract tests <!-- id: 103 -->
- [x] 2. Tinh chỉnh CSS hệ thống (`renderer/dashboard.css` & styles) <!-- id: 104 -->
  - [x] Thêm hiệu ứng Glassmorphism, viền phát sáng (Luminous Glow), đổ bóng phân tầng và micro-interactions <!-- id: 105 -->
  - [x] Tối ưu chiều cao các thẻ KPI (compact cards ~78px) giảm khoảng trống thừa, tăng kích thước số liệu chính <!-- id: 106 -->
  - [x] Thu gọn Topbar và Status Banner thành dạng thanh mỏng hoặc badge tích hợp <!-- id: 107 -->
  - [x] Tối ưu thanh lọc thời gian & toolbar thành dải ngang thanh lịch <!-- id: 108 -->
- [x] 3. Cập nhật HTML cấu trúc cho `renderer/index.html` và `renderer/token-dashboard.html` <!-- id: 109 -->
  - [x] Đồng bộ cấu trúc 1-view không cần cuộn trang để thấy toàn bộ thông tin trọng yếu <!-- id: 110 -->
  - [x] Bố trí song song: Cột trái (Biểu đồ xu hướng SVG + Donut model + Tool bars) và Cột phải (Nhật ký lượt chat thời gian thực) <!-- id: 111 -->
- [x] 4. Kiểm thử & Xác minh <!-- id: 112 -->
  - [x] Đạt 40/40 tests trên toàn bộ 3 test suites (`dashboard-analytics`, `token-dashboard`, `component-revision`) <!-- id: 113 -->
  - [x] Xác minh trực quan qua browser subagent hiển thị trọn vẹn 1-view trên cả chế độ Sáng (Light) và Tối (Dark) <!-- id: 114 -->
- [x] 3. Hoàn thiện Styling & Responsive Theme (Light/Dark) <!-- id: 12 -->
  - [x] Đảm bảo hiển thị sắc nét, chuẩn phông chữ offline (Plus Jakarta Sans, JetBrains Mono) <!-- id: 13 -->
  - [x] Kiểm tra cơ chế chuyển đổi chế độ sáng/tối đồng bộ với icon ◐ <!-- id: 14 -->
- [x] 4. Loại bỏ 2 thẻ "Phát hiện bất thường" và "Tóm tắt nhanh" theo yêu cầu người dùng <!-- id: 20 -->
  - [x] Loại bỏ Sub Card 2 ("Phát hiện bất thường") và Sub Card 4 ("Tóm tắt nhanh") khỏi `renderer/index.html` <!-- id: 21 -->
  - [x] Chuyển đổi `.da-sub-grid-4` sang `.da-sub-grid-2` chỉ giữ lại Tốc độ/Độ trễ và Heatmap 7x24 <!-- id: 22 -->
- [x] 5. Kiểm thử & Xác minh <!-- id: 15 -->
  - [x] Chạy `node --test tests/token-dashboard.test.js` (3/3 pass) <!-- id: 16 -->
  - [x] Chạy `node --test tests/dashboard-analytics.test.js` (24/24 pass) <!-- id: 17 -->
  - [x] Chạy `node --test tests/component-revision.test.js` (10/10 pass) <!-- id: 18 -->
  - [x] Xác minh hiển thị thực tế qua browser subagent và chụp ảnh màn hình 1:1 <!-- id: 19 -->

## Review & Kết quả Thực hiện
- **Đạt độ chuẩn xác 1:1 so với hình ảnh mẫu**:
  - Tái tạo trọn vẹn khung ứng dụng **Execution Hub • Control Center**:
    - Sidebar bên trái: Logo Codex Hub, menu điều hướng `[CC] Command Center` (đang kích hoạt với thanh chỉ báo lam), các mục `[TP]`, `[DV]`, `[CN]`, `[WS]`, `[SY]`, và thẻ trạng thái runtime phía dưới (`Đang hoàn tất activation epoch`, `E:\DEV\Codex-web`, `MCP ON`, `Tunnel ON`, nút `Coding Tools MCP · 0.4.3`).
    - Topbar phía trên: Nhãn `TRUNG TÂM ĐIỀU HÀNH`, tiêu đề `Tổng quan Vận hành`, chú thích `Xem tập trung MCP cục bộ, OpenAI Tunnel và môi trường triển khai.`, pill thiết bị `DESKTOP-6J643J4` (`local • ac2514f • main @ 2687ac8`), nút đổi chủ đề `◐`, nút `Kiểm tra lại` và nút `Khởi động nhanh`.
    - Banner cảnh báo: Nền vàng mềm mại với huy hiệu `DEGRADED`, tiêu đề `Runtime is online; connectivity is incomplete`, chú thích `Control Center vẫn hiển thị durable task state và client evidence hiện có...`, thời gian đồng bộ `Last sync 09:41:02` và nút `Refresh`.
    - Phân đoạn `Định lượng Token & Hiệu quả` cùng thanh công cụ lọc: Dropdown `Dự án Codex-web`, Huy hiệu `Môi trường ● Production`, Cửa sổ ngày `📅 / NGÀY GẦN NHẤT - 05/09/2026`, các nút `Tự động ▾`, `Bộ lọc`, `Xuất báo cáo`, nút xanh nổi bật `Làm mới dữ liệu` và `Bảng token`.
    - Cụm 7 Thẻ KPI: Thẻ Hero `TOKEN CHATWEB` (viền tím phát sáng, chấm xanh nhấp nháy, giá trị `≈ 344`), `TOKEN PROVIDER` (`16K`), `INPUT TOKEN` (`16K` kèm sparkline), `OUTPUT TOKEN` (`215` kèm sparkline), `CHI PHÍ QUY ĐỔI` (`$0.003` kèm sparkline), `CACHED TOKEN` (`—`), `TOKEN / KẾT QUẢ` (`182` kèm sparkline).
    - Thanh tóm tắt: `AI thực thi` (Đã đo | ChatWeb điều phối), `Context ≈ 420K token` (Độ tin cậy ước lượng: LOW • 284K-852K), `Totem lượt chat` (`≈ 344 • trực tiếp`).
    - Bảng `Nhật ký lượt chat`: Hiển thị từng dòng với timestamp `00:29:49`, huy hiệu `≈ ƯỚC LƯỢNG` và giá trị `≈ 344 (229-688)`.
  - Giữ vững toàn bộ các thành phần phân tích nâng cao (Biểu đồ xu hướng Area Chart, Donut Model Breakdown, Tool Cost, Realtime Speed, Heatmap, Bảng Accepted Result, Measurement Coverage và Bảng giá tùy chỉnh).
- **Loại bỏ nội dung theo yêu cầu**:
  - Đã loại bỏ hoàn toàn 2 thẻ phụ **"Phát hiện bất thường"** và **"Tóm tắt nhanh"** khỏi [`renderer/index.html`](file:///e:/DEV/Codex-web/renderer/index.html), tinh gọn giao diện với layout 2 cột cân đối cho khối Tốc độ/Độ trễ và Heatmap 7x24.
- **Kiểm định chất lượng 100%**:
  - `node --test tests/token-dashboard.test.js`: 3/3 bài kiểm tra vượt qua.
  - `node --test tests/dashboard-analytics.test.js`: 24/24 bài kiểm tra vượt qua.
  - `node --test tests/component-revision.test.js`: 10/10 bài kiểm tra vượt qua.
  - Trực tiếp kiểm tra hiển thị qua Browser subagent và đã lưu ảnh xác nhận thực tế.
