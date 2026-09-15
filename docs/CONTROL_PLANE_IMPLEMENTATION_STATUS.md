# Trạng thái triển khai Ubuntu Control Plane

**Cập nhật:** 15-09-2026 (Asia/Ho_Chi_Minh)  
**Trạng thái:** Pilot có kiểm soát — chưa đủ bằng chứng để gọi là production hoặc autonomous execution.

Tài liệu này là trạng thái vận hành hiện thời. Các tài liệu trong `docs/research/` là chronology/evidence tại thời điểm viết và không bị sửa để làm chúng trông như trạng thái hiện tại.

## Phạm vi đã triển khai và đã kiểm chứng

| Lớp | Trạng thái | Bằng chứng mạnh nhất |
| --- | --- | --- |
| Ubuntu control plane | Đang chạy | User service `codex-control-plane.service` active/enabled tại `/home/svhome/DEV/Codex-web`; SQLite `integrity_check=ok`. |
| Khả dụng qua đăng xuất Ubuntu | Đã cấu hình | `loginctl show-user svhome -p Linger` trả `Linger=yes`; đây chưa thay thế bài reboot acceptance. |
| Ingress mạng | Chỉ Tailnet/private | Dịch vụ bind IP Tailnet của Ubuntu trên cổng 8765; truy cập từ PC Windows tới `/healthz` đã thành công. Không công bố Internet. |
| Server identity/operator auth | Đã triển khai | Operator token chỉ ở file mode 600 ngoài repository. Endpoint operator dùng Bearer; endpoint node dùng node secret hash-verified. Không ghi payload hoặc Authorization vào log HTTP. |
| Node enrollment | Đã kiểm chứng | PC Windows tạo secret cục bộ, gửi hash để chờ duyệt; Ubuntu duyệt request; heartbeat node sau đó được xác thực với readiness `unknown`. Secret không đi qua operator response hay Git. |
| Runtime Windows | Degraded, không ready | One-shot adapter đã publish trạng thái hiện hành: Electron/MCP/tunnel và revision khớp, nhưng activation epoch vẫn `VERIFYING`, admission đóng vì chưa có current-process connector discovery. |
| Remote execution | Chưa mở, theo chủ đích | Chưa tạo workspace binding/context/work request/action. Server không gọi shell, không thay local MCP writer và không tự failover sang server. |

## Thành phần source mới

`control-plane/` là control plane Python chuẩn thư viện, SQLite-backed:

- Registry node, enrollment hai bước, binding/context/request/action/receipt/event bền vững.
- Chỉ cho phép đúng tám tool public của `smart-v3`.
- Action gắn target/binding/context/workspace generation/tool/arguments/idempotency/admission/expiry bằng digest bất biến.
- Poll ghi `dispatch_unconfirmed` trước khi trả action; node phải dedupe local và gửi receipt. Timeout không được diễn giải là retry mutation an toàn.
- `node_agent.py` hiện chỉ enrol/heartbeat/poll; poll không thực thi action.

Template systemd tại `deploy/codex-control-plane.service.example`; config thật và SQLite runtime nằm ngoài Git dưới home của tài khoản Ubuntu.

## Proof đã chạy

- Local: `python -W error -B -m unittest discover -s control-plane/tests -v` — 8 test pass, bao gồm negative operator authorization, two-step enrollment và runtime-heartbeat fail-closed.
- Ubuntu: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=control-plane python3 -W error -B -m unittest discover -s control-plane/tests -v` — 8/8 tests pass; health endpoint trả SQLite `ok`.
- Local: `git diff --check` pass.
- Windows: `npm run dev:refresh` khởi động MCP và tunnel với revision hiện tại; `npm run dev:status` xác nhận runtime telemetry hiện diện nhưng `fully_ready=false`.

## Chặn hiện tại — fail closed, không phải lỗi được bỏ qua

Control plane không được phép coi node ready chỉ vì tiến trình đang chạy. Execution Hub từ chối mở admission vì connector contract chỉ ở `UNCHANGED_ACKNOWLEDGED`, thiếu receipt `tools/list` gắn với process/activation epoch hiện tại. Lệnh acknowledgement chính thức trả `CONNECTOR_CONTRACT_NOT_REDISCOVERED`.

Điều cần xảy ra trước canary dispatch đầu tiên:

1. Kết nối/reconnect ChatGPT/Coding Tools MCP với Execution Hub Windows mới khởi động để có một `tools/list` current-process discovery.
2. Chạy lại full-clean/refresh theo lifecycle hiện hữu và xác nhận `fully_ready=true`, admission mở, connector freshness là current-process discovery.
3. Lấy workspace identity và generation từ runtime live, rồi mới tạo binding ở Ubuntu. Không tính SHA suy đoán hay trạng thái cache làm binding proof.
4. Chỉ sau đó chạy một action read-only `workspace_context`; đối chiếu receipt với đúng action và device. Mutation vẫn phải giữ authority, permission và acceptance cục bộ.

## Quyết định kiến trúc đã chốt

- Ubuntu là durable registry/queue/audit plane; Windows Execution Hub + Coding Tools MCP vẫn là execution writer và proof authority.
- Không thay tunnel hiện hữu chỉ bằng việc đổi địa chỉ server. Central link là capability phụ, không phải bypass readiness/connector/permission.
- Không auto-route model. `execution_route=auto` vẫn fail-closed deterministic.
- Không khởi động service Windows “khi chưa đăng nhập” trong pilot này. Electron, user secrets và interactive connector hiện session-bound. Nếu yêu cầu availability sau logoff/reboot Windows, phải có một workstream riêng: identity/secret store phi tương tác, Windows Service hoặc scheduled task được thiết kế lại, user-consent/TLS/rollback và reboot proof. Không được dùng auto-login như biện pháp mặc định.

## Rủi ro và việc còn lại

- Ingress hiện được bảo vệ bởi Tailnet + auth, chưa có TLS/mTLS layer ứng dụng hoặc public reverse proxy. Giữ private cho đến khi có mô hình chứng chỉ/rotation/revocation và test negative tương ứng.
- Có one-shot Windows runtime-heartbeat adapter đọc `dev-ui-lifecycle.js status` và publish state fail-closed. Chưa tạo scheduler/background service; heartbeat sau logon và runtime headless là hai capability khác nhau.
- Cấu hình hiện tại của Electron là `startWithWindows=false`, `autoStartServices=false`. Nếu bật `startWithWindows`, nó chỉ khởi động lại Recovery Host **sau khi người dùng đăng nhập Windows**; không giúp service chạy trước login.
- Chưa có proof reboot Ubuntu, offline/reconnect, duplicate-poll receipt, wrong-device binding hoặc natural multi-step Goal.
- Working tree Ubuntu đã có thay đổi của người dùng từ trước; không pull/reset/commit hoặc đụng vào chúng trong pilot. Source control-plane/deploy mới hiện cũng chưa được commit/push theo yêu cầu.

## Next action chính xác

Khôi phục discovery của connector Windows qua ChatGPT/Coding Tools MCP, kiểm tra `fully_ready=true`, rồi tạo **một** workspace binding từ runtime live và chạy **một** read-only canary. Nếu discovery không thể thực hiện trong session hiện tại, dừng ở `WAITING_FOR_CONNECTOR_DISCOVERY`; không có remote mutation và không suy diễn node là ready.
