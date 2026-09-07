# Kế hoạch Kiểm tra & Dọn rác Ổ C (Drive C: Cleanup)

## Hiện trạng ổ C (Đã quét lúc 09:03 07/09/2026)
- **Tổng dung lượng**: 455.79 GB
- **Đã dùng**: 352.15 GB
- **Còn trống**: 103.63 GB (22.7%)
- **Dung lượng rác / tạm có thể giải phóng**: **~16 - 18 GB**

---

## Danh sách công việc (Todo List)

- [ ] 1. Quét và phân loại chi tiết các vùng dữ liệu rác <!-- id: c-clean-1 -->
  - [x] Khảo sát tổng dung lượng ổ C và các vị trí lưu file tạm lớn nhất <!-- id: c-clean-1-1 -->
  - [x] Phân tích cấu trúc thư mục User Temp (`AppData\Local\Temp` chiếm 17.7 GB) <!-- id: c-clean-1-2 -->
  - [x] Xác định các thư mục validation cũ (>15 GB) và loại trừ các tiến trình đang chạy (như `opencode`) <!-- id: c-clean-1-3 -->
- [ ] 2. Trình kế hoạch chi tiết & Xin xác nhận người dùng <!-- id: c-clean-2 -->
  - [ ] Tạo `implementation_plan.md` phân nhóm an toàn vs nhóm tùy chọn <!-- id: c-clean-2-1 -->
  - [ ] Chờ người dùng duyệt kế hoạch trước khi xóa <!-- id: c-clean-2-2 -->
- [ ] 3. Thực thi dọn rác an toàn <!-- id: c-clean-3 -->
  - [ ] Dọn dẹp các thư mục validation/test cũ của codex-web trong Temp (~15.5 GB) <!-- id: c-clean-3-1 -->
  - [ ] Dọn dẹp các file cập nhật/chẩn đoán cũ (`vscode-stable-user-x64`, `DockerDesktopUpdates`, `Diagnostics`) (~720 MB) <!-- id: c-clean-3-2 -->
  - [ ] Dọn dẹp CrashDumps trong `AppData\Local\CrashDumps` (~56 MB) <!-- id: c-clean-3-3 -->
  - [ ] Dọn dẹp các file `.tmp` cũ > 24 giờ trong User Temp (bỏ qua file đang in-use) <!-- id: c-clean-3-4 -->
  - [ ] (Nếu người dùng đồng ý) Dọn Cache trình duyệt Chrome/Edge và Windows Thumbnail cache (~800 MB) <!-- id: c-clean-3-5 -->
- [ ] 4. Kiểm tra & Báo cáo kết quả <!-- id: c-clean-4 -->
  - [ ] Đo lại dung lượng trống ổ C sau khi dọn <!-- id: c-clean-4-1 -->
  - [ ] Tính toán số GB thực tế đã giải phóng <!-- id: c-clean-4-2 -->
  - [ ] Cập nhật kết quả vào `tasks/todo.md` và `walkthrough.md` <!-- id: c-clean-4-3 -->
