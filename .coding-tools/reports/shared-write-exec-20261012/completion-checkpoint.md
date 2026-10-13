# Hoàn thiện ghi và chạy lệnh trên máy mới — 12-10-2026

**Status: COMPLETED_WITH_PROOF_BOUNDARIES** — r5b READY, shared MCP
create/read/patch/readback/exec PASS, tunnel healthy. ChatGPT UI refresh được
remote discovery/tools-list HTTP 200 corroborate; persisted imported schema
và actual model call chưa được quan sát.

## Máy, repository và bản vận hành

- Máy `DESKTOP-63643J4`, repository `E:\DEV\Codex-web`, profile
  `C:\Users\Admin\AppData\Roaming\web-mcp-assistant`, role `central_executor`.
- Source HEAD `main @ 7999c4151cb501db86f2e4d0a2275d33fc248324`; có các sửa
  cục bộ của những wave trước và wave này, chưa commit/push. Không suy ra
  GitHub đã chứa các sửa đó. Final `ls-remote origin` lúc khoảng **12:07 +07**
  xác nhận remote HEAD và `main` đều đúng HEAD này.
- Candidate `dist\windows-candidate-mxc-wsb-cbe1774-machine-write-exec-1012-r5b\win-unpacked`.
  Epoch `activation-mv4r64ul-235cac58cc9592bd08ffc95abe94a111` đạt
  **READY / OPEN lúc 11:30:04.722 +07**; central route và projection rebuild
  đã xác minh. Host PID `31528`, native process `ev_bVSX46CWc8WG5`, server
  instance `XobFwIqZETgu9SLo`.
- EXE SHA256 `960adeec5aebad36374f556718d738ca50482540f427bf62cbc3178fe4078f5f`;
  ASAR SHA256 `3e5b87823089d08058620fdda56e3c410e92387c258add1ec2beeae6e4c771ba`.

## Thay đổi và validation

| Phạm vi | Thay đổi | Bằng chứng mạnh nhất hiện có |
|---|---|---|
| Quyền và Sandbox | Kiểm tra trạng thái/đăng ký/bật đọc-sửa không tự tạo VM; nút riêng xác nhận trước probe thật để bật exec; nút kiểm tra nâng cao cũng xác nhận | 70 focused source tests PASS; observer chạy từ r5b ghi zero Sandbox launches |
| Probe và policy | Probe bắt buộc trước cài exec, gộp lời gọi đang chạy cùng root/hash, cache thành công 5 phút; cache không là proof VM đang chạy; policy hiện hành vẫn xét fresh authority | Tests về cache expiry, đúng root/hash, concurrent/cancel/decline và authority reuse PASS |
| Đóng gói | r5b chứa source hiện hành và adapters/resources khớp | 91 app files, 298 resource files, 9 adapters; sanitation 332 entries; isolated smoke PASS |
| Admission trên svhome | Overlay một `store.py` cho scoped artifact/document lane theo pilot hiện có | Official release verifier 38 files/schema29, SQLite integrity `ok`; 37 release files khác byte-identical |

Source UI: `renderer/app.js`, `renderer/index.html`, `electron/main.js`,
`electron/services/controlPlaneEnrollment.js`. Focused tests:
`tests/folder-permission-editor.test.js`, `tests/control-plane-exec-sandbox.test.js`,
`tests/control-center-manager.test.js`. Server changes:
`control-plane/control_plane/store.py`, `control-plane/tests/test_store.py`.
Maintained guidance: `docs/CURRENT_STATE.md`. Sửa Sandbox cold-start,
Supervisor và activation của wave trước được giữ nguyên.

Evidence: [70 tests](../sandbox-explicit-setup-20261012/focused-tests.txt),
[package parity](r5-candidate-verification.json), [smoke](r5-candidate-smoke.txt),
[status-only observer](r5-status-only-observation.json),
[runtime identities](r5-exact-runtime-identities.json).

## Canary gốc: scope error đã reconcile bằng chứng thật

1. `document_create` và đọc lại thành công qua shared MCP, cùng original
   action/attempt/runtime identity. File trong `.coding-tools/reports` giữ
   nội dung tạo ban đầu.
2. PATCH action `act_051f354f679c45779fc32dab793e43c6`, attempt
   `try_764317ee30904d34ab41452a7c25bfb7`, nhắm vào `.coding-tools/**` bị native
   guard `PROTECTED_PATH_WRITE` từ chối trước `apply_changes_and_verify`.
   Canonical RUN `4ea601f3f7154ecda879a6986a5d7f41`, WAVE
   `2b840f59702f4d4ba34e2b3f96496ab5` chuyển sang REPLAN và thu hồi write lease.
   Generic bridge error ban đầu khiến central receipt là unknown; đây là lỗi
   chọn phạm vi canary, không phải bằng chứng runtime đã sửa file thành công.
3. Observer có node authentication xác minh original native idempotency,
   audit/guard event, policy/runtime/package hashes, resource census và
   original central attempt; sau đó **append failed terminal receipt** qua
   Node API. Không sửa DB trực tiếp, không thay journal/native audit, không
   replay action, không tạo semantic acceptance. Unknown receipt gốc còn nguyên.
4. Supported writer release và task close thành công. Census sau cleanup:
   **0 open tasks / 0 unreleased writers / 0 unsettled current-generation actions**.
   Đây là census sau cleanup gốc; canary thứ hai có lifecycle riêng.

Evidence: [original receipt log](shared-write-exec-receipt-3d0747150e2141afa3534c51a4a9122b.ndjson),
[native failure](original-patch-native-failure-observation.json),
[genuine reconciliation](original-patch-failure-reconciliation-receipt-1791780720527.json),
[original cleanup](original-canary-task-cleanup-receipt.json).

## Canary r2: original create/read/patch/readback/exec PASS

Attempt `682718c387c14047828a0a2a02faf57e` chạy qua shared MCP service thực,
target `tests/fixtures/new-machine-shared-write-proof-20261012.txt`. Cả năm
original actions có completed receipts với exactly one delivery attempt:

| Lane | Original action | Completed receipt |
|---|---|---|
| Create | `act_afb4cda9bb924693bef381d92dda467c` | `rcpt_3526b1c0246749d28cf297edc3758888` |
| Read initial | `act_df2014d6ddf64b0ca6b810d7517defdb` | `rcpt_ca33e2e27e9748bfb3f8708b7c78ae69` |
| Exact patch | `act_f1b4d13e5c8949378edbe2626ad1271a` | `rcpt_8cd4ec63fb0b4d95856ec40095269708` |
| Read final | `act_c3020ecabb85458aa2ac9ec17afbcd2a` | `rcpt_fbfef592011e4e7c99254822bdd78a23` |
| Exec | `act_e054bbb4d7854e51b23d792e2774b293` | `rcpt_f288ecb5829040ffab234d66aa08585c` |

- Final readback và original Job kiểm tra đúng 63 byte, SHA256
  `99a756fdabac6c640b5752ae4ca6088301c1eff6318840a6377f6c262d42f8fa` và marker
  `NEW_MACHINE_SHARED_MCP_WRITE_EXEC_20261012_OK`.
- Patch canonical RUN `4967dd953ce74b5d97cbf01aad827139`, WAVE
  `d4b12a2aff6f4e4eb7dd06de65833aab`. Local semantic acceptance vẫn
  **pending**, không được tự accept để làm đẹp báo cáo.
- Original exec Job `65c2908a7371487cbfbb22ee1d60c262`, command
  `rGvwOG9A-yEHoioWxEvkl_6p`, exit **0**; runtime identity giữ đúng r5b epoch,
  native process và server instance. Không redispatch command khi observe.
- Task `task_e9aa123232834a9a85008e920de7e12e` đã đóng; writer release được
  xác minh. Final report `ok=true`, `marker_verified=true`,
  `unresolved_original_actions=[]`, `requires_reconciliation=false`,
  `semantic_acceptance_performed=false`.

Evidence: [r2 original receipts](shared-write-exec-receipt-r2-682718c387c14047828a0a2a02faf57e.ndjson).

## Operations ngoài repository

- Đã retire exact r4 runtime theo supported lifecycle, install production
  Supervisor cho r5b, launch UI và refresh/activate r5b. Các history/acceptance
  guard được giữ. Không reboot Windows.
- Đã deploy và restart `codex-control-plane.service` trên target người dùng
  cho phép `svhome / 100.116.112.22`. Package serving
  `sha256:5370e6ce030e72514b664b771f400437d337e7c5eb1c39b1ac90748662c3ceb0`,
  PID `921509`, baseline `9cae1044…` với overlay một file. Backup database chỉ
  ở remote protected location; SQLite integrity `ok`.
- Pilot/binding/grants không đổi bởi deployment này. Decision
  `pilot_dfb3174078d842299c41c6638830e505`, binding
  `bind_71661b1046884174b01c99af5f8546aa`, generation
  `generation_a420c8bfcfcb4e42b5bb7fc5e5cec097`. Cấu hình renewal đã duyệt
  trước vẫn trỏ pilot này; expiry quan sát `13-10-2026 06:25:31.435 +07`.
- Không commit/push/tag/public release. Không public installer mới.
- Đã restart exact MCP tunnel trên svhome: PID `5383 → 924785`, child
  `5503 → 924804`; actual main probe `ok`, channel enabled, `/healthz` và
  `/readyz` HTTP 200 cùng first control-plane poll `ok`. Canonical credential,
  pilot/grants, server PID `921509` và schema giữ nguyên. Startup wait sử dụng
  supported `30s`; protected config backup chỉ ở remote.
- Đã thao tác Settings của connector trong ChatGPT: bấm refresh (disabled rồi
  enabled, không error toast) và lưu description đúng tính năng
  “Đọc, ghi file và chạy lệnh Windows trong sandbox theo quyền của thư mục đã
  chọn trong ứng dụng.” Không đổi quyền hoặc gửi tin nhắn. UI không trả receipt
  xác nhận catalog/schema mới. Current canonical tunnel client ghi nhận đúng
  một remote `server/discover` và một `tools/list` HTTP 200 kể từ restart
  **11:58:51 +07**, corroborate thao tác refresh. Counters không có timestamp
  riêng của từng request và không chứng minh persisted imported schema.

Evidence: [server deployment](server-deployment-receipt.json),
[tunnel restart](reviewed-tunnel-restart-receipt.json),
[post-tunnel surface snapshot](post-tunnel-final-server-surface.json),
[actual UI receipt](chatgpt-ui-update-observation.json),
[remote refresh correlation](actual-chatgpt-refresh-tunnel-correlation.json),
[saved connector description](chatgpt-plugin-updated.jpg).

## Trạng thái cuối đã quan sát

- Local read-only observer lúc **12:03:23 +07**: `ok=true`, `fullyReady=true`,
  authority/central connected, update incomplete false; same READY/open epoch,
  exact Host và byte-identical package, descriptor/epoch stable.
- Zero active tool calls, commands, managed processes, background work hay
  agent lanes. SQLite integrity `ok`, foreign-key-check zero.
- Four awaiting-acceptance RUNs (gồm r2 patch) và 18 stale history candidates
  (gồm REPLAN của canary đầu) được giữ nguyên. Native census cho thấy
  `ledger_idle=true`; service đang sống nên stop/retire gate vẫn có
  `live_runtime_state_process` guard, không phải active Job.
- OS vẫn thấy hai process `WindowsSandboxServer` và
  `wxc-windows-sandbox-daemon`. Không suy ra zero-Sandbox hay ownership.
- Final server observation: node ready, heartbeat age 13,834 ms, census
  **0 open tasks / 0 unreleased writers / 0 unsettled actions**, SQLite `ok`,
  tunnel ready 200; renewal service success, timer active/enabled.
- Final coding-tools history và secret guards **PASS với 8,846 files**, gồm
  receipt mới và UI image. Final `git diff --check` PASS, không conflicts;
  `main`/HEAD giữ nguyên, mọi sửa cục bộ được giữ và chưa commit/push.

Evidence: [final local observer](final-machine-observation-activation-mv4r64ul-235cac58cc9592bd08ffc95abe94a111-1791781403713.json),
[final server](post-tunnel-final-server-surface.json),
[compact r2 terminal proof](shared-write-exec-r2-terminal-proof-682718c387c14047828a0a2a02faf57e.json).

## Còn lại và hành động tiếp theo

- Source, package, live canonical shared MCP và tunnel đã PASS; actual ChatGPT
  model invocation/catalog acceptance vẫn chưa có bằng chứng. Nếu chat hiện
  tại tiếp tục báo empty exec schema, người dùng thử lại app trong một lượt
  ChatGPT mới để nhận tool catalog hiện hành; không cần cấp lại quyền máy.
- Reboot/logon continuity và installer signed/public chưa được kiểm chứng.
  Windows Sandbox có thể hiện cửa sổ khi probe được yêu cầu rõ hoặc command
  thật; không có headless backend mới.
- Native semantic acceptance không thuộc canary transport này và vẫn pending.
  Giữ lịch sử; không accept/rewrite để làm green trạng thái.
- Final Git/whitespace/history/secret audit đã PASS. Không còn Job canary cần
  theo dõi; bước còn lại phía người dùng là retry app trong fresh ChatGPT turn
  nếu chat cũ vẫn hiển thị empty exec schema, giữ các proof boundaries trên.
