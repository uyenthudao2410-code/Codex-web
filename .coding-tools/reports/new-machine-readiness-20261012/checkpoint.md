# Kiểm tra máy Windows hiện tại — 12-10-2026

## Phạm vi và danh tính

- Máy: `DESKTOP-63643J4`, Windows 11 Pro Insider Preview `10.0.29683`, x64.
- Repository: `E:\DEV\Codex-web`, nhánh `main`.
- HEAD quan sát: `7999c4151cb501db86f2e4d0a2275d33fc248324`.
- Ngày kiểm tra: 12-10-2026, múi giờ +07; quan sát runtime 08:55, ledger 08:58–08:59 và checkpoint cuối 09:01.
- `git ls-remote origin HEAD refs/heads/main` trả đúng cùng HEAD. Không cần pull.
- GitHub API: không có Actions run cho HEAD này, không có release trong danh sách trả về. Các workflow thành công ở HEAD cũ không phải proof của HEAD hiện tại.
- Worktree sạch lúc bắt đầu. Không sửa source/test, commit hoặc push trong đợt kiểm tra này.

## Kết luận

Source đã cập nhật tới GitHub. Desktop và MCP đã nạp source hiện tại; một unpacked candidate mới build và vượt smoke cô lập trên máy này. **Chưa đủ điều kiện gọi hoàn thiện dứt điểm hoặc triển khai READY.** Central authority/heartbeat, quyền exec, connector freshness và nghiệm thu live còn thiếu. Installer NSIS cũng có release gate riêng cho unsigned experimental MXC Windows Sandbox binaries.

## Môi trường

- Node `24.19.0`, npm `11.14.1`; dependency root đầy đủ: Electron `43.2.0`, electron-builder `26.15.7`, electron-updater `6.8.9`, @electron/fuses `1.8.0`.
- Python trong PATH `3.11.7`; pytest/jwt/mcp/yaml import được.
- Python tích hợp `resources/native-python/python.exe`: `3.12.10`; ssl/sqlite3/jwt import được.
- `WindowsSandbox.exe` tồn tại. Trạng thái Windows optional feature chưa xác minh: truy vấn DISM yêu cầu elevation. HypervisorPresent=true; không suy Sandbox READY từ việc binary tồn tại hoặc từ thuộc tính CPU riêng lẻ.
- Bộ cài `dist/coding-tools-mcp-setup-1.0.7.exe` đã có từ 23-09; số phiên bản 1.0.7 không chứng minh nó chứa commit 7999c415.

## Source validation tập trung

### Desktop setup và execution

```powershell
node --test tests/toolbar-folder-navigation.test.js tests/folder-permission-editor.test.js tests/system-setup-console.test.js tests/unified-desktop-shell.test.js tests/control-center-manager.test.js tests/settings-redesign.test.js tests/settings.test.js tests/control-plane-exec-runtime.test.js tests/control-plane-exec-sandbox.test.js
```

Kết quả: **143 tests, 132 PASS, 11 FAIL**, không skip. Tất cả 11 FAIL nằm trong `tests/folder-permission-editor.test.js`.

Fixture `policy()` tại dòng 41 thiếu `facade_contract`, `current_facade_contract`, `authority_observed_at_ms`. Guard `setupPolicyMatches()` trong `renderer/app.js:419` yêu cầu đúng contract và observation fresh, nên các fixture bị từ chối tại dòng 579. Đây là fixture không theo hợp đồng hiện tại, không phải lỗi riêng Windows. Một thử nghiệm chẩn đoán chỉ trong RAM thêm ba trường vào fixture đạt **36/36 PASS**; không sửa file và không thay guard production. Gate nguyên bản HEAD vẫn có 11 FAIL.

### Python MCP

Từ `resources/coding-tools-mcp`:

```powershell
python -B -m pytest -q -p no:cacheprovider tests/test_exec_spawn_failure.py tests/test_windows_mxc_state_aware.py
```

Kết quả: **28 PASS + 5 subtests PASS**.

### Control Plane Console

Từ `control-plane`:

```powershell
python -W error -B -m unittest discover -s tests -p test_web_ui_folder_setup.py -v
```

Kết quả: **8 PASS**. Không chạy full workspace/Rust suite vì phạm vi kiểm tra là setup/Desktop/MCP hiện tại.

## Package proof trên máy này

```powershell
node scripts/build-dev-candidate.js verify-7999c415-1012
```

Candidate mới:

`E:\DEV\Codex-web\dist\windows-candidate-mxc-wsb-cbe1774-verify-7999c415-1012\win-unpacked`

- Build exit 0.
- app.asar: **89/89** file electron/renderer khớp SHA-256 với source.
- Resources **298/298**, control-plane adapters **9/9**; sanitation kiểm tra **332 entries**.
- Metadata package khớp theo phép chuẩn hóa electron-builder.
- Direct RunAsNode probe 5 giây thất bại; retry 15 giây PASS/exit 0/marker đúng. Phân loại: lần timeout đầu đã được giải quyết bằng retry; không phải hai lần đều PASS.
- `scripts/packaged-recovery-smoke.js` chạy với `CODEX_PACKAGED_APP_ROOT` là exact candidate trên: **exit 0, ok=true**.
- Smoke chứng minh 18 resources bắt buộc, smart-v3 8 tools và task_context_id, Recovery Host/MCP/Supervisor trong profile cô lập, các guard fail-closed; production descriptor không đổi, không thay Scheduled Task.
- Sau smoke: **0 candidate processes**.
- Không chạy NSIS build/install, activate packaged production hoặc public release. AfterPack chỉ cho phép unsigned experimental MXC WSB trong unpacked dev candidate; installer release vẫn bị guard chặn. Isolated smoke không thay thế enrollment/authority/ChatGPT E2E hay reboot/logon proof.

## Khởi động local

Đã chạy `npm start` theo lifecycle chuẩn. Trước đó UI MISSING, Recovery descriptor STALE. Sau cold start/full-clean:

- Recovery Host hiện tại, native MCP và Recovery MCP đã chạy; UI CURRENT.
- UI loaded revision bằng disk revision: `f64d85acdf8304002978f01c8b57894aa76e4466a1e48ecdc7d58b7f4edf39fb`.
- MCP loaded revision bằng disk revision: `75d872d848fdf39ae6fdb595adcea9b5c9248d06280221678fff34f70caa8cf3`.
- Workspace native: `E:\DEV\Codex-web`; mode `development`.
- Activation epoch: `activation-mv4lnjoy-e086a0528d6d74c3799d4d6f27abd68f`, quan sát `VERIFYING`, admission CLOSED, expiry 09:04:35 +07.
- `fully_ready=false`, `central_connected=false`, `authority_ready=false`, `central_status_reason=LOCAL_EXECUTOR_NOT_READY`.
- Connector `CHANGED_NEEDS_DISCOVERY`, chưa có current-process discovery/ACK.
- `npm run probe:execution-hub` PASS route_loaded=true; đây chỉ là gateway route proof, không phải quyền chạy lệnh hay READY.

CLI `npm start` đã kết thúc **exit 1**, mã `DEV_UI_REFRESH_POSTFLIGHT_FAILED`: không chứng minh đầy đủ component/activation identity và readiness. Không thử lại lifecycle để vượt gate. Read-only checkpoint lúc **09:01:32 +07** vẫn UI CURRENT/MCP current, central_connected=false/authority_ready=false/fully_ready=false, epoch VERIFYING và admission CLOSED. Desktop/Recovery/MCP local còn chạy; epoch có thời hạn 09:04:35 +07 và do supervision quản lý. Đây là khởi động local có nạp source nhưng **activation chưa thành công**, không phải startup READY.

Profile có enrollment approved được cache từ 23-09, route evidence từ 02-10 đã hết hạn, agent status từ 03-10 báo transport unavailable. Registry workspace hiện read/write=true nhưng exec=false; `control-plane-exec-policy.json` chưa có. Không dùng các cache này như heartbeat/authority fresh.

## Ledger và công việc còn sống

Quan sát 08:58–08:59 +07 bằng SQLite URI mode=ro, PRAGMA query_only=ON:

- **0 Job/command chưa terminal**, 0 background operation đang chạy, 0 write fence, 0 agent lane đang chạy, 0 resource claim, 0 controller lease còn live.
- Không có RUN/Job/event mới từ lúc native hiện tại bắt đầu 08:55:01.
- Ledger giữ 20 RUN active lịch sử: 17 thuộc E:\DEV từ 15-09, 3 ACCEPTING thuộc E:\Github\Tools-Codex-web/base HEAD 2c554f59. Chúng không chứng minh process hiện đang chạy; không accept/reject hoặc sửa bằng chứng lịch sử.
- CURRENT_STATE proof r14 thuộc DaoChienThang/E:\Github, vẫn thiếu full TAP và native ChatWeb acceptance. Không chuyển các proof đó thành READY của máy này.

## Việc tiếp theo

1. Sửa fixture test theo hợp đồng hiện tại, giữ nguyên guard production; chạy lại file 36 tests.
2. Vận hành exact packaged candidate bằng supported installation/activation flow. Central folder/policy setup bị khóa trong npm start.
3. Trong Hệ thống → Kết nối máy chủ và máy này, kiểm tra enrollment hiện có bằng receipt fresh; không tạo pairing mới chỉ vì cache cũ.
4. Chọn đúng workspace hiện có, quyền Làm việc với mã nguồn; owner trung tâm phải cấp đúng binding/device/generation. Kiểm tra liên kết → Tiếp tục thiết lập để xác minh read/edit/exec policy, Sandbox probe và heartbeat mới.
5. Connector ChatGPT discovery/ACK đúng process/epoch/contract; chỉ gọi READY sau admission mở và các gate cùng đạt. Native acceptance phải do controller thật xử lý.
6. Installer/public release cần xử lý gate unsigned MXC và bằng chứng install/live được yêu cầu trước delivery.

## Phạm vi thay đổi

Đã khởi động dịch vụ **cục bộ** theo npm start và tạo candidate cô lập trong dist. Runtime làm đổi `.coding-tools/orchestration/ledger.sqlite3` và `.coding-tools/performance.json`; báo cáo này là evidence mới. Không sửa source/test, không cài Scheduled Task, không reboot, không accept RUN lịch sử, không deploy/restart Ubuntu, không commit/push/tag/release.

Checkpoint cuối: main@7999c415; Git dirty gồm hai runtime evidence file và thư mục báo cáo mới. `git diff --check` sạch, không có unmerged paths; các test/build/smoke/start CLI đã terminal, candidate processes=0, không có Job mới được dispatch. Không stage hoặc chạy delivery guard vì chưa có commit/push nào.
