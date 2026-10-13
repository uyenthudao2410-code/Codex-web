# Hoàn thiện máy Windows mới — 12-10-2026

## Kết quả đã chứng minh

- Máy `DESKTOP-63643J4`, repository `E:\DEV\Codex-web`, `main @ 7999c4151cb501db86f2e4d0a2275d33fc248324`.
- GitHub `HEAD` và `refs/heads/main` được kiểm tra lại, cùng HEAD. Các sửa cục bộ chưa commit/push.
- Profile `C:\Users\Admin\AppData\Roaming\web-mcp-assistant`; execution role `central_executor`.
- Candidate đang vận hành: `E:\DEV\Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-machine-coldstart-1012-r4\win-unpacked`.
- Epoch `activation-mv4od6fe-c45648f5d945ceeb7f3640048b0e91b7` tự đạt `READY / OPEN` lúc **10:11:37.093 +07**. Không gọi explicit complete cạnh tranh với startup.
- Host PID `28804`, instance `b97555fece0cd8178c218e80c0b4c89b`; native process `Mmrm0HVhHUpvj9sz`, server `oOu_kV3jhDH_x822`.
- `fullyReady=true`, `centralConnected=true`, `authorityReady=true`, `updateIncomplete=false` được quan sát sau READY.
- Projection rebuild đạt; UI/Host/MCP revision và component epoch đều khớp trong final activation census.

## Sửa source và bằng chứng

| Phạm vi | Thay đổi | Proof |
|---|---|---|
| Sandbox | Rendezvous 150 s, ready 180 s; rebuild ba binary và cập nhật provenance/hash consumers | Probe Sandbox thật với Node/npm/process con PASS; 18 packaging checks, 25 Python checks + 5 subtests PASS |
| Supervisor | Tìm manifest hiện tại trong roaming profile trước, legacy khi current thật sự absent; current malformed/inaccessible fail closed | Focused/lifecycle tests PASS |
| Activation | Một reservation bảo vệ receipt producers của startup, operator, watchdog, bootstrap và auto activation đến admission; equality giữ nguyên | 16 concurrency, 21 regression, 3 real-process E2E PASS |
| Permission fixture | Current facade contract và authority observation fresh | Permission file 36 PASS; Desktop lane 143 PASS |
| Pilot continuity | Chỉ expired bounded read unknown có đầy đủ immutable evidence trên retired generation/revoked binding/closed context cùng owner/device/workspace/principal không chặn generation mới | 8 focused server tests + independent review PASS; history không đổi |
| Evidence retention/reproducibility | Narrow `.gitignore` exception và exact `.gitattributes` LF cho MXC patch | Secret guard và coding-tools history guard PASS, 8713 files tại thời điểm chạy; raw patch hash giữ nguyên |

Các file source/test chính: `electron/services/recoveryHost.js`, `recoveryHostLauncher.js`, `controlPlaneEnrollment.js`; `tests/recovery-host-activation-completion.test.js`, `dev-supervisor-suppression.test.js`, `folder-permission-editor.test.js`; `control-plane/control_plane/store.py`, `control-plane/tests/test_store.py`; MXC patch/build/provenance/binary và hash consumers trong `scripts`, `resources` cùng `.gitignore`, `.gitattributes`. Guidance cập nhật tại `docs/CURRENT_STATE.md`; lịch sử checkpoint cũ giữ nguyên.

R4 package parity: **91 application files, 298 resources, 9 adapters**, sanitation 332 entries; isolated smoke PASS. EXE SHA `9d8290da25a32265f08eb00a27e7ed1a5dbbff1dab45bc9adebefdbf55d7cef1`; ASAR SHA `88b33896cf50bb1219f425dcafe094fc9cd4dcc5dbaf248a923779c8f0436175`.

Bằng chứng: [source validation](r4-source-validation.json), [package parity](r4-candidate-verification.json), [packaged smoke](r4-candidate-smoke.json), [retirement](packaged-retire-receipt.json), [r3 evidence trước chuyển](r3-pre-transition-evidence).

## Tài nguyên ngoài repository đã thay đổi

- Cài production Scheduled Task `WebMCP Recovery Supervisor` cho r4; dừng exact r3 UI/host qua supported lifecycle và PID/start-token guards, khởi động UI r4, full-clean refresh. Census lúc retirement safe; durable state và ba historical awaiting-acceptance RUN giữ nguyên.
- Đã triển khai và restart `codex-control-plane.service` trên `svhome` / `100.116.112.22` theo xác nhận của người dùng. Serving baseline `9cae1044…` với một `store.py` overlay; **37 file khác byte-identical**, schema 29. Đây không phải full server release của HEAD `7999c415`.
- Serving PID `912047`; package actual/manifest/expected cùng `sha256:f235d3a2898ad53597e3b48e55e27d2278ea7d6d0c9fb2fef21301467a5d9712`. HTTPS health và SQLite integrity `ok`. Backup DB/config chỉ ở remote protected locations, mode 0600.
- Chuyển pilot bằng supported recovery → exact decision → scoped-pilot API. New decision `pilot_dfb3174078d842299c41c6638830e505`, binding `bind_71661b1046884174b01c99af5f8546aa`, generation `generation_a420c8bfcfcb4e42b5bb7fc5e5cec097`. Pilot máy cũ bị thu hồi đúng quyền đã duyệt; principal/grants/scopes giữ nguyên.
- Sau xác nhận riêng của người dùng, đã sửa đúng một ID pilot trong protected env và chạy `codex-control-plane-authority-renewal.service` chính thức lúc **10:25:31 +07**. Pilot mới được gia hạn 20 giờ đến **13-10-2026 06:25:31.435 +07**. Existing timer active/enabled, cấu hình/identity pre/post giống nhau; main service PID 912047 không restart thêm, all grant rows/scopes/history không đổi. Backup config remote mode 0600. Timer được cấu hình tiếp tục tự gia hạn; các chu kỳ tương lai chưa phải proof đã quan sát.
- Hai historical quarantined unknown read families vẫn nguyên byte/digest `724cb852c916eb91bb16e8631ef423ce2cdda0b3d0e8e58e1f1c69bdf7d83d2f`; không settle/replay/accept giả.

Bằng chứng server: [deployment receipt](../new-machine-20261012/server-deployed-continuity-receipt.json), [pilot receipt](../new-machine-20261012/pilot-transfer-success-receipt.json), [renewal receipt](../new-machine-20261012/new-machine-renewal-execution-receipt.json).

## Job thật qua shared MCP

- Kết thúc **10:16:21.353 +07**, `ok=true`, exit **0**.
- Original action `act_df3616c34cc74c59846ae2d4b5adf509`, original Job `41965b8ea98447cebebc0fcc71ebf396`, command `8SSwgS5eEEVYU_ZGdQHlq4aC`; đúng **một** delivery attempt.
- Structured argv: `node --test .coding-tools/reports/new-machine-readiness-20261012/shared-exec-canary.cjs`.
- Marker `NEW_MACHINE_SHARED_MCP_EXEC_20261012_OK` và bounded nontruncated output được xác minh.
- Completed receipt `rcpt_cfb9bccb419e49928e09170fb6ab0608` ghim đúng epoch/process/server/smart-v3 fingerprint. Không dùng actor giả hay redispatch để tạo proof.
- Task `task_be0162a72d164f94b832d98711229771` đóng, writer release verified. SSH canary terminal exit 0; không stop/reconciliation.
- Central read-only census **10:19:17.179 +07**: tasks mở 0, writers chưa release 0, heartbeat READY fresh ~2.9 s; serving PID không đổi.

Bằng chứng: [original Job proof](shared-exec-canary-proof.json), [full sanitized receipt](shared-exec-canary-receipt-r2.ndjson).

## Census local cuối — 10:23:23.822 +07

- Read-only observer dùng đúng r4 ASAR/EXE hashes và exact verified Host; epoch/owner/digest trước và sau không đổi.
- `READY / OPEN`, `fullyReady=true`, ledger idle. Active tool calls, commands, starting commands, background operations, managed processes, foreign heavy processes, agent lanes và owned sidecar residues đều **0**.
- SQLite query-only Backup API snapshot integrity `ok`; foreign-key violations **0**, unexplained active runs **0**, unbound live resources **0**, projection drift false.
- Ba historical awaiting-acceptance RUN còn nguyên; census cho phép giữ lịch sử bằng supported `allowAcceptancePending=true`, không chấp nhận/settle chúng.
- Native OS observation có `WindowsSandboxServer` PID 32212 và `wxc-windows-sandbox-daemon` PID 40024, không còn `vmmemWindowsSandbox` trong named process observation này. Không suy ownership/teardown/zero-Sandbox từ ledger idle.
- Final lightweight runtime observation sau gia hạn vẫn `READY / OPEN`, `fullyReady/centralConnected/authorityReady=true`, `updateIncomplete=false`, cùng host PID 28804 và epoch r4.

Bằng chứng: [final local observation](final-machine-observation-activation-mv4od6fe-c45648f5d945ceeb7f3640048b0e91b7-1791775403822.json).

## Lỗi được giải quyết, phạm vi và phần còn lại

- R3 activation thất bại với `CROSS_OBSERVATION_RECEIPT_MISMATCH` do receipt producer cạnh tranh. Failure giữ nguyên; r4 source guard, focused/process tests và genuine READY giải quyết lỗi.
- First server deployment bị service guard từ chối do manifest fingerprint thiếu delimiter trong phép tính. Giữ failure receipt; corrected immutable fp2 artifact dùng official fingerprint helper rồi restart/postflight PASS. Chỉ metadata thay giữa hai artifact, 38 runtime files giống nhau.
- First MCP inventory HTTP 400 thiếu `clientCapabilities={}` theo stateless contract, chưa task/action/dispatch. Failure giữ nguyên; distinct attempt r2 sau correction PASS, không replay action.
- Renewal timer trước sửa trỏ pilot cũ đã revoked, khiến oneshot exit 2. Người dùng đã xác nhận retarget + 20 giờ + tiếp tục tự gia hạn; guarded protected single-key edit và official oneshot PASS. Hạn hiện tại **13-10-2026 06:25:31.435 +07**.
- Sandbox sau canary còn warm: quan sát host server/daemon và `vmmemWindowsSandbox`; không tuyên bố zero VM hay thực hiện force teardown/reboot.
- Public NSIS/signed release còn gate unsigned experimental MXC. Delivery hiện là unpacked candidate trên máy này; reboot/logon proof và genuine ChatGPT UI discovery/call/acceptance là boundary riêng chưa chứng minh.
- Checkout kiểm tra tạm ngoài repo còn giữ do automatic approval từ chối recursive deletion; không vòng qua từ chối đó.
- First final observer bị `ENOENT` khi dùng Electron virtual fs để hash raw ASAR; đây là lỗi read-only helper, không có runtime effect. Dùng `original-fs` cho archive bytes; subsequent exact observer PASS.
- Chưa commit, push, tag, public release hoặc Windows reboot. Source/test/build/canary commands đã terminal; final job census idle. Không stage delivery vì chưa có commit/push nào.

## Checkpoint kết thúc — 10:26–10:28 +07

- Remote postflight **10:26:55**: exact renewed expiry, r4 node READY/policy enabled, fresh heartbeat 14.5 s, admission scoped_pilot, tasks/writers **0**, main PID 912047 và HTTPS fingerprint đúng. Renewal oneshot success/exit 0/PID 0, timer active/enabled/Persistent.
- Git cuối: `main @ 7999c4151cb501db86f2e4d0a2275d33fc248324`, worktree dirty gồm các sửa đã mô tả và runtime evidence/context mới; không mất work hay lịch sử. `git diff --check` sạch; index không conflict. Focused credential-marker scan hai thư mục evidence mới không có match; `rg` exit 1 ở bước đó là kết quả không-match dự kiến.
- LF review finding đã giải quyết bằng exact attribute; [hash/attribute receipt](patch-eol-resolution.json) PASS. Không sửa native bytes hay rebuild/test lại chỉ vì metadata Git.
- Không còn command/test/build/canary/helper Job của đợt sửa đang chạy. Product Host/UI/native/Supervisor và server phục vụ vẫn chạy; warm Sandbox backend được quan sát riêng. Không có failure hiện tại ngăn vận hành trong phạm vi đã duyệt.

Bằng chứng bổ sung: [renewal postflight](../new-machine-20261012/new-machine-renewal-postflight-census.json).

Trong phạm vi triển khai máy mới đã duyệt, không còn blocker: r4 READY, shared MCP exec thật PASS, pilot đúng máy và automatic renewal được sửa. Các boundary signed installer/public release, reboot/logon, genuine ChatGPT UI discovery/acceptance cần bằng chứng riêng khi được yêu cầu.
