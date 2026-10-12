# Vận hành Coding Tools MCP từ web

## Trạng thái áp dụng

Ngày 11-10-2026: mã nguồn sửa feedback/status có focused proof; revision
`beaa9d5ade4926ef231e3ec9d0a517fe93830e90` đã được triển khai lên
`svhome@100.116.112.22` và restart user service `codex-control-plane.service`
lúc 15:24:40 +07. Live revision/fingerprint và verifier 38 file khớp nhau.
Sau khi owner reboot lúc 15:42:38.500 +07, Windows candidate unpacked 1.0.7
`exec-coldstart-1011-r5` đã được kích hoạt cho profile `web-mcp-assistant`.
Lúc 16:16:02 +07, epoch
`activation-mv3lxw05-c20b330cb58f3edea4f421b9a65b0743` là READY, admission mở,
`updateIncomplete=false`; local/component/central/authority readiness đều đạt.
Đây là rollout có phạm vi kiểm soát, chưa là public release.
Primary repository giữ dirty `main @ 2c554f59`, HEAD/index không đổi.

Binding `bind_3e05bf64cb3e4bab93d930ae1692bebb` giữ đúng workspace
`E:/Github/Tools-Codex-web`. Context/pilot được gia hạn đúng 60 phút, từ
15:26:24.008 đến **16:26:24.008 +07 ngày 11-10-2026**; admission là
`scoped_pilot`. Policy metadata Windows khớp hạn này và standing policy đọc/sửa
đã cài. Sandbox probe và exec policy đúng workspace cũng đã đạt sau reboot.
Khi hết hạn context/pilot, cần quyền owner mới trước khi gia hạn.

Discovery trực tiếp lúc 14:52 +07 quan sát facade schema 32, profile
`control-plane-private-tunnel-service-v1`. Hash phải lấy lại từ đúng phiên/server
đang dùng. Giá trị `profile: "workspace_context"` và hash bắt đầu `bc44c044` trong
yêu cầu bị lỗi là pin sai: tên tool và `targets[].contract_version` của node
không phải contract của facade.

[Receipt live mới](../.coding-tools/reports/mcp-web-contract-20261011/live-rollout-verification.jsonl)
xác nhận target online/ready/dispatchable, policy enabled và lỗi pin sai trả
`CONTRACT_MISMATCH` có `isError=true` thay vì JSON-RPC `Invalid params`.
Hai lần đọc có receipt và hash khớp: fixture 49 bytes và 40 dòng đầu mã nguồn
`control-plane/control_plane/mcp_facade.py` (1.366 bytes). Diagnostic của patch
lịch sử được trả an toàn, action không bị replay. Đây là bằng chứng qua API
MCP Ubuntu xác thực; acceptance trên client ChatGPT thật và write mới vẫn
chưa được chứng minh. Lần exec r5 mới đã hoàn tất lúc 16:16:56: chạy
`node --test tests/control-plane-approved-patch-runtime.test.js` qua Windows
Sandbox, **4 PASS / 0 FAIL**, exit code 0, một attempt và receipt
`completed/settled`. Task/writer đã đóng; Ubuntu quan sát lúc 16:17:36 có
zero queued/accepted actions và zero open tasks/writers. Xem
[receipt chạy test](../.coding-tools/reports/mcp-web-contract-20261011/postreboot-exec-r5-verification.jsonl).

## Thiết lập xuyên suốt trong mã nguồn mới

Luồng dưới đây đã có trong source, chưa được kích hoạt trên profile đang dùng.
Bản Windows có live proof gần nhất vẫn là r5 mô tả ở trên. Các mốc quyền đã ghi
không tự gia hạn khi UI được thay đổi.

1. App Desktop mở một cửa sổ chính. Trong **Cài đặt**, đi theo ba phần liền nhau:
   **Máy chủ & máy này → Thư mục & quyền → Kiểm tra thực thi**. Bảng **Thực thi
   mã** và **Tác vụ & kết quả** nằm trong cùng cửa sổ.
2. Kết nối máy tới Ubuntu; owner vẫn duyệt identity máy. Chọn thư mục local và
   mức Đọc/Sửa/Chạy. App chỉ gửi định danh đăng ký, không gửi đường dẫn local tới
   Ubuntu. Đổi mức quyền của đăng ký hiện có vẫn cần xác nhận generation mới.
3. Bấm **Hoàn tất thiết lập** và xác nhận đúng máy, thư mục cùng mức quyền. App
   kiểm tra quyền Ubuntu mỗi 15 giây, tối đa 10 phút. Khi đúng target đã được
   cấp, app đồng bộ metadata và dùng các API policy đọc/sửa/chạy hiện có cho
   những bước còn thiếu. Quyền Chạy vẫn cần sandbox sẵn sàng.
4. Owner dùng form thư mục gộp trên Console để chọn đúng máy/workspace, dùng lại
   hoặc tạo binding và cấp một context có hạn. Form không tạo grant/pilot hoặc
   mở admission. Với private tunnel service, owner còn phải hoàn tất service
   grant, pilot đúng target và admission qua quy trình operator được bảo vệ.
5. Có thể dừng tiếp tục hoặc đổi lựa chọn để ngăn các bước tiếp theo. Thao tác
   đã gửi vẫn cần đối soát kết quả. Thoát hẳn app chỉ giữ bản nháp định danh
   workspace; mở lại phải xác nhận tiếp tục. Nút đóng cửa sổ khi app chạy nền
   vẫn giữ lượt chờ đang còn hạn.

UI mới không cấp quyền tự động và không bỏ gate xác thực, policy, sandbox hay
receipt. Checklist đọc/sửa/chạy xác nhận policy tương ứng; chỉ receipt lệnh
settled, exit code và output mới chứng minh test thực tế. Chọn folder cũng không
đổi workspace của tác vụ đang có. Sau rollout được duyệt, kiểm chứng từ client
ChatGPT bằng các bước dưới đây và giữ nguyên quy tắc xử lý UNKNOWN.

## Quy trình đọc file

1. Gọi `workspace_context` với `{"operation":"inventory"}`. Chọn chính xác
   `binding_id` của workspace được giao; không dùng tên hiển thị làm target.
2. Sao chép nguyên object `structuredContent.tool_contract` gồm
   `schema_version`, `profile`, `sha256` vào `expected_facade_contract`.
   Nếu bản server cũ chưa trả trường này, lấy object
   `_meta.control_plane.tool_contract` từ discovery; không tự đoán giá trị.
3. Khi cần giữ task cho nhiều thao tác, gọi `workspace_context task_open` với
   `binding_id`, `label`, `idempotency_key`. Lưu `task.task_id`. Đọc một file có
   thể bỏ `task_id`; `task_open` không nhận `expected_facade_contract`.
4. Gọi `workspace_context read_file` với các trường dưới đây. Các trường tùy
   chọn chưa dùng phải được bỏ khỏi object, không điền `null`.
5. Khi nhận `action_id`, gọi `workspace_context` với
   `{"operation":"read_status","action_id":"<action_id đã nhận>"}`.
   Chỉ coi file đã đọc khi có receipt được xác minh và `file_accessed=true`.
6. Nếu tiếp tục sửa/chạy lệnh, dùng task và writer theo phần kế tiếp. Kết thúc
   công việc bằng `workspace_context task_close` với đúng `task_id`.

Ví dụ chuẩn bị arguments sau khi đã nhận kết quả inventory; đây là object
JavaScript, `contract` phải là object thật từ response:

```javascript
const contract = inventory.structuredContent.tool_contract;
const argumentsForRead = {
  operation: "read_file",
  binding_id: selectedTarget.binding_id,
  path: "control-plane/control_plane/mcp_facade.py",
  idempotency_key: "read-facade-001",
  expected_facade_contract: contract,
  start_line: 1,
  max_lines: 40,
  max_bytes: 8192
};
// Nếu đã task_open: argumentsForRead.task_id = task.task_id;
```

Root hiện tại là `E:/Github/Tools-Codex-web`. `path` tính từ root này, dùng `/`;
đường dẫn source đúng là `control-plane/control_plane/mcp_facade.py`.
`control_plane/mcp_facade.py` thiếu thư mục cha. Không gửi đường dẫn tuyệt đối
`E:/DEV/...`, `E:/Github/...`, dấu `\` hay thành phần `..`. Policy cục bộ vẫn
quyết định file nào được phép đọc.

Retry một ý định phải giữ **cùng key và toàn bộ arguments**. Đổi đường dẫn,
contract, bounds hoặc task là ý định mới; không dùng lại key cũ cho nó. Nếu
response đã có action, theo dõi action đó trước khi tạo thao tác thay thế.

## Task, writer và nghiệm thu

- `task_control task_observe` quan sát task đã cấp, không đổi target.
- Trước mutation, `task_control writer_claim` với `task_id`; sau khi hoàn tất
  hoặc bàn giao, `writer_release` với cùng task và lý do. Lease chỉ tuần tự hóa
  tác vụ; policy Windows và quyền của service vẫn phải cho phép thao tác.
- Standing write dùng policy workspace đã cài. Luồng owner-reviewed patch cần
  scope đã được duyệt. Dùng đúng schema đang discovery cho `agent_workflow`;
  đọc lại file và đối chiếu hash trước khi nghiệm thu.
- `workspace_context task_close` đóng task, giữ lịch sử. Đóng task hoặc verdict
  trên Console không chứng minh đã hoàn tất proof/acceptance trong Coding MCP.

Central verdict hiện chưa có adapter hoàn tất semantic acceptance cục bộ. Wave
đang chờ acceptance vẫn phải được controller hợp lệ xử lý với proof đúng;
không sửa ledger hoặc tạo proof giả để đóng nó.

Rollout r4 chưa chạy patch live mới: lane exact-file không tạo/xóa fixture dùng
thử, và mỗi lượt sửa/hoàn nguyên đều tạo wave ACCEPTING cục bộ. Khi chưa có
adapter nghiệm thu từ central sang local, giữ hàng đợi pending hiện có.
Standing write policy đã bật và source có focused proof; hai điều này chưa
chứng minh một write roundtrip mới qua r4.

### Patch từng bị từ chối đã được đối chiếu

Action `act_16f5443e532942019fa7bb43868b34b0` thất bại trước hiệu ứng ghi:
Coding MCP từ chối `arguments.include_diff` vì trường này không thuộc schema.
Background operation `HAt4M_RQNok1GYYb` đã terminalize; tại lần thất bại,
fixture vẫn có SHA-256 `742976da6d38a49f35c48b5824eea2badc1e98258dd74d8c34720f08f09a14cb`.
Bridge đã bỏ trường sai và có test đối chiếu với validator thật.

[Bằng chứng trước hiệu ứng](../.coding-tools/reports/folder-permissions-20261011/pre-effect-rejection.json)
và [receipt reconciliation](../.coding-tools/reports/folder-permissions-20261011/terminal-reconciliation-receipt.json)
ghi server receipt `rejected`, delivery `settled`, `replayed=false`; journal ban
đầu được giữ nguyên. Không retry action này. Đây là kết luận dựa trên evidence
của action cụ thể, không phải quy tắc coi mọi `unknown` là chưa ghi file.

## Quy trình chạy test

1. Lấy inventory mới, chọn đúng binding của `Tools-Codex-web` và giữ nguyên
   `tool_contract`. Kiểm tra target online/ready và policy enabled.
2. Mở task bằng `workspace_context task_open`, lưu `task.task_id`, rồi gọi
   `task_control writer_claim` cho task đó.
3. Gọi `exec_command exec_run` với structured argv và một idempotency key mới
   cho ý định chạy này. Ví dụ sau dùng các object vừa nhận từ bước 1–2:

   ```javascript
   const argumentsForTest = {
     operation: "exec_run",
     binding_id: selectedTarget.binding_id,
     task_id: task.task_id,
     argv: ["node", "--test", "tests/control-plane-approved-patch-runtime.test.js"],
     cwd: "",
     timeout_ms: 300000,
     max_output_bytes: 32768,
     idempotency_key: "workspace-patch-runtime-test-001",
     expected_facade_contract: inventory.structuredContent.tool_contract
   };
   ```

4. Quan sát cùng `action_id` bằng `exec_command exec_status`; duy trì writer
   bằng `writer_claim` khoảng mỗi 25 giây khi chờ. Cold Sandbox có thể mất vài
   phút trước khi trả Job; r5 đã sửa timeout của lượt khởi động này.
5. Khi completed/settled, lấy `command_control exec_output` và kiểm tra exit
   code cùng kết quả test. Nếu UNKNOWN, đối soát đúng action/job trước khi
   quyết định bước tiếp theo; không enqueue bản thay thế.
6. Khi action đã terminal và settled, gọi `task_control writer_release`, rồi
   `workspace_context task_close`. Một bài test đạt không chứng minh toàn bộ
   suite đạt; tiếp tục chọn đúng lane trong [TESTING](TESTING.md).

## Phân biệt khả năng và quyền thực thi

| Quan sát | Chứng minh được |
| --- | --- |
| `targets[].capabilities.read/write/exec=true` | Khả năng workspace đã đăng ký |
| Metadata policy/heartbeat, node `online`, readiness `ready` | Kết nối và quan sát runtime tại thời điểm đó |
| `relay_capabilities[tool].relay_enabled=true` | Server công bố operation của relay |
| `relay_capabilities[tool].local_admission="unverified"` | Chưa xác minh admission của thao tác cục bộ |
| Receipt hoàn tất được xác minh, readback/hash hoặc exit/output | Kết quả thao tác cụ thể |

`relay_enabled=true` không phải bằng chứng lệnh đã được phép chạy. Đọc
`implemented_operations`, `capability_state`, `execution` của đúng tool; nếu
client báo relay unavailable trong khi discovery mới có operation, làm mới
discovery/phiên connector rồi kiểm tra lại. Inventory không tự cấp thêm quyền.

## Đọc lỗi và phục hồi

Trong **revision Ubuntu đã triển khai**, lỗi validation/domain của tool được nhận diện có
`result.isError=true`; xem `structuredContent.code`, `message`, `validation`
(`missing_fields`, `unexpected_fields`, `invalid_fields`) và `next_action`.
Tên trường tùy ý được che thành `<unknown>`; giá trị lỗi không được phản chiếu.
Malformed protocol, tool không tồn tại hoặc arguments không phải object vẫn
là lỗi JSON-RPC. Server cũ có thể chỉ hiện `Invalid params` cùng `error.data`.

| Mã/trạng thái | Thao tác tiếp theo |
| --- | --- |
| `CONTRACT_MISMATCH` | Xem `mismatch_fields`; lấy lại inventory/discovery và dùng nguyên `expected_facade_contract` mà lỗi trả về |
| `VALIDATION_ERROR` | Sửa trường được chỉ ra; không lồng `bounds`, không thêm trường của operation khác |
| `FORBIDDEN` / policy expired | Kiểm tra đúng binding, scope và policy; chỉ gia hạn theo quyền owner đã cấp |
| `CONFLICT` | Quan sát task/action và writer đang có; không tạo thao tác cạnh tranh |
| `local_*_rejected`, `expired`, `local_failure` | Đọc mã lý do terminal trong status; xử lý nguyên nhân trước ý định mới |
| `unknown` | Giữ action/journal, kiểm tra hiệu ứng thực tế và reconcile bằng luồng được hỗ trợ; không tự replay |
| `queued_for_local_admission` hoặc receipt chưa terminal | Tiếp tục quan sát cùng action; chưa coi là thành công |

## Bảy nhóm công việc và gate còn lại

| Nhóm | Bằng chứng source/test hiện có | Gate còn lại |
| --- | --- | --- |
| Exec & local admission | Sandbox probe, policy và [test live r5](../.coding-tools/reports/mcp-web-contract-20261011/postreboot-exec-r5-verification.jsonl) đạt: 4 PASS, exit 0, settled | Tiếp tục kiểm tra đúng scope/hạn quyền; chưa chạy toàn bộ suite hoặc nghiệm thu client ChatGPT |
| Patch & lỗi | [Runtime patch tests](../tests/control-plane-approved-patch-runtime.test.js) kiểm tra schema thật; diagnostic rejection terminal lịch sử đã xác minh live | Write roundtrip mới và local semantic acceptance adapter còn thiếu |
| API/schema | [Feedback tests](../control-plane/tests/test_mcp_client_feedback.py), [file-read](../control-plane/tests/test_mcp_file_read_facade.py); contract mismatch và hai receipt đọc mới đã xác minh live | Làm mới discovery và nghiệm thu trên client ChatGPT thật; chưa có operation liệt kê thư mục |
| Task/writer | [Task session tests](../control-plane/tests/test_mcp_task_sessions.py), [OAuth HTTP](../control-plane/tests/test_mcp_oauth.py) kiểm tra lease và target | Controller nghiệm thu wave pending bằng proof hợp lệ |
| Permission/security | [Permission tests](../control-plane/tests/test_mcp_permission_requests.py), [private service](../control-plane/tests/test_mcp_private_tunnel_service_facade.py), path và scope guards | Xác minh đúng policy/scope/hạn authority cho từng thao tác live |
| Recovery/monitoring | [Recovery runbook](CONTROL_PLANE_RECOVERY_RUNBOOK.md), receipt/journal/idempotency; backup và preservation qua deploy verified; r5 READY, agent heartbeat đạt | 13 action lịch sử chưa giải quyết được giữ, không replay; UNKNOWN cần reconciliation; observation READY có thời điểm, cần kiểm tra lại khi thực hiện việc mới |
| Document/image | [Artifact relay](../control-plane/tests/test_mcp_artifact_relay.py), [node artifacts](../control-plane/tests/test_artifact_node_agent.py), [document writes](../control-plane/tests/test_document_write_node_agent.py); cap/expiry, reparse và thay đổi file có focused proof; r5 đã READY | Kiểm thử live trong scope đã cấp; một ca symlink thật bị skip do quyền Windows, ca thuộc tính reparse đạt |

Các đường dẫn feedback, file-read, status, writer và artifact đã đạt 88 focused
checks, một ca symlink thật SKIP do quyền Windows. Packaged smoke r4 đạt sau
một retry không thay mã của lỗi startup timeout; evidence lần đầu vẫn giữ.
HTTP exec real-process chưa chạy. `WINDOWS_WORKSPACE_REALPATH_EPERM` lịch sử
đến từ ProcessContainer fallback; host probe hiện đạt, nên chưa thể quy lỗi
cho quyền truy cập ổ E của host. Không restart Windows tự động.

Receipt r5 chứng minh bài test exec live nêu trên, chưa chứng minh production readiness. Phải
phân biệt source có test, packaged smoke, launch, READY, triển khai server và
receipt thao tác. Local RUN `95e909f0040a448faa9f1f3257e2ee2c` vẫn chờ semantic
acceptance. Trạng thái rollout/gate mới nhất được ghi tại
[CURRENT_STATE](CURRENT_STATE.md) và
[receipt Ubuntu](../.coding-tools/reports/mcp-web-contract-20261011/ubuntu-rollout-checkpoint.md).
