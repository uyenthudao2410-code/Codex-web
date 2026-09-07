# Bài học & Nguyên tắc Tự Cải thiện (Lessons & Self-Improvement)

> Tài liệu này được tự động cập nhật sau mỗi phản hồi hiệu chỉnh từ người dùng nhằm ngăn ngừa triệt để các lỗi tương tự trong tương lai.

---

## 1. Bài học về Tên Biến Cấu hình Toolchain (Toolchain Config Variable Naming)
- **Sai lầm đã xảy ra**: Tự giả định tên biến môi trường của Electron cache theo quy ước thông thường viết hoa (`ELECTRON_CACHE`), trong khi mã nguồn thực tế của `@electron/get` (được gọi từ `node_modules/electron/install.js:46`) yêu cầu chính xác là `process.env.electron_config_cache`.
- **Hậu quả**: Dữ liệu cache cũ đã chuyển sang E:, nhưng khi Electron tải mới vẫn phân giải về đường dẫn mặc định trên C:.
- **Quy tắc bắt buộc**:
  1. Khi cấu hình biến môi trường cho bất kỳ thư viện hay công cụ nào, **bắt buộc phải đọc trực tiếp mã nguồn của gói đang cài** (file `install.js`, loader, resolver) thay vì chỉ suy đoán từ tài liệu chung.
  2. Thiết lập đồng thời cả tên biến chính thức trong source code (`electron_config_cache`) và tên biến alias (`ELECTRON_CACHE`) để bao quát các công cụ liên quan.

---

## 2. Bài học về Quy trình Di dời Dữ liệu An toàn (Safe Data Migration Protocol)
- **Sai lầm đã xảy ra**: Script PowerShell sử dụng `robocopy ... /MOVE` kết hợp `Remove-Item -Recurse -Force` với `SilentlyContinue` mà không kiểm tra `$LASTEXITCODE`, không kiểm tra checksum trước khi xóa nguồn.
- **Hậu quả**: Dù không mất dữ liệu trong thực tế, nhưng quy trình tiềm ẩn rủi ro xóa nguồn khi quá trình copy chưa hoàn tất trọn vẹn, không đáp ứng tiêu chuẩn kỹ thuật an toàn cao.
- **Quy tắc bắt buộc**:
  1. Tuyệt đối **không dùng `/MOVE` kết hợp `Remove-Item -Force -SilentlyContinue`** trong một chuỗi lệnh mù.
  2. Quy trình di chuyển dữ liệu chuẩn 4 bước:
     - **Bước 1**: Copy nguồn sang đích (`robocopy /E`, không dùng `/MOVE`).
     - **Bước 2**: Kiểm tra `$LASTEXITCODE -le 7` (mã thành công của robocopy).
     - **Bước 3**: Kiểm chứng số lượng tệp, tổng byte và băm SHA256 giữa nguồn và đích.
     - **Bước 4**: Chỉ sau khi nghiệm thu kiểm chứng khớp 100% mới thực hiện dọn dẹp hoặc lưu bản backup nguồn tối thiểu 7 ngày.

---

## 3. Bài học về Phạm vi Cấu hình CLI (Config Scoping Accuracy)
- **Sai lầm đã xảy ra**: Dùng lệnh `npm config set cache ... --global` và mô tả trong báo cáo là "cấu hình user".
- **Phân tích kỹ thuật**: `npm config set ... --global` ghi vào file global config theo prefix (`AppData\Roaming\npm\etc\npmrc`), trong khi User config của npm là `~/.npmrc` (`C:\Users\Admin\.npmrc`).
- **Quy tắc bắt buộc**:
  1. Phân định rạch ròi giữa `--location=user` (`~/.npmrc`) và `--location=global` (`<prefix>/etc/npmrc`).
  2. Để đảm bảo cấu hình ăn khớp trên toàn bộ các ngữ cảnh gọi npm của người dùng, phải thiết lập rõ ràng ở cả cấp User (`--location=user`) và Global (`--location=global`).

---

## 4. Bài học về Tính Kế thừa Môi trường Tiến trình (Process Environment Inheritance)
- **Sai lầm đã xảy ra**: Báo cáo nghiệm thu khẳng định ngay sau khi ghi vào Windows Registry User Environment (`[System.Environment]::SetEnvironmentVariable(..., "User")`).
- **Phân tích kỹ thuật**: Các tiến trình đang chạy (Terminal, IDE, Background Tasks) được fork trước thời điểm ghi Registry sẽ **không tự động cập nhật** biến môi trường mới nếu không được reload hoặc spawn lại.
- **Quy tắc bắt buộc**:
  1. Luôn cập nhật cả 2 phạm vi: Registry User lâu dài (`"User"`) và biến môi trường của tiến trình hiện tại (`$env:...`).
  2. Báo cáo nghiệm thu phải ghi chú rõ ràng: *"Các tiến trình đang mở cần được khởi động lại hoặc nhận biến môi trường mới trong phiên tiếp theo."*
  3. Kiểm chứng phải được thực hiện bằng cách spawn một tiến trình con mới để chứng minh tính kế thừa thực tế.

---

## 5. Bài học về Tính Chuẩn mực & Khiêm tốn Khoa học trong Báo cáo (Technical Rigor & Scientific Claims)
- **Sai lầm đã xảy ra**:
  - Dùng từ ngữ tuyệt đối hóa: *"Chấm dứt hoàn toàn hao mòn SSD"*, *"Không làm chậm"* khi chưa có dữ liệu đo SMART/TBW dài hạn.
  - Sử dụng đơn vị GB thay vì GiB (khi chia cho `1024^3`).
  - Gộp mức tăng dung lượng của nhiều đợt khác nhau (Pagefile, dọn Temp, WSL) gán vào riêng Gói A.
  - Khẳng định Pagefile trên C: đã tắt/giải phóng trong khi Windows thực tế vẫn đang giữ file in-use 23 GiB do chưa Reboot.
- **Quy tắc bắt buộc**:
  1. **Chuẩn đơn vị**: Sử dụng chính xác **GiB / MiB** khi tính toán theo lũy thừa nhị phân (`/ 1024^2`, `/ 1024^3`).
  2. **Trình bày bằng chứng thực tế**: Chỉ tuyên bố những gì đã đo được trực tiếp; nêu rõ phạm vi đo và điều kiện cần thiết (ví dụ: cần Reboot hệ thống để Windows nhả file `pagefile.sys` đang in-use trên C:).
  3. **Đánh giá khách quan hai mặt**: Nêu rõ việc chuyển sang HDD cơ học có thể làm giảm tốc độ đọc/giải nén ban đầu so với SSD NVMe, đổi lại là ưu thế về dung lượng dồi dào và bảo vệ số chu kỳ ghi của SSD.
