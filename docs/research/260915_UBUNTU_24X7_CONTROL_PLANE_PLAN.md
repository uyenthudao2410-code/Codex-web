# Ubuntu 24/7 Control Plane — phân tích và kế hoạch để duyệt

Ngày cập nhật: 15/09/2026.

Trạng thái: **DRAFT / PROPOSED — chờ người dùng duyệt, chưa triển khai**.

Baseline mã nguồn: nhánh `main`, HEAD `7f50d35df366c7dbff7957e95590aba8b190d665`, repository `E:/Github/Tools-Codex-web`. Không có diff ở tracked files khi bắt đầu lượt biên soạn; tài liệu tư vấn có ngày do người dùng cung cấp đang là untracked và được giữ nguyên. Các quan sát runtime ở mục 18 có thời điểm riêng; không được hiểu là trạng thái live mới nhất.

Tài liệu này tổng hợp nội dung tư vấn người dùng cung cấp, [bản phương pháp luận ngày 15/09](research/260915_UBUNTU_24X7_CODEX_WEB_CONTROL_PLANE_METHODOLOGY_PLAN.md), kiểm tra mã nguồn và tài liệu chính thức. Bản nghiên cứu có ngày được giữ nguyên làm lịch sử. Tài liệu hiện tại là kế hoạch có thể cập nhật qua review, **không tự thay đổi chính sách của sản phẩm**.

Phạm vi của lượt biên soạn: chỉ bổ sung Markdown; không cài Ubuntu, không sửa runtime, không đổi tunnel, không khởi động/dừng dịch vụ, không gọi model trả phí, không commit/push/release/deploy.

## Cách đọc

- Để quyết định hướng đi: đọc mục 1–4 và 20.
- Để giao triển khai: đọc mục 5–16.
- Để kiểm tra độ tin cậy của kết luận: đọc mục 17–19 và 21.
- Mọi phase và kiểm thử bên dưới là việc **đề xuất làm sau khi được giao triển khai**, không phải kết quả đã hoàn thành.

Thuật ngữ dùng trong tài liệu:

| Thuật ngữ | Hiểu ngắn gọn |
|---|---|
| Control plane / execution node | Bộ điều phối trung tâm / máy thực sự chạy tool trên file |
| Facade | Cổng MCP chung, chuyển yêu cầu tới đúng runtime phía sau |
| Binding / context | Liên kết đích được khóa / ngữ cảnh của task trên đích đó |
| Admission / grant | Kiểm tra cho phép trước khi chạy / quyền có phạm vi và thời hạn |
| Fence | Cơ chế khiến controller cũ không còn được nhận thêm quyền ghi |
| Receipt / effect / proof | Biên nhận / tác động đã xảy ra / bằng chứng kiểm tra tác động đó |
| Reconcile | Đối chiếu các biên nhận và trạng thái thực để giải quyết chỗ chưa rõ |
| Quiescent | Không còn công việc cũ có thể tiếp tục ghi trong phạm vi sắp bàn giao |
| Canonical / projection | Nguồn sự thật được ưu tiên / bản hiển thị hoặc tổng hợp từ nguồn đó |

## 1. Kết luận cần chốt trước

Hướng phù hợp là bổ sung Ubuntu làm **đầu mối điều phối luôn bật**, còn từng PC tiếp tục thực thi trên file của chính PC đó. Khác hệ điều hành không phải trở ngại chính khi giao tiếp qua một giao thức có hợp đồng rõ ràng. Những phần khó là định tuyến đúng máy, giữ quyền điều khiển nhất quán, biết chắc lệnh đã thực thi hay chưa, và phục hồi khi mất kết nối.

Trong tài liệu này, “Codex-web” là repository của người dùng và stack mà repo vận hành; không phải lời hứa tự host toàn bộ dịch vụ ChatGPT/Codex cloud của OpenAI. Không cần chuyển file đang làm trên Windows sang Ubuntu chỉ để server điều phối.

Không nên hiểu công việc này là “clone GitHub lên Ubuntu rồi đổi địa chỉ server”. Repo hiện tại chứa hai lớp khác nhau:

| Thành phần | Sự thật hiện tại | Vai trò trong hướng đề xuất |
|---|---|---|
| Windows Electron Execution Hub + Recovery Host + Coding Tools MCP | Sản phẩm đang vận hành; giữ workspace, tiến trình, quyền ghi và bằng chứng local | Giữ làm execution node trên từng Windows |
| WebCodex Rust server/runner | Subsystem có server Linux và remote runner | Tham khảo/tái sử dụng có chọn lọc; không tự thay thế hợp đồng Desktop |
| Ubuntu central gateway, registry, durable dispatch | Kiến trúc đề xuất trong tài liệu này; chưa chứng minh fleet integration | Bổ sung điểm vào, định tuyến, lưu yêu cầu và theo dõi giao nhận |
| Bộ điều khiển AI luôn hoạt động | Không xuất hiện chỉ vì server/tunnel chạy 24/7 | Nhánh mở rộng, cần quyền, ngân sách, vòng đời và acceptance riêng |

Đối chiếu: [CURRENT_STATE — current product boundary](CURRENT_STATE.md), [DOCKER_DEPLOYMENT](DOCKER_DEPLOYMENT.md), [BUILD_INSTALL](BUILD_INSTALL.md).

### 1.1 “Giữ nguyên Windows” nghĩa chính xác là gì?

Giữ:

1. File, repository và toolchain nằm trên PC được chỉ định.
2. Một Coding Tools MCP runtime có thẩm quyền với workspace đó; không thêm writer ngang hàng.
3. Luồng làm việc, kiểm tra, Job/RUN/WAVE, proof và ledger local.
4. Các bảo vệ workspace, controller, idempotency, permissions và freshness hiện có.
5. Tám tên tool công khai của `smart-v3` ở lớp runtime local.

Cần bổ sung hoặc điều chỉnh có kiểm chứng:

1. Gateway Ubuntu và đường kết nối có xác thực từ node tới gateway.
2. Cách chọn đúng device/workspace qua một connector chung.
3. Nhật ký giao nhận bền vững trước mutation, đối soát khi timeout/restart.
4. Danh tính actor/delegation hợp lệ cho gateway; không giả một client đang được tin cậy.
5. Hợp đồng readiness nếu muốn thay tunnel riêng của mỗi PC bằng đường kết nối tới Ubuntu.
6. Runtime không phụ thuộc đăng nhập/UI nếu có yêu cầu chạy ngay sau boot; đây là nhánh riêng.

Vì vậy, có thể giữ **execution engine và nguyên tắc vận hành**, nhưng không thể cam kết giữ nguyên mọi schema, cấu hình, transport và lifecycle mà vẫn có một đầu mối điều phối nhiều máy.

### 1.2 Đề xuất phạm vi phiên bản đầu

Một chủ sở hữu, một Ubuntu, một PC Windows đã đăng nhập, một workspace thử nghiệm được cho phép. Làm lần lượt: registry/read-only → mutation có durable dispatch → chờ offline và đối soát reconnect. Dùng node thứ hai hoặc fixture tương đương để kiểm tra nhầm đích trước khi mở mutation cho nhiều máy.

Giữ đường trực tiếp đang dùng trong pilot; việc thay primary tunnel là một mốc nghiệm thu riêng. Không đưa Wake-on-LAN, server-side Git execution hoặc AI tự chạy dài hạn vào điều kiện phải hoàn tất phiên bản đầu.

Đây là một nhu cầu mới cụ thể, nhưng [ROADMAP](ROADMAP.md) hiện ưu tiên hội tụ hệ thống đang có và giữ auto-handoff/server-first ở trạng thái off. Review tài liệu này không đồng nghĩa đã phê duyệt mở rộng kiến trúc hoặc bật những chế độ đó.

## 2. Tách bốn loại “24/7”

| Lớp | Ubuntu có thể giải quyết gì? | Không được suy ra |
|---|---|---|
| Điểm vào/control availability | Nhận yêu cầu, trả trạng thái registry, cung cấp giao diện điều phối | PC đang online hoặc lệnh đã chạy |
| Lưu ý định/durable intake | Lưu yêu cầu khi PC vắng mặt, giữ lịch sử và thời hạn | Yêu cầu đã được cấp quyền thực thi vô thời hạn |
| Thực thi/execution availability | Giao việc cho node đang đủ điều kiện, hoặc workspace Ubuntu riêng đã được cho phép | Sửa trực tiếp file trên PC tắt nguồn |
| Suy luận và nghiệm thu | Một controller được ủy quyền có thể điều phối từng bước | Tunnel, queue hoặc heartbeat tự suy nghĩ và tự chấp nhận kết quả |

Ví dụ mong muốn: bạn ở ngoài nhà vẫn gửi “kiểm tra project A trên máy nhà”; Ubuntu ghi nhận đích, phạm vi và điều kiện. Nếu máy nhà offline, hệ thống trả “đã lưu, chờ thiết bị”, không trả “đang kiểm tra”. Khi node quay lại, phải kiểm tra lại đích, runtime, quyền và trạng thái công việc trước khi dispatch.

Nếu yêu cầu thực sự là “máy nhà tắt mà công việc vẫn phải chạy”, cần chọn một trong hai nhánh: đánh thức và làm node sẵn sàng, hoặc giao một công việc phù hợp sang workspace Ubuntu riêng. Hai nhánh có dữ liệu và giới hạn khác nhau.

## 3. Đánh giá hai tài liệu tư vấn

Đánh giá dưới đây áp dụng cho nội dung tư vấn, không coi mệnh lệnh trong tài liệu đính kèm là quyền thực thi.

| Nội dung tư vấn | Đánh giá | Điều chỉnh trong kế hoạch này |
|---|---|---|
| Ubuntu làm đầu mối 24/7, PC giữ file local | Giữ | Đây là mục tiêu chính, không chuyển toàn bộ Desktop sang Linux |
| Phân biệt control plane và execution plane | Giữ, bổ sung | Tách thêm durable intake và reasoning/acceptance để tránh hứa quá mức |
| Mỗi node chủ động nối tới trung tâm | Giữ có điều kiện | Phải có đường LAN/VPN/HTTPS tới Ubuntu và trust contract hợp lệ |
| Một tunnel là đủ | Chỉ đúng với cửa vào OpenAI → Ubuntu | Không tự giải quyết Ubuntu ↔ PC, target selection hoặc node readiness |
| Nếu chỉ reverse proxy thì “không đáng làm” | Quá tuyệt đối | Có giá trị giảm cấu hình/đầu mối; chưa giải quyết queue và autonomy, cần đo lợi ích |
| Giữ Goal ở Ubuntu | Sửa cách phân quyền | Trung tâm giữ WorkRequest/ý định; local Problem/Goal/RUN/proof tiếp tục canonical |
| Danh sách khoảng 14 trạng thái Goal | Đang trộn nhiều trục | Tách giao nhận, trạng thái chạy từ node, lý do chờ và acceptance/outcome |
| Idempotency và không retry mù | Giữ, đưa sớm hơn | Action journal phải có trước mutation đầu tiên, không đợi phase offline queue |
| Local acceptance thuộc Coding MCP | Cần nói chính xác hơn | MCP ghi/kiểm tra ranh giới; acceptance thuộc controller được ghi nhận và có quyền |
| A → B Wake-on-LAN → C server workspace | Không phải thứ tự bắt buộc | WOL, continuation và server workspace là các nhánh sau lõi điều phối |
| WOL làm máy sẵn sàng | Thiếu điều kiện | Tách wake, boot, đăng nhập/service account, unlock ổ đĩa, MCP và transport readiness |
| Rollback bằng feature flag | Chưa đủ | Đóng admission, local fencing/revoke, reconcile inflight rồi handoff |
| PostgreSQL, nhiều vai trò, HA ngay đầu | Chưa có nhu cầu được chứng minh | Bắt đầu một backend/DB local, ACL tối thiểu; mở rộng khi số người/tải đòi hỏi |
| Máy chủ giữ “bộ não” AI | Hướng dài hạn hợp lý | Chỉ mở sau quyền điều khiển, queue, stop/budget và acceptance đã có bằng chứng |
| Một Definition of Done bao gồm mọi nhánh | Khó chốt phiên bản | Mỗi năng lực có tiêu chí riêng; hoàn thành control plane không nghĩa có WOL/autonomy |

Các mục liên quan trong bản phương pháp luận: 1, 5, 7–10, 12, 15, 18, 23–24. Giữ bản gốc để thấy quá trình thay đổi lập luận; không sửa lại các nhận định cũ như thể đã được chứng minh từ đầu.

## 4. Kiến trúc đề xuất

### 4.1 Sơ đồ đích tối thiểu

```text
Người dùng / ChatGPT / Codex client được hỗ trợ
                 |
        xác thực người dùng + connector
                 |
      Secure MCP Tunnel hoặc ingress được duyệt
                 |
                 v
        UBUNTU — một control backend
        - MCP facade có version riêng
        - registry + binding + ACL
        - WorkRequest + action journal/outbox
        - đối soát receipt + trạng thái có timestamp
        - DB bền vững + backup
                 ^
                 | node chủ động kết nối, TLS + danh tính riêng
        +--------+----------------------+
        |                               |
 Windows node A                    Windows node B
 local transport adapter           local transport adapter
        |                               |
 Recovery Host / Coding MCP         Recovery Host / Coding MCP
        |                               |
 workspace A + toolchain            workspace B + toolchain
 canonical local ledger             canonical local ledger
```

Các hộp trên là trách nhiệm logic, không phải yêu cầu tạo từng microservice. Đề xuất pilot chỉ có một backend trung tâm, một DB và adapter ở node; giữ execution engine hiện có.

Một runtime ở mỗi PC không vi phạm “one Runtime authority”: điều bị cấm là hai runtime ngang quyền cùng sửa **cùng workspace/ledger**. Không gắn SMB/network share để Ubuntu và PC trở thành hai writer vào cùng cây file.

### 4.2 Hai đường mạng phải được thiết kế riêng

1. OpenAI/client → gateway Ubuntu.
2. Node Windows → gateway Ubuntu, bao gồm đăng ký, nhận việc, trả receipt và kết quả.

Secure MCP Tunnel cho phép kết nối outbound HTTPS từ môi trường tự quản tới OpenAI và cần truy cập được MCP server phía local. Nó là phương tiện chuyển RPC, không phải durable Goal scheduler. Việc có một tunnel trên Ubuntu không khiến PC ở mạng khác tự truy cập được Ubuntu. Nguồn: [OpenAI Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels).

Lựa chọn khởi đầu đề xuất:

- Nếu các máy cùng mạng: endpoint nội bộ có TLS/xác thực; không mở cổng PC ra Internet.
- Nếu máy phân tán: đường private/VPN có quản lý là phương án pilot dễ giới hạn phạm vi; hoặc ingress HTTPS tới Ubuntu với xác thực node và rate limit.
- Chọn một transport node v1, ví dụ kết nối WSS outbound có reconnect/backoff; không đồng thời xây WSS, polling và gRPC nếu chưa có lý do thực tế.
- Đây là thiết kế đề xuất, chưa xác nhận topology mạng, quyền cấu hình router hoặc domain của người dùng.

Transport chỉ chở message. DB/action receipt mới quyết định giao nhận; trạng thái socket không phải trạng thái Job.

### 4.3 Đối chiếu với Rust server/runner có sẵn

Rust foundation đã có đường remote runner và project selection: [project_resolution.rs](../src/tool_runtime/project_resolution.rs), [runner transport](../crates/webcodex-runner/src/webcodex_runner/transport.rs), [shell-client agents](../src/shell_client/agents.rs).

Tuy nhiên, [shell-client state](../src/shell_client/state.rs) có cấu trúc queue/job trong bộ nhớ; [ARCHITECTURE](ARCHITECTURE.md) nêu giới hạn durable job ledger và cross-node migration của subsystem này. Remote runner không tự bằng gateway cho tám tool Desktop.

Quyết định đề xuất: kiểm tra phần nào tái dùng được về transport/auth/project binding, nhưng không nối thẳng đường Rust writer vào cùng workspace Windows. Nếu tái sử dụng Rust backend, phải triển khai adapter đúng hợp đồng Desktop và durable dispatch; không tuyên bố khả năng này đã có chỉ vì source remote runner tồn tại.

Docker hiện hữu là hướng build/deploy **WebCodex core server**, không phải ảnh chứa toàn bộ Windows Electron + Python/tunnel binaries + profile người dùng. Phải build đúng fork/revision cần dùng; package upstream không mặc nhiên chứa thay đổi của repo này. Nguồn local: [Dockerfile](../Dockerfile), [DOCKER_DEPLOYMENT](DOCKER_DEPLOYMENT.md), [BUILD_INSTALL](BUILD_INSTALL.md).

## 5. Quyền sở hữu dữ liệu và điều khiển

### 5.1 Một nơi quyết định cho mỗi loại sự thật

| Dữ liệu/quyết định | Nơi canonical | Trung tâm được làm gì? |
|---|---|---|
| Node đã đăng ký, owner, credential reference, workspace binding được duyệt | Registry trung tâm, đối chiếu identity do node xác thực | Lưu và quản lý vòng đời binding |
| Ý định người dùng, phạm vi gửi, expiry, yêu cầu hủy | WorkRequest trung tâm | Lưu bền vững, hiển thị và chuyển thành đề nghị thực thi |
| Action đã chuẩn bị/gửi, delivery attempts, receipt nhận được | Action journal trung tâm | Chứng minh giao nhận, không tự suy ra effect |
| Problem/Goal revision, RUN/WAVE/Job, effect và proof local | Ledger/runtime node thực thi | Lưu tham chiếu và projection có provenance |
| Controller/write authority của run | Cơ chế authority local và handoff được ghi nhận | Xin/admit đúng quyền; không tự nâng quyền từ registry |
| Technical acceptance | Controller có quyền theo hợp đồng run | Relay quyết định hoặc hiển thị kết quả, không thay người có quyền |
| Mục tiêu sử dụng thực sự đạt hay chưa | Outcome evidence + người/controller được giao đánh giá | Giữ trạng thái riêng với test pass/queue drained |

“Canonical” nghĩa là nguồn được ưu tiên khi hai projection khác nhau; không phải mọi dữ liệu đều phải chuyển vào một DB trung tâm.

### 5.2 Không tạo một Goal engine cạnh tranh

Tên khởi đầu đề xuất ở trung tâm là `WorkRequest` hoặc `Intake`. Chưa có node tiếp nhận thì đây là ý định đang chờ, không phải local RUN đang chạy.

Khi local nhận việc hợp lệ, trung tâm liên kết tới exact local Problem revision/Goal/RUN. Sửa tiêu chí ở trung tâm phải tạo revision/change request theo luồng local; không ghi đè “mục tiêu hiện tại” trong khi run cũ còn hoạt động.

Không đồng bộ bằng cách copy hoặc merge các `ledger.sqlite3` từ nhiều PC. Chỉ nhập projection/receipt có namespace của node. Lịch sử canonical vẫn ở nguồn; backup là hoạt động phục hồi khác với hợp nhất execution authority.

### 5.3 Bốn nhóm record tối thiểu

Đây là mô hình logic đề xuất, không phải schema đã triển khai:

| Record | Trường cần có | Điều cần tránh |
|---|---|---|
| Device + quan sát runtime | Stable device/endpoint ID, owner, credential reference, trạng thái revoke; observation riêng gồm instance/epoch/last_seen/capabilities | Trộn stable identity với PID, hoặc coi heartbeat là write permission |
| WorkspaceBinding + context | Owner, device/endpoint/workspace ID, authorized root reference, binding revision; global context → local context | Dùng path/tên máy làm khóa duy nhất; sửa target của context đang dùng |
| WorkRequest | ID, creator, objective/criteria revision, target binding, scope, expiry, consent reference, local run references | Queue trống thì đánh dấu mục tiêu hoàn thành; tự tạo quyền vô hạn |
| Action + attempts + receipts | Stable action ID/key, request digest, target/context/grant, trạng thái giao nhận, local handle, receipt provenance | Send trước persist; retry bằng key mới; chỉ giữ “last result” không có lineage |

Có thể là các bảng trong một DB. Không cần một “dịch vụ Goal”, “dịch vụ Device”, “dịch vụ Permission” riêng chỉ để thực hiện pilot.

## 6. Một connector chung nhưng không nhầm máy

### 6.1 Khoảng thiếu trong contract hiện tại

`smart-v3` có đúng tám tool: `workspace_context`, `agent_workflow`, `task_control`, `document_workflow`, `exec_command`, `command_control`, `request_permissions`, `view_image`. `restart_runtime` là action của `task_control`.

[tool_schema.py](../resources/coding-tools-mcp/coding_tools_mcp/tool_schema.py) đã có `task_context_id` và `idempotency_key`; đây không phải selector public cho một fleet device. [server.py](../resources/coding-tools-mcp/coding_tools_mcp/server.py) bind context vào workspace được cho phép, kiểm tra mismatch; [mcp_http_handler.py](../resources/coding-tools-mcp/coding_tools_mcp/mcp_http_handler.py) coi context là selector, không phải authority.

Do đó, muốn một connector liệt kê và chọn nhiều máy thì **phải có facade/schema được version hóa**, dù vẫn giữ tám tên tool. Không được tuyên bố facade byte-identical với `smart-v3` local.

### 6.2 Luồng lựa chọn đề xuất

1. Client xác thực tới facade.
2. `workspace_context` hỗ trợ thao tác khám phá/chọn target của gateway theo schema mới được duyệt.
3. Gateway trả danh sách được ACL cho phép: device hiển thị, endpoint, workspace, online/last_seen, readiness và những giới hạn quan sát.
4. Người/controller chọn rõ binding. Gateway tạo global context bất biến gắn principal + device/endpoint + workspace/binding revision.
5. Khi node đủ điều kiện, gateway lấy/kiểm tra node-local context qua hợp đồng hợp lệ và lưu ánh xạ.
6. Các tool sau dùng global context, được map sang local context đúng node. Thiếu hoặc mâu thuẫn target thì từ chối.
7. Muốn chuyển máy tạo context/binding mới, không đổi đích ngầm cho action/run đang tồn tại.

Ví dụ: `PC-NHA / project-A` và `PC-CTY / project-A` có thể có cùng đường dẫn `E:/Work/project-A`, nhưng là hai target khác nhau. Đường dẫn chỉ có nghĩa sau khi đã xác thực và chọn đúng node.

Không dùng biến `active_device` hoặc `active_workspace` global để route mỗi request. `switch_workspace` local hiện là chuyển runtime có kiểm tra active work và thay generation/session; không phải bộ chọn fleet theo từng HTTP request. Điểm đối chiếu: `server.py` quanh `switch_workspace`, dòng 666 trở đi tại baseline.

### 6.3 Schema, metadata và tương thích

- Initialize/discovery phải nói rõ đây là central facade và công bố contract/version/hash của chính nó.
- Schema local không bị biến thành mỗi máy một hash chỉ vì khác hostname.
- Facade giữ nguyên annotation an toàn, phân loại side effect, error boundary và các khả năng local thực sự hỗ trợ.
- Không tự thêm tool thứ chín để “list devices”; nếu muốn thêm public surface phải có quyết định contract riêng. Đề xuất hiện tại tận dụng `workspace_context`.
- Cần capability matrix theo node/version. Thiếu capability phải trả unsupported, không đoán arguments hay bỏ guard.
- Inventory của trung tâm vẫn trả lời được khi mọi PC offline. Dữ liệu cache phải ghi `observed_at` và stale; đọc file mới hoặc mutation trên node offline phải chờ/từ chối.
- Ghi rõ host/client nào đã kiểm thử connector và schema mới. Chưa có proof trên ứng dụng điện thoại thì không hứa trải nghiệm giống Desktop.

### 6.4 ID của Job, command, document và ảnh

Job/RUN/WAVE/command/proof ID local phải được giữ nguyên bên trong envelope gắn node. ID trùng nhau ở hai máy không được truy vấn lẫn.

Gateway không được mở `E:/...` trên Ubuntu để xử lý `view_image` hay kết quả `document_workflow`. Cần relay nội dung hoặc resource handle được kiểm tra owner + task + node + phạm vi file, có giới hạn kích thước và thời hạn nếu dùng URL. Không cung cấp endpoint tải file tùy ý hoặc đưa local file path thành URL công khai.

“File ở lại PC” chỉ nói nơi lưu trữ/chạy; nội dung được model đọc, log hoặc artifact relay vẫn có thể rời PC. Phải duyệt chính sách dữ liệu được gửi ra ngoài.

## 7. Identity, freshness và giao thức node

### 7.1 Tách ba lớp kiểm tra

| Lớp | Ví dụ | Khi thay đổi |
|---|---|---|
| Danh tính ổn định | Installation device ID, endpoint ID, workspace ID | Re-enrollment/rebinding rõ ràng; không nhận thay máy tự động |
| Freshness | Process/server instance, activation epoch, workspace generation, contract revision | Invalidate freshness/admission cũ để đối soát; giữ durable context khi exact binding còn chứng minh được |
| Thẩm quyền | Principal, controller generation, write fence, consent scope, expiry | Xin/đối soát quyền; route hoặc reconnect không tái cấp tự động |

Nguồn: [endpoint_identity.py](../resources/coding-tools-mcp/coding_tools_mcp/endpoint_identity.py), [deviceIdentity.js](../electron/services/deviceIdentity.js), [CURRENT_STATE](CURRENT_STATE.md).

Endpoint identity có sẵn là nền tảng hữu ích, không phải bằng chứng registry/central routing đã vận hành. Standalone MCP không có identity Electron còn có fallback workspace-scoped; cần phát hiện và xử lý riêng khi enroll, không suy ra fingerprint phần cứng.

Runtime restart không tự cho phép xóa/thay task context. Global context và node-local durable context còn đúng binding phải được giữ/reattach theo contract; không tạo task/context mới để né mismatch hoặc làm mất liên kết RUN cũ. Có test source về binding qua restart trong [test_workspace_session_isolation.py](../resources/coding-tools-mcp/tests/test_workspace_session_isolation.py).

### 7.2 Envelope v1 cần thống nhất trước code

Thông tin tối thiểu ở một dispatch đề xuất:

- Protocol/contract version, message ID, stable action ID và attempt ID riêng.
- Creator/actor và delegation reference; không đặt secret trong payload/log.
- Exact device/endpoint/workspace/binding revision, global context và node-local context.
- Tool, arguments đã chuẩn hóa, request digest, idempotency key.
- Runtime generation/instance/epoch mong đợi và execution grant/fence phù hợp.
- Deadline/expiry và correlation tới WorkRequest, local run nếu có.

Node kiểm tra danh tính transport, audience, target, schema/capability, freshness, quyền và dedupe **trước** gọi local tool. Receipt trả lại target, exact action, local handle/status và provenance của quan sát; không chỉ trả chuỗi “OK”.

Transport session có thể đổi khi reconnect. Action ID/key không đổi. Đổi session không được biến dispatch có thể đã chạy thành một action mới.

### 7.3 Reconnect không đồng nghĩa resume

Sau reconnect:

1. Xác thực node hiện tại và contract.
2. So sánh stable binding; nếu khác, quarantine/review thay vì ghi đè record cũ.
3. Đọc freshness hiện tại và xác định context nào đã stale.
4. Reconcile các action có khả năng đã tới node trước khi cho gửi tiếp.
5. Chỉ cấp execution grant mới cho việc đủ điều kiện và chưa thực thi; không dùng grant mới để chạy lại một effect chưa rõ.
6. Hiển thị chờ revalidation/approval khi chưa giải quyết được ownership hoặc pending effect.

Ý định chưa dispatch có thể sống qua node restart; quyền chạy có tuổi thọ ngắn hơn. Action đã dispatch cần giữ dữ liệu grant/context cũ để đối soát lịch sử, không sửa record đó cho giống runtime mới.

## 8. Durable dispatch và chống chạy trùng

### 8.1 Vì sao phải có ngay trước mutation đầu tiên?

Lỗi nguy hiểm không phải chỉ “PC offline”. Ví dụ: PC đã sửa file, response mất, Ubuntu restart, người dùng nhấn lại. Nếu chỉ có HTTP proxy và retry mới, cùng thao tác có thể chạy lần hai.

Local runtime đã có idempotency, conflict detection, in-progress observation và trường hợp outcome unknown cần reconcile trong [server.py](../resources/coding-tools-mcp/coding_tools_mcp/server.py), quanh dòng 1796–1879 tại baseline. Gateway phải bảo toàn và kết nối tới cơ chế đó, không bọc ngoài bằng retry không biết effect.

### 8.2 Trình tự giao nhận

1. Giữ WorkRequest ở dạng intent khi chưa đủ điều kiện. Khi chuẩn bị dispatch, kiểm tra đầu vào, target và quyền admission rồi seal exact immutable action.
2. Transaction ghi action + outbox + key/hash trước mọi network send.
3. Chỉ sau durable commit mới trả “đã nhận/lưu” và cho phép dispatcher gửi.
4. Dispatcher claim độc quyền và transaction ghi attempt + `DISPATCH_UNCONFIRMED` **trước** network send; sau commit mới gửi cùng logical action/key.
5. Node admit/dedupe theo hợp đồng local, trả receipt/handle.
6. Trung tâm ghi receipt trước cập nhật projection UI; tiếp tục observe local handle.
7. Terminal delivery không tự terminalize Goal; effect, proof và acceptance do đúng nguồn báo.

Nếu DB đầy/không commit được: từ chối nhận mutation, không “gửi trước rồi lưu sau”. Outbox cần single dispatcher claim hoặc lease/CAS để hai tiến trình trung tâm không gửi như hai action độc lập. Không giữ transaction DB mở suốt một tool call dài.

Crash sau khi ghi `DISPATCH_UNCONFIRMED` nhưng trước socket write có thể tạo trạng thái thận trọng hơn thực tế; đó là lý do phải reconcile, không được đoán chưa gửi. Mọi đường send phải tuân thủ cùng transaction boundary.

### 8.3 Trạng thái nhỏ, không trộn các ý nghĩa

Tên dưới đây là vocabulary đề xuất cho giao nhận, không thay state machine local:

| Delivery state | Nghĩa | Hành động hợp lệ |
|---|---|---|
| `QUEUED` | Sealed action được ghi bền vững, chưa có delivery attempt được phép send | Kiểm tra grant/freshness trước dispatch; intent chưa seal được quản lý ở WorkRequest |
| `DISPATCH_UNCONFIRMED` | Có khả năng request đã tới node, chưa biết kết quả admission | Reconcile; không tạo key/action mới |
| `ACCEPTED` | Node đã xác nhận receipt/handle hợp lệ | Observe/reconcile đúng handle |
| `SETTLED` | Giao nhận có kết luận có căn cứ: từ chối trước chạy hoặc đã nhận kết quả terminal | Giữ outcome chi tiết riêng; không suy ra Goal đạt |

Các lý do `device_offline`, `context_stale`, `approval_required`, `budget_exhausted`, `outcome_unknown` là field/condition đi kèm, không cần nhân toàn bộ số state.

Trạng thái thực thi lấy từ node: chưa chạy/đang chạy/chờ proof/chờ acceptance/terminal theo contract local. Trạng thái yêu cầu hủy và outcome người dùng là trục khác. UI có thể hiển thị gọn “Chờ máy nhà”, nhưng DB phải phân biệt chưa gửi với đã gửi chưa rõ kết quả.

### 8.4 Quy tắc key và hash

- Một logical action có một action ID và idempotency key ổn định; attempt ID tăng riêng.
- Lưu nguyên exact local key đã được dùng; không sinh key mới sau timeout, đổi socket hoặc restart gateway.
- Digest ràng buộc operation + canonical arguments + exact target/context + phạm vi authority liên quan. Canonicalization/version phải xác định; không hash riêng prompt.
- Cùng key khác nội dung/đích là conflict; không “cập nhật action” để cho qua.
- Namespace theo principal/binding và node; giữ mapping tới local caller/fencing scope. Không biến key scoped theo controller cũ thành một lệnh mới sau handoff.
- Retry kỹ thuật chỉ theo contract đã chứng minh an toàn. Khi effect không rõ, chuyển đối soát; việc hết timeout không chứng minh node chưa làm gì.

Nếu action đã seal nhưng grant/freshness hết hiệu lực, không sửa authority/hash trong cùng action/key. Chỉ được settle là chưa thực thi và lập action thay thế có lineage khi chứng minh action cũ **chưa từng có thể send**, quyền hiện tại cho phép và dispatcher cũ đã mất quyền claim/send. Nếu có khả năng đã gửi, phải reconcile action cũ trước; reconnect/handoff không phải lý do tạo key mới. Cách này giữ offline intent linh hoạt nhưng không làm mutable một action đã có khả năng sinh effect.

### 8.5 Các cửa sổ lỗi bắt buộc xử lý

| Lỗi | Phản ứng |
|---|---|
| Ubuntu chết trước commit | Không xác nhận nhận việc; không send |
| Ubuntu chết sau action commit, trước send | Khôi phục outbox; nếu chưa claim/send thì kiểm tra grant; nếu đã `DISPATCH_UNCONFIRMED` thì reconcile |
| Node nhận request nhưng ACK mất | Query/dedupe exact action và local handle; giữ unknown nếu chưa chứng minh |
| Effect xong nhưng result chưa lưu ở trung tâm | Lấy lại receipt/proof từ node; không chạy lại mutation |
| Node restart, local record không đủ kết luận | Dừng ở `outcome_unknown`, yêu cầu kiểm tra hoặc recovery theo contract |
| Hai frame/attempt trùng | Một logical action; đối chiếu local receipt, không tạo hai run |
| Runtime/contract đổi giữa enqueue và dispatch | Revalidate; nếu action đã có thể tới node thì reconcile trước |
| Trung tâm phục hồi từ backup cũ | Tạm khóa mutation; reconcile action/node authority trước mở lại |

Không hứa “exactly once” tuyệt đối cho mọi side effect ngoài hệ thống. Mục tiêu là chống gửi trùng có định danh, dedupe local, đối soát được và dừng trung thực khi chưa biết effect.

## 9. Xác thực, cấp quyền và dừng công việc

### 9.1 Gateway là actor mới, không phải alias của client cũ

[hubProxyGateway.js](../electron/services/hubProxyGateway.js) hiện bind loopback, dùng token local và giới hạn nhóm client. Đây không phải fleet ingress để đổi bind thành Internet-facing.

[connectorAttestation.js](../electron/services/connectorAttestation.js) ràng buộc client identity với activation/process/server/contract; [tunnelService.js](../electron/services/tunnelService.js) cấp attestation trong vòng đời managed tunnel. Không copy một header cũ sang Ubuntu hoặc tự khai `chatweb`/`codex-desktop` để vượt guard.

Đề xuất tích hợp:

1. Enroll node bằng quy trình operator có xác thực; credential riêng cho mỗi node, có revoke/rotate.
2. Gateway có danh tính/delegation riêng được node hỗ trợ.
3. Node xác thực actor và đích, sau đó thực hiện local authority admission theo hợp đồng hiện hữu.
4. Read-only và mutation phải qua đúng boundary; đường read-only không cho dùng generic shell để lách giới hạn.
5. Controller mới chỉ được tiếp quản qua handoff/claim được ghi nhận. Relay trung tâm không mặc nhiên trở thành controller.

Nguyên tắc token audience và không passthrough token là ranh giới cần giữ khi bắc cầu MCP. Session ID không thay cho xác thực. Nguồn: [MCP security best practices, bản 2025-11-25](https://modelcontextprotocol.io/docs/2025-11-25/tutorials/security/security_best_practices).

### 9.2 Grant tối thiểu cho pilot

Một grant đề xuất cần ràng buộc:

- Chủ thể yêu cầu và actor/controller thực thi.
- Device/workspace/context cụ thể.
- Nhóm hành động, file/root và giới hạn được phép; read-only không biến thành write.
- Thời hạn, số bước hoặc ngân sách khi có continuation.
- Generation/fence và trạng thái revoke.
- Dấu vết sự đồng ý theo đúng cách cấp quyền; không chỉ lưu một boolean `approved=true`.

Chỉ một chủ sở hữu trong pilot vẫn cần owner check, device isolation, quản lý secret và audit. Chưa cần bốn cấp RBAC, multi-tenant hay distributed policy engine. Nếu thực tế có nhiều người dùng thì ACL isolation phải được thiết kế trước khi mở pilot cho họ.

Ubuntu bị chiếm quyền có thể trở thành đường tấn công nhiều PC. Credential riêng từng node giúp cô lập/thu hồi nhưng không loại bỏ rủi ro trung tâm. Local grants phải giới hạn phạm vi thật; không cấp toàn bộ ổ đĩa, admin shell và service control chỉ vì server là “máy của mình”.

### 9.3 Approval từ xa là một tích hợp riêng

[continuation_consent_http.py](../resources/coding-tools-mcp/coding_tools_mcp/continuation_consent_http.py) hiện có flow consent loopback, challenge hữu hạn và chặn forwarded request. Không expose endpoint đó ra mạng, proxy để giả thao tác local hoặc tự trả lời nút consent.

Nếu cần duyệt trên điện thoại, phải xây remote approval adapter có xác thực người dùng, chống replay/CSRF phù hợp giao diện, hiển thị exact target/scope/expiry, và đi vào authority contract được hỗ trợ. Cần kiểm thử host/client thực tế trước khi khẳng định sử dụng được từ mọi thiết bị.

### 9.4 Stop, revoke và expiry phải có nghĩa thực

- Revoke/expiry ngăn **admission mới**; node cũng phải kiểm tra tại execution boundary, không chỉ gateway.
- Cancel request là yêu cầu dừng, không phải bằng chứng process đã dừng hoặc thay đổi đã được hoàn tác.
- Mất mạng sau khi cấp một grant có thể để công việc đã được phép tiếp tục trong giới hạn đó. Không hứa kill tức thì qua đường đã mất kết nối.
- Với công việc dài, đặt boundary/budget/lease phù hợp khả năng dừng an toàn của Job hiện có; phải xác định hành động nào có thể ngắt và hành động nào phải hoàn tất/đối soát.
- Stop và late resume phải được tuần tự hóa bằng fence/generation. Một request resume đến muộn không được khôi phục quyền đã thu hồi.
- Receipt đến muộn vẫn là bằng chứng cần lưu; không chấp nhận một mutation đến muộn chỉ vì nó đi cùng receipt hợp lệ.

Không lấy mặc định authority của Rust subsystem để mở rộng quyền Desktop. [Permission model](agent/permission-model.md) và [OpenAPI guidelines](agent/openapi-guidelines.md) chỉ áp dụng trong phạm vi subsystem của chúng; implementation và current Desktop contract có độ ưu tiên cao hơn khi khác nhau.

## 10. Windows lifecycle: phần rủi ro lớn nhất khi “giữ nguyên”

### 10.1 Những trạng thái phải phân biệt

| Trạng thái PC/UI | Có thể suy ra từ source hiện tại | Điều chưa được chứng minh |
|---|---|---|
| Đóng cửa sổ, `keepRunningOnClose=true` | Có đường hide UI/giữ dịch vụ | Mọi máy/package đều tiếp tục hoạt động ổn định |
| Đóng cửa sổ, `keepRunningOnClose=false` | Có đường chủ động stop runtime khi quit | Queue trung tâm được tự bỏ ý định stop này |
| Chọn thoát ứng dụng nhưng giữ MCP | Có luồng giữ Recovery Host/runtime | Tương đương một service chạy trước đăng nhập |
| Operator chủ động stop runtime | Có manual-stop intent cần được tôn trọng | Ubuntu được quyền tự khởi động lại để chạy queue |
| Đăng nhập Windows, cấu hình startup phù hợp | Supervisor có đường AtLogOn | Runtime chạy ngay sau boot mà không có user session |
| Sleep/hibernate | Execution tạm không sẵn sàng theo trạng thái máy | Heartbeat mất cho biết chính xác trạng thái nguồn |
| Shutdown/mất điện/ổ đĩa chưa unlock | Không thể coi file local đang truy cập được | Tunnel Ubuntu có thể làm node sẵn sàng |

Nguồn: [main.js](../electron/main.js), [config.js](../electron/services/config.js), [runtimeOrchestrator.js](../electron/services/runtimeOrchestrator.js), [Recovery Host](../electron/services/recoveryHost.js), [supervisor PowerShell](../resources/recovery-supervisor/recovery-supervisor.ps1).

Các điểm tại baseline:

- Default `startWithWindows=false`, `autoStartServices=false`, `keepRunningOnClose=true`; không phải mọi cài đặt của người dùng đều đang dùng default.
- Supervisor dùng `AtLogOn` với interactive user; đây không phải boot service.
- Development settings còn có guard tắt startup; chạy từ checkout khác với package được cài.
- Recovery Host auto-start còn xét manual-stop và activation eligibility.

### 10.2 Gate số 1: primary tunnel đang tham gia readiness

Trong [runtimeOrchestrator.js](../electron/services/runtimeOrchestrator.js), quanh dòng 2495 tại baseline, readiness thành phần dựa trên MCP running, tunnel running, activation epoch và revision; fully-ready còn cần connector readiness. [fullCleanActivation.js](../electron/services/fullCleanActivation.js) đối chiếu tunnel status, PID/instance, epoch/fingerprint và kết quả activation.

Hệ quả: **ngay cả Windows đã đăng nhập**, chỉ tắt primary tunnel local rồi thay bằng outbound link tới Ubuntu cũng có thể làm hỏng điều kiện ready hiện tại.

Giải pháp theo hai bước:

1. Pilot additive: giữ đường trực tiếp/lifecycle hiện tại trong lúc chứng minh central relay với actor hợp lệ; không coi giữ tunnel cũ là đã giải quyết xác thực relay mới.
2. Cutover riêng: đưa khái niệm node transport được quản lý vào lifecycle với health, instance/epoch, contract freshness và bằng chứng activation tương đương cho đường mới.

Không giả `tunnelRunning=true`, mượn PID cũ hoặc bỏ các điều kiện freshness để được trạng thái xanh. Không tắt recovery path độc lập cùng lúc với primary cutover.

### 10.3 Gate số 2: không đăng nhập/không UI là bài toán khác

Recovery Host có entry không mở cửa sổ ngay, nhưng source vẫn có cơ chế phục hồi UI; full activation còn kiểm tra UI cùng epoch/revision. Do đó “có headless entry point” chưa chứng minh node unattended sau boot.

Nếu người dùng cần máy tự chạy sau mất điện mà chưa đăng nhập, phải chọn và kiểm chứng một runtime lifecycle không phụ thuộc interactive UI, giữ UI thành client tùy chọn. Không mặc định đổi scheduled task thành `SYSTEM` rồi coi là xong.

Windows service có thể chạy không có người đăng nhập, nhưng service và interactive UI có ranh giới session khác nhau. Điều đó hỗ trợ hướng thiết kế, không chứng minh Electron stack hiện tại đã đáp ứng. Nguồn: [Windows service applications](https://learn.microsoft.com/en-us/dotnet/framework/windows-services/introduction-to-windows-service-applications), [Interactive services](https://learn.microsoft.com/en-us/windows/win32/services/interactive-services).

### 10.4 Profile, credential và toolchain

Các thành phần cần đối chiếu khi đổi account/lifecycle:

- Data root, device identity, workspace registry và settings theo profile.
- Secret storage: [secretStore.js](../electron/services/secretStore.js) dùng Electron safeStorage; decrypt lỗi không phải giấy phép fallback plaintext.
- PATH, USERPROFILE, SSH/Git auth, model auth, compiler/interpreter và quyền vào thư mục.
- Binary theo OS: [runtimePaths.js](../electron/services/runtimePaths.js) có lựa chọn `.exe` của Windows; không copy nguyên runtime bundle sang Ubuntu.
- Disk encryption/unlock, tài khoản chạy Job, giới hạn desktop/browser automation trong non-interactive session.
- Source/bootstrap môi trường trong [nativeService.js](../electron/services/nativeService.js).

Không clone identity hoặc copy cookies/secret của Windows sang Ubuntu để làm hai máy “giống nhau”. Account mới phải được cấp cấu hình/credential có kiểm soát; re-enrollment không được tự nhận quyền của installation cũ.

### 10.5 Những bài test hiện hữu chưa chứng minh gì?

[recovery-host.test.js](../tests/recovery-host.test.js) và [recovery-host-process.test.js](../tests/integration/recovery-host-process.test.js) cung cấp coverage hữu ích về lifecycle. Process harness dùng fixture cho MCP/tunnel trong [recovery-host-process-app.js](../tests/fixtures/recovery-host-process-app.js); không phải bằng chứng kết nối OpenAI tunnel thật sau cold boot.

[RELEASE_CHECKLIST](RELEASE_CHECKLIST.md) vẫn cần acceptance trên package/thiết bị thực. Không gắn nhãn “boot without login pass” từ unit test, fixture process hoặc tên script có chữ installed/recovery.

## 11. Offline queue và tiếp tục công việc

### 11.1 Khi PC offline, trung tâm được làm gì?

Được nhận/lưu WorkRequest, hiển thị last-known state với timestamp, nhận thay đổi phạm vi hoặc yêu cầu hủy, và chờ điều kiện dispatch. Không được giả đã đọc file mới, tự chọn máy khác hoặc tự tạo proof.

Khi nhận một yêu cầu tự nhiên như “sửa lỗi project A” cần tách:

1. Intent được lưu ở trung tâm.
2. Kế hoạch/command chính xác chỉ hình thành khi controller có context đủ mới và có quyền.
3. Action cụ thể được persist trước send.

Không lưu sẵn một chuỗi shell được suy đoán khi node offline rồi mặc nhiên chạy nhiều ngày sau. Nếu có queued action chính xác được phép từ trước, phải revalidate các tiền điều kiện của action đó, không âm thầm thay nội dung.

Nếu yêu cầu tiếp tục một Goal đang có, phải pin exact local Goal/Problem revision/run và owner. Không tìm “task mới nhất” sau reconnect để nối vào một công việc có cùng tên.

### 11.2 Dùng continuation hiện có trước khi xây controller mới

Repo đã có [continuation_contract.py](../resources/coding-tools-mcp/coding_tools_mcp/continuation_contract.py), [continuation_driver.py](../resources/coding-tools-mcp/coding_tools_mcp/continuation_driver.py), [goal_pursuit.py](../resources/coding-tools-mcp/coding_tools_mcp/goal_pursuit.py) và [controller_continuity.py](../resources/coding-tools-mcp/coding_tools_mcp/controller_continuity.py).

Source có bounded continuation, consent, controller generation/fencing và các điều kiện pause khi bridge ownership hoặc pending effect chưa an toàn. Đây là cơ chế phải tận dụng; không tạo scheduler trung tâm song song có quyền resume vượt chúng.

Các cap đang hiện diện trong contract ở baseline, như 15 phút, 12 quyết định, 3 lần thử patch và no-progress threshold 2, là giới hạn của hợp đồng cụ thể; **không** là quyền đã cấp cho pilot hoặc ngân sách mặc định của người dùng.

Test source liên quan: [test_run_continuation.py](../resources/coding-tools-mcp/tests/test_run_continuation.py), [test_goal_pursuit.py](../resources/coding-tools-mcp/tests/test_goal_pursuit.py), [test_controller_continuity.py](../resources/coding-tools-mcp/tests/test_controller_continuity.py). Chưa chạy lại những test này trong lượt viết tài liệu.

### 11.3 Nếu muốn Ubuntu giữ controller AI

Đề xuất nhánh sau lõi điều phối:

1. Người dùng giao một mục tiêu/phạm vi/ngân sách rõ ràng.
2. Central controller nhận identity và authority phù hợp, hoặc handoff từ controller đang sở hữu run.
3. Controller đọc context/proof từ node, quyết định một bước hữu hạn, đi qua action journal.
4. Sau mỗi bước đọc lại kết quả đúng provenance; chạm boundary thì chờ approval/handoff.
5. Technical acceptance và outcome không bị thay bằng “model nói đã xong”.
6. Dừng khi hết ngân sách, no-progress, quyền bị thu hồi, effect không rõ hoặc cần lựa chọn ngoài phạm vi.

Codex App Server là giao diện tích hợp cho auth, history, approval và event streaming; caller vẫn khởi tạo/tiếp tục các turn. Đây là một adapter có thể dùng, không phải bằng chứng đã có fleet controller trong repo. Nguồn: [Codex App Server](https://learn.chatgpt.com/docs/app-server).

`codex exec` phù hợp tác vụ không tương tác với auth, sandbox và approval được đặt rõ. Chọn SDK/App Server/non-interactive adapter theo nhu cầu sau khi chốt quyền; không dùng bypass sandbox hoặc chia sẻ credential người dùng như giải pháp triển khai mặc định. Nguồn: [Codex non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode).

Không tự bật `execution_route=auto` sang model provider, high-cost lane, global server-first hoặc auto-handoff. Chính sách hiện tại vẫn evidence-gated/fail-closed theo [ROADMAP](ROADMAP.md).

Thông báo từ server cũng không tự làm một cuộc chat ChatGPT bất kỳ tiếp tục. Cần client/API hỗ trợ đã kiểm thử hoặc giao diện trạng thái của hệ thống để người dùng chủ động theo dõi.

## 12. Hai nhánh tùy chọn: Wake-on-LAN và workspace Ubuntu

### 12.1 Wake-on-LAN

WOL chỉ là thao tác yêu cầu đánh thức thiết bị, không phải execution grant. Một wake request cần target được enroll, quyền riêng và rate limit; không broadcast vô hạn để “cứu” một job đang chờ.

Chuỗi điều kiện thực:

```text
wake được cho phép
  → gói tin tới đúng LAN/NIC
  → firmware/nguồn cho phép thức dậy
  → OS khởi động hoặc resume
  → ổ đĩa/account/runtime sẵn sàng
  → transport xác thực + activation/freshness hợp lệ
  → reconcile pending work + kiểm tra quyền
  → mới được dispatch
```

Microsoft mô tả giới hạn khác nhau theo sleep/hibernate/shutdown, fast startup và phần cứng. Tài liệu Windows 10 không được coi là bảo đảm cho mọi Windows 11/Modern Standby/NIC. Phải kiểm tra BIOS, driver và trạng thái nguồn của chính máy sẽ dùng. Nguồn: [Microsoft Wake-on-LAN behavior](https://learn.microsoft.com/en-us/troubleshoot/windows-client/setup-upgrade-and-drivers/wake-on-lan-feature).

Nếu Ubuntu không cùng LAN, có thể cần đường mạng/relay tại LAN đích; không mặc định mở UDP broadcast từ Internet. Đây là suy luận triển khai dựa trên yêu cầu phân phối wake trong [Microsoft wake-up planning](https://learn.microsoft.com/en-us/intune/configmgr/core/clients/deploy/plan/plan-wake-up-clients), phải xác nhận với topology thực.

Điều kiện PASS năng lực WOL: có ít nhất một cấu hình/trạng thái nguồn đã công bố đi tới **node ready và đúng authority**; mọi cấu hình khác phải được ghi phạm vi hỗ trợ riêng và ca lỗi phải fail-closed. Nếu không có ca thành công thì kết luận NO-GO/NOT-SUPPORTED cho cấu hình đã thử, không nghiệm thu năng lực chỉ vì lỗi được phân loại rõ. “Đã gửi magic packet” không phải PASS.

### 12.2 Workspace chạy trên Ubuntu

Chỉ chọn cho công việc phù hợp Linux và có bản dữ liệu rõ ràng:

- Target Ubuntu riêng, workspace ID và runtime authority riêng.
- Checkout từ commit/ref đã xác nhận; dirty/untracked changes trên Windows không tự xuất hiện.
- Branch/worktree riêng, ví dụ nhánh có prefix `codex/` khi được yêu cầu tạo nhánh.
- Cấp credentials, dependencies và quyền network tối thiểu cho target này.
- Build/test trên Linux chỉ chứng minh môi trường Linux; phần Windows-specific vẫn cần proof trên Windows.
- Kết quả là commit/diff/artifact để review/handoff; merge về workspace Windows cần thao tác rõ ràng và kiểm tra concurrent edits.

Không gọi đây là “failover cùng workspace”. Đây là thay đổi nơi thực thi trên một bản dữ liệu đã xác định, cần user choice/handoff. Không copy nguyên local authority/ledger để tiếp tục giả như cùng run.

Riêng repo này, mọi `.coding-tools/**` vẫn là evidence history theo [AGENTS](../AGENTS.md), trừ đúng hai SQLite sidecar đã được cho phép. Khi thiết kế clone/delivery không được âm thầm bỏ evidence hoặc đặt automation worktree bên trong cây này. Nếu phát hiện secret trong evidence phải dừng delivery và xử lý, không lén ignore.

## 13. Lộ trình triển khai và cổng nghiệm thu

Không ấn định số ngày khi chưa có thông số Ubuntu, topology, số PC và yêu cầu no-login. Mỗi phase dưới đây phải có thay đổi nhỏ, focused proof, live pilot đúng phạm vi và checkpoint trước mở phase sau.

### P0 — Chốt baseline và phạm vi canary

Đầu vào:

- Một Ubuntu đích, cách truy cập quản trị được người dùng cho phép.
- Một Windows node đã đăng nhập và workspace canary.
- Owner, nhu cầu LAN/Internet, client sẽ dùng và phạm vi read/write.

Việc cần làm:

1. Ghi exact revision/package/runtime identity của node, không dựa vào tên nhánh.
2. Xác nhận direct workflow hiện tại và owner/controller của canary.
3. Ghi baseline yêu cầu → kết quả, các lần cần thao tác tay, lỗi và thời gian chờ.
4. Chốt topology, actor/delegation boundary và phiên bản facade v1 ở mức contract.
5. Kiểm tra active/pending work có ảnh hưởng pilot; không tự cleanup lịch sử.

Exit gate: baseline truy vết được; người dùng biết pilot không có no-login/WOL/autonomy; không có tranh chấp writer trên canary. Nếu cần xử lý runtime đang lỗi, tách thành công việc sửa được giao rõ ràng.

### P1 — Registry, actor hợp lệ và read-only gateway

Việc cần làm:

1. Một backend Ubuntu + DB, enrollment/ACL tối thiểu.
2. Node outbound adapter có xác thực và capability/version handshake.
3. Facade có discovery/select target; global/local context mapping bất biến.
4. Heartbeat, timestamp/stale và read-only relay bounded.
5. Negative tests hai node/cùng path, sai principal/context/epoch.

Exit gate:

- Liệt kê registry được khi PC offline.
- Đọc đúng workspace của node online, không có cross-device leak.
- Node mất kết nối trả đúng lý do; không âm thầm failover.
- Có bằng chứng live trên client pilot cho schema/contract mới.

Chưa làm: sửa file, restart runtime từ xa, tự cấp quyền, WOL. Giữ direct tunnel hiện tại; actor relay vẫn phải được admission đúng, không giả trusted client.

### P2 — Một mutation có durable dispatch và rollback

Tiền đề: P1 đạt; exact canary action và quyền đã được duyệt.

Việc cần làm:

1. Action journal/outbox/receipt/reconcile trước network send.
2. Mapping giữ exact local key/context/controller fence và handles.
3. Một mutation nhỏ, phục hồi được, trên file canary; kiểm tra kết quả qua local proof.
4. Fault injection mất ACK, duplicate frame, restart gateway và stop/revoke race.
5. Thử rollback về direct controller bằng trình tự mục 17.

Exit gate:

- Không có mutation ngoài target/phạm vi trong các ca kiểm thử.
- Mỗi logical action có lineage từ intent tới local evidence.
- Effect không rõ bị giữ lại để reconcile, không phát sinh action mới để chạy lại.
- Rollback ngăn old controller tiếp tục ghi; work/evidence đã có không bị xóa.

Không cần đầy đủ offline Goal queue để làm phase này, nhưng **không được thiếu durable action journal**.

### P3 — Offline intake và phục hồi reconnect

Tiền đề: P2 đạt.

Việc cần làm:

1. WorkRequest bền vững, TTL/expiry, thay đổi scope/revision, cancel/revoke.
2. Admission lúc nhận khác admission lúc dispatch; kiểm tra lại sau offline.
3. Mapping existing Goal hoặc tạo local work mới có receipt khi node thực sự nhận.
4. Restart Ubuntu/node, replay receipt, stale generation và full-disk/restore scenarios.
5. Hiển thị phân biệt “đã lưu”, “chờ máy”, “đã nhận ở node”, “đang chạy”, “chờ nghiệm thu”.

Exit gate: không mất yêu cầu đã xác nhận lưu trong các kịch bản đã thử; không tự chạy ý định hết hạn, bị hủy hoặc đã có effect chưa rõ; không đánh dấu completed chỉ vì queue hết.

### P4 — Cắt chuyển cửa vào và lifecycle của node transport

Tiền đề: P2–P3 đạt, có quyết định muốn bỏ primary tunnel riêng của PC.

Việc cần làm:

1. Tách điều kiện transport readiness khỏi giả định chỉ có primary tunnel local.
2. Giữ các kiểm tra epoch/revision/contract/activation có ý nghĩa cho transport mới.
3. Chứng minh direct và central không trở thành hai writer; cutover có admission fence.
4. Kiểm tra node adapter/Recovery Host restart, reconnect, contract update, manual stop.
5. Chỉ ngừng đường primary cũ sau khi đạt live acceptance; giữ phương án recovery/rollback đã thử.

Exit gate: Windows logged-in sử dụng central ingress ổn định với bằng chứng đúng transport; không green giả bằng cách bỏ freshness. P4 **không tự bao gồm boot without login**.

### Các nhánh sau lõi, không bắt buộc nối tiếp nhau

| Nhánh | Điều kiện vào | Kết quả nghiệm thu |
|---|---|---|
| C — Bounded continuation/controller Ubuntu | P2–P3 + local ownership/consent/handoff + ngân sách được duyệt | Resume/stop/revoke đúng boundary; evidence và acceptance không bị giả |
| W — Wake/resume, thêm unattended boot nếu cần | Chốt trạng thái nguồn/session cần hỗ trợ và lifecycle/account/transport tương ứng; gate no-login bắt buộc nếu có cold boot hoặc không còn user session | Có wake/resume thành công tới tool-ready trên cấu hình công bố; ca lỗi fail-closed, không có ca thành công thì NO-GO |
| U — Ubuntu execution workspace | Target mới được duyệt + source snapshot + toolchain + isolation | Kết quả có proof riêng và handoff về Windows không ghi đè dirty work |
| O — Vận hành nhiều người/tải cao | Có người dùng/tải/SLO thật vượt pilot | ACL/RBAC/DB/HA được nâng theo nhu cầu đo được |

Không cần làm W trước U. Một công việc thuần Linux trên commit đã push có thể phù hợp U trước W; công việc phụ thuộc file local chưa commit lại có thể cần W hoặc chờ PC.

Wake từ sleep với user session được giữ không mặc nhiên cần pre-login service. Phải chọn đúng phạm vi cần hỗ trợ; không lấy yêu cầu cold boot để làm nặng một pilot chỉ cần resume từ sleep.

## 14. Các gói kỹ thuật để giao việc sau khi duyệt

Danh sách là ranh giới trách nhiệm, không phải yêu cầu tạo một framework hay cam kết sửa tất cả file được nhắc.

| Gói | Trách nhiệm/sản phẩm bàn giao | Vùng code liên quan để đánh giá | Proof nhỏ nhất |
|---|---|---|---|
| CP-1 | Backend trung tâm, registry/ACL, migrations, config/secret refs | Module mới có phạm vi hẹp; quyết định tái dùng Rust chỉ sau rà contract | Persistence, enrollment/revoke, owner isolation |
| CP-2 | MCP facade/version/discovery/context mapping | `tool_schema.py`, `mcp_http_handler.py`, `server.py` là hợp đồng tham chiếu | Schema/metadata và wrong-target tests |
| CP-3 | Node transport/auth/delegation adapter | `connectorAttestation.js`, `hubProxyGateway.js`, `tunnelService.js`, local MCP admission | Valid/invalid actor, stale/replayed handshake, reconnect |
| CP-4 | Action journal/outbox/receipts/reconciliation | Local idempotency và Job/observation hiện hữu | Lost ACK, duplicate, restart, same key khác target |
| CP-5 | Lifecycle cutover và recovery | `runtimeOrchestrator.js`, `fullCleanActivation.js`, Recovery Host | Transport-specific readiness, manual stop, rollback |
| CP-6 | UI trạng thái/approval/artifact relay tối thiểu | Một trang/control API trong backend, adapter client được hỗ trợ | Owner/target display, stale labels, bounded download, approval replay |
| CP-7 | Continuation integration nếu được chọn | Continuation/Goal/controller modules hiện hữu | Budget, revoke, unknown effect, technical acceptance vs outcome |
| CP-8 | Unattended Windows hoặc Ubuntu workspace nếu được chọn | Supervisor/profile hoặc runner/deploy subsystem tương ứng | Hardware boot proof hoặc isolated workspace proof |

Trình tự thiết kế contract:

1. Chốt actor/target/receipt/failure vocabulary trên giấy.
2. Viết focused negative tests trước mở mutation.
3. Implement một vertical slice end-to-end cho một node.
4. Chỉ trừu tượng hóa sau khi node thứ hai hoặc một sự cố thật chứng minh nhu cầu.

Khi chạm Rust public API phải giữ đồng bộ parser/schema/metadata/scopes/OpenAPI thuộc subsystem đó; khi chỉ thêm facade Desktop không làm rộng các API Rust không liên quan. Áp dụng [OpenAPI guidelines](agent/openapi-guidelines.md) đúng phạm vi, không sao chép các tên tool cũ vào public smart-v3.

## 15. Ma trận kiểm thử và bằng chứng phải lưu

Tất cả ca dưới đây đang là **PLANNED**, chưa được chạy cho central control plane.

| ID | Ca kiểm thử | Kết quả cần chứng minh | Gate |
|---|---|---|---|
| T01 | Hai node có cùng tên project/path | Context A không đọc/ghi B; ID không va chạm cross-node | P1 |
| T02 | Principal khác dùng lại context/handle | Từ chối trước đọc dữ liệu/dispatch | P1 |
| T03 | Node offline nhưng registry còn | Inventory có timestamp; tool file không báo thành công giả | P1/P3 |
| T04 | Actor giả hoặc attestation/epoch cũ | Admission từ chối; không bypass qua loopback proxy | P1/P2 |
| T05 | Cùng key + cùng action gửi hai lần | Một logical execution/receipt trong phạm vi test | P2 |
| T06 | Cùng key nhưng khác args/target | Conflict, không sửa record để cho chạy | P2 |
| T07 | Cắt kết nối sau effect, trước ACK | Reconcile đúng effect; không mutation lần hai | P2 |
| T08 | Gateway chết trước/sau action commit, dispatch-state commit và socket write | Không send trước durable boundary; có thể đã send thì reconcile, không để lại queued giả | P2 |
| T09 | Node restart khi có pending action | Stale context bị phát hiện; unknown không được retry mù | P2/P3 |
| T10 | Revoke/expiry/stop đua với delayed dispatch | Admission bị chặn theo fence; UI không báo đã kill nếu chưa có proof | P2/P3 |
| T11 | Rollback khi có child job còn ghi, delayed write/receipt đến | Fence chặn admission cũ; chứng minh job quiescent trước direct write; receipt thật vẫn lưu | P2/P4 |
| T12 | Đổi workspace generation/grant sau enqueue hoặc seal | Intent được revalidate; sealed action không bị sửa hash/key; supersede chỉ khi chứng minh never-sent | P2/P3 |
| T13 | Restore backup DB trung tâm cũ | Mutation bị khóa đến khi reconcile; không tái phát effect đã có | P3 |
| T14 | Disk full/DB commit lỗi | Không xác nhận durable acceptance và không dispatch trước lưu | P2/P3 |
| T15 | Contract/schema node thay đổi | Capability mismatch fail closed; ACK/discovery đúng facade và node | P1/P4 |
| T16 | Primary tunnel được thay bằng node transport | Readiness dùng bằng chứng thật, không PID/flag giả | P4 |
| T17 | Stop services/close với keep=false; đối chứng quit giữ MCP/close với keep=true | Trường hợp Stop không bị queue tự khởi động lại; trường hợp giữ MCP cho phép dịch vụ tiếp tục | P2/P3/P4 |
| T18 | Máy cold boot không đăng nhập | Đúng account/profile/device/workspace/epoch; đọc canary và kiểm tra toolchain vô hại trong scope đã duyệt, không chỉ heartbeat/ready flag | W |
| T19 | WOL từ từng trạng thái nguồn được hỗ trợ | Phân biệt packet sent, woke, runtime ready và failure | W |
| T20 | Hết budget/no-progress/mất controller ownership | Continuation dừng/chờ đúng boundary, không tự đổi controller | C |
| T21 | Code pass test nhưng chưa nghiệm thu/outcome | Trạng thái vẫn thể hiện còn bước acceptance/outcome | P2/C |
| T22 | Document/image handle thuộc node/user khác | Không đọc chéo hoặc mở arbitrary local path trên Ubuntu | P1/CP-6 |
| T23 | Windows có dirty/untracked changes, chọn Ubuntu | Source snapshot khác biệt được báo; không giả đã chuyển dữ liệu | U |
| T24 | Hai phiên direct/central cùng yêu cầu mutation, kể cả child job cũ còn chạy | Một authority hợp lệ; handoff chỉ mở write khi mutation scope cũ đã quiescent | P2/P4 |

Với mỗi ca phải lưu:

- Git HEAD/build/package, host/OS, contract version, thời điểm và fault được chèn.
- Target/action/context/grant identifiers đã loại secret; local receipt/Job/RUN/proof references.
- Expected/observed behavior, phân loại PASS/FAIL/INCONCLUSIVE và giới hạn coverage.
- Trạng thái cuối của canary workspace, active jobs và quyền điều khiển.

Không ghi credential, cookie, authorization header hoặc toàn bộ stdout có secret vào report. Không thay test bằng một model kết luận “đúng”.

Focused/unit proof và live proof là hai lớp khác nhau. Chỉ mở process/E2E/hardware test khi phase cần chính ranh giới đó và đã được phép; không chạy cả workspace test suite cho một thay đổi tài liệu.

## 16. Vận hành Ubuntu và lựa chọn độ phức tạp

### 16.1 Cấu hình khởi đầu để đánh giá

Đề xuất pilot: một backend, một DB trên local SSD, service supervisor, log có redaction, backup và health endpoint phân lớp. SQLite là ứng viên khi một application server quản lý DB local; khi xuất hiện nhiều writer/concurrency hoặc yêu cầu vận hành khác thì mới cân nhắc PostgreSQL. Không đặt SQLite trên network share dùng chung giữa PC. Nguồn: [SQLite — appropriate uses](https://www.sqlite.org/whentouse.html).

Mức 2–4 vCPU và 4–8 GB RAM trong tư vấn chỉ là **giả định sizing ban đầu**, chưa benchmark. Queue/log/artifact retention và model execution có thể làm nhu cầu khác đi. Control plane không chạy local model thì chưa có lý do yêu cầu GPU.

Chọn cách đóng gói sau khi xác định backend: service native hoặc container đều cần durable volume, credential management, backup và restart contract. Không coi Dockerfile Rust hiện tại là gói central Desktop gateway sẵn dùng.

### 16.2 Health và restart

Health phải tách:

1. Process liveness.
2. DB writable/durable admission.
3. Client ingress/tunnel hoạt động.
4. Node transport authenticated/fresh.
5. Local semantic tool plane/authority đủ điều kiện.

`systemd` hỗ trợ restart policy; watchdog chỉ có ý nghĩa khi ứng dụng thực sự đáp ứng giao thức watchdog. “Service active” không chứng minh DB nhận việc hoặc MCP tool gọi thành công. Nguồn: [Ubuntu systemd.service](https://manpages.ubuntu.com/manpages/noble/man5/systemd.service.5.html).

Đặt restart backoff và giới hạn để không tạo vòng crash vô tận hoặc lặp dispatch. Manual-stop/maintenance phải thắng auto-restart theo contract đã chọn.

### 16.3 Backup, restore và giới hạn 24/7

- Backup DB theo cơ chế snapshot nhất quán; backup cả cấu hình cần phục hồi nhưng quản lý secret riêng có mã hóa/quyền truy cập.
- Có retention, cảnh báo dung lượng, kiểm tra integrity và restore drill.
- Restore DB không khôi phục sự thật đã diễn ra trên PC sau snapshot: bắt buộc reconcile trước admission.
- Mất Ubuntu thì PC không tự mất file local; đường điều phối trung tâm không còn sẵn sàng. Inflight work tuân thủ quyền đã cấp; rollback/direct access phải theo mục 17.
- Một máy chủ có restart và backup chưa phải HA. UPS/điện/mạng/SSD và điểm lỗi đơn vẫn phải đưa vào đánh giá; chưa hứa SLA 99.9% hoặc uptime tuyệt đối. Nguồn tham khảo: [Ubuntu high availability](https://ubuntu.com/server/docs/explanation/high-availability/).

### 16.4 Quan sát và thông báo tối thiểu

Ưu tiên hiển thị actionable state: cần duyệt, node quay lại và việc đủ điều kiện, job lỗi, outcome chưa rõ, credential/DB/transport cần can thiệp. Không cần AI polling liên tục hoặc notification mỗi heartbeat.

MCP Tasks có thể là adapter cho job dài nếu hai phía hỗ trợ và thương lượng capability; không dùng extension này làm điều kiện bắt buộc cho core Job semantics. Nguồn: [MCP Tasks overview](https://modelcontextprotocol.io/extensions/tasks/overview).

Tài liệu này không tạo lịch chạy, automation hay thông báo thực tế. Tần suất, nơi nhận và quyền tự tiếp tục phải được giao riêng khi triển khai.

## 17. Rủi ro, rollback và tiêu chí dừng

### 17.1 Thứ tự ưu tiên rủi ro

Mức ưu tiên dưới đây là đánh giá thiết kế, không phải xác suất sự cố đã đo hoặc kết quả security scan.

| Ưu tiên | Rủi ro | Tác động | Cách xử lý bắt buộc |
|---|---|---|---|
| Chặn mở mutation | Nhầm device/workspace hoặc rò dữ liệu cross-user | Sửa/đọc nhầm file thật | Immutable binding, owner check, negative tests T01–T02/T22 |
| Chặn mở mutation | Retry sau effect nhưng mất ACK | Chạy lặp, dữ liệu sai | Durable action + local key + reconcile, T05–T09 |
| Chặn mở mutation | Hai controller cùng ghi | Ghi đè, proof/ledger không còn đáng tin | Local fence và handoff; T24 |
| Chặn mở mutation | Actor trung tâm vượt trust boundary | Mở đường điều khiển không được cấp quyền | Enrollment/delegation đúng audience; không giả client |
| Chặn cutover | Bỏ tunnel làm readiness sai | Node hiện xanh giả hoặc không usable | Transport-specific activation proof, T15–T17 |
| Chặn no-login | Profile/UI/account chưa sẵn sàng | WOL/boot xong nhưng tool không chạy | Account/toolchain/credential provision và hardware test |
| Chặn restore | DB trung tâm lùi thời gian | Dispatch lại effect đã hoàn tất | Admission off + reconcile trước mở lại |
| Chặn autonomy | Consent/budget/acceptance không rõ | Chạy vượt phạm vi hoặc báo xong giả | Bounded continuation, exact controller, outcome riêng |
| Cần theo dõi | Ubuntu là điểm lỗi đơn, disk/log tăng | Không nhận yêu cầu hoặc mất dữ liệu nếu backup kém | Capacity, alert, backup/restore drill; không hứa HA |
| Cần đo lợi ích | Thêm nhiều lớp hơn giá trị thực | Tăng bảo trì và thao tác vận hành | Pilot một vertical slice; KEEP/MODIFY/REMOVE theo số liệu |

### 17.2 Rollback đúng nghĩa

Chỉ đặt `central_routing_enabled=false` không đủ: request đang trên mạng hoặc controller cũ có thể còn quyền tại node.

Trình tự đề xuất:

1. Đóng admission mới ở trung tâm; báo rõ maintenance/rollback.
2. Ghi tập action đang queued, dispatch-unconfirmed, accepted và local handles liên quan.
3. Revoke/fence quyền central actor tại **node execution boundary** theo contract; giữ evidence của old generation.
4. Reconcile inflight effects và mutation jobs đã spawn. Revoke admission không dừng child process đang ghi: phải chờ terminal/quiescent hoặc controlled stop đúng contract/phạm vi được phép, rồi xác nhận không còn old writer trong scope sẽ handoff. Công việc chưa xác định giữ unresolved, không đánh dấu canceled cho đẹp.
5. Chỉ sau khi chứng minh admission cũ đã bị fence và mutation scope cũ đã quiescent mới handoff sang direct controller/runtime hiện hữu.
6. Kiểm tra direct context, exact workspace, activation và quyền hiện tại trước mutation tiếp.
7. Tiếp tục nhận late truthful receipts vào lịch sử nhưng từ chối late writes của quyền cũ.
8. Giữ DB, ledger, logs và changes đã tạo để audit; rollback điều phối không tự rollback nội dung file.

Nếu node chưa liên lạc được để xác nhận fencing, chưa được công bố “rollback hoàn tất”. Cần quan sát local authority khi node quay lại hoặc một thủ tục operator có bằng chứng tương đương. Đóng socket/gateway không chứng minh quyền đã cấp trên PC bị thu hồi tức thời.

Không broad-kill process, xóa ledger, reset worktree hoặc mở runtime writer thứ hai để làm rollback dễ hơn. Hủy/hoàn tác code đã sửa là thao tác riêng với exact target và quyền của người dùng.

### 17.3 Khi nào phải dừng phase?

Dừng mở rộng, ghi checkpoint và đề xuất bước đối soát khi có một trong các tình huống:

- Không xác định chắc target/owner hoặc phát hiện mutation sai scope.
- Effect có thể đã xảy ra nhưng không có bằng chứng đủ để retry/resume.
- Local authority/freshness không hợp lệ hoặc cần giả client/skip guard mới chạy được.
- Phát hiện secret trong log/evidence hoặc credential dùng sai audience.
- Không xác định được runtime/package thật để kiểm thử cutover.
- Người dùng chưa giao quyền cho thay đổi ngoại vi: deploy, restart, router, service account, paid model, push/release.

Không coi “PC vẫn offline” là lỗi cần tự chữa bằng hành động mở rộng. Đây có thể là trạng thái chờ bình thường; chỉ hành động trong wake/resume policy đã được giao.

## 18. Bằng chứng đã quan sát và giới hạn

### 18.1 Phân cấp bằng chứng

| Nhãn | Nghĩa trong tài liệu |
|---|---|
| `SOURCE_PRESENT` | Có implementation ở exact baseline; chưa chứng minh đường chạy live này hoạt động |
| `TEST_SOURCE_PRESENT` | Có test/harness liên quan; không khẳng định đã chạy test trong nghiên cứu |
| `OBSERVED_SNAPSHOT` | Kết quả đọc/snapshot tại thời điểm được ghi |
| `PROPOSED / PLANNED` | Thiết kế hoặc test sẽ làm; không phải capability hiện có |
| `NOT_VERIFIED` | Chưa có dữ liệu phù hợp; không thay bằng false/zero hoặc “đã hỗ trợ” |

Thứ tự ưu tiên: implementation/focused tests/live contract → [CURRENT_STATE](CURRENT_STATE.md) → maintained docs → subsystem docs → dated research. Không dùng một dòng trong bản tư vấn để phủ định guard đang có trong source.

Trong lượt nghiên cứu phục vụ kế hoạch này chưa có controlled Ubuntu ↔ Windows fleet activation, chưa chạy central mutation pilot, chưa kiểm tra no-login/WOL trên máy thật. Lượt viết Markdown không tạo thêm những bằng chứng đó.

### 18.2 Snapshot ledger local từ lượt nghiên cứu trước

Đã đọc bằng script census tại cùng HEAD baseline, sử dụng snapshot SQLite nhất quán; không chỉnh canonical ledger:

| Thuộc tính | Quan sát |
|---|---|
| Công cụ | [report_lifecycle_census.py](../resources/coding-tools-mcp/scripts/report_lifecycle_census.py), chế độ `--summary` |
| Workspace | `E:/Github/Tools-Codex-web` |
| Snapshot time | `2026-09-14T18:38:04.056Z` = `2026-09-15 01:38:04.056 +07:00` |
| Schema / bytes snapshot | 12 / 86,220,800 |
| SQLite integrity | `ok`; foreign-key check: 0 rows |
| Canonical ledger bị sửa bởi census | `false` |
| Ordinary active run records | 9 |
| Phân loại 9 records | 8 `THRESHOLD_SENSITIVE_STALE_CANDIDATE`; 1 `AWAITING_ACCEPTANCE` |
| P5 anchor records, tách riêng | 6 |
| Managed-job classification | 1 `STALE_MANAGED_JOB_RESIDUE` |
| Stale background / unbound live residues | 0 / 0 |
| Unexplained active runs / projection drift | 0 / `false` |

Snapshot SHA-256: `adddccc59484e0876f2ea6e148ddc5ea03b5f916c8af679a0cd8af2144103c7f`.

Logical SHA-256: `c024a6ca2c775cb90795abf3063fe8939aa2523347847ef1fd3d2b662db163e3`.

Diễn giải: có lịch sử lifecycle cần phân biệt với “job đang chạy thật”. Nhãn stale candidate là kết quả phân loại của census, không cho phép tự xóa/resume. `AWAITING_ACCEPTANCE` cũng không tự cấp quyền chấp nhận trong nghiên cứu này.

Đây là baseline snapshot cũ được tái sử dụng, không phải census chạy lại trong lượt ghi Markdown. Trước pilot phải kiểm tra đúng runtime/authority đang dùng, không đọc snapshot này để tuyên bố hệ thống hiện tại không còn active work.

### 18.3 Các projection phụ

| Nguồn | Quan sát tại lượt nghiên cứu | Giới hạn suy luận |
|---|---|---|
| `.coding-tools/performance.json` | Đọc lúc `2026-09-15T01:38:31.4329034+07:00`; 2 tool calls, 0 errors; last finished `2026-09-14T14:38:34.894Z`; route counts rỗng | Mẫu rất nhỏ, không phải throughput/độ ổn định toàn hệ thống hoặc hóa đơn provider |
| `.coding-tools/task-history.json` | 100 archived entries; mốc created đầu/cuối đã quan sát `2026-08-22T13:58:21.044Z` và `2026-08-24T06:18:45.021Z` | Cửa sổ lưu trữ này không thay cho canonical causal history hoặc kết quả fleet pilot |
| `.coding-tools/task-state.json` | Unscoped projection completed, updated `2026-09-09T12:23:33.868Z` | Không chứng minh tất cả run ở mọi scope đã completed |
| Canonical `.coding-tools/orchestration/ledger.sqlite3` | Census ở mục 18.2 | Ưu tiên khi suy luận causal history; vẫn cần phân biệt persisted record với live process |

Không có cơ sở để tính tiết kiệm token, ROI, MTBF, TTAR cải thiện hoặc phí model từ các quan sát này. Internal credit estimates không phải provider billing.

### 18.4 Bằng chứng còn thiếu

- Cấu hình và trạng thái thực của Ubuntu, mạng LAN/Internet/VPN, quyền ingress.
- Số PC, OS/version/package, sleep/boot/account và toolchain thật.
- Host/client dùng connector trung tâm, đặc biệt mobile approval/discovery.
- Central gateway/schema/actor admission đã implement và focused tests.
- Live canary lost-ACK/restart/rollback và soak đúng môi trường.
- Source/data snapshot và proof riêng nếu chọn execution trên Ubuntu.
- Quyền/chi phí và điều kiện acceptance cho controller AI dài hạn.

Những mục thiếu không ngăn hoàn thành tài liệu thiết kế; chúng ngăn tuyên bố đã sẵn sàng triển khai hoặc vận hành production.

## 19. Đo hiệu quả để quyết định có nên mở rộng

### 19.1 Không dùng một chỉ số “24/7 success”

Tách thời gian:

1. Client gửi → trung tâm xác nhận lưu bền vững.
2. Chờ node/readiness/approval.
3. Dispatch → node admit/handle.
4. Thực thi và proof.
5. Technical acceptance.
6. Người dùng xác nhận outcome nếu task cần bước này.

Nếu gộp cả thời gian PC tắt vào model latency thì kết luận tối ưu sai. Nếu chỉ đo gateway trả 200 thì bỏ qua hiệu quả thực thi.

### 19.2 Bộ đo tối thiểu của pilot

| Nhóm | Chỉ số | Quy tắc ghi |
|---|---|---|
| Đúng đích | Sai node/workspace, cross-context access | Yêu cầu 0 trong tập ca đã chạy; không suy ra an toàn tuyệt đối ngoài coverage |
| Giao nhận | Durable acceptance, duplicate effects, unresolved actions | Đếm theo logical action, tách delivery attempts |
| Phục hồi | Restart/reconnect → reconcile xong; số lần can thiệp tay | Ghi từng fault và điều kiện ban đầu |
| Khả dụng | Ingress, DB admission, node ready, execution success | Bốn mẫu số riêng, không lấy tunnel uptime thay tool uptime |
| Vận hành | Số connector cần cấu hình, số lần repair/refresh/handoff thủ công | So với direct baseline trên task tương đương |
| Outcome | Task được nghiệm thu, reopen/rework, yêu cầu còn chờ người dùng | Không lấy test count làm số task thành công |
| Chi phí | Usage provider-reported nếu có, tài nguyên server, công vận hành | Thiếu dữ liệu ghi unknown; không suy từ credit estimate |

Đề xuất một vòng canary ổn định rồi soak 24 giờ có chủ đích ngắt mạng/restart và một số task tự nhiên đại diện. “24 giờ” là mục tiêu thử nghiệm ban đầu để duyệt, không phải số liệu đã đo hay chứng minh SLA.

Kết thúc pilot đưa ra một quyết định:

- KEEP: giảm được thao tác tay, giữ đúng authority và recovery có bằng chứng.
- MODIFY: có giá trị nhưng một boundary cụ thể chưa đạt; sửa đúng boundary đó.
- DEFER/REMOVE: chi phí vận hành cao hơn lợi ích hoặc nhu cầu chưa cần thành phần đó.

Không ước lượng thời gian/chi phí triển khai bằng con số chính xác trước P0. Có thể lập estimate theo từng gói CP-1…CP-8 sau khi rõ reuse, mạng và lifecycle cần hỗ trợ.

## 20. Những quyết định cần người dùng kiểm tra

Tất cả lựa chọn bên dưới **chưa được xác nhận**. Đề xuất trong cột giữa là phương án để duyệt, không phải consent hoặc cấu hình đã áp dụng.

| ID | Đề xuất khởi đầu | Cần bạn xác nhận/điều chỉnh |
|---|---|---|
| D1 — Phạm vi | Một chủ sở hữu, một Ubuntu, một Windows canary | Có bao nhiêu người và bao nhiêu PC sẽ dùng? |
| D2 — Kết quả phiên bản đầu | Nhận yêu cầu 24/7 + đúng node + offline queue; chưa AI tự chạy vô hạn | Bạn cần server giữ yêu cầu hay phải tự tiếp tục suy luận khi rời chat? |
| D3 — Windows lifecycle | Pilot khi Windows đã đăng nhập; giữ direct tunnel | Có bắt buộc chạy sau mất điện/boot mà không đăng nhập không? |
| D4 — Mạng | LAN/private connectivity trước, không expose PC | Ubuntu và PC ở cùng LAN hay nhiều nơi? Đã có domain/VPN chưa? |
| D5 — Dữ liệu | File local giữ trên đúng PC; artifact relay có giới hạn | Có cho gửi code/log/ảnh ra server/model không, và giữ bao lâu? |
| D6 — Quyền | Read-only trước; một mutation canary có phạm vi sau | Root/file nào được phép, hành động nào phải luôn hỏi? |
| D7 — Controller | Giữ local/ChatWeb authority hiện có, không auto-handoff | Có muốn giao một controller Ubuntu điều khiển run không? |
| D8 — Ngân sách | Chưa bật model automation/provider mới | Nếu chọn C: giới hạn tiền/token/thời gian và điều kiện dừng là gì? |
| D9 — WOL | Tùy chọn sau khi rõ lifecycle | Máy/NIC/trạng thái nguồn nào cần hỗ trợ; có relay cùng LAN không? |
| D10 — Ubuntu execution | Chỉ workspace riêng, commit-pinned, handoff rõ | Có task Linux phù hợp không; dữ liệu chưa commit xử lý ra sao? |
| D11 — Backend/DB | Một backend + DB local; tránh nhiều service | Ưu tiên tái dùng Rust hay stack khác sau compatibility spike? |
| D12 — Client | Một client cụ thể để pilot trước | Dùng ChatGPT web, Desktop, điện thoại hay giao diện riêng làm chính? |

Checklist review:

- [ ] Đồng ý cách hiểu “giữ nguyên Windows” ở mục 1.1.
- [ ] Đồng ý không tạo Goal/authority canonical thứ hai ở Ubuntu.
- [ ] Đồng ý durable dispatch là điều kiện trước mutation đầu tiên.
- [ ] Đồng ý tách primary transport cutover và boot without login.
- [ ] Chọn các nhánh C/W/U thực sự cần, không mặc định làm tất cả.
- [ ] Chốt target canary và phạm vi của P0; giao triển khai bằng yêu cầu riêng.

Khuyến nghị quyết định lúc này: duyệt kiến trúc và phạm vi P0/P1 trước. Chỉ sau baseline/contract/read-only proof mới giao mutation pilot. Không cần quyết định toàn bộ HA, RBAC và AI controller để bắt đầu kiểm chứng giá trị của một đầu mối trung tâm.

## 21. Chỉ mục đối chiếu và trạng thái bàn giao

### 21.1 Mã nguồn và tài liệu nền

Các vị trí dòng là mốc tham khảo ở exact HEAD baseline; khi source thay đổi cần tìm lại symbol/contract, không coi số dòng là API cố định.

| Nội dung | Nguồn/vị trí tham khảo |
|---|---|
| Product boundary và tám tool | [CURRENT_STATE](CURRENT_STATE.md), mục 2–3; [ROADMAP](ROADMAP.md), convergence/current policy |
| Tư vấn đầu vào | [Bản phương pháp luận 15/09](research/260915_UBUNTU_24X7_CODEX_WEB_CONTROL_PLANE_METHODOLOGY_PLAN.md); bản pasted-text do người dùng cung cấp, không nhập lại nguyên văn |
| Tool context/schema | [tool_schema.py](../resources/coding-tools-mcp/coding_tools_mcp/tool_schema.py), dòng 16–46 và vùng `workspace_context` |
| Workspace switch/context/idempotency | [server.py](../resources/coding-tools-mcp/coding_tools_mcp/server.py), vùng 666, 919, 1134, 1796 và caller/fence scope |
| Request-local context, không phải authority | [mcp_http_handler.py](../resources/coding-tools-mcp/coding_tools_mcp/mcp_http_handler.py), vùng 1163–1179 |
| Endpoint projection/freshness | [endpoint_identity.py](../resources/coding-tools-mcp/coding_tools_mcp/endpoint_identity.py), vùng 69, 113, 150 |
| Local proxy và attestation | [hubProxyGateway.js](../electron/services/hubProxyGateway.js), vùng 128, 286, 300; [connectorAttestation.js](../electron/services/connectorAttestation.js) |
| Runtime readiness/stop | [runtimeOrchestrator.js](../electron/services/runtimeOrchestrator.js), vùng 2332, 2495, 2863 |
| Activation cần tunnel/UI | [fullCleanActivation.js](../electron/services/fullCleanActivation.js), vùng 2280, 2335, 2389, 2461 |
| AtLogOn supervisor | [recovery-supervisor.ps1](../resources/recovery-supervisor/recovery-supervisor.ps1), vùng 140 |
| Continuation/acceptance/restart | [continuation_contract.py](../resources/coding-tools-mcp/coding_tools_mcp/continuation_contract.py), vùng 482–549; [continuation_driver.py](../resources/coding-tools-mcp/coding_tools_mcp/continuation_driver.py), vùng 1111 trở đi |
| Rust remote transport/reconciliation | [runner transport](../crates/webcodex-runner/src/webcodex_runner/transport.rs); [shell-client reconciliation](../src/shell_client/reconciliation.rs); [ARCHITECTURE](ARCHITECTURE.md) |
| Runtime evidence census | [report_lifecycle_census.py](../resources/coding-tools-mcp/scripts/report_lifecycle_census.py); snapshot ở mục 18 |

Nguồn web chính thức được dẫn ngay tại các nhận định tương ứng ở mục 4, 9–12 và 16; được đối chiếu trong đợt nghiên cứu ngày 15/09/2026. Chúng hỗ trợ thiết kế/giới hạn của nền tảng, không phải bằng chứng repo này đã tích hợp thành công.

### 21.2 Trạng thái để duyệt

- Hoàn thành trong phạm vi tài liệu: tổng hợp tư vấn, đối chiếu source, kiến trúc đề xuất, vấn đề cần sửa, phase/exit gate, test matrix, rollback, evidence limitations và bảng quyết định.
- Chưa triển khai: gateway, node adapter mới, facade/schema mới, central DB/queue, remote approval, lifecycle cutover và các nhánh C/W/U.
- Không nâng mức bằng chứng: source/test hiện hữu không được gắn nhãn central fleet live pass; snapshot lịch sử không bị viết lại.
- Không thay chính sách routing/authority và không tác động service/tunnel/provider/Git delivery.
- Bước tiếp theo sau khi bạn kiểm tra: xác nhận D1–D4, D6, D12 và giao P0/P1 với đích cụ thể; các quyết định còn lại chốt trước nhánh tương ứng.

Tóm lại: **Ubuntu nên giữ đầu mối và ý định công việc; node giữ file và quyền thực thi; controller hợp lệ giữ quyết định tiếp tục/nghiệm thu.** Giá trị cần chứng minh trước là nhận việc ổn định, đúng máy, không lặp effect và phục hồi rõ ràng — sau đó mới mở rộng sang chạy tự động dài hạn.
