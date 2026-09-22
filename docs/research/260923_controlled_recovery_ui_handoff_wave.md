# Controlled recovery wave — UI handoff và canonical ledger boundary

Ngày quan sát: `2026-09-23` (Asia/Ho_Chi_Minh)

Workspace: `E:\DEV\Codex-web`

Branch: `main`

Base trước wave: `da7d8273fe94d082d873d186b95bf75886c3dbfa`

Đây là một snapshot tiến độ mới, không sửa lại các số liệu lịch sử trong
`260922_ke_hoach_xu_ly_hai_problem_va_danh_gia_toan_dien_app.md` hoặc
`260923_recheck_runtime_va_activation_authority.md`.

## 1. Phạm vi và ranh giới quyền hạn

Wave này xử lý blocker handoff của hai Problem đang vẫn mở:

| Problem | Revision | Contract | Trạng thái tại thời điểm wave |
|---|---:|---:|---|
| `prl-22e670302757c9b7663170e226ed7c26` | 1 | C01–C12 | `OPEN` |
| `prl-e918c7d33e70c2d304d0797e11b05fcb` | 2 | 18 tiêu chí | `OPEN` |

Mục tiêu kỹ thuật của wave là làm cho **idle packaged-to-development handoff**
có thể đọc được bằng chứng UI fresh một cách an toàn. Đây không phải là
quyền tự động mở admission, không phải acceptance của Problem, và không phải
proof MCP/Tunnel/natural-use.

`E:\DEV\Codex-web\.coding-tools\orchestration\ledger.sqlite3` vẫn là
canonical live evidence. Wave không mở SQLite writer, không import report,
không chèn checkpoint, không sửa byte ledger và không gắn checkpoint cũ vào
HEAD mới. File ledger dirty chỉ phản ánh runtime evidence đang được bảo toàn
theo repository policy.

## 2. Reproduction và nguyên nhân đã chứng minh

Trước wave, Recovery Host packaged còn sống và Supervisor healthy nhưng primary
MCP/Tunnel/admission đều chưa usable:

```text
mcpRunning=false
nativeAlive=false
tunnelRunning=false
fullyReady=false
updateIncomplete=true
admission_open=false
connectorRediscovered=false
connectorContractState=UNAVAILABLE
```

`npm start` đã đi vào đúng đường cold-start `idle_packaged_handoff`, sau đó bị
chặn bởi:

```text
RECOVERY_HOST_IDLE_HANDOFF_REFUSED
The packaged Recovery Host is not provably idle for a development-checkout handoff.
```

Readback authenticated trước wave cho thấy điều kiện fail duy nhất là
`ui_quiescent=false`. Recovery Host trả projection cached:

```text
electron_ui_recovery.alive = null
electron_ui_recovery.state = unknown
registered = false
initial_registration_grace_until = expired
pending_registration_until = null
next_attempt_at = null
circuit_suppressed_until = null
```

Nguyên nhân typed là **handoff dùng cached status**, trong khi cached path cố
ý không chạy process-identity probe trên IPC event loop. Với UI chưa từng đăng
ký, projection đó không có một lần `observeUiPresence()` fresh để tạo
`alive=false`; vì vậy guard đúng khi từ chối, nhưng không có đường đọc bounded
để chứng minh trạng thái vắng mặt terminal.

Không được sửa nguyên nhân bằng cách đổi mọi `unknown` thành `missing`: UI đã
đăng ký nhưng identity probe không xác minh được phải tiếp tục là
`alive=null/state=unknown` và phải block handoff.

## 3. Thay đổi đã triển khai trong source

### 3.1 Fresh status read cho idle handoff

`electron/services/recoveryHost.js` bổ sung `freshHostStatus()`:

1. gọi `activation.observeUiPresence()` bất đồng bộ;
2. giữ nguyên cached runtime projection cho MCP/Tunnel/epoch;
3. chỉ thay phần `electron_ui_recovery` bằng kết quả fresh;
4. không gọi mutation, không mở admission, không ghi ledger.

`recovery.status` nhận tùy chọn nội bộ `{ fresh: true }`. Status/heartbeat bình
thường vẫn dùng cached projection như trước.

### 3.2 Handoff gọi đúng fresh path

`electron/services/recoveryBootstrap.js` truyền `fresh: true` vào status call
trong `proveIdlePackagedHandoff()`, vẫn dùng chung bounded deadline với
`runtime.lightweight_snapshot()`.

`electron/services/recoveryIpc.js` giữ cờ `fresh` ở request argument, không
để nó trở thành transport/identity authority. Descriptor owner PID,
instance-id và process-start-token vẫn được kiểm tra như trước.

### 3.3 Invariant không đổi

- UI đã đăng ký nhưng process identity `unavailable` → `alive=null`,
  `state=unknown`, handoff bị từ chối.
- Runtime component đang sống, snapshot stale/busy, epoch không terminal hoặc
  workspace không khớp → handoff bị từ chối.
- Fresh status là read-only; không được dùng để sửa epoch, descriptor,
  accepted checkpoint hay canonical ledger.

## 4. Bằng chứng kiểm thử của wave

Đã chạy:

```text
node --test tests/recovery-host.test.js tests/recovery-bootstrap.test.js
  88/88 PASS

npm run test:recovery:e2e
  3/3 PASS
  - Electron client chết và reattach không thay Recovery Host ownership
  - Safe Code Activation thay Coding MCP đúng boundary
  - Recovery Host handoff giữ nguyên MCP/Tunnel identity boundary

node --check electron/services/recoveryIpc.js
node --check electron/services/recoveryBootstrap.js
node --check electron/services/recoveryHost.js
git diff --check
  PASS

npm test
  1022/1022 PASS
  source root clean
  repository secret check: PASS

npm run dist:dir
  PASS; dist/win-unpacked/resources/app.asar SHA-256=
  49E1FB34BB1F43AECC170A957390CC102ED364D1CC2A2FCF530A8916DC00BA84
  packaged electron/services/recoveryHost.js SHA-256 matches source
  DC032904EF9DE968F4B78A57DE1778BE8A829B1FEEBC432E89A0FDAEA343AA7F

node scripts/packaged-recovery-smoke.js
  PASS: executable/app.asar/resources/tool contract/isolation/recovery host/
  MCP alive/Supervisor fail-closed checks
```

Regression tests mới bao phủ:

- fresh status với UI chưa đăng ký → `alive=false/state=missing`;
- fresh status với UI đã đăng ký nhưng async identity unavailable →
  `alive=null/state=unknown`;
- IPC client truyền `{fresh:true}` như một read argument, không trộn vào
  transport options.

Số PASS này bao gồm regression wrapper; không suy diễn từ nó sang packaged
runtime hoặc canonical Problem acceptance.

## 5. Trạng thái ledger và recovery thật

Tại thời điểm ghi snapshot:

- chưa có controlled recovery thành công cho `ledger.sqlite3`;
- không có accepted checkpoint mới cho HEAD hiện tại;
- không có quyền hợp lệ để nhận các checkpoint/report lịch sử bind HEAD cũ;
- Supervisor/Recovery Host liveness không được nâng thành
  `LIVE_ACCEPTED` hoặc `fullyReady`;
- packaged artifact đang chạy phải được kiểm tra lại sau khi source patch được
  đóng gói; source test pass chưa chứng minh installed runtime đã nạp patch.

Vì vậy wave này mới đạt **source + focused proof + integration boundary**.
Nó chưa đạt `PACKAGED_RELEASED`, `STRICT_REDISCOVERED`, `LIVE_ACCEPTED`,
`workspace_context` thật, reboot/logon acceptance hoặc natural outcome.

## 6. Bước kế tiếp có điều kiện

1. Chạy lại focused suite sau regression wrapper và kiểm tra diff.
2. Commit source/test/research trực tiếp trên `main`; trước commit chạy
   `npm run stage:coding-tools-delivery`,
   `npm run check:coding-tools-delivery` và history/secret guards theo
   `AGENTS.md`. Không stage thủ công `ledger.sqlite3`.
3. Push commit lên `origin/main` theo yêu cầu vận hành hiện tại.
4. Tạo packaged artifact chứa đúng source hash, chạy packaged smoke/identity
   checks; không gọi đó là installed-runtime proof nếu chưa đối chiếu path và
   process identity.
5. Chỉ khi packaged host nạp patch và `proveIdlePackagedHandoff()` PASS mới
   chạy supported `npm start`/full-clean activation. Postflight bắt buộc kiểm:
   MCP, native process, Tunnel hoặc central route, activation epoch/loaded
   revision, connector freshness/strict discovery, `fullyReady=true`, và một
   `workspace_context` thật trên đúng workspace.
6. Sau đó mới xem xét reboot matrix, Machine B, fault injection, 48 giờ
   natural-use và independent outcome cho C09/C12 hoặc các tiêu chí tương ứng.

## 7. Quyết định hiện tại

**Tiếp tục triển khai source repair là an toàn và có regression proof.**
**Không được tuyên bố recovery ledger đã hoàn tất và không được đóng một trong
hai Problem.** Blocker tiếp theo là package/runtime identity: bản patch phải
được nạp vào packaged Recovery Host qua đường được hỗ trợ; nếu installation
guard hoặc source/checkpoint authority còn thiếu, giữ fail-closed và ghi
`BLOCKED` kèm bằng chứng cụ thể thay vì bypass.

## 8. Hậu kiểm commit và Ubuntu transport — 2026-09-23 00:35 +07

Source wave đã được ghi vào commit `889e76c10a76822e2d942bd8500ee862c046f020`.
Delivery receipt được refresh trong commit
`a8aff1ad2f1f6b733ddd67040d40893d73fcfc5f`; cả hai đã được push tới
`origin/main`. Các commit này không thay đổi `control-plane/` hoặc `deploy/`.
Vì vậy Ubuntu không cần nhận một control-plane package mới cho source wave
fresh-UI này; release immutable đang chạy vẫn được đối chiếu độc lập với
revision `da7d8273fe94d082d873d186b95bf75886c3dbfa`.

Readback SSH sau commit cho thấy:

- `codex-control-plane.service` và `codex-control-plane-mcp-tunnel.service`
  đều `active`; health của control-plane qua `100.116.112.22:8765/healthz`
  trả `ok=true`, SQLite `integrity=ok`, schema `25`, admission `recovery`,
  actual/expected package SHA cùng là
  `sha256:4cbb2b37b4c2ce84ba8aaaa5564ebed83b376dd2d8e5d7af62c98adc3ea6a18c`,
  declared revision `da7d8273…`, và `unquarantined_unresolved_action_count=0`.
- MCP grant cũ đã hết hạn theo đúng TTL; không hồi sinh record cũ. Một grant
  mới được cấp qua `POST /v1/mcp-access-grants` cho context hiện tại với
  principal `ubuntu-root-tunnel-da7d8273`, hết hạn lúc
  `1790120919948`, grant id
  `mcpgrant_1785dd64202a4f4cbd5db07a4849eb51`. Raw bearer không được ghi vào
  repository, log hoặc báo cáo; header private được thay thế atomic đúng
  launcher contract (file chứa giá trị thuần `Bearer <grant>`, mode
  `0600`) và metadata redacted được cập nhật. Grant trung gian ghi nhầm dạng
  `Authorization: ...` đã được revoke qua API trước khi kết thúc wave.
- Sau restart Tunnel, `healthz=live`, `readyz=ready`; authenticated loopback
  MCP `initialize` và `tools/list` đều thành công. `tools/list` trả đủ tám
  public tools và contract `schema_version=6`,
  `profile=control-plane-scoped-read-only-relay-v5`,
  `sha256=c947f8d5f3fed1355bc1236f0d45c8e7c7877a3d0b2c1a17344a90ead98c8f1b`.

Đây là bằng chứng **remote service + authenticated local MCP strict
discovery**. Nó không phải Windows installed-runtime proof, ChatGPT cloud
client discovery, `workspace_context` natural task, admission mở, reboot
acceptance hay release/production acceptance. Windows source patch đã build và
packaged smoke PASS trong working tree, nhưng installed Recovery Host vẫn
phải được cài bằng đường được hỗ trợ và vẫn đang bị installation/source
acceptance guard chặn; không được gọi `npm start` là hoàn tất.

## 9. Rollout Ubuntu theo HEAD hiện tại — 2026-09-23 01:01 +07

Sau khi mục tiêu vận hành yêu cầu server nhận đúng HEAD, control-plane release
đã được build lại từ `2b432b030cd8c94b3bf9ae0601d0b444e6edaec5` và verify độc lập:

- schema `25`, manifest có `34` file;
- package source fingerprint giữ nguyên
  `sha256:4cbb2b37b4c2ce84ba8aaaa5564ebed83b376dd2d8e5d7af62c98adc3ea6a18c`;
- archive SHA-256
  `c60c283729ca381fe0d29aee74a569378a8bc9e227b67db1f59bf3c1aa8cbec1`;
- backup trước rollout chạy qua systemd, SQLite `integrity=ok`, schema `25`,
  snapshot SHA-256
  `781868516bdd708c461f151b1e4d4116ba70800bb3c9de0cd08a3c75f7f65b2d`,
  `unquarantined_unresolved_action_count=0`.

Archive được upload/extract vào release directory versioned, verifier remote
PASS, immutable environment/drop-in được chuẩn bị bằng
`prepare-control-plane-activation.py`, rồi symlink `current` được chuyển
atomic. Sau `systemctl --user daemon-reload` và restart service, readback thực
tế xác nhận:

```text
current = /home/svhome/.local/lib/codex-control-plane/releases/codex-control-plane-2b432b030cd8c94b3bf9ae0601d0b444e6edaec5
declared_source_revision = 2b432b030cd8c94b3bf9ae0601d0b444e6edaec5
package_source_sha256 = expected_package_source_sha256
sqlite_integrity = ok
schema_version = 25
admission_mode = recovery
service_instance_id = cp_f21afc55faca4c2da313f3592186d71d
unquarantined_unresolved_action_count = 0
codex-control-plane.service = active
codex-control-plane-mcp-tunnel.service = active
8768/readyz = ready
```

Sau rollout, authenticated local MCP `initialize` và `tools/list` vẫn PASS với
đúng tám tool và contract SHA `c947f8d5…`. Đây là **server deployment + local
strict discovery** của HEAD hiện tại; admission vẫn cố ý đóng ở `recovery`,
không tự retry 11 action unresolved đã quarantine, không phải Windows
installed-runtime acceptance hoặc natural-work outcome.
