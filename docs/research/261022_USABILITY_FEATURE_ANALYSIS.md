# Đề xuất làm Codex Hub dễ sử dụng hơn

Ngày khảo sát: **22/10/2026**, quan sát nguồn lúc **14:10 giờ Việt Nam (07:10 UTC)**.

## 1. Phạm vi và kết luận

Đợt này tạo **phân tích và bản mẫu tương tác** để xem xét luồng sử dụng. Đây là đề xuất thiết kế, chưa phải tính năng đã triển khai, bản cài đặt đã kiểm chứng hay kết quả thử nghiệm với người dùng.

Hướng ưu tiên: **gom thao tác theo công việc, làm rõ trạng thái và bước tiếp theo**. Màn hình chính đề xuất có ba điểm đến: **Làm việc · Lịch sử · Cài đặt**. Dự án và máy đang dùng luôn hiện ở đầu trang; mỗi trạng thái có một hành động chính phù hợp.

Không cần đổi Electron sang React/Tauri hoặc nhập nguyên hệ thống chat của kho tham khảo. Tận dụng setup, quyền, Job, lịch sử và continuity hiện có; đưa thông tin kỹ thuật vào phần mở rộng.

## 2. Cơ sở bằng chứng

| Nguồn | Phiên bản và mức bằng chứng |
|---|---|
| Kho local `E:\DEV\Codex-web` | Nhánh `main`, HEAD `5c5e207265f56a69b72f16dd78c4d2951f382609`; worktree đã có thay đổi app, runtime và `.coding-tools` trước khảo sát. Nhận xét local dựa trên nguồn đang có thay đổi, không chỉ HEAD. |
| Chat On Steroids | Commit `e4a26876e61775331d7d90f2d62867238b098bfc`; đọc README và các nguồn liên quan. Chưa chạy ứng dụng hoặc xác nhận bản đóng gói. |
| WebCodex upstream | Commit `2bac8248a2e635022ae9c636fc1287bc01b6b833`; đọc Workbench, AddLocalProject và Runtime Console. Chỉ tham khảo cách tổ chức trải nghiệm. |

Chẩn đoán bên dưới là **suy luận từ nguồn**, chưa phải số liệu về số lần bấm hay độ khó đã đo. Không dùng projection hiệu năng hoặc ledger để suy ra trải nghiệm người dùng; nghiên cứu này không có phép đo tốc độ, chi phí hay billing.

## 3. Điểm gây khó hiểu cần xử lý

1. **Các bề mặt bị phân tán.** Điều hướng hiện có Thực thi mã, Sử dụng, Tác vụ & kết quả, Máy này và Cài đặt; setup còn có liên kết riêng giữa kết nối, thư mục và kiểm tra. Người dùng phải hiểu nơi quản lý từng thành phần. Xem [index.html](E:/DEV/Codex-web/renderer/index.html:27) và [các liên kết setup](E:/DEV/Codex-web/renderer/index.html:637).
2. **Ngôn ngữ và thuật ngữ chưa thống nhất.** Workspace strip tiếng Việt nhưng health hero còn “Checking”, “Reading Execution Hub state”, “Refresh”, “Restart runtime”. Các khái niệm authority, route và proof xuất hiện trong lời giới thiệu vận hành. Xem [health hero](E:/DEV/Codex-web/renderer/index.html:65).
3. **Có ứng viên lỗi nhãn và đích đến của nút chính.** `executionNextAction` khai báo `data-nav="system"` tại [index.html:63](E:/DEV/Codex-web/renderer/index.html:63). [app.js:866](E:/DEV/Codex-web/renderer/app.js:866) đổi nhãn sang theo dõi Tác vụ khi đủ điều kiện nhưng đoạn này không đổi đích; [handler điều hướng](E:/DEV/Codex-web/renderer/app.js:3630) đọc `data-nav`. Cần xác nhận trên UI bản chạy trước khi gọi đây là lỗi live.
4. **Chi tiết nghiên cứu chen vào màn tác vụ.** Panel P5-A0 Shadow A/A nằm cùng tác vụ và lịch sử trong [index.html:842](E:/DEV/Codex-web/renderer/index.html:842). Nên đặt dưới Chẩn đoán/Nghiên cứu và giữ khả năng truy cập.

Hai giới hạn quan trọng của kết luận: analytics được chuyển vào trang **Sử dụng** bằng [app.js:3842](E:/DEV/Codex-web/renderer/app.js:3842), nên không kết luận trang chính đang đầy biểu đồ. Nhóm Goal/Knowledge có `legacy-overview` và bị ẩn bởi [control-center.css:105](E:/DEV/Codex-web/renderer/control-center.css:105); không tính chúng là nội dung đang gây rối trên trang chính.

## 4. Đã có gì, cần bổ sung gì

| Khả năng | Hiện trạng nguồn local | Đề xuất |
|---|---|---|
| Thiết lập và bước tiếp theo | Đã có checklist, summary và `setupPrimaryAction`; [index.html:626](E:/DEV/Codex-web/renderer/index.html:626). | Gom về một luồng theo trạng thái thật, không xây wizard thứ hai. |
| Thư mục gần đây | Đã có MRU tối đa 50 trong [config.js:128](E:/DEV/Codex-web/electron/services/config.js:128). | Đưa danh sách gần đây vào bộ chọn dự án; hiển thị đầy đủ đường dẫn khi cần. |
| Quyền theo mẫu | Đã có Chỉ xem, Làm việc với mã nguồn, Tùy chỉnh; [index.html:690](E:/DEV/Codex-web/renderer/index.html:690). | Giải thích tác dụng và phạm vi máy/thư mục ngay tại hộp xác nhận. |
| Tạm dừng, tiếp tục, dừng và lịch sử | Đã có điều khiển tại [index.html:833](E:/DEV/Codex-web/renderer/index.html:833), handler tại [app.js:3799](E:/DEV/Codex-web/renderer/app.js:3799). | Đặt cạnh tác vụ hiện tại và chỉ cho thao tác hợp lệ; không tạo lifecycle song song. |
| Kết quả, file và build artifact | Renderer đã có phần dựng kết quả trong [app.js:1919](E:/DEV/Codex-web/renderer/app.js:1919). | Một lối vào Xem kết quả; bổ sung diff có phạm vi rõ khi dữ liệu hỗ trợ. |
| Tìm thao tác/cài đặt | Chưa xác nhận một luồng tìm thống nhất trong các phần đã khảo sát. | Bổ sung tìm kiếm Ctrl+K, gồm nhãn tiếng Việt không dấu; mở đúng trang và focus điều khiển. |
| Chuyển phiên và continuity | Đã có nền tảng continuity của sản phẩm; chưa kiểm chứng luồng khôi phục cho người dùng trong đợt này. | Xem trước bản tiếp tục từ dữ liệu hiện có; chỉ nối phiên/Job đã được xác nhận. |

## 5. Tính năng theo ưu tiên

### P0 — Luồng chính rõ ràng

- **Làm việc:** dự án, máy, trạng thái kết nối và tác vụ hiện tại. Một nút chính theo bảng trạng thái bên dưới. Dùng tên tiếng Việt nhất quán, giữ dữ liệu kỹ thuật nguyên bản trong Chi tiết.
- **Bộ chọn dự án:** tận dụng MRU; chuyển dự án phải cập nhật cả nhãn, quyền và đích thao tác. Không ngầm chọn dự án khác khi đích đã mất.
- **Thiết lập theo phần còn thiếu:** kết nối, chọn thư mục/quyền, xác minh. Quyền đã cấp và thao tác đã chạy thành công phải là hai thông tin riêng.
- **Lịch sử:** các công việc đã chạy, kết quả và bộ lọc dự án; Sử dụng là mục phụ. **Cài đặt:** kết nối, quyền, giao diện; chẩn đoán và nghiên cứu trong phần mở rộng. Máy hiện tại mở từ đầu trang.

| Trạng thái quan sát được | Hành động chính đề xuất | Điều kiện cần giữ |
|---|---|---|
| Chưa chọn dự án | Chọn dự án | Hiển thị đúng máy và đường dẫn. |
| Thiếu kết nối | Kiểm tra kết nối | Mở đúng phần lỗi; không tự khởi động lại dịch vụ. |
| Chờ cấp quyền | Xem yêu cầu cấp quyền | Đúng máy, thư mục, quyền và bên có thẩm quyền duyệt. |
| Chưa kiểm chứng thao tác | Xem bước xác minh | Không hiển thị “đã chạy thành công” từ policy. |
| Đang có Job | Xem tiến độ | Mở đúng Job; không gửi lại lệnh. |
| Đã có kết quả | Xem kết quả | Giữ định danh Job và trạng thái lỗi nếu có. |

### P1 — Giảm tìm kiếm và mất ngữ cảnh

- **Ctrl+K:** tìm thao tác/cài đặt, hỗ trợ gõ không dấu; Enter mở kết quả, Escape đóng và trả focus. Không tìm nội dung chat mà Hub chưa sở hữu.
- **Lý do chờ dễ hiểu:** đang chạy lệnh, chờ người dùng, chờ worker, mất kết nối hoặc chưa có dữ liệu. Nếu backend chưa cung cấp lý do thì ghi chưa xác định; không đoán “bị treo”.
- **Xem thay đổi và sản phẩm đầu ra:** liên kết từ công việc đến file/diff/artifact đúng phạm vi; không phát triển thêm một IDE đầy đủ.
- **Tiếp tục có xem trước:** hiện mục tiêu, việc đã làm, bằng chứng, việc còn lại và câu hỏi đang chờ. Tái sử dụng continuity; không tự tạo phiên hay chạy lại Job khi chỉ mở phần xem trước.

### P2 — Tiện ích sau khi luồng chính đã ổn

- Ghim dự án/thao tác thường dùng nếu MRU và tìm kiếm chưa đáp ứng nhu cầu thực tế.
- Mẫu yêu cầu ngắn như kiểm tra lỗi, giải thích mã, xem thay đổi; chỉ thêm khi có luồng gửi yêu cầu thật đến client phù hợp.
- Chỉ báo usage/context trong Chi tiết nếu có nguồn đáng tin; ghi rõ số đo, ước tính và dữ liệu chưa có.

Chưa ưu tiên thêm browser automation, marketplace, nhiều chế độ Goal/Loop hay cấu hình chọn model tự động: chúng tăng số khái niệm và không giải quyết trực tiếp điều hướng hiện tại.

## 6. Học từ hai kho tham khảo

**Chat On Steroids:** học cách [tìm cài đặt rồi focus đúng control](https://github.com/totec448-spec/chat-on-steroids/blob/e4a26876e61775331d7d90f2d62867238b098bfc/src/renderer/settings-search.ts), [minh họa bước setup](https://github.com/totec448-spec/chat-on-steroids/blob/e4a26876e61775331d7d90f2d62867238b098bfc/src/renderer/setup-guide.ts), [trình bày lý do phục hồi/chờ](https://github.com/totec448-spec/chat-on-steroids/blob/e4a26876e61775331d7d90f2d62867238b098bfc/src/renderer/recovery.ts) và [nội dung handoff](https://github.com/totec448-spec/chat-on-steroids/blob/e4a26876e61775331d7d90f2d62867238b098bfc/src/shared/handoff.ts). README vẫn có nhiều bước kết nối và kiến trúc browser riêng; không nhập toàn bộ vào Hub. Giữ quyền đúng phạm vi hiện tại.

**WebCodex:** học [Workbench giữ lựa chọn và ngữ cảnh](https://github.com/yyjeqhc/webcodex/blob/2bac8248a2e635022ae9c636fc1287bc01b6b833/frontend/src/runtime-v2/components/WindowWorkbench.tsx), [chọn thư mục rồi xem quyền trước khi xác nhận](https://github.com/yyjeqhc/webcodex/blob/2bac8248a2e635022ae9c636fc1287bc01b6b833/apps/desktop/src/features/projects/AddLocalProject.tsx), và [Runtime Console tập trung Activity, chỉ tải chi tiết khi cần](https://github.com/yyjeqhc/webcodex/blob/2bac8248a2e635022ae9c636fc1287bc01b6b833/docs/runtime-console.md). Chuyển nguyên tắc thiết kế vào Electron hiện tại; không coi frontend upstream là màn hình local đã triển khai.

## 7. Các đợt thực hiện và tiêu chí nghiệm thu

| Đợt | Sản phẩm cụ thể | Tiêu chí quan sát được |
|---|---|---|
| A — Phân tích và bản mẫu | Tài liệu này; mẫu tương tác bên ngoài repo. | Chuyển được ba mục chính và các tình huống minh họa; mọi trạng thái mẫu được ghi là mô phỏng; không gọi runtime. |
| B — Tích hợp P0 | Điều hướng, thuật ngữ, bộ chọn dự án, CTA; dùng backend hiện có. | Nhãn CTA và trang đích khớp trong từng trạng thái; máy/dự án không lệch khi chuyển; panel nghiên cứu vẫn truy cập được trong Chi tiết. Kiểm tra nguồn và UI bản chạy của đúng candidate. |
| C — Tích hợp P1 | Tìm kiếm, lý do chờ, kết quả/diff và xem trước tiếp tục. | Tìm “quyen” thấy “quyền”; bàn phím dùng được; trạng thái unknown không thành ready; mở Job không tạo Job mới; tiếp tục không lẫn máy/dự án hoặc replay hành động. |
| D — Thử sử dụng | Quan sát người dùng thực hiện chọn dự án, xử lý một bước thiếu và mở kết quả. | Ghi bước đi, chỗ dừng/nhầm và kết quả thực tế. Mục tiêu là giảm việc phải đọc tài liệu; chưa tuyên bố phần trăm cải thiện. Chỉ chọn P2 từ vấn đề còn tồn tại. |

Khi thực sự đổi code, thêm kiểm tra tập trung cho mapping trạng thái/CTA, tìm không dấu và giữ scope; kiểm tra trực quan trên candidate. Không chạy toàn bộ workspace để xác nhận tài liệu hay bản mẫu.

## 8. Ranh giới kiến trúc và trạng thái bàn giao

Sản phẩm đích là **Windows Electron Execution Hub + Coding Tools MCP**. Giữ một đường authority hiện có, lifecycle Job và bằng chứng runtime. Public surface `smart-v3` vẫn gồm tám tool: `workspace_context`, `agent_workflow`, `task_control`, `document_workflow`, `exec_command`, `command_control`, `request_permissions`, `view_image`. Đề xuất UI không mở rộng surface này. `execution_route=auto` vẫn bị chặn theo evidence và trở về `deterministic`; không quảng bá tự chọn model thông minh từ bản mẫu.

Bản mẫu tham chiếu: `C:/Users/Admin/.codex/visualizations/2026/10/22/01a1626c-2121-7c40-acec-27e1c315c255/codex-hub-simple.html`. Hai phương án: **Tập trung** và **Có tiến trình**. Đây là file thiết kế riêng, không phải renderer của ứng dụng.

Trong đợt này chỉ bổ sung tài liệu phân tích vào repo; không sửa app, runtime hay `.coding-tools`. Không thực hiện kiểm thử sản phẩm, activation, commit, push, release, deployment hoặc thao tác dịch vụ sản phẩm. Những thay đổi có sẵn trong worktree được giữ nguyên. Bản mẫu được xem qua một máy chủ preview loopback tạm thời; đây không phải runtime sản phẩm. Bằng chứng mạnh nhất là khảo sát source và bản mẫu; xác nhận packaged/live và hiệu quả với người dùng còn thuộc các đợt sau.

### Kiểm tra bản mẫu

- Parse khối JavaScript bằng Node: PASS. Lỗi trùng tên `permissions` ở bản nháp đã được sửa trước lượt kiểm tra cuối.
- Kiểm tra trong trình duyệt: tìm `quyen` trả về “Thư mục và quyền”; chuyển dự án không lẫn lịch sử và giữ quyền khi chuyển về; tạm dừng được sau khi hạ quyền, nhưng tiếp tục bước sửa mã bị chặn khi chỉ được đọc; mở được bản xem trước tiếp tục.
- Đã xem cả hai phương án; kiểm tra chiều rộng 320 px không tràn ngang trong khung ứng dụng. Chưa phải nghiệm thu khả năng truy cập đầy đủ hoặc kiểm thử UI sản phẩm.
- Máy chủ preview và tab kiểm tra tạm đã đóng sau kiểm tra. Không có Job sản phẩm mới được tạo; trạng thái live của các Job bên ngoài đợt này chưa được kiểm tra.

Bước tiếp theo: xem các tình huống trong bản mẫu, chốt luồng P0 rồi tích hợp vào renderer hiện tại với các tiêu chí của đợt B.
