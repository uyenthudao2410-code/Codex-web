# Trợ lý Web MCP (GPT-WebCodex)

Một công cụ nhỏ giúp phiên bản web của ChatGPT có thể đọc và ghi trực tiếp tệp mã nguồn trên máy tính của bạn. **Khi hạn mức Codex / Cursor bị hết, bạn có thể sử dụng công cụ này làm "phiên bản thay thế mượt mà", giải quyết triệt để vấn đề hết hạn mức**. Không cần cài đặt Docker, chỉ cần nhấp đôi là có thể sử dụng trên Windows.

---

## 📌 Tại sao phát triển công cụ này?

Nhiều bạn làm lập trình chắc hẳn đã gặp phải tình huống trớ trêu: **Hạn mức đăng ký Codex hoặc Cursor vừa dùng vài ngày đã báo hết**, muốn tiếp tục dùng ChatGPT bản web để viết code nhưng bản web lại không thể trực tiếp đọc và chỉnh sửa tệp tin cục bộ, việc sao chép và dán thủ công vô cùng phiền phức.

Mục đích cốt lõi của trợ lý này là: **Cung cấp một giải pháp thay thế "không cần cấu hình" cho Codex**. Công cụ đóng gói môi trường Python, đường truyền tunnel và cơ chế cách ly quyền truy cập thư mục thành một ứng dụng Windows `.exe` thông thường.

Sau khi khởi động trợ lý, bạn chỉ cần đưa ra yêu cầu trong khung chat ChatGPT bản web quen thuộc, AI sẽ có thể:
- 📁 **Đọc trực tiếp các tệp mã nguồn trong dự án cục bộ hoặc trên Desktop**
- ✏️ **Tạo mới tệp, chỉnh sửa mã nguồn, sửa lỗi (Bug) trực tiếp trong thư mục dự án của bạn**

Khi hết hạn mức Codex, bạn chỉ cần chuyển sang ChatGPT bản web kết nối với trợ lý này để tiếp tục tái cấu trúc mã nguồn một cách mượt mà.

---

## 💡 Các điểm nổi bật

- **Giải pháp thay thế Codex**: Không lo hết hạn mức Codex, kết hợp ChatGPT bản web với trợ lý để tiếp tục chỉnh sửa code cục bộ.
- **Không cần cài Docker**: Tích hợp sẵn môi trường Python di động bên trong phần mềm, nhấp đôi để chạy ngay, không cần sửa biến môi trường hệ thống.
- **Cách ly quyền thư mục**: Mỗi lần sử dụng chỉ cấp quyền cho **duy nhất một thư mục dự án** được chọn, tuyệt đối không truy cập trái phép các ổ đĩa hoặc tệp riêng tư khác trên máy tính.
- **Mã hóa khóa cục bộ**: API Key được lưu trữ mã hóa trong kho khóa DPAPI cục bộ của Windows, không tải lên bất kỳ máy chủ bên thứ ba nào.
- **Tự động kết nối lại qua Proxy**: Tự động nhận diện proxy hệ thống, chẩn đoán kết nối chạy ngầm, tự động kết nối lại khi mất mạng.

---

## 📦 Cách tải về và sử dụng

Sử dụng thông thường **hoàn toàn không cần cấu hình bất kỳ môi trường lập trình nào**:

1. Nhấp trực tiếp vào liên kết **[Releases](../../releases)** ở bên phải trang GitHub.
2. Tải về gói cài đặt `.exe` mới nhất (ví dụ `web-mcp-assistant-setup-0.1.6.exe`), nhấp đôi để cài đặt.

---

## 💻 Biên dịch mã nguồn cho nhà phát triển (Tùy chọn)

Nếu bạn muốn tùy chỉnh mã nguồn hoặc tự đóng gói:

```powershell
# Nhân bản dự án và cài đặt phụ thuộc
git clone https://github.com/3169657175/gpt-webcodex.git
cd gpt-webcodex
npm install

# Chạy thử cục bộ
npm start

# Đóng gói tạo file cài đặt chỉ với 1 lệnh
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\build.ps1
```

---

## 📜 Giấy phép mã nguồn mở

- Dự án này được phát hành dưới dạng mã nguồn mở theo giấy phép [MIT License](LICENSE).
- Tích hợp mã nguồn [Coding Tools MCP](https://github.com/anthropics/anthropic-tools), tuân thủ quy định Apache License 2.0, xem chi tiết tại [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

