# W2 — Port UI CoS vào Work Hub: đối chiếu, lấp khoảng trống, không fork

- Ngày: 2026-10-23 (Asia/Saigon). Phạm vi: snapshot VM `~/workspace/projects/Codex-web` — **không commit/push, không restart, không packaged**. Nối tiếp W0 (`261023_COS_WEBCODEX_W0_AUDIT.md`) và W1 (`261023_COS_W1_ADAPTER.md`).
- **Hướng đã chốt lại theo chỉ đạo của user 19:03 23/10**: mục tiêu là **kết hợp logic/tính năng của CoS vào trong Codex-web** để sản phẩm chạy native, **không** yêu cầu cài hay chạy thêm app CoS. Hệ quả cho tài liệu này:
  - Mọi tính năng port ở W2 (và các W sau) phải hoạt động **khi không có CoS** — CoS chỉ là nguồn tham chiếu mã nguồn (MIT) đặt trong thư mục nghiên cứu.
  - Adapter W1 (`cosCompanionAdapter`) chỉ là **cầu tham chiếu/tùy chọn** cho ai *đã* chạy CoS sẵn và muốn quan sát phiên của nó trong Work Hub; nó **không phải phụ thuộc của sản phẩm**, mặc định tắt, và không tính năng native nào được xây trên nó.
  - Không mở rộng sang việc làm cho app CoS chạy tốt hơn; CoS pilot trên Windows đã dừng/gỡ theo chỉ đạo trên.
- Nguyên tắc giữ nguyên: backend giữ của Codex-web (`workHubFiles.js`, `workHubCoordination.js`, EOCL ledger); không tạo authority/ledger thứ hai; UI không phải proof; render dữ liệu ngoài chỉ bằng text node, không `innerHTML`.

## 1. Bảng đối chiếu §5 → đã có / thiếu / khác

### 1.1 §5.1 File/Diff

| Hạng mục kế hoạch | Hiện trạng trước W2 | Kết luận |
|---|---|---|
| Port `unified-diff.ts` + phần cần thiết của `file-panel.ts`, backend giữ `workHubFiles.js` | Cây thư mục + xem tệp + tìm mã đã có từ Đợt A/M1 (F06) — **không cần port file-panel** (1.728 dòng, phụ thuộc `shared/project-files`/`project-git` của CoS) | Đã có tương đương native; chỉ port phần diff (dưới) |
| Trình bày diff dễ đọc | `gitFileDiff` trả **văn bản thô**, renderer đổ nguyên khối vào `<pre>` bằng `textContent`: không số dòng hai phía, không phân biệt màu thêm/bớt, không giới hạn số dòng hiển thị (chỉ cắt 200KB ký tự ở backend) | **Thiếu — đã lấp** (mục 2) |
| Diff kèm Git HEAD + source fingerprint | HEAD chỉ được tải riêng phục vụ `expectedHead` khi commit; kết quả diff **không** kèm HEAD/fingerprint. Duyệt bản vá (F10) gắn với hash FNV phía renderer của đúng nội dung diff | **Thiếu — đã lấp ở backend + UI** (mục 2) |
| Dữ liệu stale được gắn nhãn | Capsule handoff đã có nhãn HEAD khớp/đổi; riêng **diff đang hiển thị thì không** — HEAD đổi sau khi tải diff, UI im lặng | **Thiếu — đã lấp** (nhãn STALE ở meta + ở khối duyệt) |
| UI không hợp nhất thay đổi ngoài task vào kết quả task | Tab Thay đổi liệt kê **toàn bộ** thay đổi cây làm việc (đúng thiết kế review), tệp do task ghi nhận có danh sách riêng kèm nhãn "Được task ghi nhận"; diff theo từng tệp nên không trộn tệp ngoài task vào diff của tệp thuộc task. Hunk ngoài task *trong cùng một tệp* không tách được ở mức working-tree — hàng task đã ghi rõ điều này | Đã có ở mức tệp; giới hạn hunk-cùng-tệp ghi nhận, không sửa |
| Tệp/diff lớn không treo UI | Đọc tệp cắt 256KB có cờ `truncated`; diff cắt 200KB. Nhưng hiển thị diff là một text node khổng lồ | **Đã lấp phía hiển thị**: parser giới hạn 600 dòng render (đếm +/− vẫn đủ), ghi chú rõ khi bị giới hạn |

### 1.2 §5.2 Worker Board / Activity

| Hạng mục | Hiện trạng trước W2 | Kết luận |
|---|---|---|
| Hiển thị từ `agent-panel.ts`/`agent-activity.ts`/`agent-plan.ts` của CoS | Đã có tương đương native từ M2: danh sách RUN, chi tiết wave/worker/lane/lease/proof/message/activity đọc từ ledger EOCL (`workHubCoordination.js`) + bảng điều phối ở tab Kết quả (`renderWorkers`) | Đã có; không port UI CoS (khác nguồn dữ liệu và vòng đời) |
| Phân biệt nguồn worker (CoS / Codex App Server / EOCL) | Chi tiết RUN in dòng `Worker …`/`Lane …` **không nhãn nguồn**; `renderWorkers` còn gọi delegation là "Lane" gây nhầm. Panel companion (W1) đã ghi chú worker trong Hub là EOCL, nhưng ngay trên board thì chưa | **Thiếu — đã lấp**: mọi dòng mang tiền tố nguồn (`Worker EOCL`, `Lane (agent lane)`, `EOCL · Client/Delegation`) + dòng nguồn đầu khối chi tiết. Worker CoS không xuất hiện trên board (W0 S1: không đọc được ở read-only; và theo hướng mới, CoS không phải thành phần của sản phẩm) |
| Hiện workspace + đang chờ gì + mức proof | Workspace chỉ ngầm hiểu theo dự án đang chọn; worker có status nhưng không nói "đang chờ"; lease/proof/message ack đã có trong chi tiết RUN | **Lấp một phần**: dòng nguồn ghi rõ workspace của ledger; worker chưa kết thúc được ghi "chưa kết thúc (đang chạy hoặc đang chờ)"; lease (owner + hết hạn) và proof (stage/exit/thời gian) đã có sẵn. "Đang chờ *ai/cái gì*" theo từng delegation chưa có dữ liệu trong ledger — ghi nhận là khoảng trống dữ liệu, không bịa nhãn |
| Không tạo nút Resume/Stop rỗng | Rà soát toàn bộ `work-hub.js`: **không có** nút Resume/Stop cho worker/RUN. Nút dừng duy nhất là dừng Job (`whJobKill`) — có backend thật qua `command_control`, tự khóa khi Job đã kết thúc; nút Dispatch steering ghi capsule thật có sha256 | Đạt — không có nút rỗng để gỡ |

### 1.3 §5.3 Chat Workspace — ranh giới với W3

| Thành phần | Đã có trong Work Hub | Thuộc W3 (không làm ở W2) |
|---|---|---|
| Shell / bố cục | Trang Làm việc với 5 tab Yêu cầu / Tiến trình / Thay đổi / Kiểm chứng / Kết quả (giữ nguyên, không đổi ở W2) | — |
| Composer | Soạn yêu cầu native: thẻ loại việc, thư viện lời nhắc, giỏ ngữ cảnh @file, xem trước + tự lưu nháp theo dự án. Composer này *chuẩn bị* yêu cầu cho đường thực thi Codex-web, không gửi vào phiên ChatGPT | Composer gửi thật vào phiên chat (qua Codex App Server / MCP) |
| Session selector | Chọn dự án; danh sách phiên CoS quan sát được (panel companion W1, nhãn OBSERVED) | Selector cho phiên chat native + liên kết phiên ↔ RUN bằng receipt |
| Timeline | Sự kiện của phiên CoS (chỉ đọc, W1); activity của RUN từ ledger | Timeline của phiên chat native (streaming, tool calls) |
| Tìm kiếm trong phiên | Ctrl+K tìm trang/dự án/lời nhắc/lệnh + tìm trong mã | Tìm trong nội dung phiên chat native |
| File context | Giỏ @file theo dự án + gói ngữ cảnh có nội dung/hash (Đợt 1) | Đính kèm file vào phiên chat native |

## 2. Quyết định port unified-diff: PORT CHỌN LỌC (mô hình dòng + trình bày), không port nguyên file

- File thật đã kiểm tra: `src/renderer/unified-diff.ts` của CoS = 66 dòng, MIT (LICENSE: Copyright (c) 2026 Chat On Steroids contributors). Phần có giá trị: **mô hình dòng** `{kind, old, next, text}`, giới hạn dòng hiển thị có cờ `truncated`, trình bày hai gutter + dấu +/− bằng text node.
- Phần **không** port: thuật toán `Chunk.build` của `@codemirror/merge` trên hai snapshot `Text` của `@codemirror/state` và tô màu cú pháp bằng `@lezer/highlight`. Lý do: (1) đầu vào của Codex-web là *văn bản unified-diff do `git diff` sinh* (backend `workHubFiles.js`), không phải hai snapshot — port nguyên thuật toán sẽ bắt phải đổi backend sang lấy base/current từng tệp, mất phân biệt staged/unstaged đang có; (2) CodeMirror/lezer không có trong renderer hiện tại — kéo vào chỉ để tô màu diff là phình dependency ngược nguyên tắc §2 của AGENTS.md.
- Đã làm thay thế tương đương về *trình bày*: module native mới `renderer/diff-view.js` (`WorkHubDiff.parseUnifiedDiff`) phân tích văn bản git diff thành đúng mô hình dòng của CoS (số dòng old/next suy từ header `@@ -a,b +c,d @@`, đếm +/− đầy đủ kể cả khi hiển thị bị giới hạn ở 600 dòng). Attribution ghi trong header của file và mục mới trong `THIRD_PARTY_NOTICES.md`.
- Bằng chứng "đã tương đương" cho phần còn lại của §5.1: cây file/xem/tìm (F06), danh sách thay đổi + commit chọn lọc có `expectedHead` (M1), duyệt bản vá gắn hash nội dung (F10) đều đã có test và đang chạy — liệt kê ở bảng 1.1.

## 3. Thay đổi đã làm (toàn bộ native, chạy khi không có CoS)

| File | Thay đổi |
|---|---|
| `electron/services/workHubFiles.js` | `gitFileDiff` trả thêm `head` (HEAD tại thời điểm đọc diff) và `fingerprint` (sha256 của đúng nội dung diff chưa cắt). Shape cũ giữ nguyên, tương thích ngược |
| `renderer/diff-view.js` | **Mới** — parser unified-diff thuần (không DOM, test được bằng node:test), dual-export như `work-hub-store.js` |
| `renderer/work-hub.js` | `renderDiff` hiển thị cấu trúc (gutter đôi, hàng theo kind, giới hạn dòng) với fallback văn bản thô khi thiếu parser; ô meta `whDiffMeta` hiện HEAD + fingerprint + nhãn **STALE** khi HEAD đã đổi (đối chiếu mỗi lần `renderGit` tải lại HEAD); khối duyệt bản vá cảnh báo STALE tương tự; nhãn nguồn EOCL/lane trên board worker (mục 1.2); xem commit trong lịch sử dọn meta diff cũ và ghi rõ đang xem commit, không phải diff cây làm việc |
| `renderer/index.html` | Thêm `<p id="whDiffMeta">` dưới khối diff + nạp `diff-view.js` trước `work-hub.js` |
| `renderer/work-hub.css` | Style `.wh-diff-line/.wh-diff-gutter/.wh-diff-sign` theo biến màu sẵn có của app (xanh `--green` cho thêm, đỏ `--red` cho bớt, accent cho hunk) |
| `THIRD_PARTY_NOTICES.md` | Mục attribution cho mô hình dòng unified-diff của CoS (MIT) + ghi rõ chỉ port mô hình trình bày, không bundle code/dependency CoS |
| `tests/work-hub-diff-view.test.js` | **Mới** — 4 test parser: đánh số qua thay/thêm/xóa, hai section stage/chưa stage đánh số độc lập, giới hạn 600 dòng + cờ truncated + đếm vẫn đúng, đầu vào rỗng/binary |
| `tests/work-hub-files.test.js` | Thêm test: `gitFileDiff` trả `head` khớp `gitHead` và `fingerprint` = sha256 của diff; HEAD đổi sau commit được phản ánh ở lần đọc sau |

Không đổi: các tab Yêu cầu/Tiến trình/Thay đổi/Kiểm chứng/Kết quả, IPC, preload, adapter W1.

## 4. Test đã chạy (VM, Node 24)

- Baseline trước khi sửa (7 suite work-hub): **88/88 PASS**.
- Sau khi sửa: `tests/work-hub-diff-view.test.js` + `tests/work-hub-files.test.js` → **24/24 PASS**; toàn bộ suite liên quan (work-hub-ui/store/scope/render-scope/coordination/jobs/browser-qa/lsp/ssh + diff-view + files + cos-companion-adapter) → **157/157 PASS, 0 fail**.
- `node --check` đạt cho `renderer/diff-view.js`, `renderer/work-hub.js`, `electron/services/workHubFiles.js`.
- Lỗi có sẵn từ trước, không liên quan W2: `tests/chat-ui-compact.test.js` fail 1/6 (kỳ vọng chuỗi `Show the settings shell immediately` trong `renderer/app.js` — file sửa lần cuối 22/10, W2 không đụng), giữ nguyên trạng như ghi nhận ở W1.

## 5. Khoảng trống còn lại và ranh giới

- **GUI/packaged**: trình bày diff cấu trúc + nhãn STALE mới chứng minh ở mức test fixture DOM và service test trên VM; nghiệm thu trên bản packaged thật thuộc W6 (T02).
- **Dữ liệu "đang chờ gì"** cho từng delegation chưa có trong ledger — cần bổ sung ở tầng EOCL nếu muốn hiện, không thuộc W2.
- **Tô màu cú pháp trong diff** (CoS có qua lezer): defer có chủ đích — giá trị thấp hơn chi phí dependency; chỉ xét lại nếu có nhu cầu thật.
- **W3** (theo hướng mới): chat native trong Codex-web qua Codex App Server + ChatGPT-over-MCP (không qua app CoS), session linking bằng receipt, handoff — toàn bộ timeline/composer-gửi-thật/session-selector-native nằm ở đó như bảng 1.3. Goal/Compact&Resume logic port (W4) được kéo lên sớm theo chỉ đạo 19:03.
