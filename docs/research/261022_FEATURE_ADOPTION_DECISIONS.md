# Quyết định tiếp nhận tính năng từ Chat On Steroids và WebCodex

Ngày đối chiếu: **22/10/2026**; chốt snapshot local bổ sung lúc **15:32:13 (+07)** tại **`278d972701bd8a42734a84c3cb666cdd905d7dcb`**. Đây là phân tích nguồn và thiết kế đề xuất, không phải kết quả chạy ứng dụng hay xác nhận bản phát hành. Các thay đổi sau snapshot cần được đối chiếu riêng.

## 1. Kết luận

Nên tiếp nhận và hoàn thiện **8 nhóm chức năng**, triển khai thành một chu trình sử dụng: chọn đúng dự án/tệp → chuẩn bị yêu cầu → theo dõi công việc → xem thay đổi → kiểm chứng → lấy kết quả → tiếp tục khi cần.

Ưu tiên cao nhất là **ngữ cảnh chứa đúng nội dung, diff gắn đúng công việc, Job/lệnh chạy và theo dõi được, sản phẩm có thể lấy ra sử dụng**. Work Hub vừa có nhiều UI nền cho các nhóm này; phần còn thiếu chủ yếu là nối thành luồng hoàn chỉnh và kiểm chứng tích hợp. Thông báo, bản nháp/tìm kiếm và handoff hoàn thiện chu trình đó. Bảng task/worker đáng làm sau khi có truy vấn chi tiết và điều khiển đúng từng task.

Danh mục 40 mục trước là tập ứng viên, gồm cả ý tưởng riêng. Không nên hiểu đó là 40 chức năng đều có nguyên mẫu hoàn chỉnh trong hai kho, đều chưa có ở local, hoặc đều nên triển khai. Tài liệu này đưa ra quyết định chọn lọc và các điều kiện kỹ thuật phát hiện khi đọc sâu hơn; giữ nguyên các tài liệu nghiên cứu trước làm lịch sử.

### Phiên bản nguồn

| Nguồn | Phiên bản quan sát | Cách dùng trong phân tích |
|---|---|---|
| Local | `main`, snapshot cuối `278d972701bd8a42734a84c3cb666cdd905d7dcb` | Khảo sát bắt đầu ở `5c5e2072…`; công việc khác commit increment 1 tại `69f6ab81…`, rồi increment 2 tại `278d9727…`. Đã đọc bổ sung cả hai delta. Không nhận các commit đó là sản phẩm của đợt phân tích này. |
| Chat On Steroids (CoS) | `3f6b2b8bb86a6e591848bc9add36332433093921` | HEAD được xác nhận lại; so với `557d0bbb…` chỉ đổi một test worktree, các nguồn tính năng đã khảo sát không đổi. |
| WebCodex upstream (W) | `2bac8248a2e635022ae9c636fc1287bc01b6b833` | HEAD được xác nhận lại; tái dùng nguồn ghim revision và đọc sâu thêm hợp đồng Job/input/resources. |

Mức bằng chứng: source có implementation; tests được đọc như đặc tả khi cần, không chạy lại sản phẩm. Catalog do công việc triển khai cập nhật ghi nhận 29/29 test liên quan; đây là kết quả được báo cáo ở đợt đó, không phải kết quả chạy của khảo sát này và không thay bằng chứng GUI Electron. Không đo thời gian thao tác, tỷ lệ lỗi hay hiệu suất; mức giá trị/công sức dưới đây là nhận định thiết kế. `.coding-tools` không được dùng để suy diễn kết quả UX hoặc chi phí.

### Work Hub hiện đã có gì — tránh đề xuất xây lại

| Phần đã có trong source `278d9727` | Mức hoàn chỉnh quan sát được | Quyết định tiếp theo |
|---|---|---|
| Thư viện prompt, biến, 5 loại công việc | CRUD và tạo preview/copy; chưa tự giao việc cho model | Giữ; thêm nháp theo dự án và đường chuyển yêu cầu rõ ràng |
| Ghim/đặt tên dự án | Metadata trên MRU; kết quả tìm dự án chỉ mở trang workspace | Giữ; cho chọn đúng dự án trực tiếp, khôi phục nháp và ngữ cảnh |
| Giỏ ngữ cảnh theo dự án | Thêm tay hoặc từ cây tệp; nội dung xuất ra là path/size | Hoàn thiện chọn dòng, kiểm tra phiên bản và chuẩn bị nội dung/ref mà client đọc được |
| Cây tệp, đọc text, tìm nội dung | Có service và 5 IPC mới; tìm thấy dòng nhưng mở viewer chưa nhảy đúng dòng | Hoàn thiện phạm vi, chống phản hồi cũ, giới hạn đọc thật và tìm kiếm không khóa main process |
| Git status/diff nội tuyến | Có staged/unstaged cho working tree hiện tại | Bổ sung task/base/version, history và xử lý đúng rename/tên đặc biệt/untracked |
| Khay sản phẩm | Đọc `task.last_build_report`, preview text và copy path | Mở/tải kết quả, ảnh và export báo cáo; kiểm tra đúng run/hash và trạng thái thiếu dữ liệu |
| Recipe có tên | Lưu `name/command/cwd` toàn cục, chỉ Copy/Delete | Thêm phạm vi dự án và Run → Job → output/control; giữ store hiện hữu |
| Ctrl+K | Tìm trang, prompt, recipe và dự án; hỗ trợ tiếng Việt không dấu | Thêm task/report/file và điều hướng đúng đối tượng |
| Notification | Có API `Notification`, toggle, test và dedup local | Nối sự kiện nền, đúng run/event, click mở công việc; thêm keep-awake khi cần |
| Handoff preview | Dựng từ task projection; chưa đọc capsule canonical | Sửa ánh xạ schema, phân biệt thiếu detail, nối capsule và bước tiếp tục |

Nguồn: [Work Hub UI](E:/DEV/Codex-web/renderer/work-hub.js:58), [store](E:/DEV/Codex-web/renderer/work-hub-store.js:215), [file/Git service](E:/DEV/Codex-web/electron/services/workHubFiles.js:22), [IPC](E:/DEV/Codex-web/electron/preload.js:124). Đây là bằng chứng source, chưa xác nhận tính năng đã chạy trên bản cài người dùng.

## 2. Mỗi dự án nên cung cấp điều gì cho local

| Dự án | Phần nên học | Giới hạn tiếp nhận |
|---|---|---|
| CoS | Thao tác gần người dùng: file panel, chọn ngữ cảnh, draft, diff/editor, terminal, xuất nội dung, thông báo, worker panel, Skills | Nhiều chức năng nối với browser/ChatGPT conversation. Lấy trải nghiệm và hành vi phù hợp; không tự đưa recorder, DOM transport hoặc worker chat pool vào Hub. |
| W | Job observation/input, resource references, artifact retrieval, Git/worktree, scoped workbench, semantic tools, target/provider contracts | Không chuyển toàn bộ Server/Runner/Desktop hoặc public API vào local. Workbench đọc tài nguyên không đồng nghĩa editor; source không chứng minh mọi bộ cài đã được nghiệm thu. |
| Local hiện tại | Một runtime authority, durable task/Job identity, file/patch/Git, scope/permission, proof, continuity và recovery | Giữ các cơ chế này. Phần thiếu thường là thao tác UI và IPC có scope; một số chỗ còn cần hoàn thiện contract thực thi, không chỉ renderer. |

Nền sản phẩm hiện hành: [CURRENT_STATE.md](E:/DEV/Codex-web/docs/CURRENT_STATE.md:3), [ARCHITECTURE.md](E:/DEV/Codex-web/docs/ARCHITECTURE.md:5), [ROADMAP.md](E:/DEV/Codex-web/docs/ROADMAP.md:16). Source hiện mặc định `local / host_user`; không lấy checkpoint live cũ làm bằng chứng mode mới đã được kích hoạt.

## 3. Những phát hiện làm thay đổi thứ tự ưu tiên

1. **Electron đã có đường đọc file/diff mới, nhưng chưa nối toàn bộ luồng runtime.** [preload.js](E:/DEV/Codex-web/electron/preload.js:124) đã expose list/read/search/status/diff. [main.js](E:/DEV/Codex-web/electron/main.js:865) chọn root từ settings và gọi service local trực tiếp, không qua file/context workflow MCP. Đây là adapter đọc local; chưa thể suy ra nó có target remote, task scope, content revision hay authority tương đương runtime. Giữ IPC theo thao tác; hoàn thiện binding và dùng workflow hiện hữu ở bước chuẩn bị ngữ cảnh/ghi/thực thi.
2. **Build/Test đã có UI nhưng đang dùng một đường thực thi riêng.** [main.js](E:/DEV/Codex-web/electron/main.js:1201) gọi `BuildVerificationService.execute`; [service](E:/DEV/Codex-web/electron/services/buildVerificationService.js:75) giữ `running`/`lastReport` trong bộ nhớ và gọi `cmd.exe` ở dòng 89. Recipe mới chỉ copy command, thậm chí chưa lọc theo dự án. Có thể giữ store và trải nghiệm nhập lệnh/nhận diện dự án, nhưng cần gắn execution với Job/runtime hiện hành nếu muốn theo dõi lại và điều khiển nhất quán.
3. **Job identity bền không đồng nghĩa mọi output đều bền.** [command_output_artifact_ref](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/artifact_refs.py:58) ghi `process_runtime`, `restart_safe=False`. Mở lại panel, restart MCP và restart máy là ba tình huống khác nhau. UI phải phản ánh retention thực tế; muốn đọc log sau runtime restart cần bổ sung lưu trữ có phạm vi rõ.
4. **Input chưa có bằng chứng chống gửi lặp tương đương upstream.** [write_stdin](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/session_control.py:466) gửi `chars` vào process; [schema](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/tool_schema.py:845) chưa có `input_id`. W có [input identity/receipt][w-input]. Nếu thêm console nhập liệu qua kết nối có thể mất phản hồi, cần reconcile thay vì tự gửi lại. Cursor output hiện có không giải quyết trùng input.
5. **Task board cần query đúng task, không chỉ nhiều card.** [canonicalTaskStateFromControl](E:/DEV/Codex-web/electron/main.js:515) đọc `task_list.current`, chỉ ghép projection khi task/run khớp. [history](E:/DEV/Codex-web/electron/main.js:1181) đã dùng ledger canonical. Cần detail query theo exact task/run trước khi điều khiển nhiều việc; không đổi active workspace ngầm để thao tác card khác. `details_available=false` cần hiển thị là chưa lấy được chi tiết, không biến thành khẳng định chưa có test/artifact.
6. **Local chủ động không có ChatGPT recorder/composer tích hợp.** [chat-page-retirement.test.js](E:/DEV/Codex-web/tests/chat-page-retirement.test.js:10) bảo vệ ranh giới này. `@file`, prompt, voice, steering hoặc chat search phải chỉ rõ dữ liệu thuộc local và cách chuyển sang client được hỗ trợ. Không quảng cáo thao tác tự gửi vào ChatGPT khi chỉ mới có bản nháp local.
7. **Handoff/tóm tắt đang đọc lệch schema thật.** [helper](E:/DEV/Codex-web/renderer/work-hub-store.js:299) đọc `steps[].title/name/step`, `tests`, `files/changed_files`; [projection](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/task_snapshot_projection.py:16) trả `steps[].text`, `test_results`, `modified_files`. Vì vậy tên bước, test và tệp có thể biến mất ở preview/import. Artifact tray đọc `last_build_report` đúng schema; không gộp hai nhận định này thành lỗi chung của toàn bộ task state.
8. **Trải nghiệm “đúng dự án/đúng tệp” cần kiểm chứng thêm ở adapter mới.** [resolveInsideRoot](E:/DEV/Codex-web/electron/services/workHubFiles.js:22) chỉ kiểm tra đường dẫn lexical; `statSync/readFileSync` theo symlink/junction nên chưa bảo đảm containment vật lý. File được đọc toàn bộ trước khi cắt 256 KiB; tìm nội dung chạy đồng bộ trên main process. [viewer](E:/DEV/Codex-web/renderer/work-hub.js:268) và [diff](E:/DEV/Codex-web/renderer/work-hub.js:317) chưa kiểm tra request/workspace generation. Đây là các điểm source cụ thể cần sửa và kiểm chứng trước khi gọi luồng tệp hoàn chỉnh; chưa có đo đạc cho mức độ chậm hoặc tái hiện live trong khảo sát.
9. **Các nút mới chưa tương đương một vòng sử dụng hoàn chỉnh.** Thông báo chỉ được xét trong `loadTask`, không có subscription nền/click route; tìm dự án chỉ mở trang workspace; tìm trong mã chưa nhảy đúng dòng; Git status dùng porcelain tách dòng nên cần xử lý tên quoted/Unicode và rename. Ưu tiên đóng các điểm đứt này trước khi tăng số thẻ trên Work Hub.

## 4. Tám nhóm nên bổ sung

### A1. Tệp và giỏ ngữ cảnh có nội dung sử dụng được — hoàn thiện sớm

**Lấy từ:** file panel/preview và file completion của [CoS][c-files]; cách discovery/read tài nguyên có phạm vi của [W][w-resources].

**Tình huống sử dụng:** chọn file lỗi và test liên quan → xem đoạn cần xử lý → thêm vào yêu cầu. Người dùng thấy chính xác AI được cung cấp ngữ cảnh nào.

**Local đã có:** [read/list/search](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/file_tools.py:59), [context preparation](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/context_tools.py:200), workflow nhận `paths`, `queries` và giới hạn tệp/byte. Work Hub increment 2 đã thêm cây tệp, viewer, tìm nội dung, IPC và thêm tệp vào giỏ theo dự án. [contextPackageText](E:/DEV/Codex-web/renderer/work-hub-store.js:238) hiện chỉ xuất danh sách đường dẫn/kích thước; chưa là nội dung đính kèm hoặc resource ref đã được client nhận.

**Phần nên bổ sung:** mở kết quả đúng dòng; chọn đoạn hoặc cả tệp; tổng kích thước thực; preview chính xác phần nội dung/ref sẽ chuyển sang client. Đọc lại/version-check lúc chuẩn bị nội dung, cho biết phần bị cắt. Giữ giỏ và viewer hiện hữu, không cần semantic index mới hoặc IDE đầy đủ. Import ảnh/tài liệu làm sau khi chọn nguồn/đích và xử lý trùng tên rõ ràng.

**Điểm tích hợp:** giữ adapter đọc local phù hợp, bổ sung workspace ID/generation và phiên bản nội dung; bước tạo gói ngữ cảnh dùng file/context workflow hiện có. Sửa containment qua link và đọc có giới hạn thật; tìm kiếm không chặn main process, hiển thị khi hết budget quét. Gói chuẩn bị yêu cầu khác capsule handoff: không nhét raw source vào capsule.

**Nghiệm thu:** đổi dự án khi request đang về không hiện tệp dự án cũ; file đổi phải được nhận biết; đọc thiếu do hạn mức có nhãn rõ; preview không gửi yêu cầu hoặc chạy task. **Công sức:** vừa, gồm UI và IPC.

**Liên hệ catalog:** F05–F07; F06 nên trước F08.

### A2. Diff và Git review gắn đúng công việc — hoàn thiện sớm

**Lấy từ:** [CoS file/diff panel][c-file-panel], [W Git inspection][w-git].

**Tình huống:** bấm một file được báo là đã sửa → thấy trước/sau, base và phạm vi; mở lịch sử khi cần biết lý do thay đổi.

**Local đã có:** [git_diff](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/git_tools.py:689), log/show/blame và committed review. Trang Task còn danh sách file dạng text; Work Hub đã có [Git status và diff nội tuyến](E:/DEV/Codex-web/renderer/work-hub.js:299), chia staged/unstaged. Service mới đọc toàn working tree, chưa nối task/base; chưa có history/blame UI hoặc diff cho file untracked.

**Phần nên bổ sung:** tệp được task ghi nhận → diff có base/current rõ → dòng liên quan → thêm vào context; thêm History/committed range khi cần. Sửa parser status để giữ đúng rename/tên có dấu/quoted path; trình bày file mới. Phân biệt thay đổi ngoài task. Không thể lấy toàn bộ `git diff` rồi ghi nhãn “AI đã làm”.

**Sau đó:** sửa nhanh text và xem trước patch, dùng [preimage/guarded patch](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/file_tools.py:588) hiện có. Duyệt từng hunk chỉ làm khi contract hỗ trợ chính xác; copy editor CoS không đồng nghĩa copy đường ghi file của nó.

**Nghiệm thu:** HEAD hoặc file đổi giữa hai lần đọc không trộn snapshot; concurrent edit chặn lưu đè; preview không sửa index/worktree. **Công sức:** vừa để hoàn thiện viewer và binding; lớn hơn cho editor/approval.

**Liên hệ catalog:** F09, F25 trước; F08, F10 sau; F26–F28 là nhóm riêng có điều kiện.

### A3. Job console và lệnh đã lưu — ưu tiên nền tảng trước tự động hóa

**Lấy từ:** thao tác terminal/output của [CoS][c-terminal], [W observation][w-observe] và [input receipts][w-input]. Thư viện recipe có tên là thiết kế đề xuất cho local; không gán cho CoS một tính năng tương đương chưa được xác nhận.

**Tình huống:** chọn “Test đăng nhập” → thấy lệnh/máy/thư mục → chạy → xem output → rời màn hình → trở lại đúng lần chạy; có thể dừng hoặc gửi input nếu backend hỗ trợ.

**Local đã có:** `exec_command`, `command_control` poll/read/write/kill, output paging và cursor độc lập. Build page đã nhận diện Node/Python/Rust/Go, có ô nhập lệnh và báo cáo. Work Hub đã lưu recipe có tên, command và cwd, nhưng [listRecipes](E:/DEV/Codex-web/renderer/work-hub-store.js:246) trả danh sách toàn cục; nút [Copy](E:/DEV/Codex-web/renderer/work-hub.js:183) chỉ sao chép command. Thiếu Run → Job, console theo từng lần chạy và lọc theo dự án; Build helper chưa nằm trên cùng lifecycle Job.

**Phần nên bổ sung:** chọn recipe của dự án → thấy command/cwd/máy → chạy một lần → lưu handle → hiển thị output/exit/timeout/cancel/unknown. Giữ CRUD recipe hiện tại và thêm hành động chạy đúng contract. Mở lại chỉ quan sát. Bắt đầu với pipe output và thao tác thực sự được backend hỗ trợ; PTY đa tab là lựa chọn sau.

**Điểm tích hợp:** tái sử dụng runtime admission và execution bridge hiện hành; giữ logic nhận diện dự án của Build page khi thích hợp. Structured argv là dữ liệu nội bộ qua bridge đã xác minh: [schema](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/tool_schema.py:977) dành `argv` cho attested bridge, caller thông thường không được gửi tùy ý. Không mở rộng helper `cmd.exe` thành executor thứ hai.

**Phần cần quyết định riêng:** lưu output cần xem sau restart; input receipt/dedup nếu console tương tác; cách hiển thị output đã bị loại khỏi retention. Không cam kết khôi phục process/pipe đã chết.

**Nghiệm thu:** hai viewer không tiêu thụ output của nhau; reconnect không chạy lại; lost ACK không tự gửi input lần hai; yêu cầu dừng khác với đã xác nhận dừng; kết quả ghi `skipped` khi chưa chạy. **Công sức:** vừa–lớn.

**Liên hệ catalog:** F19–F20; đây là điều kiện trước F14/F15/F24 có dispatch.

### A4. Khay sản phẩm và xuất báo cáo — làm cùng diff/Job

**Lấy từ:** export/lưu kết quả của [CoS][c-export], resource/artifact retrieval của [W][w-artifacts]. Local dùng dữ liệu task/proof; không copy exporter transcript khi không có transcript tương đương.

**Tình huống:** công việc xong, người dùng lấy được report/file build/ảnh, biết test nào đã chạy và việc gì còn thiếu.

**Local đã có:** [artifact refs](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/artifact_refs.py:13), document inspect/create; build report có đường dẫn, dung lượng, SHA. Work Hub đã có [tray từ `task.last_build_report`](E:/DEV/Codex-web/renderer/work-hub.js:326), preview text theo extension và copy path. Schema này khớp task projection; đây là report của task, khác `lastReport` của Manual Build helper. Projection hiện trả tối đa 8 artifact, chưa là danh mục đầu ra đầy đủ.

**Phần nên bổ sung:** mở tệp/thư mục, preview ảnh, xuất Markdown/TXT/DOCX từ task/proof, đọc thêm artifact khi danh sách bị giới hạn. Khi chạy remote cần retrieval/tải về có trạng thái; path remote không được đưa cho filesystem local. Các loại khác có thể mở bằng ứng dụng ngoài sau xác minh đường dẫn. Preview Office nâng cao không phải điều kiện của bản đầu.

**Điểm tích hợp:** dùng artifact owner/retrieval/hash hiện có, thêm IPC mở có phạm vi và document workflow export. Preview hiện tại đọc path mà chưa đối chiếu lại hash; cần phân biệt tệp còn trên đĩa, tệp đã đổi, ref hết hạn và output chỉ còn trong runtime. Không gộp mọi trạng thái khác `passed` thành thất bại; thiếu exact task detail phải hiện “chưa lấy được dữ liệu”. Hash một tệp trong `dist` không tự chứng minh lần chạy hiện tại đã tạo tệp đó: cần liên kết run, thời điểm và artifact receipt khi kết luận nguồn gốc.

**Nghiệm thu:** không mở nhầm file do path từ UI; artifact mất/đổi được báo; report giữ phần skipped/unknown; exit 0 không tự sinh số test đã chạy. **Công sức:** thấp–vừa cho bản đầu.

**Liên hệ catalog:** F12, F30; F11 lưu code qua nội dung người dùng chọn là mở rộng nhỏ sau đó.

### A5. Bản nháp, tìm kiếm và tổ chức dự án — giảm thao tác lặp

**Lấy từ:** [CoS composer drafts][c-drafts] và [chat search][c-search], nhưng áp dụng trước cho dữ liệu local sở hữu. Prompt templates/ghi chú dự án là đề xuất thích nghi, không nhận là tính năng gốc tương đương đã được kiểm chứng.

**Local đã có:** MRU/chuyển workspace, [history canonical](E:/DEV/Codex-web/electron/main.js:1181), prompt library, 5 task form, pins/aliases và Ctrl+K. Search hiện chỉ có trang/prompt/recipe/dự án; chọn dự án chỉ mở trang workspace. Form đang soạn chưa được lưu thành draft theo dự án; history UI chủ yếu objective/status/ID/time.

**Phần nên bổ sung:** giữ nháp đang soạn theo dự án; chọn dự án trực tiếp từ MRU/search; mở đúng task/report từ Ctrl+K; thêm ghi chú/quy ước do người dùng chọn đưa vào yêu cầu. Giữ prompt/pin/search hiện hữu. Tìm metadata trước; chưa cần cơ sở dữ liệu nội dung hội thoại hoặc hệ thống memory mới.

**Điểm tích hợp:** mở rộng WorkHubStore hiện có cho draft; báo rõ nếu lưu local thất bại thay vì để người dùng tưởng nháp đã được lưu. Task history vẫn đọc ledger. Chỉ rõ thao tác tạo preview/Copy; chỉ thêm gửi sang client khi có adapter được hỗ trợ. Nếu flow vẫn buộc copy sang client, đánh giá lợi ích trên người dùng thật trước khi mở rộng composer.

**Nghiệm thu:** nháp còn sau mở lại; chuyển dự án không lẫn; tìm tiếng Việt không dấu có kết quả đúng; kết quả tìm mở đúng task. **Công sức:** thấp–vừa; search chi tiết task phụ thuộc A7.

**Liên hệ catalog:** F01–F04, F31–F32. Có thể làm song song A1–A4 nhưng không ưu tiên lên trước nền tảng kết quả.

### A6. Thông báo có hành động — bổ sung sớm

**Lấy từ:** [CoS turn notifications][c-notify] và [keep-awake][c-awake].

**Local đã có:** toast/tray, task/Job state và [Notification renderer](E:/DEV/Codex-web/renderer/work-hub.js:216). Work Hub chỉ xét thông báo khi `loadTask` chạy ở refresh/thao tác người dùng; chưa có subscription nền hoặc click handler mở đúng task. Dedup lấy task ID/objective + status, và ghi nhận đã báo trước khi kiểm tra quyền thông báo. Chưa thấy keep-awake.

**Phần nên bổ sung:** nhận sự kiện nền ngay cả khi đang ở trang khác; báo khi xong, lỗi hoặc cần người dùng; click mở đúng công việc. Chỉ đánh dấu đã gửi khi xử lý được, phân biệt run/event. Không báo mỗi tool call. Có tùy chọn giữ máy thức khi Job thực sự chạy, nhả khi xong hoặc bằng chứng chạy đã hết hạn.

**Điểm tích hợp:** subscribe sự kiện canonical, dedup theo event/report ID; dùng trạng thái của Hub, không copy “chat turn completed” của CoS. Không đoán model đã xong từ việc process idle.

**Nghiệm thu:** reconnect không báo lặp, click dẫn đúng scope/task, trạng thái stale không giữ máy thức vô hạn. **Công sức:** thấp–vừa. **Liên hệ catalog:** F22.

### A7. Bảng task/worker và điều chỉnh đang chạy — làm sau đường quan sát

**Lấy từ:** [CoS workers][c-workers] và [W WindowWorkbench][w-board].

**Tình huống:** biết việc nào đang chạy/chờ duyệt/xong, reviewer làm ở đâu, báo cáo nào cần xem; gửi “chỉ sửa module A” và biết controller đã nhận hay chưa.

**Local đã có:** task contexts, canonical ledger, [lane control](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/coordination.py:235), message/replan; [renderDelegations](E:/DEV/Codex-web/renderer/panel.js:525) mới hiện route/model/effort/status. Thiếu exact detail/select và thao tác theo task/worker trên UI.

**Bản tối thiểu:** danh sách theo dự án và trạng thái; chi tiết task/run; link Job/diff/report; worker role/scope/status/result; điều chỉnh có ba mức đã lưu/đã chuyển/đã xác nhận. Chỉ bật action runtime cho phép. Bảng quan sát trước, launcher sau.

**Điểm tích hợp:** thêm scoped query/IPC trên ledger/lane hiện hữu; selection UI không thay execution authority. Task A/B cùng tiêu đề vẫn có ID khác. Reviewer chỉ đọc; `auto` vẫn chịu evidence gate.

**Nghiệm thu:** phản hồi chậm của task A không ghi vào card B; Stop A không chạm B; mở worker không tạo lane mới; message lưu không hiển thị “agent đã đọc” nếu chưa có ack. **Công sức:** vừa–lớn.

**Liên hệ catalog:** F16–F18, F21. F15 queue là extension riêng, không suy từ nhãn queued hiện tại.

### A8. Xem trước và tiếp tục công việc — hoàn thiện chức năng đã có

**Lấy từ:** ý tưởng Compact/Resume của CoS và [continuity của W][w-continuity].

**Local đã có:** [recordHandoff](E:/DEV/Codex-web/renderer/panel.js:622), transfer controller, continuity core và ledger; Work Hub có preview từ task state. Preview mới chưa đọc capsule canonical, đồng thời có lệch schema bước/test/tệp ở mục 3. Không cần engine memory/goal thứ hai.

**Phần nên bổ sung:** sửa preview theo schema thật và trạng thái detail; đọc capsule đã lưu trước chuyển phiên: mục tiêu, đã làm, bằng chứng, chưa kiểm chứng, blocker, Job đang tồn tại và bước tiếp theo. Tìm capsule theo task/run, copy hoặc dùng adapter client hỗ trợ. Phân biệt “tóm tắt trạng thái hiện tại” với “bản bàn giao đã được ghi nhận”.

**Điểm tích hợp:** tiếp tục `task_control` hiện hành, revalidate workspace/revision/Job. [Schema capsule](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/tool_schema.py:632) cấm raw transcript/source/output; dùng tóm tắt bounded và ID/ref/hash. Đây khác gói ngữ cảnh tệp ở A1.

**Nghiệm thu:** preview không khởi động Job; không replay lệnh đã chạy; file khác phiên bản phải được nhận biết; phần chưa kiểm chứng không biến thành done. **Công sức:** thấp–vừa cho preview, lớn hơn cho automatic host continuation.

**Liên hệ catalog:** F29; F23 Goal có giới hạn chỉ mở sau khi controller/grant/cancellation đủ rõ.

## 5. Những khả năng đáng lấy nhưng cần điều kiện cụ thể

| Khả năng từ dự án tham khảo | Quyết định và lý do | Khi nào bắt đầu |
|---|---|---|
| **Skills library** — [CoS][c-skills], W Runner | Nên có khi dùng lại quy trình. Local Codex bridge chia sẻ skills/config của client nhưng chưa có manager/consumer contract chung; review profile còn đặt `skill_search=False`. Chọn consumer trước, tham chiếu store chuẩn của client; tránh registry sao chép. | Sau khi xác định client thực sự đọc skill, project scope và version. Import/preview trước marketplace/auto-update. |
| **Semantic navigation/LSP** — [W][w-lsp] | Có giá trị với repo lớn. Local đã có localization/provider và graph; thiếu API/UI navigation đầy đủ, không làm LSP supervisor mới. | Sau file viewer, có provider hoạt động được xác minh. Phân biệt kết quả semantic, text fallback và partial coverage. |
| **Web preview + browser QA** — [CoS browser tools][c-browser], W browser runtime | Hữu ích nếu thường xây web. Preview URL của Job là bước nhỏ; inspect console/network và thử luồng cần adapter/browser lifecycle riêng. | Sau Job monitor; có app/URL/tab được chọn và readiness thật. Không nhập ChatGPT observer theo. |
| **Managed worktree** — [CoS worktrees][c-worktrees], [W managed worktree][w-worktree] | Nên thêm khi cần hai writer hoặc thử hướng lớn độc lập. Quan sát nhiều task không tự yêu cầu worktree. | Sau Git viewer, owner/scope/lifecycle rõ. Resolve base commit; đặt ngoài `.coding-tools`; không tự mang dirty work hoặc xóa khi xong. |
| **Selective commit/restore** — W Git mutations | Có ích nhưng sau read-only review. Git generic exec chưa phải API/UI commit. Commit phải giữ quy định staging/delivery của repo. | Khi đã có exact HEAD/index preview và guard; restore theo file/patch có revalidation, không reset/clean toàn repo. |
| **Queue/steering/Goal** — CoS | Steering nằm trong A7; queue và Goal cần dispatch/ack/lifecycle thật. Không suy background Job là task queue. Goal dùng engine hiện có. | Recipe queue có thể trước AI queue. Model/controller phải sẵn sàng, dispatch không lặp và có giới hạn/dừng. Không tự bật Loop vô hạn. |
| **Máy thực thi/SSH resources** — [W][w-ssh], CoS projects | Local đã có enrollment/workspace/authority. Nếu tiếp tục dùng cặp Windows/Ubuntu mô tả trong current-state, nên làm target picker ở đợt 2; SSH generic làm sau. Dùng registry hiện hữu. | Hiển thị rõ máy/thư mục/readiness. Biết rõ chỉ chạy command remote hay cả file/Git remote. Đổi target chỉ ảnh hưởng việc mới; offline/unknown không tự failover. |
| **MCP/plugin manager** — [W][w-plugins], CoS plugins | Chưa nên xây marketplace/gateway tổng quát. Adapter cụ thể hiện có không chứng minh plugin framework chung. | Bắt đầu một tích hợp đang cần; có consumer thứ hai mới cân nhắc shared gateway. Saved config khác active capability. |
| **Voice-to-draft** — CoS dictation | Tiện cho nhập yêu cầu dài, nhưng không khắc phục các khoảng trống file/Job/diff. | Sau draft và consumer flow rõ; ghi âm theo thao tác, xem/sửa trước dùng. Không coi đây là voice agent hai chiều. |
| **Windows desktop automation** — CoS Windows API | Capability mới, không phải hệ quả của chạy lệnh Windows. Có thể hữu ích cho workflow GUI/AutoCAD cụ thể. | Chỉ khi có use case GUI, adapter UIA/capture/input, đúng cửa sổ và cancellation. Không gộp vào bản đầu của coding workbench. |
| **Chat organization/search/export/fork** — CoS | Không phù hợp để nhập nguyên khối hiện nay vì local chủ động bỏ recorder/embedded chat. Có thể lưu URL/nhãn do người dùng chọn. | Nội dung/fork thực sự cần host integration được hỗ trợ và message identity; không thay bằng đọc DOM. |
| **Lịch kiểm tra định kỳ** | Là đề xuất riêng của catalog, chưa xác nhận scheduler tương đương trong các nguồn đã khảo sát. Giá trị thấp hơn recipe chạy tay + notification ở hiện trạng. | Chỉ sau Job/recipe, có nhu cầu lặp cụ thể và missed-run/host-availability policy. |

Nguồn local bổ sung: [Codex bridge skills/config](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/codex_bridge.py:423), [review profile](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/codex_bridge.py:65), [semantic provider](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/semantic_localization.py:19), [semantic graph](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/semantic_graph.py:351).

## 6. Không nên nhập nguyên khối

- CoS ChatGPT DOM transport, recorder và browser-chat worker family: không khớp current Desktop boundary.
- W Desktop/Server/Runner/installers như một cuộc thay kiến trúc: chỉ tham khảo component contract liên quan.
- Một task/goal/history/memory database hoặc execution/process manager mới cạnh runtime hiện hành.
- Một full IDE/PTY/LSP stack trước khi file viewer, diff và Job output dùng được.
- Auto-routing model, auto-handoff, Loop hoặc scheduler chỉ vì repo khác có source. Local gates và controller capability vẫn quyết định.
- Tool registry tràn từ upstream. Giữ public smart-v3 tám tool; thao tác mới có thể cần action/schema/IPC nhưng không mặc nhiên mở public surface tùy ý.

## 7. Lộ trình đề xuất và tiêu chí kết thúc từng đợt

### Trước khi nghiệm thu phần Work Hub vừa thêm

Đây là hoàn thiện implementation đã có ở `278d9727`, không phải thêm hệ thống mới:

1. Sửa ánh xạ `steps[].text / test_results / modified_files`; kiểm tra bằng fixture lấy từ canonical projection. Giữ trạng thái thiếu detail riêng với “không có kết quả”.
2. Gắn request với project/generation; reset viewer/selection khi đổi dự án và loại phản hồi cũ. Xác nhận đường dẫn vật lý khi qua junction/symlink.
3. Đọc có hạn mức trước khi nạp toàn tệp; tìm nội dung không khóa main process; thông báo hết budget quét và mở đúng dòng.
4. Parse Git bằng định dạng giữ nguyên tên tệp, xử lý rename/untracked; giữ base/version của diff.
5. Thông báo từ nguồn sự kiện nền, có đúng run và link về task; sửa thời điểm đánh dấu đã báo.
6. Đối chiếu artifact và handoff với dữ liệu thật. Chạy một luồng GUI Electron có chuyển dự án; test store/service hiện có chưa chứng minh luồng này.

### Đợt 1 — Một chu trình công việc hoàn chỉnh

Hoàn thiện **A1 + A2 + A3 + A4**, thêm A6 khi đã có event nguồn đúng. Tái sử dụng UI file/diff/results của increment 2 và recipe store của increment 1. Chạy recipe qua runtime Job là phần mới lớn nhất; có thể làm song song với ngữ cảnh và provenance kết quả. Không phát hành recipe dưới lời hứa Job bền trước khi đường thực thi được nối và kiểm chứng.

Nghiệm thu bằng một tình huống thật: chọn hai tệp → chuẩn bị yêu cầu → agent sửa → người dùng xem diff → chạy test liên quan → mở kết quả và báo cáo. Xen thao tác chuyển dự án và đóng/mở panel để chứng minh không nhầm scope, không chạy lặp. Đây là mục tiêu kiểm thử tương lai, chưa được thực hiện trong phân tích.

### Đợt 2 — Giảm thao tác lặp và điều hành nhiều việc

Làm **A5 + A8**, rồi **A7** theo mức backend query/ack đã có. Tích hợp nguồn history/capsule/lane hiện hữu. Đưa chọn máy/dự án vào đợt này nếu vận hành cả Windows/Ubuntu. Có thể thêm recipe queue giới hạn sau khi Job monitor ổn; chưa tự bật free-text AI queue.

Nghiệm thu: tìm lại task, tiếp tục từ capsule, mở hai task độc lập, gửi điều chỉnh có ack; dữ liệu trả chậm và việc đổi lựa chọn không thay target cũ.

### Đợt 3 — Chọn một năng lực chuyên sâu theo công việc thực tế

Chọn Skills khi quy trình lặp; browser QA khi phát triển web; semantic navigation khi repo lớn; worktree khi nhiều writer; target/SSH khi có máy remote. Không cần triển khai tất cả để hoàn thành mục tiêu thuận tiện của Hub.

### Cách giữ UI dễ thao tác

Một nơi chọn **dự án/máy**, một danh sách **công việc**, vùng chi tiết có **Ngữ cảnh / Thay đổi / Kiểm chứng / Kết quả**. Recipe đặt cạnh kết quả kiểm chứng; worker và output chỉ mở khi cần. Cài đặt tích hợp nằm ngoài luồng thường dùng. Mức chi tiết kỹ thuật có thể mở thêm, nhưng nhãn trạng thái phải luôn phân biệt đang chạy, chờ người dùng, chưa xác minh và hoàn tất.

Các thao tác chính nên khép kín: tìm tệp → mở đúng dòng → thêm ngữ cảnh; bấm file đổi → xem diff; chọn lệnh → chạy → thấy output; bấm kết quả → mở hoặc xuất. Bổ sung số lượng tính năng chỉ có giá trị khi giảm bước chuyển trang/copy đường dẫn trong các luồng này. Chưa đặt chỉ tiêu giảm thời gian theo phần trăm vì chưa có baseline đo thật.

### Quyết định cho toàn bộ 40 ứng viên trước đó

Đối chiếu [catalog 40 mục](E:/DEV/Codex-web/docs/research/261022_FEATURE_EXPANSION_CATALOG.md:25). “Có” dưới đây chỉ nói về source ở snapshot đã chốt; “hoàn thiện” mô tả phần cần làm tiếp, không phải xác nhận bản phát hành.

| ID | Quyết định tại snapshot này |
|---|---|
| F01 · Lời nhắc mẫu | Giữ CRUD/biến/preview đã có; nối draft và client flow khi phù hợp. |
| F02 · Nháp theo dự án | Bổ sung ở A5; đây là tiện ích còn thiếu dù đã có template. |
| F03 · Ghim/đặt tên dự án | Giữ; hoàn thiện chuyển đúng dự án và khôi phục trạng thái. |
| F04 · Loại công việc | Giữ 5 form; sửa dữ liệu/nháp trước khi thêm nhiều loại. |
| F05 · Giỏ ngữ cảnh | Hoàn thiện thành nội dung/ref có phiên bản ở A1. |
| F06 · Tệp/tìm/xem | Đã có nền; hoàn thiện scope, tốc độ phản hồi và điều hướng dòng. |
| F07 · Tài liệu/ảnh đầu vào | Bổ sung sau A1; hỗ trợ nhập có đích rõ ràng và xử lý trùng tên. |
| F08 · Sửa nhanh text | Sau diff; dùng guarded patch hiện có, giữ concurrent edits. |
| F09 · Diff theo task | Hoàn thiện A2 từ Git diff hiện tại; thêm attribution/base. |
| F10 · Duyệt patch | Sau A2, chỉ action khớp approved-patch contract. |
| F11 · Lưu code thành tệp | Mở rộng nhỏ sau editor/context; nội dung do người dùng chọn. |
| F12 · Khay sản phẩm | Hoàn thiện A4 từ tray text/copy hiện có. |
| F13 · Symbol/reference | Sau viewer; tận dụng provider/graph, chỉ bật khi provider sẵn sàng. |
| F14 · Web preview | Sau A3; Job dev server → readiness → URL mở được. |
| F15 · Hàng đợi | Sau Job dispatch; recipe queue giới hạn trước AI queue. |
| F16 · Nhiều task | A7; scoped detail query trước control. |
| F17 · Kế hoạch/tiêu chí | A7; trình bày mốc và proof hiện có, không tạo lifecycle thứ hai. |
| F18 · Điều chỉnh khi chạy | A7; phân biệt saved/delivered/acknowledged. |
| F19 · Job console | Ưu tiên A3; thực thi và quan sát từng lần chạy. |
| F20 · Lệnh đã lưu | Đã có lưu/copy; ưu tiên project binding và Run → Job. |
| F21 · Worker/reviewer | A7; quan sát scope/kết quả trước launcher. |
| F22 · Thông báo | Hoàn thiện A6; hiện có API nhưng thiếu luồng nền/action. |
| F23 · Goal có giới hạn | Sau A7/A8; dùng controller/grant/continuation hiện hành. |
| F24 · Lịch chạy | Chỉ làm sau recipe/Job và khi có nhu cầu lặp cụ thể. |
| F25 · Git history | Hoàn thiện A2; status/diff đã có, history/blame UI còn thiếu. |
| F26 · Commit chọn tệp | Sau Git review và delivery guard; không suy từ generic exec. |
| F27 · Worktree | Khi cần nhiều writer/cách thử độc lập; sau owner/lifecycle rõ. |
| F28 · Checkpoint/hoàn tác | Sau preview/preimage; restore theo phạm vi, giữ thay đổi ngoài task. |
| F29 · Tiếp tục công việc | Sửa schema ngay; hoàn thiện A8 nối capsule thật. |
| F30 · Xuất báo cáo | A4; nên thêm sớm để kết quả dùng được ngoài Hub. |
| F31 · Tìm kiếm chung | Đã có Ctrl+K; thêm task/report/file và đích mở chính xác. |
| F32 · Ghi chú dự án | A5; ghi chú do người dùng quản lý, chọn đưa vào request. |
| F33 · Chọn máy/dự án | Đợt 2 khi dùng Windows/Ubuntu; dùng registry/authority hiện có. |
| F34 · Skills | Chọn consumer thật và store chuẩn trước khi làm manager. |
| F35 · Voice-to-draft | Sau draft; tiện ích nhập liệu, ưu tiên sau luồng kết quả. |
| F36 · MCP/plugin manager | Chưa làm framework; bắt đầu từ tích hợp cụ thể đang cần. |
| F37 · Browser QA | Nên thêm cho công việc web sau A3/F14; cần adapter browser. |
| F38 · Windows GUI automation | Chỉ khi có workflow GUI cụ thể; cần adapter độc lập. |
| F39 · Chat organization/fork | Chưa nhập recorder; URL/nhãn trước, host integration sau. |
| F40 · SSH resources | Sau target picker; xác định rõ phạm vi command/file/Git remote. |

## 8. Trạng thái bàn giao

Đợt phân tích này thêm riêng tài liệu quyết định tiếp nhận; không sửa ứng dụng, mockup trước, runtime hoặc `.coding-tools`. Giữ nguyên nghiên cứu cũ và các thay đổi đồng thời của người dùng. Hai commit Work Hub trong lúc khảo sát thuộc công việc khác; báo cáo đã cập nhật theo implementation của chúng. Đợt phân tích không chạy test/build sản phẩm, tạo Job sản phẩm, commit/push, đóng gói, release, deploy hoặc thao tác dịch vụ.

Kiểm tra: đối chiếu từng kết luận với source, rà độc lập khác biệt upstream/local và hai delta Work Hub, kiểm tra links local/ID, whitespace/conflict markers. Không có bằng chứng chạy live cho các feature đề xuất; không có Job sản phẩm nào do khảo sát này khởi chạy hoặc để lại. Git ở snapshot là `main@278d9727`, tài liệu này mới/untracked; có biến động evidence `.coding-tools` từ công việc khác và được giữ nguyên. Không có blocker ngăn hoàn thành phân tích. Bước kỹ thuật đề xuất tiếp theo là sửa các điểm tích hợp đã chỉ ra, đặc tả phần mở rộng A1–A4 và đường recipe → runtime Job, rồi nghiệm thu một luồng GUI thật.

**Kiểm tra bàn giao lúc 15:41:23 (+07):** HEAD vẫn `278d9727`. Tài liệu có đủ 40 quyết định, 8 nhóm A1–A8 và 44 liên kết local hợp lệ; không có trailing whitespace/conflict marker trong tài liệu. Tuy nhiên working tree vừa phát sinh trạng thái `UU` ở `resources/coding-tools-mcp/coding_tools_mcp/exec_tools.py` và `resources/coding-tools-mcp/coding_tools_mcp/runtime_config.py`; `git diff --check` báo conflict markers tại các tệp đó. Đây là thay đổi đồng thời sau snapshot, được giữ nguyên và không dùng làm source đã hoàn tất. Vì vậy không tuyên bố toàn repository sạch; phía đang thực hiện Git operation cần giải quyết xung đột trước build/commit tiếp. Phân tích này không bị chặn và không khởi chạy Job/dịch vụ để xử lý phần việc ngoài phạm vi đó.

## Nguồn upstream ghim revision

[c-files]: https://github.com/totec448-spec/chat-on-steroids/blob/3f6b2b8bb86a6e591848bc9add36332433093921/src/main/project-files.ts#L284
[c-file-panel]: https://github.com/totec448-spec/chat-on-steroids/blob/3f6b2b8bb86a6e591848bc9add36332433093921/src/renderer/file-panel.ts#L167
[c-terminal]: https://github.com/totec448-spec/chat-on-steroids/blob/3f6b2b8bb86a6e591848bc9add36332433093921/src/main/workspace-terminal.ts#L27
[c-export]: https://github.com/totec448-spec/chat-on-steroids/blob/3f6b2b8bb86a6e591848bc9add36332433093921/src/shared/markdown-export.ts#L24
[c-drafts]: https://github.com/totec448-spec/chat-on-steroids/blob/3f6b2b8bb86a6e591848bc9add36332433093921/src/renderer/composer-drafts.ts
[c-search]: https://github.com/totec448-spec/chat-on-steroids/blob/3f6b2b8bb86a6e591848bc9add36332433093921/src/renderer/chat-search.ts
[c-notify]: https://github.com/totec448-spec/chat-on-steroids/blob/3f6b2b8bb86a6e591848bc9add36332433093921/src/main/turn-notifications.ts#L41
[c-awake]: https://github.com/totec448-spec/chat-on-steroids/blob/3f6b2b8bb86a6e591848bc9add36332433093921/src/main/keep-awake.ts#L32
[c-workers]: https://github.com/totec448-spec/chat-on-steroids/blob/3f6b2b8bb86a6e591848bc9add36332433093921/src/main/agents.ts#L2073
[c-skills]: https://github.com/totec448-spec/chat-on-steroids/blob/3f6b2b8bb86a6e591848bc9add36332433093921/src/renderer/skills-library.ts#L7
[c-browser]: https://github.com/totec448-spec/chat-on-steroids/blob/3f6b2b8bb86a6e591848bc9add36332433093921/src/main/mcp/tools-browser.ts
[c-worktrees]: https://github.com/totec448-spec/chat-on-steroids/blob/3f6b2b8bb86a6e591848bc9add36332433093921/src/main/worktrees/index.ts
[w-input]: https://github.com/yyjeqhc/webcodex/blob/2bac8248a2e635022ae9c636fc1287bc01b6b833/docs/implementation/interactive-job-input.md
[w-observe]: https://github.com/yyjeqhc/webcodex/blob/2bac8248a2e635022ae9c636fc1287bc01b6b833/src/tool_runtime/observe_jobs.rs
[w-resources]: https://github.com/yyjeqhc/webcodex/blob/2bac8248a2e635022ae9c636fc1287bc01b6b833/docs/implementation/workbench-resource-references.md
[w-artifacts]: https://github.com/yyjeqhc/webcodex/blob/2bac8248a2e635022ae9c636fc1287bc01b6b833/src/tool_runtime/files/artifacts.rs
[w-git]: https://github.com/yyjeqhc/webcodex/blob/2bac8248a2e635022ae9c636fc1287bc01b6b833/src/tool_runtime/git_tools.rs
[w-board]: https://github.com/yyjeqhc/webcodex/blob/2bac8248a2e635022ae9c636fc1287bc01b6b833/frontend/src/runtime-v2/components/WindowWorkbench.tsx
[w-continuity]: https://github.com/yyjeqhc/webcodex/blob/2bac8248a2e635022ae9c636fc1287bc01b6b833/docs/SESSION_CONTINUITY.md
[w-lsp]: https://github.com/yyjeqhc/webcodex/blob/2bac8248a2e635022ae9c636fc1287bc01b6b833/src/tool_runtime/lsp_tools.rs
[w-worktree]: https://github.com/yyjeqhc/webcodex/blob/2bac8248a2e635022ae9c636fc1287bc01b6b833/crates/webcodex-runner/src/webcodex_runner/projects/managed_worktree.rs
[w-ssh]: https://github.com/yyjeqhc/webcodex/blob/2bac8248a2e635022ae9c636fc1287bc01b6b833/docs/RUNNER.md#ssh-session-resources-advanced
[w-plugins]: https://github.com/yyjeqhc/webcodex/blob/2bac8248a2e635022ae9c636fc1287bc01b6b833/docs/PLUGINS.md

## 9. Trạng thái triển khai (bổ sung 22/10/2026, sau snapshot 278d9727)

Đợt triển khai theo đúng lộ trình mục 7 đã hoàn thành trên VM và đồng bộ 3 máy (chi tiết kiểm chứng ở catalog mục 11): toàn bộ nhóm "Trước khi nghiệm thu phần Work Hub vừa thêm" (6 điểm), Đợt 1 (A1–A4 + A6 ở mức Hub, gồm đường recipe → runtime Job qua `exec_command`/`command_control`), Đợt 2 (A5, A8 mức preview + revalidate, A7 mức quan sát/chuẩn bị). Xung đột merge được ghi ở mục 8 đã được giải quyết trước đợt này (giữ bản refresh 22/10; merge commit `d4213349`). Các mục có điều kiện ở mục 5 giữ nguyên quyết định: chỉ làm bản đầu an toàn (Skills hướng dẫn, voice-to-draft, kiểm tra HTTP, liệt kê cửa sổ) hoặc để sau (LSP đầy đủ, commit/worktree UI, checkpoint, đọc capsule qua IPC riêng). Chưa có bằng chứng GUI Electron cho các phần mới — cần một luồng test GUI thật như mục 7 yêu cầu.
