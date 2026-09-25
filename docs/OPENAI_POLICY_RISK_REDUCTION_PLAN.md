# Kế hoạch hoàn thiện hệ thống và giảm rủi ro chính sách OpenAI

Ngày lập: **25-09-2026**, múi giờ **Asia/Saigon (+07)**. Phạm vi: `E:\DEV\Codex-web`, Windows Execution Hub + Coding Tools MCP + Ubuntu Control Plane.

**Trạng thái tài liệu: kế hoạch để duyệt, không phải chứng nhận tuân thủ hay biên bản hoàn tất triển khai.** Trong lượt lập kế hoạch chỉ tạo tài liệu; giữ nguyên các sửa đổi source và runtime evidence đã có. Không đăng nhập/thử tài khoản bị khóa, không thay quyền, không restart/deploy/commit/push.

## 1. Quyết định kiến trúc đề xuất

Giữ chức năng hữu ích: chọn thư mục trên Windows, quản lý thiết bị qua Ubuntu/Tailscale, đọc/sửa file và chạy lệnh có giới hạn. Loại việc ứng dụng tự quan sát hoặc can thiệp trang ChatGPT khỏi kiến trúc đích.

Đường tác vụ dự kiến, không phải bằng chứng luồng hiện đã chạy:

```text
Người dùng trong ChatGPT/Codex chính thức
  -> kết nối MCP được sản phẩm hỗ trợ, xác thực và cấp quyền đúng phạm vi
  -> Secure MCP Tunnel trên Ubuntu
  -> Ubuntu Control Plane: xác thực, binding, action, receipt
  -> Windows executor qua mạng riêng Tailscale
  -> thư mục đã đăng ký + sandbox + chính sách read/write/exec
```

App Windows chỉ giữ giao diện quản lý executor và nút mở ChatGPT bằng trình duyệt hệ thống theo thao tác người dùng. Không mở ChatGPT âm thầm khi app khởi động. Không thay thế các hook bị gỡ bằng extension, CDP hoặc tiến trình theo dõi trình duyệt ngoài.

Đây là lựa chọn kỹ thuật để giảm bề mặt rủi ro, **không phải khẳng định mọi WebView hoặc mọi phép đo DOM đều bị OpenAI cấm**. Nguyên nhân khóa tài khoản chưa được OpenAI xác nhận; bỏ các phần dưới đây không bảo đảm được mở khóa hay miễn trừ chính sách.

### 1.1 Ba khái niệm phải tách riêng

| Khái niệm | Ý nghĩa | Không được suy ra |
| --- | --- | --- |
| Thư mục làm việc Windows | Đường dẫn do người dùng chọn trong app; ví dụ `E:\DEV\Codex-web`, gắn node/workspace ID/generation | Không phải nhóm ChatGPT; chọn thư mục không tự cấp exec |
| ChatGPT Business workspace | Nhóm thành viên và quyền dùng connector | Không tự cấp quyền đọc ổ đĩa; dùng chung connector không phải dùng chung tài khoản đăng nhập |
| OpenAI Platform organization | Phạm vi quản trị tunnel/runtime key và quyền Platform | Cùng email không đủ chứng minh mọi organization/workspace đã liên kết đúng |

Mục tiêu tự động hóa: không bắt duyệt lặp lại ở app cho thao tác đã được cấp quyền hợp lệ. **Không cam kết tắt mọi xác nhận của ChatGPT**, không tự bấm Allow, không gắn nhãn read-only cho thao tác ghi để tránh xác nhận. Quyền ứng dụng không ghi đè kiểm soát của host/workspace. [Quyền ứng dụng trong ChatGPT](https://help.openai.com/en/articles/20001495-managing-app-permissions-in-chatgpt)

## 2. Baseline đã kiểm tra và giới hạn bằng chứng

### 2.1 Source và runtime

- Git: `main`, HEAD `2b04eec5e98a774daa2fb92749d40a911b472fce` — `Fix scoped pilot healthcheck acceptance`.
- Có patch chưa commit ở 7 file source/test, gồm file test encoding mới. Có 3 file `.coding-tools` đang dirty; không xem chúng là rác hoặc xóa để làm sạch Git.
- Quan sát Windows sáng 25-09: tiến trình vẫn chạy từ `E:\DEV\Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-r9\win-unpacked`. Không có bằng chứng bản này đã nạp patch chưa build.
- Registry local được đọc ngày 25-09: thư mục `E:\DEV\Codex-web`, `read=true`, `write=true`, `exec=false`; file exec policy chưa tồn tại. Registry không chứng minh các policy khác còn hiệu lực hoặc đã E2E.
- Lần SSH Ubuntu gần nhất ngày 24-09 bị Tailscale ACL từ chối user `admin`. **Chưa kiểm tra lại server trong lượt lập kế hoạch**, không khẳng định Ubuntu đang dừng hoặc đang chạy đúng bản mới nhất.
- Tài khoản bị vô hiệu hóa theo email người dùng cung cấp; chưa có phản hồi kháng nghị hoặc nguyên nhân cụ thể từ OpenAI.

### 2.2 Phần đã làm dở, không được báo thành hoàn tất

| Hạng mục | Bằng chứng hiện có | Còn thiếu |
| --- | --- | --- |
| Bỏ hook phản hồi ChatGPT | Patch đã xóa fetch/SSE/JSON.parse/Response.json hooks và bootstrap debugger; 18 test journal và 32 test UI lân cận PASS ở lượt trước | DOM observer, đọc text/counts, consent từ DOM và WebView còn; chưa build/activate |
| Sửa encoding Python–Electron | Đã tái hiện lỗi CP1252/UTF-8 ở 5 bridge; patch đổi pipe sang bytes UTF-8 | Kết quả cuối của nhóm 53 test sau sửa chưa thu được do lượt bị ngắt; không tính PASS |
| Test ranh giới IPC thật | 4 test file-read adapter PASS, gồm stdin JSON → Recovery IPC loopback thật và từ chối request sai | Không chỉ ra được field sai của production action cũ |
| Bridge lân cận | 24 test Node bridge/runtime PASS ở lượt trước | Không phải canary ChatGPT → Ubuntu → Windows |
| Test exec runner | 4 lỗi fixture do gọi tên `python3` trên Windows; đã đổi fixture sang `sys.executable` | Cần xác nhận lại kết quả; không phải bằng chứng exec production được bật |
| Action đọc cũ | `act_048df93488874a70aa97a7ee18ccbd03`, attempt `try_1c5604c35dd64d7fb670773f7708485d`, lần đọc trước còn `unknown/reconcile_required` | Reconciliation theo giao diện hỗ trợ; không retry hoặc suy đoán hoàn tất |

Các số test trên là **kết quả lịch sử của lượt sửa**, không phải test chạy trong lượt lập kế hoạch. Phiên test cuối không còn handle để lấy kết quả; chỉ phần thiếu mới cần chạy lại khi tiếp tục implementation.

### Implementation update — 25-09-2026

- W1 source đã gỡ `ChatViewController`, `ChatEvaluationJournal`, `chatConversationAccess` và `DownloadService`; bỏ IPC/trang Settings xóa session nhúng. Control Center mở trang connector ChatGPT bằng thao tác người dùng qua system browser. Dữ liệu browser cũ trong app profile được để nguyên và source mới không dùng tới.
- Panel layout và executor overview đã đổi sang ngữ nghĩa executor; telemetry thiếu hiển thị unknown. Schema 8 MCP tools/connector không bị đổi chỉ vì gỡ Electron WebView.
- W1/W4 focused Node/Recovery kiểm tra **117/117 PASS**, Python bridge/lane tests **53/53 PASS**; tunnel-child environment allowlist cũng được kiểm trong Node lane.
- Full `npm run test:all` sau đó trả **Node 1019/1019 PASS**, source-root clean và repository secret check PASS; Python **1183 PASS / 5 SKIP / 4 FAIL**. Ba thất bại là WinError 32/5 lúc test continuation xóa temporary directory. Thất bại thứ tư là sandbox npm script không tìm thấy `C:\Windows\System32\cmd.exe` (`ENOENT`). Hệ thống giữ `exec=false`; chưa đổi filesystem/net scope để ép test xanh.
- Candidate `policy-w1-c-20260925` đã build với trạng thái unsigned/dev-only; builder `afterPack` exact-resource check pass. Sáu file Electron/renderer được hash đối chiếu giữa source và `app.asar`, và marker page-instrumentation đã được quét khỏi code đã pack. Isolated Recovery smoke pass: 18 resources, 8 tool contract, Recovery Host/supervisor healthy, production descriptor/Scheduled Task giữ nguyên.
- App r9 trên Windows vẫn chạy source cũ; chưa cài/chuyển runtime. Candidate C chưa thay thế tiến trình đó và chưa chạy live ChatGPT connector.
- W3 auth/user identity, Ubuntu readback hiện tại, đối soát production unknown action, live read/patch/exec, xác nhận quyền từ connector thật và release vẫn là gate mở.
- Local Consent/Task API độc lập được giữ trong repository; local consent HTTP không bị xóa. Thiếu accounting vẫn là unknown và không thể trở thành execution receipt/authority.

### 2.3 Hai kết luận cần sửa cách hiểu

1. `CONTROL_PLANE_FILE_READ_REQUEST_INVALID` và lỗi giải mã UTF-8 là hai vấn đề phải phân biệt. Đã chứng minh lỗi encoding, chưa chứng minh nó giải thích toàn bộ lỗi schema production. Không nới `exactKeys`, kiểu dữ liệu hoặc kiểm tra quyền để làm canary xanh.
2. Deadline của giao dịch activation đã hoàn tất không tự là hạn sống của runtime. `READY` cũ cũng không chứng minh connector/E2E mới. `workspace_accessed=false` trong một lời gọi status trung tâm có thể hoàn toàn đúng; chỉ lời gọi thực sự đọc workspace mới cần bằng chứng truy cập.

Nguồn mã: [bridge admission](E:/DEV/Codex-web/electron/services/controlPlaneFileReadBridge.js:331), [pipe node-agent](E:/DEV/Codex-web/control-plane/control_plane/node_agent.py:4286), [activation epoch](E:/DEV/Codex-web/electron/services/activationEpoch.js:1521), [readiness theo vai trò](E:/DEV/Codex-web/electron/services/runtimeOrchestrator.js:90).

## 3. Căn cứ chính sách và cách áp dụng

Đối chiếu nguồn chính thức ngày 25-09-2026; phải kiểm tra lại khi chuẩn bị release nếu nguồn hoặc sản phẩm đổi.

| Mã | Nguồn | Nguyên tắc dùng trong kế hoạch |
| --- | --- | --- |
| P1 | [OpenAI Services Agreement, §3](https://openai.com/policies/services-agreement/) | Tách tài khoản từng người; không trích xuất trái phép, vượt giới hạn hoặc biện pháp bảo vệ |
| P2 | [Usage Policies](https://openai.com/policies/usage-policies/) | Không dùng công cụ để lạm dụng hệ thống, xâm phạm riêng tư hoặc vượt safeguards |
| P3 | [App Developer Terms, §1–3](https://openai.com/policies/developer-apps-terms/) | Xử lý dữ liệu đúng mục đích, bảo vệ dữ liệu/quyền truy cập, không gây hiểu nhầm app được OpenAI chứng nhận |
| P4 | [Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels) | Tunnel riêng là đường tích hợp được hỗ trợ; quyền Platform và quyền workspace cần đối chiếu riêng |
| P5 | [Build an MCP server](https://developers.openai.com/plugins/build/mcp-server) | Schema/annotations phản ánh hành vi thật; dữ liệu trả về tối thiểu; metadata không thay xác thực |
| P6 | [Authentication](https://developers.openai.com/plugins/build/auth) | Xác thực người dùng và kiểm tra scope cho truy cập riêng/ghi; OAuth 2.1 là hướng tiêu chuẩn được mô tả |
| P7 | [Security & Privacy](https://developers.openai.com/plugins/guides/security-privacy) | Quyền tối thiểu, xác nhận thao tác không thể đảo ngược, phòng prompt injection, log đã lọc |
| P8 | [Plugin guidelines](https://developers.openai.com/plugins/app-guidelines) | Không tự thu toàn bộ chat; công bố dữ liệu thu thập; nhãn tác vụ chính xác |
| P9 | [Managing app permissions](https://help.openai.com/en/articles/20001495-managing-app-permissions-in-chatgpt) | Không dùng cấp quyền local để vượt xác nhận/chính sách của host |
| P10 | [Account deactivation and appeal](https://help.openai.com/en/articles/10562188-why-was-my-openai-account-deactivated) | Sự cố tài khoản giải quyết bằng kênh kháng nghị, không bằng đổi đường gọi để né khóa |

P8 là hướng dẫn cho plugin công bố; ở đây dùng làm chuẩn thiết kế thận trọng. Không suy ra hệ thống nội bộ bắt buộc phải public endpoint hoặc nộp App Directory. Không dùng quy định iframe của plugin để tuyên bố mọi Electron WebView đều vi phạm. Quyết định bỏ WebView là đề xuất sản phẩm của kế hoạch này.

## 4. Ma trận giữ, loại bỏ và giới hạn

| Phạm vi | Bằng chứng/đánh giá | Xử lý đích | Gate |
| --- | --- | --- | --- |
| Hook fetch/SSE/JSON/Response của ChatGPT | Từng có và đã bỏ trong patch; chưa triển khai | Loại khỏi source, package và runtime, không có cờ bật lại ẩn | G1 |
| DOM text/counts, theo dõi lượt/submit/keydown, suy token từ chat | Còn trong source | Loại collection từ trang ChatGPT; số đo không có thành `unknown` | G1 |
| Consent/tiếp tục suy từ DOM ChatGPT | Còn reader và staging | Loại nguồn cấp quyền từ DOM; giữ cơ chế consent local đã xác thực | G1/G3 |
| WebView ChatGPT, cookie partition, auth popup, monitor backend conversation | Có trong app; không tự động kết luận vi phạm | Retire trong kiến trúc đích; mở trình duyệt ngoài bằng thao tác rõ ràng | G1 |
| Chỉnh DOM để gộp tool card | Không cần cho executor | Retire cùng WebView; không chuyển sang extension ngoài | G1 |
| Gọi backend-api, replay cookie, tự login/click Allow | Chưa thấy implementation trong phạm vi đã audit | Cấm bổ sung; regression scan bảo vệ; không xuất/copy session cũ | G1/G2 |
| Đổi account/key/proxy để né suspension/429 | Chưa có bằng chứng đã làm | Không đưa vào fallback; lỗi quyền chặn nhánh liên quan, lỗi tạm thời có backoff hữu hạn | G2 |
| Tailscale + native Secure MCP Tunnel | Giữ theo cấu hình được hỗ trợ | Không public admin UI; chỉ MCP upstream đúng đích; kiểm tra binary và quyền | G2/G3 |
| Shared connector cho 2 người | Đúng yêu cầu sản phẩm; app hiện dùng shared service identity | Mỗi người tài khoản riêng; không giả danh per-user; chốt auth phù hợp trước mutation | G3 |
| Đọc/sửa/chạy lệnh trong thư mục được chọn | Giữ mục tiêu | Policy riêng từng capability, exact binding, sandbox, receipt và revoke | G4 |
| Arbitrary shell, toàn ổ đĩa, upload/deploy tùy ý | Không thuộc bản hoàn thiện tối thiểu | Không mở qua preset; thêm riêng chỉ khi có nhu cầu và đánh giá phạm vi | G4 |
| Task/command logs của hệ thống mình | Cần cho chẩn đoán và lịch sử | Giữ tối thiểu, redaction và quyền đọc; không thu transcript để bù telemetry | G2/G4 |
| Bộ định tuyến/kinh tế dùng số liệu ChatWeb không có | Chưa có đủ số đo | Không coi missing là 0; không promote auto-routing vì giả định chi phí | G1/G5 |

“Loại” ở đây là loại khỏi đường thực thi và gói mới. **Không xóa lịch sử Git, `.coding-tools`, receipt lỗi hoặc tự xóa hồ sơ đăng nhập của người dùng.** Hồ sơ cũ không được mở/đọc/migrate tự động; việc xóa dữ liệu nhạy cảm cần xử lý riêng có xác nhận và theo nghĩa vụ lưu trữ.

## 5. Kế hoạch triển khai theo thứ tự

### W0 — Chốt baseline và khoanh sự cố tài khoản

**Chủ trì:** người triển khai; chủ tài khoản phụ trách kháng nghị. **Phụ thuộc:** không.

1. Ghi HEAD, source diff/hash, đường dẫn executable/app.asar và phiên bản đang chạy; tách WIP khỏi code đã được nghiệm thu.
2. Giữ receipt `unknown`; ghi lại ID, thời điểm và phân loại lỗi, không ghi token hoặc nội dung file vào báo cáo chẩn đoán.
3. Khi bắt đầu triển khai có thẩm quyền vận hành: dừng có kiểm soát các job/account call bị ảnh hưởng; không tắt toàn bộ Ubuntu/Windows và không đụng connector khác. Ghi đúng PID/service đã dừng.
4. Không retry đăng nhập, Refresh tool hoặc provider canary bằng tài khoản bị vô hiệu hóa. Kháng nghị không gửi tự động; không chuyển traffic sang tài khoản người khác để làm thay phần bị chặn.
5. Đọc lại Ubuntu qua quyền SSH/Tailscale đúng user khi truy cập được. Nếu ACL từ chối, giữ blocker hạ tầng, không thử user/key tùy ý hoặc public/Funnel workaround.

**G0 đạt:** baseline reviewable, không có tác vụ mutation chưa xác định chủ sở hữu, phương án bảo toàn evidence và danh sách tài nguyên được phép vận hành rõ ràng. Tài khoản chưa được khôi phục không chặn sửa/test offline, nhưng chặn nghiệm thu qua tài khoản đó.

### W1 — Bỏ tích hợp vào trang ChatGPT, giữ executor hoạt động độc lập

**Chủ trì:** Desktop/runtime. **Phụ thuộc:** G0. **Ưu tiên:** cao nhất.

Phạm vi chính: [chat controller](E:/DEV/Codex-web/electron/chatViewController.js), [journal](E:/DEV/Codex-web/electron/services/chatEvaluationJournal.js), [main](E:/DEV/Codex-web/electron/main.js), [preload](E:/DEV/Codex-web/electron/preload.js), [browser shell](E:/DEV/Codex-web/renderer/browser.js), [browser HTML](E:/DEV/Codex-web/renderer/browser.html), [settings UI](E:/DEV/Codex-web/renderer/app.js), [conversation monitor](E:/DEV/Codex-web/electron/services/chatConversationAccess.js).

1. Hoàn tất patch bỏ response hooks; loại luôn DOM observer, event listener, counts, tool-card script và consent reader của trang ChatGPT. Không giữ code dormant/no-op/fallback để dễ bật lại ngoài review.
2. Chuyển shell hiện tại thành quản lý executor; giữ chọn thư mục, task/command controls, pause/stop, runtime health. Bỏ Back/Forward/Reload/Clear ChatGPT Session thuộc browser nhúng. Nút mở ChatGPT chỉ mở URL HTTPS allowlist, không query chứa token.
3. Retire `onEvaluation`, evaluation timers và các recorder chuyên nhận page events; không xóa local MCP metrics, provider receipt thật hoặc các API task đang dùng hợp lệ.
4. Trước W1, journal chỉ consume `chatweb-host-turn-pending/binding` khi nhận cả host span và controller usage. W1 đã xóa journal và Electron producer; không kéo correlation này vào executor. Dữ liệu/reporting cũ được giữ nguyên dưới nhãn missing/unknown, không tạo receipt usage giả. Dấu vết mã được kiểm lúc baseline: `electron/services/chatEvaluationJournal.js` tại HEAD `2b04eec5`, đã retire trong source mới.
5. Phân tách đo lường và quyền: [live_control](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/live_control.py:205) đang báo thiếu accounting; chưa chứng minh đó là gate execution. Trace consumer trước khi sửa. Giữ trạng thái accounting incomplete và mọi lease/consent/acceptance thật; chỉ bỏ phụ thuộc ngoài ý muốn nếu test tái hiện được.
6. Giữ [consent HTTP local](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/continuation_consent_http.py) cùng xác thực/challenge/expiry. Cấp quyền tiếp tục qua giao diện local hoặc công cụ được hỗ trợ, không bằng việc đọc lời nói từ trang ChatGPT.
7. Giữ reader lịch sử nếu còn báo cáo cần đọc; dữ liệu mới không có phải dùng `chat_journal_unavailable`, `no_host_turn_spans`, `unknown_not_zero`. Không tự suy token/chi phí từ độ dài text hoặc số lệnh tool.

**G1 đạt:** test chứng minh không tạo WebView/session/monitor ChatGPT, không chèn script, không đọc DOM/response/cookie; task local vẫn chạy với host telemetry không có; consent vẫn bị từ chối khi giả mạo/hết hạn; local logs cũ không bị sửa. Có danh sách chức năng bị retire và ảnh/UI kiểm tra tương ứng.

### W2 — Thu hẹp credential, mạng, retry và dữ liệu

**Chủ trì:** Desktop/deploy. **Phụ thuộc:** G0; có thể làm độc lập W1 sau khi chốt giao diện.

Phạm vi: [tunnel environment](E:/DEV/Codex-web/electron/services/tunnelProcessEnvironment.js), [tunnel launcher Windows](E:/DEV/Codex-web/electron/services/tunnelService.js), [recovery plane](E:/DEV/Codex-web/electron/services/recoveryPlaneService.js), [proxy service](E:/DEV/Codex-web/electron/services/proxyService.js), [Ubuntu launcher](E:/DEV/Codex-web/deploy/control-plane-mcp-tunnel-launcher.sh), [secret store](E:/DEV/Codex-web/electron/services/secretStore.js).

1. Thay kế thừa toàn bộ environment bằng allowlist cho từng child: biến hệ thống cần thiết, trust-store/proxy đã chọn và credential đúng vai trò. Không lén làm mất CA/proxy của người dùng. Test bằng secret giả để chứng minh biến không cần thiết không vào child.
2. Tách Runtime API Key, tunnel admin credential, MCP service bearer, node secret và local IPC token. Không truyền operator credential vào tunnel/node hoặc đưa secret vào argv, URL, tool result và log. Không yêu cầu người dùng gửi key trong chat.
3. Ở Windows `central_executor`: không yêu cầu Runtime API Key OpenAI riêng; OpenAI tunnel nằm trên Ubuntu. Giữ direct mode chỉ khi còn một nhu cầu thực tế riêng, không bật đồng thời để “thử route”.
4. Không tự quét/chuyển proxy để khắc phục khóa tài khoản. Giữ một lựa chọn mạng do operator xác nhận; cấu hình enterprise proxy hợp lệ không bị quy thành vi phạm.
5. Phân loại lỗi theo nơi phát sinh. Local bridge 403 không tự đồng nghĩa tài khoản OpenAI bị khóa. Provider disabled/revoked hoặc thiếu quyền là terminal cho nhánh đó; token hết hạn chỉ đi qua flow refresh/reauth chuẩn có giới hạn, không thử key/account khác. 429 theo thời gian chờ được cung cấp, backoff+jitter hữu hạn; timeout/5xx không sinh replay mutation. Kiểm tra cả native tunnel retry và systemd restart budget, không suy từ `RestartSec=5` rằng đang request flood.
6. Allowlist upstream, timeout/size/concurrency; không tắt TLS verification. Giữ admin/health riêng trong Tailnet/loopback. Queue rỗng không chứng minh chưa có request; cần counter và cửa sổ quan sát.
7. Viết data inventory ngắn: dữ liệu nào gửi vào OpenAI qua tool, trường log tối thiểu, ai đọc được, retention. Chỉ trả phần file/kết quả cần cho tác vụ; không gửi cả repo, hồ sơ trình duyệt, `.env` hoặc báo cáo nhạy cảm không liên quan. Secret scan là một lớp, không thay sandbox và quyền truy cập.

**G2 đạt:** child-env tests, secret-output tests, URL/TLS tests, 401/403/429/retry tests và simulated revoke đều PASS; không có outbound account call tự phát khi mở manager. Không coi filter regex là chứng minh tuyệt đối không rò dữ liệu.

### W3 — Chốt xác thực và contract MCP trung thực

**Chủ trì:** Control Plane + chủ Business workspace. **Phụ thuộc:** G0; G2 trước live.

Phạm vi: [facade](E:/DEV/Codex-web/control-plane/control_plane/mcp_facade.py), [OAuth/service principal](E:/DEV/Codex-web/control-plane/control_plane/mcp_oauth.py), [HTTP API](E:/DEV/Codex-web/control-plane/control_plane/http_api.py), [store](E:/DEV/Codex-web/control-plane/control_plane/store.py), [deploy config](E:/DEV/Codex-web/deploy/control-plane.env.example).

1. Đối soát đúng Business workspace, Platform organization, tunnel ID và binary/version. Không tạo tunnel thứ hai chỉ để né lỗi hoặc chuyển quyền từ org khác.
2. Giữ connector dùng chung theo yêu cầu; phân biệt hai tài khoản OpenAI riêng với một backend service principal. Hiện `private_tunnel_service` không chứng minh danh tính từng thành viên. Audit không được ghi “user A đã làm” nếu chỉ biết shared principal.
3. **Gate auth bắt buộc trước file riêng/write/exec:** xác nhận mô hình được host hỗ trợ cho đúng loại kết nối. Tài liệu mô tả OAuth 2.1 cho authenticated MCP; tunnel permission không tự là bằng chứng end-user auth. Nếu mô hình shared principal không có căn cứ hỗ trợ đủ cho use case, không tự đổi thành `noauth` để vượt qua. Khi đó phải chọn auth tiêu chuẩn hoặc giữ remote capability bị chặn; không tự dựng IdP/domain công khai vì người dùng hiện chỉ muốn Tailnet. [Hướng dẫn auth](https://developers.openai.com/plugins/build/auth)
4. Điều kiện có thể phải đổi yêu cầu: không hứa đồng thời “không có hạ tầng auth phù hợp”, “mọi người dùng chung quyền”, “không có xác nhận host” và “full write/exec được nghiệm thu”. Đây là quyết định kiến trúc cần trình operator nếu G3 không thể đáp ứng, không phải lý do nới policy.
5. Audit tám tool theo từng operation: read/write/stop/restart, network access, idempotency, scope, mô tả và annotation. Không mở rộng public tool surface để chữa một lỗi nhãn.
6. Sửa sự không nhất quán đã thấy: `workspace_context` luôn có `readOnlyHint=true` nhưng một cấu hình cho `task_open/task_close`. Phân loại theo side effect thực; annotation cấp tool phải bảo thủ nếu tool chứa operation mutation. Ưu tiên boolean theo capability đang advertise, giữ schema và tests đồng bộ. Không gắn false cho mọi GET chỉ vì có audit log nội bộ, nhưng durable task mutation không được bỏ qua. [Vị trí hiện tại](E:/DEV/Codex-web/control-plane/control_plane/mcp_facade.py:700)
7. Giữ `readOnlyHint=false` cho patch/exec/stop; xác định `destructiveHint` và `openWorldHint` theo hành vi thật. Không giấu khả năng ghi/network dưới wrapper read-only. [Quy tắc annotation](https://developers.openai.com/plugins/build/mcp-server)
8. Nếu bật OAuth, sửa đúng protected-resource metadata gồm `resource`, issuer/audience/scopes. Nếu không dùng OAuth, không trả JSON OAuth sai dạng để giả discovery thành công. Warning metadata cũ là vấn đề cần kiểm tra, chưa được xác nhận là nguyên nhân file-read lỗi.
9. Scope tối thiểu, revoke ưu tiên hơn renewal; đổi generation/root làm quyền cũ mất hiệu lực. Refresh/discovery phải qua client thật và contract mới; không gọi ACK thô hoặc sửa hash/epoch thủ công.

**G3 đạt:** có quyết định auth reviewable, negative tests sai principal/scope/expired/revoked PASS, schema/annotation phù hợp operation. Live G3 còn cần đúng người dùng/host sau khi quyền tài khoản được khôi phục; tài liệu không tự cấp authority.

### W4 — Hoàn thiện read → patch → exec, không trộn với sự cố account

**Chủ trì:** node/Recovery Host. **Phụ thuộc:** source G0; live cần G1–G3.

1. Rà lại patch UTF-8 cả năm subprocess bridges. Input/output dùng bytes UTF-8 chặt chẽ; stderr không làm hỏng receipt; stdout lỗi phải thành typed error, không decode thay thế rồi nhận thành công.
2. Chạy lại phần test cuối chưa thu được. Giữ test CP1252, tiếng Việt, stderr byte lỗi, stdout invalid; dùng Python thực trong fixture Windows, không phụ thuộc alias `python3`.
3. Giữ test thực qua stdin/Recovery IPC. Thêm diagnostic structural cho schema production: chỉ tên field nằm trong allowlist, loại sai/thiếu, fingerprint và action correlation tối thiểu; không log request values, token, nội dung hoặc root tuyệt đối.
4. Xác định chính xác field làm action cũ bị từ chối; nếu chưa có request/trace an toàn thì ghi blocker, không kết luận encoding đã sửa mọi lỗi. `unknown` vẫn phải qua reconciliation được hỗ trợ; không retry mù hay ghi receipt hoàn tất bằng tay.
5. Nghiệm thu read trên file vô hại trong workspace canary được đăng ký rõ ràng. Thành công phải có content/hash/range khớp, `file_accessed=true`, local handle và completed receipt từ đúng node. Status-only không thay phép thử này.
6. Sau read, thử patch một file fixture với preimage hash chính xác. Thử stale preimage, ngoài root, symlink/junction, secret path, revoke giữa chừng và cùng idempotency key: phải không có ghi ngoài ý muốn, không lặp effect.
7. Exec là gate riêng: central capability + local registry + exec policy + sandbox/probe đúng root đều cần đủ. Không đổi `exec=false` thành true trực tiếp trong JSON. Chính sách lệnh phải giới hạn argv, timeout/output/concurrency; `cwd` đơn thuần không phải sandbox.
8. Thử argv vô hại (`node --version`), rồi script fixture không dùng package scripts của repo thật. Không mạng/host-loopback mặc định; process tree phải dừng khi timeout/cancel. Script `npm`/`node`/`python` có thể làm nhiều hơn tên lệnh, nên prefix allowlist không thay OS isolation.
9. Windows Sandbox candidate hiện unsigned/experimental/dev-only: giữ gate release. Nếu máy thiếu tier an toàn, exec tiếp tục off; không fallback host PowerShell tùy ý, bỏ DACL guard hoặc mạng không giới hạn. [Sandbox hiện có](E:/DEV/Codex-web/resources/coding-tools-mcp/coding_tools_mcp/windows_mxc_sandbox.py)

**G4 đạt:** read/patch/exec có receipt độc lập, deny cases không có effect, replay không lặp, stop/expiry/root switch đúng. Có thể công bố read/write đạt và exec còn blocked; không gom thành “full”.

### W5 — Rút gọn Settings và trạng thái vận hành

**Chủ trì:** Desktop UI. **Phụ thuộc:** contract G1–G4 đã rõ.

Giữ một mục “Thiết lập hệ thống”, tận dụng wizard hiện có, chỉ bốn bước:

1. **Máy chủ:** Ubuntu origin trong Tailnet, pairing và trạng thái kết nối.
2. **Thư mục trên máy này:** danh sách root rõ đường dẫn, chọn/thêm/bỏ qua cơ chế được hỗ trợ; không nhầm với nhóm Business.
3. **Quyền:** read/write/exec riêng; hiển thị giới hạn lệnh, network, expiry/revoke và cơ chế shared/per-user thật.
4. **Kiểm chứng:** ba dòng read/patch/exec, receipt gần nhất, thời gian và hành động tiếp theo. Context/task IDs ở phần kỹ thuật, không bắt nhập tay để dùng bình thường.

Phân biệt trên UI: process sống; đã tới Ubuntu; quyền local; quyền connector; canary E2E. `fullyReady` không đổi nghĩa để che missing proof. Với central executor, không ép local direct tunnel/ACK chỉ để xanh; discovery cần kiểm tra ở facade/đường gọi thực sự áp dụng.

**G5 đạt:** người dùng biết lỗi nằm ở account, tunnel, binding, policy, runtime hay action; reopen giữ thiết lập; inventory lỗi khác danh sách rỗng; không hướng dẫn Refresh vô hạn. Không quảng bá đã được OpenAI chứng nhận.

### W6 — Build, activation, nghiệm thu thật và bàn giao

**Chủ trì:** release/operator. **Phụ thuộc:** G1–G5 cho phạm vi định phát hành; quyền vận hành tường minh.

1. Chốt diff có review và test đúng fingerprint. Tách scope đã đạt khỏi blocker external. Giữ các lần thử thất bại trong evidence.
2. Build một unpacked candidate mới, tag chưa dùng; không ghi đè r9 đang chạy. Kiểm tra executable/app.asar/resource hashes chứa đúng source đã sửa, đặc biệt không còn page hooks và có node-agent UTF-8.
3. Smoke trong user-data cô lập, không tự bật OpenAI connection hay mở account page. Kiểm tra local read/write/exec fixtures, service ownership và không đụng descriptor/scheduled task production.
4. Khi được phép, activate Windows bằng lifecycle hỗ trợ, có rollback và current-process identity. Nếu Ubuntu package cần thay, triển khai artifact hash-verified riêng qua quyền SSH đúng; sửa source Windows không tự cập nhật Ubuntu.
5. Chỉ chạy discovery và canary qua ChatGPT khi tài khoản/workspace/connector được phép dùng. Không dùng tài khoản thứ hai làm proxy cho tài khoản bị đình chỉ. Refresh một lần theo contract mới rồi đọc kết quả, không xem thao tác Refresh là bằng chứng PASS. [Quy trình connect/test](https://developers.openai.com/plugins/deploy/connect-chatgpt)
6. E2E trên thư mục canary riêng: inventory/status → chọn binding → read → patch → exec → receipt; sau đó một tác vụ code thật có đầu ra được người dùng kiểm tra. Cùng hiệu ứng không được tạo action thay thế khi attempt cũ chưa đối soát.
7. Chốt commit local khi có yêu cầu delivery; trước mỗi commit/push chạy đúng stage/check evidence của repo. Push/tag/release/publication là quyền riêng, không suy từ “commit”. Không cài installer thử nghiệm như release chính thức.

**G6 đạt:** phân biệt rõ ba mức ở mục 8; handoff có hash/version/runtime/path/receipt, phạm vi quyền và rollback. Không thể nghiệm thu qua tài khoản bị khóa chỉ bằng source/unit tests.

## 6. Ma trận kiểm tra tối thiểu

Các lệnh dưới đây là **dự kiến khi implementation tiếp tục**, chưa chạy trong lượt lập kế hoạch. Bắt đầu bằng nhóm nhỏ; không rerun nhóm PASS nếu source liên quan chưa đổi.

| Boundary | Check/lệnh hoặc test cần có | Bằng chứng cần giữ |
| --- | --- | --- |
| Page removal | Cập nhật focused Node tests cho chat UI/journal/conversation access; thay test obsolete bằng assert không có page access và manager vẫn hoạt động | Source diff + negative test + UI không tạo remote view |
| Encoding, 5 adapters | Từ `E:\DEV\Codex-web\control-plane`: `python -B -m unittest tests.test_bridge_subprocess_encoding tests.test_file_read_node_agent tests.test_approved_patch_node_agent tests.test_document_write_node_agent tests.test_exec_node_agent -q` | Exit code và kết quả đầy đủ; không chỉ dòng bắt đầu |
| IPC envelope | Từ repo root: `node --test control-plane/tests/recovery_file_read_bridge.test.cjs tests/control-plane-file-read-bridge.test.js tests/control-plane-file-read-runtime.test.js` | Đúng kiểu/keys qua IPC, wrong shape từ chối trước effect |
| Correlation/consent | Focused tests cho journal lifecycle, `test_continuation_consent_http.py`, `test_controller_usage_post_turn.py` tại đúng MCP package root | Missing telemetry không thành authority, consent sai bị chặn |
| Auth/contract | `test_mcp_oauth.py`, `test_mcp_private_tunnel_service_facade.py`, `test_mcp_file_read_facade.py`, `test_authority_renewal.py` | Principal/scope/revoke/metadata/annotation matrix |
| Child environment | `tests/tunnel-process-environment.test.js` và mock process cho primary/recovery tunnel | Chỉ biến allowlist; secret giả không ra log/argv |
| Sandbox | `tests/control-plane-exec-sandbox.test.js`, `tests/control-plane-exec-sandbox-probe.test.js` và packaged fixture | Ngoài root/network bị chặn; timeout không còn process |
| Source hygiene | `git diff --check`; `npm run check:repository-secrets`; `npm run check:coding-tools-history` | Không lỗi conflict/whitespace/secret policy; không xóa evidence |
| Release boundary | Follow `E:\DEV\Codex-web\docs\RELEASE_CHECKLIST.md`; full affected suites và packaged smoke chỉ ở integration/release gate | Exact source → exact artifact → exact running identity |
| Live | Account active/authorized + auth G3 + tailnet route; kiểm tra task qua connector thật | Action/attempt/receipt cùng đích, không fake ACK |

Không cần Cargo suite cho tài liệu hoặc thay đổi Electron/Python không chạm Rust. Mọi canary provider/online, install, deploy và restart phải nằm trong quyền vận hành của bước đó.

## 7. Rollback, dữ liệu lịch sử và giao nhận

- Backup có kiểm tra cho settings/binding/policy và release pointer; giữ credential trong nơi bảo vệ, không copy ra tài liệu hay Git.
- Nếu candidate mới lỗi: dừng action admission của phạm vi đó; giữ unknown receipts và evidence; rollback runtime qua cơ chế hỗ trợ. Không rollback bằng cách bật lại ChatGPT hooks rồi dùng tài khoản thật.
- Không sửa SQLite hoặc JSON projection bằng tay để làm status xanh. Reconciliation phải có bằng chứng đúng action và quy trình được hỗ trợ; khi chưa có cơ chế đủ thì chặn, không viết thêm script settle tùy ý.
- Mọi `.coding-tools/**` tiếp tục được bảo toàn theo AGENTS, ngoại trừ hai sidecar SQLite được cho phép. Data minimization áp dụng cho collection mới, không phải lý do tự ý purge lịch sử. Nếu có secret trong evidence, dừng delivery và xử lý secret/rotation theo phạm vi đã duyệt trước khi commit; không giấu file khỏi guard.
- Trước mỗi commit/push: `npm run stage:coding-tools-delivery`, rồi `npm run check:coding-tools-delivery`; xử lý runtime drift bằng snapshot hợp lệ, không sửa receipt hoặc bỏ file. Không auto-push/tag/publish.
- Các tài liệu current-state hiện chứa checkpoint cũ: cập nhật một bản tóm tắt mới khi triển khai đạt gate; giữ chronology và research cũ nguyên vẹn. Không chỉnh dữ liệu cũ thành kết quả mới.

## 8. Định nghĩa hoàn tất và điểm dừng

| Mức | Điều kiện | Không được dùng thay thế |
| --- | --- | --- |
| A — Kỹ thuật local | G1/G2 và các phần source G3/G4 PASS; package đúng source, manager không truy cập trang ChatGPT | Không gọi là end-to-end hoặc tài khoản đã được phục hồi |
| B — Công việc thực tế | Tài khoản/host được phép + auth đúng + real discovery + read/patch/exec receipts + một tác vụ code thật được xác minh | Unit test, runtime healthy, status active không đủ |
| C — Bản phát hành | A/B cùng phạm vi, package/provenance/installer/rollback/security và phép phát hành đầy đủ | Candidate unsigned/dev-only không phải release |

Các điểm dừng cứng:

- Account bị đình chỉ hoặc host không cho action: không bypass; tiếp tục phần offline, để live gate mở.
- Auth shared-service chưa được xác nhận phù hợp: không nâng write/exec thành production.
- SSH ACL từ chối: không tự đổi IAM/user hoặc mở public ingress.
- Unknown effect: không retry mutation, không đổi thành completed theo suy đoán.
- Sandbox không có hoặc không đúng root: exec không bật.
- Package/source/runtime hash khác: không nghiệm thu bằng test của bản khác.
- Thiếu usage: accounting chưa đầy đủ; không tạo số liệu hoặc bỏ authority guard.

## 9. Thứ tự thực hiện và việc tiếp theo

Thứ tự khuyến nghị: **W0 → W1**, đồng thời có thể chuẩn bị **W2/W3** ở mức source; sau đó **W4 → W5 → W6**. Account appeal và SSH/auth access là nhánh ngoại vi, không bắt mọi việc offline phải chờ nhưng phải xong trước live acceptance tương ứng.

W1 đã loại page-access scope khỏi source/candidate. Bước code tiếp theo là chẩn đoán test sandbox `cmd.exe` và WinError32 cleanup độc lập trước khi đổi quyền exec hoặc cấu hình sandbox. Candidate C chỉ nghiệm thu được packaged W1/Recovery; live W3/W4 cần Ubuntu access và connector/tài khoản được phép. Không thêm auth tự chế, tunnel mới hoặc workaround bypass.

Checklist cuối:

- [ ] Không còn đường page access/response hook/DOM consent ChatGPT trong app mới.
- [ ] Executor/Task/Command Center vẫn hoạt động khi không có ChatGPT page.
- [ ] Không lấy missing usage làm 0 hoặc quyền tiếp tục.
- [ ] Credential, child-env và log tối thiểu; không account/proxy fallback né khóa.
- [ ] Auth shared/per-user, workspace và tunnel association đúng, có evidence.
- [ ] Annotation phản ánh mọi operation được advertise.
- [ ] Read, patch và exec có test/receipt riêng; unknown được xử lý hợp lệ.
- [ ] Sandbox đúng root; network và process lifecycle được kiểm chứng.
- [ ] Settings nói rõ thư mục local, nhóm Business và trạng thái E2E.
- [ ] Windows/Ubuntu cùng contract tương thích và artifact đã được xác nhận riêng.
- [ ] Account/live gates được kiểm tra đúng quyền; không tuyên bố mở khóa bằng code.
- [ ] Release/commit/evidence/rollback theo phạm vi được duyệt; không tự push/publication.

**Kết luận kế hoạch:** giữ hệ thống coding và quản trị máy; loại việc app sở hữu, đọc và điều khiển trang ChatGPT; bảo vệ xác thực/scope/receipt/sandbox; hoàn thiện theo gate có bằng chứng. Đây là giảm rủi ro có thể kiểm chứng trong sản phẩm, không phải bảo đảm OpenAI sẽ không áp dụng chính sách với bất kỳ hoạt động nào về sau.
