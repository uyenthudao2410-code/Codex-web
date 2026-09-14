# Kế hoạch khép lỗi khởi động và chuyển máy

Problem tham chiếu: `BOOT_HOST_TRANSITION_RECONNECTION_LOOP`.

Ngày lập: 14/09/2026, múi giờ Việt Nam. Repository: `E:\DEV\Codex-web`.

**Đây là kế hoạch triển khai, không phải biên bản nghiệm thu hoặc lệnh cấp quyền.** Tài liệu không tạo canonical Problem/RUN, không sửa sản phẩm, bật autorun, thao tác tài khoản, restart máy/dịch vụ, commit/push, cài đặt hoặc phát hành. Mỗi bước có tác động cần đúng quyền và đúng máy đích khi triển khai.

## 1. Đích đến và quyết định sản phẩm

Sau cấu hình ban đầu hợp lệ trên từng máy, người dùng mở ứng dụng hoặc đăng nhập Windows theo chế độ đã bật và sử dụng được đúng workspace. Không cần sửa source, xóa dữ liệu, đăng nhập lại hoặc chạy nhiều lệnh refresh để vượt lỗi lifecycle nội bộ.

Phương án khuyến nghị:

- **Dùng hằng ngày trên nhiều máy:** bản cài Windows đã nghiệm thu. Người dùng chọn một lần việc tự mở cùng Windows và tự chạy dịch vụ; không âm thầm bật các tùy chọn đó.
- **Phát triển tại checkout:** giữ `npm start` / `npm run dev` làm entry point cold-start được hỗ trợ. Giữ development autorun bị vô hiệu để tránh khởi chạy checkout cũ. Mở trực tiếp Electron development phải hướng dẫn về entry point hỗ trợ, không hứa có Windows autorun.
- **Bản cài mở trực tiếp/logon và watchdog:** dùng cùng quyết định recovery trong Recovery Host, tái sử dụng FullCleanActivation; không thêm supervisor, daemon, database hoặc public MCP tool mới.
- **Đăng nhập tài khoản, cấu hình máy và connector là ba lớp riêng.** Máy mới cần setup/login khi chưa có quyền hợp lệ. Không coi phiên hết hạn hoặc quyền bị thu hồi là lỗi có thể vượt bằng refresh.
- **Hai máy là hai endpoint.** Coding-VP Live và Coding MCP qua tunnel riêng không bị gộp. Chỉ đổi mục tiêu ghi khi người dùng chọn/chấp nhận đích mới một cách rõ ràng.

Quyết định này phải nằm trong Problem Revision được controller chấp nhận trước W2. Nếu chủ đích thực tế chỉ là development CLI, ghi phạm vi hẹp đó rõ ràng; không dùng thành công CLI để đóng tiêu chí installed/logon hoặc tự âm thầm bỏ tiêu chí hai máy.

## 2. Baseline và cách hiểu bằng chứng

Git được kiểm tra lại khi lập kế hoạch: `main`, HEAD `ae04947d5969e9ee92bf1fe7532bf30e186f8280`, local chậm ref `origin/main` một commit, working tree có source/test/docs và runtime evidence chưa commit. Không fetch/merge/rebase trong lượt lập kế hoạch. Các ref có thể thay đổi trước lúc triển khai.

| Quan sát từ đợt audit 14/09 | Đã chứng minh | Chưa chứng minh |
| --- | --- | --- |
| Current contract `d69436...`, ACK `d69436...`; epoch `activation-mu0nwtkj-5b558ae4a52562fb6c739de983b52912` | Development runtime READY/OPEN, compatible bootstrap hợp lệ; status lúc khoảng 10:28 còn xanh | Reboot tiếp theo, logon bản cài, máy thứ hai hoặc tác vụ người dùng hoàn tất |
| Working-tree edge `d694 -> d52` và transitive closure | Khắc phục thiếu khai báo additive và hỗ trợ membership nhiều phiên bản trong focused tests | Mọi thay đổi schema tương lai tự tương thích |
| CLI cold-start tests 16/16; terminal-epoch guards 2/2 | CLI có đường tạo epoch mới; không được spawn MCP trong READY cũ | Direct installed/logon/watchdog tự chuyển đúng sang epoch mới |
| Census chỉ đọc khoảng 4,2 giây, ledger 77.737.984 bytes | Snapshot warm, integrity ok, không foreign-key error/projection drift/unexplained active residue | Phân bố cold latency, hiệu quả timeout trên máy chậm |
| Test `test_runtime_startup_preserves_stale_candidates_until_explicit_reconcile` còn đỏ | Expected component set cũ thiếu hai component continuation đã có ở HEAD | Integrated proof xanh cho exact gói sửa |
| Tìm capsule theo tên cold-boot/reconnection chưa có kết quả lúc khoảng 10:18 | Chưa có canonical lineage được chứng minh cho tên Problem này | Không được suy ra không có Problem tương tự dưới tên khác |

Không chạy lại toàn bộ audit chỉ để bắt đầu. W0 thu lại các identity/state dễ thay đổi và tái dùng proof chỉ khi exact inputs còn khớp. Số test trên là kết quả audit trước, không phải kết quả thực thi kế hoạch.

Các nguồn triển khai chính:

- [CLI cold-start](../scripts/dev-ui-lifecycle.js), [runtime startup/recovery](../electron/services/runtimeOrchestrator.js), [Recovery Host](../electron/services/recoveryHost.js).
- [FullCleanActivation](../electron/services/fullCleanActivation.js), [Python discovery](../electron/services/environmentService.js), [command runner](../electron/services/commandRunner.js).
- [Bootstrap Python](../resources/coding-tools-mcp/coding_tools_mcp/activation_lifecycle.py), [reviewed compatibility graph](../resources/coding-tools-mcp/coding_tools_mcp/tool_contract.py).
- [Census helper](../resources/coding-tools-mcp/coding_tools_mcp/activation_ledger_census.py), [immutable census](../resources/coding-tools-mcp/coding_tools_mcp/lifecycle_census.py).
- [Session](../electron/chatViewController.js), [development settings](../electron/services/settingsStore.js), [endpoint identity](../resources/coding-tools-mcp/coding_tools_mcp/endpoint_identity.py).
- [PRL public input](../resources/coding-tools-mcp/coding_tools_mcp/tool_schema.py), [PRL semantics](../resources/coding-tools-mcp/coding_tools_mcp/problem_lineage.py), [release checklist](RELEASE_CHECKLIST.md).

## 3. Tiêu chí đóng phải được đóng băng trước khi sửa

Các mã C01–C12 dưới đây là mã tiêu chí trong kế hoạch/Problem capsule, không phải enum runtime mới.

| ID | Điều kiện phải đạt | Bằng chứng bắt buộc |
| --- | --- | --- |
| C01 | Đúng entry point của mode đã chọn có thể cold-start từ trạng thái process cũ đã mất | Unit/integration và reboot thực tế theo ma trận mục 7 |
| C02 | Chỉ một owner tạo epoch mới; không spawn MCP dưới terminal READY; không handoff khi supervision của chính mình chưa drain | Negative tests + process-bound receipt |
| C03 | Same SHA đã ACK có thể bootstrap dù predecessor list rỗng | Python→Electron integration; không chỉ test hàm membership |
| C04 | Skipped compatible releases hoạt động; changed unknown/breaking contract vẫn cần discovery thật | Exact contract diff/graph proof, attestation negatives, connector smoke |
| C05 | Dò Python, census, chờ lock và cleanup đều kết thúc hữu hạn và trả đúng loại lỗi | Fake-clock tests + isolated forced-timeout/lock-reacquisition proof |
| C06 | manualStop, active write/job/lease, foreign identity và source drift không bị recovery vượt qua | Mỗi invariant có test riêng với các điều kiện còn lại hợp lệ |
| C07 | Host-only restart rồi Tunnel loss không đưa người dùng vào retry loop | Isolated process test và authorized live fault case |
| C08 | Phiên hợp lệ được giữ; thiếu/revoked login hoặc cấu hình được chỉ rõ đúng lớp | Session tests và quan sát người dùng; không đọc/copy credential |
| C09 | Hai máy dùng đúng endpoint/workspace/tunnel; không silent mutating failover | Hai bộ receipt máy vật lý độc lập và thao tác đọc thật trên từng máy |
| C10 | Source/proof/acceptance/runtime/artifact liên kết exact; rollback không xóa lịch sử hoặc dùng sai authority | Canonical checkpoint, artifact SHA, rollback test |
| C11 | Không cần sửa source, xóa state hoặc refresh thủ công trong các ca vận hành thành công thuộc phạm vi | Bảng kết quả đầy đủ, gồm cả fail/retry; không chọn riêng ca xanh |
| C12 | Người dùng xác nhận kết quả sử dụng thực tế của đúng Problem Revision, không có blocker bắt buộc còn mở | Runtime-derived independent outcome receipt và transition được phép |

Protected invariants: fail-closed admission; immutable terminal epochs; exact device/workspace/process/server binding; source authority; một writer mỗi phạm vi; không mất lịch sử; không credential/PII/private reasoning trong evidence; không tự cấp consent; không ninth public tool; không đổi routing/P5/promotion.

**Ba mức đầy đủ:**

1. **Kỹ thuật:** W1–W5 đạt trên exact source, có acceptance và runtime/process proof phù hợp. Có thể đề nghị provisional resolution qua guard hiện có; chưa tự nhận user outcome.
2. **Vận hành thực tế:** W6 đạt trên hai máy và có sử dụng tự nhiên/xác nhận độc lập. Đây mới đủ cơ sở đề nghị `RESOLVED_CONFIRMED`, cùng các điều kiện PRL đang được server thực thi.
3. **Phát hành:** candidate/artifact/delivery/rollback đạt và có quyền phát hành. Local confirmed outcome không tự động cho phép public release; public release cũng không thay thế user outcome.

## 4. Thứ tự, ownership và điểm dừng

Một canonical Problem, một engineering RUN nhiều WAVE khi contract/authority cho phép. W0 phải kiểm tra trùng lặp trước khi mở mới. Không đổi objective của RUN pagination cũ thành cold-start và không đóng RUN khác để làm census đẹp.

| Gói | Kết quả | Phụ thuộc | Owner triển khai | Phạm vi ghi chính |
| --- | --- | --- | --- | --- |
| W0 | Baseline, Problem Revision, scope và authority rõ | Không | Controller | Canonical actions qua connector; không sửa SQLite |
| W1 | Oracle đáng tin và exact-SHA/compatibility hoàn chỉnh | W0 | MCP writer; controller review | `activation_lifecycle.py`, `tool_contract.py`, Python tests, `tests/runtime-lifecycle.test.js` |
| W2 | Recovery Host tạo epoch mới an toàn cho entry points hỗ trợ | W0, W1 contract | Một lifecycle writer | `recoveryHost.js`, `runtimeOrchestrator.js`, lifecycle adapters/tests liên quan |
| W3 | Bounded discovery/census/cleanup | W0 | Một timeout writer | `environmentService.js`, `commandRunner.js`, `fullCleanActivation.js`, helper/tests cần thiết |
| W4 | Phân loại lỗi/UI và setup từng máy rõ ràng | W1; interface W2/W3 đã chốt | Controller/MCP writer | Projection/UI/session tests, maintained docs; không đổi credential store nếu không có reproduction |
| W5 | Exact integration, acceptance, controlled activation và candidate | W1–W4 | Controller + proof plane | Integration fixes hẹp, checkpoint/delivery theo quyền |
| W6 | Ma trận hai máy và sử dụng tự nhiên | W5 | Operator + controller quan sát | Chỉ lifecycle operations đã cấp quyền và evidence runtime |
| W7 | Final reconciliation và đóng Problem đúng quy tắc | W6 | Controller có authority | PRL/acceptance/report ACK qua contract công khai |

Đường chính: `W0 → W1 → W2 → W4 → W5 → W6 → W7`. W3 có thể làm song song W1/W2 **sau khi chốt interface**, bằng candidate-only hoặc worktree ngoài `.coding-tools`. `fullCleanActivation.js`, `recoveryHost.js` và Node lifecycle tests dễ giao nhau: mọi chỉnh sửa giao nhau do một writer tích hợp tuần tự, không hai agent sửa cùng file.

Giám sát dùng Job/operation/epoch receipts và watchdog đã có; controller theo dõi trong lúc worker thực hiện. Không thêm automation theo lịch hoặc watcher cạnh tranh. Không chạy restart song song với writer/proof đang cần runtime đó.

Mỗi WAVE kết thúc bằng checkpoint người dùng đọc được: đã làm gì; Git/RUN/WAVE/epoch; exact proof; lỗi/blocker; còn gì; next action. `ACCEPTING` phải accept/reject trước WAVE tiếp theo. Một REPLAN phải nêu dữ liệu/chiến lược nào đã thay đổi, không retry nguyên xi.

## 5. Nội dung triển khai từng gói

### W0 — Khóa đúng phạm vi, không mất các sửa đang có

1. Xác minh root/branch/HEAD/status, changed files, runtime-loaded revisions và process identity. Liệt kê owner của source đang dirty và active RUN/WAVE/job/write lease; hiện đã có công việc khác cập nhật `.coding-tools`.
2. Lập exact-byte manifest cho các sửa census/compatibility có sẵn. Phân biệt file do gói này cần tiếp nhận với thay đổi của tác vụ khác. Không restore/reset/clean, không stage cả source mù.
3. Giải quyết baseline chậm upstream bằng một bước integration được phép, sau khi bảo toàn WIP và owner đồng ý. Không `pull --rebase` trên worktree dirty. Nếu HEAD thay đổi, tạo/rebind WAVE và invalid proof bị ảnh hưởng; đừng làm tới cuối rồi mới phát hiện source drift.
4. Qua connector đúng endpoint/workspace, đọc danh sách Problem và exact capsule để tìm trùng. Nếu chưa có, dùng `task_control(action="problem", problem_event.operation="open")` với `task_class=bugfix`, `engineering_floor=REQUIRED` và C01–C12.
5. Capsule chỉ chứa `objective_summary`, `acceptance_criteria` gồm `criterion_id/summary`, `protected_invariants`, `constraints`, `unresolved_conditions`; giữ trong giới hạn privacy 8 KiB. Không nhét transcript/log/source vào capsule. ID/fingerprint/clock/host authority lấy theo server; không tự tạo receipt.
6. Nếu tool surface/attested controller không sẵn sàng, ghi blocker đúng lớp. Có thể hoàn thiện packet/candidate read-only; không đi đường SQLite hoặc giả request ChatWeb để lấy lease/acceptance.
7. Chốt quyền thao tác service, candidate build/install, hai máy đích và maintenance window riêng. Kế hoạch không tự cấp các quyền này.

**Exit:** đúng Problem ID + revision + contract fingerprint; base manifest; ownership; không overlapping writer; cấu hình entry points mục 1 đã được chấp nhận. Các sửa cũ được giữ hoặc nhận exact-byte theo adoption guard, không mặc nhiên xem là durable-accepted.

### W1 — Sửa bootstrap và lấp khoảng trống oracle

1. Giữ reviewed edge `d694 → d52` và closure; không thêm hash không được chứng minh. Có test cycle, unknown root, malformed node, nhánh chung không lặp và contract SHA thực tế.
2. Sửa expected component set cũ trong `test_efficiency_runtime.py` sau khi đối chiếu `runtime_behavior_identity.py`. Không bỏ assertion hoặc đổi production để khớp expected lỗi thời.
3. Đổi gate Python đang yêu cầu predecessor list không rỗng thành điều kiện cho **no-workspace current-process handshake**. Tại Python, chỉ nhận đúng `workspace_context`, epoch đang admission-closed hợp lệ/chưa hết hạn/chưa failed, current contract/profile hợp lệ và attested ChatWeb. Không coi handshake receipt là quyết định tương thích hay quyền đọc workspace.
4. Recovery Host/Electron vẫn là nơi so current SHA với persisted ACK: same SHA → exact bootstrap; khác SHA trong reviewed closure cùng schema/profile → compatible bootstrap; khác SHA unknown/breaking hoặc chưa có ACK → không mở admission, cần real discovery. Metadata/receipt tổng hợp một mình không đủ.
5. Test đầy đủ Python nhận request → publish bounded receipt → Electron kiểm tra → final census → ACK/open. Case same SHA + zero predecessor phải đạt; thay process/server/epoch/workspace generation hoặc attestation phải bị chặn. Không chỉ test `Set.has()`.
6. Negative tests đặt mọi điều kiện còn lại hợp lệ rồi làm sai đúng một điều kiện, đặc biệt schema/profile/unknown ACK. Có positive control cùng fixture để biết test không bị chặn sớm bởi nguyên nhân khác.
7. Dùng test exact tool contract hiện có làm guard bắt buộc của gói sửa khi schema/registry thay đổi. Thay đổi phải đi kèm quyết định reviewed-compatible hoặc intentional-breaking và kế hoạch discovery; không tự suy luận compatibility chỉ từ version/tool count.

**Exit:** Python/Electron cùng semantics; focused tests xanh; tám public tools không đổi; original lỗi hash không tái hiện; exact same-SHA không phụ thuộc lịch sử predecessor. Nếu public schema thực sự đổi, phải tính lại hash và review delta trước W2/W5.

### W2 — Khép vòng recovery, không nới terminal-epoch guard

Đặt quyết định ở Recovery Host hiện có; adapters CLI/UI/logon chỉ yêu cầu cùng hành vi. Không tạo một state machine thứ hai để thay ActivationEpochStore.

| Trạng thái quan sát | Hành động thiết kế |
| --- | --- |
| Đúng identity, mọi process đang khỏe, source/current receipt khớp | Attach/focus/reuse; không tạo epoch mới chỉ vì mở UI |
| Terminal READY nhưng MCP đã mất; nguồn cũ và ownership xác minh được; có start/recovery intent hợp lệ | Tạo **một epoch mới** qua FullCleanActivation; không spawn vào epoch cũ |
| Host-only restart, primary vẫn sống, receipt hợp lệ | Adopt existing runtime; không đổi process vô ích |
| Sau host-only restart, Tunnel mất và host không còn attestation secret hợp lệ | Không tạo secret thay thế cho MCP đang sống; yêu cầu full-clean operation mới sau census/quiescence |
| Chỉ Tunnel lỗi, host vẫn có attestation binding hợp lệ | Dùng existing tunnel-only recovery sau guard |
| Active epoch đang thực hiện / cùng operation đã tồn tại | Attach/observe operation đó; không restart cạnh tranh |
| Active tool/job/lease/write fence hoặc chưa xác minh PID/identity | Defer/block có typed reason; không đánh đồng unavailable với stopped |
| `manualStop=true` hoặc chưa bật automatic-start intent | Không tự chạy lại primary; explicit Start mới thay đổi intent |
| Source đổi so với durable revision được phép dùng | Đi accepted-code update path hoặc block cần source authority; auto recovery không nạp unaccepted bytes |
| FAILED/malformed epoch, foreign installation/workspace, nguồn không xác minh được | Giữ fail-closed, control plane và hướng dẫn đúng; không tự sửa/ghi lại terminal evidence |

Chi tiết bắt buộc:

1. Giữ `assertMcpReplacementAllowed()` từ chối READY/READY_COMMITTED/FAILED. Thay caller recovery, không xóa guard để đạt xanh.
2. Automatic lifecycle intent phải bắt nguồn từ tùy chọn người dùng được lưu hợp lệ hoặc explicit Start, bound đúng installation/workspace. Không mở rộng ngoại lệ `full_clean_refresh` hiện dành cho explicit dev start thành quyền nạp mọi source dirty.
3. Chỉ tự relaunch revision đã được durable authority cho phép và revalidate exact disk bytes ngay trước mutation. Nếu chưa có authority phù hợp sau reboot, dừng bằng lý do riêng; giải quyết provenance ở W0/W5, không thêm fallback im lặng.
4. Reuse operation ID/single-flight của coordinator. Dispatch handoff sau khi tick/tool boundary hiện tại đã kết thúc, tránh handoff chờ chính `supervisionInFlight` đang gọi nó.
5. Retry chỉ cho transient được phân loại và có evidence mới (ví dụ mạng phục hồi, lock đã được giải phóng). Áp dụng bounded backoff/attempt limit đã có; nếu phải bổ sung limit, chốt trước trong WAVE. Không tạo epoch mới mỗi tick khi cùng blocker chưa thay đổi.
6. Tách start intent của bản cài khỏi development autorun. Bản cài opt-in một lần; không tự sửa registry hoặc Task Scheduler ngoài installer/UI chính thức.
7. Test crash ở trước epoch-create, sau close admission, sau spawn, sau READY commit; chỉ đúng owner được resume/finalize. Không tăng automatic mutation scope cho foreign lease, managed job hay stale target.

**Exit:** isolated real-process harness chứng minh missing MCP dưới READY dẫn tới epoch mới hợp lệ khi được phép; đúng old/new PID/start token; không self-deadlock, double-spawn hay retry storm; manualStop/busy/source drift vẫn chặn.

### W3 — Deadline và cleanup có giới hạn thực

1. Cho `pythonStatus()`/`commandExists()` nhận remaining budget/timeout từ caller. Ưu tiên portable interpreter đúng resource root nếu sẵn sàng; không để nhiều lệnh `where` không giới hạn làm chặn bước trước census.
2. Dùng đồng hồ monotonic cho elapsed/remaining budget của operation. Giữ wall-clock expiry cho signed/durable envelope theo contract hiện hữu; không thay bừa expiry bằng monotonic value.
3. Ngân sách khởi điểm đề xuất để đo trong harness: discovery toàn bộ ≤5 giây, census child ≤30 giây, termination/cleanup ≤5 giây. Exclusive-lock 5 giây nằm **bên trong** child budget, không cộng thêm. Một census call gồm các pha có trần dự kiến 40 giây; đây là mục tiêu kỹ thuật cần kiểm chứng, không phải SLO đã đo.
4. Rà tất cả caller/IPC/bootstrap theo tổng remaining deadline, gồm hai census trước admission. Không để caller hết hạn sớm trong lúc callee vẫn có thể mutate. Giữ durable epoch 600 giây và MCP prepare-fence 55 giây trừ khi một packet riêng có bằng chứng cần đổi; renew cùng fence ở immediate mutation boundary như contract hiện có.
5. Lock contention không phải census timeout: giữ typed cause riêng, không tăng lock wait để vượt qua active writer. Chỉ retry sau snapshot mới và không còn authority xung đột.
6. Khi timeout: dừng đúng child được tạo, chờ exit/close trong cleanup budget, verify không còn lock/process do attempt giữ trước retry. Nếu kết quả terminate chưa xác định, fail-closed và báo cleanup uncertainty, không báo đã dừng.
7. Temporary snapshot của helper phải có ownership rõ và cleanup hợp lệ. Không recursive delete broad TEMP, không xóa `.coding-tools`; crash leftovers chỉ cleanup theo exact manifest của attempt khi an toàn.
8. Receipt giữ stage, typed cause, elapsed, configured budget và outcome cleanup đã quan sát. Không persist stdout/stderr/argv/secret. Không tự đổi public tool schema chỉ để thêm diagnostic nội bộ.

**Test cần có:** fake hanging discovery; interpreter không hợp lệ; lock giữ quá 5 giây; child không phát output; forced timeout trước/giữa snapshot; exit ngay trước timeout; timeout rồi retry lấy lock; stdout malformed/over-limit; cleanup không xác nhận; remaining deadline quá ngắn trước stop. Dùng temp fixture/owned process, không tiêm lỗi vào live ledger.

**Exit:** mọi attempt có kết quả hữu hạn, không orphan/lock leak trong isolated harness, lỗi đúng lớp, không giảm kiểm tra integrity/authority. Mốc thời gian thực đo phải được ghi; nếu cần đổi budget, revise trước khi nghiệm thu thay vì nâng tới khi hết đỏ.

### W4 — Người dùng biết đúng việc cần làm, không bị yêu cầu login sai lớp

1. UI hiển thị riêng: account/session; cấu hình workspace/credential máy; runtime/process; Tunnel/gateway heartbeat; connector freshness/ACK. Unknown giữ unknown, không tô xanh từ persisted hash.
2. Runtime/Tunnel/census lỗi không gọi `clearSession()`. Chỉ clear khi người dùng yêu cầu rõ; giữ partition `persist:chatgpt-session`.
3. Phiên hết hạn/revoked: người dùng đăng nhập tương tác; thiếu local key/tunnel/workspace: chỉ dẫn setup đúng mục. Không bảo đảm provider sẽ không yêu cầu reauth và không tự động hóa login/CAPTCHA.
4. Khi mở app mới đủ setup và đã opt-in, chạy W2. Khi connector chỉ pending, observe receipt hiện có, không restart toàn bộ liên tục. Khi schema thực sự breaking, nêu đúng yêu cầu real discovery.
5. `Codex auth token is unavailable` được chẩn đoán như lỗi lớp Codex/client nếu còn tái hiện. Gắn related issue/subcriterion rõ: fix repo không được tuyên bố đã sửa auth của client ngoài repo. Nếu nó chặn workflow được chấp nhận, Problem chưa đóng; nếu nằm ngoài entry point đã chốt, ghi hạn chế ngoài phạm vi thay vì im lặng xóa.
6. Cập nhật CURRENT_STATE/README/RECOVERY_HOST/RELEASE_CHECKLIST đúng surfaces vừa thay đổi. Hiện `package.json` cho `npm run dist` gọi `test:all`, trái câu cũ trong RELEASE_CHECKLIST nói không chạy Python: sửa guidance theo implementation khi làm gói docs tương ứng, không dùng mô tả cũ để bỏ MCP proof.

**Exit:** mỗi loại lỗi có một next action đúng; không reset cookie do lỗi hạ tầng; hiển thị source/current process/freshness trung thực; test session/layer classification và UI smoke đạt.

### W5 — Tích hợp, acceptance và candidate cố định

1. Tích hợp tuần tự lên base đã chốt, review diff/protected paths, giải quyết mọi overlap với tác vụ khác. Chỉ proof các node bị thay đổi; không gọi lại full suite mỗi WAVE.
2. Chạy focused lanes mục 6, rồi một integrated gate phù hợp vì gói thay đổi Python/Electron/process boundary. Fix test failure thật hoặc xác định blocker; không gọi cả gói PASS khi vẫn đỏ.
3. Ghi proof fingerprint, exact file receipt và controller acceptance qua EOCL. Với sửa có sẵn trước RUN, dùng exact-byte adoption nếu guard hỗ trợ; thiếu receipt thì dừng nhận acceptance, không bù bằng current bytes đơn thuần.
4. Sau khi có quyền local service operation và census không chặn, controlled activation từ exact source. `READY/OPEN` phải khớp epoch/process/server/device/workspace và running/disk revisions; lưu freshness mode thực tế. Exit 0 còn VERIFYING/CLOSED không đạt gate này.
5. Trước delivery có quyền: review source phạm vi + toàn bộ `.coding-tools` theo AGENTS; chạy `npm run stage:coding-tools-delivery`, rồi `npm run check:coding-tools-delivery` trước mỗi commit/push. Không tự làm bước này trong lượt lập kế hoạch vì nó có staging side effect.
6. Candidate build từ exact accepted source/revision, không đóng gói source đang đổi. Ghi artifact hash, version, source identity và các proof không bị invalidated. Nếu runtime evidence đổi thì stage snapshot đúng quy tắc; không để volatility ấy làm source fingerprint đổi.
7. Build và test packaged/installed ở môi trường được phép. `installed-recovery-smoke.js` là isolated install có uninstall cleanup và yêu cầu máy không có per-user installation hiện hữu; không chạy mù trên máy chính. Smoke này không thay thế Windows reboot/logon thật.

**Exit:** exact candidate + technical acceptance + local/process/packaged proof cần thiết; biết rollback về artifact nào. Có thể handoff W6, chưa gọi toàn bộ Problem confirmed.

### W6 — Hai máy, rồi quan sát sử dụng tự nhiên

Chuẩn bị hai phiếu machine binding, không phải hai cấu hình dùng chung credential:

- Máy A: endpoint đang vận hành Coding-VP Live, workspace/installation được xác minh.
- Máy B: endpoint Coding MCP và Tunnel riêng; lấy identity thực tế khi bắt đầu, không tự đặt route/device ID hay dùng dữ liệu A thay B.
- Cài exact candidate theo quyền trên từng máy; setup/login ban đầu do operator hoàn thành. Không tạo tài khoản/khóa mới hoặc thu hồi tài khoản thật chỉ để làm test.
- Mỗi ca kiểm tra có baseline, trigger, observed result, manual-intervention count và artifact/source/process identity. Ca fault phải dùng môi trường/target được phép và không cắt tác vụ người dùng đang chạy.
- Thực hiện ma trận mục 7. Đối với metadata sai/foreign-write, dùng isolated fixtures để chứng minh bị từ chối; không thử ghi sai vào repository thật.
- Sau controlled matrix, quan sát **ít nhất 48 giờ có sử dụng thực tế**, với ít nhất một phiên làm việc tự nhiên hoàn tất trên mỗi máy và xác nhận độc lập của người dùng. Đây là minimum đề xuất để duyệt trước W0, không phải chứng minh tỷ lệ tin cậy dài hạn. Máy không được sử dụng không tính là đã qua window; không tạo task giả để đủ mẫu.
- Giám sát trong các phiên kiểm chứng/triển khai qua cơ chế runtime/Job hiện có. Không tự tạo automation lịch; khi sang phiên khác phải handoff trạng thái và thu lại identity, không hứa controller này đang giám sát liên tục nếu không có cơ chế hoạt động.

**Exit:** tất cả ca bắt buộc thuộc phạm vi đạt, không missing machine/mode; 0 manual source repair/state deletion/extra refresh do lỗi nội bộ trong các ca thành công; độc lập user outcome có thật. Provider outage/revoked credential được phân loại riêng, không giả thành PASS hoặc sửa sample denominator để bỏ thất bại.

### W7 — Đóng đúng Problem Revision

1. Thu lại canonical Problem/RUN/WAVE/checkpoint/proof/epoch và kết quả matrix cuối. Đảm bảo không còn WAVE ACCEPTING, job mơ hồ hoặc blocker bắt buộc của Problem; không ép đóng RUN không liên quan.
2. Nếu đủ technical checkpoint nhưng thiếu outcome: dùng `reconcile_provisional` đúng checkpoint khi server cho phép; giữ `PROVISIONALLY_RESOLVED` hoặc trạng thái hợp lệ server trả. Không tự viết state label vào DB.
3. Chỉ gọi `confirm` khi có explicit user outcome của exact revision và runtime-derived outcome receipt. Không tự truyền receipt/clock/authority giả vào public input, không thay user confirmation bằng lời executor.
4. Nếu cùng lỗi tái diễn, `reopen` exact revision với evidence mới. Nếu mục tiêu thay đổi thật sự, `revise` theo authority và giữ revision cũ. Không tạo Problem mới mỗi lần fail để mất recurrence.
5. Checkpoint cuối nêu đủ: tiêu chí đạt/chưa đạt, số ca và failure/retry, hai máy/mode đã thử, exact source/artifact, Git state, remaining limitations, đã/chưa publish. ACK completion report theo đúng ID nếu contract yêu cầu.

**Exit:** server ghi `RESOLVED_CONFIRMED` đúng quy tắc, kèm biên bản người dùng đọc được. Nếu một điều kiện bắt buộc còn thiếu, kết quả là CHƯA ĐÓNG; không đổi tên “khép kỹ thuật” thành “khép toàn bộ”.

## 6. Các lane kiểm chứng dự kiến

Những lệnh dưới đây là kế hoạch, chưa được chạy bởi việc tạo tài liệu. Chạy từ root trừ lệnh Python được đặt working directory rõ. File test mới chỉ tạo nếu không có fixture hiện hữu phù hợp.

| Phạm vi | Lane hiện có / cách bổ sung |
| --- | --- |
| W1 exact contract/bootstrap | Python `tests/test_efficiency_runtime.py`, `tests/test_activation_epoch.py`, `tests/test_connector_bootstrap_identity.py`, `tests/test_stateless_http_2026.py` trong `resources/coding-tools-mcp` |
| W1/W2 identity boundaries | Node `tests/runtime-lifecycle.test.js`, `tests/connector-binding.test.js`, `tests/recovery-host.test.js`; Python `tests/test_workspace_binding.py`, `tests/test_connector_attestation.py` |
| W2 state/start | Node `tests/runtime-soft-replacement.test.js`, `tests/dev-ui-lifecycle.test.js`, `tests/activation-self-recovery.test.js`, `tests/dev-checkout-authority.test.js` |
| W3 census/deadline | Node `tests/full-clean-activation.test.js`, `tests/recovery-bootstrap.test.js`; Python `tests/test_activation_ledger_census_script.py`, `tests/test_lifecycle_census.py`; thêm targeted discovery/runner tests nếu fixture chưa có |
| W4 UX/session | Node `tests/connector-status-consistency.test.js`, `tests/chat-conversation-access.test.js` và session fixture tương ứng |
| Process boundary W2/W3 | `npm run test:recovery:e2e`; bổ sung isolated host-restart/tunnel-loss/deadline ca còn thiếu |
| Integrated/release candidate | `npm run test:all` hoặc gate tương đương được `npm run dist` thực thi trên exact inputs; không chủ động chạy hai lần liên tiếp nếu command build đã bao gồm cùng proof |
| Packaged recovery | `npm run test:recovery:packaged` theo isolated user-data contract; không đồng nghĩa đã cài Scheduled Task |
| Installed smoke | `node scripts/installed-recovery-smoke.js` chỉ khi đúng điều kiện máy sạch/per-user install và có quyền install/uninstall |
| Live observation | `npm run dev:status` và supported canonical census read; current-process connector call qua client thật |

Full suite/process/packaged lanes chỉ ở integration/candidate hoặc khi thay đổi boundary yêu cầu, không mặc định cho từng edit. Khớp relevant files/toolchain/config mới được reuse proof; Git hash giống nhau nhưng source dirty đã đổi thì không được reuse.

## 7. Ma trận nghiệm thu tối thiểu

Số lần dưới đây là **đề xuất minimum nghiệm thu**, không phải số liệu đã đo hay căn cứ tuyên bố 99,9% reliability. Chốt trước W0. “Lần” nghĩa là một transition có receipt đầy đủ; không tính repeated polling là nhiều mẫu.

| Ca | Trigger / phạm vi | Kết quả phải thấy | Minimum và loại proof |
| --- | --- | --- | --- |
| M01 | CLI dev cold-start: host absent; runtime stopped | Một new epoch, đúng checkout, không can thiệp ngoài lệnh start chuẩn | Mỗi nhánh 1 isolated process case; 3 live CLI cold starts trên máy dev được chọn |
| M02 | Windows reboot + installed direct launch/logon đã opt-in | Đúng profile, retained session khi còn hợp lệ; tự READY rồi dùng được workspace | 3 reboot trên mỗi máy vật lý; gồm Restart và power-on nếu được phép, ghi rõ Fast Startup/boot mode thực tế |
| M03 | Đóng/mở UI khi runtime khỏe | Reuse process, không tạo epoch hoặc reset session vô ích | 3 lần trên mỗi máy |
| M04 | Durable READY, MCP đã mất | Không spawn trong epoch cũ; tạo epoch mới theo valid recovery intent hoặc typed block đúng authority | Unit negative + 1 isolated real-process case; 1 authorized live case mỗi máy |
| M05 | Host-only restart rồi Tunnel loss | Adopt đúng process còn sống; khi không còn attestation key thì guarded full-clean, không retry storm | 1 isolated real-process + 1 authorized live case mỗi máy |
| M06 | Same SHA đã ACK, predecessor rỗng | Current-process handshake vẫn tới final ACK/open; không giả rediscovery | Python→Electron integration; 1 real client case trên candidate/fixture version được phép |
| M07 | Client cache bỏ qua ít nhất hai compatible releases | Chọn đúng reviewed closure, giữ device/workspace; compatible mode được ghi thật | Graph negatives + 1 real cached-client/version transition mỗi máy; không sửa ACK file bằng tay |
| M08 | Contract changed unknown/breaking hoặc máy mới chưa ACK | Chặn tool/admission cho tới real discovery, sau đó có thể hoàn tất | Isolated negatives + 1 real discovery smoke trên mỗi endpoint; không gán hash giả vào live state |
| M09 | Hanging discovery / lock contention / timeout / cleanup race | Hết deadline đúng pha, không orphan/lock leak, retry sau cleanup có bằng chứng | Deterministic cases mục W3 + isolated forced-process case; không làm chậm live ledger |
| M10 | Busy, manualStop, source drift, wrong process/device/workspace | Không tự restart/ghi sai đích, typed reason; khi điều kiện hợp lệ trở lại thì có next action | Mỗi invariant 1 discriminating test; live busy/manualStop chỉ khi có quyền, foreign-write ở fixture |
| M11 | New session/profile hoặc expired/revoked auth; config thiếu | Chỉ yêu cầu login/setup đúng lớp, không clear session do Tunnel/census lỗi | Fixture auth/config negatives + manual first-setup observation; không cố tình revoke credential thật |
| M12 | A offline hoặc đang giữ task; B online qua tunnel riêng | Không tự chuyển tác vụ ghi A sang B; mỗi máy đọc đúng workspace được chọn | 3 A/B selection cycles, tối thiểu 1 A-unavailable case; thao tác ghi sai đích chỉ trong fixture |
| M13 | Activation fail/timeout và quay về candidate trước | Failed evidence còn nguyên; rollback dùng exact artifact và new operation; durable DB không downgrade bừa | 1 isolated process/packaged rollback; live rollback chỉ khi được phép |
| M14 | Người dùng làm việc bình thường sau matrix | Không cần sửa/refresh để vào việc; outcome độc lập trên exact revision | Window W6 và tối thiểu 1 phiên tự nhiên mỗi máy; missing vẫn missing |

Nếu máy B, client cache hoặc quyền reboot chưa có, ghi rõ `NOT_RUN` cho ca tương ứng và giữ gate mở. Không lấy VM/temp directory trên A thay bằng chứng hai máy vật lý. Synthetic tests không được đưa vào số outcome tự nhiên.

## 8. Làm giàu dữ liệu trong cùng quá trình sửa

Tận dụng canonical ledger/receipt/report hiện có. Bảng ca trong tài liệu chỉ là kế hoạch; không trở thành nguồn ghi sự thật cạnh tranh.

Mỗi attempt cần nối được:

1. Problem ID/revision/contract fingerprint; RUN/WAVE; exact source/checkpoint/artifact.
2. Scenario ID, runtime-derived event/operation identity, endpoint/workspace generation, old/new process/server/epoch; không dùng hostname/tài khoản thật nếu opaque ID đủ.
3. Reproduction thực, typed cause và mức chắc chắn (`observed`, suy luận, chưa biết). “30s hết lỗi một lần” không tự trở thành causal performance proof.
4. Durations theo phase và nguồn đồng hồ; kết quả deadline/cleanup/retry, số thao tác sửa tay của operator. Latency chưa đo là unknown, không phải 0.
5. Proof inputs/results, acceptance và user outcome là các loại evidence riêng. Failed/replanned/reopened attempts vẫn được giữ và liên kết, không chỉ thu thành công.

Giữ event identity/idempotency của runtime để reconnect không đếm trùng. Không sửa bản ghi quá khứ hoặc backdate recommendation. Nếu schema hiện có chưa lưu được một trường cần thiết, trước hết dùng generated report/receipt đã hỗ trợ; chỉ thêm typed telemetry tối thiểu khi chứng minh có consumer cụ thể, không xây một nền tảng analytics mới.

Đo phục vụ vận hành: cold-start time, phase latency, recovery attempts, time-to-first-successful-workspace-call, số lần manual repair/refresh, recurrence theo revision và mode. Không suy ra ROI/routing superiority hay provider billing từ các chỉ số này; không tự bật policy/routing/P5 sau ca xanh.

## 9. Rollback và STOP rules

- Lưu trước exact known-good source/artifact và per-machine installation/workspace/epoch identity qua supported receipts. Không coi Git checkout sạch là backup của config/secret store/ledger.
- Nếu candidate lỗi: ngừng rollout máy tiếp theo, giữ evidence, ngừng writer mới; thu census và chọn supported controlled rollback về artifact đã biết theo quyền. Đó là operation mới, không sửa READY/FAILED cũ thành trạng thái mong muốn.
- Kế hoạch không yêu cầu ledger schema migration. Nếu implementation phát sinh migration, phải tách packet compatibility/rollback; không downgrade SQLite bằng copy đè snapshot cũ và làm mất events mới.
- Dừng trước mutation khi foreign/unknown PID owner, unavailable ledger authority, source fingerprint lệch, active job/lease chưa quiescent, thiếu exact attestation/consent, thiếu máy đích hoặc phát hiện secret trong evidence.
- Khi ledger gate busy: không ép xóa lock hoặc bulk-reconcile stale RUN. Khi auth client lỗi: không copy token hoặc đổi machine failover. Khi receipt không đủ: không giả ACK/discovery/acceptance.
- Với deadline/network transient: giữ cùng lineage và operation nếu đúng contract; chỉ retry bounded khi có evidence mới. Sau failure lặp không đổi điều kiện, báo blocker và next action; không tạo vòng refresh vô hạn.

## 10. Dự trù và hành động bắt đầu

Ước lượng lập kế hoạch, chưa phải benchmark hay cam kết: W0–W4 khoảng **3–5 ngày công kỹ thuật**; W5 thêm **1–2 ngày công** tùy process/packaging defects; W6 cần **ít nhất 48 giờ có sử dụng thực tế sau matrix**, phụ thuộc lịch hai máy và quyền thao tác. Không tính thời gian chờ account/network/second machine thành thời gian đã hoàn tất.

Hành động đầu tiên khi được giao triển khai: **W0**, không restart thêm. Xác minh canonical Problem/owner/bytes, chốt bản cài là target sử dụng đa máy, freeze C01–C12, chuẩn bị scope/lease rồi giao W1 và W3; W2 theo interface đã chốt. Worker nội bộ chỉ đưa evidence/candidate; quyền semantic acceptance thuộc controller được runtime xác thực, không phụ thuộc tên model tự khai.

Biên bản kết thúc cuối cùng phải trả lời được một câu bằng bằng chứng: **trên hai máy và các entry point đã cam kết, người dùng đã vào làm việc nhiều lần mà không cần sửa nguồn/state hoặc refresh thủ công do lỗi nội bộ, đồng thời mọi guard sai đích/sai quyền vẫn chặn — và kết quả đó đã được xác nhận độc lập trong exact Problem Revision.**
