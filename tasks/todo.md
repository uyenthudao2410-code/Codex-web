# Kế hoạch Kiểm tra & Dọn rác Ổ C (Drive C: Cleanup)

## Tổng kết Toàn diện Sau 2 Đợt Tối ưu (07/09/2026)
- **Tổng dung lượng Ổ C**: 455.79 GB
- **Ban đầu**: Đã dùng 352.15 GB | Còn trống **103.63 GB** (22.7%)
- **Hiện tại**: Đã dùng 310.37 GB | Còn trống **145.42 GB** (31.9%)
- **Tổng dung lượng giải phóng thành công**: **+41.79 GB** trống thêm trên ổ C! :tada:

---

## Danh sách công việc (Todo List)

- [x] 1. Quét và phân loại chi tiết các vùng dữ liệu rác <!-- id: c-clean-1 -->
  - [x] Khảo sát tổng dung lượng ổ C và các vị trí lưu file tạm lớn nhất <!-- id: c-clean-1-1 -->
  - [x] Phân tích cấu trúc thư mục User Temp (`AppData\Local\Temp` chiếm 17.7 GB) <!-- id: c-clean-1-2 -->
  - [x] Xác định các thư mục validation cũ (>15 GB) và loại trừ các tiến trình đang chạy (như `opencode`) <!-- id: c-clean-1-3 -->
- [x] 2. Trình kế hoạch chi tiết & Xin xác nhận người dùng <!-- id: c-clean-2 -->
  - [x] Tạo `implementation_plan.md` phân nhóm an toàn vs nhóm tùy chọn <!-- id: c-clean-2-1 -->
  - [x] Chờ người dùng duyệt kế hoạch trước khi xóa (Người dùng đã xác nhận đồng ý) <!-- id: c-clean-2-2 -->
- [x] 3. Thực thi dọn rác an toàn đợt 1 <!-- id: c-clean-3 -->
  - [x] Dọn dẹp các thư mục validation/test cũ của codex-web trong Temp (25 thư mục validation cũ) <!-- id: c-clean-3-1 -->
  - [x] Dọn dẹp các file cập nhật/chẩn đoán cũ (`vscode-stable-user-x64`, `DockerDesktopUpdates`, `Diagnostics`, `coding-tools-census-*`) <!-- id: c-clean-3-2 -->
  - [x] Dọn dẹp CrashDumps trong `AppData\Local\CrashDumps` (giảm về 0 MB) <!-- id: c-clean-3-3 -->
  - [x] Dọn dẹp hơn 2,100 file `.tmp` cũ > 24 giờ trong User Temp (bảo toàn tiến trình `opencode` và file đang in-use) <!-- id: c-clean-3-4 -->
  - [x] Dọn Cache trình duyệt Chrome/Edge và Thùng rác <!-- id: c-clean-3-5 -->
- [x] 4. Báo cáo kết quả đợt 1 & Rà soát chuyên sâu 340 GB còn lại <!-- id: c-clean-4 -->
  - [x] Bóc tách chi tiết 153 GB trong `C:\Users\Admin`, 49 GB `Program Files`, 48 GB `Windows`, 23 GB `pagefile.sys` <!-- id: c-clean-4-1 -->
  - [x] Phát hiện các vị trí lớn: Docker VHDX (22.8 GB), Pagefile (23 GB), WSL VHDX (9.4 GB), LM Studio (4.3 GB), npm-cache (1.88 GB) <!-- id: c-clean-4-2 -->
- [x] 5. Tối ưu theo yêu cầu (Người dùng xử lý Docker/Pagefile, Agent xử lý các mục còn lại) <!-- id: c-auto-1 -->
  - [x] 5.1. Dọn dẹp sạch sẽ `npm-cache` trong `AppData\Local\npm-cache` (giải phóng ~1.88 GB) <!-- id: c-auto-1-1 -->
  - [x] 5.2. Xóa các phiên bản cũ và gói cài đặt dư thừa của GitHub Desktop (`app-3.6.3`, `app-3.6.4`, `packages`) (giải phóng ~1.02 GB) <!-- id: c-auto-1-2 -->
  - [x] 5.3. Di chuyển kho Models & Extensions của LM Studio sang `E:\LMStudio` bằng Directory Junctions trong suốt (giải phóng ~4.04 GB) <!-- id: c-auto-1-3 -->
  - [x] 5.4. Kích hoạt Sparse mode cho đĩa ảo WSL Ubuntu để tự động thu hồi dung lượng đĩa trống <!-- id: c-auto-1-4 -->
  - [x] 5.5. Dọn dẹp các tệp tạm/installer còn sót (`.cache\codex-runtime-install-*`, `.codex\.tmp`) <!-- id: c-auto-1-5 -->
- [x] 6. Đo lường tổng kết & Báo cáo dung lượng cuối cùng <!-- id: c-auto-2 -->
  - [x] Đo lại dung lượng ổ C: Đạt **145.42 GB trống** (tăng từ 103.63 GB ban đầu) <!-- id: c-auto-2-1 -->
  - [x] Cập nhật kết quả vào `tasks/todo.md` và `walkthrough.md` <!-- id: c-auto-2-2 -->

---

## Giai đoạn 4: Triển khai Gói A (Chuyển Cache Tải & Cài đặt sang HDD E:)

- [x] 7. Thiết lập cấu hình chuyển ghi sang HDD E: <!-- id: pkg-a-1 -->
  - [x] 7.1. Khởi tạo cấu trúc thư mục cache trên E: (`E:\Caches\Admin\npm`, `electron`, `electron-builder`) <!-- id: pkg-a-1-1 -->
  - [x] 7.2. Cấu hình npm cache toàn cục: `npm config set cache "E:\Caches\Admin\npm" --global` <!-- id: pkg-a-1-2 -->
  - [x] 7.3. Cấu hình biến môi trường User cho Electron: `ELECTRON_CACHE="E:\Caches\Admin\electron"` <!-- id: pkg-a-1-3 -->
  - [x] 7.4. Cấu hình biến môi trường User cho electron-builder: `ELECTRON_BUILDER_CACHE="E:\Caches\Admin\electron-builder"` <!-- id: pkg-a-1-4 -->
  - [x] 7.5. Di chuyển cache cũ hiện có của Electron (629.4 MB) và electron-builder (48.9 MB) sang E: <!-- id: pkg-a-1-5 -->
  - [x] 7.6. Kiểm tra & xác minh các biến cấu hình và quyền ghi trên E: (Xác nhận 100% trỏ sang E:) <!-- id: pkg-a-1-6 -->

---

## Giai đoạn 5: Triển khai Toàn diện Di dời Cache sang `E:\Caches` & Tạo Tài liệu Quản trị

- [x] 8. Di dời toàn bộ Cache lập trình, AI & Cold Data sang `E:\Caches` <!-- id: pkg-all-1 -->
  - [x] 8.1. Khởi tạo cấu trúc các thư mục đích trong `E:\Caches` (`Admin\ms-playwright`, `Admin\uv`, `Admin\.cargo`, `Admin\.rustup`, `AI\...`, `Codex\sessions_archive`) <!-- id: pkg-all-1-1 -->
  - [x] 8.2. Chuyển Playwright Browsers và đặt biến `PLAYWRIGHT_BROWSERS_PATH` (~1.02 GB) <!-- id: pkg-all-1-2 -->
  - [x] 8.3. Chuyển uv cache và đặt biến `UV_CACHE_DIR` (~0.68 GB) <!-- id: pkg-all-1-3 -->
  - [x] 8.4. Chuyển Cargo & Rustup và đặt biến `CARGO_HOME`, `RUSTUP_HOME` (~3.37 GB) <!-- id: pkg-all-1-4 -->
  - [x] 8.5. Cấu hình sẵn các biến môi trường cho AI models (`HF_HOME`, `TORCH_HOME`, `OLLAMA_MODELS`) <!-- id: pkg-all-1-5 -->
  - [x] 8.6. Di chuyển các phiên Codex cũ (> 7 ngày) sang `E:\Caches\Codex\sessions_archive` (~3.56 GB) <!-- id: pkg-all-1-6 -->
  - [x] 8.7. Di chuyển máy ảo WSL Ubuntu sang `E:\WSL\Ubuntu` (~9.39 GB) <!-- id: pkg-all-1-7 -->
- [x] 9. Biên soạn tài liệu quản trị tệp `E:\Caches\README_STORAGE_MIGRATION.md` <!-- id: pkg-all-2 -->
  - [x] Diễn giải chi tiết kiến trúc, bảng phân bổ, biến môi trường, cơ chế xác minh và hướng dẫn hoàn tác <!-- id: pkg-all-2-1 -->
  - [x] Cập nhật nhật ký các lần dịch chuyển (Changelog) đầy đủ mốc thời gian <!-- id: pkg-all-2-2 -->
- [x] 10. Nghiệm thu & Báo cáo tổng kết <!-- id: pkg-all-3 -->
  - [x] Đo lại dung lượng ổ C: Đạt **163.54 GB trống** (tăng từ 103.63 GB ban đầu) <!-- id: pkg-all-3-1 -->
  - [x] Cập nhật kết quả vào `tasks/todo.md` và `walkthrough.md` <!-- id: pkg-all-3-2 -->

---

## Giai đoạn 6: Dọn Rác Driver NVIDIA, Browser Offline Cache & Quy Hoạch Go/NuGet

- [x] 11. Xử lý các vùng rác lớn và quy hoạch cache bổ sung <!-- id: pkg-ext-1 -->
  - [x] 11.1. Xóa sạch bộ cài driver cũ của NVIDIA trong `ota-artifacts` (`grd` & `nvapp`, ~4.39 GiB) <!-- id: pkg-ext-1-1 -->
  - [x] 11.2. Dọn sạch Code Cache và Service Worker CacheStorage của Chrome & Edge (~2.80 GiB) <!-- id: pkg-ext-1-2 -->
  - [x] 11.3. Di dời Go module cache (`go\pkg\mod`) sang `E:\Caches\Admin\go\mod` và đặt biến `GOMODCACHE` (~0.34 GiB) <!-- id: pkg-ext-1-3 -->
  - [x] 11.4. Di dời NuGet packages (`.nuget\packages`) sang `E:\Caches\Admin\nuget\packages` và đặt biến `NUGET_PACKAGES` (~0.29 GiB) <!-- id: pkg-ext-1-4 -->
  - [x] 11.5. Dọn dẹp Scoop installer cache (`scoop\cache`) <!-- id: pkg-ext-1-5 -->
- [x] 12. Cập nhật tài liệu quản trị `E:\Caches\README_STORAGE_MIGRATION.md` & Đo lường nghiệm thu <!-- id: pkg-ext-2 -->
  - [x] Đồng bộ bổ sung các biến Go và NuGet vào sổ tay quản trị <!-- id: pkg-ext-2-1 -->
  - [x] Đo lường chỉ số dung lượng ổ C cuối cùng (Đạt 166.47 GiB trống) <!-- id: pkg-ext-2-2 -->

---

## Giai đoạn 7: Khắc Phục Lỗi Cấu Hình Đường Dẫn Đĩa Ảo Docker Desktop Trên Ổ E:

- [x] 13. Khắc phục cấu hình và khởi động hoàn chỉnh Docker Desktop <!-- id: docker-fix-1 -->
  - [x] 13.1. Dừng triệt để các tiến trình Docker Desktop đang chạy lỗi ngầm <!-- id: docker-fix-1-1 -->
  - [x] 13.2. Tạo Directory Junction liên kết trong suốt `E:\Cache\DockerDesktopWSL` -> `E:\Caches\DockerDesktopWSL` <!-- id: docker-fix-1-2 -->
  - [x] 13.3. Cập nhật `settings-store.json` chuẩn hóa `"CustomWslDistroDir": "E:\\Caches\\DockerDesktopWSL"` <!-- id: docker-fix-1-3 -->
  - [x] 13.4. Khởi động lại hệ thống WSL (`wsl --shutdown`) để giải phóng trạng thái lỗi <!-- id: docker-fix-1-4 -->
  - [x] 13.5. Khởi chạy Docker Desktop và xác minh trạng thái Engine (`docker info`, `docker ps`) <!-- id: docker-fix-1-5 -->
  - [x] 13.6. Cập nhật nhật ký tài liệu quản trị `E:\Caches\README_STORAGE_MIGRATION.md` <!-- id: docker-fix-1-6 -->

---

## Giai đoạn 8: Chẩn Đoán Toàn Diện Tốc Độ Mạng & Định Danh Nguyên Nhân Nghẽn Mạng

- [x] 14. Chẩn đoán đa tầng mạng Internet & Tín hiệu máy tính <!-- id: net-diag-1 -->
  - [x] 14.1. Khảo sát cấu hình Card mạng, Tín hiệu Wi-Fi / Ethernet Link Speed & Adapter Duplex <!-- id: net-diag-1-1 -->
  - [x] 14.2. Rà soát lưu lượng băng thông tiêu thụ theo tiến trình (phát hiện tiến trình chạy ngầm ngốn mạng) <!-- id: net-diag-1-2 -->
  - [x] 14.3. Kiểm tra độ trễ (Latency), Jitter & Tỷ lệ rớt gói (Packet Loss) tới Default Gateway cục bộ <!-- id: net-diag-1-3 -->
  - [x] 14.4. Đo tốc độ phân giải DNS và độ trễ tới các DNS Server chính (Google, Cloudflare, VNPT/Viettel) <!-- id: net-diag-1-4 -->
  - [x] 14.5. Đo kiểm độ trễ và mất gói tới các dịch vụ trong nước vs quốc tế (Domestic vs International) <!-- id: net-diag-1-5 -->
  - [x] 14.6. Kiểm tra cấu hình Proxy, VPN, WSL vpnkit, Docker Network có can thiệp/bóp băng thông không <!-- id: net-diag-1-6 -->
  - [x] 14.7. Tổng hợp kết luận nguyên nhân chính xác: Do mạng chung (ISP/Router) hay do máy tính (Hardware/Software) <!-- id: net-diag-1-7 -->

---

## Review & Kết Quả Chẩn Đoán Mạng Toàn Diện (Giai Đoạn 8)

1. **Kết luận cốt lõi**:
   - **Máy tính KHÔNG làm suy yếu tín hiệu mạng**: Kết nối dây mạng LAN Gigabit (`Intel I219-V`, 1 Gbps Full Duplex), phần cứng 0 lỗi gói (`0 ReceivedPacketErrors`), ping modem nội bộ siêu tốc **0.68 ms**, 0% rớt gói.
   - **Băng thông máy tính đang rất dồi dào**: Tải thử nghiệm 25 MB qua Cloudflare CDN đạt tốc độ thực tế **~240 Mbps** (chỉ mất 0.85 giây).
   - **Không có tiến trình ngầm ngốn mạng**: Băng thông nền nhàn rỗi (Upload ~0.30 Mbps, Download ~0.27 Mbps).
   - **Độ trễ Bufferbloat**: Rất tốt (độ trễ khi tải nặng chỉ tăng -0.1 ms, không bị nghẽn đệm).

2. **Nguyên nhân tiềm ẩn gây cảm giác "chậm"**:
   - Định tuyến quốc tế của nhà mạng FPT Telecom (AS18403) đối với một số dịch vụ quốc tế/cáp quang biển.
   - Cơ chế Double NAT qua 2 lớp router (`192.168.10.1` -> `192.168.1.1`).
   - Các dịch vụ web cụ thể chặn gói tin ICMP Ping hoặc cơ chế DoH (Secure DNS) của trình duyệt.

---

## Review & Nghiệm Thu Giai Đoạn 7 (Docker Desktop Đã Hoàn Chỉnh)

1. **Nguyên nhân gốc rễ (Root Cause)**:
   - File đĩa ảo `docker_data.vhdx` (22.79 GB) và `ext4.vhdx` (109 MB) thực tế đã được chuyển thành công sang thư mục `E:\Caches\DockerDesktopWSL`.
   - Tuy nhiên cấu hình gốc trong `settings-store.json` vẫn lưu giá trị cũ `E:\Cache\DockerDesktopWSL` (thiếu chữ `s`).
   - Khi người dùng vào Docker Desktop Settings UI để thêm chữ `s`, giao diện Docker Desktop áp dụng cơ chế kiểm tra di dời đĩa (migration check), đòi hỏi thư mục đích phải **chưa tồn tại**. Vì thư mục `E:\Caches\DockerDesktopWSL` đã có sẵn dữ liệu, Docker Desktop ném hộp thoại báo lỗi:
     `Invalid path: E:\Caches\DockerDesktopWSL already exists. Please remove it and retry.`

2. **Giải pháp thực thi hoàn chỉnh**:
   - **Tạo Directory Junction 2 chiều**: Tạo liên kết `E:\Cache\DockerDesktopWSL` trỏ tới `E:\Caches\DockerDesktopWSL`. Dù hệ thống hay bất kỳ tiến trình nào gọi đường dẫn có `s` hay không có `s`, Windows đều phân giải trong suốt vào đúng thư mục dữ liệu thực trên ổ E:.
   - **Chuẩn hóa cấu hình Docker**: Cập nhật trực tiếp `C:\Users\Admin\AppData\Roaming\Docker\settings-store.json` với `"CustomWslDistroDir": "E:\\Caches\\DockerDesktopWSL"`.
   - **Tái khởi động WSL Subsystem**: `wsl --shutdown` để giải phóng socket và lock cũ.
   - **Khởi động lại Docker Desktop**: Docker Desktop tự động kết nối vào phân vùng đĩa ảo 22.79 GB tại `E:\Caches\DockerDesktopWSL`.

3. **Bằng chứng kiểm chứng thực tế (Proof of Work)**:
   - `docker version`: Client 29.7.2, Server Docker Desktop 4.87.0 (Engine 29.7.2).
   - `docker info`: Nhận diện đầy đủ 4 containers, 11 images, WSL2 backend.
   - `docker images`: Hiển thị đầy đủ 11 image (alpine, postgres, redis, minio, sub2api, kirogo, ds2api...).
   - `docker run --rm alpine:latest echo ...`: Chạy thử container thành công 100%.
   - Dung lượng ổ C: Giữ vững ở mức **165.59 GiB trống** (đã giải phóng triệt để 22.79 GB đĩa ảo Docker khỏi ổ SSD C:).

---

## Giai đoạn 9: Thiết lập `token-dashboard.html` làm Giao diện Chính Duy nhất

- [x] 15. Tối ưu kiến trúc UI: Thiết lập `token-dashboard.html` làm giao diện chính duy nhất <!-- id: ui-consolidate-1 -->
  - [x] 15.1. Khảo sát cấu trúc DOM và CSS của `renderer/index.html` và `renderer/token-dashboard.html` <!-- id: ui-consolidate-1-1 -->
  - [x] 15.2. Cấu hình `electron/main.js` để `managerWindow` tải trực tiếp `renderer/token-dashboard.html` làm cửa sổ chính <!-- id: ui-consolidate-1-2 -->
  - [x] 15.3. Loại bỏ iframe lồng ghép `overviewTokenFrame` và dọn dẹp CSS thừa khỏi `index.html` và `control-center.css` <!-- id: ui-consolidate-1-3 -->
  - [x] 15.4. Đồng bộ logic đóng cửa sổ (`token-dashboard:close`) hỗ trợ đóng cả `managerWindow` và `tokenWindow` <!-- id: ui-consolidate-1-4 -->
  - [x] 15.5. Tinh chỉnh ghi chú sidebar footer trong `token-dashboard.html` phản ánh đúng vai trò giao diện chính <!-- id: ui-consolidate-1-5 -->
  - [x] 15.6. Chạy bộ kiểm thử tự động (`token-dashboard.test.js`, `dashboard-analytics.test.js`, `control-center-manager.test.js`, `npm test`) <!-- id: ui-consolidate-1-6 -->
  - [x] 15.7. Tổng kết và bàn giao kết quả trực quan cho người dùng <!-- id: ui-consolidate-1-7 -->
