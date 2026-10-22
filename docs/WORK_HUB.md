# Không gian làm việc của Execution Hub

Thanh đầu ứng dụng có ba mục **Làm việc / Lịch sử / Cài đặt**, cùng dự án và máy đang dùng. **Đổi dự án** mở các thư mục gần đây. **Trạng thái & công cụ** chứa kiểm tra kết nối, khởi động và các trang vận hành ít dùng.

Trong **Làm việc**, cột **Tệp & ngữ cảnh** luôn ở bên cạnh công việc đang chọn. Có thể tìm, xem và chọn tệp trong lúc chuyển giữa các tab của công việc mà không phải mở một trang riêng.

## Luồng hằng ngày

| Tab | Thao tác chính |
|---|---|
| **Yêu cầu** | Nhập trực tiếp vào ô **Bạn muốn làm gì?**, thêm nội dung tệp từ cột bên rồi sao chép sang client đang sử dụng. Mở **Soạn từ mẫu hoặc loại công việc** khi cần trợ giúp cấu trúc yêu cầu. |
| **Tiến trình** | Theo dõi kế hoạch, tệp và kết quả đã ghi nhận; lưu điều chỉnh để chuyển cho trợ lý. Phân biệt nội dung đã lưu với nội dung đã được xác nhận. |
| **Thay đổi** | Xem tệp đã đổi, so sánh staged/unstaged và lịch sử Git. Nhãn tệp của công việc giúp phân biệt dữ liệu task với toàn bộ thay đổi trong thư mục. |
| **Kiểm chứng** | Chọn một lệnh đã lưu của dự án rồi chạy và theo dõi kết quả. Mở **Thêm lệnh kiểm tra** để lưu lệnh mới kèm thư mục chạy và địa chỉ xem trước nếu có. |
| **Kết quả** | Xem sản phẩm, mở hoặc sao chép đường dẫn, xuất báo cáo và đọc bản bàn giao trước khi tiếp tục công việc. |

**Ctrl+K** mở tìm nhanh. Có thể tìm không dấu; chọn kết quả để mở đúng phần liên quan. Các tab cũng dùng được bằng bàn phím.

## Nháp và dữ liệu theo dự án

Nháp được lưu trên máy này trong bộ nhớ của ứng dụng (`localStorage`), cùng loại công việc, các trường đang nhập, mẫu đã chọn và nội dung yêu cầu. Chuyển dự án sẽ khôi phục nháp tương ứng. Giỏ tệp và ghi chú cũng được tách theo dự án. Dùng **Xóa nháp** để bắt đầu lại.

Lưu nháp không đồng nghĩa đã gửi yêu cầu cho model. Dữ liệu này không phải bản sao lưu và không tự đồng bộ sang máy khác; nếu ứng dụng báo không lưu được, hãy sao chép nội dung cần giữ.

## Theo dõi lệnh đang chạy

Lệnh được gửi qua runtime hiện hữu; mỗi lần chạy có định danh riêng. Mở tab khác rồi quay lại chỉ quan sát lần chạy đang có. Khi trạng thái chưa xác định, hãy lấy kết quả mới để kiểm tra trước khi chạy lại.

**Dừng lệnh** gửi yêu cầu dừng; giao diện chỉ báo đã dừng khi nhận được kết quả xác nhận. Mất phản hồi không chứng minh process đã kết thúc. Nếu gửi nội dung vào lệnh mà chưa nhận phản hồi, cập nhật output trước khi quyết định gửi lại. Một phần output có thể không còn sau khi runtime khởi động lại.

## Xem và sửa tệp

Các thao tác tệp dùng dự án đang chọn. Cột bên hiển thị tìm kiếm, danh sách tệp, nội dung xem nhanh và các tệp đã chọn. Mở kết quả tìm kiếm để xem dòng liên quan rồi thêm đúng tệp vào ngữ cảnh. Kiểm tra nhãn rút gọn khi tệp hoặc kết quả tìm kiếm vượt giới hạn.

**Sửa nhanh** mở nội dung văn bản để chỉnh sửa. **Lưu thay đổi** kiểm tra phiên bản đã đọc để tránh ghi đè thay đổi bên ngoài; **Hủy sửa** bỏ phần chỉnh sửa chưa lưu. **Thêm đường dẫn thủ công** mở các trường nhập tệp ít dùng; danh sách đã chọn và nút **Đưa nội dung vào yêu cầu** luôn hiện bên dưới.

Tạo tệp mới và nhập tài liệu nằm trong phần mở rộng của tab **Yêu cầu**. Khi nhập tệp, xem thư mục đích và kết quả xử lý trùng tên.

Diff hiện tại mô tả trạng thái Git của thư mục đang dùng. Không suy ra mọi thay đổi đều do công việc hiện tại tạo ra. Báo cáo và sản phẩm phải giữ rõ phần đã kiểm chứng, chưa kiểm chứng hoặc chưa lấy được chi tiết.

## Công cụ mở khi cần

- **Soạn từ mẫu hoặc loại công việc:** chọn loại việc hoặc mẫu để tạo nội dung trong ô yêu cầu chính; có thể tiếp tục chỉnh sửa trực tiếp.
- **Quản lý mẫu yêu cầu:** tạo, sửa hoặc xóa mẫu; các biến dự án, yêu cầu và tệp được giải thích ngay trong form.
- **Thêm lệnh kiểm tra:** lưu tên, lệnh, thư mục chạy và địa chỉ xem trước tùy chọn; danh sách lệnh hiện có luôn ở đầu tab Kiểm chứng.
- **Nhập tài liệu hoặc tạo tệp mới:** nhập tệp và lưu đoạn mã thành tệp.
- **Hàng đợi, lịch kiểm tra & mục tiêu:** chuẩn bị việc tiếp theo và cấu hình có giới hạn; lịch được xét khi ứng dụng đang mở.
- **Công việc, kiến thức & tích hợp:** xem công việc/trợ lý, quản lý ghi chú, hướng dẫn, liên kết hội thoại và kết nối đã cấu hình.

## Phạm vi và bằng chứng

Tài liệu này mô tả giao diện trong source của **Electron Execution Hub + Coding Tools MCP**. Nó không xác nhận cùng giao diện đã có trong bản cài đang chạy hoặc bản phát hành. Năng lực thực thi vẫn phụ thuộc runtime, workspace, quyền và client được cấu hình; trang Làm việc dùng các cơ chế hiện hữu của sản phẩm.
