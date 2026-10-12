# Checkpoint vận hành — 11/10/2026, 14:16 +07

## Kết quả đã xác minh

- Ubuntu `100.116.112.22`: triển khai hotfix `70de202d93c9a759befe5d38491ce54e9ef4b3cd` và restart user service `codex-control-plane.service` lúc 14:11:02 +07. Health khớp package `sha256:fd5132676f1a68e875348fe790c6803c591f65a73311d793194c20a4e70b7d81`, schema 28. Backup DB/config được xác minh và giữ riêng trên server; không restore DB.
- Gia hạn đúng binding `bind_3e05bf64cb3e4bab93d930ae1692bebb`, workspace `workspace_dda1d78e9a21402aa6213f72af64f788`, generation `generation_c2f13e8d02344cf6a38a3f42ecfa59b6` trên DaoChienThang. Context `ctx_9cb78107d4aa4828bed2a0c0ee40633e` và pilot `pilot_c9bac9faee6c459680e6a7c44931848d` hết hạn **15:11:19 +07 ngày 11/10/2026**. Grant và credential không thay đổi. Admission đã mở lại `scoped_pilot`.
- Metadata assignment khớp hạn mới; ACL được kiểm tra trực tiếp: protected, chỉ user hiện tại/SYSTEM/Administrators được FullControl. Trường installer `windows_acl_verified=false` không thay thế kết quả kiểm tra ACL riêng.
- Candidate Windows unpacked 1.0.7 r3 đang chạy trên profile `web-mcp-assistant`: Recovery Host PID 12036, UI PID 20308. `fullyReady`, `localReady`, `componentsReady`, `centralConnected`, `authorityReady` đều true; `updateIncomplete=false`.
- Connected agent packaged mới PID 10668, bắt đầu 14:14:19 +07, heartbeat thành công; tối đa 200 iterations. Đây là phiên kiểm tra hữu hạn, không cài lịch chạy hoặc supervisor thường trực. PID cũ 20504 đã kết thúc và bị process khác dùng lại; không kill PID đó.
- Read → patch → readback qua Ubuntu loopback MCP tới Windows đã PASS trước triển khai. Fixture `tests/fixtures/folder-permissions-20261011.txt` vẫn có SHA-256 `14c82d572e3416dc67c06046ed33455ccfbaee4af1b1160196d97083def600a2`. Owner acceptance sau triển khai đã trả **accepted** cho action `act_45ac771eec124a6a9a043b3c471902dd`; không thực hiện lại patch.
- Windows feature `Containers-DisposableClientVM` đã Enabled qua UAC lúc 13:57:59 +07, `restartNeeded=true`. **Không restart Windows**.

## Phạm vi source và proof

Luồng folder đã gộp toolbar và Settings vào một manager, giữ exact ID/generation và realpath guards. Bridge bỏ argument `include_diff` không được schema nhận. `store.py` sửa lookup owner acceptance cho cả approved và standing patch intents.

Proof đã có ở cùng source liên quan được tái sử dụng: 75/75 Node UI/enrollment, affected Recovery test, 4/4 bridge schema tests, 4/4 focused owner acceptance tests, preview 1100/760 px, packaged smoke và byte comparison. Release builder/verifier kiểm tra 37 file. Không chạy lại các suite đã PASS khi source liên quan không đổi. Lần này bổ sung live acceptance sau deploy, metadata/ACL renewal, heartbeat/readiness và census.

Kiểm tra cuối: `git diff --check` PASS, không có unmerged entry, index vẫn không staged. `npm run check:coding-tools-history` PASS (4946 files), bao gồm repository secret guard PASS. Các receipt chỉ chứa trạng thái đã lọc; credential và remote backup riêng không được đưa vào repository.

Các file chính: `renderer/app.js`, `renderer/index.html`, `renderer/styles.css`, `electron/main.js`, `electron/preload.js`, `electron/services/controlPlaneEnrollment.js`, `electron/services/runtimeOrchestrator.js`, `control-plane/control_plane/store.py` và các focused test tương ứng. `docs/CURRENT_STATE.md` ghi trạng thái hiện hành; receipts nằm cùng thư mục báo cáo này.

## Giới hạn và job state

- **Exec chưa được chứng minh:** `WindowsSandbox.exe` vẫn chưa có trước reboot, local exec policy chưa cài. Probe exact E-drive trước đó còn báo `WINDOWS_WORKSPACE_REALPATH_EPERM`; cần kiểm tra lại sau reboot, không suy ra reboot sẽ giải quyết mọi gate.
- Local run `95e909f0040a448faa9f1f3257e2ee2c`, wave `c101beadfc6d4f2fbc13845052c84693` vẫn acceptance-pending. Owner verdict trung tâm chưa có adapter truyền về checkpoint local. Không giả controller/proof hoặc sửa ledger để đóng. Action-specific writes vẫn có đường riêng; ordinary full-clean vẫn chặn hàng đợi acceptance.
- Census cuối: active tool calls/commands/background operations/managed processes/agent lanes đều 0. `safe=false`, `RUNTIME_BUSY` vì runtime đang sống và còn acceptance-pending; connected agent hệ thống vẫn chạy như mô tả trên.
- Hai test task của binding hiện tại đã đóng, writer đã release, năm test action đều settled. 13 action lịch sử có supported dispositions (12 UNKNOWN quarantine, 1 unobserved dispatch) được giữ nguyên, không replay hoặc settle giả.
- Primary Git vẫn `main` tại `2c554f59cb7b8ffc86ce5e0e28076c792777642f`, worktree dirty với source/evidence và các thay đổi đã có, index không staged. Chỉ có commit artifact cô lập `70de202d`; không commit primary, không push/public release.

## Bước kế tiếp

Chủ máy khởi động lại Windows khi thuận tiện. Sau reboot, kiểm tra Sandbox đúng workspace, nối lại agent, cài exec policy bằng installer hỗ trợ và thử lệnh structured vô hại trong Sandbox. Chỉ tiếp tục trong cửa sổ quyền còn hiệu lực; nếu đã quá 15:11:19 thì cần quyền gia hạn mới. ChatGPT Tunnel client acceptance vẫn cần phép kiểm tra từ chính client đó; proof hiện tại là Ubuntu MCP loopback tới Windows.

## Receipts

- `server-acceptance-fix/deployment-result.jsonl`
- `server-renewal.jsonl`, `server-renewal-open.jsonl`, `server-renewal-final.jsonl`
- `metadata-renewal-result.json`, `metadata-renewal-acl.json`
- `central-patch-acceptance-deployed.jsonl`, `central-file-proof-r3.jsonl`
- `runtime-result.json`, `connected-agent-renewal-status.json`, `connected-agent-renewal-process.json`
- `windows-sandbox-feature-result.json`, `local-job-census.json`

Receipt lỗi HTTP 404 cũ và journal UNKNOWN gốc được giữ làm chronology; dùng receipt mới cho kết quả hiện tại.
