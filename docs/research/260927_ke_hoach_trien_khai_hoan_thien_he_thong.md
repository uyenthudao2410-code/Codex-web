# Kế hoạch triển khai hoàn thiện Coding Tools MCP / Electron Execution Hub

> Ngày lập: **27/09/2026** — tên file theo quy ước `yymmdd_noi_dung`.
>
> Trạng thái: **KẾ HOẠCH ĐỂ TRIỂN KHAI; CHƯA THỰC THI CÁC GÓI BÊN DƯỚI**.
>
> Phạm vi mặc định: `E:\DEV\Codex-web`. Ubuntu, ChatGPT, máy B, dịch vụ Windows, package cài đặt và quyền thực thi là những đích riêng, chỉ thao tác khi có phê duyệt tương ứng.

## 0. Đọc trước khi triển khai

### 0.1. Kết luận và đường đi ngắn nhất

Hệ thống đã có nhiều implementation và focused proof, nhưng chưa hoàn tất vận hành đầu-cuối. Snapshot cuối của lượt rà soát trước khi lập kế hoạch cho thấy central connection/authority và heartbeat đã hoạt động; Desktop UI chưa chạy, Coding Tools MCP dừng và full-clean activation thiếu accepted source checkpoint.

Đường đi ưu tiên:

```text
H0 Chốt phạm vi, owner, baseline và nguồn bằng chứng
  -> H1 Hoàn thiện đúng các source packet đang dở + focused proof
  -> H2 Có đường nghiệm thu hợp lệ + exact accepted checkpoint
  -> H3 Kích hoạt local executor bằng authority được hỗ trợ
  -> H4 Đồng bộ Ubuntu / facade / policy / client schema
  -> H5 ChatGPT thật: inventory -> task -> read -> receipt -> close
  -> H6 Patch có giới hạn; exec chỉ mở sau sandbox/package gate riêng
  -> H7 Recovery matrix + H8 Goal continuation trên công việc thật
  -> H9 Đóng Problem bằng criterion coverage và outcome độc lập
  -> H10 Package/upgrade/rollback/release theo đúng quyền
```

H7 và H8 chỉ chạy song song khi khác owner, không cùng viết workspace, không dùng fault injection làm nhiễu mẫu công việc tự nhiên. Có thể chuẩn bị source/test, package candidate và hồ sơ rollout Ubuntu trước; không được bỏ qua các gate trước khi cho hiệu ứng thật xảy ra.

Hai điểm hội tụ cần tránh hiểu thành vòng phụ thuộc: nếu activation H3 đang chờ discovery hợp lệ thì làm phần client-schema/discovery H4 và quay lại postflight của **cùng operation**, không khởi động lại lần nữa; candidate/package proof cần cho exec H6 được chuẩn bị trước từ quy trình H10, còn phát hành cuối vẫn chờ các gate thuộc phạm vi release.

**Việc đầu tiên cần giao:** H0 và H1, sau đó H2. Không bắt đầu bằng `npm start`, reinstall, mở exec, đổi tài khoản hay deploy Ubuntu để thử vận may.

### 0.2. Ba mức hoàn thành phải báo riêng

| Mức | Điều kiện hoàn thành | Không được dùng thay thế |
| --- | --- | --- |
| M1 — Khả dụng kỹ thuật | Đúng nguồn đã nghiệm thu; runtime đúng identity; target đúng; thao tác được phép hoàn thành từ client thật; negative/stop/replay liên quan đạt | Test source, heartbeat hoặc inventory đơn lẻ |
| M2 — Hiệu quả trên công việc thật | Một Problem tự nhiên có oracle, đầy đủ lineage, đủ tiêu chí và outcome độc lập; tiếp tục thêm mẫu nếu muốn kết luận ổn định/hiệu quả | Synthetic canary, số RUN accepted, lời model tự báo xong |
| M3 — Sẵn sàng phát hành | Exact package, installer/upgrade/rollback, installed-session/recovery, required CI và tài liệu phù hợp; quyền publish riêng | Unpacked unsigned candidate, smoke cô lập, phiên bản ghi trong package.json |

M1 có thể được nghiệm thu cho phạm vi **read-only** trước, sau đó read/patch. Nếu exec còn tắt thì phải ghi rõ phạm vi chưa bao gồm exec; không đánh dấu hoàn thiện toàn sản phẩm khi một tiêu chí bắt buộc vẫn thiếu.

### 0.3. Quyền hiện có của lần lập tài liệu

Lần lập file này chỉ được phép tạo kế hoạch. Không có gói H0–H10 nào được coi là đã được cấp quyền triển khai chỉ vì xuất hiện trong tài liệu.

- Không commit, push, tag, release, deploy, restart, reboot, install hoặc đổi policy trong lượt lập kế hoạch.
- Không tự mở quyền ghi/exec, cấp grant, đổi OAuth, tạo tunnel, đăng nhập Tailscale hoặc dùng tài khoản khác.
- Không chỉnh ledger/receipt/activation file để tạo một trạng thái xanh.
- Không xóa các file concurrent, browser profile cũ, package cũ hay `.coding-tools`.
- Các lệnh dưới đây là **runbook có điều kiện**, không phải script chạy liên tục từ đầu tới cuối.

## 1. Baseline có thời điểm và giới hạn bằng chứng

### 1.1. Nguồn/Git tại lúc bắt đầu lập kế hoạch

- Root đã kiểm tra: `E:\DEV\Codex-web`.
- Branch: `main`.
- HEAD: `5cebc8a98f852eebaadfd3ecb36c3c7abde0e1bb`.
- Lượt rà soát trước ghi `0 behind / 14 ahead` so với `origin/main` lưu cục bộ; chưa fetch, không phải xác nhận GitHub hiện tại.
- Khi bắt đầu lập kế hoạch: 27 tracked paths thay đổi, 6 untracked paths. Bản kế hoạch này sẽ thêm một untracked path; không trộn nó vào baseline cũ.
- Dirty source gồm Control Plane facade/agent/store/UI, renderer, Recovery Supervisor, tests, docs; `.coding-tools` có runtime drift.
- Năm file root `app.js`, `main.js`, `browser.html`, `browser.js`, `browserPreload.js` xuất hiện trong lượt rà soát trước; chưa xác định owner/mục đích. File `control-plane/tests/test_connected_agent_status.py` cũng chưa tracked.

HEAD không đại diện đủ cho dirty source. Không chọn package hoặc reuse proof chỉ bằng SHA HEAD.

### 1.2. Runtime snapshot từ lượt rà soát trước

**Cửa sổ:** 27/09/2026, 14:34–14:35 +07. Đây là bằng chứng có thời điểm, không được tái sử dụng như trạng thái live khi triển khai sau này.

| Thành phần | Đã quan sát | Giới hạn kết luận |
| --- | --- | --- |
| Tailscale | `Running`, `SelfOnline=true`, 2 peer online | Không chứng minh route/ACL/HTTP/tool invocation cụ thể |
| Supervisor / agent | Supervisor healthy; agent PID 33100; telemetry fresh, heartbeat succeeded | Heartbeat thành công không chứng minh local executor chạy được |
| Recovery Host | PID 34064, source-current, running/disk revision khớp, full-clean capability có | Không tự tạo source acceptance |
| Central | `central_connected=true`, `authority_ready=true` | Chưa thay cho local readiness hoặc read receipt |
| Desktop / MCP | UI `MISSING`, MCP `stopped`, `fully_ready=false`, `LOCAL_EXECUTOR_NOT_READY` | M1 chưa đạt |
| Activation | Epoch được báo `READY` nhưng `admission_open=false`; preflight `ACTIVATION_SOURCE_CHECKPOINT_REQUIRED` | Không coi chữ READY riêng lẻ là admission mở |
| Accepted-code profile | `active_checkpoint_id=null`, không có `closure_input` | Chưa có closure để dùng cho full-clean |
| Local connector | `UNAVAILABLE`, `connector_rediscovered=false` | Không suy rằng plugin Ubuntu hỏng; cần kiểm tuyến central đúng role |

Lúc 14:28 có status timeout, sau đó descriptor cũ stale; tới snapshot cuối đã có host mới và status thành công. Lượt rà soát không yêu cầu restart. Nguyên nhân đầy đủ của chuyển tiếp chưa được xác lập; giữ sự kiện này làm case điều tra, không tuyên bố lỗi còn kéo dài hoặc recovery đã đạt toàn bộ.

### 1.3. Canonical evidence đã đọc

Snapshot census ngày 27/09/2026 lúc `07:28:23.956Z`, lấy bằng SQLite Backup API:

- Schema ledger 12, integrity `ok`, foreign-key violations 0.
- `mutated_canonical_ledger=false`, không instantiate canonical writer/runtime.
- 17 ordinary active RUNs, đều thuộc `THRESHOLD_SENSITIVE_STALE_CANDIDATE`.
- 6 P5 experiment anchors; không coi là 6 workload đang chạy.
- Không projection drift, không unbound live-resource residue, không unexplained active RUN.
- Snapshot SHA-256: `6147d3ec6fafd55c5db286bb17b1d0c791de730745788da9b5cc05ef4ff6dec2`.
- Logical SHA-256: `20eb47783cf7cde51e39552a5d03dc2b0119d572d7f0dc7846e2fb37d92ab089`.

Các hash trên định danh observation cũ, **không phải precondition cho mutation tương lai**. Snapshot tạm của reporter không phải một backup giao hàng được lưu lâu dài.

Query-only read lúc `07:30:18Z` xác nhận:

| Problem | Revision | Tiêu chí | Trạng thái | Outcome receipt |
| --- | --- | ---: | --- | --- |
| `prl-22e670302757c9b7663170e226ed7c26` | 1 | 12, C01–C12 | OPEN | Chưa có |
| `prl-e918c7d33e70c2d304d0797e11b05fcb` | 2 | 18, 4 continuity/telemetry + BG01–BG14 | OPEN | Chưa có |

`goal_continuations=0`, `goal_continuation_observations=0` trong ledger đã đọc. Không suy rằng source không tồn tại; cũng không suy đã có autonomous natural outcome từ một run-continuation canary.

### 1.4. Những bằng chứng cũ cần giữ nhưng không nâng cấp thành current PASS

- 23/09: HTTP handler shutdown/drain có báo cáo 1.162 MCP tests pass, 5 skip.
- 25/09: W1 bỏ embedded ChatGPT source; candidate `policy-w1-c-20260925` có isolated packaged smoke, unsigned/dev-only.
- 25/09: Node 1.019 pass; Python 1.183 pass, 5 skip, 4 fail trong integrated lane. Lỗi sandbox `cmd.exe` và lỗi Windows teardown chưa được coi là pass.
- 25/09: backend Ubuntu MCP loopback → Windows Recovery IPC đọc được 56 byte; không phải ChatGPT-originated E2E.
- 25/09: 13 unresolved actions trong remote snapshot; không lấy con số này làm count hiện tại nếu chưa đọc lại Ubuntu.
- 26–27/09: có 122 MCP tests pass dưới WSL, 32 UI tests pass, 17 Supervisor tests pass trong các checkpoint. Chưa rerun ở lần lập file này.
- Personal ChatGPT connection từng gọi inventory/task_list; chưa có current real-client task/read/patch/exec acceptance cho toàn bộ nguồn mới.

## 2. Nguyên tắc triển khai và phân quyền

### 2.1. Owner

| Vai trò | Trách nhiệm | Không được tự làm |
| --- | --- | --- |
| Controller / người tích hợp | Scope, contract, write ownership, review, chốt từng gate | Tự nhận quyền triển khai/mutation từ kết quả worker |
| Source owner Windows | Renderer, Recovery Host/Supervisor, bridges, tests Windows | Đổi Ubuntu grant hoặc policy ngoài packet |
| Source owner Control Plane | Facade/schema/agent/store, tests và package nguồn | Deploy/restart remote khi chưa được giao |
| Operator Windows | Supported activation/install, policy, sandbox, maintenance window | Sửa ledger/descriptor bằng tay hoặc kill PID không xác minh |
| Operator Ubuntu | Backup/rollout/health/reconciliation/renewal theo runbook | Restore DB cũ rồi replay effect unknown |
| Người nghiệm thu độc lập | Oracle, criterion coverage, kết quả người dùng | Coi worker tự nói hoàn thành là outcome |

Một người có thể giữ nhiều vai trò, nhưng từng action vẫn cần phạm vi và quyền tương ứng. Mỗi exact file chỉ có một writer; một runtime lifecycle owner tại một thời điểm.

### 2.2. Những quyền cần chốt trước từng loại thao tác

| Hành động | Cần chốt |
| --- | --- |
| Sửa source | Exact paths, owner, invariants, focused oracle |
| Commit local | Phạm vi source/docs + toàn bộ `.coding-tools` theo retention; không suy ra push |
| Windows activation/install/restart | Đúng installation/profile, checkpoint, thời gian bảo trì, job/lease state, rollback owner |
| Ubuntu rollout | Host/user/service/release/DB đích, backup, grant/admission policy, phương án rollback |
| ChatGPT task/read | Connection và binding đúng; file/range/bytes được phép; cho phép tạo/đóng task nếu cần |
| Patch | Exact existing file, before-hash, diff/size, write policy và verifier |
| Exec / fault / reboot / máy B | Package/sandbox/argv/cwd/budget, thời gian bảo trì, máy và phạm vi lỗi cho phép |
| Publish/tag/release | Repository/tag/version/kênh/artifact/destination cụ thể, riêng với quyền commit |

Không ghi secret values vào packet. Chỉ dùng secret handle/owner-protected file qua giao diện có sẵn. Không sao chép bearer token từ profile vào chat hoặc curl thủ công.

### 2.3. Retention và state machine

- Giữ mọi `.coding-tools/**`, trừ đúng hai SQLite sidecar `.coding-tools/orchestration/ledger.sqlite3-shm` và `ledger.sqlite3-wal` được ignore theo AGENTS.
- Runtime evidence không được tham gia source fingerprint để tạo drift giả; actual source/config/contract drift phải invalidate proof liên quan.
- Khi runtime EOCL áp dụng, đi qua RUN/WAVE và exact write lease; `ACCEPTING` chưa phải `CHECKPOINTED`.
- REPLAN phải có thay đổi về evidence/scope/strategy, không retry cùng lỗi và cùng giả định.
- Unknown effect phải reconcile, không retry mutation để tìm câu trả lời.
- Rollback giữ lịch sử và trạng thái off/manual-stop trước đó; không khởi động mọi dịch vụ vô điều kiện.
- Giữ `execution_route=auto` deterministic; automatic handoff, promotion và P5 treatment không tự mở bởi kế hoạch này.

## 3. Bảng gói công việc và đường phụ thuộc

Các mã H0–H10 là mã công việc của tài liệu này, không thay thế ID RUN/WAVE hoặc đổi tên W0–W6 trong policy plan cũ.

| Gói | Phụ thuộc | Owner chính | Đầu ra bắt buộc | Gate |
| --- | --- | --- | --- | --- |
| H0 Baseline/ownership | Không | Controller | Inventory có timestamp; source owner; target/authority; evidence-gap list | G0 |
| H1 Source/proof | H0 | Source owners | Diff nhỏ đã review; focused proof đúng fingerprint | G1 |
| H2 Acceptance/bootstrap | H1 | Controller + Windows owner | Accepted checkpoint hợp lệ hoặc blocker/path bootstrap được xác minh | G2 |
| H3 Local activation | G2 + quyền dịch vụ | Windows operator | UI/MCP/current identity/admission/readiness đúng intent | G3 |
| H4 Central rollout | G1 + quyền rollout; discovery hội tụ với H3 | Ubuntu + Windows operators | Exact package/facade/policy/client contract phù hợp | G4 |
| H5 Real read workflow | G3 + G4 | Client operator + reviewer | Completed target-bound read receipt từ ChatGPT thật | G5-R |
| H6 Patch / exec riêng | G5-R; exec thêm sandbox/package | Operators + reviewer | Patch receipt; exec PASS hoặc OFF/NOT_RUN rõ ràng | G6-W / G6-X |
| H7 Recovery matrix | G3/G4; isolated fault trước natural | Windows/Ubuntu test owners | C01–C12 evidence hoặc per-criterion gap | G7 |
| H8 Goal continuation | G5-R + đủ quyền của task | Continuation/controller owner | BG/continuity proof + natural goal outcome | G8 |
| H9 Problem closure | G7/G8 theo Problem | Controller + user/outcome owner | Canonical coverage/outcome/transition đúng revision | G9 |
| H10 Release | Source freeze + các gate thuộc phạm vi release | Release owner | Exact installed artifact, rollback, tài liệu, bàn giao | G10 |

Không ước lượng ngày hoàn tất cố định khi còn thiếu authority, client thật hoặc công việc tự nhiên. Ước lượng sau H0; thời gian chờ người dùng/host/provider tách khỏi thời gian engineering.

## 4. H0 — Chốt nguồn, target, owner và evidence trước mutation

**Mục tiêu:** không làm sai checkout, không ghi đè concurrent work, không tiếp tục bằng receipt cũ.

1. Đọc root/deeper AGENTS; kiểm tra root, branch, HEAD, status, diff có liên quan, recent history.
2. Phân loại dirty paths: runtime evidence; source đã có proof; source chưa đủ proof; docs; untracked chưa rõ owner. Hỏi owner chỉ với overlap không thể tự xác định.
3. Với năm file mới ở root, đối chiếu nguồn tạo và mục đích trước khi chọn vào packet; không tự xóa, di chuyển hoặc đưa vào package.
4. Chụp read-only runtime theo nhóm tuần tự để tránh gây nhiễu: Supervisor → dev status → full-clean status/preflight. Nếu PID/instance đổi, đóng observation cũ rồi tạo observation mới.
5. Chụp lifecycle census bằng reporter hỗ trợ; đọc hai Problem/current revision và đối chiếu latest accepted references bằng API/report hoặc query-only snapshot.
6. Đối soát các report/checkpoint thiếu trong canonical history được nêu ở kế hoạch 22/09. Giữ danh sách ID/hashes; không nhập lại row thủ công.
7. Chốt intended role `central_executor`, workspace/binding/generation, server/tunnel đích. Windows direct tunnel và Ubuntu Secure MCP Tunnel là hai tuyến khác nhau.
8. Ghi quyền còn thiếu: source writer, acceptance surface, Windows lifecycle, Ubuntu rollout, read/patch/exec, reboot/máy B, release.

**Lệnh chẩn đoán tham chiếu — PowerShell, chỉ đọc trạng thái:**

```powershell
Set-Location -LiteralPath 'E:\DEV\Codex-web'
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git status --short
git log -8 --date=iso-strict --pretty=format:'%h %ad %s'
git diff --stat
git ls-files --unmerged
npm run recovery:supervisor:status
npm run dev:status
node scripts/full-clean-activation.js --status
node scripts/full-clean-activation.js --preflight
python -B resources/coding-tools-mcp/scripts/report_lifecycle_census.py --workspace 'E:\DEV\Codex-web' --summary
```

`--preflight` thất bại vì thiếu checkpoint là một kết quả chẩn đoán, không cho phép chạy `--execute`. Reporter census tạo bản sao tạm để đọc và tự dọn bản sao đó; không sửa ledger canonical.

**Exit G0:** xác định đúng scope/owner; không conflict chưa giải quyết; đủ baseline có timestamp; mọi observation lịch sử được gắn nhãn; có next action cụ thể cho từng blocker. Git không bắt buộc sạch để điều tra, nhưng source dùng để build/accept phải được chốt đủ identity.

**Dừng:** thấy secret trong bằng chứng; wrong target; writer khác đang sửa exact packet; cần restore/history rewrite; không biết ai sở hữu một thay đổi có thể bị ghi đè.

## 5. H1 — Hoàn thiện source packet đang dở, không mở rộng kiến trúc

### 5.1. Chia packet nhỏ và owner không trùng file

| Packet | Phạm vi ứng viên đã tồn tại | Cần kiểm chứng trước khi thêm code |
| --- | --- | --- |
| S-CP | `control-plane/control_plane/mcp_facade.py`, `node_agent.py`, `store.py`, `web_ui.py`; tests tương ứng | Schema từng operation khớp parser; identity/grant/policy không nới; telemetry heartbeat không lẫn poll failure |
| S-REC | `resources/recovery-supervisor/recovery-supervisor.ps1`; tests Supervisor/activation | Manifest/PID/start identity/telemetry; replacement không giữ agent không có provenance; lock cleanup exact owner; manual-stop/idle preserved |
| S-UI | `renderer/app.js`, `index.html`, `settings-compact.css`; tests Settings/manager/setup | Online, capability, dispatch, readiness, policy freshness tách biệt; lỗi executor không hướng dẫn pair lại; unknown không thành ready |
| S-DOC | Maintained docs, README và version guidance | Không yêu cầu sai Organization/Workspace IDs để chọn local project; không nhầm account eligibility với tool readiness; checklist version phù hợp |

Source paths chỉ là ứng viên. Khi contract/ownership hiện tại khác, controller thu hẹp/chuyển packet bằng bằng chứng; không giao write overlap.

Riêng `control-plane/tests/test_connected_agent_status.py` đang untracked ở baseline: phải xác nhận owner/nội dung và đưa vào exact source/proof manifest được review trước khi dùng làm G1/G4/release evidence. Nếu chạy trước bước đó thì chỉ ghi exploratory; không tự stage/package hoặc dùng kết quả để nghiệm thu nguồn chưa được chốt.

### 5.2. Các điều kiện kiểm thử bắt buộc

1. Facade: valid operation payload được nhận; missing required/extra field bị từ chối trước khi tạo task/action; legacy schema không trả null; profile/schema/hash phân biệt rõ với SQLite schema.
2. Agent: heartbeat succeeded nhưng poll sau đó fail phải phản ánh hai sự kiện riêng; lỗi chỉ ghi sanitized code; telemetry-write error không được làm giả heartbeat hay dừng agent không cần thiết.
3. Supervisor: stale/unrecorded PID không đủ điều kiện retain; PID reuse/wrong script/wrong manifest/stale telemetry phải fail-closed; cleanup lock chỉ với exact stopped owner; không kill foreign process.
4. UI: capability true + offline/degraded/expired policy không thành readiness true; hiển thị một next action đúng lớp; kiểm tra trạng thái sau mở lại UI.
5. W1: không khôi phục embedded ChatGPT observer/hooks/download/session IPC; external browser handoff do người dùng chủ động; profile cũ không bị tự xóa.
6. Credential/network: giữ fail-fast với credential rejection, bounded retry, environment allowlist, bảo vệ grant file và secret output. Không đổi account/tunnel để bypass rejection.

Chỉ sửa lỗi tái hiện hoặc contract gap đã chứng minh. Các bài kiểm tra có sẵn là điểm bắt đầu; thêm regression phân biệt được đúng lỗi, không chỉ tăng tổng test.

**Exit G1:** từng packet có before/after diff, source/config fingerprint, focused check thực tế, fail/skip phân loại và reviewer. Nếu thay đổi sau proof, chỉ proof bị ảnh hưởng phải chạy lại. Historical 122/32/17 không tự trở thành proof của dirty source mới.

**Rollback source:** qua patch có review trên đúng phần do packet sở hữu; không `reset --hard`, `checkout --`, clean hoặc revert concurrent work.

## 6. H2 — Giải quyết acceptance/activation đúng authority, tránh vòng lặp

### 6.1. Vấn đề cần giải

Không thể đơn giản bảo “gọi task_control để accept” nếu MCP/connector cung cấp action đó đang dừng hoặc phiên hiện tại không expose nó. Phải xác định **một đường điều khiển được hỗ trợ thực sự callable**, hoặc kết luận thiếu đường bootstrap và giao đúng owner xử lý.

### 6.2. Cây quyết định

| Điều kiện mới kiểm tra | Hành động hợp lệ | Không được làm |
| --- | --- | --- |
| Có `task_control` đúng runtime/workspace và source proof hiện hành | Review RUN/WAVE/proof/receipts, accept/checkpoint qua action được hỗ trợ | Accept một run khác hoặc coi tool cùng tên ở facade khác là EOCL |
| Có checkpoint đã accepted và match toàn bộ identity/fingerprint hiện tại | Đọc lại qua authority hỗ trợ, kiểm receipt/provenance, dùng closure do hệ thống xuất | Copy một ID từ Markdown rồi tự ráp proof |
| Recovery Host mixed-version/stale, có source receipt hợp lệ cho trusted bootstrap | Đọc preflight trusted bootstrap; nếu đủ điều kiện, xin quyền cho đúng bootstrap | Dùng bootstrap như cách bỏ qua source acceptance hoặc mở workspace admission |
| Host đã source-current nhưng MCP dừng, không có acceptance surface/eligible receipt | Ghi blocker; owner khôi phục/mở supported control surface hoặc xử lý một bootstrap defect bằng packet có oracle | Chạy stdio/runtime phụ, sửa DB/activation/descriptor hay tự chế raw RPC để tạo quyền |
| Source/worktree đã đổi sau acceptance | Thu lại proof bị ảnh hưởng, tạo wave/acceptance đúng contract | Gắn receipt cũ vào source mới |

### 6.3. Trusted Recovery Bootstrap là nhánh có điều kiện

Source hiện có [trusted-recovery-bootstrap.js](../../scripts/trusted-recovery-bootstrap.js). Lệnh có `--preflight` chỉ đánh giá; lệnh **không có `--preflight` là mutation**, không được dùng thử.

```powershell
# Chỉ khi H2 xác định cần đánh giá nhánh trusted bootstrap.
node scripts/trusted-recovery-bootstrap.js --preflight
```

CLI này không nhận checkpoint/path/PID do caller chọn; nó chọn nguồn recovery_host có receipt rồi kiểm deferred handoff owner. Không cam kết nó sẽ pass với ledger hiện tại. Nếu không có eligible receipt, giữ fail-closed và báo đúng mã; không tạo attestation giả. PASS của preflight cũng không phải natural outcome hoặc full product source acceptance.

Selector hiện yêu cầu accepted checkpoint đúng HEAD, `eligible=true`, `code=ACTIVATABLE`, `affected_components` chỉ gồm `recovery_host`, và receipt còn khớp file bytes/SHA. Supervisor handoff phải có capability, PID sống và heartbeat đủ mới theo verifier. Đây là nhánh mixed-version recovery hẹp, không phải lối restart chung khi mọi checkpoint khác thiếu.

Lệnh mutation còn cần descriptor Recovery Host hợp lệ và đúng installation khi tạo deferred request. Vì thế trusted preflight PASS chưa bảo đảm mutation sẽ được nhận nếu host/descriptor vừa mất. Phân loại ba blocker khác nhau: thiếu accepted source authority; thiếu Supervisor handoff; thiếu Recovery Host identity. Với baseline host đã current nhưng không có eligible receipt, không dùng nhánh này để bypass H2.

### 6.4. Đầu ra G2

Closure hợp lệ phải có đủ năm trường lấy từ **kết quả chính thức**, không tự điền:

```text
checkpoint_id
run_id
wave_id
proof_fingerprint
git_head
```

Gắn kèm source/worktree/config identity mà verifier hiện hành thực sự kiểm, accepted file receipts và owner review. Nếu có delivery commit sau acceptance, đọc lại luật binding và xác nhận/rebind qua authority hỗ trợ; không sửa `git_head` trong closure bằng tay.

Phải kiểm closure chính thức xác nhận source accepted, receipts complete, activation eligible/ACTIVATABLE, affected components hợp lệ, accepted HEAD phù hợp và lifecycle clean theo contract. Chỉ sự có mặt của năm chuỗi ID chưa đủ.

**Exit G2:** có checkpoint đúng nguồn và có đường vận hành để full-clean preflight kiểm nó; hoặc kết thúc gói ở blocker cụ thể gồm tên missing surface/receipt, owner, exact next action. BLOCKED của H2 không cho H3 tự chạy.

## 7. H3 — Kích hoạt Windows local theo checkpoint đã nghiệm thu

**Entry:** G2 đạt; có quyền lifecycle, maintenance window, rollback owner; không có live writer/job/lease xung đột; đúng development/packaged installation.

1. Chụp lại PID/start token/instance/profile/workspace, source revisions, manual-stop/off intent, pending operations, jobs và leases.
2. Operator lấy closure chính thức vào `FULL_CLEAN_SOURCE_CHECKPOINT_JSON` theo [Recovery Host runbook](../RECOVERY_HOST.md). Không lưu raw authority/secrets vào repository; không dùng một JSON ví dụ làm checkpoint thật.
3. Chạy `--status`, rồi `--preflight`. Kiểm exact target/checkpoint/busy/source/authority; bất kỳ refusal nào đều cần phân loại trước bước tiếp.
4. Chỉ khi preflight pass và vẫn còn quyền, gọi đúng supported `--execute`. Deferred acknowledgment chỉ là “đã xếp yêu cầu”, chưa phải activation completed.
5. Theo dõi operation/epoch qua giao diện hỗ trợ đến terminal hoặc NEEDS_DISCOVERY/typed blocker; không spawn một activation thứ hai vì CLI đầu đã trả.
6. Xác minh đúng successor process/instance/revisions, UI registration, MCP running, readiness/admission và role `central_executor`.
7. Kiểm heartbeat/policy observations mới; UI hiển thị đúng; không mất session, không xóa evidence, không mở exec ngoài ý định.

**Lệnh lifecycle — chỉ thực hiện sau quyền và G2:**

```powershell
node scripts/full-clean-activation.js --preflight
# Dừng tại đây nếu preflight không pass hoặc quyền bảo trì chưa có.
node scripts/full-clean-activation.js --execute
```

Đây không phải block để paste chạy cả hai lệnh mù. Phải có checkpoint/approval được kiểm ở giữa.

**Exit G3:** UI và MCP hoạt động đúng nguồn; `LOCAL_EXECUTOR_NOT_READY` đã được giải quyết bằng bằng chứng; role/route/authority đúng; operation kết thúc hợp lệ; không còn job mồ côi. G3 chưa tự đóng strict discovery hoặc ChatGPT read E2E.

Nếu verifier của activation yêu cầu discovery trước khi terminal/admission open, ghi rõ `LOCAL_PROCESS_READY / WAITING_FOR_CLIENT_DISCOVERY` là trạng thái trung gian, **chưa G3 PASS**. Chuyển sang phần client-schema/discovery H4, rồi đọc postflight cùng operation/epoch. Không bắt H4 đợi G3 PASS trong tình huống đó; chỉ cấm H5/H6 dispatch khi cả hai chưa hội tụ. Hết deadline thì giữ typed failure và REPLAN, không kéo dài/tạo operation mới để che timeout.

**Nếu fail:** giữ admission closed khi cần; ghi operation/epoch và nguyên nhân; không kill/reinstall tự phát, không ACK connector thay client. Rollback chỉ theo owner hỗ trợ, giữ trạng thái off trước đó nếu baseline là off và giữ toàn bộ ledger/receipt.

## 8. H4 — Đồng bộ Ubuntu, local policy và schema mà client thật sử dụng

**Entry:** G1 có source được chốt; quyền Ubuntu đúng host/user/service. Có thể chuẩn bị package/so sánh read-only song song H2/H3; live admission/canary chỉ sau local ready.

Artifact chuẩn bị trước source acceptance H2 phải mang nhãn `PREPARATION_ONLY / NOT_ACCEPTED`, có exact source/config/dirty fingerprint và provenance. Không dùng nó làm activation/canary/release acceptance. Sau H2, đối chiếu/rebind bằng authority hỗ trợ tới accepted source đúng fingerprint; chỉ rebuild phần bị invalidated nếu inputs thay đổi, không rerun build/proof y hệt khi đã khớp.

Rollout schema phía Ubuntu và client rediscovery có thể thực hiện trong cửa sổ được duyệt khi H3 đang chờ discovery; đây không phải quyền dispatch read/write/exec lên node chưa ready. Sau khi hai phía khớp, quay lại postflight H3 trước H5.

### 8.1. Chuẩn bị và rollout

1. Đọc lại package đang chạy, health/admission, SQLite schema/integrity, source declaration/package fingerprint; không lấy `7dec4b6e` của ngày 25/09 làm current.
2. Kiểm auth mode hiện hành: private service grant hay OAuth. Service principal không phải danh tính riêng từng người ChatGPT; không tuyên bố per-user audit nếu hệ thống không có bằng chứng đó.
3. Đọc unresolved actions và quarantine dispositions hiện tại. Đối chiếu local effects/handles/receipts trước reconciliation; không xóa row hay gọi lại action unknown.
4. Backup DB qua maintenance command được hỗ trợ; inspect/hash/integrity; lưu backup ngoài repository theo runbook, chỉ đưa receipt đã khử nhạy cảm vào evidence được phép.
5. Build release từ source sạch theo quy định builder; kiểm package manifest và verify release. Chốt migration/mixed-version/rollback compatibility trước khi switch.
6. Deploy theo service/runbook hiện hành, trong cửa sổ được phép; không gộp đổi auth, tunnel, domain, grant và package nếu không cần.
7. Readback health/admission/revision/package hash/schema/permissions. Health HTTP 200 không thay admission hoặc tool receipt.
8. Chỉ cấp/gia hạn policy đã duyệt, đúng binding/generation/capability, với expiry có quan sát mới. Kiểm timer renewal, kết quả oneshot và expiry; scheduled/enabled không tự chứng minh renewal succeeded.
9. Kiểm node agent báo đúng runtime/server/epoch/tool contract; không dùng `policy_state=enabled` từ heartbeat quá hạn.

Các entry point để operator chuẩn bị trên **host sở hữu DB**, từ đúng package/checkout đã chọn:

```bash
# Template: thay mọi <...> bằng target vừa xác minh; không paste chạy nguyên khối.
# PYTHONPATH chỉ áp dụng cho từng command này, không sửa môi trường service production.
PYTHONPATH="$PWD/control-plane" python3 -B -m control_plane.maintenance package-fingerprint
PYTHONPATH="$PWD/control-plane" python3 -B -m control_plane.maintenance snapshot --source '<existing-control-plane.sqlite3>' --destination '<new-snapshot.sqlite3>'
PYTHONPATH="$PWD/control-plane" python3 -B -m control_plane.maintenance inspect-snapshot --source '<completed-snapshot.sqlite3>' --expected-sha256 '<hash-from-snapshot-receipt>'

# GET-only sau rollout được phép; expected admission phải là trạng thái đã readback.
PYTHONPATH="$PWD/control-plane" python3 -B -m control_plane.deployment_verifier --health-url 'https://<private-endpoint>/healthz' --expected-package-source-sha256 '<selected-package-sha256>' --expected-admission recovery
```

Snapshot tạo file backup mới, không phải hoàn toàn không ghi filesystem; nó không thay DB nguồn hoặc mở admission. Không copy live SQLite bằng filesystem command và không xóa WAL/SHM. Verifier chỉ xác nhận những trường nó kiểm; không thay proof systemd owner/configuration/TLS hoặc Windows effect. Không ghi lệnh `systemctl` với unit đoán trước vào kế hoạch; operator dùng đúng unit/path đã xác minh và runbook của release.

### 8.2. Schema và client

1. Phân biệt product version, DB user_version, facade profile/version và contract hash.
2. Lấy tool schema thực tế từ **đúng client connection/tuyến central** sau rollout; refresh/rediscover bằng chức năng được hỗ trợ.
3. Đối chiếu operation union, required/allowed fields với parser; dùng valid/invalid examples trong test làm oracle, không gửi negative mutation lên production tùy tiện.
4. Không đòi Organization ID/ChatGPT Workspace ID như tham số chọn thư mục Windows. Quản trị Platform/tunnel là phạm vi riêng, không tự sửa trong rollout này.
5. Không tạo plugin/tunnel/grant mới nếu connection hiện hành có thể được sửa/refresh đúng hợp đồng.
6. Chỉ bật capability cần cho gate kế tiếp. Read có thể đi trước; standing-write chỉ khi chuẩn bị canary patch được duyệt; exec vẫn off. “Allow all tools” ở client không thay server grant, binding, local policy hoặc acceptance.

**Exit G4:** exact package/route/binding/policy/client schema tương thích; có readback mới và negative authority proof phù hợp; quyền chưa được bật vẫn tắt. Không yêu cầu direct Windows tunnel discovery thay cho central-route proof, cũng không dùng backend loopback discovery thay cho ChatGPT-originated discovery.

**Rollback:** nếu code rollback tương thích schema thì switch qua operator path đã duyệt. Nếu không tương thích, vào recovery/admission-closed và làm restore drill/reconciliation theo [Control Plane Recovery Runbook](../CONTROL_PLANE_RECOVERY_RUNBOOK.md). Restore central DB không đảo các hiệu ứng đã xảy ra trên Windows; cấm replay unknown chỉ vì row cũ không còn.

## 9. H5 — Nghiệm thu luồng đọc thật từ ChatGPT

**Entry:** G3/G4 đạt; connection, binding/generation và local policy mới; owner cho phép tạo task, đọc đúng file/range và đóng task. Mặc định chọn nội dung công khai/không nhạy cảm trong repository; không đọc `.env`, credential, raw browser data hoặc dữ liệu khách hàng.

| Bước | Thực hiện | Bằng chứng phải giữ |
| --- | --- | --- |
| R1 | Client thật gọi inventory | Connection/route đúng; node online; readiness ready; policy timestamp/expiry còn hiệu lực |
| R2 | Mở task theo schema live | Server-issued task ID đúng owner/binding; idempotency key hợp lệ; không tạo duplicate task |
| R3 | Gửi bounded read | Exact file/path, bounds/byte cap, current contract; action ID do server cấp |
| R4 | Theo dõi status/receipt có giới hạn | completed receipt, byte/hash/path binding; unknown không được trình bày là success |
| R5 | Đối chiếu nội dung/kết quả | Nội dung/range đúng file đã cho phép; không chỉ nhận inventory hay metadata |
| R6 | Đóng task theo quyền/schema | Terminal state hợp lệ, không bỏ open task do quên cleanup |

Không hardcode task/action/binding ID trong file này. Lấy ID từ response vừa nhận và truyền đúng ownership. `task_open` cần `idempotency_key`; không tự thêm `expected_facade_contract` nếu live schema không cho; `read_file` phải dùng đúng envelope bounds/contract của profile live, không copy ví dụ `bounds={...}` đã sai.

Bảng tham số tham chiếu từ source hiện tại; phải so lại schema live trước gửi:

| Operation của central `workspace_context` | Trường theo source hiện tại |
| --- | --- |
| `inventory`, `task_list` | Chỉ `operation` |
| `task_open` | `operation`, `binding_id`, `label`, `idempotency_key` |
| `read_file` | Bắt buộc `operation`, `binding_id`, `path`, `idempotency_key`, `expected_facade_contract`; tùy chọn `task_id`, `start_line`, `max_lines`, `max_bytes` ở top-level |
| `read_status` | `operation`, `action_id` do server trả |
| `task_close` | `operation`, `task_id` do server trả |

`expected_facade_contract` là object `{schema_version, profile, sha256}` lấy từ metadata live; không suy từ DB schema hoặc điền source version vào request chưa được server xác nhận. Transport retry chỉ được replay cùng exact intent/key qua cơ chế idempotency; không tạo key mới để lặp effect chưa rõ kết quả.

**Exit G5-R:** từ real ChatGPT invocation đến completed Windows file-read receipt và task terminal có correlation đầy đủ. Backend 56-byte canary cũ và inventory/task_list thành công không đủ.

**Nếu timeout/unknown:** dừng gửi effect mới cho cùng intent, thu action/attempt/handle/receipt/quarantine evidence và giao operator reconcile. Không sửa quyền, tăng scope hoặc retry bằng idempotency key mới để vượt gate.

## 10. H6 — Patch trước; exec là nhánh độc lập có gate mạnh hơn

### 10.1. G6-W — Patch có giới hạn

1. Chọn một existing file thử nghiệm được owner duyệt; ghi before-hash, exact small diff, size và validator; không chọn file đang được người khác sửa.
2. Có approved patch/standing policy đúng principal/binding/generation; writer claim và local lease tuân schema live.
3. Client thật gửi request, nhận action/receipt; xác minh after-hash và diff chỉ nằm trong allowlist.
   - Nếu response là `effect_applied_pending_local_acceptance`, chỉ được kết luận effect đã áp dụng và còn chờ nghiệm thu local.
   - Hoàn tất proof/review/acceptance đúng runtime authority, rồi đọc lại disposition cuối. Không gọi trạng thái pending đó là completed/accepted.
4. Kiểm stale before-hash/wrong path/scope denied/replay bằng fixture hoặc canary cô lập được duyệt; expected denial phải không có effect.
5. Hoàn tác nội dung thử qua một patch có review và authority riêng nếu cần; không dùng `git checkout --` để xóa cả thay đổi khác.
6. Release writer/close task qua giao diện hỗ trợ; kiểm không có duplicate effect hoặc orphaned writer.

**Exit:** completed patch receipt từ client thật, đúng before/after/proof và task/lease terminal; negative cases không có effect. Không gộp document create/convert vào patch PASS nếu chưa có canary riêng cho capability đó.

Trong central facade, writer claim dùng contract `task_control(operation="writer_claim")`; đó không phải EOCL `task_control(action="accept")` của local Coding Tools MCP. Phải kiểm đúng profile, schema và server identity trước khi chọn operation/action; cùng tên public tool không đồng nghĩa cùng authority.

### 10.2. G6-X — Exec giữ OFF cho tới đủ các điều kiện

Các điều kiện đồng thời:

- Exact packaged Windows runtime được chấp nhận; không coi development policy bị từ chối là lỗi cần bypass.
- Workspace-bound Windows Sandbox probe thành công trên đúng installation/device/workspace/generation.
- Ubuntu capability/grant/binding và local exec policy khớp, fingerprint/expiry được readback.
- Lỗi sandbox `cmd.exe`/npm-script được tái hiện, xác định nguyên nhân và sửa bằng regression; không nới host filesystem/network để ép xanh.
- Npm/npx prefix/cwd, guest path/temp, Node child lifecycle, stop/process-tree cleanup và deny off-scope đã được chứng minh.
- Explicit structured argv/cwd/budget của canary được duyệt; không chạy một project script thật vì chọn nhầm cwd/prefix.

Canary bắt đầu từ thao tác không phá dữ liệu, trong fixture/selected workspace được phép. Cần receipt spawn → observe → exit/stop và không có effect ngoài scope. Symlink/junction/path traversal, child process, environment leak và timeout phải có proof ở đúng OS boundary.

**Nếu thiếu bất kỳ điều kiện nào:** `exec=false`, G6-X = BLOCKED hoặc NOT_RUN với lý do cụ thể; read/patch có thể tiếp tục trong phạm vi đã duyệt. Không gọi toàn bộ kế hoạch hoàn tất nếu exec thuộc hợp đồng cuối cùng.

## 11. H7 — Nghiệm thu recovery theo C01–C12

### 11.1. Trước fault injection

- Chốt installed/development/package identity, source checkpoint và role; không trộn chứng cứ hai installation.
- Isolated harness trước; real maintenance/reboot/máy B sau và có quyền riêng.
- Chụp user intent: running, idle hoặc manual stop; ghi jobs/leases/epoch trước/sau.
- Không khởi chạy test lỗi khi workspace có writer thật hoặc công việc tự nhiên H8 đang dùng cùng runtime.
- Timeout/số retry theo hợp đồng/harness đang dùng; nếu chưa có thì chốt trước test, không kéo dài sau khi fail để tạo PASS.

### 11.2. Ma trận coverage

| Tiêu chí | Case bắt buộc/đầu ra để đánh giá | Không đủ để PASS |
| --- | --- | --- |
| C01 | Cold start và reboot/logon đúng entry point; fresh boot/start-token/package; task đúng workspace | Chỉ process spawn trong fixture |
| C02 | Một owner/epoch; late-busy/semantic refusal; drain trước handoff; không spawn dưới terminal READY | Ping healthy |
| C03 | Same-SHA bootstrap theo attestation hợp lệ khi predecessor rỗng; admission vẫn đúng boundary | ACK tự chế |
| C04 | Compatible skipped releases positive; unknown/breaking/tamper/cycle bị từ chối/đòi discovery | Chỉ version string giống |
| C05 | Timeout/lock/cleanup hữu hạn; typed cause; census không orphan | Một lần start thành công |
| C06 | ManualStop, idle-off, live writer/job/lease, foreign identity/PID reuse/source drift không bị vượt | Hết lỗi nhờ kill/reset state |
| C07 | Host-only loss/restart đúng role; bounded retries; không duplicate owner/effect | Tự bật lại được một lần |
| C08 | Giữ valid session; missing/revoked/login phân loại đúng; không clear session vì runtime lỗi | Login lại bằng tay rồi gọi là giữ session |
| C09 | Hai máy/client receipts đúng endpoint/workspace/generation; wrong-target fail-closed | Hai tab cùng một máy thay cho yêu cầu hai máy |
| C10 | Exact source→proof→acceptance→runtime→artifact; rollback giữ history; missing refs được xử lý | Markdown report không nối canonical checkpoint |
| C11 | Natural success không sửa source/xóa state/refresh tay không cần thiết | Canary do operator nudge liên tục |
| C12 | Đủ mandatory coverage, user/outcome đúng revision, không blocker bắt buộc | Accepted RUN hoặc tỷ lệ tiêu chí tự chấm |

Hồ sơ 22/09 nêu cửa sổ dùng thực tế ≥48h và máy B. Phải đối chiếu contract/owner hiện hành trước khi áp dụng hoặc thay đổi; không tự bỏ các điều kiện này vì khó tổ chức.

**Exit G7:** mỗi criterion có trạng thái, evidence identity và reviewer; thiếu thì OPEN/UNKNOWN/NOT_RUN rõ ràng. Không gán cả 12 PASS chỉ từ một packaged smoke.

## 12. H8 — Goal continuation trên công việc thật

### 12.1. Tái sử dụng thay vì xây lại

Kiểm tra các module đã có: `goal_pursuit.py`, `run_continuation.py`, `continuation_driver.py`, `continuation_contract.py`, `continuation_consent_http.py`, `problem_resolution_journey.py` và ledger authority. Chỉ bổ sung nối dispatch/observe/telemetry khi một test hoặc natural case chứng minh thiếu.

1. Chọn một Problem thật trong `E:\DEV\Codex-web`; làm việc ở HR hay repository khác cần scope riêng, không suy quyền từ kế hoạch này.
2. Chốt exact Problem Revision, oracle độc lập, accepted behavior, allowed paths, endpoint/workspace/controller, budgets và stop/revoke/expiry.
3. Cấp continuation grant qua đường hỗ trợ sau consent; không tự tạo background automation hoặc goal để làm báo cáo xanh.
4. Proof fixture trước: typed proposal → validate → actual dispatch → observe → proof → review; không chỉ sinh văn bản yêu cầu người dùng copy sang chat khác.
5. Natural run: người dùng giao một lần, observation window rõ; ghi mọi intervention và failed attempt; approvals/review có ý nghĩa không bị đếm thành unnecessary nudge.
6. Reconnect/restart chỉ khi nằm trong grant/maintenance permission; revalidate identity, budget, pending effects và current revision.
7. Đến ACCEPTING thì controller review; model/worker không tự accept. Đến outcome gate thì người xác nhận độc lập đưa kết quả.

### 12.2. Ma trận đủ 18 tiêu chí revision 2

| Criterion | Oracle / bằng chứng bắt buộc |
| --- | --- |
| continuity.auto_resume | Sau ordinary REPLAN/report/reconnect/accepted restart có dispatch thực tiếp theo khi được phép, không manual pump |
| continuity.no_duplicate_effect | Retry/reconnect/crash trước-sau ACK không lặp effect; unknown có reconciliation |
| continuity.terminal_stop | Terminal/blocker/stop/revoke dừng đúng typed cause; transport timeout không làm im lặng hoặc retry vô hạn |
| telemetry.durable_events | Event durable qua restart, exact logical IDs, không transcript/private reasoning |
| BG01 | Một exact Goal/Problem Revision/workspace/endpoint/controller; duplicate-start không tạo pursuit/RUN trùng |
| BG02 | Opt-in còn hiệu lực thì response end không ngắt; stop/revoke thắng continuation |
| BG03 | Oracle PASS/FAIL/UNKNOWN từ proof thật; stale/missing/zero-test không thành PASS |
| BG04 | Typed proposal được dispatch thật, có turn/action/result/proof linkage; không human relay |
| BG05 | Parent budget durable/atomic, không reset qua child/restart, không tự gia hạn |
| BG06 | Duplicate/out-of-order/two-wake/lost ACK không double mutation; unknown không replay |
| BG07 | Resume revalidate source/env/revision/epoch/authority; không chuyển máy/scope ngầm |
| BG08 | No-progress/expiry/budget/blocker dừng hữu hạn; typed next action và bounded backoff |
| BG09 | Progress/review tới đúng giao diện/controller; ACCEPTING cần accept/reject được phép |
| BG10 | Natural case có zero manual relay và zero unnecessary nudge được quan sát trong cửa sổ đã duyệt |
| BG11 | Failure→replan→dispatch→proof→budget/recovery→acceptance→outcome nối canonical, gồm attempt thất bại |
| BG12 | Dedup/privacy/coverage rõ; synthetic riêng, missing data unknown; không ROI giả |
| BG13 | Exact source/proof/runtime + isolated fault proof; rollback không mất ledger |
| BG14 | Confirmed chỉ với outcome đúng user/Problem Revision và không mandatory blocker |

**Exit G8:** technical continuation và natural outcome báo riêng. Sau một case thật, mở rộng 5–10 case khi có nhu cầu và quyền để đánh giá ổn định/hiệu quả; không bịa workload hay coi một case là causal ROI.

## 13. H9 — Đóng Problem bằng coverage và outcome, không bằng số test

1. Đọc lại current revision và contract fingerprint trước khi closure; không dùng revision đã bị thay thế.
2. Lập coverage mapping từng criterion → exact RUN/WAVE/proof/checkpoint/runtime/client receipt → reviewer → outcome.
3. Đối soát missing report/ledger references. Nếu lịch sử không đủ thì UNKNOWN; không tạo lại acceptance hoặc lùi clock cho khớp báo cáo.
4. Reconcile stale RUN/resource qua supported exact-ID maintenance sau baseline/authority cần thiết. Không coi 17 stale candidates là quyền bulk-close.
5. Dùng outcome/reconcile/confirm action đúng schema đang expose. Nếu outcome chưa có, dừng ở trạng thái kỹ thuật/provisional được contract cho phép.
6. Khi user xác nhận hoặc oracle độc lập chứng minh sai, reopen/replan đúng revision lineage, không xóa kết quả cũ.

**Exit G9:** hai Problem được đóng riêng khi đủ hợp đồng riêng. Không cho thành công recovery tự đóng continuation hoặc ngược lại.

## 14. H10 — Package, cài đặt, rollback và release

### 14.1. Source freeze và version

1. Chốt source/config/contract fingerprint, owner review, Git identity và accepted receipt cho candidate.
2. Sửa maintained release guidance đang nói `1.0.3` để phù hợp quyết định version thực tế (`package.json` baseline là `1.0.7`); không tự bump version hoặc đổi protocol/schema theo product version.
3. Phân loại mọi dirty/untracked path. Không bắt unrelated work phải mất đi để có clean build; dùng checkout/worktree đã chuẩn bị đúng nguồn nếu cần, ngoài `.coding-tools` và qua công cụ worktree được hỗ trợ.
4. Nếu commit được yêu cầu, tuân mục 17; commit không cấp quyền push, install hoặc publish.

### 14.2. Candidate không ghi đè artifact cũ

Phần build/proof candidate của mục này được phép chuẩn bị từ G1/source freeze để phục vụ G6-X và G7. **Không cần phát hành trước mới kiểm được exec**; ngược lại, publish/customer acceptance vẫn phải đợi đủ các gate của scope release. Candidate còn thiếu exec proof phải ghi đúng hạn chế và giữ policy exec off ngoài canary được cấp quyền.

`npm run dist` hiện gọi `scripts/clean-dist.js`, xóa toàn bộ `dist` trước NSIS build. **Không chạy mặc định** khi trong đó còn candidate, artifact runtime hoặc bằng chứng cần giữ. Đọc script và xác định chính xác targets; lưu giữ/hash/kiểm tra không process nào cần chúng trước khi có quyền cleanup/build.

Trước cleanup, cần preservation receipt/manifest được chốt cho các artifact sẽ bị tác động: exact path, SHA-256, size, source/candidate/runtime identity, process/reference đang dùng và destination bảo toàn đã kiểm hash; nếu không bảo toàn được thì ghi `DO_NOT_CLEAN`. Có thể dùng artifact manifest hiện có, không xây một hệ thống mới. Nếu process còn trỏ vào artifact hoặc chưa xác định owner thì dừng cleanup, chọn output/tag cô lập; không dừng process chỉ để làm sạch `dist`.

`npm run dist:dir` hiện dùng candidate tag mặc định có thể đã tồn tại. Ưu tiên chọn tag mới, ví dụ dưới đây, sau khi xác nhận thư mục chưa tồn tại:

```powershell
# Tạo artifact local, không install/restart; cần G1 và nguồn build đã chốt.
node scripts/build-dev-candidate.js 260927-completion-c1
```

Builder hiện tạo `dist/windows-candidate-mxc-wsb-cbe1774-260927-completion-c1`. Chuỗi `cbe1774` là một phần naming của script, **không phải chứng cứ source HEAD**. Phải dùng provenance/manifest/hash để xác nhận nguồn. Builder từ chối overwrite; nếu tag đã dùng, chọn tag mới, không xóa candidate cũ để reuse tên.

Script này bật opt-in cho unsigned experimental MXC Windows Sandbox dev candidate. Không dùng opt-in hoặc candidate unsigned đó để vượt release verifier; NSIS/customer release vẫn phải đạt tiêu chí thực sự.

### 14.3. Proof package và cài đặt

- Verify exact resources, source/app.asar hashes, product version và marker W1; giữ cả negative tests.
- Chạy packaged Recovery smoke bằng đúng candidate, isolated user data; xác minh descriptor/Scheduled Task production không đổi bởi smoke.
- Sau quyền install, kiểm installed provenance, startup/logon/reboot, selected workspace và runtime role trên bản cài thật.
- Chạy lại real-client bounded read canary với exact installed source; patch/exec theo scope release.
- Kiểm upgrade/rollback với compatible DB/schema/effects; không restore toàn profile/ledger cũ để giả thành công.
- UI UAT: mở lại Settings, tình trạng offline/stale/denied/expired/ready có một next action đúng; không bắt pair/login lại sai lớp.
- Required CI/external checks thiếu hoặc bị account/runner block phải ghi riêng; local pass không thay CI.

**Exit G10:** release manifest, hashes/signing status, exact source/proof/live/installed receipts, known limitations, rollback, operator acceptance. Chỉ publish/tag/push sau explicit destination authority. Nếu chưa có authority, bàn giao local candidate và ghi NOT_PUBLISHED.

## 15. Validation matrix — lệnh có thật, chạy khi đúng phạm vi

Không chạy tất cả lệnh cho mỗi gói. Reuse exact valid proof nếu relevant inputs chưa đổi. Những lệnh test/build có thể tạo fixture, cache hoặc child process; không gọi chúng là read-only status.

### 15.1. Node focused — PowerShell tại repository root

```powershell
# S-UI
node --check renderer/app.js
node --test tests/settings-redesign.test.js tests/control-center-manager.test.js tests/system-setup-console.test.js

# S-REC / H2, chỉ chọn nhóm bị thay đổi
node --test tests/recovery-supervisor.test.js tests/trusted-recovery-bootstrap.test.js tests/activation-closure.test.js
node --test tests/full-clean-activation-command.test.js tests/full-clean-activation.test.js tests/accepted-code-activation.test.js

# W1 / bridge boundaries nếu packet liên quan
node --test tests/chat-page-retirement.test.js tests/control-plane-file-read-bridge.test.js tests/control-plane-approved-patch-bridge.test.js
```

### 15.2. Control Plane focused

```powershell
# Dùng interpreter đã xác định dependencies; không cài package tùy tiện trên runtime production.
python -B -m unittest discover -s control-plane/tests -p 'test_mcp_file_read_facade.py' -q
python -B -m unittest discover -s control-plane/tests -p 'test_mcp_task_sessions.py' -q
python -B -m unittest discover -s control-plane/tests -p 'test_connected_agent_status.py' -q
python -B -m unittest discover -s control-plane/tests -p 'test_authority_renewal.py' -q
```

Nếu S-CP đổi auth/profile/cross-surface, chạy thêm batch thích hợp **trong WSL/Ubuntu đã cấu hình**:

```bash
cd /mnt/e/DEV/Codex-web
python3 -B -m unittest discover -s control-plane/tests -p 'test_mcp*.py' -q
```

Path WSL trên chỉ đúng khi repo được mount tại `/mnt/e`; kiểm root trước. POSIX permission/symlink tests fail trên Windows phải phân loại environment, không xóa test hoặc gọi là source PASS. WSL pass không thay Windows DPAPI/ACL/process proof.

### 15.3. Coding Tools MCP / continuation / sandbox

```powershell
Push-Location -LiteralPath 'E:\DEV\Codex-web\resources\coding-tools-mcp'
python -B -m pytest tests/test_goal_pursuit.py tests/test_run_continuation.py tests/test_continuation_consent_http.py -q
# Chỉ nhánh exec/sandbox khi cần đúng Windows environment và fixture authority.
python -B -m pytest tests/test_windows_mxc_state_aware.py tests/test_windows_mxc_sandbox.py -q
Pop-Location
```

Đây là các nhóm ứng viên, không buộc rerun mọi file nếu chỉ một behavior bị đổi. Tách process/live cases khỏi fast unit theo marker/harness thực tế; không suy skip trên Linux là Windows PASS.

### 15.4. Cross-boundary và package gates

| Lệnh/entry point | Khi nào cần | Side effect / lưu ý |
| --- | --- | --- |
| `npm test` | Integrated Electron source gate hoặc release | Có source-root helper có thể dọn legacy `%SystemDrive%` artifact; đọc và kiểm target trước nếu đang giữ forensic evidence |
| `npm run test:mcp` | MCP cross-cutting/full acceptance cần thiết | Không mặc định sau docs-only; giữ lỗi/skip/environment classification |
| `npm run test:all` | Final integrated source có ranh giới rộng hoặc release | Không dùng một lần xanh để thay live/installed proof |
| `npm run test:recovery:e2e` | Thay process ownership/recovery | Real-process harness; kiểm isolated profile/cleanup trước |
| `node scripts/packaged-recovery-smoke.js` | Candidate đã build, `CODEX_PACKAGED_APP_ROOT` do operator chọn đúng | Chạy isolated package processes; không trỏ profile production |
| `npm run test:recovery:packaged` | Chỉ khi wrapper build-default phù hợp | Wrapper build `dist:dir` trước smoke; có thể đụng default tag, không chạy lại mù |
| `python scripts/build-control-plane-release.py --output-dir <new-output-dir>` | Source/package Control Plane đã chốt | Tạo artifact; placeholder phải được thay bằng đích mới được kiểm |
| `python deploy/control-plane-verify-release.py --release-dir <extracted-release-dir>` | Trước/sau transfer package | Kiểm release đã extract, không tự deploy |
| `git diff --check` | Review diff packet | Không phải code behavior proof |
| `npm run check:coding-tools-history` | Final delivery gate sau khi đã chốt quyền commit/push | Kiểm đúng hai sidecar exceptions, không ignored evidence khác/nested repo/gitlink; không thay staged snapshot proof |
| `npm run stage:coding-tools-delivery` rồi `npm run check:coding-tools-delivery` | Trước mỗi commit hoặc push được yêu cầu | Cả quy trình thay Git index; không phải baseline chỉ đọc; giữ exact snapshot receipt theo mục 17 |

Đây là bảng hướng dẫn; các chuỗi có `<...>` không phải lệnh copy chạy trực tiếp. Với smoke candidate, lấy tên biến/path từ script đang chạy; không giả receipt sau khi chỉ build xong.

## 16. Bằng chứng, checkpoint và bàn giao từng wave

### 16.1. Một bản ghi tối thiểu, không thêm database/framework mới

Dùng canonical ledger/reporting hiện hành cho execution; tài liệu chỉ trỏ tới evidence. Mỗi wave cần:

```text
packet_id / objective / owner / allowed_paths / authority
observed_at / evidence_window / host / workspace / binding_generation
HEAD / source_worktree_fingerprint / contract_profile_version_hash
RUN / WAVE / proof_ids / checkpoint_id
runtime_PID_start_identity / instance / epoch / installed_artifact_hash
commands_actually_run / exit_codes / failed_skipped_not_run
client_origin / task_action_attempt_receipt_ids / effect_disposition
criterion_coverage / independent_outcome / unresolved_blocker
rollback_state / next_action / required_owner
```

Không lưu raw tokens, auth headers, cookies, private keys, raw browser/ChatGPT content, full sensitive command output hoặc private reasoning. Mọi claim missing phải là UNKNOWN/NOT_RUN, không ghi 0.

### 16.2. Mẫu checkpoint operator-visible

```markdown
### Checkpoint <thời điểm + múi giờ> — <packet / RUN / WAVE>

- Đã làm/thay đổi: ...
- Source/Git và source fingerprint: ...
- Runtime/remote/job/lease state: ...
- Proof mạnh nhất: source / focused / accepted / live / installed / natural outcome ...
- Lỗi: current / expected-negative / environment / pre-existing / resolved-retry ...
- Gate: PASS / BLOCKED / UNKNOWN / NOT_RUN, kèm evidence ...
- Phần chưa được phép hoặc chưa làm: ...
- Rollback/trạng thái bảo toàn: ...
- Next action chính xác và owner: ...
```

Kết thúc mỗi batch material, trước handoff/pause hoặc khi gặp refusal phải có checkpoint. Tool output không thay báo cáo trạng thái. Một request queued/running/needs-review không được báo completed.

## 17. Commit/delivery và retention — chỉ chạy khi được yêu cầu

1. Review exact staged source/docs, không stage unrelated source để tiện commit.
2. `.coding-tools` là ngoại lệ bắt buộc của phạm vi delivery: giữ đầy đủ evidence theo AGENTS, không cherry-pick vài file để nhìn sạch.
3. Trước **mỗi commit hoặc push**, thực hiện đúng:

```powershell
npm run stage:coding-tools-delivery
npm run check:coding-tools-delivery
```

**Cảnh báo:** `check:coding-tools-delivery` hiện gọi cả staging helper, không phải một check hoàn toàn chỉ đọc. Không chạy nó trong H0 hoặc lượt lập tài liệu chỉ để xem trạng thái.

4. Xác minh receipt/index/ledger integrity theo guard hiện hành; live canonical drift chỉ được chấp nhận đúng điều kiện receipt/index được quy định. Nếu có mutation khác, stage/check lại trước delivery.
5. `check:coding-tools-history` phải giữ đúng hai ignore exceptions, không nested repository/gitlink trong `.coding-tools`.
6. Nếu phát hiện secret trong evidence: dừng delivery, báo conflict và xử lý secret qua quyền riêng; không tự ignore hoặc publish secret.
7. Không amend unrelated commit, không force-push, không rewrite history hoặc move tag. Commit local không đồng nghĩa push/release/deploy.

## 18. Checklist bắt đầu và checklist kết thúc chương trình

### 18.1. Checklist lượt triển khai đầu tiên

- [ ] Đọc file này, AGENTS và các runbook liên quan; xác nhận chỉ triển khai scope được giao.
- [ ] Recapture HEAD/dirty/owners/runtime, không reuse PID/hash/checkpoint cũ.
- [ ] Phân loại sáu untracked files baseline và mọi phát sinh mới; không xóa tự động.
- [ ] Chốt S-CP/S-REC/S-UI/S-DOC và proof còn hợp lệ; sửa đúng gap có reproduction.
- [ ] Xác định acceptance surface hoặc trusted bootstrap path thực sự được hỗ trợ.
- [ ] Có checkpoint exact source; nếu chưa có, báo blocker/owner/next action, không activation.
- [ ] Xin/chốt quyền Windows lifecycle trước H3; Ubuntu/client/policy quyền riêng sau đó.

### 18.2. Checklist hoàn thiện

- [ ] M1 được nghiệm thu đúng phạm vi read / patch / exec, không gộp capability chưa thử.
- [ ] UI và local MCP chạy đúng installation/source; authority và admission đúng ý định.
- [ ] Ubuntu package/facade/client schema/policy/binding đều có current receipts.
- [ ] Real ChatGPT read workflow hoàn thành; patch/exec có proof riêng nếu thuộc scope.
- [ ] Unknown/quarantined effects có disposition trung thực; không duplicate mutation.
- [ ] C01–C12 có coverage hoặc gap được người dùng chấp nhận qua contract revision hợp lệ.
- [ ] 18 continuity/BG criteria có coverage; BG14 có independent outcome.
- [ ] Hai Problem có canonical transition đúng revision; không tự đóng từ test count.
- [ ] M2 có natural-work evidence, intervention/missingness rõ; economics/ROI chưa đo vẫn unknown.
- [ ] M3 có exact package/install/upgrade/rollback/CI và tài liệu version phù hợp.
- [ ] `.coding-tools` retention/delivery guard đạt nếu có commit/push.
- [ ] Jobs/leases/operations terminal hoặc được bàn giao owner rõ; Git dirty/concurrent state được báo đầy đủ.
- [ ] Chỉ push/tag/publish/deploy nếu có authority và destination cụ thể; nếu không, ghi NOT_PERFORMED.

## 19. Tài liệu và implementation tham chiếu

Thứ tự quyết định: current implementation/focused proof/live contract → CURRENT_STATE → maintained docs → component docs → dated research. Kế hoạch này không ghi đè lịch sử hoặc sửa contract canonical bằng văn bản.

### Điều hành và rollout

- [AGENTS repository](../../AGENTS.md)
- [CURRENT_STATE](../CURRENT_STATE.md)
- [Shared account / workspace status](../SHARED_ACCOUNT_WORKSPACE_STATUS.md)
- [Control Plane implementation status](../CONTROL_PLANE_IMPLEMENTATION_STATUS.md)
- [Control Plane Recovery Runbook](../CONTROL_PLANE_RECOVERY_RUNBOOK.md)
- [Windows exact validation](../WINDOWS_EXACT_VALIDATION_RUNBOOK.md)
- [Recovery Host](../RECOVERY_HOST.md)
- [Testing](../TESTING.md)
- [Release checklist](../RELEASE_CHECKLIST.md)
- [OpenAI policy risk reduction W0–W6](../OPENAI_POLICY_RISK_REDUCTION_PLAN.md)
- [Settings simplification](../SETTINGS_SIMPLIFICATION_PLAN.md)
- [System setup simplification](../260922_SYSTEM_SETUP_SIMPLIFICATION_PLAN.md)

### Hợp đồng và chronology

- [Kế hoạch hai Problem, 22/09](260922_ke_hoach_xu_ly_hai_problem_va_danh_gia_toan_dien_app.md)
- [Single Goal background continuation](../SINGLE_GOAL_BACKGROUND_CONTINUATION_PLAN.md)
- [BG01–BG14 source/focused audit, 23/09](260923_bg01_bg14_source_focused_audit.md)
- [HTTP shutdown/drain proof, 23/09](260923_http_server_shutdown_full_suite_proof.md)
- [Control Plane README / facade contracts](../../control-plane/README.md)

### Entry points đã đối chiếu khi lập kế hoạch

- [Package scripts](../../package.json)
- [Full-clean activation](../../scripts/full-clean-activation.js)
- [Trusted bootstrap](../../scripts/trusted-recovery-bootstrap.js)
- [Trusted source/receipt validation](../../electron/services/trustedRecoveryBootstrap.js)
- [Lifecycle census](../../resources/coding-tools-mcp/scripts/report_lifecycle_census.py)
- [Facade schema](../../control-plane/control_plane/mcp_facade.py)
- [Supervisor](../../resources/recovery-supervisor/recovery-supervisor.ps1)
- [Candidate builder](../../scripts/build-dev-candidate.js)
- [Packaged recovery smoke](../../scripts/packaged-recovery-smoke.js)
- [Control Plane release builder](../../scripts/build-control-plane-release.py)
- [Control Plane release verifier](../../deploy/control-plane-verify-release.py)

---

**Trạng thái bàn giao tài liệu:** kế hoạch được thiết kế để bắt đầu từ H0, không xác nhận đã hoàn thành H0–H10. Bằng chứng baseline thuộc lượt rà soát ngày 27/09; operator phải recapture trước thao tác. Không có deployment, activation, commit, push hoặc release phát sinh chỉ bởi việc tạo file này.
