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

## 8. Post-push, package và live-boundary recheck

Commit đã push trực tiếp lên `origin/main`:

```text
889e76c10a76822e2d942bd8500ee862c046f020
HEAD = origin/main
```

Sau push, supported `npm start` đã được thử một lần. CLI nhận diện đúng
`idle_packaged_handoff` nhưng vẫn dừng fail-closed:

```text
RECOVERY_HOST_IDLE_HANDOFF_REFUSED
```

Lý do runtime không được đổi là descriptor đang thuộc packaged process cũ:

```text
Recovery Host PID = 40120
executable = C:\Users\Admin\AppData\Local\Programs\Coding Tools MCP\Coding Tools MCP.exe
DEV_UI status = host=available installation=mismatch
full-clean preflight/status = RECOVERY_HOST_INSTALLATION_MISMATCH
```

Postflight không thấy epoch mới, không thay PID/instance của Recovery Host và
không mở admission. Đây là blocker **installed-runtime/package deployment**,
không phải lý do để sửa descriptor, xoá process bằng tên, hoặc nạp source
thủ công vào app.asar đang chạy.

### 8.1 Installer candidate

Đã chạy release-boundary build không cài đè production:

```text
npm run dist
  JavaScript: 1022/1022 PASS
  MCP Python: 1162 passed, 5 skipped
  NSIS: dist/coding-tools-mcp-setup-1.0.7.exe
  installer_size = 121588717 bytes
  installer_sha256 = D17E71CC89CF80C1C2E75BD4148E873FB9015808183070D11FE71333F3DE24F2
  blockmap_size = 129158 bytes
```

`node scripts/installed-recovery-smoke.js` đã cài candidate vào target cô lập,
kiểm tra executable/app.asar/resources/smart-v3/recovery/MCP/Supervisor, rồi
uninstall thành công:

```text
installer installed=true registered=true version=1.0.7
packaged_smoke.ok=true
uninstall.exit_code=0
installed_files_removed=true
registration_removed=true
production_descriptor_stable=true
scheduled_task_definition_stable=true
```

Đây là bằng chứng **isolated installed package**, không phải bằng chứng rằng
instance production PID `40120` đã nạp patch. Việc cài đè vào production path,
restart packaged host và chạy full-clean activation vẫn cần một execution wave
được ủy quyền riêng; không tự thực hiện bằng copy thô hay `taskkill`.

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

## 10. Controlled recovery recheck và sửa lỗi READY proof — 2026-09-23 01:36 +07

### 10.1 Live recheck trước khi thử lại

Đã đọc lại bằng `RecoveryIpcClient` chính thức của packaged installation, với
đúng data root `C:\Users\Admin\AppData\Roaming\web-mcp-assistant`; không dùng
raw IPC, không sửa JSON runtime/control-plane, không đụng trực tiếp SQLite và
không gửi restart lần ba trước khi xác định nguyên nhân.

Receipt quan trọng tại `2026-09-22T18:32:01Z–18:32:23Z`:

| Lớp | Quan sát | Diễn giải |
|---|---|---|
| Supervisor | PID `6172`, `healthy`, task `Running`, `consecutive_failures=0`; host PID `52348`, instance `7e969d265f1c9c28f99bb3678d5bd96f` | Recovery supervisor và replacement Recovery Host vẫn sống; không cần kill/spawn lại để chứng minh host |
| Recovery Host | packaged, code revision running=disk `9dbfd39a…`, descriptor epoch `activation-mud08kdv-4d0c8e0ed107f0a6c2b1c9f18825c95e` | Host identity/revision hiện tại có thể xác minh; đây chưa phải READY epoch |
| Primary MCP | `mcpRunning=true`, `nativeAlive=true`, running=disk revision `a49891f8…`, process/server identity đã đọc được | Primary process thực sự đã start; không còn là lỗi “không spawn được MCP” |
| Central route | `centralConnected=true`, `authorityReady=true`, route evidence hợp lệ nhưng `runtime_readiness=degraded`; aggregate reason `LOCAL_EXECUTOR_NOT_READY` | Route/authenticated heartbeat tồn tại, nhưng local executor chưa được phép quảng bá READY |
| Activation | `epoch_state=FAILED`, projected `state=UPDATE_INCOMPLETE`, `admission_open=false`, `ready_commit_digest=null` | Admission vẫn đóng đúng fail-closed; không có proof READY để mở lại |
| Connector | `connectorRediscovered=false`, `connectorRefreshRequired=true`, contract `smart-v3` | Với `central_executor`, đây không phải điều kiện thay thế cho central route; vẫn chưa có strict ChatWeb discovery |
| UI/recovery plane | UI registered/alive PID `51620` nhưng đang `suppressed/operator_quit`; recovery MCP state có PID `51296`; final census trước đó không được ghi đầy đủ | Không suy diễn `ui_verified`/`recovery_plane_verified` từ liveness đơn lẻ |

Không có ledger recovery mutation mới. Census query-only độc lập trước retry vẫn
giữ `integrity_check=ok`, `foreign_key_check_rows=0`,
`mutated_canonical_ledger=false`, `projection_drift=false`,
`unexplained_active_runs=0`; do đó blocker hiện tại không phải corruption hay
quyền ghi ledger.

### 10.2 Nguyên nhân đã tái hiện bằng code và regression proof

Failure `ACTIVATION_EPOCH_READY_PROOF_REQUIRED` với message
`Final runtime census reports UPDATE_INCOMPLETE` được truy ngược tới hai pha
được thiết kế trong `FullCleanActivation`:

1. `finalCensus()` chạy khi record còn `state=VERIFYING` và
   `admission_state=CLOSED`, trước `commitReady()/complete_epoch`.
2. `lightweightSnapshot()` phản ánh trung thực epoch chưa mở admission bằng
   `runtime.updateIncomplete=true`, đồng thời `fullyReady=false` và
   `centralStatusReason=LOCAL_EXECUTOR_NOT_READY`.
3. Khi tất cả predicate độc lập của final census đã đạt (MCP/native, revision,
   workspace/device, process identity, UI, recovery plane, projection và
   central route), proof vẫn mang cờ `runtime.updateIncomplete=true` vào
   `ActivationEpochStore.commitReady()`, nên store từ chối proof hoàn chỉnh.

Đây là lỗi ở biên proof hai pha, không phải lý do để hạ revision guard hoặc
cho phép route degraded thành READY. Đã sửa tại
`electron/services/fullCleanActivation.js`: chỉ sau khi `pass=true` và đúng
record `VERIFYING/CLOSED`, proof được đánh dấu `admissionPending=true` và tách
`runtime.updateIncomplete` của trạng thái chờ mở admission khỏi các guard
component/revision/identity. Mọi failure trước `pass` vẫn giữ nguyên
`updateIncomplete=true` và fail-closed.

Regression test central activation được mở rộng để inject đúng trạng thái
`updateIncomplete=true` trong cửa sổ pre-admission và yêu cầu:

```text
runtime.updateIncomplete=false
runtime.admissionPending=true
finalize() -> READY
admission_state -> OPEN
```

Proof đã chạy:

```text
node --test tests/full-clean-activation.test.js
63/63 PASS
```

Đây mới là source/focused proof; packaged installation đang chạy chưa chứa
patch mới ở thời điểm receipt trên.

### 10.3 Checkpoint và bước tiếp theo

Checkpoint wave này:

- controlled restart lần đầu: `CANONICAL_LEDGER_CENSUS_TIMEOUT`, không tạo epoch;
- census độc lập sau đó: PASS, không mutation/projection drift;
- controlled retry: tạo epoch mới, đi qua `HANDOFF → STARTING → VERIFYING`,
  nhưng fail ở READY proof vì cờ pre-admission nêu trên;
- sau failure: Supervisor/Recovery Host vẫn healthy, admission vẫn CLOSED,
  không được gọi là ledger corruption và không retry nguyên trạng;
- source fix + regression proof đã có, chưa build/cài packaged candidate mới.

Exact next action là: chạy release-boundary JavaScript/package proof cho patch
này, cài packaged candidate qua đường installer được hỗ trợ vào đúng production
profile (không copy thô/app.asar edit), đọc lại process/package hashes, rồi
chỉ thực hiện **một** controlled full-clean recovery mới nếu preflight/census
độc lập còn PASS. Postflight phải chứng minh activation `READY`/admission OPEN,
`fullyReady=true`, central route READY, exact epoch/revision/process identity,
strict connector discovery và một `workspace_context` thật trên
`E:\DEV\Codex-web`. Nếu một điều kiện fail, giữ `BLOCKED` và ghi receipt; không
kill process theo tên, không sửa descriptor/route evidence, không chỉnh ledger.

## 11. Postflight sau epoch READY và concurrent development owner — 2026-09-23 02:14 +07

### 11.1 Readback ngay sau packaged recovery

Đã gọi lại `RecoveryIpcClient` chính thức, có ràng buộc
`owner_pid/instance_id/process_start_token` và kiểm tra descriptor trước/sau
đọc. Bản đọc đầu tiên lúc `2026-09-22T19:11:44.249Z` vẫn nhìn thấy descriptor
packaged của epoch trước:

```text
Recovery Host PID/instance: 51596 / 07fbc4a9bb4f0125b9437b53298f54d5
runtime_mode: packaged
activation_epoch_id: activation-mud1ltj0-dbb496722a2f89bdc3bd67d11bdce579
epoch/state: READY / READY, admission_open=true
ready_commit_digest: 9f62d74db3b2252af458b932ded265e0777569ccf45e7e61bc6f96cdcf0376
```

Tuy nhiên readback process-level không còn đủ để gọi runtime live: `identityObservation()`
trả `identity_current=false`, không có current MCP process/server identity và
không có `workspace_read`. Ngay sau đó `lightweight_snapshot()` trả
`snapshotSource=recovery_host_supervision_unavailable`, `telemetryAvailable=false`,
`signalStale=true`, `updateIncomplete=true`; `health.inspect()` trả
`healthy=false`, MCP `Chưa khởi động`, central reason `LOCAL_EXECUTOR_NOT_READY`.
Vì vậy epoch `READY` cũ chỉ là durable proof của thời điểm trước, không được
re-use như live acceptance.

### 11.2 Concurrent owner đã làm thay đổi runtime

Process audit read-only cho thấy một lifecycle owner khác bắt đầu đúng trong
window hậu kiểm:

```text
PID 51104  npm start
PID 2296   node scripts/dev-ui-lifecycle.js start
PID 29980  Electron --recovery-host --replace-recovery-host=...
runtime_mode hiện tại: development
```

Log runtime ghi nhận lúc `2026-09-22T19:11:38Z–19:12:09Z` các bước stop
Coding Tools MCP, tạo epoch `activation-mud1wb9n-29d19ff6ea2be6cd41ee7c718e2aa041`
với operation `full-clean-refresh-mud1w05k-233e50c07a154cdcf048baf1`, rồi
khởi động development host/MCP. Packaged host `51596`, packaged UI `52212` và
Recovery MCP `52676` không còn sống sau handoff; Supervisor PID `53176` vẫn
đang chạy và status file trỏ tới development host `29980`. Đây là conflict
ownership, không phải lý do để kill theo tên/process tree; process này được giữ
nguyên trong wave hiện tại.

### 11.3 Epoch mới fail-closed đúng guard

Epoch development mới đã ghi:

```text
state/admission: FAILED / CLOSED
error: UPDATE_INCOMPLETE
reason: A live component identity changed before MCP admission.
central_status_reason: CENTRAL_ROUTE_EVIDENCE_STALE
central_connected: false
authority_ready: false
central_route_verified: false
```

Final census trung gian có `pass=true` và các predicate local như workspace,
device, revisions, process identity, UI, recovery plane đều đúng; nhưng bước
revalidation cuối phát hiện central route stale và live identity đã đổi, nên
không mở admission. Đây là hành vi fail-closed đúng thiết kế, không phải lỗi
để hạ guard hoặc ghi đè `activation-epoch.json`.

### 11.4 Canonical ledger census sau biến động runtime

Đã chạy lại reporter chính thức query-only lúc
`2026-09-22T19:14:38.258Z`:

```text
content_free=true
mutated_canonical_ledger=false
integrity_check=ok
foreign_key_check_rows=0
schema_version=12
projection.classification=CONTEXTUAL_PROJECTIONS
context_count=1079
projection_drift=false
ordinary_active_runs=17
P5_EXPERIMENT_ANCHOR=6
THRESHOLD_SENSITIVE_STALE_CANDIDATE=17
stale_background_operation_residues=0
unbound_live_resource_residues=0
unexplained_active_runs=0
```

Snapshot mới có physical SHA-256
`2c496d38caff846eec69866bbc94680aa25597a29c0acfc50d5a7f4e721b14da` và logical SHA-256
`d61e251cb03f18383b36dcee7bb226e3ce5bb779312e4241b0fc05fd8bf19c8d`.
Hash thay đổi giữa các snapshot là biến động runtime/evidence; census đồng thời
khẳng định `mutated_canonical_ledger=false`, integrity/FK vẫn PASS. Không có
căn cứ gọi đây là corruption, không VACUUM/truncate/insert hoặc sửa trực tiếp
SQLite.

### 11.5 Connector và workspace proof vẫn chưa đạt

Vì runtime hiện tại đã fail và không có action/admission receipt từ ChatWeb
client, không thực hiện `runtime.control_plane_read_only_workspace_context`.
Schema local yêu cầu policy/owner/device/endpoint/workspace/generation,
`context_id`, `binding_id`, `action_id`, `attempt_id`, expiry và facade contract
đúng policy; tự tạo các ID này sẽ là fabrication, nên không dùng. Không có
strict current-process `tools/list`/`server/discover`, không có connector ACK
mới và không có một `workspace_context` thật trên `E:\DEV\Codex-web`.

### 11.6 Checkpoint và hành động kế tiếp

Wave hậu kiểm này được phân loại **BLOCKED — concurrent lifecycle owner + stale
central route**, với các kết luận tách biệt:

- **Đã chứng minh:** source fix READY proof; packaged installer/smoke; epoch
  packaged trước đó READY; ledger hiện tại integrity/FK/census PASS; không có
  mutation ledger bất thường.
- **Chưa chứng minh:** packaged runtime đang sống sau concurrent handoff;
  strict connector discovery; `workspace_context` thật; reboot/logon,
  Machine B, fault injection, natural-use và independent outcome.
- **Không thực hiện:** không kill process, không chỉnh descriptor/route
  evidence, không retry restart mù, không sửa SQLite.

Exact next action cần một lifecycle window không có `npm start`/dev owner đang
giữ data root: xác định owner của PID `51104` và cho phép dừng/hoàn tất đúng
process đó (hoặc chờ nó terminalize), sau đó đọc lại supervisor/descriptor và
chạy **một** controlled activation từ packaged installer. Nếu central route còn
stale, dừng ở `BLOCKED_EXTERNAL_DISCOVERY` và xử lý heartbeat/discovery trước;
không coi local `fullyReady` hay epoch cũ là product closure. Hai Problem vẫn
OPEN, tách revision và không được gộp trạng thái.

## 12. Controlled refresh hậu kiểm — epoch mới READY, ledger chỉ đọc — 2026-09-23 02:29 +07

### 12.1 Không tạo activation cạnh tranh

Trước khi gửi bất kỳ lệnh restart nào, preflight phát hiện một lifecycle owner
đang tồn tại:

```text
PID 37968  node scripts/dev-ui-lifecycle.js refresh
PID 53240  Electron --recovery-host --activation-epoch-id=activation-mud2ehak-...
PID 53176  recovery-supervisor.ps1 -Action Run
PID 37192  packaged control-plane node_agent.py run-connected-agent
```

Vì vậy wave không gửi restart thứ hai, không kill theo tên/process tree và
không sửa descriptor. Owner hiện tại đã tự hoàn tất controlled refresh; việc
để PID `37968` tồn tại được ghi nhận như trạng thái concurrent owner, không được
diễn giải thành một activation mới do wave này tự tạo.

### 12.2 Receipt Recovery IPC chính thức

Bản đọc dùng `RecoveryIpcClient` với cả `owner_pid`, `instance_id` và
`owner_process_start_token` lấy từ descriptor rồi kiểm tra lại cùng owner trong
mọi request. Thời điểm receipt: `2026-09-22T19:28:47.176Z` UTC.

| Gate | Kết quả hiện tại | Bằng chứng |
|---|---|---|
| Recovery Host | `healthy`, packaged/development descriptor hợp lệ, PID `53240`, instance `f0f47e1682e1ff18b78bb8492f9caeda` | `recovery.status({fresh:true})` và process-start-token khớp |
| Epoch | `READY`, `admission_open=true`, `update_incomplete=false` | `activation-mud2ehak-7ad885728cf77543cc9c84c30c851c46`, operation `full-clean-refresh-mud2e765-086d9a39c0c6c5573b757f03`, ready digest `26b95907ada975a1344b020df021bcb8f8d89fcd5356fe7d5cd147a0b316d28e` |
| MCP/native | `mcpRunning=true`, `nativeAlive=true`, `componentsReady=true`, `fullyReady=true` | lightweight snapshot fresh, telemetry available, signal không stale, snapshot không busy |
| Central route | `centralConnected=true`, `authorityReady=true`, `centralStatusReason=null`, `central_route_verified=true` | runtime snapshot + `health.inspect()` control-plane route `ok=true` |
| Tunnel | `tunnelRunning=false`, `tunnel_state=not_configured` | đúng với `executionRole=central_executor`; không bật tunnel cục bộ để làm xanh số liệu |
| Identity/epoch binding | `identity_current=true`, MCP process `gEEsgwMs2LiE6Cxu`, server `pXqwTEXehcD0eBZ-`, cả hai cùng epoch | `runtime.identity_observation` khớp descriptor/epoch hiện tại |
| Workspace | `E:\DEV\Codex-web`, device `4c4b7a5b-7744-49ae-a490-78a528a00471`, branch `main`, HEAD `b02fe564` | lightweight snapshot và health inspect |
| Connector | **chưa đạt** | `connectorRediscovered=false`, `connectorRefreshRequired=true`, `connectorContractState=CHANGED_NEEDS_DISCOVERY` |
| Client workspace read | **chưa có** | `workspace_read=null`; chưa có current-process `tools/list`/`server/discover` và `workspace_context` thật từ ChatWeb |

Receipt này chứng minh **local/central runtime recovery**, không chứng minh
strict connector discovery, ChatWeb delivery hay natural product outcome.
`runtime_readiness=degraded` trong route evidence vẫn được lưu đúng như một
trường advisory; các predicate acceptance đã dùng là `centralConnected`,
`authorityReady` và `central_route_verified`, không biến advisory đó thành
`connector_ready`.

### 12.3 Ledger census sau controlled refresh

Đã chạy reporter chính thức query-only lúc `2026-09-22T19:29:22.119Z` UTC:

```text
content_free=true
mutated_canonical_ledger=false
canonical_writer_instantiated=false
runtime_instantiated=false
integrity_check=ok
foreign_key_check_rows=0
schema_version=12
projection.classification=CONTEXTUAL_PROJECTIONS
context_count=1079
projection_drift=false
ordinary_active_runs=17
P5_EXPERIMENT_ANCHOR=6
THRESHOLD_SENSITIVE_STALE_CANDIDATE=17
stale_background_operation_residues=0
unbound_live_resource_residues=0
unexplained_active_runs=0
```

Snapshot của chính lần census này:

```text
physical SHA-256: 209f743e3f730ad37923e115165361d6a119951332eaf5200ffdd44eccdbf68d
logical SHA-256:  66a7bcffcc6f9e53d2520aff3cefc2871cca7323662e3b36654937d11c935d48
size:             97,742,848 bytes
```

Đọc trực tiếp read-only cùng cửa sổ cho thấy canonical hiện đã nhìn thấy ba
RUN lịch sử trước đây từng chỉ xuất hiện trong generated report:

| Problem/revision | accepted | aborted | active | Tổng RUN bind hiện tại |
|---|---:|---:|---:|---:|
| `prl-22e670302757c9b7663170e226ed7c26` / rev 1 | 47 | 16 | 3 | 66 |
| `prl-e918c7d33e70c2d304d0797e11b05fcb` / rev 2 | 16 | 10 | 13 | 39 |

Ba RUN đã được thấy trong canonical snapshot hiện tại là `dcb539e0e1694bc1bb29eed2b2e07f8b`,
`d01a5dce50c846fc8e13673cdfc8b3b3` và `b194ab1e311e42efa1dd0614ca245037`,
đều `accepted` và đều bind Problem `prl-22e...` rev 1. Việc snapshot trước
đó không nhìn thấy chúng và snapshot hiện tại nhìn thấy chúng là một sai khác
giữa các cửa sổ/copy ledger; chưa có căn cứ quy nguyên nhân, không gọi là
corruption và không tự insert/reconcile SQLite. Current canonical read là số
được dùng cho đánh giá này; các số `44/16/3` ở Section 11 chỉ giữ nguyên như
lịch sử của snapshot cũ.

Hai Problem vẫn `OPEN`: số RUN/accepted tăng không tạo criterion disposition,
independent outcome, natural-use, reboot/logon matrix, Machine B, fault
injection hoặc closure authority. Không được gộp rev 1 với rev 2.

### 12.4 Checkpoint wave và bước tiếp theo

Wave này được phân loại **RUNTIME_RECOVERY_VERIFIED / PRODUCT_ACCEPTANCE_OPEN**:

- **Đã đạt:** controlled refresh không cạnh tranh; Recovery Host identity;
  epoch mới `READY/OPEN`; MCP/native/central route/authority; matching
  process identity và workspace; ledger census integrity/FK/projection không
  drift; Problem counts current được đọc lại trực tiếp.
- **Chưa đạt:** current-process connector strict discovery; `tools/list` hoặc
  `server/discover` receipt; một `workspace_context` thật có delivery
  confirmation; reboot/logon; Machine B; authorized fault injection; natural
  48-hour use; independent outcome; criterion coverage và closure.
- **Không thực hiện:** không sửa byte `ledger.sqlite3`, không tạo RUN/checkpoint
  thủ công, không acknowledge connector bằng hash cũ, không bật local tunnel
  trái role, không kill process theo tên, không dùng epoch cũ làm acceptance.

Exact next action là thu current ChatWeb connector receipt bằng đường client
chính thức (strict `tools/list`/`server/discover`), sau đó mới gọi một
`workspace_context` thật trên đúng workspace và lưu readback bound vào process,
server, epoch và contract SHA. Nếu không có client/connector receipt, giữ
`PRODUCT_ACCEPTANCE_OPEN`; không hạ guard và không tuyên bố hai Problem đã đóng.

### 12.5 Source gap được sửa sau receipt

Receipt runtime đã tái hiện một lỗi ở **lifecycle CLI**, không phải lỗi MCP hay
central route: `refreshRuntimeReady()` và postflight trước đây bắt buộc
`tunnelPid`, `tunnelInstanceId` và `tunnel_health_verified` cho mọi role. Với
`central_executor`, đây là sai hợp đồng vì local Coding Tunnel được cấu hình
`not_configured`; kết quả là epoch đã `READY/OPEN` nhưng
`npm run dev:refresh` tiếp tục polling và không trả thành công.

Đã sửa trực tiếp trên `main`:

- role `central_executor` lấy `tunnel_required=false` từ final census/role
  contract;
- central route phải có đủ `central_connected`, `authority_ready` và
  `central_route_verified` — không được bỏ qua route proof để làm xanh CLI;
- PID/identity/process-alive và freshness chỉ yêu cầu Coding Tunnel khi
  `tunnel_required=true`;
- direct-legacy vẫn giữ nguyên yêu cầu tunnel và connector pending gate;
- dòng postflight hiển thị `tunnel=not-required` cho central executor, giữ
  `tunnel=ready/stopped` cho role cần tunnel.

Focused regression đã chạy:

```text
node --test tests/dev-ui-lifecycle.test.js
71/71 PASS

- central-executor refresh accepts route proof without inventing a Coding Tunnel
- dev:refresh accepts a central executor without a local tunnel
- direct-legacy exact refresh vẫn yêu cầu tunnel/identity như trước
```

Đây là source/focused proof cho CLI gate. Cần chạy lại một lifecycle refresh
được giám sát sau khi owner `37968` terminalize để chứng minh installed/runtime
postflight dùng logic mới; không dùng lại epoch cũ như một receipt mới.

## 13. Refresh mới sau khi owner terminalize — runtime READY, connector vẫn mở — 2026-09-23 02:38 +07

### 13.1 Controlled refresh receipt

Sau khi PID `37968` đã kết thúc và không còn lifecycle owner cạnh tranh, đã chạy
đúng một lệnh:

```text
node scripts/dev-ui-lifecycle.js refresh
exit=0
epoch=activation-mud2rqud-3343e319a40c7e2c9fc856be6434546f
activation=READY
host=fb0d900d04874005df606f065dc78cbe
ui=ea980597bb5477d74fbbdb84f1ddcc16
mcp_pid=21000
tunnel_pid=unknown
mcp=ready
tunnel=not-required
admission=open
fully_ready=true
```

Lệnh trên được chạy trước khi bản sửa connector-presentation ở Section 12.5
được nạp vào CLI, nên dòng cuối của chính lần chạy đó in
`connector=ready`. Dòng này **không phải connector receipt** và không được dùng
làm bằng chứng strict discovery; readback Recovery IPC ngay sau đó là authority
cho connector và trả `connectorReady=false`/`CHANGED_NEEDS_DISCOVERY`.

### 13.2 Readback authoritative sau refresh

Receipt `RecoveryIpcClient` có ràng buộc descriptor tại
`2026-09-22T19:38:34.323Z` UTC:

```text
Recovery Host: PID 50572, instance fb0d900d04874005df606f065dc78cbe
Epoch: READY / admission_open=true / update_incomplete=false
Operation: full-clean-refresh-mud2regy-33ff5646c80036e675e39f0b
Ready digest: cd8070bb14745c2cde3f48694c2d10abcd2fdd37494e9bce2df2927c6075f8e4
MCP/native: true / true; componentsReady=true; fullyReady=true
Central: centralConnected=true; authorityReady=true; centralStatusReason=null
Tunnel: false; tunnel_state=not_configured; executionRole=central_executor
MCP process/server: iT8OpsOV6dDu1Knq / XQTIoNq7bXLmcZUD
identity_current=true; current_activation_epoch_id khớp epoch
connectorReady=false; connectorRefreshRequired=true
connectorRediscovered=false; connectorContractState=CHANGED_NEEDS_DISCOVERY
workspace_read=null
health control-plane-route: ok=true
```

`node scripts/dev-ui-lifecycle.js status` lúc `2026-09-22T19:38:11.706Z`
cũng phản ánh đúng phân tách mới: `fully_ready=true` nhưng
`connector_state=CHANGED_NEEDS_DISCOVERY` và `connector_refresh_required=true`.
Sau Section 12.5, các lần refresh tiếp theo sẽ in `connector=pending` cho tuple
này; không còn lấy `fullyReady` của central executor làm connector readiness.

### 13.3 Ledger census cuối cửa sổ refresh

Reporter query-only lúc `2026-09-22T19:38:43.679Z` UTC tiếp tục cho:

```text
content_free=true
mutated_canonical_ledger=false
canonical_writer_instantiated=false
runtime_instantiated=false
integrity_check=ok
foreign_key_check_rows=0
projection_drift=false
context_count=1079
ordinary_active_runs=17
P5_EXPERIMENT_ANCHOR=6
THRESHOLD_SENSITIVE_STALE_CANDIDATE=17
stale_background_operation_residues=0
unbound_live_resource_residues=0
unexplained_active_runs=0
physical SHA-256: cd0291b9e1e7da017d9699489606c14fe8781b7399212f89ec42b15871fd7273
logical SHA-256:  a0e6c6753c2a6029ad237e3a4be9463d39fb982db63795b66d9100b323b75337
```

Hash vật lý/logical tiếp tục thay đổi giữa các immutable read window trong khi
integrity/FK và census predicates vẫn PASS. Đây là runtime/evidence drift cần
được gắn snapshot khi delivery; không phải căn cứ để sửa, truncate, VACUUM hay
reconcile thủ công ledger.

### 13.4 Kết luận wave

Controlled recovery hiện đã chứng minh được **runtime layer** trên một epoch mới
và source CLI đã được sửa cho đúng role/connector semantics. Mục tiêu của hai
Problem vẫn chưa đạt vì còn thiếu strict connector discovery, một
`workspace_context` thật, reboot/Machine B/fault-injection, natural-use,
independent outcome và criterion closure. Trạng thái chính xác là
`RUNTIME_RECOVERY_VERIFIED / PRODUCT_ACCEPTANCE_OPEN`, không phải
`LIVE_ACCEPTED` hay `PROBLEM_CLOSED`.

### 13.5 Validation sau source patch

```text
node --test tests/dev-ui-lifecycle.test.js
  71/71 PASS

npm test
  1025/1025 PASS
  source root clean
  repository secret check: PASS
```

`npm test` là source/test proof ở HEAD làm việc hiện tại; nó không thay thế
strict connector discovery, ChatWeb `workspace_context`, reboot matrix hoặc
natural outcome. Bước delivery tiếp theo vẫn phải snapshot lại volatile
`.coding-tools/**`, chạy các guard delivery bắt buộc, rồi commit/push trực tiếp
trên `main` theo chính sách repository.

## 14. Controlled recovery tiếp theo — route/epoch đã hội tụ, connector vẫn mở — 2026-09-23

### 14.1. Mục tiêu và nguyên tắc thực hiện

Wave này được thực hiện trực tiếp trên checkout `main`, không tạo worktree và
không chỉnh byte của `ledger.sqlite3`. Trước mutation, route evidence được đọc
bằng chính `readControlPlaneRouteEvidence()` với `Date.now()`, descriptor được
đối chiếu với PID/instance/installation/start-token, và census canonical được
chạy bằng Backup API/query-only. Không dùng epoch cũ để nhận là mới, không tạo
epoch thủ công, không truyền source checkpoint cho `refresh=true`, không gọi
`npm start` cạnh tranh và không bật local Coding Tunnel cho
`central_executor`.

### 14.2. Phát hiện nguyên nhân của lần handoff đầu

Preflight đầu tiên lúc khoảng `2026-09-22T19:51Z` cho thấy route parser đã
`CENTRAL_ROUTE_READY` (policy `enabled`, endpoint đúng, age khoảng vài giây),
connected agent PID `37192` và Recovery Host PID `19628` đều sống đúng
identity. Request `full_clean_refresh` được gửi qua `RecoveryIpcClient` với
đúng owner PID/instance/start-token, nhưng socket trả `ECONNRESET` sau khi
handoff bắt đầu. Không retry mù; epoch mới ghi lại `FAILED/ECONNRESET` và
Recovery Host replacement đã chuyển sang source `development`.

Sau handoff, packaged connected-agent của Supervisor vẫn chạy với
`runtime-mode=packaged`, trong khi descriptor mới là `development`. Official
`runtime-heartbeat` packaged trả `runtime_status_unavailable`; route evidence
không được cập nhật và sau hơn 60 giây parser trả
`CENTRAL_ROUTE_EVIDENCE_STALE`. Đây là mismatch package–epoch–runtime, không
phải bằng chứng Control Plane đã mất enrollment. Process PID `37192` còn
`Responding` nhưng không có socket và heartbeat không tiến; sau khi xác minh
lock instance/start-token, chỉ đúng PID này được terminate bằng
`terminateExactProcessTree()`. Supervisor đã spawn replacement PID `50576`,
nhưng replacement packaged vẫn không đọc được host development.

Không sửa route evidence bằng tay. Một lần gọi official source
`runtime-heartbeat` với `runtime-mode=development` và `node.exe` của source
đã ghi evidence fresh (`policy_state=enabled`, route parser `CENTRAL_ROUTE_READY`)
và phân loại readiness là `degraded` vì strict connector discovery chưa có.
Đây là lý do hợp lệ để mở một epoch mới; nó không được nâng thành connector
receipt hay natural outcome.

### 14.3. Epoch mới và postcondition runtime

Sau khi route fresh, một request có owner identity ràng buộc được gửi duy nhất
một lần:

```text
reason=operator_route_recovery_retry_after_dev_heartbeat
executionRole=central_executor
componentProfile=central_executor_v1
refresh=true
mode=full_clean_refresh
allowAcceptancePending=false
```

Request trả `HANDOFF` với:

```text
operation_id=full-clean-mud3kybn-1c42c9b4abcc0bc7dba2d758
activation_epoch_id=activation-mud3l2r5-24df6bcefa255d01e213d0556c167be4
```

Readback authoritative lúc `2026-09-22T20:00:48.441Z` UTC (03:00:48 +07):

| Gate | Kết quả | Phân loại |
|---|---|---|
| Recovery Host | PID `52256`, identity sống, mode `development` | PASS cho current source host |
| Epoch | `READY`, `admission_open=true`, `update_incomplete=false` | PASS |
| MCP/native | `true/true`; `componentsReady=true`; `fullyReady=true` | PASS |
| Central route | `centralConnected=true`; `authorityReady=true`; reason `null` | PASS |
| Role/Tunnel | `central_executor`; `tunnelRunning=false` | PASS — local Tunnel không được yêu cầu |
| MCP identity | `identity_current=true`; epoch hiện tại khớp | PASS |
| Contract | `smart-v3`, SHA `bc44c044…` | PASS cho loaded runtime |
| Connector | `connectorReady=false`; `CHANGED_NEEDS_DISCOVERY`; `connectorRediscovered=false` | OPEN |
| Workspace read | `null` trong snapshot identity | Chưa có client receipt |

`mcp_process_instance_id` và `mcp_server_instance_id` của lần đọc này đã được
đối chiếu với `runtime.identity_observation`; chúng chỉ là runtime binding,
không phải bằng chứng ChatWeb đã gọi `tools/list`/`server/discover`.

`node scripts/dev-ui-lifecycle.js status` cùng cửa sổ cũng cho
`state=CURRENT`, UI/MCP revision current, `components_ready=true`,
`fully_ready=true`, nhưng vẫn `connector_state=CHANGED_NEEDS_DISCOVERY` và
`connector_refresh_required=true`. Vì vậy source fix ở Section 12.5 đã được
kiểm chứng trên runtime mới: central executor không bị ép có Tunnel, nhưng
không được làm xanh connector bằng `fullyReady`.

### 14.4. Canonical ledger và chỉ số tri thức sau wave

Reporter chính thức query-only lúc `2026-09-22T20:02:07.512Z` UTC trả:

```text
content_free=true
mutated_canonical_ledger=false
canonical_writer_instantiated=false
runtime_instantiated=false
integrity_check=ok
foreign_key_check_rows=0
schema_version=12
projection.classification=CONTEXTUAL_PROJECTIONS
context_count=1079
contextual_sha256=8ffd702686dde2da39eda737f79589e942a41fc0a465bea7037a5f67a8c2398f
projection_drift=false
ordinary_active_runs=17
P5_EXPERIMENT_ANCHOR=6
THRESHOLD_SENSITIVE_STALE_CANDIDATE=17
stale_background_operation_residues=0
unbound_live_resource_residues=0
unexplained_active_runs=0
```

Immutable read hiện tại của hai Problem vẫn tách revision:

| Problem/revision | accepted | aborted | active | Tổng RUN bind | State |
|---|---:|---:|---:|---:|---|
| `prl-22e670302757c9b7663170e226ed7c26` / rev 1 | 47 | 16 | 3 | 66 | `OPEN` |
| `prl-e918c7d33e70c2d304d0797e11b05fcb` / rev 2 | 16 | 10 | 13 | 39 | `OPEN` |

Các số này là status mix của RUN đã bind; không phải completion rate và không
phải criterion PASS. Trên current revision vẫn chưa có canonical
`coverage_manifest`/`criterion_dispositions`/`problem_outcome_claim` đủ để
đóng 12 hoặc 18 criterion. `context_count=1079` là projection ngữ cảnh, không
phải 1.079 natural task. P5 vẫn có 6 shadow A/A anchor nhưng chưa có
enrollment/assignment/protocol/binding/outcome; efficacy/ROI vẫn
`UNESTIMABLE`. Knowledge ACK missingness, P4 mismatch và 48-hour natural-use
gate nêu ở Section 3–10 giữ nguyên; không tự ACK, không biến report-gate thành
outcome.

Physical/logical SHA của các cửa sổ ledger thay đổi theo runtime evidence; wave
này chỉ ghi snapshot được reporter trả về, không dùng drift đó làm lý do
VACUUM/truncate/reconcile hay insert history. Trước delivery tiếp theo phải
stage lại snapshot canonical và chạy đủ delivery/history/secret guards.

### 14.5. Quyết định lựa chọn và backlog còn lại

**Lựa chọn đã thực hiện:** giữ `central_executor`, route central authenticated,
local Tunnel `not_required`, runtime source/epoch mới và admission mở. Đây là
lựa chọn ít state nhất cho host hiện tại và phù hợp role contract; không chuyển
sang `direct_legacy` chỉ để ép Tunnel lên.

**P1 cần bổ sung cho app:** Supervisor hiện hard-code connected-agent
`runtime-mode=packaged`. Khi full-clean handoff từ installed host sang source
development, agent sẽ không đọc được runtime và heartbeat sẽ stale. Cần chọn
một trong hai hướng trước acceptance reboot lâu dài:

1. **Khuyến nghị:** freeze acceptance trên một packaged bundle duy nhất và giữ
   Supervisor/Recovery Host/agent cùng `packaged` identity; source `main` chỉ
   là authority để build/verify bundle.
2. Nếu sản phẩm chính thức cho phép development runtime tự resume, bổ sung
   mode-aware Supervisor manifest/agent (development node, explicit data-root,
   exact app-root/install identity) cùng focused tests và reinstall proof. Không
   trộn agent packaged với host development và không dùng one-shot heartbeat
   như workaround vận hành.

Các gate sau vẫn mở và phải có receipt độc lập:

- current ChatWeb connector `tools/list` hoặc `server/discover`, bind với MCP
  process/server/epoch/contract SHA;
- một `workspace_context` thật trên `E:\DEV\Codex-web`, có
  `workspace_accessed=true` và delivery/receipt readback;
- reboot/logon installed matrix, Machine B, authorized fault injection;
- ít nhất 48 giờ natural-use theo canonical capsule, một natural case và
  independent outcome;
- exact criterion coverage/disposition và closure authority riêng cho từng
  Problem revision.

Cho tới khi các gate trên có bằng chứng, trạng thái được ghi chính thức là:

```text
RUNTIME_RECOVERY_VERIFIED
PRODUCT_ACCEPTANCE_OPEN
```

Không gọi `LIVE_ACCEPTED`, không gọi `PROBLEM_CLOSED`, không coi
`fullyReady=true` là strict connector discovery và không gộp trạng thái rev 1
với rev 2.

## 15. Packaged alignment sau controlled recovery — runtime hiện tại READY, acceptance vẫn mở — 23/09/2026

### 15.1. Phạm vi và preflight bất biến

Wave này tiếp tục trên đúng checkout `main`, không tạo worktree và không ghi
trực tiếp vào canonical `ledger.sqlite3`. Trước khi hạ host, một census
query-only/Backup API đã xác minh:

```text
integrity_check=ok
foreign_key_check_rows=0
mutated_canonical_ledger=false
canonical_writer_instantiated=false
runtime_instantiated=false
ordinary_active_runs=17
projection_drift=false
context_count=1079
P5 epochs=6
stale_background_operation_residues=0
unbound_live_resource_residues=0
unexplained_active_runs=0
```

Snapshot ledger sau khi runtime hội tụ (được gắn thời điểm, không dùng như
current-live claim ngoài cửa sổ này):

```text
snapshot_at=2026-09-22T20:30:10.699Z UTC
size=97,742,848 bytes
schema_version=12
physical_sha256=c29f5c2bde1045c6a25b65872bd8646979217b8a9f8d478bb6983d2834e09d29
logical_sha256=b7bc5bdb7e7fe208b66d544903dc33ec06c9ddbea0d9640eb7042465f5c8aa4a
integrity_check=ok
foreign_key_check_rows=0
mutated_canonical_ledger=false
```

Các hash/size này là evidence snapshot của wave. Ledger và các projection
`.coding-tools` có thể tiếp tục drift sau thời điểm snapshot; không được
reconcile, truncate, VACUUM, insert hoặc chỉnh byte để làm hash ổn định.

### 15.2. Handoff được xác thực và một lần refresh có kiểm soát

Development Recovery Host trước handoff có identity:

```text
PID=52256
instance_id=61b8b8f8e636c3304e79d1f5d6dad5a2
runtime_mode=development
installation_id=2628d627fb21b539eef81c4bf57ce0107d362532edd516a475500fef9359a1a6
process_start_token=134345807766169590
```

Đã gọi đúng authenticated IPC `runtime.stop({ manual: false })`. Sau khi đọc
lại descriptor và xác minh start-token, chỉ PID `52256` được chuyển qua
`terminateExactProcessTree()`; kết quả `state=already_exited`,
`exit_state=exited`, `verified_start_token=true`. Không dùng `taskkill` theo
tên và không kill nhầm process khác.

Supervisor sau đó tự spawn packaged Recovery Host PID `11816`. Chỉ một request
refresh được gửi qua đường chính thức:

```text
runtime.restart({
  reason: "operator_packaged_runtime_alignment",
  refresh: true,
  mode: "full_clean_refresh",
  executionRole: "central_executor",
  componentProfile: "central_executor_v1",
  allowAcceptancePending: false
})
```

Response ban đầu là `state=HANDOFF`, với:

```text
operation_id=full-clean-mud4ar4v-94707fc5d3be30ef24785f4d
activation_epoch_id=activation-mud4ayw2-005f6a3498d3d4a6e82de0a36d0051c2
```

Trong lúc handoff, epoch đã đi qua `UPDATE_INCOMPLETE/VERIFYING` với
`admission_open=false`. Đây là trạng thái trung gian được giữ fail-closed;
không retry mù, không acknowledge acceptance pending và không suy ra failure
cuối cùng từ snapshot trung gian.

### 15.3. Postflight runtime và package identity

Readback authenticated sau khi các component/route/identity postflight hoàn tất:

```text
Recovery Host PID=40048
runtime_mode=packaged
instance_id=1bf6bb38f4626c12a23c267bee371da0
installation_id=ac60479cbef9e20f6b4c2e246a16a2f20141863dc417d28ef32c7a01ed1ae001

activation_epoch_id=activation-mud4ayw2-005f6a3498d3d4a6e82de0a36d0051c2
operation_id=full-clean-mud4ar4v-94707fc5d3be30ef24785f4d
state=READY
admission_open=true
update_incomplete=false

mcpRunning=true
nativeAlive=true
componentsReady=true
fullyReady=true
executionRole=central_executor
tunnelRunning=false
tunnel_required=false
centralConnected=true
authorityReady=true
identity_current=true
```

MCP continuity của cùng epoch:

```text
running_revision=a49891f8e6bff0bfb2d49284ff85d8cd73946508f59ff0a7b8ebd8ed0339dfe5
disk_revision=a49891f8e6bff0bfb2d49284ff85d8cd73946508f59ff0a7b8ebd8ed0339dfe5
update_pending=false
mcp_process_instance_id=ZFuaGyMY-5GxEboc
mcp_server_instance_id=dHWLsx0swGYNatpt
tool_contract_sha256=bc44c044a0b08dfdea80b8ba0dfcc080e180e21a5460dbf9726b49ac1fa769b0
```

Health readback trả `healthy=true`, `workspace=true`, `runtime=true`,
`mcp-port=true`, `mcp=true`, `control-plane-route=true`. Supervisor cũng ở
`state=healthy`, `last_host_pid=40048`, `control_plane_agent_state=
running_heartbeat_only`, `restart_attempts=0`, `last_error_code=null`.

Installed identity đã được ghi lại để không gộp source với package:

```text
Coding Tools MCP.exe = CF6602046D0B6412C1A162C9574E6BB123B03AF69458922D196377C4DD75B9F7
resources/app.asar  = 46275190064B83910F967F41F76D84CD65F45C0DCEF9B96695A1DB9B8527BBD6
packaged node_agent.py = E36C072298A907494DDEF5F18C9430099D5BB8F84BC0063ED4250F4BCC5D5AE4
Supervisor manifest = F51709192BBD7C5B27DAD3E3D377F7442792BC459B67250F825AF072FA87991F
```

Route evidence lúc postflight có `policy_state=enabled`,
`runtime_readiness=ready`, device `4c4b7a5b-7744-49ae-a490-78a528a00471` và
endpoint `executor-4c4b7a5b-7744-49ae-a490-78a528a00471`. Với
`central_executor`, `tunnelRunning=false` là đúng contract; không bật local
Tunnel chỉ để làm xanh một gate không thuộc role này.

### 15.4. Ranh giới connector, workspace và natural outcome

Runtime `READY` không làm thay thế strict connector discovery. Readback vẫn là:

```text
connectorRediscovered=false
connectorRefreshRequired=true
connectorContractState=CHANGED_NEEDS_DISCOVERY
workspace_read=null
```

Chưa có receipt current ChatWeb `tools/list`/`server/discover` bind với MCP
process/server, activation epoch và contract SHA; chưa có
`workspace_context` thật trên `E:\DEV\Codex-web` với `workspace_accessed=true`;
chưa có delivery confirmation và independent product outcome. Vì vậy không
gọi `acknowledgeConnectorContract()`, không tự ghi ACK, không biến một
`fullyReady=true` thành connector-ready, và không tuyên bố reboot/natural-use
đã đạt.

### 15.5. Chỉ số Problem và lựa chọn xử lý tiếp theo

Reporter empirical query-only tiếp tục tách hai Problem:

| Problem/revision | RUN | accepted | aborted | active | controller coverage | natural/technical |
|---|---:|---:|---:|---:|---:|---|
| `prl-22e670302757c9b7663170e226ed7c26` / rev 1 | 66 | 47 | 16 | 3 | 0/66 | `typed_natural=false`, `technically_accepted=false` |
| `prl-e918c7d33e70c2d304d0797e11b05fcb` / rev 2 | 39 | 16 | 10 | 13 | 0/39 | `typed_natural=false`, `technically_accepted=false` |

Toàn cục vẫn `observed_problem_revisions=3`, confirmed resolved `0`,
independent user outcome `3/49`, missing/incomplete observation `66`,
`n5=COLLECTING`, `n10=COLLECTING`, `causal_claim_allowed=false`. P4 còn
`COLLECTING` với 98 representative terminal tasks nhưng 0 repaired task; P5
đang `EPOCH_HARD_STOPPED`, chưa có `experiment_start_ready` hay automatic start.

Sự lựa chọn hiện tại là giữ packaged bundle/agent/Recovery Host cùng identity,
giữ role `central_executor` và central route đã xác thực; source `main` chỉ là
authority build/verify. Patch mode-aware Supervisor hiện có trong working tree
cho phép `development` dùng đúng Python/agent của source và `packaged` dùng
đúng resources packaged, truyền `--runtime-mode` theo manifest. Patch này cần
focused test và reinstall proof trước khi coi development auto-resume là đường
acceptance chính thức; không trộn agent packaged với host development.

### 15.6. Checkpoint wave

```text
COMPLETED:
  controlled authenticated stop -> exact PID/start-token handoff
  packaged Supervisor spawn -> one-shot full-clean refresh
  runtime/epoch/route/package identity readback
  canonical ledger integrity and Problem metrics read-only evidence

CURRENT:
  branch=main
  HEAD=44f4897361951076e714209cd508bbcbdcb94ece
  origin/main=44f4897361951076e714209cd508bbcbdcb94ece
  runtime=RUNTIME_RECOVERY_VERIFIED
  acceptance=PRODUCT_ACCEPTANCE_OPEN
  problems=OPEN (rev 1 and rev 2 remain separate)

BLOCKER / OPEN:
  strict connector receipt, workspace_context, reboot/logon/Machine B,
  authorized fault injection, natural-use, independent outcome,
  criterion coverage/disposition and closure authority

NEXT ACTION:
  validate the mode-aware Supervisor patch, stage the complete volatile
  .coding-tools evidence tree with a fresh delivery snapshot, run all history/
  secret/index guards, then commit and push this evidence wave on main.
```

## 15.7. Post-delivery checkpoint và handoff-agent safety — 23/09/2026

Wave delivery đã hoàn tất trực tiếp trên `main`:

```text
commit=5c831fc93069fec6a1328ca1114d62838875c566
message=fix: align recovery supervisor runtime modes
origin/main=5c831fc93069fec6a1328ca1114d62838875c566
```

Commit đã bao gồm wave report và kế hoạch tổng thể (phần post-delivery này là
follow-up), `RECOVERY_HOST.md`, patch mode-aware Supervisor/manifest/argv, test fixture development và toàn bộ
snapshot `.coding-tools` được stage qua Backup API. Các guard cuối wave đều
PASS: focused Supervisor `17/17`, lifecycle `71/71`, toàn bộ `npm test`
`1025/1025`, `check:coding-tools-delivery`, `check:coding-tools-history`,
`check:repository-secrets`, `--verify-index` và `git diff --cached --check`.

Sau khi push, một phần bổ sung tiếp tục xuất hiện trong working tree và được
giữ lại ngoài commit để không ghi đè thay đổi đồng thời: Supervisor có helper
`Stop-ControlPlaneAgentForReplacement` và call-site trong `Install-Supervisor`.
Ý định của helper là đọc đúng `data_root`, state PID và lock owner, xác minh
process path cùng command line là `node_agent.py run-connected-agent`, chỉ dừng
đúng agent cũ khi mode/path/hash thay đổi, rồi mới cài Supervisor mới. Nếu
identity không chứng minh được, helper fail-closed; không kill theo tên và
không thay PID tái sử dụng. Focused test hiện tại đã kiểm tra parser/helper
presence, `Get-CimInstance` identity gate và các runtime-mode assertions; chưa
có live install/reinstall proof cho nhánh này.

Working tree sau push vẫn có ba loại trạng thái cần phân biệt:

```text
M  .coding-tools/orchestration/ledger.sqlite3
 M resources/recovery-supervisor/recovery-supervisor.ps1
?? dist-recovery-6d2b0dec/
```

Ledger `M` là runtime drift sau snapshot đã commit, không được chép đè hoặc
reconcile thủ công. Helper Supervisor là thay đổi chưa commit vì xuất hiện sau
delivery snapshot và cần owner/acceptance riêng. `dist-recovery-6d2b0dec/` là
untracked packaged build output, không phải canonical evidence, chưa đưa vào
Git để tránh phát hành nhầm binary; việc dọn artifact cần một quyết định riêng.

Trạng thái kết thúc wave không đổi:

```text
SOURCE_FIX_PRESENT
PACKAGED_RUNTIME_RECOVERY_VERIFIED
RUNTIME_CURRENT_READY (snapshot-bound)
STRICT_CONNECTOR_DISCOVERY_OPEN
PRODUCT_ACCEPTANCE_OPEN
BOTH_PROBLEMS_OPEN
```

Không dùng commit/push này để tuyên bố `LIVE_ACCEPTED`, natural outcome,
reboot matrix, Machine B, fault injection hay đóng `prl-22e...`/`prl-e918...`.

## 15.8. Checkpoint sau khi commit helper handoff — 23/09/2026

Phần helper đã được review ở mức source/parser và focused test, sau đó commit
và push riêng trên `main`:

```text
commit=dd3d49d008d5a7cc0fd7578e4f351537b0a0a36a
message=fix: guard control-plane agent handoff
origin/main=dd3d49d008d5a7cc0fd7578e4f351537b0a0a36a
```

Commit này gồm `Stop-ControlPlaneAgentForReplacement`, call-site trong
`Install-Supervisor`, assertions nhận diện executable/command line và phần
checkpoint Markdown. Focused Supervisor suite vẫn `17/17 PASS`; delivery,
history, secret, staged-ledger index và cached-diff guards đều PASS trước push.
Mục đích là chặn việc trộn connected-agent packaged với host development trong
quá trình reinstall/handoff; đây chưa phải live reinstall proof.

Postflight Git hiện tại:

```text
HEAD == origin/main == dd3d49d008d5a7cc0fd7578e4f351537b0a0a36a
M  .coding-tools/orchestration/ledger.sqlite3   # runtime drift ngoài snapshot
?? dist-recovery-6d2b0dec/                      # build output, chưa track
```

Không còn source/docs helper unstaged. Ledger drift tiếp tục không được
overwrite/reconcile; build output không được commit như release artifact. Runtime
vẫn chỉ là `RUNTIME_RECOVERY_VERIFIED / PRODUCT_ACCEPTANCE_OPEN`, connector
strict discovery, `workspace_context`, reboot matrix, natural-use, outcome và
closure của cả hai Problem đều còn mở.

## 15.9. Recheck sau `2c7fce90` và refresh bị từ chối fail-closed — 23/09/2026

Wave này tiếp tục trực tiếp trên `main`, không tạo worktree và không chạy thêm
refresh khi request trước vẫn còn được đối soát. Trong lúc đọc trạng thái, một
commit source đã được đồng bộ lên cả local và remote:

```text
HEAD == origin/main = 2c7fce90ada3cc5ab7312b8fdb5261f072792f04
message = fix: preserve exact UI suppression across handoff
source worktree = clean (ngoài .coding-tools runtime evidence)
```

Commit trên đã chứa patch suppression/re-arm theo đúng `instance_id` và hai
regression cases: heartbeat của cùng UI instance không tự xoá suppression;
UI instance mới mới được coi là explicit re-arm signal kể cả khi epoch đang
`VERIFYING`. Đây là source/focused-proof change đã publish; không gộp nó với
runtime acceptance.

### Runtime refresh boundary

Refresh đã chạy trước wave này kết thúc bằng lỗi chính thức:

```text
DEV_UI_REFRESH_POSTFLIGHT_FAILED
Full-system refresh did not prove fresh Recovery Host, MCP, Tunnel, UI and activation-epoch identities.
```

Readback sau khi process terminal:

```text
full-clean epoch = activation-mud5ulma-b78e78a8c66f46f34d60ec60d348b4d6
expected disk revision = 94ea711860aba7b21527b9b081744a8e5b6d8dc519b6de6ebf8f53425f00eb00
Recovery Host PID = 34168
host running revision = c53f5f524bc8b97fcc6fa1d3264ea84ada498244a3d385d8a075c42fb33f3ab6
state = UPDATE_INCOMPLETE
admission_open = false
current_for_full_clean = false
full_clean_capability_available = false
```

`dev-ui-lifecycle status` đồng thời chiếu UI hiện hữu nhưng không usable:

```text
components_ready = false
fully_ready = false
runtime_update_incomplete = true
connector_state = CHANGED_NEEDS_DISCOVERY
connector_rediscovered = false
connector_refresh_required = true
```

Đây là source/package/runtime drift thật, không phải lý do để hạ guard hoặc
kill/spawn lặp. Strongest current state là
`RUNTIME_UPDATE_INCOMPLETE + ADMISSION_CLOSED`; không dùng outer/old READY,
`/healthz`, test xanh hoặc host liveness để nâng thành `LIVE_ACCEPTED`.

### Controlled ledger recovery boundary

Controlled evidence-only recovery trước đó (section 16.34 của kế hoạch tổng
thể) đã apply một lần với rollback backup, exact pointer CAS và postflight
integrity/event-chain. Wave này **không apply lần hai** vì:

1. canonical ledger hiện đã chứa ba RUN historical và tail evidence đã được
   nối; không còn một `missing RUN allowlist` mới để replay;
2. các candidate/receipt cũ không bind với snapshot hiện tại; dùng lại sẽ vi
   phạm exact physical/logical hash guard;
3. runtime vẫn chưa có quiesce receipt mới chứng minh writer ownership bằng
   `0` và refresh vừa đóng admission ở lớp activation, nên không được tạo
   quiesce giả hoặc gọi `apply` với `runtime_stopped=true`.

Immutable Backup-API census mới (không tạo writer, không sửa canonical bytes)
trả:

```text
snapshot_at = 2026-09-22T21:11:11.848Z
physical_sha256 = cf85a6e1bc084ebe7837b9cb87a31ed21a4448e31d831ddd36beb9e54b4afdf3
logical_sha256 = 4b5f05e5059081bf67c33deb16ae943a7b20630b9f29b3c952d17bf9cce57769
schema_version = 12
integrity_check = ok
foreign_key_check_rows = 0
mutated_canonical_ledger = false
ordinary_active_runs = 17
p5_epochs = 6
stale_background_operation_residues = 0
unbound_live_resource_residues = 0
```

Hash mới chỉ là snapshot quan sát; nó không phải receipt cho một canonical
switch mới và không được trộn với candidate cũ.

### Metrics read-only cho hai Problem và toàn app

Các reporter chính thức cùng snapshot immutable ghi nhận:

| Chỉ số | Giá trị | Cách diễn giải đúng |
| --- | ---: | --- |
| SQLite / FK | `ok` / `0` | Causal ledger đọc được; không phải runtime/client proof |
| Exact revision binding | `193/211 = 91.4692%` | Còn 18 event không bind exact; descriptive mechanics |
| Criterion-to-proof structural coverage | `34/34 = 100%` | Manifest/proof bridge có cấu trúc; không phải natural outcome |
| Receipt-bound authoritative confirmation | `3/3` | Mẫu rất nhỏ; không suy ra efficacy |
| Independent outcome coverage | `3/49 = 6.1224%` | 46 revision còn thiếu outcome độc lập |
| Natural evidence | `false` | Reporter không tự suy cohort từ timestamp/text |
| Problem revisions | `49` | 7 `OPEN`, 30 `PROVISIONALLY_RESOLVED`, 3 `RESOLVED_CONFIRMED`, 2 `BLOCKED` |
| Right-censored unconfirmed revisions | `37` | Không được gọi là failed hay resolved |
| Restricted TTPR | p50 `589000.3782 ms`, p90 `2129062.2617 ms` | Descriptive stage-union proxy; không phải TTOC |
| P4 shadow population | `100` (98 terminal) | `20` raw patch-repaired nhưng `0` causal-solution repaired; `29` unknown |
| P4/P5 gate | `COLLECTING` / `experiment_start_ready=false` | Chưa được auto-promote policy hay mở treatment |

Đối với đúng hai Problem mục tiêu, joined-ledger audit vẫn giữ số liệu và
trạng thái tách biệt:

| Problem/revision | RUN | Accepted | Aborted | Active | State | Closure evidence |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| `prl-22e670302757c9b7663170e226ed7c26` / rev 1 | 66 | 47 | 16 | 3 | `OPEN` | `typed_natural=false`, `technically_accepted=false` |
| `prl-e918c7d33e70c2d304d0797e11b05fcb` / rev 2 | 39 | 16 | 10 | 13 | `OPEN` | `typed_natural=false`, `technically_accepted=false` |

Không được gộp `66/39 RUN`, không dùng 3 confirmation của revision khác để
đóng hai Problem này, và không coi pointer/evidence continuity là resolution.

### Operator checkpoint và next action

- **Đã hoàn thành:** source patch `2c7fce90` đã ở `main`/`origin/main`; refresh
  thất bại đã được terminalize đúng mã; ledger được census bằng Backup API;
  metrics PRL/P4 được recapture; không có canonical ledger mutation mới.
- **Trạng thái hiện tại:** `SOURCE_PRESENT + FOCUSED_PROOF +
  EVIDENCE_RECOVERY_APPLIED_HISTORICALLY`; runtime mới nhất
  `UPDATE_INCOMPLETE/ADMISSION_CLOSED`; strict connector, `workspace_context`,
  reboot/Machine B, fault injection, natural-use, independent outcome và
  closure authority vẫn mở.
- **Phân loại blocker:** source/package/epoch continuity và activation
  authority; không phải lỗi integrity SQLite, không phải lý do replay ledger.
- **Exact next action:** review focused proof của commit `2c7fce90`, stage
  delivery snapshot mới cho `.coding-tools`, chạy toàn bộ delivery/history/
  secret/index guards và push trực tiếp `main`. Sau đó chỉ một owner-authorized
  packaged activation mới được phép tạo epoch/candidate exact; không apply
  candidate ledger cũ, không gọi connector ACK, không reboot và không đóng
  Problem trước strict discovery + real `workspace_context` + independent
  outcome.

## 15.10. Một refresh có kiểm soát mới hết hạn trong postflight — 23/09/2026

Sau delivery `2e505d41`, Recovery Host đã đạt điều kiện identity đầu vào:

```text
PID = 35616
running_revision = disk_revision = 94ea711860aba7b21527b9b081744a8e5b6d8dc519b6de6ebf8f53425f00eb00
current_for_full_clean = true
full_clean_capability_available = true
```

Theo đúng quy tắc chỉ thử một request, đã gửi một `dev-ui-lifecycle refresh`
duy nhất:

```text
epoch = activation-mud67x1j-36d6d1214646926eb647054603117bda
operation = full-clean-refresh-mud67l9n-da18537154680aa635b74390
initial_state = VERIFYING
```

Process đã terminalize với lỗi chính thức:

```text
DEV_UI ERROR code=ACTIVATION_REQUEST_EXPIRED
The durable activation epoch expired during postflight and remains admission-closed.
```

Postflight không có readiness mới để nâng trạng thái:

```text
epoch_state = UPDATE_INCOMPLETE
admission_open = false
components_ready = false
fully_ready = false
connector_state = CHANGED_NEEDS_DISCOVERY
connector_rediscovered = false
connector_refresh_required = true
```

Đây là **deadline/activation continuity failure**, không phải lỗi SQLite và
không được xử lý bằng cách retry cùng epoch, mở admission bằng tay, hoặc dùng
snapshot `READY` cũ. Recovery Host vẫn current về byte revision nhưng primary
MCP/Tunnel/UI aggregate chưa có proof end-to-end.

### Checkpoint sau expiry

- **Đã hoàn thành:** một refresh có kiểm soát duy nhất đã được terminalize;
  `ACTIVATION_REQUEST_EXPIRED` được ghi nhận; không có request song song,
  không sửa ledger trực tiếp, không ACK connector và không reboot.
- **Ledger:** trạng thái read-only gần nhất vẫn `integrity=ok`, FK `0`,
  `mutated_canonical_ledger=false`; live `ledger.sqlite3` có drift ngoài
  delivery snapshot như chính sách cho phép.
- **Git:** `HEAD == origin/main == 2e505d41`; source/docs đã publish. Chỉ
  runtime ledger drift và `dist-recovery-6d2b0dec/` build output untracked còn
  thấy; build output không phải release artifact và chưa được đưa vào Git.
- **Blocker:** activation request deadline/epoch expiry, strict connector
  discovery, real `workspace_context`, reboot/Machine B, fault injection,
  natural-use, independent outcome và closure authority.
- **Exact next action:** không retry epoch đã hết hạn. Owner phải cấp một
  activation window mới với packaged/source identity exact và deadline đủ dài;
  sau đó mới chạy một refresh mới, đọc `READY`/`admission_open`, rồi mới xin
  current-process `tools/list`/`server/discover`. Hai Problem vẫn `OPEN`.

## 15.11. Route heartbeat bounded và readback READY sau activation — 23/09/2026

Recheck live sau section 15.10 cho thấy epoch `activation-mud6y13k-10d3877ba21943bffbd3a5edcc06d471` vẫn tồn tại nhưng route evidence đã quá TTL 60 giây. `runtime.snapshot` chỉ rõ:

```text
Recovery Host PID/instance = 41648 / 296aa20eea59f9b3c13e54940070a6b1
Recovery Host revision     = 94ea711860aba7b21527b9b081744a8e5b6d8dc519b6de6ebf8f53425f00eb00
MCP running == disk        = a49891f8e6bff0bfb2d49284ff85d8cd73946508f59ff0a7b8ebd8ed0339dfe5
central_status_reason      = CENTRAL_ROUTE_EVIDENCE_STALE
central_connected          = false
authority_ready            = false
fully_ready                = false
activation state/admission = READY / false
```

Đây không phải source/package drift mới và cũng không phải SQLite failure: MCP/native vẫn sống, running/disk revision khớp, nhưng route evidence one-shot đã hết hạn. Theo đúng boundary hiện hành, không gọi lại `dev:refresh`, không mở admission bằng tay và không bật Tunnel chỉ để đổi trạng thái.

Đã chạy **một** `runtime-heartbeat` bounded, read-only đối với ledger và không cấp write/exec authority. Kết quả trực tiếp của heartbeat là:

```json
{"readiness":"degraded","reason":"mcp_revision_unproven","runtime_identity":"unreported","runtime_state":"CURRENT","fully_ready":"false","policy_state":"enabled","route_evidence":"fresh"}
```

`degraded/unreported` ở thời điểm heartbeat là đúng: node agent chưa được phép tự biến một runtime chưa chứng minh identity thành ready. Sau khoảng 8 giây để Recovery Host supervision đọc route evidence mới, `npm run dev:status`, `full-clean-activation --status` và authenticated readback đã hội tụ:

```text
epoch state/admission      = READY / true
Recovery Host current      = true; full_clean_capability_available=true
mcpRunning/nativeAlive     = true / true
componentsReady/fullyReady = true / true
runtime_update_incomplete  = false
centralConnected/authority = true / true
tunnelRequired/running     = false / false
connector state             = CHANGED_NEEDS_DISCOVERY
connectorRediscovered      = false
connectorRefreshRequired   = true
contract SHA-256            = bc44c044a0b08dfdea80b8ba0dfcc080e180e21a5460dbf9726b49ac1fa769b0
```

`central_executor` không yêu cầu Windows Tunnel; `tunnelRunning=false` là bằng chứng đúng thiết kế, không phải lỗi cần sửa. UI development cũng đang `CURRENT` với PID `16916`, UI running/disk revision khớp `1c252e835ef58a9862aeee4c0585416cdea4ec3122caf640c627f149ff20e73a`.

### Giới hạn proof sau heartbeat

`collect-boot-runtime-observation.js --workspace E:\DEV\Codex-web` trả `status=OBSERVED`, nhưng vẫn giữ:

```text
authority_granted = false
live_accepted     = false
client            = null
missing           = REAL_CLIENT_WORKSPACE_READ,
                    CLIENT_DELIVERY_CONFIRMATION,
                    CLIENT_DISCOVERY_PROVENANCE,
                    BOOT_BEFORE_AFTER,
                    PACKAGE_EXECUTABLE_SUPERVISOR_HASHES,
                    CENTRAL_BINDING_POLICY_RECEIPT,
                    ATTEMPT_HISTORY_STARTUP_INTENT
```

Điều này chứng minh local Recovery Host/route/readiness, không chứng minh connector ChatWeb đã nhận MCP. Phiên Codex hiện tại không expose Coding Tools MCP namespace; `list_mcp_resources` và `list_mcp_resource_templates` đều trả rỗng. Do đó chưa thể thực hiện current-process `tools/list`/`server/discover` một cách hợp lệ và không được thay bằng local HTTP probe, `runtime-heartbeat`, persisted compatibility flag hoặc ACK thủ công.

### Đánh giá phần app còn phải bổ sung hoặc hoàn tất

| Ưu tiên | Phần cần xử lý | Bằng chứng hiện có | Điều kiện hoàn tất bắt buộc |
| --- | --- | --- | --- |
| P0 | Strict connector discovery | Contract SHA hiện tại, local runtime READY; chưa có discovery receipt | ChatWeb connector thật gọi `tools/list` hoặc `server/discover`, trả đúng 8 tool public, receipt bind PID/process instance, MCP server instance, epoch và contract SHA |
| P0 | Real workspace bootstrap | `client=null`, `workspace_context` chưa được quan sát | Một request thật trên `E:\DEV\Codex-web` có `completed=true`, `workspace_accessed=true`, request/workspace generation và server/process identity khớp |
| P1 | Route heartbeat lifecycle | Heartbeat one-shot làm readiness READY chỉ trong TTL; sau đó lại stale | Thiết kế logon-scoped/interactive heartbeat có expiry/fail-closed rõ ràng, không cấp authority ngầm; có focused test và receipt fresh sau idle/reconnect |
| P1 | Handoff P1/P2 | Guard source đã có; chưa có live reinstall proof | Reinstall/handoff trên đúng packaged bundle, chứng minh semantic stop refusal không terminate và rollback giữ nguyên service-off ban đầu |
| P1 | Reboot oracle | Receipt cũ chỉ kiểm boot/PID/hash | Oracle mới phải kiểm supervisor, packaged host, MCP/native/Tunnel theo role, revision/epoch, connector freshness, `fullyReady`, và real `workspace_context` |
| P2 | Evidence continuity | Ledger hiện integrity/FK tốt; một số generated report lịch sử chưa nối lại được vào snapshot hiện tại | Supported export/receipt linking bind exact RUN/WAVE/checkpoint; không insert/reconcile trực tiếp vào SQLite |
| P2 | Natural outcome | Independent outcome `3/49`, natural evidence=false | Mỗi Problem có natural-use thật, outcome oracle độc lập, 48 giờ chỉ tính khi canonical capsule còn yêu cầu và có bằng chứng thực |
| P2 | Policy/knowledge loop | P4 `COLLECTING`, 20 raw patch-repaired nhưng 0 causal-solution repaired, 29 unknown | Hoàn thiện typed repair/lesson linkage, missingness và P4/P5 gate; không auto-promote routing/policy từ shadow data |
| P3 | Release/remote boundary | Runtime local proof có, package/production chưa claim | Exact package/installer/deployment identity, strict discovery và release gate riêng; không suy từ `fully_ready` hay Git push |

### Checkpoint điều hành

- **Đã hoàn thành:** route evidence được làm mới một lần có kiểm soát; activation epoch hiện `READY/admission_open=true`; local MCP/native/central route đã hội tụ và byte identity được đọc lại; không sửa ledger và không tạo ACK/outcome giả.
- **Trạng thái mạnh nhất hiện tại:** `RUNTIME_RECOVERY_VERIFIED + CENTRAL_ROUTE_READY + PRODUCT_ACCEPTANCE_OPEN`.
- **Blocker thật:** current ChatWeb connector discovery và real `workspace_context`; sau đó mới có thể mở reboot/logon/Machine B, fault injection, natural-use và closure.
- **Exact next action:** giữ epoch hiện tại, dùng connector được hỗ trợ để lấy một discovery receipt bind exact identity; nếu connector không xuất hiện trong phiên vận hành, ghi `WAITING_FOR_SUPPORTED_CONNECTOR` và dừng, không retry refresh/ACK.

## 15.12. Read-only recheck sau khi route TTL hết hạn lần nữa — 23/09/2026

Sau khi push commit của section 15.11, không gọi thêm heartbeat, refresh, ACK
hay reboot. Read-only recheck lúc `2026-09-22T21:56:03Z` cho thấy MCP và
Recovery Host vẫn current nhưng route evidence one-shot đã hết TTL lần nữa:

```text
UI state                    = CURRENT (PID 16916)
Recovery Host               = PID 41648, instance 296aa20eea59f9b3c13e54940070a6b1
Recovery Host running/disk  = 94ea7118… / 94ea7118…
MCP running/disk            = a49891f8… / a49891f8…
components_ready            = true
fully_ready                 = false
runtime_update_incomplete   = true
central_connected           = false
authority_ready             = false
activation state/admission  = READY / false
connector                   = CHANGED_NEEDS_DISCOVERY, rediscovered=false
```

`collect-boot-runtime-observation` vẫn trả `status=OBSERVED`,
`authority_granted=false`, `live_accepted=false`, `client=null`. Đây là hành vi
fail-closed dự kiến khi heartbeat không được duy trì; không phải bằng chứng
MCP chết, source drift hay ledger corruption. Readback trước đó
`READY/admission_open=true` chỉ có hiệu lực trong observation window của route
evidence, không được kéo dài thành present-tense product acceptance.

**Checkpoint:** trạng thái mạnh nhất hiện tại là
`RUNTIME_RECOVERY_VERIFIED_AT_PRIOR_READBACK + ADMISSION_CLOSED_CURRENT +
PRODUCT_ACCEPTANCE_OPEN`. Route heartbeat lifecycle vẫn là gap P1, nhưng không
được giải quyết bằng loop heartbeat vô hạn trong wave discovery. Exact next
action không đổi: lấy current-process strict discovery từ connector được hỗ trợ;
nếu connector không expose, terminalize `WAITING_FOR_SUPPORTED_CONNECTOR`.

## 15.13. Đã sửa root cause connected-agent development và gate activation — 23/09/2026

Read-only process inspection trước patch cho thấy Supervisor vẫn healthy nhưng
connected-agent development dùng command line:

```text
...\resources\native-python\python.exe -I ...\control_plane\node_agent.py
run-connected-agent ... --node E:\DEV\Codex-web\node_modules\electron\dist\electron.exe
--runtime-mode development
```

Với `runtime-mode=development`, `node_agent.py` gọi trực tiếp
`[args.node, scripts/dev-ui-lifecycle.js, status]` và chỉ đặt
`ELECTRON_RUN_AS_NODE=1` ở packaged adapter. Reproduction với đúng command/path
trên trả `runtime_status_unavailable`; cùng command với `node.exe` thật trả
được status. Đây là typed cause của heartbeat route bị stale, không phải
`ledger.sqlite3` corruption và không phải lý do để bật Tunnel.

Source patch trong `resources/recovery-supervisor/recovery-supervisor.ps1`:

* `packaged` pin `--node` vào chính Recovery Host executable;
* `development` resolve absolute `node.exe` một lần tại Supervisor install,
  ghi `control_plane_node_path` cùng `control_plane_node_sha256` vào manifest;
* `development` truyền thêm `--data-root` đúng profile vào connected-agent để
  `runtime_heartbeat()` có thể đọc policy projection; packaged không nhận
  `--data-root` vì packaged policy root phải do adapter tự derive;
* preflight kiểm path/hash của Python, agent và Node; mismatch hoặc manifest
  thiếu identity làm agent `manifest_legacy`/`integrity_unproven` và không spawn;
* replacement nhận biết Node identity **và argv contract** thay đổi để không giữ
  lại agent cũ; development yêu cầu đúng `--data-root`, packaged cấm cờ này;
* không fallback sang Electron executable hoặc PATH trong heartbeat.

Focused proof: `node --test tests/recovery-supervisor.test.js` **17/17 PASS**;
test mới chứng minh development executable giả lập Electron khác `node.exe`
nhưng `--node` nhận đúng `process.execPath`, development có `--data-root`, còn
packaged giữ executable host và không nhận cờ data-root.
`git diff --check` PASS. Chưa coi đây là live recovery proof: installed
Supervisor chưa được reinstall/activation sau source patch trong section này.

**Checkpoint:** source/focused-proof đạt; runtime hiện tại vẫn có thể đang chạy
manifest cũ và route evidence có thể stale. Exact next action là commit/push
source+test+docs trực tiếp trên `main`, sau đó reinstall Supervisor bằng lệnh
được hỗ trợ, capture command line/hash mới và quan sát tối thiểu hai chu kỳ
heartbeat. Chỉ nếu route evidence tự refresh mới quay lại strict discovery;
không ACK thủ công, không sửa byte ledger, không reboot trong wave này.

## 15.14. Live activation proof sau reinstall Supervisor — 23/09/2026

Sau commit `eb244709` và `npm run recovery:supervisor:install`, replacement
đã dừng agent cũ còn giữ lock và publish process mới:

```text
Supervisor PID       = 50720 (parent Task Scheduler, state healthy)
Connected-agent PID  = 33404, parent PID = 50720
Python               = E:\DEV\Codex-web\resources\native-python\python.exe
Agent                = E:\DEV\Codex-web\control-plane\control_plane\node_agent.py
--node               = C:\Program Files\nodejs\node.exe
--runtime-mode       = development
--data-root          = C:\Users\Admin\AppData\Roaming\web-mcp-assistant
```

Manifest mới có `control_plane_node_path` và `control_plane_node_sha256`
(`3602f2bb…`); lock PID khớp `33404`. Route evidence tự cập nhật qua hai chu
kỳ độc lập, không gọi one-shot heartbeat trong lúc đo:

```text
route mtime               = 22:33:04 (baseline)
route mtime/observed_at   = 22:33:35 / 1790116415472
route mtime/observed_at   = 22:34:06 / 1790116446528
runtime_readiness       = degraded (mcp_revision_unproven)
policy_state            = enabled
```

Đây là `LIVE_CONTROLLED_ACTIVATION + HEARTBEAT_LIFECYCLE_PROOF`, xác nhận
đúng root cause đã sửa. Nó chưa nâng product acceptance: `dev:status` vẫn
`components_ready=true`, `fully_ready=false`, `runtime_update_incomplete=true`,
`connector_state=CHANGED_NEEDS_DISCOVERY`, `connector_rediscovered=false`;
`full-clean-activation --status` cho thấy Recovery Host running `94ea7118…`
nhưng disk `4158c76a…`, `current_for_full_clean=false`, `admission_open=false`.
`collect-boot-runtime-observation` vẫn là `OBSERVED`, `authority_granted=false`,
`live_accepted=false`, `client=null`; không có strict discovery hoặc real
`workspace_context`.

Ledger readback cùng thời điểm dùng Backup API/query-only, không mutate
canonical bytes: physical SHA `9bad16da…`, logical SHA `0e0b3a9c…`, schema `12`,
integrity `ok`, FK `0`, `ordinary_active_runs=17`, `p5_epochs=6`,
`projection_drift=false`, stale background residues `0`, unbound live resource
residues `0`. Không có candidate exact/bound mới, nên **không apply evidence
recovery lần hai** và không chỉnh byte `ledger.sqlite3`.

**Checkpoint:** heartbeat lifecycle và Supervisor replacement đã đạt proof live;
Problem `prl-22e…`/`prl-e918…` vẫn `OPEN`. Exact next action là giữ bundle/epoch
fail-closed, lấy strict connector discovery bằng client được hỗ trợ; sau đó mới
real `workspace_context`, reboot matrix và natural-use/outcome. Không bật Tunnel
chỉ để làm xanh `fully_ready`, không ACK thủ công và không gộp hai Problem.

## 15.15. Recheck sau wave oracle/ledger — 23/09/2026

Wave này chỉ đọc và chạy focused oracle trên checkout `main`; không tạo
worktree/branch, không reset/clean, không refresh/reboot/Tunnel/ACK.

```text
HEAD/origin/main          = cab69630882c4f5d9dbfc41de83ae8301d6721ae
Supervisor                = PID 50720, healthy
Connected-agent           = PID 33404, parent=50720, development + data-root
Recovery Host             = PID 41648 / instance 296aa20eea59f9b3c13e54940070a6b1
Recovery Host              = running 94ea7118… / disk 4158c76… / update_pending=true
Coding MCP                = running a49891f8… / disk a49891f8…
activation                = READY / admission closed
runtime                   = mcp=true, native=true, tunnel=false, fully_ready=false
connector                 = CHANGED_NEEDS_DISCOVERY / rediscovered=false
workspace observation    = OBSERVED, workspace_matched=true, client=null
authority/live accepted  = false / false
```

Ledger được đọc bằng SQLite Online Backup API rồi mở `immutable + query_only`:

```text
snapshot_at      = 2026-09-22T22:43:27.431Z
physical_sha256  = e73b7010c428a7108719205cfccb93e0c3f2e95cc468b29428abb5cd8b211b19
logical_sha256   = cb46731ba30e2ef05aa0946a79ba7b67262d32559dda610b92bc5dcdc5f75243
schema/integrity/FK = 12 / ok / 0
ordinary_active_runs = 17; p5_epochs = 6
projection_drift = false; stale/unbound residues = 0 / 0
```

Exact revision counts ở snapshot mới nhất là `prl-22e…` rev1: `47 accepted /
16 aborted / 3 active = 66 RUN`, và `prl-e918…` rev2: `16 / 10 / 13 = 39 RUN`;
cả hai vẫn `OPEN`. Không gộp với snapshot cũ `63/39`, không chuyển active
durable thành process đang sống và không dùng generated projection thay
canonical ledger.

Focused suite:

```text
node --test tests/boot-acceptance.test.js \
  tests/boot-runtime-observation.test.js \
  tests/recovery-bootstrap.test.js
93 passed, 0 failed
```

Kết quả chỉ đóng local source/oracle proof. Runtime vẫn chưa có current-process
connector receipt; `list_mcp_resources` và `list_mcp_resource_templates` trong
phiên Codex đều rỗng. Vì vậy gate strict giữ
`WAITING_FOR_SUPPORTED_CONNECTOR`, không dùng health/heartbeat/ACK/local probe
để thay `tools/list` hoặc `server/discover`, và không gọi app là usable.

**Operator checkpoint:** recheck đã hoàn thành, canonical ledger bytes không bị
mutate, dirty `.coding-tools/**` được giữ nguyên theo retention invariant; thư
mục `dist-recovery-*` không đưa vào commit. Exact next action không đổi: khi
connector được hỗ trợ xuất hiện, bind discovery vào PID/process instance/MCP
server instance/activation epoch/contract SHA, rồi gọi real `workspace_context`
trên `E:\\DEV\\Codex-web`. Nếu không có connector, dừng ở
`WAITING_FOR_SUPPORTED_CONNECTOR`; hai Problem tiếp tục `OPEN`.

## 15.16. Controlled full-clean activation sau khi freeze epoch — 23/09/2026

Đã chạy đúng lifecycle command `npm run dev:refresh` một lần sau khi Recovery
Host đã được thay bằng Supervisor đúng argv contract. Guard đã hoàn tất full
handoff và không có kill/spawn thủ công:

```text
epoch       = activation-mud9uu5m-8fbccc1580217bcc2104000d8f77e0ce
operation   = full-clean-refresh-mud9uiqm-2aedc95e177f56320ff05012
host        = fcf3bed2359aadc93046dc3b1a12ccdf
ui          = 568b52ff5f1b5e646cee786870fea3f4
mcp_pid     = 48220
activation  = READY / admission=open
fully_ready = true
mcp         = ready
tunnel      = not-required (central_executor)
connector   = pending / CHANGED_NEEDS_DISCOVERY
focused lifecycle/oracle suite = 148 passed, 0 failed
```

Sau activation, running/disk revision đã khớp:

```text
Recovery Host = 4158c76… / 4158c76…
Coding MCP   = a49891f… / a49891f…
MCP/native   = true / true
central route/authority = true / true
update_incomplete = false
connector_rediscovered = false
connector_refresh_required = true
```

Đây là proof cho runtime continuity và `fully_ready`, không phải proof
connector/client. `collect-boot-runtime-observation` vẫn không có `client` và
giữ `authority_granted=false`, `live_accepted=false` do thiếu real client
workspace read và discovery provenance. Phiên Codex không có Coding Tools MCP
namespace; hai resource discovery calls đều rỗng. Do đó không ACK thủ công,
không dùng local probe/health/heartbeat thay `tools/list` hoặc `server/discover`.

Ledger ngay sau activation vẫn `integrity=ok`, FK `0`, projection drift/residue
`false/0/0`; physical SHA `252d9e5bf9c9492c8bcecca2ea6d9e55531480416000987ed7f377d6bcf02e4`,
logical SHA `5826f4eb01e3939889ca5169a2f5f9300fda4b5adb5f35f008bfb29bbc55ffad`.
Hai Problem giữ nguyên `OPEN` với `66` và `39` RUN theo đúng revision.

**Operator checkpoint:** `LIVE_CONTROLLED_ACTIVATION` và
`FULL_RUNTIME_READY` đã đạt; `STRICT_REDISCOVERED`, real `workspace_context`,
reboot/Machine B/fault/natural-use và independent outcome chưa đạt. Exact next
action vẫn là connector được hỗ trợ thực hiện discovery và workspace read; nếu
connector không xuất hiện, giữ `WAITING_FOR_SUPPORTED_CONNECTOR` thay vì lặp
refresh.
