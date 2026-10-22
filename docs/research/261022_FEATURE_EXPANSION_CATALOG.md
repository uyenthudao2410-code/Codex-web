# Danh mục tính năng bổ sung cho Codex Web

Ngày khảo sát: **22/10/2026**; mốc đối chiếu nguồn local **14:29 (+07), 07:29 UTC**.

## 1. Kết luận và phạm vi bổ sung

Bản phân tích giao diện trước chưa bao quát nhu cầu bổ sung chức năng. Tài liệu này mở rộng thành **40 ứng viên tính năng**, gồm thao tác tệp, ngữ cảnh, thực thi, Git, công việc dài, tích hợp và tiện ích. Đây là backlog để chọn triển khai; không phải cam kết đưa cả 40 mục lên màn hình chính hoặc xác nhận chúng đã được cài đặt.

**Nhóm nên bổ sung đầu tiên:** thư viện lời nhắc; giỏ ngữ cảnh tệp; cây thư mục và xem mã; diff và xem trước patch; khay sản phẩm đầu ra; lệnh dự án đã lưu; thông báo có ích; tìm kiếm công việc. Chúng tạo thành luồng đầy đủ: **chọn tệp → giao việc → xem thay đổi → kiểm thử → nhận sản phẩm**.

Phần mềm hiện có nhiều primitive phía runtime nhưng thiếu bề mặt thao tác thuận tiện cho người dùng. “Đã có backend” không đồng nghĩa người dùng đã có thể thực hiện chức năng bằng một thao tác trong Electron. Ngược lại, handoff, build/test, dự án gần đây và điều khiển tác vụ đã có UI; không tính chúng là chức năng hoàn toàn mới.

## 2. Phiên bản và mức bằng chứng

| Nguồn | Phiên bản quan sát | Mức bằng chứng |
|---|---|---|
| Local `E:\DEV\Codex-web` | `main`, HEAD `5c5e207265f56a69b72f16dd78c4d2951f382609`; có thay đổi đồng thời chưa commit trong renderer, Electron, runtime, tests và `.coding-tools`. | Đọc nguồn và focused tests như tài liệu đặc tả; không chạy test sản phẩm hoặc xác nhận live trong đợt khảo sát. |
| Chat On Steroids (CoS) | `557d0bbb25f40539d8ee2629b64f4fde1b3989eb`; commit mới hơn `e4a26876…` dùng trong bản phân tích trước. | Đọc README và nguồn liên quan; không chạy ứng dụng. |
| WebCodex upstream (W) | `2bac8248a2e635022ae9c636fc1287bc01b6b833`. | Đọc nguồn và hợp đồng hiện hành; không suy ra bộ cài, GUI hoặc mọi nền tảng đã được nghiệm thu. |

Trong các bảng: **Mới** = chưa tìm thấy sản phẩm tương đương trong renderer/IPC/runtime đã khảo sát; không phải bằng chứng vắng mặt ở mọi nhánh. **Một phần** = đã thấy primitive hoặc một phần UI, cần tích hợp thêm. **Đã có** = hoàn thiện trải nghiệm của chức năng hiện hữu. Các mức công sức thấp/vừa/lớn là nhận định kỹ thuật tương đối, chưa phải ước lượng thời gian.

Nguồn cảm hứng trong bảng được ghi là **CoS**, **W**, hoặc **Đề xuất riêng**. Chỉ các đường dẫn được dẫn ở mục 9 mới là bằng chứng đã đọc; thiết kế đích của local là đề xuất, không phải màn hình đã triển khai ở kho tham khảo.

## 3. Chuẩn bị yêu cầu và ngữ cảnh

| ID | Tính năng và thao tác cụ thể | Local hiện tại / phần phải bổ sung | Ưu tiên · công sức |
|---|---|---|---|
| F01 | **Thư viện lời nhắc và đoạn mẫu.** Lưu “Sửa lỗi”, “Review trước commit”, “Viết tài liệu”; điền biến dự án/tệp/yêu cầu rồi xem trước và sao chép. | **Mới**, ngoài một prompt hướng dẫn cố định. Cần lưu, sửa, tìm, đặt tên và tái sử dụng. Chuẩn bị gói yêu cầu local, không ngầm gửi vào chat. Đề xuất riêng, có thể liên kết thư viện Skills của F34. | P0 · thấp–vừa |
| F02 | **Bản nháp theo dự án.** Chuyển dự án hoặc đóng cửa sổ vẫn giữ yêu cầu đang soạn và tệp đã chọn. | **Mới**. Cần kho nháp local có giới hạn; tách nháp giữa dự án, không ghi nội dung nháp vào log. CoS. | P1 · thấp–vừa |
| F03 | **Ghim và đặt tên dự án.** Giữ các dự án dùng thường xuyên ở đầu danh sách, tìm theo tên hoặc đường dẫn. | **Một phần**: MRU 50 và bộ chuyển thư mục đã có. Bổ sung metadata ghim/tên, không tạo registry dự án thứ hai. Đề xuất riêng; CoS là tham khảo tổ chức dự án/chat, không phải chứng cứ local đã có project pin. | P0 · thấp |
| F04 | **Thẻ loại công việc.** Chọn Sửa lỗi / Thêm tính năng / Review / Test lỗi / Tài liệu; chỉ điền dữ liệu cần cho loại đó. | **Một phần**: `agent_workflow` có các workflow và phase. Cần form sinh yêu cầu, điều kiện hoàn thành, tệp liên quan và kiểm chứng; kế hoạch AI cần client/controller phù hợp. | P0 · vừa |
| F05 | **Giỏ ngữ cảnh `@file` và đoạn mã.** Chọn một số tệp hoặc dòng, thấy dự án/đường dẫn/kích thước rồi tạo gói ngữ cảnh. | **Một phần**: workflow có `paths`, `queries` và hạn mức tệp/byte. Cần UI chọn/bỏ chọn/xem trước; `@file` là thao tác local hoặc adapter host, chưa phải tính năng composer ChatGPT của app. CoS, W. | P0 · vừa |

## 4. Tệp, chỉnh sửa và sản phẩm đầu ra

| ID | Tính năng và thao tác cụ thể | Local hiện tại / phần phải bổ sung | Ưu tiên · công sức |
|---|---|---|---|
| F06 | **Cây thư mục, tìm trong mã và xem nhanh.** Bấm tệp → xem mã; tìm kết quả → mở đúng dòng → thêm vào giỏ ngữ cảnh. | **Một phần**: đọc/list/search đã có trong `file_tools.py`. Cần viewer và đường gọi có phạm vi; không cần mở thêm tool public. CoS, W. | P0 · vừa |
| F07 | **Kéo thả/chọn tài liệu và ảnh.** Xem nguồn và thư mục đích, xác nhận đưa tệp vào dự án rồi dùng cho yêu cầu. | **Một phần**: document/image runtime có sẵn, chưa thấy dropzone/attachment UI. Cần xử lý trùng tên, xác nhận ghi, file lớn và phạm vi. Không tự kéo attachment từ phiên ChatGPT. CoS, W. | P1 · vừa |
| F08 | **Sửa nhanh tệp văn bản.** Mở tệp → sửa đoạn nhỏ → xem diff → lưu; báo xung đột nếu tệp đã đổi bên ngoài. | **Một phần**: guarded patch và preimage đã có. Cần editor nhỏ và save qua boundary hiện hành. Không nhận một textarea là đầy đủ IDE. CoS; W có primitive, Workbench upstream là chỉ đọc. | P1 · vừa |
| F09 | **Diff trực tiếp theo tác vụ.** Bấm tệp thay đổi → so trước/sau → mở dòng liên quan; giữ snapshot để review khi công việc còn chạy. | **Một phần**: Git diff/committed review đã có, danh sách file UI chủ yếu là text. Phải phân biệt thay đổi của tác vụ với toàn bộ dirty worktree. CoS, W. | P0 · vừa |
| F10 | **Xem trước và duyệt patch.** Xem file, diff, phạm vi và kết quả kiểm tra trước khi xác nhận đúng bản vá. | **Một phần**: approved-patch bridge và kiểm tra preimage đã có. Cần màn duyệt ràng buộc đúng patch/phiên bản; sửa patch làm mất hiệu lực phê duyệt cũ. Không tự áp dụng từng hunk ngoài contract hiện có. | P1 · vừa |
| F11 | **Lưu đoạn code thành tệp.** Dán/chọn code → chọn tên và thư mục → xem trước ghi đè → tạo file. | **Mới ở UI**; runtime ghi tệp đã có. CoS có chức năng code-file mới. Bản đầu dùng clipboard/chọn nội dung rõ ràng; nhận trực tiếp code block từ ChatGPT cần adapter riêng. | P1 · thấp–vừa |
| F12 | **Khay sản phẩm đầu ra.** Kết thúc tác vụ thấy report, ảnh và tệp build; mở, preview hoặc mở thư mục chứa. | **Một phần**: artifact refs, đường dẫn/hash và document inspect đã có. Cần viewer đúng loại; PDF/DOCX extraction không đồng nghĩa đã có PDF/Office renderer. CSV/XLSX preview là phần mở rộng riêng nếu cần. CoS, W. | P0 · vừa |
| F13 | **Đi tới symbol, tham chiếu và tác động thay đổi.** Chọn hàm → tìm định nghĩa/nơi gọi/test liên quan khi provider sẵn sàng. | **Một phần**: semantic localization/graph reachable qua workflow; chưa thấy API smart-v3 riêng cho đầy đủ editor navigation/diagnostics. Cần UI và kiểm tra provider, không hiển thị kết quả suy đoán là LSP thật. W. | P2 · vừa–lớn |
| F14 | **Xem trước website đang phát triển.** Chọn lệnh dev đã lưu → theo dõi Job → mở URL preview được xác nhận → xem lỗi liên quan. | **Đề xuất riêng**, cần UI quản lý preview và nối đúng Job/port. Không tự suy ra localhost là sẵn sàng hay tự bật server sau mọi build. Browser QA nâng cao thuộc F37. | P1 · vừa |

## 5. Điều hành công việc và nhiều agent

| ID | Tính năng và thao tác cụ thể | Local hiện tại / phần phải bổ sung | Ưu tiên · công sức |
|---|---|---|---|
| F15 | **Hàng đợi công việc.** Thêm, đổi thứ tự, tạm dừng hàng đợi; chọn việc kế tiếp để bắt đầu trong đúng dự án. | **Mới**: background Job không phải task queue. Cần queue bền, dispatch một lần, kiểm tra authority khi bắt đầu; một checkout không tự có nhiều writer. Phần cần AI chờ host/controller phù hợp. | P1 · lớn |
| F16 | **Bảng nhiều tác vụ theo dự án.** Thấy việc đang chạy, chờ, cần duyệt và xong; bấm mở đúng công việc. | **Một phần**: scoped task inventory có sẵn nhưng UI thường trình bày một task. Cần danh sách/filter theo scope, không ghép các task thành một state giả. W. | P1 · vừa |
| F17 | **Kế hoạch và tiêu chí hoàn thành.** Xem các mốc, sửa yêu cầu hoặc tiêu chí; mỗi mốc hiện kết quả kiểm chứng và blocker. | **Một phần**: task steps, goal/problem và proof đã có. Cần trình bày dễ đọc và thao tác gửi thay đổi, không thêm lifecycle Plan cạnh tranh. CoS, W. | P1 · vừa |
| F18 | **Gửi điều chỉnh khi đang làm.** Nhập “chỉ sửa module A”, “dừng sau test”; thấy đã lưu, đã chuyển và đã được xác nhận riêng. | **Một phần**: feedback/replan/message primitives đã có. Cần ô điều chỉnh và acknowledgment; không coi lưu message là model đã đọc hoặc tự chèn vào chat. CoS, W. | P1 · vừa–lớn |
| F19 | **Bảng lệnh/Job.** Xem stdout/stderr, lệnh đang chờ input, gửi input nếu backend hỗ trợ, dừng và mở lại đúng Job. | **Một phần**: exec/session control/poll/read/write/kill đã có. Cần UI; khả năng pipe/TTY tùy backend, không hứa terminal toàn màn hình ở mọi route. Theo dõi lại không chạy lại lệnh. CoS, W. | P1 · vừa–lớn |
| F20 | **Lệnh dự án đã lưu.** Đặt tên “Test module”, “Lint”, “Build bản thử”; xem lệnh và thư mục trước chạy, thấy kết quả/file đầu ra. | **Một phần**: detect project, build/test và artifact hashing đã có UI. Phần mới là lưu recipe có tên, chọn đúng phạm vi và tái sử dụng; không gọi build/test cơ bản là chức năng còn thiếu. | P0 · vừa |
| F21 | **Bảng worker/reviewer.** Thấy agent nào làm gì, ở đâu, trạng thái và kết quả; yêu cầu review hoặc dừng đúng lane được phép. | **Một phần**: delegation/Job UI, persistent reviewer lane và bridge đã có. Cần thẻ scope/kết quả/điều khiển rõ ràng. Lane chỉ đọc không biến thành writer; routing auto vẫn evidence-gated. CoS, W. | P1 · vừa |
| F22 | **Thông báo khi cần chú ý và làm việc nền.** Nhận thông báo khi xong, lỗi, chờ duyệt; bấm quay về đúng công việc. Có thể chọn giữ máy thức trong lúc Job thật đang chạy. | **Mới trong scope đã khảo sát**: hiện chủ yếu toast/tray. Cần native notification, khử trùng sự kiện; tùy chọn keep-awake phải nhả khi xong/mất bằng chứng chạy. Không báo từng tool call. CoS. | P0 · thấp–vừa |
| F23 | **Tiếp tục theo mục tiêu có giới hạn.** Đặt tiêu chí, hạn thời gian/lượt; xem vì sao chờ hoặc dừng; có nút dừng rõ ràng. | **Một phần**: goal/continuation ledger và driver đã có. Cần UI dùng đúng grant/controller hiện hành. Chưa có grant thì chỉ chuẩn bị yêu cầu; không thêm Loop vô hạn hoặc coi Goal là scheduler. CoS, W. | P2 · lớn |
| F24 | **Lịch kiểm tra định kỳ.** Lưu lịch chạy một recipe đã chọn, xem lần chạy kế tiếp/kết quả, tắt lịch. | **Đề xuất riêng**, chưa tìm thấy scheduler sản phẩm tương đương. Bản đầu nên giới hạn check/test có phạm vi; cần scheduler bền, missed-run policy, authority và host availability. Không tự deploy/commit/chạy AI vô hạn theo lịch. | P2 · lớn |

## 6. Git, lưu tiến độ và kiến thức dự án

| ID | Tính năng và thao tác cụ thể | Local hiện tại / phần phải bổ sung | Ưu tiên · công sức |
|---|---|---|---|
| F25 | **Git Changes/History.** Xem staged/unstaged, commit trước, diff và blame của dòng đang đọc. | **Một phần**: Git status/diff/log/show/blame có implementation; UI có badge. Cần panel và điều hướng, giữ provenance/HEAD của kết quả. W. | P1 · vừa |
| F26 | **Commit có chọn tệp và xem trước.** Chọn file, nhập message, xem đúng thay đổi staged và kết quả sau commit. | **Mới như API/UI sản phẩm**: generic exec không phải Git commit feature. Cần expected HEAD, chống lẫn work và chạy `stage:coding-tools-delivery` rồi `check:coding-tools-delivery` trước mỗi commit/push. Không tự push. W. | P2 · lớn |
| F27 | **Làm việc trong worktree riêng.** Tạo bản làm việc từ nhánh/commit rõ ràng; review trước khi tích hợp; giữ được công việc gốc. | **Mới như API/UI sản phẩm**. Cần quản lý đường dẫn, ref, scope và lifecycle. Đặt ngoài `.coding-tools`; không mang dirty changes sang ngầm hoặc tự xóa sau khi xong. CoS, W. | P2 · lớn |
| F28 | **Checkpoint và hoàn tác theo phạm vi.** Xem trạng thái trước/sau; chọn phần cần khôi phục và xem diff tác động trước xác nhận. | **Đề xuất riêng** dựa trên nguyên tắc review/restore của W. Cần thiết kế snapshot/inverse patch, kiểm tra file hiện tại và bảo vệ thay đổi ngoài task; không triển khai bằng reset/clean toàn repo. | P2 · lớn |
| F29 | **Tiếp tục công việc qua chat mới.** Xem mục tiêu, đã làm, chưa kiểm chứng, file và bước tiếp theo rồi dùng capsule hiện có. | **Đã có** handoff và continuity. Bổ sung màn xem trước, tìm đúng task và revalidate file/Git/Job; không xây memory thứ hai hay hứa khôi phục chat chưa lưu. CoS, W. | P0 · thấp–vừa |
| F30 | **Xuất báo cáo tác vụ.** Một thao tác tạo Markdown/TXT hoặc DOCX gồm kết quả, file đổi, test/build, sản phẩm, giới hạn và việc còn lại. | **Một phần**: completion report và document create đã có. Cần nút export, chọn đích, preview và lọc nội dung nhạy cảm. Export không tự gửi cho người khác. | P1 · vừa |
| F31 | **Tìm kiếm chung.** Gõ một chỗ để tìm thao tác, dự án, task, report và lời nhắc; mở đúng mục khớp. | **Một phần**: history/search file có nguồn riêng, chưa thấy index sản phẩm chung. Ưu tiên metadata trước, index nội dung local được sở hữu có giới hạn; chat riêng cần adapter/chấp thuận riêng. CoS, W. | P0 · vừa |
| F32 | **Ghi chú và quy ước dự án.** Ghim lệnh quan trọng, quyết định, đường dẫn; chọn ghi chú đưa vào yêu cầu tiếp theo. | **Một phần nền tảng**, không phải wiki hiện hữu: operational knowledge checkpoint đã có. Cần ghi chú do người dùng quản lý, nguồn/thời điểm rõ ràng; không để ghi chú thay authority hoặc tự ghi đè AGENTS.md. | P1 · vừa |

## 7. Tích hợp tùy chọn sau luồng chính

| ID | Tính năng và thao tác cụ thể | Local hiện tại / phần phải bổ sung | Ưu tiên · công sức |
|---|---|---|---|
| F33 | **Chọn máy và dự án thực thi.** Chọn Windows/Ubuntu đã đăng ký, thấy đúng đường dẫn, online/readiness/quyền rồi tạo công việc mới. | **Một phần**: Control Plane enrollment/authority/workspace đã có. Cần target picker dùng binding đã xác minh; đổi lựa chọn không retarget Job đang chạy. SSH resource đặt tên là mở rộng riêng, không đồng nghĩa toàn bộ file/Git/LSP đã chạy remote. W. | P1 · vừa–lớn |
| F34 | **Thư viện Skills theo dự án.** Chọn mẫu quy trình có hướng dẫn; import local/GitHub, xem nội dung/phiên bản và bật cho dự án. | **Mới ở sản phẩm**: chưa thấy Skills loader/store chung của local MCP trong scope khảo sát. Phân biệt hướng dẫn với executable, biết client nào tiêu thụ Skill; không thêm marketplace trước khi có nhu cầu. CoS, W. | P2 · vừa–lớn |
| F35 | **Nhập yêu cầu bằng giọng nói.** Bấm ghi → chuyển thành chữ → sửa → tự xác nhận dùng yêu cầu. | **Mới**, cần chọn engine và luồng microphone. Bản đầu chỉ tạo nháp local; không tự gửi hoặc chạy lệnh theo âm thanh. CoS có triển khai Windows, không suy ra hỗ trợ mọi OS. | P2 · vừa–lớn |
| F36 | **Quản lý tích hợp MCP/plugin.** Xem tích hợp đã cài, trạng thái hoạt động, cấu hình theo dự án và tắt khi không dùng. | **Mới như manager tổng quát**: adapter Codex/OpenCode hiện hữu không phải plugin manager. Cần lifecycle/capability/credentials riêng; cấu hình đã lưu khác active. Giữ smart-v3 tám tool của runtime chính. CoS, W. | P2 · lớn |
| F37 | **Browser QA tự động.** Chia sẻ một tab hoặc dùng profile riêng để AI xem trang, chụp ảnh, kiểm tra console/network và thử luồng web. | **Mới**, cần adapter browser, lifecycle profile và quyền gắn đúng tab; chặn stale element reference. Chỉ thao tác trang được chia sẻ hoặc profile đã quản lý. Tích hợp hội thoại ở F39 cần dữ liệu và quyết định kiến trúc riêng. CoS, W. | P2 · lớn |
| F38 | **Tự động thao tác ứng dụng Windows.** Chọn cửa sổ ứng dụng, cho AI xem UI/screenshot và thực hiện phần việc GUI được giao; theo dõi và dừng được. | **Mới**, cần adapter UI Automation/capture/input có window identity và quyền riêng. CoS có source; không suy ra MCP hiện tại đã có thể điều khiển AutoCAD hoặc mọi ứng dụng Windows. | P2 · lớn |
| F39 | **Gắn hội thoại vào dự án, ghim, tìm/xuất và rẽ nhánh hội thoại.** Chọn chat gốc hoặc câu trả lời để thử hướng xử lý khác mà giữ liên kết với task. | **Mới/khác kiến trúc hiện tại**. CoS có conversation data/recorder/adapter; local chủ động không có chúng. Bản đầu có thể lưu URL/nhãn chat do người dùng nhập; nội dung, message identity và fork thực sự cần tích hợp host được hỗ trợ. Chat branch khác Git branch. | P2 · lớn |
| F40 | **Tài nguyên SSH đặt tên.** Chọn máy/thư mục đã cấu hình để chạy kiểm tra, nhận output và kết quả; tránh dán lại host/key vào mỗi yêu cầu. | **Mới như capability SSH sản phẩm**. W có SSH command resources; CoS có remote project qua SFTP/terminal. Phải quyết định chỉ command remote hay cả file/Git remote; không gắn nhãn mọi thao tác đã chuyển máy khi mới đổi shell. | P2 · lớn |

## 8. Các đợt triển khai tạo ra chức năng dùng được

### Đợt A — Giao việc và nhận kết quả

Tập trung **F01, F03–F06, F09, F12, F20, F22, F29, F31**. Có thể chia nhỏ từng chức năng, nhưng phải hoàn thành một chu trình thật: chọn dự án/tệp → chuẩn bị yêu cầu → xem tác vụ và diff → chạy recipe → mở sản phẩm đầu ra. Tác vụ cần AI vẫn đi qua client/controller đã cấu hình; app không tự trở thành chat model.

Nghiệm thu cụ thể:

- Lời nhắc đã lưu vẫn còn sau mở lại, biến dự án/tệp được điền đúng; preview không tự gửi.
- Giỏ ngữ cảnh không lẫn tệp giữa hai dự án; tệp đã đổi được đọc lại trước thao tác cần phiên bản chính xác.
- Diff ghi rõ task/base/current và phần thay đổi ngoài tác vụ; artifact có nguồn, đường dẫn và trạng thái hiện tại.
- Recipe chạy đúng dự án và Job; mở lại màn hình chỉ theo dõi Job cũ. Chỉ công bố test count khi parser có bằng chứng, không coi exit 0 là mọi kiểm thử đã chạy.
- Một sự kiện hoàn tất chỉ thông báo một lần; lỗi và cần duyệt dẫn về đúng task.
- Handoff hiển thị rõ phần chưa kiểm chứng; mở preview không tạo Job hay chạy lại lệnh.

### Đợt B — Nhiều công việc và can thiệp trong lúc chạy

Tập trung **F02, F07–F08, F10–F11, F14–F19, F21, F25, F30, F32–F33** theo nhu cầu thực tế. Hàng đợi là thay đổi lớn hơn một danh sách UI, nên tách ra khỏi việc hiển thị nhiều tác vụ.

Nghiệm thu các boundary chính: item queue bắt đầu tối đa một lần dù reconnect; scope/authority còn hợp lệ khi dispatch; steering phân biệt đã lưu/đã chuyển/đã nhận; editor chặn stale overwrite; terminal chỉ hiện input khi route hỗ trợ; target picker không di chuyển công việc cũ; worker reviewer giữ đúng quyền đã cấp.

### Đợt C — Năng lực chuyên sâu tùy chọn

**F13, F23–F24, F26–F28, F34–F40** cần thiết kế/kiểm chứng riêng trước tích hợp. Chọn theo công việc thực tế: semantic navigation cho dự án lớn; worktree cho sửa song song; Skills cho quy trình lặp lại; browser QA cho phát triển web; voice cho nhập yêu cầu; desktop automation khi công việc có bước GUI. Không bật đồng loạt chỉ vì kho tham khảo có source.

Lịch, continuation hoặc plugin không được giả định luôn có model/controller online. UI phải phản ánh waiting/unknown và không dùng retry như một cách phát lại tác động không xác định. Model routing `auto` hiện vẫn resolve về `deterministic` khi chưa qua evidence gate. Các capability mới có thể cần handler, schema/action và adapter mới; giữ tám tool public không đồng nghĩa mọi tính năng chỉ cần sửa renderer. Mọi thay đổi contract phải qua kiểm chứng và quy trình discovery/activation phù hợp.

## 9. Bằng chứng chính và implementation để tái sử dụng

### Local

- Prompt hướng dẫn và workflow hiện có: [renderer/index.html](E:/DEV/Codex-web/renderer/index.html:821), [workflow schema](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/tool_schema.py:226), [workflow handler](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/workflow_tools.py:780).
- MRU: [config.js](E:/DEV/Codex-web/electron/services/config.js:128); context paths/queries: [tool_schema.py](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/tool_schema.py:387).
- File primitives: [file_tools.py](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/file_tools.py:59), [list/search](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/file_tools.py:167), [guarded patch](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/file_tools.py:588); [approved patch bridge](E:/DEV/Codex-web/electron/services/controlPlaneApprovedPatchBridge.js:655).
- Git: [git_tools.py](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/git_tools.py:481); [immutable committed review](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/git_tools.py:291).
- Build/test detection và artifact hashing: [buildVerificationService.js](E:/DEV/Codex-web/electron/services/buildVerificationService.js:16); artifacts: [artifact_refs.py](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/artifact_refs.py:13); documents: [document_tools.py](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/document_tools.py:211).
- Scoped tasks: [task_state.py](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/task_state.py:1056); Job input/output: [session_control.py](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/session_control.py:387); lanes: [coordination.py](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/coordination.py:235).
- Handoff có UI: [panel.html](E:/DEV/Codex-web/renderer/panel.html:355), [panel.js](E:/DEV/Codex-web/renderer/panel.js:622); [knowledge checkpoints](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/controller_continuity.py:168); [continuity core](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/controller_continuity.py:1018).
- Semantic context: [context_tools.py](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/context_tools.py:310), [semantic_localization.py](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/semantic_localization.py:19), [semantic_graph.py](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/semantic_graph.py:351).
- Host boundary: [chat-page-retirement.test.js](E:/DEV/Codex-web/tests/chat-page-retirement.test.js:10), [browserPreload.js](E:/DEV/Codex-web/electron/browserPreload.js:5). Đây là căn cứ không gọi các tiện ích chat/browser là chức năng sẵn có của Hub.
- Current execution mode: [CURRENT_STATE.md](E:/DEV/Codex-web/docs/CURRENT_STATE.md:3). Source hiện mặc định `local / host_user`; sandbox là tùy chọn. Không dùng checkpoint October 13 làm bằng chứng local-mode mới đang chạy.

### CoS, ghim revision khảo sát mới

- [README và bản đồ khả năng](https://github.com/totec448-spec/chat-on-steroids/blob/557d0bbb25f40539d8ee2629b64f4fde1b3989eb/README.md).
- [File panel](https://github.com/totec448-spec/chat-on-steroids/blob/557d0bbb25f40539d8ee2629b64f4fde1b3989eb/src/renderer/file-panel.ts), [file editor và revision checks](https://github.com/totec448-spec/chat-on-steroids/blob/557d0bbb25f40539d8ee2629b64f4fde1b3989eb/src/main/project-files.ts), [code-file](https://github.com/totec448-spec/chat-on-steroids/blob/557d0bbb25f40539d8ee2629b64f4fde1b3989eb/src/main/code-file.ts), [composer drafts](https://github.com/totec448-spec/chat-on-steroids/blob/557d0bbb25f40539d8ee2629b64f4fde1b3989eb/src/renderer/composer-drafts.ts).
- [Chat search](https://github.com/totec448-spec/chat-on-steroids/blob/557d0bbb25f40539d8ee2629b64f4fde1b3989eb/src/renderer/chat-search.ts), [settings search](https://github.com/totec448-spec/chat-on-steroids/blob/557d0bbb25f40539d8ee2629b64f4fde1b3989eb/src/renderer/settings-search.ts), [handoff](https://github.com/totec448-spec/chat-on-steroids/blob/557d0bbb25f40539d8ee2629b64f4fde1b3989eb/src/shared/handoff.ts).
- [Attachment và steer/queue](https://github.com/totec448-spec/chat-on-steroids/blob/557d0bbb25f40539d8ee2629b64f4fde1b3989eb/src/renderer/chat.ts), [Plan/Goal](https://github.com/totec448-spec/chat-on-steroids/blob/557d0bbb25f40539d8ee2629b64f4fde1b3989eb/src/main/goal.ts), [Goal/Loop protocol](https://github.com/totec448-spec/chat-on-steroids/blob/557d0bbb25f40539d8ee2629b64f4fde1b3989eb/src/shared/goal.ts), [workers](https://github.com/totec448-spec/chat-on-steroids/blob/557d0bbb25f40539d8ee2629b64f4fde1b3989eb/src/main/agents.ts).
- [Terminal](https://github.com/totec448-spec/chat-on-steroids/blob/557d0bbb25f40539d8ee2629b64f4fde1b3989eb/src/main/workspace-terminal.ts), [worktrees](https://github.com/totec448-spec/chat-on-steroids/blob/557d0bbb25f40539d8ee2629b64f4fde1b3989eb/src/main/worktrees/index.ts), [projects/SSH](https://github.com/totec448-spec/chat-on-steroids/blob/557d0bbb25f40539d8ee2629b64f4fde1b3989eb/src/main/projects.ts).
- [Notifications](https://github.com/totec448-spec/chat-on-steroids/blob/557d0bbb25f40539d8ee2629b64f4fde1b3989eb/src/main/turn-notifications.ts), [keep awake](https://github.com/totec448-spec/chat-on-steroids/blob/557d0bbb25f40539d8ee2629b64f4fde1b3989eb/src/main/keep-awake.ts), [Windows dictation](https://github.com/totec448-spec/chat-on-steroids/blob/557d0bbb25f40539d8ee2629b64f4fde1b3989eb/src/main/dictation.ts).
- [Skills library](https://github.com/totec448-spec/chat-on-steroids/blob/557d0bbb25f40539d8ee2629b64f4fde1b3989eb/src/renderer/skills-library.ts), [plugins](https://github.com/totec448-spec/chat-on-steroids/blob/557d0bbb25f40539d8ee2629b64f4fde1b3989eb/src/renderer/plugins.ts), [browser tools](https://github.com/totec448-spec/chat-on-steroids/blob/557d0bbb25f40539d8ee2629b64f4fde1b3989eb/src/main/mcp/tools-browser.ts), [Windows automation](https://github.com/totec448-spec/chat-on-steroids/blob/557d0bbb25f40539d8ee2629b64f4fde1b3989eb/src/main/computer/windows-api.ts).

### WebCodex upstream, ghim revision

- [File tools](https://github.com/yyjeqhc/webcodex/blob/2bac8248a2e635022ae9c636fc1287bc01b6b833/src/tool_runtime/file_tools.rs), [resource references](https://github.com/yyjeqhc/webcodex/blob/2bac8248a2e635022ae9c636fc1287bc01b6b833/docs/implementation/workbench-resource-references.md), [Live Work Result](https://github.com/yyjeqhc/webcodex/blob/2bac8248a2e635022ae9c636fc1287bc01b6b833/docs/MCP.md#live-work-result-card).
- [Git tools](https://github.com/yyjeqhc/webcodex/blob/2bac8248a2e635022ae9c636fc1287bc01b6b833/src/tool_runtime/git_tools.rs), [managed worktrees](https://github.com/yyjeqhc/webcodex/blob/2bac8248a2e635022ae9c636fc1287bc01b6b833/docs/agent/session-model.md#full-runtime-coding-continuity).
- [Job reliability](https://github.com/yyjeqhc/webcodex/blob/2bac8248a2e635022ae9c636fc1287bc01b6b833/docs/agent/job-reliability-and-concurrency.md), [interactive input](https://github.com/yyjeqhc/webcodex/blob/2bac8248a2e635022ae9c636fc1287bc01b6b833/docs/implementation/interactive-job-input.md), [project validation](https://github.com/yyjeqhc/webcodex/blob/2bac8248a2e635022ae9c636fc1287bc01b6b833/docs/implementation/project-validation-test-options.md).
- [Artifacts](https://github.com/yyjeqhc/webcodex/blob/2bac8248a2e635022ae9c636fc1287bc01b6b833/src/tool_runtime/files/artifacts.rs), [spreadsheet reader](https://github.com/yyjeqhc/webcodex/blob/2bac8248a2e635022ae9c636fc1287bc01b6b833/src/tool_runtime/files/spreadsheet.rs), [Session continuity](https://github.com/yyjeqhc/webcodex/blob/2bac8248a2e635022ae9c636fc1287bc01b6b833/docs/SESSION_CONTINUITY.md).
- [Goal Workbench](https://github.com/yyjeqhc/webcodex/blob/2bac8248a2e635022ae9c636fc1287bc01b6b833/frontend/src/runtime-v2/components/GoalWorkbench.tsx), [durable agent conversation](https://github.com/yyjeqhc/webcodex/blob/2bac8248a2e635022ae9c636fc1287bc01b6b833/docs/architecture/durable-agent-conversation.md), [coding agents](https://github.com/yyjeqhc/webcodex/blob/2bac8248a2e635022ae9c636fc1287bc01b6b833/apps/desktop/src/features/extensions/CodingAgentsPanel.tsx).
- [Projects panel](https://github.com/yyjeqhc/webcodex/blob/2bac8248a2e635022ae9c636fc1287bc01b6b833/apps/desktop/src/features/projects/ProjectsPanel.tsx), [Runner/LSP/SSH/Skills](https://github.com/yyjeqhc/webcodex/blob/2bac8248a2e635022ae9c636fc1287bc01b6b833/docs/RUNNER.md), [plugins](https://github.com/yyjeqhc/webcodex/blob/2bac8248a2e635022ae9c636fc1287bc01b6b833/docs/PLUGINS.md), [browser runtime](https://github.com/yyjeqhc/webcodex/blob/2bac8248a2e635022ae9c636fc1287bc01b6b833/docs/architecture/browser-cdp-runtime.md).

## 10. Trạng thái bàn giao

Đợt này bổ sung tài liệu feature catalog, không sửa ứng dụng hoặc ghi `.coding-tools`. Bản phân tích UI và mẫu trước được giữ làm snapshot riêng; mẫu đó chưa thể hiện toàn bộ danh mục ở đây. Không chạy test sản phẩm, tạo Job sản phẩm, commit/push, đóng gói, release, deploy hoặc điều khiển dịch vụ. Worktree có thay đổi trước và đồng thời từ công việc khác; không nhận các thay đổi đó là kết quả của khảo sát này.

Kiểm tra bàn giao: đối chiếu bảng với source local/upstream; rà soát ID, whitespace, conflict marker, diff và Git state. Mức bằng chứng là khảo sát nguồn và thiết kế; khả năng sử dụng thực tế, tích hợp host, packaging/live và tác động đến hiệu suất chưa được đo. Bước tiếp theo cụ thể là đặc tả rồi triển khai chu trình Đợt A vào renderer/IPC hiện tại, giữ một runtime authority và public smart-v3 tám tool.

## 11. Trạng thái triển khai (cập nhật thường xuyên)

### 2026-10-22 — Đợt A, increment 1 (Muse triển khai trực tiếp trên VM)

Nền nguồn trước khi triển khai: đã hợp nhất toàn bộ thay đổi chưa commit ngày 22/10 trên Windows (`direct local mode`, 28 tệp) về VM làm nền chung; backup tại `~/workspace/codex-merge-20261022/` phía VM. Lưu ý thay đổi hành vi ở bản nền này: cơ chế `confirm_destructive=true` đã bị gỡ, lệnh phá hủy bị chặn cứng `PERMISSION_REQUIRED` (có test khóa riêng).

Đã triển khai vào renderer (trang mới **Làm việc** — `data-page-view="workhub"`):

| ID | Trạng thái | Ghi chú triển khai |
|---|---|---|
| F01 | Đã xong (increment 1) | `renderer/work-hub-store.js` + UI: thư viện lời nhắc lưu local (`localStorage` key `coding-tools-work-hub-v1`, theo tiền lệ `coding-tools-*-v1`), 3 mẫu sẵn, CRUD, điền biến `{{project}} {{request}} {{files}}`, xem trước không tự gửi. |
| F03 | Đã xong (increment 1) | Ghim/đặt tên dự án trên danh sách MRU hiện có; ghim lên đầu, nhãn dự án đang dùng; không tạo registry thứ hai. |
| F04 | Đã xong (increment 1) | 5 thẻ loại công việc; form theo loại, kiểm tra trường bắt buộc, sinh yêu cầu kèm tiêu chí hoàn thành và gói ngữ cảnh. |
| F05 | Đã xong (increment 1) | Giỏ ngữ cảnh tách theo dự án, chống trùng, thêm tay hoặc nhập tệp từ task state hiện tại, tạo gói ngữ cảnh văn bản. Viewer chọn tệp trực quan thuộc F06. |
| F06 | Một phần | Đã có đường vào tệp từ tác vụ + giỏ. Còn thiếu cây thư mục / tìm trong mã / xem nhanh nội dung — cần IPC đọc tệp phía Electron (increment sau). |
| F09 | Một phần | Work Hub hiện tóm tắt tệp đã sửa và mở trang Tác vụ (nơi có danh sách/diff hiện hữu). Diff nội tuyến theo tác vụ trong Work Hub: increment sau. |
| F12 | Một phần | Tóm tắt kết quả kiểm thử/tác vụ trong Work Hub, mở trang Tác vụ/Build để xem sản phẩm đầy đủ. Khay preview theo loại tệp: increment sau. |
| F20 | Đã xong (increment 1) | Recipe có tên (lệnh + thư mục), xem lại trước khi chạy, sao chép nhanh. Chạy thực tế vẫn qua trang Build/terminal để giữ đúng Job/authority hiện tại — UI ghi rõ ranh giới này. |
| F22 | Đã xong (increment 1) | Notification native từ renderer cho trạng thái xong/lỗi/chờ duyệt/tạm dừng; cổng chống trùng bền (mỗi sự kiện báo một lần); công tắc bật/tắt + nút gửi thử. |
| F29 | Đã xong (increment 1) | Xem trước bản tiếp tục từ task state: mục tiêu, đã làm, chưa kiểm chứng (bước chưa xong, test lỗi, chưa có test), bước tiếp theo, tệp; mở preview không tạo Job. |
| F31 | Đã xong (increment 1) | Ctrl+K: tìm trang, dự án, lời nhắc, lệnh đã lưu; khớp tiếng Việt không dấu, xếp hạng tiêu đề trước chi tiết. |

Kiểm chứng increment 1: `tests/work-hub-store.test.js` 9/9 đạt; `tests/settings.test.js` 15/15 đạt; `node --check` cho `app.js`, `work-hub.js`, `work-hub-store.js` đạt; cấu trúc HTML hợp lệ. Chưa kiểm chứng: chạy GUI Electron thật trên Windows (làm sau khi đồng bộ + build ở mốc đồng bộ Đợt A).

Tệp thay đổi: `renderer/work-hub-store.js` (mới), `renderer/work-hub.js` (mới), `renderer/index.html`, `renderer/app.js`, `renderer/styles.css`, `tests/work-hub-store.test.js` (mới), tài liệu này.
