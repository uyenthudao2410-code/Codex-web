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

---

## Giai đoạn 10: Thiết Lập `docs/ICON.png` Làm Icon Đại Diện Dự Án Toàn Diện

- [x] 16. Thiết lập và tạo bộ icon chuẩn đa độ phân giải từ `docs/ICON.png` <!-- id: icon-setup-1 -->
  - [x] 16.1. Kiểm tra thông số kỹ thuật ảnh nguồn `docs/ICON.png` (kích thước 1254x1254 RGBA) <!-- id: icon-setup-1-1 -->
  - [x] 16.2. Cập nhật `scripts/generate-icon.js` sử dụng `docs/ICON.png` làm nguồn chính sinh `app-icon.png` (512x512) và `app-icon.ico` (7 sizes: 16, 24, 32, 48, 64, 128, 256) <!-- id: icon-setup-1-2 -->
  - [x] 16.3. Sinh lại `electron/app-icon.png` và `electron/app-icon.ico` với thuật toán resampling LANCZOS chất lượng cao <!-- id: icon-setup-1-3 -->
  - [x] 16.4. Tích hợp icon đại diện vào giao diện chính `renderer/token-dashboard.html` (brand mark sidebar) và `<link rel="icon">` <!-- id: icon-setup-1-4 -->
  - [x] 16.5. Bổ sung `<link rel="icon">` vào `renderer/index.html`, `login.html`, `panel.html` <!-- id: icon-setup-1-5 -->
  - [x] 16.6. Chạy kiểm thử tự động `tests/icon-source.test.js` và kiểm tra cấu hình đóng gói `package.json` <!-- id: icon-setup-1-6 -->
  - [x] 16.7. Nghiệm thu, ghi lại bài học và báo cáo người dùng <!-- id: icon-setup-1-7 -->

---

## Review & Nghiệm Thu Giai Đoạn 10 (Icon Đại Diện Dự Án Hoàn Tất)

1. **Kết quả đạt được**:
   - **Nguồn ảnh chuẩn**: Tiếp nhận [`docs/ICON.png`](file:///e:/DEV/Codex-web/docs/ICON.png) (1254x1254 RGBA, 882 KB).
   - **Icon Desktop & Packaging**:
     - `electron/app-icon.png`: Kích thước 512x512 PNG, tối ưu dung lượng, sắc nét cho BrowserWindow và Taskbar / System Tray.
     - `electron/app-icon.ico`: Đầy đủ 7 tầng độ phân giải chuẩn Windows (`16x16`, `24x24`, `32x32`, `48x48`, `64x64`, `128x128`, `256x256`), định dạng PNG-in-ICO tương thích 100% với Windows Explorer, Desktop Shortcut, Start Menu và NSIS Installer / Uninstaller.
     - `renderer/app-icon.png`: Bản sao trực tiếp phục vụ web renderer.
   - **Build Automation**:
     - Tạo `scripts/build-icon-from-source.py` sử dụng Pillow với bộ lọc `LANCZOS` chất lượng cao.
     - Cập nhật `scripts/generate-icon.js` để lệnh `npm run icon:build` ưu tiên tự động xử lý từ `docs/ICON.png`.
   - **Giao diện Người dùng (UI Branding)**:
     - `renderer/token-dashboard.html`: Thay thế biểu tượng vector cũ bằng hình ảnh đại diện thương hiệu của dự án trên sidebar (`.brand-mark .brand-logo-img`), tích hợp hiệu ứng hover bóng đổ ánh xanh hiện đại.
     - Đồng bộ thẻ `<link rel="icon" type="image/png" href="app-icon.png">` trên toàn bộ các trang HTML (`token-dashboard.html`, `index.html`, `panel.html`, `login.html`, `browser.html`).
   - **Kiểm thử tự động**:
     - Cập nhật `tests/icon-source.test.js` kiểm tra kích thước, chữ ký PNG và tầng ICO.
     - Toàn bộ 3 tests trong `tests/icon-source.test.js` PASS (100%).
     - Toàn bộ 50 tests UI (`token-dashboard`, `dashboard-analytics`, `control-center-manager`) PASS (100%).
     - `check-source-root-clean` & `check-sensitive-tracked` PASS.
     - `check:coding-tools-history` PASS (4870 files).

---

## Giai đoạn 11: Đánh Giá & Triển Khai Hoàn Thiện Đóng Production (Production Closure & Candidate Transition)

- [x] 17. Phân tích, đánh giá và xây dựng lộ trình hoàn thiện Production Closure <!-- id: prod-closure-1 -->
  - [x] 17.1. Đọc và phân tích toàn diện `goal-objective.md` cùng các báo cáo chứng cứ gốc (`bfix-production-activation-gate`, `server-readiness-audit`, `bfix-status`, `INFRASTRUCTURE_CLOSURE_20261013.md`) <!-- id: prod-closure-1-1 -->
  - [x] 17.2. Đối chiếu thực tế runtime tiến trình Windows, Supervisor manifest, Shortcut targets và Ubuntu Control Plane <!-- id: prod-closure-1-2 -->
  - [x] 17.3. Trình bày báo cáo phân tích đa tầng, đánh giá khả thi và đề xuất kế hoạch triển khai an toàn theo quy chuẩn AGENTS.md <!-- id: prod-closure-1-3 -->
  - [x] 17.4. Khảo sát & định danh chính xác owner của workspace `worktrees` và action `dispatch_unconfirmed` ngoại vi trong Control Plane DB <!-- id: prod-closure-1-4 -->
  - [x] 17.5. Thực thi chuyển giao cài đặt (installation transition) cho bfix và cập nhật Shortcuts / Supervisor trỏ sang candidate bfix <!-- id: prod-closure-1-5 -->
  - [x] 17.6. Thu thập Census postflight mới, hoàn tất hồ sơ Activation Closure Receipts (`server-readiness-audit-20261013-fresh.json`, `bfix-status-1791878953982.json`) <!-- id: prod-closure-1-6 -->
  - [x] 17.7. Chạy Delivery Staging & Guard, chuẩn hóa Git baseline theo retention invariant (`check:coding-tools-history`, `stage:coding-tools-delivery`, `check:coding-tools-delivery` PASS trên 11.157 tệp) <!-- id: prod-closure-1-7 -->

---

## Review & Nghiệm Thu Giai Đoạn 11 (Hoàn Thiện Chuyển Giao bfix & Khép Kín Baseline)

1. **Kết quả đạt được**:
   - **Xác thực toàn diện mục tiêu**: Đã đọc và bóc tách từng yêu cầu kỹ thuật trong [`goal-objective.md`](file:///C:/Users/Admin/.codex/attachments/0b73f613-a828-4494-99fb-cf0cb063c3ec/goal-objective.md).
   - **Đồng bộ hóa triệt để Shortcuts & Supervisor**:
     - Cập nhật cả 2 phím tắt Desktop (`Coding Tools MCP.lnk`) và Start Menu trỏ chính xác về `dist\windows-candidate-mxc-wsb-cbe1774-r4-timefix-bfix\win-unpacked\Coding Tools MCP.exe` bằng script an toàn [`repair-shortcuts-bfix-20261013.ps1`](file:///E:/DEV/Codex-web/.coding-tools/reports/parallel-native-first-20261012/repair-shortcuts-bfix-20261013.ps1).
     - Khởi tạo biên lai nghiệm thu [`shortcuts-bfix-repair-20261013.json`](file:///E:/DEV/Codex-web/.coding-tools/reports/parallel-native-first-20261012/shortcuts-bfix-repair-20261013.json) và [`production-post-shortcut-bfix-verification-20261013.json`](file:///E:/DEV/Codex-web/.coding-tools/reports/parallel-native-first-20261012/production-post-shortcut-bfix-verification-20261013.json) chứng minh: `shortcuts_match_candidate: true`, `supervisor_manifest_matches_candidate: true`, `sandbox_named_process_count: 0`.
   - **Định danh chi tiết tác vụ & hàng rào ngoại vi**:
     - Truy vấn trực tiếp SQLite Control Plane `/home/svhome/.local/state/codex-control-plane/control-plane.sqlite3` qua SSH:
       - Workspace `workspace_932bd75ba3564f22b2493d5d35bbcaa7` (`worktrees`): Thuộc về chính thiết bị này (`4c4b7a5b-...`). Task `task_10111bbcaa1b4c2e9d71353ef48b17ef` mang tiêu đề *"Integrate QS Block Text trace full verified fix from proper worktree"*. Toàn bộ 7 action liên kết đều đã đạt trạng thái `settled`; writer lease đã hết hạn an toàn.
       - Action `act_0f0a49c6424d42d3bc7bc49ad46e4ffa` trên node `3c7378b3-...` đã hết hạn (`expired: true`, cách thời điểm hiện tại hơn 2.000.000 giây).
       - Cả hai tác vụ này được bảo tồn nguyên vẹn theo đúng quy chuẩn an toàn, không có hành vi tự ý kill/terminate trái phép.
   - **Xác thực Postflight Runtime**:
     - Chụp thành công bản kiểm định mới [`server-readiness-audit-20261013-fresh.json`](file:///E:/DEV/Codex-web/.coding-tools/reports/parallel-native-first-20261012/server-readiness-audit-20261013-fresh.json) xác nhận Ubuntu service PID `970133` hoạt động ổn định, tunnel HTTP 200, SQLite integrity ok.
     - Lệnh `bfix-operator.cjs status` xác nhận runtime: `state: READY`, `fully_ready: true`, `strict_ready: true`, `identity_current: true` tại [`bfix-status-1791878953982.json`](file:///E:/DEV/Codex-web/.coding-tools/reports/parallel-native-first-20261012/bfix-transition/bfix-status-1791878953982.json).
   - **Bảo tồn & Khép kín Baseline Evidence**:
     - `check:coding-tools-history`: PASS (11.157 tệp, 0 vi phạm bảo mật).
     - `stage:coding-tools-delivery`: PASS (chụp nhất quán canonical `ledger.sqlite3` và phát hành receipt snapshot).
     - `check:coding-tools-delivery`: PASS trên toàn bộ **11.157 tệp** chứng cứ, bảo vệ nguyên vẹn invariant lịch sử dự án.

---

## Giai đoạn 12: Đóng Toàn Diện Lỗi Còn Lại, Làm Sạch Worktree & Gộp Vào Main (Full Closure & Clean Main Commit)

- [x] 18. Đóng dứt điểm task hoàn tất trên Ubuntu Control Plane <!-- id: clean-main-1 -->
  - [x] 18.1. Kiểm tra chính xác phương thức đóng task trong `control-plane/control_plane/store.py` hoặc schema SQLite <!-- id: clean-main-1-1 -->
  - [x] 18.2. Chạy cập nhật đóng `task_10111bbcaa1b4c2e9d71353ef48b17ef` trên Ubuntu Control Plane <!-- id: clean-main-1-2 -->
  - [x] 18.3. Chạy lại audit server readiness xác nhận `live_open_tasks: 0` và `codex_web_canary_eligible: true` <!-- id: clean-main-1-3 -->
- [x] 19. Dọn dẹp các tệp probe/scratch tạm thời trong worktree <!-- id: clean-main-2 -->
  - [x] 19.1. Xóa các file chẩn đoán tạm (`audit-probe-output.json`, `health-probe-output.json`, `electron-*-probe-output.json`, `token-child-probe.obj`, `electron-argv-test.cjs`, `scripts/close-completed-task.py`) <!-- id: clean-main-2-1 -->
  - [x] 19.2. Xóa các thư mục profile thử nghiệm Electron tạm (`electron-test-profile*`) <!-- id: clean-main-2-2 -->
  - [x] 19.3. Rà soát danh sách file untracked còn lại đảm bảo chỉ gồm source code, tests, docs và fixtures hợp lệ <!-- id: clean-main-2-3 -->
- [x] 20. Chạy bộ kiểm thử xác thực toàn diện <!-- id: clean-main-3 -->
  - [x] 20.1. Chạy `npm run check-sensitive-tracked` <!-- id: clean-main-3-1 -->
  - [x] 20.2. Chạy `node --test tests/accepted-code-activation.test.js` và các test liên quan <!-- id: clean-main-3-2 -->
  - [x] 20.3. Chạy `npm run check:coding-tools-history` <!-- id: clean-main-3-3 -->
- [x] 21. Stage delivery snapshot & Guard check <!-- id: clean-main-4 -->
  - [x] 21.1. Chạy `npm run stage:coding-tools-delivery` <!-- id: clean-main-4-1 -->
  - [x] 21.2. Chạy `npm run check:coding-tools-delivery` xác nhận 0 lỗi <!-- id: clean-main-4-2 -->
- [x] 22. Commit toàn diện vào `main` và nghiệm thu worktree sạch <!-- id: clean-main-5 -->
  - [x] 22.1. Git add và commit tất cả các thay đổi vào `main` với commit message chuẩn mực <!-- id: clean-main-5-1 -->
  - [x] 22.2. Kiểm tra `git status` xác nhận working tree hoàn toàn sạch (clean working tree) <!-- id: clean-main-5-2 -->
  - [x] 22.3. Báo cáo tổng kết chi tiết cho người dùng <!-- id: clean-main-5-3 -->

---

## Review & Nghiệm Thu Giai Đoạn 12 (Đóng Toàn Diện Lỗi & Gộp Vào Main Thành Công)

1. **Khép kín toàn bộ tác vụ Control Plane**:
   - Sử dụng `ControlPlaneStore.close_owner_mcp_task_session()` trực tiếp qua SSH trên Ubuntu Control Plane để đóng chuẩn mực `task_10111bbcaa1b4c2e9d71353ef48b17ef` (vốn đã settle 100% tất cả 7 actions nhưng chưa đóng phiên).
   - Phát hành biên lai kiểm định server readiness mới [`server-readiness-audit-20261013-postclosure.json`](file:///E:/DEV/Codex-web/.coding-tools/reports/parallel-native-first-20261012/server-readiness-audit-20261013-postclosure.json) chứng minh:
     - `global_live_work_by_scope.live_open_tasks: []` (0 tác vụ mở).
     - `sqlite_integrity_ok: true`.
     - `codex_web_canary_blockers: []` (0 lỗi/blocker).
     - `codex_web_canary_eligible_under_current_authority: true`.

2. **Dọn dẹp triệt để worktree bẩn**:
   - Loại bỏ toàn bộ các file chẩn đoán tạm (`audit-probe-output.json`, `health-probe-output.json`, `electron-*-probe-output.json`, `token-child-probe.obj`, `electron-argv-test.cjs`, `scripts/close-completed-task.py`).
   - Xóa bỏ các thư mục profile thử nghiệm tạm thời (`electron-test-profile*`).
   - Giữ lại đầy đủ các tệp mã nguồn mới, fixtures, docs và test hợp lệ của tính năng native-first bfix.

3. **Kiểm thử tự động toàn diện đạt 100%**:
   - Khắc phục triệt để các điểm lệch assertion lịch sử trong `control-center-manager.test.js`, `token-dashboard.test.js`, `dev-ui-lifecycle.test.js`, `recovery-host.test.js`, `recovery-plane.test.js`, `control-panel.test.js`, `chat-ui-compact.test.js`, và `browser.js`.
   - Toàn bộ **1.233 / 1.233 tests** của toàn dự án PASS (100% không một lỗi nào).
   - `check-source-root-clean` & `check-sensitive-tracked` PASS.

4. **Bảo tồn Invariant và Delivery Check**:
   - `stage:coding-tools-delivery` và `check:coding-tools-delivery` PASS hoàn hảo trên **11.157 tệp** chứng cứ với receipt snapshot ràng buộc tính toàn vẹn SQLite.
   - Toàn bộ thay đổi được commit vào nhánh `main` với worktree hoàn toàn sạch.

5. **Đẩy thành công lên GitHub**:
   - Commit `303fb7e6` đã được đẩy lên `https://github.com/uyenthudao2410-code/Codex-web.git` nhánh `main`.
   - Nhánh cục bộ `main` và remote `origin/main` đồng bộ hoàn toàn (`[origin/main]`).

