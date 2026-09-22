# Kế hoạch đơn giản hóa thiết lập Windows–Ubuntu và quản trị máy dùng chung

**Trạng thái:** CANDIDATE ĐÃ TRIỂN KHAI Ở SOURCE — ĐÃ QUA G2/G3, ĐÃ KIỂM TRA GÓI `win-unpacked` VÀ ĐÃ SỬA/VERIFY GÓI CONTROL PLANE CHO BUILD TỪ WINDOWS; CHƯA CÀI ĐẶT, KÍCH HOẠT HAY DEPLOY LIVE.

**Ngày lập:** 22-09-2026, GMT+7. **Repository:** `E:\DEV\Codex-web`, `main`, HEAD quan sát `77d73471dc896a1f1ac189b2df46529276481552`.

Yêu cầu hiện tại là lập kế hoạch để kiểm tra trước khi chạy xử lý. Candidate source đã được hoàn thiện trong worktree để người dùng kiểm tra; đã tạo một thư mục packaged candidate cô lập để kiểm tra byte/resource và recovery smoke, nhưng chưa cài đặt, kích hoạt, restart, duyệt máy, cấp quyền, deploy, commit hay push. Các lệnh vận hành Ubuntu ở dưới vẫn là **lệnh dự kiến**, không phải biên bản đã thực hiện.

### Bằng chứng candidate mới nhất

- Source candidate đang ở worktree `main @ 77d73471dc896a1f1ac189b2df46529276481552`; chưa commit.
- Syntax check cho `renderer/app.js`, `electron/main.js`, `electron/preload.js`: đạt.
- G2/G3 focused suite: **49 pass, 0 fail** (`settings-redesign`, `central-executor-handoff-ui`, enrollment/authority, control-center và system-setup-console).
- `git diff --check` cho các hunk candidate: đạt; toàn worktree chỉ còn cảnh báo line-ending CRLF và hai cảnh báo blank-line-at-EOF thuộc thay đổi concurrent ở `tasks/todo.md` và `tests/icon-source.test.js`.
- Preview visual QA: `?preview=1#system` vào đúng `Thiết lập hệ thống` trong phiên trình duyệt mới; 375/768/1024/1440 px không có overflow ngang; light-mode, keyboard focus và central-dev guard đã kiểm tra. Ảnh nằm trong `output/playwright/system-setup-*.png`.
- Full Node/Electron test lane trước đợt revalidation cuối: **943 pass, 0 fail**. Đây là hồi quy source rộng; không thay thế packaged/live proof.
- Candidate Electron cuối cùng build thành công tại `output/packaged-candidate-revalidated-20260922-135500/win-unpacked`: exact resource proof **285/285 file**, Control Plane adapter **9/9 file**, sanitation **318 entries**, và `packaged-recovery-smoke.js` trả `ok=true` (smart-v3 contract, recovery host, supervisor fail-closed và production descriptor/task isolation). Hash tại thời điểm build: `Coding Tools MCP.exe` = `886681D8BD3013F07461965BEB59F8C4AA59E44A21360F2CF45B07D0827CFEAE`; `resources/app.asar` = `A8AB17DFDFE4DC2A25B112AA032D7B131F9A116FDADA25405BB1974493C16F2B`. Sau đó source/UI revision tiếp tục drift từ `a6e8…` sang `3997…`, nên candidate này chỉ là last-successful artifact evidence, chưa phải candidate hiện hành để cài.
- Một lần build tiếp theo vào `output/packaged-candidate-revalidated-20260922-140500` dừng ở `EBUSY` khi electron-builder edit/sign `Coding Tools MCP.exe`; thư mục này là failed attempt, không phải candidate hợp lệ. Không retry mù hoặc kill process; cần xác định/giải phóng host file-lock rồi build lại từ source freeze.
- Đổi output sang Temp để tránh host file-lock đã tạo được candidate theo source revision hiện tại `3997e59b…`: `C:\Users\Admin\AppData\Local\Temp\codex-packaged-revalidated-20260922-141500\win-unpacked`. Candidate này đạt exact resources **285/285**, Control Plane adapter **9/9**, sanitation **318 entries** và `packaged-recovery-smoke.js` **`ok=true`**. Hash hiện tại: `Coding Tools MCP.exe` = `6901368048C9836FCC5DF8675A9D64738C7A47CEA70870DC7706698F7782D38F`; `resources/app.asar` = `3BABFFB709F267AC7FD9C3E9A3190CAA0C89C041407FE7486489FC0BE714DB03`. Đây là candidate current-source để operator review, chưa installed/live.
- Lượt revalidation hiện tại trên worktree sau các thay đổi concurrent: focused setup suite **30 pass, 0 fail**, full `npm test` **939 pass, 0 fail**, scanner báo `source root clean` và `repository secret check: PASS` (đây không có nghĩa Git worktree sạch), cùng candidate Electron mới `packaged-recovery-smoke.js` **`ok=true`**. Đây là revalidation cục bộ; không làm thay đổi trạng thái Ubuntu hoặc installed runtime.
- Lượt xác nhận mới nhất sau khi khóa contract origin/opaque workspace: focused setup lane **57 pass, 0 fail**; `test_store.py` **86/86**; `test_http_api.py` **43/43**; full `npm test` **944 pass, 0 fail**; syntax `node --check` **3/3**; `source root clean` và `repository secret check: PASS`. Đây là bằng chứng source/local mới nhất, không phải installed/live proof.
- Candidate Electron cô lập mới nhất được build từ worktree hiện tại tại `C:\Users\Admin\AppData\Local\Temp\codex-packaged-system-setup-20260922-160000\win-unpacked`; `packaged-recovery-smoke.js` trả `ok=true` (smart-v3, recovery host, supervisor fail-closed, production descriptor isolation). Hash: `Coding Tools MCP.exe` = `8E3BA764ED0E6149A30A40F203646BBC1B41D8D902D712E657E2574077FA3CB7`; `resources/app.asar` = `FF51611C07358645D1682E2E08F3CD3413E87E61A01B7081A219DA5125BB769B`. Candidate này chưa cài đặt, chưa chạy thay cho runtime hiện tại và chưa là release.
- Read-only lifecycle census lúc **12:59:53 +07** dùng immutable SQLite Backup API: `content_free=true`, `mutated_canonical_ledger=false`, `integrity_check=ok`, `foreign_key_check_rows=0`, `projection_drift=false`, `unbound_live_resource_residues=0`, `stale_background_operation_residues=0`; 17 ordinary active runs đều được phân loại `THRESHOLD_SENSITIVE_STALE_CANDIDATE`, không có `unexplained_active_runs`. Đây là điều kiện để owner xem xét lifecycle refresh chính thức, không phải quyền tự restart hay sửa ledger.
- Control Plane source proof: `PYTHONPATH=E:\DEV\Codex-web\control-plane python -m pytest control-plane/tests/test_http_api.py control-plane/tests/test_store.py -q` đạt **129 passed, 50 subtests**. Trong đó đã sửa một lỗi thật trên Windows: liveness lock dùng `OpenProcess/GetExitCodeProcess`, nên crash của node không khóa vĩnh viễn read-only poll.
- Đã tạo candidate release Control Plane cô lập từ source worktree (không cài/deploy): `output/control-plane-release-candidate-20260922-132547/codex-control-plane-77d73471dc896a1f1ac189b2df46529276481552`; manifest verification **33 files**, schema **24**, package fingerprint `sha256:f941d54fdb1b5a3561a990101f991c3ca437a4dac37290d5ecc85e480c9c970f`. Read-only deployment verifier đối chiếu fingerprint này với Ubuntu `/healthz` trả `CONTROL_PLANE_DEPLOYMENT_HEALTH_MISMATCH`, xác nhận live package hiện chưa phải candidate. Archive này được giữ làm bằng chứng manifest; sau khi sửa portability mode/LF phải build lại archive deploy từ source freeze, không cài archive cũ.
- Khi kiểm tra release artifact trên Windows, đã phát hiện và sửa một lỗi thật của đường đóng gói: NTFS không giữ executable bit và checkout có thể materialize shell launcher bằng CRLF. `scripts/build-control-plane-release.py` hiện ép bốn launcher thành mode `0755` trong `TarInfo` và chuẩn hóa riêng các file `.sh` thành LF trước khi hash/archive. Test Windows `python -m unittest control-plane.tests.test_release_artifact` đạt **2 passed, 1 skipped** (skip chỉ cho chạy shell trực tiếp trên Windows); archive candidate mode-fix đã được giải nén trong WSL với cả bốn file `755`, `file` nhận diện shell executable không CRLF và `bash -n` đạt. Đây là proof của artifact/compatibility, chưa phải deploy Ubuntu.
- Cùng candidate đã được `control-plane-verify-release.py` đọc/verify trong WSL Ubuntu; từ môi trường Linux đó, GET `/` và `/healthz` tới cùng private origin cũng trả **200**. Đây chứng minh đường truy cập chung tới một Control Plane root, không chứng minh operator session, approval hay quyền mutation.
- Hai quan sát GET-only lúc **14:24:04 +07** và kiểm tra Tailscale lúc **14:25:44–14:26:48 +07** dùng nhầm hostname cũ `svhome.tail0e403.ts.net` (thiếu số `2`), nên lỗi DNS/TLS trong chronology đó không phải blocker của origin hiện hành và không được dùng để kết luận Ubuntu tắt.
- Recheck bằng origin đúng `https://svhome.tail0e4032.ts.net/` đã trả **HTTP 200** cho cả `/` và `/healthz`; đường DNS/HTTPS hiện đã quan sát được. Đây chỉ là proof reachability/health, chưa thay thế đối chiếu package/schema/auth, operator session, approval, binding hoặc admission.
- Snapshot full `control-plane/tests` **281 passed, 9 skipped, 12 failed** được chụp trước khi cập nhật host-lane assertion ở release artifact; các fail khi đó được phân loại là Windows/Unix mismatch (exec, LF/CRLF fixture, POSIX owner-private/symlink và shell launcher). Không dùng tổng số snapshot này để claim Control Plane live/release readiness; Linux/Ubuntu release lane vẫn cần chạy trên đúng host.
- Candidate cũ `output/packaged-candidate-final` đã bị loại khỏi đường cài vì Control Plane adapter không còn khớp `node_agent.py` hiện tại. Nếu build lại candidate mới, phải chụp lại fingerprint và chạy lại smoke; không dùng hash cũ `7C3495EA…`/`3B3CE689…` làm identity hiện hành.
- Console preview còn các cảnh báo môi trường đã biết: Google Fonts bị CSP chặn, hai inline-style bị CSP chặn, iframe token-dashboard bị chặn font và thiếu `favicon.ico`. Không nới CSP hoặc coi các cảnh báo này là bằng chứng runtime packaged.
- Đây chỉ là proof của source/preview/local tests. **G4 Ubuntu, G5 packaged activation, G6 strict discovery/canary/natural task và G7 release vẫn chưa đạt.**

## 1. Kết luận để chốt hướng xử lý

1. **Không cần xây một hệ thống quản trị mới.** Ubuntu đã có browser operator console ở đường dẫn `/`; lần kiểm tra GET trực tiếp trong phiên này nhận HTTP 200 và tiêu đề `Control Plane` tại `https://svhome.tail0e4032.ts.net/`.
2. **Giao diện Windows cần một lối vào “Thiết lập hệ thống”.** Kết nối, thư mục, tài khoản và kiểm tra không nên tiếp tục là những trang rời rạc, thiếu bước tiếp theo.
3. **`npm start` và bản cài đặt có hợp đồng khác nhau.** Hiện tại development UI bị chặn có chủ đích đối với pairing, đọc enrollment/authority, đăng ký/liệt kê workspace, rotation và cài policy. Giao diện phải nói rõ điều này trước khi người dùng bấm.
4. **Ubuntu bật không có nghĩa hệ thống đã chạy được tác vụ.** Phải kiểm tra riêng phiên bản server, máy được duyệt, thư mục, quyền tài khoản, policy local, runtime và client discovery.
5. **Quản trị từ máy nào cũng được là truy cập cùng một trang trên Ubuntu**, không phải mỗi máy chạy một server quản trị riêng và không phải tự chuyển nơi thực thi tác vụ.

Khuyến nghị: hoàn thiện UX và giữ các chốt quyền hiện tại trước; sau đó mới đồng bộ bản chạy, pairing và nghiệm thu thật. Nếu muốn `npm start` trở thành executor development thực sự, thực hiện nhánh riêng ở mục 4, không bỏ guard packaged trong đợt sửa UI.

## 2. Hiện trạng và giới hạn bằng chứng

### 2.1 Quan sát trực tiếp trong phiên làm việc

| Hạng mục | Đã quan sát | Không được suy ra |
|---|---|---|
| Windows checkout | `main @ 77d73471…`; version trong package là `1.0.7` | Không chứng minh artifact installed chứa cùng source |
| Windows runtime — lần đọc mới nhất | Read-only `npm run dev:status` lúc **14:16:53 +07** báo `state=MISSING`, `installation=current`, `mode=development`, descriptor PID cũ `23008` nhưng `running_revision=none`, `disk_revision=3997e59b…`, `update_pending=false`; MCP riêng `current`; `components_ready=false`, `fully_ready=false`, `runtime_update_incomplete=true`, `connector_state=CHANGED_NEEDS_DISCOVERY`, `connector_rediscovered=false` | UI process không còn sống; activation epoch vẫn phải đối chiếu riêng; không tự restart hoặc nhận `MISSING` là executor PASS |
| Activation epoch hiện tại | Read-only `activation-epoch.json` lúc **14:10:00 +07**: `state=FAILED`, `admission_state=CLOSED`, `activation_epoch_id=activation-mucbq2r3-…`, operation `full-clean-refresh-mucbpolc-…`, `error_code=ACTIVATION_REQUEST_EXPIRED`; Recovery Host PID `14300` còn sống | Không sửa tay epoch/ledger, không tạo refresh thứ hai và không kill PID concurrent; owner phải xác nhận refresh chính thức sau khi kiểm tra job/lease |
| Windows Control Plane node | Read-only `control-plane-node.json`: Ubuntu origin đã lưu, `enrollment_id` có mặt, `enrollment_state=pending_operator_approval`, credential DPAPI có mặt nhưng không đọc raw; `control-plane-route-evidence.json` chưa có; settings có local workspace nhưng `authorized_roots_count=0` | Không gửi pairing lại, không tự coi máy đã approved/route-ready và không tự cấp root; operator Ubuntu phải duyệt đúng enrollment trước |
| Connector | `CHANGED_NEEDS_DISCOVERY`, `connector_rediscovered=false` | Không được gọi strict client discovery là đã đạt |
| Ubuntu root UI | HTTPS GET `/` trả 200, HTML có tiêu đề `Control Plane` | Chưa đăng nhập operator, chưa đọc danh sách máy có xác thực, chưa kiểm tra từ máy thứ hai |
| Ubuntu health, 11:06:09 +07 | `ok=true`, `schema_version=19`, `admission_mode=recovery`, `mcp_authentication_mode=legacy_context_grant` | Không chứng minh OAuth/shared-account flow hiện hành đã hoạt động |
| Ubuntu metadata công bố | `declared_source_revision=0843ece334e07dd29f03cbd4c67fa97fc885ea1c`; `package_source_sha256=sha256:3a151842840530206acf90cdeb0731476af555a46601a357d750ce2105a5b773` | Đây là health metadata, chưa phải đối chiếu systemd/process/package bytes độc lập |
| Control Plane source hiện tại | `control-plane/control_plane/store.py` khai báo `SCHEMA_VERSION = 24` | Không được giả định server schema 19 có đủ chức năng của source schema 24 |

**Cập nhật read-only mới nhất trong lượt này:** `npm run dev:status` lúc `2026-09-22T08:43:59.934Z` (`15:43:59 +07`) vẫn báo `state=MISSING`, `installation=current`, `mode=development`, `running_revision=none`, `disk_revision=99b9261492aeb2e205b5632812b2411429e642e12f8c4df6f9f9c1b21fd329dc`, `components_ready=false`, `fully_ready=false`, `runtime_update_incomplete=true`, `connector_state=CHANGED_NEEDS_DISCOVERY`, `connector_rediscovered=false`; host còn khả dụng và Recovery Host telemetry còn fresh. Không restart hoặc tạo activation mới trong lượt này. `activation-epoch.json` hiện là `FAILED/CLOSED` với `ACTIVATION_REQUEST_EXPIRED` (failed `2026-09-22T07:09:18.220Z`); Recovery Host PID `14300` còn sống, runtime mode `development`.

Windows profile hiện vẫn có enrollment `pending_operator_approval` và credential DPAPI (không đọc raw); node config lưu origin dưới field legacy `server_url`, còn `settings.json` chưa có `controlPlaneServerUrl` và chưa có route evidence/workspace registry. Đây là đúng lỗi UX “mở lại mất địa chỉ” mà source mới xử lý bằng receipt `server_origin`; chưa được dùng để suy ra máy đã approved hoặc route-ready.

Recheck đúng origin `https://svhome.tail0e4032.ts.net/` trong lượt này trả HTTP **200** cho `/` (title `Control Plane`) và `/healthz`: `ok=true`, `schema_version=19`, `admission_mode=recovery`, `mcp_authentication_mode=legacy_context_grant`, `sqlite_integrity=ok`, live package `sha256:3a151842…`, `unquarantined_unresolved_action_count=1`. Vì vậy blocker DNS/TLS cũ đã được phân loại là truy vấn nhầm hostname; blocker thật hiện là version/package/auth/admission và onboarding chưa làm.

**Đọc lại chỉ xem ngày 22-09-2026:** `npm run dev:status` sau lượt `npm test` lúc **14:16:53 +07** vẫn báo `state=MISSING`, `running_revision=none`, `disk_revision=3997e59b…`, `update_pending=false`; MCP vẫn current nhưng `components_ready=false`, `fully_ready=false`, `runtime_update_incomplete=true`, `connector_state=CHANGED_NEEDS_DISCOVERY`, `connector_rediscovered=false`. Lần epoch recheck gần nhất trước đó cho thấy refresh đã terminal `FAILED` lúc `14:09:18 +07`, `admission=CLOSED`, `error_code=ACTIVATION_REQUEST_EXPIRED`, Recovery Host PID `14300` còn sống; epoch chưa được tự mở lại trong lượt này. Ubuntu `/` và `/healthz` vẫn trả HTTP 200; health vẫn là `schema_version=19`, `admission_mode=recovery`, `mcp_authentication_mode=legacy_context_grant`, `sqlite_integrity=ok`, service instance `cp_992cf7223c9746a5a9d48ac4b8c38799`, với `unresolved_action_count=11` và `quarantined_unknown_action_count=10`; live package SHA `3a151842…` vẫn khác candidate SHA `f941d54f…`. Đây là các lần đọc chỉ xem, không phải hành động thay đổi trạng thái.

Service instance trong health quan sát: `cp_992cf7223c9746a5a9d48ac4b8c38799`. Các quan sát runtime phải được làm mới ở đầu đợt triển khai, không dùng vô thời hạn.

Các snapshot trước từng chuyển `MISSING → CURRENT → STALE`; lần đọc mới nhất là `MISSING` sau khi full-clean refresh terminal `FAILED/ACTIVATION_REQUEST_EXPIRED`. Do đó mọi nghiệm thu phải ghi thời điểm và đọc lại ngay trước thao tác; không dùng trạng thái cũ vô thời hạn, và không coi observation timeout là terminal. `CURRENT` chỉ chứng minh UI revision khớp disk; các gate activation, central route, authority, tunnel và connector discovery vẫn độc lập. Preview tĩnh `?preview=1` chỉ chứng minh source/renderer, không thay thế runtime readiness.

### 2.2 Các nguồn mã nguồn đã đối chiếu

- [package.json](../package.json): `start` gọi development lifecycle.
- [ControlPlaneEnrollmentService](../electron/services/controlPlaneEnrollment.js): guard `runtimeMode() !== 'packaged'` chạy trước node agent; có các mã `CONTROL_PLANE_*_PACKAGED_REQUIRED`.
- [Runtime orchestrator](../electron/services/runtimeOrchestrator.js): readiness gồm local runtime, central route và authority; `LOCAL_EXECUTOR_NOT_READY` khác pending enrollment.
- [Renderer](../renderer/app.js), [HTML](../renderer/index.html), [CSS](../renderer/settings-compact.css): vị trí triển khai setup và trình bày trạng thái.
- [HTTP API](../control-plane/control_plane/http_api.py), [web UI](../control-plane/control_plane/web_ui.py): root operator console và API/session bảo vệ.
- [Control Plane README](../control-plane/README.md): private HTTPS origin, operator session, CSRF và ranh giới browser console.

Nguồn vận hành liên quan: [bản tóm tắt hiện trạng](SHARED_ACCOUNT_WORKSPACE_STATUS.md), [kế hoạch shared-account](TRUSTED_WORKSPACE_ACCOUNT_COMPLETION_PLAN.md), [runbook Windows exact](WINDOWS_EXACT_VALIDATION_RUNBOOK.md), [runbook phục hồi Control Plane](CONTROL_PLANE_RECOVERY_RUNBOOK.md). Các checkpoint cũ trong đó là lịch sử; không dùng commit/PID/receipt cũ như bằng chứng hiện tại.

### 2.3 Các thay đổi nháp cần xử lý trước khi tiếp tục

Trước khi người dùng đổi yêu cầu sang “lập kế hoạch”, có sửa nháp chưa commit tại:

- `renderer/index.html`, `renderer/app.js`, `renderer/settings-compact.css`.
- `electron/main.js`, `electron/preload.js`.

Nội dung nháp: gom navigation, hướng dẫn theo trạng thái, thông báo development, và IPC mở trang quản trị bằng HTTPS origin đã được kiểm tra. Đây là **candidate chưa nghiệm thu**, không phải tính năng đã bàn giao.

Các điểm phải review, không tự coi là hoàn thành:

- Kết quả **13 pass, 1 fail** ở lần chạy cũ chỉ là lịch sử trước khi cập nhật contract; không dùng nó thay cho candidate proof hiện tại. Candidate hiện tại đã có **49/49** test G2/G3 đạt; full Node/Electron lane trước đó là **943/943**, còn lượt revalidation mới nhất là **939/939**.
- Candidate đã thêm test riêng cho IPC mở console và boundary caller; đây vẫn là source/local proof, không phải bằng chứng operator session hoặc Ubuntu route thật.
- Guidance cần phân biệt authority stale với enrollment đã approved; không hướng dẫn như thể quyền tài khoản đã được xác minh.
- Contract enrollment có `unconfigured`, `request_sent`, `pending_operator_approval`, `approved`, `revoked`, `unknown`; không tự thêm trạng thái `rejected/denied` nếu contract chưa phát ra chúng.
- `LOCAL_EXECUTOR_NOT_READY` cần có chỉ dẫn riêng; approval không phải readiness. Tuy nhiên, không bắt `fullyReady` làm điều kiện cho enrollment/workspace vì sẽ tạo vòng phụ thuộc.
- Các nút chọn thư mục/capability trong development đã được vô hiệu hóa hoặc ghi rõ chỉ là xem trước, không để người dùng tưởng đăng ký đã thành công.
- Visual QA, luồng development/pending/stale/revoked, bàn phím và viewport hẹp đã được kiểm tra ở local preview. Preview còn báo CSP/font/inline-style và favicon; phải phân loại lỗi có sẵn so với lỗi do thay đổi, không nới CSP để làm xanh.
- Nếu runtime mode không phải `packaged` hoặc không xác minh được, setup fail-closed với trạng thái `runtime-unverified`; không gửi pairing, đọc inventory hoặc cài policy chỉ vì `centralConnected`/heartbeat có vẻ sống.

Hai file `.coding-tools/orchestration/ledger.sqlite3` và `.coding-tools/performance.json` đã dirty do runtime từ đầu và được giữ nguyên. Hai log/snapshot `.playwright-cli` phát sinh từ preview được giữ lại. Server preview loopback và browser session kiểm thử đã được dừng; không dừng runtime sản phẩm.

Lần kiểm tra Git cuối còn thấy thay đổi đồng thời ngoài các sửa của đợt này: `.coding-tools/evaluation/chatweb-host-observations.jsonl` modified và `.coding-tools/evaluation/chatweb-host-turn-binding.json` deleted; nhóm icon (`electron/app-icon.*`, `scripts/generate-icon.js`, `docs/ICON.png`, `renderer/app-icon.png`, `scripts/build-icon-from-source.py`, `tests/icon-source.test.js`, `tasks/todo.md`); và các renderer khác (`renderer/browser.html`, `renderer/login.html`, `renderer/panel.html`, `renderer/styles.css`, `renderer/token-dashboard.html`). Không tự khôi phục hoặc đưa các thay đổi này vào commit; G0/delivery phải đối chiếu writer và retention trước. Chỉ quan sát trạng thái, chưa kết luận nguyên nhân việc xóa/sửa.

Candidate directory build và packaged smoke đã được chạy sau khi source/test G0–G3 hiện tại đạt; không chạy installer/installed smoke hoặc refresh production trước khi người dùng duyệt target và side-effect boundary. Không tự reset/revert để làm sạch worktree; quyết định giữ/điều chỉnh/loại bỏ nháp phải được người dùng duyệt và chỉ tác động đúng các hunk của đợt này.

## 3. Mô hình sử dụng đích

### 3.1 Một nguồn quản trị chung

```text
Trình duyệt Windows / Ubuntu / máy khác có quyền truy cập mạng riêng
                         |
          https://svhome.tail0e4032.ts.net/
                         |
       Ubuntu: quản trị, danh sách máy, hàng đợi, audit
                         |
       Máy Windows được chọn: workspace và thực thi local
```

Không thêm DB, registry, Goal engine hay server quản trị cạnh tranh. Không public Internet/Funnel, không tự động failover task giữa các máy. Máy thực thi offline thì UI phải báo offline/chưa thực thi, không báo thành công vì Ubuntu còn sống.

### 3.2 Điều hướng Windows đề xuất

- **Tổng quan:** tình trạng vận hành và một hành động tiếp theo.
- **Công việc:** task, tiến độ và bằng chứng.
- **Máy này:** định danh và điều khiển runtime local; ghi rõ không phải danh sách toàn hệ thống.
- **Thiết lập hệ thống:** một nơi chứa toàn bộ setup.

Trong “Thiết lập hệ thống”, giữ một khung tiến độ chung khi chuyển các phần:

1. **Máy chủ & kết nối:** một trường địa chỉ HTTPS, mở trang quản trị, gửi một yêu cầu, theo dõi duyệt máy.
2. **Thư mục & quyền:** chọn thư mục local; mặc định chỉ xem; giải thích rõ quyền đọc/ghi/chạy trước khi lưu.
3. **Tài khoản & quyền làm việc:** tài khoản nào được dùng máy/thư mục nào; hiển thị bằng tên dễ hiểu, không bắt nhập context ID/token/JSON.
4. **Kiểm tra sẵn sàng:** điều kiện còn thiếu và nút kiểm tra chỉ đọc; không ngầm restart/cấp quyền.

Giao diện, khởi động cùng Windows, chạy nền đặt ở **Tùy chọn ứng dụng**. Proxy, credential rotation, legacy direct, log và activation diagnostics đặt ở **Nâng cao**. Không lặp lại cùng một thiết lập ở nhiều vị trí.

### 3.3 Mỗi trạng thái phải trả lời ba câu hỏi

**Đang ở đâu? Ai cần xử lý? Bấm gì tiếp theo?** Mã kỹ thuật và enrollment ID vẫn có trong phần chi tiết để hỗ trợ, không đẩy toàn bộ lên màn hình chính.

| Tình huống | Nội dung chính | Người xử lý / hành động |
|---|---|---|
| Development bị packaged guard | “Bản dev chưa hỗ trợ hoàn tất đăng ký máy” | Windows: mở bản cài được xác minh; vẫn có thể mở admin trong trình duyệt |
| Runtime mode không xác minh được | “Chưa xác minh bản chạy của máy này” | Windows: kiểm tra đúng bản packaged; giữ pairing/workspace/policy đóng |
| Chưa có địa chỉ / unconfigured | “Chưa chọn máy chủ” | Windows: nhập đúng HTTPS origin; không nhập `/mcp` hoặc token |
| Đang gửi | “Đang gửi yêu cầu” | Khóa thao tác trùng, không phát sinh request thứ hai |
| Pending approval | “Đã gửi — chờ quản trị viên duyệt” | Ubuntu admin: duyệt đúng máy; Windows chỉ kiểm tra lại |
| Enrollment read stale/unavailable | “Chưa kiểm tra được; giữ yêu cầu đã lưu” | Kiểm tra mạng/phiên bản/giới hạn runtime; không tự re-enroll |
| Approved, chưa có workspace | “Máy được duyệt — cần thêm thư mục” | Chủ máy Windows chọn thư mục và phạm vi quyền |
| Workspace có, chưa có binding/tài khoản | “Chưa cấp thư mục này cho tài khoản” | Operator/account flow hiện có cấp đúng target |
| Authority read stale/unavailable | “Chưa xác minh được quyền hiện tại” | Kiểm tra trạng thái; không giữ nhãn xanh từ receipt cũ |
| Local executor not ready | “Máy đã được duyệt nhưng runtime local chưa sẵn sàng” | Windows: xem blocker/activation cụ thể; không yêu cầu pairing lại |
| Revoked hoặc generation thay đổi | “Quyền cũ không còn hiệu lực” | Người có quyền xem xét cấp lại; không tự đổi máy/thư mục |
| Route/policy thiếu hoặc stale | “Kết nối có, chưa đủ điều kiện thực thi” | Kiểm tra đúng device/generation/policy và làm mới bằng đường hỗ trợ |
| Đủ toàn bộ điều kiện | “Sẵn sàng trong phạm vi quyền được cấp” | Chạy kiểm tra có kiểm soát; chưa gọi là nghiệm thu phát hành |

Các trạng thái trên là lớp trình bày từ contract hiện có; không tạo thêm một state machine có quyền thực thi cạnh tranh với runtime.

## 4. Quyết định cần duyệt về `npm start`

### Phương án A — khuyến nghị cho đợt này

- `npm start`: phát triển UI, snapshot local, chẩn đoán và mở trang admin; không giả rằng enrollment/authority/workspace APIs hoạt động trong dev.
- Bản cài packaged đã xác minh: pairing, workspace, policy và vận hành executor thật.
- Hiển thị loại runtime và nơi chuyển tiếp rõ ràng. Không yêu cầu người dùng sửa JSON/token, không mở hai writer/profile production đồng thời.
- “Mở trang quản trị” chỉ mở HTTPS trong browser, không đọc/gửi operator token và không tạo enrollment.

**Lợi ích:** phạm vi nhỏ, tận dụng đường đã được bảo vệ và kiểm thử. **Đánh đổi:** người dùng phải dùng bản cài để kết nối executor thật; sửa UI xong chưa tự giải quyết các gate vận hành.

### Phương án B — chỉ triển khai nếu người dùng muốn development executor thật

Không thể đạt bằng cách xóa `PACKAGED_REQUIRED` hoặc truyền giả `--runtime-mode packaged`. Cần một packet riêng:

1. Định nghĩa loại node development, identity, source fingerprint và quyền operator chấp nhận.
2. Cô lập profile/data root/credential khỏi production; kiểm tra không hai process cùng giữ writer.
3. Xác minh đường chọn Python/agent/source và lifecycle đúng dev contract.
4. Áp dụng đủ enrollment, revoke, workspace generation, policy, audit và no-replay như packaged.
5. Kiểm thử âm tính credential isolation, source drift, wrong-target, duplicate request và restart.
6. Thử nghiệm node dev có giới hạn trước; không tự nâng thành production.

Nhánh B ảnh hưởng boundary tin cậy và runtime, không gộp vào việc “gom setting”. Kế hoạch chính bên dưới mặc định **A**; đây là đề xuất để duyệt, chưa phải quyết định thay người dùng.

## 5. Các giai đoạn thực hiện và cổng nghiệm thu

| Giai đoạn | Kết quả cần có | Phạm vi | Điều kiện chuyển bước |
|---|---|---|---|
| G0. Chốt baseline & nháp | Manifest thay đổi, quyết định giữ/điều chỉnh nháp, nguồn proof hiện tại | Git/source/diagnostics local, chỉ đọc trước | Không xung đột; không mất evidence; không lẫn process/dev/packaged |
| G1. Chốt UX và luồng | Wireframe ngắn, bảng trạng thái và câu chữ, phương án A/B | Thiết kế và tài liệu | Người dùng duyệt bố cục và vai trò `npm start` |
| G2. Hoàn thiện source | Setup thống nhất, admin shortcut an toàn, trạng thái đúng | Renderer + IPC cần thiết + focused tests | Không thay quyền/cấu hình ngoài ý muốn; không thêm control plane mới |
| G3. Kiểm thử local | Behavior tests, security negatives, visual/keyboard QA | Fixture/local preview cô lập | Không còn lỗi liên quan; bản nháp được acceptance đúng fingerprint |
| G4. Đối chiếu và cập nhật Ubuntu | Exact package/service identity, schema/auth phù hợp, admin thật | Ubuntu có tên đích và quyền triển khai riêng | Backup/rollback khả dụng; deploy được phép; health không thay cho identity proof |
| G5. Kết nối Windows thật | Đúng packaged identity, approved node, workspace/account/policy | Windows + Ubuntu operator | Từng gate có receipt đúng máy/phiên bản; không bypass activation |
| G6. Kiểm tra nhiều máy & task | Hai browser cùng admin, read-only rồi bounded task | Đúng máy/target người dùng chọn | Kết quả đúng; không duplicate effect, không wrong-target |
| G7. Bàn giao | Hướng dẫn ngắn, current-state rõ, Git delivery nếu được yêu cầu | Docs/evidence và delivery có phép | Người dùng thao tác được, rủi ro còn lại được ghi rõ |

G2–G3 không phụ thuộc quyền SSH Ubuntu. G4 có thể chuẩn bị kiểm tra chỉ đọc song song, nhưng **không bắt đầu deploy/migration** chỉ vì UI đã xanh. G5/G6 không chạy trước khi server và client có contract tương thích đã được xác minh.

### G0 — bảo toàn công việc và chốt hiện trạng

1. Xác nhận root, branch, HEAD, diff liên quan và active jobs; không dùng baseline cũ để overwrite.
2. Đánh dấu năm file nháp ở mục 2.3, giữ nguyên `.coding-tools` và artifacts.
3. Chốt patch candidate sẽ hoàn thiện; nếu muốn bỏ nháp, lấy chỉ đạo rõ và chỉ bỏ đúng hunk của đợt này.
4. Xác định runtime Windows là dev hay installed, process owner, workspace và source/package lineage; không đọc raw credential.
5. Kiểm tra lại Ubuntu root/health và login page. Chỉ thử quyền operator khi chủ máy tự đăng nhập hoặc cung cấp đường xác thực được hỗ trợ; không đưa token vào chat/URL/log.

**Dừng nếu:** concurrent edits trùng file chưa phân biệt được, wrong workspace/host, job còn đang sử dụng write lease, activation epoch ở `FAILED/CLOSED`, hoặc thiếu quyền thay process. Với epoch đã hết hạn, chỉ dùng lifecycle command chính thức sau khi owner xác nhận cửa sổ refresh; không sửa JSON/ledger bằng tay.

### G1 — review màn hình trước khi code tiếp

1. Một mục “Thiết lập hệ thống”; thử 3 mẫu màn hình: dev bị chặn, packaged chờ duyệt, packaged sẵn sàng.
2. Trạng thái Windows và Ubuntu đặt cạnh nhau, không gộp một chấm xanh chung.
3. Nút chính chỉ làm một việc, ghi đúng tác động: mở trang / gửi yêu cầu / kiểm tra / chọn thư mục / khởi động lại.
4. Admin shortcut có địa chỉ đích nhìn thấy được. Khi server không có console hoặc sai phiên bản, báo rõ, không giả button là proof khả dụng.
5. Tiếp tục được sau khi đóng/mở cửa sổ; origin là setting không bí mật, không tự tạo request mới khi reload.

**Đạt khi:** người dùng nhìn màn hình biết việc tiếp theo và máy nào phải xử lý mà không cần đọc mã lỗi.

### G2 — phạm vi sửa source

| Nhóm | File dự kiến | Nội dung |
|---|---|---|
| Cấu trúc và copy | `renderer/index.html` | Một entry, khung tiến độ, server/admin action, cấp độ chi tiết |
| Trạng thái và tương tác | `renderer/app.js` | Ánh xạ typed state, fresh/stale, no duplicate enrollment, read-only refresh, resume |
| Trình bày | `renderer/settings-compact.css` | Nội dung dễ đọc, không card lồng nhiều tầng, focus và responsive |
| Mở browser | `electron/main.js`, `electron/preload.js` | IPC chỉ dành manager, HTTPS origin không credential/path/query/fragment; không save/restart/enroll |
| Test UI | `tests/settings-redesign.test.js`, test setup behavior mới nếu cần | Kiểm tra thực thi trạng thái/navigation, không chỉ tìm chuỗi HTML |
| Test IPC | `tests/system-setup-console.test.js` | Caller deny, input deny, đúng origin/root, không side effect |
| Hướng dẫn | Tài liệu setup/current-state phù hợp | Phân biệt dev/installed/admin/execution, không sửa chronology cũ |

Không sửa `controlPlaneEnrollment.js` chỉ để nới packaged guard. Chỉ mở rộng redacted projection nếu review chứng minh thiếu field cần thiết; phải có test giới hạn dữ liệu trả về và không đọc credential vào renderer.

### G3 — validation nhỏ nhất đủ phát hiện hồi quy

Các lệnh dự kiến trên Windows, sau khi source candidate đã được hoàn thiện:

```powershell
node --check renderer/app.js
node --check electron/main.js
node --check electron/preload.js
node --test tests/settings-redesign.test.js tests/central-executor-handoff-ui.test.js tests/control-plane-enrollment.test.js tests/control-plane-authority-status.test.js tests/control-center-manager.test.js tests/system-setup-console.test.js
npm test
git diff --check -- renderer electron tests docs/260922_SYSTEM_SETUP_SIMPLIFICATION_PLAN.md
```

- Bổ sung assertions: alias `#deploy/#workspace/#settings` về cùng setup shell; không đổi nhầm target; refresh không start/restart; approved node không đòi pairing lại; stale authority không xanh; lỗi không làm mất cấu hình.
- IPC: từ chối non-manager, `http:`, `file:`, `javascript:`, userinfo, `/mcp`, query, fragment; đường hợp lệ chỉ mở root HTTPS, không gửi bí mật/cấp quyền.
- Visual QA: dùng URL preview có `?preview=1`; kiểm tra light/dark, 375/768/1024/1440 px, bàn phím, focus, central-dev guard và không tràn ngang; mock/fixture phải ghi rõ, không gán kết quả đó cho runtime thật.
- Không chạy toàn Cargo/MCP mỗi lần sửa nhãn UI. Nếu build artifact mới để cài, chạy các gate packaging mà repository quy định và lưu kết quả theo đúng source fingerprint.

Đối với release Control Plane được build từ Windows, phải chạy thêm lane artifact sau mỗi thay đổi builder/launcher:

```powershell
python -m unittest control-plane.tests.test_release_artifact
```

Điều kiện bắt buộc là bốn member `.sh` trong archive có mode `0755`, không còn CRLF và qua `bash -n` trong WSL/Ubuntu. Test chạy shell trực tiếp trên Windows được skip vì đó là giới hạn host (`WinError 193`), không phải skip cho archive mode. Nếu test live launcher trong WSL timeout ở một POST sau khi `/healthz` đã lên, ghi nhận riêng là host-lane timing và chạy lại isolated với log stderr; không dùng timeout đó để tuyên bố package/live PASS hoặc tự deploy.

Kiểm tra packaged candidate cô lập, không đụng `dist`/cài đặt hiện tại:

```powershell
$out = "output/packaged-candidate-$((Get-Date).ToString('yyyyMMdd-HHmmss'))"
npx electron-builder --dir --config.directories.output=$out
$env:CODEX_PACKAGED_APP_ROOT = (Resolve-Path "$out\win-unpacked").Path
node scripts/packaged-recovery-smoke.js
Remove-Item Env:CODEX_PACKAGED_APP_ROOT -ErrorAction SilentlyContinue
```

Lệnh smoke tự kiểm tra resource/adapter exactness, smart-v3 contract, recovery host, supervisor fail-closed và production descriptor/task isolation. Nếu thư mục cũ báo `EBUSY`, không xoá cưỡng bức; dùng một tên `$out` mới và ghi lại fingerprint mới.

**Dừng nếu:** test còn fail, chỉ có regex pass mà chưa thử hành vi, visual không đọc được, IPC mở URL tùy ý hoặc số liệu runtime bị bịa.

### G4 — xử lý Ubuntu đang chạy bản cũ

1. Operator đối chiếu đúng host, service/unit, process, package path, source fingerprint, schema, auth mode, private HTTPS proxy/certificate và admission. Không dùng `declared_source_revision` đơn độc làm attestation.
2. Xác nhận package đích có feature set cần dùng. Hiện server tự báo schema 19/legacy auth trong khi source là schema 24; phải coi là **version/contract gap**, không thử account flow mới trên giả định chúng giống nhau.
3. Trước deploy/migration: có quyền SSH/service cụ thể, database backup nhất quán, integrity result, package cũ và phương án restore đã kiểm tra. Đối chiếu inflight/unknown actions trước chuyển dịch vụ.
4. Khi được cho phép, deploy package đã kiểm thử bằng runbook hiện có; một writer DB, không chép SQLite đang chạy bằng thao tác file tùy tiện. Không mở admission chỉ để che lỗi health.
5. Readback: service instance/package identity/schema/auth/private origin đúng; login, session, CSRF và redaction đúng. Nếu cần OAuth config, dùng quy trình credential được bảo vệ, không công bố secret trong terminal/chat.
6. Giữ admission `recovery` cho đến khi gate review thích hợp cho phép bước kế tiếp. Các thao tác browser có trong source không tự cho phép mở admission hoặc shell.

**Rollback:** không chạy binary cũ trực tiếp lên DB đã migrate nếu không có chứng minh tương thích. Dùng recovery/restore candidate cô lập và reconcile các receipt/effect sau thời điểm backup; không xóa audit để quay về trạng thái “sạch”.

**Đạt khi:** exact server identity và các route/auth cần dùng đã được xác minh; không chỉ `/healthz=200`. Nếu chưa có quyền deploy, G4 ghi rõ blocked, G5/G6 chưa được coi là hoàn tất.

### G5 — kết nối Windows và tài khoản bằng đường chính thức

1. Chọn installed candidate đã được xác minh; kiểm tra identity/source và role `central_executor`. Không để dev và packaged cùng chiếm runtime production.
2. Phân biệt **identity/runtime bootstrap** với **fullyReady**: phải biết đúng process trước; không yêu cầu `fullyReady=true` trước pairing vì readiness cuối còn phụ thuộc pairing/policy.
3. Khôi phục request đang có bằng receipt/config được hỗ trợ. Chỉ gửi mới khi thật sự chưa có request; không lặp request chỉ vì receipt stale.
4. Operator mở admin, kiểm tra tên/định danh máy, duyệt request đúng đích. Không suy operator approval từ việc máy xuất hiện trong inventory.
5. Windows reconcile trạng thái approved và credential bằng node-agent/SecretStore hiện có; không dán Runtime API Key/Tunnel/operator token vào Windows.
6. Chủ máy chọn thư mục local, bắt đầu bằng quyền chỉ xem cho canary. Không tự nâng thành quyền ghi/chạy để qua test.
7. Dùng account/OAuth/binding flow hiện có để cấp đúng machine/workspace generation. Login operator và OAuth tài khoản ChatGPT là hai quyền khác nhau.
8. Đồng bộ policy/route đúng device, workspace và generation; kiểm tra freshness. Thiếu local executor là lỗi runtime, không yêu cầu duyệt máy lại.
9. Nếu cần activation/restart, lấy cửa sổ bảo trì và authority riêng; dùng preflight/activation theo runbook, không sửa tay epoch/closure/ledger và không tái sử dụng receipt HEAD khác.
10. Đọc lại `localReady`, `centralConnected`, `authorityReady`, `fullyReady`, running/disk revisions và strict client discovery. Compatible ACK không thay thế client thật đã rediscover.

**Đạt khi:** UI và structured state nhất quán; không mất cấu hình sau mở lại; lỗi ở tầng nào chỉ rõ tầng đó. Chưa gọi là thành công tác vụ khi chưa chạy G6.

### G6 — người dùng kiểm tra vận hành thật

| Ca | Cách kiểm tra | Kết quả bắt buộc |
|---|---|---|
| U01 | Mở setup từ sidebar và các link cũ | Cùng một nơi, không trang cấu hình mâu thuẫn |
| U02 | Chạy bằng `npm start` | Thấy rõ dev; unsupported action không giả thành công; mở admin không đổi role |
| U03 | Nhập URL sai / URL chứa credential | Bị từ chối trước shell/navigation; không lưu bí mật |
| U04 | Gửi pairing một lần, reload cửa sổ | Cùng request, không nhân đôi |
| U05 | Chưa duyệt / duyệt đúng máy | Pending và approved phân biệt; chưa tự có quyền task |
| U06 | Ubuntu không truy cập được | Báo chưa xác minh; giữ cấu hình, không fallback sang máy khác |
| U07 | Approved nhưng runtime Windows chưa ready | Báo đúng lỗi local, không bắt đăng ký lại |
| U08 | Workspace đã có nhưng chưa account binding | Không báo sẵn sàng nhận việc |
| U09 | Receipt quyền stale / quyền bị thu hồi | Không giữ trạng thái xanh hoặc chạy với quyền cũ |
| U10 | Mở admin từ hai máy trong mạng được phép | Cùng inventory central, có thời điểm quan sát; không tạo DB thứ hai |
| U11 | Trình duyệt chưa đăng nhập / sai phiên / sai CSRF | Không đọc dữ liệu quản trị hoặc thực hiện mutation trái phép |
| U12 | Read-only canary vào đúng workspace | Có receipt đúng target; không ghi file và không chạy lệnh ngoài scope |
| U13 | Mutation nhỏ được người dùng cấp quyền riêng | Chỉ đúng diff/output mong đợi; retry không lặp effect |
| U14 | Hai client cùng account chọn target đã cấp | Cùng target hợp lệ; task pinning và lease được giữ, không retarget âm thầm |
| U15 | Đóng/mở UI, ngắt/nối mạng trong phạm vi thử được cho phép | Cấu hình bền vững; active job không bị tuyên bố kết thúc sai |
| U16 | Một công việc thật do người dùng chọn | Người dùng kiểm kết quả độc lập; technical PASS không tự thành outcome PASS |

U13–U16 cần scope/cửa sổ thử cụ thể. Không tự tạo “công việc thật” để hợp thức hóa nghiệm thu. Không hứa máy Windows tắt hoặc chưa đăng nhập vẫn thực thi được; WOL/no-login/HA ngoài phạm vi đợt này.

### G7 — bàn giao và ranh giới hoàn thành

Tách ba mức:

1. **Dùng được về kỹ thuật:** source/test, đúng package/service, setup không bế tắc, strict runtime/client và canary đạt.
2. **Hiệu quả trong công việc thật:** U16 có kết quả người dùng xác nhận; còn thiếu thì ghi thiếu, không suy từ health hoặc test.
3. **Sẵn sàng phát hành:** packaging/CI, upgrade/rollback/recovery, tài liệu và delivery gates phù hợp. Không tự đánh dấu release-ready từ local preview.

Nếu được yêu cầu commit/push sau này: review đúng phạm vi, kiểm secret, giữ toàn bộ `.coding-tools` trừ đúng hai SQLite sidecars được phép; chạy `npm run stage:coding-tools-delivery` rồi `npm run check:coding-tools-delivery` trước mỗi commit/push. Không suy yêu cầu xem kế hoạch thành quyền delivery.

## 6. Điều kiện người dùng cần xác nhận trước khi cho chạy

- [ ] Duyệt một setup entry và tận dụng operator console Ubuntu hiện có.
- [ ] Chọn phương án A cho đợt đầu, hoặc yêu cầu thiết kế nhánh B development executor riêng.
- [ ] Review/duyệt candidate ở năm file chính và tests/docs liên quan; không coi local proof là nghiệm thu packaged/live.
- [ ] Khi tới G4: xác nhận host, package đích, quyền deploy/migration/restart và cửa sổ bảo trì Ubuntu.
- [ ] Khi tới G5: xác nhận bản Windows, workspace/phạm vi quyền và cửa sổ thay runtime.
- [ ] Khi tới G6: chọn máy kiểm tra thứ hai, tài khoản, canary và một công việc thực tế; mutation có phạm vi riêng.
- [ ] Commit/push/release chỉ khi được yêu cầu rõ; không nằm trong phê duyệt UI mặc định.

## 6.1 Phiếu chạy để người dùng kiểm tra

Dùng một phiếu cho mỗi đợt kiểm tra. Không ghi token, API key, cookie, private key, credential DPAPI, context ID hoặc nội dung dữ liệu nhạy cảm vào phiếu, terminal capture hay ảnh màn hình. Các trường `PASS` chỉ được đánh dấu sau khi có receipt/log tương ứng; nếu chưa chạy thì để `NOT RUN`, nếu gặp điều kiện dừng thì để `BLOCKED`.

### A. Thông tin đợt chạy

```text
Ngày/giờ bắt đầu (GMT+7): ____________________
Người vận hành/operator: ______________________
Windows machine/device ID: ____________________
Ubuntu origin (HTTPS origin, không credential): ____________________
Candidate/package fingerprint: _________________
Cửa sổ bảo trì đã được duyệt:  YES / NO / N/A
Backup/rollback receipt: _______________________
```

### B. Preflight read-only trên Windows

Chạy từ `E:\DEV\Codex-web` và lưu output không chứa secret:

```powershell
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git status --short
npm run dev:status
```

Ghi kết quả:

| Kiểm tra | Kết quả | Evidence/timestamp |
|---|---|---|
| Root/branch/HEAD đúng checkout | `PASS / BLOCKED` | ____________________ |
| Dirty files đã phân loại, không có writer xung đột | `PASS / BLOCKED` | ____________________ |
| Runtime mode (`development`/`packaged`) đã xác minh | `PASS / BLOCKED` | ____________________ |
| `running_revision` và `disk_revision` đã đối chiếu | `PASS / BLOCKED` | ____________________ |
| `components_ready`/`fully_ready` được đọc từ snapshot mới | `PASS / BLOCKED` | ____________________ |
| `connector_rediscovered=true` (chỉ đánh dấu sau strict discovery) | `PASS / NOT RUN` | ____________________ |

Nếu `state=MISSING`, epoch `FAILED/CLOSED`, `runtime_update_incomplete=true` hoặc còn active writer chưa rõ chủ, dừng ở đây và ghi `BLOCKED`; không tự restart, sửa epoch/ledger hoặc gửi pairing mới.

### C. Preflight read-only trên Ubuntu

1. Từ máy được phép, mở đúng HTTPS origin đã ghi ở mục A.
2. Đọc root và `/healthz` theo runbook Ubuntu hiện hành.
3. Đối chiếu độc lập service instance, package path/fingerprint, schema, auth mode, admission và database integrity.
4. Đăng nhập operator chỉ trong trình duyệt được kiểm soát; không dán credential vào ứng dụng Windows, URL hoặc phiếu này.

Nếu hostname không phân giải, có thể chạy hai lệnh read-only để phân loại đường mạng trước khi dừng:

```powershell
tailscale status
tailscale ping svhome
```

`svhome` online hoặc `ping` qua DERP chỉ chứng minh Tailscale nhìn thấy node; chưa chứng minh HTTPS Control Plane, certificate, service identity hoặc operator session đã dùng được.

| Kiểm tra | Kết quả | Evidence/timestamp |
|---|---|---|
| Root HTTPS trả đúng Control Plane | `PASS / BLOCKED` | ____________________ |
| Service/package identity khớp candidate đã chọn | `PASS / BLOCKED` | ____________________ |
| Schema/auth contract tương thích client | `PASS / BLOCKED` | ____________________ |
| Backup/rollback/integrity được xác nhận | `PASS / BLOCKED` | ____________________ |
| Operator session/CSRF đúng | `PASS / NOT RUN` | ____________________ |
| Enrollment đúng machine/device ID hiện ra | `PASS / NOT RUN` | ____________________ |

`HTTP 200` hoặc `sqlite_integrity=ok` một mình không đủ để đánh dấu các dòng identity, auth, enrollment hay readiness là `PASS`.

### D. Quyết định chuyển gate

```text
G0 baseline:       PASS / BLOCKED / NOT RUN   Evidence: ____________________
G1 UX review:       PASS / BLOCKED / NOT RUN   Evidence: ____________________
G2 source:          PASS / BLOCKED / NOT RUN   Evidence: ____________________
G3 local proof:     PASS / BLOCKED / NOT RUN   Evidence: ____________________
G4 Ubuntu:          PASS / BLOCKED / NOT RUN   Evidence: ____________________
G5 Windows:         PASS / BLOCKED / NOT RUN   Evidence: ____________________
G6 two-client/task: PASS / BLOCKED / NOT RUN   Evidence: ____________________
G7 handoff/release: PASS / BLOCKED / NOT RUN   Evidence: ____________________
```

Chỉ chuyển sang gate kế tiếp khi gate hiện tại có evidence cụ thể và không còn điều kiện dừng. Nếu G4 `BLOCKED`, không chạy G5/G6. Nếu G5 mới chỉ có `approved` nhưng chưa có `authorityReady`, `fullyReady` và strict discovery, không chạy mutation. Nếu G6 chưa có outcome độc lập của công việc thật, không gọi là hoàn tất sản phẩm.

## 7. Checkpoint của lượt lập kế hoạch

- **Hoàn tất trong đợt tiếp tục:** revalidate source/setup candidate, focused setup **57/57**, Python store **86/86**, HTTP API **43/43**, full Node/Electron **944/944**, syntax **3/3**, scanner/secret guard PASS; build candidate packaged cô lập mới và `packaged-recovery-smoke.js` `ok=true`; archive Control Plane build-from-Windows mode/LF proof đạt; cập nhật worksheet vận hành và sửa chronology DNS sai hostname; không có live mutation.
- **Chưa hoàn tất:** G4 đối chiếu/deploy exact Ubuntu package, G5 installed activation, G6 strict client discovery/canary/natural task và G7 release vẫn chưa có bằng chứng đủ.
- **Sản phẩm thay đổi:** candidate ở `renderer/index.html`, `renderer/app.js`, `renderer/settings-compact.css`, `electron/main.js`, `electron/preload.js`; Control Plane liveness/authority hardening ở `control-plane/control_plane/node_agent.py` và `control-plane/control_plane/store.py`; release archive portability ở `scripts/build-control-plane-release.py`; regression/contract assertions ở `control-plane/tests/test_http_api.py`, `control-plane/tests/test_store.py`, `control-plane/tests/test_release_artifact.py` và `tests/system-setup-console.test.js`; các test liên quan và tài liệu kế hoạch này. Đã có packaged candidate cô lập, nhưng chưa installed/live acceptance.
- **Git:** chưa commit/push; HEAD không đổi; runtime evidence `.coding-tools` và file evidence deleted ngoài candidate vẫn được giữ nguyên để reconcile riêng trước delivery.
- **Jobs của đợt này:** preview server PID `31316` và hai browser QA session đã được đóng sau khi lưu visual artifacts; không dừng hoặc suy trạng thái của runtime sản phẩm khác.
- **Runtime Windows lần đọc cuối:** `npm run dev:status` lúc `2026-09-22T08:43:59.934Z` là `MISSING`, descriptor PID `23008`, running revision `none`, disk `99b926…`, MCP current `396e169…`; `components_ready=false`, `fully_ready=false`, `runtime_update_incomplete=true`, `connector_state=CHANGED_NEEDS_DISCOVERY`, `connector_rediscovered=false`.
- **Activation/ledger recheck:** epoch hiện tại `FAILED / full_clean_activation / admission=CLOSED / ACTIVATION_REQUEST_EXPIRED` (failed `07:09:18Z`), Recovery Host PID `14300` còn sống; owner cần quyết định refresh chính thức sau lifecycle check. Census/ledger không được dùng để mở epoch bằng tay.
- **Hệ thống ngoài:** các lỗi DNS/TLS trong chronology 14:24–14:26 dùng nhầm hostname thiếu số `2` và đã được phân loại lại; origin đúng `https://svhome.tail0e4032.ts.net/` hiện trả HTTP 200 cho `/` và `/healthz`. Vẫn chưa login operator, approve enrollment, cấp policy/binding, mở admission, deploy hoặc restart dịch vụ sản phẩm.
- **Bước kế tiếp chính xác:** không tạo refresh/restart thứ hai từ lượt này; owner kiểm tra lifecycle/lease/job rồi cấp authority cho một refresh chính thức nếu cần. Candidate để review/cài thử là thư mục Temp và hai hash ở trên, không dùng các candidate cũ. Sau khi có cửa sổ cài đặt/rollback, đối chiếu exact identity rồi mới chạy installed activation; giữ nguyên enrollment `pending_operator_approval`, operator đăng nhập Control Plane Ubuntu và duyệt đúng enrollment hiện có. Trước account flow phải đối chiếu schema 19/auth legacy live với source schema 24 và xác định quyền deploy/restart/backup/rollback. Không gửi pairing mới hoặc mở G4–G6 bằng giả định schema tương thích.
