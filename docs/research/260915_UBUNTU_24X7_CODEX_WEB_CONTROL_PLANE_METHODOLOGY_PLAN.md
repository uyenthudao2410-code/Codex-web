# CODEX-WEB 24/7 — PHƯƠNG PHÁP LUẬN VÀ KẾ HOẠCH TRIỂN KHAI UBUNTU CONTROL PLANE

**Ngày lập:** 15/09/2026  
**Mục đích:** Tài liệu đánh giá kiến trúc trước khi triển khai source.  
**Phạm vi:** Codex-web hiện tại chạy Windows Execution Hub + Coding Tools MCP; bổ sung Ubuntu Server làm điểm vào 24/7, giữ Goal/Task/Device/Workspace binding bền vững và cho phép điều khiển từ điện thoại/máy khác được ủy quyền.  
**Trạng thái:** PHƯƠNG ÁN THIẾT KẾ — chưa phải bằng chứng triển khai, chưa thay đổi runtime, chưa thay đổi tunnel, chưa triển khai production.

---

## 1. Tóm tắt điều hành

Mục tiêu của phương án này không phải chuyển toàn bộ Codex-web từ Windows sang Ubuntu, cũng không phải biến Ubuntu thành một máy thứ hai cùng sửa workspace. Mục tiêu là tách rõ hai lớp:

1. **Control Plane 24/7 trên Ubuntu:** luôn online, giữ điểm vào trung tâm, định danh thiết bị, workspace binding, Goal/Task, trạng thái, quyền, hàng đợi, routing, audit và về sau có thể giữ AI orchestration.
2. **Execution Plane trên từng Windows:** tiếp tục sở hữu workspace thật, Git, build/test, Coding Tools MCP, write authority, proof, recovery và mọi mutation đối với file local.

Kiến trúc này giải quyết trực tiếp giới hạn hiện tại: khi máy Windows tắt, sleep, chưa đăng nhập hoặc tunnel/runtime không hoạt động thì ChatGPT/Codex không còn một đầu mối luôn online để nhận yêu cầu. Ubuntu trở thành **front door 24/7**, nhưng không giả vờ rằng một PC đang tắt vẫn có thể sửa trực tiếp file nằm trên ổ đĩa của PC đó.

Thiết kế đích:

```text
Điện thoại / Laptop / ChatGPT / Codex
                 |
                 v
        Ubuntu Control Plane 24/7
   +----------------------------------+
   | Central MCP / API Front Door     |
   | Device Registry                  |
   | Workspace Registry               |
   | Goal / Task Store                |
   | Routing + Policy                 |
   | Queue / Resume / Audit           |
   | Optional AI Orchestrator         |
   +----------------+-----------------+
                    |
           private outbound links
        +-----------+-----------+
        |                       |
        v                       v
    Windows A               Windows B
 Execution Node           Execution Node
 Coding Tools MCP         Coding Tools MCP
 Workspace A              Workspace B
 Git / Test / Proof       Git / Test / Proof
```

North Star của hệ thống vẫn là:

> **Nhận một Goal thực tế, gắn nó vào đúng thiết bị/workspace/authority, theo đuổi đến accepted outcome với ít manual relay nhất, đồng thời không phá fail-closed, proof và quyền ghi hiện có.**

Ubuntu chỉ có giá trị nếu phục vụ North Star này. Nếu nó chỉ là một reverse proxy cho tunnel thì không đáng xây.

---

## 2. Vấn đề thực tế cần giải quyết

### 2.1 Hiện trạng giới hạn

Mô hình hiện tại về bản chất là:

```text
ChatGPT / Codex
      |
      v
Tunnel trên Windows
      |
      v
Recovery Host / Coding MCP
      |
      v
Local Workspace
```

Điểm yếu vận hành:

- Khi PC tắt hoặc sleep, endpoint không thực thi được.
- Khi runtime/tunnel trên PC mất, không còn điểm vào của PC đó.
- Người dùng từ điện thoại/máy khác phụ thuộc trực tiếp vào tunnel/runtime của máy đích.
- Goal/Task nếu chỉ gắn vào phiên điều khiển hiện tại có nguy cơ phụ thuộc vòng đời client/chat.
- Không có một nơi trung tâm luôn online để giữ hàng đợi, trạng thái WAITING_FOR_DEVICE, quyền, lịch sử và routing.
- Mở rộng nhiều máy theo mô hình “mỗi máy một tunnel trực tiếp” vẫn làm control-plane phân tán.

### 2.2 Vấn đề không được nhầm

Ubuntu Server **không** tự giải quyết việc sửa file khi máy Windows đã tắt nếu file chỉ tồn tại trên máy Windows đó.

Phải phân biệt:

```text
CONTROL AVAILABILITY   = hệ thống vẫn nhận lệnh, giữ Goal/Task, biết trạng thái 24/7.
EXECUTION AVAILABILITY = máy chứa workspace có đủ điều kiện để thực thi hay không.
```

Ubuntu giải quyết control availability 24/7. Execution availability cần một trong ba cách:

1. PC vẫn online và Execution Node hoạt động.
2. Ubuntu đánh thức PC rồi resume task.
3. Task được phép chuyển sang server-side Git workspace tách biệt.

---

## 3. Mục tiêu sản phẩm và các nguyên tắc bất biến

### 3.1 Mục tiêu tối cao

Codex-web không nên được định nghĩa là “MCP điều khiển máy” hay “tunnel cho ChatGPT”. Định nghĩa đúng hơn:

> **Codex-web là execution/orchestration platform biến AI theo từng lượt chat thành một hệ thống có khả năng theo đuổi Goal bền vững, thực thi trên đúng authority, tự kiểm chứng, tự continuation trong phạm vi được cấp và chỉ quay lại con người khi có decision boundary thật.**

### 3.2 Các invariant không được phá

1. **One execution authority per local workspace.** Không tạo Ubuntu runtime ngang hàng cùng ghi trực tiếp một local workspace/ledger với Windows Coding MCP.
2. **No silent failover.** PC A offline không được tự chuyển mutation sang PC B chỉ vì có repo tương tự.
3. **Workspace binding is identity, not path text.** `E:\Project` trên hai máy không phải cùng một workspace.
4. **Tunnel alive != runtime ready.** Online transport không được suy thành quyền mutation.
5. **Goal durable != execution authorized.** Goal có thể tồn tại trên server khi node offline nhưng không được tự thực thi khi thiếu authority.
6. **Timeout != retry permission.** Mất response không được tự replay mutation chưa reconcile.
7. **Technical PASS != user outcome.** Test/proof chỉ là technical evidence; outcome thực tế vẫn có boundary riêng khi cần.
8. **Server cannot fabricate endpoint freshness.** Process/server/activation/workspace-generation phải được node xác nhận lại.
9. **No credential fan-out.** Không dùng một secret toàn cục để mọi node impersonate nhau.
10. **No direct filesystem bypass.** Không dùng SMB/WinRM/SSH để lách Coding MCP write authority cho local workspace mặc định.

---

## 4. Kiến trúc mục tiêu

### 4.1 Phân lớp

#### Ubuntu — Central Control Plane

Sở hữu:

- Central ingress / MCP front door hoặc service gateway.
- Device Registry.
- Workspace Registry.
- User / Role / Permission Registry.
- Durable Goal/Task Store.
- Task queue và trạng thái chờ.
- Routing table.
- Node heartbeat/status projection.
- Audit trail.
- Approval requests.
- Optional AI/model gateway.
- Optional server-side isolated Git workspace.
- Optional Wake/Resume controller.

Không sở hữu mặc định:

- Quyền ghi trực tiếp file local của PC.
- Local Windows process lifecycle chi tiết.
- Local Git credential của user nếu không được cấp riêng.
- Local acceptance authority thay cho Coding MCP.

#### Windows — Execution Node

Giữ:

- Recovery Host / node agent.
- Coding Tools MCP.
- Local workspace.
- Git/build/test/toolchain.
- RUN/WAVE/write lease/proof local.
- Local process/runtime identity.
- Recovery/supervision.
- Device credential riêng.
- Kết nối outbound dài hạn tới Ubuntu.

Electron UI nên trở thành control/config UI; node execution cần tiến tới khả năng hoạt động nền độc lập với việc người dùng mở cửa sổ UI.

### 4.2 Luồng chính khi node online

```text
User from phone
    |
    v
Ubuntu receives Goal/command
    |
    v
Resolve user -> device -> workspace binding
    |
    v
Check node online + freshness
    |
    v
Dispatch typed action
    |
    v
Windows Execution Node revalidates
 endpoint / workspace / generation / authority
    |
    v
Coding MCP executes
    |
    v
Proof + result returned
    |
    v
Ubuntu updates durable Goal/Task state
```

### 4.3 Luồng khi node offline

```text
Goal received
   |
   v
Target binding resolved
   |
   v
Node offline
   |
   +--> WAITING_FOR_DEVICE
   |
   +--> optionally request Wake
   |
   +--> optionally use server-side isolated workspace if policy allows
```

Không được chuyển endpoint ngầm.

---

## 5. Ba mức 24/7 cần phân biệt

### Mức A — 24/7 Control Plane

Ubuntu luôn online, nhận lệnh và giữ trạng thái. PC offline thì task chờ.

**Giá trị:** người dùng luôn có một địa chỉ cố định từ điện thoại/máy khác; Goal không mất.

### Mức B — 24/7 Control + Wake/Resume

Ubuntu có thể đánh thức node được cấp quyền, node boot/reconnect/revalidate rồi tiếp tục task.

**Giá trị:** phần lớn công việc local có thể khởi động từ xa mà không cần người ngồi trước máy.

### Mức C — 24/7 Execution độc lập PC

Ubuntu có server-side isolated Git workspace cho những task đã được policy cho phép.

**Giá trị:** task có thể tiếp tục dù PC đích đang tắt.

**Rủi ro:** drift/conflict với local dirty state; phải dùng branch/worktree/fingerprint và tuyệt đối không giả làm cùng workspace.

Khuyến nghị triển khai theo A -> B -> C, không nhảy thẳng lên C.

---

## 6. Phương pháp luận triển khai

### 6.1 Nguyên tắc: Add above, not rewrite below

Không viết lại Execution Hub/Coding MCP đang có. Ubuntu được thêm **ở phía trên**, rồi từng năng lực được chuyển dần vào central control-plane chỉ khi có proof rằng nó giảm manual intervention hoặc tăng availability.

### 6.2 Nguyên tắc: Evidence before promotion

Mỗi phase phải có:

1. Problem statement.
2. Invariants.
3. Minimal implementation.
4. Focused deterministic proof.
5. Fault injection.
6. Live canary.
7. Quantitative operator-value observation.
8. Go/No-Go.

### 6.3 Nguyên tắc: No architecture by aspiration

Không mở rộng thành microservices/Kubernetes/multi-region chỉ vì “sau này có thể cần”. Bắt đầu với một Ubuntu server, một backend, một durable store và một node Windows.

### 6.4 Nguyên tắc: Fail-closed on identity uncertainty

Nếu server không chứng minh được exact endpoint/workspace/generation/authority thì trạng thái phải là `STALE_BINDING`, `WAITING_REVALIDATION` hoặc `BLOCKED`, không chạy.

### 6.5 Nguyên tắc: Persist intent, not false execution state

Ubuntu được phép biết “Goal này cần chạy trên node A”, nhưng không được tự ghi “đã thực thi” chỉ vì đã dispatch. Execution receipt phải tới từ node/runtime có authority.

---

## 7. Mô hình dữ liệu tối thiểu

### 7.1 Device

```text
Device
- device_id
- endpoint_id
- display_name
- node_public_identity
- status
- last_seen_at
- runtime_version
- process_instance_id
- server_instance_id
- activation_epoch_id
- capabilities
- wake_capability
- revoked_at
```

### 7.2 Workspace Binding

```text
WorkspaceBinding
- binding_id
- device_id
- workspace_id
- workspace_generation
- display_name
- local_path_label (protected/minimized)
- git_remote_fingerprint (optional)
- current_head (projection)
- writable
- last_verified_at
```

### 7.3 Goal

```text
Goal
- goal_id
- owner_user_id
- problem_id / revision if applicable
- target_binding_id
- objective
- criteria
- state
- priority
- budget
- created_at
- updated_at
- policy_version
```

### 7.4 Action / Dispatch

```text
Action
- action_id
- goal_id
- target_binding_id
- operation_type
- request_hash
- state
- dispatch_attempt
- effect_state
- runtime_receipt
- proof_refs
- created_at
- completed_at
```

### 7.5 Permission

```text
Permission
- principal
- device_scope
- workspace_scope
- allowed_operations
- shell_policy
- git_policy
- wake_policy
- server_workspace_policy
- approval_requirements
- expiry
```

---

## 8. Trạng thái task/goal đề xuất

Không tạo state machine cạnh tranh với local EOCL. Ubuntu chỉ có projection cấp control-plane:

```text
NEW
QUEUED
WAITING_FOR_DEVICE
WAITING_REVALIDATION
READY_TO_DISPATCH
DISPATCHED
RUNNING_REMOTE
WAITING_EVIDENCE
WAITING_APPROVAL
WAITING_USER_OUTCOME
BLOCKED
PAUSED
COMPLETED
CANCELLED
```

Local RUN/WAVE vẫn là authority cho execution attempt.

---

## 9. Giao thức Node <-> Ubuntu

### 9.1 Hướng kết nối

Node Windows **chủ động kết nối outbound** tới Ubuntu. Không yêu cầu mở inbound port trên từng mạng của máy thành viên.

Ưu tiên transport có:

- TLS.
- Mutual authentication hoặc device credential mạnh.
- Long-lived connection.
- Reconnect/backoff.
- Server push typed dispatch.
- Client heartbeat.
- Correlation ID.
- Flow control.
- Request size limit.
- Message versioning.

Có thể đánh giá WebSocket/HTTP2/gRPC; lựa chọn cuối phải dựa vào stack hiện tại và khả năng đóng gói Windows, không chọn vì xu hướng.

### 9.2 Handshake bắt buộc

Node gửi:

- device identity.
- endpoint identity.
- app/runtime version.
- process/server/activation identity.
- workspace binding summaries.
- capability manifest.
- signed nonce/challenge response.

Server trả:

- accepted/rejected identity.
- session id.
- policy version.
- allowed bindings.
- heartbeat interval.
- revoked bindings.

### 9.3 Reconnect

Reconnect không tự hồi sinh authority cũ. Phải revalidate:

```text
endpoint_id
workspace_id
workspace_generation
process_instance_id
server_instance_id
activation_epoch_id
runtime contract/version
```

Sau đó mới resume dispatch còn pending.

---

## 10. Idempotency và chống thực thi lặp

Đây là yêu cầu bắt buộc trước khi cho remote mutation.

### 10.1 Quy tắc

Mỗi action có `action_id + request_hash`.

- Cùng ID + cùng hash -> dedupe/reconcile.
- Cùng ID + khác hash -> fail closed.
- Response mất -> query action status/effect journal, không tự phát action mới.
- Unknown effect -> `EFFECT_UNKNOWN`, không replay mutation tự động.

### 10.2 Fault cases phải test

- Server dispatch, node execute xong, response bị mất.
- Node nhận duplicate frame.
- Server restart giữa dispatch và receipt.
- Node restart sau write nhưng trước proof.
- Out-of-order result.
- Reconnect bằng process identity mới.

---

## 11. Quyền và bảo mật

### 11.1 Tách các trust boundary

Phải tách:

- User -> Ubuntu.
- Ubuntu -> Node.
- Node -> Local Coding MCP.
- Optional Ubuntu -> AI provider.

Không dùng token của một boundary cho boundary khác.

### 11.2 RBAC tối thiểu

Role gợi ý:

- Platform Admin.
- Project Admin.
- Developer/Operator.
- Read-only Observer.

Quyền phải granular theo:

- Device.
- Workspace.
- Read/write.
- Command class.
- Git mutation.
- Push/release.
- Wake.
- Restart runtime.
- Server-side execution.

### 11.3 Secret management

- Mỗi node có credential riêng.
- Rotate/revoke từng node độc lập.
- Không ghi secret vào log/audit.
- Ubuntu backup phải mã hóa secret store.
- Compromised node không được dùng credential để impersonate node khác.

---

## 12. Wake / Resume

### 12.1 Wake chỉ là capability, không phải guarantee

Wake phụ thuộc phần cứng, BIOS, LAN/router và trạng thái nguồn. Server phải biểu diễn capability thực tế:

```text
wake_supported
wake_method
last_wake_success
last_wake_failure
```

### 12.2 Flow

```text
Task WAITING_FOR_DEVICE
  -> wake requested
  -> WAITING_FOR_BOOT
  -> node heartbeat
  -> identity revalidation
  -> workspace revalidation
  -> READY_TO_DISPATCH
```

Nếu wake thất bại, task giữ nguyên và báo typed blocker; không retry vô hạn.

---

## 13. Server-side Git Workspace — phase nâng cao

Chỉ triển khai sau khi Central Control Plane và Node path đã ổn định.

### 13.1 Use case hợp lệ

- Code đã có trên remote Git.
- Task không cần local-only dependency/hardware.
- Policy cho phép server execution.
- Base commit xác định được.

### 13.2 Mô hình

```text
Ubuntu
  /workspaces/<goal-id>/<repo>
      isolated branch/worktree
```

Không map thành cùng `workspace_id` với Windows local workspace.

### 13.3 Sync back

Kết quả phải đi qua một trong:

- commit/branch.
- patch artifact.
- pull request.
- explicit handoff.

Không rsync đè local dirty checkout mặc định.

---

## 14. AI orchestration trên Ubuntu — không phải Phase 1

Ubuntu ban đầu chỉ cần control plane. AI brain có thể thêm sau khi execution path ổn định.

Khi triển khai AI orchestration, server có thể giữ:

```text
Goal -> criteria/gaps -> next action proposal -> dispatch -> proof -> re-evaluate
```

Nhưng không được tự chiếm semantic acceptance. Các boundary cần người dùng/admin quyết định vẫn phải dừng ở `WAITING_APPROVAL` hoặc `WAITING_USER_OUTCOME`.

---

## 15. Lộ trình triển khai chi tiết

### Phase 0 — Baseline và khóa invariant

#### Mục tiêu

Không code feature server ngay. Chứng minh baseline Windows hiện tại và chốt contract sẽ giữ.

#### Công việc

- Xác nhận current endpoint identity contract.
- Xác nhận workspace binding/generation semantics.
- Xác nhận Recovery Host/Tunnel lifecycle.
- Xác nhận EOCL/write lease/proof authority.
- Xác định hành vi khi Electron UI đóng.
- Xác định hành vi reboot/logon.
- Ghi rõ các operation tuyệt đối không được server bypass.

#### Acceptance

- Có tài liệu invariant được duyệt.
- Có một Windows node baseline reproducible.
- Đóng Electron UI không làm mất node nếu thiết kế hiện hành yêu cầu headless runtime.
- Phân loại rõ shutdown/sleep/logoff/reboot behavior.

#### No-Go nếu

- Chưa xác định được single write authority.
- Node lifecycle còn phụ thuộc UI không ổn định.

---

### Phase 1 — Ubuntu Central Registry + Read-only Heartbeat

#### Mục tiêu

Ubuntu nhìn thấy node và workspace nhưng chưa dispatch mutation.

#### Ubuntu

- Service daemon.
- Durable DB.
- Device registry.
- Workspace registry.
- Heartbeat API.
- Minimal admin UI hoặc CLI.

#### Windows

- Node connector chạy nền.
- Outbound authenticated connection.
- Publish bounded metadata.

#### Acceptance

- Ubuntu restart không mất registry.
- Windows reconnect giữ stable device identity.
- Workspace generation change được phát hiện.
- Revoked node không reconnect được.
- Hai máy có cùng path vẫn hiển thị thành hai binding khác nhau.

#### Fault tests

- Network cut.
- Ubuntu restart.
- Node restart.
- Credential revoke.
- Clock drift hợp lý.

---

### Phase 2 — Central 24/7 Front Door Read-only

#### Mục tiêu

Người dùng từ điện thoại/máy khác có một endpoint trung tâm luôn online để hỏi trạng thái và đọc dữ liệu được phép từ node online.

#### Công việc

- Central authentication.
- User -> device/workspace ACL.
- Read-only routed calls.
- Node unavailable projection.
- Mobile/browser-friendly status.

#### Acceptance

- Từ mạng ngoài truy cập được qua approved ingress.
- User A không nhìn thấy binding không được cấp.
- Node offline trả `WAITING/UNAVAILABLE`, không failover.
- Central tunnel/ingress vẫn sống khi một node Windows tắt.

---

### Phase 3 — Remote Mutation với Exact Binding

#### Mục tiêu

Cho phép sửa từ điện thoại/máy khác nhưng chỉ trên node online và exact authorized workspace.

#### Công việc

- Typed dispatch.
- Exact binding checks.
- Idempotency/effect journal.
- Reconciliation API.
- Approval boundaries.
- Proof return.

#### Acceptance bắt buộc

- Wrong device rejection.
- Wrong workspace rejection.
- Stale generation rejection.
- Duplicate mutation không chạy lại.
- Lost response được reconcile.
- No silent cross-device failover.
- Proof gắn đúng source/runtime identity.

#### Canary

Một repo thử nghiệm, mutation nhỏ, test deterministic.

---

### Phase 4 — Durable Goal/Task Queue

#### Mục tiêu

Goal tồn tại trên Ubuntu độc lập với điện thoại/browser/chat hiện tại.

#### Công việc

- Goal store.
- Task queue.
- Binding persistence.
- WAITING_FOR_DEVICE.
- Resume after node reconnect.
- Stop/revoke.
- Budget/expiry.

#### Acceptance

- Tắt browser không mất Goal.
- Ubuntu restart không mất Goal.
- Node offline rồi online lại không tạo task trùng.
- Stop/revoke thắng race với resume.
- Goal không tự chạy trên endpoint khác.

---

### Phase 5 — Wake and Resume

#### Mục tiêu

Từ điện thoại có thể yêu cầu tiếp tục task trên máy đang tắt khi hạ tầng wake hỗ trợ.

#### Công việc

- Wake capability registry.
- Wake request authorization.
- Bounded retry.
- Boot timeout.
- Node revalidation before resume.

#### Acceptance

- Wake thành công trên ít nhất một máy thật.
- Wake failure không loop.
- Node khác không bị đánh thức nhầm.
- Sau boot phải revalidate workspace/epoch trước mutation.

---

### Phase 6 — Background Goal Continuation

#### Mục tiêu

Sau khi Goal được cấp scope/budget, không cần người dùng liên tục nhắn “tiếp tục”.

#### Công việc

- Server-held parent Goal state.
- Dispatch next valid action.
- Consume proof.
- Re-evaluate criteria.
- WAITING_APPROVAL boundary.
- WAITING_USER_OUTCOME boundary.

#### Acceptance

- Một natural Goal hoàn thành nhiều bước mà không manual relay.
- Không auto-accept.
- Không retry unchanged failure vô hạn.
- Có complete causal lineage.
- Đo manual-intervention count và TTAR.

---

### Phase 7 — Optional Server-side Execution

#### Mục tiêu

Cho phép một subset task chạy 24/7 dù PC tắt.

#### Công việc

- Isolated Git workspace manager.
- Remote repo credentials scoped.
- Branch/worktree lifecycle.
- CI/build environment.
- Handoff back to PC/user.

#### Acceptance

- Không ghi đè local dirty state.
- Base mismatch fail closed.
- Server result có provenance riêng.
- Sync back explicit.

---

### Phase 8 — Multi-user / Enterprise Control

#### Mục tiêu

Biến hệ thống thành nền tảng AI execution dùng chung nội bộ.

#### Công việc

- RBAC đầy đủ.
- Organization/project scopes.
- Quota/budget.
- Usage reporting.
- Audit/export.
- Fleet rollout/versioning.

Chỉ làm sau khi 1-user/1-Goal economics chứng minh hiệu quả.

---

## 16. Tiêu chí đánh giá hiệu quả

Không đánh giá bằng số service hoặc số feature.

### KPI chính

1. **Availability of control plane** — tỷ lệ thời gian front door Ubuntu hoạt động.
2. **Remote success rate** — tỷ lệ task remote chạy đúng endpoint/workspace.
3. **Wrong-target execution count** — mục tiêu = 0.
4. **Duplicate-effect count** — mục tiêu = 0 cho các action có oracle idempotency.
5. **Manual relay count** — số lần phải nhắn “tiếp tục” không cần thiết.
6. **Time to accepted result (TTAR).**
7. **Replan/rework count.**
8. **False closure rate.**
9. **Recovery success after node reconnect.**
10. **Wake success rate** với node có capability.
11. **Operator burden** — số thao tác admin/người dùng mỗi Goal.

### Điều kiện để gọi dự án 24/7 thành công

Không phải “Ubuntu ping được Windows”. Phải chứng minh:

```text
User submits Goal from another device
 -> central service remains reachable
 -> exact device/workspace resolved
 -> offline condition handled truthfully
 -> node reconnect/wake resumes safely
 -> mutation executes once
 -> proof returns
 -> Goal persists across browser/server/node interruptions
```

---

## 17. Ma trận rủi ro

| Rủi ro | Mức | Biện pháp |
|---|---:|---|
| Wrong device/workspace mutation | Critical | exact binding + generation + fail closed |
| Duplicate side effect after lost response | Critical | action ID + effect journal + reconcile |
| Ubuntu compromise | Critical | node-scoped creds, least privilege, secret rotation |
| Node impersonation | Critical | per-node auth + challenge + revoke |
| Server becomes second writer | Critical | prohibit direct local FS path; Coding MCP owns local mutation |
| Goal resumes after authority revoked | High | revalidation on reconnect/resume |
| Server-side workspace conflicts local dirty state | High | isolated branch/worktree + explicit handoff |
| Wake loops/battery/network issues | Medium | bounded retry + capability state |
| Too much architecture before value proof | High | phased gates + KPI + KEEP/MODIFY/REMOVE |
| Central outage blocks all nodes | High | local execution should degrade gracefully where possible |

---

## 18. Rollback strategy

### Phase 1–2

Ubuntu là additive. Tắt server -> Windows direct mode vẫn dùng được.

### Phase 3+

Phải có feature flag:

```text
central_routing_enabled=false
```

để quay lại direct tunnel/local path khi cần.

Không migration phá hủy local ledger/workspace.

Goal server-side phải export được thành trạng thái chờ, không ép local runtime nhận task không có authority.

---

## 19. Cấu hình triển khai ban đầu đề xuất

### Ubuntu

Cho pilot một vài node:

- Ubuntu LTS.
- 2–4 vCPU.
- 4–8 GB RAM.
- SSD.
- TLS.
- systemd services.
- PostgreSQL hoặc một durable DB phù hợp sau khi chốt concurrency; không cần microservice DB riêng cho từng module.
- Reverse proxy chỉ nếu cần ingress/TLS termination.
- Backup encrypted.

Không cần GPU nếu server chưa chạy model local.

### Windows Node

- Giữ Codex-web hiện tại.
- Bổ sung node connector nền.
- Auto-start/recovery.
- Per-node secret.
- No inbound Internet port.

---

## 20. Pilot đầu tiên đề xuất

### Thiết bị

- Ubuntu Server: luôn online.
- Windows A: máy thử nghiệm chính.
- Điện thoại hoặc laptop khác: remote client.

### Test cases

1. Windows A online -> đọc workspace từ điện thoại.
2. Sửa một file canary -> test -> proof.
3. Ngắt mạng giữa response -> reconcile, không chạy hai lần.
4. Tắt Windows A -> Ubuntu vẫn online, task thành WAITING_FOR_DEVICE.
5. Bật Windows A -> node reconnect -> revalidate -> task tiếp tục.
6. Restart Ubuntu -> registry/Goal còn nguyên.
7. Đổi workspace generation -> stale task bị chặn.
8. Thêm Windows B với path workspace giống A -> route không nhầm.
9. Revoke Windows A -> không nhận task mới.
10. Nếu Wake khả dụng -> thử wake/resume thật.

Pilot chỉ được coi đạt nếu **không có wrong-target, duplicate mutation hoặc false READY**.

---

## 21. Quyết định kiến trúc đề xuất

### Nên làm

- Ubuntu = persistent central control plane.
- Windows = execution nodes.
- Node outbound private connection.
- Goal/task/binding bền vững trên server.
- Exact identity revalidation.
- Central ingress/tunnel 24/7.
- Offline queue.
- Wake/resume sau.
- Server-side Git execution cuối cùng, opt-in.

### Không nên làm

- Chuyển toàn bộ Coding MCP lên Ubuntu ngay.
- Mount remote Windows drive làm đường mutation chính.
- Mỗi node là một tunnel độc lập mãi mãi nếu mục tiêu là central 24/7.
- Auto failover workspace khi node offline.
- Tạo second orchestration ledger tranh authority với local EOCL.
- Cho server replay mutation chỉ vì timeout.
- Xây Kubernetes/multi-region trước pilot.

---

## 22. Quan hệ với North Star của Codex-web

Central Ubuntu không phải một dự án tách rời. Nó chỉ hợp lý khi nâng khả năng:

```text
Goal
 -> durable binding
 -> correct execution node
 -> autonomous continuation
 -> deterministic proof
 -> accepted result
 -> user outcome
```

Lợi ích trực tiếp:

- Goal không chết theo browser/chat.
- Hệ thống có điểm vào cố định từ điện thoại.
- Node offline không làm mất intent.
- Có thể wake/resume.
- Sau này có thể chuyển một subset workload sang server-side execution.
- Mở đường multi-user/fleet mà không phá local execution authority.

Nếu sau pilot không giảm manual relay, không tăng availability hữu ích hoặc làm tăng rework/complexity nhiều hơn giá trị nhận được thì phải thu hẹp hoặc dừng, không tiếp tục chỉ vì đã đầu tư kiến trúc.

---

## 23. Definition of Done tổng thể

Chỉ coi chương trình “Codex-web 24/7” đạt khi có bằng chứng thực tế rằng:

1. Có một central endpoint luôn online độc lập với Windows UI.
2. Người dùng có thể giao/kiểm tra Goal từ điện thoại hoặc máy khác được ủy quyền.
3. Device/workspace binding đúng và bền vững.
4. Node offline được biểu diễn trung thực và Goal không mất.
5. Node reconnect/wake có thể resume sau revalidation.
6. Remote mutation chống duplicate/lost-response đúng.
7. Không có silent failover hoặc second writer.
8. Proof/acceptance vẫn giữ authority đúng.
9. Một natural multi-step Goal giảm rõ manual relay so với baseline.
10. Có rollback về direct/local mode.
11. Metrics cho thấy TTAR/operator burden tốt hơn hoặc availability tăng đủ để biện minh chi phí kiến trúc.

---

## 24. Thứ tự ưu tiên khuyến nghị

```text
P0  Baseline Windows / invariant
P1  Ubuntu Registry + heartbeat
P2  Central 24/7 read-only front door
P3  Exact remote mutation
P4  Durable Goal/Task queue
P5  Wake + reconnect/resume
P6  Background Goal continuation
P7  Optional server-side Git execution
P8  Multi-user / fleet / AI gateway
```

Không đảo thứ tự P3 trước P1/P2; không làm P7 trước khi P3/P4 chứng minh identity/idempotency; không làm P8 trước khi một-user Goal economics cho thấy giá trị.

---

## 25. Kết luận

Kiến trúc Ubuntu đáng triển khai khi nó được xem là **persistent control plane cho Codex-web**, không phải máy thay thế Windows và không phải proxy cho có.

Mô hình tối ưu cho mục tiêu hiện tại là:

> **Ubuntu luôn online để nhận Goal, giữ routing/binding/task state và điều phối; Windows node giữ quyền thực thi local; node có thể được wake/resume; những task đủ điều kiện mới được chạy trên server-side isolated workspace.**

Thiết kế này giải quyết đúng hai yêu cầu lớn nhất:

1. **Điểm vào 24/7 từ điện thoại/máy khác, không phụ thuộc app/tunnel của từng PC đang mở.**
2. **Tiến tới Goal continuation bền vững mà vẫn bảo toàn exact workspace authority, proof và fail-closed của Codex-web hiện tại.**

Đây nên được triển khai như một chương trình đo bằng accepted-result economics và operator burden, không phải bằng số lượng thành phần mới được xây.
